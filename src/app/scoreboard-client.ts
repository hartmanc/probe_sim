// Scoreboard client (docs/scoreboard.md §3): the HTTP calls, the device's name / id / personal bests in
// localStorage, building submissions, deciding whether a lap may be submitted, and the board context the
// hot-lap and (future) race modes submit through. No DOM besides localStorage / location / fetch, all guarded,
// so it is unit-tested in node.
import { raceScoreView } from '../scoreboard/validate';
import {
  LIMITS, boardKey, lowerIsBetter, normalizeName,
  type ApiError, type Board, type HotlapSubmission, type InputTrace, type InputType, type Mode, type RaceSubmission,
  type Submission, type SubmitResult,
} from '../scoreboard';
import type { Lap } from './timing';

export const LS_NAME = 'probe-sim.scoreboard.name';
export const LS_DEVICE = 'probe-sim.scoreboard.device';
export const lsPbKey = (board: string): string => `probe-sim.scoreboard.pb.${board}`;

/** localStorage-like; every access is wrapped (private windows throw). */
export interface KV { getItem(k: string): string | null; setItem(k: string, v: string): void }
type FetchFn = (input: string, init?: RequestInit) => Promise<Response>;

function defaultStorage(): KV | null {
  try { return typeof localStorage === 'undefined' ? null : localStorage; } catch { return null; }
}

/** API endpoint: same-origin /api/scores, or `?api=<base>` (e.g. http://localhost:3000) for local testing. */
export function apiBase(search: string = typeof location === 'undefined' ? '' : location.search): string {
  const p = new URLSearchParams(search).get('api');
  if (p && /^https?:\/\/[^\s]+$/i.test(p)) {
    const b = p.replace(/\/+$/, '');
    return /\/api\/scores$/.test(b) ? b : `${b}/api/scores`;
  }
  return '/api/scores';
}

export type ApiResult<T> =
  | { ok: true; value: T }
  /** Network failure, timeout or a non-JSON answer (no API behind this origin). */
  | { ok: false; offline: true; error: string; status?: number; reasons?: undefined }
  | { ok: false; offline: false; status: number; error: string; reasons: string[] };

export interface ServerInfo { store: string; boards: Record<string, string> }

export class ScoreboardClient {
  /** null: never asked; true after a failed request; false after a good one. */
  offline: boolean | null = null;
  readonly base: string;
  private fetchFn: FetchFn;
  private kv: KV | null;

  constructor(opts: { base?: string; fetch?: FetchFn; storage?: KV | null } = {}) {
    this.base = opts.base ?? apiBase();
    this.fetchFn = opts.fetch ?? ((u, i) => fetch(u, i));
    this.kv = opts.storage === undefined ? defaultStorage() : opts.storage;
  }

  // ------------------------------------------------------------ storage

  private get(k: string): string | null { try { return this.kv?.getItem(k) ?? null; } catch { return null; } }
  private set(k: string, v: string): void { try { this.kv?.setItem(k, v); } catch { /* private window */ } }

  /** The remembered display name (normalised), or null. */
  get name(): string | null { return normalizeName(this.get(LS_NAME)); }
  /** Store a name; returns the normalised name or null if invalid (nothing stored). */
  setName(raw: string): string | null {
    const n = normalizeName(raw);
    if (n) this.set(LS_NAME, n);
    return n;
  }

  /** Random per-browser id, made once (moderation only, never shown). */
  get device(): string | undefined {
    const cur = this.get(LS_DEVICE);
    if (cur && /^[A-Za-z0-9-]{1,64}$/.test(cur)) return cur;
    let id: string;
    try { id = crypto.randomUUID(); } catch { id = Array.from({ length: 4 }, () => Math.random().toString(36).slice(2, 10)).join('-'); }
    this.set(LS_DEVICE, id);
    return this.get(LS_DEVICE) === id ? id : undefined;
  }

  /** This device's personal best on a board (lap time s or metres), or null. */
  pb(board: string): number | null {
    const v = Number(this.get(lsPbKey(board)));
    return this.get(lsPbKey(board)) !== null && Number.isFinite(v) && v > 0 ? v : null;
  }
  /** Keep the better of the stored PB and `score`. */
  savePb(board: string, mode: Mode, score: number): void {
    const cur = this.pb(board);
    if (cur === null || isBetter(mode, score, cur)) this.set(lsPbKey(board), String(score));
  }

  // ------------------------------------------------------------ HTTP

  private async call<T>(url: string, init: RequestInit, timeoutMs: number): Promise<ApiResult<T>> {
    const ac = typeof AbortController !== 'undefined' ? new AbortController() : null;
    const timer = ac ? setTimeout(() => ac.abort(), timeoutMs) : null;
    try {
      const r = await this.fetchFn(url, { ...init, signal: ac?.signal, cache: 'no-store' });
      const ct = r.headers.get('content-type') ?? '';
      if (!ct.includes('json')) { this.offline = true; return { ok: false, offline: true, error: `no scoreboard API (${r.status})`, status: r.status }; }
      const body = (await r.json()) as (T & { ok: true }) | ApiError;
      this.offline = false;
      if (r.ok && body && (body as { ok?: unknown }).ok === true) return { ok: true, value: body as T };
      const e = body as ApiError;
      return { ok: false, offline: false, status: r.status, error: e?.error ?? `HTTP ${r.status}`, reasons: Array.isArray(e?.reasons) ? e.reasons : [] };
    } catch (e) {
      this.offline = true;
      return { ok: false, offline: true, error: (e as Error)?.name === 'AbortError' ? 'timed out' : String((e as Error)?.message ?? e) };
    } finally {
      if (timer) clearTimeout(timer);
    }
  }

  /** GET /api/scores: the server's current boards (and whether it is reachable at all). */
  info(): Promise<ApiResult<ServerInfo>> { return this.call<ServerInfo>(this.base, { method: 'GET' }, 8000); }

  /** GET the top 10 of a board, plus `you` for the stored (or given) name. */
  board(key: string, name: string | null = this.name): Promise<ApiResult<Board>> {
    const q = new URLSearchParams({ board: key });
    if (name) q.set('name', name);
    return this.call<Board>(`${this.base}?${q}`, { method: 'GET' }, 8000);
  }

  /** POST a submission; on ok the PB for its board is updated. */
  async submit(sub: Submission): Promise<ApiResult<SubmitResult>> {
    const r = await this.call<SubmitResult>(this.base, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sub),
    }, 30000);
    if (r.ok) {
      const score = sub.mode === 'hotlap' ? (r.value.replayed ?? sub.time) : sub.metres;
      this.savePb(r.value.board, sub.mode, score);
    }
    return r;
  }
}

/** Is `a` a better score than `b` on a board of this mode? */
export const isBetter = (mode: Mode, a: number, b: number): boolean => (lowerIsBetter(mode) ? a < b : a > b);

/** One-line description of a failed call, for a toast. */
export function describeFailure(r: Exclude<ApiResult<unknown>, { ok: true }>): string {
  if (r.offline) return 'Scoreboard offline';
  if (r.status === 429) return 'Scoreboard: too many submissions, try again in a few minutes';
  if (r.reasons.some((x) => /physics version mismatch/.test(x))) return 'Scoreboard: the game was updated — reload the page to submit';
  return `Scoreboard rejected it: ${r.reasons.length ? r.reasons.join('; ') : r.error}`;
}

// ---------------------------------------------------------------- hot lap

export interface HotlapCheck {
  /** Better than this device's PB for the board (and not already offered this session). */
  best: boolean;
  /** Can be posted; when false, `reason` says why (for the player). */
  submittable: boolean;
  reason?: string;
}

/**
 * Should this lap be offered to the scoreboard? `pb` = the device's stored PB, `offered` = the best time already
 * offered this session (skipped or submitted), `steps` / `rows` = the trace size at the lap's step.
 */
export function checkHotlap(lap: Lap, o: { pb: number | null; offered: number | null; steps: number; rows: number; assetsOk: boolean }): HotlapCheck {
  const bar = [o.pb, o.offered].filter((x): x is number => x !== null);
  const best = lap.valid && bar.every((b) => lap.time < b);
  let reason: string | undefined;
  if (!lap.valid) reason = 'off track for more than 2 s';
  else if (!o.assetsOk) reason = 'stand-in assets are loaded (reload the page)';
  else if (lap.n > LIMITS.maxLap) reason = `only laps 1–${LIMITS.maxLap} after a reset count — press reset to post again`;
  else if (o.steps > LIMITS.maxTraceSteps || o.rows > LIMITS.maxTraceRows) reason = 'too long since the reset — press reset to post again';
  else if (!(lap.time > LIMITS.lapMin && lap.time < LIMITS.lapMax)) reason = `lap times must be ${LIMITS.lapMin}–${LIMITS.lapMax} s`;
  return { best, submittable: reason === undefined, reason };
}

export function buildHotlapSubmission(a: { lap: Lap; trace: InputTrace; name: string; input: InputType; device?: string }): HotlapSubmission {
  const t = a.trace;
  return {
    mode: 'hotlap', track: t.track, car: t.car, physics: t.physics, name: a.name, input: a.input,
    ...(a.device ? { device: a.device } : {}),
    time: a.lap.time, lap: a.lap.n, valid: a.lap.valid, trace: t,
  };
}

// ---------------------------------------------------------------- board context + race hook

/** A score the player may post: shown by the UI's new-best prompt, then built and POSTed. */
export interface Candidate {
  mode: Mode;
  board: string;
  score: number;
  /** "Lap 3" / "Race · 7 laps" */
  detail: string;
  build(name: string): Submission;
}

export type SubmitOutcome =
  | { status: 'submitted'; result: SubmitResult }
  | { status: 'skipped' | 'not-best' | 'unavailable' }
  | { status: 'failed'; message: string };

export interface BoardContext {
  client: ScoreboardClient;
  track: string;
  car: string;
  /** physicsVersion() of the loaded car + track (HotlapSim.physics). */
  physics: string;
  /** Input type in use (input.inputTag). */
  input(): InputType;
  /** False when stand-in assets are loaded (submissions would fail the physics check or the replay). */
  assetsOk: boolean;
  /** Race AI version (src/physics/ai) once the race mode exists: enables the Race board. */
  raceAiVersion?: string;
  /** The UI's new-best prompt (scoreboard-ui.ts); without it candidates are submitted directly if a name is stored. */
  offer?(c: Candidate): Promise<SubmitOutcome>;
}

let ctx: BoardContext | null = null;

/** Set / patch the board context (index.ts after loading; the race mode adds `raceAiVersion`). */
export function setBoardContext(patch: Partial<BoardContext>): void {
  ctx = { ...(ctx ?? {}), ...patch } as BoardContext;
}
export const boardContext = (): BoardContext | null => ctx;

export function hotlapBoard(c: BoardContext | null = ctx): string | null {
  return c ? boardKey('hotlap', c.track, c.car, c.physics) : null;
}
export function raceBoard(c: BoardContext | null = ctx): string | null {
  return c?.raceAiVersion ? boardKey('race', c.track, c.car, c.physics, c.raceAiVersion) : null;
}

/** What the race mode reports at the end of a race (docs §2 race submission). */
export interface RaceResult {
  /** Distance covered, m (the score). */
  metres: number;
  /** Laps completed, 0..LIMITS.raceLaps. */
  laps: number;
  /** Race time, s from the green to the last-lap crossing (finishers only; the score). */
  time?: number;
  /** Race AI version; part of the board key. Defaults to the context's raceAiVersion. */
  aiVersion?: string;
  /** Field seed (stored in the reserved `replay` field; ignored by the server today). */
  seed?: number | string;
  position?: number;
  finished?: boolean;
  /** Input type override (default: the most recent device, input.inputTag). */
  input?: InputType;
}

/**
 * For the race mode: offer the race result to the scoreboard. If it beats this device's PB on the race board,
 * the UI shows the new-best prompt (name, Submit / Skip) and POSTs it. Never throws; never blocks driving.
 */
export async function submitRace(result: RaceResult): Promise<SubmitOutcome> {
  const c = ctx;
  const ai = result.aiVersion ?? c?.raceAiVersion;
  if (!c || !ai || !c.assetsOk) return { status: 'unavailable' };
  if (!c.raceAiVersion) setBoardContext({ raceAiVersion: ai });
  const board = boardKey('race', c.track, c.car, c.physics, ai);
  const pb = c.client.pb(board);
  if (!(result.metres > 0) || (pb !== null && !isBetter('race', result.metres, pb))) return { status: 'not-best' };
  const input = result.input ?? c.input();
  const cand: Candidate = {
    mode: 'race', board, score: result.metres,
    detail: `Race · ${result.laps} lap${result.laps === 1 ? '' : 's'}${result.position ? ` · P${result.position}` : ''}`,
    build: (name): RaceSubmission => ({
      mode: 'race', track: c.track, car: c.car, physics: c.physics, ai_version: ai, name, input,
      ...(c.client.device ? { device: c.client.device } : {}),
      metres: result.metres, laps: result.laps,
      ...(result.position !== undefined ? { position: result.position } : {}),
      ...(result.finished !== undefined ? { finished: result.finished } : {}),
      ...(result.seed !== undefined ? { replay: { seed: result.seed } } : {}),
    }),
  };
  return offerCandidate(cand);
}

/** Through the UI prompt when there is one, else directly with the stored name. */
export async function offerCandidate(cand: Candidate): Promise<SubmitOutcome> {
  const c = ctx;
  if (!c) return { status: 'unavailable' };
  if (c.offer) return c.offer(cand);
  const name = c.client.name;
  if (!name) return { status: 'skipped' };
  return postCandidate(c.client, cand, name);
}

export async function postCandidate(client: ScoreboardClient, cand: Candidate, name: string): Promise<SubmitOutcome> {
  const r = await client.submit(cand.build(name));
  return r.ok ? { status: 'submitted', result: r.value } : { status: 'failed', message: describeFailure(r) };
}

// ---------------------------------------------------------------- formatting

export function fmtLapTime(t: number): string {
  const m = Math.floor(t / 60);
  return `${m}:${(t - m * 60).toFixed(3).padStart(6, '0')}`;
}

/** Race score: laps + distance into the next lap. */
export function fmtMetres(metres: number, laps: number | undefined, trackLength: number): string {
  if (laps === undefined || !(trackLength > 0)) return `${Math.round(metres).toLocaleString('en-US')} m`;
  const rest = Math.max(0, metres - laps * trackLength);
  return `${laps}L +${Math.round(rest).toLocaleString('en-US')} m`;
}

export const fmtScore = (mode: Mode, score: number, laps?: number, trackLength = 0): string => {
  if (mode === 'hotlap') return fmtLapTime(score);
  const v = raceScoreView(score, trackLength);
  return 'time' in v ? `${laps ?? LIMITS.raceLaps}L ${fmtLapTime(v.time)}` : fmtMetres(v.metres, laps, trackLength);
};
