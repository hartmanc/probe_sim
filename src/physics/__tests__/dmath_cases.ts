// The argument sets of the dmath identity proof (docs/determinism.md section 3), shared by the vitest test
// (dmath.test.ts) and the browser oracle (tools/determinism/oracle.mts), so both walk exactly the same doubles.
// Pure TS with exact integer / IEEE operations only: the sequence is the same in every engine.
import * as D from '../dmath';

const F = new Float64Array(1), U = new Uint32Array(F.buffer);
const LE = new Uint8Array(new Uint16Array([1]).buffer)[0] === 1;
function wordsToDouble(hi: number, lo: number): number { U[LE ? 1 : 0] = hi; U[LE ? 0 : 1] = lo; return F[0]; }

/** mulberry32, 32-bit state: integer arithmetic only. */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  const next32 = (): number => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return (t ^ (t >>> 14)) >>> 0;
  };
  // uniform double in [0, 1) with 53 random bits
  return () => ((next32() >>> 5) * 67108864 + (next32() >>> 6)) / 9007199254740992;
}

/** 2^e, exact: built from the bit pattern (no Math.pow / ** involved). */
export function pow2(e: number): number {
  if (e >= -1022) return wordsToDouble((e + 1023) << 20, 0);
  return wordsToDouble(1 << 20, 0) * wordsToDouble((e + 1022 + 1023) << 20, 0);   // 2^-1022 · 2^(e+1022), exact
}

export type Fn1 = 'sin' | 'cos' | 'tan' | 'atan' | 'exp' | 'log' | 'cbrt';
export type Fn2 = 'atan2' | 'hypot';
export type Fn3 = 'hypot3';
export type FnName = Fn1 | Fn2 | Fn3;

/** One argument set: `arity` doubles per case, generated from `seed`. */
export interface CaseSet { id: string; fn: FnName; n: number; seed: number; gen: (r: () => number) => number }

const uni = (lo: number, hi: number) => (r: () => number) => lo + (hi - lo) * r();
const sym = (R: number) => (r: () => number) => (2 * r() - 1) * R;
/** random sign, magnitude 2^e·(1+u) with e uniform in [e0, e1] */
const logu = (e0: number, e1: number) => (r: () => number) => {
  const s = r() < 0.5 ? -1 : 1;
  const e = e0 + Math.floor(r() * (e1 - e0 + 1));
  return s * (1 + r()) * pow2(e);
};
const PI = 3.141592653589793;

/** The random sets: the ranges the physics uses (angles to 4 pi, track roughness phases to 1e4 rad, exp to 50, log of
 *  ratios and loads), then wide log-uniform sweeps where the argument reduction and the special paths matter. */
export const CASE_SETS: CaseSet[] = [
  { id: 'sin.4pi', fn: 'sin', n: 1_000_000, seed: 101, gen: sym(4 * PI) },
  { id: 'cos.4pi', fn: 'cos', n: 1_000_000, seed: 102, gen: sym(4 * PI) },
  { id: 'tan.4pi', fn: 'tan', n: 1_000_000, seed: 103, gen: sym(4 * PI) },
  { id: 'sin.1e4', fn: 'sin', n: 1_000_000, seed: 104, gen: sym(1e4) },
  { id: 'cos.1e4', fn: 'cos', n: 1_000_000, seed: 105, gen: sym(1e4) },
  { id: 'sin.wide', fn: 'sin', n: 200_000, seed: 106, gen: logu(-1074, 1023) },
  { id: 'cos.wide', fn: 'cos', n: 200_000, seed: 107, gen: logu(-1074, 1023) },
  { id: 'tan.wide', fn: 'tan', n: 200_000, seed: 108, gen: logu(-1074, 1023) },
  { id: 'atan.10', fn: 'atan', n: 1_000_000, seed: 109, gen: sym(10) },
  { id: 'atan.wide', fn: 'atan', n: 200_000, seed: 110, gen: logu(-1074, 1023) },
  { id: 'exp.50', fn: 'exp', n: 1_000_000, seed: 111, gen: sym(50) },
  { id: 'exp.range', fn: 'exp', n: 200_000, seed: 112, gen: uni(-750, 712) },
  { id: 'exp.small', fn: 'exp', n: 200_000, seed: 113, gen: logu(-60, -1) },
  { id: 'log.1e6', fn: 'log', n: 1_000_000, seed: 114, gen: uni(0, 1e6) },
  { id: 'log.near1', fn: 'log', n: 200_000, seed: 115, gen: uni(0.999, 1.001) },
  { id: 'log.wide', fn: 'log', n: 200_000, seed: 116, gen: (r) => Math.abs(logu(-1074, 1023)(r)) },
  { id: 'cbrt.1e6', fn: 'cbrt', n: 1_000_000, seed: 123, gen: sym(1e6) },
  { id: 'cbrt.wide', fn: 'cbrt', n: 200_000, seed: 124, gen: logu(-1074, 1023) },
  { id: 'atan2.100', fn: 'atan2', n: 1_000_000, seed: 117, gen: sym(100) },
  { id: 'atan2.wide', fn: 'atan2', n: 200_000, seed: 118, gen: logu(-1074, 1023) },
  { id: 'hypot.100', fn: 'hypot', n: 1_000_000, seed: 119, gen: sym(100) },
  { id: 'hypot.wide', fn: 'hypot', n: 200_000, seed: 120, gen: logu(-1074, 1023) },
  { id: 'hypot3.100', fn: 'hypot3', n: 1_000_000, seed: 121, gen: sym(100) },
  { id: 'hypot3.wide', fn: 'hypot3', n: 200_000, seed: 122, gen: logu(-1074, 1023) },
];

export const ARITY: Record<FnName, number> = { cbrt: 1, sin: 1, cos: 1, tan: 1, atan: 1, exp: 1, log: 1, atan2: 2, hypot: 2, hypot3: 3 };

/** The engine's own Math function for `fn` (hypot3 = Math.hypot with three arguments). */
export function mathFn(fn: FnName, M: Math = Math): (a: number, b: number, c: number) => number {
  switch (fn) {
    case 'atan2': return (a, b) => M.atan2(a, b);
    case 'hypot': return (a, b) => M.hypot(a, b);
    case 'hypot3': return (a, b, c) => M.hypot(a, b, c);
    default: { const f = M[fn]; return (a) => f(a); }
  }
}
/** The port's function for `fn`. */
export function dmathFn(fn: FnName): (a: number, b: number, c: number) => number {
  switch (fn) {
    case 'atan2': return (a, b) => D.atan2(a, b);
    case 'hypot': return (a, b) => D.hypot(a, b);
    case 'hypot3': return (a, b, c) => D.hypot3(a, b, c);
    default: { const f = D[fn]; return (a) => f(a); }
  }
}

/** The 64 bits of x as 16 hex digits (NaN canonical: engines may differ in NaN payloads, which JS cannot observe
 *  except through typed arrays). */
export function bits(x: number): string {
  if (x !== x) return '7ff8000000000000';
  F[0] = x;
  const hi = U[LE ? 1 : 0], lo = U[LE ? 0 : 1];
  return hi.toString(16).padStart(8, '0') + lo.toString(16).padStart(8, '0');
}
/** A double from 16 hex digits. */
export function fromBits(h: string): number {
  U[LE ? 1 : 0] = parseInt(h.slice(0, 8), 16); U[LE ? 0 : 1] = parseInt(h.slice(8), 16);
  return F[0];
}

/** Running 64-bit digest (two FNV-1a style 32-bit lanes) over result bit patterns. */
export class Digest {
  private h1 = 0x811c9dc5; private h2 = 0x01000193 ^ 0x5bd1e995;
  add(x: number): void {
    let hi: number, lo: number;
    if (x !== x) { hi = 0x7ff80000; lo = 0; } else { F[0] = x; hi = U[LE ? 1 : 0]; lo = U[LE ? 0 : 1]; }
    this.h1 = Math.imul(this.h1 ^ lo, 0x01000193) >>> 0;
    this.h1 = Math.imul(this.h1 ^ hi, 0x01000193) >>> 0;
    this.h2 = Math.imul(this.h2 ^ hi, 0x5bd1e995) >>> 0;
    this.h2 = Math.imul(this.h2 ^ (this.h2 >>> 13) ^ lo, 0x5bd1e995) >>> 0;
  }
  get hex(): string { return this.h1.toString(16).padStart(8, '0') + this.h2.toString(16).padStart(8, '0'); }
}

export interface SetResult { id: string; fn: FnName; n: number; digest: string; mismatches?: number; first?: [number[], string, string] | null }

/** Walk one set with `f`; with `g` also count elementwise mismatches of f against g (bits, NaN = NaN). */
export function runSet(s: CaseSet, f: (a: number, b: number, c: number) => number, g?: (a: number, b: number, c: number) => number): SetResult {
  const r = rng(s.seed), k = ARITY[s.fn], d = new Digest();
  let mism = 0, first: SetResult['first'] = null;
  for (let i = 0; i < s.n; i++) {
    const a = s.gen(r), b = k > 1 ? s.gen(r) : 0, c = k > 2 ? s.gen(r) : 0;
    const y = f(a, b, c);
    d.add(y);
    if (g) {
      const z = g(a, b, c);
      if (!(Object.is(y, z) || (y !== y && z !== z))) { mism++; if (!first) first = [[a, b, c].slice(0, k), bits(y), bits(z)]; }
    }
  }
  return { id: s.id, fn: s.fn, n: s.n, digest: d.hex, ...(g ? { mismatches: mism, first } : {}) };
}

const SPECIAL = [0, -0, 5e-324, -5e-324, 2.2250738585072014e-308, -2.2250738585072014e-308, 2.225073858507201e-308,
  1.7976931348623157e308, -1.7976931348623157e308, Infinity, -Infinity, NaN, 1, -1, 0.5, -0.5, 2, -2,
  PI, -PI, PI / 2, -PI / 2, PI / 4, -PI / 4, 3 * PI / 4, 2 * PI, 1e22, -1e22, pow2(52), pow2(53) + 2, pow2(1023), 1e300,
  0.4375, 0.6875, 1.1875, 2.4375, pow2(66), pow2(-27), pow2(-28), 0.3, 0.78125, 0.6744, 0.6744155717943024,
  709.782712893384, 709.7827128933841, 709.78, -745.1332191019411, -745.1332191019412, -708.4, 0.34657359027997264,
  1.0397207708399179, 1.0000000000000002, 0.9999999999999999, 1e-300, 1e-10, 3.725290298461914e-9, 1.4901161193847656e-8,
  1.5707963267948966, 1.5707963267948968, 4.71238898038469, 6.283185307179586, 1e5, 823549.6, pow2(19) * PI / 2, 1e9];

/** The edge cases: every special value per function, and their pairs / triples for the multi-argument ones. */
export function edgeCases(): { fn: FnName; args: number[] }[] {
  const out: { fn: FnName; args: number[] }[] = [];
  for (const fn of ['sin', 'cos', 'tan', 'atan', 'exp', 'log', 'cbrt'] as const) {
    for (const x of SPECIAL) out.push({ fn, args: [x] });
    // the neighbours of each special value
    for (const x of SPECIAL) if (Number.isFinite(x) && x !== 0) { out.push({ fn, args: [x * (1 + pow2(-52))] }, { fn, args: [x * (1 - pow2(-53))] }); }
  }
  const P = [0, -0, 5e-324, -5e-324, 1, -1, 2, -0.5, Infinity, -Infinity, NaN, 1e300, -1e300, 1e-300, pow2(-1022), PI];
  for (const a of P) for (const b of P) { out.push({ fn: 'atan2', args: [a, b] }, { fn: 'hypot', args: [a, b] }); }
  for (const a of P) for (const b of P) for (const c of [0, -1, Infinity, NaN, 1e300, 5e-324]) out.push({ fn: 'hypot3', args: [a, b, c] });
  return out;
}
