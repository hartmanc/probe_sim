// Pit lane (scenery.json pit_lane): paved, full grip, and smooth along its centre and across its edges.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';
import { createTrackSurface, loadHeightfield } from '../index';
import type { PitLaneJson, TrackJson } from '../index';

const dir = fileURLToPath(new URL('../../../public/tracks/laguna_seca/', import.meta.url));
const track = JSON.parse(readFileSync(dir + 'track.json', 'utf8')) as TrackJson;
const hf = loadHeightfield(Uint8Array.from(readFileSync(dir + 'heightfield.bin')).buffer);
const scenery = JSON.parse(readFileSync(dir + 'scenery.json', 'utf8')) as { pit_lane: PitLaneJson; paved_zones?: PitLaneJson };
const pit = scenery.pit_lane;
const zones = scenery.paved_zones;

describe('pit lane surface', () => {
  test('walking the pit-lane centre: paved, mu 1.0, continuous heights', () => {
    expect(pit && pit.parts.length).toBeGreaterThan(0);
    const surf = createTrackSurface(track, hf, { pitLane: pit });
    const plain = createTrackSurface(track, hf);
    let checked = 0, differs = 0;
    for (const part of pit.parts) {
      let prev: number | null = null, prevDz: number | null = null;
      for (let i = 0; i < part.n - 1; i++) {
        for (const f of [0, 0.25, 0.5, 0.75]) {
          const a = part.center[i], b = part.center[i + 1];
          const x = a[0] + (b[0] - a[0]) * f, y = a[1] + (b[1] - a[1]) * f;
          const smp = surf.sample(x, y);
          expect(smp.paved).toBe(true);
          expect(smp.mu).toBe(1.0);
          if (!smp.onTrack && Math.abs(plain.sample(x, y).mu - 1.0) > 1e-9) differs++;
          if (prev !== null) {
            const dz = smp.z - prev;
            expect(Math.abs(dz)).toBeLessThan(0.06);                       // <= 24 % grade at 0.25 m steps
            if (prevDz !== null) expect(Math.abs(dz - prevDz)).toBeLessThan(0.02); // no steps
            prevDz = dz;
          }
          prev = smp.z;
          checked++;
        }
      }
    }
    expect(checked).toBeGreaterThan(1000);
    // without the pit lane those same points would mostly be dirt
    expect(differs).toBeGreaterThan(checked * 0.5);
  });

  test('walking out across both pit-lane edges is continuous', () => {
    const surf = createTrackSurface(track, hf, { pitLane: pit });
    for (const part of pit.parts) {
      for (let i = 10; i < part.n - 10; i += 40) {
        const c = part.center[i], a = part.center[i - 1], b = part.center[i + 1];
        const tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty);
        const nx = -ty / l, ny = tx / l;
        for (const side of [1, -1]) {
          const z: number[] = [];
          for (let d = 0; d <= 12; d += 0.1) z.push(surf.sample(c[0] + side * d * nx, c[1] + side * d * ny).z);
          // no step: no single 0.1 m increment stands out from both neighbours by 2 cm or more (slope changes at
          // the edge, where the flat lane meets the blended shoulder, are allowed)
          for (let k = 1; k < z.length - 2; k++) {
            const d0 = Math.abs(z[k] - z[k - 1]), d1 = Math.abs(z[k + 1] - z[k]), d2 = Math.abs(z[k + 2] - z[k + 1]);
            expect(d1 - Math.max(d0, d2)).toBeLessThan(0.02);
          }
        }
      }
    }
  });

  test('paved runoff zones (same code path): paved, mu 1.0, continuous heights', () => {
    expect(zones && zones.parts.length).toBeGreaterThan(0);
    const both = { spacing_m: 1, fractions: pit.fractions, parts: [...pit.parts, ...zones!.parts] };
    const surf = createTrackSurface(track, hf, { pitLane: both });
    for (const part of zones!.parts) {
      let prev: number | null = null, prevDz: number | null = null;
      for (let i = 5; i < part.n - 6; i++) {
        const c = part.center[i];
        const smp = surf.sample(c[0], c[1]);
        expect(smp.paved).toBe(true);
        expect(smp.mu).toBe(1.0);
        if (prev !== null) {
          const dz = smp.z - prev;
          // 1 m steps; the zone takes the track's edge heights (lidar profile, cm-level texture), so allow 5 cm
          if (prevDz !== null) expect(Math.abs(dz - prevDz)).toBeLessThan(0.05);
          prevDz = dz;
        }
        prev = smp.z;
      }
    }
  });
});
