// The Cars page, pure parts (unit-tested): the order of the field, award matching helpers, the card's text and the
// scripted engine (cold start, idle with throttle blips). No DOM, no three.
//
// Order (owner, 31 Oct 2026): the Index of Effluency winner, then the class winners A, B, C, then every other award
// winner in the award page's order, then everyone else in finishing order.

export interface IdentityRow {
  number: string; id?: string; team: string; class?: string; finish?: number | null; class_finish?: number | null;
  laps?: number; best_lap_s?: number; make?: string; model?: string; year?: number;
  engine?: { family?: string; cylinders?: number; layout?: string; exhaust_note?: string; redline_rpm?: number };
  [k: string]: unknown;
}
/** public/cars/field/<track>/awards.json: cars in the award page's order. */
export interface AwardEntry { number: string; id: string; awards: string[] }
export interface CreditRow { title?: string; author?: string; licence?: string; licence_url?: string; url?: string; changes?: string }
export interface PhotoRow { file: string; page_url?: string; owner?: boolean }

/** The field key of a row (pace.json `id`, else the number). */
export const keyOf = (r: { id?: unknown; number: unknown }): string => String(r.id != null && String(r.id) !== '' ? r.id : r.number);

export type AwardClass = 'index' | 'A' | 'B' | 'C' | 'other';
export function awardClass(award: string): AwardClass {
  if (/index of effluency/i.test(award)) return 'index';
  const m = /^winner,?\s+class\s+([abc])\b/i.exec(award.trim());
  return m ? (m[1].toUpperCase() as AwardClass) : 'other';
}

export interface ViewerCar { key: string; row: IdentityRow; awards: string[] }

/**
 * The field in viewing order. `hasModel(key)` filters (cars without a model are counted in `skipped`, not shown).
 * `awards` is the page's list in page order; a car appears once, at its best group.
 */
export function viewerOrder(identity: readonly IdentityRow[], awards: readonly AwardEntry[], hasModel: (key: string) => boolean): { cars: ViewerCar[]; skipped: number } {
  const byKey = new Map<string, IdentityRow>();
  for (const r of identity) byKey.set(keyOf(r), r);
  const awardsOf = new Map<string, string[]>();
  const pageOrder: string[] = [];
  for (const a of awards) {
    if (!byKey.has(a.id)) continue;
    if (!awardsOf.has(a.id)) { awardsOf.set(a.id, []); pageOrder.push(a.id); }
    awardsOf.get(a.id)!.push(...a.awards);
  }
  const placed = new Set<string>();
  const order: string[] = [];
  const add = (k: string) => { if (!placed.has(k)) { placed.add(k); order.push(k); } };
  for (const group of ['index', 'A', 'B', 'C'] as AwardClass[]) {
    for (const k of pageOrder) if (awardsOf.get(k)!.some((a) => awardClass(a) === group)) add(k);
  }
  for (const k of pageOrder) add(k);
  const rest = identity.map(keyOf).filter((k) => !placed.has(k));
  const fin = (k: string) => { const f = byKey.get(k)!.finish; return typeof f === 'number' && f > 0 ? f : Number.POSITIVE_INFINITY; };
  rest.sort((a, b) => fin(a) - fin(b));
  for (const k of rest) add(k);
  const cars: ViewerCar[] = [];
  let skipped = 0;
  for (const k of order) {
    if (!hasModel(k)) { skipped++; continue; }
    cars.push({ key: k, row: byKey.get(k)!, awards: awardsOf.get(k) ?? [] });
  }
  return { cars, skipped };
}

/** Index of the car with this number (typed digits), -1 when none. */
export function indexByNumber(cars: readonly ViewerCar[], digits: string): number {
  if (!digits) return -1;
  return cars.findIndex((c) => String(c.row.number) === digits);
}

// ---------------------------------------------------------------- card text

export function ordinal(n: number): string {
  const m100 = n % 100, m10 = n % 10;
  const s = m100 >= 11 && m100 <= 13 ? 'th' : m10 === 1 ? 'st' : m10 === 2 ? 'nd' : m10 === 3 ? 'rd' : 'th';
  return `${n}${s}`;
}

/** m:ss.sss ("1:48.150"); '–' when there is no lap. */
export function lapText(s: number | undefined | null): string {
  if (typeof s !== 'number' || !isFinite(s) || s <= 0) return '–';
  const ms = Math.round(s * 1000);
  const m = Math.floor(ms / 60000), rem = ms - m * 60000;
  return `${m}:${(rem / 1000).toFixed(3).padStart(6, '0')}`;
}

export interface Card {
  position: string;
  number: string;
  team: string;
  car: string;
  cls: string;
  awards: string[];
  overall: string;
  classRank: string;
  laps: string;
  fastest: string;
  model: { text: string; title?: string; titleUrl?: string; author?: string; licence?: string; licenceUrl?: string; changes?: string };
  photos: { n: number; url: string }[];
  ownerPhotos: number;
}

/** The field size for "P7 of 45": the entry list, or the last finishing place when that is higher. */
export function fieldSize(identity: readonly IdentityRow[]): number {
  return Math.max(identity.length, ...identity.map((r) => (typeof r.finish === 'number' ? r.finish : 0)));
}

/** Cars per class in the entry list (identity rows). */
export function classSizes(identity: readonly IdentityRow[]): Record<string, number> {
  const n: Record<string, number> = {};
  for (const r of identity) if (typeof r.class === 'string' && r.class) n[r.class] = (n[r.class] ?? 0) + 1;
  return n;
}

export function cardFor(car: ViewerCar, index: number, count: number, total: number, credit: CreditRow | null | undefined, photos: readonly PhotoRow[] | undefined, classes: Record<string, number> = {}): Card {
  const r = car.row;
  const name = [r.year, r.make, r.model].filter((x) => x !== undefined && x !== null && x !== '').join(' ');
  const cls = typeof r.class === 'string' ? r.class : '';
  const hasFinish = typeof r.finish === 'number' && r.finish > 0;
  const hasCf = typeof r.class_finish === 'number' && r.class_finish > 0;
  const c = credit && (credit.title || credit.author) ? credit : null;
  return {
    position: `${index + 1} / ${count}`,
    number: String(r.number),
    team: r.team,
    car: name,
    cls,
    awards: car.awards,
    overall: hasFinish ? `P${r.finish} of ${total}` : '–',
    classRank: hasCf && cls ? `P${r.class_finish} of ${classes[cls] ?? '?'} in ${cls}` : '–',
    laps: typeof r.laps === 'number' ? String(r.laps) : '–',
    fastest: lapText(r.best_lap_s),
    model: c
      ? { text: 'Model', title: c.title, titleUrl: c.url, author: c.author, licence: c.licence, licenceUrl: c.licence_url, changes: c.changes }
      : { text: 'Built for the sim' },
    photos: (photos ?? []).filter((p) => !p.owner && p.page_url).map((p, i) => ({ n: i + 1, url: p.page_url! })),
    ownerPhotos: (photos ?? []).filter((p) => p.owner).length,
  };
}

/** credits.json `cars` as a dict by field key or a list of rows with an id; the row for this car, else null. */
export function creditFor(cars: unknown, key: string): CreditRow | null {
  if (Array.isArray(cars)) return (cars.find((c) => c && String((c as { id?: unknown }).id) === key) as CreditRow | undefined) ?? null;
  if (cars && typeof cars === 'object') return ((cars as Record<string, CreditRow>)[key]) ?? null;
  return null;
}

/** Links only to http(s): the data files are ours, but a link on the page is never built from anything else. */
export const safeUrl = (u: string | undefined): string | null => (u && /^https?:\/\//i.test(u) ? u : null);

// ---------------------------------------------------------------- scripted engine

export interface EngineFrame { rpm: number; throttle: number }
/** Cold start: crank to CRANK_END, catch, one rev to REV_RPM, settle to idle by SETTLE_END (s from showing the car). */
export const CRANK_END = 1.0, CATCH_END = 1.3, REV_UP_END = 1.9, REV_HOLD_END = 2.1, SETTLE_END = 3.2;
export const REV_RPM = 3000, CRANK_RPM = 220;
/** Warming up after the cold start: throttle blips of random size, with short idle gaps (owner, 31 Oct 2026). */
export const PEAK_MIN = 2000, PEAK_MAX = 4000;
export interface Blip { t0: number; peak: number; rise: number; fall: number }
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (x: number) => { const t = clamp01(x); return t * t * (3 - 2 * t); };

/**
 * The rpm and throttle at time t for a car idling at `idle` rpm. `blips` are the throttle blips after the cold start.
 */
export function engineAt(t: number, idle: number, blips: readonly Blip[]): EngineFrame {
  if (t < 0) return { rpm: 0, throttle: 0 };
  if (t < CRANK_END) return { rpm: CRANK_RPM * (0.55 + 0.45 * smooth(t / 0.3)) * (1 + 0.12 * Math.sin(t * 38)), throttle: 0 };
  if (t < CATCH_END) { const u = smooth((t - CRANK_END) / (CATCH_END - CRANK_END)); return { rpm: CRANK_RPM + (1400 - CRANK_RPM) * u, throttle: 0.55 }; }
  if (t < REV_UP_END) { const u = smooth((t - CATCH_END) / (REV_UP_END - CATCH_END)); return { rpm: 1400 + (REV_RPM - 1400) * u, throttle: 0.85 }; }
  if (t < REV_HOLD_END) return { rpm: REV_RPM, throttle: 0.85 };
  if (t < SETTLE_END) { const u = smooth((t - REV_HOLD_END) / (SETTLE_END - REV_HOLD_END)); return { rpm: REV_RPM + (idle - REV_RPM) * u, throttle: 0 }; }
  for (const b of blips) {
    const d = t - b.t0;
    if (d >= 0 && d < b.rise + b.fall) {
      const up = smooth(d / b.rise), down = d < b.rise ? 0 : smooth((d - b.rise) / b.fall);
      const k = up * (1 - down);
      return { rpm: idle + (b.peak - idle) * k, throttle: d < b.rise ? 0.4 + 0.5 * up : 0 };
    }
  }
  return { rpm: idle, throttle: 0.06 };
}

/** The blip that starts 0.5 to 1.5 s after `after` (the end of the last one): peak 2,000 to 4,000 rpm, its own rise and fall. `rand` gives 0..1. */
export function makeBlip(after: number, rand: () => number): Blip {
  return { t0: after + 0.5 + rand(), peak: PEAK_MIN + (PEAK_MAX - PEAK_MIN) * rand(), rise: 0.12 + 0.35 * rand(), fall: 0.25 + 0.9 * rand() };
}

// ---------------------------------------------------------------- parking on a cambered road

export interface PlaneFit { a: number; b: number; c: number; residuals: number[] }
/**
 * Least-squares plane z = a + b·u + c·v through points [u, v, z] (u forward, v left, metres; the car's origin is (0, 0)).
 * residuals[i] = z_i − plane(u_i, v_i). Needs at least three points that are not in a line.
 */
export function fitPlane(pts: readonly (readonly [number, number, number])[]): PlaneFit {
  let n = 0, su = 0, sv = 0, sz = 0, suu = 0, suv = 0, svv = 0, suz = 0, svz = 0;
  for (const [u, v, z] of pts) { n++; su += u; sv += v; sz += z; suu += u * u; suv += u * v; svv += v * v; suz += u * z; svz += v * z; }
  // normal equations [n su sv; su suu suv; sv suv svv] [a b c]ᵀ = [sz suz svz]ᵀ, solved by Cramer's rule
  const det = (m: number[][]) => m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  const A = [[n, su, sv], [su, suu, suv], [sv, suv, svv]];
  const d = det(A);
  if (Math.abs(d) < 1e-12) return { a: n ? sz / n : 0, b: 0, c: 0, residuals: pts.map(([, , z]) => z - (n ? sz / n : 0)) };
  const col = (k: number) => A.map((row, i) => row.map((x, j) => (j === k ? [sz, suz, svz][i] : x)));
  const a = det(col(0)) / d, b = det(col(1)) / d, c = det(col(2)) / d;
  return { a, b, c, residuals: pts.map(([u, v, z]) => z - (a + b * u + c * v)) };
}

/** How far the car's plane is lifted (m) so its lowest wheel contact is exactly on the surface: the smallest residual. */
export const seatOffset = (fit: PlaneFit): number => Math.min(...fit.residuals);

// ---------------------------------------------------------------- touch gestures

export interface PointerSample { t: number; x: number; y: number }
/** A flick pages: at least FLICK_PX of travel within FLICK_MS, or at least FLICK_FAST_PX at FLICK_SPEED px/ms or more; mostly horizontal. */
export const FLICK_PX = 50, FLICK_MS = 350, FLICK_FAST_PX = 30, FLICK_SPEED = 0.6, FLICK_RATIO = 2;

/**
 * What a finished touch gesture was. `tracks` holds one list of samples per finger that was down. A second finger
 * (a pinch) is never a swipe. One finger: a quick, mostly horizontal flick is a swipe (left = next car, right = previous);
 * a slow or diagonal drag is the orbit.
 */
export function classifyGesture(tracks: readonly (readonly PointerSample[])[]): 'orbit' | 'next' | 'prev' {
  if (tracks.length !== 1 || tracks[0].length < 2) return 'orbit';
  const s = tracks[0], a = s[0], b = s[s.length - 1];
  const dx = b.x - a.x, dy = b.y - a.y, dt = Math.max(1, b.t - a.t), adx = Math.abs(dx);
  if (adx < Math.abs(dy) * FLICK_RATIO) return 'orbit';
  const quick = adx >= FLICK_PX && dt <= FLICK_MS;
  const fast = adx >= FLICK_FAST_PX && adx / dt >= FLICK_SPEED;
  if (!quick && !fast) return 'orbit';
  return dx < 0 ? 'next' : 'prev';
}

/** The compact (phone) card: line 1 and line 2 of the strip. */
export function stripLines(c: Pick<Card, 'number' | 'team' | 'car' | 'cls' | 'overall' | 'classRank' | 'laps' | 'fastest'>): [string, string] {
  return [
    `#${c.number} ${c.team} · ${c.car}${c.cls ? ` · Class ${c.cls}` : ''}`,
    [c.overall, c.classRank, `${c.laps} laps`, c.fastest].join(' · '),
  ];
}

// ---------------------------------------------------------------- the camera distance on a phone

export const DESKTOP_DISTANCE = 7.5;
/** The reference box (m): a car's length, height and width, centred on the target; it is the same for every car, so sizes compare. */
export const REF_LENGTH = 4.6, REF_HEIGHT = 1.8, REF_WIDTH = 1.8, VIEW_FOV_DEG = 38;
/** The orbit elevation (rad) the page opens with, and the share of the clear area the projected box may take. */
export const DEFAULT_ELEVATION = 0.2;
export const FIT_HEIGHT = 0.72, FIT_WIDTH = 0.85;
export const FIT_YAWS_DEG = [0, 45, 90] as const;

/** The reference box seen from a camera at distance d, elevation el, looking at its centre; yaw turns the box (0 side-on, 90 end-on). NDC extents (y up). */
export function projectBox(d: number, el: number, yawDeg: number, aspect: number): { x0: number; x1: number; y0: number; y1: number } {
  const t = Math.tan((VIEW_FOV_DEG * Math.PI) / 360);
  const cy = Math.cos(yawDeg * Math.PI / 180), sy = Math.sin(yawDeg * Math.PI / 180);
  const C = [0, d * Math.sin(el), d * Math.cos(el)];            // camera (azimuth 0), target at the origin
  const F = [-C[0] / d, -C[1] / d, -C[2] / d];
  const R = [1, 0, 0];                                            // F x up, normalised: along +x for azimuth 0
  const U = [R[1] * F[2] - R[2] * F[1], R[2] * F[0] - R[0] * F[2], R[0] * F[1] - R[1] * F[0]];
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const a of [-1, 1]) for (const b of [-1, 1]) for (const c of [-1, 1]) {
    const lx = a * REF_LENGTH / 2, ly = b * REF_HEIGHT / 2, lz = c * REF_WIDTH / 2;
    const P = [lx * cy + lz * sy, ly, -lx * sy + lz * cy];
    const z = (P[0] - C[0]) * F[0] + (P[1] - C[1]) * F[1] + (P[2] - C[2]) * F[2];
    const x = (P[0] * R[0] + P[1] * R[1] + P[2] * R[2]) / z / (t * aspect), y = (P[0] * U[0] + P[1] * U[1] + P[2] * U[2]) / z / t;
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
  }
  return { x0, x1, y0, y1 };
}

/**
 * The default camera on a phone. Not compact: the constant 7.5 m, no shift. Compact: the nearest distance at which the
 * reference box (4.6 x 1.8 x 1.8 m), seen through the opening elevation at yaw 0, 45 and 90 degrees (side-on to end-on),
 * is at most 72 % of the clear height and 85 % of the clear width (the clear area lies between the title row on top, the
 * strip below and the chevrons at the sides), and `shiftPx`, how far the image must move up so the middle of the box's
 * height range sits at the centre of the clear area. Depends on the viewport only, never on the car.
 */
export function viewFit(compact: boolean, w: number, h: number, stripH: number, titleH: number, chevW: number, elevation = DEFAULT_ELEVATION): { distance: number; shiftPx: number } {
  if (!compact) return { distance: DESKTOP_DISTANCE, shiftPx: 0 };
  const clearH = Math.max(40, h - stripH - titleH), clearW = Math.max(40, w - 2 * chevW);
  const aspect = w / h;
  const union = (d: number) => {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const yaw of FIT_YAWS_DEG) { const e = projectBox(d, elevation, yaw, aspect); x0 = Math.min(x0, e.x0); x1 = Math.max(x1, e.x1); y0 = Math.min(y0, e.y0); y1 = Math.max(y1, e.y1); }
    return { x0, x1, y0, y1 };
  };
  const fits = (d: number) => { const u = union(d); return ((u.y1 - u.y0) * h) / 2 <= FIT_HEIGHT * clearH && ((u.x1 - u.x0) * w) / 2 <= FIT_WIDTH * clearW; };
  let lo = 2, hi = 40;
  for (let k = 0; k < 40; k++) { const m = (lo + hi) / 2; if (fits(m)) hi = m; else lo = m; }
  const u = union(hi), mid = (u.y0 + u.y1) / 2;
  const boxMidPx = h / 2 - (mid * h) / 2, clearMidPx = titleH + clearH / 2;
  return { distance: hi, shiftPx: boxMidPx - clearMidPx };
}

export const viewDistance = (compact: boolean, w: number, h: number, stripH: number, titleH: number, chevW: number, elevation = DEFAULT_ELEVATION): number =>
  viewFit(compact, w, h, stripH, titleH, chevW, elevation).distance;

/** Pixels the image must move up (negative: down) so the car sits in the clear area's centre rather than the viewport's. */
export const clearAreaShift = (stripH: number, titleH: number): number => (stripH - titleH) / 2;
