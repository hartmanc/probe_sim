// Trial table from selfplay --json files: tools/race/out/<prefix>_<tag>_s<seed>.json, one row per tag, the seeds pooled
// (per-seed values in brackets). Race time and median best lap / drawn target per seed; --exclude s0-s1 adds the
// contacts outside a station window (a place knobs cannot fix, e.g. Sonoma T7 brake 2040-2110).
//   npx tsx tools/race/selfplay_table.ts [--dir tools/race/out] [--exclude 2040-2110] <prefix> <tag> [<tag> ...]
import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { ROOT } from './load';

const argv = process.argv.slice(2);
const opt = (k: string) => { const i = argv.indexOf(k); if (i < 0) return null; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const dir = resolve(ROOT, opt('--dir') ?? 'tools/race/out');
const ex = opt('--exclude')?.split('-').map(Number) ?? null;
const [prefix, ...tags] = argv;
type M = { carLaps: number; raceTime: number; rules: { contacts: number; fourOff: number; recoveries: number; contactsPerCarLap: number; fourOffPerCarLap: number; contactAt: { s: number }[] };
  passing: { completed: number; situations: number }; pace?: { bestOverTarget: number; followScale: number; laneMargin: number; shiftGrip: number } };
const f3 = (x: number) => x.toFixed(3);
console.log(`| trial | knobs (followScale / laneMargin / shiftGrip) | seeds | contacts / car-lap | ${ex ? `contacts outside ${ex[0]}-${ex[1]} | ` : ''}four-off / car-lap | recoveries | race time (s) | median best lap / target | clearly-faster passes |`);
console.log(`|---|---|---|---|${ex ? '---|' : ''}---|---|---|---|---|`);
for (const tag of tags) {
  const names = readdirSync(dir).filter((f) => f.startsWith(`${prefix}_${tag}_s`) && f.endsWith('.json')).sort();
  const ms: M[] = names.map((f) => JSON.parse(readFileSync(resolve(dir, f), 'utf8')));
  if (!ms.length) continue;
  const cl = ms.reduce((a, m) => a + m.carLaps, 0), c = ms.reduce((a, m) => a + m.rules.contacts, 0), fo = ms.reduce((a, m) => a + m.rules.fourOff, 0);
  const out = ms.reduce((a, m) => a + m.rules.contactAt.filter((e) => !ex || e.s < ex[0] || e.s > ex[1]).length, 0);
  const ps = ms.reduce((a, m) => a + m.passing.completed, 0), sit = ms.reduce((a, m) => a + m.passing.situations, 0);
  const k = ms[0].pace; const knobs = k ? `${k.followScale} / ${k.laneMargin} / ${k.shiftGrip}` : '-';
  const per = (g: (m: M) => number) => ms.map((m) => f3(g(m))).join(' / ');
  console.log(`| ${tag} | ${knobs} | ${names.map((n) => n.replace(/.*_s(\d+)\.json$/, '$1')).join(', ')} | **${f3(c / cl)}** (${per((m) => m.rules.contactsPerCarLap)}) | ${ex ? `${f3(out / cl)} | ` : ''}**${f3(fo / cl)}** (${per((m) => m.rules.fourOffPerCarLap)}) | ${ms.map((m) => m.rules.recoveries).join(' / ')} | ${ms.map((m) => m.raceTime.toFixed(0)).join(' / ')} | ${ms.map((m) => m.pace ? m.pace.bestOverTarget.toFixed(3) : '-').join(' / ')} | ${(100 * ps / Math.max(1, sit)).toFixed(1)} % |`);
}
