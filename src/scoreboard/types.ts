// Scoreboard wire types (docs/scoreboard.md). Shared by the client and api/scores.ts.
import type { InputType, Mode } from './config';
export type { InputType, Mode } from './config';

/**
 * One input row, all integers: [stepIndex, steer, throttle, brake, flags].
 * stepIndex is a multiple of SAMPLE_EVERY (10) counted from the reset; steer is −1000..1000
 * (+ = left), throttle and brake 0..1000 (thousandths); flags = FLAG_* bits.
 * A row is written only when a value differs from the previous row; values hold until the next row,
 * except the shift bits, which act only on the step of the row that carries them.
 */
export type TraceRow = [number, number, number, number, number];

/** Deterministic hot-lap input trace: everything the server needs to re-run the lap. */
export interface InputTrace {
  /** TRACE_FORMAT */
  v: number;
  /** physicsVersion(car.json, track length) of the client that recorded it. */
  physics: string;
  track: string;
  car: string;
  /** Samples per second (100) and physics step (0.001); informative, the server uses its own constants. */
  hz: number;
  dt: number;
  /** The reset the recording started from (the canonical rolling start; checked by the server). */
  reset: { pos: [number, number, number]; heading: number; speed: number };
  /** Gear-schedule reference ghost id (ghosts.json lap id) per step: [[0, id], [step, id], …]; null = rpm rules. */
  ref: [number, string | null][];
  rows: TraceRow[];
  /** Physics steps recorded since the reset (the step at which the submission was built). */
  steps: number;
}

interface SubmissionBase {
  mode: Mode;
  track: string;
  car: string;
  /** physicsVersion() the client computed; must equal the server's. */
  physics: string;
  name: string;
  input: InputType;
  /** Optional random per-browser id (localStorage); stored for moderation, not shown. */
  device?: string;
  /** The device secret (32 hex, owner.ts): required by the server, checked against the name's owner, never stored. */
  secret?: string;
}

export interface HotlapSubmission extends SubmissionBase {
  mode: 'hotlap';
  /** Claimed lap time, s. */
  time: number;
  /** Lap number (LapTimer Lap.n) the time belongs to. */
  lap: number;
  /** LapTimer Lap.valid; must be true. */
  valid: boolean;
  trace: InputTrace;
}

export interface RaceSubmission extends SubmissionBase {
  mode: 'race';
  /** Race AI version (src/physics/ai); part of the board key. */
  ai_version: string;
  /** Distance covered in the race, m (the score; higher is better). */
  metres: number;
  /** Laps completed (0..LIMITS.raceLaps). */
  laps: number;
  /** Race time, s from the green flag to the crossing that completed the last lap. Required when finished; it is the score. */
  time?: number;
  /** Finishing position, 1-based (optional, informative). */
  position?: number;
  finished?: boolean;
  /** Reserved for a future replay of the race; ignored today. */
  replay?: unknown;
}

export type Submission = HotlapSubmission | RaceSubmission;

/** A stored / returned board entry. */
export interface Score {
  rank: number;      // 1-based
  name: string;
  /** Hot lap: lap time s. Race: finish time s for a finished race, else LIMITS.raceDnfBase + (max metres - metres)
   *  for a car classified short (validate.ts raceScore / raceScoreView). Lower is better in both. */
  score: number;
  input: InputType;
  /** ISO date of the submission. */
  at: string;
  ai_version?: string;
  laps?: number;
}

export interface Board {
  /** Board key (boardKey()). */
  board: string;
  mode: Mode;
  entries: Score[];
  /** Present when GET asked for ?name= and that name is on the board. */
  you?: Score | null;
}

export interface SubmitResult {
  ok: true;
  board: string;
  /** Rank of the submitted name on the board after the insert (1-based), null if trimmed off. */
  rank: number | null;
  /** The score the server stored for this name (best of old and new). */
  best: number;
  /** True when this submission improved the name's entry. */
  improved: boolean;
  /** Hot lap: the replayed lap time that was stored. */
  replayed?: number;
}

export interface ApiError {
  ok: false;
  error: string;
  reasons?: string[];
}
