# Buttonwillow round 10, stages 2 and 3: ledger (23 Oct 2026)

The owner approved the round-10 outline on his decisions page (23 Oct 2026, 18:32-18:35 PDT), with four decisions. This
round carries them out: the gate rework, stage 1 again, stage 2, stage 3 and the publish to `public/tracks/buttonwillow`.
It stops before the preview and the judge.

Builds: `tools/track/out/bw_r10s1` (stage 1, 2 and 3; published), geometry config **4cad7f3fe9287d8b**. The approved
outline is `out/bw_r10` (config 41a97d3d60d1b0e3, track.json 65196e4532446f16), with a copy of its track.json in
`out/bw_r10_approved/`. Logs are in the round's scratch.

## The owner's decisions and what each became

| # | decision | what it became | evidence / numbers |
|---|---|---|---|
| 1 | The round-10 outline is right. The edges may not move except for the kerb additions; prove it with rms < 0.02 m outside the new kerb zones. | The edges are unchanged except at the five new kerb zones and their ramps. Outside those zones (each zone plus its ramp of ceil(0.9 / 0.08) + 1 = 13 stations either side), the new edges sit **0.0136 m (left) / 0.0113 m (right) rms** from the approved ones. That is the exact point-to-segment distance against the approved edge polylines (90.5 % / 94.0 % of stations within 0.02 m). **What moved** is listed under "What moved" below. | `/tmp`-style comparison script on track.json, approved vs new. A control build with the reworked gates and **without** the five zones reproduces the approved track.json byte for byte (65196e4532446f16) and the approved heightfield (cmp), so the gate rework itself moves nothing. |
| 2 | No cones at the pit entry (left, stations 4280-4314 in mouths.json, 4270-4304 in the config). Every other red across a mouth keeps its cone line, plus the T2 exception line at the kink of his green near s 641. The hairpin runoff at s 600-650 stays open. | The new `scenery.owner_mouth_cones` places **19 cone lines** on his red, from `owner_mouths_r10`, which every mouth with cones=True reads: 18 'red across' and the T2 kink line. The pit entry gets none, and `gates.allowed` now lists the pit lane across his pit-entry red (cars drive through it). The closed-road rule cones at two of those mouths are switched off because his line replaces them: Atlantic s 170 R and the 34351015 crossover s 1824 R. The cone_lines_declared rows are onboard observations, so they stay. The T2 runoff zone (s 606-641 left) is unchanged and open. | Stage-3 log: "owner mouth cones: 19 lines"; "owner mouth left 4270-4304 (red across): no cones". The containment escape at the pit entry (left s 4286, 1 ray) is closed by the allowed entry. Stills: `pit_entry_s4290`, `hairpin_s625`, `t2_exception_s641`, `cones_dogleg_left_s1990`, `cones_dragstrip_right_s2552`. |
| 3 | His red wins over the gates where he drew both edges; the old gates stay where no owner edge exists. | **`edge_gate.OWNER_REF`** (see "The gate rework"). On his stations, each edge must lie within 0.40 m of his red at every station, outside his mouth segments ±12 stations. The width must lie within 0.40 m of the width between his lines. The 20-80 m band is measured on (fit − his red), within 0.30 m. The rolling-100 waviness may not exceed his red's own. The owner-edge max (0.5 m) leaves out the mouth segments ±12. Everywhere else the original code runs (owner=None). Laguna and Sonoma declare no owner edges or mouths. | `test_owner_reference.py`: 7 tests, including the detected-edge fixture (original result, metric for metric). Laguna / Sonoma repro and stage 3 below. |
| 4 | Kerbs: the onboard wins. Add the five runs at the standard width outside his red. The seven capture-only bands stay unplaced. The 34 existing strips stay. | Five `OWNER_KERBS_R10` zones at the scenery.kerb width 0.9 m: left 538-560, 2837-2843, 3458-3505; right 1161-1182, 1294-1299 (stations_ref). On this package they are left 537-559, 2853-2859, 3475-3522 and right 1172-1194, 1307-1312. Their five `kerbs_declared` runs are now **zone strips** (`zone`, off −0.45 m, width 0.9 m) between his red and the edge; their capture block lines are no longer used. All 39 runs stay (34 + 5). The seven capture-only bands (left 1956-1961, 3105-3111; right 392-399, 1984-2005, 3672-3678, 3761-3772, 4410-4417) are not placed. | The edges moved out by a median of 0.79-0.92 m in the five zones (table below). The kerb traversal gate passes (vitest kerbgate: no roll past 15°, no rollover; 117 Buttonwillow passes, 61 with a wheel lift, advisory). Stills: `kerb_new_left_s3490`, `kerb_new_right_s1180`. |

## The gate rework (decision 3)

`tools/track/edge_gate.py`: `OWNER_REF`, `owner_reference`, `owner_station_gate`, `owner_waviness`, and
`width_gates(owner=...)`. `tools/track/build_track.py`: `owner_ref`, the owner-edge max, the per-station gate, and the
fit waviness. The new config key is `spline.owner_mouths = 'owner/r10/mouths.json'`, a stage-1 key whose file content
enters the geometry hash.

- **Which stations.** Each per-edge gate (his-red tolerance, 20-80 m band, rolling waviness) runs on the stations where
  he drew that edge. The width gate runs where he drew both edges. Gaps of up to 5 stations are interpolated. On each
  side, the stations of his 'red across' mouth segments are left out, found by world position on the current centre and
  widened by 12 stations at each end.
- **The 12-station allowance is derived, not tuned.** It is half the support of one cubic B-spline basis function at the
  fit's 6-station knots (4 knot intervals = 24 stations). That is how far the fit cuts across a corner in his red. At
  the mouth corners his red bulges up to 1 m into the mouth before it crosses (right 2528-2537: 7.34 m against the fit's
  6.64 m), and on the approved fit every exceedance lay 1-12 stations past a segment end.
- **The 0.40 m tolerance comes from his stroke accuracy.** Where two of his round-10 windows overlap, his two drawings
  of one edge differ by more than 0.3 m at 756 of 1677 left stations and 639 of 1793 right stations, by a median of
  0.49 / 0.46 m where they do (`owner/r10/merged_report.json`, compare/owner_merge.py tol 0.3). A fit held to 0.40 m of
  the cross-faded line therefore sits inside his own repeatability. The 0.25 m first proposed holds at 99.7 % of these
  stations, but the approved fit has stations at 0.25-0.38 m that may not move (decision 1), so 0.25 m at every station
  would fail the outline he approved. The stations over 0.25 m are listed below for his outline page. The orchestrator
  accepted this on these conditions (message of 23 Oct 2026).
- **Waviness.** The 20-80 m band of (fit offset − his offset) must stay within 0.30 m, the WIDTH wave, unchanged. The
  rolling-100 fit waviness is held to max(0.04 m, his red's own rolling rms) and the peak to max(0.10 m, his red's
  largest residual in the same window): the fit may add no wave his red does not have. Measured on (fit − red) alone,
  it would gate the wiggle of his stroke, which the smoother fit does not follow (0.08 m on the approved fit).
- **Nothing loosened.** The per-window owner-edge gate keeps ≥ 90 % within 0.25 m and max 0.5 m, its max now taken
  outside the mouth segments ±12 as decided. The new 0.40 m per-station cap is tighter than that 0.5 m max.
  `gate.owner_ref_tol` can only tighten. With owner=None, `width_gates` runs the original code path.

### Stations over 0.25 m from his red (final package, for the outline page)

These are package stations of `public/tracks/buttonwillow` (n 4708, spacing 0.99813 m); values are fit − his red (m).
His red includes the kerb shifts.

- **Left edge (11 stations):** 548 +0.273, 572 +0.258, 581 −0.308, 1304 −0.264, 1305 −0.352, 1306 −0.274, 1645 −0.291,
  1646 −0.341, 1858 −0.333, 1859 −0.381, 1860 −0.271.
- **Right edge (5 stations):** 269 −0.251, 3467 +0.267, 4387 +0.252, 4393 −0.328, 4394 −0.255.
- **Width (22 stations):** 548 +0.308, 549 +0.384, 550 +0.264, 580 −0.257, 581 −0.324, 606 +0.251, 615 −0.300,
  616 −0.359, 617 −0.309, 1170 −0.264, 1293 +0.252, 1305 −0.321, 1306 −0.350, 1307 −0.286, 1640 +0.250, 2020 +0.266,
  2021 +0.264, 3388 +0.274, 3896 +0.276, 4387 +0.299, 4388 +0.287, 4428 +0.310.

On the approved fit, with the same rule, the counts were 12 edge and 21 width stations (max 0.35 / 0.36 m). The new
kerb zones at left 537-559 and right 1172-1194 / 1307-1312 add the 548-550, 1170 and 1293 entries: those stations sit on
the zones' ramps.

## Gate numbers, before and after

Stage 1 (geometry). "Before" is the approved run (`edges_r10/run1.log`, written with --write-on-fail); "after" is this
round's run, which passed without --write-on-fail.

| gate | before (approved, old gates) | after (this round) |
|---|---|---|
| owner edge left 0-2359 / right 0-2359 / left 2360-4707 / right 2360-4707 | FAIL max 0.586 / FAIL 0.664 / ok 0.236 / FAIL 0.700 (share 99.0 / 99.2 / 100.0 / 99.6 %) | ok: max outside the mouth segments ±12 0.381 / 0.251 / 0.236 / 0.328 (with them 0.584 / 0.667 / 0.236 / 0.700); share 98.8 / 99.2 / 100.0 / 99.6 % |
| owner reference (new) | n/a | ok: left max 0.381 at 1859 (4267 stations), right 0.328 at 4393 (4168) ≤ 0.40 |
| fit left / right waviness | FAIL rolling rms 0.050 / 0.057, peak 0.115 / 0.137 | ok: on his stations rms 0.051 / 0.057 against his red's own (max 0.098 / 0.104), peak 0.114 / 0.137; elsewhere rms 0.018 / 0.038, peak 0.035 / 0.069 |
| width consistency | FAIL max 2.321 m at 342, 1599 of 3185 stations over 0.3 | ok: max |fit width − his width| 0.384 at 549 (3802 stations); no station outside his both-edge stretches and the junction ranges |
| edge waviness left / right | FAIL 0.345 at 3883 / 0.332 at 1635 | ok: band of (fit − red) 0.136 at 559 / 0.120 at 4395 (p95 0.061 / 0.061) |
| fit observations within 0.25 m | ok 98.8 / 99.4 % | ok 98.7 / 99.4 % |
| coverage / longest gap / kink | ok 99 % / 11, 1 st / 0.34, 0.38 °/st | ok 99 % / 11, 1 st / 0.34, 0.37 °/st |
| edge gate rms / step | ok 0.065 / 0.066 m, step 0.040 / 0.048 | ok 0.066 / 0.066 m, step 0.042 / 0.048 |
| world continuity | ok 0.0073 / 0.0092 m | ok 0.0076 / 0.0073 m |
| profile / edge jumps / cross slope | ok 0.017 / 0.103, 0.114 / 9.8 % | ok 0.017 / 0.104, 0.120 / 9.9 % |
| lap length | 4699.87 m | 4699.19 m (n 4708) |

Stage 2 (ghosts, no logger): the pure minimum-curvature line within the edges less 1.0 m. The kerb strips lie inside the
edges, so they are racing surface; the config's kerb margin is the 1.0 m default, the same as the margin. Offset range
−5.47..+5.51 m. Line inside the edges: min clearance 1.00 m. Curvature: sum k² 0.1526 against the centre's 0.2318.

Stage 3 (scenery, every gate required; it passed and was published with `--publish --overwrite-package`):

| gate | result |
|---|---|
| edge (with walls), world continuity, profile | ok (as stage 1) |
| barrier gaps | ok, min 4.17 m over 17 runs |
| containment | ok: 14124 rays, 0 escapes, 3493 onto allowed runoff, 78 pit-lane junction hits |
| pit connectivity | ok: pit box → exit → track 388 m, track → entry → box 382 m; lane paths 738 stations, 0 obstacles |
| signs / wall ends / tyre facings | ok: 16 / 1 of 1 protected / 0 |
| coverage | ok: 87 rows, 171 objects, MISSING 0, UNSUPPORTED 0, 5 dispositions placed |
| pit lane | ok: 7 wall rows |
| kerb traversal (vitest) | ok: no roll past 15°, no rollover (Laguna, Sonoma, Buttonwillow) |
| kerb run step | 0.000 m on every run (strips flush to the edge, below) |

The stage-3 post steps (scenery_post) ran inside the stage.

The in-page continuity scan (`scan_surfaces.js`, through a headless CDP runner) found 22024 flags on this package
against 20895 on the round-8 package (the same scan, same page). Most are the raised kerbs over the ribbon:
track:road above the surface by more than 5 cm 2795 (round 8: 3091), track:shoulder below by more than 5 cm 15 (43),
track:road below by more than 5 cm 86 (44, at the T1 kerb 286-323). New surface kinks: L4 at 4173 / 4187 (0.244), R9
at 1178 / 1685 (0.148), L1 at 762 (0.084). They are listed here and not fixed in this round.

## What moved, and what changed in the package

**Edges, outside the five zones** (rms 0.0136 / 0.0113 m): the stations that moved more than 0.05 m are these. Each
lies within a ramp or a spline knot span of a new zone, or in the pit-out run, where his left red is absent and the
evidence fit couples to the centre.

- Left: 391-410 (0.089), 522-523 (0.081), 573 (0.081), 1195-1202 (0.059), 1523-1535 (0.076), 2838-2839 (0.089), 2873
  (0.063), 2880-2881 (0.052), 2995-3000 (0.056), 3020-3021 (0.051), 3323-3327 (0.053), 3389-3400 (0.068), 3460-3461
  (0.097), 3536-3537 (0.083).
- Right: 1157-1158 (0.089), 1208-1209 (0.102), 1292-1293 (0.093), 1326 (0.081), 1333-1336 (0.056), 1849-1866 (0.097),
  2351-2365 (0.077).

**Edges, in the five zones** (moved outward from the approved fit by the 0.9 m strip):

| zone (package stations) | median | max |
|---|---|---|
| left 537-559 | 0.920 | 0.964 |
| left 2853-2859 | 0.795 | 0.812 |
| left 3475-3522 | 0.904 | 0.942 |
| right 1172-1194 | 0.910 | 0.961 |
| right 1307-1312 | 0.789 | 0.799 |

**Centre and length:** the centre is the midpoint of the edges, so it follows the zones (max 0.48 m at 3501, the left
3475-3522 zone). The lap is 4699.187 m (approved 4699.874 m; registry `length_m` 4703.806 m, round 8). Station 0 is
0.31 m from the timing line.

**Package against the round-8 package** (`compare/compare_packages.py`; matched 554, missing 45, extra 15, no height
differences):

| object | change |
|---|---|
| kerbs | 39 → 39, all matched, median offset 0.44 m. Every run is now **flush inside the edge**, off = −width/2, as the stage-1 zones define the strip: the band between his red and the band's outer limit, `kerb.flush_runs`. Each run's measured line sets its extent only. On the round-10 edges the round-5 block-line offsets ran up to 3.4 m outside the edge (left 1089-1116, a 0.21 m station step that failed the run gate) and +0.8 to +1.2 m outside at right 1868-1933, right 4321-4370 and left 1203-1272. Widths and colours are unchanged. |
| cone lines | 30 → 47: +19 on his red, −2 closed-road rule cones (Atlantic s 170 R, crossover s 1824 R), plus the existing declared rows. |
| closed roads | 23 → 22 parts. The outer T2 loop takes OSM 39224609 nodes 393994752-393994769 only: the last two nodes cross the hairpin onto the dirt inside it (w_s0625 on c20_s0700, no pavement), and that 16 m part met the round-10 right edge at s 571 (36 + 77 containment escapes). Ten roads take their paving edges from **his green** (`owner_green`, `edges_from_green`; at 20-295 of each road's points, logged per road; the paddock lanes at only 0-20 points, because his green barely reaches them). |
| paint lines | 407 → 257: the crack-seal marks inside the track polygon (579 candidates, 257 kept). The round-10 edges are narrower than round 8's (width median 11.6 m), so fewer measured marks lie inside. |
| paved areas, runoff zones | the same objects, moved with the edges (median 0.33 / 0.78 m). |
| walls, tyre walls, fence, stations, blocks, buildings, mast, pit lane | unchanged (0 m). |

`src/scoreboard/config.ts`: Buttonwillow `length_m` 4699.187 and `rev` 7acf260f50 (the registry test's fingerprint of
the published files), so the new package opens fresh boards. `PHYSICS_VERSION` is untouched (a per-track rev, as round 8
did). `src/app/changelog.ts` is not touched: one version per publish, and the preview is the orchestrator's step.

## What did not change

- Laguna and Sonoma: `git diff --stat` is empty for `public/tracks/laguna_seca` and `public/tracks/sonoma`.
- Acceptance 6 reproductions:
  - Sonoma stage 1 exits 0, and track.json (9d7d52be96485e08) and heightfield.bin are byte-identical to the published files.
  - Laguna stage 1 gives track.json d4e8634710813961 and a byte-identical heightfield.bin, failing `edge gate left` with
    0.105 m at station 46, as documented.
- Stage 3 with this round's builder:
  - Sonoma's scenery.json, far_heightfield.bin, far_ortho.jpg and ortho.jpg are byte-identical to the published package.
  - Laguna's stage 3 on its repro geometry is byte-identical to the HEAD (f9c7aec) builder's stage 3 on the same geometry.
- Walls, barriers, structures, buildings, trees, terraces, marshal posts, boards, the pit lane, the bridge-free
  layout: no change.

## Stills (`compare/pose_walk.ts`, eye 1.3 m, 4 m ahead of the car; `stills/*_r10.jpg`, local)

| still | station | what it shows |
|---|---|---|
| pit_entry_s4290 | 30 m before s 4290, turned 25° left | the pit entry open on the left, no cones; the T11 station |
| hairpin_s625 | 30 m before s 625 | the T2 hairpin; the runoff on the left open; the kink cone line beyond |
| t2_exception_s641 | 25 m before s 641, turned 30° left | the T2 exception cone line on his green's kink, the runoff open before it |
| kerb_new_left_s3490 | 25 m before s 3490, turned 15° left | the new left strip 3475-3522 (red / white / blue) between his red and the edge |
| kerb_new_right_s1180 | 25 m before s 1180, turned 30° right | the new right strip 1172-1194 at T4 |
| cones_dogleg_left_s1990 | 35 m before s 1990, turned 20° left | the Dog Leg mouth's cone line on his red |
| cones_dragstrip_right_s2552 | 35 m before s 2552, turned 20° right | the drag-strip mouth's cone line on his red |

Hood sheet (SKILL 1.10): `hood/sim/fwd_s*.jpg`, 63 stills every 75 m (`camera_walk.ts --no-rows --back-step 0
--pit-step 0 --no-runoff --step 75`), local. The builder looked at it at contact-sheet size and saw no edge wave or
missing surface. It is for the orchestrator's review.

## Open, for the orchestrator and the owner

1. The 0.40 m tolerance and the 12-station corner allowance (above). The 16 edge and 22 width stations over 0.25 m are
   for his outline page.
2. Pacific mouth (right 4571-4599): judge r3 (4573 R EXTRA) had read the onboard t002 / t150 as single cones, not a
   line. His red across it now carries a cone line, per his decision 2, and the two single cones stay as declared.
3. The new in-page surface kinks (L4 4173 / 4187, R9 1178 / 1685, L1 762) and the raised-kerb ribbon flags, which are
   comparable to round 8.
4. The 34 strips are now flush inside the edge (a lateral change, not a new placement). The colours are unchanged; the
   judge should look at the T4 run (left 1089-1116), whose capture block line diverged from his red.
5. Closed roads from his green: the paddock lanes barely take it (0-20 points per part); their edges stay on the NAIP /
   OSM half-width there.
6. Not done here, per the brief: the preview, the judge (JUDGE.md sheets), the boundary audit (4.1b), stage 5 and
   self-play.
