// Lost in the hills (owner, 23 Oct 2026): the player's car far off the track for OFFTRACK_HOLD_S is launched into space
// like a hard wall hit, with its own game-over line. "Far" is from the track data (src/physics/offtrack.ts).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import {
  OFFTRACK_BARRIER_MARGIN_M, OFFTRACK_FAR_M, OFFTRACK_HOLD_S, OffTrackWatch, Vehicle, createEdgeDistance, createOffTrackJudge,
  type TrackJson,
} from '../../physics';
import { HotlapSim, type SceneryLike } from '../../scoreboard';
import { lagunaAssets } from '../../scoreboard/__tests__/fixtures';
import { LOST_IN_HILLS_LINE } from '../offtrack';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const load = (id: string) => ({
  track: JSON.parse(readFileSync(`${pub}tracks/${id}/track.json`, 'utf8')) as TrackJson,
  scenery: JSON.parse(readFileSync(`${pub}tracks/${id}/scenery.json`, 'utf8')) as SceneryLike,
});

/** A point `past` m beyond the edge on `side` of station i (along the centreline's normal there). */
function besideStation(track: TrackJson, i: number, side: 1 | -1, past: number): [number, number] {
  const c = track.center[i], e = side > 0 ? track.left[i] : track.right[i];
  const dx = e[0] - c[0], dy = e[1] - c[1], h = Math.hypot(dx, dy);
  return [e[0] + (dx / h) * past, e[1] + (dy / h) * past];
}

describe('lost in the hills: the hold', () => {
  const DT = 0.005;   // the sim's timing tick
  const run = (w: OffTrackWatch, far: boolean, s: number) => {
    let fired = false;
    for (let t = 0; t < s - 1e-9; t += DT) fired = w.update(far, DT) || fired;
    return fired;
  };
  it('inside the band: never', () => {
    expect(run(new OffTrackWatch(), false, 60)).toBe(false);
  });
  it('beyond it for OFFTRACK_HOLD_S: once, not a tick earlier', () => {
    expect(OFFTRACK_HOLD_S).toBe(2);
    const w = new OffTrackWatch();
    expect(run(w, true, OFFTRACK_HOLD_S - DT)).toBe(false);
    expect(w.update(true, DT)).toBe(true);
    expect(run(w, true, 10)).toBe(false);   // once
    w.reset();
    expect(run(w, true, OFFTRACK_HOLD_S)).toBe(true);
  });
  it('a brief excursion: no launch, and coming back starts the count again', () => {
    const w = new OffTrackWatch();
    expect(run(w, true, 1.5)).toBe(false);
    expect(run(w, false, DT)).toBe(false);
    expect(w.heldS).toBe(0);
    expect(run(w, true, 1.5)).toBe(false);
  });
});

describe('lost in the hills: "far" from the track data', () => {
  for (const id of ['laguna_seca', 'sonoma']) {
    const { track, scenery } = load(id);
    const judge = createOffTrackJudge(track, { barriers: scenery.barriers });
    const edge = createEdgeDistance(track);
    it(`${id}: the road and a runoff are not far; past the local limit and off the terrain band are`, () => {
      let checked = 0;
      for (let i = 0; i < track.n; i += 50) {
        for (const side of [1, -1] as const) {
          expect(judge.far(track.center[i][0], track.center[i][1])).toBe(false);
          const near = besideStation(track, i, side, 25);   // a wide excursion, inside the default limit
          const e = edge(near[0], near[1]);
          if (e.seg !== i && e.seg !== (i - 1 + track.n) % track.n) continue;   // another part of the lap is nearer
          expect(judge.far(near[0], near[1])).toBe(false);
          const lim = judge.limit(e.seg, side);
          expect(lim).toBeGreaterThanOrEqual(OFFTRACK_FAR_M);
          const out = besideStation(track, i, side, lim + 5);
          const eo = edge(out[0], out[1]);
          if (eo.d <= lim + 1 || eo.side !== side || Math.abs(eo.seg - e.seg) > 2) continue;   // folds back toward the lap
          expect(judge.far(out[0], out[1])).toBe(true);
          checked++;
        }
      }
      expect(checked).toBeGreaterThan(20);
      const h = track.heightfield;
      expect(judge.far(h.x0 - 50, h.y0 - 50)).toBe(true);   // beyond the modelled terrain
    });
    it(`${id}: every containment barrier stands inside the limit (a runoff ends at its wall, never "far")`, () => {
      for (const b of scenery.barriers ?? []) {
        if (!['armco', 'concrete', 'tyres'].includes(b.kind)) continue;
        for (const p of b.pts) {
          const e = edge(p[0], p[1]);
          expect(e.d).toBeLessThanOrEqual(judge.limit(e.seg, e.side) - OFFTRACK_BARRIER_MARGIN_M + 1e-9);
        }
      }
    });
  }
});

describe('lost in the hills: the launch (HotlapSim, Laguna)', () => {
  const assets = lagunaAssets();
  const idle = () => ({ steer: 0, throttle: 0, brake: 1 });
  const stepFor = (sim: HotlapSim, s: number) => { for (let k = 0; k < Math.round(s / 0.001); k++) sim.step(idle); };
  const { track } = assets;
  const judge = createOffTrackJudge(track, { barriers: assets.scenery?.barriers });
  const edge = createEdgeDistance(track);
  // a far point and a runoff point beside the same straight-ish station
  let farPt: [number, number] = [0, 0], nearPt: [number, number] = [0, 0];
  for (let i = 0; i < track.n; i += 7) {
    const f = besideStation(track, i, 1, judge.limit(i, 1) + 20), n = besideStation(track, i, 1, 20);
    const ef = edge(f[0], f[1]);
    if (ef.side === 1 && Math.abs(ef.seg - i) <= 2 && judge.far(f[0], f[1]) && !judge.far(n[0], n[1])) { farPt = f; nearPt = n; break; }
  }
  const put = (sim: HotlapSim, p: [number, number]) => {
    sim.vehicle.reset([p[0], p[1], sim.surface.sample(p[0], p[1]).z], 0, 0);
  };

  it('finds a far point and a runoff point beside the same station', () => {
    expect(judge.far(farPt[0], farPt[1])).toBe(true);
    expect(judge.far(nearPt[0], nearPt[1])).toBe(false);
    expect(edge(nearPt[0], nearPt[1]).d).toBeGreaterThan(15);   // well off the road, all four wheels on the dirt
  });
  it('beyond the band for OFFTRACK_HOLD_S: launched into space, with its own line', () => {
    const sim = new HotlapSim(assets);
    put(sim, farPt);
    stepFor(sim, OFFTRACK_HOLD_S - 0.1);
    expect(sim.vehicle.state.launched).toBe(false);
    stepFor(sim, 0.2);
    expect(sim.vehicle.state.launched).toBe(true);
    expect(sim.launchedOffTrack).toBe(true);
    const z0 = sim.vehicle.state.pos[2];
    stepFor(sim, 1);
    expect(sim.vehicle.state.pos[2]).toBeGreaterThan(z0 + 30);   // the same sequence as the wall: up, fast
    sim.reset();
    expect(sim.launchedOffTrack).toBe(false);
    expect(LOST_IN_HILLS_LINE).toBe('You got lost in the hills, so the tow truck sent you home the fast way.');
  });
  it('inside the band (a wide runoff excursion): no launch', () => {
    const sim = new HotlapSim(assets);
    put(sim, nearPt);
    stepFor(sim, 4);
    expect(sim.vehicle.state.launched).toBe(false);
  });
  it('a brief excursion beyond it: no launch', () => {
    const sim = new HotlapSim(assets);
    put(sim, farPt);
    stepFor(sim, 1.5);
    put(sim, nearPt);   // back inside the band
    stepFor(sim, 0.5);
    put(sim, farPt);
    stepFor(sim, 1.5);
    expect(sim.vehicle.state.launched).toBe(false);
  });
  it('AI cars are unaffected: a Vehicle stepped outside HotlapSim (as the race director steps the field) stays down', () => {
    const sim = new HotlapSim(assets);
    const v = new Vehicle(sim.spec);
    v.reset([farPt[0], farPt[1], sim.surface.sample(farPt[0], farPt[1]).z], 0, 0);
    for (let k = 0; k < 4000; k++) v.step({ steer: 0, throttle: 0, brake: 1, shiftUp: false, shiftDown: false, handbrake: false }, sim.surface, 0.001);
    expect(v.state.launched).toBe(false);
  });
});
