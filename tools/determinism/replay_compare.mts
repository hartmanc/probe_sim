// Replay hot-lap traces with the physics of a given source tree and print every lap time and the final state as bits
// (docs/determinism.md section 4): run it on this branch and on a release-040 checkout, with and without
// tools/determinism/strict-math.mjs, and compare the lines.
//   npx tsx tools/determinism/replay_compare.mts <source root> <trace.json ...>
// A trace file is an InputTrace, a Submission ({ trace }) or a list of either; autopilot:<track>[:laps] records one
// first with tools/determinism/autopilot.ts on the given tree (SAVE_TRACES=<path prefix> keeps it).
import { readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

const [rootArg, ...items] = process.argv.slice(2);
const root = resolve(rootArg);
const imp = (p: string) => import(pathToFileURL(join(root, p)).href);
const { loadSimAssets } = await imp('api/_lib/assets.ts');
const { replayTrace } = await imp('src/scoreboard/replay.ts');
const { HotlapSim } = await imp('src/scoreboard/sim.ts');
const { autopilot } = await import(pathToFileURL(resolve(new URL('.', import.meta.url).pathname, 'autopilot.ts')).href);

const f64 = new Float64Array(1), u8 = new Uint8Array(f64.buffer);
const hex = (x: number) => { f64[0] = x; return Buffer.from(u8).toString('hex'); };
function stateHash(sim: any): string {
  const s = sim.vehicle.state, h = createHash('sha256');
  const v = [...s.pos, ...s.quat, ...s.vel, ...s.angVel, s.rpm, s.gear, s.speed, sim.simTime, sim.s, sim.stepIndex];
  for (const w of s.wheels) v.push(...w.pos, w.spinAngle, w.steer, w.compression, w.omega, w.slipRatio, w.slipAngle, w.load);
  h.update(Buffer.from(new Float64Array(v).buffer));
  return h.digest('hex').slice(0, 16);
}

for (const it of items) {
  let traces: any[];
  if (it.startsWith('autopilot:')) {
    const [, track, n] = it.split(':'); const laps = Number(n ?? 1);
    const a = await loadSimAssets(track, 'probe_gt'); const sim = new HotlapSim(a, { record: true }); const drive = autopilot(sim);
    let k = 0; while (k < laps && sim.stepIndex < 720_000) { const ev = sim.step(drive); if (ev && ev !== 'start') k++; }
    traces = [JSON.parse(JSON.stringify(sim.trace()))];
    if (process.env.SAVE_TRACES) writeFileSync(`${process.env.SAVE_TRACES}${track}_autopilot_${laps}.json`, JSON.stringify(traces[0]));
  } else {
    const j = JSON.parse(readFileSync(it, 'utf8'));
    traces = (Array.isArray(j) ? j : [j]).map((x: any) => x.trace ?? x);
  }
  for (const t of traces) {
    const a = await loadSimAssets(t.track, t.car);
    const r = replayTrace(a, t);
    const rows = createHash('sha256').update(JSON.stringify(t.rows)).digest('hex').slice(0, 8);
    console.log(`${it.split('/').pop()} ${t.track} rows ${rows} steps ${r.steps} laps ${r.laps.map((l: any) => `${l.n}:${l.time.toFixed(4)}=${hex(l.time)}${l.valid ? '' : '(inv)'}`).join(' ')} state ${stateHash(r.sim)}`);
  }
}
