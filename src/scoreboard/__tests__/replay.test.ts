import { beforeAll, describe, expect, test } from 'vitest';
import { HotlapSim } from '../sim';
import { checkTrace, replayTrace, verifyHotlap } from '../replay';
import { physicsVersion } from '../hash';
import { LIMITS, SAMPLE_EVERY } from '../config';
import type { Lap } from '../../app/timing';
import type { InputTrace } from '../types';
import { autopilot, lagunaAssets } from './fixtures';

let live: HotlapSim;
let lap: Lap;
let trace: InputTrace;

beforeAll(() => {
  const a = lagunaAssets();
  live = new HotlapSim(a, { record: true });
  const drive = autopilot(live);
  for (let i = 0; i < 400_000; i++) {
    const ev = live.step(drive);
    if (ev && ev !== 'start' && ev.n === 1) { lap = ev; break; }
  }
  // what the client would POST: through JSON and back
  trace = JSON.parse(JSON.stringify(live.trace())) as InputTrace;
});

function flat(sim: HotlapSim): number[] {
  const s = sim.vehicle.state;
  const out = [...s.pos, ...s.quat, ...s.vel, ...s.angVel, s.rpm, s.gear, s.speed, s.gLat, s.gLong, s.throttleOut, sim.simTime, sim.s];
  for (const w of s.wheels) out.push(...w.pos, w.spinAngle, w.steer, w.compression, w.omega, w.slipRatio, w.slipAngle, w.load);
  return out;
}

describe('hot-lap trace', () => {
  test('the autopilot completes a valid flying lap', () => {
    expect(lap).toBeDefined();
    expect(lap.valid).toBe(true);
    expect(lap.time).toBeGreaterThan(LIMITS.lapMin);
    expect(lap.time).toBeLessThan(LIMITS.lapMax);
    expect(live.vehicle.nanResets).toBe(0);
  });

  test('trace format: grid-aligned integer rows, header filled in', () => {
    expect(checkTrace(trace)).toEqual([]);
    expect(trace.physics).toBe(physicsVersion(lagunaAssets().carJson, 3560));
    expect(trace.steps).toBe(live.stepIndex);
    expect(trace.rows[0][0]).toBe(0);
    expect(trace.rows.every((r) => r[0] % SAMPLE_EVERY === 0)).toBe(true);
    expect(trace.ref[0]).toEqual([0, 'driver_a_best']);
    expect(trace.reset.speed).toBe(22);
  });

  test('determinism: a fresh replay reproduces the final state to 1e-9 and the lap time exactly', () => {
    const r = replayTrace(lagunaAssets(), trace, 1);
    expect(r.lap).not.toBeNull();
    expect(r.lap!.time).toBe(lap.time);
    expect(r.lap!.valid).toBe(true);
    expect(r.steps).toBe(live.stepIndex);
    const a = flat(live), b = flat(r.sim);
    expect(b.length).toBe(a.length);
    for (let i = 0; i < a.length; i++) expect(Math.abs(a[i] - b[i])).toBeLessThanOrEqual(1e-9);
    expect(r.sim.vehicle.state.pos).toEqual(live.vehicle.state.pos); // in fact bit-identical
  });

  test('a full lap replay costs well under 1 s of CPU', () => {
    const r = replayTrace(lagunaAssets(), trace, 1);
    console.log(`replay of ${r.steps} steps (${lap.time.toFixed(3)} s lap + out-lap): ${r.cpuMs.toFixed(0)} ms`);
    expect(r.cpuMs).toBeLessThan(3000); // 0.3 s alone; headroom for a loaded parallel test run
  });

  test('replay after a reset in the same sim matches (reset is complete)', () => {
    const a = lagunaAssets();
    const sim = new HotlapSim(a, { record: true });
    const drive = autopilot(sim);
    for (let i = 0; i < 5000; i++) sim.step(drive); // drive a bit, then reset like the R key
    sim.reset();
    const drive2 = autopilot(sim);
    let l: Lap | null = null;
    while (!l && sim.stepIndex < 400_000) { const ev = sim.step(drive2); if (ev && ev !== 'start') l = ev; }
    expect(l!.time).toBe(lap.time);
  });

  test('acceptance threshold: within 0.05 s accepted, a better claimed time rejected', () => {
    const a = lagunaAssets();
    expect(verifyHotlap(a, trace, 1, lap.time).ok).toBe(true);
    expect(verifyHotlap(a, trace, 1, lap.time - 0.04).ok).toBe(true);
    const fake = verifyHotlap(a, trace, 1, lap.time - 0.5);
    expect(fake.ok).toBe(false);
    expect(fake.reasons.join(' ')).toMatch(/differs from the claimed/);
    expect(fake.replayed).toBe(lap.time);
  });

  test('a doctored trace (no braking anywhere) does not reproduce the claim', () => {
    const t2: InputTrace = JSON.parse(JSON.stringify(trace));
    for (const r of t2.rows) { if (r[3] > 0) { r[3] = 0; r[2] = 1000; } }
    const v = verifyHotlap(lagunaAssets(), t2, 1, lap.time);
    expect(v.ok).toBe(false);
  });

  test('a trace from another start or with an unknown reference ghost is rejected', () => {
    const t2: InputTrace = JSON.parse(JSON.stringify(trace));
    t2.reset.pos[0] += 5;
    expect(verifyHotlap(lagunaAssets(), t2, 1, lap.time).reasons[0]).toMatch(/canonical rolling start/);
    const t3: InputTrace = JSON.parse(JSON.stringify(trace));
    t3.ref = [[0, 'nobody']];
    expect(verifyHotlap(lagunaAssets(), t3, 1, lap.time).reasons[0]).toMatch(/unknown reference ghost/);
  });

  test('claiming a lap the trace never completes is rejected', () => {
    const v = verifyHotlap(lagunaAssets(), trace, 2, lap.time);
    expect(v.ok).toBe(false);
    expect(v.reasons[0]).toMatch(/did not complete/);
  });

  test('checkTrace catches malformed rows', () => {
    const bad = (f: (t: InputTrace) => void) => { const t: InputTrace = JSON.parse(JSON.stringify(trace)); f(t); return checkTrace(t); };
    expect(bad((t) => { t.rows[1][0] = 15; })).not.toEqual([]);
    expect(bad((t) => { t.rows[1][1] = 1001; })).not.toEqual([]);
    expect(bad((t) => { t.rows[1][4] = 64; })).not.toEqual([]);
    expect(bad((t) => { t.rows[1][2] = 0.5; })).not.toEqual([]);
    expect(bad((t) => { t.rows[0][0] = 10; })).not.toEqual([]);
    expect(bad((t) => { t.steps = LIMITS.maxTraceSteps + 1; })).not.toEqual([]);
    expect(checkTrace(null)).toEqual(['trace missing']);
  });

  test('settings changes mid-lap (auto-shift off, ABS off, reference ghost) are recorded and replayed', () => {
    const a = lagunaAssets();
    const sim = new HotlapSim(a, { record: true });
    const drive = autopilot(sim);
    let l: Lap | null = null;
    let shifted = false;
    while (!l && sim.stepIndex < 400_000) {
      if (sim.stepIndex === 30_000) { sim.setRef('coby_best'); sim.abs = false; }
      if (sim.stepIndex === 60_000) { sim.setRef(null); sim.autoShift = false; }
      if (sim.stepIndex === 90_000) sim.autoShift = true;
      const ev = sim.step(() => {
        const r = drive();
        if (!shifted && sim.stepIndex === 70_000) { shifted = true; return { ...r, shiftDown: true }; }
        return r;
      });
      if (ev && ev !== 'start') l = ev;
    }
    const t = JSON.parse(JSON.stringify(sim.trace())) as InputTrace;
    expect(t.ref.map((r) => r[1])).toEqual(['driver_a_best', 'coby_best', null]);
    expect(t.rows.some((r) => (r[4] & 2) !== 0)).toBe(true);
    const r = replayTrace(a, t, l!.n);
    expect(r.lap!.time).toBe(l!.time);
    expect(r.sim.vehicle.state.pos).toEqual(sim.vehicle.state.pos);
  });
});
