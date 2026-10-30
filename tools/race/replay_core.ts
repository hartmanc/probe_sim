// Offline re-run of a race recording (src/scoreboard/racerec.ts, docs/races.md) and the analysis of how the human player passed
// the AI and was passed. No file I/O (replay_race.ts does that), so the unit test drives it directly.
//
// The re-run builds the director exactly as the app's race does (src/app/race-build.ts buildDirector over the recording's
// build options), steps the same HotlapSim with the recorded 100 Hz samples and the between-step events, and CHECKS that the
// recording's live lap times, line crossings, classification and once-a-second positions come out identical. Only then are
// the passes trusted. With `analyse` it also samples every car at 10 Hz and writes the pass rows.
import { HotlapSim, STEP, type SimAssets } from '../../src/scoreboard';
import { AI_VERSION, type PaceJson } from '../../src/physics/ai/field';
import type { RaceCar, RaceDirector, RaceCrossing } from '../../src/physics/ai/race';
import { lineToWorld } from '../../src/physics';
import { PLAYER_NUMBER, buildDirector } from '../../src/app/race-build';
import { neighbourField } from '../../src/app/field-select';
import type { FieldData } from '../../src/app/loader';
import { decodeSnapshot, type RaceRecording } from '../../src/scoreboard/racerec';
import { RaceTap, configOf, liveOf } from '../../src/scoreboard/racetap';
import type { TraceRow } from '../../src/scoreboard/types';
import { makeWhere } from './selfplay_where';
import { median } from './pace_rules';
import { pairsWithDrops, type Pair } from './traffic_curves';
import { simRefs } from './traffic_sim';

// ---------------------------------------------------------------- results

export interface CheckReport {
  /** nothing differed: the re-run reproduced the recording */
  ok: boolean;
  /** why the re-run was refused or what differed, first divergence first */
  problems: string[];
  /** the version / build / config mismatches alone (a --force run reports them and goes on) */
  mismatches: string[];
  config: boolean; live: boolean; snapshot: boolean | null;
}

export type LaneState = 'human' | 'alone' | 'following' | 'pass phase' | 'making room' | 'lifting';
/** One car at one 10 Hz sample. `dt` is seconds from the pass. */
export interface CarSample {
  dt: number; s: number; e: number; v: number;
  /** the car's own target speed at its station (AI only), and v over it */
  vProf: number | null; vOver: number | null;
  thr: number; brk: number; steer: number | null;
  lane: LaneState; eT: number; limiter: string | null; passPhase: number; lead: number | null;
  /** distance along the race to the player, m (positive: this car is ahead); null on the player's own row */
  gap: number | null;
}
export interface PassRow {
  kind: 'made' | 'received';
  /** race time of the pass, s */
  t: number; lap: number;
  /** the AI car passed (made) or the AI car that passed the player (received) */
  car: string;
  s: number; where: string; phase: 'straight' | 'brake' | 'entry' | 'exit'; corner: string | null;
  side: 'inside' | 'outside' | 'straight';
  /** the other car's pace hint over the player's pace estimate (< 1: the AI car is the quicker) */
  paceRatio: number;
  /** gap (m, along the race, positive = the AI car ahead for a pass made) at -5 s, and the closing speed over the 5 s before, m/s */
  gap5: number | null; closing5: number | null;
  /** time spent within 20 m behind the car before the pass, s (passes made) */
  behindS: number | null;
  /** the other car's state (the passed car for a pass made) -5 s .. +5 s at 10 Hz, and the player's alongside */
  other: CarSample[]; player: CarSample[];
}
export interface Analysis {
  trackId: string; seed: number; laps: number; owner: boolean; aborted: boolean; steps: number;
  passes: PassRow[];
  waits: { car: string; t0: number; dur: number; ended: string; paceRatio: number }[];
  contacts: { t: number; car: string; closing: number; s: number; where: string }[];
  fourOffs: { t: number; s: number; where: string }[];
  laps: { lap: number; time: number; fieldMedian: number | null }[];
  summary: {
    playerBest: number | null; fieldMedianBest: number | null; rankByBest: number | null; cars: number;
    passesMade: number; passesReceived: number; finishPosition: number | null;
  };
  crossings: RaceCrossing[];
  pairs: Pair[];
}
export interface ReplayResult { check: CheckReport; analysis: Analysis | null; steps: number; wallS: number }

// ---------------------------------------------------------------- the re-run

export interface ReplayOptions {
  assets: SimAssets; pace: PaceJson; identity: unknown | null;
  /** the current tree's short sha; given, a recording from another build is refused ('' / absent: not checked) */
  currentSha?: string;
  /** go on although the version, build or config differ */
  force?: boolean;
  analyse?: boolean;
  /** stop after this many physics steps (tests) */
  maxSteps?: number;
}

const shaMatch = (a: string, b: string): boolean => !!a && !!b && (a.startsWith(b) || b.startsWith(a));

export function replayRecording(rec: RaceRecording, o: ReplayOptions): ReplayResult {
  const t0 = Date.now();
  const check: CheckReport = { ok: false, problems: [], mismatches: [], config: true, live: true, snapshot: null };
  const bad = (m: string): void => { check.problems.push(m); };
  const refuse = (m: string): ReplayResult => { bad(m); return { check, analysis: null, steps: 0, wallS: (Date.now() - t0) / 1000 }; };

  if (rec.v !== 1) return refuse(`recording format ${rec.v} is not one this tool reads`);
  if (rec.aiVersion !== String(AI_VERSION)) check.mismatches.push(`AI version: recorded ${rec.aiVersion}, this tree ${AI_VERSION}`);
  if (o.currentSha !== undefined && o.currentSha !== '' && !shaMatch(rec.buildSha, o.currentSha)) check.mismatches.push(`build: recorded ${rec.buildSha || '(unknown)'}, this tree ${o.currentSha}`);
  if (rec.trackId !== o.assets.trackId) return refuse(`track: recorded ${rec.trackId}, assets for ${o.assets.trackId}`);

  const b = rec.build;
  const sim = new HotlapSim(o.assets, { record: false, autoShift: b.autoShift, abs: b.abs, ref: b.ref });
  if (rec.physics !== sim.physics) check.mismatches.push(`physics version: recorded ${rec.physics}, this tree ${sim.physics}`);
  if (check.mismatches.length && !o.force) {
    return refuse(`refused: ${check.mismatches.join('; ')} (the recording is only exact on the tree and build it was made on; --force runs it anyway)`);
  }
  sim.launchUntil = 0;
  const pace = b.fieldCap !== null ? neighbourField(o.pace as unknown as { cars: { number: string; grid: number; targetLap: number; sigma?: number }[] }, b.fieldCap, PLAYER_NUMBER) as unknown as PaceJson : o.pace;
  const field = { pace, identity: o.identity, models: [], missing: [] } as unknown as FieldData;
  const dir = buildDirector(sim, field, { seed: b.seed, laps: b.laps, trackId: rec.trackId, realGrid: b.realGrid, playerAi: b.playerAi, lod: b.lod, strengthPct: b.strengthPct, closeRacing: b.closeRacing, planner: b.planner });
  sim.stepVehicle = (di) => dir.step(STEP, di as Parameters<RaceDirector['step']>[1]);

  // the effective config: a difference means this tree builds another race than the one recorded
  const cfg = configOf(dir);
  for (const k of new Set([...Object.keys(cfg), ...Object.keys(rec.config)])) {
    if (JSON.stringify(cfg[k]) !== JSON.stringify(rec.config[k])) { check.config = false; check.mismatches.push(`config.${k}: recorded ${JSON.stringify(rec.config[k])}, this tree ${JSON.stringify(cfg[k])}`); }
  }
  if (!check.config && !o.force) return refuse(`refused: ${check.mismatches.join('; ')}`);

  const tap = new RaceTap(sim, dir);
  const an = o.analyse ? new Analyzer(sim, dir, rec) : null;
  const rows = rec.inputs.rows, refs = rec.inputs.ref, events = rec.events;
  const limit = Math.min(rec.truncated?.atStep ?? rec.inputs.steps, o.maxSteps ?? Infinity, rec.inputs.steps);
  let ri = 0, fi = 0, ei = 0;
  while (sim.stepIndex < limit) {
    const k = sim.stepIndex;
    // between-step events apply before the step they were logged at (the app's recovery, the pit-exit cones)
    while (ei < events.length && events[ei][0] <= k) {
      const ev = events[ei++];
      if (ev[1] === 0) {
        const L = sim.assets.track.length_m, p = lineToWorld(sim.assets.track, () => 0, ((ev[2] % L) + L) % L);
        sim.vehicle.reset([p.pos[0], p.pos[1], p.pos[2]], p.heading, 0);
      } else dir.reportViolation(ev[2], ev[3]);
    }
    if (k % 10 === 0) {
      while (fi < refs.length && refs[fi][0] <= k) { sim.replayRef(refs[fi][1]); fi++; }
      if (fi === 0) sim.replayRef(null);
      while (ri + 1 < rows.length && rows[ri + 1][0] <= k) ri++;
      const row: TraceRow = rows[ri] ?? [0, 0, 0, 0, 0];
      sim.applyRow(row, row[0] === k);
    }
    sim.advance();
    tap.after();
    an?.afterStep();
  }

  // ---- the checks
  const live = liveOf(dir);
  const rl = rec.live;
  const same = (a: number, c: number): boolean => a === c || (Number.isNaN(a) && Number.isNaN(c));
  const liveBad: string[] = [];
  for (let i = 0; i < Math.max(live.lapTimes.length, rl.lapTimes.length); i++) {
    if (live.lapTimes[i] === undefined || rl.lapTimes[i] === undefined || !same(live.lapTimes[i], rl.lapTimes[i])) { liveBad.push(`player lap ${i + 1}: recorded ${rl.lapTimes[i]} s, re-run ${live.lapTimes[i]} s`); break; }
  }
  for (let i = 0; i < Math.max(live.crossings.length, rl.crossings.length); i++) {
    const a = rl.crossings[i], c = live.crossings[i];
    if (!a || !c || a.car !== c.car || a.lapNr !== c.lapNr || !same(a.t, c.t)) {
      liveBad.push(`crossing ${i + 1}: recorded ${a ? `#${a.car} lap ${a.lapNr} t ${a.t}` : 'none'}, re-run ${c ? `#${c.car} lap ${c.lapNr} t ${c.t}` : 'none'}`);
      break;
    }
  }
  if (rl.results) {
    const cr = live.results;
    if (!cr) liveBad.push('classification: recorded at the flag, the re-run has none');
    else for (let i = 0; i < Math.max(cr.length, rl.results.length); i++) {
      const a = rl.results[i], c = cr[i];
      if (!a || !c || a.number !== c.number || a.laps !== c.laps || a.time !== c.time) { liveBad.push(`classification row ${i + 1}: recorded ${JSON.stringify(a)}, re-run ${JSON.stringify(c)}`); break; }
    }
  }
  if (liveBad.length) { check.live = false; for (const m of liveBad) bad(`live data differs: ${m}`); }

  if (rec.snapshot) {
    const want = decodeSnapshot(rec.snapshot), got = tap.drain();
    check.snapshot = true;
    const n = Math.min(want.S.length, got.snapS.length);
    if (rec.snapshot.cars.join() !== dir.cars.map((c) => c.number).join()) { check.snapshot = false; bad('snapshot: the car list differs'); }
    else outer: for (let k = 0; k < n; k++) for (let i = 0; i < rec.snapshot.cars.length; i++) {
      if (want.S[k][i] !== got.snapS[k][i] || want.E[k][i] !== got.snapE[k][i]) {
        check.snapshot = false;
        bad(`snapshot differs at second ${k + 1}, car #${rec.snapshot.cars[i]}: recorded s ${(want.S[k][i] / 10).toFixed(1)} m e ${(want.E[k][i] / 10).toFixed(1)} m, re-run s ${(got.snapS[k][i] / 10).toFixed(1)} m e ${(got.snapE[k][i] / 10).toFixed(1)} m`);
        break outer;
      }
    }
    if (check.snapshot && got.snapS.length < want.S.length && !rec.truncated) { check.snapshot = false; bad(`snapshot: the recording has ${want.S.length} seconds, the re-run ${got.snapS.length}`); }
  }
  check.ok = check.problems.length === 0 && check.mismatches.length === 0;
  if (check.problems.length) check.ok = false;
  const analysis = an ? an.finish(check, limit) : null;
  return { check, analysis, steps: sim.stepIndex, wallS: (Date.now() - t0) / 1000 };
}

// ---------------------------------------------------------------- analysis

const TICK = 100;           // steps between samples (10 Hz)
const WIN = 50;             // ticks each side of a pass (5 s)
const PASS_NEAR = 50;       // m: the selfplay pass rule (selfplay_metrics passesTotal)
const CLEAR = 0.97;         // pace ratio: clearly faster
const WAIT_NEAR = 25, WAIT_DROP = 60;
const r2 = (x: number): number => Math.round(x * 100) / 100;
const F = 14;               // floats per car per tick

interface DrvLike { passPhase: number; passTarget: number; limiter: string; leadIdx: number; shift: number; input: { throttle: number; brake: number; steer: number }; needsRecovery?: boolean }

class Analyzer {
  private readonly tr: RaceDirector['traffic'];
  private readonly cars: RaceCar[];
  private readonly n: number;
  private readonly P: number;
  private readonly where: (s: number) => string;
  private readonly ring: Float32Array;       // WIN + 1 ticks of F floats per car
  private readonly times = new Float64Array(WIN + 1);
  private tickNo = 0;
  private readonly sign: Int8Array;
  private readonly behind: Float64Array;
  private pending: { row: PassRow; car: number; tickAt: number; pre: CarSample[]; prePl: CarSample[] }[] = [];
  private done: PassRow[] = [];
  private waitState = new Map<number, { t0: number }>();
  private waits: Analysis['waits'] = [];
  private contactsSeen = new Map<number, number>();
  private contacts: Analysis['contacts'] = [];
  private fourOffs: Analysis['fourOffs'] = [];
  private offFor = 0; private offFired = false;
  private readonly L: number;

  constructor(private readonly sim: HotlapSim, private readonly dir: RaceDirector, private readonly rec: RaceRecording) {
    this.tr = dir.traffic; this.cars = dir.cars; this.n = dir.cars.length; this.P = dir.player.idx; this.L = dir.line.L;
    this.where = makeWhere(dir.line);
    this.ring = new Float32Array((WIN + 1) * this.n * F);
    this.sign = new Int8Array(this.n);
    this.behind = new Float64Array(this.n);
  }

  /** Per physics step: contacts with the player. Per tick (10 Hz): the pass rule, the ring, the waits, the four-offs. */
  afterStep(): void {
    const dir = this.dir, tr = this.tr, P = this.P;
    for (let c = 0; c < dir.contactCount; c++) {
      const ev = dir.contacts[c];
      if ((ev.a !== P && ev.b !== P) || ev.closing <= 1 || dir.phase !== 'green') continue;
      const other = ev.a === P ? ev.b : ev.a, key = other;
      const last = this.contactsSeen.get(key) ?? -1e9;
      this.contactsSeen.set(key, dir.time);
      if (dir.time - last < 1) continue;
      this.contacts.push({ t: r2(dir.time), car: this.cars[other].number, closing: r2(ev.closing), s: Math.round(tr.s[P]), where: this.where(tr.s[P]) });
    }
    if (this.sim.stepIndex % TICK === 0) this.tick();
  }

  /** Where the AI car is in the lane model: lifting (being passed), making room, in a pass, following, alone. */
  private laneState(i: number, d: DrvLike | null): LaneState {
    if (!d) return 'human';
    const lim = d.limiter, tr = this.tr;
    if (lim === 'passed') return 'lifting';
    if (lim === 'yield' || lim === 'alongside') return 'making room';
    if (d.passPhase !== 0) return 'pass phase';
    if (Math.abs(tr.eT[i]) > 0.5 && !tr.off[i]) return 'making room';
    if (lim === 'follow' || d.leadIdx >= 0) return 'following';
    return 'alone';
  }

  private tick(): void {
    const tr = this.tr, dir = this.dir, n = this.n, P = this.P;
    const phase = dir.phase, t = dir.time;
    const slot = this.tickNo % (WIN + 1);
    this.times[slot] = t;
    // the ring: every car's compact state at this tick
    for (let i = 0; i < n; i++) {
      const o = (slot * n + i) * F, c = this.cars[i], d = c.driver as unknown as DrvLike | null, prof = tr.profile[i];
      this.ring[o] = tr.s[i]; this.ring[o + 1] = tr.e[i]; this.ring[o + 2] = tr.v[i]; this.ring[o + 3] = prof ? this.dir.line.at(prof, tr.s[i]) : -1;
      const inp = i === P ? this.sim.input : d?.input;
      this.ring[o + 4] = inp?.throttle ?? 0; this.ring[o + 5] = inp?.brake ?? 0; this.ring[o + 6] = i === P ? this.sim.input.steer : 0;
      this.ring[o + 7] = ['human', 'alone', 'following', 'pass phase', 'making room', 'lifting'].indexOf(i === P ? 'human' : this.laneState(i, d));
      this.ring[o + 8] = tr.eT[i];
      this.ring[o + 9] = d ? limCode(d.limiter) : -1; this.ring[o + 10] = d ? d.passPhase : 0; this.ring[o + 11] = d ? d.leadIdx : -1;
      this.ring[o + 12] = tr.U[i] - tr.U[P]; this.ring[o + 13] = tr.off[i];
    }
    // pending passes collect the next 5 s
    for (const p of this.pending) {
      const k = this.tickNo - p.tickAt;
      p.row.other.push(this.fromRing(p.car, slot, k / 10, p.car)); p.row.player.push(this.fromRing(P, slot, k / 10, p.car));
    }
    this.pending = this.pending.filter((p) => {
      if (this.tickNo - p.tickAt >= WIN) { this.done.push(p.row); return false; }
      return true;
    });
    if (phase === 'green' || phase === 'formation') {
      for (let j = 0; j < n; j++) {
        if (j === P) continue;
        const now: 1 | -1 = tr.U[P] > tr.U[j] ? 1 : -1, was = this.sign[j];
        this.sign[j] = now;
        if (was === 0 || phase !== 'green') continue;
        // the pass rule of selfplay_metrics (from behind to ahead within 50 m of a running car), for the pairs with the player
        if (was === -1 && now === 1 && Math.abs(tr.U[P] - tr.U[j]) < PASS_NEAR && !tr.off[j] && !tr.away[j] && tr.v[j] > 5 && !(this.cars[j].driver as unknown as DrvLike | null)?.needsRecovery) this.pass('made', j, P, j);
        else if (was === 1 && now === -1 && Math.abs(tr.U[P] - tr.U[j]) < PASS_NEAR && !tr.off[P] && !tr.away[P] && tr.v[P] > 5) this.pass('received', j, j, P);
      }
      if (phase === 'green') for (let j = 0; j < n; j++) { if (j !== P && this.sign[j] === -1 && tr.U[j] - tr.U[P] > 0 && tr.U[j] - tr.U[P] < 20) this.behind[j] += 0.1; }
    }
    // the wait: a clearly faster AI car arriving within 25 m behind the player until it is ahead (or dropped back / the player is off)
    if (phase === 'green') for (let j = 0; j < n; j++) {
      if (j === P) continue;
      const gap = tr.U[P] - tr.U[j], faster = tr.pace[j] < CLEAR * tr.pace[P], w = this.waitState.get(j);
      if (!w) { if (faster && gap > 0 && gap < WAIT_NEAR && !tr.off[P] && tr.v[P] > 5) this.waitState.set(j, { t0: t }); continue; }
      const end = gap < 0 ? 'done' : gap > WAIT_DROP ? 'dropped' : tr.off[P] ? 'player off' : null;
      if (end) { this.waits.push({ car: this.cars[j].number, t0: r2(w.t0), dur: r2(t - w.t0), ended: end, paceRatio: r2(tr.pace[j] / tr.pace[P]) }); this.waitState.delete(j); }
    }
    // four wheels off for 0.25 s
    const st = dir.player.vehicle.state;
    if (phase === 'green' && st.wheels.every((w) => !w.onTrack)) { this.offFor += 0.1; if (this.offFor >= 0.25 && !this.offFired) { this.offFired = true; this.fourOffs.push({ t: r2(t), s: Math.round(tr.s[P]), where: this.where(tr.s[P]) }); } } else { this.offFor = 0; this.offFired = false; }
    this.tickNo++;
  }

  private fromRing(i: number, slot: number, dtS: number, ref: number): CarSample {
    const o = (slot * this.n + i) * F, r = this.ring;
    const vProf = r[o + 3] >= 0 ? r[o + 3] : null;
    const isP = i === this.P;
    return {
      dt: r2(dtS), s: r2(r[o]), e: r2(r[o + 1]), v: r2(r[o + 2]), vProf: vProf === null ? null : r2(vProf), vOver: vProf ? r2(r[o + 2] / vProf) : null,
      thr: r2(r[o + 4]), brk: r2(r[o + 5]), steer: isP ? r2(r[o + 6]) : null,
      lane: LANES[r[o + 7]] ?? 'alone', eT: r2(r[o + 8]), limiter: r[o + 9] >= 0 ? LIMITERS[r[o + 9]] ?? '?' : null, passPhase: r[o + 10], lead: r[o + 11] >= 0 ? Number(this.cars[r[o + 11]]?.number) : null,
      gap: isP ? null : r2(this.ring[(slot * this.n + ref) * F + 12]),
    };
  }

  /** A pass made (the player over car `other`) or received (the car over the player): the row, with the 5 s before from the ring. */
  private pass(kind: PassRow['kind'], other: number, passer: number, passed: number): void {
    const tr = this.tr, dir = this.dir, P = this.P, cur = this.tickNo % (WIN + 1);
    const s = tr.s[passer], w = this.where(s), phase = w === 'straight' ? 'straight' : (w.split(' ')[1] as PassRow['phase']);
    const corner = w === 'straight' ? null : w.split(' ')[0];
    const c = corner ? dir.line.corners.find((q) => q.name === corner) : null;
    const de = tr.e[passer] - tr.e[passed];
    const side: PassRow['side'] = !c ? 'straight' : (c.dir > 0 ? de > 0 : de < 0) ? 'inside' : 'outside';
    const pre: CarSample[] = [], prePl: CarSample[] = [];
    const have = Math.min(this.tickNo, WIN);
    for (let q = have; q >= 0; q--) {
      const sl = (cur - q + (WIN + 1) * 4) % (WIN + 1);
      pre.push(this.fromRing(other, sl, -q / 10, other)); prePl.push(this.fromRing(P, sl, -q / 10, other));
    }
    // gap5 / closing over the 5 s before, from the ring's gap column (positive: the AI car ahead of the player)
    const g0 = pre.length > 1 ? pre[0].gap : null, g1 = pre.length > 1 ? pre[pre.length - 1].gap : null;
    const span = (pre.length - 1) / 10;
    const row: PassRow = {
      kind, t: r2(dir.time), lap: Math.max(0, Math.floor(Math.max(0, tr.U[P]) / this.L)) + 1, car: this.cars[other].number,
      s: Math.round(s), where: w, phase, corner, side, paceRatio: r2(tr.pace[other] / tr.pace[P]),
      gap5: g0 === null ? null : r2(Math.abs(g0)), closing5: g0 === null || g1 === null || span <= 0 ? null : r2((Math.abs(g0) - Math.abs(g1)) / span),
      behindS: kind === 'made' ? r2(this.behind[other]) : null, other: pre, player: prePl,
    };
    if (kind === 'made') this.behind[other] = 0;
    this.pending.push({ row, car: other, tickAt: this.tickNo, pre, prePl });
    // the pass instant itself is the last of `pre`; the ticks after it are appended by tick()
  }

  finish(check: CheckReport, steps: number): Analysis {
    void check;
    for (const p of this.pending) this.done.push(p.row);
    this.pending = [];
    const passes = this.done.sort((a, b) => a.t - b.t);
    const crossings = this.dir.crossings.map((c) => ({ ...c }));
    const tag = (c: RaceCrossing) => c;
    const cr = crossings.map(tag);
    const { pairs } = pairsWithDrops(cr, simRefs(cr), { minLap: 30 });
    const me = this.dir.player.number;
    const byLap = new Map<number, number[]>();
    for (const c of cr) if (c.green && !c.pit && c.lapTime > 0 && c.lapNr >= 1) { const a = byLap.get(c.lapNr) ?? []; a.push(c.lapTime); byLap.set(c.lapNr, a); }
    const laps = cr.filter((c) => c.car === me && Number.isFinite(c.lapTime) && c.lapTime > 0).map((c) => ({ lap: c.lapNr, time: c.lapTime, fieldMedian: byLap.has(c.lapNr) ? r2(median(byLap.get(c.lapNr)!)) : null }));
    const best = new Map<string, number>();
    for (const c of cr) if (c.green && !c.pit && c.lapTime > 30 && c.lapNr > 1) best.set(c.car, Math.min(best.get(c.car) ?? Infinity, c.lapTime));
    const bests = [...best.values()].sort((a, b) => a - b), mine = best.get(me) ?? null;
    const res = this.dir.getResults();
    return {
      trackId: this.rec.trackId, seed: this.rec.seed, laps: this.rec.laps, owner: this.rec.owner, aborted: !!this.rec.aborted, steps,
      passes, waits: this.waits, contacts: this.contacts, fourOffs: this.fourOffs, laps, crossings: cr, pairs,
      summary: {
        playerBest: mine, fieldMedianBest: bests.length ? r2(median(bests)) : null, rankByBest: mine === null ? null : bests.indexOf(mine) + 1, cars: this.n,
        passesMade: passes.filter((p) => p.kind === 'made').length, passesReceived: passes.filter((p) => p.kind === 'received').length,
        finishPosition: res ? res.findIndex((r) => r.player) + 1 : null,
      },
    };
  }
}

const LANES: LaneState[] = ['human', 'alone', 'following', 'pass phase', 'making room', 'lifting'];
const LIMITERS = ['profile', 'cap', 'grip', 'offline', 'lane', 'mishap', 'follow', 'yield', 'rejoin', 'pinch', 'passed', 'alongside'];
const limCode = (name: string): number => { let k = LIMITERS.indexOf(name); if (k < 0) { LIMITERS.push(name); k = LIMITERS.length - 1; } return k; };
