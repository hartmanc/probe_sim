// Scenery gates of the track pipeline's stage 3 (20 Oct 2026): containment, pit connectivity, sign placement.
// Pure functions over a package's track.json and scenery.json (plus the gate config from the track config); the CLI
// (run_gates.ts) prints the reports and exits 1 on a failure. Run by build_track.py --stage scenery for every circuit.
//
//   CONTAINMENT       from every station, on each side, rays across the terrain (the outward normal and +-35 deg):
//                     any other paved surface (pit lane, closed road) reached before a barrier, a cone line or the
//                     track itself is an escape, unless the config lists it as allowed runoff (or it is a pit-lane
//                     junction: the lane abuts the edge, within 1 m, where it is meant to join).
//   PIT CONNECTIVITY  the autopilot path pit box -> pit exit -> track and track -> pit entry -> pit box (the lane's
//                     centre polyline plus straight connectors to the track centre 15 m beyond each end) crosses no
//                     barrier, and every metre of it is paved (track or pit lane).
//   SIGN PLACEMENT    brake boards, turn signs, banners, flag stands and marshal posts stand off the track, never inside
//                     a pit lane, closed road or declared paddock polygon; brake and turn boards within 15 m of an edge.

export type V2 = [number, number];
export type V3 = [number, number, number];
export interface TrackLike { n: number; spacing_m: number; center: V3[]; left: V3[]; right: V3[] }
export interface PartLike { center: V3[]; left: V3[]; right: V3[]; gap_left?: number[]; gap_right?: number[]; turn?: string; kind?: string; name?: string }
export interface SceneryLike {
  barriers?: { kind: string; pts: V3[]; src?: string }[];
  pit_lane?: { parts: PartLike[] } | null;
  paved_zones?: { parts: PartLike[] } | null;
  pit_exit_cones?: { pts: V3[]; spacing_m?: number; src?: string } | null;
  cone_lines?: { pts: V3[]; src?: string; spacing_m?: number }[];
  landmarks?: { kind: string; text?: string; x: number; y: number }[];
}
export interface AllowedRunoff { target: string; side?: 'left' | 'right'; s0?: number; s1?: number; why: string }
export interface GateConfig {
  allowed?: AllowedRunoff[];
  /** paddock polygons (ENU) where no sign may stand */
  paddock?: { name: string; poly: V2[] }[];
  /** ray length, m (default 120) */
  reach?: number;
  /** station step, m (default 2) */
  step?: number;
}

// ------------------------------------------------------------------ geometry primitives (tested)
/** Parameter t in [0, 1] along a->b where it crosses segment c->d, or null. */
export function segCross(a: V2, b: V2, c: V2, d: V2): number | null {
  const rx = b[0] - a[0], ry = b[1] - a[1], sx = d[0] - c[0], sy = d[1] - c[1];
  const den = rx * sy - ry * sx;
  if (Math.abs(den) < 1e-12) return null;
  const qx = c[0] - a[0], qy = c[1] - a[1];
  const t = (qx * sy - qy * sx) / den, u = (qx * ry - qy * rx) / den;
  return t >= 0 && t <= 1 && u >= 0 && u <= 1 ? t : null;
}

/** Even-odd point in polygon. */
export function inPoly(p: V2, poly: V2[]): boolean {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** A paved part (pit-lane strip layout) as a closed polygon: left edge forward, right edge back. */
export function partPolygon(p: PartLike): V2[] {
  return [...p.left.map((q) => [q[0], q[1]] as V2), ...p.right.slice().reverse().map((q) => [q[0], q[1]] as V2)];
}

/** Uniform grid over segments for fast ray / path queries. */
export class SegIndex {
  private cells = new Map<string, number[]>();
  readonly segs: { a: V2; b: V2; tag: string }[] = [];
  constructor(private cell = 10) {}
  add(a: V2, b: V2, tag: string): void {
    const k = this.segs.length;
    this.segs.push({ a, b, tag });
    const x0 = Math.floor(Math.min(a[0], b[0]) / this.cell), x1 = Math.floor(Math.max(a[0], b[0]) / this.cell);
    const y0 = Math.floor(Math.min(a[1], b[1]) / this.cell), y1 = Math.floor(Math.max(a[1], b[1]) / this.cell);
    for (let i = x0; i <= x1; i++) for (let j = y0; j <= y1; j++) {
      const key = `${i},${j}`;
      const c = this.cells.get(key);
      if (c) c.push(k); else this.cells.set(key, [k]);
    }
  }
  addPolyline(pts: ArrayLike<ArrayLike<number>>, tag: string): void {
    for (let i = 0; i + 1 < pts.length; i++) this.add([pts[i][0], pts[i][1]], [pts[i + 1][0], pts[i + 1][1]], tag);
  }
  /** First crossing of a->b: {t, tag} or null. */
  first(a: V2, b: V2): { t: number; tag: string } | null {
    const seen = new Set<number>();
    let best: { t: number; tag: string } | null = null;
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const steps = Math.max(1, Math.ceil(len / (this.cell / 2)));
    for (let s = 0; s <= steps; s++) {
      const x = a[0] + ((b[0] - a[0]) * s) / steps, y = a[1] + ((b[1] - a[1]) * s) / steps;
      const ci = Math.floor(x / this.cell), cj = Math.floor(y / this.cell);
      for (let di = -1; di <= 1; di++) for (let dj = -1; dj <= 1; dj++) {
        for (const k of this.cells.get(`${ci + di},${cj + dj}`) ?? []) {
          if (seen.has(k)) continue;
          seen.add(k);
          const t = segCross(a, b, this.segs[k].a, this.segs[k].b);
          if (t !== null && (!best || t < best.t)) best = { t, tag: this.segs[k].tag };
        }
      }
    }
    return best;
  }
}

/** Track frame: left normals and half-widths per station. */
export function trackFrame(t: TrackLike) {
  const n = t.n, nl: V2[] = [], hl: number[] = [], hr: number[] = [];
  for (let i = 0; i < n; i++) {
    const a = t.center[(i - 1 + n) % n], b = t.center[(i + 1) % n];
    const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
    nl.push([-dy / l, dx / l]);
    const c = t.center[i];
    hl.push((t.left[i][0] - c[0]) * nl[i][0] + (t.left[i][1] - c[1]) * nl[i][1]);
    hr.push(-((t.right[i][0] - c[0]) * nl[i][0] + (t.right[i][1] - c[1]) * nl[i][1]));
  }
  return { nl, hl, hr };
}

/** Nearest station (brute force over a stride, then refined) and the point's lateral / distance beyond the edge. */
export function makeProjector(t: TrackLike) {
  const { nl, hl, hr } = trackFrame(t);
  const n = t.n, cell = 20, grid = new Map<string, number[]>();
  for (let i = 0; i < n; i++) {
    const key = `${Math.floor(t.center[i][0] / cell)},${Math.floor(t.center[i][1] / cell)}`;
    const c = grid.get(key); if (c) c.push(i); else grid.set(key, [i]);
  }
  return (p: V2, radius = 60): { i: number; lat: number; out: number } | null => {
    const ci = Math.floor(p[0] / cell), cj = Math.floor(p[1] / cell), r = Math.ceil(radius / cell);
    let bi = -1, bd = Infinity;
    for (let di = -r; di <= r; di++) for (let dj = -r; dj <= r; dj++) {
      for (const i of grid.get(`${ci + di},${cj + dj}`) ?? []) {
        const d = (t.center[i][0] - p[0]) ** 2 + (t.center[i][1] - p[1]) ** 2;
        if (d < bd) { bd = d; bi = i; }
      }
    }
    if (bi < 0) return null;
    const c = t.center[bi];
    const lat = (p[0] - c[0]) * nl[bi][0] + (p[1] - c[1]) * nl[bi][1];
    return { i: bi, lat, out: Math.abs(lat) - (lat > 0 ? hl[bi] : hr[bi]) };
  };
}

const sDist = (a: number, b: number, L: number) => { const d = Math.abs(a - b) % L; return Math.min(d, L - d); };

// ------------------------------------------------------------------ containment
export interface Escape { s: number; side: 'left' | 'right'; angle: number; target: string; dist: number }
export interface ContainmentReport { rays: number; escapes: Escape[]; allowed: (Escape & { why: string })[]; junctions: number }

interface Target { name: string; kind: 'pit' | 'closed'; poly: V2[]; box: [number, number, number, number]; part: PartLike }

export function pavedTargets(sc: SceneryLike): Target[] {
  const out: Target[] = [];
  const add = (p: PartLike, name: string, kind: 'pit' | 'closed') => {
    const poly = partPolygon(p);
    const xs = poly.map((q) => q[0]), ys = poly.map((q) => q[1]);
    out.push({ name, kind, poly, box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)], part: p });
  };
  (sc.pit_lane?.parts ?? []).forEach((p, k) => add(p, `pit lane${(sc.pit_lane?.parts.length ?? 0) > 1 ? ' ' + k : ''}`, 'pit'));
  for (const p of sc.paved_zones?.parts ?? []) if (p.kind === 'closed_road') add(p, p.turn ?? p.name ?? 'closed road', 'closed');
  return out;
}

export function barrierIndex(sc: SceneryLike, withCones = true): SegIndex {
  const ix = new SegIndex(10);
  for (const b of sc.barriers ?? []) ix.addPolyline(b.pts, `${b.kind}: ${b.src ?? ''}`);
  if (withCones) {
    if (sc.pit_exit_cones?.pts?.length) ix.addPolyline(sc.pit_exit_cones.pts, 'pit-exit cones');
    for (const c of sc.cone_lines ?? []) ix.addPolyline(c.pts, `cones: ${c.src ?? ''}`);
  }
  return ix;
}

export function containment(t: TrackLike, sc: SceneryLike, cfg: GateConfig = {}): ContainmentReport {
  const reach = cfg.reach ?? 120, stepS = cfg.step ?? 2, L = t.n * t.spacing_m;
  const { nl, hl, hr } = trackFrame(t);
  const proj = makeProjector(t);
  const bars = barrierIndex(sc, true);
  const targets = pavedTargets(sc);
  const rep: ContainmentReport = { rays: 0, escapes: [], allowed: [], junctions: 0 };
  const angles = [0, 35, -35].map((d) => (d * Math.PI) / 180);
  const stride = Math.max(1, Math.round(stepS / t.spacing_m));
  for (let i = 0; i < t.n; i += stride) {
    const s = i * t.spacing_m, c = t.center[i];
    for (const side of [1, -1]) {
      const e: V2 = [c[0] + nl[i][0] * side * (side > 0 ? hl[i] : hr[i]), c[1] + nl[i][1] * side * (side > 0 ? hl[i] : hr[i])];
      const ox = nl[i][0] * side, oy = nl[i][1] * side;
      for (const ang of angles) {
        rep.rays++;
        const ca = Math.cos(ang), sa = Math.sin(ang);
        // the outward normal rotated by ang (counter-clockwise from above)
        const dx = ox * ca - oy * sa, dy = ox * sa + oy * ca;
        const end: V2 = [e[0] + dx * reach, e[1] + dy * reach];
        const hit = bars.first([e[0] + dx * 0.05, e[1] + dy * 0.05], end);
        const dBar = hit ? 0.05 + hit.t * (reach - 0.05) : Infinity;
        // walk out in 0.5 m steps: re-entering the track ends the ray; entering a target before the barrier is an escape
        let found: { name: string; d: number; target: Target } | null = null;
        for (let d = 0.5; d <= Math.min(reach, dBar); d += 0.5) {
          const p: V2 = [e[0] + dx * d, e[1] + dy * d];
          const pr = proj(p, 40);
          if (pr && pr.out < 0 && sDist(pr.i * t.spacing_m, s, L) > 30) break;   // back on the circuit
          let tg: Target | null = null;
          for (const T of targets) {
            if (p[0] < T.box[0] || p[0] > T.box[2] || p[1] < T.box[1] || p[1] > T.box[3]) continue;
            if (inPoly(p, T.poly)) { tg = T; break; }
          }
          if (tg) { found = { name: tg.name, d, target: tg }; break; }
        }
        if (!found) continue;
        const esc: Escape = { s: Math.round(s * 10) / 10, side: side > 0 ? 'left' : 'right', angle: Math.round((ang * 180) / Math.PI), target: found.name, dist: found.d };
        if (found.target.kind === 'pit' && found.d <= 1.0) { rep.junctions++; continue; }
        const al = (cfg.allowed ?? []).find((a) => a.target === found!.name && (!a.side || a.side === esc.side)
          && (a.s0 === undefined || a.s1 === undefined || (a.s0 <= a.s1 ? s >= a.s0 && s <= a.s1 : s >= a.s0 || s <= a.s1)));
        if (al) rep.allowed.push({ ...esc, why: al.why }); else rep.escapes.push(esc);
      }
    }
  }
  return rep;
}

/** Escapes grouped into runs (same side and target, stations within 10 m) for the log. */
export function escapeRuns(es: Escape[]): { side: string; target: string; s0: number; s1: number; n: number; dmin: number }[] {
  const out: { side: string; target: string; s0: number; s1: number; n: number; dmin: number }[] = [];
  const sorted = es.slice().sort((a, b) => (a.side + a.target).localeCompare(b.side + b.target) || a.s - b.s);
  for (const e of sorted) {
    const r = out[out.length - 1];
    if (r && r.side === e.side && r.target === e.target && e.s - r.s1 <= 10) { r.s1 = e.s; r.n++; r.dmin = Math.min(r.dmin, e.dist); }
    else out.push({ side: e.side, target: e.target, s0: e.s, s1: e.s, n: 1, dmin: e.dist });
  }
  return out;
}

// ------------------------------------------------------------------ pit connectivity
export interface PitReport {
  ok: boolean; paths: { name: string; length: number; crossings: string[]; unpaved_m: number; cones: number }[];
  /** round 7 (Sonoma owner note 37: a cone line converging into the outer wall closed the pit-in while the centre path
   *  passed): the lane driven on two paths 1.5 m from each lane edge; `blocked` lists every barrier, cone line or wall
   *  end inside the lane polygon or within 1.0 m of either path, `pinched` the stations where the lane is under 3 m wide
   *  between two closed edges (neither open to the track). */
  lane?: { stations: number; blocked: string[]; pinched: number[] };
}

/** Distance from p to segment a-b. */
export function segDist(p: V2, a: V2, b: V2): number {
  const dx = b[0] - a[0], dy = b[1] - a[1], l2 = dx * dx + dy * dy;
  const t = l2 > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2)) : 0;
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
}

/** Two-path lane check (see PitReport.lane). Barriers and cone lines both count; a lane edge is 'open' where it lies on
 *  the track's paved width (the junctions), and a narrow lane is only allowed there. */
export function laneClearance(t: TrackLike, sc: SceneryLike, opts: { off?: number; clear?: number; minW?: number; inset?: number } = {}): NonNullable<PitReport['lane']> {
  const off = opts.off ?? 1.5, clear = opts.clear ?? 1.0, minW = opts.minW ?? 3.0, inset = opts.inset ?? 0.3;
  const proj = makeProjector(t);
  const obst: { a: V2; b: V2; tag: string }[] = [];
  const short = (tag: string) => tag.length > 90 ? tag.slice(0, 90) + '...' : tag;
  for (const b of sc.barriers ?? []) for (let i = 0; i + 1 < b.pts.length; i++) obst.push({ a: [b.pts[i][0], b.pts[i][1]], b: [b.pts[i + 1][0], b.pts[i + 1][1]], tag: `${b.kind}: ${short(b.src ?? '')}` });
  for (const c of sc.cone_lines ?? []) for (let i = 0; i + 1 < c.pts.length; i++) obst.push({ a: [c.pts[i][0], c.pts[i][1]], b: [c.pts[i + 1][0], c.pts[i + 1][1]], tag: `cones: ${short(c.src ?? '')}` });
  const out = { stations: 0, blocked: [] as string[], pinched: [] as number[] };
  const seen = new Set<string>();
  const hit = (tag: string, where: V2, why: string) => {
    const pr = proj(where, 80), key = `${tag}|${why}`;
    if (seen.has(key)) return;
    seen.add(key);
    out.blocked.push(`${why}: ${tag} near s ${pr ? (pr.i * t.spacing_m).toFixed(0) : '?'} (${where[0].toFixed(1)}, ${where[1].toFixed(1)})`);
  };
  for (const p of sc.pit_lane?.parts ?? []) {
    const poly = partPolygon(p);
    const xs = poly.map((q) => q[0]), ys = poly.map((q) => q[1]);
    const box = [Math.min(...xs) - 3, Math.min(...ys) - 3, Math.max(...xs) + 3, Math.max(...ys) + 3];
    const near = obst.filter((o) => Math.max(o.a[0], o.b[0]) >= box[0] && Math.min(o.a[0], o.b[0]) <= box[2] && Math.max(o.a[1], o.b[1]) >= box[1] && Math.min(o.a[1], o.b[1]) <= box[3]);
    const edgeD = (q: V2) => { let d = Infinity; for (let i = 0; i < poly.length; i++) d = Math.min(d, segDist(q, poly[i], poly[(i + 1) % poly.length])); return d; };
    // 1. nothing stands inside the lane (deeper than `inset` from its boundary: the bounding walls sit on it)
    for (const o of near) {
      const L = Math.hypot(o.b[0] - o.a[0], o.b[1] - o.a[1]);
      for (let d = 0; d <= L; d += 0.5) {
        const q: V2 = [o.a[0] + ((o.b[0] - o.a[0]) * d) / (L || 1), o.a[1] + ((o.b[1] - o.a[1]) * d) / (L || 1)];
        if (inPoly(q, poly) && edgeD(q) > inset) { hit(o.tag, q, 'inside the lane'); break; }
      }
    }
    // 2. two paths 1.5 m in from each edge, 1.0 m clear of every barrier and cone line
    const openAt = (q: V3) => { const pr = proj([q[0], q[1]], 40); return !!pr && pr.out <= 0.3; };
    for (let j = 0; j < p.center.length; j++) {
      const l: V2 = [p.left[j][0], p.left[j][1]], r: V2 = [p.right[j][0], p.right[j][1]];
      const w = Math.hypot(r[0] - l[0], r[1] - l[1]);
      out.stations++;
      const oL = openAt(p.left[j]), oR = openAt(p.right[j]);
      if (w < 2 * off) { if (!oL && !oR) { const pr = proj(l, 80); out.pinched.push(pr ? Math.round(pr.i * t.spacing_m) : -1); } continue; }
      const ux = (r[0] - l[0]) / w, uy = (r[1] - l[1]) / w;
      const paths: V2[] = [[l[0] + ux * off, l[1] + uy * off], [r[0] - ux * off, r[1] - uy * off]];
      for (const q of paths) for (const o of near) if (segDist(q, o.a, o.b) < clear) hit(o.tag, q, `within ${clear} m of a lane path`);
    }
  }
  return out;
}

/** Point on the track centre `ds` m along from station i (wrapped). */
function centreAt(t: TrackLike, i: number, ds: number): V2 {
  const k = (((i + Math.round(ds / t.spacing_m)) % t.n) + t.n) % t.n;
  return [t.center[k][0], t.center[k][1]];
}

export function pitConnectivity(t: TrackLike, sc: SceneryLike, boxS?: number): PitReport {
  const parts = sc.pit_lane?.parts ?? [];
  const proj = makeProjector(t);
  const walls = barrierIndex({ barriers: sc.barriers }, false);
  const cones = barrierIndex({ pit_exit_cones: sc.pit_exit_cones, cone_lines: sc.cone_lines }, true);
  const lanePolys = parts.map(partPolygon);
  const rep: PitReport = { ok: parts.length > 0, paths: [] };
  const frame = trackFrame(t);
  if (!parts.length) return rep;
  // the pit box: the lane centre point abeam boxS (default: the start/finish line, station 0)
  const s0 = boxS ?? 0, target = t.center[Math.round(s0 / t.spacing_m) % t.n];
  let bp = 0, bk = 0, bd = Infinity;
  parts.forEach((p, k) => p.center.forEach((q, j) => { const d = (q[0] - target[0]) ** 2 + (q[1] - target[1]) ** 2; if (d < bd) { bd = d; bp = k; bk = j; } }));
  const check = (name: string, P: V2[]) => {
    const crossings: string[] = []; let cn = 0, len = 0, unp = 0;
    for (let i = 0; i + 1 < P.length; i++) {
      const h = walls.first(P[i], P[i + 1]);
      if (h) crossings.push(`${h.tag} near (${P[i][0].toFixed(1)}, ${P[i][1].toFixed(1)})`);
      if (cones.first(P[i], P[i + 1])) cn++;
      const sl = Math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]); len += sl;
      for (let d = 0; d < sl; d += 1) {
        const q: V2 = [P[i][0] + ((P[i + 1][0] - P[i][0]) * d) / sl, P[i][1] + ((P[i + 1][1] - P[i][1]) * d) / sl];
        const pr = proj(q, 40);
        if (pr && pr.out <= 0.05) continue;
        if (lanePolys.some((poly) => inPoly(q, poly))) continue;
        unp += 1;
      }
    }
    rep.paths.push({ name, length: Math.round(len), crossings, unpaved_m: unp, cones: cn });
    if (crossings.length || unp > 2) rep.ok = false;
  };
  const xy = (q: V3): V2 => [q[0], q[1]];
  // exit: box -> end of its part -> 15 m onto the track centre beyond the part's end
  const pe = parts[bp], last = pe.center[pe.center.length - 1];
  const prE = proj(xy(last), 80);
  // connectors: lane end -> the track edge abeam it -> the track centre 15 m on (the way a car merges)
  const abeam = (q: V2, i: number): V2 => {
    const { nl, hl, hr } = frame; const c = t.center[i], lat = (q[0] - c[0]) * nl[i][0] + (q[1] - c[1]) * nl[i][1];
    const h = lat > 0 ? Math.min(lat, hl[i] - 0.2) : -Math.min(-lat, hr[i] - 0.2);
    return [c[0] + nl[i][0] * h, c[1] + nl[i][1] * h];
  };
  const exitPath: V2[] = [...pe.center.slice(bk).map(xy)];
  if (prE) exitPath.push(abeam(xy(last), prE.i), centreAt(t, prE.i, 15));
  check('pit box -> pit exit -> track', exitPath);
  // entry: the track centre 15 m before the part's start -> the part -> box
  const pi = parts[bp], first = pi.center[0];
  const prI = proj(xy(first), 80);
  const entryPath: V2[] = [];
  if (prI) entryPath.push(centreAt(t, prI.i, -15), abeam(xy(first), prI.i));
  entryPath.push(...pi.center.slice(0, bk + 1).map(xy));
  check('track -> pit entry -> pit box', entryPath);
  rep.lane = laneClearance(t, sc);
  if (rep.lane.blocked.length || rep.lane.pinched.length) rep.ok = false;
  return rep;
}

// ------------------------------------------------------------------ sign placement
export interface SignReport { checked: number; bad: { kind: string; text: string; x: number; y: number; why: string }[] }

export const SIGN_KINDS = ['brake', 'corner', 'banner', 'sign', 'flagstand', 'marshal'];

export function signPlacement(t: TrackLike, sc: SceneryLike, cfg: GateConfig = {}): SignReport {
  const proj = makeProjector(t);
  const polys: { name: string; poly: V2[] }[] = [
    ...pavedTargets(sc).map((T) => ({ name: T.name, poly: T.poly })),
    ...(cfg.paddock ?? []).map((p) => ({ name: `paddock ${p.name}`, poly: p.poly })),
  ];
  const rep: SignReport = { checked: 0, bad: [] };
  for (const m of sc.landmarks ?? []) {
    if (!SIGN_KINDS.includes(m.kind)) continue;
    rep.checked++;
    const p: V2 = [m.x, m.y];
    const pr = proj(p, 200);
    const bad = (why: string) => rep.bad.push({ kind: m.kind, text: m.text ?? '', x: m.x, y: m.y, why });
    if (pr && pr.out < 0.3) { bad(`on the track (${pr.out.toFixed(1)} m from the edge)`); continue; }
    const inside = polys.find((q) => inPoly(p, q.poly));
    if (inside) { bad(`inside ${inside.name}`); continue; }
    if ((m.kind === 'brake' || m.kind === 'corner') && (!pr || pr.out > 15)) bad(`${pr ? pr.out.toFixed(1) : '>200'} m from the circuit edge (max 15)`);
  }
  return rep;
}

// ------------------------------------------------------------------ exposed wall ends (round 7, Sonoma owner notes 39 / 41)
export interface ExposedEnd { label: string; side: 'left' | 'right'; s: number; out: number; why: string }
export interface EndsReport { checked: number; ok: { label: string; s: number; how: string }[]; exposed: ExposedEnd[] }

/** Every rigid barrier run (concrete, pitwall, armco) whose upstream end (the end a car travelling the lap meets first)
 *  stands within `near` m (30; 8 until Sonoma round 14B) of the edge must be protected, else it is an end face exposed to
 *  oncoming travel. Round 14B (Sonoma owner, round-13 drive at T10: "we should be skeptical of any concrete wall ends
 *  that jut out into traffic. This would kill someone if they ran into it at speed"): a car leaving the track meets a
 *  bare head 11 m out as surely as one 7 m out (run 37's head stood 7 m inside the long outer wall's line, 11 m out, and
 *  the 8 m gate never looked at it). Tyre runs keep `nearTyres` (8): their heads were gated from round 11 at 8 m. Every
 *  end checked before is checked exactly as before (the old gate is a subset). A run standing OUTSIDE the head (further
 *  from the track) protects nothing: only a lapping run closer to the track counts.
 *  - joined: another barrier, a tyre run or an impact block is within `join` m (1.5) of the end point (one wall, or a
 *    cushion at its head);
 *  - lapped: a run on the same side ends within `lap` m (25) upstream of it, or overlaps it, and stands closer to the
 *    track there (the downstream start further from the track than the upstream end: the lapping rule);
 *  - tapered: the run angles away from the track at its head (its end is at least `taper` m (1.5) further out than
 *    the run 10 m downstream).
 *  Runs from 25 m upstream of the end are compared on the end's own side. */
export function exposedEnds(t: TrackLike, sc: SceneryLike & { landmarks?: { kind: string; x: number; y: number }[] }, opts: { near?: number; nearTyres?: number; join?: number; lap?: number; taper?: number } = {}): EndsReport {
  const near = opts.near ?? 30, nearTyres = opts.nearTyres ?? 8, join = opts.join ?? 1.5, lap = opts.lap ?? 25, taper = opts.taper ?? 1.5;
  const proj = makeProjector(t), L = t.n * t.spacing_m;
  const dens = (P: V3[]): V2[] => {
    const o: V2[] = [];
    for (let i = 0; i + 1 < P.length; i++) {
      const d = Math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]), n = Math.max(1, Math.ceil(d));
      for (let k = 0; k < n; k++) o.push([P[i][0] + ((P[i + 1][0] - P[i][0]) * k) / n, P[i][1] + ((P[i + 1][1] - P[i][1]) * k) / n]);
    }
    if (P.length) o.push([P[P.length - 1][0], P[P.length - 1][1]]);
    return o;
  };
  interface Run { k: number; kind: string; label: string; xy: V2[]; s: number[]; out: number[]; lat: number[] }
  const runs: Run[] = [];
  (sc.barriers ?? []).forEach((b, k) => {
    if (b.pts.length < 2 || b.kind === 'fence') return;
    const xy = dens(b.pts);
    const pr = xy.map((p) => proj(p, 120));
    if (pr.some((q) => !q)) return;
    // unwrap s along the run
    const s: number[] = [];
    pr.forEach((q, i) => { let v = q!.i * t.spacing_m; if (i) { while (v - s[i - 1] > L / 2) v -= L; while (s[i - 1] - v > L / 2) v += L; } s.push(v); });
    runs.push({ k, kind: b.kind, label: `${b.kind}: ${(b.src ?? '').slice(0, 100)}`, xy, s, out: pr.map((q) => q!.out), lat: pr.map((q) => q!.lat) });
  });
  const cushions: V2[] = ((sc.landmarks ?? []) as { kind: string; x: number; y: number }[]).filter((m) => m.kind === 'impact').map((m) => [m.x, m.y]);
  const rep: EndsReport = { checked: 0, ok: [], exposed: [] };
  const sd = (a: number, b: number) => { let d = (b - a) % L; if (d > L / 2) d -= L; if (d < -L / 2) d += L; return d; };  // b - a, wrapped
  for (const r of runs) {
    // the upstream end: the end with the lower s along the run's direction of travel
    const fwd = r.s[r.s.length - 1] >= r.s[0];
    const ord = fwd ? r.xy.map((_, i) => i) : r.xy.map((_, i) => r.xy.length - 1 - i);
    const h = ord[0];
    // tyre runs are checked like every other run (round 11, Sonoma owner note 67: "the wall transition shown in the sim
    // generally don't exist because they are extremely dangerous": a tyre wall never starts bare facing travel; until
    // 22 Oct 2026 every tyre run was skipped here). The one exemption: a cushion, a tyre run of at most 12 m whose
    // downstream end joins a rigid run (it IS the end protection of that run's head)
    if (r.kind === 'tyres') {
      const tail = r.xy[ord[ord.length - 1]];
      const len = r.xy.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - r.xy[i - 1][0], p[1] - r.xy[i - 1][1]) : 0), 0);
      const cushion = len <= 12 && runs.some((q) => q !== r && q.kind !== 'tyres' && q.xy.some((p) => Math.hypot(p[0] - tail[0], p[1] - tail[1]) <= join));
      if (cushion) continue;
    }
    if (r.out[h] > (r.kind === 'tyres' ? nearTyres : near) || r.out[h] < -0.5) continue;
    // a run that crosses the track (a wall across a closed road's mouth, out < 0 on the road) is not a lap wall end
    rep.checked++;
    const side: 'left' | 'right' = r.lat[h] > 0 ? 'left' : 'right';
    const P = r.xy[h], s0 = ((r.s[h] % L) + L) % L, o0 = r.out[h];
    const label = r.label;
    // joined / cushioned
    let how = '';
    for (const q of runs) {
      if (q === r) continue;
      if (q.xy.some((p) => Math.hypot(p[0] - P[0], p[1] - P[1]) <= join)) { how = `joined to ${q.kind} run ${q.k}`; break; }
    }
    if (!how && cushions.some((c) => Math.hypot(c[0] - P[0], c[1] - P[1]) <= join + 1.5)) how = 'impact block at its head';
    // lapped by an upstream run on the same side standing closer to the track
    if (!how) for (const q of runs) {
      if (q === r) continue;
      let best = Infinity;
      for (let i = 0; i < q.xy.length; i++) {
        if ((q.lat[i] > 0 ? 'left' : 'right') !== side) continue;
        const d = sd(((q.s[i] % L) + L) % L, s0);  // > 0: q's point is upstream of the head
        if (d < -2 || d > lap) continue;
        if (q.out[i] < o0 - 0.2) best = Math.min(best, q.out[i]);
      }
      if (best < Infinity) { how = `lapped by ${q.kind} run ${q.k} (${best.toFixed(1)} m out vs ${o0.toFixed(1)} m)`; break; }
    }
    // a run that leaves the track at a right angle (a wall across a runoff or a road mouth) shows its end face across the
    // track, not along it: nothing travelling the lap meets it head-on
    if (!how) {
      const j = ord.find((i) => Math.hypot(r.xy[i][0] - P[0], r.xy[i][1] - P[1]) >= 5);
      const pr = proj(P, 60);
      if (j !== undefined && pr) {
        const a = t.center[(pr.i + 1) % t.n], b = t.center[(pr.i - 1 + t.n) % t.n];
        const tx = a[0] - b[0], ty = a[1] - b[1], dx = r.xy[j][0] - P[0], dy = r.xy[j][1] - P[1];
        const cos = Math.abs(tx * dx + ty * dy) / ((Math.hypot(tx, ty) || 1) * (Math.hypot(dx, dy) || 1));
        if (cos < 0.5) how = `leaves the track at ${(Math.acos(cos) * 180 / Math.PI).toFixed(0)} deg (its end faces across the lap)`;
      }
    }
    // tapered: angled away from the track at its head
    if (!how) {
      const j = ord.find((i) => Math.abs(sd(((r.s[h] % L) + L) % L, ((r.s[i] % L) + L) % L)) >= 10);
      if (j !== undefined && o0 - r.out[j] >= taper) how = `tapered (${o0.toFixed(1)} m out at the head, ${r.out[j].toFixed(1)} m 10 m on)`;
    }
    if (how) rep.ok.push({ label, s: Math.round(s0), how });
    else rep.exposed.push({ label, side, s: Math.round(s0), out: Math.round(o0 * 10) / 10, why: `upstream end ${o0.toFixed(1)} m beyond the ${side} edge faces oncoming travel: no join, cushion, lapping run or taper` });
  }
  return rep;
}

// ------------------------------------------------------------------ tyre facings (round 7b, Sonoma owner note 48)
export interface SideBySide { tyre: string; wall: string; s: number; off: number }

/** A tyre run beside a rigid wall (concrete, pitwall, armco) must be a FACING of it (its stacks within `facing` m, 0.8,
 *  of the wall line) or meet it end to end; a tyre run standing `facing`..`reach` (2.5) m off a wall over a stretch is
 *  two runs of different kinds side by side with an offset. Points within `joint` m (1.5) of the wall's own end points
 *  are the joint and not counted. Returns one entry per (tyre run, wall) pair, at its first offending point. */
export function sideBySide(t: TrackLike, sc: SceneryLike, opts: { facing?: number; reach?: number; joint?: number } = {}): SideBySide[] {
  const facing = opts.facing ?? 0.8, reach = opts.reach ?? 2.5, joint = opts.joint ?? 1.5;
  const proj = makeProjector(t);
  const out: SideBySide[] = [];
  const bars = sc.barriers ?? [];
  const xy = (P: V3[]): V2[] => P.map((p) => [p[0], p[1]]);
  for (const tb of bars) {
    if (tb.kind !== 'tyres') continue;
    const T: V2[] = [];
    const P = xy(tb.pts);
    for (let i = 0; i + 1 < P.length; i++) {
      const d = Math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]), n = Math.max(1, Math.ceil(d / 0.5));
      for (let k = 0; k < n; k++) T.push([P[i][0] + ((P[i + 1][0] - P[i][0]) * k) / n, P[i][1] + ((P[i + 1][1] - P[i][1]) * k) / n]);
    }
    for (const wb of bars) {
      if (!['concrete', 'pitwall', 'armco'].includes(wb.kind)) continue;
      const W = xy(wb.pts), e0 = W[0], e1 = W[W.length - 1];
      // side by side = PARALLEL at an offset: consecutive 0.5 m samples in the band whose offset changes under 0.1 m
      // per sample (< ~11 deg); a run angling in to meet the wall (a taper) changes faster and is not counted
      let bad = 0, best = 0, first: V2 | null = null, offAt = 0, prev = NaN;
      for (const q of T) {
        let d = Infinity;
        for (let i = 0; i + 1 < W.length; i++) d = Math.min(d, segDist(q, W[i], W[i + 1]));
        const atJoint = Math.hypot(q[0] - e0[0], q[1] - e0[1]) < joint || Math.hypot(q[0] - e1[0], q[1] - e1[1]) < joint;
        if (!atJoint && d > facing && d < reach && Math.abs(d - prev) < 0.1) { bad++; if (bad > best) { best = bad; } if (!first) { first = q; offAt = d; } }
        else bad = 0;
        prev = d;
      }
      if (best >= 4 && first) {   // >= 2 m of parallel run
        const pr = proj(first, 80);
        out.push({ tyre: (tb.src ?? '').slice(0, 80), wall: (wb.src ?? '').slice(0, 80), s: pr ? Math.round(pr.i * t.spacing_m) : -1, off: Math.round(offAt * 10) / 10 });
      }
    }
  }
  return out;
}

// ------------------------------------------------------------------ wall tops, joins and tyre faces (round 12)
// Sonoma judge r11 N65 / N67 (22 Oct 2026). The drawn layout these gates check is the app's (src/app/scenery.ts): a
// concrete / pit wall is 0.36 m thick on its line (Armco: the beam 0.05 m off it) and stands to `top_z` per point where
// it is level across a hollow (tools/track/barrier_rules.py), else ground + h; a tyre run is two rows of 0.31 m stacks,
// row 0 on the line and row 1 0.6 m to the polyline's left (the physics collides at the same faces).
export const TYRE_R = 0.31, TYRE_ROW = 0.6;
const RIGID_KINDS = ['concrete', 'pitwall', 'armco'];
const HALF_THICK: Record<string, number> = { concrete: 0.18, pitwall: 0.18, armco: 0.05 };
type BarrierTop = { kind: string; pts: V3[]; src?: string; h?: number; top_z?: number[] };
const topsOf = (b: BarrierTop): number[] => (b.top_z && b.top_z.length === b.pts.length ? b.top_z : b.pts.map((p) => p[2] + (b.h ?? 0)));

export interface WallTopsReport {
  checked: number;
  /** a rigid run whose top line changes faster than `slope` m per m between points >= 0.5 m apart (a step) */
  steps: { label: string; s: number; slope: number; dz: number }[];
  /** a board on a wall ('wall board on <wall>' with `top`) whose foot is not on the wall's top */
  boards: { text: string; s: number; z: number; top: number }[];
  boardsChecked: number;
}

/** Wall tops (round 12, N65: "a depressed, stepped section between taller boarded runs"): the top line of every
 *  concrete, pit-wall and Armco run has no step (|d top| / d run <= `slope`, 0.5, where the builder bridges any hollow
 *  steeper than that), and every board standing on a wall has its foot within `tol` m (0.10) of that wall's top. */
export function wallTops(t: TrackLike, sc: SceneryLike & { barriers?: BarrierTop[]; landmarks?: { kind: string; text?: string; x: number; y: number; z?: number; src?: string; top?: number }[] },
  opts: { slope?: number; tol?: number } = {}): WallTopsReport {
  const slopeMax = opts.slope ?? 0.5, tol = opts.tol ?? 0.1;
  const proj = makeProjector(t);
  const sOf = (p: V2) => { const q = proj(p, 200); return q ? Math.round(q.i * t.spacing_m) : -1; };
  const rep: WallTopsReport = { checked: 0, steps: [], boards: [], boardsChecked: 0 };
  const rigid = (sc.barriers ?? []).filter((b) => RIGID_KINDS.includes(b.kind) && b.pts.length >= 2);
  for (const b of rigid) {
    rep.checked++;
    const top = topsOf(b);
    let worst = { slope: 0, i: -1, dz: 0 };
    for (let i = 0; i + 1 < b.pts.length; i++) {
      const ds = Math.hypot(b.pts[i + 1][0] - b.pts[i][0], b.pts[i + 1][1] - b.pts[i][1]);
      if (ds < 0.5) continue;
      const dz = top[i + 1] - top[i], sl = Math.abs(dz) / ds;
      if (sl > worst.slope) worst = { slope: sl, i, dz };
    }
    if (worst.slope > slopeMax) rep.steps.push({ label: `${b.kind}: ${(b.src ?? '').slice(0, 90)}`, s: sOf([b.pts[worst.i][0], b.pts[worst.i][1]]),
      slope: Math.round(worst.slope * 100) / 100, dz: Math.round(worst.dz * 100) / 100 });
  }
  for (const m of sc.landmarks ?? []) {
    if (m.kind !== 'sign' || typeof m.top !== 'number' || typeof m.z !== 'number' || !(m.src ?? '').startsWith('wall board on ')) continue;
    // the nearest segment within 1 m of the board's own wall ('wall board on <name> (...)' -> 'declared: <name>'; a panel
    // stands 0.12 m in front of its wall's line)
    const src = m.src ?? '', name = src.slice('wall board on '.length, src.lastIndexOf(' (') > 0 ? src.indexOf(' (', 'wall board on '.length) : undefined);
    let best = { d: 1.0, top: NaN };
    for (const b of rigid) {
      if (!(b.src ?? '').startsWith(`declared: ${name}`)) continue;
      const top = topsOf(b);
      for (let i = 0; i + 1 < b.pts.length; i++) {
        const a = b.pts[i], c = b.pts[i + 1], dx = c[0] - a[0], dy = c[1] - a[1], l2 = dx * dx + dy * dy || 1e-9;
        const u = Math.max(0, Math.min(1, ((m.x - a[0]) * dx + (m.y - a[1]) * dy) / l2));
        const d = Math.hypot(a[0] + dx * u - m.x, a[1] + dy * u - m.y);
        if (d < best.d) best = { d, top: top[i] + (top[i + 1] - top[i]) * u };
      }
    }
    if (!Number.isFinite(best.top)) continue;
    rep.boardsChecked++;
    if (Math.abs(m.z - best.top) > tol) rep.boards.push({ text: m.text ?? '', s: sOf([m.x, m.y]), z: m.z, top: Math.round(best.top * 100) / 100 });
  }
  return rep;
}

export interface JoinFace { wall: string; tyres: string; s: number; downstream: 'tyres' | 'wall'; step: number }

/** Flush joins (round 12, N67: "whether the wall meets the tyre head flush"): where a rigid run's end meets a tyre run's
 *  end end to end (within `join` m, 1.5, the run directions within 60 deg), the downstream run's track face may stand
 *  at most `tol` m (0.15, checked by the caller) proud toward the track of the upstream run's: else the downstream run's
 *  head is a step facing oncoming travel. Returns every join, with `step` = downstream face - upstream face (m, + = the
 *  downstream head stands proud toward the track; a recessed downstream head is shielded and fine). */
export function joinFaces(t: TrackLike, sc: SceneryLike & { barriers?: BarrierTop[] }, opts: { join?: number } = {}): JoinFace[] {
  const join = opts.join ?? 1.5;
  const proj = makeProjector(t);
  const out: JoinFace[] = [];
  const bars = sc.barriers ?? [];
  const ends = (P: V3[]) => [{ p: P[0], q: P[1] }, { p: P[P.length - 1], q: P[P.length - 2] }];
  for (const tb of bars) {
    if (tb.kind !== 'tyres' || tb.pts.length < 2) continue;
    for (const [k, te] of ends(tb.pts).entries()) {
      const H = te.p, ux0 = te.q[0] - H[0], uy0 = te.q[1] - H[1], ul = Math.hypot(ux0, uy0) || 1;
      const ux = ux0 / ul, uy = uy0 / ul;   // into the tyre run from its end
      // the polyline's left normal at this end (the run's own direction, first -> last)
      const nlx = k === 0 ? -uy : uy, nly = k === 0 ? ux : -ux;
      const pr = proj([H[0], H[1]], 200);
      if (!pr) continue;
      const c = t.center[pr.i], trackLeft = (c[0] - H[0]) * nlx + (c[1] - H[1]) * nly > 0;
      const ntx = trackLeft ? nlx : -nlx, nty = trackLeft ? nly : -nly;   // toward the track
      const tyreFace = trackLeft ? TYRE_ROW + TYRE_R : TYRE_R;
      for (const wb of bars) {
        if (!RIGID_KINDS.includes(wb.kind) || wb.pts.length < 2) continue;
        for (const we of ends(wb.pts)) {
          const E = we.p;
          if (Math.hypot(E[0] - H[0], E[1] - H[1]) > join) continue;
          const wx0 = E[0] - we.q[0], wy0 = E[1] - we.q[1], wl = Math.hypot(wx0, wy0) || 1;   // out of the wall at its end
          if ((wx0 / wl) * ux + (wy0 / wl) * uy < 0.5) continue;   // not end to end (a facing or a crossing)
          const wallFace = (E[0] - H[0]) * ntx + (E[1] - H[1]) * nty + (HALF_THICK[wb.kind] ?? 0.18);
          // driving direction at the joint (stations are in driving order): do the tyres run on downstream of it?
          const fa = t.center[(pr.i + 1) % t.n], fb = t.center[(pr.i - 1 + t.n) % t.n];
          const tyresDown = (fa[0] - fb[0]) * ux + (fa[1] - fb[1]) * uy > 0;
          out.push({ wall: `${wb.kind}: ${(wb.src ?? '').slice(0, 70)}`, tyres: (tb.src ?? '').slice(0, 70), s: Math.round(pr.i * t.spacing_m),
            downstream: tyresDown ? 'tyres' : 'wall', step: Math.round((tyresDown ? tyreFace - wallFace : wallFace - tyreFace) * 100) / 100 });
        }
      }
    }
  }
  return out;
}

export interface TyreFace { tyres: string; s: number; face: number; rowsToTrack: boolean }

/** Tyre faces off the road (round 12, N67: the T11-approach tyre wall's row 1 stood 0.37 m on the road): every tyre run's
 *  drawn track-side face stands at least `min` m (0.2) beyond the edge. Returns the runs that do not, at their worst
 *  point. Points more than 60 m from the centre (far runs, other roads) are not checked. */
export function tyreFaces(t: TrackLike, sc: SceneryLike, opts: { min?: number } = {}): TyreFace[] {
  const min = opts.min ?? 0.2;
  const proj = makeProjector(t);
  const out: TyreFace[] = [];
  for (const tb of sc.barriers ?? []) {
    if (tb.kind !== 'tyres' || tb.pts.length < 2) continue;
    const P = tb.pts;
    let worst: TyreFace | null = null;
    for (let i = 0; i < P.length; i++) {
      const a = P[Math.max(0, i - 1)], b = P[Math.min(P.length - 1, i + 1)], l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      const nlx = -(b[1] - a[1]) / l, nly = (b[0] - a[0]) / l;
      const pr = proj([P[i][0], P[i][1]], 60);
      if (!pr) continue;
      const c = t.center[pr.i], trackLeft = (c[0] - P[i][0]) * nlx + (c[1] - P[i][1]) * nly > 0;
      const face = pr.out - (trackLeft ? TYRE_ROW + TYRE_R : TYRE_R);
      if (!worst || face < worst.face) worst = { tyres: (tb.src ?? '').slice(0, 90), s: Math.round(pr.i * t.spacing_m), face: Math.round(face * 100) / 100, rowsToTrack: trackLeft };
    }
    if (worst && worst.face < min) out.push(worst);
  }
  return out;
}

// ------------------------------------------------------------------ run gaps (round 13, Sonoma owner note 131)
export interface RunGap { a: string; b: string; s: number; side: 'left' | 'right'; out: number; gap: number; x: number; y: number }
export interface RunGapsReport { checked: number; gaps: RunGap[]; openings: { s: number; gap: number; why: string }[] }

/** Two barrier runs that are one line with a hole in it: an end of run A and an end of run B (tyres, concrete, pit wall,
 *  Armco; fences have gates) `minGap` (0.5) to `maxGap` (25) m apart, facing each other (each end's outward direction,
 *  its last `tail` (6) m, within `angle` (25) deg of the line to the other end), both beyond the edge on one side. Not a
 *  finding when the hole is an opening: a paved surface (the track, a pit-lane part, a paved zone or closed road, a paved
 *  area) crosses the segment between the ends, another barrier run passes within 2 m of its midpoint (a lapping run), or
 *  the config declares it (`openings`: [{x, y, why}] within 10 m of the midpoint). The wall-ends gate checks only
 *  upstream ends within 8 m of the edge and the joins gate only ends that already meet, so a 13.5 m hole 10-25 m out
 *  (Sonoma s 306-318, right, round 12) passed both. */
export function runGaps(t: TrackLike, sc: SceneryLike & { paved_areas?: { name?: string; poly: V2[] }[] },
  opts: { minGap?: number; maxGap?: number; angle?: number; tail?: number; openings?: { x: number; y: number; why: string }[] } = {}): RunGapsReport {
  const minGap = opts.minGap ?? 0.5, maxGap = opts.maxGap ?? 25, cosA = Math.cos(((opts.angle ?? 25) * Math.PI) / 180), tail = opts.tail ?? 6;
  const proj = makeProjector(t);
  const kinds = ['tyres', 'concrete', 'pitwall', 'armco'];
  const runs = (sc.barriers ?? []).map((b, k) => ({ b, k })).filter(({ b }) => kinds.includes(b.kind) && b.pts.length >= 2);
  interface End { k: number; label: string; p: V2; dir: V2 }
  const ends: End[] = [];
  for (const { b, k } of runs) {
    for (const head of [true, false]) {
      const P = head ? b.pts : [...b.pts].reverse();
      const p: V2 = [P[0][0], P[0][1]];
      // the point `tail` m into the run; outward direction = from it to the end
      let acc = 0, q: V2 = [P[1][0], P[1][1]];
      for (let i = 1; i < P.length; i++) { acc += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); q = [P[i][0], P[i][1]]; if (acc >= tail) break; }
      const d = Math.hypot(p[0] - q[0], p[1] - q[1]) || 1;
      ends.push({ k, label: `${b.kind} run ${k}: ${(b.src ?? '').slice(0, 90)}`, p, dir: [(p[0] - q[0]) / d, (p[1] - q[1]) / d] });
    }
  }
  const paved: V2[][] = [];
  for (const grp of [sc.pit_lane?.parts ?? [], sc.paved_zones?.parts ?? []]) for (const p of grp) paved.push(partPolygon(p));
  for (const a of sc.paved_areas ?? []) paved.push(a.poly);
  const crossesPaved = (a: V2, b: V2) => {
    for (let k = 0; k <= 10; k++) {
      const p: V2 = [a[0] + ((b[0] - a[0]) * k) / 10, a[1] + ((b[1] - a[1]) * k) / 10];
      const q = proj(p, 80);
      if (q && q.out < 0) return 'the track';
      for (const poly of paved) if (inPoly(p, poly)) return 'a paved surface';
    }
    return '';
  };
  const segs = runs.map(({ b, k }) => ({ k, P: b.pts }));
  const nearOther = (m: V2, ka: number, kb: number) => segs.some(({ k, P }) => k !== ka && k !== kb
    && P.some((_, i) => i > 0 && segDist(m, [P[i - 1][0], P[i - 1][1]], [P[i][0], P[i][1]]) <= 2));
  const rep: RunGapsReport = { checked: 0, gaps: [], openings: [] };
  const seen = new Set<string>();
  for (let i = 0; i < ends.length; i++) for (let j = 0; j < ends.length; j++) {
    const A = ends[i], B = ends[j];
    if (A.k === B.k) continue;
    const key = `${Math.min(i, j)}-${Math.max(i, j)}`;
    if (seen.has(key)) continue;
    const dx = B.p[0] - A.p[0], dy = B.p[1] - A.p[1], g = Math.hypot(dx, dy);
    if (g < minGap || g > maxGap) continue;
    const ux = dx / g, uy = dy / g;
    if (A.dir[0] * ux + A.dir[1] * uy < cosA || -(B.dir[0] * ux + B.dir[1] * uy) < cosA) continue;
    const qa = proj(A.p, 120), qb = proj(B.p, 120);
    if (!qa || !qb || qa.out < 0 || qb.out < 0 || Math.sign(qa.lat) !== Math.sign(qb.lat)) continue;
    seen.add(key);
    rep.checked++;
    const m: V2 = [(A.p[0] + B.p[0]) / 2, (A.p[1] + B.p[1]) / 2];
    const s = Math.round(((proj(m, 120) ?? qa).i) * t.spacing_m);
    const why = crossesPaved(A.p, B.p) || (nearOther(m, A.k, B.k) ? 'a lapping run' : '')
      || (opts.openings ?? []).find((o) => Math.hypot(o.x - m[0], o.y - m[1]) <= 10)?.why || '';
    if (why) { rep.openings.push({ s, gap: Math.round(g * 10) / 10, why }); continue; }
    rep.gaps.push({ a: A.label, b: B.label, s, side: qa.lat > 0 ? 'left' : 'right', out: Math.round(Math.min(qa.out, qb.out) * 10) / 10,
      gap: Math.round(g * 10) / 10, x: Math.round(m[0] * 10) / 10, y: Math.round(m[1] * 10) / 10 });
  }
  return rep;
}

// ------------------------------------------------------------------ cones off the surface (round 11, 23 Oct 2026)
/** The cone spots of one line exactly as the app places them (src/app/scenery.ts buildPitExitCones): one every
 *  `spacing` m along the polyline, the remainder carried over each vertex, the first at the line's start. */
export function coneSpots(pts: ArrayLike<ArrayLike<number>>, spacing?: number): V2[] {
  const out: V2[] = [];
  const step = spacing || 16;
  let carry = 0;
  for (let k = 0; k + 1 < pts.length; k++) {
    const a = pts[k], b = pts[k + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    for (let d = carry; d < L; d += step) { const t = d / L; out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); }
    carry = ((carry - L) % step + step) % step;
  }
  return out;
}

export interface ConeOnSurface { line: number; src: string; s: number; side: 'left' | 'right'; depth: number }
export interface ConesReport { lines: number; cones: number; tol: number; bad: ConeOnSurface[]; worst: number; onLane: number }

/** CONES OFF THE SURFACE (Buttonwillow round 11; judge r10: the Atlantic mouth cones stood up to 1.24 m inside the right
 *  edge, on the racing surface). Every cone of every line (cone_lines and pit_exit_cones, spots as the app places them)
 *  that stands inside the course polygon (the track's station quads) more than `tol` m (0.15) from the nearer edge
 *  polyline fails. `depth` is that distance (m inside the edge); `worst` the largest over all cones (0 when none is
 *  inside). One entry per offending cone.
 *  Not gated (counted in `onLane`): the cones of a pit lane's separation line where the lane and the track share the
 *  pavement (SKILL 3.5: pit-in / pit-out cones stand ON the measured painted blend line): the pit_exit_cones line, any
 *  cone on the pit-lane paving (inside a pit_lane part or within `laneReach` m, 0.5, of its outline), and the cone
 *  lines the track's gate config names in `exempt` (a substring of the line's src with the reason; Sonoma's pit-in
 *  double white line). */
export function conesOffSurface(t: TrackLike, sc: SceneryLike, tol = 0.15, laneReach = 0.5, exempt: { src: string; why: string }[] = []): ConesReport {
  const proj = makeProjector(t);
  const n = t.n, W = 6;
  const lines = [...(sc.pit_exit_cones?.pts?.length ? [{ ...sc.pit_exit_cones, src: sc.pit_exit_cones.src ?? 'pit-exit cones', pit: true }] : []),
    ...(sc.cone_lines ?? []).map((c) => ({ ...c, pit: exempt.some((e) => (c.src ?? '').includes(e.src)) }))];
  const rep: ConesReport = { lines: lines.length, cones: 0, tol, bad: [], worst: 0, onLane: 0 };
  const lane = (sc.pit_lane?.parts ?? []).map((q) => partPolygon(q));
  const L2 = (p: V3): V2 => [p[0], p[1]];
  lines.forEach((cl, li) => {
    for (const p of coneSpots(cl.pts, cl.spacing_m)) {
      rep.cones++;
      const pr = proj(p, 60);
      if (!pr) continue;
      let inside = false, dl = Infinity, dr = Infinity;
      for (let k = -W; k < W; k++) {
        const a = (pr.i + k + n) % n, b = (a + 1) % n;
        if (!inside && inPoly(p, [L2(t.left[a]), L2(t.left[b]), L2(t.right[b]), L2(t.right[a])])) inside = true;
        dl = Math.min(dl, segDist(p, L2(t.left[a]), L2(t.left[b])));
        dr = Math.min(dr, segDist(p, L2(t.right[a]), L2(t.right[b])));
      }
      if (!inside) continue;
      if (cl.pit || lane.some((q) => inPoly(p, q) || q.some((a, k) => segDist(p, a, q[(k + 1) % q.length]) <= laneReach))) { rep.onLane++; continue; }
      const depth = Math.min(dl, dr);
      rep.worst = Math.max(rep.worst, depth);
      if (depth > tol) rep.bad.push({ line: li, src: (cl.src ?? '').slice(0, 90), s: Math.round(pr.i * t.spacing_m * 10) / 10, side: dl < dr ? 'left' : 'right', depth: Math.round(depth * 100) / 100 });
    }
  });
  return rep;
}
