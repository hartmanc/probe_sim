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
  /** Plain string keys (name ownership, transfer codes): get, set (nx = only if absent, ex = expiry s; false when nx
   *  refused), delete. Keys are used as given (callers prefix them, `sb:own:`, `sb:xfer:`). */
  kvGet(key: string): Promise<string | null>;
  kvSet(key: string, value: string, opts?: { nx?: boolean; ex?: number }): Promise<boolean>;
  kvDel(key: string): Promise<void>;
  /**
   * Name ownership, atomic (owner.ts). The owner record is a string "v1|<iso date>|<hash>,<hash>,…" at `ownerKey`;
   * the transfer code's hash sits at `xferKey`. Each call is ONE Redis operation (a Lua script under EVAL on Upstash; a
   * synchronous step on the memory store), so concurrent adoptions, a code issued meanwhile or a manual release
   * cannot interleave with it.
   * issueTransfer: when `deviceHash` is in the record, store `codeHash` (replacing any earlier code) for `ttlS`.
   * adoptTransfer: when `codeHash` is the current code, consume it; then, when the record exists, add `deviceHash`
   * (moved to the end if present; the oldest dropped past `maxDevices`).
   */
  issueTransfer(ownerKey: string, xferKey: string, deviceHash: string, codeHash: string, ttlS: number): Promise<'ok' | 'free' | 'other'>;
  adoptTransfer(ownerKey: string, xferKey: string, codeHash: string, deviceHash: string, maxDevices: number): Promise<'ok' | 'bad-code' | 'not-registered'>;
  /** Every board that has entries (board keys, without the `sb:z:` prefix). */
  boards(): Promise<string[]>;
  /** Give a board (its sorted set and hash) an expiry of `seconds` unless it already has one. */
  expireBoard(board: string, seconds: number): Promise<void>;
  /** Give a plain string key an expiry of `seconds` unless it already has one (the #1 ghost trace of a stale board). */
  expireKey(key: string, seconds: number): Promise<void>;
}

const zkey = (b: string) => `sb:z:${b}`;

// ------------------------------------------------------------------ owner records ("v1|<at>|<h>,<h>,…")
export function encodeOwner(at: string, hashes: string[]): string { return `v1|${at}|${hashes.join(',')}`; }
export function decodeOwner(raw: string | null): { at: string; h: string[] } | null {
  if (!raw || !raw.startsWith('v1|')) return null;
  const i = raw.indexOf('|', 3);
  if (i < 0) return null;
  return { at: raw.slice(3, i), h: raw.slice(i + 1).split(',').filter(Boolean) };
}
/** The Lua twins of the memory store's issueTransfer / adoptTransfer (KEYS[1] owner, KEYS[2] xfer). */
export const LUA_ISSUE = `local rec = redis.call('GET', KEYS[1])
if not rec then return 'free' end
local i = string.find(rec, '|', 4, true)
if not i then return 'other' end
local list = ',' .. string.sub(rec, i + 1) .. ','
if not string.find(list, ',' .. ARGV[1] .. ',', 1, true) then return 'other' end
redis.call('SET', KEYS[2], ARGV[2], 'EX', tonumber(ARGV[3]))
return 'ok'`;
export const LUA_ADOPT = `local want = redis.call('GET', KEYS[2])
if (not want) or want ~= ARGV[1] then return 'bad-code' end
redis.call('DEL', KEYS[2])
local rec = redis.call('GET', KEYS[1])
if not rec then return 'not-registered' end
local i = string.find(rec, '|', 4, true)
if not i then return 'not-registered' end
local out = {}
for h in string.gmatch(string.sub(rec, i + 1), '[^,]+') do if h ~= ARGV[2] then table.insert(out, h) end end
table.insert(out, ARGV[2])
local max = tonumber(ARGV[3])
while #out > max do table.remove(out, 1) end
redis.call('SET', KEYS[1], string.sub(rec, 1, i) .. table.concat(out, ','))
return 'ok'`;
const hkey = (b: string) => `sb:h:${b}`;

// ------------------------------------------------------------------ in-memory
export class MemoryStore implements ScoreStore {
  readonly kind = 'memory' as const;
  private z = new Map<string, Map<string, number>>();
  private h = new Map<string, Map<string, string>>();
  private c = new Map<string, { n: number; until: number }>();
  private kv = new Map<string, { v: string; until: number }>();
  /** board -> expiry time (ms); a board past it is gone, as in Redis */
  private exp = new Map<string, number>();
  constructor(private readonly now: () => number = () => Date.now()) {}

  private alive(board: string): void {
    const t = this.exp.get(board);
    if (t !== undefined && t <= this.now()) { this.z.delete(zkey(board)); this.h.delete(hkey(board)); this.exp.delete(board); }
  }
  async kvGet(key: string) {
    const e = this.kv.get(key);
    if (!e) return null;
    if (e.until <= this.now()) { this.kv.delete(key); return null; }
    return e.v;
  }
  async kvSet(key: string, value: string, opts: { nx?: boolean; ex?: number } = {}) {
    if (opts.nx && (await this.kvGet(key)) !== null) return false;
    this.kv.set(key, { v: value, until: opts.ex ? this.now() + opts.ex * 1000 : Infinity });
    return true;
  }
  async kvDel(key: string) { this.kv.delete(key); }
  async boards() {
    const out: string[] = [];
    for (const k of [...this.z.keys()]) { const b = k.slice(5); this.alive(b); if (this.z.has(k)) out.push(b); }
    return out;
  }
  async expireBoard(board: string, seconds: number) {
    if (this.z.has(zkey(board)) && !this.exp.has(board)) this.exp.set(board, this.now() + seconds * 1000);
  }
  async expireKey(key: string, seconds: number) {
    const e = this.kv.get(key);
    if (e && e.until === Infinity) e.until = this.now() + seconds * 1000;
  }
  // no await inside: each runs as one uninterrupted step, like the Lua scripts
  async issueTransfer(ownerKey: string, xferKey: string, deviceHash: string, codeHash: string, ttlS: number) {
    const rec = decodeOwner(this.kvGetSync(ownerKey));
    if (!rec) return 'free' as const;
    if (!rec.h.includes(deviceHash)) return 'other' as const;
    this.kv.set(xferKey, { v: codeHash, until: this.now() + ttlS * 1000 });
    return 'ok' as const;
  }
  async adoptTransfer(ownerKey: string, xferKey: string, codeHash: string, deviceHash: string, maxDevices: number) {
    const want = this.kvGetSync(xferKey);
    if (want === null || want !== codeHash) return 'bad-code' as const;
    this.kv.delete(xferKey);
    const raw = this.kvGetSync(ownerKey);
    const rec = decodeOwner(raw);
    if (!rec) return 'not-registered' as const;
    const hs = [...rec.h.filter((x) => x !== deviceHash), deviceHash].slice(-maxDevices);
    this.kv.set(ownerKey, { v: encodeOwner(rec.at, hs), until: this.kv.get(ownerKey)!.until });
    return 'ok' as const;
  }
  private kvGetSync(key: string): string | null {
    const e = this.kv.get(key);
    if (!e) return null;
    if (e.until <= this.now()) { this.kv.delete(key); return null; }
    return e.v;
  }
  /** test helper: the board's expiry time (ms) or null */
  expiryOf(board: string): number | null { return this.exp.get(board) ?? null; }

  private sorted(board: string, asc: boolean): Member[] {
    this.alive(board);
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
  async score(board: string, member: string) { this.alive(board); return this.z.get(zkey(board))?.get(member) ?? null; }
  async meta(board: string, member: string) { this.alive(board); return this.h.get(hkey(board))?.get(member) ?? null; }
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
  async kvGet(key: string) {
    const [r] = await this.pipe([['GET', key]]);
    return (r as string | null) ?? null;
  }
  async kvSet(key: string, value: string, opts: { nx?: boolean; ex?: number } = {}) {
    const cmd: Cmd = ['SET', key, value];
    if (opts.nx) cmd.push('NX');
    if (opts.ex) cmd.push('EX', Math.max(1, Math.round(opts.ex)));
    const [r] = await this.pipe([cmd]);
    return r === 'OK';
  }
  async kvDel(key: string) { await this.pipe([['DEL', key]]); }
  async issueTransfer(ownerKey: string, xferKey: string, deviceHash: string, codeHash: string, ttlS: number) {
    const [r] = await this.pipe([['EVAL', LUA_ISSUE, 2, ownerKey, xferKey, deviceHash, codeHash, Math.max(1, Math.round(ttlS))]]);
    return (r === 'ok' || r === 'free' ? r : 'other') as 'ok' | 'free' | 'other';
  }
  async adoptTransfer(ownerKey: string, xferKey: string, codeHash: string, deviceHash: string, maxDevices: number) {
    const [r] = await this.pipe([['EVAL', LUA_ADOPT, 2, ownerKey, xferKey, codeHash, deviceHash, maxDevices]]);
    return (r === 'ok' || r === 'not-registered' ? r : 'bad-code') as 'ok' | 'bad-code' | 'not-registered';
  }
  async boards() {
    const out: string[] = [];
    let cursor = '0';
    for (let i = 0; i < 100; i++) {
      const [r] = await this.pipe([['SCAN', cursor, 'MATCH', 'sb:z:*', 'COUNT', 500]]);
      const [next, keys] = (r as [string, string[]]) ?? ['0', []];
      for (const k of keys ?? []) out.push(k.slice(5));
      cursor = String(next);
      if (cursor === '0') break;
    }
    return [...new Set(out)];
  }
  async expireBoard(board: string, seconds: number) {
    const [ttl] = await this.pipe([['TTL', zkey(board)]]);
    if (Number(ttl) === -1) await this.pipe([['EXPIRE', zkey(board), seconds], ['EXPIRE', hkey(board), seconds]]);
  }
  async expireKey(key: string, seconds: number) {
    const [ttl] = await this.pipe([['TTL', key]]);
    if (Number(ttl) === -1) await this.pipe([['EXPIRE', key, seconds]]);
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
