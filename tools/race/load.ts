// Node loaders for the race tools (track package, Probe car.json, pace / identity).
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTrackSurface, loadHeightfield, type TrackJson, type Surface, type PitLaneJson } from '../../src/physics/index';
import { RaceLine, type GhostsJsonLike } from '../../src/physics/ai/line';
import { parseIdentity, type IdentityCar, type PaceJson } from '../../src/physics/ai/field';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const PACE_PATH = resolve(ROOT, 'public/cars/field/pace.json');
export const IDENTITY_PATH = resolve(ROOT, 'public/cars/field/identity.json');

export interface TrackPack { track: TrackJson; ghosts: GhostsJsonLike; scenery: any; surface: Surface; line: RaceLine; pitLane: PitLaneJson | null; heightfield: Float32Array }

export function loadTrackPack(dir = 'public/tracks/laguna_seca'): TrackPack {
  const D = resolve(ROOT, dir);
  const track: TrackJson = JSON.parse(readFileSync(resolve(D, 'track.json'), 'utf8'));
  const buf = readFileSync(resolve(D, 'heightfield.bin'));
  const heightfield = loadHeightfield(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
  const ghosts = JSON.parse(readFileSync(resolve(D, 'ghosts.json'), 'utf8'));
  const scenery = existsSync(resolve(D, 'scenery.json')) ? JSON.parse(readFileSync(resolve(D, 'scenery.json'), 'utf8')) : null;
  const pit = scenery?.pit_lane ?? null, zones = scenery?.paved_zones ?? null;
  const pitLane = pit || zones ? { spacing_m: 1, fractions: (pit ?? zones).fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] } : null;
  const surface = createTrackSurface(track, heightfield, { pitLane });
  const line = new RaceLine(track, ghosts);
  if (scenery?.pit_exit_cones?.pts?.length) line.restrictLeft(scenery.pit_exit_cones.pts);
  return { track, ghosts, scenery, surface, line, pitLane, heightfield };
}

export function loadProbeJson(): any { return JSON.parse(readFileSync(resolve(ROOT, 'public/cars/probe_gt/car.json'), 'utf8')); }
export function loadPace(): PaceJson { return JSON.parse(readFileSync(PACE_PATH, 'utf8')); }
export function loadIdentity(): Map<string, IdentityCar> {
  return existsSync(IDENTITY_PATH) ? parseIdentity(JSON.parse(readFileSync(IDENTITY_PATH, 'utf8'))) : new Map();
}
