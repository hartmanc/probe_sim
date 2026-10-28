// The AI field: pace.json / identity.json types, per-car CarSpec construction (Probe spec + identity
// overrides + one pace scale), the per-car performance model the driver uses (acceleration table,
// brake gain, understeer feed-forward) and the per-car target speed profile.
//
// Field keys (22 Oct 2026): a car's identity row and its model are found by its `id` (pace.json cars[].id, absent =
// its number; `fieldKey`). identity.json / models.json rows are keyed the same way (`id`, else `number`), so the Laguna
// files, which have no ids, resolve by number exactly as before. A circuit's own field (Buttonwillow) gives a car whose
// number is a different Laguna car's an id of its own ("0_bw"), so it never picks up that car's identity or model.
// A car may name its model explicitly with `model_id` (pace row, else identity row; modelKey): a renumbered car reuses
// its earlier model.

import { cbrt as dcbrt, exp as dexp, log as dlog, pow as dpow } from '../dmath';   // the AI computes like the physics: the same bits on every host and engine
import { loadCarSpec, type CarSpec } from '../spec';
import { Vehicle } from '../vehicle';
import { createFlatSurface } from '../devtrack';
import type { RaceLine } from './line';
import { Rng, hashSeed } from './rng';

/** Bump whenever the AI driver or the calibration changes behaviour (pace.json scales are then stale). */
export const AI_VERSION = 8; // 8: an understeering car (front slip > 2x its peak) unwinds the lock instead of holding full lock. 7: lateral mu capped at 1.20 (pace above it from power); profiles credit banking and the crest/dip load; driver margins 0.97 lateral / 0.85 braking, grip limiter at 1.5x, engine-braking blip for sliding RWD cars. 6: CG lowered with the fitted grip (T/2h >= 1.15 x lateral mu: quick cars rolled over at T2 on the painted-road track). 5: pace fit split into grip (corners) and power (straights): power follows the powertrain
// 4: per-stint driver pace (each race draws one real stint per car), stint outlier rules
// 3: #49 Mayflower re-specced as a Honda K24 swap (owner), recalibrated

// ------------------------------------------------------------------ data files

/** One car in public/cars/field/pace.json. */
export interface PaceCar {
  /** Where targetLap comes from when it is not this circuit's own result (tools/race/pace_sonoma.ts). */
  targetSource?: string;
  /** The car's identity / model key (identity.json and models.json rows by `id`, else by number). Absent = `number`
   *  (Laguna). A circuit's own field sets it on every car; a number that belongs to a different Laguna car gets
   *  "<number>_<track>" (Buttonwillow "0_bw", tools/race/pace_track.ts --own). */
  id?: string;
  /** The models.json row this car shows when it is not its own id: a car renumbered since an earlier event reuses that
   *  event's model (Buttonwillow #6 Team Tinyvette = Laguna #8: "8"). Resolution: model_id, then id, then number. */
  model_id?: string;
  number: string;
  team: string;
  class: string;            // 'A' | 'B' | 'C'
  grid: number;             // real starting position (1-based)
  finish: number;           // real overall finishing position
  classFinish?: number;
  lapsCompleted: number;    // real laps completed in the race
  greenLaps: number;        // laps used for the pace statistics
  targetLap: number;        // s: median green non-pit lap (outliers > 1.3 x median dropped)
  bestLap: number;          // s
  sigma: number;            // s: robust sigma of those laps (1.4826 x MAD)
  aggression: 0 | 1 | 2;    // 0 calm, 1 normal, 2 aggressive
  player?: boolean;         // true for the player's car (#619), kept for reference
  scale?: number;           // fitted pace scale (tools/race/calibrate_field.ts)
  achievedLap?: number;     // AI clean lap with that scale, s
  /** resolved car (drive, engine, gearbox, mass, power with the scale) for the app and the audio stream */
  resolved?: ResolvedCar;
  /** the car's real pit-to-pit stints (one driver each); a race draws one of them with `drawPace` */
  stints?: PaceStint[];
  /**
   * The car's solo lap against its pace scale, [scale, lap s] by rising scale with the lap falling (AI round 1, 27 Oct
   * 2026; tools/race/pace_curve.ts: every calibration of this car, its own fit and its stints' at the four pace quantiles
   * 0.5 / 0.35 / 0.25 / 0.15, made monotone). The AI strength setting reads it (strengthPace); absent = LAP_SCALE_SLOPE.
   */
  curve?: [number, number][];
}

/**
 * One pit-to-pit stint of a car's real race, i.e. one driver's run (pace.json cars[].stints[]). Laps
 * dropped before the statistics: non-green laps, the pit lap, the out lap after it (and the race's first
 * lap), laps slower than 1.2 x the stint's own median or 1.3 x the car's median, and anything faster
 * than 0.97 x the official best. A stint needs 5 clean laps to count.
 */
export interface PaceStint {
  index: number;            // 0-based, in race order
  laps: number;             // clean laps the statistics come from
  firstLap: number;         // real lap number the stint started on
  targetLap: number;        // s: that driver's pace = median of the stint's clean laps
  bestLap: number;          // s
  sigma: number;            // s: 1.4826 x MAD of the stint's clean laps
  scale?: number;           // fitted pace scale for targetLap (calibrate_field.ts)
  achievedLap?: number;     // AI solo lap with that scale, s
}

/** The driver pace a race uses for one car (see drawPace). */
export interface DrawnPace {
  /** stint index drawn, -1 when the car has no eligible stint (car-level pace used) */
  stint: number;
  of: number;
  targetLap: number;
  bestLap: number;
  sigma: number;
  /** fitted scale for that pace, null when not calibrated (the director then estimates it) */
  scale: number | null;
  /** the solo lap the calibration measured at that scale, null when not calibrated */
  achievedLap: number | null;
}

/** The AI strength choices (player setting, AI round 1): every AI car's clean solo lap is its target / strength. */
export const AI_STRENGTHS: readonly number[] = [0.9, 0.95, 1, 1.05, 1.1];
/** d ln(lap) / d ln(scale) for a car without a curve (the pooled median of the four fields' curves, tools/race/pace_curve.ts). */
export const LAP_SCALE_SLOPE = -0.35;

/** ln(lap) of a car's curve at ln(scale) `x`: piecewise linear in (ln scale, ln lap) between its points, beyond the
 *  ends along the least-squares slope of all its points (never rising). */
function curveLn(xs: Float64Array, ys: Float64Array, b: number, x: number): number {
  const n = xs.length;
  if (x <= xs[0]) return ys[0] + b * (x - xs[0]);
  if (x >= xs[n - 1]) return ys[n - 1] + b * (x - xs[n - 1]);
  let k = 1;
  while (xs[k] < x) k++;
  const f = (x - xs[k - 1]) / (xs[k] - xs[k - 1]);
  return ys[k - 1] + f * (ys[k] - ys[k - 1]);
}

/**
 * The AI strength map (AI round 1, Part B): the pace scale at which a car whose calibrated pace is `scale0` (its solo lap
 * `lap0` there, built to `target0`) laps target0 / strength, from its lap(scale) curve (PaceCar.curve) anchored on its own
 * point (the stint's offset from the car's curve is kept). Strength 1 returns the inputs bit for bit. The scale stays in
 * [PACE_MIN, PACE_MAX]: a car whose curve cannot reach the lap inside that range gets the cap and the lap its curve gives
 * there (`capped`), so it races at what the caps allow, and its pace hint (paceHint) is that lap.
 */
export function strengthPace(curve: readonly (readonly [number, number])[] | undefined, scale0: number, lap0: number, target0: number, strength: number):
  { scale: number; lap: number; targetLap: number; capped: boolean } {
  if (strength === 1) return { scale: scale0, lap: lap0, targetLap: target0, capped: false };
  const T = target0 / strength;
  let xs: Float64Array, ys: Float64Array, b = LAP_SCALE_SLOPE;
  if (curve && curve.length >= 2) {
    xs = Float64Array.from(curve, (p) => dlog(p[0])); ys = Float64Array.from(curve, (p) => dlog(p[1]));
    const n = xs.length;
    let mx = 0, my = 0;
    for (let k = 0; k < n; k++) { mx += xs[k]; my += ys[k]; }
    mx /= n; my /= n;
    let sxy = 0, sxx = 0;
    for (let k = 0; k < n; k++) { sxy += (xs[k] - mx) * (ys[k] - my); sxx += (xs[k] - mx) * (xs[k] - mx); }
    b = sxx > 1e-12 ? Math.min(0, sxy / sxx) : LAP_SCALE_SLOPE;
  } else { xs = Float64Array.of(dlog(scale0)); ys = Float64Array.of(dlog(lap0)); }
  const off = dlog(lap0) - curveLn(xs, ys, b, dlog(scale0));
  const want = dlog(T) - off;
  let lo = dlog(PACE_MIN), hi = dlog(PACE_MAX);
  if (curveLn(xs, ys, b, hi) > want) return { scale: PACE_MAX, lap: dexp(curveLn(xs, ys, b, hi) + off), targetLap: T, capped: true };
  if (curveLn(xs, ys, b, lo) < want) return { scale: PACE_MIN, lap: dexp(curveLn(xs, ys, b, lo) + off), targetLap: T, capped: true };
  for (let it = 0; it < 60; it++) { const m = 0.5 * (lo + hi); if (curveLn(xs, ys, b, m) > want) lo = m; else hi = m; }
  const x = 0.5 * (lo + hi);
  return { scale: dexp(x), lap: dexp(curveLn(xs, ys, b, x) + off), targetLap: T, capped: false };
}

/** A fit is converged when its solo lap is within this share of the target (calibrate_field.ts: max(tol, 0.005)). */
export const FIT_TOL = 0.005;
/**
 * The pace hint other drivers read (Traffic.pace: the clearly-faster test, defending, pass planning) for a car built
 * to `targetLap` whose calibrated solo lap is `achievedLap` (AI round 1, 27 Oct 2026): the target, except where the fit
 * did not converge (a car at the caps cannot reach it): then the lap it can actually do, so it does not plan passes it
 * cannot make and nobody waves it by as clearly faster.
 */
export function paceHint(targetLap: number, achievedLap: number | null | undefined): number {
  return achievedLap != null && achievedLap > 0 && Math.abs(achievedLap / targetLap - 1) > FIT_TOL ? achievedLap : targetLap;
}

/**
 * Draw the car's driver for a race: one of its real stints, uniformly, from (seed, number, AI_VERSION).
 * Sometimes that driver was quick, sometimes slow. A car without eligible stints keeps its car-level pace.
 * The draw is never shown to the player (owner's call).
 */
export function drawPace(c: PaceCar, seed: number): DrawnPace {
  const st = c.stints ?? [];
  if (!st.length) return { stint: -1, of: 0, targetLap: c.targetLap, bestLap: c.bestLap, sigma: c.sigma, scale: c.scale && c.scale > 0 ? c.scale : null, achievedLap: c.scale && c.scale > 0 && c.achievedLap ? c.achievedLap : null };
  const k = new Rng(hashSeed(seed, `stint:${c.number}:v${AI_VERSION}`)).int(st.length);
  const s = st[k];
  return { stint: k, of: st.length, targetLap: s.targetLap, bestLap: s.bestLap, sigma: s.sigma, scale: s.scale && s.scale > 0 ? s.scale : null, achievedLap: s.scale && s.scale > 0 && s.achievedLap ? s.achievedLap : null };
}

export interface PaceJson {
  ai_version: number;
  source?: string;
  /** free-text notes on how the field was built (ids, cars left out) */
  notes?: string;
  track?: string;
  /** Which statistic of the clean laps the targets are (tools/race/pace_rules.ts): the quantile `q`; 0.5 is the median. */
  pace?: { stat: 'quantile'; q: number };
  /** Calibration metadata (written by calibrate_field.ts). */
  calibrated?: { ai_version: number; date?: string; tolerance?: number };
  cars: PaceCar[];
}

/** A field car's model key: the pace row's `model_id`, else the identity row's `model_id`, else its field key. */
export function modelKey(c: { id?: unknown; number?: unknown; model_id?: unknown }, identity?: { [k: string]: unknown } | null): string {
  const m = c.model_id ?? identity?.model_id;
  return m != null && String(m) !== '' ? String(m) : fieldKey(c);
}

/** A field car's identity / model key: its `id`, else its number (pace.json cars, identity.json / models.json rows). */
export function fieldKey(c: { id?: unknown; number?: unknown }): string {
  return c.id != null && String(c.id) !== '' ? String(c.id) : String(c.number);
}

/**
 * Car identity (public/cars/field/identity.json, or the track's own cars/field/<track>/identity.json, written by
 * another tool; rows keyed by `id`, else `number`). All fields optional; this
 * module reads several spellings (top level or under `dims` / `dimensions`) so the two can evolve
 * independently. Missing → Probe values.
 */
export interface IdentityEngine {
  family?: string; cylinders?: number; layout?: string; displacement_l?: number; aspiration?: string;
  redline_rpm?: number; stock_power_kw?: number; exhaust_note?: string; confidence?: number | string;
}
export interface IdentityCar {
  number: string;
  /** the row's field key when it differs from the number ("0_bw"); see fieldKey */
  id?: string;
  make?: string; model?: string; year?: number;
  mass_kg?: number;
  power_kw?: number;
  length_m?: number; width_m?: number; height_m?: number; wheelbase_m?: number; track_m?: number;
  engine?: IdentityEngine;
  /** optional explicit overrides */
  drive?: string; gears?: number;
  color?: string; colors?: string[]; model_file?: string;
  /** id of the same physical car at an earlier event (e.g. Sonoma 21 -> Laguna 200): one body, livery per event */
  same_car?: string;
  [k: string]: unknown;
}

function pickNum(o: any, keys: string[]): number | undefined {
  for (const k of keys) {
    const parts = k.split('.');
    let v: any = o;
    for (const p of parts) v = v == null ? undefined : v[p];
    if (typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v))) v = Number(v);
    if (typeof v === 'number' && Number.isFinite(v) && v > 0) return v;
  }
  return undefined;
}
const dimKeys = (k: string, extra: string[] = []) => [k, `dims.${k}`, `dimensions.${k}`, ...extra];

/** Normalize identity.json (array, { cars: [...] } or { "<number>": {...} }) into a map by field key (`id`, else number). */
export function parseIdentity(json: unknown): Map<string, IdentityCar> {
  const out = new Map<string, IdentityCar>();
  if (!json || typeof json !== 'object') return out;
  const j: any = json;
  const list: any[] = Array.isArray(j) ? j : Array.isArray(j.cars) ? j.cars : Object.entries(j).filter(([, v]) => v && typeof v === 'object').map(([k, v]: [string, any]) => ({ number: k, ...v }));
  for (const c of list) {
    if (!c || (c.number == null && c.id == null)) continue;
    const num = String(c.number ?? c.id);
    const key = fieldKey(c);
    const kw = pickNum(c, dimKeys('power_kw', ['powerKw', 'power.kw']));
    const hp = pickNum(c, dimKeys('power_hp', ['hp', 'power.hp', 'horsepower']));
    const e = c.engine && typeof c.engine === 'object' ? c.engine : {};
    out.set(key, {
      ...c,
      number: num,
      year: pickNum(c, ['year']),
      mass_kg: pickNum(c, dimKeys('mass_kg', ['mass', 'race_mass_kg', 'weight_kg', 'curb_weight_kg', 'dims.mass'])),
      power_kw: kw ?? (hp ? hp * 0.7457 : undefined),
      length_m: pickNum(c, dimKeys('length_m', ['dimensions.length'])),
      width_m: pickNum(c, dimKeys('width_m', ['dimensions.width'])),
      height_m: pickNum(c, dimKeys('height_m', ['dimensions.height'])),
      wheelbase_m: pickNum(c, dimKeys('wheelbase_m', ['dimensions.wheelbase'])),
      track_m: pickNum(c, dimKeys('track_m', ['dimensions.track'])),
      gears: pickNum(c, ['gears', 'transmission.gears', 'engine.gears']),
      engine: {
        ...e,
        cylinders: pickNum(e, ['cylinders']),
        displacement_l: pickNum(e, ['displacement_l', 'displacement']),
        redline_rpm: pickNum(e, ['redline_rpm', 'redline']),
        stock_power_kw: pickNum(e, ['stock_power_kw', 'power_kw']),
      },
    });
  }
  return out;
}

// ------------------------------------------------------------------ car type (drive, engine, gearbox)

export type DriveLayout = 'fwd' | 'rwd' | 'awd';
export type EnginePos = 'front' | 'mid' | 'rear';

/** What the AI car is mechanically, resolved from identity.json with defaults (recorded in pace.json). */
export interface CarType {
  drive: DriveLayout;
  enginePos: EnginePos;
  frontWeight: number;
  /** "I4" | "I6" | "V6" | "V8" | "flat4" | "flat6" | "rotary" | "I5" | "V12" ... */
  engineLayout: string;
  cylinders: number;
  turbo: boolean;
  redline: number;
  /** auto-shift upshift point, rpm */
  shiftRpm: number;
  gears: number;
  /** stock peak power, kW (before the pace scale) */
  stockPowerKw: number;
  /** exhaust note from identity.json, for the audio stream */
  exhaustNote: string | null;
  /** true when no identity row was found (the car is a Probe clone) */
  probeFallback: boolean;
}

const RX = (s: string) => new RegExp(s, 'i');
const REAR_ENGINE = RX('beetle|\\bbug\\b|type ?1|type ?3|karmann|corvair|\\b911\\b|\\b912\\b|smart fortwo|\\b(?:vw )?bus\\b|vanagon|type ?2|hillman imp|renault (?:dauphine|r8|10)|fiat 500(?!x)|fiat 600|\\btrabant');
const MID_ENGINE = RX('mr2|mr-2|mr-s|fiero|\\b914\\b|boxster|cayman|x1/?9|elise|exige|\\bnsx\\b|lotus europa|pantera|\\bmidget\\b(?=.*mid)');
const AWD = RX('quattro|subaru(?!.*brz)|impreza|legacy|outback|forester|\\bwrx\\b|\\bsti\\b|evo(?:lution)?\\b|galant vr-?4|talon tsi awd|eclipse gsx|celica (?:all-?trac|gt-?four)|skyline gt-?r|\\bawd\\b|4wd|4x4|audi (?:s4|rs)|syncro');
const TRANSAXLE = RX('\\b944\\b|\\b924\\b|\\b928\\b|corvette c[5-8]|alfa (?:alfetta|gtv|75|milano)');
const RWD = RX('miata|mx-?5|rx-?7|rx-?8|\\brx-?[23]\\b|e21|e30|e36|e46|e9[0-3]|e28|e34|e39|z3|z4|\\bbmw\\b(?!.*mini)|mustang|camaro|firebird|trans ?am|corvette|\\bnova\\b|chevelle|impala|caprice|el camino|monte carlo|crown vic|grand marquis|town car|panther|thunderbird|cougar(?!.*199[89]|.*200)|fox ?body|mercedes|benz|\\b(?:volvo )?(?:142|144|240|244|245|740|760|940|960)\\b|240sx|180sx|silvia|300zx|280zx?|260z|240z|350z|370z|datsun (?:510|620|720|1200|z)|\\b510\\b|supra|cressida|ae86|corolla gt-?s|s2000|aerostar|ranger|\\bs-?10\\b|pickup|truck|jaguar|lexus (?:is|sc|gs|ls)|chrysler 300|charger|challenger|dart|valiant|duster|barracuda|g35|g37|infiniti (?:g|q|m)|\\bgto\\b|cutlass|regal|grand national|caddy|cadillac (?:deville 19[6-7]|cts)|\\bmg ?b\\b|\\bmgb\\b|triumph|spitfire|tr[4-8]\\b|alfa|fiat 124|lotus|\\bbrz\\b|frs|fr-s|86\\b|genesis coupe|solstice|sky\\b|hilux|land cruiser|bronco|jeep|ford model|falcon|capri|pinto|mustang ii|granada|fairmont|ltd|volvo p1800|saab sonett|amc|gremlin|hornet|javelin|studebaker|rambler|plymouth|dodge (?:dart|charger|challenger|ram|dakota)|chevy (?:s-?10|c-?10|luv)');
const FWD_HINT = RX('mini|cooper|civic|crx|integra|prelude|accord|golf|rabbit|jetta|gti|scirocco|corrado|passat|probe|mx-?6|\\b626\\b|protege|\\b323\\b|neon|saturn|cavalier|sunfire|escort|focus|fiesta|contour|taurus|sentra|altima|maxima|camry|tercel|\\becho\\b|yaris|del sol|\\bfit\\b|\\b99\\b|900|9-3|saab|\\b850\\b|s70|v70|eclipse(?!.*gsx)|galant(?!.*vr)|lancer(?!.*evo)|elantra|tiburon|accent|aveo|cobalt|grand am|sunbird|beretta|corsica|lumina|reliant|omni|horizon|caravan|shadow|sundance|cirrus|stratus|sebring|x-?type|\\ba3\\b|\\ba4\\b(?!.*quattro)|\\btt\\b(?!.*quattro)|minivan|odyssey|sienna|windstar|quest|metro|swift|sidekick');

/** Resolve drive layout, engine and gearbox for one car (identity row may be null → the Probe). */
export function resolveCarType(id: IdentityCar | null | undefined): CarType {
  if (!id) {
    return { drive: 'fwd', enginePos: 'front', frontWeight: 0.62, engineLayout: 'V6', cylinders: 6, turbo: false, redline: 6900, shiftRpm: 5000, gears: 5, stockPowerKw: 0, exhaustNote: null, probeFallback: true };
  }
  const name = `${id.make ?? ''} ${id.model ?? ''}`.trim();
  const e = id.engine ?? {};
  const year = typeof id.year === 'number' ? id.year : 1990;
  // ---- drive layout and engine position
  let enginePos: EnginePos = 'front';
  let drive: DriveLayout = 'fwd';
  if (REAR_ENGINE.test(name)) { enginePos = 'rear'; drive = 'rwd'; }
  else if (MID_ENGINE.test(name)) { enginePos = 'mid'; drive = 'rwd'; }
  else if (AWD.test(name)) drive = 'awd';
  else if (FWD_HINT.test(name)) drive = 'fwd';
  else if (/celica/i.test(name)) drive = year >= 1986 ? 'fwd' : 'rwd';
  else if (/corolla/i.test(name)) drive = year >= 1984 && !/ae86|gt-?s/i.test(name) ? 'fwd' : 'rwd';
  else if (TRANSAXLE.test(name) || RWD.test(name)) drive = 'rwd';
  else drive = year < 1978 ? 'rwd' : 'fwd'; // unknown: old cars were mostly RWD
  const forced = typeof id.drive === 'string' ? id.drive.toLowerCase() : '';
  if (forced === 'fwd' || forced === 'rwd' || forced === 'awd') drive = forced;
  const frontWeight = enginePos === 'rear' ? 0.40 : enginePos === 'mid' ? 0.43 : TRANSAXLE.test(name) ? 0.50
    : drive === 'fwd' ? 0.62 : drive === 'awd' ? 0.58 : 0.53;
  // ---- engine
  const aspiration = String(e.aspiration ?? '').toLowerCase();
  // a battery-electric car (identity layout "EV" / aspiration "EV", cylinders 0: Buttonwillow #16 Bolt): layout 'EV',
  // cylinders 0 (callers must not divide by it), a constant-power torque shape, never turbo
  const electric = /^(EV|BEV|ELECTRIC)$/i.test(String(e.layout ?? '').trim()) || /^(ev|bev|electric)$/.test(aspiration.trim());
  const turbo = !electric && (/turbo|super|charged|boost/.test(aspiration) || /turbo/i.test(name));
  let cyl = e.cylinders ?? 0;
  let layout = electric ? 'EV' : String(e.layout ?? '').toUpperCase().replace(/\s+/g, '');
  if (/FLAT|BOXER|^H\d/.test(layout)) layout = cyl >= 6 || /6/.test(layout) ? 'flat6' : 'flat4';
  if (/ROTARY|WANKEL/.test(layout) || /rx-?\d|\b12a\b|\b13b\b/i.test(`${name} ${e.family ?? ''}`)) layout = 'rotary';
  if (!layout) {
    if (/subaru|beetle|bug|karmann|type ?[123]|vanagon|\b914\b/i.test(name)) layout = cyl >= 6 ? 'flat6' : 'flat4';
    else if (/\b911\b|boxster|cayman/i.test(name)) layout = 'flat6';
    else if (cyl >= 8) layout = 'V8';
    else if (cyl === 6) layout = /bmw|supra|cressida|datsun|nissan (?:z|280|260|240z)|volvo|jaguar|mercedes|jeep/i.test(name) ? 'I6' : 'V6';
    else if (cyl === 5) layout = 'I5';
    else if (cyl > 0) layout = 'I4';
    else layout = drive === 'fwd' ? 'I4' : 'I4';
  }
  if (!cyl && !electric) cyl = layout === 'V8' ? 8 : /6/.test(layout) ? 6 : layout === 'I5' ? 5 : layout === 'rotary' ? 2 : layout === 'V12' ? 12 : 4;
  const disp = e.displacement_l ?? (cyl === 8 ? 5.0 : cyl === 6 ? 2.8 : cyl === 5 ? 2.3 : layout === 'rotary' ? 1.3 : 1.8);
  const redDefault = layout === 'V8' ? (disp >= 4.5 ? 5600 : 6200) : layout === 'I6' ? 6500 : layout === 'V6' ? 6300
    : layout === 'flat4' ? (/beetle|bug|karmann|type ?[123]|vanagon|bus/i.test(name) ? 4800 : 6200) : layout === 'flat6' ? 6800
      : layout === 'rotary' ? 8000 : layout === 'I5' ? 6500 : year >= 1988 ? 7000 : 6200;
  const redline = Math.min(9500, Math.max(3400, e.redline_rpm ?? (redDefault - (turbo ? 300 : 0))));
  const shiftFrac = layout === 'V8' ? 0.9 : layout === 'I4' || layout === 'rotary' ? 0.96 : 0.93;
  // stock power: identity, else a specific-output estimate by era / aspiration / layout
  const kwPerL = (layout === 'V8' ? (year < 1990 ? 34 : 45) : layout === 'rotary' ? 75 : year < 1980 ? 38 : year < 1995 ? 52 : 62) * (turbo ? 1.4 : 1);
  const stockPowerKw = e.stock_power_kw ?? id.power_kw ?? Math.max(30, kwPerL * disp);
  const gears = Math.round(id.gears ?? (year < 1955 ? 3 : year < 1975 ? 4 : year >= 2004 ? 6 : 5));
  return {
    drive, enginePos, frontWeight, engineLayout: layout, cylinders: cyl, turbo, redline,
    shiftRpm: Math.round(redline * shiftFrac / 50) * 50, gears: Math.min(6, Math.max(3, gears)), stockPowerKw,
    exhaustNote: typeof e.exhaust_note === 'string' ? e.exhaust_note : null, probeFallback: false,
  };
}

/** Torque curve shape (fractions of redline → fraction of peak torque) by engine type. */
function torqueShape(t: CarType): { rpm: number[]; tq: number[] } {
  if (t.turbo) return { rpm: [0.15, 0.3, 0.42, 0.55, 0.7, 0.85, 0.95, 1.0], tq: [0.45, 0.55, 0.85, 1.0, 1.0, 0.9, 0.8, 0.72] };
  switch (t.engineLayout) {
    case 'EV': return { rpm: [0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0], tq: [1.0, 1.0, 1.0, 0.75, 0.6, 0.5, 0.42] };   // flat torque, then ~constant power
    case 'V8': return { rpm: [0.17, 0.3, 0.45, 0.6, 0.75, 0.88, 1.0], tq: [0.82, 0.95, 1.0, 0.98, 0.92, 0.82, 0.70] };
    case 'I6': case 'flat6': case 'I5': return { rpm: [0.15, 0.3, 0.45, 0.6, 0.72, 0.85, 0.95, 1.0], tq: [0.70, 0.82, 0.92, 0.99, 1.0, 0.95, 0.86, 0.80] };
    case 'V6': return { rpm: [0.15, 0.29, 0.43, 0.58, 0.7, 0.81, 0.9, 0.96, 1.0], tq: [0.71, 0.85, 0.94, 0.99, 1.0, 0.98, 0.92, 0.86, 0.76] };
    case 'rotary': return { rpm: [0.15, 0.3, 0.45, 0.6, 0.75, 0.88, 1.0], tq: [0.60, 0.75, 0.88, 0.97, 1.0, 0.95, 0.85] };
    default: return { rpm: [0.15, 0.3, 0.45, 0.6, 0.72, 0.82, 0.92, 1.0], tq: [0.60, 0.72, 0.84, 0.94, 1.0, 0.99, 0.92, 0.83] }; // I4, flat4: peaky
  }
}

// ------------------------------------------------------------------ spec construction

const PROBE_LENGTH = 4.52; // hull front - rear of the Probe car.json

/** Static rollover threshold T/2h kept at least this multiple of the AI car's fitted lateral tyre mu (aiCarJson). */
export const ROLL_GRIP = 1.15;
/**
 * Ceiling on an AI car's fitted lateral tyre mu (owner, 18 Oct 2026: Lemons cars on 200-treadwear tyres; 1.28-1.48 g
 * fits were not physical). The Probe car.json base is 1.10, so grip (x g^2) stops at sqrt(1.20 / 1.10); above that the
 * pace comes from power. aiCarJson also clamps the fitted mu.
 */
export const MU_LAT_MAX = 1.2, PROBE_MU_LAT = 1.1;
/** Pace scalar range the calibration may use, and the grip range it trims before touching power. */
export const PACE_MIN = 0.3, PACE_MAX = 1.8, GRIP_MIN = 0.55, GRIP_MAX = Math.sqrt(MU_LAT_MAX / PROBE_MU_LAT);
/** Power-to-weight ceiling for AI cars, kW per tonne (see aiCarJson). */
export const KWT_MAX = 150;

/**
 * Split the fitted pace scalar into a grip factor (cornering and braking: tyres plus how hard the
 * driver leans on them) and a power factor. Between GRIP_MIN and GRIP_MAX only grip moves and the car
 * keeps its own power (stock, or the Lemons swap floor), so a heavy V8 with a slow lap is quick on the
 * straights and slow in the corners while a light turbo car at the front is quick everywhere. Power
 * only moves (cubically) once grip alone cannot reach the lap. Lap time falls monotonically with the
 * scalar, which keeps the one-dimensional calibration fit.
 */
export function paceSplit(scale: number): { grip: number; power: number } {
  const s = Math.min(PACE_MAX, Math.max(PACE_MIN, scale));
  const grip = Math.min(GRIP_MAX, Math.max(GRIP_MIN, s));
  const power = s < GRIP_MIN ? dpow(s / GRIP_MIN, 3) : s > GRIP_MAX ? dpow(s / GRIP_MAX, 3) : 1;
  return { grip, power };
}
const RPMK = 60 / (2 * Math.PI);

/** Peak power of a car.json torque curve, kW. */
export function peakPowerKw(json: any): number {
  const r: number[] = json.engine.torqueCurve.rpm, t: number[] = json.engine.torqueCurve.torque;
  let best = 0;
  for (let i = 0; i < r.length; i++) best = Math.max(best, t[i] * r[i] * Math.PI / 30 / 1000);
  return best;
}

/**
 * car.json for an AI car: the Probe car.json with identity overrides (mass, dimensions, drive layout,
 * weight distribution from the engine position, engine type → torque shape / redline / shift points,
 * stock power, gear count with ratios fitted to the car's top speed), then the pace fit from
 * `paceSplit`: grip g on tyre mu0 (x g^2 above 1, x g below so slow cars stay drivable), brake torque
 * likewise, the lateral speed-sensitivity reference speed x g (slope / g); power q on engine torque.
 * Steering shaping is bypassed (the AI commands the road-wheel angle, like the calibration
 * autopilot). Without an identity row the car is the Probe (V6, FWD, 5 speeds) with the pace scale.
 */
export function aiCarJson(probeJson: any, identity: IdentityCar | null | undefined, scale: number): any {
  const j = JSON.parse(JSON.stringify(probeJson));
  const id = identity ?? null;
  const type = resolveCarType(id);
  // ---- identity: mass (everything that carries load scales with it)
  const m0 = j.mass as number;
  const mr = id?.mass_kg ? Math.min(2, Math.max(0.4, id.mass_kg / m0)) : 1;
  // ---- identity: dimensions
  const len = id?.length_m ?? PROBE_LENGTH * (id?.wheelbase_m ? id.wheelbase_m / j.wheelbase : 1);
  const lr = Math.min(1.4, Math.max(0.7, len / PROBE_LENGTH));
  const wb = id?.wheelbase_m ?? j.wheelbase * lr;
  const wr = id?.width_m ? Math.min(1.25, Math.max(0.8, id.width_m / (2 * j.hull.halfWidth))) : 1;
  const tr = id?.track_m ?? j.trackFront * wr;
  const hr = id?.height_m ? Math.min(1.5, Math.max(0.75, id.height_m / 1.31)) : 1;
  j.mass = m0 * mr;
  j.wheelbase = wb; j.trackFront = tr; j.trackRear = tr * (j.trackRear / probeJson.trackFront);
  j.inertia.roll *= mr * wr * wr; j.inertia.pitch *= mr * lr * lr; j.inertia.yaw *= mr * lr * lr;
  for (const ax of ['front', 'rear']) {
    const a = j.suspension[ax];
    a.springRate *= mr; a.damperBump *= mr; a.damperRebound *= mr; a.antiRollRate *= mr;
  }
  j.suspension.bumpStopForceAtFull *= mr;
  j.suspension.tyreVerticalRate *= mr;
  j.tyre.Fz0 *= mr;
  j.wheel.spinInertia *= Math.sqrt(mr);
  j.brakes.maxTorque *= mr;
  j.brakes.handbrakeTorque *= mr;
  // CG: a little higher for tall cars, but race-lowered so the static rollover threshold T/2h stays
  // above 1.35 g (narrow, tall classics otherwise tip over when nudged at high grip)
  j.cgHeight = Math.min(j.cgHeight * dpow(hr, 0.5), (0.5 * (tr + j.trackRear)) / 2.7);
  j.hull.front *= lr; j.hull.rear *= lr; j.hull.roofFront *= lr; j.hull.roofRear *= lr;
  j.hull.halfWidth *= wr; j.hull.roof *= hr;
  j.aero.frontalArea *= wr * hr;
  const { grip: p, power: q } = paceSplit(scale);
  // grip above 1 self-similar (p^2); below 1 it falls only linearly so slow cars stay drivable
  const p2 = p >= 1 ? p * p : p, p3 = q;
  if (!type.probeFallback) {
    // ---- layout and balance
    j.drivetrain.layout = type.drive;
    j.drivetrain.awdFrontShare = 0.4;
    j.frontWeightFraction = type.frontWeight;
    // brake bias and roll stiffness follow the weight
    j.brakes.frontBias = Math.min(0.75, Math.max(0.55, 0.7 + (type.frontWeight - 0.62) * 0.8));
    if (type.drive !== 'fwd') {
      // RWD balance: more front roll stiffness so the AI's car is stable on power (as most race RWD set-ups)
      j.suspension.front.antiRollRate *= 1.1; j.suspension.rear.antiRollRate *= 0.8;
      j.suspension.front.complianceSteerDegPerKN *= 0.6;
    }
    // ---- engine: shape x stock power
    const sh = torqueShape(type);
    const rl = type.redline;
    const rpm = sh.rpm.map((f) => Math.max(900, Math.round(f * rl)));
    for (let k = 1; k < rpm.length; k++) if (rpm[k] <= rpm[k - 1]) rpm[k] = rpm[k - 1] + 50;
    let peak = 0;
    for (let k = 0; k < rpm.length; k++) peak = Math.max(peak, sh.tq[k] * rpm[k] / RPMK / 1000);
    // Lemons cars run modified engines: a car whose real lap needs far more power than its stock
    // engine makes gets a power floor (an assumed swap / tune) at 70 % of the Probe's power-to-weight,
    // so every car can reach its lap time with its grip fit
    const floorKw = 0.7 * (peakPowerKw(probeJson) / probeJson.mass) * j.mass;
    // ... and a ceiling: above about 150 kW/t the AI driver cannot keep a rear-drive car straight on corner
    // exits (the 206 kW/t 1JZ Corona spun every lap), and a Lemons car rarely puts more than that down anyway
    const effKw = Math.min(Math.max(type.stockPowerKw, floorKw), KWT_MAX * j.mass / 1000);
    const tq0 = effKw / peak; // N·m at the shape's 1.0
    j.engine.torqueCurve = { rpm, torque: sh.tq.map((f) => +(f * tq0).toFixed(2)) };
    j.engine.revLimitRpm = rl + 100;
    j.engine.idleRpm = type.engineLayout === 'V8' ? 750 : 850;
    j.engine.inertia = 0.1 + 0.025 * type.cylinders;
    j.engine.brakingTorqueIdle = -0.12 * tq0; j.engine.brakingTorqueLimit = -0.3 * tq0;
    const a = j.drivetrain.autoShift;
    a.upshiftRpm = type.shiftRpm;
    a.downshiftRpm = Math.round(0.5 * type.shiftRpm);
    a.downshiftMaxRpm = Math.round(0.95 * type.shiftRpm);
    a.kickdownRpm = Math.round(0.8 * type.shiftRpm); a.kickdownHoldRpm = Math.min(rl, Math.round(1.08 * type.shiftRpm));
    a.scheduleMinUpshiftRpm = Math.round(0.8 * type.shiftRpm);
    j.drivetrain.clutch.engageRpm = Math.max(900, j.engine.idleRpm + 50);
    j.drivetrain.clutch.fullRpm = j.drivetrain.clutch.engageRpm + 300;
    // ---- gearbox: top gear reaches the shift point a little above the car's top speed (with the pace power)
    const P = effKw * 1000 * p3 * 0.9;
    const cda = j.aero.cd * j.aero.frontalArea, mg = j.mass * 9.81;
    let vTop = 40;
    for (let it = 0; it < 40; it++) vTop = dcbrt(Math.max(1, P - j.rollingResistance * mg * vTop) / (0.5 * j.aero.airDensity * cda));
    const r = j.wheel.radius;
    const wTop = type.shiftRpm / RPMK;
    const top = wTop * r / (1.04 * vTop);
    const spread = type.gears <= 3 ? 2.6 : type.gears === 4 ? 3.1 : type.gears === 5 ? 3.8 : 4.4;
    const ratios: number[] = [];
    for (let k = 0; k < type.gears; k++) {
      const f = 1 - k / (type.gears - 1);
      ratios.push(+(top * dpow(spread, dpow(f, 1.12))).toFixed(4)); // slightly closer upper gears
    }
    j.drivetrain.gearRatios = ratios;
    j.drivetrain.reverseRatio = ratios[0];
  } else {
    const pw = mr; // keep the Probe's power-to-weight
    j.engine.torqueCurve.torque = j.engine.torqueCurve.torque.map((t: number) => t * pw);
  }
  // ---- pace fit: power q on the engine, grip p on tyres, brakes and the speed sensitivity
  j.engine.torqueCurve.torque = j.engine.torqueCurve.torque.map((t: number) => t * p3);
  j.engine.brakingTorqueIdle *= Math.min(1, p3); j.engine.brakingTorqueLimit *= Math.min(1, p3);
  j.drivetrain.clutch.maxTorque = Math.max(j.drivetrain.clutch.maxTorque, 2 * Math.max(...j.engine.torqueCurve.torque));
  j.tyre.lateral.mu0 *= p2;
  j.tyre.longitudinal.mu0 *= p2;
  if (j.tyre.lateral.mu0 > MU_LAT_MAX) { const c = MU_LAT_MAX / j.tyre.lateral.mu0; j.tyre.lateral.mu0 = MU_LAT_MAX; j.tyre.longitudinal.mu0 *= c; }
  // ... and the CG race-lowered further when the fitted grip exceeds that: the static rollover threshold T/2h stays
  // ROLL_GRIP x the lateral mu, so a high-grip car cannot lift both inside wheels and tip over in a long corner
  // (18 Oct 2026, painted-road track: the quick stints need grip scale > 1.14, where tall cars rolled over at T2)
  {
    const tAvg = 0.5 * (j.trackFront + j.trackRear), rt = Math.max(1.35, ROLL_GRIP * j.tyre.lateral.mu0);
    j.cgHeight = Math.min(j.cgHeight, tAvg / (2 * rt));
  }
  j.brakes.maxTorque *= p2;
  j.tyre.speedSensitivity.refSpeed *= p;
  j.tyre.speedSensitivity.slope /= p;
  j.steering.shapingSpeed = 1e6;
  j.steering.rateSpeed *= p;
  j.name = `AI ${id?.make ?? 'Probe'} ${id?.model ?? ''}`.trim();
  return j;
}

/** Resolved per-car spec summary recorded in pace.json (for the app and the audio stream). */
export interface ResolvedCar {
  make: string | null; model: string | null;
  drive: DriveLayout; enginePos: EnginePos; frontWeight: number;
  engineLayout: string; cylinders: number; turbo: boolean;
  redline: number; shiftRpm: number; gears: number; gearRatios: number[];
  massKg: number; powerKw: number; stockPowerKw: number;
  /** the pace fit split (paceSplit) and what it gives: driver lateral budget in g and the drag-limited top speed */
  gripScale: number; powerScale: number; lateralG: number; topSpeedKph: number;
  exhaustNote: string | null; probeFallback: boolean;
}

export function describeAiCar(probeJson: any, identity: IdentityCar | null | undefined, scale: number): ResolvedCar {
  const t = resolveCarType(identity);
  const j = aiCarJson(probeJson, identity, scale);
  const split = paceSplit(scale);
  const perf = measureCarPerf(loadCarSpec(j));
  const P = peakPowerKw(j) * 1000 * 0.9, cda = j.aero.cd * j.aero.frontalArea, mg = j.mass * 9.81;
  let vTop = 40;
  for (let it = 0; it < 40; it++) vTop = dcbrt(Math.max(1, P - j.rollingResistance * mg * vTop) / (0.5 * j.aero.airDensity * cda));
  return {
    make: (identity?.make as string) ?? null, model: (identity?.model as string) ?? null,
    drive: t.drive, enginePos: t.enginePos, frontWeight: j.frontWeightFraction,
    engineLayout: t.engineLayout, cylinders: t.cylinders, turbo: t.turbo,
    redline: t.probeFallback ? j.engine.revLimitRpm : t.redline, shiftRpm: j.drivetrain.autoShift.upshiftRpm,
    gears: j.drivetrain.gearRatios.length, gearRatios: j.drivetrain.gearRatios,
    massKg: Math.round(j.mass), powerKw: +peakPowerKw(j).toFixed(1),
    stockPowerKw: +(t.probeFallback ? peakPowerKw(probeJson) : t.stockPowerKw).toFixed(1),
    gripScale: +split.grip.toFixed(4), powerScale: +split.power.toFixed(4), lateralG: +perf.alat.toFixed(3), topSpeedKph: +(vTop * 3.6).toFixed(1),
    exhaustNote: t.exhaustNote, probeFallback: t.probeFallback,
  };
}

export function buildAiSpec(probeJson: any, identity: IdentityCar | null | undefined, scale: number): CarSpec {
  return loadCarSpec(aiCarJson(probeJson, identity, scale));
}

// ------------------------------------------------------------------ performance model

const G = 9.81;
const RPM = 60 / (2 * Math.PI);

/** What the driver knows about its car (measured / derived once per car). */
export interface CarPerf {
  /** Full-throttle acceleration on flat ground per 0.5 m/s speed bin, m/s². */
  acc: Float64Array;
  /** Deceleration (g) per unit of brake pedal in the linear range. */
  brakeGain: number;
  /** Understeer feed-forward, rad of road-wheel angle per g. */
  kUs: number;
  /** Driver lateral grip budget (g) and braking budget (g). */
  alat: number; abrake: number;
  /** Max road-wheel angle, rad. */
  maxSteer: number;
  wheelbase: number;
  mass: number; aeroK: number; crr: number;
  peakSlipRatio: number;
  /** slip angle of the pure-lateral tyre peak, rad */
  peakSlipAngle: number;
  /** wheels whose spin the driver watches for wheelspin (driven axle) */
  drivenFront: boolean; drivenRear: boolean;
  hullFront: number; hullRear: number; halfWidth: number;
}

export const ACC_BIN = 0.5;
export const ACC_N = 160;

function torqueAt(spec: CarSpec, rpm: number): number {
  const r = spec.engine.torqueCurve.rpm, t = spec.engine.torqueCurve.torque;
  if (rpm <= r[0]) return t[0];
  for (let i = 1; i < r.length; i++) if (rpm <= r[i]) return t[i - 1] + (t[i] - t[i - 1]) * (rpm - r[i - 1]) / (r[i] - r[i - 1]);
  return t[t.length - 1];
}

/**
 * Build the driver's model of the car. The acceleration table is analytic (gear the auto-shift would
 * hold, traction-limited on the front axle, drag, rolling resistance, an inertia allowance); brake
 * gain and understeer are measured with two short runs on flat ground (~3.5k physics steps).
 */
export function measureCarPerf(spec: CarSpec): CarPerf {
  const m = spec.mass, r = spec.wheel.radius;
  const aeroK = 0.5 * spec.aero.airDensity * spec.aero.cd * spec.aero.frontalArea;
  const ratios = spec.drivetrain.gearRatios, up = spec.drivetrain.autoShift.upshiftRpm;
  const acc = new Float64Array(ACC_N);
  const lay = spec.drivetrain.layout;
  const drivenShare = lay === 'rwd' ? 1 - spec.frontWeightFraction : lay === 'awd' ? 1 : spec.frontWeightFraction;
  const trac = spec.tyre.longitudinal.mu0 * drivenShare * m * G * (lay === 'fwd' ? 1.05 : 1.1);
  for (let b = 0; b < ACC_N; b++) {
    const v = (b + 0.5) * ACC_BIN;
    let F = 0;
    for (let g = 0; g < ratios.length; g++) {
      const rpm = Math.max(spec.engine.idleRpm, (v / r) * ratios[g] * RPM);
      if (rpm > spec.engine.revLimitRpm) continue;
      const f = torqueAt(spec, rpm) * ratios[g] * spec.drivetrain.efficiency / r;
      // the auto-shift holds the lowest gear below the upshift rpm: use it, but allow a higher gear's force
      F = Math.max(F, rpm <= up || g === ratios.length - 1 ? f : 0);
      if (rpm <= up) break;
    }
    if (F === 0) { // above the upshift rpm in top gear
      const g = ratios.length - 1, rpm = (v / r) * ratios[g] * RPM;
      F = rpm <= spec.engine.revLimitRpm ? torqueAt(spec, rpm) * ratios[g] * spec.drivetrain.efficiency / r : 0;
    }
    F = Math.min(F, trac);
    const res = aeroK * v * v + (spec.rollingResistance + spec.rollingResistanceSpeed * v * v) * m * G;
    acc[b] = (F - res) / (m * 1.06);
  }
  const flat = createFlatSurface();
  const inp = { steer: 0, throttle: 0, brake: 0.3, shiftUp: false, shiftDown: false };
  // brake gain: pedal 0.3 from 25 m/s for 0.8 s
  let brakeGain = 1.2;
  {
    const car = new Vehicle(spec, { autoShift: true });
    car.reset([0, 0, 0], 0, 25);
    for (let i = 0; i < 100; i++) car.step(inp, flat, 0.001);
    const v0 = car.state.speed;
    for (let i = 0; i < 700; i++) car.step(inp, flat, 0.001);
    const d = (v0 - car.state.speed) / 0.7 / G;
    if (d > 0.05) brakeGain = d / 0.3;
  }
  // understeer: steady turn at 25 m/s, ~0.7 g
  const L = spec.wheelbase, maxSteer = (spec.steering.maxAngleDeg * Math.PI) / 180;
  let kUs = 0;
  {
    const u0 = 25;
    const delta = 0.0035 + (L * 0.7 * G * spec.tyre.lateral.mu0 / 1.1) / (u0 * u0);
    const car = new Vehicle(spec, { autoShift: true });
    car.reset([0, 0, 0], 0, u0);
    let integ = 0, a = 0, k = 0, n = 0;
    const ci = { steer: Math.min(1, delta / maxSteer), throttle: 0, brake: 0, shiftUp: false, shiftDown: false };
    for (let i = 0; i < 2600; i++) {
      const e = u0 - car.state.speed;
      integ = Math.max(-2, Math.min(5, integ + e * 0.001));
      ci.throttle = Math.max(0, Math.min(1, 0.25 * e + 0.08 * integ + 0.25));
      car.step(ci, flat, 0.001);
      if (i > 1800) { a += car.state.speed * car.state.angVel[2] / G; k += car.state.angVel[2] / Math.max(1, car.state.speed); n++; }
    }
    a /= n; k /= n;
    kUs = a > 0.1 ? Math.max(0, Math.min(0.08, (delta - L * k) / a)) : 0.035;
  }
  return {
    acc, brakeGain, kUs,
    // grip budget: narrow, tall cars lose more to load transfer (track / 2h relative to the Probe's 1.51)
    alat: 0.955 * spec.tyre.lateral.mu0 * Math.min(1, dpow((0.5 * (spec.trackFront + spec.trackRear)) / (2 * spec.cgHeight) / 1.51, 0.4)),
    abrake: 0.95 * spec.tyre.longitudinal.mu0 / 1.08,
    maxSteer, wheelbase: L, mass: m, aeroK, crr: spec.rollingResistance,
    peakSlipRatio: spec.tyre.longitudinal.peakSlipRatio,
    peakSlipAngle: (spec.tyre.lateral.peakSlipAngleDeg * Math.PI) / 180,
    drivenFront: spec.drivetrain.layout !== 'rwd', drivenRear: spec.drivetrain.layout !== 'fwd',
    hullFront: spec.hull.front, hullRear: spec.hull.rear, halfWidth: spec.hull.halfWidth,
  };
}

export function accAt(perf: CarPerf, v: number): number {
  const u = Math.max(0, Math.min(ACC_N - 1.001, v / ACC_BIN - 0.5));
  const i = Math.floor(u);
  return perf.acc[i] + (u - i) * (perf.acc[i + 1] - perf.acc[i]);
}

export function coastDecel(perf: CarPerf, v: number): number {
  return (perf.aeroK * v * v) / perf.mass / G + perf.crr + 0.02;
}

/**
 * Target speed profile per station: the car's own limit, i.e. the lateral-grip speed (alat budget,
 * lateral speed sensitivity) with forward (acceleration, friction-ellipse) and backward (braking)
 * passes, as tools/calibrate/drive.ts does. The ghost speed shape only caps it at GHOST_CAP x the
 * real Probe lap (a sanity ceiling): the fit lives in the car (paceSplit), so a powerful heavy car
 * keeps its straight-line speed and a gripless one its slow corners.
 */
const GHOST_CAP = 1.3;
/** Profile options (experiments and tools): `ghostCap` x the real Probe lap as a ceiling, `commit` = share of the lateral and braking budgets the profile asks for. */
export interface ProfileOptions { ghostCap?: number; commit?: number }
/**
 * Lateral acceleration capacity (g) on a banked road: a level-road capacity `a` (g) plus the road's bank toward the
 * inside of the turn (tan b > 0; the line's `bank` times the turn direction): (a + b) / (1 - a b). Laguna's T5, T6, the
 * Corkscrew, Rainey and T10 are banked 4-12 %, worth 0.1-0.25 g (18 Oct 2026: the profile ignored it, so the AI
 * drove the banked corners as if flat).
 */
/** Share of the banking credited in the profile (1.0 ran the cars ~1 m wide at Rainey and T3/T5: line rms 0.4 m alone). */
const BANK_CREDIT = 0.85;
export function bankedG(a: number, line: RaceLine, i: number, v = 0): number {
  const k = line.curv[i];
  const b = BANK_CREDIT * Math.max(-0.15, Math.min(0.15, k >= 0 ? line.bank[i] : -line.bank[i]));
  return loadFactor(line, i, v) * (a + b) / Math.max(0.5, 1 - a * b);
}

/** Normal load factor from the line's vertical curvature at speed v: < 1 over a crest (the Corkscrew drop), > 1 in a dip. */
export function loadFactor(line: RaceLine, i: number, v: number): number {
  return Math.max(0.5, Math.min(1.25, 1 + v * v * line.vcurv[i] / G));
}


export function buildSpeedProfile(line: RaceLine, perf: CarPerf, spec: CarSpec, opts: ProfileOptions = {}): Float64Array {
  const N = line.N, curv = line.curv, grade = line.grade, ds = line.ds;
  const ghostCap = opts.ghostCap ?? GHOST_CAP, commit = opts.commit ?? 1;
  const vLat = new Float64Array(N);
  const ref = spec.tyre.speedSensitivity.refSpeed, slope = spec.tyre.speedSensitivity.slope;
  const VMAX = 85;
  const capAt = (i: number, v: number) => bankedG(commit * perf.alat * Math.max(0.6, 1 - slope * Math.max(0, v - ref)), line, i, v);
  for (let i = 0; i < N; i++) {
    const k = Math.max(1e-6, Math.abs(curv[i]));
    let v = Math.min(VMAX, Math.sqrt(bankedG(perf.alat, line, i) * G / k));
    for (let it = 0; it < 4; it++) v = Math.min(VMAX, Math.sqrt(capAt(i, v) * G / k));
    vLat[i] = v;
  }
  const prof = new Float64Array(N);
  for (let i = 0; i < N; i++) prof[i] = Math.min(vLat[i], ghostCap * line.ghostV[i]);
  const ell = (v: number, i: number) => {
    const u = Math.min(1, (v * v * Math.abs(curv[i])) / (capAt(i, v) * G));
    return Math.sqrt(Math.max(0, 1 - u * u));
  };
  for (let pass = 0; pass < 3; pass++) {
    for (let k = 0; k < 2 * N; k++) {
      const i = k % N, j = (i + 1) % N, v = prof[i];
      const a = Math.max(0, accAt(perf, v)) * ell(v, i) - G * grade[i];
      const vn = Math.sqrt(Math.max(0, v * v + 2 * a * ds[i]));
      if (vn < prof[j]) prof[j] = vn;
    }
    for (let k = 2 * N; k > 0; k--) {
      const j = k % N, i = (j - 1 + N) % N, v = prof[j];
      const d = commit * perf.abrake * G * loadFactor(line, j, v) * ell(v, j) + G * grade[i];
      const vp = Math.sqrt(Math.max(0, v * v + 2 * Math.max(0.5, d) * ds[i]));
      if (vp < prof[i]) prof[i] = vp;
    }
  }
  return prof;
}

/** Lap time implied by a profile (s). */
export function profileLapTime(line: RaceLine, prof: ArrayLike<number>): number {
  let t = 0;
  for (let i = 0; i < line.N; i++) t += line.ds[i] / Math.max(1, 0.5 * (prof[i] + prof[(i + 1) % line.N]));
  return t;
}
