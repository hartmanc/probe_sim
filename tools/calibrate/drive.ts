// Autopilot calibration driver: runs the real physics at 1 kHz on a track package (--track <dir>, default Laguna Seca),
// following the ghost racing line, and compares the lap with the logger ghosts.
//
//   npx tsx tools/calibrate/drive.ts [--car public/cars/probe_gt/car.json]
//       [--set aero.cd=0.45 --set tyre.lateral.mu0=1.2 ...] [--torque-scale 1.0]
//       [--alat 1.05] [--abrake 0.95] [--out tools/calibrate/out] [--json] [--quiet]
//
// See tools/calibrate/README.md.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { deriveGearSchedule, scheduleTargetAt } from '../../src/physics';
import {
  Vehicle, loadCarSpec, createTrackSurface, createTrackProjector, lineToWorld, loadHeightfield,
  type DriverInput, type TrackJson, type Surface,
} from '../../src/physics/index';
import { createFlatSurface } from '../../src/physics/devtrack';
import { TRACKS, DEFAULT_TRACK } from '../../src/scoreboard/config';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const G = 9.81;
const DT = 0.001;

// ------------------------------------------------------------------ args
interface Args {
  car: string; sets: [string, number][]; torqueScale: number;
  alat: number; abrake: number; out: string; track: string; bank: boolean; json: boolean; quiet: boolean; noFiles: boolean; keepShaping: boolean; upshift: number; learn: number; schedule: string;
  refGhosts: string;
}
function parseArgs(argv: string[]): Args {
  const a: Args = {
    car: 'public/cars/probe_gt/car.json', sets: [], torqueScale: 1, alat: 1.05, abrake: 0.95,
    out: 'tools/calibrate/out', track: 'public/' + TRACKS[DEFAULT_TRACK].dir.replace(/\/$/, ''), bank: false, json: false, quiet: false, noFiles: false, keepShaping: false, upshift: 5000, learn: 0, schedule: '',
    refGhosts: '',
  };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    const nxt = () => argv[++i];
    if (k === '--car') a.car = nxt();
    else if (k === '--set') { const [p, v] = nxt().split('='); a.sets.push([p, Number(v)]); }
    else if (k === '--torque-scale') a.torqueScale = Number(nxt());
    else if (k === '--alat') a.alat = Number(nxt());
    else if (k === '--abrake') a.abrake = Number(nxt());
    else if (k === '--out') a.out = nxt();
    else if (k === '--track') a.track = nxt();
    else if (k === '--bank') a.bank = true;
    else if (k === '--json') a.json = true;
    else if (k === '--quiet') a.quiet = true;
    else if (k === '--no-files') a.noFiles = true;
    else if (k === '--keep-shaping') a.keepShaping = true;
    else if (k === '--upshift') a.upshift = Number(nxt());
    else if (k === '--learn') a.learn = Number(nxt());
    else if (k === '--schedule') a.schedule = nxt();
    else if (k === '--ref-ghosts') a.refGhosts = nxt();
    else throw new Error(`unknown argument ${k}`);
  }
  return a;
}

function setPath(obj: any, path: string, v: number): void {
  const parts = path.split('.');
  let o = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (!(parts[i] in o)) throw new Error(`--set: no key ${parts.slice(0, i + 1).join('.')}`);
    o = o[parts[i]];
  }
  const last = parts[parts.length - 1];
  if (!(last in o)) throw new Error(`--set: no key ${path}`);
  o[last] = v;
}

const args = parseArgs(process.argv.slice(2));
const DEBUG = process.env.DRIVE_DEBUG ? process.env.DRIVE_DEBUG.split(',').map(Number) : null;
const log = (...x: unknown[]) => { if (!args.quiet) console.error(...x); };

// ------------------------------------------------------------------ data
const carJson = JSON.parse(readFileSync(resolve(ROOT, args.car), 'utf8'));
for (const [p, v] of args.sets) setPath(carJson, p, v);
if (args.torqueScale !== 1) carJson.engine.torqueCurve.torque = carJson.engine.torqueCurve.torque.map((t: number) => t * args.torqueScale);
const spec = loadCarSpec(carJson);
// The autopilot commands the road-wheel angle directly, like a real driver with a real steering
// wheel. The car.json speed-dependent shaping is a gamepad aid that caps the road-wheel angle
// (4.8 deg at 116 km/h), less than some corners need at the limit, so it is bypassed here
// unless --keep-shaping is given. maxAngleDeg and the rate limit still apply.
// The drivers also short-shift: the ghost laps never exceed ~5450 rpm and upshift at about
// 4900-5200 rpm (engine preservation in an endurance race), while car.json's autoShift (the
// player's automatic box) revs to 6750. The autopilot shifts like the drivers (--upshift).
const driveJson = JSON.parse(JSON.stringify(carJson));
if (!args.keepShaping) driveJson.steering.shapingSpeed = 1e6;
if (args.upshift > 0) driveJson.drivetrain.autoShift.upshiftRpm = args.upshift;
const driveSpec = loadCarSpec(driveJson);

const TDIR = resolve(ROOT, args.track);
const track: TrackJson = JSON.parse(readFileSync(resolve(TDIR, 'track.json'), 'utf8'));
const hfBuf = readFileSync(resolve(TDIR, 'heightfield.bin'));
const heightfield = loadHeightfield(hfBuf.buffer.slice(hfBuf.byteOffset, hfBuf.byteOffset + hfBuf.byteLength));
const ghosts = JSON.parse(readFileSync(resolve(TDIR, 'ghosts.json'), 'utf8'));
const surface: Surface = createTrackSurface(track, heightfield);
const projector = createTrackProjector(track);
const LEN = track.length_m;
// 1 m samples of the line, s = i metres, over the whole lap (20 Oct 2026: was min(n, floor(length)), which left the last
// length - n metres unsampled on a package with spacing_m > 1, ~11 m of Sonoma's first build; lineToWorld takes metres)
const N = Math.floor(LEN);

const gridDs: number = ghosts.s_grid_m;
// --schedule <ghost id>: autoShift follows that ghost's gear schedule (deriveGearSchedule)
const SCHED = (() => {
  if (!args.schedule) return null;
  const lap = ghosts.laps.find((l: any) => l.id === args.schedule || l.id.startsWith(args.schedule));
  if (!lap) throw new Error(`--schedule: no ghost ${args.schedule}`);
  return deriveGearSchedule(spec, lap, ghosts.s_grid_m);
})();
const offs: number[] = ghosts.line.offset_m;
const NG = offs.length;
function offsetAt(s: number): number {
  let u = (((s % LEN) + LEN) % LEN) / gridDs;
  const i = Math.floor(u) % NG, j = (i + 1) % NG;
  u -= Math.floor(u);
  return offs[i] + u * (offs[j] - offs[i]);
}
const wrap = (s: number) => ((s % LEN) + LEN) % LEN;

// ------------------------------------------------------------------ racing line geometry (per 1 m centre station)
const LX = new Float64Array(N), LY = new Float64Array(N), LZ = new Float64Array(N);
for (let i = 0; i < N; i++) {
  const p = lineToWorld(track, offsetAt, i).pos;
  LX[i] = p[0]; LY[i] = p[1]; LZ[i] = p[2];
}
const DS = new Float64Array(N); // line arc length from i to i+1
for (let i = 0; i < N; i++) { const j = (i + 1) % N; DS[i] = Math.hypot(LX[j] - LX[i], LY[j] - LY[i], LZ[j] - LZ[i]); }
function smoothPeriodic(a: Float64Array, sigma: number): Float64Array {
  const r = Math.ceil(3 * sigma), w: number[] = [];
  let ws = 0;
  for (let k = -r; k <= r; k++) { const x = Math.exp(-0.5 * (k / sigma) ** 2); w.push(x); ws += x; }
  const out = new Float64Array(a.length);
  for (let i = 0; i < a.length; i++) {
    let acc = 0;
    for (let k = -r; k <= r; k++) acc += w[k + r] * a[(i + k + a.length) % a.length];
    out[i] = acc / ws;
  }
  return out;
}
// heading from central differences, curvature = dψ/ds, smoothed
const HEAD = new Float64Array(N);
for (let i = 0; i < N; i++) {
  const a = (i - 1 + N) % N, b = (i + 1) % N;
  HEAD[i] = Math.atan2(LY[b] - LY[a], LX[b] - LX[a]);
}
const kRaw = new Float64Array(N);
for (let i = 0; i < N; i++) {
  const a = (i - 1 + N) % N, b = (i + 1) % N;
  let dh = HEAD[b] - HEAD[a];
  while (dh > Math.PI) dh -= 2 * Math.PI;
  while (dh < -Math.PI) dh += 2 * Math.PI;
  kRaw[i] = dh / (DS[a] + DS[i]);
}
const CURV = smoothPeriodic(kRaw, 4);
const gradeRaw = new Float64Array(N);
for (let i = 0; i < N; i++) { const a = (i - 1 + N) % N, b = (i + 1) % N; gradeRaw[i] = (LZ[b] - LZ[a]) / (DS[a] + DS[i]); }
const GRADE = smoothPeriodic(gradeRaw, 3);
// road bank per station: median slope of the four inner cross-section segments (lidar profile),
// as tan(angle) with + = left side LOWER (helps a left-hander, CURV > 0)
const BANK = new Float64Array(N);
{
  const fr = track.profile.fractions;
  for (let i = 0; i < N; i++) {
    const st = Math.round(i / (track.spacing_m ?? 1)) % track.n;   // metre i -> station
    const c = track.center[st], l = track.left[st], r = track.right[st];
    const hl = Math.hypot(l[0] - c[0], l[1] - c[1]), hr = Math.hypot(r[0] - c[0], r[1] - c[1]);
    const lat = fr.map((f) => (f < 0 ? -f * hl : -f * hr)); // + left
    const z = track.profile.z[st];
    const sl: number[] = [];
    for (let k = 1; k < fr.length - 2; k++) sl.push((z[k + 1] - z[k]) / (lat[k + 1] - lat[k]));
    sl.sort((a, b) => a - b);
    BANK[i] = -0.5 * (sl[1] + sl[2]); // dz/dlat < 0 (left lower) -> positive
  }
}

// ------------------------------------------------------------------ empirical straight-line acceleration a(v) on flat ground
const flat = createFlatSurface();
const inp = (p: Partial<DriverInput> = {}): DriverInput => ({ steer: 0, throttle: 0, brake: 0, shiftUp: false, shiftDown: false, ...p });

const VB = 0.5, NVB = 160; // bins of 0.5 m/s up to 80 m/s
const ACC = new Float64Array(NVB);
let flatTopSpeed = 0;
{
  const car = new Vehicle(driveSpec, { autoShift: true });
  car.reset([0, 0, 0], 0, 2);
  const sums = new Float64Array(NVB), cnt = new Float64Array(NVB);
  const full = inp({ throttle: 1 });
  let vPrev = car.state.speed;
  const win = 50; // differentiate over 50 ms
  const hist: number[] = [];
  for (let k = 0; k < 200_000; k++) {
    car.step(full, flat, DT);
    hist.push(car.state.speed);
    if (hist.length > win) {
      const v0 = hist[hist.length - 1 - win], v1 = car.state.speed;
      const a = (v1 - v0) / (win * DT);
      const b = Math.floor(0.5 * (v0 + v1) / VB);
      if (b < NVB) { sums[b] += a; cnt[b]++; }
    }
    vPrev = car.state.speed;
  }
  flatTopSpeed = vPrev;
  // bin averages (include the shift dips: that is real time lost), then fill gaps
  let last = 0;
  for (let b = 0; b < NVB; b++) {
    if (cnt[b] > 0) { ACC[b] = sums[b] / cnt[b]; last = ACC[b]; } else ACC[b] = b * VB > flatTopSpeed ? Math.min(0, last) : last;
  }
}
function accAt(v: number): number {
  const u = Math.max(0, Math.min(NVB - 1.001, v / VB));
  const i = Math.floor(u);
  return ACC[i] + (u - i) * (ACC[i + 1] - ACC[i]);
}

// threshold braking on flat: best constant pedal from 100 km/h to 30 km/h
function brakeTest(pedal: number): { decel: number; locked: boolean } {
  const car = new Vehicle(driveSpec, { autoShift: true });
  car.reset([0, 0, 0], 0, 100 / 3.6);
  const b = inp({ brake: pedal });
  let t = 0, locked = false;
  while (car.state.speed > 30 / 3.6 && t < 10) {
    car.step(b, flat, DT); t += DT;
    for (const w of car.state.wheels) if (Math.abs(w.slipRatio) > 0.5) locked = true;
  }
  return { decel: (100 / 3.6 - car.state.speed) / t / G, locked };
}
let bestBrake = { pedal: 0, decel: 0, locked: false };
const brakeSweep: { pedal: number; decel: number; locked: boolean }[] = [];
for (let p = 0.3; p <= 1.0001; p += 0.05) {
  const r = brakeTest(p);
  brakeSweep.push({ pedal: +p.toFixed(2), ...r });
  if (r.decel > bestBrake.decel && !r.locked) bestBrake = { pedal: p, ...r };
}
const fullBrake = brakeSweep[brakeSweep.length - 1];
// pedal → decel gain in the linear range (pedal 0.3)
const brakeGain = brakeSweep[0].decel / 0.3;
log(`flat: top speed ${(flatTopSpeed * 3.6).toFixed(1)} km/h, threshold brake ${bestBrake.decel.toFixed(3)} g @ pedal ${bestBrake.pedal.toFixed(2)}, full pedal ${fullBrake.decel.toFixed(3)} g locked=${fullBrake.locked}`);

// ------------------------------------------------------------------ target speed profile
// alatAt[i]: lateral-grip budget (g) per station; uniform args.alat unless --learn adapts it per corner
const VMAX = 80;
const vProf = new Float64Array(N);
const alatAt = new Float64Array(N).fill(args.alat);
function buildProfile(): void {
  const vLat = new Float64Array(N);
  // with --bank the budget is the tyres' share: the road's banking toward the turn adds
  // a_c = g (mu + tb) / (1 - mu tb); without it the budget applies to v^2 k directly (flat-road assumption)
  const cap = (i: number) => {
    const mu = alatAt[i], tb = args.bank ? BANK[i] * Math.sign(CURV[i]) : 0;
    return (mu + tb) / Math.max(0.2, 1 - mu * tb);
  };
  for (let i = 0; i < N; i++) vLat[i] = Math.min(VMAX, Math.sqrt(cap(i) * G / Math.max(1e-6, Math.abs(CURV[i]))));
  const latUse = (v: number, i: number) => Math.min(1, (v * v * Math.abs(CURV[i])) / (cap(i) * G));
  const ell = (v: number, i: number) => Math.sqrt(Math.max(0, 1 - latUse(v, i) ** 2));
  vProf.set(vLat);
  for (let pass = 0; pass < 3; pass++) {
    // forward (acceleration) pass
    for (let k = 0; k < 2 * N; k++) {
      const i = k % N, j = (i + 1) % N;
      const v = vProf[i];
      const a = Math.max(0, accAt(v)) * ell(v, i) - G * GRADE[i];
      const vn = Math.sqrt(Math.max(0, v * v + 2 * a * DS[i]));
      if (vn < vProf[j]) vProf[j] = vn;
    }
    // backward (braking) pass
    for (let k = 2 * N; k > 0; k--) {
      const j = k % N, i = (j - 1 + N) % N;
      const v = vProf[j];
      const d = args.abrake * G * ell(v, j) + G * GRADE[i];
      const vp = Math.sqrt(Math.max(0, v * v + 2 * Math.max(0.5, d) * DS[i]));
      if (vp < vProf[i]) vProf[i] = vp;
    }
  }
}
buildProfile();
function profAt(s: number): number {
  const u = wrap(s), i = Math.floor(u) % N, j = (i + 1) % N, f = u - Math.floor(u);
  return vProf[i] + f * (vProf[j] - vProf[i]);
}
function linePt(s: number): [number, number] {
  const u = wrap(s), i = Math.floor(u) % N, j = (i + 1) % N, f = u - Math.floor(u);
  return [LX[i] + f * (LX[j] - LX[i]), LY[i] + f * (LY[j] - LY[i])];
}

// ------------------------------------------------------------------ autopilot
const car = new Vehicle(driveSpec, { autoShift: true });
const L = spec.wheelbase;
const maxSteerRad = (v: number) => Math.max(driveSpec.steering.minAngleDeg, driveSpec.steering.maxAngleDeg / (1 + (v / driveSpec.steering.shapingSpeed) ** 2)) * Math.PI / 180;

// understeer feed-forward: a driver adds steer in proportion to the lateral g for an understeering car
// (compliance steer, load transfer). Measured on the flat: K = (δ − L·r/u) / a_y at ~0.7 g, 25 m/s.
const K_US = (() => {
  if (process.env.DRIVE_NOFF) return 0;
  const u0 = 25, L = spec.wheelbase;
  const delta = 0.0035 + (L * 0.7 * G) / (u0 * u0); // a little above the kinematic angle for 0.7 g
  const car = new Vehicle(driveSpec, { autoShift: true });
  car.reset([0, 0, 0], 0, u0);
  let integ = 0, a = 0, k = 0;
  for (let i = 0; i < 6000; i++) {
    const e = u0 - car.state.speed;
    integ = Math.max(-2, Math.min(5, integ + e * DT));
    const thr = Math.max(0, Math.min(1, 0.25 * e + 0.08 * integ + 0.25));
    car.step(inp({ steer: Math.min(1, delta / maxSteerRad(car.state.speed)), throttle: thr }), flat, DT);
    if (i > 4000) { a += car.state.speed * car.state.angVel[2] / G; k += car.state.angVel[2] / car.state.speed; }
  }
  a /= 2000; k /= 2000;
  const K = a > 0.1 ? Math.max(0, (delta - L * k) / a) : 0;
  log(`understeer: ${(K * 180 / Math.PI).toFixed(2)} deg/g at ${a.toFixed(2)} g (feed-forward)`);
  return K;
})();const coastDecel = (v: number) => (0.5 * spec.aero.airDensity * spec.aero.cd * spec.aero.frontalArea * v * v) / spec.mass / G + spec.rollingResistance + 0.02;

// start: rolling, on the line, a bit before start/finish so the timed lap starts at speed
const START_S = LEN - 350;

interface Row { s: number; t: number; v: number; vref: number; rpm: number; gear: number; throttle: number; brake: number; steer: number; gLat: number; gLong: number; latErr: number; onTrack: boolean }
interface LapResult { rows: Row[]; lapTime: number; lapsDone: number; maxLatErr: number; offTrackSteps: number; spun: boolean }

function runLap(): LapResult {
{
  const p = lineToWorld(track, offsetAt, START_S);
  car.reset(p.pos, p.heading, Math.min(profAt(START_S), 30));
}
const rows: Row[] = [];
let integ = 0;
let t = 0;
let sPrev = START_S;
let lapStart = -1, lapTime = -1, lapsDone = 0;
let nextGrid = 0;
let maxLatErr = 0, offTrackSteps = 0, spun = false;
let steer = 0;
let brakeCap = 1, thrCap = 1;
const TMAX = 400;
const KR = Number(process.env.DRIVE_KR ?? 0.25);
const LD0 = Number(process.env.DRIVE_LD0 ?? 3), LDK = Number(process.env.DRIVE_LDK ?? 0.25); // pure-pursuit look-ahead Ld = LD0 + LDK·v (m) // rad of road-wheel angle per rad/s of yaw-rate error
const halfWidth = (m: number) => { const i = Math.round(m / (track.spacing_m ?? 1)) % track.n; return 0.5 * Math.hypot(track.left[i][0] - track.right[i][0], track.left[i][1] - track.right[i][1]); };

while (t < TMAX) {
  const st = car.state;
  const v = Math.max(0, st.speed);
  const pr = projector.project(st.pos[0], st.pos[1]);
  const s = pr.s;
  // heading
  const [qx, qy, qz, qw] = st.quat;
  const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
  const cy = Math.cos(yaw), sy = Math.sin(yaw);

  // --- pure pursuit from the rear axle
  const rx = st.pos[0] - cy * L / 2, ry = st.pos[1] - sy * L / 2;
  const Ld = LD0 + LDK * v;
  const [tx, ty] = linePt(s - L / 2 + Ld);
  const dx = tx - rx, dy = ty - ry;
  const alpha = Math.atan2(-sy * dx + cy * dy, cy * dx + sy * dy);
  const dist = Math.hypot(dx, dy);
  const kappaPP = 2 * Math.sin(alpha) / dist;
  // pure pursuit + yaw-rate feedback (catches slides before the position error builds up)
  let delta = Math.atan(L * kappaPP) + KR * (v * kappaPP - st.angVel[2]);
  delta += K_US * Math.max(-1.3, Math.min(1.3, (v * v * kappaPP) / G));
  // lateral error to the line (for logging and a small integral-free correction)
  const latErr = pr.lateral - offsetAt(s);
  steer = Math.max(-1, Math.min(1, delta / maxSteerRad(v)));

  // --- speed control: feedforward of the profile slope at a short preview + PI on speed error
  const sp = s + v * 0.12;
  const vref = profAt(sp);
  const v2 = profAt(sp + 2);
  const aref = (v2 * v2 - vref * vref) / 4; // m/s²
  const e = vref - v;
  const kp = 0.3, ki = 0.15; // g per m/s, g per m
  let u = aref / G + kp * e + ki * integ;
  let throttle = 0, brake = 0;
  if (u >= 0) {
    const amax = Math.max(0.03, accAt(v) / G + coastDecel(v));
    throttle = Math.min(1, (u + coastDecel(v)) / amax);
  } else {
    brake = Math.min(1, Math.max(0, (-u - coastDecel(v)) / brakeGain));
  }
  // driver pedal modulation: back off the brake when a wheel starts to lock and the
  // throttle when a front wheel spins up (a competent driver's feel, not an ABS/TC model)
  {
    let lock = 0, spin = 0;
    // only loaded wheels count: an unloaded inside rear locks at any pedal and carries no force anyway
    for (const w of st.wheels) { if (w.load > 1000 && -w.slipRatio > lock) lock = -w.slipRatio; }
    for (let i = 0; i < 2; i++) { const w = st.wheels[i]; if (w.load > 1000 && w.slipRatio > spin) spin = w.slipRatio; }
    const kpk = spec.tyre.longitudinal.peakSlipRatio;
    brakeCap = lock > 1.5 * kpk ? Math.max(0.25, Math.min(brakeCap, brake) - 3 * DT) : Math.min(1, brakeCap + 3 * DT);
    thrCap = spin > 1.5 * kpk ? Math.max(0.2, Math.min(thrCap, throttle) - 3 * DT) : Math.min(1, thrCap + 3 * DT);
    brake = Math.min(brake, brakeCap);
    throttle = Math.min(throttle, thrCap);
  }
  // anti-windup
  const sat = (throttle >= 1 && e > 0) || (brake >= 1 && e < 0);
  if (!sat) integ = Math.max(-0.5, Math.min(0.5, integ + e * DT));

  if (DEBUG && lapStart >= 0 && s > DEBUG[0] && s < DEBUG[1] && Math.round(t * 1000) % 20 === 0) {
    const w = st.wheels;
    console.error(`aref ${(aref / G).toFixed(2)} I ${(ki * integ).toFixed(2)} bg ${brakeGain.toFixed(2)} s ${s.toFixed(1)} v ${(v * 3.6).toFixed(1)} vref ${(vref * 3.6).toFixed(1)} thr ${throttle.toFixed(2)} brk ${brake.toFixed(2)} cap ${brakeCap.toFixed(2)} steer ${steer.toFixed(3)} delta ${(delta * 57.3).toFixed(2)} yawr ${st.angVel[2].toFixed(3)} lat ${latErr.toFixed(2)} gear ${st.gear} rpm ${st.rpm.toFixed(0)} kappa ${w.map((x) => x.slipRatio.toFixed(3)).join('/')} alpha ${w.map((x) => (x.slipAngle * 57.3).toFixed(1)).join('/')} Fz ${w.map((x) => x.load.toFixed(0)).join('/')}`);
  }
  if (SCHED) car.setScheduledGear(Math.abs(pr.lateral - offsetAt(s)) < 15 ? scheduleTargetAt(SCHED, s) : 0);
  car.step({ steer, throttle, brake, shiftUp: false, shiftDown: false }, surface, DT);
  t += DT;

  // --- lap bookkeeping (crossing s = 0)
  const sNow = projector.project(car.state.pos[0], car.state.pos[1]).s;
  const crossed = sPrev > LEN - 100 && sNow < 100;
  if (crossed) {
    const ds0 = LEN - sPrev, ds1 = sNow;
    const tc = t - DT * ds1 / Math.max(1e-6, ds0 + ds1);
    if (lapStart >= 0) { lapTime = tc - lapStart; lapsDone++; break; }
    lapStart = tc; nextGrid = 0;
  }
  if (lapStart >= 0) {
    const cs = car.state;
    const absErr = Math.abs(latErr);
    if (absErr > maxLatErr) maxLatErr = absErr;
    let on = true;
    for (const w of cs.wheels) if (!w.onTrack) on = false;
    if (!on) offTrackSteps++;
    if (Math.abs(cs.angVel[2]) > 2.5 || cs.speed < 1) spun = true;
    while (nextGrid < LEN && sNow >= nextGrid && sNow < nextGrid + 50) {
      rows.push({ s: nextGrid, t: t - lapStart, v: cs.speed, vref, rpm: cs.rpm, gear: cs.gear, throttle, brake, steer, gLat: cs.gLat, gLong: cs.gLong, latErr, onTrack: on });
      nextGrid += gridDs;
    }
  }
  sPrev = sNow;
  if (spun) break;
}
return { rows, lapTime, lapsDone, maxLatErr, offTrackSteps, spun };
}

// --learn N: a few practice laps. Where the car ran more than LEARN_TOL off the line, lower the
// grip budget over the approach to that point; where a corner stayed within half of it, raise it.
// This is what a driver does in practice; it ends at the fastest lap that stays on the line.
const LEARN_TOL = 1.0;
let best: LapResult | null = null;
let bestAlat = new Float64Array(alatAt);
for (let it = 0; ; it++) {
  const r = runLap();
  const clean = r.lapsDone === 1 && !r.spun && r.maxLatErr <= LEARN_TOL;
  if (args.learn > 0) log(`learn ${it}: lap ${r.lapTime.toFixed(2)} s, max err ${r.maxLatErr.toFixed(2)} m${clean ? ' (clean)' : ''}`);
  const better = !best || (clean && (!(best.lapsDone === 1 && !best.spun && best.maxLatErr <= LEARN_TOL) || r.lapTime < best.lapTime))
    || (!clean && !(best.lapsDone === 1 && !best.spun && best.maxLatErr <= LEARN_TOL) && r.maxLatErr < best.maxLatErr);
  if (better) { best = r; bestAlat = new Float64Array(alatAt); }
  if (it >= args.learn) break;
  // per-station max error on this lap
  const err = new Float64Array(N);
  for (const row of r.rows) { const i0 = Math.round(row.s); for (let k = 0; k < gridDs; k++) err[(i0 + k) % N] = Math.max(err[(i0 + k) % N], Math.abs(row.latErr)); }
  if (r.rows.length === 0 || r.spun) { for (let i = 0; i < N; i++) alatAt[i] *= 0.97; buildProfile(); continue; }
  const adj = new Float64Array(N).fill(1.02);
  for (let i = 0; i < N; i++) {
    if (err[i] > LEARN_TOL) for (let k = -100; k <= 20; k++) adj[(i + k + N) % N] = Math.min(adj[(i + k + N) % N], 0.96);
    else if (err[i] > 0.5 * LEARN_TOL) for (let k = -100; k <= 20; k++) adj[(i + k + N) % N] = Math.min(adj[(i + k + N) % N], 1.0);
  }
  for (let i = 0; i < N; i++) alatAt[i] = Math.min(args.alat * 1.5, alatAt[i] * adj[i]);
  buildProfile();
}
alatAt.set(bestAlat); buildProfile();
const { rows, lapTime, lapsDone, maxLatErr, offTrackSteps, spun } = best!;

// ------------------------------------------------------------------ comparison
// Comparison laps: this package's ghosts, or --ref-ghosts <ghosts.json> of another package of the same circuit (a package
// built without logger laps has none), resampled onto this grid by the fraction of the lap. Without any, the sim lap
// stands in, so the tables compare the sim with itself and only the lap time and the sim column mean anything.
const refJson = args.refGhosts ? JSON.parse(readFileSync(resolve(ROOT, args.refGhosts), 'utf8')) : ghosts;
const lapsById: Record<string, any> = {};
for (const l of refJson.laps) {
  if (refJson === ghosts) { lapsById[l.id] = l; continue; }
  const m = l.t.length, out: any = { ...l, t: [], v_mps: [], rpm: [], throttle: [] };
  for (let i = 0; i < NG; i++) {
    const u = (i / NG) * m, a = Math.min(m - 1, Math.floor(u)), b = Math.min(m - 1, a + 1), f = u - Math.floor(u);
    for (const k of ['t', 'v_mps', 'rpm', 'throttle']) out[k].push(l[k][a] + f * (l[k][b] - l[k][a]));
  }
  lapsById[l.id] = out;
}
const kmhSim = Float64Array.from({ length: NG }, () => NaN);
for (const r of rows) kmhSim[Math.round(r.s / gridDs)] = r.v;
const simLap = { id: 'sim', lap_time_s: lapTime, v_mps: Array.from(kmhSim, (v, i) => (Number.isFinite(v) ? v : kmhSim[(i + NG - 1) % NG])),
  t: Array.from({ length: NG }, (_, i) => i), rpm: new Array(NG).fill(0), throttle: new Array(NG).fill(0) };
const noRef = !lapsById['driver_a_best'] || !lapsById['optimal'];

const driver_a = lapsById['driver_a_best'] ?? simLap, opt = lapsById['optimal'] ?? simLap;
const kmh = (x: number) => x * 3.6;
const simV = new Float64Array(NG).fill(NaN);
for (const r of rows) simV[Math.round(r.s / gridDs)] = r.v;

// Corner and straight windows from this package's own track.json corners (20 Oct 2026: they were Laguna's names and
// sectors moved by corner offsets, which skipped half of Sonoma's corners): every directed corner +-60 m, and every
// stretch from one corner's exit to 30 m before the next corner.
const trackCorners: { turn?: string | null; name?: string; s: number; dir?: string | null }[] =
  ((track as any).corners ?? []).filter((c: any) => c.dir).sort((x: any, y: any) => x.s - y.s);
const cname = (c: { turn?: string | null; name?: string }) => (c.name && c.name !== c.turn ? `${c.turn} ${c.name}` : String(c.turn ?? c.name)).slice(0, 17);
const CORNERS: [string, number, number][] = trackCorners.map((c) => [cname(c), c.s - 60, c.s + 60]);
function minIn(v: ArrayLike<number>, a: number, b: number): { v: number; s: number } {
  let best = Infinity, bs = 0;
  for (let i = Math.ceil(a / gridDs); i <= Math.floor(b / gridDs); i++) { const k = ((i % NG) + NG) % NG; if (v[k] < best) { best = v[k]; bs = k * gridDs; } }
  return { v: best, s: bs };
}
function maxIn(v: ArrayLike<number>, a: number, b: number): { v: number; s: number } {
  let best = -Infinity, bs = 0;
  for (let i = Math.ceil(a / gridDs); i <= Math.floor(b / gridDs); i++) { const k = ((i % NG) + NG) % NG; if (v[k] > best) { best = v[k]; bs = k * gridDs; } }
  return { v: best, s: bs };
}
const corners = CORNERS.map(([name, a, b]) => {
  const e = minIn(driver_a.v_mps, a, b), o = minIn(opt.v_mps, a, b), m = minIn(simV, a, b);
  return { name, driver_a: kmh(e.v), optimal: kmh(o.v), sim: kmh(m.v), simS: m.s, driver_aS: e.s,
    errDriverA: (m.v / e.v - 1) * 100, errOpt: (m.v / o.v - 1) * 100 };
});
// straights: from corner exit minimum to the max before the next braking point
const STRAIGHTS: [string, number, number, number, number][] = trackCorners.map((c, i) => {
  const nx = trackCorners[(i + 1) % trackCorners.length];
  const nxs = nx.s > c.s ? nx.s : nx.s + LEN;
  return [`${cname(c)} -> ${cname(nx)}`.slice(0, 29), c.s - 60, c.s + 60, c.s + 60, nxs - 30] as [string, number, number, number, number];
});
function straightOf(v: ArrayLike<number>, st: typeof STRAIGHTS[number]) {
  const lo = minIn(v, st[1], st[2]);
  const vv = Array.from(v);
  // front straight wraps: max window is on the next lap's s
  const hi = maxIn(vv, st[3], st[4]);
  return { vmin: kmh(lo.v), vmax: kmh(hi.v), gain: kmh(hi.v - lo.v), sMax: hi.s };
}
// Speed-matched acceleration check: over the speed range all three traces cover on a straight
// (from the highest exit minimum to the lowest pre-braking maximum), the distance each needs to
// gain it. Same speeds, so the same drag and gears; only power, drag and traction differ.
function distBetween(v: ArrayLike<number>, st: typeof STRAIGHTS[number], vlo: number, vhi: number): number {
  const i0 = Math.round(minIn(v, st[1], st[2]).s / gridDs);
  const i1 = Math.round(maxIn(v, st[3], st[4]).s / gridDs);
  const n = (i1 - i0 + NG) % NG;
  let sLo = NaN, sHi = NaN;
  for (let k = 0; k < n; k++) {
    const a = v[(i0 + k) % NG], b = v[(i0 + k + 1) % NG];
    if (Number.isNaN(sLo) && a < vlo && b >= vlo) sLo = (k + (vlo - a) / (b - a)) * gridDs;
    if (Number.isNaN(sHi) && a < vhi && b >= vhi) { sHi = (k + (vhi - a) / (b - a)) * gridDs; break; }
  }
  return sHi - sLo;
}
const straights = STRAIGHTS.map((st) => {
  const e = straightOf(driver_a.v_mps, st), o = straightOf(opt.v_mps, st), m = straightOf(simV, st);
  const vlo = Math.max(e.vmin, o.vmin, m.vmin) + 2, vhi = Math.min(e.vmax, o.vmax, m.vmax) - 2;
  const matched = vhi - vlo > 5 ? {
    vlo, vhi,
    driver_a: distBetween(driver_a.v_mps, st, vlo / 3.6, vhi / 3.6),
    optimal: distBetween(opt.v_mps, st, vlo / 3.6, vhi / 3.6),
    sim: distBetween(simV, st, vlo / 3.6, vhi / 3.6),
  } : null;
  return { name: st[0], driver_a: e, optimal: o, sim: m, matched };
});
// speed at s = 300 (front straight, logger max point)
const at = (v: ArrayLike<number>, s: number) => kmh(v[Math.round(s / gridDs)]);
const longest = STRAIGHTS.reduce((m, st) => (st[4] - st[3] > m[4] - m[3] ? st : m), STRAIGHTS[0]);
const front = { name: longest[0], driver_a: maxIn(driver_a.v_mps, longest[3], longest[4]).v * 3.6, optimal: maxIn(opt.v_mps, longest[3], longest[4]).v * 3.6,
  sim: maxIn(simV, longest[3], longest[4]).v * 3.6, driver_aMax: maxIn(driver_a.v_mps, longest[3], longest[4]), simMax: maxIn(simV, longest[3], longest[4]) };
void at;

// ghost braking rates (dv/dt smoothed over ±2 grid points)
function decelPeaks(l: any): { s: number; g: number }[] {
  const out: { s: number; g: number }[] = [];
  const v = l.v_mps, tt = l.t;
  const a: number[] = [];
  for (let i = 0; i < NG; i++) {
    const i0 = Math.max(0, i - 2), i1 = Math.min(NG - 1, i + 2);
    a.push((v[i1] - v[i0]) / (tt[i1] - tt[i0]) / G);
  }
  for (const [, , , , end] of STRAIGHTS) {
    // braking zone: from the straight's max to the next corner's min
    const st = STRAIGHTS.find((x) => x[4] === end)!;
    const sMax = maxIn(v, st[3], st[4]).s;
    let lo = 0, ls = 0;
    for (let i = sMax / gridDs; i < sMax / gridDs + 90 && i < NG; i++) if (a[i] < lo) { lo = a[i]; ls = i * gridDs; }
    out.push({ s: ls, g: -lo });
  }
  return out;
}
const brakingDriverA = decelPeaks(driver_a), brakingOpt = decelPeaks(opt);
const simPeakDecel = Math.max(0, ...rows.map((r) => -r.gLong));
const simPeakLat = Math.max(0, ...rows.map((r) => Math.abs(r.gLat)));

const summary = {
  car: args.car, sets: args.sets, torqueScale: args.torqueScale, alat: args.alat, abrake: args.abrake,
  complete: lapsDone === 1 && !spun, spun, lapTime, maxLatErr, offTrackSteps,
  flatTopSpeedKmh: kmh(flatTopSpeed), thresholdBrake: bestBrake, fullPedalBrake: fullBrake, brakeSweep,
  accTable: Array.from(ACC).map((a, i) => [i * VB + VB / 2, a]),
  front, corners, straights, brakingDriverA, brakingOpt, simPeakDecel, simPeakLat,
  profileLapTime: (() => { let tt = 0; for (let i = 0; i < N; i++) tt += DS[i] / Math.max(1, 0.5 * (vProf[i] + vProf[(i + 1) % N])); return tt; })(),
};

// ------------------------------------------------------------------ output
const fmt = (x: number, d = 1) => (Number.isFinite(x) ? x.toFixed(d) : 'nan');
if (!args.noFiles) {
  const outDir = resolve(ROOT, args.out);
  mkdirSync(outDir, { recursive: true });
  const hdr = 's,t,v_kmh,vref_kmh,rpm,gear,throttle,brake,steer,gLat,gLong,lat_err_m,on_track,driver_a_v_kmh,driver_a_t,driver_a_rpm,driver_a_throttle,optimal_v_kmh,optimal_t,line_curv,line_grade';
  const lines = [hdr];
  for (const r of rows) {
    const gi = Math.round(r.s / gridDs);
    lines.push([r.s, fmt(r.t, 3), fmt(kmh(r.v), 2), fmt(kmh(r.vref), 2), fmt(r.rpm, 0), r.gear, fmt(r.throttle, 3), fmt(r.brake, 3), fmt(r.steer, 4),
      fmt(r.gLat, 3), fmt(r.gLong, 3), fmt(r.latErr, 3), r.onTrack ? 1 : 0,
      fmt(kmh(driver_a.v_mps[gi]), 2), fmt(driver_a.t[gi], 3), fmt(driver_a.rpm[gi], 0), fmt(driver_a.throttle[gi], 3),
      fmt(kmh(opt.v_mps[gi]), 2), fmt(opt.t[gi], 3), fmt(CURV[Math.round(r.s) % N], 5), fmt(GRADE[Math.round(r.s) % N], 4)].join(','));
  }
  writeFileSync(resolve(outDir, 'sim_lap.csv'), lines.join('\n') + '\n');
  writeFileSync(resolve(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
  const prof = ['s,vprof_kmh,curv,grade'];
  for (let i = 0; i < N; i++) prof.push(`${i},${fmt(kmh(vProf[i]), 2)},${fmt(CURV[i], 5)},${fmt(GRADE[i], 4)}`);
  writeFileSync(resolve(outDir, 'target_profile.csv'), prof.join('\n') + '\n');
}

if (args.json) {
  console.log(JSON.stringify(summary));
} else {
  const mmss = (x: number) => `${Math.floor(x / 60)}:${(x % 60).toFixed(2).padStart(5, '0')}`;
  console.log(`lap: ${summary.complete ? 'complete' : 'INCOMPLETE'}  time ${lapTime > 0 ? mmss(lapTime) : '-'}  (profile ${mmss(summary.profileLapTime)}${noRef ? ', no reference laps' : `, driver A ${mmss(driver_a.lap_time_s)}, optimal ${mmss(opt.lap_time_s)}`})`);
  console.log(`line tracking: max |lateral error| ${fmt(maxLatErr, 2)} m, wheel-off-track steps ${offTrackSteps}`);
  if (noRef) {
    // no reference laps: the sim is not compared with itself (20 Oct 2026); sim-only tables
    console.log(`no reference laps (ghosts.json has none; --ref-ghosts <ghosts.json> of the same circuit gives them): sim only`);
    console.log(`longest straight (${front.name}): sim max ${fmt(front.sim)} km/h; flat-ground top speed ${fmt(summary.flatTopSpeedKmh)} km/h`);
    console.log('\ncorner minimum speeds (km/h), sim');
    for (const c of corners) console.log(`${c.name.padEnd(17)} ${fmt(c.sim).padStart(6)} at ${fmt(c.simS, 0)} m`);
    console.log('\nstraights: exit min -> max before braking (km/h), sim');
    for (const st of straights) console.log(`${st.name.padEnd(29)} ${fmt(st.sim.vmin, 0)}->${fmt(st.sim.vmax, 0)}`);
    console.log(`  sim: threshold (no lock) ${fmt(bestBrake.decel, 3)} g at pedal ${fmt(bestBrake.pedal, 2)}; peak decel in lap ${fmt(simPeakDecel, 2)} g; peak lateral ${fmt(simPeakLat, 2)} g`);
  } else {
  console.log(`longest straight (${front.name}): max sim ${fmt(front.sim)}  driver A ${fmt(front.driver_a)}  optimal ${fmt(front.optimal)} km/h; flat-ground top speed ${fmt(summary.flatTopSpeedKmh)} km/h`);
  console.log('\ncorner minimum speeds (km/h)');
  console.log('corner             driver A  optimal    sim   vs driver A  vs opt');
  for (const c of corners) console.log(`${c.name.padEnd(17)} ${fmt(c.driver_a).padStart(6)} ${fmt(c.optimal).padStart(8)} ${fmt(c.sim).padStart(6)} ${(fmt(c.errDriverA) + '%').padStart(9)} ${(fmt(c.errOpt) + '%').padStart(7)}`);
  console.log('\nstraights: exit min -> max before braking (km/h)');
  console.log('straight                      driver A            optimal          sim              gain E/O/sim');
  for (const s of straights) {
    const f = (x: any) => `${fmt(x.vmin, 0)}->${fmt(x.vmax, 0)}`.padEnd(16);
    console.log(`${s.name.padEnd(29)} ${f(s.driver_a)} ${f(s.optimal)} ${f(s.sim)} ${fmt(s.driver_a.gain, 0)}/${fmt(s.optimal.gain, 0)}/${fmt(s.sim.gain, 0)}`);
  }
  console.log('\nspeed-matched acceleration: metres needed to go from vlo to vhi (shorter = stronger)');
  console.log('straight                      vlo->vhi km/h   driver A  optimal    sim');
  for (const s of straights) {
    const m = s.matched;
    if (!m) { console.log(`${s.name.padEnd(29)} (no common range)`); continue; }
    console.log(`${s.name.padEnd(29)} ${(fmt(m.vlo, 0) + '->' + fmt(m.vhi, 0)).padEnd(14)} ${fmt(m.driver_a, 0).padStart(6)} ${fmt(m.optimal, 0).padStart(8)} ${fmt(m.sim, 0).padStart(6)}`);
  }
  console.log('\nbraking: ghost peak decel per zone (g), driver A / optimal');
  console.log('  ' + brakingDriverA.map((b, i) => `${b.s}:${fmt(b.g, 2)}/${fmt(brakingOpt[i].g, 2)}`).join('  '));
  console.log(`  sim: threshold (no lock) ${fmt(bestBrake.decel, 3)} g at pedal ${fmt(bestBrake.pedal, 2)}; full pedal ${fmt(fullBrake.decel, 3)} g locked=${fullBrake.locked}; peak decel in lap ${fmt(simPeakDecel, 2)} g; peak lateral ${fmt(simPeakLat, 2)} g`);
  }
}
