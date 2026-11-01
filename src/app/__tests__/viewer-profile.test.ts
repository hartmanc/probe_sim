import { describe, expect, it } from 'vitest';
import { BALANCED, settingsFor, viewerProfile } from '../quality';

describe('the Cars page profile', () => {
  const phone = settingsFor('phone', 'auto', true);
  it('phone at dpr 3, 844 x 390: ratio 2, shadows, anisotropy 16, the post stack, 30 fps', () => {
    expect(viewerProfile(phone, 3, 844, 390)).toEqual({ ratio: 2, shadows: true, anisotropy: 16, post: true, fpsCap: 30 });
  });
  it('phone at dpr 3, 1200 x 560: the 2.5 MP budget caps the ratio', () => {
    const p = viewerProfile(phone, 3, 1200, 560);
    expect(p.ratio).toBeCloseTo(Math.sqrt(BALANCED.maxPixels / (1200 * 560)), 9);
    expect(p.ratio).toBeLessThan(2);
    expect(1200 * 560 * p.ratio * p.ratio).toBeLessThanOrEqual(BALANCED.maxPixels + 1);
  });
  it('phone at dpr 1 keeps ratio 1 (never up-scales)', () => {
    expect(viewerProfile(phone, 1, 844, 390).ratio).toBe(1);
  });
  it('desktop and balanced keep their own tier unchanged', () => {
    const desk = settingsFor('desktop', 'auto', false), bal = settingsFor('balanced', 'forced', false);
    expect(viewerProfile(desk, 2, 1280, 720)).toEqual({ ratio: 1.5, shadows: true, anisotropy: 16, post: true, fpsCap: 0 });
    expect(viewerProfile(bal, 2, 1280, 720)).toEqual({ ratio: 1.5, shadows: true, anisotropy: BALANCED.maxAnisotropy, post: true, fpsCap: 0 });
  });
  it('the phone tier itself is untouched (ratio 1, no shadows, anisotropy 2)', () => {
    expect(phone).toMatchObject({ maxPixelRatio: 1, shadows: false, maxAnisotropy: 2 });
  });
});
