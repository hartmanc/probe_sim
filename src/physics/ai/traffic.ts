// Per-step snapshot of every car on track (AI and player), sorted by s once per step, so that each
// driver's neighbour query is a short walk along the order instead of an O(n) scan.

export class Traffic {
  readonly n: number;
  readonly L: number;
  /** track position (wrapped, m), lateral offset from the centre (+left, m), forward speed (m/s) */
  readonly s: Float64Array; readonly lat: Float64Array; readonly v: Float64Array;
  /** unwrapped distance (m): race distance, grid cars start negative (before the line) */
  readonly U: Float64Array;
  /** low-passed forward acceleration, m/s² (the director updates it) */
  readonly a: Float64Array;
  /** hull front (+), rear (as a positive distance) and half width, m */
  readonly front: Float64Array; readonly rear: Float64Array; readonly hw: Float64Array;
  /** 1 = not a traffic obstacle on the racing surface (far off track, e.g. in the pit lane) */
  readonly away: Uint8Array;
  /** 1 = off the track / recovering (others pass it freely, also under yellow) */
  readonly off: Uint8Array;
  /** target lap of each car, s (a pace hint for overtaking decisions) */
  readonly pace: Float64Array;
  /** index of the car each driver is passing (-1 = none; drivers write it) */
  readonly passing: Int32Array;
  /** low-passed lateral velocity, m/s (+ left; the director updates it) */
  readonly vlat: Float64Array;
  /**
   * Lane model (NOTES "Racecraft (the lane model) and mishaps"): lane coordinate e = lateral offset from the racing line (m, + left),
   * measured (the director, each step) and aimed for (eT: each AI driver publishes its target; a human player's is its
   * current e plus 0.5 s of lateral drift). A car occupies [min(e, eT) - hw, max(e, eT) + hw] laterally.
   */
  readonly e: Float64Array; readonly eT: Float64Array;
  /** low-passed rate of e, m/s (a car drifting off its target, e.g. sliding wide, shows it here) */
  readonly ve: Float64Array;
  /** (C2, the offset planner) 1: this car holds an offset off the racing line with a car within 30 m ahead (a pass in hand) */
  readonly oPass: Uint8Array;
  /** (C4, the offset planner) the car this car attacks (-1 none) and the side it commits to (+1 left / -1 right, 0 none) */
  readonly oAtt: Int32Array; readonly oSide: Int8Array;
  /** (L1, RaceConfig.cornerPass) the car this car holds its side of through a corner (it had the overlap at that car's turn-in; -1 none) */
  readonly cpHold: Int32Array;
  /** lane spacing, m (>= widest car + 0.6 m; the director sets it from the field) */
  laneW = 2.6;
  /** each AI car's target speed profile per station (null for a human player): per-corner speed comparisons */
  readonly profile: (Float64Array | null)[];
  /** car indices sorted by s ascending; rank[i] = position of car i in order */
  readonly order: Int32Array; readonly rank: Int32Array;

  constructor(n: number, L: number) {
    this.n = n; this.L = L;
    this.s = new Float64Array(n); this.lat = new Float64Array(n); this.v = new Float64Array(n); this.U = new Float64Array(n); this.a = new Float64Array(n);
    this.front = new Float64Array(n); this.rear = new Float64Array(n); this.hw = new Float64Array(n);
    this.away = new Uint8Array(n); this.off = new Uint8Array(n); this.pace = new Float64Array(n);
    this.e = new Float64Array(n); this.eT = new Float64Array(n); this.ve = new Float64Array(n);
    this.oPass = new Uint8Array(n);
    this.oAtt = new Int32Array(n).fill(-1); this.oSide = new Int8Array(n);
    this.cpHold = new Int32Array(n).fill(-1);
    this.passing = new Int32Array(n).fill(-1); this.vlat = new Float64Array(n); this.profile = new Array(n).fill(null);
    this.order = new Int32Array(n); this.rank = new Int32Array(n);
    for (let i = 0; i < n; i++) this.order[i] = i;
  }

  /** Insertion sort by s (the order barely changes between steps, so this is ~O(n)). */
  sort(): void {
    const o = this.order, s = this.s;
    for (let i = 1; i < this.n; i++) {
      const k = o[i], sk = s[k];
      let j = i - 1;
      while (j >= 0 && s[o[j]] > sk) { o[j + 1] = o[j]; j--; }
      o[j + 1] = k;
    }
    for (let i = 0; i < this.n; i++) this.rank[o[i]] = i;
  }

  /** Signed along-track distance from car i to car j, wrapped into [-L/2, L/2). */
  ds(i: number, j: number): number {
    let d = this.s[j] - this.s[i];
    const h = 0.5 * this.L;
    if (d >= h) d -= this.L; else if (d < -h) d += this.L;
    return d;
  }
}
