// AI round 1 (27 Oct 2026): the pace hint of a car that cannot reach its target (Part A), the AI strength map (Part B),
// the live estimate of the human player's pace (Part C).
import { expect, test } from 'vitest';
import { AI_STRENGTHS, drawPace, paceHint, strengthPace, FIT_TOL, LAP_SCALE_SLOPE, PACE_MAX, PACE_MIN, type PaceJson } from '../ai/field';
import { pack, director } from './ai_fixture';
import { AI_VERSION, buildAiSpec, buildSpeedProfile, measureCarPerf } from '../ai/field';
import { RaceDirector, playerPaceEstimate, type PlayerLapRecord } from '../ai/race';
import { AiDriver, paceClass } from '../ai/driver';
import { Vehicle } from '../vehicle';

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

test('strength map: 100 % is the calibrated pace bit for bit; monotonic; the lap follows target / strength; caps hold', () => {
  const p = pack();
  let n = 0;
  for (const c of p.pace.cars) for (const s of [{ scale: c.scale!, lap: c.achievedLap!, target: c.targetLap }, ...(c.stints ?? []).map((x) => ({ scale: x.scale!, lap: x.achievedLap!, target: x.targetLap }))]) {
    const id = strengthPace(c.curve, s.scale, s.lap, s.target, 1);
    expect(id.scale).toBe(s.scale); expect(id.lap).toBe(s.lap); expect(id.targetLap).toBe(s.target); expect(id.capped).toBe(false);
    let prev = -Infinity;
    for (const st of [0.9, 0.95, ...AI_STRENGTHS, 1.1]) {
      const r = strengthPace(c.curve, s.scale, s.lap, s.target, st);
      expect(r.scale).toBeGreaterThanOrEqual(prev);                    // stronger = a larger scale, never smaller
      prev = r.scale;
      expect(r.targetLap).toBeCloseTo(s.target / st, 9);
      expect(r.scale).toBeGreaterThanOrEqual(PACE_MIN); expect(r.scale).toBeLessThanOrEqual(PACE_MAX);
      if (!r.capped && st !== 1) expect(Math.abs(r.lap / r.targetLap - 1)).toBeLessThan(1e-9 + Math.abs(s.lap / s.target - 1) * 1.2 + 1e-6);
      if (r.capped) { if (st > 1) expect(r.lap).toBeGreaterThan(r.targetLap); else expect(r.lap).toBeLessThan(r.targetLap); }   // held at PACE_MAX / PACE_MIN
    }
    n++;
  }
  expect(n).toBeGreaterThan(100);
  // without a curve: the pooled slope; a flat curve cannot go faster than its caps
  const r = strengthPace(undefined, 1, 120, 120, 1.1);
  expect(r.scale).toBeCloseTo(Math.pow(1.1, 1 / -LAP_SCALE_SLOPE), 6);
  const flat = strengthPace([[1, 120], [1.2, 120]], 1, 120, 120, 1.1);
  expect(flat.capped).toBe(true); expect(flat.scale).toBe(PACE_MAX); expect(flat.lap).toBeCloseTo(120, 9);
});

test('a race at 110 %: every AI car built at its mapped scale, hints and sigma follow, the player untouched', () => {
  const a = director({ seed: 3, maxAi: 8 }, { walls: false }), b = director({ seed: 3, maxAi: 8, strength: 1.1 }, { walls: false });
  for (let k = 0; k < a.cars.length; k++) {
    const x = a.cars[k], y = b.cars[k];
    if (x.isPlayer) { expect(y.paceScale).toBe(x.paceScale); expect(b.traffic.pace[k]).toBe(a.traffic.pace[k]); continue; }
    const dp = drawPace(x.pace!, 3);
    const r = strengthPace(x.pace!.curve, dp.scale!, dp.achievedLap!, dp.targetLap, 1.1);
    expect(y.paceScale).toBe(r.scale);
    expect(y.paceTarget).toBeCloseTo(x.paceTarget / 1.1, 9);
    expect(y.paceSigma).toBeCloseTo(x.paceSigma / 1.1, 9);
    expect(b.traffic.pace[k]).toBe(paceHint(r.targetLap, r.lap));
    expect(y.paceScale).toBeGreaterThan(x.paceScale);
  }
}, 60000);

test('player pace estimate: start value, median of the last three clean laps, the filters and the clamps', () => {
  const L = (lap: number, f: Partial<PlayerLapRecord> = {}): PlayerLapRecord => ({ lap, off: false, penalty: false, contact: false, ...f });
  expect(playerPaceEstimate(120, [])).toBe(120);
  expect(playerPaceEstimate(120, [L(118)])).toBe(118);
  expect(playerPaceEstimate(120, [L(118), L(122)])).toBe(120);                          // two: their mean
  expect(playerPaceEstimate(120, [L(130), L(118), L(119), L(121)])).toBe(119);          // the last three only
  // interrupted laps never count: an off, a penalty, a contact at fault
  expect(playerPaceEstimate(120, [L(117), L(140, { off: true }), L(150, { penalty: true }), L(135, { contact: true })])).toBe(117);
  expect(playerPaceEstimate(120, [L(100, { off: true })])).toBe(120);
  expect(playerPaceEstimate(120, [L(118), L(119), L(117), L(200, { contact: true })])).toBe(118);
  // clamps: never quicker than 0.9 x, never slower than 1.3 x the start value
  expect(playerPaceEstimate(120, [L(100), L(101), L(99)])).toBe(108);
  expect(playerPaceEstimate(120, [L(170), L(180), L(175)])).toBe(156);
  expect(playerPaceEstimate(120, [L(Number.NaN)])).toBe(120);
});

test('a human lapping at 0.93 x his row median moves from clearly slower to close for a car at his pace within two laps', () => {
  const p = pack();
  // the human: the AI Probe at scale 1 (~120.2 s solo) driven from outside the director, as a player's inputs
  const ref = 120.2, row = ref / 0.93;
  const pace: PaceJson = { ai_version: AI_VERSION, cars: [
    { number: 'T1', team: 't', class: 'B', grid: 1, finish: 1, lapsCompleted: 10, greenLaps: 10, targetLap: 120.5, bestLap: 119, sigma: 0.3, aggression: 1, scale: 1 },
    { number: '619', team: 't', class: 'B', grid: 2, finish: 2, lapsCompleted: 10, greenLaps: 10, targetLap: row, bestLap: row, sigma: 0.3, aggression: 1, player: true },
  ] };
  const spec = buildAiSpec(p.probeJson, null, 1), veh = new Vehicle(spec, { autoShift: true });
  const d = new RaceDirector({ line: p.line, surface: p.surface, makeSurface: p.makeSurface, probeJson: p.probeJson, pace, identity: null, pitLane: p.scenery.pit_lane ?? null, playerVehicle: veh },
    { seed: 1, laps: 4, greenWindow: [3, 4], gridGap: 250, mishapRate: 0 });
  const perf = measureCarPerf(spec);
  const human = new AiDriver(veh, p.line, perf, spec, buildSpeedProfile(p.line, perf, spec), { number: '619', scale: 1, targetLap: ref, sigma: 0, aggression: 1, seed: 1 }, d.player.idx, d.traffic);
  human.ctl.noise = false;
  const t1 = d.cars.find((c) => c.number === 'T1')!;
  const cls = () => paceClass(d.traffic.pace[t1.idx], d.playerPace);
  expect(d.playerPace).toBe(row);
  expect(cls()).toBe('slower');
  const seen: string[] = [];
  let k = 0;
  while (d.player.lapsDone < 3 && d.time < 600) {
    if (k++ % 2 === 0) { Object.assign(human.ctl, { speedCap: t1.driver!.ctl.speedCap, noPass: t1.driver!.ctl.noPass, minGap: t1.driver!.ctl.minGap }); human.update(0.002); }
    const before = d.player.lapsDone;
    d.step(0.001, human.input);
    if (d.player.lapsDone !== before) seen.push(`${d.player.lapsDone}:${cls()}:${d.playerPace.toFixed(2)}`);
  }
  console.log(`human laps ${d.player.lastLap.toFixed(2)} s (row median ${row.toFixed(2)}): ${seen.join(' ')}`);
  expect(d.player.lapsDone).toBeGreaterThanOrEqual(3);
  // two completed green laps (lap 1 starts at the line after the green): his estimate is his sim pace, the class is close
  const at2 = seen.find((x) => x.startsWith('2:'))!;
  expect(at2.split(':')[1]).toBe('close');
  expect(d.playerPace).toBeLessThan(0.97 * row);
  expect(cls()).toBe('close');
}, 120000);
