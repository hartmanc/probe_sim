// GET /api/scores?ghost=<board>: the board's #1 trace is kept when a new #1 passes verification and served read-only.
import { beforeAll, describe, expect, test } from 'vitest';
import { handleScores, sweepStaleBoards, topKey, type HandlerDeps } from '../handler';
import { MemoryStore } from '../store';
import { physicsVersion } from '../hash';
import { boardKey } from '../validate';
import { LIMITS } from '../config';
import type { Lap } from '../../app/timing';
import type { GhostReply, InputTrace } from '../types';
import { lagunaAssets, recordLap } from './fixtures';

let lap: Lap, trace: InputTrace, PV: string, BOARD: string;
beforeAll(() => {
  ({ lap, trace } = recordLap());
  PV = physicsVersion(lagunaAssets().carJson, lagunaAssets().track.length_m);
  BOARD = boardKey('hotlap', 'laguna_seca', 'probe_gt', PV);
});
const ORIGIN = 'https://probe.example';
const deps = (over: Partial<HandlerDeps> = {}): HandlerDeps => ({ store: new MemoryStore(), assets: async () => lagunaAssets(), physics: async () => PV, ...over });
const fakeVerify = (replayed?: number): HandlerDeps['verify'] => (_a, _t, _n, claimed) => ({ ok: true, reasons: [], replayed: replayed ?? claimed, cpuMs: 0 });
const post = (body: unknown, ip = '9.9.9.9') => new Request(`${ORIGIN}/api/scores`, {
  method: 'POST', headers: { 'content-type': 'application/json', host: 'probe.example', origin: ORIGIN, 'x-forwarded-for': ip }, body: JSON.stringify(body),
});
const get = (q: string, ip = '8.8.8.8') => new Request(`${ORIGIN}/api/scores${q}`, { headers: { host: 'probe.example', 'x-forwarded-for': ip } });
const secretOf = (n: string) => n.padEnd(32, '0').replace(/[^0-9a-f]/g, 'a').slice(0, 32);
const hot = (name: string, time: number, over: Record<string, unknown> = {}) => ({
  mode: 'hotlap', track: 'laguna_seca', car: 'probe_gt', physics: PV, name, input: 'pad', secret: secretOf(name.toLowerCase().replace(/[^0-9a-f]/g, 'b')),
  time, lap: lap.n, valid: true, trace, ...over,
});
const ghost = async (d: HandlerDeps, board = BOARD, ip?: string) => {
  const r = await handleScores(get(`?ghost=${encodeURIComponent(board)}`, ip), d);
  return { r, j: (await r.json()) as GhostReply & { error?: string; reasons?: string[] } };
};

describe('GET ?ghost=', () => {
  test('an empty board has no ghost: 404 with a reason, board cache headers', async () => {
    const { r, j } = await ghost(deps());
    expect(r.status).toBe(404);
    expect(j).toMatchObject({ ok: false, error: 'no ghost' });
    expect(r.headers.get('cache-control')).toBe('no-store');
  });

  test('the first verified lap becomes #1 and its trace is served: name, replayed time, lap, the whole trace, no secret', async () => {
    const d = deps({ verify: fakeVerify() });
    expect((await handleScores(post(hot('Alba', 120.5)), d)).status).toBe(200);
    const { r, j } = await ghost(d);
    expect(r.status).toBe(200);
    expect(j).toMatchObject({ ok: true, board: BOARD, name: 'Alba', score: 120.5, lap: lap.n, input: 'pad' });
    expect(j.trace).toEqual(trace);
    expect(JSON.stringify(j)).not.toMatch(/secret|device/);
    expect(r.headers.get('cache-control')).toBe('no-store');
  });

  test('a slower lap by someone else does not replace #1; a faster one does; the same name improving does too', async () => {
    const d = deps({ verify: fakeVerify() });
    await handleScores(post(hot('Alba', 120.5)), d);
    await handleScores(post(hot('Bruno', 121.0, { trace: { ...trace, steps: trace.steps } })), d);
    expect((await ghost(d)).j.name).toBe('Alba');
    await handleScores(post(hot('Bruno', 119.0)), d);
    expect(await ghost(d)).toMatchObject({ j: { name: 'Bruno', score: 119 } });
    await handleScores(post(hot('Bruno', 118.25)), d);
    expect((await ghost(d)).j.score).toBe(118.25);
    expect((await handleScores(get(`?board=${encodeURIComponent(BOARD)}`), d).then((x) => x.json()) as { entries: { name: string; score: number }[] }).entries[0]).toMatchObject({ name: 'Bruno', score: 118.25 });
  });

  test('the stored score is the replayed time, not the claimed one', async () => {
    const d = deps({ verify: fakeVerify(120.4) });
    await handleScores(post(hot('Alba', 120.43)), d);
    expect((await ghost(d)).j.score).toBe(120.4);
  });

  test('a stored #1 that is no longer the board\'s #1 (trimmed / raced) is not served', async () => {
    const d = deps({ verify: fakeVerify() });
    await handleScores(post(hot('Alba', 120.5)), d);
    await d.store.submit(BOARD, 'zed', 110, true, JSON.stringify({ name: 'Zed', input: 'keys', at: 'x' }), LIMITS.keep);   // a #1 posted without a trace (an older entry)
    const { r, j } = await ghost(d);
    expect(r.status).toBe(404);
    expect(j.reasons?.join(' ')).toMatch(/not the board/);
  });

  test('garbage in the store, a trace for another board, or a bad key are refused', async () => {
    const d = deps({ verify: fakeVerify() });
    await handleScores(post(hot('Alba', 120.5)), d);
    const rec = JSON.parse((await d.store.kvGet(topKey(BOARD)))!);
    await d.store.kvSet(topKey(BOARD), '{not json');
    expect((await ghost(d)).r.status).toBe(404);
    await d.store.kvSet(topKey(BOARD), JSON.stringify({ ...rec, trace: { ...rec.trace, physics: 'other' } }));
    expect((await ghost(d)).j.reasons?.join(' ')).toMatch(/does not match/);
    await d.store.kvSet(topKey(BOARD), JSON.stringify({ ...rec, trace: { ...rec.trace, rows: [[5, 0, 0, 0, 0]] } }));
    expect((await ghost(d)).r.status).toBe(404);   // structurally invalid trace: validated on the way out
    expect((await ghost(d, 'nonsense')).r.status).toBe(400);
    expect((await ghost(d, `race:laguna_seca:probe_gt:${PV}:x`)).r.status).toBe(400);
  });

  test('rate limited per IP, separately from the posts', async () => {
    const d = deps();
    for (let i = 0; i < LIMITS.rateGhosts; i++) expect((await ghost(d, BOARD, '7.7.7.7')).r.status).toBe(404);
    const over = await ghost(d, BOARD, '7.7.7.7');
    expect(over.r.status).toBe(429);
    expect(over.r.headers.get('retry-after')).toMatch(/^\d+$/);
    expect((await ghost(d, BOARD, '7.7.7.8')).r.status).toBe(404);
  });

  test('the trace goes with a stale board: a physics-version change expires it with the board', async () => {
    let t = 1_000_000;
    const store = new MemoryStore(() => t);
    const d = deps({ store, verify: fakeVerify(), physics: async () => PV });
    await handleScores(post(hot('Alba', 120.5)), d);
    expect(await store.kvGet(topKey(BOARD))).not.toBeNull();
    const newer = deps({ store, physics: async () => 'newphysics1' });
    expect(await sweepStaleBoards(newer)).toEqual([BOARD]);
    expect(await store.kvGet(topKey(BOARD))).not.toBeNull();   // expires after the stale TTL, not at once
    t += (LIMITS.staleBoardTtlS + 5) * 1000;
    expect(await store.kvGet(topKey(BOARD))).toBeNull();
    expect((await ghost(d)).r.status).toBe(404);
  });

  test('one bounded key per board: the next #1 overwrites it', async () => {
    const d = deps({ verify: fakeVerify() });
    await handleScores(post(hot('Alba', 120.5)), d);
    const a = (await d.store.kvGet(topKey(BOARD)))!.length;
    await handleScores(post(hot('Bruno', 119)), d);
    const b = (await d.store.kvGet(topKey(BOARD)))!.length;
    expect(Math.abs(b - a)).toBeLessThan(100);   // same trace, a different name: replaced, not appended
    expect(a).toBeLessThan(LIMITS.maxBodyBytes);
  });
});
