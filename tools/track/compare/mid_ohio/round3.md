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
   | D5 (PROVISIONAL, for his approval) | right 427-475 | w_s0500 vs w_s0375 (0.49 m) | w_s0500's right red is ONE 3-point Arc over 150 m (control points 426 / 480 / 576 within 0.04-0.35 m of the kerb line); between them it bows up to 0.67 m inside the yellow T1-exit kerb's asphalt-side limit, which the capture shows straight (close-up E) and w_s0375 traces (kerb readings 0.05 m vs 0.42 m). The arc is his stroke; the image cannot establish whether the bow was intended. Over 452-475 it is his ONLY red, so setting it aside removes his constraint there and the capture readings set the edge; the replacement still misses a capture reading by 0.49 m at s 458 (the kerb's end). Asked on the page | w_s0375 to 451; captures 452-475; w_s0500 from 476 | w_s0500 427-475 |
   | D6 | left 3519-3538, right 3519-3524 | w_s0000 vs w_s3500 (0.41 / 0.32 m) | w_s0000's two-click straight ends at its window border (s 3522); w_s3500 is interior there and 0.09 m from the paint vs 0.44 m; the two cross-fade over 3539-3575 (within 0.3 m) | w_s3500 | w_s0000 (there only) |
   | D7 | right 3431-3443 | w_s3500 vs w_s3375 (0.61 m at 3437) | close-up F: w_s3500 runs 0.3-0.6 m outside the white edge line onto the grass; w_s3375 on the line's asphalt side (0.21 m vs 0.41 m). The paint overrides REVIEW.txt's save-order clue here | w_s3375 | w_s3500 |
   | – | right 268 | close_s0320 vs w_s0250 (0.33 m) | close_s0320's reading is its window border (merge weight 1.0 vs 55.5): the merge follows w_s0250 | weighted | none |

   Merged (`owner/r2/merged.json`): left 712 stations, right 722; no remaining spread over 0.3 m except the weighted
   border reading at right 268. No window has red on left 363-390; on right 452-475 his only red (the D5 arc) is set
   aside, provisionally. The capture readings set the edge on both.
3. **Local refit** (config `centre.local` window 3395..610 through S/F, blend 15, `restation 'index'`, `refit_final`,
   `centre_smooth 1.0`; `spline.owner_edges` one entry, `local=True`, lo 3425 / hi 576, `chains=False`,
   `reach='drawn'`, `project='foot'`; `spline.owner_measure 'foot'`). The global fit converges first with no other
   key changed (round 2's geometry), then only the window is refitted. No builder code changed in this round.

## Held course (round 2 vs round 3)

`r3/held_proof.py` (replaces the one-way `r3/held_edges.py` table after the Astra review: a point-to-sampled-curve
distance cannot show along-track movement or coverage, and its ~1 cm ceiling was the 2 cm sampling's half-spacing).
Window 3395..610 (blend 15) in each package's own stations.

**1. Bidirectional point-to-segment distance outside the window** (exact segment distance, both directions):

| polyline | direction | points | max (mm) | RMS (mm) | p99 (mm) |
|---|---|---|---|---|---|
| left | r3 -> r2 | 2784 | 1.2 | 0.4 | 0.9 |
| left | r2 -> r3 | 2784 | 5.1 | 1.0 | 3.7 |
| right | r3 -> r2 | 2784 | 1.1 | 0.4 | 0.9 |
| right | r2 -> r3 | 2784 | 3.9 | 0.9 | 2.8 |
| center | r3 -> r2 | 2784 | 2.6 | 0.6 | 1.8 |
| center | r2 -> r3 | 2784 | 2.4 | 0.6 | 1.7 |

Every point of each curve outside the window lies within 5.1 mm of the other curve, both ways, so neither curve has a
part the other lacks (coverage) and the curves coincide (the package stores mm).

**2. Station correspondence round 2 -> round 3.** Each round-2 centre station's foot on the round-3 centre, as a
fractional round-3 station u(k): monotone over all 3595 stations. Spacing 1.000608 -> 1.000693 m (lap 3597.185 ->
3597.492 m, n unchanged: the window's +0.31 m spread over the uniform re-stationing).

| region (r2 stations) | u(k) - k, stations: min / median / max | along-track (m) | same-index |P3[k] - P2[k]| max (m): centre / left / right |
|---|---|---|---|
| outside 611..3394 | -0.1654 / -0.0461 / +0.0729 | -0.166 .. +0.073 | 0.166 / 0.188 / 0.154 |
| window 3395..610 | -0.2194 / -0.0041 / +0.1095 | -0.220 .. +0.110 | 1.061 / 2.359 / 2.485 |

The stations outside the window slide along the unchanged curve by up to 0.17 m (growing from 0.07 m at s ~600 to
0.17 m at s ~3300, the re-stationing's accumulated spacing change); that slide is the whole of the same-index
displacement there (Astra's 0.188 / 0.154 / 0.166 m). Config station numbers map by fraction of the lap, so a
station-ranged item moves by at most this much along the road; a world point does not move.

**3. World anchors.** origin, heightfield box, ortho box, z0, direction and n identical. Config lat/lon points
projected on both centres (lateral offset, + left):

| anchor | r2 s / lateral (m) | r3 s / lateral (m) | delta lateral (mm) | in window |
|---|---|---|---|---|
| timing line | 0.00 / +0.015 | 0.00 / +0.162 | +147.2 | yes (pit straight refit) |
| T1 anchor | 322.27 / -0.368 | 322.11 / -0.540 | -172.8 | yes |
| T2 .. T12 anchors (11) | | | -1.0 .. +1.2 | no |
| T13 anchor | 3461.58 / -3.154 | 3461.81 / -2.860 | +293.9 | yes |
| T1 footbridge | 232.90 / +0.438 | 232.84 / +0.504 | +65.8 | yes |

Outside the window every anchor keeps its lateral offset to 1.2 mm (its station value moves +0.12-0.15 m with the
re-stationing, as in 2). Station 0 stays on the timing line (0.16 m from it, build log). Heightfield: 224 of 472896
cells differ (max |dz| 0.519 m), every one nearest a window station; none outside.

Section widths (p5 / median / p95, m), round 2 → round 3: T13 exit / pit entry 3395-3480 11.88/13.12/15.41 →
11.89/12.43/14.67; pit straight W of S/F 12.21/12.67/13.52 → 12.07/12.27/12.58; E of S/F 12.02/12.22/14.20 →
11.61/11.72/12.00; bridge approach 12.91/13.25/15.31 → 11.77/12.23/12.44; T1 12.27/12.84/14.84 → 11.84/12.58/13.27;
T1 exit 11.79/12.14/14.62 → 11.81/12.07/13.92 (published 40 ft = 12.19 m, advisory).

Where the round-3 fit still differs from a capture kerb / paint reading by more than 0.3 m inside the window (no owner
reading there): left 365 (+0.36 m) and 373 (-0.36 m), painted, inside left 363-390 where no window has red; right 458 (+0.49 m),
the yellow kerb's end, inside D5's 452-475 (his arc set aside there, provisionally).

## Gates and tests (round 3)

- Geometry stage (`build_track.py --stage geometry --out tools/track/out/mid_ohio_r3`): every check ok except
  **lap length FAIL** (3597.49 m vs 3633.934, -1.003 %). Owner-edge gates, measured against the MERGED, FILTERED
  evidence (`owner/r2/merged.json`: the strokes set aside by D1-D7 are not in it, so D5's arc cannot fail the gate):
  share = geometric proximity of each fitted edge point to his merged line (left 99.6 %, right 100.0 % within 0.25 m;
  >= 90 %), max = the station-normal residual (left 0.356 m, right 0.154 m; <= 0.5 m). Fit, coverage, waviness, kink, edge gate (0.023 / 0.023 m
  rms), world continuity (0.0050 / 0.0073 m), profile gate (0.021 m), cross slope (11.6 % max), edge jumps
  (0.083 / 0.084 m) all ok. Advisory exit overshoot at T1 +2.19 m (s 392; also in round 2). Rebuilt with
  `--write-on-fail` for this page: identical gate lines. The package is diagnostic, not accepted.
- `edge_gate.py --track tools/track/out/mid_ohio_r3 --config mid_ohio`: edge gate left / right and profile gate ok.
- Python: the focused set (`test_yellow_kerb.py`, `test_profile_gap.py`, `test_pit_merge.py`) 15 passed; every
  `test_*.py` under `tools/track` (21 files) 124 passed (125 after the review fixes, see below). Node: `test_edge_mark_transfer.cjs` 4 passed.
- Sonoma / Laguna reproductions: not needed for this round (no builder file changed; the two compare tools changed
  only behind new flags). Still required before any merge (SKILL Acceptance 6).

## Length (the nominal gate)

Measured (`r3/length_check.py`, all in the ENU frame): built centre 3597.5 m; left (outside, cw) edge 3635.6 m; right
edge 3560.3 m; the raw OSM loop of the six config ways 3620.2 m (smoothed 3622.95 m, manifest.md). Per section the
built centre is 0.5-3.7 m shorter than OSM in 12 of 14 sections (sum -22.7 m). This establishes a discrepancy of
-0.63 % against OSM and -1.003 % against the published figure; it does not establish its cause (OSM's tracing, the
published figure's measuring line, or a scale error are all candidates, the last tested below).

The published figure: 2.258 mi, 13 turns, is published for this layout (the 1989-90 "straight option between Turn 1
and the Keyhole" that skips the chicane; operator, midohio.com news 1084; Wikipedia; IMSA's track page). No source found
states the line or method it is measured on. The 2.400 mi chicane course is published as 228.5 m longer, while OSM's
chicane way is 30.0 m longer than the straight it replaces; this pair does not fit OSM's geometry, which is unexplained
here, not evidence of how either figure was measured. The outside edge's 3635.6 m (+0.05 %) is a coincidence of
numbers, not evidence of the operator's convention.

**Scale check** (`r3/scale_check.py`; Astra review item 5: the build and OSM share cfg.enu, so their agreement is no
projection check):
- A. Capture placement against NAIP (independently georeferenced), 77 captures over 706 m east and 1190 m north,
  each capture's registration shift regressed on its position: scale east 1 -0.072 % +- 0.079 %, north
  1 +0.058 % +- 0.044 % (1 sigma); 1082 capture pairs over 600 m apart: length ratio median +0.02 %. The capture
  pipeline's scale agrees with NAIP's within 0.1 %; no -0.6 % scale error.
- B2. The captures' mpp against their own lat/lon placement: 100 overlapping capture pairs 50-120 m apart at full
  resolution: scale 1 -0.0000 % +- 0.0002 % (east), 1 -0.0004 % +- 0.0007 % (north); residual 2 mm. (B, the halves
  of each capture against the 0.6 m NAIP, is too noisy at +-0.7 % and is not used.)
- C. cfg.enu against the WGS84 ellipsoid (the exact inverse of cfg.enu, pyproj.Geod): the frame is equirectangular on
  the equatorial radius, so 1000 m north in ENU is 997.56 m on the ellipsoid (+0.245 %) and 1000 m east is 1001.43 m
  (-0.142 %). For this lap: ENU / geodesic = +0.115 % (centre 3597.49 m in ENU = 3593.35 m on the ellipsoid; + 0.0065 %
  for the ~379 m ellipsoidal height: about 3593.6 m on the ground, -1.11 % against the published figure).

Scale finding: confirmed, within 0.1 % against NAIP; the only systematic scale term found is the frame's own +0.115 %,
which makes the course LONGER in ENU, not shorter. The shortfall is not a scale error. (The frame's anisotropy is the
contract's ENU definition (CONTRACTS section 1), shared by every track; recorded, not changed.)

Nothing was changed: `official_m` stays 3633.934, the tolerance stays 1 %, the course is not stretched. The choice is
the owner's (question 1). One more measure is available next run without new sources: the N837 onboard's Catalyst speed
readout integrated over the lap (Buttonwillow's method); it is pending, not yet a measure.

## T4 evidence note (2024 reconstruction)

- Operator (midohio.com news 1084, 19 Dec 2024): Kokosing, 14 Oct - 8 Nov 2024. "Turn 4's original footprint was
  preserved with the existing apex curbing kept in place at driver's right." "Its banking was reduced from 4 to 2
  degrees by removing 520 feet of track surface and excavating up to 18 inches along the outside edge." New underdrains,
  base and asphalt "to match the surface repavement completed in October 2023". "Both sides of the track were regraded
  starting 400 feet before the turn." Run-off stripped, raised with fill and 500 concrete blocks, regravelled; access
  roads on the back hillside; new guardrail in the T4 area through the Esses.
- The 2019 lidar profile at T4 (round 3 = round 2 there, held): bank toward the inside (right) rises from 0 at
  s ~1865 to 3.9-4.4 deg over s ~1950-1975 (apex s 1961) and back to 0 by s ~2005. This matches the operator's
  pre-2024 "4 degrees".
- Arithmetic, not proof: at 12.19 m (40 ft) width, rotating a section about its inside edge from 4 to 2 deg lowers the
  outside edge by 0.427 m (16.8 in); from the measured 4.4 deg peak, 0.47 m (18.4 in). The same order as "up to 18
  inches"; it does not show that excavation depth equals the final lowering (base and asphalt were rebuilt).
- Onboard: N837 (15 Apr 2026, post-rebuild) frames t62-64, 66-69 (`inventory/frames_t4_N837`, local; t65 is a player
  overlay): one uniform fresh surface through T4 with no seam, grass run-off on the outside, the red barrier beyond it,
  T5's red/white kerbs at t66-67. A hood camera cannot separate a 2 deg bank from the car's roll: the frames do not
  measure the bank. The owner's IndyCar sources (2026 onboard compilation 9Drr1VkE1_U; 2025 360 deg lap e25u_vjn1uM)
  are recorded in sources.json, not surveyed in this round.

**Hypothesis for approval (NOT applied; the heightfield is unchanged).** A section rule over T4 that halves the
measured bank. Each element is an assumption, with the measured anchor that would replace it:

| assumption | basis now | measured anchor that would replace it |
|---|---|---|
| the rebuilt 158.5 m (520 ft) lies symmetric about the 2019 bank peak (s ~1882-2040) | none: the operator gives the length, not its position | the rebuild's ends located in the 360 deg lap (pavement seam / new kerb ends) or post-2024 imagery |
| the inside edge keeps its 2019 elevation everywhere | "footprint preserved, apex curbing kept" (plan, not height) | inside-edge heights at the kerb from a post-2024 survey, or the kerb's height to the road in the 360 deg lap |
| every cross-slope over the interval is halved (4 to 2 deg is a ratio at the peak, not a rule elsewhere) | the operator's two numbers at one place | bank measured at several stations (360 deg lap sideways views against level references, or a newer lidar / survey) |
| the outside edge drops by the rotation (excavation = lowering) | the 18 in agrees in magnitude | outside-edge heights from a post-2024 survey |
| smoothstep transitions over the 400 ft regraded approach | "regraded starting 400 feet before the turn" (both sides of the track, i.e. the roadsides) | the profile at the rebuild's ends (seams located as above) |
| crown and longitudinal profile unchanged inside the interval | none | a newer survey or the onboard's horizon / pitch against landmarks |
| run-off raised beyond the outside edge | "fill ... raise the surface level" (no numbers) | heights from the 360 deg lap or newer imagery / survey |

The T1 footbridge `profile_gaps` repair is unchanged (stations 218-248, max repair 3.263 m).

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
edge; cyan band under them: every round-2 red stroke as drawn, those set aside included; white bars: window 3395 /
3410 / 595 / 610; yellow: ticks. Each caption lists the dispositions in that window; the intro asks D5 plainly.
Renderer `r3/review_windows.py`. To be published by the orchestrator (capabilities db, files win/*).

## Questions for the owner

1. Length (his decision; `official_m` unchanged). Matrix:

   | | keep 3633.934 m, 1 % gate | official_m None + independent checks (Buttonwillow rule) | ask the operator how 2.258 mi is measured |
   |---|---|---|---|
   | gate today | fails (-1.003 %) | passes only once the checks exist | pending |
   | evidence basis | the published figure for this layout, line unknown | today ONE independent measure (OSM, -0.63 %); the speed-integrated lap is pending | would settle it |
   | geometry change | none | none | none |
   | what it costs | the package stays diagnostic; downstream waits | drops an applicable published-length check | time |
   | scale check | confirmed within 0.1 % (scale_check.py); not the cause | same | same |
2. D5: approve or reject setting aside his T1-exit right arc (s 427-475) for the kerb line; the replacement still
   misses a capture reading by 0.49 m at s 458. Windows r3_s10_at0420 and r3_s11_at0490.
3. T4: which of the hypothesis's assumptions to pursue with the 360 deg lap next run (none applied).

## Review fixes (GPT 6 Astra, round 3: HOLD)

- Frames schema (7): `owner_edges.py --frames` reads the round-3 schema (`centre_enu`, `half` or `image_px`);
  `r3/frames_roundtrip.py`: the round-3 edges written as image strokes through the published `frames.json` and read
  back by the importer: worst 0.027 m = 0.45 px (13 windows; median 1-9 mm).
- Page (7): the cyan band labelled as every round-2 stroke as drawn; per-window dispositions in the captions; D5 asked
  plainly in the intro (`r3/page_intro.html`, `r3/build_page.sh`). Same window ids, frames and images (frames.json and
  every PNG byte-identical to the published version).
- Held proof (1): `r3/held_proof.py`, above. Scale (5): `r3/scale_check.py`, above. Length and T4 wording (5, 6),
  gate labels (4): above. Tests (2): `test_owner_edges.py::test_cli_frame_schemas_and_both_axes` (the CLI, four frame
  schemas, both axes, the default's half pixel on both).
