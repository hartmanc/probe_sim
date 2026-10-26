# Mid-Ohio edge review — round 3 (narrowed geometry checkpoint)

Opus 5.5 takeover of the Codex build, 26 Oct 2026, branch `mid-ohio`. Scope of this round: the owner's round-2 marks
applied to the pit straight and its transitions, the held course proved, the nominal-length question, the T4 evidence
note, and a changed-region checkpoint page. It STOPS here for the owner's review (SKILL stage 1, "Owner checkpoint after
edge detection", item 4). Nothing downstream (stage 0 inventory, racing line, scenery, drives, judges, registry, field,
AI, preview) was started.

## History

- Round 1 (14976d4): source-derived geometry, outer-kerb convention, `edges_r1/`, `review_r1/` (port 5197).
- Round 2 (4937ab5, e217c6b, 0deae2e): inside-kerb convention (`spline.kerb_edge='inner'`), `edges_r2/`, `review_r2/`
  (port 5198), round-1 marks carried over (`round2.md`).
- Owner review of round 2 (ff01b8d, `owner_review_r2/`): "Other than the pit straight, and the transitions onto and off
  it, the fits were good." 13 windows, 46 red and 50 green strokes.
- Round 3 (this file): the local refit below. Package `tools/track/out/mid_ohio_r3/` (local, DIAGNOSTIC: written with
  `--write-on-fail`, see "Length"). Page `owner_review_r3/` (new; no earlier review directory touched).

## What was applied

1. **His vectors, not his pixels.** `compare/owner_edges.py --by-stroke` on each window of
   `owner_review_r2/edge-marks.json` (sha256 fa809758…, unchanged), frames from `owner_review_r2/frames.json` (each
   window's `center_enu` checked equal to the round-2 package's centre at its station: 0.000 m for all 13), projected on
   `tools/track/out/mid_ohio_r2`, into `tracks/mid_ohio/owner/r2/<window>.json` (committed; raw, every stroke).
   - Frame convention checked: the drawing page records continuous canvas coordinates (image pixel i spans [i, i+1);
     `edge_draw_page.py` `pos()`), which is how `capwin.py` draws (`(x - x0) / mpp`) and how `edge_mark_transfer.cjs`
     projects (`x0 + p * mpp`). `owner_edges.py --by-stroke` added half a pixel (its PNG-path convention): a 6 cm bias at
     0.12 m/px. New opt-in flag `--vector-origin continuous` (default unchanged, so Sonoma's files reproduce), with a test
     (`test_owner_edges.py::test_by_stroke_vector_origin`). The `--frames` reader also takes the outline windows' own schema
     (`center_enu`, `half`).
   - No red line ran across the road (0 across segments at 35 deg in every window). His 2.2 m inward lines at the pit
     entry mouth (left, s ~3453-3480) and before the bridge (right, s ~180-200) are longitudinal course edges.
   - Green strokes (1223 points after the 1 m thinning) are kept in each window file and in `merged.json`
     (`green_enu_xy`) as paved-boundary evidence for the scenery stage; the fit does not read them; nothing is drawn.
2. **Overlaps reconciled** (`r3/overlaps.py` → `r3/overlaps.json`; close-ups `r3/overlap_sheet.py`, local PNGs): every
   station / side seen by two windows, compared with each other and with the round-2 fit's capture readings (paint and
   kerb rows of `work/fit_assoc_<side>.json`). Nine runs differ by more than 0.3 m (REVIEW.txt's 0.68 m worst is right
   s 220). Dispositions (`tracks/mid_ohio/owner/r2/merge.sh`, `compare/owner_merge.py --drop`, a new opt-in flag; the raw
   window files keep every vector):

   | # | side, stations (r2) | windows | evidence | kept | left out |
   |---|---|---|---|---|---|
   | D1 | right 186-243 | close_s0220 vs w_s0250 (0.67 m at 220); w_s0125 vs w_s0250 at 186-200 | close_s0220 0.40 m from the paint readings vs 0.89 m; close-up: close_s0220 on the white line along the wall, w_s0250 0.4-0.7 m inside on plain asphalt; close_s0220 is the dated, finer (0.06 m/px) review; w_s0125 agrees with it (<= 0.16 m) | close_s0220 (+ w_s0125) | w_s0250 |
   | D2 | left 189-200 | w_s0125 vs w_s0250 (0.45 m) | w_s0250 0.38 m from paint vs 0.76 m; s 200 is w_s0125's window border (75 m from its centre); close_s0220 lies within 0.25 m of both | w_s0250 + close_s0220 | w_s0125 |
   | D3a | left 274-295 | w_s0250 vs close_s0320 / w_s0375 (0.48 m) | close_s0320 0.28 m from the kerb / paint readings vs 0.65 m | close_s0320, w_s0375 | w_s0250 |
   | D3b | left 311-323 | w_s0375 vs close_s0320 (0.33 m) | close_s0320 0.09 m vs 0.23 m (T1 inside kerb) | close_s0320 | w_s0375 |
   | D4 | right 339-340 | w_s0375 vs close_s0320 (0.35 m) | 0.02 m vs 0.34 m | close_s0320 | w_s0375 |
   | D5 | right 427-475 | w_s0500 vs w_s0375 (0.49 m) | w_s0500's right red is ONE 3-point Arc over 150 m (control points 426 / 480 / 576 within 0.04-0.35 m of the kerb line); between them the circle bows up to 0.67 m inside the yellow T1-exit kerb's asphalt-side limit, which the capture shows straight (close-up E) and w_s0375 traces (kerb readings 0.05 m vs 0.42 m). The bow is the arc's interpolation, not a line he placed. Over 452-475 no other window drew: the capture's kerb / paint readings stand there | w_s0375 to 451; captures 452-475; w_s0500 from 476 | w_s0500 427-475 |
   | D6 | left 3519-3538, right 3519-3524 | w_s0000 vs w_s3500 (0.41 / 0.32 m) | w_s0000's two-click straight ends at its window border (s 3522); w_s3500 is interior there and 0.09 m from the paint vs 0.44 m; the two cross-fade over 3539-3575 (within 0.3 m) | w_s3500 | w_s0000 (there only) |
   | D7 | right 3431-3443 | w_s3500 vs w_s3375 (0.61 m at 3437) | close-up F: w_s3500 runs 0.3-0.6 m outside the white edge line onto the grass; w_s3375 on the line's asphalt side (0.21 m vs 0.41 m). The paint overrides REVIEW.txt's save-order clue here | w_s3375 | w_s3500 |
   | – | right 268 | close_s0320 vs w_s0250 (0.33 m) | close_s0320's reading is its window border (merge weight 1.0 vs 55.5): the merge follows w_s0250 | weighted | none |

   Merged (`owner/r2/merged.json`): left 712 stations, right 722; no remaining spread over 0.3 m except the weighted
   border reading at right 268. No owner red on left 363-390 and right 452-475 (the captures stand there).
3. **Local refit** (config `centre.local` window 3395..610 through S/F, blend 15, `restation 'index'`, `refit_final`,
   `centre_smooth 1.0`; `spline.owner_edges` one entry, `local=True`, lo 3425 / hi 576, `chains=False`,
   `reach='drawn'`, `project='foot'`; `spline.owner_measure 'foot'`). The global fit converges first with no other
   key changed (round 2's geometry), then only the window is refitted. No builder code changed in this round.

## Held course (round 2 vs round 3)

`r3/held_edges.py`: each round-3 point's distance to the round-2 polyline of the same kind (densified to 2 cm), by
round-2 station region.

| polyline | region (round-2 stations) | points | max (m) | RMS (m) | p99 (m) |
|---|---|---|---|---|---|
| left | outside 611..3394 | 2784 | 0.0100 | 0.0061 | 0.0098 |
| left | blend 3395..3409, 596..610 | 30 | 0.0165 | 0.0095 | 0.0164 |
| left | window interior 3410..595 | 781 | 2.3446 | 0.7049 | 2.2832 |
| right | outside 611..3394 | 2784 | 0.0100 | 0.0056 | 0.0098 |
| right | blend 3395..3409, 596..610 | 30 | 0.0132 | 0.0087 | 0.0132 |
| right | window interior 3410..595 | 781 | 2.4680 | 0.4902 | 2.3752 |
| center | outside 611..3394 | 2784 | 0.0099 | 0.0057 | 0.0097 |
| center | blend 3395..3409, 596..610 | 30 | 0.0213 | 0.0104 | 0.0207 |
| center | window interior 3410..595 | 781 | 1.0606 | 0.3235 | 1.0170 |

Outside the window the accepted course is held to 1.0 cm max (6 mm RMS; the package stores mm). Station count 3595
unchanged; lap 3597.185 → 3597.492 m.

Section widths (p5 / median / p95, m), round 2 → round 3: T13 exit / pit entry 3395-3480 11.88/13.12/15.41 →
11.89/12.43/14.67; pit straight W of S/F 12.21/12.67/13.52 → 12.07/12.27/12.58; E of S/F 12.02/12.22/14.20 →
11.61/11.72/12.00; bridge approach 12.91/13.25/15.31 → 11.77/12.23/12.44; T1 12.27/12.84/14.84 → 11.84/12.58/13.27;
T1 exit 11.79/12.14/14.62 → 11.81/12.07/13.92 (published 40 ft = 12.19 m, advisory).

Where the round-3 fit still differs from a capture kerb / paint reading by more than 0.3 m inside the window (no owner
reading there): left 365 (+0.36 m) and 373 (-0.36 m), painted, inside his undrawn left 363-390; right 458 (+0.49 m),
the yellow kerb's end, inside D5's undrawn 452-475.

## Gates and tests (round 3)

- Geometry stage (`build_track.py --stage geometry --out tools/track/out/mid_ohio_r3`): every check ok except
  **lap length FAIL** (3597.49 m vs 3633.934, -1.003 %). Owner-edge gates: left 99.6 % within 0.25 m of his line, max
  0.356 m; right 100.0 %, max 0.154 m (>= 90 %, <= 0.5 m). Fit, coverage, waviness, kink, edge gate (0.023 / 0.023 m
  rms), world continuity (0.0050 / 0.0073 m), profile gate (0.021 m), cross slope (11.6 % max), edge jumps
  (0.083 / 0.084 m) all ok. Advisory exit overshoot at T1 +2.19 m (s 392; also in round 2). Rebuilt with
  `--write-on-fail` for this page: identical gate lines. The package is diagnostic, not accepted.
- `edge_gate.py --track tools/track/out/mid_ohio_r3 --config mid_ohio`: edge gate left / right and profile gate ok.
- Python: the focused set (`test_yellow_kerb.py`, `test_profile_gap.py`, `test_pit_merge.py`) 15 passed; every
  `test_*.py` under `tools/track` (21 files) 124 passed. Node: `test_edge_mark_transfer.cjs` 4 passed.
- Sonoma / Laguna reproductions: not needed for this round (no builder file changed; the two compare tools changed
  only behind new flags). Still required before any merge (SKILL Acceptance 6).

## Length (the nominal gate)

Measured (`r3/length_check.py`): built centre 3597.5 m; left (outside, cw) edge 3635.6 m; right edge 3560.3 m; the
raw OSM loop of the six config ways 3620.2 m (the smoothed loop 3622.95 m, manifest.md). Per section the built centre
runs 0.5-3.7 m shorter than OSM almost everywhere (sum -22.7 m), spread over every section, not one piece: OSM's
hand-traced nodes wander and run wide in corners, while the built centre is the midpoint of edges fitted to the paint
(painted-midpoint residual 0.03 m rms).

The official figure: 2.258 mi, 13 turns, is the published length of exactly this layout (the 1989-90 "straight option
between Turn 1 and the Keyhole" that skips the chicane; operator, midohio.com news 1084; Wikipedia; IMSA's track page).
No source states the line it is measured on. The same sources give the chicane course as 2.400 mi, 228.5 m longer; OSM's
chicane way (444205376) is 30.0 m longer than the straight option it replaces (223.7 vs 193.7 m). The published pair is
therefore not a survey of today's centreline. Laguna (official 3602, built 3588, -0.39 %) and Sonoma (official_m 4088
derived from the 2.52 mi figure plus the OSM length of the T7a piece the Lemons course adds) both had the official
figure on their own layout; Buttonwillow set `official_m=None` because no published figure is for its Lemons loop
(built centre checked against OSM within 1 % in its manifest). Mid-Ohio's built centre is -0.63 % against OSM.

Finding: the evidence cannot settle it. The course is not short by a missing piece (the loop is the one the figure
names); the 1.003 % is the published figure's own measure, which no source states; the outside edge happens to measure
3635.6 m (+0.05 %), but no source says the figure is taken there, so that is not a citation. Nothing was changed:
`official_m` stays 3633.934, the tolerance stays 1 %, the course is not stretched. A question for the owner (below).
One more measure is available next run without new sources: the N837 onboard shows a Catalyst speed readout (Buttonwillow's
speed-integrated lap length method).

## T4 evidence note (2024 reconstruction)

- Operator (midohio.com news 1084, 19 Dec 2024): Kokosing, 14 Oct - 8 Nov 2024. "Turn 4's original footprint was
  preserved with the existing apex curbing kept in place at driver's right." "Its banking was reduced from 4 to 2
  degrees by removing 520 feet of track surface and excavating up to 18 inches along the outside edge." New underdrains,
  base and asphalt "to match the surface repavement completed in October 2023". "Both sides of the track were regraded
  starting 400 feet before the turn." Run-off stripped, raised with fill and 500 concrete blocks, regravelled; access
  roads on the back hillside; new guardrail in the T4 area through the Esses.
- The 2019 lidar profile at T4 (round 3 package = round 2 there, held): bank toward the inside (right) rises from 0 at
  s ~1865 to 3.9-4.4 deg over s ~1950-1975 (apex s 1961) and back to 0 by s ~2005; the operator's "4 degrees" is the
  pre-2024 state, so the survey is exactly what was rebuilt.
- Consistency of the operator's numbers: at 12.19 m (40 ft) width, rotating the section about its inside edge from
  4 to 2 deg lowers the outside edge by 12.19 × (tan 4° - tan 2°) = 0.427 m (16.8 in); the measured 4.4 deg peak gives
  0.47 m (18.4 in). Both agree with "excavating up to 18 inches along the outside edge" with the inside apex held.
- Onboard checks: N837 (15 Apr 2026, post-rebuild) frames t62-64, 66-69 (`inventory/frames_t4_N837`, local; t65 is a
  player overlay): one uniform fresh surface through T4 with no patch seam, grass run-off on the outside, the red barrier
  line beyond it, T5's red/white kerbs at t66-67. A hood camera cannot separate a 2 deg bank from the car's roll, so the
  frames do not measure the bank. The owner's IndyCar sources (2026 onboard compilation 9Drr1VkE1_U, segments start in
  Thunder Valley; 2025 360° lap e25u_vjn1uM) are recorded in sources.json; the sideways view through T4 from the 360°
  lap is the right check and needs the equirectangular reader of the next (stage-0) run. Not surveyed in this round.
- **Proposed rule (for approval, NOT applied):** a `repave_fixes`-style section rule over the operator's 520 ft
  (158.5 m) centred on the measured T4 bank peak (s ~1882-2040, to be placed from the 360° lap's sideways view): keep
  each station's inside (right) edge height and the centreline's longitudinal profile at the inside edge, halve the
  measured cross-slope (4 → 2 deg is half), so the outside edge drops by up to ~0.43-0.47 m; smoothstep transitions to
  the measured profile over the 400 ft regraded approach; carried into the heightfield as the profile repairs are
  (lateral fade beyond the outside edge into the raised run-off, which the operator says was filled). All numbers from
  the operator; the onboard is the check. The heightfield is unchanged in this round. The T1 footbridge `profile_gaps`
  repair is unchanged (stations 218-248, max repair 3.263 m).

## Deferred, recorded so nothing is lost

- AI field (owner, 26 Oct 2026: after he accepts the track): Lemons 2026 "Mid-West Crisis" at Mid-Ohio, 11-12 Apr 2026,
  results https://24hoursoflemons.com/results-2/?id=439 (confirmed as the event's results page; full entrant list
  behind its "View Full Results" link), plus the owner's Probe #619. In sources.json `field_source`.
- Stage 0 next run: the 360° lap (equirectangular reader, both sides every 2 s, kerbs, walls, pit lane, buildings,
  heights; time-to-station from landmarks), the IndyCar compilation (per-segment anchors from Thunder Valley landmarks),
  the full N837 two-second inventory.
- Green strokes (owner/r2, merged.json `green_enu_xy`): pit-exit / apron paving and the unused chicane and crossover
  surfaces, for the scenery stage.

## Stage-1 step ledger (round 3)

| step | record |
|---|---|
| 1.1 loop | unchanged config loop ways; n 3595; station 0 0.16 m from the timing line (build log) |
| 1.2 registration | unchanged (common shift, round 1) |
| 1.3 centreline (no logger) | global fit as round 2; local refit 3395..610 (config `centre.local`) |
| 1.4 fitted edges, local change | `centre.local` + `spline.owner_edges` local; held-edge table above (1.0 cm) |
| 1.5 convention / owner checkpoint | inner-kerb convention kept; his red applied; page `owner_review_r3/` |
| 1.6 profile / heightfield | unchanged rules; T1 footbridge `profile_gaps` as before; T4 rule proposed, not applied |
| 1.7 corners | build log corners line (T1 R 69.3 m at s 357.2; others as round 2) |
| 1.8 roughness | profile gate 0.021 m; cross slope 11.6 % max |
| 1.9 edge gate | build log and `edge_gate.py` ok; owner-edge gates ok |
| 1.10 driver's-eye sheet | n/a: after the owner accepts this checkpoint (no downstream before it) |
| 1.11 derived data | n/a: no ghosts / scenery exist yet |
| 1.12 paved shoulders | n/a this round (scenery stage; green evidence kept) |
| 1.13 terrain override | n/a this round |
| lap length | FAIL -1.003 %, question to the owner |

## Owner checkpoint page

`owner_review_r3/src/` (13 window PNGs local, `index.html` captions, `frames.json`: s, station, half 40, mpp 0.06,
centre_enu, image_px 1333) → `owner_review_r3/page/` (`edge_draw_page.py --src ... --out ... --title "Mid-Ohio Edge
Strokes, Round 3" --intro ...`; `--intro` is a new optional flag). Windows in driving order: r3_s01_at3400,
r3_s02_at3470, r3_s03_at3540, r3_s04_at0000, r3_s05_at0070, r3_s06_at0140, r3_s07_at0210, r3_s08_at0280,
r3_s09_at0350, r3_s10_at0420, r3_s11_at0490, r3_s12_at0560, r3_s13_at0620. Red: round-3 left edge; magenta: right
edge; cyan band under them: his round-2 red as applied; white bars: window 3395 / 3410 / 595 / 610; yellow: ticks.
Renderer `r3/review_windows.py`. To be published by the orchestrator (capabilities db, files win/*).

## Questions for the owner

1. Length: keep the 2.258 mi (3633.934 m) gate and leave the package diagnostic until a source says how the figure is
   measured, or treat it as Buttonwillow was (published figure not a centreline survey; check the built centre against
   independent measures: OSM -0.63 %, and next run the Catalyst speed-integrated lap)? Matrix:

   | | keep 3633.934 m, 1 % gate | official_m None + OSM / speed check (Buttonwillow rule) | ask the operator how 2.258 mi is measured |
   |---|---|---|---|
   | gate today | fails by 0.003 % points | passes (-0.63 % vs OSM) | pending |
   | evidence basis | published figure, line unknown | two independent measures of this loop | would settle it |
   | geometry change | none | none | none |
   | risk | blocks downstream on a figure no source ties to a line | loses the published figure as a check | time |
2. D5: his round-2 arc on the T1 exit right (s 427-475) bows up to 0.67 m inside the yellow kerb; it was left out for
   the kerb line. Window r3_s10_at0420 shows both (cyan band vs magenta).
3. T4: approve the proposed bank-halving rule (operator numbers), to be placed with the 360° lap next run?
