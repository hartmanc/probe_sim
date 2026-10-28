// AI strength map check (AI round 1, Part B): for a sample of cars per track, the solo lap at the scale field.ts
// strengthPace gives for each strength against the intended lap (target / strength), and per track how many cars / stints
// the caps hold short of the 110 % lap.
//   npx tsx tools/race/strength_check.ts [--track <id>] [--pace <file>] [--n 6] [--strengths 0.9,1.1] [--workers 6]
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';
import { fileURLToPath } from 'node:url';
import { loadTrackPack, loadProbeJson, loadIdentity, pacePath, trackArg } from './load';
import { runSolo } from '../../src/physics/ai/solo';
import { fieldKey, strengthPace, type PaceJson } from '../../src/physics/ai/field';

interface Job { number: string; key: string; strength: number; scale: number; target: number; intended: number; predicted: number; capped: boolean }

if (!isMainThread) {
  const { track, jobs } = workerData as { track: string; jobs: Job[] };
  const pack = loadTrackPack(track), probe = loadProbeJson(), ident = loadIdentity(track);
  for (const j of jobs) {
    const r = runSolo(pack.line, pack.surface, probe, ident.get(j.key) ?? null, j.scale, 2);
    parentPort!.postMessage({ ...j, lap: r.laps.length >= 2 && r.recoveries === 0 ? r.laps[1] : NaN });
  }
} else {
  const argv = process.argv.slice(2);
  const arg = (k: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
  const track = trackArg(argv);
  const pace: PaceJson = JSON.parse(readFileSync(arg('--pace') ? resolve(arg('--pace')!) : pacePath(track), 'utf8'));
  const nSample = Number(arg('--n') ?? 6), workers = Number(arg('--workers') ?? 6);
  const strengths = (arg('--strengths') ?? '0.9,1.1').split(',').map(Number);
  const ai = pace.cars.filter((c) => !c.player && c.scale && c.achievedLap);
  // caps at 110 %: cars (car-level fit) and stints the map holds at PACE_MAX / short of the lap
  for (const st of [1.05, 1.1]) {
    let cars = 0, stints = 0, nSt = 0;
    for (const c of ai) {
      if (strengthPace(c.curve, c.scale!, c.achievedLap!, c.targetLap, st).capped) cars++;
      for (const s of c.stints ?? []) { nSt++; if (s.scale && strengthPace(c.curve, s.scale, s.achievedLap ?? s.targetLap, s.targetLap, st).capped) stints++; }
    }
    console.log(`${track} at ${Math.round(st * 100)} %: ${cars} of ${ai.length} cars (car-level pace) and ${stints} of ${nSt} stints at the caps`);
  }
  // sample: cars spread over the field's pace (car-level target), fastest to slowest
  const sorted = [...ai].sort((a, b) => a.targetLap - b.targetLap);
  const sample = Array.from({ length: nSample }, (_, k) => sorted[Math.round((k * (sorted.length - 1)) / Math.max(1, nSample - 1))]);
  const jobs: Job[] = [];
  for (const c of sample) for (const st of strengths) {
    const r = strengthPace(c.curve, c.scale!, c.achievedLap!, c.targetLap, st);
    jobs.push({ number: c.number, key: fieldKey(c), strength: st, scale: r.scale, target: c.targetLap, intended: c.targetLap / st, predicted: r.lap, capped: r.capped });
  }
  const res: (Job & { lap: number })[] = [];
  await new Promise<void>((done, fail) => {
    let live = 0;
    for (let w = 0; w < workers; w++) {
      const mine = jobs.filter((_, k) => k % workers === w);
      if (!mine.length) continue;
      live++;
      const wk = new Worker(fileURLToPath(import.meta.url), { workerData: { track, jobs: mine }, execArgv: ['--import', 'tsx'] });
      wk.on('message', (m) => res.push(m)); wk.on('error', fail); wk.on('exit', () => { if (--live === 0) done(); });
    }
    if (live === 0) done();
  });
  res.sort((a, b) => a.target - b.target || a.strength - b.strength);
  console.log('| track | car | target s | strength | scale | intended s | solo lap s | error % | capped |');
  console.log('|---|---|---|---|---|---|---|---|---|');
  for (const r of res) console.log(`| ${track} | ${r.number} | ${r.target.toFixed(2)} | ${Math.round(r.strength * 100)} % | ${r.scale.toFixed(4)} | ${r.intended.toFixed(2)} | ${Number.isFinite(r.lap) ? r.lap.toFixed(2) : 'off'} | ${((r.lap / r.intended - 1) * 100).toFixed(2)} | ${r.capped ? `yes (map ${r.predicted.toFixed(2)})` : ''} |`);
  const errs = res.filter((r) => !r.capped).map((r) => Math.abs(r.lap / r.intended - 1) * 100);
  if (errs.length) console.log(`worst |error| (uncapped) ${Math.max(...errs).toFixed(2)} %`);
}
