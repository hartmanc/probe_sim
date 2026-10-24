// Pure parts of the stage-3 scenery gates (tools/track/gates/sceneryGates.ts, 20 Oct 2026): segment crossing, polygon
// test, containment escapes / barriers / allowed runoff, pit connectivity and sign placement on a synthetic straight.
import { describe, expect, it } from 'vitest';
import { coneSpots, conesOffSurface, containment, escapeRuns, exposedEnds, inPoly, laneClearance, pitConnectivity, segCross, sideBySide, signPlacement, type SceneryLike, type TrackLike, type V3 } from '../../../tools/track/gates/sceneryGates';

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
    expect(exposedEnds(T, { barriers: [wall(40, 120, -20, 'far')] }).exposed).toHaveLength(0);
    // a wall leaving the edge at a right angle (across a runoff) faces across the lap, not along it
    expect(exposedEnds(T, { barriers: [{ kind: 'concrete', pts: [[60, -6, 0], [60, -30, 0]], src: 'across' }] }).exposed).toHaveLength(0);
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
