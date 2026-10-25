// Paved coverage (Buttonwillow round 13, GPT 6 Astra's review of the paddock bands): the drawn paving and the physics
// surface must agree. The app draws every paved part as its strip (left and right edges); the physics gives a point to
// the part whose centre line is nearest (the pit lane and the paved zones are one list, src/physics/track.ts), so two
// overlapping parts, one of which ends inside the other's drawing, leave unpaved seams the drawing does not show.
//
//  pavedCoverage: every sample on a `step` grid inside the drawn strip of each named part (scenery.json
//    paved_zones.parts, `turn` matching one of the patterns), more than `wallClear` m from any barrier line (the wall's
//    own footprint) and more than `edge_tol` m from the drawn edge of every named part (the app's strip edges are chords
//    between offset points, 0.01 m rounded; the physics interpolates the half-width along each centre segment, so the two
//    may differ by centimetres on an edge, and two bands that meet exactly on their bisector meet on an edge), must be
//    paved in the package's own driven surface (terrainGates.plainSurface). Config-gated (gates_config paved_coverage
//    {parts, step, wall_clear, edge_tol}); strict: one unpaved sample fails the stage.
import { plainSurface } from './terrainGates';
import type { TrackJson } from '../../../src/physics/index';

export interface PavedCoverageOptions { parts: string[]; step?: number; wall_clear?: number; edge_tol?: number }
export interface PavedCoverageReport { parts: number; samples: number; holes: { x: number; y: number; part: string }[]; step: number; wallClear: number; edgeTol: number; onEdge: number }

type V2 = [number, number];
function inPoly(x: number, y: number, P: V2[]): boolean {
  let c = false;
  for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
    const [xi, yi] = P[i], [xj, yj] = P[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}
function segDist(x: number, y: number, a: number[], b: number[]): number {
  const dx = b[0] - a[0], dy = b[1] - a[1], l2 = dx * dx + dy * dy;
  const t = l2 > 0 ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / l2)) : 0;
  return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy);
}

export function pavedCoverage(track: TrackJson, hf: Float32Array, sc: any, o: PavedCoverageOptions): PavedCoverageReport {
  const step = o.step ?? 0.25, wallClear = o.wall_clear ?? 0.4, edgeTol = o.edge_tol ?? 0.1;
  const pats = o.parts.map((p) => new RegExp(p));
  const parts = (sc.paved_zones?.parts ?? []).filter((p: any) => pats.some((r) => r.test(p.turn ?? '')));
  const rep: PavedCoverageReport = { parts: parts.length, samples: 0, holes: [], step, wallClear, edgeTol, onEdge: 0 };
  if (!parts.length) return rep;
  const { surf } = plainSurface(track, hf, sc);
  const polys = parts.map((p: any) => ({ name: p.turn as string, P: [...p.left, ...p.right.slice().reverse()].map((q: number[]) => [q[0], q[1]] as V2) }));
  const box = (P: V2[]) => P.reduce((b, [x, y]) => [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)], [Infinity, Infinity, -Infinity, -Infinity]);
  const walls: number[][][] = (sc.barriers ?? []).map((b: any) => b.pts);
  const nearWall = (x: number, y: number) => walls.some((W) => W.some((p, k) => k > 0 && segDist(x, y, W[k - 1], p) < wallClear));
  const seen = new Set<string>();
  for (const { name, P } of polys) {
    const [x0, y0, x1, y1] = box(P);
    for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) {
      for (let y = Math.ceil(y0 / step) * step; y <= y1; y += step) {
        const key = `${Math.round(x / step)},${Math.round(y / step)}`;
        if (seen.has(key) || !inPoly(x, y, P)) continue;
        seen.add(key);
        if (nearWall(x, y)) continue;
        if (polys.some((q: { P: V2[] }) => q.P.some((p, k) => segDist(x, y, q.P[k === 0 ? q.P.length - 1 : k - 1], p) < edgeTol))) { rep.onEdge++; continue; }
        rep.samples++;
        if (!surf.sample(x, y).paved) rep.holes.push({ x: Math.round(x * 100) / 100, y: Math.round(y * 100) / 100, part: name });
      }
    }
  }
  return rep;
}
