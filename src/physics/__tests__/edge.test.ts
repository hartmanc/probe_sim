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
