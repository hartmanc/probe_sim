// A line-following autopilot for the determinism proofs (docs/determinism.md): the test fixture's pure pursuit on the
// ghosts' racing line (src/scoreboard/__tests__/fixtures.ts autopilot), with a curvature speed profile for a track whose
// ghosts.json has no real lap (Sonoma). Reads only the sim's state, so it drives a HotlapSim in Node or the game's
// HotlapSim in a browser page (window.__sim.hotlap). Its own maths (Math.*) is engine-specific on purpose: whatever it
// commands is quantised and recorded in the trace, and the replay must reproduce that trace bit for bit.
import { lineToWorld } from '../../src/physics/track';
import type { HotlapSim, RawInput } from '../../src/scoreboard/sim';

export function autopilot(sim: HotlapSim, pace = 0.85): () => RawInput {
  const a = sim.assets, track = a.track, g = a.ghosts, L = track.length_m;
  const off = g.line?.offset_m ?? [], grid = g.s_grid_m || 2;
  const at = (arr: ArrayLike<number>, s: number) => {
    const u = (((s % L) + L) % L) / grid, i = Math.floor(u), t = u - i;
    return arr[i % arr.length] * (1 - t) + arr[(i + 1) % arr.length] * t;
  };
  const offsetAt = (s: number) => (off.length ? at(off, s) : 0);
  const ref = [...g.laps].filter((l) => l.kind === 'real').sort((x, y) => (x.lap_time_s ?? 0) - (y.lap_time_s ?? 0))[0];
  let vRef: ArrayLike<number>;
  if (ref) vRef = ref.v_mps;
  else {
    // curvature-limited speed on the racing line (0.85 g), smoothed over +-10 m
    const n = Math.ceil(L / grid), raw = new Float64Array(n), sm = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const h0 = lineToWorld(track, offsetAt, (i * grid - 4 + L) % L).heading, h1 = lineToWorld(track, offsetAt, (i * grid + 4) % L).heading;
      let dh = h1 - h0; while (dh > Math.PI) dh -= 2 * Math.PI; while (dh < -Math.PI) dh += 2 * Math.PI;
      const k = Math.abs(dh) / 8;
      raw[i] = Math.min(58, Math.sqrt(8.3 / Math.max(k, 1e-4)));
    }
    const w = Math.round(10 / grid);
    for (let i = 0; i < n; i++) { let m = Infinity; for (let d = -w; d <= w; d++) m = Math.min(m, raw[(i + d + n) % n]); sm[i] = m; }
    vRef = sm;
  }
  const vAt = (s: number) => pace * at(vRef, s);
  const spec = sim.spec, wb = spec.wheelbase, st = spec.steering;
  let integ = 0;
  return () => {
    const s0 = sim.vehicle.state;
    const [qx, qy, qz, qw] = s0.quat;
    const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const s = sim.projector.project(s0.pos[0], s0.pos[1]).s;
    const v = Math.max(1, s0.speed);
    const rx = s0.pos[0] - cy * wb / 2, ry = s0.pos[1] - sy * wb / 2;
    const Ld = 4 + 0.45 * v;
    const [tx, ty] = lineToWorld(track, offsetAt, s - wb / 2 + Ld).pos;
    const dx = tx - rx, dy = ty - ry;
    const ang = Math.atan2(-sy * dx + cy * dy, cy * dx + sy * dy);
    const k = (2 * Math.sin(ang)) / Math.hypot(dx, dy);
    let delta = Math.atan(wb * k) + 0.15 * (v * k - s0.angVel[2]);
    delta += (2.3 * Math.PI / 180) * Math.max(-1.3, Math.min(1.3, (v * v * k) / 9.81));
    const vr = v / st.shapingSpeed;
    const maxA = Math.max(st.minAngleDeg, st.maxAngleDeg / (1 + vr * vr));
    const steer = Math.max(-1, Math.min(1, (delta * 180 / Math.PI) / maxA));
    let target = Infinity;
    for (let d = 0; d <= 160; d += 8) {
      const vd = vAt(s + d);
      target = Math.min(target, Math.sqrt(vd * vd + 2 * 7.5 * d));
    }
    const e = target - v;
    integ = Math.max(-2, Math.min(5, integ + e * 0.01));
    if (e < -1.5) return { steer, throttle: 0, brake: Math.min(1, -e * 0.25), handbrake: false };
    return { steer, throttle: Math.max(0, Math.min(1, 0.35 * e + 0.1 * integ + 0.45)), brake: 0, handbrake: false };
  };
}
