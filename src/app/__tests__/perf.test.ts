import { afterEach, describe, expect, it } from 'vitest';
import { director } from '../../physics/__tests__/ai_fixture';
import { ADAPT_MISS_FRAC, ADAPT_OK_FRAC, ADAPT_SETTLE_MS, ADAPT_STEP_GAP_MS, ADAPT_UP_HOLD_MS, AdaptiveQuality, AdaptivePolicy, FrameWindow, adaptLadder, newDirectorTiming, parsePerfFlags, storeWorker, storedWorker, workerChoice, WORKER_KEY } from '../perf';

describe('perf flags', () => {
  it('defaults: overlay off, no autopilot, adaptive on, LOD and worker unset', () => {
    expect(parsePerfFlags('')).toEqual({ perf: false, playerAi: false, adapt: true, lod: null, worker: null });
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

describe('adaptive policy (missed frames, not the interval p95)', () => {
  it('steps down when more than 5 % of the last 2 s were missed, one step per 3 s, and stops at the bottom', () => {
    const p = new AdaptivePolicy(3);
    expect(p.update(0, ADAPT_MISS_FRAC, null)).toBeNull();            // exactly 5 %: not more
    expect(p.update(10, ADAPT_MISS_FRAC + 0.01, null)).toBe(1);
    expect(p.update(1000, 0.5, null)).toBeNull();
    expect(p.update(10 + ADAPT_STEP_GAP_MS - 1, 0.5, null)).toBeNull();
    expect(p.update(10 + ADAPT_STEP_GAP_MS, 0.5, null)).toBe(2);
    expect(p.update(10 + 2 * ADAPT_STEP_GAP_MS, 0.5, null)).toBe(3);
    expect(p.update(10 + 3 * ADAPT_STEP_GAP_MS, 0.5, null)).toBeNull();
  });
  it('steps up one level only with 10 s in and under 1 % of them slow', () => {
    const p = new AdaptivePolicy(3);
    p.update(0, 0.5, null); p.update(3000, 0.5, null);
    expect(p.level).toBe(2);
    expect(p.update(5000, 0, null)).toBeNull();                       // the 10 s are not in yet
    expect(p.update(8000, 0, ADAPT_OK_FRAC)).toBeNull();              // 1 % exactly: not fewer
    expect(p.update(8000, 0, 0.005)).toBeNull();                      // too soon after the last step
    expect(p.update(3000 + ADAPT_UP_HOLD_MS, 0, 0.005)).toBe(1);
    expect(p.update(3000 + 2 * ADAPT_UP_HOLD_MS, 0, 0)).toBe(0);
    expect(p.update(3000 + 3 * ADAPT_UP_HOLD_MS, 0, 0)).toBeNull();   // already at the top
  });
});

describe('adaptive quality over frame times', () => {
  const base = { shadowCasters: 12, maxDrawn: 45, ratioCap: 1.5 };
  const run = (aq: AdaptiveQuality, from: number, secs: number, interval: (i: number) => number) => {
    let t = from;
    for (let i = 0; t < from + secs * 1000; i++) { const ms = interval(i); t += ms; aq.frame(t, ms); }
    return t;
  };
  it('steady 60 Hz with vsync jitter (16.7-19 ms) never steps', () => {
    const aq = new AdaptiveQuality(base, () => { throw new Error('stepped'); });
    run(aq, 0, 60, (i) => 16.7 + (i % 7) * 0.35);
    expect(aq.level).toBe(0);
  });
  it('a missed vsync in more than 5 % of frames walks down the ladder; clean frames walk back up', () => {
    const seen: number[] = [];
    const aq = new AdaptiveQuality(base, (l) => seen.push(l.shadowCasters));
    let t = run(aq, 0, 15, (i) => (i % 5 === 0 ? 33.4 : 16.7));      // one frame in five missed
    expect(aq.level).toBe(5);
    expect(seen.slice(0, 2)).toEqual([6, 0]);
    t = run(aq, t, 80, () => 16.7);
    expect(aq.level).toBe(0);
    expect(aq.trace.length).toBe(10);
  });
  it('a miss rate under 5 % does not step', () => {
    const aq = new AdaptiveQuality(base, () => { throw new Error('stepped'); });
    run(aq, 0, 30, (i) => (i % 40 === 0 ? 33.4 : 16.7));             // 2.5 %
    expect(aq.level).toBe(0);
  });
  it('no step in the first 3 s after hold() (a race build, the tab becoming visible), then it reacts', () => {
    const aq = new AdaptiveQuality(base, () => {});
    aq.hold(0);
    let t = run(aq, 0, ADAPT_SETTLE_MS / 1000 - 0.1, () => 50);      // all missed, inside the hold: ignored
    expect(aq.level).toBe(0);
    t = run(aq, t, 4, () => 50);
    expect(aq.level).toBeGreaterThan(0);
  });
  it('FrameWindow keeps two seconds and counts the share above a threshold', () => {
    const w = new FrameWindow(2000);
    for (let t = 0; t < 5000; t += 100) w.push(t, t < 2500 ? 40 : 10);
    expect(w.quantile(0.95)).toBe(10);
    expect(w.count).toBeLessThanOrEqual(21);
    expect(w.fractionAbove(25)).toBe(0);
    w.push(5100, 40);
    expect(w.fractionAbove(25)).toBeGreaterThan(0);
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

describe('the worker toggle (Graphics menu)', () => {
  const g = globalThis as unknown as { localStorage?: unknown };
  const mem = (): Storage => { const m = new Map<string, string>(); return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) } as unknown as Storage; };
  afterEach(() => { delete g.localStorage; });
  it('is off unless stored; storing on and off round-trips; no storage reads as off', () => {
    expect(storedWorker()).toBe(false);                    // no localStorage at all
    g.localStorage = mem();
    expect(storedWorker()).toBe(false);
    storeWorker(true);
    expect(storedWorker()).toBe(true);
    expect((g.localStorage as Storage).getItem(WORKER_KEY)).toBe('1');
    storeWorker(false);
    expect(storedWorker()).toBe(false);
    expect((g.localStorage as Storage).getItem(WORKER_KEY)).toBeNull();
    expect(() => storeWorker(true)).not.toThrow();
  });
  it('?worker= overrides the stored choice for the page load, as ?phone= does for the tier', () => {
    expect(workerChoice(null, false)).toBe(false);
    expect(workerChoice(null, true)).toBe(true);
    expect(workerChoice(true, false)).toBe(true);
    expect(workerChoice(false, true)).toBe(false);
    expect(workerChoice(parsePerfFlags('?worker=1').worker, false)).toBe(true);
    expect(workerChoice(parsePerfFlags('?worker=0').worker, true)).toBe(false);
    expect(workerChoice(parsePerfFlags('').worker, true)).toBe(true);
  });
  it('a storage that throws reads as off and does not throw on write', () => {
    g.localStorage = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); }, removeItem() { throw new Error('blocked'); } };
    expect(storedWorker()).toBe(false);
    expect(() => storeWorker(true)).not.toThrow();
  });
});
