// physicsVersion: a short stable id of "what the replay depends on", computed identically in the
// browser (from the fetched car.json) and on the server (from the bundled car.json).
import { PHYSICS_VERSION } from './config';

/** cyrb53 string hash (53-bit, deterministic, no crypto needed). */
export function cyrb53(str: string, seed = 0): number {
  let h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return 4294967296 * (2097151 & h2) + (h1 >>> 0);
}

/** Key-order-independent JSON (sorted object keys), so formatting of car.json does not matter. */
export function canonicalJson(v: unknown): string {
  if (v === null || typeof v !== 'object') return JSON.stringify(v) ?? 'null';
  if (Array.isArray(v)) return '[' + v.map(canonicalJson).join(',') + ']';
  const o = v as Record<string, unknown>;
  return '{' + Object.keys(o).sort().filter((k) => o[k] !== undefined).map((k) => JSON.stringify(k) + ':' + canonicalJson(o[k])).join(',') + '}';
}

/**
 * Physics version string: PHYSICS_VERSION + hash(car.json) + track length. Boards are keyed by it,
 * so a recalibration of car.json (or a PHYSICS_VERSION bump) starts fresh boards.
 */
export function physicsVersion(carJson: unknown, trackLengthM: number): string {
  const h = cyrb53(`${PHYSICS_VERSION}|${trackLengthM}|${canonicalJson(carJson)}`);
  return h.toString(36).padStart(11, '0');
}
