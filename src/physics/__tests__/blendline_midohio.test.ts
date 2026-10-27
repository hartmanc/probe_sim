// The Mid-Ohio package's pit-exit blend line (round 11): what it is, that the racing-line autopilot never trips it through
// the T1 exit, and that two wheels across it, with the lap started, invalidate the hot lap with the black-flag words.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { lineToWorld, loadHeightfield, type TrackJson } from '../index';
import { BlendLine, type BlendLineJson } from '../blendline';
import { HotlapSim, type GhostsLike, type RawInput, type SceneryLike, type SimAssets } from '../../scoreboard/sim';

const pub = fileURLToPath(new URL('../../../public/', import.meta.url));
const buf = (p: string): ArrayBuffer => Uint8Array.from(readFileSync(pub + p)).buffer;
const json = <T>(p: string): T => JSON.parse(readFileSync(pub + p, 'utf8')) as T;
const dir = 'tracks/mid_ohio/';
const track = json<TrackJson>(dir + 'track.json');
const scenery = json<SceneryLike & { blend_line: BlendLineJson & { s: [number, number]; src: string } }>(dir + 'scenery.json');
const assets = (): SimAssets => ({
  trackId: 'mid_ohio', carId: 'probe_gt', track, heightfield: loadHeightfield(buf(dir + 'heightfield.bin')), carJson: json<unknown>('cars/probe_gt/car.json'),
  scenery, farHeightfield: scenery.far?.heightfield?.file ? loadHeightfield(buf(dir + scenery.far.heightfield.file)) : null, ghosts: json<GhostsLike>(dir + 'ghosts.json'),
});
const L = track.length_m;

/** Pure pursuit on the package's racing line (the ghosts' offsets), speed from the line's curvature (0.75 g, 4 m/s2 out, 7.5 braking). */
function lineDriver(sim: HotlapSim, pace = 0.85): () => RawInput {
  const g = sim.assets.ghosts, off = g.line.offset_m, grid = g.s_grid_m;
  const at = (arr: number[], s: number) => { const u = (((s % L) + L) % L) / grid, i = Math.floor(u), t = u - i; return arr[i % arr.length] * (1 - t) + arr[(i + 1) % arr.length] * t; };
  const offsetAt = (s: number) => at(off, s);
  const n = Math.ceil(L / 2), v = new Float64Array(n);
  for (let k = 0; k < n; k++) {
    const a = lineToWorld(track, offsetAt, k * 2 - 4).pos, b = lineToWorld(track, offsetAt, k * 2).pos, c = lineToWorld(track, offsetAt, k * 2 + 4).pos;
    const cr = Math.abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]));
    const kap = (2 * cr) / (Math.hypot(b[0] - a[0], b[1] - a[1]) * Math.hypot(c[0] - b[0], c[1] - b[1]) * Math.hypot(c[0] - a[0], c[1] - a[1]) + 1e-9);
    v[k] = Math.min(50, Math.sqrt((0.75 * 9.81) / Math.max(kap, 1e-4))) * pace;
  }
  for (let pass = 0; pass < 2; pass++) {
    for (let k = n * 2 - 1; k >= 0; k--) { const a = k % n, b = (k + 1) % n; v[a] = Math.min(v[a], Math.sqrt(v[b] * v[b] + 2 * 7.5 * 2)); }
    for (let k = 0; k < n * 2; k++) { const a = k % n, b = (k + 1) % n; v[b] = Math.min(v[b], Math.sqrt(v[a] * v[a] + 2 * 4 * 2)); }
  }
  const vAt = (s: number) => v[Math.floor((((s % L) + L) % L) / 2) % n];
  const spec = sim.spec, wb = spec.wheelbase, st = spec.steering;
  let integ = 0;
  return () => {
    const s0 = sim.vehicle.state, [qx, qy, qz, qw] = s0.quat;
    const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz)), cy = Math.cos(yaw), sy = Math.sin(yaw);
    const s = sim.projector.project(s0.pos[0], s0.pos[1]).s, sp = Math.max(1, s0.speed);
    const rx = s0.pos[0] - cy * wb / 2, ry = s0.pos[1] - sy * wb / 2, Ld = 4 + 0.45 * sp;
    const [tx, ty] = lineToWorld(track, offsetAt, s - wb / 2 + Ld).pos;
    const dx = tx - rx, dy = ty - ry, ang = Math.atan2(-sy * dx + cy * dy, cy * dx + sy * dy), k = (2 * Math.sin(ang)) / Math.hypot(dx, dy);
    let delta = Math.atan(wb * k) + 0.15 * (sp * k - s0.angVel[2]);
    delta += (2.3 * Math.PI / 180) * Math.max(-1.3, Math.min(1.3, (sp * sp * k) / 9.81));
    const vr = sp / st.shapingSpeed, maxA = Math.max(st.minAngleDeg, st.maxAngleDeg / (1 + vr * vr));
    const steer = Math.max(-1, Math.min(1, (delta * 180 / Math.PI) / maxA));
    let target = Infinity;
    for (let d = 0; d <= 160; d += 8) target = Math.min(target, Math.sqrt(vAt(s + d) ** 2 + 2 * 7.5 * d));
    const e = target - sp;
    integ = Math.max(-2, Math.min(5, integ + e * 0.01));
    if (e < -1.5) return { steer, throttle: 0, brake: Math.min(1, -e * 0.25), handbrake: false };
    return { steer, throttle: Math.max(0, Math.min(1, 0.35 * e + 0.1 * integ + 0.45)), brake: 0, handbrake: false };
  };
}

describe('the Mid-Ohio blend line (scenery.json blend_line)', () => {
  const bl = scenery.blend_line, line = new BlendLine(bl);
  it('is declared: the T1 pit-exit ladder\'s inner line from the pit wall\'s end to the T1 inside kerb, pit exit on its left', () => {
    expect(bl.pit_side).toBe(1);
    expect(bl.label).toBe('crossed the blend line at T1');
    expect(bl.s[0]).toBeGreaterThan(205); expect(bl.s[0]).toBeLessThan(220);      // the pit wall ends at s 212
    expect(bl.s[1]).toBeGreaterThan(290); expect(bl.s[1]).toBeLessThan(300);      // the raised red / white kerb starts at s 299.2
    expect(line.length).toBeGreaterThan(70); expect(line.length).toBeLessThan(90);
    const kerb = (scenery.kerbs as { strips: { side: number; s0: number; kind?: string }[] }).strips.find((k) => k.side === 1 && k.s0 > 250 && k.s0 < 350)!;
    expect(bl.s[1]).toBeLessThanOrEqual(kerb.s0);
  });
  it('lies on the race edge: 0.05-0.15 m beyond the left edge along its whole length, and the pit lane is on its pit side', () => {
    const n = track.n, left = track.left, centre = track.center;
    for (let i = 0; i < bl.pts.length; i += 5) {
      const [x, y] = bl.pts[i] as [number, number];
      let b = 0, bd = Infinity;
      for (let k = Math.floor(bl.s[0]) - 5; k <= Math.ceil(bl.s[1]) + 5; k++) { const d = Math.hypot(x - centre[k][0], y - centre[k][1]); if (d < bd) { bd = d; b = k; } }
      const half = Math.hypot(left[b][0] - centre[b][0], left[b][1] - centre[b][1]);
      expect(bd - half).toBeGreaterThan(0.03); expect(bd - half).toBeLessThan(0.2);
      expect(b).toBeLessThan(n);
    }
    const pit = scenery.pit_lane!.parts[0], mid = pit.center[Math.floor(pit.center.length / 2)];
    const h = { x: 0, y: 0 };
    h.x = mid[0]; h.y = mid[1];
    // some lane centre point near the line is on the pit side
    const near = pit.center.filter((c) => Math.hypot(c[0] - bl.pts[40][0], c[1] - bl.pts[40][1]) < 14);
    expect(near.length).toBeGreaterThan(0);
    for (const c of near) expect(line.locate(c[0], c[1]).d * line.pitSide).toBeGreaterThan(0);
  });
  it.each([0.85, 1.0])('the racing-line autopilot (pace %s) drives the T1 exit and never trips it: every wheel stays on the course side, with a margin', { timeout: 120_000 }, (pace) => {
    const sim = new HotlapSim(assets());
    const drive = lineDriver(sim, pace);
    let minClear = Infinity, inBand = 0;
    for (let i = 0; i < 40_000; i++) {
      sim.step(drive);
      const s = sim.s;
      if (sim.timer.started && s > bl.s[0] - 10 && s < bl.s[1] + 10) {
        for (const w of sim.vehicle.state.wheels) {
          const h = line.locate(w.pos[0], w.pos[1]);
          if (h.band) { inBand++; minClear = Math.min(minClear, -h.d * line.pitSide); }
        }
      }
      if (sim.timer.started && s > bl.s[1] + 40 && s < L / 2) break;
    }
    expect(sim.timer.started).toBe(true);
    expect(inBand).toBeGreaterThan(100);                                  // it did pass the band
    expect(sim.blendFlags).toBe(0);
    expect(sim.timer.currentValid).toBe(true);
    console.log(`autopilot pace ${pace} through the band: minimum wheel clearance to the blend line ${minClear.toFixed(2)} m, ${inBand} wheel samples`);
    expect(minClear).toBeGreaterThan(0);
  });
  it('two wheels across it on the lap: the hot lap is invalid, with the flag\'s words', { timeout: 120_000 }, () => {
    const sim = new HotlapSim(assets());
    const drive = lineDriver(sim);
    for (let i = 0; i < 40_000 && !sim.timer.started; i++) sim.step(drive);
    expect(sim.timer.started).toBe(true);
    const place = (s: number, lat: number) => {
      const p = lineToWorld(track, () => lat, s);
      sim.vehicle.reset([p.pos[0], p.pos[1], sim.surface.sample(p.pos[0], p.pos[1]).z], p.heading, 5);
    };
    const hold = () => ({ steer: 0, throttle: 0, brake: 1, handbrake: false });
    const half = (s: number) => Math.hypot(track.left[s][0] - track.center[s][0], track.left[s][1] - track.center[s][1]);
    const s = 250;
    place(s - 12, half(s - 12) - 2.0);                                   // on the course, 2 m inside the left edge
    for (let i = 0; i < 400; i++) sim.step(hold);
    expect(sim.blendFlags).toBe(0); expect(sim.timer.currentValid).toBe(true);
    place(s, half(s) + 0.3);                                             // the centre 0.2 m beyond the line: the left wheels across, the right not
    for (let i = 0; i < 400; i++) sim.step(hold);
    expect(sim.blendFlags).toBe(1);
    expect(sim.lastBlendReason).toBe('crossed the blend line at T1');
    expect(sim.timer.currentValid).toBe(false);
  });
});
