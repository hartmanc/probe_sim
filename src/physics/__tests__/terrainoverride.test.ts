// Terrain override (scenery.json terrain_override, Sonoma round 14A): inside a region the off-pavement surface and the
// paved parts are the heightfield itself (no 5 m shoulder blend, no dirt roughness), weighted in over the region's ramp;
// without one the surface is bit for bit what it was.
import { describe, expect, test } from 'vitest';
import { createTrackSurface, terrainOverrideWeightFn } from '../index';
import { REGION, continuation, heightfieldOf, ovalTrack, stripPart } from './terrain_fixture';

const track = ovalTrack();
// lumpy lidar-like ground: the course's plane plus 0.2 m bumps
const lumpy = (x: number, y: number) => continuation(x, y) - 0.4 + 0.2 * Math.sin(x / 3.1) * Math.cos(y / 2.3);
const hfLumpy = heightfieldOf(track, lumpy);
const hfSmooth = heightfieldOf(track, continuation);
const H = track.heightfield;
const bilinear = (hf: Float32Array, x: number, y: number) => {
  const fx = (x - H.x0) / H.dx, fy = (y - H.y0) / H.dx, j = Math.floor(fx), i = Math.floor(fy), tx = fx - j, ty = fy - i, k = i * H.nx + j;
  const a = hf[k] + tx * (hf[k + 1] - hf[k]), b = hf[k + H.nx] + tx * (hf[k + H.nx + 1] - hf[k + H.nx]);
  return a + ty * (b - a);
};

describe('terrain override', () => {
  test('absent, empty or far away: every sample bit for bit the surface without it', () => {
    const plain = createTrackSurface(track, hfLumpy);
    const empty = createTrackSurface(track, hfLumpy, { terrainOverride: { regions: [] } });
    const far = createTrackSurface(track, hfLumpy, { terrainOverride: { regions: [{ ramp: 2, poly: [[200, 180], [240, 180], [240, 210], [200, 210]] }] } });
    let n = 0;
    for (let x = -120; x <= 120; x += 3.7) for (let y = -30; y <= 30; y += 1.3) {
      const a = plain.sample(x, y), za = a.z, ma = a.mu, nxa = a.nx;
      for (const s of [empty, far]) { const b = s.sample(x, y); expect(b.z).toBe(za); expect(b.mu).toBe(ma); expect(b.nx).toBe(nxa); }
      n++;
    }
    expect(n).toBeGreaterThan(1000);
  });

  test('inside a region off pavement: the heightfield itself, from the edge out (no shoulder blend, no roughness)', () => {
    const s = createTrackSurface(track, hfLumpy, { terrainOverride: REGION });
    for (const y of [-5.2, -6, -8, -12, -20, 5.3, 9, 25]) for (const x of [-40, -10, 0, 17, 40]) {
      expect(Math.abs(s.sample(x, y).z - bilinear(hfLumpy, x, y))).toBeLessThan(1e-9);
    }
    // the plain surface blends from the edge to the ground over 5 m and carries the dirt roughness: different
    const plain = createTrackSurface(track, hfLumpy);
    expect(Math.abs(plain.sample(0, -7).z - bilinear(hfLumpy, 0, -7))).toBeGreaterThan(0.01);
  });

  test('on the course: unchanged by the override', () => {
    const s = createTrackSurface(track, hfLumpy, { terrainOverride: REGION }), plain = createTrackSurface(track, hfLumpy);
    for (let x = -50; x <= 50; x += 2.3) for (let y = -4.9; y <= 4.9; y += 0.7) {
      const a = s.sample(x, y);
      expect(a.onTrack).toBe(true);
      expect(a.z).toBe(plain.sample(x, y).z);
    }
  });

  test('a paved part inside a region lies on the heightfield (its 7-point profile cannot step against the ground)', () => {
    // the strip's own profile 0.1 m off the ground: inside the region the surface is the ground, paved
    const part = stripPart((x, y) => lumpy(x, y) + 0.1);
    const pitLane = { spacing_m: 1, fractions: track.profile.fractions, parts: [part] };
    const s = createTrackSurface(track, hfLumpy, { pitLane, terrainOverride: REGION });
    const q = s.sample(5, -11);
    expect(q.paved).toBe(true);
    expect(Math.abs(q.z - bilinear(hfLumpy, 5, -11))).toBeLessThan(1e-9);
    // outside the region the part keeps its own profile
    const s2 = createTrackSurface(track, hfLumpy, { pitLane, terrainOverride: { regions: [{ ramp: 1, poly: [[100, -40], [140, -40], [140, 40], [100, 40]] }] } });
    expect(Math.abs(s2.sample(5, -11).z - (lumpy(5, -11) + 0.1))).toBeLessThan(0.02);
  });

  test('continuous across the ramp at the region boundary, and the weight is 0 outside, 1 deep inside', () => {
    // as built: the override surface continues the course near its edges and leaves it beyond (here 0.2 m bumps from
    // 4 m out); the region's ramp crosses the course, its shoulder and the bumps
    const sm = (t: number) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
    const built = (x: number, y: number) => continuation(x, y) + 0.2 * Math.sin(x / 3.1) * Math.cos(y / 2.3) * sm((Math.abs(y) - 5) / 4);
    const s = createTrackSurface(track, heightfieldOf(track, built), { terrainOverride: REGION });
    const w = terrainOverrideWeightFn(REGION);
    expect(w(70, -10)).toBe(0); expect(w(0, -10)).toBe(1); expect(w(59.25, -10)).toBeGreaterThan(0); expect(w(59.25, -10)).toBeLessThan(1);
    for (const y of [-5.5, -7, -9]) {
      let prev = s.sample(56, y).z;
      for (let x = 56.05; x <= 64; x += 0.05) {
        const z = s.sample(x, y).z;
        expect(Math.abs(z - prev)).toBeLessThan(0.005);   // under 10 % over 5 cm: no step
        prev = z;
      }
    }
  });

  test('with the heightfield continuing the course (C1), the edge has no step and no cross-slope change', () => {
    const s = createTrackSurface(track, hfSmooth, { terrainOverride: REGION });
    for (const x of [-30, 0, 30]) for (const side of [1, -1]) {
      const e = side * 5, at = (d: number) => s.sample(x, e + side * d).z;
      expect(Math.abs(at(0.02) - at(-0.02))).toBeLessThan(0.002);
      const si = (at(-0.05) - at(-1.05)), so = (at(1.05) - at(0.05));
      expect(Math.abs(Math.atan(so) - Math.atan(si)) * 180 / Math.PI).toBeLessThan(0.1);
    }
    // the plain surface's shoulder flattens the cross-slope at the edge (3 % -> 0): the change the override removes
    const plain = createTrackSurface(track, hfSmooth, { roughness: 0 });
    const at = (d: number) => plain.sample(0, -5 - d).z;
    expect(Math.abs(Math.atan(at(1.05) - at(0.05)) - Math.atan(at(-0.05) - at(-1.05))) * 180 / Math.PI).toBeGreaterThan(1);
  });
});
