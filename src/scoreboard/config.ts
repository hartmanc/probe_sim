// Scoreboard constants shared by the client and the server (docs/scoreboard.md).
// Pure TS: no DOM, no Node built-ins.

/**
 * Bump whenever anything that changes a replay changes without changing car.json or the track length:
 * src/physics code, track.json geometry/profile, heightfield.bin, scenery.json (walls, pit lane, paved zones,
 * far terrain), ghosts.json (gear schedules, line offsets) or the sim loop in src/scoreboard/sim.ts.
 * It feeds physicsVersion(), so a bump also opens fresh boards.
 */
export const PHYSICS_VERSION = 'probe-sim-2026-10-18-edges';

/** Input-trace format version (InputTrace.v). */
export const TRACE_FORMAT = 1;

/** Physics step, s (1000 Hz). */
export const STEP = 0.001;
/** Input sampling grid: one sample every SAMPLE_EVERY physics steps (100 Hz), held between samples. */
export const SAMPLE_EVERY = 10;
/** Timing / off-track / gear-schedule work every TIMING_EVERY steps (200 Hz), as src/app/index.ts. */
export const TIMING_EVERY = 5;
/** Quantisation of steer / throttle / brake: integers in thousandths. */
export const QUANT = 1000;

/** Rolling start (HotlapSim.canonicalReset): this far before the T11 hairpin at this speed, on the racing line
 *  (230 m since 17 Oct 2026, was 130 m on the centreline: the hot lap now launches itself for LAUNCH_S first). */
export const ROLLING_START_BEFORE_T11_M = 230;
export const ROLLING_START_SPEED = 22;
/** Hot-lap auto-launch (owner, 17 Oct 2026): for this long after the rolling start the car drives itself at full
 *  throttle along the racing line while the HUD counts 3-2-1, then the driver takes over. The launch inputs go
 *  through the normal 100 Hz sample path, so a trace replays them like any other input. */
export const LAUNCH_S = 3;
/** Fallback when the track has no T11: standing start this far behind the line. */
export const START_BACK_M = 25;

/** Trace flag bits. shiftUp/shiftDown are one-sample pulses; the others are held states. */
export const FLAG_SHIFT_UP = 1;
export const FLAG_SHIFT_DOWN = 2;
export const FLAG_HANDBRAKE = 4;
export const FLAG_AUTOSHIFT = 8;
export const FLAG_ABS = 16;
export const FLAG_MASK = 31;

export type Mode = 'hotlap' | 'race';
export const MODES: readonly Mode[] = ['hotlap', 'race'];
export type InputType = 'pad' | 'keys' | 'phone';
export const INPUT_TYPES: readonly InputType[] = ['pad', 'keys', 'phone'];

/** Whitelisted tracks. `dir` is relative to public/ (client fetch base and server file root). */
export const TRACKS: Readonly<Record<string, { dir: string; length_m: number }>> = {
  laguna_seca: { dir: 'tracks/laguna_seca/', length_m: 3588.048 },
};
/** Whitelisted cars. */
export const CARS: Readonly<Record<string, { dir: string }>> = {
  probe_gt: { dir: 'cars/probe_gt/' },
};

export const LIMITS = {
  /** Entries returned by GET. */
  top: 10,
  /** Entries kept per board. */
  keep: 100,
  nameMax: 12,
  /** Hot lap: 90 s < time < 600 s. */
  lapMin: 90,
  lapMax: 600,
  /** |replayed − claimed| lap time tolerance, s. */
  replayTolerance: 0.05,
  /** Highest lap number a hot-lap submission may claim (the trace runs from the reset to that lap's end). */
  maxLap: 6,
  /** Longest trace, physics steps (720 s: rolling start + 6 slow laps). */
  maxTraceSteps: 720_000,
  /** Most trace rows (one per 100 Hz sample at worst). */
  maxTraceRows: 72_001,
  /** Request body cap, bytes. */
  maxBodyBytes: 2_500_000,
  /** Race: laps and the slack on the metres check, m. */
  raceLaps: 5,
  raceMarginM: 250,
  /** Race boards rank finish time; a car classified short is ranked by distance, encoded above this base so one
   *  ascending sorted set orders both (see validate.ts raceScore). */
  raceDnfBase: 1_000_000,
  /** Rate limit: posts per window per IP. */
  ratePosts: 10,
  rateWindowS: 600,
} as const;
