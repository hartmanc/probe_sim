// The track edge must be seamless: walking across it the height may slope but must not step.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';
import { createTrackSurface, lineToWorld, loadHeightfield, SHOULDER_WIDTH_M } from '../index';
import type { TrackJson } from '../index';

const dir = fileURLToPath(new URL('../../../public/tracks/laguna_seca/', import.meta.url));
const track = JSON.parse(readFileSync(dir + 'track.json', 'utf8')) as TrackJson;
const buf = readFileSync(dir + 'heightfield.bin');
const hf = loadHeightfield(Uint8Array.from(buf).buffer);

describe('track edge continuity (Laguna Seca)', () => {
  test('walking across both edges at the Corkscrew is continuous to 2 cm per 0.1 m step', () => {
    const surf = createTrackSurface(track, hf);
    const corkscrew = track.corners.filter((c) => c.name.startsWith('The Corkscrew'));
    expect(corkscrew.length).toBeGreaterThan(0);
    const step = 0.1;
    for (const c of corkscrew) {
      for (const ds of [-10, 0, 10]) {
        const p = lineToWorld(track, () => 0, c.s + ds);
        const nx = -Math.sin(p.heading), ny = Math.cos(p.heading);
        for (const side of [1, -1]) {
          // centre -> well past the edge and the shoulder
          const reach = 10 + SHOULDER_WIDTH_M + 3;
          const z: number[] = [];
          let sawEdge = false, prevOn = true;
          for (let d = 0; d <= reach; d += step) {
            const smp = surf.sample(p.pos[0] + side * d * nx, p.pos[1] + side * d * ny);
            if (prevOn && !smp.onTrack) sawEdge = true;
            prevOn = smp.onTrack;
            z.push(smp.z);
          }
          expect(sawEdge).toBe(true);
          // A step shows up as one increment far from its neighbours; a slope (banking, the 20 % grade, the
          // shoulder blending towards the heightfield) changes the increment smoothly.
          for (let k = 1; k < z.length - 1; k++) {
            const dz = z[k] - z[k - 1], next = z[k + 1] - z[k];
            expect(Math.abs(next - dz)).toBeLessThan(0.02);
          }
        }
      }
    }
  });
});

// 18 Oct 2026: the edges follow the painted road with the red/white apex kerbs included (kerbs are driveable
// pavement, drawn as `inside: true` strips on the ribbon). Walking out across each apex kerb strip in scenery.json the
// wheel keeps paved grip and a continuous height until it leaves the kerb's outer line.
describe('apex kerbs are pavement (Laguna Seca)', () => {
  const sc = JSON.parse(readFileSync(dir + 'scenery.json', 'utf8')) as {
    kerbs: { width: number; inside?: boolean; strips: { side: number; s0: number; s1: number; kind: string }[] };
  };
  const surf = createTrackSurface(track, hf);
  const apex = sc.kerbs.strips.filter((s) => s.kind === 'apex');
  test('kerbs sit inside the edge', () => { expect(sc.kerbs.inside).toBe(true); expect(apex.length).toBeGreaterThan(8); });
  test.each(apex.map((k) => [k.s0, k.s1, k.side] as const))('kerb s %i-%i side %i: paved grip and no step across it', (s0, s1, side) => {
    const i = Math.round((s0 + s1) / 2 / track.spacing_m) % track.n;   // strip ranges are metres
    const p = lineToWorld(track, () => 0, i * track.spacing_m);
    const nx = -Math.sin(p.heading), ny = Math.cos(p.heading);
    const e = side > 0 ? track.left[i] : track.right[i];
    const half = Math.hypot(e[0] - track.center[i][0], e[1] - track.center[i][1]);
    const z: number[] = [];
    for (let d = half - sc.kerbs.width - 0.5; d <= half - 0.05; d += 0.05) {
      const smp = surf.sample(p.pos[0] + side * d * nx, p.pos[1] + side * d * ny);
      expect(smp.onTrack).toBe(true);
      expect(smp.mu).toBeCloseTo(smp.muPaved ?? smp.mu, 6);
      z.push(smp.z);
    }
    for (let k = 1; k < z.length - 1; k++) expect(Math.abs((z[k + 1] - z[k]) - (z[k] - z[k - 1]))).toBeLessThan(0.02);
  });
});
