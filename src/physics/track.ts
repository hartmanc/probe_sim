// Track geometry: Surface from track.json + heightfield, projector, lineToWorld.

import type { Surface, SurfaceSample, Vec3 } from './types';

/** Mirrors public/tracks/<track>/track.json (CONTRACTS.md §2). */
export interface TrackJson {
  name: string;
  origin: { lat: number; lon: number };
  z0_navd88: number;
  direction: string;
  spacing_m: number;
  n: number;
  length_m: number;
  center: Vec3[];
  left: Vec3[];
  right: Vec3[];
  profile: { fractions: number[]; z: number[][] };
  start_finish: { index: number };
  corners: { name: string; s: number }[];
  heightfield: { file: string; x0: number; y0: number; dx: number; nx: number; ny: number };
  ortho?: { file: string; x0: number; y0: number; x1: number; y1: number; width_px: number; height_px: number };
  sources?: string;
}

/** Pit lane (scenery.json `pit_lane`, CONTRACTS §2b): open polylines with the track's centre/left/right/profile
 *  layout (one 7-value profile row per station, fractions as the track's). */
export interface PitLaneJson {
  spacing_m: number;
  fractions: number[];
  parts: { n: number; center: Vec3[]; left: Vec3[]; right: Vec3[]; profile_z: number[][] }[];
}

/** Raised "sausage" kerbs (scenery.json `sausages`): a half-elliptical concrete hump `width` m wide and `height` m
 *  high laid `gap` m beyond the painted kerb (`kerb_width`) on the inside of an apex, between stations s0..s1 on
 *  `side` (+1 left). Running over one lifts the wheel by up to `height` with a steep normal: it upsets the car. */
export interface SausageJson {
  width: number; height: number; gap: number; kerb_width: number;
  strips: { side: number; s0: number; s1: number; corner?: string }[];
}

interface SausageStrip { xs: Float64Array; ys: Float64Array; tx: Float64Array; ty: Float64Array; len: Float64Array; L: number; minx: number; maxx: number; miny: number; maxy: number }

/** Each strip's centreline (1 m points) from the track edges, plus a bounding box for the cheap reject. */
function buildSausageStrips(track: TrackJson, j: SausageJson): SausageStrip[] {
  const n = track.n, sp = track.spacing_m || 1;
  const off = j.kerb_width + j.gap + j.width / 2;
  const out: SausageStrip[] = [];
  for (const st of j.strips) {
    const i0 = Math.round(st.s0 / sp), i1 = Math.round(st.s1 / sp);
    const m = i1 - i0 + 1;
    if (m < 2) continue;
    const xs = new Float64Array(m), ys = new Float64Array(m);
    for (let k = 0; k < m; k++) {
      const i = (((i0 + k) % n) + n) % n;
      const a = track.center[(i - 1 + n) % n], b = track.center[(i + 1) % n];
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      const e = st.side > 0 ? track.left[i] : track.right[i];
      xs[k] = e[0] + (-dy / l) * st.side * off;
      ys[k] = e[1] + (dx / l) * st.side * off;
    }
    const tx = new Float64Array(m - 1), ty = new Float64Array(m - 1), len = new Float64Array(m - 1);
    let L = 0, minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
    for (let k = 0; k < m - 1; k++) {
      const dx = xs[k + 1] - xs[k], dy = ys[k + 1] - ys[k], l = Math.hypot(dx, dy) || 1e-6;
      tx[k] = dx / l; ty[k] = dy / l; len[k] = l; L += l;
    }
    for (let k = 0; k < m; k++) { minx = Math.min(minx, xs[k]); maxx = Math.max(maxx, xs[k]); miny = Math.min(miny, ys[k]); maxy = Math.max(maxy, ys[k]); }
    const pad = j.width / 2 + 0.5;
    out.push({ xs, ys, tx, ty, len, L, minx: minx - pad, maxx: maxx + pad, miny: miny - pad, maxy: maxy + pad });
  }
  return out;
}

/** Ends ramp down over this length (m). */
export const SAUSAGE_RAMP_M = 1.5;
/** The wheel is a point contact, so the hump is widened by the tyre's footprint on a step of its height (a 0.3 m tyre
 *  starts climbing a 6 cm hump ~0.19 m before its centre reaches it) and shaped as a raised cosine: the car feels a
 *  bump, not a wall. (Owner, 18 Oct 2026: 13 cm with steep flanks rolled the car every time.) */
export const SAUSAGE_TYRE_R = 0.3;
export const SAUSAGE_MAX_SLOPE = 0.6;

/** Hump height and world gradient at (x, y); h = 0 when clear of every strip. */
function sausageAt(strips: SausageStrip[], j: SausageJson, x: number, y: number, out: { h: number; gx: number; gy: number }): void {
  out.h = 0; out.gx = 0; out.gy = 0;
  const Wh = j.width / 2 + Math.sqrt(2 * SAUSAGE_TYRE_R * j.height);
  for (const s of strips) {
    if (x < s.minx || x > s.maxx || y < s.miny || y > s.maxy) continue;
    let bestD = Infinity, bk = -1, bt = 0, u = 0, acc = 0;
    for (let k = 0; k < s.len.length; k++) {
      const dx = x - s.xs[k], dy = y - s.ys[k];
      let t = (dx * s.tx[k] + dy * s.ty[k]) / s.len[k];
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      const px = dx - t * s.len[k] * s.tx[k], py = dy - t * s.len[k] * s.ty[k];
      const d2 = px * px + py * py;
      if (d2 < bestD) { bestD = d2; bk = k; bt = t; u = acc + t * s.len[k]; }
      acc += s.len[k];
    }
    if (bk < 0) continue;
    const dx = x - s.xs[bk], dy = y - s.ys[bk];
    const d = -dx * s.ty[bk] + dy * s.tx[bk];            // signed lateral distance (+left of the strip)
    const q = d / Wh;
    if (q <= -1 || q >= 1) continue;
    const ramp = Math.min(1, Math.min(u, s.L - u) / SAUSAGE_RAMP_M);
    if (ramp <= 0) continue;
    // raised cosine over the tyre-widened half-width: continuous height and slope at the edges
    const h = j.height * 0.5 * (1 + Math.cos(Math.PI * q)) * ramp;
    let slope = -j.height * 0.5 * Math.PI * Math.sin(Math.PI * q) / Wh * ramp;   // dh/dd
    if (slope > SAUSAGE_MAX_SLOPE) slope = SAUSAGE_MAX_SLOPE; else if (slope < -SAUSAGE_MAX_SLOPE) slope = -SAUSAGE_MAX_SLOPE;
    if (h > out.h) { out.h = h; out.gx = slope * -s.ty[bk]; out.gy = slope * s.tx[bk]; }
  }
}

/** Raised kerb profile (scenery.json `kerbs.profile`, 20 Oct 2026): a concrete kerb `height` m high whose track-side face
 *  rises over `face` m (smoothstep) to a flat top, and whose back drops to the ground over `back` m beyond the band.
 *  Absent = flat paint at road level (Laguna). Sonoma: the stepped concrete kerbs (owner: "more aggressive, you can feel
 *  it in the car"; Street View J6fsnW4hj4xCjQLzrgRGzA / gd1SNdksCq5QZtwlsrzR7g, a sloped face of ~10-15 cm). */
export interface KerbProfileJson { height: number; face: number; back: number }
/** scenery.json `kerbs` as the physics reads it: band [edge - width, edge] on `side` (inside the edge) or, with a strip's
 *  `off`, a band `width` wide centred `off` m beyond the edge. */
export interface KerbsJson {
  width: number; inside?: boolean; profile?: KerbProfileJson | null;
  strips: { side: number; s0: number; s1: number; kind?: string; off?: number;
    /** a run's own raised profile (Buttonwillow's T9 kerb, 21 Oct 2026) on top of the track default `profile`; absent: the
     *  default (flat paint when the track has none) */
    profile?: KerbProfileJson | null;
    /** a run's own band width (Buttonwillow round 8); absent: the track's `width` */
    width?: number }[];
}

/** The kerb band's centre offset beyond the edge (m, + outside) of a strip. */
export function kerbBandCentre(k: KerbsJson, st: { off?: number }): number {
  return st.off !== undefined ? st.off : (k.inside ?? true) ? -k.width / 2 : k.width / 2;
}

/** Each raised kerb strip's centreline (1 m points beyond/inside the edge) in the sausage strip layout. */
function buildKerbStrips(track: TrackJson, k: KerbsJson): (SausageStrip & { side: number; pr: KerbProfileJson; hw: number })[] {
  const out: (SausageStrip & { side: number; pr: KerbProfileJson; hw: number })[] = [];
  for (const st of k.strips) {
    if (st.kind === 'verge' || st.kind === 'blocks') continue; // 'blocks': a line of low kerb blocks, drawn only (20 Oct 2026)
    const pr = st.profile ?? k.profile;
    if (!pr) continue;                                          // flat paint: no height
    const off = kerbBandCentre(k, st), w = st.width ?? k.width;
    // reuse the sausage layout: kerb_width + gap + width/2 = off
    const ss = buildSausageStrips(track, { width: w, height: 0, gap: 0, kerb_width: off - w / 2, strips: [st] });
    for (const s2 of ss) { s2.minx -= 1; s2.maxx += 1; s2.miny -= 1; s2.maxy += 1; out.push({ ...s2, side: st.side, pr, hw: w / 2 }); }
  }
  return out;
}

const smooth01 = (t: number) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
const dsmooth01 = (t: number) => (t <= 0 || t >= 1 ? 0 : 6 * t * (1 - t));

/** Kerb hump height and world gradient at (x, y) (h = 0 clear of every strip). o = outward distance from the band centre. */
function kerbAt(strips: (SausageStrip & { side: number; pr: KerbProfileJson; hw: number })[], k: KerbsJson, x: number, y: number, out: { h: number; gx: number; gy: number }): void {
  out.h = 0; out.gx = 0; out.gy = 0;
  for (const s of strips) {
    const pr = s.pr, H = pr.height, hw = s.hw;
    if (x < s.minx || x > s.maxx || y < s.miny || y > s.maxy) continue;
    let bestD = Infinity, bk = -1, u = 0, acc = 0;
    for (let q = 0; q < s.len.length; q++) {
      const dx = x - s.xs[q], dy = y - s.ys[q];
      let t = (dx * s.tx[q] + dy * s.ty[q]) / s.len[q];
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      const px = dx - t * s.len[q] * s.tx[q], py = dy - t * s.len[q] * s.ty[q];
      const d2 = px * px + py * py;
      if (d2 < bestD) { bestD = d2; bk = q; u = acc + t * s.len[q]; }
      acc += s.len[q];
    }
    if (bk < 0) continue;
    const dx = x - s.xs[bk], dy = y - s.ys[bk];
    const o = (-dx * s.ty[bk] + dy * s.tx[bk]) * s.side;   // + away from the track
    if (o < -hw || o > hw + pr.back) continue;
    const ramp = Math.min(1, Math.min(u, s.L - u) / SAUSAGE_RAMP_M);
    if (ramp <= 0) continue;
    let h: number, dhdo: number;
    if (o < -hw + pr.face) { const t = (o + hw) / pr.face; h = H * smooth01(t); dhdo = (H * dsmooth01(t)) / pr.face; }
    else if (o <= hw) { h = H; dhdo = 0; }
    else { const t = (o - hw) / pr.back; h = H * (1 - smooth01(t)); dhdo = (-H * dsmooth01(t)) / pr.back; }
    h *= ramp; dhdo *= ramp;
    if (dhdo > SAUSAGE_MAX_SLOPE) dhdo = SAUSAGE_MAX_SLOPE; else if (dhdo < -SAUSAGE_MAX_SLOPE) dhdo = -SAUSAGE_MAX_SLOPE;
    if (h > out.h) {
      // d(o)/d(world) = side * (-ty, tx)
      out.h = h; out.gx = dhdo * s.side * -s.ty[bk]; out.gy = dhdo * s.side * s.tx[bk];
    }
  }
}

export interface TrackSurfaceOptions {
  /** Raised sausage kerbs beyond the apex kerbs (scenery.json `sausages`); null / absent = none. */
  sausages?: SausageJson | null;
  /** scenery.json `kerbs`: raised only when it carries a `profile` (Sonoma); flat paint otherwise (no height). */
  kerbs?: KerbsJson | null;
  /** Paved pit lane: mu = muOnTrack and profile heights inside its footprint; it blends to the heightfield over the
   *  same shoulder width as the track. onTrack stays false there; `paved` is true. */
  pitLane?: PitLaneJson | null;
  /** Far heightfield (scenery.json `far.heightfield` grid + decoded far_heightfield.bin), used outside the near grid. */
  far?: { heightfield: Float32Array; x0: number; y0: number; dx: number; nx: number; ny: number } | null;
  /** Friction multiplier on the racing surface. Default 1.0. */
  muOnTrack?: number;
  /** Friction multiplier off pavement (dry Laguna dirt / dry grass). Default OFF_PAVEMENT_MU (0.72). A car's
   *  car.json `surfaces.offPavementMu` overrides it in the Vehicle (see NOTES-surface.md). */
  muOffTrack?: number;
  /** Width past the paved edge over which mu (and the `dirt` weight) blend from pavement to dirt, m.
   *  Default SURFACE_GRIP_BLEND_M (1 m). */
  gripBlend?: number;
  /** Peak amplitude of the low-frequency ground roughness off pavement, m (0 disables). Default DIRT_ROUGHNESS_M. */
  roughness?: number;
  /** Width beyond the edge over which the height blends from the profile edge to the heightfield, m.
   *  Default SHOULDER_WIDTH_M (5 m), the same shoulder the app renders, so the car drives on what is drawn. */
  edgeBlend?: number;
}

/** Shoulder width outside each track edge: heights blend linearly from the ribbon edge to the heightfield.
 *  The app's ribbon shoulder (src/app/scene.ts) samples this surface, so keep the two in step. */
export const SHOULDER_WIDTH_M = 5.0;

/** Off-pavement friction relative to pavement: a 200-treadwear street tyre on dry hard-packed dirt / dry grass
 *  keeps roughly 0.65-0.8 of its asphalt grip (see NOTES-surface.md). */
export const OFF_PAVEMENT_MU = 0.72;
/** Grip blends from pavement to dirt over this distance past the paved edge (smoothstep), m. */
export const SURFACE_GRIP_BLEND_M = 1.0;
/** Peak amplitude of the off-pavement ground undulation, m (three long-wavelength waves, seeded by position). */
export const DIRT_ROUGHNESS_M = 0.012;

// Roughness: three plane waves (wavelengths 3.7, 5.3 and 8.9 m, odd directions so the pattern never lines up with
// the track), amplitude split 0.4/0.35/0.25. Deterministic in (x, y); faded in with the dirt weight.
const RW = [
  { kx: (2 * Math.PI / 3.7) * Math.cos(0.41), ky: (2 * Math.PI / 3.7) * Math.sin(0.41), a: 0.4, ph: 1.3 },
  { kx: (2 * Math.PI / 5.3) * Math.cos(2.17), ky: (2 * Math.PI / 5.3) * Math.sin(2.17), a: 0.35, ph: 4.1 },
  { kx: (2 * Math.PI / 8.9) * Math.cos(-1.05), ky: (2 * Math.PI / 8.9) * Math.sin(-1.05), a: 0.25, ph: 2.6 },
];

/** Decode heightfield.bin (float32 little-endian). */
export function loadHeightfield(buffer: ArrayBuffer): Float32Array {
  if (buffer.byteLength % 4 !== 0) throw new Error('heightfield: byte length is not a multiple of 4');
  const n = buffer.byteLength / 4;
  const out = new Float32Array(n);
  const dv = new DataView(buffer);
  for (let i = 0; i < n; i++) out[i] = dv.getFloat32(4 * i, true);
  return out;
}

// ---------------------------------------------------------------------------
// Precomputed geometry, cached per TrackJson object.

interface Geo {
  n: number;
  spacing: number;
  length: number;
  cx: Float64Array; cy: Float64Array;
  tx: Float64Array; ty: Float64Array;   // unit direction of segment i → i+1
  segLen: Float64Array;
  halfL: Float64Array; halfR: Float64Array;
  nf: number;
  fr: Float64Array;                      // profile fractions
  pz: Float64Array;                      // profile z, n × nf
  // spatial hash over station positions
  cell: number; gx0: number; gy0: number; gnx: number; gny: number;
  cellStart: Int32Array; cellItems: Int32Array;
  maxHalf: number;
}

const geoCache = new WeakMap<TrackJson, Geo>();

function getGeo(track: TrackJson): Geo {
  let g = geoCache.get(track);
  if (!g) { g = buildGeo(track); geoCache.set(track, g); }
  return g;
}

function buildGeo(t: TrackJson): Geo {
  const n = t.n | 0;
  if (!(n >= 3) || t.center.length < n || t.left.length < n || t.right.length < n || t.profile.z.length < n) {
    throw new Error('track.json: n and the station arrays are inconsistent');
  }
  const cx = new Float64Array(n), cy = new Float64Array(n);
  for (let i = 0; i < n; i++) { cx[i] = t.center[i][0]; cy[i] = t.center[i][1]; }
  const tx = new Float64Array(n), ty = new Float64Array(n), segLen = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const dx = cx[j] - cx[i], dy = cy[j] - cy[i];
    const l = Math.hypot(dx, dy) || 1e-9;
    tx[i] = dx / l; ty[i] = dy / l; segLen[i] = l;
  }
  const halfL = new Float64Array(n), halfR = new Float64Array(n);
  let maxHalf = 0;
  for (let i = 0; i < n; i++) {
    halfL[i] = Math.max(0.5, Math.hypot(t.left[i][0] - cx[i], t.left[i][1] - cy[i]));
    halfR[i] = Math.max(0.5, Math.hypot(t.right[i][0] - cx[i], t.right[i][1] - cy[i]));
    maxHalf = Math.max(maxHalf, halfL[i], halfR[i]);
  }
  const fr = Float64Array.from(t.profile.fractions);
  const nf = fr.length;
  const pz = new Float64Array(n * nf);
  for (let i = 0; i < n; i++) for (let k = 0; k < nf; k++) pz[i * nf + k] = t.profile.z[i][k];

  // hash: cell large enough that a point within (maxHalf + margin) of a station
  // finds it in the 3×3 neighbourhood
  const spacing = t.spacing_m;
  const cell = Math.max(8, maxHalf + 2 * spacing + 4);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (let i = 0; i < n; i++) { x0 = Math.min(x0, cx[i]); y0 = Math.min(y0, cy[i]); x1 = Math.max(x1, cx[i]); y1 = Math.max(y1, cy[i]); }
  const gx0 = x0 - cell, gy0 = y0 - cell;
  const gnx = Math.ceil((x1 - gx0) / cell) + 2, gny = Math.ceil((y1 - gy0) / cell) + 2;
  const counts = new Int32Array(gnx * gny + 1);
  const cellOf = (i: number) => Math.floor((cx[i] - gx0) / cell) + gnx * Math.floor((cy[i] - gy0) / cell);
  for (let i = 0; i < n; i++) counts[cellOf(i) + 1]++;
  for (let c = 0; c < gnx * gny; c++) counts[c + 1] += counts[c];
  const cellStart = counts;
  const fill = cellStart.slice(0, gnx * gny);
  const cellItems = new Int32Array(n);
  for (let i = 0; i < n; i++) cellItems[fill[cellOf(i)]++] = i;
  return { n, spacing, length: t.length_m, cx, cy, tx, ty, segLen, halfL, halfR, nf, fr, pz, cell, gx0, gy0, gnx, gny, cellStart, cellItems, maxHalf };
}

/** Result of locating a point against the centreline (reused object). */
interface Loc { found: boolean; seg: number; t: number; lateral: number }

/** Nearest station via the hash (−1 if none within one cell size). */
function nearestStation(g: Geo, x: number, y: number): number {
  const ci = Math.floor((x - g.gx0) / g.cell), cj = Math.floor((y - g.gy0) / g.cell);
  let best = -1, bd = Infinity;
  for (let dj = -1; dj <= 1; dj++) {
    const jj = cj + dj;
    if (jj < 0 || jj >= g.gny) continue;
    for (let di = -1; di <= 1; di++) {
      const ii = ci + di;
      if (ii < 0 || ii >= g.gnx) continue;
      const c = ii + g.gnx * jj;
      for (let k = g.cellStart[c], e = g.cellStart[c + 1]; k < e; k++) {
        const s = g.cellItems[k];
        const dx = x - g.cx[s], dy = y - g.cy[s];
        const d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = s; }
      }
    }
  }
  // Only exact if within the radius the 3×3 neighbourhood is guaranteed to cover.
  return bd <= g.cell * g.cell ? best : -1;
}

function nearestStationBrute(g: Geo, x: number, y: number): number {
  let best = 0, bd = Infinity;
  for (let s = 0; s < g.n; s++) {
    const dx = x - g.cx[s], dy = y - g.cy[s];
    const d = dx * dx + dy * dy;
    if (d < bd) { bd = d; best = s; }
  }
  return best;
}

/** Project onto the two segments adjacent to station s; pick the closer. */
function locateAt(g: Geo, x: number, y: number, s: number, out: Loc): void {
  const n = g.n;
  let bestD = Infinity;
  for (let k = 0; k < 2; k++) {
    const seg = k === 0 ? (s - 1 + n) % n : s;
    const dx = x - g.cx[seg], dy = y - g.cy[seg];
    let t = (dx * g.tx[seg] + dy * g.ty[seg]) / g.segLen[seg];
    const tc = t < 0 ? 0 : t > 1 ? 1 : t;
    const px = dx - tc * g.segLen[seg] * g.tx[seg], py = dy - tc * g.segLen[seg] * g.ty[seg];
    const d = px * px + py * py;
    if (d < bestD) {
      bestD = d;
      out.seg = seg; out.t = tc;
      out.lateral = -dx * g.ty[seg] + dy * g.tx[seg]; // left normal (−ty, tx)
    }
  }
  out.found = true;
}

/** Profile height at segment seg, param t, signed lateral (+left). Also returns slopes. */
interface ProfileOut { z: number; dzds: number; dzdl: number; f: number }

function profileAt(g: Geo, seg: number, t: number, lateral: number, out: ProfileOut, clampF: boolean): void {
  const n = g.n, nf = g.nf, fr = g.fr, pz = g.pz;
  const j = (seg + 1) % n;
  const hL = g.halfL[seg] + t * (g.halfL[j] - g.halfL[seg]);
  const hR = g.halfR[seg] + t * (g.halfR[j] - g.halfR[seg]);
  // fraction −1 = left edge, +1 = right edge; lateral is +left
  const half = lateral > 0 ? hL : hR;
  let f = -lateral / half;
  out.f = f;
  if (clampF || f < fr[0] || f > fr[nf - 1]) f = f < fr[0] ? fr[0] : f > fr[nf - 1] ? fr[nf - 1] : f;
  let k = 0;
  while (k < nf - 2 && f > fr[k + 1]) k++;
  const df = fr[k + 1] - fr[k];
  const a = (f - fr[k]) / df;
  const i0 = seg * nf + k, j0 = j * nf + k;
  const z0 = pz[i0] + a * (pz[i0 + 1] - pz[i0]);
  const z1 = pz[j0] + a * (pz[j0 + 1] - pz[j0]);
  out.z = z0 + t * (z1 - z0);
  out.dzds = (z1 - z0) / g.segLen[seg];
  const dzdf = ((pz[i0 + 1] - pz[i0]) * (1 - t) + (pz[j0 + 1] - pz[j0]) * t) / df;
  out.dzdl = (dzdf * -1) / half;
}

// ---------------------------------------------------------------------------

class HeightField {
  constructor(private d: Float32Array, private x0: number, private y0: number, private dx: number, private nx: number, private ny: number) {
    if (d.length < nx * ny) throw new Error(`heightfield: expected ${nx * ny} values, got ${d.length}`);
  }
  z = 0; gx = 0; gy = 0;
  sample(x: number, y: number): void {
    let fx = (x - this.x0) / this.dx, fy = (y - this.y0) / this.dx;
    const mx = this.nx - 1.000001, my = this.ny - 1.000001;
    let edge = false;
    if (fx < 0) { fx = 0; edge = true; } else if (fx > mx) { fx = mx; edge = true; }
    if (fy < 0) { fy = 0; edge = true; } else if (fy > my) { fy = my; edge = true; }
    const j = Math.floor(fx), i = Math.floor(fy);
    const tx = fx - j, ty = fy - i;
    const k = i * this.nx + j, d = this.d;
    const z00 = d[k], z01 = d[k + 1], z10 = d[k + this.nx], z11 = d[k + this.nx + 1];
    const za = z00 + tx * (z01 - z00), zb = z10 + tx * (z11 - z10);
    this.z = za + ty * (zb - za);
    if (edge) { this.gx = 0; this.gy = 0; return; }
    this.gx = ((z01 - z00) * (1 - ty) + (z11 - z10) * ty) / this.dx;
    this.gy = (zb - za) / this.dx;
  }
}

/** Grid description shared by heightfield.bin and far_heightfield.bin. */
export interface HeightGrid { x0: number; y0: number; dx: number; nx: number; ny: number }

/** Near heightfield with an optional coarser far heightfield around it. Never returns a bogus height. */
class Terrain {
  z = 0; gx = 0; gy = 0;
  constructor(private near: HeightField, private nearGrid: HeightGrid, private far: HeightField | null, private farGrid: HeightGrid | null) {}
  private static inside(g: HeightGrid, x: number, y: number): boolean {
    const fx = (x - g.x0) / g.dx, fy = (y - g.y0) / g.dx;
    return fx >= 0 && fy >= 0 && fx <= g.nx - 1 && fy <= g.ny - 1;
  }
  sample(x: number, y: number): void {
    // near grid where it exists; far grid (clamped at its edge) everywhere else
    const src = this.far && !Terrain.inside(this.nearGrid, x, y) ? this.far : this.near;
    src.sample(x, y);
    this.z = src.z; this.gx = src.gx; this.gy = src.gy;
  }
}

// ---------------------------------------------------------------------------
// Pit lane: the parts are concatenated into one Geo (same arrays as the track, so profileAt works); segments that
// would join the end of one part to the start of the next (or wrap) are marked invalid.

interface PitGeo { g: Geo; valid: Uint8Array; first: Uint8Array; last: Uint8Array }

function buildPitGeo(p: PitLaneJson): PitGeo | null {
  const parts = p.parts.filter((q) => q.n >= 2);
  const n = parts.reduce((a, q) => a + q.n, 0);
  if (n < 3) return null;
  const center: Vec3[] = [], left: Vec3[] = [], right: Vec3[] = [], z: number[][] = [];
  const valid = new Uint8Array(n), first = new Uint8Array(n), last = new Uint8Array(n);
  let k = 0;
  for (const q of parts) {
    for (let i = 0; i < q.n; i++, k++) {
      center.push(q.center[i]); left.push(q.left[i]); right.push(q.right[i]); z.push(q.profile_z[i]);
      valid[k] = i < q.n - 1 ? 1 : 0;
      first[k] = i === 0 ? 1 : 0;
      last[k] = i === q.n - 2 ? 1 : 0;
    }
  }
  const pseudo = { n, spacing_m: p.spacing_m, length_m: n * p.spacing_m, center, left, right,
    profile: { fractions: p.fractions, z } } as unknown as TrackJson;
  return { g: buildGeo(pseudo), valid, first, last };
}

interface PitLoc { seg: number; t: number; lateral: number; over: number }

/** Project onto the valid segments next to station s; `over` = distance beyond the end of a part (0 inside). */
function locatePit(pg: PitGeo, x: number, y: number, s: number, out: PitLoc): boolean {
  const g = pg.g, n = g.n;
  let bestD = Infinity, found = false;
  for (let k = 0; k < 2; k++) {
    const seg = k === 0 ? s - 1 : s;
    if (seg < 0 || seg >= n || !pg.valid[seg]) continue;
    const dx = x - g.cx[seg], dy = y - g.cy[seg];
    const t = (dx * g.tx[seg] + dy * g.ty[seg]) / g.segLen[seg];
    const tc = t < 0 ? 0 : t > 1 ? 1 : t;
    const px = dx - tc * g.segLen[seg] * g.tx[seg], py = dy - tc * g.segLen[seg] * g.ty[seg];
    const d = px * px + py * py;
    if (d < bestD) {
      bestD = d; found = true;
      out.seg = seg; out.t = tc;
      out.lateral = -dx * g.ty[seg] + dy * g.tx[seg];
      out.over = pg.first[seg] && t < 0 ? -t * g.segLen[seg] : pg.last[seg] && t > 1 ? (t - 1) * g.segLen[seg] : 0;
    }
  }
  return found;
}

/**
 * Surface for a track package. sample() returns a reused object.
 * Outside the near heightfield it falls back to `opts.far` (far_heightfield.bin,
 * CONTRACTS §2b) when given; beyond every grid it holds the edge height.
 */
export function createTrackSurface(track: TrackJson, heightfield: Float32Array, opts: TrackSurfaceOptions = {}): Surface {
  const g = getGeo(track);
  const h = track.heightfield;
  const nearHf = new HeightField(heightfield, h.x0, h.y0, h.dx, h.nx, h.ny);
  const f = opts.far ?? null;
  const farHf = f ? new HeightField(f.heightfield, f.x0, f.y0, f.dx, f.nx, f.ny) : null;
  const hf = new Terrain(nearHf, h, farHf, f);
  const muOn = opts.muOnTrack ?? 1.0;
  const muOff = opts.muOffTrack ?? OFF_PAVEMENT_MU;
  const blend = Math.max(0, opts.edgeBlend ?? SHOULDER_WIDTH_M);
  const gripBlend = Math.max(1e-6, opts.gripBlend ?? SURFACE_GRIP_BLEND_M);
  const rough = Math.max(0, opts.roughness ?? DIRT_ROUGHNESS_M);
  const out: SurfaceSample = { z: 0, nx: 0, ny: 0, nz: 1, onTrack: false, mu: muOff, paved: false, dirt: 1, muPaved: muOn };
  const loc: Loc = { found: false, seg: 0, t: 0, lateral: 0 };
  const prof: ProfileOut = { z: 0, dzds: 0, dzdl: 0, f: 0 };
  let cache = -1;
  const near = g.maxHalf + blend + 2 * g.spacing;
  const pit = opts.pitLane ? buildPitGeo(opts.pitLane) : null;
  const ploc: PitLoc = { seg: 0, t: 0, lateral: 0, over: 0 };

  const setNormal = (gxw: number, gyw: number) => {
    const l = 1 / Math.sqrt(gxw * gxw + gyw * gyw + 1);
    out.nx = -gxw * l; out.ny = -gyw * l; out.nz = l;
  };
  const strips = opts.sausages && opts.sausages.strips?.length ? buildSausageStrips(track, opts.sausages) : null;
  const kerbStrips = opts.kerbs && opts.kerbs.strips?.length && (opts.kerbs.profile || opts.kerbs.strips.some((s) => s.profile))
    ? buildKerbStrips(track, opts.kerbs) : null;
  const bump = { h: 0, gx: 0, gy: 0 }, kb = { h: 0, gx: 0, gy: 0 };

  const base: Surface = {
    sample(x: number, y: number): SurfaceSample {
      // locate: try the cached station's neighbourhood first, else the hash
      let s = -1;
      if (cache >= 0) {
        // walk downhill in distance from the cached station (cheap for nearby queries)
        let best = cache;
        let bd = (x - g.cx[best]) ** 2 + (y - g.cy[best]) ** 2;
        let converged = false;
        for (let step = 0; step < 24; step++) {
          const a = (best + 1) % g.n, b = (best - 1 + g.n) % g.n;
          const da = (x - g.cx[a]) ** 2 + (y - g.cy[a]) ** 2;
          const db = (x - g.cx[b]) ** 2 + (y - g.cy[b]) ** 2;
          if (da < bd && da <= db) { best = a; bd = da; } else if (db < bd) { best = b; bd = db; } else { converged = true; break; }
        }
        if (converged && bd <= near * near) s = best;
      }
      if (s < 0) s = nearestStation(g, x, y);
      cache = s;
      // track: on the racing surface -> profile; else remember the edge height and distance beyond the edge
      let dOutT = Infinity, zT = 0;
      if (s >= 0) {
        locateAt(g, x, y, s, loc);
        profileAt(g, loc.seg, loc.t, loc.lateral, prof, false);
        const af = Math.abs(prof.f);
        if (af <= 1) {
          out.z = prof.z;
          const tx = g.tx[loc.seg], ty = g.ty[loc.seg];
          // world gradient = dz/ds·T + dz/dlat·N, N = (−ty, tx)
          setNormal(prof.dzds * tx - prof.dzdl * ty, prof.dzds * ty + prof.dzdl * tx);
          out.onTrack = true;
          out.paved = true;
          out.mu = muOn;
          out.dirt = 0;
          return out;
        }
        const half = loc.lateral > 0
          ? g.halfL[loc.seg] + loc.t * (g.halfL[(loc.seg + 1) % g.n] - g.halfL[loc.seg])
          : g.halfR[loc.seg] + loc.t * (g.halfR[(loc.seg + 1) % g.n] - g.halfR[loc.seg]);
        dOutT = (af - 1) * half;
        if (dOutT < blend) { profileAt(g, loc.seg, loc.t, loc.lateral, prof, true); zT = prof.z; }
      }
      // pit lane: paved footprint -> its profile; else edge height and distance for the blend
      let dOutP = Infinity, zP = 0;
      if (pit) {
        const sp = nearestStation(pit.g, x, y);
        if (sp >= 0 && locatePit(pit, x, y, sp, ploc)) {
          const pg = pit.g;
          profileAt(pg, ploc.seg, ploc.t, ploc.lateral, prof, false);
          const half = ploc.lateral > 0
            ? pg.halfL[ploc.seg] + ploc.t * (pg.halfL[ploc.seg + 1] - pg.halfL[ploc.seg])
            : pg.halfR[ploc.seg] + ploc.t * (pg.halfR[ploc.seg + 1] - pg.halfR[ploc.seg]);
          dOutP = Math.max((Math.abs(prof.f) - 1) * half, ploc.over);
          if (dOutP <= 0) {
            out.z = prof.z;
            const tx = pg.tx[ploc.seg], ty = pg.ty[ploc.seg];
            setNormal(prof.dzds * tx - prof.dzdl * ty, prof.dzds * ty + prof.dzdl * tx);
            out.onTrack = false;
            out.paved = true;
            out.mu = muOn;
            out.dirt = 0;
            return out;
          }
          if (dOutP < blend) { profileAt(pg, ploc.seg, ploc.t, ploc.lateral, prof, true); zP = prof.z; }
        }
      }
      hf.sample(x, y);
      out.onTrack = false;
      out.paved = false;
      // grip: smoothstep from pavement to dirt over the first `gripBlend` m past the nearest paved edge
      const dOut = dOutT < dOutP ? dOutT : dOutP;
      const g01 = dOut >= gripBlend ? 1 : dOut / gripBlend;
      const dirt = g01 * g01 * (3 - 2 * g01);
      out.dirt = dirt;
      out.mu = muOn + dirt * (muOff - muOn);
      // low-frequency roughness, faded in with the dirt weight (zero at the paved edge, so heights stay continuous)
      let rz = 0, rgx = 0, rgy = 0;
      if (rough > 0 && dirt > 0) {
        for (let k = 0; k < 3; k++) {
          const wv = RW[k], ph = wv.kx * x + wv.ky * y + wv.ph, amp = rough * dirt * wv.a;
          rz += amp * Math.sin(ph);
          const c = amp * Math.cos(ph);
          rgx += c * wv.kx; rgy += c * wv.ky;
        }
      }
      setNormal(hf.gx + rgx, hf.gy + rgy);
      // shoulder: blend from the nearest paved edge(s) to the heightfield over `blend` m. With one source this is
      // edge + smoothstep(d/blend)(hf - edge); with two, each edge dominates at its own edge (w/(1-w) weights), so the
      // height stays continuous where the pit lane runs close to the track.
      const wT = dOutT < blend ? 1 - dOutT / blend : 0;
      const wP = dOutP < blend ? 1 - dOutP / blend : 0;
      if (wT <= 0 && wP <= 0) { out.z = hf.z + rz; return out; }
      const kT = wT / (1 - wT + 1e-6), kP = wP / (1 - wP + 1e-6);
      const zE = (kT * zT + kP * zP) / (kT + kP);
      // smoothstep across the shoulder: no slope break at the paved edge or where it meets the heightfield
      const u = 1 - Math.max(wT, wP);
      out.z = zE + u * u * (3 - 2 * u) * (hf.z - zE) + rz;
      return out;
    },
  };
  if (!strips && !kerbStrips) return base;
  // sausage kerbs and raised kerbs ride on top of whatever is under them (shoulder, kerb paint, pavement): add the hump
  // and tilt the normal
  return {
    sample(x: number, y: number): SurfaceSample {
      base.sample(x, y);
      if (strips) sausageAt(strips, opts.sausages!, x, y, bump); else { bump.h = 0; bump.gx = 0; bump.gy = 0; }
      if (kerbStrips) {
        kerbAt(kerbStrips, opts.kerbs!, x, y, kb);
        if (kb.h > bump.h) { bump.h = kb.h; bump.gx = kb.gx; bump.gy = kb.gy; }
      }
      if (bump.h > 0) {
        const gx = -out.nx / out.nz + bump.gx, gy = -out.ny / out.nz + bump.gy;
        out.z += bump.h;
        setNormal(gx, gy);
        // painted concrete: full grip, no dust
        out.mu = out.muPaved ?? muOn; out.dirt = 0;
      }
      return out;
    },
  };
}

export interface TrackProjection { s: number; lateral: number; index: number }

export function createTrackProjector(track: TrackJson): { project(x: number, y: number): TrackProjection } {
  const g = getGeo(track);
  const loc: Loc = { found: false, seg: 0, t: 0, lateral: 0 };
  return {
    project(x: number, y: number): TrackProjection {
      let s = nearestStation(g, x, y);
      if (s < 0) s = nearestStationBrute(g, x, y);
      locateAt(g, x, y, s, loc);
      let sm = (loc.seg + loc.t) * g.spacing;
      sm %= g.length; if (sm < 0) sm += g.length;
      return { s: sm, lateral: loc.lateral, index: loc.seg };
    },
  };
}

/** Centreline position at s (m, wrapped) offset laterally (+left) along the segment's left normal. */
function lineXY(g: Geo, offsetAtS: (s: number) => number, s: number, out: { x: number; y: number; seg: number; t: number; off: number }): void {
  let sw = s % g.length; if (sw < 0) sw += g.length;
  let u = sw / g.spacing;
  let seg = Math.floor(u);
  if (seg >= g.n) seg = g.n - 1;
  const t = u - seg;
  const j = (seg + 1) % g.n;
  const x = g.cx[seg] + t * (g.cx[j] - g.cx[seg]);
  const y = g.cy[seg] + t * (g.cy[j] - g.cy[seg]);
  const off = offsetAtS(sw);
  out.x = x - off * g.ty[seg];
  out.y = y + off * g.tx[seg];
  out.seg = seg; out.t = t; out.off = off;
}

export function lineToWorld(track: TrackJson, offsetAtS: (s: number) => number, s: number): { pos: [number, number, number]; heading: number } {
  const g = getGeo(track);
  const a = { x: 0, y: 0, seg: 0, t: 0, off: 0 };
  const b = { x: 0, y: 0, seg: 0, t: 0, off: 0 };
  const c = { x: 0, y: 0, seg: 0, t: 0, off: 0 };
  lineXY(g, offsetAtS, s, c);
  const prof: ProfileOut = { z: 0, dzds: 0, dzdl: 0, f: 0 };
  profileAt(g, c.seg, c.t, c.off, prof, true);
  const ds = 0.5 * g.spacing;
  lineXY(g, offsetAtS, s - ds, a);
  lineXY(g, offsetAtS, s + ds, b);
  const heading = Math.atan2(b.y - a.y, b.x - a.x);
  return { pos: [c.x, c.y, prof.z], heading };
}
