// The used-tyre look (Buttonwillow round 13, the owner's T2 note of 25 Oct 2026: "Try to make it look less dark / look
// like an actual stack of used tires"): every tyre wall on every track. A recorded casing colour darker than the used-
// rubber grey is lifted toward it, lighter ones are kept; each tyre of a stack has its own tread band and shade, the
// grooves between tyres stay darker than any tread, and a stack stays within its triangle budget.
import { describe, expect, test } from 'vitest';
import { TYRE_LOOK, tyreCasing, tyreStackGeometry } from '../scenery';

const lum = (hex: string) => { const v = parseInt(hex.slice(1), 16); return ((v >> 16) & 255) + ((v >> 8) & 255) + (v & 255); };

describe('tyre casing colour', () => {
  test('flat black is lifted toward the rubber grey, not past it', () => {
    const c = tyreCasing('#161616');
    expect(lum(c)).toBeGreaterThan(lum('#161616'));
    expect(lum(c)).toBeLessThanOrEqual(lum(TYRE_LOOK.rubber));
  });
  test('white stacks and lighter recorded colours are kept', () => {
    expect(tyreCasing('#dedede')).toBe('#dedede');
    expect(tyreCasing('#80736f')).toBe('#80736f');
  });
  test('the default casing is the rubber grey itself', () => {
    expect(tyreCasing(TYRE_LOOK.rubber)).toBe(TYRE_LOOK.rubber);
  });
  test('a colour that is not #rrggbb passes through', () => {
    expect(tyreCasing('red')).toBe('red');
  });
});

describe('tyre stack geometry', () => {
  for (const n of [1, 4, 6]) {
    test(`a stack of ${n}: grooves darker than every tread, tyres not all one shade, within budget`, () => {
      const g = tyreStackGeometry(n);
      const p = g.attributes.position, c = g.attributes.color;
      const tread: number[] = [], groove: number[] = [];
      for (let i = 0; i < p.count; i++) {
        const r = Math.hypot(p.getX(i), p.getZ(i));
        if (r > 0.28) tread.push(c.getX(i)); else if (r > 0.2) groove.push(c.getX(i));
      }
      expect(Math.max(...groove)).toBeLessThan(Math.min(...tread));
      expect(Math.max(...tread) - Math.min(...tread)).toBeGreaterThan(0.1);
      const tris = (g.index ? g.index.count : p.count) / 3;
      expect(tris).toBeLessThanOrEqual(16 * (3 * n + 4));
      // height: n tyres of 0.23 m
      g.computeBoundingBox();
      expect(g.boundingBox!.max.y).toBeCloseTo(n * 0.23, 5);
    });
  }
});
