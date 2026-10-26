# Physics determinism across engines (0.4.0 round, 26 Oct 2026)

Goal: a hot-lap trace recorded in any browser engine (Chrome / V8, Safari and every iPhone browser / JavaScriptCore,
Firefox / SpiderMonkey) replays on the scoreboard server (Vercel, Node 24, V8) to the same bits, without changing
the server's results (the 0.3.0 boards and their keys stay valid). Code: `src/physics/dmath.ts`; proofs:
`src/physics/__tests__/dmath.test.ts`, `tools/determinism/`.

**Status: done for every transcendental function the physics uses except `Math.pow`, which is open (section 5): six-lap
WebKit and Chrome traces replay on Node to the bit, the server's results are unchanged, the browsers' step cost is
within 10 % (Node on this Mac +18.6 %). One AI test fails on this Mac (section 4.1).**

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

## 3. Proof: the port is bit-identical to V8

`tools/determinism/oracle.mts` (Chromium 149 headless with `--js-flags=--no-use-libm-trig-functions`, Playwright
1.61.1 from `~/dev/frame-it`) evaluates the oracle's `Math.*` and the port side by side in the page, element by element.
`src/physics/__tests__/dmath.test.ts` re-checks the port on any host against the oracle's digests, edge bits and a
sample of the replay arguments (`fixtures/dmath_oracle.json`), and element by element against `Math.*` on a strict Node.
A one-ulp change to one atan coefficient fails 5 of its tests (checked).

| set | arguments | mismatches |
|---|---|---|
| (a) random, the physics' ranges | sin, cos, tan on ±4π (10^6 each); sin, cos on ±10^4 (10^6 each); atan on ±10 (10^6); exp on ±50 (10^6); log on (0, 10^6] (10^6); atan2 and hypot pairs on ±100, hypot triples on ±100 (10^6 each) | **0** |
| (a) random, wide | log-uniform over the whole double range for every function (2·10^5 each), exp on [-750, 712], exp of tiny arguments, log near 1 | **0** |
| (c) edge cases | 3 158: ±0, denormals, ±min normal, ±max, ±∞, NaN, ±1, the kernels' branch thresholds (0.4375, 0.6875, 1.1875, 2.4375, 2^66, 2^-27, 2^-28, 0.3, 0.78125, 0.6744), multiples of π/2 and 1e22 / 2^1023 (large-argument reduction), the exp overflow / underflow thresholds, each with its neighbours; atan2 / hypot over all pairs of 16 specials, hypot over 1 536 triples | **0** |
| (b) recorded replay arguments | every call in 2 autopilot laps and 4 six-lap browser traces (Laguna Seca, Sonoma): atan 70.5 M calls (38.8 M distinct), sin 41.7 M (23.0 M), cos 16.1 M (8.8 M), hypot 3.4 M (1.8 M), atan2 3.2 M (1.8 M), tan 3.2 M (1.8 M), log 32 040 (8 681) | **0** |

For comparison, the same sets against other engines' `Math.*` (mismatches per 10^6 on the physics' ranges):

| engine | sin | cos | tan | atan | exp | log | atan2 | hypot | hypot (3) |
|---|---|---|---|---|---|---|---|---|---|
| WebKit 26.5 (JavaScriptCore, Apple libm) | 46 915 | 46 729 | 415 247 | 58 015 | 97 719 | 9 298 | 180 624 | 376 926 | 364 334 |
| Chrome 149 as shipped (glibc-port sin / cos) | 33 385 | 33 224 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Homebrew Node 26 on this Mac (FMA-contracted fdlibm) | 5 688 | 5 105 | 10 612 | 1 103 | 470 | 419 | 1 667 | 0 | 0 |
| the port (every engine) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

No function needed to be given up: every function the physics calls except `Math.pow` (section 5) is bit-identical.

## 4. Proof: the server's results are unchanged

The server is a strict V8 (section 2.1), so "unchanged" means: release-040 run with the strict maths gives the same
bits as this branch. On this Mac that is checked by running release-040 (a `git archive` copy) and this branch with
`tools/determinism/strict-math.mjs`, which makes `Math.sin / cos / tan / atan / atan2 / exp / log / hypot` the port (=
the strict V8) for the whole process; `Math.pow` is the host's in both.

| check | release-040, strict maths | this branch | identical |
|---|---|---|---|
| replay of a 2-lap Laguna autopilot trace (`replay_compare.mts`) | 139.3511 / 139.3541 s, state `edbab2b4…` | the same, natively and with the harness | yes, every bit |
| replay of a 2-lap Sonoma autopilot trace | 154.8720 / 154.5286 s, state `d1adb5d7…` | the same | yes |
| self-play Laguna, 4 laps, seed 1 (`--json`) | 45 cars, 162.6 car-laps, race 599 s, order 83 0 40 58 105 … | the same | yes: every metric and the order; only the measured µs per step differ |
| self-play Sonoma, 2 laps, seed 1 | 134 cars, 194.6 car-laps, race 299 s | the same | yes |
| `tools/calibrate/drive.ts` autopilot lap (`--json`) | 123.85261100167271 s, JSON sha `78daea58…` | the same | yes |
| board keys (`pins.test.ts`) | 12oxe5efqsv, 0aitg05wi4d, 0ewchkyn2w5 | the same | yes: they hash PHYSICS_VERSION, car.json, the track length and rev, not the code |

The scoreboard replay tests (`replay.test.ts`: record live, replay, lap time `toBe` and state) pass. They record and
replay in the same process, so they hold on any host; there are no stored traces from before this round.

What this Mac's own Node computes is not the server's: release-040 run natively here replays the same Laguna trace
to 139.3509 / **139.3826** s (the server: 139.3511 / 139.3541), and self-play / drive.ts give other numbers too
(drive.ts 123.83767973117908 s). Numbers measured on this Mac before this round were the Mac's, not the server's.
After this round the physics computes the server's values on this Mac as well; tools that also use `Math.*` outside
the physics (the self-play AI, test drivers) still see the Mac's maths there.

### 4.1 Tests that moved on this Mac

- `surface.test.ts` "9 s Laguna drive is bit-identical to the fixture": the fixture had been recorded with this Mac's
  contracted maths. Re-recorded with its own tool (`record_onpave.ts`); the test stays bit-exact. Evidence that only the
  maths moved: release-040 and this branch, both with the strict harness, give the same trace (sha `f69802f0…`).
- **`ai_race.test.ts` "45 cars, 3 laps …" fails on this Mac (open).** Its last check, "a car in control never crosses
  the pit-exit cones", sees car #49 cross for 42 samples (0.84 s) with no mishap or recovery. The AI keeps `Math.*`
  (brief), so on this Mac the race now runs on mixed maths (physics strict, AI contracted) and takes a different
  course. It is not a regression on the server's maths: release-040 and this branch, both strict, pass this test and
  give the same race. With the strict maths everywhere, release-040 itself fails `ai_behaviour.test.ts` "full field, 2
  laps" (`expected 1 to be +0`), which this branch also does, identically. These AI tests hold on the arithmetic they were
  tuned on and break on another; the cone crossing is real AI behaviour (a car in control in the pit-exit lane) that
  any browser's maths could produce. Not loosened; left for an AI round or the owner's call (section 7).

## 5. Proof: cross-engine identity, and what is open

`tools/determinism/browser_trace.mts` loads the built game (`npm run build`, `npx vite preview --port 4173`) in a
Playwright engine, starts a hot lap through the game's own `HotlapLoop` / `HotlapSim` and recording (rolling start with
the auto-launch), installs `tools/determinism/autopilot.ts` as the loop's input reader, advances the sim from the
script (render loop frozen), takes the trace at the end of lap 6, then replays it on Node with the server's code and
compares every lap time and the 59-value final state (pose, velocities, rpm, gear, per-wheel state, sim clock). Six
laps run past the 720 s `LIMITS.maxTraceSteps` cap that bounds a posted trace, so the tool (and the fixture test)
replays with `replayTrace`'s loop without the cap.

| engine | track | steps | laps (s) | lap times | final state |
|---|---|---|---|---|---|
| WebKit 26.5 (Playwright 1.61.1, `webkit-2311`) | Laguna Seca | 859 999 | 139.3537, 139.3511, 139.3506, 139.3489, 139.3499, 139.3500 | **6 / 6 bit-identical** | **bit-identical** |
| WebKit 26.5 | Sonoma | 932 999 | 154.8721, 154.5268, 154.5308, 154.5297, 154.5306, 154.5297 | **6 / 6** | **bit-identical** |
| Chrome 149 headless (control, default flags) | Laguna Seca | 859 999 | as WebKit | **6 / 6** | **bit-identical** |
| Chrome 149 headless | Sonoma | 932 999 | as WebKit | **6 / 6** | **bit-identical** |
| Firefox / SpiderMonkey | — | — | — | not run: Playwright's Firefox is not installed here and was not downloaded (about 100 MB; a download that would be executed) | — |

Before (the release-040 build, same tool, replayed with release-040 code on the strict maths): the WebKit trace's
lap 5 is 139.3500 s in WebKit and 139.2977 s on the server; the Chrome trace drifts by lap 3 (139.3505 against
139.3491) and the replay never completes lap 4. Replaying one autopilot trace in each engine with release-040 code
gives lap 2 = 139.3970 (Chrome), 139.3539 (WebKit), 139.3541 (server); with this branch 139.3541 in all three.

The WebKit and Chrome traces of a track came out with identical rows: the autopilot's own (engine-specific) maths
never changed a quantised input, which is itself a check that the two engines ran the identical physics for the
whole 860 s. `src/scoreboard/__tests__/crossengine.test.ts` keeps the WebKit Laguna trace (403 KB gzipped) and its
WebKit lap and state bits.

### Open: `Math.pow` (stopped, the owner's decision)

The tyre's load sensitivity calls `Math.pow(Fz / Fz0, -0.1)` four times a step. V8 14.6 (Node 24 and 26, Chrome) has
`--use-std-math-pow` on by default: `Math.pow` is the platform C library's `std::pow` after a few special cases, so
there is no V8 pow to port. The server's pow is glibc's (Vercel, linux-x64), the iPhone's and every Mac's is Apple's,
Windows Chrome's is the UCRT's, Firefox's is its platform's. Glibc's pow (ARM optimized-routines, < 0.52 ulp, not
correctly rounded) has FMA and non-FMA code paths selected by CPU, so even a port of it could only be proven against
the server on a Linux x86-64 machine, which this round does not have. Node 22 would have used V8's own fdlibm pow
(the same on every platform, and portable to JS), but the project runs Node 24.

So the cross-engine proof above holds with pow equal on both sides, which it is on this Mac (WebKit, Chrome and Node
all call Apple's libm). Between an iPhone and the server, pow can still differ in the last bit for some loads, and a
lap can drift from there. Options:

| | A. port glibc's pow, verify on Linux | B. software pow + PHYSICS_VERSION bump | C. leave pow native |
|---|---|---|---|
| server results | unchanged if the port matches Vercel's glibc bit for bit | change: new boards, the old ones expire by the 30-day TTL | unchanged |
| iPhone / Firefox / Windows identical to the server | yes | yes | no: pow can differ in the last bit |
| proof needed | a Linux x86-64 run (CI, a container, or a preview function) of the 76 M recorded arguments against Node's Math.pow; glibc's FMA path vs non-FMA path matters | the same proofs as this round (port = its own reference) | none |
| work | port ~300 lines + two 128-entry tables, exact FMA emulation (two-product) | port fdlibm's `__ieee754_pow` (V8's `legacy::pow`, already in V8's sources) | none |
| risk | the Vercel host is not x86-64 (arm64 would differ again), or glibc changes | players lose their 0.3.0 times | Safari players' laps can be rejected or replayed a little differently |

Until then the 0.05 s tolerance stays as it is (section 6) and no client note was added (section 7).

## 6. Performance

The physics step on the 302 380-step Laguna autopilot replay (`tools/determinism/bench.mts`, best of 5-7):

| engine | release-040 (native Math) | this branch (dmath) | change |
|---|---|---|---|
| Chrome 149 headless | 1.766 µs | 1.921 µs | +8.5 % |
| WebKit 26.5 | 1.605 µs | 1.714 µs | +6.8 % |
| Node 26.12 on this Mac | 1.62 µs | 1.92 µs | **+18.6 %** (over the 10 % budget) |

In the browsers the cost is within 10 %. A 60 Hz frame steps ~17 times: 33 µs of a 16.7 ms frame (0.2 %).
On Node the baseline is this Mac's FMA-contracted C fdlibm; the port's atan (22 calls a step, 82 % on its short path)
is the largest share. Optimisations done: double-threshold range tests instead of word extraction, inline-sized fast
paths for atan and sin, constants as scalars, no allocation. A server replay of one lap (159 000 steps) goes from about
0.26 s to 0.31 s of CPU; the worst case (720 000 steps) about 1.4 s, within `maxDuration` 30 s. Not measured on
linux-x64, where the native baseline has no FMA and is likely slower.

## 7. Scoreboard tolerance and client note

- `verifyHotlap` keeps `|replayed − claimed| ≤ 0.05 s` and stores the replayed time. Not tightened to bits: pow
  (section 5) can still make an iPhone lap differ from the server's in the last bits, and a 0.3.0 page still open in
  a browser (same board key, native maths) would be rejected outright. Tighten when pow is settled.
- The client note ("phone laps verify best early in a session") was not added: the cross-engine proof passed for
  WebKit and Chrome. Whether Safari players need it depends on the pow decision.
- Open for the owner: the pow choice (section 5); `ai_race.test.ts` on this Mac (section 4.1); confirming the Vercel
  function's architecture (x86-64) on the first preview.

## 8. Re-running the proofs

```sh
npx vitest run src/physics/__tests__/dmath.test.ts src/scoreboard/__tests__/crossengine.test.ts
npx tsx tools/determinism/record_args.mts /tmp/dmath_args [browser traces …]       # replay arguments
npx tsx tools/determinism/oracle.mts --args /tmp/dmath_args [--write]               # vs Chromium's strict V8
npm run build && npx vite preview --port 4173 --strictPort &
npx tsx tools/determinism/browser_trace.mts webkit --track laguna_seca --laps 6 --out /tmp/wk.json
npx tsx tools/determinism/bench.mts . /tmp/trace.json --engine chromium
```
