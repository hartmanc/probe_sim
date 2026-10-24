// Structural mirror of the physics API in CONTRACTS.md §4.
// The app codes against these interfaces so it works with either the real
// module (src/physics) or the kinematic stub (physics-stub.ts).

export type Vec3 = [number, number, number];

export interface SurfaceSample {
  z: number; nx: number; ny: number; nz: number; onTrack: boolean; mu: number; paved?: boolean;
  /** 0 on pavement → 1 fully off it (blended over the first metre past the paved edge). */
  dirt?: number;
  /** Friction multiplier of the pavement. */
  muPaved?: number;
}
export interface Surface { sample(x: number, y: number): SurfaceSample }

export interface DriverInput {
  steer: number;      // -1..1, positive = left
  throttle: number;   // 0..1
  brake: number;      // 0..1
  shiftUp: boolean;   // edge-triggered (true for one step)
  shiftDown: boolean;
  handbrake?: boolean;
}

export interface WheelState {
  pos: Vec3;
  spinAngle: number;
  steer: number;
  compression: number;
  omega: number;
  slipRatio: number; slipAngle: number; load: number; onTrack: boolean;
  /** Combined slip / tyre peak (1 = at the peak), real physics only. */
  slipUse?: number;
  /** On pavement (track, pit lane, paved runoff) this step, from the surface under the wheel. Real physics + stub. */
  paved?: boolean;
  /** Friction multiplier the tyre used this step. */
  mu?: number;
}

export interface VehicleState {
  pos: Vec3;
  quat: [number, number, number, number];
  vel: Vec3;
  angVel: Vec3;
  wheels: [WheelState, WheelState, WheelState, WheelState];
  rpm: number; gear: number;
  speed: number;
  gLat: number; gLong: number;
  throttleOut: number;
  /** Last barrier / building / tree impact (real physics only). */
  impact?: { speedNormal: number;
  /** The car's own speed at the impact, m/s (shown on the game-over card; the stub physics may omit it). */
  speed?: number; kind: string; t: number } | null;
  /** Blasted into space after a hard wall hit (real physics only). */
  launched?: boolean;
  launchedAt?: number;
  /** ABS modulating a channel (real physics only). */
  absActive?: boolean;
}

export interface VehicleLike {
  readonly state: VehicleState;
  autoShift: boolean;
  reset(pos: Vec3, headingRad: number, speed?: number): void;
  step(input: DriverInput, surface: Surface, dt: number): void;
  /** Real physics only: autoShift follows this scheduled gear (0 = rpm rules). */
  setScheduledGear?(g: number): void;
  /** Real physics only: ABS fitted and switched on. */
  abs?: boolean;
  /** Real physics only: attach the collision world from createCollisionWorld. */
  setCollisionWorld?(cw: unknown): void;
}

/** Pit lane (scenery.json `pit_lane`, CONTRACTS §2b): open parts with the track's centre/left/right/profile layout. */
/** Kerb strips (scenery.json `kerbs`); raised only with a `profile` (see src/physics/track.ts KerbsJson). */
export interface KerbsJson {
  width: number; inside?: boolean; profile?: { height: number; face: number; back: number } | null;
  strips: { side: number; s0: number; s1: number; kind?: string; off?: number }[];
}

/** Raised sausage kerbs (scenery.json `sausages`, see src/physics/track.ts SausageJson). */
export interface SausageJson {
  width: number; height: number; gap: number; kerb_width: number;
  strips: { side: number; s0: number; s1: number; corner?: string }[];
}

export interface PitLaneJson {
  spacing_m: number;
  fractions: number[];
  parts: { n: number; center: Vec3[]; left: Vec3[]; right: Vec3[]; profile_z: number[][] }[];
}

/** Far heightfield passed to createTrackSurface (scenery.json far.heightfield grid + data). */
/** Terrain override regions (scenery.json `terrain_override`, see src/physics/track.ts TerrainOverrideJson). */
export interface TerrainOverrideJson { regions: { name?: string; ramp: number; poly: number[][] }[] }

export interface FarHeightfield { heightfield: Float32Array; x0: number; y0: number; dx: number; nx: number; ny: number }

export interface TrackCorner { name: string; s: number; turn?: string | null; dir?: string | null; radius_m?: number | null }

export interface TrackJson {
  name: string;
  origin: { lat: number; lon: number };
  z0_navd88: number;
  direction: string;
  spacing_m: number;
  n: number;
  length_m: number;
  center: Vec3[];
  left: Vec3[];
  right: Vec3[];
  profile: { fractions: number[]; z: number[][] };
  start_finish: { index: number };
  corners: TrackCorner[];
  heightfield: { file: string; x0: number; y0: number; dx: number; nx: number; ny: number };
  ortho: { file: string; x0: number; y0: number; x1: number; y1: number; width_px: number; height_px: number };
  sources?: string;
}

export interface TrackProjector { project(x: number, y: number): { s: number; lateral: number; index: number } }

export interface GhostLap {
  id: string; driver: string; label: string;
  kind: 'real' | 'optimal' | string;
  lap_time_s: number;
  t: number[]; v_mps: number[]; rpm?: number[]; throttle?: number[];
}
export interface GhostsJson {
  track: string;
  s_grid_m: number;
  line: { offset_m: number[] };
  laps: GhostLap[];
}

/** What the app needs from a physics module (methods so parameter types are bivariant). */
export interface PhysicsApi {
  Vehicle: new (spec: any, opts?: { autoShift?: boolean }) => VehicleLike;
  loadCarSpec(json: unknown): unknown;
  createTrackSurface(track: TrackJson, heightfield: Float32Array, opts?: { far?: FarHeightfield | null; pitLane?: PitLaneJson | null; sausages?: SausageJson | null; kerbs?: KerbsJson | null; terrainOverride?: TerrainOverrideJson | null }): Surface;
  /** Real physics only: static collision world from scenery.json (null scenery → boundary only). */
  createCollisionWorld?(scenery: unknown, track: TrackJson): unknown;
  /** Real physics only: the gear a ghost used at every grid point (from its rpm and speed channels). */
  deriveGearSchedule?(spec: any, lap: GhostLap, grid?: number): unknown;
  /** Real physics only: scheduled gear at s with a few metres of hysteresis. */
  scheduleTargetAt?(schedule: any, s: number, lag?: number): number;
  createTrackProjector(track: TrackJson): TrackProjector;
  lineToWorld(track: TrackJson, offsetAtS: (s: number) => number, s: number): { pos: Vec3; heading: number };
}
