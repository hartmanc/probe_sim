// Stand-in for src/physics with the same public API (CONTRACTS §4).
// A kinematic bicycle car with a simple engine/gearbox and a grip limit,
// plus a heightfield + track-profile surface. Good enough to drive around
// and exercise the app; not a vehicle model.
import type {
  DriverInput, Surface, SurfaceSample, TrackJson, TrackProjector, Vec3, VehicleLike, VehicleState, WheelState,
} from './physics-types';
import { halfWidths, pointAt, profileZ, tangentAt } from './trackmath';

export type { TrackJson } from './physics-types';

const G = 9.81;

export interface StubSpec {
  mass: number; wheelbase: number; halfTrack: number; tyreRadius: number;
  ratios: number[]; reverseRatio: number; finalDrive: number;
  idleRpm: number; redline: number; limiter: number; peakTorque: number; peakTorqueRpm: number;
  cdA: number; maxLock: number; steerRate: number; steerSpeedRef: number;
}

const DEFAULT_SPEC: StubSpec = {
  mass: 1380, wheelbase: 2.614, halfTrack: 0.757, tyreRadius: 0.316,
  ratios: [3.31, 1.96, 1.31, 1.03, 0.79], reverseRatio: 3.17, finalDrive: 4.39,
  idleRpm: 850, redline: 6500, limiter: 7000, peakTorque: 217, peakTorqueRpm: 4200,
  cdA: 0.68, maxLock: 0.58, steerRate: 1.6, steerSpeedRef: 22,
};

export function loadCarSpec(json: unknown): StubSpec {
  const spec = { ...DEFAULT_SPEC };
  if (json && typeof json === 'object') {
    const j = json as Record<string, unknown>;
    if (typeof j.mass === 'number') spec.mass = j.mass;
    if (typeof j.mass_kg === 'number') spec.mass = j.mass_kg;
  }
  return spec;
}

// ---------------------------------------------------------------- projector

export function createTrackProjector(track: TrackJson): TrackProjector {
  const n = track.n;
  const cx = new Float64Array(n), cy = new Float64Array(n);
  for (let i = 0; i < n; i++) { cx[i] = track.center[i][0]; cy[i] = track.center[i][1]; }
  let hint = 0;
  const d2 = (i: number, x: number, y: number) => (cx[i] - x) ** 2 + (cy[i] - y) ** 2;
  return {
    project(x: number, y: number) {
      let best = hint, bd = d2(hint, x, y);
      for (let k = -60; k <= 60; k++) {
        const i = (hint + k + n) % n;
        const d = d2(i, x, y);
        if (d < bd) { bd = d; best = i; }
      }
      if (bd > 40 * 40) {
        for (let i = 0; i < n; i++) { const d = d2(i, x, y); if (d < bd) { bd = d; best = i; } }
      }
      hint = best;
      const [tx, ty] = tangentAt(track, best);
      const dx = x - cx[best], dy = y - cy[best];
      const along = dx * tx + dy * ty;
      const lateral = -dx * ty + dy * tx;
      let s = best * track.spacing_m + along;
      s = ((s % track.length_m) + track.length_m) % track.length_m;
      return { s, lateral, index: best };
    },
  };
}

// ---------------------------------------------------------------- surface

export function createTrackSurface(track: TrackJson, heightfield: Float32Array): Surface {
  const hf = track.heightfield;
  const proj = createTrackProjector(track);
  const ground = (x: number, y: number) => {
    let u = (x - hf.x0) / hf.dx, v = (y - hf.y0) / hf.dx;
    u = Math.min(Math.max(u, 0), hf.nx - 1.001); v = Math.min(Math.max(v, 0), hf.ny - 1.001);
    const j = Math.floor(u), i = Math.floor(v), fu = u - j, fv = v - i;
    const k = i * hf.nx + j;
    const a = heightfield[k], b = heightfield[k + 1], c = heightfield[k + hf.nx], d = heightfield[k + hf.nx + 1];
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv;
  };
  const out: SurfaceSample = { z: 0, nx: 0, ny: 0, nz: 1, onTrack: true, mu: 1 };
  return {
    sample(x: number, y: number): SurfaceSample {
      const p = proj.project(x, y);
      const [hl, hr] = halfWidths(track, p.index);
      const on = p.lateral <= hl + 0.3 && -p.lateral <= hr + 0.3;
      let z: number;
      if (on) {
        const frac = p.lateral >= 0 ? -p.lateral / Math.max(hl, 0.1) : -p.lateral / Math.max(hr, 0.1);
        z = profileZ(track, p.index, Math.max(-1, Math.min(1, frac)));
      } else {
        z = ground(x, y);
      }
      const e = 1.0;
      const gx = (ground(x + e, y) - ground(x - e, y)) / (2 * e);
      const gy = (ground(x, y + e) - ground(x, y - e)) / (2 * e);
      const l = Math.hypot(gx, gy, 1);
      out.z = z; out.nx = -gx / l; out.ny = -gy / l; out.nz = 1 / l;
      out.onTrack = on; out.paved = on; out.dirt = on ? 0 : 1; out.mu = on ? 1.0 : 0.72;
      return out;
    },
  };
}

export function lineToWorld(track: TrackJson, offsetAtS: (s: number) => number, s: number): { pos: Vec3; heading: number } {
  return pointAt(track, s, offsetAtS(s));
}

// ---------------------------------------------------------------- vehicle

function makeWheel(): WheelState {
  return { pos: [0, 0, 0], spinAngle: 0, steer: 0, compression: 0.06, omega: 0, slipRatio: 0, slipAngle: 0, load: 3400, onTrack: true, paved: true, mu: 1 };
}

export class Vehicle implements VehicleLike {
  readonly state: VehicleState;
  autoShift: boolean;
  private spec: StubSpec;
  private yaw = 0; private v = 0; private delta = 0;
  private pitch = 0; private roll = 0; private ax = 0; private ay = 0;
  private shiftTimer = 0;

  constructor(spec: unknown, opts?: { autoShift?: boolean }) {
    this.spec = (spec && typeof spec === 'object' && 'ratios' in spec) ? spec as StubSpec : loadCarSpec(spec);
    this.autoShift = opts?.autoShift ?? true;
    this.state = {
      pos: [0, 0, 0], quat: [0, 0, 0, 1], vel: [0, 0, 0], angVel: [0, 0, 0],
      wheels: [makeWheel(), makeWheel(), makeWheel(), makeWheel()],
      rpm: this.spec.idleRpm, gear: 1, speed: 0, gLat: 0, gLong: 0, throttleOut: 0,
    };
  }

  reset(pos: Vec3, headingRad: number, _speed = 0): void {
    this.yaw = headingRad; this.v = 0; this.delta = 0; this.pitch = 0; this.roll = 0; this.ax = 0; this.ay = 0;
    const s = this.state;
    s.pos = [pos[0], pos[1], pos[2]];
    s.gear = 1; s.rpm = this.spec.idleRpm; s.speed = 0;
    for (const w of s.wheels) { w.spinAngle = 0; w.omega = 0; w.slipRatio = 0; w.slipAngle = 0; }
    this.updatePose(null);
  }

  private torque(rpm: number): number {
    const sp = this.spec;
    const x = (rpm - sp.peakTorqueRpm) / 4500;
    return Math.max(60, sp.peakTorque * (1 - x * x));
  }

  private ratio(gear: number): number {
    if (gear === 0) return 0;
    if (gear < 0) return -this.spec.reverseRatio;
    return this.spec.ratios[gear - 1];
  }

  step(input: DriverInput, surface: Surface, dt: number): void {
    const sp = this.spec, st = this.state;
    // ---- gears
    this.shiftTimer = Math.max(0, this.shiftTimer - dt);
    if (input.shiftUp && st.gear < sp.ratios.length) { st.gear = st.gear === -1 ? 0 : st.gear + 1; this.shiftTimer = 0.12; }
    if (input.shiftDown) {
      if (st.gear > 1) st.gear--;
      else if (st.gear === 1) st.gear = 0;
      else if (st.gear === 0 && Math.abs(this.v) < 1) st.gear = -1;
      this.shiftTimer = 0.12;
    }
    if (this.autoShift && this.shiftTimer === 0) {
      if (st.gear === 0 && input.throttle > 0.1) st.gear = 1;
      else if (st.gear >= 1 && st.gear < sp.ratios.length && st.rpm > sp.redline) { st.gear++; this.shiftTimer = 0.15; }
      else if (st.gear > 1) {
        const lower = Math.abs(this.v) / sp.tyreRadius * this.ratio(st.gear - 1) * sp.finalDrive * 60 / (2 * Math.PI);
        if (lower < sp.redline - 1200 && st.rpm < 3000) { st.gear--; this.shiftTimer = 0.15; }
      }
    }

    // ---- surface under the car
    const cy = Math.cos(this.yaw), sy = Math.sin(this.yaw);
    const here = surface.sample(st.pos[0], st.pos[1]);
    const mu = here.mu;

    // ---- engine
    const ratio = this.ratio(st.gear) * sp.finalDrive;
    const wheelRpm = Math.abs(this.v) / sp.tyreRadius * 60 / (2 * Math.PI);
    let rpm = st.gear === 0 ? sp.idleRpm + input.throttle * 5500 : wheelRpm * Math.abs(ratio);
    if (st.gear !== 0 && rpm < 1100 + input.throttle * 2200 && Math.abs(st.gear) === 1) rpm = Math.max(rpm, 1100 + input.throttle * 2200); // clutch slip
    rpm = Math.max(sp.idleRpm, rpm);
    st.rpm += (rpm - st.rpm) * Math.min(1, dt * 30);
    let thr = input.throttle;
    if (st.rpm >= sp.limiter || this.shiftTimer > 0) thr = 0;
    st.throttleOut = thr;
    const drive = st.gear === 0 ? 0 : this.torque(st.rpm) * ratio * 0.88 / sp.tyreRadius * thr;

    // ---- longitudinal
    const m = sp.mass;
    const dir = Math.sign(this.v) || Math.sign(drive) || 1;
    const drag = 0.5 * 1.2 * sp.cdA * this.v * Math.abs(this.v);
    const roll = (Math.abs(this.v) > 0.05 ? 0.015 * m * G : 0) * dir * (here.onTrack ? 1 : 4);
    const brakeF = (input.brake * 1.05 + (input.handbrake ? 0.35 : 0)) * mu * m * G;
    const slope = -G * (here.nx * cy + here.ny * sy) * m;   // gravity along heading
    const driveLimit = 0.62 * mu * m * G * 1.05;            // FWD traction limit
    const driveUsed = Math.max(-driveLimit, Math.min(driveLimit, drive));
    const wheelspin = Math.abs(drive) > driveLimit ? Math.min(0.6, (Math.abs(drive) - driveLimit) / driveLimit) : 0;
    let a = (driveUsed - drag - roll + slope) / m;
    // brakes oppose motion and cannot reverse it
    const brakeA = brakeF / m;
    if (Math.abs(this.v) < brakeA * dt + 0.02 && Math.abs(driveUsed) < brakeF) { this.v = 0; a = 0; }
    else a -= Math.sign(this.v) * brakeA;
    if (this.v === 0 && Math.abs(driveUsed + slope) < Math.abs(roll) + 1) a = 0;

    // ---- steering (speed-dependent lock + rate limit)
    const vAbs = Math.abs(this.v);
    const lock = sp.maxLock / (1 + (vAbs / sp.steerSpeedRef) ** 2);
    const target = input.steer * lock;
    const maxD = sp.steerRate * dt;
    this.delta += Math.max(-maxD, Math.min(maxD, target - this.delta));

    // ---- lateral with grip limit
    let kappa = Math.tan(this.delta) / sp.wheelbase;
    const ayMax = mu * G * 0.98;
    const ayWanted = this.v * this.v * kappa;
    let understeer = 0;
    if (Math.abs(ayWanted) > ayMax && vAbs > 0.5) {
      const k2 = Math.sign(kappa) * ayMax / (this.v * this.v);
      understeer = Math.abs(Math.atan(kappa * sp.wheelbase) - Math.atan(k2 * sp.wheelbase));
      kappa = k2;
    }
    const ay = this.v * this.v * kappa;
    // friction circle: lateral use reduces available longitudinal
    const latUse = Math.min(1, Math.abs(ay) / ayMax);
    const axMax = mu * G * Math.sqrt(Math.max(0.05, 1 - latUse * latUse)) * 1.05;
    if (Math.abs(a) > axMax) a = Math.sign(a) * axMax;
    this.v += a * dt;
    if (st.gear === -1 && this.v > 0 && input.throttle > 0) { /* reversing from rolling forward */ }
    const yawRate = this.v * kappa;
    this.yaw += yawRate * dt;
    this.ax += (a - this.ax) * Math.min(1, dt * 8);
    this.ay += (ay - this.ay) * Math.min(1, dt * 8);

    st.pos[0] += this.v * Math.cos(this.yaw) * dt;
    st.pos[1] += this.v * Math.sin(this.yaw) * dt;

    // ---- wheels / slip info
    const lockSlip = input.brake > 0.9 && vAbs > 3 ? 0.2 : 0;
    const latSlip = latUse * 0.085 + understeer;
    const ws = st.wheels;
    for (let k = 0; k < 4; k++) {
      const w = ws[k];
      const front = k < 2;
      const spin = front ? wheelspin : 0;
      const slipRatio = front ? (spin > 0 ? spin * Math.sign(this.v || 1) : -lockSlip) : (input.handbrake && vAbs > 1 ? -1 : -lockSlip * 0.5);
      w.slipRatio = slipRatio;
      w.slipAngle = (front ? latSlip : latSlip * 0.8) * Math.sign(kappa);
      w.omega = this.v / sp.tyreRadius * (1 + slipRatio);
      w.spinAngle += w.omega * dt;
      w.steer = front ? this.delta : 0;
      w.load = m * G / 4;
    }
    this.updatePose(surface);
    st.speed = this.v;
    st.vel = [this.v * Math.cos(this.yaw), this.v * Math.sin(this.yaw), 0];
    st.angVel = [0, 0, yawRate];
    st.gLong = this.ax / G; st.gLat = this.ay / G;
  }

  private updatePose(surface: Surface | null): void {
    const sp = this.spec, st = this.state;
    const cy = Math.cos(this.yaw), sy = Math.sin(this.yaw);
    const L2 = sp.wheelbase / 2, W = sp.halfTrack;
    // ground heights at the four contact patches
    const pts: [number, number][] = [[L2, W], [L2, -W], [-L2, W], [-L2, -W]];
    const zs = [0, 0, 0, 0];
    const ws = st.wheels;
    if (surface) {
      for (let k = 0; k < 4; k++) {
        const [bx, by] = pts[k];
        const smp = surface.sample(st.pos[0] + bx * cy - by * sy, st.pos[1] + bx * sy + by * cy);
        zs[k] = smp.z; ws[k].onTrack = smp.onTrack; ws[k].paved = smp.paved ?? smp.onTrack; ws[k].mu = smp.mu;
      }
    } else {
      zs.fill(st.pos[2]);
    }
    const zc = (zs[0] + zs[1] + zs[2] + zs[3]) / 4;
    const terrainPitch = -Math.atan2((zs[0] + zs[1]) / 2 - (zs[2] + zs[3]) / 2, sp.wheelbase);
    const terrainRoll = Math.atan2((zs[0] + zs[2]) / 2 - (zs[1] + zs[3]) / 2, 2 * W);
    const dynPitch = Math.max(-0.05, Math.min(0.05, -this.ax * 0.0045));
    const dynRoll = Math.max(-0.07, Math.min(0.07, this.ay * 0.0065));
    this.pitch = terrainPitch + dynPitch;
    this.roll = terrainRoll + dynRoll;
    st.pos[2] = zc;
    // quat = Rz(yaw) * Ry(pitch) * Rx(roll)
    const hy = this.yaw / 2, hp = this.pitch / 2, hr = this.roll / 2;
    const cz = Math.cos(hy), szq = Math.sin(hy), cp = Math.cos(hp), spq = Math.sin(hp), cr = Math.cos(hr), sr = Math.sin(hr);
    const qw = cz * cp * cr + szq * spq * sr;
    const qx = cz * cp * sr - szq * spq * cr;
    const qy = cz * spq * cr + szq * cp * sr;
    const qz = szq * cp * cr - cz * spq * sr;
    st.quat = [qx, qy, qz, qw];
    // wheel hubs in world: rotate body-frame offsets by quat
    for (let k = 0; k < 4; k++) {
      const [bx, by] = pts[k];
      const p = rotate(qx, qy, qz, qw, bx, by, sp.tyreRadius);
      ws[k].pos = [st.pos[0] + p[0], st.pos[1] + p[1], st.pos[2] + p[2]];
      ws[k].compression = 0.06 + (zs[k] - zc) * 0.5;
    }
  }
}

function rotate(qx: number, qy: number, qz: number, qw: number, x: number, y: number, z: number): Vec3 {
  // v' = v + 2w(q×v) + 2 q×(q×v)
  const tx = 2 * (qy * z - qz * y), ty = 2 * (qz * x - qx * z), tz = 2 * (qx * y - qy * x);
  return [x + qw * tx + (qy * tz - qz * ty), y + qw * ty + (qz * tx - qx * tz), z + qw * tz + (qx * ty - qy * tx)];
}
