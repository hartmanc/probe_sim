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

import { atan as datan, atan2 as datan2, cos as dcos, hypot as dhypot, sin as dsin } from '../dmath';   // the AI computes like the physics: the same bits on every host and engine
import type { DriverInput } from '../types';
import type { Vehicle } from '../vehicle';
import type { CarSpec } from '../spec';
import type { RaceLine } from './line';
import { accAt, bankedG, coastDecel, loadFactor, type CarPerf } from './field';
import type { Traffic } from './traffic';
import { Rng } from './rng';
import { knobs as oKnobs, PlanWork, plan as planOffset, FOLLOW_CLR as FOLLOW_CLR_O, PLAN_EVERY as O_EVERY, PLAN_AHEAD, PLAN_BEHIND, NB_MAX, PLAN_DT, PLAN_N, BIG, MOVE_EPS, MIN_HOLD, type Planner, type PlanEnv } from './planner';

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
  /** Racing time headway x this (per track, RaceConfig.followScale; 1 = the tuned Laguna values). */
  followScale: number;
  /** Lateral grip share a pass lane's own path speed is held to, x CORNER_MARGIN (per track, RaceConfig.laneMargin; 1 = Laguna). */
  laneMargin: number;
  /** Lane changes held within the spare lateral grip, x this (per track, RaceConfig.shiftGrip; 0 = off, Laguna). */
  shiftGrip: number;
  /** Close racing within 3 % (traffic round E, RaceConfig.closeRacing): one decisive covering move instead of the light DEFEND. */
  closeRacing: boolean;
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
/** Black-flag hook (traffic round): the pass commit weighs a risk term (passRisk: 0 today); a lane whose risk exceeds
 *  PASS_RISK_MAX is not taken and RISK_W x risk comes off its score. The AI black-flag round plugs the expected flag cost in. */
const PASS_RISK_MAX = 1, RISK_W = 4;
const STUCK_T = [3.0, 1.8, 1.0];
const PASS_ADV = [1.06, 1.04, 1.025];      // own target speed vs theirs needed to pass at once
const DEFEND = [0.5, 0.8, 1.1];            // m of lateral move to cover the inside (light, by aggression)
/** Target lap ratio below which a car is "clearly faster" (it goes for the pass; the car ahead does not defend). */
export const CLEARLY_FASTER = 0.97;
/** How a driver whose pace hint is `mine` classes a car whose hint is `theirs` (s per lap): 'faster' (clearly: it is let by,
 *  never defended), 'close' (within 3 % either way: raced), 'slower' (clearly). */
export function paceClass(mine: number, theirs: number): 'faster' | 'close' | 'slower' {
  return theirs < CLEARLY_FASTER * mine ? 'faster' : mine < CLEARLY_FASTER * theirs ? 'slower' : 'close';
}
/** Loss-of-control factor by aggression tier (calm, normal, aggressive). */
export const MISHAP_AGGRESSION = [0.6, 1, 1.5];
/** Share of mishaps that are run-wide (the rest are spins). */
const MISHAP_WIDE = 0.7;
/** Run-wide slow phase: hold = HOLD0 + HOLDK x drawn loss (3-8 s), fitted with tools/race/selfplay.ts. */
const MISHAP_HOLD0 = -2.5, MISHAP_HOLDK = 1.4;
const CORNER_MARGIN = 0.97, BRAKE_MARGIN = 0.85;    // driverProfile: share of the lateral grip / braking used (0.95 / 0.8 until 18 Oct 2026)
/** The grip limiter lifts only when the commanded path needs more than this multiple of the (banked) lateral grip (1 until
 *  18 Oct 2026: at 1 it braked mid-corner for the pursuit's own correction curvature, ~1.5 s a lap on the Probe). */
const GRIP_LIMIT = 1.5;
/** Front slip angle (x the tyre's peak) above which an understeering car stops adding lock and unwinds it. */
const STEER_PLOUGH = 2;
const REAR_SLIP0 = 0.08, REAR_SLIPK = 6; // rad, 1/rad: ease the brake when the rear slides
/** A cone cap ahead (RaceLine.capL) bounds the lateral target within CAP_LOOK m by an approach at CAP_ACC m/s² laterally. */
const CAP_LOOK = 100, CAP_ACC = 3;
/** A slide (AI robustness round, 26 Oct 2026): the rear's slip angle past SLIDE_REAR x the tyre's peak and over the front's
 *  by half a peak, the yaw rate over the travel direction's turn rate by SLIDE_DIV rad/s. Then: brake at most SLIDE_BRAKE,
 *  a driven rear at most SLIDE_THR throttle (a front-drive car at least SLIDE_THR), the fronts not steered into the
 *  rotation past their direction of travel. */
const SLIDE_REAR = 1.5, SLIDE_BRAKE = 0.1, SLIDE_THR = 0.15;
const SLIDE_DIV = 0.15;
// lane model (NOTES "Racecraft (the lane model) and mishaps")
const LANE_CLR = 0.3;      // m each side of a car's span in lane-occupancy checks (adjacent lanes leave >= 0.6 m)
const FOLLOW_CLR = 0.4;    // m edge to edge: a car ahead closer than this laterally is in my lane and followed
const ALONG_CLR = 0.7;     // m corridor margin beside a car alongside (0.45 until 18 Oct 2026: on the painted-road widths
                           // yawed cars side by side at 0.1-0.4 m touched in T3, T9 and T10)
const GIVE_CLR = 0.2;      // m of that margin eaten before the car further back gives way
const PLAN_EVERY = 0.2;    // s between pass plans / lane checks
const PLAN_T = 10;         // s plan horizon for the occupancy projection
const PLAN_T_MAX = 40;     // s: a pass that would take longer than this is not started
const MIN_ADV = 0.2;       // m/s mean speed advantage in the pass lane needed to start
const PINCH_OK = 0.7;       // alongside = centres closer than 0.7 x (my front + its rear): where the lanes pinch, it makes room
/** s of look-ahead for a lane the road shuts beside a car (pinch guard, pass rule). 3 s (24 Oct 2026) took Sonoma's
 *  contacts to 0.016 per car-lap but failed ai_behaviour's full-field pass completion (51 %, > 58 %) and its within-3 %
 *  defending case: kept at 2 s */
const PINCH_T = 2;
/** m: the most a pass plan looks ahead for a lane the road shuts (shutBeside, the whole pass up to here) */
const PLAN_SHUT_MAX = 150;
const DROP_BACK = 30;      // m: abort a pass when I have fallen this far behind the car
const PASS_HEADWAY = 0.3;  // s: following the car I am passing (held in behind it where the lanes pinch), any aggression
const PASS_T_MAX = 30;     // s: give up a pass after this long
const PASS_SHIFT = 1.3;    // lane changes for a pass: x the shift rate
const PASS_EDGE = 0.5;     // m from the track edge (car side) a pass lane is clamped to
/** m ahead in which a car in the racing lane delays the merge back (it was front + 7 m + 0.2 s: merging at 9-14 m/s
 *  closing onto a slower car 20 m ahead rear-ended it; the 1.5 s occupancy projection decides within this range) */
const MERGE_AHEAD = 60;
/** m/s: (C2 H1) a car whose lateral drift is below this (and whose target is where it is) holds its line */
const STILL_VE = 0.3;
const SHIFT_RATE = 2.2;                    // m/s lateral change of the target offset
/** Lane changes within the spare lateral grip (per track, `ctl.shiftGrip`, 20 Oct 2026): the shift rate is capped at
 *  shiftGrip x a_spare x Ld / v (pure pursuit turns a shift rate r into ~ r / (v Ld) of path curvature on top of the
 *  line's), never below SHIFT_RATE_MIN. A room-making or corridor push at 2 x SHIFT_RATE through Sonoma's esses asked
 *  3-5 x the line's curvature, the grip limiter braked with the rear sliding and the car spun. */
const SHIFT_RATE_MIN = 0.8;
const KR = 0.25, LD0 = 3, LDK = 0.25;
/** No-passing corners by track id and corner id (track.json `turn`; noPassZone). Laguna Seca's Corkscrew (T8, merged with
 *  T8A) only: keyed to the track, not to a corner's name (issue #19: every track's T8 was treated as the Corkscrew). */
export const NO_PASS_CORNERS: Readonly<Record<string, readonly string[]>> = { laguna_seca: ['T8'] };

/**
 * The driver's own copy of the car's speed profile (field.ts buildSpeedProfile = the car's full grip):
 * corner speeds at CORNER_MARGIN of the lateral grip and braking at BRAKE_MARGIN of the car's braking
 * (combined with cornering on the friction ellipse), so the car stays on its line at the limit.
 */
export function driverProfile(line: RaceLine, perf: CarPerf, prof: Float64Array): Float64Array {
  const N = line.N, curv = line.curv, grade = line.grade, ds = line.ds;
  const out = Float64Array.from(prof);
  const alat = CORNER_MARGIN * perf.alat;
  for (let i = 0; i < N; i++) {
    const k = Math.max(1e-5, Math.abs(curv[i]));
    let v = out[i];
    for (let it = 0; it < 4; it++) v = Math.min(out[i], Math.sqrt(bankedG(alat, line, i, v) * G / k));
    out[i] = v;
  }
  for (let k = 2 * N; k > 0; k--) {
    const j = k % N, i = (j - 1 + N) % N, v = out[j];
    const u = Math.min(1, (v * v * Math.abs(curv[j])) / (bankedG(perf.alat, line, j, v) * G));
    const d = BRAKE_MARGIN * perf.abrake * G * loadFactor(line, j, v) * Math.sqrt(Math.max(0, 1 - u * u)) + G * grade[i];
    const vp = Math.sqrt(Math.max(0, v * v + 2 * Math.max(0.5, d) * ds[i]));
    if (vp < out[i]) out[i] = vp;
  }
  return out;
}

export class AiDriver {
  /** (tools) when set, planLane tallies why candidate lanes were rejected (selfplay_trace.ts --loss) */
  static planWhy: Record<string, number> | null = null;
  /** (tools) called after every offset plan with the car index, the plan's work and the target before it (C2 diagnosis) */
  static planHook: ((i: number, w: PlanWork, prev: number) => void) | null = null;
  private static why(k: string): void { const W = AiDriver.planWhy; if (W) W[k] = (W[k] ?? 0) + 1; }
  readonly vehicle: Vehicle;
  readonly line: RaceLine;
  readonly perf: CarPerf;
  readonly params: AiDriverParams;
  readonly idx: number;
  readonly traffic: Traffic;
  /** Target speed profile per station (m/s), from buildSpeedProfile. */
  profile: Float64Array;
  readonly input: DriverInput = { steer: 0, throttle: 0, brake: 0, shiftUp: false, shiftDown: false };
  readonly ctl: DriverControl = { speedCap: Infinity, noPass: false, minGap: 0, followScale: 1, laneMargin: 1, shiftGrip: 0, closeRacing: false, paceFactor: 1, noise: true, mishapRate: 0 };
  readonly rng: Rng;

  // ---- state
  /** current station hint for the projector */
  hint = -1;
  /** lateral shift of the target offset from the racing line (m, + left), commanded and target */
  shift = 0;
  private shiftTarget = 0;
  private integ = 0;
  private brakeCap = 1; private thrCap = 1; private steerCap = 1;
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
  /** close racing (E): the corner I last covered (one move per corner) */
  private coverCorner = -1;
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
  /** (tools) an oversteer being caught on the last tick */
  sliding = false;
  /** pure-pursuit path curvature commanded on the last tick, 1/m */
  private kCmd = 0;
  // ---- C1, the offset planner (RaceConfig.planner 'offset'; planner.ts). The lane model's pass machinery is not used then.
  /** which planner this driver races with (selected at construction; the lane model is the default) */
  readonly planner: Planner;
  /** the offset planner's target offset e* (m from the racing line, + left; 0 = the line) */
  oStar = 0;
  /** (tools) the offset planner's last cost and plans made */
  oCost = 0; oPlans = 0; oMoves = 0;
  private oTimer = 0; private oMoveDir = 0; private oMoveApex = -1; private oHeld = 0;
  /** a car the plan could not keep clear of (every candidate broke a rule): I give way to it until the next plan (-1 none) */
  private oYield = -1;
  private readonly pw: PlanWork | null = null;
  private readonly penv: PlanEnv | null = null;
  private pS = 0; private pPf = 1; private pHw = 0;
  /** the vehicle's steering shaping (spec.steering): full lock at speed v = max(minSteer, maxSteer / (1 + (v/shapeV)²)), rad */
  private readonly lockMax: number; private readonly lockMin: number; private readonly lockV: number;

  constructor(vehicle: Vehicle, line: RaceLine, perf: CarPerf, spec: CarSpec, profile: Float64Array, params: AiDriverParams, idx: number, traffic: Traffic, planner: Planner = 'lanes') {
    this.vehicle = vehicle; this.line = line; this.perf = perf; this.profile = driverProfile(line, perf, profile);
    this.params = params; this.idx = idx; this.traffic = traffic;
    this.planner = planner;
    if (planner === 'offset') {
      this.pw = new PlanWork();
      // my side of the plan (s = m ahead of my station at the plan): race-line speed, lane factor, corridor (PASS_EDGE from
      // the edges as a pass lane is held, the racing line always in it)
      this.penv = {
        vRef: (x: number) => this.profAt(this.pS + x) * this.pPf,
        factor: (e: number, x: number) => laneFactor(this.line, e, this.pS + x, true),
        lo: (x: number) => this.roadLo(this.pS + x, this.pHw) + PASS_EDGE - 0.15,
        hi: (x: number) => this.roadHi(this.pS + x, this.pHw) - PASS_EDGE + 0.15,
        curv: (x: number) => this.line.at(this.line.curv, this.pS + x),
        risk: (e: number) => this.passRisk(-1, e, e > 0 ? 1 : -1),
      };
    }
    this.oTimer = (idx % 8) * O_EVERY / 8;
    this.rng = new Rng(params.seed);
    const np = NO_PASS_CORNERS[line.trackId] ?? [];
    this.corkscrew = line.corners.findIndex((c) => np.includes(c.turn));
    this.lockMax = (spec.steering.maxAngleDeg * Math.PI) / 180; this.lockMin = (spec.steering.minAngleDeg * Math.PI) / 180; this.lockV = spec.steering.shapingSpeed;
  }

  /** Forget transient state (after a reset onto the track). */
  resetState(): void {
    this.shift = 0; this.shiftTarget = 0; this.integ = 0; this.brakeCap = 1; this.thrCap = 1; this.steerCap = 1;
    this.passTarget = -1; this.passSide = 0; this.passTimer = 0; this.stuckTimer = 0;
    this.passE = Number.NaN; this.passPhase = 0; this.planTimer = 0;
    this.defendSide = 0; this.defendCorner = -1; this.defendTimer = 0; this.offTrack = false;
    this.coverCorner = -1;
    this.mishap = null; this.mPhase = 0; this.mT = 0; this.mCorner = -1; this.nextCorner = -1; this.onTimer = 0; this.offTimer = 0;
    this.stuckTime = 0; this.needsRecovery = false; this.hint = -1; this.kCmd = 0; this.passCool = 0; this.traffic.passing[this.idx] = -1;
    this.oStar = 0; this.oTimer = (this.idx % 8) * O_EVERY / 8; this.oMoveDir = 0; this.oMoveApex = -1; this.oYield = -1;
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
  /**
   * No passing through the Corkscrew (from 120 m before its braking point to 90 m past the apex): the line runs edge
   * to edge over a blind crest there, so a lane measured from it is not a usable path on the painted-road widths
   * (18 Oct 2026: pass lanes on the outside of T8 merged back wide at the T8A exit and left the road). A pass still
   * behind its car is given up there; the merge back waits for a free racing lane until the braking point (`before` 0).
   */
  private noPassZone(s: number, before = 120): boolean {
    const k = this.corkscrew;
    if (k < 0) return false;
    const c = this.line.corners[k];
    return this.ahead(s, c.brake) <= before && this.ahead(s, c.apex) >= -90;
  }
  private readonly corkscrew: number = -1;

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
    const yaw = datan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    let herr = yaw - line.headingAt(s);
    while (herr > Math.PI) herr -= 2 * Math.PI;
    while (herr < -Math.PI) herr += 2 * Math.PI;
    let wheelsOff = 0;
    for (let k = 0; k < 4; k++) if (!st.wheels[k].onTrack) wheelsOff++;
    const edgeL = line.at(line.halfL, s), edgeR = line.at(line.halfR, s);
    // off the road = off the pavement: a cone cap (restrictLeft) is a lane boundary, not the road's edge, and counting the
    // cap as the edge dropped the lane clamp right at it (AI robustness round, 26 Oct 2026)
    const outside = lat > line.at(line.halfLRoad, s) + 0.3 || lat < -edgeR - 0.3;
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
    const offset = this.pw !== null;
    // (the offset planner: an offset it holds is a lane of its own, as a pass lane)
    const offline = this.shift === 0 ? 1 : laneFactor(line, this.shift, sp, offset ? this.oStar !== 0 : this.passPhase !== 0);
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
    // (in a pass lane: the lane's own curvature, not the transient of a lane change, plus a small allowance; merging back
    // onto the line the full commanded curvature: corner-exit merges carried cars off at the Corkscrew)
    let kG = Math.abs(this.kCmd);
    if (offset ? this.oStar !== 0 : this.passPhase === 1 || this.passPhase === 2) { const kl = line.at(line.curv, sp); kG = Math.min(kG, Math.abs(kl) / Math.max(0.5, 1 - kl * this.shift) + 0.004); }
    if (kG > 2e-3) {
      const vk = Math.sqrt(GRIP_LIMIT * bankedG(perf.alat, line, Math.min(line.N - 1, Math.floor(line.wrap(sp) / line.spacing)), v) * G / kG);
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
    if (offset ? this.oStar !== 0 : this.passPhase !== 0) {
      const eL = offset ? this.oStar : this.passPhase === 3 ? 0 : this.passE;
      const b = 0.75 * BRAKE_MARGIN * perf.abrake * G, aG = ctl.laneMargin * CORNER_MARGIN * perf.alat * G;
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
    const headway = HEADWAY[this.params.aggression] * ctl.followScale;
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
        // (the offset planner: a car my body already overlaps along the track and clear of me laterally is beside me, not
        // ahead: overlap holds, the corridor and the plan keep us apart)
        if (offset && gap < 0) continue;
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
      // (C2 H4, the offset planner: a clearly slower car ahead is followed at PASS_HEADWAY, close enough to pass it)
      const press = offset && oKnobs.h4 && green && tr.pace[i] < CLEARLY_FASTER * tr.pace[leadJ];
      const gd = ctl.minGap > 0 ? Math.max(0.6 * ctl.minGap, 0.3 * ctl.minGap + 0.6 * v) : 1.5 + ((this.passPhase === 1 && leadJ === this.passTarget) || press ? PASS_HEADWAY : headway) * v;
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
    if (!offset && green && (this.passPhase === 0 || this.passPhase === 2) && leadJ >= 0 && !this.offTrack && this.mishap === null) {
      const j = leadJ, vj = Math.max(0, tr.v[j]);
      const myPot = this.profAt(tr.s[j]) * pf;
      const slower = tr.off[j] === 1 || myPot > PASS_ADV[this.params.aggression] * Math.max(1, vj) || tr.pace[j] > tr.pace[i] * 1.004;   // (my own hint, as the others read me: a capped car's achievable lap)
      if (leadGap < Math.max(ctl.minGap, 1.5 + headway * v) + 10 && slower) this.stuckTimer += dt; else this.stuckTimer = Math.max(0, this.stuckTimer - dt);
      const clearly = tr.pace[i] < CLEARLY_FASTER * tr.pace[j];
      // clearly faster; a car that is off / nearly stopped; or quicker on pace and stuck behind it (a car held up in a
      // train is not a reason: everybody behind it would pull out at once)
      const want = clearly || tr.off[j] === 1 || vj < 0.5 * myPot || (tr.pace[i] < tr.pace[j] && this.stuckTimer > STUCK_T[this.params.aggression]);
      if (want && this.passCool <= 0 && this.planTimer <= 0 && leadGap < Math.max(30, 0.9 * v) && !this.noPassZone(s)) {
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
    if (this.coverCorner >= 0 && this.ahead(s, cs[this.coverCorner].apex) < -100) this.coverCorner = -1;   // (E: that corner is behind me)
    if (green && this.passPhase === 0 && !this.offTrack && this.mishap === null) {
      if (this.defendSide !== 0) {
        this.defendTimer -= dt;
        if (this.defendTimer <= 0 || this.ahead(s, cs[this.defendCorner].apex) < 0) { this.defendSide = 0; this.defendCorner = -1; this.defendCool = 2; }
      } else if (this.defendCool <= 0) {
        for (let k = 1; k < n; k++) {
          const j = order[(tr.rank[i] - k + n) % n];
          const d = -tr.ds(i, j);
          if (d < 0 || d > Math.min(28, Math.max(10, v))) break;
          if (tr.away[j]) continue;
          // a car rejoining right behind me is passed over for the next one, unless it is clearly faster: then whoever
          // is behind it, covering the inside is a move against a clearly faster car (AI robustness round: seed 1's
          // full field defended against a within-3 % car 19 m back with a clearly faster one rejoining 5 m back)
          if (tr.off[j]) { if (tr.pace[j] < CLEARLY_FASTER * tr.pace[i]) break; continue; }
          const r = tr.pace[j] / tr.pace[i];
          if (r >= CLEARLY_FASTER && r <= 1 / CLEARLY_FASTER && d > myRear + tr.front[j] + 1) {
            const c = this.passableAhead(s, 120, 10);
            if (c >= 0 && ctl.closeRacing) {
              // close racing (E): ONE early move to the inside lane before the braking zone, then hold it to the apex; none
              // when I already have the inside, none twice for a corner, none into a passer's lane
              const dir = cs[c].dir, eC = dir * tr.laneW;
              const have = eMe * dir >= 0.5 * tr.laneW;
              if (!have && c !== this.coverCorner && !this.passerIn(Math.min(eC, eMe) - hwI - LANE_CLR, Math.max(eC, eMe) + hwI + LANE_CLR)) {
                this.defendSide = dir; this.defendCorner = c; this.defendTimer = 8; this.coverCorner = c;
              }
            } else if (c >= 0) { this.defendSide = cs[c].dir; this.defendCorner = c; this.defendTimer = 8; }
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
    else if (this.defendSide !== 0 && !offset) shiftWant = this.defendSide * (ctl.closeRacing ? tr.laneW : DEFEND[this.params.aggression]);
    if (offset) {
      // the offset planner: a plan every PLAN_EVERY s while another car is within its horizon; alone, the racing line
      this.oTimer -= dt; this.oHeld += dt;
      if (!green || this.offTrack || this.mishap !== null) { this.oStar = 0; this.oYield = -1; this.oMoveDir = 0; tr.oPass[i] = 0; }
      else if (this.oTimer <= 0) { this.oTimer += O_EVERY; if (this.oTimer < 0) this.oTimer = 0; this.planStep(v, eMe, pf, headway); }
      shiftWant = this.oStar;
      if (this.oYield >= 0) {
        // every candidate broke a rule against this car, right in front of me or beside me: the car further back gives way
        // (relative to it)
        const j = this.oYield, dj = tr.ds(i, j);
        if (dj > 0 && dj < myFront + tr.rear[j] + 10 && tr.v[j] > 4) { const vy = Math.max(3, tr.v[j] - 1.5); if (vy < vCmd) { vCmd = vy; this.limiter = 'yield'; aref = Math.min(aref, -0.3); } }
      }
    }
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
            // (the offset planner: a car alongside behind me and converging, in a corner only; no lift on a straight)
            if (offset && d < 0 && d > -(myRear + tr.front[j]) && Math.abs(line.at(line.curv, s)) * 170 > 1) passerSqueeze = true;
          }
        }
      }
    }
    // being passed: the lane of a car passing me (within 25 m behind, laterally clear of me) is reserved; I never drift
    // into it, also not while making room for another car passing me on the other side
    if (!offset) for (let k = 1; k < n; k++) {
      const j = order[(tr.rank[i] - k + n) % n];
      const d = -tr.ds(i, j);
      if (d < 0 || d > 25) break;
      if (tr.passing[j] !== i || tr.away[j]) continue;
      const need = hwI + tr.hw[j] + ALONG_CLR, ej = tr.eT[j];
      if (Math.abs(ej - eMe) < need - 0.3) continue;   // straight behind me in my lane: nothing reserved yet
      if (ej > eMe) corHiE = Math.min(corHiE, ej - need); else corLoE = Math.max(corLoE, ej + need);
    }
    // pinch guard: a car alongside in the next lane whose lane and mine (both clamped to the road) close up within
    // PINCH_T s (the racing line runs edge to edge, so lanes measured from it converge at turn-in, apex and exit): the car
    // whose centre is further back drops behind it; the one ahead holds its lane.
    // (In lane coordinates, as following: the absolute lateral offsets of two cars a few metres apart differ by the
    // line's sweep across the road between them, so in a corner a car one lane over read as "straight ahead" and was
    // left to following, which saw it in another lane: neither held the car back (24 Oct 2026, Sonoma T9A). Sampled
    // every 5 m: an apex shuts a lane over 10-15 m only, which 10 m steps could step over.)
    // (the offset planner: none; its clearance over the horizon, with the road clamping every car, and the yield instead)
    if (!offset) for (let k = 1; k < n; k++) {
      const j = order[(tr.rank[i] + k) % n];
      const d = tr.ds(i, j);
      if (d < 0 || d > myFront + tr.rear[j] + 4 + 1.5 * Math.max(0, v - tr.v[j])) break;
      if (tr.away[j] || tr.v[j] < 4) continue;                          // a (nearly) stopped car: following / planning handle it
      if (Math.abs(eMe - tr.e[j]) < hwI + tr.hw[j] - 0.2) continue;     // straight ahead: following handles it
      // alongside on a pass: it makes room (passStep gives the pass up first where the road shuts my lane beside it)
      if (j === this.passTarget && d < PINCH_OK * (myFront + tr.rear[j])) continue;
      const need = hwI + tr.hw[j] + 0.3 + this.yawClr(s + 0.5 * v), ej = tr.eT[j], hwJ = tr.hw[j];
      const ePlan = this.passPhase === 1 || this.passPhase === 2 ? this.passE : this.passPhase === 3 ? 0 : this.shiftTarget;
      const dist = Math.max(12, PINCH_T * v);
      for (let x = 0; x <= dist; x += 5) {
        const sx = s + x;
        const me = Math.max(this.roadLo(sx, hwI), Math.min(this.roadHi(sx, hwI), ePlan));
        const it = Math.max(this.roadLo(sx, hwJ), Math.min(this.roadHi(sx, hwJ), ej));
        if (Math.abs(me - it) < need && (me - it) * (eMe - tr.e[j]) >= 0) {
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
      const mg = (offset ? this.oStar !== 0 : this.passPhase !== 0) ? PASS_EDGE : 0.15;   // a pass lane keeps a little more room to the edge
      const lo = -line.at(line.halfR, sLook) + hwI + mg - lineLook;
      let hi = line.at(line.halfL, sLook) - hwI - mg - lineLook;
      // a cone cap ahead (RaceLine.capL: a hard lane boundary) is approached with bounded lateral acceleration: the shift
      // (held relative to the line, so it travels with the line's sweep) stays under the cap's lane-coordinate limit x m
      // further on plus what CAP_ACC brings back in the time to get there, so a pass lane or a room-making shift beside a
      // cap that closes (the racing line sweeping toward it) eases off before it, instead of carrying the car's lateral
      // speed into it (26 Oct 2026, Laguna's front straight: the line sweeps 4.8 m left toward the pit-exit cones)
      for (let x = 0; x <= CAP_LOOK; x += 5) {
        const sx = sLook + x;
        if (!line.capL[Math.min(line.N - 1, Math.floor(line.wrap(sx) / line.spacing))]) continue;
        const t = x / Math.max(5, v);
        hi = Math.min(hi, line.at(line.halfL, sx) - hwI - mg - line.at(line.off, sx) + 0.5 * CAP_ACC * t * t);
      }
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
      // (the offset planner: only when squeezed; a car alongside holds its side and the exit decides)
      if (!offset && behindHi && Math.max(lat, latP) > corHi + GIVE_CLR) giveWay = true;
      if (!offset && behindLo && Math.min(lat, latP) < corLo - GIVE_CLR) giveWay = true;
      const vGive = Math.max(3, (behindHi ? corHiV : corLoV) - 1.5); // relative to it: never a runaway lift
      if (giveWay && vGive < vCmd) { vCmd = vGive; this.limiter = 'alongside'; aref = Math.min(aref, -0.3); }

      this.shiftTarget = tgt;
      tr.eT[i] = tgt;
      let rate = (push !== 0 || !Number.isNaN(mishapLat) ? 2 * SHIFT_RATE : this.offTrack ? 0.8 * SHIFT_RATE : (offset ? this.oStar !== 0 : this.passPhase !== 0) ? PASS_SHIFT * SHIFT_RATE : SHIFT_RATE) * dt;
      if (ctl.shiftGrip > 0 && Number.isNaN(mishapLat) && !this.offTrack) {
        // within the spare lateral grip at the look point (a mishap or a rejoin keeps its own rate)
        const kl = Math.abs(line.at(line.curv, sLook)), aSp = Math.max(0.25 * perf.alat * G, perf.alat * G - v * v * kl);
        rate = Math.min(rate, Math.max(SHIFT_RATE_MIN, ctl.shiftGrip * aSp * (LD0 + LDK * v) / Math.max(5, v)) * dt);
      }
      const dsh = this.shiftTarget - this.shift;
      this.shift += dsh > rate ? rate : dsh < -rate ? -rate : dsh;
      // the line sweeps across the road faster than the shift may change: never let a held shift carry the car off
      if (!this.offTrack && Number.isNaN(mishapLat)) this.shift = Math.max(lo, Math.min(hi, this.shift));
    }

    // ---- a slide: the rear past SLIDE_REAR x the tyre's peak slip and over the front's by half a peak, while the car
    // rotates faster than its direction of travel turns (yaw rate minus lateral acceleration / speed, same sign as the
    // yaw rate, over SLIDE_DIV): an oversteer that is growing, not a car drifting steadily at the limit
    let sliding = false;
    {
      const fpk = perf.peakSlipAngle, r = st.angVel[2];
      const rsS = Math.max(Math.abs(st.wheels[2].slipAngle), Math.abs(st.wheels[3].slipAngle));
      let fsS = 0;
      for (let k = 0; k < 2; k++) { const w = st.wheels[k]; if (w.load > 1000) fsS = Math.max(fsS, Math.abs(w.slipAngle)); }
      const excess = r - (st.gLat * G) / Math.max(5, v);
      sliding = v > 6 && this.mishap === null && rsS > SLIDE_REAR * fpk && rsS > fsS + 0.5 * fpk && excess * r > 0 && Math.abs(excess) > SLIDE_DIV;
    }
    this.sliding = sliding;

    // ---- steering: pure pursuit from the rear axle
    {
      const cy = dcos(yaw), sy = dsin(yaw);
      const rx = st.pos[0] - cy * L / 2, ry = st.pos[1] - sy * L / 2;
      const Ld = LD0 + LDK * v;
      const sT = s - L / 2 + Ld;
      line.pointAt(sT, line.at(line.off, sT) + this.shift, this.pt);
      const dx = this.pt[0] - rx, dy = this.pt[1] - ry;
      const alpha = datan2(-sy * dx + cy * dy, cy * dx + sy * dy);
      const dist = Math.max(1, dhypot(dx, dy));
      const kappa = 2 * dsin(alpha) / dist;
      this.kCmd = kappa;
      let delta = datan(L * kappa) + KR * (v * kappa - st.angVel[2]);
      delta += perf.kUs * Math.max(-1.3, Math.min(1.3, (v * v * kappa) / G));
      let sc = Math.max(-1, Math.min(1, delta / perf.maxSteer));
      // front axle sliding past its peak (understeer, at speed): hold / unwind the lock. More lock only pushes the front
      // wider, then bites all at once as the car slows and throws it back across the road (19 Oct 2026: making room or
      // changing lanes at turn-in, cars ploughed 4-7 m wide at full lock and snapped back into the car alongside)
      {
        let fs = 0;
        for (let k = 0; k < 2; k++) { const w = st.wheels[k]; if (w.load > 1000) fs = Math.max(fs, Math.abs(w.slipAngle)); }
        const rs = Math.max(Math.abs(st.wheels[2].slipAngle), Math.abs(st.wheels[3].slipAngle)), fp = perf.peakSlipAngle;
        const plough = fs > STEER_PLOUGH * fp && fs > rs + 0.5 * fp && v > 10 && !this.offTrack;
        this.steerCap = plough ? Math.max(0.1, Math.min(this.steerCap, Math.abs(this.input.steer)) - 2 * dt) : Math.min(1, this.steerCap + 2 * dt);
        sc = Math.max(-this.steerCap, Math.min(this.steerCap, sc));
      }
      // a slide (above): the front wheels never point further into the rotation than the front axle's direction of travel
      // (road angle + ISO slip angle), so the fronts never push the nose further round. Pure pursuit aims the car's nose;
      // in a slide the nose and the direction of travel part, and it steered further into the rotation (26 Oct 2026,
      // Laguna: full lock into a slide on the front straight, the car spun into the pit-exit lane)
      {
        const w0 = st.wheels[0], w1 = st.wheels[1];
        if (sliding && v > 8 && w0.load > 1000 && w1.load > 1000 && w0.paved && w1.paved) {   // (off the pavement the tyre's peak moves out)
          const course = 0.5 * (w0.steer + w0.slipAngle + w1.steer + w1.slipAngle);
          const vr = v / this.lockV, lock = Math.max(this.lockMin, this.lockMax / (1 + vr * vr));
          const edge = course / lock;
          if (st.angVel[2] > 0) sc = Math.max(-1, Math.min(sc, edge)); else sc = Math.min(1, Math.max(sc, edge));
        }
      }
      this.input.steer = sc;
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
      const kpk = perf.peakSlipRatio;
      for (let k = perf.drivenFront ? 0 : 2; k < (perf.drivenRear ? 4 : 2); k++) { const w = st.wheels[k]; if (w.load > 1000 && w.slipRatio > spin) spin = w.slipRatio; }
      this.brakeCap = lock > 1.5 * kpk ? Math.max(0.25, Math.min(this.brakeCap, brake) - 3 * dt) : Math.min(1, this.brakeCap + 3 * dt);
      this.thrCap = spin > 1.5 * kpk ? Math.max(0.2, Math.min(this.thrCap, throttle) - 3 * dt) : Math.min(1, this.thrCap + 3 * dt);
      // rear stepping out on a trailing brake: ease off the brake (a driver's feel for entry oversteer)
      const rs = Math.max(Math.abs(st.wheels[2].slipAngle), Math.abs(st.wheels[3].slipAngle));
      if (rs > REAR_SLIP0 && (this.limiter === 'profile' || this.limiter === 'grip')) brake *= Math.max(0.1, 1 - REAR_SLIPK * (rs - REAR_SLIP0));
      brake = Math.min(brake, this.brakeCap);
      throttle = Math.min(throttle, this.thrCap);
      // a slide (an oversteer growing, above): catch it, never feed it. The brake (any limiter: the grip limiter brakes for
      // the pursuit's curvature, which in a slide is the rotation, not the path) comes off, since braking loads the front
      // and unloads the rear; a driven rear gets no more than a maintenance throttle; a front-drive car keeps a little
      // drive (it pulls the nose straight, a lift would add to the rotation). Steering: above. (AI robustness round, 26 Oct
      // 2026: braking at 0.25-0.5 with the rear at 0.3-0.7 rad spun cars in Laguna's T4, T6 and T10)
      if (sliding) {
        if (this.limiter !== 'follow') brake = Math.min(brake, SLIDE_BRAKE);   // (stopping behind a car ahead comes first)
        throttle = perf.drivenRear ? Math.min(throttle, SLIDE_THR) : Math.max(SLIDE_THR, Math.min(0.6, throttle));
      }
      // rear-drive car sliding while the engine brakes the rear wheels: a little throttle to stop the engine braking
      // (a driver's blip; 18 Oct 2026: light, powerful RWD cars spun off the T3 exit on a closed throttle)
      if (perf.drivenRear && rs > REAR_SLIP0 && brake < 0.3) {
        const lr = Math.min(st.wheels[2].slipRatio, st.wheels[3].slipRatio);
        if (lr < -0.5 * kpk) throttle = Math.max(throttle, Math.min(0.2, 4 * (-lr - 0.5 * kpk)));
      }
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

  /**
   * A pass lane that the road shuts beside the car being passed before I am ahead of it (NOTES "24 Oct 2026: a pass
   * needs its lane through the corner"). The racing line runs to the inside edge at an apex (and to the outside edge at
   * the track-out), so a lane measured from it on that side is clamped onto the line there; the car being passed cannot
   * make 2-3 m of room at the limit in the corner (its lane changes are rate-limited), and a passer still beside it is
   * squeezed into it. Looks at the first station ahead where my lane e on `side` of car j (+1 its left) and j's lane,
   * both clamped to the road, come closer than the pinch guard's clearance; r = where I am relative to j when I get
   * there at the closing speed dv. True when r is not ahead of j by PINCH_OK car lengths (ahead, j is the car further
   * back and drops behind me) and, in a pass in hand, not still behind it (then following and the pinch guard keep me
   * behind; with `plan`, starting a pass, that is a reason not to start: a lane that will be shut before I am ahead is
   * no lane). Uses only the line, the road edges and the two cars: no track-specific data.
   * Horizon: a pass in hand looks max(12 m, PINCH_T s) ahead (the pinch guard's look-ahead); planning (`plan`) looks
   * `look` m (planLane: my speed x the occupancy horizon Tn = min(PLAN_T, D / adv), so a pass longer than PLAN_T = 10 s
   * is checked over its first 10 s only), never less than the pass-in-hand look-ahead, at most PLAN_SHUT_MAX m.
   * Lanes: mine is clamped as a pass lane is held (laneAt: PASS_EDGE from the edge, as the lateral target in a pass),
   * j's as a car off a pass is held (the 0.15 m road margin): each where that car will actually be.
   * dv is floored at 0: a passer falling back is projected where it is now (still beside it), not further back, so a
   * pass that is losing ground is given up rather than kept on the hope of being behind by the shut.
   */
  private shutBeside(j: number, e: number, side: number, v: number, dv: number, look = 0, plan = false): boolean {
    const tr = this.traffic, i = this.idx, s = tr.s[i], hwI = tr.hw[i], hwJ = tr.hw[j];
    if (tr.v[j] < 4 || tr.off[j]) return false;           // a stopped / off car: planning and following handle it
    const len = tr.front[i] + tr.rear[j], d = tr.ds(i, j);
    if (d < -PINCH_OK * len) return false;                // already ahead of it
    const need = hwI + hwJ + 0.3 + this.yawClr(s + 0.5 * v);
    const dist = plan ? Math.min(PLAN_SHUT_MAX, Math.max(12, PINCH_T * v, look)) : Math.max(12, PINCH_T * v);
    for (let x = 0; x <= dist; x += 5) {
      const sx = s + x;
      const me = this.laneAt(sx, e, hwI);
      const it = Math.max(this.roadLo(sx, hwJ), Math.min(this.roadHi(sx, hwJ), tr.eT[j]));
      if (side * (me - it) < need) {
        const r = d - Math.max(0, dv) * x / Math.max(1, v);   // where I am relative to it when I get there
        return r > -PINCH_OK * len && (plan || r < len + 1);
      }
    }
    return false;
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
        if (this.passerIn(Math.min(e, eMe) - hwI - LANE_CLR, Math.max(e, eMe) + hwI + LANE_CLR)) { AiDriver.why('passer'); continue; }
        // the band I sweep through on the way there must be free now (j: following keeps me behind it)
        if (Math.abs(e - eMe) > W * 0.5 && this.laneBlock(Math.min(e, eMe) - hwI - LANE_CLR, Math.max(e, eMe) + hwI + LANE_CLR, 1.5, v, 40, 40, j) < 1.5) { AiDriver.why('band'); continue; }
        let onRoad = true;
        for (let d = 0; d <= 30; d += 15) if (e < this.roadLo(s + d, hwI) - 0.3 || e > this.roadHi(s + d, hwI) + 0.3) { onRoad = false; break; }
        if (!onRoad) { AiDriver.why('road'); continue; }
        const adv = this.laneSpeed(e, s, pf, 100) - vJ;
        if (adv < MIN_ADV) { AiDriver.why('adv'); continue; }
        const Tn = Math.min(PLAN_T, D / adv);
        if (D / adv > PLAN_T_MAX) { AiDriver.why('long'); continue; }
        // no lane beside j where the road shuts it before I would be ahead of it: looked at over the occupancy horizon
        // Tn at my speed (the whole pass when it takes up to PLAN_T s; its first PLAN_T s otherwise), at most
        // PLAN_SHUT_MAX m, closing at the planned advantage or the speed difference now if larger. (Checking passes
        // longer than PLAN_T to their end, 24 Oct 2026: Sonoma contacts 0.022 -> 0.031, Laguna 0.033 -> 0.038 over
        // 8 seeds, 6 % fewer green passes on Sonoma: not kept.)
        if (this.shutBeside(j, e, side, v, Math.max(adv, v - vj), v * Tn, true)) { AiDriver.why('shut'); continue; }
        // (projected at the speed I plan to pass at: a slower car further up that lane blocks it)
        const tFree = this.laneBlock(e - hwI - LANE_CLR, e + hwI + LANE_CLR, Tn + 2, Math.max(v, vJ + adv), 150, 60, j, e, true);
        if (tFree < Tn + 0.5) { AiDriver.why('occupied'); continue; }
        const risk = this.passRisk(j, e, side);
        if (risk > PASS_RISK_MAX) { AiDriver.why('risk'); continue; }
        AiDriver.why('ok');
        const score = Math.min(12, tFree) + (inside !== 0 && side === inside ? 3 : 0) - m - 0.2 * Tn - RISK_W * risk;
        if (score > bestScore) { bestScore = score; best = e; this.planAdv = adv; }
      }
    }
    return best;
  }

  /**
   * The risk of committing to a pass on car j in lane e on `side` (traffic round; the hook for the AI black-flag round: an
   * expected flag cost, e.g. from the contact-at-fault and four-off odds of this lane at this closing speed, against the time a
   * pass gains). 0 today: the pass is held to the same corridor, alongside and pinch margins as before.
   */
  private passRisk(_j: number, _e: number, _side: number): number { return 0; }

  /**
   * C1, the offset planner (planner.ts): the neighbours (the NB_MAX nearest within PLAN_AHEAD m ahead and PLAN_BEHIND m
   * behind, by distance, ties by car index), each projected over the horizon as the lane model projects an occupant
   * (laneBlock: its span e / eT / drift clamped to the road where it will be, ± its half width, + 0.8 m when off; planLane:
   * its speed from its own profile scaled by how held up it is now; a car without a profile, the human player, at its speed
   * now), then one plan. Alone (no neighbour): the racing line, nothing evaluated.
   */
  private planStep(v: number, eMe: number, pf: number, headway: number): void {
    const tr = this.traffic, i = this.idx, n = tr.n, line = this.line, w = this.pw!, s = tr.s[i], hwI = tr.hw[i];
    const A = this.nbA, B = this.nbB, AD = this.nbAD, BD = this.nbBD;
    let na = 0, nb = 0;
    for (let k = 1; k < n && na < NB_MAX; k++) {
      const q = tr.order[(tr.rank[i] + k) % n];
      const d = tr.ds(i, q);
      if (d < 0 || d > PLAN_AHEAD) break;
      if (tr.away[q]) continue;
      A[na] = q; AD[na++] = d;
    }
    let cf = -1;
    for (let k = 1; k < n && nb < NB_MAX; k++) {
      const q = tr.order[(tr.rank[i] - k + n) % n];
      const d = -tr.ds(i, q);
      if (d < 0 || d > PLAN_BEHIND) break;
      if (tr.away[q]) continue;
      if (cf < 0 && !tr.off[q]) cf = q;
      B[nb] = q; BD[nb++] = d;
    }
    if (na + nb === 0) { this.oStar = 0; this.oYield = -1; this.oMoveDir = 0; tr.oPass[i] = 0; return; }
    // merge by distance (ties: the lower car index)
    let a = 0, b = 0, nN = 0;
    const S = PLAN_N + 1;
    while (nN < NB_MAX && (a < na || b < nb)) {
      const takeA = b >= nb || (a < na && (AD[a] < BD[b] || (AD[a] === BD[b] && A[a] < B[b])));
      const q = takeA ? A[a] : B[b], rel0 = takeA ? AD[a++] : -BD[b++];
      const k = nN++;
      w.nIdx[k] = q; w.nFront[k] = tr.front[q]; w.nRear[k] = tr.rear[q]; w.nE[k] = tr.e[q]; w.nOff[k] = tr.off[q];
      // (C2 H1, predictability: the passer commits because the car ahead holds its line) a car on its line and not moving (its
      // target where it is, no lateral drift, not off, not itself passing) is projected as its line only: its half width, no
      // target span, no drift widening; a car moving, off or passing keeps the widened band
      const still = !tr.off[q] && !tr.oPass[q] && tr.passing[q] < 0 && Math.abs(tr.eT[q] - tr.e[q]) < MOVE_EPS && Math.abs(tr.ve[q]) < STILL_VE;
      const hq = tr.hw[q], ext = hq + (tr.off[q] ? 0.8 : 0), sLo = still ? tr.e[q] : this.spanLo(q), sHi = still ? tr.e[q] : this.spanHi(q);
      // speed: its own profile, scaled by how held up it is now (planLane); off or without a profile: its speed now
      const vq0 = Math.max(0, tr.v[q]), pq = tr.profile[q], useP = pq !== null && !tr.off[q];
      const ratio = useP ? Math.min(1, vq0 / Math.max(1, line.at(pq!, tr.s[q]))) : 1;
      let x = rel0, o = k * S;
      for (let m = 0; m <= PLAN_N; m++, o++) {
        if (m > 0) x += (useP ? line.at(pq!, s + x) * ratio : vq0) * PLAN_DT;
        const sx = s + x;
        const rLo = this.roadLo(sx, hq), rHi = this.roadHi(sx, hq);
        w.X[o] = x;
        w.LO[o] = Math.max(rLo, Math.min(rHi, sLo)) - ext;
        w.HI[o] = Math.max(rLo, Math.min(rHi, sHi)) + ext;
      }
      // lateral now: following me in my band (its job), or alongside (it owns its side)
      const o0 = k * S, sep = Math.max(w.LO[o0] - (eMe + hwI), (eMe - hwI) - w.HI[o0]);
      w.nIgnore[k] = rel0 < 0 && sep < FOLLOW_CLR_O ? 1 : 0;
      const over = rel0 < tr.front[i] + tr.rear[q] && rel0 > -(tr.rear[i] + tr.front[q]);
      w.nOwn[k] = over && sep >= 0 ? (tr.e[q] > eMe ? 1 : -1) : 0;
    }
    w.nN = nN;
    // me
    this.pS = s; this.pPf = pf; this.pHw = hwI;
    w.v = v; w.eCur = this.shift; w.eMeas = eMe; w.ePrev = this.oStar; w.rate = PASS_SHIFT * SHIFT_RATE;
    w.hw = hwI; w.front = tr.front[i]; w.rear = tr.rear[i]; w.headway = oKnobs.h4 && na > 0 && tr.pace[i] < CLEARLY_FASTER * tr.pace[A[0]] ? PASS_HEADWAY : headway; w.aggr = this.params.aggression;
    w.bMax = 0.85 * this.perf.abrake * G; w.aLat = this.perf.alat * G;
    w.ePref = this.defendSide !== 0 ? this.defendSide * (this.ctl.closeRacing ? tr.laneW : DEFEND[this.params.aggression]) : Number.NaN;
    // a clearly faster car (by its pace hint: the player's is his live estimate) within 25 m behind: hold, never toward it
    w.cfSide = 0;
    w.cfPassing = na > 0 && AD[0] < PLAN_BEHIND && !tr.off[A[0]] && tr.pace[i] < CLEARLY_FASTER * tr.pace[A[0]];
    if (cf >= 0 && tr.pace[cf] < CLEARLY_FASTER * tr.pace[i]) w.cfSide = Math.abs(tr.e[cf] - eMe) < hwI + tr.hw[cf] ? 2 : tr.e[cf] > eMe ? 1 : -1;
    // the no-pass window (Laguna's Corkscrew: 120 m before its braking point to 90 m past the apex)
    w.zoneLo = Number.NaN; w.zoneHi = Number.NaN;
    if (this.corkscrew >= 0) {
      const C = line.corners[this.corkscrew], hiZ = this.ahead(s, C.apex) + 90;
      if (hiZ >= 0) { w.zoneLo = this.ahead(s, C.brake) - 120; w.zoneHi = hiZ; }
    }
    const cs = line.corners;
    w.moveDir = this.oMoveDir; w.locked = this.oHeld < MIN_HOLD;
    // (one move per corner approach while racing a car: one within 20 m of me, ahead or behind)
    let near = false;
    for (let k = 0; k < nN; k++) { const r = w.X[k * S]; if (!w.nIgnore[k] && r < 20 + tr.front[i] && r > -(20 + tr.rear[i])) { near = true; break; } }
    w.moveOpen = near && this.oMoveApex >= 0 && this.ahead(s, cs[this.oMoveApex].apex) > 0;
    const prev = this.oStar;
    const e = planOffset(w, this.penv!);
    this.oCost = w.bestCost; this.oPlans = w.evaluated;
    if (AiDriver.planHook) AiDriver.planHook(i, w, prev);
    this.oYield = w.bestCost >= BIG && w.bestCulprit >= 0 ? w.nIdx[w.bestCulprit] : -1;
    if (Math.abs(e - prev) > MOVE_EPS) {
      // a new move: its direction, held to the apex of the next corner
      this.oMoveDir = e > prev ? 1 : -1; this.oMoveApex = -1; this.oMoves++; this.oHeld = 0;
      let best = Infinity;
      for (let k = 0; k < cs.length; k++) { const d = this.ahead(s, cs[k].apex); if (d > 0 && d < best) { best = d; this.oMoveApex = k; } }
    } else if (!w.moveOpen) this.oMoveDir = 0;
    this.oStar = e;
    tr.oPass[i] = Math.abs(e) > MOVE_EPS && na > 0 && AD[0] < 30 ? 1 : 0;
  }
  private readonly nbA = new Int32Array(NB_MAX); private readonly nbB = new Int32Array(NB_MAX);
  private readonly nbAD = new Float64Array(NB_MAX); private readonly nbBD = new Float64Array(NB_MAX);

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
      else if (this.noPassZone(tr.s[i]) && d > 0) end = 'corkscrew';   // still behind it: give it up, merge back
      // the road shuts my lane beside it before I am ahead: give it up and tuck in behind it (the pinch guard no longer
      // exempts it, so I drop back; the merge waits until its lane is free around me)
      else if (this.shutBeside(j, this.passE, this.passSide, v, v - tr.v[j])) end = 'shut';
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
      // (or the road has already put me back on the line, behind the car I gave up on: in its lane following it, which
      // blocks the lane check at following distance; waiting on, the lane comes back past the apex and steered me out
      // into it again: AI robustness round, ai_passing "drops back behind it and merges")
      if (!green || this.offTrack || this.mishap !== null || this.noPassZone(tr.s[i], 0) || Math.abs(eMe) < 0.4 || this.laneBlock(lo, hi, 1.5, v, MERGE_AHEAD, 60, -1) > 1.5) this.passPhase = 3;
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
