// The race field on phones and tablets (owner's decision, 26 Oct 2026): 40 AI cars instead of the whole entry list (133 at
// Sonoma), because iPhone and iPad Safari run out of memory with every car. The 40 are the Probe's pace neighbours, so
// the race around the player is the real one:
//
//   the player's expected pace band = its pace.json row's targetLap ± sigma (Sonoma 151.7 ± 7.9 s; Laguna 128.7 ± 6.7 s);
//   each AI car's distance = how far its targetLap lies outside that band (0 inside it); the 40 smallest win, ties by
//   |targetLap − the player's targetLap|, then by the real grid. The chosen cars keep their real relative order (the
//   pace.json order and grid numbers are untouched; the race director's seeded start-order shuffle applies as on desktop).
//
// Desktop keeps the full field; hot laps are unaffected. Pure (unit-tested).
import type { DeviceClass } from './quality';

export const MOBILE_FIELD = 40;

interface PaceRow { number: string; grid: number; targetLap: number; sigma?: number; player?: boolean }
interface PaceLike { cars: PaceRow[] }

/** How many AI cars this device races against (Infinity = all). */
export const fieldCapFor = (device: DeviceClass): number => (device === 'desktop' ? Infinity : MOBILE_FIELD);

/** The AI cars of a pace file (every row but the player's). */
export const aiCount = (pace: unknown, playerNumber: string): number =>
  ((pace as PaceLike | null)?.cars ?? []).filter((c) => c.number !== playerNumber).length;

/**
 * The pace file with at most `n` AI cars: the player's pace neighbours (see above), in the file's own order. The player's
 * row stays. Unchanged when the field is already small enough or the player has no row.
 */
export function neighbourField<T extends PaceLike>(pace: T, n: number, playerNumber: string): T {
  const ai = pace.cars.filter((c) => c.number !== playerNumber);
  if (!(ai.length > n)) return pace;
  const me = pace.cars.find((c) => c.number === playerNumber);
  const centre = me && Number.isFinite(me.targetLap) ? me.targetLap : median(ai.map((c) => c.targetLap));
  const half = me && Number.isFinite(me.sigma) ? Math.max(0, me.sigma!) : 0;
  const keyed = ai.map((c) => {
    const d = Math.abs(c.targetLap - centre);
    return { c, out: Math.max(0, d - half), d };
  });
  keyed.sort((a, b) => a.out - b.out || a.d - b.d || a.c.grid - b.c.grid);
  const keep = new Set(keyed.slice(0, n).map((k) => k.c));
  return { ...pace, cars: pace.cars.filter((c) => c.number === playerNumber || keep.has(c)) };
}

function median(a: number[]): number {
  const s = a.filter(Number.isFinite).sort((x, y) => x - y);
  return s.length ? s[Math.floor(s.length / 2)] : 0;
}

/** The Start menu's field line: "40 of 133 cars on this device" (phones, tablets) / "all 133 cars". */
export function fieldLine(total: number, device: DeviceClass): string {
  const cap = fieldCapFor(device);
  return total > cap ? `${cap} of ${total} cars on this device` : `all ${total} cars`;
}
