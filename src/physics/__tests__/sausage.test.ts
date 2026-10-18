// Sausage kerbs: a hump beyond the apex kerb that the surface sampler adds on top of the shoulder.
import { describe, expect, it } from 'vitest';
import { createDevTrack } from '../devtrack';
import { createTrackSurface, SAUSAGE_RAMP_M, type SausageJson } from '../track';

const dev = createDevTrack();
const J: SausageJson = { width: 0.5, height: 0.06, gap: 0.25, kerb_width: 0.9, strips: [{ side: 1, s0: 100, s1: 124, corner: 'test' }] };
/** tyre-widened half-width the sampler uses (see SAUSAGE_TYRE_R) */
const WH = J.width / 2 + Math.sqrt(2 * 0.3 * J.height);
const plain = createTrackSurface(dev.track, dev.heightfield);
const withS = createTrackSurface(dev.track, dev.heightfield, { sausages: J });

/** Point `d` m left of the sausage's centreline at station i (centre = left edge + 1.45 m). */
function at(i: number, d: number): [number, number] {
  const t = dev.track, n = t.n;
  const a = t.center[(i - 1 + n) % n], b = t.center[(i + 1) % n];
  const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy);
  const nx = -dy / l, ny = dx / l, e = t.left[i], off = 0.9 + 0.25 + 0.25 + d;
  return [e[0] + nx * off, e[1] + ny * off];
}

describe('sausage kerbs', () => {
  it('lifts the surface by the hump height on the centreline and not beside it', () => {
    const [x, y] = at(112, 0);
    const z0 = plain.sample(x, y).z, z1 = withS.sample(x, y).z;
    expect(z1 - z0).toBeCloseTo(0.06, 3);
    const [x2, y2] = at(112, WH + 0.05);
    expect(withS.sample(x2, y2).z - plain.sample(x2, y2).z).toBeCloseTo(0, 6);
    const [x3, y3] = at(112, -WH - 0.05);
    expect(withS.sample(x3, y3).z - plain.sample(x3, y3).z).toBeCloseTo(0, 6);
  });
  it('tilts the normal on the flank, full grip on the concrete, ramps down at the ends', () => {
    const [x, y] = at(112, WH / 2);
    const s = withS.sample(x, y);
    // a bump, not a wall: the flank tilts the normal by a few degrees, never past SAUSAGE_MAX_SLOPE
    expect(Math.hypot(s.nx, s.ny)).toBeGreaterThan(0.05);
    expect(Math.hypot(s.nx, s.ny) / s.nz).toBeLessThanOrEqual(0.6 + 1e-9);
    expect(s.mu).toBeCloseTo(s.muPaved ?? 1, 6);
    const [xe, ye] = at(100, 0); // the end station: ramp 0
    expect(withS.sample(xe, ye).z - plain.sample(xe, ye).z).toBeLessThan(0.02);
    const [xr, yr] = at(100 + Math.ceil(SAUSAGE_RAMP_M), 0);
    expect(withS.sample(xr, yr).z - plain.sample(xr, yr).z).toBeCloseTo(0.06, 2);
  });
  it('leaves the racing surface untouched', () => {
    const c = dev.track.center[112];
    expect(withS.sample(c[0], c[1]).z).toBeCloseTo(plain.sample(c[0], c[1]).z, 9);
    expect(withS.sample(c[0], c[1]).onTrack).toBe(true);
  });
});
