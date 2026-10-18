import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { audioParamsFromCarJson, binWeights, healLoopSeams, squealMix, wheelSqueal, type EngineIndex } from '../audio';
import type { VehicleState, WheelState } from '../physics-types';

const carJson = JSON.parse(readFileSync(new URL('../../../public/cars/probe_gt/car.json', import.meta.url).pathname, 'utf8'));
const P = audioParamsFromCarJson(carJson);

const wheel = (o: Partial<WheelState> = {}): WheelState => ({
  pos: [0, 0, 0], spinAngle: 0, steer: 0, compression: 0, omega: 0, slipRatio: 0, slipAngle: 0, load: 3500, onTrack: true, ...o,
});
const state = (w: Partial<WheelState>[], speed = 20): VehicleState => ({
  pos: [0, 0, 0], quat: [0, 0, 0, 1], vel: [speed, 0, 0], angVel: [0, 0, 0],
  wheels: [wheel(w[0]), wheel(w[1]), wheel(w[2]), wheel(w[3])], rpm: 4000, gear: 3, speed, gLat: 0, gLong: 0, throttleOut: 1,
});

describe('engine bin cross-fade', () => {
  const bins = Float64Array.from({ length: 23 }, (_, i) => 1000 + 250 * i);
  const out = new Float64Array(4);
  it('is equal-power and continuous across bin boundaries', () => {
    let prev: number[] | null = null;
    for (let rpm = 900; rpm <= 6900; rpm += 7) {
      binWeights(bins, rpm, out);
      expect(out[1] ** 2 + out[3] ** 2).toBeCloseTo(1, 9);
      // per-bin weight vector is continuous in rpm
      const v = new Array(23).fill(0); v[out[0]] += out[1]; v[out[2]] += out[3];
      if (prev) for (let i = 0; i < 23; i++) expect(Math.abs(v[i] - prev[i])).toBeLessThan(0.07);
      prev = v;
    }
  });
  it('picks the bins around rpm', () => {
    binWeights(bins, 3125, out);
    expect([out[0], out[2]]).toEqual([8, 9]);
    expect(out[1]).toBeCloseTo(Math.SQRT1_2, 6);
  });
  it('the shipped index covers 1000-6500 rpm every 250 with both loads', () => {
    const idx: EngineIndex = JSON.parse(readFileSync(new URL('../../../public/audio/engine.json', import.meta.url).pathname, 'utf8'));
    expect(idx.bins.map((b) => b.rpm)).toEqual(Array.from(bins));
    for (const b of idx.bins) for (const r of [b.on, b.off]) {
      expect(r.duration).toBeGreaterThan(0.3);
      expect(Math.abs((r.rpm ?? b.rpm) - b.rpm)).toBeLessThan(40);
    }
  });
});

describe('tyre squeal onset', () => {
  it('reads the tyre peaks from car.json', () => {
    expect(P.peakSlipAngle).toBeCloseTo((7 * Math.PI) / 180, 6);
    expect(P.peakSlipRatio).toBeCloseTo(0.12, 6);
  });
  it('is silent below 0.85 of the peak, full at 1.3, using slipUse', () => {
    expect(wheelSqueal(wheel({ slipUse: 0.84 }), 20, P)).toBe(0);
    expect(wheelSqueal(wheel({ slipUse: 1.0 }), 20, P)).toBeGreaterThan(0);
    expect(wheelSqueal(wheel({ slipUse: 1.0 }), 20, P)).toBeLessThan(0.4);
    expect(wheelSqueal(wheel({ slipUse: 1.3 }), 20, P)).toBeCloseTo(1, 6);
    // slipUse wins over the raw slips
    expect(wheelSqueal(wheel({ slipUse: 0.5, slipAngle: 0.3 }), 20, P)).toBe(0);
  });
  it('falls back to the slip angle / ratio against the peaks', () => {
    expect(wheelSqueal(wheel({ slipAngle: 0.8 * P.peakSlipAngle }), 20, P)).toBe(0);
    expect(wheelSqueal(wheel({ slipAngle: 1.3 * P.peakSlipAngle }), 20, P)).toBeCloseTo(1, 6);
  });
  it('needs load and speed', () => {
    expect(wheelSqueal(wheel({ slipUse: 2, load: 1400 }), 20, P)).toBe(0);
    expect(wheelSqueal(wheel({ slipUse: 2 }), 4.9, P)).toBe(0);
  });
  it('separates lock-up (skid) from lateral scrub', () => {
    const m = { scrub: 0, skid: 0, slide: 0 };
    squealMix(state([{ slipUse: 1.5, slipAngle: 0.15 }, {}, {}, {}]), P, m);
    expect(m.scrub).toBeCloseTo(1, 6); expect(m.skid).toBe(0);
    squealMix(state([{ slipUse: 2.5, slipRatio: -0.3 }, { slipUse: 2.5, slipRatio: -0.3 }, {}, {}]), P, m);
    expect(m.skid).toBeCloseTo(1, 6); expect(m.scrub).toBeCloseTo(0, 6);
    expect(m.slide).toBeGreaterThan(5);
  });
});

describe('loop seam healing', () => {
  it('removes a codec step at the loop seam using the cyclic tail pad', () => {
    const sr = 1000, pad = 50, len = 400;
    const loop = Array.from({ length: len }, (_, i) => Math.sin((2 * Math.PI * 5 * i) / len));
    const data = new Float32Array(pad + len + pad);
    for (let i = 0; i < pad; i++) data[i] = loop[len - pad + i];
    for (let i = 0; i < len; i++) data[pad + i] = loop[i];
    for (let i = 0; i < pad; i++) data[pad + len + i] = loop[i];
    // "codec noise": the loop's tail decoded 0.3 off
    for (let i = len - 60; i < len; i++) data[pad + i] += 0.3;
    const step = () => Math.abs(data[pad] - data[pad + len - 1]);
    expect(step()).toBeGreaterThan(0.2);
    healLoopSeams(data, sr, [{ offset: pad / sr, duration: len / sr }], 32);
    expect(step()).toBeLessThan(0.1 + 1e-3); // one ordinary sample step of this sine is ~0.08
    expect(Math.abs(data[pad + len - 1] - data[pad - 1])).toBeLessThan(1e-6);
  });
});
