# Integration dry run, 23 Oct 2026

Branch `integration`, started from `track-pipeline` at 895c5dd (the Sonoma track and pipeline). Merged in order with
`git merge --no-ff`: `buttonwillow` (e1dba23), `field-buttonwillow` (835d57d), `field-sonoma` (cade7a9). Nothing is
pushed and `main` is untouched. Every conflict below was resolved by keeping both sides' intent; nothing was dropped
(no track, car, gate, test or changelog line).

## Merge 1: buttonwillow into integration (track-pipeline)

Background: track-pipeline's last commit (895c5dd, Sonoma round 14B part 1) PORTED the owner-edge tools from buttonwillow
f9c7aec / e1dba23 and generalised them for Sonoma (owner edges local to a `centre.local` window, `--frames` /
`--strokes`, `--across` / `--step` mouths, owner-reference gates without a width model), leaving out buttonwillow's
width model, masks, kerb-search zones and unpainted-side gates (track-pipeline has no `width_model.py`). So for the
ported files the true common ancestor is buttonwillow's version, not the merge base eefd5b3; each was resolved against a
direct diff of the two branch versions, so nothing would be applied twice (the plain 3-way merge would have duplicated
the owner-edge station remap in trackcfg.py, see below).

| file | track-pipeline (ours) intent | buttonwillow (theirs) intent | resolution |
|---|---|---|---|
| `.gitignore` | track the Sonoma edges_r14b outline page | ignore Buttonwillow compare imagery, track its markdown and the edges_r9 / edges_r10 pages | both blocks kept |
| `src/app/scene.ts` (pit boxes) | `no_boxes` lane station ranges with no box lines (Sonoma judge r9) | `pit_lane.boxes` ranges where boxes ARE painted (Buttonwillow note 9) | both filters applied, in that order |
| `src/physics/track.ts` (`buildTrackSurface`) | `buildOverride(opts.terrainOverride)` (round 14A terrain override) | kerb strips built also when only a strip carries its own `profile` (per-run kerb profile) | buttonwillow's kerb-strip condition plus the override line |
| `tools/track/trackcfg.py` docstring | owner_edges / owner_mouths, feature 6th element `{local}` | asphalt_end, warm_thr, mask, width_model, warm_end and kerb_band features | one docstring listing every key and feature kind |
| `tools/track/trackcfg.py` `remap_stations` (auto-merged, fixed by hand) | owner_edges window remap (ported) | the same owner_edges remap plus mask, kerb_search, width_model junctions, kerbs_declared zones | the auto-merge had the owner_edges remap TWICE (stations remapped twice, a silent bug); the second copy removed, everything else kept |
| `tools/track/compare/owner_edges.py` (add/add) | buttonwillow's tool plus `--frames` / `--window` / `--strokes` | the original tool | track-pipeline's (a strict superset) |
| `tools/track/compare/owner_mouths.py` (add/add) | plus `--across` / `--step`, width-model junctions optional | the original (junctions required) | track-pipeline's (superset; still reads the junctions when a width model exists) |
| `tools/track/compare/outline_page.py` (add/add) | plus the no-width-model path (owner-reference gates, per-window widths, before / after) | width-model page | track-pipeline's (superset; the width-model path is unchanged) |
| `tools/track/test_owner_edges_fit.py`, `test_owner_reference.py` (add/add) | Sonoma now declares owner edges: `test_laguna_and_sonoma_declare_no_owner_*` became `test_laguna_declares_no_owner_*` plus `test_sonoma_owner_edges_are_local` | the original tests | track-pipeline's: every assertion kept or made more specific (the Sonoma case is now tested positively), none loosened |
| `tools/track/compare/pose_walk.ts` | `camera` ('hood' / 'chase') per pose or `--camera` | `eye` (camera height above the surface, 4 m ahead) | both: the camera is set, then the eye offset applied, the position restored after the render |
| `tools/track/straights.py` | (the `once` / `width_shared` code was ported from buttonwillow) | plus fit `asphalt_end` (`aend_points`) | buttonwillow's (a strict superset) |
| `tools/track/edge_gate.py` | `owner_gates` (owner-reference gates for a circuit without a width model), junction-step mouths, `main()` owner path | unpainted-side gates (UNPAINTED, `bias_gate`, `side_within_gate`, `per_kind_report`), width gates in `main()` | buttonwillow's file plus `owner_gates` and the comments; `main()`: width gates when a width model exists (buttonwillow), else the owner-reference gates when owner edges and mouths exist (Sonoma) |
| `tools/track/edges_spline.py` | `fit_periodic(..., hold=)` for the local refit (held edges outside the window), `assoc_owner` | AEND / MASK / KSEARCH / WARM_THR detectors, `warm_end`, kerb-search zones, `kerb_band`, `fit_periodic(..., obs=, anchors_cover=)`, `assoc_kind`, unpainted and per-kind reports | buttonwillow's file plus the `hold` parameter (both blends, the hold-aware `within_gated`) and `assoc_owner` (track-pipeline's own definition, capture index -1); `assoc_kind` kept as buttonwillow computes it |
| `tools/track/build_track.py` | build_anchors refactor, `centre.local` (one window or a list) with `owner_windows(phase=)`, owner per-window reports, owner gates without a width model, terrain override (stage 1 and 3), ortho_pave, marks_on_surface, stage-3 owner gates, openings, ground-lines gate | `prior_shift`, lap-length log, width-model pass and gates and `width_model_report.json`, report_by_kind width report, masks and kerb-search zones per remap, unpainted bias / coverage gates and per-kind report, `--publish --partial` | track-pipeline's file with every buttonwillow addition put back: mask / kerb_search set on every remap (also in the local refit); in the converged refit the features are re-taken from the remap when kerb_search or an owner window ACTIVE in that phase exists (Sonoma's owner windows are local-only, so its global fit is unchanged; Buttonwillow's behaviour is unchanged); the width-model pass runs after convergence and before any local refit; width gates if a width model, else owner gates; `fit_assoc_<side>.json` carries both `kind` and `owner` (diagnosis only, work/) |
| `tools/track/build_scenery.py` | `HOLLOWS` (barrier_hollows), `tyre_rows_outside`, marshal `d` and `roof` colour | `CFG_ALL`, `extend_parts_to_walls`, marshal canopy keys (mound_h, railing, stair, base_color, body_h, body_color, pole, roof, fine) | all kept. Marshal record: `d` and a truthy `roof` as track-pipeline writes them, then the canopy keys; a falsy `roof` still passes through as buttonwillow wrote it. Note: Buttonwillow's starter's stand record now has `roof` before `color` (JSON key order only; values identical) |
| `src/app/scenery.ts` types | barrier `arm`, `top_z`; marshal `d` (depth), `roof?: string` (colour) | barrier `pattern` / `sections`; kerb colours `KerbColors` (3 colours); marshal canopy keys, `roof?: boolean` (platform canopy) | union; `roof?: string \| boolean`: a string is the roof colour, a truthy value on a 'platform' is its canopy (the only Buttonwillow use is `roof=True` on the platform; every Sonoma use is a colour) |
| `src/app/scenery.ts` `buildBarriers` | `drawn` parameter; walls from `foot()` to `atTop(top_z)` | `sliceLine`, `barrierSections` (colour sections along a run) | both: sections drawn per slice with the foot and the sliced `top_z` (a copy of the line at its top heights cut at the same arc lengths); without sections exactly track-pipeline's faces |
| `src/app/scenery.ts` marshal posts | style 'deck' (Sonoma 8a tower), `D = m.d ?? W`, roof material from `m.roof` | style 'canopy', `fine` scaffold, dense rails, platform canopy and stair | one builder: canopy, else deck, else the hut / platform with the `fine` options; the hut roof in the roof colour (white when absent, as before) |
| `.claude/skills/build-track/SKILL.md` gate table | four new rows (pavement joins, surface smoothness, ground marks on surface, kerbs on surface); kerb traversal row "no wheel lifted (`it.fails` for Sonoma)" | kerb traversal row: wheel lifts advisory (the owner, 21 Oct 2026) | buttonwillow's kerb traversal row (it matches the merged `kerbgate.test.ts`, which auto-merged to the owner's advisory rule) plus track-pipeline's four rows |

## Merge 2: field-buttonwillow into integration

field-buttonwillow branched from buttonwillow at ff2eb57 (before Buttonwillow rounds 9 and 10), so its track commits are
already in. The only file changed on both sides since that base besides the auto-merged `src/app/modes/race.ts`
(terrain override and the lost-in-the-hills reason on one side, the per-event model queue, ids and silent EVs on the
other, in different places) was the registry.

| file | integration (ours) intent | field-buttonwillow (theirs) intent | resolution |
|---|---|---|---|
| `src/scoreboard/config.ts` `TRACKS.buttonwillow` | the round-10 package: `length_m` 4699.187, `rev` '7acf260f50' | Buttonwillow's own field: the `--own` pace file comment and `identity: 'cars/field/buttonwillow/identity.json'` (package still the round-8 rev '6ebc6e3263', 4703.806 m) | the round-10 length and rev with the field's identity key and comment |

Note for the pace stage: field-buttonwillow's AI_VERSION 8 calibration of the Buttonwillow field (884 fits) was made on
the round-8 package (4703.806 m); the merged tree carries the round-10 package (4699.187 m, edges refit from the
owner's red). The calibration itself is unchanged by this merge.

## Merge 3: field-sonoma into integration

field-sonoma (cade7a9, including the #203 Del Camino B-series engine row) branched from track-pipeline at 427449c.
No conflicts. The car pool (`public/cars/field/models.json`, `credits.json`, 228 `models/*.glb` changed on both sides)
is byte-identical between field-buttonwillow and field-sonoma (`git diff field-buttonwillow field-sonoma` over the pool
is empty), and the merged pool equals field-sonoma's. The other two files changed on both sides, `src/app/loader.ts`
and `src/physics/ai/field.ts`, auto-merged to field-buttonwillow's per-event identity code plus field-sonoma's
`same_car` fields (FieldModelInfo, IdentityCar). `changelog.ts`, `package.json` and the track registry are unchanged by
this merge.

## Checks on the merged tree (6907760)

- `npx vitest run`: 60 files, 502 tests passed, 0 expected failures (track-pipeline alone: 464 + 1 expected fail, the
  Sonoma kerb wheel-lift `it.fails`, now an advisory report by buttonwillow's owner rule of 21 Oct).
- `tsc --noEmit -p tsconfig.build.json`: clean. `npx vite build`: built (one 1.26 MB chunk).
- Pipeline python tests (after merge 1, `uv run --python 3.12 ... -m pytest tools/track`): 71 passed, 3 skipped.
- Self-play (`tools/race/selfplay.ts --track <id>`, defaults: 4 laps, seed 1, the track's AI knobs):

| track | cars | line rms alone | contacts / car-lap (<= 0.02) | four-off / car-lap | same seed on the unmerged branch |
|---|---|---|---|---|---|
| laguna_seca | 45 | 0.30 m | 0.012 | 0.100 | (not run) |
| buttonwillow | 100 | 0.37 m | 0.077 | 0.151 | field-buttonwillow (round-8 package): 0.38 m, 0.107, 0.189; race time 753 s there, 801 s merged |
| sonoma | 45 | 0.46 m | 0.158 | 0.044 | track-pipeline: identical numbers (not caused by the merge) |

- `calibrate_field.ts --track buttonwillow --only 619 --dry` (no file written): #619 refits to scale 0.8640 for its
  160.51 s target on the round-10 package; the stored AI_VERSION 8 scale (fitted on round 8) is 0.87416. The
  Buttonwillow field needs recalibrating on the merged geometry.

# Refresh, 24 Oct 2026: the final Sonoma and Buttonwillow packages

Branch `integration` at b779969 (the dry run above plus the AI-readiness commits). Merged in order with
`git merge --no-ff`: `track-pipeline` (845a321, Sonoma round 14B, rev 6b766e08d6, lap 4105.328 m) and `buttonwillow`
(de8c9b7, Buttonwillow round 11, rev 69e80ace38, lap 4699.187 m). Nothing pushed; `main` and the other worktrees untouched.

For every file changed on the incoming branch, the merged file's change against `integration` was compared with the
branch's own change against the merge base (`git diff <base> <branch> -- f` against `git diff HEAD -- f`, the +/- lines):
identical for every auto-merged file, so nothing was applied twice or lost; the files that differ are the hand
resolutions below. A line-count check (no line occurring more often in the merged file than in either parent) found
no duplicate beyond those explained.

## Refresh merge 1: track-pipeline (845a321) into integration (base 895c5dd)

| file | integration (ours) intent | track-pipeline (theirs) intent | resolution |
|---|---|---|---|
| `.gitignore` | track Buttonwillow's compare markdown and edges_r9 / edges_r10 pages | track the round-14B checkpoint pages (intro / extra) and owner_edges_r14b JSON | both blocks |
| `src/scoreboard/config.ts` `TRACKS.sonoma` | Sonoma's own field: the `identity` key and its pace comment (round 14A, 4098.5 m, rev e4e8928b59) | round 14B: `length_m` 4105.328, `rev` '6b766e08d6' | the round-14B length and rev with the identity key and comment; Sonoma's `ai` knobs unchanged |
| `tools/track/trackcfg.py` docstring | `warm_end` / `kerb_band` feature kinds | `spline.refine` (local knot refinement) | one docstring with both |
| `tools/track/trackcfg.py` `remap_stations` | Buttonwillow's owner_edges remap (stations only), placed with mask / kerb_search | the owner_edges remap in its round-14B form (kerb runs as world points, `_st_or_xy`) plus the `refine` remap, placed after `centre.local` | the round-14B owner_edges remap ONCE and the refine remap; Buttonwillow's earlier copy removed (keeping both would remap the windows twice, the dry run's bug); mask, kerb_search, width_model junctions and kerbs_declared zones kept |
| `tools/track/edges_spline.py` `fit_periodic` | the kerb_search zone check, `obs` given by the caller (width_model.py), `anchors_cover` | `REF_ALL` / `REFINE` per side and the refined `basis()` | the zone check, `REF_ALL` / `REFINE`, the caller's `obs` (else `gather`), `Bx = basis(...)`; the rest of round 14B's step profile and refinement auto-merged around Buttonwillow's per-kind reports |
| auto-merged: `build_track.py`, `build_scenery.py`, `edge_gate.py`, `terrain_override.py`, `build_ghosts.py`, `run_gates.ts`, `owner_edges.py`, `outline_page.py`, `capwin.py`, `src/physics/track.ts` / `types.ts`, `src/app/physics-types.ts`, `CONTRACTS.md`, `src/app/index.ts`, `src/scoreboard/sim.ts`, Sonoma's config | - | round 14B part 2 (stage-3 owner gates read the raw config, coverage carries inventory rows by world position, `known_exposures`, `gap_min` / `wall_gap_margin`, the declared-centre closed road, `margin_zones`, `SurfaceSample.offCourse` in both type mirrors) | each change set identical to track-pipeline's own |

`public/tracks/sonoma/` is byte-identical to track-pipeline's (`git diff --quiet 845a321 -- public/tracks/sonoma`).

## Refresh merge 2: buttonwillow (de8c9b7) into integration (base e1dba23)

| file | integration (ours) intent | buttonwillow (theirs) intent | resolution |
|---|---|---|---|
| `src/scoreboard/config.ts` `TRACKS.buttonwillow` | the field's identity key and pace comment, round-10 rev 7acf260f50, the AI knobs (followScale 1.4, laneMargin 0.7, shiftGrip 1) | round 11: `rev` '69e80ace38' (on its stale comment of an uncalibrated pace file and no identity key) | integration's entry with rev 69e80ace38; the comment names round 11 |
| `tools/track/gates/sceneryGates.ts` | wall tops, wall-tyre joins, tyre faces, run gaps (rounds 12-13) | `coneSpots`, `conesOffSurface` (cones off the surface), `spacing_m` / `src` on cone lines | every gate of both; the cone section appended after run gaps |
| `tools/track/gates/run_gates.ts` | wall tops, joins, tyre faces, run gaps, terrain override, ground marks, `openings`, `known_exposures` | the cones-off-the-surface gate, `cone_tol` / `cones_exempt` | all gates (the cone gate last, before the JSON line, `cones` in the JSON); the config type carries every key |
| `src/scoreboard/__tests__/scenerygates.test.ts` | tests of the round 12-13 gates | three cone-gate tests | the union of the imports and of the describe blocks |
| `tools/track/compare/pose_walk.ts` | `camera` ('hood' / 'chase') per pose and `--camera` | `--port` and `--out` required, flags documented | buttonwillow's required flags and header with the camera key and `--camera` documented |
| `tools/track/tracks/sonoma/config.py` `scenery.gates` | round 14B's gates dict (`inventory_lap`, `known_exposures`, `openings`, the escape-road and pit-in allowed entries; the T1 pit-wall nose entry removed in round 8, 56a3ff0) | `cones_exempt` for the pit-in double white line, on its stale copy of the dict (which still has the T1 entry) | integration's dict plus `cones_exempt`; the T1 entry stays removed |
| auto-merged: `build_track.py` (passes `cones_exempt` to the gates), `build_scenery.py`, `src/app/scenery.ts` (paint-line gloss), `poses.ts`, `boundary_sheets.py`, `camera_walk.ts`, `SKILL.md`, Buttonwillow's and the template config | - | round 11 | each change set identical to buttonwillow's own |

`public/tracks/buttonwillow/` is byte-identical to buttonwillow's (`git diff --quiet de8c9b7 -- public/tracks/buttonwillow`).

## Checks on the refreshed tree (a11a8f1)

- `npm run build` (tsc on tsconfig.build.json + vite): clean, built (one 1.26 MB chunk).
- `npx vitest run`: 62 files, **510 passed**, 0 failed, 0 expected failures. Reconciled: integration's 505, + 2 (round
  14B `offcourse.test.ts`), + 4 (round 11: one runoff-pose test, three cone-gate tests), - 1 (round 14B removed the
  T7-approach tyre run, and `tyrewall.test.ts` runs one case per tyre run). track-pipeline's expected fail (the Sonoma
  kerb wheel-lift `it.fails`) is an advisory report here by the owner's rule of 21 Oct, as in the dry run.
- Python pipeline tests (`uv run --python 3.12 ... python -I -m pytest tools/track -q`): **79 passed, 3 skipped**.
- Stage-3 gate CLI (`run_gates.ts`), read-only gate configs from the two worktrees:

| gate | Sonoma 14B (track-pipeline's `sonoma_r14b` config) | Sonoma 14B (that config + the merged `cones_exempt`) | Buttonwillow r11 (`bw_r11` config) | Buttonwillow r10 package, same code (for comparison) |
|---|---|---|---|---|
| containment | ok, 0 escapes | ok | ok, 0 escapes, 3166 allowed | ok |
| pit connectivity, signs, tyre facings | ok | ok | ok | ok |
| wall ends | ok (41, 1 known exposure s 736 L) | ok | **FAIL**: 3 exposed (tyre surrounds of the stations at s 826 R, 1184 R; T3 station mound tyres s 1020 R) | FAIL (same 3) |
| wall tops, wall-tyre joins, tyre faces | ok | ok | ok | ok |
| run gaps | ok (6 openings) | ok | **FAIL**: 2 holes, the pit-lane paddock-side wall between its west / tower / east runs (s 4657 L 12.5 m, s 47 L 14.5 m) | FAIL (same 2) |
| terrain override (joins / smoothness / kerbs) | ok (0.0056 m / 1.63 deg; 0.0099 m; 0.71 deg) | ok | n/a (no region) | n/a |
| ground marks on surface | ok (0.008 m) | ok | **FAIL**: 1680 of 19202 vertices off (-0.063 .. 0.027 m against 0 .. 0.01), mostly the redrawn crack seal | FAIL (250 off) |
| cones off the surface | **FAIL**: 8 cones (7 on the pit-in double white line, not exempt in that config; 1 on the owner's T1 mouth arc) | **FAIL**: 1 cone, the owner's T1 paddock-side mouth arc, s 173.9 R, 0.26 m inside the round-14B edge (limit 0.15) | ok (264 cones, 0 inside) | FAIL (20, the round-10 finding) |

  The Buttonwillow failures are not caused by the merge: the round-10 package fails the same three gates with the same
  code. Those gates (wall ends widened for Sonoma, run gaps of round 13, ground marks of round 14B) are track-pipeline's,
  and Buttonwillow was never built with them. The Sonoma cone failure is new with this pair: buttonwillow's cone gate was
  checked on the round-14A Sonoma package, and round 14B's T1 refit put the edge 0.26 m past one cone of the owner's T1
  mouth line. Neither package is changed here (no package changes beyond the merge); both go to the coordinator.

## AI reruns and calibration on the refreshed tree

Details in `tools/race/AI_READINESS.md` section 5.
- `wall_phantoms.ts`: 0 segments reach the racing line on Sonoma 14B (the T7 tyre run of 14A is gone), Buttonwillow
  and Laguna.
- Sonoma 14B, seeds 1-2, kept knobs (on the 14A calibration): contacts 0.046 per car-lap (14A 0.080), 0 at T7, four-off
  0.011; T9A s 3000-3070 is the top place (13 of 41 contacts, 1 four-off). laneMargin 0.7: 0.039 / 0.029, not kept.
- Buttonwillow r11 seed 1: 0.019 contacts, 0.019 four-off, 756 s; the round-10 package on the merged code reproduces the
  round-10 row (0.025 / 0.033 / 11 recoveries), so the change is round 11's kerbs, not the merge.
- Laguna seed 1: bit-identical to the pre-merge code (2 contacts, 17 four-offs, 620.11 s, same order and events).
- Sonoma calibration on rev 6b766e08d6: Probe 143.42 s at scale 1 (141.73), scales +2.0 % median, 5 fits outside 0.5 % in
  2 cars (17 in 8 before). Still to do: the Sonoma seed 1-2 self-play on the new scales, and a vitest / build pass after
  this commit if the coordinator wants one (pace.json only).
