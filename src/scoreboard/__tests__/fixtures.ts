// Test fixtures: the real Laguna Seca + Probe GT assets from public/, and a line-following autopilot.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { lineToWorld, loadHeightfield, type TrackJson } from '../../physics';
import { HotlapSim, type GhostsLike, type RawInput, type SceneryLike, type SimAssets } from '../sim';
import type { Lap } from '../../app/timing';
import type { InputTrace } from '../types';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const buf = (p: string): ArrayBuffer => Uint8Array.from(readFileSync(pub + p)).buffer;
const json = <T>(p: string): T => JSON.parse(readFileSync(pub + p, 'utf8')) as T;

let cached: SimAssets | null = null;
/** Decoded assets exactly as the server loads them (api/_lib/assets.ts). */
export function lagunaAssets(): SimAssets {
  if (cached) return cached;
  const dir = 'tracks/laguna_seca/';
  const track = json<TrackJson>(dir + 'track.json');
  const scenery = json<SceneryLike>(dir + 'scenery.json');
  const farFile = scenery.far?.heightfield?.file;
  cached = {
    trackId: 'laguna_seca', carId: 'probe_gt', track,
    heightfield: loadHeightfield(buf(dir + 'heightfield.bin')),
    carJson: json<unknown>('cars/probe_gt/car.json'),
    scenery,
    farHeightfield: farFile ? loadHeightfield(buf(dir + farFile)) : null,
    ghosts: json<GhostsLike>(dir + 'ghosts.json'),
  };
  return cached;
}

/**
 * A simple autopilot (pure pursuit on the ghosts' racing line, speed target = `pace` × the fastest real
 * ghost's speed, look-ahead braking). Returns a sampler for HotlapSim.step(); it reads only sim state.
 */
export function autopilot(sim: HotlapSim, pace = 0.85): () => RawInput {
  const a = sim.assets, track = a.track, g = a.ghosts, L = track.length_m;
  const off = g.line.offset_m, grid = g.s_grid_m;
  const ref = [...g.laps].filter((l) => l.kind === 'real').sort((x, y) => (x.lap_time_s ?? 0) - (y.lap_time_s ?? 0))[0];
  const at = (arr: number[], s: number) => {
    const u = (((s % L) + L) % L) / grid, i = Math.floor(u), t = u - i;
    return arr[i % arr.length] * (1 - t) + arr[(i + 1) % arr.length] * t;
  };
  const offsetAt = (s: number) => at(off, s);
  const vAt = (s: number) => pace * at(ref.v_mps, s);
  const spec = sim.spec, wb = spec.wheelbase, st = spec.steering;
  let integ = 0;
  return () => {
    const s0 = sim.vehicle.state;
    const [qx, qy, qz, qw] = s0.quat;
    const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const s = sim.projector.project(s0.pos[0], s0.pos[1]).s;
    const v = Math.max(1, s0.speed);
    const rx = s0.pos[0] - cy * wb / 2, ry = s0.pos[1] - sy * wb / 2;
    const Ld = 4 + 0.45 * v;
    const [tx, ty] = lineToWorld(track, offsetAt, s - wb / 2 + Ld).pos;
    const dx = tx - rx, dy = ty - ry;
    const ang = Math.atan2(-sy * dx + cy * dy, cy * dx + sy * dy);
    const k = (2 * Math.sin(ang)) / Math.hypot(dx, dy);
    let delta = Math.atan(wb * k) + 0.15 * (v * k - s0.angVel[2]);
    delta += (2.3 * Math.PI / 180) * Math.max(-1.3, Math.min(1.3, (v * v * k) / 9.81));
    const vr = v / st.shapingSpeed;
    const maxA = Math.max(st.minAngleDeg, st.maxAngleDeg / (1 + vr * vr));
    const steer = Math.max(-1, Math.min(1, (delta * 180 / Math.PI) / maxA));
    // target: the slowest of the reference speeds over the next ~2 s of braking distance
    let target = Infinity;
    for (let d = 0; d <= 160; d += 8) {
      const vd = vAt(s + d);
      const vmax = Math.sqrt(vd * vd + 2 * 7.5 * d); // can still brake from vmax to vd over d at ~0.75 g
      target = Math.min(target, vmax);
    }
    const e = target - v;
    integ = Math.max(-2, Math.min(5, integ + e * 0.01));
    if (e < -1.5) return { steer, throttle: 0, brake: Math.min(1, -e * 0.25), handbrake: false };
    return { steer, throttle: Math.max(0, Math.min(1, 0.35 * e + 0.1 * integ + 0.45)), brake: 0, handbrake: false };
  };
}

/** Drive one flying lap with the autopilot and return the lap + its trace (as JSON would deliver it). */
export function recordLap(pace = 0.85): { lap: Lap; trace: InputTrace } {
  const sim = new HotlapSim(lagunaAssets(), { record: true });
  const drive = autopilot(sim, pace);
  for (let i = 0; i < 400_000; i++) {
    const ev = sim.step(drive);
    if (ev && ev !== 'start') return { lap: ev, trace: JSON.parse(JSON.stringify(sim.trace())) };
  }
  throw new Error('autopilot did not finish a lap');
}
