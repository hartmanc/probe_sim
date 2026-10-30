import { afterEach, describe, expect, it } from 'vitest';
import { GRIP_MAX, GRIP_MIN, getPowerShare, paceSplit, setPowerShare } from '../ai/field';

// The power share p (30 Oct 2026): the share of the pace scalar that comes from power instead of grip.
describe('power share', () => {
  afterEach(() => setPowerShare(0));
  const old = (scale: number) => {   // the grip-only split inside the grip range, power only beyond it
    const grip = Math.min(GRIP_MAX, Math.max(GRIP_MIN, scale));
    return { grip, power: scale < GRIP_MIN ? Math.pow(scale / GRIP_MIN, 3) : scale > GRIP_MAX ? Math.pow(scale / GRIP_MAX, 3) : 1 };
  };
  it('p = 0 is the grip-only split', () => {
    setPowerShare(0);
    for (const s of [0.4, 0.55, 0.8, 1, 1.1, 1.3, 1.5]) {
      const a = paceSplit(s), b = old(s);
      expect(a.grip).toBeCloseTo(b.grip, 12);
      expect(a.power).toBeCloseTo(b.power, 9);
    }
  });
  it('p moves part of the scalar to power, both ways from 1', () => {
    setPowerShare(0.5);
    expect(getPowerShare()).toBe(0.5);
    const up = paceSplit(1.06), down = paceSplit(0.9);
    expect(up.grip).toBeCloseTo(1.03, 9); expect(up.power).toBeCloseTo(Math.pow(1.03, 3), 9);
    expect(down.grip).toBeCloseTo(0.95, 9); expect(down.power).toBeCloseTo(Math.pow(0.95, 3), 9);
    expect(paceSplit(1).power).toBeCloseTo(1, 12);
  });
  it('what the grip clamp cuts off goes to power (monotone in the scalar)', () => {
    setPowerShare(0.5);
    let last = 0;
    for (let s = 0.4; s <= 1.8; s += 0.05) { const { grip, power } = paceSplit(s); const m = grip * power; expect(m).toBeGreaterThan(last); last = m; }
  });
  it('is clamped to 0..1', () => { setPowerShare(3); expect(getPowerShare()).toBe(1); setPowerShare(-1); expect(getPowerShare()).toBe(0); setPowerShare(NaN); expect(getPowerShare()).toBe(0); });
});
