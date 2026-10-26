// Cross-engine proof (docs/determinism.md section 5): drive N hot laps in a real browser engine on the built game
// (`npm run build && npx vite preview --port 4173 --strictPort`), through the game's own HotlapLoop / HotlapSim and
// its recording, then replay the trace in Node with the server's code and compare every lap time and the final state
// bit for bit.
//   npx tsx tools/determinism/browser_trace.mts <chromium|webkit|firefox> [--track laguna_seca] [--laps 6]
//       [--url http://localhost:4173/] [--out <file.json>: { engine, ua, laps (with bits), state (bits), trace }]
// The driver is tools/determinism/autopilot.ts, bundled into the page and installed as the loop's input reader; the
// rendering loop is frozen (timeScale 0) and the sim is advanced from the script in 1 s slices, so a 6-lap run takes
// seconds, not 14 minutes. Everything the physics computes runs in the engine under test.
import { writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { bundleIife, playwright } from './common.mts';
import { loadSimAssets } from '../../api/_lib/assets';
import { HotlapSim } from '../../src/scoreboard/sim';
import { SAMPLE_EVERY } from '../../src/scoreboard/config';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
const argv = process.argv.slice(2);
const arg = (k: string, d = '') => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const engine = argv[0] ?? 'webkit';
const track = arg('--track', 'laguna_seca'), laps = Number(arg('--laps', '6'));
const base = arg('--url', 'http://localhost:4173/');
const out = arg('--out');

const ap = await bundleIife(join(root, 'tools/determinism/autopilot.ts'), 'AP');
const pw = await playwright();
if (!pw[engine]) throw new Error(`no ${engine} in playwright-core`);
let browser;
try { browser = await pw[engine].launch(); } catch (e) { console.log(`${engine}: not available (${(e as Error).message.split('\n')[0]})`); process.exit(2); }
const page = await browser.newPage({ viewport: { width: 960, height: 540 }, bypassCSP: true });
const errors: string[] = [];
page.on('pageerror', (e: Error) => errors.push(e.message));
await page.goto(`${base}?track=${track}`);
await page.waitForFunction(() => !!(window as any).__sim?.hotlap, null, { timeout: 180_000 });
const ua = await page.evaluate(() => navigator.userAgent);
await page.evaluate(ap);

const res = await page.evaluate(async ({ laps }: { laps: number }) => {
  const S = (window as any).__sim, sim = S.hotlap, loop = S.loop;
  S.setMode('hotlap');
  loop.timeScale = () => 0;              // the render loop no longer advances the sim; this script does
  S.mode.reset();                        // the rolling start with the auto-launch, a fresh recording
  const drive = (window as any).AP.autopilot(sim);
  loop.read = () => { const r = drive(); return { steer: r.steer, throttle: r.throttle, brake: r.brake, handbrake: false, tag: 'keys' }; };
  const lapsSeen: { n: number; time: number; valid: boolean }[] = [];
  let trace: unknown = null, state: number[] | null = null;
  const orig = loop.onLap;
  loop.onLap = (lap: any, tag: string) => {
    lapsSeen.push({ n: lap.n, time: lap.time, valid: lap.valid });
    if (lap.n === laps) {
      trace = JSON.parse(JSON.stringify(sim.trace()));
      const s = sim.vehicle.state;
      state = [...s.pos, ...s.quat, ...s.vel, ...s.angVel, s.rpm, s.gear, s.speed, sim.simTime, sim.s, sim.stepIndex];
      for (const w of s.wheels) state.push(...w.pos, w.spinAngle, w.steer, w.compression, w.omega, w.slipRatio, w.slipAngle, w.load);
    }
    orig?.(lap, tag);
  };
  const t0 = performance.now();
  while (!trace && sim.stepIndex < 1_000_000) {
    loop.timeScale = () => 1;
    loop.advance(1.0);
    loop.timeScale = () => 0;
    if (S.menu?.isOpen) S.menu.close?.();
  }
  const ms = performance.now() - t0;
  loop.onLap = orig;
  return { laps: lapsSeen, trace, state, steps: sim.stepIndex, ms };
}, { laps });
await browser.close();
if (errors.length) console.log(`page errors: ${errors.slice(0, 3).join(' | ')}`);
if (!res.trace || !res.state) throw new Error(`${engine}: no lap ${laps} (${res.laps.length} laps, ${res.steps} steps)`);
const t = res.trace as any;

// replay on Node with the server's code
const a = await loadSimAssets(t.track, t.car);
// replayTrace()'s loop without its cap: six autopilot laps (~139 s each) run past LIMITS.maxTraceSteps (720 s), which
// bounds what a player may post, not the physics; the stepping is the server's HotlapSim.applyRow / advance as is
function replayUncapped(t: any, lapN: number) {
  const sim = new HotlapSim(a, { record: false, ref: t.ref[0]?.[1] ?? null });
  const rows = t.rows, refs = t.ref, laps: any[] = [];
  let ri = 0, fi = 0;
  while (sim.stepIndex < t.steps + 1000) {
    const k = sim.stepIndex;
    if (k % SAMPLE_EVERY === 0) {
      while (fi < refs.length && refs[fi][0] <= k) { sim.replayRef(refs[fi][1]); fi++; }
      if (fi === 0) sim.replayRef(null);
      while (ri + 1 < rows.length && rows[ri + 1][0] <= k) ri++;
      sim.applyRow(rows[ri], rows[ri][0] === k);
    }
    const ev = sim.advance();
    if (ev && ev !== 'start') { laps.push(ev); if (ev.n === lapN) break; }
  }
  return { sim, laps, steps: sim.stepIndex };
}
const r = replayUncapped(t, laps);
const s = r.sim.vehicle.state;
const mine = [...s.pos, ...s.quat, ...s.vel, ...s.angVel, s.rpm, s.gear, s.speed, r.sim.simTime, r.sim.s, r.sim.stepIndex];
for (const w of s.wheels) mine.push(...w.pos, w.spinAngle, w.steer, w.compression, w.omega, w.slipRatio, w.slipAngle, w.load);
const f = new Float64Array(1), b = new Uint8Array(f.buffer);
const hex = (x: number) => { f[0] = x; return Buffer.from(b).toString('hex'); };
const lapLine = (l: { n: number; time: number; valid: boolean }) => `${l.n}:${l.time.toFixed(4)}${l.valid ? '' : '(inv)'}`;
const browserLaps = res.laps, nodeLaps = r.laps;
let same = browserLaps.length === nodeLaps.length;
for (let i = 0; i < Math.min(browserLaps.length, nodeLaps.length); i++) if (hex(browserLaps[i].time) !== hex(nodeLaps[i].time) || browserLaps[i].valid !== nodeLaps[i].valid) same = false;
const stateSame = res.state.length === mine.length && res.state.every((x, i) => hex(x) === hex(mine[i]));
let diffs = 0, maxd = 0;
for (let i = 0; i < mine.length; i++) if (hex(res.state[i]) !== hex(mine[i])) { diffs++; maxd = Math.max(maxd, Math.abs(res.state[i] - mine[i])); }
if (out) writeFileSync(out, JSON.stringify({ engine, ua, laps: browserLaps.map((l) => ({ ...l, bits: hex(l.time) })), state: res.state.map(hex), trace: t }));
const bytes = JSON.stringify(t).length;
console.log(`${engine} (${ua.match(/(Chrome|Version|Firefox)\/[\d.]+/)?.[0] ?? ua}) ${track}: ${res.steps} steps in ${(res.ms / 1000).toFixed(1)} s in the page, trace ${t.rows.length} rows, ${(bytes / 1024).toFixed(0)} KB, rows sha ${createHash('sha256').update(JSON.stringify(t.rows)).digest('hex').slice(0, 8)}`);
console.log(`  browser laps ${browserLaps.map(lapLine).join(' ')}`);
console.log(`  node    laps ${nodeLaps.map(lapLine).join(' ')}`);
console.log(`  lap times bit-identical: ${same ? 'YES' : 'NO'}; final state (${mine.length} values) bit-identical: ${stateSame ? 'YES' : `NO (${diffs} differ, max |d| ${maxd.toExponential(2)})`}`);
process.exit(same && stateSame ? 0 : 1);
