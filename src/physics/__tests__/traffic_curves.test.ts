import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pairsWithDrops, curves, gBin, dBin, type Crossing, type StintRef } from '../../../tools/race/traffic_curves';
import { loadEvent, analyse, toJson } from '../../../tools/race/traffic_data';

// Hand-written crossings of four scenarios, each in its own time window (> 10 s from the others) so they cannot interact.
// car(id, times) -> lap 1..n crossings with lapTime = the difference (lap 1 = 100).
const car = (id: string, times: number[], over: Record<number, Partial<Crossing>> = {}): Crossing[] =>
  times.map((t, i) => ({ car: id, lapNr: i + 1, t, lapTime: i ? t - times[i - 1] : 100, green: true, pit: false, ...over[i + 1] }));
const fixture: Crossing[] = [
  // 1 pass: A (ref 96) 2 s behind B (ref 100) at 200/202, A laps 96 s and B 100 s -> A crosses first; B then trails A by 6 s
  ...car('B', [100, 200, 300, 400]), ...car('A', [102, 202, 298, 394]),
  // 2 stuck: C 1 s behind D, both 100 s laps
  ...car('D', [1000, 1100, 1200, 1300]), ...car('C', [1001, 1101, 1201, 1301]),
  // 3 pit exclusion: F pits on lap 3 (flagged, 400 s), so E at 2102 has nobody on the road ahead
  ...car('F', [2000, 2100, 2500, 2600], { 3: { pit: true } }), ...car('E', [2002, 2102, 2202, 2302]),
  // 4 yellow exclusion: G's lap 3 is yellow
  ...car('H', [3000, 3100, 3200, 3300]), ...car('G', [3001, 3101, 3201, 3301], { 3: { green: false } }),
  // 5 pull-away: I behind J at 4100/4101; J laps 96 s and I 100 s
  ...car('J', [4000, 4100, 4196, 4292]), ...car('I', [4001, 4101, 4201, 4301]),
];
const refs: StintRef[] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'].map((k) => ({ car: k, fromLap: 1, toLap: 20, ref: k === 'A' || k === 'J' ? 96 : 100 }));

describe('traffic_curves', () => {
  it('bins', () => {
    expect([0.1, 0.5, 1.9, 2.5, 4, 6, 9.9].map(gBin)).toEqual([0, 1, 2, 3, 4, 5, 6]);
    expect([-0.01, 0, 0.02, 0.05, 0.1, 0.2].map(dBin)).toEqual([0, 1, 2, 3, 4, 5]);
  });
  const { pairs, drops } = pairsWithDrops(fixture, refs);
  const find = (x: string, lap: number) => pairs.find((p) => p.x === x && p.lap === lap);
  it('a clean pass', () => {
    const p = find('A', 3)!;
    expect(p.y).toBe('B'); expect(p.g).toBeCloseTo(2); expect(p.outcome).toBe('passed'); expect(p.d).toBeCloseTo(4 / 96); expect(p.lostX).toBeCloseTo(0);
    const c = curves(pairs).cells.find((q) => q.g === '2-3' && q.d === '3-8')!;
    expect(c.n).toBe(2); expect(c.passed).toBe(1);   // A also trails B on lap 2 (same gap, same pace: stuck)
  });
  it('a stuck lap', () => {
    const p = find('C', 3)!;
    expect(p.y).toBe('D'); expect(p.outcome).toBe('stuck'); expect(p.gNew).toBeCloseTo(1); expect(p.d).toBeCloseTo(0);
  });
  it('a pull-away', () => {
    const p = find('I', 3)!;
    expect(p.y).toBe('J'); expect(p.outcome).toBe('pulledAway'); expect(p.gNew).toBeCloseTo(5); expect(p.d).toBeCloseTo(-0.04);
    expect(find('B', 4)!.outcome).toBe('pulledAway');   // B trails A after being passed
  });
  it('excludes a car in the pits and a yellow lap', () => {
    expect(pairs.some((p) => p.x === 'E' && p.lap === 3)).toBe(false);
    expect(drops.inPitsSkipped).toBeGreaterThan(0);
    expect(pairs.some((p) => p.x === 'G' && p.lap === 3)).toBe(false);
    expect(drops.yellow).toBeGreaterThan(0);
  });
});

describe('traffic_data loader', () => {
  it('reproduces the committed Laguna curves', () => {
    const committed = JSON.parse(readFileSync(resolve(__dirname, '../../../tools/race/data/traffic/curves.json'), 'utf8'));
    const now = JSON.parse(toJson(analyse(loadEvent('laguna')).summary));
    expect(now).toEqual(committed.events.laguna);
  });
});
