// Synthetic test fixtures: a 2 km oval with a gentle hill (valid track.json +
// heightfield), and simple flat / split-mu surfaces.

import { cos as dcos, exp as dexp, hypot as dhypot, sin as dsin } from './dmath';   // bit-identical to V8 on every engine (docs/determinism.md)
import type { TrackJson } from './track';
import type { SceneryCollisionJson } from './collision';
import type { Surface, SurfaceSample, Vec3 } from './types';

export interface DevTrackOptions {
  length?: number;      // m, default 2000
  radius?: number;      // turn radius, m, default 150
  halfWidth?: number;   // m, default 6
  hillHeight?: number;  // m, default 5
  hillSigma?: number;   // m, default 60
  spacing?: number;     // m, default 1
}

/** Analytic ground height for the dev track (also used by tests). */
export function devGround(x: number, y: number, o: Required<DevTrackOptions>): number {
  const dx = x, dy = y - o.radius; // hill centred on the back straight
  return o.hillHeight * dexp(-(dx * dx + dy * dy) / (2 * o.hillSigma * o.hillSigma));
}

export function devTrackOptions(opts: DevTrackOptions = {}): Required<DevTrackOptions> {
  return {
    length: opts.length ?? 2000,
    radius: opts.radius ?? 150,
    halfWidth: opts.halfWidth ?? 6,
    hillHeight: opts.hillHeight ?? 5,
    hillSigma: opts.hillSigma ?? 60,
    spacing: opts.spacing ?? 1,
  };
}

/**
 * Counter-clockwise oval. Station 0 is mid front straight at (0, −R) heading
 * +x (east); the inside of the oval is on the driver's left.
 */
export function createDevTrack(opts: DevTrackOptions = {}): { track: TrackJson; heightfield: Float32Array; options: Required<DevTrackOptions> } {
  const o = devTrackOptions(opts);
  const R = o.radius;
  const Ls = (o.length - 2 * Math.PI * R) / 2;
  if (Ls <= 0) throw new Error('devtrack: radius too large for length');
  const n = Math.round(o.length / o.spacing);
  const L = n * o.spacing;
  const fractions = [-1, -2 / 3, -1 / 3, 0, 1 / 3, 2 / 3, 1];

  const pointAt = (sIn: number): { x: number; y: number; h: number } => {
    let s = (sIn + Ls / 2) % L; if (s < 0) s += L;
    if (s < Ls) return { x: -Ls / 2 + s, y: -R, h: 0 };
    s -= Ls;
    if (s < Math.PI * R) { const th = s / R; return { x: Ls / 2 + R * dsin(th), y: -R * dcos(th), h: th }; }
    s -= Math.PI * R;
    if (s < Ls) return { x: Ls / 2 - s, y: R, h: Math.PI };
    s -= Ls;
    const th = s / R;
    return { x: -Ls / 2 - R * dsin(th), y: R * dcos(th), h: Math.PI + th };
  };

  const center: Vec3[] = [], left: Vec3[] = [], right: Vec3[] = [], pz: number[][] = [];
  for (let i = 0; i < n; i++) {
    const p = pointAt(i * o.spacing);
    const nx = -dsin(p.h), ny = dcos(p.h); // left normal
    const zc = devGround(p.x, p.y, o);
    center.push([p.x, p.y, zc]);
    const lx = p.x + o.halfWidth * nx, ly = p.y + o.halfWidth * ny;
    const rx = p.x - o.halfWidth * nx, ry = p.y - o.halfWidth * ny;
    left.push([lx, ly, devGround(lx, ly, o)]);
    right.push([rx, ry, devGround(rx, ry, o)]);
    pz.push(fractions.map((f) => {
      const d = -f * o.halfWidth; // +left
      return devGround(p.x + d * nx, p.y + d * ny, o);
    }));
  }

  const margin = 150, dx = 2;
  const x0 = -Ls / 2 - R - margin, y0 = -R - margin;
  const nxh = Math.ceil((Ls + 2 * R + 2 * margin) / dx) + 1;
  const nyh = Math.ceil((2 * R + 2 * margin) / dx) + 1;
  const heightfield = new Float32Array(nxh * nyh);
  for (let i = 0; i < nyh; i++) for (let j = 0; j < nxh; j++) heightfield[i * nxh + j] = devGround(x0 + j * dx, y0 + i * dx, o);

  const track: TrackJson = {
    name: 'Dev oval',
    origin: { lat: 0, lon: 0 },
    z0_navd88: 0,
    direction: 'ccw',
    spacing_m: o.spacing,
    n,
    length_m: L,
    center, left, right,
    profile: { fractions, z: pz },
    start_finish: { index: 0 },
    corners: [{ name: 'Turn 1', s: Ls / 2 + Math.PI * R / 2 }, { name: 'Turn 2', s: Ls * 1.5 + Math.PI * R * 1.5 }],
    heightfield: { file: 'heightfield.bin', x0, y0, dx, nx: nxh, ny: nyh },
    ortho: { file: 'ortho.jpg', x0, y0, x1: x0 + (nxh - 1) * dx, y1: y0 + (nyh - 1) * dx, width_px: 1, height_px: 1 },
    sources: 'synthetic',
  };
  return { track, heightfield, options: o };
}

export interface FlatSurfaceOptions {
  z?: number;
  mu?: number;
  /** Optional per-point friction, overrides mu. */
  muAt?: (x: number, y: number) => number;
}

/** Infinite flat ground. */
export function createFlatSurface(opts: FlatSurfaceOptions = {}): Surface {
  const out: SurfaceSample = { z: opts.z ?? 0, nx: 0, ny: 0, nz: 1, onTrack: true, mu: opts.mu ?? 1 };
  const muAt = opts.muAt;
  return {
    sample(x: number, y: number): SurfaceSample {
      if (muAt) out.mu = muAt(x, y);
      return out;
    },
  };
}

// ---------------------------------------------------------------------------
// Scenery for collision tests (CONTRACTS §2b subset) + a far heightfield.


export interface DevScenery {
  scenery: SceneryCollisionJson;
  far: { heightfield: Float32Array; x0: number; y0: number; dx: number; nx: number; ny: number };
  /** y of the Armco line along the outside of the front straight, and of the concrete wall behind the back straight. */
  armcoY: number;
  concreteY: number;
  /** Far terrain height (rises 1 % per metre beyond 600 m from the centre). */
  farGround(x: number, y: number): number;
  tree: { x: number; y: number };
}

export function createDevScenery(o: Required<DevTrackOptions> = devTrackOptions()): DevScenery {
  const R = o.radius;
  const Ls = (o.length - 2 * Math.PI * R) / 2;
  const farGround = (x: number, y: number) => devGround(x, y, o) + 0.01 * Math.max(0, dhypot(x, y) - 600);
  const run = (y: number, x0: number, x1: number) => {
    const pts: number[][] = [];
    for (let x = x0; x <= x1 + 1e-9; x += 2) pts.push([x, y, devGround(x, y, o)]);
    return pts;
  };
  const armcoY = -R - o.halfWidth - 4;
  const concreteY = R + o.halfWidth + 4;
  const tyreX = Ls / 2 + R + o.halfWidth + 4;
  const tyres: number[][] = [];
  for (let y = -30; y <= 30; y += 2) tyres.push([tyreX, y, devGround(tyreX, y, o)]);
  const tree = { x: 120, y: -40 };
  const scenery: SceneryCollisionJson = {
    far: { heightfield: { x0: -2500, y0: -2500, dx: 10, nx: 501, ny: 501 } },
    barriers: [
      { kind: 'armco', h: 0.75, fence: 0, pts: run(armcoY, -200, 200) },
      { kind: 'concrete', h: 1.0, fence: 2.5, pts: run(concreteY, -200, 200) },
      { kind: 'tyres', h: 0.9, fence: 0, pts: tyres },
    ],
    buildings: [{ z: 0, h: 6, footprint: [[-120, -40], [-100, -40], [-100, -20], [-120, -20]] }],
    trees: { stride: 5, fields: ['x', 'y', 'z', 'height', 'crown_radius'], scale: 0.1, data: [tree.x * 10, tree.y * 10, 0, 120, 40] },
  };
  const nx = 501, ny = 501;
  const hf = new Float32Array(nx * ny);
  for (let i = 0; i < ny; i++) for (let j = 0; j < nx; j++) hf[i * nx + j] = farGround(-2500 + j * 10, -2500 + i * 10);
  return { scenery, far: { heightfield: hf, x0: -2500, y0: -2500, dx: 10, nx, ny }, armcoY, concreteY, farGround, tree };
}
