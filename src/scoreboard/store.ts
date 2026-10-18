// Score storage: Redis sorted sets (Upstash REST) in production, an in-memory twin for local dev / tests.
// Pure TS (uses global fetch only).
import { LIMITS } from './config';

export interface Member { member: string; score: number }

/** The subset of Redis the scoreboard needs. Boards are sorted sets; per-entry details live in a hash. */
export interface ScoreStore {
  readonly kind: 'memory' | 'upstash';
  /**
   * Insert or improve `member` with `score`, keeping the better of old and new (lower if `asc`), store
   * `meta` when improved, then trim the board to `keep` entries. Returns whether it improved and the stored score.
   */
  submit(board: string, member: string, score: number, asc: boolean, meta: string, keep?: number): Promise<{ improved: boolean; best: number }>;
  /** Best `n` entries in board order with their meta (JSON strings). */
  top(board: string, n: number, asc: boolean): Promise<(Member & { meta: string | null })[]>;
  /** 0-based rank of member, or null. */
  rank(board: string, member: string, asc: boolean): Promise<number | null>;
  score(board: string, member: string): Promise<number | null>;
  meta(board: string, member: string): Promise<string | null>;
  /** Fixed-window counter: increments `key`, starting a `windowS` expiry on the first hit. Returns count and seconds left. */
  hit(key: string, windowS: number): Promise<{ count: number; ttl: number }>;
}

const zkey = (b: string) => `sb:z:${b}`;
const hkey = (b: string) => `sb:h:${b}`;

// ------------------------------------------------------------------ in-memory
export class MemoryStore implements ScoreStore {
  readonly kind = 'memory' as const;
  private z = new Map<string, Map<string, number>>();
  private h = new Map<string, Map<string, string>>();
  private c = new Map<string, { n: number; until: number }>();
  constructor(private readonly now: () => number = () => Date.now()) {}

  private sorted(board: string, asc: boolean): Member[] {
    const m = this.z.get(zkey(board));
    if (!m) return [];
    // Redis order: by score, ties by member (lexicographic); REV reverses both
    const a = [...m].map(([member, score]) => ({ member, score }));
    a.sort((x, y) => x.score - y.score || (x.member < y.member ? -1 : x.member > y.member ? 1 : 0));
    return asc ? a : a.reverse();
  }

  async submit(board: string, member: string, score: number, asc: boolean, meta: string, keep: number = LIMITS.keep) {
    let m = this.z.get(zkey(board));
    if (!m) { m = new Map(); this.z.set(zkey(board), m); }
    let h = this.h.get(hkey(board));
    if (!h) { h = new Map(); this.h.set(hkey(board), h); }
    const old = m.get(member);
    const improved = old === undefined || (asc ? score < old : score > old);
    if (improved) { m.set(member, score); h.set(member, meta); }
    const all = this.sorted(board, asc);
    for (const e of all.slice(keep)) { m.delete(e.member); h.delete(e.member); }
    return { improved, best: improved ? score : old! };
  }
  async top(board: string, n: number, asc: boolean) {
    const h = this.h.get(hkey(board));
    return this.sorted(board, asc).slice(0, n).map((e) => ({ ...e, meta: h?.get(e.member) ?? null }));
  }
  async rank(board: string, member: string, asc: boolean) {
    const i = this.sorted(board, asc).findIndex((e) => e.member === member);
    return i < 0 ? null : i;
  }
  async score(board: string, member: string) { return this.z.get(zkey(board))?.get(member) ?? null; }
  async meta(board: string, member: string) { return this.h.get(hkey(board))?.get(member) ?? null; }
  async hit(key: string, windowS: number) {
    const t = this.now();
    let e = this.c.get(key);
    if (!e || e.until <= t) { e = { n: 0, until: t + windowS * 1000 }; this.c.set(key, e); }
    e.n++;
    return { count: e.n, ttl: Math.ceil((e.until - t) / 1000) };
  }
}

// ------------------------------------------------------------------ Upstash REST
type Cmd = (string | number)[];
type FetchLike = (url: string, init: { method: string; headers: Record<string, string>; body: string }) => Promise<{ ok: boolean; status: number; json(): Promise<unknown> }>;

/** Upstash Redis over its REST API (POST /pipeline with a JSON array of commands). No SDK needed. */
export class UpstashStore implements ScoreStore {
  readonly kind = 'upstash' as const;
  constructor(private readonly url: string, private readonly token: string, private readonly fetchFn: FetchLike = fetch as unknown as FetchLike) {}

  private async pipe(cmds: Cmd[]): Promise<unknown[]> {
    const res = await this.fetchFn(this.url.replace(/\/+$/, '') + '/pipeline', {
      method: 'POST',
      headers: { Authorization: `Bearer ${this.token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(cmds.map((c) => c.map(String))),
    });
    if (!res.ok) throw new Error(`redis http ${res.status}`);
    const out = (await res.json()) as { result?: unknown; error?: string }[];
    return out.map((o) => { if (o.error) throw new Error(`redis: ${o.error}`); return o.result; });
  }

  async submit(board: string, member: string, score: number, asc: boolean, meta: string, keep: number = LIMITS.keep) {
    const z = zkey(board), h = hkey(board);
    // ZADD LT/GT CH: only an improvement (or a new member) counts as changed
    const [changed, cur] = await this.pipe([['ZADD', z, asc ? 'LT' : 'GT', 'CH', score, member], ['ZSCORE', z, member]]);
    const improved = Number(changed) > 0;
    const cmds: Cmd[] = [];
    if (improved) cmds.push(['HSET', h, member, meta]);
    // trim: members past `keep` in board order
    cmds.push(asc ? ['ZRANGE', z, keep, -1] : ['ZRANGE', z, 0, -(keep + 1)]);
    const res = await this.pipe(cmds);
    const drop = (res[res.length - 1] as string[] | null) ?? [];
    if (drop.length) await this.pipe([['ZREM', z, ...drop], ['HDEL', h, ...drop]]);
    return { improved, best: Number(cur) };
  }
  async top(board: string, n: number, asc: boolean) {
    const [flat] = await this.pipe([asc ? ['ZRANGE', zkey(board), 0, n - 1, 'WITHSCORES'] : ['ZRANGE', zkey(board), 0, n - 1, 'REV', 'WITHSCORES']]);
    const f = (flat as string[]) ?? [];
    const rows: Member[] = [];
    for (let i = 0; i + 1 < f.length; i += 2) rows.push({ member: f[i], score: Number(f[i + 1]) });
    if (!rows.length) return [];
    const [metas] = await this.pipe([['HMGET', hkey(board), ...rows.map((r) => r.member)]]);
    return rows.map((r, i) => ({ ...r, meta: ((metas as (string | null)[]) ?? [])[i] ?? null }));
  }
  async rank(board: string, member: string, asc: boolean) {
    const [r] = await this.pipe([[asc ? 'ZRANK' : 'ZREVRANK', zkey(board), member]]);
    return r === null || r === undefined ? null : Number(r);
  }
  async score(board: string, member: string) {
    const [r] = await this.pipe([['ZSCORE', zkey(board), member]]);
    return r === null || r === undefined ? null : Number(r);
  }
  async meta(board: string, member: string) {
    const [r] = await this.pipe([['HGET', hkey(board), member]]);
    return (r as string | null) ?? null;
  }
  async hit(key: string, windowS: number) {
    const k = `sb:rl:${key}`;
    const [n, ttl] = await this.pipe([['INCR', k], ['TTL', k]]);
    let t = Number(ttl);
    if (t < 0) { await this.pipe([['EXPIRE', k, windowS]]); t = windowS; }
    return { count: Number(n), ttl: t };
  }
}

/**
 * Pick the store from the environment, by presence: UPSTASH_REDIS_REST_URL/TOKEN, else KV_REST_API_URL/TOKEN
 * (the names the Vercel Marketplace Upstash integration injects), else in-memory.
 */
export function storeFromEnv(env: Record<string, string | undefined>, fetchFn?: FetchLike): ScoreStore {
  const url = env.UPSTASH_REDIS_REST_URL || env.KV_REST_API_URL;
  const token = env.UPSTASH_REDIS_REST_URL ? env.UPSTASH_REDIS_REST_TOKEN : env.KV_REST_API_TOKEN;
  if (url && token) return new UpstashStore(url, token, fetchFn);
  return new MemoryStore();
}
