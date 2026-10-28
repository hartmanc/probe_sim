// Traffic round (28 Oct 2026): the director's crossing log (the sim's own MyLaps), and the behaviours tuned against the data
// (tools/race/traffic_sim.ts, NOTES "Traffic round").
import { expect, test } from 'vitest';
import { createCollisionWorld } from '../index';
import { RaceDirector, type RaceConfig } from '../ai/race';
import { AI_VERSION, type PaceCar, type PaceJson } from '../ai/field';
import { pack, director } from './ai_fixture';
import { runSelfplay } from '../../../tools/race/selfplay_metrics';
import { pairsWithDrops } from '../../../tools/race/traffic_curves';
import { simRefs } from '../../../tools/race/traffic_sim';

test('crossings: every car (the player too) logs each line crossing; lap times and the line clock agree; lap 1 is the first timed', () => {
  const d = director({ seed: 3, laps: 2, maxAi: 4, playerAi: true, gridGap: 40, greenWindow: [2, 3], mishapRate: 0 });
  while (d.cars.some((c) => c.lapsDone < 2) && d.time < 900) d.step(0.001);   // (the race ends 3 s after the leader's flag: run on until all have 2 laps)
  const cr = d.crossings;
  expect(cr.some((c) => c.car === d.player.number)).toBe(true);
  for (const car of d.cars) {
    const a = cr.filter((c) => c.car === car.number);
    expect(a.length).toBeGreaterThanOrEqual(3);                      // the start of lap 1, the end of laps 1 and 2
    expect(a[0].lapNr).toBe(0);
    expect(Number.isNaN(a[0].lapTime)).toBe(true);
    expect(a[0].green).toBe(false);
    for (let k = 1; k < a.length; k++) {
      expect(a[k].lapNr).toBe(a[k - 1].lapNr + 1);
      expect(a[k].lapTime).toBeCloseTo(a[k].t - a[k - 1].t, 9);
      expect(a[k].pit).toBe(false);
    }
    expect(a[1].green && a[2].green).toBe(true);                     // laps 1 and 2 raced under green
    for (const c of a.slice(3)) expect(c.green).toBe(false);         // cool-down laps after the flag are not
  }
  // the module reads them: refs per car, pairs only from lap 2 on
  const refs = simRefs(cr);
  expect(refs.length).toBe(d.cars.length);
  const { pairs } = pairsWithDrops(cr, refs, { minLap: 30 });
  for (const p of pairs) expect(p.lap).toBeGreaterThanOrEqual(2);
  void pack;
}, 120000);

/** A hand-made field of Probe clones (as ai_behaviour.test.ts). */
function field(rows: { number: string; targetLap: number; aggression?: 0 | 1 | 2; scale?: number }[], cfg: Partial<RaceConfig>): RaceDirector {
  const p = pack();
  const cars: PaceCar[] = rows.map((r, k) => ({
    number: r.number, team: 'test', class: 'B', grid: k + 1, finish: k + 1, lapsCompleted: 10, greenLaps: 10,
    targetLap: r.targetLap, bestLap: r.targetLap - 2, sigma: 0.5, aggression: r.aggression ?? 1, player: r.number === '619' || undefined,
    ...(r.scale ? { scale: r.scale } : {}),
  }));
  const pace: PaceJson = { ai_version: AI_VERSION, cars };
  return new RaceDirector({
    line: p.line, surface: p.surface, makeSurface: p.makeSurface, probeJson: p.probeJson, pace, identity: p.identity,
    pitLane: p.scenery.pit_lane ?? null, collisionWorld: createCollisionWorld(p.scenery, p.track),
  }, { seed: 1, playerAi: true, greenWindow: [3, 4], ...cfg });
}
/** the first seed (from 1) whose shuffled grid starts `b` right behind `a` */
function seeded(rows: Parameters<typeof field>[0], cfg: Partial<RaceConfig>, a: string, b: string): RaceDirector {
  let d = field(rows, cfg);
  for (let seed = 2; seed < 60; seed++) {
    const g = (n: string) => d.cars.find((c) => c.number === n)!.grid;
    if (g(b) === g(a) + 1) break;
    d = field(rows, { ...cfg, seed });
  }
  return d;
}

test('decisive pass: a car 10 % quicker gets by within one lap of closing to 2 s (the data: 98 % at d 8-15 %), no contact, no defence', () => {
  const rows = [{ number: 'T1', targetLap: 140, scale: 0.5 }, { number: 'T2', targetLap: 125, scale: 1.0 }, { number: '619', targetLap: 170, scale: 0.4 }];
  const d = seeded(rows, { laps: 3, mishapRate: 0 }, 'T1', 'T2');
  const t1 = d.cars.find((c) => c.number === 'T1')!, t2 = d.cars.find((c) => c.number === 'T2')!;
  let tClose = NaN, tBy = NaN, k = 0;
  const step0 = d.step.bind(d);
  (d as unknown as { step: typeof d.step }).step = (dt, inp) => {
    step0(dt, inp);
    if (++k % 20 || d.phase !== 'green' || Number.isFinite(tBy)) return;
    const gap = (t1.U - t2.U) / Math.max(5, d.traffic.v[t2.idx]);
    if (Number.isNaN(tClose) && gap < 2) tClose = d.time;
    if (Number.isFinite(tClose) && t2.U > t1.U + 2) tBy = d.time;
  };
  const m = runSelfplay(d, pack().makeSurface());
  expect(Number.isFinite(tClose)).toBe(true);
  expect(tBy - tClose).toBeLessThan(140);                     // within T1's lap
  expect(m.defending.vsClearlyFaster).toBe(0);
  expect(m.rules.contacts).toBe(0);
}, 120000);
