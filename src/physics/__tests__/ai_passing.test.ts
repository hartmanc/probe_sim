// A pass needs its lane through the corner (driver.ts shutBeside, NOTES "24 Oct 2026: a pass needs its lane through the
// corner"): a car passing on the inside that would still be beside the car it passes where the road shuts its lane at
// the apex gives the pass up ('shut'), drops back and merges in behind it; a pass is not planned into such a lane; the
// same pass where the lane lasts is kept, and planned. Two cars placed by hand in a Traffic on Laguna Seca.
import { expect, test } from 'vitest';
import { Vehicle } from '../vehicle';
import { AiDriver } from '../ai/driver';
import { buildAiSpec, buildSpeedProfile, measureCarPerf } from '../ai/field';
import { Traffic } from '../ai/traffic';
import type { RaceLine } from '../ai/line';
import { pack } from './ai_fixture';

interface Setup { d: AiDriver; tr: Traffic; car: Vehicle; line: RaceLine; prof: Float64Array }

/** Car 0 (the driver under test) `back` m behind car 1 (on the racing line, a Traffic entry only), car 0 in the lane
 *  `lanes` lane widths to `side` of the line; car 0 at speed v, car 1 at v1; car 1 at station s1. With `pass` (default),
 *  a pass in hand on car 1 in that lane. */
function setup(s1: number, side: number, back: number, v: number, opts: { lanes?: number; v1?: number; pass?: boolean } = {}): Setup {
  const p = pack(), line = p.line;
  const spec = buildAiSpec(p.probeJson, null, 1), perf = measureCarPerf(spec), prof = buildSpeedProfile(line, perf, spec);
  const tr = new Traffic(2, line.L);
  tr.laneW = 2.6;
  const e0 = side * (opts.lanes ?? 1) * tr.laneW, s0 = s1 - back;
  for (let i = 0; i < 2; i++) { tr.front[i] = spec.hull.front; tr.rear[i] = -spec.hull.rear; tr.hw[i] = spec.hull.halfWidth; tr.pace[i] = i === 0 ? 120 : 130; tr.profile[i] = prof; }
  tr.v[0] = v; tr.v[1] = opts.v1 ?? v;
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
  if (opts.pass !== false) {
    Object.assign(d as any, { passPhase: 1, passTarget: 1, passE: e0, passSide: side, planAdv: 2 });
    tr.passing[0] = 1;
  }
  return { d, tr, car, line, prof };
}

/** The slowest passable corner of the lap (the line at the inside edge at its apex). */
function slowCorner(line: RaceLine) { return [...line.corners].filter((k) => k.passable).sort((a, b) => a.vApex - b.vApex)[0]; }

/** The station whose next 120 m leave the most road on both sides of the line. */
function widest(line: RaceLine): { s: number; room: number } {
  let best = -1, bestRoom = -Infinity;
  for (let s = 0; s < line.L; s += 5) {
    let room = Infinity;
    for (let x = 0; x <= 120; x += 5) room = Math.min(room, line.at(line.halfL, s + x) - line.at(line.off, s + x), line.at(line.halfR, s + x) + line.at(line.off, s + x));
    if (room > bestRoom) { bestRoom = room; best = s; }
  }
  return { s: best, room: bestRoom };
}

test('a pass whose lane the road shuts at the apex while beside the car is given up; where the lane lasts it is kept', () => {
  const line = pack().line, c = slowCorner(line), inside = c.dir;
  // the inside lane one lane width over is clamped onto the line within 20 m of the apex (the premise)
  const near = (s: number) => inside > 0 ? line.at(line.halfL, s) - line.at(line.off, s) : line.at(line.halfR, s) + line.at(line.off, s);
  let minRoom = Infinity;
  for (let x = -20; x <= 20; x++) minRoom = Math.min(minRoom, near(c.apex + x));
  expect(minRoom).toBeLessThan(2.6);
  // beside it (centre 1 m behind its centre) 25 m before the apex at 15 m/s: the lane shuts within 2 s → give it up
  const shut = setup(c.apex - 25, inside, 1, 15); shut.d.update(0.002);
  expect(shut.d.passEnd).toBe('shut');
  expect(shut.d.passPhase).toBe(2);
  expect(shut.d.passTarget).toBe(-1);
  // already ahead of it by more than PINCH_OK car lengths: it is the car further back and drops behind me → kept
  const ahead = setup(c.apex - 25, inside, -5, 15); ahead.d.update(0.002);
  expect(ahead.d.passPhase).toBe(1);
  expect(ahead.d.passEnd).not.toBe('shut');
  // the same pass on the widest stretch of the lap, where the lane lasts over the look-ahead → kept
  const w = widest(line);
  expect(w.room).toBeGreaterThan(4);
  const wide = setup(w.s + 5, 1, 1, 30); wide.d.update(0.002);
  expect(wide.d.passPhase).toBe(1);
  expect(wide.d.passEnd).not.toBe('shut');
});

test('planning: no pass into a lane the road shuts before I would be ahead; a lane that lasts is planned', () => {
  const line = pack().line, c = slowCorner(line), inside = c.dir;
  // 12 m straight behind a car 15 % below its profile, 45 m before the apex: the inside lane shuts at the apex before
  // the pass could be done (planLane itself, called as update calls it)
  const plan = (st: Setup) => (st.d as any).planLane(1, st.tr.v[0], 1, Number.NaN) as number;
  const vIn = line.at(line.ghostV, c.apex - 45);
  const corner = setup(c.apex - 45, 0, 12, vIn, { lanes: 0, v1: 0.85 * vIn, pass: false });
  const e = plan(corner);
  expect(Number.isNaN(e) || Math.sign(e) !== inside).toBe(true);
  // the same on the widest stretch of the lap: a lane is found
  const w = widest(line);
  const vW = line.at(line.ghostV, w.s);
  const straight = setup(w.s + 12, 0, 12, vW, { lanes: 0, v1: 0.85 * vW, pass: false });
  expect(Number.isNaN(plan(straight))).toBe(false);
});

test('after giving a pass up at a shutting apex the car drops back behind it and merges, not staying alongside', () => {
  const p = pack(), line = p.line, c = slowCorner(line), inside = c.dir;
  const v0 = line.at(line.ghostV, c.apex - 40);
  const { d, tr, car, prof } = setup(c.apex - 40, inside, 1, v0);
  const surface = p.makeSurface();
  const len = tr.front[0] + tr.rear[1];
  let hint = -1, shutAt = -1, merged = -1, overlapAtApex = Infinity, t = 0;
  const dt = 0.001;
  for (let k = 0; k < 8000; k++) {
    if (k % 2 === 0) d.update(2 * dt);
    if (d.passEnd === 'shut' && shutAt < 0) shutAt = t;
    car.step(d.input, surface, dt);
    t += dt;
    // car 0 from its vehicle; car 1 drives its line at 95 % of the profile
    const q = line.project(car.state.pos[0], car.state.pos[1], hint); hint = q.index;
    let ds0 = q.s - tr.s[0]; if (ds0 > line.L / 2) ds0 -= line.L; else if (ds0 < -line.L / 2) ds0 += line.L;
    tr.s[0] = q.s; tr.U[0] += ds0; tr.lat[0] = q.lateral; tr.v[0] = car.state.speed;
    const e = q.lateral - line.at(line.off, q.s);
    tr.ve[0] += ((e - tr.e[0]) / dt - tr.ve[0]) * 0.02; tr.e[0] = e;
    tr.v[1] = 0.95 * line.at(prof, tr.s[1]);
    tr.s[1] = line.wrap(tr.s[1] + tr.v[1] * dt); tr.U[1] += tr.v[1] * dt; tr.lat[1] = line.at(line.off, tr.s[1]);
    tr.sort();
    // while car 1 passes its apex: how far car 0's front is behind car 1's rear (> 0 = no overlap)
    const toApex = line.wrap(tr.s[1] - c.apex + line.L / 2) - line.L / 2;
    if (Math.abs(toApex) < 5) overlapAtApex = Math.min(overlapAtApex, tr.ds(0, 1) - len);
    if (shutAt >= 0 && d.passPhase === 3 && merged < 0) merged = t;   // merging back onto the line
  }
  console.log(`shut at ${shutAt.toFixed(2)} s, gap at the apex ${overlapAtApex.toFixed(2)} m, merged at ${merged.toFixed(2)} s`);
  expect(shutAt).toBeGreaterThanOrEqual(0);              // the pass was given up
  expect(overlapAtApex).toBeGreaterThan(0);              // behind it (no overlap) where the lane is shut
  expect(merged).toBeGreaterThan(shutAt);                // and merges back onto the racing line (within 8 s)
  expect(d.offTrack).toBe(false);
});
