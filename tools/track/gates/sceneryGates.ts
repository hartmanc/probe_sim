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
  pit_exit_cones?: { pts: V3[] } | null;
  cone_lines?: { pts: V3[]; src?: string }[];
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
export interface PitReport { ok: boolean; paths: { name: string; length: number; crossings: string[]; unpaved_m: number; cones: number }[] }

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
