import { beforeAll, describe, expect, test } from 'vitest';
import { currentRaceAiVersion, handleScores, sweepStaleBoards, type HandlerDeps } from '../handler';
import { MemoryStore } from '../store';
import { physicsVersion } from '../hash';
import { boardKey } from '../validate';
import { LIMITS, TRACKS } from '../config';
import type { Lap } from '../../app/timing';
import type { InputTrace } from '../types';
import { lagunaAssets, recordLap } from './fixtures';

let lap: Lap;
let trace: InputTrace;
let PV: string;
beforeAll(() => {
  ({ lap, trace } = recordLap());
  PV = physicsVersion(lagunaAssets().carJson, lagunaAssets().track.length_m);
});

const deps = (over: Partial<HandlerDeps> = {}): HandlerDeps => ({
  store: new MemoryStore(),
  assets: async () => lagunaAssets(),
  physics: async () => PV,
  ...over,
});
const ORIGIN = 'https://probe.example';
const post = (body: unknown, headers: Record<string, string> = {}) => new Request(`${ORIGIN}/api/scores`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', host: 'probe.example', origin: ORIGIN, 'x-forwarded-for': '9.9.9.9', ...headers },
  body: typeof body === 'string' ? body : JSON.stringify(body),
});
const get = (q: string, headers: Record<string, string> = {}) => new Request(`${ORIGIN}/api/scores${q}`, { headers: { host: 'probe.example', ...headers } });
const SECRET = '0123456789abcdef0123456789abcdef';
const OTHER = 'fedcba9876543210fedcba9876543210';
const hot = (over: Record<string, unknown> = {}) => ({
  mode: 'hotlap', track: 'laguna_seca', car: 'probe_gt', physics: PV, name: 'Coby', input: 'pad', secret: SECRET,
  time: lap.time, lap: lap.n, valid: true, trace, ...over,
});
// a fake replay so ranking tests do not re-run the physics for every entry
const fakeVerify: HandlerDeps['verify'] = (_a, _t, _n, claimed) => ({ ok: true, reasons: [], replayed: claimed, cpuMs: 0 });

describe('api handler', () => {
  test('GET without a board lists the current hot-lap board of every registered track', async () => {
    const r = await handleScores(get(''), deps());
    expect(r.status).toBe(200);
    expect(r.headers.get('cache-control')).toBe('no-store');
    // the fixture's physics() answers PV for every track; one board per registered track
    const boards = Object.fromEntries(Object.keys(TRACKS).map((t) => [`${t}/probe_gt`, `hotlap:${t}:probe_gt:${PV}`]));
    expect(boards['laguna_seca/probe_gt']).toBe(`hotlap:laguna_seca:probe_gt:${PV}`);
    expect(await r.json()).toEqual({ ok: true, store: 'memory', boards });
  });

  test('POST a real hot lap: replayed on the server, stored, ranked; GET shows it', async () => {
    const d = deps();
    const r = await handleScores(post(hot()), d);
    const j = await r.json() as Record<string, unknown>;
    expect(r.status).toBe(200);
    expect(j).toMatchObject({ ok: true, board: boardKey('hotlap', 'laguna_seca', 'probe_gt', PV), rank: 1, improved: true });
    expect(j.replayed).toBeCloseTo(lap.time, 3);
    const g = await handleScores(get(`?board=${encodeURIComponent(j.board as string)}&name=COBY`), d);
    const b = await g.json() as { entries: { name: string; score: number; input: string; rank: number }[]; you: { rank: number } };
    expect(b.entries).toHaveLength(1);
    expect(b.entries[0]).toMatchObject({ rank: 1, name: 'Coby', input: 'pad' });
    expect(b.entries[0].score).toBeCloseTo(lap.time, 3);
    expect(b.you.rank).toBe(1);
  });

  test('a fake submission claiming a better time than the replay is rejected with reasons', async () => {
    const d = deps();
    const r = await handleScores(post(hot({ time: lap.time - 2 })), d);
    expect(r.status).toBe(422);
    const j = await r.json() as { ok: boolean; reasons: string[] };
    expect(j.ok).toBe(false);
    expect(j.reasons.join(' ')).toMatch(/differs from the claimed/);
    expect(await d.store.top(boardKey('hotlap', 'laguna_seca', 'probe_gt', PV), 10, true)).toEqual([]);
  });

  test('stale client (physics version mismatch) is rejected before any replay', async () => {
    let replays = 0;
    const r = await handleScores(post(hot({ physics: 'old', trace: { ...trace, physics: 'old' } })), deps({ verify: (...a) => { replays++; return fakeVerify!(...a); } }));
    expect(r.status).toBe(422);
    expect(((await r.json()) as { reasons: string[] }).reasons).toContain('physics version mismatch: reload the game');
    expect(replays).toBe(0);
  });

  test('ranking: hot lap ascending, best per name kept, top 10 returned', async () => {
    const d = deps({ verify: fakeVerify });
    for (let i = 0; i < 12; i++) await handleScores(post(hot({ name: `P${i}`, time: 100 + i }), { 'x-forwarded-for': `10.0.0.${i}` }), d);
    let r = await handleScores(post(hot({ name: 'p3', time: 99 }), { 'x-forwarded-for': '10.0.1.1' }), d);
    expect(await r.json()).toMatchObject({ rank: 1, improved: true, best: 99 });
    r = await handleScores(post(hot({ name: 'P3', time: 105 }), { 'x-forwarded-for': '10.0.1.2' }), d);
    expect(await r.json()).toMatchObject({ rank: 1, improved: false, best: 99 });
    const g = await (await handleScores(get(`?board=hotlap:laguna_seca:probe_gt:${PV}&name=P11`), d)).json() as { entries: { name: string; score: number }[]; you: { rank: number } };
    expect(g.entries).toHaveLength(LIMITS.top);
    expect(g.entries[0]).toMatchObject({ name: 'p3', score: 99 });
    expect(g.entries[1]).toMatchObject({ name: 'P0', score: 100 });
    expect(g.you.rank).toBe(12);
  });

  test('race: plausibility only, finishers by time then distance, current AI version only (with race boards open)', async () => {
    const d = deps({ raceBoards: true });
    const AI = currentRaceAiVersion();
    const race = (name: string, metres: number, laps: number, ai = AI, time?: number) => post({ mode: 'race', track: 'laguna_seca', car: 'probe_gt', physics: PV, name, input: 'keys', secret: SECRET, ai_version: ai, metres, laps, replay: null, ...(time ? { finished: true, time } : {}) }, { 'x-forwarded-for': name });
    expect((await handleScores(race('a', 14_000, 3), d)).status).toBe(200);
    expect(await (await handleScores(race('b', 16_000, 4), d)).json()).toMatchObject({ rank: 1, board: `race:laguna_seca:probe_gt:${PV}:${AI}` });
    // a finisher ranks by race time, ahead of every car classified short
    expect(await (await handleScores(race('f', 17_800, 5, AI, 700), d)).json()).toMatchObject({ rank: 1 });
    expect(await (await handleScores(race('g', 17_800, 5, AI, 650), d)).json()).toMatchObject({ rank: 1 });
    expect(await (await handleScores(race('b2', 16_500, 4), d)).json()).toMatchObject({ rank: 3 });
    const old = await handleScores(race('c', 1_000, 0, 'ai-2'), d);
    expect(old.status).toBe(422);
    expect(((await old.json()) as { reasons: string[] }).reasons).toContain('race AI version is not current: reload the game');
    expect((await handleScores(race('d', 99_000, 5), d)).status).toBe(422);
    const g = await (await handleScores(get(`?board=race:laguna_seca:probe_gt:${PV}:${AI}`), d)).json() as { entries: { name: string; laps: number; ai_version: string }[] };
    expect(g.entries.map((e) => e.name)).toEqual(['g', 'f', 'b2', 'b', 'a']);
    expect(g.entries[0]).toMatchObject({ laps: 5, ai_version: AI });
  });

  test('race boards are closed for the public: race posts and race board reads answer 410, nothing is stored', async () => {
    const d = deps();
    const r = await handleScores(post({ mode: 'race', track: 'laguna_seca', car: 'probe_gt', physics: PV, name: 'r', input: 'keys', secret: SECRET, ai_version: currentRaceAiVersion(), metres: 1000, laps: 0 }), d);
    expect(r.status).toBe(410);
    expect(((await r.json()) as { reasons: string[] }).reasons[0]).toMatch(/race boards are closed/);
    expect(await d.store.boards()).toEqual([]);
    expect((await handleScores(get(`?board=race:laguna_seca:probe_gt:${PV}:${currentRaceAiVersion()}`), d)).status).toBe(410);
  });

  test('name ownership: secret required, first device claims, another device is refused, transfer code adopts', async () => {
    const d = deps({ verify: fakeVerify });
    const noSecret = await handleScores(post(hot({ secret: undefined })), d);
    expect(noSecret.status).toBe(422);
    expect(((await noSecret.json()) as { reasons: string[] }).reasons).toContain('device secret missing: reload the game');
    expect((await handleScores(post(hot({ secret: 'short' })), d)).status).toBe(422);
    expect((await handleScores(post(hot()), d)).status).toBe(200);                          // claims "coby"
    const other = await handleScores(post(hot({ name: 'COBY', secret: OTHER }), { 'x-forwarded-for': '7.7.7.7' }), d);
    expect(other.status).toBe(403);
    expect(await d.store.kvGet('sb:own:coby')).not.toContain(SECRET);                          // only a hash is stored
    // the other device cannot ask for a code; the owner can
    expect((await handleScores(post({ op: 'transfer-code', name: 'Coby', secret: OTHER }, { 'x-forwarded-for': '7.7.7.7' }), d)).status).toBe(403);
    const free = await handleScores(post({ op: 'transfer-code', name: 'Nobody', secret: SECRET }, { 'x-forwarded-for': '7.7.7.8' }), d);
    expect(free.status).toBe(404);
    const c = await handleScores(post({ op: 'transfer-code', name: 'Coby', secret: SECRET }, { 'x-forwarded-for': '7.7.7.9' }), d);
    const { code } = await c.json() as { code: string };
    expect(code).toMatch(/^[A-HJKMNP-Z2-9]{6}$/);
    // a wrong code, then the right one typed loosely
    expect((await handleScores(post({ op: 'adopt', name: 'Coby', code: 'AAAAAA', secret: OTHER }, { 'x-forwarded-for': '6.6.6.1' }), d)).status).toBe(403);
    const ok = await handleScores(post({ op: 'adopt', name: 'coby', code: ` ${code.slice(0, 3).toLowerCase()}-${code.slice(3)} `, secret: OTHER }, { 'x-forwarded-for': '6.6.6.2' }), d);
    expect(ok.status).toBe(200);
    expect((await handleScores(post(hot({ secret: OTHER, time: lap.time - 1 }), { 'x-forwarded-for': '6.6.6.3' }), d)).status).toBe(200);
    expect((await handleScores(post(hot({ time: lap.time - 2 }), { 'x-forwarded-for': '6.6.6.4' }), d)).status).toBe(200);   // both devices post
    // single use
    expect((await handleScores(post({ op: 'adopt', name: 'Coby', code, secret: '11111111111111111111111111111111' }, { 'x-forwarded-for': '6.6.6.5' }), d)).status).toBe(403);
  });

  test('transfer codes: guessing is rate limited per IP, per IP + name, and per name from all IPs', async () => {
    const d = deps({ verify: fakeVerify });
    expect((await handleScores(post(hot()), d)).status).toBe(200);
    await handleScores(post({ op: 'transfer-code', name: 'Coby', secret: SECRET }, { 'x-forwarded-for': '5.5.5.5' }), d);
    const guess = (ip: string) => handleScores(post({ op: 'adopt', name: 'Coby', code: 'ZZZZZZ', secret: OTHER }, { 'x-forwarded-for': ip }), d);
    for (let i = 0; i < 5; i++) expect((await guess('4.4.4.4')).status).toBe(403);
    expect((await guess('4.4.4.4')).status).toBe(429);                                       // 5 per IP per 10 min
    // per name from all IPs: 100 per 10 min (5 here + 95 from 19 more addresses), then 429 for everyone
    for (let k = 0; k < 19; k++) for (let i = 0; i < 5; i++) expect((await guess(`3.3.${k}.1`)).status).toBe(403);
    expect((await guess('3.3.99.1')).status).toBe(429);
    // the owner's device is unaffected: it still posts
    expect((await handleScores(post(hot({ time: lap.time - 1 }), { 'x-forwarded-for': '2.2.2.2' }), d)).status).toBe(200);
  });

  test('old boards expire: hot-lap boards keyed by a physics version that is not current get a TTL', async () => {
    const store = new MemoryStore();
    const d = deps({ store, verify: fakeVerify });
    await store.submit(`hotlap:laguna_seca:probe_gt:oldphysics`, 'x', 120, true, '{}');
    await store.submit(`race:laguna_seca:probe_gt:${PV}:7-5L`, 'y', 700, true, '{}');
    expect((await handleScores(post(hot()), d)).status).toBe(200);
    const cur = boardKey('hotlap', 'laguna_seca', 'probe_gt', PV);
    expect(store.expiryOf('hotlap:laguna_seca:probe_gt:oldphysics')).not.toBeNull();
    expect(store.expiryOf(cur)).toBeNull();
    expect(store.expiryOf(`race:laguna_seca:probe_gt:${PV}:7-5L`)).toBeNull();
    expect(await sweepStaleBoards(d)).toEqual(['hotlap:laguna_seca:probe_gt:oldphysics']);
  });

  test('rate limit: 10 posts per IP per window, then 429 with Retry-After', async () => {
    const d = deps({ verify: fakeVerify });
    for (let i = 0; i < LIMITS.ratePosts; i++) expect((await handleScores(post(hot({ name: `n${i}` })), d)).status).toBe(200);
    const r = await handleScores(post(hot({ name: 'late' })), d);
    expect(r.status).toBe(429);
    expect(Number(r.headers.get('retry-after'))).toBeGreaterThan(0);
    expect((await handleScores(post(hot({ name: 'other' }), { 'x-forwarded-for': '8.8.8.8' }), d)).status).toBe(200);
  });

  test('same-origin only: foreign Origin refused, allowed list honoured, no Origin passes', async () => {
    const d = deps({ verify: fakeVerify, allowedOrigins: ['http://localhost:5173'] });
    const bad = await handleScores(post(hot(), { origin: 'https://evil.example' }), d);
    expect(bad.status).toBe(403);
    expect(bad.headers.get('access-control-allow-origin')).toBeNull();
    const dev = await handleScores(post(hot({ name: 'dev' }), { origin: 'http://localhost:5173', 'x-forwarded-for': '1.1.1.1' }), d);
    expect(dev.status).toBe(200);
    expect(dev.headers.get('access-control-allow-origin')).toBe('http://localhost:5173');
    expect((await handleScores(get('?board=bogus', { origin: 'https://evil.example' }), d)).status).toBe(403);
    const pre = await handleScores(new Request(`${ORIGIN}/api/scores`, { method: 'OPTIONS', headers: { host: 'probe.example', origin: ORIGIN } }), d);
    expect(pre.status).toBe(204);
    expect(pre.headers.get('access-control-allow-origin')).toBe(ORIGIN);
  });

  test('JSON errors: bad board key, bad JSON, wrong content type, oversize, wrong method', async () => {
    const d = deps();
    const bk = await handleScores(get('?board=nope'), d);
    expect(bk.status).toBe(400);
    expect(await bk.json()).toMatchObject({ ok: false, error: 'bad board key' });
    expect((await handleScores(post('{not json'), d)).status).toBe(400);
    expect((await handleScores(post('{}', { 'content-type': 'text/plain' }), d)).status).toBe(415);
    expect((await handleScores(post('{}', { 'content-length': String(LIMITS.maxBodyBytes + 1) }), d)).status).toBe(413);
    expect((await handleScores(new Request(`${ORIGIN}/api/scores`, { method: 'DELETE', headers: { host: 'probe.example' } }), d)).status).toBe(405);
    const r = await handleScores(post({ mode: 'hotlap', name: 'x' }), d);
    expect(r.status).toBe(422);
    expect(((await r.json()) as { reasons: string[] }).reasons.length).toBeGreaterThan(3);
  });

  test('a store failure becomes a 500 JSON error', async () => {
    const store = new MemoryStore();
    store.top = async () => { throw new Error('down'); };
    const r = await handleScores(get(`?board=hotlap:laguna_seca:probe_gt:${PV}`), deps({ store }));
    expect(r.status).toBe(500);
    expect(await r.json()).toEqual({ ok: false, error: 'internal error' });
  });
});
