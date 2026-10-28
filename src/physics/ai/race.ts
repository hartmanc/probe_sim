// RaceDirector: builds the field (45 AI cars + the player), runs the formation, the seeded random
// green, the race and the flag; counts laps, keeps the running order and gaps, resolves car-vs-car
// contacts, and runs the player rule engine (black flags, Lemons escalation, stop-and-go in the pit
// lane). Deterministic: a race is reproducible from (seed, AI_VERSION) and the player's inputs.
//
// Per physics step (dt = 0.001 s): step(dt, playerInput). Per frame: hud(), poses().

import { atan2 as datan2, hypot as dhypot } from '../dmath';   // the AI computes like the physics: the same bits on every host and engine
import type { DriverInput, Surface, VehicleState } from '../types';
import type { PitLaneJson } from '../track';
import type { CollisionWorld } from '../collision';
import { Vehicle } from '../vehicle';
import { BlendLine, BlendLineWatch, BlendFlag, type BlendLineJson } from '../blendline';
import { loadCarSpec, type CarSpec } from '../spec';
import { CarCollider, type CarBody, type CarContactEvent } from '../cars';
import type { RaceLine } from './line';
import { AiDriver, type MishapKind } from './driver';
import { AI_VERSION, resolveCarType, aiCarJson, buildSpeedProfile, measureCarPerf, parseIdentity, drawPace, paceHint, fieldKey, modelKey, type CarPerf, type IdentityCar, type PaceCar, type PaceJson } from './field';
import { Traffic } from './traffic';
import { Rng, hashSeed } from './rng';

/** v * v: the same bits as v ** 2 in V8, without relying on any engine's pow. */
const sq = (v: number): number => v * v;

export type RacePhase = 'formation' | 'green' | 'yellow' | 'chequered' | 'finished';
export type RaceFlag = 'yellow' | 'green' | 'chequered' | 'black';

export interface RaceConfig {
  laps: number;
  seed: number;
  /** Must match AI_VERSION for exact reproduction; recorded in results. */
  ai_version: number;
  playerNumber: string;
  /** The green flag comes at a seeded random time in this window (s after the start of the formation). */
  greenWindow: [number, number];
  /** Formation / yellow rolling speed cap, m/s (≈ 50 % of race pace). */
  formationSpeed: number;
  /** Gap between cars on the grid and in formation, m (bumper to bumper). */
  gridGap: number;
  /** AI control rate: driver update every N physics steps (2 → 500 Hz at dt 1 ms). */
  aiControlEvery: number;
  /**
   * AI physics rate: each AI car integrates every N steps with N·dt (staggered by car, so half the field
   * steps on each tick). 2 = 500 Hz: solo laps match 1 kHz to 0.01 s and it halves the cost. The
   * player's car always steps every call. When > 1 the driver updates with the car's physics step.
   */
  aiPhysicsEvery: number;
  /** Attach the static collision world (walls, trees) to AI cars too. */
  aiWalls: boolean;
  /** Headless: the player's car is driven by an AI (tests, attract mode). */
  playerAi: boolean;
  /** Use only the first N AI cars by grid (tests). Default all. */
  maxAi: number;
  /**
   * Loss-of-control probability per AI car per corner passage during green, before the corner difficulty
   * (RaceLine.corners, mean 1) and aggression (calm 0.6, normal 1, aggressive 1.5) factors. Never the player.
   */
  mishapRate: number;
  /**
   * Racing time headway factor for every AI driver (per track: src/scoreboard/config.ts TRACKS[id].ai; 1 = Laguna,
   * where the headways were tuned).
   */
  followScale: number;
  /**
   * Pass-lane speed margin (per track, TRACKS[id].ai.laneMargin; 1 = Laguna): the lateral grip share a pass lane's own
   * path (clamped to the road) is driven at, x the driver's corner margin. Sonoma 0.85: inside pass lanes into T4 and
   * T11 collapse onto the line at the apex and the passer ran 1-2 m wide into the car making room.
   */
  laneMargin: number;
  /**
   * Lane changes within the spare lateral grip, x this (per track, TRACKS[id].ai.shiftGrip; 0 = off, Laguna). Sonoma 1:
   * room-making and pass lane changes at 2-4 m/s through the esses made the cars spin (driver.ts SHIFT_RATE_MIN).
   */
  shiftGrip: number;
  /**
   * Start order. 'shuffle' (default, owner 17 Oct 2026): a seeded shuffle of the whole field. 'real' (owner 26 Oct 2026):
   * the pace file's real grid order (PaceCar.grid), used by phones and tablets, which race the player's 40 pace
   * neighbours (src/app/field-select.ts) so the race around the player is the real one. 'shuffle' is the code path as before.
   */
  gridOrder: 'shuffle' | 'real';
  /**
   * Self-play only (`playerAi`): the AI-driven player's pace scale (tools/race/selfplay.ts --player-scale; the AI Probe:
   * scale 1 = its solo lap, 120.2 s at Laguna) instead of its pace row's. NaN = the row's (default).
   */
  playerScale: number;
  /** With `playerScale`: the player's pace hint (its solo lap at that scale), s. NaN = the row's target lap. */
  playerLap: number;
}

/** One AI loss of control (director.mishapLog). */
export interface MishapEvent { t: number; idx: number; number: string; corner: string; kind: MishapKind }

export const DEFAULT_RACE_CONFIG: RaceConfig = {
  laps: 10, seed: 1, ai_version: AI_VERSION, playerNumber: '619', greenWindow: [5, 30],
  formationSpeed: 20, gridGap: 15, aiControlEvery: 2, aiPhysicsEvery: 2, aiWalls: true, playerAi: false, maxAi: Infinity,
  mishapRate: 0.0002,
  followScale: 1,
  laneMargin: 1,
  gridOrder: 'shuffle',
  shiftGrip: 0,
  playerScale: Number.NaN,
  playerLap: Number.NaN,
};

export interface RaceInputs {
  line: RaceLine;
  /** Physics surface (with the pit lane / paved zones, as the app builds it). Used by the director's own queries. */
  surface: Surface;
  /**
   * Factory for one Surface per car (same options as `surface`). Surface.sample() caches the last
   * station, so cars sharing one surface would make results depend on evaluation order; give each car
   * its own. Strongly recommended (the determinism guarantee assumes it); without it every car
   * shares `surface` (still reproducible run to run, since the order is fixed).
   */
  makeSurface?: () => Surface;
  /** The player's surface (the app's), when the app keeps using its own; default makeSurface(). */
  playerSurface?: Surface;
  /** Probe car.json (the base of every AI car). */
  probeJson: unknown;
  pace: PaceJson;
  /** identity.json contents (the track's own, else public/cars/field/identity.json), or null when missing; rows are
   *  matched to pace cars by field key (`id`, else number: field.ts fieldKey). */
  identity?: unknown | null;
  /** scenery.json pit_lane (the penalty box is on its first part); null → fallback box beside the front straight. */
  pitLane?: PitLaneJson | null;
  /** scenery.json blend_line (Mid-Ohio round 11): two wheels across the pit-exit blend line are a black flag; absent = no rule. */
  blendLine?: BlendLineJson | null;
  collisionWorld?: CollisionWorld | null;
  /** The player's Vehicle (the app's). Omit to let the director create one from probeJson. */
  playerVehicle?: Vehicle | null;
}

export interface GapInfo { number: string; seconds: number; metres: number }
export interface PenaltyHud {
  /** black flags so far (1st = warning) */
  count: number;
  /** stop-and-go penalties waiting to be served, seconds each */
  pending: number[];
  /** remaining seconds of the stop-and-go being served (0 when none) */
  servingRemaining: number;
  inBox: boolean;
  /** the stop-and-go is being fast-forwarded: the car is held in place and the app runs time at FF_SCALE */
  fastForward: boolean;
  /** laps left to serve the first pending penalty before ejection (null when none pending) */
  lapsToServe: number | null;
  /** reason of the last black flag */
  lastReason: string | null;
  lastAt: number;
  ejected: boolean;
}
export interface ResultRow {
  position: number; number: string; team: string; class: string;
  /** metres covered at the flag (race distance from the start/finish line) */
  metres: number;
  /** fractional laps = metres / lap length */
  laps: number;
  lapsCompleted: number;
  bestLap: number | null;
  /** race time, s from the green to the crossing that completed the last lap; null for a car classified short of it */
  time: number | null;
  status: 'running' | 'ejected';
  player: boolean;
}
export interface RaceHud {
  phase: RacePhase;
  flag: RaceFlag;
  /** race clock since the start of the formation, s */
  time: number;
  lap: number; lapsTotal: number;
  /** the player's distance since the green flag, m (0 before it): the live counter. Results and the scoreboard keep
   *  race distance from the start/finish line, so a back-of-grid start earns no extra metres on the board. */
  raced: number;
  position: number; carsTotal: number;
  classPosition: number; className: string;
  gapAhead: GapInfo | null; gapBehind: GapInfo | null;
  lastLap: number | null; bestLap: number | null;
  penalties: PenaltyHud;
  /** short text for a banner ("BLACK FLAG: contact — warning", "GREEN GREEN GREEN", ...) */
  message: string | null;
  results: ResultRow[] | null;
}
/** For the engine-sound stream: what kind of engine this car has (rpm / gear / throttleOut come from `state`). */
export interface EngineInfo { layout: string; cylinders: number; redline: number; shiftRpm: number; turbo: boolean; exhaustNote: string | null; drive: string }
export interface CarPose {
  number: string; isPlayer: boolean;
  /** the car's field key (pace.json `id`, else its number): identity / model / sound rows are found by it */
  id: string;
  /** live VehicleState (pos, quat, wheels, rpm, gear, throttleOut, impact): pass to CarRig.pose() */
  state: VehicleState;
  /** placeholder tint (#rrggbb) when the car's own model is missing; identity colors take precedence */
  tint: string;
  identity: IdentityCar | null;
  engine: EngineInfo;
  /** brake pedal 0..1 this step (AI: its driver's input; the player: 0 here, the app knows its own) */
  brake: number;
}

export interface RaceCar {
  idx: number;
  number: string; team: string; cls: string; grid: number;
  /** field key (pace.json `id`, else the number): the identity row is found by it */
  id: string;
  /** models.json key: pace `model_id`, else identity `model_id`, else `id` (field.ts modelKey) */
  model: string;
  isPlayer: boolean;
  vehicle: Vehicle;
  /** this car's own Surface (see RaceInputs.makeSurface) */
  surface: Surface;
  spec: CarSpec;
  driver: AiDriver | null;
  pace: PaceCar | null;
  identity: IdentityCar | null;
  tint: string;
  /**
   * The driver pace this race drew for the car (field.ts drawPace: one of its real stints, from the race
   * seed): target lap s, its lap sigma, the pace scale the vehicle was built with, and the stint index
   * (-1 = car-level pace). Internal: never shown to the player.
   */
  paceTarget: number; paceSigma: number; paceScale: number; stint: number;
  /** the pace the other drivers read for it (Traffic.pace; field.ts paceHint: the target, or the lap a capped car can do) */
  paceHint: number;
  // race bookkeeping
  U: number; hint: number;
  lapStart: number; lastLap: number; bestLap: number;
  /** race time (s after the green) of the crossing that completed the last lap; NaN until then */
  finishAt: number;
  lapsDone: number;
  lapIdx: number; lapStartGreen: boolean;
  /** race distance U at the green flag (NaN before): the live counter counts from here (owner, 17 Oct 2026) */
  greenU: number;
  finished: boolean;
  recoveries: number;
  /** losses of control this race (AI only) */
  mishaps: number;
}

const RING_DS = 4;
/** Black-flag reasons for app-side violations (reportViolation). */
const VIOLATION_TEXT: Record<string, string> = { pit_exit_cones: 'crossed the pit-exit cones' };
/** Closing speed (m/s) a car-vs-car contact needs before the player can be at fault: 5 mph. Gentle taps and
 *  door-to-door rubbing below it are racing, not a black flag (owner, 17 Oct 2026). */
export const CONTACT_FAULT_CLOSING = 5 * 0.44704;
/** Stop-and-go fast-forward (owner, 17 Oct 2026): once the player stands still in the box with more than FF_TAIL_S
 *  left, the director holds the car (the player's input is replaced by HOLD_INPUT) and sets `timeScale` = FF_SCALE
 *  for the app's frame loop; the last FF_TAIL_S run at 1x with the driver back in control, ready to go. */
export const FF_SCALE = 10;
export const FF_TAIL_S = 5;
const HOLD_INPUT: DriverInput = { steer: 0, throttle: 0, brake: 1, shiftUp: false, shiftDown: false, handbrake: true };
/** Seconds of chequered flag before the race is `finished` for the player (was 120: a full cool-down lap). */
export const FINISH_GRACE_S = 3;
const STOP_GO = [0, 0, 60, 60, 180]; // by black-flag count (1-based); 5th = ejected

/** Penalty box: a stretch of the pit lane where the player must stand still. */
class PenaltyBox {
  private cx: Float64Array; private cy: Float64Array; private hw: Float64Array; private n: number;
  readonly fallback: boolean;
  constructor(pit: PitLaneJson | null | undefined, private line: RaceLine) {
    const part = pit?.parts?.[0];
    if (part && part.n > 20) {
      const i0 = Math.floor(0.4 * part.n), i1 = Math.floor(0.7 * part.n);
      this.n = i1 - i0;
      this.cx = new Float64Array(this.n); this.cy = new Float64Array(this.n); this.hw = new Float64Array(this.n);
      for (let k = 0; k < this.n; k++) {
        const c = part.center[i0 + k], l = part.left[i0 + k], r = part.right[i0 + k];
        this.cx[k] = c[0]; this.cy[k] = c[1];
        this.hw[k] = 0.5 * dhypot(l[0] - r[0], l[1] - r[1]) + 0.3;
      }
      this.fallback = false;
    } else { this.n = 0; this.cx = this.cy = this.hw = new Float64Array(0); this.fallback = true; }
  }
  /** A spot in the middle of the box (world x, y, heading) for tests / a HUD marker. */
  spot(): { x: number; y: number; heading: number } | null {
    if (this.fallback || this.n < 3) return null;
    const k = this.n >> 1;
    return { x: this.cx[k], y: this.cy[k], heading: datan2(this.cy[k + 1] - this.cy[k - 1], this.cx[k + 1] - this.cx[k - 1]) };
  }
  contains(x: number, y: number, s: number, lat: number): boolean {
    if (this.fallback) {
      // no pit lane data: stopped beside the front straight, off the racing surface (either side)
      const L = this.line.L;
      const inS = s > L - 250 || s < 20;
      const edge = lat > 0 ? this.line.at(this.line.halfL, s) : this.line.at(this.line.halfR, s);
      return inS && Math.abs(lat) > edge + 0.5 && Math.abs(lat) < edge + 25;
    }
    let best = Infinity, bk = -1;
    for (let k = 0; k < this.n; k++) {
      const d = sq(x - this.cx[k]) + sq(y - this.cy[k]);
      if (d < best) { best = d; bk = k; }
    }
    return bk > 0 && bk < this.n - 1 && Math.sqrt(best) < this.hw[bk];
  }
}

function tintFor(num: string): string {
  const h = hashSeed(17, `tint:${num}`) % 360;
  // HSL (h, 55 %, 50 %) → hex
  const s = 0.55, l = 0.5;
  const f = (n: number) => { const k = (n + h / 30) % 12; const c = l - s * Math.min(l, 1 - l) * Math.max(-1, Math.min(k - 3, 9 - k, 1)); return Math.round(255 * c).toString(16).padStart(2, '0'); };
  return `#${f(0)}${f(8)}${f(4)}`;
}

/** Cache of per-car derived data (spec, perf, profile) keyed by number + scale, shared across restarts. */
interface Prepared { spec: CarSpec; perf: CarPerf; profile: Float64Array }

/** AI Probe solo lap at scale 1, s (calibrate_field prints the current value): the scale estimate when pace.json is stale. */
const REF_LAP = 121.5;

export class RaceDirector {
  readonly config: RaceConfig;
  readonly line: RaceLine;
  readonly surface: Surface;
  readonly cars: RaceCar[] = [];
  readonly player: RaceCar;
  readonly traffic: Traffic;
  readonly collider = new CarCollider();
  /** true when pace.json was calibrated with another AI_VERSION (or has no scales): paces are approximate */
  readonly calibrationStale: boolean;
  phase: RacePhase = 'formation';
  time = 0;
  /** car-vs-car contacts this step (valid until the next step) */
  contacts: readonly CarContactEvent[] = [];
  contactCount = 0;
  /** every AI loss of control so far, in order (tools / tests; not shown in the HUD) */
  readonly mishapLog: MishapEvent[] = [];

  #greenAt = 0;            // never exposed before it happens
  private rng: Rng;
  private stepIdx = 0;
  private lastDt = 0.001;
  private bodies: CarBody[] = [];
  private probe: unknown;
  private collisionWorld: CollisionWorld | null;
  private flagAt = NaN;
  private results: ResultRow[] | null = null;
  private ring: Float64Array[] = [];
  private ringBin: Int32Array[] = [];
  private readonly ringN: number;
  private box: PenaltyBox;
  private readonly playerInputAi: DriverInput = { steer: 0, throttle: 0, brake: 0, shiftUp: false, shiftDown: false };
  private readonly prepared = new Map<string, Prepared>();
  private yellowOn = false;
  // player rules
  private pen = { count: 0, pending: [] as number[], serving: 0, deadlineU: Infinity, inBox: false, fastForward: false, lastReason: null as string | null, lastAt: -1e9, ejected: false };
  /** What the app multiplies its frame dt by right now: FF_SCALE while a stop-and-go is fast-forwarded, else 1. */
  timeScale = 1;
  private offT = 0; private onT = 99; private offArmed = true;
  private readonly blend: BlendFlag | null;
  private contactSeen = new Map<number, number>();
  private violationSeen = new Map<string, number>();
  private aheadOfPlayer: Int8Array;
  private message: string | null = null; private messageUntil = 0;
  private hudObj: RaceHud | null = null;
  private poseCache: CarPose[] | null = null;

  constructor(inputs: RaceInputs, config: Partial<RaceConfig> = {}) {
    this.config = { ...DEFAULT_RACE_CONFIG, ...config };
    this.line = inputs.line;
    // the director's own queries get their own Surface when possible (sample() caches per instance)
    this.surface = inputs.makeSurface ? inputs.makeSurface() : inputs.surface;
    this.box = new PenaltyBox(inputs.pitLane ?? null, this.line);
    this.blend = inputs.blendLine ? new BlendFlag(new BlendLineWatch(new BlendLine(inputs.blendLine))) : null;
    const ident = inputs.identity ? parseIdentity(inputs.identity) : new Map<string, IdentityCar>();
    const pace = inputs.pace;
    this.calibrationStale = pace.ai_version !== AI_VERSION || pace.cars.some((c) => !c.player && (!(c.scale! > 0) || (c.stints ?? []).some((s) => !(s.scale! > 0))));
    const probe = inputs.probeJson as any;
    // field: by grid
    const byGrid = [...pace.cars].sort((a, b) => a.grid - b.grid);
    let aiLeft = this.config.maxAi;
    const entries: PaceCar[] = [];
    let playerEntry = byGrid.find((c) => c.number === this.config.playerNumber) ?? null;
    for (const c of byGrid) {
      if (c.number === this.config.playerNumber) { entries.push(c); continue; }
      if (aiLeft-- > 0) entries.push(c);
    }
    if (!playerEntry) {
      playerEntry = { number: this.config.playerNumber, team: 'Player', class: 'B', grid: entries.length + 1, finish: 0, lapsCompleted: 0, greenLaps: 0, targetLap: 128, bestLap: 120, sigma: 3, aggression: 1, player: true };
      entries.push(playerEntry);
    }
    this.probe = probe;
    this.collisionWorld = inputs.collisionWorld ?? null;
    for (const c of entries) {
      const isPlayer = c.number === this.config.playerNumber;
      const id = ident.get(fieldKey(c)) ?? null;
      let vehicle: Vehicle, spec: CarSpec, driver: AiDriver | null = null;
      const dp = this.drawFor(c, isPlayer, this.config.seed);
      if (isPlayer && inputs.playerVehicle) {
        vehicle = inputs.playerVehicle; spec = vehicle.spec;
      } else if (isPlayer && !this.config.playerAi) {
        spec = loadCarSpec(probe); vehicle = new Vehicle(spec, { autoShift: true });
      } else {
        const prep = this.prepare(probe, c.number, isPlayer ? null : id, dp.scale);
        spec = prep.spec; vehicle = new Vehicle(spec, { autoShift: true });
      }
      if (inputs.collisionWorld && (isPlayer ? !inputs.playerVehicle : this.config.aiWalls)) vehicle.setCollisionWorld(inputs.collisionWorld);
      const car: RaceCar = {
        idx: this.cars.length, number: c.number, id: fieldKey(c), model: modelKey(c, id), team: c.team, cls: c.class, grid: c.grid, isPlayer, vehicle,
        surface: (isPlayer && inputs.playerSurface) || (inputs.makeSurface ? inputs.makeSurface() : inputs.surface), spec, driver, pace: c,
        identity: id, tint: tintFor(c.number), paceTarget: dp.targetLap, paceSigma: dp.sigma, paceScale: dp.scale, stint: dp.stint, paceHint: dp.hint,
        U: 0, hint: -1, lapStart: NaN, lastLap: NaN, bestLap: NaN, finishAt: NaN, lapsDone: 0, lapIdx: 0, lapStartGreen: false, greenU: NaN, finished: false, recoveries: 0, mishaps: 0,
      };
      this.cars.push(car);
    }
    this.player = this.cars.find((c) => c.isPlayer)!;
    const n = this.cars.length;
    this.traffic = new Traffic(n, this.line.L);
    for (const car of this.cars) {
      const sp = car.spec;
      this.traffic.front[car.idx] = sp.hull.front; this.traffic.rear[car.idx] = -sp.hull.rear; this.traffic.hw[car.idx] = sp.hull.halfWidth;
      this.traffic.pace[car.idx] = car.paceHint;
      this.bodies.push({ vehicle: car.vehicle, front: sp.hull.front, rear: sp.hull.rear, halfWidth: sp.hull.halfWidth });
      const aiDriven = !car.isPlayer || this.config.playerAi;
      if (aiDriven) car.driver = this.makeDriver(car);
      this.traffic.profile[car.idx] = car.driver ? car.driver.profile : null;
    }
    // lane spacing: the widest car plus 0.6 m (adjacent lanes leave every pair of cars >= 0.6 m apart)
    { let hw = 0; for (let k = 0; k < n; k++) hw = Math.max(hw, this.traffic.hw[k]); this.traffic.laneW = Math.max(2.4, 2 * hw + 0.6); }
    this.ringN = Math.ceil((2 * this.line.L) / RING_DS) + 4;
    for (let i = 0; i < n; i++) { this.ring.push(new Float64Array(this.ringN)); this.ringBin.push(new Int32Array(this.ringN).fill(-2147483648)); }
    this.aheadOfPlayer = new Int8Array(n);
    this.rng = new Rng(1);
    this.restart(this.config.seed);
  }

  /** The pace a car races with: the player keeps its car-level pace (self-play: `playerScale`); an AI car draws one of its real
   *  stints from the seed. `hint`: what the other drivers read (Traffic.pace, field.ts paceHint). */
  private drawFor(c: PaceCar, isPlayer: boolean, seed: number): { targetLap: number; sigma: number; scale: number; stint: number; hint: number } {
    if (isPlayer) {
      const cfg = this.config;
      if (cfg.playerAi && cfg.playerScale > 0) { const t = cfg.playerLap > 0 ? cfg.playerLap : c.targetLap; return { targetLap: t, sigma: c.sigma, scale: cfg.playerScale, stint: -1, hint: t }; }
      return { targetLap: c.targetLap, sigma: c.sigma, scale: c.scale && c.scale > 0 ? c.scale : 1, stint: -1, hint: c.targetLap };
    }
    const dp = drawPace(c, seed);
    return { targetLap: dp.targetLap, sigma: dp.sigma, scale: dp.scale ?? REF_LAP / dp.targetLap, stint: dp.stint, hint: paceHint(dp.targetLap, dp.achievedLap) };
  }

  private makeDriver(car: RaceCar): AiDriver {
    const prep = this.prepare(this.probe, car.number, car.isPlayer ? null : car.identity, car.paceScale);
    return new AiDriver(car.vehicle, this.line, prep.perf, car.spec, prep.profile, {
      number: car.number, scale: car.paceScale, targetLap: car.paceTarget, sigma: car.paceSigma,
      aggression: (car.pace?.aggression ?? 1) as 0 | 1 | 2, seed: 0,
    }, car.idx, this.traffic);
  }

  /**
   * Re-draw an AI car's driver for a new seed; when the pace changed, rebuild its vehicle (the scale is
   * baked into the spec), collision body and driver. The player's car is never rebuilt.
   */
  private redraw(car: RaceCar, seed: number): void {
    if (car.isPlayer || !car.pace) return;
    const dp = this.drawFor(car.pace, false, seed);
    if (dp.scale === car.paceScale && dp.targetLap === car.paceTarget && dp.sigma === car.paceSigma && dp.hint === car.paceHint) return;
    const prep = this.prepare(this.probe, car.number, car.identity, dp.scale);
    car.spec = prep.spec;
    car.vehicle = new Vehicle(prep.spec, { autoShift: true });
    if (this.collisionWorld && this.config.aiWalls) car.vehicle.setCollisionWorld(this.collisionWorld);
    const sp = car.spec;
    this.bodies[car.idx] = { vehicle: car.vehicle, front: sp.hull.front, rear: sp.hull.rear, halfWidth: sp.hull.halfWidth };
    car.paceTarget = dp.targetLap; car.paceSigma = dp.sigma; car.paceScale = dp.scale; car.stint = dp.stint; car.paceHint = dp.hint;
    this.traffic.pace[car.idx] = dp.hint;
    car.driver = this.makeDriver(car);
    this.traffic.profile[car.idx] = car.driver.profile;
  }

  private prepare(probe: any, number: string, id: IdentityCar | null, scale: number): Prepared {
    const key = `${number}|${scale}|${id ? 'id' : '-'}`;
    let p = this.prepared.get(key);
    if (!p) {
      const spec = loadCarSpec(aiCarJson(probe, id, scale));
      const perf = measureCarPerf(spec);
      p = { spec, perf, profile: buildSpeedProfile(this.line, perf, spec) };
      this.prepared.set(key, p);
    }
    return p;
  }

  /** Restart the race with a new seed: same field, new driver draw per AI car, new grid formation and green moment. */
  restart(seed: number): void {
    (this.config as RaceConfig).seed = seed;
    this.rng = new Rng(hashSeed(seed, `race:v${AI_VERSION}`));
    for (const car of this.cars) this.redraw(car, seed);
    const [g0, g1] = this.config.greenWindow;
    this.#greenAt = this.rng.range(g0, g1);
    this.phase = 'formation'; this.time = 0; this.stepIdx = 0; this.flagAt = NaN; this.results = null; this.yellowOn = false;
    this.pen = { count: 0, pending: [], serving: 0, deadlineU: Infinity, inBox: false, fastForward: false, lastReason: null, lastAt: -1e9, ejected: false };
    this.offT = 0; this.onT = 99; this.offArmed = true; this.contactSeen.clear(); this.violationSeen.clear(); this.blend?.reset();
    this.message = null; this.messageUntil = 0;
    const line = this.line, L = line.L;
    // grid (owner, 17 Oct 2026): a seeded shuffle, so every race and restart has a different start order (`?seed=`
    // reproduces one), single file on the racing line, the WHOLE field behind the start/finish line so race distance
    // (U) and lap 1 begin at the line after the green: the leader starts far enough back to still be before the line
    // at the latest green moment (greenWindow[1] x formationSpeed + 30 m), each car ~gridGap behind the one ahead
    const sorted = [...this.cars];
    if (this.config.gridOrder === 'real') sorted.sort((a, b) => (a.pace?.grid ?? Infinity) - (b.pace?.grid ?? Infinity) || a.idx - b.idx);
    else for (let k = sorted.length - 1; k > 0; k--) { const j = this.rng.int(k + 1); const t = sorted[k]; sorted[k] = sorted[j]; sorted[j] = t; }
    sorted.forEach((c, k) => { c.grid = k + 1; });
    const lenOf = (c: RaceCar) => c.spec.hull.front - c.spec.hull.rear;
    let s = L - (this.config.greenWindow[1] * this.config.formationSpeed + 30);
    const pos = new Float64Array(2);
    for (let k = 0; k < sorted.length; k++) {
      const car = sorted[k];
      if (k > 0) s -= this.config.gridGap + 0.5 * (lenOf(car) + lenOf(sorted[k - 1]));
      const sw = line.wrap(s);
      line.pointAt(sw, line.at(line.off, sw), pos);
      const sm = car.surface.sample(pos[0], pos[1]);
      const z = sm.z, up = [sm.nx, sm.ny, sm.nz];   // copy: the sample object is reused
      let v0 = this.config.formationSpeed;
      if (car.driver) v0 = Math.min(v0, 0.9 * line.at(car.driver.profile, sw));
      car.vehicle.reset([pos[0], pos[1], z], line.headingAt(sw), Math.max(5, v0), up);
      // race distance from the start/finish line: negative before it (s near L), positive past it
      car.U = sw > 0.5 * L ? sw - L : sw;
      car.hint = -1; car.lapStart = NaN; car.lastLap = NaN; car.bestLap = NaN; car.finishAt = NaN; car.lapsDone = 0; car.lapIdx = Math.floor(car.U / L); car.lapStartGreen = false; car.greenU = NaN; car.finished = false; car.recoveries = 0; car.mishaps = 0;
      if (car.driver) {
        car.driver.resetState();
        car.driver.mishapCount = 0;
        (car.driver.params as { seed: number }).seed = hashSeed(seed, `drv:${car.number}`);
        (car.driver as unknown as { rng: Rng }).rng = new Rng(hashSeed(seed, `drv:${car.number}`));
        (car.driver as unknown as { lastLapIdx: number }).lastLapIdx = Number.NaN;
      }
      this.ringBin[car.idx].fill(-2147483648);
    }
    this.mishapLog.length = 0;
    this.refreshTraffic(true);
    for (const car of this.cars) this.aheadOfPlayer[car.idx] = car.U > this.player.U ? 1 : -1;
    this.applyControl();
    this.say('FORMATION — double yellow, hold position', 6);
  }

  /** Full-course yellow on/off (no passing, speed capped). The race starts with the formation instead. */
  setYellow(on: boolean): void {
    if (this.phase === 'green' || this.phase === 'yellow') { this.yellowOn = on; this.phase = on ? 'yellow' : 'green'; this.applyControl(); }
  }

  private say(msg: string, seconds: number): void { this.message = msg; this.messageUntil = this.time + seconds; }

  private applyControl(): void {
    for (const car of this.cars) {
      const d = car.driver;
      if (!d) continue;
      const c = d.ctl;
      c.noise = true;
      c.followScale = this.config.followScale;
      c.laneMargin = this.config.laneMargin;
      c.shiftGrip = this.config.shiftGrip;
      c.mishapRate = this.phase === 'green' && !car.isPlayer && !car.finished ? this.config.mishapRate : 0;
      if (this.phase === 'formation') { c.speedCap = this.config.formationSpeed + 3; c.noPass = true; c.minGap = this.config.gridGap; c.paceFactor = 1; }
      else if (this.phase === 'yellow') { c.speedCap = this.config.formationSpeed * 1.25 + 3; c.noPass = true; c.minGap = 10; c.paceFactor = 1; }
      else { c.speedCap = Infinity; c.noPass = false; c.minGap = 0; c.paceFactor = car.finished ? 0.6 : 1; }
    }
  }

  // ------------------------------------------------------------------ stepping

  /**
   * Advance the whole race by dt (0.001 s): AI control, every vehicle (the player's with `playerInput`),
   * car-vs-car contacts, lap counting, flags and the player rules.
   */
  step(dt: number, playerInput?: DriverInput | null): void {
    this.time += dt;
    this.stepIdx++;
    const phys = Math.max(1, this.config.aiPhysicsEvery | 0);
    const every = phys > 1 ? phys : Math.max(1, this.config.aiControlEvery | 0);
    for (const car of this.cars) {
      const d = car.driver;
      if (!d) continue;
      if ((this.stepIdx + car.idx) % every === 0) {
        d.update(dt * every);
        if (d.mishapCount !== car.mishaps) {
          car.mishaps = d.mishapCount;
          this.mishapLog.push({ t: this.time, idx: car.idx, number: car.number, corner: this.line.corners[d.lastMishapCorner]?.name ?? '?', kind: d.mishap ?? 'wide' });
        }
      }
    }
    for (const car of this.cars) {
      if (car.isPlayer && !car.driver) { car.vehicle.step(this.pen.fastForward ? HOLD_INPUT : (playerInput ?? this.playerInputAi), car.surface, dt); continue; }
      if (car.isPlayer || phys === 1) car.vehicle.step(car.driver!.input, car.surface, dt);
      else if ((this.stepIdx + car.idx) % phys === 0) car.vehicle.step(car.driver!.input, car.surface, dt * phys);
    }
    this.contactCount = this.collider.resolve(this.bodies, this.traffic.order, this.traffic.s, this.line.L);
    this.contacts = this.collider.events;
    this.lastDt = dt;
    this.refreshTraffic(false);
    this.bookkeeping(dt);
  }

  private refreshTraffic(init: boolean): void {
    const tr = this.traffic, line = this.line, L = line.L;
    for (const car of this.cars) {
      const st = car.vehicle.state;
      const p = line.project(st.pos[0], st.pos[1], car.hint);
      car.hint = p.index;
      const i = car.idx;
      if (!init) {
        let d = p.s - tr.s[i];
        if (d > 0.5 * L) d -= L; else if (d < -0.5 * L) d += L;
        car.U += d;
      }
      tr.a[i] = init ? 0 : tr.a[i] + 0.05 * ((st.speed - tr.v[i]) / this.lastDt - tr.a[i]);
      tr.vlat[i] = init ? 0 : tr.vlat[i] + 0.02 * ((p.lateral - tr.lat[i]) / this.lastDt - tr.vlat[i]);
      tr.s[i] = p.s; tr.lat[i] = p.lateral; tr.v[i] = st.speed; tr.U[i] = car.U;
      { const e = p.lateral - line.at(line.off, p.s); tr.ve[i] = init ? 0 : tr.ve[i] + 0.02 * ((e - tr.e[i]) / this.lastDt - tr.ve[i]); tr.e[i] = e; }
      if (!car.driver || init) tr.eT[i] = tr.e[i] + (car.driver ? 0 : Math.max(-1.5, Math.min(1.5, 0.5 * tr.vlat[i])));
      const edge = p.lateral > 0 ? line.at(line.halfL, p.s) : line.at(line.halfR, p.s);
      tr.away[i] = Math.abs(p.lateral) > edge + 4 || (car.isPlayer && this.pen.ejected) ? 1 : 0;
      if (car.driver) car.driver.hint = p.index;
      if (car.isPlayer && !car.driver) {
        let off = 0;
        for (const w of st.wheels) if (!w.onTrack) off++;
        tr.off[i] = off >= 3 ? 1 : 0;
      }
    }
    tr.sort();
  }

  private bookkeeping(dt: number): void {
    const L = this.line.L, t = this.time;
    // phase: green at the seeded moment
    if (this.phase === 'formation' && t >= this.#greenAt) {
      this.phase = 'green';
      for (const c of this.cars) c.greenU = c.U;   // the live distance counter starts here
      this.applyControl();
      this.say('GREEN GREEN GREEN', 4);
    }
    // laps, time-at-distance ring
    for (const car of this.cars) {
      const i = car.idx;
      const U = car.U;
      const bin = Math.floor(U / RING_DS);
      const slot = ((bin % this.ringN) + this.ringN) % this.ringN;
      if (this.ringBin[i][slot] !== bin) { this.ringBin[i][slot] = bin; this.ring[i][slot] = t; }
      const li = Math.floor(U / L);
      if (li > car.lapIdx) {
        // crossed the start/finish line (race distance U is measured from it)
        const v = Math.max(1, car.vehicle.state.speed);
        const tc = t - (U - li * L) / v;
        if (car.lapStartGreen && Number.isFinite(car.lapStart) && li === car.lapIdx + 1) {
          car.lastLap = tc - car.lapStart;
          if (!(car.bestLap <= car.lastLap)) car.bestLap = car.lastLap;
        }
        car.lapStart = tc;
        car.lapStartGreen = this.phase === 'green' || this.phase === 'yellow';
        car.lapIdx = li;
        car.lapsDone = Math.max(0, li);
        if (li >= this.config.laps && !Number.isFinite(car.finishAt)) car.finishAt = tc - this.#greenAt;
        if ((this.phase === 'chequered' || this.phase === 'finished') && !car.finished) {
          car.finished = true;
          if (car.driver) { car.driver.ctl.paceFactor = 0.6; car.driver.ctl.mishapRate = 0; }
        }
      } else if (li < car.lapIdx) car.lapIdx = li; // reversed over the line
      // recovery
      const d = car.driver;
      if (d && d.needsRecovery) this.recover(car);
    }
    // the flag
    if ((this.phase === 'green' || this.phase === 'yellow')) {
      let leader = this.cars[0];
      for (const c of this.cars) if (c.U > leader.U && !(c.isPlayer && this.pen.ejected)) leader = c;
      if (leader.U >= this.config.laps * L) {
        this.phase = 'chequered';
        this.flagAt = t;
        this.results = this.buildResults();
        for (const c of this.cars) if (c.U >= this.config.laps * L) { c.finished = true; }
        this.applyControl();
        this.say('CHEQUERED FLAG', 6);
      }
    } else if (this.phase === 'chequered') {
      const p = this.player;
      // the race is over when the leader takes the last lap (owner, 17 Oct 2026): FINISH_GRACE_S of chequered banner, sooner if
      // the player crosses the line or is ejected
      if (p.finished || this.pen.ejected || t - this.flagAt > FINISH_GRACE_S) { this.phase = 'finished'; this.applyControl(); }
    }
    this.playerRules(dt);
  }

  /** Marshal reset: put a stuck / wrong-way AI car back on the racing line at its s, rolling slowly. */
  private recover(car: RaceCar): void {
    const tr = this.traffic, line = this.line, i = car.idx;
    // wait while traffic is close behind or alongside
    // wait for a gap (the longer the car has been stuck, the smaller the gap it accepts)
    const waited = car.driver!.stuckTime;
    const behind = waited > 15 ? 8 : waited > 8 ? 25 : 50;
    for (let k = 1; k < tr.n; k++) {
      const j = tr.order[(tr.rank[i] - k + tr.n) % tr.n];
      const d = -tr.ds(i, j);
      if (d < 0 || d > behind) break;
      // (a stopped car right behind does not block the reset: two stuck cars would otherwise wait for each other)
      if (!tr.away[j] && (tr.v[j] > 5 || (d < 8 && tr.v[j] > 1.5))) return;
    }
    // the spot itself must be clear: a car (stopped or not) within 7 m behind that sits on the line would be reset
    // into (a reset onto stopped #34 left 0.86 m of overlap), so the spot moves ahead of it instead of waiting
    let shift = 0;
    for (let k = 1; k < tr.n; k++) {
      const j = tr.order[(tr.rank[i] - k + tr.n) % tr.n];
      const d = -tr.ds(i, j);
      if (d < 0 || d > 7) break;
      if (!tr.away[j] && Math.abs(tr.lat[j] - line.at(line.off, tr.s[j])) < 3) shift = Math.max(shift, 7 - d);
    }
    for (let k = 1; k < tr.n; k++) {
      const j = tr.order[(tr.rank[i] + k) % tr.n];
      const d = tr.ds(i, j);
      if (d < 0 || d > 10 + shift) break;
      if (!tr.away[j] && Math.abs(tr.lat[j] - this.line.at(this.line.off, tr.s[j])) < 3) return; // somebody on the spot ahead
    }
    const s = line.wrap(tr.s[i] + shift);
    const pos = new Float64Array(2);
    line.pointAt(s, line.at(line.off, s), pos);
    { const sm = car.surface.sample(pos[0], pos[1]); car.vehicle.reset([pos[0], pos[1], sm.z], line.headingAt(s), 8, [sm.nx, sm.ny, sm.nz]); }
    car.driver!.resetState();
    car.hint = -1;
    car.recoveries++;
  }

  // ------------------------------------------------------------------ player rule engine

  /** Issue a black flag to the player (the rule engine's own entry point; also for app-side rules and tests). */
  penalize(reason: string): void { this.blackFlag(reason); }

  /**
   * App-side rule violation (e.g. 'pit_exit_cones' from the scene's cone-line helper): a black flag with the
   * same Lemons escalation as the built-in rules. Debounced like the contact rule: one flag per kind per 2 s
   * (repeated reports while the car is still over the line do not stack). Ignored after the race is finished
   * or once the player is ejected. Returns true when a flag was issued.
   */
  reportViolation(kind: 'pit_exit_cones' | string, detail?: string): boolean {
    if (this.pen.ejected || this.phase === 'finished') return false;
    const last = this.violationSeen.get(kind) ?? -1e9;
    this.violationSeen.set(kind, this.time);
    if (this.time - last < 2) return false;
    const base = VIOLATION_TEXT[kind] ?? kind.replace(/_/g, ' ');
    this.blackFlag(detail ? `${base} (${detail})` : base);
    return true;
  }

  /** Middle of the penalty box (stop-and-go spot) in world coordinates, or null without pit-lane data. */
  penaltyBoxSpot(): { x: number; y: number; heading: number } | null { return this.box.spot(); }

  private blackFlag(reason: string): void {
    if (this.pen.ejected) return;
    const p = this.pen;
    p.count++;
    p.lastReason = reason; p.lastAt = this.time;
    if (p.count === 1) { this.say(`BLACK FLAG: ${reason} — warning`, 6); return; }
    if (p.count >= 5) { this.eject(`5th black flag (${reason})`); return; }
    const dur = STOP_GO[p.count];
    p.pending.push(dur);
    if (p.pending.length === 1) { p.serving = dur; p.deadlineU = this.player.U + 2 * this.line.L; }
    this.say(`BLACK FLAG: ${reason} — ${dur} s stop-and-go in the pit lane within 2 laps`, 8);
  }

  private eject(why: string): void {
    this.pen.ejected = true;
    this.pen.pending = []; this.pen.serving = 0; this.pen.fastForward = false; this.timeScale = 1;
    this.say(`EJECTED: ${why}`, 1e9);
    if (this.results) return;
  }

  private playerRules(dt: number): void {
    const P = this.player, st = P.vehicle.state, pen = this.pen;
    if (pen.ejected || this.phase === 'finished') { pen.fastForward = false; this.timeScale = 1; return; }
    // (a) contact where the player closed on the other car
    for (let k = 0; k < this.contactCount; k++) {
      const ev = this.contacts[k];
      if (ev.a !== P.idx && ev.b !== P.idx) continue;
      const other = ev.a === P.idx ? ev.b : ev.a;
      const last = this.contactSeen.get(other) ?? -1e9;
      this.contactSeen.set(other, this.time);
      if (this.time - last < 2) continue;      // same contact (or a follow-up within 2 s)
      const mine = ev.a === P.idx ? ev.aApproach : ev.bApproach;
      const theirs = ev.a === P.idx ? ev.bApproach : ev.aApproach;
      if (ev.closing > CONTACT_FAULT_CLOSING && mine > theirs + 0.5) this.blackFlag(`contact with #${this.cars[other].number}`);
    }
    // (b) four wheels off the paved surface (sustained 0.25 s; re-armed after 2 s back on)
    let allOff = true;
    for (const w of st.wheels) {
      if (w.onTrack) { allOff = false; break; }
      const smp = this.surface.sample(w.pos[0], w.pos[1]);
      if (smp.paved || smp.onKerbBand) { allOff = false; break; }   // round 15: outside kerb bands are course
    }
    if (allOff) { this.offT += dt; this.onT = 0; } else { this.offT = 0; this.onT += dt; }
    if (this.onT >= 2) this.offArmed = true;
    if (allOff && this.offT >= 0.25 && this.offArmed) { this.offArmed = false; this.blackFlag('four wheels off'); }
    // (b2) the pit-exit blend line (a package that declares one): two wheels across it, strictly, the same flag and penalty
    if (this.blend && this.blend.update(st.pos[0], st.pos[1], st.wheels, dt)) this.blackFlag(this.blend.watch.line.label);
    // (c) passing under yellow: gaining a position on a running car during the formation / a yellow
    const noPass = this.phase === 'formation' || this.phase === 'yellow';
    const tr = this.traffic;
    for (const c of this.cars) {
      if (c === P) continue;
      const now: 1 | -1 = c.U > P.U ? 1 : -1;
      const was = this.aheadOfPlayer[c.idx];
      this.aheadOfPlayer[c.idx] = now;
      if (noPass && was === 1 && now === -1 && P.U - c.U < 50 && !tr.off[c.idx] && !tr.away[c.idx] && c.vehicle.state.speed > 5 && !(c.driver?.needsRecovery)) {
        this.blackFlag(`passing under yellow (#${c.number})`);
      }
    }
    // stop-and-go: serve in the penalty box
    pen.inBox = false; pen.fastForward = false;
    if (pen.pending.length > 0) {
      const p = this.line.project(st.pos[0], st.pos[1], P.hint);
      pen.inBox = Math.abs(st.speed) < 3 && this.box.contains(st.pos[0], st.pos[1], p.s, p.lateral);
      if (pen.inBox && Math.abs(st.speed) < 0.5) {
        pen.serving -= dt;
        if (pen.serving <= 0) {
          pen.pending.shift();
          if (pen.pending.length) { pen.serving = pen.pending[0]; pen.deadlineU = P.U + 2 * this.line.L; this.say(`stop-and-go served — next ${pen.serving} s`, 5); }
          else { pen.serving = 0; pen.deadlineU = Infinity; this.say('stop-and-go served — rejoin the race', 5); }
        }
      }
      // fast-forward: stood still in the box with more than FF_TAIL_S to go → hold the car, the app runs time at FF_SCALE
      pen.fastForward = pen.inBox && Math.abs(st.speed) < 0.5 && pen.pending.length > 0 && pen.serving > FF_TAIL_S;
      if (pen.pending.length && P.U > pen.deadlineU) this.eject('stop-and-go not served within 2 laps');
    }
    this.timeScale = pen.fastForward ? FF_SCALE : 1;
  }

  // ------------------------------------------------------------------ outputs

  private timeAt(i: number, U: number): number {
    const bin = Math.floor(U / RING_DS);
    const slot = ((bin % this.ringN) + this.ringN) % this.ringN;
    return this.ringBin[i][slot] === bin ? this.ring[i][slot] : NaN;
  }

  private order(): RaceCar[] {
    return [...this.cars].sort((a, b) => b.U - a.U || a.grid - b.grid);
  }

  private buildResults(): ResultRow[] {
    const L = this.line.L;
    return this.order().map((c, k) => ({
      position: k + 1, number: c.number, team: c.team, class: c.cls,
      metres: +Math.max(0, c.U).toFixed(1), laps: +(Math.max(0, c.U) / L).toFixed(3),
      lapsCompleted: Math.max(0, Math.floor(c.U / L)),
      bestLap: Number.isFinite(c.bestLap) ? +c.bestLap.toFixed(3) : null,
      time: Number.isFinite(c.finishAt) ? +c.finishAt.toFixed(3) : null,
      status: c.isPlayer && this.pen.ejected ? 'ejected' : 'running', player: c.isPlayer,
    }));
  }

  /** Final classification (set at the chequered flag; null before). */
  getResults(): ResultRow[] | null { return this.results; }

  /** Plain HUD state (the object is reused between calls). The green moment is never in it before it happens. */
  hud(): RaceHud {
    const P = this.player, L = this.line.L, pen = this.pen;
    const ord = this.order();
    const pos = ord.indexOf(P);
    const ahead = pos > 0 ? ord[pos - 1] : null, behind = pos < ord.length - 1 ? ord[pos + 1] : null;
    const gap = (front: RaceCar, back: RaceCar): GapInfo => {
      const m = front.U - back.U;
      let sec = this.time - this.timeAt(front.idx, back.U);
      if (!Number.isFinite(sec)) sec = m / Math.max(5, back.vehicle.state.speed);
      return { number: front === P ? back.number : front.number, seconds: +sec.toFixed(2), metres: +m.toFixed(1) };
    };
    const cls = ord.filter((c) => c.cls === P.cls);
    let flag: RaceFlag = this.phase === 'formation' || this.phase === 'yellow' ? 'yellow' : this.phase === 'green' ? 'green' : 'chequered';
    if (pen.ejected || pen.pending.length > 0 || this.time - pen.lastAt < 5) flag = 'black';
    const hud: RaceHud = this.hudObj ?? (this.hudObj = {} as RaceHud);
    hud.phase = this.phase; hud.flag = flag; hud.time = this.time;
    hud.lap = Math.min(this.config.laps, Math.max(1, Math.floor(Math.max(0, P.U) / L) + 1));
    hud.lapsTotal = this.config.laps;
    hud.raced = Number.isFinite(P.greenU) ? Math.max(0, P.U - P.greenU) : 0;
    hud.position = pos + 1; hud.carsTotal = ord.length;
    hud.classPosition = cls.indexOf(P) + 1; hud.className = P.cls;
    hud.gapAhead = ahead ? gap(ahead, P) : null;
    hud.gapBehind = behind ? gap(P, behind) : null;
    hud.lastLap = Number.isFinite(P.lastLap) ? P.lastLap : null;
    hud.bestLap = Number.isFinite(P.bestLap) ? P.bestLap : null;
    hud.penalties = {
      count: pen.count, pending: [...pen.pending], servingRemaining: pen.pending.length ? Math.max(0, pen.serving) : 0, inBox: pen.inBox, fastForward: pen.fastForward,
      lapsToServe: pen.pending.length ? Math.max(0, (pen.deadlineU - P.U) / L) : null,
      lastReason: pen.lastReason, lastAt: pen.lastAt, ejected: pen.ejected,
    };
    hud.message = this.time < this.messageUntil ? this.message : null;
    hud.results = this.results;
    return hud;
  }

  /** Every car's pose for rendering (CarRig.pose takes the VehicleState). */
  poses(): CarPose[] {
    if (!this.poseCache) {
      this.poseCache = this.cars.map((c) => {
        const t = c.isPlayer ? resolveCarType(null) : resolveCarType(c.identity);
        const engine: EngineInfo = {
          layout: t.engineLayout, cylinders: t.cylinders, redline: c.spec.engine.revLimitRpm - (t.probeFallback ? 0 : 100),
          shiftRpm: c.spec.drivetrain.autoShift.upshiftRpm, turbo: t.turbo, exhaustNote: t.exhaustNote, drive: c.spec.drivetrain.layout,
        };
        return { number: c.number, id: c.id, isPlayer: c.isPlayer, state: c.vehicle.state, tint: c.tint, identity: c.identity, engine, brake: 0 };
      });
    }
    for (let i = 0; i < this.poseCache.length; i++) { const d = this.cars[i].driver; this.poseCache[i].brake = d ? d.input.brake : 0; }
    return this.poseCache;
  }

  /** Recoveries (marshal resets) so far, all cars. */
  get recoveries(): number { let r = 0; for (const c of this.cars) r += c.recoveries; return r; }

  /** AI losses of control so far, all cars (per car: `car.mishaps`; details: `mishapLog`). */
  get mishaps(): number { return this.mishapLog.length; }
}
