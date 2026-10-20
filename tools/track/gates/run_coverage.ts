// CLI of the coverage and pit-lane gates (coverageGate.ts):
//   npx tsx tools/track/gates/run_coverage.ts <package dir> <inventory.json> [gate config json] [--json <out>] [--all]
// The gate config may carry {tol, pit_walls: [{side, s0, s1, h, src}]} (build_track.py writes it from the track
// config's pit_lane section). Prints the MISSING and UNSUPPORTED lists (runs; every row with --all), the HEIGHT
// mismatches and the pit-lane report; exits 1 when the coverage or the pit-lane gate fails.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { coverage, missingRuns, pitLaneWalls, MUST_COVER, type Inventory, type PitWallDecl } from './coverageGate';

const args = process.argv.slice(2);
const flag = (f: string) => { const i = args.indexOf(f); if (i < 0) return undefined; const v = args[i + 1]; args.splice(i, 2); return v; };
const jsonOut = flag('--json');
const all = args.includes('--all'); if (all) args.splice(args.indexOf('--all'), 1);
const [dir, invPath, cfgPath] = args;
if (!dir || !invPath) { console.error('usage: run_coverage.ts <package dir> <inventory.json> [gate config json] [--json out] [--all]'); process.exit(2); }
const cfg: { tol?: number; pit_walls?: PitWallDecl[] } = cfgPath ? JSON.parse(readFileSync(cfgPath, 'utf8')) : {};
const track = JSON.parse(readFileSync(join(dir, 'track.json'), 'utf8'));
const sc = JSON.parse(readFileSync(join(dir, 'scenery.json'), 'utf8'));
const inv: Inventory = JSON.parse(readFileSync(invPath, 'utf8'));
const r = coverage(track, sc, inv, { tol: cfg.tol });
const kinds = (o: Record<string, number>) => Object.entries(o).sort((a, b) => b[1] - a[1]).map(([k, n]) => `${k} ${n}`).join(', ') || 'none';
console.log(`[${r.pass ? 'ok' : 'FAIL'}] coverage: ${r.checked} inventory rows checked (${r.skipped} 'ahead' rows without a distance skipped), `
  + `${r.objects} scenery objects; MISSING ${r.missing.length} (${kinds(r.missingByKind)}), UNSUPPORTED ${r.unsupported.length} (${kinds(r.unsupportedByKind)}); `
  + `fails on MISSING ${MUST_COVER.join(' / ')} or any UNSUPPORTED`);
const runs = missingRuns(r.missing);
console.log(`       MISSING in ${runs.length} runs (kind, side, stations, rows, first source):`);
for (const m of runs) console.log(`       missing ${m.kind.padEnd(10)} ${m.side.padEnd(5)} s ${m.s0.toFixed(0)}-${m.s1.toFixed(0)} (${m.n} rows) ${m.first.what}${m.first.h ? `, ${m.first.h} m` : ''} [${m.first.source}]`);
if (all) for (const m of r.missing) console.log(`         row s ${m.s.toFixed(0)} ${m.side} ${m.kind}: ${m.what} [${m.source}${m.frame ? ' ' + m.frame : ''}]`);
for (const u of r.unsupported) console.log(`       unsupported ${u.kind.padEnd(10)} ${u.side.padEnd(5)} s ${u.s0}-${u.s1} ${u.label} (src: ${u.src.slice(0, 80) || 'none'})`);
console.log(`       HEIGHT mismatches (advisory, ${r.heights.length}):`);
for (const h of r.heights) console.log(`       height ${h.kind} ${h.side} s ${h.s.toFixed(0)}: inventory ${h.row_h} m (${h.method}) vs package ${h.obj_h} m on ${h.obj} [${h.source}]`);
const p = pitLaneWalls(track, sc, inv, cfg.pit_walls ?? [], cfg.tol ?? 15);
console.log(`[${p.pass ? 'ok' : 'FAIL'}] pit lane: ${p.checked} pit-lane wall rows; ${p.undeclared.length} not declared in the config's pit_lane.walls, `
  + `${p.absent.length} with no barrier in the package${p.lane ? '' : ' (no pit lane in the package)'}`);
for (const u of p.undeclared) console.log(`       undeclared ${u.side.padEnd(5)} s ${u.s.toFixed(0)}: ${u.what} [${u.source}]`);
for (const u of p.absent) console.log(`       absent     ${u.side.padEnd(5)} s ${u.s.toFixed(0)}: ${u.what} [${u.source}]`);
const out = { coverage: { ...r, runs }, pit: p };
if (jsonOut) writeFileSync(jsonOut, JSON.stringify(out, null, 1));
console.log('COVERAGE_JSON ' + JSON.stringify({ pass: r.pass, missing: r.missing.length, unsupported: r.unsupported.length, missingByKind: r.missingByKind,
  unsupportedByKind: r.unsupportedByKind, heights: r.heights.length, pit: { pass: p.pass, undeclared: p.undeclared.length, absent: p.absent.length } }));
process.exit(r.pass && p.pass ? 0 : 1);
