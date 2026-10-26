// The pow argument sets the server probe evaluated (tools/determinism/pow_server.json; docs/determinism.md section 5).
// The same generator is inlined in the throwaway probe function (branch powprobe, api/powprobe.ts); the probe also
// returned the SHA-256 of the arguments, so a mismatch in generation would show. Exact operations only.

export const LS_EXP = -0.1;              // car.json tyre.loadSensitivity (the tyre's (Fz/Fz0)^lsExp)
export const PEDAL_EXPS = [1, 1.5, 2.5]; // car.json brakes.pedalExponent is 1 (default; the call is skipped); two more for coverage
export const N = 100_000;

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  const next32 = (): number => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return (t ^ (t >>> 14)) >>> 0;
  };
  return () => ((next32() >>> 5) * 67108864 + (next32() >>> 6)) / 9007199254740992;
}
const F = new Float64Array(1), U = new Uint32Array(F.buffer);
/** 2^e for -1022 <= e <= 1023, from the bits (little-endian hosts). */
function pow2(e: number): number { U[1] = (e + 1023) << 20; U[0] = 0; return F[0]; }

/** [x0, y0, x1, y1, ...] for each set. */
export function powSets(): Record<string, Float64Array> {
  const load = new Float64Array(2 * (N + 1));
  for (let i = 0; i <= N; i++) { load[2 * i] = (3 * i) / N; load[2 * i + 1] = LS_EXP; }
  const sets: Record<string, Float64Array> = { load };
  for (const e of PEDAL_EXPS) {
    const a = new Float64Array(2 * (N + 1));
    for (let i = 0; i <= N; i++) { a[2 * i] = i / N; a[2 * i + 1] = e; }
    sets[`pedal${e}`] = a;
  }
  const r = mulberry32(20261026), rnd = new Float64Array(2 * N);
  for (let i = 0; i < N; i++) {
    const e = -20 + Math.floor(r() * 41);            // x log-uniform over 2^-20 .. 2^21
    rnd[2 * i] = (1 + r()) * pow2(e);
    rnd[2 * i + 1] = -8 + 16 * r();                  // y uniform on [-8, 8)
  }
  sets.random = rnd;
  return sets;
}
