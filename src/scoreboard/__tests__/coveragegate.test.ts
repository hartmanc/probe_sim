// Coverage and pit-lane gates (tools/track/gates/coverageGate.ts, 21 Oct 2026): matching inventory rows to scenery
// objects by kind, side and station (+-15 m), UNSUPPORTED objects, the pass rule, heights, and the pit-lane walls.
import { describe, expect, it } from 'vitest';
import { coverage, missingRuns, pitLaneWalls, sceneryObjects, type Inventory, type InvRow } from '../../../tools/track/gates/coverageGate';
import type { TrackLike, V3 } from '../../../tools/track/gates/sceneryGates';

// the 400 m loop of scenerygates.test.ts: bottom straight y = 0 from x 0 to 150 driving +x (left = +y), 1 m stations
function loop(): TrackLike {
  const C: V3[] = [], L: V3[] = [], R: V3[] = [];
  const Ls = 150, Rr = 30, n = Math.round(2 * Ls + 2 * Math.PI * Rr);
  for (let k = 0; k < n; k++) {
    let s = k, x: number, y: number, h: number;
    if (s < Ls) { x = s; y = 0; h = 0; }
    else if ((s -= Ls) < Math.PI * Rr) { const a = s / Rr; x = Ls + Rr * Math.sin(a); y = Rr - Rr * Math.cos(a); h = a; }
    else if ((s -= Math.PI * Rr) < Ls) { x = Ls - s; y = 2 * Rr; h = Math.PI; }
    else { s -= Ls; const a = s / Rr; x = -Rr * Math.sin(a); y = Rr + Rr * Math.cos(a); h = Math.PI + a; }
    const nx = -Math.sin(h), ny = Math.cos(h);
    C.push([x, y, 0]); L.push([x + nx * 5, y + ny * 5, 0]); R.push([x - nx * 5, y - ny * 5, 0]);
  }
  return { n, spacing_m: 1, center: C, left: L, right: R };
}
const T = loop();
const row = (s: number, side: InvRow['side'], kind: string, attrs: Record<string, unknown> = {}): InvRow =>
  ({ s, t: null, side, kind, attrs, confidence: 0.9, source: 'test' });
const inv = (rows: InvRow[]): Inventory => ({ track: 'test', length_m: T.n, rows });
const wall = (x0: number, x1: number, y: number, src = 'c20_s0000: test', h = 1, kind = 'concrete', fence = 0) =>
  ({ kind, h, fence, src, pts: [[x0, y, 0], [x1, y, 0]] as V3[] });

describe('coverage gate: matching', () => {
  it('a wall row is covered by a wall on its side within 15 m, missing without one', () => {
    const sc = { barriers: [wall(20, 120, -8)] };
    expect(coverage(T, sc, inv([row(60, 'right', 'wall')])).missing).toHaveLength(0);
    const r = coverage(T, { barriers: [] }, inv([row(60, 'right', 'wall')]));
    expect(r.missing).toHaveLength(1);
    expect(r.missing[0]).toMatchObject({ s: 60, side: 'right', kind: 'wall' });
    expect(r.pass).toBe(false);
  });
  it('the side matters: a wall on the left does not cover a right-side row', () => {
    const r = coverage(T, { barriers: [wall(20, 120, 8)] }, inv([row(60, 'right', 'wall')]));
    expect(r.missing.map((m) => m.side)).toEqual(['right']);
  });
  it('the kind matters: a concrete wall does not cover a tyre-wall row; a tyres barrier does', () => {
    expect(coverage(T, { barriers: [wall(20, 120, -8)] }, inv([row(60, 'right', 'tyre_wall')])).missing).toHaveLength(1);
    expect(coverage(T, { barriers: [wall(20, 120, -8, 'c20_s0000', 1, 'tyres')] }, inv([row(60, 'right', 'tyre_wall')])).missing).toHaveLength(0);
  });
  it('tolerance is +-15 m along the lap', () => {
    const sc = { barriers: [wall(100, 140, -8)] };
    expect(coverage(T, sc, inv([row(88, 'right', 'wall')])).missing).toHaveLength(0);
    expect(coverage(T, sc, inv([row(80, 'right', 'wall')])).missing).toHaveLength(1);
    expect(coverage(T, sc, inv([row(80, 'right', 'wall')]), { tol: 25 }).missing).toHaveLength(0);
  });
  it('a catch fence on a wall covers a fence row; kerb strips map side +1 to left', () => {
    const sc = { barriers: [wall(20, 120, 8, 'c20_s0000', 1, 'concrete', 3)], kerbs: { strips: [{ side: 1, s0: 40, s1: 70, src: 'c20_s0000' }] } };
    const r = coverage(T, sc, inv([row(60, 'left', 'fence'), row(55, 'left', 'kerb'), row(55, 'right', 'kerb')]));
    expect(r.missing.map((m) => `${m.kind} ${m.side}`)).toEqual(['kerb right']);
  });
  it("'both' needs each side; 'ahead' rows are skipped unless they carry a distance", () => {
    const sc = { barriers: [wall(20, 120, 8)] };
    const r = coverage(T, sc, inv([row(60, 'both', 'wall'), row(60, 'ahead', 'wall'), row(60, 'ahead', 'wall', { ahead_m: 30 })]));
    expect(r.skipped).toBe(1);
    expect(r.missing.map((m) => m.side)).toEqual(['right']);
  });
  it('pit-scope rows are left to the pit-lane gate', () => {
    expect(coverage(T, { barriers: [] }, inv([{ ...row(60, 'right', 'wall'), scope: 'pit' }])).missing).toHaveLength(0);
  });
});

describe('coverage gate: unsupported objects, pass rule, heights', () => {
  it('an object with neither a capture source nor an inventory row is UNSUPPORTED', () => {
    const osm = { barriers: [wall(20, 120, -8, 'osm:123')] };
    expect(coverage(T, osm, inv([])).unsupported).toHaveLength(1);
    expect(coverage(T, osm, inv([row(70, 'right', 'wall')])).unsupported).toHaveLength(0);
    expect(coverage(T, osm, inv([row(70, 'left', 'wall')])).unsupported).toHaveLength(1);
    expect(coverage(T, { barriers: [wall(20, 120, -8, 'declared: c20_s1815 bright band')] }, inv([])).unsupported).toHaveLength(0);
    expect(coverage(T, { barriers: [wall(20, 120, -8, 'Street View 5MY4xR9O7etAXEHnZCVnGQ')] }, inv([])).unsupported).toHaveLength(0);
  });
  it('passes with only masts / stands missing; fails on a missing kerb, fence, tyre wall, wall or bridge', () => {
    const ok = coverage(T, { barriers: [] }, inv([row(60, 'right', 'mast'), row(60, 'left', 'stand')]));
    expect(ok.missing).toHaveLength(2);
    expect(ok.pass).toBe(true);
    for (const k of ['kerb', 'fence', 'tyre_wall', 'wall', 'bridge']) expect(coverage(T, {}, inv([row(60, 'right', k)])).pass).toBe(false);
  });
  it('lists a measured wall height that the package misses by more than max(0.3 m, 25 %)', () => {
    const sc = { barriers: [wall(20, 120, -8)] };
    const r = coverage(T, sc, inv([row(60, 'right', 'wall', { h_m: 4.0, h_method: 'horizon-ratio' }), row(80, 'right', 'wall', { h_m: 1.1, h_method: 'jersey-ref' }),
      row(90, 'right', 'wall', { h_m: 4.0, h_method: 'unmeasured' })]));
    expect(r.heights).toHaveLength(1);
    expect(r.heights[0]).toMatchObject({ s: 60, row_h: 4, obj_h: 1 });
  });
  it('bridges match on either side; runs group consecutive rows', () => {
    const sc = { bridges: [{ id: 'b', kind: 'foot', s: 100, deck_z: 6, deck_src: 'lidar' }] };
    expect(coverage(T, sc, inv([row(110, 'both', 'bridge')])).missing).toHaveLength(0);
    expect(sceneryObjects(T, sc)[0].side).toBe('both');
    const r = coverage(T, {}, inv([row(10, 'right', 'wall'), row(40, 'right', 'wall'), row(130, 'right', 'wall')]));
    expect(missingRuns(r.missing).map((m) => [m.s0, m.s1, m.n])).toEqual([[10, 40, 2], [130, 130, 1]]);
  });
});

describe('pit-lane gate', () => {
  // a pit lane beside the bottom straight on the right (y -14 .. -20), driving +x like the track, track_s = x
  const lane = { center: Array.from({ length: 101 }, (_, k) => [20 + k, -17, 0] as V3), left: Array.from({ length: 101 }, (_, k) => [20 + k, -14, 0] as V3),
    right: Array.from({ length: 101 }, (_, k) => [20 + k, -20, 0] as V3), track_s: Array.from({ length: 101 }, (_, k) => 20 + k) };
  const pitRow = (s: number, side: 'left' | 'right'): InvRow => ({ ...row(s, side, 'wall', { type: 'pit wall' }), scope: 'pit' });
  it('a pit wall row needs a declaration and a barrier on that side of the lane', () => {
    const sc = { pit_lane: { parts: [lane] }, barriers: [wall(20, 120, -12)] };
    const ok = pitLaneWalls(T, sc, inv([pitRow(60, 'left')]), [{ side: 'left', s0: 20, s1: 120 }]);
    expect(ok.pass).toBe(true);
    const undeclared = pitLaneWalls(T, sc, inv([pitRow(60, 'left')]), []);
    expect(undeclared.undeclared).toHaveLength(1);
    expect(undeclared.pass).toBe(false);
    const absent = pitLaneWalls(T, sc, inv([pitRow(60, 'right')]), [{ side: 'right', s0: 20, s1: 120 }]);
    expect(absent.absent).toHaveLength(1);
  });
  it('without a pit lane in the package the gate fails', () => {
    expect(pitLaneWalls(T, {}, inv([]), []).pass).toBe(false);
  });
});
