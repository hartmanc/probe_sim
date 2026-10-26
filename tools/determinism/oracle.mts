// The V8 identity proof of src/physics/dmath.ts against a strict V8 (docs/determinism.md section 3).
//
// Node on this machine is Homebrew's arm64 build, compiled with FP contraction (fused multiply-adds inside V8's fdlibm),
// so its Math.atan / exp / log / sin / cos / tan differ from the plain IEEE evaluation in ~0.1-0.8 % of arguments: not the
// server's maths. The server (Vercel, Node 24, linux-x64 official build: GCC, baseline x86-64, no FMA) evaluates the
// same fdlibm without contraction. The oracle is therefore Chromium's V8 (no contraction) with
// --no-use-libm-trig-functions, i.e. exactly the fdlibm routines of the server, evaluated as the server does.
//
//   npx tsx tools/determinism/oracle.mts [--write] [--args <dir of recorded *.f64>] [--engine chromium|webkit]
// Without --write it only compares. --write stores src/physics/__tests__/fixtures/dmath_oracle.json (the digests of the
// oracle's Math.* over every CASE_SETS set, the edge-case bits, and a sample of the recorded replay arguments with the
// oracle's results), which dmath.test.ts checks the port against on any host.
import { readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { bundleIife, f64ToB64, playwright, STRICT_V8_ARGS } from './common.mts';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
const argv = process.argv.slice(2);
const arg = (k: string, d = '') => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const engine = arg('--engine', 'chromium');
const argsDir = arg('--args');
const SAMPLE = Number(arg('--sample', '1000'));

const lib = await bundleIife(join(root, 'src/physics/__tests__/dmath_cases.ts'), 'DC');
const pw = await playwright();
const browser = await pw[engine].launch(engine === 'chromium' ? { args: STRICT_V8_ARGS } : {});
const page = await browser.newPage();
await page.evaluate(lib);
const version = `${engine} ${browser.version()}${engine === 'chromium' ? ' ' + STRICT_V8_ARGS.join(' ') : ''}`;
console.log(`oracle: ${version}`);

// 1. the random sets: the oracle's Math digest, and the port's mismatches against it, elementwise
const sets: { id: string; fn: string; n: number; digest: string; mismatches: number; first: unknown }[] = [];
for (const id of await page.evaluate(() => (globalThis as any).DC.CASE_SETS.map((s: any) => s.id))) {
  const r = await page.evaluate((id: string) => {
    const DC = (globalThis as any).DC, s = DC.CASE_SETS.find((x: any) => x.id === id);
    const math = DC.runSet(s, DC.mathFn(s.fn));
    const cmp = DC.runSet(s, DC.dmathFn(s.fn), DC.mathFn(s.fn));
    return { id, fn: s.fn, n: s.n, digest: math.digest, mismatches: cmp.mismatches, first: cmp.first };
  }, id);
  sets.push(r);
  console.log(`  ${r.id.padEnd(12)} n ${String(r.n).padStart(8)}  mismatches ${r.mismatches}${r.first ? '  first ' + JSON.stringify(r.first) : ''}`);
}

// 2. the edge cases: the oracle's bits, and the port's
const edges = await page.evaluate(() => {
  const DC = (globalThis as any).DC;
  return DC.edgeCases().map((c: any) => {
    const [a, b, d] = [c.args[0], c.args[1] ?? 0, c.args[2] ?? 0];
    return { fn: c.fn, args: c.args.map(DC.bits), math: DC.bits(DC.mathFn(c.fn)(a, b, d)), port: DC.bits(DC.dmathFn(c.fn)(a, b, d)) };
  });
});
const edgeBad = edges.filter((e: any) => e.math !== e.port);
console.log(`  edges        n ${String(edges.length).padStart(8)}  mismatches ${edgeBad.length}${edgeBad.length ? '  first ' + JSON.stringify(edgeBad[0]) : ''}`);

// 3. recorded replay arguments (tools/determinism/record_args.mts): all of them elementwise, a sample kept as a fixture
const replay: Record<string, { calls: number; unique: number; mismatches: number; sample: string; arity: number }> = {};
if (argsDir) {
  for (const f of readdirSync(argsDir).filter((x) => x.endsWith('.f64')).sort()) {
    const fn = f.replace(/\.f64$/, '');
    const raw = readFileSync(join(argsDir, f));
    const all = new Float64Array(raw.buffer, raw.byteOffset, raw.byteLength / 8);
    const arity = fn === 'hypot3' ? 3 : fn === 'atan2' || fn === 'hypot' ? 2 : 1;
    // unique argument tuples (bit patterns): one-argument functions by sorting the bit patterns (tens of millions of
    // calls), the others with a set of their bytes
    let u: Float64Array;
    if (arity === 1) {
      const bitsArr = new BigUint64Array(all.length); bitsArr.set(new BigUint64Array(all.buffer.slice(all.byteOffset, all.byteOffset + all.byteLength)));
      bitsArr.sort();
      let n = 0; for (let i = 0; i < bitsArr.length; i++) if (i === 0 || bitsArr[i] !== bitsArr[i - 1]) bitsArr[n++] = bitsArr[i];
      u = new Float64Array(bitsArr.buffer.slice(0, n * 8));
    } else {
      const seen = new Set<string>(); const uniq: number[] = [];
      const b = Buffer.from(all.buffer, all.byteOffset, all.byteLength);
      for (let i = 0; i < all.length; i += arity) {
        const key = b.toString('latin1', i * 8, (i + arity) * 8);
        if (!seen.has(key)) { seen.add(key); for (let k = 0; k < arity; k++) uniq.push(all[i + k]); }
      }
      u = new Float64Array(uniq);
    }
    let mism = 0; let first: unknown = null;
    const CH = 600_000 - (600_000 % arity);
    const outs: number[] = [];
    for (let o = 0; o < u.length; o += CH) {
      const part = u.subarray(o, Math.min(u.length, o + CH));
      const r = await page.evaluate(({ b64, fn, arity }: { b64: string; fn: string; arity: number }) => {
        const DC = (globalThis as any).DC;
        const bin = atob(b64); const by = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) by[i] = bin.charCodeAt(i);
        const a = new Float64Array(by.buffer); const m = DC.mathFn(fn), d = DC.dmathFn(fn);
        let mism = 0, first = null as unknown; const res = new Float64Array(a.length / arity);
        for (let i = 0, j = 0; i < a.length; i += arity, j++) {
          const x = a[i], y = arity > 1 ? a[i + 1] : 0, z = arity > 2 ? a[i + 2] : 0;
          const p = m(x, y, z), q = d(x, y, z); res[j] = p;
          if (!(Object.is(p, q) || (p !== p && q !== q))) { mism++; if (!first) first = [x, y, z, DC.bits(p), DC.bits(q)]; }
        }
        let s = ''; const rb = new Uint8Array(res.buffer); for (let i = 0; i < rb.length; i++) s += String.fromCharCode(rb[i]);
        return { mism, first, res: btoa(s) };
      }, { b64: f64ToB64(part), fn, arity });
      mism += r.mism; if (!first && r.first) first = r.first;
      const rb = Buffer.from(r.res, 'base64'); const rr = new Float64Array(rb.buffer, rb.byteOffset, rb.byteLength / 8);
      for (const v of rr) outs.push(v);
    }
    // sample: SAMPLE tuples evenly over the unique ones, each followed by the oracle's result
    const nU = u.length / arity, step = Math.max(1, Math.floor(nU / SAMPLE));
    const smp: number[] = [];
    for (let j = 0; j < nU && smp.length < SAMPLE * (arity + 1); j += step) { for (let k = 0; k < arity; k++) smp.push(u[j * arity + k]); smp.push(outs[j]); }
    replay[fn] = { calls: all.length / arity, unique: nU, mismatches: mism, sample: f64ToB64(new Float64Array(smp)), arity };
    console.log(`  replay ${fn.padEnd(6)} calls ${String(all.length / arity).padStart(9)}  unique ${String(nU).padStart(8)}  mismatches ${mism}${first ? '  first ' + JSON.stringify(first) : ''}`);
  }
}
await browser.close();

const total = sets.reduce((s, r) => s + r.mismatches, 0) + edgeBad.length + Object.values(replay).reduce((s, r) => s + r.mismatches, 0);
console.log(`total mismatches: ${total}`);
if (argv.includes('--write')) {
  if (engine !== 'chromium') throw new Error('the fixture is written from the strict-V8 oracle only');
  if (total) throw new Error('not writing a fixture while the port mismatches the oracle');
  const out = join(root, 'src/physics/__tests__/fixtures/dmath_oracle.json');
  const prev = existsSync(out) ? JSON.parse(readFileSync(out, 'utf8')) : null;
  writeFileSync(out, JSON.stringify({
    oracle: version, note: 'tools/determinism/oracle.mts --write; docs/determinism.md section 3',
    sets: sets.map(({ id, fn, n, digest }) => ({ id, fn, n, digest })),
    edges: edges.map(({ fn, args, math }: any) => ({ fn, args, bits: math })),
    replay: argsDir ? Object.fromEntries(Object.entries(replay).map(([k, v]) => [k, { calls: v.calls, unique: v.unique, arity: v.arity, sample: v.sample }])) : prev?.replay ?? {},
  }, null, 0).replace(/\},\{/g, '},\n{') + '\n');
  console.log(`wrote ${out}`);
}
process.exit(total ? 1 : 0);
