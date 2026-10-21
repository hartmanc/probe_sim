// Kerb traversal probe: drives the player's Probe (public/cars/probe_gt/car.json, the real 1 kHz physics) over every
// kerb strip of a track package (scenery.json kerbs + sausages) and logs what the car does on it: per-wheel ground
// height above the plain road, wheel load, suspension travel, body roll (relative to the road) and roll rate, wheel
// lift, hull (floor) contact. Also an AI-driven solo lap with the same logging (`--lap`), with time into the lap.
// The gate (src/physics/__tests__/kerbgate.test.ts) fails on roll past 15 deg relative to the road or a rollover; wheel
// lifts are reported, not gated (the owner, 21 Oct 2026: "Lifting a wheel isn't inherently a realism issue. Driving
// over a kerb and rolling over is an issue.").
//
//   npx tsx tools/physics/kerb_sweep.ts [--track sonoma] [--offsets -1,0,1] [--angles 0] [--speed-scale 1]
//       [--raised] [--set car.path=value ...] [--profile height,face,back] [--lap] [--trace <stripIndex>:<offset>[:<angle>] --csv out.csv] [--json out.json] [--quiet]
//
// Sweep: for each strip, start 60 m before it on the racing line + offset (m, toward the kerb's side = +), at the
// speed profile's speed (buildSpeedProfile for this car: "line speed"), and follow the offset line with a pure-pursuit
// driver until 30 m past the strip. --angles θ (deg, > 0) instead drives a crossing path: from 3 m inside the kerb band
// toward and over it at θ to the line, crossing the band centre at the strip's middle.
import { loadTrackPack, loadProbeJson, trackArg } from '../race/load';
import { kerbTraversal, gateCases, type TraversalCase, type TraversalResult, runAiLap } from '../../src/physics/__tests__/kerbprobe';
import { writeFileSync } from 'node:fs';
import { createTrackSurface } from '../../src/physics/index';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const track = trackArg(argv);
const pack = loadTrackPack(track);
const probe = loadProbeJson();
// --set suspension.front.damperKnee=0.3 ... (car.json overrides, as tools/calibrate/drive.ts)
for (let i = 0; i < argv.length; i++) if (argv[i] === '--set') {
  const [p, v] = argv[++i].split('='); const ks = p.split('.'); let o = probe;
  for (const k of ks.slice(0, -1)) o = o[k];
  o[ks[ks.length - 1]] = Number(v);
}
// --profile height,face,back: try another kerb profile (the package's own otherwise)
if (argv.includes('--profile') && pack.scenery?.kerbs) {
  const [height, face, back] = arg('--profile', '').split(',').map(Number);
  pack.scenery.kerbs.profile = { height, face, back };
  pack.surface = createTrackSurface(pack.track, pack.heightfield, { pitLane: pack.pitLane, sausages: pack.scenery.sausages ?? null, kerbs: pack.scenery.kerbs });
}
const quiet = argv.includes('--quiet');
const offsets = arg('--offsets', '-1,0,1').split(',').map(Number);
const angles = arg('--angles', '0').split(',').map(Number);
const speedScale = Number(arg('--speed-scale', '1'));

const fmt = (r: TraversalResult) =>
  `${r.label.padEnd(34)} v ${r.v0.toFixed(1).padStart(5)} m/s  kerb ${r.onKerbMs.toString().padStart(5)} ms  h ${(r.maxKerbH * 100).toFixed(1).padStart(4)} cm  ` +
  `roll ${r.maxRollDeg.toFixed(1).padStart(5)} deg (base ${r.baseRollDeg.toFixed(1).padStart(4)})  rate ${r.maxRollRateDeg.toFixed(0).padStart(4)} deg/s  ` +
  `lift ${r.liftMs.toString().padStart(4)} ms (kerb ${r.kerbLiftMs.toString().padStart(4)}, gap ${(r.kerbLiftGap * 100).toFixed(1).padStart(4)} cm)  Fz ${(r.maxLoad / 1000).toFixed(1).padStart(5)} kN  ` +
  `hull ${r.hullMs.toString().padStart(3)} ms  susp ${r.maxWheelVz.toFixed(2)} m/s${r.rolledOver ? '  ROLLED' : ''}${r.fail ? '  FAIL' : ''}`;

if (argv.includes('--lap')) {
  const r = runAiLap(pack, probe, { quiet });
  for (const e of r.events) console.log(e);
  console.log(`lap ${r.lapTime.toFixed(2)} s, max roll ${r.maxRollDeg.toFixed(1)} deg at t ${r.maxRollT.toFixed(2)} s s ${r.maxRollS.toFixed(0)}, rolled ${r.rolled}`);
  process.exit(0);
}

const trace = arg('--trace', '');
const results: TraversalResult[] = [];
const kerbs = pack.scenery?.kerbs?.strips ?? [];
const saus = pack.scenery?.sausages?.strips ?? [];
// every strip, raised or not (a flat one is a no-op: it shows the line's own roll and lifts), unless --raised
const cases: TraversalCase[] = argv.includes('--raised') ? gateCases(pack, offsets, angles) : [];
if (!argv.includes('--raised')) for (let k = 0; k < kerbs.length + saus.length; k++) {
  const isK = k < kerbs.length;
  const st = isK ? kerbs[k] : saus[k - kerbs.length];
  if (isK && st.kind === 'verge') continue;
  for (const a of angles) for (const o of a > 0 ? [0] : offsets) cases.push({ kind: isK ? 'kerb' : 'sausage', index: isK ? k : k - kerbs.length, offset: o, angleDeg: a, speedScale });
}
let sel = cases;
if (trace) {
  const [i, o, a] = trace.split(':').map(Number);
  sel = [{ kind: 'kerb', index: i, offset: o, angleDeg: a || 0, speedScale }];
}
for (const c of sel) {
  const r = kerbTraversal(pack, probe, c, { trace: !!trace });
  results.push(r);
  if (!quiet || r.fail) console.log(fmt(r));
  if (trace && r.rows) {
    const out = arg('--csv', 'kerb_trace.csv');
    writeFileSync(out, r.rows.join('\n') + '\n');
    console.log(`trace -> ${out} (${r.rows.length - 1} rows)`);
  }
}
const fails = results.filter((r) => r.fail);
console.log(`${results.length} traversals, ${fails.length} fail (roll > 15 deg relative to the road, or a wheel lifted by the kerb, or rolled over)`);
const j = arg('--json', '');
if (j) writeFileSync(j, JSON.stringify(results.map(({ rows, ...r }) => r), null, 1));
