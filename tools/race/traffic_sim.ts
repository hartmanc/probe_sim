// The traffic yardstick in the sim (traffic round, 28 Oct 2026): self-play races (the player's car AI-driven, as selfplay.ts)
// record every line crossing (RaceDirector.crossings); the crossings go through tools/race/traffic_curves.ts exactly as the
// MyLaps data did (tools/race/traffic_data.ts), so the sim's pass rate by pace delta and gap and its time lost per lap
// compare cell for cell with tools/race/data/traffic/curves.json.
//   one race:  npx tsx tools/race/traffic_sim.ts --track <id> --laps 10 --seed S [--json out.json] [--set key=value ...]
//   a set:     npx tsx tools/race/traffic_sim.ts --tracks all --seeds 1-8 --workers 6 [--laps 10] [--set key=value ...]
//              [--runs <dir>] [--compare tools/race/data/traffic/curves.json] [--save tools/race/out/traffic/<name>]
// A set runs each (track, seed) in its own process (`--workers` at a time), caches each race's JSON in --runs (default
// tools/race/out/traffic/runs/<tag>, tag from the --set values and laps) and pools. One stint = the whole race; a car's ref =
// quantile 0.2 of its usable laps by the module's own rules (green, not lap 1, <= 1.3 x its median); lap 1 is excluded by the
// module, as in the data. `--set` passes RaceConfig fields (numbers / booleans) to the director (A/B of a switch).
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { curves, pairsWithDrops, wilson, type Crossing, type Curves, type Pair, type StintRef, D_BINS, G_BINS } from './traffic_curves';
import { median, quantile } from './pace_rules';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const sets = argv.flatMap((a, i) => (a === '--set' ? [argv[i + 1]] : []));
export const ALL_TRACKS = ['laguna_seca', 'sonoma', 'buttonwillow', 'mid_ohio'];

export interface RunOut {
  track: string; seed: number; laps: number; set: string[];
  crossings: Crossing[];
  metrics: { carLaps: number; contacts: number; contactsPerCarLap: number; fourOff: number; fourOffPerCarLap: number; fourOffNonMishapPerCarLap: number; passesTotal: number;
    situations: number; completed: number; defending: { vsClearlyFaster: number; within3: number; vsSlower: number; none: number }; recoveries: number; mishaps: number;
    contactAt: unknown[]; fourOffAt: unknown[]; yields?: number };
}

const parseSet = (kv: string[]): Record<string, number | boolean | string> => Object.fromEntries(kv.map((s) => { const [k, v] = s.split('='); return [k, v === 'true' ? true : v === 'false' ? false : Number.isNaN(Number(v)) ? v : Number(v)]; }));   // (a word stays a string: planner=offset)

async function runOne(): Promise<void> {
  const { createCollisionWorld } = await import('../../src/physics/index');
  const { RaceDirector } = await import('../../src/physics/ai/race');
  const { loadTrackPack, loadProbeJson, loadPace, loadIdentityJson, trackArg } = await import('./load');
  const { runSelfplay } = await import('./selfplay_metrics');
  const { TRACKS } = await import('../../src/scoreboard/config');
  const track = trackArg(argv), laps = Number(arg('--laps', '10')), seed = Number(arg('--seed', '1'));
  const pack = loadTrackPack(track);
  const ai = TRACKS[track]?.ai ?? {};
  const dir = new RaceDirector({
    line: pack.line, surface: pack.surface, makeSurface: pack.makeSurface, probeJson: loadProbeJson(), pace: loadPace(track), identity: loadIdentityJson(track),
    pitLane: pack.scenery?.pit_lane ?? null, blendLine: pack.scenery?.blend_line ?? null, collisionWorld: createCollisionWorld(pack.scenery, pack.track),
  }, { laps, seed, playerAi: true, followScale: ai.followScale ?? 1, laneMargin: ai.laneMargin ?? 1, shiftGrip: ai.shiftGrip ?? 0, ...parseSet(sets) });
  const m = runSelfplay(dir, pack.makeSurface(), { log: false });
  const r = m.rules;
  const out: RunOut = {
    track, seed, laps, set: sets, crossings: dir.crossings.map((c) => ({ ...c })),
    metrics: { carLaps: m.carLaps, contacts: r.contacts, contactsPerCarLap: r.contactsPerCarLap, fourOff: r.fourOff, fourOffPerCarLap: r.fourOffPerCarLap, fourOffNonMishapPerCarLap: r.fourOffNonMishapPerCarLap,
      passesTotal: m.passing.passesTotal, situations: m.passing.situations, completed: m.passing.completed, defending: m.defending, recoveries: r.recoveries, mishaps: m.mishaps.total,
      contactAt: r.contactAt, fourOffAt: r.fourOffAt, yields: undefined },
  };
  const js = arg('--json', '');
  if (js) writeFileSync(js, JSON.stringify(out)); else console.log(JSON.stringify(out.metrics));
}

/** One stint per car (the whole race): ref = quantile 0.2 of its usable laps (traffic_curves' rules: green, not lap 1, not after
 *  an untimed / pit lap, <= 1.3 x its median of green laps). */
export function simRefs(cr: Crossing[], cut = 1.3): StintRef[] {
  const by = new Map<string, Crossing[]>();
  for (const c of cr) { let a = by.get(c.car); if (!a) by.set(c.car, a = []); a.push(c); }
  const refs: StintRef[] = [];
  for (const [car, a] of by) {
    const lap = new Map(a.map((c) => [c.lapNr, c]));
    const green = a.filter((c) => c.green && !c.pit && c.lapTime > 0).map((c) => c.lapTime);
    if (!green.length) continue;
    const med = median(green);
    const ok = a.filter((c) => { const p = lap.get(c.lapNr - 1); return c.lapNr > 1 && c.green && !c.pit && p && !p.pit && c.lapTime <= cut * med; }).map((c) => c.lapTime);
    if (!ok.length) continue;
    refs.push({ car, fromLap: 0, toLap: 1e9, ref: quantile(ok, 0.2) });
  }
  return refs;
}

export function runPairs(r: RunOut): Pair[] {
  const tag = `${r.track}:${r.seed}:`;
  const cr = r.crossings.map((c) => ({ ...c, car: tag + c.car }));
  return pairsWithDrops(cr, simRefs(cr), { minLap: 30 }).pairs;
}

const pct = (x: number) => (Number.isFinite(x) ? (100 * x).toFixed(1) : '-');
const f1 = (x: number) => (Number.isFinite(x) ? x.toFixed(1) : '-');

/** The gate cells (G1, G2) of a pooled sim curve against the data's. */
export function compareRows(sim: Curves, data: Curves): string[] {
  const L: string[] = ['| d (g < 2 s) | data | sim (n; Wilson 90 %) | delta pp |', '|---|---|---|---|'];
  for (let k = 0; k < D_BINS.length; k++) {
    const a = data.byD[k], b = sim.byD[k];
    L.push(`| ${D_BINS[k]} | ${pct(a.rate)} | ${pct(b.rate)} (${b.n}; ${pct(b.lo)}-${pct(b.hi)}) | ${f1(100 * (b.rate - a.rate))} |`);
  }
  L.push('', '| g (d >= 3 %) | data | sim (n; Wilson 90 %) | delta pp |', '|---|---|---|---|');
  for (let k = 0; k < G_BINS.length; k++) {
    const a = data.byG[k], b = sim.byG[k];
    L.push(`| ${G_BINS[k]} | ${pct(a.rate)} | ${pct(b.rate)} (${b.n}; ${pct(b.lo)}-${pct(b.hi)}) | ${f1(100 * (b.rate - a.rate))} |`);
  }
  L.push('', '| d (g < 2 s) | stuck: data / sim (n) | passed lap: data / sim (n) | pulledAway: data / sim (n) |', '|---|---|---|---|');
  for (let k = 0; k < D_BINS.length; k++) {
    const a = data.lostByD[k], b = sim.lostByD[k];
    L.push(`| ${D_BINS[k]} | ${f1(a.stuck.med)} / ${f1(b.stuck.med)} (${b.stuck.n}) | ${f1(a.passed.med)} / ${f1(b.passed.med)} (${b.passed.n}) | ${f1(a.pulledAway.med)} / ${f1(b.pulledAway.med)} (${b.pulledAway.n}) |`);
  }
  return L;
}

/** G1 / G2 verdicts (pooled). */
export function gates(sim: Curves, data: Curves): { g1: boolean; g2: boolean; notes: string[] } {
  const notes: string[] = [];
  let g1 = true, g2 = true;
  const tolD = [NaN, 8, 6, 6, 6, 6];
  for (let k = 1; k < 6; k++) { const dd = 100 * (sim.byD[k].rate - data.byD[k].rate); if (!(Math.abs(dd) <= tolD[k])) { g1 = false; notes.push(`G1 d ${D_BINS[k]}: ${f1(dd)} pp`); } }
  if (!(sim.byD[0].rate <= 0.12)) { g1 = false; notes.push(`G1 floor ${pct(sim.byD[0].rate)} %`); }
  for (const k of [3, 4, 5]) { const dd = 100 * (sim.byG[k].rate - data.byG[k].rate); if (!(Math.abs(dd) <= 8)) { g1 = false; notes.push(`G1 g ${G_BINS[k]}: ${f1(dd)} pp`); } }
  const within = (s: number, d: number) => Math.abs(s - d) <= Math.max(0.35 * d, 1.5);
  for (let k = 1; k < 5; k++) {
    const a = data.lostByD[k], b = sim.lostByD[k];
    if (b.stuck.n >= 5 && !within(b.stuck.med, a.stuck.med)) { g2 = false; notes.push(`G2 stuck d ${D_BINS[k]}: ${f1(b.stuck.med)} vs ${f1(a.stuck.med)}`); }
    if (b.passed.n >= 5 && !within(b.passed.med, a.passed.med)) { g2 = false; notes.push(`G2 passed d ${D_BINS[k]}: ${f1(b.passed.med)} vs ${f1(a.passed.med)}`); }
  }
  return { g1, g2, notes };
}

async function runSet(): Promise<void> {
  const tracks = arg('--tracks', 'all') === 'all' ? ALL_TRACKS : arg('--tracks', '').split(',');
  const [s0, s1] = arg('--seeds', '1-8').split('-').map(Number);
  const laps = Number(arg('--laps', '10')), workers = Number(arg('--workers', '6'));
  const tag = arg('--tag', `l${laps}` + (sets.length ? '_' + sets.join('_').replace(/[^a-zA-Z0-9.=_-]/g, '') : ''));
  const runsDir = resolve(ROOT, arg('--runs', `tools/race/out/traffic/runs/${tag}`));
  mkdirSync(runsDir, { recursive: true });
  const jobs: { track: string; seed: number; file: string }[] = [];
  for (const track of tracks) for (let s = s0; s <= (s1 ?? s0); s++) jobs.push({ track, seed: s, file: resolve(runsDir, `${track}_${s}.json`) });
  const skip = new Set(arg('--skip', '').split(',').filter(Boolean));   // track_seed jobs another process is running
  const todo = (argv.includes('--force') ? jobs : jobs.filter((j) => !existsSync(j.file))).filter((j) => !skip.has(`${j.track}_${j.seed}`));
  // the biggest fields first (Sonoma 134 cars, Buttonwillow 100) so the pool ends together
  const weight: Record<string, number> = { sonoma: 4, buttonwillow: 3, mid_ohio: 2, laguna_seca: 1 };
  todo.sort((a, b) => (weight[b.track] ?? 0) - (weight[a.track] ?? 0));
  const tsx = resolve(ROOT, 'node_modules/.bin/tsx');
  let next = 0, done = 0;
  const t0 = Date.now();
  await new Promise<void>((res, rej) => {
    if (!todo.length) { res(); return; }
    const launch = (): void => {
      if (next >= todo.length) return;
      const j = todo[next++];
      const p = spawn(tsx, [fileURLToPath(import.meta.url), '--track', j.track, '--seed', String(j.seed), '--laps', String(laps), '--json', j.file, ...sets.flatMap((s) => ['--set', s])], { cwd: ROOT, stdio: ['ignore', 'ignore', 'inherit'] });
      p.on('exit', (code) => {
        if (code !== 0) { rej(new Error(`${j.track} seed ${j.seed} exited ${code}`)); return; }
        done++;
        console.error(`  ${j.track} seed ${j.seed} done (${done}/${todo.length}, ${((Date.now() - t0) / 1000).toFixed(0)} s)`);
        if (done === todo.length) res(); else launch();
      });
    };
    for (let w = 0; w < Math.min(workers, todo.length); w++) launch();
  });
  if (skip.size) { console.error('skipped jobs: pool later'); return; }
  const runs: RunOut[] = jobs.map((j) => JSON.parse(readFileSync(j.file, 'utf8')));
  report(runs, tracks, laps, `${s0}-${s1 ?? s0}`);
}

function report(runs: RunOut[], tracks: string[], laps: number, seeds: string): void {
  const dataPath = arg('--compare', 'tools/race/data/traffic/curves.json');
  const data = JSON.parse(readFileSync(resolve(ROOT, dataPath), 'utf8'));
  const dataPooled: Curves = data.pooled.curves;
  const dataEv = (t: string): Curves | null => { const id = t === 'laguna_seca' ? 'laguna' : t; return data.events?.[id]?.curves ?? null; };
  const all: Pair[] = [];
  const per: Record<string, { pairs: Pair[]; carLaps: number; contacts: number; fourOff: number; fourOffNM: number; passes: number; vsCF: number; within3: number; situations: number; completed: number; seeds: { seed: number; contacts: number; fourOff: number; passes: number }[] }> = {};
  for (const r of runs) {
    const ps = runPairs(r);
    all.push(...ps);
    const P = per[r.track] ??= { pairs: [], carLaps: 0, contacts: 0, fourOff: 0, fourOffNM: 0, passes: 0, vsCF: 0, within3: 0, situations: 0, completed: 0, seeds: [] };
    P.pairs.push(...ps);
    const m = r.metrics;
    P.carLaps += m.carLaps; P.contacts += m.contacts; P.fourOff += m.fourOff; P.fourOffNM += m.fourOffNonMishapPerCarLap * m.carLaps; P.passes += m.passesTotal;
    P.vsCF += m.defending.vsClearlyFaster; P.within3 += m.defending.within3; P.situations += m.situations; P.completed += m.completed;
    P.seeds.push({ seed: r.seed, contacts: +m.contactsPerCarLap.toFixed(4), fourOff: +m.fourOffPerCarLap.toFixed(4), passes: m.passesTotal });
  }
  const pooled = curves(all);
  const g = gates(pooled, dataPooled);
  const L: string[] = [`# Traffic yardstick: ${tracks.join(', ')}, seeds ${seeds}, ${laps} laps${sets.length ? ', ' + sets.join(' ') : ''}`, '', `${all.length} pairs pooled. G1 ${g.g1 ? 'PASS' : 'FAIL'}, G2 ${g.g2 ? 'PASS' : 'FAIL'}${g.notes.length ? ': ' + g.notes.join('; ') : ''}`, '', '## Pooled', '', ...compareRows(pooled, dataPooled), '', '## Rules and passes per track (sum over seeds)', '',
    '| track | car-laps | contacts / car-lap | four-off / car-lap (non-mishap) | green passes | clearly-faster completed | defending vs clearly faster / within 3 % |', '|---|---|---|---|---|---|---|'];
  const perOut: Record<string, unknown> = {};
  for (const t of tracks) {
    const P = per[t]; if (!P) continue;
    L.push(`| ${t} | ${P.carLaps.toFixed(0)} | ${(P.contacts / P.carLaps).toFixed(4)} | ${(P.fourOff / P.carLaps).toFixed(4)} (${(P.fourOffNM / P.carLaps).toFixed(4)}) | ${P.passes} | ${pct(P.completed / P.situations)} % | ${P.vsCF} / ${P.within3} |`);
  }
  for (const t of tracks) {
    const P = per[t]; if (!P) continue;
    const c = curves(P.pairs), d = dataEv(t);
    L.push('', `## ${t} (${P.pairs.length} pairs)`, '', ...(d ? compareRows(c, d) : []));
    perOut[t] = { pairs: P.pairs.length, carLaps: P.carLaps, contactsPerCarLap: P.contacts / P.carLaps, fourOffPerCarLap: P.fourOff / P.carLaps, fourOffNonMishapPerCarLap: P.fourOffNM / P.carLaps, passesTotal: P.passes, clearlyFasterCompleted: P.completed / P.situations, defendingVsClearlyFaster: P.vsCF, defendingWithin3: P.within3, seeds: P.seeds, curves: { byD: c.byD, byG: c.byG, lostByD: c.lostByD } };
  }
  const md = L.join('\n');
  console.log(md);
  const save = arg('--save', '');
  if (save) {
    const base = resolve(ROOT, save);
    mkdirSync(dirname(base), { recursive: true });
    writeFileSync(base + '.md', md + '\n');
    writeFileSync(base + '.json', JSON.stringify({ tracks, seeds, laps, set: sets, gates: g, pooled: { pairs: all.length, byD: pooled.byD, byG: pooled.byG, lostByD: pooled.lostByD, pressure: pooled.pressure, groups: pooled.groups }, perTrack: perOut }, null, 1));
  }
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  if (argv.includes('--tracks') || argv.includes('--seeds')) runSet().catch((e) => { console.error(e); process.exit(1); });
  else runOne().catch((e) => { console.error(e); process.exit(1); });
}
void wilson;
