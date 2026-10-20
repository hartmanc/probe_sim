# Buttonwillow evidence manifest (round 0: sources and stage 1, 20 Oct 2026)

Status: **stage 0 complete, stage 1 stopped at its fit gates** (no package, nothing published, no scenery placed). The
build-track skill's fitted-edge gates assume a painted edge line; Buttonwillow has none (see "Stage 1" below). Every
object table of a scenery round starts empty here: no object without a cited source, and no object yet.

## The event and the layout (stage 0.1)

| item | value | source |
|---|---|---|
| event | 24 Hours of Lemons "Button Turrible 2026", 26-27 Sep 2026 (race sessions Sat 10:00-18:00, Sun 9:00-15:30) | 24hoursoflemons.com/race/?id=454 (fetched 20 Oct 2026) |
| layout picture | registration.24hoursoflemons.com/userfiles/races/26_buttonwillow.png: 404 on the live server on 20 Oct 2026; read from web.archive.org/web/20260111111352id_/... (sha1 66affc15b9af2f9d02abc69bc04db22a0618349c); identical drawing to the 2027 event's buttonwillow27.png (race/?id=485) | the event page's `<img>` |
| direction | clockwise: arrow east on the start/finish straight; shoelace area of the picture's turn circles positive in image (y-down) coordinates; 11 numbered turns | the picture |
| configuration | Race #13 CW ("13CW" in the 2026 onboard titles); the operator's map brp-track-map-race-13-outline.png is the same loop | buttonwillowraceway.com/track-info/track-maps/ |
| results | MyLaps / Speedhive event 3731897, race session 12906863 (105 classified; best lap 2:15.252, GT Poorty Racing); Friday test 12906860. #619 Anal Corkscrew Probe: P15, best 2:29.956, 287 laps | eventresults-api.speedhive.com (data in tools/race/data/buttonwillow/) |
| loop | 16 OSM raceway parts, clockwise from the front straight (config `loop_ways`): front straight, Sunrise (T1), Off Ramp (T2), I-5, Cotton Corners (T3, T4), Grapevine (T5), the Club Corner / Bus Stop / Truck Stop hump, Riverside (T6, T7), Lost Hill (T8), the drag strip's north end, Star Mazda Turn (T9), Esses (T10), Sunset (T11) | OSM 20 Oct 2026 |
| loop check | the onboard's Garmin Catalyst minimap (GPS trace of the driven lap), affine-fitted to five candidate loops: centre -> trace p95 6.3 m for this loop; 17 m with the outer T2 loop (OSM 39224609), 37 m with the drag strip instead of Lost Hill, 46 m with the Dog Leg instead of the hump, 64 m with the Sweeper instead of Star Mazda | onboard 7QS2M-HGSI4 frame t100 (an ad-hoc fit of the trace to each OSM variant; the method is that of inventory/catalyst_dots.py; numbers in the config) |
| start/finish | no painted line on the captures; the timing loop's two saw cuts below the starter's stand (c20_s0150 px x 450), on the first centre: 35.4887078, -119.5445213; the Catalyst lap line is within 10 m | captures, pit-lane video 22:19-22:28, onboard |
| lap length | no official figure better than ~3 % (Wikipedia "3.000 mi" = a rounded 3.0 mi; lapmeta 4.43 / 4.83 km; MyLaps' 3.1 mi is the Classic track's East + West length, the venue default). Measured: OSM loop 4701 m; onboard speed integrated over lap 21: 4650 m on the driven line; stage-1 centre 4697-4705 m | config `loop_check` (official_m None, with the reason) |

## Sources (stage 0.2-0.5)

| input | what | date |
|---|---|---|
| OSM | API map call -119.556,35.478,-119.530,35.500 (cache osm/osm.xml): the raceway ways, the "Pit / Fire Road" (39224587) pit lane, 2 buildings (the control tower block), 1 comms tower node, no barriers | 20 Oct 2026 |
| 1 m DEM | USGS 3DEP CA_SanJoaquin_2021_A21, tiles x26y393, x26y394, x27y393, x27y394 (UTM 11N, NAVD88) | published 20 Jan 2024 |
| lidar | the DEM's own survey CA_SanJoaquin_2021_A21, Entwine tiles usgs-lidar-public/CA_SanJoaquin_6_2021 (1256 nodes over the box, 43.7 M points, ~18 pts/m^2; classes 1, 2, 8) | flown 24 Feb - 22 Mar 2021 (published 1 Mar 2023) |
| repave history | the circuit was repaved in July 2014 (Wikipedia, uncited) and has had no reported repave since: the 2021 survey postdates it; the profile is flat (3.3 m range) | |
| 1/3 arc-second DEM | n36w120 | current |
| NAIP | m_3511936_ne_11_060_20220608 (0.6 m) | 8 Jun 2022 |
| clean captures | 106 Google satellite z20 captures (0.12156 m/px, 1440 x 725, labels off, UI hidden, panned by dragging) along the loop every 50 m (c20_sNNNN) and the pit lane (c20_pNNNN), taken in a headless Chrome (tools/track/compare/headless_capture.ts maps). Imagery (c) Airbus / Maxar, watermarks (c) 2025-2026 Google; capture date unknown. Common shift Google - NAIP (0.6, 0.0) m (median of 83 registrations with peak >= 8); 182 overlapping neighbour pairs agree within 0.01 m (compare/capture_pairs.py), no capture excluded | 20 Oct 2026 |
| onboard (lap) | youtube.com/watch?v=7QS2M-HGSI4 "Buttonwillow 2026 Lemons, My best lap of the weekend" (Daniel Peters, uploaded 29 Sep 2026): Garmin Catalyst hood camera ~1.05 m, lap 21 = 2:27.48, 80 frames every 2 s at 720p-1080p | race of 26-27 Sep 2026 |
| onboard (pit lane) | youtube.com/watch?v=ucmXJu5QKFQ "Lemons 2026 at Buttonwillow - Saturday - Jason Evening Yellow Flag Tour" (Jason Dosch, uploaded 13 Oct 2026): 20:31-22:46 pit-in before T11, the lane end to end between two Jersey walls, the tower, the starter's stand | Sat 26 Sep 2026 |
| other onboards examined | sBNZ9qIJjqg (car 414 best lap, in-cabin, 360p: not used), ywKaF_7NJ6Q and the bajarider1000 13CW GoPro series (not stepped), HPTVVvRZdk4 / 3OdejgGWrGk (Jason Dosch stints: no pit lane in the sampled minutes), 5Jsiwpr1o-A (360 camera, unusable), goGxY2m__08 (car 414 stint 4, in-cabin; pit exit not resolvable) | 2026 |
| Street View | none on the circuit (compare/buttonwillow/streetview.md): coverage only on Cal Club Rd north of the paddock, 200-250 m from the track | 20 Oct 2026 |

## The survey walk (stage 0.5)

| spot | placed / used | why |
|---|---|---|
| every corner, the pit lane, the tower, the stations | not surveyed | no Street View or photo sphere (coverage overlay z16 and z19) |
| Cal Club Rd | not used | too far from the track to read anything on it |

## Eye-level inventory (stage 0.6-0.10)

`inventory.json` / `inventory.md` (generated by `inventory.py --pkg tools/track/out/buttonwillow`, i.e. mapped onto the
stage-1 diagnostic candidate, since no package is published): 59 lap frames between the start/finish crossings
(0:05.47-2:32.95), **92 rows**: kerb 37 (left 18, right 19), cone_line 16, wall 14, station 14, paint 4, building 3,
runoff 2, tyre_wall 1, mast 1; 13 of them pit-lane rows (`inventory/pit.jsonl`). Heights: 32 rows carry one, every one
with a method (jersey-ref 0.81 m for the K-rail pit and paddock walls, cone-ref, storeys for the tower); station heights
are not measured yet.

Time map (`inventory/source.json`): the start/finish crossings from the Catalyst lap timer, 15 GPS anchors every 10 s
from the Catalyst minimap dot (`tools/track/inventory/catalyst_dots.py`, fit p95 6.6 m), and the T2 and T9 speed minima.
Leave-one-out residuals 1.6-29.5 m with the speed profile (5-56 m linear); speeds in/out 21-41 m/s.

What the lap shows (for the scenery round): an open desert circuit, dirt runoff everywhere; one wall on the lap, the
white / red K-rail pit wall along the front straight, with a second K-rail between the pit lane and the paddock; flat
red / white / blue painted concrete kerbs (blocks ~1.0 m, band ~0.9 m beyond the asphalt edge; colour order blue,
white, red, white) at almost every corner; roofed corner stations on tyre-faced earth mounds; single orange cones at
turn-in points; the two-storey control tower with a blue roof and the scaffold starter's stand on the pit wall; a tall
communications mast north of T9 (OSM node 10220517717).

## Scans examined

| scan | captures | result |
|---|---|---|
| kerb blocks (compare/kerb_detect.py on the run-3 candidate) | all 106 | 41 candidate runs, 31 used as edge features (outer limit >= 0.3 m beyond the asphalt end, >= 9 m); colour reads "grey" on the captures (the onboard shows red / white / blue) |
| road mouths (OSM ways leaving the road, ray test) | - | 17 mouths besides the pit lane; prior interpolated across each (config `prior.interp`) |
| edge contrast (R, G, B across the edge at six stations) | c20_s0750, s1150, s1600, s2300, s2700, s4100 | asphalt R - B +8..+12, dirt +20..+31, luminance 140-160 on both sides: a 5-15 step in brightness, the outer 1-1.5 m of asphalt dusty |

## Stage 1: why it stopped

Five geometry runs (20 Oct 2026; `build_track.py --stage geometry`, the last two with `--write-on-fail` for diagnosis):

| run | edge evidence | coverage L / R | obs within 0.25 m L / R | other failures |
|---|---|---|---|---|
| 2 | default (painted lines) | 15 / 13 % | 93 / 91 % | gaps of 554 / 479 stations: no painted line to find |
| 3 | asphalt_end everywhere | 44 / 46 % | 77 / 81 % | waviness, kinks at the T1 and T11 kerbs, edge steps |
| 5 | asphalt_end tuned (jump 8, sat 40, -2..+2 m) + kerb_band at 31 kerb zones + prior across 17 mouths | 48 / 50 % | 75 / 78 % | waviness 0.046 / 0.050 m, edge steps 0.16-0.19 m at the pit-in (s ~4510), Sunset width collapsing to 4.9 m at the pit-in split |

Gates that pass in run 5: longest gap, painted-midpoint residual, loop stations, elevation range (3.3 m), direction,
start/finish (0.79 m), edge jumps, cross slope (max 9.7 %), world continuity, profile (max step 0.023 m); centre
converged after 30 refits; length 4697 m; corners T1 R 52, T2 26, T3 41, T4 40, T5 43, T6 88, T7 111, T8 68, T9 33,
T10 66, T11 46 m.

The blocker is the fit gates' measure, not a missing source: the fitted method's evidence is the painted line (12 cm,
sharp) and the red kerb band. Buttonwillow has neither: its asphalt ends in a ragged, dusty edge whose position varies
0.3-1.2 m station to station on the captures (the miss distribution in run 5 is flat from 0.25 to 1.2 m:
1006 / 738 / 667 / 635 / 500 rows), and its kerbs read grey. A warmth-step detector (R - B) finds the dust line
1.2-1.6 m inside the asphalt end (and would make the road ~11 m wide, under the operator's 36 ft minimum). The 90 %
within 0.25 m and 60 % coverage gates cannot be met from these captures without loosening them, which the skill
forbids. Options for the owner:

1. A gate definition for unpainted asphalt-to-dirt edges (an owner decision, written into the skill): e.g. the
   observation tolerance and coverage measured only on painted / kerb evidence, with asphalt-end sides held to the
   waviness, kink and edge-gate checks (which run 5 nearly passes) plus a whole-lap hood sheet review.
2. A sharper edge source: the 2021 lidar's intensity (18 pts/m^2; asphalt dark, dirt bright; a first 0.25 m raster
   at s ~2600 shows the road as a dark band with diffuse edges, so a 0.5 m grid at best), or licensed higher-resolution
   imagery.
3. Accept the NAIP-derived edges (13.0-13.7 m median width, inside the operator's 36-55 ft) as a provisional
   geometry for driving, clearly marked as not passing stage 1.

Builder changes made for this circuit (config-gated; Laguna's and Sonoma's code paths unchanged: their OSM loops and
the default asphalt_end are identical to the 1e71ef2 code on their caches and on 3000 random profiles): OSM way parts
driven against node order (`geo.osm_loop`), edge features `warm_end` and `kerb_band`, the asphalt_end detector's
parameters (`spline.asphalt_end`), `inventory.py --pkg`, and the app's three-colour kerb paint (`colors: [stripe,
base, stripe 2]`).

## Stage 1, round 2 (20 Oct 2026): better evidence, gates unchanged

No geometry run this round: neither lead produced evidence that meets the bar for a refit (below), so the last gate
lines are still run 5's, exactly as the builder printed them:

```
[FAIL] fit left: observations within 0.25 m: 74.9 % of the associated observations (>= 90 %); 78 % of capture rows have a band within 1.2 m (>= 85 %); 43 % of all rows
[FAIL] fit left: coverage: 48 % of stations (>= 60 %)
[ok]   fit left: longest gap: 47 st at (354, 400) (<= 60)
[FAIL] fit left: waviness: rolling-100 rms max 0.046 m (<= 0.04), peak 0.080 m (<= 0.1)
[FAIL] fit left: kink: max 0.59 deg/station (<= 0.5); over at [(4664, 4672)]
[FAIL] fit right: observations within 0.25 m: 77.9 % of the associated observations (>= 90 %); 81 % within 1.2 m (>= 85 %); 49 % of all rows
[FAIL] fit right: coverage: 50 % of stations (>= 60 %)
[ok]   fit right: longest gap: 41 st at (583, 623) (<= 60)
[FAIL] fit right: waviness: rolling-100 rms max 0.050 m (<= 0.04), peak 0.096 m (<= 0.1)
[ok]   fit right: kink: max 0.48 deg/station (<= 0.5)
[FAIL] edge gate left : rms 0.086 m (<= 0.1) | max adjacent step 0.161 m at 4512 (<= 0.1)
[FAIL] edge gate right: rms 0.068 m (<= 0.1) | max adjacent step 0.186 m at 4511 (<= 0.1)
```

### Lead B: the capture detector's ambiguity

Every capture profile at the run-5 asphalt-end stations (8117 station-side pairs, all 106 captures), read relative to
the run-5 fitted edge:

| detector | side | coverage | readings agree across captures (within 0.25 m of the station median) | station medians within 0.25 m of a 41-station running median | rms | lag-1 correlation of that residual along s |
|---|---|---|---|---|---|---|
| asphalt_end tuned (inside out, the run-5 detector) | left | 0.83 | 0.96 | 0.37 | 0.87 m | 0.38 |
| | right | 0.84 | 0.96 | 0.41 | 0.85 m | 0.37 |
| outermost transition (outside in), jump 6 | left / right | 0.96 / 0.96 | 0.89 / 0.85 | 0.34 / 0.30 | 0.80 / 0.80 | 0.37 / 0.32 |
| jump 8 | left / right | 0.90 / 0.91 | 0.88 / 0.86 | 0.30 / 0.26 | 0.85 / 0.87 | 0.36 / 0.34 |
| jump 10 | left / right | 0.79 / 0.83 | 0.90 / 0.88 | 0.28 / 0.26 | 0.91 / 0.92 | 0.34 / 0.36 |

Readings of the tuned detector relative to the fitted edge (0.25 m bins from -2.0 to +2.0 m), left:
665 279 339 396 358 637 **2052 1595** 628 381 384 311 334 326 261 197; right: 710 279 329 345 387 658 **2427 2017**
635 359 350 322 213 180 280 166. A central mode at -0.5..0 m on a flat background from -2 to +2 m, plus a pile at the
window's inner end (-2 m).

Reading: the captures agree with each other at a station (they are one mosaic, so this is not independent evidence),
but the station medians jump along the track (lag-1 correlation 0.37: not a smooth physical wander, which would
correlate strongly from one metre to the next). So the scatter is partly the detector choosing between transitions,
as suspected. But reading from outside in does not fix it: the dirt beyond the edge has its own transitions (tyre
tracks, vegetation, graded strips), and the outside-in detector piles up at the far end of the window (+1.75..+2.0 m:
2582 / 3090 readings at jump 6) and scatters more along the track (0.26-0.34 within 0.25 m). No detector tried gives a
reading that is smooth along the track.

### Lead A: the lidar point cloud

`tools/track/lidar_edge.py` re-reads the EPT tiles (cache/buttonwillow/ept) with Intensity, Classification and
ReturnNumber into a corridor cache (cache/buttonwillow/lidar_corridor.npz: 3.59 M points within 25 m of the centre;
class 2 ground 2.61 M, class 1 0.98 M). Per station the points within +-W m along the track are binned across the
normal (0.1 m bins over -4.5..+4.0 m from the current edge, as edges_spline.U) and averaged. Density turned out to be
lower than 18 pts/m2 on the road: 14-65 ground points per 0.1 m bin at W = 10 m (16-20 m of road).

Two readings per station: the intensity step (the largest rise of the 0.6 m means either side within -2.5..+2.5 m,
at least 350 and 20 %) and the elevation slope break (first sustained 3 cm departure from the line fitted on
-4.0..-1.5 m).

| reading | W | side | coverage | within 0.25 m of a 41-station running median | rms | vs the capture median on the eight stretches: n, bias, p10 / p90, share with abs diff > 0.5 m |
|---|---|---|---|---|---|---|
| intensity step | 5 m | left | 0.62 | 0.76 | 0.45 | 355, -0.24, -1.98 / +1.60, 0.78 |
| | | right | 0.61 | 0.81 | 0.35 | 427, -0.18, -2.24 / +0.78, 0.67 |
| | 10 m | left | 0.55 | 0.80 | 0.29 | 336, -0.20, -1.68 / +1.69, 0.77 |
| | | right | 0.58 | 0.82 | 0.29 | 419, -0.16, -2.13 / +0.79, 0.64 |
| slope break | 5 m | left | 0.81 | 0.52 | 0.63 | 435, +0.66, -1.10 / +2.27, 0.74 |
| | | right | 0.76 | 0.51 | 0.64 | 411, +0.84, -0.80 / +2.24, 0.83 |
| | 10 m | left | 0.81 | 0.58 | 0.58 | 448, +0.76, -1.05 / +2.36, 0.76 |
| | | right | 0.75 | 0.55 | 0.60 | 379, +0.86, -0.88 / +2.30, 0.82 |

(The running-median smoothness of a W-windowed reading is flattered by the overlapping windows: adjacent stations share
most of their points.)

Stacking the lidar intensity on the capture edge over the eight stretches (276 / 277 stations, 2 m window) shows no
step but a ramp: left 1684 at -2 m rising evenly to 2637 at +2 m, right 1648 to 2937. In the lidar, as in the
captures, the asphalt-to-dirt transition at Buttonwillow is spread over 2-4 m.

The lidar disagrees with the captures by more than 0.5 m at 64-83 % of the eight stretches' stations. Its
differences have no stable sign (bias -0.2 m for the intensity step and +0.8 m for the slope break, p10 / p90 out to
+-2 m), so they read as noise rather than a 2021-to-2025/26 edge that moved. The lidar is not consistent along the
track either (80-82 % at best against the 90 % bar). It is therefore **not** added as an evidence feature, and no
refit was run.

### What this means for the owner's decision

Both datasets say the same thing: at Buttonwillow there is no sharp edge to measure. The 2026 captures and the 2021
lidar both show a 2-4 m asphalt-to-dirt transition. The capture readings are consistent across captures (0.96) but
not along the track (0.37-0.41 within 0.25 m of a running median). The fitted spline's 75-78 % "within 0.25 m" is
what a ragged, dusty edge measured by any of these detectors gives. The proposal for a gate on unpainted edges stays
an open owner decision (report of this round).

## Stage 1, round 3 (20 Oct 2026): the gates that bind under any definition

Within / coverage are the owner's decision and still fail (expected). Two runs:

- **Run 6**: the asphalt_end inner window back to -1.2 m. Final config and output `tools/track/out/buttonwillow_r6`.
- **Run 7**: run 6 plus the front straight declared as a straight line fitted to the asphalt-end readings. Not kept.

**Run 6 (final), gate lines as printed:**
```
[FAIL] centre convergence: centre still moving 0.062 m after 40 refits
[FAIL] fit left: observations within 0.25 m: 72.9 % of the associated observations (>= 90 %, the skill's measure); 88 % of capture rows have a band within 1.2 m (>= 85 %); of those 53.6 % within 0.25 m, the rest at 0.25-0.4/0.4-0.6/0.6-0.8/0.8-1.0/1.0-1.2 m: [1203, 816, 760, 947, 344]; 47 % of all rows
[FAIL] fit left: coverage: 51 % of stations (>= 60 %)
[ok] fit left: longest gap: 40 st at (356, 395) (<= 60)
[FAIL] fit left: waviness: rolling-100 rms max 0.058 m (<= 0.04), peak 0.095 m (<= 0.1) outside tight corners; over at [(61, 124), (150, 183), (4438, 4527)]
[ok] fit left: kink: max 0.45 deg/station (<= 0.5) outside tight corners; station 0 0.07
[FAIL] fit right: observations within 0.25 m: 77.5 % of the associated observations (>= 90 %, the skill's measure); 88 % of capture rows have a band within 1.2 m (>= 85 %); of those 58.6 % within 0.25 m, the rest at 0.25-0.4/0.4-0.6/0.6-0.8/0.8-1.0/1.0-1.2 m: [1090, 781, 689, 852, 363]; 52 % of all rows
[FAIL] fit right: coverage: 54 % of stations (>= 60 %)
[ok] fit right: longest gap: 45 st at (582, 626) (<= 60)
[FAIL] fit right: waviness: rolling-100 rms max 0.066 m (<= 0.04), peak 0.120 m (<= 0.1) outside tight corners; over at [(186, 235)]
[ok] fit right: kink: max 0.43 deg/station (<= 0.5) outside tight corners; station 0 0.06
[ok] edge jumps: max lateral change between stations: left 0.161 m, right 0.160 m
[FAIL] edge gate left : rms vs 41-st median (R>250 m, 2280 st) 0.075 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.118 m at 62 (next 0.112@4265, 0.112@4267; <= 0.1) | max edge-column cross-section step 0.024 m at 1318
[FAIL] edge gate right: rms vs 41-st median (R>250 m, 2280 st) 0.080 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.137 m at 4124 (next 0.137@4125, 0.137@4123; <= 0.1) | max edge-column cross-section step 0.022 m at 25
```

**What changed from run 5:**
- Run 5's inner window of -2.0 m let the asphalt-end edge creep inward on every refit. By the end, the front straight's half-widths were down to 0.6-2.5 m at s 4524-4560 and 4656-30, with the centre wandering into the dirt.
- That collapse is what produced the run-5 kink at 4664-4672 and the steps at 4511-4512, and the 4.9 m "pit-in width". It was not the pit-in split: the pit lane leaves at s ~4296 (OSM 39224587), behind the wall.
- With -1.2 m, the kinks pass on both sides (0.45 / 0.43°). The width (report) is median 14.27 m, p10 12.08, p90 17.22, min 9.02 m at 3731, max 23.91 m at 23. 4.2 % of stations are under the operator's 36 ft (10.97 m) and 14.4 % over 55 ft (16.76 m).

**What still binds and fails:**
- Waviness, all on or next to the front straight and T1:
  - left 61-124 and 150-183: the edge on the pit-wall median, whose gravel strip gives scattered readings;
  - left 4438-4527: the T11 exit into the straight;
  - right 186-235: the T1 kerb, where kerb_band takes the inner side of the white blocks rather than their outer limit (sheet `worst2_left_right_150-235`).
- Edge steps:
  - left 0.118 m at 62 (front straight) and 0.112 m at 4265-4267, 3-5 stations before the pit-in exemption (4270-4330);
  - right 0.137 m at 4124, 6 stations before the Zorros Corners mouth exemption (4130-4190).
  - I did not widen either exemption: that needs the capture showing the junction's fillet.
- Centre convergence: a 0.062 m limit cycle after 40 refits.

**Run 7 (front straight as a straight from the asphalt-end readings, lo 4470 .. hi 180, 318 / 625 inliers):** worse.
- It starts inside the T11 exit curve, where the station normals cross the line far off: width -5.15 m at 4477, kinks 0.74 / 0.73° at 4432-4476, waviness 0.068 / 0.078 m.
- Not kept. A start after the pit-wall head (~4520) is the next thing to try.

**Report-only numbers (run 6; builder flag `spline.report_by_kind`; no gate reads them):**

| side | evidence | rows / stations | within 0.25 m (all associated rows) | within 0.6 m | coverage | readings within 0.25 m of their station's median over captures |
|---|---|---|---|---|---|---|
| left | asphalt_end | 8962 / 4061 | 50.2 % | 74.1 % | 50 % | 98.3 % |
| left | kerb_band | 1047 / 631 | 80.8 % | 96.7 % | 56 % | - |
| right | asphalt_end | 9355 / 4056 | 56.3 % | 77.5 % | 54 % | 97.9 % |
| right | kerb_band | 966 / 636 | 79.0 % | 93.9 % | 49 % | - |

Width on the fitted edges: median 14.27 m, p10 12.08, p90 17.22, min 9.02 m (station 3731), against the operator's 10.97-16.76 m.
Cross-capture agreement (round 2): 0.96.

**Sheets for the owner:** `compare/buttonwillow/edge_sheets/` (local, ignored, reference only):
- the eight clean stretches, clean1-clean8;
- the three worst waviness stretches, worst1-3;
- the two edge steps, at 4124 right and 4265 left.

Fitted edges are drawn in red, the centre in blue, asphalt-end readings in yellow and kerb-band readings in cyan (`tools/track/compare/edge_sheets.py`).

## Stage 1, round 4 (20 Oct 2026): the decision-independent gates

Two runs: run 8 and run 9 (final, `tools/track/out/buttonwillow_r9`). Everything except within / coverage (the
owner's decision) and one edge step now passes.

**Run 9 (final), gate lines as printed:**
```
converged after 26 centre refits
[FAIL] fit left: observations within 0.25 m: 71.7 % of the associated observations (>= 90 %, the skill's measure); 87 % of capture rows have a band within 1.2 m (>= 85 %); of those 49.9 % within 0.25 m, the rest at 0.25-0.4/0.4-0.6/0.6-0.8/0.8-1.0/1.0-1.2 m: [1176, 996, 834, 1028, 330]; 43 % of all rows
[FAIL] fit left: coverage: 54 % of stations (>= 60 %)
[ok] fit left: longest gap: 38 st at (352, 389) (<= 60)
[ok] fit left: waviness: rolling-100 rms max 0.030 m (<= 0.04), peak 0.048 m (<= 0.1) outside tight corners
[ok] fit left: kink: max 0.36 deg/station (<= 0.5) outside tight corners; station 0 0.00
[FAIL] fit right: observations within 0.25 m: 75.5 % of the associated observations (>= 90 %, the skill's measure); 88 % of capture rows have a band within 1.2 m (>= 85 %); of those 53.7 % within 0.25 m, the rest at 0.25-0.4/0.4-0.6/0.6-0.8/0.8-1.0/1.0-1.2 m: [1066, 741, 688, 1207, 415]; 47 % of all rows
[FAIL] fit right: coverage: 56 % of stations (>= 60 %)
[ok] fit right: longest gap: 41 st at (583, 623) (<= 60)
[ok] fit right: waviness: rolling-100 rms max 0.036 m (<= 0.04), peak 0.063 m (<= 0.1) outside tight corners
[ok] fit right: kink: max 0.36 deg/station (<= 0.5) outside tight corners; station 0 0.01
[ok] painted-midpoint residual: rms 0.17 -> 0.04 m (final refit)
[ok] start/finish: station 0 is 0.04 m from the configured timing line
[ok] edge jumps: max lateral change between stations: left 0.112 m, right 0.107 m
[FAIL] edge gate left : rms vs 41-st median (R>250 m, 2356 st) 0.071 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.100 m at 4267 (next 0.100@4268, 0.099@4265; <= 0.1) | max edge-column cross-section step 0.024 m at 1315
[ok] edge gate right: rms vs 41-st median (R>250 m, 2356 st) 0.061 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.092 m at 3102 (next 0.092@3103, 0.091@3101; <= 0.1) | max edge-column cross-section step 0.020 m at 4402
[ok] world continuity left / right, profile gate (0.024 m), loop, elevation, direction, cross slope, no NaN
```

**What changed and why:**

1. **Centre convergence.** Run 6's swing (0.06-0.075 m) sat at stations 39-40 and 166, the right-side mouths of the
   infield connector 34351026 and of Atlantic 34351042 on the front straight. The free fit alternated between taking
   the road's edge and the mouth there. Fix: the front straight is declared as a straight line fitted to the
   asphalt-end readings, from after the pit-wall head (4525) to the T1 kerb (180), on both sides (`straights` fit
   'asphalt_end'; 609 / 585 inliers). Round 3's run 7 had started it at 4470, inside the T11 exit. Runs 8 and 9
   converge (24 / 26 refits).
2. **Waviness.** The straight also removes left 61-124 and 150-183 (the free fit following the gravel median) and
   4438-4527. Right 186-235 (T1 kerb) is gone too.
   - The kerb_band reading was already the band's outer limit: it is the `u1` of a 0.3-2.6 m band. At s 195-225 the
     bright band runs -1.3..-0.0 m and the reading is -0.02..+0.18 m.
   - The waviness came from the straight's edge meeting the kerb, where the kerb flares out from the asphalt at its
     start (the r6 sheet `worst2`). The free fit could not hold both; with the straight fixed up to 180, it can.
   - No detector change was needed.
   - Run 8 still showed left 1879-1959 (0.047) and right 2048-2132 (0.055), with no junction, kerb or shadow at either.
     Its sheets show the readings jumping 0.3-0.5 m between the asphalt end and a dust line. In run 9, with station 0
     moved (item 4), both are inside 0.04: 0.030 left, 0.036 right. They sit near the bound, and the cause is the
     edge's own scatter.
3. **Edge steps.**
   - Right, 0.137 m at 4124 (run 6): c20_s4250 (sheet `step_right4124`) shows the paved fillet of the Zorros Corners
     mouth starting at s ~4115 on the right. The exemption's evidence changed and its range with it: 4108-4190 (was
     4130-4190, from the OSM node +-30). The prior interpolation also starts at 4112. Run 9's largest right step is
     0.092 m at 3102.
   - Left, 0.118 m at 62 (run 6): the front straight. Gone with the straight.
   - Left, 0.100 m at 4267 (run 9; 0.112 m in run 6): **not changed**. c20_s4400 (sheet `step_left4265`) shows no
     junction there. The pit lane's fillet begins at ~4280 on the left, and the exemption covers 4270-4330. At
     4255-4270 there is a marshal post's tyre-faced mound on the left beside the edge; the readings scatter around it,
     and the edge steps by 0.100 m just before the exemption. It fails the 0.1 m bound by rounding (0.1004 m). It stays,
     and the capture is as described.
4. **Start/finish.** Run 8 failed it: station 0 sat 7.19 m from the configured point, all of it across the track. The
   configured point lay on the FIRST centre, which sat 4-7 m toward the right edge once the front straight was fitted.
   The point now sits where the same timing line crosses the fitted centre (35.4887722, -119.5445271). Run 9: 0.04 m.

**Report-only numbers (run 9):**

| side | evidence | rows / stations | within 0.25 m | within 0.6 m | coverage | within 0.25 m of the station's median over captures |
|---|---|---|---|---|---|---|
| left | asphalt_end | 8995 / 4061 | 46.4 % | 72.5 % | 49 % | 97.7 % |
| left | kerb_band | 1033 / 631 | 77.4 % | 93.6 % | 55 % | - |
| right | asphalt_end | 9201 / 4056 | 50.4 % | 71.5 % | 51 % | 97.8 % |
| right | kerb_band | 964 / 636 | 81.6 % | 94.8 % | 52 % | - |

Width: median 14.38 m, p10 12.13, p90 17.18, min 10.31 m at 2512, max 19.43 m at 2430. 2.3 % of stations are under
the operator's 36 ft (10.97 m) and 14.2 % over 55 ft (16.76 m). Cross-capture agreement: 0.96 (round 2).

**Sheets:** `compare/buttonwillow/edge_sheets/` holds the same thirteen places on run 9; `edge_sheets/r6/` holds them on
run 6 (before / after, e.g. `worst2_left_right_150-235`). Local and ignored.

**Advisory (not a gate):** exit overshoot at T1 (+2.38 m, 426), T2 (+3.64 m, 687) and Star Mazda (+2.51 m, 3535).
At 455-500 the run-8 sheet shows the right edge running through the dirt past the T1 marshal post beside the pit-out
lane. This is where the pit-merge logic applies (cone line 440-521) and is for the stage-1 hood-sheet review.

## Stage 1, round 5 (20 Oct 2026): the owner's unpainted-side gate; stage 1 and 2 pass, published for the 1.10 review

**The owner's decision (20 Oct 2026, 14:00 PDT).**
- A side is unpainted when at least 80 % of its associated readings come from asphalt_end.
- On an unpainted side, a bias gate replaces "observations within 0.25 m": over rolling 41-station windows that hold at
  least 10 readings, the median signed residual must lie within +-0.25 m in at least 90 % of the windows.
- Coverage on an unpainted side is held to 50 %.
- Everything else is unchanged, and painted and kerb sides keep FITTED.

**Where it is implemented.**
- The rule lives in `edge_gate.py` (UNPAINTED, unpainted_side, bias_gate, unpainted_thresholds) and in the builder, with
  a docstring update.
- It is documented in SKILL.md under 1.9, together with the owner-traced edge recorded as a future evidence feature.
- Tests: `tools/track/test_edge_gate_unpainted.py`, 7 tests (ragged zero bias passes, shifted 0.4 m fails, a painted
  side keeps the old gate, the threshold, Laguna and Sonoma are not unpainted).

**Before the gate: merged track-pipeline 2bad53f** (no conflicts). Python tests, vitest and the build pass after the merge.

**Config this round**
- `spline.mask` (new key, edges_spline MASK; empty = every reading): left 4250-4272. This is the marshal post's tyre
  mound beside the edge on the T11 approach (c20_s4400). The 0.100 m step at 4267 is gone: the largest left step is now
  0.078 m, at 3688.
- `spline.lam` 60 and `huber` 0.15 (defaults 30 / 0.25). These are the skill's allowed knobs. The first run under the new
  gate (masked, default spline) failed on:
  - right waviness 0.056 m at 2050-2131 and steps of 0.101 m left at 2466 and 0.105 m right at 2112 (the Riverside
    straight's readings jumping between the asphalt end and a dust line);
  - the stiffer spline with the tighter robust loss runs through the middle of them.
- The timing line point and the front-straight straight are as in round 4.

**Stage 1 (final run, exit 0, `work/stage_geometry.json` passed):**
```
converged after 16 centre refits
[ok] fit left: unpainted bias: unpainted side (85 % of 5715 associated readings from asphalt_end); 98.3 % of 4598 41-station windows have a median residual within +-0.25 m (>= 90 %); worst -0.453 m at 394 (374..414); 86 % of capture rows have a band within 1.2 m (>= 85 %); spread (printed, not gated): |residual| p10/p50/p90 (0.033, 0.158, 0.401) m, 68.7 % within 0.25 m
[ok] fit left: coverage: 51 % of stations (>= 50 %, unpainted side)
[ok] fit left: longest gap: 59 st at (470, 528) (<= 60)
[ok] fit left: waviness: rolling-100 rms max 0.019 m (<= 0.04), peak 0.031 m (<= 0.1) outside tight corners
[ok] fit left: kink: max 0.24 deg/station (<= 0.5) outside tight corners; station 0 0.00
[ok] fit right: unpainted bias: unpainted side (86 % of 6094 associated readings from asphalt_end); 98.0 % of 4662 41-station windows have a median residual within +-0.25 m (>= 90 %); worst +0.361 m at 27 (7..47); 86 % of capture rows have a band within 1.2 m (>= 85 %); spread (printed, not gated): |residual| p10/p50/p90 (0.021, 0.126, 0.365) m, 76.4 % within 0.25 m
[ok] fit right: coverage: 53 % of stations (>= 50 %, unpainted side)
[ok] fit right: longest gap: 41 st at (583, 623) (<= 60)
[ok] fit right: waviness: rolling-100 rms max 0.018 m (<= 0.04), peak 0.028 m (<= 0.1) outside tight corners
[ok] fit right: kink: max 0.26 deg/station (<= 0.5) outside tight corners; station 0 0.00
[ok] painted-midpoint residual: rms 0.14 -> 0.03 m (final refit)
[ok] loop stations: n = 4692
     lap length: 4694.19 m (no official figure in the config: loop_check.official_m is None)
[ok] elevation range: 3.4 m (z0 76.67 NAVD88)
[ok] direction: signed area -368950 m^2, config cw
[ok] start/finish: station 0 is 0.02 m from the configured timing line
[ok] edge jumps: max lateral change between stations: left 0.115 m, right 0.090 m
[ok] cross slope (inner 2/3): max 7.9% at s=2192; 0 stations over 12 % (listed in work/report.json)
[ok] cross slope (edge thirds): max 8.9% at s=2193
[ok] edge gate left : rms vs 41-st median (R>250 m, 2373 st) 0.039 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.078 m at 3688 (next 0.077@3690, 0.077@3685; <= 0.1) | max edge-column cross-section step 0.022 m at 1318
[ok] edge gate right: rms vs 41-st median (R>250 m, 2373 st) 0.043 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.090 m at 2466 (next 0.090@2467, 0.088@2463; <= 0.1) | max edge-column cross-section step 0.020 m at 4401
[ok] world continuity left : max |third difference| of the edge polyline 0.0058 m at station 619 (<= 0.02)
[ok] world continuity right: max |third difference| of the edge polyline 0.0050 m at station 1065 (<= 0.02)
[ok] profile gate: max cross-section step any column 0.022 m at station 1318 column 0 (<= 0.1)
```
Width (report): median 14.40 m, p10 12.23, p90 17.28, min 7.66 m at station 509 (the pit-out merge, where the pit-merge
logic draws the left edge on the cone line), max 19.40 m at 2435. 3.4 % of stations are under 36 ft and 14.8 % over
55 ft. Corners: T1 R 46.9, T2 26.3, T3 43.0, T4 54.2, T5 49.7, T6 134.3, T7 124.0, T8 69.1, T9 32.6, T10 75.2,
T11 44.5 m. Advisory exit overshoots at T1 (+2.63 m), T2 (+3.01), T6 (+1.46) and Star Mazda (+2.65) are for the
hood-sheet review.

**Stage 2 (exit 0):**
```
racing line: no logger laps, pure minimum-curvature line within the edges less 1.0 m (offset range -6.09..+6.80 m)
================ GHOST VALIDATION (no logger) ================
[ok] line inside edges: min clearance to edge 1.03 m
     line curvature: sum k^2 0.1312 vs centre 0.1999
     implied-g checks skipped (no ghost laps): validate with tools/calibrate/drive.ts --track <dir>
wrote ghosts.json: 0.02 MB, racing line only (2346 points)
```

**Published (partial: geometry + ghosts; new builder flag `--publish --partial`, refused over a package with
scenery):**
- `public/tracks/buttonwillow/`: track.json, heightfield.bin, ortho.jpg, ghosts.json.
- Registry entry `buttonwillow`: length_m 4694.187; start at s 4580, speed 22, on the front straight ~115 m before the
  line; rev 5106465b48.
- The rev covers the files the package has. The registry test and the TrackInfo doc now hash the files present; Sonoma's
  rev is unchanged.
- No AI keys. The registry requires a pace file, so `public/cars/field/buttonwillow/pace.json` is the uncalibrated
  `pace_track.ts` build: 6 cars from their own laps, the rest placeholders, with the AI Probe solo lap 145.03 s against
  Laguna 120.20 s. Stage 5 replaces it.
- The inventory was re-mapped on the published package (GPS anchors re-projected; residuals 4.2-25.9 m).

**The 1.10 hood sheet (for the orchestrator's review; not judged here):**
- `compare/buttonwillow/compare_sheets/`: 16 sheets, 94 hood stills every 50 m (`camera_walk.ts --camera hood
  --no-rows --back-step 0 --pit-step 0 --no-runoff`, dev server on 5183, stopped).
- Each still is paired with the onboard 7QS2M-HGSI4 frame at the inventory's mapped time.
- The 94 onboard frames come from a headless Chrome. Two of them (t 60.01, 126.32) were drawn without the
  presented-frame callback, and the worst time mismatch is 0.58 s.
- Local, git-ignored.
