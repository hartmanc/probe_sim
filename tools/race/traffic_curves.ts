// Passing statistics from lap-crossing records (28 Oct 2026). Pure: no file I/O, so the same code can be fed the real
// MyLaps crossings (tools/race/traffic_data.ts) and the sim's own crossing times and compared like for like.
//
// A pair = one attacker X crossing the line at t (the end of lap L) with a car Y on the road ahead of it within `maxGap`
// seconds; the outcome is read at X's next crossing (end of lap L+1): X got by (`passed`), Y left (`pulledAway`, the gap
// grew by more than `pullMargin`) or X stayed behind (`stuck`).
import { median, quantile } from './pace_rules';

export interface Crossing { car: string; lapNr: number; t: number; lapTime: number; green: boolean; pit: boolean }
export interface StintRef { car: string; fromLap: number; toLap: number; ref: number }
export type Outcome = 'passed' | 'stuck' | 'pulledAway';
export interface Pair {
  x: string; y: string;
  /** X's lap that carries the outcome (L+1) */
  lap: number; yLap: number;
  /** gap at the crossing (s), pace delta d = (refY - refX) / refX (positive: X is the faster car) */
  g: number; d: number; outcome: Outcome; gNew: number;
  lostX: number; lostY: number;
  /** pace percentile of the stint refs in this call (0 = fastest) */
  xPct: number; yPct: number;
  /** time at X's crossing */
  t: number;
}
export interface PairOpts { maxGap?: number; minLap?: number; cut?: number; tol?: number; pitFactor?: number; pullMargin?: number }
export interface Drops { crossings: number; noAhead: number; inPitsSkipped: number; yellow: number; pitOrOut: number; outlier: number; inconsistent: number; noRef: number; usable: number }

export const G_EDGES = [0, 0.5, 1, 2, 3, 5, 8, 10];
export const G_BINS = ['0-0.5', '0.5-1', '1-2', '2-3', '3-5', '5-8', '8-10'];
export const D_BINS = ['Yfaster', '0-1', '1-3', '3-8', '8-15', '>15'];
export const gBin = (g: number): number => { for (let i = 0; i < 7; i++) if (g < G_EDGES[i + 1]) return i; return 6; };
export const dBin = (d: number): number => d < 0 ? 0 : d < 0.01 ? 1 : d < 0.03 ? 2 : d < 0.08 ? 3 : d < 0.15 ? 4 : 5;

export function pairsWithDrops(crossings: Crossing[], refs: StintRef[], opts: PairOpts = {}): { pairs: Pair[]; drops: Drops } {
  const maxGap = opts.maxGap ?? 10, minLap = opts.minLap ?? 0, cut = opts.cut ?? 1.3, tol = opts.tol ?? 1.5, pitFactor = opts.pitFactor ?? 1.5, pullMargin = opts.pullMargin ?? 2;
  const byCar = new Map<string, Map<number, Crossing>>();
  for (const c of crossings) { let m = byCar.get(c.car); if (!m) byCar.set(c.car, m = new Map()); m.set(c.lapNr, c); }
  const med = new Map<string, number>();
  for (const [car, m] of byCar) med.set(car, median([...m.values()].filter((c) => c.green && !c.pit && c.lapTime > minLap).map((c) => c.lapTime)));
  const refsBy = new Map<string, StintRef[]>();
  for (const r of refs) { let a = refsBy.get(r.car); if (!a) refsBy.set(r.car, a = []); a.push(r); }
  const refOf = (car: string, lap: number): number | null => { for (const r of refsBy.get(car) ?? []) if (lap >= r.fromLap && lap <= r.toLap) return r.ref; return null; };
  const usable = (c: Crossing): 'ok' | 'yellow' | 'pit' | 'outlier' => {
    if (c.pit) return 'pit';
    const prev = byCar.get(c.car)!.get(c.lapNr - 1);
    if (c.lapNr <= 1 || !prev || prev.pit || prev.lapTime > pitFactor * med.get(c.car)!) return 'pit';   // out lap: after a flagged lap, or after the long lap that holds the stop when MyLaps flags the lap before it
    if (!c.green) return 'yellow';
    if (!(c.lapTime > minLap) || c.lapTime > cut * med.get(c.car)!) return 'outlier';
    return 'ok';
  };
  const allRefs = refs.map((r) => r.ref).sort((a, b) => a - b);
  const pct = (r: number) => { let lo = 0, hi = allRefs.length; while (lo < hi) { const m = (lo + hi) >> 1; if (allRefs[m] < r) lo = m + 1; else hi = m; } return allRefs.length ? lo / allRefs.length : 0; };
  const all = [...crossings].sort((a, b) => a.t - b.t || (a.car < b.car ? -1 : 1));
  const drops: Drops = { crossings: 0, noAhead: 0, inPitsSkipped: 0, yellow: 0, pitOrOut: 0, outlier: 0, inconsistent: 0, noRef: 0, usable: 0 };
  const pairs: Pair[] = [];
  for (let i = 0; i < all.length; i++) {
    const X = all[i];
    const nx = byCar.get(X.car)!.get(X.lapNr + 1);
    if (X.pit || !nx) continue;
    drops.crossings++;
    let Y: Crossing | null = null, ny: Crossing | undefined;
    for (let j = i - 1; j >= 0 && X.t - all[j].t <= maxGap; j--) {
      const c = all[j];
      if (c.car === X.car || c.t >= X.t || c.pit) continue;
      const n = byCar.get(c.car)!.get(c.lapNr + 1);
      if (!n || n.pit || n.t - c.t > pitFactor * med.get(c.car)!) { drops.inPitsSkipped++; continue; }
      Y = c; ny = n; break;
    }
    if (!Y || !ny) { drops.noAhead++; continue; }
    const ux = usable(nx), uy = usable(ny);
    if (ux === 'yellow' || uy === 'yellow') { drops.yellow++; continue; }
    if (ux === 'pit' || uy === 'pit') { drops.pitOrOut++; continue; }
    if (ux === 'outlier' || uy === 'outlier') { drops.outlier++; continue; }
    if (Math.abs(nx.t - X.t - nx.lapTime) > tol || Math.abs(ny.t - Y.t - ny.lapTime) > tol) { drops.inconsistent++; continue; }
    const rx = refOf(X.car, nx.lapNr), ry = refOf(Y.car, ny.lapNr);
    if (rx === null || ry === null) { drops.noRef++; continue; }
    const g = X.t - Y.t, gNew = nx.t - ny.t;
    const outcome: Outcome = gNew < 0 ? 'passed' : gNew > g + pullMargin ? 'pulledAway' : 'stuck';
    drops.usable++;
    pairs.push({ x: X.car, y: Y.car, lap: nx.lapNr, yLap: ny.lapNr, g, d: (ry - rx) / rx, outcome, gNew, lostX: nx.lapTime - rx, lostY: ny.lapTime - ry, xPct: pct(rx), yPct: pct(ry), t: X.t });
  }
  return { pairs, drops };
}
export const pairs = (crossings: Crossing[], refs: StintRef[], opts?: PairOpts): Pair[] => pairsWithDrops(crossings, refs, opts).pairs;

/** Wilson score interval, z = 1.645 (90 %) */
export function wilson(k: number, n: number, z = 1.645): [number, number] {
  if (!n) return [NaN, NaN];
  const p = k / n, z2 = z * z, den = 1 + z2 / n, c = p + z2 / (2 * n), h = z * Math.sqrt(p * (1 - p) / n + z2 / (4 * n * n));
  return [(c - h) / den, (c + h) / den];
}
export interface Q { n: number; med: number; q1: number; q3: number }
export const qstat = (a: number[]): Q => ({ n: a.length, med: median(a), q1: quantile(a, 0.25), q3: quantile(a, 0.75) });
export interface Rate { n: number; passed: number; rate: number; lo: number; hi: number }
const rate = (k: number, n: number): Rate => { const [lo, hi] = wilson(k, n); return { n, passed: k, rate: n ? k / n : NaN, lo, hi }; };
export interface Cell extends Rate { g: string; d: string; stuck: number; pulledAway: number; lost: { stuck: Q; passed: Q; pulledAway: Q } }
export interface Ratio { n: number; actual: number; expected: number; ratio: number; z: number }
export interface Curves {
  pairs: number;
  cells: Cell[];
  /** pass rate by d, g <= 2 s */
  byD: (Rate & { d: string })[];
  /** pass rate by g, d >= 3 % */
  byG: (Rate & { g: string })[];
  /** attacker's time lost per lap by d (g <= 2 s) and outcome */
  lostByD: { d: string; stuck: Q; passed: Q; pulledAway: Q }[];
  /** Y's own time lost on the lap, by Y slow (slowest 10 % of refs) or rest, X near (g <= 1 s) or far (3-10 s), X faster by >= 3 % or not */
  pressure: { y: 'slow' | 'rest'; x: 'near' | 'far'; faster: boolean; lost: Q }[];
  /** opportunity groups (d >= 1 %, g < 3 s): fastest pace quartile as attackers, slowest 10 % as the car ahead, and their complements */
  groups: Record<string, Ratio>;
}
export const OPP_D = 0.01, OPP_G = 3;
const isOpp = (p: Pair) => p.d >= OPP_D && p.g < OPP_G;

export function curves(ps: Pair[]): Curves {
  const cellOf = (g: number, d: number) => gBin(g) * 6 + dBin(d);
  const bucket: Pair[][] = Array.from({ length: 42 }, () => []);
  for (const p of ps) bucket[cellOf(p.g, p.d)].push(p);
  const cells: Cell[] = [];
  for (let gi = 0; gi < 7; gi++) for (let di = 0; di < 6; di++) {
    const b = bucket[gi * 6 + di];
    const lost = (o: Outcome) => qstat(b.filter((p) => p.outcome === o).map((p) => p.lostX));
    cells.push({ g: G_BINS[gi], d: D_BINS[di], ...rate(b.filter((p) => p.outcome === 'passed').length, b.length), stuck: b.filter((p) => p.outcome === 'stuck').length, pulledAway: b.filter((p) => p.outcome === 'pulledAway').length, lost: { stuck: lost('stuck'), passed: lost('passed'), pulledAway: lost('pulledAway') } });
  }
  const near = ps.filter((p) => p.g < 2);
  const byD = D_BINS.map((d, di) => ({ d, ...rate(near.filter((p) => dBin(p.d) === di && p.outcome === 'passed').length, near.filter((p) => dBin(p.d) === di).length) }));
  const fast = ps.filter((p) => p.d >= 0.03);
  const byG = G_BINS.map((g, gi) => ({ g, ...rate(fast.filter((p) => gBin(p.g) === gi && p.outcome === 'passed').length, fast.filter((p) => gBin(p.g) === gi).length) }));
  const lostByD = D_BINS.map((d, di) => {
    const b = near.filter((p) => dBin(p.d) === di);
    const l = (o: Outcome) => qstat(b.filter((p) => p.outcome === o).map((p) => p.lostX));
    return { d, stuck: l('stuck'), passed: l('passed'), pulledAway: l('pulledAway') };
  });
  const pressure: Curves['pressure'] = [];
  for (const y of ['slow', 'rest'] as const) for (const x of ['near', 'far'] as const) for (const faster of [true, false]) {
    const sel = ps.filter((p) => (p.yPct >= 0.9) === (y === 'slow') && (x === 'near' ? p.g <= 1 : p.g >= 3) && (p.d >= 0.03) === faster);
    pressure.push({ y, x, faster, lost: qstat(sel.map((p) => p.lostY)) });
  }
  const c: Curves = { pairs: ps.length, cells, byD, byG, lostByD, pressure, groups: {} };
  const grp = (name: string, f: (p: Pair) => boolean) => { c.groups[name] = ratio(ps.filter((p) => isOpp(p) && f(p)), c); };
  grp('attackerFastestQuartile', (p) => p.xPct <= 0.25);
  grp('attackerOthers', (p) => p.xPct > 0.25);
  grp('aheadSlowest10', (p) => p.yPct >= 0.9);
  grp('aheadOthers', (p) => p.yPct < 0.9);
  return c;
}
/** expected pass probability of a pair from the curves' (g, d) cell */
export const expectedRate = (c: Curves, p: Pair): number => c.cells[gBin(p.g) * 6 + dBin(p.d)].rate;
function ratio(ps: Pair[], c: Curves): Ratio {
  let e = 0, v = 0, a = 0;
  for (const p of ps) { const r = expectedRate(c, p); e += r; v += r * (1 - r); if (p.outcome === 'passed') a++; }
  return { n: ps.length, actual: a, expected: e, ratio: e ? a / e : NaN, z: v ? (a - e) / Math.sqrt(v) : NaN };
}
export interface CarAggression extends Ratio { car: string; tier: 'attacker' | 'neutral' | 'passive'; meanXPct: number }
/** Per attacker with >= minOpps opportunities (d >= 1 %, g < 3 s): actual vs the curves' expected passes. */
export function perCar(ps: Pair[], c: Curves, minOpps = 20): CarAggression[] {
  const by = new Map<string, Pair[]>();
  for (const p of ps) if (isOpp(p)) { let a = by.get(p.x); if (!a) by.set(p.x, a = []); a.push(p); }
  const out: CarAggression[] = [];
  for (const [car, a] of [...by].sort((u, v) => (u[0] < v[0] ? -1 : 1))) {
    if (a.length < minOpps) continue;
    const r = ratio(a, c);
    out.push({ car, ...r, tier: r.z > 1.5 ? 'attacker' : r.z < -1.5 ? 'passive' : 'neutral', meanXPct: a.reduce((s, p) => s + p.xPct, 0) / a.length });
  }
  return out;
}
