// A ghost lap (the app's GhostLap shape: time and speed on a distance grid) from a lap's own samples: the session's
// best lap as it is driven, and the leaderboard's all-time best rebuilt from its input trace with the same replay the
// server runs (replay.ts), so its time is the board's time. Pure TS: no DOM.
import { TIMING_EVERY } from './config';
import { replayTrace } from './replay';
import type { SimAssets } from './sim';
import type { InputTrace } from './types';

/** One timing tick of a lap in progress: seconds since the lap's start, distance along the lap (m), speed (m/s). */
export interface LapSample { t: number; s: number; v: number }

/** The ghost-lap shape of src/app/physics-types.ts GhostLap (declared here to keep this module free of app imports). */
export interface BuiltGhostLap {
  id: string; driver: string; label: string; kind: string;
  lap_time_s: number;
  t: number[]; v_mps: number[];
}

/**
 * Resample a lap's samples onto the ghost grid (`grid` m, floor(length / grid) points, as synthesizeGhosts does):
 * t[i] and v[i] at s = i * grid by linear interpolation, the start pinned at (0, 0), samples that do not advance
 * dropped, the tail past the last sample extended at its speed. GhostTrace.tAt takes it from there to the line.
 */
export function buildGhostLap(samples: readonly LapSample[], lapTime: number, length: number, grid: number, meta: { id: string; driver: string; label: string; kind?: string }): BuiltGhostLap | null {
  const pts: LapSample[] = [{ t: 0, s: 0, v: samples.length ? samples[0].v : 0 }];
  for (const p of samples) {
    const last = pts[pts.length - 1];
    if (p.s > last.s && p.t > last.t && p.s < length) pts.push(p);
  }
  if (pts.length < 3 || !(lapTime > 0)) return null;
  const m = Math.floor(length / grid);
  const t: number[] = new Array(m), v: number[] = new Array(m);
  let k = 0;
  for (let i = 0; i < m; i++) {
    const s = i * grid;
    while (k + 1 < pts.length - 1 && pts[k + 1].s < s) k++;
    const a = pts[k], b = pts[k + 1];
    if (s <= b.s) {
      const f = (s - a.s) / (b.s - a.s);
      t[i] = a.t + (b.t - a.t) * f; v[i] = a.v + (b.v - a.v) * f;
    } else {   // past the last sample: carry on at its speed
      const sp = Math.max(1, b.v);
      t[i] = b.t + (s - b.s) / sp; v[i] = b.v;
    }
  }
  return { id: meta.id, driver: meta.driver, label: meta.label, kind: meta.kind ?? 'session', lap_time_s: lapTime, t, v_mps: v };
}

/**
 * Rebuild a lap from an input trace: replay it to the end of lap `lapN` (the replay the server ran when it verified the
 * post) and collect the timing ticks of that lap. Returns the lap time the replay measured and the built lap, or null when
 * the lap does not complete or is invalid.
 */
export function ghostFromTrace(assets: SimAssets, trace: InputTrace, lapN: number, meta: { id: string; driver: string; label: (time: number) => string; kind?: string }): { time: number; lap: BuiltGhostLap } | null {
  const samples: LapSample[] = [];
  const res = replayTrace(assets, trace, lapN, undefined, (sim) => {
    if (sim.stepIndex % TIMING_EVERY !== 0) return;   // the timing ticks (sim.s moves there)
    const tm = sim.timer;
    if (!tm.started || tm.lapNumber !== lapN) return;
    samples.push({ t: sim.simTime - tm.lapStart, s: sim.s, v: Math.abs(sim.vehicle.state.speed) });
  });
  if (!res.lap || !res.lap.valid) return null;
  // the tick that completes the lap already belongs to lap n + 1 (the timer re-armed), so `samples` ends at the line
  const lap = buildGhostLap(samples, res.lap.time, assets.track.length_m, assets.ghosts.s_grid_m, { ...meta, label: meta.label(res.lap.time) });
  return lap ? { time: res.lap.time, lap } : null;
}
