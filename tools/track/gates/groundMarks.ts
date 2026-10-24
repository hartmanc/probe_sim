// Ground marks on the driven surface (Sonoma round 14B; Astra's judge_r14a regression: the white edge line along the
// drag-strip continuation toward T7 disappeared once round 14A draped the paved zones on the override surface, because
// the closed-road paint lines kept the heights of the surface they were built on: a closed road's painted edge took its
// zone's CENTRE height (the cross-slope ignored, 0.02 m up), a declared line the raw heightfield, so after the drape the
// line lay under the raised zone or floated over the lowered one; measured on the round-14A package: -0.45 .. +0.26 m,
// region or not).
//
//  drapeMarks: every stored height of a ground mark takes the package's own driven surface (the plain surface of the
//    physics, src/physics/track.ts, as terrainGates.ts measures it: the course, the paved parts as draped, the override
//    surface in a region, the heightfield beyond): paint_lines vertices at surface + `lift`; cone_lines,
//    pit_exit_cones, kerb_lines points and ground_signs centres on the surface. The app already draws the edge lines,
//    ground signs, kerb lines and cones on its ground function; the paint lines it draws at their stored heights.
//  groundMarksGate ("ground marks on surface", REQUIRED in stage 3, region or not): every vertex of a paint line (its
//    stored height), of an edge line and of a ground sign (as the app builds them on the ground: edge lines
//    EDGE_LINE_LIFT, signs GROUND_SIGN_LIFT above it) lies within `tol` (0.01 m) above the driven surface and never
//    below it.
import { plainSurface } from './terrainGates';
import type { TrackJson } from '../../../src/physics/index';

export const PAINT_LIFT = 0.008;        // a paint line's stored height above the driven surface (the edge lines' lift)
export const EDGE_LINE_LIFT = 0.008;    // src/app/scenery.ts buildEdgeLines (dz)
export const GROUND_SIGN_LIFT = 0.008;  // src/app/scenery.ts buildGroundSigns (round 14B: was 0.02)
export const MARKS_TOL = 0.01;

type V3 = [number, number, number];
const r3 = (v: number) => Math.round(v * 1000) / 1000;

export interface DrapeReport { paint: number; cones: number; kerbLines: number; signs: number; maxChange: number; worst: string }

export function drapeMarks(track: TrackJson, hf: Float32Array, sc: any, lift = PAINT_LIFT): DrapeReport {
  const { surf } = plainSurface(track, hf, sc);
  const z = (x: number, y: number) => surf.sample(x, y).z;
  const rep: DrapeReport = { paint: 0, cones: 0, kerbLines: 0, signs: 0, maxChange: 0, worst: '' };
  const put = (P: V3, dz: number, what: string) => {
    const zn = r3(z(P[0], P[1]) + dz), d = Math.abs(zn - P[2]);
    if (d > rep.maxChange) { rep.maxChange = d; rep.worst = what; }
    P[2] = zn;
  };
  for (const l of sc.paint_lines ?? []) for (const P of l.pts as V3[]) { put(P, lift, `paint line ${(l.src ?? '').slice(0, 60)}`); rep.paint++; }
  for (const c of [...(sc.cone_lines ?? []), ...(sc.pit_exit_cones ? [sc.pit_exit_cones] : [])]) for (const P of c.pts as V3[]) { put(P, 0, 'cone'); rep.cones++; }
  for (const k of sc.kerb_lines ?? []) for (const P of k.pts as V3[]) { put(P, 0, 'kerb line'); rep.kerbLines++; }
  for (const g of sc.ground_signs ?? []) {
    const zn = r3(z(g.x, g.y)), d = Math.abs(zn - g.z);
    if (d > rep.maxChange) { rep.maxChange = d; rep.worst = `ground sign ${g.text}`; }
    g.z = zn; rep.signs++;
  }
  rep.maxChange = r3(rep.maxChange);
  return rep;
}

export interface MarkMiss { what: string; x: number; y: number; d: number }
export interface MarksReport { vertices: { paint: number; edge: number; sign: number }; minD: number; maxD: number; bad: MarkMiss[] }

/** The edge-line vertices as src/app/scenery.ts edgeFrame / buildEdgeLines place them (both borders of the 0.12 m line,
 *  `inset` inside the edge, every station of each run), on the driven surface. */
function edgeLineVertices(track: TrackJson, el: any, z: (x: number, y: number) => number): { x: number; y: number; zz: number; s: number; side: number }[] {
  const n = track.n, out: { x: number; y: number; zz: number; s: number; side: number }[] = [];
  const sp = track.spacing_m || 1;
  for (const r of el?.runs ?? []) {
    const i0 = Math.round(r.s0 / sp), i1 = Math.round(r.s1 / sp);
    for (let i = i0; i <= i1; i++) {
      const ii = ((i % n) + n) % n;
      const a = track.center[(ii - 1 + n) % n], b = track.center[(ii + 1) % n];
      const tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty) || 1, nx = -ty / l, ny = tx / l;
      const e = r.side > 0 ? track.left[ii] : track.right[ii];
      for (const out_ of [-el.inset - el.width, -el.inset]) {
        const x = e[0] + nx * r.side * out_, y = e[1] + ny * r.side * out_;
        out.push({ x, y, zz: z(x, y) + EDGE_LINE_LIFT, s: ii * sp, side: r.side });
      }
    }
  }
  return out;
}

export function groundMarksGate(track: TrackJson, hf: Float32Array, sc: any, tol = MARKS_TOL): MarksReport {
  const { surf } = plainSurface(track, hf, sc);
  const z = (x: number, y: number) => surf.sample(x, y).z;
  const rep: MarksReport = { vertices: { paint: 0, edge: 0, sign: 0 }, minD: Infinity, maxD: -Infinity, bad: [] };
  const check = (what: string, x: number, y: number, zz: number) => {
    const d = zz - z(x, y);
    rep.minD = Math.min(rep.minD, d); rep.maxD = Math.max(rep.maxD, d);
    if (d < -1e-6 || d > tol + 1e-6) rep.bad.push({ what, x: +x.toFixed(1), y: +y.toFixed(1), d: +d.toFixed(3) });
  };
  for (const l of sc.paint_lines ?? []) for (const [x, y, zz] of l.pts as V3[]) { check(`paint line ${(l.src ?? '').slice(0, 50)}`, x, y, zz); rep.vertices.paint++; }
  for (const v of edgeLineVertices(track, sc.edge_lines, z)) { check(`edge line ${v.side > 0 ? 'left' : 'right'} s ${v.s.toFixed(0)}`, v.x, v.y, v.zz); rep.vertices.edge++; }
  for (const gs of sc.ground_signs ?? []) {
    // the app's grid (src/app/scenery.ts buildGroundSigns): 16 x 4 cells over length x height, draped on the ground
    const NX = 16, NY = 4, ux = Math.cos(gs.heading), uy = Math.sin(gs.heading), vx = -uy, vy = ux;
    for (let j = 0; j <= NY; j++) for (let i = 0; i <= NX; i++) {
      const a = (i / NX - 0.5) * gs.length, b = (j / NY - 0.5) * gs.height;
      const x = gs.x + ux * a + vx * b, y = gs.y + uy * a + vy * b;
      check(`ground sign ${gs.text}`, x, y, z(x, y) + GROUND_SIGN_LIFT); rep.vertices.sign++;
    }
  }
  if (!Number.isFinite(rep.minD)) { rep.minD = 0; rep.maxD = 0; }
  rep.minD = r3(rep.minD); rep.maxD = r3(rep.maxD);
  return rep;
}
