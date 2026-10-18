// Headless race: the whole field (player car driven by an AI) for N laps; prints timing, results and
// per-car pace vs target.   npx tsx tools/race/sim_race.ts [--laps 3] [--seed 1] [--every 2]
import { createTrackSurface, createCollisionWorld } from '../../src/physics/index';
import { RaceDirector } from '../../src/physics/ai/race';
import { loadTrackPack, loadProbeJson, loadPace, IDENTITY_PATH } from './load';
import { existsSync, readFileSync } from 'node:fs';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const laps = Number(arg('--laps', '3')), seed = Number(arg('--seed', '1')), every = Number(arg('--every', '2'));
const pack = loadTrackPack();
const identity = existsSync(IDENTITY_PATH) ? JSON.parse(readFileSync(IDENTITY_PATH, 'utf8')) : null;
const cw = argv.includes('--no-walls') ? null : createCollisionWorld(pack.scenery, pack.track);
const t0 = performance.now();
const dir = new RaceDirector({
  line: pack.line, surface: pack.surface, makeSurface: () => createTrackSurface(pack.track, pack.heightfield, { pitLane: pack.pitLane }),
  probeJson: loadProbeJson(), pace: loadPace(), identity, pitLane: pack.scenery?.pit_lane ?? null, collisionWorld: cw,
}, { laps, seed, playerAi: true, aiControlEvery: every });
console.log(`setup ${(performance.now() - t0).toFixed(0)} ms, ${dir.cars.length} cars, stale calibration: ${dir.calibrationStale}`);
const dt = 0.001;
let steps = 0, ms = 0, contacts = 0, hard = 0;
const tStart = performance.now();
while (dir.phase !== 'finished' && dir.time < laps * 200 + 200) {
  const a = performance.now();
  for (let k = 0; k < 1000; k++) { dir.step(dt); contacts += dir.contactCount; for (let c = 0; c < dir.contactCount; c++) if (dir.contacts[c].closing > 3) hard++; }
  ms += performance.now() - a; steps += 1000;
  if (steps % 30000 === 0) { const h = dir.hud(); console.log(`t ${dir.time.toFixed(0)} ${h.phase} lap ${h.lap} P${h.position} ${(ms * 1000 / steps / dir.cars.length).toFixed(2)} µs/car-step`); }
  if (dir.phase === 'chequered' && dir.player.finished) break;
}
const usPerStep = ms * 1000 / steps;
console.log(`\n${steps} steps in ${(ms / 1000).toFixed(1)} s: ${usPerStep.toFixed(1)} µs per step (${(usPerStep / dir.cars.length).toFixed(2)} µs per car), ${(usPerStep / 10).toFixed(1)} % of real time; wall ${((performance.now() - tStart) / 1000).toFixed(1)} s`);
console.log(`contacts ${contacts} (closing > 3 m/s: ${hard}), max depth ${dir.collider.maxDepth.toFixed(3)} m, recoveries ${dir.recoveries}, nanResets ${dir.cars.reduce((a, c) => a + c.vehicle.nanResets, 0)}`);
const res = dir.getResults();
console.log('\npos #    cls  laps    best     target  dev%  recov');
for (const r of res ?? []) {
  const c = dir.cars.find((x) => x.number === r.number)!;
  const dev = r.bestLap ? (r.bestLap / c.paceTarget - 1) * 100 : NaN;
  console.log(`${String(r.position).padStart(3)} ${r.number.padEnd(5)} ${r.class}  ${r.laps.toFixed(2).padStart(6)}  ${r.bestLap?.toFixed(2) ?? '-'}  ${c.paceTarget.toFixed(2)}  ${dev.toFixed(1).padStart(5)}  ${c.recoveries}${r.player ? '  (player/AI)' : ''}`);
}
