// Raised kerb profile (scenery.json kerbs.profile, 20 Oct 2026): Sonoma's stepped concrete kerbs lift the surface by
// their height on the band, rise over the track-side face, and leave a kerb set without a profile (Laguna) flat.
import { describe, expect, it } from 'vitest';
import { createDevTrack } from '../devtrack';
import { createTrackSurface, kerbBandCentre, type KerbsJson } from '../track';

const dev = createDevTrack();
const strips = [{ side: 1, s0: 100, s1: 130, off: 0.3 }];
const K: KerbsJson = { width: 0.65, inside: true, profile: { height: 0.1, face: 0.25, back: 0.3 }, strips };
const plain = createTrackSurface(dev.track, dev.heightfield);
const raised = createTrackSurface(dev.track, dev.heightfield, { kerbs: K });
const flat = createTrackSurface(dev.track, dev.heightfield, { kerbs: { ...K, profile: null } });

/** Point `o` m beyond the left edge at station i. */
function at(i: number, o: number): [number, number] {
  const t = dev.track, n = t.n;
  const a = t.center[(i - 1 + n) % n], b = t.center[(i + 1) % n];
  const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy);
  const e = t.left[i];
  return [e[0] + (-dy / l) * o, e[1] + (dx / l) * o];
}
const dz = (s: typeof raised, i: number, o: number) => { const [x, y] = at(i, o); return s.sample(x, y).z - plain.sample(x, y).z; };

describe('raised kerb profile', () => {
  it('band centre: off when given, else the inside convention', () => {
    expect(kerbBandCentre(K, { off: 0.3 })).toBe(0.3);
    expect(kerbBandCentre({ ...K, inside: true }, {})).toBeCloseTo(-0.325, 9);
    expect(kerbBandCentre({ ...K, inside: false }, {})).toBeCloseTo(0.325, 9);
  });
  it('lifts the band by its height, nothing on the track or past the back slope', () => {
    expect(dz(raised, 115, 0.3)).toBeCloseTo(0.1, 3);              // band centre
    expect(dz(raised, 115, 0.6)).toBeCloseTo(0.1, 3);              // flat top to the outer limit (0.625)
    expect(Math.abs(dz(raised, 115, -0.5))).toBeLessThan(1e-9);    // on the track, inside the face
    expect(Math.abs(dz(raised, 115, 0.3 + 0.325 + 0.35))).toBeLessThan(1e-9); // past the back slope
  });
  it('rises over the face (a step you feel, slope capped) and ramps at the strip ends', () => {
    const mid = dz(raised, 115, 0.3 - 0.325 + 0.125);
    expect(mid).toBeGreaterThan(0.03); expect(mid).toBeLessThan(0.07);
    const [x, y] = at(115, 0.3 - 0.325 + 0.125);
    const s = raised.sample(x, y);
    expect(Math.hypot(s.nx, s.ny) / s.nz).toBeGreaterThan(0.3);
    expect(Math.hypot(s.nx, s.ny) / s.nz).toBeLessThanOrEqual(0.6 + 0.01);   // the cap plus the road's own cross-slope
    expect(dz(raised, 100, 0.3)).toBeLessThan(0.02);
  });
  it('no profile: flat paint, the surface is unchanged (Laguna)', () => {
    for (const o of [-0.5, 0, 0.3, 0.6, 1]) expect(Math.abs(dz(flat, 115, o))).toBeLessThan(1e-12);
  });
  it('a run\'s own profile (Buttonwillow T9, 21 Oct 2026): raised on that run only, the track default flat', () => {
    const runs: KerbsJson = { width: 0.65, inside: true, profile: null,
      strips: [{ side: 1, s0: 100, s1: 130, off: 0.3, profile: { height: 0.06, face: 0.15, back: 0.3 } }, { side: 1, s0: 200, s1: 230, off: 0.3 }] };
    const r = createTrackSurface(dev.track, dev.heightfield, { kerbs: runs });
    expect(dz(r, 115, 0.3)).toBeCloseTo(0.06, 3);
    for (const o of [-0.5, 0, 0.3, 0.6, 1]) expect(Math.abs(dz(r, 215, o))).toBeLessThan(1e-12);
  });
  it('a run profile equal to the default gives the same surface as the default (Sonoma unchanged)', () => {
    const same = createTrackSurface(dev.track, dev.heightfield, { kerbs: { ...K, strips: strips.map((s) => ({ ...s, profile: K.profile })) } });
    for (const i of [100, 104, 115, 126, 130]) for (const o of [-0.5, -0.02, 0.1, 0.3, 0.6, 0.8, 1.1]) expect(dz(same, i, o)).toBe(dz(raised, i, o));
  });
});
