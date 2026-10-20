// Rollover propensity of the player's Probe on flat tarmac (no kerbs): NHTSA-style fishhook and J-turn at several
// speeds, and steady full-lock cornering on a negatively banked plane (the inside wheels raised, as on an apex kerb).
// Prints max roll angle (deg), two-wheel time (ms with both wheels of one side unloaded) and whether the car rolled.
//   npx tsx tools/physics/roll_flat.ts [--set path=value ...]
import { Vehicle, loadCarSpec, type Surface, type SurfaceSample } from '../../src/physics/index';
import { loadProbeJson } from '../race/load';

const argv = process.argv.slice(2);
const probe = loadProbeJson();
for (let i = 0; i < argv.length; i++) if (argv[i] === '--set') {
  const [p, v] = argv[++i].split('='); const ks = p.split('.'); let o = probe; for (const k of ks.slice(0, -1)) o = o[k]; o[ks[ks.length - 1]] = Number(v);
}
const DT = 0.001;
/** Plane z = gy·y (bank: y is lateral to the initial heading +x). */
function plane(gy: number): Surface {
  const l = Math.hypot(gy, 1);
  const out: SurfaceSample = { z: 0, nx: 0, ny: -gy / l, nz: 1 / l, onTrack: true, mu: 1, paved: true, dirt: 0, muPaved: 1 };
  return { sample(_x: number, y: number) { out.z = gy * y; return out; } };
}
function roll(q: number[]): number {
  const [x, y, z, w] = q;
  return Math.atan2(2 * (y * z + x * w), 1 - 2 * (x * x + y * y)) * 180 / Math.PI;
}
function run(v0: number, steerAt: (t: number) => number, surf: Surface, T = 4): { maxRoll: number; twoWheel: number; rolled: boolean } {
  const car = new Vehicle(loadCarSpec(probe), { autoShift: true });
  const n = (surf.sample(0, 0));
  car.reset([0, 0, 0], 0, v0, [n.nx, n.ny, n.nz]);
  const inp = { steer: 0, throttle: 0.0, brake: 0, shiftUp: false, shiftDown: false, handbrake: false };
  let maxRoll = 0, two = 0, rolled = false;
  for (let i = 0; i < T / DT; i++) {
    const t = i * DT;
    inp.steer = steerAt(t);
    inp.throttle = car.state.speed < v0 ? 0.6 : 0.2;
    car.step(inp, surf, DT);
    const r = Math.abs(roll(car.state.quat as unknown as number[]));
    if (r > maxRoll) maxRoll = r;
    if (r > 60) rolled = true;
    const w = car.state.wheels;
    if ((w[0].load <= 0 && w[2].load <= 0) || (w[1].load <= 0 && w[3].load <= 0)) two++;
  }
  return { maxRoll, twoWheel: two, rolled };
}
const ramp = (t: number, t0: number, rate: number) => Math.max(0, Math.min(1, (t - t0) * rate));
const flat = plane(0);
console.log('test            v m/s  maxRoll deg  twoWheel ms  rolled');
for (const v of [15, 20, 25, 30, 35]) {
  const fish = run(v, (t) => (t < 0.3 ? 0 : t < 0.8 ? ramp(t, 0.3, 4) : t < 1.1 ? 1 - 2 * ramp(t, 0.8, 4) : -1), flat);
  const j = run(v, (t) => ramp(t, 0.3, 6), flat);
  console.log(`fishhook flat   ${v.toString().padStart(5)}  ${fish.maxRoll.toFixed(1).padStart(10)}  ${fish.twoWheel.toString().padStart(10)}  ${fish.rolled}`);
  console.log(`J-turn flat     ${v.toString().padStart(5)}  ${j.maxRoll.toFixed(1).padStart(10)}  ${j.twoWheel.toString().padStart(10)}  ${j.rolled}`);
}
// steady full-lock left turn on a plane banked AWAY from the turn centre (inside raised): gy > 0 raises +y (left = inside)
for (const deg of [2, 4, 6, 8]) for (const v of [20, 30]) {
  const r = run(v, (t) => ramp(t, 0.3, 6), plane(Math.tan(deg * Math.PI / 180)));
  console.log(`J-turn bank -${deg}  ${v.toString().padStart(5)}  ${r.maxRoll.toFixed(1).padStart(10)}  ${r.twoWheel.toString().padStart(10)}  ${r.rolled}`);
}
