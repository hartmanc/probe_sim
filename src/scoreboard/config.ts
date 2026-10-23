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

/** Rolling start (HotlapSim.canonicalReset): this far before the track's last corner (the last track.json corner with a
 *  direction; Laguna's T11 hairpin) at this speed, on the racing line (230 m since 17 Oct 2026, was 130 m on the
 *  centreline: the hot lap now launches itself for LAUNCH_S first). */
export const ROLLING_START_BEFORE_LAST_CORNER_M = 230;
export const ROLLING_START_SPEED = 22;
/** Hot-lap auto-launch (owner, 17 Oct 2026): for this long after the rolling start the car drives itself at full
 *  throttle along the racing line while the HUD counts 3-2-1, then the driver takes over. The launch inputs go
 *  through the normal 100 Hz sample path, so a trace replays them like any other input. */
export const LAUNCH_S = 3;
/** Fallback when the track has no directed corner: standing start this far behind the line. */
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

/** One circuit. Paths are relative to public/ (client fetch base and server file root). */
export interface TrackInfo {
  /** track package directory: track.json, heightfield.bin, ortho.jpg, ghosts.json, scenery.json, far_* */
  dir: string;
  /** full name (track.json `name`) */
  name: string;
  /** short name for titles and captions */
  short: string;
  /** track.json length_m (feeds physicsVersion and the race metres check) */
  length_m: number;
  /** the race field's per-stint pace for this circuit (tools/race/pace.ts, calibrate_field.ts) */
  pace: string;
  /** The rolling start of hot laps and replays (canonicalReset), an explicit fact of the track: either a distance before a
   *  named corner (Laguna: 230 m before T11, the rule its boards were recorded with) or a station in metres along the lap,
   *  and the speed. Part of every replay: changing it changes the board key's meaning. */
  start: { beforeCorner: string; m: number; speed: number } | { s_m: number; speed: number };
  /** Per-track AI race parameters (RaceConfig): followScale multiplies the racing time headway, laneMargin the grip share of
   *  a pass lane's own path (absent = 1, Laguna), shiftGrip caps lane changes by the spare lateral grip (absent = 0 = off). */
  ai?: { followScale?: number; laneMargin?: number; shiftGrip?: number };
  /** Revision of the published package: sha256 over the sha256 of track.json, heightfield.bin, ghosts.json, scenery.json
   *  and far_heightfield.bin, first 10 hex (the registry test checks it), part of physicsVersion() and so
   *  of the board key: a rebuilt package opens its own boards without a global PHYSICS_VERSION bump. Laguna has none
   *  (its key is unchanged since 0.2.0). */
  rev?: string;
  /** "Far off the track" for the lost-in-the-hills launch, m past the nearer track edge (absent = OFFTRACK_FAR_M, 40 m,
   *  src/physics/offtrack.ts). Only the player's car; outside the near heightfield always counts as far. */
  offTrackFarM?: number;
}

/** The track registry: every circuit the app, the scoreboard server and the tools know (whitelist). A new track gets an
 *  entry here (built by tools/track/build_track.py, see the build-track skill) and a pace file of its own under
 *  cars/field/<id>/pace.json; Laguna's predates that and stays at cars/field/pace.json. */
export const TRACKS: Readonly<Record<string, TrackInfo>> = {
  laguna_seca: { dir: 'tracks/laguna_seca/', name: 'WeatherTech Raceway Laguna Seca', short: 'Laguna Seca', length_m: 3588.048, pace: 'cars/field/pace.json',
    start: { beforeCorner: 'T11', m: ROLLING_START_BEFORE_LAST_CORNER_M, speed: ROLLING_START_SPEED } },
  sonoma: { dir: 'tracks/sonoma/', name: 'Sonoma Raceway', short: 'Sonoma', length_m: 4098.5, pace: 'cars/field/sonoma/pace.json', rev: '1d38e06899',
    // on the front straight, ~120 m before the line (230 m before the last corner, T12, was 26 m past the T11 apex)
    start: { s_m: 3975, speed: ROLLING_START_SPEED },
    // 20 Oct 2026, 8 seeds of 4 laps: AI-AI contacts 91 at the Laguna headways, 57 at x1.4, 51 at x1.8 (the rest are passes);
    // 16 seeds of 4 laps with kerbs: shiftGrip 1 contacts 0.047 -> 0.033, four-off 0.094 -> 0.031 (spins in the esses);
    // laneMargin 0.85 on top 0.025 / 0.019 (inside passes at T4, T11); passes 73.0 -> 73.5 %
    ai: { followScale: 1.4, laneMargin: 0.85, shiftGrip: 1 } },
};
/** The track when none is chosen (URL ?track=, Start menu). */
export const DEFAULT_TRACK = 'laguna_seca';

/** A registered track id, or the default for anything else (unknown ids fall back rather than break the page). */
export function resolveTrackId(id: string | null | undefined): string {
  return id && Object.prototype.hasOwnProperty.call(TRACKS, id) ? id : DEFAULT_TRACK;
}
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
