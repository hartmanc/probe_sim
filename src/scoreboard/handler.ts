// The scoreboard HTTP handler (Web Request -> Response), used by api/scores.ts and tested directly.
// Pure TS: storage and asset loading are injected.
import { CARS, LIMITS, TRACKS } from './config';
import { AI_VERSION } from '../physics/ai/field';
import { checkTrace, verifyHotlap } from './replay';
import { clientIp, originAllowed } from './http';
export { clientIp, originAllowed };
import { OWNER, SECRET_RE, adopt, claim, issueCode, normalizeCode, ownership } from './owner';
import type { SimAssets } from './sim';
import type { ScoreStore } from './store';
import type { ApiError, Board, GhostReply, HotlapSubmission, InputType, RaceSubmission, Score, SubmitResult } from './types';
import { boardKey, lowerIsBetter, nameKey, normalizeName, parseBoardKey, raceScore, validateSubmission } from './validate';

export interface HandlerDeps {
  store: ScoreStore;
  /** Decoded sim assets for a whitelisted track + car (cached by the caller). */
  assets(track: string, car: string): Promise<SimAssets>;
  /** The server's physicsVersion() for a track + car. */
  physics(track: string, car: string): Promise<string>;
  /** Extra origins allowed besides the request's own host (e.g. a local Vite dev server). */
  allowedOrigins?: string[];
  /** Replay override (tests). */
  verify?: typeof verifyHotlap;
  log?: (msg: string) => void;
  /**
   * Race boards (owner, 26 Oct 2026): hidden for the public until a race replay exists, so by default race posts are
   * refused (410) and race boards are not served. true re-opens them (tests keep the race code paths covered).
   */
  raceBoards?: boolean;
  /** Clock (ms) for the stale-board sweep (tests). */
  now?: () => number;
}

/** The race board version the server accepts (the client's raceBoardVersion(AI_VERSION) in src/app/modes/race.ts). */
export const currentRaceAiVersion = (): string => `${AI_VERSION}-${LIMITS.raceLaps}L`;

const RACE_CLOSED = 'race boards are closed until races can be replayed on the server; hot-lap boards are open';

interface Meta { name: string; input: InputType; at: string; ai_version?: string; laps?: number; finished?: boolean; device?: string; replayed?: number; claimed?: number }

const BASE_HEADERS: Record<string, string> = {
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'no-store',
  'X-Content-Type-Options': 'nosniff',
};

function json(status: number, body: unknown, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { ...BASE_HEADERS, ...extra } });
}
const fail = (status: number, error: string, reasons?: string[], extra?: Record<string, string>) =>
  json(status, { ok: false, error, ...(reasons && reasons.length ? { reasons } : {}) } satisfies ApiError, extra);

function toScore(rank: number, score: number, meta: string | null, member: string): Score {
  let m: Partial<Meta> = {};
  try { m = meta ? (JSON.parse(meta) as Meta) : {}; } catch { m = {}; }
  const s: Score = { rank, name: m.name ?? member, score, input: m.input ?? 'keys', at: m.at ?? '' };
  if (m.ai_version !== undefined) s.ai_version = m.ai_version;
  if (m.laps !== undefined) s.laps = m.laps;
  return s;
}

/** Where a hot-lap board's current #1 lap is kept: one string key per board, overwritten by the next #1, expired with the stale board. */
export const topKey = (board: string): string => `sb:top:${board}`;

interface TopRecord { v: 1; name: string; score: number; at: string; input: InputType; lap: number; trace: HotlapSubmission['trace'] }

/** GET ?ghost=<board key>: the board's #1 lap with its input trace, validated as it was on the way in. */
async function getGhost(req: Request, key: string, deps: HandlerDeps): Promise<Response> {
  const none = (reason: string) => fail(404, 'no ghost', [reason]);
  const b = parseBoardKey(key);
  if (!b || b.mode !== 'hotlap') return fail(400, 'bad board key', ['ghost needs a hot-lap board key: hotlap:<track>:<car>:<physics>']);
  const rl = await deps.store.hit(`ghost:${clientIp(req)}`, LIMITS.rateWindowS);
  if (rl.count > LIMITS.rateGhosts) return fail(429, 'rate limited', [`at most ${LIMITS.rateGhosts} ghost downloads per ${LIMITS.rateWindowS / 60} min`], { 'Retry-After': String(Math.max(1, rl.ttl)) });
  const raw = await deps.store.kvGet(topKey(key));
  if (!raw) return none('this board has no stored top lap yet');
  let rec: Partial<TopRecord>;
  try { rec = JSON.parse(raw) as Partial<TopRecord>; } catch { return none('the stored top lap is unreadable'); }
  const t = rec.trace;
  if (rec.v !== 1 || typeof rec.name !== 'string' || typeof rec.score !== 'number' || !Number.isFinite(rec.score) || typeof rec.at !== 'string'
    || typeof rec.lap !== 'number' || !Number.isInteger(rec.lap) || rec.lap < 1 || rec.lap > LIMITS.maxLap || !t || typeof t !== 'object') return none('the stored top lap is malformed');
  if (checkTrace(t).length || t.physics !== b.physics || t.track !== b.track || t.car !== b.car) return none('the stored top lap does not match this board');
  // the stored lap must still be the board's #1 (a concurrent post or a trimmed entry could have left it behind)
  const [top] = await deps.store.top(key, 1, true);
  if (!top || top.member !== nameKey(rec.name) || Math.abs(top.score - rec.score) > 1e-6) return none('the stored top lap is not the board\'s #1 any more');
  const out: GhostReply = { ok: true, board: key, name: rec.name, score: rec.score, at: rec.at, input: rec.input === 'pad' || rec.input === 'phone' ? rec.input : 'keys', lap: rec.lap, trace: t };
  return json(200, out);
}

async function getBoard(req: Request, deps: HandlerDeps): Promise<Response> {
  const u = new URL(req.url);
  const gk = u.searchParams.get('ghost');
  if (gk) return getGhost(req, gk, deps);
  const key = u.searchParams.get('board');
  if (!key) {
    // discovery: the server's current hot-lap boards (handy for the client and for smoke tests)
    const boards: Record<string, string> = {};
    for (const t of Object.keys(TRACKS)) for (const c of Object.keys(CARS)) {
      try { boards[`${t}/${c}`] = boardKey('hotlap', t, c, await deps.physics(t, c)); } catch { /* asset missing */ }
    }
    return json(200, { ok: true, store: deps.store.kind, boards });
  }
  const b = parseBoardKey(key);
  if (!b) return fail(400, 'bad board key', ['board must look like hotlap:<track>:<car>:<physics> or race:<track>:<car>:<physics>:<ai_version>']);
  if (b.mode === 'race' && !deps.raceBoards) return fail(410, 'gone', [RACE_CLOSED]);
  const asc = lowerIsBetter(b.mode);
  const rows = await deps.store.top(key, LIMITS.top, asc);
  const out: Board = { board: key, mode: b.mode, entries: rows.map((r, i) => toScore(i + 1, r.score, r.meta, r.member)) };
  const qn = u.searchParams.get('name');
  if (qn !== null) {
    const n = normalizeName(qn);
    out.you = null;
    if (n) {
      const m = nameKey(n);
      const rk = await deps.store.rank(key, m, asc);
      if (rk !== null) {
        const [sc, meta] = await Promise.all([deps.store.score(key, m), deps.store.meta(key, m)]);
        if (sc !== null) out.you = toScore(rk + 1, sc, meta, m);
      }
    }
  }
  return json(200, { ok: true, ...out });
}

async function postScore(req: Request, deps: HandlerDeps): Promise<Response> {
  const ct = req.headers.get('content-type') ?? '';
  if (!ct.toLowerCase().startsWith('application/json')) return fail(415, 'content-type must be application/json');
  const len = Number(req.headers.get('content-length') ?? '0');
  if (len > LIMITS.maxBodyBytes) return fail(413, 'payload too large');

  // rate limit before any parsing / replay work
  const rl = await deps.store.hit(`post:${clientIp(req)}`, LIMITS.rateWindowS);
  if (rl.count > LIMITS.ratePosts) return fail(429, 'rate limited', [`at most ${LIMITS.ratePosts} submissions per ${LIMITS.rateWindowS / 60} min`], { 'Retry-After': String(Math.max(1, rl.ttl)) });

  const text = await req.text();
  if (text.length > LIMITS.maxBodyBytes) return fail(413, 'payload too large');
  let body: unknown;
  try { body = JSON.parse(text); } catch { return fail(400, 'body is not valid JSON'); }

  if (body && typeof body === 'object' && !Array.isArray(body) && 'op' in body) return nameOp(req, body as Record<string, unknown>, deps);
  if ((body as { mode?: unknown })?.mode === 'race' && !deps.raceBoards) return fail(410, 'gone', [RACE_CLOSED]);

  const physicsCache = new Map<string, string>();
  const b0 = body as { track?: unknown; car?: unknown };
  if (typeof b0?.track === 'string' && typeof b0?.car === 'string' && Object.hasOwn(TRACKS, b0.track) && Object.hasOwn(CARS, b0.car)) {
    try { physicsCache.set(`${b0.track}/${b0.car}`, await deps.physics(b0.track, b0.car)); } catch (e) {
      deps.log?.(`assets unavailable: ${(e as Error).message}`);
      return fail(503, 'server assets unavailable');
    }
  }
  const v = validateSubmission(body, (t, c) => physicsCache.get(`${t}/${c}`));
  if (!v.ok || !v.value) return fail(422, 'rejected', v.reasons);
  const sub = v.value;
  const name = sub.name;
  const member = nameKey(name);
  // name ownership (owner.ts): a device secret is required; a name another device owns is refused before any replay
  const secret = (body as { secret?: unknown }).secret;
  if (typeof secret !== 'string' || !SECRET_RE.test(secret)) return fail(422, 'rejected', ['device secret missing: reload the game']);
  if ((await ownership(deps.store, member, secret)) === 'other') {
    return fail(403, 'name taken', [`"${name}" belongs to another device. Type its transfer code (Scoreboard settings on that device) or pick another name.`]);
  }
  if (sub.mode === 'race' && (sub as RaceSubmission).ai_version !== currentRaceAiVersion()) return fail(422, 'rejected', ['race AI version is not current: reload the game']);
  const at = new Date().toISOString();
  let score: number, meta: Meta, key: string;
  let replayed: number | undefined;

  if (sub.mode === 'hotlap') {
    const s = sub as HotlapSubmission;
    const assets = await deps.assets(s.track, s.car);
    const verdict = (deps.verify ?? verifyHotlap)(assets, s.trace, s.lap, s.time);
    deps.log?.(`replay ${verdict.ok ? 'ok' : 'rejected'} claimed ${s.time} replayed ${verdict.replayed} cpu ${verdict.cpuMs} ms`);
    if (!verdict.ok || verdict.replayed === null) return fail(422, 'rejected', verdict.reasons);
    replayed = Math.round(verdict.replayed * 1000) / 1000;
    score = replayed;
    key = boardKey('hotlap', s.track, s.car, s.physics);
    meta = { name, input: s.input, at, replayed, claimed: s.time, ...(s.device ? { device: s.device } : {}) };
  } else {
    const s = sub as RaceSubmission;
    score = raceScore(s, Object.hasOwn(TRACKS, s.track) ? TRACKS[s.track].length_m : 0);
    key = boardKey('race', s.track, s.car, s.physics, s.ai_version);
    meta = { name, input: s.input, at, ai_version: s.ai_version, laps: s.laps, finished: !!s.finished, ...(s.device ? { device: s.device } : {}) };
  }
  if (!(await claim(deps.store, member, secret))) return fail(403, 'name taken', [`"${name}" was just claimed by another device`]);
  const asc = lowerIsBetter(sub.mode);
  const res = await deps.store.submit(key, member, score, asc, JSON.stringify(meta), LIMITS.keep);
  const rk = await deps.store.rank(key, member, asc);
  // a new #1 keeps its trace (one bounded key per board) so the game can rebuild the all-time-best ghost (GET ?ghost=)
  if (sub.mode === 'hotlap' && res.improved && rk === 0) {
    const s = sub as HotlapSubmission;
    const rec: TopRecord = { v: 1, name, score, at, input: s.input, lap: s.lap, trace: s.trace };
    try { await deps.store.kvSet(topKey(key), JSON.stringify(rec)); } catch (e) { deps.log?.(`top trace not kept: ${(e as Error).message}`); }
  }
  const out: SubmitResult = { ok: true, board: key, rank: rk === null ? null : rk + 1, best: res.best, improved: res.improved };
  if (replayed !== undefined) out.replayed = replayed;
  return json(200, out);
}

/**
 * Name operations (POST with `op`): `transfer-code` { op, name, secret } -> { ok, code, expires_s } for a name this
 * secret owns; `adopt` { op, name, code, secret } -> { ok, name } adds this device's secret to the name.
 */
async function nameOp(req: Request, b: Record<string, unknown>, deps: HandlerDeps): Promise<Response> {
  const ip = clientIp(req);
  const name = normalizeName(b.name);
  const secret = b.secret;
  if (!name) return fail(422, 'rejected', [`name must be 1-${LIMITS.nameMax} printable characters`]);
  if (typeof secret !== 'string' || !SECRET_RE.test(secret)) return fail(422, 'rejected', ['device secret missing: reload the game']);
  const member = nameKey(name);
  if (b.op === 'transfer-code') {
    const rl = await deps.store.hit(`code:${ip}`, OWNER.windowS);
    if (rl.count > OWNER.codesPerIp) return fail(429, 'rate limited', ['too many transfer codes, try again in a few minutes'], { 'Retry-After': String(Math.max(1, rl.ttl)) });
    const code = await issueCode(deps.store, member, secret);
    if (code) return json(200, { ok: true, name, code, expires_s: OWNER.codeTtlS });
    if ((await ownership(deps.store, member, secret)) === 'free') return fail(404, 'not registered', [`"${name}" has no scores from this device yet: post a lap first`]);
    return fail(403, 'name taken', [`"${name}" belongs to another device`]);
  }
  if (b.op === 'adopt') {
    const rl = await deps.store.hit(`adopt:${ip}`, OWNER.windowS);
    if (rl.count > OWNER.adoptPerIp) return fail(429, 'rate limited', ['too many attempts, try again in a few minutes'], { 'Retry-After': String(Math.max(1, rl.ttl)) });
    // per IP + name (5, as per IP) and a per-name ceiling (100) that takes 20 addresses to reach: a lockout of a name's
    // transfers needs many IPs, and brute force stays bounded (100 guesses / 10 min over 31^6 codes that live 1 hour)
    const ipName = await deps.store.hit(`adoptname:${ip}:${member}`, OWNER.windowS);
    if (ipName.count > OWNER.adoptPerIp) return fail(429, 'rate limited', ['too many attempts for this name, try again in a few minutes'], { 'Retry-After': String(Math.max(1, ipName.ttl)) });
    const per = await deps.store.hit(`adoptname:${member}`, OWNER.windowS);
    if (per.count > OWNER.adoptPerName) return fail(429, 'rate limited', ['too many attempts for this name, try again later'], { 'Retry-After': String(Math.max(1, per.ttl)) });
    const code = normalizeCode(b.code);
    const r = code ? await adopt(deps.store, member, code, secret) : 'bad-code';
    if (r === 'ok') { deps.log?.(`name adopted: ${member}`); return json(200, { ok: true, name }); }
    return fail(r === 'not-registered' ? 404 : 403, r === 'not-registered' ? 'not registered' : 'wrong code', [r === 'not-registered' ? `"${name}" is not registered` : 'that code is wrong or expired: ask the other device for a new one']);
  }
  return fail(400, 'unknown op', ['op must be transfer-code or adopt']);
}

// ---- stale boards: hot-lap boards keyed by a physics version that is no longer current expire (LIMITS.staleBoardTtlS)
const lastSweep = new WeakMap<object, number>();
export async function sweepStaleBoards(deps: HandlerDeps): Promise<string[]> {
  const expired: string[] = [];
  for (const key of await deps.store.boards()) {
    const b = parseBoardKey(key);
    if (b?.mode === 'race') continue;   // race boards are hidden, not swept (their key carries the AI version)
    let stale = !b;
    if (b) { try { stale = b.physics !== (await deps.physics(b.track, b.car)); } catch { stale = false; } }
    if (stale) { await deps.store.expireBoard(key, LIMITS.staleBoardTtlS); await deps.store.expireKey(topKey(key), LIMITS.staleBoardTtlS); expired.push(key); }
  }
  if (expired.length) deps.log?.(`stale boards expire in ${LIMITS.staleBoardTtlS / 86400} d: ${expired.join(', ')}`);
  return expired;
}
async function maybeSweep(deps: HandlerDeps): Promise<void> {
  const now = (deps.now ?? Date.now)();
  const last = lastSweep.get(deps.store) ?? -Infinity;
  if (now - last < LIMITS.sweepEveryS * 1000) return;
  lastSweep.set(deps.store, now);
  try { await sweepStaleBoards(deps); } catch (e) { deps.log?.(`sweep failed: ${(e as Error).message}`); }
}

/** Entry point: GET (board / discovery), POST (submit), OPTIONS (same-origin preflight). */
export async function handleScores(req: Request, deps: HandlerDeps): Promise<Response> {
  const o = originAllowed(req, deps);
  const cors: Record<string, string> = o.ok && o.origin ? { 'Access-Control-Allow-Origin': o.origin, Vary: 'Origin' } : { Vary: 'Origin' };
  if (!o.ok) return fail(403, 'cross-origin requests are not allowed', undefined, cors);
  let res: Response;
  try {
    if (req.method === 'OPTIONS') {
      res = new Response(null, { status: 204, headers: { ...cors, 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600', 'Cache-Control': 'no-store' } });
      return res;
    }
    if (req.method === 'GET') res = await getBoard(req, deps);
    else if (req.method === 'POST') { res = await postScore(req, deps); await maybeSweep(deps); }
    else res = fail(405, 'method not allowed', undefined, { Allow: 'GET, POST, OPTIONS' });
  } catch (e) {
    deps.log?.(`error: ${(e as Error)?.stack ?? e}`);
    res = fail(500, 'internal error');
  }
  for (const [k, v] of Object.entries(cors)) res.headers.set(k, v);
  return res;
}
