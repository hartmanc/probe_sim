// Car audio. Engine = loops cut from the team's onboard race footage of this car (Mazda KL-DE 2.5 V6), one per
// 250 rpm bin and load (on/off throttle), played back at rpm / binRpm and cross-faded; tyre squeal = a loop cut
// from the same footage; road rumble and wind = filtered noise. Built by tools/audio (see its README).
// The AudioContext starts on the first user gesture (browsers block autoplay); the files are fetched at boot.
import type { VehicleState, WheelState } from './physics-types';

/** Fallback tyre peaks when the physics does not publish WheelState.slipUse (the stub) and car.json has none. */
export const PEAK_SLIP_ANGLE = 0.122; // rad (7°, car.json tyre.lateral.peakSlipAngleDeg)
export const PEAK_SLIP_RATIO = 0.12;  // car.json tyre.longitudinal.peakSlipRatio
/** Squeal is silent below SQUEAL_START × the tyre peak and full at SQUEAL_FULL × the peak. */
export const SQUEAL_START = 0.85, SQUEAL_FULL = 1.3;
/** Wheels carrying less than this (N) do not squeal (an unloaded inside wheel spins silently). */
export const SQUEAL_MIN_LOAD = 1500;
/** No squeal below this speed (m/s). */
export const SQUEAL_MIN_SPEED = 5;

export interface LoopRef { offset: number; duration: number; rpm?: number }
export interface EngineBin { rpm: number; on: LoopRef; off: LoopRef }
export type SpriteKey = 'on' | 'off' | 'squeal';
/** AAC (.m4a) copies of the sprites for browsers without Ogg Opus decoding (tools/audio/encode_fallback.py). */
export interface FallbackInfo {
  on: string; off: string; squeal: string;
  /** Seconds the AAC decode lags the Opus decode (edit list applied); per file in offsets_s when measured. */
  offset_s: number;
  offsets_s?: Partial<Record<SpriteKey, number>>;
  /** Encoder priming (s): extra leading audio from a decoder that ignores the MP4 edit list. */
  priming_s?: number;
  /** Decoded length (s) with the edit list applied, per file: a longer decode means the priming was kept. */
  lengths_s?: Partial<Record<SpriteKey, number>>;
}
export interface EngineIndex { sampleRate: number; bins: EngineBin[]; sprites?: { on: string; off: string }; fallback?: FallbackInfo }

/**
 * Seconds to add to every loop offset of sprite `key` when it was decoded from the AAC fallback and came back
 * `decodedS` seconds long: the measured codec offset, plus the encoder priming if this decoder kept it.
 */
export function fallbackShift(fb: FallbackInfo, key: SpriteKey, decodedS: number): number {
  const base = fb.offsets_s?.[key] ?? fb.offset_s ?? 0;
  const len = fb.lengths_s?.[key], pr = fb.priming_s ?? 0;
  if (len != null && pr > 0 && decodedS - len > pr / 2) return base + pr;
  return base;
}

/** A copy of the index with the on / off loop offsets moved by the given seconds (fallback decode). */
export function shiftIndex(index: EngineIndex, onS: number, offS: number): EngineIndex {
  if (!onS && !offS) return index;
  return {
    ...index,
    bins: index.bins.map((b) => ({ ...b, on: { ...b.on, offset: b.on.offset + onS }, off: { ...b.off, offset: b.off.offset + offS } })),
  };
}

/** Minimal decoder surface (BaseAudioContext.decodeAudioData), so the fallback logic is testable. */
export type Decode<B extends { duration: number }> = (data: ArrayBuffer) => Promise<B>;

/**
 * Decode one sprite: the Ogg Opus file first (unless `primary` already is the fallback), then the AAC fallback
 * on failure. Returns the buffer and the shift (s) to apply to its loop offsets.
 */
export async function decodeSprite<B extends { duration: number }>(
  decode: Decode<B>, primary: ArrayBuffer | null, primaryIsFallback: boolean,
  loadFallback: () => Promise<ArrayBuffer | null>, fb: FallbackInfo | undefined, key: SpriteKey,
): Promise<{ buffer: B; shift: number; fallback: boolean }> {
  if (primary && !primaryIsFallback) {
    try { return { buffer: await decode(primary), shift: 0, fallback: false }; } catch (e) {
      if (!fb) throw e;
      console.warn(`audio: ${key} Ogg decode failed, using the AAC fallback`, e);
    }
  }
  if (!fb) throw new Error(`audio: ${key} missing`);
  const data = primaryIsFallback && primary ? primary : await loadFallback();
  if (!data) throw new Error(`audio: ${key} fallback missing`);
  const buffer = await decode(data);
  return { buffer, shift: fallbackShift(fb, key, buffer.duration), fallback: true };
}

/** Whether this browser can play Ogg Opus (a hint; a failed decode still falls back). */
export function canPlayOggOpus(): boolean {
  try {
    if (typeof document === 'undefined') return true;
    const a = document.createElement('audio');
    return !!a.canPlayType && a.canPlayType('audio/ogg; codecs="opus"') !== '';
  } catch { return true; }
}

export interface AudioCarParams {
  idleRpm: number;
  revLimitRpm: number;
  peakSlipAngle: number; // rad
  peakSlipRatio: number;
}

/** Engine parameters and tyre peaks from car.json (same numbers as physics tyrePeakSlip(spec)). */
export function audioParamsFromCarJson(json: unknown): AudioCarParams {
  const j = (json ?? {}) as { engine?: { idleRpm?: number; revLimitRpm?: number };
    tyre?: { lateral?: { peakSlipAngleDeg?: number }; longitudinal?: { peakSlipRatio?: number } } };
  const num = (v: unknown, d: number) => (typeof v === 'number' && isFinite(v) && v > 0 ? v : d);
  return {
    idleRpm: num(j.engine?.idleRpm, 850),
    revLimitRpm: num(j.engine?.revLimitRpm, 6900),
    peakSlipAngle: (num(j.tyre?.lateral?.peakSlipAngleDeg, (PEAK_SLIP_ANGLE * 180) / Math.PI) * Math.PI) / 180,
    peakSlipRatio: num(j.tyre?.longitudinal?.peakSlipRatio, PEAK_SLIP_RATIO),
  };
}

const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };

/**
 * The two bins around rpm and their equal-power weights. Writes into `out` (no allocation):
 * out[0] = lower bin index, out[1] = its weight, out[2] = upper bin index, out[3] = its weight.
 */
export function binWeights(binRpm: ArrayLike<number>, rpm: number, out: Float64Array): Float64Array {
  const n = binRpm.length;
  if (rpm <= binRpm[0] || n === 1) { out[0] = 0; out[1] = 1; out[2] = Math.min(1, n - 1); out[3] = 0; return out; }
  if (rpm >= binRpm[n - 1]) { out[0] = n - 2; out[1] = 0; out[2] = n - 1; out[3] = 1; return out; }
  let i = 0;
  while (i < n - 2 && rpm >= binRpm[i + 1]) i++;
  const u = (rpm - binRpm[i]) / (binRpm[i + 1] - binRpm[i]);
  out[0] = i; out[1] = Math.cos((u * Math.PI) / 2); out[2] = i + 1; out[3] = Math.sin((u * Math.PI) / 2);
  return out;
}

/** Wheel on pavement (track, pit lane, paved runoff). Physics without WheelState.paved: fall back to onTrack. */
export function onPavement(w: WheelState): boolean {
  return typeof w.paved === 'boolean' ? w.paved : w.onTrack;
}

/** Squeal drive of one wheel: 0 below SQUEAL_START × peak, smooth rise to 1 at SQUEAL_FULL × peak. */
export function wheelSqueal(w: WheelState, speed: number, p: AudioCarParams): number {
  // tyres do not squeal on dirt or grass: they slide quietly (the gravel layer covers it)
  if (!onPavement(w) || w.load < SQUEAL_MIN_LOAD || Math.abs(speed) < SQUEAL_MIN_SPEED) return 0;
  const use = typeof w.slipUse === 'number' && isFinite(w.slipUse)
    ? w.slipUse
    : Math.hypot(w.slipAngle / p.peakSlipAngle, w.slipRatio / p.peakSlipRatio);
  return smooth((use - SQUEAL_START) / (SQUEAL_FULL - SQUEAL_START));
}

export interface SquealMix { scrub: number; skid: number; slide: number }

/**
 * Whole-car squeal: `scrub` (lateral scrub and wheelspin), `skid` (braking lock-up: slip ratio past the peak on
 * the negative side, which includes ABS pulsing) and `slide`, the sliding speed (m/s) of the hardest-working wheel,
 * for the pitch. Writes into `out`.
 */
export function squealMix(st: VehicleState, p: AudioCarParams, out: SquealMix): SquealMix {
  let scrubMax = 0, scrubSum = 0, skidMax = 0, skidSum = 0, slide = 0, best = 0;
  const v = Math.abs(st.speed);
  for (let i = 0; i < 4; i++) {
    const w = st.wheels[i];
    const x = wheelSqueal(w, st.speed, p);
    if (x <= 0) continue;
    const k = w.slipRatio / p.peakSlipRatio, a = w.slipAngle / p.peakSlipAngle;
    // share of the slip that is longitudinal braking (lock-up) vs lateral scrub / wheelspin
    const lock = w.slipRatio < 0 ? (k * k) / (k * k + a * a + 1e-9) : 0;
    const sk = x * lock, sc = x * (1 - lock);
    scrubSum += sc; skidSum += sk;
    if (sc > scrubMax) scrubMax = sc;
    if (sk > skidMax) skidMax = sk;
    if (x > best) { best = x; slide = v * Math.hypot(w.slipRatio, Math.tan(Math.min(Math.abs(w.slipAngle), 1.2))); }
  }
  out.scrub = Math.min(1, scrubMax + 0.25 * (scrubSum - scrubMax));
  out.skid = Math.min(1, skidMax + 0.25 * (skidSum - skidMax));
  out.slide = slide;
  return out;
}

/** Wheels carrying less than this (N) do not make dirt noise (airborne / unloaded). */
export const DIRT_MIN_LOAD = 200;
/** Dirt noise reaches full level at this speed, m/s. */
export const DIRT_FULL_SPEED = 25;

export interface DirtMix {
  /** Rolling-on-dirt bed, 0..1: share of loaded wheels off pavement × speed (full at DIRT_FULL_SPEED). */
  level: number;
  /** Spraying gravel, 0..1: the most-slipping off-pavement wheel (slipUse past ~0.8 of the peak), × speed. */
  spray: number;
}

/** Gravel / grass noise drive from the wheels off pavement. Writes into `out` (no allocation). */
export function dirtMix(st: VehicleState, p: AudioCarParams, out: DirtMix): DirtMix {
  const v = Math.abs(st.speed);
  let n = 0, slip = 0;
  for (let i = 0; i < 4; i++) {
    const w = st.wheels[i];
    if (onPavement(w) || w.load < DIRT_MIN_LOAD) continue;
    n++;
    const use = typeof w.slipUse === 'number' && isFinite(w.slipUse)
      ? w.slipUse
      : Math.hypot(w.slipAngle / p.peakSlipAngle, w.slipRatio / p.peakSlipRatio);
    const x = smooth((use - 0.8) / 0.8);
    if (x > slip) slip = x;
  }
  out.level = (n / 4) * smooth(v / DIRT_FULL_SPEED);
  out.spray = n ? slip * smooth(v / 6) : 0;
  return out;
}

/**
 * Make each decoded loop seamless. The sprites store every loop as [tail pad | loop | head pad] (cyclic copies),
 * so after a lossy codec the samples just before loopStart are a second decoding of the loop's own tail that runs
 * continuously into loopStart. Blending the last `n` samples of the loop into that copy removes the step that
 * codec noise leaves at the seam (both versions are the same audio, so the blend is inaudible).
 */
export function healLoopSeams(data: Float32Array, sampleRate: number, refs: LoopRef[], n = 256): void {
  for (const r of refs) {
    const a = Math.round(r.offset * sampleRate), len = Math.round(r.duration * sampleRate);
    const e = a + len, m = Math.min(n, a, len >> 2);
    for (let i = 0; i < m; i++) {
      const w = (i + 1) / m; // 0 → 1 toward the loop end
      const k = e - m + i;
      data[k] += (data[a - m + i] - data[k]) * w;
    }
  }
}

interface Fetched {
  index: EngineIndex | null; on: ArrayBuffer | null; off: ArrayBuffer | null; squeal: ArrayBuffer | null; squealMeta: LoopRef | null;
  /** The buffers above are already the AAC fallback (the browser reported no Ogg Opus support). */
  isFallback: boolean;
}

interface Slot {
  gain: GainNode;
  src: AudioBufferSourceNode | null;
  bin: number; load: number; // load 0 = off, 1 = on
  neededAt: number;
  rateRpm: number;
}

const N_SLOTS = 8;
const SLOT_LINGER = 0.3; // s a slot stays assigned after its bin stopped being needed
const LOAD_UP = 0.035, LOAD_DOWN = 0.07; // lag of the on/off layer cross-fade, s (lift-off reads as a note change)
const LIMITER_HZ = 16;

/** Level of the AI field bus (CarAudio.fieldBus) against the player's engine. */
export const FIELD_BUS_GAIN = 0.55;

export class CarAudio {
  private ctx: BaseAudioContext | null = null;
  private master!: GainNode;
  private engineIn!: GainNode;
  private engineGate!: GainNode;
  private limiterDepth!: GainNode;
  private engineLevel!: GainNode;
  private engineLP!: BiquadFilterNode;
  private slots: Slot[] = [];
  private sprites: [AudioBuffer | null, AudioBuffer | null] = [null, null]; // off, on
  private index: EngineIndex | null = null;
  private binRpm = new Float64Array(0);
  private bw = new Float64Array(4);
  private fallback: { osc: OscillatorNode; gain: GainNode } | null = null;
  private squealBuf: AudioBuffer | null = null;
  private squealRef: LoopRef | null = null;
  private scrubSrc: AudioBufferSourceNode | null = null;
  private skidSrc: AudioBufferSourceNode | null = null;
  private scrubGain!: GainNode;
  private skidGain!: GainNode;
  private skidNoiseGain!: GainNode;
  private rumbleGain!: GainNode;
  private rumbleLP!: BiquadFilterNode;
  private gravelGain!: GainNode;
  private dirtLowGain!: GainNode;
  private sprayGain!: GainNode;
  private sprayGrit!: GainNode;
  private dirt: DirtMix = { level: 0, spray: 0 };
  private windGain!: GainNode;
  private windFilter!: BiquadFilterNode;
  private noiseBuf: AudioBuffer | null = null;
  private fetched: Promise<Fetched> | null = null;
  private buf: (f: string) => Promise<ArrayBuffer | null> = async () => null;
  /** 'ogg' or 'm4a' once the engine sprites are decoded (which file set is playing). */
  codec: 'ogg' | 'm4a' | null = null;
  private params: AudioCarParams = { idleRpm: 850, revLimitRpm: 6900, peakSlipAngle: PEAK_SLIP_ANGLE, peakSlipRatio: PEAK_SLIP_RATIO };
  private load = 0;
  private lastT = 0;
  private mix: SquealMix = { scrub: 0, skid: 0, slide: 0 };
  muted = false;
  /** Set when the recorded engine is playing (false: still loading, or fell back to the oscillator). */
  samplesReady = false;

  constructor(private base = 'audio/') {}

  /** Car parameters (rev limit, idle, tyre peaks), e.g. audioParamsFromCarJson(assets.carSpecJson). */
  configure(p: Partial<AudioCarParams>): void { this.params = { ...this.params, ...p }; }

  /** Start fetching the sample files (no AudioContext needed). Called at boot; start() calls it if not. */
  preload(): void {
    if (this.fetched) return;
    const get = (f: string) => fetch(this.base + f).then((r) => {
      const ct = r.headers.get('content-type') ?? '';
      if (!r.ok || ct.includes('text/html')) throw new Error(`${f}: ${r.status}`);
      return r;
    });
    const buf = (f: string) => get(f).then((r) => r.arrayBuffer()).catch(() => null);
    this.buf = buf;
    this.fetched = (async () => {
      const index = await get('engine.json').then((r) => r.json() as Promise<EngineIndex>).catch(() => null);
      const fb = index?.fallback;
      const useFb = !!fb && !canPlayOggOpus();
      const sp = useFb ? fb! : index?.sprites ?? { on: 'engine_on.ogg', off: 'engine_off.ogg' };
      const [on, off, squeal, squealMeta] = await Promise.all([
        index ? buf(sp.on) : null, index ? buf(sp.off) : null, buf(useFb ? fb!.squeal : 'squeal.ogg'),
        get('squeal.json').then((r) => r.json() as Promise<LoopRef>).catch(() => null),
      ]);
      return { index, on, off, squeal, squealMeta, isFallback: useFb };
    })();
  }

  /**
   * Create the audio graph. Without an argument: a real-time AudioContext (call from a user gesture).
   * Tests / offline renders pass an OfflineAudioContext and await the returned promise before rendering.
   */
  start(ctxIn?: BaseAudioContext): Promise<void> {
    if (this.ctx) { this.unlock(); return Promise.resolve(); }
    let ctx: BaseAudioContext;
    if (ctxIn) ctx = ctxIn;
    else {
      // iOS: play through the ring / silent switch like a game, not as "ambient" sound (Safari 16.4+)
      try { const s = (navigator as unknown as { audioSession?: { type: string } }).audioSession; if (s) s.type = 'playback'; } catch { /* older */ }
      try { ctx = new AudioContext({ sampleRate: 48000, latencyHint: 'interactive' }); } catch { ctx = new AudioContext(); }
      // must run inside the user gesture (iOS creates the context suspended)
      void (ctx as AudioContext).resume();
    }
    this.ctx = ctx;
    this.buildGraph(ctx);
    this.preload();
    return this.fetched!.then((f) => this.attachSamples(ctx, f)).catch((e) => { console.warn('engine audio:', e); this.useFallback(ctx); });
  }

  private buildGraph(ctx: BaseAudioContext): void {
    this.master = ctx.createGain();
    this.master.gain.value = this.muted ? 0 : 0.9;
    // one master compressor working as a soft limiter, so nothing clips
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -12; comp.knee.value = 6; comp.ratio.value = 12; comp.attack.value = 0.003; comp.release.value = 0.15;
    this.master.connect(comp).connect(ctx.destination);

    const noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    let seed = 12345;
    for (let i = 0; i < d.length; i++) { seed = (seed * 1664525 + 1013904223) >>> 0; d[i] = seed / 2147483648 - 1; }
    this.noiseBuf = noiseBuf;
    const noise = () => { const s = ctx.createBufferSource(); s.buffer = noiseBuf; s.loop = true; s.start(0, Math.random() * 1.9); return s; };

    // engine: voices -> engineIn -> gate (rev limiter) -> level -> low-pass (opens with throttle) -> master
    this.engineIn = ctx.createGain();
    this.engineGate = ctx.createGain();
    this.engineGate.gain.value = 1;
    this.limiterDepth = ctx.createGain();
    this.limiterDepth.gain.value = 0;
    const lfo = ctx.createOscillator();
    lfo.type = 'square'; lfo.frequency.value = LIMITER_HZ;
    lfo.connect(this.limiterDepth).connect(this.engineGate.gain); // gate = 1 - d/2 ± d/2 (set in update)
    lfo.start();
    this.engineLevel = ctx.createGain();
    this.engineLevel.gain.value = 0;
    this.engineLP = ctx.createBiquadFilter();
    this.engineLP.type = 'lowpass'; this.engineLP.Q.value = 0.6; this.engineLP.frequency.value = 2000;
    this.engineIn.connect(this.engineGate).connect(this.engineLevel).connect(this.engineLP).connect(this.master);
    for (let i = 0; i < N_SLOTS; i++) {
      const g = ctx.createGain(); g.gain.value = 0; g.connect(this.engineIn);
      this.slots.push({ gain: g, src: null, bin: -1, load: -1, neededAt: -1, rateRpm: 1 });
    }

    // tyres: scrub (the recorded squeal), skid (same recording pitched down and darkened, plus a low noise howl)
    this.scrubGain = ctx.createGain(); this.scrubGain.gain.value = 0;
    this.scrubGain.connect(this.master);
    const skidLP = ctx.createBiquadFilter(); skidLP.type = 'lowpass'; skidLP.frequency.value = 1400; skidLP.Q.value = 0.7;
    this.skidGain = ctx.createGain(); this.skidGain.gain.value = 0;
    this.skidGain.connect(skidLP).connect(this.master);
    const howl = ctx.createBiquadFilter(); howl.type = 'bandpass'; howl.frequency.value = 650; howl.Q.value = 3;
    this.skidNoiseGain = ctx.createGain(); this.skidNoiseGain.gain.value = 0;
    noise().connect(howl).connect(this.skidNoiseGain).connect(this.master);

    // road / tyre rumble: low band of noise, rising with speed; rougher band off the paved surface
    this.rumbleLP = ctx.createBiquadFilter(); this.rumbleLP.type = 'lowpass'; this.rumbleLP.frequency.value = 160; this.rumbleLP.Q.value = 0.5;
    const rumbleHP = ctx.createBiquadFilter(); rumbleHP.type = 'highpass'; rumbleHP.frequency.value = 35;
    this.rumbleGain = ctx.createGain(); this.rumbleGain.gain.value = 0;
    noise().connect(rumbleHP).connect(this.rumbleLP).connect(this.rumbleGain).connect(this.master);
    // off pavement (per-wheel WheelState.paved): a low dirt bed (ground roughness through the tyres + a gravel band)
    // and, when the tyres slide, a brighter gritty spray (stones and dirt flung into the arches). Subtle: well under
    // the engine and the road rumble's peak.
    const gravel = ctx.createBiquadFilter(); gravel.type = 'bandpass'; gravel.frequency.value = 420; gravel.Q.value = 0.8;
    this.gravelGain = ctx.createGain(); this.gravelGain.gain.value = 0;
    noise().connect(gravel).connect(this.gravelGain).connect(this.master);
    const dirtLP = ctx.createBiquadFilter(); dirtLP.type = 'lowpass'; dirtLP.frequency.value = 140; dirtLP.Q.value = 0.9;
    this.dirtLowGain = ctx.createGain(); this.dirtLowGain.gain.value = 0;
    noise().connect(dirtLP).connect(this.dirtLowGain).connect(this.master);
    const spray = ctx.createBiquadFilter(); spray.type = 'bandpass'; spray.frequency.value = 2600; spray.Q.value = 0.6;
    this.sprayGain = ctx.createGain(); this.sprayGain.gain.value = 0;
    noise().connect(spray).connect(this.sprayGain).connect(this.master);
    // grit: the spray's level flutters with a slow random envelope (individual stones rather than a hiss)
    const gritLP = ctx.createBiquadFilter(); gritLP.type = 'lowpass'; gritLP.frequency.value = 22;
    this.sprayGrit = ctx.createGain(); this.sprayGrit.gain.value = 0;
    noise().connect(gritLP).connect(this.sprayGrit).connect(this.sprayGain.gain);

    // wind
    this.windFilter = ctx.createBiquadFilter(); this.windFilter.type = 'lowpass'; this.windFilter.frequency.value = 400;
    this.windGain = ctx.createGain(); this.windGain.gain.value = 0;
    noise().connect(this.windFilter).connect(this.windGain).connect(this.master);
  }

  private async attachSamples(ctx: BaseAudioContext, f: Fetched): Promise<void> {
    if (!f.index || !f.on || !f.off) throw new Error('engine samples missing');
    const fb = f.index.fallback;
    const dec = (b: ArrayBuffer) => ctx.decodeAudioData(b);
    const [on, off] = await Promise.all([
      decodeSprite(dec, f.on, f.isFallback, () => this.buf(fb!.on), fb, 'on'),
      decodeSprite(dec, f.off, f.isFallback, () => this.buf(fb!.off), fb, 'off'),
    ]);
    const index = shiftIndex(f.index, on.shift, off.shift);
    healLoopSeams(on.buffer.getChannelData(0), on.buffer.sampleRate, index.bins.map((b) => b.on));
    healLoopSeams(off.buffer.getChannelData(0), off.buffer.sampleRate, index.bins.map((b) => b.off));
    this.sprites = [off.buffer, on.buffer];
    this.index = index;
    this.codec = on.fallback || off.fallback ? 'm4a' : 'ogg';
    this.binRpm = Float64Array.from(index.bins.map((b) => b.rpm));
    this.samplesReady = true;
    if (f.squeal || fb) {
      try {
        const sq = await decodeSprite(dec, f.squeal, f.isFallback, () => this.buf(fb!.squeal), fb, 'squeal');
        this.squealBuf = sq.buffer;
        const meta = f.squealMeta ?? { offset: 0.15, duration: Math.max(0.1, sq.buffer.duration - 0.4) };
        this.squealRef = { ...meta, offset: meta.offset + sq.shift };
        healLoopSeams(this.squealBuf.getChannelData(0), this.squealBuf.sampleRate, [this.squealRef]);
        const mk = (dest: GainNode) => {
          const s = ctx.createBufferSource();
          s.buffer = this.squealBuf; s.loop = true;
          s.loopStart = this.squealRef!.offset; s.loopEnd = this.squealRef!.offset + this.squealRef!.duration;
          s.connect(dest); s.start(0, this.squealRef!.offset + Math.random() * this.squealRef!.duration);
          return s;
        };
        this.scrubSrc = mk(this.scrubGain);
        this.skidSrc = mk(this.skidGain);
        this.skidSrc.playbackRate.value = 0.62;
      } catch (e) { console.warn('squeal audio:', e); }
    }
  }

  /** No samples: a plain oscillator so the car is not silent. */
  private useFallback(ctx: BaseAudioContext): void {
    const osc = ctx.createOscillator(); osc.type = 'sawtooth'; osc.frequency.value = 40;
    const gain = ctx.createGain(); gain.gain.value = 0.25;
    osc.connect(gain).connect(this.engineIn); osc.start();
    this.fallback = { osc, gain };
  }

  private fieldGain: GainNode | null = null;
  /**
   * The AI field's destination: a gain into the master bus (so Mute and the master limiter apply to it), created
   * on first use. null until start(). Its level balances the field against the player's engine.
   */
  fieldBus(): GainNode | null {
    const ctx = this.ctx;
    if (!ctx) return null;
    if (!this.fieldGain) {
      this.fieldGain = ctx.createGain();
      this.fieldGain.gain.value = FIELD_BUS_GAIN;
      this.fieldGain.connect(this.master);
    }
    return this.fieldGain;
  }

  setMuted(m: boolean): void {
    this.muted = m;
    if (this.ctx) this.master.gain.setTargetAtTime(m ? 0 : 0.9, this.ctx.currentTime, 0.05);
  }

  suspend(): void { if (this.ctx instanceof AudioContext) void this.ctx.suspend(); }
  /** Resume a context the browser suspended or interrupted (iOS after a call / backgrounding); call from a gesture. */
  unlock(): void {
    const c = this.ctx;
    if (c instanceof AudioContext && c.state !== 'running') void c.resume();
  }
  resume(): void { if (this.ctx instanceof AudioContext) void this.ctx.resume(); }

  /** A thump for a barrier / tree impact; loudness from the closing speed (m/s). */
  impact(speedNormal: number): void {
    const ctx = this.ctx;
    if (!ctx || !this.noiseBuf || speedNormal < 1) return;
    const t = ctx.currentTime;
    const src = ctx.createBufferSource(); src.buffer = this.noiseBuf;
    const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 180 + Math.min(speedNormal, 30) * 60;
    const g = ctx.createGain();
    const peak = Math.min(1, speedNormal / 15) * 0.9;
    g.gain.setValueAtTime(peak, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.25 + Math.min(speedNormal, 30) * 0.02);
    src.connect(lp).connect(g).connect(this.master);
    src.start(t, Math.random() * 1.5);
    src.stop(t + 1);
  }

  /** Point slot s at (bin, load), starting a new looping source at a random point of that loop. */
  private assign(s: Slot, bin: number, load: number, t: number): void {
    const ctx = this.ctx!, buf = this.sprites[load]!, ref = load ? this.index!.bins[bin].on : this.index!.bins[bin].off;
    if (s.src) { try { s.src.stop(); } catch { /* already stopped */ } s.src.disconnect(); }
    const src = ctx.createBufferSource();
    src.buffer = buf; src.loop = true;
    src.loopStart = ref.offset; src.loopEnd = ref.offset + ref.duration;
    src.connect(s.gain);
    src.start(t, ref.offset + Math.random() * ref.duration);
    s.src = src; s.bin = bin; s.load = load; s.rateRpm = ref.rpm ?? this.index!.bins[bin].rpm;
    s.gain.gain.cancelScheduledValues(t);
    s.gain.gain.setValueAtTime(0, t);
  }

  /** Ensure (bin, load) has a slot, set its target gain and rate. */
  private want(bin: number, load: number, w: number, rpm: number, t: number): void {
    let s: Slot | null = null;
    for (let i = 0; i < N_SLOTS; i++) { const c = this.slots[i]; if (c.bin === bin && c.load === load) { s = c; break; } }
    if (!s) {
      if (w < 1e-3) return; // not worth starting a voice that would be silent
      let oldest = Infinity;
      for (let i = 0; i < N_SLOTS; i++) {
        const c = this.slots[i];
        if (c.bin < 0) { s = c; break; }
        if (c.neededAt < oldest) { oldest = c.neededAt; s = c; }
      }
      this.assign(s!, bin, load, t);
    }
    s!.neededAt = t;
    s!.gain.gain.setTargetAtTime(w, t, 0.012);
    s!.src!.playbackRate.setTargetAtTime(Math.max(0.25, rpm / s!.rateRpm), t, 0.008);
  }

  /**
   * Per rendered frame. `throttleIn` = the driver's pedal (0..1), used for the rev limiter;
   * the engine load follows st.throttleOut (gear-change torque cut, limiter, launch shaping).
   */
  update(st: VehicleState, throttleIn: number = st.throttleOut): void {
    const ctx = this.ctx;
    if (!ctx) return;
    const t = ctx.currentTime;
    const dt = Math.min(0.1, Math.max(0, t - this.lastT));
    this.lastT = t;
    const rpm = Math.max(1, st.rpm);
    const speed = Math.abs(st.speed);

    if (st.launched) {
      // in space: the engine winds down and fades, no tyres, thin wind
      this.engineLevel.gain.setTargetAtTime(0, t, 1.2);
      for (let i = 0; i < N_SLOTS; i++) {
        const s = this.slots[i];
        if (s.src) s.src.playbackRate.setTargetAtTime(Math.max(0.25, rpm / s.rateRpm), t, 0.2);
      }
      this.fallback?.osc.frequency.setTargetAtTime(rpm / 20, t, 0.2);
      this.limiterDepth.gain.setTargetAtTime(0, t, 0.02);
      this.engineGate.gain.setTargetAtTime(1, t, 0.02);
      this.scrubGain.gain.setTargetAtTime(0, t, 0.1);
      this.skidGain.gain.setTargetAtTime(0, t, 0.1);
      this.skidNoiseGain.gain.setTargetAtTime(0, t, 0.1);
      this.rumbleGain.gain.setTargetAtTime(0, t, 0.3);
      this.gravelGain.gain.setTargetAtTime(0, t, 0.3);
      this.dirtLowGain.gain.setTargetAtTime(0, t, 0.3);
      this.sprayGain.gain.setTargetAtTime(0, t, 0.2);
      this.sprayGrit.gain.setTargetAtTime(0, t, 0.2);
      this.windGain.gain.setTargetAtTime(0.04, t, 0.5);
      return;
    }

    // ---- engine
    const thr = clamp01(st.throttleOut);
    const tau = thr > this.load ? LOAD_UP : LOAD_DOWN;
    this.load += (thr - this.load) * (1 - Math.exp(-dt / tau));
    const L = this.load;
    const wOn = Math.sin((L * Math.PI) / 2), wOff = Math.cos((L * Math.PI) / 2);
    if (this.samplesReady && this.index) {
      const bw = binWeights(this.binRpm, Math.max(rpm, this.params.idleRpm * 0.6), this.bw);
      const lo = bw[0], wl = bw[1], hi = bw[2], wh = bw[3];
      this.want(lo, 1, wl * wOn, rpm, t);
      this.want(lo, 0, wl * wOff, rpm, t);
      this.want(hi, 1, wh * wOn, rpm, t);
      this.want(hi, 0, wh * wOff, rpm, t);
      for (let i = 0; i < N_SLOTS; i++) {
        const s = this.slots[i];
        if (s.bin < 0 || s.neededAt === t) continue;
        s.gain.gain.setTargetAtTime(0, t, 0.012);
        if (s.src) s.src.playbackRate.setTargetAtTime(Math.max(0.25, rpm / s.rateRpm), t, 0.008);
        if (t - s.neededAt > SLOT_LINGER && s.src) {
          try { s.src.stop(t + 0.05); } catch { /* ignore */ }
          s.src = null; s.bin = -1; s.load = -1;
        }
      }
    } else if (this.fallback) {
      this.fallback.osc.frequency.setTargetAtTime(rpm / 20, t, 0.01);
    }
    // level: throttle and a small rpm term; low-pass opens with throttle (muffled on the overrun)
    const level = 0.95 * (0.5 + 0.5 * Math.pow(L, 0.8)) * (0.8 + 0.2 * Math.min(1.2, rpm / 6000));
    this.engineLevel.gain.setTargetAtTime(level, t, 0.02);
    this.engineLP.frequency.setTargetAtTime(1300 + 9500 * L * L + rpm * 0.25, t, 0.03);
    // rev limiter: while rpm sits at the limit with the pedal down, gate the engine at LIMITER_HZ
    const atLimit = rpm >= this.params.revLimitRpm - 60 && throttleIn > 0.5;
    const depth = atLimit ? 0.85 : 0;
    this.limiterDepth.gain.setTargetAtTime(depth / 2, t, 0.008);
    this.engineGate.gain.setTargetAtTime(1 - depth / 2, t, 0.008);

    // ---- tyres (within ~50 ms: frame-rate updates, 15 ms attack)
    const m = squealMix(st, this.params, this.mix);
    const pitch = 0.94 + 0.16 * clamp01(m.slide / 10);
    const atk = (cur: number, target: number) => (target > cur ? 0.015 : 0.05);
    const scrubT = 0.55 * m.scrub * m.scrub;
    const skidT = 0.6 * m.skid * m.skid;
    this.scrubGain.gain.setTargetAtTime(scrubT, t, atk(this.scrubGain.gain.value, scrubT));
    this.skidGain.gain.setTargetAtTime(skidT, t, atk(this.skidGain.gain.value, skidT));
    this.skidNoiseGain.gain.setTargetAtTime(0.35 * m.skid * m.skid, t, 0.03);
    if (this.scrubSrc) this.scrubSrc.playbackRate.setTargetAtTime(pitch, t, 0.03);
    if (this.skidSrc) this.skidSrc.playbackRate.setTargetAtTime(0.6 + 0.08 * clamp01(m.slide / 10), t, 0.03);

    // ---- road rumble and wind
    const v = Math.min(speed / 45, 1.3);
    this.rumbleGain.gain.setTargetAtTime(0.32 * Math.pow(v, 1.2), t, 0.08);
    this.rumbleLP.frequency.setTargetAtTime(110 + speed * 3, t, 0.1);
    // ---- gravel / grass (wheels off pavement)
    const dm = dirtMix(st, this.params, this.dirt);
    this.gravelGain.gain.setTargetAtTime(0.1 * dm.level, t, 0.05);
    this.dirtLowGain.gain.setTargetAtTime(0.22 * dm.level, t, 0.05);
    const sprayT = 0.07 * dm.spray * (0.4 + 0.6 * dm.level);
    this.sprayGain.gain.setTargetAtTime(sprayT, t, 0.04);
    this.sprayGrit.gain.setTargetAtTime(2.5 * sprayT, t, 0.04);
    const vw = Math.min(speed / 60, 1.2);
    this.windGain.gain.setTargetAtTime(vw * vw * 0.16, t, 0.1);
    this.windFilter.frequency.setTargetAtTime(250 + speed * 14, t, 0.1);
  }

  /** The AudioContext (null until start()); the AI field (audio-field.ts) shares it. Also for debugging / offline renders. */
  get context(): BaseAudioContext | null { return this.ctx; }
}
