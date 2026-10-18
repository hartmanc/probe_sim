// Car-vs-car contacts: no tunnelling, no launch, momentum roughly conserved, impacts surfaced.
import { expect, test } from 'vitest';
import { Vehicle } from '../index';
import { CarCollider, type CarBody } from '../cars';
import { createFlatSurface } from '../devtrack';
import { DT, input, probeSpec } from './helpers';

function run(setup: (a: Vehicle, b: Vehicle) => void, steps: number, inA = input(), inB = input()) {
  const spec = probeSpec();
  const flat = createFlatSurface();
  const a = new Vehicle(spec), b = new Vehicle(spec);
  setup(a, b);
  const col = new CarCollider();
  const bodies: CarBody[] = [a, b].map((v) => ({ vehicle: v, front: spec.hull.front, rear: spec.hull.rear, halfWidth: spec.hull.halfWidth }));
  const order = new Int32Array([0, 1]), s = new Float64Array(2);
  let contacts = 0, maxDepth = 0, maxVz = 0, maxTilt = 0, minSideGap = Infinity;
  const p0 = spec.mass * (a.state.vel[0] + b.state.vel[0]);
  for (let i = 0; i < steps; i++) {
    a.step(inA, flat, DT); b.step(inB, flat, DT);
    // "s" along +x for the broad phase
    s[0] = a.state.pos[0] + 1000; s[1] = b.state.pos[0] + 1000;
    if (s[0] <= s[1]) { order[0] = 0; order[1] = 1; } else { order[0] = 1; order[1] = 0; }
    const n = col.resolve(bodies, order, s, 1e6);
    contacts += n;
    for (let k = 0; k < n; k++) maxDepth = Math.max(maxDepth, col.events[k].depth);
    if (Math.abs(a.state.pos[0] - b.state.pos[0]) < 3.5) minSideGap = Math.min(minSideGap, Math.abs(a.state.pos[1] - b.state.pos[1]));
    for (const v of [a, b]) {
      maxVz = Math.max(maxVz, Math.abs(v.state.vel[2]));
      const [x, y] = v.state.quat; maxTilt = Math.max(maxTilt, 2 * Math.hypot(x, y));
    }
  }
  const p1 = spec.mass * (a.state.vel[0] + b.state.vel[0]);
  return { a, b, contacts, maxDepth, maxVz, maxTilt, p0, p1, minSideGap };
}

test('rear-end at 15 m/s closing: no tunnelling, no launch, momentum kept, impact kind car', () => {
  const r = run((a, b) => { a.reset([0, 0, 0], 0, 35); b.reset([7, 0, 0], 0, 20); }, 1500);
  expect(r.contacts).toBeGreaterThan(0);
  expect(r.a.state.pos[0]).toBeLessThan(r.b.state.pos[0]);              // still behind: no tunnelling
  expect(r.b.state.pos[0] - r.a.state.pos[0]).toBeGreaterThan(4.0);      // boxes separated (hull length 4.52)
  expect(r.maxDepth).toBeLessThan(0.15);
  expect(r.maxVz).toBeLessThan(2);                                        // no launch
  expect(r.maxTilt).toBeLessThan(0.2);
  expect(r.a.state.impact?.kind).toBe('car');
  expect(r.b.state.impact?.kind).toBe('car');
  expect(r.a.state.impact!.speedNormal).toBeGreaterThan(10);
  // the hit: the front car speeds up, the rear car slows (low restitution)
  expect(r.b.state.speed).toBeGreaterThan(20);
  expect(r.a.state.speed).toBeLessThan(r.b.state.speed + 1);
});

test('side swipe at 3 m/s lateral: cars pushed apart, stay upright', () => {
  // b alongside a, a steering into it
  const r = run((a, b) => { a.reset([0, 0, 0], 0.08, 25); b.reset([0, 2.2, 0], 0, 25); }, 2000, input({ throttle: 0.3 }), input({ throttle: 0.3 }));
  expect(r.contacts).toBeGreaterThan(0);
  expect(r.maxDepth).toBeLessThan(0.15);
  expect(r.maxVz).toBeLessThan(2);
  expect(r.maxTilt).toBeLessThan(0.25);
  expect(r.minSideGap).toBeGreaterThan(1.55); // never overlapping side by side (2 x 0.86 half width)
  expect(r.a.nanResets + r.b.nanResets).toBe(0);
});

test('head-on at 60 m/s closing does not pass through', () => {
  const r = run((a, b) => { a.reset([0, 0, 0], 0, 30); b.reset([20, 0.3, 0], Math.PI, 30); }, 600);
  expect(r.contacts).toBeGreaterThan(0);
  expect(r.a.state.pos[0]).toBeLessThan(r.b.state.pos[0]);
  expect(r.maxVz).toBeLessThan(3);
  expect(Math.abs(r.p1)).toBeLessThan(Math.abs(r.p0) + 0.2 * 1380 * 60); // no energy injected along x
});
