// Barrier colour sections (Buttonwillow judge r2, 20 Oct 2026): a wall run without `pattern` / `sections` is drawn in one
// colour exactly as before (null: the old code path); a pattern alternates its colours along the run's length; explicit
// sections override it where they lie.
import { describe, expect, test } from 'vitest';
import { barrierSections, sliceLine } from '../scenery';

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
