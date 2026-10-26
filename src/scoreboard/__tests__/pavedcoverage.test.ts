// Paved coverage (tools/track/gates/pavedCoverage.ts; Buttonwillow round 13, GPT 6 Astra's review): the drawn paddock
// bands of the published Buttonwillow package are paved in the physics everywhere off their edges, and the gate finds a
// seam when one is put in (a narrow part inside a band takes the points nearer its centre line than to the band's).
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { pavedCoverage } from '../../../tools/track/gates/pavedCoverage';
import { loadHeightfield } from '../../physics/index';

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

// round 14 review (GPT 6 Astra, the blocker): the pit lane's drawn strip beside the front straight is in the gate too
// (lane_box), so a mouth part whose centre takes lane samples behind the pit wall fails the build
const LANE = { parts: ['^front straight mouth '], step: 0.5, wall_clear: 0.4, edge_tol: 0.1, lane_box: [-205, -245, 245, -175] as [number, number, number, number] };
describe('paved coverage of the front-straight mouths and the pit lane beside them', () => {
  it('every drawn sample of the mouths and of the lane beside the straight is paved', () => {
    const r = pavedCoverage(track, hf, scenery(), LANE);
    expect(r.parts).toBeGreaterThanOrEqual(10);
    expect(r.samples).toBeGreaterThan(20000);
    expect(r.holes).toEqual([]);
  }, 120000);
  it('without the lane band behind mouth A the lane behind the wall is a seam the gate finds', () => {
    const sc = scenery();
    sc.paved_zones.parts = sc.paved_zones.parts.filter((p: any) => !/^front straight mouth A lane/.test(p.turn));
    const r = pavedCoverage(track, hf, sc, LANE);
    const lane = r.holes.filter((h) => h.part === 'pit lane');
    expect(lane.length).toBeGreaterThan(0);
    // all of them behind mouth A (x -40 .. 10, north of the pit wall)
    expect(lane.every((h) => h.x > -45 && h.x < 15 && h.y > -219)).toBe(true);
  }, 120000);
});
