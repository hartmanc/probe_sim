// Placeholder field pace for a circuit without its own results matched per car yet: every car's (and stint's) target
// lap is its Laguna target scaled by the ratio of the AI Probe's solo lap on the new circuit to its solo lap at Laguna,
// both at pace scale 1. Then run calibrate_field.ts --track <id> to fit the scales.
//
//   npx tsx tools/race/pace_ratio.ts --track <id> [--from laguna_seca]
//
// This is a stand-in: replace it with tools/race/pace.ts on the circuit's own MyLaps results (Sonoma: the March 2026
// export cached in tools/race/data/sonoma/) once the cars are matched to identity.json per car.
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { loadTrackPack, loadProbeJson, loadPace, pacePath, trackArg } from './load';
import { runSolo } from '../../src/physics/ai/solo';
import { AI_VERSION, type PaceJson } from '../../src/physics/ai/field';

const argv = process.argv.slice(2);
const track = trackArg(argv);
const from = argv.includes('--from') ? argv[argv.indexOf('--from') + 1] : 'laguna_seca';
const probe = loadProbeJson();
const solo = (id: string) => {
  const p = loadTrackPack(id);
  const r = runSolo(p.line, p.surface, probe, null, 1, 2);
  if (r.laps.length < 2 || r.recoveries) throw new Error(`${id}: the AI Probe did not complete two clean laps`);
  return r.laps[1];
};
const a = solo(from), b = solo(track), k = b / a;
console.log(`AI Probe solo at scale 1: ${from} ${a.toFixed(2)} s, ${track} ${b.toFixed(2)} s, ratio ${k.toFixed(4)}`);
const src = loadPace(from);
const r3 = (x: number) => +(x * k).toFixed(3);
const out: PaceJson = {
  ai_version: AI_VERSION,
  source: `PLACEHOLDER: ${from} targets x ${k.toFixed(4)} (AI Probe solo lap ratio ${track}/${from} at scale 1; tools/race/pace_ratio.ts). ` +
    `Not this circuit's results; replace with tools/race/pace.ts on its own MyLaps export.`,
  track,
  cars: src.cars.map((c) => ({
    ...c, targetLap: r3(c.targetLap), bestLap: r3(c.bestLap), sigma: +(c.sigma * k).toFixed(3), scale: undefined, achievedLap: undefined,
    resolved: undefined, stints: (c.stints ?? []).map((s) => ({ ...s, targetLap: r3(s.targetLap), bestLap: r3(s.bestLap), sigma: +(s.sigma * k).toFixed(3), scale: undefined, achievedLap: undefined })),
  })) as PaceJson['cars'],
};
mkdirSync(dirname(pacePath(track)), { recursive: true });
writeFileSync(pacePath(track), JSON.stringify(out, null, 1) + '\n');
console.log(`wrote ${pacePath(track)} (${out.cars.length} cars)`);
