// Name ownership (owner's decision, 26 Oct 2026; docs/scoreboard.md §1.1). Pure TS (Web Crypto + the injected store).
//
// - Every device makes a random 128-bit secret once (32 hex characters, localStorage) and sends it with every post.
// - The first device to post a name claims it: the server keeps a SHA-256 of that secret against the lower-cased name
//   (Redis `sb:own:<name>`, JSON { h: [hash, …], at }). Posts of an owned name without a matching secret are refused.
// - Transfer: the owning device asks for a six-character code (`sb:xfer:<name>`, the code's hash, 1 hour, one use) and
//   the player types it once on another device, which then adds its own secret's hash to the name. The code alone is
//   useless without the name, it expires, it is single-use, and guesses are rate limited per IP (5) and per name (10 per 10 min).
// - The owner releases a name in the Upstash console with `DEL sb:own:<name>` (and `DEL sb:xfer:<name>`); the next
//   device to post it claims it. Entries already on the boards keep their times either way.
import type { ScoreStore } from './store';

export const SECRET_RE = /^[0-9a-f]{32}$/;
/** Transfer-code alphabet: no 0/O, 1/I/L (read aloud or copied from another screen). 31^6 ≈ 8.9e8 codes. */
export const CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
export const CODE_LEN = 6;

export const OWNER = {
  /** devices that may post one name */
  maxDevices: 5,
  /** transfer code lifetime, s */
  codeTtlS: 3600,
  /** adopt attempts per IP per window */
  adoptPerIp: 5,
  /** adopt attempts per name per window (from any IP) */
  adoptPerName: 10,
  windowS: 600,
  /** transfer-code requests per IP per window */
  codesPerIp: 10,
} as const;

export const ownerKey = (nameKey: string): string => `sb:own:${nameKey}`;
export const xferKey = (nameKey: string): string => `sb:xfer:${nameKey}`;

export interface OwnerRecord { h: string[]; at: string }

function hex(buf: ArrayBuffer): string {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
export async function sha256Hex(s: string): Promise<string> {
  return hex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)));
}
/** What is stored for a device secret (domain-separated so the hash is useless elsewhere). */
export const secretHash = (secret: string): Promise<string> => sha256Hex(`probe-sim/owner/v1/${secret}`);
const codeHash = (nameKey: string, code: string): Promise<string> => sha256Hex(`probe-sim/xfer/v1/${nameKey}/${code}`);

/** A random transfer code (rejection sampling: uniform over the alphabet). */
export function newTransferCode(rand: (n: number) => Uint8Array = (n) => crypto.getRandomValues(new Uint8Array(n))): string {
  let out = '';
  const lim = 256 - (256 % CODE_ALPHABET.length);
  while (out.length < CODE_LEN) for (const b of rand(16)) { if (b < lim && out.length < CODE_LEN) out += CODE_ALPHABET[b % CODE_ALPHABET.length]; }
  return out;
}
/** Normalise what a player typed: upper case, spaces and dashes dropped; null when it cannot be a code. */
export function normalizeCode(raw: unknown): string | null {
  if (typeof raw !== 'string' || raw.length > 32) return null;
  const c = raw.toUpperCase().replace(/[\s-]+/g, '');
  return c.length === CODE_LEN && [...c].every((ch) => CODE_ALPHABET.includes(ch)) ? c : null;
}

function parseRecord(raw: string | null): OwnerRecord | null {
  if (!raw) return null;
  try {
    const r = JSON.parse(raw) as OwnerRecord;
    return r && Array.isArray(r.h) ? r : null;
  } catch { return null; }
}

export type Ownership = 'free' | 'you' | 'other';

/** Who owns `nameKey` relative to this secret (a missing / malformed secret is never 'you'). */
export async function ownership(store: ScoreStore, nameKey: string, secret: unknown): Promise<Ownership> {
  const rec = parseRecord(await store.kvGet(ownerKey(nameKey)));
  if (!rec) return 'free';
  if (typeof secret !== 'string' || !SECRET_RE.test(secret)) return 'other';
  return rec.h.includes(await secretHash(secret)) ? 'you' : 'other';
}

/** Claim a free name for this secret. False when another device claimed it first. */
export async function claim(store: ScoreStore, nameKey: string, secret: string, now = new Date()): Promise<boolean> {
  const h = await secretHash(secret);
  if (await store.kvSet(ownerKey(nameKey), JSON.stringify({ h: [h], at: now.toISOString() } satisfies OwnerRecord), { nx: true })) return true;
  return (await ownership(store, nameKey, secret)) === 'you';
}

/** Issue a transfer code for a name this secret owns (replaces any earlier code). */
export async function issueCode(store: ScoreStore, nameKey: string): Promise<string> {
  const code = newTransferCode();
  await store.kvSet(xferKey(nameKey), await codeHash(nameKey, code), { ex: OWNER.codeTtlS });
  return code;
}

/** Adopt a name on a new device with a transfer code: adds this secret's hash, consumes the code. */
export async function adopt(store: ScoreStore, nameKey: string, code: string, secret: string): Promise<'ok' | 'bad-code' | 'not-registered'> {
  const want = await store.kvGet(xferKey(nameKey));
  if (!want || want !== (await codeHash(nameKey, code))) return 'bad-code';
  const rec = parseRecord(await store.kvGet(ownerKey(nameKey)));
  if (!rec) return 'not-registered';
  const h = await secretHash(secret);
  const hs = [...rec.h.filter((x) => x !== h), h].slice(-OWNER.maxDevices);
  await store.kvSet(ownerKey(nameKey), JSON.stringify({ h: hs, at: rec.at } satisfies OwnerRecord));
  await store.kvDel(xferKey(nameKey));
  return 'ok';
}
