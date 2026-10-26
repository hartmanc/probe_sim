// Record every argument the physics passes to src/physics/dmath.ts during hot-lap replays (docs/determinism.md
// section 3b), for tools/determinism/oracle.mts --args. The physics is bundled with esbuild with its `./dmath` import
// redirected to a recording wrapper, so the shipped code stays untouched.
//   npx tsx tools/determinism/record_args.mts <out dir> [--laps 1] [trace.json ...]
// Replays: an autopilot recording (tools/determinism/autopilot.ts) on Laguna Seca and on Sonoma, then
// every trace file given (an InputTrace or a Submission with .trace; its track from the trace).
import { build, type Plugin } from 'esbuild';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
const argv = process.argv.slice(2);
const out = resolve(argv[0] ?? 'dmath_args');
const lapsI = argv.indexOf('--laps');
const laps = lapsI >= 0 ? Number(argv[lapsI + 1]) : 1;
const traces = argv.slice(1).filter((a, i, all) => a !== '--laps' && all[i] !== '--laps' && all[i - 1] !== '--laps').map((p) => resolve(p));

const wrapper = `
import * as R from ${JSON.stringify(join(root, 'src/physics/dmath.ts'))};
const bufs = {}; export const rec = { on: false, bufs };
function push(fn, a, b, c, k) { if (!rec.on) return; let x = bufs[fn]; if (!x) x = bufs[fn] = { a: new Float64Array(1 << 20), n: 0 };
  if (x.n + k > x.a.length) { const y = new Float64Array(x.a.length * 2); y.set(x.a); x.a = y; }
  x.a[x.n++] = a; if (k > 1) x.a[x.n++] = b; if (k > 2) x.a[x.n++] = c; }
export const sin = (x) => (push('sin', x, 0, 0, 1), R.sin(x));
export const cos = (x) => (push('cos', x, 0, 0, 1), R.cos(x));
export const tan = (x) => (push('tan', x, 0, 0, 1), R.tan(x));
export const atan = (x) => (push('atan', x, 0, 0, 1), R.atan(x));
export const exp = (x) => (push('exp', x, 0, 0, 1), R.exp(x));
export const log = (x) => (push('log', x, 0, 0, 1), R.log(x));
export const atan2 = (y, x) => (push('atan2', y, x, 0, 2), R.atan2(y, x));
export const hypot = (x, y) => (push('hypot', x, y, 0, 2), R.hypot(x, y));
export const hypot3 = (x, y, z) => (push('hypot3', x, y, z, 3), R.hypot3(x, y, z));
`;
const redirect: Plugin = {
  name: 'record-dmath',
  setup(b) {
    b.onResolve({ filter: /^\.\/dmath$/ }, (a) => (a.importer.includes('/src/physics/') ? { path: 'rec-dmath', namespace: 'rec' } : undefined));
    b.onLoad({ filter: /.*/, namespace: 'rec' }, () => ({ contents: wrapper, loader: 'js', resolveDir: root }));
  },
};
const runner = `
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { rec } from 'rec-dmath';
import { loadSimAssets } from ${JSON.stringify(join(root, 'api/_lib/assets.ts'))};
import { HotlapSim } from ${JSON.stringify(join(root, 'src/scoreboard/sim.ts'))};
import { replayTrace } from ${JSON.stringify(join(root, 'src/scoreboard/replay.ts'))};
import { autopilot } from ${JSON.stringify(join(root, 'tools/determinism/autopilot.ts'))};
export async function run(out, laps, traces) {
  const jobs = [];
  for (const track of ['laguna_seca', 'sonoma']) {
    const a = await loadSimAssets(track, 'probe_gt');
    const sim = new HotlapSim(a, { record: true }); const drive = autopilot(sim);
    let n = 0; for (let i = 0; i < 400000 * laps && n < laps; i++) { const ev = sim.step(drive); if (ev && ev !== 'start') n++; }
    jobs.push([track + ' autopilot ' + n + ' lap(s)', a, JSON.parse(JSON.stringify(sim.trace()))]);
  }
  for (const p of traces) { const j = JSON.parse(readFileSync(p, 'utf8')); const t = j.trace ?? j; jobs.push([p, await loadSimAssets(t.track, t.car), t]); }
  for (const [name, a, t] of jobs) {
    rec.on = true; const r = replayTrace(a, t); rec.on = false;
    console.log('replayed ' + name + ': ' + r.steps + ' steps, laps ' + r.laps.map((l) => l.time.toFixed(3)).join(' '));
  }
  for (const [fn, x] of Object.entries(rec.bufs)) { writeFileSync(join(out, fn + '.f64'), Buffer.from(x.a.buffer, 0, x.n * 8)); console.log(fn + ': ' + x.n + ' doubles'); }
}
`;
const r = await build({
  stdin: { contents: runner, resolveDir: root, loader: 'ts' }, bundle: true, format: 'esm', platform: 'node', target: 'node22',
  write: false, plugins: [redirect, { name: 'rec-entry', setup(b) { b.onResolve({ filter: /^rec-dmath$/ }, () => ({ path: 'rec-dmath', namespace: 'rec' })); } }], logLevel: 'error',
});
mkdirSync(out, { recursive: true });
const bundle = join(out, 'runner.mjs');
writeFileSync(bundle, r.outputFiles[0].text);
const m = await import(pathToFileURL(bundle).href);
await m.run(out, laps, traces);
