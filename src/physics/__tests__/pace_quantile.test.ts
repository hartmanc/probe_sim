// The field pace statistic is a quantile (tools/race/pace_rules.ts; AI round 1, 27 Oct 2026): q = 0.5 is today's median.
import { describe, expect, test } from 'vitest';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, copyFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { median, quantile, carPace } from '../../../tools/race/pace_rules';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');

describe('quantile', () => {
  test('0.5 equals the median for lengths 1-6 (bit for bit, unsorted input)', () => {
    const base = [101.3, 99.7, 100.1, 103.9, 98.2, 100.77];
    for (let n = 1; n <= 6; n++) {
      const a = base.slice(0, n);
      expect(quantile(a, 0.5)).toBe(median(a));
    }
  });
  test('linear interpolation between order statistics', () => {
    const a = [50, 10, 40, 20, 30];            // sorted 10 20 30 40 50: position (n-1) q
    expect(quantile(a, 0)).toBe(10);
    expect(quantile(a, 1)).toBe(50);
    expect(quantile(a, 0.25)).toBe(20);        // position 1
    expect(quantile(a, 0.35)).toBeCloseTo(24, 10);   // position 1.4
    expect(quantile([10, 20, 30, 40], 0.25)).toBeCloseTo(17.5, 10);   // position 0.75
    expect(quantile([], 0.25)).toBeNaN();
  });
  test('one synthetic stint: the target is the 0.25 quantile, the cuts and sigma do not move', () => {
    // a lap-1 out lap, then 8 clean laps 100.0 ... 103.5, one slow lap (> 1.2 x the stint median: cut)
    const clean = [100.0, 100.5, 101.0, 101.5, 102.0, 102.5, 103.0, 103.5];
    const laps = [{ lapNr: 1, lapTime: '1:50.000', inPit: false, status: 'GREEN' },
      ...clean.map((t, i) => ({ lapNr: i + 2, lapTime: `1:${(t - 60).toFixed(3).padStart(6, '0')}`, inPit: false, status: 'GREEN' })),
      { lapNr: 10, lapTime: '2:30.000', inPit: false, status: 'GREEN' }];
    const med = carPace(laps, 100);
    const q25 = carPace(laps, 100, undefined, 0.25);
    expect(med.stints).toHaveLength(1);
    expect(med.stints[0].targetLap).toBe(101.75);            // median of the 8 laps
    expect(q25.stints[0].targetLap).toBe(100.875);           // position 1.75: 100.5 + 0.75 x 0.5 = 100.875
    expect(q25.stints[0].laps).toBe(med.stints[0].laps);
    expect(q25.stints[0].sigma).toBe(med.stints[0].sigma);
    expect(q25.greenLaps).toBe(med.greenLaps);
    expect(q25.targetLap).toBeLessThan(med.targetLap);
  });
});

// Regenerating each public file at q = 0.5 with its recorded command line gives the same `cars` (fitted fields aside).
const SESSIONS: Record<string, { track: string; args: string[]; seedWithPublic?: boolean }> = {
  'cars/field/pace.json': { track: 'laguna_seca', args: ['tools/race/pace.ts', '--track', 'laguna_seca'] },
  // Sonoma keeps the player's reference row "from the previous file" (#619 did not race): the regeneration starts from a copy
  'cars/field/sonoma/pace.json': { track: 'sonoma', args: ['tools/race/pace_track.ts', '--track', 'sonoma', '--session', '11838772', '--own'], seedWithPublic: true },
  'cars/field/buttonwillow/pace.json': { track: 'buttonwillow', args: ['tools/race/pace_track.ts', '--track', 'buttonwillow', '--session', '12906863', '--own'] },
  'cars/field/mid_ohio/pace.json': { track: 'mid_ohio', args: ['tools/race/pace_track.ts', '--track', 'mid_ohio', '--session', '11926749', '--own'] },
};
const stripFit = (cars: any[]) => cars.map((c) => {
  const { scale: _s, achievedLap: _a, resolved: _r, ...rest } = c;
  return { ...rest, stints: (c.stints ?? []).map(({ scale: _s2, achievedLap: _a2, ...st }: any) => st) };
});

describe('regenerating the public pace files at q = 0.5', () => {
  for (const [rel, { track, args, seedWithPublic }] of Object.entries(SESSIONS)) {
    test(rel, () => {
      const pub = JSON.parse(readFileSync(resolve(ROOT, 'public', rel), 'utf8'));
      const dir = mkdtempSync(resolve(tmpdir(), 'pace_q_'));
      const out = resolve(dir, track, 'pace.json');
      mkdirSync(dirname(out), { recursive: true });
      if (seedWithPublic) copyFileSync(resolve(ROOT, 'public', rel), out);
      execFileSync(resolve(ROOT, 'node_modules/.bin/tsx'), [...args, '--source', pub.source, '--quantile', '0.5'], {
        cwd: ROOT, env: { ...process.env, FIELD_TRACK: track, FIELD_PACE: out }, stdio: 'pipe',
      });
      const got = JSON.parse(readFileSync(out, 'utf8'));
      expect(got.pace).toEqual({ stat: 'quantile', q: 0.5 });
      expect(got.cars.length).toBe(pub.cars.length);
      // Mid-Ohio's public file was re-id'd by hand (2b060d1: #56 156 -> 56_mo) after it was generated; the tool, reading the
      // identity row (id 56_mo, laguna_number 156), now also writes model_id "156" there, which the public file lacks
      // (its model comes from the identity row at runtime). The one known difference; everything else must be equal.
      const exempt = (cars: any[]) => cars.map((c) => (rel.includes('mid_ohio') && c.id === '56_mo' ? (({ model_id: _m, ...r }) => r)(c) : c));
      expect(exempt(stripFit(got.cars))).toEqual(exempt(stripFit(pub.cars)));
    }, 120_000);
  }
});
