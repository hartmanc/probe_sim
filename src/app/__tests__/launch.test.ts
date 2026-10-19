// Hot-lap auto-launch: LAUNCH_S of full throttle along the racing line, then the driver's input applies; the launch
// rows are ordinary trace rows (replayable), and the rolling start sits on the racing line 230 m before T11.
import { describe, expect, it } from 'vitest';
import { HotlapLoop } from '../modes/hotlap';
import { HotlapSim, canonicalReset } from '../../scoreboard';
import { lastCorner } from '../../scoreboard/sim';
import { LAUNCH_S, ROLLING_START_BEFORE_LAST_CORNER_M, ROLLING_START_SPEED } from '../../scoreboard/config';
import { lagunaAssets } from '../../scoreboard/__tests__/fixtures';

describe('hot-lap launch', () => {
  const assets = lagunaAssets();
  it('rolling start: 230 m before T11 on the racing line at the rolling speed', () => {
    // the start is derived from track.json (the last directed corner) since the multi-track registry; at Laguna that
    // is T11, so the canonical start is where it always was
    const t11 = assets.track.corners!.find((c) => /^T11\b/i.test(c.name))!;
    expect(lastCorner(assets.track)!.name).toBe(t11.name);
    const r = canonicalReset(assets.track, (s) => 1.5);
    const r0 = canonicalReset(assets.track);
    expect(r.speed).toBe(ROLLING_START_SPEED);
    expect(Math.hypot(r.pos[0] - r0.pos[0], r.pos[1] - r0.pos[1])).toBeCloseTo(1.5, 1);   // the lateral offset is honoured
    expect(ROLLING_START_BEFORE_LAST_CORNER_M).toBe(230);
    expect(t11.s).toBeGreaterThan(ROLLING_START_BEFORE_LAST_CORNER_M);
    // 230 m before T11 along the centre: the start lies within a metre of that station's centre point plus the offset
    const k = Math.round((t11.s - 230) / assets.track.spacing_m);
    const c = assets.track.center[k];
    expect(Math.hypot(r0.pos[0] - c[0], r0.pos[1] - c[1])).toBeLessThan(1.0);
  });
  it('drives itself at full throttle for LAUNCH_S, then hands over; the rows are in the trace', () => {
    const sim = new HotlapSim(assets, { autoShift: true, record: true });
    const loop = new HotlapLoop(sim, () => ({ steer: 0, throttle: 0, brake: 1, handbrake: false, tag: 'keys' as const }));
    loop.reset();
    sim.launchUntil = LAUNCH_S;
    const v0 = sim.vehicle.state.speed;
    loop.advance(LAUNCH_S);
    const vHand = sim.vehicle.state.speed;
    expect(vHand).toBeGreaterThan(v0 + 6);                               // accelerated hard
    for (const w of sim.vehicle.state.wheels) expect(w.onTrack).toBe(true); // and stayed on the road
    loop.advance(1.0);                                                    // the driver's brake now applies
    expect(sim.vehicle.state.speed).toBeLessThan(vHand - 3);
    const tr = sim.trace();
    expect(tr.rows[0][2]).toBe(1000);                                      // throttle 1.000 recorded from the first sample
    expect(tr.reset.speed).toBe(ROLLING_START_SPEED);
    // the schedule suspension is recorded as reference changes: null at the start, the ghost back after the launch
    expect(tr.ref[0]).toEqual([0, null]);
    expect(tr.ref.length).toBeGreaterThanOrEqual(2);
    expect(tr.ref[1][0]).toBeGreaterThanOrEqual(LAUNCH_S * 1000 - 10);
  });
  it('a race never launches (launchUntil 0 leaves the device input in charge)', () => {
    const sim = new HotlapSim(assets, { autoShift: true });
    const loop = new HotlapLoop(sim, () => ({ steer: 0, throttle: 0, brake: 1, handbrake: false, tag: 'keys' as const }));
    loop.reset();
    const v0 = sim.vehicle.state.speed;
    loop.advance(1.0);
    expect(sim.vehicle.state.speed).toBeLessThan(v0);
  });
});
