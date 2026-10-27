// Start menu → "Report a bug / request a feature" (owner's decision, 26 Oct 2026): the player types a description and
// picks bug / feature; the game adds the version, the build's commit, the track, the device class, the browser, the
// screen and the last captured error, and POSTs it to /api/feedback, which files a public GitHub issue (src/feedback).
// No email field. The scoreboard name registered on this device goes with it (the server checks the device secret).
import type { MenuEntry, MenuPage } from './menu';
import { lastError } from './errors';

export interface FeedbackPayload {
  kind: 'bug' | 'feature';
  description: string;
  context: { version: string; sha: string; track: string; device: string; ua: string; screen: string; error?: string };
  name?: string;
  secret?: string;
  images?: PictureUpload[];
}

/** One picture on the wire: always a re-encoded JPEG, base64 without a data: prefix. */
export interface PictureUpload { name: string; type: 'image/jpeg'; data: string }

export const MAX_DESCRIPTION = 2000;
export const MAX_PICTURES = 3;
export const MAX_SIDE = 1600;
export const JPEG_QUALITY = 0.85;
/** the encoder tries to land at or under this ... */
export const TARGET_BYTES = 600 * 1024;
/** ... and a picture still over this is refused */
export const MAX_PICTURE_BYTES = 900 * 1024;
/** the whole JSON body (the Function takes 4.5 MB; the server caps it lower) */
export const MAX_BODY_BYTES = 2.5 * 1024 * 1024;

/** Pure: the image files in a paste event's clipboardData (items first, then files), in order. */
export function imagesFromClipboard(cd: { items?: ArrayLike<{ kind: string; type: string; getAsFile(): File | null }>; files?: ArrayLike<File> } | null | undefined): File[] {
  const out: File[] = [];
  if (!cd) return out;
  if (cd.items && cd.items.length) {
    for (let i = 0; i < cd.items.length; i++) {
      const it = cd.items[i];
      if (it.kind === 'file' && it.type.startsWith('image/')) { const f = it.getAsFile(); if (f) out.push(f); }
    }
    return out;
  }
  if (cd.files) for (let i = 0; i < cd.files.length; i++) if (cd.files[i].type.startsWith('image/')) out.push(cd.files[i]);
  return out;
}

/** Pure: how many of `incoming` fit next to `have` pictures, and how many were left out. */
export function takePictures<T>(have: number, incoming: T[]): { take: T[]; dropped: number } {
  const room = Math.max(0, MAX_PICTURES - have);
  return { take: incoming.slice(0, room), dropped: Math.max(0, incoming.length - room) };
}

/** Pure: the size gate after downscaling; a reason when the picture is refused. */
export function pictureSizeProblem(bytes: number): string | null {
  return bytes > MAX_PICTURE_BYTES ? `too big even after shrinking (${Math.round(bytes / 1024)} KB, the limit is ${MAX_PICTURE_BYTES / 1024} KB)` : null;
}

/** Pure: the byte length of the JSON body, and a reason when it is over the limit. */
export function bodyBytes(json: string): number { return new TextEncoder().encode(json).length; }
export function bodyProblem(json: string): string | null {
  const n = bodyBytes(json);
  return n > MAX_BODY_BYTES ? `The report with its pictures is too large (${(n / 1024 / 1024).toFixed(1)} MB, the limit is ${MAX_BODY_BYTES / 1024 / 1024} MB): remove a picture` : null;
}

/** Pure: longest side scaled to at most `max`, never enlarged. */
export function fitSize(w: number, h: number, max = MAX_SIDE): { w: number; h: number } {
  const k = Math.min(1, max / Math.max(w, h, 1));
  return { w: Math.max(1, Math.round(w * k)), h: Math.max(1, Math.round(h * k)) };
}

/** The canvas step, injectable so tests need no canvas: encode `file` as JPEG with the longest side <= maxSide. */
export type JpegEncoder = (file: File, maxSide: number, quality: number) => Promise<{ bytes: number; data: string }>;

/** Steps tried in order until one lands under TARGET_BYTES; the first is the spec (1600 px, 0.85). */
const ENCODE_STEPS: [number, number][] = [[MAX_SIDE, JPEG_QUALITY], [MAX_SIDE, 0.7], [1200, 0.7], [1000, 0.6]];

/** Shrink a picture for upload: a ready PictureUpload, or the reason it was refused. */
export async function preparePicture(file: File, encode: JpegEncoder = canvasEncode): Promise<{ ok: true; pic: PictureUpload; bytes: number } | { ok: false; reason: string }> {
  let best: { bytes: number; data: string } | null = null;
  try {
    for (const [side, q] of ENCODE_STEPS) {
      const r = await encode(file, side, q);
      if (!best || r.bytes < best.bytes) best = r;
      if (r.bytes <= TARGET_BYTES) break;
    }
  } catch { return { ok: false, reason: `${file.name || 'picture'} could not be read as a picture` }; }
  const bad = pictureSizeProblem(best!.bytes);
  if (bad) return { ok: false, reason: `${file.name || 'picture'} is ${bad}` };
  const base = (file.name || 'picture').replace(/\.[^.]*$/, '').replace(/[^\w.-]+/g, '_').slice(0, 40) || 'picture';
  return { ok: true, pic: { name: `${base}.jpg`, type: 'image/jpeg', data: best!.data }, bytes: best!.bytes };
}

/** Browser canvas: decode, draw on white (PNG transparency), re-encode as JPEG. */
async function canvasEncode(file: File, maxSide: number, quality: number): Promise<{ bytes: number; data: string }> {
  const bmp = await createImageBitmap(file);
  const { w, h } = fitSize(bmp.width, bmp.height, maxSide);
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d')!;
  g.fillStyle = '#fff'; g.fillRect(0, 0, w, h);
  g.drawImage(bmp, 0, 0, w, h);
  bmp.close?.();
  const blob = await new Promise<Blob | null>((res) => c.toBlob(res, 'image/jpeg', quality));
  if (!blob) throw new Error('encode failed');
  const buf = new Uint8Array(await blob.arrayBuffer());
  let bin = '';
  for (let i = 0; i < buf.length; i += 0x8000) bin += String.fromCharCode(...buf.subarray(i, i + 0x8000));
  return { bytes: buf.length, data: btoa(bin) };
}

/** Pure: the request body. */
export function buildFeedback(a: {
  kind: 'bug' | 'feature'; description: string; version: string; sha: string; track: string; device: string;
  ua: string; screen: string; error: string | null; name: string | null; secret: string | undefined; images?: PictureUpload[];
}): FeedbackPayload {
  return {
    kind: a.kind,
    description: a.description.trim().slice(0, MAX_DESCRIPTION),
    context: { version: a.version, sha: a.sha, track: a.track, device: a.device, ua: a.ua.slice(0, 300), screen: a.screen, ...(a.error ? { error: a.error } : {}) },
    ...(a.name && a.secret ? { name: a.name, secret: a.secret } : {}),
    ...(a.images?.length ? { images: a.images.slice(0, MAX_PICTURES) } : {}),
  };
}

export interface FeedbackPageOptions {
  version: string;
  sha: string;
  track: string;
  device: string;
  name(): string | null;
  secret(): string | undefined;
  toast(msg: string, ms?: number): void;
  refresh(): void;
  fetch?: (url: string, init: RequestInit) => Promise<Response>;
  /** test hook: the canvas step */
  encode?: JpegEncoder;
}

interface Pic { pic: PictureUpload; bytes: number; src: string }

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

let box: HTMLElement | null = null;
let area: HTMLTextAreaElement | null = null;
let count: HTMLElement | null = null;
let strip: HTMLElement | null = null;
let picCount: HTMLElement | null = null;
let pics: Pic[] = [];
let busy = 0;
let notify: (m: string, ms?: number) => void = () => {};
let encoder: JpegEncoder | undefined;

function renderPics(): void {
  if (!strip || !picCount) return;
  strip.replaceChildren(...pics.map((p, i) => {
    const w = el('div', 'fb-pic');
    const img = el('img');
    img.src = p.src; img.alt = `Picture ${i + 1}`;
    const rm = el('button', 'fb-rm', '×');
    rm.type = 'button';
    rm.setAttribute('aria-label', `Remove picture ${i + 1}`);
    rm.addEventListener('click', () => { URL.revokeObjectURL?.(p.src); pics = pics.filter((x) => x !== p); renderPics(); });
    w.append(img, rm);
    return w;
  }));
  picCount.textContent = `${pics.length} of ${MAX_PICTURES} pictures`;
}

async function addFiles(files: File[]): Promise<void> {
  const { take, dropped } = takePictures(pics.length + busy, files);
  if (dropped) notify(`At most ${MAX_PICTURES} pictures per report`);
  busy += take.length;
  for (const f of take) {
    const r = await preparePicture(f, encoder);
    busy--;
    if (!r.ok) { notify(r.reason, 5000); continue; }
    let src = '';
    try { src = URL.createObjectURL(f); } catch { src = `data:image/jpeg;base64,${r.pic.data}`; }
    pics.push({ pic: r.pic, bytes: r.bytes, src });
  }
  renderPics();
}

export function feedbackPage(o: FeedbackPageOptions): MenuPage {
  let kind: 'bug' | 'feature' = 'bug';
  let state: 'idle' | 'sending' | 'sent' = 'idle';
  if (!box) {
    box = el('div', 'feedback');
    area = el('textarea', 'fb-text');
    area.maxLength = MAX_DESCRIPTION;
    area.rows = 5;
    area.placeholder = 'What happened, where on the track, what you expected. Or the feature you would like.';
    area.setAttribute('aria-label', 'Description');
    count = el('div', 'fb-count');
    // typing belongs to the text box: keep keys from input.ts (W A S D, Esc, Enter = menu verbs); Esc leaves the box
    area.addEventListener('keydown', (e) => { e.stopPropagation(); if (e.key === 'Escape') area!.blur(); });
    area.addEventListener('keyup', (e) => e.stopPropagation());
    area.addEventListener('input', () => { count!.textContent = `${area!.value.length} / ${MAX_DESCRIPTION}`; });
    strip = el('div', 'fb-pics');
    picCount = el('div', 'fb-count');
    const add = el('label', 'fb-add');
    const input = el('input');
    input.type = 'file'; input.accept = 'image/*'; input.multiple = true;
    input.setAttribute('aria-label', 'Add a picture');
    input.addEventListener('change', () => { void addFiles([...(input.files ?? [])]); input.value = ''; });
    add.append(input, el('span', undefined, 'Add a picture'), el('span', 'fb-hint', ' (or paste or drop one here)'));
    for (const t of [input, strip]) { t.addEventListener('keydown', (e) => e.stopPropagation()); t.addEventListener('keyup', (e) => e.stopPropagation()); }
    // paste anywhere on the page (the text box included) and drop onto the box
    document.addEventListener('paste', (e) => {
      if (!box!.isConnected) return;
      const files = imagesFromClipboard(e.clipboardData);
      if (files.length) { e.preventDefault(); void addFiles(files); }
    });
    box.addEventListener('dragover', (e) => { if (e.dataTransfer?.types?.includes('Files')) e.preventDefault(); });
    box.addEventListener('drop', (e) => {
      const files = [...(e.dataTransfer?.files ?? [])].filter((f) => f.type.startsWith('image/'));
      if (files.length) { e.preventDefault(); void addFiles(files); }
    });
    box.append(area, count, add, strip, picCount, el('div', 'fb-note', 'The report, your scoreboard name and the pictures are public on GitHub. Please do not include personal details.'));
    renderPics();
  }
  notify = o.toast; encoder = o.encode;
  const b = box, a = area!, cnt = count!;
  cnt.textContent = `${a.value.length} / ${MAX_DESCRIPTION}`;
  const send = () => {
    if (state === 'sending') return;
    const text = a.value.trim();
    if (!text) { o.toast('Type a description first'); a.focus(); return; }
    state = 'sending'; o.refresh();
    const body = buildFeedback({
      kind, description: text, version: o.version, sha: o.sha, track: o.track, device: o.device,
      ua: navigator.userAgent, screen: `${screen.width}x${screen.height}@${window.devicePixelRatio || 1} (${innerWidth}x${innerHeight})`,
      error: lastError(), name: o.name(), secret: o.secret(), images: pics.map((p) => p.pic),
    });
    const json = JSON.stringify(body);
    const tooBig = bodyProblem(json);
    if (tooBig) { state = 'idle'; o.refresh(); o.toast(tooBig, 6000); return; }
    const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(body.images ? { 'X-Feedback-Images': String(body.images.length) } : {}) };
    (o.fetch ?? ((u, i) => fetch(u, i)))('/api/feedback', { method: 'POST', headers, body: json })
      .then(async (r) => {
        const j = (await r.json().catch(() => null)) as { ok?: boolean; number?: number; images?: { uploaded: number; failed: number }; reasons?: string[]; error?: string } | null;
        if (r.ok && j?.ok) { state = 'sent'; a.value = ''; cnt.textContent = `0 / ${MAX_DESCRIPTION}`; pics.forEach((p) => URL.revokeObjectURL?.(p.src)); pics = []; renderPics(); o.toast(`Thanks! Filed as issue #${j.number ?? '?'} on GitHub${j.images?.failed ? ' (pictures could not be uploaded)' : ''}`, 6000); }
        else { state = 'idle'; o.toast(`Could not send the report: ${j?.reasons?.[0] ?? j?.error ?? `HTTP ${r.status}`}`, 6000); }
      })
      .catch(() => { state = 'idle'; o.toast('Could not send the report: offline?', 6000); })
      .finally(() => o.refresh());
  };
  return {
    title: 'Report a bug / request a feature',
    subtitle: `Files a public GitHub issue · v${o.version}${o.sha ? ` · ${o.sha}` : ''} · ${o.name() ? `as ${o.name()}` : 'anonymous'}`,
    body: () => b,
    entries: (): MenuEntry[] => [
      { kind: 'choice', id: 'fbKind', label: 'Type', options: [{ value: 'bug', label: 'Bug' }, { value: 'feature', label: 'Feature' }], get: () => kind, set: (v) => { kind = v as 'bug' | 'feature'; } },
      { kind: 'action', id: 'fbSend', label: state === 'sent' ? 'Sent · send another' : 'Send', note: state === 'sending' ? 'sending…' : undefined, disabled: state === 'sending', run: () => { if (state === 'sent') state = 'idle'; send(); } },
      { kind: 'back', id: 'back', label: 'Back' },
    ],
  };
}
