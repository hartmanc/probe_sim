// Pit-exit cone crossings and spins without a mishap, with the driver's state before each (AI robustness round,
// 26 Oct 2026). Runs the race exactly as ai_race.test.ts "45 cars, 3 laps" does (--fixture: the test's own director,
// Laguna) or as selfplay.ts does (--track), samples every car every 20 ms like the test, and prints for each car that
// crosses the cone line (> 0.2 m left of it) or spins (|heading error| > 1.3 rad) without a mishap / recovery a
// per-0.1 s table from --pre s before the event: station, lane e, shift / target, cap, edges, wheels on, off flag,
// steer, pedals, limiter, pass phase, heading error, slips.
//   npx tsx tools/race/cone_trace.ts --fixture [--seed 1] [--laps 3] [--pre 4] [--post 2] [--car NUM]
//   npx tsx tools/race/cone_trace.ts --track sonoma --seed 2 --laps 2
import { createCollisionWorld } from '../../src/physics/index';
import { RaceDirector } from '../../src/physics/ai/race';
import { loadTrackPack, loadProbeJson, loadPace, loadIdentityJson, trackArg } from './load';
import { TRACKS } from '../../src/scoreboard/config';
import { director as fixtureDirector, pack as fixturePack } from '../../src/physics/__tests__/ai_fixture';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const seed = Number(arg('--seed', '1'));
const fixture = argv.includes('--fixture');
const laps = Number(arg('--laps', fixture ? '3' : '4'));
const pre = Number(arg('--pre', '4')), post = Number(arg('--post', '2'));
const onlyCar = arg('--car', '');
let dir: RaceDirector, scenery: any;
if (fixture) {
  dir = fixtureDirector({ seed, laps, playerAi: true });
  scenery = fixturePack().scenery;
} else {
  const track = trackArg(argv);
  const pack = loadTrackPack(track);
  scenery = pack.scenery;
  const ai = TRACKS[track]?.ai;
  dir = new RaceDirector({
    line: pack.line, surface: pack.surface, makeSurface: pack.makeSurface, probeJson: loadProbeJson(), pace: loadPace(track), identity: loadIdentityJson(track),
    pitLane: pack.scenery?.pit_lane ?? null, collisionWorld: createCollisionWorld(pack.scenery, pack.track),
  }, { laps, seed, playerAi: true, followScale: ai?.followScale ?? 1, laneMargin: ai?.laneMargin ?? 1, shiftGrip: ai?.shiftGrip ?? 0 });
}
const line = dir.line, tr = dir.traffic, cars = dir.cars, n = cars.length;
const cones = scenery?.pit_exit_cones as { s0: number; s1: number; pts: number[][] } | undefined;
const coneLat: [number, number][] = cones ? cones.pts.map((p) => { const q = line.project(p[0], p[1]); return [q.s, q.lateral] as [number, number]; }).sort((a, b) => a[0] - b[0]) : [];
const latAt = (s: number) => { let lo = 0, hi = coneLat.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (coneLat[m][0] <= s) lo = m; else hi = m; } const [sa, la] = coneLat[lo], [sb, lb] = coneLat[hi]; return la + (sb > sa ? (s - sa) / (sb - sa) : 0) * (lb - la); };
const herrOf = (i: number) => {
  const st = cars[i].vehicle.state, [qx, qy, qz, qw] = st.quat;
  let h = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz)) - line.headingAt(tr.s[i]);
  while (h > Math.PI) h -= 2 * Math.PI; while (h < -Math.PI) h += 2 * Math.PI;
  return h;
};
const hist: string[][] = cars.map(() => []);
const histT: number[][] = cars.map(() => []);
const firstCone = new Map<number, number>(), coneN = new Map<number, number>(), maxOver = new Map<number, number>();
const firstSpin = new Map<number, number>();
// --detail NUM --from t0 --to t1: every 50 ms, per wheel (FL FR RL RR) slip use / slip ratio / load kN / mu, gear
const dNum = arg('--detail', ''), dFrom = Number(arg('--from', '0')), dTo = Number(arg('--to', '0'));
const dIdx = dNum ? cars.findIndex((c) => c.number === dNum) : -1;
const detail: string[] = [];
let k = 0;
while (dir.phase !== 'finished' && dir.time < (fixture ? 700 : laps * 220 + 120)) {
  dir.step(0.001);
  if (++k % 20 !== 0) continue;
  if (dIdx >= 0 && k % 50 === 0 && dir.time >= dFrom && dir.time <= dTo) {
    const d = cars[dIdx].driver as any, st = cars[dIdx].vehicle.state, w = st.wheels;
    detail.push(`${dir.time.toFixed(2)} s${tr.s[dIdx].toFixed(1)} v${tr.v[dIdx].toFixed(1)} e${tr.e[dIdx].toFixed(2)} herr${herrOf(dIdx).toFixed(3)} yr${st.angVel[2].toFixed(2)} st${d.input.steer.toFixed(2)} th${d.input.throttle.toFixed(2)} br${d.input.brake.toFixed(2)} g${st.gear} ${d.limiter} kC${(d.kCmd * 1000).toFixed(1)} | ` +
      w.map((x: any) => `${x.slipUse.toFixed(2)}/${x.slipAngle.toFixed(2)}/${x.slipRatio.toFixed(2)}/${(x.load / 1000).toFixed(1)}/${x.mu.toFixed(2)}${x.paved ? '' : 'U'}${x.onTrack ? '' : 'o'}`).join(' '));
  }
  for (let i = 0; i < n; i++) {
    const d = cars[i].driver as any; if (!d) continue;
    const s = tr.s[i];
    if (cones && s >= cones.s0 && s <= cones.s1) {
      const over = tr.lat[i] - latAt(s);
      if (over > 0.2) { if (!firstCone.has(i)) firstCone.set(i, dir.time); coneN.set(i, (coneN.get(i) ?? 0) + 1); maxOver.set(i, Math.max(maxOver.get(i) ?? 0, over)); }
    }
    const h = herrOf(i);
    if (dir.phase === 'green' && Math.abs(h) > 1.3 && !firstSpin.has(i)) firstSpin.set(i, dir.time);
    if (k % 100 !== 0) continue;
    const st = cars[i].vehicle.state, w = st.wheels, o = line.at(line.off, s);
    const capE = cones && s >= cones.s0 && s <= cones.s1 ? (latAt(s) - o).toFixed(2) : '-';
    hist[i].push(`${dir.time.toFixed(1)} s${s.toFixed(0)} v${tr.v[i].toFixed(1)}/${line.at(d.profile, s).toFixed(1)} e${tr.e[i].toFixed(2)} sh${d.shift.toFixed(2)} eT${tr.eT[i].toFixed(2)} cone${capE} [${(-line.at(line.halfR, s) - o).toFixed(1)} ${(line.at(line.halfL, s) - o).toFixed(1)}] on${w.filter((x: any) => x.onTrack).length} ${d.offTrack ? 'OFF' : 'on'} ${d.mishap ?? '-'} st${d.input.steer.toFixed(2)} th${d.input.throttle.toFixed(2)} br${d.input.brake.toFixed(2)} hb${d.input.handbrake ? 1 : 0} ${d.limiter} ph${d.passPhase} pt${d.passTarget >= 0 ? cars[d.passTarget].number : '-'} herr${h.toFixed(2)} yr${st.angVel[2].toFixed(2)} slF${Math.max(Math.abs(w[0].slipAngle), Math.abs(w[1].slipAngle)).toFixed(2)} slR${Math.max(Math.abs(w[2].slipAngle), Math.abs(w[3].slipAngle)).toFixed(2)} vlat${tr.vlat[i].toFixed(1)} kC${(d.kCmd * 1000).toFixed(1)} cap${d.steerCap.toFixed(2)}`);
    histT[i].push(dir.time);
  }
}
if (dIdx >= 0) { console.log(`detail #${dNum} (${(cars[dIdx] as any).spec?.name ?? ''}): slipUse/slipAngle/slipRatio/load kN/mu per wheel FL FR RL RR`); console.log(detail.join('\n')); }
const show = (i: number, t: number, tag: string) => {
  const c = cars[i];
  console.log(`${tag} #${c.number} at t ${t.toFixed(2)} (mishaps ${c.mishaps}, recoveries ${c.recoveries}, agg ${(c.driver as any).params.aggression})`);
  for (let q = 0; q < hist[i].length; q++) if (histT[i][q] >= t - pre && histT[i][q] <= t + post) console.log('   ' + hist[i][q]);
};
console.log(`cone crossings (20 ms samples > 0.2 m left): ${[...coneN].map(([i, v]) => `#${cars[i].number} ${v} max ${maxOver.get(i)!.toFixed(2)} m (mishaps ${cars[i].mishaps}, recoveries ${cars[i].recoveries})`).join(', ') || 'none'}`);
console.log(`spins (|herr| > 1.3 in green): ${[...firstSpin].map(([i, t]) => `#${cars[i].number} t${t.toFixed(1)} s${'?'} (mishaps ${cars[i].mishaps}, rec ${cars[i].recoveries})`).join(', ') || 'none'}`);
console.log(`mishaps: ${dir.mishapLog.map((e) => `#${e.number} ${e.kind} ${e.corner} t${e.t.toFixed(1)}`).join(', ')}`);
for (const [i, t] of firstCone) if (!onlyCar || cars[i].number === onlyCar) show(i, t, 'CONE');
for (const [i, t] of firstSpin) if ((!onlyCar && !firstCone.has(i)) || cars[i].number === onlyCar) show(i, t, 'SPIN');
