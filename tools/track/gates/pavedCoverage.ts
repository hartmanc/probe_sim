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
//
//  Buttonwillow round 14 (GPT 6 Astra's second review): three further checks, each with its own sample set and its own
//  edge exclusions, so the round-13 check above is exactly what it was:
//    lane: the pit lane's drawn strip (scenery pit_lane.parts) inside the box of every named part's drawn strip grown by
//      `lane.margin` m (derived from the parts, not a hand number): a zone part whose centre takes lane samples fails;
//      edges left out: the lane's and the named parts';
//    also: the drawn strips of the parts matching `also[].parts` inside the same box (the paddock aisle beside the lane);
//    outlines: the owner's own outlines (`outlines`: ENU polygons, closed inside the course): every sample in them off
//      the course is paved (the drawn strips are generated; his green is the intent); edges left out: the outlines'.
import { plainSurface } from './terrainGates';
import type { TrackJson } from '../../../src/physics/index';

export interface PavedCoverageOptions { parts: string[]; step?: number; wall_clear?: number; edge_tol?: number;
  lane?: { margin?: number }; also?: { parts: string[]; near_lane?: number }[]; outlines?: { name: string; poly: number[][] }[] }
export interface PavedCoverageReport {
  parts: number; samples: number; holes: { x: number; y: number; part: string }[]; step: number; wallClear: number; edgeTol: number; onEdge: number;
  lane?: { box: number[]; parts: number; samples: number; onEdge: number; holes: number };
  also?: { parts: number; samples: number; onEdge: number; holes: number };
  outlines?: { polys: number; samples: number; onEdge: number; holes: number };
}

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
const G = 10;   // the segment grid (world-aligned, 10 m cells): the same distance tests, only on the segments near a sample
function grid(segsIn: [number[], number[]][], pad: number): Map<string, [number[], number[]][]> {
  const m = new Map<string, [number[], number[]][]>();
  for (const [a, b] of segsIn)
    for (let gx = Math.floor((Math.min(a[0], b[0]) - pad) / G); gx <= Math.floor((Math.max(a[0], b[0]) + pad) / G); gx++)
      for (let gy = Math.floor((Math.min(a[1], b[1]) - pad) / G); gy <= Math.floor((Math.max(a[1], b[1]) + pad) / G); gy++) {
        const key = `${gx},${gy}`; if (!m.has(key)) m.set(key, []); m.get(key)!.push([a, b]);
      }
  return m;
}
const near = (m: Map<string, [number[], number[]][]>, x: number, y: number, r: number) =>
  (m.get(`${Math.floor(x / G)},${Math.floor(y / G)}`) ?? []).some(([a, b]) => segDist(x, y, a, b) < r);
const ring = (P: V2[]) => P.map((p, k) => [P[k === 0 ? P.length - 1 : k - 1], p] as [number[], number[]]);
const stripOf = (p: any) => [...p.left, ...p.right.slice().reverse()].map((q: number[]) => [q[0], q[1]] as V2);
const bounds = (P: V2[]) => P.reduce((b, [x, y]) => [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)], [Infinity, Infinity, -Infinity, -Infinity]);

/** one sampled check: every grid sample inside `polys` (clipped to `clip` when given), off the barriers' footprints and
 *  off the `edges` (the check's own exclusion set), and not on the course when `offCourse`, must be paved */
function check(surf: any, polys: { name: string; P: V2[]; near?: (x: number, y: number) => boolean }[], edges: Map<string, [number[], number[]][]>, walls: Map<string, [number[], number[]][]>,
  step: number, wallClear: number, edgeTol: number, clip: number[] | null, offCourse: boolean, holes: { x: number; y: number; part: string }[]) {
  let samples = 0, onEdge = 0, nh = 0;
  const seen = new Set<string>();
  for (const { name, P, near: keep } of polys) {
    let [x0, y0, x1, y1] = bounds(P);
    if (clip) { x0 = Math.max(x0, clip[0]); y0 = Math.max(y0, clip[1]); x1 = Math.min(x1, clip[2]); y1 = Math.min(y1, clip[3]); }
    for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) {
      for (let y = Math.ceil(y0 / step) * step; y <= y1; y += step) {
        const key = `${Math.round(x / step)},${Math.round(y / step)}`;
        if (seen.has(key) || !inPoly(x, y, P)) continue;
        seen.add(key);
        if (keep && !keep(x, y)) continue;
        if (near(walls, x, y, wallClear)) continue;
        if (near(edges, x, y, edgeTol)) { onEdge++; continue; }
        const r = surf.sample(x, y);
        if (offCourse && r.onTrack) continue;
        samples++;
        if (!r.paved) { nh++; holes.push({ x: Math.round(x * 100) / 100, y: Math.round(y * 100) / 100, part: name }); }
      }
    }
  }
  return { samples, onEdge, holes: nh };
}

export function pavedCoverage(track: TrackJson, hf: Float32Array, sc: any, o: PavedCoverageOptions): PavedCoverageReport {
  const step = o.step ?? 0.25, wallClear = o.wall_clear ?? 0.4, edgeTol = o.edge_tol ?? 0.1;
  const pats = o.parts.map((p) => new RegExp(p));
  // a part the app does not draw (draw: false, round 14: the lane bands, paving under the lane's own drawing) has no
  // drawn strip to check; its paving is checked as the lane's (lane) and the owner's outlines' (outlines)
  const parts = (sc.paved_zones?.parts ?? []).filter((p: any) => p.draw !== false && pats.some((r) => r.test(p.turn ?? '')));
  const rep: PavedCoverageReport = { parts: parts.length, samples: 0, holes: [], step, wallClear, edgeTol, onEdge: 0 };
  if (!parts.length) return rep;
  const { surf } = plainSurface(track, hf, sc);
  const walls = grid(((sc.barriers ?? []) as any[]).flatMap((b) => b.pts.slice(1).map((p: number[], k: number) => [b.pts[k], p] as [number[], number[]])), wallClear);
  // the round-13 check, unchanged: the named parts' drawn strips, their own edges left out
  const polys = parts.map((p: any) => ({ name: p.turn as string, P: stripOf(p) }));
  const zEdges = grid(polys.flatMap((q: { P: V2[] }) => ring(q.P)), edgeTol);
  const z = check(surf, polys, zEdges, walls, step, wallClear, edgeTol, null, false, rep.holes);
  rep.samples = z.samples; rep.onEdge = z.onEdge;
  // the box every named part reaches, grown by the margin
  const bb = polys.reduce((b: number[], q: { P: V2[] }) => { const c = bounds(q.P); return [Math.min(b[0], c[0]), Math.min(b[1], c[1]), Math.max(b[2], c[2]), Math.max(b[3], c[3])]; }, [Infinity, Infinity, -Infinity, -Infinity]);
  if (o.lane) {
    const m = o.lane.margin ?? 10;
    const box = [bb[0] - m, bb[1] - m, bb[2] + m, bb[3] + m];
    const lp = (sc.pit_lane?.parts ?? []).map((p: any) => ({ name: 'pit lane', P: stripOf(p) }));
    const edges = grid([...lp, ...polys].flatMap((q: { P: V2[] }) => ring(q.P)), edgeTol);
    const r = check(surf, lp, edges, walls, step, wallClear, edgeTol, box, false, rep.holes);
    rep.lane = { box: box.map((v) => Math.round(v * 100) / 100), parts: lp.length, ...r };
    for (const a of o.also ?? []) {
      const ap = a.parts.map((q) => new RegExp(q));
      const xs = (sc.paved_zones?.parts ?? []).filter((p: any) => ap.some((r_) => r_.test(p.turn ?? ''))).map((p: any) => ({ name: p.turn as string, P: stripOf(p) }));
      const e2 = grid([...xs, ...lp, ...polys].flatMap((q: { P: V2[] }) => ring(q.P)), edgeTol);
      // only near the lane (near_lane m of its drawn strip: the aisle end beside it), the rest of the paddock as it is
      const lg = grid(lp.flatMap((q: { P: V2[] }) => ring(q.P)), a.near_lane ?? 1e9);
      const nl = a.near_lane;
      const xs2 = nl === undefined ? xs : xs.map((q: { name: string; P: V2[] }) => ({ ...q, near: (x: number, y: number) => near(lg, x, y, nl) || lp.some((l: { P: V2[] }) => inPoly(x, y, l.P)) }));
      const r2 = check(surf, xs2, e2, walls, step, wallClear, edgeTol, box, false, rep.holes);
      rep.also = { parts: (rep.also?.parts ?? 0) + xs.length, samples: (rep.also?.samples ?? 0) + r2.samples, onEdge: (rep.also?.onEdge ?? 0) + r2.onEdge, holes: (rep.also?.holes ?? 0) + r2.holes };
    }
  }
  if (o.outlines?.length) {
    const op = o.outlines.map((q) => ({ name: `outline ${q.name}`, P: q.poly.map((p) => [p[0], p[1]] as V2) }));
    const e3 = grid(op.flatMap((q) => ring(q.P)), edgeTol);
    const r3 = check(surf, op, e3, walls, step, wallClear, edgeTol, null, true, rep.holes);
    rep.outlines = { polys: op.length, ...r3 };
  }
  return rep;
}
