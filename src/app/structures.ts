// Parametric structures (the buildings round, Sonoma, 21 Oct 2026): a kit of generators the app draws from the
// scenery.json `structures` descriptors that tools/track/build_structures.py writes from a track config's `structures`
// section. Generic, not per circuit: a bleacher grandstand (rows rising from a block-wall base, stair aisles, end stair
// towers, a glazed suites deck under a pitched roof with light clusters, a timing tower), a single-storey garage row
// (pitched metal roof, trim band, roll-up doors), a flat-roof block with window bands, a fuel island (canopy on posts,
// plain pylon), chain-link fence runs, light masts with head clusters, painted ground rectangles (pit-box lines), plain
// board panels along a line, and the dressing of a hillside terrace (bench rows, stair aisles with hand rails, shade
// roofs). Plain colours only (no logos, no imagery). Everything is merged into three meshes (solid, ground paint,
// fence fabric) so the whole set costs three draw calls.
//
// The geometry functions are pure (ENU metres in, triangle soup out) and tested in src/app/__tests__/structures.test.ts;
// buildStructures() wraps them in three.js meshes. ENU -> three: X = x, Y = z, Z = -y.
import * as THREE from 'three';

export type V2 = [number, number];
export type V3 = [number, number, number];

/** A bleacher grandstand. Local frame: t along the front line from `a` to `b` (m), d away from the track along `dir`
 *  (m), z above the structure's ground `z`. */
export interface GrandstandJson {
  type: 'grandstand'; name: string; src: string;
  a: V2; b: V2; dir: V2; z: number;
  /** block-wall base along the front: height, depth of the walkway on top, colour; plain panels on its face */
  base: { h: number; depth: number; color: string; walk?: string; rail?: string;
    panels?: { colors: string[]; w: number; h: number; gap: number; z: number } };
  /** seat rows: count, tread depth, rise per row, first tread above z, seat and riser colours, seat-back height */
  rows: { n: number; depth: number; rise: number; z0: number; seat: string; riser: string; back: number };
  /** stair aisles through the rows: pitch along the front (first at pitch / 2), width, colour */
  aisles?: { pitch: number; w: number; color: string };
  /** stair towers outside both ends: width along t, depth along d (from d0), top height, steel and cap colours */
  towers?: { w: number; d0: number; depth: number; h: number; steel: string; cap?: string };
  /** glazed suites deck over the top rows: from d0 to d1, floor and glass heights, roof [z front, z ridge, z back,
   *  ridge as a fraction of d0..d1], colours, column pitch, light clusters on the roof at t positions */
  suites?: { d0: number; d1: number; floor: number; glass: [number, number]; roof: [number, number, number, number];
    color: string; glass_color: string; roof_color: string; columns?: number;
    back?: { depth: number; h: number }; lights?: { t: number[]; h: number } };
  /** timing / press tower on the deck: t0..t1, d0..d1, from z0 to h, glazed band, colours */
  tower?: { t0: number; t1: number; d0: number; d1: number; z0: number; h: number; color: string; glass: string; roof: string };
  /** rear wall under the deck (ground to the floor) */
  rear?: { color: string };
  /** Mid-Ohio round 7: drawn part self-lit (TERRACE_SELF_LIT) like the terraces: aluminium bleachers that face away from
   *  the sun stay light; absent: plain Lambert */
  self_lit?: boolean;
  /** Mid-Ohio round 7: a roof over the rows (covered grandstand): d0..d1 from the front line (default 0 .. the top row
   *  + 0.5 m), its underside at z0 (front) and z1 (back), colours, column pitch, an optional fascia band across the
   *  front at z (a two-tier stand's middle deck); absent: no roof (every other track's grandstands unchanged) */
  cover?: { z0: number; z1: number; d0?: number; d1?: number; color: string; fascia?: string; under?: string; post?: string;
    posts?: number; band?: { z: number; h: number; color: string } };
}

/** Single-storey garage row: box l (along heading) x w, eaves at `eave`, ridge along the length at `ridge`
 *  (ridge == eave: flat), trim band under the eaves, roll-up doors at a pitch on one or both long sides. */
export interface GarageJson {
  type: 'garage'; name: string; src: string; c: V2; heading: number; l: number; w: number; z: number;
  eave: number; ridge: number; wall: string; roof: string; trim: string; trim_h: number; overhang?: number;
  /** side: +1 the left long side (seen along heading), -1 the right, 0 both */
  doors?: { side: -1 | 0 | 1; pitch: number; w: number; h: number; color: string };
  windows?: { side: -1 | 0 | 1; pitch: number; w: number; h: number; z: number; color: string };
  /** a parapet (m above the eaves) in the trim colour round a low roof */
  parapet?: number;
  /** mono-pitch roof: the eaves on this side (+1 left / -1 right) rise to `ridge`, the other side stays at `eave` */
  mono?: -1 | 1;
  /** round 9 (Sonoma pit-exit building): a continuous band on all four walls from z0 to z1 (a dark frontage) */
  band?: { z0: number; z1: number; color: string };
}

/** Round canopy (round 9, Sonoma's pit-exit terrace): a ring roof `d` across with an open centre `hole` across, its
 *  centre at height `h`, tilted up by `tilt_deg` toward the bearing `tilt_bearing`; a centre column and `posts` posts
 *  down to a raised round terrace (`deck`: top height, diameter, colour; none: the ground). */
export interface CanopyJson {
  type: 'canopy'; name?: string; src: string; c: V2; z: number; d: number; h: number; hole?: number; tilt_deg?: number;
  tilt_bearing?: number; color: string; post_color?: string; posts?: number; deck?: { h: number; d: number; color: string };
  /** round 10: the terrace stands on posts, open beneath (absent: a solid round podium, as round 9 drew it) */
  deck_posts?: number;
  /** round 10: a straight stair flight from the terrace edge down to the ground, leaving on `bearing_deg`, `w` wide, `run`
   *  long, its centre line `lateral` m to the right of that bearing through the canopy centre */
  stair?: { bearing_deg: number; w: number; run: number; lateral?: number; color?: string };
}

/** Flat-roof block of `storeys` storeys with a window band per storey on every face, roof parapet. */
export interface BlockJson {
  type: 'block'; name: string; src: string; c: V2; heading: number; l: number; w: number; z: number; h: number;
  storeys: number; wall: string; band: string; roof: string; parapet?: number; band_frac?: [number, number];
  /** the storeys (0 = ground) that carry a window band; absent: every storey (Buttonwillow's tower: the upper only) */
  bands?: number[];
  /** a balcony along the long side `side` (+1 / -1 of the frame, the builder resolves 'track'): its floor at z, depth
   *  out from the wall, a 1 m railing; and an exterior stair from the ground up to it at the +l end */
  balcony?: { side: number; z: number; depth: number; color?: string; stair?: boolean };
  /** a storey set back on the roof of a lower one (Buttonwillow's tower, judge r3): the block's base height above the
   *  ground (m), its glazing divided by wall-coloured mullions every mullions_m (m), and a railing round its own top
   *  edge (the open deck on the lower storey's roof) */
  base?: number; mullions_m?: number; deck_rail?: boolean;
  /** Mid-Ohio round 8 (the control tower): a hip roof over the block's top, its eaves `overhang` m out, rising `rise` m
   *  to a ridge of `ridge` m along l (0: a pyramid); absent: the flat roof */
  hip?: { rise: number; overhang: number; color: string; ridge?: number };
  /** Mid-Ohio round 8: decks wrapping all four faces (floor slab `depth` m out at z above the block's base, a solid
   *  railing `rail` m high in `color`); absent: none */
  wrap_decks?: { z: number; depth: number; color: string; rail?: number; floor?: string }[];
  /** discrete windows instead of the continuous band (Buttonwillow's tower, judge r5: a solid lower storey with a few
   *  windows): `w` wide every `pitch` m along each face from z0 to z1 (m above the block's base), on the faces listed
   *  (+1 / -1 long sides, +2 / -2 the ends; absent: all four); and doors (`at` along the face from its centre) */
  windows?: { w: number; pitch: number; z0: number; z1: number; faces?: number[] };
  doors_at?: { face: number; at: number; w: number; h: number; color?: string }[];
}

/** Fuel island: canopy slab on posts, island kerbs with pumps, a plain sign pylon at a local offset. */
export interface FuelJson {
  type: 'fuel'; name: string; src: string; c: V2; heading: number; l: number; w: number; z: number;
  h: number; fascia: number; canopy: string; fascia_color: string; posts: number; islands: number; edge_posts?: boolean;
  /** low hip roof on the canopy: rise above the fascia and colour */
  hip?: number; hip_color?: string;
  pylon?: { at: V2; h: number; w: number; color: string; panel: string };
}

export interface FenceJson { type: 'fence'; name?: string; src: string; pts: V3[]; h: number; color?: string; post_m?: number }
/** Light masts: base points [x, y, z, heading the lamps face], height, lamp grid [cols, rows] */
export interface MastJson { type: 'mast'; name?: string; src: string; at: [number, number, number, number][]; h: number; heads: [number, number]; color?: string }
/** Painted ground rectangles [cx, cy, heading, length, width] (pit-box lines) */
export interface PaintJson { type: 'paint'; name?: string; src: string; rects: [number, number, number, number, number][]; color: string; z?: number[] }
/** Plain board panels standing along a line at z0..z0 + h above the line's points */
/** `names` (round 6): each panel's typed name [text, background, text colour] in turn (the names the footage shows, as
 *  plain bold text, no logo artwork; drawn by buildStructures' `label`), its background replacing `colors` */
export interface BoardsJson { type: 'boards'; name?: string; src: string; pts: V3[]; z0: number; h: number; colors: string[]; panel: number; names?: [string, string, string][] }
/** A slender scoring tower (round 6, Sonoma's on the Carousel hill): a column w (along `heading_deg`) x d, h tall over
 *  the ground at its centre, on an optional plinth, with an optional wider head board at its top. */
export interface ScoringTowerJson {
  type: 'scoring_tower'; name?: string; src: string; c: V2; z: number; heading_deg: number; w: number; d: number; h: number; color: string;
  head?: { h: number; w: number; d: number; color: string }; plinth?: { w: number; h: number; color: string };
}
/** Dressing of a hillside terrace (scenery.json `terraces` by name): bench strip per row, stair aisles with hand
 *  rails, shade roofs over the top rows between fractions f0..f1 of the row length */
export interface TerraceDressJson {
  type: 'terrace_dress'; name?: string; src: string; terrace: string;
  bench?: { color: string; h: number; depth: number };
  aisles?: { pitch: number; w: number; color: string; rail?: string };
  shades?: { f0: number; f1: number; rows: number; h: number; color: string }[];
}

/** every structure may carry solid outlines for the collision world (src/physics/collision.ts reads them like buildings) */
export interface Collide { collide?: { footprint: V2[]; z: number; h: number }[] }
export type StructureJson = (GrandstandJson | GarageJson | BlockJson | FuelJson | FenceJson | MastJson | PaintJson | BoardsJson | TerraceDressJson | ScoringTowerJson | CanopyJson) & Collide;
/** A terrace row: straight (a, b at height z), or, for a terrace declared by its measured footprint (Sonoma round 6), a
 *  polyline following the stand: `pts` [x, y, z, z_low, m] (tread height, the row below's height, metres along the front
 *  line) with `nrm` the uphill unit vector per vertex, and `k` the row number. */
export interface TerraceRow { a: V2; b: V2; z: number; k?: number; pts?: [number, number, number, number, number][]; nrm?: V2[] }
export interface TerraceJson { name: string; run: number; dir: V2; z_ground_front: number; rows: TerraceRow[] }

// ------------------------------------------------------------------ triangle soup
const colorCache = new Map<string, [number, number, number]>();
/** sRGB hex -> linear rgb (three's working colour space) */
export function rgb(hex: string, k = 1): [number, number, number] {
  let c = colorCache.get(hex);
  if (!c) { const t = new THREE.Color(hex); c = [t.r, t.g, t.b]; colorCache.set(hex, c); }
  return k === 1 ? c : [c[0] * k, c[1] * k, c[2] * k];
}

/** Triangles in ENU with a colour per triangle. */
export class Soup {
  pos: number[] = [];
  col: number[] = [];
  /** per-vertex uv, only for soups built with ribbon(..., uvScale) (the fence fabric) */
  uv: number[] = [];
  get tris(): number { return this.pos.length / 9; }
  tri(a: V3, b: V3, c: V3, k: [number, number, number]): void {
    this.pos.push(a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]);
    for (let i = 0; i < 3; i++) this.col.push(k[0], k[1], k[2]);
  }
  quad(a: V3, b: V3, c: V3, d: V3, k: [number, number, number]): void { this.tri(a, b, c, k); this.tri(a, c, d, k); }
  /** axis-aligned box of a local frame: five faces (no bottom) unless `bottom` */
  box(f: Frame, t0: number, t1: number, d0: number, d1: number, z0: number, z1: number, k: [number, number, number], opt: { bottom?: boolean; top?: [number, number, number] | null; shade?: boolean } = {}): void {
    const p = (t: number, d: number, z: number) => f.p(t, d, z);
    const s = opt.shade === false ? 1 : 0.86;   // darker sides for some form without lighting tricks
    const ks: [number, number, number] = [k[0] * s, k[1] * s, k[2] * s];
    this.quad(p(t0, d0, z0), p(t1, d0, z0), p(t1, d0, z1), p(t0, d0, z1), k);     // front (d0)
    this.quad(p(t1, d1, z0), p(t0, d1, z0), p(t0, d1, z1), p(t1, d1, z1), k);     // back (d1)
    this.quad(p(t0, d1, z0), p(t0, d0, z0), p(t0, d0, z1), p(t0, d1, z1), ks);    // end t0
    this.quad(p(t1, d0, z0), p(t1, d1, z0), p(t1, d1, z1), p(t1, d0, z1), ks);    // end t1
    if (opt.top !== null) this.quad(p(t0, d0, z1), p(t1, d0, z1), p(t1, d1, z1), p(t0, d1, z1), opt.top ?? k);
    if (opt.bottom) this.quad(p(t0, d1, z0), p(t1, d1, z0), p(t1, d0, z0), p(t0, d0, z0), k);
  }
  /** a vertical quad strip along a polyline from z+z0 to z+z1 (per point z); with uvScale, uv = (distance along the
   *  line, height) / uvScale */
  ribbon(P: V3[], z0: number, z1: number, k: [number, number, number], uvScale = 0): void {
    let u = 0;
    for (let i = 0; i + 1 < P.length; i++) {
      const a = P[i], b = P[i + 1], du = Math.hypot(b[0] - a[0], b[1] - a[1]);
      this.quad([a[0], a[1], a[2] + z0], [b[0], b[1], b[2] + z0], [b[0], b[1], b[2] + z1], [a[0], a[1], a[2] + z1], k);
      if (uvScale) {
        const u0 = u / uvScale, u1 = (u + du) / uvScale, v0 = z0 / uvScale, v1 = z1 / uvScale;
        this.uv.push(u0, v0, u1, v0, u1, v1, u0, v0, u1, v1, u0, v1);
      }
      u += du;
    }
  }
  bounds(): { min: V3; max: V3 } {
    const min: V3 = [Infinity, Infinity, Infinity], max: V3 = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < this.pos.length; i += 3) for (let j = 0; j < 3; j++) { min[j] = Math.min(min[j], this.pos[i + j]); max[j] = Math.max(max[j], this.pos[i + j]); }
    return { min, max };
  }
}

/** Local frame: origin o (ENU, z = ground), t along ut, d along ud (unit, any angle to ut), z up. */
export class Frame {
  constructor(public o: V3, public ut: V2, public ud: V2) {}
  static heading(c: V2, z: number, heading: number): Frame {
    const ut: V2 = [Math.cos(heading), Math.sin(heading)];
    return new Frame([c[0], c[1], z], ut, [-ut[1], ut[0]]);
  }
  p(t: number, d: number, z: number): V3 {
    return [this.o[0] + this.ut[0] * t + this.ud[0] * d, this.o[1] + this.ut[1] * t + this.ud[1] * d, this.o[2] + z];
  }
}

const hash = (i: number) => { let x = (i * 2654435761) >>> 0; x ^= x >>> 15; return (x % 1000) / 1000; };

// ------------------------------------------------------------------ grandstand
export function grandstand(g: GrandstandJson, s: Soup): void {
  const L = Math.hypot(g.b[0] - g.a[0], g.b[1] - g.a[1]);
  const ut: V2 = [(g.b[0] - g.a[0]) / L, (g.b[1] - g.a[1]) / L];
  const f = new Frame([g.a[0], g.a[1], g.z], ut, g.dir);
  const B = g.base, R = g.rows;
  const cBase = rgb(B.color), cWalk = rgb(B.walk ?? '#a9a69f'), cRail = rgb(B.rail ?? '#5d6166');
  const cSeat = rgb(R.seat), cSeatBack = rgb(R.seat, 0.95), cRiser = rgb(R.riser);
  // base wall and the walkway on it
  s.box(f, 0, L, 0, B.depth, -0.5, B.h, cBase, { top: cWalk });
  s.box(f, 0, L, 0.02, 0.12, B.h, B.h + 1.05, cRail, { top: cRail });            // front hand rail (solid panel)
  if (B.panels) {
    const P = B.panels;
    let t = P.gap / 2, i = 0;
    while (t + P.w <= L - P.gap / 2 + 1e-6) {
      s.box(f, t, t + P.w, -0.08, 0, P.z, P.z + P.h, rgb(P.colors[i % P.colors.length]), { shade: false });
      t += P.w + P.gap; i++;
    }
  }
  // sections between aisles along t
  const cuts: [number, number, boolean][] = [];   // [t0, t1, isAisle]
  if (g.aisles && g.aisles.pitch > g.aisles.w) {
    let t = 0;
    for (let x = g.aisles.pitch / 2; x < L - g.aisles.w; x += g.aisles.pitch) {
      cuts.push([t, x - g.aisles.w / 2, false]); cuts.push([x - g.aisles.w / 2, x + g.aisles.w / 2, true]); t = x + g.aisles.w / 2;
    }
    cuts.push([t, L, false]);
  } else cuts.push([0, L, false]);
  const cAisle = rgb(g.aisles?.color ?? '#b5b2aa');
  const dTop = B.depth + R.n * R.depth;
  for (let r = 0; r < R.n; r++) {
    const d0 = B.depth + r * R.depth, d1 = d0 + R.depth;
    const z = R.z0 + r * R.rise, zl = r === 0 ? B.h : R.z0 + (r - 1) * R.rise;
    for (const [t0, t1, aisle] of cuts) {
      if (aisle) {
        // two steps per row
        const zm = (z + zl) / 2, dm = d0 + R.depth / 2;
        s.quad(f.p(t0, d0, zl), f.p(t1, d0, zl), f.p(t1, d0, zm), f.p(t0, d0, zm), cRiser);
        s.quad(f.p(t0, d0, zm), f.p(t1, d0, zm), f.p(t1, dm, zm), f.p(t0, dm, zm), cAisle);
        s.quad(f.p(t0, dm, zm), f.p(t1, dm, zm), f.p(t1, dm, z), f.p(t0, dm, z), cRiser);
        s.quad(f.p(t0, dm, z), f.p(t1, dm, z), f.p(t1, d1, z), f.p(t0, d1, z), cAisle);
      } else {
        s.quad(f.p(t0, d0, zl), f.p(t1, d0, zl), f.p(t1, d0, z), f.p(t0, d0, z), cRiser);     // riser
        s.quad(f.p(t0, d0, z), f.p(t1, d0, z), f.p(t1, d1, z), f.p(t0, d1, z), cSeat);       // tread
        // seat backs: a slab leaning on the back third of the tread (reads as a row of chairs)
        const db = d0 + R.depth * 0.62;
        s.quad(f.p(t0, db, z), f.p(t1, db, z), f.p(t1, db + 0.08, z + R.back), f.p(t0, db + 0.08, z + R.back), cSeatBack);
      }
    }
    // end walls under each row (closing the rake)
    for (const t of [0, L]) s.quad(f.p(t, d0, -0.5), f.p(t, d1, -0.5), f.p(t, d1, z), f.p(t, d0, z), rgb(B.color, 0.9));
  }
  const zTop = R.z0 + (R.n - 1) * R.rise;
  const Su = g.suites;
  // rear: from the top row back to the deck's back, ground to the floor (or the top row height)
  const dRear = Su ? Math.max(Su.d1, dTop) : dTop;
  const zRear = Su ? Su.floor : zTop + 1.1;
  const cRear = rgb(g.rear?.color ?? B.color);
  s.box(f, 0, L, dTop, dRear, -0.5, zRear, cRear);
  if (!Su) s.box(f, 0, L, dTop - 0.1, dTop, zTop, zTop + 1.1, cRail);              // top rail
  if (Su) {
    const cS = rgb(Su.color), cG = rgb(Su.glass_color), cRoof = rgb(Su.roof_color);
    // floor slab over the top rows, columns at its front edge down to the seats
    s.box(f, 0, L, Su.d0, Su.d1, Su.floor - 0.6, Su.floor, cS, { bottom: true });
    if (Su.columns) {
      const zAt = (d: number) => R.z0 + Math.max(0, Math.min(R.n - 1, Math.floor((d - B.depth) / R.depth))) * R.rise;
      for (let t = Su.columns / 2; t < L; t += Su.columns) s.box(f, t - 0.3, t + 0.3, Su.d0 + 0.3, Su.d0 + 0.9, zAt(Su.d0 + 0.6), Su.floor - 0.6, cS, { top: null });
    }
    // glazed band set back 1 m (a balcony), spandrel to the roof, solid back and ends
    const [g0, g1] = Su.glass;
    s.box(f, 0, L, Su.d0, Su.d0 + 0.12, Su.floor, Su.floor + 1.05, cRail, { top: cRail });   // balcony rail
    s.box(f, 0.3, L - 0.3, Su.d0 + 1, Su.d1 - 0.2, Su.floor, g0, cS, { top: null });
    s.box(f, 0.3, L - 0.3, Su.d0 + 1, Su.d1 - 0.2, g0, g1, cG, { top: null });
    // mullions every 3.6 m on the glass front
    for (let t = 1.8; t < L - 0.5; t += 3.6) s.box(f, t - 0.08, t + 0.08, Su.d0 + 0.92, Su.d0 + 1, g0, g1, cS, { top: null, shade: false });
    const [zf, zr, zb, rf] = Su.roof;
    const dr = Su.d0 + (Su.d1 - Su.d0) * rf;
    s.box(f, 0.3, L - 0.3, Su.d0 + 1, Su.d1 - 0.2, g1, Math.min(zf, zb) - 0.4, cS, { top: null });
    // roof: two slopes with a 1 m overhang at the front, fascia
    const o = 1.0;
    s.quad(f.p(-0.4, Su.d0 - o, zf), f.p(L + 0.4, Su.d0 - o, zf), f.p(L + 0.4, dr, zr), f.p(-0.4, dr, zr), cRoof);
    s.quad(f.p(-0.4, dr, zr), f.p(L + 0.4, dr, zr), f.p(L + 0.4, Su.d1, zb), f.p(-0.4, Su.d1, zb), rgb(Su.roof_color, 0.9));
    s.quad(f.p(-0.4, Su.d0 - o, zf - 0.7), f.p(L + 0.4, Su.d0 - o, zf - 0.7), f.p(L + 0.4, Su.d0 - o, zf), f.p(-0.4, Su.d0 - o, zf), cS);
    for (const t of [-0.4, L + 0.4]) {   // gable ends of the roof down to the walls
      s.tri(f.p(t, Su.d0 - o, zf), f.p(t, dr, zr), f.p(t, Su.d1, zb), cRoof);
      s.quad(f.p(t, Su.d0 - o, zf - 0.7), f.p(t, Su.d1, zb - 0.7), f.p(t, Su.d1, zb), f.p(t, Su.d0 - o, zf), cS);
    }
    if (Su.back) s.box(f, 0, L, Su.d1, Su.d1 + Su.back.depth, -0.5, Su.back.h, cRear);
    // light clusters on the roof
    if (Su.lights) for (const t of Su.lights.t) {
      const dz = zf + (zr - zf) * 0.5, d = Su.d0 + (dr - Su.d0) * 0.5;
      mastAt(s, f.p(t, d, dz), Su.lights.h, [3, 2], Math.atan2(-g.dir[1], -g.dir[0]), '#8c9196');
    }
  }
  const Cv = g.cover;
  if (Cv) {
    // Mid-Ohio round 7: a roof over the rows (the covered grandstands of the pit straight), a slab from d0 to d1 sloping
    // from z0 (front) to z1 (back) with a fascia band, on columns along the front and the back every `posts` m
    const d0 = Cv.d0 ?? 0, d1 = Cv.d1 ?? dTop + 0.5, cR = rgb(Cv.color), cF = rgb(Cv.fascia ?? Cv.color, 0.85), cP = rgb(Cv.post ?? '#5d6166');
    const th = 0.35;
    s.quad(f.p(-0.3, d0, Cv.z0 + th), f.p(L + 0.3, d0, Cv.z0 + th), f.p(L + 0.3, d1, Cv.z1 + th), f.p(-0.3, d1, Cv.z1 + th), cR);   // top
    s.quad(f.p(-0.3, d1, Cv.z1), f.p(L + 0.3, d1, Cv.z1), f.p(L + 0.3, d0, Cv.z0), f.p(-0.3, d0, Cv.z0), rgb(Cv.under ?? '#55585c'));  // underside
    s.quad(f.p(-0.3, d0, Cv.z0), f.p(L + 0.3, d0, Cv.z0), f.p(L + 0.3, d0, Cv.z0 + th), f.p(-0.3, d0, Cv.z0 + th), cF);   // front fascia
    s.quad(f.p(L + 0.3, d1, Cv.z1), f.p(-0.3, d1, Cv.z1), f.p(-0.3, d1, Cv.z1 + th), f.p(L + 0.3, d1, Cv.z1 + th), cF);   // back fascia
    const pitch = Cv.posts ?? 8;
    for (let t = 0; t <= L + 1e-6; t += Math.max(2, L / Math.max(1, Math.round(L / pitch)))) {
      s.box(f, t - 0.12, t + 0.12, d0 + 0.1, d0 + 0.34, -0.3, Cv.z0, cP, { top: null });
      s.box(f, t - 0.12, t + 0.12, d1 - 0.34, d1 - 0.1, -0.3, Cv.z1, cP, { top: null });
    }
    // a second, lower roof band across the front (the two-tier stand's middle deck fascia), optional
    if (Cv.band) s.box(f, 0, L, d0 - 0.2, d0 + 0.2, Cv.band.z, Cv.band.z + Cv.band.h, rgb(Cv.band.color));
  }
  const T = g.tower;
  if (T) {
    const cT = rgb(T.color), cG = rgb(T.glass);
    const zg0 = T.z0 + (T.h - T.z0) * 0.25, zg1 = T.z0 + (T.h - T.z0) * 0.8;
    s.box(f, T.t0, T.t1, T.d0, T.d1, T.z0, zg0, cT, { top: null });
    s.box(f, T.t0 + 0.2, T.t1 - 0.2, T.d0 + 0.2, T.d1 - 0.2, zg0, zg1, cG, { top: null });
    s.box(f, T.t0, T.t1, T.d0, T.d1, zg1, T.h, cT, { top: rgb(T.roof) });
    s.box(f, T.t0 - 0.5, T.t1 + 0.5, T.d0 - 0.5, T.d1 + 0.5, T.h, T.h + 0.5, rgb(T.roof));   // roof slab with overhang
  }
  const W = g.towers;
  if (W) {
    const cSt = rgb(W.steel), cCap = rgb(W.cap ?? W.steel);
    for (const [ta, tb] of [[-W.w, 0], [L, L + W.w]] as [number, number][]) {
      const d0 = W.d0, d1 = W.d0 + W.depth;
      for (const t of [ta, tb]) for (const d of [d0, d1]) s.box(f, t - 0.15, t + 0.15, d - 0.15, d + 0.15, -0.3, W.h, cSt, { top: null });
      // landings every 3.6 m and switchback flights between them
      const nL = Math.max(1, Math.floor(W.h / 3.6));
      for (let k = 1; k <= nL; k++) {
        const z = (W.h * k) / nL, zp = (W.h * (k - 1)) / nL, dm = (d0 + d1) / 2;
        s.box(f, ta, tb, k % 2 ? d1 - 1.4 : d0, k % 2 ? d1 : d0 + 1.4, z - 0.25, z, cSt);
        const tm = (ta + tb) / 2;
        const [sa, sb] = k % 2 ? [d0 + 1.4, d1 - 1.4] : [d1 - 1.4, d0 + 1.4];
        const half = k % 2 ? [ta, tm] : [tm, tb];
        s.quad(f.p(half[0], sa, zp), f.p(half[1], sa, zp), f.p(half[1], sb, z), f.p(half[0], sb, z), cSt);
        s.box(f, ta - 0.03, tb + 0.03, dm - 0.03, dm + 0.03, z - 0.2, z + 1.0, cSt, { top: null, shade: false });   // guard rail
      }
      s.box(f, ta - 0.4, tb + 0.4, d0 - 0.4, d1 + 0.4, W.h, W.h + 0.4, cCap);   // cap
    }
  }
}

// ------------------------------------------------------------------ garage row, block, fuel island
function sideList(side: -1 | 0 | 1): (-1 | 1)[] { return side === 0 ? [1, -1] : [side]; }

export function garage(g: GarageJson, s: Soup): void {
  const f = Frame.heading(g.c, g.z, g.heading);
  const hl = g.l / 2, hw = g.w / 2, o = g.overhang ?? 0.5;
  const cW = rgb(g.wall), cR = rgb(g.roof), cTr = rgb(g.trim);
  s.box(f, -hl, hl, -hw, hw, -0.5, g.eave, cW, { top: null });
  if (g.trim_h > 0) s.box(f, -hl - 0.05, hl + 0.05, -hw - 0.05, hw + 0.05, g.eave - g.trim_h, g.eave, cTr, { top: null, shade: false });   // trim band
  if (g.band) {
    // round 9: a continuous band round the walls (no openings), just proud of the wall faces
    const e = 0.04, z0 = g.band.z0, z1 = g.band.z1, cB = rgb(g.band.color);
    s.quad(f.p(-hl, -hw - e, z0), f.p(hl, -hw - e, z0), f.p(hl, -hw - e, z1), f.p(-hl, -hw - e, z1), cB);
    s.quad(f.p(hl, hw + e, z0), f.p(-hl, hw + e, z0), f.p(-hl, hw + e, z1), f.p(hl, hw + e, z1), cB);
    s.quad(f.p(-hl - e, hw, z0), f.p(-hl - e, -hw, z0), f.p(-hl - e, -hw, z1), f.p(-hl - e, hw, z1), cB);
    s.quad(f.p(hl + e, -hw, z0), f.p(hl + e, hw, z0), f.p(hl + e, hw, z1), f.p(hl + e, -hw, z1), cB);
  }
  if (g.mono) {
    // mono-pitch: high side at d = mono * hw; side walls and the end walls rise to the roof line
    const m = g.mono, zr = g.ridge, ze = g.eave;
    const zAt = (d: number) => ze + ((d * m + hw) / (2 * hw)) * (zr - ze);
    s.box(f, -hl, hl, m > 0 ? hw - 0.01 : -hw, m > 0 ? hw : -hw + 0.01, g.eave, zr, cW, { top: null });
    for (const t of [-hl, hl]) s.quad(f.p(t, -hw, ze), f.p(t, hw, ze), f.p(t, hw, zAt(hw)), f.p(t, -hw, zAt(-hw)), cW);
    s.quad(f.p(-hl - o, -hw - o, zAt(-hw - o)), f.p(hl + o, -hw - o, zAt(-hw - o)), f.p(hl + o, hw + o, zAt(hw + o)), f.p(-hl - o, hw + o, zAt(hw + o)), cR);
    for (const d of [-hw - o, hw + o]) s.quad(f.p(-hl - o, d, zAt(d) - 0.45), f.p(hl + o, d, zAt(d) - 0.45), f.p(hl + o, d, zAt(d)), f.p(-hl - o, d, zAt(d)), cTr);
    for (const t of [-hl - o, hl + o]) s.quad(f.p(t, -hw - o, zAt(-hw - o) - 0.45), f.p(t, hw + o, zAt(hw + o) - 0.45), f.p(t, hw + o, zAt(hw + o)), f.p(t, -hw - o, zAt(-hw - o)), cTr);
  } else if (g.parapet) {
    s.box(f, -hl - 0.1, hl + 0.1, -hw - 0.1, hw + 0.1, g.eave, g.eave + g.parapet, cTr, { top: null, shade: false });
    s.quad(f.p(-hl, -hw, g.eave + 0.2), f.p(hl, -hw, g.eave + 0.2), f.p(hl, hw, g.eave + 0.2), f.p(-hl, hw, g.eave + 0.2), cR);
  } else if (g.ridge > g.eave + 0.05) {
    // ridge along the length; eaves overhang by o
    const zr = g.ridge, ze = g.eave - o * (g.ridge - g.eave) / hw;
    s.quad(f.p(-hl - o, -hw - o, ze), f.p(hl + o, -hw - o, ze), f.p(hl + o, 0, zr), f.p(-hl - o, 0, zr), cR);
    s.quad(f.p(hl + o, hw + o, ze), f.p(-hl - o, hw + o, ze), f.p(-hl - o, 0, zr), f.p(hl + o, 0, zr), rgb(g.roof, 0.88));
    for (const t of [-hl, hl]) s.tri(f.p(t, -hw, g.eave), f.p(t, hw, g.eave), f.p(t, 0, zr), cW);   // gables
    for (const d of [-hw - o, hw + o]) s.quad(f.p(-hl - o, d, ze - 0.25), f.p(hl + o, d, ze - 0.25), f.p(hl + o, d, ze), f.p(-hl - o, d, ze), cTr);   // fascia
  } else {
    s.box(f, -hl - o, hl + o, -hw - o, hw + o, g.eave, g.eave + 0.3, cR, { shade: false });
  }
  const openings = (spec: { side: -1 | 0 | 1; pitch: number; w: number; h: number; color: string }, z0: number) => {
    for (const sd of sideList(spec.side)) {
      const n = Math.max(1, Math.floor((g.l - 1) / spec.pitch));
      const t0 = -((n - 1) * spec.pitch) / 2;
      for (let i = 0; i < n; i++) {
        const t = t0 + i * spec.pitch;
        const d = sd * (hw + 0.04);
        const a = f.p(t - spec.w / 2, d, z0), b = f.p(t + spec.w / 2, d, z0), c = f.p(t + spec.w / 2, d, z0 + spec.h), e = f.p(t - spec.w / 2, d, z0 + spec.h);
        s.quad(a, b, c, e, rgb(spec.color, 0.92 + 0.08 * hash(i)));
      }
    }
  };
  if (g.doors) openings(g.doors, 0);
  if (g.windows) openings(g.windows, g.windows.z);
}

export function block(b: BlockJson, s: Soup): void {
  const f = Frame.heading(b.c, b.z + (b.base ?? 0), b.heading);
  const hl = b.l / 2, hw = b.w / 2;
  const cW = rgb(b.wall), cB = rgb(b.band), cR = rgb(b.roof);
  s.box(f, -hl, hl, -hw, hw, -0.5, b.h, cW, { top: cR });
  if (b.parapet) {
    s.box(f, -hl, hl, -hw, -hw + 0.25, b.h, b.h + b.parapet, cW, { shade: false });
    s.box(f, -hl, hl, hw - 0.25, hw, b.h, b.h + b.parapet, cW, { shade: false });
    s.box(f, -hl, -hl + 0.25, -hw, hw, b.h, b.h + b.parapet, cW, { shade: false });
    s.box(f, hl - 0.25, hl, -hw, hw, b.h, b.h + b.parapet, cW, { shade: false });
  }
  const [f0, f1] = b.band_frac ?? [0.3, 0.8];
  const sh = b.h / b.storeys;
  for (let k = 0; k < b.storeys; k++) {
    if (b.bands && !b.bands.includes(k)) continue;
    const z0 = k * sh + f0 * sh, z1 = k * sh + f1 * sh, e = 0.04;
    s.quad(f.p(-hl + 0.6, -hw - e, z0), f.p(hl - 0.6, -hw - e, z0), f.p(hl - 0.6, -hw - e, z1), f.p(-hl + 0.6, -hw - e, z1), cB);
    s.quad(f.p(hl - 0.6, hw + e, z0), f.p(-hl + 0.6, hw + e, z0), f.p(-hl + 0.6, hw + e, z1), f.p(hl - 0.6, hw + e, z1), cB);
    s.quad(f.p(-hl - e, hw - 0.6, z0), f.p(-hl - e, -hw + 0.6, z0), f.p(-hl - e, -hw + 0.6, z1), f.p(-hl - e, hw - 0.6, z1), cB);
    s.quad(f.p(hl + e, -hw + 0.6, z0), f.p(hl + e, hw - 0.6, z0), f.p(hl + e, hw - 0.6, z1), f.p(hl + e, -hw + 0.6, z1), cB);
  }
  if (b.mullions_m) {
    // wall-coloured mullions across the bands (divided glazing)
    const e = 0.06;
    for (let k = 0; k < b.storeys; k++) {
      if (b.bands && !b.bands.includes(k)) continue;
      const z0 = k * sh + f0 * sh, z1 = k * sh + f1 * sh;
      for (let t = -hl + 0.6 + b.mullions_m; t < hl - 0.6; t += b.mullions_m) {
        s.box(f, t - 0.06, t + 0.06, -hw - e, -hw, z0, z1, cW); s.box(f, t - 0.06, t + 0.06, hw, hw + e, z0, z1, cW);
      }
      for (let d = -hw + 0.6 + b.mullions_m; d < hw - 0.6; d += b.mullions_m) {
        s.box(f, -hl - e, -hl, d - 0.06, d + 0.06, z0, z1, cW); s.box(f, hl, hl + e, d - 0.06, d + 0.06, z0, z1, cW);
      }
    }
  }
  if (b.windows) {
    const W = b.windows, e = 0.04, faces = W.faces ?? [1, -1, 2, -2];
    for (const fc of faces) {
      const half = Math.abs(fc) === 1 ? hl : hw, n = Math.max(1, Math.floor((2 * half - 1.2) / W.pitch));
      for (let q = 0; q < n; q++) {
        const t = -((n - 1) * W.pitch) / 2 + q * W.pitch, a = t - W.w / 2, c = t + W.w / 2;
        if (fc === 1) s.quad(f.p(c, hw + e, W.z0), f.p(a, hw + e, W.z0), f.p(a, hw + e, W.z1), f.p(c, hw + e, W.z1), cB);
        else if (fc === -1) s.quad(f.p(a, -hw - e, W.z0), f.p(c, -hw - e, W.z0), f.p(c, -hw - e, W.z1), f.p(a, -hw - e, W.z1), cB);
        else if (fc === 2) s.quad(f.p(hl + e, a, W.z0), f.p(hl + e, c, W.z0), f.p(hl + e, c, W.z1), f.p(hl + e, a, W.z1), cB);
        else s.quad(f.p(-hl - e, c, W.z0), f.p(-hl - e, a, W.z0), f.p(-hl - e, a, W.z1), f.p(-hl - e, c, W.z1), cB);
      }
    }
  }
  for (const d of b.doors_at ?? []) {
    const e = 0.05, cD = rgb(d.color ?? '#6b5a48'), a = d.at - d.w / 2, c = d.at + d.w / 2;
    if (d.face === 1) s.quad(f.p(c, hw + e, 0), f.p(a, hw + e, 0), f.p(a, hw + e, d.h), f.p(c, hw + e, d.h), cD);
    else if (d.face === -1) s.quad(f.p(a, -hw - e, 0), f.p(c, -hw - e, 0), f.p(c, -hw - e, d.h), f.p(a, -hw - e, d.h), cD);
    else if (d.face === 2) s.quad(f.p(hl + e, a, 0), f.p(hl + e, c, 0), f.p(hl + e, c, d.h), f.p(hl + e, a, d.h), cD);
    else s.quad(f.p(-hl - e, c, 0), f.p(-hl - e, a, 0), f.p(-hl - e, a, d.h), f.p(-hl - e, c, d.h), cD);
  }
  for (const dk of b.wrap_decks ?? []) {
    const D = dk.depth, cF = rgb(dk.floor ?? '#8b8d90'), cRl = rgb(dk.color), rh = dk.rail ?? 1.0;
    s.box(f, -hl - D, hl + D, -hw - D, hw + D, dk.z - 0.25, dk.z, cF, { bottom: true });
    s.box(f, -hl - D, hl + D, -hw - D, -hw - D + 0.08, dk.z, dk.z + rh, cRl);
    s.box(f, -hl - D, hl + D, hw + D - 0.08, hw + D, dk.z, dk.z + rh, cRl);
    s.box(f, -hl - D, -hl - D + 0.08, -hw - D, hw + D, dk.z, dk.z + rh, cRl);
    s.box(f, hl + D - 0.08, hl + D, -hw - D, hw + D, dk.z, dk.z + rh, cRl);
  }
  if (b.hip) {
    const o = b.hip.overhang, z0 = b.h + (b.parapet ?? 0), z1 = z0 + b.hip.rise, cH = rgb(b.hip.color), cU = rgb(b.hip.color, 0.6);
    const A = hl + o, B = hw + o, rl = Math.min(b.hip.ridge ?? 0, 2 * A) / 2;
    const e0 = f.p(-A, -B, z0), e1 = f.p(A, -B, z0), e2 = f.p(A, B, z0), e3 = f.p(-A, B, z0), r0 = f.p(-rl, 0, z1), r1 = f.p(rl, 0, z1);
    s.quad(e0, e1, r1, r0, rgb(b.hip.color, 0.92)); s.quad(e2, e3, r0, r1, rgb(b.hip.color, 0.86));
    s.tri(e1, e2, r1, cH); s.tri(e3, e0, r0, rgb(b.hip.color, 0.8));
    s.quad(e3, e2, e1, e0, cU);   // the soffit under the eaves
  }
  if (b.deck_rail) {
    const cR = rgb('#5d6166'), zr = b.h + 1.0;
    s.box(f, -hl, hl, -hw, -hw + 0.06, zr - 0.05, zr, cR); s.box(f, -hl, hl, hw - 0.06, hw, zr - 0.05, zr, cR);
    s.box(f, -hl, -hl + 0.06, -hw, hw, zr - 0.05, zr, cR); s.box(f, hl - 0.06, hl, -hw, hw, zr - 0.05, zr, cR);
    for (let t = -hl; t <= hl + 1e-6; t += 1.5) { s.box(f, t - 0.03, t + 0.03, -hw, -hw + 0.06, b.h, zr, cR); s.box(f, t - 0.03, t + 0.03, hw - 0.06, hw, b.h, zr, cR); }
  }
  if (b.balcony) balcony(b, s, f);
}

function balcony(b: BlockJson, s: Soup, f: Frame): void {
  const B = b.balcony!; const hl = b.l / 2, hw = b.w / 2, sd = B.side >= 0 ? 1 : -1;
  const d0 = sd > 0 ? hw : -hw - B.depth, d1 = sd > 0 ? hw + B.depth : -hw;
  const cB = rgb(B.color ?? b.wall), cR = rgb('#5d6166');
  s.box(f, -hl, hl, d0, d1, B.z - 0.18, B.z, cB, { bottom: true });                                   // the floor slab
  const dr0 = sd > 0 ? d1 - 0.06 : d0, dr1 = sd > 0 ? d1 : d0 + 0.06;
  s.box(f, -hl, hl, dr0, dr1, B.z + 0.95, B.z + 1.0, cR);                                             // hand rail
  for (let t = -hl; t <= hl + 1e-6; t += 1.5) s.box(f, t - 0.03, t + 0.03, dr0, dr1, B.z, B.z + 1.0, cR);   // balusters
  if (B.stair) {
    // a straight flight up the +l end, outside the balcony's line, ground to the floor
    const n = Math.max(4, Math.round(B.z / 0.18)), run = B.z / 0.75;
    for (let k = 0; k < n; k++) {
      const t0 = hl + 0.2 + run - (k + 1) * (run / n), z = (k + 1) * (B.z / n);
      s.box(f, t0, t0 + run / n, d0, d1, z - 0.06, z, cB);
    }
  }
}

export function fuel(u: FuelJson, s: Soup): void {
  const f = Frame.heading(u.c, u.z, u.heading);
  const hl = u.l / 2, hw = u.w / 2;
  const cC = rgb(u.canopy), cF = rgb(u.fascia_color), cPost = rgb('#c9c7c0'), cIs = rgb('#b9b6ae'), cPump = rgb('#dcdad3');
  s.box(f, -hl, hl, -hw, hw, u.h, u.h + u.fascia, cF, { top: cC, bottom: true });
  if (u.hip) {
    const z0 = u.h + u.fascia, z1 = z0 + u.hip, r = Math.max(0, hl - hw), k = rgb(u.hip_color ?? u.canopy);
    s.quad(f.p(-hl, -hw, z0), f.p(hl, -hw, z0), f.p(r, 0, z1), f.p(-r, 0, z1), k);
    s.quad(f.p(hl, hw, z0), f.p(-hl, hw, z0), f.p(-r, 0, z1), f.p(r, 0, z1), rgb(u.hip_color ?? u.canopy, 0.88));
    s.tri(f.p(-hl, hw, z0), f.p(-hl, -hw, z0), f.p(-r, 0, z1), rgb(u.hip_color ?? u.canopy, 0.94));
    s.tri(f.p(hl, -hw, z0), f.p(hl, hw, z0), f.p(r, 0, z1), rgb(u.hip_color ?? u.canopy, 0.94));
  }
  const n = Math.max(1, u.posts);
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0 : -hl + 1 + ((u.l - 2) * i) / (n - 1);
    // edge_posts (Buttonwillow's open shade roof, judge r6): thin posts along both long edges instead of the centre line,
    // so the roof reads as open on posts from the lane
    if (u.edge_posts) for (const d of [-hw + 0.3, hw - 0.3]) s.box(f, t - 0.08, t + 0.08, d - 0.08, d + 0.08, -0.3, u.h, cPost, { top: null });
    else s.box(f, t - 0.2, t + 0.2, -0.2, 0.2, -0.3, u.h, cPost, { top: null });
  }
  for (let k = 0; k < u.islands; k++) {
    const d = u.islands === 1 ? 0 : -hw + 1.5 + ((u.w - 3) * k) / (u.islands - 1);
    s.box(f, -hl + 1, hl - 1, d - 0.6, d + 0.6, -0.3, 0.2, cIs);
    for (const t of [-hl / 2, hl / 2]) s.box(f, t - 0.35, t + 0.35, d - 0.25, d + 0.25, 0.2, 1.8, cPump);
  }
  if (u.pylon) {
    const P = u.pylon;
    const pf = new Frame(f.p(P.at[0], P.at[1], 0), f.ut, f.ud);
    s.box(pf, -0.3, 0.3, -0.3, 0.3, -0.3, P.h * 0.45, cPost, { top: null });
    s.box(pf, -P.w / 2, P.w / 2, -0.35, 0.35, P.h * 0.45, P.h, rgb(P.color));
    s.box(pf, -P.w / 2 + 0.25, P.w / 2 - 0.25, -0.4, 0.4, P.h * 0.62, P.h - 0.35, rgb(P.panel), { top: null, shade: false });
  }
}

// ------------------------------------------------------------------ fences, masts, paint, boards
export function fence(u: FenceJson, s: Soup, fabric: Soup): void {
  const cP = rgb(u.color ?? '#8c9196');
  const step = u.post_m ?? 3;
  let acc = 0;
  for (let i = 0; i < u.pts.length; i++) {
    const p = u.pts[i];
    if (i > 0) acc += Math.hypot(p[0] - u.pts[i - 1][0], p[1] - u.pts[i - 1][1]);
    if (i === 0 || i === u.pts.length - 1 || acc >= step) {
      acc = 0;
      const f = new Frame(p, [1, 0], [0, 1]);
      s.box(f, -0.03, 0.03, -0.03, 0.03, -0.2, u.h, cP, { top: null, shade: false });
    }
  }
  // top rail and the fabric
  for (let i = 0; i + 1 < u.pts.length; i++) {
    const a = u.pts[i], b = u.pts[i + 1];
    s.quad([a[0], a[1], a[2] + u.h - 0.05], [b[0], b[1], b[2] + u.h - 0.05], [b[0], b[1], b[2] + u.h], [a[0], a[1], a[2] + u.h], cP);
  }
  fabric.ribbon(u.pts, 0, u.h, rgb('#d7dadc'), 0.3);
}

function mastAt(s: Soup, p: V3, h: number, heads: [number, number], face: number, color: string): void {
  const f = Frame.heading([p[0], p[1]], p[2], face);   // t toward the lamps' facing
  const c = rgb(color), lamp = rgb('#f4f1e2'), frame = rgb('#5d6166');
  // tapered square pole
  const r0 = 0.22, r1 = 0.12;
  const q = (r: number, z: number): V3[] => [f.p(-r, -r, z), f.p(r, -r, z), f.p(r, r, z), f.p(-r, r, z)];
  const A = q(r0, -0.3), B = q(r1, h - 0.4);
  for (let i = 0; i < 4; i++) s.quad(A[i], A[(i + 1) % 4], B[(i + 1) % 4], B[i], i % 2 ? c : rgb(color, 0.85));
  // head: a frame with cols x rows lamps facing +t
  const [nc, nr] = heads, lw = 0.55, W = nc * lw, H = nr * lw;
  s.box(f, -0.15, 0.15, -W / 2, W / 2, h - 0.4, h - 0.4 + H, frame);
  for (let i = 0; i < nc; i++) for (let j = 0; j < nr; j++) {
    const d0 = -W / 2 + i * lw + 0.05, z0 = h - 0.4 + j * lw + 0.05;
    s.quad(f.p(0.16, d0, z0), f.p(0.16, d0 + lw - 0.1, z0), f.p(0.16, d0 + lw - 0.1, z0 + lw - 0.1), f.p(0.16, d0, z0 + lw - 0.1), lamp);
  }
}

export function masts(u: MastJson, s: Soup): void {
  for (const [x, y, z, hd] of u.at) mastAt(s, [x, y, z], u.h, u.heads, hd, u.color ?? '#9ea3a8');
}

export function paint(u: PaintJson, s: Soup, ground?: (x: number, y: number) => number): void {
  const c = rgb(u.color);
  u.rects.forEach(([cx, cy, hd, l, w], i) => {
    const f = Frame.heading([cx, cy], 0, hd);
    const P = [f.p(-l / 2, -w / 2, 0), f.p(l / 2, -w / 2, 0), f.p(l / 2, w / 2, 0), f.p(-l / 2, w / 2, 0)];
    const zc = u.z?.[i] ?? 0;
    for (const p of P) p[2] = (ground ? ground(p[0], p[1]) : zc) + 0.02;
    s.quad(P[0], P[1], P[2], P[3], c);
  });
}

/** The panels of a boards run: frame at the panel's start, length, the z offset over it, and its name entry. */
export function scoringTower(u: ScoringTowerJson, s: Soup): void {
  const f = Frame.heading(u.c, u.z, (u.heading_deg * Math.PI) / 180);
  const pl = u.plinth;
  const z0 = pl ? pl.h : 0;
  if (pl) s.box(f, -pl.w / 2, pl.w / 2, -pl.w / 2, pl.w / 2, -0.5, pl.h, rgb(pl.color));
  const hd = u.head;
  const zc = hd ? u.h - hd.h : u.h;
  s.box(f, -u.w / 2, u.w / 2, -u.d / 2, u.d / 2, z0, zc, rgb(u.color));
  if (hd) s.box(f, -hd.w / 2, hd.w / 2, -hd.d / 2, hd.d / 2, zc, u.h, rgb(hd.color));
}

export function canopy(u: CanopyJson, s: Soup): void {
  const N = 32, R = u.d / 2, r = (u.hole ?? 0) / 2, th = 0.25;
  const tb = ((u.tilt_bearing ?? 0) * Math.PI) / 180, slope = Math.tan(((u.tilt_deg ?? 0) * Math.PI) / 180);
  const dir: V2 = [Math.sin(tb), Math.cos(tb)];   // bearing -> ENU unit vector
  const z0 = u.deck ? u.deck.h : 0;
  const at = (rad: number, a: number, dz = 0): V3 => {
    const x = rad * Math.cos(a), y = rad * Math.sin(a);
    return [u.c[0] + x, u.c[1] + y, u.z + u.h + slope * (x * dir[0] + y * dir[1]) + dz];
  };
  const cRoof = rgb(u.color), cUnder = rgb(u.color, 0.7), cPost = rgb(u.post_color ?? '#9aa0a6');
  for (let i = 0; i < N; i++) {
    const a0 = (i / N) * 2 * Math.PI, a1 = ((i + 1) / N) * 2 * Math.PI;
    s.quad(at(r, a0), at(R, a0), at(R, a1), at(r, a1), cRoof);                       // top
    s.quad(at(r, a1, -th), at(R, a1, -th), at(R, a0, -th), at(r, a0, -th), cUnder);  // underside
    s.quad(at(R, a0, -th), at(R, a1, -th), at(R, a1), at(R, a0), cRoof);             // rim
    if (r > 0) s.quad(at(r, a1, -th), at(r, a0, -th), at(r, a0), at(r, a1), cUnder);
    if (u.deck) {
      const D = u.deck.d / 2, cD = rgb(u.deck.color);
      const g = (rad: number, a: number, z: number): V3 => [u.c[0] + rad * Math.cos(a), u.c[1] + rad * Math.sin(a), u.z + z];
      if (u.deck_posts) {
        // round 10: a 0.3 m slab on posts, open beneath (edge band, floor, soffit)
        const zt = u.deck.h, zb = u.deck.h - 0.3;
        s.quad(g(D, a0, zb), g(D, a1, zb), g(D, a1, zt), g(D, a0, zt), rgb(u.deck.color, 0.86));
        s.tri(g(0, 0, zt), g(D, a0, zt), g(D, a1, zt), cD);
        s.tri(g(0, 0, zb), g(D, a1, zb), g(D, a0, zb), rgb(u.deck.color, 0.6));
        // a rail round the terrace edge, 1.0 m
        s.quad(g(D - 0.05, a0, zt + 0.95), g(D - 0.05, a1, zt + 0.95), g(D - 0.05, a1, zt + 1.0), g(D - 0.05, a0, zt + 1.0), rgb(u.post_color ?? '#9aa0a6'));
      } else {
        s.quad(g(D, a0, -0.5), g(D, a1, -0.5), g(D, a1, u.deck.h), g(D, a0, u.deck.h), rgb(u.deck.color, 0.86));   // terrace wall
        s.tri(g(0, 0, u.deck.h), g(D, a0, u.deck.h), g(D, a1, u.deck.h), cD);                                       // terrace floor
      }
    }
  }
  // centre column and a ring of posts from the terrace up to the roof's underside
  const col = (x: number, y: number, w: number) => {
    const zt = u.h + slope * (x * dir[0] + y * dir[1]) - th;
    s.box(Frame.heading([u.c[0] + x, u.c[1] + y], u.z, 0), -w / 2, w / 2, -w / 2, w / 2, z0, zt, cPost, { top: null });
  };
  if (r > 0) {
    for (let k = 0; k < (u.posts ?? 6); k++) { const a = (k / (u.posts ?? 6)) * 2 * Math.PI; col(r * Math.cos(a), r * Math.sin(a), 0.25); }
  } else col(0, 0, 0.5);
  for (let k = 0; k < (u.posts ?? 6); k++) { const a = (k / (u.posts ?? 6)) * 2 * Math.PI + 0.3; col(R * 0.8 * Math.cos(a), R * 0.8 * Math.sin(a), 0.16); }
  if (u.deck && u.deck_posts) {
    // round 10: the terrace's posts, ground to the slab's underside, on a ring at 0.85 of its radius and at the centre
    const zb = u.deck.h - 0.3, pc = rgb(u.post_color ?? '#9aa0a6'), Dd = u.deck.d / 2;
    const leg = (x: number, y: number) => s.box(Frame.heading([u.c[0] + x, u.c[1] + y], u.z, 0), -0.15, 0.15, -0.15, 0.15, -0.3, zb, pc, { top: null });
    leg(0, 0);
    for (let k = 0; k < u.deck_posts; k++) { const a = (k / u.deck_posts) * 2 * Math.PI; leg(Dd * 0.85 * Math.cos(a), Dd * 0.85 * Math.sin(a)); }
  }
  if (u.deck && u.stair) {
    // round 10: a straight flight of solid steps from the terrace edge to the ground
    const b = (u.stair.bearing_deg * Math.PI) / 180, dir: V2 = [Math.sin(b), Math.cos(b)], right: V2 = [dir[1], -dir[0]];
    const lat = u.stair.lateral ?? 0, Dd = u.deck.d / 2;
    const off = Math.sqrt(Math.max(0, Dd * Dd - lat * lat));   // where the flight's centre line meets the terrace edge
    const o: V2 = [u.c[0] + dir[0] * off + right[0] * lat, u.c[1] + dir[1] * off + right[1] * lat];
    const f = new Frame([o[0], o[1], u.z], dir, [-dir[1], dir[0]]);
    const n = Math.max(2, Math.round(u.deck.h / 0.18)), tr = u.stair.run / n, ck = rgb(u.stair.color ?? u.deck.color, 0.9);
    for (let i = 0; i < n; i++) s.box(f, i * tr, (i + 1) * tr, -u.stair.w / 2, u.stair.w / 2, -0.3, u.deck.h * (1 - i / n), ck);
  }
}

export function boardPanels(u: BoardsJson): { f: Frame; l: number; dz: number; k: number }[] {
  const out: { f: Frame; l: number; dz: number; k: number }[] = [];
  let k = 0;
  for (let i = 0; i + 1 < u.pts.length; i++) {
    const a = u.pts[i], b = u.pts[i + 1];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (len < 1e-3) continue;
    const n = Math.max(1, Math.round(len / u.panel));
    for (let j = 0; j < n; j++) {
      const f0 = j / n, f1 = (j + 1) / n;
      const p0: V3 = [a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0, a[2] + (b[2] - a[2]) * f0];
      const p1: V3 = [a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1, a[2] + (b[2] - a[2]) * f1];
      const ut: V2 = [(b[0] - a[0]) / len, (b[1] - a[1]) / len];
      out.push({ f: new Frame(p0, ut, [-ut[1], ut[0]]), l: Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) - 0.06, dz: p1[2] - p0[2], k: k++ });
    }
  }
  return out;
}

export function boards(u: BoardsJson, s: Soup): void {
  // walk the line, one panel per `panel` metres, colours (or the names' backgrounds) in order
  for (const { f, l, dz, k } of boardPanels(u)) {
    const col = u.names?.length ? u.names[k % u.names.length][1] : u.colors[k % u.colors.length];
    s.box(f, 0.03, 0.03 + l, -0.03, 0.03, u.z0 + Math.min(0, dz), u.z0 + u.h + Math.max(0, dz), rgb(col), { shade: false });
  }
}

// ------------------------------------------------------------------ terrace dressing
/** With `ground` (the drawn terrain), each bench piece (at most 8 m) sits on the higher of its row height and the
 *  terrain under it, so the rows read on a hillside whose ground varies along a row (the treads are flat per row). */
export function terraceDress(u: TerraceDressJson, t: TerraceJson, s: Soup, ground?: (x: number, y: number) => number): void {
  if (t.rows.some((r) => r.pts?.length)) { terraceDressPolyline(u, t, s, ground); return; }
  const [ux, uy] = t.dir, h = t.run / 2;
  const rows = t.rows;
  if (!rows.length) return;
  // aisle centres as fractions of each row (the rows are cut by the outline, so aisles are placed by fraction of the
  // middle row's length, then mapped onto each row by distance from its own `a` end along the common direction)
  const mid = rows[Math.floor(rows.length / 2)];
  const vx = mid.b[0] - mid.a[0], vy = mid.b[1] - mid.a[1], vl = Math.hypot(vx, vy) || 1;
  const vu: V2 = [vx / vl, vy / vl];
  const proj = (p: V2) => (p[0] - mid.a[0]) * vu[0] + (p[1] - mid.a[1]) * vu[1];
  const A = u.aisles;
  const aisleAt: number[] = [];
  if (A) {
    const lo = Math.min(...rows.map((r) => Math.min(proj(r.a), proj(r.b)))), hi = Math.max(...rows.map((r) => Math.max(proj(r.a), proj(r.b))));
    for (let x = lo + A.pitch / 2; x < hi; x += A.pitch) aisleAt.push(x);
  }
  const cBench = rgb(u.bench?.color ?? '#c9c6bd'), cBenchF = rgb(u.bench?.color ?? '#c9c6bd', 0.55);
  const cAisle = rgb(A?.color ?? '#c2c0b9'), cRail = rgb(A?.rail ?? '#7d8186');
  const at = (r: { a: V2; b: V2 }, x: number): V2 => {
    const pa = proj(r.a), pb = proj(r.b), fr = (x - pa) / (pb - pa || 1);
    return [r.a[0] + (r.b[0] - r.a[0]) * fr, r.a[1] + (r.b[1] - r.a[1]) * fr];
  };
  rows.forEach((r, i) => {
    const pa = proj(r.a), pb = proj(r.b), x0 = Math.min(pa, pb), x1 = Math.max(pa, pb);
    if (x1 - x0 < 1) return;
    // bench segments between aisles
    const cuts: [number, number][] = [];
    let c0 = x0;
    if (A) for (const x of aisleAt) { if (x - A.w / 2 > c0 && x + A.w / 2 < x1) { cuts.push([c0, x - A.w / 2]); c0 = x + A.w / 2; } }
    cuts.push([c0, x1]);
    if (u.bench) {
      const B = u.bench;
      for (const [q0, q1] of cuts) {
        if (q1 - q0 < 0.5) continue;
        const db0 = h - B.depth - 0.05, db1 = h - 0.05;
        const P = (p: V2, d: number, z: number): V3 => [p[0] + ux * d, p[1] + uy * d, z];
        const n = Math.max(1, Math.ceil((q1 - q0) / 8));
        for (let k = 0; k < n; k++) {
          const p0 = at(r, q0 + ((q1 - q0) * k) / n), p1 = at(r, q0 + ((q1 - q0) * (k + 1)) / n);
          const zb = ground ? Math.max(r.z, ground(p0[0] + ux * h, p0[1] + uy * h), ground(p1[0] + ux * h, p1[1] + uy * h), ground((p0[0] + p1[0]) / 2 + ux * h, (p0[1] + p1[1]) / 2 + uy * h)) : r.z;
          // bench strip on the back part of the tread: a top and a darker front face
          s.quad(P(p0, db0, zb + B.h), P(p1, db0, zb + B.h), P(p1, db1, zb + B.h), P(p0, db1, zb + B.h), cBench);
          s.quad(P(p0, db0, zb), P(p1, db0, zb), P(p1, db0, zb + B.h), P(p0, db0, zb + B.h), cBenchF);
        }
      }
    }
    if (A) for (const x of aisleAt) {
      if (x - A.w / 2 <= x0 || x + A.w / 2 >= x1) continue;
      const p0 = at(r, x - A.w / 2), p1 = at(r, x + A.w / 2);
      const zl = i === 0 ? t.z_ground_front : rows[i - 1].z, zm = (zl + r.z) / 2;
      const P = (p: V2, d: number, z: number): V3 => [p[0] + ux * d, p[1] + uy * d, z + 0.01];
      // two steps per row in a lighter concrete
      s.quad(P(p0, -h, zm), P(p1, -h, zm), P(p1, 0, zm), P(p0, 0, zm), cAisle);
      s.quad(P(p0, 0, zm), P(p1, 0, zm), P(p1, 0, r.z), P(p0, 0, r.z), rgb(A.color, 0.85));
      s.quad(P(p0, 0, r.z), P(p1, 0, r.z), P(p1, h, r.z), P(p0, h, r.z), cAisle);
      // hand rail down the aisle centre: a bar from this row to the next
      if (i + 1 < rows.length) {
        const c = at(r, x), cn = at(rows[i + 1], x);
        const a3: V3 = [c[0], c[1], r.z + 0.9], b3: V3 = [cn[0] + ux * 0, cn[1] + uy * 0, rows[i + 1].z + 0.9];
        s.quad([a3[0], a3[1], a3[2] - 0.05], [b3[0], b3[1], b3[2] - 0.05], b3, a3, cRail);
        if (i % 3 === 0) s.quad([c[0] - 0.03 * uy, c[1] + 0.03 * ux, r.z], [c[0] + 0.03 * uy, c[1] - 0.03 * ux, r.z], [c[0] + 0.03 * uy, c[1] - 0.03 * ux, r.z + 0.9], [c[0] - 0.03 * uy, c[1] + 0.03 * ux, r.z + 0.9], cRail);
      }
    }
  });
  for (const sh of u.shades ?? []) {
    const top = rows.slice(-sh.rows);
    if (!top.length) continue;
    const r0 = top[0], r1 = top[top.length - 1];
    const span = (r: { a: V2; b: V2 }): [V2, V2] => {
      const pa = proj(r.a), pb = proj(r.b), x0 = Math.min(pa, pb), x1 = Math.max(pa, pb);
      return [at(r, x0 + (x1 - x0) * sh.f0), at(r, x0 + (x1 - x0) * sh.f1)];
    };
    const [a0, b0] = span(r0), [a1, b1] = span(r1);
    const z0 = r0.z + sh.h, z1 = r1.z + sh.h;
    const c = rgb(sh.color);
    s.quad([a0[0] - ux * h, a0[1] - uy * h, z0], [b0[0] - ux * h, b0[1] - uy * h, z0], [b1[0] + ux * h, b1[1] + uy * h, z1 + 0.6], [a1[0] + ux * h, a1[1] + uy * h, z1 + 0.6], c);
    // posts at the corners and every ~8 m along the back
    const back = Math.max(2, Math.round(Math.hypot(b1[0] - a1[0], b1[1] - a1[1]) / 8));
    for (let k = 0; k <= back; k++) {
      const fx = k / back;
      for (const [p, z, d] of [[[a0[0] + (b0[0] - a0[0]) * fx, a0[1] + (b0[1] - a0[1]) * fx] as V2, r0.z, -h], [[a1[0] + (b1[0] - a1[0]) * fx, a1[1] + (b1[1] - a1[1]) * fx] as V2, r1.z, h]] as [V2, number, number][]) {
        const zt = z === r0.z ? z0 : z1 + 0.6;
        const fr = new Frame([p[0] + ux * d * 0.9, p[1] + uy * d * 0.9, z], [ux, uy], [-uy, ux]);
        s.box(fr, -0.08, 0.08, -0.08, 0.08, 0, zt - z, rgb('#8c9196'), { top: null, shade: false });
      }
    }
  }
}

/** A point on a polyline row at metres `m` along the front line: position, tread height, the row below's height and the
 *  uphill normal (linear between vertices); null outside the row. */
function rowAt(r: TerraceRow, m: number): { p: V2; z: number; zl: number; n: V2 } | null {
  const P = r.pts!, N = r.nrm!;
  if (m < P[0][4] - 1e-6 || m > P[P.length - 1][4] + 1e-6) return null;
  let i = 0;
  while (i < P.length - 2 && P[i + 1][4] < m) i++;
  const a = P[i], b = P[i + 1], f = Math.min(1, Math.max(0, (m - a[4]) / (b[4] - a[4] || 1)));
  const nx = N[i][0] + (N[i + 1][0] - N[i][0]) * f, ny = N[i][1] + (N[i + 1][1] - N[i][1]) * f, nl = Math.hypot(nx, ny) || 1;
  return { p: [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f], z: a[2] + (b[2] - a[2]) * f, zl: a[3] + (b[3] - a[3]) * f, n: [nx / nl, ny / nl] };
}

/** Dressing of a terrace whose rows follow the stand (polyline rows): bench pieces between the aisles on every row (each
 *  on the higher of the tread and the drawn terrain), aisle steps and hand rails at fixed metres along the front line, and
 *  shade roofs over the top `rows` rows between fractions f0..f1 of the front line. */
function terraceDressPolyline(u: TerraceDressJson, t: TerraceJson, s: Soup, ground?: (x: number, y: number) => number): void {
  const h = t.run / 2;
  const rows = t.rows.filter((r) => r.pts && r.pts.length >= 2);
  if (!rows.length) return;
  const mlo = Math.min(...rows.map((r) => r.pts![0][4])), mhi = Math.max(...rows.map((r) => r.pts![r.pts!.length - 1][4]));
  const A = u.aisles;
  const aisleAt: number[] = [];
  if (A) for (let x = mlo + A.pitch / 2; x < mhi; x += A.pitch) aisleAt.push(x);
  // the bench's front face in shadow (0.35 of its colour): the dark line per row that reads as rows from the track
  const cBench = rgb(u.bench?.color ?? '#c9c6bd'), cBenchF = rgb(u.bench?.color ?? '#c9c6bd', 0.35);
  const cAisle = rgb(A?.color ?? '#c2c0b9'), cRail = rgb(A?.rail ?? '#7d8186');
  const P3 = (q: { p: V2; n: V2 }, d: number, z: number): V3 => [q.p[0] + q.n[0] * d, q.p[1] + q.n[1] * d, z];
  const byK = new Map<number, TerraceRow[]>();
  for (const r of rows) { const k = r.k ?? 0; if (!byK.has(k)) byK.set(k, []); byK.get(k)!.push(r); }
  for (const r of rows) {
    const m0 = r.pts![0][4], m1 = r.pts![r.pts!.length - 1][4];
    if (m1 - m0 < 1) continue;
    const cuts: [number, number][] = [];
    let c0 = m0;
    if (A) for (const x of aisleAt) { if (x - A.w / 2 > c0 && x + A.w / 2 < m1) { cuts.push([c0, x - A.w / 2]); c0 = x + A.w / 2; } }
    cuts.push([c0, m1]);
    if (u.bench) {
      const B = u.bench, db0 = h - B.depth - 0.05, db1 = h - 0.05;
      for (const [q0, q1] of cuts) {
        if (q1 - q0 < 0.5) continue;
        // pieces of at most 4 m (the rows bend), each on the higher of its tread and the terrain under its back edge
        const n = Math.max(1, Math.ceil((q1 - q0) / 4));
        for (let k = 0; k < n; k++) {
          const a = rowAt(r, q0 + ((q1 - q0) * k) / n), b = rowAt(r, q0 + ((q1 - q0) * (k + 1)) / n);
          if (!a || !b) continue;
          const gz = ground ? Math.max(ground(a.p[0] + a.n[0] * h, a.p[1] + a.n[1] * h), ground(b.p[0] + b.n[0] * h, b.p[1] + b.n[1] * h)) : -Infinity;
          const za = Math.max(a.z, gz), zb = Math.max(b.z, gz);
          s.quad(P3(a, db0, za + B.h), P3(b, db0, zb + B.h), P3(b, db1, zb + B.h), P3(a, db1, za + B.h), cBench);
          s.quad(P3(a, db0, za), P3(b, db0, zb), P3(b, db0, zb + B.h), P3(a, db0, za + B.h), cBenchF);
        }
      }
    }
    if (A) for (const x of aisleAt) {
      if (x - A.w / 2 <= m0 || x + A.w / 2 >= m1) continue;
      const a = rowAt(r, x - A.w / 2)!, b = rowAt(r, x + A.w / 2)!, c = rowAt(r, x)!;
      const zm = (c.zl + c.z) / 2;
      const Q = (q: { p: V2; n: V2 }, d: number, z: number): V3 => P3(q, d, z + 0.01);
      s.quad(Q(a, -h, zm), Q(b, -h, zm), Q(b, 0, zm), Q(a, 0, zm), cAisle);
      s.quad(Q(a, 0, zm), Q(b, 0, zm), Q(b, 0, c.z), Q(a, 0, c.z), rgb(A.color, 0.85));
      s.quad(Q(a, 0, c.z), Q(b, 0, c.z), Q(b, h, c.z), Q(a, h, c.z), cAisle);
      const nx = (byK.get((r.k ?? 0) + 1) ?? []).map((q) => rowAt(q, x)).find((q) => q);
      if (nx) {
        const a3: V3 = [c.p[0], c.p[1], c.z + 0.9], b3: V3 = [nx.p[0], nx.p[1], nx.z + 0.9];
        s.quad([a3[0], a3[1], a3[2] - 0.05], [b3[0], b3[1], b3[2] - 0.05], b3, a3, cRail);
        if ((r.k ?? 0) % 3 === 0) s.quad([c.p[0] - 0.03 * c.n[1], c.p[1] + 0.03 * c.n[0], c.z], [c.p[0] + 0.03 * c.n[1], c.p[1] - 0.03 * c.n[0], c.z], [c.p[0] + 0.03 * c.n[1], c.p[1] - 0.03 * c.n[0], c.z + 0.9], [c.p[0] - 0.03 * c.n[1], c.p[1] + 0.03 * c.n[0], c.z + 0.9], cRail);
      }
    }
  }
  // shade roofs: at each metre mark across f0..f1, from the front of the row `rows - 1` below the top row there to the
  // back of the top row, `h` over the treads (0.6 m more at the back), posts every ~8 m
  const kmax = (m: number) => { let best: { k: number; q: ReturnType<typeof rowAt> } | null = null; for (const r of rows) { const q = rowAt(r, m); if (q && (!best || (r.k ?? 0) > best.k)) best = { k: r.k ?? 0, q }; } return best; };
  for (const sh of u.shades ?? []) {
    const a0 = mlo + (mhi - mlo) * sh.f0, a1 = mlo + (mhi - mlo) * sh.f1;
    const n = Math.max(1, Math.ceil((a1 - a0) / 4));
    const col = rgb(sh.color), post = rgb('#8c9196');
    let prev: [V3, V3] | null = null;
    for (let k = 0; k <= n; k++) {
      const m = a0 + ((a1 - a0) * k) / n, top = kmax(m);
      if (!top || !top.q) { prev = null; continue; }
      const lowK = Math.max(0, top.k - sh.rows + 1);
      const low = (byK.get(lowK) ?? []).map((q) => rowAt(q, m)).find((q) => q) ?? top.q;
      const f: V3 = P3(low, -h, low.z + sh.h), b: V3 = P3(top.q, h, top.q.z + sh.h + 0.6);
      if (prev) s.quad(prev[0], f, b, prev[1], col);
      if (k === 0 || k === n || k % 2 === 0) for (const [q, z, d] of [[low, low.z, -h * 0.9], [top.q, top.q.z, h * 0.9]] as [{ p: V2; n: V2 }, number, number][]) {
        const fr = new Frame(P3(q, d, z), [q.n[0], q.n[1]], [-q.n[1], q.n[0]]);
        s.box(fr, -0.08, 0.08, -0.08, 0.08, 0, (q === low ? f[2] : b[2]) - z, post, { top: null, shade: false });
      }
      prev = [f, b];
    }
  }
}

// ------------------------------------------------------------------ assembly
/** Share of a hillside terrace's own colour added unlit (round 6): concrete lit by the sky as well as the sun, so the
 *  step faces and benches turned away from the sun stay grey with the row contrast intact, not black (the onboard's stands
 *  read light grey with darker row lines whatever the sun's side). */
export const TERRACE_SELF_LIT = 0.45;
export function selfLitMaterial(k: number): THREE.MeshLambertMaterial {
  const mat = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
  mat.onBeforeCompile = (sh) => {
    sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>',
      `#include <emissivemap_fragment>\n  totalEmissiveRadiance += ${k.toFixed(2)} * vColor.rgb;`);
  };
  mat.customProgramCacheKey = () => `selflit${k}`;
  return mat;
}

/** `terrace`: the terrace dressing, drawn with the terraces' part-self-lit concrete (scenery.ts) so benches and aisles keep
 *  their grey on a stand the sun lights from behind (round 6) */
export interface StructureSoups { solid: Soup; paint: Soup; fabric: Soup; terrace: Soup; perType: Record<string, number> }

/** All structures as four triangle soups (pure; deterministic for the same input). */
export function structureSoups(list: StructureJson[], terraces: TerraceJson[] = [], ground?: (x: number, y: number) => number): StructureSoups {
  const solid = new Soup(), pnt = new Soup(), fabric = new Soup(), terr = new Soup();
  const perType: Record<string, number> = {};
  for (const u of list) {
    const before = solid.tris + pnt.tris + fabric.tris + terr.tris;
    switch (u.type) {
      // Mid-Ohio round 7 (the T4 bleachers rendered dark: their rows face away from the sun, plain Lambert): `self_lit`
      // draws a stand with the terraces' part-self-lit concrete; absent: the solid soup as before
      case 'grandstand': grandstand(u, u.self_lit ? terr : solid); break;
      case 'garage': garage(u, solid); break;
      case 'block': block(u, solid); break;
      case 'fuel': fuel(u, solid); break;
      case 'fence': fence(u, solid, fabric); break;
      case 'mast': masts(u, solid); break;
      case 'paint': paint(u, pnt, ground); break;
      case 'boards': boards(u, solid); break;
      case 'scoring_tower': scoringTower(u, solid); break;
      case 'canopy': canopy(u, solid); break;
      case 'terrace_dress': { const t = terraces.find((x) => x.name === u.terrace); if (t) terraceDress(u, t, terr, ground); break; }
      default: break;
    }
    perType[u.type] = (perType[u.type] ?? 0) + solid.tris + pnt.tris + fabric.tris + terr.tris - before;
  }
  return { solid, paint: pnt, fabric, terrace: terr, perType };
}

function toGeometry(s: Soup): THREE.BufferGeometry {
  const P = new Float32Array(s.pos.length);
  for (let i = 0; i < s.pos.length; i += 3) { P[i] = s.pos[i]; P[i + 1] = s.pos[i + 2]; P[i + 2] = -s.pos[i + 1]; }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(P, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(s.col, 3));
  g.computeVertexNormals();
  g.computeBoundingSphere();
  return g;
}

function fabricTexture(): THREE.Texture | null {
  if (typeof document === 'undefined') return null;
  const cv = document.createElement('canvas');
  cv.width = cv.height = 32;
  const g = cv.getContext('2d');
  if (!g) return null;
  g.strokeStyle = 'rgba(210,212,214,1)'; g.lineWidth = 1.4;
  g.beginPath(); g.moveTo(0, 0); g.lineTo(32, 32); g.moveTo(32, 0); g.lineTo(0, 32); g.stroke();
  const t = new THREE.CanvasTexture(cv);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

/** The structures as three meshes (solid, ground paint, fence fabric). */
/** `label`: a texture of one typed board name (scenery.ts bannerTexture): boards runs with `names` get their name on
 *  both faces of every panel. */
export type BoardLabel = (text: string, bg: string, fg: string, w: number, h: number) => THREE.Texture;
export function buildStructures(list: StructureJson[], terraces: TerraceJson[] = [], ground?: (x: number, y: number) => number, label?: BoardLabel): THREE.Group {
  const grp = new THREE.Group();
  grp.name = 'structures';
  const S = structureSoups(list, terraces, ground);
  if (label) {
    const mats = new Map<string, THREE.MeshLambertMaterial>();
    for (const u of list) {
      if (u.type !== 'boards' || !u.names?.length) continue;
      for (const { f, l, dz, k } of boardPanels(u)) {
        const [text, bg, fg] = u.names[k % u.names.length];
        const key = `${text}|${bg}|${fg}|${l.toFixed(1)}|${u.h}`;
        if (!mats.has(key)) mats.set(key, new THREE.MeshLambertMaterial({ map: label(text, bg, fg, l, u.h) }));
        for (const side of [1, -1]) {
          const c = f.p(0.03 + l / 2, side * 0.036, u.z0 + u.h / 2 + dz / 2);
          const pl = new THREE.Mesh(new THREE.PlaneGeometry(l, u.h), mats.get(key)!);
          pl.position.set(c[0], c[2], -c[1]);
          // the plane's +Z normal along the panel's side normal (ENU d axis); three's yaw from ENU heading
          const nx = f.ud[0] * side, ny = f.ud[1] * side;
          pl.rotation.y = Math.atan2(nx, -ny);
          grp.add(pl);
        }
      }
    }
  }
  if (S.solid.tris) {
    const m = new THREE.Mesh(toGeometry(S.solid), new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }));
    m.name = 'structures_solid';
    grp.add(m);
  }
  if (S.terrace.tris) {
    const m = new THREE.Mesh(toGeometry(S.terrace), selfLitMaterial(TERRACE_SELF_LIT));
    m.name = 'structures_terrace';
    grp.add(m);
  }
  if (S.paint.tris) {
    const m = new THREE.Mesh(toGeometry(S.paint), new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -10 }));
    m.name = 'structures_paint';
    grp.add(m);
  }
  if (S.fabric.tris) {
    const g = toGeometry(S.fabric);
    g.setAttribute('uv', new THREE.Float32BufferAttribute(S.fabric.uv, 2));
    const tex = fabricTexture();
    const m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ vertexColors: true, ...(tex ? { map: tex } : {}), transparent: true, opacity: tex ? 0.5 : 0.25, side: THREE.DoubleSide, depthWrite: false }));
    m.name = 'structures_fabric';
    m.renderOrder = 2;
    grp.add(m);
  }
  return grp;
}
