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
export function pacePath(trackId: string = DEFAULT_TRACK): string {
  // FIELD_TRACK=<id> FIELD_PACE=<path under public/>: write / read ONE track's pace elsewhere than its registry entry
  // (Mid-Ohio's real field, 26 Oct 2026, while the registry still points at the Laguna stand-in); unset: the registry
  if (process.env.FIELD_TRACK === trackId && process.env.FIELD_PACE) return resolve(ROOT, 'public', process.env.FIELD_PACE);
  return resolve(ROOT, 'public', TRACKS[trackId].pace);
}
export const PACE_PATH = pacePath(DEFAULT_TRACK);
/** The global identity.json (Laguna's field; the fallback of a track without its own). */
export const IDENTITY_PATH = resolve(ROOT, 'public/cars/field/identity.json');
/** The identity file a track's race uses, as the app (src/app/loader.ts loadFieldData): TRACKS[id].identity when that
 *  file exists, else the global IDENTITY_PATH. Rows are keyed by `id`, else number (field.ts fieldKey). */
export function identityPath(trackId: string = DEFAULT_TRACK): string {
  const own = process.env.FIELD_TRACK === trackId && process.env.FIELD_IDENTITY ? process.env.FIELD_IDENTITY : TRACKS[trackId]?.identity;
  return own && existsSync(resolve(ROOT, 'public', own)) ? resolve(ROOT, 'public', own) : IDENTITY_PATH;
}
/** The track's identity.json contents (identityPath), or null when there is none. */
export function loadIdentityJson(trackId: string = DEFAULT_TRACK): unknown | null {
  const p = identityPath(trackId);
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf8')) : null;
}

export interface TrackPack {
  track: TrackJson; ghosts: GhostsJsonLike; scenery: any; surface: Surface; line: RaceLine; pitLane: PitLaneJson | null; heightfield: Float32Array;
  /** far terrain (scenery.json far.heightfield), as the app loads it, or null */
  farHeightfield: Float32Array | null;
  /** A new physics Surface with the app's options (src/app/modes/race.ts surfaceFactory, HotlapSim): pit lane + paved
   *  zones, far terrain, sausage kerbs and the per-track kerb profile. Every race tool builds its surfaces with this. */
  makeSurface: () => Surface;
}

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
  // far terrain: the app reads nx·ny floats from scenery.json far.heightfield.file (src/app/loader.ts)
  let farHeightfield: Float32Array | null = null;
  const farGrid = scenery?.far?.heightfield;
  if (farGrid?.file && existsSync(resolve(D, farGrid.file))) {
    const fb = readFileSync(resolve(D, farGrid.file)), n = farGrid.nx * farGrid.ny;
    if (fb.byteLength >= n * 4) farHeightfield = new Float32Array(fb.buffer.slice(fb.byteOffset, fb.byteOffset + n * 4));
  }
  const far = farGrid && farHeightfield ? { heightfield: farHeightfield, x0: farGrid.x0, y0: farGrid.y0, dx: farGrid.dx, nx: farGrid.nx, ny: farGrid.ny } : null;
  // (until 20 Oct 2026 selfplay / sim_race / selfplay_trace built their per-car surfaces with the pit lane only: no
  // sausages, no kerb profile, no far terrain, unlike the app's race)
  const makeSurface = () => createTrackSurface(track, heightfield, { far, pitLane, sausages: scenery?.sausages ?? null, kerbs: scenery?.kerbs ?? null });
  const surface = makeSurface();
  // the track id keys corner-specific racecraft (issue #19); a package given by directory takes the id whose dir it is
  const trackId = Object.prototype.hasOwnProperty.call(TRACKS, idOrDir) ? idOrDir : Object.keys(TRACKS).find((k) => resolve(ROOT, 'public/' + TRACKS[k].dir) === D) ?? '';
  const line = new RaceLine(track, ghosts, undefined, trackId);
  if (scenery?.pit_exit_cones?.pts?.length) line.restrictLeft(scenery.pit_exit_cones.pts);
  return { track, ghosts, scenery, surface, line, pitLane, heightfield, farHeightfield, makeSurface };
}

export function loadProbeJson(): any { return JSON.parse(readFileSync(resolve(ROOT, 'public/cars/probe_gt/car.json'), 'utf8')); }
export function loadPace(trackId: string = DEFAULT_TRACK): PaceJson { return JSON.parse(readFileSync(pacePath(trackId), 'utf8')); }
/** The track's identity rows by field key (`id`, else number); empty when there is no identity file. */
export function loadIdentity(trackId: string = DEFAULT_TRACK): Map<string, IdentityCar> {
  const j = loadIdentityJson(trackId);
  return j ? parseIdentity(j) : new Map();
}
