// Server-side asset loading for the replay: reads track/car files from public/ on disk.
// On Vercel they are shipped with the function through vercel.json `functions["api/scores.ts"].includeFiles`
// (paths stay relative to the project root, so they land at <cwd>/public/...). Locally the same paths work.
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadHeightfield, type TrackJson } from '../../src/physics/index';
import { CARS, TRACKS } from '../../src/scoreboard/config';
import { physicsVersion } from '../../src/scoreboard/hash';
import type { GhostsLike, SceneryLike, SimAssets } from '../../src/scoreboard/sim';

function publicRoot(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    process.env.SCOREBOARD_ASSET_ROOT,
    join(process.cwd(), 'public'),
    resolve(here, '../../public'),
  ].filter((x): x is string => !!x);
  for (const c of candidates) if (existsSync(join(c, 'tracks'))) return c;
  throw new Error(`scoreboard assets not found (looked in ${candidates.join(', ')})`);
}

const toAB = (b: Uint8Array): ArrayBuffer => b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;

const cache = new Map<string, SimAssets>();
const carCache = new Map<string, unknown>();
const trackCache = new Map<string, TrackJson>();

function readCar(car: string): unknown {
  let j = carCache.get(car);
  if (j === undefined) {
    j = JSON.parse(readFileSync(join(publicRoot(), CARS[car].dir, 'car.json'), 'utf8'));
    carCache.set(car, j);
  }
  return j;
}
function readTrack(track: string): TrackJson {
  let t = trackCache.get(track);
  if (!t) {
    t = JSON.parse(readFileSync(join(publicRoot(), TRACKS[track].dir, 'track.json'), 'utf8')) as TrackJson;
    trackCache.set(track, t);
  }
  return t;
}

/** Decoded sim assets for a whitelisted track + car, cached for the life of the (warm) function instance. */
export async function loadSimAssets(track: string, car: string): Promise<SimAssets> {
  if (!(track in TRACKS) || !(car in CARS)) throw new Error('not whitelisted');
  const key = `${track}/${car}`;
  let a = cache.get(key);
  if (a) return a;
  const root = publicRoot();
  const tdir = join(root, TRACKS[track].dir);
  const t = readTrack(track);
  const scenery = existsSync(join(tdir, 'scenery.json')) ? JSON.parse(readFileSync(join(tdir, 'scenery.json'), 'utf8')) as SceneryLike : null;
  const farFile = scenery?.far?.heightfield?.file;
  a = {
    trackId: track, carId: car, track: t,
    heightfield: loadHeightfield(toAB(readFileSync(join(tdir, t.heightfield?.file ?? 'heightfield.bin')))),
    carJson: readCar(car),
    scenery,
    farHeightfield: farFile && existsSync(join(tdir, farFile)) ? loadHeightfield(toAB(readFileSync(join(tdir, farFile)))) : null,
    ghosts: JSON.parse(readFileSync(join(tdir, 'ghosts.json'), 'utf8')) as GhostsLike,
  };
  cache.set(key, a);
  return a;
}

/** The server's physicsVersion() for a track + car (reads only car.json and track.json). */
export async function serverPhysics(track: string, car: string): Promise<string> {
  if (!(track in TRACKS) || !(car in CARS)) throw new Error('not whitelisted');
  return physicsVersion(readCar(car), readTrack(track).length_m);
}
