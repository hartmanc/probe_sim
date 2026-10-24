// Ground marks on the driven surface (tools/track/gates/groundMarks.ts, Sonoma round 14B; judge r14a: the drag-strip
// continuation's edge line buried under its draped zone). A paint line built on another surface than the one the car
// drives on (the zone's centre height, the raw heightfield before an override) fails the gate; draped, it passes; the
// edge lines and ground signs the app drapes itself pass; the published Sonoma package's marks, draped, all pass.
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { loadHeightfield } from '../../physics/index';
import { drapeMarks, groundMarksGate, MARKS_TOL, PAINT_LIFT } from '../../../tools/track/gates/groundMarks';
import { REGION, continuation, heightfieldOf, ovalTrack, stripPart } from '../../physics/__tests__/terrain_fixture';

const track = ovalTrack();
type V3 = [number, number, number];
const line = (y: number, z: (x: number) => number, src = 'test line') => ({ width: 0.12, src, pts: Array.from({ length: 41 }, (_, i) => [-20 + i, y, z(-20 + i)] as V3) });

describe('ground marks on surface: synthetic', () => {
  // the override surface continues the course; the strip (8-14 m right) built 0.2 m lower than it, then draped
  const hf = heightfieldOf(track, continuation);
  const sc = () => ({ terrain_override: REGION, paved_zones: { spacing_m: 1, fractions: track.profile.fractions, parts: [stripPart(continuation)] },
    edge_lines: { width: 0.12, inset: 0.15, runs: [{ side: 1, s0: 100, s1: 200 }, { side: -1, s0: 100, s1: 200 }] },
    ground_signs: [{ x: 0, y: -11, z: 0, heading: 0, length: 8, height: 2, text: 'TEST', fg: '#fff' }] });

  it('a line at its zone\'s pre-drape height (0.2 m under the surface) fails; one floating 0.05 m over it fails', () => {
    const buried = { ...sc(), paint_lines: [line(-9, (x) => continuation(x, -9) - 0.2)] };
    const r = groundMarksGate(track, hf, buried);
    expect(r.bad.length).toBe(41);
    expect(r.minD).toBeLessThan(-0.19);
    const floating = { ...sc(), paint_lines: [line(-9, (x) => continuation(x, -9) + 0.05)] };
    expect(groundMarksGate(track, hf, floating).bad.length).toBe(41);
  });

  it('draped: every paint-line vertex lies PAINT_LIFT over the surface and the gate passes; edge lines and signs pass', () => {
    const s = { ...sc(), paint_lines: [line(-9, (x) => continuation(x, -9) - 0.2), line(-13, () => 1.0)] };
    const d = drapeMarks(track, hf, s);
    expect(d.paint).toBe(82);
    expect(d.maxChange).toBeGreaterThan(0.19);
    const r = groundMarksGate(track, hf, s);
    expect(r.bad).toHaveLength(0);
    expect(r.vertices.edge).toBeGreaterThan(300);
    expect(r.vertices.sign).toBe(85);
    expect(r.minD).toBeGreaterThanOrEqual(0);
    expect(r.maxD).toBeLessThanOrEqual(MARKS_TOL);
    expect(Math.abs(r.minD - PAINT_LIFT)).toBeLessThan(0.0011);
  });

  it('cones, kerb lines and ground signs take the surface height', () => {
    const s: any = { ...sc(), cone_lines: [{ spacing_m: 4, pts: [[0, -9, 5], [4, -9, 5]] }], kerb_lines: [{ pts: [[-5, -15, -3], [5, -15, -3]], width: 1, height: 0.05, stripe_m: 1, colors: ['#fff'] }] };
    drapeMarks(track, hf, s);
    for (const P of [...s.cone_lines[0].pts, ...s.kerb_lines[0].pts]) expect(Math.abs(P[2] - continuation(P[0], P[1]))).toBeLessThan(0.002);
    expect(Math.abs(s.ground_signs[0].z - continuation(0, -11))).toBeLessThan(0.002);
  });
});

describe('ground marks on surface: the published Sonoma package', () => {
  const dir = fileURLToPath(new URL('../../../public/tracks/sonoma/', import.meta.url));
  const has = existsSync(dir + 'scenery.json');
  it.runIf(has)('its marks draped on its own surface all pass (the drape is what stage 3 does with scenery.marks_on_surface)', () => {
    const t = JSON.parse(readFileSync(dir + 'track.json', 'utf8'));
    const sc = JSON.parse(readFileSync(dir + 'scenery.json', 'utf8'));
    const hf = loadHeightfield(Uint8Array.from(readFileSync(dir + 'heightfield.bin')).buffer);
    drapeMarks(t, hf, sc);
    const r = groundMarksGate(t, hf, sc);
    expect(r.vertices.paint).toBeGreaterThan(1000);
    expect(r.bad).toHaveLength(0);
  });
});
