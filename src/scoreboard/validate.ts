// Plausibility rules for submissions (server-authoritative; the client may run them to pre-check).
// Pure TS.
import { CARS, INPUT_TYPES, LIMITS, MODES, TRACKS, type Mode } from './config';
import { checkTrace } from './replay';
import type { HotlapSubmission, RaceSubmission, Submission } from './types';

export interface Validation<T> { ok: boolean; reasons: string[]; value?: T }

/**
 * Normalise a display name: NFC, whitespace runs collapsed to one space, trimmed. Returns null when it is
 * empty, longer than 12 characters (code points) or contains control / format / unassigned / private-use
 * characters or non-space separators.
 */
export function normalizeName(raw: unknown): string | null {
  if (typeof raw !== 'string' || raw.length > 200) return null;
  const s = raw.normalize('NFC').replace(/[ \t]+/g, ' ').trim();
  if (!s || [...s].length > LIMITS.nameMax) return null;
  if (/[\p{C}\p{Zl}\p{Zp}]/u.test(s) || /[^\S ]/u.test(s)) return null;
  return s;
}

/** Board member id for a name: case-insensitive, so "Coby" and "coby" share one entry. */
export const nameKey = (name: string): string => name.toLocaleLowerCase('en-US');

const ID_RE = /^[a-z0-9_]{1,32}$/;
const AI_RE = /^[A-Za-z0-9._-]{1,32}$/;

/** Board key: hotlap:<track>:<car>:<physics>  |  race:<track>:<car>:<physics>:<ai_version>. */
export function boardKey(mode: Mode, track: string, car: string, physics: string, aiVersion?: string): string {
  return mode === 'race' ? `race:${track}:${car}:${physics}:${aiVersion}` : `hotlap:${track}:${car}:${physics}`;
}

export function parseBoardKey(key: unknown): { mode: Mode; track: string; car: string; physics: string; ai_version?: string } | null {
  if (typeof key !== 'string' || key.length > 160) return null;
  const p = key.split(':');
  const [mode, track, car, physics, ai] = p;
  if (!(MODES as readonly string[]).includes(mode)) return null;
  if (!Object.hasOwn(TRACKS, track) || !Object.hasOwn(CARS, car) || !/^[0-9a-z]{1,32}$/.test(physics ?? '')) return null;
  if (mode === 'hotlap' && p.length === 4) return { mode, track, car, physics };
  if (mode === 'race' && p.length === 5 && AI_RE.test(ai)) return { mode, track, car, physics, ai_version: ai };
  return null;
}

/** Ascending boards (lower is better) vs descending. */
/** Both boards sort ascending: hot-lap time, and the race score below (finish time, then distance). */
export const lowerIsBetter = (_mode: Mode): boolean => true;

/** Race score for the sorted set: finish time for a finished race, else distance encoded above LIMITS.raceDnfBase
 *  (max metres - metres, so more distance sorts first). Lower is better. */
export function raceScore(s: { finished?: boolean; time?: number; metres: number }, trackLength: number): number {
  if (s.finished && typeof s.time === 'number') return Math.round(s.time * 1000) / 1000;
  const maxM = LIMITS.raceLaps * trackLength + LIMITS.raceMarginM;
  return LIMITS.raceDnfBase + Math.round(Math.max(0, maxM - s.metres) * 100) / 100;
}
/** Inverse for display: the finish time, or the metres of a car classified short. */
export function raceScoreView(score: number, trackLength: number): { time: number } | { metres: number } {
  if (score < LIMITS.raceDnfBase) return { time: score };
  return { metres: Math.max(0, LIMITS.raceLaps * trackLength + LIMITS.raceMarginM - (score - LIMITS.raceDnfBase)) };
}

/**
 * Plausibility checks on a parsed POST body. `serverPhysics` is the server's physicsVersion() for the
 * submission's track + car (undefined when unknown). Does not replay; see verifyHotlap().
 */
export function validateSubmission(body: unknown, serverPhysics?: (track: string, car: string) => string | undefined): Validation<Submission> {
  const r: string[] = [];
  if (!body || typeof body !== 'object' || Array.isArray(body)) return { ok: false, reasons: ['body must be a JSON object'] };
  const b = body as Record<string, unknown>;
  const mode = b.mode as Mode;
  if (!(MODES as readonly string[]).includes(mode as string)) r.push('mode must be hotlap or race');
  const track = b.track, car = b.car;
  if (typeof track !== 'string' || !ID_RE.test(track) || !Object.hasOwn(TRACKS, track)) r.push('unknown track');
  if (typeof car !== 'string' || !ID_RE.test(car) || !Object.hasOwn(CARS, car)) r.push('unknown car');
  if (typeof b.physics !== 'string' || !/^[0-9a-z]{1,32}$/.test(b.physics)) r.push('physics version missing');
  else if (serverPhysics && typeof track === 'string' && typeof car === 'string' && Object.hasOwn(TRACKS, track) && Object.hasOwn(CARS, car)) {
    const sp = serverPhysics(track, car);
    if (sp !== undefined && sp !== b.physics) r.push('physics version mismatch: reload the game');
  }
  const name = normalizeName(b.name);
  if (name === null) r.push(`name must be 1-${LIMITS.nameMax} printable characters`);
  if (!(INPUT_TYPES as readonly string[]).includes(b.input as string)) r.push('input must be pad, keys or phone');
  if (b.device !== undefined && (typeof b.device !== 'string' || !/^[A-Za-z0-9-]{1,64}$/.test(b.device))) r.push('device malformed');

  if (mode === 'hotlap') {
    const t = b.time;
    if (typeof t !== 'number' || !Number.isFinite(t) || !(t > LIMITS.lapMin && t < LIMITS.lapMax)) r.push(`time must be between ${LIMITS.lapMin} and ${LIMITS.lapMax} s`);
    if (b.valid !== true) r.push('lap is not valid');
    if (typeof b.lap !== 'number' || !Number.isInteger(b.lap) || b.lap < 1 || b.lap > LIMITS.maxLap) r.push(`lap must be 1..${LIMITS.maxLap}`);
    if (b.trace === undefined || b.trace === null) r.push('trace missing');
    else {
      r.push(...checkTrace(b.trace));
      const tr = b.trace as { physics?: unknown; track?: unknown; car?: unknown };
      if (tr.physics !== b.physics || tr.track !== track || tr.car !== car) r.push('trace does not match the submission (physics/track/car)');
    }
  } else if (mode === 'race') {
    if (typeof b.ai_version !== 'string' || !AI_RE.test(b.ai_version)) r.push('ai_version missing');
    const L = typeof track === 'string' && Object.hasOwn(TRACKS, track) ? TRACKS[track].length_m : 0;
    const m = b.metres, laps = b.laps;
    const maxM = LIMITS.raceLaps * L + LIMITS.raceMarginM;
    if (typeof m !== 'number' || !Number.isFinite(m) || !(m > 0 && m <= maxM)) r.push(`metres must be > 0 and <= ${maxM}`);
    if (typeof laps !== 'number' || !Number.isInteger(laps) || laps < 0 || laps > LIMITS.raceLaps) r.push(`laps must be 0..${LIMITS.raceLaps}`);
    else if (typeof m === 'number' && L > 0 && (m < laps * L - LIMITS.raceMarginM || m > (laps + 1) * L + LIMITS.raceMarginM)) r.push('laps inconsistent with metres');
    if (b.position !== undefined && (typeof b.position !== 'number' || !Number.isInteger(b.position) || b.position < 1 || b.position > 64)) r.push('position malformed');
    if (b.finished !== undefined && typeof b.finished !== 'boolean') r.push('finished malformed');
    if (b.finished === true && laps !== LIMITS.raceLaps) r.push('finished requires all laps');
    const tm = b.time;
    const tMin = LIMITS.raceLaps * LIMITS.lapMin, tMax = LIMITS.raceLaps * LIMITS.lapMax;
    if (b.finished === true) {
      if (typeof tm !== 'number' || !Number.isFinite(tm) || !(tm > tMin && tm < tMax)) r.push(`finished requires a race time between ${tMin} and ${tMax} s`);
    } else if (tm !== undefined && tm !== null) r.push('time only with a finished race');
  }
  if (r.length) return { ok: false, reasons: r };
  const value = { ...(b as object), name } as Submission;
  delete (value as { secret?: unknown }).secret;   // checked by the handler (owner.ts), never stored
  if (value.mode === 'race') delete (value as RaceSubmission).replay; // reserved; not stored yet
  return { ok: true, reasons: [], value };
}

export type { HotlapSubmission, RaceSubmission };
