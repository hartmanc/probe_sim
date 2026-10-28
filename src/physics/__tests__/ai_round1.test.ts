// AI round 1 (27 Oct 2026): the pace hint of a car that cannot reach its target (Part A), the AI strength map (Part B),
// the live estimate of the human player's pace (Part C).
import { expect, test } from 'vitest';
import { drawPace, paceHint, FIT_TOL, type PaceJson } from '../ai/field';
import { pack, director } from './ai_fixture';

test('pace hint: the target, or the achieved lap where the fit did not converge', () => {
  expect(paceHint(120, 120.3)).toBe(120);                     // converged (0.25 %)
  expect(paceHint(120, 120 * (1 + FIT_TOL))).toBe(120);       // at the tolerance
  expect(paceHint(120, 123.4)).toBe(123.4);                   // capped: 2.8 % slow
  expect(paceHint(120, 116)).toBe(116);                       // could not be slowed enough
  expect(paceHint(120, null)).toBe(120);                      // not calibrated
});

test('a capped stint races with its achievable lap as the Traffic pace hint, its target unchanged', () => {
  const p = pack();
  const pace: PaceJson = JSON.parse(JSON.stringify(p.pace));
  const car = pace.cars.find((c) => !c.player && (c.stints?.length ?? 0) > 1)!;
  for (const s of car.stints!) s.achievedLap = +(s.targetLap * 1.03).toFixed(3);   // every stint 3 % short of its target
  const d = director({ seed: 5, maxAi: 60 }, { walls: false, pace });
  const rc = d.cars.find((c) => c.number === car.number)!;
  const dp = drawPace(car, 5);
  expect(rc.paceTarget).toBe(dp.targetLap);
  expect(rc.driver!.params.targetLap).toBe(dp.targetLap);
  expect(d.traffic.pace[rc.idx]).toBe(dp.achievedLap);
  // the other cars keep their targets (their fits converged)
  for (const c of d.cars) if (!c.isPlayer && c !== rc && c.stint >= 0) {
    const s = c.pace!.stints![c.stint];
    if (Math.abs(s.achievedLap! / s.targetLap - 1) <= FIT_TOL) expect(d.traffic.pace[c.idx]).toBe(c.paceTarget);
  }
}, 60000);
