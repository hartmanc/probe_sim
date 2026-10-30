// L1 K3 (30 Oct 2026): a car's aggression from the MyLaps passing data (tools/race/data/traffic/curves.json `aggression`, per
// event, tools/race/traffic_data.ts section (d)): a car with >= MIN_OPP opportunities in its event takes its tier (attacker 2,
// neutral 1, passive 0); every other car keeps the seeded draw (src/physics/ai/rng.ts aggressionFor). Used by the pace generators
// (pace.ts, pace_track.ts), so the pace files stay reproducible (pace_quantile.test.ts).
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { aggressionFor } from '../../src/physics/ai/rng';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const MIN_OPP = 20;
const TIER: Record<string, 0 | 1 | 2> = { attacker: 2, neutral: 1, passive: 0 };
/** curves.json event id of a track id */
const EVENT: Record<string, string> = { laguna_seca: 'laguna', sonoma: 'sonoma', buttonwillow: 'buttonwillow', mid_ohio: 'mid_ohio' };

let cache: Record<string, { number: string; n: number; tier: string }[]> | null = null;
/** The data tier's aggression for car `number` at `track` (n >= MIN_OPP), else the seeded draw for its class. */
export function aggressionData(track: string, number: string, cls: string): 0 | 1 | 2 {
  cache ??= JSON.parse(readFileSync(resolve(ROOT, 'tools/race/data/traffic/curves.json'), 'utf8')).aggression;
  const row = cache![EVENT[track] ?? track]?.find((r) => r.number === number);
  return row && row.n >= MIN_OPP && row.tier in TIER ? TIER[row.tier] : aggressionFor(number, cls);
}
