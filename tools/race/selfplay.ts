// Headless self-play: the whole field (player car driven by an AI) races N laps and the AI's racecraft is
// measured: line tracking when alone, passing when clearly faster, defending by pace gap, rules
// (contacts, four wheels off, formation passes), mishaps, and the per-step cost.
//   npx tsx tools/race/selfplay.ts [--track <id>] [--laps 4] [--seed 1] [--max-ai N] [--pace path] [--mishap-rate 0.0002] [--follow-scale 1] [--no-kerbs] [--json out.json] [--quiet]
import { createTrackSurface, createCollisionWorld } from '../../src/physics/index';
import { RaceDirector } from '../../src/physics/ai/race';
import type { PaceJson } from '../../src/physics/ai/field';
import { loadTrackPack, loadProbeJson, loadPace, IDENTITY_PATH, trackArg } from './load';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
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
const pack = loadTrackPack(track);
const identity = existsSync(IDENTITY_PATH) ? JSON.parse(readFileSync(IDENTITY_PATH, 'utf8')) : null;
const pace: PaceJson = pacePath ? JSON.parse(readFileSync(pacePath, 'utf8')) : loadPace(track);
// the app's surface options (load.ts); --no-kerbs: the pit-lane-only surface self-play used until 20 Oct 2026 (comparison)
const makeSurface = argv.includes('--no-kerbs') ? () => createTrackSurface(pack.track, pack.heightfield, { pitLane: pack.pitLane }) : pack.makeSurface;
const dir = new RaceDirector({
  line: pack.line, surface: pack.surface, makeSurface,
  probeJson: loadProbeJson(), pace, identity, pitLane: pack.scenery?.pit_lane ?? null, collisionWorld: createCollisionWorld(pack.scenery, pack.track),
}, { laps, seed, playerAi: true, maxAi, followScale, laneMargin: TRACKS[track]?.ai?.laneMargin ?? 1, shiftGrip: TRACKS[track]?.ai?.shiftGrip ?? 0, ...(mishapRate !== undefined ? { mishapRate } : {}) });
const m = runSelfplay(dir, makeSurface(), { log: !argv.includes('--quiet') });
printReport(m);
const out = arg('--json', '');
if (out) writeFileSync(out, JSON.stringify(m, null, 1));
