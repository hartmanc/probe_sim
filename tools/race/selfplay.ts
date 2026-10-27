// Headless self-play: the whole field (player car driven by an AI) races N laps and the AI's racecraft is
// measured: line tracking when alone, passing when clearly faster, defending by pace gap, rules
// (contacts, four wheels off, formation passes), mishaps, and the per-step cost.
//   npx tsx tools/race/selfplay.ts [--track <id>] [--laps 4] [--seed 1] [--max-ai N] [--pace path] [--mishap-rate 0.0002] [--follow-scale 1] [--lane-margin 1] [--shift-grip 0] [--no-kerbs] [--json out.json] [--quiet]
import { createTrackSurface, createCollisionWorld } from '../../src/physics/index';
import { RaceDirector } from '../../src/physics/ai/race';
import type { PaceJson } from '../../src/physics/ai/field';
import { loadTrackPack, loadProbeJson, loadPace, loadIdentityJson, trackArg } from './load';
import { readFileSync, writeFileSync } from 'node:fs';
import { runSelfplay, printReport } from './selfplay_metrics';
import { TRACKS } from '../../src/scoreboard/config';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const laps = Number(arg('--laps', '4')), seed = Number(arg('--seed', '1'));
const maxAi = Number(arg('--max-ai', 'Infinity'));
const pacePath = arg('--pace', '');
const mishapRate = argv.includes('--mishap-rate') ? Number(arg('--mishap-rate', '0.0002')) : undefined;
const track = trackArg(argv);
// the track's AI parameters (TRACKS[id].ai), or --follow-scale to try another
const followScale = argv.includes('--follow-scale') ? Number(arg('--follow-scale', '1')) : (TRACKS[track]?.ai?.followScale ?? 1);
// --lane-margin / --shift-grip: try another value of the track's knob (trials; the registry keeps the chosen one)
const laneMargin = argv.includes('--lane-margin') ? Number(arg('--lane-margin', '1')) : (TRACKS[track]?.ai?.laneMargin ?? 1);
const shiftGrip = argv.includes('--shift-grip') ? Number(arg('--shift-grip', '0')) : (TRACKS[track]?.ai?.shiftGrip ?? 0);
const pack = loadTrackPack(track);
// the track's own identity.json, else the global one (as the app)
const identity = loadIdentityJson(track);
const pace: PaceJson = pacePath ? JSON.parse(readFileSync(pacePath, 'utf8')) : loadPace(track);
// the app's surface options (load.ts); --no-kerbs: the pit-lane-only surface self-play used until 20 Oct 2026 (comparison)
const makeSurface = argv.includes('--no-kerbs') ? () => createTrackSurface(pack.track, pack.heightfield, { pitLane: pack.pitLane }) : pack.makeSurface;
const dir = new RaceDirector({
  line: pack.line, surface: pack.surface, makeSurface,
  probeJson: loadProbeJson(), pace, identity, pitLane: pack.scenery?.pit_lane ?? null, blendLine: pack.scenery?.blend_line ?? null, collisionWorld: createCollisionWorld(pack.scenery, pack.track),
}, { laps, seed, playerAi: true, maxAi, followScale, laneMargin, shiftGrip, ...(mishapRate !== undefined ? { mishapRate } : {}) });
const m = runSelfplay(dir, makeSurface(), { log: !argv.includes('--quiet') });
printReport(m);
// race pace against the calibrated pace: each AI car's best and last lap over the target lap of the stint it drew
const med = (a: number[]) => { const b = a.filter(Number.isFinite).sort((x, y) => x - y); return b.length ? b[Math.floor(b.length / 2)] : NaN; };
const ai = dir.cars.filter((c) => !c.isPlayer && c.paceTarget > 0);
const racePace = { bestOverTarget: +med(ai.map((c) => c.bestLap / c.paceTarget)).toFixed(4), lastOverTarget: +med(ai.map((c) => c.lastLap / c.paceTarget)).toFixed(4), followScale, laneMargin, shiftGrip };
console.log(`(g) pace: median best lap / drawn target ${racePace.bestOverTarget}, last lap / target ${racePace.lastOverTarget}; knobs followScale ${followScale} laneMargin ${laneMargin} shiftGrip ${shiftGrip}`);
(m as unknown as { pace: typeof racePace }).pace = racePace;
// finishing order (the results frozen at the flag; else by race distance): the bit-identity check across knob changes
const order = dir.getResults()?.map((r) => r.number) ?? dir.cars.map((c, i) => ({ c, U: dir.traffic.U[i] })).sort((a, b) => b.U - a.U).map((r) => r.c.number);
(m as unknown as { order: string[] }).order = order;
console.log(`(h) finishing order: ${order.slice(0, 10).join(' ')}${order.length > 10 ? ' ...' : ''} (${order.length} cars)`);
const out = arg('--json', '');
if (out) writeFileSync(out, JSON.stringify(m, null, 1));
