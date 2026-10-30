// The jam measurement (tools/race/jams_core.ts) on one self-play race: the player's car AI-driven, the director as traffic_sim.ts
// builds it (switch defaults), stepped to the flag. Read only.
//   npx tsx tools/race/jams_selfplay.ts --track sonoma --seed 1 --laps 10 [--out tools/race/out/jams/<name>]
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { createCollisionWorld } from '../../src/physics/index';
import { RaceDirector } from '../../src/physics/ai/race';
import { TRACKS } from '../../src/scoreboard/config';
import { ROOT, loadTrackPack, loadProbeJson, loadPace, loadIdentityJson, trackArg } from './load';
import { JamTracker, jamsMd } from './jams_core';

const argv = process.argv.slice(2);
const arg = (k: string, d: string): string => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const track = trackArg(argv), laps = Number(arg('--laps', '10')), seed = Number(arg('--seed', '1'));
const pack = loadTrackPack(track);
const ai = TRACKS[track]?.ai ?? {};
const dir = new RaceDirector({
  line: pack.line, surface: pack.surface, makeSurface: pack.makeSurface, probeJson: loadProbeJson(), pace: loadPace(track), identity: loadIdentityJson(track),
  pitLane: pack.scenery?.pit_lane ?? null, blendLine: pack.scenery?.blend_line ?? null, collisionWorld: createCollisionWorld(pack.scenery, pack.track),
}, { laps, seed, playerAi: true, followScale: ai.followScale ?? 1, laneMargin: ai.laneMargin ?? 1, shiftGrip: ai.shiftGrip ?? 0 });
const jt = new JamTracker(dir, track);
const maxTime = laps * 220 + 120;
let step = 0;
while (dir.time < maxTime) {
  dir.step(0.001); step++;
  jt.afterStep(step);
  if (step % 10 === 0 && (dir.phase === 'finished' || (dir.phase === 'chequered' && dir.player.finished))) break;
}
const res = jt.finish();
const md = jamsMd(res, `${track} self-play, seed ${seed}, ${laps} laps`);
console.log(md);
const out = arg('--out', '');
if (out) {
  const base = resolve(ROOT, out);
  mkdirSync(dirname(base), { recursive: true });
  writeFileSync(base + '.md', md);
  writeFileSync(base + '.json', JSON.stringify(res));
}
