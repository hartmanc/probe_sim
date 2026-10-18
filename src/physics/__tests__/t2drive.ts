// Line-following driver for the T2 braking test on the real Laguna package.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createTrackProjector, createTrackSurface, lineToWorld, loadHeightfield, Vehicle, type CarSpec, type TrackJson } from '../index';
import { DT, input } from './helpers';
import { stickForAngle } from './manoeuvres';

const dir = fileURLToPath(new URL('../../../public/tracks/laguna_seca/', import.meta.url));
export const track = JSON.parse(readFileSync(dir + 'track.json', 'utf8')) as TrackJson;
const hf = loadHeightfield(Uint8Array.from(readFileSync(dir + 'heightfield.bin')).buffer);
const ghosts = JSON.parse(readFileSync(dir + 'ghosts.json', 'utf8')) as { s_grid_m: number; line: { offset_m: number[] }; laps: { id: string; v_mps: number[] }[] };
const driver_a = (ghosts.laps.find((l) => l.id.startsWith('driver_a')) ?? ghosts.laps[0]).v_mps;
/** driver A's speed at s, m/s. */
export function driver_aV(s: number): number {
  const u = Math.max(0, s) / ghosts.s_grid_m, i = Math.floor(u), t = u - i;
  return driver_a[i % driver_a.length] * (1 - t) + driver_a[(i + 1) % driver_a.length] * t;
}
export const surface = createTrackSurface(track, hf);
export const projector = createTrackProjector(track);
const grid = ghosts.s_grid_m, off = ghosts.line.offset_m;
export function offsetAt(s: number): number {
  const L = track.length_m;
  let u = (((s % L) + L) % L) / grid;
  const i = Math.floor(u), t = u - i;
  return off[i % off.length] * (1 - t) + off[(i + 1) % off.length] * t;
}
const linePt = (s: number) => lineToWorld(track, offsetAt, s).pos;

export let DEBUG = false;
export function setDebug(d: boolean): void { DEBUG = d; }

export interface T2Result {
  /** max |lateral error| to the line after the first 0.5 s of braking, m */
  maxErrAfter: number;
  maxErr: number;
  /** time each front wheel spent past 35 % braking slip, s */
  lockTime: [number, number];
  /** longest continuous front lock, s */
  longestLock: number;
  minSpeed: number;
  spun: boolean;
  absSeen: boolean;
}

/**
 * Arrive at 140 km/h on the racing line, brake at `pedal` from s = brakeAt (driver A's braking point) whenever
 * the car is faster than driver A was at that s, and follow the line through the T2 hairpin (apex s ≈ 479).
 */
export function driveT2(spec: CarSpec, pedal: number, opts: { abs?: boolean; brakeAt?: number; holdTo?: number } = {}): T2Result {
  // holdTo (km/h): keep the pedal down from brakeAt until the speed falls to this (a late, committed stop)
  const holdTo = opts.holdTo !== undefined ? opts.holdTo / 3.6 : 0;
  let holding = holdTo > 0;
  const brakeAt = opts.brakeAt ?? 335;
  const car = new Vehicle(spec, { autoShift: true });
  if (opts.abs !== undefined) car.abs = opts.abs;
  const s0 = brakeAt - 50;
  const p = lineToWorld(track, offsetAt, s0);
  car.reset(p.pos, p.heading, 140 / 3.6);
  const inp = input();
  const L = spec.wheelbase;
  let braking = false, tb = 0, maxErr = 0, maxErrAfter = 0, longest = 0, minSpeed = Infinity, spun = false, absSeen = false, done = false;
  const lock: [number, number] = [0, 0], run = [0, 0];
  let integ = 0;
  for (let i = 0; i < 9000 && !done; i++) {
    const st = car.state;
    const [qx, qy, qz, qw] = st.quat;
    const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const pr = projector.project(st.pos[0], st.pos[1]);
    const s = pr.s, v = Math.max(1, st.speed);
    const err = pr.lateral - offsetAt(s);
    // pure pursuit from the rear axle + yaw-rate damping
    const rx = st.pos[0] - cy * L / 2, ry = st.pos[1] - sy * L / 2;
    const Ld = 4 + 0.45 * v;
    const [tx, ty] = linePt(s - L / 2 + Ld);
    const dx = tx - rx, dy = ty - ry;
    const a = Math.atan2(-sy * dx + cy * dy, cy * dx + sy * dy);
    const k = (2 * Math.sin(a)) / Math.hypot(dx, dy);
    let delta = Math.atan(L * k) + 0.15 * (v * k - st.angVel[2]);
    delta += (2.3 * Math.PI / 180) * Math.max(-1.3, Math.min(1.3, (v * v * k) / 9.81)); // understeer feed-forward
    inp.steer = stickForAngle(spec, v, (delta * 180) / Math.PI);
    if (!braking && s >= brakeAt && s < brakeAt + 200) braking = true;
    if (braking && s > 500) done = true;
    if (braking && holding && st.speed <= holdTo) holding = false;
    if (braking && (holding || st.speed > driver_aV(s) + 0.5)) { inp.brake = pedal; inp.throttle = 0; tb += DT; }
    else if (braking) { inp.brake = 0; inp.throttle = 0.15; if (tb > 0) tb += DT; }
    else { const e = 140 / 3.6 - st.speed; integ = Math.max(-2, Math.min(5, integ + e * DT)); inp.throttle = Math.max(0, Math.min(1, 0.3 * e + 0.1 * integ + 0.4)); inp.brake = 0; }
    car.step(inp, surface, DT);
    if (DEBUG && i % 100 === 0) console.log(`s ${s.toFixed(0)} v ${(st.speed * 3.6).toFixed(0)} err ${err.toFixed(2)} steer ${inp.steer.toFixed(2)} brk ${inp.brake} lat ${pr.lateral.toFixed(1)} off ${offsetAt(s).toFixed(1)}`);
    if (braking) {
      maxErr = Math.max(maxErr, Math.abs(err));
      if (tb > 0.5) maxErrAfter = Math.max(maxErrAfter, Math.abs(err));
      minSpeed = Math.min(minSpeed, car.state.speed);
      if (car.state.absActive) absSeen = true;
      for (let w = 0; w < 2; w++) {
        const ws = car.state.wheels[w];
        const vx = car.state.speed;
        const slip = vx > 2 ? 1 - (ws.omega * spec.wheel.radius) / vx : 0;
        if (slip > 0.35) { lock[w] += DT; run[w] += DT; longest = Math.max(longest, run[w]); } else run[w] = 0;
      }
      const [x, y, z, w] = car.state.quat;
      const yawNow = Math.atan2(2 * (x * y + z * w), 1 - 2 * (y * y + z * z));
      const vh = Math.atan2(car.state.vel[1], car.state.vel[0]);
      let b = Math.abs(yawNow - vh); if (b > Math.PI) b = 2 * Math.PI - b;
      if (b > 0.5) spun = true;
    }
  }
  return { maxErrAfter, maxErr, lockTime: lock, longestLock: longest, minSpeed: minSpeed * 3.6, spun, absSeen };
}
