// Engine voices for the AI field. Each opponent plays its engine family's sample set (built by
// tools/audio/families, same sprite format as the player's public/audio/engine.json): on/off-throttle layers
// cross-faded by throttle, two rpm bins cross-faded by rpm, playbackRate = rpm / loop rpm × trim × Doppler,
// a rev-limiter stutter at the car's redline and a low-pass "muffler". FieldAudio keeps the N nearest cars
// audible, pools the voices, and applies distance gain, equal-power panning and Doppler.
// It never touches the player's CarAudio: it is handed an AudioContext and a destination node from outside.
//
// World axes (src/physics/spec.ts): z up; a car's body x is forward and y is left; quats are [x, y, z, w].
import { binWeights, canPlayOggOpus, decodeSprite, healLoopSeams, shiftIndex, type EngineIndex, type FallbackInfo, type LoopRef } from './audio';

export type Vec3 = [number, number, number];
export type Layout = 'inline' | 'v' | 'flat';

/** A family's engine.json: the Probe's format plus family metadata. */
export interface FamilyEngineIndex extends EngineIndex {
  padding_s?: number;
  family?: string;
  cylinders?: number;
  layout?: Layout;
  fire?: string;
  redline_rpm?: number;
  idle_rpm?: number;
}

export interface FamilyEntry {
  cylinders: number; layout: Layout; redline: number; idle: number;
  engine: string; sprites?: { on: string; off: string };
}

/** public/audio/families/index.json */
export interface FamilyIndex {
  version: number;
  families: Record<string, FamilyEntry>;
  /** [regex source, family id], case-insensitive, tried in order against "engineFamily make model". */
  aliases: [string, string][];
  fallback: { cylinders: number; layout?: Layout; family: string }[];
  default: string;
}

export interface CarEngineGuess { engineFamily?: string; make?: string; model?: string; cylinders?: number; layout?: Layout }

/** Map a car's engine guess (identity.json engine.family / make / model) to a family id. */
export function familyFor(index: FamilyIndex, g: CarEngineGuess): string {
  const s = `${g.engineFamily ?? ''} ${g.make ?? ''} ${g.model ?? ''}`;
  if (g.engineFamily && index.families[g.engineFamily]) return g.engineFamily;
  for (const [re, fam] of index.aliases) {
    try { if (new RegExp(re, 'i').test(s) && index.families[fam]) return fam; } catch { /* bad regex: skip */ }
  }
  if (g.cylinders) {
    const exact = index.fallback.find((f) => f.cylinders === g.cylinders && (!g.layout || f.layout === g.layout));
    if (exact && index.families[exact.family]) return exact.family;
    const cyl = index.fallback.find((f) => f.cylinders === g.cylinders);
    if (cyl && index.families[cyl.family]) return cyl.family;
  }
  return index.default;
}

export interface FamilyAssets {
  index: FamilyEngineIndex;
  on: AudioBuffer;
  off: AudioBuffer;
  binRpm: Float64Array;
  idle: number;
  redline: number;
}

type FetchFn = (url: string) => Promise<{ ok: boolean; json(): Promise<unknown>; arrayBuffer(): Promise<ArrayBuffer> }>;
const defaultFetch: FetchFn = (u) => fetch(u);

const familyCache = new WeakMap<BaseAudioContext, Map<string, Promise<FamilyAssets>>>();

/** Fetch and decode a family's engine.json and its two sprites (cached per context and URL). */
export function loadFamily(ctx: BaseAudioContext, engineJsonUrl: string, fetchFn: FetchFn = defaultFetch): Promise<FamilyAssets> {
  let m = familyCache.get(ctx);
  if (!m) { m = new Map(); familyCache.set(ctx, m); }
  const hit = m.get(engineJsonUrl);
  if (hit) return hit;
  const p = (async () => {
    const get = async (u: string) => { const r = await fetchFn(u); if (!r.ok) throw new Error(`${u}: not ok`); return r; };
    const index = (await (await get(engineJsonUrl)).json()) as FamilyEngineIndex;
    if (!Array.isArray(index?.bins) || !index.bins.length || !index.bins.every((b) => b?.on && b?.off && b.rpm > 0)) {
      throw new Error(`${engineJsonUrl}: no usable bins`); // mid-rebuild / wrong shape: rejected, so retried later
    }
    const dir = engineJsonUrl.slice(0, engineJsonUrl.lastIndexOf('/') + 1);
    const sp = index.sprites ?? { on: 'engine_on.ogg', off: 'engine_off.ogg' };
    // The AAC copy (family blocks have no "squeal"; fallbackShift never reads it).
    const fb = index.fallback?.on && index.fallback?.off ? (index.fallback as FallbackInfo) : undefined;
    const useFb = !!fb && !canPlayOggOpus(); // the browser says no Ogg Opus: straight to the m4a
    const fetchBuf = (f: string) => get(dir + f).then((r) => r.arrayBuffer());
    const dec = (x: ArrayBuffer) => ctx.decodeAudioData(x);
    // Ogg first; a failed fetch or decode falls back to the m4a. With neither working this rejects (retried later).
    const sprite = async (key: 'on' | 'off') => {
      const ogg = useFb ? null : fb ? await fetchBuf(sp[key]).catch(() => null) : await fetchBuf(sp[key]);
      return decodeSprite(dec, ogg, false, () => fetchBuf(fb![key]), fb, key);
    };
    const [on, off] = await Promise.all([sprite('on'), sprite('off')]);
    const index2 = shiftIndex(index, on.shift, off.shift) as FamilyEngineIndex;
    healLoopSeams(on.buffer.getChannelData(0), on.buffer.sampleRate, index2.bins.map((x) => x.on));
    healLoopSeams(off.buffer.getChannelData(0), off.buffer.sampleRate, index2.bins.map((x) => x.off));
    const binRpm = Float64Array.from(index2.bins.map((x) => x.rpm));
    return { index: index2, on: on.buffer, off: off.buffer, binRpm, idle: index.idle_rpm ?? 900, redline: index.redline_rpm ?? binRpm[binRpm.length - 1] };
  })();
  p.catch(() => m!.delete(engineJsonUrl)); // a failed load may be retried
  m.set(engineJsonUrl, p);
  return p;
}

// ------------------------------------------------------------------ one car's engine

export interface VoiceOptions {
  /** Pitch trim factor, 0.96..1.04 (per-car variation within a family). */
  trim?: number;
  /**
   * Opt-in upshift shaping (ShiftDrop): on a gear increment the note falls to the clutch-side rpm (FieldCar.boxRpm)
   * with a fast time constant instead of gliding down with the physics' slipping clutch. Off: the voice plays the
   * physics rpm exactly as before. Fixed at construction.
   */
  shiftDrop?: boolean;
  /** 0 = open exhaust (low-pass at ~12 kHz) … 1 = heavily muffled (~900 Hz). */
  muffler?: number;
  redline?: number;
  idle?: number;
}

const LOAD_UP = 0.035, LOAD_DOWN = 0.07; // throttle-layer lag, s (as in audio.ts)
/** ShiftDrop: time constant of the note's fall to the clutch-side rpm, s (95 % within the 0.15 s torque cut). */
export const SHIFT_DROP_TAU = 0.05;
/** ShiftDrop: longest the note may stay off the physics rpm after an upshift, s (then it blends back). */
export const SHIFT_DROP_MAX_S = 1.0;
/** ShiftDrop: the note rejoins the physics rpm once they are within this fraction. */
export const SHIFT_DROP_MEET = 0.02;

/**
 * Upshift note shaping (round two of the engine sounds, 26 Oct 2026). Through an upshift the physics cuts the torque
 * for 0.15 s and then re-engages its automatic clutch with the throttle back on; the driven wheels spin up to meet the
 * engine and the wheelspin dies away over 0.3-0.6 s, so the engine rpm glides down to the next gear under load (60-75 %
 * of the drop with throttleOut = 1; tools/audio/shift_trace.ts). Played as a loaded loop pitched smoothly through
 * that glide it reads as a sustained, organ-like note; a real upshift drops with the clutch. ShiftDrop: on a gear
 * increment the played rpm leaves the physics rpm and falls with SHIFT_DROP_TAU to the landing rpm (the road-speed
 * clutch-side rpm in the new gear, `boxRpm`, times the slip the engine ran at before the shift), never above the
 * physics rpm; it rejoins the physics rpm once within SHIFT_DROP_MEET of it, or blends back after SHIFT_DROP_MAX_S.
 * Downshifts and frames without gear / boxRpm pass the physics rpm through unchanged. Pure logic (no Web Audio).
 */
export class ShiftDrop {
  private gear = 0;
  private active = false;
  private blending = false;
  private t = 0;
  private r = 0;
  private slip = 1;
  private target = 0;
  /** True while the played rpm is off the physics rpm (diagnostics / tests). */
  get shaping(): boolean { return this.active || this.blending; }
  reset(): void { this.gear = 0; this.active = false; this.blending = false; this.t = 0; this.r = 0; this.slip = 1; this.target = 0; }

  /** The rpm to play this frame. */
  step(rpm: number, gear: number | undefined, boxRpm: number | undefined, dt: number): number {
    if (gear === undefined || boxRpm === undefined || !(boxRpm > 0) || !isFinite(boxRpm)) {
      this.reset();
      return rpm;
    }
    const prev = this.gear;
    this.gear = gear;
    if (gear > prev && prev >= 1 && rpm > boxRpm * this.slip * (1 + SHIFT_DROP_MEET)) {
      // start from the note being played (a second upshift mid-shape continues from where the note is)
      this.r = this.active || this.blending ? Math.min(this.r, rpm) : rpm;
      this.active = true; this.blending = false; this.t = 0;
    } else if (gear < prev && this.active) {
      this.active = false; this.blending = true; // a downshift mid-shape: back to the physics rpm
    }
    if (this.active) {
      this.t += dt;
      this.target = boxRpm * this.slip;
      this.r += (this.target - this.r) * (1 - Math.exp(-dt / SHIFT_DROP_TAU));
      if (this.r > rpm) this.r = rpm;
      if (Math.abs(rpm - this.r) <= SHIFT_DROP_MEET * rpm) { this.active = false; this.r = rpm; return rpm; }
      if (this.t >= SHIFT_DROP_MAX_S) { this.active = false; this.blending = true; }
      else return this.r;
    }
    if (this.blending) {
      this.r += (rpm - this.r) * (1 - Math.exp(-dt / 0.1));
      if (Math.abs(rpm - this.r) <= 0.005 * rpm) { this.blending = false; this.r = rpm; return rpm; }
      return this.r;
    }
    // steady in gear: learn the slip the engine runs at over the road-speed clutch side (wheelspin under power)
    if (gear >= 1) this.slip += (Math.min(1.25, Math.max(1, rpm / boxRpm)) - this.slip) * (1 - Math.exp(-dt / 0.2));
    this.r = rpm;
    return rpm;
  }
}

const LIMITER_HZ = 16;
const N_SRC = 4;

/** Low-pass cutoff (Hz) for a muffler setting, geometric between 12 kHz and 900 Hz. */
export function mufflerCutoff(muffler: number): number {
  const m = Math.min(1, Math.max(0, muffler));
  return 12000 * Math.pow(900 / 12000, m);
}

interface Src { gain: GainNode; src: AudioBufferSourceNode | null; bin: number; load: number; refRpm: number; neededAt: number }

export class EngineVoice {
  readonly output: GainNode;
  private sum: GainNode;
  private gate: GainNode;
  private level: GainNode;
  private lp: BiquadFilterNode;
  private srcs: Src[] = [];
  private bw = new Float64Array(4);
  private load = 0;
  private lastT = -1;
  private limiting = false;
  private opts: Required<Omit<VoiceOptions, 'shiftDrop'>>;
  private shift: ShiftDrop | null;
  disposed = false;

  constructor(private ctx: BaseAudioContext, destination: AudioNode, readonly assets: FamilyAssets, opts: VoiceOptions = {}) {
    this.opts = { trim: 1, muffler: 0.3, redline: assets.redline, idle: assets.idle };
    this.shift = opts.shiftDrop ? new ShiftDrop() : null;
    this.setOptions(opts);
    // sources -> sum -> gate (limiter) -> level -> muffler low-pass -> output (fade / distance) -> destination
    this.sum = ctx.createGain();
    this.gate = ctx.createGain();
    this.level = ctx.createGain(); this.level.gain.value = 0;
    this.lp = ctx.createBiquadFilter();
    this.lp.type = 'lowpass';
    this.lp.Q.value = -6; // Web Audio lowpass Q is in dB: -6 dB = 0.5, a soft knee with no resonance
    this.lp.frequency.value = mufflerCutoff(this.opts.muffler) * 0.45; // closed (load 0) at the start
    this.output = ctx.createGain(); this.output.gain.value = 0;
    this.sum.connect(this.gate).connect(this.level).connect(this.lp).connect(this.output).connect(destination);
    for (let i = 0; i < N_SRC; i++) this.srcs.push({ gain: this.newGain(), src: null, bin: -1, load: -1, refRpm: 1, neededAt: -1 });
  }

  setOptions(o: VoiceOptions): void {
    if (o.trim !== undefined) this.opts.trim = Math.min(1.04, Math.max(0.96, o.trim));
    if (o.muffler !== undefined) this.opts.muffler = o.muffler;
    if (o.redline !== undefined && o.redline > 0) this.opts.redline = o.redline;
    if (o.idle !== undefined && o.idle > 0) this.opts.idle = o.idle;
  }

  private newGain(): GainNode {
    const g = this.ctx.createGain(); g.gain.value = 0; g.connect(this.sum); return g;
  }

  /** Point slot s at (bin, load). The previous source fades out on its own gain node and is stopped. */
  private assign(s: Src, bin: number, load: number, t: number): void {
    if (s.src) {
      const old = s.src, og = s.gain;
      og.gain.cancelScheduledValues(t);
      og.gain.setTargetAtTime(0, t, 0.008);
      try { old.stop(t + 0.06); } catch { /* stopped */ }
      old.onended = () => { old.disconnect(); og.disconnect(); };
      s.gain = this.newGain();
    }
    const a = this.assets, ref: LoopRef = load ? a.index.bins[bin].on : a.index.bins[bin].off;
    const src = this.ctx.createBufferSource();
    src.buffer = load ? a.on : a.off; src.loop = true;
    src.loopStart = ref.offset; src.loopEnd = ref.offset + ref.duration;
    src.connect(s.gain);
    src.start(t, ref.offset + Math.random() * ref.duration);
    s.src = src; s.bin = bin; s.load = load; s.refRpm = ref.rpm ?? a.index.bins[bin].rpm;
  }

  private want(bin: number, load: number, w: number, rate: number, t: number): void {
    let s: Src | null = null;
    for (const c of this.srcs) if (c.bin === bin && c.load === load) { s = c; break; }
    if (!s) {
      if (w < 1e-3) return;
      let oldest = Infinity;
      for (const c of this.srcs) {
        if (c.neededAt === t) continue; // in use this frame
        if (c.bin < 0) { s = c; break; }
        if (c.neededAt < oldest) { oldest = c.neededAt; s = c; }
      }
      if (!s) return;
      this.assign(s, bin, load, t);
    }
    s.neededAt = t;
    s.gain.gain.setTargetAtTime(w, t, 0.012);
    s.src!.playbackRate.setTargetAtTime(Math.max(0.25, rate / s.refRpm), t, 0.008);
  }

  /** The playbackRate a layer of loop rpm `loopRpm` gets at this rpm (rpm / loopRpm × trim × rateFactor). */
  rateFor(rpm: number, loopRpm: number, rateFactor = 1): number { return Math.max(0.25, (rpm * this.opts.trim * rateFactor) / loopRpm); }

  /**
   * Per frame. rateFactor carries the Doppler shift. gear and boxRpm (the clutch-side rpm in the current gear) are
   * only read with the shiftDrop option.
   */
  update(rpm: number, throttle: number, rateFactor: number, t: number, gear?: number, boxRpm?: number): void {
    if (this.disposed) return;
    const dt = this.lastT < 0 ? 0.016 : Math.min(0.1, Math.max(0, t - this.lastT));
    this.lastT = t;
    if (this.shift) rpm = this.shift.step(rpm, gear, boxRpm, dt);
    rpm = Math.max(1, rpm);
    const thr = Math.min(1, Math.max(0, throttle));
    this.load += (thr - this.load) * (1 - Math.exp(-dt / (thr > this.load ? LOAD_UP : LOAD_DOWN)));
    const L = this.load;
    const wOn = Math.sin((L * Math.PI) / 2), wOff = Math.cos((L * Math.PI) / 2);
    const bw = binWeights(this.assets.binRpm, Math.max(rpm, this.opts.idle * 0.6), this.bw);
    const lo = bw[0], wl = bw[1], hi = bw[2], wh = bw[3];
    const r = rpm * this.opts.trim * rateFactor;
    this.want(lo, 1, wl * wOn, r, t);
    this.want(lo, 0, wl * wOff, r, t);
    this.want(hi, 1, wh * wOn, r, t);
    this.want(hi, 0, wh * wOff, r, t);
    for (const s of this.srcs) {
      if (s.bin < 0 || s.neededAt === t) continue;
      s.gain.gain.setTargetAtTime(0, t, 0.012);
      if (s.src) s.src.playbackRate.setTargetAtTime(Math.max(0.25, r / s.refRpm), t, 0.008);
    }
    const level = (0.5 + 0.5 * Math.pow(L, 0.8)) * (0.8 + 0.2 * Math.min(1.2, rpm / this.opts.redline));
    this.level.gain.setTargetAtTime(level, t, 0.02);
    // the muffler sets the open cutoff; lifting closes it further (overrun reads darker)
    this.lp.frequency.setTargetAtTime(mufflerCutoff(this.opts.muffler) * (0.45 + 0.55 * L), t, 0.03);
    // rev limiter: gate at LIMITER_HZ, scheduled ahead on a fixed time grid so frames join seamlessly
    const atLimit = rpm >= this.opts.redline - 60 && thr > 0.5;
    const g = this.gate.gain;
    if (atLimit) {
      g.cancelScheduledValues(t);
      const half = 1 / (2 * LIMITER_HZ);
      let k = Math.floor(t / half);
      g.setTargetAtTime(k % 2 ? 0.15 : 1, t, 0.003);
      for (k++; k * half < t + 0.15; k++) g.setTargetAtTime(k % 2 ? 0.15 : 1, k * half, 0.003);
      this.limiting = true;
    } else if (this.limiting) {
      g.cancelScheduledValues(t);
      g.setTargetAtTime(1, t, 0.005);
      this.limiting = false;
    }
  }

  /** Fade the voice's output gain toward `gain` with time constant tau. */
  fadeTo(gain: number, t: number, tau: number): void {
    this.output.gain.cancelScheduledValues(t);
    this.output.gain.setTargetAtTime(gain, t, tau);
  }

  /** Stop all sources at t (fade first with fadeTo for a click-free stop). */
  stop(t: number): void {
    for (const s of this.srcs) {
      if (s.src) { try { s.src.stop(t); } catch { /* stopped */ } }
      s.src = null; s.bin = -1; s.load = -1; s.neededAt = -1;
      s.gain.gain.cancelScheduledValues(t);
      s.gain.gain.setValueAtTime(0, t);
    }
    this.load = 0;
    this.lastT = -1;
    this.shift?.reset();
  }

  /** Number of live buffer sources (for tests / diagnostics). */
  get sourceCount(): number { return this.srcs.filter((s) => s.src).length; }
  /** Live sources with their loop rpm (for tests / diagnostics). */
  get sources(): { src: AudioBufferSourceNode; refRpm: number; load: number; bin: number }[] {
    return this.srcs.filter((s) => s.src).map((s) => ({ src: s.src!, refRpm: s.refRpm, load: s.load, bin: s.bin }));
  }

  dispose(): void {
    if (this.disposed) return;
    this.stop(this.ctx.currentTime);
    this.disposed = true;
    for (const s of this.srcs) s.gain.disconnect();
    this.sum.disconnect(); this.gate.disconnect(); this.level.disconnect(); this.lp.disconnect(); this.output.disconnect();
  }
}

// ------------------------------------------------------------------ the field

export interface FieldCar {
  id: string | number;
  pos: Vec3; vel: Vec3;
  rpm: number; throttle: number; redline: number;
  family: string;
  trim?: number; muffler?: number;
  /** Current gear and the road-speed clutch-side rpm in it (speed / wheel radius x ratio, x rpm_scale): read by shiftDrop. */
  gear?: number; boxRpm?: number;
}

export interface Listener { pos: Vec3; vel: Vec3; quat?: [number, number, number, number] }

export interface FieldOptions {
  /** Voices at once (8 desktop, FIELD_VOICES_PHONE on phones). */
  maxVoices?: number;
  /** Audible range, m. */
  range?: number;
  /** Base URL of public/audio/families/ (index.json and the family folders). */
  base?: string;
  /** The family index; fetched from base + 'index.json' when absent. */
  index?: FamilyIndex;
  fetchFn?: FetchFn;
  /** Distance at which a voice plays at full gain, m. */
  refDistance?: number;
  /** Lowest distance gain inside the range (before the edge fade). */
  floor?: number;
  /** Upshift note shaping for every voice (VoiceOptions.shiftDrop); off by default. */
  shiftDrop?: boolean;
}

export const FIELD_VOICES_DESKTOP = 8;
export const FIELD_VOICES_PHONE = 4;
export const SPEED_OF_SOUND = 343;
const FADE_IN_TAU = 0.05;  // ≈ 0.15 s to full
const FADE_OUT_TAU = 0.08; // ≈ 0.25 s to silence
const RELEASE_S = 0.5;     // a released voice is reusable (silent) after this
const IDLE_DISPOSE_S = 5;
/** A family whose files failed to load (missing, mid-rebuild) is retried after this long, s. */
export const FAMILY_RETRY_S = 10;

/** Doppler playback factor (c + v_listener·u) / (c − v_source·(−u)), u = listener→source; clamped ±15 %. */
export function dopplerFactor(lp: Vec3, lv: Vec3, sp: Vec3, sv: Vec3, c = SPEED_OF_SOUND): number {
  const dx = sp[0] - lp[0], dy = sp[1] - lp[1], dz = sp[2] - lp[2];
  const d = Math.hypot(dx, dy, dz);
  if (d < 1e-6) return 1;
  const ux = dx / d, uy = dy / d, uz = dz / d;
  const vr = lv[0] * ux + lv[1] * uy + lv[2] * uz;       // listener moving toward the source
  const vs = -(sv[0] * ux + sv[1] * uy + sv[2] * uz);    // source moving toward the listener
  const f = (c + vr) / Math.max(1, c - vs);
  return Math.min(1.15, Math.max(0.85, f));
}

/** Inverse-distance gain with a floor, faded to 0 over the last 20 % of the range. */
export function distanceGain(d: number, range: number, ref = 5, floor = 0.04): number {
  const g = Math.max(floor, ref / Math.max(d, ref));
  const u = Math.min(1, Math.max(0, (range - d) / (0.2 * range)));
  return g * u * u * (3 - 2 * u);
}

/**
 * Ids of the n nearest cars within range. Cars already selected (`current`) count as 10 % nearer and stay
 * eligible out to 105 % of the range, so voices do not flap at the boundaries.
 */
export function selectNearest(listener: Vec3, cars: FieldCar[], n: number, range: number, current?: Set<FieldCar['id']>): FieldCar['id'][] {
  const ranked: [number, FieldCar['id']][] = [];
  for (const c of cars) {
    const d = Math.hypot(c.pos[0] - listener[0], c.pos[1] - listener[1], c.pos[2] - listener[2]);
    const held = current?.has(c.id) ?? false;
    if (d > (held ? 1.05 * range : range)) continue;
    ranked.push([held ? 0.9 * d : d, c.id]);
  }
  ranked.sort((a, b) => a[0] - b[0]);
  return ranked.slice(0, n).map((r) => r[1]);
}

interface PooledVoice {
  voice: EngineVoice;
  panner: PannerNode;
  family: string;
  carId: FieldCar['id'] | null;
  releasedAt: number;
  doppler: number;
}

const rot = (q: [number, number, number, number], v: Vec3): Vec3 => {
  const [x, y, z, w] = q;
  // v' = v + 2w(q×v) + 2 q×(q×v)
  const cx = y * v[2] - z * v[1], cy = z * v[0] - x * v[2], cz = x * v[1] - y * v[0];
  const ccx = y * cz - z * cy, ccy = z * cx - x * cz, ccz = x * cy - y * cx;
  return [v[0] + 2 * (w * cx + ccx), v[1] + 2 * (w * cy + ccy), v[2] + 2 * (w * cz + ccz)];
};

/** Glide a param toward v (tau > 0) or snap it (tau = 0). */
const setParam = (p: AudioParam | undefined, v: number, t: number, tau: number) => {
  if (!p) return;
  if (tau > 0) p.setTargetAtTime(v, t, tau);
  else { p.cancelScheduledValues(t); p.setValueAtTime(v, t); }
};

export class FieldAudio {
  private index: FamilyIndex | null = null;
  private indexP: Promise<FamilyIndex | null>;
  private assets = new Map<string, FamilyAssets>();
  private loading = new Set<string>();
  private failedAt = new Map<string, number>();
  private pool: PooledVoice[] = [];
  private byCar = new Map<FieldCar['id'], PooledVoice>();
  private selected = new Set<FieldCar['id']>();
  readonly maxVoices: number;
  readonly range: number;
  private base: string;
  private fetchFn: FetchFn;
  private ref: number;
  private floor: number;
  private shiftDrop: boolean;
  private lastT = -1;

  constructor(private ctx: BaseAudioContext, private destination: AudioNode, opts: FieldOptions = {}) {
    this.maxVoices = opts.maxVoices ?? FIELD_VOICES_DESKTOP;
    this.range = opts.range ?? 150;
    this.base = opts.base ?? 'audio/families/';
    this.fetchFn = opts.fetchFn ?? defaultFetch;
    this.ref = opts.refDistance ?? 5;
    this.floor = opts.floor ?? 0.04;
    this.shiftDrop = opts.shiftDrop ?? false;
    this.indexP = opts.index
      ? Promise.resolve(opts.index)
      : this.fetchFn(this.base + 'index.json').then((r) => r.json() as Promise<FamilyIndex>).catch(() => null);
    this.indexP.then((i) => { this.index = i; });
  }

  /** Resolves once the family index is known. */
  ready(): Promise<void> { return this.indexP.then(() => undefined); }

  /** Start loading these families now (e.g. the grid's), instead of when the cars first come near. */
  preload(families: string[]): Promise<void> {
    return this.ready().then(() => Promise.all(families.map((f) => this.loadAssets(this.resolve(f)))).then(() => undefined));
  }

  private resolve(f: string): string {
    const i = this.index;
    if (!i) return f;
    return i.families[f] ? f : i.default;
  }

  private loadAssets(fam: string): Promise<FamilyAssets | null> {
    const e = this.index?.families[fam];
    if (!e) return Promise.resolve(null);
    this.loading.add(fam);
    return loadFamily(this.ctx, this.base + e.engine, this.fetchFn)
      .then((a) => { this.assets.set(fam, a); this.failedAt.delete(fam); return a; })
      .catch((err) => {
        if (!this.failedAt.has(fam)) console.warn(`field audio ${fam} (retrying every ${FAMILY_RETRY_S} s):`, err);
        this.failedAt.set(fam, this.ctx.currentTime);
        return null;
      })
      .finally(() => this.loading.delete(fam));
  }

  /** The voice currently given to a car (tests / diagnostics). */
  voiceFor(id: FieldCar['id']): EngineVoice | null { return this.byCar.get(id)?.voice ?? null; }
  /** Doppler factor currently applied to a car's voice. */
  dopplerFor(id: FieldCar['id']): number | null { return this.byCar.get(id)?.doppler ?? null; }
  /** Cars with a voice. */
  get activeIds(): FieldCar['id'][] { return [...this.byCar.keys()]; }
  /** Voices in the pool (active + releasing + idle). */
  get poolSize(): number { return this.pool.length; }

  private newVoice(fam: string, a: FamilyAssets): PooledVoice {
    const ctx = this.ctx;
    const panner = ctx.createPanner();
    panner.panningModel = 'equalpower';
    panner.distanceModel = 'linear';
    panner.rolloffFactor = 0; // our own distance gain
    panner.refDistance = 1; panner.maxDistance = 1e4;
    panner.connect(this.destination);
    const voice = new EngineVoice(ctx, panner, a, this.shiftDrop ? { shiftDrop: true } : {});
    const pv: PooledVoice = { voice, panner, family: fam, carId: null, releasedAt: -Infinity, doppler: 1 };
    this.pool.push(pv);
    return pv;
  }

  private setListener(l: Listener, t: number): void {
    const L = this.ctx.listener as AudioListener & Partial<Record<'positionX' | 'positionY' | 'positionZ' | 'forwardX' | 'forwardY' | 'forwardZ' | 'upX' | 'upY' | 'upZ', AudioParam>>;
    let f: Vec3 = [1, 0, 0], u: Vec3 = [0, 0, 1];
    const tau = this.lastT < 0 ? 0 : 0.01; // snap on the first frame
    if (l.quat) { f = rot(l.quat, [1, 0, 0]); u = rot(l.quat, [0, 0, 1]); }
    else {
      const s = Math.hypot(l.vel[0], l.vel[1]);
      if (s > 0.5) f = [l.vel[0] / s, l.vel[1] / s, 0];
    }
    if (L.positionX) {
      setParam(L.positionX, l.pos[0], t, tau); setParam(L.positionY, l.pos[1], t, tau); setParam(L.positionZ, l.pos[2], t, tau);
      setParam(L.forwardX, f[0], t, tau); setParam(L.forwardY, f[1], t, tau); setParam(L.forwardZ, f[2], t, tau);
      setParam(L.upX, u[0], t, tau); setParam(L.upY, u[1], t, tau); setParam(L.upZ, u[2], t, tau);
    } else {
      L.setPosition(l.pos[0], l.pos[1], l.pos[2]);
      L.setOrientation(f[0], f[1], f[2], u[0], u[1], u[2]);
    }
  }

  /** Per frame: the listener (the player's car / camera) and every AI car. */
  update(listener: Listener, cars: FieldCar[]): void {
    const t = this.ctx.currentTime;
    const dt = this.lastT < 0 ? 0.016 : Math.min(0.1, Math.max(0, t - this.lastT));
    this.setListener(listener, t);
    this.lastT = t;
    const want = new Set(selectNearest(listener.pos, cars, this.maxVoices, this.range, this.selected));
    this.selected = want;

    // release voices whose car left the set
    for (const [id, pv] of this.byCar) {
      if (want.has(id)) continue;
      pv.voice.fadeTo(0, t, FADE_OUT_TAU);
      pv.carId = null; pv.releasedAt = t;
      this.byCar.delete(id);
    }
    for (const pv of this.pool) {
      if (pv.carId === null && t - pv.releasedAt > RELEASE_S && pv.voice.sourceCount > 0) pv.voice.stop(t);
    }

    for (const c of cars) {
      if (!want.has(c.id)) continue;
      let pv = this.byCar.get(c.id);
      let fresh = false;
      if (!pv) {
        if (!this.index) continue;
        const fam = this.resolve(c.family);
        const a = this.assets.get(fam);
        if (!a) {
          const failed = this.failedAt.get(fam);
          if (!this.loading.has(fam) && (failed === undefined || t - failed >= FAMILY_RETRY_S)) void this.loadAssets(fam);
          continue;
        }
        pv = this.pool.find((p) => p.carId === null && p.family === fam && t - p.releasedAt > RELEASE_S && !p.voice.disposed)
          ?? this.newVoice(fam, a);
        pv.carId = c.id; pv.doppler = 1;
        pv.voice.stop(t); // fresh state (silent already)
        pv.voice.output.gain.cancelScheduledValues(t);
        pv.voice.output.gain.setValueAtTime(0, t);
        this.byCar.set(c.id, pv);
        fresh = true;
      }
      pv.voice.setOptions({ trim: c.trim ?? 1, muffler: c.muffler ?? 0.3, redline: c.redline });
      const d = Math.hypot(c.pos[0] - listener.pos[0], c.pos[1] - listener.pos[1], c.pos[2] - listener.pos[2]);
      const df = dopplerFactor(listener.pos, listener.vel, c.pos, c.vel);
      pv.doppler += (df - pv.doppler) * (1 - Math.exp(-dt / 0.1));
      pv.voice.update(c.rpm, c.throttle, pv.doppler, t, c.gear, c.boxRpm);
      pv.voice.fadeTo(distanceGain(d, this.range, this.ref, this.floor), t, FADE_IN_TAU);
      const P = pv.panner as PannerNode & Partial<Record<'positionX' | 'positionY' | 'positionZ', AudioParam>>;
      const ptau = fresh ? 0 : 0.01; // a (re)assigned voice jumps to its car while silent
      if (P.positionX) { setParam(P.positionX, c.pos[0], t, ptau); setParam(P.positionY, c.pos[1], t, ptau); setParam(P.positionZ, c.pos[2], t, ptau); }
      else P.setPosition(c.pos[0], c.pos[1], c.pos[2]);
    }

    // dispose voices idle for a while, keeping at most maxVoices spare
    let spare = 0;
    for (let i = this.pool.length - 1; i >= 0; i--) {
      const pv = this.pool[i];
      if (pv.carId !== null) continue;
      if (t - pv.releasedAt > IDLE_DISPOSE_S || ++spare > this.maxVoices) {
        if (t - pv.releasedAt <= RELEASE_S) continue; // still fading out
        pv.voice.dispose(); pv.panner.disconnect();
        this.pool.splice(i, 1);
      }
    }
  }

  /** Fade everything out and free the nodes. */
  dispose(): void {
    const t = this.ctx.currentTime;
    for (const pv of this.pool) { pv.voice.fadeTo(0, t, 0.02); pv.voice.dispose(); pv.panner.disconnect(); }
    this.pool = []; this.byCar.clear(); this.selected.clear();
  }
}
