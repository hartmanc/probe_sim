// The recorder side of race recordings (docs/races.md): the tap that watches a running sim + director and the safeguard data read
// from a director. Split from racerec.ts (the format, which the server also imports) because it reaches into the AI.
import type { RaceDirector } from '../physics/ai/race';
import { getPowerShare } from '../physics/ai/field';
import type { HotlapSim } from './sim';
import { SNAP_STEPS, type RecChunk, type RecEvent, type RecLive } from './racerec';

/** Quantised snapshot of one director: station mod L (dm) and lane offset (dm, clamped). */
export function snapshotOf(dir: RaceDirector): { s: Int32Array; e: Int8Array } {
  const tr = dir.traffic, n = dir.cars.length, L10 = Math.round(dir.line.L * 10);
  const s = new Int32Array(n), e = new Int8Array(n);
  for (let i = 0; i < n; i++) {
    const q = Math.round(tr.s[i] * 10);
    s[i] = Number.isFinite(q) ? ((q % L10) + L10) % L10 : 0;
    const w = Math.round(tr.e[i] * 10);
    e[i] = Number.isFinite(w) ? Math.max(-127, Math.min(127, w)) : 0;
  }
  return { s, e };
}

/**
 * Collects what the inputs alone cannot say. The inputs themselves are the sim's own recorded trace (HotlapSim `record`), so
 * the rows are exactly the quantised samples the director consumed; the tap drains them with `drain`. It also logs the
 * between-step events and takes the position snapshot every SNAP_STEPS steps. Call `after()` once per physics step.
 */
export class RaceTap {
  private rowsFrom = 0;
  private refsFrom = 0;
  private events: RecEvent[] = [];
  private snapS: Int32Array[] = [];
  private snapE: Int8Array[] = [];
  /** snapshots are skipped when positions in dm would not fit the Int16 deltas (a track over 6.5 km) */
  readonly snapshots: boolean;
  constructor(private readonly sim: HotlapSim, private readonly dir: RaceDirector) {
    this.snapshots = Math.round(dir.line.L * 10) <= 65000;
  }

  /** The player was put back on the centreline at station s (before the next step). */
  recover(s: number): void { this.events.push([this.sim.stepIndex, 0, s]); }
  /** An app-side rule report reached the director (before the next step). */
  violation(kind: string, detail?: string): void { this.events.push(detail === undefined ? [this.sim.stepIndex, 1, kind] : [this.sim.stepIndex, 1, kind, detail]); }

  /** After each physics step. */
  after(): void {
    if (this.snapshots && this.sim.stepIndex % SNAP_STEPS === 0) {
      const q = snapshotOf(this.dir);
      this.snapS.push(q.s); this.snapE.push(q.e);
    }
  }

  /** Everything new since the last drain (rows and refs are copied out of the sim). */
  drain(): RecChunk {
    const sim = this.sim;
    const rows = sim.rowsFrom(this.rowsFrom), refs = sim.refsFrom(this.refsFrom);
    this.rowsFrom += rows.length; this.refsFrom += refs.length;
    const ch: RecChunk = { rows, refs, events: this.events, snapS: this.snapS, snapE: this.snapE, steps: sim.stepIndex, reset: sim.start };
    this.events = []; this.snapS = []; this.snapE = [];
    return ch;
  }
}

/** The live safeguard data of a director (the worker host reads it from its own, the app from the one it stepped). */
export function liveOf(dir: RaceDirector): RecLive {
  const me = dir.player.number;
  const lapTimes: number[] = [];
  for (const c of dir.crossings) if (c.car === me && Number.isFinite(c.lapTime) && c.lapTime > 0) lapTimes.push(c.lapTime);
  const res = dir.getResults();
  return {
    lapTimes,
    crossings: dir.crossings.map((c) => ({ car: c.car, lapNr: c.lapNr, t: c.t })),
    results: res ? res.map((r) => ({ number: r.number, laps: r.lapsCompleted, time: r.time, metres: r.metres })) : null,
  };
}

/** The director's effective RaceConfig as plain JSON (NaN / Infinity -> null) plus the one global the AI reads (the power split). */
export function configOf(dir: RaceDirector): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(dir.config as unknown as Record<string, unknown>)) out[k] = typeof v === 'number' && !Number.isFinite(v) ? null : v;
  out.powerShare = getPowerShare();
  return JSON.parse(JSON.stringify(out)) as Record<string, unknown>;
}

