// Deterministic maths for the physics (determinism round, 26 Oct 2026; docs/determinism.md).
//
// JavaScript's + - * / and Math.sqrt / floor / ceil / trunc / round / abs / min / max / fround are exact IEEE operations
// and give the same bits in every engine. The transcendental Math functions are not specified to the bit: V8 (Node, the
// scoreboard server, Chrome), JavaScriptCore (Safari, every iPhone browser) and SpiderMonkey (Firefox) round differently
// in the last place now and then, and over thousands of physics steps a last-bit difference grows into a different lap.
// The physics therefore calls these software versions, bit-identical to Node's V8 (the server), on every engine.
//
// Provenance: a line-for-line port of V8 14.6's src/base/ieee754.cc (fdlibm 5.3, Sun Microsystems 1993, as modified
// by Google; V8 tag 14.6.202.34, the V8 of Node 26.12): __ieee754_rem_pio2, __kernel_rem_pio2 (prec 2), __kernel_sin,
// __kernel_cos, __kernel_tan, sin / cos (Node's V8 is built without V8_USE_LIBM_TRIG_FUNCTIONS, so Math.sin / cos are
// the fdlibm ones, not the glibc port Chrome ships), tan, atan, atan2, exp, log; and of V8's Torque builtin
// FastMathHypot (src/builtins/math.tq) for hypot of 2 and 3 arguments. Math.pow is NOT here: V8 delegates it to the
// platform C library (std::pow, flag --use-std-math-pow, default on), so there is no single V8 pow to match.
//
// Only exact operations are used inside (no Math.* apart from abs / floor / trunc / sqrt). Word access goes through a
// shared Float64Array / Uint32Array pair with the endianness detected once. The C integer conversions are mirrored:
// `(int32)d` -> `d | 0` (always in range here), C's arithmetic >> on int32 -> JS >>.
//
// ====================================================
// Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
//
// Developed at SunSoft, a Sun Microsystems, Inc. business.
// Permission to use, copy, modify, and distribute this
// software is freely granted, provided that this notice
// is preserved.
// ====================================================
// Modifications Copyright 2016 the V8 project authors (BSD-style licence).

import { POW_LN2HI, POW_LN2LO, POW_A, POW_TAB, EXP_INVLN2N, EXP_NEGLN2HIN, EXP_NEGLN2LON, EXP_SHIFT, EXP_C, EXP_TAB_U32 } from './dmath_pow_data';

const F64 = new Float64Array(1);
const U32 = new Uint32Array(F64.buffer);
// Word order: every engine this ships to runs little-endian (x86-64, arm64); literal indices keep the hot paths free of a
// module-level lookup. A big-endian host would get wrong bits, so refuse it loudly.
if (new Uint8Array(new Uint16Array([1]).buffer)[0] !== 1) throw new Error('dmath: big-endian host not supported');
const HI = 1, LO = 0;

/** High 32 bits of x as a signed int32 (C: int32_t hx = bits >> 32). */
function hiWord(x: number): number { F64[0] = x; return U32[1] | 0; }
/** Low 32 bits of x as an unsigned int32. */
function loWord(x: number): number { F64[0] = x; return U32[0]; }
/** INSERT_WORDS. */
function fromWords(hi: number, lo: number): number { U32[1] = hi; U32[0] = lo; return F64[0]; }
/** SET_LOW_WORD(x, 0). */
function clearLow(x: number): number { F64[0] = x; U32[0] = 0; return F64[0]; }

/** The double whose high word is `hi` and low word 0. For a non-NaN x with high word hx (sign masked: ix),
 *  `ix < hi` is exactly `|x| < atHi(hi)` and `ix >= hi` is `|x| >= atHi(hi)`: the hot paths compare doubles instead of
 *  extracting words (same branches, no typed-array round trip). */
function atHi(hi: number): number { return fromWords(hi, 0); }

/** scalbn(x, n) = x · 2^n, exact for the normal-range results it is used for here (stepwise like the C library's). */
function scalbn(x: number, n: number): number {
  while (n > 1023) { x *= 8.98846567431158e307; n -= 1023; }          // 0x1p1023
  while (n < -1022) { x *= 2.2250738585072014e-308; n += 1022; }       // 0x1p-1022
  return x * fromWords((n + 1023) << 20, 0);
}

// ---------------------------------------------------------------- argument reduction (__ieee754_rem_pio2)

const TWO_OVER_PI = new Int32Array([
  0xA2F983, 0x6E4E44, 0x1529FC, 0x2757D1, 0xF534DD, 0xC0DB62, 0x95993C,
  0x439041, 0xFE5163, 0xABDEBB, 0xC561B7, 0x246E3A, 0x424DD2, 0xE00649,
  0x2EEA09, 0xD1921C, 0xFE1DEB, 0x1CB129, 0xA73EE8, 0x8235F5, 0x2EBB44,
  0x84E99C, 0x7026B4, 0x5F7E41, 0x3991D6, 0x398353, 0x39F49C, 0x845F8B,
  0xBDF928, 0x3B1FF8, 0x97FFDE, 0x05980F, 0xEF2F11, 0x8B5A0A, 0x6D1F6D,
  0x367ECF, 0x27CB09, 0xB74F46, 0x3F669E, 0x5FEA2D, 0x7527BA, 0xC7EBE5,
  0xF17B3D, 0x0739F7, 0x8A5292, 0xEA6BFB, 0x5FB11F, 0x8D5D08, 0x560330,
  0x46FC7B, 0x6BABF0, 0xCFBC20, 0x9AF436, 0x1DA9E3, 0x91615E, 0xE61B08,
  0x659985, 0x5F14A0, 0x68408D, 0xFFD880, 0x4D7327, 0x310606, 0x1556CA,
  0x73A8C9, 0x60E27B, 0xC08C6B,
]);

const NPIO2_HW = new Int32Array([
  0x3FF921FB, 0x400921FB, 0x4012D97C, 0x401921FB, 0x401F6A7A, 0x4022D97C,
  0x4025FDBB, 0x402921FB, 0x402C463A, 0x402F6A7A, 0x4031475C, 0x4032D97C,
  0x40346B9C, 0x4035FDBB, 0x40378FDB, 0x403921FB, 0x403AB41B, 0x403C463A,
  0x403DD85A, 0x403F6A7A, 0x40407E4C, 0x4041475C, 0x4042106C, 0x4042D97C,
  0x4043A28C, 0x40446B9C, 0x404534AC, 0x4045FDBB, 0x4046C6CB, 0x40478FDB,
  0x404858EB, 0x404921FB,
]);

const invpio2 = 6.36619772367581382433e-01; /* 0x3FE45F30, 0x6DC9C883 */
const pio2_1 = 1.57079632673412561417e+00;  /* 0x3FF921FB, 0x54400000 */
const pio2_1t = 6.07710050650619224932e-11; /* 0x3DD0B461, 0x1A626331 */
const pio2_2 = 6.07710050630396597660e-11;  /* 0x3DD0B461, 0x1A600000 */
const pio2_2t = 2.02226624879595063154e-21; /* 0x3BA3198A, 0x2E037073 */
const pio2_3 = 2.02226624871116645580e-21;  /* 0x3BA3198A, 0x2E000000 */
const pio2_3t = 8.47842766036889956997e-32; /* 0x397B839A, 0x252049C1 */
const two24 = 1.67772160000000000000e+07;   /* 0x41700000, 0x00000000 */
const twon24 = 5.96046447753906250000e-08;  /* 0x3E700000, 0x00000000 */

/** y[0] + y[1] of the last remPio2 call (the C out-parameter). */
let Y0 = 0, Y1 = 0;

const PIO2 = new Float64Array([
  1.57079625129699707031e+00, /* 0x3FF921FB, 0x40000000 */
  7.54978941586159635335e-08, /* 0x3E74442D, 0x00000000 */
  5.39030252995776476554e-15, /* 0x3CF84698, 0x80000000 */
  3.28200341580791294123e-22, /* 0x3B78CC51, 0x60000000 */
  1.27065575308067607349e-29, /* 0x39F01B83, 0x80000000 */
  1.22933308981111328932e-36, /* 0x387A2520, 0x40000000 */
  2.73370053816464559624e-44, /* 0x36E38222, 0x80000000 */
  2.16741683877804819444e-51, /* 0x3569F31D, 0x00000000 */
]);
const KX = new Float64Array(3);
const KF = new Float64Array(20), KFQ = new Float64Array(20), KQ = new Float64Array(20);
const KIQ = new Int32Array(20);

/** __kernel_rem_pio2(x, y, e0, nx, prec = 2, two_over_pi): writes Y0, Y1, returns n & 7. */
function kernelRemPio2(x: Float64Array, e0: number, nx: number): number {
  const f = KF, fq = KFQ, q = KQ, iq = KIQ;
  const jk = 4;              // init_jk[prec = 2]
  const jp = jk;
  const jx = nx - 1;
  let jv = Math.trunc((e0 - 3) / 24);
  if (jv < 0) jv = 0;
  let q0 = e0 - 24 * (jv + 1);

  let j = jv - jx;
  const m = jx + jk;
  for (let i = 0; i <= m; i++, j++) f[i] = j < 0 ? 0 : TWO_OVER_PI[j];

  let fw: number;
  for (let i = 0; i <= jk; i++) {
    fw = 0.0;
    for (j = 0; j <= jx; j++) fw += x[j] * f[jx + i - j];
    q[i] = fw;
  }

  let jz = jk;
  let z: number, n: number, ih: number, carry: number;
  for (;;) {   // recompute:
    let i = 0;
    for (j = jz, z = q[jz]; j > 0; i++, j--) {
      fw = (twon24 * z) | 0;
      iq[i] = (z - two24 * fw) | 0;
      z = q[j - 1] + fw;
    }

    z = scalbn(z, q0);
    z -= 8.0 * Math.floor(z * 0.125);
    n = z | 0;
    z -= n;
    ih = 0;
    if (q0 > 0) {
      i = iq[jz - 1] >> (24 - q0);
      n += i;
      iq[jz - 1] -= i << (24 - q0);
      ih = iq[jz - 1] >> (23 - q0);
    } else if (q0 === 0) {
      ih = iq[jz - 1] >> 23;
    } else if (z >= 0.5) {
      ih = 2;
    }

    if (ih > 0) {
      n += 1;
      carry = 0;
      for (i = 0; i < jz; i++) {
        j = iq[i];
        if (carry === 0) {
          if (j !== 0) { carry = 1; iq[i] = 0x1000000 - j; }
        } else {
          iq[i] = 0xFFFFFF - j;
        }
      }
      if (q0 > 0) {
        if (q0 === 1) iq[jz - 1] &= 0x7FFFFF;
        else if (q0 === 2) iq[jz - 1] &= 0x3FFFFF;
      }
      if (ih === 2) {
        z = 1.0 - z;
        if (carry !== 0) z -= scalbn(1.0, q0);
      }
    }

    if (z === 0) {
      j = 0;
      for (i = jz - 1; i >= jk; i--) j |= iq[i];
      if (j === 0) {   // need recomputation
        let k = 1;
        while (jk >= k && iq[jk - k] === 0) k++;
        for (i = jz + 1; i <= jz + k; i++) {
          f[jx + i] = TWO_OVER_PI[jv + i];
          fw = 0.0;
          for (j = 0; j <= jx; j++) fw += x[j] * f[jx + i - j];
          q[i] = fw;
        }
        jz += k;
        continue;
      }
    }
    break;
  }

  if (z === 0.0) {
    jz -= 1;
    q0 -= 24;
    while (iq[jz] === 0) { jz--; q0 -= 24; }
  } else {
    z = scalbn(z, -q0);
    if (z >= two24) {
      fw = (twon24 * z) | 0;
      iq[jz] = z - two24 * fw;   // C: implicit double -> int32 (exact integer here)
      jz += 1;
      q0 += 24;
      iq[jz] = fw;
    } else {
      iq[jz] = z;
    }
  }

  fw = scalbn(1.0, q0);
  for (let i = jz; i >= 0; i--) { q[i] = fw * iq[i]; fw *= twon24; }

  for (let i = jz; i >= 0; i--) {
    fw = 0.0;
    for (let k = 0; k <= jp && k <= jz - i; k++) fw += PIO2[k] * q[i + k];
    fq[jz - i] = fw;
  }

  // prec 2: compress fq[] into y[0], y[1]
  fw = 0.0;
  for (let i = jz; i >= 0; i--) fw += fq[i];
  Y0 = ih === 0 ? fw : -fw;
  fw = fq[0] - fw;
  for (let i = 1; i <= jz; i++) fw += fq[i];
  Y1 = ih === 0 ? fw : -fw;
  return n & 7;
}

/** __ieee754_rem_pio2(x, y): x - n·pi/2 in Y0 + Y1, returns n. Callers handle |x| <= pi/4 and non-finite x. */
const RP_3PIO4 = atHi(0x4002D97C), RP_PIO2_LO = atHi(0x3FF921FB), RP_PIO2_HI = atHi(0x3FF921FC);
function remPio2(x: number): number {
  const ax = Math.abs(x);
  let z: number;
  if (ax < RP_3PIO4) {   /* |x| < 3pi/4, special case with n=+-1 */
    const nearPio2 = ax >= RP_PIO2_LO && ax < RP_PIO2_HI;   /* ix == 0x3FF921FB */
    if (x > 0) {
      z = x - pio2_1;
      if (!nearPio2) { Y0 = z - pio2_1t; Y1 = (z - Y0) - pio2_1t; }
      else { z -= pio2_2; Y0 = z - pio2_2t; Y1 = (z - Y0) - pio2_2t; }
      return 1;
    } else {
      z = x + pio2_1;
      if (!nearPio2) { Y0 = z + pio2_1t; Y1 = (z - Y0) + pio2_1t; }
      else { z += pio2_2; Y0 = z + pio2_2t; Y1 = (z - Y0) + pio2_2t; }
      return -1;
    }
  }
  const hx = hiWord(x);
  const ix = hx & 0x7FFFFFFF;
  if (ix <= 0x413921FB) {   /* |x| ~<= 2^19*(pi/2), medium size */
    let t = Math.abs(x);
    const n = (t * invpio2 + 0.5) | 0;
    const fn = n;
    let r = t - fn * pio2_1;
    let w = fn * pio2_1t;
    if (n < 32 && ix !== NPIO2_HW[n - 1]) {
      Y0 = r - w;
    } else {
      const j = ix >> 20;
      Y0 = r - w;
      let high = hiWord(Y0);
      let i = j - ((high >> 20) & 0x7FF);
      if (i > 16) {   /* 2nd iteration needed, good to 118 */
        t = r;
        w = fn * pio2_2;
        r = t - w;
        w = fn * pio2_2t - ((t - r) - w);
        Y0 = r - w;
        high = hiWord(Y0);
        i = j - ((high >> 20) & 0x7FF);
        if (i > 49) {   /* 3rd iteration need, 151 bits acc */
          t = r;
          w = fn * pio2_3;
          r = t - w;
          w = fn * pio2_3t - ((t - r) - w);
          Y0 = r - w;
        }
      }
    }
    Y1 = (r - Y0) - w;
    if (hx < 0) { Y0 = -Y0; Y1 = -Y1; return -n; }
    return n;
  }
  if (ix >= 0x7FF00000) { Y0 = Y1 = x - x; return 0; }
  /* set z = scalbn(|x|,ilogb(x)-23) */
  const low = loWord(x);
  const e0 = (ix >> 20) - 1046;
  z = fromWords(ix - (e0 << 20), low);
  const tx = KX;
  for (let i = 0; i < 2; i++) { tx[i] = z | 0; z = (z - tx[i]) * two24; }
  tx[2] = z;
  let nx = 3;
  while (tx[nx - 1] === 0) nx--;
  const n = kernelRemPio2(tx, e0, nx);
  if (hx < 0) { Y0 = -Y0; Y1 = -Y1; return -n; }
  return n;
}

// ---------------------------------------------------------------- kernels on [-pi/4, pi/4]

const C1 = 4.16666666666666019037e-02;  /* 0x3FA55555, 0x5555554C */
const C2 = -1.38888888888741095749e-03; /* 0xBF56C16C, 0x16C15177 */
const C3 = 2.48015872894767294178e-05;  /* 0x3EFA01A0, 0x19CB1590 */
const C4 = -2.75573143513906633035e-07; /* 0xBE927E4F, 0x809C52AD */
const C5 = 2.08757232129817482790e-09;  /* 0x3E21EE9E, 0xBDB4B1C4 */
const C6 = -1.13596475577881948265e-11; /* 0xBDA8FAE9, 0xBE8838D4 */

/** __kernel_cos(x, y). */
const KC_TINY = atHi(0x3E400000), KC_03 = atHi(0x3FD33333), KC_078 = atHi(0x3FE90001);
function kernelCos(x: number, y: number): number {
  const ax = Math.abs(x);
  if (ax < KC_TINY) {   /* if x < 2**27 */
    if ((x | 0) === 0) return 1.0;
  }
  const z = x * x;
  const r = z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))));
  if (ax < KC_03) {   /* if |x| < 0.3 */
    return 1.0 - (0.5 * z - (z * r - x * y));
  }
  /* x > 0.78125 ? 0.28125 : x/4 with the low word cleared (INSERT_WORDS(qx, ix - 0x00200000, 0)) */
  // clearLow(|x|) / 4 without the word round trip: |x| in [0.3, 0.78125) has exponent -2 or -1, so clearing the low 32
  // mantissa bits is truncating to multiples of 2^-22 or 2^-21 (exact: floor of an exact power-of-two scaling)
  const qx = ax >= KC_078 ? 0.28125 : ax < 0.5 ? Math.floor(ax * 4194304) * 5.960464477539063e-8 : Math.floor(ax * 2097152) * 1.1920928955078125e-7;
  const iz = 0.5 * z - qx;
  const a = 1.0 - qx;
  return a - (iz - (z * r - x * y));
}

const S1 = -1.66666666666666324348e-01; /* 0xBFC55555, 0x55555549 */
const S2 = 8.33333333332248946124e-03;  /* 0x3F811111, 0x1110F8A6 */
const S3 = -1.98412698298579493134e-04; /* 0xBF2A01A0, 0x19C161D5 */
const S4 = 2.75573137070700676789e-06;  /* 0x3EC71DE3, 0x57B1FE7D */
const S5 = -2.50507602534068634195e-08; /* 0xBE5AE5E6, 0x8A2B9CEB */
const S6 = 1.58969099521155010221e-10;  /* 0x3DE5D93A, 0x5ACFD57C */

/** __kernel_sin(x, y, iy). */
function kernelSin(x: number, y: number, iy: number): number {
  if (Math.abs(x) < KC_TINY) {   /* |x| < 2**-27 */
    if ((x | 0) === 0) return x;
  }
  const z = x * x;
  const v = z * x;
  const r = S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)));
  if (iy === 0) return x + v * (S1 + z * r);
  return x - ((z * (0.5 * y - v * r) - y) - v * S1);
}

const T = new Float64Array([
  3.33333333333334091986e-01,  /* 3FD55555, 55555563 */
  1.33333333333201242699e-01,  /* 3FC11111, 1110FE7A */
  5.39682539762260521377e-02,  /* 3FABA1BA, 1BB341FE */
  2.18694882948595424599e-02,  /* 3F9664F4, 8406D637 */
  8.86323982359930005737e-03,  /* 3F8226E3, E96E8493 */
  3.59207910759131235356e-03,  /* 3F6D6D22, C9560328 */
  1.45620945432529025516e-03,  /* 3F57DBC8, FEE08315 */
  5.88041240820264096874e-04,  /* 3F4344D8, F2F26501 */
  2.46463134818469906812e-04,  /* 3F3026F7, 1A8D1068 */
  7.81794442939557092300e-05,  /* 3F147E88, A03792A6 */
  7.14072491382608190305e-05,  /* 3F12B80F, 32F0A7E9 */
  -1.85586374855275456654e-05, /* BEF375CB, DB605373 */
  2.59073051863633712884e-05,  /* 3EFB2A70, 74BF7AD4 */
]);
const pio4 = 7.85398163397448278999e-01;   /* 3FE921FB, 54442D18 */
const pio4lo = 3.06161699786838301793e-17; /* 3C81A626, 33145C07 */

/** __kernel_tan(x, y, iy): tan (iy = 1) or -1/tan (iy = -1). */
function kernelTan(x: number, y: number, iy: number): number {
  let z: number, r: number, v: number, w: number, s: number;
  const hx = hiWord(x);
  const ix = hx & 0x7FFFFFFF;
  if (ix < 0x3E300000) {   /* x < 2**-28 */
    if ((x | 0) === 0) {
      const low = loWord(x);
      if (((ix | low) | (iy + 1)) === 0) return 1.0 / Math.abs(x);
      if (iy === 1) return x;
      /* compute -1 / (x+y) carefully */
      z = w = x + y;
      z = clearLow(z);
      v = y - (z - x);
      const a = -1.0 / w;
      const t = clearLow(a);
      s = 1.0 + t * z;
      return t + a * (s + t * v);
    }
  }
  if (ix >= 0x3FE59428) {   /* |x| >= 0.6744 */
    if (hx < 0) { x = -x; y = -y; }
    z = pio4 - x;
    w = pio4lo - y;
    x = z + w;
    y = 0.0;
  }
  z = x * x;
  w = z * z;
  r = T[1] + w * (T[3] + w * (T[5] + w * (T[7] + w * (T[9] + w * T[11]))));
  v = z * (T[2] + w * (T[4] + w * (T[6] + w * (T[8] + w * (T[10] + w * T[12])))));
  s = z * x;
  r = y + z * (s * (r + v) + y);
  r += T[0] * s;
  w = x + r;
  if (ix >= 0x3FE59428) {
    v = iy;
    return (1 - ((hx >> 30) & 2)) * (v - 2.0 * (x - (w * w / (w + v) - r)));
  }
  if (iy === 1) return w;
  /* compute -1.0 / (x+r) accurately */
  z = clearLow(w);
  v = r - (z - x);
  const a = -1.0 / w;
  const t = clearLow(a);
  s = 1.0 + t * z;
  return t + a * (s + t * v);
}

// ---------------------------------------------------------------- public functions

/** Math.sin as V8 (fdlibm sin). */
const PIO4_UP = atHi(0x3FE921FC);   /* ix <= 0x3FE921FB  <=>  |x| < PIO4_UP */
export function sin(x: number): number {
  // the common case (89 % of the physics' calls: 2^-27 <= |x| < pi/4, __kernel_sin with iy = 0) inline-sized
  const ax = Math.abs(x);
  if (ax < PIO4_UP && ax >= KC_TINY) {
    const z = x * x, v = z * x;
    return x + v * (S1 + z * (S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)))));
  }
  return sinRest(x, ax);
}
function sinRest(x: number, ax: number): number {
  if (ax < PIO4_UP) return kernelSin(x, 0.0, 0);
  if (!(ax < Infinity)) return x - x;
  const n = remPio2(x);
  switch (n & 3) {
    case 0: return kernelSin(Y0, Y1, 1);
    case 1: return kernelCos(Y0, Y1);
    case 2: return -kernelSin(Y0, Y1, 1);
    default: return -kernelCos(Y0, Y1);
  }
}

/** Math.cos as V8 (fdlibm cos). */
export function cos(x: number): number {
  const ax = Math.abs(x);
  if (ax < PIO4_UP) return kernelCos(x, 0.0);
  if (!(ax < Infinity)) return x - x;
  const n = remPio2(x);
  switch (n & 3) {
    case 0: return kernelCos(Y0, Y1);
    case 1: return -kernelSin(Y0, Y1, 1);
    case 2: return -kernelCos(Y0, Y1);
    default: return kernelSin(Y0, Y1, 1);
  }
}

/** Math.tan as V8 (fdlibm tan). */
export function tan(x: number): number {
  const ix = hiWord(x) & 0x7FFFFFFF;
  if (ix <= 0x3FE921FB) return kernelTan(x, 0.0, 1);
  if (ix >= 0x7FF00000) return x - x;
  const n = remPio2(x);
  return kernelTan(Y0, Y1, 1 - ((n & 1) << 1));
}

const ATANHI = new Float64Array([
  4.63647609000806093515e-01, /* atan(0.5)hi 0x3FDDAC67, 0x0561BB4F */
  7.85398163397448278999e-01, /* atan(1.0)hi 0x3FE921FB, 0x54442D18 */
  9.82793723247329054082e-01, /* atan(1.5)hi 0x3FEF730B, 0xD281F69B */
  1.57079632679489655800e+00, /* atan(inf)hi 0x3FF921FB, 0x54442D18 */
]);
const ATANLO = new Float64Array([
  2.26987774529616870924e-17, /* atan(0.5)lo 0x3C7A2B7F, 0x222F65E2 */
  3.06161699786838301793e-17, /* atan(1.0)lo 0x3C81A626, 0x33145C07 */
  1.39033110312309984516e-17, /* atan(1.5)lo 0x3C700788, 0x7AF0CBBD */
  6.12323399573676603587e-17, /* atan(inf)lo 0x3C91A626, 0x33145C07 */
]);
const ATANHI0 = ATANHI[0], ATANHI1 = ATANHI[1], ATANHI2 = ATANHI[2], ATANHI3 = ATANHI[3];
const ATANLO0 = ATANLO[0], ATANLO1 = ATANLO[1], ATANLO2 = ATANLO[2], ATANLO3 = ATANLO[3];
const aT0 = 3.33333333333329318027e-01;  /* 0x3FD55555, 0x5555550D */
const aT1 = -1.99999999998764832476e-01; /* 0xBFC99999, 0x9998EBC4 */
const aT2 = 1.42857142725034663711e-01;  /* 0x3FC24924, 0x920083FF */
const aT3 = -1.11111104054623557880e-01; /* 0xBFBC71C6, 0xFE231671 */
const aT4 = 9.09088713343650656196e-02;  /* 0x3FB745CD, 0xC54C206E */
const aT5 = -7.69187620504482999495e-02; /* 0xBFB3B0F2, 0xAF749A6D */
const aT6 = 6.66107313738753120669e-02;  /* 0x3FB10D66, 0xA0D03D51 */
const aT7 = -5.83357013379057348645e-02; /* 0xBFADDE2D, 0x52DEFD9A */
const aT8 = 4.97687799461593236017e-02;  /* 0x3FA97B4B, 0x24760DEB */
const aT9 = -3.65315727442169155270e-02; /* 0xBFA2B444, 0x2C6A6C2F */
const aT10 = 1.62858201153657823623e-02; /* 0x3F90AD3A, 0xE322DA11 */

/** Math.atan as V8 (fdlibm atan). */
const AT_2P66 = atHi(0x44100000), AT_04375 = atHi(0x3FDC0000), AT_TINY = atHi(0x3E400000), AT_11875 = atHi(0x3FF30000),
  AT_06875 = atHi(0x3FE60000), AT_24375 = atHi(0x40038000);
export function atan(x: number): number {
  // the common case (82 % of the physics' calls: |x| < 0.4375) in a function small enough for the JIT to inline
  const ax = Math.abs(x);
  if (ax < AT_04375 && ax >= AT_TINY) {
    const z = x * x, w = z * z;
    const s1 = z * (aT0 + w * (aT2 + w * (aT4 + w * (aT6 + w * (aT8 + w * aT10)))));
    const s2 = w * (aT1 + w * (aT3 + w * (aT5 + w * (aT7 + w * aT9))));
    return x - x * (s1 + s2);
  }
  return atanRest(x, ax);
}
function atanRest(x: number, ax: number): number {
  if (ax < AT_TINY) return x;   /* |x| < 2^-27 (huge + x > one is always true) */
  if (!(ax < AT_2P66)) return atanHuge(x);   /* |x| >= 2^66, or NaN */
  let t: number, hi: number, lo: number;
  if (ax < AT_11875) {   /* |x| < 1.1875 */
    if (ax < AT_06875) { t = (2.0 * ax - 1.0) / (2.0 + ax); hi = ATANHI0; lo = ATANLO0; }   /* 7/16 <=|x|<11/16 */
    else { t = (ax - 1.0) / (ax + 1.0); hi = ATANHI1; lo = ATANLO1; }                     /* 11/16<=|x|< 19/16 */
  } else if (ax < AT_24375) { t = (ax - 1.5) / (1.0 + 1.5 * ax); hi = ATANHI2; lo = ATANLO2; }   /* |x| < 2.4375 */
  else { t = -1.0 / ax; hi = ATANHI3; lo = ATANLO3; }                                           /* 2.4375 <= |x| < 2^66 */
  const z = t * t, w = z * z;
  const s1 = z * (aT0 + w * (aT2 + w * (aT4 + w * (aT6 + w * (aT8 + w * aT10)))));
  const s2 = w * (aT1 + w * (aT3 + w * (aT5 + w * (aT7 + w * aT9))));
  const zz = hi - ((t * (s1 + s2) - lo) - t);
  return x < 0 ? -zz : zz;   /* hx < 0 (x is not -0 here) */
}
/** atan's |x| >= 2^66 and NaN branch, kept out of the hot function. */
function atanHuge(x: number): number {
  if (x !== x) return x + x;   /* NaN */
  return x < 0 ? -ATANHI3 - ATANLO3 : ATANHI3 + ATANLO3;
}

const tiny = 1.0e-300;
const pi_o_4 = 7.8539816339744827900e-01; /* 0x3FE921FB, 0x54442D18 */
const pi_o_2 = 1.5707963267948965580e+00; /* 0x3FF921FB, 0x54442D18 */
const pi = 3.1415926535897931160e+00;     /* 0x400921FB, 0x54442D18 */
const pi_lo = 1.2246467991473531772e-16;  /* 0x3CA1A626, 0x33145C07 */

/** Math.atan2 as V8 (fdlibm atan2). */
export function atan2(y: number, x: number): number {
  if (x !== x || y !== y) return x + y;   /* x or y is NaN */
  const hx = hiWord(x), lx = loWord(x);
  const ix = hx & 0x7FFFFFFF;
  const hy = hiWord(y), ly = loWord(y);
  const iy = hy & 0x7FFFFFFF;
  if (x === 1.0) return atan(y);   /* x=1.0 */
  let m = ((hy >> 31) & 1) | ((hx >> 30) & 2);   /* 2*sign(x)+sign(y) */

  /* when y = 0 */
  if ((iy | ly) === 0) {
    switch (m) {
      case 0: case 1: return y;     /* atan(+-0,+anything)=+-0 */
      case 2: return pi + tiny;     /* atan(+0,-anything) = pi */
      default: return -pi - tiny;   /* atan(-0,-anything) =-pi */
    }
  }
  /* when x = 0 */
  if ((ix | lx) === 0) return hy < 0 ? -pi_o_2 - tiny : pi_o_2 + tiny;

  /* when x is INF */
  if (ix === 0x7FF00000) {
    if (iy === 0x7FF00000) {
      switch (m) {
        case 0: return pi_o_4 + tiny;
        case 1: return -pi_o_4 - tiny;
        case 2: return 3.0 * pi_o_4 + tiny;
        default: return -3.0 * pi_o_4 - tiny;
      }
    } else {
      switch (m) {
        case 0: return 0.0;
        case 1: return -0.0;
        case 2: return pi + tiny;
        default: return -pi - tiny;
      }
    }
  }
  /* when y is INF */
  if (iy === 0x7FF00000) return hy < 0 ? -pi_o_2 - tiny : pi_o_2 + tiny;

  /* compute y/x */
  const k = (iy - ix) >> 20;
  let z: number;
  if (k > 60) {   /* |y/x| >  2**60 */
    z = pi_o_2 + 0.5 * pi_lo;
    m &= 1;
  } else if (hx < 0 && k < -60) {
    z = 0.0;   /* 0 > |y|/x > -2**-60 */
  } else {
    z = atan(Math.abs(y / x));
  }
  switch (m) {
    case 0: return z;                     /* atan(+,+) */
    case 1: return -z;                    /* atan(-,+) */
    case 2: return pi - (z - pi_lo);      /* atan(+,-) */
    default: return (z - pi_lo) - pi;     /* atan(-,-) */
  }
}

const o_threshold = 7.09782712893383973096e+02;  /* 0x40862E42, 0xFEFA39EF */
const u_threshold = -7.45133219101941108420e+02; /* 0xC0874910, 0xD52D3051 */
const ln2HI0 = 6.93147180369123816490e-01;       /* 0x3FE62E42, 0xFEE00000 */
const ln2LO0 = 1.90821492927058770002e-10;       /* 0x3DEA39EF, 0x35793C76 */
const invln2 = 1.44269504088896338700e+00;       /* 0x3FF71547, 0x652B82FE */
const P1 = 1.66666666666666019037e-01;           /* 0x3FC55555, 0x5555553E */
const P2 = -2.77777777770155933842e-03;          /* 0xBF66C16C, 0x16BEBD93 */
const P3 = 6.61375632143793436117e-05;           /* 0x3F11566A, 0xAF25DE2C */
const P4 = -1.65339022054652515390e-06;          /* 0xBEBBBD41, 0xC5D26BF1 */
const P5 = 4.13813679705723846039e-08;           /* 0x3E663769, 0x72BEA4D0 */
const E = 2.718281828459045;                     /* 0x4005BF0A, 0x8B145769 */
const huge = 1.0e+300;
const twom1000 = 9.33263618503218878990e-302;    /* 2**-1000=0x01700000,0 */
const two1023 = 8.988465674311579539e307;        /* 0x1p1023 */

/** Math.exp as V8 (fdlibm exp with V8's exp(1) = E special case). */
export function exp(x: number): number {
  let hi = 0.0, lo = 0.0, k = 0;
  let hx = hiWord(x);
  const xsb = (hx >>> 31) & 1;   /* sign bit of x */
  hx &= 0x7FFFFFFF;              /* high word of |x| */

  /* filter out non-finite argument */
  if (hx >= 0x40862E42) {   /* if |x|>=709.78... */
    if (hx >= 0x7FF00000) {
      if (x !== x) return x + x;   /* NaN */
      return xsb === 0 ? x : 0.0;  /* exp(+-inf)={inf,0} */
    }
    if (x > o_threshold) return huge * huge;         /* overflow */
    if (x < u_threshold) return twom1000 * twom1000; /* underflow */
  }

  /* argument reduction */
  if (hx > 0x3FD62E42) {   /* if  |x| > 0.5 ln2 */
    if (hx < 0x3FF0A2B2) {   /* and |x| < 1.5 ln2 */
      if (x === 1.0) return E;
      if (xsb === 0) { hi = x - ln2HI0; lo = ln2LO0; } else { hi = x + ln2HI0; lo = -ln2LO0; }
      k = 1 - xsb - xsb;
    } else {
      k = (invln2 * x + (xsb === 0 ? 0.5 : -0.5)) | 0;
      const t = k;
      hi = x - t * ln2HI0;   /* t*ln2HI is exact here */
      lo = t * ln2LO0;
    }
    x = hi - lo;
  } else if (hx < 0x3E300000) {   /* when |x|<2**-28 */
    return 1.0 + x;               /* huge + x > one is always true */
  } else {
    k = 0;
  }

  /* x is now in primary range */
  const t = x * x;
  const twopk = k >= -1021 ? fromWords(0x3FF00000 + (k << 20), 0) : fromWords(0x3FF00000 + ((k + 1000) << 20), 0);
  const c = x - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))));
  if (k === 0) return 1.0 - ((x * c) / (c - 2.0) - x);
  const y = 1.0 - ((lo - (x * c) / (2.0 - c)) - hi);
  if (k >= -1021) {
    if (k === 1024) return y * 2.0 * two1023;
    return y * twopk;
  }
  return y * twopk * twom1000;
}

const ln2_hi = 6.93147180369123816490e-01; /* 3fe62e42 fee00000 */
const ln2_lo = 1.90821492927058770002e-10; /* 3dea39ef 35793c76 */
const two54 = 1.80143985094819840000e+16;  /* 43500000 00000000 */
const Lg1 = 6.666666666666735130e-01;      /* 3FE55555 55555593 */
const Lg2 = 3.999999999940941908e-01;      /* 3FD99999 9997FA04 */
const Lg3 = 2.857142874366239149e-01;      /* 3FD24924 94229359 */
const Lg4 = 2.222219843214978396e-01;      /* 3FCC71C5 1D8E78AF */
const Lg5 = 1.818357216161805012e-01;      /* 3FC74664 96CB03DE */
const Lg6 = 1.531383769920937332e-01;      /* 3FC39A09 D078C69F */
const Lg7 = 1.479819860511658591e-01;      /* 3FC2F112 DF3E5244 */

/** Math.log as V8 (fdlibm __ieee754_log). */
export function log(x: number): number {
  let hx = hiWord(x);
  const lx = loWord(x);
  let k = 0;
  if (hx < 0x00100000) {   /* x < 2**-1022  */
    if (((hx & 0x7FFFFFFF) | lx) === 0) return -Infinity;   /* log(+-0)=-inf */
    if (hx < 0) return NaN;                                  /* log(-#) = NaN */
    k -= 54;
    x *= two54;   /* subnormal number, scale up x */
    hx = hiWord(x);
  }
  if (hx >= 0x7FF00000) return x + x;
  k += (hx >> 20) - 1023;
  hx &= 0x000FFFFF;
  let i = (hx + 0x95F64) & 0x100000;
  x = fromWords(hx | (i ^ 0x3FF00000), loWord(x));   /* normalize x or x/2 */
  k += i >> 20;
  const f = x - 1.0;
  let dk: number;
  if ((0x000FFFFF & (2 + hx)) < 3) {   /* -2**-20 <= f < 2**-20 */
    if (f === 0) {
      if (k === 0) return 0;
      dk = k;
      return dk * ln2_hi + dk * ln2_lo;
    }
    const R = f * f * (0.5 - 0.33333333333333333 * f);
    if (k === 0) return f - R;
    dk = k;
    return dk * ln2_hi - ((R - dk * ln2_lo) - f);
  }
  const s = f / (2.0 + f);
  dk = k;
  const z = s * s;
  i = hx - 0x6147A;
  const w = z * z;
  const j = 0x6B851 - hx;
  const t1 = w * (Lg2 + w * (Lg4 + w * Lg6));
  const t2 = z * (Lg1 + w * (Lg3 + w * (Lg5 + w * Lg7)));
  i |= j;
  const R = t2 + t1;
  if (i > 0) {
    const hfsq = 0.5 * f * f;
    if (k === 0) return f - (hfsq - s * (hfsq + R));
    return dk * ln2_hi - ((hfsq - (s * (hfsq + R) + dk * ln2_lo)) - f);
  }
  if (k === 0) return f - s * (f - R);
  return dk * ln2_hi - ((s * (f - R) - dk * ln2_lo) - f);
}

const CB_P0 = 1.87595182427177009643;   /* 0x3FFE03E6, 0x0F61E692 */
const CB_P1 = -1.88497979543377169875;  /* 0xBFFE28E0, 0x92F02420 */
const CB_P2 = 1.621429720105354466140;  /* 0x3FF9F160, 0x4A49D6C2 */
const CB_P3 = -0.758397934778766047437; /* 0xBFE844CB, 0xBEE751D9 */
const CB_P4 = 0.145996192886612446982;  /* 0x3FC2B000, 0xD4E4EDD7 */

/** Math.cbrt as V8 (fdlibm / FreeBSD cbrt in V8's ieee754.cc). */
export function cbrt(x: number): number {
  let hx = hiWord(x);
  const low = loWord(x);
  const sign = hx & 0x80000000;
  hx = (hx ^ sign) >>> 0;
  if (hx >= 0x7FF00000) return x + x;   /* cbrt(NaN,INF) is itself */
  let t: number;
  if (hx < 0x00100000) {   /* zero or subnormal? */
    if ((hx | low) === 0) return x;   /* cbrt(0) is itself */
    t = 18014398509481984 * x;          /* t = 2**54 * x */
    const high = hiWord(t) >>> 0;
    t = fromWords((sign | (Math.trunc((high & 0x7FFFFFFF) / 3) + 696219795)) >>> 0, 0);   /* B2 */
  } else {
    t = fromWords((sign | (Math.trunc(hx / 3) + 715094163)) >>> 0, 0);                    /* B1 */
  }
  let r = (t * t) * (t / x);
  t = t * ((CB_P0 + r * (CB_P1 + r * CB_P2)) + ((r * r) * r) * (CB_P3 + r * CB_P4));
  /* round t away from zero to 23 bits: bits = (bits + 0x80000000) & 0xFFFFFFFFC0000000 */
  let lo = loWord(t) + 0x80000000, hi = hiWord(t) >>> 0;
  if (lo > 0xFFFFFFFF) { lo -= 4294967296; hi = (hi + 1) >>> 0; }
  t = fromWords(hi, (lo & 0xC0000000) >>> 0);
  /* one step Newton iteration to 53 bits with error < 0.667 ulps */
  const s = t * t;
  r = x / s;
  const w = t + t;
  r = (r - t) / (w + r);
  return t + t * r;
}

/** Math.hypot(a, b) as V8 (Torque FastMathHypot, two arguments). */
export function hypot(x: number, y: number): number {
  const a = Math.abs(x), b = Math.abs(y);
  if (a === Infinity || b === Infinity) return Infinity;
  // Float64Max: NaN if either is NaN
  if (a !== a || b !== b) return NaN;
  const max = a > b ? a : b;
  if (max === 0) return 0;
  return Math.sqrt((a / max) * (a / max) + (b / max) * (b / max)) * max;
}

/** Math.hypot(a, b, c) as V8 (Torque FastMathHypot, three arguments, with its compensation term). */
export function hypot3(x: number, y: number, z: number): number {
  const a = Math.abs(x), b = Math.abs(y), c = Math.abs(z);
  if (a === Infinity || b === Infinity || c === Infinity) return Infinity;
  if (a !== a || b !== b || c !== c) return NaN;
  const ab = a > b ? a : b;
  const max = ab > c ? ab : c;
  if (max === 0) return 0;
  const powerA = (a / max) * (a / max);
  const powerB = (b / max) * (b / max);
  const compensation = (powerA + powerB) - powerA - powerB;
  const powerC = (c / max) * (c / max) - compensation;
  return Math.sqrt(powerA + powerB + powerC) * max;
}

// ---------------------------------------------------------------- pow (the server's: glibc's, as V8 calls it)
//
// V8 hands Math.pow to the platform C library (math::pow: NaN / |x| = 1 with infinite y / y = 2 / y = 0.5 handled
// first, then std::pow). The scoreboard server is Vercel's linux-x64 Node 24 with glibc 2.34 on an Intel Xeon, where
// std::pow is glibc's __ieee754_pow_fma: sysdeps/ieee754/dbl-64/e_pow.c (Szabolcs Nagy's 2018 pow from ARM's
// optimized-routines, MIT OR Apache-2.0 WITH LLVM-exception there) compiled with -mfma -mavx2 and GCC's default
// contraction, so besides its explicit __builtin_fma calls every a * b + c whose product feeds only additions is fused.
// This port evaluates exactly that: each fused operation is an exactly emulated fma (below). Proven against the
// server's own Math.pow on 600 006 arguments (tools/determinism/pow_server.json.gz, docs/determinism.md section 5).

/** fma(a, b, c) = RN(a·b + c): Dekker's exact product, then Boldo & Melquiond's emulation (RN(th + RO(tl + pl))). Exact for
 *  operands whose product neither overflows nor underflows, which holds on every path of pow below. */
function fma(a: number, b: number, c: number): number {
  const p = a * b;
  let t = 134217729 * a; const ah = t - (t - a), al = a - ah;
  t = 134217729 * b; const bh = t - (t - b), bl = b - bh;
  const pl = ((ah * bh - p) + ah * bl + al * bh) + al * bl;
  const th = c + p, z = th - c, tl = (c - (th - z)) + (p - z);
  let v = tl + pl;
  const w = v - tl, e = (tl - (v - w)) + (pl - w);
  return finishFma(th, v, e);
}
/** The exact rounding error of a·b (fma(a, b, -RN(a·b))), Dekker. */
function prodErr(a: number, b: number, p: number): number {
  let t = 134217729 * a; const ah = t - (t - a), al = a - ah;
  t = 134217729 * b; const bh = t - (t - b), bl = b - bh;
  return ((ah * bh - p) + ah * bl + al * bh) + al * bl;
}

/** Veltkamp halves of a constant, for fmaK. */
function hiHalf(b: number): number { const t = 134217729 * b; return t - (t - b); }
/** fma(a, b, c) with b a constant pre-split into bh + bl (same result as fma, one split fewer). */
function fmaK(a: number, b: number, bh: number, bl: number, c: number): number {
  const p = a * b;
  const t = 134217729 * a, ah = t - (t - a), al = a - ah;
  const pl = ((ah * bh - p) + ah * bl + al * bh) + al * bl;
  const th = c + p, z = th - c, tl = (c - (th - z)) + (p - z);
  let v = tl + pl;
  const w = v - tl, e = (tl - (v - w)) + (pl - w);
  return finishFma(th, v, e);
}
/**
 * RN(th + v + e) from th, v = RN(tl + pl) and its exact error e (the last step of the fma emulation). RN(th + v) is already
 * right unless th + v is exactly halfway between two doubles while e != 0 (the double-rounding case): then the exact sum
 * lies off the midpoint on e's side. (With |tl| <= ulp(th)/2 and |pl| <= ulp(a·b)/2, e != 0 only when |v| <= 2^-50 |th|, so
 * no other boundary is within reach of e; with strong cancellation th is exact and e = 0.) Checked against an exact
 * BigInt fma on 10^7 operand triples (tools/determinism, docs section 5).
 */
function finishFma(th: number, v: number, e: number): number {
  const res = th + v;
  if (e === 0) return res;
  const bb = res - th, err = (th - (res - bb)) + (v - bb);   // th + v = res + err exactly
  // a tie: err is exactly half an ulp of res, i.e. res + 2·err is the next double and the step is exact
  if (err !== 0 && (res + 2 * err) - res === 2 * err) return (e > 0) === (err > 0) ? res + 2 * err : res;
  return res;
}
const PA0 = POW_A[0], PA1 = POW_A[1], PA2 = POW_A[2], PA3 = POW_A[3], PA4 = POW_A[4], PA5 = POW_A[5], PA6 = POW_A[6];
const EC2 = EXP_C[0], EC3 = EXP_C[1], EC4 = EXP_C[2], EC5 = EXP_C[3];
const PA2H = hiHalf(PA2), PA2L = PA2 - PA2H, PA4H = hiHalf(PA4), PA4L = PA4 - PA4H, PA6H = hiHalf(PA6), PA6L = PA6 - PA6H;
const EC3H = hiHalf(EC3), EC3L = EC3 - EC3H, EC5H = hiHalf(EC5), EC5L = EC5 - EC5H;
const LN2LOH = hiHalf(POW_LN2LO), LN2LOL = POW_LN2LO - LN2LOH, NLLH = hiHalf(EXP_NEGLN2LON), NLLL = EXP_NEGLN2LON - NLLH;
const ILNH = hiHalf(EXP_INVLN2N), ILNL = EXP_INVLN2N - ILNH;
const SIGN_BIAS = 0x800 << 7;
const LOG_TAIL = new Float64Array(1);   // a typed slot: a module-level `let` double would be re-boxed on every store

/** log_inline(ix): the words of x (normalised in the subnormal range); returns hi, the tail in LOG_TAIL. */
function powLog(hi32: number, lo32: number): number {
  const tmpHi = (hi32 - 0x3FE69555) >>> 0;           // tmp = ix - OFF (OFF's low word is 0)
  const i = (tmpHi >>> 13) & 127;                    // (tmp >> (52 - 7)) % N
  const k = (tmpHi | 0) >> 20;                       // (int64_t) tmp >> 52
  const z = fromWords((hi32 - (tmpHi & 0xFFF00000)) >>> 0, lo32);
  const kd = k;
  const invc = POW_TAB[3 * i], logc = POW_TAB[3 * i + 1], logctail = POW_TAB[3 * i + 2];
  const pz = z * invc;
  const r = (pz - 1.0) + prodErr(z, invc, pz);       // __builtin_fma (z, invc, -1.0): exactly representable
  const t1 = kd * POW_LN2HI + logc;                 // fused in glibc; exact either way (checked for every entry and k)
  const t2 = t1 + r;
  const lo1 = (k < 16 && k > -16) ? kd * POW_LN2LO + logctail : fmaK(kd, POW_LN2LO, LN2LOH, LN2LOL, logctail);   // |k| < 16: the product is exact
  const lo2 = t1 - t2 + r;
  const ar = PA0 * r;
  const ar2 = r * ar;
  const ar3 = r * ar2;
  const hi = t2 + ar2;
  const lo3 = prodErr(ar, r, ar2);                   // __builtin_fma (ar, r, -ar2)
  const lo4 = t2 - hi + ar2;
  const p = fma(ar2, fma(ar2, fmaK(r, PA6, PA6H, PA6L, PA5), fmaK(r, PA4, PA4H, PA4L, PA3)), fmaK(r, PA2, PA2H, PA2L, PA1));
  const lo = fma(ar3, p, lo1 + lo2 + lo3 + lo4);
  const y = hi + lo;
  LOG_TAIL[0] = hi - y + lo;
  return y;
}

/** specialcase(tmp, sbits, ki) of exp_inline. */
function powExpSpecial(tmp: number, sbHi: number, sbLo: number, kNeg: boolean): number {
  if (!kNeg) {   /* k > 0, the exponent of scale might have overflowed by <= 460. */
    const scale = fromWords((sbHi - (1009 << 20)) >>> 0, sbLo);
    return 5.486124068793689e303 * fma(scale, tmp, scale);   // 0x1p1009
  }
  /* k < 0, need special care in the subnormal range. */
  const adjHi = (sbHi + (1022 << 20)) >>> 0;
  const scale = fromWords(adjHi, sbLo);
  let y = fma(scale, tmp, scale);
  if (Math.abs(y) < 1.0) {
    const one = y < 0.0 ? -1.0 : 1.0;
    let lo = fma(scale, tmp, scale - y);
    const hi = one + y;
    lo = one - hi + y + lo;
    y = (hi + lo) - one;
    if (y === 0.0) y = (adjHi & 0x80000000) !== 0 ? -0.0 : 0.0;   /* fix the sign of 0 */
  }
  return 2.2250738585072014e-308 * y;   // 0x1p-1022
}

/** exp_inline(x, xtail, sign_bias). */
function powExp(x: number, xtail: number, signBias: number): number {
  let abstop = (hiWord(x) >>> 20) & 0x7FF;
  if (((abstop - 0x3C9) >>> 0) >= 0x408 - 0x3C9) {   /* top12(0x1p-54), top12(512.0) */
    if (((abstop - 0x3C9) >>> 0) >= 0x80000000) { const one = 1.0 + x; return signBias ? -one : one; }
    if (abstop >= 0x409) {   /* top12(1024.0) */
      if (x < 0) return signBias ? -0.0 : 0.0;          /* __math_uflow (sign_bias) */
      return signBias ? -Infinity : Infinity;            /* __math_oflow (sign_bias) */
    }
    abstop = 0;   /* large x is special cased below */
  }
  // kd = RN(InvLn2N * x + Shift) - Shift (one fused operation in glibc) is the integer nearest to the exact product, ties
  // to even: from the rounded product, its exact error and the exact remainder against the nearest integer
  const zr = x * EXP_INVLN2N;
  const ta = 134217729 * x, xh = ta - (ta - x), xl = x - xh;
  const ez = ((xh * ILNH - zr) + xh * ILNL + xl * ILNH) + xl * ILNL;
  let k = (zr + EXP_SHIFT) - EXP_SHIFT;
  const d0 = zr - k, rem = d0 + ez, remErr = (d0 - (rem - (rem - d0))) + (ez - (rem - d0));
  if (rem > 0.5 || (rem === 0.5 && (remErr > 0 || (remErr === 0 && (k & 1) !== 0)))) k += 1;
  else if (rem < -0.5 || (rem === -0.5 && (remErr < 0 || (remErr === 0 && (k & 1) !== 0)))) k -= 1;
  const kd = k;
  const kiLo = k | 0;                                  // the low word of asuint64 (Shift + k)
  const r0 = (k < 131072 && k > -131072) ? kd * EXP_NEGLN2HIN + x : fma(kd, EXP_NEGLN2HIN, x);   // the product is exact for |k| < 2^17
  let r = k === 0 ? r0 : fmaK(kd, EXP_NEGLN2LON, NLLH, NLLL, r0);
  r += xtail;
  const idx = 2 * (kiLo & 127);
  const topHi = ((k + signBias) << 13) >>> 0;          // (ki + sign_bias) << (52 - 7): only the low 19 bits of k survive
  const tail = fromWords(EXP_TAB_U32[2 * idx], EXP_TAB_U32[2 * idx + 1]);
  const sbHi = (EXP_TAB_U32[2 * idx + 2] + topHi) >>> 0, sbLo = EXP_TAB_U32[2 * idx + 3];
  const r2 = r * r;
  const tmp = fma(r2 * r2, fmaK(r, EC5, EC5H, EC5L, EC4), fma(r2, fmaK(r, EC3, EC3H, EC3L, EC2), tail + r));
  if (abstop === 0) return powExpSpecial(tmp, sbHi, sbLo, (kiLo & 0x80000000) !== 0);
  const scale = fromWords(sbHi, sbLo);
  return fma(scale, tmp, scale);
}

/** checkint: 0 not an integer, 1 odd, 2 even (finite non-zero y). */
function checkint(y: number): number {
  if (!Number.isInteger(y)) return 0;
  const a = Math.abs(y);
  if (a >= 9007199254740992) return 2;
  return a % 2 === 1 ? 1 : 2;
}

/** Math.pow as the server computes it: V8's math::pow special cases, then glibc 2.34's __pow (FMA build). */
export function pow(x: number, y: number): number {
  // V8 math::pow (src/numbers/ieee754.cc, use_std_math_pow)
  if (y !== y) return NaN;
  if ((y === Infinity || y === -Infinity) && (x === 1 || x === -1)) return NaN;
  if (y === 2) return x * x;
  if (y === 0.5) return x === -Infinity ? Infinity : Math.sqrt(x + 0);
  // glibc __pow
  let signBias = 0;
  let hx = hiWord(x) >>> 0, lx = loWord(x);
  const hy = hiWord(y) >>> 0;
  let topx = hx >>> 20;
  const topy = hy >>> 20;
  if (((topx - 0x001) >>> 0) >= 0x7FF - 0x001 || (((topy & 0x7FF) - 0x3BE) >>> 0) >= 0x43E - 0x3BE) {
    if (y === 0 || !Number.isFinite(y)) {   /* zeroinfnan (iy) */
      if (y === 0) return 1.0;
      if (x === 1) return 1.0;
      if (x !== x) return x + y;
      if (x === 1 || x === -1) return 1.0;
      if ((Math.abs(x) < 1) === !(hy >>> 31)) return 0.0;   /* |x|<1 && y==inf or |x|>1 && y==-inf */
      return y * y;
    }
    if (x === 0 || !Number.isFinite(x)) {   /* zeroinfnan (ix) */
      let x2 = x * x;
      if ((hx >>> 31) !== 0 && checkint(y) === 1) x2 = -x2;
      return (hy >>> 31) !== 0 ? 1 / x2 : x2;
    }
    /* here x and y are non-zero finite */
    if ((hx >>> 31) !== 0) {
      const yint = checkint(y);
      if (yint === 0) return NaN;   /* __math_invalid */
      if (yint === 1) signBias = SIGN_BIAS;
      hx &= 0x7FFFFFFF;
      topx &= 0x7FF;
    }
    if ((((topy & 0x7FF) - 0x3BE) >>> 0) >= 0x43E - 0x3BE) {
      const ax = Math.abs(x);
      if (ax === 1) return 1.0;
      if ((topy & 0x7FF) < 0x3BE) return ax > 1 ? 1.0 + y : 1.0 - y;   /* |y| < 2^-65, x^y ~= 1 + y*log(x) */
      return (ax > 1) === (topy < 0x800) ? Infinity : 0.0;           /* __math_oflow (0) : __math_uflow (0) */
    }
    if (topx === 0) {   /* normalise subnormal x so the exponent becomes negative */
      const xs = Math.abs(x) * 4503599627370496;   // 0x1p52
      hx = ((hiWord(xs) & 0x7FFFFFFF) - (52 << 20)) >>> 0;
      lx = loWord(xs);
    }
  }
  const hi = powLog(hx, lx);
  const lo = LOG_TAIL[0];
  const ehi = y * hi;
  const elo = fma(y, lo, prodErr(y, hi, ehi));        // y * lo + __builtin_fma (y, hi, -ehi)
  return powExp(ehi, elo, signBias);
}
