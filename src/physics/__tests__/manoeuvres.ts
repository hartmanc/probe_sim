// Scripted handling manoeuvres shared by balance.test.ts (and handy for tuning).
import { Vehicle, type CarSpec, type Surface } from '../index';
import { createFlatSurface } from '../devtrack';
import { DT, input, yawOf } from './helpers';

export interface Metrics {
  /** max |body slip angle| (deg) during the evaluation window */
  maxBeta: number;
  /** yaw-rate overshoot above the settled value, fraction */
  overshoot: number;
  spun: boolean;
  /** extra numbers per manoeuvre */
  [k: string]: number | boolean;
}

/** Body-frame velocity components and slip angle (deg, + = nose pointing left of travel... i.e. ISO beta). */
/** Max loaded rear-wheel slip angle, deg. */
export function rearSlip(car: Vehicle): number {
  let m = 0;
  for (const i of [2, 3]) { const w = car.state.wheels[i]; if (w.load > 800) m = Math.max(m, Math.abs(w.slipAngle)); }
  return (m * 180) / Math.PI;
}

export function bodyVel(car: Vehicle): { u: number; v: number; beta: number; r: number } {
  const s = car.state;
  const [x, y, z, w] = s.quat;
  // body x and y axes in world
  const ex = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)];
  const ey = [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)];
  const ez = [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)];
  const u = s.vel[0] * ex[0] + s.vel[1] * ex[1] + s.vel[2] * ex[2];
  const v = s.vel[0] * ey[0] + s.vel[1] * ey[1] + s.vel[2] * ey[2];
  const r = s.angVel[0] * ez[0] + s.angVel[1] * ez[1] + s.angVel[2] * ez[2];
  return { u, v, beta: (Math.atan2(v, Math.abs(u)) * 180) / Math.PI, r };
}

function mkCar(spec: CarSpec, v0: number): { car: Vehicle; surf: Surface } {
  const car = new Vehicle(spec, { autoShift: true });
  car.reset([0, 0, 0], 0, v0);
  return { car, surf: createFlatSurface() };
}

/** Throttle PI that holds a target speed. */
function speedHold(target: number) {
  let integ = 0;
  return (v: number) => {
    const e = target - v;
    integ = Math.max(-2, Math.min(5, integ + e * DT));
    return Math.max(0, Math.min(1, 0.25 * e + 0.08 * integ + 0.25));
  };
}

/** Road-wheel (centre) angle in degrees that `stick` gives at speed v. */
export function angleOf(spec: CarSpec, v: number, stick: number): number {
  const st = spec.steering;
  const vr = Math.abs(v) / st.shapingSpeed;
  return stick * Math.max(st.minAngleDeg, st.maxAngleDeg / (1 + vr * vr));
}

/** Stick that gives road-wheel (centre) angle `deg` at speed v through the car's input shaping. */
export function stickForAngle(spec: CarSpec, v: number, deg: number): number {
  const st = spec.steering;
  const vr = Math.abs(v) / st.shapingSpeed;
  const maxA = Math.max(st.minAngleDeg, st.maxAngleDeg / (1 + vr * vr));
  return Math.max(-1, Math.min(1, deg / maxA));
}

/** Steady circle at speed v with stick s (speed held), then returns the car ready for the event. */
function settleCorner(spec: CarSpec, v: number, stick: number, secs = 4) {
  const { car, surf } = mkCar(spec, v);
  const hold = speedHold(v);
  const inp = input();
  for (let i = 0; i < secs / DT; i++) {
    inp.steer = stick * Math.min(1, i * DT / 0.5);
    inp.throttle = hold(car.state.speed);
    car.step(inp, surf, DT);
  }
  return { car, surf, inp, hold };
}

/** Find the stick that gives `g` lateral at speed v in steady state (bisection on the flat). */
export function stickFor(spec: CarSpec, v: number, g: number): number {
  let lo = 0, hi = 1;
  for (let k = 0; k < 14; k++) {
    const m = 0.5 * (lo + hi);
    const { car } = settleCorner(spec, v, m, 3);
    const b = bodyVel(car);
    const a = (b.u * b.r) / 9.81;
    if (Math.abs(bodyVel(car).beta) > 20 || a > g) hi = m; else lo = m;
  }
  return 0.5 * (lo + hi);
}

/** Step steer from straight running to `stick` at speed v; yaw-rate overshoot and max beta over 4 s. */
export function stepSteer(spec: CarSpec, v: number, stick: number): Metrics {
  const { car, surf } = mkCar(spec, v);
  const hold = speedHold(v);
  const inp = input();
  for (let i = 0; i < 500; i++) { inp.throttle = hold(car.state.speed); car.step(inp, surf, DT); }
  let maxR = 0, maxBeta = 0, spun = false, aMax = 0, rear = 0;
  const rs: number[] = [];
  for (let i = 0; i < 4000; i++) {
    inp.steer = stick;
    inp.throttle = hold(car.state.speed);
    car.step(inp, surf, DT);
    const b = bodyVel(car);
    maxR = Math.max(maxR, Math.abs(b.r));
    maxBeta = Math.max(maxBeta, Math.abs(b.beta));
    aMax = Math.max(aMax, Math.abs(b.u * b.r) / 9.81);
    if (Math.abs(b.beta) > 25) spun = true;
    rear = Math.max(rear, rearSlip(car));
    rs.push(Math.abs(b.r));
  }
  const settled = rs.slice(-1000).reduce((a, x) => a + x, 0) / 1000;
  return { maxBeta, overshoot: settled > 1e-3 ? maxR / settled - 1 : 0, spun, rearSlip: rear, settledG: (settled * bodyVel(car).u) / 9.81 };
}

/** Steady corner at ~g lateral, then lift the throttle completely for 2.5 s with the stick held. */
export function liftOff(spec: CarSpec, v: number, g: number): Metrics {
  const stick = stickFor(spec, v, g);
  const { car, surf, inp } = settleCorner(spec, v, stick);
  const b0 = bodyVel(car);
  let maxBeta = 0, spun = false, maxR = 0, rear = 0;
  const rear0 = rearSlip(car);
  const ang = angleOf(spec, v, stick);
  for (let i = 0; i < 2500; i++) {
    inp.throttle = 0;
    inp.steer = stickForAngle(spec, car.state.speed, ang);
    car.step(inp, surf, DT);
    rear = Math.max(rear, rearSlip(car));
    const b = bodyVel(car);
    maxBeta = Math.max(maxBeta, Math.abs(b.beta));
    maxR = Math.max(maxR, Math.abs(b.r));
    if (Math.abs(b.beta) > 25) spun = true;
  }
  return { maxBeta, overshoot: maxR / Math.abs(b0.r) - 1, spun, beta0: Math.abs(b0.beta), g0: (b0.u * b0.r) / 9.81, stick, rearSlip0: rear0, rearSlip: rear };
}

/** Sine steer at f Hz, amplitude `amp` stick, 4 cycles, speed held. */
export function sineSteer(spec: CarSpec, v: number, amp: number, f = 1): Metrics {
  const { car, surf } = mkCar(spec, v);
  const hold = speedHold(v);
  const inp = input();
  let maxBeta = 0, spun = false, rear = 0;
  for (let i = 0; i < 4 / f / DT; i++) {
    inp.steer = amp * Math.sin(2 * Math.PI * f * i * DT);
    inp.throttle = hold(car.state.speed);
    car.step(inp, surf, DT);
    rear = Math.max(rear, rearSlip(car));
    const b = bodyVel(car);
    maxBeta = Math.max(maxBeta, Math.abs(b.beta));
    if (Math.abs(b.beta) > 25) spun = true;
  }
  // settle 3 s straight: must come back
  for (let i = 0; i < 3000; i++) { inp.steer = 0; inp.throttle = hold(car.state.speed); car.step(inp, surf, DT); }
  const b = bodyVel(car);
  return { maxBeta, overshoot: 0, spun, rearSlip: rear, finalBeta: Math.abs(b.beta), finalR: Math.abs(b.r) };
}

/** 2nd-gear corner at ~0.8 g, then full throttle with the stick held for 2 s. */
export function powerExit(spec: CarSpec, v: number, g: number): Metrics {
  const stick = stickFor(spec, v, g);
  const { car, surf, inp } = settleCorner(spec, v, stick);
  car.setGear(2);
  for (let i = 0; i < 300; i++) car.step(inp, surf, DT);
  const b0 = bodyVel(car);
  const k0 = b0.r / b0.u; // path curvature
  let maxBeta = 0, spun = false, maxInsideSlip = 0, minK = Infinity, rear = 0;
  const ang = angleOf(spec, v, stick);
  for (let i = 0; i < 2000; i++) {
    inp.throttle = 1;
    inp.steer = stickForAngle(spec, car.state.speed, ang);
    car.step(inp, surf, DT);
    const b = bodyVel(car);
    maxBeta = Math.max(maxBeta, Math.abs(b.beta));
    if (Math.abs(b.beta) > 25) spun = true;
    maxInsideSlip = Math.max(maxInsideSlip, car.state.wheels[stick > 0 ? 0 : 1].slipRatio);
    rear = Math.max(rear, rearSlip(car));
    if (i > 300) minK = Math.min(minK, b.r / b.u);
  }
  return { maxBeta, overshoot: 0, spun, curvatureRatio: minK / k0, insideSlip: maxInsideSlip, rearSlip: rear };
}

/** Straight at v, then brake `brk` while turning in with a stick ramp over 0.4 s to the stick that gives ~g steady. */
export function trailBrake(spec: CarSpec, v: number, g: number, brk: number): Metrics {
  const stick = stickFor(spec, v, g);
  const { car, surf } = mkCar(spec, v);
  const hold = speedHold(v);
  const inp = input();
  for (let i = 0; i < 500; i++) { inp.throttle = hold(car.state.speed); car.step(inp, surf, DT); }
  let maxBeta = 0, spun = false, maxRatio = 0, rear = 0, front1 = 0, rear1 = 0, beta1 = 0;
  let vHold: ((v: number) => number) | null = null;
  const yaw0 = yawOf(car.state.quat);
  const ang = angleOf(spec, v, stick);
  for (let i = 0; i < 2000; i++) {
    // brake while turning in for 1 s, then back to throttle like a driver (speed held at the new pace)
    if (i === 1000) vHold = speedHold(car.state.speed);
    inp.throttle = i < 1000 ? 0 : vHold!(car.state.speed);
    inp.brake = i < 1000 ? brk : 0;
    inp.steer = stickForAngle(spec, car.state.speed, ang * Math.min(1, i * DT / 0.4));
    car.step(inp, surf, DT);
    rear = Math.max(rear, rearSlip(car));
    const b = bodyVel(car);
    maxBeta = Math.max(maxBeta, Math.abs(b.beta));
    if (Math.abs(b.beta) > 25) spun = true;
    if (i === 999) {
      const w = car.state.wheels, d = 180 / Math.PI;
      front1 = ((Math.abs(w[0].slipAngle) + Math.abs(w[1].slipAngle)) / 2) * d;
      rear1 = ((Math.abs(w[2].slipAngle) + Math.abs(w[3].slipAngle)) / 2) * d;
      beta1 = Math.abs(b.beta);
    }
  }
  void maxRatio;
  return { maxBeta, overshoot: 0, spun, stick, rearSlip: rear, front1, rear1, beta1, yawChange: Math.abs(yawOf(car.state.quat) - yaw0) * 180 / Math.PI };
}
