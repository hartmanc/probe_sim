// Traffic round (28 Oct 2026): the director's crossing log (the sim's own MyLaps), and the behaviours tuned against the data
// (tools/race/traffic_sim.ts, NOTES "Traffic round").
import { expect, test } from 'vitest';
import { pack, director } from './ai_fixture';
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
