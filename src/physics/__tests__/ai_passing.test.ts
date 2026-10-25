// A pass needs its lane through the corner (driver.ts shutBeside, NOTES "24 Oct 2026: a pass needs its lane through the
// corner"): a car passing on the inside that would still be beside the car it passes where the road shuts its lane at
// the apex gives the pass up ('shut') and is not exempt from the pinch guard; the same pass on a stretch where the lane
// lasts is kept. Two cars placed by hand in the Traffic on Laguna Seca, one control tick of the passer.
import { expect, test } from 'vitest';
import { Vehicle } from '../vehicle';
import { AiDriver } from '../ai/driver';
import { buildAiSpec, buildSpeedProfile, measureCarPerf } from '../ai/field';
import { Traffic } from '../ai/traffic';
import { pack } from './ai_fixture';

/** The passer (car 0) `back` m behind car 1 (on the racing line), in the lane `lanes` lane widths to the given side of
 *  the line, both at speed v, car 1 at station s1; one update of the passer with a pass in hand on car 1. */
function setup(s1: number, side: number, back: number, v: number, lanes = 1) {
  const p = pack(), line = p.line;
  const spec = buildAiSpec(p.probeJson, null, 1), perf = measureCarPerf(spec), prof = buildSpeedProfile(line, perf, spec);
  const tr = new Traffic(2, line.L);
  tr.laneW = 2.6;
  const e0 = side * lanes * tr.laneW, s0 = s1 - back;
  for (let i = 0; i < 2; i++) { tr.front[i] = spec.hull.front; tr.rear[i] = -spec.hull.rear; tr.hw[i] = spec.hull.halfWidth; tr.pace[i] = i === 0 ? 120 : 130; tr.v[i] = v; tr.profile[i] = prof; }
  tr.s[0] = line.wrap(s0); tr.s[1] = line.wrap(s1);
  tr.e[0] = e0; tr.eT[0] = e0; tr.e[1] = 0; tr.eT[1] = 0;
  tr.lat[0] = e0 + line.at(line.off, s0); tr.lat[1] = line.at(line.off, s1);
  tr.U[0] = 1000 + tr.s[0]; tr.U[1] = 1000 + tr.s[1];
  tr.sort();
  const car = new Vehicle(spec, { autoShift: true });
  const pos = new Float64Array(2);
  line.pointAt(s0, tr.lat[0], pos);
  car.reset([pos[0], pos[1], p.surface.sample(pos[0], pos[1]).z], line.headingAt(s0), v);
  const d = new AiDriver(car, line, perf, spec, prof, { number: 'P', scale: 1, targetLap: 120, sigma: 0, aggression: 1, seed: 1 }, 0, tr);
  d.ctl.noise = false;
  d.shift = e0;
  // a pass in hand on car 1 in that lane
  Object.assign(d as any, { passPhase: 1, passTarget: 1, passE: e0, passSide: side, planAdv: 2 });
  tr.passing[0] = 1;
  d.update(0.002);
  return { d, line };
}

test('a pass whose lane the road shuts at the apex while beside the car is given up; where the lane lasts it is kept', () => {
  const { line } = setup(100, 1, 1, 20);
  // the slowest corner (the line's inside edge at its apex, a real braking zone)
  const c = [...line.corners].filter((k) => k.passable).sort((a, b) => a.vApex - b.vApex)[0];
  // the inside lane one lane width over is clamped onto the line within 20 m of the apex (the premise)
  const inside = c.dir, near = (s: number) => inside > 0 ? line.at(line.halfL, s) - line.at(line.off, s) : line.at(line.halfR, s) + line.at(line.off, s);
  let minRoom = Infinity;
  for (let x = -20; x <= 20; x++) minRoom = Math.min(minRoom, near(c.apex + x));
  expect(minRoom).toBeLessThan(2.6);
  // beside it (centre 1 m behind its centre) 25 m before the apex at 15 m/s: the lane shuts within 3 s → give it up
  const shut = setup(c.apex - 25, inside, 1, 15).d;
  expect(shut.passEnd).toBe('shut');
  expect(shut.passPhase).toBe(2);
  expect(shut.passTarget).toBe(-1);
  // already ahead of it by more than PINCH_OK car lengths: it is the car further back and drops behind me → kept
  const ahead = setup(c.apex - 25, inside, -5, 15).d;
  expect(ahead.passPhase).toBe(1);
  expect(ahead.passEnd).not.toBe('shut');
  // the same pass on the widest straight stretch of the lap, where the lane lasts over the next 3 s → kept
  let best = -1, bestRoom = -Infinity;
  for (let s = 0; s < line.L; s += 5) {
    let room = Infinity;
    for (let x = 0; x <= 120; x += 5) room = Math.min(room, line.at(line.halfL, s + x) - line.at(line.off, s + x), line.at(line.halfR, s + x) + line.at(line.off, s + x));
    if (room > bestRoom) { bestRoom = room; best = s; }
  }
  expect(bestRoom).toBeGreaterThan(4);
  const wide = setup(best + 5, 1, 1, 30).d;
  expect(wide.passPhase).toBe(1);
  expect(wide.passEnd).not.toBe('shut');
});
