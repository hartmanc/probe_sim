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
  /** ?worker=1: physics and AI in a Web Worker (default off) */
  worker: boolean;
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
    worker: on(q.get('worker')),
  };
}

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

/** The last `spanMs` of frame intervals, for the p95 the overlay and the adaptive policy read. */
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
  /** p in 0..1 (nearest rank); NaN when empty */
  quantile(p: number): number {
    if (!this.ms.length) return NaN;
    const s = [...this.ms].sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.floor(p * s.length))];
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

export const ADAPT_DOWN_MS = 18;       // p95 over the window above this: step down
export const ADAPT_UP_MS = 14;         // p95 below this for ADAPT_UP_HOLD_MS: step back up one level
export const ADAPT_STEP_GAP_MS = 3000; // between two downward steps
export const ADAPT_UP_HOLD_MS = 10_000;

/** Pure state machine: feed it the window's p95 and the clock; it says when the level changes. */
export class AdaptivePolicy {
  level = 0;
  private lastChange = -Infinity;
  private underSince: number | null = null;
  constructor(readonly maxLevel: number) {}
  /** Returns the new level when it changed, else null. `p95` NaN (no data) changes nothing. */
  update(nowMs: number, p95: number): number | null {
    if (!Number.isFinite(p95)) return null;
    if (p95 > ADAPT_DOWN_MS) {
      this.underSince = null;
      if (this.level < this.maxLevel && nowMs - this.lastChange >= ADAPT_STEP_GAP_MS) {
        this.level++; this.lastChange = nowMs;
        return this.level;
      }
      return null;
    }
    if (p95 < ADAPT_UP_MS && this.level > 0) {
      if (this.underSince === null) this.underSince = nowMs;
      if (nowMs - this.underSince >= ADAPT_UP_HOLD_MS) {
        this.level--; this.lastChange = nowMs; this.underSince = nowMs;
        return this.level;
      }
      return null;
    }
    this.underSince = null;
    return null;
  }
}

/** The adaptive controller the app owns: a FrameWindow + a policy over a ladder; `apply` receives the level's numbers. */
export class AdaptiveQuality {
  readonly ladder: AdaptLevel[];
  readonly policy: AdaptivePolicy;
  readonly win = new FrameWindow(2000);
  private lastEval = -Infinity;
  constructor(base: AdaptLevel, private readonly apply: (l: AdaptLevel) => void) {
    this.ladder = adaptLadder(base);
    this.policy = new AdaptivePolicy(this.ladder.length - 1);
  }
  get level(): number { return this.policy.level; }
  get current(): AdaptLevel { return this.ladder[this.policy.level]; }
  /** One rendered frame's interval, ms; evaluates at most 4 times a second. */
  frame(nowMs: number, ms: number): void {
    this.win.push(nowMs, ms);
    if (nowMs - this.lastEval < 250 || this.win.count < 20) return;
    this.lastEval = nowMs;
    const lv = this.policy.update(nowMs, this.win.quantile(0.95));
    if (lv !== null) { this.win.clear(); this.apply(this.ladder[lv]); }
  }
  /** A menu / pause / hitch: the old samples mean nothing. */
  reset(): void { this.win.clear(); }
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
