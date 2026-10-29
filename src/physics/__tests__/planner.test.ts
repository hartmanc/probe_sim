// C1, the offset planner (src/physics/ai/planner.ts): its rules on synthetic neighbours (a straight, constant speeds), and alone
// through the driver (the racing line, nothing evaluated).
import { describe, expect, test } from 'vitest';
import { PlanWork, plan, candidateCost, BIG, PLAN_DT, PLAN_N, REVERSE_W, type PlanEnv } from '../ai/planner';
import { director } from './ai_fixture';

const S = PLAN_N + 1;
/** a straight 10 m wide road at 30 m/s: corridor ±5 m around the line */
const env: PlanEnv = { vRef: () => 30, factor: () => 1, lo: () => -5, hi: () => 5, curv: () => 0, risk: () => 0 };

function work(o: Partial<PlanWork> = {}): PlanWork {
  const w = new PlanWork();
  Object.assign(w, { v: 30, eCur: 0, eMeas: 0, ePrev: 0, rate: 2.86, hw: 0.9, front: 2.2, rear: 2.2, headway: 0.55, aggr: 1, bMax: 8, aLat: 9 }, o);
  return w;
}
/** neighbour k: m ahead now (negative: behind), lane offset e, constant speed v */
function car(w: PlanWork, k: number, rel0: number, e: number, v: number, o: { own?: number; ignore?: number; off?: number } = {}): void {
  for (let m = 0; m <= PLAN_N; m++) { w.X[k * S + m] = rel0 + v * m * PLAN_DT; w.LO[k * S + m] = e - 0.9; w.HI[k * S + m] = e + 0.9; }
  w.nFront[k] = 2.2; w.nRear[k] = 2.2; w.nE[k] = e; w.nIdx[k] = k;
  w.nOwn[k] = o.own ?? 0; w.nIgnore[k] = o.ignore ?? 0; w.nOff[k] = o.off ?? 0;
  w.nN = Math.max(w.nN, k + 1);
}
/** the cost of target e (added as an extra candidate) */
function costOf(w: PlanWork, e: number): number { w.cand[0] = e; w.nC = 1; return candidateCost(w, env, 0); }

describe('offset planner (pure)', () => {
  test('a clearly slower car ahead in my band: the plan moves out to pass it', () => {
    const w = work();
    car(w, 0, 25, 0, 24);
    const e = plan(w, env);
    expect(Math.abs(e)).toBeGreaterThanOrEqual(2);
    expect(w.bestCost).toBeLessThan(BIG);
  });

  test('overlap holds: a car alongside owns its side, no move into its margin', () => {
    const w = work();
    car(w, 0, 0.5, 2.0, 30, { own: 1 });       // alongside on my left
    car(w, 1, 25, 0, 24);                       // and a slower car ahead in my band: a reason to move
    expect(costOf(w, 1.0)).toBeGreaterThanOrEqual(2 * BIG);   // into its side
    expect(costOf(w, -2.5)).toBeLessThan(BIG);                // away from it
    expect(plan(w, env)).toBeLessThanOrEqual(0);
  });

  test('never across: no move that sweeps through a car within the sweep length', () => {
    const w = work();
    car(w, 0, 8, 1.5, 30);                      // just ahead, between me and +3 m
    expect(costOf(w, 3)).toBeGreaterThanOrEqual(2 * BIG);
    car(w, 0, 80, 1.5, 30);                     // far ahead: the sweep is done long before it
    expect(costOf(w, 3)).toBeLessThan(BIG);
  });

  test('no move toward a clearly faster car behind; straight behind me, no move at all', () => {
    const w = work({ cfSide: 1 });
    car(w, 0, -10, 2.6, 33);
    expect(costOf(w, 1)).toBeGreaterThanOrEqual(2 * BIG);
    expect(costOf(w, -1)).toBeLessThan(BIG);
    w.cfSide = 2;
    expect(costOf(w, -1)).toBeGreaterThanOrEqual(2 * BIG);
    expect(costOf(w, 0)).toBeLessThan(BIG);     // holding
    expect(plan(w, env)).toBe(0);
  });

  test('no-pass window: no candidate takes me from behind to ahead of a running car inside it', () => {
    const w = work({ zoneLo: -10, zoneHi: 400 });
    car(w, 0, 15, 0, 20);
    expect(costOf(w, -3)).toBeGreaterThanOrEqual(2 * BIG);
    expect(plan(w, env)).toBe(0);               // single file behind it
    const v = work();
    car(v, 0, 15, 0, 20);
    expect(Math.abs(plan(v, env))).toBeGreaterThanOrEqual(2);   // outside a window the same car is passed
    const off = work({ zoneLo: -10, zoneHi: 400 });
    car(off, 0, 15, 0, 5, { off: 1 });          // a car off / recovering is passed freely
    expect(costOf(off, -3)).toBeLessThan(BIG);
  });

  test('one move: a new target is held MIN_HOLD s and must beat the current one by the margin; a reversal in the approach costs', () => {
    const w = work({ locked: true });
    car(w, 0, 25, 0, 24);
    expect(plan(w, env)).toBe(0);               // just set: held
    w.locked = false;
    expect(plan(w, env)).not.toBe(0);
    // a reversal before the apex of the move
    const a = work({ ePrev: 2, eCur: 2, eMeas: 2, moveDir: 1, moveOpen: false }), b = work({ ePrev: 2, eCur: 2, eMeas: 2, moveDir: 1, moveOpen: true });
    car(a, 0, 30, 2, 30); car(b, 0, 30, 2, 30);
    expect(costOf(b, 0) - costOf(a, 0)).toBeCloseTo(REVERSE_W, 6);
    // equal options: ties and the hysteresis go to the current target
    const t = work({ ePrev: 0.5 });
    car(t, 0, 140, -4, 30);
    expect(plan(t, env)).toBe(0.5);
  });
});

describe('offset planner in the driver', () => {
  test('alone: the racing line, no plan evaluated', () => {
    const d = director({ planner: 'offset', seed: 2, laps: 1, maxAi: 5, playerAi: true, gridGap: 300, greenWindow: [2, 3], mishapRate: 0 });
    const tr = d.traffic;
    let checked = 0;
    while (d.time < 60) {
      const plans = d.cars.map((c) => (c.driver as unknown as { oPlans: number }).oPlans);
      for (let k = 0; k < 10; k++) d.step(0.001);
      if (d.phase !== 'green') continue;
      for (const c of d.cars) {
        const i = c.idx;
        let near = false;
        for (let j = 0; j < tr.n; j++) { if (j === i) continue; const r = tr.ds(i, j); if (r > -45 && r < 170) near = true; }
        if (near) continue;
        const drv = c.driver as unknown as { oStar: number; oPlans: number; shift: number };
        expect(drv.oStar).toBe(0);
        expect(drv.oPlans).toBe(plans[i]);
        checked++;
      }
    }
    expect(checked).toBeGreaterThan(1000);
  }, 60000);
});
