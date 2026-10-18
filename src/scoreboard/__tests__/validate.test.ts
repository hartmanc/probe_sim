import { describe, expect, test } from 'vitest';
import { boardKey, normalizeName, parseBoardKey, validateSubmission, nameKey } from '../validate';
import { physicsVersion, canonicalJson } from '../hash';
import type { InputTrace } from '../types';
import { TRACKS } from '../config';

/** 5 laps of the registry's Laguna Seca length (the race distance the metres rule is built on) */
const FIVE_LAPS = Math.round(5 * TRACKS.laguna_seca.length_m);

const trace = (over: Partial<InputTrace> = {}): InputTrace => ({
  v: 1, physics: 'abc123', track: 'laguna_seca', car: 'probe_gt', hz: 100, dt: 0.001,
  reset: { pos: [1, 2, 3], heading: 0.5, speed: 22 }, ref: [[0, 'driver_a_best']],
  rows: [[0, 0, 1000, 0, 24], [10, -5, 900, 0, 24]], steps: 120000, ...over,
});
const hot = (over: Record<string, unknown> = {}) => ({
  mode: 'hotlap', track: 'laguna_seca', car: 'probe_gt', physics: 'abc123', name: 'Coby', input: 'pad',
  time: 118.5, lap: 1, valid: true, trace: trace(), ...over,
});
const race = (over: Record<string, unknown> = {}) => ({
  mode: 'race', track: 'laguna_seca', car: 'probe_gt', physics: 'abc123', name: 'Coby', input: 'keys',
  ai_version: 'ai-1', metres: FIVE_LAPS, laps: 5, finished: true, time: 640, ...over,
});
const reasons = (b: unknown, sp?: string) => validateSubmission(b, sp ? () => sp : undefined).reasons.join(' | ');

describe('names', () => {
  test('trimmed, whitespace collapsed, 1-12 code points, no control characters', () => {
    expect(normalizeName('  Coby  ')).toBe('Coby');
    expect(normalizeName('a\t \tb')).toBe('a b');
    expect(normalizeName('123456789012')).toBe('123456789012');
    expect(normalizeName('1234567890123')).toBeNull();
    expect(normalizeName('🏎️🏁')).toBe('🏎️🏁');
    expect(normalizeName('   ')).toBeNull();
    expect(normalizeName('')).toBeNull();
    expect(normalizeName('bad\u0007')).toBeNull();
    expect(normalizeName('a\nb')).toBeNull();
    expect(normalizeName('zero​width')).toBeNull();
    expect(normalizeName('nb sp')).toBeNull();
    expect(normalizeName(42)).toBeNull();
    expect(nameKey('CoBy')).toBe(nameKey('coby'));
  });
});

describe('board keys', () => {
  test('round trip and whitelist', () => {
    expect(boardKey('hotlap', 'laguna_seca', 'probe_gt', 'abc')).toBe('hotlap:laguna_seca:probe_gt:abc');
    expect(parseBoardKey('race:laguna_seca:probe_gt:abc:ai-1')).toEqual({ mode: 'race', track: 'laguna_seca', car: 'probe_gt', physics: 'abc', ai_version: 'ai-1' });
    expect(parseBoardKey('hotlap:monza:probe_gt:abc')).toBeNull();
    expect(parseBoardKey('race:laguna_seca:probe_gt:abc')).toBeNull();
    expect(parseBoardKey('hotlap:laguna_seca:probe_gt:abc:x')).toBeNull();
    expect(parseBoardKey('drift:laguna_seca:probe_gt:abc')).toBeNull();
  });
  test('physics version is stable under key order and changes with car.json', () => {
    const a = { b: 1, a: [1, { y: 2, x: 3 }] }, b = { a: [1, { x: 3, y: 2 }], b: 1 };
    expect(canonicalJson(a)).toBe(canonicalJson(b));
    expect(physicsVersion(a, 3560)).toBe(physicsVersion(b, 3560));
    expect(physicsVersion(a, 3560)).not.toBe(physicsVersion({ ...a, b: 2 }, 3560));
    expect(physicsVersion(a, 3560)).not.toBe(physicsVersion(a, 3561));
  });
});

describe('hot-lap plausibility', () => {
  test('a well-formed submission passes', () => {
    const v = validateSubmission(hot(), () => 'abc123');
    expect(v.reasons).toEqual([]);
    expect(v.value!.name).toBe('Coby');
  });
  test('time window 90..600 s', () => {
    expect(reasons(hot({ time: 90 }))).toMatch(/time/);
    expect(reasons(hot({ time: 600 }))).toMatch(/time/);
    expect(reasons(hot({ time: 'fast' }))).toMatch(/time/);
    expect(reasons(hot({ time: 90.001 }))).toBe('');
  });
  test('invalid lap, missing trace, mismatched trace, bad lap number', () => {
    expect(reasons(hot({ valid: false }))).toMatch(/not valid/);
    expect(reasons(hot({ trace: undefined }))).toMatch(/trace missing/);
    expect(reasons(hot({ trace: trace({ car: 'other' }) }))).toMatch(/does not match/);
    expect(reasons(hot({ lap: 0 }))).toMatch(/lap must/);
    expect(reasons(hot({ lap: 7 }))).toMatch(/lap must/);
  });
  test('whitelists: mode, track, car, input; physics version must match the server', () => {
    expect(reasons(hot({ mode: 'drift' }))).toMatch(/mode/);
    expect(reasons(hot({ track: 'monza' }))).toMatch(/unknown track/);
    expect(reasons(hot({ car: 'miata' }))).toMatch(/unknown car/);
    expect(reasons(hot({ input: 'wheel' }))).toMatch(/input/);
    expect(reasons(hot(), 'zzz')).toMatch(/physics version mismatch/);
    expect(reasons(hot({ name: '' }))).toMatch(/name/);
    expect(reasons(hot({ device: 'x'.repeat(65) }))).toMatch(/device/);
    expect(reasons([])).toMatch(/JSON object/);
  });
});

describe('race plausibility', () => {
  test('a full race passes; the replay field is reserved and dropped', () => {
    const v = validateSubmission(race({ replay: { anything: 1 } }));
    expect(v.reasons).toEqual([]);
    expect('replay' in v.value!).toBe(false);
  });
  test('metres within 0 < m <= 5 laps + margin, laps consistent, finishers carry a race time', () => {
    expect(reasons(race({ metres: 0 }))).toMatch(/metres/);
    expect(reasons(race({ metres: 5 * TRACKS.laguna_seca.length_m + 251 }))).toMatch(/metres/);
    expect(reasons(race({ metres: 5 * TRACKS.laguna_seca.length_m + 249 }))).toBe('');
    expect(reasons(race({ laps: 3, metres: 16_000, finished: false, time: undefined }))).toMatch(/inconsistent/);
    expect(reasons(race({ laps: 3, metres: 12_000, finished: false, time: undefined }))).toBe('');
    expect(reasons(race({ laps: 6 }))).toMatch(/laps must/);
    expect(reasons(race({ laps: 4, metres: 16_000 }))).toMatch(/finished requires/);
    expect(reasons(race({ time: undefined }))).toMatch(/race time/);
    expect(reasons(race({ time: 100 }))).toMatch(/race time/);
    expect(reasons(race({ laps: 3, metres: 12_000, finished: false, time: 640 }))).toMatch(/time only/);
    expect(reasons(race({ ai_version: undefined }))).toMatch(/ai_version/);
    expect(reasons(race({ ai_version: 'a:b' }))).toMatch(/ai_version/);
  });
});
