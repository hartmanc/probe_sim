// Real load progress (owner, 1 Nov 2026: "no progress visible to the user"). The big files (probe.glb 4.8 MB, the heightfield,
// the aerial imagery, the far terrain) are read through a streaming reader that reports bytes received against Content-Length;
// the overall fraction is the byte-weighted progress of each stage's files inside the stage's weight. A file without a
// Content-Length counts as 0 until it ends (the old stage tick). Pure and unit-tested; the DOM never appears here.

export interface Stage { id: string; weight: number }

/** A fraction of a stage's bytes is never reported as done before the stage is: parsing and decoding still follow the download. */
export const BYTES_CEILING = 0.95;

export class LoadProgress {
  private files = new Map<string, Map<string, { got: number; total: number }>>();
  private ended = new Set<string>();
  private best = 0;
  private sum: number;

  constructor(private stages: readonly Stage[]) {
    this.sum = stages.reduce((a, s) => a + s.weight, 0) || 1;
  }

  /** Bytes received of one file of a stage (`total` 0 or unknown: the file only counts when its stage ends). */
  bytes(stage: string, file: string, got: number, total?: number): void {
    let m = this.files.get(stage);
    if (!m) { m = new Map(); this.files.set(stage, m); }
    m.set(file, { got: Math.max(0, got), total: total && total > 0 ? total : 0 });
  }

  /** A stage is complete (its work finished, whether or not its bytes were counted). */
  end(stage: string): void { this.ended.add(stage); }

  private stageFrac(id: string): number {
    if (this.ended.has(id)) return 1;
    const m = this.files.get(id);
    if (!m) return 0;
    let got = 0, total = 0;
    for (const f of m.values()) if (f.total > 0) { got += Math.min(f.got, f.total); total += f.total; }
    return total > 0 ? Math.min(BYTES_CEILING, got / total) : 0;
  }

  /** What is still outstanding, for the slow-load console line: stages not ended, and their files' bytes. */
  outstanding(): string[] {
    const out: string[] = [];
    for (const st of this.stages) {
      if (this.ended.has(st.id)) continue;
      const fs = [...(this.files.get(st.id) ?? [])].map(([n, f]) => `${n} ${f.got}/${f.total || '?'} B`);
      out.push(`${st.id}${fs.length ? ` (${fs.join(', ')})` : ''}`);
    }
    return out;
  }

  /** 0..1, never decreasing; 1 only when every stage has ended. */
  fraction(): number {
    let f = 0;
    for (const s of this.stages) f += s.weight * this.stageFrac(s.id);
    const v = Math.min(1, f / this.sum);
    if (v > this.best) this.best = v;
    return this.best;
  }
}

/** Calls `fn` at most every `ms`, always delivering the last value (a trailing call); `flush` delivers it now. */
export function throttled<T>(fn: (v: T) => void, ms: number, now: () => number = () => performance.now(), later: (f: () => void, ms: number) => unknown = setTimeout): { push(v: T): void; flush(): void } {
  let last = -Infinity, pending: { v: T } | null = null, armed = false;
  const run = () => { armed = false; if (pending) { const v = pending.v; pending = null; last = now(); fn(v); } };
  return {
    push(v: T) {
      pending = { v };
      const wait = last + ms - now();
      if (wait <= 0) run();
      else if (!armed) { armed = true; later(run, wait); }
    },
    flush() { run(); },
  };
}

// ---------------------------------------------------------------- streamed reads that cannot hang

export const STALL_MS = 5000;
export const SLOW_LOAD_MS = 20000;

/** "0.4 of 1.7 MB" while a file streams (one decimal); just "0.4 MB" without a Content-Length. */
export function mbReadout(got: number, total: number): string {
  const mb = (n: number) => (n / 1048576).toFixed(1);
  return total > 0 ? `${mb(Math.min(got, total))} of ${mb(total)} MB` : `${mb(got)} MB`;
}

/** The overall fraction has not moved for SLOW_LOAD_MS: say so (the label, one console line). */
export const loadIsSlow = (lastChangeAt: number, now: number): boolean => now - lastChangeAt >= SLOW_LOAD_MS;

export interface StreamDeps {
  /** Open the file (null: missing, a real 404 or an HTML fallback page). */
  open(signal?: AbortSignal): Promise<Response | null>;
  onBytes?(got: number, total: number): void;
  /** one console line per fallback */
  log?(msg: string): void;
  stallMs?: number;
}

/**
 * A file's bytes, streamed with byte counts, that cannot hang or silently turn into "missing":
 * - no chunk for `stallMs`: cancel the reader, abort the request, re-fetch the file once plainly (arrayBuffer);
 * - a read error, or a body that cannot be read as a stream: the same plain fetch;
 * - only a real missing file (open() → null) gives null.
 */
export async function streamBytes(name: string, d: StreamDeps): Promise<{ buf: ArrayBuffer; type: string } | null> {
  const stallMs = d.stallMs ?? STALL_MS;
  const ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  let got = 0, total = 0, type = '';
  const plain = async (why: string): Promise<{ buf: ArrayBuffer; type: string } | null> => {
    d.log?.(`[loader] ${name}: ${why} after ${got} bytes, re-fetched plainly`);
    try {
      const r = await d.open();
      if (!r) return null;
      const buf = await r.arrayBuffer();
      d.onBytes?.(buf.byteLength, buf.byteLength);
      return { buf, type: r.headers.get('content-type') ?? type };
    } catch (e) { d.log?.(`[loader] ${name}: the plain fetch failed too: ${String(e)}`); return null; }
  };
  const r = await d.open(ctrl?.signal);
  if (!r) return null;
  type = r.headers.get('content-type') ?? '';
  total = Number(r.headers.get('content-length')) || 0;
  let reader: ReadableStreamDefaultReader<Uint8Array>;
  try {
    if (!r.body?.getReader) throw new Error('body is not a stream');
    reader = r.body.getReader();
  } catch (e) { return plain(`no readable stream (${String(e)})`); }
  const chunks: Uint8Array[] = [];
  d.onBytes?.(0, total);
  for (;;) {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const stall = new Promise<'stall'>((res) => { timer = setTimeout(() => res('stall'), stallMs); });
    let step: ReadableStreamReadResult<Uint8Array> | 'stall';
    try { step = await Promise.race([reader.read(), stall]); }
    catch (e) { clearTimeout(timer); try { ctrl?.abort(); } catch { /* done */ } return plain(`stream error (${String(e)})`); }
    clearTimeout(timer);
    if (step === 'stall') {
      try { await reader.cancel(); } catch { /* already broken */ }
      try { ctrl?.abort(); } catch { /* done */ }
      return plain('stream stalled');
    }
    if (step.done) break;
    chunks.push(step.value); got += step.value.byteLength;
    d.onBytes?.(got, total);
  }
  const out = new Uint8Array(got);
  let o = 0;
  for (const c of chunks) { out.set(c, o); o += c.byteLength; }
  return { buf: out.buffer, type };
}
