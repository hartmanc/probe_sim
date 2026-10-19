// Print the gear schedule and shift rpm per ghost: npx tsx tools/calibrate/gears.ts [ghostId]
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { deriveGearSchedule, loadCarSpec, shiftRpmSummary } from '../../src/physics';
import { TRACKS, DEFAULT_TRACK } from '../../src/scoreboard/config';
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const spec = loadCarSpec(JSON.parse(readFileSync(resolve(ROOT, 'public/cars/probe_gt/car.json'), 'utf8')));
const gh = JSON.parse(readFileSync(resolve(ROOT, 'public', TRACKS[DEFAULT_TRACK].dir, 'ghosts.json'), 'utf8'));
const want = process.argv[2];
for (const lap of gh.laps) {
  if (want && lap.id !== want) continue;
  const sch = deriveGearSchedule(spec, lap, gh.s_grid_m);
  console.log(`${lap.id}: ${sch.shifts.length} shifts; ` + shiftRpmSummary(sch).map((x) => `${x.from}->${x.to} @${x.rpm.toFixed(0)} (x${x.count})`).join(', '));
  if (want) console.log(sch.shifts.map((x) => `s ${x.s} ${x.from}->${x.to} @${x.rpm.toFixed(0)}`).join('\n'));
}
