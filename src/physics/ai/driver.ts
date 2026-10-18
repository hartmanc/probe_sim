// AI driver: produces a DriverInput for one Vehicle each control tick.
//
// Steering: pure pursuit from the rear axle to a look-ahead point on a target lateral offset (the
// racing line plus a rate-limited "shift" for passing, defending, avoiding and rejoining), with
// yaw-rate feedback and an understeer feed-forward (as tools/calibrate/drive.ts). Speed: the car's
// own target profile (ghost shape x pace, capped by its grip; field.ts) with a feed-forward of the
// profile slope plus PI, mapped to throttle / brake through the car model, with a driver's pedal
// feel (back off on lock-up and wheelspin). Gears: the vehicle's auto-shift.
// Traffic (Traffic, sorted by s once per step) through a lane model (NOTES "Racecraft (the lane model) and mishaps"): every car
// occupies a lateral span in lane coordinates (offset from the racing line); only a car in my lane is followed; a
// clearly faster car plans a pass in a free lane (occupants projected forward, the road squeezing lanes together
// taken into account), holds it past one car or a train, and merges back when the racing lane is free; the car being
// passed holds its lane and makes room where the road pinches; light defending within 3 % only; rejoin after an off
// into a free lane; single file under yellow / formation.
// Mishaps: a seeded per-corner loss of control (run wide / spin). See NOTES "Racecraft (the lane model) and mishaps".

import type { DriverInput } from '../types';
import type { Vehicle } from '../vehicle';
import type { CarSpec } from '../spec';
import type { RaceLine } from './line';
import { accAt, coastDecel, type CarPerf } from './field';
import type { Traffic } from './traffic';
import { Rng } from './rng';

const G = 9.81;

export interface AiDriverParams {
  number: string;
  /** Pace scale fitted by calibrate_field (also baked into the CarSpec). The profile's ghost factor. */
  scale: number;
  /** Real median lap, s (pace hint for overtaking decisions). */
  targetLap: number;
  /** Robust lap sigma, s (per-lap pace noise). */
  sigma: number;
  aggression: 0 | 1 | 2;
  seed: number;
}

/** What race control tells this driver (set by the RaceDirector before each update). */
export interface DriverControl {
  /** Speed cap, m/s (Infinity = none). */
  speedCap: number;
  /** No overtaking (formation, yellow). */
  noPass: boolean;
  /** Minimum gap to the car ahead, m (formation: 15). 0 = time headway only. */
  minGap: number;
  /** Fraction of the target profile (cool-down lap after the flag: 0.6). */
  paceFactor: number;
  /** Per-lap pace noise on (race) or off (calibration). */
  noise: boolean;
  /**
   * Loss-of-control probability per corner passage before the corner and aggression factors (0 = off;
   * the director sets it during green for AI cars only). Ignored when `noise` is false.
   */
  mishapRate: number;
}

export type MishapKind = 'wide' | 'spin';

const HEADWAY = [0.75, 0.55, 0.38];        // s, following time gap by aggression
const STUCK_T = [3.0, 1.8, 1.0];
const PASS_ADV = [1.06, 1.04, 1.025];      // own target speed vs theirs needed to pass at once
const DEFEND = [0.5, 0.8, 1.1];            // m of lateral move to cover the inside (light, by aggression)
/** Target lap ratio below which a car is "clearly faster" (it goes for the pass; the car ahead does not defend). */
export const CLEARLY_FASTER = 0.97;
/** Loss-of-control factor by aggression tier (calm, normal, aggressive). */
export const MISHAP_AGGRESSION = [0.6, 1, 1.5];
/** Share of mishaps that are run-wide (the rest are spins). */
const MISHAP_WIDE = 0.7;
/** Run-wide slow phase: hold = HOLD0 + HOLDK x drawn loss (3-8 s), fitted with tools/race/selfplay.ts. */
const MISHAP_HOLD0 = -2.5, MISHAP_HOLDK = 1.4;
const CORNER_MARGIN = 0.95, BRAKE_MARGIN = 0.8;     // driverProfile: share of the lateral grip / braking used
const REAR_SLIP0 = 0.08, REAR_SLIPK = 6; // rad, 1/rad: ease the brake when the rear slides
// lane model (NOTES "Racecraft (the lane model) and mishaps")
const LANE_CLR = 0.3;      // m each side of a car's span in lane-occupancy checks (adjacent lanes leave >= 0.6 m)
const FOLLOW_CLR = 0.4;    // m edge to edge: a car ahead closer than this laterally is in my lane and followed
const ALONG_CLR = 0.45;    // m corridor margin beside a car alongside (inside the lane gap)
const GIVE_CLR = 0.2;      // m of that margin eaten before the car further back gives way
const PLAN_EVERY = 0.2;    // s between pass plans / lane checks
const PLAN_T = 10;         // s plan horizon for the occupancy projection
const PLAN_T_MAX = 40;     // s: a pass that would take longer than this is not started
const MIN_ADV = 0.2;       // m/s mean speed advantage in the pass lane needed to start
const PINCH_OK = 0.7;       // alongside = centres closer than 0.7 x (my front + its rear): where the lanes pinch, it makes room
const DROP_BACK = 30;      // m: abort a pass when I have fallen this far behind the car
const PASS_HEADWAY = 0.3;  // s: following the car I am passing (held in behind it where the lanes pinch), any aggression
const PASS_T_MAX = 30;     // s: give up a pass after this long
const PASS_SHIFT = 1.3;    // lane changes for a pass: x the shift rate
const PASS_EDGE = 0.5;     // m from the track edge (car side) a pass lane is clamped to
const SHIFT_RATE = 2.2;                    // m/s lateral change of the target offset
const KR = 0.25, LD0 = 3, LDK = 0.25;

/**
 * The driver's own copy of the car's speed profile (field.ts buildSpeedProfile = the car's full grip):
 * corner speeds at CORNER_MARGIN of the lateral grip and braking at BRAKE_MARGIN of the car's braking
 * (combined with cornering on the friction ellipse), so the car stays on its line at the limit.
 */
export function driverProfile(line: RaceLine, perf: CarPerf, prof: Float64Array): Float64Array {
  const N = line.N, curv = line.curv, grade = line.grade, ds = line.ds;
  const out = Float64Array.from(prof);
  const alat = CORNER_MARGIN * perf.alat;
  for (let i = 0; i < N; i++) out[i] = Math.min(out[i], Math.sqrt(alat * G / Math.max(1e-5, Math.abs(curv[i]))));
  for (let k = 2 * N; k > 0; k--) {
    const j = k % N, i = (j - 1 + N) % N, v = out[j];
    const u = Math.min(1, (v * v * Math.abs(curv[j])) / (perf.alat * G));
    const d = BRAKE_MARGIN * perf.abrake * G * Math.sqrt(Math.max(0, 1 - u * u)) + G * grade[i];
    const vp = Math.sqrt(Math.max(0, v * v + 2 * Math.max(0.5, d) * ds[i]));
    if (vp < out[i]) out[i] = vp;
  }
  return out;
}

export class AiDriver {
  readonly vehicle: Vehicle;
  readonly line: RaceLine;
  readonly perf: CarPerf;
  readonly params: AiDriverParams;
  readonly idx: number;
  readonly traffic: Traffic;
  /** Target speed profile per station (m/s), from buildSpeedProfile. */
  profile: Float64Array;
  readonly input: DriverInput = { steer: 0, throttle: 0, brake: 0, shiftUp: false, shiftDown: false };
  readonly ctl: DriverControl = { speedCap: Infinity, noPass: false, minGap: 0, paceFactor: 1, noise: true, mishapRate: 0 };
  readonly rng: Rng;

  // ---- state
  /** current station hint for the projector */
  hint = -1;
  /** lateral shift of the target offset from the racing line (m, + left), commanded and target */
  shift = 0;
  private shiftTarget = 0;
  private integ = 0;
  private brakeCap = 1; private thrCap = 1;
  /** per-lap pace factor (1 ± noise) */
  lapFactor = 1;
  private lastLapIdx = Number.NaN;
  // passing
  /** car being passed (-1 none) and the side of it I pass on (+1 left / -1 right) */
  passTarget = -1; passSide = 0; private passTimer = 0; private stuckTimer = 0;
  /** pass lane (lane coordinate, m from the racing line) and phase: 0 none, 1 passing, 2 waiting to merge back, 3 merging */
  passE = Number.NaN; passPhase = 0;
  private planTimer = 0;
  /** the last plan's estimated speed advantage over the car being passed, m/s (lane checks project me at it) */
  planAdv = 0;
  /** (tools) the car I followed on the last tick (-1 none) */
  leadIdx = -1;
  /** how the last pass attempt ended (tools): 'done' | 'dropped' | 'timeout' | 'stalled' | 'blocked' | 'off' | 'flag' | 'away' */
  passEnd = '';
  private passCool = 0;
  // defending: covering the inside of corner `defendCorner` (+1 left / -1 right; read by tools)
  defendSide = 0; private defendCorner = -1; private defendTimer = 0; private defendCool = 0;
  // loss of control (mishap): kind, phase, timers and draws; next corner whose braking point is ahead
  mishap: MishapKind | null = null; private mPhase = 0; private mT = 0; private mCorner = -1;
  private mOver = 1; private mOut = 0; private mHold = 0;
  private nextCorner = -1;
  /** mishaps this driver has had since the race (re)started; the director logs each new one */
  mishapCount = 0; lastMishapCorner = -1;
  // off track
  offTrack = false; private onTimer = 0; private offTimer = 0;
  // stuck / wrong way → the director recovers the car (marshal reset)
  stuckTime = 0;
  needsRecovery = false;
  /** debug: why the speed is limited ('profile' | 'follow' | 'cap' | 'rejoin' | 'alongside') */
  limiter = 'profile';
  private readonly pt = new Float64Array(2);
  /** pure-pursuit path curvature commanded on the last tick, 1/m */
  private kCmd = 0;

  constructor(vehicle: Vehicle, line: RaceLine, perf: CarPerf, spec: CarSpec, profile: Float64Array, params: AiDriverParams, idx: number, traffic: Traffic) {
    this.vehicle = vehicle; this.line = line; this.perf = perf; this.profile = driverProfile(line, perf, profile);
    this.params = params; this.idx = idx; this.traffic = traffic;
    this.rng = new Rng(params.seed);
    void spec;
  }

  /** Forget transient state (after a reset onto the track). */
  resetState(): void {
    this.shift = 0; this.shiftTarget = 0; this.integ = 0; this.brakeCap = 1; this.thrCap = 1;
    this.passTarget = -1; this.passSide = 0; this.passTimer = 0; this.stuckTimer = 0;
    this.passE = Number.NaN; this.passPhase = 0; this.planTimer = 0;
    this.defendSide = 0; this.defendCorner = -1; this.defendTimer = 0; this.offTrack = false;
    this.mishap = null; this.mPhase = 0; this.mT = 0; this.mCorner = -1; this.nextCorner = -1; this.onTimer = 0; this.offTimer = 0;
    this.stuckTime = 0; this.needsRecovery = false; this.hint = -1; this.kCmd = 0; this.passCool = 0; this.traffic.passing[this.idx] = -1;
  }

  private profAt(s: number): number { return this.line.at(this.profile, s); }

  /** True while a loss of control is playing out (the car is then flagged `off` in the Traffic snapshot). */
  get mishapActive(): boolean { return this.mishap !== null; }

  /** Signed distance (m) from s forward to station t, in [-L/2, L/2). */
  private ahead(s: number, t: number): number {
    const L = this.line.L;
    let d = t - s;
    if (d >= 0.5 * L) d -= L; else if (d < -0.5 * L) d += L;
    return d;
  }

  /** The next passable corner whose braking point is 0..maxD m ahead of s (index), or -1. */
  private passableAhead(s: number, maxD: number, minD = 0): number {
    const cs = this.line.corners;
    for (let k = 0; k < cs.length; k++) {
      if (!cs[k].passable) continue;
      const d = this.ahead(s, cs[k].brake);
      if (d >= minD && d <= maxD) return k;
    }
    return -1;
  }

  /**
   * Compute the input for the next `dt` seconds (call before vehicle.step; dt = the control period).
   * Reads this car's projection from the Traffic snapshot.
   */
  update(dt: number): DriverInput {
    const tr = this.traffic, i = this.idx, line = this.line, perf = this.perf, ctl = this.ctl;
    const st = this.vehicle.state;
    const v = Math.max(0, st.speed);
    const s = tr.s[i], lat = tr.lat[i];
    const L = perf.wheelbase;
    const hwI = tr.hw[i];

    // ---- per-lap pace noise
    const lapIdx = Math.floor(tr.U[i] / line.L);
    if (lapIdx !== this.lastLapIdx) {
      this.lastLapIdx = lapIdx;
      if (ctl.noise) {
        const rel = Math.min(0.008, Math.max(0.001, 0.4 * this.params.sigma / Math.max(60, this.params.targetLap)));
        this.lapFactor = 1 + Math.max(-2.5, Math.min(2.5, this.rng.normal())) * rel;
      } else this.lapFactor = 1;
    }

    // ---- heading, off track, stuck
    const [qx, qy, qz, qw] = st.quat;
    const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    let herr = yaw - line.headingAt(s);
    while (herr > Math.PI) herr -= 2 * Math.PI;
    while (herr < -Math.PI) herr += 2 * Math.PI;
    let wheelsOff = 0;
    for (let k = 0; k < 4; k++) if (!st.wheels[k].onTrack) wheelsOff++;
    const edgeL = line.at(line.halfL, s), edgeR = line.at(line.halfR, s);
    const outside = lat > edgeL + 0.3 || lat < -edgeR - 0.3;
    if (wheelsOff >= 3 || outside) {
      this.offTimer += dt; this.onTimer = 0;
      if (!this.offTrack && this.offTimer > 0.15) {
        this.offTrack = true;
        // start the rejoin from where the car is
        this.shift = lat - line.at(line.off, s);
        this.passTarget = -1; if (this.passPhase !== 0) this.passPhase = 3;
      }
    } else {
      this.offTimer = 0;
      if (this.offTrack) { this.onTimer += dt; if (this.onTimer > 1.5) this.offTrack = false; }
    }
    const wrongWay = Math.abs(herr) > 1.75;
    if ((v < 1.5 && ctl.speedCap > 3) || wrongWay) this.stuckTime += dt; else this.stuckTime = Math.max(0, this.stuckTime - 2 * dt);
    if (this.stuckTime > (wrongWay ? 2.5 : 4)) this.needsRecovery = true;

    // ---- corner passages: seeded loss of control (rate x corner difficulty x aggression)
    const cs = line.corners;
    if (cs.length) {
      if (this.nextCorner < 0) {
        let best = Infinity;
        for (let k = 0; k < cs.length; k++) { let d = this.ahead(s, cs[k].brake); if (d <= 0) d += line.L; if (d < best) { best = d; this.nextCorner = k; } }
      }
      const dB = this.ahead(s, cs[this.nextCorner].brake);
      if (dB <= 0 && dB > -60) {
        const k = this.nextCorner;
        this.nextCorner = (k + 1) % cs.length;
        if (ctl.noise && ctl.mishapRate > 0 && this.mishap === null && !this.offTrack && v > 12) {
          if (this.rng.next() < ctl.mishapRate * cs[k].difficulty * MISHAP_AGGRESSION[this.params.aggression]) this.startMishap(k);
        }
      } else if (dB <= -60) this.nextCorner = -1;
    }
    if (this.mishap !== null) this.mT += dt;
    tr.off[i] = this.offTrack || (this.mishap === 'spin' && this.mPhase >= 1) ? 1 : 0;

    // ---- target speed from the profile
    const pf = ctl.paceFactor * this.lapFactor;
    const sp = s + v * 0.12;
    // off the racing line: slower on the inside of a corner by its tighter radius (laneFactor); a little slower anywhere
    // when not in a pass lane (in one only in corners)
    const offline = this.shift === 0 ? 1 : laneFactor(line, this.shift, sp, this.passPhase !== 0);
    const vProf = this.profAt(sp) * pf * offline;
    let vCmd = vProf;
    this.limiter = 'profile';
    let aref = 0;
    {
      const v2 = this.profAt(sp + 2) * pf * offline;
      aref = (v2 * v2 - vProf * vProf) / 4;
    }
    if (ctl.speedCap < vCmd) { vCmd = ctl.speedCap; this.limiter = 'cap'; }
    // the path I am steering for (last tick's pure-pursuit curvature) must stay within the tyres' grip
    // (in a pass lane: the lane's own curvature, not the transient of a lane change, plus a small allowance)
    let kG = Math.abs(this.kCmd);
    if (this.passPhase !== 0) { const kl = line.at(line.curv, sp); kG = Math.min(kG, Math.abs(kl) / Math.max(0.5, 1 - kl * this.shift) + 0.004); }
    if (kG > 2e-3) {
      const vk = Math.sqrt(perf.alat * G / kG);
      if (vk < vCmd) { vCmd = Math.max(0.95 * v, vk); this.limiter = 'grip'; aref = Math.min(aref, 0); }
    }
    // held off the line on the inside of a corner coming up: brake in time for its tighter radius
    if (Math.abs(this.shiftTarget) > 0.5 || Math.abs(this.shift) > 0.5) {
      const sh = Math.abs(this.shiftTarget) > Math.abs(this.shift) ? this.shiftTarget : this.shift;
      const b = 0.75 * BRAKE_MARGIN * perf.abrake * G;
      for (let d = 8; d <= 48; d += 8) {
        const ks = line.at(line.curv, s + d) * sh;
        if (ks <= 0.02) continue;
        const vt = this.profAt(s + d) * pf * Math.sqrt(Math.max(0.5, 1 - ks));
        const vl = Math.sqrt(vt * vt + 2 * b * d);
        if (vl < vCmd) { vCmd = vl; this.limiter = 'offline'; aref = Math.min(aref, 0); }
      }
    }
    // in a pass lane: the speed its own path allows (the lane clamped to the road, so where the road squeezes it the
    // car runs along the edge, tighter than the lane), looked ahead with a braking envelope
    if (this.passPhase !== 0) {
      const eL = this.passPhase === 3 ? 0 : this.passE;
      const b = 0.75 * BRAKE_MARGIN * perf.abrake * G, aG = CORNER_MARGIN * perf.alat * G;
      let ePrev = this.laneAt(s - 8, eL, hwI), e0 = this.laneAt(s, eL, hwI);
      for (let d = 0; d <= 48; d += 8) {
        const x = s + d, eNext = this.laneAt(x + 8, eL, hwI), k = line.at(line.curv, x);
        const kap = Math.abs(k / Math.max(0.5, 1 - k * e0) + (eNext - 2 * e0 + ePrev) / 64);
        ePrev = e0; e0 = eNext;
        if (kap < 2e-3) continue;
        const vl = Math.sqrt(aG / kap + 2 * b * d);
        if (vl < vCmd) { vCmd = Math.max(d === 0 ? 0.95 * v : 0, vl); this.limiter = 'lane'; aref = Math.min(aref, 0); }
      }
    }
    // mishap speed: overdrive the entry (brake late, never below mOver x profile), then lose time
    let mishapLat = NaN;
    if (this.mishap !== null) {
      const C = cs[this.mCorner];
      const toApex = this.ahead(s, C.apex);
      if (this.mPhase === 0) {
        const carry = Math.min(v, this.mOver * vProf);
        if (carry > vCmd) { vCmd = carry; aref = Math.max(aref, 0); this.limiter = 'mishap'; }
        if (this.mishap === 'wide') {
          if (toApex < 50) {
            const out = C.dir > 0 ? line.at(line.halfR, s + 10) : line.at(line.halfL, s + 10);
            mishapLat = -C.dir * (out - hwI + this.mOut);
          }
          if (this.offTrack || toApex < -25 || this.mT > 12) { this.mPhase = 1; this.mT = 0; }
        } else if (toApex < 35 || this.mT > 12) { this.mPhase = 1; this.mT = 0; }
      } else if (this.mishap === 'wide') {
        // on the dirt / gathered it up: slow for mHold s, then race on (the rejoin logic brings it back)
        const vs = Math.max(8, 0.45 * vProf);
        if (vs < vCmd) { vCmd = vs; aref = Math.min(aref, 0); this.limiter = 'mishap'; }
        if (this.mT > this.mHold) this.mishap = null;
      } else if (this.mT > 15) this.mishap = null; // spin: the marshal reset (resetState) normally ends it
    }

    // ---- traffic: the lane model (NOTES "Racecraft (the lane model) and mishaps"). Lane coordinate e = lateral offset from the
    // racing line; every car occupies [min(e, eT) - hw, max(e, eT) + hw] (eT = where it is heading). Cars whose spans
    // do not overlap mine (with clearance) are in another lane: never followed, never given way to.
    const n = tr.n, order = tr.order;
    const myFront = tr.front[i], myRear = tr.rear[i];
    const eMe = lat - line.at(line.off, s);
    let shiftWant = 0;
    let leadJ = -1, leadGap = Infinity;
    const headway = HEADWAY[this.params.aggression];
    const green = !ctl.noPass;
    this.planTimer -= dt;
    this.passCool = Math.max(0, this.passCool - dt);
    if (this.passPhase !== 0) this.passStep(dt, v, eMe, green, pf);
    // where I am heading in lane coordinates: the pass lane, the racing line on the way back, else last tick's target
    const eAim = this.passPhase === 1 || this.passPhase === 2 ? this.passE : this.passPhase === 3 ? 0 : this.shiftTarget;
    // walk ahead along the order: the nearest car in my lane (its span overlaps the band I sweep through to reach it)
    for (let k = 1; k < n; k++) {
      const j = order[(tr.rank[i] + k) % n];
      const d = tr.ds(i, j);
      if (d < 0 || d > 130) break;
      if (tr.away[j] && !this.offTrack) continue;
      const gap = d - myFront - tr.rear[j];
      const sj = tr.s[j];
      const aimThere = Math.max(this.roadLo(sj, hwI), Math.min(this.roadHi(sj, hwI), eAim));
      const a = Math.min(1, d / (LD0 + LDK * v + 1));
      const eThere = eMe * (1 - a) + aimThere * a;
      // (the whole band only when it is close; further up the road, where I will be when I get there)
      const near = gap < 15;
      const mLo = near ? Math.min(eMe, eThere) : eThere, mHi = near ? Math.max(eMe, eThere) : eThere;
      const ext = tr.off[j] ? 0.8 : 0;
      const jLo = this.spanLo(j) - ext, jHi = this.spanHi(j) + ext;
      const sep = Math.max(jLo - mHi, mLo - jHi);
      const needF = hwI + tr.hw[j] + FOLLOW_CLR + this.yawClr(sj);
      if (sep >= needF) {
        // and where I would catch it (within 3 s), both lanes clamped to the road there: a lane the road squeezes
        // into mine is my lane by then
        const tc = Math.min(3, Math.max(0, gap) / Math.max(0.5, v - tr.v[j]));
        const sm = sj + Math.max(0, tr.v[j]) * tc;
        const me = Math.max(this.roadLo(sm, hwI), Math.min(this.roadHi(sm, hwI), eAim));
        const itLo = Math.max(this.roadLo(sm, tr.hw[j]), Math.min(this.roadHi(sm, tr.hw[j]), jLo)), itHi = Math.max(this.roadLo(sm, tr.hw[j]), Math.min(this.roadHi(sm, tr.hw[j]), jHi));
        if (Math.max(itLo - me, me - itHi) >= needF) continue;
      }
      leadGap = gap; leadJ = j;
      break;
    }
    this.leadIdx = leadJ;
    {
    }
    if (leadJ >= 0) {
      const vj = Math.max(0, tr.v[leadJ]);
      // formation / yellow: constant gap plus a time headway (pure constant spacing is string-unstable
      // over 45 cars); racing: time headway by aggression
      // (on a pass, behind the car being passed where the road squeezes the lanes together: PASS_HEADWAY)
      const gd = ctl.minGap > 0 ? Math.max(0.6 * ctl.minGap, 0.3 * ctl.minGap + 0.6 * v) : 1.5 + (this.passPhase === 1 && leadJ === this.passTarget ? PASS_HEADWAY : headway) * v;
      // speed that holds the gap (P on gap, small deadband) and a hard braking limit for the closing speed
      const ge = leadGap - gd;
      let vF = vj + (ctl.minGap > 0 ? 0.35 : 0.6) * (Math.abs(ge) < 1.5 ? 0 : ge - Math.sign(ge) * 1.5);
      // braking limit: stop behind it even if it brakes as hard as I can (0.1 s reaction)
      const room = Math.max(0, leadGap - 0.8 - 0.1 * Math.max(0, v - vj));
      const bm = 0.85 * perf.abrake * G;
      const vBrake = Math.sqrt(0.85 * vj * vj + 2 * bm * room);
      if (vBrake < vF) vF = vBrake;
      if (vF < vCmd) { vCmd = Math.max(0, vF); this.limiter = 'follow'; aref = Math.min(aref, Math.min(0, tr.a[leadJ])); }
    }

    // formation / yellow: the cap is the pace car speed + 3 m/s so followers can close gaps; whoever
    // has nobody close ahead holds the pace speed itself
    if (ctl.minGap > 0 && (leadJ < 0 || leadGap > 60) && ctl.speedCap - 3 < vCmd) { vCmd = ctl.speedCap - 3; this.limiter = 'cap'; }
    // ---- start a pass on the car I am following in my lane: clearly faster, stuck behind a slower car, or it is off
    if (green && (this.passPhase === 0 || this.passPhase === 2) && leadJ >= 0 && !this.offTrack && this.mishap === null) {
      const j = leadJ, vj = Math.max(0, tr.v[j]);
      const myPot = this.profAt(tr.s[j]) * pf;
      const slower = tr.off[j] === 1 || myPot > PASS_ADV[this.params.aggression] * Math.max(1, vj) || tr.pace[j] > this.params.targetLap * 1.004;
      if (leadGap < Math.max(ctl.minGap, 1.5 + headway * v) + 10 && slower) this.stuckTimer += dt; else this.stuckTimer = Math.max(0, this.stuckTimer - dt);
      const clearly = tr.pace[i] < CLEARLY_FASTER * tr.pace[j];
      // clearly faster; a car that is off / nearly stopped; or quicker on pace and stuck behind it (a car held up in a
      // train is not a reason: everybody behind it would pull out at once)
      const want = clearly || tr.off[j] === 1 || vj < 0.5 * myPot || (tr.pace[i] < tr.pace[j] && this.stuckTimer > STUCK_T[this.params.aggression]);
      if (want && this.passCool <= 0 && this.planTimer <= 0 && leadGap < Math.max(30, 0.9 * v)) {
        this.planTimer = PLAN_EVERY;
        const e = this.planLane(j, v, pf, NaN);
        if (!Number.isNaN(e)) {
          this.passE = e; this.passPhase = 1; this.passTarget = j; this.passSide = e > tr.e[j] ? 1 : -1;
          this.passTimer = 0; this.stuckTimer = 0;
        }
      }
    } else if (this.passPhase === 0) this.stuckTimer = Math.max(0, this.stuckTimer - dt);

    // ---- defending (lightly): a car within 3 % of my pace, within ~1 s behind, approaching a passable
    // corner: cover its inside once, hold it to the apex (no weaving). Never against a clearly faster car.
    this.defendCool = Math.max(0, this.defendCool - dt);
    if (green && this.passPhase === 0 && !this.offTrack && this.mishap === null) {
      if (this.defendSide !== 0) {
        this.defendTimer -= dt;
        if (this.defendTimer <= 0 || this.ahead(s, cs[this.defendCorner].apex) < 0) { this.defendSide = 0; this.defendCorner = -1; this.defendCool = 2; }
      } else if (this.defendCool <= 0) {
        for (let k = 1; k < n; k++) {
          const j = order[(tr.rank[i] - k + n) % n];
          const d = -tr.ds(i, j);
          if (d < 0 || d > Math.min(28, Math.max(10, v))) break;
          if (tr.away[j] || tr.off[j]) continue;
          const r = tr.pace[j] / tr.pace[i];
          if (r >= CLEARLY_FASTER && r <= 1 / CLEARLY_FASTER && d > myRear + tr.front[j] + 1) {
            const c = this.passableAhead(s, 120, 10);
            if (c >= 0) { this.defendSide = cs[c].dir; this.defendCorner = c; this.defendTimer = 8; }
          }
          break;
        }
      }
    } else { this.defendSide = 0; this.defendCorner = -1; }

    // ---- lateral target (lane coordinate at the look point)
    const sLook = s + LD0 + LDK * v;
    const lineLook = line.at(line.off, sLook);
    if (this.passPhase === 1 || this.passPhase === 2) shiftWant = this.passE;
    else if (this.passPhase === 3) shiftWant = 0;
    else if (this.defendSide !== 0) shiftWant = this.defendSide * DEFEND[this.params.aggression];
    if (!Number.isNaN(mishapLat)) shiftWant = mishapLat - lineLook;
    if (this.offTrack) {
      // rejoin: come back just inside the edge, the line ramps back in afterwards; wait at / beyond the edge until
      // the lane I rejoin into is free (nobody in it reaching me within 2.5 s)
      const lo = -edgeR + hwI + 0.6, hi = edgeL - hwI - 0.6;
      const inLat = Math.max(lo, Math.min(hi, lat));
      const eIn = inLat - line.at(line.off, s);
      const threat = this.laneBlock(Math.min(eMe, eIn) - hwI - LANE_CLR, Math.max(eMe, eIn) + hwI + LANE_CLR, 2.5, v, 20, 90, -1) < 2.5;
      const tgtLat = threat ? (lat > hi || lat < lo ? lat : lat > 0 ? hi : lo) : inLat;
      shiftWant = tgtLat - line.at(line.off, s);
      const vr = threat ? 8 : Math.max(12, 0.65 * vProf);
      if (vr < vCmd) { vCmd = vr; this.limiter = 'rejoin'; aref = Math.min(aref, 0); }
    }
    // alongside: cars overlapping in s bound my lateral corridor (a lane's width apart, never steer into them)
    let push = 0;
    let corLo = -Infinity, corHi = Infinity, corLoD = 0, corHiD = 0, corLoV = 0, corHiV = 0;
    let passerSqueeze = false;
    // (and in lane coordinates at the look point: where its lane, clamped to the road there, will put it)
    let corLoE = -Infinity, corHiE = Infinity;
    const sLk = s + LD0 + LDK * v;
    const yc = Math.max(this.yawClr(s), this.yawClr(sLk + v));
    {
      for (let dir = -1; dir <= 1; dir += 2) {
        for (let k = 1; k < n; k++) {
          const j = order[(tr.rank[i] + dir * k + n * 2) % n];
          const d = tr.ds(i, j);
          // behind: cars overlapping me, and a car passing me from 12 m back (I hold my lane and leave it its lane)
          if (dir > 0 ? (d < 0 || d > myFront + tr.rear[j] + 3) : (d > 0 || d < -(myRear + tr.front[j] + 12))) break;
          if (tr.away[j] && !this.offTrack) continue;
          const dl = lat - tr.lat[j];
          if (dir < 0 && d < -(myRear + tr.front[j] + 1) && (Math.abs(dl) < hwI + tr.hw[j] + 0.1 || tr.passing[j] !== i)) continue;
          const need = hwI + tr.hw[j] + ALONG_CLR + yc;
          const side = dl >= 0 ? 1 : -1;
          // only cars actually beside me (a car straight ahead / behind is handled by following)
          if (Math.abs(dl) < hwI + tr.hw[j] - 0.2 && Math.abs(d) > 0.6 * (myFront + tr.rear[j])) continue;
          if (side > 0) { if (tr.lat[j] + need > corLo) { corLo = tr.lat[j] + need; corLoD = d; corLoV = tr.v[j]; } } else if (tr.lat[j] - need < corHi) { corHi = tr.lat[j] - need; corHiD = d; corHiV = tr.v[j]; }
          {
            // (a car passing me: where the road will push its lane over the next second, so I make room in time, but
            // never further than my own road allows there: beyond that it is a squeeze and the car further back yields)
            const look = tr.passing[j] === i ? 1.0 * v : 0;
            for (let x = 0; x <= look; x += Math.max(4, 0.5 * v)) {
              const sx = sLk + x;
              const eS = side > 0 ? this.spanHi(j) : this.spanLo(j);   // its edge toward me (target or drift)
              const eL = Math.max(this.roadLo(sx, tr.hw[j]), Math.min(this.roadHi(sx, tr.hw[j]), eS));
              if (side > 0) corLoE = Math.max(corLoE, Math.min(eL + need, this.roadHi(sx, hwI) - 0.35));
              else corHiE = Math.min(corHiE, Math.max(eL - need, this.roadLo(sx, hwI) + 0.35));
              if (look === 0) break;
            }
          }
          if (Math.abs(dl) < need) {
            push += side * (need - Math.abs(dl));
            if (tr.passing[j] === i && d < 0 && d > -PINCH_OK * (myRear + tr.front[j])) passerSqueeze = true;
          }
        }
      }
    }
    // being passed: the lane of a car passing me (within 25 m behind, laterally clear of me) is reserved; I never drift
    // into it, also not while making room for another car passing me on the other side
    for (let k = 1; k < n; k++) {
      const j = order[(tr.rank[i] - k + n) % n];
      const d = -tr.ds(i, j);
      if (d < 0 || d > 25) break;
      if (tr.passing[j] !== i || tr.away[j]) continue;
      const need = hwI + tr.hw[j] + ALONG_CLR, ej = tr.eT[j];
      if (Math.abs(ej - eMe) < need - 0.3) continue;   // straight behind me in my lane: nothing reserved yet
      if (ej > eMe) corHiE = Math.min(corHiE, ej - need); else corLoE = Math.max(corLoE, ej + need);
    }
    // pinch guard: a car alongside in the next lane whose lane and mine (both clamped to the road) close up within
    // ~2 s (the racing line runs edge to edge, so lanes measured from it converge at turn-in, apex and exit): the car
    // whose centre is further back drops behind it; the one ahead holds its lane
    for (let k = 1; k < n; k++) {
      const j = order[(tr.rank[i] + k) % n];
      const d = tr.ds(i, j);
      if (d < 0 || d > myFront + tr.rear[j] + 4 + 1.5 * Math.max(0, v - tr.v[j])) break;
      if (tr.away[j] || tr.v[j] < 4) continue;                          // a (nearly) stopped car: following / planning handle it
      if (Math.abs(lat - tr.lat[j]) < hwI + tr.hw[j] - 0.2) continue;   // straight ahead: following handles it
      if (j === this.passTarget && d < PINCH_OK * (myFront + tr.rear[j])) continue;   // alongside on a pass: it makes room
      const need = hwI + tr.hw[j] + 0.3 + this.yawClr(s + 0.5 * v), ej = tr.eT[j], hwJ = tr.hw[j];
      const ePlan = this.passPhase === 1 || this.passPhase === 2 ? this.passE : this.passPhase === 3 ? 0 : this.shiftTarget;
      const dist = Math.max(12, 2 * v);
      for (let x = 0; x <= dist; x += 10) {
        const sx = s + x;
        const me = Math.max(this.roadLo(sx, hwI), Math.min(this.roadHi(sx, hwI), ePlan));
        const it = Math.max(this.roadLo(sx, hwJ), Math.min(this.roadHi(sx, hwJ), ej));
        if (Math.abs(me - it) < need && (me - it) * (lat - tr.lat[j]) >= 0) {
          const vp = Math.max(0.5 * tr.v[j], tr.v[j] - 4);
          if (vp < vCmd) { vCmd = vp; this.limiter = 'pinch'; aref = Math.min(aref, -1); }
          break;
        }
      }
    }
    // being passed: a car passing me alongside and converging → lift slightly (never a defence)
    if (passerSqueeze && 0.97 * v < vCmd) { vCmd = 0.97 * v; this.limiter = 'passed'; aref = Math.min(aref, 0); }
    // rate-limited shift (faster when pushing away from contact)
    {
      let tgt = shiftWant + push;
      const mg = this.passPhase !== 0 ? PASS_EDGE : 0.15;   // a pass lane keeps a little more room to the edge
      const lo = -line.at(line.halfR, sLook) + hwI + mg - lineLook, hi = line.at(line.halfL, sLook) - hwI - mg - lineLook;
      // corridor between the cars alongside (absolute lateral → shift at the look point)
      const cl = Math.max(corLo - lineLook, corLoE), ch = Math.min(corHi - lineLook, corHiE);
      let squeezed = cl > ch;
      if (cl <= ch) tgt = Math.max(cl, Math.min(ch, tgt));
      else tgt = 0.5 * (cl + ch);
      // track edges vs the corridor: no room on the track → use up to 0.6 m past the edge and drop back
      if (!this.offTrack && Number.isNaN(mishapLat)) {
        const tc = Math.max(lo - 0.6, Math.min(hi + 0.6, tgt));
        if (tc < lo - 0.05 || tc > hi + 0.05 || Math.abs(tc - tgt) > 0.05) squeezed = true;
        tgt = tc;
      }
      // the car further back gives way (two cars side by side never both back off): squeezed, or the lane gap
      // to a car alongside that is ahead of me nearly gone (only to a moving car, down to just under its speed)
      const behindHi = corHi < Infinity && corHiD > 0 && corHiV > 4, behindLo = corLo > -Infinity && corLoD > 0 && corLoV > 4;
      let giveWay = squeezed && (behindHi || behindLo);
      const latP = lat + Math.max(-3, Math.min(3, tr.vlat[i])) * 0.4; // where I will be in 0.4 s
      if (behindHi && Math.max(lat, latP) > corHi + GIVE_CLR) giveWay = true;
      if (behindLo && Math.min(lat, latP) < corLo - GIVE_CLR) giveWay = true;
      const vGive = Math.max(3, (behindHi ? corHiV : corLoV) - 1.5); // relative to it: never a runaway lift
      if (giveWay && vGive < vCmd) { vCmd = vGive; this.limiter = 'alongside'; aref = Math.min(aref, -0.3); }

      this.shiftTarget = tgt;
      tr.eT[i] = tgt;
      const rate = (push !== 0 || !Number.isNaN(mishapLat) ? 2 * SHIFT_RATE : this.offTrack ? 0.8 * SHIFT_RATE : this.passPhase !== 0 ? PASS_SHIFT * SHIFT_RATE : SHIFT_RATE) * dt;
      const dsh = this.shiftTarget - this.shift;
      this.shift += dsh > rate ? rate : dsh < -rate ? -rate : dsh;
      // the line sweeps across the road faster than the shift may change: never let a held shift carry the car off
      if (!this.offTrack && Number.isNaN(mishapLat)) this.shift = Math.max(lo, Math.min(hi, this.shift));
    }

    // ---- steering: pure pursuit from the rear axle
    {
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const rx = st.pos[0] - cy * L / 2, ry = st.pos[1] - sy * L / 2;
      const Ld = LD0 + LDK * v;
      const sT = s - L / 2 + Ld;
      line.pointAt(sT, line.at(line.off, sT) + this.shift, this.pt);
      const dx = this.pt[0] - rx, dy = this.pt[1] - ry;
      const alpha = Math.atan2(-sy * dx + cy * dy, cy * dx + sy * dy);
      const dist = Math.max(1, Math.hypot(dx, dy));
      const kappa = 2 * Math.sin(alpha) / dist;
      this.kCmd = kappa;
      let delta = Math.atan(L * kappa) + KR * (v * kappa - st.angVel[2]);
      delta += perf.kUs * Math.max(-1.3, Math.min(1.3, (v * v * kappa) / G));
      this.input.steer = Math.max(-1, Math.min(1, delta / perf.maxSteer));
    }

    // ---- speed control
    {
      const e = vCmd - v;
      const kp = 0.3, ki = 0.15;
      const u = aref / G + kp * e + ki * this.integ;
      let throttle = 0, brake = 0;
      const cd = coastDecel(perf, v);
      if (u >= 0) {
        const amax = Math.max(0.03, accAt(perf, v) / G + cd);
        throttle = Math.min(1, (u + cd) / amax);
      } else {
        brake = Math.min(1, Math.max(0, (-u - cd) / perf.brakeGain));
      }
      let lock = 0, spin = 0;
      for (let k = 0; k < 4; k++) { const w = st.wheels[k]; if (w.load > 1000 && -w.slipRatio > lock) lock = -w.slipRatio; }
      for (let k = perf.drivenFront ? 0 : 2; k < (perf.drivenRear ? 4 : 2); k++) { const w = st.wheels[k]; if (w.load > 1000 && w.slipRatio > spin) spin = w.slipRatio; }
      const kpk = perf.peakSlipRatio;
      this.brakeCap = lock > 1.5 * kpk ? Math.max(0.25, Math.min(this.brakeCap, brake) - 3 * dt) : Math.min(1, this.brakeCap + 3 * dt);
      this.thrCap = spin > 1.5 * kpk ? Math.max(0.2, Math.min(this.thrCap, throttle) - 3 * dt) : Math.min(1, this.thrCap + 3 * dt);
      // rear stepping out on a trailing brake: ease off the brake (a driver's feel for entry oversteer)
      const rs = Math.max(Math.abs(st.wheels[2].slipAngle), Math.abs(st.wheels[3].slipAngle));
      if (rs > REAR_SLIP0 && this.limiter === 'profile') brake *= Math.max(0.1, 1 - REAR_SLIPK * (rs - REAR_SLIP0));
      brake = Math.min(brake, this.brakeCap);
      throttle = Math.min(throttle, this.thrCap);
      const sat = (throttle >= 1 && e > 0) || (brake >= 1 && e < 0);
      if (!sat) this.integ = Math.max(-0.5, Math.min(0.5, this.integ + e * dt));
      // stopped behind something: hold the brake
      if (vCmd < 0.3 && v < 1) { throttle = 0; brake = 0.4; }
      this.input.throttle = throttle;
      this.input.brake = brake;
    }
    this.input.handbrake = false;
    tr.passing[i] = this.passTarget;
    // ---- spin: handbrake and full lock into the corner at turn-in, then lock everything up and stop
    if (this.mishap === 'spin' && this.mPhase >= 1) {
      const C = cs[this.mCorner];
      this.input.throttle = 0; this.input.handbrake = true;
      if (this.mPhase === 1) {
        this.input.steer = C.dir; this.input.brake = 0.2;
        if (Math.abs(herr) > 1.3 || this.mT > 1.5) { this.mPhase = 2; this.mT = 0; }
      } else {
        this.input.steer = 0; this.input.brake = 1;
      }
    }
    return this.input;
  }

  /** Begin a loss of control at corner k (kind and severity drawn from this car's Rng). */
  private startMishap(k: number): void {
    this.mishapCount++; this.lastMishapCorner = k; this.mCorner = k; this.mPhase = 0; this.mT = 0;
    this.passTarget = -1; this.passSide = 0; this.defendSide = 0; this.defendCorner = -1;
    if (this.passPhase !== 0) this.passPhase = 3;
    if (this.rng.next() < MISHAP_WIDE) {
      this.mishap = 'wide';
      this.mOver = this.rng.range(1.15, 1.3);           // entry speed over the car's own profile
      this.mOut = this.rng.range(0.4, 2.8);             // m past the outside edge (2 or 4 wheels off)
      this.mHold = MISHAP_HOLD0 + MISHAP_HOLDK * this.rng.range(3, 8); // slow time for a 3-8 s loss
    } else {
      this.mishap = 'spin';
      this.mOver = this.rng.range(1.0, 1.15);
    }
  }

  // ------------------------------------------------------------------ lane model helpers

  /** Lowest / highest lane coordinate (offset from the racing line) a car of half width hw may use at s. */
  private roadLo(s: number, hw: number): number { this.road(s); return this.rR + hw + 0.15; }
  private roadHi(s: number, hw: number): number { this.road(s); return this.rL - hw - 0.15; }
  /** Edges in lane coordinates at s (rL = left edge, rR = right edge, offsets from the racing line); cached per s. */
  private road(s: number): void {
    if (s === this.rS) return;
    const l = this.line, u = l.wrap(s) / l.spacing;
    let a = Math.floor(u); if (a >= l.N) a = l.N - 1;
    const b = a + 1 === l.N ? 0 : a + 1, f = u - a;
    const off = l.off[a] + f * (l.off[b] - l.off[a]);
    this.rL = l.halfL[a] + f * (l.halfL[b] - l.halfL[a]) - off;
    this.rR = -(l.halfR[a] + f * (l.halfR[b] - l.halfR[a])) - off;
    this.rS = s;
  }
  private rS = Number.NaN; private rL = 0; private rR = 0;

  /** Lateral span centre-line bounds of car q in lane coordinates: now, its target, and 0.6 s of its drift. */
  private spanLo(q: number): number { const tr = this.traffic, d = tr.e[q] + Math.max(-2, Math.min(2, 0.6 * tr.ve[q])); return Math.min(tr.e[q], tr.eT[q], d); }
  private spanHi(q: number): number { const tr = this.traffic, d = tr.e[q] + Math.max(-2, Math.min(2, 0.6 * tr.ve[q])); return Math.max(tr.e[q], tr.eT[q], d); }

  /** A car within 25 m behind that is passing me occupies (its span overlaps) [lo, hi]: being passed, I hold my lane. */
  private passerIn(lo: number, hi: number): boolean {
    const tr = this.traffic, i = this.idx, n = tr.n;
    for (let k = 1; k < n; k++) {
      const q = tr.order[(tr.rank[i] - k + n) % n];
      const r = tr.ds(i, q);
      if (r > 0 || r < -25) break;
      if (tr.passing[q] !== i) continue;
      if (this.spanLo(q) - tr.hw[q] < hi && this.spanHi(q) + tr.hw[q] > lo) return true;
    }
    return false;
  }

  /**
   * Extra lateral clearance in tight corners (m): yawed through a hairpin, a car's box sweeps wider than its half
   * width (≈ half its length × sin of the yaw); 10 m × |curvature|, at most 0.8 m.
   */
  private yawClr(s: number): number { return Math.min(0.8, 10 * Math.abs(this.line.at(this.line.curv, s))); }

  /** Lane coordinate e clamped to the road at s the way a pass lane is held (PASS_EDGE from the edge). */
  private laneAt(s: number, e: number, hw: number): number {
    return Math.max(this.roadLo(s, hw) + PASS_EDGE - 0.15, Math.min(this.roadHi(s, hw) - PASS_EDGE + 0.15, e));
  }

  /** Braking cushion (m) a car at vq behind me needs when I am in its lane in front of it at vMe. */
  private cushB(vq: number, vMe: number): number { return 2 + 0.2 * vq + 0.8 * Math.max(0, vq - vMe); }

  /**
   * Lane occupancy: the earliest time (s, within horizon T; Infinity = free) at which another car whose lateral
   * span overlaps [lo, hi] (lane coordinates) is inside my window: its rear within my front plus a cushion
   * (2 m + 0.2 s at my speed) ahead, or its front within my rear plus its braking cushion behind. Occupants are
   * projected forward at their speed, I at vMe. 0 = occupied now. Cars further than `ahead` / `behind` m and
   * car `skip` are ignored.
   * With a lane `eLane` (the lane [lo, hi] belongs to) the lateral overlap is tested where the two cars will be level
   * (start, middle and end of the window), both lanes clamped to the road there: a lane the road squeezes into mine
   * is occupied. With `skipPinch`, car `skip` (the car I am passing) counts only there and only while I am not yet
   * alongside it (centres > PINCH_OK x lengths apart; alongside, it makes room).
   */
  private laneBlock(lo: number, hi: number, T: number, vMe: number, ahead: number, behind: number, skip: number, eLane = Number.NaN, skipPinch = false): number {
    const tr = this.traffic, i = this.idx, n = tr.n, hwI = tr.hw[i];
    const road = !Number.isNaN(eLane);
    let tFirst = Infinity;
    for (let dir = 1; dir >= -1; dir -= 2) {
      for (let k = 1; k < n; k++) {
        const q = tr.order[(tr.rank[i] + dir * k + 2 * n) % n];
        const r0 = tr.ds(i, q);
        if (dir > 0 ? (r0 < 0 || r0 > ahead) : (r0 > 0 || r0 < -behind)) break;
        if (tr.away[q] || (q === skip && !(road && skipPinch))) continue;
        const ext = tr.hw[q] + (tr.off[q] ? 0.8 : 0);
        const lateralNow = !(this.spanLo(q) - ext >= hi || this.spanHi(q) + ext <= lo);
        if (!road && !lateralNow) continue;
        const vq = Math.max(0, tr.v[q]), dv = vq - vMe;
        const bLo = -(tr.rear[i] + tr.front[q] + this.cushB(vq, vMe)), bHi = tr.front[i] + tr.rear[q] + 2 + 0.2 * vMe;
        // window [t0, t1] in which q is inside my longitudinal band
        let t0: number, t1: number;
        if (Math.abs(dv) < 1e-6) { if (r0 < bLo || r0 > bHi) continue; t0 = 0; t1 = T; }
        else { const ta = (bLo - r0) / dv, tb = (bHi - r0) / dv; t0 = Math.max(0, Math.min(ta, tb)); t1 = Math.min(T, Math.max(ta, tb)); }
        if (t0 > t1) continue;
        if (!road) { if (t0 < tFirst) tFirst = t0; continue; }
        const alongside = PINCH_OK * (tr.front[i] + tr.rear[q]);
        for (let m = 0; m < 3; m++) {
          const t = m === 0 ? t0 : m === 1 ? 0.5 * (t0 + t1) : t1;
          if (t >= tFirst) break;
          if (q === skip && (t === 0 || r0 + dv * t <= alongside)) continue;
          let ok: boolean;
          if (t === 0 && q !== skip) ok = !lateralNow;
          else {
            const x = tr.s[q] + vq * t, sh = this.laneAt(x, eLane, hwI) - eLane;
            const qLo = Math.max(this.roadLo(x, tr.hw[q]), Math.min(this.roadHi(x, tr.hw[q]), this.spanLo(q))) - ext;
            const qHi = Math.max(this.roadLo(x, tr.hw[q]), Math.min(this.roadHi(x, tr.hw[q]), this.spanHi(q))) + ext;
            ok = qLo >= hi + sh || qHi <= lo + sh;
          }
          if (!ok) { tFirst = t; break; }
        }
      }
    }
    return tFirst;
  }

  /** Mean own target speed over the next `dist` m on lane coordinate e (its radius-limited speed). */
  private laneSpeed(e: number, s0: number, pf: number, dist: number): number {
    let acc = 0, k = 0;
    for (let d = 0; d <= dist; d += 10, k++) acc += this.profAt(s0 + d) * pf * laneFactor(this.line, e, s0 + d, true);
    return acc / k;
  }

  /**
   * Pass planning around car j (the car I follow): the free lane with the longest clear window. Candidates are
   * the nearest lane on each side clear of j's span and the one beyond it (lanes on the grid e = k · laneW). A lane
   * qualifies when it is on the road here and over the next 30 m, my speed in it beats j's, and it stays free
   * (occupants projected forward) until I am clear ahead of j by its braking cushion. Score: clear time, minus
   * where the lane is pinched by the road over the pass (j would have to make room), plus a bonus for the inside
   * of the next corner. Returns the lane coordinate or NaN.
   */
  private planLane(j: number, v: number, pf: number, avoid: number): number {
    const tr = this.traffic, line = this.line, i = this.idx, s = tr.s[i], hwI = tr.hw[i], W = tr.laneW;
    const jLo = this.spanLo(j) - tr.hw[j] - (tr.off[j] ? 0.8 : 0), jHi = this.spanHi(j) + tr.hw[j] + (tr.off[j] ? 0.8 : 0);
    // already beside it (not straight behind): only lanes on my side, never across its lane
    const eMe = tr.e[i], behind = tr.ds(i, j) > tr.front[i] + tr.rear[j] + 1;
    const mySide = eMe - hwI >= jHi ? 1 : eMe + hwI <= jLo ? -1 : 0;
    let c = 0;
    for (let d = 20; d <= 150; d += 10) c += line.at(line.curv, s + d);
    const inside = c > 0.002 ? 1 : c < -0.002 ? -1 : 0;
    // j's speed: its own profile over the stretch, scaled down when it is held up now
    const pj = tr.profile[j], vj = Math.max(0, tr.v[j]);
    let vJ = vj;
    if (pj) {
      let acc = 0, k = 0;
      for (let d = 0; d <= 100; d += 10, k++) acc += line.at(pj, s + d);
      vJ = (acc / k) * Math.min(1, vj / Math.max(1, line.at(pj, tr.s[j])));
      if (tr.off[j]) vJ = Math.min(vJ, vj);
    }
    const D = tr.ds(i, j) + tr.rear[i] + tr.front[j] + this.cushB(vj, v);
    let best = NaN, bestScore = -Infinity;
    for (let sd = 0; sd < 2; sd++) {
      const side = sd === 0 ? (inside || 1) : -(inside || 1);
      const k0 = side > 0 ? Math.ceil((jHi + hwI + LANE_CLR) / W - 1e-9) : Math.floor((jLo - hwI - LANE_CLR) / W + 1e-9);
      for (let m = 0; m < 2; m++) {
        const e = (k0 + side * m) * W;
        if (e === avoid) continue;
        if (mySide !== 0 && side !== mySide && !behind) continue;
        if (this.passerIn(Math.min(e, eMe) - hwI - LANE_CLR, Math.max(e, eMe) + hwI + LANE_CLR)) continue;
        // the band I sweep through on the way there must be free now (j: following keeps me behind it)
        if (Math.abs(e - eMe) > W * 0.5 && this.laneBlock(Math.min(e, eMe) - hwI - LANE_CLR, Math.max(e, eMe) + hwI + LANE_CLR, 1.5, v, 40, 40, j) < 1.5) continue;
        let onRoad = true;
        for (let d = 0; d <= 30; d += 15) if (e < this.roadLo(s + d, hwI) - 0.3 || e > this.roadHi(s + d, hwI) + 0.3) { onRoad = false; break; }
        if (!onRoad) continue;
        const adv = this.laneSpeed(e, s, pf, 100) - vJ;
        if (adv < MIN_ADV) continue;
        const Tn = Math.min(PLAN_T, D / adv);
        if (D / adv > PLAN_T_MAX) continue;
        // (projected at the speed I plan to pass at: a slower car further up that lane blocks it)
        const tFree = this.laneBlock(e - hwI - LANE_CLR, e + hwI + LANE_CLR, Tn + 2, Math.max(v, vJ + adv), 150, 60, j, e, true);
        if (tFree < Tn + 0.5) continue;
        const score = Math.min(12, tFree) + (inside !== 0 && side === inside ? 3 : 0) - m - 0.2 * Tn;
        if (score > bestScore) { bestScore = score; best = e; this.planAdv = adv; }
      }
    }
    return best;
  }

  /** A pass in hand: progress, done (next car of a train, else back to the racing line), abort, the merge. */
  private passStep(dt: number, v: number, eMe: number, green: boolean, pf: number): void {
    const tr = this.traffic, i = this.idx, hwI = tr.hw[i];
    if (this.passPhase === 1) {
      const j = this.passTarget;
      this.passTimer += dt;
      const d = tr.ds(i, j);
      let end = '';
      if (!green) end = 'flag';
      else if (this.offTrack || this.mishap !== null) end = 'off';
      else if (tr.away[j]) end = 'away';
      else if (d > DROP_BACK) end = 'dropped';
      else if (this.passTimer > PASS_T_MAX) end = 'timeout';
      if (end) { this.passEnd = end; this.passCool = 1.5; this.passPhase = 2; this.passTarget = -1; this.stuckTimer = 0; return; }
      if (d < -(tr.rear[i] + tr.front[j] + 1)) {
        // clear of j: a train? the next car ahead in the racing lane that I am catching → pass it in the same lane
        this.passEnd = 'done';
        let q = -1;
        for (let k = 1; k < tr.n; k++) {
          const c = tr.order[(tr.rank[i] + k) % tr.n];
          const dq = tr.ds(i, c);
          if (dq < 0 || dq > 60) break;
          if (tr.away[c]) continue;
          const lo = this.spanLo(c) - tr.hw[c], hi = this.spanHi(c) + tr.hw[c];
          if (hi <= -hwI - LANE_CLR || lo >= hwI + LANE_CLR) continue;
          if (tr.v[c] < v - 0.3 || tr.pace[c] > tr.pace[i] / CLEARLY_FASTER || tr.off[c]) q = c;
          break;
        }
        if (q >= 0) { this.passTarget = q; this.passTimer = 0; }
        else { this.passPhase = 2; this.passTarget = -1; }
        return;
      }
      // the pass lane must stay free ahead (j excluded: beside it the corridor and its making room keep us apart)
      if (this.planTimer <= 0) {
        this.planTimer = PLAN_EVERY;
        const e = this.passE;
        if (this.laneBlock(e - hwI - LANE_CLR, e + hwI + LANE_CLR, 2.5, Math.max(v, tr.v[j] + 0.5 * this.planAdv), 120, 10, j, e) < 1) {
          const alt = this.planLane(j, v, pf, e);
          if (!Number.isNaN(alt)) this.passE = alt;
          else { this.passEnd = 'blocked'; this.passCool = 1.5; this.passPhase = 2; this.passTarget = -1; }
        }
      }
      return;
    }
    if (this.passPhase === 2) {
      // back to the racing line once its lane is free around me (or straight away under a flag)
      const lo = Math.min(0, eMe) - hwI - LANE_CLR, hi = Math.max(0, eMe) + hwI + LANE_CLR;
      // (cars behind / alongside in it must not reach me; a car ahead in it is simply followed once I am back)
      if (!green || this.offTrack || this.mishap !== null || this.laneBlock(lo, hi, 1.5, v, tr.front[i] + 7 + 0.2 * v, 60, -1) > 1.5) this.passPhase = 3;
      return;
    }
    // 3: merging
    if (Math.abs(eMe) < 0.4 || this.offTrack || this.mishap !== null) { this.passPhase = 0; this.passE = NaN; }
  }
}

/**
 * Speed factor for a line offset e (m, lane coordinate) from the racing line at s: on the inside of a corner its
 * tighter radius (v ∝ √R: R_offset / R_line = 1 − e · curvature), and 1.2 % per m off the line (in a pass lane only
 * in corners, |curvature| > 1/170 m; otherwise anywhere, the original rule that solo laps are calibrated with).
 */
export function laneFactor(line: RaceLine, e: number, s: number, lane: boolean): number {
  const k = line.at(line.curv, s);
  let f = Math.max(0.9, 1 - 0.012 * Math.abs(e) * (lane ? Math.min(1, Math.abs(k) * 170) : 1));
  const ks = k * e;
  if (ks > 0) f = Math.min(f, Math.sqrt(Math.max(0.5, 1 - ks)));
  return f;
}
