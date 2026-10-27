import { beforeAll, describe, expect, test } from 'vitest';
import { buildGhostLap, ghostFromTrace, type LapSample } from '../ghostlap';
import { replayTrace } from '../replay';
import { GhostTrace } from '../../app/ghosts';
import type { Lap } from '../../app/timing';
import type { InputTrace } from '../types';
import { lagunaAssets, recordLap } from './fixtures';

describe('buildGhostLap (pure)', () => {
  test('a constant-speed lap resamples to t = s / v on the grid, pinned at the start', () => {
    const L = 3588, v = 40, samples: LapSample[] = [];
    for (let s = 0.2; s < L - 1; s += 0.2 * v * 0.25) samples.push({ t: s / v, s, v });
    const g = buildGhostLap(samples, L / v, L, 2, { id: 'x', driver: 'You', label: 'You 1:29' })!;
    expect(g.t).toHaveLength(Math.floor(L / 2));
    expect(g.t[0]).toBe(0);
    for (const i of [1, 100, 900, 1793]) expect(g.t[i]).toBeCloseTo((i * 2) / v, 3);
    expect(g.v_mps[500]).toBeCloseTo(v, 6);
    expect(new GhostTrace(g, 2, L).tAt(L)).toBeCloseTo(L / v, 1);
  });
  test('samples that do not advance are dropped; too few samples is no lap', () => {
    const s: LapSample[] = [{ t: 1, s: 10, v: 10 }, { t: 1.1, s: 10, v: 10 }, { t: 1.2, s: 9, v: 10 }, { t: 2, s: 20, v: 10 }, { t: 3, s: 30, v: 10 }];
    const g = buildGhostLap(s, 100, 100, 2, { id: 'x', driver: 'd', label: 'l' })!;
    expect(g.t.every((x, i) => i === 0 || x > g.t[i - 1])).toBe(true);
    expect(buildGhostLap([{ t: 1, s: 5, v: 5 }], 100, 100, 2, { id: 'x', driver: 'd', label: 'l' })).toBeNull();
  });
});

describe('ghostFromTrace: a posted trace rebuilds to the posted lap', () => {
  let lap: Lap, trace: InputTrace;
  beforeAll(() => { ({ lap, trace } = recordLap()); }, 120_000);

  test('the rebuilt lap time is the replayed lap time to the millisecond, and the replay is unchanged by the hook', () => {
    const a = lagunaAssets();
    const plain = replayTrace(a, trace, lap.n);
    const g = ghostFromTrace(a, trace, lap.n, { id: 'board_best', driver: 'Top', label: (t) => `Top ${t.toFixed(3)}` })!;
    expect(g).not.toBeNull();
    expect(g.time).toBe(plain.lap!.time);
    expect(g.time).toBeCloseTo(lap.time, 3);
    expect(g.lap.lap_time_s).toBe(g.time);
    expect(g.lap.label).toBe(`Top ${g.time.toFixed(3)}`);
  }, 120_000);

  test('t(s) is increasing, starts at 0, ends at the lap time, and its speed is the car\'s', () => {
    const a = lagunaAssets();
    const { lap: g } = ghostFromTrace(a, trace, lap.n, { id: 'b', driver: 'T', label: () => 'T' })!;
    const L = a.track.length_m, grid = a.ghosts.s_grid_m;
    expect(g.t).toHaveLength(Math.floor(L / grid));
    expect(g.t[0]).toBe(0);
    for (let i = 1; i < g.t.length; i++) expect(g.t[i]).toBeGreaterThan(g.t[i - 1]);
    const tr = new GhostTrace(g, grid, L);
    expect(Math.abs(tr.tAt(L) - g.lap_time_s)).toBeLessThan(0.1);   // the last metres to the line
    // the lap's own minimum speed per corner (the timer's trace) is what the ghost's speed channel reproduces
    const i = Math.floor(L / 3 / grid);
    const near = Math.min(...g.v_mps.slice(i - 20, i + 20));
    const timerNear = Math.min(...Array.from(lap.speedTrace.slice(i - 20, i + 20)));
    expect(Math.abs(near - timerNear)).toBeLessThan(1.5);
    // sAt inverts tAt
    expect(tr.sAt(tr.tAt(1500))).toBeCloseTo(1500, 0);
  }, 120_000);

  test('a trace whose lap never completes gives null', () => {
    const a = lagunaAssets();
    expect(ghostFromTrace(a, trace, lap.n + 3, { id: 'b', driver: 'T', label: () => 'T' })).toBeNull();
  }, 120_000);
});
