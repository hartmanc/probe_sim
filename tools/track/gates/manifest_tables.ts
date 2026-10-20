// Evidence-manifest tables from a package and its eye-level inventory (21 Oct 2026): every scenery object of a physical
// kind with its source, and every inventory row with its outcome under the coverage gate (covered by which object,
// MISSING, dispositioned by the manifest (placed / assigned / rejected / not resolvable), skipped, or not a checked kind), so tools/track/compare/<id>/manifest.md can say
// what happened to each row and where each object comes from. Markdown on stdout.
//   npx tsx tools/track/gates/manifest_tables.ts <package dir> <inventory.json> [coverage_config.json]
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { coverage, objectNear, sceneryObjects, PHYSICAL, type Inventory } from './coverageGate';

const [dir, invPath, cfgPath] = process.argv.slice(2);
const track = JSON.parse(readFileSync(join(dir, 'track.json'), 'utf8'));
const sc = JSON.parse(readFileSync(join(dir, 'scenery.json'), 'utf8'));
const inv: Inventory = JSON.parse(readFileSync(invPath, 'utf8'));
const cfg = cfgPath ? JSON.parse(readFileSync(cfgPath, 'utf8')) : {};
const tol = cfg.tol ?? 15, L = track.n * track.spacing_m;
const objs = sceneryObjects(track, sc);
const rep = coverage(track, sc, inv, { tol, assigned: cfg.assigned, dispositions: cfg.dispositions });
const cell = (v: unknown) => String(v ?? '').replace(/\|/g, '/').replace(/\n/g, ' ');
const mmss = (t: number | null) => (t === null ? '' : `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, '0')}`);

console.log(`### Scenery objects of the checked kinds (${objs.length}, from ${dir})\n`);
console.log('| # | kind | side | s (m) | out (m) | object | source |');
console.log('|---|---|---|---|---|---|---|');
objs.forEach((o, k) => {
  const ss = o.pts.map((p) => p.s), out = o.pts.map((p) => p.out);
  const wrap = Math.max(...ss) - Math.min(...ss) > L / 2;
  const span = wrap ? `${Math.round(Math.min(...ss.filter((s) => s > L / 2)))}-${Math.round(Math.max(...ss.filter((s) => s <= L / 2)))} (wraps)` : `${Math.round(Math.min(...ss))}-${Math.round(Math.max(...ss))}`;
  console.log(`| ${k + 1} | ${o.kind} | ${o.side} | ${span} | ${Math.round(Math.min(...out))}-${Math.round(Math.max(...out))} | ${cell(o.label)} | ${cell(o.src)} |`);
});

console.log(`\n### Every inventory row and its outcome (${inv.rows.length} rows)\n`);
console.log('| s (m) | t | side | kind | what | source | outcome |');
console.log('|---|---|---|---|---|---|---|');
const miss = new Set(rep.missing.map((m) => `${m.s}|${m.kind}|${m.source}|${m.side}`));
const disp = new Map(rep.dispositioned.map((m) => [`${m.s}|${m.kind}|${m.source}|${m.side}`, `${m.disposition}: ${m.text}`] as const));
for (const r of inv.rows) {
  const a = r.attrs ?? {};
  const corr = a.correction ? ` (corrected in ${(a.correction as any).round}: ${Object.entries((a.correction as any).was).map(([k, v]) => `${k} was ${v ?? 'none'}`).join(', ')})` : '';
  const added = a.added ? ` (row added in ${a.added})` : '';
  let out: string;
  if ((r.scope ?? 'lap') === 'pit') out = r.kind === 'wall' ? 'pit-lane gate (pit_lane.walls)' : 'pit lane: not a checked kind for the lap';
  else if (!PHYSICAL.includes(r.kind)) out = 'surroundings (not a checked kind)';
  else if (r.side === 'ahead' && typeof a.ahead_m !== 'number') out = "skipped: 'ahead' without a distance";
  else {
    const sides = r.kind === 'bridge' || r.side === 'ahead' ? ['any'] : r.side === 'both' ? ['left', 'right'] : [r.side];
    const parts: string[] = [];
    for (const sd of sides) {
      const key = `${r.s}|${r.kind}|${r.source}|${sd === 'any' ? r.side : sd}`;
      if (disp.has(key)) { parts.push(`MISSING, ${disp.get(key)}${sides.length > 1 ? ` (${sd})` : ''}`); continue; }
      if (miss.has(key)) { parts.push(`MISSING${sides.length > 1 ? ` (${sd})` : ''}`); continue; }
      const near = objs.filter((o) => o.kind === r.kind && objectNear(o, r.s, sd === 'any' ? 'both' : (sd as any), tol, L));
      parts.push(`covered by ${near.slice(0, 2).map((o) => o.label).join('; ')}${sides.length > 1 ? ` (${sd})` : ''}`);
    }
    out = parts.join('; ');
  }
  console.log(`| ${r.s.toFixed(0)} | ${mmss(r.t)} | ${r.side} | ${r.kind} | ${cell(a.type ?? r.note ?? '')} | ${cell(r.source)} | ${cell(out + corr + added)} |`);
}
