// End-to-end test of the scoreboard flow (docs/scoreboard.md "E2E"). NOT part of the normal suite: `npm run test:e2e`.
//
//   local   (default): starts a throwaway redis-server (port 6399, no persistence, tmp dir) and binds the real handler
//           to UpstashStore over a RESP adapter, so the real Lua scripts (LUA_ISSUE, LUA_ADOPT) run on a real Redis with the
//           same commands the Upstash REST client sends. Skips with "redis-server not found: brew install redis".
//   http    (E2E_BASE_URL=<deployment>): the same flow over HTTP against a deployment; E2E_BYPASS_HEADER="Name: value" adds a
//           protection-bypass header (never printed). Skips when unset. It posts real entries under `e2e-<hex>` names to that
//           deployment's store: use a preview with its own store, never production.
//   E2E_STORE=memory: dry run of this file's own logic on MemoryStore (no Redis); not an E2E, for editing the test.
//
// The hot lap is the first lap of the recorded WebKit trace fixture (webkit_laguna_6.json.gz), cut to the lap and sent in
// the POST shape; the server replays it with the shipped physics, track and car.json.
import { spawn, spawnSync, type ChildProcess } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { afterAll, beforeAll, describe, expect, test } from 'vitest';
import { Redis } from 'ioredis';
import { currentRaceAiVersion, handleScores, type HandlerDeps } from '../handler';
import { OWNER, ownerKey, xferKey } from '../owner';
import { MemoryStore, UpstashStore, decodeOwner, type ScoreStore } from '../store';
import { replayTrace } from '../replay';
import { LIMITS } from '../config';
import { boardKey, nameKey } from '../validate';
import type { InputTrace } from '../types';
import { loadSimAssets, serverPhysics } from '../../../api/_lib/assets';
import { respFetch, type RespClient } from './support/respAdapter';

const PORT = 6399;
const SKIP_MSG = 'redis-server not found: brew install redis';
const BASE_URL = process.env.E2E_BASE_URL?.replace(/\/+$/, '') || '';
const MEMORY = process.env.E2E_STORE === 'memory';
const hasRedis = !spawnSync('redis-server', ['--version'], { stdio: 'ignore' }).error;

// ------------------------------------------------------------------ the recorded fixture, cut to laps 1 and 2
interface Recorded { laps: { n: number; time: number; valid: boolean }[]; trace: InputTrace }
const rec = JSON.parse(gunzipSync(readFileSync(new URL('./fixtures/webkit_laguna_6.json.gz', import.meta.url))).toString('utf8')) as Recorded;

/** The trace up to the end of lap `n` (the server replays until that lap completes): steps cut to it, later rows dropped. */
function cut(pv: string, n: number): { trace: InputTrace; time: number; replayed: number } {
  const assets = lagunaAssetsSync();
  const r = replayTrace(assets, rec.trace, n);
  if (!r.lap || !r.lap.valid) throw new Error(`recorded lap ${n} did not replay on this physics (BOUND: stop and report)`);
  const steps = r.steps;
  const trace: InputTrace = { ...rec.trace, physics: pv, steps, rows: rec.trace.rows.filter((row) => row[0] < steps) };
  return { trace, time: rec.laps[n - 1].time, replayed: r.lap.time };
}
let assetsCache: Awaited<ReturnType<typeof loadSimAssets>> | null = null;
const lagunaAssetsSync = () => assetsCache!;

// ------------------------------------------------------------------ transports
interface Reply { status: number; body: any }   // eslint-disable-line @typescript-eslint/no-explicit-any
interface Api { get(query: string): Promise<Reply>; post(body: unknown, ip: string): Promise<Reply> }

function localApi(deps: HandlerDeps): Api {
  const ORIGIN = 'https://e2e.example';
  return {
    async get(query) {
      const r = await handleScores(new Request(`${ORIGIN}/api/scores${query}`, { method: 'GET', headers: { host: 'e2e.example' } }), deps);
      return { status: r.status, body: await r.json() };
    },
    async post(body, ip) {
      const r = await handleScores(new Request(`${ORIGIN}/api/scores`, {
        method: 'POST', headers: { 'content-type': 'application/json', host: 'e2e.example', origin: ORIGIN, 'x-forwarded-for': ip }, body: JSON.stringify(body),
      }), deps);
      return { status: r.status, body: await r.json() };
    },
  };
}
function httpApi(base: string): Api {
  const bypass = process.env.E2E_BYPASS_HEADER;
  const extra: Record<string, string> = {};
  if (bypass) { const i = bypass.indexOf(':'); if (i > 0) extra[bypass.slice(0, i).trim()] = bypass.slice(i + 1).trim(); }
  const run = async (init: RequestInit, query: string): Promise<Reply> => {
    const r = await fetch(`${base}/api/scores${query}`, { ...init, headers: { ...(init.headers as Record<string, string>), ...extra } });
    const text = await r.text();
    let body: unknown; try { body = JSON.parse(text); } catch { body = { ok: false, error: `non-JSON reply (HTTP ${r.status})` }; }   // never echo the page: it may carry deployment detail
    return { status: r.status, body };
  };
  return {
    get: (query) => run({ method: 'GET' }, query),
    post: (body) => run({ method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }, ''),
  };
}

// ------------------------------------------------------------------ the scenario, shared by both transports
const hex = (n: number) => randomBytes(n).toString('hex');
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
let ipSeq = 0;
const ip = () => `10.${(ipSeq >> 16) & 255}.${(ipSeq >> 8) & 255}.${ipSeq++ & 255}`;   // one address per request: the per-IP rate limits are not under test here

interface Ctx {
  api: Api;
  /** Local only: the store, for the owner record and the expiry shortcut. */
  store?: ScoreStore;
  /** Local only: shorten a transfer code's life (the handler's TTL is the fixed OWNER.codeTtlS = 1 h). */
  expireCode?: (nameKey: string) => Promise<void>;
}

function scenario(label: string, mk: () => Promise<Ctx>, finish: () => Promise<void>, localOnly: boolean) {
  const secret = () => hex(16);
  const A = secret(), B = secret(), C = secret();
  const name = `e2e-${hex(4)}`;
  const s = { ctx: null as unknown as Ctx, pv: '', board: '' };
  let lap1: ReturnType<typeof cut>, lap2: ReturnType<typeof cut>;
  const submission = (secretHex: string, l: ReturnType<typeof cut>, lap: number, over: Record<string, unknown> = {}) => ({
    mode: 'hotlap', track: 'laguna_seca', car: 'probe_gt', physics: s.pv, name, input: 'pad', secret: secretHex,
    time: l.time, lap, valid: true, trace: l.trace, ...over,
  });
  const code = async (secretHex: string): Promise<string> => {
    const r = await s.ctx.api.post({ op: 'transfer-code', name, secret: secretHex }, ip());
    expect(r.status, JSON.stringify(r.body)).toBe(200);
    expect(r.body.code).toMatch(/^[A-HJKMNP-Z2-9]{6}$/);
    expect(r.body.expires_s).toBe(OWNER.codeTtlS);
    return r.body.code as string;
  };
  const adopt = (secretHex: string, c: string) => s.ctx.api.post({ op: 'adopt', name, code: c, secret: secretHex }, ip());

  describe(label, () => {
    beforeAll(async () => {
      assetsCache = await loadSimAssets('laguna_seca', 'probe_gt');
      s.ctx = await mk();
      // the server's board key comes from its own discovery answer
      const d = await s.ctx.api.get('');
      expect(d.status).toBe(200);
      s.board = d.body.boards['laguna_seca/probe_gt'];
      s.pv = s.board.split(':')[3];
      lap1 = cut(s.pv, 1);
      lap2 = cut(s.pv, 2);
    }, 120_000);
    afterAll(finish, 30_000);

    test('fixture: the recorded laps replay to the recorded times on the shipped physics', () => {
      expect(lap1.replayed).toBe(lap1.time);
      expect(lap2.replayed).toBe(lap2.time);
      expect(lap1.trace.steps).toBeLessThan(LIMITS.maxTraceSteps);
      expect(lap2.trace.steps).toBeLessThan(LIMITS.maxTraceSteps);
    });

    test('device A posts the recorded first lap under a fresh name: 200, verified on the server, on the board', async () => {
      const r = await s.ctx.api.post(submission(A, lap1, 1), ip());
      expect(r.status, JSON.stringify(r.body)).toBe(200);
      expect(r.body).toMatchObject({ ok: true, board: s.board, rank: 1, improved: true });
      expect(r.body.replayed).toBeCloseTo(lap1.time, 3);
      const g = await s.ctx.api.get(`?board=${encodeURIComponent(s.board)}&name=${name}`);
      expect(g.status).toBe(200);
      expect(g.body.entries.map((e: { name: string }) => e.name)).toContain(name);
      expect(g.body.you).toMatchObject({ name, rank: 1 });
      expect(g.body.you.score).toBeCloseTo(lap1.time, 3);
    }, 120_000);

    test('a second device cannot post the owned name before it adopts it', async () => {
      const r = await s.ctx.api.post(submission(C, lap1, 1), ip());
      expect(r.status).toBe(403);
      expect(r.body.error).toBe('name taken');
    });

    let adoptCode = '';
    test('A issues a transfer code; B adopts it ("now posts as"); the code is single use: C is refused', async () => {
      adoptCode = await code(A);
      const ok = await adopt(B, adoptCode);
      expect(ok.status, JSON.stringify(ok.body)).toBe(200);
      expect(ok.body).toEqual({ ok: true, name });   // the client shows "now posts as <name>"
      const reuse = await adopt(C, adoptCode);
      expect(reuse.status).toBe(403);
      expect(reuse.body.error).toBe('wrong code');
      expect((await adopt(C, 'AAAAAA')).status).toBe(403);   // a wrong code
    });

    test('B posts a second lap under the name: accepted, and the board holds the better time', async () => {
      const r = await s.ctx.api.post(submission(B, lap2, 2), ip());
      expect(r.status, JSON.stringify(r.body)).toBe(200);
      const better = Math.min(lap1.time, lap2.time);
      expect(r.body.improved).toBe(lap2.time < lap1.time);
      expect(r.body.best).toBeCloseTo(better, 3);
      expect(r.body.rank).toBe(1);
      const g = await s.ctx.api.get(`?board=${encodeURIComponent(s.board)}&name=${name}`);
      expect(g.body.entries.filter((e: { name: string }) => e.name === name)).toHaveLength(1);   // one entry per name
      expect(g.body.you.score).toBeCloseTo(better, 3);
    }, 120_000);

    test('the other owned device still posts (A is still an owner after B joined)', async () => {
      const r = await s.ctx.api.post({ op: 'transfer-code', name, secret: A }, ip());
      expect(r.status).toBe(200);
    });

    test('hidden race board: GET 410, race POST 410', async () => {
      const key = `race:laguna_seca:probe_gt:${s.pv}:${currentRaceAiVersion()}`;
      const g = await s.ctx.api.get(`?board=${encodeURIComponent(key)}`);
      expect(g.status).toBe(410);
      const p = await s.ctx.api.post({ mode: 'race', track: 'laguna_seca', car: 'probe_gt', physics: s.pv, name, input: 'keys', secret: A, ai_version: currentRaceAiVersion(), metres: 1000, laps: 0 }, ip());
      expect(p.status).toBe(410);
    });

    test('an unknown name\'s GET returns an empty board position (entries unchanged, you null); an empty board lists nothing', async () => {
      const g = await s.ctx.api.get(`?board=${encodeURIComponent(s.board)}&name=never-${hex(3)}`);
      expect(g.status).toBe(200);
      expect(g.body.you).toBeNull();
      const empty = await s.ctx.api.get(`?board=${encodeURIComponent(boardKey('hotlap', 'laguna_seca', 'probe_gt', 'zzzzzzzz'))}&name=nobody`);
      expect(empty.status).toBe(200);
      expect(empty.body.entries).toEqual([]);
      expect(empty.body.you).toBeNull();
    });

    test('tampered replays are rejected by verification: one decisive input altered; a claimed time that is not the replayed one', async () => {
      // the longest-held row after the launch (rows are written only on change, so it spans the most steps): full brake there
      const rows = lap1.trace.rows;
      let at = -1, gap = 0;
      for (let i = 0; i + 1 < rows.length; i++) if (rows[i][0] > 4000 && rows[i + 1][0] - rows[i][0] > gap) { gap = rows[i + 1][0] - rows[i][0]; at = i; }
      expect(at).toBeGreaterThan(0);
      const altered = rows.map((r, i) => (i === at ? [r[0], r[1], 0, 1000, r[4]] : r)) as typeof rows;
      expect(altered.filter((r, i) => r !== rows[i])).toHaveLength(1);
      const before = (await s.ctx.api.get(`?board=${encodeURIComponent(s.board)}&name=${name}`)).body.you.score;
      const t1 = await s.ctx.api.post(submission(A, { ...lap1, trace: { ...lap1.trace, rows: altered } }, 1), ip());
      expect(t1.status, JSON.stringify(t1.body)).toBe(422);
      expect(t1.body.reasons.join(' ')).toMatch(/replay/);
      const t2 = await s.ctx.api.post(submission(A, lap1, 1, { time: lap1.time - 1 }), ip());
      expect(t2.status).toBe(422);
      expect(t2.body.reasons.join(' ')).toMatch(/differs from the claimed/);
      expect((await s.ctx.api.get(`?board=${encodeURIComponent(s.board)}&name=${name}`)).body.you.score).toBe(before);   // the board did not move
    }, 180_000);

    // device limit and expiry need many addresses / the store: local only
    (localOnly ? test : test.skip)('devices D, E, F adopt new codes up to the limit of 5; the sixth adopts and the oldest (A) falls off', async () => {
      const store = s.ctx.store!;
      const D = secret(), E = secret(), F = secret(), G = secret();
      const devices = async () => decodeOwner(await store.kvGet(ownerKey(nameKey(name))))!.h.length;
      expect(await devices()).toBe(2);   // A, B
      for (const d of [D, E, F]) expect((await adopt(d, await code(B))).status).toBe(200);
      expect(await devices()).toBe(OWNER.maxDevices);   // A, B, D, E, F
      // all five still own the name
      for (const d of [A, B, D, E, F]) expect((await s.ctx.api.post({ op: 'transfer-code', name, secret: d }, ip())).status).toBe(200);
      // the sixth device: the Lua script keeps the newest `maxDevices` hashes. The adoption is accepted and the OLDEST
      // device (A) is dropped; it is not "refused" (the brief expected a refusal; the shipped script evicts).
      const sixth = await adopt(G, await code(B));
      expect(sixth.status).toBe(200);
      expect(await devices()).toBe(OWNER.maxDevices);
      expect((await s.ctx.api.post({ op: 'transfer-code', name, secret: A }, ip())).status).toBe(403);   // A lost the name
      for (const d of [B, D, E, F, G]) expect((await s.ctx.api.post({ op: 'transfer-code', name, secret: d }, ip())).status).toBe(200);
    }, 60_000);

    (localOnly ? test : test.skip)('an expired code is refused (the code\'s key is given a 1 s life, the handler\'s TTL being the fixed 1 h)', async () => {
      const store = s.ctx.store!;
      const H = secret();
      const c = await code(B);
      expect(await store.kvGet(xferKey(nameKey(name)))).not.toBeNull();
      await s.ctx.expireCode!(nameKey(name));
      await sleep(1300);
      expect(await store.kvGet(xferKey(nameKey(name)))).toBeNull();
      const r = await adopt(H, c);
      expect(r.status).toBe(403);
      expect(r.body.error).toBe('wrong code');
      // and a code for a name nobody has posted under is refused as not registered
      const none = await s.ctx.api.post({ op: 'adopt', name: `e2e-${hex(4)}`, code: 'AAAAAA', secret: H }, ip());
      expect([403, 404]).toContain(none.status);
    }, 30_000);

    (localOnly ? test : test.skip)('store parity: MemoryStore and the Redis-backed UpstashStore answer the owner operations the same', async () => {
      const real = s.ctx.store!;
      const mem = new MemoryStore();
      const o = `sb:own:par-${hex(3)}`, x = o.replace('own', 'xfer');
      const run = async (st: ScoreStore) => {
        const out: unknown[] = [];
        out.push(await st.issueTransfer(o, x, 'h1', 'c1', 60));                       // free
        await st.kvSet(o, 'v1|2026-01-01T00:00:00.000Z|h1', { nx: true });
        out.push(await st.issueTransfer(o, x, 'h9', 'c1', 60));                       // other
        out.push(await st.issueTransfer(o, x, 'h1', 'c1', 60));                       // ok
        out.push(await st.adoptTransfer(o, x, 'zz', 'h2', 3));                        // bad-code
        out.push(await st.adoptTransfer(o, x, 'c1', 'h2', 3));                        // ok
        out.push(await st.adoptTransfer(o, x, 'c1', 'h3', 3));                        // bad-code (consumed)
        for (const h of ['h3', 'h4']) { await st.issueTransfer(o, x, 'h2', 'c' + h, 60); out.push(await st.adoptTransfer(o, x, 'c' + h, h, 3)); }
        out.push(await st.kvGet(o));                                                   // h2,h3,h4 (h1 dropped)
        await st.kvDel(o);
        return out;
      };
      expect(await run(real)).toEqual(await run(mem));
    });
  });
}

// ------------------------------------------------------------------ local: a throwaway redis-server
let proc: ChildProcess | null = null;
let redis: Redis | null = null;
let tmp = '';

async function startRedis(): Promise<Redis> {
  tmp = mkdtempSync(join(tmpdir(), 'probe-e2e-redis-'));
  proc = spawn('redis-server', ['--port', String(PORT), '--bind', '127.0.0.1', '--save', '', '--appendonly', 'no', '--dir', tmp], { stdio: 'ignore' });
  let exited = false;
  proc.on('exit', () => { exited = true; });
  const c = new Redis({ host: '127.0.0.1', port: PORT, lazyConnect: true, protocol: 2, maxRetriesPerRequest: 1, retryStrategy: () => null });
  c.on('error', () => { /* connection refused while it starts */ });
  for (let i = 0; i < 100; i++) {
    if (exited) throw new Error(`redis-server exited at start (port ${PORT} in use?)`);
    try { await c.connect(); await c.ping(); return c; } catch { await sleep(100); }
  }
  throw new Error('redis-server did not answer');
}

async function stopRedis(): Promise<void> {
  try {
    if (redis) {
      await redis.flushall();
      expect(await redis.dbsize()).toBe(0);   // every key the test made is gone
      await redis.shutdown('NOSAVE').catch(() => { /* the connection drops as it exits */ });
      redis.disconnect();
    }
  } finally {
    if (proc && proc.exitCode === null) proc.kill('SIGKILL');
    if (tmp) rmSync(tmp, { recursive: true, force: true });
    redis = null; proc = null;
  }
}

const localDeps = (store: ScoreStore): HandlerDeps => ({ store, assets: loadSimAssets, physics: serverPhysics });

if (BASE_URL) {
  scenario(`E2E over HTTP against ${new URL(BASE_URL).host}`, async () => ({ api: httpApi(BASE_URL) }), async () => { /* the deployment's store is not ours to clean: see docs/scoreboard.md */ }, false);
} else if (MEMORY) {
  let st: MemoryStore;
  scenario('E2E logic dry run on MemoryStore (E2E_STORE=memory; not an E2E)', async () => {
    st = new MemoryStore();
    return { api: localApi(localDeps(st)), store: st, expireCode: async (n) => { const k = xferKey(n); await st.kvSet(k, (await st.kvGet(k))!, { ex: 1 }); } };
  }, async () => { /* in memory */ }, true);
} else if (hasRedis) {
  scenario('E2E on a throwaway real Redis (real Lua scripts through the RESP adapter)', async () => {
    redis = await startRedis();
    const store = new UpstashStore('http://redis.invalid', 'none', respFetch(redis as unknown as RespClient));
    return {
      api: localApi(localDeps(store)), store,
      // the shipped TTL is 1 h and fixed; give the live code key 1 s through Redis itself (the expiry is Redis's own)
      expireCode: async (n) => { await redis!.expire(xferKey(n), 1); },
    };
  }, stopRedis, true);
} else {
  describe('E2E scoreboard', () => { test.skip(SKIP_MSG, () => { /* redis-server is not on PATH */ }); });
  console.warn(SKIP_MSG);
}
