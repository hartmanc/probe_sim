// A reset vehicle must be bit-identical to a freshly constructed one (replays, race restarts).
import { expect, test } from 'vitest';
import { Vehicle } from '../index';
import { createFlatSurface } from '../devtrack';
import { DT, input, probeSpec, rng } from './helpers';

function snapshot(v: Vehicle): string {
  const o: Record<string, unknown> = {};
  for (const [k, val] of Object.entries(v)) {
    if (k === 'nanResets' || k === 'cw' || k === 'spec') continue;
    o[k] = ArrayBuffer.isView(val) ? Array.from(val as unknown as ArrayLike<number>) : val;
  }
  return JSON.stringify(o, (_k, x) => (typeof x === 'number' && !Number.isFinite(x) ? String(x) : x));
}

test('reset() after a drive equals a new Vehicle: same state, same behaviour for 1000 steps', () => {
  const spec = probeSpec();
  const flat = createFlatSurface();
  const used = new Vehicle(spec, { autoShift: true });
  used.reset([0, 0, 0], 0, 20);
  const r = rng(7);
  for (let i = 0; i < 4300; i++) {
    used.setScheduledGear(i % 1000 < 500 ? 3 : 0);
    used.step(input({ steer: Math.sin(i * 0.003), throttle: r(), brake: i % 900 > 700 ? 1 : 0, handbrake: i % 1500 > 1400, shiftUp: i === 1000, shiftDown: i === 2500 }), flat, DT);
  }
  used.reportImpact(3, 'car');
  const fresh = new Vehicle(spec, { autoShift: true });
  fresh.reset([5, 2, 0], 0.3, 15);
  used.reset([5, 2, 0], 0.3, 15);
  expect(snapshot(used)).toBe(snapshot(fresh));
  const r1 = rng(3), r2 = rng(3);
  for (let i = 0; i < 1000; i++) {
    fresh.step(input({ steer: 0.2 * Math.sin(i * 0.01), throttle: r1() }), flat, DT);
    used.step(input({ steer: 0.2 * Math.sin(i * 0.01), throttle: r2() }), flat, DT);
  }
  expect(snapshot(used)).toBe(snapshot(fresh));
  expect(JSON.stringify(used.state)).toBe(JSON.stringify(fresh.state));
});
