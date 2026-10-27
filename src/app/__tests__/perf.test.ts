import { describe, expect, it } from 'vitest';
import { director } from '../../physics/__tests__/ai_fixture';
import { ADAPT_DOWN_MS, ADAPT_STEP_GAP_MS, ADAPT_UP_HOLD_MS, ADAPT_UP_MS, AdaptiveQuality, AdaptivePolicy, FrameWindow, adaptLadder, newDirectorTiming, parsePerfFlags } from '../perf';

describe('perf flags', () => {
  it('defaults: overlay off, no autopilot, adaptive on, LOD and worker unset', () => {
    expect(parsePerfFlags('')).toEqual({ perf: false, playerAi: false, adapt: true, lod: null, worker: false });
  });
  it('reads the switches', () => {
    expect(parsePerfFlags('?perf=1&playerai=1&adapt=0&lod=1&worker=1')).toEqual({ perf: true, playerAi: true, adapt: false, lod: true, worker: true });
    expect(parsePerfFlags('?lod=0').lod).toBe(false);
  });
});

describe('adaptive ladder', () => {
  it('desktop: casters 12 -> 6 -> 0, drawn 45 -> 30, ratio cap -0.25 down to 1.0', () => {
    const l = adaptLadder({ shadowCasters: 12, maxDrawn: 45, ratioCap: 1.5 });
    expect(l.map((x) => [x.shadowCasters, x.maxDrawn, x.ratioCap])).toEqual([
      [12, 45, 1.5], [6, 45, 1.5], [0, 45, 1.5], [0, 30, 1.5], [0, 30, 1.25], [0, 30, 1],
    ]);
  });
  it('skips steps the tier already sits under, and never goes below the phone numbers', () => {
    const b = adaptLadder({ shadowCasters: 4, maxDrawn: 30, ratioCap: 1.3 });
    expect(b.map((x) => [x.shadowCasters, x.maxDrawn, x.ratioCap])).toEqual([[4, 30, 1.3], [2, 30, 1.3], [0, 30, 1.3], [0, 30, 1.05], [0, 30, 1]]);
    for (const x of adaptLadder({ shadowCasters: 12, maxDrawn: 45, ratioCap: 2 })) {
      expect(x.shadowCasters).toBeGreaterThanOrEqual(0); expect(x.maxDrawn).toBeGreaterThanOrEqual(20); expect(x.ratioCap).toBeGreaterThanOrEqual(1);
    }
    expect(adaptLadder({ shadowCasters: 0, maxDrawn: 20, ratioCap: 1 })).toHaveLength(1);
  });
});

describe('adaptive policy', () => {
  it('steps down when p95 stays over 18 ms, one step per 3 s, and stops at the bottom', () => {
    const p = new AdaptivePolicy(3);
    expect(p.update(0, ADAPT_DOWN_MS + 1)).toBe(1);
    expect(p.update(1000, 30)).toBeNull();
    expect(p.update(ADAPT_STEP_GAP_MS - 1, 30)).toBeNull();
    expect(p.update(ADAPT_STEP_GAP_MS, 30)).toBe(2);
    expect(p.update(2 * ADAPT_STEP_GAP_MS, 30)).toBe(3);
    expect(p.update(3 * ADAPT_STEP_GAP_MS, 30)).toBeNull();
    expect(p.level).toBe(3);
  });
  it('steps back up one level after 10 s under 14 ms, and an in-between frame time resets the wait', () => {
    const p = new AdaptivePolicy(3);
    p.update(0, 20); p.update(3000, 20);
    expect(p.level).toBe(2);
    let t = 10_000;
    expect(p.update(t, ADAPT_UP_MS - 1)).toBeNull();
    expect(p.update(t + ADAPT_UP_HOLD_MS - 1, ADAPT_UP_MS - 1)).toBeNull();
    expect(p.update(t + ADAPT_UP_HOLD_MS, ADAPT_UP_MS - 1)).toBe(1);
    t += ADAPT_UP_HOLD_MS;
    expect(p.update(t + 5000, 16)).toBeNull();                // between 14 and 18: hold, and restart the wait
    expect(p.update(t + 5001, 10)).toBeNull();
    expect(p.update(t + 5001 + ADAPT_UP_HOLD_MS, 10)).toBe(0);
    expect(p.update(t + 99_999, 10)).toBeNull();               // already at the top
  });
  it('NaN (no data) changes nothing', () => {
    expect(new AdaptivePolicy(2).update(0, NaN)).toBeNull();
  });
});

describe('adaptive quality over frame times', () => {
  it('slow frames walk down the ladder, quick ones walk back up', () => {
    const seen: number[] = [];
    const aq = new AdaptiveQuality({ shadowCasters: 12, maxDrawn: 45, ratioCap: 1.5 }, (l) => seen.push(l.shadowCasters));
    let t = 0;
    for (let i = 0; i < 600; i++) { t += 25; aq.frame(t, 25); }     // 15 s at 40 fps
    expect(aq.level).toBe(5);
    expect(seen.slice(0, 2)).toEqual([6, 0]);
    for (let i = 0; i < 6000; i++) { t += 10; aq.frame(t, 10); }    // 60 s at 100 fps
    expect(aq.level).toBe(0);
  });
  it('FrameWindow keeps two seconds', () => {
    const w = new FrameWindow(2000);
    for (let t = 0; t < 5000; t += 100) w.push(t, t < 3000 ? 40 : 10);
    expect(w.quantile(0.95)).toBe(10);
    expect(w.count).toBeLessThanOrEqual(21);
  });
});

describe('director timing counters', () => {
  it('collect only when set, and never change the race', () => {
    const run = (timing: boolean) => {
      const d = director({ seed: 3, maxAi: 5, playerAi: true }, { walls: false });
      if (timing) d.timing = newDirectorTiming();
      for (let i = 0; i < 3000; i++) d.step(0.001);
      return d;
    };
    const a = run(false), b = run(true);
    expect(a.timing).toBeNull();
    expect(b.timing!.steps).toBe(3000);
    expect(b.timing!.aiPhysics).toBeGreaterThan(0);
    expect(b.timing!.player).toBeGreaterThan(0);
    expect(b.timing!.control).toBeGreaterThan(0);
    for (let i = 0; i < a.cars.length; i++) {
      expect(Array.from(b.cars[i].vehicle.state.pos)).toEqual(Array.from(a.cars[i].vehicle.state.pos));
      expect(b.cars[i].U).toBe(a.cars[i].U);
    }
  }, 60000);
});
