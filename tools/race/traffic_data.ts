// Traffic data stage (28 Oct 2026): the MyLaps lap rows of four 2026 Lemons races -> crossings -> tools/race/traffic_curves.ts
// -> tools/race/data/traffic/curves.json + REPORT.md.   npx tsx tools/race/traffic_data.ts [--track laguna|sonoma|buttonwillow|mid_ohio] [--out dir]
// Drivers are referred to by stint number only.
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { carPace, parseLap, median, quantile, robustSigma, MIN_STINT_LAPS } from './pace_rules';
import { ROOT } from './load';
import { pairsWithDrops, curves, perCar, wilson, D_BINS, G_BINS, gBin, dBin, type Crossing, type StintRef, type Pair, type Curves, type CarAggression, type Drops, type Q } from './traffic_curves';

export const EVENTS: Record<string, { dir: string; cls: string; label: string }> = {
  laguna: { dir: 'laps', cls: 'sessions_12975608_classification.json', label: 'Laguna Seca (Oct 2026)' },
  sonoma: { dir: 'sonoma/laps', cls: 'sonoma/sessions_11838772_classification.json', label: 'Sonoma (Mar 2026)' },
  buttonwillow: { dir: 'buttonwillow/laps', cls: 'buttonwillow/sessions_12906863_classification.json', label: 'Buttonwillow (Sep 2026)' },
  mid_ohio: { dir: 'mid_ohio/laps', cls: 'mid_ohio/sessions_11926749_classification.json', label: 'Mid-Ohio (Apr 2026)' },
};
const DATA = resolve(ROOT, 'tools/race/data');
const isoMs = (s: string): number => {
  const m = /^(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)(?:\.(\d+))?/.exec(s)!;
  return Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6], m[7] ? Math.round(+('0.' + m[7]) * 1000) : 0);
};

export interface StintDetail { index: number; fromLap: number; toLap: number; startT: number; endT: number; keep: number[]; keepLaps: number[]; ref: number; med: number; q80: number; sigma: number }
/** Stints under the rules of pace_rules.carPace (same clean-lap cuts), with the lap range and the laps kept. */
export function buildStints(laps: any[], official: number): StintDetail[] {
  const rows = laps.map((l: any) => {
    const st: string[] = Array.isArray(l.status) ? l.status : [l.status];
    const t = parseLap(l.lapTime);
    return { nr: l.lapNr as number, t, pit: !!l.inPit, ok: !l.inPit && st.length > 0 && st.every((x) => x === 'GREEN') && Number.isFinite(t) && t > 60, at: isoMs(l.timeOfDay) / 1000 };
  });
  const m0 = median(rows.filter((l) => l.ok).map((l) => l.t));
  const out: StintDetail[] = [];
  let run: { t: number; nr: number }[] = [], first = -1, last = -1, afterPit = true;
  const startOf = (nr: number) => { const r = rows.find((q) => q.nr === nr); return r ? r.at - (Number.isFinite(r.t) ? r.t : 0) : NaN; };
  const flush = () => {
    if (run.length) {
      const sm = median(run.map((r) => r.t));
      const keep = run.filter((r) => r.t <= 1.2 * sm && r.t <= 1.3 * m0 && r.t >= 0.97 * official);
      if (keep.length >= MIN_STINT_LAPS) {
        const ts = keep.map((r) => r.t);
        out.push({ index: out.length + 1, fromLap: first, toLap: last, startT: startOf(first), endT: rows.find((q) => q.nr === last)!.at, keep: ts, keepLaps: keep.map((r) => r.nr), ref: quantile(ts, 0.2), med: median(ts), q80: quantile(ts, 0.8), sigma: robustSigma(ts) });
      }
    }
    run = []; first = -1;
  };
  for (const l of rows) {
    if (l.pit) { flush(); afterPit = true; continue; }
    last = l.nr;
    if (afterPit) { afterPit = false; first = l.nr; continue; }
    if (first < 0) first = l.nr;
    if (l.ok) run.push({ t: l.t, nr: l.nr });
  }
  flush();
  return out;
}

export interface CarMeta { id: string; number: string; team: string; cls: string; startPos: number; finishPos: number; laps: number; medianRef: number; paceRank: number }
export interface EventData { id: string; crossings: Crossing[]; refs: StintRef[]; cars: CarMeta[]; stints: Map<string, StintDetail[]>; positionGains: number; positionLosses: number; pitReading: { pitLaps: number; pitLapMedianRatio: number; nextLapMedianRatio: number; pitLapsLongerThan15: number }; stintMismatch: number; origin: number }

export function loadEvent(id: string): EventData {
  const ev = EVENTS[id];
  const cls = JSON.parse(readFileSync(resolve(DATA, ev.cls), 'utf8'));
  const files = readdirSync(resolve(DATA, ev.dir)).filter((f) => /^pos\d+\.json$/.test(f)).sort();
  const raw = files.map((f) => ({ f, j: JSON.parse(readFileSync(resolve(DATA, ev.dir, f), 'utf8')) }));
  let origin = Infinity;
  for (const { j } of raw) for (const l of j.laps) origin = Math.min(origin, isoMs(l.timeOfDay));
  const crossings: Crossing[] = [], refs: StintRef[] = [], cars: CarMeta[] = [], stints = new Map<string, StintDetail[]>();
  let gains = 0, losses = 0, stintMismatch = 0;
  const pitRatios: number[] = [], nextRatios: number[] = [];
  for (const { f, j } of raw) {
    const car = f.replace('.json', '');
    const pi = j.lapDataInfo.participantInfo;
    const row = cls.rows.find((r: any) => r.position === pi.fieldFinishPos) ?? cls.rows.find((r: any) => String(r.startNumber) === String(pi.startNr));
    const official = row ? parseLap(row.bestTime) : 0;
    const laps: any[] = j.laps;
    if (!laps.length) continue;
    let prevPos = -1, prevNr = -1;
    const med = median(laps.filter((l) => !l.inPit && (Array.isArray(l.status) ? l.status : [l.status]).every((x: string) => x === 'GREEN')).map((l) => parseLap(l.lapTime)));
    laps.forEach((l, i) => {
      const st: string[] = Array.isArray(l.status) ? l.status : [l.status];
      crossings.push({ car, lapNr: l.lapNr, t: (isoMs(l.timeOfDay) - origin) / 1000, lapTime: parseLap(l.lapTime), green: st.length > 0 && st.every((x) => x === 'GREEN'), pit: !!l.inPit });
      const pos = l.fieldComparison?.position;
      if (l.lapNr === prevNr + 1 && !l.inPit && !laps[i - 1].inPit && typeof pos === 'number' && prevPos > 0) { if (pos < prevPos) gains += prevPos - pos; else if (pos > prevPos) losses += pos - prevPos; }
      prevPos = typeof pos === 'number' ? pos : -1; prevNr = l.lapNr;
      if (l.inPit) { pitRatios.push(parseLap(l.lapTime) / med); const n = laps[i + 1]; if (n && n.lapNr === l.lapNr + 1) nextRatios.push(parseLap(n.lapTime) / med); }
    });
    const sts = buildStints(laps, official);
    const cp = carPace(laps, official, undefined, 0.2).stints;
    if (cp.length !== sts.length || cp.some((s, k) => Math.abs(s.targetLap - sts[k].ref) > 0.0006 || s.laps !== sts[k].keep.length)) stintMismatch++;
    stints.set(car, sts);
    for (const s of sts) refs.push({ car, fromLap: s.fromLap, toLap: s.toLap, ref: s.ref });
    cars.push({ id: car, number: String(pi.startNr), team: pi.name, cls: pi.class, startPos: pi.startPos, finishPos: pi.fieldFinishPos, laps: laps.length, medianRef: sts.length ? median(sts.map((s) => s.ref)) : NaN, paceRank: 0 });
  }
  const ranked = cars.filter((c) => Number.isFinite(c.medianRef)).sort((a, b) => a.medianRef - b.medianRef);
  ranked.forEach((c, i) => { c.paceRank = i + 1; });
  return { id, crossings, refs, cars, stints, positionGains: gains, positionLosses: losses, stintMismatch, origin,
    pitReading: { pitLaps: pitRatios.length, pitLapMedianRatio: median(pitRatios), nextLapMedianRatio: median(nextRatios), pitLapsLongerThan15: pitRatios.filter((r) => r > 1.5).length / pitRatios.length } };
}

export interface ProbeStint { stint: number; fromLap: number; toLap: number; start: string; end: string; cleanLaps: number; ref: number; median: number; q80: number; sigma: number; passesPerLap: number; passedPerLap: number; lostPerLap: number; rookie: boolean }
export interface Probe { car: string; team: string; stints: ProbeStint[]; rookieFactorRef: number | null; rookieFactorMedian: number | null; rookiePassesPerLap: number | null; othersPassesPerLap: number | null; rookiePassedPerLap: number | null; othersPassedPerLap: number | null; rookiePassedMore: boolean | null; rookiePassesFewer: boolean | null }
const hhmm = (sec: number, _origin: number) => new Date(sec * 1000).toISOString().slice(0, 16).replace('T', ' ');

export interface EventSummary { label: string; cars: number; crossings: number; drops: Drops; medianGap: number; floor: { n: number; passed: number; rate: number }; crosscheck: { myPasses: number; positionGains: number; positionLosses: number; pairsUsable: number }; pitReading: EventData['pitReading']; stintMismatch: number; curves: Curves; probe: Probe | null }

export function analyse(ed: EventData): { pairs: Pair[]; summary: EventSummary } {
  const { pairs, drops } = pairsWithDrops(ed.crossings, ed.refs, { minLap: 60 });
  const c = curves(pairs);
  const floorP = pairs.filter((p) => p.d < 0 && p.g < 2);
  const meta = ed.cars.find((m) => m.number === '619');
  let probe: Probe | null = null;
  if (meta) {
    const sts = ed.stints.get(meta.id) ?? [];
    const mk = (s: typeof sts[number]): ProbeStint => {
      const n = s.keep.length;
      return { stint: s.index, fromLap: s.fromLap, toLap: s.toLap, start: hhmm(s.startT, ed.origin), end: hhmm(s.endT, ed.origin), cleanLaps: n, ref: s.ref, median: s.med, q80: s.q80, sigma: s.sigma,
        passesPerLap: pairs.filter((p) => p.x === meta.id && p.outcome === 'passed' && p.lap >= s.fromLap && p.lap <= s.toLap).length / n,
        passedPerLap: pairs.filter((p) => p.y === meta.id && p.outcome === 'passed' && p.yLap >= s.fromLap && p.yLap <= s.toLap).length / n,
        lostPerLap: s.keep.reduce((a, b) => a + b, 0) / n - s.ref, rookie: false };
    };
    const rows = sts.map(mk);
    let rf: number | null = null, rm: number | null = null, rp: number | null = null, op: number | null = null, rq: number | null = null, oq: number | null = null;
    if (rows.length >= 2) {
      const ri = rows.reduce((b, r, i) => (r.ref > rows[b].ref ? i : b), 0);
      rows[ri].rookie = true;
      const others = rows.filter((_, i) => i !== ri), oS = sts.filter((_, i) => i !== ri);
      rf = rows[ri].ref / median(others.map((r) => r.ref)); rm = rows[ri].median / median(others.map((r) => r.median));
      const nO = others.reduce((a, r) => a + r.cleanLaps, 0);
      rp = rows[ri].passesPerLap; op = others.reduce((a, r) => a + r.passesPerLap * r.cleanLaps, 0) / nO;
      rq = rows[ri].passedPerLap; oq = others.reduce((a, r) => a + r.passedPerLap * r.cleanLaps, 0) / nO;
      void oS;
    }
    probe = { car: meta.id, team: meta.team, stints: rows, rookieFactorRef: rf, rookieFactorMedian: rm, rookiePassesPerLap: rp, othersPassesPerLap: op, rookiePassedPerLap: rq, othersPassedPerLap: oq, rookiePassedMore: rq !== null ? rq > oq! : null, rookiePassesFewer: rp !== null ? rp < op! : null };
  }
  return { pairs, summary: { label: EVENTS[ed.id].label, cars: ed.cars.length, crossings: ed.crossings.length, drops, medianGap: median(pairs.map((p) => p.g)),
    floor: { n: floorP.length, passed: floorP.filter((p) => p.outcome === 'passed').length, rate: floorP.filter((p) => p.outcome === 'passed').length / floorP.length },
    crosscheck: { myPasses: pairs.filter((p) => p.outcome === 'passed').length, positionGains: ed.positionGains, positionLosses: ed.positionLosses, pairsUsable: pairs.length },
    pitReading: ed.pitReading, stintMismatch: ed.stintMismatch, curves: c, probe } };
}

const R = (k: string, v: unknown) => (typeof v === 'number' ? (Number.isFinite(v) ? Math.round(v * 10000) / 10000 : null) : v);
export const toJson = (o: unknown) => JSON.stringify(o, R as any, 1);

// ---------- report ----------
const pc = (x: number, d = 1) => (Number.isFinite(x) ? (100 * x).toFixed(d) + '%' : '-');
const qs = (q: Q) => (q.n ? `${q.med.toFixed(1)} [${q.q1.toFixed(1)}, ${q.q3.toFixed(1)}] n=${q.n}` : '-');
const rt = (r: { n: number; passed: number; rate: number; lo: number; hi: number }) => (r.n ? `${pc(r.rate)} (${r.passed}/${r.n}; ${pc(r.lo, 0)}-${pc(r.hi, 0)})` : '-');
const f2 = (x: number | null) => (x === null || !Number.isFinite(x) ? '-' : x.toFixed(3));

function report(ids: string[], sums: Record<string, EventSummary>, pooled: Curves, aggr: Record<string, { car: CarMeta; a: CarAggression }[]>, rookie: { medianRef: number | null; medianMed: number | null }): string {
  const L: string[] = [];
  L.push('# Traffic data (MyLaps 2026 Lemons races)', '', 'Generated by `npx tsx tools/race/traffic_data.ts`; deterministic. Drivers are referred to by stint number only.', '');
  L.push('## Method notes', '',
    '- Crossing = a lap row at `timeOfDay`, the moment the car crossed the line that ENDS the lap. One origin per event (earliest crossing).',
    '- `inPit` reading: MyLaps flags the lap whose crossing is made after the stop (the lap that contains the pit visit; its time is the whole in-to-out duration). The lap AFTER it is the out lap (slow, not flagged); I treat it as an out lap myself. Check per event below.',
    '- Usable lap: green, not a pit lap, not the lap after a pit lap, not lap 1, time <= 1.3 x the car\'s raw median of green non-pit laps and > 60 s. Stints and the clean-lap set are those of `pace_rules.ts` (checked against `carPace(q=0.2)`; mismatching cars below).',
    '- Car ahead on the road = the other car with the latest crossing before X\'s, skipping cars in the pits (crossing was a pit lap, or its next crossing is a pit lap or later than 1.5 x its median lap). Gap g = difference of the two crossing times, kept <= 10 s.',
    '- Outcome at X\'s next crossing: passed = X crossed before Y; pulledAway = new gap > g + 2 s; else stuck. Pairs dropped when either outcome lap is yellow, pit/out/lap-1, an outlier, or its crossing time disagrees with its lap time by > 1.5 s.',
    '- Free pace ref = quantile 0.2 of a stint\'s clean laps; d = (refY - refX) / refX, positive = X faster. Time lost = lapTime - ref.',
    '- Pace percentile = position of the stint ref among all stint refs in the event (0 = fastest); "slowest 10 %" = refs in the top decile, "fastest quartile" = bottom quartile.', '');
  L.push('## Caveats', '',
    '- One crossing per lap: the gap is known only at the line, the outcome is a lap-long window (a pass and a re-pass inside one lap cancel; a pass early in the lap and a gap that reopens look the same as a pass).',
    '- Yellow laps are dropped entirely (the pair is not used), so the curves are green-flag only. 10 s cut: beyond it there is no interaction; dropped counts below.',
    '- The in-pit reading above is inferred from lap times; a short stop that is not flagged would look like a slow lap and be dropped as an outlier only if > 1.3 x median.',
    '- 2026 fields only: four events, three of them 100+ cars (Sonoma, Buttonwillow, Mid-Ohio), Laguna 45.', '');
  L.push('## Pooled pass rate by pace delta d (rows) and gap g (columns), pass within one lap', '', '| d | g 0-0.5 | 0.5-1 | 1-2 | all g<2 |', '|---|---|---|---|---|');
  for (let di = 0; di < 6; di++) {
    const cell = (gi: number) => pooled.cells[gi * 6 + di];
    L.push(`| ${D_BINS[di]} | ${rt(cell(0))} | ${rt(cell(1))} | ${rt(cell(2))} | ${rt(pooled.byD[di])} |`);
  }
  L.push('', 'Wilson 90 % interval in brackets. Rows `Yfaster` are the floor (the car ahead is faster).', '');
  L.push('## Pooled pass rate by gap, d >= 3 %', '', '| g | rate |', '|---|---|');
  pooled.byG.forEach((r) => L.push(`| ${r.g} | ${rt(r)} |`));
  L.push('', '## Pooled full table (g x d): n, passes, rate', '', '| g \\ d | ' + D_BINS.join(' | ') + ' |', '|---|' + D_BINS.map(() => '---').join('|') + '|');
  for (let gi = 0; gi < 7; gi++) L.push(`| ${G_BINS[gi]} | ` + D_BINS.map((_, di) => { const c = pooled.cells[gi * 6 + di]; return c.n ? `${c.passed}/${c.n} ${pc(c.rate, 0)}` : '-'; }).join(' | ') + ' |');
  L.push('', '## Pooled time lost per lap by the attacker (s above its stint ref), g < 2 s: median [q1, q3] n', '', '| d | stuck | passed (lap of the pass) | pulledAway |', '|---|---|---|---|');
  pooled.lostByD.forEach((r) => L.push(`| ${r.d} | ${qs(r.stuck)} | ${qs(r.passed)} | ${qs(r.pulledAway)} |`));
  L.push('', '## (c) Pressure on the car ahead: Y\'s own time lost (s above its ref) on the lap after X was close behind', '', 'near = g <= 1 s, far = 3-10 s (the comparison); "X faster" = X faster by >= 3 %.', '', '| Y | X | X faster | Y time lost median [q1,q3] n |', '|---|---|---|---|');
  pooled.pressure.forEach((p) => L.push(`| ${p.y} | ${p.x} | ${p.faster ? 'yes' : 'no'} | ${qs(p.lost)} |`));
  L.push('', '## (d) Aggression groups (opportunities: d >= 1 %, g < 3 s), pooled', '', '| group | opportunities | actual | expected | ratio | z |', '|---|---|---|---|---|---|');
  for (const [k, v] of Object.entries(pooled.groups)) L.push(`| ${k} | ${v.n} | ${v.actual} | ${v.expected.toFixed(1)} | ${f2(v.ratio)} | ${f2(v.z)} |`);
  L.push('', 'Per event:', '', '| event | fastest quartile ratio (z) | others ratio (z) | slowest 10 % ahead ratio (z) | others ahead ratio (z) |', '|---|---|---|---|---|');
  for (const id of ids) { const g = sums[id].curves.groups; const s = (n: string) => `${f2(g[n].ratio)} (${f2(g[n].z)}; n=${g[n].n})`; L.push(`| ${id} | ${s('attackerFastestQuartile')} | ${s('attackerOthers')} | ${s('aheadSlowest10')} | ${s('aheadOthers')} |`); }
  L.push('', '## Cross-checks', '', '| event | cars | crossings | usable pairs | passes (mine) | position gains (sum) | position losses (sum) | median g | floor (Yfaster, g<2) | pairs dropped: no car <=10 s / yellow / pit,out / outlier / inconsistent / no ref | pit laps: median ratio, next lap, share > 1.5 | stint mismatches vs carPace |', '|---|---|---|---|---|---|---|---|---|---|---|---|');
  for (const id of ids) { const s = sums[id], d = s.drops; L.push(`| ${id} | ${s.cars} | ${s.crossings} | ${s.crosscheck.pairsUsable} | ${s.crosscheck.myPasses} | ${s.crosscheck.positionGains} | ${s.crosscheck.positionLosses} | ${s.medianGap.toFixed(2)} s | ${s.floor.passed}/${s.floor.n} = ${pc(s.floor.rate)} | ${d.noAhead} / ${d.yellow} / ${d.pitOrOut} / ${d.outlier} / ${d.inconsistent} / ${d.noRef} | ${s.pitReading.pitLapMedianRatio.toFixed(2)}, ${s.pitReading.nextLapMedianRatio.toFixed(2)}, ${pc(s.pitReading.pitLapsLongerThan15, 0)} | ${s.stintMismatch} |`); }
  L.push('', 'Position gains/losses come from consecutive `fieldComparison.position` values (classification, not road order; lapped cars and pit cycles move it). My passes count only pairs within 10 s with both outcome laps clean, so they are lower by construction.', '');
  L.push('## (e) Probe #619 by stint number', '');
  for (const id of ids) {
    const p = sums[id].probe;
    L.push(`### ${EVENTS[id].label}`, '');
    if (!p) { L.push('No car #619 in this event.', ''); continue; }
    L.push(`Team: ${p.team}`, '', '| stint | tag | laps (first-last) | start | end | clean laps | ref q0.2 | median | q0.8 | sigma | passes made/lap | times passed/lap | mean lost/lap |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|');
    p.stints.forEach((s) => L.push(`| ${s.stint} | ${s.rookie ? 'rookie' : ''} | ${s.fromLap}-${s.toLap} | ${s.start} | ${s.end} | ${s.cleanLaps} | ${s.ref.toFixed(2)} | ${s.median.toFixed(2)} | ${s.q80.toFixed(2)} | ${s.sigma.toFixed(2)} | ${s.passesPerLap.toFixed(3)} | ${s.passedPerLap.toFixed(3)} | ${s.lostPerLap.toFixed(2)} |`));
    L.push('', p.rookieFactorRef === null ? 'Fewer than 2 stints.' : `Rookie factor: ref ${p.rookieFactorRef.toFixed(3)}, median lap ${p.rookieFactorMedian!.toFixed(3)} (rookie stint over the median of the other stints). Passes made per lap: rookie ${p.rookiePassesPerLap!.toFixed(3)} vs others ${p.othersPassesPerLap!.toFixed(3)} (rookie fewer: ${p.rookiePassesFewer}). Times passed per lap: rookie ${p.rookiePassedPerLap!.toFixed(3)} vs others ${p.othersPassedPerLap!.toFixed(3)} (rookie passed more: ${p.rookiePassedMore}).`, '');
  }
  L.push(`Pooled rookie factor (median over events): ref ${f2(rookie.medianRef)}, median lap ${f2(rookie.medianMed)}.`, '');
  L.push('## (d) Per-car aggression (pooled curves; >= 20 opportunities)', '');
  for (const id of ids) {
    const rows = aggr[id], n = (t: string) => rows.filter((r) => r.a.tier === t).length;
    L.push(`### ${EVENTS[id].label}: ${n('attacker')} attacker / ${n('neutral')} neutral / ${n('passive')} passive of ${rows.length} cars`, '', '| # | team | class | pace rank | opps | actual | expected | ratio | z | tier |', '|---|---|---|---|---|---|---|---|---|---|');
    rows.sort((a, b) => b.a.z - a.a.z).forEach(({ car, a }) => L.push(`| ${car.number} | ${car.team} | ${car.cls} | ${car.paceRank} | ${a.n} | ${a.actual} | ${a.expected.toFixed(1)} | ${f2(a.ratio)} | ${f2(a.z)} | ${a.tier} |`));
    L.push('');
  }
  return L.join('\n');
}

export function main(argv: string[]): void {
  const ti = argv.indexOf('--track'), oi = argv.indexOf('--out');
  const ids = ti >= 0 ? [argv[ti + 1]] : Object.keys(EVENTS);
  for (const id of ids) if (!EVENTS[id]) throw new Error('unknown --track ' + id);
  const outDir = oi >= 0 ? resolve(argv[oi + 1]) : resolve(DATA, 'traffic');
  mkdirSync(outDir, { recursive: true });
  const data = ids.map(loadEvent), an = data.map(analyse);
  const sums: Record<string, EventSummary> = {}; ids.forEach((id, i) => { sums[id] = an[i].summary; });
  const all = an.flatMap((a) => a.pairs), pooled = curves(all);
  const aggr: Record<string, { car: CarMeta; a: CarAggression }[]> = {};
  ids.forEach((id, i) => { aggr[id] = perCar(an[i].pairs, pooled).map((a) => ({ car: data[i].cars.find((c) => c.id === a.car)!, a })); });
  const med = (f: (p: Probe) => number | null) => { const v = ids.map((id) => sums[id].probe).filter((p): p is Probe => !!p).map(f).filter((x): x is number => x !== null); return v.length ? median(v) : null; };
  const rookie = { medianRef: med((p) => p.rookieFactorRef), medianMed: med((p) => p.rookieFactorMedian) };
  const json = { events: sums, pooled: { curves: pooled, rookie }, aggression: Object.fromEntries(ids.map((id) => [id, aggr[id].map(({ car, a }) => ({ number: car.number, team: car.team, class: car.cls, paceRank: car.paceRank, ...a }))])) };
  writeFileSync(resolve(outDir, 'curves.json'), toJson(json) + '\n');
  writeFileSync(resolve(outDir, 'REPORT.md'), report(ids, sums, pooled, aggr, rookie) + '\n');
  console.log(`traffic: ${ids.join(', ')}: ${all.length} usable pairs, ${all.filter((p) => p.outcome === 'passed').length} passes -> ${outDir}`);
}
if (process.argv[1] && /traffic_data\.ts$/.test(process.argv[1])) main(process.argv.slice(2));
