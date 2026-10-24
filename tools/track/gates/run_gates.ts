// CLI of the stage-3 scenery gates (sceneryGates.ts): npx tsx tools/track/gates/run_gates.ts <package dir> [gate config json]
// Prints the three reports and a JSON summary line; exits 1 when a gate fails.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { containment, escapeRuns, exposedEnds, joinFaces, pitConnectivity, runGaps, sideBySide, signPlacement, tyreFaces, wallTops, type GateConfig } from './sceneryGates';
import { terrainGates } from './terrainGates';
import { groundMarksGate, MARKS_TOL } from './groundMarks';
import { loadHeightfield } from '../../../src/physics/index';

const dir = process.argv[2];
const cfg: GateConfig & { pit_box_s?: number; openings?: { x: number; y: number; why: string }[] } = process.argv[3] ? JSON.parse(readFileSync(process.argv[3], 'utf8')) : {};
const track = JSON.parse(readFileSync(join(dir, 'track.json'), 'utf8'));
const sc = JSON.parse(readFileSync(join(dir, 'scenery.json'), 'utf8'));
let fail = false;

const c = containment(track, sc, cfg);
const runs = escapeRuns(c.escapes);
console.log(`[${runs.length ? 'FAIL' : 'ok'}] containment: ${c.rays} rays (normal, +-35 deg, every ${cfg.step ?? 2} m, ${cfg.reach ?? 120} m), `
  + `${c.escapes.length} escapes in ${runs.length} runs, ${c.allowed.length} onto allowed runoff, ${c.junctions} pit-lane junction hits`);
for (const r of runs) console.log(`       escape ${r.side.padEnd(5)} s ${r.s0.toFixed(0)}-${r.s1.toFixed(0)} -> ${r.target} (${r.n} rays, nearest ${r.dmin.toFixed(1)} m beyond the edge)`);
const al = escapeRuns(c.allowed);
for (const r of al) console.log(`       allowed ${r.side.padEnd(5)} s ${r.s0.toFixed(0)}-${r.s1.toFixed(0)} -> ${r.target} (${r.n} rays)`);
if (runs.length) fail = true;

const p = pitConnectivity(track, sc, cfg.pit_box_s);
console.log(`[${p.ok ? 'ok' : 'FAIL'}] pit connectivity: ${p.paths.length ? p.paths.map((q) => `${q.name}: ${q.length} m, ${q.crossings.length} barrier crossings, ${q.unpaved_m} m unpaved, ${q.cones} cone-line crossings`).join('; ') : 'no pit lane'}`);
for (const q of p.paths) for (const x of q.crossings.slice(0, 5)) console.log(`       ${q.name}: crosses ${x}`);
if (p.lane) {
  console.log(`       lane (two paths 1.5 m from each edge, 1.0 m clearance, cone lines count): ${p.lane.stations} stations, ${p.lane.blocked.length} obstacles, ${p.lane.pinched.length} pinched stations`);
  for (const x of p.lane.blocked.slice(0, 12)) console.log(`       lane blocked: ${x}`);
  if (p.lane.pinched.length) console.log(`       lane pinched (< 3 m between closed edges) at s ${[...new Set(p.lane.pinched)].slice(0, 20).join(', ')}`);
}
if (!p.ok) fail = true;

const g = signPlacement(track, sc, cfg);
console.log(`[${g.bad.length ? 'FAIL' : 'ok'}] sign placement: ${g.checked} signs, boards and posts checked, ${g.bad.length} misplaced`);
for (const b of g.bad) console.log(`       ${b.kind} '${b.text}' at (${b.x.toFixed(1)}, ${b.y.toFixed(1)}): ${b.why}`);
if (g.bad.length) fail = true;

const e = exposedEnds(track, sc);
console.log(`[${e.exposed.length ? 'FAIL' : 'ok'}] wall ends: ${e.checked} upstream run ends within 30 m (tyre runs 8 m) of an edge checked, ${e.ok.length} joined / cushioned / lapped / tapered, ${e.exposed.length} exposed to oncoming travel`);
for (const x of e.exposed) console.log(`       exposed ${x.side.padEnd(5)} s ${x.s} (${x.out} m out): ${x.label}`);
if (e.exposed.length) fail = true;
const sb = sideBySide(track, sc);
console.log(`[${sb.length ? 'FAIL' : 'ok'}] tyre facings: ${sb.length} tyre runs standing 0.8-2.5 m off a wall side by side (a tyre run beside a wall must face it, within 0.8 m, or meet it end to end)`);
for (const x of sb) console.log(`       side by side s ${x.s} (${x.off} m off): ${x.tyre} | ${x.wall}`);
if (sb.length) fail = true;

// round 12 (Sonoma judge r11 N65 / N67): wall tops without steps and boards on them, flush wall-tyre joins, tyre faces off the road
const wt = wallTops(track, sc);
const wtBad = wt.steps.length + wt.boards.length;
console.log(`[${wtBad ? 'FAIL' : 'ok'}] wall tops: ${wt.checked} concrete / pit-wall / Armco runs, top line steeper than 0.5 m per m in ${wt.steps.length}; `
  + `${wt.boardsChecked} wall boards, ${wt.boards.length} off their wall's top by more than 0.10 m`);
for (const x of wt.steps) console.log(`       step s ${x.s}: ${x.dz} m at ${x.slope} m per m: ${x.label}`);
for (const x of wt.boards) console.log(`       board '${x.text}' s ${x.s}: foot ${x.z} m, wall top ${x.top} m`);
if (wtBad) fail = true;
const jf = joinFaces(track, sc);
const jfBad = jf.filter((x) => x.step > 0.15);
console.log(`[${jfBad.length ? 'FAIL' : 'ok'}] wall-tyre joins: ${jf.length} end-to-end joins, ${jfBad.length} with the downstream head more than 0.15 m proud toward the track`
  + (jf.length ? ` (steps ${jf.map((x) => `s ${x.s} ${x.downstream} ${x.step >= 0 ? '+' : ''}${x.step.toFixed(2)}`).join(', ')})` : ''));
for (const x of jfBad) console.log(`       proud s ${x.s}: ${x.downstream} head ${x.step.toFixed(2)} m toward the track: ${x.wall} | ${x.tyres}`);
if (jfBad.length) fail = true;
const tf = tyreFaces(track, sc);
console.log(`[${tf.length ? 'FAIL' : 'ok'}] tyre faces: ${tf.length} tyre runs whose drawn track-side face stands under 0.2 m beyond the edge`);
for (const x of tf) console.log(`       tyre face s ${x.s}: ${x.face.toFixed(2)} m (row 1 ${x.rowsToTrack ? 'toward' : 'away from'} the track): ${x.tyres}`);
if (tf.length) fail = true;

// round 13 (Sonoma owner note 131): two runs of one line with a hole between them, anywhere beyond the edge
const rg = runGaps(track, sc, { openings: cfg.openings });
console.log(`[${rg.gaps.length ? 'FAIL' : 'ok'}] run gaps: ${rg.checked} facing run ends 0.5-25 m apart on one side, ${rg.openings.length} openings `
  + `(paved surface, lapping run or declared), ${rg.gaps.length} holes in a barrier line`);
for (const x of rg.openings) console.log(`       opening s ${x.s} (${x.gap} m): ${x.why}`);
for (const x of rg.gaps) console.log(`       hole ${x.side.padEnd(5)} s ${x.s} (${x.gap} m, ${x.out} m out, at ${x.x}, ${x.y}): ${x.a} | ${x.b}`);
if (rg.gaps.length) fail = true;

// round 14A (Sonoma owner, round-13 drive): the terrain-override gates (terrainGates.ts), on the package's own driven
// surface; a package without scenery.json terrain_override has no region and passes them as n/a
const tg = terrainGates(track, loadHeightfield(Uint8Array.from(readFileSync(join(dir, 'heightfield.bin'))).buffer), sc);
if (!tg.regions) console.log('[ok] terrain override: no region (n/a)');
else {
  const j = tg.joins, m = tg.smooth, k = tg.kerbs;
  console.log(`[${j.bad.length ? 'FAIL' : 'ok'}] pavement joins: ${j.checked} boundary points in ${tg.regions} override region(s) (course edges and paved-part edges, every metre; ${j.ramp} in the ramps not gated), `
    + `max step ${j.maxStep.toFixed(4)} m (limit 0.02), max cross-slope change ${j.maxSlopeDeg.toFixed(2)} deg (limit 2), ${j.bad.length} over`);
  for (const x of j.bad.slice(0, 12)) console.log(`       ${x.what} at (${x.x}, ${x.y}): step ${x.step} m, slope change ${x.slopeDeg} deg`);
  console.log(`[${m.badD2.length || m.badDev.length ? 'FAIL' : 'ok'}] surface smoothness: ${m.profiles} cross-profiles, ${m.points} points at 1 m, max |second difference| ${m.maxD2.toFixed(4)} m (limit 0.01), `
    + `deepest trough ${m.maxTrough.toFixed(4)} m, highest ridge ${m.maxRidge.toFixed(4)} m against the line 5 m either side (limit 0.05); ${m.badD2.length} + ${m.badDev.length} over`);
  for (const x of [...m.badD2, ...m.badDev].slice(0, 12)) console.log(`       s ${x.s} ${x.side} +${x.off} m (${x.x}, ${x.y}): ${x.d2 !== undefined ? `second difference ${x.d2} m` : `${x.dev! < 0 ? 'trough' : 'ridge'} ${Math.abs(x.dev!)} m`}`);
  console.log(`[${k.bad.length ? 'FAIL' : 'ok'}] kerbs on surface: ${k.blocks} kerb blocks in the region(s), max tilt from the surface ${k.maxTiltDeg.toFixed(2)} deg (limit 2), max gap under a block ${k.maxGap.toFixed(4)} m (limit 0); ${k.bad.length} over`);
  for (const x of k.bad.slice(0, 12)) console.log(`       ${x.what} at (${x.x}, ${x.y}): tilt ${x.tiltDeg} deg, gap ${x.gap} m`);
  if (tg.fail) fail = true;
}

// round 14B (judge r14a: the drag-strip continuation's edge line buried by the draped zone): every vertex of a paint
// line, edge line and ground sign within 0.01 m above the driven surface, never below it, region or not
const gm = groundMarksGate(track, loadHeightfield(Uint8Array.from(readFileSync(join(dir, 'heightfield.bin'))).buffer), sc);
console.log(`[${gm.bad.length ? 'FAIL' : 'ok'}] ground marks on surface: ${gm.vertices.paint} paint-line, ${gm.vertices.edge} edge-line and ${gm.vertices.sign} ground-sign vertices, `
  + `height above the driven surface ${gm.minD.toFixed(3)} .. ${gm.maxD.toFixed(3)} m (0 .. ${MARKS_TOL}); ${gm.bad.length} off`);
{
  const by = new Map<string, { n: number; lo: number; hi: number }>();
  for (const x of gm.bad) { const b = by.get(x.what) ?? { n: 0, lo: Infinity, hi: -Infinity }; b.n++; b.lo = Math.min(b.lo, x.d); b.hi = Math.max(b.hi, x.d); by.set(x.what, b); }
  for (const [w, b] of [...by].slice(0, 20)) console.log(`       ${w}: ${b.n} vertices off, ${b.lo.toFixed(3)} .. ${b.hi.toFixed(3)} m`);
}
if (gm.bad.length) fail = true;

console.log('GATES_JSON ' + JSON.stringify({ marks: { ...gm, bad: gm.bad.length }, terrain: { regions: tg.regions, joins: { ...tg.joins, bad: tg.joins.bad.length }, smooth: { ...tg.smooth, badD2: tg.smooth.badD2.length, badDev: tg.smooth.badDev.length }, kerbs: { ...tg.kerbs, bad: tg.kerbs.bad.length } }, runGaps: rg, containment: { escapes: c.escapes.length, runs, allowed: c.allowed.length, junctions: c.junctions },
  pit: p, signs: g, ends: e, facings: sb, wallTops: wt, joins: jf, tyreFaces: tf, fail }));
process.exit(fail ? 1 : 0);
