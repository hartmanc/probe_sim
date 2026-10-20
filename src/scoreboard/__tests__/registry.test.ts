// The track registry agrees with the published packages (20 Oct 2026): length, a per-track rolling start that is not
// just past a hairpin, and Laguna's board key unchanged by the per-track revision.
import { describe, expect, test } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { TRACKS } from '../config';
import { physicsVersion } from '../hash';
import { canonicalReset } from '../sim';

const ROOT = resolve(__dirname, '../../..');
const trackJson = (id: string) => JSON.parse(readFileSync(resolve(ROOT, 'public', TRACKS[id].dir, 'track.json'), 'utf8'));

describe('track registry', () => {
  test.each(Object.keys(TRACKS))('%s: package exists and its length matches the registry', (id) => {
    expect(existsSync(resolve(ROOT, 'public', TRACKS[id].dir, 'track.json'))).toBe(true);
    expect(trackJson(id).length_m).toBe(TRACKS[id].length_m);
    expect(existsSync(resolve(ROOT, 'public', TRACKS[id].pace))).toBe(true);
  });
  test.each(Object.keys(TRACKS).filter((id) => TRACKS[id].rev))('%s: rev is the fingerprint of the published package', (id) => {
    const h = createHash('sha256');
    // the files the package has (a package before its scenery stage has no scenery.json / far_heightfield.bin;
    // Buttonwillow, 20 Oct 2026): a complete package's rev is unchanged
    for (const f of ['track.json', 'heightfield.bin', 'ghosts.json', 'scenery.json', 'far_heightfield.bin'])
      if (existsSync(resolve(ROOT, 'public', TRACKS[id].dir, f)))
        h.update(createHash('sha256').update(readFileSync(resolve(ROOT, 'public', TRACKS[id].dir, f))).digest());
    expect(h.digest('hex').slice(0, 10)).toBe(TRACKS[id].rev);
  });
  test('Laguna keeps its 0.2.0 board key and rolling start rule', () => {
    expect(TRACKS.laguna_seca.rev).toBeUndefined();
    const car = { a: 1 };
    expect(physicsVersion(car, 3588.048, TRACKS.laguna_seca.rev)).toBe(physicsVersion(car, 3588.048));
    expect(TRACKS.laguna_seca.start).toEqual({ beforeCorner: 'T11', m: 230, speed: 22 });
    const t = trackJson('laguna_seca');
    expect(canonicalReset(t, () => 0, TRACKS.laguna_seca.start)).toEqual(canonicalReset(t));
  });
  test.each(Object.keys(TRACKS))('%s: the rolling start is at least 150 m past a hairpin apex (radius under 30 m)', (id) => {
    const t = trackJson(id);
    const st = TRACKS[id].start;
    const s = 's_m' in st ? st.s_m : (t.corners.find((c: { turn?: string }) => c.turn === st.beforeCorner).s - st.m + t.length_m) % t.length_m;
    const prev = t.corners.filter((c: { dir?: string | null; radius_m?: number | null }) => c.dir && (c.radius_m ?? 999) < 30)
      .map((c: { s: number }) => (s - c.s + t.length_m) % t.length_m);
    expect(Math.min(...prev)).toBeGreaterThan(150);
  });
});
