// Car-vs-car contacts: oriented boxes (car.json hull: front / rear / halfWidth, horizontal footprint
// along the body heading) between every pair of nearby cars, impulse-based with low restitution and
// Coulomb friction, plus a clamped positional push-out. Applied through the Vehicle contact hooks
// (pointVelocity / invMassAt / applyImpulseAt / nudge / reportImpact) between physics steps.
//
// Broad phase: the caller passes the cars' order along the track (sorted by s once per step); only
// neighbours within `reach` metres along s are tested, so the cost is ~O(n). The contact point is
// placed at each car's CG height, so impulses give yaw but no roll (no launches off a bump).

import { hypot as dhypot } from './dmath';   // bit-identical to V8 on every engine (docs/determinism.md)
import type { Vehicle } from './vehicle';

export interface CarBody {
  vehicle: Vehicle;
  /** hull front (+, m), hull rear (negative, m), half width (m), body frame */
  front: number; rear: number; halfWidth: number;
  /** skip this car (e.g. removed from the race) */
  ghost?: boolean;
}

export interface CarContactEvent {
  /** car indices; the normal points from a to b */
  a: number; b: number;
  nx: number; ny: number;
  /** contact point, world */
  x: number; y: number;
  /** closing speed along the normal before the impulse, m/s (> 0 = approaching) */
  closing: number;
  /** each car's own velocity toward the other along the normal (world frame), m/s: who closed in */
  aApproach: number; bApproach: number;
  /** normal impulse applied, N·s */
  impulse: number;
  depth: number;
}

export interface CarColliderOptions {
  restitution?: number;   // default 0.2
  friction?: number;      // default 0.35
  /** along-track reach of the broad phase, m (default 7) */
  reach?: number;
  /** solver passes over the contact list (default 3) */
  iterations?: number;
}

const MAX_EVENTS = 128;

export class CarCollider {
  readonly e: number; readonly mu: number; readonly reach: number; readonly iters: number;
  /** contacts found in the last resolve() (first `count` entries are valid; objects are reused) */
  readonly events: CarContactEvent[] = [];
  count = 0;
  /** total contacts / max penetration seen (diagnostics) */
  totalContacts = 0; maxDepth = 0;
  private readonly va = new Float64Array(3); private readonly vb = new Float64Array(3);
  private readonly cs = new Float64Array(8); // box: cx, cy, fx, fy, lx, ly, hl, hw
  private readonly cs2 = new Float64Array(8);
  private readonly vtx = new Float64Array(8);

  constructor(opts: CarColliderOptions = {}) {
    this.e = opts.restitution ?? 0.2;
    this.mu = opts.friction ?? 0.35;
    this.reach = opts.reach ?? 7;
    this.iters = opts.iterations ?? 3;
    for (let k = 0; k < MAX_EVENTS; k++) this.events.push({ a: 0, b: 0, nx: 0, ny: 0, x: 0, y: 0, closing: 0, aApproach: 0, bApproach: 0, impulse: 0, depth: 0 });
  }

  private box(c: CarBody, out: Float64Array): void {
    const st = c.vehicle.state;
    const [qx, qy, qz, qw] = st.quat;
    // body x axis in world, projected on the ground plane
    let fx = 1 - 2 * (qy * qy + qz * qz), fy = 2 * (qx * qy + qz * qw);
    const l = dhypot(fx, fy) || 1;
    fx /= l; fy /= l;
    const mid = 0.5 * (c.front + c.rear);
    out[0] = st.pos[0] + fx * mid; out[1] = st.pos[1] + fy * mid;
    out[2] = fx; out[3] = fy; out[4] = -fy; out[5] = fx;
    out[6] = 0.5 * (c.front - c.rear); out[7] = c.halfWidth;
  }

  /**
   * Find and resolve contacts. `order` = car indices sorted by track s, `s` = each car's s (wrapped),
   * L = lap length. Returns the number of contact events (this.events[0..count-1]).
   */
  resolve(cars: CarBody[], order: Int32Array, s: Float64Array, L: number): number {
    const n = cars.length;
    this.count = 0;
    if (n < 2) return 0;
    for (let k = 0; k < n; k++) {
      const a = order[k];
      if (cars[a].ghost) continue;
      for (let m = 1; m < n; m++) {
        const b = order[(k + m) % n];
        let d = s[b] - s[a];
        if (d < 0) d += L;
        if (d > this.reach) break;
        if (cars[b].ghost) continue;
        this.pair(cars, a, b);
      }
    }
    // a few sequential-impulse passes for stacks of cars (3-wide etc.)
    for (let it = 1; it < this.iters; it++) {
      for (let k = 0; k < this.count; k++) this.impulse(cars, this.events[k], false);
    }
    return this.count;
  }

  private pair(cars: CarBody[], a: number, b: number): void {
    const A = cars[a], B = cars[b];
    const pa = A.vehicle.state.pos, pb = B.vehicle.state.pos;
    const dx0 = pb[0] - pa[0], dy0 = pb[1] - pa[1];
    const ra = Math.max(A.front, -A.rear) + A.halfWidth, rb = Math.max(B.front, -B.rear) + B.halfWidth;
    if (dx0 * dx0 + dy0 * dy0 > (ra + rb) * (ra + rb)) return;
    if (Math.abs(pb[2] - pa[2]) > 2.5) return;
    const bA = this.cs, bB = this.cs2;
    this.box(A, bA); this.box(B, bB);
    const dx = bB[0] - bA[0], dy = bB[1] - bA[1];
    // SAT over the four face normals
    let best = Infinity, nx = 0, ny = 0, fromA = true;
    for (let ax = 0; ax < 4; ax++) {
      const src = ax < 2 ? bA : bB;
      const ux = ax % 2 === 0 ? src[2] : src[4], uy = ax % 2 === 0 ? src[3] : src[5];
      const rA = bA[6] * Math.abs(bA[2] * ux + bA[3] * uy) + bA[7] * Math.abs(bA[4] * ux + bA[5] * uy);
      const rB = bB[6] * Math.abs(bB[2] * ux + bB[3] * uy) + bB[7] * Math.abs(bB[4] * ux + bB[5] * uy);
      const dp = dx * ux + dy * uy;
      const o = rA + rB - Math.abs(dp);
      if (o <= 0) return;
      if (o < best) { best = o; const sg = dp >= 0 ? 1 : -1; nx = ux * sg; ny = uy * sg; fromA = ax < 2; }
    }
    // contact point: the incident box's vertices deepest along the normal (averaged when a face is flush)
    const inc = fromA ? bB : bA;
    const dir = fromA ? -1 : 1; // B's vertices most toward A (−n), or A's most toward B (+n)
    const vt = this.vtx;
    let k = 0;
    for (const su of [-1, 1]) for (const sv of [-1, 1]) {
      vt[k++] = inc[0] + su * inc[6] * inc[2] + sv * inc[7] * inc[4];
      vt[k++] = inc[1] + su * inc[6] * inc[3] + sv * inc[7] * inc[5];
    }
    let mn = Infinity;
    for (let q = 0; q < 4; q++) mn = Math.min(mn, dir * (vt[2 * q] * nx + vt[2 * q + 1] * ny));
    let px = 0, py = 0, cnt = 0;
    for (let q = 0; q < 4; q++) {
      if (dir * (vt[2 * q] * nx + vt[2 * q + 1] * ny) <= mn + 0.08) { px += vt[2 * q]; py += vt[2 * q + 1]; cnt++; }
    }
    px /= cnt; py /= cnt;
    // move the point half the depth toward the reference box so it sits between the two
    px += dir * nx * 0.5 * best; py += dir * ny * 0.5 * best;
    if (this.count >= MAX_EVENTS) return;
    const ev = this.events[this.count++];
    ev.a = a; ev.b = b; ev.nx = nx; ev.ny = ny; ev.x = px; ev.y = py; ev.depth = best; ev.impulse = 0;
    const va = A.vehicle.state.vel, vb = B.vehicle.state.vel;
    ev.aApproach = va[0] * nx + va[1] * ny;
    ev.bApproach = -(vb[0] * nx + vb[1] * ny);
    this.totalContacts++;
    if (best > this.maxDepth) this.maxDepth = best;
    this.impulse(cars, ev, true);
    // push-out, split by inverse mass, clamped so it never explodes
    const ma = 1 / A.vehicle.spec.mass, mb = 1 / B.vehicle.spec.mass;
    let push = Math.max(0, best - 0.01) * 0.25;
    if (push > 0.01) push = 0.01;
    if (push > 0) {
      const fa = ma / (ma + mb), fb = mb / (ma + mb);
      A.vehicle.nudge(-nx * push * fa, -ny * push * fa);
      B.vehicle.nudge(nx * push * fb, ny * push * fb);
    }
  }

  /** Normal + friction impulse at an event (first pass also records closing speed and impact). */
  private impulse(cars: CarBody[], ev: CarContactEvent, first: boolean): void {
    const A = cars[ev.a].vehicle, B = cars[ev.b].vehicle;
    const za = A.cgWorld[2], zb = B.cgWorld[2];
    const nx = ev.nx, ny = ev.ny;
    A.pointVelocity(ev.x, ev.y, za, this.va);
    B.pointVelocity(ev.x, ev.y, zb, this.vb);
    const rvx = this.vb[0] - this.va[0], rvy = this.vb[1] - this.va[1];
    const vn = rvx * nx + rvy * ny; // < 0 approaching
    if (first) {
      ev.closing = -vn;
      if (-vn > 0.5) { A.reportImpact(-vn, 'car'); B.reportImpact(-vn, 'car'); }
    }
    if (vn >= 0) return;
    const kA = A.invMassAt(ev.x, ev.y, za, nx, ny, 0), kB = B.invMassAt(ev.x, ev.y, zb, nx, ny, 0);
    const e = ev.closing > 1 ? this.e : 0;
    const j = (-(1 + e) * vn) / (kA + kB);
    A.applyImpulseAt(ev.x, ev.y, za, -nx * j, -ny * j, 0);
    B.applyImpulseAt(ev.x, ev.y, zb, nx * j, ny * j, 0);
    ev.impulse += j;
    // friction along the sliding direction
    A.pointVelocity(ev.x, ev.y, za, this.va);
    B.pointVelocity(ev.x, ev.y, zb, this.vb);
    let tx = this.vb[0] - this.va[0], ty = this.vb[1] - this.va[1];
    const vnn = tx * nx + ty * ny;
    tx -= vnn * nx; ty -= vnn * ny;
    const vt = dhypot(tx, ty);
    if (vt < 1e-4) return;
    tx /= vt; ty /= vt;
    const kt = A.invMassAt(ev.x, ev.y, za, tx, ty, 0) + B.invMassAt(ev.x, ev.y, zb, tx, ty, 0);
    const jt = Math.min(vt / kt, this.mu * j);
    A.applyImpulseAt(ev.x, ev.y, za, tx * jt, ty * jt, 0);
    B.applyImpulseAt(ev.x, ev.y, zb, -tx * jt, -ty * jt, 0);
  }
}
