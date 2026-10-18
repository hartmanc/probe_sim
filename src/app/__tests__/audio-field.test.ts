import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import {
  EngineVoice, FieldAudio, dopplerFactor, distanceGain, familyFor, loadFamily, mufflerCutoff, selectNearest,
  type FamilyIndex, type FieldCar, type Vec3,
} from '../audio-field';
import { FAMILY_RETRY_S } from '../audio-field';
import { carSound, fieldAudioHook, fillAudioCar, parseSoundIndex } from '../modes/race';
import type { FieldAudioCar } from '../modes/mode';

// ---------------------------------------------------------------------------------------------------------------
// A small offline Web Audio fake (Node has none): only what audio-field.ts uses. Rendered in 128-sample blocks;
// gain is evaluated per sample, everything else per block.
/* eslint-disable @typescript-eslint/no-explicit-any */
const SR = 48000, BLOCK = 128;

type Ev = { type: 'set' | 'target'; time: number; v: number; tau: number };
class FParam {
  private ev: Ev[] = [];
  private mode: Ev = { type: 'set', time: 0, v: 0, tau: 0 };
  private t0 = 0; private v0 = 0; cur: number;
  constructor(private ctx: FakeCtx, v: number) { this.cur = v; this.mode.v = v; }
  get value() { return this.cur; }
  set value(v: number) { this.setValueAtTime(v, this.ctx.currentTime); }
  private add(e: Ev) { let i = this.ev.length; while (i > 0 && this.ev[i - 1].time > e.time) i--; this.ev.splice(i, 0, e); return this; }
  setValueAtTime(v: number, time: number) { return this.add({ type: 'set', time, v, tau: 0 }); }
  setTargetAtTime(v: number, time: number, tau: number) { return this.add({ type: 'target', time, v, tau }); }
  cancelScheduledValues(time: number) { this.ev = this.ev.filter((e) => e.time < time); return this; }
  private at(t: number) {
    const m = this.mode;
    return m.type === 'set' ? m.v : m.v + (this.v0 - m.v) * Math.exp(-(t - this.t0) / m.tau);
  }
  sample(t: number): number {
    while (this.ev.length && this.ev[0].time <= t) {
      const e = this.ev.shift()!;
      this.v0 = this.at(e.time); this.t0 = e.time; this.mode = e;
    }
    return (this.cur = this.at(t));
  }
  block(t: number, out: Float32Array) { for (let i = 0; i < out.length; i++) out[i] = this.sample(t + i / SR); return out; }
}

class FNode {
  inputs: FNode[] = [];
  outs: FNode[] = [];
  private cacheBlock = -1; private cache: Float32Array[] = [];
  onended: (() => void) | null = null;
  constructor(public ctx: FakeCtx) {}
  connect<T>(d: T): T { (d as any).inputs.push(this); this.outs.push(d as any); return d; }
  disconnect() { for (const d of this.outs) d.inputs = d.inputs.filter((x) => x !== this); this.outs = []; }
  pull(b: number, t: number): Float32Array[] {
    if (this.cacheBlock !== b) { this.cache = this.process(b, t); this.cacheBlock = b; }
    return this.cache;
  }
  mix(b: number, t: number): Float32Array[] {
    const ins = this.inputs.map((n) => n.pull(b, t));
    const ch = Math.max(1, ...ins.map((x) => x.length));
    const out = Array.from({ length: ch }, () => new Float32Array(BLOCK));
    for (const x of ins) for (let c = 0; c < ch; c++) { const s = x[Math.min(c, x.length - 1)]; for (let i = 0; i < BLOCK; i++) out[c][i] += s[i]; }
    return out;
  }
  process(b: number, t: number): Float32Array[] { return this.mix(b, t); }
}
class FGain extends FNode {
  gain = new FParam(this.ctx, 1); private g = new Float32Array(BLOCK);
  process(b: number, t: number) { const x = this.mix(b, t); this.gain.block(t, this.g); for (const c of x) for (let i = 0; i < BLOCK; i++) c[i] *= this.g[i]; return x; }
}
class FSource extends FNode {
  buffer: FBuffer | null = null; loop = false; loopStart = 0; loopEnd = 0;
  playbackRate = new FParam(this.ctx, 1);
  private when = Infinity; private stopAt = Infinity; private pos = 0; private ended = false;
  start(when = 0, offset = 0) { this.when = when; this.pos = offset * SR; }
  stop(when = 0) { this.stopAt = when; }
  process(_b: number, t: number) {
    const out = new Float32Array(BLOCK), d = this.buffer!.data;
    const rate = this.playbackRate.sample(t);
    const ls = this.loopStart * SR, le = this.loopEnd * SR;
    for (let i = 0; i < BLOCK; i++) {
      const ti = t + i / SR;
      if (ti < this.when || this.ended) continue;
      if (ti >= this.stopAt) { this.ended = true; this.onended?.(); continue; }
      const k = Math.floor(this.pos), f = this.pos - k;
      out[i] = (d[k] ?? 0) * (1 - f) + (d[k + 1] ?? 0) * f;
      this.pos += rate;
      if (this.loop && this.pos >= le) this.pos -= le - ls;
    }
    return [out];
  }
}
class FBiquad extends FNode {
  type = 'lowpass'; frequency = new FParam(this.ctx, 350); Q = new FParam(this.ctx, 1);
  private z: number[][] = [];
  process(b: number, t: number) {
    const x = this.mix(b, t);
    const w = (2 * Math.PI * Math.min(this.frequency.sample(t), 0.49 * SR)) / SR, q = Math.pow(10, this.Q.sample(t) / 20);
    const al = Math.sin(w) / (2 * q), cw = Math.cos(w), a0 = 1 + al;
    const b0 = (1 - cw) / 2 / a0, b1 = (1 - cw) / a0, a1 = (-2 * cw) / a0, a2 = (1 - al) / a0;
    x.forEach((c, ci) => {
      const s = (this.z[ci] ??= [0, 0, 0, 0]);
      for (let i = 0; i < BLOCK; i++) {
        const y = b0 * c[i] + b1 * s[0] + b0 * s[1] - a1 * s[2] - a2 * s[3];
        s[1] = s[0]; s[0] = c[i]; s[3] = s[2]; s[2] = y; c[i] = y;
      }
    });
    return x;
  }
}
const sub = (a: number[], b: number[]) => a.map((v, i) => v - b[i]);
const dot = (a: number[], b: number[]) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: number[], b: number[]) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: number[]) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return a.map((v) => v / l); };
class FPanner extends FNode {
  panningModel = 'HRTF'; distanceModel = 'inverse'; rolloffFactor = 1; refDistance = 1; maxDistance = 1e4;
  positionX = new FParam(this.ctx, 0); positionY = new FParam(this.ctx, 0); positionZ = new FParam(this.ctx, 0);
  /** Spec equal-power azimuth for a mono input (distance attenuation ignored: the code sets rolloffFactor 0). */
  process(b: number, t: number) {
    const x = this.mix(b, t), m = x[0];
    const L = this.ctx.listener;
    const lp = [L.positionX.sample(t), L.positionY.sample(t), L.positionZ.sample(t)];
    const fw = norm([L.forwardX.sample(t), L.forwardY.sample(t), L.forwardZ.sample(t)]);
    const upIn = [L.upX.sample(t), L.upY.sample(t), L.upZ.sample(t)];
    const sp = [this.positionX.sample(t), this.positionY.sample(t), this.positionZ.sample(t)];
    let az = 0;
    const sl = sub(sp, lp);
    if (Math.hypot(sl[0], sl[1], sl[2]) > 1e-9) {
      const s = norm(sl), right = norm(cross(fw, upIn)), up = cross(right, fw);
      const proj = norm(sub(s, up.map((v) => v * dot(s, up))));
      az = (180 * Math.acos(Math.max(-1, Math.min(1, dot(proj, right))))) / Math.PI;
      if (dot(proj, fw) < 0) az = 360 - az;
      az = az <= 270 ? 90 - az : 450 - az;
    }
    if (az < -90) az = -180 - az; else if (az > 90) az = 180 - az;
    const u = (az + 90) / 180, gl = Math.cos((u * Math.PI) / 2), gr = Math.sin((u * Math.PI) / 2);
    const l = new Float32Array(BLOCK), r = new Float32Array(BLOCK);
    for (let i = 0; i < BLOCK; i++) { l[i] = m[i] * gl; r[i] = m[i] * gr; }
    return [l, r];
  }
}
class FBuffer {
  constructor(public data: Float32Array, public sampleRate = SR) {}
  get length() { return this.data.length; }
  get duration() { return this.data.length / this.sampleRate; }
  numberOfChannels = 1;
  getChannelData() { return this.data; }
}
class FakeCtx {
  sampleRate = SR; currentTime = 0; private blk = 0;
  destination = new FNode(this);
  listener: Record<string, FParam>;
  out: [number[], number[]] = [[], []];
  constructor(private decode: (ab: ArrayBuffer) => Float32Array) {
    const p = (v: number) => new FParam(this, v);
    this.listener = { positionX: p(0), positionY: p(0), positionZ: p(0), forwardX: p(0), forwardY: p(0), forwardZ: p(-1), upX: p(0), upY: p(1), upZ: p(0) };
  }
  createGain() { return new FGain(this); }
  createBufferSource() { return new FSource(this); }
  createBiquadFilter() { return new FBiquad(this); }
  createPanner() { return new FPanner(this); }
  decodeAudioData(ab: ArrayBuffer) { return Promise.resolve(new FBuffer(this.decode(ab))); }
  /** Render `sec` seconds (whole blocks), appending to out. */
  advance(sec: number) {
    const n = Math.max(1, Math.round((sec * SR) / BLOCK));
    for (let k = 0; k < n; k++) {
      const y = this.destination.pull(this.blk, this.currentTime);
      for (let c = 0; c < 2; c++) for (const v of y[Math.min(c, y.length - 1)]) this.out[c].push(v);
      this.blk++; this.currentTime = (this.blk * BLOCK) / SR;
    }
  }
}
const asCtx = (c: FakeCtx) => c as unknown as BaseAudioContext;
const resp = (body: unknown) => ({ ok: true, json: async () => body, arrayBuffer: async () => (body as ArrayBuffer) });

// ---------------------------------------------------------------------------------------------------------------
// A synthetic family: every loop is 0.1 s of a sine at rpm / 5 Hz (a whole number of periods, so it loops
// seamlessly, and every bin played at the same rpm gives the same tone).
const synth = (() => {
  const pad = 0.05, dur = 0.1, bins = [] as any[];
  let pos = 0.1;
  for (let rpm = 1000; rpm <= 7000; rpm += 500) {
    const on = { offset: pos + pad, duration: dur, rpm }; pos += dur + 2 * pad;
    const off = { offset: pos + pad, duration: dur, rpm }; pos += dur + 2 * pad;
    bins.push({ rpm, on, off });
  }
  const n = Math.ceil((pos + 0.1) * SR);
  const data = new Float32Array(n);
  for (const b of bins) for (const r of [b.on, b.off]) {
    const a = Math.round(r.offset * SR), f = b.rpm / 5;
    for (let i = a - pad * SR; i < a + (r.duration + pad) * SR; i++) data[i] = 0.3 * Math.sin((2 * Math.PI * f * (i - a)) / SR);
  }
  const json = { sampleRate: SR, padding_s: pad, sprites: { on: 'engine_on.ogg', off: 'engine_off.ogg' }, bins,
    family: 'test_i4', cylinders: 4, layout: 'inline', redline_rpm: 6500, idle_rpm: 900 };
  return { json, data };
})();
const index: FamilyIndex = {
  version: 1,
  families: {
    test_i4: { cylinders: 4, layout: 'inline', redline: 6500, idle: 900, engine: 'test_i4/engine.json' },
    test_v8: { cylinders: 8, layout: 'v', redline: 5800, idle: 750, engine: 'test_v8/engine.json' },
  },
  aliases: [['\\bmiata\\b|mx-?5', 'test_i4'], ['small.?block|\\bsbc\\b|camaro|nova', 'test_v8']],
  fallback: [{ cylinders: 8, layout: 'v', family: 'test_v8' }, { cylinders: 4, layout: 'inline', family: 'test_i4' }],
  default: 'test_i4',
};
const synthFetch = async (url: string) => (url.endsWith('.json') ? resp(synth.json) : resp(new ArrayBuffer(8)));
const synthCtx = () => new FakeCtx(() => synth.data.slice());

const car = (id: number, pos: Vec3, o: Partial<FieldCar> = {}): FieldCar =>
  ({ id, pos, vel: [0, 0, 0], rpm: 4200, throttle: 1, redline: 6500, family: 'test_i4', ...o });
const lis = { pos: [0, 0, 0] as Vec3, vel: [0, 0, 0] as Vec3, quat: [0, 0, 0, 1] as [number, number, number, number] };

describe('family index', () => {
  it('maps engine guesses through aliases, then layout + cylinders, then the default', () => {
    expect(familyFor(index, { engineFamily: 'test_v8' })).toBe('test_v8');
    expect(familyFor(index, { make: 'Mazda', model: 'MX-5 Miata' })).toBe('test_i4');
    expect(familyFor(index, { engineFamily: 'Chevy small block 350', make: 'Chevrolet' })).toBe('test_v8');
    expect(familyFor(index, { make: 'Ford', model: 'Mustang', cylinders: 8, layout: 'v' })).toBe('test_v8');
    expect(familyFor(index, { make: 'Rover', cylinders: 8, layout: 'flat' })).toBe('test_v8'); // same cylinders
    expect(familyFor(index, { make: 'Unknown' })).toBe('test_i4');
  });
});

describe('loading a family', () => {
  it('loads the shipped engine.json format and both sprites, caching per context', async () => {
    const json = JSON.parse(readFileSync(new URL('../../../public/audio/engine.json', import.meta.url).pathname, 'utf8'));
    const last = json.bins[json.bins.length - 1];
    const need = Math.ceil((Math.max(last.on.offset + last.on.duration, last.off.offset + last.off.duration) + 0.2) * SR);
    const urls: string[] = [];
    const f = async (u: string) => { urls.push(u); return u.endsWith('.json') ? resp(json) : resp(new ArrayBuffer(4)); };
    const ctx = new FakeCtx(() => new Float32Array(need));
    const a = await loadFamily(asCtx(ctx), 'audio/families/probe/engine.json', f);
    expect(urls.sort()).toEqual(['audio/families/probe/engine.json', 'audio/families/probe/engine_off.ogg', 'audio/families/probe/engine_on.ogg']);
    expect(a.binRpm.length).toBe(json.bins.length);
    expect(a.binRpm[0]).toBe(1000);
    expect(a.on.length).toBe(need);
    const again = await loadFamily(asCtx(ctx), 'audio/families/probe/engine.json', f);
    expect(again).toBe(a);
    expect(urls.length).toBe(3);
  });
});

describe('AAC fallback', () => {
  const OFF_S = 96 / SR, PRIME_S = 2112 / SR;
  const fbJson = (extra: object = {}) => ({
    ...synth.json,
    fallback: { on: 'engine_on.m4a', off: 'engine_off.m4a', format: 'test', offset_s: OFF_S, offsets_s: { on: OFF_S, off: OFF_S },
      priming_s: PRIME_S, lengths_s: { on: synth.data.length / SR + OFF_S, off: synth.data.length / SR + OFF_S }, ...extra },
  });
  /** Ogg (first byte 1) cannot be decoded; the m4a (first byte 2) comes back delayed by `lead` samples. */
  const iosCtx = (lead: number, extraTail = 0) => new FakeCtx((ab) => {
    if (new Uint8Array(ab)[0] === 1) throw new DOMException('EncodingError');
    const d = new Float32Array(synth.data.length + lead + extraTail);
    d.set(synth.data, lead);
    return d;
  });
  const mkFetch = (json: object, urls: string[]) => async (u: string) => {
    urls.push(u);
    if (u.endsWith('.json')) return resp(json);
    return resp(new Uint8Array([u.endsWith('.m4a') ? 2 : 1]).buffer);
  };

  it('uses the m4a when the Ogg decode throws, shifting every loop offset by the measured codec offset', async () => {
    const urls: string[] = [];
    const ctx = iosCtx(96, 0);
    const a = await loadFamily(asCtx(ctx), 'x/test_i4/engine.json', mkFetch(fbJson(), urls));
    expect(urls.filter((u) => /\.(ogg|m4a)$/.test(u)).sort()).toEqual(['x/test_i4/engine_off.m4a', 'x/test_i4/engine_off.ogg', 'x/test_i4/engine_on.m4a', 'x/test_i4/engine_on.ogg']);
    expect(a.index.bins.map((b) => b.on.offset)).toEqual(synth.json.bins.map((b) => b.on.offset + OFF_S));
    expect(a.index.bins.map((b) => b.off.offset)).toEqual(synth.json.bins.map((b) => b.off.offset + OFF_S));
    // the shifted offset lands on the same audio as the original offset did in the Ogg decode
    const b0 = a.index.bins[3];
    const k = Math.round(b0.on.offset * SR), k0 = Math.round(synth.json.bins[3].on.offset * SR);
    for (const i of [10, 100, 300]) expect(a.on.getChannelData(0)[k + i]).toBeCloseTo(synth.data[k0 + i], 5);
    expect(synth.json.bins[3].on.offset).not.toBe(b0.on.offset); // the original index is untouched
  });

  it('adds the priming when the decoder kept it (longer decode)', async () => {
    const ctx = iosCtx(96 + 2112, 0);
    const a = await loadFamily(asCtx(ctx), 'x/test_i4/engine.json', mkFetch(fbJson(), []));
    expect(a.index.bins[0].on.offset).toBeCloseTo(synth.json.bins[0].on.offset + OFF_S + PRIME_S, 9);
    expect(a.index.bins[0].off.offset).toBeCloseTo(synth.json.bins[0].off.offset + OFF_S + PRIME_S, 9);
  });

  it('falls back when the Ogg file cannot be fetched, and without a fallback block still rejects', async () => {
    const urls: string[] = [];
    const base = mkFetch(fbJson(), urls);
    const f = async (u: string) => (u.endsWith('.ogg') ? { ok: false, json: async () => ({}), arrayBuffer: async () => new ArrayBuffer(0) } : base(u));
    const a = await loadFamily(asCtx(iosCtx(96)), 'x/a/engine.json', f);
    expect(a.index.bins[0].on.offset).toBeCloseTo(synth.json.bins[0].on.offset + OFF_S, 9);
    await expect(loadFamily(asCtx(iosCtx(96)), 'x/b/engine.json', mkFetch(synth.json, []))).rejects.toBeTruthy();
  });

  it('rejects (so the caller retries later) when neither codec decodes, and does not cache the failure', async () => {
    const ctx = new FakeCtx(() => { throw new DOMException('EncodingError'); });
    await expect(loadFamily(asCtx(ctx), 'x/test_i4/engine.json', mkFetch(fbJson(), []))).rejects.toBeTruthy();
    const ok = await loadFamily(asCtx(ctx), 'x/test_i4/engine.json', mkFetch(fbJson(), [])).catch(() => 'again');
    expect(ok).toBe('again');
  });

  it('goes straight to the m4a when the browser reports no Ogg Opus', async () => {
    const urls: string[] = [];
    const g = globalThis as any;
    const saved = g.document;
    g.document = { createElement: () => ({ canPlayType: () => '' }) };
    try {
      const ctx = new FakeCtx(() => synth.data.slice());
      const a = await loadFamily(asCtx(ctx), 'x/test_i4/engine.json', mkFetch(fbJson({ priming_s: 0 }), urls));
      expect(urls.some((u) => u.endsWith('.ogg'))).toBe(false);
      expect(a.index.bins[0].on.offset).toBeCloseTo(synth.json.bins[0].on.offset + OFF_S, 9);
    } finally { if (saved === undefined) delete g.document; else g.document = saved; }
  });
});

describe('engine voice', () => {
  it('plays rpm / loop rpm × trim, both bins and both loads crossfaded', async () => {
    const ctx = synthCtx();
    const a = await loadFamily(asCtx(ctx), 'x/test_i4/engine.json', synthFetch);
    const v = new EngineVoice(asCtx(ctx), ctx.destination as any, a, { trim: 1.03 });
    v.fadeTo(1, 0, 0.01);
    for (let k = 0; k < 15; k++) { v.update(4200, 0.5, 1, ctx.currentTime); ctx.advance(1 / 60); }
    const s = v.sources;
    expect(s.length).toBe(4); // 4000 and 4500 bins, on and off
    expect(new Set(s.map((x) => x.refRpm))).toEqual(new Set([4000, 4500]));
    for (const x of s) expect(x.src.playbackRate.value).toBeCloseTo((4200 * 1.03) / x.refRpm, 3);
    expect(v.rateFor(4200, 4000, 1.1)).toBeCloseTo((4200 * 1.03 * 1.1) / 4000, 9);
    // full throttle: the off layer is dropped once it fades
    for (let k = 0; k < 30; k++) { v.update(4200, 1, 1, ctx.currentTime); ctx.advance(1 / 60); }
    expect(v.sourceCount).toBeLessThanOrEqual(4);
  });
  it('trim is clamped to ±4 % and the muffler maps 0..1 to 12 kHz..900 Hz', () => {
    expect(mufflerCutoff(0)).toBeCloseTo(12000, 6);
    expect(mufflerCutoff(1)).toBeCloseTo(900, 6);
    expect(mufflerCutoff(0.5)).toBeGreaterThan(900);
    expect(mufflerCutoff(0.5)).toBeLessThan(12000);
  });
  it('stutters at the redline under throttle', async () => {
    const ctx = synthCtx();
    const a = await loadFamily(asCtx(ctx), 'x/test_i4/engine.json', synthFetch);
    const v = new EngineVoice(asCtx(ctx), ctx.destination as any, a, { redline: 6000, muffler: 0 });
    v.fadeTo(1, 0, 0.005);
    for (let k = 0; k < 60; k++) { v.update(6000, 1, 1, ctx.currentTime); ctx.advance(1 / 60); }
    const x = ctx.out[0].slice(SR * 0.5); // 32 half-periods per second -> windows of 1/32 s alternate
    const w = SR / 32, rms: number[] = [];
    for (let i = 0; i + w <= x.length; i += w) rms.push(Math.sqrt(x.slice(i, i + w).reduce((s, y) => s + y * y, 0) / w));
    const hi = Math.max(...rms), lo = Math.min(...rms);
    expect(lo / hi).toBeLessThan(0.4);
  });
});

describe('field selection, distance and Doppler', () => {
  it('keeps the N nearest within range', async () => {
    const ctx = synthCtx();
    const fa = new FieldAudio(asCtx(ctx), ctx.destination as any, { maxVoices: 4, index, base: 'x/', fetchFn: synthFetch });
    await fa.preload(['test_i4']);
    const cars = [car(99, [200, 0, 0]), ...Array.from({ length: 11 }, (_, i) => car(i, [0, 12 + 9 * i, 0]))];
    cars.reverse();
    fa.update(lis, cars);
    expect(fa.activeIds.map(Number).sort((p, q) => p - q)).toEqual([0, 1, 2, 3]);
    expect(selectNearest([0, 0, 0], cars, 20, 150)).not.toContain(99);
    // hysteresis: car 3 (39 m) stays against a newcomer at 37 m
    expect(selectNearest([0, 0, 0], [...cars, car(50, [37, 0, 0])], 4, 150, new Set([0, 1, 2, 3]))).toContain(3);
    expect(selectNearest([0, 0, 0], [...cars, car(50, [30, 0, 0])], 4, 150, new Set([0, 1, 2, 3]))).toContain(50);
  });
  it('distance gain: full inside 5 m, inverse distance, a floor, zero at the range edge', () => {
    expect(distanceGain(2, 150)).toBe(1);
    expect(distanceGain(20, 150)).toBeCloseTo(0.25, 6);
    expect(distanceGain(500, 1000)).toBeCloseTo(0.04, 6);
    expect(distanceGain(150, 150)).toBe(0);
  });
  it('Doppler: approaching raises the pitch, receding lowers it, clamped to ±15 %', () => {
    const o: Vec3 = [0, 0, 0], z: Vec3 = [0, 0, 0];
    expect(dopplerFactor(o, z, [50, 0, 0], [-30, 0, 0])).toBeGreaterThan(1);
    expect(dopplerFactor(o, z, [50, 0, 0], [30, 0, 0])).toBeLessThan(1);
    expect(dopplerFactor(o, [30, 0, 0], [50, 0, 0], z)).toBeGreaterThan(1); // listener driving toward it
    expect(dopplerFactor(o, z, [50, 0, 0], [0, 30, 0])).toBeCloseTo(1, 9);  // crossing
    expect(dopplerFactor(o, z, [50, 0, 0], [-200, 0, 0])).toBe(1.15);
    expect(dopplerFactor(o, z, [50, 0, 0], [200, 0, 0])).toBe(0.85);
  });
  it('applies Doppler to the voice playback rate and pans a car on the right to the right', async () => {
    const ctx = synthCtx();
    const fa = new FieldAudio(asCtx(ctx), ctx.destination as any, { maxVoices: 4, index, base: 'x/', fetchFn: synthFetch });
    await fa.preload(['test_i4']);
    // car 1 on the listener's right (y is left), driving toward the listener; car 2 far ahead, driving away
    for (let k = 0; k < 40; k++) {
      fa.update(lis, [car(1, [0, -20, 0], { vel: [0, 30, 0] }), car(2, [60, 0, 0], { vel: [30, 0, 0] })]);
      ctx.advance(1 / 60);
    }
    expect(fa.dopplerFor(1)!).toBeGreaterThan(1.05);
    expect(fa.dopplerFor(2)!).toBeLessThan(0.95);
    const v = fa.voiceFor(1)!;
    for (const s of v.sources) expect(s.src.playbackRate.value).toBeCloseTo((4200 * fa.dopplerFor(1)!) / s.refRpm, 2);
    // only car 1 now: its energy sits in the right channel
    for (let k = 0; k < 40; k++) { fa.update(lis, [car(1, [0, -20, 0])]); ctx.advance(1 / 60); }
    const tail = (c: number) => ctx.out[c].slice(-SR * 0.1).reduce((s, y) => s + y * y, 0);
    expect(tail(1)).toBeGreaterThan(20 * tail(0));
  });
});

describe('voice swaps', () => {
  it('fade in and out without clicks as cars enter and leave the nearest set', async () => {
    const ctx = synthCtx();
    const fa = new FieldAudio(asCtx(ctx), ctx.destination as any, { maxVoices: 3, index, base: 'x/', fetchFn: synthFetch });
    await fa.preload(['test_i4']);
    let swaps = 0, prev = '';
    const T = 3;
    for (let k = 0; k * (1 / 60) < T; k++) {
      const t = k / 60;
      const cars = Array.from({ length: 8 }, (_, i) => {
        const d = 15 + 60 * (0.5 + 0.5 * Math.sin(2.1 * t + i * 0.8));
        const a = i * 0.7;
        return car(i, [d * Math.cos(a), d * Math.sin(a), 0], { rpm: 5000 }); // a 1 kHz tone: 2 periods per 2 ms
      });
      fa.update(lis, cars);
      const ids = fa.activeIds.map(Number).sort().join(',');
      if (prev && ids !== prev) swaps++;
      prev = ids;
      ctx.advance(1 / 60);
    }
    expect(swaps).toBeGreaterThan(3);
    expect(fa.poolSize).toBeLessThanOrEqual(6);
    for (const x of ctx.out) {
      // sample steps: a 1 kHz sine moves at most 2π·1000/48000 ≈ 0.13 of its local peak per sample
      const n = x.length, win = 48;
      const gpk = x.reduce((m, y) => Math.max(m, Math.abs(y)), 0); // steps far below the content level are inaudible
      let worst = 0;
      for (let i = win; i < n - win; i++) {
        let pk = 1e-4;
        for (let j = i - win; j <= i + win; j += 4) pk = Math.max(pk, Math.abs(x[j]));
        worst = Math.max(worst, Math.abs(x[i] - x[i - 1]) / Math.max(pk, 0.05 * gpk));
      }
      expect(worst).toBeLessThan(0.2);
      // Gain steps: every voice plays the same 1 kHz tone, so x[i] − 2cos(ω)·x[i−1] + x[i−2] cancels the tone
      // whatever its amplitude and phase; what is left is the curvature of the gain envelopes. Smooth fades leave
      // ~0.003 of the peak, a hard gain cut ~0.2 (measured). (A 2 ms RMS envelope is not used: identical tones from
      // several voices interfere, and a new voice's muffler sweep shifts its phase, which moves the envelope
      // without any click.) Checked after the whole field's own onset from silence at t = 0.
      expect(gpk).toBeGreaterThan(0.01);
      const c2 = 2 * Math.cos((2 * Math.PI * 1000) / SR);
      let res = 0;
      for (let i = Math.round(0.25 * SR); i < n; i++) res = Math.max(res, Math.abs(x[i] - c2 * x[i - 1] + x[i - 2]));
      expect(res / gpk).toBeLessThan(0.02);
    }
  });
});

// race-mode plumbing (modes/race.ts fieldAudioHook): index.json with its per-car table → FieldAudio on a shared
// context, into a field bus; rpm × rpm_scale; a family whose files are missing stays silent and is retried.
describe('race field-audio hook', () => {
  const tick = () => new Promise((r) => setTimeout(r, 0));
  const raceIndex = { ...index, cars: { '34': { family: 'test_i4', trim: 1.0, muffler: 0.1, rpm_scale: 0.75, redline: 7000 }, '8': { family: 'test_v8', trim: 1.0 } } };
  const physState = (x: number, rpm: number) => ({ pos: [x, 0, 0] as Vec3, vel: [0, 0, 0] as Vec3, rpm, throttleOut: 1 });
  it('plays a car at physics rpm × rpm_scale into the field bus', async () => {
    const ctx = synthCtx();
    const bus = ctx.createGain();
    bus.connect(ctx.destination);
    const f = async (u: string) => (u.endsWith('index.json') ? resp(raceIndex) : synthFetch(u));
    const hook = fieldAudioHook(asCtx(ctx), bus as unknown as AudioNode, 8, 'x/', f)!;
    await hook.ready;
    expect(hook.audio).not.toBeNull();
    const snd = hook.sound({ number: '34', identity: null, engine: { layout: 'I3', cylinders: 3, exhaustNote: null } });
    expect(snd).toEqual({ family: 'test_i4', trim: 1, muffler: 0.1, rpmScale: 0.75 });
    const c: FieldAudioCar = fillAudioCar({ id: '34', pos: [0, 0, 0], vel: [0, 0, 0], rpm: 0, throttle: 0, redline: 0, family: '' }, physState(6, 5600), 6000, snd);
    expect(c.rpm).toBeCloseTo(4200, 9);
    expect(c.redline).toBeCloseTo(4500, 9);
    for (let k = 0; k < 40; k++) { await tick(); hook.audio!.update(lis, [c]); ctx.advance(1 / 60); }
    const fa = hook.audio as FieldAudio;
    const v = fa.voiceFor('34')!;
    expect(v).toBeTruthy();
    for (const x of v.sources) expect(x.src.playbackRate.value).toBeCloseTo(4200 / x.refRpm, 2);
    const tail = ctx.out[0].slice(-4800);
    expect(Math.max(...tail.map(Math.abs))).toBeGreaterThan(0.01); // audible through the bus
    hook.dispose();
  });
  it('a family whose files are missing is silent, does not throw, and is retried later', async () => {
    const ctx = synthCtx();
    let v8Fetches = 0;
    const f = async (u: string) => {
      if (u.endsWith('index.json')) return resp(raceIndex);
      if (u.includes('test_v8')) { v8Fetches++; return { ok: false, json: async () => null, arrayBuffer: async () => new ArrayBuffer(0) }; }
      return synthFetch(u);
    };
    const hook = fieldAudioHook(asCtx(ctx), ctx.destination as unknown as AudioNode, 8, 'x/', f)!;
    await hook.ready;
    const c = car(8, [5, 0, 0], { id: '8', family: 'test_v8', rpm: 4000 });
    const fa = hook.audio!;
    for (let k = 0; k < 60; k++) { expect(() => fa.update(lis, [c])).not.toThrow(); await tick(); ctx.advance(1 / 60); }
    expect((fa as FieldAudio).voiceFor('8')).toBeNull();
    expect(v8Fetches).toBe(1);                          // not hammered every frame
    ctx.advance(FAMILY_RETRY_S + 0.5);
    fa.update(lis, [c]);
    await tick();
    expect(v8Fetches).toBe(2);                          // retried after the back-off
    hook.dispose();
  });
  it('an unusable index.json leaves the hook silent (null audio) instead of throwing', async () => {
    const ctx = synthCtx();
    const hook = fieldAudioHook(asCtx(ctx), ctx.destination as unknown as AudioNode, 4, 'x/', async () => resp({ version: 1 }))!;
    await hook.ready;
    expect(hook.audio).toBeNull();
    expect(() => hook.tick?.()).not.toThrow();
    expect(parseSoundIndex(null)).toBeNull();
    expect(parseSoundIndex({ families: { a: {} }, default: 'zz' })!.default).toBe('a');
  });
  it('a car without an index row falls back to familyFor, the hashed trim and rpm_scale 1', () => {
    const i = parseSoundIndex(raceIndex)!;
    const s = carSound(i, { number: '999', identity: { make: 'Chevrolet', model: 'Nova', engine: { family: 'small block' } }, engine: { layout: 'V8', cylinders: 8 } });
    expect(s.family).toBe('test_v8');
    expect(s.rpmScale).toBe(1);
    expect(s.trim).toBeGreaterThanOrEqual(0.96);
    expect(s.trim).toBeLessThanOrEqual(1.04);
    // a row naming a family the index does not have (mid-rebuild) also falls back
    const j = parseSoundIndex({ ...raceIndex, cars: { '5': { family: 'gone', rpm_scale: 0.75 } } })!;
    const t = carSound(j, { number: '5', identity: null, engine: { layout: 'I4', cylinders: 4 } });
    expect(t.family).toBe('test_i4');
    expect(t.rpmScale).toBe(0.75);
    expect(carSound(null, { number: '5', identity: null, engine: { layout: 'I4', cylinders: 4 } }).family).toBe('');
  });
});
