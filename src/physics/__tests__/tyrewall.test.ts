// Tyre walls are solid (Sonoma owner note, 22 Oct 2026: "I can drive into the tires in a tire wall"): on every
// registered track with tyre walls, the car driven square into tyre runs stops OUTSIDE the drawn stacks (the stack
// faces of src/app/scenery.ts, TYRE_WALL), as the armco test holds for a rail.
import { describe, expect, it } from 'vitest';
import { TRACKS } from '../../scoreboard/config';
import { createCollisionWorld, TYRE_WALL } from '../collision';
import { Vehicle } from '../index';
import { loadKerbPack } from './kerbprobe';
import { DT, input, probeSpec } from './helpers';

const FRONT = probeSpec().hull.front;
const ids = Object.keys(TRACKS).filter((id) => (loadKerbPack(TRACKS[id].dir).scenery?.barriers ?? []).some((b: any) => b.kind === 'tyres'));

describe.each(ids)('tyre walls are solid: %s', (id) => {
  const p = loadKerbPack(TRACKS[id].dir);
  const world = createCollisionWorld(p.scenery, p.track);
  const C = p.track.center;
  // every run 6 m or longer, approached square at its middle (by arc length; tangent over +-2 m) from the track's side
  const at = (pts: number[][], cum: number[], d: number) => {
    let i = 1; while (i < pts.length - 1 && cum[i] < d) i++;
    const f = (d - cum[i - 1]) / Math.max(cum[i] - cum[i - 1], 1e-9);
    return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
  };
  const cases = (p.scenery.barriers as any[]).filter((b) => b.kind === 'tyres').map((b) => {
    const cum = [0];
    for (let i = 1; i < b.pts.length; i++) cum.push(cum[i - 1] + Math.hypot(b.pts[i][0] - b.pts[i - 1][0], b.pts[i][1] - b.pts[i - 1][1]));
    const L = cum[cum.length - 1], m = at(b.pts, cum, L / 2), a = at(b.pts, cum, L / 2 - 2), e = at(b.pts, cum, L / 2 + 2);
    return { b, L, m, a, e };
  }).filter((c) => c.L >= 6);

  it.each(cases.map((c, k) => [k, c] as const))('run %i: a 12 m/s square hit stops outside the stacks', (_k, c) => {
    const tl = Math.hypot(c.e[0] - c.a[0], c.e[1] - c.a[1]);
    const tx = (c.e[0] - c.a[0]) / tl, ty = (c.e[1] - c.a[1]) / tl, lx = -ty, ly = tx;
    const [mx, my] = c.m;
    let j = 0, dj = Infinity;
    for (let k = 0; k < C.length; k++) { const d = Math.hypot(C[k][0] - mx, C[k][1] - my); if (d < dj) { dj = d; j = k; } }
    const side = (C[j][0] - mx) * lx + (C[j][1] - my) * ly > 0 ? 1 : -1;     // +1: the track is on the run's left
    const face = side > 0 ? TYRE_WALL.row + TYRE_WALL.r : -TYRE_WALL.r;     // the stacks' face toward the track
    const start = face + side * (FRONT + 4);
    const v = new Vehicle(probeSpec(), { autoShift: true });
    v.setCollisionWorld(world);
    const x0 = mx + lx * start, y0 = my + ly * start;
    v.reset([x0, y0, p.surface.sample(x0, y0).z + 0.05], Math.atan2(-side * ly, -side * lx), 12);
    let closest = Infinity;   // the nose's least distance before the stacks' face (negative: into the stacks)
    for (let i = 0; i < 2500; i++) {
      v.step(input(), p.surface, DT);
      const s = v.state, d = side * ((s.pos[0] - mx) * lx + (s.pos[1] - my) * ly) - side * face - FRONT;
      closest = Math.min(closest, d);
    }
    console.log(`${id} tyre run ${c.b.src?.slice(0, 40) ?? ''}: nose ${closest.toFixed(3)} m from the stack face, impact ${v.state.impact?.kind} ${v.state.impact?.speedNormal.toFixed(1)} m/s`);
    // a run behind another barrier (the T7 approach: concrete in front of it) is not reached: no tyre impact needed
    if (closest < 0.3) expect(v.state.impact?.kind).toBe('tyres');
    expect(v.state.launched).toBe(false);
    expect(closest).toBeGreaterThan(-0.15);   // the nose never more than 15 cm into the stacks (the armco test's rule)
  });
});
