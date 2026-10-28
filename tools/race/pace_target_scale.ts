// A copy of a pace file with every target (car and stint) divided by a strength, for calibrating the AI strength curve's
// point at that strength (AI round 1, Part B: tools/race/out/pace_q/s<strength>/<track>/pace.json, then calibrate_field.ts
// --pace <copy>, then pace_curve.ts). Fits are kept as warm starts; nothing else changes.
//   npx tsx tools/race/pace_target_scale.ts --track <id> --strength 1.1 --out <file>
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pacePath, trackArg } from './load';
import type { PaceJson } from '../../src/physics/ai/field';
const argv = process.argv.slice(2);
const arg = (k: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
const track = trackArg(argv), st = Number(arg('--strength') ?? 1.1), out = resolve(arg('--out')!);
const p: PaceJson = JSON.parse(readFileSync(pacePath(track), 'utf8'));
for (const c of p.cars) {
  c.targetLap = +(c.targetLap / st).toFixed(3);
  for (const s of c.stints ?? []) s.targetLap = +(s.targetLap / st).toFixed(3);
  delete c.curve;
}
(p as unknown as { strengthTarget: number }).strengthTarget = st;
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, JSON.stringify(p, null, 1) + '\n');
console.log(`wrote ${out}: targets / ${st}`);
