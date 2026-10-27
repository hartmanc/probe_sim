// Round 15 (Buttonwillow, the owner's decision of 26 Oct 2026, item 19): with scenery `kerbs.inside` false the race edge
// is the kerb's asphalt side and every strip a band OUTSIDE it; the track limit stays the kerb's outside. A sample in
// such a band is SurfaceSample.onKerbBand (on the course for the track-limit tests) and nothing else changes: grip,
// height, paved and onTrack are what they were. Packages with inside kerbs (absent / true `inside`: Laguna, Sonoma) never
// set it.
import { describe, expect, it } from 'vitest';
import { createTrackSurface } from '../index';
import type { KerbsJson } from '../track';
import { continuation, heightfieldOf, ovalTrack } from './terrain_fixture';

const track = ovalTrack();
const hf = heightfieldOf(track, continuation);
// bottom straight: station s at x = s - 150, y = 0; the right edge at y = -5, the left at y = +5
const flat = (inside: boolean | undefined): KerbsJson => ({
  width: 0.9, ...(inside === undefined ? {} : { inside }),
  strips: [{ side: -1, s0: 100, s1: 140, off: 0.5, width: 1.0 }, { side: 1, s0: 200, s1: 230, kind: 'blocks', off: 0.45 }],
});
const surf = (k: KerbsJson | null) => createTrackSurface(track, hf, { kerbs: k });
const copy = (s: ReturnType<ReturnType<typeof surf>['sample']>) => ({ ...s });

describe('outside kerb bands are course for the track limit (kerbs.inside false)', () => {
  it('inside the band: onKerbBand, with grip, height and paving unchanged', () => {
    const a = copy(surf(flat(false)).sample(-30, -5.3)), b = copy(surf(null).sample(-30, -5.3));
    expect(a.onKerbBand).toBe(true);
    expect(a.onTrack).toBe(false); expect(a.paved).toBe(false);
    expect(a.mu).toBe(b.mu); expect(a.z).toBe(b.z); expect(a.dirt).toBe(b.dirt);
    expect(surf(flat(false)).sample(-30, -5.95).onKerbBand).toBe(true);    // 0.95 m out: the band is 1.0 m
  });
  it('beyond the kerb\'s outer edge, past its ends, on the other side and on the track: not on the band', () => {
    const s = surf(flat(false));
    expect(s.sample(-30, -6.1).onKerbBand).toBe(false);                    // 1.1 m out
    expect(s.sample(-60, -5.3).onKerbBand).toBe(false);                    // s 90, before the strip
    expect(s.sample(-5, -5.3).onKerbBand).toBe(false);                     // s 145, past it
    expect(s.sample(-30, 5.3).onKerbBand).toBe(false);                     // left side at s 120
    expect(s.sample(-30, -4.0).onKerbBand).toBe(false);                    // on the track
    expect(s.sample(-30, -4.0).onTrack).toBe(true);
  });
  it('a drawn-only block line is not a kerb band', () => {
    // bottom straight only runs to s 300; the left 'blocks' strip at s 200-230 is at x 50-80, y +5
    expect(surf(flat(false)).sample(65, 5.3).onKerbBand).toBe(false);
  });
  it('a raised outside band is on the course too (its hump unchanged)', () => {
    const raised: KerbsJson = { ...flat(false), profile: { height: 0.06, face: 0.15, back: 0.3 } };
    const r = copy(surf(raised).sample(-30, -5.5));
    expect(r.onKerbBand).toBe(true);
    expect(r.z - copy(surf(null).sample(-30, -5.5)).z).toBeCloseTo(0.06, 3);
  });
  it('inside kerbs (absent or true): never set, every field identical', () => {
    for (const k of [flat(undefined), flat(true)]) {
      for (const [x, y] of [[-30, -5.3], [-30, -4.0], [-30, -6.5], [65, 5.3]]) {
        const a = copy(surf(k).sample(x, y)), b = copy(surf(null).sample(x, y));
        expect(a.onKerbBand ?? false).toBe(false);
        expect(a.z).toBe(b.z); expect(a.mu).toBe(b.mu); expect(a.paved).toBe(b.paved); expect(a.onTrack).toBe(b.onTrack);
      }
    }
  });
});
