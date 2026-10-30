// The race-recording endpoint (src/scoreboard/racehandler.ts, api/races.ts): POST by anyone within the scoreboard's limits, GET only
// with the owner token, the owner flag decided by the server.
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';
import { handleRaces, RACES, type RaceRecDeps } from '../../src/scoreboard/racehandler';
import { sweepStaleBoards } from '../../src/scoreboard/handler';
import { MemoryStore } from '../../src/scoreboard/store';
import { REC_MAX_BYTES, gzipText, type RaceRecording } from '../../src/scoreboard/racerec';

const ORIGIN = 'https://probe.example', TOKEN = 'owner-token-0123456789abcdef-xyz';
const sample = (over: Partial<RaceRecording> = {}): RaceRecording => ({
  v: 1, trackId: 'laguna_seca', fieldId: 'cars/field/pace.json', seed: 478797500, laps: 5, aiVersion: '9', buildSha: 'fd8a8d7', physics: 'abc123',
  build: { seed: 478797500, laps: 5, realGrid: false, playerAi: false, lod: false, strengthPct: 100, closeRacing: null, planner: null, fieldCap: null, ref: 'driver_a_best', autoShift: true, abs: true },
  config: { laps: 5, playerNumber: '619', aiControlEvery: 2, aiPhysicsEvery: 2, mishapRate: 0.0002 },
  inputs: { v: 1, physics: 'abc123', track: 'laguna_seca', car: 'probe_gt', hz: 100, dt: 0.001, reset: { pos: [1, 2, 3], heading: 0.5, speed: 22 }, ref: [[0, 'driver_a_best']],
    rows: [[0, 0, 0, 0, 24], [10, 100, 500, 0, 24], [20, 120, 700, 0, 24]], steps: 30 },
  events: [[15, 0, 1234.5]],
  live: { lapTimes: [], crossings: [{ car: '619', lapNr: 0, t: 40.1 }], results: null },
  snapshot: null, owner: false, started: '2026-10-30T12:00:00.000Z', durationS: 0.03,
  ...over,
});
let ipSeq = 0;
const post = async (deps: RaceRecDeps, body: BodyInit | null, h: Record<string, string> = {}, ip = `10.0.0.${++ipSeq}`) =>
  handleRaces(new Request(`${ORIGIN}/api/races`, { method: 'POST', headers: { host: 'probe.example', 'x-forwarded-for': ip, ...h }, body }), deps);
const gz = async (o: unknown): Promise<Uint8Array> => (await gzipText(JSON.stringify(o)))!;
const get = (deps: RaceRecDeps, q: string, token: string | null = TOKEN) =>
  handleRaces(new Request(`${ORIGIN}/api/races${q}`, { method: 'GET', headers: { host: 'probe.example', ...(token ? { 'x-owner-token': token } : {}) } }), deps);
const mk = (): RaceRecDeps => ({ store: new MemoryStore(), ownerToken: TOKEN, now: () => Date.parse('2026-10-30T12:30:00Z') });

describe('POST /api/races', () => {
  it('stores a gzipped or plain recording, answers 204, and lists / returns it for the owner only', async () => {
    const deps = mk();
    expect((await post(deps, await gz(sample()) as BodyInit, { 'content-type': 'application/gzip' })).status).toBe(204);
    expect((await post(deps, JSON.stringify(sample({ seed: 7 })), { 'content-type': 'application/json' })).status).toBe(204);
    const list = await (await get(deps, '?day=2026-10-30')).json() as { count: number; recordings: { id: string; seed: number; owner: boolean; track: string; bytes: number }[] };
    expect(list.count).toBe(2);
    expect(list.recordings.map((r) => r.seed).sort((a, b) => a - b)).toEqual([7, 478797500]);
    expect(list.recordings.every((r) => r.id.startsWith('2026-10-30-') && r.track === 'laguna_seca' && r.bytes > 0 && r.owner === false)).toBe(true);
    const one = await (await get(deps, `?id=${list.recordings[0].id}`)).json() as RaceRecording;
    expect(one.v).toBe(1); expect(one.inputs.rows.length).toBe(3); expect(one.owner).toBe(false);
    expect((await get(deps, '?day=2026-10-30', null)).status).toBe(403);          // the public cannot read
    expect((await get(deps, '?day=2026-10-30', 'x'.repeat(32))).status).toBe(403);
    expect((await get({ ...deps, ownerToken: undefined }, '?day=2026-10-30')).status).toBe(403);   // no token configured: nobody is the owner
    expect((await get(deps, '?id=nope')).status).toBe(400);
    expect((await get(deps, '?id=2026-10-30-000000000000')).status).toBe(404);
  });

  it('the owner flag is the server\'s: a claim without the token is dropped, the token makes it true', async () => {
    const deps = mk();
    await post(deps, await gz(sample({ owner: true, seed: 1 })) as BodyInit, { 'content-type': 'application/gzip' });                                  // claims, no token
    await post(deps, await gz(sample({ owner: false, seed: 2 })) as BodyInit, { 'content-type': 'application/gzip', 'x-owner-token': TOKEN });          // token
    await post(deps, await gz(sample({ owner: true, seed: 3 })) as BodyInit, { 'content-type': 'application/gzip', 'x-owner-token': 'a'.repeat(40) });   // wrong token
    const list = await (await get(deps, '?day=2026-10-30')).json() as { recordings: { id: string; seed: number; owner: boolean }[] };
    expect(Object.fromEntries(list.recordings.map((r) => [r.seed, r.owner]))).toEqual({ 1: false, 2: true, 3: false });
    for (const r of list.recordings) expect(((await (await get(deps, `?id=${r.id}`)).json()) as RaceRecording).owner).toBe(r.owner);
  });

  it('refuses what is not a recording: content type, size, bad JSON, bad shape, a gzip bomb, an unknown track', async () => {
    const deps = mk();
    expect((await post(deps, 'x', { 'content-type': 'text/plain' })).status).toBe(415);
    expect((await post(deps, '{', { 'content-type': 'application/json' })).status).toBe(400);
    expect((await post(deps, 'not gzip', { 'content-type': 'application/gzip' })).status).toBe(400);
    expect((await post(deps, 'x', { 'content-type': 'application/json', 'content-length': String(REC_MAX_BYTES + 1) })).status).toBe(413);
    expect((await post(deps, 'x'.repeat(REC_MAX_BYTES + 5), { 'content-type': 'application/json' })).status).toBe(413);   // past the cap whatever the header says
    const bomb = (await gzipText('['.padEnd(40 * 1024 * 1024, '0')))!;                                                      // 40 MB of text, a few KB gzipped
    expect(bomb.byteLength).toBeLessThan(REC_MAX_BYTES);
    expect((await post(deps, bomb as BodyInit, { 'content-type': 'application/gzip' })).status).toBe(400);
    const bad = async (over: Record<string, unknown>) => (await post(deps, JSON.stringify({ ...sample(), ...over }), { 'content-type': 'application/json' }));
    for (const over of [{ aiVersion: 9 }, { buildSha: { a: 1 } }, { seed: -1 }, { laps: 99 }, { v: 2 }, { inputs: { ...sample().inputs, steps: 99_999_999 } }, { inputs: { ...sample().inputs, rows: [[0, 5000, 0, 0, 0]] } }, { events: [[1, 7, 0]] }, { live: null }]) {
      const r = await bad(over);
      expect(r.status, JSON.stringify(Object.keys(over))).toBe(422);
    }
    expect((await bad({ trackId: 'monza' })).status).toBe(422);
    expect((await (await get(deps, '?day=2026-10-30')).json() as { count: number }).count).toBe(0);   // nothing was stored
  });

  it('is rate limited per IP like the scoreboard, refuses another origin, and only knows GET / POST / OPTIONS', async () => {
    const deps = mk();
    const same = '10.9.9.9';
    for (let i = 0; i < RACES.perIp; i++) expect((await post(deps, JSON.stringify(sample()), { 'content-type': 'application/json' }, same)).status).toBe(204);
    const r = await post(deps, JSON.stringify(sample()), { 'content-type': 'application/json' }, same);
    expect(r.status).toBe(429); expect(r.headers.get('retry-after')).toBeTruthy();
    expect((await post(deps, JSON.stringify(sample()), { 'content-type': 'application/json', origin: 'https://evil.example' })).status).toBe(403);
    expect((await handleRaces(new Request(`${ORIGIN}/api/races`, { method: 'DELETE', headers: { host: 'probe.example' } }), deps)).status).toBe(405);
    const o = await handleRaces(new Request(`${ORIGIN}/api/races`, { method: 'OPTIONS', headers: { host: 'probe.example', origin: ORIGIN } }), deps);
    expect(o.status).toBe(204); expect(o.headers.get('access-control-allow-headers')).toContain('X-Owner-Token');
  });
});

describe('the scoreboard\'s stale-board sweep', () => {
  it('leaves the recordings\' day indexes alone', async () => {
    const deps = mk();
    await post(deps, JSON.stringify(sample()), { 'content-type': 'application/json' });
    expect(await deps.store.boards()).toEqual(['rr:2026-10-30']);
    const expired = await sweepStaleBoards({ store: deps.store, assets: async () => { throw new Error('unused'); }, physics: async () => 'x' });
    expect(expired).toEqual([]);
  });
});

describe('api/races.ts (the deployed entry point)', () => {
  beforeAll(() => {
    for (const k of ['UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'KV_REST_API_URL', 'KV_REST_API_TOKEN']) vi.stubEnv(k, '');
    vi.stubEnv('RACES_OWNER_TOKEN', TOKEN);
  });
  afterAll(() => { vi.unstubAllEnvs(); });
  it('POST then owner GET through the module, memory store', async () => {
    const m = await import('../races');
    const p = await m.POST(new Request(`${ORIGIN}/api/races`, { method: 'POST', headers: { host: 'probe.example', 'content-type': 'application/json', 'x-forwarded-for': '10.1.1.1' }, body: JSON.stringify(sample()) }));
    expect(p.status).toBe(204);
    const day = new Date().toISOString().slice(0, 10);
    const l = await m.GET(new Request(`${ORIGIN}/api/races?day=${day}`, { headers: { host: 'probe.example', 'x-owner-token': TOKEN } }));
    expect(((await l.json()) as { count: number }).count).toBe(1);
    expect((await m.GET(new Request(`${ORIGIN}/api/races?day=${day}`, { headers: { host: 'probe.example' } }))).status).toBe(403);
  });
});
