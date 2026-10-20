// CLI of the stage-3 scenery gates (sceneryGates.ts): npx tsx tools/track/gates/run_gates.ts <package dir> [gate config json]
// Prints the three reports and a JSON summary line; exits 1 when a gate fails.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { containment, escapeRuns, exposedEnds, pitConnectivity, sideBySide, signPlacement, type GateConfig } from './sceneryGates';

const dir = process.argv[2];
const cfg: GateConfig & { pit_box_s?: number } = process.argv[3] ? JSON.parse(readFileSync(process.argv[3], 'utf8')) : {};
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
console.log(`[${e.exposed.length ? 'FAIL' : 'ok'}] wall ends: ${e.checked} upstream run ends within 8 m of an edge checked, ${e.ok.length} joined / cushioned / lapped / tapered, ${e.exposed.length} exposed to oncoming travel`);
for (const x of e.exposed) console.log(`       exposed ${x.side.padEnd(5)} s ${x.s} (${x.out} m out): ${x.label}`);
if (e.exposed.length) fail = true;
const sb = sideBySide(track, sc);
console.log(`[${sb.length ? 'FAIL' : 'ok'}] tyre facings: ${sb.length} tyre runs standing 0.8-2.5 m off a wall side by side (a tyre run beside a wall must face it, within 0.8 m, or meet it end to end)`);
for (const x of sb) console.log(`       side by side s ${x.s} (${x.off} m off): ${x.tyre} | ${x.wall}`);
if (sb.length) fail = true;

console.log('GATES_JSON ' + JSON.stringify({ containment: { escapes: c.escapes.length, runs, allowed: c.allowed.length, junctions: c.junctions },
  pit: p, signs: g, ends: e, facings: sb, fail }));
process.exit(fail ? 1 : 0);
