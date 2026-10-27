// Round 11 note 3, "check that the AI's line and the two-lap self-play never cross the line": the whole self-play field (the
// player's car driven by an AI) races N laps on the Mid-Ohio package; every car's four wheels are tested against the pit-exit blend
// line (src/physics/blendline.ts) at every 5 ms, each car with its own watch (the entry side decides the mode, as in the rule).
// Reports the violations by car and station, and the smallest wheel clearance to the line over the cars that passed it.
//   npx tsx tools/track/compare/mid_ohio/r11/blend_selfplay.ts [--laps 2] [--seed 1] [--max-ai N]
import { createCollisionWorld } from '../../../../../src/physics/index';
import { RaceDirector } from '../../../../../src/physics/ai/race';
import { BlendLine, BlendLineWatch, BlendFlag } from '../../../../../src/physics/blendline';
import type { PaceJson } from '../../../../../src/physics/ai/field';
import { loadTrackPack, loadProbeJson, loadPace, loadIdentityJson } from '../../../../race/load';
import { TRACKS } from '../../../../../src/scoreboard/config';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const laps = Number(arg('--laps', '2')), seed = Number(arg('--seed', '1')), maxAi = Number(arg('--max-ai', 'Infinity'));
const track = 'mid_ohio';
const pack = loadTrackPack(track);
const bl = pack.scenery.blend_line;
const line = new BlendLine(bl);
const ai = TRACKS[track].ai;
const dir = new RaceDirector({
  line: pack.line, surface: pack.surface, makeSurface: pack.makeSurface, probeJson: loadProbeJson(), pace: loadPace(track) as PaceJson,
  identity: loadIdentityJson(track), pitLane: pack.scenery?.pit_lane ?? null, blendLine: bl, collisionWorld: createCollisionWorld(pack.scenery, pack.track),
}, { laps, seed, playerAi: true, maxAi, followScale: ai?.followScale ?? 1, laneMargin: ai?.laneMargin ?? 1, shiftGrip: ai?.shiftGrip ?? 0 });
const flags = dir.cars.map(() => new BlendFlag(new BlendLineWatch(line)));
const anyDir = dir as unknown as { mishapLog?: { t: number; idx: number; corner: string; kind: string }[] };
const tmp = { d: 0, band: false };
const viol: { idx: number; car: string; t: number; s: number; kind: string }[] = [];
const minClear = new Float64Array(dir.cars.length).fill(Infinity), passed = new Uint8Array(dir.cars.length), wasIn = new Uint8Array(dir.cars.length);
let steps = 0, flagged = 0;
const maxTime = laps * 260 + 200;
const t0 = Date.now();
while (dir.time < maxTime && dir.phase !== 'finished') {
  dir.step(0.001);
  if (++steps % 5) continue;
  for (let i = 0; i < dir.cars.length; i++) {
    const c = dir.cars[i], st = c.vehicle.state;
    const v = flags[i].update(st.pos[0], st.pos[1], st.wheels, 0.005);
    if (flags[i].watch.mode !== 'none') {
      wasIn[i] = 1;
      for (const w of st.wheels) { line.locate(w.pos[0], w.pos[1], tmp); if (tmp.band) minClear[i] = Math.min(minClear[i], -tmp.d * line.pitSide); }
    } else if (wasIn[i]) { passed[i]++; wasIn[i] = 0; }
    if (v) { const pr = pack.line.project(st.pos[0], st.pos[1], 0), dv = c.driver as unknown as { passTarget?: number; passSide?: number; offTrack?: boolean; mishapActive?: boolean } | null;
      console.log(`   detail: car ${c.number} t ${dir.time.toFixed(1)} s ${pr.s.toFixed(0)} lateral ${pr.lateral.toFixed(2)} (line ${pack.line.at(pack.line.off, pr.s).toFixed(2)}, left edge ${pack.line.at(pack.line.halfL, pr.s).toFixed(2)}) speed ${st.speed.toFixed(1)} passTarget ${dv?.passTarget} passSide ${dv?.passSide} offTrack ${dv?.offTrack} mishap ${dv?.mishapActive} recoveries ${c.recoveries}`);
      flagged++; viol.push({ idx: i, car: `${c.isPlayer ? 'player(AI) ' : ''}#${c.number}`, t: +dir.time.toFixed(1), s: +pack.line.project(st.pos[0], st.pos[1], 0).s.toFixed(0), kind: v }); }
  }
}
const lapsPassed = [...passed].reduce((a, b) => a + b, 0);
const clear = [...minClear].filter(Number.isFinite);
console.log(`self-play ${laps} laps, seed ${seed}, ${dir.cars.length} cars, ${dir.time.toFixed(0)} s of race, ${((Date.now() - t0) / 1000).toFixed(0)} s wall; band passes ${lapsPassed}`);
console.log(`wheel clearance to the line (min over each car's passes): worst ${Math.min(...clear).toFixed(2)} m, median ${clear.sort((a, b) => a - b)[Math.floor(clear.length / 2)].toFixed(2)} m, cars that passed ${clear.length}`);
console.log(`violations (episodes of >= 2 wheels across, AI cars and the AI-driven player; re-armed after 2 s legal): ${flagged}`);
for (const v of viol.slice(0, 30)) {
  console.log('  ', JSON.stringify(v));
  for (const m of (anyDir.mishapLog ?? []).filter((m) => m.idx === v.idx && m.t > v.t - 12 && m.t < v.t + 1)) console.log('      mishap before it:', JSON.stringify(m));
}
const h = dir.hud();
console.log(`player penalties at the end: ${h.penalties.count} (${h.penalties.lastReason ?? '-'})`);
