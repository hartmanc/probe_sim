// Small geometry helpers over a TrackJson, shared by the stub physics,
// the dev track, ghost synthesis and the scene. Pure functions, ENU frame.
import type { TrackJson, Vec3 } from './physics-types';

export function wrapS(track: TrackJson, s: number): number {
  const L = track.length_m;
  return ((s % L) + L) % L;
}

/** Station index (float) for distance s. */
export function stationAt(track: TrackJson, s: number): { i0: number; i1: number; f: number } {
  const n = track.n;
  const u = wrapS(track, s) / track.spacing_m;
  const i0 = Math.floor(u) % n;
  return { i0, i1: (i0 + 1) % n, f: u - Math.floor(u) };
}

function lerp3(a: Vec3, b: Vec3, f: number): Vec3 {
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
}

/** Unit tangent (x, y) at station i, central difference. */
export function tangentAt(track: TrackJson, i: number): [number, number] {
  const n = track.n;
  const a = track.center[(i - 1 + n) % n];
  const b = track.center[(i + 1) % n];
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const l = Math.hypot(dx, dy) || 1;
  return [dx / l, dy / l];
}

/** Profile height at lateral fraction f in [-1 (left), 1 (right)] at station i. */
export function profileZ(track: TrackJson, i: number, frac: number): number {
  const fr = track.profile.fractions;
  const zs = track.profile.z[i];
  if (frac <= fr[0]) return zs[0];
  for (let k = 0; k < fr.length - 1; k++) {
    if (frac <= fr[k + 1]) {
      const u = (frac - fr[k]) / (fr[k + 1] - fr[k]);
      return zs[k] + (zs[k + 1] - zs[k]) * u;
    }
  }
  return zs[zs.length - 1];
}

/** Half widths (left, right) at station i. */
export function halfWidths(track: TrackJson, i: number): [number, number] {
  const c = track.center[i], l = track.left[i], r = track.right[i];
  return [Math.hypot(l[0] - c[0], l[1] - c[1]), Math.hypot(r[0] - c[0], r[1] - c[1])];
}

/**
 * World point at distance s, lateral offset (+left) from the centre line,
 * z from the cross-section profile. Returns position and heading.
 */
export function pointAt(track: TrackJson, s: number, offset: number): { pos: Vec3; heading: number } {
  const { i0, i1, f } = stationAt(track, s);
  const c = lerp3(track.center[i0], track.center[i1], f);
  const t0 = tangentAt(track, i0), t1 = tangentAt(track, i1);
  let tx = t0[0] + (t1[0] - t0[0]) * f, ty = t0[1] + (t1[1] - t0[1]) * f;
  const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
  const nx = -ty, ny = tx;
  const [hl, hr] = halfWidths(track, i0);
  // fraction: -1 = left edge, +1 = right edge
  const frac = offset >= 0 ? -offset / Math.max(hl, 0.1) : -offset / Math.max(hr, 0.1);
  const z0 = profileZ(track, i0, frac), z1 = profileZ(track, i1, frac);
  return {
    pos: [c[0] + nx * offset, c[1] + ny * offset, z0 + (z1 - z0) * f],
    heading: Math.atan2(ty, tx),
  };
}

/** Signed curvature (+left) per station, from heading change over ±k stations. */
export function curvatures(track: TrackJson, k = 6): Float32Array {
  const n = track.n;
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const a = tangentAt(track, (i - k + n) % n);
    const b = tangentAt(track, (i + k) % n);
    const dh = Math.atan2(a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1]);
    out[i] = dh / (2 * k * track.spacing_m);
  }
  return out;
}

// ---------------------------------------------------------------- pit-exit cones (scenery.json pit_exit_cones)
type P2 = [number, number];

/** True if segment p0-p1 intersects segment a-b (touching counts). */
function segmentsCross(p0: P2, p1: P2, a: P2, b: P2): boolean {
  const d = (o: P2, u: P2, v: P2) => (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0]);
  const d1 = d(a, b, p0), d2 = d(a, b, p1), d3 = d(p0, p1, a), d4 = d(p0, p1, b);
  if (((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))) return true;
  const on = (o: P2, u: P2, q: P2) => Math.min(o[0], u[0]) <= q[0] && q[0] <= Math.max(o[0], u[0]) && Math.min(o[1], u[1]) <= q[1] && q[1] <= Math.max(o[1], u[1]);
  return (d1 === 0 && on(a, b, p0)) || (d2 === 0 && on(a, b, p1)) || (d3 === 0 && on(p0, p1, a)) || (d4 === 0 && on(p0, p1, b));
}

/** True if the segment p0-p1 (e.g. a car's move between two samples) intersects the open polyline `line`. */
export function crossesPolyline(p0: P2, p1: P2, line: P2[]): boolean {
  const x0 = Math.min(p0[0], p1[0]), x1 = Math.max(p0[0], p1[0]), y0 = Math.min(p0[1], p1[1]), y1 = Math.max(p0[1], p1[1]);
  for (let k = 0; k + 1 < line.length; k++) {
    const a = line[k], b = line[k + 1];
    if (Math.max(a[0], b[0]) < x0 || Math.min(a[0], b[0]) > x1 || Math.max(a[1], b[1]) < y0 || Math.min(a[1], b[1]) > y1) continue;
    if (segmentsCross(p0, p1, a, b)) return true;
  }
  return false;
}

/** Distance from point p to the open polyline `line` (m). */
export function distanceToPolyline(p: P2, line: P2[]): number {
  let best = Infinity;
  for (let k = 0; k + 1 < line.length; k++) {
    const a = line[k], b = line[k + 1];
    const ux = b[0] - a[0], uy = b[1] - a[1], l2 = ux * ux + uy * uy;
    const t = l2 > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * ux + (p[1] - a[1]) * uy) / l2)) : 0;
    best = Math.min(best, Math.hypot(p[0] - a[0] - ux * t, p[1] - a[1] - uy * t));
  }
  if (line.length === 1) best = Math.hypot(p[0] - line[0][0], p[1] - line[0][1]);
  return best;
}

/** scenery.json `pit_exit_cones` (CONTRACTS §2b): the cone line between the pit-exit lane and the track. */
export interface PitExitConesJson { spacing_m: number; s0: number; s1: number; pts: [number, number, number][]; src?: string;
  /** round 7: cone colour (default the orange traffic cone) and height in m (default 0.7) from the evidence */ color?: string; size?: number }

/**
 * Reports crossings of the pit-exit cone line from the car's successive positions (ENU x, y). One crossing is one
 * event: after an event the detector re-arms only once the car is `rearmM` from the line, so crossing back (or
 * weaving along the line) does not count again. Jumps longer than `maxJumpM` (resets, teleports) are ignored.
 * Usage: `if (cones.update(x, y)) penalise()`; call `clear()` on reset.
 */
export class PitExitCones {
  readonly line: P2[];
  private prev: P2 | null = null;
  private armed = true;
  count = 0;
  constructor(data: PitExitConesJson | { pts: [number, number, number][] | [number, number][] }, private rearmM = 4, private maxJumpM = 25) {
    this.line = data.pts.map((p) => [p[0], p[1]] as P2);
  }
  /** Forget the previous position (call after a reset or teleport). */
  clear(): void { this.prev = null; this.armed = true; }
  /** Feed the car's position; true exactly once per crossing. */
  update(x: number, y: number): boolean {
    const p: P2 = [x, y];
    const q = this.prev;
    this.prev = p;
    if (this.line.length < 2) return false;
    if (!this.armed) {
      if (distanceToPolyline(p, this.line) > this.rearmM) this.armed = true;
      return false;
    }
    if (!q || Math.hypot(x - q[0], y - q[1]) > this.maxJumpM) return false;
    if (!crossesPolyline(q, p, this.line)) return false;
    this.armed = false;
    this.count++;
    return true;
  }
}
