// Per-stint driver pace: each race draws one real stint per AI car from the seed (field.ts drawPace).
import { expect, test } from 'vitest';
import { drawPace } from '../ai/field';
import { pack, director } from './ai_fixture';

test('stint draw: deterministic per seed, every stint reachable, roughly uniform', () => {
  const p = pack();
  const c = p.pace.cars.find((x) => x.number === '711')!;
  const n = c.stints!.length;
  expect(n).toBeGreaterThan(2);
  expect(drawPace(c, 42)).toEqual(drawPace(c, 42));
  const counts = new Array(n).fill(0);
  for (let s = 1; s <= 600; s++) { const d = drawPace(c, s); counts[d.stint]++; expect(d.targetLap).toBe(c.stints![d.stint].targetLap); expect(d.scale).toBe(c.stints![d.stint].scale); }
  for (const k of counts) expect(k).toBeGreaterThan((600 / n) * 0.5);
  // a car without stints keeps its car-level pace
  expect(drawPace({ ...c, stints: [] }, 1)).toMatchObject({ stint: -1, targetLap: c.targetLap, scale: c.scale });
});

test('a race builds each AI car at its drawn pace; restart redraws and matches a fresh director', () => {
  const d = director({ seed: 5, maxAi: 6 }, { walls: false });
  for (const c of d.cars) {
    if (c.isPlayer) { expect(c.stint).toBe(-1); continue; }
    const dp = drawPace(c.pace!, 5);
    expect(c.paceTarget).toBe(dp.targetLap);
    expect(c.driver!.params.targetLap).toBe(dp.targetLap);
    expect(c.driver!.params.scale).toBe(dp.scale);
  }
  const before = d.cars.map((c) => c.paceTarget);
  d.restart(6);
  const fresh = director({ seed: 6, maxAi: 6 }, { walls: false });
  expect(d.cars.map((c) => c.paceTarget)).toEqual(fresh.cars.map((c) => c.paceTarget));
  expect(d.cars.map((c) => c.vehicle.state.pos)).toEqual(fresh.cars.map((c) => c.vehicle.state.pos));
  let differs = false;
  for (let s = 7; s < 40 && !differs; s++) { d.restart(s); differs = d.cars.some((c, i) => c.paceTarget !== before[i]); }
  expect(differs).toBe(true);
  // the drawn driver is never exposed through the HUD or the results
  for (let k = 0; k < 2000; k++) d.step(0.001);
  expect(JSON.stringify(d.hud())).not.toMatch(/stint|paceTarget|paceScale/);
}, 60000);
