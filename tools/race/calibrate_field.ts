// Fit each AI car's pace scale so its clean solo lap equals the real target lap (pace.json), and one
// scale per real stint (pace.json cars[].stints[]: the per-driver paces a race draws from).
//
//   npx tsx tools/race/calibrate_field.ts [--track <id>] [--only 711,619] [--workers 8] [--tol 0.002] [--dry]
//
// Identity: the track's own cars/field/<id>/identity.json (TRACKS[id].identity) when it exists, else the global one;
// a car's row is found by its pace.json `id`, else its number (field.ts fieldKey), as in the app's race.
// Per car: the AI driver alone on the track (registry id, default Laguna Seca) with the race physics (1 kHz, control at 500 Hz), 2
// flying laps per evaluation, lap 2 counts. Bracketed secant / bisection on the scale (<= 8
// evaluations), starting from the Probe's lap ratio. Writes scale + achievedLap into the track's pace file
// (TRACKS[id].pace; Laguna public/cars/field/pace.json) and prints a table. Bump AI_VERSION (src/physics/ai/field.ts) when the
// driver or this procedure changes behaviour, then re-run.

import { writeFileSync } from 'node:fs';
import { cpus } from 'node:os';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';
import { fileURLToPath } from 'node:url';
import { loadTrackPack, loadProbeJson, loadPace, loadIdentity, pacePath, trackArg } from './load';
import { runSolo } from '../../src/physics/ai/solo';
import { AI_VERSION, PACE_MIN, PACE_MAX, describeAiCar, fieldKey, paceSplit, type PaceCar } from '../../src/physics/ai/field';

// number: the car (the player's #619 runs without identity); key: its identity row (pace.json `id`, else the number)
interface Job { id: string; number: string; key: string; target: number; guess: number; tol: number }
interface Fit { id: string; number: string; scale: number; lap: number; evals: number; ok: boolean; history: [number, number][] }

const MAX_EVALS = 12;
const PLAYER = '619';

function fitOne(job: Job, evalLap: (scale: number) => number): Fit {
  const T = job.target;
  const hist: [number, number][] = [];
  const f = (p: number) => { const t = evalLap(p); hist.push([p, t]); return t; };
  // lap time falls with the scale: g(p) = lap(p) - T is decreasing
  let p = job.guess, t = f(p);
  let lo: [number, number] | null = null, hi: [number, number] | null = null; // lo: too slow (t > T), hi: too fast
  // a NaN lap means the car spun or left the track on that evaluation: not a point on the lap(scale) curve
  const upd = (pp: number, tt: number) => { if (Number.isNaN(tt)) return; if (tt > T) { if (!lo || pp > lo[0]) lo = [pp, tt]; } else { if (!hi || pp < hi[0]) hi = [pp, tt]; } };
  upd(p, t);
  let best: [number, number] = [p, Number.isNaN(t) ? 1e3 : t];
  while (hist.length < MAX_EVALS && (Number.isNaN(t) || Math.abs(t - T) / T > job.tol)) {
    let next: number;
    if (Number.isNaN(t)) {
      // step back toward the last clean scale (or down a little): the spin region is usually a sliver
      next = best[1] < 1e3 ? 0.5 * (p + best[0]) : p * 0.95;
    } else if (lo && hi) {
      // secant inside the bracket, fall back to bisection when it lands too close to an end
      const [p1, t1] = lo, [p2, t2] = hi;
      next = p1 + (t1 - T) * (p2 - p1) / (t1 - t2);
      const w = p2 - p1;
      if (!(next > p1 + 0.1 * w && next < p2 - 0.1 * w)) next = 0.5 * (p1 + p2);
    } else {
      // lap ~ 1/p: proportional step, a bit beyond to get a bracket
      next = p * (t / T) * (t > T ? 1.002 : 0.998);
      if (!Number.isFinite(t) || t <= 0) next = p * 0.95;
    }
    next = Math.min(PACE_MAX, Math.max(PACE_MIN, next));
    p = next; t = f(p); upd(p, t);
    if (!Number.isNaN(t) && Math.abs(t - T) < Math.abs(best[1] - T)) best = [p, t];
  }
  return { id: job.id, number: job.number, scale: +best[0].toFixed(5), lap: +best[1].toFixed(3), evals: hist.length, ok: Math.abs(best[1] - T) / T <= Math.max(job.tol, 0.005), history: hist };
}

function makeEval(track: string) {
  const pack = loadTrackPack(track);
  const probe = loadProbeJson();
  const ident = loadIdentity(track);   // the track's own identity.json, else the global one (tools/race/load.ts)
  return (num: string, key: string = num) => (scale: number) => {
    const r = runSolo(pack.line, pack.surface, probe, num === PLAYER ? null : ident.get(key) ?? null, scale, 2);
    return r.laps.length >= 2 && r.recoveries === 0 ? r.laps[1] : Number.NaN;   // spun / off / stuck: not a usable lap
  };
}

if (!isMainThread) {
  const evalFor = makeEval(workerData.track);
  const jobs: Job[] = workerData.jobs;
  for (const job of jobs) parentPort!.postMessage(fitOne(job, evalFor(job.number, job.key)));
} else {
  const argv = process.argv.slice(2);
  const arg = (k: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
  const only = arg('--only')?.split(',');
  const tol = Number(arg('--tol') ?? 0.002);
  const nWorkers = Math.max(1, Number(arg('--workers') ?? Math.min(8, Math.max(1, cpus().length - 2))));
  const dry = argv.includes('--dry');
  const track = trackArg(argv);
  const pace = loadPace(track);
  const probeJson = loadProbeJson();
  const ident = loadIdentity(track);
  const cars = pace.cars.filter((c) => !only || only.includes(c.number));
  // reference: the Probe at scale 1
  const t0 = performance.now();
  const ref = makeEval(track)('619')(1);
  console.log(`reference: AI Probe at scale 1.000 laps ${ref.toFixed(2)} s`);
  const fresh = pace.ai_version === AI_VERSION;
  const jobs: Job[] = [];
  for (const c of cars) {
    const key = fieldKey(c);
    jobs.push({ id: c.number, number: c.number, key, target: c.targetLap, guess: c.scale && fresh ? c.scale : ref / c.targetLap, tol });
    for (const s of c.stints ?? []) jobs.push({ id: `${c.number}/${s.index}`, number: c.number, key, target: s.targetLap, guess: s.scale && fresh ? s.scale : ref / s.targetLap, tol });
  }
  console.log(`${jobs.length} fits (${cars.length} cars + their stints)`);
  const fits = new Map<string, Fit>();
  await new Promise<void>((done, fail) => {
    const per = Math.ceil(jobs.length / nWorkers);
    let live = 0;
    for (let w = 0; w < nWorkers; w++) {
      // interleave so every worker gets fast and slow cars
      const mine = jobs.filter((_, k) => k % nWorkers === w);
      if (!mine.length) continue;
      live++;
      const wk = new Worker(fileURLToPath(import.meta.url), { workerData: { jobs: mine, track }, execArgv: ['--import', 'tsx'] });
      wk.on('message', (f: Fit) => { fits.set(f.id, f); process.stderr.write(`  #${f.id.padEnd(6)} scale ${f.scale.toFixed(4)} lap ${f.lap.toFixed(2)} (${f.evals} evals)\n`); });
      wk.on('error', fail);
      wk.on('exit', () => { if (--live === 0) done(); });
      void per;
    }
  });
  const mmss = (x: number) => `${Math.floor(x / 60)}:${(x % 60).toFixed(2).padStart(5, '0')}`;
  console.log('\n #       cls grid  target    AI lap    err%   scale  evals   grip  power');
  let worst = 0;
  for (const c of pace.cars) {
    const f = fits.get(c.number);
    if (!f) continue;
    const err = (f.lap / c.targetLap - 1) * 100;
    worst = Math.max(worst, Math.abs(err));
    const sp = paceSplit(f.scale);
    console.log(`${c.number.padEnd(7)} ${c.class}   ${String(c.grid).padStart(3)}  ${mmss(c.targetLap)}  ${mmss(f.lap)}  ${err.toFixed(2).padStart(6)}  ${f.scale.toFixed(4)}  ${f.evals}   ${sp.grip.toFixed(3)}  ${sp.power.toFixed(3)}${f.ok ? '' : '  NOT CONVERGED'}${c.player ? '  (player, reference only)' : ''}`);
    (c as PaceCar).scale = f.scale;
    (c as PaceCar).achievedLap = f.lap;
    for (const s of c.stints ?? []) {
      const fs = fits.get(`${c.number}/${s.index}`);
      if (!fs) continue;
      const e = (fs.lap / s.targetLap - 1) * 100;
      worst = Math.max(worst, Math.abs(e));
      const ss = paceSplit(fs.scale);
      console.log(`  /${String(s.index).padEnd(4)}       ${String(s.laps).padStart(3)}  ${mmss(s.targetLap)}  ${mmss(fs.lap)}  ${e.toFixed(2).padStart(6)}  ${fs.scale.toFixed(4)}  ${fs.evals}   ${ss.grip.toFixed(3)}  ${ss.power.toFixed(3)}${fs.ok ? '' : '  NOT CONVERGED'}`);
      s.scale = fs.scale; s.achievedLap = fs.lap;
    }
    // the player's car is the real Probe (car.json); its row is a reference AI fit without identity overrides
    (c as PaceCar).resolved = describeAiCar(probeJson, c.player ? null : ident.get(fieldKey(c)) ?? null, f.scale);
  }
  console.log(`\nworst error ${worst.toFixed(2)} %, ${((performance.now() - t0) / 1000).toFixed(1)} s with ${nWorkers} workers`);
  pace.ai_version = AI_VERSION;
  pace.calibrated = { ai_version: AI_VERSION, date: new Date().toISOString().slice(0, 10), tolerance: tol };
  if (!dry) { writeFileSync(pacePath(track), JSON.stringify(pace, null, 1) + '\n'); console.log(`wrote ${pacePath(track)}`); }
}
