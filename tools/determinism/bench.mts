// Physics step cost before / after (docs/determinism.md section 6): replay one trace with the physics of a source tree,
// in Node or in a browser engine, several times, and report the best µs per physics step.
//   npx tsx tools/determinism/bench.mts <source root> <trace.json> [--reps 7] [--engine node|chromium|webkit]
//       [--url http://localhost:4173/]   (browser engines fetch the track and car files from a `vite preview`)
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';
import { playwright } from './common.mts';

const argv = process.argv.slice(2);
const arg = (k: string, d = '') => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const root = resolve(argv[0]);
const traceText = readFileSync(argv[1], 'utf8');
const reps = Number(arg('--reps', '7')), engine = arg('--engine', 'node'), url = arg('--url', 'http://localhost:4173/');

if (engine === 'node') {
  const { loadSimAssets } = await import(pathToFileURL(join(root, 'api/_lib/assets.ts')).href);
  const { replayTrace } = await import(pathToFileURL(join(root, 'src/scoreboard/replay.ts')).href);
  const t = JSON.parse(traceText);
  const a = await loadSimAssets(t.track, t.car);
  const us: number[] = [];
  for (let i = 0; i < reps; i++) { const t0 = performance.now(); const r = replayTrace(a, t); us.push(((performance.now() - t0) * 1000) / r.steps); }
  us.sort((x, y) => x - y);
  console.log(`node ${process.version} ${root.split('/').pop()}: ${JSON.parse(traceText).steps} steps, best ${us[0].toFixed(3)} µs/step, median ${us[us.length >> 1].toFixed(3)} µs/step`);
} else {
  const r = await build({
    stdin: { contents: `export { replayTrace } from ${JSON.stringify(join(root, 'src/scoreboard/replay.ts'))}; export { loadHeightfield } from ${JSON.stringify(join(root, 'src/physics/index.ts'))}; export { TRACKS, CARS } from ${JSON.stringify(join(root, 'src/scoreboard/config.ts'))};`, resolveDir: root, loader: 'ts' },
    bundle: true, format: 'iife', globalName: 'RB', write: false, platform: 'browser', target: 'es2022', logLevel: 'error', minify: true,
  });
  const lib = r.outputFiles[0].text + '\nglobalThis.RB = RB;';
  const pw = await playwright();
  const b = await pw[engine].launch();
  const p = await b.newPage({ bypassCSP: true });
  await p.goto(url + 'cars/probe_gt/car.json');   // a same-origin page for the asset fetches
  await p.evaluate(lib);
  // a plain string (tsx would wrap a function argument in its __name helper, unknown in the page)
  const PAGE = `async (traceText, reps, BASE) => {
    const RB = globalThis.RB, t = JSON.parse(traceText);
    const T = RB.TRACKS[t.track], dir = T.dir, C = RB.CARS[t.car].dir;
    const j = async (u) => (await fetch(new URL(u, BASE))).json(), bin = async (u) => (await fetch(new URL(u, BASE))).arrayBuffer();
    const track = await j(dir + 'track.json'), scenery = await j(dir + 'scenery.json').catch(() => null);
    const far = scenery?.far?.heightfield?.file;
    const a = { trackId: t.track, carId: t.car, track, heightfield: RB.loadHeightfield(await bin(dir + (track.heightfield?.file ?? 'heightfield.bin'))),
      carJson: await j(C + 'car.json'), scenery, farHeightfield: far ? RB.loadHeightfield(await bin(dir + far)) : null, ghosts: await j(dir + 'ghosts.json') };
    const us = []; let lapTimes = '';
    for (let i = 0; i < reps; i++) { const t0 = performance.now(); const r = RB.replayTrace(a, t, Infinity, () => performance.now()); us.push(((performance.now() - t0) * 1000) / r.steps); lapTimes = r.laps.map((l) => l.time.toFixed(4)).join(' '); }
    us.sort((x, y) => x - y);
    return { best: us[0], median: us[us.length >> 1], lapTimes, ua: navigator.userAgent };
  }`;
  const out = await p.evaluate(`(${PAGE})(${JSON.stringify(traceText)}, ${reps}, ${JSON.stringify(url)})`);
  await b.close();
  console.log(`${engine} (${out.ua.match(/(Chrome|Version|Firefox)\/[\d.]+/)?.[0]}) ${root.split('/').pop()}: best ${out.best.toFixed(3)} µs/step, median ${out.median.toFixed(3)} µs/step; laps ${out.lapTimes}`);
}
