// Joint engine-torque-scale / CdA check on the two long full-throttle straights.
//
//   npx tsx tools/calibrate/fit_power.ts [--torque-scale 1.0] [--cd 0.5] [--area 2.25] [--grid]
//
// For each straight (front: T11 exit -> T2 braking point; Rahal: T6 exit -> Corkscrew braking point)
// the start/end s are taken from the driver A ghost (speed minimum after the corner, maximum before the
// braking zone). The car starts on the ghost racing line at the ghost's speed and runs full throttle
// with the car.json autoShift (upshift 5000 rpm like the drivers, kickdown on), steering by pure pursuit,
// over the real surface (real grade). Prints the speed gain vs driver A and optimal.
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTrackProjector, createTrackSurface, lineToWorld, loadCarSpec, loadHeightfield, Vehicle } from '../../src/physics';
import type { TrackJson } from '../../src/physics';
import { TRACKS, DEFAULT_TRACK } from '../../src/scoreboard/config';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const argv = process.argv.slice(2);
const arg = (k: string, d: number) => { const i = argv.indexOf(k); return i >= 0 ? Number(argv[i + 1]) : d; };
const TD = resolve(ROOT, 'public', TRACKS[DEFAULT_TRACK].dir);
const track = JSON.parse(readFileSync(TD + '/track.json', 'utf8')) as TrackJson;
const hf = loadHeightfield(Uint8Array.from(readFileSync(TD + '/heightfield.bin')).buffer);
const ghosts = JSON.parse(readFileSync(TD + '/ghosts.json', 'utf8'));
const surface = createTrackSurface(track, hf);
const projector = createTrackProjector(track);
const grid: number = ghosts.s_grid_m;
const off: number[] = ghosts.line.offset_m;
const L = track.length_m;
const offsetAt = (s: number) => { const u = (((s % L) + L) % L) / grid, i = Math.floor(u), t = u - i; return off[i % off.length] * (1 - t) + off[(i + 1) % off.length] * t; };
const lap = (id: string) => ghosts.laps.find((l: any) => l.id === id) ?? ghosts.laps.find((l: any) => l.kind === id);
const driver_a = lap('driver_a_best'), optimal = lap('optimal');
const vAt = (g: any, s: number) => { const u = (((s % L) + L) % L) / grid, i = Math.floor(u), t = u - i; const v = g.v_mps; return v[i % v.length] * (1 - t) + v[(i + 1) % v.length] * t; };
const cornerS = (re: RegExp) => track.corners.find((c) => re.test(c.name))!.s;

// straight windows from driver A: min speed within [a, b], then max speed after it before the next braking
function window(a: number, b: number): { s0: number; s1: number } {
  let s0 = a, vmin = Infinity;
  for (let s = a; s <= a + 160; s += grid) { const v = vAt(driver_a, s); if (v < vmin) { vmin = v; s0 = s; } }
  let s1 = s0, vmax = 0;
  for (let s = s0; s <= b; s += grid) { const v = vAt(driver_a, s); if (v > vmax) { vmax = v; s1 = s; } }
  return { s0, s1 };
}
const STRAIGHTS = [
  { name: 'front (T11 -> T2)', ...window(cornerS(/^T11/), cornerS(/Andretti/) + L - 60) },
  { name: 'Rahal (T6 -> Corkscrew)', ...window(cornerS(/^T6/), cornerS(/Corkscrew/) - 60) },
];

function run(torqueScale: number, cd: number, area: number): { name: string; ghostE: number; ghostO: number; sim: number; v0: number }[] {
  const j = JSON.parse(readFileSync(resolve(ROOT, 'public/cars/probe_gt/car.json'), 'utf8'));
  j.engine.torqueCurve.torque = j.engine.torqueCurve.torque.map((t: number) => t * torqueScale);
  j.aero.cd = cd; j.aero.frontalArea = area;
  j.steering.shapingSpeed = 1e6; j.steering.rate = 100;
  const spec = loadCarSpec(j);
  // average over three start points (s0, s0+10, s0+20) so shift timing does not dominate the result
  return STRAIGHTS.map((st0) => {
    const rs = [0, 10, 20].map((d) => one({ ...st0, s0: st0.s0 + d }));
    const avg = (k: 'ghostE' | 'ghostO' | 'sim' | 'v0') => rs.reduce((a, r) => a + r[k], 0) / rs.length;
    return { name: st0.name, ghostE: avg('ghostE'), ghostO: avg('ghostO'), sim: avg('sim'), v0: avg('v0') };
  });
  function one(st: { name: string; s0: number; s1: number }) {
    const car = new Vehicle(spec, { autoShift: true });
    const p = lineToWorld(track, offsetAt, st.s0);
    const v0 = vAt(driver_a, st.s0);
    car.reset(p.pos, p.heading, v0);
    const span = ((st.s1 - st.s0) % L + L) % L;
    let travelled = 0, sPrev = st.s0;
    for (let i = 0; i < 60000 && travelled < span; i++) {
      const s = car.state;
      const [qx, qy, qz, qw] = s.quat;
      const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
      const sNow = projector.project(s.pos[0], s.pos[1]).s;
      let ds = sNow - sPrev; if (ds < -L / 2) ds += L; travelled += ds; sPrev = sNow;
      const v = Math.max(1, s.speed), Ld = 4 + 0.45 * v;
      const rx = s.pos[0] - Math.cos(yaw) * spec.wheelbase / 2, ry = s.pos[1] - Math.sin(yaw) * spec.wheelbase / 2;
      const t = lineToWorld(track, offsetAt, sNow - spec.wheelbase / 2 + Ld).pos;
      const dx = t[0] - rx, dy = t[1] - ry;
      const a = Math.atan2(-Math.sin(yaw) * dx + Math.cos(yaw) * dy, Math.cos(yaw) * dx + Math.sin(yaw) * dy);
      const k = 2 * Math.sin(a) / Math.hypot(dx, dy);
      const delta = Math.atan(spec.wheelbase * k) + 0.15 * (v * k - s.angVel[2]) + (2.3 * Math.PI / 180) * (v * v * k / 9.81);
      car.step({ steer: Math.max(-1, Math.min(1, delta / (spec.steering.maxAngleDeg * Math.PI / 180))), throttle: 1, brake: 0, shiftUp: false, shiftDown: false }, surface, 0.001);
    }
    return { name: st.name, ghostE: (vAt(driver_a, st.s1) - v0) * 3.6, ghostO: (vAt(optimal, st.s1) - vAt(optimal, st.s0)) * 3.6, sim: (car.state.speed - v0) * 3.6, v0: v0 * 3.6 };
  }
}

const fmt = (r: ReturnType<typeof run>) => r.map((x) => `${x.name}: from ${x.v0.toFixed(0)} km/h gain driver A ${x.ghostE.toFixed(1)} optimal ${x.ghostO.toFixed(1)} sim ${x.sim.toFixed(1)} (${(x.sim - x.ghostE >= 0 ? '+' : '') + (x.sim - x.ghostE).toFixed(1)})`).join('\n');
for (const st of STRAIGHTS) {
  const rise = lineToWorld(track, offsetAt, st.s1).pos[2] - lineToWorld(track, offsetAt, st.s0).pos[2];
  console.log(`${st.name}: s ${st.s0.toFixed(0)} -> ${st.s1.toFixed(0)}, rise ${rise.toFixed(1)} m`);
}
if (argv.includes('--grid')) {
  for (const ts of [1.0, 1.05, 1.1]) for (const cd of [0.4, 0.43, 0.46, 0.5]) {
    const r = run(ts, cd, arg('--area', 2.25));
    const err = Math.hypot(...r.map((x) => x.sim - 0.5 * (x.ghostE + x.ghostO)));
    console.log(`torque x${ts.toFixed(2)} Cd ${cd.toFixed(2)}: ` + r.map((x) => `${x.name.split(' ')[0]} ${x.sim.toFixed(1)}/${x.ghostE.toFixed(1)}`).join('  ') + `  (optimal ${r.map((x) => x.ghostO.toFixed(1)).join('/')})  rms err vs ghost mean ${(err / Math.SQRT2).toFixed(1)}`);
  }
} else {
  console.log(fmt(run(arg('--torque-scale', 1), arg('--cd', 0.5), arg('--area', 2.25))));
}
