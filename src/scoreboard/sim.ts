// The deterministic hot-lap simulation loop, shared by the client (live driving + recording) and the
// server (replay). It mirrors createSim()/physicsStep() in src/app/index.ts; the client should drive
// the car through HotlapSim.step() so that what is recorded is exactly what the server re-runs.
// Pure TS: no DOM, no Node built-ins.
import {
  Vehicle, loadCarSpec, createTrackSurface, createTrackProjector, createCollisionWorld, lineToWorld,
  deriveGearSchedule, scheduleTargetAt, createOffTrackJudge, OffTrackWatch, OFFTRACK_FAR_M,
  type OffTrackJudge,
  type CarSpec, type DriverInput, type Surface, type TrackJson, type PitLaneJson, type SceneryCollisionJson, type CollisionWorld,
  type GearSchedule,
  type SausageJson, type KerbsJson, type TerrainOverrideJson } from '../physics';
import { LapTimer, type Lap } from '../app/timing';
import {
  STEP, SAMPLE_EVERY, TIMING_EVERY, ROLLING_START_BEFORE_LAST_CORNER_M, ROLLING_START_SPEED, START_BACK_M,
  FLAG_SHIFT_UP, FLAG_SHIFT_DOWN, FLAG_HANDBRAKE, FLAG_AUTOSHIFT, FLAG_ABS, QUANT, TRACE_FORMAT, TRACKS, type TrackInfo,
} from './config';
import { physicsVersion } from './hash';
import type { InputTrace, TraceRow } from './types';

/** scenery.json fields the sim uses (a structural subset of src/app/scenery.ts SceneryJson). */
export interface SceneryLike extends SceneryCollisionJson {
  far?: { heightfield?: { file?: string; x0: number; y0: number; dx: number; nx: number; ny: number } | null } | null;
  pit_lane?: { fractions: number[]; parts: PitLaneJson['parts'] } | null;
  paved_zones?: { fractions: number[]; parts: PitLaneJson['parts'] } | null;
  /** raised sausage kerbs (physics: src/physics/track.ts) */
  sausages?: SausageJson | null;
  /** kerb strips; raised only with a `profile` (physics: src/physics/track.ts KerbsJson) */
  kerbs?: KerbsJson | null;
  /** terrain override regions (physics: src/physics/track.ts TerrainOverrideJson; Sonoma round 14A) */
  terrain_override?: TerrainOverrideJson | null;
}

/** ghosts.json fields the sim uses. */
export interface GhostsLike {
  s_grid_m: number;
  line: { offset_m: number[] };
  laps: { id: string; kind?: string; lap_time_s?: number; v_mps: number[]; rpm?: number[] | null }[];
}

/** Everything the sim needs, already decoded. The browser has these from loadAssets(); the server reads them from disk. */
export interface SimAssets {
  trackId: string;
  carId: string;
  track: TrackJson;
  /** heightfield.bin as floats (nx·ny). */
  heightfield: Float32Array;
  /** car.json as parsed JSON (unmodified). */
  carJson: unknown;
  scenery: SceneryLike | null;
  /** far_heightfield.bin as floats, or null. */
  farHeightfield: Float32Array | null;
  ghosts: GhostsLike;
}

/** Driver input as read from the device, before quantisation. Shifts are latched by the caller since the last sample. */
export interface RawInput {
  steer: number; throttle: number; brake: number;
  handbrake?: boolean; shiftUp?: boolean; shiftDown?: boolean;
}

export const q = (x: number, lo: number, hi: number): number => {
  const v = Number.isFinite(x) ? x : 0;
  return Math.round(Math.max(lo, Math.min(hi, v)) * QUANT);
};

/** The fastest real ghost (GhostManager.fastestReal in src/app/ghosts.ts): the app's default schedule reference. */
export function defaultRefGhost(g: GhostsLike): string | null {
  let best: GhostsLike['laps'][number] | null = null;
  for (const l of g.laps) if (l.kind === 'real' && (!best || (l.lap_time_s ?? Infinity) < (best.lap_time_s ?? Infinity))) best = l;
  return (best ?? g.laps[0])?.id ?? null;
}

/** The track's last corner: the directed track.json corner with the largest s (Laguna: T11). */
export function lastCorner(track: TrackJson): { name: string; s: number } | null {
  let last: { name: string; s: number } | null = null;
  for (const c of track.corners ?? []) {
    if (!(c as { dir?: string | null }).dir) continue;
    if (!last || c.s > last.s) last = c;
  }
  return last;
}

/** The canonical start: ROLLING_START_BEFORE_LAST_CORNER_M before the last corner on the racing line (`lineOffset`,
 *  0 = centreline), at ROLLING_START_SPEED; a track without directed corners gets a standing start START_BACK_M back. */
export function canonicalReset(track: TrackJson, lineOffset: (s: number) => number = () => 0,
  start?: TrackInfo['start']): { pos: [number, number, number]; heading: number; speed: number } {
  if (start && 's_m' in start) {
    const p = lineToWorld(track, lineOffset, ((start.s_m % track.length_m) + track.length_m) % track.length_m);
    return { pos: [p.pos[0], p.pos[1], p.pos[2]], heading: p.heading, speed: start.speed };
  }
  // a named corner (Laguna: T11), else the last directed corner; the same arithmetic as before 20 Oct 2026
  const named = start ? (track.corners ?? []).find((c) => (c as { turn?: string | null }).turn === start.beforeCorner) ?? null : null;
  const lc = named ?? lastCorner(track);
  const before = start ? start.m : ROLLING_START_BEFORE_LAST_CORNER_M;
  const s = lc
    ? (lc.s - before + track.length_m) % track.length_m
    : (track.length_m - START_BACK_M) % track.length_m;
  const p = lineToWorld(track, lineOffset, s);
  return { pos: [p.pos[0], p.pos[1], p.pos[2]], heading: p.heading, speed: lc ? (start ? start.speed : ROLLING_START_SPEED) : 0 };
}

export interface HotlapSimOptions {
  autoShift?: boolean;
  /** Default: car.json brakes.abs.enabled. */
  abs?: boolean;
  /** Gear-schedule reference ghost id; undefined = defaultRefGhost(), null = none (rpm rules). */
  ref?: string | null;
  /** Record an InputTrace (client: true; replay: false). */
  record?: boolean;
}

/**
 * One car on one track, stepped at 1 kHz with input sampled on a 100 Hz grid.
 *
 * Determinism rules this class enforces (see docs/scoreboard.md): a fresh Vehicle and a fresh Surface on
 * every reset (Vehicle.reset() keeps some internal state and Surface.sample() caches the last station),
 * a private Surface that nothing else samples, stepIndex/simTime restarted at the reset, quantised input.
 */
export class HotlapSim {
  readonly spec: CarSpec;
  readonly physics: string;
  readonly timer: LapTimer;
  vehicle!: Vehicle;
  /** Private to the sim: do not sample it from rendering / HUD code (its station cache is part of the state). */
  surface!: Surface;
  readonly projector: { project(x: number, y: number): { s: number; lateral: number } };
  readonly collision: CollisionWorld;
  simTime = 0;
  /** Physics steps since the reset. */
  stepIndex = 0;
  /** Projected s at the last timing tick. */
  s = 0;

  /** Requested settings; applied at the next sample step (and recorded there). */
  autoShift: boolean;
  abs: boolean;
  private ref: string | null;
  /**
   * Hot-lap auto-launch: until this sim time the HotlapLoop drives (full throttle, `lineSteer`) and the reference
   * ghost's gear schedule is suspended so the kickdown rule picks the launch gear. The suspension is an ordinary
   * recorded reference change (`refs`), so a replay (launchUntil 0) reproduces it exactly. 0 = no launch (a race).
   */
  launchUntil = 0;
  private appliedRef: string | null | undefined = undefined;
  private schedule: GearSchedule | null = null;

  private readonly di: DriverInput = { steer: 0, throttle: 0, brake: 0, shiftUp: false, shiftDown: false, handbrake: false };
  /** Record the InputTrace. The race mode sets it false (races are not replayed; avoids the trace growing). */
  record: boolean;
  /**
   * Race mode: steps the vehicle in place of `vehicle.step(input, surface, STEP)` (the RaceDirector steps every car,
   * the player's with this input, then contacts). null = the plain hot-lap step. Not part of the replay.
   */
  stepVehicle: ((input: Readonly<DriverInput>) => void) | null = null;
  private rows: TraceRow[] = [];
  private refs: [number, string | null][] = [];
  private last: TraceRow | null = null;
  private resetInfo = { pos: [0, 0, 0] as [number, number, number], heading: 0, speed: 0 };
  /** The canonical rolling start this sim resets to (a copy): the replayer checks a trace's reset against it. */
  get start(): { pos: [number, number, number]; heading: number; speed: number } {
    return { pos: [...this.resetInfo.pos] as [number, number, number], heading: this.resetInfo.heading, speed: this.resetInfo.speed };
  }
  private readonly pitLane: PitLaneJson | null;
  private readonly far: { heightfield: Float32Array; x0: number; y0: number; dx: number; nx: number; ny: number } | null;
  private readonly lineOffsets: number[];
  /** Lost in the hills: the player far off the track (offtrack.ts) for OFFTRACK_HOLD_S of sim time is launched. */
  private readonly offTrackJudge: OffTrackJudge;
  private readonly offTrack = new OffTrackWatch();
  private offTrackLaunchAt = NaN;

  constructor(readonly assets: SimAssets, opts: HotlapSimOptions = {}) {
    const a = assets;
    this.spec = loadCarSpec(a.carJson);
    this.physics = physicsVersion(a.carJson, a.track.length_m, TRACKS[a.trackId]?.rev);
    const farGrid = a.scenery?.far?.heightfield;
    this.far = farGrid && a.farHeightfield
      ? { heightfield: a.farHeightfield, x0: farGrid.x0, y0: farGrid.y0, dx: farGrid.dx, nx: farGrid.nx, ny: farGrid.ny } : null;
    const pit = a.scenery?.pit_lane ?? null, zones = a.scenery?.paved_zones ?? null;
    this.pitLane = pit || zones
      ? { spacing_m: 1, fractions: (pit ?? zones)!.fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] }
      : null;
    this.projector = createTrackProjector(a.track);
    this.collision = createCollisionWorld(a.scenery ?? null, a.track);
    this.timer = new LapTimer(a.track.length_m);
    this.lineOffsets = a.ghosts.line?.offset_m ?? [];
    this.offTrackJudge = createOffTrackJudge(a.track, { farM: TRACKS[a.trackId]?.offTrackFarM ?? OFFTRACK_FAR_M, barriers: a.scenery?.barriers ?? null });
    this.autoShift = opts.autoShift ?? true;
    this.abs = opts.abs ?? this.spec.brakes.abs.enabled >= 0.5;
    this.ref = opts.ref === undefined ? defaultRefGhost(a.ghosts) : opts.ref;
    this.record = opts.record ?? false;
    this.reset();
  }

  /** Gear-schedule reference (applied at the next sample). Unknown ids fall back to none. */
  setRef(id: string | null): void { this.ref = id; }
  get refId(): string | null { return this.ref; }

  /** Rolling start: fresh vehicle + surface, timer and counters cleared, a new trace begins. */
  reset(): void {
    const a = this.assets;
    this.vehicle = new Vehicle(this.spec, { autoShift: this.autoShift });
    this.vehicle.abs = this.abs;
    this.vehicle.setCollisionWorld(this.collision);
    this.surface = createTrackSurface(a.track, a.heightfield, { far: this.far, pitLane: this.pitLane, sausages: a.scenery?.sausages ?? null, kerbs: a.scenery?.kerbs ?? null, terrainOverride: a.scenery?.terrain_override ?? null });
    const r = canonicalReset(a.track, (s) => this.lineOffsetAt(s), TRACKS[a.trackId]?.start);
    this.vehicle.reset(r.pos, r.heading, r.speed);
    this.resetInfo = r;
    this.timer.reset();
    this.simTime = 0; this.stepIndex = 0; this.s = 0;
    this.appliedRef = undefined; this.schedule = null;
    this.rows = []; this.refs = []; this.last = null;
    this.offTrack.reset(); this.offTrackLaunchAt = NaN;
  }

  private applyRef(): void {
    let want = this.simTime < this.launchUntil ? null : this.ref;   // the launch suspends the schedule
    if (this.appliedRef === want) return;
    const lap = want === null ? null : this.assets.ghosts.laps.find((l) => l.id === want) ?? null;
    if (!lap && want !== null) { this.ref = null; want = null; }
    if (this.appliedRef === want) return;
    this.appliedRef = want;
    this.schedule = lap && lap.rpm && lap.rpm.length ? deriveGearSchedule(this.spec, lap, this.assets.ghosts.s_grid_m) : null;
    if (this.record) this.refs.push([this.stepIndex, want]);
  }

  /**
   * Steer (DriverInput.steer, -1..1) that follows the racing line: pure pursuit on a point 8-30 m ahead (0.8 s at
   * the current speed). The hot-lap auto-launch (HotlapLoop.launchUntil) drives with it at full throttle.
   */
  lineSteer(): number {
    const st = this.vehicle.state, L = this.assets.track.length_m;
    const pr = this.projector.project(st.pos[0], st.pos[1]);
    const look = Math.min(32, Math.max(10, 0.7 * Math.abs(st.speed)));
    const tgt = lineToWorld(this.assets.track, (s) => this.lineOffsetAt(s), (((pr.s + look) % L) + L) % L);
    const [qx, qy, qz, qw] = st.quat;
    const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    let a = Math.atan2(tgt.pos[1] - st.pos[1], tgt.pos[0] - st.pos[0]) - yaw;
    a = Math.atan2(Math.sin(a), Math.cos(a));
    const delta = Math.atan2(2 * this.spec.wheelbase * Math.sin(a), look);
    // the vehicle shapes the input by a speed-dependent maximum angle (Vehicle.step steering shaping): command
    // against the same limit so the road-wheel angle is the one pure pursuit asked for
    const sp = this.spec.steering, v = Math.abs(st.speed), vr = v / sp.shapingSpeed;
    const maxA = Math.max((sp.minAngleDeg * Math.PI) / 180, ((sp.maxAngleDeg * Math.PI) / 180) / (1 + vr * vr));
    return Math.max(-1, Math.min(1, delta / maxA));
  }

  private lineOffsetAt(s: number): number {
    const o = this.lineOffsets, g = this.assets.ghosts.s_grid_m, L = this.assets.track.length_m;
    if (!o.length) return 0;
    const u = (((s % L) + L) % L) / g, i = Math.floor(u), f = u - i;
    return o[i % o.length] * (1 - f) + o[(i + 1) % o.length] * f;
  }

  /** The quantised input in force (read-only view, for HUD/audio). */
  get input(): Readonly<DriverInput> { return this.di; }

  /** True on steps where step() will call its sampler. */
  get sampleDue(): boolean { return this.stepIndex % SAMPLE_EVERY === 0; }

  /**
   * One physics step. On every SAMPLE_EVERY-th step `sample()` is called for the driver's input, which is
   * quantised, recorded and held for the next SAMPLE_EVERY steps. Returns the lap timer's event.
   */
  step(sample: () => RawInput): 'start' | Lap | null {
    const di = this.di;
    if (this.stepIndex % SAMPLE_EVERY === 0) {
      const raw = sample();
      this.applyRef();
      const flags = (raw.shiftUp ? FLAG_SHIFT_UP : 0) | (raw.shiftDown ? FLAG_SHIFT_DOWN : 0) | (raw.handbrake ? FLAG_HANDBRAKE : 0)
        | (this.autoShift ? FLAG_AUTOSHIFT : 0) | (this.abs ? FLAG_ABS : 0);
      const row: TraceRow = [this.stepIndex, q(raw.steer, -1, 1), q(raw.throttle, 0, 1), q(raw.brake, 0, 1), flags];
      this.applyRow(row, true);
      if (this.record) {
        const l = this.last;
        if (!l || l[1] !== row[1] || l[2] !== row[2] || l[3] !== row[3] || l[4] !== row[4]) this.rows.push(row);
        this.last = row;
      }
    }
    return this.advance();
  }

  /** Apply a (decoded) trace row: used by step() and by the replayer. `edge` = this step carries the row's shift pulses. */
  applyRow(row: TraceRow, edge: boolean): void {
    const di = this.di, f = row[4];
    di.steer = row[1] / QUANT; di.throttle = row[2] / QUANT; di.brake = row[3] / QUANT;
    di.handbrake = (f & FLAG_HANDBRAKE) !== 0;
    di.shiftUp = edge && (f & FLAG_SHIFT_UP) !== 0;
    di.shiftDown = edge && (f & FLAG_SHIFT_DOWN) !== 0;
    this.autoShift = (f & FLAG_AUTOSHIFT) !== 0;
    this.abs = (f & FLAG_ABS) !== 0;
    this.vehicle.autoShift = this.autoShift;
    this.vehicle.abs = this.abs;
  }

  /** Replayer hook: set the reference at a sample step exactly as recorded. */
  replayRef(id: string | null): void { this.ref = id; this.applyRef(); }

  /** The physics step + timing tick (src/app/index.ts physicsStep). */
  advance(): 'start' | Lap | null {
    const di = this.di, v = this.vehicle;
    if (this.stepVehicle) this.stepVehicle(di); else v.step(di, this.surface, STEP);
    di.shiftUp = false; di.shiftDown = false;
    this.stepIndex++;
    if (v.state.launched) return null; // lap timer stops
    this.simTime += STEP;
    if (this.stepIndex % TIMING_EVERY !== 0) return null;
    const st = v.state;
    const pr = this.projector.project(st.pos[0], st.pos[1]);
    this.s = pr.s;
    const onLine = this.schedule !== null && Math.abs(pr.lateral - this.lineOffsetAt(pr.s)) < 15 && st.speed > 2;
    v.setScheduledGear(onLine ? scheduleTargetAt(this.schedule!, pr.s) : 0);
    let allOff = true;
    for (const w of st.wheels) {
      if (w.onTrack || this.surface.sample(w.pos[0], w.pos[1]).paved) { allOff = false; break; }
    }
    // lost in the hills (src/physics/offtrack.ts): every wheel off any pavement and the car far off the track (past the
    // local limit or off the near heightfield), held for OFFTRACK_HOLD_S of sim time: launched like a hard wall hit
    const far = allOff && this.offTrackJudge.far(st.pos[0], st.pos[1]);
    if (this.offTrack.update(far, STEP * TIMING_EVERY)) {
      this.offTrackLaunchAt = v.launchIntoSpace(this.offTrackJudge.away.x, this.offTrackJudge.away.y);
      this.offTrack.reset();   // re-armed for a car put back on the road (race recovery resets the vehicle in place)
    }
    return this.timer.update(this.simTime, pr.s, Math.abs(st.speed), allOff, STEP * TIMING_EVERY);
  }

  /** True while the player's car is in space because it got lost in the hills (not after a wall hit). */
  get launchedOffTrack(): boolean {
    const st = this.vehicle.state;
    return !!st.launched && st.launchedAt === this.offTrackLaunchAt;
  }

  /** The trace recorded since the last reset (a copy; call it when the lap you want to submit completes). */
  trace(): InputTrace {
    const a = this.assets;
    return {
      v: TRACE_FORMAT, physics: this.physics, track: a.trackId, car: a.carId, hz: 1 / (STEP * SAMPLE_EVERY), dt: STEP,
      reset: { pos: [...this.resetInfo.pos] as [number, number, number], heading: this.resetInfo.heading, speed: this.resetInfo.speed },
      ref: this.refs.map((r) => [r[0], r[1]] as [number, string | null]),
      rows: this.rows.map((r) => [...r] as TraceRow),
      steps: this.stepIndex,
    };
  }
}
