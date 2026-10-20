// Coverage and pit-lane gates (tools/track/gates/coverageGate.ts, 21 Oct 2026): matching inventory rows to scenery
// objects by kind, side and station (+-15 m), UNSUPPORTED objects, the pass rule, heights, and the pit-lane walls.
import { describe, expect, it } from 'vitest';
import { coverage, dispositionProblem, missingRuns, pitLaneWalls, sceneryObjects, type Disposition, type Inventory, type InvRow } from '../../../tools/track/gates/coverageGate';
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
  it('every kind counts (codify round, 20 Oct 2026): a missing mast or stand fails without a disposition, as a missing kerb, fence, tyre wall, wall or bridge does', () => {
    const r = coverage(T, { barriers: [] }, inv([row(60, 'right', 'mast'), row(60, 'left', 'stand')]));
    expect(r.missing).toHaveLength(2);
    expect(r.pass).toBe(false);
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

describe('coverage gate: board heights and assignments (21 Oct 2026)', () => {
  it('ad boards standing on a declared wall count toward its height at their stations; boards on posts (no top) do not', () => {
    const w = { ...wall(20, 120, -8), src: 'declared: W (c20_s0000)' };
    const board = (x: number, top?: number) => ({ kind: 'sign', text: '', x, y: -8.1, z: 0, heading: 0, h: 2.5, w: 6,
      src: 'wall board on W (onboard)', ...(top !== undefined ? { top } : {}) });
    const rows = [row(60, 'right', 'wall', { h_m: 3.6, h_method: 'horizon-ratio' })];
    expect(coverage(T, { barriers: [w], landmarks: [board(58, 3.5), board(64, 3.5)] }, inv(rows)).heights).toHaveLength(0);
    // boards far away along the lap do not lift the wall at the row
    expect(coverage(T, { barriers: [w], landmarks: [board(100, 3.5)] }, inv(rows)).heights).toHaveLength(1);
    // boards on posts carry no `top`: the wall keeps its own height
    expect(coverage(T, { barriers: [w], landmarks: [board(60)] }, inv(rows)).heights[0]).toMatchObject({ obj_h: 1 });
  });
  it('a MISSING building row assigned to another round is ASSIGNED, not MISSING; any other kind is REJECTED and fails', () => {
    const rows = [row(60, 'right', 'building'), row(90, 'right', 'wall')];
    const sc = { barriers: [wall(80, 100, -8)] };
    const r = coverage(T, sc, inv(rows), { assigned: [{ kind: 'building', side: 'right', s: 60, to: 'buildings round' }] });
    expect(r.missing).toHaveLength(0);
    expect(r.assigned.map((a) => [a.kind, a.s, a.to])).toEqual([['building', 60, 'buildings round']]);
    expect(r.pass).toBe(true);
    const bad = coverage(T, { barriers: [] }, inv(rows), { assigned: [{ kind: 'wall', side: 'right', s: 90, to: 'buildings round' }] });
    expect(bad.rejected).toHaveLength(1);
    expect(bad.missing.map((m) => m.kind)).toContain('wall');
    expect(bad.pass).toBe(false);
    const stale = coverage(T, sc, inv(rows), { assigned: [{ kind: 'building', side: 'left', s: 60, to: 'buildings round' }] });
    expect(stale.unmatched).toHaveLength(1);
    expect(stale.missing.map((m) => m.kind)).toEqual(['building']);
  });
});

describe('coverage gate: manifest dispositions (codify round, 20 Oct 2026)', () => {
  const d = (kind: string, side: string, s: number, type: Disposition['type'], text: string): Disposition => ({ kind, side, s, type, text });
  const mastSc = { landmarks: [{ kind: 'mast', text: '', x: 100, y: -40, h: 20, src: 'Light masts: lidar spike, c20_s0000 base and shadow' }] };
  it('a MISSING mast passes with a valid disposition of each type and is listed as dispositioned', () => {
    const rows = [row(20, 'right', 'mast'), row(30, 'left', 'stand'), row(40, 'right', 'cone_line'), row(50, 'left', 'building')];
    const r = coverage(T, mastSc, inv(rows), { dispositions: [
      d('mast', 'right', 20, 'placed', 'Light masts (the mast at (100, -40), 80 m ahead)'),
      d('stand', 'left', 30, 'not resolvable', 'no seating footprint on c20_s3135 / c20_s3190'),
      d('cone_line', 'right', 40, 'rejected', 'a marshal holding a flag (onboard 1:56, t116)'),
      d('building', 'left', 50, 'assigned', 'buildings round'),
    ] });
    expect(r.missing).toHaveLength(0);
    expect(r.invalid).toHaveLength(0);
    expect(r.dispositioned.map((m) => [m.kind, m.disposition])).toEqual([['mast', 'placed'], ['stand', 'not resolvable'], ['cone_line', 'rejected'], ['building', 'assigned']]);
    expect(r.assigned.map((m) => m.kind)).toEqual(['building']);
    expect(r.pass).toBe(true);
  });
  it('a row without a disposition stays MISSING and fails; a disposition matches kind, side and station within 1 m', () => {
    const rows = [row(20, 'right', 'mast'), row(80, 'right', 'mast')];
    const ok = d('mast', 'right', 20.6, 'not resolvable', 'c20_s0000 shows no base');
    const r = coverage(T, mastSc, inv(rows), { dispositions: [ok, d('mast', 'left', 80, 'not resolvable', 'c20_s0000'), d('mast', 'right', 82, 'not resolvable', 'c20_s0000')] });
    expect(r.missing.map((m) => m.s)).toEqual([80]);
    expect(r.unmatchedDispositions).toHaveLength(2);
    expect(r.pass).toBe(false);
  });
  it('no disposition excuses a MISSING wall, fence, kerb, tyre wall or bridge: the line is INVALID and the gate fails', () => {
    for (const k of ['wall', 'fence', 'kerb', 'tyre_wall', 'bridge']) {
      const r = coverage(T, {}, inv([row(60, 'right', k)]), { dispositions: [d(k, 'right', 60, 'not resolvable', 'c20_s0000')] });
      expect(r.invalid).toHaveLength(1);
      expect(r.missing).toHaveLength(1);
      expect(r.pass).toBe(false);
    }
  });
  it('validates each type: rejected names evidence, not resolvable names a capture, placed names an object of the kind, assigned is for buildings only', () => {
    const objs = sceneryObjects(T, mastSc);
    expect(dispositionProblem(d('mast', 'right', 20, 'rejected', 'not there'), objs)).toMatch(/evidence/);
    expect(dispositionProblem(d('mast', 'right', 20, 'rejected', 'not on c20_o0440'), objs)).toBe('');
    expect(dispositionProblem(d('mast', 'right', 20, 'rejected', 'contradicted by the lidar'), objs)).toBe('');
    expect(dispositionProblem(d('mast', 'right', 20, 'not resolvable', 'the captures are poor'), objs)).toMatch(/capture/);
    expect(dispositionProblem(d('mast', 'right', 20, 'not resolvable', 'onboard 0:48 only'), objs)).toMatch(/capture/);
    expect(dispositionProblem(d('mast', 'right', 20, 'placed', 'Scoring tower (somewhere)'), objs)).toMatch(/no mast object/);
    expect(dispositionProblem(d('stand', 'right', 20, 'placed', 'Light masts'), objs)).toMatch(/no stand object/);
    expect(dispositionProblem(d('mast', 'right', 20, 'placed', 'light masts'), objs)).toBe('');
    expect(dispositionProblem(d('mast', 'right', 20, 'assigned', 'buildings round'), objs)).toMatch(/building/);
    expect(dispositionProblem(d('mast', 'right', 20, 'placed', ''), objs)).toMatch(/needs its text/);
    expect(dispositionProblem({ ...d('mast', 'right', 20, 'placed', 'x'), type: 'ignored' as Disposition['type'] }, objs)).toMatch(/not one of/);
  });
  it('an invalid disposition fails the gate even when its row is otherwise dispositioned', () => {
    const r = coverage(T, mastSc, inv([row(20, 'right', 'mast')]), { dispositions: [d('mast', 'right', 20, 'not resolvable', 'c20_s0000'), d('mast', 'right', 20, 'rejected', 'gone')] });
    expect(r.missing).toHaveLength(0);
    expect(r.invalid).toHaveLength(1);
    expect(r.pass).toBe(false);
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
