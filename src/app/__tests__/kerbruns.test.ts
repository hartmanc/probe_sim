// Kerb runs (Buttonwillow, 21 Oct 2026, the owner's "weird, disjointed kerbs"): a run's per-station offsets move the
// strip's columns with no steps; a strip without offsets (Laguna, Sonoma) builds exactly the geometry it did before.
import { describe, expect, it } from 'vitest';
import { createDevTrack } from '../../physics/devtrack';
import { PaintStrips, edgeFrame } from '../scenery';

const dev = createDevTrack();
const cols = [{ out: -0.45, dz: 0.008, v: 0.1 }, { out: 0, dz: 0.009, v: 0.5 }, { out: 0.45, dz: 0.01, v: 0.9 }];
const build = (shift?: number[]) => {
  const p = new PaintStrips(edgeFrame(dev.track as never, undefined), undefined, dev.track.spacing_m || 1);
  p.add(1, 100, 140, cols, -1.2, 0, shift);
  return p;
};

describe('kerb runs', () => {
  it('no offsets: the same vertices, uvs and indices as before (a zero shift changes nothing)', () => {
    const a = build(), b = build(new Array(41).fill(0));
    expect(b.pos).toEqual(a.pos); expect(b.puv).toEqual(a.puv); expect(b.idx).toEqual(a.idx);
  });
  it('per-station offsets move every column by the offset, and the paint u runs on continuously', () => {
    const sh = Array.from({ length: 41 }, (_, i) => 0.3 + 0.01 * i);
    const a = build(), b = build(sh), K = cols.length;
    for (const i of [0, 20, 40]) for (let k = 0; k < K; k++) {
      const q = (i * K + k) * 3;
      const d = Math.hypot(b.pos[q] - a.pos[q], b.pos[q + 2] - a.pos[q + 2]);
      expect(d).toBeCloseTo(sh[i], 6);
    }
    const u = b.puv.filter((_, j) => j % 2 === 0);
    for (let i = 1; i < 41; i++) expect(u[i * K] - u[(i - 1) * K]).toBeGreaterThan(0);
  });
});
