import { expect, test } from 'vitest';
import { createTrackSurface, lineToWorld, Vehicle } from '../index';
import { createDevTrack } from '../devtrack';
import { DT, input, probeSpec, rng } from './helpers';

const { track, heightfield } = createDevTrack();
const surf = createTrackSurface(track, heightfield);

for (const seed of [1, 2, 3]) {
  test(`8. robustness: 60 s of random gamepad input (seed ${seed})`, () => {
    const r = rng(seed);
    const car = new Vehicle(probeSpec(), { autoShift: seed !== 3 });
    const start = lineToWorld(track, () => 0, 0);
    car.reset(start.pos, start.heading);
    const inp = input();
    // Gamepad-like signals: held values that change at random times, with
    // occasional full-scale flicks, stomps, handbrake pulls and shift presses.
    let steerT = 0, thrT = 0, brkT = 0, hold = 0;
    let vmax = 0, maxGap = 0;
    for (let i = 0; i < 60 / DT; i++) {
      if (hold <= 0) {
        hold = 50 + Math.floor(r() * 2500);
        const mode = r();
        steerT = mode < 0.15 ? (r() < 0.5 ? -1 : 1) : (r() * 2 - 1) * r() * r();
        if (mode < 0.7) { thrT = r() < 0.7 ? 1 : r(); brkT = 0; }
        else if (mode < 0.85) { thrT = 0; brkT = r() < 0.5 ? 1 : r(); }
        else { thrT = r(); brkT = r() * 0.3; }
        inp.handbrake = r() < 0.03;
      }
      hold--;
      // analog stick / trigger travel with a little noise
      inp.steer = Math.max(-1, Math.min(1, inp.steer + (steerT - inp.steer) * 0.05 + (r() - 0.5) * 0.02));
      inp.throttle = Math.max(0, Math.min(1, inp.throttle + (thrT - inp.throttle) * 0.05));
      inp.brake = Math.max(0, Math.min(1, inp.brake + (brkT - inp.brake) * 0.05));
      inp.shiftUp = r() < 0.0005;
      inp.shiftDown = !inp.shiftUp && r() < 0.0005;
      car.step(inp, surf, DT);
      const s = car.state;
      const ok = [...s.pos, ...s.vel, ...s.quat, ...s.angVel, s.rpm].every(Number.isFinite);
      if (!ok) throw new Error(`non-finite state at t = ${(i * DT).toFixed(3)}`);
      const sp = Math.hypot(...s.vel);
      if (sp > vmax) vmax = sp;
      const gz = surf.sample(s.pos[0], s.pos[1]).z;
      maxGap = Math.max(maxGap, Math.abs(s.pos[2] - gz));
    }
    console.log(`seed ${seed}: max speed ${(vmax * 3.6).toFixed(0)} km/h, max |z − ground| ${maxGap.toFixed(2)} m`);
    expect(car.nanResets).toBe(0);
    expect(vmax * 3.6).toBeLessThan(400);
    expect(maxGap).toBeLessThan(5);
  });
}

test('8b. violent inputs at high speed: flicks, handbrake, off-track, and a drop', () => {
  const car = new Vehicle(probeSpec(), { autoShift: true });
  const start = lineToWorld(track, () => 0, 100);
  car.reset(start.pos, start.heading, 50);
  const inp = input({ throttle: 1 });
  let maxGap = 0, minUp = 1;
  for (let i = 0; i < 30 / DT; i++) {
    const t = i * DT;
    inp.steer = Math.sin(t * 2 * Math.PI * 0.8) > 0 ? 1 : -1;
    inp.handbrake = Math.floor(t) % 3 === 0;
    inp.brake = Math.floor(t) % 5 === 4 ? 1 : 0;
    if (i === 15000) car.reset([car.state.pos[0], car.state.pos[1], car.state.pos[2] + 3], 1.0, 20); // drop from 3 m
    car.step(inp, surf, DT);
    const s = car.state;
    if (![...s.pos, ...s.vel, ...s.quat, ...s.angVel, s.rpm].every(Number.isFinite)) throw new Error(`non-finite at ${t}`);
    maxGap = Math.max(maxGap, Math.abs(s.pos[2] - surf.sample(s.pos[0], s.pos[1]).z));
    const [x, y, , w] = s.quat;
    minUp = Math.min(minUp, 1 - 2 * (x * x + y * y));
  }
  console.log(`violent: max |z − ground| ${maxGap.toFixed(2)} m, min body-up z ${minUp.toFixed(2)}`);
  expect(car.nanResets).toBe(0);
  expect(maxGap).toBeLessThan(5);
});

test('8c. parked on the hill with the brake held does not creep', () => {
  const car = new Vehicle(probeSpec(), { autoShift: true });
  // back straight, on the slope of the hill (≈ 5 % grade)
  const { options: o } = createDevTrack();
  const Ls = (o.length - 2 * Math.PI * o.radius) / 2;
  const s0 = Ls + Math.PI * o.radius - o.hillSigma; // back straight, x = +σ: steepest point
  const p = lineToWorld(track, () => 0, s0);
  const ahead = lineToWorld(track, () => 0, s0 + 10);
  expect(ahead.pos[2] - p.pos[2]).toBeGreaterThan(0.4); // ~5 % uphill
  car.reset(p.pos, p.heading);
  const inp = input({ brake: 0.3 });
  for (let i = 0; i < 2000; i++) car.step(inp, surf, DT);
  const p0 = [...car.state.pos];
  for (let i = 0; i < 10000; i++) car.step(inp, surf, DT);
  const d = Math.hypot(car.state.pos[0] - p0[0], car.state.pos[1] - p0[1]);
  console.log(`parked on slope: moved ${(d * 1000).toFixed(2)} mm in 10 s`);
  expect(d).toBeLessThan(0.005);
});
