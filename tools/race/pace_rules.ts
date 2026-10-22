// The per-car pace rules of tools/race/pace.ts as a function, shared by pace.ts (Laguna) and pace_track.ts --own (a
// field built from a circuit's own session). Moved out of pace.ts unchanged (22 Oct 2026; pace.ts reproduces
// public/cars/field/pace.json byte for byte).
//
// Per car: target lap = median of GREEN, non-pit laps after dropping outliers (> 1.3 x the raw median); consistency =
// robust sigma (1.4826 x MAD) of those laps; best lap = the official best (classification bestTime).
// Stints (one driver each): the laps between pit stops. Per stint the pace is the median of that driver's clean laps,
// after dropping: non-green laps, the pit lap, the out lap after it (and lap 1 of the race), laps slower than 1.2 x the
// stint's own median or 1.3 x the car's median, and anything faster than 0.97 x the official best. A stint needs
// MIN_STINT_LAPS clean laps.
import type { PaceStint } from '../../src/physics/ai/field';

export const MIN_STINT_LAPS = 5;

export function parseLap(s: string): number {
  const parts = s.split(':').map(Number);
  let t = 0;
  for (const p of parts) t = t * 60 + p;
  return t;
}
export const median = (a: number[]) => { const b = [...a].sort((x, y) => x - y); const n = b.length; return n ? (n % 2 ? b[(n - 1) / 2] : 0.5 * (b[n / 2 - 1] + b[n / 2])) : NaN; };
export const robustSigma = (a: number[]) => { const m = median(a); return 1.4826 * median(a.map((t) => Math.abs(t - m))); };

interface Lap { nr: number; t: number; pit: boolean; ok: boolean }

export interface CarPaceStats {
  /** clean green laps (after the 1.3 x median cut) */
  greenLaps: number;
  targetLap: number; bestLap: number; sigma: number;
  stints: PaceStint[];
}

/**
 * One car's pace from its MyLaps lap file (`laps` of .../lapdata/<position>/laps) and its official best lap (s).
 * `prevStint(k, target)` may return the fitted scale of the same stint in a previous file (pace.ts keeps it when the
 * target is unchanged).
 */
export function carPace(lapsJson: any[], official: number, prevStint?: (k: number, target: number) => { scale: number; achievedLap?: number } | null): CarPaceStats {
  const laps: Lap[] = lapsJson.map((l: any) => {
    const st: string[] = Array.isArray(l.status) ? l.status : [l.status];
    const t = parseLap(l.lapTime);
    return { nr: l.lapNr, t, pit: !!l.inPit, ok: !l.inPit && st.length > 0 && st.every((x) => x === 'GREEN') && Number.isFinite(t) && t > 60 };
  });
  const green = laps.filter((l) => l.ok).map((l) => l.t);
  const m0 = median(green);
  const clean = green.filter((t) => t <= 1.3 * m0);
  const med = median(clean);
  const mad = median(clean.map((t) => Math.abs(t - med)));

  const stints: PaceStint[] = [];
  let run: number[] = [], first = -1, afterPit = true;   // the race's first lap is an out lap too
  const flush = () => {
    if (run.length) {
      const sm = median(run);
      const keep = run.filter((t) => t <= 1.2 * sm && t <= 1.3 * m0 && t >= 0.97 * official);
      if (keep.length >= MIN_STINT_LAPS) {
        const k = stints.length;
        const target = +median(keep).toFixed(3);
        const old = prevStint?.(k, target);
        stints.push({
          index: k, laps: keep.length, firstLap: first, targetLap: target,
          bestLap: +Math.min(...keep).toFixed(3), sigma: +robustSigma(keep).toFixed(3),
          ...(old ? { scale: old.scale, achievedLap: old.achievedLap } : {}),
        });
      }
    }
    run = []; first = -1;
  };
  for (const l of laps) {
    if (l.pit) { flush(); afterPit = true; continue; }
    if (afterPit) { afterPit = false; first = l.nr; continue; }     // out lap: starts the stint, never counts
    if (first < 0) first = l.nr;
    if (l.ok) run.push(l.t);
  }
  flush();
  return { greenLaps: clean.length, targetLap: +med.toFixed(3), bestLap: +official.toFixed(3), sigma: +(1.4826 * mad).toFixed(3), stints };
}
