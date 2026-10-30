// C1, the offset planner (src/physics/ai/planner.ts): its rules on synthetic neighbours (a straight, constant speeds), and alone
// through the driver (the racing line, nothing evaluated).
import { describe, expect, test } from 'vitest';
import { PlanWork, plan, candidateCost, shiftRate, attackOverlap, attackNext, lineFree, bandTaken, trainTarget, BIG, PLAN_DT, PLAN_N, REVERSE_W, SHIFT_MIN, ATT_NONE, ATT_COMMIT, ATT_HOLD, ATT_BACK, type PlanEnv } from '../ai/planner';
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

  test('C3 R1: a car behind me that my body does not overlap changes nothing in my plan; told, I hold my target', () => {
    for (const ePrev of [0, 1.5]) {
      const a = work({ ePrev, eCur: ePrev, eMeas: ePrev }), b = work({ ePrev, eCur: ePrev, eMeas: ePrev });
      car(a, 0, 25, 0, 24); car(b, 0, 25, 0, 24);   // a slower car ahead: a reason to move
      car(b, 1, -6, 2.4, 36);                        // a faster car 6 m behind, on my left, coming up
      car(b, 2, -12, -2.4, 36);                      // and one on my right
      const ea = plan(a, env), eb = plan(b, env);
      expect(eb).toBe(ea);
      expect(b.bestCost).toBeCloseTo(a.bestCost, 9);
      for (let c = 0; c < a.nC; c++) expect(b.cost[c]).toBeCloseTo(a.cost[c], 9);
    }
    // overlap still holds: the same car with its nose beside my rear owns its side
    const o = work();
    car(o, 0, 25, 0, 24); car(o, 1, -2, 2.0, 30, { own: 1 });
    expect(costOf(o, 1.5)).toBeGreaterThanOrEqual(2 * BIG);
    // told: the target is held (never moved for the passer)
    const f = work({ frozen: true });
    car(f, 0, 25, 0, 24);
    expect(plan(f, env)).toBe(0);
  });

  test('C3 R2: inside a car\'s entry vortex without overlap at its turn-in is refused; alongside it is allowed; a straight has none', () => {
    // a left-hander: the car ahead (on the line, 25 m ahead, 10 m/s slower) turns in 40 m ahead of me, apex at 100 m, track-out
    // at 160 m
    const vortex = (w: PlanWork, k: number) => { w.vIn[k] = 40; w.vAp[k] = 100; w.vOut[k] = 160; w.vDir[k] = 1; };
    const behind = work({ v: 30 });
    car(behind, 0, 25, 0, 20); vortex(behind, 0);
    expect(costOf(behind, 3)).toBeGreaterThanOrEqual(BIG);       // a dive to its inside: alongside only after its turn-in (refused)
    expect(costOf(behind, 0)).toBeLessThan(BIG);                  // backing out: in behind it
    const wake = work({ v: 30 });
    car(wake, 0, 25, 0, 30); vortex(wake, 0);
    expect(costOf(wake, 3)).toBeLessThan(BIG);                    // inside it but never alongside: no dive
    const along = work({ v: 30, ePrev: 2.5, eCur: 2.5, eMeas: 2.5 });
    car(along, 0, 1, 0, 28); vortex(along, 0);                    // alongside (overlapping) by its turn-in
    along.vIn[0] = 5;
    expect(costOf(along, 3)).toBeLessThan(BIG);
    const straight = work({ v: 30 });
    car(straight, 0, 25, 0, 20);                                  // no corner: pass anywhere
    expect(costOf(straight, 3)).toBeLessThan(BIG);
    // the exit vortex: past its apex, behind it on its outside
    const exit = work({ v: 30 });
    car(exit, 0, 8, 0, 25); exit.vIn[0] = -40; exit.vAp[0] = 10; exit.vOut[0] = 150; exit.vDir[0] = 1;
    expect(costOf(exit, -3)).toBeGreaterThanOrEqual(BIG);
  });

  test('C3 R3: the plan moves at the rate the grip leaves, and the road clamping my outside offset faster than that is a hard rule', () => {
    const w = work();
    expect(shiftRate(w, 30, 0)).toBeCloseTo(2.86, 6);              // a straight: the pass rate
    expect(shiftRate(w, 30, 0.01)).toBe(SHIFT_MIN);                // at the grip limit (v²κ = a_lat): the least rate
    expect(shiftRate(w, 30, 0.005)).toBeLessThan(2.86);
    // a right-hander at the limit, held 2 m to its outside (left) while the road closes on it at 1.2 m/s (C2 passed it: < 0.6 x 2.86)
    const right: PlanEnv = { ...env, curv: () => -0.01, hi: (s: number) => Math.max(0.2, Math.min(5, 3 - 0.04 * (s - 10))) };
    const h = work({ ePrev: 2, eCur: 2, eMeas: 2 });
    car(h, 0, 140, -4, 30);
    h.cand[0] = 2; h.nC = 1;
    expect(candidateCost(h, right, 0)).toBeGreaterThanOrEqual(BIG);
  });
});

describe('C4: the Lemons pass (pure)', () => {
  const OVL = 2.2;   // half of a 4.4 m car
  test('P1: on a straight, a clearly slower car ahead: the attack offset gets my nose half a car past its tail before a braking point 200 m ahead, not one 30 m ahead; the plan takes it', () => {
    const w = work();
    car(w, 0, 18, 0, 26);                                   // 18 m ahead (centre), 4 m/s slower, on the line
    expect(attackOverlap(w, env, 0, 2.6, 200)).toBeLessThan(BIG);
    expect(w.attOv).toBeGreaterThanOrEqual(OVL);
    attackOverlap(w, env, 0, 2.6, 30);
    expect(w.attOv).toBeLessThan(OVL);
    // a straight longer than the horizon: no braking point in reach, the check is made again when it comes in
    attackOverlap(w, env, 0, 2.6, 1e4);
    expect(w.attOv).toBe(Number.POSITIVE_INFINITY);
    // committed: the attack offset is preferred, and the plan moves there
    const c = work();
    car(c, 0, 18, 0, 26);
    c.eAtt = 2.6;
    expect(plan(c, env)).toBeCloseTo(2.6, 6);
  });

  test('P1 pick: a third car in the attack band where I reach the braking point takes that side', () => {
    const w = work();
    car(w, 0, 18, 0, 26);
    expect(bandTaken(w, 0, 2.6, 60)).toBe(false);
    car(w, 1, 40, 2.4, 24);                                 // in the left band, 40 m up the road (I reach 60 m in 2 s, it is at 88 m)
    expect(bandTaken(w, 0, 2.6, 60)).toBe(false);
    car(w, 1, 15, 2.4, 22);                                 // ... where I will be: at 59 m when I reach 60 m
    expect(bandTaken(w, 0, 2.6, 60)).toBe(true);
    expect(bandTaken(w, 0, -2.6, 60)).toBe(false);
  });

  test('P2 / P3: at the braking point without the overlap back out (then re-plan past the apex); with it hold the side to the track-out', () => {
    // (ov: m my nose is past its tail; dB / dAp / dOut: m to the braking point, apex, track-out; reach: m to the next check)
    expect(attackNext(ATT_COMMIT, -3, OVL, 120, 200, 260, 8)).toBe(ATT_COMMIT);       // still on the straight
    expect(attackNext(ATT_COMMIT, -3, OVL, 5, 85, 145, 8)).toBe(ATT_BACK);           // at the braking point, not alongside
    expect(attackNext(ATT_COMMIT, 1.5, OVL, 5, 85, 145, 8)).toBe(ATT_BACK);          // a nose in is not the overlap
    expect(attackNext(ATT_COMMIT, 3, OVL, 5, 85, 145, 8)).toBe(ATT_HOLD);            // half a car alongside: hold
    expect(attackNext(ATT_BACK, -6, OVL, -40, 30, 90, 8)).toBe(ATT_BACK);            // backing out until the apex
    expect(attackNext(ATT_BACK, -12, OVL, -80, -2, 60, 8)).toBe(ATT_NONE);           // past it: re-plan
    expect(attackNext(ATT_HOLD, 4, OVL, -80, -2, 60, 8)).toBe(ATT_HOLD);             // holding through the apex
    expect(attackNext(ATT_HOLD, 6, OVL, -140, -60, -1, 8)).toBe(ATT_NONE);           // to the track-out
    // backing out, the plan tucks in behind it (the preference: its line), once my nose is behind its tail
    const b = work({ v: 28, ePrev: 2.6, eCur: 2.6, eMeas: 2.6 });
    car(b, 0, 14, 0, 28);
    b.eAtt = 0;
    expect(Math.abs(plan(b, env))).toBeLessThan(0.3);
    // holding: the side is kept although another target is cheaper
    const h = work({ ePrev: 2.6, eCur: 2.6, eMeas: 2.6 });
    car(h, 0, 1, 0, 29.5);                                 // alongside, its nose ahead of mine
    h.eAtt = 2.6; h.attHold = true;
    expect(plan(h, env)).toBeCloseTo(2.6, 6);
  });

  test('P4: nobody within ret m ahead (nor reached within retT s) and nobody beside me: the racing line, no plan', () => {
    const w = work();
    car(w, 0, 100, 0, 30);                                  // 100 m ahead at my speed
    expect(lineFree(w)).toBe(true);
    car(w, 0, 100, 0, 22);                                  // 100 m ahead, 8 m/s slower: within 40 m of it in 10 s
    expect(lineFree(w)).toBe(false);
    car(w, 0, 20, 0, 30);                                   // 20 m ahead
    expect(lineFree(w)).toBe(false);
    car(w, 0, -1, 2.2, 30);                                 // beside me
    expect(lineFree(w)).toBe(false);
    car(w, 0, -15, 0, 31);                                  // well behind me: the lead car holds its line (R1)
    expect(lineFree(w)).toBe(true);
  });
});

describe('C5: the train pass (pure)', () => {
  const OVL = 2.2;
  /** a train of three cars on the line at 26 m/s, 20 / 28 / 36 m ahead (about 0.14 s apart); me at 30 m/s, the pressure headway */
  function train(): { w: PlanWork; ks: Int32Array } {
    const w = work({ headway: 0.3 });
    car(w, 0, 20, 0, 26); car(w, 1, 28, 0, 26); car(w, 2, 36, 0, 26);
    w.nTrain[0] = 1; w.nTrain[1] = 1; w.nTrain[2] = 1;
    return { w, ks: Int32Array.from([0, 1, 2]) };
  }
  test('T1: the target is the furthest car of the train my nose passes by ovl before the landing: the front of it on a long straight', () => {
    const { w, ks } = train();
    expect(trainTarget(w, env, ks, 3, 2, 2.6, 20, OVL)).toBe(-1);       // a braking point 20 m ahead: no landing
    expect(trainTarget(w, env, ks, 3, 2, 2.6, 150, OVL)).toBe(0);       // 150 m: the first car only
    expect(trainTarget(w, env, ks, 3, 2, 2.6, 240, OVL)).toBe(1);       // 240 m: two of them
    expect(trainTarget(w, env, ks, 3, 2, 2.6, 400, OVL)).toBe(2);       // beyond the horizon, carried on at the closing speed: all three
    expect(w.attOvK[2]).toBeGreaterThan(20);
    // the target never moves further out than the one committed to (upTo), and a passed car (-1) is not counted
    expect(trainTarget(w, env, ks, 3, 1, 2.6, 400, OVL)).toBe(1);
    // without the hold (the C2 pass that merges back after the first car) the projection tucks in behind the second one
    w.trainHold = false; w.eAtt = Number.NaN;
    attackOverlap(w, env, 0, 2.6, 400);
    expect(w.attOvK[2]).toBeLessThan(OVL);
  });

  test('T2: committed, the attack offset holds under a soft cost and the commit aborts under a hard rule (a car moving into my lane ahead)', () => {
    // soft: the corridor's edge 0.2 m from the attack offset (a corridor cost every sample): still a landing
    const envN: PlanEnv = { ...env, hi: () => 2.8 };
    const a = train();
    expect(trainTarget(a.w, envN, a.ks, 3, 2, 2.6, 400, OVL)).toBe(2);
    a.w.cand[0] = 2.6; a.w.nC = 1; a.w.trainHold = true; a.w.eAtt = 2.6;
    const soft = candidateCost(a.w, envN, 0);
    expect(soft).toBeGreaterThan(0); expect(soft).toBeLessThan(BIG);
    // hard: a much slower car in the attack lane 18 m ahead: I cannot brake to it in the room
    const b = train();
    car(b.w, 3, 18, 2.6, 15);
    expect(trainTarget(b.w, env, b.ks, 3, 2, 2.6, 400, OVL)).toBe(-2);
  });

  test('T3: the landing needs the overlap at the target\'s turn-in: without it back out behind it, with it hold the side', () => {
    // (dTi: m to its turn-in; ovlTi: m of my nose past its tail needed there)
    expect(attackNext(ATT_HOLD, 1, OVL, -10, 60, 120, 8, 5, 1.32)).toBe(ATT_BACK);
    expect(attackNext(ATT_HOLD, 3, OVL, -10, 60, 120, 8, 5, 1.32)).toBe(ATT_HOLD);
    expect(attackNext(ATT_HOLD, 1, OVL, -10, 60, 120, 8, 30, 1.32)).toBe(ATT_HOLD);   // not at the turn-in yet
    expect(attackNext(ATT_HOLD, 1, OVL, -10, 60, 120, 8)).toBe(ATT_HOLD);              // C4 (no turn-in check)
    // and the braking point still needs ovl: a nose in is no landing
    expect(attackNext(ATT_COMMIT, 1.5, OVL, 5, 85, 145, 8, 40, 1.32)).toBe(ATT_BACK);
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
