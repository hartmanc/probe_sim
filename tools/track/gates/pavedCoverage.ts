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

export interface PavedCoverageOptions { parts: string[]; step?: number; wall_clear?: number; edge_tol?: number;
  /** Buttonwillow round 14 review: also the pit lane's drawn strip (scenery pit_lane.parts) inside this ENU box
   *  [x0, y0, x1, y1], so a zone part whose centre takes lane samples fails the gate */
  lane_box?: [number, number, number, number] }
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
  const zparts = (sc.paved_zones?.parts ?? []).filter((p: any) => pats.some((r) => r.test(p.turn ?? '')));
  const lb = o.lane_box;
  const lparts = lb ? (sc.pit_lane?.parts ?? []).map((p: any) => ({ ...p, turn: 'pit lane' })) : [];
  const parts = [...zparts, ...lparts];
  const rep: PavedCoverageReport = { parts: parts.length, samples: 0, holes: [], step, wallClear, edgeTol, onEdge: 0 };
  if (!parts.length) return rep;
  const { surf } = plainSurface(track, hf, sc);
  const polys = parts.map((p: any) => ({ name: p.turn as string, P: [...p.left, ...p.right.slice().reverse()].map((q: number[]) => [q[0], q[1]] as V2) }));
  const box = (P: V2[]) => P.reduce((b, [x, y]) => [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)], [Infinity, Infinity, -Infinity, -Infinity]);
  const walls: number[][][] = (sc.barriers ?? []).map((b: any) => b.pts);
  // the barrier segments in a 10 m grid (the same test as before, only the segments near a sample are tried)
  const G = 10, segs = new Map<string, [number[], number[]][]>();
  for (const W of walls) for (let k = 1; k < W.length; k++) {
    const a = W[k - 1], b = W[k];
    for (let gx = Math.floor((Math.min(a[0], b[0]) - wallClear) / G); gx <= Math.floor((Math.max(a[0], b[0]) + wallClear) / G); gx++)
      for (let gy = Math.floor((Math.min(a[1], b[1]) - wallClear) / G); gy <= Math.floor((Math.max(a[1], b[1]) + wallClear) / G); gy++) {
        const key = `${gx},${gy}`; if (!segs.has(key)) segs.set(key, []); segs.get(key)!.push([a, b]);
      }
  }
  const nearWall = (x: number, y: number) => (segs.get(`${Math.floor(x / G)},${Math.floor(y / G)}`) ?? []).some(([a, b]) => segDist(x, y, a, b) < wallClear);
  // the drawn edges of every named part in the same grid (the edge tolerance test, as before, on the nearby edges only)
  const esegs = new Map<string, [number[], number[]][]>();
  for (const { P } of polys) for (let k = 0; k < P.length; k++) {
    const a = P[k === 0 ? P.length - 1 : k - 1], b = P[k];
    for (let gx = Math.floor((Math.min(a[0], b[0]) - edgeTol) / G); gx <= Math.floor((Math.max(a[0], b[0]) + edgeTol) / G); gx++)
      for (let gy = Math.floor((Math.min(a[1], b[1]) - edgeTol) / G); gy <= Math.floor((Math.max(a[1], b[1]) + edgeTol) / G); gy++) {
        const key = `${gx},${gy}`; if (!esegs.has(key)) esegs.set(key, []); esegs.get(key)!.push([a, b]);
      }
  }
  const seen = new Set<string>();
  for (const { name, P } of polys) {
    let [x0, y0, x1, y1] = box(P);
    if (lb && name === 'pit lane') { x0 = Math.max(x0, lb[0]); y0 = Math.max(y0, lb[1]); x1 = Math.min(x1, lb[2]); y1 = Math.min(y1, lb[3]); }
    for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) {
      for (let y = Math.ceil(y0 / step) * step; y <= y1; y += step) {
        const key = `${Math.round(x / step)},${Math.round(y / step)}`;
        if (seen.has(key) || !inPoly(x, y, P)) continue;
        seen.add(key);
        if (nearWall(x, y)) continue;
        if ((esegs.get(`${Math.floor(x / G)},${Math.floor(y / G)}`) ?? []).some(([a, b]) => segDist(x, y, a, b) < edgeTol)) { rep.onEdge++; continue; }
        rep.samples++;
        if (!surf.sample(x, y).paved) rep.holes.push({ x: Math.round(x * 100) / 100, y: Math.round(y * 100) / 100, part: name });
      }
    }
  }
  return rep;
}
