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
| station | right | 996 | corner station, blue canopy | onboard t040 | placed: T3 (s 1013 right, 17 m: time-map error) |
| station | right | 1522 | corner station on a tyre-walled mound | onboard t058 (ahead 30 m) | placed: T5 (s 1492 right, 29 m: the frame's look-ahead and the time map) |
| station | right | 3765 | corner station | onboard t122 (ahead 120 m) | placed: T10 (s 3697 right; the 120 m look-ahead was estimated by eye) |
| station | right | 2052 | corner station on a tyre-walled mound | onboard t074 (ahead 40 m) | placed: T6 (Riverside) (s 2069 right, 17 m: time-map error) |
| mast | ahead | 3444 | tall pole | onboard t106 | placed: OSM man_made=mast (the 49.5 m communications tower, s 3439 left, ~400 m off; the pole on t106 is most likely it) |
| cone_line | right | 146 | several orange cones on the paved shoulder | onboard t008 | rejected: round 8 (owner lap 2 note 24): t008 at full resolution shows small dark marker posts beyond the edge, no orange cones; the t006 cones are the s 40-55 row |

## First-centre round and judge r1 (20 Oct 2026)

### Stage 1: the first centre on the circuit's pavement (runs 21-30)

At T1 exit, T10 and T11 exit the OSM way ran on the paved apron beyond the block line. The changes:
- `centre.prior_shift` shifts the first centre by the lateral offset measured on capture windows with a 2 m ruler (stage3_evidence/ruler_t1.png, ruler_t1b.png, ruler_t10.png, ruler_t11.png).
- The shift shortened the loop by 7 m, so `stations_ref` is frozen on the run-20 centre (`tracks/buttonwillow/stations_ref.json`). The fit's masks and kerb-search zones are now remapped like the features.
- The three exits' kerb zones are back in: T1 right 355-432, T10 left 3675-3760, T11 right 4402-4492. `('left', 4470, 4501)` is dropped (wrong side).
- The edge sits on the block line at all three (±0.2 m at 4405-4480, 0 to -0.4 m at 367-415, ±0.2 m at 3683-3738). Widths: T1 exit 13.4-15.3 m, T10 12.1-16.4 m, T11 exit 12.6-16.5 m.

The unpainted rule is now stated at side level. This is the owner's decision of 20 Oct, 14:00, as restated by the orchestrator:
- a side is unpainted when asphalt_end readings are the majority of its associated readings;
- its within gate is the bias gate over all of them, kerb readings pooled;
- coverage is 50 %;
- a painted side is computed as before;
- the per-kind numbers are a printed report only.

Reason: the grey block bands blur like the asphalt end (85-86 % within 0.25 m, zone medians within ±0.05 m; stage3_evidence/bw_kerbzones.txt).

Zone fixes on their windows:
- **left 536-578:** the blocks end at 552; past that the readings were parked cars and the outer-loop junction. The zone is now 528-552 (oc_555).
- **right 1007-1033:** 10 readings only; the curve sat 0.3 m outside the blocks. A -3..+1.5 m window (oc_1020).
- **right 1858-1874:** the Dog Leg separation blocks; the curve sat 0.36 m inside them. A -3..+2 m window (oc_1866).
- **The T4-T5 apron step:** exemptions left 1380-1430 and right 1370-1435 in the reference frame, with the prior carried across on the left. Both cite cw_1348. The right one is the station frame swinging as the left edge steps out; the right edge's world continuity passes.
- **The T11-approach mound mask, left 4250-4272:** dropped. The mound stands ~8 m beyond the new edge (gap4255), and the mask had left a 71-station gap.
- **T4-T5 right 1322-1376:** a warm_end zone with a -1.5..+6 m window. The grey asphalt runs 1.5-4.5 m past the old edge before the warm dirt (width_profiles.txt). Run 29 used asphalt_end over the same window; it crept out to 39 m and was dropped.

Widths against 10.97-16.76 m (run 30): median 13.86, p10 11.92, p90 16.69, min 8.83 (s 1076), max 18.85 (s 1414); 4.8 % under, 9.6 % over.

Under-width stretches, read across the side without the block line (R-B warmth: asphalt +9..+16, dirt +20..+31; width_profiles.txt):

| stretch | min width | side read | reading | verdict |
|---|---|---|---|---|
| 1034-1115 | 8.83 m | right | warmth 17-25 from the edge out | dirt (warm_end reads it as dirt); the width stands |
| 1204-1230 | 10.52 m | right | warmth 18-29 | the width stands; the left blocks at 1193 lie 1.5 m beyond the edge (kerb strip 1193-1202) |
| 1322-1361 | 9.58 m | right | asphalt to +1.5..+4.5 m | the warm_end zone took the edge out (min 7.1 to 9.6 m); the rest is warm_end's threshold |
| 2509-2541 | 10.28 m | right | asphalt continues | the drag-strip mouth: the prior is carried across it |
| 2756-2799 | 10.43 m | left | a bright band at +1 m, then warmth 19-20 | the width stands |

Stage 1, run 30 (as printed):
```
[ok] fit left: unpainted bias: unpainted side (83 % of 6364 associated readings from asphalt_end, a majority); 99.0 % of 4675 41-station windows have a median residual within +-0.25 m (>= 90 %); worst -0.409 m at 146 (126..166); 87 % of capture rows have a band within 1.2 m (>= 85 %); spread (printed, not gated): |residual| p10/p50/p90 (0.031, 0.154, 0.401) m, 70.9 % within 0.25 m
     report left per evidence kind (not gated): asphalt_end 5257 readings (83 %), 69.0 % within 0.25 m; kerb_band 1107 readings (17 %), 80.2 % within 0.25 m
[ok] fit left: coverage: 56 % of stations (>= 50 %, unpainted side)
[ok] fit left: longest gap: 37 st at (351, 387) (<= 60)
[ok] fit left: waviness: rolling-100 rms max 0.024 m (<= 0.04), peak 0.034 m (<= 0.1) outside tight corners
[ok] fit left: kink: max 0.24 deg/station (<= 0.5) outside tight corners; station 0 0.00
[ok] fit right: unpainted bias: unpainted side (78 % of 6885 associated readings from asphalt_end, a majority); 97.9 % of 4633 41-station windows have a median residual within +-0.25 m (>= 90 %); worst +0.369 m at 147 (127..167); 89 % of capture rows have a band within 1.2 m (>= 85 %); spread (printed, not gated): |residual| p10/p50/p90 (0.021, 0.125, 0.388) m, 75.1 % within 0.25 m
     report right per evidence kind (not gated): asphalt_end 5355 readings (78 %), 71.4 % within 0.25 m; kerb_band 1464 readings (21 %), 88.0 % within 0.25 m; warm_end 66 readings (1 %), 81.8 % within 0.25 m
[ok] fit right: coverage: 58 % of stations (>= 50 %, unpainted side)
[ok] fit right: longest gap: 41 st at (580, 620) (<= 60)
[ok] fit right: waviness: rolling-100 rms max 0.029 m (<= 0.04), peak 0.044 m (<= 0.1) outside tight corners
[ok] fit right: kink: max 0.27 deg/station (<= 0.5) outside tight corners; station 0 0.00
[ok] painted-midpoint residual: rms 0.19 -> 0.03 m (final refit)
[ok] loop stations: n = 4685
[ok] elevation range: 3.3 m (z0 76.67 NAVD88)
[ok] direction: signed area -369983 m^2, config cw
[ok] start/finish: station 0 is 0.47 m from the configured timing line
[ok] edge jumps: max lateral change between stations: left 0.106 m, right 0.110 m
[ok] cross slope (inner 2/3): max 7.4% at s=2227; 0 stations over 12 % (listed in work/report.json)
[ok] cross slope (edge thirds): max 8.4% at s=2227
[ok] no NaN: 
[ok] edge gate left : rms vs 41-st median (R>250 m, 2408 st) 0.053 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.083 m at 1376 (next 0.080@1440, 0.080@1437; <= 0.1) | max edge-column cross-section step 0.018 m at 565
[ok] edge gate right: rms vs 41-st median (R>250 m, 2408 st) 0.045 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.097 m at 1366 (next 0.093@1365, 0.091@1364; <= 0.1) | max edge-column cross-section step 0.019 m at 4652
[ok] world continuity left : max |third difference| of the edge polyline 0.0051 m at station 612 (<= 0.02)
[ok] world continuity right: max |third difference| of the edge polyline 0.0045 m at station 1324 (<= 0.02)
[ok] profile gate: max cross-section step any column 0.019 m at station 4652 column 6 (<= 0.1)
     report width: median 13.86 m, p10 11.92, p90 16.69, min 8.83 m at station 1076, max 18.85 m at station 1414; 4.8 % of stations under 10.97 m, 9.6 % over 16.76 m
```

### After the judge (judge_r1.md): the rows, fixed or false

| judge row | what was done |
|---|---|
| 1. timing tower (4600-4695 L) | **Fixed.** OSM 765811057 is suppressed and replaced by a 2-storey block (6.4 m, beige-white, glazed band) with a blue roof deck on posts at 8.9-9.4 m; the lidar top is 9.8 m. OSM 765811056 behind it is plain. Still: `structure_stills/structure_timing_tower_r2.jpg`. The blue canopy tent beside it is a temporary event tent and is not placed. |
| 2. pit-wall K-rail (4514-150 L) | **Present:** 426 m of concrete, 0.81 m, colour #e4e2dc, from s 4513. It shows on the side still at 4609 L (compare_sheets/sim/row_s4609_left.jpg) as a pale band against the pale ground. The red / white panels and the black section near s 101 cannot be drawn: a barrier takes one colour. That is a rendering-kit feature, not a scenery input. The wall head now has a sand berm (impact barrier, pit-lane video t1240000). |
| 3. cones | **Added:** the small-cone line at 752-772 L (the 700 L cones are this line seen from 60 m back); 3196-3204 L; 4046-4054 R (two inventory rows added from the judge's frames). The flagged 297 R, 834 L, 973 L, 1040 R, 2158 R and 3439 R cones are in the package (one cone each, 1.5 m beyond the edge, at the inventory stations) but too small to read on the sheets. |
| 4. kerbs | **Fixed:** the strips were regenerated on the run-30 edges (166). 1200 L: 1193-1202. 1348 L: 1324-1387 (zone). 1878-1900 R: band pieces 1868-1905. 3329-3350 L: 3316-3366. 4300-4308 R: 4305-4324. The three exits: on the block lines. 4122 R: no band on the captures at 4113-4132; the t136 row is covered by the strips at 4093-4112. |
| 5. stations | **Placed:** the 246 L canopy at the white roof among the trees inside T1, 42 m out (blob247.png). The T1-exit station sits right of the shifted road (hood sheet fwd_01, s 450-500). 2350 R (T7) and 3758 R (T10) stand 19 m and 14.5 m off: dispositioned, with the time-map distances. |
| 6. tyre mounds | **Added:** tyre rings of 3.5 m radius round the T3, T5, T6 and T11-approach station roofs (capture rings, blob_scan). |
| 7. pit-lane frames | **Done:** the 13 pit rows carry their video frames (`pit_ucm/t<ms>.jpg`), and the pit sheets pair each still with the frame within 30 m. The pit-out lane (s 0-411) is not in the video (20:31-22:46 covers the pit-in to the paddock), so those stills carry no frame. |

Inventory corrections this round:
- t060 kerb left: ahead_m 30 → 95. Its blocks are at s 1636-1679.
- Two cone rows added (t107 L, t134 R).
- The pit rows carry their frames.

### Stage 3 (as printed, the published package)

All gates ok:
- barrier gaps 2.41 m;
- containment 0 escapes;
- pit connectivity 386 / 381 m with 0 crossings;
- signs 0 misplaced;
- wall ends 1 checked, 1 cushioned;
- tyre facings ok;
- coverage 76 rows, 210 objects, MISSING 0, UNSUPPORTED 0, 8 dispositions placed;
- pit lane 7 rows ok.

Objects: 166 kerb strips; 9 barriers (4 concrete, 5 tyre runs); 15 huts; 1 mast; 1 impact berm; 16 cone lines; 2 structures (the timing tower); 1 building; 9 closed roads.

## Round 3 (20 Oct 2026): pipeline merge, judge r2 (GPT 6 Astra + orchestrator), stages 1-4 again

### Merge and Acceptance 6

Merged track-pipeline eefd5b3 (`centre.pit_exit`; stage 1 reads no scenery key). Conflicts resolved:
- `build_track.py`: FIT_DUMP_DIR kept; `pit_merge_inputs` taken; the dead `centre.pit_merge_line` branch dropped.
- `build_scenery.py`: `pit_exit_cones.draw False` kept together with the new line-source selection.

Buttonwillow declares `centre.pit_exit.wall_end_latlon` at the K-rail's east end (cw_wallend.png). The builder logs it as outside the merge stretch (391..416): the line is detected as before.

Results:
- Stage 1 on the merged code: track.json and heightfield.bin byte-identical to rev dd0d1e6ab3.
- Sonoma reproduction: exit 0; track.json 9d7d52be96485e08 and heightfield.bin byte-identical to public/tracks/sonoma.
- Laguna reproduction: heightfield.bin identical; track.json sha256 d4e8634710813961. The documented edge gate left 0.105 m at 46 still fails, as expected.
- Both reproductions were written under out/buttonwillow_acc_*.
- The Laguna and Sonoma captures are linked read-only from the track-pipeline worktree into this worktree's ignored compare/ paths.

### Stage 1 (run 32): block lines

New kerb zones (`kerb_band` feature plus a `kerb_search` window) where the blocks sat inside the fitted edge:
- T2 hairpin inside, right 574-606: the edge was 6-7 m beyond the blocks (t2_595.png).
- right 1160-1185, 1289-1315 and 1912-1930.
- left 1440-1472, 1525-1566 and 3818-3868.
- left 528-556 (extended).

Every zone reached its blocks (band median within ±0.2 m). The paved patch inside the T2 hairpin is a measured-outline `paved_area` (new `latlon` form), and the inventory has an added kerb row at 590 R.

T10 3740-3810, the judge's open question: FALSE.
- The block line crosses from the left edge (3690-3755) to the right-hand apex (3765-3800); the onboard frame t126 / inventory row 3788 R shows the right kerb there (t10b.png, t10frames.jpg).
- The hood frames at s 3750 and 3800 are the same video frame (onboard.json: media_t -1 at s 3800, lap time 1:59.46 on both). The "left beside the car at 3800" is the 3750 frame repeated.

1034-1115 is left as it is (the owner's markup).

Widths (run 32): median 13.73, p10 11.24, p90 16.65, min 6.65 (s 583), max 18.36 (s 2442); 8.8 % under, 8.0 % over.
- Under 10.97 m: 534-632 (6.65 m, T2 hairpin entry to apex: the inside edge on the blocks). The outer left edge there stops at the outer-loop junction's tone change; open for the judge / owner.
- Also under: 1038-1120 (owner), 1184-1243 (8.1 m, T4 with the 1160-1185 R zone), 1326-1364, 2502-2544 (mouth), 2758-2802, 2957-2998.

### After the judge r2 (judge_r2.md): every row

| row | status |
|---|---|
| T2 hairpin inside line (orchestrator 1) | **fixed:** zone, strips on the blocks (the T2 pieces), the inside patch a paved area, an inventory row added |
| t032 left line at 0:26.5 | **settled:** the long block line along the left edge at s 700-760 (t032cap.png), not the outer-loop line. Strips 730-761 L from the band reader (kerb_detect had only 745-752) |
| timing tower | **fixed:** tan walls, glazing on the upper storey only (`bands`), a track-side balcony with an exterior stair (kit `balcony`), a broad blue roof deck 1.5 m past the footprint. The blue canopy tent is not placed: temporary, and no capture shows its position |
| K-rail colours | **fixed:** kit `pattern` / `sections` on barriers. Pit wall and paddock-side runs alternate white, white, red over 18.3 m (6.1 m K-rail segments, frames t148 / pit video); a dark section at 286-292 m along the pit wall (s ~101, t004 / t006). Test: src/app/__tests__/barrier-sections.test.ts |
| 22 strips off the edge | **fixed:** 15 became zones. Dropped as false: 1842-1848 R (the left block line read 8.6 m across) and 3105-3112 L (a parked car, k22_3108). 1835-1842 L is a real block line 6 m inside the left edge at the Dog Leg mouth (cw_1824): kept. The builder now reports strips more than 1.2 m off the edge; seven remain, listed in the stage-3 log |
| T10 line side | **FALSE** (above) |
| stations as enclosed cabins (Astra, all) | **fixed:** kit style `canopy` (roof on four posts over an earth mound, open). All 12 corner stations use it (mound 1.2 m). The starter's stand is a `platform` with railings and an access stair (kit `stair`) |
| kerb colours / block length | **fixed palette:** rwb #c4463b / #e2dfd6 / #4a7ccc, lighter blue from the close frames t014 / t044. The block length stays 1.0 m: the captures measure a 1.8-2.3 m light / coloured pair period. **Open:** a close-still comparison |
| kerbs missing or short | 741-747 vs 750-770 L: now 730-761 L. 1224 L: band pieces 1209-1238 L. 1850-1908 R: band pieces 1873-1910 R. 4350 L: FALSE (strips from 4367, inside the 15 m tolerance). 1500 R, 1750 R, 2400 L: FALSE (strips exist). 3100 L: dropped (a car) |
| single cones (300 R, 550 L, 950 L, 1050 R, 1300 R, 2150 R, 3450 R, 4550-4600 R) | **FALSE:** placed objects at 297 R, 533 L, 973 L, 1040 R, 1307 R, 2158 R, 3439 R, 4575 / 4593 R |
| cone lines from frames | **added:** 140-160 R (t006-t008), 895-905 L (t036), 1780-1830 R (t066-t068), 3250-3300 L (t108-t110), 3645-3655 R (t122). Inventory rows added |
| runoff closures | **added:** mouth cones at 1824 R (crossover 34351015) and 4607 R (Pacific). **Open:** 1562 L, 1780 R, 4064 R, 46 R, 293 R and 3256 L have no closed-road mouth within 20-60 m on that side, so their paved branches need a capture outline first |
| pit-lane cones | **added:** 0.46 m cones along both K-rails on the lane side (pit video t1249000-t1348000), s 4478-4679. **Open:** s 11, where the video does not cover the lane |
| pit-in mouth | Partly FALSE. On c20_s4400 (pitin.png) the fillet at 4290-4310 is paved and the wedge beyond 4310 is dirt, as the package has it. **Open:** the yellow hatch field is the NAIP 2022 texture inside the tone-matched lane, which the kit cannot erase |
| closed-road tone | **fixed:** the four front-straight crossovers take the asphalt tone (onboard t002-t006, t150-t152 outrank the pale captures). **Open:** the chevron marks at the 1824 R mouth are NAIP 2022 texture |
| smaller rows | 800 R base: the canopy style's mound. 574 R: paved area. **Open:** the 450 R tyre colour (#202020 declared; the app draws the tyre faces); the masts at 3200 / 3500 R (the comms tower drawn as a plain pole: a lattice style is a kit item); the 10-15 m mast at 3256 R (the lidar spike line at ENU x ≈ -190 is not pinned on a capture) |

### Stage 3 (published, rev e08631e61f)

All gates ok:
- barrier gaps 2.41 m; containment 0 escapes;
- pit connectivity 386 / 376 m with 0 crossings;
- signs 0 misplaced; wall ends cushioned;
- coverage 83 rows, 234 objects, MISSING 0, UNSUPPORTED 0, 5 dispositions;
- pit lane ok.

Objects: 181 kerb strips; 9 barriers; 15 huts; 1 mast; 1 berm; 25 cone lines; 1 paved area; 2 structures.

## Round 4 (20 Oct 2026): judge r3 (GPT 6 Astra, checked by the orchestrator)

No stage-1 change was kept, so the package's geometry is unchanged. Stage 1 and the ghosts rebuild byte-identical
(track.json, heightfield.bin and ghosts.json `cmp`-equal to rev e08631e61f).

### A. Kerb run extents (every run)

How each run was measured:
- the block line was followed on the clean captures with the edge fit's band reader (edges_spline.bands outer limits,
  -10..+1.5 m from the fitted edge, at least 2 capture rows per station, each station within 0.8 m of the last);
- it was grown out from the run's ends until 5 stations were missed;
- the strips were rebuilt over the measured extents in <= 10 m pieces, each citing its capture.

The onboard frames at the judge's places agree with the capture ends:
- s0600: the T2 apex line ahead-right;
- s1300 and s1500: right kerbs close;
- s1350 and s1450: left lines long;
- s4050 and s4100: right blocks ahead (stage3_evidence/ext_frames.jpg).

The lines the judge saw "running on 30-60 m" are the camera's look along the same line. The extents do not reach
640 or 1330: the captures show the T2 inside line ending at ~605 and the T4-exit line at ~1311. Dropped as false:
- 1960-1965 L: no band on c20_s2050;
- 548-554 R, 583-590 L and 1922-1931 R: 2-3 stray hits.

1009-1047 R is kept: the blocks are clear on c20_s1150 (oc_1020.png). The judge's plain edge is the hood's blind zone.

| side | run before | capture extent | strips |
|---|---|---|---|
| left | 281-320 | 284-323 | 4 pieces |
| left | 534-556 | 535-545 | 1 pieces |
| left | 583-590 | 586-589 | dropped |
| left | 732-763 | 738-763 | 3 pieces |
| left | 944-1004 | 947-1008 | 6 pieces |
| left | 1083-1092 | 1086-1093 | 1 pieces |
| left | 1105-1114 | 1107-1114 | 1 pieces |
| left | 1199-1208 | 1200-1211 | 1 pieces |
| left | 1221-1266 | 1229-1269 | 4 pieces |
| left | 1331-1394 | 1334-1394 | 6 pieces |
| left | 1429-1478 | 1431-1475 | 5 pieces |
| left | 1533-1570 | 1536-1570 | 4 pieces |
| left | 1640-1676 | 1642-1677 | 4 pieces |
| left | 1842-1848 | 1837-1848 | 1 pieces |
| left | 1960-1965 | 1962-1962 | dropped |
| left | 2519-2538 | 2532-2538 | 1 pieces |
| left | 2673-2740 | 2671-2740 | 7 pieces |
| left | 2837-2843 | 2837-2856 | 1 pieces |
| left | 2996-3005 | 2999-3007 | 1 pieces |
| left | 3322-3380 | 3334-3380 | 5 pieces |
| left | 3461-3510 | 3463-3513 | 5 pieces |
| left | 3683-3717 | 3684-3755 | 6 pieces |
| left | 3728-3755 | 3722-3755 | merged |
| left | 3826-3871 | 3838-3871 | 4 pieces |
| left | 3962-4015 | 3965-4018 | 5 pieces |
| left | 4371-4405 | 4374-4405 | 3 pieces |
| right | 180-268 | 187-269 | 9 pieces |
| right | 358-382 | 360-380 | 2 pieces |
| right | 394-423 | 398-424 | 3 pieces |
| right | 548-554 | 551-552 | dropped |
| right | 580-609 | 582-605 | 3 pieces |
| right | 1009-1027 | 1011-1046 | 4 pieces |
| right | 1034-1047 | 1035-1046 | merged |
| right | 1164-1183 | 1166-1188 | 3 pieces |
| right | 1288-1308 | 1285-1311 | 2 pieces |
| right | 1488-1507 | 1491-1510 | 2 pieces |
| right | 1774-1813 | 1776-1815 | 4 pieces |
| right | 1864-1872 | 1863-1916 | 6 pieces |
| right | 1878-1915 | 1917-1955 | 3 pieces |
| right | 1922-1931 | 1926-1926 | dropped |
| right | 2307-2343 | 2309-2338 | 2 pieces |
| right | 2756-2786 | 2759-2786 | 2 pieces |
| right | 3391-3445 | 3393-3445 | 6 pieces |
| right | 3769-3804 | 3772-3804 | 4 pieces |
| right | 3879-3929 | 3887-3930 | 5 pieces |
| right | 4021-4070 | 4023-4114 | 8 pieces |
| right | 4087-4120 | 4115-4120 | 1 pieces |
| right | 4170-4176 | 4173-4173 | merged |
| right | 4310-4363 | 4313-4364 | 5 pieces |
| right | 4418-4492 | 4418-4496 | 8 pieces |

### B. Strips inside the road

Now drawn within 1.2 m of the edge, except one:
- 550-556 L, 583-590 L, 548-554 R, 1922-1931 R: dropped (above);
- 600-609 R and 4061-4070 R: rebuilt on the followed line;
- 1285-1294 R, 1947-1955 R and 2847-2856 L: pieces over 1.2 m dropped.

**Open: 1837-1846 L**, a real block line 6.65 m inside the left edge where the Dog Leg branches (cw_1824). A stage-1
zone, left 1830-1856, was tried (run 33). It failed `fit right: waviness 0.047 m (<= 0.04) at 4452-4552` and moved
the held T2 stretch, so it was reverted (stage3_evidence/geometry_run33_zone1830.log). The strip stays because the
inventory kerb row 1839 L (t068) must be covered.

### C. Stations, each from its own frame (stage3_evidence/station_crops.jpg)

The zoomed frames show, at every corner, a pale round base, a cabinet on it and a flat canopy on one central pole.
The kit's canopy style now draws:
- a rounded base (base_color);
- a booth (body_h, body_color);
- a single pole (pole).

Cabinets:
- T1 exit white (t020); T2-T3 blue (t034); T3 dark (t040); T4 dark (t046); T5 white (t058); T6 pale (t074);
- T7 dark under a light-blue canopy (t082); T8 dark blue (t092, judge); T9 dark (t112); T10 dark (t122);
- T11 approach dark on a pale round base (t138); the north-leg station dark (no frame).

Other station items:
- The tyre rings and the T1-exit face take the pale base colour.
- Starter's stand: a compact platform, deck 1.8 m, w 1.6 m, rails, stair and a small canopy (kit `roof`).
- Pit-in station: a canopy on a pole over a white "CAC CLUB" cabinet at the pit-wall head (pit video t1240000; blob 4511 L). Pit row s 4320 corrected to 4508.
- 820 R: the hut stands at s 818, 7 m out. The side still at 834 looks 70 degrees right from 16 m past it, so it is behind the camera: FALSE.

### D. Timing tower

The capture (tower_cap.png, c20_s0050 / c20_p0420) shows the roof at ~25 x 20 m, the OSM footprint the walls. Built as:
- a tan ground storey with windows (3.2 m) and a deck railing round its roof;
- a glazed upper storey set back 3-3.5 m, with divided glazing (`base`, `mullions_m`);
- a track-side stair (balcony stair);
- the blue roof deck over the whole at 6.4-7.0 m.

The kit has new block `base`, `mullions_m` and `deck_rail` options.

### E. Pit lane

1. The 162 + 219 lane cones are dropped. Three yellow cones now stand at the tower foot, as in t1303000.
2. The lane is paved to both walls: `pit_lane.lane.to_walls` (new; 135 edge points extended).
3. The wall-head nose: kit impact style `rounded`, pale, 1.8 x 2.6 x 0.9 m (t1240000).
4. The paddock mesh fence along the entry: 1.5 m, 1 m beyond the lane's paddock edge at s 4290-4362.
5. The entry strip: a measured-outline asphalt `paved_area` over the NAIP patches.

### F. Paved aprons

Eight aprons are measured between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to
4.4-15.7 m wide:
- T1 exit right 356-512; T2 inside right 553-624 (replaces the hard-edged patch); T4 right 1165-1239;
- T4-T5 left 1305-1456; drag-strip rejoin right 2963-3025; T10 left 3701-3783; Zorros mouth right 4133-4208;
- T11 exit right 4406-4529.

They are drawn as the new `apron` surface: worn pale asphalt whose cells thin out within 2.5 m of the outline.

**Open:**
- the T2 outer loop (650 L): a closed road already in the asphalt tone; not re-checked on a still;
- the T5 exit apron (1700 L): no gap between the run-20 and current edges there; it needs a capture outline.

### G. Cones

**FALSE** (each placed): 150 R (140-160 R), 300 R (297 R), 550 L (533 L), 900 L (895-905 L), 1050 R (1040 R), 2150 R
(2158 R), 2700 L (2696 L), 4550 / 4600 R (4575 / 4593 R singles).

**Fixed:**
- 1920 R: one cone at the kerb's end (s1900 frame);
- 3200 R: one cone (s3200 frame);
- the Pacific mouth cones (4607 R) are dropped, so 4575 / 4593 read as the single cones the onboard shows;
- 170 R: mouth cones on the Atlantic branch;
- 46 R: cones across the crossover mouth;
- inventory rows were added for each.

**Settled from the frames:** 2000 R shows a dark bin, no cone; 2200 R and 2800 L show nothing (FALSE).

**Open:**
- 294 R and 4068 R: the frames t012 / t134 show the single cones already placed (297 R, 4071 R), and no branch is outlined;
- the 3200-3250 L density: the s3200 frame shows two cones ahead.

### H. Tree-line tyre barrier

TRUE: a long dark tyre line under the trees ~27 m beyond the left edge at s ~4150-4260 (c20_s4300, tyre4200.png).
Declared as a tyre run, 0.85 m. The round-2 barrier ledger called the "east of Sunset" far line tyre tracks; corrected
here.

### I. Masts

- The communications mast now carries a floodlight head (kit mast style `flood`).
- 3256 R: not resolvable. The lidar spike line at ENU x ≈ -190 is not pinned on any capture
  (c20_s3300 / c20_s3350 show no base).

### J. Held

T2 534-632 and T4 1034-1115: untouched; waiting for the owner's mark-ups.

### Stage 3 (published, rev d7b31ce2af)

Every gate ok (barrier gaps 1.49 m over 11 runs; containment 0 escapes; pit connectivity 386 / 376 m, 0 crossings; wall ends cushioned). Coverage: 87 rows, 220 objects, MISSING 0, UNSUPPORTED 0, 5 dispositions.

## Round 5 (21 Oct 2026): the owner's traced edges, the T2 runoff, kerb runs, the texture pass

Owner inputs: his T2 / T4 drawings (owner/t2_edges.json, owner/t4_edges.json; compare/owner_edges.py reproduces both
hand JSONs, max 0.046 m) and his lap-1 findings (owner_findings.md: disjointed kerbs, Star Mazda kerb, textures).

### A. The owner-traced edge (`spline.owner_edges`)

- Readings: one per station and side on the CURRENT centre (edges_spline.owner_readings), from his drawing's continuous
  lines (owner_chains: single linkage 3 m, lines of >= 5 points), each line given to the side of the centre holding most
  of it. The JSON's own left / right labels came from the run-32 centre: at T4 1118-1137 the RIGHT line's points carried
  the 'left' label (he drew no left line there); the chain rule fixes that, and one stray point is dropped.
- In the fit: one 'owner' row per station (the side's kind counts and bias gate see it once) plus a weighted anchor
  (OWNER_W 40) so his line outweighs the third-difference penalty; capture rows are replaced only within 3 stations of a
  reading of his (T4 left 1115-1137, where he drew nothing, keeps the captures).
- `kerb_inside` (T2 right 582-605, T2 left 535-545, T4 left 1086-1114, config stations): the reading moved outward by
  the kerb width 0.9 m, ramped in over 6 stations at each end (a 0.9 m step in a reading is no edge; run 41 failed on
  exactly those steps).
- Gate `owner edge <side> <lo>-<hi>`: >= 90 % of stations within 0.25 m, max <= 0.5 m (edge_gate.FITTED, tighten only).
- `centre.prior_shift`: T2 knots from his midline (8 knots, blend 20), T4 4 knots (the 1134 knot came from the mislabelled
  points and is gone).
- Bugs found on the way (fixed, tested): the right side's readings had the wrong sign (run 36: residual 50 m); the final
  refit used features from an earlier remap while its kerb-search zones came from the new one (run 40 stopped at
  'kerb_search (right, 1921, 1939): ends in different feature zones' once the stations moved ~9 m).
- New config (evidence): the T4-exit left block line s 1198-1274 is ONE kerb_band zone with a search window (-8, 1.5)
  (c20_s1300, stage3_evidence/gap1215_r32.png): with the T4 owner edge the left curve had left it for the apron's outer
  boundary 6 m out (63-station gap, run 41-42).
- Stage-1 runs 35-44 (logs in stage3_evidence/geometry_run3x/4x.log). The T11-exit waviness exemption tried in run 38
  is NOT kept: on the final geometry that stretch is 0.024 m (<= 0.04) without it.

### B. Stage 1 (run 44, published)

Length 4704.32 m (was 4697.63). Every gate ok: owner edge T2 left 90.9 % (p50 0.045 / p90 0.228 / max 0.429 m), T2
right 97.0 % (0.052 / 0.183 / 0.314), T4 left 98.9 % (0.054 / 0.157 / 0.294), T4 right 100 % (0.040 / 0.102 / 0.204);
fit left bias 98.4 % of windows, coverage 58 %, longest gap 33; fit right bias 97.6 %, coverage 61 %, longest gap 32;
waviness 0.020 / 0.025 m; kink 0.22 / 0.26 deg; edge gate rms 0.052 / 0.051 m, max step 0.082 / 0.078 m; world
continuity 0.0067 / 0.0076 m; profile 0.018 m; cross slope 9.4 %.

Width (left + right half-width, m) at the package's own stations, run 32 (round 4) -> run 43 (owner edges; run 44 adds
only the Dog Leg zone): T2 500 12.6->10.2, 540 10.4->11.2, 560 8.1->10.6, 580 6.7->11.2, 600 7.6->11.4, 620 9.7->10.6,
640 11.6->10.9, 660 13.2->11.0, 680 15.0->11.2, 700 15.1->12.1; T4 1030 11.3->11.6, 1060 9.5->10.7, 1075 8.9->10.2, 1090
9.0->10.6, 1105 9.8->11.3, 1120 10.9->10.5, 1135 12.2->10.5, 1150 13.3->11.1, 1165 13.1->12.1, 1180 11.5->12.8. The T2
apex is 4.5 m wider than round 4's (6.7 m), as his lines show.

The owner-edge table (published edge against his line):

**owner/t2_edges.json left 502-676** (every 10th station; owner = his line on the current centre, kerb_inside shift included; fit = the published edge; half-widths in m)

| station | owner | fitted edge | residual |
|---|---|---|---|
| 504 | 5.22 | 5.14 | -0.08 |
| 514 | 5.28 | 5.30 | +0.02 |
| 525 | 5.54 | 5.52 | -0.02 |
| 535 | 5.72 | 5.49 | -0.23 |
| 546 | 5.17 | 5.46 | +0.29 |
| 556 | 5.67 | 5.52 | -0.14 |
| 566 | 5.32 | 5.14 | -0.18 |
| 576 | 5.01 | 5.21 | +0.21 |
| 587 | 6.17 | 6.06 | -0.11 |
| 597 | 6.05 | 6.08 | +0.03 |
| 608 | 5.42 | 5.50 | +0.08 |
| 618 | 5.16 | 5.18 | +0.02 |
| 629 | 5.18 | 5.18 | +0.01 |
| 639 | 5.43 | 5.41 | -0.02 |
| 649 | 5.54 | 5.55 | +0.00 |
| 659 | 5.55 | 5.54 | -0.00 |
| 669 | 5.51 | 5.52 | +0.01 |

**owner/t2_edges.json right 502-676** (every 10th station; owner = his line on the current centre, kerb_inside shift included; fit = the published edge; half-widths in m)

| station | owner | fitted edge | residual |
|---|---|---|---|
| 503 | 4.90 | 4.97 | +0.07 |
| 513 | 5.18 | 5.16 | -0.02 |
| 523 | 5.56 | 5.66 | +0.10 |
| 533 | 6.15 | 6.03 | -0.11 |
| 543 | 5.57 | 5.49 | -0.08 |
| 553 | 4.84 | 4.94 | +0.10 |
| 563 | 5.41 | 5.35 | -0.06 |
| 573 | 5.82 | 5.73 | -0.09 |
| 585 | 5.68 | 5.55 | -0.13 |
| 597 | 5.34 | 5.45 | +0.11 |
| 608 | 5.59 | 5.45 | -0.14 |
| 618 | 5.35 | 5.40 | +0.05 |
| 628 | 5.51 | 5.46 | -0.04 |
| 638 | 5.39 | 5.43 | +0.04 |
| 649 | 5.41 | 5.41 | -0.00 |
| 659 | 5.47 | 5.45 | -0.02 |
| 670 | 5.48 | 5.50 | +0.02 |

**owner/t4_edges.json left 1049-1162** (every 10th station; owner = his line on the current centre, kerb_inside shift included; fit = the published edge; half-widths in m)

| station | owner | fitted edge | residual |
|---|---|---|---|
| 1049 | 5.41 | 5.27 | -0.13 |
| 1059 | 5.11 | 5.17 | +0.05 |
| 1069 | 5.41 | 5.42 | +0.00 |
| 1079 | 5.55 | 5.43 | -0.12 |
| 1090 | 4.89 | 5.05 | +0.16 |
| 1101 | 5.24 | 5.16 | -0.08 |
| 1111 | 5.49 | 5.50 | +0.01 |
| 1137 | 5.18 | 5.21 | +0.03 |
| 1147 | 5.26 | 5.25 | -0.00 |
| 1158 | 5.82 | 5.83 | +0.01 |

**owner/t4_edges.json right 1049-1162** (every 10th station; owner = his line on the current centre, kerb_inside shift included; fit = the published edge; half-widths in m)

| station | owner | fitted edge | residual |
|---|---|---|---|
| 1049 | 5.57 | 5.66 | +0.09 |
| 1059 | 5.58 | 5.54 | -0.04 |
| 1069 | 5.04 | 4.98 | -0.06 |
| 1079 | 4.62 | 4.74 | +0.12 |
| 1089 | 5.52 | 5.49 | -0.03 |
| 1099 | 6.21 | 6.14 | -0.07 |
| 1109 | 5.67 | 5.64 | -0.02 |
| 1119 | 4.73 | 4.90 | +0.16 |
| 1129 | 5.05 | 4.98 | -0.07 |
| 1139 | 5.54 | 5.50 | -0.04 |
| 1150 | 5.80 | 5.76 | -0.03 |


### Dog Leg zone 1830-1856 L (retry): kept

Feature + kerb_search ('left', 1830, 1856, (-8.0, 1.5)) on c20_s1900 / c20_s1950 (stage3_evidence/dog1843.png): the
left edge now runs on the separation blocks (dog1843_r44.png). Run 44 passes every gate. The coupling of run 33 was the
T11-exit waviness (0.047 m there in runs 33 and 37 without the zone too): it moved with the held T2 widths; with the T2
edges set it is 0.025 m. The round-4 strip 6.65 m inside the road is gone: the run 1843-1851 L sits -0.56..-0.34 m.

### C. The T2 runoff

`scenery.runoff_zones` 'T2 runoff' (left, s 605-640, width 10.2-22.2 m): from the fitted left edge (his red line) to the
outer-loop block line, between his two green end lines (owner/t2_edges.json green at s 579-608 and 635-647). The outer
line: his green 1 outer end, the block line traced on his frame of the 2026 capture (white blocks 12-34 m left of the
centre, s 608-642, 2-station median), his green 2 outer end. Listed in gates.allowed (containment ok: 3407 rays onto
allowed runoff). The block line is drawn as 15 `blocks` runs (0.5 x 1.0 x 0.12 m every 2 m, drawn only). Surface
'asphalt' (texture pass, below: the zone overlaps the outer loop's own paving).

### D. Judge r4 items

- Pit-entry strip: removed (see the texture pass: the lane, paved to its walls, covers 99.8 % of it).
- T5 exit apron 1700 L: FALSE. stage3_evidence/t5apron.png (c20_s1750): dirt beside the left edge 1650-1750; the paved
  branches there are the closed roads on the right. No apron.
- Tower: the upper storey is an open deck (rect l 9 w 6), roof on 6 posts, railing (structure_timing_tower_* stills).
- 4068 R: closed. t134 shows the single cone already placed (4071 R); no branch is outlined there.

### E. Kerb runs (owner lap 1: "a lot of weird, disjointed kerbs")

Round 4 published 161 strips of <= 10 m, each with its own `off`: 114 joins within 3 m, 21 stepping over 0.3 m (up to
1.20 m at 3781 R). Now ONE run per block line (39 runs, 1420 m): `kerbs_declared` entries with `line_latlon` (the band
centre's world line: the extent pass's per-station outer limits on the round-5 edges, band centre 0.45 m inside;
contiguous extents and the two declared merges (T4 apex left 1086-1114, his kerb_inside; T4-exit left 1203-1272, the
stage-1 zone) joined; end readings over 0.35 m off the run's median trimmed). The builder projects the line every build,
smooths the offset (median 9, Gaussian 4: the reader alternates between a block's inner and outer limit on some lines)
and publishes one strip with `offs` per station; the kit moves every column by it and the paint's colour cycle runs on
over the run. Gate: max station-to-station offset step <= `kerb.run_max_step` 0.1 m (stage fails above). Runs with no
band-reader hit on the new edge (T4 apex left, T4 exit left 1203-1213 before the merge, T4 exit right 1168-1191) keep
their round-4 extent at the standard band centre. One run stands 1.48 m inside the edge (2846-2852 L, reported). Round
4's dropped strips stay dropped (1960 L, 1922 R, 548 R, 583 L).

| side | s (m) | length | offset (m, + out) | max step (m) | profile |
|---|---|---|---|---|---|
| left | 283-322 | 40 | -0.64 .. -0.37 | 0.030 | flat paint |
| left | 535-548 | 14 | -0.10 .. +0.26 | 0.036 | flat paint |
| left | 744-766 | 23 | -0.64 .. -0.23 | 0.036 | flat paint |
| left | 953-1010 | 58 | -0.64 .. -0.45 | 0.021 | flat paint |
| left | 1088-1115 | 28 | -0.45 .. -0.43 | 0.002 | flat paint |
| left | 1202-1271 | 70 | -0.77 .. -0.29 | 0.035 | flat paint |
| left | 1336-1394 | 59 | -0.63 .. -0.37 | 0.020 | flat paint |
| left | 1447-1477 | 31 | -0.68 .. -0.34 | 0.034 | flat paint |
| left | 1539-1572 | 34 | -0.58 .. -0.41 | 0.017 | flat paint |
| left | 1651-1678 | 28 | -0.61 .. -0.21 | 0.030 | flat paint |
| left | 1841-1849 | 9 | -0.56 .. -0.34 | 0.044 | flat paint |
| left | 2536-2541 | 6 | -0.61 .. -0.54 | 0.015 | flat paint |
| left | 2686-2743 | 58 | -0.56 .. -0.23 | 0.030 | flat paint |
| left | 2846-2852 | 7 | -1.68 .. -1.25 | 0.077 | flat paint |
| left | 3002-3010 | 9 | -0.55 .. -0.25 | 0.044 | flat paint |
| left | 3336-3379 | 44 | -0.53 .. -0.29 | 0.032 | flat paint |
| left | 3466-3514 | 49 | -0.67 .. -0.30 | 0.016 | flat paint |
| left | 3687-3756 | 70 | -0.52 .. -0.31 | 0.013 | flat paint |
| left | 3841-3872 | 32 | -0.55 .. -0.27 | 0.039 | flat paint |
| left | 3968-4019 | 52 | -0.63 .. -0.39 | 0.027 | flat paint |
| left | 4376-4401 | 26 | -0.84 .. -0.41 | 0.084 | flat paint |
| right | 188-268 | 81 | -0.50 .. -0.35 | 0.017 | flat paint |
| right | 360-376 | 17 | -0.57 .. -0.40 | 0.021 | flat paint |
| right | 410-424 | 15 | -0.44 .. -0.18 | 0.041 | flat paint |
| right | 583-603 | 21 | +0.01 .. +0.36 | 0.039 | flat paint |
| right | 1019-1048 | 30 | -0.72 .. -0.37 | 0.034 | flat paint |
| right | 1167-1190 | 24 | -0.45 .. -0.44 | 0.001 | flat paint |
| right | 1303-1308 | 6 | -0.63 .. -0.42 | 0.045 | flat paint |
| right | 1493-1513 | 21 | -0.65 .. -0.49 | 0.014 | flat paint |
| right | 1777-1816 | 40 | -0.62 .. -0.37 | 0.011 | flat paint |
| right | 1866-1931 | 66 | -0.29 .. +0.20 | 0.034 | flat paint |
| right | 2312-2337 | 26 | -0.50 .. -0.27 | 0.028 | flat paint |
| right | 2762-2789 | 28 | -0.48 .. -0.33 | 0.014 | flat paint |
| right | 3396-3447 | 52 | -0.55 .. -0.34 | 0.018 | raised 0.06 / 0.15 / 0.30 m |
| right | 3790-3806 | 17 | -0.42 .. -0.01 | 0.027 | flat paint |
| right | 3890-3931 | 42 | -0.94 .. -0.38 | 0.058 | flat paint |
| right | 4025-4122 | 98 | -0.74 .. -0.38 | 0.022 | flat paint |
| right | 4316-4365 | 50 | -0.65 .. -0.21 | 0.039 | flat paint |
| right | 4419-4496 | 78 | -0.67 .. -0.37 | 0.038 | flat paint |

**Star Mazda (T9).** Raised: the apex run right 3396-3447. HEIGHTS.md horizon ratio: camera height 1.49 m from the CRX
ahead in t116 (roof 1.29 m, 76 px, base row 363, horizon row ~275); t114 (1:52) shows the apex kerb's sloped track-side
face 10-15 px tall at base row ~555 (horizon ~265): 0.05-0.08 m, 0.06 m used, face 0.15 m, back 0.30 m. The exit kerb
(left 3466-3514, t116 1:56) shows a face of 1-2 px (<= 0.02 m at 0.8 cm/px): flat paint. No other frame on the lap shows
a raised kerb face (the circuit's other block lines are flat paint, HEIGHTS.md row 7). The profile is per run
(`kerbs.strips[].profile` over the track default; physics `buildKerbStrips`, the app's kerb paint follows it); the kerb
traversal gate covers it (3 passes, line -1 / 0 / +1 m: no roll past 15 deg, no wheel lifted).

### F. Texture pass (owner lap 1: "some screwed up textures")

Poses: structure_stills/textures_r5/poses.json (213: every paved area, every paved zone, three points of the pit lane,
every kerb run, nine road spots), each from 0.5 m looking along, 0.5 m turned 60 deg toward the verge, and 2.5 m looking
down 30 deg; the camera stands 4 m ahead of the car (pose_walk `eye`). Stills: textures_r5/*_r5.jpg (final),
pass1/ (before), pass2/ (after the first fixes).

| # | where | what | stills | outcome |
|---|---|---|---|---|
| 1 | the 8 `apron` areas | 1.5 m cells, a tone step per cell, cells dropped near the outline: a flat staircase of grey squares | pass1/area_apron_* | FIXED (kit): a 0.5 m grid of shared vertices, smooth tone (two noise octaves, +-6 %), vertex-alpha fade over 2.5 m of the outline |
| 2 | pit-entry strip | a flat untextured slab over the pit lane, blocky edges, a tone step against the lane | pass1/area_pit_entry_strip_*, pass2/pit0_10_* | FIXED (config): removed; the lane covers 99.8 % of it |
| 3 | front-straight crossover, Atlantic (mouth parts) | dirt blotches through the asphalt: the track's shoulder drew over the zone | pass2/zone_front_straight_*, zone_Atlantic_* | FIXED (kit + config `paved_zones_over`): zone road quads in front (closed roads ahead of runoff), its shoulder behind |
| 4 | T2 runoff / outer T2 loop | tan / grey blotches: the two zones overlap at different heights | pass2/zone_T2_runoff_* | FIXED: runoff surface 'asphalt' (one material), closed road in front |
| 5 | crossover mouth parts | the paving ends square-cut against the dirt | zone_front_straight_crossover__OSM_34351026__low_r5 | OPEN (geometry of the part ends) |
| 6 | racing surface T4 entry s ~1100, T4 exit s ~1203 | white smears on the asphalt: bright NAIP marks kept as paint by the asphalt grade (luminance > 0.58) | road_s1100_high_r5, kerb_L1203_high_r5 | OPEN (needs a ghost / paint-over of those marks, stage 2) |
| 7 | aprons | flat colour, no grain at 0.5 m | area_apron_left_s_3701_3783_low_r5 | OPEN (kit: the asphalt detail texture is not available to paved areas) |
| 8 | asphalt at 0.5 m | the detail texture reads coarse and stretched at grazing angles | road_s2450_low_r5 | OPEN (UV scale / anisotropy; not seen at the hood height) |
| 9 | pit lane, the eight kerb runs checked, crossover OSM 34351015, Pacific, Sweeper, Zorros, drag strip, Dog Leg | no seam, smear or step | pit0_*, kerb_*, zone_* | ok |

### Stage 3 (published, rev b3bd33079b)

Every gate ok (barrier gaps 2.47 m over 11 runs; containment 0 escapes, 3407 rays onto allowed runoff; pit connectivity
386 / 382 m, 0 crossings; wall ends cushioned). Coverage: 87 rows, 130 objects, MISSING 0, UNSUPPORTED 0, 5 dispositions.
Stage 4: compare_sheets/ (50 sheets with pit frames), compare_sheets/hood_r5/ (16), structure_stills/*_r5.jpg (71, r4 set
in structure_stills/r4/), compare_sheets/prefix_r5/ (the same before the texture fixes).

## Round 6 (21 Oct 2026): judge r5 (GPT 6 Astra, checked by the orchestrator)

No stage-1 change: track.json and heightfield.bin are byte-identical to rev b3bd33079b (`git diff ec813d9` on both
empty). Stage 3 every gate ok; published rev 84a9fc7678.

### Settled FALSE (judge_r5.md), with the package object

- Stations "on a single stem above a solid pedestal": the kit's canopy style on the frames (stage3_evidence/station_crops.jpg), unchanged.
- Kerbs "missing" within the 30 m mapping tolerance: the runs 584-604 R, 1168-1191 R, 1449-1479 L, 1653-1680 L, 2765-2792 R, 1203-1272 L, 1495-1515 R, 1868-1933 R, 4424-4501 R (manifest Round 5 / E).
- Single cones and short lines "missing": placed (scenery.json cone_lines; 0.7 m, too small for the sheet).
- back_07 4700 L tower, side_10 3765 R station: behind the camera.

### TRUE / CHECK rows

| row | finding | outcome |
|---|---|---|
| Timing tower massing (fwd_15, side_13, side_14, back_00, pit_01, pit_02) | round 5 glazed both storeys over the whole 25 x 19 m roof outline | FIXED: the tower is the east 14 m of the outline (c20_p0420 / c20_s0050, structure_stills/tower_cap_r6.png): a solid tan lower storey 14 x 14 m with two doors and windows every 4.5 m (kit: block `windows` / `doors_at`, no continuous band), the deck rail and the exterior stair at its west end; the upper storey 11 x 8 m set back, windows between posts on the lane side and the ends (glazed upper only); the blue roof 17 x 16 m on 6 posts (1.5 m overhang). The west 11 m: an open shade roof on posts, 2.6 m (pit video t1312000's dark shade roof); the north 5 m strip behind the tower a plain 2.6 m block. Stills r6_tower_close / r6_tower_from_lane |
| Pit lane paving, left edge (pit_01, pit_02) | white line and a tan strip to the paddock-side wall | FIXED: `to_walls` reach 4 -> 6 m (the wall stood 4.1-5.3 m past the left edge at x -150..+9; 570 edge points now meet the walls); the left edge line dropped (`pit_lane.no_edge_line ['left']`, kit) |
| Pit-lane cones (pit_01 4490-4514 L, pit_02 4665-4690 L) | the round-4 removal took the frame's row too | FIXED: one row of 6 small orange cones, 10 m apart, along the paddock-side wall abeam s ~4612-4662 (t1267000), and the tower-foot pair, yellow + orange (t1312000 / t1339000); 0.4 m off the wall at the edge of the lane paving (the pit-connectivity gate keeps the lane clear: at 2.5 m they stood inside the lane). Inventory rows added (pit scope, s 4637 and 4697 left). None elsewhere |
| Pit-entry fence (pit_00 4294-4318 L, fwd_14 4300 L) | the fence 1.0 m from the lane | FIXED: re-measured on the tree line's lane-side edge (c20_s4400 / c20_p0180, stage3_evidence/fence_r6.png) where t1231000 shows its posts beside the parked trucks: 20-27 m from the lane edge (the brief's 5-10 m is not what the capture shows) |
| Pit-wall nose (pit_01 4490 R) | an isolated plinth, then a wall with a square start | FIXED: on t1231000 / t1240000 the station stands on the broad head of the separation barrier: the berm (impact, rounded) now wraps the wall's square end by 0.8 m (builder `overlap`), 3.4 m long; the station moved from 1.7 m beside the wall onto its line, 1.6 m from its start |
| Aprons and the T2 runoff (fwd_00, fwd_01, fwd_03, back_01, side_02, runoff_04) | aprons read as dirt without grain; the T2 runoff a dark band | FIXED (kit): surface 'apron' = pale weathered asphalt with the asphalt detail grain (photoGround `apron`), the 8 apron areas through the paint surface (their weight fading over 2.5 m of the outline into the photo), the T2 runoff and the outer T2 loop it overlaps in the same look. Inside T2 (side_02 574 R): the terrain lies 0.10-0.35 m BELOW the edge 2-20 m in at 560-605 (heightfield), no bank: the look made it read so. T1 inside 200-250 R on c20_s0300: dirt, no apron (FALSE) |
| Crossover mouths (side_00 21 / 46 / 146 R, fwd_15 4600-4650 R) | a dirt wedge between the zone and the edge | FIXED: zone ends within 1.5 m of the road have their end points moved along the zone onto the road, 0.3 m inside (`scenery.zones_meet_edge`; 20 points) |
| NAIP smears (fwd_09 2800-2850 L, T4 ~1100, ~1203) | bright NAIP marks kept as paint | FIXED (config-gated `scenery.ortho_paint_over`, stage 3's ortho step): 5 outlines on the package ortho (stage3_evidence/smears_r6.jpg); only road pixels brighter than the road's median there change: 42 + 21 px at 2825, 112 px at 1100 (the NAIP kerb blocks now inside the owner-traced edge), 7 + 38 px at 1203. fwd_08 2550 R chevrons: still open |
| Kerb 4300-4320 R | run starts 4321 | FALSE: c20_s4450 shows the block line beginning where the run begins; t140's kerb at ~4300 is the time map's +-30 m |
| Kerb 4350-4380 L | run starts 4381 | FALSE: c20_s4450 / c20_s4500: the inside blocks begin at ~4383 |
| Kerb 536-552 L | run ends 549 | FIXED: c20_s0650 shows the blocks on to ~558; the run extended at its last offset |
| Kerb 410-424 R (back_00 500 R) | the onboard line runs to ~500 | FALSE: c20_s0550 / c20_s0600 show no blocks on the right after 425 |
| Kerb 4381-4406 L colours | "pale edging without coloured blocks" | FALSE: the run is red / white / blue (scenery.json), as t142 shows |
| Kerb 3005-3013 L (EXTRA) | | FALSE: c20_s3100 shows the short white block line there; kept |
| Masts (fwd_11 3400 L, back_05 3500 R) | the comms tower as a thin pole | FIXED (kit): style 'lattice': three tapering legs (4 m -> 1.2 m), bracing every ~3 m as ONE merged mesh, a 3.0 x 1.8 m pale head that reads from both sides (the 3500 R head seen from behind is this tower) |
| 21 R cone pair | one yellow, one orange | FIXED: two declarations, one each |
| K-rail dark section (side_00 104 L) | not seen | FALSE: the section is in the package (286-292 m along the pit wall, x 111-117, track s ~98-104), beside / behind the 104 L pose; still r6_dark_krail_section |
| 3200-3250 L cone cluster | density | FIXED: t108 shows two at the mouth (was three) |
| Starter's stand (side_13 4693 L) | heavy frame, solid canopy | FIXED (kit): platform `fine`: 6 cm legs with X braces, a thin deck, a thin roof on four thin posts (t1339000) |
| K-rail profile (sloped faces), stepped section joins near the building | | OPEN (kit items, low) |

### Stage 3 (published, rev 84a9fc7678)

Every gate ok: barrier gaps 2.47 m over 11 runs; containment 0 escapes (3428 rays onto allowed runoff); pit connectivity
386 / 382 m, 0 crossings, the lane clear; wall ends cushioned; coverage 87 rows, 135 objects, MISSING 0, UNSUPPORTED 0.
Stage 4: compare_sheets/ (50 sheets with pit frames), compare_sheets/hood_r6/ (16), structure_stills/*_r6.jpg (80: the
round-5 set plus 14 round-6 poses: the tower, the pit lane and its cones, the nose, the pit-entry fence, the starter's stand,
the lattice tower front and back, the T2 apron and runoff, a crossover mouth, the paint-overs, the dark K-rail section);
the round-5 sets in compare_sheets/r5/ and structure_stills/r5/; compare_sheets/r6_pre_annex/ and
structure_stills/r6_pre_annex/ are the same before the west annex became an open shade roof.

## Round 7 (21 Oct 2026): judge r6 (Astra for 7 batches, the orchestrator for the rest), cosmetic

Geometry byte-identical to b3bd33079b (`git diff ec813d9` on track.json and heightfield.bin empty). Stage 3 every gate ok;
published rev b7a674a6da.

### Settled FALSE in judge_r6.md

Stations, kerbs within the mapping tolerance, placed cones, the pit-lane lead-in cones (the 4612-4662 row seen from
120 m), the dark K-rail section (renders at s 98-104), the pit-entry fence (20-27 m out), the station base at 800 R, the
paddock-side K-rail at 4593-4662 L: each as judge_r6.md cites, objects unchanged.

### TRUE / CHECK rows

| row | outcome |
|---|---|
| Apron tone (side_02 574 R, side_05 1309 R / 1344 L / 1476 L, fwd_04 1300-1450) | FIXED (kit): the apron's weight is a straight 1 m feather on the signed distance to the outline (-0.5..+0.5 m), so its own colour covers the area; the tone pale grey-beige (0.50, 0.49, 0.46) with little of the photo's light / dark (t024 / t058). The T2 runoff and the outer loop share it. Stills structure_stills/textures_r7/area_* (pass1/ before the road clip) |
| Apron fade edge (back_05 3000 R) | FIXED: `scenery.aprons_meet_road`: each apron outline is clipped to the road polygon (the outline's own steps along the track edge made the bites), the road-edge segments unfaded (`feather` per segment) and the apron drawn over the track's shoulder there; a narrow straight strip of the shoulder remains at the edge line |
| Tower roof (fwd_15 4600-4650) | FIXED: the roof sits on the upper storey (underside 6.1 m), fascia 0.9 m, a darker fascia tone |
| Tower annex (pit_02 4640) | FIXED (kit `edge_posts`): the shade roof stands on thin posts along both long edges with a thin dark fascia: open from the lane (r6_tower_close_r7). The white block behind it is the OSM 765811056 building (plain white walls, t1312000 / t1330000), unchanged |
| runoff_04 623 dark / light division | left: the track tone at T2 is the ortho's; the runoff now pale as the aprons |
| pit_00 4294-4318 R hatch, fwd_08 2550 R chevrons | FIXED: two `ortho_paint_over` outlines with `on='any'` (off the road; a yellow cast counts as a mark too): 441 px in the pit-entry gore, 495 px on the drag-strip crossing (stage3_evidence/hatch_chevrons_r7.jpg) |
| Paddock buildings behind the pit wall west of the tower (fwd_00 0 L) | FIXED, one: the pit video t1267000 / t1303000 shows a long low dark shade roof on posts behind the paddock-side K-rail west of the tower; the only roofed structure there in the lidar is the 29 x 8 m footprint at (35.4896585, -119.5454773), 3.7 m (outside the 2026 clean captures): drawn there as an open shade roof on edge posts (structures 'paddock shade roof'), inventory row added (pit scope, s 4618 L). The pop-up tents and trailers: temporary, not placed. The other dropped lidar footprints stay dropped (no frame attributes a building to them) |
| 3200-3250 L cluster | FALSE: t108 zoomed shows one standing orange cone and a thin dark marker post at the mouth (and debris); t110 none; the package's 2 stand |
| 21 R yellow cone | FALSE: the package has it yellow (#e8c21c) and it renders yellow (r7_cones_21R_r7) |
| Pit stand rail (pit_02 4690 R) | FIXED (kit, `fine` only): a mid rail and balusters every 0.3 m |
| K-rail sloped profile, stepped joins | OPEN (kit, low) |

### Stage 3 (published, rev b7a674a6da)

Every gate ok (containment 0 escapes; pit connectivity clear; coverage 87 rows, MISSING 0, UNSUPPORTED 0). Stage 4:
compare_sheets/ (50 with pit frames), compare_sheets/hood_r7/ (16), structure_stills/*_r7.jpg (90, incl. the aprons, the
tower from the lane and close, the stand, the 21 R pair, the hatch and chevrons) and textures_r7/ (42 apron and zone
stills); round-6 sets in compare_sheets/r6/ and structure_stills/r6/.

## Round 8 (21 Oct 2026, checkpoint): the owner's lap 2, notes 1-24 (in progress)

Geometry changed (owner notes 6, 8, 20, 21, 23). Stage 1 run 85 every gate ok (28 lines, owner edges T2 / T4 and the
Dog Leg zone included); lap 4703.81 m (was 4704.32); track.json sha256 b592641cf7cb3177..., heightfield.bin c36561136e37069c...;
published rev 37991e53ab.

### Straights (config `straights`, new options `once` and `width_shared` in straights.py)

- Sunset, both sides, config 4192-4276 (current 4203-4287): read once from 3.5 m inside the first fit's edge (reading
  around the moving edge walked the line outward: run 80 19 m, run 82 16.3 m). Width 12.6-12.9 m over 4210-4290 (was
  12.3-17.1 with the bulges). The right-side readings at 4241-4258: lighter, rutted dirt beside the asphalt, no structure;
  the left bay 4241-4270: the T11-approach station mound area (2-8 m off the asphalt). The Zorros-mouth fillet 4130-4190
  (exempted) still reads 13.7-17.2 m.
- Drag strip, config 3022-3374: left read once, right PARALLEL to it (`width_shared`): one width, 11.44 m (was 11.8-16.2).
- Front straight, config 4525-180: right (south asphalt end) read once, left PARALLEL at the dark / pale tone step
  (the asphalt_end detector read from 7 m inside the old edge): one width, 13.12 m (was 19.2 at 4540 to 15.8 at 160).
  The pale strip between it and the pit-wall K-rail: two runoff zones in the apron look ('front straight pale strip'
  west / east, 7.5-8.5 / 5.6-8.0 m wide), K-rail unchanged; pit connectivity ok.
- Capture ruler checks: the automatic dark-band ruler (tools: /tmp ruler, the dark band against the road median + 18) is
  unreliable here (dirt and asphalt within 18 grey levels: 11-28 m readings): OPEN, to measure by eye on ruled windows.
- The T4-T5 edge-gate exemption right widened 1370 -> 1365 (config), the same apron step (cw_1348.png) now reached at
  config 1368 (run 84: 0.101 m).

### Kerb heights (notes 1, 2, 3, 19, 22): measured, NOT applied (gate decision pending)

Lidar (2021, class-2 ground, first returns; tools: /tmp/bw_tools/kerb_heights.py, stage3_evidence/kerb_heights_lidar_r8.json):
per station the asphalt line on the 1.6 m inside the band, extrapolated under it; the run's step = median, sigma = MAD.
The steps do not resolve kerbs: the T9 apex (6 cm on t114) reads 0.0 ± 0.2 cm, and every negative value is the road's
crest or banking (the Cotton hilltop run 1020-1049 R, raised on the third video, reads -9.3 cm). The ground
classification removes kerb tops; the lidar cannot settle heights.

| run | stations | points | lidar step |
|---|---|---|---|
| left 283-322 | 40 | 827 | -2.6 ± 0.2 cm |
| left 536-558 | 23 | 492 | +0.9 ± 0.7 cm |
| left 745-767 | 23 | 454 | +0.1 ± 0.2 cm |
| left 954-1011 | 57 | 1036 | -0.4 ± 0.2 cm |
| left 1089-1116 | 28 | 2406 | +0.5 ± 0.4 cm |
| left 1203-1272 | 69 | 2338 | +0.2 ± 0.1 cm |
| left 1338-1396 | 59 | 2211 | +1.8 ± 0.2 cm |
| left 1449-1479 | 31 | 695 | +1.3 ± 0.1 cm |
| left 1541-1574 | 34 | 608 | +1.9 ± 0.3 cm |
| left 1653-1680 | 28 | 489 | +2.6 ± 0.2 cm |
| left 1843-1851 | 9 | 190 | +0.9 ± 0.4 cm |
| left 2539-2544 | 6 | 198 | -2.6 ± 1.1 cm |
| left 2689-2746 | 55 | 925 | -4.7 ± 0.2 cm |
| left 2849-2855 | 7 | 100 | -8.5 ± 1.9 cm |
| left 3005-3013 | 9 | 150 | -7.2 ± 0.5 cm |
| left 3340-3383 | 43 | 743 | -10.2 ± 0.3 cm |
| left 3470-3518 | 49 | 850 | +1.7 ± 0.3 cm |
| left 3691-3760 | 65 | 1007 | +0.1 ± 0.2 cm |
| left 3845-3876 | 32 | 544 | +0.7 ± 0.2 cm |
| left 3972-4024 | 45 | 649 | +0.6 ± 0.2 cm |
| left 4381-4406 | 26 | 886 | +2.6 ± 0.6 cm |
| right 188-268 | 81 | 1625 | +3.3 ± 0.2 cm |
| right 360-376 | 17 | 380 | -0.0 ± 0.2 cm |
| right 410-424 | 15 | 303 | -0.1 ± 0.3 cm |
| right 584-604 | 21 | 424 | -0.2 ± 0.1 cm |
| right 1020-1049 | 30 | 616 | -9.3 ± 0.3 cm |
| right 1168-1191 | 24 | 738 | +2.8 ± 0.7 cm |
| right 1304-1310 | 6 | 176 | -7.0 ± 0.1 cm |
| right 1495-1515 | 21 | 400 | +1.9 ± 0.4 cm |
| right 1779-1818 | 39 | 738 | +1.8 ± 0.3 cm |
| right 1868-1933 | 66 | 1244 | -4.5 ± 0.2 cm |
| right 2315-2340 | 25 | 574 | +0.4 ± 0.3 cm |
| right 2765-2792 | 27 | 448 | +0.5 ± 0.4 cm |
| right 3400-3451 | 49 | 743 | -0.0 ± 0.2 cm |
| right 3794-3810 | 17 | 316 | -5.8 ± 0.3 cm |
| right 3894-3935 | 42 | 685 | -9.2 ± 0.3 cm |
| right 4030-4127 | 98 | 2758 | -4.9 ± 0.2 cm |
| right 4321-4370 | 50 | 1392 | -5.3 ± 0.3 cm |
| right 4424-4501 | 78 | 2336 | -0.6 ± 0.2 cm |

Traversal gate (no wheel lifted, 3 passes per run) with every run raised, tried in the test harness: 6 cm / 0.15 m face:
44 of 117 passes lift a wheel; 8 cm / 0.3: 43; 10 cm / 0.3: 44; 10 cm / 0.45: 36; 8 cm / 0.45: 35; 6 cm / 0.3: 37; no
roll past 15 deg in any. The T9 exit alone at 10 cm / 0.2 m: 215-562 ms lifts. The same car-suspension behaviour as
Sonoma's known failure. The T9 exit run stays flat in this checkpoint; the decision is in the report.

### Scenery items done

- Pit boxes (note 9): `pit_lane.lane.boxes = []` (no box lines on t1249000-t1339000); scenery.json pit_lane.boxes; the app
  draws the rule boxes only without the key (Laguna). Still r8_pit_road_8 / r8_pit_road_95.
- Pit-in gore (note 7): the paint-over recolours to the road's median within 15 m (`tone='road'`); the hatch paint left
  out. Still r8_pit_in_gore: tan patches remain on the gore's dirt part (OPEN).
- Apron edge (note 4 / the wedge look beside kerbs): apron vertices snapped onto the outline (no 0.5 m grid steps), the
  1 m fade inward from the feathered segments only.
- Kerb runs: a run under 12 m takes one offset (its median); 1449-1479 L starts 6 m later (the edge-relative ramp at the
  T4-T5 apron step). OPEN: the Dog Leg run 1843-1851 L now stands 1.5 m inside the edge (the edge moved out there).

### Not done in this checkpoint (OPEN)

The CCW video (_7QwJdGQtaE, NASA SoCal HPDE 2 Buttonwillow Classic CCW 4/5/2025, Fast Car Seats; frames t000-t300 in
inventory/frames/ccw_7Qw, local) is grabbed but not yet read for the infield fence (notes 5, 10, 11), the T2-outside tyre
wall (12), kerb faces; the third video (XIxXIvsDz3s) not yet grabbed (notes 17, 19, 22); the tower awning (14), the
paddock layout and buildings (15), the willows (16), the T2 concrete patch (17), surface marks (18), the Cotton K-rail
blocks and the ~1100 stripe (19), per-run kerb width and block length (22), the cone re-reads and the service road (24:
t006 shows four cones parallel to the edge ~3.8 m out, yellow / white / orange / orange), the boundary audit (13), the
raised-kerb mesh check on the curved runs (4: the raised strip is one shared-vertex grid; T9 apex stills show no gaps).

## Round 8 (continued, 21 Oct 2026): the owner's kerb-height decision and notes 9-24 (checkpoint, rev 8736f6da3c)

Geometry unchanged from 8bf8602 (track.json / heightfield.bin identical). Stage 3 every gate ok (containment 0 escapes,
3558 onto allowed runoff; pit connectivity ok; coverage 0 missing, 6 dispositions: + rejected 146 R cones).

### Kerb profiles (the owner's decision: "Lifting a wheel isn't inherently a realism issue. Driving over a kerb and rolling over is an issue." / "I drove over a kerb at Buttonwillow and lifted at least one wheel a few weeks ago.")

- Track default `kerb.profile` 10 cm / 0.15 m face / 0.30 m back on every run ('default raised, no resolving frame':
  the 2021 lidar does not resolve kerb tops; the closest frames show faces without a measurable height). The T9 apex
  keeps its measured 6 cm (t114). The two Dog Leg separation runs (1843-1851 L, 1868-1933 R) roll the car over at 10 cm
  (37.4 deg and 180 deg at line +1 / -1 m) and take 6 cm (max roll 8.9 deg), pending the owner's figure.
- Width per run from the capture band (edges_spline.bands, median over stations x captures; 23 runs differ from
  0.9 m by 0.1 m or more; 3339-3382 L, the Star Mazda entry the owner calls 2-3 m wide, measures 1.24 m on the captures:
  OPEN for the owner). Block length unchanged (1.0 m).
- kerbgate.test.ts: roll past 15 deg relative to the road or a rollover fails (unchanged numbers); wheel lifts are an
  advisory report printed per pass on every track (Sonoma's it.fails removed with it). Max roll: Laguna 7.9 deg (30
  passes), Sonoma 8.38 deg (90 passes, 16 with a lift, as before), Buttonwillow 9.88 deg (117 passes, 43 with a lift).

| run | lidar step | width | profile (h / face / back) | longest lift | max roll | source |
|---|---|---|---|---|---|---|
| left 283-322 | -2.6 ± 0.2 cm | 0.50 m | 10 cm / 0.15 / 0.30 | 0 ms | 4.51 deg | default raised, no resolving frame |
| left 536-558 | +0.9 ± 0.7 cm | 0.60 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.38 deg | default raised, no resolving frame |
| left 745-767 | +0.1 ± 0.2 cm | 1.05 m | 10 cm / 0.15 / 0.30 | 28 ms | 1.54 deg | default raised, no resolving frame |
| left 954-1011 | -0.4 ± 0.2 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 229 ms | 6.11 deg | default raised, no resolving frame |
| left 1089-1116 | +0.5 ± 0.4 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 450 ms | 4.92 deg | default raised, no resolving frame |
| left 1203-1272 | +0.2 ± 0.1 cm | 0.75 m | 10 cm / 0.15 / 0.30 | 472 ms | 7.9 deg | default raised, no resolving frame |
| left 1337-1395 | +1.8 ± 0.2 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 143 ms | 5.39 deg | default raised, no resolving frame |
| left 1454-1478 | +1.3 ± 0.1 cm | 0.65 m | 10 cm / 0.15 / 0.30 | - ms | - deg | default raised, no resolving frame |
| left 1542-1575 | +1.9 ± 0.3 cm | 1.15 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.45 deg | default raised, no resolving frame |
| left 1654-1681 | +2.6 ± 0.2 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 361 ms | 7.96 deg | default raised, no resolving frame |
| left 1843-1851 | +0.9 ± 0.4 cm | 1.10 m | 6 cm / 0.15 / 0.30 | 391 ms | 7.67 deg | 6 cm: 10 cm rolls the car here (gate) |
| left 2539-2544 | -2.6 ± 1.1 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.25 deg | default raised, no resolving frame |
| left 2690-2747 | -4.7 ± 0.2 cm | 1.10 m | 10 cm / 0.15 / 0.30 | 0 ms | 2.97 deg | default raised, no resolving frame |
| left 2850-2856 | -8.5 ± 1.9 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 187 ms | 5.93 deg | default raised, no resolving frame |
| left 3005-3013 | -7.2 ± 0.5 cm | 1.10 m | 10 cm / 0.15 / 0.30 | 0 ms | 1.75 deg | default raised, no resolving frame |
| left 3339-3382 | -10.2 ± 0.3 cm | 1.25 m | 10 cm / 0.15 / 0.30 | 114 ms | 4.07 deg | default raised, no resolving frame |
| left 3470-3518 | +1.7 ± 0.3 cm | 0.75 m | 10 cm / 0.15 / 0.30 | 483 ms | 9.88 deg | default raised, no resolving frame |
| left 3691-3760 | +0.1 ± 0.2 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.29 deg | default raised, no resolving frame |
| left 3845-3876 | +0.7 ± 0.2 cm | 0.75 m | 10 cm / 0.15 / 0.30 | 149 ms | 6.01 deg | default raised, no resolving frame |
| left 3972-4023 | +0.6 ± 0.2 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 309 ms | 7.05 deg | default raised, no resolving frame |
| left 4380-4406 | +2.6 ± 0.6 cm | 1.05 m | 10 cm / 0.15 / 0.30 | 0 ms | 4.9 deg | default raised, no resolving frame |
| right 188-268 | +3.3 ± 0.2 cm | 1.30 m | 10 cm / 0.15 / 0.30 | 147 ms | 5.41 deg | default raised, no resolving frame |
| right 360-376 | -0.0 ± 0.2 cm | 1.10 m | 10 cm / 0.15 / 0.30 | 0 ms | 4.65 deg | default raised, no resolving frame |
| right 410-424 | -0.1 ± 0.3 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 0 ms | 2.12 deg | default raised, no resolving frame |
| right 584-604 | -0.2 ± 0.1 cm | 0.60 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.76 deg | default raised, no resolving frame |
| right 1020-1049 | -9.3 ± 0.3 cm | 1.05 m | 10 cm / 0.15 / 0.30 | 96 ms | 4.47 deg | default raised, no resolving frame |
| right 1168-1191 | +2.8 ± 0.7 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 423 ms | 6.81 deg | default raised, no resolving frame |
| right 1304-1309 | -7.0 ± 0.1 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 151 ms | 4.37 deg | default raised, no resolving frame |
| right 1494-1516 | +1.9 ± 0.4 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.33 deg | default raised, no resolving frame |
| right 1779-1819 | +1.8 ± 0.3 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 278 ms | 6.8 deg | default raised, no resolving frame |
| right 1869-1934 | -4.5 ± 0.2 cm | 0.70 m | 6 cm / 0.15 / 0.30 | 921 ms | 8.9 deg | 6 cm: 10 cm rolls the car here (gate) |
| right 2315-2340 | +0.4 ± 0.3 cm | 1.10 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.03 deg | default raised, no resolving frame |
| right 2766-2793 | +0.5 ± 0.4 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 0 ms | 3.11 deg | default raised, no resolving frame |
| right 3400-3450 | -0.0 ± 0.2 cm | 0.90 m | 6 cm / 0.15 / 0.30 | 0 ms | 5.15 deg | t114 (6 cm measured) |
| right 3794-3810 | -5.8 ± 0.3 cm | 1.10 m | 10 cm / 0.15 / 0.30 | 344 ms | 7.82 deg | default raised, no resolving frame |
| right 3894-3935 | -9.2 ± 0.3 cm | 0.55 m | 10 cm / 0.15 / 0.30 | 283 ms | 5.76 deg | default raised, no resolving frame |
| right 4029-4126 | -4.9 ± 0.2 cm | 0.70 m | 10 cm / 0.15 / 0.30 | 212 ms | 6.54 deg | default raised, no resolving frame |
| right 4320-4370 | -5.3 ± 0.3 cm | 1.15 m | 10 cm / 0.15 / 0.30 | 158 ms | 4.5 deg | default raised, no resolving frame |
| right 4424-4501 | -0.6 ± 0.2 cm | 0.90 m | 10 cm / 0.15 / 0.30 | 535 ms | 9.78 deg | default raised, no resolving frame |

### Other notes

- Note 24 cones: the four t006 cones (yellow, white, orange, orange) as one line parallel to the edge 3.8 m out at s 40-55
  R; the 140-160 R line removed (t008: dark marker posts, no cones; inventory s 146 row rejected in the dispositions;
  s 21 row corrected to 47). The Sunrise-Cotton service road: OPEN (not modelled).
- Note 12: the T2-outside tyre wall, 115 m, 1.0 m, traced on c20_s0700 / c20_s0750 (stage3_evidence/t2tyres_r8.png),
  CCW onboard t286 / t288. The heightfield bump under it: left as is (known lidar artefact, no mask in the pipeline).
- Note 14: the tower centred under the 25 x 19 m roof; the awning (OSM 765811056, 23.6 x 17.4 m, 4.3 m) behind it as an
  open shade roof on posts; the round-6 / 7 annexes removed.
- Note 15: 13 lidar paddock buildings restored, each confirmed on the new 2026 z20 paddock captures (satellite_paddock/
  pad_0-pad_7, local); the paddock lanes (12 OSM service ways) as pale closed roads (no mouths), in gates.allowed until
  the infield fence is placed. The Fast Lane school / kart track: OPEN.
- Note 16: trees from the lidar canopy with the NAIP check off and a 3 m / 6 m minimum crown: 233 crowns, height
  p10 / p50 / p90 12.0 / 15.4 / 19.1 m, crown radius p50 4.8 m (was 30 crowns).
- Dog Leg run 1843-1851 L: the extent pass on the new edges puts the band 1.5 m inside the edge on the separation blocks
  (stage3_evidence/dog_r8.png: the strip sits on the white blocks); the edge itself runs beyond them. Not a misplacement.
- OPEN: the infield chain-link fence (notes 5, 10, 11; CCW t138-t140 show it on posts by the eucalyptus at the pit-out
  end), the T2 concrete patch (17), crack-seal surface marks (18), the Cotton K-rail blocks and the ~1100 stripe (19),
  the pit-in gore's tan patches (9), the boundary audit tool (13), the kerb mesh check on curved raised runs (4).

## Round 8 checkpoint 3 (21 Oct 2026, rev e168ce1ca4)

Geometry unchanged (track.json / heightfield.bin identical to 8bf8602; a full stage-1/2/3 rebuild was needed because the
config's `sources` gained the two videos, and it reproduced them byte for byte). Stage 3 every gate ok.

- Dog Leg kerbs: 10 cm with a 0.30 m face tried (sweep): 1843-1851 L passes its own passes (max 13.8 deg) but the
  1868-1933 R pass at line -1 m crosses it (it stands 1.5 m inside the road on the separation blocks) and rolls over;
  1868-1933 R rolls over at 10 cm with every face 0.15-0.60 m (180 deg at line -1 m). Both stay at 6 cm / 0.15 m (every
  pass under 15 deg), reasons in each profile's comment; pending the owner's figure.
- Star Mazda entry width: left at the measured 1.24 m (owner to mark the extent).
- Infield fence (5, 10, 11): OPEN. Existence: CCW t138-t140 (pit-out end, along the tree line: the round-6 pit-entry
  fence 20-27 m out is that fence's south piece) and t1370 (a chain-link fence at the far right on the T1 side). Position:
  not resolved: on c20_p0780 / c20_s0500 the thin dark line inside the east pit road's curve could not be separated from the
  dirt track edge and the tree shadows by the detector (stage3_evidence attempts not kept). The paddock-lane containment
  allowance stays until it is placed.
- T2 concrete patch (17): placed, 7.6 m2, the pale slab beside the inside kerb on c20_s0700 (stage3_evidence/
  t2patch_r8.png); the part under the parked car on the capture not resolved.
- ~1095 stripe (19): a DARK NAIP mark on the road (stage3_evidence/stripe1100_r8.png), not the round-7 recolour;
  painted over (`ortho_paint_over` with `dark=True`, 43 px). The Cotton K-rail blocks: OPEN (the third video's frames
  grabbed, t440-t620, do not include the Cotton crest).
- Pit-in gore (9): paved over the hatch outline in the lane's tone (#8c8a85); it renders as a flat untextured slab
  (r8c_pit_in_gore_r8): OPEN as a look.
- Service road Sunrise -> Cotton (24): on c20_s0350 / c20_s0400 it is a dirt track (the OSM 'track' type), not paved:
  left as the open dirt it is, no cones.
- Fast Lane school / kart track (15): OPEN (the kart track lies outside the lidar box; OSM has no way for it).
- Crack-seal surface marks (18): OPEN (not started).
- Raised-kerb mesh on curves (4): the r8b / r8c close stills show no gaps at the T9 apex and exit, the Esses, Cotton;
  the 0.5 m stills at the Dog Leg missed the kerb (camera yaw): a re-shoot is OPEN.
- Videos recorded in config `sources`: video_ccw (_7QwJdGQtaE) and video_cw_ftd (XIxXIvsDz3s), with what each was used for.
- Boundary audit (13): tool tools/track/compare/boundary_sheets.py and SKILL 4.1b; run on rev a8c39183b2 (1250 stills,
  53 sheets in boundary_sheets/, local). Read: the paved-area, pit-lane, T2-zone and front-straight groups. Finding: the
  framing (camera over the boundary, looking along it) shows mostly one side, and the apron views read tan (the outer,
  dirt-side boundary): the sheets are not yet a usable audit; the tool's framing (turn toward the surface, both sides)
  is OPEN, and no seam rows are listed from it yet.
- Stage 4: 50 sheets and the hood set (compare_sheets/hood_r8/) and stills r8b / r8c rendered on rev a8c39183b2 (the
  only change to e168ce1ca4: the 1843-1851 L profile 10 -> 6 cm).

## Round 8 checkpoint 4 (22 Oct 2026, rev 2025a3091f)

Geometry unchanged from 8bf8602. Stage 3 every gate ok; kerb roll gate 6 / 6.

- Dog Leg runs (1843-1851 L, 1868-1933 R): flat separation blocks (profile height 0) per the coordinator, pending the
  owner; no CW frame shows them raised (t066-t068: painted blocks).
- Infield fence (5, 10, 11), lidar route (/tmp tool: points 1.3-2.8 m over the DEM with nothing above 3.5 m in a 2 m
  neighbourhood, 0.5 m cells, RANSAC lines): the only linear runs are inside the paddock / east yard clutter (vehicles,
  sheds); the one isolated linear series, x ~ -195 m from y 170 to 625 (west of the paddock), is points every ~20-25 m
  (poles or trees, not a chain-link fence, which would read continuous at 0.5 m); chain-link returns are too sparse to
  show. Not confirmed; nothing placed; the paddock-lane containment allowance stays. Frames that show it: CCW t138-t140,
  t1370.
- Cotton crest (19): the third video t700 (lap 0:32.44) shows the hilltop kerb: a wide dark-painted concrete kerb, raised
  (a pale face on its track side), consistent with the 10 cm default; height not measurable from the frame. The K-rail
  blocks are not in the frames grabbed (t0-t1200 at 2 s; t700-t708 show no blocks right of the crest): OPEN.
- Crack-seal marks (18): `surface_marks` (build_scenery): 261 candidate segments on the clean captures, 111 kept
  (contrast 14, min 3 m, length / width >= 6), published as dark 0.1 m paint lines. At the T2 / front-straight stills
  (r8e_crack_seal_*) they are not visible: the detection is sparse; OPEN to tune.
- Boundary audit (13): framing fixed (camera 1.2 m up, 6 m on the unpaved side, looking across, every 25 m): 743 stills,
  31 sheets in boundary_sheets/ (cp3/ holds the first run). Seam rows from the sampled groups (area, edge L / R, pit,
  zones; about 200 stills read):
  | kind | where | what | status |
  |---|---|---|---|
  | paved area | pit-in gore (pit part 0-25 m, both sides) | flat untextured slab, a hard tone step against the lane | OPEN (the 'lane' look tried rendered near-black; reverted to the lane tone) |
  | paved area | T2 concrete patch (583 R) | flat grey untextured slab | OPEN |
  | pit lane | right side ~175 m | a dark blotch on the ground beside the lane | OPEN |
  | zone | front-straight pale strip west ~75 m | green-toned ground beside the K-rail (C11) | OPEN |
  | zone | front-straight crossover left ~125 m | a yellow-tan NAIP patch left on the asphalt | OPEN (paint-over outline candidate) |
  | edge | left ~1900 (Dog Leg) | a dark brown ground patch, hard tone step | OPEN |
  | area | apron 2963-3025 R start | a lighter triangle where apron and road meet | OPEN |
  | edge / zone | 1800 R, 3600 R | zone ends square-cut against the dirt | OPEN |
  No row was fixed in this checkpoint.
- Pit-in gore (9): the kit's 'lane' look (the road's graded photo) rendered near-black; reverted to the lane tone #8c8a85
  (flat): OPEN.
- Fast Lane school / kart track (15): the Fast Lane garages are among the 13 lidar buildings restored in checkpoint 2
  (pad_3 / pad_4); the kart track (pad_5) is a winding loop with an inner island, which the paved-area kit (one outline,
  no holes) cannot draw: OPEN.
- Kerb mesh (4): close stills facing the runs at the Dog Leg (1842 L, 1868 R), the Esses (3690 L) and the T2 apex (583 R)
  from 0.5 m and 1.5 m (structure_stills/r8d_*): no gaps or tears.
- Videos in config `sources`: done in checkpoint 3.
- Stage 4: 50 sheets and the hood set rendered on rev 8bbcab1d43 (the only difference from 2025a3091f: the gore's look).

## Round 8 checkpoint 5 (22 Oct 2026, rev c0fbb9bd11)

Geometry unchanged from 8bf8602. Stage 3 every gate ok; kerb roll gate ok. Dog Leg runs stay flat blocks pending the owner.

### Boundary seam rows (checkpoint 4)

| row | outcome |
|---|---|
| pit-in gore, flat slab | FIXED (kit): the paved-area branch ignored `look` and drew the flat cell mesh (the cause of the near-black slab in cp4, not the grading); now the toned apron shader with the lane tone (asphalt grain, the photo's light / dark): r8f_pit_in_gore |
| T2 concrete patch, flat slab | FIXED (kit): `look='concrete'`, pale concrete tone with grain; its 1 m feather fades to the tan photo at the edge (it lies on the road): OPEN as a detail (r8f_T2_concrete_patch) |
| pit lane right ~175 m dark blotch | ortho_paint_over (dark, 127 px) |
| pale strip west ~75 m green ground | ortho_paint_over (`all=True`: the whole 12 m box to the ring median, 441 px) |
| crossover left ~125 m yellow-tan patch | ortho_paint_over (yellow, 5 px): the patch in the still persists: it is not in the ortho at that box; OPEN |
| Dog Leg 1900 L dark brown patch | ortho_paint_over (dark, 158 px) |
| apron 2963-3025 R start lighter triangle | OPEN: the apron clip / feather do not explain it (the triangle is the apron's own outline corner beyond the clip); needs the outline re-traced |
| zone ends square-cut at 1800 R / 3600 R | OPEN: the paved-zone ribbon has no end feather (its asphalt weight is per column, not per row); a kit change |

### Kerb widths re-measured (painted blocks + contiguous pale concrete)

The capture reader extended outward over pale grey, unsaturated, non-warm pixels contiguous with the band. On the clean
captures there is no wide pale concrete beyond the blocks: at Cotton (1020-1049 R) and the Star Mazda entry (3339-3382 L)
the blocks meet the dirt directly (capture windows at 0.04 m/px, local). Widths unchanged in the package; table:

| run | painted (m) | painted + pale (m) | readings |
|---|---|---|---|
| left 283-322 | 0.52 | 0.64 | 10 |
| left 536-558 | 0.6 | 0.62 | 16 |
| left 745-767 | 1.04 | 1.04 | 24 |
| left 954-1011 | 0.96 | 0.96 | 48 |
| left 1089-1116 | 0.9 | 1.0 | 4 |
| left 1203-1272 | 0.76 | 0.92 | 33 |
| left 1337-1395 | 0.88 | 1.08 | 64 |
| left 1454-1478 | 0.64 | 0.68 | 26 |
| left 1542-1575 | 1.16 | 1.2 | 45 |
| left 1654-1681 | 0.88 | 0.88 | 31 |
| left 1843-1851 | 1.12 | 1.26 | 12 |
| left 2539-2544 | 0.9 | 0.9 | 6 |
| left 2690-2747 | 1.12 | 1.14 | 50 |
| left 2850-2856 | 0.94 | 1.04 | 4 |
| left 3005-3013 | 1.1 | 1.1 | 10 |
| left 3339-3382 | 1.24 | 1.24 | 51 |
| left 3470-3518 | 0.76 | 1.0 | 55 |
| left 3691-3760 | 0.88 | 1.02 | 34 |
| left 3845-3876 | 0.74 | 0.88 | 18 |
| left 3972-4023 | 0.88 | 0.96 | 38 |
| left 4380-4406 | 1.04 | 1.08 | 35 |
| right 188-268 | 1.28 | 1.4 | 117 |
| right 360-376 | 1.08 | 1.2 | 22 |
| right 410-424 | 1.0 | 1.12 | 20 |
| right 584-604 | 0.6 | 0.64 | 19 |
| right 1020-1049 | 1.04 | 1.04 | 18 |
| right 1304-1309 | 0.36 | 0.36 | 3 |
| right 1494-1516 | 0.88 | 0.88 | 25 |
| right 1779-1819 | 1.0 | 1.12 | 65 |
| right 1869-1934 | 0.68 | 0.8 | 92 |
| right 2315-2340 | 1.12 | 1.12 | 18 |
| right 2766-2793 | 0.84 | 0.88 | 21 |
| right 3400-3450 | 1.0 | 1.0 | 60 |
| right 3794-3810 | 1.12 | 1.12 | 18 |
| right 3894-3935 | 0.56 | 0.8 | 28 |
| right 4029-4126 | 0.68 | 0.72 | 81 |
| right 4320-4370 | 1.16 | 1.16 | 72 |
| right 4424-4501 | 1.0 | 1.16 | 151 |

### Crack-seal marks

Contrast 14 -> 9: 884 candidate segments, 407 kept (cap 1200). Per 400 m section from s 0: 29, 31, 34, 33, 47, 21, 34,
15, 46, 50, 34. Visible as thin dark lines from 2 m (r8f_crack_T2_high); at hood height they are faint.

### Kart track

Traced on the paddock capture pad_5 by skeleton: only 106 m resolved (the loop leaves the tile to the north and merges
with the paved lot on the right): not placed; OPEN (needs more capture tiles).

## Round 8 checkpoint 6 (22 Oct 2026, rev 6ebc6e3263): judge r8 rows

Geometry unchanged from 8bf8602. Stage 3 every gate ok. Stills structure_stills/r8g_*_r8.jpg.

| row | outcome |
|---|---|
| Control tower | FIXED: back to the compact tower (the east 14 m of the 25 x 19 m roof outline: solid lower storey 14 x 14 m with doors and windows, set-back glazed upper 11 x 8, deck rail, stair, 17 x 16 m roof); the west 11 m an open shade roof on posts; the awning (OSM 765811056) behind (r8g_tower_close / _from_lane) |
| Station surrounds | FIXED for 826 R (t034), 1185 R (t046), 2370 R (t082), 3433 R (t112), 3716 R (t122): pale tyre ring 0.8 m, 3.5 m radius, each with the capture's dark tyre ring. 2776 R (t092 does not show it) and 3202 R: none placed |
| Apron tone | FIXED (kit): the apron shader varies (+-9 % patches at 6 m and 1.5 m) and darkens to 0.72 over the 3 m next to the road edge; the T2 runoff shares the shader but has no road-edge segments (no worn band) |
| Square-cut zone ends 1800 R / 3600 R | FIXED (kit + builder `zone_end_feather`): 38 zone ends on the dirt fade their asphalt over 4 rows |
| Apron 2963-3025 R corner, 2550 R seam, 2800 L triangle, 4300 L wedge, 590 R strip | OPEN (not reworked this checkpoint; stills r8g_seam_*) |
| Pit wall | the nose's first 12.2 m (two K-rail segments) beige, unpainted, as t1240000 shows; the nose position and the pit-in-facing end: OPEN |
| Pit-lane cones | the tower-foot cone fluorescent yellow-green (#c6e21e, t1312000) |
| Lattice mast | thinner members (0.12 / 0.045 m) and a lighter grey |
| T1 cones on the pavement, T2 apex run width / colours, the dark K-rail section's visibility, the K-rail's T1 end, the 4100 R kerb end, mouth-cone visibility | OPEN (not reached) |

### Generated tables (manifest_tables.ts on the published package, rev b7a674a6da)

### Scenery objects of the checked kinds (136, from public/tracks/buttonwillow/)

| # | kind | side | s (m) | out (m) | object | source |
|---|---|---|---|---|---|---|
| 1 | wall | left | 4514-206 (wraps) | 2-4 | barrier 0 (concrete) | declared: pit wall, front straight (wall_measure.py --edge left 4490-4693 (88 % picked, offset p50 3.56 m) and 0-300 (75 %, p50 3.74 m) on c20_s4550..c20_s0300; onboard t000-t008, t148-t158 (white K-rail with red panels); pit-lane video 20:40-22:28 (on the right of the lane)) |
| 2 | wall | left | 4526-4656 | 20-21 | barrier 1 (concrete) | declared: pit lane, paddock side, west (wall_measure.py --edge left 4490-4693 --off 12,30 (68 % picked, 20.8 m beyond the left edge) on c20_s4600 / c20_p0360; pit-lane video 20:49-21:52 (Jersey wall on the left of the lane)) |
| 3 | wall | left | 4668-40 (wraps) | 21-22 | barrier 2 (concrete) | declared: pit lane, paddock side, tower (wall_measure.py --edge left (175-210 m and 0-42 m runs, 21 m beyond the left edge) on c20_p0420 / c20_p0480; pit-lane video 21:52 (the wall at the tower, a yellow cone at its foot)) |
| 4 | wall | left | 54-174 | 21-21 | barrier 3 (concrete) | declared: pit lane, paddock side, east (wall_measure.py --edge left 0-300 --off 12,30 (54-196 m run, 21 m beyond the left edge) on c20_p0540 / c20_p0600) |
| 5 | tyre_wall | right | 472-489 | 9-14 | barrier 4 (tyres) | declared: T1-exit station mound tyres (onboard t020 (0:20); c20_s0600 / c20_s0650 (the tyre ring round the station roof); position: 0.8 m beyond the fitted right edge at s 474-488, the mound face) |
| 6 | tyre_wall | right | 1014-1026 | 7-14 | barrier 5 (tyres) | declared: T3 station mound tyres (c20_s1100 / c20_s1150: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t040 (0:40) (inventory station row s 996 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 7 | tyre_wall | right | 1496-1507 | 8-15 | barrier 6 (tyres) | declared: T5 station mound tyres (c20_s1600: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t058 (0:58) (inventory station row s 1525 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 8 | tyre_wall | right | 2077-2084 | 7-14 | barrier 7 (tyres) | declared: T6 (Riverside) station mound tyres (c20_s2150: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t074 (1:14) (inventory station row s 2054 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 9 | tyre_wall | left | 4284-4291 | 6-13 | barrier 8 (tyres) | declared: T11 approach (Sunset) station mound tyres (c20_s4400: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t138 (2:18) (inventory station row s 4273 left: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 10 | fence | left | 4303-4451 | 34-56 | barrier 9 (fence + 1.5 m fence) | declared: pit entry paddock fence (pit-lane video t1231000 (20:31): the mesh fence along the paddock boundary under the trees left of the pit entry; the line on the tree line lane-side edge, c20_s4400 / c20_p0180) |
| 11 | tyre_wall | left | 4166-4271 | 27-31 | barrier 10 (tyres) | declared: T11 approach tree-line tyre barrier (c20_s4300 (stage3_evidence/tyre4200.png): a long dark tyre line under the trees ~27 m beyond the left edge at s ~4150-4260; judge r3 back_07 (looking back at 4200); onboard t136-t138 (dark line under the trees, left)) |
| 12 | kerb | left | 283-322 | 0-0 | kerb 283.3-322.4 | run left s 283-322: kerb run (owner lap 1): the block line followed on c20_s0400 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t014.jpg (red / white / blue; inventory row s 300 left) |
| 13 | kerb | left | 536-558 | 0-0 | kerb 535.6-557.6 | run left s 536-549: kerb run (owner lap 1): the block line followed on c20_s0650 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; extended to s ~558 (judge r5 fwd_01 550 L): c20_s0650 shows the block line continuing ~9 m past the end of the band reader, at the last offset of the run; colour: t022.jpg (red / white / blue; inventory row s 531 left) |
| 14 | kerb | left | 745-767 | 0-0 | kerb 744.8-766.9 | run left s 745-767: kerb run (owner lap 1): the block line followed on c20_s0900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t032.jpg (white / red; inventory row s 738 left) |
| 15 | kerb | left | 954-1011 | 0-0 | kerb 954.1-1011.1 | run left s 954-1011: kerb run (owner lap 1): the block line followed on c20_s1100 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t040.jpg (red / white / blue; inventory row s 996 left) |
| 16 | kerb | left | 1089-1116 | 0-0 | kerb 1089.2-1116.3 | run left s 1089-1116: kerb run (owner lap 1): the round-4 strip extent on c20_s1250; the band reader found no line on the new edge: band centre 0.45 m inside the edge; colour: t044.jpg (red / white / blue; inventory row s 1088 left) |
| 17 | kerb | left | 1203-1272 | 0-0 | kerb 1203.4-1272.4 | run left s 1203-1272: kerb run (owner lap 1): the block line followed on c20_s1350 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 18 | kerb | left | 1338-1396 | 0-0 | kerb 1337.5-1395.6 | run left s 1338-1396: kerb run (owner lap 1): the block line followed on c20_s1500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t054.jpg (red / white / blue; inventory row s 1344 left) |
| 19 | kerb | left | 1449-1479 | 0-0 | kerb 1448.6-1478.7 | run left s 1449-1479: kerb run (owner lap 1): the block line followed on c20_s1600 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1449-1479 |
| 20 | kerb | left | 1541-1574 | 0-0 | kerb 1540.7-1573.8 | run left s 1541-1574: kerb run (owner lap 1): the block line followed on c20_s1700 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1541-1574 |
| 21 | kerb | left | 1653-1680 | 0-0 | kerb 1652.9-1679.9 | run left s 1653-1680: kerb run (owner lap 1): the block line followed on c20_s1800 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 22 | kerb | left | 1843-1851 | 0-0 | kerb 1843.1-1851.1 | run left s 1843-1851: kerb run (owner lap 1): the block line followed on c20_s1950 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t068.jpg (red / white / blue; inventory row s 1839 left) |
| 23 | kerb | left | 2539-2544 | 0-0 | kerb 2538.9-2543.9 | run left s 2539-2544: kerb run (owner lap 1): the block line followed on c20_s2650 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2539-2544 |
| 24 | kerb | left | 2689-2746 | 0-0 | kerb 2689-2746.1 | run left s 2689-2746: kerb run (owner lap 1): the block line followed on c20_s2850 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 25 | kerb | left | 2849-2855 | 0-0 | kerb 2849.2-2855.2 | run left s 2849-2855: kerb run (owner lap 1): the block line followed on c20_s2950 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2849-2855 |
| 26 | kerb | left | 3005-3013 | 0-0 | kerb 3005.4-3013.4 | run left s 3005-3013: kerb run (owner lap 1): the block line followed on c20_s3150 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: colour unverified: no inventory kerb row on that side within 40 m of s 3005-3013 |
| 27 | kerb | left | 3340-3383 | 0-0 | kerb 3339.8-3382.8 | run left s 3340-3383: kerb run (owner lap 1): the block line followed on c20_s3500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 28 | kerb | left | 3470-3518 | 0-0 | kerb 3469.9-3518 | run left s 3470-3518: kerb run (owner lap 1): the block line followed on c20_s3600 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t116.jpg (red / white / blue; inventory row s 3479 left) |
| 29 | kerb | left | 3691-3760 | 0-0 | kerb 3691.2-3760.3 | run left s 3691-3760: kerb run (owner lap 1): the block line followed on c20_s3850 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t124.jpg (red / white / blue; inventory row s 3725 left) |
| 30 | kerb | left | 3845-3876 | 0-0 | kerb 3845.3-3876.4 | run left s 3845-3876: kerb run (owner lap 1): the block line followed on c20_s3950 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t128.jpg (red / white / blue; inventory row s 3848 left) |
| 31 | kerb | left | 3973-4024 | 0-0 | kerb 3972.5-4023.5 | run left s 3972-4024: kerb run (owner lap 1): the block line followed on c20_s4100 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t132.jpg (red / white / blue; inventory row s 3981 left) |
| 32 | kerb | left | 4381-4406 | 0-0 | kerb 4381-4406 | run left s 4381-4406: kerb run (owner lap 1): the block line followed on c20_s4500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t142.jpg (red / white / blue; inventory row s 4371 left) |
| 33 | kerb | right | 188-268 | 0-0 | kerb 188.2-268.3 | run right s 188-268: kerb run (owner lap 1): the block line followed on c20_s0350 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t012.jpg (red / white / blue; inventory row s 256 right) |
| 34 | kerb | right | 360-376 | 0-0 | kerb 360.4-376.4 | run right s 360-376: kerb run (owner lap 1): the block line followed on c20_s0500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t018.jpg (red / white / blue; inventory row s 408 right) |
| 35 | kerb | right | 411-425 | 0-0 | kerb 410.5-424.5 | run right s 410-424: kerb run (owner lap 1): the block line followed on c20_s0550 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t018.jpg (red / white / blue; inventory row s 408 right) |
| 36 | kerb | right | 584-604 | 0-0 | kerb 583.7-603.7 | run right s 584-604: kerb run (owner lap 1): the block line followed on c20_s0700 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t025.jpg (red / white / blue; inventory row s 590 right) |
| 37 | kerb | right | 1020-1049 | 0-0 | kerb 1020.2-1049.2 | run right s 1020-1049: kerb run (owner lap 1): the block line followed on c20_s1150 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1020-1049 |
| 38 | kerb | right | 1168-1191 | 0-0 | kerb 1168.3-1191.3 | run right s 1168-1191: kerb run (owner lap 1): the round-4 strip extent on c20_s1300; the band reader found no line on the new edge: band centre 0.45 m inside the edge; colour: t048.jpg (red / white; inventory row s 1175 right) |
| 39 | kerb | right | 1305-1310 | 0-0 | kerb 1304.5-1309.5 | run right s 1304-1309: kerb run (owner lap 1): the block line followed on c20_s1450 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t052.jpg (red / white / blue; inventory row s 1304 right) |
| 40 | kerb | right | 1495-1515 | 0-0 | kerb 1494.7-1514.7 | run right s 1495-1515: kerb run (owner lap 1): the block line followed on c20_s1650 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t058.jpg (red / white / blue; inventory row s 1492 right) |
| 41 | kerb | right | 1779-1818 | 0-0 | kerb 1779-1818.1 | run right s 1779-1818: kerb run (owner lap 1): the block line followed on c20_s1900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t066.jpg (white / red / blue; inventory row s 1773 right) |
| 42 | kerb | right | 1868-1933 | 0-0 | kerb 1868.1-1933.2 | run right s 1868-1933: kerb run (owner lap 1): the block line followed on c20_s2000 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t070.jpg (red / white / blue; inventory row s 1878 right) |
| 43 | kerb | right | 2315-2340 | 0-0 | kerb 2314.6-2339.6 | run right s 2315-2340: kerb run (owner lap 1): the block line followed on c20_s2450 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t082.jpg (red / white / blue; inventory row s 2313 right) |
| 44 | kerb | right | 2765-2792 | 0-0 | kerb 2765.1-2792.2 | run right s 2765-2792: kerb run (owner lap 1): the block line followed on c20_s2900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t094.jpg (red / white / blue; inventory row s 2760 right) |
| 45 | kerb | right | 3400-3451 | 0-0 | kerb 3399.8-3450.9 | run right s 3400-3451: kerb run (owner lap 1): the block line followed on c20_s3550 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; raised: onboard t114 (1:52) shows the T9 apex kerb's sloped track-side face 10-15 px tall at base row ~555 (horizon row ~265), camera 1.49 m from the CRX ahead in t116 (roof 1.29 m, 76 px at base row 363): horizon ratio 0.05-0.08 m, 0.06 m used (compare/HEIGHTS.md); the exit kerb (t116, 3463-3512 L) shows a face of 1-2 px (<= 0.02 m): flat; colour: t114.jpg (red / white / blue; inventory row s 3445 right) |
| 46 | kerb | right | 3794-3810 | 0-0 | kerb 3794.3-3810.3 | run right s 3794-3810: kerb run (owner lap 1): the block line followed on c20_s3900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t126.jpg (red / white / blue; inventory row s 3787 right) |
| 47 | kerb | right | 3894-3935 | 0-0 | kerb 3894.4-3935.4 | run right s 3894-3935: kerb run (owner lap 1): the block line followed on c20_s4050 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 48 | kerb | right | 4030-4127 | 0-0 | kerb 4029.6-4126.7 | run right s 4030-4127: kerb run (owner lap 1): the block line followed on c20_s4200 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t136.jpg (white / blue; inventory row s 4122 right) |
| 49 | kerb | right | 4321-4370 | 0-0 | kerb 4320.9-4369.9 | run right s 4321-4370: kerb run (owner lap 1): the block line followed on c20_s4450 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 50 | kerb | right | 4424-4501 | 0-0 | kerb 4424-4501.1 | run right s 4424-4501: kerb run (owner lap 1): the block line followed on c20_p0240 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; colour: t144.jpg (white / blue / red; inventory row s 4410 right) |
| 51 | station | right | 480-480 | 10-10 | marshal 'T1 exit' | c20_s0650: white roof 5.5 m2 in a dark tyre ring (compare/blob_scan.py, 0.4 m beyond the right edge at s 482); onboard t020 (0:20): canopy on posts on a tyre-faced mound close right; inventory s 477 right |
| 52 | station | right | 825-825 | 7-7 | marshal 'T2 to T3, east side' | c20_s0600: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 7.1 m beyond the right edge at s 820); onboard t034 (0:34): blue canopy on a tyre-faced mound ahead right; inventory s 834 right |
| 53 | station | right | 1019-1019 | 11-11 | marshal 'T3' | c20_s1150: white roof 5.6 m2 in a dark tyre ring (compare/blob_scan.py, 9.2 m beyond the right edge at s 1014); onboard t040 (0:40): blue canopy on posts on a tyre-faced mound close right; inventory s 996 right |
| 54 | station | right | 1185-1185 | 12-12 | marshal 'T4' | c20_s1300: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.6 m beyond the right edge at s 1173); onboard t046 (0:46): canopy on posts ahead right; inventory s 1186 right |
| 55 | station | right | 1501-1501 | 12-12 | marshal 'T5' | c20_s1550: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.8 m beyond the right edge at s 1492); onboard t058 (0:58): canopy on a tyre-faced mound right; inventory s 1524 right |
| 56 | station | right | 2080-2080 | 10-10 | marshal 'T6 (Riverside)' | c20_s2150: white roof 6.3 m2 in a dark tyre ring (compare/blob_scan.py, 10.4 m beyond the right edge at s 2069); onboard t074 (1:14): canopy on a tyre-faced mound ahead right; inventory s 2050 right |
| 57 | station | right | 2369-2369 | 19-19 | marshal 'T7' | c20_s2500: white roof 5.9 m2 in a dark tyre ring (compare/blob_scan.py, 19.2 m beyond the right edge at s 2358); onboard t082 (1:22): canopy on a mound ahead right; inventory s 2372 right |
| 58 | station | right | 2776-2776 | 10-10 | marshal 'T8' | c20_s2900: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 9.8 m beyond the right edge at s 2764); onboard t092 (1:32): canopy on posts ahead right; inventory s 2776 right |
| 59 | station | right | 3202-3202 | 11-11 | marshal 'north leg before T9' | c20_s3300: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 11.0 m beyond the right edge at s 3189); onboard not in the 2 s frames (t106-t108 look past it); roof and tyre ring on c20_s3300 / c20_s3350 |
| 60 | station | right | 3433-3433 | 14-14 | marshal 'T9 (Star Mazda)' | c20_s3500: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 13.6 m beyond the right edge at s 3420); onboard t112 (1:52): roofed platform on stilts ahead right; inventory s 3436 right |
| 61 | station | right | 3716-3716 | 7-7 | marshal 'T10' | c20_s3800: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 15.4 m beyond the right edge at s 3698); onboard t122 (2:02): station far ahead right; inventory s 3758 right |
| 62 | station | left | 4287-4287 | 9-9 | marshal 'T11 approach (Sunset)' | c20_s4350: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 5.0 m beyond the left edge at s 4272); onboard t138 (2:18): canopy on a tyre-faced mound ahead left; inventory s 4274 left |
| 63 | station | left | 4516-4516 | 2-2 | marshal 'pit-in station' | pit-lane video ucmXJu5QKFQ 20:40 (t1240000): a canopy on one pole over a small white 'CAC CLUB' cabinet on a pale base at the pit-wall head (judge r3 pit_00, the entry shelter); c20_s4550 / c20_s4600: the white roof at the wall head (compare/blob_scan.py, s 4511 left 8.5 m); pit row s 4320 corrected to 4508 |
| 64 | station | left | 246-246 | 42-42 | marshal 'T1 inside canopy' | c20_s0300 / c20_s0350: a white roof ~5 x 3 m among the trees inside T1, 42 m beyond the left edge at s 247 (compare/blob_scan.py; stage3_evidence/blob247.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60; judge r1 row) |
| 65 | station | left | 199-199 | 5-5 | marshal 'pit-wall end hut' | c20_s0300 / c20_s0350: white roof 7.8 m2 at the east end of the pit wall (compare/blob_scan.py, 5.2 m beyond the left edge at s 199; window stage3_evidence/cw_wallend.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60) |
| 66 | station | left | 2-2 | 3-3 | marshal 'starter's stand' | c20_s0050 / c20_s0100 / c20_s0150: the white structure on the pit wall at the timing line (blob_scan s 2, 3.4 m beyond the left edge); pit-lane video ucmXJu5QKFQ 22:19-22:28: the scaffold starter's stand with a canopy on the pit wall |
| 67 | tyre_stack | left | 610-610 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 68 | tyre_stack | left | 611-611 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 69 | tyre_stack | left | 612-612 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 70 | tyre_stack | left | 613-613 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 71 | tyre_stack | left | 614-614 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 72 | tyre_stack | left | 616-616 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 73 | tyre_stack | left | 616-616 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 74 | tyre_stack | left | 618-618 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 75 | tyre_stack | left | 619-619 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 76 | tyre_stack | left | 620-620 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 77 | tyre_stack | left | 621-621 | 12-12 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 78 | tyre_stack | left | 622-622 | 13-13 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 79 | tyre_stack | left | 623-623 | 13-13 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 80 | tyre_stack | left | 624-624 | 13-13 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 81 | tyre_stack | left | 625-625 | 14-14 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 82 | tyre_stack | left | 627-627 | 14-14 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 83 | tyre_stack | left | 628-628 | 15-15 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 84 | tyre_stack | left | 629-629 | 15-15 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 85 | tyre_stack | left | 630-630 | 16-16 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 86 | tyre_stack | left | 631-631 | 17-17 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 87 | tyre_stack | left | 632-632 | 17-17 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 88 | tyre_stack | left | 634-634 | 18-18 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 89 | tyre_stack | left | 635-635 | 19-19 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 90 | tyre_stack | left | 636-636 | 19-19 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 91 | tyre_stack | left | 637-637 | 20-20 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 92 | tyre_stack | left | 638-638 | 21-21 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 93 | tyre_stack | left | 639-639 | 22-22 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 94 | tyre_stack | left | 641-641 | 23-23 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 95 | tyre_stack | left | 642-642 | 24-24 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 96 | tyre_stack | left | 643-643 | 25-25 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 97 | tyre_stack | left | 644-644 | 26-26 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 98 | tyre_stack | left | 645-645 | 26-26 | block '' | the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb |
| 99 | mast | left | 3448-3448 | 161-161 | mast '' | OSM man_made=mast / communications tower node 10220517717; the lidar (CA_SanJoaquin_2021) has an isolated spike 49.5-49.7 m over the DEM there (30 cells, compare/stage3 lidar spike scan); onboard t106 (1:46): a tall thin pole far ahead on the north leg (inventory mast row s 3400 ahead, ahead_m 250) |
| 100 | building | left | 4694-13 (wraps) | 46-63 | building 0 '' 4.3 m | osm (pit-lane video ucmXJu5QKFQ 21:52-22:10 (t1312000, t1330000): the two-storey timing tower with the blue roof beside the pit lane; OSM footprint, lidar height) |
| 101 | building | left | 0-14 | 23-37 | structure 0 block 'timing tower' | pit-lane video t1312000 / t1339000 (judge r5): solid tan lower storey with a door and a few windows, the deck on its roof with a railing, the exterior stair at the west end; footprint on c20_p0420 / c20_s0050 |
| 102 | building | left | 2-13 | 29-37 | structure 1 block 'timing tower upper storey' | pit-lane video t1312000 / t1339000: the upper storey set back behind the deck, windows between dark posts on the lane side and the ends (glazed upper storey only) |
| 103 | building | left | 0-7 | 30-31 | structure 2 fuel 'timing tower roof' | pit-lane video t1312000 / t1339000: the deep blue roof on posts over the tower, ~1.5 m overhang past its walls (the 14 m tower, not the 25 m outline) |
| 104 | building | left | 4612-4625 | 92-96 | structure 3 fuel 'paddock shade roof' | pit-lane video t1267000 / t1303000: the long low dark shade roof on posts behind the paddock-side K-rail west of the tower; footprint and height from the lidar (2021) structure there, 29 x 8 m, 3.7 m |
| 105 | building | left | 4694-4699 | 23-32 | structure 4 fuel 'timing tower west annex' | the west 11 m of the 25 x 19 m roof outline on c20_p0420 / c20_s0050: the low flat shade roof on posts west of the tower (pit video t1312000, the dark shade roof at the frame edge); plain, low, open |
| 106 | building | left | 0-14 | 37-42 | structure 5 block 'timing tower rear annex' | the north 5 m strip of the roof outline behind the tower (c20_p0420): plain, low |
| 107 | cone_line | right | 179-182 | 0-4 | cone line 0 | closed road Atlantic (OSM 34351042) mouth (judge r3 runoff_01 (s 170 R): a clear row of cones closing the paved branch; onboard t010-t012) |
| 108 | cone_line | right | 1827-1830 | 0-3 | cone line 1 | closed road crossover (OSM 34351015) mouth (onboard t068 (judge r2 runoff_02, s 1824 R): cones across the crossover mouth) |
| 109 | cone_line | right | 40-54 | 1-1 | cone line 2 | judge r3 runoff (s 46 R): cones across the front-straight crossover (OSM 34351026) mouth on the right; onboard t006 (the two cones at the mouth, inventory s 20-24 R) |
| 110 | cone_line | right | 1914-1915 | 1-2 | cone line 3 | compare_sheets onboard s1900 (t 70.76): an orange cone beside the end of the right kerb (judge r3 1920 R) |
| 111 | cone_line | right | 3199-3200 | 1-2 | cone line 4 | compare_sheets onboard s3200 (t 107.15): an orange cone at the right edge (judge r3 fwd_10 3200 R) |
| 112 | cone_line | right | 140-160 | 2-2 | cone line 5 | onboard t006-t008 (judge r2, fwd_00): several orange cones on the paved shoulder right |
| 113 | cone_line | left | 895-905 | 1-2 | cone line 6 | onboard t036 (judge r2, fwd_02 / fwd_03): orange cones on the left |
| 114 | cone_line | right | 1780-1830 | 3-3 | cone line 7 | onboard t066-t068 (judge r2, fwd_06): a long line of cones separating the adjacent pavement (the Dog Leg / crossover mouth) on the right |
| 115 | cone_line | left | 3250-3300 | 1-2 | cone line 8 | onboard t108-t110 (judge r2, fwd_10 / fwd_11): orange cones along the left |
| 116 | cone_line | right | 3645-3655 | 1-2 | cone line 9 | onboard t122 (judge r2, fwd_12): orange cones on the right |
| 117 | cone_line | left | 4612-4662 | 20-21 | cone line 10 | pit-lane video t1267000 (21:07): six small orange cones along the left (paddock-side) wall ahead of the tower, at the wall foot (0.4 m off it, at the edge of the lane paving, which now stops 0.3 m short of the wall; the pit-connectivity gate keeps the lane itself clear), ~10 m apart (judge r5 pit_01 / pit_02) |
| 118 | cone_line | left | 4694-4695 | 21-21 | cone line 11 | pit-lane video t1312000 / t1339000: the yellow cone at the tower foot, 0.4 m off the paddock-side wall |
| 119 | cone_line | left | 4698-4699 | 21-21 | cone line 12 | pit-lane video t1312000 / t1339000: the orange cone beside it at the tower foot |
| 120 | cone_line | left | 752-772 | 3-3 | cone line 13 | onboard t030 / compare_sheets s0700, s0750 (fwd_02, side_02): a line of small orange cones on the pale apron left of the T2 approach (inventory cone_line row s 770 left, ahead_m 80); the "3-4 cones" of s0700 are this line seen from 60 m back |
| 121 | cone_line | left | 3198-3202 | 2-2 | cone line 14 | compare_sheets s3200 (fwd_10): orange cones at a mouth on the left; judge r5 fwd_10 3200 L: onboard t108 shows two (was three) |
| 122 | cone_line | right | 4046-4054 | 3-3 | cone line 15 | compare_sheets s4050 (fwd_13): cones on the right apron, 20 m before the t134 cone at s 4071 |
| 123 | cone_line | right | 20-21 | 1-1 | cone line 16 | onboard t006.jpg (yellow, orange; inventory s 20 right: two cones, yellow and orange); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 124 | cone_line | right | 24-25 | 2-2 | cone line 17 | onboard t006.jpg (yellow, orange; inventory s 20 right: two cones, yellow and orange); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 125 | cone_line | right | 297-298 | 2-2 | cone line 18 | onboard t012.jpg (orange; inventory s 297 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 126 | cone_line | left | 533-534 | 2-2 | cone line 19 | onboard t022.jpg (orange; inventory s 533 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 127 | cone_line | left | 834-835 | 2-2 | cone line 20 | onboard t034.jpg (orange; inventory s 834 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 128 | cone_line | left | 973-974 | 1-2 | cone line 21 | onboard t038.jpg (orange; inventory s 973 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 129 | cone_line | right | 1040-1041 | 1-1 | cone line 22 | onboard t042.jpg (orange; inventory s 1040 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 130 | cone_line | right | 1307-1308 | 1-2 | cone line 23 | onboard t052.jpg (orange; inventory s 1307 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 131 | cone_line | right | 2158-2159 | 1-1 | cone line 24 | onboard t078.jpg (orange; inventory s 2158 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 132 | cone_line | left | 2696-2700 | 1-2 | cone line 25 | onboard t092.jpg (orange; inventory s 2696 left: two orange cones); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 133 | cone_line | right | 3439-3440 | 1-1 | cone line 26 | onboard t114.jpg (orange; inventory s 3439 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 134 | cone_line | right | 4071-4072 | 1-2 | cone line 27 | onboard t134.jpg (orange; inventory s 4071 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 135 | cone_line | right | 4575-4576 | 1-1 | cone line 28 | onboard t002.jpg (orange; inventory s 4575 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 136 | cone_line | right | 4593-4594 | 1-1 | cone line 29 | onboard t150.jpg (orange; inventory s 4593 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |

### Every inventory row and its outcome (108 rows)

| s (m) | t | side | kind | what | source | outcome |
|---|---|---|---|---|---|---|
| 21 | 0:06.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@6.0 | covered by barrier 0 (concrete); barrier 2 (concrete) |
| 21 | 0:06.0 | right | cone_line | two cones, yellow and orange | onboard:7QS2M-HGSI4@6.0 | covered by cone line 16; cone line 17 |
| 46 | 0:06.0 | right | cone_line | cones across the crossover mouth | onboard:7QS2M-HGSI4@6.0 | covered by cone line 2 (corrected in round 4, 20 Oct 2026 (judge r3): ) (row added in true) |
| 104 | 0:08.0 | left | wall | concrete K-rail, a dark (black) section at its east end | onboard:7QS2M-HGSI4@8.0 | covered by barrier 0 (concrete); barrier 3 (concrete) |
| 146 | 0:09.0 | right | cone_line | several orange cones on the paved shoulder | onboard:7QS2M-HGSI4@9.0 | covered by cone line 5 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 186 | 0:10.0 | right | cone_line | a row of cones closing the paved branch (Atlantic) | onboard:7QS2M-HGSI4@10.0 | covered by cone line 0 (corrected in round 4, 20 Oct 2026 (judge r3): ) (row added in true) |
| 216 | 0:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@10.0 | covered by kerb 188.2-268.3 |
| 246 | 0:10.0 | left | station | canopy on posts over a low concrete platform | onboard:7QS2M-HGSI4@10.0 | covered by marshal 'T1 inside canopy' |
| 256 | 0:12.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@12.0 | covered by kerb 188.2-268.3 |
| 296 | 0:12.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@12.0 | covered by cone line 18 |
| 300 | 0:14.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@14.0 | covered by kerb 283.3-322.4 |
| 408 | 0:18.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@18.0 | covered by kerb 410.5-424.5 |
| 477 | 0:20.0 | right | station | corner station: canopy on posts on a tyre-walled earth mound | onboard:7QS2M-HGSI4@20.0 | covered by marshal 'T1 exit' |
| 477 | 0:20.0 | right | tyre_wall | tyres around the station mound | onboard:7QS2M-HGSI4@20.0 | covered by barrier 4 (tyres) |
| 531 | 0:22.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@22.0 | covered by cone line 19 |
| 531 | 0:22.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@22.0 | covered by kerb 535.6-557.6 |
| 574 | 0:24.0 | right | runoff | pale paved / concrete patch inside the hairpin | onboard:7QS2M-HGSI4@24.0 | surroundings (not a checked kind) |
| 590 | 0:25.0 | right | kerb | block line on the inside of the T2 hairpin apex | onboard:7QS2M-HGSI4@25.0 | covered by kerb 583.7-603.7 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 738 | 0:32.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@32.0 | covered by kerb 744.8-766.9 |
| 770 | 0:30.0 | left | cone_line | line of small cones | onboard:7QS2M-HGSI4@30.0 | covered by cone line 13 |
| 833 | 0:34.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@34.0 | covered by cone line 20 |
| 833 | 0:34.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@34.0 | covered by marshal 'T2 to T3, east side' |
| 893 | 0:37.0 | left | cone_line | orange cones on the left | onboard:7QS2M-HGSI4@37.0 | covered by cone line 6 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 972 | 0:38.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@38.0 | covered by cone line 21 |
| 972 | 0:38.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@38.0 | covered by kerb 954.1-1011.1 |
| 996 | 0:40.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@40.0 | covered by kerb 954.1-1011.1 |
| 996 | 0:40.0 | right | station | corner station: blue canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@40.0 | MISSING, placed: T3 (s 1013 right, 17 m: time-map error) |
| 1041 | 0:42.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@42.0 | covered by cone line 22 |
| 1088 | 0:44.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@44.0 | covered by kerb 1089.2-1116.3 |
| 1175 | 0:48.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@48.0 | covered by kerb 1168.3-1191.3 |
| 1190 | 0:46.0 | right | station | corner station: canopy on posts | onboard:7QS2M-HGSI4@46.0 | covered by marshal 'T4' |
| 1224 | 0:50.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@50.0 | covered by kerb 1203.4-1272.4 |
| 1304 | 0:52.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@52.0 | covered by kerb 1304.5-1309.5 |
| 1309 | 0:52.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@52.0 | covered by cone line 23 |
| 1344 | 0:54.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@54.0 | covered by kerb 1337.5-1395.6 |
| 1476 | 0:56.0 | left | paint | white painted blocks at the left edge | onboard:7QS2M-HGSI4@56.0 | surroundings (not a checked kind) |
| 1492 | 0:58.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@58.0 | covered by kerb 1494.7-1514.7 |
| 1522 | 0:58.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@58.0 | MISSING, placed: T5 (s 1492 right, 29 m: the frame's look-ahead and the time map) |
| 1645 | 1:00.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@60.0 | covered by kerb 1652.9-1679.9 (corrected in first-centre round, 20 Oct 2026 (judge r1): ahead_m was 30) |
| 1645 | 1:02.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@62.0 | covered by kerb 1652.9-1679.9 |
| 1773 | 1:06.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@66.0 | covered by kerb 1779-1818.1 (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 1793 | 1:07.0 | right | cone_line | a long line of cones separating the adjacent pavement | onboard:7QS2M-HGSI4@67.0 | covered by cone line 7 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 1824 | 1:08.0 | right | cone_line | cones across the crossover mouth | onboard:7QS2M-HGSI4@68.0 | covered by cone line 1; cone line 7 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 1839 | 1:08.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@68.0 | covered by kerb 1843.1-1851.1 (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 1878 | 1:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@70.0 | covered by kerb 1868.1-1933.2 |
| 1924 | 1:11.0 | right | cone_line | single orange cone at the kerb's end | onboard:7QS2M-HGSI4@71.0 | covered by cone line 3 (corrected in round 4, 20 Oct 2026 (judge r3): ) (row added in true) |
| 2022 | 1:12.0 | left | paint | white painted chevrons / blocks at the left edge | onboard:7QS2M-HGSI4@72.0 | surroundings (not a checked kind) |
| 2053 | 1:14.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@74.0 | MISSING, placed: T6 (Riverside) (s 2069 right, 17 m: time-map error) |
| 2158 | 1:18.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@78.0 | covered by cone line 24 |
| 2313 | 1:22.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@82.0 | covered by kerb 2314.6-2339.6 |
| 2373 | 1:22.0 | right | station | corner station: canopy on a mound | onboard:7QS2M-HGSI4@82.0 | covered by marshal 'T7' |
| 2697 | 1:32.0 | left | cone_line | two orange cones | onboard:7QS2M-HGSI4@92.0 | covered by cone line 25 |
| 2697 | 1:32.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@92.0 | covered by kerb 2689-2746.1 |
| 2760 | 1:34.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@94.0 | covered by kerb 2765.1-2792.2 |
| 2777 | 1:32.0 | right | station | corner station: canopy on posts | onboard:7QS2M-HGSI4@92.0 | covered by marshal 'T8' |
| 2857 | 1:36.0 | left | paint | white painted blocks at the left edge | onboard:7QS2M-HGSI4@96.0 | surroundings (not a checked kind) |
| 3196 | 1:47.0 | left | cone_line | three orange cones at a mouth | onboard:7QS2M-HGSI4@107.0 | covered by cone line 14 (corrected in first-centre round, 20 Oct 2026 (judge r1): ) (row added in true) |
| 3196 | 1:47.0 | right | cone_line | single orange cone at the right edge | onboard:7QS2M-HGSI4@107.0 | covered by cone line 4 (corrected in round 4, 20 Oct 2026 (judge r3): ) (row added in true) |
| 3287 | 1:49.0 | left | cone_line | orange cones along the left | onboard:7QS2M-HGSI4@109.0 | covered by cone line 8 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 3329 | 1:50.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@110.0 | covered by kerb 3339.8-3382.8 |
| 3425 | 1:52.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@112.0 | covered by kerb 3399.8-3450.9 |
| 3440 | 1:52.0 | right | station | corner station: roofed platform on stilts | onboard:7QS2M-HGSI4@112.0 | covered by marshal 'T9 (Star Mazda)' |
| 3444 | 1:46.0 | ahead | mast | tall pole (light / camera mast) | onboard:7QS2M-HGSI4@106.0 | MISSING, placed: OSM man_made=mast (the 49.5 m communications tower, s 3439 left, ~400 m off; the pole on t106 is most likely it) (corrected in stage-3 pass, 20 Oct 2026: ahead_m was 250) |
| 3445 | 1:54.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@114.0 | covered by cone line 26 |
| 3445 | 1:54.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@114.0 | covered by kerb 3399.8-3450.9 |
| 3479 | 1:56.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@116.0 | covered by kerb 3469.9-3518 |
| 3645 | 2:02.0 | right | cone_line | orange cones on the right | onboard:7QS2M-HGSI4@122.0 | covered by cone line 9 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 3725 | 2:04.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@124.0 | covered by kerb 3691.2-3760.3 |
| 3765 | 2:02.0 | right | station | corner station | onboard:7QS2M-HGSI4@122.0 | MISSING, placed: T10 (s 3697 right; the 120 m look-ahead was estimated by eye) |
| 3787 | 2:06.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@126.0 | covered by kerb 3794.3-3810.3 |
| 3848 | 2:08.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@128.0 | covered by kerb 3845.3-3876.4 |
| 3914 | 2:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@130.0 | covered by kerb 3894.4-3935.4 |
| 3981 | 2:12.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@132.0 | covered by kerb 3972.5-4023.5 |
| 4045 | 2:14.0 | right | cone_line | cones on the right apron | onboard:7QS2M-HGSI4@134.0 | covered by cone line 15 (corrected in first-centre round, 20 Oct 2026 (judge r1): ) (row added in true) |
| 4065 | 2:14.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@134.0 | covered by kerb 4029.6-4126.7 |
| 4070 | 2:14.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@134.0 | covered by cone line 27 |
| 4122 | 2:16.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@136.0 | covered by kerb 4029.6-4126.7 |
| 4273 | 2:18.0 | left | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@138.0 | covered by marshal 'T11 approach (Sunset)' |
| 4308 | 2:20.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@140.0 | covered by kerb 4320.9-4369.9 |
| 4371 | 2:22.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@142.0 | covered by kerb 4381-4406 |
| 4410 | 2:24.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@144.0 | covered by kerb 4424-4501.1 |
| 4458 | 2:26.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@146.0 | covered by kerb 4424-4501.1 |
| 4502 | 0:00.0 | left | wall | concrete K-rail (Jersey) segments | onboard:7QS2M-HGSI4@0.0 | covered by barrier 0 (concrete) |
| 4502 | 0:00.0 | right | runoff | dirt, flat, open | onboard:7QS2M-HGSI4@0.0 | surroundings (not a checked kind) |
| 4573 | 0:02.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@2.0 | covered by cone line 28 |
| 4593 | 2:30.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@150.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4593 | 2:30.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@150.0 | covered by cone line 29 |
| 4599 | 2:28.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@148.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4643 | 0:04.0 | left | wall | concrete K-rail (Jersey) | onboard:7QS2M-HGSI4@4.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4662 | 2:32.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@152.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4693 | 0:02.0 | left | building | control tower: 2 storeys, blue flat roof on posts over a deck | onboard:7QS2M-HGSI4@2.0 | covered by building 0 '' 4.3 m; structure 0 block 'timing tower' |
| 4695 | 0:04.0 | left | building | control tower | onboard:7QS2M-HGSI4@4.0 | covered by building 0 '' 4.3 m; structure 0 block 'timing tower' (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 4296 |  | right | paint | the lane leaves the track's left edge before T11 (no wall at the split) | onboard:ucmXJu5QKFQ@20:31 | pit lane: not a checked kind for the lap |
| 4497 |  | left | cone_line | small yellow and orange cones | onboard:ucmXJu5QKFQ@20:40 | pit lane: not a checked kind for the lap |
| 4508 |  | right | station | canopy on a pole over a low concrete pad | onboard:ucmXJu5QKFQ@20:31 | pit lane: not a checked kind for the lap (corrected in round 4, 20 Oct 2026 (judge r3): s was 4320) |
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
| 4637 |  | left | cone_line | row of small orange cones along the paddock-side wall | onboard:ucmXJu5QKFQ@21:07 | pit lane: not a checked kind for the lap (row added in judge r5 (round 6): t1267000 shows the row ahead of the tower) |
| 4697 |  | left | cone_line | two cones at the tower foot (yellow, orange) | onboard:ucmXJu5QKFQ@21:52 | pit lane: not a checked kind for the lap (row added in judge r5 (round 6): t1312000 / t1339000) |
| 4618 |  | left | building | long low dark shade roof on posts in the paddock behind the paddock-side K-rail | onboard:ucmXJu5QKFQ@21:07 | pit lane: not a checked kind for the lap (row added in judge r6 (round 7): fwd_00 0 L, t1267000 / t1303000) |
