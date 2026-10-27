// Pit-exit blend line (Mid-Ohio round 11, the owner's drive of round 10, 26 Oct 2026: "the 'invalid lap' or black flag for
// crossing into the pit exit at T1 should be pretty strict. It's pretty easy to put two wheels 'off', which IMO should be a
// black flag"). Some circuits paint a line between the pit exit and the course (a ladder of white lines from the pit wall's end
// to the raised kerb that takes over): the package declares it as a polyline (scenery.json `blend_line`) with its pit side.
// Within the line's length (the band):
//   - a car on its lap (it entered the band from the course side) with two or more wheels beyond the line on the pit side is
//     cutting into the pit-exit lane: a violation;
//   - a car leaving the pits (it entered the band from the pit side) with two or more wheels beyond the line on the course
//     side is joining the course before the line's end: a violation.
// Strict, as he asked: a wheel counts as soon as its centre is past the line (grace 0 m by default, GRACE_M; a package may set
// `grace_m`, never more than a wheel's own width). Pure geometry, no state beyond the watch; the player's car only (the callers
// decide: HotlapSim for the hot lap's validity, the race rule engine for the black flag). Packages that declare no line have no
// rule: the watch is never built.

export type Pt = readonly [number, number];

export interface BlendLineJson {
  /** the line, ENU metres, in driving direction */
  pts: readonly (readonly number[])[];
  /** +1: the pit exit lies to the left of the line's driving direction, -1: to the right */
  pit_side: 1 | -1;
  /** the words of the black flag and the invalid-lap reason */
  label?: string;
  /** optional tolerance, m (default GRACE_M = 0) */
  grace_m?: number;
}

/** A wheel counts as across the line as soon as its centre is this far past it (strict: none). */
export const GRACE_M = 0;
/** A wheel's own width: the largest grace a package may declare. */
export const WHEEL_WIDTH_M = 0.2;
/** Wheels across the line that make a violation. */
export const WHEELS_ACROSS = 2;
/** Default words. */
export const BLEND_LINE_LABEL = 'crossed the blend line';

export interface LineHit {
  /** signed distance to the line, m, positive to its left */
  d: number;
  /** true when the nearest point is inside the line's length (not beyond either end) */
  band: boolean;
}

/** Signed distance of points to a polyline and whether they lie within its length. */
export class BlendLine {
  readonly label: string;
  readonly pitSide: 1 | -1;
  readonly grace: number;
  private readonly ax: Float64Array; private readonly ay: Float64Array;
  private readonly dx: Float64Array; private readonly dy: Float64Array; private readonly len: Float64Array;
  private readonly n: number;
  /** length of the line, m */
  readonly length: number;
  /** bounding box grown by `REACH` m: points outside it are far from the line */
  private readonly box: [number, number, number, number];
  private static readonly REACH = 12;

  constructor(json: BlendLineJson) {
    const P = json.pts;
    if (P.length < 2) throw new Error('blend_line needs at least two points');
    this.n = P.length - 1;
    this.ax = new Float64Array(this.n); this.ay = new Float64Array(this.n);
    this.dx = new Float64Array(this.n); this.dy = new Float64Array(this.n); this.len = new Float64Array(this.n);
    let L = 0, x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (let i = 0; i < this.n; i++) {
      this.ax[i] = P[i][0]; this.ay[i] = P[i][1];
      this.dx[i] = P[i + 1][0] - P[i][0]; this.dy[i] = P[i + 1][1] - P[i][1];
      this.len[i] = Math.hypot(this.dx[i], this.dy[i]); L += this.len[i];
    }
    for (const p of P) { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]); }
    this.length = L;
    this.box = [x0 - BlendLine.REACH, y0 - BlendLine.REACH, x1 + BlendLine.REACH, y1 + BlendLine.REACH];
    this.pitSide = json.pit_side === -1 ? -1 : 1;
    this.label = json.label || BLEND_LINE_LABEL;
    this.grace = Math.min(Math.max(json.grace_m ?? GRACE_M, 0), WHEEL_WIDTH_M);
  }

  /** Nearest point of the line to (x, y): the signed distance and whether it lies inside the line's length. */
  locate(x: number, y: number, out: LineHit = { d: 0, band: false }): LineHit {
    const b = this.box;
    if (x < b[0] || y < b[1] || x > b[2] || y > b[3]) { out.d = 0; out.band = false; return out; }
    let best = Infinity, bd = 0, bband = false;
    for (let i = 0; i < this.n; i++) {
      const L = this.len[i];
      if (L < 1e-9) continue;
      const px = x - this.ax[i], py = y - this.ay[i];
      const raw = (px * this.dx[i] + py * this.dy[i]) / (L * L);
      const t = raw < 0 ? 0 : raw > 1 ? 1 : raw;
      const qx = px - t * this.dx[i], qy = py - t * this.dy[i];
      const d2 = qx * qx + qy * qy;
      if (d2 < best) {
        best = d2;
        bd = (this.dx[i] * py - this.dy[i] * px) / L;   // cross(direction, point): positive to the left
        // beyond an end only on the first / last segment; interior joints are inside the line
        bband = !((i === 0 && raw < 0) || (i === this.n - 1 && raw > 1));
      }
    }
    out.d = bd; out.band = bband;
    return out;
  }
}

export type BlendViolation = 'pit_side' | 'course_side';
/** Which way a car entered the band: from the course (on its lap) or from the pit exit (leaving the pits). */
export type BlendMode = 'none' | 'lap' | 'pit';

/** Per-car state: the entry side is fixed when the car's centre first lies inside the band, and holds until it leaves. */
export class BlendLineWatch {
  mode: BlendMode = 'none';
  private readonly hit: LineHit = { d: 0, band: false };
  constructor(readonly line: BlendLine) {}

  reset(): void { this.mode = 'none'; }

  /**
   * One tick. `wheels`: the four wheels (WheelState: `pos` is the hub centre, world [x, y, z]); `cx`, `cy`: the car's centre.
   * Returns the violation this tick shows, or null. Stateless about repeats: the caller debounces (one flag, re-armed after
   * a couple of seconds legal, as the four-wheels-off flag is).
   */
  update(cx: number, cy: number, wheels: readonly { pos: readonly number[] }[]): BlendViolation | null {
    const ln = this.line, h = this.hit;
    ln.locate(cx, cy, h);
    if (!h.band) { this.mode = 'none'; return null; }
    if (this.mode === 'none') this.mode = h.d * ln.pitSide > 0 ? 'pit' : 'lap';
    let across = 0;
    for (const w of wheels) {
      ln.locate(w.pos[0], w.pos[1], h);
      if (!h.band) continue;
      const side = h.d * ln.pitSide;   // positive: pit side
      if (this.mode === 'lap' ? side > ln.grace : side < -ln.grace) across++;
    }
    if (across < WHEELS_ACROSS) return null;
    return this.mode === 'lap' ? 'pit_side' : 'course_side';
  }
}

/**
 * The debounce shared by the callers: a violation fires once and is re-armed after REARM_S of sim time without one (the
 * four-wheels-off flag's rule). Returns the violation to report this tick (or null).
 */
export const REARM_S = 2;
export class BlendFlag {
  private armed = true;
  private legalT = 0;
  constructor(readonly watch: BlendLineWatch) {}
  reset(): void { this.watch.reset(); this.armed = true; this.legalT = 0; }
  update(cx: number, cy: number, wheels: readonly { pos: readonly number[] }[], dt: number): BlendViolation | null {
    const v = this.watch.update(cx, cy, wheels);
    if (v) { this.legalT = 0; if (this.armed) { this.armed = false; return v; } return null; }
    this.legalT += dt;
    if (this.legalT >= REARM_S) this.armed = true;
    return null;
  }
}
