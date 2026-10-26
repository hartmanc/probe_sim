// Seeded PRNG for everything random in a race (grid jitter, green-flag moment, per-lap pace noise,
// driver decisions). A race is reproducible from (seed, ai_version): never call Math.random in src/physics/ai.
import { cos as dcos, log as dlog } from '../dmath';   // the AI computes like the physics: the same bits on every host and engine

/** mulberry32: 32-bit state, period 2^32, good enough for game decisions. */
export class Rng {
  private a: number;
  constructor(seed: number) { this.a = (seed >>> 0) || 0x9e3779b9; }
  /** Uniform in [0, 1). */
  next(): number {
    this.a = (this.a + 0x6d2b79f5) >>> 0;
    let t = this.a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  /** Uniform in [lo, hi). */
  range(lo: number, hi: number): number { return lo + (hi - lo) * this.next(); }
  /** Integer in [0, n). */
  int(n: number): number { return Math.floor(this.next() * n) % n; }
  /** Standard normal (Box-Muller, one value per call). */
  normal(): number {
    let u = this.next();
    if (u < 1e-12) u = 1e-12;
    return Math.sqrt(-2 * dlog(u)) * dcos(2 * Math.PI * this.next());
  }
  /** Index drawn from unnormalized weights. */
  pick(weights: readonly number[]): number {
    let tot = 0;
    for (const w of weights) tot += w;
    let u = this.next() * tot;
    for (let i = 0; i < weights.length; i++) { u -= weights[i]; if (u < 0) return i; }
    return weights.length - 1;
  }
  /** Independent child stream (e.g. one per car), derived deterministically from this one's next value and a salt. */
  fork(salt: number | string): Rng { return new Rng(hashSeed(this.next() * 4294967296, salt)); }
  /** Current internal state (for snapshots / debugging). */
  get state(): number { return this.a; }
}

/** FNV-1a over a string, mixed with a number: stable 32-bit seeds from car numbers, names, etc. */
export function hashSeed(base: number, salt: number | string = ''): number {
  let h = (0x811c9dc5 ^ (base >>> 0)) >>> 0;
  const s = String(salt);
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  // final avalanche (murmur3 fmix32)
  h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b) >>> 0; h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35) >>> 0; h ^= h >>> 16;
  return h >>> 0;
}

/** Aggression tier weights [calm, normal, aggressive] per class (A cars more aggressive on average). */
export const AGGRESSION_WEIGHTS: Record<string, readonly number[]> = {
  A: [0.15, 0.45, 0.40],
  B: [0.25, 0.50, 0.25],
  C: [0.35, 0.50, 0.15],
};

/** Aggression tier 0 calm, 1 normal, 2 aggressive: a seeded draw from the car number, class-weighted. */
export function aggressionFor(number: string, cls: string): 0 | 1 | 2 {
  const r = new Rng(hashSeed(7919, `aggr:${number}`));
  return r.pick(AGGRESSION_WEIGHTS[cls] ?? AGGRESSION_WEIGHTS.B) as 0 | 1 | 2;
}
