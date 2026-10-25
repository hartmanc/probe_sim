// Barrier colour sections (Buttonwillow judge r2, 20 Oct 2026): a wall run without `pattern` / `sections` is drawn in one
// colour exactly as before (null: the old code path); a pattern alternates its colours along the run's length; explicit
// sections override it where they lie.
import { describe, expect, test } from 'vitest';
import { barrierSections, paintLineZ, sliceLine, trussMembers, tyreRows, wallHalfThickness } from '../scenery';

const P: [number, number, number][] = [[0, 0, 0], [10, 0, 0], [10, 10, 0]];

describe('barrier colour sections', () => {
  test('no pattern, no sections: one colour, the old path', () => {
    expect(barrierSections(P, { color: '#ffffff' })).toBeNull();
  });
  test('alternating pattern over the run length', () => {
    const s = barrierSections(P, { pattern: { colors: ['#fff', '#c00'], period_m: 4 } })!;
    expect(s[0]).toEqual({ a: 0, b: 2, color: '#fff' });
    expect(s[1]).toEqual({ a: 2, b: 4, color: '#c00' });
    expect(s[s.length - 1].b).toBeCloseTo(20);
  });
  test('explicit sections override the base colour', () => {
    const s = barrierSections(P, { color: '#fff', sections: [{ from_m: 5, to_m: 8, color: '#222' }] })!;
    expect(s.map((q) => q.color)).toEqual(['#fff', '#222', '#fff']);
    expect(s[1].a).toBe(5); expect(s[1].b).toBe(8);
  });
  test('sliceLine interpolates the ends and follows corners', () => {
    const q = sliceLine(P, 5, 15);
    expect(q[0]).toEqual([5, 0, 0]);
    expect(q[1]).toEqual([10, 0, 0]);
    expect(q[q.length - 1]).toEqual([10, 5, 0]);
  });
});

// Sonoma round 14D: a deep tyre wall's rows, a thick wall's width and the open truss footbridge's lattice ends.
describe('round 14D drawing helpers', () => {
  test('tyre rows: absent 2 (the old two rows), else the given count, 1-8', () => {
    expect(tyreRows({})).toEqual([0, 1]);
    expect(tyreRows({ rows: 4 })).toEqual([0, 1, 2, 3]);
    expect(tyreRows({ rows: 0 })).toEqual([0]);
    expect(tyreRows({ rows: 20 })).toHaveLength(8);
  });
  test('wall half thickness: absent 0.18 (the 0.36 m wall), else w / 2', () => {
    expect(wallHalfThickness({})).toBe(0.18);
    expect(wallHalfThickness({ w: 0.96 })).toBeCloseTo(0.48, 6);
  });
  test('truss end sections: verticals and diagonals over the first and last 4.5 m only, at both piers', () => {
    const m = trussMembers(34);
    expect(m.length).toBe(2 * (4 + 3));                          // 3 bays of 1.5 m: 4 verticals, 3 diagonals per end
    expect(Math.max(...m.map((q) => Math.abs(q.x)))).toBeCloseTo(17, 6);
    expect(Math.min(...m.map((q) => Math.abs(q.x)))).toBeGreaterThanOrEqual(17 - 4.5 - 1e-9);
    expect(m.filter((q) => q.rot !== 0).every((q) => Math.abs(q.len - Math.hypot(1.5, 1.1)) < 1e-9)).toBe(true);
    // a short span keeps its middle open: each end at most a quarter of it
    expect(Math.min(...trussMembers(8).map((q) => Math.abs(q.x)))).toBeGreaterThanOrEqual(2 - 1e-9);
  });
});

describe('round 14D paint lines on open ground', () => {
  test('a line keeps its package height unless the drawn terrain rises over it', () => {
    expect(paintLineZ(2.38, 0, 0)).toBe(2.38);
    expect(paintLineZ(2.38, 0, 0, () => 2.30)).toBe(2.38);             // a zone / ribbon over the sunk terrain: unchanged
    expect(paintLineZ(2.38, 0, 0, () => 2.45)).toBeCloseTo(2.458, 6);   // buried by the 3 m mesh: 0.008 m over it
  });
});
