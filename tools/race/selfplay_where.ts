// Where self-play rule events happen: bins contacts and four-offs from selfplay --json files by corner phase
// (brake zone, entry to apex, exit to apex+120 m, straight) and by context.
//   npx tsx tools/race/selfplay_where.ts --track <id> run1.json run2.json ...
import { readFileSync } from 'node:fs';
import { loadTrackPack, trackArg } from './load';

const argv = process.argv.slice(2);
const track = trackArg(argv);
const files = argv.filter((a, i) => a.endsWith('.json') && argv[i - 1] !== '--track');
const { line } = loadTrackPack(track);
const L = line.L, C = line.corners;
const fwd = (a: number, b: number) => { let d = b - a; while (d < 0) d += L; while (d >= L) d -= L; return d; };
export function where(s: number): string {
  for (const c of C) {
    const span = fwd(c.brake, c.apex), u = fwd(c.brake, s);
    if (u <= span) return `${c.name} ${u < fwd(c.brake, c.apex) * 0.5 ? 'brake' : 'entry'}`;
    if (fwd(c.apex, s) <= 120 && fwd(c.apex, s) < fwd(c.apex, C[(C.indexOf(c) + 1) % C.length].brake)) return `${c.name} exit`;
  }
  return 'straight';
}
const tally = (m: Map<string, number>, k: string) => m.set(k, (m.get(k) ?? 0) + 1);
const byC = new Map<string, number>(), byCctx = new Map<string, number>(), byF = new Map<string, number>(), byFctx = new Map<string, number>();
let carLaps = 0, nC = 0, nF = 0;
const rows: string[] = [];
for (const f of files) {
  const m = JSON.parse(readFileSync(f, 'utf8'));
  carLaps += m.carLaps;
  for (const e of m.rules.contactAt) { nC++; const w = where(e.s); tally(byC, w); tally(byCctx, w + ' | ' + e.ctx.split('/')[0]); rows.push(`C ${f.split('/').pop()} s${e.s} ${w} ${e.a}-${e.b} cl${e.closing} ${e.ctx} ph${e.phase} ds${e.ds} dl${e.dl}`); }
  for (const e of m.rules.fourOffAt) { nF++; const w = where(e.s); tally(byF, w); tally(byFctx, w + ' | ' + e.ctx.split('/')[0]); }
}
const show = (t: string, m: Map<string, number>) => { console.log(t); for (const [k, v] of [...m].sort((a, b) => b[1] - a[1])) console.log(`  ${String(v).padStart(4)}  ${k}`); };
console.log(`${files.length} runs, ${carLaps.toFixed(0)} car-laps; contacts ${nC} = ${(nC / carLaps).toFixed(3)}/car-lap; four-off ${nF} = ${(nF / carLaps).toFixed(3)}/car-lap`);
console.log('corners: ' + C.map((c) => `${c.name} brake ${c.brake.toFixed(0)} apex ${c.apex.toFixed(0)} dir ${c.dir}${c.passable ? ' P' : ''}`).join('; '));
show('contacts by place', byC); show('contacts by place | ctx', byCctx); show('four-off by place', byF); show('four-off by place | ctx', byFctx);
if (argv.includes('--rows')) for (const r of rows) console.log(r);
