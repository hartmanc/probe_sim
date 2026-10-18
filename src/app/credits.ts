// Credits screen (main menu → Credits): third-party material the game uses, read from the data files at open time
// so new entries appear without code changes:
//   public/cars/field/credits.json         base 3D models of field cars (tools/cars/kit/import_model.py)
//   public/cars/field/models/credits.json  images used in the cars' decals (the kit's image decals)
//   public/audio/families/index.json       AI engine families (+ each family's engine.json `sources`)
//   public/cars/field/identity.json        team names for the car headings (optional)
// plus the race-photo reference line. Either credits file may be missing or change shape slightly: the parsers
// accept {cars: {num: entry | entry[]}}, {num: entry | entry[]} and [{number, ...}], and the two are merged by car
// number and source (pure functions, unit-tested). The card is a menu page: the body scrolls (wheel / touch), and
// "Scroll down / up" rows move it for pads and keys.
import type { MenuEntry, MenuPage } from './menu';

export interface CreditLine {
  /** What it is: '3D model', 'Decal image', 'Engine sound', 'Photos', … */
  kind: string;
  title?: string;
  author?: string;
  licence?: string;
  licenceUrl?: string;
  url?: string;
  note?: string;
}
export interface CarCredits { number: string; team?: string; lines: CreditLine[] }
export interface AudioCredits { family: string; character?: string; lines: CreditLine[] }
export interface CreditsData { cars: CarCredits[]; audio: AudioCredits[]; photos: CreditLine[]; about: string[] }

/** The race photos (reference only: liveries, numbers, car identities). */
export const PHOTO_CREDITS: CreditLine[] = [{
  kind: 'Photos',
  title: 'Twenty Ridiculous Years at Laguna',
  author: '24 Hours of Lemons (SmugMug gallery)',
  url: 'https://24hoursoflemons.smugmug.com/Race/Twenty-Ridiculous-Years-at-Laguna-October-2026',
  note: 'used as reference only (liveries, numbers, car identities); no photos are shipped',
}];

// ---------------------------------------------------------------- parsing (pure)

const str = (v: unknown): string | undefined => (typeof v === 'string' && v.trim() ? v.trim() : typeof v === 'number' ? String(v) : undefined);
const pick = (o: Record<string, unknown>, keys: string[]) => { for (const k of keys) { const v = str(o[k]); if (v) return v; } return undefined; };
const isUrl = (s: string | undefined) => !!s && /^https?:\/\//i.test(s);

/** One credit entry of any of the files, in a common shape (null when it carries nothing to credit). */
export function creditLine(raw: unknown, kind: string): CreditLine | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const o = raw as Record<string, unknown>;
  const src = pick(o, ['url', 'source_url', 'link', 'href', 'source']);
  const url = isUrl(src) ? src : pick(o, ['url', 'source_url', 'link', 'href']);
  const title = pick(o, ['title', 'name', 'model']) ?? (!isUrl(src) ? src : undefined);
  const line: CreditLine = {
    kind: pick(o, ['kind', 'type']) ?? kind,
    title,
    author: pick(o, ['author', 'by', 'creator', 'artist', 'uploader', 'owner']),
    licence: pick(o, ['licence', 'license']),
    licenceUrl: pick(o, ['licence_url', 'license_url', 'licenceUrl', 'licenseUrl']),
    url: isUrl(url) ? url : undefined,
    note: pick(o, ['changes', 'note', 'notes']),
  };
  for (const k of Object.keys(line) as (keyof CreditLine)[]) if (line[k] === undefined) delete line[k];
  return line.title || line.author || line.url ? line : null;
}

/** Credits of one cars file, by car number. Accepts {cars: …}, {num: entry | entry[]} or [{number, …}]. */
export function carCreditsFrom(raw: unknown, kind: string): Map<string, CreditLine[]> {
  const out = new Map<string, CreditLine[]>();
  const add = (num: string | undefined, v: unknown) => {
    if (!num) return;
    for (const e of Array.isArray(v) ? v : [v]) {
      const l = creditLine(e, kind);
      if (l) { const a = out.get(num) ?? []; a.push(l); out.set(num, a); }
    }
  };
  if (!raw || typeof raw !== 'object') return out;
  if (Array.isArray(raw)) {
    for (const e of raw) if (e && typeof e === 'object') add(pick(e as Record<string, unknown>, ['number', 'car', 'num', 'car_number']), e);
    return out;
  }
  const o = raw as Record<string, unknown>;
  if (o.cars && typeof o.cars === 'object') return carCreditsFrom(o.cars, kind);
  for (const [k, v] of Object.entries(o)) if (v && typeof v === 'object') add(k, v);
  return out;
}

const lineKey = (l: CreditLine) => [l.kind, l.url ?? '', l.url ? '' : l.title ?? '', l.author ?? '', l.licence ?? ''].join('|').toLowerCase();

/** Merge per-car credits from several files: one entry per car number, duplicate sources dropped, numeric order. */
export function mergeCarCredits(maps: Map<string, CreditLine[]>[], teams: Record<string, string> = {}): CarCredits[] {
  const by = new Map<string, CreditLine[]>();
  for (const m of maps) {
    for (const [num, lines] of m) {
      const cur = by.get(num) ?? [];
      const seen = new Set(cur.map(lineKey));
      for (const l of lines) { const k = lineKey(l); if (!seen.has(k)) { seen.add(k); cur.push(l); } }
      by.set(num, cur);
    }
  }
  return [...by.entries()]
    .sort(([a], [b]) => (Number(a) - Number(b)) || a.localeCompare(b))
    .map(([number, lines]) => ({ number, ...(teams[number] ? { team: teams[number] } : {}), lines }));
}

/** Engine-sound credits: per family, the index entry's `sources` and its engine.json `sources`, deduplicated. */
export function audioCreditsFrom(index: unknown, engines: Record<string, unknown> = {}): AudioCredits[] {
  if (!index || typeof index !== 'object') return [];
  const fams = (index as { families?: unknown }).families;
  if (!fams || typeof fams !== 'object') return [];
  const out: AudioCredits[] = [];
  for (const [id, entry] of Object.entries(fams as Record<string, unknown>)) {
    const e = (entry && typeof entry === 'object' ? entry : {}) as Record<string, unknown>;
    const lists = [e.sources, (engines[id] as { sources?: unknown } | undefined)?.sources];
    const seen = new Set<string>();
    const lines: CreditLine[] = [];
    for (const list of lists) {
      if (!Array.isArray(list)) continue;
      for (const s of list) {
        if (s && typeof s === 'object' && (s as { skip?: unknown }).skip === true) continue;
        const l = creditLine(s, 'Engine sound');
        if (!l) continue;
        const k = (l.url ?? lineKey(l)).toLowerCase();
        if (!seen.has(k)) { seen.add(k); lines.push(l); }
      }
    }
    if (lines.length) out.push({ family: id, ...(str(e.character) ? { character: str(e.character) } : {}), lines });
  }
  return out;
}

/** Team names by number from identity.json (array of {number, team} or {cars: […]}). */
export function teamsFrom(identity: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  const list = Array.isArray(identity) ? identity : identity && typeof identity === 'object' && Array.isArray((identity as { cars?: unknown }).cars) ? (identity as { cars: unknown[] }).cars : [];
  for (const c of list) {
    if (!c || typeof c !== 'object') continue;
    const n = pick(c as Record<string, unknown>, ['number']), t = pick(c as Record<string, unknown>, ['team']);
    if (n && t) out[n] = t;
  }
  return out;
}

// ---------------------------------------------------------------- loading

type FetchFn = (url: string) => Promise<{ ok: boolean; json(): Promise<unknown> }>;
const defaultFetch: FetchFn = (u) => fetch(u, { cache: 'no-cache' });

const getJson = (f: FetchFn, url: string): Promise<unknown> => f(url).then((r) => (r.ok ? r.json() : null)).catch(() => null);

/** Fetch every credits source (each optional) and build the credits. */
export async function loadCredits(fetchFn: FetchFn = defaultFetch, base = ''): Promise<CreditsData> {
  const [models, decals, index, identity] = await Promise.all([
    getJson(fetchFn, base + 'cars/field/credits.json'),
    getJson(fetchFn, base + 'cars/field/models/credits.json'),
    getJson(fetchFn, base + 'audio/families/index.json'),
    getJson(fetchFn, base + 'cars/field/identity.json'),
  ]);
  const engines: Record<string, unknown> = {};
  const fams = (index as { families?: Record<string, { engine?: unknown }> } | null)?.families;
  if (fams && typeof fams === 'object') {
    const famBase = str((index as { base?: unknown }).base) ?? 'audio/families/';
    await Promise.all(Object.entries(fams).map(async ([id, e]) => {
      const eng = str(e?.engine);
      if (eng) engines[id] = await getJson(fetchFn, base + famBase + eng);
    }));
  }
  const about = [models, decals].map((m) => (m && typeof m === 'object' ? str((m as { about?: unknown }).about) : undefined)).filter((s): s is string => !!s);
  return {
    cars: mergeCarCredits([carCreditsFrom(models, '3D model'), carCreditsFrom(decals, 'Decal image')], teamsFrom(identity)),
    audio: audioCreditsFrom(index, engines),
    photos: PHOTO_CREDITS,
    about,
  };
}

// ---------------------------------------------------------------- the card

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function lineEl(l: CreditLine, showKind = true): HTMLElement {
  const row = el('div', 'cr-line');
  if (showKind) row.append(el('span', 'cr-kind', l.kind));
  const t = l.url ? el('a', 'cr-title', l.title ?? l.url) : el('span', 'cr-title', l.title ?? '');
  if (t instanceof HTMLAnchorElement) { t.href = l.url!; t.target = '_blank'; t.rel = 'noopener noreferrer'; }
  if (t.textContent) row.append(t);
  if (l.author) row.append(el('span', 'cr-by', `by ${l.author}`));
  if (l.licence) {
    const lic = l.licenceUrl && isUrl(l.licenceUrl) ? el('a', 'cr-lic', l.licence) : el('span', 'cr-lic', l.licence);
    if (lic instanceof HTMLAnchorElement) { lic.href = l.licenceUrl!; lic.target = '_blank'; lic.rel = 'noopener noreferrer'; }
    row.append(lic);
  }
  if (l.note) row.append(el('div', 'cr-note', l.note));
  return row;
}

/** The credits as DOM (pure rendering of CreditsData). */
export function renderCredits(d: CreditsData, box: HTMLElement): void {
  const parts: HTMLElement[] = [];
  const section = (title: string, intro?: string) => {
    const s = el('section', 'cr-section');
    s.append(el('h3', 'cr-h', title));
    if (intro) s.append(el('div', 'cr-intro', intro));
    parts.push(s);
    return s;
  };
  const ph = section('Race photos');
  for (const l of d.photos) ph.append(lineEl(l, false));
  const cars = section('Field cars', d.about.join(' ') || undefined);
  if (!d.cars.length) cars.append(el('div', 'cr-intro', 'No third-party car material listed yet.'));
  for (const c of d.cars) {
    const g = el('div', 'cr-group');
    g.append(el('div', 'cr-gh', `#${c.number}${c.team ? ` · ${c.team}` : ''}`));
    for (const l of c.lines) g.append(lineEl(l));
    cars.append(g);
  }
  const au = section('AI engine sounds', 'Loops cut from onboard videos; each family plays for several cars.');
  if (!d.audio.length) au.append(el('div', 'cr-intro', 'No engine-sound sources listed yet.'));
  for (const a of d.audio) {
    const g = el('div', 'cr-group');
    g.append(el('div', 'cr-gh', `${a.family.replace(/_/g, ' ')}${a.character ? ` · ${a.character}` : ''}`));
    for (const l of a.lines) g.append(lineEl(l, false));
    au.append(g);
  }
  box.replaceChildren(...parts);
}

let box: HTMLElement | null = null;
let loading: Promise<void> | null = null;

const scrollBox = (dir: 1 | -1) => { if (box) box.scrollBy({ top: dir * Math.max(80, box.clientHeight * 0.8), behavior: 'auto' }); };

/** Main menu → Credits. The data is re-read every time the page opens (new entries show up without a reload). */
export function creditsPage(): MenuPage {
  if (!box) { box = el('div', 'credits'); box.tabIndex = -1; }
  const b = box;
  if (!loading) {
    if (!b.childElementCount) b.replaceChildren(el('div', 'cr-intro', 'Loading credits…'));
    loading = loadCredits().then((d) => renderCredits(d, b)).catch((e) => { b.replaceChildren(el('div', 'cr-intro', `Could not load the credits: ${String(e)}`)); })
      .finally(() => { loading = null; });
  }
  b.scrollTop = 0;
  return {
    title: 'Credits',
    subtitle: 'Third-party material in this game',
    // the menu re-renders the body on every change; keep the same element and its scroll position
    body: () => { const top = b.scrollTop; queueMicrotask(() => { b.scrollTop = top; }); return b; },
    entries: (): MenuEntry[] => [
      { kind: 'action', id: 'crDown', label: 'Scroll down ▾', run: () => scrollBox(1) },
      { kind: 'action', id: 'crUp', label: 'Scroll up ▴', run: () => scrollBox(-1) },
      { kind: 'back', id: 'back', label: 'Back' },
    ],
  };
}
