// Mid-Ohio round 6, T8 (c): the race AI's own speed profile (src/physics/ai/field.ts buildSpeedProfile: banking credit,
// the crest load factor 1 + v^2 vcurv / g, braking at that load) for the Probe at full pace on the package's racing line,
// through T7-T9, with and without the crest term (vcurv zeroed), beside drive.ts's target profile (no crest term).
// Read only: nothing in the package or the AI is changed.
//
//   npx tsx tools/track/compare/mid_ohio/r6/ai_profile_t8.ts <package dir> [drive out dir] > out.json
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { RaceLine } from '../../../../../src/physics/ai/line';
import { buildAiSpec, buildSpeedProfile, measureCarPerf, loadFactor } from '../../../../../src/physics/ai/field';

const pkg = process.argv[2], drive = process.argv[3];
const track = JSON.parse(readFileSync(join(pkg, 'track.json'), 'utf8'));
const ghosts = JSON.parse(readFileSync(join(pkg, 'ghosts.json'), 'utf8'));
const probe = JSON.parse(readFileSync('public/cars/probe_gt/car.json', 'utf8'));
const line = new RaceLine(track, ghosts);
const spec = buildAiSpec(probe, null, 1), perf = measureCarPerf(spec);
const prof = buildSpeedProfile(line, perf, spec);
const saved = Float64Array.from(line.vcurv);
(line.vcurv as Float64Array).fill(0);
const flat = buildSpeedProfile(line, perf, spec);
(line.vcurv as Float64Array).set(saved);
const dp: Record<number, number> = {};
if (drive && existsSync(join(drive, 'target_profile.csv'))) {
  for (const r of readFileSync(join(drive, 'target_profile.csv'), 'utf8').trim().split('\n').slice(1)) { const [s, v] = r.split(','); dp[Number(s)] = Number(v); }
}
const kmh = (v: number) => Math.round(v * 36) / 10;
const rows = [];
for (let s = 2380; s <= 2680; s += 10) {
  const i = Math.round(s / line.spacing) % line.N;
  rows.push({ s, v_ai_kmh: kmh(prof[i]), v_ai_no_crest_kmh: kmh(flat[i]), v_drive_target_kmh: dp[s] ?? null,
    load_factor: Math.round(loadFactor(line, i, prof[i]) * 1000) / 1000, vcurv_per_km: Math.round(line.vcurv[i] * 1e5) / 100,
    R_line_m: Math.round(1 / Math.max(1e-6, Math.abs(line.curv[i]))), grade_pct: Math.round(line.grade[i] * 1000) / 10 });
}
const win = (a: number, b: number, arr: ArrayLike<number>) => { let m = 1e9, at = 0; for (let s = a; s <= b; s++) { const i = Math.round(s / line.spacing) % line.N; if (arr[i] < m) { m = arr[i]; at = s; } } return { min_kmh: kmh(m), at_s: at }; };
console.log(JSON.stringify({ perf: { alat_g: perf.alat, abrake_g: perf.abrake }, corners: line.corners.filter((c) => /T7|T8|T9/.test(c.name)),
  T8_window_2460_2600: { ai: win(2460, 2600, prof), ai_no_crest: win(2460, 2600, flat) },
  T9_window_2600_2700: { ai: win(2600, 2700, prof), ai_no_crest: win(2600, 2700, flat) }, rows }, null, 1));
