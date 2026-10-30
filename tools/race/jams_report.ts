// The combined jam report for NOTES ("Jams (30 Oct 2026)"): the real / sim slow-lap shares (jams_laps.ts) and the jam sections of several
// races side by side (jams_core.ts results: the owner's replay JSON and the self-play JSONs).
//   npx tsx tools/race/jams_report.ts --runs tools/race/out/traffic/runs/l10 <label>=<file.json> ... [--out file.md]
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { median, quantile } from './pace_rules';
import { ROOT } from './load';
import { lapsMd } from './jams_laps';
import type { JamsResult } from './jams_core';

const a = process.argv.slice(2);
const g = (k: string, d: string): string => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const files = a.filter((x) => /=/.test(x) && !x.startsWith('--')).map((x) => { const [label, f] = x.split('='); const j = JSON.parse(readFileSync(resolve(ROOT, f), 'utf8')); return { label, r: (j.analysis ? j.analysis.jams : j) as JamsResult }; });
const f1 = (x: number): string => (Number.isFinite(x) ? x.toFixed(1) : '-');
const f2 = (x: number): string => (Number.isFinite(x) ? x.toFixed(2) : '-');
const L: string[] = ['## Jams (30 Oct 2026): the tables', '', '### 1 and 2. Slow laps, real against sim', '', lapsMd(resolve(ROOT, g('--runs', 'tools/race/out/traffic/runs/l10'))), ''];
const cols = files.map((f) => f.label);
const row = (name: string, fn: (r: JamsResult) => string): string => `| ${name} | ${files.map((f) => fn(f.r)).join(' | ')} |`;
const head = (): string[] => [`| | ${cols.join(' | ')} |`, `|---|${cols.map(() => '---').join('|')}|`];
L.push('### 3. Jams by race', '', 'Jammed = an AI car on a straight or a corner exit at under 50 % of its own profile speed there, no mishap / off / recovery of its own, in green. Everything but the "first 40 s" row is after the first 40 s of green.', '', ...head());
L.push(row('AI cars', (r) => String(r.cars)), row('laps by the leader', (r) => f1(r.laps)));
L.push(row('jam car-seconds per race lap', (r) => f1(r.jamS / r.laps)), row('jam car-seconds per car-lap', (r) => f2(r.jamS / (r.cars * r.laps))), row('share of all car-time, %', (r) => f2(100 * r.jamS / (r.cars * (r.greenS - 40)))));
L.push(row('first 40 s of green: jam car-seconds (largest queue)', (r) => `${f1(r.start.jamS)} (${r.start.maxQueue})`));
const ds = (r: JamsResult) => r.episodes.map((e) => e.dur);
L.push(row('episodes per car-lap', (r) => f2(r.episodes.length / (r.cars * r.laps))), row('episodes of 3 s or more', (r) => String(r.episodes.filter((e) => e.dur >= 3).length)), row('episode duration median / p90 / max, s', (r) => `${f1(median(ds(r)))} / ${f1(quantile(ds(r), 0.9))} / ${f1(Math.max(0, ...ds(r)))}`));
L.push(row('queue size median / p90 / max', (r) => `${f1(median(r.queues))} / ${f1(quantile(r.queues, 0.9))} / ${Math.max(0, ...r.queues)}`), row('samples with a queue of 3 or more, %', (r) => f1(100 * r.queues.filter((x) => x >= 3).length / Math.max(1, r.queues.length))));
const byLap = (r: JamsResult, lap: (l: number) => boolean): number => r.episodes.filter((e) => lap(e.lap)).reduce((x, e) => x + e.dur, 0);
L.push(row('episode-seconds on lap 1 after the start window (share of all episode-seconds, %)', (r) => `${f1(byLap(r, (l) => l === 1))} (${f1(100 * byLap(r, (l) => l === 1) / Math.max(1, byLap(r, () => true)))})`), row('episode-seconds per lap on laps 2+', (r) => f1(byLap(r, (l) => l >= 2) / Math.max(1, r.laps - 1))));
L.push(row('car-seconds whose chain runs through a passing car, %', (r) => f1(100 * r.throughPass / r.jamS)));
L.push('', 'Head of the queue (the first car on the follow chain not itself capped by the car ahead): share of the jam car-seconds, %:', '', ...head());
const states = [...new Set(files.flatMap((f) => Object.keys(f.r.heads)))];
const tot = (r: JamsResult): number => Object.values(r.heads).reduce((x, y) => x + y, 0);
for (const s of states.sort((x, y) => files.reduce((n, f) => n + (f.r.heads[y] ?? 0) / tot(f.r), 0) - files.reduce((n, f) => n + (f.r.heads[x] ?? 0) / tot(f.r), 0))) L.push(row(s, (r) => f1(100 * (r.heads[s] ?? 0) / tot(r))));
L.push('', 'Top five 100 m stations (car-seconds per lap, place):', '', ...head());
for (let k = 0; k < 5; k++) L.push(row(String(k + 1), (r) => { const t = r.hist.map((x, b) => ({ x, b })).sort((p, q) => q.x - p.x)[k]; return `${t.b * 100}-${t.b * 100 + 100} m, ${r.histNames[t.b]}: ${f2(t.x / r.laps)}`; }));
L.push('', 'Ten worst episodes (duration x peak queue), one line each: t s / lap / car / station / place / s long / peak queue / head and its state / how it ended:', '');
for (const f of files) {
  L.push(`**${f.label}**`, '');
  for (const e of [...f.r.episodes].sort((p, q) => q.weight - p.weight).slice(0, 10)) L.push(`- ${f1(e.t0)} s, lap ${e.lap}, #${e.car}, s ${e.s} (${e.where}), ${f1(e.dur)} s, queue ${e.queue}, head #${e.head} (${e.headState}); ${e.ended}`);
  L.push('');
}
L.push('### 4. AI brake applications of 0.9 or more outside a braking zone (straight or corner exit): count per race lap / mean shockwave', '', 'Shockwave = cars within 250 m behind, not braking at the time, that brake at 0.5 or more on a straight or exit within the next 3 s.', '', ...head());
const reasons = [...new Set(files.flatMap((f) => f.r.brakes.map((b) => b.reason)))];
const cnt = (r: JamsResult, k: string): number => r.brakes.find((b) => b.reason === k)?.n ?? 0;
for (const k of reasons.sort((x, y) => files.reduce((n, f) => n + cnt(f.r, y), 0) - files.reduce((n, f) => n + cnt(f.r, x), 0))) L.push(row(k, (r) => { const b = r.brakes.find((q) => q.reason === k); return b ? `${f2(b.n / r.laps)} / ${f2(b.shock.reduce((x, y) => x + y, 0) / b.n)} (max ${Math.max(...b.shock)})` : '-'; }));
L.push(row('all', (r) => { const n = r.brakes.reduce((x, b) => x + b.n, 0), s = r.brakes.reduce((x, b) => x + b.shock.reduce((p, q) => p + q, 0), 0); return `${f2(n / r.laps)} / ${f2(s / Math.max(1, n))}`; }));
const md = L.join('\n') + '\n';
console.log(md);
if (g('--out', '')) writeFileSync(resolve(ROOT, g('--out', '')), md);
