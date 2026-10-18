import { expect, test } from 'vitest';
import { createTrackSurface, lineToWorld, Vehicle } from '../index';
import { createDevTrack } from '../devtrack';
import { DT, input, probeSpec } from './helpers';

test('7. performance: 100 000 steps under 2 s', () => {
  const { track, heightfield } = createDevTrack();
  const surf = createTrackSurface(track, heightfield);
  const car = new Vehicle(probeSpec(), { autoShift: true });
  const start = lineToWorld(track, () => 0, 0);
  car.reset(start.pos, start.heading);
  const inp = input({ throttle: 0.8 });
  // warm up the JIT
  for (let i = 0; i < 5000; i++) car.step(inp, surf, DT);
  car.reset(start.pos, start.heading);
  const t0 = performance.now();
  for (let i = 0; i < 100000; i++) {
    inp.steer = 0.3 * Math.sin(i * 1e-3);
    inp.throttle = i % 20000 < 15000 ? 0.8 : 0;
    inp.brake = i % 20000 < 15000 ? 0 : 0.6;
    car.step(inp, surf, DT);
  }
  const ms = performance.now() - t0;
  console.log(`100k steps: ${ms.toFixed(0)} ms (${(ms * 1000 / 100000).toFixed(2)} µs/step)`);
  expect(ms).toBeLessThan(2000);
  expect(car.nanResets).toBe(0);
});

test('7b. performance with the collision world: car scraping a wall', async () => {
  const { createCollisionWorld } = await import('../index');
  const { createDevScenery } = await import('../devtrack');
  const dev = createDevTrack();
  const sc = createDevScenery(dev.options);
  const surf = createTrackSurface(dev.track, dev.heightfield, { far: sc.far });
  const car = new Vehicle(probeSpec(), { autoShift: true });
  car.setCollisionWorld(createCollisionWorld(sc.scenery, dev.track));
  const inp = input({ throttle: 0.5, steer: -0.05 });
  const start = () => car.reset([-190, sc.armcoY + 1.2, 0], -0.05, 15);
  start();
  for (let i = 0; i < 5000; i++) car.step(inp, surf, DT);
  let ms = 0, contacts = 0;
  for (let rep = 0; rep < 10; rep++) {
    start();
    const t0 = performance.now();
    for (let i = 0; i < 10000; i++) car.step(inp, surf, DT);
    ms += performance.now() - t0;
    if (car.state.impact) contacts++;
  }
  console.log(`100k steps along a wall: ${ms.toFixed(0)} ms (${(ms / 100).toFixed(2)} µs/step)`);
  expect(contacts).toBeGreaterThan(0);
  expect(ms).toBeLessThan(2000);
  expect(car.nanResets).toBe(0);
});
