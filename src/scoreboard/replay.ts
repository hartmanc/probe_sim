// Input-trace recording and server-side replay. Recording happens inside HotlapSim (sim.ts) when it is
// built with { record: true }; this module re-runs a trace in a fresh HotlapSim and measures the lap.
// Pure TS: no DOM, no Node built-ins.
import type { Lap } from '../app/timing';
import { SAMPLE_EVERY, QUANT, FLAG_MASK, LIMITS, TRACE_FORMAT } from './config';
import { HotlapSim, type SimAssets } from './sim';
import type { InputTrace, TraceRow } from './types';

export { HotlapSim } from './sim';

const isInt = (x: unknown): x is number => typeof x === 'number' && Number.isInteger(x);

/** Structural checks on a trace (cheap; run before any replay). Returns reasons, empty when fine. */
export function checkTrace(t: unknown): string[] {
  const r: string[] = [];
  if (!t || typeof t !== 'object') return ['trace missing'];
  const tr = t as Partial<InputTrace>;
  if (tr.v !== TRACE_FORMAT) r.push(`trace.v must be ${TRACE_FORMAT}`);
  if (typeof tr.physics !== 'string' || tr.physics.length > 64) r.push('trace.physics missing');
  if (typeof tr.track !== 'string' || typeof tr.car !== 'string') r.push('trace.track/car missing');
  if (!isInt(tr.steps) || tr.steps <= 0 || tr.steps > LIMITS.maxTraceSteps) r.push(`trace.steps must be 1..${LIMITS.maxTraceSteps}`);
  const rs = tr.reset;
  if (!rs || !Array.isArray(rs.pos) || rs.pos.length !== 3 || ![...rs.pos, rs.heading, rs.speed].every((x) => typeof x === 'number' && Number.isFinite(x))) r.push('trace.reset malformed');
  if (!Array.isArray(tr.ref) || tr.ref.length > 64) r.push('trace.ref malformed');
  else {
    let prev = -1;
    for (const e of tr.ref) {
      if (!Array.isArray(e) || e.length !== 2 || !isInt(e[0]) || e[0] % SAMPLE_EVERY !== 0 || e[0] <= prev || !(e[1] === null || (typeof e[1] === 'string' && e[1].length <= 64))) { r.push('trace.ref entry malformed'); break; }
      prev = e[0];
    }
    if (tr.ref.length && tr.ref[0]?.[0] !== 0) r.push('trace.ref must start at step 0');
  }
  if (!Array.isArray(tr.rows) || tr.rows.length === 0) { r.push('trace.rows missing'); return r; }
  if (tr.rows.length > LIMITS.maxTraceRows) { r.push(`trace.rows over ${LIMITS.maxTraceRows}`); return r; }
  let prev = -1;
  for (let i = 0; i < tr.rows.length; i++) {
    const row = tr.rows[i] as unknown;
    if (!Array.isArray(row) || row.length !== 5 || !row.every(isInt)) { r.push(`trace.rows[${i}] malformed`); break; }
    const [k, st, th, br, f] = row as TraceRow;
    if (k % SAMPLE_EVERY !== 0 || k <= prev || (i === 0 && k !== 0) || (isInt(tr.steps) && k >= tr.steps)) { r.push(`trace.rows[${i}] step ${k} out of order / off grid`); break; }
    if (st < -QUANT || st > QUANT || th < 0 || th > QUANT || br < 0 || br > QUANT || f < 0 || (f & ~FLAG_MASK) !== 0) { r.push(`trace.rows[${i}] value out of range`); break; }
    prev = k;
  }
  return r;
}

export interface ReplayResult {
  /** The lap the claim names, as the replay timed it (null if it never completed). */
  lap: Lap | null;
  /** Every lap the replay completed. */
  laps: Lap[];
  steps: number;
  cpuMs: number;
  /** Final vehicle state + sim clock, for determinism checks. */
  sim: HotlapSim;
}

/**
 * Re-run `trace` from the canonical reset in a fresh HotlapSim until lap `lapN` completes (or the trace's
 * steps + 1 s run out). Throws on a reset mismatch or unknown reference ghost (callers map to a rejection).
 */
export function replayTrace(assets: SimAssets, trace: InputTrace, lapN = Infinity, nowMs: () => number = () => Date.now()): ReplayResult {
  const t0 = nowMs();
  const sim = new HotlapSim(assets, { record: false, ref: trace.ref[0]?.[1] ?? null });
  const r = sim.start;   // canonicalReset on the racing line (the sim applies the ghost line's offset)
  const d = Math.max(Math.abs(r.pos[0] - trace.reset.pos[0]), Math.abs(r.pos[1] - trace.reset.pos[1]), Math.abs(r.pos[2] - trace.reset.pos[2]),
    Math.abs(r.heading - trace.reset.heading), Math.abs(r.speed - trace.reset.speed));
  if (!(d < 1e-6)) throw new Error('reset does not match the canonical rolling start');
  for (const [, id] of trace.ref) if (id !== null && !assets.ghosts.laps.some((l) => l.id === id)) throw new Error(`unknown reference ghost ${id}`);

  const rows = trace.rows, refs = trace.ref;
  const limit = Math.min(trace.steps + 1000, LIMITS.maxTraceSteps + 1000);
  let ri = 0, fi = 0;
  let lap: Lap | null = null;
  const laps: Lap[] = [];
  while (sim.stepIndex < limit) {
    const k = sim.stepIndex;
    if (k % SAMPLE_EVERY === 0) {
      while (fi < refs.length && refs[fi][0] <= k) { sim.replayRef(refs[fi][1]); fi++; }
      if (fi === 0) sim.replayRef(null);
      while (ri + 1 < rows.length && rows[ri + 1][0] <= k) ri++;
      sim.applyRow(rows[ri], rows[ri][0] === k);
    }
    const ev = sim.advance();
    if (ev && ev !== 'start') {
      laps.push(ev);
      if (ev.n === lapN) { lap = ev; break; }
    }
  }
  return { lap, laps, steps: sim.stepIndex, cpuMs: nowMs() - t0, sim };
}

export interface HotlapVerdict {
  ok: boolean;
  reasons: string[];
  replayed: number | null;
  cpuMs: number;
}

/** Replay a hot-lap claim and judge it: lap `lapN` must complete, be valid and match `claimed` within the tolerance. */
export function verifyHotlap(assets: SimAssets, trace: InputTrace, lapN: number, claimed: number): HotlapVerdict {
  let res: ReplayResult;
  try { res = replayTrace(assets, trace, lapN); } catch (e) {
    return { ok: false, reasons: [`replay: ${(e as Error).message}`], replayed: null, cpuMs: 0 };
  }
  const reasons: string[] = [];
  if (!res.lap) reasons.push(`replay: lap ${lapN} did not complete`);
  else {
    if (!res.lap.valid) reasons.push('replay: lap invalid (more than 2 s off track)');
    const dt = Math.abs(res.lap.time - claimed);
    if (!(dt <= LIMITS.replayTolerance)) reasons.push(`replay: lap time ${res.lap.time.toFixed(3)} s differs from the claimed ${claimed.toFixed(3)} s`);
  }
  return { ok: reasons.length === 0, reasons, replayed: res.lap ? res.lap.time : null, cpuMs: res.cpuMs };
}
