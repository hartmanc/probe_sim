// Per-car race pace from the real MYLAPS results of the 2026-10-12 Laguna Seca Lemons race.
//
//   npx tsx tools/race/pace.ts [--track <id>] [--data <dir>]   # writes the track's pace file (TRACKS[id].pace,
//                                          Laguna: public/cars/field/pace.json), keeping fitted scales already there
//
// Input: tools/race/data/sessions_12975608_classification.json + tools/race/data/laps/posNNN.json.
// Per car: target lap = median of GREEN, non-pit laps after dropping outliers (> 1.3 x the raw median);
// consistency = robust sigma (1.4826 x MAD) of those laps; best lap; laps completed; grid; class; team.
// Aggression tier = seeded draw from the car number with class weighting (src/physics/ai/rng.ts).
//
// Stints (one driver each): the laps between pit stops. A race draws ONE stint per car (field.ts drawPace),
// so a car is sometimes driven by its quick driver and sometimes by its slow one. Per stint the pace is the
// median of that driver's clean laps, after dropping: non-green laps, the pit lap, the out lap after it
// (and lap 1 of the race), laps slower than 1.2 x the stint's own median or 1.3 x the car's median, and
// anything faster than 0.97 x the official best. A stint needs MIN_STINT_LAPS clean laps.
// Chosen against the owner's real result (the Probe ran P5-P7): averaged over the draw, the stint median
// puts 5-6 AI cars ahead of a 2:00-2:02 Probe; the 25th percentile would put 6-8 ahead.

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { aggressionFor } from '../../src/physics/ai/rng';
import { AI_VERSION, type PaceCar, type PaceJson } from '../../src/physics/ai/field';
import { carPace, parseLap } from './pace_rules';
import { pacePath, trackArg } from './load';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const ARGV = process.argv.slice(2);
const TRACK = trackArg(ARGV);
// the race results the paces come from (Laguna: the 2026-10-12 MYLAPS session in tools/race/data)
const DATA = resolve(ROOT, ARGV.includes('--data') ? ARGV[ARGV.indexOf('--data') + 1] : 'tools/race/data');
const OUT = pacePath(TRACK);
const PLAYER = '619';

const cls = JSON.parse(readFileSync(resolve(DATA, 'sessions_12975608_classification.json'), 'utf8'));
const prev: PaceJson | null = existsSync(OUT) ? JSON.parse(readFileSync(OUT, 'utf8')) : null;
const prevBy = new Map((prev?.cars ?? []).map((c) => [c.number, c]));
const keepScales = prev?.ai_version === AI_VERSION;

const cars: PaceCar[] = [];
for (const r of cls.rows) {
  const f = resolve(DATA, `laps/pos${String(r.position).padStart(3, '0')}.json`);
  const lj = JSON.parse(readFileSync(f, 'utf8'));
  const info = lj.lapDataInfo.participantInfo;
  const number = String(r.startNumber);
  const p = prevBy.get(number);
  // the rules (stints, outliers): tools/race/pace_rules.ts
  const pc = carPace(lj.laps, parseLap(r.bestTime), (k, target) => {
    const old = keepScales ? p?.stints?.[k] : undefined;
    return old && old.targetLap === target && old.scale !== undefined ? { scale: old.scale, achievedLap: old.achievedLap } : null;
  });

  const car: PaceCar = {
    number,
    team: r.name,
    class: r.resultClass,
    grid: info.startPos,
    finish: r.position,
    classFinish: r.positionInClass,
    lapsCompleted: r.numberOfLaps,
    greenLaps: pc.greenLaps,
    targetLap: pc.targetLap,
    bestLap: pc.bestLap,
    sigma: pc.sigma,
    aggression: aggressionFor(number, r.resultClass),
    ...(number === PLAYER ? { player: true } : {}),
    ...(keepScales && p?.scale !== undefined ? { scale: p.scale, achievedLap: p.achievedLap } : {}),
    stints: pc.stints,
  };
  cars.push(car);
}
cars.sort((a, b) => a.grid - b.grid);
const out: PaceJson = {
  ai_version: prev?.ai_version ?? AI_VERSION,
  source: ARGV.includes('--source') ? ARGV[ARGV.indexOf('--source') + 1]
    : 'MYLAPS session 12975608 (24 Hours of Lemons, WeatherTech Raceway Laguna Seca, 2026-10-12); tools/race/pace.ts',
  track: TRACK,
  cars,
};
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n');
const mmss = (x: number) => `${Math.floor(x / 60)}:${(x % 60).toFixed(2).padStart(5, '0')}`;
console.log('grid  #     cls aggr  target    best   sigma  laps  stints  stint pace range        team');
for (const c of cars) {
  const st = c.stints ?? [];
  const rng = st.length ? `${mmss(Math.min(...st.map((s) => s.targetLap)))} - ${mmss(Math.max(...st.map((s) => s.targetLap)))}` : '(none: car pace)   ';
  console.log(`${String(c.grid).padStart(3)}  ${c.number.padEnd(5)} ${c.class}   ${c.aggression}   ${mmss(c.targetLap)} ${mmss(c.bestLap)} ${c.sigma.toFixed(2).padStart(6)} ${String(c.greenLaps).padStart(4)}  ${String(st.length).padStart(4)}    ${rng}   ${c.team}${c.player ? '  (player)' : ''}`);
}
console.log(`wrote ${OUT} (${cars.length} cars, ${cars.reduce((a, c) => a + (c.stints?.length ?? 0), 0)} stints)`);
