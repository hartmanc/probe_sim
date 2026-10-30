// The race-recording endpoint (api/races.ts; docs/races.md). Web Request -> Response, storage injected, pure TS.
//   POST  a RaceRecording as JSON (Content-Type application/json) or gzipped JSON (application/gzip)  -> 204
//   GET   (fetch token only)  ?day=YYYY-MM-DD   -> the day's index;  ?id=<id>  -> one recording (the JSON as stored)
// The public can only post. A recording is data for tuning the AI: no name, no device id, no secret (racerec.ts).
import { LIMITS, TRACKS } from './config';
import { clientIp, originAllowed } from './http';
import { REC_MAX_BYTES, REC_MAX_JSON_BYTES, checkRecording, fromWire, gzipText, gunzipCapped, readBytesCapped, b64decode, b64encode, type RaceRecording } from './racerec';
import { sha256Hex } from './owner';
import type { ScoreStore } from './store';

export interface RaceRecDeps {
  store: ScoreStore;
  allowedOrigins?: string[];
  /** RACES_FETCH_TOKEN: the credential of the offline tool (header X-Fetch-Token); absent = GET is refused */
  fetchToken?: string;
  log?: (msg: string) => void;
  /** Clock (ms), tests. */
  now?: () => number;
}

export const RACES = {
  /** posts per IP per window: the scoreboard's rate limit */
  perIp: LIMITS.ratePosts,
  windowS: LIMITS.rateWindowS,
  /** fetch GETs per IP per window */
  getsPerIp: 240,
  /** a day's index keeps this many recordings; recordings and the index expire after this many days */
  keepPerDay: 5000,
  keepDays: 90,
} as const;

/** Index board of a day (not a scoreboard: the stale-board sweep skips the `rr:` prefix). */
export const dayBoard = (day: string): string => `rr:${day}`;
export const bodyKey = (id: string): string => `sb:rr:${id}`;
const ID_RE = /^\d{4}-\d{2}-\d{2}-[0-9a-f]{12}$/;
const DAY_RE = /^\d{4}-\d{2}-\d{2}$/;

/** What the day index keeps per recording (small: the index is read whole). */
export interface RecIndexMeta { at: string; track: string; seed: number; laps: number; ai: string; sha: string; bytes: number; steps: number; aborted?: true; truncated?: true }

const HEADERS: Record<string, string> = { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
const json = (status: number, body: unknown, extra: Record<string, string> = {}): Response =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...HEADERS, ...extra } });
const fail = (status: number, error: string, reasons?: string[], extra?: Record<string, string>): Response =>
  json(status, { ok: false, error, ...(reasons?.length ? { reasons } : {}) }, extra);

/** The token matches (hash compare: no early exit on the first differing character). */
async function hasFetchToken(req: Request, deps: RaceRecDeps): Promise<boolean> {
  const want = deps.fetchToken, got = req.headers.get('x-fetch-token');
  if (!want || want.length < 16 || !got || got.length > 256) return false;
  const [a, b] = await Promise.all([sha256Hex(`probe-sim/races/v1/${want}`), sha256Hex(`probe-sim/races/v1/${got}`)]);
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

const randomId = (day: string): string => `${day}-${[...crypto.getRandomValues(new Uint8Array(6))].map((b) => b.toString(16).padStart(2, '0')).join('')}`;

async function post(req: Request, deps: RaceRecDeps): Promise<Response> {
  const ct = (req.headers.get('content-type') ?? '').toLowerCase();
  const gz = ct.startsWith('application/gzip');
  if (!gz && !ct.startsWith('application/json')) return fail(415, 'content-type must be application/json or application/gzip');
  const len = Number(req.headers.get('content-length') ?? '0');
  if (len > REC_MAX_BYTES) return fail(413, 'payload too large', [`at most ${REC_MAX_BYTES} bytes after compression`]);
  // rate limit before any parsing
  const rl = await deps.store.hit(`rec:${clientIp(req)}`, RACES.windowS);
  if (rl.count > RACES.perIp) return fail(429, 'rate limited', [`at most ${RACES.perIp} recordings per ${RACES.windowS / 60} min`], { 'Retry-After': String(Math.max(1, rl.ttl)) });
  const bytes = await readBytesCapped(req.body, REC_MAX_BYTES);
  if (!bytes) return fail(413, 'payload too large', [`at most ${REC_MAX_BYTES} bytes after compression`]);
  const text = gz ? await gunzipCapped(bytes, REC_MAX_JSON_BYTES) : new TextDecoder().decode(bytes);
  if (text === null) return fail(400, 'body is not gzip, or unpacks past the size limit');
  let body: unknown;
  try { body = JSON.parse(text); } catch { return fail(400, 'body is not valid JSON'); }
  const rec = fromWire(body) as RaceRecording;   // the wire form carries the rows as deltas (racerec.ts toWire)
  const reasons = checkRecording(rec);
  if (!reasons.length && !Object.hasOwn(TRACKS, rec.trackId)) reasons.push('trackId is not a known track');
  if (reasons.length) return fail(422, 'recording rejected', reasons.slice(0, 8));
  const now = (deps.now ?? Date.now)(), at = new Date(now).toISOString(), day = at.slice(0, 10), id = randomId(day);
  // stored gzipped (base64) whatever the client sent: a recording is a few hundred KB at most, Upstash's request limit is not generous
  const z = gz ? bytes : await gzipText(text);
  if (!z) return fail(503, 'cannot store: no compression in this runtime');
  const meta: RecIndexMeta = { at, track: rec.trackId, seed: rec.seed, laps: rec.laps, ai: rec.aiVersion, sha: rec.buildSha, bytes: z.byteLength, steps: rec.inputs.steps,
    ...(rec.aborted ? { aborted: true as const } : {}), ...(rec.truncated ? { truncated: true as const } : {}) };
  const ttl = RACES.keepDays * 86400;
  await deps.store.kvSet(bodyKey(id), b64encode(z), { ex: ttl });
  await deps.store.submit(dayBoard(day), id, now, true, JSON.stringify(meta), RACES.keepPerDay);
  await deps.store.expireBoard(dayBoard(day), ttl);
  deps.log?.(`recorded ${id} ${rec.trackId} seed ${rec.seed} ${z.byteLength} B`);
  return new Response(null, { status: 204, headers: HEADERS });
}

async function get(req: Request, deps: RaceRecDeps): Promise<Response> {
  if (!(await hasFetchToken(req, deps))) return fail(403, 'forbidden');
  const rl = await deps.store.hit(`recget:${clientIp(req)}`, RACES.windowS);
  if (rl.count > RACES.getsPerIp) return fail(429, 'rate limited', undefined, { 'Retry-After': String(Math.max(1, rl.ttl)) });
  const u = new URL(req.url), id = u.searchParams.get('id');
  if (id !== null) {
    if (!ID_RE.test(id)) return fail(400, 'bad id');
    const raw = await deps.store.kvGet(bodyKey(id));
    if (!raw) return fail(404, 'no such recording');
    const text = await gunzipCapped(b64decode(raw), REC_MAX_JSON_BYTES);
    if (text === null) return fail(500, 'the stored recording is unreadable');
    return new Response(text, { status: 200, headers: { 'Content-Type': 'application/json; charset=utf-8', ...HEADERS } });
  }
  const day = u.searchParams.get('day') ?? new Date((deps.now ?? Date.now)()).toISOString().slice(0, 10);
  if (!DAY_RE.test(day)) return fail(400, 'bad day', ['day must look like 2026-10-30']);
  const limit = Math.max(1, Math.min(RACES.keepPerDay, Number(u.searchParams.get('limit') ?? '1000') || 1000));
  const rows = await deps.store.top(dayBoard(day), limit, true);
  const recordings = rows.map((r) => { let m: Partial<RecIndexMeta> = {}; try { m = r.meta ? JSON.parse(r.meta) as RecIndexMeta : {}; } catch { m = {}; } return { id: r.member, ...m }; });
  return json(200, { ok: true, day, count: recordings.length, recordings });
}

/** Entry point: POST (record), GET (fetch token), OPTIONS (same-origin preflight). */
export async function handleRaces(req: Request, deps: RaceRecDeps): Promise<Response> {
  const o = originAllowed(req, deps);
  const cors: Record<string, string> = o.ok && o.origin ? { 'Access-Control-Allow-Origin': o.origin, Vary: 'Origin' } : { Vary: 'Origin' };
  if (!o.ok) return fail(403, 'cross-origin requests are not allowed', undefined, cors);
  let res: Response;
  try {
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: { ...cors, ...HEADERS, 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600' } });
    if (req.method === 'POST') res = await post(req, deps);
    else if (req.method === 'GET') res = await get(req, deps);
    else res = fail(405, 'method not allowed', undefined, { Allow: 'GET, POST, OPTIONS' });
  } catch (e) {
    deps.log?.(`error: ${(e as Error)?.stack ?? e}`);
    res = fail(500, 'internal error');
  }
  for (const [k, v] of Object.entries(cors)) res.headers.set(k, v);
  return res;
}
