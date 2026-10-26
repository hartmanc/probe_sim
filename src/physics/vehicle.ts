// Vehicle dynamics core. See README.md in this directory for the model.
//
// Hot path rules: no allocations in step(), all state in typed arrays or
// number fields, Surface.sample() results are consumed immediately.

import { atan as datan, atan2 as datan2, cos as dcos, exp as dexp, hypot as dhypot, hypot3 as dhypot3, pow as dpow, sin as dsin, tan as dtan } from './dmath';   // bit-identical to V8 on every engine (docs/determinism.md)
import type { CarSpec } from './spec';
import { mfShape, solveMfB } from './tyre';
import type { DriverInput, Surface, VehicleState, WheelState, Vec3, ImpactInfo } from './types';
import { COLLISION_KINDS, KIND_PROPS, type CollisionWorld } from './collision';

/** Closing speed normal to a wall above which the car blasts into space. */
export const LAUNCH_SPEED = 25;
/** Tyre stacks launch at the same speed as hard walls (about 56 mph); below it they absorb. */
export const LAUNCH_SPEED_SOFT = 25;
const MAX_CONTACTS = 48;
const WALL_HALF_THICKNESS = 0.1;
const KIND_E = COLLISION_KINDS.map((k) => KIND_PROPS[k].restitution);
const KIND_MU = COLLISION_KINDS.map((k) => KIND_PROPS[k].friction);
const KIND_LAUNCH = COLLISION_KINDS.map((k) => KIND_PROPS[k].launches);
const KIND_SOFT = COLLISION_KINDS.map((k) => KIND_PROPS[k].soft);
const KIND_BOUNDARY = COLLISION_KINDS.indexOf('boundary');

const GRAV = 9.81;
const RPM = 60 / (2 * Math.PI); // rad/s → rpm
const PGS_ITERS = 8;
const MAX_ANG_VEL = 60; // rad/s, safety clamp on the body

function clamp(x: number, lo: number, hi: number): number {
  return x < lo ? lo : x > hi ? hi : x;
}
function fin(x: number | undefined, d: number): number {
  return typeof x === 'number' && Number.isFinite(x) ? x : d;
}

export interface VehicleOptions { autoShift?: boolean }

export class Vehicle {
  readonly state: VehicleState;
  autoShift: boolean;
  readonly spec: CarSpec;
  /** Count of steps where a non-finite state was detected (car is then reset in place). Should stay 0. */
  nanResets = 0;

  // ---------------------------------------------------------------- constants
  private readonly mass: number;
  private readonly Ixx: number;
  private readonly Iyy: number;
  private readonly Izz: number;
  private readonly cgX: number;
  private readonly cgZ: number;
  private readonly wheelbase: number;
  private readonly trackF: number;

  private readonly mountX = new Float64Array(4);
  private readonly mountY = new Float64Array(4);
  private readonly zDroop = new Float64Array(4);
  private readonly preload = new Float64Array(4);
  private readonly kSpring = new Float64Array(4);
  private readonly cBump = new Float64Array(4);
  private readonly cReb = new Float64Array(4);
  /** digressive damper: knee shaft speed (m/s; Infinity = linear) and high-speed slope ratio, per wheel */
  private readonly dKnee = new Float64Array(4);
  private readonly dHi = new Float64Array(4);
  private readonly kArb = new Float64Array(4);
  private readonly cStatic = new Float64Array(4);
  private readonly kTyreV: number;
  private readonly travel: number;
  private readonly bumpStart: number;
  private readonly kBump: number;

  private readonly radius: number;
  private readonly Iw: number;

  private readonly Bx: number; private readonly Cx: number; private readonly Ex: number;
  private readonly kpX: number; private readonly sigX: number; private readonly mu0x: number;
  private readonly By: number; private readonly Cy: number; private readonly Ey: number;
  private readonly apY: number; private readonly tanApY: number; private readonly sigY: number; private readonly mu0y: number;
  private readonly Fz0: number; private readonly lsExp: number;
  private readonly vFloor: number; private readonly vBlend: number; private readonly cLx: number; private readonly cLy: number;

  private readonly curveRpm: Float64Array;
  private readonly curveT: Float64Array;
  private readonly idleRpm: number;
  private readonly limitRpm: number;
  private readonly cutTime: number;
  private readonly Ie: number;
  private readonly tbIdle: number;
  private readonly tbLimit: number;
  private readonly idleBase: number;
  private readonly idleGain = 1 / 300;

  private readonly ratios: Float64Array;
  /** Driven-wheel coefficients (torque share per wheel, sum 1); FWD keeps the original code path. */
  private readonly fwd: boolean;
  private readonly dc = new Float64Array(4);
  private readonly nGears: number;
  private readonly reverseRatio: number;
  private readonly eff: number;
  private readonly shiftTime: number;
  private readonly clutchMax: number;
  private readonly clutchEngage: number;
  private readonly clutchFull: number;
  private readonly clutchBoost: number;
  private readonly engageTime: number;
  private readonly upRpm: number;
  private readonly downRpm: number;
  private readonly downMaxRpm: number;
  private readonly autoInterval: number;

  private readonly brakeMax: number;
  private readonly brakeBias: number;
  private readonly hbTorque: number;
  private readonly propKnee: number;
  private readonly propSlope: number;
  private readonly pedalExp: number;
  private readonly muRefV: number;
  private readonly muSlope: number;
  /** ABS fitted and switched on (settings toggle). Defaults to car.json brakes.abs.enabled. */
  abs: boolean;
  private readonly absCfg: CarSpec['brakes']['abs'];
  private readonly vxW = new Float64Array(4);       // contact-patch forward speed per wheel
  private readonly absLockT = new Float64Array(3);  // channels: FL, FR, rear axle
  private readonly absOn = new Uint8Array(3);
  private readonly absF = new Float64Array(3).fill(1);
  private readonly absHold = new Float64Array(3);
  private readonly absCalm = new Float64Array(3);
  private absAny = false;
  private readonly compl = new Float64Array(4);   // compliance steer, rad per N (+ = understeer)
  private readonly fyFilt = new Float64Array(4);  // low-passed tyre lateral force, N
  private readonly aeroK: number;
  private readonly crr0: number;
  private readonly crr2: number;
  // off pavement (car.json `surfaces`, NOTES-surface.md)
  private readonly offMu: number;      // NaN = use the surface's mu
  private readonly offKy: number;      // lateral stiffness factor on full dirt
  private readonly dirtCrr0: number;
  private readonly dirtCrr1: number;
  private readonly pavedW = [true, true, true, true];
  private readonly muW = new Float64Array(4).fill(1);

  private readonly maxSteer: number;
  private readonly minSteer: number;
  private readonly ackermann: number;
  private readonly shapeV: number;
  private readonly steerRate: number;
  private readonly rateV: number;

  private readonly hullPts = new Float64Array(24);
  private readonly hullMu: number;

  // ---------------------------------------------------------------- dynamic state
  private readonly p = new Float64Array(3); // CG, world
  private readonly v = new Float64Array(3); // CG velocity, world
  private readonly w = new Float64Array(3); // angular velocity, world
  private readonly q = new Float64Array(4); // body→world (x, y, z, w)
  private readonly R = new Float64Array(9); // row-major rotation body→world

  private readonly susC = new Float64Array(4);
  private readonly susPrev = new Float64Array(4);
  private readonly defU = new Float64Array(4);
  private readonly defW = new Float64Array(4);
  private readonly omega = new Float64Array(4);
  private readonly spin = new Float64Array(4);
  private readonly steerAng = new Float64Array(4);
  private readonly load = new Float64Array(4);
  private readonly slipK = new Float64Array(4);
  private readonly slipA = new Float64Array(4);
  private readonly slipUse = new Float64Array(4);
  private readonly tyreFx = new Float64Array(4);
  private readonly kWheel = new Float64Array(4);
  private readonly rrCap = new Float64Array(4);
  private readonly invIw = new Float64Array(4);
  private readonly brakeCap = new Float64Array(4);
  private readonly brakeLam = new Float64Array(4);
  private readonly gz = new Float64Array(4);   // ground z under each wheel
  private readonly gn = new Float64Array(12);  // ground normal under each wheel
  private readonly gx = new Float64Array(8);   // wheel sample x,y
  private readonly onTrk = [false, false, false, false];
  private readonly lastGood = new Float64Array(7);

  private omegaE = 0;
  private gear = 1;
  private shiftTimer = 0;
  private kickHold = false;
  private schedGear = 0;
  private engageTimer = 0;
  private shiftCooldown = 0;
  private limiterTimer = 0;
  private clutchLocked = false;
  private steerCmd = 0;
  private fLong = 0;
  private fLat = 0;
  private thrOut = 0;

  // collisions
  private cw: CollisionWorld | null = null;
  private simTime = 0;
  private launched = false;
  private launchedAt = NaN;
  private readonly impactInfo: ImpactInfo = { speedNormal: 0, speed: 0, kind: '', t: 0 };
  private hasImpact = false;
  private readonly colPts: Float64Array;      // body-frame sample points (x, y, z)
  private readonly colN: number;
  private readonly colW = new Float64Array(3 * 32); // world positions of the sample points
  private readonly ctP = new Float64Array(3 * MAX_CONTACTS);
  private readonly ctN = new Float64Array(2 * MAX_CONTACTS);
  private readonly ctD = new Float64Array(MAX_CONTACTS);
  private readonly ctK = new Uint8Array(MAX_CONTACTS);
  private readonly ctSoft = new Uint8Array(MAX_CONTACTS);
  private readonly ctJ = new Float64Array(MAX_CONTACTS);
  private readonly ctT = new Float64Array(MAX_CONTACTS);
  private readonly ctKn = new Float64Array(MAX_CONTACTS);
  private readonly ctVt = new Float64Array(MAX_CONTACTS);
  private readonly ctRn = new Float64Array(3 * MAX_CONTACTS); // I⁻¹(r×n), world
  private nCt = 0;
  private readonly hullFront: number; private readonly hullRear: number; private readonly hullHW: number;
  private readonly hullFloor: number; private readonly hullRoof: number; private readonly hullBumper: number;

  // tyre scratch outputs
  private tFx = 0; private tFy = 0; private tKw = 0;

  constructor(spec: CarSpec, opts?: VehicleOptions) {
    this.spec = spec;
    this.autoShift = opts?.autoShift ?? true;
    const s = spec;
    this.mass = s.mass;
    this.Ixx = s.inertia.roll; this.Iyy = s.inertia.pitch; this.Izz = s.inertia.yaw;
    const L = s.wheelbase;
    this.wheelbase = L;
    this.trackF = s.trackFront;
    // CG x from the static distribution: front share = (distance CG→rear axle) / L.
    this.cgX = L / 2 - (1 - s.frontWeightFraction) * L;
    this.cgZ = s.cgHeight;
    this.radius = s.wheel.radius;
    this.Iw = s.wheel.spinInertia;

    const su = s.suspension;
    this.kTyreV = su.tyreVerticalRate;
    this.travel = su.travel;
    this.bumpStart = su.travel - su.bumpStopRange;
    this.kBump = su.bumpStopForceAtFull / (su.bumpStopRange * su.bumpStopRange);
    const W = s.mass * GRAV;
    for (let i = 0; i < 4; i++) {
      const front = i < 2;
      const left = i % 2 === 0;
      const ax = front ? su.front : su.rear;
      const track = front ? s.trackFront : s.trackRear;
      this.mountX[i] = front ? L / 2 : -L / 2;
      this.mountY[i] = left ? track / 2 : -track / 2;
      const axleShare = front ? s.frontWeightFraction : 1 - s.frontWeightFraction;
      const Ws = (W * axleShare) / 2;
      this.kSpring[i] = ax.springRate;
      this.cBump[i] = ax.damperBump;
      this.cReb[i] = ax.damperRebound;
      this.dKnee[i] = ax.damperKnee; this.dHi[i] = ax.damperHighSpeedRatio;
      this.kArb[i] = ax.antiRollRate;
      this.cStatic[i] = ax.staticCompression;
      // d * d, not d ** 2: the same bits in V8 (math::pow special-cases y = 2), without relying on any engine's pow
      const dBs = ax.staticCompression - this.bumpStart;
      const bs = ax.staticCompression > this.bumpStart ? this.kBump * (dBs * dBs) : 0;
      this.preload[i] = Ws - ax.springRate * ax.staticCompression - bs;
      if (this.preload[i] < 0) throw new Error(`car spec: staticCompression too large for the spring rate (negative preload on wheel ${i})`);
      // Hub at full droop sits so that at static load the ground is at body z = 0.
      this.zDroop[i] = this.radius - ax.staticCompression - Ws / this.kTyreV;
    }

    const ty = s.tyre;
    this.Cx = ty.longitudinal.C; this.Ex = ty.longitudinal.E; this.kpX = ty.longitudinal.peakSlipRatio;
    this.Bx = solveMfB(this.Cx, this.Ex, this.kpX);
    this.sigX = ty.longitudinal.relaxationLength; this.mu0x = ty.longitudinal.mu0;
    this.Cy = ty.lateral.C; this.Ey = ty.lateral.E; this.apY = (ty.lateral.peakSlipAngleDeg * Math.PI) / 180;
    this.tanApY = dtan(this.apY);
    this.By = solveMfB(this.Cy, this.Ey, this.apY);
    this.sigY = ty.lateral.relaxationLength; this.mu0y = ty.lateral.mu0;
    this.Fz0 = ty.Fz0; this.lsExp = ty.loadSensitivity;
    this.vFloor = ty.lowSpeed.velocityFloor; this.vBlend = ty.lowSpeed.blendSpeed;
    this.cLx = ty.lowSpeed.dampingLong; this.cLy = ty.lowSpeed.dampingLat;

    const e = s.engine;
    this.curveRpm = Float64Array.from(e.torqueCurve.rpm);
    this.curveT = Float64Array.from(e.torqueCurve.torque);
    this.idleRpm = e.idleRpm; this.limitRpm = e.revLimitRpm; this.cutTime = e.limiterCutTime;
    this.Ie = e.inertia; this.tbIdle = e.brakingTorqueIdle; this.tbLimit = e.brakingTorqueLimit;
    const tFullIdle = this.fullTorque(this.idleRpm);
    this.idleBase = clamp(-this.tbIdle / Math.max(1, tFullIdle - this.tbIdle), 0, 1);

    const d = s.drivetrain;
    this.ratios = Float64Array.from(d.gearRatios);
    this.fwd = d.layout === 'fwd';
    {
      const f = d.layout === 'fwd' ? 1 : d.layout === 'rwd' ? 0 : d.awdFrontShare;
      this.dc[0] = this.dc[1] = 0.5 * f; this.dc[2] = this.dc[3] = 0.5 * (1 - f);
    }
    this.nGears = d.gearRatios.length;
    this.reverseRatio = d.reverseRatio;
    this.eff = d.efficiency;
    this.shiftTime = d.shiftTime;
    this.clutchMax = d.clutch.maxTorque; this.clutchEngage = d.clutch.engageRpm;
    this.clutchFull = Math.max(d.clutch.fullRpm, d.clutch.engageRpm + 50); this.clutchBoost = d.clutch.launchRpmBoost;
    this.engageTime = Math.max(1e-3, d.clutch.engageTime);
    this.upRpm = d.autoShift.upshiftRpm; this.downRpm = d.autoShift.downshiftRpm;
    this.downMaxRpm = d.autoShift.downshiftMaxRpm; this.autoInterval = d.autoShift.minInterval;

    this.brakeMax = s.brakes.maxTorque; this.brakeBias = s.brakes.frontBias; this.hbTorque = s.brakes.handbrakeTorque;
    this.propKnee = s.brakes.proportioningKnee; this.propSlope = s.brakes.proportioningSlope;
    this.pedalExp = s.brakes.pedalExponent;
    this.muRefV = s.tyre.speedSensitivity.refSpeed; this.muSlope = s.tyre.speedSensitivity.slope;
    this.absCfg = s.brakes.abs;
    this.abs = s.brakes.abs.enabled >= 0.5;
    for (let i = 0; i < 4; i++) {
      const c = ((i < 2 ? s.suspension.front : s.suspension.rear).complianceSteerDegPerKN * Math.PI) / 180 / 1000;
      // front: steer out of the turn (against the force); rear: steer with the force
      this.compl[i] = i < 2 ? -c : c;
    }
    this.aeroK = 0.5 * s.aero.airDensity * s.aero.cd * s.aero.frontalArea;
    this.crr0 = s.rollingResistance; this.crr2 = s.rollingResistanceSpeed;
    const sf = s.surfaces ?? { offPavementMu: NaN, offPavementLateralStiffness: 0.65, offPavementRollingResistance: 0.04, offPavementRollingResistanceSpeed: 0.0015 };
    this.offMu = sf.offPavementMu; this.offKy = sf.offPavementLateralStiffness;
    this.dirtCrr0 = sf.offPavementRollingResistance; this.dirtCrr1 = sf.offPavementRollingResistanceSpeed;

    const st = s.steering;
    this.maxSteer = (st.maxAngleDeg * Math.PI) / 180;
    this.minSteer = (st.minAngleDeg * Math.PI) / 180;
    this.ackermann = st.ackermann; this.shapeV = st.shapingSpeed;
    this.steerRate = st.rate; this.rateV = st.rateSpeed;

    const h = s.hull;
    let k = 0;
    for (const x of [h.front, h.rear]) for (const y of [h.halfWidth, -h.halfWidth]) for (const z of [h.floor, h.roof]) {
      this.hullPts[k++] = x; this.hullPts[k++] = y; this.hullPts[k++] = z;
    }
    this.hullMu = h.friction;
    this.hullFront = h.front; this.hullRear = h.rear; this.hullHW = h.halfWidth;
    this.hullFloor = h.floor; this.hullRoof = h.roof; this.hullBumper = h.bumper;
    {
      // wall sample points: bumper ring (corners, ends, sides every ≤ 1.2 m) and roof corners
      const pts: number[] = [];
      const xs: number[] = [];
      const nSide = Math.max(2, Math.ceil((h.front - h.rear) / 1.2));
      for (let i = 0; i <= nSide; i++) xs.push(h.rear + ((h.front - h.rear) * i) / nSide);
      for (const x of xs) { pts.push(x, h.halfWidth, h.bumper, x, -h.halfWidth, h.bumper); }
      pts.push(h.front, 0, h.bumper, h.rear, 0, h.bumper);
      for (const x of [h.roofFront, h.roofRear]) for (const y of [h.halfWidth - 0.15, -(h.halfWidth - 0.15)]) pts.push(x, y, h.roof);
      this.colPts = Float64Array.from(pts.slice(0, 3 * 32));
      this.colN = this.colPts.length / 3;
    }

    const mkWheel = (): WheelState => ({ pos: [0, 0, 0], spinAngle: 0, steer: 0, compression: 0, omega: 0, slipRatio: 0, slipAngle: 0, slipUse: 0, load: 0, onTrack: true, paved: true, mu: 1 });
    this.state = {
      pos: [0, 0, 0], quat: [0, 0, 0, 1], vel: [0, 0, 0], angVel: [0, 0, 0],
      wheels: [mkWheel(), mkWheel(), mkWheel(), mkWheel()],
      rpm: 0, gear: 1, speed: 0, gLat: 0, gLong: 0, throttleOut: 0,
      impact: null, launched: false, launchedAt: NaN, absActive: false,
    };
    this.reset([0, 0, 0], 0);
  }

  // ------------------------------------------------------------------ public

  /**
   * Place the car with its body origin at `pos` (ground level at static ride
   * height), heading `headingRad` (from +x toward +y). Optional `speed` (m/s,
   * forward) starts the car rolling in a sensible gear with the clutch closed.
   */
  /**
   * Put the car at `pos` (ground point under the body origin) heading `headingRad`, rolling at `speed`. With `up`
   * (the ground normal there) the body is pitched and rolled onto the slope instead of spawning level and dropping its
   * downhill wheels onto it (the Corkscrew grid slots rolled cars over, owner, 17 Oct 2026); without it, level.
   */
  reset(pos: [number, number, number], headingRad: number, speed = 0, up?: readonly number[]): void {
    if (up && Math.abs(up[2]) > 0.3) {
      let ux = up[0], uy = up[1], uz = up[2];
      const un = dhypot3(ux, uy, uz) || 1; ux /= un; uy /= un; uz /= un;
      let fx = dcos(headingRad), fy = dsin(headingRad), fz = 0;
      const d = fx * ux + fy * uy; fx -= d * ux; fy -= d * uy; fz -= d * uz;            // forward in the ground plane
      const fn = dhypot3(fx, fy, fz) || 1; fx /= fn; fy /= fn; fz /= fn;
      const lx = uy * fz - uz * fy, ly = uz * fx - ux * fz, lz = ux * fy - uy * fx;   // left = up × forward
      // body axes (x forward, y left, z up) as matrix columns → quaternion (x, y, z, w)
      const m00 = fx, m10 = fy, m20 = fz, m01 = lx, m11 = ly, m21 = lz, m02 = ux, m12 = uy, m22 = uz;
      const tr = m00 + m11 + m22;
      let qx: number, qy: number, qz: number, qw: number;
      if (tr > 0) { const s = Math.sqrt(tr + 1) * 2; qw = 0.25 * s; qx = (m21 - m12) / s; qy = (m02 - m20) / s; qz = (m10 - m01) / s; }
      else if (m00 > m11 && m00 > m22) { const s = Math.sqrt(1 + m00 - m11 - m22) * 2; qw = (m21 - m12) / s; qx = 0.25 * s; qy = (m01 + m10) / s; qz = (m02 + m20) / s; }
      else if (m11 > m22) { const s = Math.sqrt(1 + m11 - m00 - m22) * 2; qw = (m02 - m20) / s; qx = (m01 + m10) / s; qy = 0.25 * s; qz = (m12 + m21) / s; }
      else { const s = Math.sqrt(1 + m22 - m00 - m11) * 2; qw = (m10 - m01) / s; qx = (m02 + m20) / s; qy = (m12 + m21) / s; qz = 0.25 * s; }
      this.q[0] = qx; this.q[1] = qy; this.q[2] = qz; this.q[3] = qw;
    } else {
      const hz = 0.5 * headingRad;
      this.q[0] = 0; this.q[1] = 0; this.q[2] = dsin(hz); this.q[3] = dcos(hz);
    }
    this.updateR();
    const R = this.R;
    this.p[0] = pos[0] + R[0] * this.cgX + R[2] * this.cgZ;
    this.p[1] = pos[1] + R[3] * this.cgX + R[5] * this.cgZ;
    this.p[2] = pos[2] + R[6] * this.cgX + R[8] * this.cgZ;
    this.v[0] = R[0] * speed; this.v[1] = R[3] * speed; this.v[2] = R[6] * speed;
    this.w.fill(0);
    for (let i = 0; i < 4; i++) {
      this.susC[i] = this.cStatic[i];
      this.defU[i] = 0; this.defW[i] = 0;
      this.omega[i] = speed / this.radius;
      this.spin[i] = 0; this.steerAng[i] = 0;
      this.slipK[i] = 0; this.slipA[i] = 0; this.slipUse[i] = 0;
      this.load[i] = 0; this.tyreFx[i] = 0; this.kWheel[i] = 0; this.fyFilt[i] = 0;
    }
    this.steerCmd = 0;
    this.shiftTimer = 0; this.shiftCooldown = 0; this.limiterTimer = 0;
    this.fLong = 0; this.fLat = 0; this.thrOut = 0;
    this.launched = false; this.launchedAt = NaN;
    this.absOn.fill(0); this.absF.fill(1); this.absLockT.fill(0); this.absHold.fill(0); this.absCalm.fill(0); this.absAny = false;
    this.hasImpact = false;
    // every other per-run field, so a reset vehicle is bit-identical to a freshly constructed one
    this.kickHold = false; this.schedGear = 0; this.engageTimer = 0;
    this.simTime = 0; this.nCt = 0;
    this.impactInfo.speedNormal = 0;
    this.impactInfo.speed = 0; this.impactInfo.kind = ''; this.impactInfo.t = 0;
    this.tFx = 0; this.tFy = 0; this.tKw = 0;
    this.susPrev.fill(0); this.vxW.fill(0); this.rrCap.fill(0); this.invIw.fill(0);
    this.brakeCap.fill(0); this.brakeLam.fill(0); this.gz.fill(0); this.gn.fill(0); this.gx.fill(0);
    for (let i = 0; i < 4; i++) { this.onTrk[i] = false; this.pavedW[i] = true; this.muW[i] = 1; }
    this.ctP.fill(0); this.ctN.fill(0); this.ctD.fill(0); this.ctK.fill(0); this.ctSoft.fill(0); this.ctJ.fill(0);
    this.ctT.fill(0); this.ctKn.fill(0); this.ctVt.fill(0); this.ctRn.fill(0); this.colW.fill(0); this.tmp3.fill(0);
    // Gear: highest gear that keeps the engine above the downshift rpm.
    const wheelW = Math.abs(speed) / this.radius;
    let g = 1;
    if (speed > 1) {
      for (let k = this.nGears; k >= 1; k--) {
        if (wheelW * this.ratios[k - 1] * RPM >= this.downRpm) { g = k; break; }
      }
    }
    this.gear = g;
    const boxW = wheelW * this.ratios[g - 1];
    this.omegaE = Math.max(this.idleRpm / RPM, boxW);
    this.clutchLocked = boxW * RPM > this.clutchFull;
    this.saveGood();
    this.writeState();
  }

  /**
   * Scheduled gear for autoShift (a ghost's gear at the car's current s, see deriveGearSchedule /
   * scheduleTargetAt), or 0 for none. Call it every step (or whenever s changes); while it is
   * non-zero autoShift follows it, with rpm rules only as guards (upshift before the limiter,
   * downshift below 1800 rpm). With 0 the rpm/kickdown rules apply. Extra to §4.
   */
  setScheduledGear(g: number): void {
    this.schedGear = Number.isFinite(g) ? Math.max(0, Math.min(this.nGears, Math.round(g))) : 0;
  }

  /** Attach a static collision world (createCollisionWorld) or detach with null. Extra to §4. */
  setCollisionWorld(cw: CollisionWorld | null): void {
    this.cw = cw;
  }

  /** Simulated time since construction, s (used for impact / launch timestamps). */
  get time(): number { return this.simTime; }

  /** Force a gear (−1 reverse, 0 neutral, 1..N) without a shift delay. Extra to the contract; for tests and tools. */
  setGear(g: number): void {
    this.gear = clamp(Math.round(g), -1, this.nGears);
    this.shiftTimer = 0; this.engageTimer = 0;
    const boxW = this.fwd ? Math.abs(0.5 * this.ratioOf(this.gear) * (this.omega[0] + this.omega[1])) : Math.abs(this.ratioOf(this.gear) * this.dW());
    this.clutchLocked = this.gear !== 0 && boxW * RPM > this.clutchFull;
    if (this.clutchLocked) this.omegaE = boxW;
    this.writeState();
  }

  // ------------------------------------------------------------------ external contacts (car vs car)
  // Hooks for src/physics/cars.ts, called between steps. Extra to §4; they do not change step().

  /** Centre of mass, world (live view; do not write). */
  get cgWorld(): Readonly<Float64Array> { return this.p; }
  /** Velocity of the body point at world (x, y, z), written to out[0..2]. */
  pointVelocity(x: number, y: number, z: number, out: Float64Array): void {
    const p = this.p, v = this.v, w = this.w;
    const rx = x - p[0], ry = y - p[1], rz = z - p[2];
    out[0] = v[0] + w[1] * rz - w[2] * ry;
    out[1] = v[1] + w[2] * rx - w[0] * rz;
    out[2] = v[2] + w[0] * ry - w[1] * rx;
  }
  /** Inverse effective mass at world point (x, y, z) along the unit direction n: 1/m + (r×n)·I⁻¹(r×n). */
  invMassAt(x: number, y: number, z: number, nx: number, ny: number, nz: number): number {
    const p = this.p;
    const rx = x - p[0], ry = y - p[1], rz = z - p[2];
    const cx = ry * nz - rz * ny, cy = rz * nx - rx * nz, cz = rx * ny - ry * nx;
    this.updateR();
    this.invInertiaWorld(cx, cy, cz, this.tmp3, 0);
    return 1 / this.mass + cx * this.tmp3[0] + cy * this.tmp3[1] + cz * this.tmp3[2];
  }
  /** Apply the world impulse (jx, jy, jz) N·s at world point (x, y, z). */
  applyImpulseAt(x: number, y: number, z: number, jx: number, jy: number, jz: number): void {
    if (this.launched) return;
    const p = this.p, v = this.v, w = this.w;
    const invM = 1 / this.mass;
    v[0] += jx * invM; v[1] += jy * invM; v[2] += jz * invM;
    const rx = x - p[0], ry = y - p[1], rz = z - p[2];
    this.updateR();
    this.invInertiaWorld(ry * jz - rz * jy, rz * jx - rx * jz, rx * jy - ry * jx, this.tmp3, 0);
    w[0] += this.tmp3[0]; w[1] += this.tmp3[1]; w[2] += this.tmp3[2];
  }
  /** Move the body horizontally by (dx, dy) m (penetration push-out). */
  nudge(dx: number, dy: number): void {
    if (this.launched) return;
    this.p[0] += dx; this.p[1] += dy;
  }
  /** Record an impact from outside (kind e.g. 'car') in state.impact, with the same debounce as walls. */
  reportImpact(speedNormal: number, kind: string): void {
    const fresh = !this.hasImpact || this.simTime - this.impactInfo.t > 0.15 || speedNormal > this.impactInfo.speedNormal;
    if (!fresh) return;
    this.impactInfo.speedNormal = speedNormal;
    this.impactInfo.speed = Math.abs(this.state.speed);
    this.impactInfo.kind = kind;
    this.impactInfo.t = this.simTime;
    this.hasImpact = true;
    this.state.impact = this.impactInfo;
  }

  step(input: DriverInput, surface: Surface, dt: number): void {
    if (!(dt > 0)) return;
    this.simTime += dt;
    if (this.launched) { this.stepLaunched(dt); return; }
    const steerIn = clamp(fin(input.steer, 0), -1, 1);
    const thr = clamp(fin(input.throttle, 0), 0, 1);
    const brk = clamp(fin(input.brake, 0), 0, 1);
    const hb = !!input.handbrake;

    this.updateR();
    const R = this.R;
    const exx = R[0], exy = R[3], exz = R[6];
    const eyx = R[1], eyy = R[4], eyz = R[7];
    const ezx = R[2], ezy = R[5], ezz = R[8];
    const p = this.p, v = this.v, w = this.w;
    const vFwd = v[0] * exx + v[1] * exy + v[2] * exz;
    const absV = Math.abs(vFwd);

    // --------------------------------------------------------- gears
    this.updateGears(input, thr, dt, absV);
    const G = this.ratioOf(this.gear);

    // --------------------------------------------------------- steering shaping
    {
      const rate = this.steerRate / (1 + absV / this.rateV);
      const maxStep = rate * dt;
      const dCmd = steerIn - this.steerCmd;
      this.steerCmd += dCmd > maxStep ? maxStep : dCmd < -maxStep ? -maxStep : dCmd;
      const vr = absV / this.shapeV;
      const maxA = Math.max(this.minSteer, this.maxSteer / (1 + vr * vr));
      const dc = this.steerCmd * maxA;
      let dl = dc, dr = dc;
      if (Math.abs(dc) > 1e-6) {
        const Rt = this.wheelbase / dtan(Math.abs(dc));
        const half = this.trackF / 2;
        const inner = datan(this.wheelbase / Math.max(Rt - half, 1e-3));
        const outer = datan(this.wheelbase / (Rt + half));
        const a = Math.abs(dc);
        const inA = a + this.ackermann * (inner - a);
        const outA = a + this.ackermann * (outer - a);
        if (dc > 0) { dl = inA; dr = outA; } else { dl = -outA; dr = -inA; }
      }
      this.steerAng[0] = dl; this.steerAng[1] = dr; this.steerAng[2] = 0; this.steerAng[3] = 0;
    }

    // --------------------------------------------------------- forces
    const m = this.mass;
    let Fx = 0, Fy = 0, Fz = -m * GRAV;
    let Tx = 0, Ty = 0, Tz = 0;
    {
      const sp = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
      const k = -this.aeroK * sp;
      Fx += k * v[0]; Fy += k * v[1]; Fz += k * v[2];
    }
    const crr = this.crr0 + this.crr2 * vFwd * vFwd;
    const r = this.radius;

    this.susPrev.set(this.susC);
    for (let i = 0; i < 4; i++) {
      // hub-at-full-droop point relative to CG (body), then world
      const bx = this.mountX[i] - this.cgX, by = this.mountY[i], bz = this.zDroop[i] - this.cgZ;
      const rx = R[0] * bx + R[1] * by + R[2] * bz;
      const ry = R[3] * bx + R[4] * by + R[5] * bz;
      const rz = R[6] * bx + R[7] * by + R[8] * bz;
      const Px = p[0] + rx, Py = p[1] + ry, Pz = p[2] + rz;
      const smp = surface.sample(Px, Py);
      const zg = smp.z, nx = smp.nx, ny = smp.ny, nz = smp.nz;
      let mu = smp.mu;
      // off pavement (dirt weight 0 on pavement and for surfaces that do not publish it: pavement path untouched)
      const dirt = smp.dirt ?? 0;
      if (dirt > 0 && this.offMu === this.offMu) mu = (smp.muPaved ?? 1) * (1 - dirt * (1 - this.offMu));
      this.onTrk[i] = smp.onTrack;
      this.pavedW[i] = smp.paved ?? smp.onTrack;
      this.muW[i] = mu;
      this.gz[i] = zg; this.gn[3 * i] = nx; this.gn[3 * i + 1] = ny; this.gn[3 * i + 2] = nz;
      this.gx[2 * i] = Px; this.gx[2 * i + 1] = Py;

      const nDotEz = nx * ezx + ny * ezy + nz * ezz;
      let pen = -1, tdist = 0;
      if (nDotEz > 0.2) {
        tdist = (nz * (Pz - zg)) / nDotEz;
        pen = r - tdist;
      }

      // ---- suspension: massless wheel, spring+damper in series with the tyre spring (implicit in c)
      const c = this.susC[i];
      const j = i ^ 1;
      const cOther = this.susPrev[j];
      const inContact = pen > c;
      const Ft = inContact ? this.kTyreV * (pen - c) : 0;
      const dFt = inContact ? this.kTyreV : 0;
      let Fs = this.preload[i] + this.kSpring[i] * c + this.kArb[i] * (c - cOther);
      let dFs = this.kSpring[i] + this.kArb[i];
      if (c > this.bumpStart) {
        const e = c - this.bumpStart;
        Fs += this.kBump * e * e;
        dFs += 2 * this.kBump * e;
      }
      const f = Ft - Fs;
      const cd = f > 0 ? this.cBump[i] : this.cReb[i];
      let cNew = c + (dt * f) / (cd + dt * (dFt + dFs));
      {
        // digressive damper: past the knee the slope is dHi·cd. The implicit step solves D(v) = f - dt·k·v with
        // D(v) = cd·v below the knee and cd·vk + dHi·cd·(|v| - vk) above (same sign); below the knee this is exactly
        // the linear update above.
        const vk = this.dKnee[i];
        const vv = (cNew - c) / dt;
        if (vv > vk || vv < -vk) {
          const sg = vv > 0 ? 1 : -1, c2 = this.dHi[i] * cd;
          cNew = c + (dt * (f - sg * (cd - c2) * vk)) / (c2 + dt * (dFt + dFs));
        }
      }
      if (cNew < 0) cNew = 0;
      else if (cNew > this.travel + 0.03) cNew = this.travel + 0.03;
      this.susC[i] = cNew;
      const T = pen > cNew ? this.kTyreV * (pen - cNew) : 0;

      if (T <= 0 || nDotEz <= 0.2) {
        this.load[i] = 0;
        this.fyFilt[i] *= 0.98;
        this.tyreFx[i] = 0; this.kWheel[i] = 0; this.rrCap[i] = 0;
        // free tyre: deflections relax
        this.defU[i] *= 0.9; this.defW[i] *= 0.9;
        this.slipK[i] = 0; this.slipA[i] = 0; this.slipUse[i] = 0;
        continue;
      }
      const Fzl = T * nDotEz;
      this.load[i] = Fzl;

      // contact point (on the ground along -ez) relative to CG
      const cx = rx - ezx * tdist, cy = ry - ezy * tdist, cz = rz - ezz * tdist;
      const vcx = v[0] + w[1] * cz - w[2] * cy;
      const vcy = v[1] + w[2] * cx - w[0] * cz;
      const vcz = v[2] + w[0] * cy - w[1] * cx;

      // wheel heading projected into the ground plane
      const da = this.steerAng[i] + this.compl[i] * this.fyFilt[i];
      const cs = dcos(da), sn = dsin(da);
      let fx = exx * cs + eyx * sn, fy = exy * cs + eyy * sn, fz = exz * cs + eyz * sn;
      const dn = fx * nx + fy * ny + fz * nz;
      fx -= dn * nx; fy -= dn * ny; fz -= dn * nz;
      const fl = 1 / Math.sqrt(fx * fx + fy * fy + fz * fz);
      fx *= fl; fy *= fl; fz *= fl;
      // lateral = n × f
      const lx = ny * fz - nz * fy, ly = nz * fx - nx * fz, lz = nx * fy - ny * fx;
      const Vx = vcx * fx + vcy * fy + vcz * fz;
      const Vy = vcx * lx + vcy * ly + vcz * lz;

      this.vxW[i] = Vx;
      this.tyre(i, Fzl, mu, Vx, Vy, dt, dirt > 0 ? 1 - dirt * (1 - this.offKy) : 1);
      const tFx = this.tFx, tFy = this.tFy;
      this.fyFilt[i] += (tFy - this.fyFilt[i]) * (dt / (0.02 + dt));
      this.tyreFx[i] = tFx;
      this.kWheel[i] = this.tKw;
      // dirt: extra rolling resistance / sinkage drag ∝ load, growing with speed
      this.rrCap[i] = dirt > 0 ? (crr + dirt * (this.dirtCrr0 + this.dirtCrr1 * Math.abs(Vx))) * Fzl * r : crr * Fzl * r;

      const Fcx = Fzl * nx + tFx * fx + tFy * lx;
      const Fcy = Fzl * ny + tFx * fy + tFy * ly;
      const Fcz = Fzl * nz + tFx * fz + tFy * lz;
      Fx += Fcx; Fy += Fcy; Fz += Fcz;
      Tx += cy * Fcz - cz * Fcy;
      Ty += cz * Fcx - cx * Fcz;
      Tz += cx * Fcy - cy * Fcx;
    }

    // --------------------------------------------------------- hull contacts (rare)
    {
      let mx = 0, my = 0, mz = 0, mnx = 0, mny = 0, mnz = 0;
      for (let i = 0; i < 4; i++) {
        mx += this.gx[2 * i]; my += this.gx[2 * i + 1]; mz += this.gz[i];
        mnx += this.gn[3 * i]; mny += this.gn[3 * i + 1]; mnz += this.gn[3 * i + 2];
      }
      mx *= 0.25; my *= 0.25; mz *= 0.25;
      const nl = 1 / Math.sqrt(mnx * mnx + mny * mny + mnz * mnz);
      mnx *= nl; mny *= nl; mnz *= nl;
      const hp = this.hullPts;
      for (let k = 0; k < 8; k++) {
        const bx = hp[3 * k] - this.cgX, by = hp[3 * k + 1], bz = hp[3 * k + 2] - this.cgZ;
        const rx = R[0] * bx + R[1] * by + R[2] * bz;
        const ry = R[3] * bx + R[4] * by + R[5] * bz;
        const rz = R[6] * bx + R[7] * by + R[8] * bz;
        const Hx = p[0] + rx, Hy = p[1] + ry, Hz = p[2] + rz;
        // cheap pre-test against the plane through the wheel ground points
        if ((Hx - mx) * mnx + (Hy - my) * mny + (Hz - mz) * mnz > 0.12) continue;
        const smp = surface.sample(Hx, Hy);
        const pen = (smp.z - Hz) * smp.nz;
        if (pen <= 0) continue;
        const nx = smp.nx, ny = smp.ny, nz = smp.nz;
        const vhx = v[0] + w[1] * rz - w[2] * ry;
        const vhy = v[1] + w[2] * rx - w[0] * rz;
        const vhz = v[2] + w[0] * ry - w[1] * rx;
        const vn = vhx * nx + vhy * ny + vhz * nz;
        let Fn = 300000 * pen - 12000 * vn;
        if (Fn <= 0) continue;
        if (Fn > 200000) Fn = 200000;
        const vtx = vhx - vn * nx, vty = vhy - vn * ny, vtz = vhz - vn * nz;
        const vt = Math.sqrt(vtx * vtx + vty * vty + vtz * vtz);
        const ct = vt > 1e-6 ? Math.min(this.hullMu * Fn / vt, 8000) : 0;
        const Fhx = Fn * nx - ct * vtx, Fhy = Fn * ny - ct * vty, Fhz = Fn * nz - ct * vtz;
        Fx += Fhx; Fy += Fhy; Fz += Fhz;
        Tx += ry * Fhz - rz * Fhy;
        Ty += rz * Fhx - rx * Fhz;
        Tz += rx * Fhy - ry * Fhx;
      }
    }

    // --------------------------------------------------------- engine + drivetrain
    this.driveline(thr, brk, hb, G, dt);

    // --------------------------------------------------------- integrate body (semi-implicit Euler)
    const invM = 1 / m;
    v[0] += Fx * invM * dt; v[1] += Fy * invM * dt; v[2] += Fz * invM * dt;
    {
      // angular, in body frame
      const wbx = R[0] * w[0] + R[3] * w[1] + R[6] * w[2];
      const wby = R[1] * w[0] + R[4] * w[1] + R[7] * w[2];
      const wbz = R[2] * w[0] + R[5] * w[1] + R[8] * w[2];
      const tbx = R[0] * Tx + R[3] * Ty + R[6] * Tz;
      const tby = R[1] * Tx + R[4] * Ty + R[7] * Tz;
      const tbz = R[2] * Tx + R[5] * Ty + R[8] * Tz;
      const Ix = this.Ixx, Iy = this.Iyy, Iz = this.Izz;
      const hx = Ix * wbx, hy = Iy * wby, hz = Iz * wbz;
      let nwx = wbx + ((tbx - (wby * hz - wbz * hy)) / Ix) * dt;
      let nwy = wby + ((tby - (wbz * hx - wbx * hz)) / Iy) * dt;
      let nwz = wbz + ((tbz - (wbx * hy - wby * hx)) / Iz) * dt;
      const wm = Math.sqrt(nwx * nwx + nwy * nwy + nwz * nwz);
      if (wm > MAX_ANG_VEL) { const k = MAX_ANG_VEL / wm; nwx *= k; nwy *= k; nwz *= k; }
      w[0] = R[0] * nwx + R[1] * nwy + R[2] * nwz;
      w[1] = R[3] * nwx + R[4] * nwy + R[5] * nwz;
      w[2] = R[6] * nwx + R[7] * nwy + R[8] * nwz;
    }
    if (this.cw) {
      this.collide(dt);
      if (this.launched) { this.integratePose(dt); this.writeState(); return; }
    }
    this.integratePose(dt);

    // specific force (accelerometer) in body frame, low-passed
    {
      const ax = Fx * invM, ay = Fy * invM, az = Fz * invM + GRAV;
      const lon = ax * exx + ay * exy + az * exz;
      const lat = ax * eyx + ay * eyy + az * eyz;
      const a = dt / (0.05 + dt);
      this.fLong += a * (lon - this.fLong);
      this.fLat += a * (lat - this.fLat);
    }

    if (!this.finite()) {
      this.nanResets++;
      const g = this.lastGood;
      const yaw = 2 * datan2(g[5], g[6]);
      const t = this.simTime;
      this.reset([g[0], g[1], g[2]], yaw);
      this.simTime = t; // a NaN recovery keeps the clock
      return;
    }
    this.saveGood();
    this.writeState();
  }

  /** Semi-implicit position / orientation update from the (already updated) velocities. */
  private integratePose(dt: number): void {
    const p = this.p, v = this.v, w = this.w;
    p[0] += v[0] * dt; p[1] += v[1] * dt; p[2] += v[2] * dt;
    {
      const q = this.q;
      const qx = q[0], qy = q[1], qz = q[2], qw = q[3];
      const h = 0.5 * dt;
      const ax = w[0], ay = w[1], az = w[2];
      let nx = qx + h * (ax * qw + ay * qz - az * qy);
      let ny = qy + h * (-ax * qz + ay * qw + az * qx);
      let nz = qz + h * (ax * qy - ay * qx + az * qw);
      let nw = qw + h * (-ax * qx - ay * qy - az * qz);
      const l = 1 / Math.sqrt(nx * nx + ny * ny + nz * nz + nw * nw);
      q[0] = nx * l; q[1] = ny * l; q[2] = nz * l; q[3] = nw * l;
    }
  }

  // ------------------------------------------------------------------ collisions

  private addContact(px: number, py: number, pz: number, nx: number, ny: number, depth: number, kind: number, soft: boolean): void {
    let k = this.nCt;
    if (k >= MAX_CONTACTS) {
      // replace the shallowest contact if this one is deeper
      let mi = 0;
      for (let i = 1; i < MAX_CONTACTS; i++) if (this.ctD[i] < this.ctD[mi]) mi = i;
      if (this.ctD[mi] >= depth) return;
      k = mi;
    } else this.nCt++;
    this.ctP[3 * k] = px; this.ctP[3 * k + 1] = py; this.ctP[3 * k + 2] = pz;
    this.ctN[2 * k] = nx; this.ctN[2 * k + 1] = ny;
    this.ctD[k] = depth; this.ctK[k] = kind; this.ctSoft[k] = soft ? 1 : 0;
  }

  /** w = R · diag(1/I) · Rᵀ · a, written into out[o..o+2]. */
  private invInertiaWorld(ax: number, ay: number, az: number, out: Float64Array, o: number): void {
    const R = this.R;
    const bx = (R[0] * ax + R[3] * ay + R[6] * az) / this.Ixx;
    const by = (R[1] * ax + R[4] * ay + R[7] * az) / this.Iyy;
    const bz = (R[2] * ax + R[5] * ay + R[8] * az) / this.Izz;
    out[o] = R[0] * bx + R[1] * by + R[2] * bz;
    out[o + 1] = R[3] * bx + R[4] * by + R[5] * bz;
    out[o + 2] = R[6] * bx + R[7] * by + R[8] * bz;
  }

  /**
   * Car vs static world. Contacts: hull sample points vs wall segments (normal
   * toward the side the CG is on, so a point that crossed a thin wall is still
   * pushed back), wall corners / tree trunks vs the car's footprint box, and
   * the world boundary. Rigid contacts are solved with sequential impulses
   * (restitution, Coulomb friction, torque from the lever arm); fences and tyre
   * stacks are spring-dampers. Penetration is removed by a clamped push-out.
   */
  private collide(dt: number): void {
    const cw = this.cw!;
    const R = this.R, p = this.p, v = this.v, w = this.w;
    this.nCt = 0;
    // body origin
    const ox = p[0] - (R[0] * this.cgX + R[2] * this.cgZ);
    const oy = p[1] - (R[3] * this.cgX + R[5] * this.cgZ);
    const oz = p[2] - (R[6] * this.cgX + R[8] * this.cgZ);
    // world sample points
    const cp = this.colPts, cwp = this.colW, np = this.colN;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (let k = 0; k < np; k++) {
      const bx = cp[3 * k], by = cp[3 * k + 1], bz = cp[3 * k + 2];
      const x = ox + R[0] * bx + R[1] * by + R[2] * bz;
      const y = oy + R[3] * bx + R[4] * by + R[5] * bz;
      const z = oz + R[6] * bx + R[7] * by + R[8] * bz;
      cwp[3 * k] = x; cwp[3 * k + 1] = y; cwp[3 * k + 2] = z;
      if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
    }
    // footprint box (horizontal projection of the body x axis)
    let fx = R[0], fy = R[3];
    const fl = dhypot(fx, fy);
    const boxOk = fl > 0.3;
    if (boxOk) { fx /= fl; fy /= fl; } else { fx = 1; fy = 0; }
    const lx = -fy, ly = fx;
    const halfL = 0.5 * (this.hullFront - this.hullRear);
    const midX = 0.5 * (this.hullFront + this.hullRear);
    const bcx = ox + fx * midX, bcy = oy + fy * midX;
    const hw = this.hullHW;
    let zLo = Infinity, zHi = -Infinity;
    for (const bz of [this.hullFloor, this.hullRoof]) for (const bx of [this.hullFront, this.hullRear]) {
      const z = oz + R[6] * bx + R[8] * bz;
      if (z < zLo) zLo = z; if (z > zHi) zHi = z;
    }
    const zBump = oz + R[8] * this.hullBumper + R[6] * midX;

    const n = cw.query(minX - 1, minY - 1, maxX + 1, maxY + 1);
    const hits = cw.hits, nSeg = cw.nSeg;
    for (let h = 0; h < n; h++) {
      const it = hits[h];
      if (it < nSeg) {
        const ax = cw.sax[it], ay = cw.say[it], ex = cw.sbx[it] - ax, ey = cw.sby[it] - ay;
        const L2 = ex * ex + ey * ey;
        const Ls = Math.sqrt(L2);
        const nxs = -ey / Ls, nys = ex / Ls;
        const sC = (p[0] - ax) * nxs + (p[1] - ay) * nys;
        const sig = sC >= 0 ? 1 : -1;
        const zb = cw.szb[it], zt = cw.szt[it], zf = cw.szf[it], kind = cw.skind[it];
        for (let k = 0; k < np; k++) {
          const Px = cwp[3 * k], Py = cwp[3 * k + 1], Pz = cwp[3 * k + 2];
          if (Pz < zb || Pz > zf) continue;
          const t = ((Px - ax) * ex + (Py - ay) * ey) / L2;
          if (t < 0 || t > 1) continue;
          const depth = WALL_HALF_THICKNESS - sig * ((Px - ax) * nxs + (Py - ay) * nys);
          if (depth <= 0 || depth > 3) continue;
          this.addContact(Px, Py, Pz, sig * nxs, sig * nys, depth, kind, KIND_SOFT[kind] || Pz > zt);
        }
      } else if (boxOk) {
        const j = it - nSeg;
        const zb = cw.czb[j], zt = cw.czt[j], zf = cw.czf[j];
        if (zHi < zb || zLo > zf) continue;
        const r = cw.cr[j], kind = cw.ckind[j];
        const dx = cw.cx[j] - bcx, dy = cw.cy[j] - bcy;
        const u = dx * fx + dy * fy, s = dx * lx + dy * ly;
        const qu = u < -halfL ? -halfL : u > halfL ? halfL : u;
        const qs = s < -hw ? -hw : s > hw ? hw : s;
        const soft = KIND_SOFT[kind] || zBump > zt;
        if (qu !== u || qs !== s) {
          // centre outside the box
          const du = qu - u, ds = qs - s;
          const d = Math.sqrt(du * du + ds * ds);
          if (d >= r || d < 1e-9) continue;
          const nu = du / d, ns = ds / d;
          this.addContact(bcx + qu * fx + qs * lx, bcy + qu * fy + qs * ly, zBump,
            nu * fx + ns * lx, nu * fy + ns * ly, r - d, kind, soft);
        } else {
          // centre inside the box: push out through the nearest side
          const dF = halfL - u, dB = u + halfL, dL = hw - s, dR = s + hw;
          let m = dF, nu = -1, ns = 0;
          if (dB < m) { m = dB; nu = 1; ns = 0; }
          if (dL < m) { m = dL; nu = 0; ns = -1; }
          if (dR < m) { m = dR; nu = 0; ns = 1; }
          this.addContact(cw.cx[j], cw.cy[j], zBump, nu * fx + ns * lx, nu * fy + ns * ly, m + r, kind, soft);
        }
      }
    }
    // world boundary (invisible walls)
    const B = cw.bounds;
    for (let k = 0; k < np; k++) {
      const Px = cwp[3 * k], Py = cwp[3 * k + 1], Pz = cwp[3 * k + 2];
      if (Px < B.x0) this.addContact(Px, Py, Pz, 1, 0, B.x0 - Px, KIND_BOUNDARY, false);
      if (Px > B.x1) this.addContact(Px, Py, Pz, -1, 0, Px - B.x1, KIND_BOUNDARY, false);
      if (Py < B.y0) this.addContact(Px, Py, Pz, 0, 1, B.y0 - Py, KIND_BOUNDARY, false);
      if (Py > B.y1) this.addContact(Px, Py, Pz, 0, -1, Py - B.y1, KIND_BOUNDARY, false);
    }
    const nc = this.nCt;
    if (nc === 0) return;

    // ---- prepare: effective masses, closing speeds, impact / launch detection
    const invM = 1 / this.mass;
    const P = this.ctP, N = this.ctN, rn = this.ctRn;
    let maxClose = 0, maxK = -1;
    for (let k = 0; k < nc; k++) {
      const rx = P[3 * k] - p[0], ry = P[3 * k + 1] - p[1], rz = P[3 * k + 2] - p[2];
      const nx = N[2 * k], ny = N[2 * k + 1];
      // r × n with n = (nx, ny, 0)
      const cx = -rz * ny, cy = rz * nx, cz = rx * ny - ry * nx;
      this.invInertiaWorld(cx, cy, cz, rn, 3 * k);
      this.ctKn[k] = invM + cx * rn[3 * k] + cy * rn[3 * k + 1] + cz * rn[3 * k + 2];
      const vpx = v[0] + w[1] * rz - w[2] * ry, vpy = v[1] + w[2] * rx - w[0] * rz;
      const close = -(vpx * nx + vpy * ny);
      this.ctVt[k] = close;
      this.ctJ[k] = 0; this.ctT[k] = 0;
      if (close > maxClose) { maxClose = close; maxK = k; }
    }
    if (maxK >= 0 && maxClose > 0.5) {
      const kind = this.ctK[maxK];
      const fresh = !this.hasImpact || this.simTime - this.impactInfo.t > 0.15 || maxClose > this.impactInfo.speedNormal;
      if (fresh) {
        this.impactInfo.speedNormal = maxClose;
        this.impactInfo.speed = Math.abs(this.state.speed);
        this.impactInfo.kind = COLLISION_KINDS[kind];
        this.impactInfo.t = this.simTime;
        this.hasImpact = true;
      }
      if (KIND_LAUNCH[kind] && maxClose > (this.ctSoft[maxK] ? LAUNCH_SPEED_SOFT : LAUNCH_SPEED)) {
        this.launch(N[2 * maxK], N[2 * maxK + 1]);
        return;
      }
    }

    // ---- soft contacts (catch fence, tyre stacks): spring-damper impulses
    for (let k = 0; k < nc; k++) {
      if (!this.ctSoft[k]) continue;
      const nx = N[2 * k], ny = N[2 * k + 1];
      let F = 60000 * this.ctD[k] + 15000 * this.ctVt[k];
      if (F <= 0) continue;
      if (F > 150000) F = 150000;
      this.applyImpulse(k, nx, ny, 0, F * dt);
      // scrub along the barrier
      this.frictionImpulse(k, KIND_MU[this.ctK[k]] * F * dt);
    }

    // ---- rigid contacts: sequential impulses
    for (let it = 0; it < 8; it++) {
      for (let k = 0; k < nc; k++) {
        if (this.ctSoft[k]) continue;
        const rx = P[3 * k] - p[0], ry = P[3 * k + 1] - p[1], rz = P[3 * k + 2] - p[2];
        const nx = N[2 * k], ny = N[2 * k + 1];
        const vpx = v[0] + w[1] * rz - w[2] * ry, vpy = v[1] + w[2] * rx - w[0] * rz;
        const vn = vpx * nx + vpy * ny;
        const close0 = this.ctVt[k];
        const target = close0 > 1 ? KIND_E[this.ctK[k]] * close0 : 0;
        const old = this.ctJ[k];
        let j = old + (target - vn) / this.ctKn[k];
        if (j < 0) j = 0;
        const d = j - old;
        this.ctJ[k] = j;
        if (d !== 0) this.applyImpulse(k, nx, ny, 0, d);
        // friction, limited by mu × accumulated normal impulse
        const avail = KIND_MU[this.ctK[k]] * j - this.ctT[k];
        if (avail > 0) this.ctT[k] += this.frictionImpulse(k, avail);
      }
    }

    // ---- push-out (clamped so the solver never explodes)
    let sx = 0, sy = 0;
    for (let k = 0; k < nc; k++) {
      const excess = this.ctD[k] - 0.005;
      if (excess <= 0) continue;
      const rate = this.ctSoft[k] ? 0.05 : 0.3;
      sx += N[2 * k] * excess * rate;
      sy += N[2 * k + 1] * excess * rate;
    }
    const sl = dhypot(sx, sy);
    const maxPush = 0.01;
    if (sl > maxPush) { sx *= maxPush / sl; sy *= maxPush / sl; }
    p[0] += sx; p[1] += sy;
  }

  /** Apply impulse J·n (n horizontal) at contact k to the body. */
  private applyImpulse(k: number, nx: number, ny: number, nz: number, J: number): void {
    const v = this.v, w = this.w, p = this.p, P = this.ctP;
    const invM = 1 / this.mass;
    const ix = nx * J, iy = ny * J, iz = nz * J;
    v[0] += ix * invM; v[1] += iy * invM; v[2] += iz * invM;
    const rx = P[3 * k] - p[0], ry = P[3 * k + 1] - p[1], rz = P[3 * k + 2] - p[2];
    const tx = ry * iz - rz * iy, ty = rz * ix - rx * iz, tz = rx * iy - ry * ix;
    const tmp = this.tmp3;
    this.invInertiaWorld(tx, ty, tz, tmp, 0);
    w[0] += tmp[0]; w[1] += tmp[1]; w[2] += tmp[2];
  }

  private readonly tmp3 = new Float64Array(3);

  /** Friction impulse at contact k opposing the sliding velocity (3-D, minus the normal part), at most maxJ. Returns the impulse used. */
  private frictionImpulse(k: number, maxJ: number): number {
    const v = this.v, w = this.w, p = this.p, P = this.ctP, N = this.ctN;
    const rx = P[3 * k] - p[0], ry = P[3 * k + 1] - p[1], rz = P[3 * k + 2] - p[2];
    const nx = N[2 * k], ny = N[2 * k + 1];
    let vx = v[0] + w[1] * rz - w[2] * ry, vy = v[1] + w[2] * rx - w[0] * rz, vz = v[2] + w[0] * ry - w[1] * rx;
    const vn = vx * nx + vy * ny;
    vx -= vn * nx; vy -= vn * ny;
    const vt = Math.sqrt(vx * vx + vy * vy + vz * vz);
    if (vt < 1e-6) return 0;
    const tx = vx / vt, ty = vy / vt, tz = vz / vt;
    // effective mass along t
    const cx = ry * tz - rz * ty, cy = rz * tx - rx * tz, cz = rx * ty - ry * tx;
    const tmp = this.tmp3;
    this.invInertiaWorld(cx, cy, cz, tmp, 0);
    const kt = 1 / this.mass + cx * tmp[0] + cy * tmp[1] + cz * tmp[2];
    let J = vt / kt;
    if (J > maxJ) J = maxJ;
    this.applyImpulse(k, -tx, -ty, -tz, J);
    return J;
  }

  /** The same launch from outside (HotlapSim: the player far off the track for too long). (nx, ny) is the horizontal
   *  unit direction to push off along. Returns the sim time of the launch (state.launchedAt from the next step). */
  launchIntoSpace(nx: number, ny: number): number {
    if (!this.launched) this.launch(nx, ny);
    return this.launchedAt;
  }

  /** The easter egg: hard wall hit → straight up into space. (nx, ny) points away from the wall. */
  private launch(nx: number, ny: number): void {
    const v = this.v, w = this.w, R = this.R;
    v[0] = nx * 25; v[1] = ny * 25; v[2] = 70;
    // tumble: mostly pitch and roll in the body frame
    const bx = 2.6, by = -3.4, bz = 1.3;
    w[0] = R[0] * bx + R[1] * by + R[2] * bz;
    w[1] = R[3] * bx + R[4] * by + R[5] * bz;
    w[2] = R[6] * bx + R[7] * by + R[8] * bz;
    this.launched = true;
    this.launchedAt = this.simTime;
    this.thrOut = 0;
    for (let i = 0; i < 4; i++) { this.load[i] = 0; this.slipK[i] = 0; this.slipA[i] = 0; this.slipUse[i] = 0; }
  }

  /** After a launch: no gravity, a gentle upward push, constant tumble, engine and wheels wind down. */
  private stepLaunched(dt: number): void {
    this.updateR();
    this.v[2] += 3 * dt;
    const decay = dexp(-dt * 0.9);
    this.omegaE *= decay;
    for (let i = 0; i < 4; i++) { this.omega[i] *= decay; this.spin[i] += this.omega[i] * dt; }
    this.thrOut = 0;
    this.integratePose(dt);
    this.fLong *= decay; this.fLat *= decay;
    this.writeState();
  }

  // ------------------------------------------------------------------ tyre

  /**
   * Tyre forces for wheel i. Contact-patch deflection (relaxation) model:
   *   du/dt = Vsx − |Vx|·u/σx,  dv/dt = −Vy − |Vx|·v/σy
   * so slip = u/σ lags the kinematic slip with time constant σ/|Vx| and at
   * standstill the tread acts as a spring (stiffness = slip stiffness / σ).
   * The deflection is capped at the value that produces the peak force; past
   * the peak the force follows the kinematic slip (with a |Vx| floor), which
   * models sliding without unphysical wind-up. Pacejka MF per axis, combined
   * via normalized slip (so the force stays inside the friction ellipse),
   * load-sensitive mu, low-speed contact damping.
   * Writes tFx, tFy (N, along the wheel heading / its left) and tKw (wheel
   * spin damping estimate dτ/dω for the linearly implicit wheel update).
   */
  private tyre(i: number, Fz: number, mu: number, Vx: number, Vy: number, dt: number, kLat: number): void {
    const r = this.radius;
    // kLat < 1 (off pavement): lower cornering stiffness, the lateral peak moves out to apY / kLat
    const apY = kLat === 1 ? this.apY : this.apY / kLat;
    const tanApY = kLat === 1 ? this.tanApY : dtan(apY);
    const absVx = Math.abs(Vx);
    const Vsx = this.omega[i] * r - Vx;
    const vden = absVx > this.vFloor ? absVx : this.vFloor;

    // longitudinal
    let u = (this.defU[i] + dt * Vsx) / (1 + (dt * absVx) / this.sigX);
    const uMax = this.sigX * this.kpX;
    const kss = Vsx / vden;
    let kappa: number, satX = false;
    if (u >= uMax) {
      u = uMax;
      if (kss > this.kpX) { kappa = kss; satX = true; } else kappa = this.kpX;
    } else if (u <= -uMax) {
      u = -uMax;
      if (kss < -this.kpX) { kappa = kss; satX = true; } else kappa = -this.kpX;
    } else kappa = u / this.sigX;
    this.defU[i] = u;

    // lateral
    let wv = (this.defW[i] - dt * Vy) / (1 + (dt * absVx) / this.sigY);
    const wMax = this.sigY * tanApY;
    const tss = -Vy / vden;
    let tanA: number, satY = false;
    if (wv >= wMax) {
      wv = wMax;
      if (tss > tanApY) { tanA = tss; satY = true; } else tanA = tanApY;
    } else if (wv <= -wMax) {
      wv = -wMax;
      if (tss < -tanApY) { tanA = tss; satY = true; } else tanA = -tanApY;
    } else tanA = wv / this.sigY;
    this.defW[i] = wv;
    const alpha = datan(tanA);
    this.slipK[i] = kappa;
    this.slipA[i] = -alpha; // ISO sign

    if (Fz < 1 || mu <= 0) { this.tFx = 0; this.tFy = 0; this.tKw = 0; this.slipUse[i] = 0; return; }

    let muV = 1;
    if (this.muSlope > 0 && absVx > this.muRefV) { muV = 1 - this.muSlope * (absVx - this.muRefV); if (muV < 0.6) muV = 0.6; }
    // dpow: the server's pow (glibc's, which V8 calls) in every engine (docs/determinism.md section 5)
    const lsf = dpow(Fz / this.Fz0, this.lsExp) * Fz * mu;
    const Dx = this.mu0x * lsf, Dy = this.mu0y * lsf * muV;
    const sx = kappa / this.kpX, sy = alpha / apY;
    const rho = Math.sqrt(sx * sx + sy * sy);
    this.slipUse[i] = rho;
    let fx: number, fy: number, secX: number;
    if (rho < 1e-9) {
      secX = this.Bx * this.Cx * Dx;
      fx = secX * kappa;
      fy = this.By * this.Cy * Dy * alpha * (this.apY / apY);
    } else {
      const F0x = Dx * mfShape(this.Bx, this.Cx, this.Ex, rho * this.kpX);
      const F0y = Dy * mfShape(this.By, this.Cy, this.Ey, rho * this.apY);
      fx = (sx / rho) * F0x;
      fy = (sy / rho) * F0y;
      secX = F0x / (rho * this.kpX);
    }

    let wl = 0;
    if (absVx < this.vBlend) {
      wl = 0.5 * (1 + dcos((Math.PI * absVx) / this.vBlend));
      if (!satX) fx += this.cLx * wl * Vsx;
      if (!satY) fy -= this.cLy * wl * Vy;
    }
    const ex = fx / Dx, ey = fy / Dy;
    const e2 = ex * ex + ey * ey;
    if (e2 > 1) { const k = 1 / Math.sqrt(e2); fx *= k; fy *= k; }
    this.tFx = fx; this.tFy = fy;
    if (secX < 0) secX = 0;
    this.tKw = satX
      ? (r * r * secX) / vden
      : (r * r * secX * dt) / (this.sigX + dt * absVx) + (satX ? 0 : r * r * this.cLx * wl);
  }

  // ------------------------------------------------------------------ driveline

  private driveline(thr: number, brk: number, hb: boolean, G: number, dt: number): void {
    const rpmE = this.omegaE * RPM;
    const boxW = this.fwd ? 0.5 * G * (this.omega[0] + this.omega[1]) : G * this.dW();

    // throttle after shift cut / blip and rev limiter
    let thrE = thr;
    if (this.shiftTimer > 0) {
      const target = Math.abs(boxW) * RPM;
      thrE = rpmE < target - 100 ? 1 : 0; // rev-match blip on downshifts, cut on upshifts
    }
    if (rpmE > this.limitRpm) this.limiterTimer = this.cutTime;
    if (this.limiterTimer > 0) { thrE = 0; this.limiterTimer -= dt; }
    this.thrOut = this.shiftTimer > 0 ? 0 : thrE;
    const thrIdle = clamp(this.idleBase + (this.idleRpm - rpmE) * this.idleGain, 0, 1);
    const thrEff = thrE > thrIdle ? thrE : thrIdle;
    let Te = thrEff * this.fullTorque(rpmE) + (1 - thrEff) * this.brakingTorque(rpmE);
    if (Te > 0) Te *= this.eff;
    this.omegaE += (dt * Te) / this.Ie;

    // wheels: explicit tyre torque with linearly-implicit tyre damping
    const r = this.radius;
    for (let i = 0; i < 4; i++) {
      const inv = 1 / (this.Iw + dt * this.kWheel[i]);
      this.invIw[i] = inv;
      this.omega[i] += dt * -r * this.tyreFx[i] * inv;
    }

    // clutch capacity (automatic clutch)
    let cap = 0;
    if (G !== 0 && this.shiftTimer <= 0) {
      if (this.clutchLocked && rpmE >= this.clutchFull) cap = this.clutchMax;
      else {
        this.clutchLocked = false;
        const hi = this.clutchFull + thr * this.clutchBoost;
        const x = clamp((rpmE - this.clutchEngage) / (hi - this.clutchEngage), 0, 1);
        cap = this.clutchMax * x * x;
        if (this.engageTimer > 0) {
          // progressive re-engagement after a shift
          const ramp = 1 - this.engageTimer / this.engageTime;
          const lim = this.clutchMax * ramp * ramp;
          if (lim < cap) cap = lim;
        }
      }
      if (this.engageTimer > 0) this.engageTimer -= dt;
    } else this.clutchLocked = false;

    // brakes + rolling resistance as friction constraints on wheel spin
    const pl = this.pedalExp === 1 ? brk : dpow(brk, this.pedalExp); // line pressure
    const bf = (pl * this.brakeMax * this.brakeBias) / 2;
    const pr = pl <= this.propKnee ? pl : this.propKnee + this.propSlope * (pl - this.propKnee);
    const br = (pr * this.brakeMax * (1 - this.brakeBias)) / 2 + (hb ? this.hbTorque / 2 : 0);
    const hbT = hb ? this.hbTorque / 2 : 0;
    this.updateAbs(brk, dt);
    for (let i = 0; i < 4; i++) {
      const service = i < 2 ? bf : br - hbT;
      const f = this.absF[i < 2 ? i : 2];
      this.brakeCap[i] = (service * f + (i < 2 ? 0 : hbT) + this.rrCap[i]) * dt;
      this.brakeLam[i] = 0;
    }

    // projected Gauss-Seidel over clutch + brake constraints
    const half = 0.5 * G;
    const invIe = 1 / this.Ie;
    const capC = cap * dt;
    const dc = this.dc, fwd = this.fwd;
    const effC = capC > 0 ? 1 / (invIe + (fwd ? half * half * (this.invIw[0] + this.invIw[1])
      : G * G * (dc[0] * dc[0] * this.invIw[0] + dc[1] * dc[1] * this.invIw[1] + dc[2] * dc[2] * this.invIw[2] + dc[3] * dc[3] * this.invIw[3]))) : 0;
    let lamC = 0;
    const om = this.omega, invI = this.invIw, bc = this.brakeCap, bl = this.brakeLam;
    for (let it = 0; it < PGS_ITERS; it++) {
      if (effC > 0) {
        const rel = fwd ? this.omegaE - half * (om[0] + om[1]) : this.omegaE - G * (dc[0] * om[0] + dc[1] * om[1] + dc[2] * om[2] + dc[3] * om[3]);
        const old = lamC;
        lamC = clamp(old - rel * effC, -capC, capC);
        const d = lamC - old;
        this.omegaE += d * invIe;
        if (fwd) {
          om[0] -= half * d * invI[0];
          om[1] -= half * d * invI[1];
        } else for (let w = 0; w < 4; w++) om[w] -= G * dc[w] * d * invI[w];
      }
      for (let k = 0; k < 4; k++) {
        const i = (it & 1) === 0 ? k : k ^ 1; // alternate L/R order for symmetry
        if (bc[i] <= 0) continue;
        const old = bl[i];
        const nl = clamp(old - om[i] / invI[i], -bc[i], bc[i]);
        bl[i] = nl;
        om[i] += (nl - old) * invI[i];
      }
    }
    if (capC > 0) {
      const slipping = Math.abs(lamC) >= capC * 0.999;
      this.clutchLocked = !slipping && this.omegaE * RPM >= this.clutchFull;
    }
    if (this.omegaE < 0) this.omegaE = 0;
    for (let i = 0; i < 4; i++) this.spin[i] += om[i] * dt;
  }

  /** Braking slip (> 0 = wheel slower than the road) of wheel i, from the last step. */
  private brakeSlip(i: number): number {
    const vx = this.vxW[i];
    if (vx < 1) return 0;
    return 1 - (this.omega[i] * this.radius) / vx;
  }

  /**
   * Crude early-90s 3-channel ABS: fronts individually, rears together on the
   * worse wheel. A channel only wakes up after its wheel has been past
   * `lockSlip` for `wakeDelay` (the "shitty" half second of lock); once awake
   * it dumps to `releaseFactor` when slip passes `releaseSlip`, holds for
   * `holdTime`, then re-applies at `applyRate` (≈ 6–8 Hz cycles around 15–20 %
   * slip). It never asks for more than the pedal does, and shuts off below
   * `minSpeed`, under 10 % pedal, or once the wheel has run calmly at full
   * pedal torque for 0.3 s.
   */
  private updateAbs(brk: number, dt: number): void {
    const c = this.absCfg;
    let any = false;
    for (let ch = 0; ch < 3; ch++) {
      const slip = ch < 2 ? this.brakeSlip(ch) : Math.max(this.brakeSlip(2), this.brakeSlip(3));
      const vx = ch < 2 ? this.vxW[ch] : 0.5 * (this.vxW[2] + this.vxW[3]);
      if (!this.abs || brk < 0.1 || vx < c.minSpeed) {
        this.absOn[ch] = 0; this.absF[ch] = 1; this.absLockT[ch] = 0; this.absHold[ch] = 0; this.absCalm[ch] = 0;
        continue;
      }
      if (!this.absOn[ch]) {
        this.absF[ch] = 1;
        if (slip > c.lockSlip) this.absLockT[ch] += dt;
        else if (slip < 0.5 * c.lockSlip) this.absLockT[ch] = 0;
        if (this.absLockT[ch] >= c.wakeDelay) { this.absOn[ch] = 1; this.absCalm[ch] = 0; }
      }
      if (this.absOn[ch]) {
        any = true;
        if (this.absHold[ch] > 0) this.absHold[ch] -= dt;
        else if (slip > c.releaseSlip) { this.absF[ch] = c.releaseFactor; this.absHold[ch] = c.holdTime; }
        else this.absF[ch] = Math.min(1, this.absF[ch] + c.applyRate * dt);
        // wheel speeds recovered: full pedal torque without slipping for a while
        if (this.absF[ch] >= 1 && slip < 0.5 * c.releaseSlip) this.absCalm[ch] += dt; else this.absCalm[ch] = 0;
        if (this.absCalm[ch] > 0.3) { this.absOn[ch] = 0; this.absLockT[ch] = 0; }
      }
    }
    this.absAny = any;
  }

  private updateGears(input: DriverInput, thr: number, dt: number, absV: number): void {
    if (this.shiftTimer > 0) this.shiftTimer -= dt;
    if (this.shiftCooldown > 0) this.shiftCooldown -= dt;
    if (input.shiftUp) this.requestShift(this.gear + 1, absV);
    else if (input.shiftDown) this.requestShift(this.gear - 1, absV);
    else if (this.autoShift && this.gear >= 1 && this.shiftTimer <= 0 && this.shiftCooldown <= 0 && this.schedGear > 0) {
      // follow the ghost's gear schedule; rpm only as guards
      const rpmE = this.omegaE * RPM;
      const g = this.gear;
      const boxRpm = Math.abs(this.dW() * this.ratios[g - 1]) * RPM;
      const upRpm = g < this.nGears ? (boxRpm * this.ratios[g]) / this.ratios[g - 1] : 0;
      const downRpm = g > 1 ? (boxRpm * this.ratios[g - 2]) / this.ratios[g - 1] : Infinity;
      const MIN_RPM = 1800;
      // road-speed rpm: wheelspin over a crest (Corkscrew) must not trigger the limiter guard
      const roadRpm = (absV / this.radius) * this.ratios[g - 1] * RPM;
      if (g < this.nGears && rpmE >= this.limitRpm - 250 && roadRpm >= this.limitRpm - 600) this.requestShift(g + 1, absV);
      else if (g > 1 && boxRpm < MIN_RPM && downRpm < this.limitRpm - 300) this.requestShift(g - 1, absV);
      // a scheduled upshift also waits for the revs: a car slower than the ghost at that point
      // would otherwise bog down in the next gear
      else if (this.schedGear > g && upRpm >= MIN_RPM && rpmE >= this.spec.drivetrain.autoShift.scheduleMinUpshiftRpm) this.requestShift(g + 1, absV);
      else if (this.schedGear < g && downRpm < this.limitRpm - 300) {
        this.requestShift(g - 1, absV);
        // a scheduled multi-gear drop (5 -> 3 into a hairpin) goes through the gears back to back
        if (this.schedGear < this.gear) this.shiftCooldown = this.shiftTime + 0.05;
      }
      this.kickHold = false;
    }
    else if (this.autoShift && this.gear >= 1 && this.shiftTimer <= 0 && this.shiftCooldown <= 0) {
      const rpmE = this.omegaE * RPM;
      const g = this.gear;
      const boxRpm = Math.abs(this.dW() * this.ratios[g - 1]) * RPM;
      const ka = this.spec.drivetrain.autoShift;
      if (thr < 0.5) this.kickHold = false;
      const upAt = this.kickHold ? Math.max(this.upRpm, ka.kickdownHoldRpm) : this.upRpm;
      const lowerRpm = g > 1 ? (boxRpm * this.ratios[g - 2]) / this.ratios[g - 1] : Infinity;
      // no upshift while cornering hard (drivers hold the gear through a corner) unless near the limiter
      const cornering = Math.abs(this.fLat) / GRAV > 0.6 && rpmE < this.limitRpm - 400;
      if (g < this.nGears && rpmE >= upAt && boxRpm >= upAt * 0.9 && !cornering) {
        this.requestShift(g + 1, absV);
        this.kickHold = false;
      } else if (g > 1 && boxRpm < this.downRpm && lowerRpm < this.downMaxRpm) {
        this.requestShift(g - 1, absV);
      } else if (g > 1 && ka.kickdownRpm > 0 && thr >= ka.kickdownThrottle && rpmE < ka.kickdownRpm && this.clutchLocked
        && this.fLong / GRAV < ka.kickdownAccel && Math.abs(this.fLat) / GRAV < 0.5 && lowerRpm <= this.upRpm) {
        // (no kickdown while cornering hard: a mid-corner downshift upsets a FWD car at the limit)
        this.requestShift(g - 1, absV);
        this.kickHold = true;
      }
    }
  }

  private requestShift(target: number, absV: number): void {
    if (target > this.nGears || target < -1 || target === this.gear) return;
    if (target === -1 && absV > 1.5) return; // no reverse while rolling
    if (target >= 1 && target < this.gear) {
      // over-rev protection on downshifts
      const boxRpm = Math.abs(this.dW() * this.ratios[target - 1]) * RPM;
      if (boxRpm > this.limitRpm + 200) return;
    }
    this.gear = target;
    this.shiftTimer = target === 0 ? 0 : this.shiftTime;
    this.engageTimer = this.engageTime;
    this.shiftCooldown = this.shiftTime + this.autoInterval;
    this.clutchLocked = false;
  }

  /** Driven-wheel mean spin (rad/s): the front pair for FWD (original expression), else the torque-share weighted sum. */
  private dW(): number {
    const om = this.omega;
    return this.fwd ? 0.5 * (om[0] + om[1]) : this.dc[0] * om[0] + this.dc[1] * om[1] + this.dc[2] * om[2] + this.dc[3] * om[3];
  }

  private ratioOf(g: number): number {
    return g > 0 ? this.ratios[g - 1] : g < 0 ? -this.reverseRatio : 0;
  }

  /** Full-throttle crank torque at rpm (linear interpolation, linear extrapolation clamped ≥ 0). */
  fullTorque(rpm: number): number {
    const X = this.curveRpm, Y = this.curveT, n = X.length;
    let k = 0;
    if (rpm <= X[0]) k = 0;
    else if (rpm >= X[n - 1]) k = n - 2;
    else while (k < n - 2 && rpm > X[k + 1]) k++;
    const t = (rpm - X[k]) / (X[k + 1] - X[k]);
    const T = Y[k] + t * (Y[k + 1] - Y[k]);
    return T > 0 ? T : 0;
  }

  /** Closed-throttle torque (≤ 0). */
  brakingTorque(rpm: number): number {
    if (rpm <= this.idleRpm) return (this.tbIdle * Math.max(rpm, 0)) / this.idleRpm;
    const t = (rpm - this.idleRpm) / (this.limitRpm - this.idleRpm);
    return this.tbIdle + t * (this.tbLimit - this.tbIdle);
  }

  // ------------------------------------------------------------------ helpers

  private updateR(): void {
    const q = this.q, R = this.R;
    const x = q[0], y = q[1], z = q[2], w = q[3];
    R[0] = 1 - 2 * (y * y + z * z); R[1] = 2 * (x * y - z * w); R[2] = 2 * (x * z + y * w);
    R[3] = 2 * (x * y + z * w); R[4] = 1 - 2 * (x * x + z * z); R[5] = 2 * (y * z - x * w);
    R[6] = 2 * (x * z - y * w); R[7] = 2 * (y * z + x * w); R[8] = 1 - 2 * (x * x + y * y);
  }

  private finite(): boolean {
    const a = this.p, b = this.v, c = this.w, d = this.q;
    return Number.isFinite(a[0] + a[1] + a[2] + b[0] + b[1] + b[2] + c[0] + c[1] + c[2] + d[0] + d[1] + d[2] + d[3] +
      this.omegaE + this.omega[0] + this.omega[1] + this.omega[2] + this.omega[3]);
  }

  private saveGood(): void {
    const g = this.lastGood, R = this.R;
    this.updateR();
    g[0] = this.p[0] - (R[0] * this.cgX + R[2] * this.cgZ);
    g[1] = this.p[1] - (R[3] * this.cgX + R[5] * this.cgZ);
    g[2] = this.p[2] - (R[6] * this.cgX + R[8] * this.cgZ);
    // yaw only, as a half-angle quaternion pair
    const yaw = datan2(R[3], R[0]);
    g[5] = dsin(yaw / 2); g[6] = dcos(yaw / 2);
  }

  private writeState(): void {
    this.updateR();
    const R = this.R, s = this.state, p = this.p, v = this.v, w = this.w;
    const ox = -(R[0] * this.cgX + R[2] * this.cgZ);
    const oy = -(R[3] * this.cgX + R[5] * this.cgZ);
    const oz = -(R[6] * this.cgX + R[8] * this.cgZ);
    s.pos[0] = p[0] + ox; s.pos[1] = p[1] + oy; s.pos[2] = p[2] + oz;
    s.quat[0] = this.q[0]; s.quat[1] = this.q[1]; s.quat[2] = this.q[2]; s.quat[3] = this.q[3];
    s.vel[0] = v[0] + w[1] * oz - w[2] * oy;
    s.vel[1] = v[1] + w[2] * ox - w[0] * oz;
    s.vel[2] = v[2] + w[0] * oy - w[1] * ox;
    s.angVel[0] = w[0]; s.angVel[1] = w[1]; s.angVel[2] = w[2];
    for (let i = 0; i < 4; i++) {
      const ws = s.wheels[i];
      const c = this.susC[i];
      const bx = this.mountX[i] - this.cgX, by = this.mountY[i], bz = this.zDroop[i] + c - this.cgZ;
      ws.pos[0] = p[0] + R[0] * bx + R[1] * by + R[2] * bz;
      ws.pos[1] = p[1] + R[3] * bx + R[4] * by + R[5] * bz;
      ws.pos[2] = p[2] + R[6] * bx + R[7] * by + R[8] * bz;
      ws.spinAngle = this.spin[i];
      ws.steer = this.steerAng[i];
      ws.compression = c;
      ws.omega = this.omega[i];
      ws.slipRatio = this.slipK[i];
      ws.slipAngle = this.slipA[i];
      ws.slipUse = this.slipUse[i];
      ws.load = this.load[i];
      ws.onTrack = this.onTrk[i];
      ws.paved = this.pavedW[i];
      ws.mu = this.muW[i];
    }
    s.rpm = this.omegaE * RPM;
    s.gear = this.gear;
    s.speed = v[0] * R[0] + v[1] * R[3] + v[2] * R[6];
    s.gLong = this.fLong / GRAV;
    s.gLat = this.fLat / GRAV;
    s.throttleOut = this.thrOut;
    s.impact = this.hasImpact ? this.impactInfo : null;
    s.launched = this.launched;
    s.launchedAt = this.launchedAt;
    s.absActive = this.absAny;
  }
}

export type { Vec3 };
