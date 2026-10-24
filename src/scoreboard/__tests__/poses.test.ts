// The owner's poses of the drive proxy (tools/track/compare/poses.ts, codify round 20 Oct 2026): inside the pit lane end
// to end, facing the way the cars drive it, and from every paved runoff the track reaches, looking back at the track.
import { describe, expect, it } from 'vitest';
import { pitPoses, RUNOFF_BACK, runoffPoses } from '../../../tools/track/compare/poses';
import type { TrackLike, V3 } from '../../../tools/track/gates/sceneryGates';

// the 400 m loop of scenerygates.test.ts: bottom straight y = 0 from x 0 to 150 driving +x (left = +y), 1 m stations
function loop(): TrackLike {
  const C: V3[] = [], L: V3[] = [], R: V3[] = [];
  const Ls = 150, Rr = 30, n = Math.round(2 * Ls + 2 * Math.PI * Rr);
  for (let k = 0; k < n; k++) {
    let s = k, x: number, y: number, h: number;
    if (s < Ls) { x = s; y = 0; h = 0; }
    else if ((s -= Ls) < Math.PI * Rr) { const a = s / Rr; x = Ls + Rr * Math.sin(a); y = Rr - Rr * Math.cos(a); h = a; }
    else if ((s -= Math.PI * Rr) < Ls) { x = Ls - s; y = 2 * Rr; h = Math.PI; }
    else { s -= Ls; const a = s / Rr; x = -Rr * Math.sin(a); y = Rr + Rr * Math.cos(a); h = Math.PI + a; }
    const nx = -Math.sin(h), ny = Math.cos(h);
    C.push([x, y, 0]); L.push([x + nx * 5, y + ny * 5, 0]); R.push([x - nx * 5, y - ny * 5, 0]);
  }
  return { n, spacing_m: 1, center: C, left: L, right: R };
}
const T = loop();
const strip = (x0: number, x1: number, y: number, hw: number, reverse = false) => {
  const xs = Array.from({ length: x1 - x0 + 1 }, (_, k) => x0 + k);
  if (reverse) xs.reverse();
  const sg = reverse ? -1 : 1;
  return { center: xs.map((x) => [x, y, 0] as V3), left: xs.map((x) => [x, y + sg * hw, 0] as V3), right: xs.map((x) => [x, y - sg * hw, 0] as V3) };
};

describe('drive-proxy poses: pit lane', () => {
  it('walks every part end to end every step metres, facing the driving direction even when the part is stored backwards', () => {
    for (const reverse of [false, true]) {
      const p = pitPoses(T, { pit_lane: { parts: [strip(20, 120, -17, 3, reverse)] } }, 25);
      expect(p.map((q) => Math.round(q.pos[0]))).toEqual([20, 45, 70, 95, 120]);
      for (const q of p) {
        expect(Math.cos(q.heading)).toBeGreaterThan(0.99);   // +x, as the track runs alongside
        expect(q.pos[2]).toBeNull();                          // the surface height is sampled in the page
        expect(q.side).toBe('pit');
      }
      expect(Math.round(p[2].s)).toBe(70);
    }
  });
  it('no lane, or a step of 0, gives no poses', () => {
    expect(pitPoses(T, {}, 25)).toHaveLength(0);
    expect(pitPoses(T, { pit_lane: { parts: [strip(20, 120, -17, 3)] } }, 0)).toHaveLength(0);
  });
});

describe('drive-proxy poses: from the runoff', () => {
  it('one pose per paved polygon reached (per 150 m of it), from its far side, looking back across it at the track', () => {
    // a closed road on the right of the bottom straight, 9 m beyond the edge (y -14 .. -26), no barrier between
    const sc = { paved_zones: { parts: [{ ...strip(40, 100, -20, 6), kind: 'closed_road', turn: 'old road' }] } };
    const r = runoffPoses(T, sc);
    expect(r).toHaveLength(1);
    const q = r[0];
    expect(q.label).toMatch(/old road, right of s .* \(across 1[12] m of its paving\)/);
    // round 11: the whole 12 m of paving lies between the camera and the track (the car RUNOFF_BACK m beyond its far
    // side, so the hood's blind ground is the dirt behind it), not 4 m inside its near side
    expect(q.pos[1]).toBeLessThan(-26 - RUNOFF_BACK + 1);
    expect(q.pos[1]).toBeGreaterThan(-26 - RUNOFF_BACK - 1);
    expect(Math.sin(q.heading)).toBeGreaterThan(0.99);      // facing +y, back at the track
    expect(q.s).toBeGreaterThanOrEqual(40);
    expect(q.s).toBeLessThanOrEqual(100);
  });
  it('a polygon deeper than 30 m along the ray (a road running away from the track): 25 m into it', () => {
    const sc = { paved_zones: { parts: [{ center: [[60, -10, 0], [60, -80, 0]] as V3[], left: [[64, -10, 0], [64, -80, 0]] as V3[], right: [[56, -10, 0], [56, -80, 0]] as V3[], kind: 'closed_road', turn: 'spur' }] } };
    const r = runoffPoses(T, sc);
    expect(r.length).toBeGreaterThan(0);
    for (const q of r) { expect(Math.abs(q.pos[1] - (-10 - 25))).toBeLessThanOrEqual(1); expect(Math.sin(q.heading)).toBeGreaterThan(0.99); }
  });
  it('a barrier between the track and the polygon hides it; a paved runoff zone gets a pose looking at the track', () => {
    const wall = { kind: 'concrete', pts: [[0, -7, 0], [150, -7, 0]] as V3[] };
    const road = { ...strip(40, 100, -20, 6), kind: 'closed_road', turn: 'old road' };
    expect(runoffPoses(T, { barriers: [wall], paved_zones: { parts: [road] } })).toHaveLength(0);
    const zone = { ...strip(60, 80, 12, 4), kind: 'runoff', turn: 'T1 runoff' };
    const r = runoffPoses(T, { barriers: [wall], paved_zones: { parts: [road, zone] } });
    expect(r.map((q) => q.label)).toEqual(['T1 runoff (paved runoff zone)']);
    expect(Math.sin(r[0].heading)).toBeLessThan(-0.99);     // from y 12 looking toward the centre at y 0
  });
});
