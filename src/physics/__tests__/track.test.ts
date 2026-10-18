import { describe, expect, test } from 'vitest';
import { createTrackProjector, createTrackSurface, lineToWorld, loadHeightfield, OFF_PAVEMENT_MU } from '../index';
import { createDevTrack, devGround } from '../devtrack';
import { rng } from './helpers';

const { track, heightfield, options } = createDevTrack();

/** Centreline point + left normal at s, computed independently from the generator's geometry. */
function frame(s: number): { x: number; y: number; nx: number; ny: number } {
  const p = lineToWorld(track, () => 0, s);
  return { x: p.pos[0], y: p.pos[1], nx: -Math.sin(p.heading), ny: Math.cos(p.heading) };
}

function sDiff(a: number, b: number): number {
  const L = track.length_m;
  let d = (a - b) % L;
  if (d > L / 2) d -= L;
  if (d < -L / 2) d += L;
  return d;
}

describe('6. track surface and projection', () => {
  test('dev track is a consistent track.json', () => {
    expect(track.n).toBe(2000);
    expect(track.length_m).toBe(2000);
    expect(heightfield.length).toBe(track.heightfield.nx * track.heightfield.ny);
    expect(track.profile.z.length).toBe(track.n);
  });

  test('profile height on track, heightfield height off track', () => {
    // Raise the heightfield by 1 m so the two sources are distinguishable.
    const hf = Float32Array.from(heightfield, (z) => z + 1);
    const surf = createTrackSurface(track, hf);
    const r = rng(1);
    for (let k = 0; k < 400; k++) {
      const s = r() * track.length_m;
      const f = frame(s);
      // on track
      const lat = (r() * 2 - 1) * 5.5;
      const x = f.x + lat * f.nx, y = f.y + lat * f.ny;
      const a = surf.sample(x, y);
      expect(a.onTrack).toBe(true);
      expect(a.mu).toBe(1.0);
      expect(Math.abs(a.z - devGround(x, y, options))).toBeLessThan(0.03);
      expect(a.nz).toBeGreaterThan(0.99);
      // off track (beyond the 5 m blend band: half-width 6 + 5)
      const off = (r() < 0.5 ? -1 : 1) * (12 + r() * 40);
      const xo = f.x + off * f.nx, yo = f.y + off * f.ny;
      const b = surf.sample(xo, yo);
      expect(b.onTrack).toBe(false);
      expect(b.mu).toBe(OFF_PAVEMENT_MU); // dry dirt (NOTES-surface.md; was 0.6)
      expect(Math.abs(b.z - (devGround(xo, yo, options) + 1))).toBeLessThan(0.03);
    }
    // far away: clamps to the heightfield
    const far = surf.sample(5000, 5000);
    expect(Number.isFinite(far.z)).toBe(true);
    expect(far.onTrack).toBe(false);
  });

  test('normal follows the slope of the hill', () => {
    const surf = createTrackSurface(track, heightfield);
    // back straight (y = +R) runs over the hill centred at x = 0; slope at x = −σ
    const x = -options.hillSigma, y = options.radius;
    const a = surf.sample(x, y);
    const z = (xx: number) => devGround(xx, y, options);
    const dzdx = (z(x + 0.01) - z(x - 0.01)) / 0.02;
    expect(a.onTrack).toBe(true);
    expect(a.nx / a.nz).toBeCloseTo(-dzdx, 2);
    expect(Math.abs(a.ny / a.nz)).toBeLessThan(0.005);
  });

  test('projector returns s within 1 m and the sign of lateral', () => {
    const proj = createTrackProjector(track);
    const r = rng(2);
    for (let k = 0; k < 500; k++) {
      const s = r() * track.length_m;
      const f = frame(s);
      const lat = (r() * 2 - 1) * 30;
      const p = proj.project(f.x + lat * f.nx, f.y + lat * f.ny);
      expect(Math.abs(sDiff(p.s, s))).toBeLessThan(1);
      if (Math.abs(lat) > 0.1) expect(Math.sign(p.lateral)).toBe(Math.sign(lat));
      expect(p.s).toBeGreaterThanOrEqual(0);
      expect(p.s).toBeLessThan(track.length_m);
      expect(p.index).toBeGreaterThanOrEqual(0);
      expect(p.index).toBeLessThan(track.n);
    }
    // the oval is ccw, so the infield is on the left
    expect(proj.project(0, 0).lateral).toBeGreaterThan(0);
    expect(proj.project(0, -200).lateral).toBeLessThan(0);
  });

  test('lineToWorld round-trips through the projector', () => {
    const proj = createTrackProjector(track);
    const surf = createTrackSurface(track, heightfield);
    const offset = (s: number) => 3 * Math.sin(s / 97);
    for (let s = 0; s < track.length_m; s += 7.3) {
      const w = lineToWorld(track, offset, s);
      const p = proj.project(w.pos[0], w.pos[1]);
      expect(Math.abs(sDiff(p.s, s))).toBeLessThan(0.05);
      expect(p.lateral).toBeCloseTo(offset(s), 2);
      expect(w.pos[2]).toBeCloseTo(surf.sample(w.pos[0], w.pos[1]).z, 3);
    }
    // heading: start/finish is on the front straight heading east
    expect(lineToWorld(track, () => 0, 0).heading).toBeCloseTo(0, 6);
  });

  test('loadHeightfield decodes float32 little-endian', () => {
    const buf = new ArrayBuffer(12);
    const dv = new DataView(buf);
    dv.setFloat32(0, 1.5, true); dv.setFloat32(4, -2.25, true); dv.setFloat32(8, 100, true);
    expect(Array.from(loadHeightfield(buf))).toEqual([1.5, -2.25, 100]);
    expect(() => loadHeightfield(new ArrayBuffer(6))).toThrow();
  });
});
