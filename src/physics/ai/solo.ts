// A single AI car alone on the track (headless, the race physics): used by the field calibration
// (tools/race/calibrate_field.ts) and the tests.

import type { Surface } from '../types';
import { Vehicle } from '../vehicle';
import type { RaceLine } from './line';
import { AiDriver } from './driver';
import { buildAiSpec, buildSpeedProfile, measureCarPerf, type IdentityCar, type ProfileOptions } from './field';
import { Traffic } from './traffic';

export interface SoloResult {
  /** completed flying lap times, s */
  laps: number[];
  /** recoveries (marshal resets) needed, steps with >= 3 wheels off the track */
  recoveries: number; offSteps: number;
  nanResets: number;
}

/**
 * Drive `laps` flying laps alone: start rolling 520 m before the line on the racing line, time each
 * crossing of s = 0. Control tick every `ctlEvery` physics steps of `dt`.
 */
export function runSolo(line: RaceLine, surface: Surface, probeJson: any, identity: IdentityCar | null, scale: number,
  laps: number, opts: { dt?: number; ctlEvery?: number; maxTime?: number; profile?: ProfileOptions; onRecovery?: (s: number, t: number, speed: number) => void } = {}): SoloResult {
  const dt = opts.dt ?? 0.001, every = opts.ctlEvery ?? 2;
  const spec = buildAiSpec(probeJson, identity, scale);
  const perf = measureCarPerf(spec);
  const profile = buildSpeedProfile(line, perf, spec, opts.profile);
  const car = new Vehicle(spec, { autoShift: true });
  const tr = new Traffic(1, line.L);
  tr.front[0] = spec.hull.front; tr.rear[0] = -spec.hull.rear; tr.hw[0] = spec.hull.halfWidth; tr.pace[0] = 120;
  const drv = new AiDriver(car, line, perf, spec, profile, { number: 'solo', scale, targetLap: 120, sigma: 0, aggression: 1, seed: 1 }, 0, tr);
  drv.ctl.noise = false;
  // start on the run down to T11, gently: a fresh vehicle launched at 30 m/s into the hairpin spun the powerful RWD cars
  const s0 = line.L - 520;
  const pos = new Float64Array(2);
  line.pointAt(s0, line.at(line.off, s0), pos);
  const z = surface.sample(pos[0], pos[1]).z;
  car.reset([pos[0], pos[1], z], line.headingAt(s0), Math.min(18, 0.8 * line.at(profile, s0)));
  let t = 0, U = s0 - line.L, hint = -1;
  let lastCross = NaN;
  const out: number[] = [];
  let recoveries = 0, offSteps = 0;
  const maxTime = opts.maxTime ?? (laps + 0.5) * 200;
  let step = 0;
  const update = () => {
    const p = line.project(car.state.pos[0], car.state.pos[1], hint);
    hint = p.index;
    let d = p.s - tr.s[0];
    if (d > line.L / 2) d -= line.L; else if (d < -line.L / 2) d += line.L;
    tr.s[0] = p.s; tr.lat[0] = p.lateral; tr.v[0] = car.state.speed;
    return d;
  };
  tr.s[0] = s0; update(); tr.U[0] = U;
  while (t < maxTime && out.length < laps) {
    if (step % every === 0) drv.update(dt * every);
    car.step(drv.input, surface, dt);
    t += dt; step++;
    const Uprev = U;
    U += update();
    tr.U[0] = U;
    let off = 0;
    for (const w of car.state.wheels) if (!w.onTrack) off++;
    if (off >= 3) offSteps++;
    if (Math.floor(U / line.L) > Math.floor(Uprev / line.L)) {
      const tc = t - dt * (U - Math.floor(U / line.L) * line.L) / Math.max(1e-6, U - Uprev);
      if (!Number.isNaN(lastCross)) out.push(tc - lastCross);
      lastCross = tc;
    }
    if (drv.needsRecovery) {
      recoveries++;
      const s = tr.s[0];
      opts.onRecovery?.(s, t, car.state.speed);
      line.pointAt(s, line.at(line.off, s), pos);
      { const sm = surface.sample(pos[0], pos[1]); car.reset([pos[0], pos[1], sm.z], line.headingAt(s), 8, [sm.nx, sm.ny, sm.nz]); }
      drv.resetState();
    }
  }
  return { laps: out, recoveries, offSteps, nanResets: car.nanResets };
}
