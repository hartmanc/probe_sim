// CLI of the stage-3 scenery gates (sceneryGates.ts): npx tsx tools/track/gates/run_gates.ts <package dir> [gate config json]
// Prints the three reports and a JSON summary line; exits 1 when a gate fails.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { containment, escapeRuns, pitConnectivity, signPlacement, type GateConfig } from './sceneryGates';

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
if (!p.ok) fail = true;

const g = signPlacement(track, sc, cfg);
console.log(`[${g.bad.length ? 'FAIL' : 'ok'}] sign placement: ${g.checked} signs, boards and posts checked, ${g.bad.length} misplaced`);
for (const b of g.bad) console.log(`       ${b.kind} '${b.text}' at (${b.x.toFixed(1)}, ${b.y.toFixed(1)}): ${b.why}`);
if (g.bad.length) fail = true;

console.log('GATES_JSON ' + JSON.stringify({ containment: { escapes: c.escapes.length, runs, allowed: c.allowed.length, junctions: c.junctions },
  pit: p, signs: g, fail }));
process.exit(fail ? 1 : 0);
