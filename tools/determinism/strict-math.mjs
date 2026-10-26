// Proof harness only (docs/determinism.md section 4). Build its dmath.mjs first (not committed):
//   npx esbuild src/physics/dmath.ts --bundle --format=esm --outfile=tools/determinism/dmath.mjs
// then NODE_OPTIONS="--import=$PWD/tools/determinism/strict-math.mjs" npx tsx ...
// It makes this Node's Math.* the strict V8 maths (the port, proven
// bit-identical to Chromium's V8 without FP contraction), so a run here computes what linux-x64 Node computes for
// sin/cos/tan/atan/atan2/exp/log/hypot and pow (the server's glibc pow, since round 2).
import * as D from './dmath.mjs';
const nh = Math.hypot;
Object.assign(Math, { pow: D.pow, cbrt: D.cbrt, sin: D.sin, cos: D.cos, tan: D.tan, atan: D.atan, atan2: D.atan2, exp: D.exp, log: D.log,
  hypot: (...a) => a.length === 2 ? D.hypot(a[0], a[1]) : a.length === 3 ? D.hypot3(a[0], a[1], a[2]) : nh(...a) });
