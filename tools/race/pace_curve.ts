// Per car, its solo lap against its pace scale (PaceCar.curve, AI round 1 Part B: the AI strength map, field.ts
// strengthPace), from calibrations that already exist: every fitted scale of the car (its own fit and each stint's) in the
// four pace-quantile files (tools/race/out/pace_q/<q>/<track>/pace.json, q = 0.5 / 0.35 / 0.25 / 0.15; 0.5 = the public
// file as it was) and, when present, the 110 % calibration (pace_q/s1.10/<track>/pace.json: every target / 1.10). Each fit is one measured point (scale, the solo lap the calibration ran at it). Points by rising scale,
// made monotone (lap never rising with the scale: pool-adjacent-violators in ln-ln), thinned to >= 1 % apart in scale.
// No new solo laps are run.
//
//   npx tsx tools/race/pace_curve.ts --track <id> [--out <pace.json>] [--dir tools/race/out/pace_q] [--dry]
//   (default --out: the track's public pace file; its fits and targets are not touched, only `curve` is written)
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { pacePath, trackArg, ROOT } from './load';
import type { PaceJson } from '../../src/physics/ai/field';

const QS = ['0.5', '0.35', '0.25', '0.15'];
const STRENGTH_DIRS = ['s1.10'];

/** Monotone (ln lap non-increasing in ln scale) curve through measured [scale, lap] points, thinned to >= `gap` apart in ln scale. */
export function fitCurve(points: [number, number][], gap = Math.log(1.01)): [number, number][] {
  const pts = points.filter(([s, t]) => s > 0 && t > 0 && t < 999 && Number.isFinite(s) && Number.isFinite(t))
    .map(([s, t]) => [Math.log(s), Math.log(t)] as [number, number]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  // pool adjacent violators: blocks of (sum x, sum y, count) with non-increasing mean y
  const blocks: { x: number; y: number; w: number }[] = [];
  for (const [x, y] of pts) {
    blocks.push({ x, y, w: 1 });
    while (blocks.length > 1) {
      const a = blocks[blocks.length - 2], b = blocks[blocks.length - 1];
      if (a.y / a.w >= b.y / b.w && a.x / a.w < b.x / b.w) break;
      blocks.splice(blocks.length - 2, 2, { x: a.x + b.x, y: a.y + b.y, w: a.w + b.w });
    }
  }
  const m = blocks.map((b) => [b.x / b.w, b.y / b.w] as [number, number]);
  // thin: keep the first, then every point >= gap past the last kept; always the last
  const out: [number, number][] = [];
  for (let k = 0; k < m.length; k++) {
    const last = k === m.length - 1, far = !out.length || m[k][0] - out[out.length - 1][0] >= gap;
    if (last && !far && out.length > 1) out.pop();   // the last point replaces a kept one too close to it
    if (far || last) out.push(m[k]);
  }
  return out.map(([x, y]) => [+Math.exp(x).toFixed(5), +Math.exp(y).toFixed(3)]);
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('pace_curve.ts')) {
  const argv = process.argv.slice(2);
  const arg = (k: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
  const track = trackArg(argv);
  const dir = resolve(ROOT, arg('--dir') ?? 'tools/race/out/pace_q');
  const outFile = arg('--out') ? resolve(arg('--out')!) : pacePath(track);
  const files = QS.map((q) => resolve(dir, q, track, 'pace.json')).filter((f) => existsSync(f));
  if (files.length !== QS.length) { console.error(`missing quantile files under ${dir} for ${track}: have ${files.length}`); process.exit(1); }
  // the strength calibrations (pace_target_scale.ts + calibrate_field.ts --pace): every target / 1.10, when present
  for (const x of STRENGTH_DIRS) { const f = resolve(dir, x, track, 'pace.json'); if (existsSync(f)) files.push(f); }
  console.log(`${track}: points from ${files.map((f) => f.split('/').slice(-3, -2)[0]).join(', ')}`);
  const byCar = new Map<string, [number, number][]>();
  for (const f of files) {
    const p: PaceJson = JSON.parse(readFileSync(f, 'utf8'));
    for (const c of p.cars) {
      const a = byCar.get(c.number) ?? [];
      if (c.scale && c.achievedLap) a.push([c.scale, c.achievedLap]);
      for (const s of c.stints ?? []) if (s.scale && s.achievedLap) a.push([s.scale, s.achievedLap]);
      byCar.set(c.number, a);
    }
  }
  const out: PaceJson = JSON.parse(readFileSync(outFile, 'utf8'));
  const slopes: number[] = [];
  let n = 0, pts = 0;
  for (const c of out.cars) {
    const raw = byCar.get(c.number) ?? [];
    const curve = fitCurve(raw);
    if (curve.length < 2) { delete c.curve; continue; }
    c.curve = curve;
    n++; pts += curve.length;
    const xs = curve.map((p) => Math.log(p[0])), ys = curve.map((p) => Math.log(p[1]));
    const mx = xs.reduce((a, b) => a + b, 0) / xs.length, my = ys.reduce((a, b) => a + b, 0) / ys.length;
    let sxy = 0, sxx = 0;
    for (let k = 0; k < xs.length; k++) { sxy += (xs[k] - mx) * (ys[k] - my); sxx += (xs[k] - mx) ** 2; }
    if (sxx > 1e-9) slopes.push(sxy / sxx);
  }
  slopes.sort((a, b) => a - b);
  console.log(`${track}: ${n} cars with a curve (${pts} points, ${(pts / Math.max(1, n)).toFixed(1)} per car); ln-ln slope median ${slopes[slopes.length >> 1]?.toFixed(3)}, p10 ${slopes[Math.floor(0.1 * slopes.length)]?.toFixed(3)}, p90 ${slopes[Math.floor(0.9 * slopes.length)]?.toFixed(3)}`);
  if (!argv.includes('--dry')) { writeFileSync(outFile, JSON.stringify(out, null, 1) + '\n'); console.log(`wrote ${outFile}`); }
}
