// The terrain-override gates (tools/track/gates/terrainGates.ts, Sonoma round 14A): pavement joins, surface smoothness
// and kerbs on the surface, on a synthetic oval whose override surface is right, stepped, troughed or ridged; a package
// without a region passes them as n/a; the published Sonoma package passes them.
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { loadHeightfield } from '../../physics/index';
import { terrainGates } from '../../../tools/track/gates/terrainGates';
import { REGION, continuation, heightfieldOf, ovalTrack, stripPart } from '../../physics/__tests__/terrain_fixture';

const track = ovalTrack();
const sm = (t: number) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));

describe('terrain gates: synthetic', () => {
  it('a surface that continues the course, a paved strip on it and kerb blocks on it: all pass', () => {
    const hf = heightfieldOf(track, continuation);
    const sc = { terrain_override: REGION, paved_zones: { spacing_m: 1, fractions: track.profile.fractions, parts: [stripPart(continuation)] },
      kerb_lines: [{ pts: [[-20, -16, 0], [20, -16, 0]], width: 1, height: 0.05, stripe_m: 0.95, colors: ['#b8433a', '#dedbd2'] }] };
    const r = terrainGates(track, hf, sc);
    expect(r.regions).toBe(1);
    expect(r.joins.checked).toBeGreaterThan(200);
    expect(r.joins.maxStep).toBeLessThan(0.002);
    expect(r.joins.maxSlopeDeg).toBeLessThan(0.1);
    expect(r.smooth.profiles).toBeGreaterThan(100);
    expect(r.smooth.maxD2).toBeLessThan(0.001);
    expect(r.kerbs.blocks).toBeGreaterThan(30);
    expect(r.kerbs.bad).toHaveLength(0);
    expect(r.fail).toBe(false);
  });

  it('the surface stepping down 0.1 m at the course edge: the pavement-join gate fails', () => {
    const hf = heightfieldOf(track, (x, y) => continuation(x, y) - (Math.abs(y) > 5.5 ? 0.1 : 0));
    const r = terrainGates(track, hf, { terrain_override: REGION });
    expect(r.joins.bad.length).toBeGreaterThan(0);
    expect(r.joins.maxStep).toBeGreaterThan(0.02);
    expect(r.fail).toBe(true);
  });

  it('a 0.15 m trough 10 m beside the course: the smoothness gate fails on the trough and the second difference', () => {
    const hf = heightfieldOf(track, (x, y) => continuation(x, y) - 0.15 * Math.exp(-(((y + 15) / 2) ** 2)));
    const r = terrainGates(track, hf, { terrain_override: REGION });
    expect(r.joins.bad).toHaveLength(0);
    expect(r.smooth.maxTrough).toBeGreaterThan(0.05);
    expect(r.smooth.badDev.length).toBeGreaterThan(0);
    expect(r.smooth.badD2.length).toBeGreaterThan(0);
    expect(r.fail).toBe(true);
  });

  it('a gentle 0.3 m ridge spread over 60 m passes (a grade, not a ridge)', () => {
    const hf = heightfieldOf(track, (x, y) => continuation(x, y) + 0.3 * sm((Math.abs(y) - 5) / 30));
    const r = terrainGates(track, hf, { terrain_override: REGION });
    expect(r.fail).toBe(false);
  });

  it('kerb blocks on the rim of a trough: tilted from the surface and a gap under them', () => {
    // a 0.6 m trough along y = -16 (the 2 m heightfield draws it as a 4 m V): one kerb line on its rim (tilted), one straddling it (a gap under the middle)
    const hf = heightfieldOf(track, (x, y) => continuation(x, y) - 0.6 * Math.exp(-(((y + 16) / 1.0) ** 2)));
    const line = (y: number) => ({ pts: [[-20, y, 0], [20, y, 0]] as [number, number, number][], width: 1, height: 0.05, stripe_m: 0.95, colors: ['#fff'] });
    const rim = terrainGates(track, hf, { terrain_override: REGION, kerb_lines: [line(-16.5)] });
    expect(rim.kerbs.bad.length).toBeGreaterThan(0);
    expect(rim.kerbs.maxTiltDeg).toBeGreaterThan(2);
    const across = terrainGates(track, hf, { terrain_override: REGION, kerb_lines: [line(-16)] });
    expect(across.kerbs.maxGap).toBeGreaterThan(0.05);
    expect(across.kerbs.bad.length).toBeGreaterThan(0);
  });

  it('no terrain_override: no region, nothing measured, no failure', () => {
    const hf = heightfieldOf(track, (x, y) => continuation(x, y) - 0.5);
    const r = terrainGates(track, hf, {});
    expect(r.regions).toBe(0);
    expect(r.joins.checked + r.smooth.profiles + r.kerbs.blocks).toBe(0);
    expect(r.fail).toBe(false);
  });
});

describe('terrain gates: the published Sonoma package', () => {
  const dir = fileURLToPath(new URL('../../../public/tracks/sonoma/', import.meta.url));
  const sc = existsSync(dir + 'scenery.json') ? JSON.parse(readFileSync(dir + 'scenery.json', 'utf8')) : null;
  it.runIf(!!sc?.terrain_override)('passes every terrain gate in its T7 complex region', () => {
    const t = JSON.parse(readFileSync(dir + 'track.json', 'utf8'));
    const hf = loadHeightfield(Uint8Array.from(readFileSync(dir + 'heightfield.bin')).buffer);
    const r = terrainGates(t, hf, sc);
    expect(r.regions).toBeGreaterThan(0);
    expect(r.joins.checked).toBeGreaterThan(500);
    expect(r.joins.bad).toHaveLength(0);
    expect(r.smooth.badD2).toHaveLength(0);
    expect(r.smooth.badDev).toHaveLength(0);
    expect(r.kerbs.bad).toHaveLength(0);
  });
});
