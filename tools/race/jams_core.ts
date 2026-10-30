// Jam measurement (30 Oct 2026, "Jams" in src/physics/ai/NOTES.md): where the AI field bunches into queues, what the head of each
// queue is doing, and how far an AI brake application outside a braking zone travels back up the line. READ ONLY: it looks at the
// director's state after each step and changes nothing, so the replay's exactness check and the self-play numbers are untouched.
// Used by tools/race/replay_core.ts (`--jams` on replay_race.ts) and tools/race/jams_selfplay.ts.
import type { RaceDirector } from '../../src/physics/ai/race';
import { makeWhere } from './selfplay_where';
import { median, quantile } from './pace_rules';

const TICK = 100;            // steps between samples (10 Hz)
const DT = 0.1;
const JAM_FRAC = 0.5;        // jammed: speed under this share of the driver's own profile speed there
const GAP_TOL = 10;          // ticks (1 s) of not-jammed that still belong to one episode
const BRAKE_HIGH = 0.9;      // an AI brake application of this much or more outside a braking zone
const SHOCK_BACK = 250;      // m: cars behind within this distance are the ones a brake can reach
const SHOCK_T = 30;          // ticks (3 s) the following cars are watched
const SHOCK_BRAKE = 0.5;     // a follower "braked" at this much
const CHAIN_MAX = 80;
const START_S = 40;          // s after the green flag: the rolling start's own bunching is counted apart (a field accelerating from the formation)

interface DrvLike {
  passPhase: number; passTarget: number; limiter: string; leadIdx: number;
  input: { throttle: number; brake: number };
  mishap: string | null; offTrack: boolean; needsRecovery: boolean;
}

export interface Episode {
  car: string; t0: number; dur: number; s: number; where: string; lap: number;
  head: string; headState: string; queue: number; weight: number; ended: string;
  /** began in the first START_S seconds of green */
  start: boolean;
}
export interface BrakeRow { reason: string; n: number; shock: number[] }
export interface JamsResult {
  trackId: string; L: number; cars: number; laps: number; greenS: number;
  /** jammed car-seconds in all */
  jamS: number;
  /** car-seconds per 100 m of track, and the label most of them sit at */
  hist: number[]; histNames: string[];
  episodes: Episode[];
  /** per tick and head: how many jammed cars share that head */
  queues: number[];
  /** the first START_S s of green, counted apart from all of the above: jam car-seconds, by head state, the largest queue */
  start: { jamS: number; heads: Record<string, number>; maxQueue: number; episodes: number };
  /** car-seconds by the state of the head of the car's queue */
  heads: Record<string, number>;
  /** car-seconds whose chain to the head runs through a car that is itself passing another */
  throughPass: number;
  /** AI brake applications of 0.9+ outside a braking zone, by reason */
  brakes: BrakeRow[];
}

export class JamTracker {
  private readonly tr: RaceDirector['traffic'];
  private readonly cars: RaceDirector['cars'];
  private readonly n: number;
  private readonly L: number;
  private readonly where: (s: number) => string;
  private readonly human: Uint8Array;
  private readonly bmax: Float32Array;          // brake input maximum since the last tick
  private readonly ph: Uint8Array;               // 1: on a straight or a corner exit at this tick
  private readonly prevHigh: Uint8Array;
  private readonly jam: Uint8Array;
  private readonly open: ({ ep: Episode; last: number; pending: string | null; q: number } | null)[];
  private readonly episodes: Episode[] = [];
  private readonly nb = (): number => Math.ceil(this.L / 100);
  private readonly hist: number[];
  private readonly histLab: Map<string, number>[];
  private readonly queues: number[] = [];
  private readonly heads: Record<string, number> = {};
  private throughPass = 0;
  private greenT0 = NaN;
  private readonly startAcc = { jamS: 0, heads: {} as Record<string, number>, maxQueue: 0, episodes: 0 };
  private jamTicks = 0;
  private greenTicks = 0;
  private maxU = 0;
  private tickNo = 0;
  private pendBrake: { reason: string; tick: number; set: number[]; counted: Set<number> }[] = [];
  private readonly brakeRows = new Map<string, number[]>();

  constructor(private readonly dir: RaceDirector, private readonly trackId: string) {
    this.tr = dir.traffic; this.cars = dir.cars; this.n = dir.cars.length; this.L = dir.line.L;
    this.where = makeWhere(dir.line);
    this.human = Uint8Array.from(this.cars.map((c) => (c.isPlayer && !c.driver ? 1 : 0)));
    this.bmax = new Float32Array(this.n); this.ph = new Uint8Array(this.n); this.prevHigh = new Uint8Array(this.n); this.jam = new Uint8Array(this.n);
    this.open = new Array(this.n).fill(null);
    this.hist = new Array(this.nb()).fill(0);
    this.histLab = Array.from({ length: this.nb() }, () => new Map<string, number>());
  }

  private d(i: number): DrvLike | null { return this.cars[i].driver as unknown as DrvLike | null; }

  /** Per physics step: the brake maximum of every AI car (the driver's input changes between samples). */
  afterStep(stepIndex: number): void {
    for (let i = 0; i < this.n; i++) { const d = this.d(i); if (d && d.input.brake > this.bmax[i]) this.bmax[i] = d.input.brake; }
    if (stepIndex % TICK === 0) this.tick();
  }

  private free(s: number): boolean { const w = this.where(s); return w === 'straight' || w.endsWith(' exit'); }

  /** What the head of a queue is doing (the trigger). */
  private headState(h: number): string {
    const tr = this.tr, d = this.d(h);
    if (this.human[h] || !d) return 'the player';
    if (tr.off[h] || d.offTrack || d.needsRecovery) return 'off: stopped / spun / recovering';
    if (d.mishap !== null) return 'mishap slow phase (run wide)';
    const lim = d.limiter;
    if (lim === 'rejoin') return 'rejoining from off';
    if (lim === 'pinch') return 'pinch give-way';
    if (lim === 'alongside' || lim === 'passed') return 'making room for a passer (give-way / lift)';
    if (d.passPhase === 0 && Math.abs(tr.eT[h]) > 0.5 && !tr.off[h] && d.input.brake > 0.05) return 'making room (lane shift while braking)';
    if (d.passPhase !== 0) return `passing a car (limiter ${lim})`;
    if (lim === 'grip') return 'grip limiter';
    if (lim === 'lane' || lim === 'offline') return 'lane / off-line speed limit';
    if (lim === 'cap' || lim === 'yield') return `limiter ${lim}`;
    const prof = tr.profile[h] ? this.dir.line.at(tr.profile[h]!, tr.s[h]) : 0;
    if (lim === 'profile') return tr.v[h] < 0.8 * prof ? 'alone, slow on its own profile (accelerating)' : 'free, on its own pace (a slower car ahead of faster ones)';
    return `other (${lim})`;
  }

  /** Why an AI car brakes at 0.9+ outside a braking zone. */
  private brakeReason(i: number): string {
    const tr = this.tr, d = this.d(i)!;
    if (tr.off[i] || d.offTrack || d.needsRecovery || d.mishap !== null || d.limiter === 'mishap') return 'mishap / off';
    const lim = d.limiter;
    if (lim === 'rejoin') return 'rejoin from off';
    if (lim === 'alongside' || lim === 'passed') return 'making room for a passer';
    if (lim === 'pinch') return 'pinch guard';
    if (lim === 'follow') {
      const j = d.leadIdx, dj = j >= 0 ? this.d(j) : null;
      if (j < 0) return 'follow limiter: lead gone';
      if (this.human[j]) return 'follow limiter: lead is the player';
      if (tr.off[j] || (dj && (dj.offTrack || dj.needsRecovery || dj.mishap !== null))) return 'follow limiter: lead off / mishap';
      if (tr.v[j] < 3) return 'follow limiter: lead stopped';
      if (dj && dj.passPhase !== 0) return 'follow limiter: lead is passing';
      if (dj && dj.input.brake >= SHOCK_BRAKE) return 'follow limiter: lead braking (shockwave)';
      return 'follow limiter: lead moving';
    }
    if (lim === 'grip') return 'grip limiter';
    if (lim === 'lane' || lim === 'offline') return 'lane / off-line limit';
    if (lim === 'profile') return 'profile (corner approach outside the label)';
    return `other (${lim})`;
  }

  private tick(): void {
    const dir = this.dir, tr = this.tr, n = this.n, t = dir.time;
    this.tickNo++;
    const green = dir.phase === 'green';
    for (let i = 0; i < n; i++) this.ph[i] = this.free(tr.s[i]) ? 1 : 0;
    // ---- shockwaves already open: who among the cars behind braked since the last tick
    if (this.pendBrake.length) {
      this.pendBrake = this.pendBrake.filter((p) => {
        for (const c of p.set) if (!p.counted.has(c) && this.bmax[c] >= SHOCK_BRAKE && this.ph[c] && !tr.away[c]) p.counted.add(c);
        if (this.tickNo - p.tick >= SHOCK_T) { (this.brakeRows.get(p.reason) ?? this.brakeRows.set(p.reason, []).get(p.reason)!).push(p.counted.size); return false; }
        return true;
      });
    }
    if (!green) {
      for (let i = 0; i < n; i++) { this.closeAll(i, 'not green'); this.prevHigh[i] = 0; this.bmax[i] = 0; }
      return;
    }
    this.greenTicks++;
    if (Number.isNaN(this.greenT0)) this.greenT0 = t;
    const inStart = t - this.greenT0 < START_S;
    for (let i = 0; i < n; i++) if (tr.U[i] > this.maxU) this.maxU = tr.U[i];
    // ---- new brake applications (0.9+, on a straight or a corner exit)
    for (let i = 0; i < n; i++) {
      const d = this.d(i);
      if (!d || tr.away[i]) { this.prevHigh[i] = 0; continue; }
      const hi = this.bmax[i] >= BRAKE_HIGH ? 1 : 0;
      if (hi && !this.prevHigh[i] && this.ph[i]) {
        const set: number[] = [];
        for (let j = 0; j < n; j++) {
          if (j === i || this.human[j] || tr.away[j] || tr.off[j]) continue;
          const back = tr.U[i] - tr.U[j];
          if (back > 0 && back < SHOCK_BACK && this.bmax[j] < 0.3) set.push(j);
        }
        this.pendBrake.push({ reason: this.brakeReason(i), tick: this.tickNo, set, counted: new Set() });
      }
      this.prevHigh[i] = hi;
    }
    // ---- jammed cars
    this.jam.fill(0);
    for (let i = 0; i < n; i++) {
      const d = this.d(i);
      if (!d || this.human[i] || tr.away[i] || !this.ph[i]) continue;
      if (tr.off[i] || d.offTrack || d.needsRecovery || d.mishap !== null) continue;
      const prof = tr.profile[i];
      if (!prof) continue;
      const vp = dir.line.at(prof, tr.s[i]);
      if (vp > 5 && tr.v[i] < JAM_FRAC * vp) this.jam[i] = 1;
    }
    // queues: walk each jammed car forward along the follow chain to its head
    const qOf = new Map<number, number>();
    const headOf = new Int32Array(n).fill(-1), thru = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      if (!this.jam[i]) continue;
      let cur = i, through = false;
      for (let k = 0; k < CHAIN_MAX; k++) {
        const d = this.d(cur);
        if (this.human[cur] || !d || d.limiter !== 'follow' || d.leadIdx < 0) break;
        if (d.passPhase !== 0) through = true;
        cur = d.leadIdx;
      }
      headOf[i] = cur; thru[i] = through ? 1 : 0;
      qOf.set(cur, (qOf.get(cur) ?? 0) + 1);
    }
    for (const q of qOf.values()) { if (inStart) this.startAcc.maxQueue = Math.max(this.startAcc.maxQueue, q); else this.queues.push(q); }
    const bins = this.hist.length;
    for (let i = 0; i < n; i++) {
      const o = this.open[i];
      if (!this.jam[i]) {
        if (o) {
          if (o.pending === null) o.pending = this.endReason(i);
          if (this.tickNo - o.last > GAP_TOL) this.close(i);
        }
        continue;
      }
      const h = headOf[i], st = this.headState(h);
      if (inStart) { this.startAcc.jamS += DT; this.startAcc.heads[st] = (this.startAcc.heads[st] ?? 0) + DT; }
      else {
        this.jamTicks++;
        const b = Math.min(bins - 1, Math.floor(tr.s[i] / 100));
        this.hist[b] += DT;
        const lab = this.binName(tr.s[i]), m = this.histLab[b];
        m.set(lab, (m.get(lab) ?? 0) + 1);
        this.heads[st] = (this.heads[st] ?? 0) + DT;
        if (thru[i]) this.throughPass += DT;
      }
      const q = qOf.get(h) ?? 1;
      if (!o) {
        this.open[i] = { ep: { car: this.cars[i].number, t0: Math.round(t * 10) / 10, dur: 0, s: Math.round(tr.s[i]), where: this.where(tr.s[i]), lap: Math.max(0, Math.floor(tr.U[i] / this.L)) + 1, head: this.cars[h].number, headState: st, queue: q, weight: 0, ended: '', start: inStart }, last: this.tickNo, pending: null, q };
        this.open[i]!.ep.dur = DT;
      } else {
        o.ep.dur += DT * (this.tickNo - o.last); o.last = this.tickNo; o.pending = null;
        if (q > o.ep.queue) o.ep.queue = q;
      }
    }
    this.bmax.fill(0);
  }

  private endReason(i: number): string {
    const tr = this.tr, d = this.d(i)!;
    if (tr.away[i]) return 'pitted';
    if (tr.off[i] || d.offTrack || d.needsRecovery || d.mishap !== null) return 'went off / mishap';
    if (!this.ph[i]) return `reached ${this.where(tr.s[i])}`;
    return `speed recovered (limiter ${d.limiter}${d.passPhase ? ', in a pass' : ''})`;
  }

  private close(i: number): void {
    const o = this.open[i];
    if (!o) return;
    o.ep.ended = o.pending ?? 'race ended';
    o.ep.weight = Math.round(o.ep.dur * o.ep.queue * 10) / 10;
    o.ep.dur = Math.round(o.ep.dur * 10) / 10;
    if (o.ep.start) this.startAcc.episodes++; else this.episodes.push(o.ep);
    this.open[i] = null;
  }
  private closeAll(i: number, why: string): void { const o = this.open[i]; if (o) { if (o.pending === null) o.pending = why; this.close(i); } }

  finish(): JamsResult {
    for (let i = 0; i < this.n; i++) this.closeAll(i, 'race ended');
    for (const p of this.pendBrake) (this.brakeRows.get(p.reason) ?? this.brakeRows.set(p.reason, []).get(p.reason)!).push(p.counted.size);
    this.pendBrake = [];
    const nb = this.hist.length;
    return {
      trackId: this.trackId, L: this.L, cars: this.cars.filter((c) => !this.human[c.idx]).length, laps: Math.max(0.01, this.maxU / this.L), greenS: this.greenTicks * DT,
      jamS: this.jamTicks * DT, hist: this.hist.map((x) => Math.round(x * 10) / 10), histNames: Array.from({ length: nb }, (_, b) => [...this.histLab[b]].sort((x, y) => y[1] - x[1])[0]?.[0] ?? '-'), start: this.startAcc,
      episodes: this.episodes, queues: this.queues, heads: this.heads, throughPass: this.throughPass,
      brakes: [...this.brakeRows].map(([reason, shock]) => ({ reason, n: shock.length, shock })).sort((a, b) => b.n - a.n),
    };
  }

  /** The corner the 100 m bin sits in (phase label), or "straight after Tn" with the corner whose apex is the last one passed. */
  private binName(s: number): string {
    const w = this.where(s);
    if (w !== 'straight') return w;
    const C = this.dir.line.corners, L = this.L;
    let best = '', bd = Infinity;
    for (const c of C) { let d = s - c.apex; while (d < 0) d += L; if (d < bd) { bd = d; best = c.name; } }
    return best ? `straight after ${best}` : 'straight';
  }
}

// ---------------------------------------------------------------- report

const f1 = (x: number): string => (Number.isFinite(x) ? x.toFixed(1) : '-');
const f2 = (x: number): string => (Number.isFinite(x) ? x.toFixed(2) : '-');

export function jamsMd(r: JamsResult, title: string): string {
  const L: string[] = [`## Jams: ${title}`, ''];
  const carLaps = r.cars * r.laps;
  L.push(`${r.trackId}: ${r.cars} AI cars, ${f1(r.laps)} laps by the leader, ${f1(r.greenS)} s green. Jammed = an AI car on a straight or a corner exit (the pass table's phase labels) at under 50 % of its own profile speed there, no mishap, off or recovery of its own, in green.`, '');
  L.push(`- Jam car-seconds AFTER the first ${START_S} s of green: ${f1(r.jamS)} = ${f1(r.jamS / r.laps)} per race lap = ${f2(r.jamS / carLaps)} per car-lap (${f2(100 * r.jamS / (r.cars * (r.greenS - START_S)))} % of all car-time). Everything below is after the start window.`);
  const st = r.start, stTot = Object.values(st.heads).reduce((a, b) => a + b, 0);
  L.push(`- The first ${START_S} s of green (the rolling start, counted apart): ${f1(st.jamS)} jam car-seconds, ${st.episodes} episodes begun, largest queue ${st.maxQueue}; head states: ${Object.entries(st.heads).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([k, v]) => `${k} ${(100 * v / stTot).toFixed(0)} %`).join(', ') || '-'}`);
  const ep = r.episodes, long = ep.filter((e) => e.dur >= 3), durs = ep.map((e) => e.dur);
  L.push(`- Episodes (consecutive jammed samples of one car, gaps up to 1 s joined): ${ep.length}, of which ${long.length} last 3 s or more; duration median ${f1(median(durs))} s, p90 ${f1(quantile(durs, 0.9))} s, max ${f1(Math.max(0, ...durs))} s; ${f2(ep.length / carLaps)} per car-lap`);
  const q = r.queues;
  L.push(`- Queue size (jammed cars sharing one head, per 0.1 s sample): median ${f1(median(q))}, p90 ${f1(quantile(q, 0.9))}, max ${Math.max(0, ...q)}; samples with a queue of 3 or more: ${q.length ? (100 * q.filter((x) => x >= 3).length / q.length).toFixed(1) : '-'} %`);
  L.push(`- Jam car-seconds whose chain to the head runs through a car that is itself passing another: ${f1(r.throughPass)} s (${r.jamS ? (100 * r.throughPass / r.jamS).toFixed(1) : '-'} %)`);
  L.push('', 'Top five 100 m stations by jam car-seconds:', '', '| station (s m) | place | car-seconds | per lap |', '|---|---|---|---|');
  r.hist.map((x, b) => ({ x, b })).sort((a, b) => b.x - a.x).slice(0, 5).forEach(({ x, b }) => L.push(`| ${b * 100}-${b * 100 + 100} | ${r.histNames[b]} | ${f1(x)} | ${f2(x / r.laps)} |`));
  const tot = Object.values(r.heads).reduce((a, b) => a + b, 0);
  L.push('', 'Trigger: the state of the HEAD of the queue (the first car on the follow chain that is not itself capped by the car ahead), by jam car-seconds:', '', '| head state | car-seconds | share |', '|---|---|---|');
  for (const [k, v] of Object.entries(r.heads).sort((a, b) => b[1] - a[1])) L.push(`| ${k} | ${f1(v)} | ${(100 * v / tot).toFixed(1)} % |`);
  L.push('', 'Ten worst episodes (ranked by duration x peak queue size):', '', '| t s | lap | car | station | place | dur s | peak queue | head | head state at the start | ended |', '|---|---|---|---|---|---|---|---|---|---|');
  for (const e of [...ep].sort((a, b) => b.weight - a.weight).slice(0, 10)) L.push(`| ${f1(e.t0)} | ${e.lap} | #${e.car} | ${e.s} | ${e.where} | ${f1(e.dur)} | ${e.queue} | #${e.head} | ${e.headState} | ${e.ended} |`);
  if (!ep.length) L.push('| (none) |');
  L.push('', brakeMd(r));
  return L.join('\n') + '\n';
}

export function brakeMd(r: JamsResult): string {
  const L: string[] = ['AI brake applications of 0.9 or more outside a braking zone (straight or corner exit), by the driver\'s own reason; shockwave = cars within 250 m behind, not braking at the time, that brake at 0.5 or more on a straight or exit within the next 3 s:', '', '| reason | count | per lap | mean shockwave | median | max |', '|---|---|---|---|---|---|'];
  for (const b of r.brakes) L.push(`| ${b.reason} | ${b.n} | ${f2(b.n / r.laps)} | ${f2(b.shock.reduce((a, c) => a + c, 0) / b.n)} | ${f1(median(b.shock))} | ${Math.max(0, ...b.shock)} |`);
  const n = r.brakes.reduce((a, b) => a + b.n, 0), s = r.brakes.reduce((a, b) => a + b.shock.reduce((x, y) => x + y, 0), 0);
  L.push(`| all | ${n} | ${f2(n / r.laps)} | ${f2(n ? s / n : NaN)} | - | - |`);
  return L.join('\n');
}
