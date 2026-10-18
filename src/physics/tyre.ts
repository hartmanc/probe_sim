// Pacejka Magic Formula helpers.

/** Normalized Magic Formula: sin(C·atan(Bx − E·(Bx − atan(Bx)))), peak value 1. */
export function mfShape(B: number, C: number, E: number, x: number): number {
  const bx = B * x;
  return Math.sin(C * Math.atan(bx - E * (bx - Math.atan(bx))));
}

/**
 * Solve for B such that the Magic Formula with shape C and curvature E peaks
 * at slip xPeak. The peak occurs where C·atan(φ) = π/2, φ = (1−E)·u + E·atan(u), u = B·x.
 */
export function solveMfB(C: number, E: number, xPeak: number): number {
  if (!(C > 1)) throw new Error('Magic Formula C must be > 1 for a peak to exist');
  const target = Math.tan(Math.PI / (2 * C));
  const phi = (u: number) => (1 - E) * u + E * Math.atan(u);
  // phi is monotonic for E ≤ 1; bisection on u.
  let lo = 0, hi = 1;
  while (phi(hi) < target) hi *= 2;
  for (let i = 0; i < 100; i++) {
    const mid = 0.5 * (lo + hi);
    if (phi(mid) < target) lo = mid; else hi = mid;
  }
  return (0.5 * (lo + hi)) / xPeak;
}
