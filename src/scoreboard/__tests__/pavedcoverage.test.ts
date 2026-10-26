// Paved coverage (tools/track/gates/pavedCoverage.ts; Buttonwillow round 13, GPT 6 Astra's review): the drawn paddock
// bands of the published Buttonwillow package are paved in the physics everywhere off their edges, and the gate finds a
// seam when one is put in (a narrow part inside a band takes the points nearer its centre line than to the band's).
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { pavedCoverage } from '../../../tools/track/gates/pavedCoverage';
import { loadHeightfield } from '../../physics/index';
import { createTrackSurface, packageSurfaceOptions } from '../../physics/track';

const DIR = resolve(__dirname, '../../../public/tracks/buttonwillow');
const track = JSON.parse(readFileSync(join(DIR, 'track.json'), 'utf8'));
const hf = Float32Array.from(loadHeightfield(Uint8Array.from(readFileSync(join(DIR, 'heightfield.bin'))).buffer));
const scenery = () => JSON.parse(readFileSync(join(DIR, 'scenery.json'), 'utf8'));
const OPTS = { parts: ['^paddock band '], step: 0.5, wall_clear: 0.4, edge_tol: 0.1 };

describe('paved coverage of the Buttonwillow paddock bands', () => {
  it('every drawn sample off the edges is paved', () => {
    const r = pavedCoverage(track, hf, scenery(), OPTS);
    expect(r.parts).toBe(7);
    expect(r.samples).toBeGreaterThan(30000);
    expect(r.holes).toEqual([]);
  }, 120000);
  it('a narrow part inside a band leaves a seam the gate finds', () => {
    const sc = scenery();
    const T = sc.paved_zones.parts.find((p: any) => /^paddock band T/.test(p.turn));
    // 12 points of band T's centre line moved 3 m toward its left edge, 1 m wide: a part whose centre is nearer than T's
    const k0 = 120, n = 12;
    const sl = (A: number[][], off: number) => A.slice(k0, k0 + n).map((c: number[], i: number) => {
      const L = T.left[k0 + i], C = T.center[k0 + i], d = Math.hypot(L[0] - C[0], L[1] - C[1]);
      const ux = (L[0] - C[0]) / d, uy = (L[1] - C[1]) / d;
      return [c[0] + ux * off, c[1] + uy * off, c[2]];
    });
    const seam = { ...T, turn: 'paddock band seam (test)', n, center: sl(T.center, 3), left: sl(T.center, 3.5), right: sl(T.center, 2.5),
      profile_z: T.profile_z.slice(k0, k0 + n), gap_left: T.gap_left.slice(k0, k0 + n), gap_right: T.gap_right.slice(k0, k0 + n) };
    sc.paved_zones.parts.push(seam);
    const r = pavedCoverage(track, hf, sc, OPTS);
    expect(r.holes.length).toBeGreaterThan(0);
    // every hole lies by the inserted part (none elsewhere)
    const near = (h: { x: number; y: number }) => seam.center.some((c: number[]) => Math.hypot(c[0] - h.x, c[1] - h.y) < 8);
    expect(r.holes.every(near)).toBe(true);
  }, 120000);
});

// round 14 (GPT 6 Astra's reviews; the owner's decisions of 26 Oct 2026): the pit lane's drawn strip in the box the
// mouths reach (derived from their bounds + 10 m, not a hand box), the paddock aisle's end beside the lane, and the
// owner's own outlines (owner/r14_mouths.json, his green strokes) are paved in the physics; a mouth part whose centre
// takes lane samples fails; the lane's own edge on his line leaves the dirt median unpaved
const OWN = JSON.parse(readFileSync(resolve(__dirname, '../../../tools/track/tracks/buttonwillow/owner/r14_mouths.json'), 'utf8'));
const LANE = {
  parts: ['^front straight mouth '], step: 0.5, wall_clear: 0.4, edge_tol: 0.1, lane: { margin: 10 },
  also: [{ parts: ['^paddock lanes'], near_lane: 10 }],
  outlines: OWN.mouths.map((m: any) => ({ name: m.name, poly: m.outline_enu })),
};
describe('paved coverage of the front-straight mouths, the pit lane beside them and the owner outlines', () => {
  it('every drawn sample of the mouths, the lane, the aisle end and his outlines is paved', () => {
    const r = pavedCoverage(track, hf, scenery(), LANE);
    expect(r.parts).toBeGreaterThanOrEqual(5);
    expect(r.lane!.samples).toBeGreaterThan(15000);
    expect(r.also!.samples).toBeGreaterThan(50);
    expect(r.outlines!.samples).toBeGreaterThan(1500);
    expect(r.holes).toEqual([]);
  }, 180000);
  it('a mouth centre moved toward the lane takes lane samples: a seam the gate finds, by mouth B only', () => {
    const sc = scenery();
    const B = sc.paved_zones.parts.find((p: any) => /^front straight mouth B/.test(p.turn));
    B.center = B.center.map((c: number[]) => [c[0], c[1] + 6, c[2]]);
    const r = pavedCoverage(track, hf, sc, LANE);
    const lane = r.holes.filter((h) => h.part === 'pit lane');
    expect(lane.length).toBeGreaterThan(0);
    expect(lane.every((h) => h.x > 25 && h.x < 75)).toBe(true);
  }, 180000);
  it('the aisle end keeps its round-13 footprint (to y -200.75), paved; without the block across it, it is not', () => {
    // OSM 10409813's end as round 13 drew it: x -136.6 .. -128.6, y -200.75 .. -197 (0.2 m inside each side)
    const paved = (sc: any) => {
      const surf = createTrackSurface(track, hf, packageSurfaceOptions(sc));
      let n = 0, p = 0;
      for (let x = -136.4; x <= -128.8; x += 0.2) for (let y = -200.55; y <= -197.2; y += 0.2) { n++; if (surf.sample(x, y).paved) p++; }
      return [n, p];
    };
    const [n, p] = paved(scenery());
    expect(n).toBeGreaterThan(500);
    expect(p).toBe(n);
    const sc = scenery();
    sc.paved_zones.parts = sc.paved_zones.parts.filter((q: any) => !/^paddock lanes \(the aisle end/.test(q.turn));
    expect(paved(sc)[1]).toBeLessThan(n);
  }, 180000);
});

// round 14 (Astra's second review 4): the physics' surface across a bent lane band's boundary and across each mouth's
// boundary with the lane: no step between neighbouring samples 1 cm apart beyond the surface's own slope
describe('the lane band and the mouths meet the lane level in the physics', () => {
  it('transects every 1 m across mouths A, B, C and E and the lane: no step over 3 mm per cm', () => {
    const surf = createTrackSurface(track, hf, packageSurfaceOptions(scenery()));
    const sc = scenery();
    const lane = sc.pit_lane.parts[0];
    let worst = 0, at = '';
    for (const [x0, x1] of [[-30, 0], [35, 65], [-205, -150], [215, 232]]) {
      for (let x = x0; x <= x1; x += 1) {
        // from the lane's centre (nearest station) south 12 m, every cm, paved samples only
        const c = lane.center.reduce((b: number[], q: number[]) => (Math.abs(q[0] - x) < Math.abs(b[0] - x) ? q : b));
        let prev: number | null = null;
        for (let k = 0; k <= 1200; k++) {
          const y = c[1] - k * 0.01;
          const s = surf.sample(x, y);
          if (!s.paved) { prev = null; continue; }
          if (prev !== null && Math.abs(s.z - prev) > worst) { worst = Math.abs(s.z - prev); at = `${x}, ${y.toFixed(2)}`; }
          prev = s.z;
        }
      }
    }
    expect(worst, at).toBeLessThan(0.003);
  }, 180000);
});
