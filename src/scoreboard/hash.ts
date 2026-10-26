// physicsVersion: a short stable id of "what the replay depends on", computed identically in the
// browser (from the fetched car.json) and on the server (from the bundled car.json).
import { PHYSICS_KEY_PINS, PHYSICS_VERSION } from './config';

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

/** car.json without its comments: keys starting with "_" anywhere are ignored by src/physics/spec.ts, so they are not
 *  part of the physics either (0.4.0: editing a comment no longer opens fresh boards). */
export function stripComments(v: unknown): unknown {
  if (v === null || typeof v !== 'object') return v;
  if (Array.isArray(v)) return v.map(stripComments);
  const out: Record<string, unknown> = {};
  for (const [k, x] of Object.entries(v as Record<string, unknown>)) if (!k.startsWith('_')) out[k] = stripComments(x);
  return out;
}

/**
 * Physics version string: PHYSICS_VERSION + hash(car.json without comments) + track length (+ the track's rev). Boards
 * are keyed by it, so a recalibration of car.json (or a PHYSICS_VERSION bump) starts fresh boards. A computed value
 * listed in PHYSICS_KEY_PINS answers the board key it was published under (config.ts).
 */
export function physicsVersion(carJson: unknown, trackLengthM: number, trackRev?: string): string {
  // trackRev (TRACKS[id].rev, 20 Oct 2026): a per-track geometry revision / package fingerprint, so a rebuilt track opens
  // its own fresh boards without a global PHYSICS_VERSION bump; absent (Laguna) the key is exactly as before
  const h = cyrb53(`${PHYSICS_VERSION}|${trackLengthM}|${canonicalJson(stripComments(carJson))}` + (trackRev ? `|${trackRev}` : ''));
  const v = h.toString(36).padStart(11, '0');
  return Object.hasOwn(PHYSICS_KEY_PINS, v) ? PHYSICS_KEY_PINS[v] : v;
}
