// Shared track geometry for the AI: centreline frame per 1 m station, the racing line (ghosts.json
// line.offset_m), its curvature / grade / banking, the ghost speed shape, and a cheap incremental
// projector (hint-based local search, no allocation). Built once per race, shared by all drivers.

import type { TrackJson } from '../track';
import { createTrackProjector } from '../track';

export interface GhostsJsonLike {
  s_grid_m: number;
  line: { offset_m: number[] };
  laps: { id: string; kind?: string; lap_time_s: number; t: number[]; v_mps: number[] }[];
}

const TAU = 2 * Math.PI;

function smoothPeriodic(a: Float64Array, sigma: number): Float64Array {
  const r = Math.ceil(3 * sigma), w: number[] = [];
  let ws = 0;
  for (let k = -r; k <= r; k++) { const x = Math.exp(-0.5 * (k / sigma) ** 2); w.push(x); ws += x; }
  const n = a.length, out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let acc = 0;
    for (let k = -r; k <= r; k++) acc += w[k + r] * a[(i + k + n) % n];
    out[i] = acc / ws;
  }
  return out;
}

/**
 * A corner of the lap for racecraft and the mishap model (RaceLine.corners, built once per line from
 * track.json corners and the ghost speed shape).
 */
export interface LineCorner {
  name: string;
  /** station of the slowest ghost speed (the apex) and of the braking point (fastest ghost speed in the 300 m before) */
  apex: number; brake: number;
  /** +1 left-hander, -1 right-hander (sign of the racing-line curvature at the apex) */
  dir: number;
  /** ghost speed at the braking point and at the apex, m/s; peak |curvature| near the apex, 1/m */
  vEntry: number; vApex: number; kPeak: number;
  /** mean approach grade (dz/ds, negative = downhill) */
  grade: number;
  /**
   * Loss-of-control difficulty, normalised so the mean over the lap's corners is 1:
   * kPeak · vEntry · vApex (curvature at the entry speed) · (1 + 6 · downhill grade).
   */
  difficulty: number;
  /** a real braking zone (vEntry / vApex > 1.15): a place to set up and make a pass */
  passable: boolean;
}

/** Result of RaceLine.project (reused object). */
export interface LineProjection { s: number; lateral: number; index: number }

export class RaceLine {
  readonly track: TrackJson;
  readonly N: number;
  readonly L: number;
  readonly spacing: number;
  /** centre position, unit tangent (segment i -> i+1), left normal = (-ty, tx), segment length */
  readonly cx: Float64Array; readonly cy: Float64Array; readonly cz: Float64Array;
  readonly tx: Float64Array; readonly ty: Float64Array; readonly segLen: Float64Array;
  /** half widths to the left / right edge, m */
  readonly halfL: Float64Array; readonly halfR: Float64Array;
  /** racing-line lateral offset (+left), line position, line arc length to the next station */
  readonly off: Float64Array; readonly lx: Float64Array; readonly ly: Float64Array; readonly lz: Float64Array; readonly ds: Float64Array;
  /** racing line curvature (1/m, + = left), grade (dz/ds), road bank toward the left (tan) */
  readonly curv: Float64Array; readonly grade: Float64Array; readonly bank: Float64Array;
  /** vertical curvature of the line, d(grade)/ds (1/m; negative over a crest, where the car goes light) */
  readonly vcurv: Float64Array;
  /** ghost speed shape per station (m/s), from ghosts.json (default driver_a_best) */
  readonly ghostV: Float64Array;
  readonly ghostLap: number;
  /** the lap's corners in s order (see LineCorner) */
  readonly corners: LineCorner[];
  private readonly globalProj: { project(x: number, y: number): { s: number; lateral: number; index: number } };
  private readonly out: LineProjection = { s: 0, lateral: 0, index: 0 };

  constructor(track: TrackJson, ghosts: GhostsJsonLike, ghostId = 'driver_a_best') {
    this.track = track;
    const N = (this.N = track.n);
    this.spacing = track.spacing_m;
    this.L = track.length_m;
    this.cx = new Float64Array(N); this.cy = new Float64Array(N); this.cz = new Float64Array(N);
    for (let i = 0; i < N; i++) { this.cx[i] = track.center[i][0]; this.cy[i] = track.center[i][1]; this.cz[i] = track.center[i][2]; }
    this.tx = new Float64Array(N); this.ty = new Float64Array(N); this.segLen = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      const j = (i + 1) % N, dx = this.cx[j] - this.cx[i], dy = this.cy[j] - this.cy[i];
      const l = Math.hypot(dx, dy) || 1e-9;
      this.tx[i] = dx / l; this.ty[i] = dy / l; this.segLen[i] = l;
    }
    this.halfL = new Float64Array(N); this.halfR = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      this.halfL[i] = Math.max(0.5, Math.hypot(track.left[i][0] - this.cx[i], track.left[i][1] - this.cy[i]));
      this.halfR[i] = Math.max(0.5, Math.hypot(track.right[i][0] - this.cx[i], track.right[i][1] - this.cy[i]));
    }
    // racing line offset at each station (grid may be coarser than the stations)
    const g = ghosts.s_grid_m, offs = ghosts.line.offset_m, NG = offs.length;
    const gridAt = (arr: ArrayLike<number>, s: number) => {
      let u = (((s % this.L) + this.L) % this.L) / g;
      const i = Math.floor(u) % NG, j = (i + 1) % NG;
      u -= Math.floor(u);
      return arr[i] + u * (arr[j] - arr[i]);
    };
    this.off = new Float64Array(N);
    for (let i = 0; i < N; i++) this.off[i] = gridAt(offs, i * this.spacing);
    // line positions use the segment's normal like lineToWorld
    this.lx = new Float64Array(N); this.ly = new Float64Array(N); this.lz = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      this.lx[i] = this.cx[i] - this.off[i] * this.ty[i];
      this.ly[i] = this.cy[i] + this.off[i] * this.tx[i];
      this.lz[i] = this.cz[i];
    }
    this.ds = new Float64Array(N);
    for (let i = 0; i < N; i++) { const j = (i + 1) % N; this.ds[i] = Math.hypot(this.lx[j] - this.lx[i], this.ly[j] - this.ly[i], this.lz[j] - this.lz[i]) || 1e-3; }
    const head = new Float64Array(N);
    for (let i = 0; i < N; i++) { const a = (i - 1 + N) % N, b = (i + 1) % N; head[i] = Math.atan2(this.ly[b] - this.ly[a], this.lx[b] - this.lx[a]); }
    const kRaw = new Float64Array(N), gRaw = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      const a = (i - 1 + N) % N, b = (i + 1) % N;
      let dh = head[b] - head[a];
      while (dh > Math.PI) dh -= TAU;
      while (dh < -Math.PI) dh += TAU;
      kRaw[i] = dh / (this.ds[a] + this.ds[i]);
      gRaw[i] = (this.lz[b] - this.lz[a]) / (this.ds[a] + this.ds[i]);
    }
    this.curv = smoothPeriodic(kRaw, 4);
    this.grade = smoothPeriodic(gRaw, 3);
    const vRaw = new Float64Array(N);
    for (let i = 0; i < N; i++) { const a = (i - 3 + N) % N, b = (i + 3) % N; vRaw[i] = (this.grade[b] - this.grade[a]) / (6 * this.spacing); }
    this.vcurv = smoothPeriodic(vRaw, 2);
    this.bank = new Float64Array(N);
    const fr = track.profile.fractions;
    for (let i = 0; i < N; i++) {
      const hl = this.halfL[i], hr = this.halfR[i];
      const lat = fr.map((f) => (f < 0 ? -f * hl : -f * hr));
      const z = track.profile.z[i];
      const sl: number[] = [];
      for (let k = 1; k < fr.length - 2; k++) sl.push((z[k + 1] - z[k]) / (lat[k + 1] - lat[k]));
      sl.sort((a, b) => a - b);
      this.bank[i] = sl.length >= 3 ? -0.5 * (sl[1] + sl[2]) : 0;
    }
    const lap = ghosts.laps.find((l) => l.id === ghostId) ?? ghosts.laps.find((l) => l.kind === 'real') ?? ghosts.laps[0];
    this.ghostV = new Float64Array(N);
    this.ghostLap = lap ? lap.lap_time_s : 120;
    if (lap) for (let i = 0; i < N; i++) this.ghostV[i] = Math.max(5, gridAt(lap.v_mps, i * this.spacing));
    else this.ghostLap = this.curvatureSpeedProfile();
    this.globalProj = createTrackProjector(track);
    this.corners = this.buildCorners();
  }

  /** A track built without logger laps has no ghost speeds: a reference profile from the line's curvature (1.05 g
   *  laterally, 3.5 m/s^2 falling with speed forward, 8.5 m/s^2 braking, two periodic passes) stands in for the corner
   *  finder (apex, braking point, entry speed). Returns its lap time. Unused when ghosts.json has laps. */
  private curvatureSpeedProfile(): number {
    const N = this.ghostV.length, v = this.ghostV;
    for (let i = 0; i < N; i++) v[i] = Math.min(58, Math.sqrt(1.05 * 9.81 / Math.max(1e-4, Math.abs(this.curv[i]))));
    for (let pass = 0; pass < 2; pass++) {
      for (let k = 1; k < 2 * N; k++) {
        const a = k % N, b = (k - 1) % N, acc = 3.5 * Math.max(0.15, 1 - v[b] / 62);
        v[a] = Math.min(v[a], Math.sqrt(v[b] * v[b] + 2 * acc * this.ds[b]));
      }
      for (let k = 2 * N - 2; k >= 0; k--) {
        const a = k % N, b = (k + 1) % N;
        v[a] = Math.min(v[a], Math.sqrt(v[b] * v[b] + 2 * 8.5 * this.ds[a]));
      }
    }
    let t = 0;
    for (let i = 0; i < N; i++) { v[i] = Math.max(5, v[i]); t += this.ds[i] / v[i]; }
    return t;
  }

  /** Corners from track.json (radius < 150 m; corners sharing an apex, e.g. the Corkscrew T8/T8A, merged). */
  private buildCorners(): LineCorner[] {
    const out: LineCorner[] = [];
    const list = ((this.track as unknown as { corners?: { name: string; turn: string | null; s: number; radius_m: number | null }[] }).corners ?? [])
      .filter((c) => c.turn && c.radius_m != null && c.radius_m < 150);
    for (const c of list) {
      let apex = c.s, vAp = Infinity;
      for (let d = -60; d <= 60; d++) { const v = this.at(this.ghostV, c.s + d); if (v < vAp) { vAp = v; apex = this.wrap(c.s + d); } }
      if (out.some((o) => Math.abs(o.apex - apex) < 30)) continue;
      let vEn = 0, brake = apex;
      for (let d = 0; d <= 300; d++) { const v = this.at(this.ghostV, apex - d); if (v > vEn) { vEn = v; brake = this.wrap(apex - d); } }
      let kPeak = 0;
      for (let d = -40; d <= 40; d++) kPeak = Math.max(kPeak, Math.abs(this.at(this.curv, apex + d)));
      let grade = 0;
      for (let d = -60; d <= 20; d++) grade += this.at(this.grade, apex + d) / 81;
      const name = c.turn === 'T8' || c.turn === 'T8A' ? 'T8 Corkscrew' : (c.turn as string);
      out.push({ name, apex, brake, dir: this.at(this.curv, apex) >= 0 ? 1 : -1, vEntry: vEn, vApex: vAp, kPeak, grade,
        difficulty: kPeak * vEn * vAp * (1 + 6 * Math.max(0, -grade)), passable: vEn / vAp > 1.15 });
    }
    out.sort((a, b) => a.apex - b.apex);
    const mean = out.reduce((a, c) => a + c.difficulty, 0) / Math.max(1, out.length);
    for (const c of out) c.difficulty /= mean || 1;
    return out;
  }

  wrap(s: number): number { const L = this.L; s %= L; return s < 0 ? s + L : s; }

  /**
   * A cone line on the driver's LEFT (scenery.json pit_exit_cones: the pit-exit blend line) becomes the road's left
   * edge for the AI: over the stations the points cover, halfL is capped at the cones' lateral offset minus `margin`
   * (never below 1.5 m). The racing line itself is not moved; where it sits outside the cap the driver's lane clamp
   * pushes the car right of it. Returns the largest overshoot of the racing line past the cap, m (0 = it fits).
   * Owner, 17 Oct 2026: the AI must respect the cones the player is black-flagged for.
   */
  restrictLeft(points: ArrayLike<ArrayLike<number>>, margin = 0.5): number {
    if (!points.length) return 0;
    const sl: [number, number][] = [];
    let hint = -1;
    for (let k = 0; k < points.length; k++) { const p = this.project(points[k][0], points[k][1], hint); hint = p.index; sl.push([p.s, p.lateral]); }
    sl.sort((a, b) => a[0] - b[0]);
    const s0 = sl[0][0], s1 = sl[sl.length - 1][0];
    const latAt = (s: number) => {
      let lo = 0, hi = sl.length - 1;
      while (hi - lo > 1) { const m = (lo + hi) >> 1; if (sl[m][0] <= s) lo = m; else hi = m; }
      const [sa, la] = sl[lo], [sb, lb] = sl[hi];
      return la + (sb > sa ? (s - sa) / (sb - sa) : 0) * (lb - la);
    };
    let over = 0;
    for (let i = 0; i < this.N; i++) {
      const s = i * this.spacing;
      if (s < s0 || s > s1) continue;
      const cap = Math.max(1.5, latAt(s) - margin);
      if (cap < this.halfL[i]) this.halfL[i] = cap;
      over = Math.max(over, this.off[i] - this.halfL[i]);
    }
    return over;
  }

  /** Linear interpolation of a per-station array at s (wrapped). */
  at(arr: ArrayLike<number>, s: number): number {
    const u = this.wrap(s) / this.spacing;
    let i = Math.floor(u); if (i >= this.N) i = this.N - 1;
    const j = i + 1 === this.N ? 0 : i + 1, f = u - i;
    return arr[i] + f * (arr[j] - arr[i]);
  }

  /** Point at s with lateral offset `lat` (+left) from the centre; written to out[0..1]. */
  pointAt(s: number, lat: number, out: Float64Array): void {
    const u = this.wrap(s) / this.spacing;
    let i = Math.floor(u); if (i >= this.N) i = this.N - 1;
    const j = i + 1 === this.N ? 0 : i + 1, f = u - i;
    const x = this.cx[i] + f * (this.cx[j] - this.cx[i]), y = this.cy[i] + f * (this.cy[j] - this.cy[i]);
    out[0] = x - lat * this.ty[i];
    out[1] = y + lat * this.tx[i];
  }

  /** Centre heading at s (rad, from +x toward +y). */
  headingAt(s: number): number {
    const u = this.wrap(s) / this.spacing;
    let i = Math.floor(u); if (i >= this.N) i = this.N - 1;
    return Math.atan2(this.ty[i], this.tx[i]);
  }

  /**
   * Project (x, y) onto the centreline. With a station hint (the previous index) a local walk is used
   * (a few dozen flops); the global hashed projector is the fallback. Returns a reused object.
   */
  project(x: number, y: number, hint = -1): LineProjection {
    const N = this.N, cx = this.cx, cy = this.cy;
    let i = hint;
    if (i >= 0 && i < N) {
      let d = (x - cx[i]) ** 2 + (y - cy[i]) ** 2;
      for (let it = 0; it < 64; it++) {
        const a = i + 1 === N ? 0 : i + 1, b = i === 0 ? N - 1 : i - 1;
        const da = (x - cx[a]) ** 2 + (y - cy[a]) ** 2, db = (x - cx[b]) ** 2 + (y - cy[b]) ** 2;
        if (da < d && da <= db) { i = a; d = da; } else if (db < d) { i = b; d = db; } else break;
      }
      if (d > 900) i = -1; // far from the centre: let the global projector decide
    }
    if (i < 0) {
      const p = this.globalProj.project(x, y);
      this.out.s = p.s; this.out.lateral = p.lateral; this.out.index = p.index;
      return this.out;
    }
    // project onto the two segments next to station i
    let bestD = Infinity;
    for (let k = 0; k < 2; k++) {
      const seg = k === 0 ? (i === 0 ? N - 1 : i - 1) : i;
      const dx = x - cx[seg], dy = y - cy[seg];
      const t = (dx * this.tx[seg] + dy * this.ty[seg]) / this.segLen[seg];
      const tc = t < 0 ? 0 : t > 1 ? 1 : t;
      const px = dx - tc * this.segLen[seg] * this.tx[seg], py = dy - tc * this.segLen[seg] * this.ty[seg];
      const d = px * px + py * py;
      if (d < bestD) {
        bestD = d;
        let s = (seg + tc) * this.spacing;
        if (s >= this.L) s -= this.L;
        this.out.s = s; this.out.index = seg;
        this.out.lateral = -dx * this.ty[seg] + dy * this.tx[seg];
      }
    }
    return this.out;
  }
}
