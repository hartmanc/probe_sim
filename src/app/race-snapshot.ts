// The race Worker's per-frame snapshot (?worker=1, docs/performance.md): every car's state packed into one transferable
// Float32Array (CAR_STRIDE floats per car) plus a Float64Array of the per-car race numbers that must stay exact
// (distance, lap times). Pure: the worker packs, the main thread unpacks into the same VehicleState objects the
// renderer, camera, HUD and audio already read.
import type { VehicleState, ImpactInfo } from '../physics/types';

export const WHEEL_F = 14;
export const CAR_STRIDE = 27 + 4 * WHEEL_F;      // 83
export const CAR64_STRIDE = 8;
const KINDS = ['concrete', 'armco', 'tyres', 'pitwall', 'fence', 'building', 'tree', 'boundary', 'car'] as const;

/** The per-car race numbers (Float64): the distance, the track position and the lap book-keeping. */
export interface CarRace { U: number; s: number; lastLap: number; bestLap: number; finishAt: number; finished: boolean; lapIdx: number; lapsDone: number }

export function packCar(st: VehicleState, brake: number, f: Float32Array, o: number): void {
  f[o] = st.pos[0]; f[o + 1] = st.pos[1]; f[o + 2] = st.pos[2];
  f[o + 3] = st.quat[0]; f[o + 4] = st.quat[1]; f[o + 5] = st.quat[2]; f[o + 6] = st.quat[3];
  f[o + 7] = st.vel[0]; f[o + 8] = st.vel[1]; f[o + 9] = st.vel[2];
  f[o + 10] = st.angVel[0]; f[o + 11] = st.angVel[1]; f[o + 12] = st.angVel[2];
  f[o + 13] = st.rpm; f[o + 14] = st.gear; f[o + 15] = st.speed; f[o + 16] = st.gLat; f[o + 17] = st.gLong; f[o + 18] = st.throttleOut;
  f[o + 19] = st.absActive ? 1 : 0; f[o + 20] = st.launched ? 1 : 0; f[o + 21] = st.launchedAt ?? NaN;
  const im = st.impact;
  if (im) { const k = KINDS.indexOf(im.kind as typeof KINDS[number]); f[o + 22] = k < 0 ? 7 : k; f[o + 23] = im.speedNormal; f[o + 24] = im.speed; f[o + 25] = im.t; } else { f[o + 22] = -1; f[o + 23] = 0; f[o + 24] = 0; f[o + 25] = 0; }
  f[o + 26] = brake;
  for (let i = 0; i < 4; i++) {
    const w = st.wheels[i], p = o + 27 + i * WHEEL_F;
    f[p] = w.pos[0]; f[p + 1] = w.pos[1]; f[p + 2] = w.pos[2];
    f[p + 3] = w.spinAngle; f[p + 4] = w.steer; f[p + 5] = w.compression; f[p + 6] = w.omega; f[p + 7] = w.slipRatio; f[p + 8] = w.slipAngle;
    f[p + 9] = w.slipUse; f[p + 10] = w.load; f[p + 11] = w.mu; f[p + 12] = w.onTrack ? 1 : 0; f[p + 13] = w.paved ? 1 : 0;
  }
}

/** Write a packed car into an existing VehicleState in place (no allocation except a new impact object when it changed). Returns the brake. */
export function unpackCar(f: Float32Array, o: number, st: VehicleState): number {
  st.pos[0] = f[o]; st.pos[1] = f[o + 1]; st.pos[2] = f[o + 2];
  st.quat[0] = f[o + 3]; st.quat[1] = f[o + 4]; st.quat[2] = f[o + 5]; st.quat[3] = f[o + 6];
  st.vel[0] = f[o + 7]; st.vel[1] = f[o + 8]; st.vel[2] = f[o + 9];
  st.angVel[0] = f[o + 10]; st.angVel[1] = f[o + 11]; st.angVel[2] = f[o + 12];
  st.rpm = f[o + 13]; st.gear = f[o + 14]; st.speed = f[o + 15]; st.gLat = f[o + 16]; st.gLong = f[o + 17]; st.throttleOut = f[o + 18];
  st.absActive = f[o + 19] !== 0; st.launched = f[o + 20] !== 0; st.launchedAt = f[o + 21];
  const k = f[o + 22];
  if (k < 0) st.impact = null;
  else {
    const kind = KINDS[k] as string, t = f[o + 25], cur: ImpactInfo | null | undefined = st.impact;
    if (!cur || cur.t !== t || cur.kind !== kind) st.impact = { speedNormal: f[o + 23], speed: f[o + 24], kind, t };
  }
  for (let i = 0; i < 4; i++) {
    const w = st.wheels[i], p = o + 27 + i * WHEEL_F;
    w.pos[0] = f[p]; w.pos[1] = f[p + 1]; w.pos[2] = f[p + 2];
    w.spinAngle = f[p + 3]; w.steer = f[p + 4]; w.compression = f[p + 5]; w.omega = f[p + 6]; w.slipRatio = f[p + 7]; w.slipAngle = f[p + 8];
    w.slipUse = f[p + 9]; w.load = f[p + 10]; w.mu = f[p + 11]; w.onTrack = f[p + 12] !== 0; w.paved = f[p + 13] !== 0;
  }
  return f[o + 26];
}

export function packRace(c: CarRace, f: Float64Array, o: number): void {
  f[o] = c.U; f[o + 1] = c.s; f[o + 2] = c.lastLap; f[o + 3] = c.bestLap; f[o + 4] = c.finishAt; f[o + 5] = c.finished ? 1 : 0; f[o + 6] = c.lapIdx; f[o + 7] = c.lapsDone;
}
export function unpackRace(f: Float64Array, o: number, out: CarRace): CarRace {
  out.U = f[o]; out.s = f[o + 1]; out.lastLap = f[o + 2]; out.bestLap = f[o + 3]; out.finishAt = f[o + 4]; out.finished = f[o + 5] !== 0; out.lapIdx = f[o + 6]; out.lapsDone = f[o + 7];
  return out;
}
