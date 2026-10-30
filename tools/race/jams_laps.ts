// Jam measurement, sections 1 and 2 (30 Oct 2026): the share of green, non-pit, non-out car-laps that are slower than k x the car's own
// median lap (traffic_curves' outlier rule, k = 1.3 there), for the four real MyLaps events and for the sim's traffic_sim races, same code.
//   npx tsx tools/race/jams_laps.ts [--runs tools/race/out/traffic/runs/l10] [--out file.md]
// Measurement only: nothing here feeds the sim.
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { median, quantile } from './pace_rules';
import { ROOT } from './load';
import type { Crossing } from './traffic_curves';
import { EVENTS, loadEvent } from './traffic_data';

export const KS = [1.05, 1.1, 1.2, 1.3, 1.5] as const;
export interface Shares { cars: number; laps: number; over: number[]; incidentLaps: number; ratios: number[] }

/** Per car-lap shares. A lap counts when it is green, not a pit lap, not an out lap (the lap after a flagged lap or after one longer than
 *  1.5 x the median), not lap 1 (traffic_curves.pairsWithDrops `usable`); the car's own median = median of its green non-pit laps over minLap. */
export function lapShares(crossings: Crossing[], minLap: number, byStint = false): Shares {
  const byCar = new Map<string, Map<number, Crossing>>();
  for (const c of crossings) { let m = byCar.get(c.car); if (!m) byCar.set(c.car, m = new Map()); m.set(c.lapNr, c); }
  const over = KS.map(() => 0);
  let laps = 0, cars = 0, incidentLaps = 0;
  const ratios: number[] = [];
  for (const [, m] of byCar) {
    const all = [...m.values()].sort((a, b) => a.lapNr - b.lapNr);
    const med = median(all.filter((c) => c.green && !c.pit && c.lapTime > minLap).map((c) => c.lapTime));
    if (!Number.isFinite(med)) continue;
    cars++;
    // the median each lap is read against: the car's own, or (byStint) that of its stint = the laps between two pit laps
    const stintMed = new Map<number, number>();
    if (byStint) {
      let run: Crossing[] = [];
      const flush = (): void => { const mm = median(run.filter((c) => c.green && !c.pit && c.lapTime > minLap).map((c) => c.lapTime)); for (const c of run) stintMed.set(c.lapNr, mm); run = []; };
      for (const c of all) { if (c.pit) { flush(); continue; } run.push(c); }
      flush();
    }
    for (const c of m.values()) {
      if (c.pit || !c.green || !(c.lapTime > minLap) || c.lapNr <= 1) continue;
      const prev = m.get(c.lapNr - 1);
      if (!prev || prev.pit || prev.lapTime > 1.5 * med) continue;
      const ref = byStint ? stintMed.get(c.lapNr) ?? med : med;
      if (!Number.isFinite(ref)) continue;
      laps++;
      ratios.push(c.lapTime / ref);
      KS.forEach((k, i) => { if (c.lapTime > k * ref) over[i]++; });
      if (c.lapTime > 2 * ref) incidentLaps++;
    }
  }
  return { cars, laps, over, incidentLaps, ratios };
}
const pc = (x: number, d = 2): string => (100 * x).toFixed(d);
export const shareRow = (name: string, s: Shares): string => `| ${name} | ${s.cars} | ${s.laps} | ${KS.map((_, i) => `${pc(s.over[i] / s.laps)} % (${s.over[i]})`).join(' | ')} |`;
export const qRow = (name: string, s: Shares): string => `| ${name} | ${[0.5, 0.9, 0.95, 0.99, 0.999].map((q) => quantile(s.ratios, q).toFixed(3)).join(' | ')} |`;
export const QHEAD = ['| lap / reference lap | median | p90 | p95 | p99 | p99.9 |', '|---|---|---|---|---|---|'];
export const HEAD = [`| | cars | usable car-laps | ${KS.map((k) => `> ${k} x median`).join(' | ')} |`, `|---|---|---|${KS.map(() => '---').join('|')}|`];

export function realRows(byStint = false): { id: string; label: string; s: Shares }[] {
  return Object.keys(EVENTS).map((id) => ({ id, label: EVENTS[id].label, s: lapShares(loadEvent(id).crossings, 60, byStint) }));
}

/** The sim: per track pooled over the seeds in a runs dir, and the per-seed spread of the 1.3 share. */
export function simRows(runsDir: string, byStint = false): { track: string; s: Shares; perSeed: number[] }[] {
  const tracks = new Map<string, Shares>(), seeds = new Map<string, number[]>();
  for (const f of readdirSync(runsDir).filter((x) => x.endsWith('.json')).sort()) {
    const r = JSON.parse(readFileSync(resolve(runsDir, f), 'utf8')) as { track: string; seed: number; crossings: Crossing[] };
    const s = lapShares(r.crossings.map((c) => ({ ...c, car: `${r.seed}:${c.car}` })), 30, byStint);
    const t = tracks.get(r.track) ?? { cars: 0, laps: 0, over: KS.map(() => 0), incidentLaps: 0, ratios: [] };
    for (const x of s.ratios) t.ratios.push(x);
    t.cars += s.cars; t.laps += s.laps; t.incidentLaps += s.incidentLaps; s.over.forEach((v, i) => { t.over[i] += v; });
    tracks.set(r.track, t);
    (seeds.get(r.track) ?? seeds.set(r.track, []).get(r.track)!).push(s.over[3] / s.laps);
  }
  return [...tracks].map(([track, s]) => ({ track, s, perSeed: seeds.get(track)! }));
}

export function lapsMd(runsDir: string): string {
  const L: string[] = [];
  for (const [byStint, what] of [[false, "the car's own median lap (whole race)"], [true, "the median of the lap's own stint (laps between two pit laps)"]] as const) {
    L.push(`### Laps slower than k x ${what}`, '', 'Real (MyLaps), per event:', '', ...HEAD);
    for (const r of realRows(byStint)) L.push(shareRow(r.label, r.s));
    L.push('', 'Sim (traffic_sim, lane model, switch defaults, 10 laps), per track, pooled over the seeds:', '', ...HEAD.map((h) => h.replace('cars', 'car-races')));
    const sim = existsSync(runsDir) ? simRows(runsDir, byStint) : [];
    for (const r of sim) L.push(shareRow(r.track, r.s));
    L.push('', 'Quantiles of lap time over the reference lap (real, then sim):', '', ...QHEAD);
    for (const r of realRows(byStint)) L.push(qRow(r.label, r.s));
    for (const r of sim) L.push(qRow(`sim ${r.track}`, r.s));
    L.push('', 'Per-seed share over 1.3 x (min / median / max):', '');
    for (const r of sim) L.push(`- ${r.track}: ${pc(Math.min(...r.perSeed))} / ${pc(median(r.perSeed))} / ${pc(Math.max(...r.perSeed))} % over ${r.perSeed.length} seeds`);
    L.push('');
  }
  void quantile;
  return L.join('\n');
}

if (process.argv[1] && /jams_laps\.ts$/.test(process.argv[1])) {
  const a = process.argv.slice(2), g = (k: string, d: string) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
  const md = lapsMd(resolve(ROOT, g('--runs', 'tools/race/out/traffic/runs/l10')));
  console.log(md);
  if (g('--out', '')) writeFileSync(resolve(ROOT, g('--out', '')), md + '\n');
}
