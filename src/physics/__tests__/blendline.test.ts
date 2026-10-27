// The pit-exit blend line (Mid-Ohio round 11, the owner's drive of round 10: "the invalid lap or black flag for crossing into the
// pit exit at T1 should be pretty strict ... two wheels 'off' should be a black flag"). src/physics/blendline.ts: the band, one
// wheel over, two wheels over, both directions (a car on its lap cutting in, a car leaving the pits cutting out), the debounce,
// the lap timer's reason, the race rule engine's flag, and a package without the line (no rule).
import { describe, expect, it } from 'vitest';
import { BlendFlag, BlendLine, BlendLineWatch, GRACE_M, REARM_S, WHEEL_WIDTH_M, type BlendLineJson } from '../blendline';
import { LapTimer } from '../../app/timing';
import { HotlapSim } from '../../scoreboard/sim';
import { lagunaAssets } from '../../scoreboard/__tests__/fixtures';
import { RaceDirector } from '../ai/race';
import { createCollisionWorld } from '../index';
import { pack } from './ai_fixture';

// a straight line along +x from (0, 0) to (60, 0) with a joint at x = 30; the pit exit lies to its left (+y)
const json = (side: 1 | -1 = 1, extra: Partial<BlendLineJson> = {}): BlendLineJson => ({ pts: [[0, 0], [30, 0], [60, 0]], pit_side: side, label: 'crossed the blend line at T1', ...extra });
const wheels = (...ys: number[]) => ys.map((y, i) => ({ pos: [10 + (i % 2) * 2.6, y] as number[] }));
/** a car whose centre is at (x, yc) with its left wheels at yc + 0.75 and right wheels at yc - 0.75 */
const car = (x: number, yc: number) => ({ cx: x, cy: yc, w: [{ pos: [x + 1.3, yc + 0.75] }, { pos: [x + 1.3, yc - 0.75] }, { pos: [x - 1.3, yc + 0.75] }, { pos: [x - 1.3, yc - 0.75] }] });
const run = (watch: BlendLineWatch, x: number, yc: number, dy: number[] = [0, 0, 0, 0]) => {
  const c = car(x, yc); c.w.forEach((w, i) => { w.pos[1] += dy[i]; });
  return watch.update(c.cx, c.cy, c.w);
};

describe('the line: distance and band', () => {
  const L = new BlendLine(json());
  it('signed distance, positive to the left of the driving direction; length', () => {
    expect(L.length).toBeCloseTo(60, 6);
    expect(L.locate(20, 0.4).d).toBeCloseTo(0.4, 9);
    expect(L.locate(20, -0.4).d).toBeCloseTo(-0.4, 9);
    expect(L.locate(45, 2).d).toBeCloseTo(2, 9);       // beyond the joint
  });
  it('the band is the line\'s length: beyond either end is out', () => {
    expect(L.locate(0, 1).band).toBe(true);
    expect(L.locate(60, 1).band).toBe(true);
    expect(L.locate(-0.5, 1).band).toBe(false);
    expect(L.locate(60.5, 1).band).toBe(false);
    expect(L.locate(30, 100).band).toBe(false);          // far from the line (bounding box)
  });
  it('a bent line is judged on its nearest segment', () => {
    const bent = new BlendLine({ pts: [[0, 0], [10, 0], [20, 5]], pit_side: 1 });
    expect(bent.locate(15, 0).d).toBeLessThan(-0.5);      // below the second segment's line: right of it
    expect(bent.locate(15, 4).d).toBeGreaterThan(0);
    expect(bent.locate(15, -3).d).toBeLessThan(0);
  });
  it('needs two points', () => { expect(() => new BlendLine({ pts: [[0, 0]], pit_side: 1 })).toThrow(); });
});

describe('on its lap (it entered the band on the course side): the pit side is off limits', () => {
  it('no wheel over: nothing; one wheel over: nothing; two wheels over: a violation', () => {
    const w = new BlendLineWatch(new BlendLine(json()));
    expect(run(w, 5, -2)).toBeNull();                      // enters on the course side
    expect(w.mode).toBe('lap');
    // yc = -1.0: left wheels at -0.25, right at -1.75: none over
    expect(run(w, 12, -1.0)).toBeNull();
    // exactly one wheel over: left-front only
    expect(run(w, 14, -1.0, [1.5, 0, 0, 0])).toBeNull();
    // two wheels over (both left wheels)
    expect(run(w, 16, -1.0, [1.5, 0, 1.5, 0])).toBe('pit_side');
    // the rear pair or the front pair (one side of the car across)
    expect(run(w, 18, -1.0, [3, 3, 0, 0])).toBe('pit_side');
  });
  it('strict: a wheel counts as soon as its centre is past the line (grace 0), not before', () => {
    expect(GRACE_M).toBe(0);
    const w = new BlendLineWatch(new BlendLine(json()));
    run(w, 5, -2);
    expect(w.update(20, -1, [{ pos: [20, 0.0] }, { pos: [20, 0.0] }, { pos: [20, -3] }, { pos: [20, -3] }])).toBeNull();   // on the line: not over
    expect(w.update(20, -1, [{ pos: [20, 0.01] }, { pos: [20, 0.01] }, { pos: [20, -3] }, { pos: [20, -3] }])).toBe('pit_side');
  });
  it('the car\'s centre crossing mid-band does not change its mode: still on its lap', () => {
    const w = new BlendLineWatch(new BlendLine(json()));
    run(w, 5, -2);
    expect(run(w, 20, 1.5)).toBe('pit_side');                // centre over the line, all four wheels beyond
    expect(w.mode).toBe('lap');
  });
  it('wheels beyond the line\'s ends do not count; the mode is cleared once the centre leaves the band', () => {
    const w = new BlendLineWatch(new BlendLine(json()));
    run(w, 5, -2);
    expect(w.update(63, 1, [{ pos: [64, 1] }, { pos: [64, 2] }, { pos: [62, 1] }, { pos: [62, 2] }])).toBeNull();   // centre past the end
    expect(w.mode).toBe('none');
    // a car that starts beyond the end of the band never has a mode
    expect(w.update(-8, 1, [{ pos: [-7, 1] }, { pos: [-7, 2] }, { pos: [-9, 1] }, { pos: [-9, 2] }])).toBeNull();
    expect(w.mode).toBe('none');
  });
});

describe('leaving the pits (it entered the band on the pit side): the course side is off limits', () => {
  it('stays on the pit side: nothing; one wheel across: nothing; two wheels across: a violation', () => {
    const w = new BlendLineWatch(new BlendLine(json()));
    expect(run(w, 5, 3)).toBeNull();
    expect(w.mode).toBe('pit');
    expect(run(w, 10, 3)).toBeNull();
    expect(run(w, 12, 2)).toBeNull();                                    // wheels at 2.75 / 1.25: all on the pit side
    expect(run(w, 14, 2, [0, -3, 0, 0])).toBeNull();                     // one wheel across
    expect(run(w, 16, 2, [0, -3, 0, -3])).toBe('course_side');           // the right pair across
    expect(run(w, 20, -2)).toBe('course_side');                          // the whole car
  });
  it('joining the course after the line\'s end is fine', () => {
    const w = new BlendLineWatch(new BlendLine(json()));
    run(w, 5, 3);
    expect(w.update(62, -2, [{ pos: [63, -2] }, { pos: [63, -3] }, { pos: [61, -2] }, { pos: [61, -3] }])).toBeNull();
    expect(w.mode).toBe('none');
  });
});

describe('the pit side is the package\'s: a line with the pit exit on its right mirrors every rule', () => {
  it('pit_side -1: wheels on the right are the pit side', () => {
    const w = new BlendLineWatch(new BlendLine(json(-1)));
    expect(run(w, 5, 2)).toBeNull();                       // the course is to the left now
    expect(w.mode).toBe('lap');
    expect(run(w, 10, 1.0, [0, -1.5, 0, -1.5])).toBe('pit_side');
    const p = new BlendLineWatch(new BlendLine(json(-1)));
    expect(run(p, 5, -3)).toBeNull();
    expect(p.mode).toBe('pit');
    expect(run(p, 10, -0.5, [1.5, 0, 1.5, 0])).toBe('course_side');
  });
});

describe('a declared grace is never more than a wheel\'s own width', () => {
  it('grace_m 1 is clamped to the wheel width', () => {
    expect(new BlendLine(json(1, { grace_m: 1 })).grace).toBe(WHEEL_WIDTH_M);
    expect(new BlendLine(json(1, { grace_m: -1 })).grace).toBe(0);
    const w = new BlendLineWatch(new BlendLine(json(1, { grace_m: 1 })));
    run(w, 5, -2);
    expect(w.update(20, -1, [{ pos: [20, 0.15] }, { pos: [20, 0.15] }, { pos: [20, -3] }, { pos: [20, -3] }])).toBeNull();
    expect(w.update(20, -1, [{ pos: [20, 0.25] }, { pos: [20, 0.25] }, { pos: [20, -3] }, { pos: [20, -3] }])).toBe('pit_side');
  });
});

describe('BlendFlag: one flag per violation, re-armed after REARM_S legal', () => {
  it('fires once while the car stays across, again after two legal seconds', () => {
    const f = new BlendFlag(new BlendLineWatch(new BlendLine(json())));
    const c = car(20, -1.0), over = car(20, 1.5);
    f.update(5, -2, car(5, -2).w, 0.005);
    expect(f.update(over.cx, over.cy, over.w, 0.005)).toBe('pit_side');
    expect(f.update(over.cx, over.cy, over.w, 0.005)).toBeNull();
    for (let t = 0; t < REARM_S - 0.1; t += 0.1) f.update(c.cx, c.cy, c.w, 0.1);
    expect(f.update(over.cx, over.cy, over.w, 0.005)).toBeNull();      // 1.9 s legal: still disarmed
    for (let t = 0; t < REARM_S + 0.1; t += 0.1) f.update(c.cx, c.cy, c.w, 0.1);
    expect(f.update(over.cx, over.cy, over.w, 0.005)).toBe('pit_side');
  });
});

describe('the lap timer carries the reason', () => {
  const lap = (t: LapTimer, reason?: string) => {
    t.update(0, 900, 30, false, 0.005); t.update(1, 10, 30, false, 0.005);          // start
    t.update(10, 500, 30, false, 0.005);                                             // half way
    if (reason) t.invalidate(reason);
    t.update(20, 900, 30, false, 0.005); return t.update(21, 10, 30, false, 0.005);  // the lap
  };
  it('an invalidated lap is invalid with the reason; the next lap is clean', () => {
    const t = new LapTimer(1000);
    const a = lap(t, 'crossed the blend line at T1');
    expect(a).not.toBe('start'); expect(a && a !== 'start' && a.valid).toBe(false);
    expect(a && a !== 'start' && a.reason).toBe('crossed the blend line at T1');
    const b = t.update(30, 500, 30, false, 0.005) ?? t.update(40, 900, 30, false, 0.005) ?? t.update(41, 10, 30, false, 0.005);
    expect(b && b !== 'start' && b.valid).toBe(true);
    expect(b && b !== 'start' && b.reason).toBeUndefined();
  });
  it('invalidate before the lap has started does nothing; the first reason is kept', () => {
    const t = new LapTimer(1000);
    t.invalidate('x'); expect(t.currentValid).toBe(true);
    const a = lap(t, 'first'); t.invalidate('second');
    expect(a && a !== 'start' && a.reason).toBe('first');
  });
});

describe('no line declared = no rule', () => {
  it('Laguna Seca (no blend_line): the hot-lap sim has no watch, wheels anywhere never flag', () => {
    const sim = new HotlapSim(lagunaAssets());
    expect((lagunaAssets().scenery as { blend_line?: unknown }).blend_line).toBeUndefined();
    for (let i = 0; i < 2000; i++) sim.step(() => ({ steer: 0, throttle: 0.5, brake: 0 }));
    expect(sim.blendFlags).toBe(0);
    expect(sim.lastBlendReason).toBeNull();
  });
  it('the race rule engine without blendLine: the same car cutting where a line would be is not flagged', () => {
    const p = pack();
    const d = new RaceDirector({ line: p.line, surface: p.surface, makeSurface: p.makeSurface, probeJson: p.probeJson, pace: p.pace, identity: p.identity,
      pitLane: p.scenery.pit_lane ?? null, collisionWorld: createCollisionWorld(p.scenery, p.track) }, { seed: 1, maxAi: 2, greenWindow: [0.01, 0.02] });
    for (let i = 0; i < 100; i++) d.step(0.001, { steer: 0, throttle: 0, brake: 1, shiftUp: false, shiftDown: false });
    const s = 1300, edgeL = d.line.at(d.line.halfL, s), pos = new Float64Array(2);
    d.line.pointAt(s, edgeL + 0.4, pos);
    d.player.vehicle.reset([pos[0], pos[1], d.player.surface.sample(pos[0], pos[1]).z], d.line.headingAt(s), 0);
    for (let i = 0; i < 600; i++) d.step(0.001, { steer: 0, throttle: 0, brake: 1, shiftUp: false, shiftDown: false });
    expect(d.hud().penalties.count).toBe(0);
  });
});

describe('the race rule engine: the same flag and penalty as four wheels off', () => {
  it('a line declared along Laguna\'s left edge: two wheels across are a black flag with the line\'s words, once', () => {
    const p = pack();
    const probe = new RaceDirector({ line: p.line, surface: p.surface, makeSurface: p.makeSurface, probeJson: p.probeJson, pace: p.pace, identity: p.identity,
      pitLane: p.scenery.pit_lane ?? null }, { seed: 1, maxAi: 2, greenWindow: [0.01, 0.02] });
    const s0 = 1300, pts: [number, number][] = [], tmp = new Float64Array(2);
    for (let s = s0 - 40; s <= s0 + 80; s += 4) { probe.line.pointAt(s, probe.line.at(probe.line.halfL, s), tmp); pts.push([tmp[0], tmp[1]]); }
    // the line runs in driving direction, so the left edge (the pit side) is its left: pit_side +1
    const d = new RaceDirector({ line: p.line, surface: p.surface, makeSurface: p.makeSurface, probeJson: p.probeJson, pace: p.pace, identity: p.identity,
      pitLane: p.scenery.pit_lane ?? null, blendLine: { pts, pit_side: 1, label: 'crossed the blend line at T1' } }, { seed: 1, maxAi: 2, greenWindow: [0.01, 0.02] });
    const inp = { steer: 0, throttle: 0, brake: 1, shiftUp: false, shiftDown: false };
    for (let i = 0; i < 100; i++) d.step(0.001, inp);
    expect(d.phase).toBe('green');
    const place = (s: number, lat: number) => {
      d.line.pointAt(s, lat, tmp);
      d.player.vehicle.reset([tmp[0], tmp[1], d.player.surface.sample(tmp[0], tmp[1]).z], d.line.headingAt(s), 0);
      d.player.hint = -1; d.player.driver?.resetState();
    };
    const edgeL = d.line.at(d.line.halfL, s0);
    place(s0 - 20, d.line.at(d.line.halfL, s0 - 20) - 1.5);          // enters the band on the course side
    for (let i = 0; i < 300; i++) d.step(0.001, inp);
    expect(d.hud().penalties.count).toBe(0);
    place(s0, edgeL + 0.25);                                          // centre 0.25 m beyond the line: the left wheels are across, the right not
    for (let i = 0; i < 300; i++) d.step(0.001, inp);
    const h = d.hud();
    expect(h.penalties.count).toBe(1);
    expect(h.penalties.lastReason).toBe('crossed the blend line at T1');
    expect(h.flag).toBe('black');
    for (let i = 0; i < 600; i++) d.step(0.001, inp);                 // still across: one flag (debounced)
    expect(d.hud().penalties.count).toBe(1);
  });
});
