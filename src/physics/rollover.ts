// Rolled over (Oct 2026): the kerb traversal gate's definition (src/physics/__tests__/kerbprobe.ts), shared with the
// app's rollover game over. Roll is the car's lean about its long axis relative to the road normal under it.

/** A car whose roll relative to the road passes this has rolled over (the kerb gate's `rolledOver`). */
export const ROLLOVER_RAD = Math.PI / 3;

/** Roll (rad, signed) of a body with quaternion q = [x, y, z, w] (body x forward, y left, z up) relative to normal n. */
export function rollOf(q: readonly number[], n: readonly [number, number, number] | readonly number[]): number {
  const [x, y, z, w] = q;
  const ey = [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)];
  const ez = [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)];
  return Math.atan2(ey[0] * n[0] + ey[1] * n[1] + ey[2] * n[2], ez[0] * n[0] + ez[1] * n[1] + ez[2] * n[2]);
}

/** True when the car has rolled over on a road with normal n. */
export function isRolledOver(q: readonly number[], n: readonly number[]): boolean {
  return Math.abs(rollOf(q, n)) > ROLLOVER_RAD;
}
