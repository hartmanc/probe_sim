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


## Stage-3 pass (20 Oct 2026): block-line kerb zones (stage 1 again), then scenery from the evidence

The orchestrator's 1.10 review passed (all 16 sheets, 94 pairs), with two items: the pit-out merge and no rule objects.
The three choices stand: `--publish --partial`, the rev over the files present, and the placeholder pace file until
stage 5. This round is the builder's: no judge round of its own.

### Step ledger (0.1-4.5)

| step | status |
|---|---|
| 0.1-0.10 | done in stage 0 and rounds 2-5 (sections above). Inventory re-mapped on this round's package; 5 rows corrected (attrs.correction, below) |
| 1.1-1.9 | stage 1 re-run (runs 16-20) for the pit-out merge line and the block-line kerb zones; run 20 passes every gate (lines below) |
| 1.10 | orchestrator review passed 20 Oct 2026, two items (pit-out merge, no rule objects); whole-lap hood sheet redone on the run-20 geometry for the re-review (`compare_sheets/`, previous in `compare_sheets/before_block_zones/`) |
| 1.11 | derived data rebuilt by the builder after each geometry run (ghosts, scenery) |
| 1.12 | no paved shoulders declared: the paved aprons inside T1, T4-T5 and T11 exit are the block-line question (below) |
| 2.1-2.3 | ghosts re-run on the run-20 geometry: line inside the edges, min clearance 1.00 m; no logger laps, no implied-g table |
| 3.1 | every object names its source in the config (`tracks/buttonwillow/config.py`, scenery) |
| 3.2 | ground from the DEM and lidar (builder) |
| 3.3 | 158 kerb strips from kerb_detect's band reading over -10..+1.5 m (-16 m at T1 exit), in <= 10 m pieces, colour per strip from the onboard row (palettes rwb / wb / red-white) |
| 3.4 | walls from the capture scan (barrier ledger below), heights by HEIGHTS.md (Jersey 0.81 m, tyres 0.8 m) |
| 3.5 | pit lane first-class: OSM 39224587, 4 declared walls, pit-out merge line from the capture |
| 3.6 | 9 closed roads as real surface; the cones at the mouths the onboard shows are declared as cone_lines_declared |
| 3.7 | buildings: the 2 OSM footprints at the timing tower kept on the pit-lane video; 15 lidar paddock structures dropped (no 2026 source) |
| 3.8 | furniture ledger below |
| 3.9 | no boards (none in the onboard); ground-logo scan below |
| 3.10 | no bridges (no OSM bridge=yes crossing) |
| 3.11 | no edge-line paint at Buttonwillow (asphalt to dirt); the builder's rule lines stay |
| 3.12 | every gate through the builder (lines below) |
| 3.13 | dispositions below; manifest_tables.ts run after the round |
| 4.1, 4.2 | hood walk (forward every 50 m) for the re-review; the full-pose walk after stage 3 |
| 4.3 | the orchestrator's judge round (not run by the builder) |
| 4.4 | structure and surveyed-spot stills after stage 3 |
| 4.5 | the owner's lap: not yet |

### Season tint

NAIP June 2022 and the race of 26-27 Sep 2026 are both dry summer ground (pale dust and dry grass on the onboard and the
2026 captures), so `season_tint` stays None.

### Block-line kerb zones (stage 1, runs 17-20)

On Buttonwillow the kerbs are white / red / blue block lines laid on wider pavement. With no paint, asphalt_end fitted
the far side of the paved aprons beyond them. Per SKILL 1.5 the edge is the blocks' outer limit, so each zone gets a
`kerb_band` feature and its own search window (`spline.kerb_search`, new, config-gated). Its stations associate across
the whole window (edges_spline.fit_periodic), and the outer centre refits carry the edge to the blocks.

| zone | evidence | result |
|---|---|---|
| left 540-582 | cw_533, onboard t022 | in: edge on the blocks |
| left 1076-1112 | cw_1086 / n_1086, onboard t044 | in: edge on the blocks (width 8.5-10 m, min 8.46 m at 1079) |
| right 1760-1810 | cw_1751 / n_1785, onboard t066 | in |
| left 3675-3712 | c20_s3800, onboard t124 | in to 3700; the line then runs diagonally to the right edge (T10, below) |
| left 3948-4010 | c20_s4100 / c20_s4150, onboard t132 | in |
| right 4050-4112 | c20_s4150-c20_s4250, onboard t134 / t136 | in (width 18.6-18.9 -> 12.8-13.5 m) |
| right 355-432 (T1 exit) | cw_400ov, cw_t1raw, onboard 0:16-0:18 | **set aside**: run 17 (1.2 m association) left an 81-station gap. In run 19 (association across the window) the right edge reached the blocks, but the left edge did not follow west onto the pale surface: width 0.08 m at 419, cross slope 355 %, kink 0.54, steps 0.13 / 0.19 m (`stage3_evidence/geometry_run19_T1zone.log`) |
| left 1318-1392 | cw_1348, onboard t054 | **set aside**: reached (width down to 8.1 m) but the block line ends at 1387 with the apron edge 4.6 m out, so the edge-gate step fails (0.122 / 0.107 m at 1372-1380) |
| right 4402-4445 (T11 exit) | cw_4430, onboard t144 / t146 | **set aside**: a diagonal line like T1's, from 3.5 m inside the right edge at 4410 to the left edge at 4472, where the existing `('left', 4470, 4501, 'kerb_band')` holds the same blocks as a LEFT edge. With the zone the width fell to 6.8 m, because the left edge sits on a tone step 2-7 m inside the pavement |

The wrong `('left', 393, 432, 'kerb_band')` is dropped: that block line is the right limit of the pale T1-exit surface.
At three places the package still runs on the far side of a diagonal block line from the onboard: T1 exit (s 360-432),
T10 (s 3700-3757) and T11 exit (s 4410-4500). The fit cannot move both edges 5-10 m there; the numbers are above. The
kerb strips of those lines stand where the blocks are, on the side the onboard sees them.

Width against the operator's 10.97-16.76 m (`spline.report_width`, report only):
- before: median 14.10, p10 11.97, p90 16.94, min 7.86 (s 1200), max 19.33 (s 2437); 4.3 % under, 12.0 % over.
- run 20: median 13.98, p10 11.48, p90 16.73, min 8.46 (s 1079), max 19.30 (s 2437); 5.2 % under, 8.5 % over.
- still over 16.76 m: s 0-20, 41-72, 240-248 (front straight and T1 entry, 16.8 m); 1394-1424 (17.7 m, past the set-aside
  1318-1392 block line, the apron); 2272-2290 (16.9); 2398-2468 (19.3 m: T7's wide paved exit on c20_s2450 / c20_s2500,
  no block line); 4135-4161 (17.2: the Zorros mouth fillet); 4241-4258 (16.9); 4518-4691 (16.9: the front straight
  between the pit-wall median and the infield dirt, the declared straight).
- still under 10.97 m: 534-610 (10.2: T2 entry on the block line); 1046-1111 (8.5: T4 on the block line); 2507-2545 (10.1:
  the drag-strip crossing, asphalt end both sides); 2763-2794 (10.8: T8); 3708-3736 (10.6: the T10 diagonal).

### Stage-1 gates (run 20, as the builder prints them)

```
[ok] fit left: unpainted bias: unpainted side (84 % of 6094 associated readings from asphalt_end); 98.4 % of 4603 41-station windows have a median residual within +-0.25 m (>= 90 %); worst -0.784 m at 3707 (3687..3727); 87 % of capture rows have a band within 1.2 m (>= 85 %); spread (printed, not gated): |residual| p10/p50/p90 (0.03, 0.155, 0.401) m, 71.0 % within 0.25 m
[ok] fit left: coverage: 54 % of stations (>= 50 %, unpainted side)
[ok] fit left: longest gap: 38 st at (440, 477) (<= 60)
[ok] fit left: waviness: rolling-100 rms max 0.026 m (<= 0.04), peak 0.041 m (<= 0.1) outside tight corners
[ok] fit left: kink: max 0.31 deg/station (<= 0.5) outside tight corners; station 0 0.00
[ok] fit right: unpainted bias: unpainted side (83 % of 6395 associated readings from asphalt_end); 99.1 % of 4624 41-station windows have a median residual within +-0.25 m (>= 90 %); worst +0.401 m at 2834 (2814..2854); 87 % of capture rows have a band within 1.2 m (>= 85 %); spread (printed, not gated): |residual| p10/p50/p90 (0.02, 0.124, 0.366) m, 75.9 % within 0.25 m
[ok] fit right: coverage: 56 % of stations (>= 50 %, unpainted side)
[ok] fit right: longest gap: 45 st at (583, 627) (<= 60)
[ok] fit right: waviness: rolling-100 rms max 0.025 m (<= 0.04), peak 0.040 m (<= 0.1) outside tight corners
[ok] fit right: kink: max 0.29 deg/station (<= 0.5) outside tight corners; station 0 0.00
[ok] painted-midpoint residual: rms 0.17 -> 0.03 m (final refit)
[ok] loop stations: n = 4692
[ok] elevation range: 3.4 m (z0 76.67 NAVD88)
[ok] direction: signed area -368508 m^2, config cw
[ok] start/finish: station 0 is 0.15 m from the configured timing line
[ok] edge jumps: max lateral change between stations: left 0.096 m, right 0.079 m
[ok] cross slope (inner 2/3): max 9.4% at s=2230; 0 stations over 12 % (listed in work/report.json)
[ok] cross slope (edge thirds): max 10.0% at s=2230
[ok] no NaN: 
[ok] edge gate left : rms vs 41-st median (R>250 m, 2365 st) 0.053 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.093 m at 3232 (next 0.092@3233, 0.092@3231; <= 0.1) | max edge-column cross-section step 0.024 m at 1317
[ok] edge gate right: rms vs 41-st median (R>250 m, 2365 st) 0.045 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.078 m at 1756 (next 0.078@2466, 0.078@1759; <= 0.1) | max edge-column cross-section step 0.021 m at 1318
[ok] world continuity left : max |third difference| of the edge polyline 0.0045 m at station 3434 (<= 0.02)
[ok] world continuity right: max |third difference| of the edge polyline 0.0050 m at station 3471 (<= 0.02)
[ok] profile gate: max cross-section step any column 0.024 m at station 1317 column 0 (<= 0.1)
     report width: median 13.98 m, p10 11.48, p90 16.73, min 8.46 m at station 1079, max 19.30 m at station 2437; 5.2 % of stations under 10.97 m, 8.5 % over 16.76 m
```

### Barrier scan ledger (106 clean captures x 2 sides)

Per capture and side, the barriers of the package within the capture's 80 m. Rows marked "none" were examined for
lines out to the capture edge. The four dark far-line candidates of the round-3 scan are not barriers: T2 outside west
(c20_s0700 / c20_s0750), the east far line (c20_s0800 / c20_s0850), west of the north leg (c20_s3350 / c20_s3400) and
east of Sunset (c20_s4200-c20_s4400) show open runoff on the onboard (compare_sheets/onboard s0700-s0850, s3350,
s3400, s4200-s4350). They are tyre tracks and graded dirt. The station mounds' tyre rings are furniture, and only the
T1-exit ring stands within a metre of the edge (inventory tyre_wall row s 477).

| capture | side | stations | barriers |
|---|---|---|---|
| c20_p0180 | left | s 4267-4451 | none: open dirt or paved runoff out to the capture edge; station mound(s): T11 approach (Sunset) |
| c20_p0180 | right | s 4267-4451 | none: open dirt or paved runoff out to the capture edge |
| c20_p0240 | left | s 4350-4531 | placed: pit lane, paddock side, west; pit wall, front straight |
| c20_p0240 | right | s 4350-4531 | none: open dirt or paved runoff out to the capture edge |
| c20_p0300 | left | s 4439-4593 | placed: pit lane, paddock side, west; pit wall, front straight |
| c20_p0300 | right | s 4439-4593 | none: open dirt or paved runoff out to the capture edge |
| c20_p0360 | left | s 4501-4652 | placed: pit lane, paddock side, west; pit wall, front straight |
| c20_p0360 | right | s 4501-4652 | none: open dirt or paved runoff out to the capture edge |
| c20_p0420 | left | s 4559-15 | placed: pit lane, paddock side, tower; pit lane, paddock side, west; pit wall, front straight; station mound(s): starter's stand |
| c20_p0420 | right | s 4559-15 | none: open dirt or paved runoff out to the capture edge |
| c20_p0480 | left | s 4619-75 | placed: pit lane, paddock side, east; pit lane, paddock side, tower; pit lane, paddock side, west; pit wall, front straight; station mound(s): starter's stand |
| c20_p0480 | right | s 4619-75 | none: open dirt or paved runoff out to the capture edge |
| c20_p0540 | left | s 4679-135 | placed: pit lane, paddock side, east; pit lane, paddock side, tower; pit wall, front straight; station mound(s): starter's stand |
| c20_p0540 | right | s 4679-135 | none: open dirt or paved runoff out to the capture edge |
| c20_p0600 | left | s 42-195 | placed: pit lane, paddock side, east; pit wall, front straight |
| c20_p0600 | right | s 42-195 | none: open dirt or paved runoff out to the capture edge |
| c20_p0660 | left | s 102-255 | placed: pit lane, paddock side, east; pit wall, front straight; station mound(s): pit-wall end hut |
| c20_p0660 | right | s 102-255 | none: open dirt or paved runoff out to the capture edge |
| c20_p0780 | left | s 227-412 | none: open dirt or paved runoff out to the capture edge |
| c20_p0780 | right | s 227-412 | none: open dirt or paved runoff out to the capture edge |
| c20_p0840 | left | s 316-480 | none: open dirt or paved runoff out to the capture edge |
| c20_p0840 | right | s 316-480 | placed: T1-exit station mound tyres |
| c20_s0000 | left | s 4500-4660 | placed: pit lane, paddock side, west; pit wall, front straight |
| c20_s0000 | right | s 4500-4660 | none: open dirt or paved runoff out to the capture edge |
| c20_s0050 | left | s 4551-12 | placed: pit lane, paddock side, tower; pit lane, paddock side, west; pit wall, front straight; station mound(s): starter's stand |
| c20_s0050 | right | s 4551-12 | none: open dirt or paved runoff out to the capture edge |
| c20_s0100 | left | s 4601-62 | placed: pit lane, paddock side, east; pit lane, paddock side, tower; pit lane, paddock side, west; pit wall, front straight; station mound(s): starter's stand |
| c20_s0100 | right | s 4601-62 | none: open dirt or paved runoff out to the capture edge |
| c20_s0150 | left | s 4651-112 | placed: pit lane, paddock side, east; pit lane, paddock side, tower; pit wall, front straight; station mound(s): starter's stand |
| c20_s0150 | right | s 4651-112 | none: open dirt or paved runoff out to the capture edge |
| c20_s0200 | left | s 4-162 | placed: pit lane, paddock side, east; pit lane, paddock side, tower; pit wall, front straight |
| c20_s0200 | right | s 4-162 | none: open dirt or paved runoff out to the capture edge |
| c20_s0250 | left | s 54-212 | placed: pit lane, paddock side, east; pit wall, front straight; station mound(s): pit-wall end hut |
| c20_s0250 | right | s 54-212 | none: open dirt or paved runoff out to the capture edge |
| c20_s0300 | left | s 104-262 | placed: pit lane, paddock side, east; pit wall, front straight; station mound(s): pit-wall end hut |
| c20_s0300 | right | s 104-262 | none: open dirt or paved runoff out to the capture edge |
| c20_s0350 | left | s 154-314 | placed: pit lane, paddock side, east; pit wall, front straight; station mound(s): pit-wall end hut |
| c20_s0350 | right | s 154-314 | none: open dirt or paved runoff out to the capture edge |
| c20_s0400 | left | s 203-361 | placed: pit wall, front straight |
| c20_s0400 | right | s 203-361 | none: open dirt or paved runoff out to the capture edge |
| c20_s0450 | left | s 245-405 | none: open dirt or paved runoff out to the capture edge |
| c20_s0450 | right | s 245-405 | none: open dirt or paved runoff out to the capture edge |
| c20_s0500 | left | s 295-455 | none: open dirt or paved runoff out to the capture edge |
| c20_s0500 | right | s 295-455 | none: open dirt or paved runoff out to the capture edge |
| c20_s0550 | left | s 344-504 | none: open dirt or paved runoff out to the capture edge |
| c20_s0550 | right | s 344-504 | placed: T1-exit station mound tyres; station mound(s): T1 exit |
| c20_s0600 | left | s 395-555 | none: open dirt or paved runoff out to the capture edge |
| c20_s0600 | right | s 395-555 | placed: T1-exit station mound tyres; station mound(s): T1 exit |
| c20_s0650 | left | s 445-714 | none: open dirt or paved runoff out to the capture edge |
| c20_s0650 | right | s 445-714 | placed: T1-exit station mound tyres; station mound(s): T1 exit |
| c20_s0700 | left | s 495-693 | none: open dirt or paved runoff out to the capture edge |
| c20_s0700 | right | s 495-693 | none: open dirt or paved runoff out to the capture edge |
| c20_s0750 | left | s 527-707 | none: open dirt or paved runoff out to the capture edge |
| c20_s0750 | right | s 527-707 | none: open dirt or paved runoff out to the capture edge |
| c20_s0800 | left | s 527-753 | none: open dirt or paved runoff out to the capture edge |
| c20_s0800 | right | s 527-753 | none: open dirt or paved runoff out to the capture edge |
| c20_s0850 | left | s 642-800 | none: open dirt or paved runoff out to the capture edge |
| c20_s0850 | right | s 642-800 | none: open dirt or paved runoff out to the capture edge |
| c20_s0900 | left | s 691-851 | none: open dirt or paved runoff out to the capture edge |
| c20_s0900 | right | s 691-851 | none: open dirt or paved runoff out to the capture edge; station mound(s): T2 to T3, east side |
| c20_s0950 | left | s 741-901 | none: open dirt or paved runoff out to the capture edge |
| c20_s0950 | right | s 741-901 | none: open dirt or paved runoff out to the capture edge; station mound(s): T2 to T3, east side |
| c20_s1000 | left | s 792-951 | none: open dirt or paved runoff out to the capture edge |
| c20_s1000 | right | s 792-951 | none: open dirt or paved runoff out to the capture edge; station mound(s): T2 to T3, east side |
| c20_s1050 | left | s 842-1001 | none: open dirt or paved runoff out to the capture edge |
| c20_s1050 | right | s 842-1001 | none: open dirt or paved runoff out to the capture edge |
| c20_s1100 | left | s 892-1054 | none: open dirt or paved runoff out to the capture edge |
| c20_s1100 | right | s 892-1054 | none: open dirt or paved runoff out to the capture edge; station mound(s): T3 |
| c20_s1150 | left | s 941-1099 | none: open dirt or paved runoff out to the capture edge |
| c20_s1150 | right | s 941-1099 | none: open dirt or paved runoff out to the capture edge; station mound(s): T3 |
| c20_s1200 | left | s 983-1160 | none: open dirt or paved runoff out to the capture edge |
| c20_s1200 | right | s 983-1160 | none: open dirt or paved runoff out to the capture edge; station mound(s): T3 |
| c20_s1250 | left | s 1036-1208 | none: open dirt or paved runoff out to the capture edge |
| c20_s1250 | right | s 1036-1208 | none: open dirt or paved runoff out to the capture edge; station mound(s): T4 |
| c20_s1300 | left | s 1092-1253 | none: open dirt or paved runoff out to the capture edge |
| c20_s1300 | right | s 1092-1253 | none: open dirt or paved runoff out to the capture edge; station mound(s): T4 |
| c20_s1350 | left | s 1140-1301 | none: open dirt or paved runoff out to the capture edge |
| c20_s1350 | right | s 1140-1301 | none: open dirt or paved runoff out to the capture edge; station mound(s): T4 |
| c20_s1400 | left | s 1191-1352 | none: open dirt or paved runoff out to the capture edge |
| c20_s1400 | right | s 1191-1352 | none: open dirt or paved runoff out to the capture edge |
| c20_s1450 | left | s 1236-1399 | none: open dirt or paved runoff out to the capture edge |
| c20_s1450 | right | s 1236-1399 | none: open dirt or paved runoff out to the capture edge |
| c20_s1500 | left | s 1287-1449 | none: open dirt or paved runoff out to the capture edge |
| c20_s1500 | right | s 1287-1449 | none: open dirt or paved runoff out to the capture edge |
| c20_s1550 | left | s 1340-1499 | none: open dirt or paved runoff out to the capture edge |
| c20_s1550 | right | s 1340-1499 | none: open dirt or paved runoff out to the capture edge; station mound(s): T5 |
| c20_s1600 | left | s 1390-1550 | none: open dirt or paved runoff out to the capture edge |
| c20_s1600 | right | s 1390-1550 | none: open dirt or paved runoff out to the capture edge; station mound(s): T5 |
| c20_s1650 | left | s 1438-1598 | none: open dirt or paved runoff out to the capture edge |
| c20_s1650 | right | s 1438-1598 | none: open dirt or paved runoff out to the capture edge; station mound(s): T5 |
| c20_s1700 | left | s 1488-1649 | none: open dirt or paved runoff out to the capture edge |
| c20_s1700 | right | s 1488-1649 | none: open dirt or paved runoff out to the capture edge; station mound(s): T5 |
| c20_s1750 | left | s 1539-1703 | none: open dirt or paved runoff out to the capture edge |
| c20_s1750 | right | s 1539-1703 | none: open dirt or paved runoff out to the capture edge |
| c20_s1800 | left | s 1589-1754 | none: open dirt or paved runoff out to the capture edge |
| c20_s1800 | right | s 1589-1754 | none: open dirt or paved runoff out to the capture edge |
| c20_s1850 | left | s 1644-1804 | none: open dirt or paved runoff out to the capture edge |
| c20_s1850 | right | s 1644-1804 | none: open dirt or paved runoff out to the capture edge |
| c20_s1900 | left | s 1695-1856 | none: open dirt or paved runoff out to the capture edge |
| c20_s1900 | right | s 1695-1856 | none: open dirt or paved runoff out to the capture edge |
| c20_s1950 | left | s 1745-1904 | none: open dirt or paved runoff out to the capture edge |
| c20_s1950 | right | s 1745-1904 | none: open dirt or paved runoff out to the capture edge |
| c20_s2000 | left | s 1792-1951 | none: open dirt or paved runoff out to the capture edge |
| c20_s2000 | right | s 1792-1951 | none: open dirt or paved runoff out to the capture edge |
| c20_s2050 | left | s 1842-2002 | none: open dirt or paved runoff out to the capture edge |
| c20_s2050 | right | s 1842-2002 | none: open dirt or paved runoff out to the capture edge |
| c20_s2100 | left | s 1893-2054 | none: open dirt or paved runoff out to the capture edge |
| c20_s2100 | right | s 1893-2054 | none: open dirt or paved runoff out to the capture edge |
| c20_s2150 | left | s 1943-2103 | none: open dirt or paved runoff out to the capture edge |
| c20_s2150 | right | s 1943-2103 | none: open dirt or paved runoff out to the capture edge; station mound(s): T6 (Riverside) |
| c20_s2200 | left | s 1994-2153 | none: open dirt or paved runoff out to the capture edge |
| c20_s2200 | right | s 1994-2153 | none: open dirt or paved runoff out to the capture edge; station mound(s): T6 (Riverside) |
| c20_s2250 | left | s 2044-2204 | none: open dirt or paved runoff out to the capture edge |
| c20_s2250 | right | s 2044-2204 | none: open dirt or paved runoff out to the capture edge; station mound(s): T6 (Riverside) |
| c20_s2300 | left | s 2093-2253 | none: open dirt or paved runoff out to the capture edge |
| c20_s2300 | right | s 2093-2253 | none: open dirt or paved runoff out to the capture edge |
| c20_s2350 | left | s 2143-2302 | none: open dirt or paved runoff out to the capture edge |
| c20_s2350 | right | s 2143-2302 | none: open dirt or paved runoff out to the capture edge |
| c20_s2400 | left | s 2193-2351 | none: open dirt or paved runoff out to the capture edge |
| c20_s2400 | right | s 2193-2351 | none: open dirt or paved runoff out to the capture edge |
| c20_s2450 | left | s 2241-2400 | none: open dirt or paved runoff out to the capture edge |
| c20_s2450 | right | s 2241-2400 | none: open dirt or paved runoff out to the capture edge; station mound(s): T7 |
| c20_s2500 | left | s 2290-2450 | none: open dirt or paved runoff out to the capture edge |
| c20_s2500 | right | s 2290-2450 | none: open dirt or paved runoff out to the capture edge; station mound(s): T7 |
| c20_s2550 | left | s 2340-2500 | none: open dirt or paved runoff out to the capture edge |
| c20_s2550 | right | s 2340-2500 | none: open dirt or paved runoff out to the capture edge; station mound(s): T7 |
| c20_s2600 | left | s 2390-2553 | none: open dirt or paved runoff out to the capture edge |
| c20_s2600 | right | s 2390-2553 | none: open dirt or paved runoff out to the capture edge |
| c20_s2650 | left | s 2441-2603 | none: open dirt or paved runoff out to the capture edge |
| c20_s2650 | right | s 2441-2603 | none: open dirt or paved runoff out to the capture edge |
| c20_s2700 | left | s 2492-2653 | none: open dirt or paved runoff out to the capture edge |
| c20_s2700 | right | s 2492-2653 | none: open dirt or paved runoff out to the capture edge |
| c20_s2750 | left | s 2544-2703 | none: open dirt or paved runoff out to the capture edge |
| c20_s2750 | right | s 2544-2703 | none: open dirt or paved runoff out to the capture edge |
| c20_s2800 | left | s 2594-2753 | none: open dirt or paved runoff out to the capture edge |
| c20_s2800 | right | s 2594-2753 | none: open dirt or paved runoff out to the capture edge |
| c20_s2850 | left | s 2644-2805 | none: open dirt or paved runoff out to the capture edge |
| c20_s2850 | right | s 2644-2805 | none: open dirt or paved runoff out to the capture edge; station mound(s): T8 |
| c20_s2900 | left | s 2691-2851 | none: open dirt or paved runoff out to the capture edge |
| c20_s2900 | right | s 2691-2851 | none: open dirt or paved runoff out to the capture edge; station mound(s): T8 |
| c20_s2950 | left | s 2740-2901 | none: open dirt or paved runoff out to the capture edge |
| c20_s2950 | right | s 2740-2901 | none: open dirt or paved runoff out to the capture edge; station mound(s): T8 |
| c20_s3000 | left | s 2791-2951 | none: open dirt or paved runoff out to the capture edge |
| c20_s3000 | right | s 2791-2951 | none: open dirt or paved runoff out to the capture edge |
| c20_s3050 | left | s 2842-3002 | none: open dirt or paved runoff out to the capture edge |
| c20_s3050 | right | s 2842-3002 | none: open dirt or paved runoff out to the capture edge |
| c20_s3100 | left | s 2892-3053 | none: open dirt or paved runoff out to the capture edge |
| c20_s3100 | right | s 2892-3053 | none: open dirt or paved runoff out to the capture edge |
| c20_s3150 | left | s 2942-3103 | none: open dirt or paved runoff out to the capture edge |
| c20_s3150 | right | s 2942-3103 | none: open dirt or paved runoff out to the capture edge |
| c20_s3200 | left | s 2994-3153 | none: open dirt or paved runoff out to the capture edge |
| c20_s3200 | right | s 2994-3153 | none: open dirt or paved runoff out to the capture edge |
| c20_s3250 | left | s 3044-3203 | none: open dirt or paved runoff out to the capture edge |
| c20_s3250 | right | s 3044-3203 | none: open dirt or paved runoff out to the capture edge; station mound(s): north leg before T9 |
| c20_s3300 | left | s 3094-3254 | none: open dirt or paved runoff out to the capture edge |
| c20_s3300 | right | s 3094-3254 | none: open dirt or paved runoff out to the capture edge; station mound(s): north leg before T9 |
| c20_s3350 | left | s 3144-3304 | none: open dirt or paved runoff out to the capture edge |
| c20_s3350 | right | s 3144-3304 | none: open dirt or paved runoff out to the capture edge; station mound(s): north leg before T9 |
| c20_s3400 | left | s 3194-3354 | none: open dirt or paved runoff out to the capture edge |
| c20_s3400 | right | s 3194-3354 | none: open dirt or paved runoff out to the capture edge |
| c20_s3450 | left | s 3244-3407 | none: open dirt or paved runoff out to the capture edge |
| c20_s3450 | right | s 3244-3407 | none: open dirt or paved runoff out to the capture edge |
| c20_s3500 | left | s 3295-3492 | none: open dirt or paved runoff out to the capture edge |
| c20_s3500 | right | s 3295-3492 | none: open dirt or paved runoff out to the capture edge; station mound(s): T9 (Star Mazda) |
| c20_s3550 | left | s 3337-3514 | none: open dirt or paved runoff out to the capture edge |
| c20_s3550 | right | s 3337-3514 | none: open dirt or paved runoff out to the capture edge; station mound(s): T9 (Star Mazda) |
| c20_s3600 | left | s 3377-3558 | none: open dirt or paved runoff out to the capture edge |
| c20_s3600 | right | s 3377-3558 | none: open dirt or paved runoff out to the capture edge; station mound(s): T9 (Star Mazda) |
| c20_s3650 | left | s 3449-3609 | none: open dirt or paved runoff out to the capture edge |
| c20_s3650 | right | s 3449-3609 | none: open dirt or paved runoff out to the capture edge |
| c20_s3700 | left | s 3498-3657 | none: open dirt or paved runoff out to the capture edge |
| c20_s3700 | right | s 3498-3657 | none: open dirt or paved runoff out to the capture edge |
| c20_s3750 | left | s 3547-3705 | none: open dirt or paved runoff out to the capture edge |
| c20_s3750 | right | s 3547-3705 | none: open dirt or paved runoff out to the capture edge; station mound(s): T10 |
| c20_s3800 | left | s 3596-3756 | none: open dirt or paved runoff out to the capture edge |
| c20_s3800 | right | s 3596-3756 | none: open dirt or paved runoff out to the capture edge; station mound(s): T10 |
| c20_s3850 | left | s 3646-3807 | none: open dirt or paved runoff out to the capture edge |
| c20_s3850 | right | s 3646-3807 | none: open dirt or paved runoff out to the capture edge; station mound(s): T10 |
| c20_s3900 | left | s 3696-3857 | none: open dirt or paved runoff out to the capture edge |
| c20_s3900 | right | s 3696-3857 | none: open dirt or paved runoff out to the capture edge; station mound(s): T10 |
| c20_s3950 | left | s 3747-3908 | none: open dirt or paved runoff out to the capture edge |
| c20_s3950 | right | s 3747-3908 | none: open dirt or paved runoff out to the capture edge |
| c20_s4000 | left | s 3797-3958 | none: open dirt or paved runoff out to the capture edge |
| c20_s4000 | right | s 3797-3958 | none: open dirt or paved runoff out to the capture edge |
| c20_s4050 | left | s 3848-4009 | none: open dirt or paved runoff out to the capture edge |
| c20_s4050 | right | s 3848-4009 | none: open dirt or paved runoff out to the capture edge |
| c20_s4100 | left | s 3899-4061 | none: open dirt or paved runoff out to the capture edge |
| c20_s4100 | right | s 3899-4061 | none: open dirt or paved runoff out to the capture edge |
| c20_s4150 | left | s 3949-4111 | none: open dirt or paved runoff out to the capture edge |
| c20_s4150 | right | s 3949-4111 | none: open dirt or paved runoff out to the capture edge |
| c20_s4200 | left | s 4001-4161 | none: open dirt or paved runoff out to the capture edge |
| c20_s4200 | right | s 4001-4161 | none: open dirt or paved runoff out to the capture edge |
| c20_s4250 | left | s 4051-4211 | none: open dirt or paved runoff out to the capture edge |
| c20_s4250 | right | s 4051-4211 | none: open dirt or paved runoff out to the capture edge |
| c20_s4300 | left | s 4102-4261 | none: open dirt or paved runoff out to the capture edge |
| c20_s4300 | right | s 4102-4261 | none: open dirt or paved runoff out to the capture edge |
| c20_s4350 | left | s 4152-4311 | none: open dirt or paved runoff out to the capture edge; station mound(s): T11 approach (Sunset) |
| c20_s4350 | right | s 4152-4311 | none: open dirt or paved runoff out to the capture edge |
| c20_s4400 | left | s 4202-4361 | none: open dirt or paved runoff out to the capture edge; station mound(s): T11 approach (Sunset) |
| c20_s4400 | right | s 4202-4361 | none: open dirt or paved runoff out to the capture edge |
| c20_s4450 | left | s 4252-4418 | none: open dirt or paved runoff out to the capture edge; station mound(s): T11 approach (Sunset) |
| c20_s4450 | right | s 4252-4418 | none: open dirt or paved runoff out to the capture edge |
| c20_s4500 | left | s 4301-4461 | none: open dirt or paved runoff out to the capture edge |
| c20_s4500 | right | s 4301-4461 | none: open dirt or paved runoff out to the capture edge |
| c20_s4550 | left | s 4343-4508 | none: open dirt or paved runoff out to the capture edge |
| c20_s4550 | right | s 4343-4508 | none: open dirt or paved runoff out to the capture edge |
| c20_s4600 | left | s 4397-4558 | placed: pit lane, paddock side, west; pit wall, front straight |
| c20_s4600 | right | s 4397-4558 | none: open dirt or paved runoff out to the capture edge |
| c20_s4650 | left | s 4448-4608 | placed: pit lane, paddock side, west; pit wall, front straight |
| c20_s4650 | right | s 4448-4608 | none: open dirt or paved runoff out to the capture edge |
| c20_s4700 | left | s 4499-4658 | placed: pit lane, paddock side, west; pit wall, front straight |
| c20_s4700 | right | s 4499-4658 | none: open dirt or paved runoff out to the capture edge |

### Station ledger (one row per corner)

| corner | s | station | evidence |
|---|---|---|---|
| T1 | 286 | T1 exit, s 481 right (also the pit-wall end hut s 199 left and the starter's stand s 3 left) | c20_s0600 / c20_s0650 roof 5.5 m2 in a tyre ring; onboard t020 |
| T2 | 609 | T2 to T3, east side, s 818 right | c20_s0900 roof 5.7 m2; onboard t034 |
| T3 | 1029 | T3, s 1013 right | c20_s1100 / c20_s1150; onboard t040 |
| T4 | 1163 | T4, s 1176 right | c20_s1300; onboard t046 |
| T5 | 1498 | T5, s 1492 right | c20_s1600; onboard t058 |
| T6 | 2141 | T6 (Riverside), s 2069 right | c20_s2150; onboard t074 |
| T7 | 2283 | T7, s 2357 right | c20_s2450; onboard t082 |
| T8 | 2773 | T8, s 2763 right | c20_s2850 / c20_s2900; onboard t092 |
| T9 | 3432 | T9 (Star Mazda), s 3420 right (and the north-leg station s 3189 right) | c20_s3300-c20_s3550; onboard t112 |
| T10 | 3842 | T10, s 3697 right | c20_s3800; onboard t122 |
| T11 | 4377 | T11 approach (Sunset), s 4271 left | c20_s4400; onboard t138 |

All 11 corners have a station: a white roof in a dark tyre ring on its mound (compare/blob_scan.py over every capture).

### Furniture ledger

| kind | placed | evidence / why not |
|---|---|---|
| masts | 1: OSM communications tower 10220517717, 49.5 m | lidar spike 49.5-49.7 m (30 cells); onboard t106 pole ahead (row corrected to s 3439). A line of 13-15 m lidar spikes 250 m east of the north leg (ENU x -190, y 513-862) is not resolvable as masts on any capture, so none placed |
| tyre stacks | 0 free-standing | the station mounds' tyre rings: the T1-exit ring placed as a tyre face (declared wall); the other 11 stand 7-19 m off the edges and are drawn with the huts, not as barriers |
| blocks | 0 free-standing | the white / red / blue blocks are kerbs (kerbs_declared) |
| cones | 13 single cones (cone_lines_declared) | onboard rows t002-t150; the small-cone line at s 770 left is not resolvable (disposition) |
| delineators | 0 | none in the onboard |
| huts | 14 | 12 corner stations (the 11 corners and the north leg), the pit-wall end hut, the starter's stand |

### Ground-logo scan (3.9)

All 106 clean captures were examined on the 12 overlay scan sheets (`compare/buttonwillow/scan_sheets/`): the c20_s*
set every 50 m round the lap and the c20_p* set along the pit lane, both sides out to the capture edge. No painted ground
logo or text was seen, so `ground_signs` stays empty. The onboard shows none either.

### Inventory corrections (attrs.correction, this round)

- t004 building left: ahead_m 52. The tower stands abeam the timing line.
- t066 kerb right: ahead_m 20. The block line starts 20 m ahead.
- t068 kerb left: ahead_m 15. The hood hides the first ~10-15 m of ground.
- t106 mast: ahead_m 250 -> 289, at the communications tower.
- pit row s 4497 wall right: s 4510. The wall head on the captures; this video's dot fits +-30 m.

### Dispositions (3.13)

| kind | side | s (m) | what | source | disposition |
|---|---|---|---|---|---|
| station | left | 246 | canopy on posts over a low concrete platform | onboard t010 (ahead 60 m) | placed: pit-wall end hut (s 199 left; the time map's +-30 m and the frame's look-ahead) |
| station | right | 834 | corner station, canopy on a tyre-walled mound | onboard t034 (ahead 40 m) | placed: T2 to T3, east side (s 818 right, 16 m: time-map error) |
| station | right | 996 | corner station, blue canopy | onboard t040 | placed: T3 (s 1013 right, 17 m: time-map error) |
| station | right | 1525 | corner station on a tyre-walled mound | onboard t058 (ahead 30 m) | placed: T5 (s 1492 right, 33 m: the frame's look-ahead and the time map) |
| station | right | 2054 | corner station on a tyre-walled mound | onboard t074 (ahead 40 m) | placed: T6 (s 2069 right, 15.5 m: time-map error) |
| station | right | 3758 | corner station | onboard t122 (ahead 120 m) | placed: T10 (s 3697 right; the 120 m look-ahead was estimated by eye) |
| cone_line | left | 770 | line of small cones | onboard t030 (ahead 80 m), s0700 | not resolvable: c20_s0800, c20_s0850, c20_s0900 show no cones beside s 740-800 left (temporary); the line is too small on t030 / s0700 to place along the track |
| mast | ahead | 3438 | tall pole | onboard t106 | placed: OSM man_made=mast (the 49.5 m communications tower, s 3439 left, ~400 m off; the pole on t106 is most likely it) |

### Generated tables (manifest_tables.ts on the published package, rev 109a9acd5a)

###### Scenery objects of the checked kinds (193, from public/tracks/buttonwillow)

| # | kind | side | s (m) | out (m) | object | source |
|---|---|---|---|---|---|---|
| 1 | wall | left | 4514-206 (wraps) | 3-9 | barrier 0 (concrete) | declared: pit wall, front straight (wall_measure.py --edge left 4490-4693 (88 % picked, offset p50 3.56 m) and 0-300 (75 %, p50 3.74 m) on c20_s4550..c20_s0300; onboard t000-t008, t148-t158 (white K-rail with red panels); pit-lane video 20:40-22:28 (on the right of the lane)) |
| 2 | wall | left | 4527-4650 | 21-23 | barrier 1 (concrete) | declared: pit lane, paddock side, west (wall_measure.py --edge left 4490-4693 --off 12,30 (68 % picked, 20.8 m beyond the left edge) on c20_s4600 / c20_p0360; pit-lane video 20:49-21:52 (Jersey wall on the left of the lane)) |
| 3 | wall | left | 4662-40 (wraps) | 21-22 | barrier 2 (concrete) | declared: pit lane, paddock side, tower (wall_measure.py --edge left (175-210 m and 0-42 m runs, 21 m beyond the left edge) on c20_p0420 / c20_p0480; pit-lane video 21:52 (the wall at the tower, a yellow cone at its foot)) |
| 4 | wall | left | 54-174 | 20-21 | barrier 3 (concrete) | declared: pit lane, paddock side, east (wall_measure.py --edge left 0-300 --off 12,30 (54-196 m run, 21 m beyond the left edge) on c20_p0540 / c20_p0600) |
| 5 | tyre_wall | right | 474-490 | 1-4 | barrier 4 (tyres) | declared: T1-exit station mound tyres (onboard t020 (0:20); c20_s0600 / c20_s0650 (the tyre ring round the station roof); position: 0.8 m beyond the fitted right edge at s 474-488, the mound face) |
| 6 | kerb | left | 537-544 | 0-0 | kerb 536.7-543.7 | left s 536-543: block line read across the normal (edges_spline.bands outer limit, -10..+1.5 m) on c20_s0650 / c20_s0700; colour: t022.jpg (red / white / blue; inventory row s 533 left) |
| 7 | kerb | left | 545-553 | 0-0 | kerb 544.7-552.7 | left s 544-552: block line read across the normal (edges_spline.bands outer limit, -10..+1.5 m) on c20_s0650 / c20_s0700; colour: t022.jpg (red / white / blue; inventory row s 533 left) |
| 8 | kerb | left | 3718-3722 | 0-0 | kerb 3717.6-3721.6 | left s 3713-3717: the T10 block line running diagonally from the left edge (s 3695) toward the right edge (s 3735), read across the normal (edges_spline.bands outer limit, -13..+1.5 m) on c20_s3850; colour: t124.jpg (red / white / blue; inventory row s 3715 left) |
| 9 | kerb | left | 3723-3727 | 0-0 | kerb 3722.6-3726.6 | left s 3718-3722: the T10 block line running diagonally from the left edge (s 3695) toward the right edge (s 3735), read across the normal (edges_spline.bands outer limit, -13..+1.5 m) on c20_s3850; colour: t124.jpg (red / white / blue; inventory row s 3715 left) |
| 10 | kerb | left | 3728-3732 | 0-0 | kerb 3727.6-3731.6 | left s 3723-3727: the T10 block line running diagonally from the left edge (s 3695) toward the right edge (s 3735), read across the normal (edges_spline.bands outer limit, -13..+1.5 m) on c20_s3850; colour: t124.jpg (red / white / blue; inventory row s 3715 left) |
| 11 | kerb | left | 280-289 | 0-0 | kerb 280.3-289.4 | left s 280-289: kerb_detect band reading, offsets -1.1..-0.7 m (piece of the run s 280-322) on c20_s0400; colour: t014.jpg (red / white / blue; inventory row s 301 left) |
| 12 | kerb | left | 290-299 | 0-0 | kerb 290.4-299.4 | left s 290-299: kerb_detect band reading, offsets -0.6..-0.2 m (piece of the run s 280-322) on c20_s0400; colour: t014.jpg (red / white / blue; inventory row s 301 left) |
| 13 | kerb | left | 300-309 | 0-0 | kerb 300.4-309.4 | left s 300-309: kerb_detect band reading, offsets -0.4..-0.2 m (piece of the run s 280-322) on c20_s0400, c20_s0450; colour: t014.jpg (red / white / blue; inventory row s 301 left) |
| 14 | kerb | left | 310-319 | 0-0 | kerb 310.4-319.4 | left s 310-319: kerb_detect band reading, offsets -0.7..-0.4 m (piece of the run s 280-322) on c20_s0450; colour: t014.jpg (red / white / blue; inventory row s 301 left) |
| 15 | kerb | left | 554-559 | 0-0 | kerb 553.7-558.7 | left s 554-559: kerb_detect band reading, offsets -3.4..-2.5 m (piece of the run s 554-559) on c20_s0700; colour: t022.jpg (red / white / blue; inventory row s 533 left) |
| 16 | kerb | left | 582-591 | 0-0 | kerb 581.7-590.7 | left s 582-591: kerb_detect band reading, offsets -4.1..-0.9 m (piece of the run s 582-606) on c20_s0700; colour: colour unverified: no inventory kerb row on that side within 40 m of s 582-591 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 17 | kerb | left | 744-750 | 0-0 | kerb 743.9-749.9 | left s 744-750: kerb_detect band reading, offsets -0.4..-0.3 m (piece of the run s 744-750) on c20_s0850, c20_s0900; colour: t032.jpg (white / red; inventory row s 738 left) |
| 18 | kerb | left | 942-951 | 0-0 | kerb 942.2-951.2 | left s 942-951: kerb_detect band reading, offsets -1.1..-0.6 m (piece of the run s 942-1004) on c20_s1050, c20_s1100; colour: t038.jpg (white / red; inventory row s 973 left) |
| 19 | kerb | left | 952-961 | 0-0 | kerb 952.2-961.2 | left s 952-961: kerb_detect band reading, offsets -0.6..-0.6 m (piece of the run s 942-1004) on c20_s1100; colour: t038.jpg (white / red; inventory row s 973 left) |
| 20 | kerb | left | 962-971 | 0-0 | kerb 962.2-971.2 | left s 962-971: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 942-1004) on c20_s1100; colour: t038.jpg (white / red; inventory row s 973 left) |
| 21 | kerb | left | 972-981 | 0-0 | kerb 972.2-981.2 | left s 972-981: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 942-1004) on c20_s1100; colour: t038.jpg (white / red; inventory row s 973 left) |
| 22 | kerb | left | 982-991 | 0-0 | kerb 982.2-991.2 | left s 982-991: kerb_detect band reading, offsets -0.7..-0.6 m (piece of the run s 942-1004) on c20_s1100; colour: t040.jpg (red / white / blue; inventory row s 996 left) |
| 23 | kerb | left | 992-1001 | 0-0 | kerb 992.2-1001.2 | left s 992-1001: kerb_detect band reading, offsets -0.7..-0.6 m (piece of the run s 942-1004) on c20_s1100, c20_s1150; colour: t040.jpg (red / white / blue; inventory row s 996 left) |
| 24 | kerb | left | 1080-1089 | 0-0 | kerb 1080.3-1089.3 | left s 1080-1089: kerb_detect band reading, offsets -0.7..+0.1 m (piece of the run s 1080-1092) on c20_s1200; colour: t044.jpg (red / white / blue; inventory row s 1086 left) |
| 25 | kerb | left | 1102-1111 | 0-0 | kerb 1102.4-1111.4 | left s 1102-1111: kerb_detect band reading, offsets -0.7..-0.2 m (piece of the run s 1102-1111) on c20_s1250; colour: t044.jpg (red / white / blue; inventory row s 1086 left) |
| 26 | kerb | left | 1195-1204 | 0-0 | kerb 1194.5-1203.5 | left s 1194-1203: kerb_detect band reading, offsets +0.4..+0.8 m (piece of the run s 1194-1206) on c20_s1300, c20_s1350; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 27 | kerb | left | 1238-1247 | 0-0 | kerb 1237.5-1246.5 | left s 1238-1247: kerb_detect band reading, offsets -1.6..-0.1 m (piece of the run s 1238-1262) on c20_s1350, c20_s1400; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 28 | kerb | left | 1248-1257 | 0-0 | kerb 1247.5-1256.5 | left s 1248-1257: kerb_detect band reading, offsets -1.8..-0.6 m (piece of the run s 1238-1262) on c20_s1400; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 29 | kerb | left | 1258-1262 | 0-0 | kerb 1257.5-1261.6 | left s 1258-1262: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 1238-1262) on c20_s1400; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 30 | kerb | left | 1327-1336 | 0-0 | kerb 1326.6-1335.6 | left s 1327-1336: kerb_detect band reading, offsets -9.6..-9.2 m (piece of the run s 1327-1390) on c20_s1450; colour: t054.jpg (red / white / blue; inventory row s 1348 left) |
| 31 | kerb | left | 1337-1346 | 0-0 | kerb 1336.6-1345.7 | left s 1337-1346: kerb_detect band reading, offsets -9.8..-9.6 m (piece of the run s 1327-1390) on c20_s1450, c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1348 left) |
| 32 | kerb | left | 1347-1356 | 0-0 | kerb 1346.7-1355.7 | left s 1347-1356: kerb_detect band reading, offsets -9.8..-8.9 m (piece of the run s 1327-1390) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1348 left) |
| 33 | kerb | left | 1357-1366 | 0-0 | kerb 1356.7-1365.7 | left s 1357-1366: kerb_detect band reading, offsets -8.8..-7.3 m (piece of the run s 1327-1390) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1348 left) |
| 34 | kerb | left | 1367-1376 | 0-0 | kerb 1366.7-1375.7 | left s 1367-1376: kerb_detect band reading, offsets -7.1..-5.8 m (piece of the run s 1327-1390) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1348 left) |
| 35 | kerb | left | 1377-1386 | 0-0 | kerb 1376.7-1385.7 | left s 1377-1386: kerb_detect band reading, offsets -5.7..-4.8 m (piece of the run s 1327-1390) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1348 left) |
| 36 | kerb | left | 1387-1390 | 0-0 | kerb 1386.7-1389.7 | left s 1387-1390: kerb_detect band reading, offsets -4.9..-4.8 m (piece of the run s 1327-1390) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1348 left) |
| 37 | kerb | left | 1435-1444 | 0-0 | kerb 1434.8-1443.8 | left s 1435-1444: kerb_detect band reading, offsets -2.7..-2.2 m (piece of the run s 1425-1474) on c20_s1550, c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1435-1444 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 38 | kerb | left | 1445-1454 | 0-0 | kerb 1444.8-1453.8 | left s 1445-1454: kerb_detect band reading, offsets -2.1..-1.7 m (piece of the run s 1425-1474) on c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1445-1454 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 39 | kerb | left | 1455-1464 | 0-0 | kerb 1454.8-1463.8 | left s 1455-1464: kerb_detect band reading, offsets -1.6..-1.5 m (piece of the run s 1425-1474) on c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1455-1464 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 40 | kerb | left | 1465-1474 | 0-0 | kerb 1464.8-1473.8 | left s 1465-1474: kerb_detect band reading, offsets -1.6..-1.4 m (piece of the run s 1425-1474) on c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1465-1474 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 41 | kerb | left | 1530-1539 | 0-0 | kerb 1529.9-1538.9 | left s 1530-1539: kerb_detect band reading, offsets -2.3..-1.9 m (piece of the run s 1530-1566) on c20_s1650; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1530-1539 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 42 | kerb | left | 1540-1549 | 0-0 | kerb 1539.9-1548.9 | left s 1540-1549: kerb_detect band reading, offsets -1.9..-1.8 m (piece of the run s 1530-1566) on c20_s1650, c20_s1700; colour: t060.jpg (red / white; inventory row s 1580 left) |
| 43 | kerb | left | 1550-1559 | 0-0 | kerb 1549.9-1558.9 | left s 1550-1559: kerb_detect band reading, offsets -1.9..-1.8 m (piece of the run s 1530-1566) on c20_s1700; colour: t060.jpg (red / white; inventory row s 1580 left) |
| 44 | kerb | left | 1560-1566 | 0-0 | kerb 1559.9-1565.9 | left s 1560-1566: kerb_detect band reading, offsets -2.0..-1.6 m (piece of the run s 1530-1566) on c20_s1700; colour: t060.jpg (red / white; inventory row s 1580 left) |
| 45 | kerb | left | 1638-1647 | 0-0 | kerb 1638-1647 | left s 1638-1647: kerb_detect band reading, offsets -0.2..+0.1 m (piece of the run s 1638-1672) on c20_s1750, c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 46 | kerb | left | 1648-1657 | 0-0 | kerb 1648-1657 | left s 1648-1657: kerb_detect band reading, offsets -0.5..-0.3 m (piece of the run s 1638-1672) on c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 47 | kerb | left | 1658-1667 | 0-0 | kerb 1658-1667.1 | left s 1658-1667: kerb_detect band reading, offsets -0.5..-0.5 m (piece of the run s 1638-1672) on c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 48 | kerb | left | 1668-1672 | 0-0 | kerb 1668.1-1672.1 | left s 1668-1672: kerb_detect band reading, offsets -0.5..-0.5 m (piece of the run s 1638-1672) on c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 49 | kerb | left | 1839-1845 | 0-0 | kerb 1839.3-1845.3 | left s 1839-1845: kerb_detect band reading, offsets -6.5..-5.9 m (piece of the run s 1839-1845) on c20_s1950; colour: t068.jpg (red / white / blue; inventory row s 1824 left) |
| 50 | kerb | left | 2516-2525 | 0-0 | kerb 2516.1-2525.1 | left s 2516-2525: kerb_detect band reading, offsets -0.2..+0.8 m (piece of the run s 2516-2535) on c20_s2650; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2516-2525 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 51 | kerb | left | 2526-2535 | 0-0 | kerb 2526.1-2535.1 | left s 2526-2535: kerb_detect band reading, offsets -0.9..-0.3 m (piece of the run s 2516-2535) on c20_s2650; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2526-2535 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 52 | kerb | left | 2670-2679 | 0-0 | kerb 2670.3-2679.3 | left s 2670-2679: kerb_detect band reading, offsets -0.2..+0.4 m (piece of the run s 2670-2737) on c20_s2800; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 53 | kerb | left | 2680-2689 | 0-0 | kerb 2680.3-2689.3 | left s 2680-2689: kerb_detect band reading, offsets -0.3..+0.0 m (piece of the run s 2670-2737) on c20_s2800; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 54 | kerb | left | 2690-2699 | 0-0 | kerb 2690.3-2699.3 | left s 2690-2699: kerb_detect band reading, offsets -0.6..-0.3 m (piece of the run s 2670-2737) on c20_s2800, c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 55 | kerb | left | 2700-2709 | 0-0 | kerb 2700.3-2709.3 | left s 2700-2709: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 2670-2737) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 56 | kerb | left | 2710-2719 | 0-0 | kerb 2710.3-2719.3 | left s 2710-2719: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 2670-2737) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 57 | kerb | left | 2720-2729 | 0-0 | kerb 2720.3-2729.4 | left s 2720-2729: kerb_detect band reading, offsets -0.6..-0.6 m (piece of the run s 2670-2737) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 58 | kerb | left | 2730-2737 | 0-0 | kerb 2730.4-2737.4 | left s 2730-2737: kerb_detect band reading, offsets -0.6..-0.1 m (piece of the run s 2670-2737) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 59 | kerb | left | 2994-3003 | 0-0 | kerb 2993.7-3002.7 | left s 2994-3003: kerb_detect band reading, offsets -0.6..+0.0 m (piece of the run s 2994-3005) on c20_s3100, c20_s3150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2994-3003 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 60 | kerb | left | 3108-3115 | 0-0 | kerb 3107.8-3114.8 | left s 3108-3115: kerb_detect band reading, offsets -2.7..-2.2 m (piece of the run s 3108-3115) on c20_s3250; colour: colour unverified: no inventory kerb row on that side within 40 m of s 3108-3115 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 61 | kerb | left | 3319-3328 | 0-0 | kerb 3319.1-3328.1 | left s 3319-3328: kerb_detect band reading, offsets -0.3..+0.0 m (piece of the run s 3319-3377) on c20_s3450; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 62 | kerb | left | 3329-3338 | 0-0 | kerb 3329.1-3338.1 | left s 3329-3338: kerb_detect band reading, offsets -0.5..-0.3 m (piece of the run s 3319-3377) on c20_s3450; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 63 | kerb | left | 3339-3348 | 0-0 | kerb 3339.1-3348.1 | left s 3339-3348: kerb_detect band reading, offsets -0.5..-0.4 m (piece of the run s 3319-3377) on c20_s3450; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 64 | kerb | left | 3349-3358 | 0-0 | kerb 3349.1-3358.1 | left s 3349-3358: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 3319-3377) on c20_s3450, c20_s3500; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 65 | kerb | left | 3359-3368 | 0-0 | kerb 3359.1-3368.1 | left s 3359-3368: kerb_detect band reading, offsets -0.6..-0.6 m (piece of the run s 3319-3377) on c20_s3500; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 66 | kerb | left | 3369-3377 | 0-0 | kerb 3369.1-3377.2 | left s 3369-3377: kerb_detect band reading, offsets -0.5..-0.1 m (piece of the run s 3319-3377) on c20_s3500; colour: colour unverified: no inventory kerb row on that side within 40 m of s 3369-3377 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 67 | kerb | left | 3458-3467 | 0-0 | kerb 3458.3-3467.3 | left s 3458-3467: kerb_detect band reading, offsets -0.6..-0.3 m (piece of the run s 3458-3508) on c20_s3550, c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3475 left) |
| 68 | kerb | left | 3468-3477 | 0-0 | kerb 3468.3-3477.3 | left s 3468-3477: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 3458-3508) on c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3475 left) |
| 69 | kerb | left | 3478-3487 | 0-0 | kerb 3478.3-3487.3 | left s 3478-3487: kerb_detect band reading, offsets -0.5..-0.3 m (piece of the run s 3458-3508) on c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3475 left) |
| 70 | kerb | left | 3488-3497 | 0-0 | kerb 3488.3-3497.3 | left s 3488-3497: kerb_detect band reading, offsets -0.5..-0.4 m (piece of the run s 3458-3508) on c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3475 left) |
| 71 | kerb | left | 3498-3507 | 0-0 | kerb 3498.3-3507.3 | left s 3498-3507: kerb_detect band reading, offsets -0.7..-0.5 m (piece of the run s 3458-3508) on c20_s3600, c20_s3650; colour: t116.jpg (red / white / blue; inventory row s 3475 left) |
| 72 | kerb | left | 3681-3690 | 0-0 | kerb 3680.5-3689.5 | left s 3681-3690: kerb_detect band reading, offsets -0.8..-0.5 m (piece of the run s 3681-3701) on c20_s3800; colour: t124.jpg (red / white / blue; inventory row s 3715 left) |
| 73 | kerb | left | 3691-3700 | 0-0 | kerb 3690.5-3699.6 | left s 3691-3700: kerb_detect band reading, offsets -1.9..-0.9 m (piece of the run s 3681-3701) on c20_s3800, c20_s3850; colour: t124.jpg (red / white / blue; inventory row s 3715 left) |
| 74 | kerb | left | 3823-3832 | 0-0 | kerb 3822.7-3831.7 | left s 3823-3832: kerb_detect band reading, offsets -1.9..-1.7 m (piece of the run s 3823-3867) on c20_s3950; colour: t128.jpg (red / white / blue; inventory row s 3854 left) |
| 75 | kerb | left | 3833-3842 | 0-0 | kerb 3832.7-3841.7 | left s 3833-3842: kerb_detect band reading, offsets -2.0..-1.9 m (piece of the run s 3823-3867) on c20_s3950; colour: t128.jpg (red / white / blue; inventory row s 3854 left) |
| 76 | kerb | left | 3843-3852 | 0-0 | kerb 3842.7-3851.7 | left s 3843-3852: kerb_detect band reading, offsets -2.3..-2.1 m (piece of the run s 3823-3867) on c20_s3950; colour: t128.jpg (red / white / blue; inventory row s 3854 left) |
| 77 | kerb | left | 3853-3862 | 0-0 | kerb 3852.7-3861.8 | left s 3853-3862: kerb_detect band reading, offsets -2.4..-2.0 m (piece of the run s 3823-3867) on c20_s3950, c20_s4000; colour: t128.jpg (red / white / blue; inventory row s 3854 left) |
| 78 | kerb | left | 3863-3867 | 0-0 | kerb 3862.8-3866.8 | left s 3863-3867: kerb_detect band reading, offsets -2.0..-1.9 m (piece of the run s 3823-3867) on c20_s4000; colour: t128.jpg (red / white / blue; inventory row s 3854 left) |
| 79 | kerb | left | 3958-3967 | 0-0 | kerb 3957.9-3966.9 | left s 3958-3967: kerb_detect band reading, offsets -1.0..-0.7 m (piece of the run s 3958-4012) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3982 left) |
| 80 | kerb | left | 3968-3977 | 0-0 | kerb 3967.9-3976.9 | left s 3968-3977: kerb_detect band reading, offsets -0.8..-0.6 m (piece of the run s 3958-4012) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3982 left) |
| 81 | kerb | left | 3978-3987 | 0-0 | kerb 3977.9-3986.9 | left s 3978-3987: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 3958-4012) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3982 left) |
| 82 | kerb | left | 3988-3997 | 0-0 | kerb 3987.9-3996.9 | left s 3988-3997: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 3958-4012) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3982 left) |
| 83 | kerb | left | 3998-4007 | 0-0 | kerb 3997.9-4006.9 | left s 3998-4007: kerb_detect band reading, offsets -0.8..-0.6 m (piece of the run s 3958-4012) on c20_s4100, c20_s4150; colour: t132.jpg (red / white / blue; inventory row s 3982 left) |
| 84 | kerb | left | 4008-4012 | 0-0 | kerb 4007.9-4011.9 | left s 4008-4012: kerb_detect band reading, offsets -1.3..-0.4 m (piece of the run s 3958-4012) on c20_s4150; colour: t132.jpg (red / white / blue; inventory row s 3982 left) |
| 85 | kerb | left | 4367-4376 | 0-0 | kerb 4367.4-4376.4 | left s 4367-4376: kerb_detect band reading, offsets -0.6..-0.4 m (piece of the run s 4367-4393) on c20_s4500; colour: t142.jpg (red / white / blue; inventory row s 4370 left) |
| 86 | kerb | left | 4377-4386 | 0-0 | kerb 4377.4-4386.4 | left s 4377-4386: kerb_detect band reading, offsets -1.1..-0.6 m (piece of the run s 4367-4393) on c20_s4500; colour: t142.jpg (red / white / blue; inventory row s 4370 left) |
| 87 | kerb | left | 4387-4393 | 0-0 | kerb 4387.4-4393.4 | left s 4387-4393: kerb_detect band reading, offsets -1.0..+0.7 m (piece of the run s 4367-4393) on c20_s4500; colour: t142.jpg (red / white / blue; inventory row s 4370 left) |
| 88 | kerb | right | 179-188 | 0-0 | kerb 179.2-188.2 | right s 179-188: kerb_detect band reading, offsets -0.6..+0.9 m (piece of the run s 179-268) on c20_s0300; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 89 | kerb | right | 189-198 | 0-0 | kerb 189.2-198.2 | right s 189-198: kerb_detect band reading, offsets -0.8..-0.7 m (piece of the run s 179-268) on c20_s0300; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 90 | kerb | right | 199-208 | 0-0 | kerb 199.2-208.3 | right s 199-208: kerb_detect band reading, offsets -0.7..-0.6 m (piece of the run s 179-268) on c20_s0300, c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 91 | kerb | right | 209-218 | 0-0 | kerb 209.3-218.3 | right s 209-218: kerb_detect band reading, offsets -0.7..-0.7 m (piece of the run s 179-268) on c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 92 | kerb | right | 219-228 | 0-0 | kerb 219.3-228.3 | right s 219-228: kerb_detect band reading, offsets -0.7..-0.6 m (piece of the run s 179-268) on c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 93 | kerb | right | 229-238 | 0-0 | kerb 229.3-238.3 | right s 229-238: kerb_detect band reading, offsets -0.7..-0.6 m (piece of the run s 179-268) on c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 94 | kerb | right | 239-248 | 0-0 | kerb 239.3-248.3 | right s 239-248: kerb_detect band reading, offsets -0.8..-0.6 m (piece of the run s 179-268) on c20_s0350; colour: t012.jpg (red / white / blue; inventory row s 257 right) |
| 95 | kerb | right | 249-258 | 0-0 | kerb 249.3-258.3 | right s 249-258: kerb_detect band reading, offsets -0.9..-0.9 m (piece of the run s 179-268) on c20_s0350, c20_s0400; colour: t012.jpg (red / white / blue; inventory row s 257 right) |
| 96 | kerb | right | 259-268 | 0-0 | kerb 259.3-268.3 | right s 259-268: kerb_detect band reading, offsets -0.9..-0.6 m (piece of the run s 179-268) on c20_s0400; colour: t012.jpg (red / white / blue; inventory row s 257 right) |
| 97 | kerb | right | 369-375 | 0-0 | kerb 368.5-374.5 | right s 368-374: kerb_detect band reading, offsets -6.9..-4.9 m (piece of the run s 358-374) on c20_s0500; colour: t018.jpg (red / white / blue; inventory row s 409 right) |
| 98 | kerb | right | 400-409 | 0-0 | kerb 399.5-408.5 | right s 399-409: kerb_detect band reading, offsets -15.1..-13.9 m (piece of the run s 399-425) on c20_p0840, c20_s0550; colour: t018.jpg (red / white / blue; inventory row s 409 right) |
| 99 | kerb | right | 410-419 | 0-0 | kerb 409.5-418.5 | right s 410-419: kerb_detect band reading, offsets -15.8..-15.2 m (piece of the run s 399-425) on c20_s0550; colour: t018.jpg (red / white / blue; inventory row s 409 right) |
| 100 | kerb | right | 420-425 | 0-0 | kerb 419.5-424.5 | right s 420-425: kerb_detect band reading, offsets -16.0..-15.8 m (piece of the run s 399-425) on c20_s0550; colour: t018.jpg (red / white / blue; inventory row s 409 right) |
| 101 | kerb | right | 478-483 | 0-0 | kerb 477.6-482.6 | right s 478-483: kerb_detect band reading, offsets +0.1..+0.3 m (piece of the run s 478-483) on c20_s0600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 478-483 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 102 | kerb | right | 1006-1015 | 0-0 | kerb 1006.2-1015.2 | right s 1006-1015: kerb_detect band reading, offsets -2.0..-1.6 m (piece of the run s 1006-1023) on c20_s1150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1006-1015 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 103 | kerb | right | 1016-1023 | 0-0 | kerb 1016.3-1023.3 | right s 1016-1023: kerb_detect band reading, offsets -2.2..-2.0 m (piece of the run s 1006-1023) on c20_s1150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1016-1023 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 104 | kerb | right | 1028-1037 | 0-0 | kerb 1028.3-1037.3 | right s 1028-1037: kerb_detect band reading, offsets -1.9..-0.4 m (piece of the run s 1028-1043) on c20_s1150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1028-1037 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 105 | kerb | right | 1038-1043 | 0-0 | kerb 1038.3-1043.3 | right s 1038-1043: kerb_detect band reading, offsets -0.5..-0.1 m (piece of the run s 1028-1043) on c20_s1150, c20_s1200; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1038-1043 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 106 | kerb | right | 1160-1169 | 0-0 | kerb 1160.4-1169.4 | right s 1160-1169: kerb_detect band reading, offsets -3.4..-2.2 m (piece of the run s 1160-1182) on c20_s1300; colour: t048.jpg (red / white; inventory row s 1172 right) |
| 107 | kerb | right | 1170-1180 | 0-0 | kerb 1170.4-1179.5 | right s 1170-1179: kerb_detect band reading, offsets -3.8..-3.4 m (piece of the run s 1160-1182) on c20_s1300; colour: t048.jpg (red / white; inventory row s 1172 right) |
| 108 | kerb | right | 1284-1293 | 0-0 | kerb 1283.6-1292.6 | right s 1284-1293: kerb_detect band reading, offsets -2.0..-1.7 m (piece of the run s 1284-1302) on c20_s1400; colour: t052.jpg (red / white / blue; inventory row s 1302 right) |
| 109 | kerb | right | 1294-1302 | 0-0 | kerb 1293.6-1301.6 | right s 1294-1302: kerb_detect band reading, offsets -1.5..-0.5 m (piece of the run s 1284-1302) on c20_s1400, c20_s1450; colour: t052.jpg (red / white / blue; inventory row s 1302 right) |
| 110 | kerb | right | 1485-1494 | 0-0 | kerb 1484.8-1493.8 | right s 1485-1494: kerb_detect band reading, offsets -0.8..-0.6 m (piece of the run s 1485-1506) on c20_s1600; colour: t058.jpg (red / white / blue; inventory row s 1494 right) |
| 111 | kerb | right | 1495-1504 | 0-0 | kerb 1494.8-1503.9 | right s 1495-1504: kerb_detect band reading, offsets -0.8..-0.3 m (piece of the run s 1485-1506) on c20_s1600, c20_s1650; colour: t058.jpg (red / white / blue; inventory row s 1494 right) |
| 112 | kerb | right | 1770-1779 | 0-0 | kerb 1770.2-1779.2 | right s 1770-1779: kerb_detect band reading, offsets -0.3..-0.2 m (piece of the run s 1770-1811) on c20_s1900; colour: t066.jpg (white / red / blue; inventory row s 1751 right) |
| 113 | kerb | right | 1780-1789 | 0-0 | kerb 1780.2-1789.2 | right s 1780-1789: kerb_detect band reading, offsets -0.7..-0.3 m (piece of the run s 1770-1811) on c20_s1900; colour: t066.jpg (white / red / blue; inventory row s 1751 right) |
| 114 | kerb | right | 1790-1799 | 0-0 | kerb 1790.2-1799.2 | right s 1790-1799: kerb_detect band reading, offsets -0.6..-0.4 m (piece of the run s 1770-1811) on c20_s1900; colour: t066.jpg (white / red / blue; inventory row s 1751 right) |
| 115 | kerb | right | 1800-1809 | 0-0 | kerb 1800.2-1809.2 | right s 1800-1809: kerb_detect band reading, offsets -0.6..-0.3 m (piece of the run s 1770-1811) on c20_s1950; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1800-1809 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 116 | kerb | right | 1861-1869 | 0-0 | kerb 1861.3-1869.3 | right s 1861-1869: kerb_detect band reading, offsets -0.3..+0.0 m (piece of the run s 1861-1869) on c20_s2000; colour: t070.jpg (red / white / blue; inventory row s 1878 right) |
| 117 | kerb | right | 1919-1928 | 0-0 | kerb 1919.4-1928.4 | right s 1919-1928: kerb_detect band reading, offsets -3.2..+0.6 m (piece of the run s 1919-1931) on c20_s2050; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1919-1928 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 118 | kerb | right | 2304-2313 | 0-0 | kerb 2303.8-2312.8 | right s 2304-2313: kerb_detect band reading, offsets -0.6..-0.3 m (piece of the run s 2304-2340) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2312 right) |
| 119 | kerb | right | 2314-2323 | 0-0 | kerb 2313.8-2322.9 | right s 2314-2323: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 2304-2340) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2312 right) |
| 120 | kerb | right | 2324-2333 | 0-0 | kerb 2323.9-2332.9 | right s 2324-2333: kerb_detect band reading, offsets -0.6..-0.1 m (piece of the run s 2304-2340) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2312 right) |
| 121 | kerb | right | 2334-2340 | 0-0 | kerb 2333.9-2339.9 | right s 2334-2340: kerb_detect band reading, offsets +0.0..+0.9 m (piece of the run s 2304-2340) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2312 right) |
| 122 | kerb | right | 2753-2762 | 0-0 | kerb 2753.4-2762.4 | right s 2753-2762: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 2753-2783) on c20_s2900; colour: t094.jpg (red / white / blue; inventory row s 2757 right) |
| 123 | kerb | right | 2763-2772 | 0-0 | kerb 2763.4-2772.4 | right s 2763-2772: kerb_detect band reading, offsets -1.3..-0.7 m (piece of the run s 2753-2783) on c20_s2900; colour: t094.jpg (red / white / blue; inventory row s 2757 right) |
| 124 | kerb | right | 2773-2782 | 0-0 | kerb 2773.4-2782.4 | right s 2773-2782: kerb_detect band reading, offsets -0.9..-0.5 m (piece of the run s 2753-2783) on c20_s2900; colour: t094.jpg (red / white / blue; inventory row s 2757 right) |
| 125 | kerb | right | 3389-3398 | 0-0 | kerb 3389.2-3398.2 | right s 3389-3398: kerb_detect band reading, offsets -0.7..-0.5 m (piece of the run s 3389-3442) on c20_s3500, c20_s3550; colour: t112.jpg (blue / white; inventory row s 3421 right) |
| 126 | kerb | right | 3399-3408 | 0-0 | kerb 3399.2-3408.2 | right s 3399-3408: kerb_detect band reading, offsets -0.6..-0.3 m (piece of the run s 3389-3442) on c20_s3550; colour: t112.jpg (blue / white; inventory row s 3421 right) |
| 127 | kerb | right | 3409-3418 | 0-0 | kerb 3409.2-3418.2 | right s 3409-3418: kerb_detect band reading, offsets -0.2..-0.2 m (piece of the run s 3389-3442) on c20_s3550; colour: t112.jpg (blue / white; inventory row s 3421 right) |
| 128 | kerb | right | 3419-3428 | 0-0 | kerb 3419.2-3428.2 | right s 3419-3428: kerb_detect band reading, offsets -0.6..-0.3 m (piece of the run s 3389-3442) on c20_s3550; colour: t112.jpg (blue / white; inventory row s 3421 right) |
| 129 | kerb | right | 3429-3438 | 0-0 | kerb 3429.2-3438.2 | right s 3429-3438: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 3389-3442) on c20_s3550; colour: t114.jpg (red / white / blue; inventory row s 3439 right) |
| 130 | kerb | right | 3439-3442 | 0-0 | kerb 3439.2-3442.2 | right s 3439-3442: kerb_detect band reading, offsets -0.5..-0.4 m (piece of the run s 3389-3442) on c20_s3550; colour: t114.jpg (red / white / blue; inventory row s 3439 right) |
| 131 | kerb | right | 3676-3682 | 0-0 | kerb 3675.5-3681.5 | right s 3676-3682: kerb_detect band reading, offsets -1.3..-1.1 m (piece of the run s 3676-3682) on c20_s3800; colour: colour unverified: no inventory kerb row on that side within 40 m of s 3676-3682 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 132 | kerb | right | 3735-3744 | 0-0 | kerb 3734.6-3743.6 | right s 3735-3744: kerb_detect band reading, offsets +0.1..+0.6 m (piece of the run s 3735-3750) on c20_s3850; colour: colour unverified: no inventory kerb row on that side within 40 m of s 3735-3744 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 133 | kerb | right | 3745-3750 | 0-0 | kerb 3744.6-3749.6 | right s 3745-3750: kerb_detect band reading, offsets -0.7..-0.1 m (piece of the run s 3735-3750) on c20_s3850; colour: t126.jpg (red / white / blue; inventory row s 3788 right) |
| 134 | kerb | right | 3781-3790 | 0-0 | kerb 3780.7-3789.7 | right s 3781-3790: kerb_detect band reading, offsets -0.4..+0.6 m (piece of the run s 3781-3800) on c20_s3900; colour: t126.jpg (red / white / blue; inventory row s 3788 right) |
| 135 | kerb | right | 3791-3800 | 0-0 | kerb 3790.7-3799.7 | right s 3791-3800: kerb_detect band reading, offsets -0.8..-0.5 m (piece of the run s 3781-3800) on c20_s3900; colour: t126.jpg (red / white / blue; inventory row s 3788 right) |
| 136 | kerb | right | 3876-3885 | 0-0 | kerb 3875.8-3884.8 | right s 3876-3885: kerb_detect band reading, offsets -1.1..-0.6 m (piece of the run s 3876-3926) on c20_s4000; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 137 | kerb | right | 3886-3895 | 0-0 | kerb 3885.8-3894.8 | right s 3886-3895: kerb_detect band reading, offsets -0.5..-0.4 m (piece of the run s 3876-3926) on c20_s4000; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 138 | kerb | right | 3896-3905 | 0-0 | kerb 3895.8-3904.8 | right s 3896-3905: kerb_detect band reading, offsets -0.4..-0.3 m (piece of the run s 3876-3926) on c20_s4000, c20_s4050; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 139 | kerb | right | 3906-3915 | 0-0 | kerb 3905.8-3914.8 | right s 3906-3915: kerb_detect band reading, offsets -0.5..-0.3 m (piece of the run s 3876-3926) on c20_s4050; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 140 | kerb | right | 3916-3925 | 0-0 | kerb 3915.8-3924.8 | right s 3916-3925: kerb_detect band reading, offsets -0.5..-0.4 m (piece of the run s 3876-3926) on c20_s4050; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 141 | kerb | right | 4016-4025 | 0-0 | kerb 4015.9-4025 | right s 4016-4025: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 4016-4068) on c20_s4150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 4016-4025 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 142 | kerb | right | 4026-4035 | 0-0 | kerb 4026-4035 | right s 4026-4035: kerb_detect band reading, offsets -0.5..-0.2 m (piece of the run s 4016-4068) on c20_s4150; colour: t134.jpg (white / blue; inventory row s 4066 right) |
| 143 | kerb | right | 4036-4045 | 0-0 | kerb 4036-4045 | right s 4036-4045: kerb_detect band reading, offsets -0.2..-0.2 m (piece of the run s 4016-4068) on c20_s4150; colour: t134.jpg (white / blue; inventory row s 4066 right) |
| 144 | kerb | right | 4046-4055 | 0-0 | kerb 4046-4055 | right s 4046-4055: kerb_detect band reading, offsets -0.3..-0.2 m (piece of the run s 4016-4068) on c20_s4150; colour: t134.jpg (white / blue; inventory row s 4066 right) |
| 145 | kerb | right | 4056-4065 | 0-0 | kerb 4056-4065 | right s 4056-4065: kerb_detect band reading, offsets -4.9..-0.3 m (piece of the run s 4016-4068) on c20_s4150, c20_s4200; colour: t134.jpg (white / blue; inventory row s 4066 right) |
| 146 | kerb | right | 4083-4092 | 0-0 | kerb 4083-4092 | right s 4083-4092: kerb_detect band reading, offsets -0.2..-0.2 m (piece of the run s 4083-4116) on c20_s4200; colour: t134.jpg (white / blue; inventory row s 4066 right) |
| 147 | kerb | right | 4093-4102 | 0-0 | kerb 4093-4102 | right s 4093-4102: kerb_detect band reading, offsets -0.1..-0.1 m (piece of the run s 4083-4116) on c20_s4200; colour: t136.jpg (white / blue; inventory row s 4123 right) |
| 148 | kerb | right | 4103-4112 | 0-0 | kerb 4103-4112.1 | right s 4103-4112: kerb_detect band reading, offsets -0.5..-0.1 m (piece of the run s 4083-4116) on c20_s4200, c20_s4250; colour: t136.jpg (white / blue; inventory row s 4123 right) |
| 149 | kerb | right | 4113-4116 | 0-0 | kerb 4113.1-4116.1 | right s 4113-4116: kerb_detect band reading, offsets -0.6..-0.5 m (piece of the run s 4083-4116) on c20_s4250; colour: t136.jpg (white / blue; inventory row s 4123 right) |
| 150 | kerb | right | 4305-4314 | 0-0 | kerb 4305.3-4314.3 | right s 4305-4314: kerb_detect band reading, offsets -0.6..+0.0 m (piece of the run s 4305-4358) on c20_s4400, c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 151 | kerb | right | 4315-4324 | 0-0 | kerb 4315.3-4324.3 | right s 4315-4324: kerb_detect band reading, offsets -0.4..-0.2 m (piece of the run s 4305-4358) on c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 152 | kerb | right | 4325-4334 | 0-0 | kerb 4325.3-4334.3 | right s 4325-4334: kerb_detect band reading, offsets -0.6..-0.4 m (piece of the run s 4305-4358) on c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 153 | kerb | right | 4335-4344 | 0-0 | kerb 4335.3-4344.3 | right s 4335-4344: kerb_detect band reading, offsets -0.6..-0.6 m (piece of the run s 4305-4358) on c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 154 | kerb | right | 4345-4354 | 0-0 | kerb 4345.3-4354.4 | right s 4345-4354: kerb_detect band reading, offsets -0.8..-0.6 m (piece of the run s 4305-4358) on c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 155 | kerb | right | 4355-4358 | 0-0 | kerb 4355.4-4358.4 | right s 4355-4358: kerb_detect band reading, offsets -1.2..-0.6 m (piece of the run s 4305-4358) on c20_s4450, c20_s4500; colour: colour unverified: no inventory kerb row on that side within 40 m of s 4355-4358 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 156 | kerb | right | 4413-4420 | 0-0 | kerb 4413.4-4420.4 | right s 4408-4415: block line read across the normal (edges_spline.bands outer limit over -10..+1.5 m, compare/buttonwillow/stage3_evidence) on c20_s4500 / c20_s4550; a diagonal line from 3.5 m inside the right edge at s 4410 to the left edge at s 4472; colour: t144.jpg (white / blue / red; inventory row s 4416 right) |
| 157 | kerb | right | 4421-4428 | 0-0 | kerb 4421.4-4428.4 | right s 4416-4423: block line read across the normal (edges_spline.bands outer limit over -10..+1.5 m, compare/buttonwillow/stage3_evidence) on c20_s4500 / c20_s4550; a diagonal line from 3.5 m inside the right edge at s 4410 to the left edge at s 4472; colour: t144.jpg (white / blue / red; inventory row s 4416 right) |
| 158 | kerb | right | 4430-4437 | 0-0 | kerb 4429.5-4436.5 | right s 4424-4431: block line read across the normal (edges_spline.bands outer limit over -10..+1.5 m, compare/buttonwillow/stage3_evidence) on c20_s4500 / c20_s4550; a diagonal line from 3.5 m inside the right edge at s 4410 to the left edge at s 4472; colour: t144.jpg (white / blue / red; inventory row s 4416 right) |
| 159 | kerb | right | 4438-4445 | 0-0 | kerb 4437.5-4444.5 | right s 4432-4439: block line read across the normal (edges_spline.bands outer limit over -10..+1.5 m, compare/buttonwillow/stage3_evidence) on c20_s4500 / c20_s4550; a diagonal line from 3.5 m inside the right edge at s 4410 to the left edge at s 4472; colour: t144.jpg (white / blue / red; inventory row s 4416 right) |
| 160 | kerb | right | 4446-4453 | 0-0 | kerb 4445.5-4452.5 | right s 4440-4447: block line read across the normal (edges_spline.bands outer limit over -10..+1.5 m, compare/buttonwillow/stage3_evidence) on c20_s4500 / c20_s4550; a diagonal line from 3.5 m inside the right edge at s 4410 to the left edge at s 4472; colour: t144.jpg (white / blue / red; inventory row s 4416 right) |
| 161 | kerb | right | 4478-4487 | 0-0 | kerb 4477.5-4486.5 | right s 4472-4481: the same block line at the package's left edge (kerb_detect offsets -1.0..-0.6 m from the left edge, c20_s4600), declared on the right as the onboard sees it (t146: blocks on the car's right); colour: t146.jpg (red / white / blue; inventory row s 4474 right) |
| 162 | kerb | right | 4488-4497 | 0-0 | kerb 4487.5-4496.5 | right s 4482-4491: the same block line at the package's left edge (kerb_detect offsets -1.3..-0.7 m from the left edge, c20_s4600), declared on the right as the onboard sees it (t146: blocks on the car's right); colour: t146.jpg (red / white / blue; inventory row s 4474 right) |
| 163 | kerb | right | 4498-4501 | 0-0 | kerb 4497.5-4500.5 | right s 4492-4495: the same block line at the package's left edge (kerb_detect offsets -1.7..-1.5 m from the left edge, c20_s4600), declared on the right as the onboard sees it (t146: blocks on the car's right); colour: t146.jpg (red / white / blue; inventory row s 4474 right) |
| 164 | station | right | 482-482 | 1-1 | marshal 'T1 exit' | c20_s0650: white roof 5.5 m2 in a dark tyre ring (compare/blob_scan.py, 0.4 m beyond the right edge at s 482); onboard t020 (0:20): canopy on posts on a tyre-faced mound close right; inventory s 477 right |
| 165 | station | right | 819-819 | 7-7 | marshal 'T2 to T3, east side' | c20_s0600: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 7.1 m beyond the right edge at s 820); onboard t034 (0:34): blue canopy on a tyre-faced mound ahead right; inventory s 834 right |
| 166 | station | right | 1014-1014 | 9-9 | marshal 'T3' | c20_s1150: white roof 5.6 m2 in a dark tyre ring (compare/blob_scan.py, 9.2 m beyond the right edge at s 1014); onboard t040 (0:40): blue canopy on posts on a tyre-faced mound close right; inventory s 996 right |
| 167 | station | right | 1177-1177 | 8-8 | marshal 'T4' | c20_s1300: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.6 m beyond the right edge at s 1173); onboard t046 (0:46): canopy on posts ahead right; inventory s 1186 right |
| 168 | station | right | 1494-1494 | 12-12 | marshal 'T5' | c20_s1550: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.8 m beyond the right edge at s 1492); onboard t058 (0:58): canopy on a tyre-faced mound right; inventory s 1524 right |
| 169 | station | right | 2072-2072 | 10-10 | marshal 'T6 (Riverside)' | c20_s2150: white roof 6.3 m2 in a dark tyre ring (compare/blob_scan.py, 10.4 m beyond the right edge at s 2069); onboard t074 (1:14): canopy on a tyre-faced mound ahead right; inventory s 2050 right |
| 170 | station | right | 2360-2360 | 19-19 | marshal 'T7' | c20_s2500: white roof 5.9 m2 in a dark tyre ring (compare/blob_scan.py, 19.2 m beyond the right edge at s 2358); onboard t082 (1:22): canopy on a mound ahead right; inventory s 2372 right |
| 171 | station | right | 2766-2766 | 10-10 | marshal 'T8' | c20_s2900: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 9.8 m beyond the right edge at s 2764); onboard t092 (1:32): canopy on posts ahead right; inventory s 2776 right |
| 172 | station | right | 3193-3193 | 11-11 | marshal 'north leg before T9' | c20_s3300: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 11.0 m beyond the right edge at s 3189); onboard not in the 2 s frames (t106-t108 look past it); roof and tyre ring on c20_s3300 / c20_s3350 |
| 173 | station | right | 3424-3424 | 14-14 | marshal 'T9 (Star Mazda)' | c20_s3500: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 13.6 m beyond the right edge at s 3420); onboard t112 (1:52): roofed platform on stilts ahead right; inventory s 3436 right |
| 174 | station | right | 3702-3702 | 14-14 | marshal 'T10' | c20_s3800: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 15.4 m beyond the right edge at s 3698); onboard t122 (2:02): station far ahead right; inventory s 3758 right |
| 175 | station | left | 4276-4276 | 8-8 | marshal 'T11 approach (Sunset)' | c20_s4350: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 5.0 m beyond the left edge at s 4272); onboard t138 (2:18): canopy on a tyre-faced mound ahead left; inventory s 4274 left |
| 176 | station | left | 199-199 | 5-5 | marshal 'pit-wall end hut' | c20_s0300 / c20_s0350: white roof 7.8 m2 at the east end of the pit wall (compare/blob_scan.py, 5.2 m beyond the left edge at s 199; window stage3_evidence/cw_wallend.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60) |
| 177 | station | left | 2-2 | 4-4 | marshal 'starter's stand' | c20_s0050 / c20_s0100 / c20_s0150: the white structure on the pit wall at the timing line (blob_scan s 2, 3.4 m beyond the left edge); pit-lane video ucmXJu5QKFQ 22:19-22:28: the scaffold starter's stand with a canopy on the pit wall |
| 178 | mast | left | 3439-3439 | 161-161 | mast '' | OSM man_made=mast / communications tower node 10220517717; the lidar (CA_SanJoaquin_2021) has an isolated spike 49.5-49.7 m over the DEM there (30 cells, compare/stage3 lidar spike scan); onboard t106 (1:46): a tall thin pole far ahead on the north leg (inventory mast row s 3400 ahead, ahead_m 250) |
| 179 | building | left | 4688-14 (wraps) | 46-63 | building 0 '' 4.3 m | osm (pit-lane video ucmXJu5QKFQ 21:52-22:10 (t1312000, t1330000): the two-storey timing tower with the blue roof beside the pit lane; OSM footprint, lidar height) |
| 180 | building | left | 4685-11 (wraps) | 25-43 | building 1 '' 9.8 m | osm (pit-lane video ucmXJu5QKFQ 21:52-22:10 (t1312000, t1330000): the two-storey timing tower with the blue roof beside the pit lane; OSM footprint, lidar height) |
| 181 | cone_line | right | 20-24 | 1-2 | cone line 0 | onboard t006.jpg (yellow, orange; inventory s 20 right: two cones, yellow and orange); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 182 | cone_line | right | 297-298 | 2-2 | cone line 1 | onboard t012.jpg (orange; inventory s 297 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 183 | cone_line | left | 533-534 | 1-2 | cone line 2 | onboard t022.jpg (orange; inventory s 533 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 184 | cone_line | left | 834-835 | 2-2 | cone line 3 | onboard t034.jpg (orange; inventory s 834 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 185 | cone_line | left | 973-974 | 1-1 | cone line 4 | onboard t038.jpg (orange; inventory s 973 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 186 | cone_line | right | 1040-1041 | 1-1 | cone line 5 | onboard t042.jpg (orange; inventory s 1040 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 187 | cone_line | right | 1307-1308 | 1-2 | cone line 6 | onboard t052.jpg (orange; inventory s 1307 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 188 | cone_line | right | 2158-2159 | 2-2 | cone line 7 | onboard t078.jpg (orange; inventory s 2158 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 189 | cone_line | left | 2696-2700 | 1-2 | cone line 8 | onboard t092.jpg (orange; inventory s 2696 left: two orange cones); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 190 | cone_line | right | 3439-3440 | 1-2 | cone line 9 | onboard t114.jpg (orange; inventory s 3439 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 191 | cone_line | right | 4071-4072 | 1-2 | cone line 10 | onboard t134.jpg (orange; inventory s 4071 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 192 | cone_line | right | 4575-4576 | 1-1 | cone line 11 | onboard t002.jpg (orange; inventory s 4575 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 193 | cone_line | right | 4593-4594 | 1-2 | cone line 12 | onboard t150.jpg (orange; inventory s 4593 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |

###### Every inventory row and its outcome (92 rows)

| s (m) | t | side | kind | what | source | outcome |
|---|---|---|---|---|---|---|
| 20 | 0:06.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@6.0 | covered by barrier 0 (concrete); barrier 2 (concrete) |
| 20 | 0:06.0 | right | cone_line | two cones, yellow and orange | onboard:7QS2M-HGSI4@6.0 | covered by cone line 0 |
| 101 | 0:08.0 | left | wall | concrete K-rail, a dark (black) section at its east end | onboard:7QS2M-HGSI4@8.0 | covered by barrier 0 (concrete); barrier 3 (concrete) |
| 216 | 0:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@10.0 | covered by kerb 199.2-208.3; kerb 209.3-218.3 |
| 246 | 0:10.0 | left | station | canopy on posts over a low concrete platform | onboard:7QS2M-HGSI4@10.0 | MISSING |
| 257 | 0:12.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@12.0 | covered by kerb 239.3-248.3; kerb 249.3-258.3 |
| 297 | 0:12.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@12.0 | covered by cone line 1 |
| 302 | 0:14.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@14.0 | covered by kerb 280.3-289.4; kerb 290.4-299.4 |
| 411 | 0:18.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@18.0 | covered by kerb 399.5-408.5; kerb 409.5-418.5 |
| 477 | 0:20.0 | right | station | corner station: canopy on posts on a tyre-walled earth mound | onboard:7QS2M-HGSI4@20.0 | covered by marshal 'T1 exit' |
| 477 | 0:20.0 | right | tyre_wall | tyres around the station mound | onboard:7QS2M-HGSI4@20.0 | covered by barrier 4 (tyres) |
| 536 | 0:22.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@22.0 | covered by cone line 2 |
| 536 | 0:22.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@22.0 | covered by kerb 536.7-543.7; kerb 544.7-552.7 |
| 580 | 0:24.0 | right | runoff | pale paved / concrete patch inside the hairpin | onboard:7QS2M-HGSI4@24.0 | surroundings (not a checked kind) |
| 738 | 0:32.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@32.0 | covered by kerb 743.9-749.9 |
| 770 | 0:30.0 | left | cone_line | line of small cones | onboard:7QS2M-HGSI4@30.0 | MISSING |
| 834 | 0:34.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@34.0 | covered by cone line 3 |
| 834 | 0:34.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@34.0 | MISSING |
| 974 | 0:38.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@38.0 | covered by cone line 4 |
| 974 | 0:38.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@38.0 | covered by kerb 952.2-961.2; kerb 962.2-971.2 |
| 996 | 0:40.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@40.0 | covered by kerb 972.2-981.2; kerb 982.2-991.2 |
| 996 | 0:40.0 | right | station | corner station: blue canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@40.0 | MISSING |
| 1041 | 0:42.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@42.0 | covered by cone line 5 |
| 1087 | 0:44.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@44.0 | covered by kerb 1080.3-1089.3 |
| 1173 | 0:48.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@48.0 | covered by kerb 1160.4-1169.4; kerb 1170.4-1179.5 |
| 1188 | 0:46.0 | right | station | corner station: canopy on posts | onboard:7QS2M-HGSI4@46.0 | covered by marshal 'T4' |
| 1224 | 0:50.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@50.0 | covered by kerb 1237.5-1246.5 |
| 1302 | 0:52.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@52.0 | covered by kerb 1283.6-1292.6; kerb 1293.6-1301.6 |
| 1307 | 0:52.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@52.0 | covered by cone line 6 |
| 1348 | 0:54.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@54.0 | covered by kerb 1326.6-1335.6; kerb 1336.6-1345.7 |
| 1484 | 0:56.0 | left | paint | white painted blocks at the left edge | onboard:7QS2M-HGSI4@56.0 | surroundings (not a checked kind) |
| 1495 | 0:58.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@58.0 | covered by kerb 1484.8-1493.8; kerb 1494.8-1503.9 |
| 1525 | 0:58.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@58.0 | MISSING |
| 1580 | 1:00.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@60.0 | covered by kerb 1559.9-1565.9 |
| 1647 | 1:02.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@62.0 | covered by kerb 1638-1647; kerb 1648-1657 |
| 1776 | 1:06.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@66.0 | covered by kerb 1770.2-1779.2; kerb 1780.2-1789.2 (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 1840 | 1:08.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@68.0 | covered by kerb 1839.3-1845.3 (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 1878 | 1:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@70.0 | covered by kerb 1861.3-1869.3 |
| 2023 | 1:12.0 | left | paint | white painted chevrons / blocks at the left edge | onboard:7QS2M-HGSI4@72.0 | surroundings (not a checked kind) |
| 2054 | 1:14.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@74.0 | MISSING |
| 2160 | 1:18.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@78.0 | covered by cone line 7 |
| 2311 | 1:22.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@82.0 | covered by kerb 2303.8-2312.8; kerb 2313.8-2322.9 |
| 2371 | 1:22.0 | right | station | corner station: canopy on a mound | onboard:7QS2M-HGSI4@82.0 | covered by marshal 'T7' |
| 2695 | 1:32.0 | left | cone_line | two orange cones | onboard:7QS2M-HGSI4@92.0 | covered by cone line 8 |
| 2695 | 1:32.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@92.0 | covered by kerb 2680.3-2689.3; kerb 2690.3-2699.3 |
| 2757 | 1:34.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@94.0 | covered by kerb 2753.4-2762.4; kerb 2763.4-2772.4 |
| 2775 | 1:32.0 | right | station | corner station: canopy on posts | onboard:7QS2M-HGSI4@92.0 | covered by marshal 'T8' |
| 2851 | 1:36.0 | left | paint | white painted blocks at the left edge | onboard:7QS2M-HGSI4@96.0 | surroundings (not a checked kind) |
| 3329 | 1:50.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@110.0 | covered by kerb 3319.1-3328.1; kerb 3329.1-3338.1 |
| 3423 | 1:52.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@112.0 | covered by kerb 3399.2-3408.2; kerb 3409.2-3418.2 |
| 3438 | 1:46.0 | ahead | mast | tall pole (light / camera mast) | onboard:7QS2M-HGSI4@106.0 | MISSING (corrected in stage-3 pass, 20 Oct 2026: ahead_m was 250) |
| 3438 | 1:52.0 | right | station | corner station: roofed platform on stilts | onboard:7QS2M-HGSI4@112.0 | covered by marshal 'T9 (Star Mazda)' |
| 3443 | 1:54.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@114.0 | covered by cone line 9 |
| 3443 | 1:54.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@114.0 | covered by kerb 3419.2-3428.2; kerb 3429.2-3438.2 |
| 3478 | 1:56.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@116.0 | covered by kerb 3458.3-3467.3; kerb 3468.3-3477.3 |
| 3712 | 2:04.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@124.0 | covered by kerb 3717.6-3721.6; kerb 3722.6-3726.6 |
| 3758 | 2:02.0 | right | station | corner station | onboard:7QS2M-HGSI4@122.0 | MISSING |
| 3783 | 2:06.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@126.0 | covered by kerb 3780.7-3789.7; kerb 3790.7-3799.7 |
| 3851 | 2:08.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@128.0 | covered by kerb 3832.7-3841.7; kerb 3842.7-3851.7 |
| 3914 | 2:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@130.0 | covered by kerb 3895.8-3904.8; kerb 3905.8-3914.8 |
| 3981 | 2:12.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@132.0 | covered by kerb 3957.9-3966.9; kerb 3967.9-3976.9 |
| 4065 | 2:14.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@134.0 | covered by kerb 4046-4055; kerb 4056-4065 |
| 4070 | 2:14.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@134.0 | covered by cone line 10 |
| 4122 | 2:16.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@136.0 | covered by kerb 4103-4112.1; kerb 4113.1-4116.1 |
| 4273 | 2:18.0 | left | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@138.0 | covered by marshal 'T11 approach (Sunset)' |
| 4308 | 2:20.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@140.0 | covered by kerb 4305.3-4314.3; kerb 4315.3-4324.3 |
| 4371 | 2:22.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@142.0 | covered by kerb 4367.4-4376.4; kerb 4377.4-4386.4 |
| 4417 | 2:24.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@144.0 | covered by kerb 4413.4-4420.4; kerb 4421.4-4428.4 |
| 4475 | 2:26.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@146.0 | covered by kerb 4477.5-4486.5; kerb 4487.5-4496.5 |
| 4514 | 0:00.0 | left | wall | concrete K-rail (Jersey) segments | onboard:7QS2M-HGSI4@0.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4514 | 0:00.0 | right | runoff | dirt, flat, open | onboard:7QS2M-HGSI4@0.0 | surroundings (not a checked kind) |
| 4575 | 0:02.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@2.0 | covered by cone line 11 |
| 4593 | 2:30.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@150.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4593 | 2:30.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@150.0 | covered by cone line 12 |
| 4609 | 2:28.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@148.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4643 | 0:04.0 | left | wall | concrete K-rail (Jersey) | onboard:7QS2M-HGSI4@4.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4662 | 2:32.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@152.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4695 | 0:04.0 | left | building | control tower | onboard:7QS2M-HGSI4@4.0 | covered by building 0 '' 4.3 m; building 1 '' 9.8 m (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 4695 | 0:02.0 | left | building | control tower: 2 storeys, blue flat roof on posts over a deck | onboard:7QS2M-HGSI4@2.0 | covered by building 0 '' 4.3 m; building 1 '' 9.8 m |
| 4296 |  | right | paint | the lane leaves the track's left edge before T11 (no wall at the split) | onboard:ucmXJu5QKFQ@20:31 | pit lane: not a checked kind for the lap |
| 4320 |  | right | station | canopy on a pole over a low concrete pad | onboard:ucmXJu5QKFQ@20:31 | pit lane: not a checked kind for the lap |
| 4497 |  | left | cone_line | small yellow and orange cones | onboard:ucmXJu5QKFQ@20:40 | pit lane: not a checked kind for the lap |
| 4510 |  | right | wall | concrete K-rail (Jersey) segments | onboard:ucmXJu5QKFQ@20:40 | pit-lane gate (pit_lane.walls) (corrected in stage-3 pass, 20 Oct 2026: s was 4497) |
| 4528 |  | left | wall | concrete K-rail (Jersey) segments | onboard:ucmXJu5QKFQ@20:49 | pit-lane gate (pit_lane.walls) |
| 4528 |  | right | wall | concrete K-rail (Jersey) | onboard:ucmXJu5QKFQ@20:49 | pit-lane gate (pit_lane.walls) |
| 4579 |  | left | wall | concrete K-rail | onboard:ucmXJu5QKFQ@21:07 | pit-lane gate (pit_lane.walls) |
| 4579 |  | right | wall | concrete K-rail | onboard:ucmXJu5QKFQ@21:07 | pit-lane gate (pit_lane.walls) |
| 4655 |  | left | building | control tower: 2 storeys and a roof deck, blue roof | onboard:ucmXJu5QKFQ@21:52 | pit lane: not a checked kind for the lap |
| 4655 |  | left | wall | concrete K-rail | onboard:ucmXJu5QKFQ@21:52 | pit-lane gate (pit_lane.walls) |
| 4655 |  | right | wall | concrete K-rail | onboard:ucmXJu5QKFQ@21:52 | pit-lane gate (pit_lane.walls) |
| 4683 |  | both | cone_line | orange cones in two lines along the lane | onboard:ucmXJu5QKFQ@22:19 | pit lane: not a checked kind for the lap |
| 4683 |  | right | station | starter's stand: scaffold tower with a deck and canopy on the pit wall | onboard:ucmXJu5QKFQ@22:19 | pit lane: not a checked kind for the lap |
