// Lap timing from the projector's s wrapping past start/finish.
// First crossing starts timing. A lap is invalid if the car spent more than
// 2 s continuously with all four wheels off track (still shown, greyed).

export interface Lap { n: number; time: number; valid: boolean; speedTrace: Float32Array; /** why the lap is invalid when a rule other than the 2 s off-track limit made it so (the pit-exit blend line) */ reason?: string }

const OFF_LIMIT_S = 2;
export const TRACE_GRID_M = 2;

export class LapTimer {
  started = false;
  lapStart = 0;          // sim time of the last crossing
  lapNumber = 0;         // current lap (1-based once started)
  laps: Lap[] = [];
  best: Lap | null = null;
  currentValid = true;
  /** the first rule other than off-track that made the current lap invalid (undefined: none) */
  private invalidReason: string | undefined;
  offTime = 0;           // continuous fully-off-track time
  private prevS = -1;
  private prevT = 0;
  private armed = false; // passed half distance since last crossing
  private trace: Float32Array;

  constructor(readonly length: number) {
    this.trace = this.newTrace();
  }

  private newTrace(): Float32Array {
    return new Float32Array(Math.ceil(this.length / TRACE_GRID_M)).fill(Infinity);
  }

  reset(): void {
    this.started = false; this.prevS = -1; this.armed = false; this.offTime = 0; this.currentValid = true; this.invalidReason = undefined;
    this.trace = this.newTrace();
  }

  /** Make the current lap invalid for a named rule (the first reason is kept). */
  invalidate(reason: string): void {
    if (!this.started) return;
    this.currentValid = false;
    if (this.invalidReason === undefined) this.invalidReason = reason;
  }

  /** reset() plus forget the session's laps and best (mode restart). */
  clearSession(): void {
    this.reset();
    this.laps = []; this.best = null; this.lapNumber = 0; this.lapStart = 0;
  }

  current(simTime: number): number { return this.started ? simTime - this.lapStart : 0; }
  get last(): Lap | null { return this.laps.length ? this.laps[this.laps.length - 1] : null; }
  get currentTrace(): Float32Array { return this.trace; }

  /**
   * Feed the projected s at sim time t. Returns 'start' on the first crossing,
   * the finished Lap when a lap completes, or null.
   */
  update(t: number, s: number, speed: number, allOff: boolean, dt: number): 'start' | Lap | null {
    let event: 'start' | Lap | null = null;
    const L = this.length;
    if (this.prevS >= 0) {
      const crossedFwd = this.prevS > 0.75 * L && s < 0.25 * L;
      if (crossedFwd) {
        const span = (L - this.prevS) + s;
        const f = span > 0 ? (L - this.prevS) / span : 1;
        const tc = this.prevT + f * (t - this.prevT);
        if (!this.started) {
          this.started = true; event = 'start';
        } else if (this.armed) {
          const lap: Lap = { n: this.lapNumber, time: tc - this.lapStart, valid: this.currentValid, speedTrace: this.trace, ...(this.invalidReason !== undefined ? { reason: this.invalidReason } : {}) };
          this.laps.push(lap);
          if (lap.valid && (!this.best || lap.time < this.best.time)) this.best = lap;
          event = lap;
        } else {
          event = null; // crossed again without a lap (e.g. reversed over the line); restart the lap
        }
        if (event !== null || !this.armed) {
          this.lapStart = tc; this.lapNumber = this.laps.length + 1; this.currentValid = true; this.invalidReason = undefined; this.offTime = 0; this.trace = this.newTrace();
          if (event === null && this.started) event = 'start';
        }
        this.armed = false;
      }
    }
    if (s > 0.4 * L && s < 0.6 * L) this.armed = true;
    if (this.started) {
      this.offTime = allOff ? this.offTime + dt : 0;
      if (this.offTime > OFF_LIMIT_S) this.currentValid = false;
      const b = Math.min(this.trace.length - 1, Math.floor(s / TRACE_GRID_M));
      if (speed < this.trace[b]) this.trace[b] = speed;
    }
    this.prevS = s; this.prevT = t;
    return event;
  }
}

/** Minimum of a periodic grid array within ±win metres of s. */
export function minAround(arr: ArrayLike<number>, grid: number, s: number, win = 60): number {
  const n = arr.length;
  const c = Math.round(s / grid), w = Math.round(win / grid);
  let m = Infinity;
  for (let k = -w; k <= w; k++) { const v = arr[((c + k) % n + n) % n]; if (v < m) m = v; }
  return m;
}
