// Self-play event traces: runs one seed exactly as selfplay.ts does, records every car every 0.1 s, and prints the
// 3 s before each four-off / contact (lane offset e, shift, target, edges, speed vs profile, limiter, pass phase).
//   npx tsx tools/race/selfplay_trace.ts --track <id> --seed N [--near s0-s1] [--kind four|contact] [--max 20] [--pre 3]
//   [--summary: one classified line per event]  [--car NUM --from t0 --to t1: pedals / steering / slips of one car]
import { createCollisionWorld } from '../../src/physics/index';
import { RaceDirector } from '../../src/physics/ai/race';
import { loadTrackPack, loadProbeJson, loadPace, IDENTITY_PATH, trackArg } from './load';
import { existsSync, readFileSync } from 'node:fs';
import { runSelfplay } from './selfplay_metrics';
import { TRACKS } from '../../src/scoreboard/config';

const argv = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const seed = Number(arg('--seed', '1')), laps = Number(arg('--laps', '4'));
const track = trackArg(argv);
const near = arg('--near', '').split('-').map(Number);
const kind = arg('--kind', 'four'), maxN = Number(arg('--max', '20')), pre = Number(arg('--pre', '3'));
const followScale = argv.includes('--follow-scale') ? Number(arg('--follow-scale', '1')) : (TRACKS[track]?.ai?.followScale ?? 1);
const pack = loadTrackPack(track);
const identity = existsSync(IDENTITY_PATH) ? JSON.parse(readFileSync(IDENTITY_PATH, 'utf8')) : null;
const makeSurface = pack.makeSurface;   // the app's surface options (load.ts)
const dir = new RaceDirector({
  line: pack.line, surface: pack.surface, makeSurface, probeJson: loadProbeJson(), pace: loadPace(track), identity,
  pitLane: pack.scenery?.pit_lane ?? null, collisionWorld: createCollisionWorld(pack.scenery, pack.track),
}, { laps, seed, playerAi: true, followScale, laneMargin: TRACKS[track]?.ai?.laneMargin ?? 1, shiftGrip: TRACKS[track]?.ai?.shiftGrip ?? 0 });
const line = dir.line, tr = dir.traffic, cars = dir.cars, n = cars.length;
type Rec = { t: number; s: number; e: number; sh: number; eT: number; v: number; vp: number; lim: string; ph: number; pt: number; on: number; hL: number; hR: number; off: number; yaw: number; thr: number; brk: number; slR: number; lead: number };
const hist: Rec[][] = cars.map(() => []);
let k = 0;
const step0 = dir.step.bind(dir);
(dir as any).step = (dt: number, p?: any) => {
  step0(dt, p);
  if (++k % 100 !== 0) return;
  for (let i = 0; i < n; i++) {
    const d = cars[i].driver as any; if (!d) continue;
    const st = cars[i].vehicle.state, s = tr.s[i], o = line.at(line.off, s);
    const [qx, qy, qz, qw] = st.quat; const yaw = Math.atan2(2 * (qx * qy + qz * qw), 1 - 2 * (qy * qy + qz * qz));
    let herr = yaw - line.headingAt(s); while (herr > Math.PI) herr -= 2 * Math.PI; while (herr < -Math.PI) herr += 2 * Math.PI;
    hist[i].push({ t: dir.time, s, e: tr.e[i], sh: d.shift, eT: tr.eT[i], v: tr.v[i], vp: line.at(d.profile, s), lim: d.limiter, ph: d.passPhase, pt: d.passTarget,
      on: st.wheels.filter((w: any) => w.onTrack).length, hL: line.at(line.halfL, s) - o, hR: -line.at(line.halfR, s) - o, off: tr.off[i], yaw: herr, thr: d.input.throttle, brk: d.input.brake, slR: Math.max(Math.abs(st.wheels[2].slipAngle), Math.abs(st.wheels[3].slipAngle)), lead: d.leadIdx });
  }
};
// --car NUM --from t0 --to t1: a detailed per-0.1 s table for one car (pedals, steering, slips, commanded curvature)
const dcar = arg('--car', ''), dFrom = Number(arg('--from', '0')), dTo = Number(arg('--to', '0'));
const detail: string[] = [];
if (dcar) {
  const di = cars.findIndex((c) => c.number === dcar);
  const step1 = (dir as any).step;
  (dir as any).step = (dt: number, p?: any) => {
    step1(dt, p);
    if (k % 100 !== 0 || dir.time < dFrom || dir.time > dTo) return;
    const d = cars[di].driver as any, st = cars[di].vehicle.state, w = st.wheels;
    detail.push(`${dir.time.toFixed(1)} s ${tr.s[di].toFixed(0)} v ${tr.v[di].toFixed(1)} e ${tr.e[di].toFixed(2)} sh ${d.shift.toFixed(2)} lim ${d.limiter} steer ${d.input.steer.toFixed(2)} thr ${d.input.throttle.toFixed(2)} brk ${d.input.brake.toFixed(2)} kCmd ${(d.kCmd * 1000).toFixed(1)} kLine ${(line.at(line.curv, tr.s[di]) * 1000).toFixed(1)} slipF ${Math.max(Math.abs(w[0].slipAngle), Math.abs(w[1].slipAngle)).toFixed(3)} slipR ${Math.max(Math.abs(w[2].slipAngle), Math.abs(w[3].slipAngle)).toFixed(3)} srR ${Math.min(w[2].slipRatio, w[3].slipRatio).toFixed(3)} yawRate ${st.angVel[2].toFixed(2)} cap ${d.steerCap.toFixed(2)}/${d.brakeCap.toFixed(2)}`);
  };
}
const m = runSelfplay(dir, makeSurface(), { log: false });
if (dcar) { console.log(detail.join('\n')); process.exit(0); }
const idxOf = (num: string) => cars.findIndex((c) => c.number === num);
const show = (i: number, t1: number, tag: string) => {
  console.log(`  ${tag} #${cars[i].number} (agg ${(cars[i].driver as any).params.aggression})  t   s     e    shift  eT   [edgeR edgeL]  v/vprof  lim  ph tgt on yawErr`);
  for (const r of hist[i]) if (r.t >= t1 - pre && r.t <= t1 + 0.3 && Math.round(r.t * 10) % 3 === 0)
    console.log(`    ${r.t.toFixed(1)} ${r.s.toFixed(0)} ${r.e.toFixed(2)} ${r.sh.toFixed(2)} ${r.eT.toFixed(2)} [${r.hR.toFixed(1)} ${r.hL.toFixed(1)}] ${r.v.toFixed(1)}/${r.vp.toFixed(1)} ${r.lim} ${r.ph} ${r.pt >= 0 ? cars[r.pt].number : '-'} ${r.on} ${r.yaw.toFixed(2)}${r.off ? ' OFF' : ''}`);
};
let shown = 0;
// --summary: one line per event with a cause class (from the 3 s before it)
const win = (i: number, t1: number, a: number, b: number) => hist[i].filter((r) => r.t >= t1 - a && r.t <= t1 - b);
const cls = (i: number, t1: number) => {
  const w = win(i, t1, 3, 0.3), w2 = win(i, t1, 2, 0.3);
  if (w.some((r) => Math.abs(r.yaw) > 0.8)) return 'spin';
  const lag = Math.max(0, ...w2.map((r) => Math.abs(r.e - r.sh)));
  const base = w2.some((r) => r.ph === 1 || r.ph === 2) ? 'pass' : w2.some((r) => r.ph === 3) ? 'merge' : w2.some((r) => Math.abs(r.eT) > 0.5 && !r.off) ? 'room' : w2.some((r) => r.off) ? 'rejoin' : 'line';
  return base + (lag > 1.5 ? '+lag' : '');
};
if (argv.includes('--summary')) {
  const spinOnset = (i: number, t1: number) => {
    const w = win(i, t1, 8, 0); let k0 = -1;
    for (let q = 0; q < w.length; q++) if (Math.abs(w[q].yaw) > 0.8) { k0 = q; break; }
    if (k0 < 0) return '';
    let q = k0; while (q > 0 && Math.abs(w[q].yaw) > 0.25) q--;
    const a = w[Math.max(0, q - 5)], b = w[q];
    return `onset s${b.s.toFixed(0)} t${b.t.toFixed(1)} v${b.v.toFixed(1)}/${b.vp.toFixed(1)} ph${a.ph}->${b.ph} sh${a.sh.toFixed(1)}->${b.sh.toFixed(1)} eT${a.eT.toFixed(1)} e${a.e.toFixed(1)}->${b.e.toFixed(1)} lim ${a.lim}->${b.lim} thr${b.thr.toFixed(2)} brk${b.brk.toFixed(2)} slR${b.slR.toFixed(2)}`;
  };
  for (const ev of m.rules.fourOffAt) { const i = idxOf(ev.car); const r = win(i, ev.t!, 1.0, 0.3)[0]; const c = cls(i, ev.t!); console.log(`F seed${seed} s${ev.s} t${ev.t} #${ev.car} ${c} side ${r ? (r.e > 0 ? 'L' : 'R') : '?'}${c === 'spin' ? ' ' + spinOnset(i, ev.t!) : ''}`); }
  for (const ev of m.rules.contactAt) {
    const a = idxOf(ev.a), b = idxOf(ev.b);
    // rear car = the one behind in s at the contact; rear-end = nearly in line (|dl| < 2.2) and > 3.5 m apart in s
    const back = ev.ds! > 0 ? a : b, front = back === a ? b : a;
    const kind = Math.abs(ev.dl!) < 2.2 && Math.abs(ev.ds!) > 3.5 ? 'rear' : 'side';
    const fol = (dt0: number) => { const r = win(back, ev.t, dt0 + 0.06, dt0 - 0.06)[0]; return r ? (r.lead === front ? 'F' : r.lead >= 0 ? 'o' : '-') : '?'; };
    const rb = win(back, ev.t, 2, 1.9)[0], rf = win(front, ev.t, 2, 1.9)[0];
    const gap2 = rb && rf ? (rf.s - rb.s).toFixed(0) : '?', de2 = rb && rf ? (rf.e - rb.e).toFixed(1) : '?', dv2 = rb && rf ? (rb.v - rf.v).toFixed(1) : '?';
    console.log(`C seed${seed} s${ev.s} t${ev.t} ${kind} back #${cars[back].number}:${cls(back, ev.t)} front #${cars[front].number}:${cls(front, ev.t)} ${ev.ctx} cl${ev.closing} follow[-2,-1,-.5]=${fol(2)}${fol(1)}${fol(0.5)} t-2: gap ${gap2} de ${de2} dv ${dv2}`);
  }
  process.exit(0);
}
if (kind === 'four') {
  for (const ev of m.rules.fourOffAt) {
    if (near.length === 2 && !(ev.s >= near[0] && ev.s <= near[1])) continue;
    if (shown++ >= maxN) break;
    const i = idxOf(ev.car);
    console.log(`FOUR-OFF #${ev.car} s ${ev.s} t ${ev.t} ${ev.ctx}`);
    show(i, ev.t!, 'car');
    // nearest cars at the moment (within 30 m)
    const r = hist[i].find((x) => x.t >= ev.t! - 1.5);
    if (r) for (let j = 0; j < n; j++) { if (j === i) continue; const q = hist[j].find((x) => Math.abs(x.t - r.t) < 0.06); if (q && Math.abs(q.s - r.s) < 25) console.log(`    near at t-1.5: #${cars[j].number} ds ${(q.s - r.s).toFixed(1)} e ${q.e.toFixed(2)} v ${q.v.toFixed(1)} ${q.lim} ph${q.ph} tgt ${q.pt >= 0 ? cars[q.pt].number : '-'}`); }
  }
} else {
  for (const ev of m.rules.contactAt) {
    if (near.length === 2 && !(ev.s >= near[0] && ev.s <= near[1])) continue;
    if (shown++ >= maxN) break;
    console.log(`CONTACT #${ev.a}-#${ev.b} s ${ev.s} t ${ev.t} closing ${ev.closing} ${ev.ctx}`);
    show(idxOf(ev.a), ev.t, 'a'); show(idxOf(ev.b), ev.t, 'b');
  }
}
