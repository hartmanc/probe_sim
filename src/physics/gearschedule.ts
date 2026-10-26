// Gear schedule from a ghost lap: which gear the driver used at every point of the lap,
// derived from the logger's rpm and speed with the car's overall ratios.

import { log as dlog } from './dmath';   // bit-identical to V8 on every engine (docs/determinism.md)
import type { CarSpec } from './spec';

/** The parts of a ghosts.json lap the schedule needs. */
export interface GhostLapLike { v_mps: number[]; rpm?: number[] | null }

export interface GearSchedule {
  /** Grid spacing, m (ghosts.json s_grid_m). */
  grid: number;
  /** Gear per grid point (1..N), length = samples. */
  gear: Int8Array;
  /** Lap length covered (samples × grid), m. */
  length: number;
  /** Shift points: s (m), from gear, to gear, and the driver's rpm just before the shift. */
  shifts: { s: number; from: number; to: number; rpm: number }[];
}

/**
 * Derive the gear the driver used at every sample of `lap` (on a `grid`-metre grid).
 * For each sample with v > 3 m/s and an rpm reading, the gear is the one whose overall ratio is
 * closest (in log ratio) to rpm·2πr / (60·v); samples further than 12 % from every ratio (clutch
 * in, wheelspin, logger lag) and slow samples take the neighbouring gear. Runs shorter than
 * `minRun` metres (default 30, about a second) are merged into their neighbours (single-sample glitches, 1 Hz GPS, nobody shifts twice within a second).
 */
export function deriveGearSchedule(spec: CarSpec, lap: GhostLapLike, grid = 2, minRun = 30): GearSchedule {
  const v = lap.v_mps, rpm = lap.rpm ?? [];
  const n = v.length;
  const ratios = spec.drivetrain.gearRatios;
  const r = spec.wheel.radius;
  const raw = new Int8Array(n);
  for (let i = 0; i < n; i++) {
    const rp = rpm[i];
    if (!(v[i] > 3) || !(rp > 500)) continue;
    const ratio = (rp * 2 * Math.PI * r) / (60 * v[i]);
    let best = 0, bd = Infinity;
    for (let k = 0; k < ratios.length; k++) {
      const d = Math.abs(dlog(ratio / ratios[k]));
      if (d < bd) { bd = d; best = k + 1; }
    }
    if (bd < dlog(1.12)) raw[i] = best;
  }
  // fill unknown samples from the nearest known neighbour (wrapping: the lap is a loop)
  const g = new Int8Array(n);
  let anyKnown = false;
  for (let i = 0; i < n; i++) if (raw[i]) { anyKnown = true; break; }
  if (!anyKnown) { g.fill(1); return { grid, gear: g, length: n * grid, shifts: [] }; }
  for (let i = 0; i < n; i++) {
    if (raw[i]) { g[i] = raw[i]; continue; }
    for (let d = 1; d < n; d++) {
      const a = raw[(i - d + n) % n], b = raw[(i + d) % n];
      if (a || b) { g[i] = a || b; break; }
    }
  }
  // merge short runs into the longer neighbouring run (repeat until stable)
  const minSamples = Math.max(1, Math.round(minRun / grid));
  for (let pass = 0; pass < 5; pass++) {
    let changed = false;
    let i = 0;
    while (i < n) {
      let j = i;
      while (j + 1 < n && g[j + 1] === g[i]) j++;
      const len = j - i + 1;
      if (len < minSamples && len < n) {
        const prev = g[(i - 1 + n) % n], next = g[(j + 1) % n];
        const fill = prev === next ? prev : (Math.abs(prev - g[i]) <= Math.abs(next - g[i]) ? prev : next);
        for (let k = i; k <= j; k++) g[k] = fill;
        changed = true;
      }
      i = j + 1;
    }
    if (!changed) break;
  }
  const shifts: GearSchedule['shifts'] = [];
  for (let i = 1; i < n; i++) {
    if (g[i] !== g[i - 1]) shifts.push({ s: i * grid, from: g[i - 1], to: g[i], rpm: rpm[i - 1] ?? NaN });
  }
  return { grid, gear: g, length: n * grid, shifts };
}

/** Scheduled gear at s (m, wrapped). */
export function scheduleGearAt(sch: GearSchedule, s: number): number {
  const L = sch.length;
  const u = (((s % L) + L) % L) / sch.grid;
  return sch.gear[Math.floor(u) % sch.gear.length];
}

/**
 * Target gear with hysteresis: a change in the schedule only counts once the car is `lag` metres
 * past it (the gear `lag` metres back already shows it), so the target does not flicker around a
 * shift point.
 */
export function scheduleTargetAt(sch: GearSchedule, s: number, lag = 3): number {
  const a = scheduleGearAt(sch, s), b = scheduleGearAt(sch, s - lag);
  return a === b ? a : b;
}

/** Driver's shift rpm per gear transition (median over the lap), for reports. */
export function shiftRpmSummary(sch: GearSchedule): { from: number; to: number; rpm: number; count: number }[] {
  const by = new Map<string, number[]>();
  for (const sh of sch.shifts) {
    const k = `${sh.from}>${sh.to}`;
    if (!by.has(k)) by.set(k, []);
    if (Number.isFinite(sh.rpm)) by.get(k)!.push(sh.rpm);
  }
  return [...by.entries()].map(([k, a]) => {
    const [from, to] = k.split('>').map(Number);
    a.sort((x, y) => x - y);
    return { from, to, rpm: a.length ? a[Math.floor(a.length / 2)] : NaN, count: a.length };
  });
}
