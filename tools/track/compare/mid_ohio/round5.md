# Mid-Ohio round 5: GPT 6 Astra's round-4 items, stage 2 (racing line without logger laps)

Opus 5.5, 26 Oct 2026, branch `mid-ohio` (from 0948c24). Scope: the five items of Astra's round-4 review (verdict:
mergeable after the next stages, no blocker), then stage 2: the racing line on the round-4 geometry with no logger laps,
validated against real footage and by the drive proxy. Not in this round: scenery, far terrain, the registry beyond the
local wip stand-in, the Mid-Ohio field, AI tuning, previews. Package `tools/track/out/mid_ohio_r5/` (local).

## 1. Astra's items

| # | item | what changed | evidence |
|---|---|---|---|
| A1 (MAJOR) | Laguna reproduction: ghost builder found zero official rows | `tools/ghosts/build_ghosts.py`: optional untracked alias file `tools/ghosts/drivers.local.json` (`ALIAS_FILE` l.147, `load_aliases` l.150, `alias_labels` l.162; keys are a logger label or `sha256:<hex of the label>`, so the file need not hold a label in clear; `PROBE_GHOST_ALIASES` overrides the path), applied to `sections.pkl` and `official.pkl` before the existing "16d7 pre-stop" -> driver A rule; a clear stop when a driver has clean sections but no official laps (l.351) instead of the pandas `idxmin` traceback; ghost lap ids `driver_x_best` (l.364; the rewrite had left `driver x_best`, which `drive.ts` and the implied-g table look up as `driver_a_best`). `.gitignore` lists the alias file. Documented in the builder's docstring. Tests `tools/track/test_ghost_aliases.py` (3, synthetic labels). | section 2 |
| A2 (MINOR) | `profile_bank.py` multiple rules | overlapping rules refused (`rules`, l.82-90); each rule keeps its own delta (`q['dq']`, l.103) and the heightfield pass carries that, not the aggregate (l.141). Tests (`test_profile_bank.py`): two overlapping rules refused; two separate rules each applied once (profile delta = sum of the single-rule deltas, both peaks halved, not quartered; heightfield = sum of the single-rule heightfields). | Mid-Ohio rebuilt (`--stage geometry --out tools/track/out/mid_ohio_r5`, exit 0): track.json, heightfield.bin, ortho.jpg `cmp`-identical to round 4 (d19cfb7823695525 / eb74f48192e28e3c); same report line: peak s 1968, 4.38 -> 2.2 deg, changed 1864..2005, 756 cells |
| A3 (MINOR) | speed-integration tests | `tools/track/inventory/catalyst_speed.py`: `validate_times` (l.57: finite, strictly increasing), `series` (l.71: frames without a reading left out), `integrate` (l.78: crossings ordered and inside the samples, no extrapolation); `main` uses them unchanged in result. Tests `inventory/test_catalyst_speed.py` (4): a known-distance trace (900 m and 750 m exact, crossings between samples), missing samples (bridged linearly; exact on linear stretches), timestamp validation (decreasing, repeated, NaN, crossings outside, crossings reversed), and the saved N837 lap re-integrated from its own rows: 3558.9 m and 3561.9 / 3555.5 m, as recorded | tests pass |
| A4 (MAJOR for scenery) | weak time maps | `tools/track/inventory/inventory.py`: opt-in `position_uncertainty` in `source.json` (docstring l.21; `sigma_at` l.182, `add_uncertainty` l.198). Every row gets `sigma_s_m` (the larger leave-one-out residual of the two anchors bracketing its t; a row with an explicit s takes its video's map at the source time), `sigma_basis` and `placement`: 'corroborate' when the row's map has a residual over `corroborate_over_m` = 40 m (SKILL.md 0.7, line 228), else 'direct'. The residuals are an indicator, not a bound. `inventory.json` carries the per-map table; `inventory.md` a section and two columns. Unit test `UncertaintyTest` in `test_inventory.py`. | Mid-Ohio re-emitted: N837 105 rows direct (largest residual 14.8 m), 360 lap 209 rows (196 + 13 pit) direct (20.4 m), IndyCar A 26 direct (22.4 m), **B 19 and C 21 corroborate** (60.1 / 55.1 m); sigma per row B 34.3-60.1 m, C 38.2-55.1 m; every other field of every row identical to round 4 (checked by stripping the new keys). Sonoma and Buttonwillow: inventory.json and inventory.md from the HEAD and the new `inventory.py` `cmp`-identical |
| A5 | wording in `round4.md` | Laguna diagnosis corrected (labels, not a missing cache; fixed here); "a driven line runs about 1 % inside a centreline" replaced by the measured statement (this lap 1.07 % shorter than the built centre, 1.69 % shorter than the raw OSM loop); +-27.9 m described as the display-rounding term alone; the run-off raise marked unresolved; "four maps" -> five in total; heights described as about seven readings propagated to 75 rows, with the camera-height and uniform-armco assumptions, and the lidar cross-check below | `round4.md` sections 2, 3, 6, 7, 9 |

**Lidar cross-check of three heights** (`r5/lidar_heights.py` -> `r5/lidar_heights.json`; 2019 USGS lidar, local cache,
against the round-5 package's road):

| object | inventory (2025-26 video) | lidar 2019 | verdict |
|---|---|---|---|
| pit wall, left of the main straight (10 sections s 3510 -> 200) | 0.7 m (horizon ratio, 0.64-0.75, 360 k52 left) | top 0.98-1.11 m above the track's left edge (median 1.04), 0.87-1.23 m above the pit-lane side (median 1.04); a 1.25-2.0 m wide ridge 0.6-2.1 m beyond the edge; no higher returns over it | **disagrees by ~0.35 m**: the horizon-ratio reading scales with the assumed 1.7 m camera height (1.0 m would need ~2.4 m), so either the wall changed since 2019, the ridge includes a base or attachment, or the frame reading is off. Open for scenery: re-measure (a second frame, a known-size reference) before building the wall |
| T1 (Firestone) footbridge deck | no height (deferred to the lidar) | returns over the road at s 228-238, deck top 4.42 m above the road centre (classes 1, 2, 17; the class-2 contamination the profile_gaps repair masks) | lidar is the measure: 4.4 m deck top |
| covered grandstand, right of the main straight | 7 m (storeys) | s 3560-3590: 6.3-6.5 m above the right edge at 28-29 m beyond, 6.8-6.9 m above the ground between; a second structure at s 90-180, 42-48 m beyond, 6.7 -> 4.5 m above the edge (its roof sloping or stepping); nothing over 3.6 m within 120 m at s 0-75 | agrees within ~0.7 m; the stand's extent differs from the time-mapped rows (s 0 / 72 / 90 rows vs lidar ends ~3590 and starts again ~90): for scenery |

## 2. Laguna stage-1 reproduction (SKILL Acceptance 6)

The labels on disk were read, not guessed (`/tmp` helper, labels printed only as sha256 prefixes): `sections.pkl` holds
six labels (Coby, "16d7 pre-stop" and four others), `official.pkl` five. Each official label's best lap was matched to
`public/tracks/laguna_seca/ghosts.json` by logger file, official lap number and lap time (0e98 lap 11 -> driver C,
0e98 lap 35 -> driver B, 1d10 lap 134 -> driver D, 16d7 lap 166 -> driver A; Coby unchanged), and the four sha256 keys
were written to `tools/ghosts/drivers.local.json` in this worktree (git-ignored, never committed).

`build_track.py --track laguna_seca --stage geometry --out tools/track/out/laguna_repro_r5 --write-on-fail` (log
`tools/track/out/laguna_repro_r5.log`):

| check | reference (SKILL Acceptance 6) | round 5 | result |
|---|---|---|---|
| provisional racing line (build_ghosts.py on the logger laps) | runs | runs (the "argmin of an empty sequence" is gone) | ok |
| track.json sha256 | d4e8634710813961 (pipeline reference; the accepted ea1afb899d5dc66b carries the 18 Oct hand steps) | d4e8634710813961 | ok |
| heightfield.bin | byte-identical to `public/tracks/laguna_seca` | `cmp` identical (0abe5b61f0004845) | ok |
| documented gate failure | `edge gate left` 0.105 m at station 46 | `[FAIL] edge gate left ... max adjacent step 0.105 m at 46` and nothing else | as documented (not a leak) |
| `git diff main -- public/tracks/laguna_seca` | empty | empty | ok |

Without the alias file the builder now stops with: `build_ghosts: 'driver A' has 1 clean logger section row(s) but no
official lap under that label in .../official.pkl; ... Map them in the untracked alias file
tools/ghosts/drivers.local.json`. With it, Laguna's ghost stage on the reproduced package gives the published lap list
exactly (ids, lap times 140.434 / 121.584 / 120.627 / 126.897 / 119.323, official laps, optimal 117.995 s), every
ghost and implied-g check ok.

Other byte identities this round: Sonoma and Buttonwillow `ghosts.json` rebuilt by the new builder from their published
track.json are `cmp`-identical to the published files; `build_track.py` is unchanged this round, so round 4's Sonoma
stage-1 proof (track.json and heightfield.bin `cmp`-identical) stands.

## 3. Stage 2: the racing line (no logger laps)

`build_track.py --track mid_ohio --stage ghosts --out tools/track/out/mid_ohio_r5` (exit 0), the Sonoma / Buttonwillow
path: config `logger_dir=None`, `ghosts` defaults (margin 1.0 m, jerk_w 3), the pure bounded minimum-curvature line on
the round-4 geometry (T4 bank as built by the `profile_bank` rule), `laps: []`. The AI's corner finder and speed profile
run on this line at load (src/physics/ai/line.ts); nothing else is written. ghosts.json sha256 9124c3d34baffcfd.

| gate | value | limit | result |
|---|---|---|---|
| pipeline: line inside edges | min clearance 1.00 m | >= margin 1.0 m (SKILL 2.2) | ok |
| pipeline: line curvature | sum k^2 0.1477 vs centre 0.1720 | below the centre's | ok |
| independent (`r5/line_check.py` -> `r5/line_check.json`): every 1 m station, offsets interpolated as the app reads them, against track.json left / right (the inside-of-kerb race edges, owner decision 2) | min clearance 1.000 m (station 2951, right); 0 stations under 1.0 m | 1.0 m | ok |
| laps | [] | no invented logger lap | ok |
| grid | 1798 points x 2.001386 m = the 3597.49 m lap | | ok |
| offsets | -5.43 .. +5.46 m; line 3524.4 m (centre 3597.5 m); smallest line radius 28.5 m | | report |
| implied-g table (2.3) | n/a: no logger laps; the autopilot lap checks the line (section 5) | | |

## 4. Real-footage comparison (`r5/footage_compare.py` -> `r5/footage_compare.json`)

N837 lap 149 (Catalyst 1 Hz speed, round 4, placed by the N837 time map, residuals <= 14.8 m) against the line's speed
profile (`drive.ts` target profile at alat 1.2 g with banking: the solver's prediction) and the autopilot lap on it. The
N837 car is not a Probe, and **lap 149 is not its best**: the overlay's delta against its session best (1:53.71) grows
from +0.11 s at t7 to +10.93 s at t127 (`r5/n837_delta.json`, read by eye), so the lap is 9.8 % off that car's best,
losing fastest at T1 (t10-16), T8-T9 (1.59 s in t88-97), T11 and the Carousel. Shapes and ratios only; "rel" is the
ratio relative to the median ratio of all corners (or all straights).

| corner | s | centre R (m) | line R min (m) | N837 min (km/h) | profile min | autopilot min | profile / N837 (rel) | autopilot / N837 (rel) |
|---|---|---|---|---|---|---|---|---|
| T1 | 357 | 69.3 | 102 | 95.0 (s 309) | 109.5 | 109.2 | 1.153 (+11.7 %) | 1.149 (+13.3 %) |
| T2 Keyhole | 958 | 43.4 | 39 | 66.0 | 69.4 | 70.2 | 1.052 (+1.9 %) | 1.064 (+4.8 %) |
| T3 | 1445 | 299.7 | 488 | 152.9 | 141.6 | 141.2 | 0.926 (-10.3 %) | 0.923 (-9.0 %) |
| T4 | 1961 | 41.1 | 42 | 69.2 | 70.9 | 70.2 | 1.025 (-0.7 %) | 1.014 (0.0 %) |
| T5 Madness | 2100 | 38.2 | 34 | 69.2 | 71.6 | 69.9 | 1.035 (+0.2 %) | 1.010 (-0.4 %) |
| T6 | 2282 | 34.5 | 35 | 74.0 | 69.7 | 66.7 | 0.942 (-8.7 %) | 0.901 (-11.1 %) |
| T7 | 2387 | 51.8 | 72 | 85.3 | 80.0 | 74.0 | 0.938 (-9.1 %) | 0.868 (-14.5 %) |
| T8 | 2521 | 52.3 | 88 | 85.3 (s 2552) | 104.3 | 101.9 | 1.223 (+18.5 %) | 1.195 (+17.8 %) |
| T9 | 2643 | 38.5 | 47 | 70.8 | 78.0 | 75.2 | 1.102 (+6.7 %) | 1.062 (+4.7 %) |
| T10 Thunder Valley | 2931 | 150.7 | 216 | 107.8 | 118.4 | 115.1 | 1.098 (+6.4 %) | 1.068 (+5.3 %) |
| T11 | 3086 | 58.8 | 71 | 90.1 | 93.0 | 90.8 | 1.032 (0.0 %) | 1.008 (-0.7 %) |
| T12 Carousel | 3351 | 38.7 | 34 | 66.0 | 67.8 | 67.1 | 1.027 (-0.5 %) | 1.017 (+0.2 %) |
| T13 | 3454 | 44.4 | 65 | 77.2 | 78.3 | 72.6 | 1.014 (-1.7 %) | 0.940 (-7.3 %) |

Median ratio, corners: profile 1.032, autopilot 1.014.

| straight (max before braking) | N837 | profile | autopilot | profile / N837 (rel) | autopilot / N837 (rel) |
|---|---|---|---|---|---|
| T1 -> Keyhole | 140.0 | 135.1 | 134.9 | 0.965 (-4.4 %) | 0.964 (-2.4 %) |
| Keyhole -> T3 | 148.1 | 141.6 | 141.0 | 0.956 (-5.3 %) | 0.952 (-3.5 %) |
| T3 -> T4 (back straight) | 175.4 | 169.0 | 167.7 | 0.964 (-4.6 %) | 0.956 (-3.1 %) |
| Madness -> T6 | 98.2 | 106.7 | 103.0 | 1.087 (+7.6 %) | 1.049 (+6.3 %) |
| T9 -> Thunder Valley | 115.9 | 118.4 | 114.9 | 1.022 (+1.2 %) | 0.991 (+0.4 %) |
| T11 -> Carousel | 107.8 | 109.3 | 106.4 | 1.014 (+0.4 %) | 0.987 (0.0 %) |
| T13 -> T1 (pit straight) | 132.0 | 133.3 | 132.8 | 1.010 (0.0 %) | 1.006 (+1.9 %) |

| lap | N837 lap 149 | N837 session best (overlay) | profile (solver) | autopilot |
|---|---|---|---|---|
| time | 2:04.84 | 1:53.71 | 1:56.43 | 1:59.25 |
| ratio to lap 149 / to the session best | 1 / 1.098 | 0.911 / 1 | 0.933 / 1.024 | 0.955 / 1.049 |
| length | 3558.9 m driven (speed-integrated) | | line 3524.4 m | |

Where the line agrees: the Keyhole, T4, Madness, T11, the Carousel and T13 sit within 2 % of the median ratio; the
long-straight maxima keep one ratio (0.956-0.965: the N837 car is about 4 % quicker at the end of a long straight, the
same on all three), so the profile's shape matches the footage there.

Where it disagrees, and why:
- **T6 and T7 (-9 %, the autopilot -11 to -15 %)**: the line stays 1 m inside the inside-of-kerb race edges (owner
  decision 2, skill margin); the real cars use the kerbs (IndyCar segment A t56-t62, in the T5-T9 stretch, which has
  no anchor between T4 and the PERMCO bridge: wheels on the yellow and the red/white kerbs at apexes and exits), so
  their radius is larger. This is the no-logger pattern the skill expects
  (slow at the tightest corners), not a geometry fault on this evidence. T13 (-7 % autopilot only) is the autopilot
  under-speeding its target (78.3 profile vs 72.6 driven), not the line.
- **T8 (+18 %), and T9 / Thunder Valley (+7 %) after it**: the line opens T8 to R 88 m (centre 52.3 m) and holds
  104-119 km/h; N837 brakes from 112.7 to 85.3 km/h between s 2473 and 2552, just after a crest (grade +6.4 % to
  -6.3 % over s 2420-2500). Two explanations, not separable on this lap: lap 149 loses time to its own best fastest
  exactly here (1.59 s in 9 s), and the profile has no crest-unload term (the race AI's has one). **Check T8's edges
  and the line through the crest on the hood sheet (1.10) and against a second onboard before scenery.**
- **T1 (+12 %)**: the line uses the full width (R 102 m vs 69 m centre), as the IndyCar does (t18-t28: right under the
  bridge, apex left, exit onto the yellow kerb right); N837 is slowest under the bridge (88.5 km/h at s 255) and lap 149
  loses 1.2 s to its best through t10-16. Read as a slow lap there, not a line error.
- **T3 (-10 %)**: not a corner minimum: the line is flat out through the R 300 kink; both minima are the acceleration
  out of the Keyhole at the window start, where the N837 car is ahead on power (as on every long straight).
- **Madness -> T6 (+8 %)**: a 120 m run; N837 lifts early for T6.
- IndyCar segments (qualitative only; frames of segment A looked at for T1 and the T5-T9 stretch): full-width lines
  with kerb use; no IndyCar speed is read.

## 5. Drive proxy and self-play (SKILL 1.10 validation, stage 5 numbers; no tuning)

`npx tsx tools/calibrate/drive.ts --track tools/track/out/mid_ohio_r5 --alat 1.2 --learn 25 --bank`
(`r5/drive_report.txt`, `r5/drive_summary.json`). `drive.ts` did not compile on this branch or on main: the history
rewrite had turned two identifiers into `errdriver A` / `brakingdriver A` (lines 509, 576, 585, 629, 644); repaired to
`errDriverA` / `brakingDriverA` (no behaviour change).

| measure | value |
|---|---|
| autopilot lap | 1:59.25, complete, no spin |
| solver's predicted lap (target profile) | 1:56.43; autopilot +2.4 % (Laguna's logger-built package: 1:59.24 driven against its ghosts) |
| line tracking | max lateral error 0.94 m; 290 steps (0.29 s) with a wheel over the left edge at s 1861-1871 (T4 braking, where the line runs at its 1.0 m margin and the lateral error is 0.22-0.29 m) |
| peaks | lateral 1.36 g, decel 0.88 g (threshold 0.914 g); top 167.7 km/h (flat-ground 190.3) |

Self-play, **STAND-IN**: `public/tracks/mid_ohio/` built locally in this worktree from `tools/track/out/mid_ohio_r5`
(track.json, heightfield.bin, ortho.jpg, ghosts.json; rev 05d6072129 over the three package files) and a `TRACKS` entry
with `wip: true` (`r5/registry_standin.patch`; NOT committed, the package NOT committed); the pace and identity are
LAGUNA's (45 cars), the start s 3500 on the pit straight. `npx tsx tools/race/selfplay.ts --track mid_ohio --laps 2
--seed <n>` (`r5/selfplay_standin*.{json,txt}`):

| seed | car-laps | line rms alone (p95) | worst alone | AI-AI contacts / car-lap | four-off / car-lap (non-mishap) | mishaps | passes (stuck median) |
|---|---|---|---|---|---|---|---|
| 1 | 77.5 | 0.36 m (0.64) | 4.83 m at s 1570 | 0.026 | 0.039 (0.026) | 2 (wide, spin; both T2) | 160 (15.7 s) |
| 2 | 76.3 | 0.30 m (0.58) | 3.15 m at s 265 | 0.039 | 0.066 (0.066) | 0 | 175 (14.9 s) |
| 3 | 78.0 | 0.29 m (0.57) | 2.51 m at s 1755 | 0.038 | 0.051 (0.051) | 1 (wide, T5) | 200 (8.0 s) |

Line rms is inside the target (< 0.5 m) on every seed; T1 has the largest per-corner rms (0.79 m, seed 1). Contacts are
at the top of Laguna's band (0.012-0.038) and over the printed 0.02 target: a stand-in field on untuned AI knobs
(followScale / laneMargin / shiftGrip defaults), so not a verdict. One AI finding for the AI stage (not changed here):
`src/physics/ai/line.ts:188` names any corner `T8` "T8 Corkscrew" and `driver.ts:203` applies Laguna's Corkscrew
no-passing zone to it, so Mid-Ohio's T8 inherits that zone (21-29 pass attempts per run end "corkscrew").

Tests: every `test_*.py` under `tools/track` 144 passed (pytest); `inventory/test_inventory.py` 11 OK (stdlib);
`npx vitest run src/app src/scoreboard` 38 files, 357 tests passed with the stand-in registry entry (the registry test
checks its rev). The full `npx vitest run` and `npm run build` were not run this round (pre-merge gates).

## 6. Stage ledger (round 5)

| step | record |
|---|---|
| 0.1-0.10 | round 4; 0.7 adds `position_uncertainty` (section 1, A4); 0.9 adds the lidar cross-check (section 1) |
| 1.x geometry | unchanged; rebuilt byte-identical (A2) |
| 1.10 driver's-eye sheet | **open**: not shot this round; the local package and stand-in registry now make `camera_walk.ts --no-rows --back-step 0 --pit-step 0 --no-runoff` runnable; for the orchestrator's review before stage 2 is accepted (T8 first) |
| 1.11 derived data | racing line rebuilt from the package (this round); on-pavement fixture, field pace: later stages |
| 2.1 laps | n/a: no logger laps; `laps: []` |
| 2.2 racing line | section 3 |
| 2.3 implied g | n/a without a logger; autopilot lap (section 5) |
| Acceptance 6 | Laguna reproduction (section 2); Sonoma stage 1 unchanged code (round 4 proof); ghosts.json identities (section 2) |

## 7. Left open for scenery and later stages

- The owner's round-2 green strokes as paved boundaries (pit-exit apron with the hatch, the unused chicane, the T1-T3
  connector), from `owner/r2/merged.json` `green_enu_xy`; their paving tones measured from the captures.
- The weak time maps: IndyCar B and C rows are 'corroborate' (sigma 34-60 m): no precise endpoint from them alone.
- Heights: the pit wall (0.7 m video vs 1.04 m lidar) to settle; armco one height for all runs (0.8 / 1.3 m readings);
  the 1.7 m camera assumption; the footbridge deck 4.4 m from the lidar; the grandstand extents from the lidar.
- The pit lane: no 2024+ video drives it; the 13 pit rows are seen from the track.
- T4: the run-off raise is unresolved (the rule lowers the outside shoulder; it does not reconstruct the fill).
- T8 through the crest (section 4), the T4-entry wheel-off at the 1 m margin, and the Corkscrew no-pass zone keyed to
  "T8" (section 5).
- The Mid-Ohio field and pace (Lemons "Mid-West Crisis"), the registry entry and the package publication, AI knobs:
  the stand-in here is Laguna's field and is not committed.

## 8. Commits (branch `mid-ohio`)

b15e52e ghost-builder aliases and loud failure; 48870de catalyst_speed validation and tests; 7e79283 profile_bank per-rule
deltas and overlap refusal; 027c4ee inventory positional uncertainty, Mid-Ohio re-emitted; 0e9755b round-4 ledger
corrections and the lidar cross-check; 5f4cf26 stage 2 checks, footage comparison, drive proxy, drive.ts repair;
66dfca9 self-play stand-in records; this ledger.
