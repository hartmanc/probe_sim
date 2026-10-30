// Race recordings (30 Oct 2026; docs/races.md): a race is deterministic from (seed, AI version, build, config, the player's
// inputs) -- the worker identity test proves it -- so the recording is those, plus two safeguards: the live lap times and
// line-crossing times (the offline re-run must reproduce them exactly) and a once-a-second position snapshot of every car.
// No personal data: no name, no device id, no secret. Pure TS (btoa / CompressionStream are web-standard and in Node).
import type { InputTrace, TraceRow } from './types';

export const REC_FORMAT = 1;

/** Size cap of the compressed upload (the server's cap too), bytes. */
export const REC_MAX_BYTES = 512 * 1024;
/** The server refuses a body that decompresses to more than this, bytes (a gzip bomb stops here). */
export const REC_MAX_JSON_BYTES = 12 * 1024 * 1024;
/** Physics steps between position snapshots (1 s). */
export const SNAP_STEPS = 1000;
/** Fewest sim seconds a race must have run before an aborted one is worth sending. */
export const REC_MIN_ABORT_S = 20;

/**
 * Between-step events that are not input samples: the player's recovery (modes/race.ts reset(): the car back on the
 * centreline at station s) and an app-side rule report (the pit-exit cones). `step` = the sim's stepIndex when it happened,
 * i.e. applied just before that step. [step, 0, s] | [step, 1, kind, detail?]
 */
export type RecEvent = [number, 0, number] | [number, 1, string, string?];

/** What buildDirector (src/app/race-build.ts) was given, plus the sim settings at the start. */
export interface RecBuild {
  seed: number; laps: number;
  realGrid: boolean; playerAi: boolean; lod: boolean; strengthPct: number;
  closeRacing: boolean | null; planner: 'lanes' | 'offset' | null;
  /** AI cars the device raced (field-select.ts neighbourField), null = the whole pace file */
  fieldCap: number | null;
  /** the gear-schedule reference, auto-shift and ABS settings at the rolling start */
  ref: string | null; autoShift: boolean; abs: boolean;
}

export interface RecLive {
  /** the player's completed lap times, s, in order */
  lapTimes: number[];
  /** every line crossing of the race so far (the director's `crossings`), all cars */
  crossings: { car: string; lapNr: number; t: number }[];
  /** the classification at the flag (null before it) */
  results: { number: string; laps: number; time: number | null; metres: number }[] | null;
}

/** Position snapshot, once per `everySeconds`: distance and lane offset of every car, quantised to 0.1 m. */
export interface RecSnapshot {
  everySeconds: 1;
  /** car numbers in the director's order */
  cars: string[];
  /** track length in dm (positions are mod this) */
  L10: number;
  /** seconds sampled */
  n: number;
  /** each car's s at the first sample, dm */
  s0: number[];
  /** base64 Int16 (little endian): s change since the previous sample, dm, wrapped to +-L10/2; (n - 1) rows of cars.length */
  ds: string;
  /** base64 Int8: lane offset e, dm, clamped to +-127; n rows of cars.length */
  e: string;
}

export interface RaceRecording {
  v: 1;
  trackId: string;
  /** the pace file the field was built from (TRACKS[trackId].pace) */
  fieldId: string;
  seed: number;
  laps: number;
  /** AI_VERSION as a string */
  aiVersion: string;
  /** the build's short git sha (vite __GIT_SHA__), '' when unknown */
  buildSha: string;
  /** physicsVersion() of the recording client */
  physics: string;
  build: RecBuild;
  /** the director's effective RaceConfig (configOf): the offline re-run checks its own against it */
  config: Record<string, unknown>;
  /** the quantised 100 Hz samples, the hot-lap trace's encoding (types.ts TraceRow); steps = physics steps recorded */
  inputs: InputTrace;
  events: RecEvent[];
  live: RecLive;
  snapshot: RecSnapshot | null;
  /** the owner token was present (the server verifies it; this flag is only the client's claim) */
  owner: boolean;
  started: string;
  durationS: number;
  aborted?: true;
  /** the upload was cut to fit REC_MAX_BYTES: inputs, live data and snapshots end at this step */
  truncated?: { atStep: number };
}

// ---------------------------------------------------------------- assembling

/** What a RaceTap hands over since the last drain. All plain data (structured-clone safe for the Worker). */
export interface RecChunk {
  rows: TraceRow[]; refs: [number, string | null][]; events: RecEvent[];
  snapS: Int32Array[]; snapE: Int8Array[];
  /** physics steps run at the drain, and the sim's rolling-start state */
  steps: number;
  reset: { pos: [number, number, number]; heading: number; speed: number };
}


/** Chunks from one or more drains (the Worker sends one at the end, the main-thread path drains once). */
export class RecAssembler {
  rows: TraceRow[] = [];
  refs: [number, string | null][] = [];
  events: RecEvent[] = [];
  snapS: Int32Array[] = [];
  snapE: Int8Array[] = [];
  steps = 0;
  reset: RecChunk['reset'] | null = null;
  add(c: RecChunk): this {
    for (const r of c.rows) this.rows.push(r);
    for (const r of c.refs) this.refs.push(r);
    for (const e of c.events) this.events.push(e);
    for (const s of c.snapS) this.snapS.push(s);
    for (const e of c.snapE) this.snapE.push(e);
    this.steps = c.steps; this.reset = c.reset;
    return this;
  }
}

export interface RecMeta {
  trackId: string; fieldId: string; seed: number; laps: number; aiVersion: string; buildSha: string; physics: string;
  build: RecBuild; config: Record<string, unknown>; cars: string[]; L: number; carId: string;
  owner: boolean; started: string; durationS: number; aborted: boolean;
}

export function buildRecording(meta: RecMeta, a: RecAssembler, live: RecLive): RaceRecording {
  const inputs: InputTrace = {
    v: 1, physics: meta.physics, track: meta.trackId, car: meta.carId, hz: 100, dt: 0.001,
    reset: a.reset ?? { pos: [0, 0, 0], heading: 0, speed: 0 }, ref: a.refs, rows: a.rows, steps: a.steps,
  };
  const snapshot = a.snapS.length ? encodeSnapshot(meta.cars, meta.L, a.snapS, a.snapE) : null;
  return {
    v: REC_FORMAT, trackId: meta.trackId, fieldId: meta.fieldId, seed: meta.seed, laps: meta.laps, aiVersion: meta.aiVersion, buildSha: meta.buildSha,
    physics: meta.physics, build: meta.build, config: meta.config, inputs, events: a.events, live, snapshot,
    owner: meta.owner, started: meta.started, durationS: Math.round(meta.durationS * 10) / 10, ...(meta.aborted ? { aborted: true as const } : {}),
  };
}

// ---------------------------------------------------------------- snapshot codec

export function b64encode(bytes: Uint8Array): string {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}
export function b64decode(text: string): Uint8Array {
  const s = atob(text), out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

export function encodeSnapshot(cars: string[], L: number, S: Int32Array[], E: Int8Array[]): RecSnapshot {
  const n = S.length, c = cars.length, L10 = Math.round(L * 10), half = L10 / 2;
  const ds = new Int16Array(Math.max(0, n - 1) * c);
  for (let k = 1; k < n; k++) for (let i = 0; i < c; i++) {
    let d = S[k][i] - S[k - 1][i];
    if (d >= half) d -= L10; else if (d < -half) d += L10;
    ds[(k - 1) * c + i] = d;
  }
  const e = new Int8Array(n * c);
  for (let k = 0; k < n; k++) e.set(E[k], k * c);
  const le = (a: Int16Array) => { const b = new Uint8Array(a.length * 2); a.forEach((v, i) => { b[2 * i] = v & 255; b[2 * i + 1] = (v >> 8) & 255; }); return b; };
  return { everySeconds: 1, cars, L10, n, s0: Array.from(S[0] ?? []), ds: b64encode(le(ds)), e: b64encode(new Uint8Array(e.buffer, e.byteOffset, e.byteLength)) };
}

export function decodeSnapshot(sn: RecSnapshot): { S: Int32Array[]; E: Int8Array[] } {
  const c = sn.cars.length, L10 = sn.L10;
  const raw = b64decode(sn.ds), ds = new Int16Array(raw.length >> 1);
  for (let i = 0; i < ds.length; i++) ds[i] = ((raw[2 * i] | (raw[2 * i + 1] << 8)) << 16) >> 16;
  const eb = b64decode(sn.e), E: Int8Array[] = [], S: Int32Array[] = [];
  for (let k = 0; k < sn.n; k++) {
    E.push(new Int8Array(eb.buffer.slice(eb.byteOffset + k * c, eb.byteOffset + (k + 1) * c)));
    const row = new Int32Array(c);
    for (let i = 0; i < c; i++) row[i] = k === 0 ? (sn.s0[i] ?? 0) : ((((S[k - 1][i] + ds[(k - 1) * c + i]) % L10) + L10) % L10);
    S.push(row);
  }
  return { S, E };
}

// ---------------------------------------------------------------- structural check (the server's and the tool's)

const isInt = (x: unknown): x is number => typeof x === 'number' && Number.isInteger(x);
const isNum = (x: unknown): x is number => typeof x === 'number' && Number.isFinite(x);
const isStr = (x: unknown, max = 64): x is string => typeof x === 'string' && x.length <= max;

/** Reasons a parsed body is not a RaceRecording of this format; empty when it is. Bounds only: no replay. */
export function checkRecording(x: unknown, o: { maxSteps?: number; maxCars?: number } = {}): string[] {
  const r: string[] = [];
  if (!x || typeof x !== 'object' || Array.isArray(x)) return ['recording missing'];
  const rc = x as Partial<RaceRecording>;
  const maxSteps = o.maxSteps ?? 1_500_000, maxCars = o.maxCars ?? 200;
  if (rc.v !== REC_FORMAT) r.push(`v must be ${REC_FORMAT}`);
  for (const k of ['trackId', 'fieldId', 'aiVersion', 'buildSha', 'physics', 'started'] as const) if (!isStr(rc[k], 96)) r.push(`${k} must be a short string`);
  if (!isInt(rc.seed) || rc.seed < 0 || rc.seed > 4294967295) r.push('seed must be a uint32');
  if (!isInt(rc.laps) || rc.laps < 1 || rc.laps > 10) r.push('laps must be 1..10');
  if (typeof rc.owner !== 'boolean') r.push('owner must be a boolean');
  if (!isNum(rc.durationS) || rc.durationS < 0 || rc.durationS > 6000) r.push('durationS out of range');
  const b = rc.build;
  if (!b || typeof b !== 'object' || !isInt(b.seed) || !isInt(b.laps) || typeof b.realGrid !== 'boolean' || typeof b.playerAi !== 'boolean' || typeof b.lod !== 'boolean' || !isNum(b.strengthPct)
    || !(b.closeRacing === null || typeof b.closeRacing === 'boolean') || !(b.planner === null || b.planner === 'lanes' || b.planner === 'offset')
    || !(b.fieldCap === null || isInt(b.fieldCap)) || !(b.ref === null || isStr(b.ref)) || typeof b.autoShift !== 'boolean' || typeof b.abs !== 'boolean') r.push('build malformed');
  if (!rc.config || typeof rc.config !== 'object' || Array.isArray(rc.config) || Object.keys(rc.config).length > 80) r.push('config malformed');
  const t = rc.inputs;
  if (!t || typeof t !== 'object') r.push('inputs missing');
  else {
    if (!isInt(t.steps) || t.steps <= 0 || t.steps > maxSteps) r.push(`inputs.steps must be 1..${maxSteps}`);
    if (!Array.isArray(t.rows) || t.rows.length > Math.ceil(maxSteps / 10) + 1) r.push('inputs.rows malformed');
    else {
      let prev = -1;
      for (let i = 0; i < t.rows.length; i++) {
        const w = t.rows[i];
        if (!Array.isArray(w) || w.length !== 5 || !w.every(isInt) || w[0] % 10 !== 0 || w[0] <= prev || (i === 0 && w[0] !== 0)
          || Math.abs(w[1]) > 1000 || w[2] < 0 || w[2] > 1000 || w[3] < 0 || w[3] > 1000 || w[4] < 0 || w[4] > 31 || (isInt(t.steps) && w[0] >= t.steps)) { r.push(`inputs.rows[${i}] malformed`); break; }
        prev = w[0];
      }
    }
    if (!Array.isArray(t.ref) || t.ref.length > 64 || !t.ref.every((e) => Array.isArray(e) && e.length === 2 && isInt(e[0]) && (e[1] === null || isStr(e[1])))) r.push('inputs.ref malformed');
    const rs = t.reset;
    if (!rs || !Array.isArray(rs.pos) || rs.pos.length !== 3 || ![...rs.pos, rs.heading, rs.speed].every(isNum)) r.push('inputs.reset malformed');
  }
  if (!Array.isArray(rc.events) || rc.events.length > 5000 || !rc.events.every((e) => Array.isArray(e) && isInt(e[0]) && e[0] >= 0 && ((e[1] === 0 && isNum(e[2])) || (e[1] === 1 && isStr(e[2], 64) && (e[3] === undefined || isStr(e[3], 200)))))) r.push('events malformed');
  const lv = rc.live;
  if (!lv || typeof lv !== 'object') r.push('live missing');
  else {
    if (!Array.isArray(lv.lapTimes) || lv.lapTimes.length > 20 || !lv.lapTimes.every(isNum)) r.push('live.lapTimes malformed');
    if (!Array.isArray(lv.crossings) || lv.crossings.length > maxCars * 12 || !lv.crossings.every((c) => c && isStr(c.car, 16) && isInt(c.lapNr) && isNum(c.t))) r.push('live.crossings malformed');
    if (lv.results !== null && (!Array.isArray(lv.results) || lv.results.length > maxCars || !lv.results.every((c) => c && isStr(c.number, 16) && isNum(c.laps) && (c.time === null || isNum(c.time)) && isNum(c.metres)))) r.push('live.results malformed');
  }
  const sn = rc.snapshot;
  if (sn !== null && sn !== undefined) {
    if (typeof sn !== 'object' || sn.everySeconds !== 1 || !Array.isArray(sn.cars) || sn.cars.length > maxCars || !sn.cars.every((c) => isStr(c, 16)) || !isInt(sn.L10) || sn.L10 <= 0 || sn.L10 > 65000
      || !isInt(sn.n) || sn.n < 0 || sn.n > 6000 || !Array.isArray(sn.s0) || sn.s0.length !== sn.cars.length || !sn.s0.every(isInt) || typeof sn.ds !== 'string' || typeof sn.e !== 'string') r.push('snapshot malformed');
    else if (sn.e.length !== 4 * Math.ceil((sn.n * sn.cars.length) / 3) || sn.ds.length !== 4 * Math.ceil((Math.max(0, sn.n - 1) * sn.cars.length * 2) / 3)) r.push('snapshot is not the size it declares');
  }
  if (rc.aborted !== undefined && rc.aborted !== true) r.push('aborted must be true or absent');
  if (rc.truncated !== undefined && (!rc.truncated || !isInt(rc.truncated.atStep))) r.push('truncated malformed');
  return r;
}

// ---------------------------------------------------------------- the wire form of the rows

/**
 * On the wire (the upload, the stored body, a downloaded file) the input rows are one flat int array `inputs.d` of 5 numbers per
 * row: [(step - previous step) / 10, steer - previous steer, throttle - previous throttle, brake - previous brake, flags] (the
 * first row against zeros). The same rows, 2-5 x smaller after gzip (a 5-lap race of smooth hands: 139 KB -> 29 KB). In memory,
 * and for checkRecording and the re-run, they are the hot-lap trace's `rows` tuples.
 */
export function deltaRows(rows: TraceRow[]): number[] {
  const d: number[] = [];
  let p: TraceRow = [0, 0, 0, 0, 0];
  for (const r of rows) { d.push((r[0] - p[0]) / 10, r[1] - p[1], r[2] - p[2], r[3] - p[3], r[4]); p = r; }
  return d;
}
/** The tuples back from `deltaRows` (null when `d` is not a whole number of rows of integers). */
export function undeltaRows(d: unknown, maxRows = 200_000): TraceRow[] | null {
  if (!Array.isArray(d) || d.length % 5 !== 0 || d.length > 5 * maxRows) return null;
  const rows: TraceRow[] = [];
  let p: TraceRow = [0, 0, 0, 0, 0];
  for (let i = 0; i < d.length; i += 5) {
    const a = d[i], b = d[i + 1], c = d[i + 2], e = d[i + 3], f = d[i + 4];
    if (![a, b, c, e, f].every((x) => Number.isInteger(x))) return null;
    p = [p[0] + a * 10, p[1] + b, p[2] + c, p[3] + e, f];
    rows.push(p);
  }
  return rows;
}
/** A recording as it goes over the wire: `inputs.rows` replaced by `inputs.d`. */
export function toWire(rec: RaceRecording): unknown {
  const { rows, ...rest } = rec.inputs;
  return { ...rec, inputs: { ...rest, d: deltaRows(rows) } };
}
/** A parsed body back to the in-memory form: `inputs.d` unpacked into `inputs.rows` (a body that already has `rows`, or that is not a
 *  recording, passes through; a malformed `d` leaves `rows` missing for checkRecording to refuse). */
export function fromWire(x: unknown): unknown {
  if (!x || typeof x !== 'object' || Array.isArray(x)) return x;
  const rec = x as { inputs?: { rows?: unknown; d?: unknown } };
  const inp = rec.inputs;
  if (!inp || typeof inp !== 'object' || inp.rows !== undefined || inp.d === undefined) return x;
  const { d, ...rest } = inp;
  const rows = undeltaRows(d);
  return { ...rec, inputs: rows ? { ...rest, rows } : { ...rest } };
}

// ---------------------------------------------------------------- compression and the size cap

/** gzip a string; null where CompressionStream does not exist (old Safari). */
export async function gzipText(text: string): Promise<Uint8Array | null> {
  if (typeof CompressionStream === 'undefined') return null;
  const s = new Blob([text]).stream().pipeThrough(new CompressionStream('gzip'));
  return new Uint8Array(await new Response(s).arrayBuffer());
}

/** Read a byte stream, giving up (null) past `max` bytes. */
export async function readBytesCapped(body: ReadableStream<Uint8Array> | null, max: number): Promise<Uint8Array | null> {
  if (!body) return new Uint8Array(0);
  const reader = body.getReader(), parts: Uint8Array[] = [];
  let n = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    n += value.byteLength;
    if (n > max) { try { await reader.cancel(); } catch { /* closed */ } return null; }
    parts.push(value);
  }
  const all = new Uint8Array(n);
  let o = 0;
  for (const p of parts) { all.set(p, o); o += p.byteLength; }
  return all;
}

/** gunzip to text with an output cap (null past it, or when the bytes are not gzip). */
export async function gunzipCapped(bytes: Uint8Array, max: number): Promise<string | null> {
  try {
    const out = await readBytesCapped(new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream('gzip')), max);
    return out ? new TextDecoder().decode(out) : null;
  } catch { return null; }
}

export interface Packed { body: Uint8Array | string; gzip: boolean; truncated: boolean; bytes: number }

/**
 * The upload body within `cap` bytes (gzip when the runtime has it, else the raw JSON). A recording that does not fit loses its
 * position snapshot first, then the tail of the inputs (rows, events and the live data are cut at a step; `truncated` says where).
 * Returns null when nothing fits.
 */
export async function packRecording(rec: RaceRecording, cap = REC_MAX_BYTES): Promise<Packed | null> {
  const attempt = async (r: RaceRecording): Promise<Packed | null> => {
    const text = JSON.stringify(toWire(r)), z = await gzipText(text);
    const body: Uint8Array | string = z ?? text, bytes = z ? z.byteLength : text.length;
    return bytes <= cap ? { body, gzip: !!z, truncated: !!r.truncated, bytes } : null;
  };
  const whole = await attempt(rec);
  if (whole) return whole;
  const noSnap = await attempt({ ...rec, snapshot: null });
  if (noSnap) return noSnap;
  for (let keep = 0.8; keep > 0.05; keep *= 0.8) {
    const p = await attempt(cutRecording({ ...rec, snapshot: null }, Math.floor((rec.inputs.steps * keep) / 10) * 10));
    if (p) return p;
  }
  return null;
}

/**
 * The recording as it was at `step`: rows, refs and events before it, the crossings up to that director time (the director
 * clock is the step count x 1 ms) and the player's lap times they carry; the results are dropped (the flag is later) and so is
 * the snapshot. The offline re-run stops at `truncated.atStep` and checks what is left.
 */
export function cutRecording(rec: RaceRecording, step: number): RaceRecording {
  const tEnd = step * 0.001 + 1e-9, me = String(rec.config.playerNumber ?? '');
  const crossings = rec.live.crossings.filter((c) => c.t <= tEnd);
  const mine = crossings.filter((c) => c.car === me).length;
  return {
    ...rec,
    inputs: { ...rec.inputs, steps: step, rows: rec.inputs.rows.filter((r) => r[0] < step), ref: rec.inputs.ref.filter((r) => r[0] < step) },
    events: rec.events.filter((e) => e[0] <= step),
    live: { lapTimes: rec.live.lapTimes.slice(0, Math.max(0, mine - 1)), crossings, results: null },
    snapshot: null,
    truncated: { atStep: step },
  };
}
