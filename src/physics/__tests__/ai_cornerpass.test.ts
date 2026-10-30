// L1 (30 Oct 2026, NOTES "L1: corner passes in the lane model"): RaceConfig.cornerPass in the lane model. K1, the pinch rule by
// overlap at the passed car's turn-in (keep the lane through the corner, or back out; never the dive); K2, late braking in a pass
// until the overlap is made. The driver's own decision (cpStep / cpPlanShut) on a hand-set traffic snapshot at a Laguna corner whose
// inside lane the road shuts beside the racing line, so the geometry is the real road's.
import { describe, expect, test } from 'vitest';
import { director } from './ai_fixture';
import { cpKnobs, driverProfile, vortexCorners, type AiDriver } from '../ai/driver';
import type { RaceDirector } from '../ai/race';

interface CpDriver { cpStep(j: number, v: number): string; cpPlanShut(j: number, e: number, side: number, v: number, dv: number, look: number): boolean; shutStation(j: number, e: number, side: number, v: number, dv: number, dist: number): number;
  passProfile(): Float64Array; baseProf: Float64Array; cpState: number; cpC: number; boJ: number; boC: number; k2On: boolean; passPhase: number; passTarget: number; passE: number; passSide: number; ctl: { cornerPass: boolean } }

const V = 25;   // m/s, the passed car's speed (the passer's: V + dv)
/** A two-car snapshot: j at station sj on the racing line, i at d m behind it (centre to centre) in lane e. */
function place(d: RaceDirector, i: number, j: number, sj: number, gap: number, e: number, dv: number): void {
  const tr = d.traffic, L = d.line.L;
  const w = (s: number) => ((s % L) + L) % L;
  tr.s[j] = w(sj); tr.e[j] = 0; tr.eT[j] = 0; tr.v[j] = V; tr.off[j] = 0;
  tr.s[i] = w(sj - gap); tr.e[i] = e; tr.eT[i] = e; tr.v[i] = V + dv; tr.off[i] = 0;
}

describe('corner passes (lane model, cornerPass)', () => {
  const d = director({ planner: 'lanes', seed: 1, laps: 1, maxAi: 3, playerAi: true, cornerPass: true, mishapRate: 0 });
  const tr = d.traffic, line = d.line, vc = vortexCorners(line);
  const ai = d.cars.filter((c) => c.driver).slice(0, 2);
  const i = ai[0].idx, j = ai[1].idx;
  const D = ai[0].driver as unknown as CpDriver;
  for (const c of d.cars) if (c.driver) c.driver.ctl.cornerPass = true;
  // a corner whose inside pass lane (one lane inside the line) the road shuts beside the car on the line, between turn-in and track-out
  const W = tr.laneW;
  const pick = line.corners.map((C, c) => ({ C, c })).find(({ C, c }) => {
    if (!C.passable || line.trackId === 'laguna_seca' && C.turn === 'T8') return false;
    place(d, i, j, vc.turnIn[c] - 20, 2, C.dir * W, 0);
    const x = D.shutStation(j, C.dir * W, C.dir, V, 0, 150);
    const sx = tr.s[i] + x, fw = (a: number, b: number) => ((b - a) % line.L + line.L) % line.L;
    return x >= 0 && fw(vc.turnIn[c], sx) < fw(vc.turnIn[c], vc.trackOut[c]) + 10;
  })!;
  const { C, c } = pick;
  const e = C.dir * W, side = C.dir;
  const start = (gap: number, dv: number, sj = vc.turnIn[c] - 20) => {
    place(d, i, j, sj, gap, e, dv);
    D.passPhase = 1; D.passTarget = j; D.passE = e; D.passSide = side; D.cpState = 0; D.cpC = -1; D.boJ = -1; D.boC = -1; D.k2On = false;
  };
  const len = tr.front[i] + tr.rear[i];

  test('a Laguna corner with a shut inside lane exists', () => {
    expect(pick).toBeTruthy();
    expect(cpKnobs.ovlTI).toBeCloseTo(0.3, 6);
  });

  test('K1: overlap at turn-in keeps the lane through the corner (no shut rule, the passed car told)', () => {
    start(tr.front[i] + tr.rear[j] - 0.6 * len, 0);       // nose 0.6 of my length past its tail
    expect(D.cpStep(j, V)).toBe('');
    expect(D.cpState).toBe(1);                              // deferred to its turn-in
    place(d, i, j, vc.turnIn[c] + 1, tr.front[i] + tr.rear[j] - 0.6 * len, e, 0);
    expect(D.cpStep(j, V)).toBe('');
    expect(D.cpState).toBe(2);                              // held
    // half way to the apex: still held, no shut
    place(d, i, j, vc.turnIn[c] + 0.5 * (((C.apex - vc.turnIn[c]) % line.L + line.L) % line.L), tr.front[i] + tr.rear[j] - 0.6 * len, e, 0);
    expect(D.cpStep(j, V)).toBe('');
    expect(D.cpState).toBe(2);
  });

  test('K1: no overlap at turn-in backs out (no new pass before the apex)', () => {
    const gap0 = tr.front[i] + tr.rear[j] + 2;               // 2 m behind its tail, closing at 4 m/s: projected alongside at its turn-in
    start(gap0, 4);
    expect(D.cpStep(j, V + 4)).toBe('');
    expect(D.cpState).toBe(1);
    expect(D.k2On).toBe(true);                               // K2: late braking while the overlap is not made
    place(d, i, j, vc.turnIn[c] + 1, tr.front[i] + tr.rear[j] - 0.1 * len, e, 0);   // only 0.1 of my length at its turn-in
    expect(D.cpStep(j, V)).toBe('backout');
    expect(D.boJ).toBe(j);
    expect(D.boC).toBe(c);
    expect(D.cpState).toBe(0);
  });

  test('K1: the dive never happens (behind a car that has turned in: the shut rule; no pass planned into that lane)', () => {
    start(tr.front[i] + tr.rear[j] - 0.6 * len, 0, vc.turnIn[c] + 3);   // overlapping, but it turned in before I had a decision
    const r = D.cpStep(j, V);
    expect(D.cpState).not.toBe(2);
    expect(r === 'shut' || r === '').toBe(true);
    start(tr.front[i] + tr.rear[j] + 2, 3, vc.turnIn[c] + 3);
    expect(D.cpPlanShut(j, e, side, V + 3, 3, 150)).toBe(true);           // no lane
    // before its turn-in, a lane whose overlap at the turn-in is projected is a lane; one that is not is no lane
    start(tr.front[i] + tr.rear[j] + 2, 6);
    expect(D.cpPlanShut(j, e, side, V + 6, 6, 150)).toBe(false);
    start(tr.front[i] + tr.rear[j] + 2, 3);                                 // projected short of ovlTI at its turn-in
    expect(D.cpPlanShut(j, e, side, V + 3, 3, 150)).toBe(true);
    start(tr.front[i] + tr.rear[j] + 25, 0.5);
    expect(D.cpPlanShut(j, e, side, V + 0.5, 0.5, 150)).toBe(true);
  });

  test('K2: the pass margin brakes later; off once the overlap is made or the pass is given up', () => {
    const p = D.passProfile(), b = (ai[0].driver as AiDriver).profile;
    let more = 0;
    for (let k = 0; k < p.length; k++) { expect(p[k]).toBeGreaterThanOrEqual(b[k] - 1e-9); if (p[k] > b[k] + 0.05) more++; }
    expect(more).toBeGreaterThan(50);
    expect(driverProfile(line, (ai[0].driver as AiDriver).perf, D.baseProf)).toEqual(b);   // the normal margin is the normal profile
    start(tr.front[i] + tr.rear[j] + 2, 4);
    D.cpStep(j, V + 4);
    expect(D.k2On).toBe(true);
    place(d, i, j, vc.turnIn[c] - 10, tr.front[i] + tr.rear[j] - 0.5 * len, e, 4);   // overlap made before its turn-in
    D.cpStep(j, V + 4);
    expect(D.k2On).toBe(false);
    start(tr.front[i] + tr.rear[j] + 2, 4);
    D.cpStep(j, V + 4);
    expect(D.k2On).toBe(true);
    // the pass ends (passPhase leaves 1): update() clears it
    D.passPhase = 2; D.passTarget = -1;
    ai[0].driver!.update(0.002);
    expect(D.k2On).toBe(false);
  });
});
