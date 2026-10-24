// A synthetic package for the terrain-override tests (Sonoma round 14A): an oval (two 300 m straights, R 60 ends, 1 m
// stations, half-width 5 m, a 3 % cross-slope falling to the right), a 2 m heightfield whose ground beyond the edges
// is given by a function of (x, y), and an override region over the middle of the bottom straight.
import type { TrackJson, Vec3 } from '../index';

export const HALF = 5;
export const XSLOPE = 0.03;   // the course falls 3 % from its left edge to its right edge (bottom straight: left = +y)
export const FR = [-1, -0.6667, -0.3333, 0, 0.3333, 0.6667, 1];

export function ovalTrack(): TrackJson {
  const Ls = 300, R = 60, n = Math.round(2 * Ls + 2 * Math.PI * R);
  const center: Vec3[] = [], left: Vec3[] = [], right: Vec3[] = [], z: number[][] = [];
  for (let k = 0; k < n; k++) {
    let s = k, x: number, y: number, h: number;
    if (s < Ls) { x = s - Ls / 2; y = 0; h = 0; }
    else if ((s -= Ls) < Math.PI * R) { const a = s / R; x = Ls / 2 + R * Math.sin(a); y = R - R * Math.cos(a); h = a; }
    else if ((s -= Math.PI * R) < Ls) { x = Ls / 2 - s; y = 2 * R; h = Math.PI; }
    else { s -= Ls; const a = s / R; x = -Ls / 2 - R * Math.sin(a); y = R + R * Math.cos(a); h = Math.PI + a; }
    const nx = -Math.sin(h), ny = Math.cos(h);
    center.push([x, y, 0]); left.push([x + nx * HALF, y + ny * HALF, XSLOPE * HALF]); right.push([x - nx * HALF, y - ny * HALF, -XSLOPE * HALF]);
    z.push(FR.map((f) => -f * HALF * XSLOPE));
  }
  return {
    name: 'oval', origin: { lat: 0, lon: 0 }, z0_navd88: 0, direction: 'ccw', spacing_m: 1, n, length_m: n,
    center, left, right, profile: { fractions: FR, z }, start_finish: { index: 0 }, corners: [],
    heightfield: { file: 'heightfield.bin', x0: -250, y0: -100, dx: 2, nx: 251, ny: 161 },
  } as unknown as TrackJson;
}

/** The heightfield from a ground function (x, y) -> z. */
export function heightfieldOf(t: TrackJson, ground: (x: number, y: number) => number): Float32Array {
  const h = t.heightfield, out = new Float32Array(h.nx * h.ny);
  for (let i = 0; i < h.ny; i++) for (let j = 0; j < h.nx; j++) out[i * h.nx + j] = ground(h.x0 + j * h.dx, h.y0 + i * h.dx);
  return out;
}

/** The course's own plane continued beyond the bottom straight's edges (C1 with it): z = XSLOPE * y. */
export const continuation = (_x: number, y: number) => XSLOPE * y;

/** Region over the bottom straight, x -60..60, y -40..40 (the course runs through it along y = 0). */
export const REGION = { regions: [{ name: 'test', ramp: 1.5, poly: [[-60, -40], [60, -40], [60, 40], [-60, 40]] }] };

/** A paved strip (pit-lane layout) 8-14 m right of the bottom straight, x -30..30, on the given heights. */
export function stripPart(zf: (x: number, y: number) => number): { n: number; center: Vec3[]; left: Vec3[]; right: Vec3[]; profile_z: number[][] } {
  const center: Vec3[] = [], left: Vec3[] = [], right: Vec3[] = [], profile_z: number[][] = [];
  for (let x = -30; x <= 30; x++) {
    center.push([x, -11, zf(x, -11)]); left.push([x, -8, zf(x, -8)]); right.push([x, -14, zf(x, -14)]);
    profile_z.push(FR.map((f) => zf(x, -11 - f * 3)));
  }
  return { n: center.length, center, left, right, profile_z };
}
