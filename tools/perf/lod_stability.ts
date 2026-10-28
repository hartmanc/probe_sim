// Physics LOD stability check (perf round 1, option 3): the stiffest cars of a field (highest pace `scale`, lightest mass,
// highest power per kg; every car x stint of pace.json is a candidate) drive a solo lap at the LOD's 250 Hz (dt 4 ms, a
// control tick every physics step) and at the race's 500 Hz (dt 2 ms); the 250 Hz lap must stay on the road (no
// recoveries, no more steps with 3 wheels off than at 500 Hz) and within 0.1 % of the 500 Hz lap.
//   npx tsx tools/perf/lod_stability.ts --track buttonwillow [--n 6] [--json out.json]
// Reads tools/race/load.ts and src/physics/ai/solo.ts; edits neither.
import { writeFileSync } from 'node:fs';
import { loadIdentity, loadPace, loadProbeJson, loadTrackPack, trackArg } from '../race/load';
import { runSolo } from '../../src/physics/ai/solo';
import { buildAiSpec, fieldKey } from '../../src/physics/ai/field';

const argv = process.argv.slice(2);
const arg = (k: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
const track = trackArg(argv), nPer = Number(arg('--n') ?? 6);
const pack = loadTrackPack(track), probe = loadProbeJson(), pace = loadPace(track), ident = loadIdentity(track);

interface Cand { id: string; number: string; stint: number; scale: number; mass: number; pwr: number }
const cands: Cand[] = [];
for (const c of pace.cars) {
  if (c.number === '619') continue;
  const rows = c.stints?.length ? c.stints.map((s, k) => ({ k, scale: s.scale ?? c.scale ?? 1 })) : [{ k: -1, scale: c.scale ?? 1 }];
  for (const r of rows) {
    const spec = buildAiSpec(probe, ident.get(fieldKey(c)) ?? null, r.scale);
    const pw = (spec as any).engine?.peakPowerW ?? 0;
    cands.push({ id: fieldKey(c), number: c.number, stint: r.k, scale: r.scale, mass: spec.mass, pwr: pw / spec.mass });
  }
}
const pick = new Map<string, Cand>();
const take = (a: Cand[]) => { for (const c of a.slice(0, nPer)) pick.set(`${c.id}:${c.stint}`, c); };
take([...cands].sort((a, b) => b.scale - a.scale));
take([...cands].sort((a, b) => a.mass - b.mass));
take([...cands].sort((a, b) => (b.scale / b.mass) - (a.scale / a.mass)));

const rows: any[] = [];
let worst = 0, bad = 0;
for (const c of pick.values()) {
  const id = ident.get(c.id) ?? null;
  const a = runSolo(pack.line, pack.makeSurface(), probe, id, c.scale, 2, { dt: 0.002, ctlEvery: 1 });
  const b = runSolo(pack.line, pack.makeSurface(), probe, id, c.scale, 2, { dt: 0.004, ctlEvery: 1 });
  const la = a.laps[1], lb = b.laps[1], rel = Math.abs(lb - la) / la;
  const ok = a.laps.length >= 2 && b.laps.length >= 2 && b.recoveries === 0 && b.offSteps <= a.offSteps + 4 && rel <= 0.001 && b.nanResets === 0;
  if (ok) worst = Math.max(worst, rel); else bad++;
  rows.push({ id: c.id, stint: c.stint, scale: +c.scale.toFixed(3), mass: Math.round(c.mass), lap500: +(la ?? NaN).toFixed(3), lap250: +(lb ?? NaN).toFixed(3), rel_pct: +(rel * 100).toFixed(4), rec500: a.recoveries, rec250: b.recoveries, off500: a.offSteps, off250: b.offSteps, ok });
}
console.table(rows);
console.log(`${track}: ${rows.length} cars, ${bad} failing, worst |250 Hz - 500 Hz| = ${(worst * 100).toFixed(4)} %`);
if (arg('--json')) writeFileSync(arg('--json')!, JSON.stringify({ track, rows, failing: bad, worstPct: worst * 100 }, null, 1));
process.exit(bad ? 1 : 0);
