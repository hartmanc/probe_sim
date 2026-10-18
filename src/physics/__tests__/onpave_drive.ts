// A deterministic on-pavement drive on the real Laguna package (track + pit lane + paved runoff, as the app builds
// the surface), used to prove that the off-pavement surface model leaves on-pavement behaviour bit-identical.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createTrackProjector, createTrackSurface, lineToWorld, loadHeightfield, Vehicle, type PitLaneJson, type TrackJson } from '../index';
import { DT, input, probeSpec } from './helpers';

const dir = fileURLToPath(new URL('../../../public/tracks/laguna_seca/', import.meta.url));
const track = JSON.parse(readFileSync(dir + 'track.json', 'utf8')) as TrackJson;
const hf = loadHeightfield(Uint8Array.from(readFileSync(dir + 'heightfield.bin')).buffer);
const scenery = JSON.parse(readFileSync(dir + 'scenery.json', 'utf8')) as { pit_lane: PitLaneJson; paved_zones?: PitLaneJson };
const pitLane: PitLaneJson = { ...scenery.pit_lane, parts: [...scenery.pit_lane.parts, ...(scenery.paved_zones?.parts ?? [])] };

/** Drive 9 s down the centre from s = 100 m with a pure-pursuit driver; returns the state trace every 0.5 s. */
export function onPavementDrive(): { trace: number[]; allPaved: boolean } {
  const surface = createTrackSurface(track, hf, { pitLane });
  const proj = createTrackProjector(track);
  const car = new Vehicle(probeSpec(), { autoShift: true });
  const centre = (s: number) => lineToWorld(track, () => 0, s);
  const p0 = centre(100);
  car.reset(p0.pos, p0.heading, 25);
  const inp = input({ throttle: 0.55 });
  const L = 2.614;
  const trace: number[] = [];
  let allPaved = true;
  for (let i = 1; i <= 9000; i++) {
    const st = car.state;
    const [qx, qy, qz, qw] = st.quat;
    const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    const s = proj.project(st.pos[0], st.pos[1]).s;
    const v = Math.max(1, st.speed);
    const t = centre(s + 4 + 0.5 * v).pos;
    const dx = t[0] - st.pos[0], dy = t[1] - st.pos[1];
    const a = Math.atan2(-Math.sin(yaw) * dx + Math.cos(yaw) * dy, Math.cos(yaw) * dx + Math.sin(yaw) * dy);
    const k = (2 * Math.sin(a)) / Math.hypot(dx, dy);
    inp.steer = Math.max(-1, Math.min(1, (Math.atan(L * k) / 0.3) * (1 + (v / 18) ** 2)));
    inp.throttle = v > 30 ? 0.1 : 0.55;
    car.step(inp, surface, DT);
    for (const w of car.state.wheels) if (!w.onTrack) allPaved = false;
    if (i % 500 === 0) {
      const c = car.state;
      trace.push(...c.pos, ...c.vel, ...c.quat, ...c.angVel, c.rpm, c.gear, ...c.wheels.flatMap((w) => [w.omega, w.load, w.slipUse]));
    }
  }
  return { trace, allPaved };
}
