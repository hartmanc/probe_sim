// The scoreboard HTTP handler (Web Request -> Response), used by api/scores.ts and tested directly.
// Pure TS: storage and asset loading are injected.
import { CARS, LIMITS, TRACKS } from './config';
import { verifyHotlap } from './replay';
import type { SimAssets } from './sim';
import type { ScoreStore } from './store';
import type { ApiError, Board, HotlapSubmission, InputType, RaceSubmission, Score, SubmitResult } from './types';
import { boardKey, lowerIsBetter, nameKey, normalizeName, parseBoardKey, validateSubmission } from './validate';

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
}

interface Meta { name: string; input: InputType; at: string; ai_version?: string; laps?: number; device?: string; replayed?: number; claimed?: number }

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

/** Same-origin check: no Origin header (curl, same-origin GET) passes; otherwise its host must be ours or allowed. */
function originAllowed(req: Request, deps: HandlerDeps): { ok: boolean; origin: string | null } {
  const origin = req.headers.get('origin');
  if (!origin) return { ok: true, origin: null };
  if (deps.allowedOrigins?.includes(origin)) return { ok: true, origin };
  const host = req.headers.get('x-forwarded-host') ?? req.headers.get('host') ?? new URL(req.url).host;
  try { return { ok: new URL(origin).host === host, origin }; } catch { return { ok: false, origin }; }
}

function clientIp(req: Request): string {
  const xff = req.headers.get('x-forwarded-for');
  const ip = (xff ? xff.split(',')[0] : req.headers.get('x-real-ip')) ?? 'unknown';
  return ip.trim().slice(0, 64) || 'unknown';
}

function toScore(rank: number, score: number, meta: string | null, member: string): Score {
  let m: Partial<Meta> = {};
  try { m = meta ? (JSON.parse(meta) as Meta) : {}; } catch { m = {}; }
  const s: Score = { rank, name: m.name ?? member, score, input: m.input ?? 'keys', at: m.at ?? '' };
  if (m.ai_version !== undefined) s.ai_version = m.ai_version;
  if (m.laps !== undefined) s.laps = m.laps;
  return s;
}

async function getBoard(req: Request, deps: HandlerDeps): Promise<Response> {
  const u = new URL(req.url);
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

  const physicsCache = new Map<string, string>();
  const b0 = body as { track?: unknown; car?: unknown };
  if (typeof b0?.track === 'string' && typeof b0?.car === 'string' && b0.track in TRACKS && b0.car in CARS) {
    try { physicsCache.set(`${b0.track}/${b0.car}`, await deps.physics(b0.track, b0.car)); } catch (e) {
      deps.log?.(`assets unavailable: ${(e as Error).message}`);
      return fail(503, 'server assets unavailable');
    }
  }
  const v = validateSubmission(body, (t, c) => physicsCache.get(`${t}/${c}`));
  if (!v.ok || !v.value) return fail(422, 'rejected', v.reasons);
  const sub = v.value;
  const name = sub.name;
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
    score = Math.round(s.metres * 100) / 100;
    key = boardKey('race', s.track, s.car, s.physics, s.ai_version);
    meta = { name, input: s.input, at, ai_version: s.ai_version, laps: s.laps, ...(s.device ? { device: s.device } : {}) };
  }
  const asc = lowerIsBetter(sub.mode);
  const member = nameKey(name);
  const res = await deps.store.submit(key, member, score, asc, JSON.stringify(meta), LIMITS.keep);
  const rk = await deps.store.rank(key, member, asc);
  const out: SubmitResult = { ok: true, board: key, rank: rk === null ? null : rk + 1, best: res.best, improved: res.improved };
  if (replayed !== undefined) out.replayed = replayed;
  return json(200, out);
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
    else if (req.method === 'POST') res = await postScore(req, deps);
    else res = fail(405, 'method not allowed', undefined, { Allow: 'GET, POST, OPTIONS' });
  } catch (e) {
    deps.log?.(`error: ${(e as Error)?.stack ?? e}`);
    res = fail(500, 'internal error');
  }
  for (const [k, v] of Object.entries(cors)) res.headers.set(k, v);
  return res;
}
