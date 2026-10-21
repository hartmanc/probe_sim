// Scenery from the track package's scenery.json (CONTRACTS §2b): far terrain, oaks, buildings, bridges,
// barriers, kerbs, boards and the flag stand. ENU -> three: X = x, Y = z, Z = -y.
// Everything is static: instanced or merged per kind and chunked so frustum culling works. Nothing here
// casts shadows (only the car does).
import * as THREE from 'three';
import { trackDistance } from './quality';
import { mergeGeometries, mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import type { PitLaneJson, SausageJson, TrackJson } from './physics-types';
import { PitExitCones, type PitExitConesJson } from './trackmath';
import { TRACK } from './track-choice';
import { buildStructures, selfLitMaterial, TERRACE_SELF_LIT, type StructureJson, type TerraceJson } from './structures';

type V2 = [number, number];
type V3 = [number, number, number];

export interface PackedTrees { stride: number; fields: string[]; scale: number; data: number[] }
export interface SceneryJson {
  version: number;
  far?: {
    heightfield?: { file: string; x0: number; y0: number; dx: number; nx: number; ny: number };
    ortho?: { file: string; x0: number; y0: number; x1: number; y1: number } | null;
    ground_color?: string;
  };
  trees: PackedTrees;
  far_trees?: PackedTrees;
  /** plain: walls without the window / door facade (an evidence override, round 6) */
  buildings: { kind: string; name: string; z: number; h: number; footprint: V2[]; src: string; plain?: boolean }[];
  bridges: { id: string; kind: string; name: string; s: number; deck_z: number; a: V2; b: V2; width: number; banners: string[][]; style?: 'deck' | 'arch' | 'sign';
    /** where the deck meets the banks (20 Oct 2026): an abutment at `at` from z_ground to the deck, stairs on to `to` */
    ends?: { at: V2; z_ground: number; to: V2; z_to: number }[] }[];
  /** color: the wall's paint where the evidence shows it (Sonoma 2026: light blue / green), default plain concrete */
  barriers: { kind: 'concrete' | 'armco' | 'tyres' | 'pitwall' | 'fence'; h: number; fence: number; pts: V3[]; src: string; color?: string;
    /** tyres per stack (round 7; default from h) */ stack?: number }[];
  kerbs: { width: number; inside?: boolean; stripe_m: number; /** [stripe, base] sRGB hex; default red / white */ colors?: [string, string];
    /** raised concrete kerbs (physics: src/physics/track.ts KerbsJson); absent = flat paint */ profile?: { height: number; face: number; back: number } | null;
    strips: { side: number; s0: number; s1: number; kind: string; paint?: number; inset?: number ; /** verge: white line on the outer edge (default on) */ edge?: boolean;
      /** per-strip paint [stripe, base] */ colors?: [string, string]; /** band centre beyond the edge, m (default: the inside convention) */ off?: number; src?: string }[] };
  /** raised yellow sausage kerbs beyond the apex kerbs (physics: src/physics/track.ts) */
  sausages?: SausageJson | null;
  edge_lines?: { width: number; inset: number; runs: { side: number; s0: number; s1: number }[] };
  /** Paved pit lane (CONTRACTS §2b); the physics reads the same block. gap_* = free width to the track edge. */
  pit_lane?: { spacing_m: number; fractions: number[]; open?: boolean; parts: (PitLaneJson['parts'][number] & { gap_left: number[]; gap_right: number[]; track_s: number[] })[] } | null;
  /** Paved runoff (CONTRACTS §2b): same layout as pit_lane; rendered as asphalt, driven at full grip. */
  paved_zones?: { spacing_m: number; fractions: number[]; open?: boolean; parts: (PitLaneJson['parts'][number] & { gap_left: number[]; gap_right: number[]; track_s: number[]; turn?: string;
    /** closed roads (20 Oct 2026): 'asphalt' = the circuit's road material, 'concrete' = pale concrete; absent = the aerial photo's own colour (paved runoff) */
    surface?: 'asphalt' | 'concrete' })[] } | null;
  /** painted lines off the track (closed roads' edge lines measured on the captures, 20 Oct 2026): white strips */
  paint_lines?: { width: number; side?: number; pts: V3[]; src?: string; /** round 7: line colour (default white) */ color?: string }[];
  /** painted ground logos as typed text (round 7b): centre, reading direction (rad, ENU), size, colours */
  ground_signs?: { x: number; y: number; z: number; heading: number; length: number; height: number; text: string; fg: string; bg?: string; src?: string }[];
  /** raised kerb strips off the lap (round 7b): centre line, width, height, stripe length, colours */
  kerb_lines?: { pts: V3[]; width: number; height: number; stripe_m: number; colors: string[]; src?: string }[];
  /** paved ground that is not driven (the paddock, 20 Oct 2026): plain paving over the terrain, no physics */
  paved_areas?: { name: string; surface: 'asphalt' | 'concrete'; src: string; poly: V2[] }[];
  /** Cone line between the pit-exit lane and the track (CONTRACTS §2b); crossing it is a black-flag offence. */
  pit_exit_cones?: PitExitConesJson | null;
  /** cone lines across the mouths of paved but unused roads (closed variants of the circuit, 20 Oct 2026): drawn only */
  cone_lines?: { spacing_m: number; pts: [number, number, number][]; src?: string; color?: string; size?: number; style?: 'cone' | 'delineator' }[];
  /** kinds: brake | corner | flagstand | oak | banner (ad board facing the track) | sign (on a wall at z) | gantry (two
   *  lattice towers at (x, y, z) and (x2, y2, z2) with cables across the track) */
  landmarks: { kind: string; text: string; x: number; y: number; z: number; heading: number; h: number; w: number; x2?: number; y2?: number; z2?: number; color?: string; style?: string; src?: string;
    /** wall-board signs: the panel's top above the ground (m), for the coverage gate */ top?: number;
    /** 'impact' (impact barrier block at a wall's nose): its length along `heading`; 'marshal' (round 8): the hut's
     *  depth along `heading` (absent: w x w) */ d?: number;
    /** 'marshal' (round 8, Sonoma owner note 61): the roof colour (absent: white) */ roof?: string;
    /** wall boards with a typed name (round 6): the lettering's colour */ fg?: string }[];
  /** grandstands built into a hillside: stepped concrete rows following the ground (20 Oct 2026). Row r is a tread
   *  from a to b at height z, `run` m deep away from the track along `dir`; risers join consecutive rows. A terrace declared
   *  by its measured footprint (Sonoma round 6) has polyline rows that follow the stand (`pts`, `nrm`; structures.ts). */
  terraces?: TerraceJson[];
  /** parametric structures (grandstands, garages, blocks, fuel islands, fences, masts, pit-box paint, boards, terrace
   *  dressing; src/app/structures.ts, tools/track/build_structures.py; 21 Oct 2026) */
  structures?: StructureJson[];
}
export interface SceneryAssets { json: SceneryJson; farHeightfield: Float32Array | null; farOrtho: THREE.Texture | null }

const v3 = (x: number, y: number, z: number) => new THREE.Vector3(x, z, -y);
/** three rotation about +Y that turns a +Z-facing object to face ENU heading h. */
const yawFor = (h: number) => Math.atan2(Math.cos(h), -Math.sin(h));

let rngState = 12345;
const rand = () => { rngState = (rngState * 1664525 + 1013904223) >>> 0; return rngState / 4294967296; };

// ------------------------------------------------------------------ far terrain
function buildFar(track: TrackJson, sc: SceneryAssets): THREE.Object3D | null {
  const far = sc.json.far;
  const hf = sc.farHeightfield;
  if (!far?.heightfield || !hf) return null;
  const h = far.heightfield;
  const nh = track.heightfield;
  // near-terrain box, shrunk by one far cell: far quads entirely inside it are hidden under the near mesh anyway
  const bx0 = nh.x0 + h.dx, by0 = nh.y0 + h.dx;
  const bx1 = nh.x0 + (nh.nx - 1) * nh.dx - h.dx, by1 = nh.y0 + (nh.ny - 1) * nh.dx - h.dx;
  const inside = (x: number, y: number) => x > bx0 && x < bx1 && y > by0 && y < by1;
  const o = far.ortho;
  const pos = new Float32Array(h.nx * h.ny * 3);
  const uv = new Float32Array(h.nx * h.ny * 2);
  for (let r = 0; r < h.ny; r++) for (let c = 0; c < h.nx; c++) {
    const k = r * h.nx + c;
    const x = h.x0 + c * h.dx, y = h.y0 + r * h.dx;
    pos[k * 3] = x; pos[k * 3 + 1] = hf[k] - 0.6; pos[k * 3 + 2] = -y;
    if (o) { uv[k * 2] = (x - o.x0) / (o.x1 - o.x0); uv[k * 2 + 1] = (y - o.y0) / (o.y1 - o.y0); }
  }
  const idx: number[] = [];
  for (let r = 0; r < h.ny - 1; r++) for (let c = 0; c < h.nx - 1; c++) {
    const x0 = h.x0 + c * h.dx, y0 = h.y0 + r * h.dx;
    if (inside(x0, y0) && inside(x0 + h.dx, y0 + h.dx)) continue;
    const a = r * h.nx + c, b = a + 1, d = a + h.nx, e = d + 1;
    idx.push(a, b, d, b, e, d);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const ground = new THREE.Color(far.ground_color ?? '#b59a6a');
  const mat = new THREE.MeshLambertMaterial(sc.farOrtho ? { map: sc.farOrtho } : { color: ground });
  if (sc.farOrtho) { sc.farOrtho.anisotropy = 8; sc.farOrtho.wrapS = sc.farOrtho.wrapT = THREE.ClampToEdgeWrapping; }
  const g = new THREE.Group();
  g.name = 'far_terrain';
  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'far_terrain';
  g.add(mesh);
  // skirt from the far edge out to 7 km at the edge height, so the horizon never shows sky under the ground
  const ring: number[] = [];
  const edge: [number, number, number][] = [];
  for (let c = 0; c < h.nx; c++) edge.push([h.x0 + c * h.dx, h.y0, hf[c]]);
  for (let r = 1; r < h.ny; r++) edge.push([h.x0 + (h.nx - 1) * h.dx, h.y0 + r * h.dx, hf[r * h.nx + h.nx - 1]]);
  for (let c = h.nx - 2; c >= 0; c--) edge.push([h.x0 + c * h.dx, h.y0 + (h.ny - 1) * h.dx, hf[(h.ny - 1) * h.nx + c]]);
  for (let r = h.ny - 2; r >= 1; r--) edge.push([h.x0, h.y0 + r * h.dx, hf[r * h.nx]]);
  const step = 5;
  const pts: THREE.Vector3[] = [];
  for (let i = 0; i < edge.length; i += step) {
    const [x, y, z] = edge[i];
    const l = Math.hypot(x, y);
    pts.push(v3(x, y, z - 0.6), v3((x / l) * 7000, (y / l) * 7000, z * 0.6 + 20));
  }
  const m = pts.length / 2;
  for (let i = 0; i < m; i++) {
    const j = (i + 1) % m;
    const a = pts[i * 2], b = pts[i * 2 + 1], c = pts[j * 2], d = pts[j * 2 + 1];
    ring.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z, c.x, c.y, c.z, b.x, b.y, b.z, d.x, d.y, d.z);
  }
  const rg = new THREE.BufferGeometry();
  rg.setAttribute('position', new THREE.Float32BufferAttribute(ring, 3));
  rg.computeVertexNormals();
  const skirt = new THREE.Mesh(rg, new THREE.MeshLambertMaterial({ color: ground.clone().multiplyScalar(0.8), side: THREE.DoubleSide }));
  skirt.name = 'far_skirt';
  g.add(skirt);
  return g;
}

// ------------------------------------------------------------------ oaks
function lobe(cx: number, cy: number, cz: number, sx: number, sy: number, sz: number, detail: number): THREE.BufferGeometry {
  const g = new THREE.IcosahedronGeometry(1, detail);
  const p = g.attributes.position as THREE.BufferAttribute;
  // lumpy crown: displacement is a function of the unit-sphere position so the (non-indexed) faces stay closed
  const ph = rand() * 10;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const j = 1 + 0.09 * Math.sin(3.1 * x + ph) * Math.cos(2.7 * z - ph) + 0.06 * Math.sin(4.3 * y + 1.7 * x + ph * 2);
    p.setXYZ(i, cx + x * sx * j, cy + y * sy * j, cz + z * sz * j);
  }
  g.deleteAttribute('uv');
  g.deleteAttribute('normal');
  return mergeVertices(g, 1e-4); // weld so the crown shades smoothly
}

/** A 1x1 white stand-in where there is no canvas (tests). */
function flatTexture(): THREE.Texture {
  const t = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1, THREE.RGBAFormat);
  t.needsUpdate = true;
  return t;
}

/** Leaf-cluster atlas (2 x 2 cells): oak leaves as small ellipses in clumps, thinning to a ragged edge. sRGB; the
 *  cards are alpha-tested, so the canopy's silhouette is leaves, not a blob. */
function leafAtlas(): THREE.Texture {
  if (typeof document === 'undefined') return flatTexture();
  const N = 512, C = 256;
  const cv = document.createElement('canvas'); cv.width = cv.height = N;
  const g = cv.getContext('2d');
  if (!g) return flatTexture();
  const palette = ['#2f4a1f', '#3a5a26', '#46682c', '#557a35', '#3d5b2a', '#6a8a3e', '#2b3f1c', '#4f7030'];
  for (let cell = 0; cell < 4; cell++) {
    const ox = (cell % 2) * C + C / 2, oy = Math.floor(cell / 2) * C + C / 2;
    const clumps: [number, number, number][] = [];
    for (let k = 0; k < 7; k++) { const a = rand() * Math.PI * 2, d = rand() * 0.5 * (C / 2); clumps.push([ox + Math.cos(a) * d, oy + Math.sin(a) * d, (0.3 + rand() * 0.25) * (C / 2)]); }
    for (let i = 0; i < 1100; i++) {
      const [cx, cy, cr] = clumps[i % clumps.length];
      const a = rand() * Math.PI * 2, d = Math.sqrt(rand()) * cr;
      const x = cx + Math.cos(a) * d, y = cy + Math.sin(a) * d;
      if (Math.hypot(x - ox, y - oy) > C / 2 - 6) continue;
      const len = 6 + rand() * 6, wid = len * (0.4 + rand() * 0.25), rot = rand() * Math.PI;
      g.fillStyle = palette[Math.floor(rand() * palette.length)];
      g.beginPath(); g.ellipse(x, y, len / 2, wid / 2, rot, 0, Math.PI * 2); g.fill();
    }
  }
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  return t;
}

/** Bark: vertical streaks, repeated around and up the trunk. */
function barkTexture(): THREE.Texture {
  if (typeof document === 'undefined') return flatTexture();
  const W = 64, H = 256;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const g = cv.getContext('2d');
  if (!g) return flatTexture();
  g.fillStyle = '#5a4e40'; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 90; i++) {
    const x0 = rand() * W, w = 1 + rand() * 3, dark = rand() < 0.55;
    g.fillStyle = dark ? 'rgba(40,32,26,0.7)' : 'rgba(120,106,88,0.55)';
    for (let y = 0; y < H; y += 16) g.fillRect(((x0 + Math.sin(y * 0.11 + i) * 1.5) % W + W) % W, y, w, 16);
  }
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(2, 3);
  return t;
}

/**
 * Unit oak canopy as `cards` leaf-textured quads scattered through the crown (x, z in [-1, 1], y ~0.3..1, scaled
 * per tree by crown radius and height). Normals point out from the canopy's centre so the cluster shades like one
 * round crown; a vertex colour darkens the underside. Cards are half as tall as wide because the instance scale
 * stretches y by the tree's height (about twice its crown radius).
 */
function foliageGeometry(variant: number, cards: number): THREE.BufferGeometry {
  const parts: THREE.BufferGeometry[] = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), pos = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  for (let k = 0; k < cards; k++) {
    const a = rand() * Math.PI * 2, d = Math.sqrt(rand()) * 0.6;
    const cx = Math.cos(a) * d, cz = Math.sin(a) * d, cy = 0.52 + rand() * 0.3;
    const s = 1.0 + rand() * 0.5;
    const pg = new THREE.PlaneGeometry(s, s * 0.5);
    const cell = (variant * 3 + k) % 4;
    const uv = pg.attributes.uv as THREE.BufferAttribute;
    for (let i = 0; i < uv.count; i++) uv.setXY(i, (uv.getX(i) + (cell % 2)) / 2, (uv.getY(i) + (1 - Math.floor(cell / 2))) / 2);
    e.set((rand() - 0.5) * 1.3, rand() * Math.PI, (rand() - 0.5) * 1.3);
    m.compose(pos.set(cx, cy, cz), q.setFromEuler(e), one);
    pg.applyMatrix4(m);
    parts.push(pg);
  }
  const g = mergeGeometries(parts)!;
  const p = g.attributes.position as THREE.BufferAttribute;
  const n = new Float32Array(p.count * 3), c = new Float32Array(p.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.set(p.getX(i), p.getY(i) - 0.62, p.getZ(i)); v.y *= 1.8; v.normalize();
    n[i * 3] = v.x; n[i * 3 + 1] = v.y; n[i * 3 + 2] = v.z;
    const l = 0.55 + 0.55 * THREE.MathUtils.clamp((p.getY(i) - 0.3) / 0.75, 0, 1);
    c[i * 3] = l; c[i * 3 + 1] = l; c[i * 3 + 2] = l;
  }
  g.setAttribute('normal', new THREE.BufferAttribute(n, 3));
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  return g;
}

/** Unit coast-live-oak crown as a lumpy blob (the far-pack fallback and the pre-18-Oct look). */
function crownGeometry(variant: number, detail: number): THREE.BufferGeometry {
  const L: THREE.BufferGeometry[] = [];
  if (variant === 0) {
    L.push(lobe(0, 0.64, 0, 0.78, 0.34, 0.78, detail), lobe(0.42, 0.56, 0.25, 0.55, 0.27, 0.55, detail), lobe(-0.38, 0.6, -0.3, 0.55, 0.3, 0.5, detail));
  } else if (variant === 1) {
    L.push(lobe(0.1, 0.6, 0, 0.7, 0.36, 0.72, detail), lobe(-0.45, 0.52, 0.2, 0.5, 0.25, 0.5, detail), lobe(0.3, 0.72, -0.35, 0.5, 0.26, 0.5, detail));
  } else {
    L.push(lobe(0, 0.66, 0, 0.82, 0.32, 0.7, detail), lobe(0.05, 0.5, 0.45, 0.5, 0.24, 0.48, detail));
  }
  const g = mergeGeometries(L);
  g.computeVertexNormals();
  // darker underside and interior (cheap ambient occlusion) plus a little leafy variation
  const p = g.attributes.position as THREE.BufferAttribute;
  const col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const ao = 0.45 + 0.55 * THREE.MathUtils.smoothstep(y, 0.3, 0.95);
    const f = 0.9 + 0.1 * Math.sin(11 * x + 7 * z) * Math.cos(9 * y);
    col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = ao * f;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return g;
}

/** Clearance (m) a trunk keeps from any driveable centreline beyond its own crown radius: half-widths run to ~8 m,
 *  shoulders and barriers a few more (owner, 18 Oct 2026: a tree through the Corkscrew bridge — "no trees anywhere
 *  where a user can drive"). */
export const TREE_CLEARANCE_M = 10;
/** Pure: keep a tree of crown radius r whose trunk is d from the nearest driveable centreline? */
export function keepTreeClear(d: number, r: number): boolean { return d - r >= TREE_CLEARANCE_M; }

function buildTrees(packs: { p: PackedTrees; far: boolean }[], keep?: (x: number, y: number, r: number) => boolean): THREE.Group {
  const group = new THREE.Group();
  group.name = 'trees';
  // leaf cards near the track, fewer for the far pack (owner, 18 Oct 2026: "make the trees look more like trees")
  const crownsNear = [0, 1, 2].map((v) => foliageGeometry(v, 11));
  const crownsFar = [foliageGeometry(0, 5), foliageGeometry(2, 5)];
  void crownGeometry;
  const trunkGeo = new THREE.CylinderGeometry(0.55, 0.8, 1, 8, 1, true).translate(0, 0.5, 0);
  const crownMat = new THREE.MeshLambertMaterial({ map: leafAtlas(), alphaTest: 0.45, side: THREE.DoubleSide, vertexColors: true });
  const trunkMat = new THREE.MeshLambertMaterial({ map: barkTexture() });
  const base = new THREE.Color(0xe6efd8);
  const tmp = new THREE.Color();
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), pv = new THREE.Vector3();
  const Y = new THREE.Vector3(0, 1, 0);
  for (const { p, far } of packs) {
    const n = Math.floor(p.data.length / p.stride);
    const tile = far ? 900 : 250;
    const buckets = new Map<string, number[]>();
    for (let i = 0; i < n; i++) {
      const x = p.data[i * p.stride] * p.scale, y = p.data[i * p.stride + 1] * p.scale;
      if (keep && !keep(x, y, Math.max(1.2, p.data[i * p.stride + 4] * p.scale))) continue;
      const key = `${Math.floor(x / tile)},${Math.floor(y / tile)}`;
      let b = buckets.get(key);
      if (!b) buckets.set(key, (b = []));
      b.push(i);
    }
    const crowns = far ? crownsFar : crownsNear;
    for (const ids of buckets.values()) {
      const perVar: number[][] = crowns.map(() => []);
      for (const i of ids) perVar[(i * 7919) % crowns.length].push(i);
      const trunks = new THREE.InstancedMesh(trunkGeo, trunkMat, ids.length);
      let t = 0;
      perVar.forEach((list, v) => {
        if (!list.length) return;
        const im = new THREE.InstancedMesh(crowns[v], crownMat, list.length);
        list.forEach((i, k) => {
          const o = i * p.stride;
          const x = p.data[o] * p.scale, y = p.data[o + 1] * p.scale, z = p.data[o + 2] * p.scale;
          const h = Math.max(3, p.data[o + 3] * p.scale), r = Math.max(1.2, p.data[o + 4] * p.scale);
          const yaw = ((i * 2654435761) % 6283) / 1000;
          q.setFromAxisAngle(Y, yaw);
          // crowns hang low on Laguna's oaks: radius from the lidar, height a touch more than measured top
          m.compose(pv.set(x, z - 0.2, -y), q, s.set(r, h * 1.02, r * (0.9 + ((i * 31) % 20) / 100)));
          im.setMatrixAt(k, m);
          const hue = (((i * 131) % 100) / 100 - 0.5) * 0.04;
          const lum = 0.78 + ((i * 17) % 32) / 100;
          tmp.copy(base).offsetHSL(hue, 0, 0).multiplyScalar(lum);
          im.setColorAt(k, tmp);
          const tr = 0.14 + 0.022 * h;
          m.compose(pv.set(x, z - 0.3, -y), q, s.set(tr, h * 0.5, tr));
          trunks.setMatrixAt(t++, m);
        });
        im.computeBoundingSphere();
        group.add(im);
      });
      trunks.count = t;
      trunks.computeBoundingSphere();
      group.add(trunks);
    }
  }
  return group;
}

// ------------------------------------------------------------------ buildings
const BUILDING_COLORS: Record<string, number[]> = {
  building: [0xd9d3c5, 0xcac4b6, 0xbdb7aa, 0xe4dfd4, 0xc7bfae],
  garage: [0xe1ddd3, 0xd5d0c4],
  grandstand: [0xe8ebee],
  tower: [0xdcd8cf],
  hangar: [0xe3e5e6],
};

/** Facade atlas, one storey (3.2 m) per tile row: bottom 30 % plain wall, then a window band. The left half has
 *  windows (offices, tower), the right half roll-up doors (garages). uv (0.25, 0.1) is plain wall. */
function facadeTexture(): THREE.Texture {
  const cv = document.createElement('canvas');
  cv.width = 256; cv.height = 128;
  const g = cv.getContext('2d')!;
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 128);
  g.fillStyle = '#e9e9e9'; g.fillRect(0, 0, 256, 6);              // slab edge at each floor
  g.fillStyle = '#3a4654'; g.fillRect(0, 30, 128, 52);              // window band
  g.fillStyle = '#d8d8d8';
  for (let x = 0; x < 128; x += 32) g.fillRect(x, 30, 4, 52);       // mullions
  g.fillStyle = '#9b9d9f'; g.fillRect(136, 24, 112, 104);           // roll-up door
  g.fillStyle = '#8a8c8e';
  for (let y = 28; y < 128; y += 8) g.fillRect(136, y, 112, 2);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = THREE.ClampToEdgeWrapping; t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  return t;
}

/** Bleacher rows: light aluminium seat, dark riser, one row per tile (v), 0.85 m per row. */
function bleacherTexture(): THREE.Texture {
  const cv = document.createElement('canvas');
  cv.width = 8; cv.height = 64;
  const g = cv.getContext('2d')!;
  g.fillStyle = '#e4e6e8'; g.fillRect(0, 0, 8, 64);
  g.fillStyle = '#80868c'; g.fillRect(0, 40, 8, 24);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  return t;
}

/** Hillside grandstands as stepped concrete rows (scenery.json `terraces`): a tread per row at its height and a riser
 *  down to the row below (row 0 to the ground). Bleacher grey with the row contrast that reads at a distance (round 6,
 *  the orchestrator's sheets: the stands read as brown wedges): light concrete treads in two close greys, dark risers
 *  shadow lines at the foot of each riser (what the track sees between rows). Polyline rows (`pts`, `nrm`) follow the stand vertex by vertex. */
/** Polyline terrace rows onto the DRAWN terrain (round 6): the package puts each tread on the heightfield at its back
 *  edge, but the terrain is drawn as a 3 m mesh whose planes cut through 1.1-1.25 m steps and buried the rows (the stands
 *  read as flat ortho-grey slopes). Each vertex's tread is lifted to 3 cm over the drawn ground under its front, middle
 *  and back, the riser's foot follows the (lifted) row below at the same metre mark, and row 0's riser starts on the
 *  drawn ground. Straight rows and terraces without `ground` pass unchanged. Pure. */
export function liftTerraces(list: TerraceJson[], ground?: (x: number, y: number) => number): TerraceJson[] {
  if (!ground) return list;
  return list.map((t) => {
    if (!t.rows.some((r) => r.pts)) return t;
    const h = t.run / 2, lifted = new Map<string, number>();
    const rows = [...t.rows].sort((a, b) => (a.k ?? 0) - (b.k ?? 0)).map((r) => {
      if (!r.pts || !r.nrm) return r;
      const pts = r.pts.map((q, i) => {
        const n = r.nrm![i];
        const gz = Math.max(ground(q[0] - n[0] * h, q[1] - n[1] * h), ground(q[0], q[1]), ground(q[0] + n[0] * h, q[1] + n[1] * h));
        const z = Math.max(q[2], gz + 0.03);
        const below = lifted.get(`${(r.k ?? 0) - 1}:${q[4]}`);
        const zl = below !== undefined ? Math.min(below, z) : Math.min(q[3], ground(q[0] - n[0] * h, q[1] - n[1] * h));
        return [q[0], q[1], z, zl, q[4]] as [number, number, number, number, number];
      });
      for (const q of pts) lifted.set(`${r.k ?? 0}:${q[4]}`, q[2]);
      return { ...r, pts, z: Math.min(...pts.map((q) => q[2])) };
    });
    return { ...t, rows };
  });
}

export const TERRACE_TREAD_A = 0xc6c5c0, TERRACE_TREAD_B = 0xbab9b4, TERRACE_RISER = 0x4a4946, TERRACE_STEP = 0xa6a5a0;
function buildTerraces(list: NonNullable<SceneryJson['terraces']>): THREE.Mesh | null {
  const pos: number[] = [], col: number[] = [];
  const cA = new THREE.Color(TERRACE_TREAD_A), cB = new THREE.Color(TERRACE_TREAD_B), cR = new THREE.Color(TERRACE_RISER), cS = new THREE.Color(TERRACE_STEP);
  const quad = (p: THREE.Vector3[], c: THREE.Color) => {
    for (const k of [0, 1, 2, 0, 2, 3]) { pos.push(p[k].x, p[k].y, p[k].z); col.push(c.r, c.g, c.b); }
  };
  for (const t of list) {
    const [ux, uy] = t.dir, h = t.run / 2;
    t.rows.forEach((r, i) => {
      if (r.pts && r.nrm && r.pts.length >= 2) {
        const P = r.pts, N = r.nrm, c = (r.k ?? i) % 2 ? cA : cB;
        for (let j = 0; j + 1 < P.length; j++) {
          const a = P[j], b = P[j + 1], na = N[j], nb = N[j + 1];
          const fa: V2 = [a[0] - na[0] * h, a[1] - na[1] * h], fb: V2 = [b[0] - nb[0] * h, b[1] - nb[1] * h];
          const a0 = v3(fa[0], fa[1], a[2]), b0 = v3(fb[0], fb[1], b[2]);
          const a1 = v3(a[0] + na[0] * h, a[1] + na[1] * h, a[2]), b1 = v3(b[0] + nb[0] * h, b[1] + nb[1] * h, b[2]);
          quad([a0, b0, b1, a1], c);
          // riser: the shadow line under the row above's front (lower 45 %, dark) and the step face (upper part, concrete):
          // the dark line every row is what reads as rows at a distance
          const ma = a[3] + (a[2] - a[3]) * 0.45, mb = b[3] + (b[2] - b[3]) * 0.45;
          quad([v3(fa[0], fa[1], a[3]), v3(fb[0], fb[1], b[3]), v3(fb[0], fb[1], mb), v3(fa[0], fa[1], ma)], cR);
          quad([v3(fa[0], fa[1], ma), v3(fb[0], fb[1], mb), b0, a0], cS);
        }
        return;
      }
      const a0: V2 = [r.a[0] - ux * h, r.a[1] - uy * h], b0: V2 = [r.b[0] - ux * h, r.b[1] - uy * h];
      const a1: V2 = [r.a[0] + ux * h, r.a[1] + uy * h], b1: V2 = [r.b[0] + ux * h, r.b[1] + uy * h];
      quad([v3(a0[0], a0[1], r.z), v3(b0[0], b0[1], r.z), v3(b1[0], b1[1], r.z), v3(a1[0], a1[1], r.z)], i % 2 ? cA : cB);
      const zl = i === 0 ? t.z_ground_front - 0.3 : t.rows[i - 1].z;
      quad([v3(a0[0], a0[1], zl), v3(b0[0], b0[1], zl), v3(b0[0], b0[1], r.z), v3(a0[0], a0[1], r.z)], cR);
    });
  }
  if (!pos.length) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.computeVertexNormals();
  const mat = selfLitMaterial(TERRACE_SELF_LIT);
  const m = new THREE.Mesh(g, mat);
  m.name = 'terraces';
  return m;
}

function buildBuildings(track: TrackJson, list: SceneryJson['buildings'], stands = false): THREE.Mesh {
  const pos: number[] = [], col: number[] = [], uvs: number[] = [];
  const c = new THREE.Color(), cr = new THREE.Color();
  const PLAIN: [number, number] = [0.25, 0.1];
  const tri = (a: THREE.Vector3, b: THREE.Vector3, d: THREE.Vector3, cc: THREE.Color, uv?: [number, number][]) => {
    pos.push(a.x, a.y, a.z, b.x, b.y, b.z, d.x, d.y, d.z);
    for (let k = 0; k < 3; k++) { col.push(cc.r, cc.g, cc.b); const q = uv ? uv[k] : PLAIN; uvs.push(q[0], q[1]); }
  };
  // distance to the track centre (for grandstand slope)
  const dTrack = (x: number, y: number) => {
    let best = 1e9;
    for (let i = 0; i < track.n; i += 4) { const p = track.center[i]; const d = (p[0] - x) ** 2 + (p[1] - y) ** 2; if (d < best) best = d; }
    return Math.sqrt(best);
  };
  list.forEach((b, bi) => {
    let fp = b.footprint.map(([x, y]) => new THREE.Vector2(x, y));
    if (THREE.ShapeUtils.isClockWise(fp)) fp = fp.reverse();
    const pal = BUILDING_COLORS[b.kind] ?? BUILDING_COLORS.building;
    c.setHex(pal[bi % pal.length]);
    cr.copy(c).multiplyScalar(b.kind === 'grandstand' ? 0.72 : 0.62);
    const z0 = b.z - 0.4;
    // grandstands rise away from the track: low front, full height at the back
    let top = fp.map(() => b.z + b.h);
    if (b.kind === 'grandstand') {
      const d = fp.map((p) => dTrack(p.x, p.y));
      const dmin = Math.min(...d), dmax = Math.max(...d);
      top = d.map((v) => b.z + b.h * (0.3 + 0.7 * (dmax > dmin ? (v - dmin) / (dmax - dmin) : 1)));
    }
    for (let i = 0; i < fp.length; i++) {
      const j = (i + 1) % fp.length;
      const a0 = v3(fp[i].x, fp[i].y, z0), b0 = v3(fp[j].x, fp[j].y, z0);
      const a1 = v3(fp[i].x, fp[i].y, top[i]), b1 = v3(fp[j].x, fp[j].y, top[j]);
      // facade: windows on offices/tower, doors on garages, plain on grandstands and sheds under 3 m
      const len = Math.hypot(fp[j].x - fp[i].x, fp[j].y - fp[i].y);
      const plain = stands || b.h < 3 || b.plain === true;
      const half = b.kind === 'garage' ? 0.5 : 0;
      const bays = Math.max(1, Math.round(len / (b.kind === 'garage' ? 5 : 4)));
      const sto = (top[i] - z0) / 3.2, stoJ = (top[j] - z0) / 3.2;
      const u0 = half + 0.02, u1 = half + 0.48; // one atlas tile per bay
      if (plain) { tri(a0, b0, b1, c); tri(a0, b1, a1, c); }
      else {
        // split the wall into bays so each gets one window/door tile horizontally
        for (let q = 0; q < bays; q++) {
          const f0 = q / bays, f1 = (q + 1) / bays;
          const p0 = a0.clone().lerp(b0, f0), p1 = a0.clone().lerp(b0, f1);
          const t0 = a1.clone().lerp(b1, f0), t1 = a1.clone().lerp(b1, f1);
          const s0 = sto + (stoJ - sto) * f0, s1 = sto + (stoJ - sto) * f1;
          tri(p0, p1, t1, c, [[u0, 0], [u1, 0], [u1, s1]]);
          tri(p0, t1, t0, c, [[u0, 0], [u1, s1], [u0, s0]]);
        }
      }
    }
    const tris = THREE.ShapeUtils.triangulateShape(fp, []);
    // grandstand seating: rows run along the track, v counts rows away from it
    const dist = stands ? fp.map((p) => dTrack(p.x, p.y)) : null;
    const dmin = dist ? Math.min(...dist) : 0;
    const rowUV = (i: number): [number, number] => [0.5, dist ? (dist[i] - dmin) / 0.85 : 0];
    if (stands && dist && fp.length === 4) {
      // stepped seating: tiers of 0.85 m rising from the front edge (nearest the track) to the back (GPT judge, 18 Oct 2026)
      const order = [0, 1, 2, 3].sort((a, b2) => dist[a] - dist[b2]);
      const front = [fp[order[0]], fp[order[1]]], back = [fp[order[2]], fp[order[3]]];
      if (front[0].distanceTo(back[0]) + front[1].distanceTo(back[1]) > front[0].distanceTo(back[1]) + front[1].distanceTo(back[0])) back.reverse();
      const zf = Math.min(...top), zb = Math.max(...top);
      const depth = Math.max(front[0].distanceTo(back[0]), front[1].distanceTo(back[1]));
      const N = Math.max(2, Math.min(24, Math.round(depth / 0.85)));
      const at = (t: number, e: 0 | 1) => front[e].clone().lerp(back[e], t);
      for (let r = 0; r < N; r++) {
        const t0 = r / N, t1 = (r + 1) / N, z = zf + (zb - zf) * (r + 1) / N, zl = zf + (zb - zf) * r / N;
        const a0 = at(t0, 0), a1 = at(t0, 1), b0 = at(t1, 0), b1 = at(t1, 1);
        const seat = r % 2 ? c : cr;
        tri(v3(a0.x, a0.y, zl), v3(a1.x, a1.y, zl), v3(a1.x, a1.y, z), cr); tri(v3(a0.x, a0.y, zl), v3(a1.x, a1.y, z), v3(a0.x, a0.y, z), cr);
        tri(v3(a0.x, a0.y, z), v3(a1.x, a1.y, z), v3(b1.x, b1.y, z), seat, [[0.5, r], [0.5, r], [0.5, r + 1]]);
        tri(v3(a0.x, a0.y, z), v3(b1.x, b1.y, z), v3(b0.x, b0.y, z), seat, [[0.5, r], [0.5, r + 1], [0.5, r + 1]]);
      }
    } else {
      for (const [i, j, k] of tris) {
        tri(v3(fp[i].x, fp[i].y, top[i]), v3(fp[j].x, fp[j].y, top[j]), v3(fp[k].x, fp[k].y, top[k]), stands ? c : cr,
          stands ? [rowUV(i), rowUV(j), rowUV(k)] : undefined);
      }
    }
    // hangar: gabled roof over a 4-corner footprint, ridge along the long axis, 0.3 x the short side high
    if (b.kind === 'hangar' && fp.length === 4) {
      const e01 = fp[0].distanceTo(fp[1]), e12 = fp[1].distanceTo(fp[2]);
      const [p0, p1, p2, p3] = e01 >= e12 ? fp : [fp[1], fp[2], fp[3], fp[0]];
      const short = Math.min(e01, e12), ztop = b.z + b.h, zr = ztop + 0.3 * short;
      const m03 = p0.clone().add(p3).multiplyScalar(0.5), m12 = p1.clone().add(p2).multiplyScalar(0.5);
      const V = (p: THREE.Vector2, z: number) => v3(p.x, p.y, z);
      const roofC = new THREE.Color(0xb9bdc1);
      tri(V(p0, ztop), V(p1, ztop), V(m12, zr), roofC); tri(V(p0, ztop), V(m12, zr), V(m03, zr), roofC);
      tri(V(p2, ztop), V(p3, ztop), V(m03, zr), roofC); tri(V(p2, ztop), V(m03, zr), V(m12, zr), roofC);
      tri(V(p1, ztop), V(p2, ztop), V(m12, zr), c); tri(V(p3, ztop), V(p0, ztop), V(m03, zr), c);
    }
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ vertexColors: true, map: stands ? bleacherTexture() : facadeTexture(), side: THREE.DoubleSide }));
  mesh.name = stands ? 'grandstands' : 'buildings';
  return mesh;
}

// ------------------------------------------------------------------ barriers
function chainLinkTexture(): THREE.Texture {
  const cv = document.createElement('canvas');
  cv.width = cv.height = 32;
  const g = cv.getContext('2d')!;
  g.clearRect(0, 0, 32, 32);
  g.strokeStyle = 'rgba(205,208,210,1)';
  g.lineWidth = 1.4;
  g.beginPath(); g.moveTo(0, 0); g.lineTo(32, 32); g.moveTo(32, 0); g.lineTo(0, 32); g.stroke();
  const t = new THREE.CanvasTexture(cv);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  return t;
}

/** Offset polyline (ENU xy) sideways by d: per-vertex mitred normal. */
function offsetLine(P: V3[], d: number): V3[] {
  return P.map((p, i) => {
    const a = P[Math.max(0, i - 1)], b = P[Math.min(P.length - 1, i + 1)];
    const tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty) || 1;
    return [p[0] - (ty / l) * d, p[1] + (tx / l) * d, p[2]];
  });
}

class Strip {
  pos: number[] = []; col: number[] = []; uv: number[] = [];
  /** Vertical or general ribbon between two polylines of three-space points. */
  add(A: THREE.Vector3[], B: THREE.Vector3[], c: THREE.Color, uScale = 0, vA = 0, vB = 1): void {
    let u = 0;
    for (let i = 0; i < A.length - 1; i++) {
      const du = A[i].distanceTo(A[i + 1]) * uScale;
      const q = [A[i], B[i], A[i + 1], A[i + 1], B[i], B[i + 1]];
      const uu = [u, u, u + du, u + du, u, u + du];
      const vv = [vA, vB, vA, vA, vB, vB];
      q.forEach((p, k) => { this.pos.push(p.x, p.y, p.z); this.col.push(c.r, c.g, c.b); this.uv.push(uu[k], vv[k]); });
      u += du;
    }
  }
  mesh(mat: THREE.Material, name: string): THREE.Mesh | null {
    if (!this.pos.length) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.col, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, mat);
    m.name = name;
    return m;
  }
}

const TYRE_R = 0.31, TYRE_H = 0.23, TYRE_PITCH = 0.62;
/** Tyres in a stack of height h (m): one per 0.23 m, 1 to 6. */
export function tyresInStack(h: number): number { return Math.max(1, Math.min(6, Math.round((h || 0.92) / TYRE_H))); }
/** One stack of n tyres lying flat: a lathe whose profile bulges per tyre with a dark groove between tyres and a dark
 *  hole at the top (vertex colour by radius: tread 1, groove 0.45, hole 0.25). */
export function tyreStackGeometry(n: number): THREE.BufferGeometry {
  const P: THREE.Vector2[] = [new THREE.Vector2(0.001, 0), new THREE.Vector2(TYRE_R - 0.05, 0)];
  // two profile points per tyre (the bulge, then the groove) and 8 segments: ~190 triangles for a stack of 4
  for (let k = 0; k < n; k++) {
    const y0 = k * TYRE_H;
    P.push(new THREE.Vector2(TYRE_R, y0 + TYRE_H / 2), new THREE.Vector2(TYRE_R - 0.05, y0 + TYRE_H));
  }
  const top = n * TYRE_H;
  P.push(new THREE.Vector2(0.17, top - 0.01), new THREE.Vector2(0.15, top - 0.14), new THREE.Vector2(0.001, top - 0.14));
  const g = new THREE.LatheGeometry(P, 8);
  const p = g.attributes.position as THREE.BufferAttribute;
  const col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const r = Math.hypot(p.getX(i), p.getZ(i));
    const v = r > TYRE_R - 0.01 ? 1 : r > 0.2 ? 0.45 : 0.25;
    col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = v;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return g;
}

function buildBarriers(list: SceneryJson['barriers']): THREE.Group {
  const group = new THREE.Group();
  group.name = 'barriers';
  const concrete = new Strip(), armco = new Strip(), fence = new Strip();
  const cConcrete = new THREE.Color(0xc9c5bb), cTop = new THREE.Color(0xd8d5cc), cPit = new THREE.Color(0xe6e4de);
  const cRail = new THREE.Color(0xc0c6cc), cFence = new THREE.Color(0xffffff);
  const posts: THREE.Matrix4[] = [], fencePosts: THREE.Matrix4[] = [], tyres: { m: THREE.Matrix4; white: boolean; color?: string; n: number }[] = [];
  const up = (P: V3[], dz: number) => P.map((p) => v3(p[0], p[1], p[2] + dz));
  for (const b of list) {
    const P = b.pts;
    if (P.length < 2) continue;
    if (b.kind === 'concrete' || b.kind === 'pitwall') {
      const th = 0.18;
      const L = offsetLine(P, th), R = offsetLine(P, -th);
      const cc = b.color ? new THREE.Color(b.color) : b.kind === 'pitwall' ? cPit : cConcrete;
      concrete.add(up(L, -0.3), up(L, b.h), cc);
      concrete.add(up(R, b.h), up(R, -0.3), cc);
      concrete.add(up(L, b.h), up(R, b.h), b.color ? cc.clone().lerp(cTop, 0.35) : cTop);
      // end caps: close both ends of the run, else an open end shows the wall's inside (Sonoma owner note 36)
      for (const i of [0, P.length - 1]) {
        const e = [L[i], R[i]];
        concrete.add(up(e, -0.3), up(e, b.h), cc);
      }
    } else if (b.kind === 'armco') {
      // W-beam: top and bottom edges forward, the groove set back 5 cm
      const mid = offsetLine(P, 0.05);
      armco.add(up(P, 0.44), up(mid, 0.6), cRail);
      armco.add(up(mid, 0.6), up(P, 0.76), cRail);
      // end plates: close the W-beam's groove at both ends of the run
      for (const i of [0, P.length - 1]) {
        const e = [P[i], mid[i]];
        armco.add(up(e, 0.44), up(e, 0.76), cRail);
      }
      for (let i = 0; i < P.length; i++) {
        posts.push(new THREE.Matrix4().compose(v3(P[i][0], P[i][1], P[i][2] + 0.38), new THREE.Quaternion(), new THREE.Vector3(1, 1, 1)));
      }
    } else if (b.kind === 'tyres') {
      // stacks of round(h / 0.23) tyres every 0.62 m (touching), two staggered rows
      let acc = 0, k = 0;
      // tyres per stack from the evidence (b.stack) or from h; the stack is scaled to stand exactly h high
      const nT = b.stack ?? tyresInStack(b.h), sy = (b.h || nT * TYRE_H) / (nT * TYRE_H);
      const place = (x: number, y: number, z: number) => new THREE.Matrix4().makeTranslation(x, z, -y).multiply(new THREE.Matrix4().makeScale(1, sy, 1));
      for (let i = 0; i < P.length - 1; i++) {
        const a = P[i], c = P[i + 1];
        const seg = Math.hypot(c[0] - a[0], c[1] - a[1]);
        while (acc <= seg) {
          const f = acc / Math.max(seg, 1e-6);
          const x = a[0] + (c[0] - a[0]) * f, y = a[1] + (c[1] - a[1]) * f, z = a[2] + (c[2] - a[2]) * f;
          const nx = -(c[1] - a[1]) / seg, ny = (c[0] - a[0]) / seg;
          for (const row of [0, 1]) {
            const off = row * 0.6, sh = row * 0.31;
            const px = x + nx * off + ((c[0] - a[0]) / seg) * sh, py = y + ny * off + ((c[1] - a[1]) / seg) * sh;
            tyres.push({ m: place(px, py, z), white: !b.color && k % 12 < 2, color: b.color, n: nT });   // mostly black with a white pair every 12 stacks
          }
          k++;
          acc += TYRE_PITCH;
        }
        acc -= seg;
      }
      // close the run's far end: a last stack on the end point unless the spacing already put one within 0.2 m
      const last = P[P.length - 1], prev = P[P.length - 2];
      const segL = Math.hypot(last[0] - prev[0], last[1] - prev[1]);
      if (segL > 1e-6 && TYRE_PITCH - acc > 0.2) {
        const tx = (last[0] - prev[0]) / segL, ty = (last[1] - prev[1]) / segL;
        for (const row of [0, 1]) {
          const off = row * 0.6, sh = row * 0.31;
          const px = last[0] - ty * off - tx * sh, py = last[1] + tx * off - ty * sh;
          tyres.push({ m: place(px, py, last[2]), white: !b.color && k % 12 < 2, color: b.color, n: nT });
        }
      }
    }
    if (b.fence > 0) {
      const base = b.kind === 'fence' ? 0 : b.h;
      fence.add(up(P, base), up(P, base + b.fence), cFence, 1 / 0.3, 0, b.fence / 0.3);
      let acc = 0;
      for (let i = 0; i < P.length; i++) {
        if (i > 0) acc += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]);
        if (i === 0 || i === P.length - 1 || acc >= 3) {
          acc = 0;
          fencePosts.push(new THREE.Matrix4().compose(v3(P[i][0], P[i][1], P[i][2] + base + b.fence / 2), new THREE.Quaternion(), new THREE.Vector3(1, b.fence, 1)));
        }
      }
    }
  }
  const lam = (o: THREE.MeshLambertMaterialParameters) => new THREE.MeshLambertMaterial(o);
  const add = (m: THREE.Object3D | null) => { if (m) group.add(m); };
  add(concrete.mesh(lam({ vertexColors: true, side: THREE.DoubleSide }), 'concrete_walls'));
  add(armco.mesh(lam({ vertexColors: true, side: THREE.DoubleSide }), 'armco'));
  const fenceMat = lam({ vertexColors: true, map: chainLinkTexture(), transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false });
  const fm = fence.mesh(fenceMat, 'catch_fence');
  if (fm) { fm.renderOrder = 2; group.add(fm); }
  const inst = (geo: THREE.BufferGeometry, mat: THREE.Material, ms: THREE.Matrix4[], name: string) => {
    if (!ms.length) return;
    const im = new THREE.InstancedMesh(geo, mat, ms.length);
    ms.forEach((m, i) => im.setMatrixAt(i, m));
    im.computeBoundingSphere();
    im.name = name;
    group.add(im);
  };
  inst(new THREE.BoxGeometry(0.1, 0.8, 0.1), lam({ color: 0x6f747a }), posts, 'armco_posts');
  inst(new THREE.CylinderGeometry(0.035, 0.035, 1, 5), lam({ color: 0x8c9196 }), fencePosts, 'fence_posts');
  if (tyres.length) {
    // stacked tyres (round 7, Sonoma owner note 38: the stacks read as a flat segmented wall): one lathe per stack height,
    // each tyre a rounded bulge with a dark groove between tyres and the dark hole at the top, so a run reads as tyres;
    // one InstancedMesh per stack height, colour per instance (the run's recorded colour, black by default)
    const byN = new Map<number, typeof tyres>();
    for (const t of tyres) { const a = byN.get(t.n); if (a) a.push(t); else byN.set(t.n, [t]); }
    const black = new THREE.Color(0x202020), white = new THREE.Color(0xdedede);
    const tc = new Map<string, THREE.Color>();
    for (const [nT, list2] of byN) {
      const g = tyreStackGeometry(nT);
      const im = new THREE.InstancedMesh(g, lam({ vertexColors: true }), list2.length);
      // a run's recorded colour (Sonoma: black-covered stacks, white at the T11 hairpin) for all its stacks; without one,
      // black with a white pair every 12 stacks (Laguna)
      list2.forEach((t, i) => { im.setMatrixAt(i, t.m); im.setColorAt(i, t.color ? (tc.get(t.color) ?? tc.set(t.color, new THREE.Color(t.color)).get(t.color)!) : t.white ? white : black); });
      im.computeBoundingSphere();
      im.name = 'tyre_walls';
      group.add(im);
    }
  }
  return group;
}

// ------------------------------------------------------------------ sausage kerbs
/** Yellow sausage kerbs: a tube of 7 cross-section rows per metre along each strip. With `ground` = the physics
 *  surface (which carries the hump) the mesh follows the exact profile the wheels feel.
 *  Drawn 15 mm above that surface with the strongest polygon offset of the ground layers (18 Oct 2026: the tubes were
 *  invisible at T2, T8-T11): every ground mesh samples the same humped surface at its own sparse columns, and the
 *  ribbon's first shoulder column (0.5 m out) and the green verge paint's 0.5 m column (dz 0.01, units -8) sit right
 *  on the crest, so their straight tents between columns covered the tube's 4 mm lift; their polygon offsets won the
 *  rest. Outer rows are tucked down to the surface so the lifted tube has no floating lip. */
const SAUSAGE_LIFT_M = 0.015;
function buildSausages(track: TrackJson, j: SausageJson, ground?: (x: number, y: number) => number): THREE.Mesh | null {
  const n = track.n, sp = track.spacing_m || 1, ROWS = 7, Wh = j.width / 2;
  const off = j.kerb_width + j.gap + Wh;
  const pos: number[] = [], idx: number[] = [];
  for (const st of j.strips) {
    const i0 = Math.round(st.s0 / sp), i1 = Math.round(st.s1 / sp);
    const m = i1 - i0 + 1;
    if (m < 2) continue;
    const base = pos.length / 3;
    for (let k = 0; k < m; k++) {
      const i = (((i0 + k) % n) + n) % n;
      const a = track.center[(i - 1 + n) % n], b = track.center[(i + 1) % n];
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      const nx = -dy / l, ny = dx / l;
      const e = st.side > 0 ? track.left[i] : track.right[i];
      const cx = e[0] + nx * st.side * off, cy = e[1] + ny * st.side * off;
      const zc = ground ? ground(cx, cy) : (st.side > 0 ? track.profile.z[i][0] : track.profile.z[i][track.profile.z[i].length - 1]);
      for (let r = 0; r < ROWS; r++) {
        const d = -Wh + (2 * Wh * r) / (ROWS - 1);
        const x = cx + nx * d, y = cy + ny * d;
        // without a physics ground the hump is drawn as its own half-ellipse (the physics ground carries the real, tyre-smoothed profile)
        const z = ground ? ground(x, y) : zc + j.height * Math.sqrt(Math.max(0, 1 - (d / Wh) ** 2));
        pos.push(x, z + (r === 0 || r === ROWS - 1 ? 0.003 : SAUSAGE_LIFT_M), -y);
      }
    }
    for (let k = 0; k < m - 1; k++) for (let r = 0; r < ROWS - 1; r++) {
      const a = base + k * ROWS + r, b = a + 1, c = a + ROWS, d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
  }
  if (!pos.length) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  // ground layers use factor -1..-2, units -2..-10: the tube must win against all of them
  const mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0xe8c227, roughness: 0.62, metalness: 0, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -16 }));
  mesh.castShadow = true; mesh.receiveShadow = true;
  mesh.name = 'sausage_kerbs';
  return mesh;
}

// ------------------------------------------------------------------ kerbs, verge paint, edge lines
/** Supplied by scene.ts: ortho UVs and a mesh factory that shades painted geometry like the track ribbon (graded
 *  aerial image + asphalt detail under a paint layer). Geometry must carry pgA, pgE, pgUvSrc and pgPaintUv. */
export interface PaintSurface {
  uv(x: number, y: number): [number, number];
  mesh(geo: THREE.BufferGeometry, paint: THREE.Texture, name: string, offsetUnits: number): THREE.Mesh;
}

/** Point `out` m outside (negative = inside) the edge on `side` at station i, `dz` above the driven surface (ENU). */
function edgeFrame(track: TrackJson, ground: ((x: number, y: number) => number) | undefined) {
  const n = track.n;
  return (i: number, side: number, out: number, dz: number): V3 => {
    const ii = ((i % n) + n) % n;
    const a = track.center[(ii - 1 + n) % n], b = track.center[(ii + 1) % n];
    const tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty) || 1;
    const nx = -ty / l, ny = tx / l;
    const e = side > 0 ? track.left[ii] : track.right[ii];
    const x = e[0] + nx * side * out, y = e[1] + ny * side * out;
    const zs = ground ? ground(x, y) : (side > 0 ? track.profile.z[ii][0] : track.profile.z[ii][track.profile.z[ii].length - 1]);
    return [x, y, zs + dz];
  };
}

/** Paint atlas: metres along the track per texture repeat (u = metres / PAINT_TILE_M), and the v range of each band
 *  (v0 = track side of the band, v1 = outer side). Canvas rows: kerb 4-124, verge green 132-188, white line 196-252. */
const PAINT_TILE_M = 16;
const PAINT_PX_M = 128;
const PAINT_ROWS = { kerb: [4, 124], green: [132, 188], line: [196, 252] } as const;
const PAINT_V = (band: keyof typeof PAINT_ROWS, t: number) => 1 - (PAINT_ROWS[band][0] + (PAINT_ROWS[band][1] - PAINT_ROWS[band][0]) * t) / 256;

/**
 * Weathered paint atlas (2048 x 256 px, 16 m along): the Laguna Seca kerbs after the 2023 repave are flat concrete
 * strips painted red/white at road level; in the onboard footage the paint is faded (brick red, dirty off-white),
 * rubbered-in on the track half where cars ride, with worn patches showing grey concrete. The green verge paint is a
 * dull mid-green with dirt blown over it; edge lines are off-white with speckled wear. Colours are sRGB; the shader
 * multiplies them by the aerial's local brightness so they pick up the same shade and grime as the road.
 */
const hexRgb = (h: string): number[] => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export function kerbPaintTexture(stripeM: number, colors?: [string, string]): THREE.Texture {
  const key = `kerbpaint${stripeM}${colors ? colors.join('') : ''}`;
  const hit = texCache.get(key);
  if (hit) return hit;
  const W = PAINT_TILE_M * PAINT_PX_M, H = 256;
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d')!;
  const img = g.createImageData(W, H);
  const d = img.data;
  // tileable value noise along u (period W), free along v
  let seed = 911;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const lattice = (cells: number, rows: number) => { const L = new Float32Array(cells * rows); for (let k = 0; k < L.length; k++) L[k] = rnd(); return { L, cells, rows }; };
  const noise = (N: { L: Float32Array; cells: number; rows: number }, x: number, y: number) => {
    const fx = (x / W) * N.cells, fy = (y / H) * (N.rows - 1);
    const i = Math.floor(fx), j = Math.min(Math.floor(fy), N.rows - 2);
    let u = fx - i, v = fy - j;
    u = u * u * (3 - 2 * u); v = v * v * (3 - 2 * v);
    const at = (ii: number, jj: number) => N.L[jj * N.cells + (((ii % N.cells) + N.cells) % N.cells)];
    return (at(i, j) * (1 - u) + at(i + 1, j) * u) * (1 - v) + (at(i, j + 1) * (1 - u) + at(i + 1, j + 1) * u) * v;
  };
  const fade = lattice(24, 6), patch = lattice(96, 12), streak = lattice(48, 64), fine = lattice(512, 96), edgeJ = lattice(128, 4);
  const mix = (a: number[], b: number[], t: number) => a.map((v, k) => v + (b[k] - v) * t);
  const RED = colors ? hexRgb(colors[0]) : [172, 64, 56], WHITE = colors ? hexRgb(colors[1]) : [228, 225, 214], CONC = [170, 166, 156], RUBBER = [60, 58, 55];
  const GREEN = [60, 122, 72], DIRT = [168, 150, 118], LINE = [214, 212, 204];
  const stripePx = stripeM * PAINT_PX_M;
  const put = (x: number, y: number, c: number[], a: number) => {
    const k = (y * W + x) * 4;
    d[k] = c[0]; d[k + 1] = c[1]; d[k + 2] = c[2]; d[k + 3] = Math.round(a * 255);
  };
  const ss = (e0: number, e1: number, v: number) => { const t = Math.min(1, Math.max(0, (v - e0) / (e1 - e0))); return t * t * (3 - 2 * t); };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const nf = noise(fade, x, y), np = noise(patch, x, y), ns = noise(streak, x, y), nn = noise(fine, x, y);
    if (y < 128) {
      // kerb band; t = 0 at the track side
      const t = Math.min(1, Math.max(0, (y - PAINT_ROWS.kerb[0]) / (PAINT_ROWS.kerb[1] - PAINT_ROWS.kerb[0])));
      const xb = x + (noise(edgeJ, x, y) - 0.5) * 5;                       // painted stripe ends, slightly ragged
      const ph = ((xb % (2 * stripePx)) + 2 * stripePx) % (2 * stripePx);
      const red = ss(-2.5, 2.5, ph) * (1 - ss(stripePx - 2.5, stripePx + 2.5, ph)) + ss(2 * stripePx - 2.5, 2 * stripePx + 2.5, ph);
      let c = mix(WHITE, RED, Math.min(1, red));
      c = mix(c, CONC, 0.08 + 0.25 * ss(0.45, 0.85, nf));                // sun-faded paint
      c = mix(c, CONC, ss(0.66, 0.74, np) * 0.85);                        // worn through to the concrete
      const ride = ss(0.0, 0.12, t) * (1 - ss(0.45, 0.8, t));           // the half the tyres run on
      c = mix(c, RUBBER, ride * (0.08 + 0.32 * ss(0.5, 0.85, ns)));       // rubber streaks along the kerb
      c = mix(c, RUBBER, (1 - ss(0.0, 0.035, t)) * 0.45);                // grimy joint against the asphalt
      c = c.map((v) => v * (0.9 + 0.2 * nn));                            // grain
      put(x, y, c, 1);
    } else if (y < 192) {
      const t = Math.min(1, Math.max(0, (y - PAINT_ROWS.green[0]) / (PAINT_ROWS.green[1] - PAINT_ROWS.green[0])));
      let c = mix(GREEN, DIRT, 0.06 + 0.3 * ss(0.4, 0.9, nf));            // dust blown over it
      c = c.map((v) => v * (0.88 + 0.24 * nn));
      const a = 0.92 * (1 - ss(0.82, 1.0, t + (np - 0.5) * 0.25)) * (1 - 0.5 * ss(0.7, 0.8, np));
      put(x, y, c, Math.max(0, a));
    } else {
      const t = Math.min(1, Math.max(0, (y - PAINT_ROWS.line[0]) / (PAINT_ROWS.line[1] - PAINT_ROWS.line[0])));
      const c = mix(LINE, CONC, 0.15 * nf + 0.25 * ss(0.62, 0.8, nn));
      const a = 0.92 * ss(0.0, 0.12, t) * (1 - ss(0.88, 1.0, t)) * (1 - 0.45 * ss(0.68, 0.78, np));
      put(x, y, c, a);
    }
  }
  g.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.anisotropy = 8;
  texCache.set(key, tex);
  return tex;
}

/** Grid strips (stations along x columns across) on the driven surface, with the ribbon's shading attributes:
 *  pgA = 1 (asphalt grade), pgE = 1 with pgUvSrc 1.2 m inside the track side of the strip (the aerial smears asphalt
 *  and dirt at the edge, like the ribbon's edge columns), and pgPaintUv into the paint atlas. One merged mesh. */
class PaintStrips {
  pos: number[] = []; uv: number[] = []; src: number[] = []; puv: number[] = []; idx: number[] = [];
  /** `spacing` = track.spacing_m: strip ranges s0..s1 are metres along the lap (station = s / spacing). */
  constructor(private at: ReturnType<typeof edgeFrame>, private surf: PaintSurface | undefined, private spacing = 1) {}
  add(side: number, sm0: number, sm1: number, cols: { out: number; dz: number; v: number }[], srcOut: number, u0: number): void {
    const base = this.pos.length / 3, K = cols.length;
    const s0 = Math.round(sm0 / this.spacing), s1 = Math.round(sm1 / this.spacing);
    for (let i = s0; i <= s1; i++) {
      const sp = this.at(i, side, srcOut, 0);
      const su = this.surf ? this.surf.uv(sp[0], sp[1]) : [0, 0];
      for (const c of cols) {
        const [x, y, z] = this.at(i, side, c.out, c.dz);
        const p = v3(x, y, z);
        this.pos.push(p.x, p.y, p.z);
        const uv = this.surf ? this.surf.uv(x, y) : [0, 0];
        this.uv.push(uv[0], uv[1]);
        this.src.push(su[0], su[1]);
        this.puv.push((u0 + (i - s0) * this.spacing) / PAINT_TILE_M, c.v);
      }
    }
    for (let i = 0; i < s1 - s0; i++) for (let k = 0; k < K - 1; k++) {
      const a = base + i * K + k, b = a + 1, c = a + K, e = c + 1;
      this.idx.push(a, b, c, b, e, c);
    }
  }
  build(paint: THREE.Texture, name: string, offsetUnits: number): THREE.Mesh | null {
    if (!this.idx.length) return null;
    const g = new THREE.BufferGeometry();
    const n = this.pos.length / 3;
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('pgA', new THREE.Float32BufferAttribute(new Float32Array(n).fill(1), 1));
    g.setAttribute('pgE', new THREE.Float32BufferAttribute(new Float32Array(n).fill(1), 1));
    g.setAttribute('pgUvSrc', new THREE.Float32BufferAttribute(this.src, 2));
    g.setAttribute('pgPaintUv', new THREE.Float32BufferAttribute(this.puv, 2));
    g.setIndex(this.idx);
    g.computeVertexNormals();
    if (this.surf) return this.surf.mesh(g, paint, name, offsetUnits);
    // no aerial (dev track): the paint alone
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.puv, 2));
    const mesh = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ map: paint, transparent: true, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: offsetUnits }));
    mesh.receiveShadow = true;
    mesh.name = name;
    return mesh;
  }
}

/** Kerbs: flat painted concrete strips at road level (8-10 mm, i.e. paint over the driven surface; the physics
 *  surface comes from track.json), red/white every stripe_m, inside the edge on the v2 track (its edges include the
 *  kerbs), with optional green verge paint beyond. One merged mesh for kerbs and verge paint. */
function buildKerbs(track: TrackJson, k: SceneryJson['kerbs'], ground?: (x: number, y: number) => number, surf?: PaintSurface): THREE.Group | THREE.Mesh | null {
  // one paint atlas per colour pair: strips with their own colours (Sonoma 2026: red / white or blue / white by corner)
  const keyOf = (s: SceneryJson['kerbs']['strips'][number]) => (s.colors ?? k.colors ?? ['', '']).join('|');
  const keys = [...new Set(k.strips.map(keyOf))];
  if (keys.length > 1) {
    const g = new THREE.Group(); g.name = 'kerbs';
    for (const key of keys) {
      const sub = buildKerbs(track, { ...k, colors: (key === '|' ? k.colors : key.split('|')) as [string, string] | undefined, strips: k.strips.filter((s) => keyOf(s) === key).map((s) => ({ ...s, colors: undefined })) }, ground, surf);
      if (sub) { sub.name = 'kerbs'; g.add(sub); }
    }
    return g;
  }
  const colors = (k.strips[0]?.colors ?? k.colors) as [string, string] | undefined;
  const st = new PaintStrips(edgeFrame(track, ground), surf, track.spacing_m || 1);
  const w = k.width;
  const period = 2 * k.stripe_m;
  k.strips.forEach((s, j) => {
    // kerb band across the edge: inside it by default, or `off` m beyond it (centre) for a kerb measured outside the edge
    const o0 = s.off !== undefined ? s.off - w / 2 : k.inside ? -w : -0.1, o1 = s.off !== undefined ? s.off + w / 2 : k.inside ? 0 : w;
    const u0 = (j * 3 % 4) * period;                        // vary the wear pattern between kerbs, keep red first
    // columns on the ribbon's own columns where possible (edge, 0.5 m inside) so the paint follows its surface; a raised
    // kerb (profile) gets columns every ~8 cm across its face and top so the paint follows the hump the physics carries,
    // plus its back face down to the ground
    const across = k.profile
      ? [...Array.from({ length: Math.max(3, Math.ceil(w / 0.08)) + 1 }, (_, q) => o0 + (w * q) / Math.max(3, Math.ceil(w / 0.08))), o1 + k.profile.back * 0.5, o1 + k.profile.back]
      : [o0, o1 - 0.5 > o0 + 0.1 ? o1 - 0.5 : (o0 + o1) / 2, o1];
    // kind 'verge': green verge paint only (no red/white kerb), e.g. the long painted aprons seen on satellite imagery
    if (s.kind !== 'verge') st.add(s.side, s.s0, s.s1, across.map((o) => ({ out: o, dz: 0.008 + 0.002 * Math.min(1, (o - o0) / (o1 - o0)), v: PAINT_V('kerb', Math.min(1, (o - o0) / (o1 - o0))) })), o0 - 1.2, u0);
    if (s.paint) {
      const P = s.paint;
      // verge strips may start `inset` m inside the edge (the v2 edge is wider than the painted road in places)
      const base = s.kind === 'verge' ? o1 - (s.inset ?? 0) : o1;
      const cols = [0, 0.5, 1.0, P].filter((o) => o <= P).map((o) => ({ out: base + o, dz: 0.01, v: PAINT_V('green', o / P) }));
      st.add(s.side, s.s0, s.s1, cols, o0 - 1.2, u0);
      // the real green aprons carry a white line along their outer edge (GPT judge, 18 Oct 2026)
      if (s.kind === 'verge' && s.edge !== false) st.add(s.side, s.s0, s.s1, [{ out: base + P, dz: 0.012, v: PAINT_V('line', 0) }, { out: base + P + 0.12, dz: 0.012, v: PAINT_V('line', 1) }], o0 - 1.2, u0);
    }
  });
  return st.build(kerbPaintTexture(k.stripe_m, colors), 'kerbs', -8);
}

/** A line of low grey kerb blocks along the edge (kerb strips of kind 'blocks'): 0.5 x 0.3 m blocks, 0.12 m tall, one
 *  every 1.9 m (the block period read on the 2026 captures at T1), centred `off` m beyond the edge. */
function buildKerbBlocks(track: TrackJson, strips: SceneryJson['kerbs']['strips'], ground?: (x: number, y: number) => number): THREE.InstancedMesh | null {
  const sp = track.spacing_m || 1, n = track.center.length;
  const at: { x: number; y: number; z: number; h: number }[] = [];
  for (const s of strips) {
    for (let m = s.s0; m <= s.s1; m += 1.9) {
      const f = m / sp, i = Math.floor(f) % n, j = (i + 1) % n, t = f - Math.floor(f);
      const E = s.side > 0 ? track.left : track.right;
      const ex = E[i][0] + (E[j][0] - E[i][0]) * t, ey = E[i][1] + (E[j][1] - E[i][1]) * t;
      const cx = track.center[i][0] + (track.center[j][0] - track.center[i][0]) * t, cy = track.center[i][1] + (track.center[j][1] - track.center[i][1]) * t;
      const ux = ex - cx, uy = ey - cy, ul = Math.hypot(ux, uy) || 1, o = s.off ?? 0.3;
      const x = ex + (ux / ul) * o, y = ey + (uy / ul) * o;
      const tx = track.center[j][0] - track.center[i][0], ty = track.center[j][1] - track.center[i][1];
      at.push({ x, y, z: ground ? ground(x, y) : E[i][2], h: Math.atan2(ty, tx) });
    }
  }
  if (!at.length) return null;
  const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.3, 0.12, 0.5), new THREE.MeshLambertMaterial({ color: 0xb9b7b0 }), at.length);
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  at.forEach((a, k) => {
    q.setFromEuler(e.set(0, yawFor(a.h), 0));
    M.compose(v3(a.x, a.y, a.z + 0.06), q, new THREE.Vector3(1, 1, 1));
    mesh.setMatrixAt(k, M);
  });
  mesh.name = 'kerb_blocks';
  return mesh;
}

/** Weathered paint: off-white with speckled wear, tiled along the line (u = metres / 2). */
export function paintWearTexture(): THREE.Texture {
  const cv = document.createElement('canvas');
  cv.width = 128; cv.height = 16;
  const g = cv.getContext('2d')!;
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 128, 16);
  let seed = 3;
  const r = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  for (let k = 0; k < 110; k++) {
    const v = 175 + Math.floor(r() * 60);
    g.fillStyle = `rgb(${v},${v},${v - 6})`;
    g.fillRect(r() * 128, r() * 16, 1 + r() * 3, 1 + r() * 2);
  }
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = THREE.RepeatWrapping;
  t.anisotropy = 8;
  return t;
}

/** White edge lines, painted on the driven surface with the same shading as the kerbs. */
function buildEdgeLines(track: TrackJson, el: NonNullable<SceneryJson['edge_lines']>, ground?: (x: number, y: number) => number, surf?: PaintSurface, stripeM = 2): THREE.Mesh | null {
  const st = new PaintStrips(edgeFrame(track, ground), surf, track.spacing_m || 1);
  const o1 = -el.inset, o0 = -el.inset - el.width;
  for (const r of el.runs) {
    st.add(r.side, r.s0, r.s1, [{ out: o0, dz: 0.008, v: PAINT_V('line', 0) }, { out: o1, dz: 0.008, v: PAINT_V('line', 1) }], o0 - 1.2, r.s0);
  }
  return st.build(kerbPaintTexture(stripeM), 'edge_lines', -8);
}

// ------------------------------------------------------------------ pit-exit cones
let pitExitConesData: PitExitConesJson | null = null;
/** The pit-exit cone line of the last built scenery (null: none). Modes use it with trackmath's PitExitCones. */
export function pitExitConeLine(): PitExitConesJson | null { return pitExitConesData; }
/** A fresh crossing detector for the pit-exit cones (null: the track has none). Feed it the player's ENU x, y each
 *  frame: `if (w?.update(x, y)) …` (hot lap: toast + banner; race: director.reportViolation('pit_exit_cones')). */
export function pitExitConeWatcher(): PitExitCones | null { return pitExitConesData ? new PitExitCones(pitExitConesData) : null; }

/** Traffic cone, 0.7 m: square base, orange body with a white reflective band; vertex colours, merged. */
function coneGeometry(color?: string): THREE.BufferGeometry {
  const ORANGE = new THREE.Color(color ?? 0xd8501c), WHITE = new THREE.Color(0xe6e4dc), BASE = new THREE.Color(color ?? 0xc2461a).multiplyScalar(color ? 0.85 : 1);
  const prof: THREE.Vector2[] = [];
  const H = 0.7, R0 = 0.16, R1 = 0.03;
  for (const h of [0.03, 0.4, 0.4, 0.53, 0.53, H - 0.01]) prof.push(new THREE.Vector2(R0 + (R1 - R0) * (h / H), h));
  prof.push(new THREE.Vector2(0, H));
  const body = new THREE.LatheGeometry(prof, 10);
  const base = new THREE.BoxGeometry(0.38, 0.03, 0.38).translate(0, 0.015, 0);
  const paint = (g: THREE.BufferGeometry, f: (y: number) => THREE.Color) => {
    const p = g.attributes.position as THREE.BufferAttribute, c = new Float32Array(p.count * 3);
    for (let i = 0; i < p.count; i++) { const col = f(p.getY(i)); c[i * 3] = col.r; c[i * 3 + 1] = col.g; c[i * 3 + 2] = col.b; }
    g.setAttribute('color', new THREE.BufferAttribute(c, 3));
    return g;
  };
  // white band 0.40-0.53 m (duplicated profile rows keep its edges sharp), coloured per triangle
  const body2 = body.toNonIndexed();
  const pp = body2.attributes.position as THREE.BufferAttribute, cc = new Float32Array(pp.count * 3);
  for (let t = 0; t < pp.count; t += 3) {
    const ym = (pp.getY(t) + pp.getY(t + 1) + pp.getY(t + 2)) / 3;
    const col = ym > 0.4 && ym < 0.53 ? WHITE : ORANGE;
    for (let k = 0; k < 3; k++) { cc[(t + k) * 3] = col.r; cc[(t + k) * 3 + 1] = col.g; cc[(t + k) * 3 + 2] = col.b; }
  }
  body2.setAttribute('color', new THREE.BufferAttribute(cc, 3));
  body2.deleteAttribute('uv');
  const base2 = paint(base.toNonIndexed(), () => BASE);
  base2.deleteAttribute('uv');
  const g = mergeGeometries([body2, base2])!;
  g.computeVertexNormals();
  return g;
}

/** Delineator post (round 7e, Sonoma owner note 57: the pylons across the drag strip at the T7 fork), 1.0 m: a slim
 *  orange post with two white reflective bands on a dark rubber base; vertex colours, merged. */
function delineatorGeometry(color?: string): THREE.BufferGeometry {
  const ORANGE = new THREE.Color(color ?? 0xe0561c), WHITE = new THREE.Color(0xe6e4dc), BASE = new THREE.Color(0x1c1c1c);
  const H = 1.0, R0 = 0.045, R1 = 0.035;
  const bands: [number, number][] = [[0.72, 0.8], [0.86, 0.94]];
  const rows = [0.04, ...bands.flatMap(([a, b]) => [a, a, b, b]), H - 0.005];
  const prof = rows.map((h) => new THREE.Vector2(R0 + (R1 - R0) * (h / H), h));
  prof.push(new THREE.Vector2(0, H));
  const body = new THREE.LatheGeometry(prof, 8).toNonIndexed();
  const pp = body.attributes.position as THREE.BufferAttribute, cc = new Float32Array(pp.count * 3);
  for (let t = 0; t < pp.count; t += 3) {
    const ym = (pp.getY(t) + pp.getY(t + 1) + pp.getY(t + 2)) / 3;
    const col = bands.some(([a, b]) => ym > a && ym < b) ? WHITE : ORANGE;
    for (let k = 0; k < 3; k++) { cc[(t + k) * 3] = col.r; cc[(t + k) * 3 + 1] = col.g; cc[(t + k) * 3 + 2] = col.b; }
  }
  body.setAttribute('color', new THREE.BufferAttribute(cc, 3));
  body.deleteAttribute('uv');
  const base = new THREE.BoxGeometry(0.3, 0.04, 0.3).translate(0, 0.02, 0).toNonIndexed();
  const bp = base.attributes.position as THREE.BufferAttribute, bc = new Float32Array(bp.count * 3);
  for (let i = 0; i < bp.count; i++) { bc[i * 3] = BASE.r; bc[i * 3 + 1] = BASE.g; bc[i * 3 + 2] = BASE.b; }
  base.setAttribute('color', new THREE.BufferAttribute(bc, 3));
  base.deleteAttribute('uv');
  const g = mergeGeometries([body, base])!;
  g.computeVertexNormals();
  return g;
}

/** Orange cones every spacing_m along the pit-exit cone line, standing on the driven surface. One draw call. */
function buildPitExitCones(c: PitExitConesJson, ground?: (x: number, y: number) => number): THREE.InstancedMesh | null {
  const P = c.pts;
  if (P.length < 2) return null;
  const spots: V3[] = [];
  const step = c.spacing_m || 16;
  let carry = 0;
  for (let k = 0; k + 1 < P.length; k++) {
    const a = P[k], b = P[k + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    for (let d = carry; d < L; d += step) {
      const t = d / L, x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t;
      spots.push([x, y, ground ? ground(x, y) : a[2] + (b[2] - a[2]) * t]);
    }
    carry = ((carry - L) % step + step) % step;
  }
  const deli = c.style === 'delineator', h0 = deli ? 1.0 : 0.7;
  const mesh = new THREE.InstancedMesh(deli ? delineatorGeometry(c.color) : coneGeometry(c.color), new THREE.MeshLambertMaterial({ vertexColors: true }), spots.length);
  const k = (c.size ?? h0) / h0;
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), one = new THREE.Vector3(k, k, k);
  spots.forEach(([x, y, z], i) => {
    q.setFromAxisAngle(up, rand() * Math.PI);
    m.compose(v3(x, y, z), q, one);
    mesh.setMatrixAt(i, m);
  });
  mesh.instanceMatrix.needsUpdate = true;
  mesh.computeBoundingSphere();
  mesh.name = 'pit_exit_cones';
  return mesh;
}

// ------------------------------------------------------------------ text boards, bridges, flag stand
const texCache = new Map<string, THREE.Texture>();
function canvasTex(key: string, w: number, h: number, draw: (g: CanvasRenderingContext2D) => void): THREE.Texture {
  const hit = texCache.get(key);
  if (hit) return hit;
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  draw(cv.getContext('2d')!);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  texCache.set(key, t);
  return t;
}
const FONT = 'system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif';

const BANNER_STYLE: Record<string, [string, string]> = {
  MISSION: ['#c8202c', '#ffffff'], PORSCHE: ['#141414', '#f2f2f2'], WEATHERTECH: ['#f5f5f2', '#b3121d'],
  'TIRE RACK': ['#20262e', '#ffffff'], 'AUTO. HOME. PET. FIND YOUR FIT.': ['#f5f5f2', '#1f3d7a'],
  MOTUL: ['#d71920', '#ffffff'], MICHELIN: ['#27509b', '#ffd400'], kinetic: ['#e9eaeb', '#3a4654'],
};
/** `bg` overrides the board colour (plain coloured ad boards: text '' draws no lettering), `fg` the lettering's. A text
 *  'NAME|#bg|#fg' carries its own colours (Sonoma round 6: the names the footage shows, typed in their observed colours,
 *  no logo artwork, the Laguna rule). */
function bannerTexture(texts: string[], spanM: number, hM: number, bg?: string, fgOver?: string): THREE.Texture {
  const W = 2048, H = Math.max(64, Math.round((W * hM) / spanM));
  return canvasTex(`banner:${texts.join('~')}:${W}x${H}:${bg ?? ''}:${fgOver ?? ''}`, W, H, (g) => {
    const seg = W / texts.length;
    texts.forEach((raw, i) => {
      const [t, tb, tf] = raw.split('|');
      const [bg0, fg0] = BANNER_STYLE[t] ?? ['#1d2a3a', '#f3f3f0'];
      const fg = tf ?? fgOver ?? fg0;
      g.fillStyle = tb ?? bg ?? bg0; g.fillRect(i * seg, 0, seg, H);
      g.fillStyle = 'rgba(255,255,255,0.25)'; g.fillRect(i * seg, 0, 3, H);
      g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle';
      let size = H * 0.72;
      g.font = `800 ${size}px ${FONT}`;
      while (g.measureText(t).width > seg * 0.86 && size > 10) { size -= 2; g.font = `800 ${size}px ${FONT}`; }
      g.fillText(t, i * seg + seg / 2, H * 0.53);
    });
  });
}

/** The T3-T4 TIRE RACK bridge: two curved truss ribs from the ground on each side over the track, cross bracing,
 *  a banner panel hung at deck height and a logo board at the crown. */
function buildArchBridge(b: SceneryJson['bridges'][number], ground?: (x: number, y: number) => number): THREE.Group {
  const g = new THREE.Group();
  const dark = new THREE.MeshLambertMaterial({ color: 0x30353b });
  const [ax, ay] = b.a, [bx, by] = b.b;
  const span = Math.hypot(bx - ax, by - ay);
  const ux = (bx - ax) / span, uy = (by - ay) / span;
  const px = -uy, py = ux; // across the bridge
  const zA = ground ? ground(ax, ay) : b.deck_z - 6, zB = ground ? ground(bx, by) : b.deck_z - 6;
  const crown = b.deck_z + 8; // the real arch rises well above the deck line (onboard frames, T3 exit)
  const N = 28;
  const rib = (off: number) => {
    const pts: THREE.Vector3[] = [];
    for (let k = 0; k <= N; k++) {
      const u = k / N;
      const base = zA + (zB - zA) * u;
      pts.push(v3(ax + (bx - ax) * u + px * off, ay + (by - ay) * u + py * off, base + (crown - base) * Math.sin(Math.PI * u)));
    }
    return pts;
  };
  const r0 = rib(-1.4), r1 = rib(1.4);
  for (const r of [r0, r1]) g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(r), 64, 0.6, 8), dark));
  for (let k = 2; k < N - 1; k += 2) {
    const a = r0[k], c = r1[k];
    const m = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, a.distanceTo(c), 5), dark);
    m.position.copy(a).add(c).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), c.clone().sub(a).normalize());
    g.add(m);
  }
  // banner panel across the middle at deck height, both faces; logo board at the crown
  const midx = (ax + bx) / 2, midy = (ay + by) / 2;
  const yaw = yawFor(Math.atan2(uy, ux)) - Math.PI / 2;
  const panelL = span * 0.5, panelH = 2.6;
  [1, -1].forEach((face, k) => {
    const texts = b.banners[k] ?? b.banners[0] ?? ['TIRE RACK'];
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(panelL, panelH), new THREE.MeshLambertMaterial({ map: bannerTexture(texts, panelL, panelH) }));
    pl.position.copy(v3(midx + px * 1.45 * face, midy + py * 1.45 * face, b.deck_z));
    pl.rotation.y = yaw + (face > 0 ? 0 : Math.PI);
    g.add(pl);
    const logo = new THREE.Mesh(new THREE.PlaneGeometry(12, 1.8), new THREE.MeshLambertMaterial({ map: bannerTexture(texts, 12, 1.8) }));
    logo.position.copy(v3(midx + px * 1.75 * face, midy + py * 1.75 * face, crown - 0.4));
    logo.rotation.y = yaw + (face > 0 ? 0 : Math.PI);
    g.add(logo);
  });
  return g;
}

function buildBridges(list: SceneryJson['bridges'], ground?: (x: number, y: number) => number): THREE.Group {
  const group = new THREE.Group();
  group.name = 'bridges';
  const steel = new THREE.MeshLambertMaterial({ color: 0x9ea3a8 });
  const concrete = new THREE.MeshLambertMaterial({ color: 0xbfbab0 });
  const dark = new THREE.MeshLambertMaterial({ color: 0x2a2d31 });
  for (const b of list) {
    if (b.style === 'arch') { group.add(buildArchBridge(b, ground)); continue; }
    const ax = b.a[0], ay = b.a[1], bx = b.b[0], by = b.b[1];
    const span = Math.hypot(bx - ax, by - ay);
    const head = Math.atan2(by - ay, bx - ax);       // ENU direction along the span
    const yaw = yawFor(head) - Math.PI / 2;          // box X axis along the span
    const mid = v3((ax + bx) / 2, (ay + by) / 2, b.deck_z);
    // style 'sign': an advertising gantry over the track (thin dark truss, a deep banner on both faces, slim legs)
    const sign = b.style === 'sign';
    const foot = b.kind === 'foot' && !sign;
    const deckT = sign ? 0.5 : foot ? 0.9 : 1.3;
    const w = b.width;
    const g = new THREE.Group();
    g.position.copy(mid);
    g.rotation.y = yaw;
    // deck (top at deck_z)
    const deck = new THREE.Mesh(new THREE.BoxGeometry(span, deckT, w), sign ? dark : foot ? steel : concrete);
    deck.position.y = -deckT / 2;
    g.add(deck);
    // side screens with banners from the deck soffit up to the handrail (foot) / parapet (road)
    // footbridge banners hang from the handrail to below the soffit (about 3.6 m, as on the S/F bridge)
    const bh = sign ? 2.6 : foot ? 3.6 : 1.6;
    const bannerY = sign ? -bh / 2 + 0.25 : foot ? 1.1 - bh / 2 : -deckT / 2 + 0.3;
    [0, 1].forEach((face) => {
      const texts = b.banners[face] ?? b.banners[0] ?? [TRACK.short.toUpperCase()];
      const mat = new THREE.MeshLambertMaterial({ map: bannerTexture(texts, span, bh) });
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(span, bh), mat);
      pl.position.set(0, bannerY, (face === 0 ? 1 : -1) * (w / 2 + 0.03));
      if (face === 1) pl.rotation.y = Math.PI;
      g.add(pl);
    });
    if (foot) {
      // roof truss and handrail posts so it reads as the covered footbridge
      const roof = new THREE.Mesh(new THREE.BoxGeometry(span, 0.2, w + 0.4), steel);
      roof.position.y = 2.7;
      g.add(roof);
      for (let x = -span / 2; x <= span / 2 + 0.01; x += 4) {
        for (const zz of [-w / 2, w / 2]) {
          const post = new THREE.Mesh(new THREE.BoxGeometry(0.12, 2.7, 0.12), steel);
          post.position.set(x, 1.35, zz);
          g.add(post);
        }
      }
    }
    group.add(g);
    // abutments and stair flights into the banks where the scenery gives them (bridge `ends`)
    for (const e of b.ends ?? []) {
      const hgt = b.deck_z - e.z_ground;
      if (hgt > 0.2) {
        const ab = new THREE.Mesh(new THREE.BoxGeometry(1.4, hgt + 0.5, w + 0.6), concrete);
        ab.position.copy(v3(e.at[0], e.at[1], e.z_ground - 0.5 + (hgt + 0.5) / 2));
        ab.rotation.y = yaw;
        group.add(ab);
      }
      const dx = e.to[0] - e.at[0], dy = e.to[1] - e.at[1], run = Math.hypot(dx, dy);
      if (run > 0.5) {
        const drop = b.deck_z - e.z_to, len = Math.hypot(run, drop);
        const fl = new THREE.Mesh(new THREE.BoxGeometry(len, 0.35, w), concrete);
        fl.position.copy(v3((e.at[0] + e.to[0]) / 2, (e.at[1] + e.to[1]) / 2, (b.deck_z + e.z_to) / 2 - 0.2));
        fl.rotation.order = 'YXZ';
        fl.rotation.y = yawFor(Math.atan2(dy, dx)) - Math.PI / 2;
        fl.rotation.z = -Math.atan2(drop, run);
        group.add(fl);
      }
    }
    // piers at both ends, down to well below ground (terrain is lower than the deck everywhere near a bridge)
    for (const [x, y] of [b.a, b.b]) {
      const pierH = 30;
      const pier = new THREE.Mesh(new THREE.BoxGeometry(foot || sign ? 0.6 : 1.2, pierH, foot || sign ? 0.6 : w * 0.8), sign ? dark : foot ? steel : concrete);
      pier.position.copy(v3(x, y, b.deck_z - deckT - pierH / 2));
      pier.rotation.y = yaw;
      group.add(pier);
    }
  }
  return group;
}

function boardTexture(kind: string, text: string): THREE.Texture {
  return canvasTex(`board:${kind}:${text}`, 256, 384, (g) => {
    if (kind === 'brake') {
      g.fillStyle = '#f4f4f2'; g.fillRect(0, 0, 256, 384);
      g.strokeStyle = '#111'; g.lineWidth = 14; g.strokeRect(7, 7, 242, 370);
      g.fillStyle = '#111'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.font = `800 300px ${FONT}`; g.fillText(text, 128, 205);
    } else {
      g.fillStyle = '#1b3f8f'; g.fillRect(0, 0, 256, 384);
      g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.font = `700 54px ${FONT}`; g.fillText('TURN', 128, 70);
      g.font = `800 ${text.length > 2 ? 150 : 210}px ${FONT}`; g.fillText(text, 128, 235);
    }
  });
}

/** Open square lattice tower (X-braced panels), base at ENU (x, y, z). */
function latticeTower(x: number, y: number, z: number, h: number, w: number, mat: THREE.Material): THREE.Group {
  const g = new THREE.Group();
  g.position.copy(v3(x, y, z));
  const hw = w / 2, panels = Math.max(3, Math.round(h / 2.5)), ph = h / panels;
  const strut = (a: THREE.Vector3, b: THREE.Vector3, r: number) => {
    const s2 = new THREE.Mesh(new THREE.BoxGeometry(r, a.distanceTo(b), r), mat);
    s2.position.copy(a).add(b).multiplyScalar(0.5);
    s2.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    g.add(s2);
  };
  const C = [[-hw, -hw], [hw, -hw], [hw, hw], [-hw, hw]];
  for (const [cx, cz] of C) strut(new THREE.Vector3(cx, 0, cz), new THREE.Vector3(cx, h, cz), 0.16);
  for (let pi = 0; pi < panels; pi++) {
    const y0 = pi * ph, y1 = (pi + 1) * ph;
    for (let c = 0; c < 4; c++) {
      const [ax, az] = C[c], [bx, bz] = C[(c + 1) % 4];
      strut(new THREE.Vector3(ax, y0, az), new THREE.Vector3(bx, y1, bz), 0.06);
      strut(new THREE.Vector3(ax, y1, az), new THREE.Vector3(bx, y1, bz), 0.06);
    }
  }
  return g;
}

/** Painted lines off the track (scenery.json `paint_lines`): flat white strips just above the paving. */
function buildPaintLines(list: NonNullable<SceneryJson['paint_lines']>): THREE.Group | null {
  const byColor = new Map<string, number[]>();
  for (const l of list) {
    const key = l.color ?? '#e9e8e2';
    const pos = byColor.get(key) ?? (byColor.set(key, []).get(key)!);
    const P = l.pts, hw = l.width / 2;
    for (let i = 0; i + 1 < P.length; i++) {
      const [ax, ay, az] = P[i], [bx, by, bz] = P[i + 1];
      const dx = bx - ax, dy = by - ay, d = Math.hypot(dx, dy) || 1, nx = (-dy / d) * hw, ny = (dx / d) * hw;
      const q = [v3(ax + nx, ay + ny, az), v3(ax - nx, ay - ny, az), v3(bx + nx, by + ny, bz), v3(bx - nx, by - ny, bz)];
      for (const k of [0, 1, 2, 1, 3, 2]) pos.push(q[k].x, q[k].y, q[k].z);
    }
  }
  const grp = new THREE.Group();
  grp.name = 'paint_lines';
  for (const [color, pos] of byColor) {
    if (!pos.length) continue;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ color, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -10 }));
    m.name = 'paint_lines';
    grp.add(m);
  }
  return grp.children.length ? grp : null;
}

/** Raised kerb strips off the lap (scenery.json `kerb_lines`, round 7b): a low box section along each measured line,
 *  coloured stripe / base every stripe_m, standing on the driven ground. Drawn only. */
function buildKerbLines(list: NonNullable<SceneryJson['kerb_lines']>, ground?: (x: number, y: number) => number): THREE.Mesh {
  const pos: number[] = [], col: number[] = [];
  const quad = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3, d: THREE.Vector3, cc: THREE.Color) => {
    for (const p of [a, b, c, a, c, d]) { pos.push(p.x, p.y, p.z); col.push(cc.r, cc.g, cc.b); }
  };
  for (const k of list) {
    const C = k.colors.map((h) => new THREE.Color(h)), hw = k.width / 2, P = k.pts;
    let acc = 0;
    for (let i = 0; i + 1 < P.length; i++) {
      const a = P[i], b = P[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      const nx = (-(b[1] - a[1]) / L) * hw, ny = ((b[0] - a[0]) / L) * hw;
      const g = (x: number, y: number, z: number) => (ground ? ground(x, y) : z);
      const cc = C[Math.floor(acc / k.stripe_m) % C.length];
      const za = Math.max(g(a[0] + nx, a[1] + ny, a[2]), g(a[0] - nx, a[1] - ny, a[2])), zb = Math.max(g(b[0] + nx, b[1] + ny, b[2]), g(b[0] - nx, b[1] - ny, b[2]));
      const A0 = v3(a[0] + nx, a[1] + ny, za - 0.05), A1 = v3(a[0] - nx, a[1] - ny, za - 0.05), B0 = v3(b[0] + nx, b[1] + ny, zb - 0.05), B1 = v3(b[0] - nx, b[1] - ny, zb - 0.05);
      const up = (v: THREE.Vector3) => v.clone().add(new THREE.Vector3(0, k.height + 0.05, 0));
      quad(up(A0), up(A1), up(B1), up(B0), cc);
      quad(A0, up(A0), up(B0), B0, cc.clone().multiplyScalar(0.85));
      quad(A1, B1, up(B1), up(A1), cc.clone().multiplyScalar(0.85));
      if (i === 0) quad(A0, A1, up(A1), up(A0), cc);
      if (i + 2 === P.length) quad(B0, up(B0), up(B1), B1, cc);
      acc += L;
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }));
  m.name = 'kerb_lines';
  return m;
}

/** Painted ground logos (scenery.json `ground_signs`, round 7b): each a grid draped on the driven ground 2 cm up, a
 *  canvas texture with the name typed in the observed colours (no logo artwork). */
function buildGroundSigns(list: NonNullable<SceneryJson['ground_signs']>, ground?: (x: number, y: number) => number): THREE.Group {
  const grp = new THREE.Group();
  grp.name = 'ground_signs';
  for (const gs of list) {
    const tex = canvasTex(`ground:${gs.text}:${gs.fg}:${gs.bg ?? ''}`, 1024, Math.max(64, Math.round((1024 * gs.height) / gs.length)), (g) => {
      const W = g.canvas.width, H = g.canvas.height;
      g.clearRect(0, 0, W, H);
      if (gs.bg) { g.fillStyle = gs.bg; g.fillRect(0, 0, W, H); }
      g.fillStyle = gs.fg;
      let fs = H * 0.9;
      g.font = `bold ${fs}px sans-serif`;
      const w = g.measureText(gs.text).width;
      if (w > W * 0.96) { fs *= (W * 0.96) / w; g.font = `bold ${fs}px sans-serif`; }
      g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillText(gs.text, W / 2, H / 2);
    });
    const NX = 16, NY = 4, ux = Math.cos(gs.heading), uy = Math.sin(gs.heading), vx = -uy, vy = ux;
    const pos: number[] = [], uv: number[] = [], idx: number[] = [];
    for (let j = 0; j <= NY; j++) for (let i = 0; i <= NX; i++) {
      const a = (i / NX - 0.5) * gs.length, b = (j / NY - 0.5) * gs.height;
      const x = gs.x + ux * a + vx * b, y = gs.y + uy * a + vy * b;
      pos.push(x, (ground ? ground(x, y) : gs.z) + 0.02, -y); uv.push(i / NX, j / NY);
    }
    for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
      const k = j * (NX + 1) + i;
      idx.push(k, k + 1, k + NX + 1, k + 1, k + NX + 2, k + NX + 1);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    geo.setIndex(idx);
    geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ map: tex, transparent: true, side: THREE.DoubleSide, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -8 }));
    m.name = 'ground_sign';
    grp.add(m);
  }
  return grp;
}

/** Paved areas (scenery.json `paved_areas`): plain asphalt / concrete laid over the terrain on a 1.5 m grid inside the
 *  outline, so the aerial photo (parked trailers and cars in the NAIP) never shows there as ground. Drawn only. */
function buildPavedAreas(list: NonNullable<SceneryJson['paved_areas']>, ground: (x: number, y: number) => number): THREE.Mesh | null {
  const pos: number[] = [], col: number[] = [];
  const inPoly = (x: number, y: number, P: V2[]) => {
    let c = false;
    for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
      const [xi, yi] = P[i], [xj, yj] = P[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
    }
    return c;
  };
  const D = 1.5;
  for (const a of list) {
    const base = a.surface === 'concrete' ? new THREE.Color(0x9d9b95) : new THREE.Color(0x45474a);
    const xs = a.poly.map((p) => p[0]), ys = a.poly.map((p) => p[1]);
    for (let x = Math.min(...xs); x < Math.max(...xs); x += D) {
      for (let y = Math.min(...ys); y < Math.max(...ys); y += D) {
        if (!inPoly(x + D / 2, y + D / 2, a.poly)) continue;
        const c = [[x, y], [x + D, y], [x, y + D], [x + D, y + D]].map(([px, py]) => v3(px, py, ground(px, py) + 0.04));
        const k = 0.94 + 0.12 * rand();
        for (const i of [0, 1, 2, 1, 3, 2]) { pos.push(c[i].x, c[i].y, c[i].z); col.push(base.r * k, base.g * k, base.b * k); }
      }
    }
  }
  if (!pos.length) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }));
  m.name = 'paved_areas';
  return m;
}

function buildLandmarks(list: SceneryJson['landmarks']): THREE.Group {
  const group = new THREE.Group();
  group.name = 'landmarks';
  const postMat = new THREE.MeshLambertMaterial({ color: 0x5d6166 });
  const backMat = new THREE.MeshLambertMaterial({ color: 0x8a8d90 });
  const white = new THREE.MeshLambertMaterial({ color: 0xf0efea });
  const glass = new THREE.MeshLambertMaterial({ color: 0x27323d });
  for (const m of list) {
    const g = new THREE.Group();
    g.position.copy(v3(m.x, m.y, m.z));
    g.rotation.y = yawFor(m.heading);
    if (m.kind === 'brake' || m.kind === 'corner') {
      const bottom = 0.8;
      const face = new THREE.Mesh(new THREE.PlaneGeometry(m.w, m.h), new THREE.MeshLambertMaterial({ map: boardTexture(m.kind, m.text) }));
      face.position.set(0, bottom + m.h / 2, 0.03);
      const back = new THREE.Mesh(new THREE.BoxGeometry(m.w, m.h, 0.05), backMat);
      back.position.set(0, bottom + m.h / 2, 0);
      g.add(face, back);
      for (const x of [-m.w * 0.35, m.w * 0.35]) {
        const p = new THREE.Mesh(new THREE.BoxGeometry(0.08, bottom + m.h * 0.6, 0.08), postMat);
        p.position.set(x, (bottom + m.h * 0.6) / 2 - 0.2, -0.06);
        g.add(p);
      }
    } else if (m.kind === 'flagstand') {
      // starter's stand on the pit wall: white open frame, glazed cabin, flat roof
      const legH = m.h - 2.6;
      for (const [x, z] of [[-1, -0.8], [1, -0.8], [-1, 0.8], [1, 0.8]]) {
        const leg = new THREE.Mesh(new THREE.BoxGeometry(0.18, legH, 0.18), white);
        leg.position.set(x * (m.w / 2 - 0.2), legH / 2, z);
        g.add(leg);
      }
      // lattice: horizontal rings and X-braces on all four faces, three panels high
      const hx = m.w / 2 - 0.2, hz = 0.8, panels = 3, ph = legH / panels;
      const strut = (a: THREE.Vector3, b: THREE.Vector3) => {
        const len = a.distanceTo(b);
        const s2 = new THREE.Mesh(new THREE.BoxGeometry(0.07, len, 0.07), white);
        s2.position.copy(a).add(b).multiplyScalar(0.5);
        s2.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
        g.add(s2);
      };
      const corners = [[-hx, -hz], [hx, -hz], [hx, hz], [-hx, hz]];
      for (let pi = 0; pi < panels; pi++) {
        const y0 = pi * ph, y1 = (pi + 1) * ph;
        for (let c = 0; c < 4; c++) {
          const [ax, az] = corners[c], [bx, bz] = corners[(c + 1) % 4];
          strut(new THREE.Vector3(ax, y0, az), new THREE.Vector3(bx, y1, bz));
          strut(new THREE.Vector3(bx, y0, bz), new THREE.Vector3(ax, y1, az));
          strut(new THREE.Vector3(ax, y1, az), new THREE.Vector3(bx, y1, bz));
        }
      }
      const cabin = new THREE.Mesh(new THREE.BoxGeometry(m.w, 2.0, 2.0), white);
      cabin.position.set(0, legH + 1.0, 0);
      const win = new THREE.Mesh(new THREE.BoxGeometry(m.w * 0.86, 0.9, 2.04), glass);
      win.position.set(0, legH + 1.25, 0);
      const roof = new THREE.Mesh(new THREE.BoxGeometry(m.w + 0.5, 0.18, 2.6), white);
      roof.position.set(0, legH + 2.1, 0);
      g.add(cabin, win, roof);
    } else if (m.kind === 'banner' || m.kind === 'sign') {
      // ad board facing the track (two posts) or a sign on a wall at z (no posts)
      const bottom = m.kind === 'banner' ? 0.25 : 0;
      const tex = bannerTexture([m.text], m.w, m.h, m.color, m.fg);
      const face = new THREE.Mesh(new THREE.PlaneGeometry(m.w, m.h), new THREE.MeshLambertMaterial({ map: tex, side: THREE.DoubleSide }));
      face.position.set(0, bottom + m.h / 2, 0.04);
      g.add(face);
      if (m.kind === 'banner') {
        for (const x of [-m.w * 0.4, m.w * 0.4]) {
          const p = new THREE.Mesh(new THREE.BoxGeometry(0.08, bottom + m.h, 0.08), postMat);
          p.position.set(x, (bottom + m.h) / 2, -0.04);
          g.add(p);
        }
      }
    } else if (m.kind === 'marshal') {
      // corner-worker post (round 7, Sonoma owner note 40: the old post read as a small grey box): a platform on four legs
      // (deck at h - 2.6 m), a hut w x w (default 2.4 m) with an OPEN FRONT toward the track (+Z after yawFor faces the
      // heading), white walls with a coloured lower band (m.color, from the frames), a flat roof overhanging 0.6 m, and a
      // railing round the deck. style 'platform': deck and railing only. Round 8 (Sonoma owner note 61): a measured
      // footprint gives the hut w across x d along the heading (absent: w x w) and m.roof the roof colour (absent: white).
      const W = m.w || 2.4, D = m.d ?? W, legH = Math.max(0.6, m.h - 2.6), wallH = 2.2, t = 0.08;
      const band = new THREE.MeshLambertMaterial({ color: m.color ?? '#2f5d9e' });
      const roofMat = m.roof ? new THREE.MeshLambertMaterial({ color: m.roof }) : white;
      const box = (sx: number, sy: number, sz: number, x: number, y: number, z: number, mat: THREE.Material) => {
        const b2 = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat); b2.position.set(x, y, z); g.add(b2);
      };
      for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) box(0.16, legH, 0.16, x * (W / 2 - 0.1), legH / 2, z * (D / 2 - 0.1), white);
      for (const z of [-1, 1]) box(W, 0.08, 0.08, 0, legH * 0.45, z * (D / 2 - 0.1), white);   // leg braces
      box(W + 0.4, 0.14, D + 0.4, 0, legH, 0, white);                                          // deck
      if (m.style !== 'platform') {
        const y0 = legH + 0.07, bandH = Math.min(0.9, wallH * 0.4);
        // back wall and the two side walls: coloured band below, white above; the front (track side) open
        box(W, bandH, t, 0, y0 + bandH / 2, -D / 2 + t / 2, band);
        box(W, wallH - bandH, t, 0, y0 + bandH + (wallH - bandH) / 2, -D / 2 + t / 2, white);
        for (const x of [-1, 1]) {
          box(t, bandH, D, x * (W / 2 - t / 2), y0 + bandH / 2, 0, band);
          box(t, wallH - bandH, D, x * (W / 2 - t / 2), y0 + bandH + (wallH - bandH) / 2, 0, white);
        }
        box(W, bandH, t, 0, y0 + bandH / 2, D / 2 - t / 2, band);                               // low front sill (band colour)
        for (const x of [-1, 1]) box(0.12, wallH, 0.12, x * (W / 2 - 0.06), y0 + wallH / 2, D / 2 - 0.06, white);  // front posts
        box(W + 1.2, 0.14, D + 1.2, 0, y0 + wallH + 0.07, 0.15, roofMat);                        // roof, 0.6 m overhang
        box(W + 1.2, 0.05, D + 1.2, 0, y0 + wallH - 0.01, 0.15, postMat);                         // its dark underside
      } else {
        for (const [x, z, sx, sz] of [[0, D / 2 + 0.2, W + 0.4, 0.05], [-W / 2 - 0.2, 0, 0.05, D + 0.4], [W / 2 + 0.2, 0, 0.05, D + 0.4]] as const) {
          box(sx, 0.05, sz, x, legH + 1.0, z, postMat);
        }
      }
      // railing on the deck's open sides (the deck is 0.2 m wider than the hut all round)
      for (const [x, z, sx, sz] of [[0, D / 2 + 0.18, W + 0.4, 0.05]] as const) box(sx, 0.05, sz, x, legH + 1.0, z, postMat);
      for (const x of [-W / 2 - 0.18, 0, W / 2 + 0.18]) box(0.05, 1.0, 0.05, x, legH + 0.5, D / 2 + 0.18, postMat);
    } else if (m.kind === 'block') {
      // free-standing concrete block (round 7, Sonoma owner note 38: the T11 apex blocks): w across, d along the heading,
      // h high; style 'striped' paints alternating red / white bands across it (color = the red), else plain m.color
      const W = m.w, Dd = m.d ?? m.w, H = m.h;
      if (m.style === 'striped') {
        const nb = Math.max(2, Math.round(Dd / 0.5));
        for (let k = 0; k < nb; k++) {
          const blk = new THREE.Mesh(new THREE.BoxGeometry(W, H, Dd / nb), new THREE.MeshLambertMaterial({ color: k % 2 ? 0xf0efea : (m.color ?? '#c0392b') }));
          blk.position.set(0, H / 2, -Dd / 2 + (k + 0.5) * (Dd / nb));
          g.add(blk);
        }
      } else {
        const blk = new THREE.Mesh(new THREE.BoxGeometry(W, H, Dd), new THREE.MeshLambertMaterial({ color: m.color ?? '#f0efea' }));
        blk.position.set(0, H / 2, 0);
        g.add(blk);
      }
    } else if (m.kind === 'impact') {
      // impact barrier (water-filled / foam block) at a wall's nose: a plain block, w across, d along the heading
      const blk = new THREE.Mesh(new THREE.BoxGeometry(m.w, m.h, m.d ?? 2), new THREE.MeshLambertMaterial({ color: m.color ?? '#e8c21c' }));
      blk.position.set(0, m.h / 2, 0);
      g.add(blk);
    } else if (m.kind === 'tyres') {
      // free-standing tyre stack (style 'tyres': tyres lying flat, 0.21 m a layer) or a painted barrier block (style
      // 'blocks', red / white bands), 21 Oct 2026; drawn only, not in the collision world
      if (m.style === 'blocks') {
        const bands = Math.max(1, Math.round(m.h / 0.25));
        for (let k = 0; k < bands; k++) {
          const blk = new THREE.Mesh(new THREE.BoxGeometry(m.w, m.h / bands, m.w * 1.6),
            new THREE.MeshLambertMaterial({ color: k % 2 ? 0xf0efea : (m.color ?? '#c0392b') }));
          blk.position.set(0, (k + 0.5) * (m.h / bands), 0);
          g.add(blk);
        }
      } else {
        const layers = Math.max(1, Math.round(m.h / 0.21));
        const tyreMat = new THREE.MeshLambertMaterial({ color: m.color ?? '#1d1e20' });
        for (let k = 0; k < layers; k++) {
          const t = new THREE.Mesh(new THREE.CylinderGeometry(m.w / 2, m.w / 2, 0.2, 14), tyreMat);
          t.position.set(0, 0.1 + k * 0.21, 0);
          g.add(t);
        }
      }
    } else if (m.kind === 'mast') {
      // light mast: a tapered grey pole with a lamp frame on top
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.22, m.h, 8), postMat);
      pole.position.set(0, m.h / 2, 0);
      const head = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.0, 0.3), backMat);
      head.position.set(0, m.h + 0.3, 0);
      g.add(pole, head);
    } else if (m.kind === 'gantry' && m.x2 !== undefined && m.y2 !== undefined) {
      // two white lattice towers either side of the track with cables between their tops
      group.add(latticeTower(m.x, m.y, m.z, m.h, m.w, white), latticeTower(m.x2, m.y2, m.z2 ?? m.z, m.h, m.w, white));
      const A = v3(m.x, m.y, m.z + m.h - 0.3), B = v3(m.x2, m.y2, (m.z2 ?? m.z) + m.h - 0.3);
      for (const dz of [0, -1.2, -2.4]) {
        const a = A.clone().add(new THREE.Vector3(0, dz, 0)), b = B.clone().add(new THREE.Vector3(0, dz, 0));
        const mid = a.clone().add(b).multiplyScalar(0.5).add(new THREE.Vector3(0, -0.6, 0)); // slight sag
        group.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(a, mid, b), 20, 0.03, 4), postMat));
      }
      continue;
    } else {
      continue; // 'oak' is a marker on a tree that is already in the tree list
    }
    group.add(g);
  }
  return group;
}

/** `drawn`: the height of the terrain mesh as drawn (a 3 m triangulation of the heightfield, sunk under the ribbons);
 *  the hillside terraces sit on it (liftTerraces). */
export function buildScenery(track: TrackJson, _hf: Float32Array, sc: SceneryAssets, _maxAniso: number, ground?: (x: number, y: number) => number, paint?: PaintSurface, drawn?: (x: number, y: number) => number): THREE.Group {
  const root = new THREE.Group();
  root.name = 'scenery';
  const j = sc.json;
  const far = buildFar(track, sc);
  if (far) root.add(far);
  const packs = [{ p: j.trees, far: false }];
  if (j.far_trees) packs.push({ p: j.far_trees, far: true });
  // no tree within reach of the track, the pit lane or a paved zone
  const driveable = [...track.center, ...(j.pit_lane?.parts ?? []).flatMap((p) => p.center), ...(j.paved_zones?.parts ?? []).flatMap((p) => p.center)];
  const dist = trackDistance({ center: driveable as TrackJson['center'] });
  root.add(buildTrees(packs, (x, y, r) => keepTreeClear(dist(x, y), r)));
  const stands = (j.buildings ?? []).filter((b) => b.kind === 'grandstand');
  const others = (j.buildings ?? []).filter((b) => b.kind !== 'grandstand');
  if (others.length) root.add(buildBuildings(track, others));
  if (stands.length) root.add(buildBuildings(track, stands, true));
  const terr = j.terraces?.length ? liftTerraces(j.terraces, drawn ?? ground) : [];
  if (terr.length) { const t = buildTerraces(terr); if (t) root.add(t); }
  if (j.structures?.length) root.add(buildStructures(j.structures, terr, ground, (text, bg, fg, w, h) => bannerTexture([text], w, h, bg, fg)));
  // barrier feet and kerbs follow the drawn/driven surface (the track shoulder differs from the raw heightfield)
  const snap = (P: V3[]): V3[] => (ground ? P.map(([x, y]) => [x, y, ground(x, y)] as V3) : P);
  if (j.barriers?.length) root.add(buildBarriers(j.barriers.map((b) => ({ ...b, pts: snap(b.pts) }))));
  if (j.sausages?.strips?.length) { const m = buildSausages(track, j.sausages, ground); if (m) root.add(m); }
  // kind 'blocks' (Sonoma T1, 20 Oct 2026): a dotted line of low grey kerb blocks, not a painted strip
  const blockStrips = (j.kerbs?.strips ?? []).filter((s) => s.kind === 'blocks');
  if (blockStrips.length) { const m = buildKerbBlocks(track, blockStrips, ground); if (m) root.add(m); }
  const kerbs = j.kerbs ? buildKerbs(track, blockStrips.length ? { ...j.kerbs, strips: j.kerbs.strips.filter((s) => s.kind !== 'blocks') } : j.kerbs, ground, paint) : null;
  if (kerbs) root.add(kerbs);
  const lines = j.edge_lines ? buildEdgeLines(track, j.edge_lines, ground, paint, j.kerbs?.stripe_m) : null;
  if (lines) root.add(lines);
  pitExitConesData = j.pit_exit_cones ?? null;
  const cones = j.pit_exit_cones ? buildPitExitCones(j.pit_exit_cones, ground) : null;
  if (cones) root.add(cones);
  for (const cl of j.cone_lines ?? []) {
    const m = buildPitExitCones({ spacing_m: cl.spacing_m, s0: 0, s1: 0, pts: cl.pts, color: cl.color, size: cl.size, style: cl.style }, ground);
    if (m) { m.name = 'cone_line'; root.add(m); }
  }
  if (j.paint_lines?.length) { const m = buildPaintLines(j.paint_lines); if (m) root.add(m); }
  if (j.ground_signs?.length) { const m = buildGroundSigns(j.ground_signs, ground); if (m) root.add(m); }
  if (j.kerb_lines?.length) root.add(buildKerbLines(j.kerb_lines, ground));
  if (j.paved_areas?.length && ground) { const m = buildPavedAreas(j.paved_areas, ground); if (m) root.add(m); }
  if (j.bridges?.length) root.add(buildBridges(j.bridges, ground));
  if (j.landmarks?.length) root.add(buildLandmarks(j.landmarks));
  root.traverse((o) => { o.castShadow = false; if (o.name !== 'kerbs' && o.name !== 'edge_lines') o.receiveShadow = false; o.matrixAutoUpdate = false; o.updateMatrix(); });
  return root;
}
