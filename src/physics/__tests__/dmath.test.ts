// The V8 identity proof of src/physics/dmath.ts (docs/determinism.md section 3). Any differing bit fails.
//
// The reference is V8's fdlibm evaluated without FP contraction: what the scoreboard server computes (Vercel, Node 24,
// official linux-x64 build). Its results are in fixtures/dmath_oracle.json, written by tools/determinism/oracle.mts from
// Chromium's V8 with --no-use-libm-trig-functions. A Node whose Math.* reproduces the oracle (a linux-x64 build) is a
// strict host and the port is also compared with its Math.* element by element; a Node built with FP contraction (the
// Homebrew arm64 build on the owner's Mac) is not the server's maths, and the test says so instead.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { powSets } from '../../../tools/determinism/pow_cases';
import { describe, expect, test } from 'vitest';
import * as D from '../dmath';
import { ARITY, CASE_SETS, bits, dmathFn, edgeCases, fromBits, mathFn, runSet, type FnName } from './dmath_cases';

interface Oracle {
  oracle: string;
  sets: { id: string; fn: FnName; n: number; digest: string }[];
  edges: { fn: FnName; args: string[]; bits: string }[];
  replay: Record<string, { calls: number; unique: number; arity: number; sample: string }>;
}
const oracle = JSON.parse(readFileSync(new URL('./fixtures/dmath_oracle.json', import.meta.url), 'utf8')) as Oracle;

// is this Node's Math the strict fdlibm? (one cheap set per function decides; the full sets confirm below)
const strictHost = (['sin.4pi', 'cos.4pi', 'tan.4pi', 'atan.10', 'exp.50', 'log.1e6', 'atan2.100', 'hypot.100', 'hypot3.100'] as const)
  .every((id) => { const s = CASE_SETS.find((x) => x.id === id)!; return runSet({ ...s, n: 20_000 }, mathFn(s.fn)).digest === runSet({ ...s, n: 20_000 }, dmathFn(s.fn)).digest; });

describe('dmath: bit-identical to V8 (strict fdlibm and FastMathHypot)', () => {
  test('the oracle covers every case set', () => {
    expect(oracle.sets.map((s) => s.id)).toEqual(CASE_SETS.map((s) => s.id));
    console.log(`oracle: ${oracle.oracle}; this Node ${process.version} ${process.arch}: ${strictHost ? 'strict host, also compared element by element with its Math.*'
      : 'Math.* is NOT the strict fdlibm (an FP-contracted build), compared with the oracle only'}`);
  });

  for (const s of CASE_SETS) {
    test(`${s.id}: ${s.n} random arguments, the port's results digest to the oracle's`, () => {
      const want = oracle.sets.find((x) => x.id === s.id)!;
      expect(want.n).toBe(s.n);
      const got = runSet(s, dmathFn(s.fn), strictHost ? mathFn(s.fn) : undefined);
      if (strictHost) expect(got.mismatches, `first mismatch ${JSON.stringify(got.first)}`).toBe(0);
      expect(got.digest).toBe(want.digest);
    });
  }

  test('edge cases (zeros, denormals, infinities, NaN, the kernels\' thresholds, huge arguments): every bit', () => {
    const cases = edgeCases();
    expect(cases.length).toBe(oracle.edges.length);
    const bad: string[] = [];
    cases.forEach((c, i) => {
      const o = oracle.edges[i];
      expect(o.fn).toBe(c.fn);
      expect(o.args).toEqual(c.args.map(bits));
      const [a, b, d] = [c.args[0], c.args[1] ?? 0, c.args[2] ?? 0];
      const got = bits(dmathFn(c.fn)(a, b, d));
      if (got !== o.bits) bad.push(`${c.fn}(${c.args.join(', ')}) = ${got}, V8 ${o.bits}`);
      if (strictHost) { const m = bits(mathFn(c.fn)(a, b, d)); if (got !== m) bad.push(`${c.fn}(${c.args.join(', ')}) = ${got}, this Node ${m}`); }
    });
    expect(bad).toEqual([]);
  });

  test('arguments recorded in hot-lap replays (Laguna Seca, Sonoma, browser traces): a sample against the oracle', () => {
    const fns = Object.keys(oracle.replay);
    expect(fns.length).toBeGreaterThanOrEqual(6);
    let n = 0;
    const bad: string[] = [];
    for (const fn of fns as FnName[]) {
      const r = oracle.replay[fn];
      expect(r.arity).toBe(ARITY[fn]);
      const buf = Buffer.from(r.sample, 'base64');
      const a = new Float64Array(buf.buffer, buf.byteOffset, buf.byteLength / 8);
      const k = r.arity, f = dmathFn(fn), m = mathFn(fn);
      for (let i = 0; i < a.length; i += k + 1) {
        const x = a[i], y = k > 1 ? a[i + 1] : 0, z = k > 2 ? a[i + 2] : 0, want = a[i + k];
        const got = f(x, y, z);
        n++;
        if (bits(got) !== bits(want)) bad.push(`${fn}(${[x, y, z].slice(0, k).join(', ')}) = ${bits(got)}, V8 ${bits(want)}`);
        if (strictHost && bits(m(x, y, z)) !== bits(want)) bad.push(`${fn}: this Node differs from the oracle at ${x}`);
      }
    }
    expect(bad.slice(0, 5)).toEqual([]);
    expect(n).toBeGreaterThan(5000);
  });

  test('fromBits / bits round trip and the hypot arities', () => {
    expect(fromBits(bits(-0))).toBe(-0);
    expect(D.hypot(3, 4)).toBe(5);
    expect(D.hypot3(2, 3, 6)).toBe(7);
  });
});

describe('dmath.pow: bit-identical to the server\'s Math.pow (Vercel linux-x64, Node 24, glibc 2.34)', () => {
  const srv = JSON.parse(gunzipSync(readFileSync(new URL('../../../tools/determinism/pow_server.json.gz', import.meta.url))).toString('utf8')) as
    { arch: string; version: string; glibc: string; sets: Record<string, { n: number; args: string; pow: string; first64: string[] }> };
  test(`the probe ran on the server (${srv.arch} ${srv.version} glibc ${srv.glibc})`, () => {
    expect(srv.arch).toBe('x64');
    expect(Object.keys(srv.sets).sort()).toEqual(Object.keys(powSets()).sort());
  });
  for (const [k, a] of Object.entries(powSets())) {
    test(`${k}: ${a.length / 2} arguments, the SHA-256 of the results is the server's`, () => {
      const s = srv.sets[k];
      expect(createHash('sha256').update(Buffer.from(a.buffer)).digest('hex')).toBe(s.args);   // same arguments
      const n = a.length / 2, r = new Float64Array(n);
      for (let i = 0; i < n; i++) r[i] = D.pow(a[2 * i], a[2 * i + 1]);
      const b = Buffer.from(r.buffer);
      expect(Array.from({ length: Math.min(64, n) }, (_, i) => b.subarray(i * 8, i * 8 + 8).toString('hex'))).toEqual(s.first64);
      expect(createHash('sha256').update(b).digest('hex')).toBe(s.pow);
    });
  }
  test('V8\'s special cases before std::pow, and glibc\'s', () => {
    expect(D.pow(0, NaN)).toBeNaN();               // V8: y NaN -> NaN
    expect(D.pow(NaN, 0)).toBe(1);                 // glibc: y = 0 -> 1
    expect(D.pow(1, Infinity)).toBeNaN();
    expect(D.pow(-1, -Infinity)).toBeNaN();
    expect(D.pow(3, 2)).toBe(9);
    expect(D.pow(-0, 0.5)).toBe(0);
    expect(Object.is(D.pow(-0, 0.5), 0)).toBe(true);
    expect(D.pow(-Infinity, 0.5)).toBe(Infinity);
    expect(D.pow(-8, 1 / 3)).toBeNaN();
    expect(D.pow(-2, 3)).toBe(-8);
    expect(Object.is(D.pow(-0, 3), -0)).toBe(true);
    expect(D.pow(0, -1)).toBe(Infinity);
    expect(D.pow(2, 1e10)).toBe(Infinity);
    expect(D.pow(0.5, 1e10)).toBe(0);
    expect(D.pow(1, 1e300)).toBe(1);
    for (const [x, y] of [[2, 0.5], [10, 3], [2, -1074], [2, 1023], [5e-324, 0.5]]) expect(D.pow(x, y)).toBe(Math.pow(x, y));
  });
});

describe('dmath stays exact and the replay path stays on it', () => {
  const src = (p: string) => readFileSync(new URL(p, import.meta.url), 'utf8');
  const TRANSCENDENTAL = /\bMath\.(sin|cos|tan|asin|acos|atan|atan2|sinh|cosh|tanh|asinh|acosh|atanh|exp|expm1|log|log1p|log2|log10|pow|cbrt|hypot)\b/g;

  test('dmath.ts uses no Math function but the exact ones (abs, floor, trunc, sqrt)', () => {
    const code = src('../dmath.ts').replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');
    const used = [...new Set([...code.matchAll(/\bMath\.([a-zA-Z0-9]+)/g)].map((m) => m[1]))].sort();
    expect(used.every((f) => ['abs', 'floor', 'trunc', 'sqrt'].includes(f)), used.join(', ')).toBe(true);
    expect(code.includes('**')).toBe(false);
  });

  test('no native transcendental call (pow included) in the replayed physics, the sim step or the lap timer', () => {
    const files = ['../vehicle.ts', '../tyre.ts', '../track.ts', '../collision.ts', '../rollover.ts', '../gearschedule.ts', '../cars.ts',
      '../offtrack.ts', '../spec.ts', '../types.ts', '../../app/timing.ts'];
    const found: string[] = [];
    for (const f of files) {
      const code = src(f).replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');
      for (const m of code.matchAll(TRANSCENDENTAL)) found.push(`${f}: ${m[0]}`);
      for (const m of code.matchAll(/\*\*/g)) found.push(`${f}: ** at ${m.index}`);   // the exponent operator is Math.pow
    }
    expect(found).toEqual([]);
    // the sim (including the live auto-launch's lineSteer, whose output is recorded) and the dev / test track
    for (const f of ['../../scoreboard/sim.ts', '../../scoreboard/replay.ts', '../devtrack.ts']) expect([...src(f).matchAll(TRANSCENDENTAL)].map((m) => `${f}: ${m[0]}`)).toEqual([]);
  });
});
