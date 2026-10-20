// Pure parts of the stage-3 scenery gates (tools/track/gates/sceneryGates.ts, 20 Oct 2026): segment crossing, polygon
// test, containment escapes / barriers / allowed runoff, pit connectivity and sign placement on a synthetic straight.
import { describe, expect, it } from 'vitest';
import { containment, escapeRuns, inPoly, pitConnectivity, segCross, signPlacement, type SceneryLike, type TrackLike, type V3 } from '../../../tools/track/gates/sceneryGates';

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
