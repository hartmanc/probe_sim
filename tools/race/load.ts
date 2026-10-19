// Node loaders for the race tools (track package, Probe car.json, pace / identity). The track comes from the registry
// (src/scoreboard/config.ts TRACKS): every tool takes `--track <id>` (default DEFAULT_TRACK).
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTrackSurface, loadHeightfield, type TrackJson, type Surface, type PitLaneJson } from '../../src/physics/index';
import { RaceLine, type GhostsJsonLike } from '../../src/physics/ai/line';
import { parseIdentity, type IdentityCar, type PaceJson } from '../../src/physics/ai/field';
import { TRACKS, DEFAULT_TRACK } from '../../src/scoreboard/config';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
/** `--track <id>` from argv (default DEFAULT_TRACK); an unknown id is an error. */
export function trackArg(argv: string[] = process.argv.slice(2)): string {
  const i = argv.indexOf('--track');
  const id = i >= 0 ? argv[i + 1] : DEFAULT_TRACK;
  if (!id || !Object.prototype.hasOwnProperty.call(TRACKS, id)) throw new Error(`--track: unknown track ${id} (registered: ${Object.keys(TRACKS).join(', ')})`);
  return id;
}
/** The track's field pace file (TRACKS[id].pace, relative to public/). */
export function pacePath(trackId: string = DEFAULT_TRACK): string { return resolve(ROOT, 'public', TRACKS[trackId].pace); }
export const PACE_PATH = pacePath(DEFAULT_TRACK);
export const IDENTITY_PATH = resolve(ROOT, 'public/cars/field/identity.json');

export interface TrackPack { track: TrackJson; ghosts: GhostsJsonLike; scenery: any; surface: Surface; line: RaceLine; pitLane: PitLaneJson | null; heightfield: Float32Array }

/** A track package by registry id, or by directory (relative to the repo root). */
export function loadTrackPack(idOrDir: string = DEFAULT_TRACK): TrackPack {
  const D = resolve(ROOT, Object.prototype.hasOwnProperty.call(TRACKS, idOrDir) ? 'public/' + TRACKS[idOrDir].dir : idOrDir);
  const track: TrackJson = JSON.parse(readFileSync(resolve(D, 'track.json'), 'utf8'));
  const buf = readFileSync(resolve(D, 'heightfield.bin'));
  const heightfield = loadHeightfield(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
  const ghosts = JSON.parse(readFileSync(resolve(D, 'ghosts.json'), 'utf8'));
  const scenery = existsSync(resolve(D, 'scenery.json')) ? JSON.parse(readFileSync(resolve(D, 'scenery.json'), 'utf8')) : null;
  const pit = scenery?.pit_lane ?? null, zones = scenery?.paved_zones ?? null;
  const pitLane = pit || zones ? { spacing_m: 1, fractions: (pit ?? zones).fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] } : null;
  const surface = createTrackSurface(track, heightfield, { pitLane, sausages: scenery?.sausages ?? null });
  const line = new RaceLine(track, ghosts);
  if (scenery?.pit_exit_cones?.pts?.length) line.restrictLeft(scenery.pit_exit_cones.pts);
  return { track, ghosts, scenery, surface, line, pitLane, heightfield };
}

export function loadProbeJson(): any { return JSON.parse(readFileSync(resolve(ROOT, 'public/cars/probe_gt/car.json'), 'utf8')); }
export function loadPace(trackId: string = DEFAULT_TRACK): PaceJson { return JSON.parse(readFileSync(pacePath(trackId), 'utf8')); }
export function loadIdentity(): Map<string, IdentityCar> {
  return existsSync(IDENTITY_PATH) ? parseIdentity(JSON.parse(readFileSync(IDENTITY_PATH, 'utf8'))) : new Map();
}
