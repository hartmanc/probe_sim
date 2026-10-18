// Off-pavement surface model (NOTES-surface.md): mu blend across the edge, per-wheel paved flag, dirt drag, and
// on-pavement behaviour bit-identical to the recorded pre-change drive.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';
import { createTrackSurface, loadHeightfield, Vehicle, OFF_PAVEMENT_MU, SURFACE_GRIP_BLEND_M } from '../index';
import type { PitLaneJson, Surface, SurfaceSample, TrackJson } from '../index';
import { DT, input, probeSpec } from './helpers';
import { onPavementDrive } from './onpave_drive';

const dir = fileURLToPath(new URL('../../../public/tracks/laguna_seca/', import.meta.url));
const track = JSON.parse(readFileSync(dir + 'track.json', 'utf8')) as TrackJson;
const hf = loadHeightfield(Uint8Array.from(readFileSync(dir + 'heightfield.bin')).buffer);
const scenery = JSON.parse(readFileSync(dir + 'scenery.json', 'utf8')) as { pit_lane: PitLaneJson; paved_zones?: PitLaneJson };
const paved: PitLaneJson = { ...scenery.pit_lane, parts: [...scenery.pit_lane.parts, ...(scenery.paved_zones?.parts ?? [])] };

describe('surface: mu across the paved edge', () => {
  test('full grip on pavement, smooth blend over the first metre, dry-dirt mu beyond', () => {
    const surf = createTrackSurface(track, hf);
    let profiles = 0;
    for (let i = 20; i < track.n; i += 97) {
      const c = track.center[i];
      for (const e of [track.left[i], track.right[i]]) {
        const half = Math.hypot(e[0] - c[0], e[1] - c[1]);
        const ux = (e[0] - c[0]) / half, uy = (e[1] - c[1]) / half;
        const at = (d: number): SurfaceSample => ({ ...surf.sample(c[0] + ux * d, c[1] + uy * d) });
        // well inside: pavement
        const inside = at(half - 0.5);
        expect(inside.paved).toBe(true);
        expect(inside.mu).toBe(1.0);
        expect(inside.dirt).toBe(0);
        // profile from 0.3 m inside the edge to 3 m out, 2 cm steps; locate the edge as the first non-paved sample
        let prevMu = 1, edge = NaN;
        for (let d = half - 0.3; d <= half + 3; d += 0.02) {
          const s = at(d);
          expect(Math.abs(s.mu - prevMu)).toBeLessThan(0.012);     // no step anywhere
          expect(s.mu).toBeLessThanOrEqual(prevMu + 1e-12);         // monotone going out
          if (!s.paved && Number.isNaN(edge)) edge = d;
          if (!Number.isNaN(edge)) {
            const out = d - edge;
            if (out >= SURFACE_GRIP_BLEND_M + 0.05) { expect(s.mu).toBeCloseTo(OFF_PAVEMENT_MU, 9); expect(s.dirt).toBe(1); }
            if (Math.abs(out - 0.5) < 0.011) expect(s.mu).toBeGreaterThan(0.8); // half way: about the mean
          }
          prevMu = s.mu;
        }
        expect(Number.isNaN(edge)).toBe(false);
        profiles++;
      }
    }
    expect(profiles).toBeGreaterThan(20);
  });

  test('pit lane and paved runoff keep full pavement grip', () => {
    const surf = createTrackSurface(track, hf, { pitLane: paved });
    for (const part of paved.parts) {
      for (let i = 2; i < part.n - 3; i += 5) {
        const s = surf.sample(part.center[i][0], part.center[i][1]);
        expect(s.paved).toBe(true);
        expect(s.mu).toBe(1.0);
        expect(s.dirt).toBe(0);
      }
    }
  });

  test('roughness is deterministic in position and small', () => {
    const a = createTrackSurface(track, hf), b = createTrackSurface(track, hf), flat = createTrackSurface(track, hf, { roughness: 0 });
    let maxDz = 0;
    for (let k = 0; k < 200; k++) {
      const x = -300 + 3.1 * k, y = 400 - 1.7 * k;
      const za = a.sample(x, y).z;
      expect(b.sample(x, y).z).toBe(za);
      const s = flat.sample(x, y);
      if (s.dirt === 1) maxDz = Math.max(maxDz, Math.abs(za - s.z));
    }
    expect(maxDz).toBeGreaterThan(0.002);
    expect(maxDz).toBeLessThanOrEqual(0.0121);
  });
});

/** Find a point with all ground within r metres off pavement (dirt = 1), outside the track near station i. */
function dirtSpot(surf: Surface, r: number): { x: number; y: number; heading: number } {
  for (let i = 0; i < track.n; i += 37) {
    const c = track.center[i], e = track.left[i], n = track.center[(i + 1) % track.n];
    const half = Math.hypot(e[0] - c[0], e[1] - c[1]);
    for (const d of [half + 12, half + 20]) {
      const x = c[0] + ((e[0] - c[0]) / half) * d, y = c[1] + ((e[1] - c[1]) / half) * d;
      let ok = true;
      for (let a = 0; a < 16 && ok; a++) for (const rr of [0, r / 2, r]) {
        const s = surf.sample(x + rr * Math.cos(a * 0.39), y + rr * Math.sin(a * 0.39));
        if (s.dirt !== 1) ok = false;
      }
      if (ok) return { x, y, heading: Math.atan2(n[1] - c[1], n[0] - c[0]) };
    }
  }
  throw new Error('no dirt spot');
}

describe('WheelState.paved / mu', () => {
  const surf = createTrackSurface(track, hf, { pitLane: paved });
  const check = (x: number, y: number, heading: number, expectPaved: boolean) => {
    const car = new Vehicle(probeSpec());
    car.reset([x, y, surf.sample(x, y).z], heading, 0);
    for (let k = 0; k < 50; k++) car.step(input({ brake: 1 }), surf, DT);
    for (const w of car.state.wheels) {
      const s = surf.sample(w.pos[0], w.pos[1]);
      expect(w.paved).toBe(expectPaved);
      expect(w.paved).toBe(s.paved);
      if (expectPaved) expect(w.mu).toBe(1.0);
      else expect(w.mu).toBeCloseTo(OFF_PAVEMENT_MU, 9);
    }
  };
  const dirOf = (p: number[][], i: number) => Math.atan2(p[i + 1][1] - p[i][1], p[i + 1][0] - p[i][0]);

  test('on the track', () => {
    const i = 300;
    check(track.center[i][0], track.center[i][1], dirOf(track.center, i), true);
  });
  test('in the pit lane', () => {
    const part = scenery.pit_lane.parts[0], i = Math.floor(part.n / 2);
    check(part.center[i][0], part.center[i][1], dirOf(part.center, i), true);
  });
  test('on a paved runoff zone', () => {
    const z = scenery.paved_zones!.parts.reduce((a, b) => (b.n > a.n ? b : a));
    const i = Math.floor(z.n / 2);
    // the zone may be narrow: check only that each wheel agrees with the surface, and the centre wheel point is paved
    const car = new Vehicle(probeSpec());
    const [x, y] = z.center[i];
    car.reset([x, y, surf.sample(x, y).z], dirOf(z.center, i), 0);
    for (let k = 0; k < 50; k++) car.step(input({ brake: 1 }), surf, DT);
    expect(surf.sample(x, y).paved).toBe(true);
    for (const w of car.state.wheels) {
      const s = surf.sample(w.pos[0], w.pos[1]);
      expect(w.paved).toBe(s.paved);
      if (s.dirt === 0) expect(w.mu).toBe(1.0);
    }
  });
  test('on dirt', () => {
    const p = dirtSpot(surf, 3);
    check(p.x, p.y, p.heading, false);
  });
});

/** Flat ground of one kind: pavement (no dirt field, as the dev surfaces) or full dirt. */
function flat(dirt: boolean): Surface {
  const out: SurfaceSample = dirt
    ? { z: 0, nx: 0, ny: 0, nz: 1, onTrack: false, paved: false, mu: OFF_PAVEMENT_MU, dirt: 1, muPaved: 1 }
    : { z: 0, nx: 0, ny: 0, nz: 1, onTrack: true, paved: true, mu: 1, dirt: 0, muPaved: 1 };
  return { sample: () => out };
}

describe('dirt drag and grip', () => {
  const coast = (surf: Surface) => {
    const car = new Vehicle(probeSpec(), { autoShift: false });
    car.reset([0, 0, 0], 0, 25);
    car.setGear(0);
    for (let k = 0; k < 5000; k++) car.step(input(), surf, DT);
    return car.state.speed;
  };
  test('coasting 5 s from 90 km/h on dirt loses a plausible extra 2-5 m/s (0.04-0.1 g more drag)', () => {
    const vPave = coast(flat(false)), vDirt = coast(flat(true));
    const extra = vPave - vDirt;
    console.log(`coast 5 s from 25 m/s: pavement ${vPave.toFixed(2)}, dirt ${vDirt.toFixed(2)} m/s (extra loss ${extra.toFixed(2)})`);
    expect(extra).toBeGreaterThan(2);
    expect(extra).toBeLessThan(5);
  });

  test('car.json surfaces.offPavementMu overrides the surface mu, blended by the dirt weight', () => {
    const half: SurfaceSample = { z: 0, nx: 0, ny: 0, nz: 1, onTrack: false, paved: false, mu: 0.86, dirt: 0.5, muPaved: 1 };
    const car = new Vehicle(probeSpec((j) => { j.surfaces = { offPavementMu: 0.6 }; }));
    car.reset([0, 0, 0], 0, 10);
    car.step(input(), { sample: () => half }, DT);
    for (const w of car.state.wheels) expect(w.mu).toBeCloseTo(0.8, 12);
  });

  test('steady skidpad on dirt: lower but not drastically lower lateral grip', () => {
    // as vehicle.test §4: fixed road-wheel angle, slow speed ramp, 1 s moving average of v·r
    const peak = (surf: Surface) => {
      const spec = probeSpec((j) => { j.steering.shapingSpeed = 1e6; j.steering.rate = 100; });
      const car = new Vehicle(spec, { autoShift: true });
      car.reset([0, 0, 0], 0, 8);
      const inp = input({ steer: 0.35 });
      let best = 0, acc = 0, integ = 0;
      const N = 1000, buf = new Float64Array(N);
      for (let i = 0; i < 70000; i++) {
        const e = 8 + 0.2 * i * DT - car.state.speed;
        integ += e * DT;
        inp.throttle = Math.min(1, Math.max(0, 0.3 * e + 0.05 * integ));
        car.step(inp, surf, DT);
        const a = car.state.speed * car.state.angVel[2];
        acc += a - buf[i % N]; buf[i % N] = a;
        if (i >= N) best = Math.max(best, acc / N);
      }
      return best / 9.81;
    };
    const gP = peak(flat(false)), gD = peak(flat(true));
    console.log(`skidpad peak: pavement ${gP.toFixed(3)} g, dirt ${gD.toFixed(3)} g (ratio ${(gD / gP).toFixed(2)})`);
    expect(gD / gP).toBeGreaterThan(0.6);
    expect(gD / gP).toBeLessThan(0.85);
  }, 30000);
});

describe('on-pavement behaviour unchanged', () => {
  test('9 s Laguna drive is bit-identical to the fixture recorded before the surface model', () => {
    const fx = JSON.parse(readFileSync(fileURLToPath(new URL('./fixtures/onpave_drive.json', import.meta.url)), 'utf8')) as { trace: number[]; allPaved: boolean };
    const r = onPavementDrive();
    expect(r.allPaved).toBe(true);
    expect(r.trace.length).toBe(fx.trace.length);
    for (let k = 0; k < r.trace.length; k++) expect(r.trace[k]).toBe(fx.trace[k]);
  });
});
