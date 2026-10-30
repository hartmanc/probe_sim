// Race recording format helpers (src/scoreboard/racerec.ts): the snapshot codec, the structural check, the size cap and truncation.
import { describe, expect, it } from 'vitest';
import { REC_MAX_BYTES, checkRecording, cutRecording, decodeSnapshot, encodeSnapshot, gunzipCapped, gzipText, packRecording, type RaceRecording } from '../racerec';

function rec(rows = 3000, over: Partial<RaceRecording> = {}): RaceRecording {
  const r: RaceRecording['inputs']['rows'] = [];
  let seed = 7;
  const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
  for (let i = 0; i < rows; i++) r.push([i * 10, Math.round((rnd() * 2 - 1) * 1000), Math.round(rnd() * 1000), Math.round(rnd() * 300), 24]);
  return {
    v: 1, trackId: 'laguna_seca', fieldId: 'cars/field/pace.json', seed: 1, laps: 5, aiVersion: '9', buildSha: 'abc1234', physics: 'p',
    build: { seed: 1, laps: 5, realGrid: false, playerAi: false, lod: false, strengthPct: 100, closeRacing: null, planner: null, fieldCap: null, ref: null, autoShift: true, abs: true },
    config: { playerNumber: '619' },
    inputs: { v: 1, physics: 'p', track: 'laguna_seca', car: 'probe_gt', hz: 100, dt: 0.001, reset: { pos: [0, 0, 0], heading: 0, speed: 0 }, ref: [[0, null]], rows: r, steps: rows * 10 },
    events: [], live: { lapTimes: [100, 101], crossings: [{ car: '619', lapNr: 0, t: 5 }, { car: '619', lapNr: 1, t: 105 }, { car: '619', lapNr: 2, t: 206 }, { car: '12', lapNr: 1, t: 99 }], results: null },
    snapshot: null, owner: false, started: '2026-10-30T00:00:00.000Z', durationS: rows * 0.01, ...over,
  };
}

describe('snapshot codec', () => {
  it('round-trips positions across the start line (wrap) and backwards motion, and lane offsets', () => {
    const L = 3588.048, L10 = Math.round(L * 10), cars = ['a', 'b', 'c'];
    const S = [Int32Array.from([L10 - 150, 100, 20000]), Int32Array.from([60, 98, 20000 + 700]), Int32Array.from([210, 95, 20000 + 1400])];
    const E = [Int8Array.from([5, -127, 0]), Int8Array.from([-3, 10, 127]), Int8Array.from([0, 0, -1])];
    const sn = encodeSnapshot(cars, L, S, E);
    expect(sn.n).toBe(3); expect(sn.L10).toBe(L10);
    const back = decodeSnapshot(JSON.parse(JSON.stringify(sn)));
    expect(back.S.map((a) => [...a])).toEqual(S.map((a) => [...a]));
    expect(back.E.map((a) => [...a])).toEqual(E.map((a) => [...a]));
  });
});

describe('checkRecording', () => {
  it('accepts a well-formed recording and says what is wrong with a malformed one', () => {
    expect(checkRecording(rec())).toEqual([]);
    expect(checkRecording(null)).toEqual(['recording missing']);
    expect(checkRecording({ ...rec(), aiVersion: 9 })).toContain('aiVersion must be a short string');
    expect(checkRecording({ ...rec(), buildSha: 5 })).toContain('buildSha must be a short string');
    const r = rec(); r.inputs.rows[5] = [3, 0, 0, 0, 0];
    expect(checkRecording(r).join()).toMatch(/inputs.rows\[5\]/);
    const big = rec(); big.inputs.steps = 2_000_000;
    expect(checkRecording(big).join()).toMatch(/inputs.steps/);
    const sn = encodeSnapshot(['a'], 3000, [Int32Array.from([1])], [Int8Array.from([1])]);
    expect(checkRecording({ ...rec(), snapshot: sn })).toEqual([]);
    expect(checkRecording({ ...rec(), snapshot: { ...sn, n: 5000 } }).join()).toMatch(/snapshot/);
  });
});

describe('packRecording', () => {
  it('gzips under the cap; a recording over it loses its snapshot, then its tail (marked truncated)', async () => {
    const small = rec(500);
    const p = (await packRecording(small))!;
    expect(p.gzip).toBe(true); expect(p.truncated).toBe(false);
    expect(await gunzipCapped(p.body as Uint8Array, 1e8)).toBe(JSON.stringify(small));
    expect(await gunzipCapped(p.body as Uint8Array, 100)).toBeNull();                       // past the output cap
    // 60 000 random rows (a 600 s race with busy hands) do not fit 20 KB: cut at a step, live data cut with it
    const big = rec(20000);
    const cut = (await packRecording(big, 20_000))!;
    expect(cut.bytes).toBeLessThanOrEqual(20_000); expect(cut.truncated).toBe(true);
    const back = JSON.parse((await gunzipCapped(cut.body as Uint8Array, 1e8))!) as RaceRecording;
    expect(back.truncated!.atStep).toBeLessThan(200_000); expect(back.inputs.steps).toBe(back.truncated!.atStep);
    expect(Math.max(...back.inputs.rows.map((r) => r[0]))).toBeLessThan(back.inputs.steps);
    expect(checkRecording(back)).toEqual([]);
    expect(await packRecording(big, 50)).toBeNull();                                        // nothing fits
    expect(REC_MAX_BYTES).toBe(512 * 1024);
  });
  it('cutRecording keeps the crossings up to the director time of the cut and the player\'s laps they carry', () => {
    const c = cutRecording(rec(), 150_000);                                  // 150 s
    expect(c.live.crossings.map((x) => x.t)).toEqual([5, 105, 99]);
    expect(c.live.lapTimes).toEqual([100]);                                   // two player crossings -> one timed lap
    expect(c.live.results).toBeNull(); expect(c.truncated).toEqual({ atStep: 150_000 });
  });
  it('gzipText exists in this runtime', async () => { expect((await gzipText('x'))!.byteLength).toBeGreaterThan(0); });
});
