// What the physics does to engine rpm and the audio throttle through an upshift (round two, item 2: the "organ" note).
// Full throttle from rest on a flat surface with autoShift, the AI car's spec built exactly as the race does
// (buildAiSpec from public/cars/field/identity.json, pace scale 1), and the Probe. Prints and writes per-1 ms traces
// of rpm, throttleOut (what audio-field.ts / audio.ts are fed) and gear around each upshift.
//
//   npx tsx tools/audio/shift_trace.ts OUT.json [car number ...]     (default: 38 = modern_i4_stock, 41 = classic_v8_lowrev)
import { readFileSync, writeFileSync } from 'node:fs';
import { Vehicle, loadCarSpec, type CarSpec } from '../../src/physics/index';
import { createFlatSurface } from '../../src/physics/devtrack';
import { buildAiSpec, parseIdentity } from '../../src/physics/ai/field';

const out = process.argv[2] ?? 'shift_trace.json';
const nums = process.argv.length > 3 ? process.argv.slice(3) : ['38', '41'];
const probeJson = JSON.parse(readFileSync('public/cars/probe_gt/car.json', 'utf8'));
const ids = parseIdentity(JSON.parse(readFileSync('public/cars/field/identity.json', 'utf8')));

/** Mean |omega| of the driven wheels (rad/s): the gearbox input in gear is this x the overall ratio. */
function drivenOmega(w: { omega: number }[], layout: string): number {
  const a = Math.abs;
  return layout === 'fwd' ? 0.5 * (a(w[0].omega) + a(w[1].omega)) : layout === 'rwd' ? 0.5 * (a(w[2].omega) + a(w[3].omega))
    : 0.25 * (a(w[0].omega) + a(w[1].omega) + a(w[2].omega) + a(w[3].omega));
}

function trace(spec: CarSpec, T = 30) {
  const car = new Vehicle(spec, { autoShift: true });
  const flat = createFlatSurface();
  car.reset([0, 0, 0], 0);
  const dt = 0.001;
  const inp = { steer: 0, throttle: 1, brake: 0, shiftUp: false, shiftDown: false, handbrake: false };
  const t: number[] = [], rpm: number[] = [], thr: number[] = [], gear: number[] = [], box: number[] = [];
  const ratios = spec.drivetrain.gearRatios;
  for (let i = 0; i < T / dt; i++) {
    car.step(inp, flat, dt);
    const s = car.state;
    t.push(+((i + 1) * dt).toFixed(3)); rpm.push(+s.rpm.toFixed(1)); thr.push(+s.throttleOut.toFixed(3)); gear.push(s.gear);
    box.push(s.gear >= 1 ? +(drivenOmega(s.wheels, spec.drivetrain.layout) * ratios[s.gear - 1] * 60 / (2 * Math.PI)).toFixed(1) : s.rpm);
  }
  // upshifts: gear increments
  const shifts: { t: number; from: number; to: number; rpmBefore: number; rpmMin: number; tMin: number; rpmAfter200: number; cutS: number; dropS: number }[] = [];
  for (let i = 1; i < gear.length; i++) {
    if (gear[i] > gear[i - 1] && gear[i - 1] >= 1) {
      const i0 = i;
      let iMin = i0;
      for (let k = i0; k < Math.min(gear.length, i0 + 800); k++) if (rpm[k] < rpm[iMin]) iMin = k;
      let cut = 0; for (let k = i0; k < Math.min(gear.length, i0 + 800) && thr[k] < 0.5; k++) cut++;
      // time from the shift until rpm is within 2 % of its post-shift minimum
      let kd = i0; while (kd < iMin && rpm[kd] > rpm[iMin] * 1.02) kd++;
      shifts.push({ t: t[i0], from: gear[i - 1], to: gear[i], rpmBefore: rpm[i0 - 1], rpmMin: rpm[iMin], tMin: +(t[iMin] - t[i0]).toFixed(3),
        rpmAfter200: rpm[Math.min(rpm.length - 1, i0 + 200)], cutS: cut * dt, dropS: +((kd - i0) * dt).toFixed(3) });
    }
  }
  return { t, rpm, thr, gear, box, shifts, redline: spec.engine.revLimitRpm, idle: spec.engine.idleRpm, shiftTime: spec.drivetrain.shiftTime };
}

const res: Record<string, ReturnType<typeof trace> & { name: string }> = {};
res.probe = { name: 'Probe GT', ...trace(loadCarSpec(probeJson)) };
for (const n of nums) {
  const id = ids.get(n) ?? null;
  res[n] = { name: `${id?.make ?? ''} ${id?.model ?? ''}`, ...trace(buildAiSpec(probeJson, id, 1)) };
}
for (const [k, r] of Object.entries(res)) {
  console.log(`${k} ${r.name}: redline ${r.redline}, idle ${r.idle}, shiftTime ${r.shiftTime}`);
  for (const s of r.shifts.slice(0, 3)) {
    console.log(`  ${s.from}->${s.to} at ${s.t.toFixed(2)} s: ${s.rpmBefore.toFixed(0)} -> min ${s.rpmMin.toFixed(0)} after ${s.tMin} s ` +
      `(within 2 % of it after ${s.dropS} s), throttleOut cut ${s.cutS.toFixed(3)} s, rpm 0.2 s after ${s.rpmAfter200.toFixed(0)}`);
  }
}
writeFileSync(out, JSON.stringify(res));
