import { describe, expect, it } from 'vitest';
import { decodeSprite, fallbackShift, shiftIndex, type EngineIndex, type FallbackInfo } from '../audio';

const FB: FallbackInfo = {
  on: 'engine_on.m4a', off: 'engine_off.m4a', squeal: 'squeal.m4a',
  offset_s: 0.001, offsets_s: { on: 0.002, off: 0.001 }, priming_s: 0.044,
  lengths_s: { on: 22.144, off: 20.48, squeal: 1.45 },
};
const ogg = new Uint8Array([1]).buffer, m4a = new Uint8Array([2]).buffer;

/** A decoder that cannot read Ogg (old iOS) and returns `m4aDuration` for the AAC file. */
const iosDecode = (m4aDuration: number) => async (b: ArrayBuffer) => {
  if (new Uint8Array(b)[0] === 1) throw new DOMException('EncodingError');
  return { duration: m4aDuration };
};

describe('AAC fallback offsets', () => {
  it('uses the per-file offset, or the common one', () => {
    expect(fallbackShift(FB, 'on', 22.144)).toBeCloseTo(0.002, 9);
    expect(fallbackShift(FB, 'squeal', 1.45)).toBeCloseTo(0.001, 9);
  });

  it('adds the priming when the decoder kept it (longer decode)', () => {
    expect(fallbackShift(FB, 'on', 22.144 + 0.044)).toBeCloseTo(0.046, 9);
    expect(fallbackShift(FB, 'off', 20.48 - 0.006)).toBeCloseTo(0.001, 9); // end padding trimmed: no priming
  });

  it('decodes Ogg when it can (no shift)', async () => {
    const r = await decodeSprite(async () => ({ duration: 22 }), ogg, false, async () => m4a, FB, 'on');
    expect(r).toEqual({ buffer: { duration: 22 }, shift: 0, fallback: false });
  });

  it('falls back to the m4a on an Ogg decode failure and applies its offset', async () => {
    let fetched = 0;
    const r = await decodeSprite(iosDecode(22.188), ogg, false, async () => { fetched++; return m4a; }, FB, 'on');
    expect(fetched).toBe(1);
    expect(r.fallback).toBe(true);
    expect(r.shift).toBeCloseTo(0.046, 9);
  });

  it('uses an m4a primary directly (no second fetch)', async () => {
    const r = await decodeSprite(iosDecode(20.48), m4a, true, async () => { throw new Error('no fetch expected'); }, FB, 'off');
    expect(r.shift).toBeCloseTo(0.001, 9);
  });

  it('rethrows without a fallback', async () => {
    await expect(decodeSprite(iosDecode(1), ogg, false, async () => null, undefined, 'on')).rejects.toBeTruthy();
  });

  it('shifts every loop offset of a layer, leaving the rest alone', () => {
    const idx: EngineIndex = { sampleRate: 48000, bins: [
      { rpm: 1000, on: { offset: 0.15, duration: 0.9, rpm: 999 }, off: { offset: 0.15, duration: 0.8 } },
      { rpm: 1250, on: { offset: 1.2, duration: 0.9 }, off: { offset: 1.1, duration: 0.5 } },
    ] };
    const s = shiftIndex(idx, 0.046, 0.001);
    expect(s.bins.map((b) => b.on.offset)).toEqual([0.15 + 0.046, 1.2 + 0.046]);
    expect(s.bins.map((b) => b.off.offset)).toEqual([0.15 + 0.001, 1.1 + 0.001]);
    expect(s.bins[0].on.duration).toBe(0.9);
    expect(s.bins[0].on.rpm).toBe(999);
    expect(idx.bins[0].on.offset).toBe(0.15); // original untouched
    expect(shiftIndex(idx, 0, 0)).toBe(idx);
  });
});
