// Static collision world built from scenery.json (CONTRACTS §2b): barrier runs and
// building footprints as vertical wall segments, tree trunks and wall corners as
// vertical cylinders, plus an invisible boundary wall 200 m inside the far
// heightfield's border. A uniform grid over all items makes a query around the
// car cost a few microseconds.

import { cos as dcos, hypot as dhypot } from './dmath';   // bit-identical to V8 on every engine (docs/determinism.md)
import type { TrackJson } from './track';

/** Kinds of obstacle. Index = kind code stored in the world. */
export const COLLISION_KINDS = ['concrete', 'armco', 'tyres', 'pitwall', 'fence', 'building', 'tree', 'boundary'] as const;
export type CollisionKind = (typeof COLLISION_KINDS)[number];

export interface KindProps {
  /** Coefficient of restitution for the normal impulse. */
  restitution: number;
  /** Coulomb friction along the wall. */
  friction: number;
  /** A hit faster than the launch speed sends the car into space (the easter egg). */
  launches: boolean;
  /** Soft contact (catch fence / tyre stack): spring-damper instead of a rigid impulse. */
  soft: boolean;
}

export const KIND_PROPS: Record<CollisionKind, KindProps> = {
  concrete: { restitution: 0.25, friction: 0.6, launches: true, soft: false },
  armco: { restitution: 0.3, friction: 0.6, launches: true, soft: false },
  // tyre walls are solid like concrete (Sonoma owner note, 22 Oct 2026: "I can drive into the tires in a tire wall"; the
  // spring-damper let the car sink in), with a low restitution: the stacks absorb the hit rather than bounce it back
  tyres: { restitution: 0.1, friction: 0.6, launches: true, soft: false },
  pitwall: { restitution: 0.25, friction: 0.6, launches: true, soft: false },
  fence: { restitution: 0.05, friction: 0.6, launches: false, soft: true },
  building: { restitution: 0.25, friction: 0.6, launches: true, soft: false },
  tree: { restitution: 0.2, friction: 0.6, launches: true, soft: false },
  boundary: { restitution: 0.2, friction: 0.3, launches: false, soft: false },
};

interface PackedTrees { stride: number; fields: string[]; scale: number; data: number[] }
interface Grid { x0: number; y0: number; dx: number; nx: number; ny: number }

/** The parts of scenery.json the collision world reads (all optional). */
export interface SceneryCollisionJson {
  far?: { heightfield?: Grid | null } | null;
  barriers?: { kind: string; h: number; fence?: number; pts: number[][] }[];
  buildings?: { z: number; h: number; footprint: number[][] }[];
  /** parametric structures (src/app/structures.ts): their solid outlines collide like buildings */
  structures?: { collide?: { z: number; h: number; footprint: number[][] }[] }[];
  trees?: PackedTrees | null;
  far_trees?: PackedTrees | null;
  landmarks?: { kind: string; x: number; y: number; z: number; h?: number }[];
}

/** The tyre wall as the app draws it (src/app/scenery.ts): stacks of radius TYRE_WALL.r every 0.62 m in two staggered
 *  rows, row 0 on the run's line and row 1 TYRE_WALL.row m to its LEFT (direction of the points). */
export const TYRE_WALL = { r: 0.31, row: 0.6, stagger: 0.31 } as const;
/** Contact begins this far from a wall segment's line (vehicle.ts WALL_HALF_THICKNESS). */
const WALL_SKIN = 0.1;

/** The polyline offset by d m to its left (per-vertex mitred normal, the miter capped at 2 x d). */
export function offsetLeft(pts: number[][], d: number): number[][] {
  const n = pts.length, out: number[][] = [];
  const nrm = (a: number[], b: number[]) => { const dx = b[0] - a[0], dy = b[1] - a[1], l = dhypot(dx, dy) || 1; return [-dy / l, dx / l]; };
  for (let i = 0; i < n; i++) {
    const na = i > 0 ? nrm(pts[i - 1], pts[i]) : nrm(pts[i], pts[i + 1]);
    const nb = i < n - 1 ? nrm(pts[i], pts[i + 1]) : na;
    let mx = na[0] + nb[0], my = na[1] + nb[1]; const ml = dhypot(mx, my);
    if (ml < 1e-9) { mx = nb[0]; my = nb[1]; } else { mx /= ml; my /= ml; }
    const c = mx * nb[0] + my * nb[1]; const k = Math.min(2, 1 / Math.max(c, 0.5));
    out.push([pts[i][0] + mx * d * k, pts[i][1] + my * d * k, pts[i][2] ?? 0]);
  }
  return out;
}

export interface CollisionWorldOptions {
  /** Trunk radius of trees, m. Default 0.35. */
  treeRadius?: number;
  /** Distance of the invisible boundary wall inside the outermost heightfield's border, m. Default 200. */
  boundaryInset?: number;
}

export class CollisionWorld {
  // segments: a→b, z range [zb, zt] hard, [zt, zf] soft (fence)
  readonly nSeg: number;
  readonly sax: Float64Array; readonly say: Float64Array; readonly sbx: Float64Array; readonly sby: Float64Array;
  readonly szb: Float64Array; readonly szt: Float64Array; readonly szf: Float64Array;
  readonly skind: Uint8Array;
  // cylinders (trees, wall corners/ends)
  readonly nCyl: number;
  readonly cx: Float64Array; readonly cy: Float64Array; readonly cr: Float64Array;
  readonly czb: Float64Array; readonly czt: Float64Array; readonly czf: Float64Array;
  readonly ckind: Uint8Array;
  /** Boundary rectangle (the car is kept inside). */
  readonly bounds: { x0: number; y0: number; x1: number; y1: number };

  private readonly cell: number;
  private readonly gx0: number; private readonly gy0: number;
  private readonly gnx: number; private readonly gny: number;
  private readonly cellStart: Int32Array;
  private readonly cellItems: Int32Array;
  private readonly stamp: Int32Array;
  private stampId = 0;
  /** Result buffer of the last query: item ids (< nSeg: segment, else cylinder nSeg + j). */
  readonly hits: Int32Array;
  hitCount = 0;

  constructor(segs: number[][], cyls: number[][], bounds: { x0: number; y0: number; x1: number; y1: number }) {
    this.bounds = bounds;
    const ns = segs.length, nc = cyls.length;
    this.nSeg = ns; this.nCyl = nc;
    const f = (n: number) => new Float64Array(n);
    this.sax = f(ns); this.say = f(ns); this.sbx = f(ns); this.sby = f(ns);
    this.szb = f(ns); this.szt = f(ns); this.szf = f(ns); this.skind = new Uint8Array(ns);
    segs.forEach((s, i) => {
      this.sax[i] = s[0]; this.say[i] = s[1]; this.sbx[i] = s[2]; this.sby[i] = s[3];
      this.szb[i] = s[4]; this.szt[i] = s[5]; this.szf[i] = s[6]; this.skind[i] = s[7];
    });
    this.cx = f(nc); this.cy = f(nc); this.cr = f(nc); this.czb = f(nc); this.czt = f(nc); this.czf = f(nc);
    this.ckind = new Uint8Array(nc);
    cyls.forEach((c, j) => {
      this.cx[j] = c[0]; this.cy[j] = c[1]; this.cr[j] = c[2]; this.czb[j] = c[3]; this.czt[j] = c[4]; this.czf[j] = c[5]; this.ckind[j] = c[6];
    });

    // grid over the item bounding box (boundary segments are tested separately)
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    const grow = (x: number, y: number) => { if (x < x0) x0 = x; if (y < y0) y0 = y; if (x > x1) x1 = x; if (y > y1) y1 = y; };
    for (let i = 0; i < ns; i++) { grow(this.sax[i], this.say[i]); grow(this.sbx[i], this.sby[i]); }
    for (let j = 0; j < nc; j++) { grow(this.cx[j] - this.cr[j], this.cy[j] - this.cr[j]); grow(this.cx[j] + this.cr[j], this.cy[j] + this.cr[j]); }
    if (!(x1 >= x0)) { x0 = 0; y0 = 0; x1 = 1; y1 = 1; }
    const cell = 8;
    this.cell = cell;
    this.gx0 = x0 - cell; this.gy0 = y0 - cell;
    this.gnx = Math.ceil((x1 - this.gx0) / cell) + 2;
    this.gny = Math.ceil((y1 - this.gy0) / cell) + 2;
    const nCells = this.gnx * this.gny;
    const counts = new Int32Array(nCells + 1);
    const forCells = (bx0: number, by0: number, bx1: number, by1: number, fn: (c: number) => void) => {
      const i0 = Math.floor((bx0 - this.gx0) / cell), i1 = Math.floor((bx1 - this.gx0) / cell);
      const j0 = Math.floor((by0 - this.gy0) / cell), j1 = Math.floor((by1 - this.gy0) / cell);
      for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) fn(i + this.gnx * j);
    };
    const each = (fn: (c: number) => void, id: number) => {
      if (id < ns) {
        forCells(Math.min(this.sax[id], this.sbx[id]), Math.min(this.say[id], this.sby[id]), Math.max(this.sax[id], this.sbx[id]), Math.max(this.say[id], this.sby[id]), fn);
      } else {
        const j = id - ns;
        forCells(this.cx[j] - this.cr[j], this.cy[j] - this.cr[j], this.cx[j] + this.cr[j], this.cy[j] + this.cr[j], fn);
      }
    };
    for (let id = 0; id < ns + nc; id++) each((c) => { counts[c + 1]++; }, id);
    for (let c = 0; c < nCells; c++) counts[c + 1] += counts[c];
    this.cellStart = counts;
    const fill = counts.slice(0, nCells);
    this.cellItems = new Int32Array(counts[nCells]);
    for (let id = 0; id < ns + nc; id++) each((c) => { this.cellItems[fill[c]++] = id; }, id);
    this.stamp = new Int32Array(ns + nc);
    this.hits = new Int32Array(512);
  }

  /** Collect the items whose cells overlap the box into `hits` (deduplicated). Returns the count. */
  query(xmin: number, ymin: number, xmax: number, ymax: number): number {
    let i0 = Math.floor((xmin - this.gx0) / this.cell), i1 = Math.floor((xmax - this.gx0) / this.cell);
    let j0 = Math.floor((ymin - this.gy0) / this.cell), j1 = Math.floor((ymax - this.gy0) / this.cell);
    this.hitCount = 0;
    if (i1 < 0 || j1 < 0 || i0 >= this.gnx || j0 >= this.gny) return 0;
    if (i0 < 0) i0 = 0; if (j0 < 0) j0 = 0;
    if (i1 >= this.gnx) i1 = this.gnx - 1; if (j1 >= this.gny) j1 = this.gny - 1;
    const id = ++this.stampId;
    if (id === 0x7fffffff) { this.stamp.fill(0); this.stampId = 1; }
    const st = this.stamp, hits = this.hits;
    let n = 0;
    for (let j = j0; j <= j1; j++) {
      for (let i = i0; i <= i1; i++) {
        const c = i + this.gnx * j;
        for (let k = this.cellStart[c], e = this.cellStart[c + 1]; k < e; k++) {
          const it = this.cellItems[k];
          if (st[it] === this.stampId) continue;
          st[it] = this.stampId;
          if (n < hits.length) hits[n++] = it;
        }
      }
    }
    this.hitCount = n;
    return n;
  }
}

function unpackTrees(p: PackedTrees | null | undefined): { x: number; y: number; z: number; h: number }[] {
  if (!p || !Array.isArray(p.data) || !(p.stride > 0)) return [];
  const fx = p.fields.indexOf('x'), fy = p.fields.indexOf('y'), fz = p.fields.indexOf('z'), fh = p.fields.indexOf('height');
  if (fx < 0 || fy < 0) return [];
  const s = p.scale ?? 1, out: { x: number; y: number; z: number; h: number }[] = [];
  for (let i = 0; i + p.stride <= p.data.length; i += p.stride) {
    out.push({ x: p.data[i + fx] * s, y: p.data[i + fy] * s, z: fz >= 0 ? p.data[i + fz] * s : 0, h: fh >= 0 ? p.data[i + fh] * s : 10 });
  }
  return out;
}

const KIND_CODE = (k: string): number => {
  const i = (COLLISION_KINDS as readonly string[]).indexOf(k);
  return i >= 0 ? i : 0; // unknown barrier kinds collide like concrete
};

/**
 * Build the collision world. `scenery` may be null (then only the boundary
 * exists). The boundary sits `boundaryInset` (200 m) inside the far
 * heightfield's border, or the near heightfield's when there is no far one.
 */
export function createCollisionWorld(scenery: SceneryCollisionJson | null | undefined, track: TrackJson, opts: CollisionWorldOptions = {}): CollisionWorld {
  const treeR = opts.treeRadius ?? 0.35;
  const segs: number[][] = [];
  const cyls: number[][] = [];
  const sc = scenery ?? {};

  // a tyre run collides at the faces of its drawn stacks: its two outer faces as wall lines (contact WALL_SKIN before
  // the face) and a stack-sized post at each row's ends
  const runs: { kind: string; h: number; fence?: number; pts: number[][] }[] = [];
  for (const b of sc.barriers ?? []) {
    if (b.kind !== 'tyres' || !Array.isArray(b.pts) || b.pts.length < 2) { runs.push(b); continue; }
    const P = b.pts.filter((p, i) => i === 0 || dhypot(p[0] - b.pts[i - 1][0], p[1] - b.pts[i - 1][1]) >= 1e-3);
    if (P.length < 2) continue;
    runs.push({ ...b, pts: offsetLeft(P, -(TYRE_WALL.r - WALL_SKIN)) });
    runs.push({ ...b, pts: offsetLeft(P, TYRE_WALL.row + TYRE_WALL.r - WALL_SKIN) });
    const kt = KIND_CODE('tyres'), h = Math.max(0, b.h ?? 1), fence = Math.max(0, b.fence ?? 0);
    for (const [p, q, sgn] of [[P[0], P[1], 1], [P[P.length - 1], P[P.length - 2], -1]] as const) {
      const l = dhypot(q[0] - p[0], q[1] - p[1]), tx = (q[0] - p[0]) / l, ty = (q[1] - p[1]) / l;
      const lx = sgn > 0 ? -ty : ty, ly = sgn > 0 ? tx : -tx;   // the run's left normal at this end
      const zb = p[2] ?? 0;
      cyls.push([p[0], p[1], TYRE_WALL.r, zb, zb + h, zb + h + fence, kt]);
      cyls.push([p[0] + lx * TYRE_WALL.row + tx * TYRE_WALL.stagger, p[1] + ly * TYRE_WALL.row + ty * TYRE_WALL.stagger, TYRE_WALL.r, zb, zb + h, zb + h + fence, kt]);
    }
  }
  for (const b of runs) {
    const pts = b.pts;
    if (!Array.isArray(pts) || pts.length < 2) continue;
    const isFence = b.kind === 'fence';
    const k = KIND_CODE(b.kind);
    const h = Math.max(0, b.h ?? 1), fence = Math.max(0, b.fence ?? 0);
    const closed = pts.length > 2 && dhypot(pts[0][0] - pts[pts.length - 1][0], pts[0][1] - pts[pts.length - 1][1]) < 0.05;
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i], c = pts[i + 1];
      if (dhypot(c[0] - a[0], c[1] - a[1]) < 1e-3) continue;
      const zb = Math.min(a[2] ?? 0, c[2] ?? 0);
      // a standalone fence run is soft over its whole height
      const zt = isFence ? zb : zb + h;
      const zf = isFence ? zb + h + fence : zb + h + fence;
      segs.push([a[0], a[1], c[0], c[1], zb, zt, zf, k]);
    }
    // wall ends and sharp corners as thin posts so they cannot slip between the car's sample points
    for (let i = 0; i < pts.length; i++) {
      if (closed && i === pts.length - 1) break;
      const p = pts[i];
      let corner = false;
      if (!closed && (i === 0 || i === pts.length - 1)) corner = true;
      else {
        const prev = pts[(i - 1 + pts.length) % pts.length], next = pts[(i + 1) % pts.length];
        const ux = p[0] - prev[0], uy = p[1] - prev[1], vx = next[0] - p[0], vy = next[1] - p[1];
        const lu = dhypot(ux, uy), lv = dhypot(vx, vy);
        if (lu > 1e-6 && lv > 1e-6) corner = (ux * vx + uy * vy) / (lu * lv) < dcos((25 * Math.PI) / 180);
      }
      if (corner) {
        const zb = p[2] ?? 0;
        cyls.push([p[0], p[1], 0.08, zb, isFence ? zb : zb + h, zb + h + fence, k]);
      }
    }
  }

  const kb = KIND_CODE('building');
  for (const bd of [...(sc.buildings ?? []), ...(sc.structures ?? []).flatMap((st) => st.collide ?? [])]) {
    const fp = bd.footprint;
    if (!Array.isArray(fp) || fp.length < 3) continue;
    const zb = bd.z ?? 0, zt = zb + Math.max(1, bd.h ?? 3);
    for (let i = 0; i < fp.length; i++) {
      const a = fp[i], c = fp[(i + 1) % fp.length];
      if (dhypot(c[0] - a[0], c[1] - a[1]) < 1e-3) continue;
      segs.push([a[0], a[1], c[0], c[1], zb - 1, zt, zt, kb]);
      cyls.push([a[0], a[1], 0.05, zb - 1, zt, zt, kb]);
    }
  }

  const kt = KIND_CODE('tree');
  for (const t of [...unpackTrees(sc.trees), ...unpackTrees(sc.far_trees)]) {
    cyls.push([t.x, t.y, treeR, t.z - 1, t.z + Math.max(2, t.h), t.z + Math.max(2, t.h), kt]);
  }
  for (const l of sc.landmarks ?? []) {
    if (l.kind === 'oak') cyls.push([l.x, l.y, 0.8, l.z - 1, l.z + (l.h ?? 10), l.z + (l.h ?? 10), kt]);
  }

  // boundary: 200 m inside the outermost heightfield
  const g: Grid = sc.far?.heightfield ?? track.heightfield;
  const gx1 = g.x0 + (g.nx - 1) * g.dx, gy1 = g.y0 + (g.ny - 1) * g.dx;
  const insetReq = opts.boundaryInset ?? 200;
  const inset = Math.min(insetReq, 0.25 * (gx1 - g.x0), 0.25 * (gy1 - g.y0));
  const bounds = { x0: g.x0 + inset, y0: g.y0 + inset, x1: gx1 - inset, y1: gy1 - inset };
  return new CollisionWorld(segs, cyls, bounds);
}

