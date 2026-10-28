// Performance tools (docs/performance.md): the ?perf=1 overlay, the per-frame counters it reads, the dev switches and the
// adaptive-quality policy (pure state machine). Nothing here runs unless a switch asks for it: `perf.on` is false by
// default and every probe in the app is `if (perf.on) ...`.
import type { DirectorTiming } from '../physics/ai/race';

/** The dev switches read from the URL. */
export interface PerfFlags {
  /** ?perf=1: the overlay + the director's timing counters + a console line every 10 s */
  perf: boolean;
  /** ?playerai=1 (dev only): the race runs with the player's car AI-driven; never posted */
  playerAi: boolean;
  /** adaptive quality: on unless ?adapt=0 */
  adapt: boolean;
  /** ?lod=1 / ?lod=0: physics LOD for far AI cars; null = the shipped default */
  lod: boolean | null;
  /** ?worker=1 / ?worker=0: physics and AI in a Web Worker for this page load; null = the stored menu choice (default off) */
  worker: boolean | null;
}

const on = (v: string | null) => v === '1' || v === 'true';
const off = (v: string | null) => v === '0' || v === 'false';

export function parsePerfFlags(search: string): PerfFlags {
  const q = new URLSearchParams(search);
  const lod = q.get('lod');
  return {
    perf: on(q.get('perf')),
    playerAi: on(q.get('playerai')),
    adapt: !off(q.get('adapt')),
    lod: on(lod) ? true : off(lod) ? false : null,
    worker: on(q.get('worker')) ? true : off(q.get('worker')) ? false : null,
  };
}

export const WORKER_KEY = 'probeSim.worker.v1';
/** The stored Graphics-menu choice "Physics in a worker (experimental)": off unless set. */
export function storedWorker(): boolean {
  try { return localStorage.getItem(WORKER_KEY) === '1'; } catch { return false; }
}
export function storeWorker(on: boolean): void {
  try { if (on) localStorage.setItem(WORKER_KEY, '1'); else localStorage.removeItem(WORKER_KEY); } catch { /* no storage */ }
}
/** Pure: the `?worker=` URL value (true / false / null = unset) overrides the stored choice for this page load, as `?phone=` does for the tier. */
export function workerChoice(url: boolean | null, stored: boolean): boolean { return url ?? stored; }

export const flags: PerfFlags = parsePerfFlags(typeof location !== 'undefined' ? location.search : '');

/** Per-frame accumulators, ms since the overlay last read them. `on` is the one flag every probe checks. */
export const perf = {
  on: flags.perf,
  frames: 0,
  advance: 0,   // loop.advance: all physics steps of the frame (player + AI + contacts + mode.step)
  poses: 0,     // director.poses() + FieldCars.update (rig posing) + marks
  render: 0,    // look.render: renderer.render / composer.render (CPU submission time)
  hud: 0,       // hud.update + the race HUD DOM + toasts
  audio: 0,     // audio.update + field audio
  frame: 0,     // the whole frame() call
};

export function perfReset(): void {
  perf.frames = 0; perf.advance = 0; perf.poses = 0; perf.render = 0; perf.hud = 0; perf.audio = 0; perf.frame = 0;
}

export const newDirectorTiming = (): DirectorTiming => ({ steps: 0, control: 0, player: 0, aiPhysics: 0, contacts: 0, other: 0 });

// ---------------------------------------------------------------- frame window

/** The last `spanMs` of frame intervals, for the p95 the overlay reads and the miss fractions the adaptive policy reads. */
export class FrameWindow {
  private t: number[] = [];
  private ms: number[] = [];
  constructor(readonly spanMs = 2000) {}
  push(now: number, ms: number): void {
    this.t.push(now); this.ms.push(ms);
    let k = 0;
    while (k < this.t.length && now - this.t[k] > this.spanMs) k++;
    if (k > 0) { this.t.splice(0, k); this.ms.splice(0, k); }
  }
  clear(): void { this.t.length = 0; this.ms.length = 0; }
  get count(): number { return this.ms.length; }
  /** how much of the window is filled: now minus the oldest sample, ms */
  covered(now: number): number { return this.t.length ? now - this.t[0] : 0; }
  /** p in 0..1 (nearest rank); NaN when empty */
  quantile(p: number): number {
    if (!this.ms.length) return NaN;
    const s = [...this.ms].sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.floor(p * s.length))];
  }
  /** the fraction of frames in the window whose interval is above `ms` (0 when empty) */
  fractionAbove(ms: number): number {
    if (!this.ms.length) return 0;
    let n = 0;
    for (const v of this.ms) if (v > ms) n++;
    return n / this.ms.length;
  }
}

// ---------------------------------------------------------------- adaptive quality (pure)

export interface AdaptLevel { shadowCasters: number; maxDrawn: number; ratioCap: number }

/**
 * The ladder from the tier's own numbers (level 0) down: AI shadow casters halved then 0, drawn AI cars to 30, then the
 * pixel-ratio cap in 0.25 steps down to 1.0. Never below the phone tier's numbers (casters 0, 20 cars, ratio 1); steps the
 * tier already sits under are skipped, so a tier with 4 casters goes 4, 2, 0 and a 30-car tier skips the draw step.
 */
export function adaptLadder(base: AdaptLevel): AdaptLevel[] {
  const out: AdaptLevel[] = [{ ...base }];
  const push = (l: AdaptLevel) => {
    const p = out[out.length - 1];
    if (l.shadowCasters !== p.shadowCasters || l.maxDrawn !== p.maxDrawn || l.ratioCap !== p.ratioCap) out.push(l);
  };
  let cur = { ...base };
  if (cur.shadowCasters > 1) { cur = { ...cur, shadowCasters: Math.floor(cur.shadowCasters / 2) }; push(cur); }
  if (cur.shadowCasters > 0) { cur = { ...cur, shadowCasters: 0 }; push(cur); }
  if (cur.maxDrawn > 30) { cur = { ...cur, maxDrawn: 30 }; push(cur); }
  while (cur.ratioCap - 0.25 >= 1.0 - 1e-9) { cur = { ...cur, ratioCap: Math.round((cur.ratioCap - 0.25) * 100) / 100 }; push(cur); }
  if (cur.ratioCap > 1.0 + 1e-9) { cur = { ...cur, ratioCap: 1.0 }; push(cur); }
  return out;
}

// The policy reacts to MISSED frames, not to the interval's p95: at a steady 60 Hz the p95 of the interval reads 17.7-18.4 ms (vsync
// jitter), a missed vsync reads about 33 ms.
export const ADAPT_MISS_MS = 25;        // a frame whose interval is above this missed a vsync
export const ADAPT_MISS_FRAC = 0.05;    // step down when more than this share of the last 2 s was missed
export const ADAPT_OK_MS = 20;          // ... and step back up after ADAPT_UP_HOLD_MS in which fewer than ADAPT_OK_FRAC were above this
export const ADAPT_OK_FRAC = 0.01;
export const ADAPT_STEP_GAP_MS = 3000;  // between two downward steps
export const ADAPT_UP_HOLD_MS = 10_000;
export const ADAPT_SETTLE_MS = 3000;    // no step in the first 3 s after a race build or the tab becoming visible
export const ADAPT_MIN_FRAMES = 30;     // frames in the 2 s window before it is trusted

/** Pure state machine: `missed` = share of the last 2 s above ADAPT_MISS_MS; `slow10` = share of the last 10 s above ADAPT_OK_MS (null until 10 s are in). */
export class AdaptivePolicy {
  level = 0;
  private lastChange = -Infinity;
  constructor(readonly maxLevel: number) {}
  /** Returns the new level when it changed, else null. */
  update(nowMs: number, missed: number, slow10: number | null): number | null {
    if (missed > ADAPT_MISS_FRAC) {
      if (this.level < this.maxLevel && nowMs - this.lastChange >= ADAPT_STEP_GAP_MS) { this.level++; this.lastChange = nowMs; return this.level; }
      return null;
    }
    if (slow10 !== null && slow10 < ADAPT_OK_FRAC && this.level > 0 && nowMs - this.lastChange >= ADAPT_UP_HOLD_MS) {
      this.level--; this.lastChange = nowMs; return this.level;
    }
    return null;
  }
}

/** The adaptive controller the app owns: two frame windows (2 s, 10 s) + a policy over a ladder; `apply` receives the level's numbers. */
export class AdaptiveQuality {
  readonly ladder: AdaptLevel[];
  readonly policy: AdaptivePolicy;
  readonly win = new FrameWindow(2000);
  readonly win10 = new FrameWindow(ADAPT_UP_HOLD_MS);
  /** level changes, for the trace: [time ms, level] */
  readonly trace: [number, number][] = [];
  private lastEval = -Infinity;
  private holdUntil = -Infinity;
  constructor(base: AdaptLevel, private readonly apply: (l: AdaptLevel) => void) {
    this.ladder = adaptLadder(base);
    this.policy = new AdaptivePolicy(this.ladder.length - 1);
  }
  get level(): number { return this.policy.level; }
  get current(): AdaptLevel { return this.ladder[this.policy.level]; }
  /** One rendered frame's interval, ms; evaluates at most 4 times a second. */
  frame(nowMs: number, ms: number): void {
    if (nowMs < this.holdUntil) return;
    this.win.push(nowMs, ms); this.win10.push(nowMs, ms);
    if (nowMs - this.lastEval < 250 || this.win.count < ADAPT_MIN_FRAMES) return;
    this.lastEval = nowMs;
    const slow10 = this.win10.covered(nowMs) >= ADAPT_UP_HOLD_MS - 500 ? this.win10.fractionAbove(ADAPT_OK_MS) : null;
    const lv = this.policy.update(nowMs, this.win.fractionAbove(ADAPT_MISS_MS), slow10);
    if (lv !== null) { this.win.clear(); this.win10.clear(); this.trace.push([nowMs, lv]); this.apply(this.ladder[lv]); }
  }
  /** A hitch, menu or pause: the old samples mean nothing. */
  reset(): void { this.win.clear(); this.win10.clear(); }
  /** A race build or the tab becoming visible: ignore frames (and never step) for ADAPT_SETTLE_MS. */
  hold(nowMs: number): void { this.reset(); this.holdUntil = nowMs + ADAPT_SETTLE_MS; }
}

// ---------------------------------------------------------------- the overlay

export interface OverlayInfo {
  canvas: [number, number];
  ratio: number;
  drawn: number;
  casters: number;
  cars: number;
  level: string;
  director: DirectorTiming | null;
  /** the physics LOD: AI cars at the far rate right now (null: off) */
  lodFar: number | null;
}

/** Fixed top-right monospace box; text written at most 4 times a second from the accumulated counters. */
export class PerfOverlay {
  private el: HTMLPreElement;
  private lastShown = 0;
  private lastLog = 0;
  private win = new FrameWindow(2000);
  private t0 = 0;
  private framesSince = 0;
  private logFrames = 0;
  private log = { fps: 0, p95: 0, frame: 0, advance: 0, render: 0, n: 0 };

  constructor() {
    const el = document.createElement('pre');
    el.id = 'perf-overlay';
    el.setAttribute('aria-hidden', 'true');
    el.style.cssText = 'position:fixed;top:6px;right:6px;z-index:2147483000;margin:0;padding:6px 8px;background:rgba(0,0,0,.72);color:#9f9;'
      + 'font:11px/1.35 ui-monospace,Menlo,monospace;pointer-events:none;white-space:pre;border-radius:4px;min-width:250px';
    document.body.appendChild(el);
    this.el = el;
  }

  /** Call once per rendered frame (not paused) with the frame interval; `info` is called only when the text is rewritten. */
  frame(now: number, intervalMs: number, info: () => OverlayInfo): void {
    if (this.t0 === 0) { this.t0 = now; this.lastShown = now; this.lastLog = now; }
    this.win.push(now, intervalMs);
    this.framesSince++;
    if (now - this.lastShown < 250) return;
    const span = (now - this.lastShown) / 1000, n = Math.max(1, perf.frames);
    const fps = this.framesSince / span;
    const p95 = this.win.quantile(0.95);
    const i = info();
    const d = i.director;
    const per = (v: number) => (v / n).toFixed(2);
    const stepsPerFrame = d ? d.steps / n : 0;
    const dms = (v: number) => (v / n).toFixed(2);
    const lines = [
      `fps ${fps.toFixed(1)}  p95 ${p95.toFixed(1)} ms`,
      `canvas ${i.canvas[0]}x${i.canvas[1]} ${(i.canvas[0] * i.canvas[1] / 1e6).toFixed(2)} MP  ratio ${i.ratio.toFixed(2)}`,
      `AI drawn ${i.drawn}/${i.cars}  shadow casters ${i.casters}  ${i.level}${i.lodFar !== null ? `  LOD far ${i.lodFar}` : ''}`,
      `ms/frame  JS total ${per(perf.frame)}`,
      `  physics (all steps) ${per(perf.advance)}  [${stepsPerFrame.toFixed(1)} steps]`,
      ...(d ? [
        `    player ${dms(d.player)}  AI phys ${dms(d.aiPhysics)}  AI ctl ${dms(d.control)}`,
        `    contacts ${dms(d.contacts)}  traffic/rules ${dms(d.other)}`,
      ] : []),
      `  poses+rigs ${per(perf.poses)}  render ${per(perf.render)}`,
      `  HUD/DOM ${per(perf.hud)}  audio ${per(perf.audio)}`,
    ];
    this.el.textContent = lines.join('\n');
    // 10 s console summary
    this.log.fps += fps * span; this.log.p95 += (Number.isFinite(p95) ? p95 : 0) * span;
    this.log.frame += perf.frame; this.log.advance += perf.advance; this.log.render += perf.render; this.log.n += perf.frames;
    this.logFrames += this.framesSince;
    if (now - this.lastLog >= 10_000) {
      const L = this.log, secs = (now - this.lastLog) / 1000, nn = Math.max(1, L.n);
      console.info(`perf: fps ${(this.logFrames / secs).toFixed(1)} p95 ${(L.p95 / secs).toFixed(1)} ms | JS/frame ${(L.frame / nn).toFixed(2)} (physics ${(L.advance / nn).toFixed(2)}, render ${(L.render / nn).toFixed(2)}) | canvas ${i.canvas[0]}x${i.canvas[1]} ratio ${i.ratio.toFixed(2)} | drawn ${i.drawn}/${i.cars} casters ${i.casters} ${i.level}`);
      this.log = { fps: 0, p95: 0, frame: 0, advance: 0, render: 0, n: 0 };
      this.logFrames = 0; this.lastLog = now;
    }
    this.lastShown = now; this.framesSince = 0;
    perfReset();
    if (d) { d.steps = 0; d.control = 0; d.player = 0; d.aiPhysics = 0; d.contacts = 0; d.other = 0; }
  }

  dispose(): void { this.el.remove(); }
}
