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
