# Physics determinism across engines (0.4.0 round, 26 Oct 2026)

Goal: a hot-lap trace recorded in any browser engine (Chrome / V8, Safari and every iPhone browser / JavaScriptCore,
Firefox / SpiderMonkey) replays on the scoreboard server (Vercel, Node 24, V8) to the same bits, without changing
the server's results (the 0.3.0 boards and their keys stay valid). Code: `src/physics/dmath.ts`; proofs:
`src/physics/__tests__/dmath.test.ts`, `tools/determinism/`.

**Status (round 2, 26 Oct 2026): every transcendental function the physics and the AI call is in software, bit-identical
to the server, `Math.pow` included (proven against the Vercel function itself, section 5). The server's results are
unchanged; six-lap traces from WebKit, Chrome and Firefox replay on Node to the bit (section 5). Two AI tests fail on
every host now that the whole race runs on the server's arithmetic (section 4.1): their fixes are AI controller work,
left for the AI round.** (AI robustness round, 26 Oct 2026: both pass again, fixed as driver logic; `src/physics/ai/NOTES.md`
"26 Oct 2026: AI robustness".)

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
| vehicle.ts:1145 | `tyre`, load sensitivity `(Fz/Fz0)^-0.1` | pow (round 2: the server's glibc pow) | 4 |
| vehicle.ts:1228 | brake pedal map `brk^pedalExponent` | pow (round 2) | never: pedalExponent is 1 |
| devtrack.ts:20-138 | the synthetic oval and its scenery (tests only) | exp, sin, cos, hypot (8 calls) | round 2: dmath |
| src/scoreboard/sim.ts:236-239 | `lineSteer`, the live auto-launch (recorded, never replayed) | atan2, sin, cos | round 2: dmath |
| src/physics/ai/*.ts | the AI: pursuit, line build / projection, field derivation, seeded normal draw | atan, atan2, sin, cos, exp, log, hypot, pow, cbrt | round 2: dmath |

Measured on two autopilot replays (Laguna Seca 139.351 s, Sonoma 154.872 s; 324 865 steps,
`tools/determinism/record_args.mts`): atan 7 140 667 calls, sin 4 220 476, cos 1 635 966, hypot 397 372,
atan2 324 871, tan 324 231, log 10 680, exp 0 and hypot (3 args) 0 (launch / reset only). About 42 transcendental
calls per step, plus 4 `Math.pow`.

Round 2 (26 Oct 2026): every remaining native call in `src/physics` and the sim is converted, load-time code included
(geometry, collision world, kerb strips, spec derivations, the rolling start were already on dmath; the eight calls left
in `src/physics` were all in `devtrack.ts`, used only by tests). `dmath.test.ts` forbids any native transcendental call
and `**` in the physics, the sim, the replay and the timer. Still on `Math.*`: rendering and UI, the test drivers and
tools' own autopilots, and `src/app/devtrack.ts` (the app's fallback oval, `?devtrack=1`), whose physics key matches no
board, so such a lap cannot be posted.

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
| cbrt (round 2, the AI) | `cbrt` (FreeBSD / fdlibm) |
| pow (round 2) | V8's `math::pow` special cases (`src/numbers/ieee754.cc`), then **glibc 2.34's** `__ieee754_pow_fma` (`sysdeps/ieee754/dbl-64/e_pow.c`, Szabolcs Nagy 2018, from Arm's optimized-routines; tables in `src/physics/dmath_pow_data.ts`), see section 5. Licence source (AI robustness round): optimized-routines' `math/pow.c`, MIT, checked equivalent (same code paths and fma sites in the x86-64 configuration, tables identical value for value: `tools/determinism/pow_or_tables.py`); notice in `dmath.ts` and on the Credits page |

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
**Confirmed (round 2, the probe in section 5):** the Vercel function runs linux x64, Node v24.21.0 (V8 13.6.233.17),
glibc 2.34, on an Intel Xeon @ 3.00 GHz.

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

Round 2 adds cbrt (1.2·10^6 random arguments plus edges, 0 mismatches; 3 343 edge cases in all). No function was given up.

## 4. Proof: the server's results are unchanged

The server computes V8's fdlibm without contraction and glibc 2.34's pow (section 2.1, section 5), so "unchanged" means:
release-040 run with the server's maths gives the same bits as this branch. On this Mac that is checked by running
release-040 (a `git archive` copy) with `tools/determinism/strict-math.mjs`, which makes `Math.sin / cos / tan / atan /
atan2 / exp / log / hypot / cbrt / pow` the port (= the server) for the whole process, and this branch natively.

| check (round 2) | release-040 with the server's maths | this branch, natively | identical |
|---|---|---|---|
| replay of a 2-lap Laguna autopilot trace (`replay_compare.mts`) | 139.3511 / 139.3709 s, state `7b70235f…` | the same | yes, every bit |
| replay of a 2-lap Sonoma autopilot trace | 154.8720 / 154.5286 s, state `46318a7c…` | the same | yes |
| self-play Laguna, 4 laps, seed 1 (`--json`) | 45 cars, 167.1 car-laps, race 612 s, 0.054 contacts / car-lap | the same | yes: every metric and the order; only the measured µs per step differ |
| self-play Sonoma, 2 laps, seed 1 | 134 cars, 192.3 car-laps, race 297 s, 0.021 contacts / car-lap | the same | yes |
| `tools/calibrate/drive.ts` autopilot lap (`--json`) | 123.85261100167408 s, JSON sha `c9db261c…` | the same with the harness (the tool's own autopilot uses `Math.*`) | yes |
| board keys (`pins.test.ts`) | 12oxe5efqsv, 0aitg05wi4d, 0ewchkyn2w5 | the same | yes: they hash PHYSICS_VERSION, car.json, the track length and rev, not the code |

Since round 2 the whole race (the AI included) computes the server's values natively on any host, so self-play is
identical without the harness. The scoreboard replay tests (record live, replay, lap time `toBe` and state) pass.

What this Mac's own Node computed before is not the server's: release-040 run natively here replays the Laguna trace to
139.3509 / 139.3826 s, the server 139.3511 / **139.3709** s. Pow alone moves that second lap by 17 ms (139.3541 with
Apple's pow, round 1): ulp differences in the tyre grow into lap time over a lap, which is why pow had to match.

### 4.1 Tests that moved

- `surface.test.ts` "9 s Laguna drive is bit-identical to the fixture": recorded with this Mac's contracted maths and
  Apple's pow; re-recorded with its own tool (`record_onpave.ts`), the test stays bit-exact. (Its driver uses `Math.*`,
  so the fixture is this host's.)
- `crossengine.test.ts`: the WebKit fixture is re-recorded with the server's pow (section 5).
- **Two AI tests fail on every host now (open, the AI round).** With the AI on dmath the whole race runs on one
  arithmetic, the server's; on it (and also with release-040 run on the server's maths) two seeded checks fail. They had
  passed only on this Mac's contracted maths:
  - `ai_race.test.ts` "45 cars, 3 laps": "a car in control never crosses the pit-exit cones". #49 spins on its own at
    T11 exit (no contact: one wheel off at the right edge, full right lock, the car rotates and slides 17 m left into the
    pit-exit lane at 10 m/s, then backwards), and #37 in a pass lane (target 5.3 m left of the line) while the racing
    line itself sweeps 4.8 m left over 90 m at 28 m/s overshoots the cone cap by 0.2 m; at the cap the driver flags
    itself "off track" (the cap counts as the road edge), which drops the lane clamp and rejoins slowly from where it is.
    Neither car has a counted mishap or recovery.
  - `ai_behaviour.test.ts` "full field, 2 laps": 140 passes, the test wants > 150 (every other check passes: 99 / 165
    clearly-faster situations completed, 41 / 56 of those > 15 % quicker, 0.026 contacts per car-lap).
  Tried and reverted (bound: no tuning in this round): (1) off-track detection against the pavement instead of the cone
  cap: #37's crossing shrinks to one 20 ms sample at +0.20 m, #49 unchanged; seeds 2 and 3 then show other in-control
  crossings (#200, #58). (2) A cone-cap guard pulling the shift back by the car's predicted overshoot (lateral velocity ×
  0.4 s): seed 1 clean, but on seeds 2 and 3 it yanks cars into spins (shift to −6 m, speed to 0) and adds crossings.
  A crossing-proof rule needs lateral-momentum-aware lane planning near capped edges and spin handling at T11 exit,
  which changes driving and must be checked against pace and contact bands: the AI round.

## 5. Proof: cross-engine identity, and pow

### 5.1 Pow: the server as the oracle

V8 13.6 / 14.6 (Node 24 / 26, Chrome) has `--use-std-math-pow` on by default: `Math.pow` is the platform C library's
`std::pow` after V8's special cases (y NaN, |x| = 1 with infinite y, y = 2, y = 0.5). The only valid reference is the
server itself. A throwaway preview (branch `powprobe`, `api/powprobe.ts`, never merged; preview
`probe-igzqkxs8x-coby-hartmans-projects.vercel.app`, fetched with `vercel curl`) evaluated the physics' pow sites:

| set (`tools/determinism/pow_cases.ts`) | arguments | this Mac (Apple libm) vs server | the port vs server |
|---|---|---|---|
| load: `(Fz/Fz0)^-0.1`, ratio 0..3 | 100 001 | 194 differ (1 ulp) | **identical** (SHA-256 and every value) |
| pedal: `brk^e`, 0..1, e = 1, 1.5, 2.5 | 3 × 100 001 | e = 1 identical, others differ | **identical** |
| random: log-uniform x in 2^-20..2^21, y in [-8, 8) | 100 000 | 149 differ (1 ulp) | **identical** (every value) |

Server: linux x64, Node v24.21.0, V8 13.6.233.17, glibc 2.34, Intel Xeon @ 3.00 GHz (results in
`tools/determinism/pow_server.json.gz`, checked by `dmath.test.ts`). glibc picks `__ieee754_pow_fma` there: e_pow.c built
with `-mfma -mavx2` and GCC's default contraction, so besides its explicit `__builtin_fma` calls every multiply-add whose
product feeds only additions is fused. Testing each contraction site on and off against the server singled out exactly
that build (all fused: 0 mismatches; the final `scale + scale * tmp` unfused: 13 + 10 of 40 000 differ). The port
emulates each fused operation exactly: Dekker's product, then a correction of the one double-rounding case (a tie)
(checked against an exact BigInt fma on 10^7 triples and on 3·10^6 near-tie triples where the uncorrected sum is wrong
6 334 times: 0 mismatches), plus exact shortcuts where the fused and unfused results provably agree (`k·ln2hi + logc`
is exact for all 128 entries and every k, checked; small-k products are exact). The port also matched an exact-fma
reference on 10^6 wide-range arguments including overflow and underflow.

Pow is therefore no longer open: every engine computes the server's pow.

### 5.2 Six-lap traces from three engines

`tools/determinism/browser_trace.mts` loads the built game (`npm run build`, `npx vite preview --port 4173`) in a
Playwright engine, starts a hot lap through the game's own `HotlapLoop` / `HotlapSim` and recording (rolling start with
the auto-launch), installs `tools/determinism/autopilot.ts` as the loop's input reader, advances the sim from the
script (render loop frozen), takes the trace at the end of lap 6, then replays it on Node with the server's code and
compares every lap time and the 59-value final state (pose, velocities, rpm, gear, per-wheel state, sim clock). Six
laps run past the 720 s `LIMITS.maxTraceSteps` cap that bounds a posted trace, so the tool (and the fixture test)
replays with `replayTrace`'s loop without the cap.

| engine | track | steps | laps (s) | lap times | final state |
|---|---|---|---|---|---|
| WebKit 26.5 (Playwright 1.61.1, `webkit-2311`) | Laguna Seca | 859 999 | 139.3537, 139.3511, 139.3505, 139.3502, 139.3489, 139.3499 | **6 / 6 bit-identical** | **bit-identical** |
| Chrome 149 headless (default flags) | Laguna Seca | 859 999 | the same | **6 / 6** | **bit-identical** |
| Firefox 151.0 (Playwright `firefox-1532`, downloaded in round 2: 98.8 MiB from Playwright's CDN) | Laguna Seca | 859 999 | the same | **6 / 6** | **bit-identical** |
| WebKit 26.5 | Sonoma | 932 999 | 154.8721, 154.5268, 154.5315, 154.5285, 154.5310, 154.5297 | **6 / 6** | **bit-identical** |
| Chrome 149 | Sonoma | 932 999 | the same | **6 / 6** | **bit-identical** |
| Firefox 151.0 | Sonoma | 932 999 | the same | **6 / 6** | **bit-identical** |

The three engines' traces of a track came out with identical rows (sha `1f1e6b30` Laguna, `b3551721` Sonoma): the
autopilot's own engine-specific maths never changed a quantised input, itself a check that the engines ran identical
physics for the whole 860-930 s. With release-040's code the same autopilot trace replays in each engine to a different
lap 2: Chrome 139.3970, WebKit 139.3539, Firefox 139.3541, the server 139.3709; with this branch 139.3709 in all.

Before (round 1, the release-040 build, replayed with release-040 code on the strict maths): the WebKit trace's lap 5 is
139.3500 s in WebKit and 139.2977 s on the server; the Chrome trace drifts by lap 3 and the replay never completes lap 4.

`src/scoreboard/__tests__/crossengine.test.ts` keeps the WebKit Laguna trace (gzipped) and its WebKit lap and state bits.

## 6. Performance

The physics step on the 302 380-step Laguna autopilot replay (`tools/determinism/bench.mts`, best of 5-7). The budget
basis is the browsers (the Mac's contracted Node is not a comparable baseline); round 1 was within it (+8.5 % / +6.8 %):

| engine | release-040 (native Math) | this branch, round 1 (pow native) | this branch, round 2 (all software) | change vs release-040 |
|---|---|---|---|---|
| Chrome 149 headless | 1.766 µs | 1.921 µs (+8.5 %) | 2.373 µs | **+34 %** |
| WebKit 26.5 | 1.579-1.605 µs | 1.714 µs (+6.8 %) | 1.994 µs | **+26 %** |
| Firefox 151.0 | 2.515 µs | — | 3.626 µs | **+44 %** |
| Node 26.12 on this Mac (contracted, not a budget basis) | 1.62 µs | 1.92 µs | 2.43 µs | +50 % |

Over the 10 % budget since pow joined: the software pow is ~0.4-0.6 µs of each step. A 60 Hz frame steps 17 times:
about 40 µs of a 16.7 ms frame in Chrome (0.24 %). A server replay of one lap (159 000 steps) goes from about 0.26 s to
0.39 s of CPU (the 720 000-step worst case about 1.75 s, within `maxDuration` 30 s). Self-play cost (all cars):
Laguna 45 cars 115 µs a step, Sonoma 134 cars 380 µs a step on this Mac.

Pow costs about 145 ns a call in the port (native: 17 ns; 4 calls a step): about 14 exactly emulated fused
multiply-adds each. The per-step share is small against a 16.7 ms frame (17 steps a frame), but it is the largest
single cost of the port and it also lands on every AI car in a race. Further speed-ups (merging the log / exp stages,
pre-splitting more constants) are possible without changing a bit.

## 7. Scoreboard tolerance and client note

- `verifyHotlap` keeps `|replayed − claimed| ≤ 0.05 s` and stores the replayed time. With every engine now computing the
  server's maths it could be tightened to bits; not done here, because a 0.3.0 page still open in a browser (same board
  key, native maths) would then be rejected outright. A candidate for after the 0.4.0 launch.
- No client note ("phone laps verify best early in a session"): the cross-engine proof passed in every engine tested.
- The two AI tests (section 4.1): fixed in the AI robustness round (`src/physics/ai/NOTES.md`).

## 8. Re-running the proofs

```sh
npx vitest run src/physics/__tests__/dmath.test.ts src/scoreboard/__tests__/crossengine.test.ts
npx tsx tools/determinism/record_args.mts /tmp/dmath_args [browser traces …]       # replay arguments
npx tsx tools/determinism/oracle.mts --args /tmp/dmath_args [--write]               # vs Chromium's strict V8
npm run build && npx vite preview --port 4173 --strictPort &
npx tsx tools/determinism/browser_trace.mts webkit|chromium|firefox --track laguna_seca --laps 6 --out /tmp/wk.json
npx tsx tools/determinism/bench.mts . /tmp/trace.json --engine chromium
```
