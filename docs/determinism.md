# Physics determinism across engines (0.4.0 round, 26 Oct 2026)

Goal: a hot-lap trace recorded in any browser engine (Chrome / V8, Safari and every iPhone browser / JavaScriptCore,
Firefox / SpiderMonkey) replays on the scoreboard server (Vercel, Node 24, V8) to the same bits, without changing
the server's results (the 0.3.0 boards and their keys stay valid). Code: `src/physics/dmath.ts`; proofs:
`src/physics/__tests__/dmath.test.ts`, `tools/determinism/`.

**Status: done for every transcendental function the physics uses except `Math.pow`, which is open (section 5).**

## 1. Inventory: what on the replay path can differ between engines

The replay path is `replayTrace()` (`src/scoreboard/replay.ts`) → `HotlapSim` (`src/scoreboard/sim.ts`: reset, input
decoding, `advance()`) → `Vehicle.step` (`src/physics/vehicle.ts`: steering, suspension, tyres, engine, drivetrain,
brakes, aero, collisions) → the surface (`src/physics/track.ts`: station search, heightfield interpolation, kerb and
sausage profiles, dirt roughness, terrain override) → the collision world (`collision.ts`) → the off-track judge
(`offtrack.ts`) → the lap timer (`src/app/timing.ts`), plus the gear schedule (`gearschedule.ts`) and the rolling
start (`canonicalReset` → `lineToWorld`).

### 1.1 Transcendental calls (now `dmath`)

| file:line (after the change) | where | function | per physics step |
|---|---|---|---|
| vehicle.ts:273 | constructor (tan of the lateral peak slip angle) | tan | once |
| vehicle.ts:374-377, 390 | `reset` (heading quaternion, ground-plane frame) | sin, cos, hypot (3 args) | at reset |
| vehicle.ts:551-554 | `step`, Ackermann steering split | tan, atan (2) | 1 + 2 when steering |
| vehicle.ts:655 | `step`, wheel heading in the ground plane | sin, cos | 4 + 4 |
| vehicle.ts:769 | `step`, NaN recovery yaw | atan2 | only after a NaN |
| vehicle.ts:853, 1006 | `collide` (footprint box, push-out) | hypot | ~1 |
| vehicle.ts:1075 | `stepLaunched` (launched car spin decay) | exp | only while launched |
| vehicle.ts:1103, 1135 | `tyre` (off-pavement peak, slip angle) | tan, atan | 4 atan; tan off pavement |
| vehicle.ts:1165 | `tyre` (low-speed blend) | cos | below vBlend only |
| vehicle.ts:1443-1444 | `saveGood` (last good pose) | atan2, sin, cos | 1 + 1 + 1 |
| tyre.ts:7 | `mfShape` (Pacejka magic formula), 2 per wheel | sin, atan (2) | 8 sin + 16 atan |
| tyre.ts:16-17 | `solveMfB` (constructor) | tan, atan | at construction |
| track.ts:59, 67 | sausage kerb strips (build) | hypot | at build |
| track.ts:109-110 | `sausageAt` raised-cosine profile | cos, sin | on a sausage kerb |
| track.ts:285-287 | dirt roughness wave vectors (module constants) | cos, sin | at load |
| track.ts:339-346 | `buildGeo` (segment lengths, half widths) | hypot | at build |
| track.ts:689-690 | surface `sample`, dirt roughness (phases up to ~3000 rad) | sin, cos | 3 + 3 per off-road sample |
| track.ts:770 | `createEdgeDistance` | hypot | per call |
| track.ts:807 | `lineToWorld` heading (rolling start) | atan2 | at reset |
| collision.ts:62-274 | collision world build (normals, corner test `cos 25°`) | hypot, cos | at build |
| rollover.ts:13 | `rollOf` (rollover game over, kerb gate) | atan2 | app, not replayed |
| gearschedule.ts:40, 43 | `deriveGearSchedule` (log ratio match) | log | when the reference changes |
| cars.ts:72, 193 | car-vs-car contacts (race only) | hypot | race only |
| **vehicle.ts:1145** | **`tyre`, load sensitivity `(Fz/Fz0)^-0.1`** | **pow (native, open)** | **4** |
| vehicle.ts:1228 | brake pedal map `brk^pedalExponent` | pow (native) | never: pedalExponent is 1 |

Measured on two autopilot replays (Laguna Seca 139.351 s, Sonoma 154.872 s; 324 865 steps,
`tools/determinism/record_args.mts`): atan 7 140 667 calls, sin 4 220 476, cos 1 635 966, hypot 397 372,
atan2 324 871, tan 324 231, log 10 680, exp 0 and hypot (3 args) 0 (launch / reset only). About 42 transcendental
calls per step, plus 4 `Math.pow`.

Not on the replay path and left on `Math.*`: `HotlapSim.lineSteer` (the live auto-launch; its output is quantised and
recorded as trace rows, so a replay never calls it), `src/physics/devtrack.ts` (the synthetic dev oval), the AI
(`src/physics/ai/`, races are not replayed), rendering and UI.

### 1.2 Everything else that could differ

| item | finding |
|---|---|
| `+ - * / %`, `Math.sqrt / floor / ceil / trunc / round / abs / min / max / sign`, `Float64Array`, `Float32Array` | exact IEEE / exactly specified: identical in every engine |
| `x ** 2` (vehicle.ts preload, track.ts station walk) | the exponent operator is `Math.pow`. V8 special-cases y = 2 as `x * x` (`math::pow`), JavaScriptCore and SpiderMonkey use repeated multiplication for small integer exponents, so all give `x * x` today; replaced by explicit `v * v` (same bits in V8) so nothing depends on an engine's pow. A test forbids `**` on the path |
| `Math.random`, `Date.now`, `performance.now` | not in the physics, the sim or the timer; `replayTrace` uses `Date.now` only for its CPU-time report. The race RNG is seeded (`ai/rng.ts`) and not on the hot-lap path |
| `Array.prototype.sort` | not on the replay path (`gearschedule.ts shiftRpmSummary` is a report, numeric comparator) |
| object key order | `JSON.parse` keeps insertion order in every engine; `physicsVersion` hashes key-sorted JSON (`canonicalJson`) |
| number parsing | track.json / scenery.json / ghosts.json / car.json numbers have at most 17 significant digits (checked), which every engine must round correctly (ECMA-262 StringToNumber, under 20 digits) |
| typed-array endianness | `loadHeightfield` and `dmath` read words through typed arrays; every target (x86-64, arm64) is little-endian, and `dmath` detects the order anyway |
| the trace | integers (steps, steer / throttle / brake in thousandths, flags); `reset` doubles travel through JSON (shortest round trip, exact) and are checked against the server's own reset to 1e-6, then the server's is used |
| input decoding | `row / 1000`, exact |
| lap timing | `src/app/timing.ts`: arithmetic and `Math.round / floor / ceil / min`, exact |
| the compare (`verifyHotlap`) | a tolerance: `|replayed − claimed| ≤ LIMITS.replayTolerance` = 0.05 s; the replayed time is what is stored. Unchanged (section 6) |

## 2. The port (`src/physics/dmath.ts`)

A line-for-line port of V8 14.6's `src/base/ieee754.cc` (fdlibm 5.3 as modified by Google; V8 tag 14.6.202.34, the V8
of Node 26.12) and of V8's Torque builtin `FastMathHypot` (`src/builtins/math.tq`):

| function | V8 source ported |
|---|---|
| sin, cos | `fdlibm_sin` / `fdlibm_cos` (`sin` / `cos` when built without `V8_USE_LIBM_TRIG_FUNCTIONS`), `__kernel_sin`, `__kernel_cos`, `__ieee754_rem_pio2` (medium path and `__kernel_rem_pio2`, prec 2, for large arguments) |
| tan | `tan`, `__kernel_tan` (with the careful -1/tan path), `__ieee754_rem_pio2` |
| atan, atan2 | `atan`, `atan2` |
| exp | `exp` (with V8's `exp(1) = E` special case) |
| log | `log` (`__ieee754_log`) |
| hypot (2 and 3 arguments) | `FastMathHypot`: `sqrt((a/m)² + (b/m)²)·m`, the 3-argument form with its compensation term |

Only exact operations inside (+ − × ÷, `Math.sqrt / abs / floor / trunc`; a test checks); word access through one shared
`Float64Array` / `Uint32Array`; C's `(int32_t)` casts as `| 0`, arithmetic `>>` as `>>`. No tables apart from fdlibm's
own (2/π digits, π/2 pieces, polynomial coefficients); no allocation per call.

The same routines are in Node 22 / 24 / 26's V8 (`deps/v8/src/base/ieee754.cc`, diffed: comment changes only) and
`FastMathHypot` is in 24 and 26 (Node 22's general Kahan loop gives the same bits for 2 and 3 arguments). Node's gyp
build never defines `V8_USE_LIBM_TRIG_FUNCTIONS` (checked in v22, v24, v26), so Node's `Math.sin / cos` are fdlibm's.
**Chrome's are not**: Chromium builds V8 with `v8_use_libm_trig_functions = is_clang`, a port of glibc's sin / cos, so
today Chrome and the server already differ in sin / cos (33 000 in 10^6 arguments); after this round Chrome computes the
server's values.

### 2.1 Which V8 is "V8"

V8's fdlibm is C++, and its results depend on whether the compiler fused `a * b + c` into fused multiply-adds:

| V8 build | FP contraction | its Math.atan / exp / log / sin / cos / tan |
|---|---|---|
| Vercel: Node 24.x (`vercel project inspect`), official linux-x64 binary, GCC, baseline x86-64 | none possible (no FMA instructions) | the plain IEEE evaluation of fdlibm |
| Chrome 149 (Chromium build, clang; no contraction, as the 0 mismatches show) with `--js-flags=--no-use-libm-trig-functions` | off | the plain IEEE evaluation: **0 mismatches** with the port on every set below |
| Homebrew Node 26.12.1 / 22.23.4 on this Mac (arm64, Apple clang, default `-ffp-contract=on`) | on | differs from the plain evaluation in 0.1-1 % of arguments (e.g. 1 103 of 10^6 atan, 5 688 of 10^6 sin) |

So the reference for "bit-identical to V8" is the plain evaluation, which is what the server computes; this machine's
Node is not a valid oracle. The proofs use Chromium's V8 with the fdlibm trig flag (`tools/determinism/oracle.mts`).
On a strict Node (any linux-x64 build, e.g. CI) `dmath.test.ts` also compares element by element with `Math.*`.
**Assumption to confirm on the first preview:** the Vercel function runs on x86-64. On an arm64 (Graviton) host, the
official linux-arm64 Node is GCC-built with contraction and would itself differ from the plain evaluation.
