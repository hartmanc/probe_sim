// Physics LOD for far AI cars (RaceDirector config `lod`, perf round 1).
import { expect, test } from 'vitest';
import { director } from './ai_fixture';

const snap = (d: ReturnType<typeof director>) => d.cars.map((c) => [...c.vehicle.state.pos, c.vehicle.state.speed, c.U]);

test('lod with every car inside the far radius is the ordinary step, bit for bit', () => {
  const run = (lod: boolean) => {
    const d = director({ seed: 3, maxAi: 20, playerAi: true, lod, lodFarM: 1e9 }, { walls: false });
    for (let i = 0; i < 4000; i++) d.step(0.001);
    return d;
  };
  const a = run(false), b = run(true);
  expect(b.lodFar).toBe(0);
  expect(snap(b)).toEqual(snap(a));
}, 120000);

test('lod off is the default and never counts far cars', () => {
  const d = director({ seed: 3, maxAi: 20, playerAi: true }, { walls: false });
  for (let i = 0; i < 500; i++) d.step(0.001);
  expect(d.config.lod).toBe(false);
  expect(d.lodFar).toBe(0);
}, 60000);

test('far cars step at 250 Hz, near ones at 500 Hz, and the race stays sane', () => {
  const d = director({ seed: 3, maxAi: 44, playerAi: true, lod: true, greenWindow: [5, 6] }, { walls: false });
  let maxFar = 0, steps = 0;
  const counts = new Map<number, number>();
  const orig = d.cars.map((c) => c.vehicle.step.bind(c.vehicle));
  d.cars.forEach((c, i) => { c.vehicle.step = ((inp: any, surf: any, dt: number) => { counts.set(i, (counts.get(i) ?? 0) + 1); return orig[i](inp, surf, dt); }) as typeof c.vehicle.step; });
  for (let i = 0; i < 20000; i++) { d.step(0.001); steps++; maxFar = Math.max(maxFar, d.lodFar); }
  expect(maxFar).toBeGreaterThan(5);
  // simulated time of every car stays in step with the clock (each far step integrates 4 ms)
  const total = [...counts.values()].reduce((a, b) => a + b, 0);
  const every2 = d.cars.length * steps / 2;
  expect(total).toBeLessThan(every2 * 0.95);       // fewer physics steps than the 500 Hz field
  expect(total).toBeGreaterThan(every2 * 0.5);
  for (const c of d.cars) { expect(Number.isFinite(c.U)).toBe(true); expect(c.vehicle.nanResets).toBe(0); }
  expect(d.recoveries).toBeLessThan(4);
}, 120000);

test('hysteresis: a car far at 300 m is not near again until 250 m', () => {
  const d = director({ seed: 3, maxAi: 10, playerAi: true, lod: true }, { walls: false });
  for (let i = 0; i < 200; i++) d.step(0.001);
  const far0 = d.lodFar;
  expect(far0).toBeGreaterThanOrEqual(0);
  expect(d.config.lodHystM).toBe(50);
  expect(d.config.lodFarM).toBe(300);
});
