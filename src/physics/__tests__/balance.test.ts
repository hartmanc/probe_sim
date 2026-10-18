// Handling balance, ABS and kickdown (balance pass, Oct 2026). Thresholds are chosen around what
// Coby reports for the real car: a stable, understeering FWD that rotates only when trail-braked.
// The "before" numbers in the comments are the car.json before this pass.
import { describe, expect, test } from 'vitest';
import { Vehicle } from '../index';
import { createFlatSurface } from '../devtrack';
import { DT, input, probeSpec } from './helpers';
import { liftOff, powerExit, sineSteer, stepSteer, stickFor, trailBrake } from './manoeuvres';
import { driveT2 } from './t2drive';

const V100 = 100 / 3.6;
const deg = (x: number | boolean) => x as number;

describe('balance manoeuvres at 100 km/h on the flat', () => {
  const spec = probeSpec();

  test('step steer to the limit (0.9 g): no spin, yaw rate settles, rear stays below its peak', () => {
    const r = stepSteer(spec, V100, stickFor(spec, V100, 0.9));
    console.log(`step to 0.9 g: overshoot ${(r.overshoot * 100).toFixed(0)} %, max beta ${r.maxBeta.toFixed(1)}°, rear slip ${deg(r.rearSlip).toFixed(1)}°`);
    expect(r.spun).toBe(false);
    expect(r.overshoot).toBeLessThan(0.35);     // before: 0.56
    expect(deg(r.rearSlip)).toBeLessThan(5.5);   // before: 9.2° (rear past its 7° peak)
  });

  test('full-stick step: front washes out, no spin', () => {
    const r = stepSteer(spec, V100, 1);
    expect(r.spun).toBe(false);
    expect(r.maxBeta).toBeLessThan(6);           // before: 7.6°
  });

  test('throttle lift mid-corner at 0.9 g: mild rotation only', () => {
    const r = liftOff(spec, V100, 0.9);
    console.log(`lift at ${deg(r.g0).toFixed(2)} g: rear slip ${deg(r.rearSlip0).toFixed(1)}° -> ${deg(r.rearSlip).toFixed(1)}°, max beta ${r.maxBeta.toFixed(1)}°`);
    expect(r.spun).toBe(false);
    expect(deg(r.rearSlip)).toBeLessThan(5);     // before: 3.0° -> 11.7°
    expect(r.maxBeta).toBeLessThan(4);           // before: 10.3°
  });

  test('sine steer 1 Hz, ±60 % stick: stable and returns straight', () => {
    const r = sineSteer(spec, V100, 0.6);
    expect(r.spun).toBe(false);
    expect(r.maxBeta).toBeLessThan(5);           // before: 6.5°
    expect(deg(r.finalBeta)).toBeLessThan(0.5);
  });

  test('full throttle out of a 2nd-gear corner: power understeer and inside-wheel spin, no oversteer', () => {
    const r = powerExit(spec, 50 / 3.6, 0.8);
    console.log(`power exit: path curvature x${deg(r.curvatureRatio).toFixed(2)}, inside slip ${deg(r.insideSlip).toFixed(2)}, max beta ${r.maxBeta.toFixed(1)}°`);
    expect(deg(r.curvatureRatio)).toBeLessThan(0.8);
    expect(deg(r.insideSlip)).toBeGreaterThan(0.3);
    expect(r.maxBeta).toBeLessThan(2);
  });

  test('trail-braked entry (40 % brake turning in to 0.8 g): the car rotates but does not spin', () => {
    const r = trailBrake(spec, V100, 0.8, 0.4);
    console.log(`trail brake: at 1 s front ${deg(r.front1).toFixed(1)}° rear ${deg(r.rear1).toFixed(1)}° beta ${deg(r.beta1).toFixed(1)}°, max beta ${r.maxBeta.toFixed(1)}°`);
    expect(deg(r.rear1)).toBeGreaterThan(deg(r.front1)); // rear slip exceeds front: rotation
    expect(deg(r.beta1)).toBeGreaterThan(3);
    expect(r.spun).toBe(false);
    expect(r.maxBeta).toBeLessThan(20);
  });
});

describe('ABS (crude early-90s 3-channel)', () => {
  function stop(abs: boolean, pedal: number) {
    const car = new Vehicle(probeSpec());
    car.abs = abs;
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0, V100);
    const inp = input({ brake: pedal });
    let t = 0, firstLock = -1, absAt = -1;
    while (car.state.speed > 0.1 && t < 10) {
      car.step(inp, flat, DT); t += DT;
      const s = car.state;
      if (firstLock < 0 && s.wheels.some((w, i) => i < 2 && 1 - (w.omega * 0.316) / s.speed > 0.35)) firstLock = t;
      if (absAt < 0 && s.absActive) absAt = t;
    }
    return { dist: car.state.pos[0], firstLock, absAt };
  }

  test('a stab of full brake locks the fronts for 0.4-0.5 s before the ABS wakes up', () => {
    const r = stop(true, 1);
    console.log(`ABS: lock at ${r.firstLock.toFixed(2)} s, ABS active at ${r.absAt.toFixed(2)} s (after ${(r.absAt - r.firstLock).toFixed(2)} s)`);
    expect(r.firstLock).toBeGreaterThan(0);
    expect(r.absAt - r.firstLock).toBeGreaterThanOrEqual(0.4);
    expect(r.absAt - r.firstLock).toBeLessThanOrEqual(0.5);
  });

  test('stopping distance from 100 km/h with ABS is close to threshold braking', () => {
    let best = Infinity;
    for (let p = 0.4; p <= 1.0001; p += 0.05) {
      const r = stop(false, p);
      const locked = r.firstLock > 0;
      if (!locked) best = Math.min(best, r.dist);
    }
    const abs = stop(true, 1).dist;
    console.log(`100-0 km/h: ABS full pedal ${abs.toFixed(1)} m, best no-lock pedal ${best.toFixed(1)} m, no ABS full pedal ${stop(false, 1).dist.toFixed(1)} m`);
    expect(abs).toBeLessThan(best * 1.06);
  });

  test('T2 at Laguna: driver A braking point at 70 % pedal, no front lock, on the line', () => {
    const r = driveT2(probeSpec(), 0.7, { brakeAt: 335 });
    expect(r.longestLock).toBeLessThan(0.05);
    expect(r.maxErrAfter).toBeLessThan(1.0);
    expect(r.spun).toBe(false);
  });

  test('T2 at Laguna: brake super late at full pedal and turn in, steerable after the first half second', () => {
    const withAbs = driveT2(probeSpec(), 1.0, { brakeAt: 370, holdTo: 68, abs: true });
    const noAbs = driveT2(probeSpec(), 1.0, { brakeAt: 370, holdTo: 68, abs: false });
    console.log(`T2 late braking: ABS max line error ${withAbs.maxErrAfter.toFixed(2)} m (longest lock ${withAbs.longestLock.toFixed(2)} s), no ABS ${noAbs.maxErrAfter.toFixed(2)} m (lock ${noAbs.longestLock.toFixed(2)} s)`);
    expect(withAbs.absSeen).toBe(true);
    expect(withAbs.longestLock).toBeLessThan(0.7);
    expect(withAbs.maxErrAfter).toBeLessThan(1.5);
    expect(withAbs.spun).toBe(false);
    expect(noAbs.maxErrAfter).toBeGreaterThan(3); // locked fronts plough straight on
  });
});

describe('autoShift kickdown', () => {
  test('full throttle at 125 km/h in 5th kicks down to 4th and does not hunt', () => {
    const car = new Vehicle(probeSpec(), { autoShift: true });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0, 125 / 3.6);
    car.setGear(5);
    const inp = input({ throttle: 1 });
    let shifts = 0, g = car.state.gear, sawFour = false;
    for (let i = 0; i < 10000; i++) {
      car.step(inp, flat, DT);
      if (car.state.gear !== g) { shifts++; g = car.state.gear; }
      if (g === 4) sawFour = true;
    }
    expect(sawFour).toBe(true);
    expect(shifts).toBeLessThanOrEqual(2); // down to 4th, at most one upshift back at the hold rpm
  });

  test('no kickdown at part throttle', () => {
    const car = new Vehicle(probeSpec(), { autoShift: true });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0, 125 / 3.6);
    car.setGear(5);
    for (let i = 0; i < 3000; i++) car.step(input({ throttle: 0.6 }), flat, DT);
    expect(car.state.gear).toBe(5);
  });
});

describe('slipUse (for audio)', async () => {
  const { tyrePeakSlip } = await import('../index');
  test('tyrePeakSlip and slipUse: ~0 rolling straight, ~1 at the limit, > 1 sliding', () => {
    const spec = probeSpec();
    const pk = tyrePeakSlip(spec);
    expect(pk.angleRad).toBeCloseTo((7 * Math.PI) / 180, 6);
    expect(pk.ratio).toBeCloseTo(0.12, 6);
    const car = new Vehicle(spec);
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0, V100);
    for (let i = 0; i < 500; i++) car.step(input({ throttle: 0.3 }), flat, DT);
    expect(Math.max(...car.state.wheels.map((w) => w.slipUse))).toBeLessThan(0.3);
    for (let i = 0; i < 1500; i++) car.step(input({ steer: 1, throttle: 0.3 }), flat, DT);
    const front = Math.max(car.state.wheels[0].slipUse, car.state.wheels[1].slipUse);
    expect(front).toBeGreaterThan(1); // full stick at 100 km/h: fronts past the peak
  });
});
