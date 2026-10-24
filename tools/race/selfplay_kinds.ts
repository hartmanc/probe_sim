// Station histogram and kinds of self-play rule events (contacts, four-offs) from selfplay --json files, with the track
// features at each place: kerb strips, cone lines, pit-exit cones, pit lane / paved-zone mouths (blends), wall ends.
//   npx tsx tools/race/selfplay_kinds.ts --track <id> [--bin 50] [--top 8] [--md] run1.json run2.json ...
// Contact kinds from the two cars' positions in the lane frame at the contact (selfplay_metrics contactAt: ds along the
// road, dl across, 1 m/s+ closing): rear-end |dl| < 1.0 m; side-by-side |ds| < 3.0 m and |dl| >= 1.0 m; else quarter (a
// nose into a rear corner: one car moving across the other's path). "on braking" when the place is a brake zone
// (selfplay_where), "in a corner" for entry / exit, "straight" otherwise.
import { readFileSync } from 'node:fs';
import { loadTrackPack, trackArg } from './load';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const track = trackArg(argv);
const BIN = Number(arg('--bin', '50')), TOP = Number(arg('--top', '8')), MD = argv.includes('--md');
const files = argv.filter((a, i) => a.endsWith('.json') && !['--track', '--bin', '--top'].includes(argv[i - 1]));
const pack = loadTrackPack(track);
const { line, scenery } = pack;
const L = line.L, CN = line.corners;
// the place of a station, as tools/race/selfplay_where.ts (brake / entry / exit / straight)
const fwd = (a: number, c: number) => { let d = c - a; while (d < 0) d += L; while (d >= L) d -= L; return d; };
function where(s: number): string {
  for (const c of CN) {
    const span = fwd(c.brake, c.apex), u = fwd(c.brake, s);
    if (u <= span) return `${c.name} ${u < span * 0.5 ? 'brake' : 'entry'}`;
    if (fwd(c.apex, s) <= 120 && fwd(c.apex, s) < fwd(c.apex, CN[(CN.indexOf(c) + 1) % CN.length].brake)) return `${c.name} exit`;
  }
  return 'straight';
}

// ---- track features by station
type Feat = { s0: number; s1: number; what: string };
const feats: Feat[] = [];
const proj = (p: ArrayLike<number>) => { const q = line.project(p[0], p[1]); return { s: q.s, lat: q.lateral }; };
const halfAt = (s: number, lat: number) => (lat >= 0 ? line.at(line.halfL, s) : line.at(line.halfR, s));
for (const k of scenery?.kerbs?.strips ?? []) feats.push({ s0: k.s0, s1: k.s1, what: `kerb ${k.side > 0 ? 'L' : 'R'}${k.kind && k.kind !== 'kerb' ? ' ' + k.kind : ''}` });
for (const k of scenery?.sausages?.strips ?? []) feats.push({ s0: k.s0, s1: k.s1, what: 'sausage' });
const pec = scenery?.pit_exit_cones;
if (pec?.pts?.length) { const a = proj(pec.pts[0]).s, b = proj(pec.pts[pec.pts.length - 1]).s; feats.push({ s0: Math.min(a, b), s1: Math.max(a, b), what: 'pit-exit cones' }); }
for (const c of scenery?.cone_lines ?? []) {
  if (!c?.pts?.length) continue;
  const ps = c.pts.map(proj).filter((q: { s: number; lat: number }) => Math.abs(q.lat) < halfAt(q.s, q.lat) + 4);
  if (!ps.length) continue;
  const ss = ps.map((q: { s: number }) => q.s);
  const near = Math.min(...ps.map((q: { s: number; lat: number }) => Math.abs(q.lat) - halfAt(q.s, q.lat)));
  feats.push({ s0: Math.min(...ss), s1: Math.max(...ss), what: `cone line (${near < 0 ? 'ON the road ' + (-near).toFixed(1) + ' m' : near.toFixed(1) + ' m off the edge'})` });
}
const mouth = (parts: any[] | undefined, kind: string) => {
  for (const p of parts ?? []) {
    const c = p.center; if (!c?.length) continue;
    for (const [end, pt] of [['start', c[0]], ['end', c[c.length - 1]]] as const) {
      const q = proj(pt); if (Math.abs(q.lat) > halfAt(q.s, q.lat) + 6) continue;
      feats.push({ s0: q.s - 15, s1: q.s + 15, what: `${kind}${p.turn ? ' "' + p.turn + '"' : ''} ${end} (blend)` });
    }
  }
};
mouth(scenery?.pit_lane?.parts, 'pit lane'); mouth(scenery?.paved_zones?.parts, 'paved zone');
for (const b of scenery?.barriers ?? []) {
  const pts = b.pts; if (!pts?.length) continue;
  for (const pt of [pts[0], pts[pts.length - 1]]) {
    const q = proj(pt); const gap = Math.abs(q.lat) - halfAt(q.s, q.lat);
    if (gap < 12) feats.push({ s0: q.s - 10, s1: q.s + 10, what: `wall end (${b.kind ?? 'barrier'}, ${gap.toFixed(1)} m off the ${q.lat >= 0 ? 'left' : 'right'} edge)` });
  }
}
const featsIn = (s0: number, s1: number) => [...new Set(feats.filter((f) => f.s1 >= s0 && f.s0 <= s1).map((f) => f.what))];

// ---- events
type C = { s: number; closing: number; ctx: string; ds?: number; dl?: number; a: string; b: string };
type F = { s: number; ctx: string; car: string };
let carLaps = 0; const cs: C[] = [], fs: F[] = [], rs: { s: number; t: number; car: string; phase: string }[] = [];
for (const f of files) { const m = JSON.parse(readFileSync(f, 'utf8')); carLaps += m.carLaps; cs.push(...m.rules.contactAt); fs.push(...m.rules.fourOffAt); rs.push(...(m.rules.recoveryAt ?? [])); }
const kind = (e: C) => {
  const ds = Math.abs(e.ds ?? 99), dl = Math.abs(e.dl ?? 0);
  const k = dl < 1.0 ? 'rear-end' : ds < 3.0 ? 'side-by-side' : 'quarter';
  const w = where(e.s);
  const ph = w.endsWith('brake') ? 'on braking' : w === 'straight' ? 'on a straight' : 'in a corner';
  return `${k} ${ph}`;
};
const bins = new Map<number, { c: C[]; f: F[] }>();
const b = (s: number) => Math.floor((((s % L) + L) % L) / BIN);
for (const e of cs) { const k = b(e.s); if (!bins.has(k)) bins.set(k, { c: [], f: [] }); bins.get(k)!.c.push(e); }
for (const e of fs) { const k = b(e.s); if (!bins.has(k)) bins.set(k, { c: [], f: [] }); bins.get(k)!.f.push(e); }
const tally = (xs: string[]) => { const m = new Map<string, number>(); for (const x of xs) m.set(x, (m.get(x) ?? 0) + 1); return [...m].sort((p, q) => q[1] - p[1]).map(([k, v]) => `${v} ${k}`).join(', '); };

console.log(`${track}: ${files.length} runs, ${carLaps.toFixed(0)} car-laps; contacts ${cs.length} = ${(cs.length / carLaps).toFixed(3)}/car-lap; four-off ${fs.length} = ${(fs.length / carLaps).toFixed(3)}/car-lap`);
console.log(`contact kinds: ${tally(cs.map(kind))}`);
console.log(`contact context (pass / line / off / passing-other): ${tally(cs.map((e) => e.ctx.split('/')[0]))}`);
console.log(`four-off context: ${tally(fs.map((e) => e.ctx.split('/')[0] + (e.ctx.split('/')[2] ? ' ' + e.ctx.split('/')[2] : '')))}`);
const rows = [...bins].map(([k, v]) => ({ s0: k * BIN, s1: (k + 1) * BIN, ...v })).sort((p, q) => (q.c.length * 2 + q.f.length) - (p.c.length * 2 + p.f.length));
const top = rows.slice(0, TOP);
if (MD) {
  console.log(`\n| station (m) | place | contacts | contact kinds | four-offs | four-off context | features (kerb, cones, blends, wall ends) |`);
  console.log('|---|---|---|---|---|---|---|');
}
for (const r of top) {
  const place = [...new Set([...r.c.map((e) => where(e.s)), ...r.f.map((e) => where(e.s))])].join(' / ');
  const kinds = tally(r.c.map(kind)), fctx = tally(r.f.map((e) => e.ctx.split('/')[0] + ' ' + (e.ctx.split('/')[2] ?? ''))), ft = featsIn(r.s0, r.s1).join('; ') || '-';
  if (MD) console.log(`| ${r.s0}-${r.s1} | ${place} | ${r.c.length} | ${kinds || '-'} | ${r.f.length} | ${fctx || '-'} | ${ft} |`);
  else console.log(`s ${String(r.s0).padStart(5)}-${String(r.s1).padEnd(5)} ${place.padEnd(28)} contacts ${r.c.length} [${kinds}]  four-off ${r.f.length} [${fctx}]  features: ${ft}`);
}
if (rs.length) {
  const rb = new Map<number, number>(); for (const r of rs) rb.set(b(r.s), (rb.get(b(r.s)) ?? 0) + 1);
  console.log(`\nmarshal resets ${rs.length} (${rs.filter((r) => r.phase === 'green').length} in green; station after the reset): ` + [...rb].sort((p, q) => q[1] - p[1]).slice(0, TOP).map(([k, v]) => `${v} at s ${k * BIN}-${(k + 1) * BIN} (${where(k * BIN + BIN / 2)}; ${featsIn(k * BIN, (k + 1) * BIN).join('; ') || '-'})`).join(' | '));
}
if (argv.includes('--features')) for (const f of feats.sort((p, q) => p.s0 - q.s0)) console.log(`  feat ${f.s0.toFixed(0)}-${f.s1.toFixed(0)} ${f.what}`);
