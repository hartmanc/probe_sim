import { describe, expect, test } from 'vitest';
import { Vehicle, type VehicleState } from '../index';
import { createFlatSurface } from '../devtrack';
import { bodyUp, DT, G, input, probeSpec, yawOf } from './helpers';

const MPH60 = 26.8224;

function allFinite(s: VehicleState): boolean {
  const nums = [...s.pos, ...s.quat, ...s.vel, ...s.angVel, s.rpm, s.speed, s.gLat, s.gLong];
  for (const w of s.wheels) nums.push(...w.pos, w.omega, w.load, w.compression, w.slipAngle, w.slipRatio);
  return nums.every(Number.isFinite);
}

describe('1. at rest on flat ground', () => {
  test('settles within 2 s with correct loads and no residual motion', () => {
    const spec = probeSpec();
    const car = new Vehicle(spec);
    const flat = createFlatSurface();
    car.reset([0, 0, 0.03], 0.7); // dropped from 3 cm
    const inp = input();
    for (let i = 0; i < 2000; i++) {
      car.step(inp, flat, DT);
      expect(allFinite(car.state)).toBe(true);
    }
    const s = car.state;
    const loads = s.wheels.map((w) => w.load);
    const sum = loads.reduce((a, b) => a + b, 0);
    const mg = spec.mass * G;
    expect(Math.abs(sum - mg) / mg).toBeLessThan(0.01);
    const front = (loads[0] + loads[1]) / sum;
    expect(front).toBeGreaterThan(0.60);
    expect(front).toBeLessThan(0.64);
    expect(Math.hypot(...s.vel)).toBeLessThan(0.01);
    expect(Math.hypot(...s.angVel)).toBeLessThan(0.01);
    // and it stays put for another 5 s
    const p0 = [...s.pos];
    for (let i = 0; i < 5000; i++) car.step(inp, flat, DT);
    expect(Math.hypot(s.pos[0] - p0[0], s.pos[1] - p0[1], s.pos[2] - p0[2])).toBeLessThan(0.002);
    expect(Math.abs(s.speed)).toBeLessThan(0.01);
    expect(car.nanResets).toBe(0);
  });
});

describe('2. full-throttle acceleration, autoShift', () => {
  test('0-60 mph, top speed, rev limit', () => {
    const spec = probeSpec();
    const car = new Vehicle(spec, { autoShift: true });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0);
    const inp = input({ throttle: 1 });
    let t60 = -1, maxRpm = 0, vmax = 0;
    const T = 150;
    for (let i = 0; i < T / DT; i++) {
      car.step(inp, flat, DT);
      const s = car.state;
      if (s.rpm > maxRpm) maxRpm = s.rpm;
      if (s.speed > vmax) vmax = s.speed;
      if (t60 < 0 && s.speed >= MPH60) t60 = (i + 1) * DT;
    }
    const s = car.state;
    console.log(`0-60 mph ${t60.toFixed(2)} s, top speed ${(vmax * 3.6).toFixed(1)} km/h in gear ${s.gear} at ${s.rpm.toFixed(0)} rpm, max rpm ${maxRpm.toFixed(0)}`);
    expect(t60).toBeGreaterThan(6.5);
    expect(t60).toBeLessThan(9.5);
    // Spec says 175–220 km/h; the specified CdA, torque curve and 0.90 driveline
    // efficiency put the drag-limited top speed at ~223 km/h (see README, Deviations).
    expect(vmax * 3.6).toBeGreaterThan(175);
    expect(vmax * 3.6).toBeLessThan(226);
    // drag limited: top gear, below the limiter, no longer accelerating
    expect(s.gear).toBe(spec.drivetrain.gearRatios.length);
    expect(s.rpm).toBeLessThan(spec.engine.revLimitRpm);
    expect(maxRpm).toBeLessThan(spec.engine.revLimitRpm + 100);
  });
});

describe('3. braking from 100 km/h', () => {
  test('stops in 38-55 m, straight and upright', () => {
    const car = new Vehicle(probeSpec(), { autoShift: true });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0.3, 100 / 3.6);
    const inp = input({ brake: 1 });
    const x0 = car.state.pos[0], y0 = car.state.pos[1];
    let t = 0, minUp = 1;
    while (car.state.speed > 0.05 && t < 10) {
      car.step(inp, flat, DT);
      t += DT;
      minUp = Math.min(minUp, bodyUp(car.state.quat)[2]);
    }
    const d = Math.hypot(car.state.pos[0] - x0, car.state.pos[1] - y0);
    const yaw = yawOf(car.state.quat);
    console.log(`100-0 km/h: ${d.toFixed(1)} m in ${t.toFixed(2)} s, yaw change ${((yaw - 0.3) * 180 / Math.PI).toFixed(2)} deg`);
    expect(d).toBeGreaterThan(38);
    expect(d).toBeLessThan(55);
    expect(Math.abs(yaw - 0.3)).toBeLessThan((3 * Math.PI) / 180);
    expect(minUp).toBeGreaterThan(Math.cos((8 * Math.PI) / 180));
  });

  test('a small steering offset under full braking does not spin the car', () => {
    const car = new Vehicle(probeSpec(), { autoShift: true });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0, 100 / 3.6);
    const inp = input({ brake: 1, steer: 0.02 });
    let t = 0;
    while (car.state.speed > 0.05 && t < 10) { car.step(inp, flat, DT); t += DT; }
    expect(Math.abs(yawOf(car.state.quat))).toBeLessThan((15 * Math.PI) / 180);
  });
});

describe('4. steady-state cornering', () => {
  test('peak lateral acceleration 0.9-1.2 g (logger: 0.8-1.1 g in most corners), mild understeer', () => {
    // constant road-wheel angle: disable speed shaping for this test
    const spec = probeSpec((j) => { j.steering.shapingSpeed = 1e6; j.steering.rate = 100; });
    const car = new Vehicle(spec, { autoShift: true });
    const flat = createFlatSurface();
    const v0 = 8;
    car.reset([0, 0, 0], 0, v0);
    // ≈ 8° road-wheel angle (R ≈ 19 m at low speed): with ~2.3°/g of understeer gradient (compliance
    // steer, balance pass) a smaller fixed angle runs out of steering before the tyres reach their limit
    const inp = input({ steer: 0.25 });
    const N = 1000; // 1 s moving average
    const buf = new Float64Array(N);
    let acc = 0, best = 0, bestFront = 0, bestRear = 0, integ = 0;
    const T = 80;
    for (let i = 0; i < T / DT; i++) {
      const t = i * DT;
      const vt = v0 + 0.2 * t; // slow speed ramp
      const e = vt - car.state.speed;
      integ += e * DT;
      inp.throttle = Math.min(1, Math.max(0, 0.3 * e + 0.05 * integ));
      car.step(inp, flat, DT);
      const s = car.state;
      const aLat = s.speed * s.angVel[2];
      acc += aLat - buf[i % N];
      buf[i % N] = aLat;
      if (i >= N && acc / N > best) {
        best = acc / N;
        bestFront = (Math.abs(s.wheels[0].slipAngle) + Math.abs(s.wheels[1].slipAngle)) / 2;
        bestRear = (Math.abs(s.wheels[2].slipAngle) + Math.abs(s.wheels[3].slipAngle)) / 2;
      }
    }
    console.log(`peak lateral ${(best / G).toFixed(3)} g; slip angles front ${(bestFront * 180 / Math.PI).toFixed(2)}°, rear ${(bestRear * 180 / Math.PI).toFixed(2)}°`);
    expect(best / G).toBeGreaterThan(0.9);
    expect(best / G).toBeLessThan(1.2);
    expect(bestFront).toBeGreaterThan(bestRear);
    expect(car.nanResets).toBe(0);
  });
});

describe('5. open differential on split mu', () => {
  test('low-mu front wheel spins up', () => {
    const car = new Vehicle(probeSpec(), { autoShift: false });
    const split = createFlatSurface({ muAt: (_x, y) => (y > 0 ? 0.3 : 1.0) });
    car.reset([0, 0, 0], 0, 8);
    car.setGear(2);
    const inp = input({ throttle: 1 });
    let maxRatio = 0;
    for (let i = 0; i < 1000; i++) {
      car.step(inp, split, DT);
      const [fl, fr] = car.state.wheels;
      maxRatio = Math.max(maxRatio, fl.omega / fr.omega);
    }
    console.log(`split-mu: max omega FL/FR = ${maxRatio.toFixed(2)}`);
    expect(car.state.gear).toBe(2);
    expect(maxRatio).toBeGreaterThan(1.5);
  });

  test('inside front wheel spins up on power in a tight corner', () => {
    const spec = probeSpec((j) => { j.steering.shapingSpeed = 1e6; j.steering.rate = 100; });
    const car = new Vehicle(spec, { autoShift: false });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0, 9);
    car.setGear(2);
    const inp = input({ steer: 0.5, throttle: 0.15 });
    for (let i = 0; i < 3000; i++) car.step(inp, flat, DT); // settle into the corner
    inp.throttle = 1;
    // Geometrically the inside wheel turns ~15 % slower than the outside one here;
    // with an open diff and the inside front unloaded it spins up past it.
    const [fl0, fr0] = car.state.wheels;
    expect(fl0.omega / fr0.omega).toBeLessThan(0.95);
    let maxRatio = 0, maxSlip = 0;
    for (let i = 0; i < 1500; i++) {
      car.step(inp, flat, DT);
      const [fl, fr] = car.state.wheels;
      maxRatio = Math.max(maxRatio, fl.omega / fr.omega); // left turn: FL is inside
      maxSlip = Math.max(maxSlip, fl.slipRatio);
    }
    console.log(`corner exit: max omega inside/outside = ${maxRatio.toFixed(2)}, inside slip ratio ${maxSlip.toFixed(2)}`);
    expect(maxRatio).toBeGreaterThan(1.5);
    expect(maxSlip).toBeGreaterThan(0.5);
  });
});

describe('misc', () => {
  test('gears: manual edges, reverse only when slow', () => {
    const car = new Vehicle(probeSpec(), { autoShift: false });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0);
    expect(car.state.gear).toBe(1);
    car.step(input({ shiftDown: true }), flat, DT);
    expect(car.state.gear).toBe(0);
    car.step(input({ shiftDown: true }), flat, DT);
    expect(car.state.gear).toBe(-1);
    for (let i = 0; i < 3000; i++) car.step(input({ throttle: 0.5 }), flat, DT);
    expect(car.state.speed).toBeLessThan(-1);
    car.step(input({ shiftUp: true }), flat, DT);
    car.step(input({ shiftUp: true }), flat, DT);
    expect(car.state.gear).toBe(1);
  });

  test('idle in gear does not creep or stall', () => {
    const car = new Vehicle(probeSpec(), { autoShift: true });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0);
    for (let i = 0; i < 3000; i++) car.step(input(), flat, DT);
    expect(Math.abs(car.state.speed)).toBeLessThan(0.01);
    expect(car.state.rpm).toBeGreaterThan(780);
    expect(car.state.rpm).toBeLessThan(920);
  });

  test('steering shaping: max angle falls with speed, rate limited', () => {
    const car = new Vehicle(probeSpec());
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0);
    car.step(input({ steer: 1 }), flat, DT);
    expect(car.state.wheels[0].steer).toBeLessThan(0.02); // rate limited
    for (let i = 0; i < 300; i++) car.step(input({ steer: 1 }), flat, DT);
    const centreAt0 = (car.state.wheels[0].steer + car.state.wheels[1].steer) / 2;
    expect(centreAt0 * 180 / Math.PI).toBeGreaterThan(28);
    const fast = new Vehicle(probeSpec());
    fast.reset([0, 0, 0], 0, 150 / 3.6);
    for (let i = 0; i < 1000; i++) fast.step(input({ steer: 1, throttle: 0.5 }), flat, DT);
    const st = fast.state.wheels;
    const deg = ((st[0].steer + st[1].steer) / 2) * 180 / Math.PI;
    expect(deg).toBeGreaterThan(1.5);
    expect(deg).toBeLessThan(8); // shapingSpeed 18 m/s gives about 5° at 150 km/h (was 13.4 m/s, 3°)
  });
});

describe('loadCarSpec', () => {
  test('rejects missing or invalid fields with a path, ignores _comments', async () => {
    const { loadCarSpec } = await import('../index');
    const { probeJson } = await import('./helpers');
    const j = probeJson();
    expect(() => loadCarSpec(j)).not.toThrow();
    const a = probeJson(); delete a.suspension.front.springRate;
    expect(() => loadCarSpec(a)).toThrow(/suspension\.front\.springRate/);
    const b = probeJson(); b.tyre.lateral.C = 0.9;
    expect(() => loadCarSpec(b)).toThrow(/tyre\.lateral\.C/);
    const c = probeJson(); c.engine.torqueCurve.rpm[3] = 1500;
    expect(() => loadCarSpec(c)).toThrow(/ascending/);
    expect(() => loadCarSpec(null)).toThrow();
  });

  test('derived gearing matches the measured rpm per mph', () => {
    const spec = probeSpec();
    const wheelRpmPerMph = (0.44704 * 60) / (2 * Math.PI * spec.wheel.radius);
    const rpmPerMph = spec.drivetrain.gearRatios.map((g) => g * wheelRpmPerMph);
    expect(rpmPerMph[0]).toBeCloseTo(207, 0);
    expect(rpmPerMph[1]).toBeCloseTo(114.7, 0);
    expect(rpmPerMph[2]).toBeCloseTo(82, 1);
    expect(rpmPerMph[3]).toBeCloseTo(63, 1);
    expect(rpmPerMph[4]).toBeCloseTo(48.5, 1);
  });
});
