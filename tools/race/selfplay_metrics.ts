// Racecraft metrics for a headless self-play race (tools/race/selfplay.ts, ai_behaviour.test.ts).
// Pure: steps a RaceDirector to the flag and samples every SAMPLE steps. Only the director.step calls are timed.
import type { Surface } from '../../src/physics/types';
import type { RaceDirector } from '../../src/physics/ai/race';

const SAMPLE = 10;            // steps between samples (10 ms)
const ALONE = 30;             // m: nobody this close ahead or behind = alone ...
const ALONE_T = 2;            // s: ... for at least this long (clean air, not the moment an interaction ends)
const CLEAR = 0.97;           // target lap ratio: clearly faster
const HIST_BIN = 0.01, HIST_N = 2000;

class Acc {
  n = 0; sq = 0; hist = new Uint32Array(HIST_N);
  add(e: number): void { this.n++; this.sq += e * e; const b = Math.min(HIST_N - 1, Math.floor(Math.abs(e) / HIST_BIN)); this.hist[b]++; }
  rms(): number { return this.n ? Math.sqrt(this.sq / this.n) : NaN; }
  pct(p: number): number {
    if (!this.n) return NaN;
    let k = 0; const want = p * this.n;
    for (let b = 0; b < HIST_N; b++) { k += this.hist[b]; if (k >= want) return (b + 1) * HIST_BIN; }
    return HIST_N * HIST_BIN;
  }
}

export interface SelfplayMetrics {
  cars: number; laps: number; carLaps: number; raceTime: number;
  line: { instRms: number; instP95: number; why: Record<string, number>; rms: number; p95: number; samples: number; trackRms: number; trackP95: number; maxErr: number; worstAt: number; corners: { name: string; rms: number; p95: number; samples: number }[] };
  passing: { attempts: number; ends: Record<string, number>; situations: number; reachedBrakeZone: number; setUp: number; completed: number; medianStuck: number; p90Stuck: number; passesTotal: number;
    /** station of each green pass (the passing car's s when the order changed; sampled every 0.1 s) */
    passAt?: number[];
    /** completion by pace ratio (target lap of the faster / the slower): < 0.85, 0.85-0.92, 0.92-0.97 */
    byRatio: { lo: number; hi: number; fails?: string[]; situations: number; completed: number; medianStuck: number; open: Record<string, number> }[] };
  defending: { vsClearlyFaster: number; within3: number; vsSlower: number; none: number };
  rules: { contacts: number; contactsPerCarLap: number; hardContacts: number; fourOff: number; fourOffMishap: number; fourOffPerCarLap: number; fourOffNonMishapPerCarLap: number; formationPasses: number; recoveries: number; recoveryAt?: { s: number; t: number; car: string; phase: string }[]; fourOffAt: { s: number; t?: number; car: string; ctx: string }[]; contactAt: { s: number; t: number; a: string; b: string; closing: number; ctx: string; phase?: string; ds?: number; dl?: number }[] };
  mishaps: { total: number; perCarLap: number; wide: number; spin: number; byCorner: Record<string, number>; lossMedian: number; lossMin: number; lossMax: number; losses: { kind: string; corner: string; loss: number }[] };
  cost: { usPerStep: number; usPerCar: number };
}

interface Situation { i: number; j: number; base: number; t0: number; tClose: number; setup: boolean; brakeZone: boolean; done: boolean; tDone: number; seen: number; why?: string }

const median = (a: number[]) => { if (!a.length) return NaN; const b = [...a].sort((x, y) => x - y); return b[Math.floor(b.length / 2)]; };
const pctl = (a: number[], p: number) => { if (!a.length) return NaN; const b = [...a].sort((x, y) => x - y); return b[Math.min(b.length - 1, Math.floor(p * b.length))]; };

export function runSelfplay(dir: RaceDirector, surface: Surface, opts: { log?: boolean; maxTime?: number } = {}): SelfplayMetrics {
  const line = dir.line, L = line.L, tr = dir.traffic, n = dir.cars.length, cars = dir.cars;
  const corners = line.corners;
  const cornerAcc = corners.map(() => new Acc());
  const all = new Acc(), trk = new Acc(), inst = new Acc();
  const aloneFor = new Float64Array(n);
  let maxErr = 0, worstAt = -1;
  const why = new Map<string, number>();
  const situations = new Map<number, Situation>();
  const closed: Situation[] = [];
  const defend = { vsClearlyFaster: 0, within3: 0, vsSlower: 0, none: 0 };
  const prevDefend = new Int8Array(n);
  const prevPass = new Int32Array(n).fill(-1); const passEnds: Record<string, number> = {}; let passStarts = 0;
  const prevS = new Float64Array(n);
  const ahead = new Int8Array(n * n);      // sign of U[i] - U[j] (formation and green order tracking)
  let formationPasses = 0, passesTotal = 0;
  const passAt: number[] = [];
  let contacts = 0, hard = 0;
  const pairSeen = new Map<number, number>();
  const offT = new Float64Array(n), onT = new Float64Array(n).fill(99), armed = new Uint8Array(n).fill(1);
  let fourOff = 0, fourOffMishap = 0;
  const fourOffAt: { s: number; t?: number; car: string; ctx: string }[] = [], contactAt: SelfplayMetrics['rules']['contactAt'] = [];
  let Ugreen: Float64Array | null = null;
  const prevRec = new Int32Array(n); const recoveryAt: { s: number; t: number; car: string; phase: string }[] = [];
  let tGreen = NaN;
  const mishapOpen: { idx: number; U0: number; t0: number; kind: string; corner: string }[] = [];
  const losses: { kind: string; corner: string; loss: number }[] = [];
  let lastMishapLen = 0;
  const lastMishapT = new Float64Array(n).fill(-1e9);
  const dt = 0.001;
  let ms = 0, steps = 0;
  const maxTime = opts.maxTime ?? dir.config.laps * 220 + 120;
  const anyDir = dir as unknown as { mishapLog?: { t: number; idx: number; corner: string; kind: string }[] };
  const drv = (i: number) => cars[i].driver as unknown as { passTarget: number; passSide: number; defendSide: number; offTrack: boolean; mishapActive?: boolean; profile: Float64Array } | null;

  const expectedTime = (prof: Float64Array, U0: number, dist: number) => { let t = 0; for (let d = 0; d < dist; d += 2) t += 2 / Math.max(3, line.at(prof, U0 + d)); return t; };

  while (dir.time < maxTime) {
    const a = performance.now();
    for (let k = 0; k < SAMPLE; k++) {
      dir.step(dt);
      for (let c = 0; c < dir.contactCount; c++) {
        const ev = dir.contacts[c];
        if (cars[ev.a].isPlayer && !cars[ev.a].driver || cars[ev.b].isPlayer && !cars[ev.b].driver) continue;
        if (ev.closing <= 1) continue;
        const key = Math.min(ev.a, ev.b) * 1000 + Math.max(ev.a, ev.b);
        const last = pairSeen.get(key) ?? -1e9;
        pairSeen.set(key, dir.time);
        if (dir.time - last < 1) continue;
        if (dir.phase === 'green') { contacts++; if (ev.closing > 3) hard++; {
          const da = drv(ev.a), db = drv(ev.b);
          const ctx = (da?.passTarget === ev.b || db?.passTarget === ev.a) ? 'pass' : (tr.off[ev.a] || tr.off[ev.b]) ? 'off' : (da?.passTarget ?? -1) >= 0 || (db?.passTarget ?? -1) >= 0 ? 'passing-other' : 'line';
          contactAt.push({ s: Math.round(tr.s[ev.a]), t: +dir.time.toFixed(1), a: cars[ev.a].number, b: cars[ev.b].number, closing: +ev.closing.toFixed(2), ctx: ctx + '/' + ((da as unknown as { limiter: string })?.limiter ?? '') + '/' + ((db as unknown as { limiter: string })?.limiter ?? ''), phase: `${(da as unknown as { passPhase?: number })?.passPhase ?? '-'}${(db as unknown as { passPhase?: number })?.passPhase ?? '-'}`, ds: +tr.ds(ev.a, ev.b).toFixed(1), dl: +(tr.lat[ev.b] - tr.lat[ev.a]).toFixed(2) });
        } }
      }
    }
    ms += performance.now() - a; steps += SAMPLE;
    const t = dir.time, phase = dir.phase;
    if (phase === 'finished' || (phase === 'chequered' && dir.player.finished)) break;
    if (phase === 'green' && !Ugreen) { Ugreen = Float64Array.from(tr.U); tGreen = t; for (let i = 0; i < n; i++) prevS[i] = tr.s[i]; }
    // ---- order changes (formation passes; total passes during green)
    if (steps % 100 === 0 && (phase === 'formation' || phase === 'green')) {
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        if (i === j) continue;
        const now = tr.U[i] > tr.U[j] ? 1 : -1, k = i * n + j, was = ahead[k];
        ahead[k] = now;
        if (was === -1 && now === 1 && Math.abs(tr.U[i] - tr.U[j]) < 50 && !tr.off[j] && !tr.away[j] && tr.v[j] > 5 && !cars[j].driver?.needsRecovery) {
          if (phase === 'formation') formationPasses++; else { passesTotal++; passAt.push(Math.round(tr.s[i])); }
        }
      }
    }
    if (phase !== 'green') continue;
    // ---- mishap log: time lost over the next 600 m vs the car's own profile
    const log = anyDir.mishapLog;
    if (log && log.length > lastMishapLen) {
      for (let q = lastMishapLen; q < log.length; q++) { const e = log[q]; mishapOpen.push({ idx: e.idx, U0: tr.U[e.idx], t0: e.t, kind: e.kind, corner: e.corner }); lastMishapT[e.idx] = e.t; }
      lastMishapLen = log.length;
    }
    for (let q = mishapOpen.length - 1; q >= 0; q--) {
      const o = mishapOpen[q];
      if (tr.U[o.idx] >= o.U0 + 600) {
        losses.push({ kind: o.kind, corner: o.corner, loss: (t - o.t0) - expectedTime(drv(o.idx)!.profile, o.U0, 600) });
        mishapOpen.splice(q, 1);
      }
    }
    for (let i = 0; i < n; i++) {
      const d = drv(i);
      if (!d) continue;
      const s = tr.s[i], rk = tr.rank[i];
      // nearest cars ahead / behind (not away)
      let jA = -1, dA = Infinity, jB = -1, dB = Infinity;
      for (let k = 1; k < n; k++) { const j = tr.order[(rk + k) % n]; if (tr.away[j]) continue; dA = tr.ds(i, j); if (dA < 0) dA += L; jA = j; break; }
      for (let k = 1; k < n; k++) { const j = tr.order[(rk - k + n) % n]; if (tr.away[j]) continue; dB = -tr.ds(i, j); if (dB < 0) dB += L; jB = j; break; }
      const busy = d.offTrack || d.mishapActive || tr.off[i] || tr.away[i] || t - lastMishapT[i] < 15;
      // ---- (a) line tracking when alone
      if (!busy && dA > ALONE && dB > ALONE) aloneFor[i] += SAMPLE * dt; else aloneFor[i] = 0;
      if (aloneFor[i] > 0 && t - tGreen > 3) inst.add(tr.lat[i] - line.at(line.off, s));
      if (aloneFor[i] >= ALONE_T && t - tGreen > 3) {
        const e = tr.lat[i] - line.at(line.off, s);
        all.add(e);
        if (Math.abs((d as unknown as { shift: number }).shift) < 0.05) trk.add(e);
        if (Math.abs(e) > maxErr) { maxErr = Math.abs(e); worstAt = s; }
        { const sh = (d as unknown as { shift: number }).shift; const k = Math.abs(sh) < 0.05 ? 'tracking' : Math.abs(e - sh) < 0.5 ? 'offset:' + ((d as unknown as { limiter: string }).limiter) : 'offset+err'; why.set(k, (why.get(k) ?? 0) + e * e); }
        for (let c = 0; c < corners.length; c++) {
          const C = corners[c];
          let u = s - C.brake; if (u < 0) u += L;
          let span = C.apex + 60 - C.brake; if (span < 0) span += L;
          if (u <= span) { cornerAcc[c].add(e); break; }
        }
      }
      // ---- (c) defending: a new defensive move, classified by the pace of the nearest car behind
      const ds = d.defendSide | 0;
      if (ds !== 0 && prevDefend[i] === 0) {
        if (jB < 0 || dB > 30) defend.none++;
        else {
          const r = tr.pace[jB] / tr.pace[i];
          if (r < CLEAR) defend.vsClearlyFaster++; else if (r <= 1 / CLEAR) defend.within3++; else defend.vsSlower++;
        }
      }
      prevDefend[i] = ds;
      if (d.passTarget !== prevPass[i]) {
        if (prevPass[i] >= 0) { const k = (d as unknown as { passEnd: string }).passEnd || '?'; passEnds[k] = (passEnds[k] ?? 0) + 1; }
        if (d.passTarget >= 0) passStarts++;
        prevPass[i] = d.passTarget;
      }
      // ---- (b) clearly faster than the car directly ahead: open a situation
      if (jA >= 0 && dA < 40 && !busy && !tr.off[jA] && tr.pace[i] < CLEAR * tr.pace[jA]) {
        const key = i * 1000 + jA;
        let sit = situations.get(key);
        if (!sit) { sit = { i, j: jA, base: Math.round((tr.U[jA] - tr.U[i] - dA) / L) * L, t0: t, tClose: NaN, setup: false, brakeZone: false, done: false, tDone: NaN, seen: t }; situations.set(key, sit); }
        sit.seen = t;
        if (dA < 20 && Number.isNaN(sit.tClose)) sit.tClose = t;
      }
      // ---- four wheels off (unpaved), sustained 0.25 s, re-armed after 2 s back on
      const st = cars[i].vehicle.state;
      let allOff = true;
      // round 15: a kerb band outside the edge (kerbs.inside false) is course for the track limit (SurfaceSample.onKerbBand)
      for (const w of st.wheels) { if (w.onTrack) { allOff = false; break; } const sm = surface.sample(w.pos[0], w.pos[1]); if (sm.paved || sm.onKerbBand) { allOff = false; break; } }
      const h = SAMPLE * dt;
      if (allOff) { offT[i] += h; onT[i] = 0; } else { offT[i] = 0; onT[i] += h; }
      if (onT[i] >= 2) armed[i] = 1;
      if (allOff && offT[i] >= 0.25 && armed[i]) { armed[i] = 0; fourOff++; fourOffAt.push({ s: Math.round(s), t: +t.toFixed(1), car: cars[i].number, ctx: (d.passTarget >= 0 ? 'pass' : d.defendSide ? 'defend' : dA < ALONE || dB < ALONE ? 'traffic' : 'alone') + '/' + ((d as unknown as { passPhase?: number }).passPhase ?? '-') + '/' + ((d as unknown as { limiter: string }).limiter) }); if (t - lastMishapT[i] < 15 || d.mishapActive) fourOffMishap++; }
    }
    // ---- situations: progress, setup at passable brake points, completion, expiry
    for (const [key, sit] of situations) {
      const { i, j } = sit;
      const gap = tr.U[j] - tr.U[i] - sit.base;
      if (gap < -2) { sit.done = true; sit.tDone = t; closed.push(sit); situations.delete(key); continue; }
      if (gap > 80 || t - sit.seen > 20 || tr.off[j] || tr.away[j]) { sit.why = gap > 80 ? 'gap' : t - sit.seen > 20 ? 'unseen' : 'off'; closed.push(sit); situations.delete(key); continue; }
      if (gap < 30) {
        const s0 = prevS[i], s1 = tr.s[i];
        for (const C of corners) {
          if (!C.passable) continue;
          const crossed = s0 <= s1 ? s0 < C.brake && C.brake <= s1 : C.brake > s0 || C.brake <= s1;
          if (!crossed) continue;
          sit.brakeZone = true;
          const inside = (tr.lat[i] - line.at(line.off, s1)) * C.dir;
          if (inside > 1.0) sit.setup = true;
        }
      }
    }
    for (let i = 0; i < n; i++) prevS[i] = tr.s[i];
    // marshal resets (stuck > 4 s / wrong way > 2.5 s): where (the car's station after the reset) and when
    for (let i = 0; i < n; i++) if (cars[i].recoveries !== prevRec[i]) { prevRec[i] = cars[i].recoveries; if (cars[i].driver) recoveryAt.push({ s: Math.round(tr.s[i]), t: +dir.time.toFixed(1), car: cars[i].number, phase: dir.phase }); }
    if (opts.log && steps % 60000 === 0) { const hh = dir.hud(); console.log(`t ${t.toFixed(0)} ${hh.phase} lap ${hh.lap} ${(ms * 1000 / steps / n).toFixed(2)} µs/car-step`); }
  }
  for (const s of situations.values()) { s.why = 'end'; closed.push(s); }
  let carLaps = 0;
  if (Ugreen) for (let i = 0; i < n; i++) if (cars[i].driver) carLaps += Math.max(0, tr.U[i] - Ugreen[i]) / L;
  const real = closed.filter((s) => !Number.isNaN(s.tClose));
  const stuck = real.filter((s) => s.done).map((s) => s.tDone - s.tClose);
  const byCorner: Record<string, number> = {};
  let wide = 0, spin = 0;
  for (const e of anyDir.mishapLog ?? []) { byCorner[e.corner] = (byCorner[e.corner] ?? 0) + 1; if (e.kind === 'spin') spin++; else wide++; }
  const totalM = (anyDir.mishapLog ?? []).length;
  const ls = losses.map((l) => l.loss);
  const usPerStep = ms * 1000 / steps;
  return {
    cars: n, laps: dir.config.laps, carLaps, raceTime: dir.time,
    line: { instRms: inst.rms(), instP95: inst.pct(0.95), why: Object.fromEntries([...why].map(([k, v]) => [k, +(v / Math.max(1, all.n)).toFixed(4)])), rms: all.rms(), p95: all.pct(0.95), samples: all.n, trackRms: trk.rms(), trackP95: trk.pct(0.95), maxErr, worstAt, corners: corners.map((c, k) => ({ name: c.name, rms: cornerAcc[k].rms(), p95: cornerAcc[k].pct(0.95), samples: cornerAcc[k].n })) },
    passing: { attempts: passStarts, ends: passEnds, situations: real.length, reachedBrakeZone: real.filter((s) => s.brakeZone).length, setUp: real.filter((s) => s.setup).length, completed: real.filter((s) => s.done).length, medianStuck: median(stuck), p90Stuck: pctl(stuck, 0.9), passesTotal, passAt,
      byRatio: [[0, 0.85], [0.85, 0.92], [0.92, CLEAR]].map(([lo, hi]) => {
        const g = real.filter((s) => { const r = tr.pace[s.i] / tr.pace[s.j]; return r >= lo && r < hi; });
        const open: Record<string, number> = {};
        for (const s of g) if (!s.done) open[s.why ?? '?'] = (open[s.why ?? '?'] ?? 0) + 1;
        return { lo, hi, fails: g.filter((s) => !s.done).map((s) => `${cars[s.i].number}>${cars[s.j].number} ${s.why} t${s.tClose.toFixed(0)}-${s.seen.toFixed(0)}`), situations: g.length, completed: g.filter((s) => s.done).length, medianStuck: median(g.filter((s) => s.done).map((s) => s.tDone - s.tClose)), open };
      }) },
    defending: defend,
    rules: { contacts, contactsPerCarLap: contacts / Math.max(1e-9, carLaps), hardContacts: hard, fourOff, fourOffMishap, fourOffPerCarLap: fourOff / Math.max(1e-9, carLaps), fourOffNonMishapPerCarLap: (fourOff - fourOffMishap) / Math.max(1e-9, carLaps), formationPasses, recoveries: dir.recoveries, fourOffAt, contactAt, recoveryAt },
    mishaps: { total: totalM, perCarLap: totalM / Math.max(1e-9, carLaps), wide, spin, byCorner, lossMedian: median(ls), lossMin: ls.length ? Math.min(...ls) : NaN, lossMax: ls.length ? Math.max(...ls) : NaN, losses },
    cost: { usPerStep, usPerCar: usPerStep / n },
  };
}

export function printReport(m: SelfplayMetrics): void {
  const f = (x: number, d = 2) => (Number.isFinite(x) ? x.toFixed(d) : '-');
  console.log(`\n=== self-play: ${m.cars} cars, ${m.laps} laps, ${f(m.carLaps, 1)} car-laps (green), race time ${f(m.raceTime, 0)} s`);
  console.log(`(a) line when alone (>= 2 s with nobody within 30 m): rms ${f(m.line.rms)} m, p95 ${f(m.line.p95)} m (${m.line.samples} samples)   [target rms < 0.5]; with no deliberate offset: rms ${f(m.line.trackRms)} p95 ${f(m.line.trackP95)}; worst ${f(m.line.maxErr)} m at s ${f(m.line.worstAt, 0)}; instantaneous (any moment nobody within 30 m) rms ${f(m.line.instRms)} p95 ${f(m.line.instP95)}`);
  for (const c of m.line.corners) console.log(`      ${c.name.padEnd(13)} rms ${f(c.rms)}  p95 ${f(c.p95)}  n ${c.samples}`);
  const p = m.passing;
  console.log(`(b) clearly faster (>3 %) behind a car: ${p.situations} situations, ${p.reachedBrakeZone} reached a passable braking zone close, ${p.setUp} set up on the inside, ${p.completed} completed; stuck median ${f(p.medianStuck, 1)} s, p90 ${f(p.p90Stuck, 1)} s; all green passes ${p.passesTotal}; pass attempts ${p.attempts}, ended ${JSON.stringify(p.ends)}`);
  console.log(`    by pace ratio: ${p.byRatio.map((b) => `${b.lo}-${b.hi}: ${b.completed}/${b.situations} (${b.situations ? Math.round(100 * b.completed / b.situations) : '-'} %, stuck ${f(b.medianStuck, 1)} s, not done ${JSON.stringify(b.open)})`).join(', ')}`);
  const d = m.defending;
  console.log(`(c) defensive moves: vs clearly faster ${d.vsClearlyFaster}, within 3 % ${d.within3}, vs slower ${d.vsSlower}, nobody close ${d.none}   [vs clearly faster ~0]`);
  const r = m.rules;
  console.log(`(d) contacts (>1 m/s, AI-AI, per pair per 1 s) ${r.contacts} = ${f(r.contactsPerCarLap, 3)} per car-lap (>3 m/s: ${r.hardContacts}) [<= 0.02]; four-off ${r.fourOff} (${r.fourOffMishap} from mishaps) = ${f(r.fourOffPerCarLap, 3)} per car-lap, non-mishap ${f(r.fourOffNonMishapPerCarLap, 3)}; formation passes ${r.formationPasses}; recoveries ${r.recoveries}`);
  const mi = m.mishaps;
  console.log(`(e) mishaps ${mi.total} = ${f(mi.perCarLap, 4)} per car-lap (wide ${mi.wide}, spin ${mi.spin}); loss median ${f(mi.lossMedian, 1)} s [${f(mi.lossMin, 1)}..${f(mi.lossMax, 1)}]; by corner ${JSON.stringify(mi.byCorner)}`);
  console.log(`(f) cost ${f(m.cost.usPerStep, 1)} µs per step, ${f(m.cost.usPerCar)} µs per car`);
}
