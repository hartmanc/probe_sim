// Shared loaders for the ai_*.test.ts files (real Laguna Seca package + field data).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createTrackSurface, createCollisionWorld, loadHeightfield, type TrackJson, type PitLaneJson, type Surface } from '../index';
import { RaceLine } from '../ai/line';
import type { PaceJson } from '../ai/field';
import { RaceDirector, type RaceConfig } from '../ai/race';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const tdir = root + 'public/tracks/laguna_seca/';

export interface Pack {
  track: TrackJson; heightfield: Float32Array; scenery: any; pitLane: PitLaneJson | null; surface: Surface; line: RaceLine;
  probeJson: any; pace: PaceJson; identity: unknown | null; makeSurface: () => Surface;
}
let cached: Pack | null = null;

export function pack(): Pack {
  if (cached) return cached;
  const track = JSON.parse(readFileSync(tdir + 'track.json', 'utf8')) as TrackJson;
  const heightfield = loadHeightfield(Uint8Array.from(readFileSync(tdir + 'heightfield.bin')).buffer);
  const ghosts = JSON.parse(readFileSync(tdir + 'ghosts.json', 'utf8'));
  const scenery = JSON.parse(readFileSync(tdir + 'scenery.json', 'utf8'));
  const pit = scenery.pit_lane ?? null, zones = scenery.paved_zones ?? null;
  const pitLane = pit || zones ? { spacing_m: 1, fractions: (pit ?? zones).fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] } : null;
  // the same surface the race builds in the app (race.ts surfaceFactory): pit lane, paved zones and sausage kerbs
  const makeSurface = () => createTrackSurface(track, heightfield, { pitLane, sausages: scenery.sausages ?? null });
  const line = new RaceLine(track, ghosts);
  if (scenery.pit_exit_cones?.pts?.length) line.restrictLeft(scenery.pit_exit_cones.pts);
  let identity: unknown | null = null;
  try { identity = JSON.parse(readFileSync(root + 'public/cars/field/identity.json', 'utf8')); } catch { identity = null; }
  cached = {
    track, heightfield, scenery, pitLane, surface: makeSurface(), line, makeSurface,
    probeJson: JSON.parse(readFileSync(root + 'public/cars/probe_gt/car.json', 'utf8')),
    pace: JSON.parse(readFileSync(root + 'public/cars/field/pace.json', 'utf8')),
    identity,
  };
  return cached;
}

export function director(cfg: Partial<RaceConfig> = {}, opts: { walls?: boolean; playerVehicle?: any } = {}): RaceDirector {
  const p = pack();
  return new RaceDirector({
    line: p.line, surface: p.surface, makeSurface: p.makeSurface, probeJson: p.probeJson, pace: p.pace, identity: p.identity,
    pitLane: p.scenery.pit_lane ?? null, collisionWorld: opts.walls === false ? null : createCollisionWorld(p.scenery, p.track),
    playerVehicle: opts.playerVehicle ?? null,
  }, cfg);
}
