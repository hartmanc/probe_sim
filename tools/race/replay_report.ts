// The reports of tools/race/replay_race.ts: one race as markdown, and the aggregate over a directory of re-runs (human attacker
// against the AI attackers in the same races, the owner's recordings apart from the public's). Pure: strings in, strings out.
import type { Analysis, PassRow, CheckReport } from './replay_core';
import { curves, D_BINS, G_BINS, wilson, type Curves, type Pair } from './traffic_curves';
import { median, quantile } from './pace_rules';

const f1 = (x: number | null | undefined): string => (x === null || x === undefined || !Number.isFinite(x) ? '-' : x.toFixed(1));
const f2 = (x: number | null | undefined): string => (x === null || x === undefined || !Number.isFinite(x) ? '-' : x.toFixed(2));
const pc = (x: number): string => (Number.isFinite(x) ? (100 * x).toFixed(1) : '-');

export interface RaceFile { name: string; check: CheckReport; analysis: Analysis }

const atPass = (p: PassRow) => p.other.find((s) => s.dt === 0) ?? p.other[p.other.length - 1];

export function raceMd(name: string, check: CheckReport, a: Analysis): string {
  const L: string[] = [];
  L.push(`# ${name}`, '');
  L.push(`${a.trackId} · seed ${a.seed} · ${a.raceLaps} laps · ${a.owner ? 'owner' : 'public'}${a.aborted ? ' · aborted' : ''} · ${a.steps} steps (${(a.steps / 1000).toFixed(0)} s)`);
  L.push('', `**Check: ${check.ok ? 'passed' : 'FAILED'}** (config ${check.config ? 'ok' : 'differs'}, live lap times and crossings ${check.live ? 'ok' : 'differ'}, snapshots ${check.snapshot === null ? 'none' : check.snapshot ? 'ok' : 'differ'})`);
  for (const m of check.mismatches) L.push(`- mismatch: ${m}`);
  for (const m of check.problems) L.push(`- ${m}`);
  const s = a.summary;
  L.push('', '## Summary', '', `- Player best lap ${f2(s.playerBest)} s; field median of best laps ${f2(s.fieldMedianBest)} s; rank by best lap ${s.rankByBest ?? '-'} of ${s.cars}; finish ${s.finishPosition || '-'}`);
  L.push(`- Passes made ${s.passesMade}, received ${s.passesReceived}; AI waits behind the player ${a.waits.length}; contacts with the player ${a.contacts.length}; four wheels off ${a.fourOffs.length}`);
  L.push('', '## Player laps', '', '| lap | time s | field median s |', '|---|---|---|');
  for (const l of a.playerLaps) L.push(`| ${l.lap} | ${f2(l.time)} | ${f2(l.fieldMedian)} |`);
  L.push('', '## Passes', '', 'Gap and closing are over the 5 s before the pass; "other" is the car passed (made) or the car that passed the player (received) at the moment of the pass: lane-model state, speed over its own profile, throttle / brake, what capped it.', '');
  L.push('| t s | lap | kind | car | where | side | pace ratio | gap -5 s m | closing m/s | behind s | other: state | v / profile | thr | brk | limiter | e | target e | player v | player e |');
  L.push('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|');
  for (const p of a.passes) {
    const o = atPass(p), me = p.player.find((x) => x.dt === 0) ?? p.player[p.player.length - 1];
    L.push(`| ${f1(p.t)} | ${p.lap} | ${p.kind} | #${p.car} | ${p.where} | ${p.side} | ${f2(p.paceRatio)} | ${f1(p.gap5)} | ${f1(p.closing5)} | ${f1(p.behindS)} | ${o.lane} | ${f2(o.vOver)} | ${f2(o.thr)} | ${f2(o.brk)} | ${o.limiter ?? '-'} | ${f2(o.e)} | ${f2(o.eT)} | ${f1(me?.v)} | ${f2(me?.e)} |`);
  }
  if (!a.passes.length) L.push('| (none) |');
  L.push('', '## AI waits behind the player', '', 'A clearly faster AI car (pace hint 3 % or more) arriving within 25 m behind the player until it is ahead.', '', '| car | from t s | duration s | ended | pace ratio |', '|---|---|---|---|---|');
  for (const w of a.waits) L.push(`| #${w.car} | ${f1(w.t0)} | ${f1(w.dur)} | ${w.ended} | ${f2(w.paceRatio)} |`);
  if (!a.waits.length) L.push('| (none) |');
  L.push('', '## Contacts with the player', '', '| t s | car | closing m/s | where |', '|---|---|---|---|');
  for (const c of a.contacts) L.push(`| ${f1(c.t)} | #${c.car} | ${f1(c.closing)} | ${c.where} (s ${c.s}) |`);
  if (!a.contacts.length) L.push('| (none) |');
  L.push('', '## Four wheels off', '', '| t s | where |', '|---|---|');
  for (const c of a.fourOffs) L.push(`| ${f1(c.t)} | ${c.where} (s ${c.s}) |`);
  if (!a.fourOffs.length) L.push('| (none) |');
  return L.join('\n') + '\n';
}

// ---------------------------------------------------------------- aggregate

const GAP_BINS: [number, number, string][] = [[0, 5, '0-5'], [5, 10, '5-10'], [10, 20, '10-20'], [20, 40, '20-40'], [40, Infinity, '40+']];
const PHASES = ['straight', 'brake', 'entry', 'exit'] as const;
const SIDES = ['inside', 'outside', 'straight'] as const;

function group(files: RaceFile[], label: string): string[] {
  const L: string[] = [];
  const pass = files.flatMap((f) => f.analysis.passes);
  const made = pass.filter((p) => p.kind === 'made'), got = pass.filter((p) => p.kind === 'received');
  L.push(`### ${label}: ${files.length} race${files.length === 1 ? '' : 's'}, ${made.length} passes made, ${got.length} received`, '');
  if (!files.length) return [...L, '(none)', ''];
  L.push('Passes by corner phase and side (made / received):', '', `| phase | ${SIDES.join(' | ')} | all |`, '|---|---|---|---|---|');
  for (const ph of PHASES) {
    const cells = SIDES.map((sd) => `${made.filter((p) => p.phase === ph && p.side === sd).length} / ${got.filter((p) => p.phase === ph && p.side === sd).length}`);
    L.push(`| ${ph} | ${cells.join(' | ')} | ${made.filter((p) => p.phase === ph).length} / ${got.filter((p) => p.phase === ph).length} |`);
  }
  const state = (rows: PassRow[]) => {
    const at = rows.map(atPass);
    const cnt = new Map<string, number>(); for (const s of at) cnt.set(s.lane, (cnt.get(s.lane) ?? 0) + 1);
    const lim = new Map<string, number>(); for (const s of at) if (s.limiter) lim.set(s.limiter, (lim.get(s.limiter) ?? 0) + 1);
    const vo = at.map((s) => s.vOver).filter((x): x is number => x !== null);
    const thr = at.map((s) => s.thr), brk = at.map((s) => s.brk);
    const show = (m: Map<string, number>) => [...m].sort((x, y) => y[1] - x[1]).map(([k, v]) => `${k} ${v}`).join(', ') || '-';
    return `lane state: ${show(cnt)}; speed over own profile median ${f2(median(vo))} (quartiles ${f2(quantile(vo, 0.25))}-${f2(quantile(vo, 0.75))}); throttle median ${f2(median(thr))}, braking in ${pc(brk.filter((b) => b > 0.05).length / Math.max(1, brk.length))} %; capped by: ${show(lim)}`;
  };
  L.push('', `Passed car at the moment of a pass made: ${made.length ? state(made) : '-'}`, '', `Passing car at the moment of a pass received: ${got.length ? state(got) : '-'}`);
  L.push('', 'Gap 5 s before a pass made (m) and closing speed:', '', '| gap m | passes | median closing m/s | median time behind s |', '|---|---|---|---|');
  for (const [lo, hi, name] of GAP_BINS) {
    const b = made.filter((p) => p.gap5 !== null && p.gap5 >= lo && p.gap5 < hi);
    L.push(`| ${name} | ${b.length} | ${f1(median(b.map((p) => p.closing5).filter((x): x is number => x !== null)))} | ${f1(median(b.map((p) => p.behindS).filter((x): x is number => x !== null)))} |`);
  }
  const pairs = files.flatMap((f) => f.analysis.pairs);
  const me = '619';
  const human = pairs.filter((p) => p.x === me), ai = pairs.filter((p) => p.x !== me);
  L.push('', yardstick(human, ai), '');
  const waits = files.flatMap((f) => f.analysis.waits);
  const done = waits.filter((w) => w.ended === 'done');
  L.push(`AI waits behind the player: ${waits.length} (${done.length} ended in a pass), median ${f1(median(done.map((w) => w.dur)))} s, p90 ${f1(quantile(done.map((w) => w.dur), 0.9))} s`);
  const carLaps = files.reduce((n, f) => n + f.analysis.summary.cars * f.analysis.raceLaps, 0);
  L.push('', `Contacts with the player ${files.reduce((n, f) => n + f.analysis.contacts.length, 0)}, four wheels off ${files.reduce((n, f) => n + f.analysis.fourOffs.length, 0)} (${carLaps} car-laps in these races)`);
  return L;
}

function rates(c: Curves): string[] { return c.byD.map((r) => `${r.passed}/${r.n} = ${pc(r.rate)} % (${pc(r.lo)}-${pc(r.hi)})`); }

/** The pass-within-a-lap cells of the traffic yardstick (traffic_curves.ts): human attacker against the AI attackers, same races. */
function yardstick(human: Pair[], ai: Pair[]): string {
  const ch = curves(human), ca = curves(ai);
  const L: string[] = [`Yardstick cells (an attacker at the line with a car ahead within 10 s; passed within the next lap): human ${human.length} pairs, AI ${ai.length} pairs`, '',
    '| pace delta d (g < 2 s) | human | AI attackers |', '|---|---|---|'];
  const rh = rates(ch), ra = rates(ca);
  D_BINS.forEach((d, k) => L.push(`| ${d} | ${rh[k]} | ${ra[k]} |`));
  L.push('', '| gap g (d >= 3 %) | human | AI attackers |', '|---|---|---|');
  G_BINS.forEach((g, k) => { const a = ch.byG[k], b = ca.byG[k]; L.push(`| ${g} s | ${a.passed}/${a.n} = ${pc(a.rate)} % | ${b.passed}/${b.n} = ${pc(b.rate)} % |`); });
  void wilson;
  return L.join('\n');
}

export function aggregateMd(files: RaceFile[], title = 'Race recordings, aggregate'): string {
  const ok = files.filter((f) => f.check.ok), flagged = files.filter((f) => !f.check.ok);
  const L: string[] = [`# ${title}`, '', `${files.length} recordings re-run; ${ok.length} reproduced exactly, ${flagged.length} flagged and left out of the numbers.`, ''];
  if (flagged.length) { L.push('Flagged:', ''); for (const f of flagged) L.push(`- ${f.name}: ${f.check.problems[0] ?? f.check.mismatches[0] ?? 'differs'}`); L.push(''); }
  L.push(...group(ok.filter((f) => f.analysis.owner), 'Owner'), '', ...group(ok.filter((f) => !f.analysis.owner), 'Public'), '', ...group(ok, 'All'));
  return L.join('\n') + '\n';
}
