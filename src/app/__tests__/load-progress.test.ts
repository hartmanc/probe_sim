import { describe, expect, it } from 'vitest';
import { LoadProgress, throttled } from '../load-progress';

const stages = [{ id: 'a', weight: 0.25 }, { id: 'b', weight: 0.75 }];

describe('LoadProgress', () => {
  it('starts at 0 and ends at 1 only when every stage has ended', () => {
    const p = new LoadProgress(stages);
    expect(p.fraction()).toBe(0);
    p.end('a'); expect(p.fraction()).toBeCloseTo(0.25, 9);
    p.end('b'); expect(p.fraction()).toBe(1);
  });
  it('bytes move the bar inside the stage weight, byte-weighted across the stage\'s files', () => {
    const p = new LoadProgress(stages);
    p.bytes('b', 'big', 400, 800); p.bytes('b', 'small', 0, 200);
    expect(p.fraction()).toBeCloseTo(0.75 * (400 / 1000), 9);
    p.bytes('b', 'small', 200, 200);
    expect(p.fraction()).toBeCloseTo(0.75 * (600 / 1000), 9);
  });
  it('never reaches the stage weight on bytes alone (decode and parse still follow)', () => {
    const p = new LoadProgress(stages);
    p.bytes('b', 'f', 1000, 1000);
    expect(p.fraction()).toBeLessThan(0.75);
    p.end('b'); expect(p.fraction()).toBeCloseTo(0.75, 9);
  });
  it('is monotone non-decreasing even when reports arrive out of order or overshoot', () => {
    const p = new LoadProgress(stages);
    let last = 0;
    for (const [g, t] of [[100, 1000], [50, 1000], [900, 1000], [2000, 1000], [10, 1000]] as const) {
      p.bytes('b', 'f', g, t);
      const f = p.fraction();
      expect(f).toBeGreaterThanOrEqual(last); last = f;
    }
  });
  it('a missing Content-Length degrades to the stage tick', () => {
    const p = new LoadProgress(stages);
    p.bytes('b', 'f', 123456, undefined); p.bytes('b', 'g', 99, 0);
    expect(p.fraction()).toBe(0);
    p.end('b'); expect(p.fraction()).toBeCloseTo(0.75, 9);
  });
});

describe('throttled', () => {
  it('delivers at most every ms, and always the last value', () => {
    let t = 0; const seen: number[] = []; const timers: (() => void)[] = [];
    const th = throttled<number>((v) => seen.push(v), 100, () => t, (f) => { timers.push(f); });
    th.push(1); t = 30; th.push(2); t = 60; th.push(3);
    expect(seen).toEqual([1]);
    t = 100; timers.shift()!();
    expect(seen).toEqual([1, 3]);
    t = 250; th.push(4); expect(seen).toEqual([1, 3, 4]);
  });
});
