// A track built without logger laps (tools/track/build_track.py --no-logger) ships ghosts.json with the racing line only
// and `laps: []`. The sim, the scoreboard's reference-ghost logic and the AI's racing line must take it as it is.
import { describe, expect, it } from 'vitest';
import { HotlapSim, defaultRefGhost, type SimAssets } from '../sim';
import { RaceLine } from '../../physics/ai/line';
import { lagunaAssets } from './fixtures';

const lineOnly = (): SimAssets => {
  const a = lagunaAssets();
  return { ...a, ghosts: { ...a.ghosts, laps: [] } };
};

describe('ghosts.json with a racing line and no laps', () => {
  it('the hot-lap sim starts and drives on the line; no reference ghost', () => {
    const a = lineOnly();
    expect(defaultRefGhost(a.ghosts)).toBeNull();
    const sim = new HotlapSim(a, { autoShift: true, record: true });
    for (let i = 0; i < 2000; i++) sim.step(() => ({ steer: 0, throttle: 0.3, brake: 0, handbrake: false, tag: 'keys' }));
    expect(Number.isFinite(sim.vehicle.state.speed)).toBe(true);
    expect(sim.vehicle.state.speed).toBeGreaterThan(5);
  });
  it('the AI racing line finds the same corners from a curvature speed profile', () => {
    const a = lagunaAssets();
    const withLaps = new RaceLine(a.track as never, a.ghosts as never);
    const noLaps = new RaceLine(a.track as never, { ...a.ghosts, laps: [] } as never);
    expect(noLaps.ghostLap).toBeGreaterThan(100);
    expect(noLaps.ghostLap).toBeLessThan(160);
    expect(noLaps.corners.map((c) => c.name)).toEqual(withLaps.corners.map((c) => c.name));
    for (let i = 0; i < noLaps.corners.length; i++) expect(Math.abs(noLaps.corners[i].apex - withLaps.corners[i].apex)).toBeLessThan(40);
  });
});
