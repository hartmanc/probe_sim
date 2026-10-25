// Pure parts of the stage-3 scenery gates (tools/track/gates/sceneryGates.ts, 20 Oct 2026): segment crossing, polygon
// test, containment escapes / barriers / allowed runoff, pit connectivity and sign placement on a synthetic straight.
import { describe, expect, it } from 'vitest';
import { coneSpots, conesOffSurface, containment, degenerateRuns, escapeRuns, exposedEnds, inPoly, joinFaces, laneClearance, pitConnectivity, runGaps, segCross, sideBySide, signPlacement, tyreFaces, wallTops, type SceneryLike, type TrackLike, type V3 } from '../../../tools/track/gates/sceneryGates';

// a 400 m oval-ish closed loop: two 150 m straights joined by half circles R 30, 1 m stations, half-width 5
function loop(): TrackLike {
  const C: V3[] = [], L: V3[] = [], R: V3[] = [];
  const pts: [number, number, number][] = [];
  const Ls = 150, Rr = 30, n = Math.round(2 * Ls + 2 * Math.PI * Rr);
  for (let k = 0; k < n; k++) {
    let s = k, x: number, y: number, h: number;
    if (s < Ls) { x = s; y = 0; h = 0; }
    else if ((s -= Ls) < Math.PI * Rr) { const a = s / Rr; x = Ls + Rr * Math.sin(a); y = Rr - Rr * Math.cos(a); h = a; }
    else if ((s -= Math.PI * Rr) < Ls) { x = Ls - s; y = 2 * Rr; h = Math.PI; }
    else { s -= Ls; const a = s / Rr; x = -Rr * Math.sin(a); y = Rr + Rr * Math.cos(a); h = Math.PI + a; }
    pts.push([x, y, h]);
  }
  for (const [x, y, h] of pts) {
    const nx = -Math.sin(h), ny = Math.cos(h);
    C.push([x, y, 0]); L.push([x + nx * 5, y + ny * 5, 0]); R.push([x - nx * 5, y - ny * 5, 0]);
  }
  return { n, spacing_m: 1, center: C, left: L, right: R };
}
const T = loop();
// a closed paved road 10 m right of the bottom straight (y -10 .. -16, x 40 .. 110)
const road = { turn: 'closed', kind: 'closed_road', center: [[40, -13, 0], [110, -13, 0]] as V3[], left: [[40, -10, 0], [110, -10, 0]] as V3[], right: [[40, -16, 0], [110, -16, 0]] as V3[] };

describe('scenery gates: primitives', () => {
  it('segCross and inPoly', () => {
    expect(segCross([0, 0], [10, 0], [5, -1], [5, 1])).toBeCloseTo(0.5, 9);
    expect(segCross([0, 0], [10, 0], [11, -1], [11, 1])).toBeNull();
    const sq: [number, number][] = [[0, 0], [2, 0], [2, 2], [0, 2]];
    expect(inPoly([1, 1], sq)).toBe(true);
    expect(inPoly([3, 1], sq)).toBe(false);
  });
});

describe('scenery gates: containment', () => {
  it('finds the escape onto an unwalled closed road, with its stations and side', () => {
    const sc: SceneryLike = { paved_zones: { parts: [road] } };
    const r = containment(T, sc, { step: 2 });
    expect(r.escapes.length).toBeGreaterThan(0);
    const runs = escapeRuns(r.escapes);
    expect(runs.every((q) => q.side === 'right' && q.target === 'closed')).toBe(true);
    expect(Math.min(...runs.map((q) => q.s0))).toBeGreaterThan(20);
    expect(Math.max(...runs.map((q) => q.s1))).toBeLessThan(130);
  });
  it('a wall between the track and the road closes it', () => {
    const sc: SceneryLike = { paved_zones: { parts: [road] }, barriers: [{ kind: 'concrete', pts: [[0, -7, 0], [150, -7, 0]] }] };
    expect(containment(T, sc, { step: 2 }).escapes).toHaveLength(0);
  });
  it('a cone line counts as a barrier; listed runoff is allowed, not an escape', () => {
    const coned: SceneryLike = { paved_zones: { parts: [road] }, cone_lines: [{ pts: [[0, -8, 0], [150, -8, 0]] }] };
    expect(containment(T, coned, { step: 2 }).escapes).toHaveLength(0);
    const r = containment(T, { paved_zones: { parts: [road] } }, { step: 2, allowed: [{ target: 'closed', side: 'right', s0: 0, s1: 149, why: 'test' }] });
    expect(r.escapes).toHaveLength(0);
    expect(r.allowed.length).toBeGreaterThan(0);
  });
  it('runoff zones (kind runoff) are not targets', () => {
    expect(containment(T, { paved_zones: { parts: [{ ...road, kind: 'runoff' }] } }, { step: 2 }).escapes).toHaveLength(0);
  });
});

describe('scenery gates: pit connectivity and signs', () => {
  // a pit lane alongside the top straight on the left (y 66 .. 72), joining the edge at both ends
  const lane = { center: Array.from({ length: 101 }, (_, k) => [120.5 - k, 69, 0] as V3), left: Array.from({ length: 101 }, (_, k) => [122 - k * 1.02, 72, 0] as V3),
    right: Array.from({ length: 101 }, (_, k) => [122 - k * 1.02, 65, 0] as V3) };
  it('an open lane passes; a wall across its exit fails', () => {
    const ok = pitConnectivity(T, { pit_lane: { parts: [lane] } }, 280);
    expect(ok.ok).toBe(true);
    const shut = pitConnectivity(T, { pit_lane: { parts: [lane] }, barriers: [{ kind: 'concrete', pts: [[25, 60, 0], [25, 75, 0]] }] }, 280);
    expect(shut.ok).toBe(false);
    expect(shut.paths[0].crossings.length).toBeGreaterThan(0);
  });
  it('a board inside the pit lane or on the track fails; at the edge it passes', () => {
    const sc: SceneryLike = { pit_lane: { parts: [lane] }, landmarks: [
      { kind: 'brake', text: '1', x: 60, y: 69 }, { kind: 'corner', text: '2', x: 60, y: -1 }, { kind: 'brake', text: '3', x: 60, y: -8 }] };
    const r = signPlacement(T, sc);
    expect(r.checked).toBe(3);
    expect(r.bad.map((b) => b.text).sort()).toEqual(['1', '2']);
  });
});

describe('scenery gates: the lane driven on two paths (round 7, owner note 37)', () => {
  // the same 7 m lane as above, left of the top straight (y 65 .. 72)
  const lane = { center: Array.from({ length: 101 }, (_, k) => [120.5 - k, 68.5, 0] as V3), left: Array.from({ length: 101 }, (_, k) => [122 - k * 1.02, 72, 0] as V3),
    right: Array.from({ length: 101 }, (_, k) => [122 - k * 1.02, 65, 0] as V3) };
  it('an open lane passes', () => {
    const r = laneClearance(T, { pit_lane: { parts: [lane] } });
    expect(r.blocked).toHaveLength(0);
    expect(r.pinched).toHaveLength(0);
  });
  it('a cone line converging across the lane into its outer wall fails, though the centre path never crosses it', () => {
    const cones: SceneryLike = { pit_lane: { parts: [lane] }, cone_lines: [{ pts: [[70, 65.2, 0], [40, 71.5, 0]], src: 'test cones' }] };
    const r = laneClearance(T, cones);
    expect(r.blocked.some((b) => b.includes('test cones'))).toBe(true);
    expect(pitConnectivity(T, cones, 280).ok).toBe(false);
  });
  it('a wall end standing in the lane fails; walls along its edges pass', () => {
    const edges: SceneryLike = { pit_lane: { parts: [lane] }, barriers: [{ kind: 'concrete', pts: [[122, 72.1, 0], [20, 72.1, 0]] }, { kind: 'concrete', pts: [[122, 64.9, 0], [20, 64.9, 0]] }] };
    expect(laneClearance(T, edges).blocked).toHaveLength(0);
    const stub: SceneryLike = { pit_lane: { parts: [lane] }, barriers: [{ kind: 'concrete', pts: [[60, 72.1, 0], [60, 69.5, 0]], src: 'stub' }] };
    expect(laneClearance(T, stub).blocked.some((b) => b.includes('stub'))).toBe(true);
  });
});

describe('scenery gates: exposed wall ends (round 7, owner notes 39 / 41)', () => {
  // the bottom straight runs +x (stations 0..150), its right side is y < -5; walls on the right
  const wall = (x0: number, x1: number, y: number, src: string) => ({ kind: 'concrete', pts: [[x0, y, 0], [x1, y, 0]] as V3[], src });
  it('a downstream run starting closer to the track than the upstream run ends is exposed; lapped the other way it passes', () => {
    const bad = exposedEnds(T, { barriers: [wall(20, 60, -9, 'up'), wall(70, 120, -7, 'down')] });
    expect(bad.exposed.some((e) => e.label === 'concrete: down' && e.side === 'right')).toBe(true);
    const good = exposedEnds(T, { barriers: [wall(20, 60, -7, 'up'), wall(55, 120, -9, 'down')] });
    expect(good.exposed.some((e) => e.label === 'concrete: down')).toBe(false);
  });
  it('a run start near the edge with no cushion fails; a tyre cushion at its head or a taper passes; one joined polyline passes', () => {
    expect(exposedEnds(T, { barriers: [wall(40, 120, -6, 'bare')] }).exposed).toHaveLength(1);
    const cushion = exposedEnds(T, { barriers: [wall(40, 120, -6, 'cushioned'), { kind: 'tyres', pts: [[33, -6, 0], [40, -6, 0]], src: 'cushion' }] });
    expect(cushion.exposed).toHaveLength(0);
    const tapered = exposedEnds(T, { barriers: [{ kind: 'concrete', pts: [[30, -10, 0], [42, -6, 0], [120, -6, 0]], src: 'taper' }] });
    expect(tapered.exposed).toHaveLength(0);
    // beyond the 30 m reach (round 14B; 8 m before) a head is not checked
    expect(exposedEnds(T, { barriers: [wall(40, 120, -40, 'far')] }).exposed).toHaveLength(0);
    // a wall leaving the edge at a right angle (across a runoff) faces across the lap, not along it
    expect(exposedEnds(T, { barriers: [{ kind: 'concrete', pts: [[60, -6, 0], [60, -30, 0]], src: 'across' }] }).exposed).toHaveLength(0);
  });
  it('a tyre wall starting bare near the edge fails (Sonoma owner note 67); joined to the wall it meets, it passes', () => {
    const tyres = (x0: number, x1: number, y: number, src: string) => ({ kind: 'tyres', pts: [[x0, y, 0], [x1, y, 0]] as V3[], src });
    const bare = exposedEnds(T, { barriers: [tyres(40, 120, -6, 'bare tyres')] });
    expect(bare.exposed.some((e) => e.label === 'tyres: bare tyres')).toBe(true);
    // the wall along the dark line converging onto the tyres' head
    const joined = exposedEnds(T, { barriers: [{ kind: 'concrete', pts: [[10, -14, 0], [40, -6, 0]], src: 'onto' }, tyres(40, 120, -6, 'joined tyres')] });
    expect(joined.exposed.some((e) => e.label === 'tyres: joined tyres')).toBe(false);
    // a long tyre run is not a cushion even if its tail meets a wall
    const long = exposedEnds(T, { barriers: [tyres(20, 40, -6, 'long'), wall(40, 120, -6, 'w')] });
    expect(long.exposed.some((e) => e.label === 'tyres: long')).toBe(true);
  });
});

describe('scenery gates: wall ends within 30 m (Sonoma round 14B, owner round-13 drive at T10)', () => {
  const wall = (x0: number, x1: number, y: number, src: string) => ({ kind: 'concrete', pts: [[x0, y, 0], [x1, y, 0]] as V3[], src });
  const tyres = (pts: V3[], src: string) => ({ kind: 'tyres', pts, src });
  it('a bare concrete head 11 m out fails now (the 8 m gate never saw it); 7 m out it fails as before', () => {
    expect(exposedEnds(T, { barriers: [wall(40, 120, -16, 'head 11 m')] }).exposed.map((e) => e.label)).toEqual(['concrete: head 11 m']);
    expect(exposedEnds(T, { barriers: [wall(40, 120, -16, 'head 11 m')] }, { near: 8 }).exposed).toHaveLength(0);   // the old reach
    expect(exposedEnds(T, { barriers: [wall(40, 120, -12, 'head 7 m')] }).exposed).toHaveLength(1);
  });
  it('T10: a run whose head stands INSIDE a long outer wall is not protected by it; tyres from the outer wall to the head are', () => {
    // the outer wall 18 m out from s 0 to 140 (run 28), the short wall from s 60 at 11 m out angling to 7 m (run 37)
    // (its own head leaves the track at a right angle from 55 m out, so only the inner run's head is in question)
    const outer = { kind: 'concrete', pts: [[0, -60, 0], [0, -23, 0], [140, -23, 0]] as V3[], src: 'outer' };
    const inner = { kind: 'concrete', pts: [[60, -16, 0], [100, -14, 0], [123, -12, 0]] as V3[], src: 'inner' };
    const bare = exposedEnds(T, { barriers: [outer, inner] });
    expect(bare.exposed.some((e) => e.label === 'concrete: inner')).toBe(true);
    // a tyre wall from the outer wall (upstream) onto the inner run's head closes it (joined); the tyres' own head
    // stands on the outer wall (joined too)
    const closed = exposedEnds(T, { barriers: [outer, inner, tyres([[40, -23, 0], [50, -19.5, 0], [60, -16, 0]], 'tyre link')] });
    expect(closed.exposed).toHaveLength(0);
    // tyres capping the head (a cushion of <= 12 m whose tail joins the wall) close it too
    const capped = exposedEnds(T, { barriers: [outer, inner, tyres([[50, -16, 0], [60, -16, 0]], 'cap')] });
    expect(capped.exposed).toHaveLength(0);
  });
  it('a pit wall and an armco head at 20 m are checked; a tyre run head at 20 m keeps the 8 m reach', () => {
    expect(exposedEnds(T, { barriers: [{ kind: 'pitwall', pts: [[40, -25, 0], [120, -25, 0]], src: 'pw' }] }).exposed).toHaveLength(1);
    expect(exposedEnds(T, { barriers: [{ kind: 'armco', pts: [[40, -25, 0], [120, -25, 0]], src: 'ar' }] }).exposed).toHaveLength(1);
    expect(exposedEnds(T, { barriers: [tyres([[40, -25, 0], [120, -25, 0]], 'far tyres')] }).exposed).toHaveLength(0);
  });
});

describe('scenery gates: degenerate runs (Sonoma round 14C, issue #12, judge r14b A14)', () => {
  const wall = (x0: number, x1: number, y: number, src: string) => ({ kind: 'concrete', pts: [[x0, y, 0], [x1, y, 0]] as V3[], src });
  it('a zero-length tyre "bundle" at a wall head is no cushion and no join: listed as degenerate, the head exposed', () => {
    // the s 2347 case: three coincident points at the head of a wall standing 1 m beyond the right edge
    const bundle = { kind: 'tyres', pts: [[40, -6, 0], [40, -6, 0], [40, -6, 0]] as V3[], src: 'bundle at the head' };
    const r = exposedEnds(T, { barriers: [wall(40, 120, -6, 'far wall'), bundle] });
    expect(r.degenerate.map((d) => d.label)).toEqual(['tyres run 1: bundle at the head']);
    expect(r.degenerate[0].len).toBe(0);
    expect(r.exposed.map((e) => e.label)).toEqual(['concrete: far wall']);
    expect(r.ok.some((o) => o.how.includes('run 1'))).toBe(false);
    // 0.4 m and a single point are degenerate too; 0.5 m is not
    expect(degenerateRuns({ barriers: [wall(40, 40.4, -6, 'a'), { kind: 'armco', pts: [[1, -6, 0]] as V3[], src: 'b' }, wall(50, 50.5, -6, 'c'), { kind: 'fence', pts: [[1, -6, 0], [1, -6, 0]] as V3[] }] })
      .map((d) => d.k)).toEqual([0, 1]);
    // drawn as declared (2 m along the head, its tail on the wall) the bundle is the head's cushion again
    const drawn = exposedEnds(T, { barriers: [wall(40, 120, -6, 'far wall'), { ...bundle, pts: [[38, -6, 0], [40, -6, 0]] as V3[] }] });
    expect(drawn.degenerate).toHaveLength(0);
    expect(drawn.exposed).toHaveLength(0);
  });
  it('a degenerate run is never a lapping run: neither for a wall head nor across a hole in a barrier line', () => {
    // a 0.2 m stub closer to the track just upstream of a bare head does not lap it
    const r = exposedEnds(T, { barriers: [wall(40, 120, -8, 'head'), wall(30, 30.2, -6, 'stub')] });
    expect(r.exposed.map((e) => e.label)).toEqual(['concrete: head']);
    expect(r.degenerate).toHaveLength(1);
    // a 6 m hole 15 m out with a zero-length run at its midpoint is still a hole
    const a = { kind: 'concrete', pts: [[20, -20, 0], [64, -20, 0]] as V3[], src: 'a' }, b = { kind: 'concrete', pts: [[70, -20, 0], [120, -20, 0]] as V3[], src: 'b' };
    expect(runGaps(T, { barriers: [a, b, { kind: 'tyres', pts: [[67, -20, 0], [67, -20, 0]] as V3[], src: 'dot' }] }).gaps).toHaveLength(1);
    expect(runGaps(T, { barriers: [a, b, { kind: 'tyres', pts: [[60, -21.5, 0], [74, -21.5, 0]] as V3[], src: 'lap' }] }).gaps).toHaveLength(0);
  });
});

describe('scenery gates: tyre facings (round 7b, owner note 48)', () => {
  const conc = { kind: 'concrete', pts: [[20, -12, 0], [120, -12, 0]] as V3[], src: 'wall' };
  it('a tyre run parallel 1.5 m in front of a wall is side by side; as a facing (0.5 m) or angling in it passes', () => {
    expect(sideBySide(T, { barriers: [conc, { kind: 'tyres', pts: [[40, -10.5, 0], [90, -10.5, 0]], src: 'beside' }] })).toHaveLength(1);
    expect(sideBySide(T, { barriers: [conc, { kind: 'tyres', pts: [[40, -11.5, 0], [90, -11.5, 0]], src: 'facing' }] })).toHaveLength(0);
    expect(sideBySide(T, { barriers: [conc, { kind: 'tyres', pts: [[40, -6, 0], [60, -11.5, 0]], src: 'taper' }] })).toHaveLength(0);
  });
  it('a tyre run meeting the wall end to end passes', () => {
    expect(sideBySide(T, { barriers: [conc, { kind: 'tyres', pts: [[0, -12, 0], [19.5, -12, 0]], src: 'end' }] })).toHaveLength(0);
  });
});

describe('scenery gates: wall tops, wall-tyre joins and tyre faces (round 12, Sonoma judge r11 N65 / N67)', () => {
  // a wall 10 m right of the bottom straight whose ground drops into a 3 m ditch at x 40-44 (the T10-T11 boarded wall)
  const ditch = (x: number) => (x >= 40 && x <= 44 ? -3 : 0);
  const pts: V3[] = [];
  for (let x = 20; x <= 64; x += 2) pts.push([x, -10, ditch(x)]);
  const board = (x: number, z: number) => ({ kind: 'sign', text: 'SONOMA RACEWAY', x, y: -9.88, z, src: 'wall board on W (boards)', top: 2.5 });
  it('a wall that follows a ditch steps; level across it (top_z) it passes, and a board must stand on its top', () => {
    const sunk = wallTops(T, { barriers: [{ kind: 'concrete', h: 1.2, pts, src: 'declared: W' }], landmarks: [board(42, -1.8)] } as never);
    expect(sunk.steps).toHaveLength(1);
    expect(sunk.boards).toHaveLength(0);   // the board sits on the sunk wall's top: the step is the wall's
    const level = { kind: 'concrete', h: 1.2, pts, src: 'declared: W', top_z: pts.map(() => 1.2) };
    const ok = wallTops(T, { barriers: [level], landmarks: [board(42, 1.2)] } as never);
    expect(ok.steps).toHaveLength(0);
    expect(ok.boards).toHaveLength(0);
    // a board left in the ditch in front of a level wall
    expect(wallTops(T, { barriers: [level], landmarks: [board(42, -1.8)] } as never).boards).toHaveLength(1);
  });
  it('a tyre run whose rows stand toward the track proud of the wall ending on its head fails; rows behind the line pass', () => {
    const wall = { kind: 'concrete', pts: [[10, -12, 0], [25, -9, 0], [40, -6, 0]] as V3[], src: 'onto the tyres' };
    const fwd = { kind: 'tyres', pts: [[40, -6, 0], [70, -6, 0], [100, -6, 0]] as V3[], src: 'tyres' };
    const j = joinFaces(T, { barriers: [wall, fwd] });
    expect(j).toHaveLength(1);
    expect(j[0].downstream).toBe('tyres');
    expect(j[0].step).toBeCloseTo(0.6 + 0.31 - 0.18, 2);   // 0.73 m proud: the Sonoma s 3398 head
    const rev = { ...fwd, pts: [...fwd.pts].reverse() };
    expect(joinFaces(T, { barriers: [wall, rev] })[0].step).toBeCloseTo(0.31 - 0.18, 2);
  });
  it('a tyre run drawn with its face on the road fails; reversed (rows behind the line) it passes', () => {
    const fwd = { kind: 'tyres', pts: [[40, -5.55, 0], [100, -5.55, 0]] as V3[], src: 'at the edge' };
    const bad = tyreFaces(T, { barriers: [fwd] });
    expect(bad).toHaveLength(1);
    expect(bad[0].face).toBeCloseTo(0.55 - 0.91, 2);
    expect(tyreFaces(T, { barriers: [{ ...fwd, pts: [...fwd.pts].reverse() }] })).toHaveLength(0);
  });
});

describe('scenery gates: run gaps (round 13, Sonoma owner note 131)', () => {
  // one tyre line 20 m right of the bottom straight, split 13.5 m apart at x 60-73.5 (the hole past the footbridge)
  const a = { kind: 'tyres', pts: [[10, -20, 0], [35, -20, 0], [60, -20, 0]] as V3[], src: 'part 1' };
  const b = { kind: 'tyres', pts: [[73.5, -20, 0], [100, -20, 0], [130, -20, 0]] as V3[], src: 'part 2' };
  it('two runs of one line with a hole 20 m out fail (the wall-ends and joins gates do not look there)', () => {
    const r = runGaps(T, { barriers: [a, b] });
    expect(r.gaps).toHaveLength(1);
    expect(r.gaps[0].gap).toBeCloseTo(13.5, 1);
    expect(r.gaps[0].side).toBe('right');
    expect(exposedEnds(T, { barriers: [a, b] }).exposed).toHaveLength(0);
    expect(joinFaces(T, { barriers: [a, b] })).toHaveLength(0);
  });
  it('one run, a road through the hole, a lapping run or a declared opening pass', () => {
    expect(runGaps(T, { barriers: [{ ...a, pts: [...a.pts, ...b.pts] }] }).gaps).toHaveLength(0);
    const cross = { turn: 'access', kind: 'closed_road', center: [[67, -8, 0], [67, -40, 0]] as V3[], left: [[64, -8, 0], [64, -40, 0]] as V3[], right: [[70, -8, 0], [70, -40, 0]] as V3[] };
    expect(runGaps(T, { barriers: [a, b], paved_zones: { parts: [cross] } }).gaps).toHaveLength(0);
    const lap = { kind: 'concrete', pts: [[55, -21.5, 0], [80, -21.5, 0]] as V3[], src: 'behind' };
    expect(runGaps(T, { barriers: [a, b, lap] }).gaps).toHaveLength(0);
    expect(runGaps(T, { barriers: [a, b] }, { openings: [{ x: 67, y: -20, why: 'gate' }] }).gaps).toHaveLength(0);
  });
  it('runs that do not face each other (side by side, or at right angles) are not a hole', () => {
    const perp = { kind: 'tyres', pts: [[66, -25, 0], [66, -45, 0]] as V3[], src: 'across' };
    expect(runGaps(T, { barriers: [a, perp] }).gaps).toHaveLength(0);
  });
});

describe('scenery gates: cones off the surface (Buttonwillow round 11, judge r10 Atlantic mouth)', () => {
  // the bottom straight runs along y = 0 with its right edge at y = -5
  it('places the spots as the app does: every spacing m, the remainder carried over a vertex', () => {
    expect(coneSpots([[0, 0, 0], [3, 0, 0], [6, 0, 0]], 2).map((p) => p[0])).toEqual([0, 2, 4]);
    expect(coneSpots([[0, 0, 0], [3, 0, 0], [6, 0, 0]], 2).length).toBe(3);
  });
  it('a mouth line on or beyond the edge passes; one bulging 0.5 m onto the track fails at that cone', () => {
    const ok: SceneryLike = { cone_lines: [{ pts: [[40, -5.1, 0], [70, -5.1, 0]], src: 'mouth', spacing_m: 2 }] };
    const r0 = conesOffSurface(T, ok);
    expect(r0.bad).toHaveLength(0);
    expect(r0.cones).toBe(15);
    const bulge: SceneryLike = { cone_lines: [{ pts: [[40, -5.1, 0], [55, -4.5, 0], [70, -5.1, 0]], src: 'mouth', spacing_m: 2 }] };
    const r1 = conesOffSurface(T, bulge);
    expect(r1.bad.length).toBeGreaterThan(0);
    expect(r1.bad.every((b) => b.side === 'right' && b.depth > 0.15 && b.s > 40 && b.s < 70)).toBe(true);
    expect(r1.worst).toBeCloseTo(0.5, 1);
    // 0.1 m inside is within the 0.15 m tolerance
    expect(conesOffSurface(T, { cone_lines: [{ pts: [[40, -4.9, 0], [70, -4.9, 0]], spacing_m: 2 }] }).bad).toHaveLength(0);
  });
  it("a pit lane's separation line on the shared pavement is not gated: pit_exit_cones, the lane paving, a declared exemption", () => {
    const inside: V3[] = [[40, -3, 0], [70, -3, 0]];
    expect(conesOffSurface(T, { cone_lines: [{ pts: inside, src: 'pit-in line', spacing_m: 2 }] }).bad.length).toBeGreaterThan(0);
    expect(conesOffSurface(T, { pit_exit_cones: { pts: inside, spacing_m: 2 } }).bad).toHaveLength(0);
    expect(conesOffSurface(T, { cone_lines: [{ pts: inside, src: 'pit-in line', spacing_m: 2 }] }, 0.15, 0.5, [{ src: 'pit-in', why: 'test' }]).bad).toHaveLength(0);
    const lane = { center: [[40, -2, 0], [70, -2, 0]] as V3[], left: [[40, -1, 0], [70, -1, 0]] as V3[], right: [[40, -3, 0], [70, -3, 0]] as V3[] };
    const r = conesOffSurface(T, { pit_lane: { parts: [lane] }, cone_lines: [{ pts: inside, src: 'blend', spacing_m: 2 }] });
    expect(r.bad).toHaveLength(0);
    expect(r.onLane).toBe(15);
  });
});
