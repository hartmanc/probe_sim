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

### Generated tables (manifest_tables.ts on the published package, rev e08631e61f)

### Scenery objects of the checked kinds (234, from public/tracks/buttonwillow)

| # | kind | side | s (m) | out (m) | object | source |
|---|---|---|---|---|---|---|
| 1 | wall | left | 4508-206 (wraps) | 2-5 | barrier 0 (concrete) | declared: pit wall, front straight (wall_measure.py --edge left 4490-4693 (88 % picked, offset p50 3.56 m) and 0-300 (75 %, p50 3.74 m) on c20_s4550..c20_s0300; onboard t000-t008, t148-t158 (white K-rail with red panels); pit-lane video 20:40-22:28 (on the right of the lane)) |
| 2 | wall | left | 4519-4650 | 21-22 | barrier 1 (concrete) | declared: pit lane, paddock side, west (wall_measure.py --edge left 4490-4693 --off 12,30 (68 % picked, 20.8 m beyond the left edge) on c20_s4600 / c20_p0360; pit-lane video 20:49-21:52 (Jersey wall on the left of the lane)) |
| 3 | wall | left | 4662-40 (wraps) | 21-22 | barrier 2 (concrete) | declared: pit lane, paddock side, tower (wall_measure.py --edge left (175-210 m and 0-42 m runs, 21 m beyond the left edge) on c20_p0420 / c20_p0480; pit-lane video 21:52 (the wall at the tower, a yellow cone at its foot)) |
| 4 | wall | left | 54-174 | 20-21 | barrier 3 (concrete) | declared: pit lane, paddock side, east (wall_measure.py --edge left 0-300 --off 12,30 (54-196 m run, 21 m beyond the left edge) on c20_p0540 / c20_p0600) |
| 5 | tyre_wall | right | 472-488 | 6-11 | barrier 4 (tyres) | declared: T1-exit station mound tyres (onboard t020 (0:20); c20_s0600 / c20_s0650 (the tyre ring round the station roof); position: 0.8 m beyond the fitted right edge at s 474-488, the mound face) |
| 6 | tyre_wall | right | 1011-1022 | 7-14 | barrier 5 (tyres) | declared: T3 station mound tyres (c20_s1100 / c20_s1150: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t040 (0:40) (inventory station row s 996 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 7 | tyre_wall | right | 1492-1503 | 8-15 | barrier 6 (tyres) | declared: T5 station mound tyres (c20_s1600: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t058 (0:58) (inventory station row s 1525 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 8 | tyre_wall | right | 2071-2078 | 7-14 | barrier 7 (tyres) | declared: T6 (Riverside) station mound tyres (c20_s2150: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t074 (1:14) (inventory station row s 2054 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 9 | tyre_wall | left | 4278-4285 | 5-12 | barrier 8 (tyres) | declared: T11 approach (Sunset) station mound tyres (c20_s4400: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t138 (2:18) (inventory station row s 4273 left: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)) |
| 10 | kerb | left | 281-290 | 0-0 | kerb 280.8-289.8 | left s 281-290: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 281-322) on c20_s0400; colour: t014.jpg (red / white / blue; inventory row s 300 left) |
| 11 | kerb | left | 291-300 | 0-0 | kerb 290.8-299.8 | left s 291-300: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.2 m (piece of the run s 281-322) on c20_s0400; colour: t014.jpg (red / white / blue; inventory row s 300 left) |
| 12 | kerb | left | 301-310 | 0-0 | kerb 300.8-309.8 | left s 301-310: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.3 m (piece of the run s 281-322) on c20_s0400, c20_s0450; colour: t014.jpg (red / white / blue; inventory row s 300 left) |
| 13 | kerb | left | 311-320 | 0-0 | kerb 310.8-319.9 | left s 311-320: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.4 m (piece of the run s 281-322) on c20_s0450; colour: t014.jpg (red / white / blue; inventory row s 300 left) |
| 14 | kerb | left | 551-556 | 0-0 | kerb 550.5-555.5 | left s 550-555: kerb_detect band reading over -10..+1.5 m, offsets -3.5..-2.6 m (piece of the run s 550-555) on c20_s0700; colour: t022.jpg (red / white / blue; inventory row s 531 left) |
| 15 | kerb | left | 583-590 | 0-0 | kerb 582.6-589.6 | left s 583-590: kerb_detect band reading over -10..+1.5 m, offsets -2.9..-2.5 m (piece of the run s 583-590) on c20_s0700; colour: colour unverified: no inventory kerb row on that side within 40 m of s 583-590 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 16 | kerb | left | 746-752 | 0-0 | kerb 746-752 | left s 746-752: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.3 m (piece of the run s 746-752) on c20_s0850, c20_s0900; colour: t032.jpg (white / red; inventory row s 738 left) |
| 17 | kerb | left | 945-954 | 0-0 | kerb 944.5-953.6 | left s 945-954: kerb_detect band reading over -10..+1.5 m, offsets -1.0..-0.6 m (piece of the run s 945-1007) on c20_s1050, c20_s1100; colour: t038.jpg (white / red; inventory row s 972 left) |
| 18 | kerb | left | 955-964 | 0-0 | kerb 954.6-963.6 | left s 955-964: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 945-1007) on c20_s1100; colour: t038.jpg (white / red; inventory row s 972 left) |
| 19 | kerb | left | 965-974 | 0-0 | kerb 964.6-973.6 | left s 965-974: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 945-1007) on c20_s1100; colour: t038.jpg (white / red; inventory row s 972 left) |
| 20 | kerb | left | 975-984 | 0-0 | kerb 974.6-983.6 | left s 975-984: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 945-1007) on c20_s1100; colour: t038.jpg (white / red; inventory row s 972 left) |
| 21 | kerb | left | 985-994 | 0-0 | kerb 984.6-993.7 | left s 985-994: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.6 m (piece of the run s 945-1007) on c20_s1100; colour: t040.jpg (red / white / blue; inventory row s 996 left) |
| 22 | kerb | left | 995-1004 | 0-0 | kerb 994.7-1003.7 | left s 995-1004: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.7 m (piece of the run s 945-1007) on c20_s1100, c20_s1150; colour: t040.jpg (red / white / blue; inventory row s 996 left) |
| 23 | kerb | left | 1083-1092 | 0-0 | kerb 1082.9-1091.9 | left s 1083-1092: kerb_detect band reading over -10..+1.5 m, offsets -1.0..-0.3 m (piece of the run s 1083-1094) on c20_s1200; colour: t044.jpg (red / white / blue; inventory row s 1088 left) |
| 24 | kerb | left | 1105-1114 | 0-0 | kerb 1105-1114 | left s 1105-1114: kerb_detect band reading over -10..+1.5 m, offsets -0.5..+0.5 m (piece of the run s 1105-1114) on c20_s1250; colour: t044.jpg (red / white / blue; inventory row s 1088 left) |
| 25 | kerb | left | 1199-1208 | 0-0 | kerb 1199.2-1208.2 | left s 1199-1208: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.4 m (piece of the run s 1199-1211) on c20_s1300, c20_s1350; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 26 | kerb | left | 1242-1251 | 0-0 | kerb 1242.3-1251.4 | left s 1242-1251: kerb_detect band reading over -10..+1.5 m, offsets -0.5..+0.0 m (piece of the run s 1242-1266) on c20_s1350, c20_s1400; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 27 | kerb | left | 1252-1261 | 0-0 | kerb 1252.4-1261.4 | left s 1252-1261: kerb_detect band reading over -10..+1.5 m, offsets -1.6..-0.5 m (piece of the run s 1242-1266) on c20_s1400; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 28 | kerb | left | 1262-1266 | 0-0 | kerb 1262.4-1266.4 | left s 1262-1266: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 1242-1266) on c20_s1400; colour: t050.jpg (red / white / blue; inventory row s 1224 left) |
| 29 | kerb | left | 1331-1340 | 0-0 | kerb 1330.6-1339.6 | left s 1331-1340: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 1331-1394) on c20_s1450; colour: t054.jpg (red / white / blue; inventory row s 1344 left) |
| 30 | kerb | left | 1341-1350 | 0-0 | kerb 1340.6-1349.6 | left s 1341-1350: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.3 m (piece of the run s 1331-1394) on c20_s1450, c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1344 left) |
| 31 | kerb | left | 1351-1360 | 0-0 | kerb 1350.6-1359.7 | left s 1351-1360: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.4 m (piece of the run s 1331-1394) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1344 left) |
| 32 | kerb | left | 1361-1370 | 0-0 | kerb 1360.7-1369.7 | left s 1361-1370: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.4 m (piece of the run s 1331-1394) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1344 left) |
| 33 | kerb | left | 1371-1380 | 0-0 | kerb 1370.7-1379.7 | left s 1371-1380: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.4 m (piece of the run s 1331-1394) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1344 left) |
| 34 | kerb | left | 1381-1390 | 0-0 | kerb 1380.7-1389.7 | left s 1381-1390: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.3 m (piece of the run s 1331-1394) on c20_s1500; colour: t054.jpg (red / white / blue; inventory row s 1344 left) |
| 35 | kerb | left | 1391-1394 | 0-0 | kerb 1390.7-1393.7 | left s 1391-1394: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.4 m (piece of the run s 1331-1394) on c20_s1500; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1391-1394 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 36 | kerb | left | 1429-1438 | 0-0 | kerb 1428.8-1437.9 | left s 1429-1438: kerb_detect band reading over -10..+1.5 m, offsets +0.2..+0.6 m (piece of the run s 1429-1478) on c20_s1550; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1429-1438 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 37 | kerb | left | 1439-1448 | 0-0 | kerb 1438.9-1447.9 | left s 1439-1448: kerb_detect band reading over -10..+1.5 m, offsets +0.0..+0.2 m (piece of the run s 1429-1478) on c20_s1550, c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1439-1448 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 38 | kerb | left | 1449-1458 | 0-0 | kerb 1448.9-1457.9 | left s 1449-1458: kerb_detect band reading over -10..+1.5 m, offsets -0.3..+0.0 m (piece of the run s 1429-1478) on c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1449-1458 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 39 | kerb | left | 1459-1468 | 0-0 | kerb 1458.9-1467.9 | left s 1459-1468: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.3 m (piece of the run s 1429-1478) on c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1459-1468 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 40 | kerb | left | 1469-1478 | 0-0 | kerb 1469-1478 | left s 1469-1478: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.6 m (piece of the run s 1429-1478) on c20_s1600; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1469-1478 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 41 | kerb | left | 1533-1542 | 0-0 | kerb 1533.1-1542.1 | left s 1533-1542: kerb_detect band reading over -10..+1.5 m, offsets -0.9..-0.6 m (piece of the run s 1533-1570) on c20_s1650; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1533-1542 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 42 | kerb | left | 1543-1552 | 0-0 | kerb 1543.2-1552.2 | left s 1543-1552: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 1533-1570) on c20_s1650, c20_s1700; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1543-1552 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 43 | kerb | left | 1553-1562 | 0-0 | kerb 1553.2-1562.2 | left s 1553-1562: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 1533-1570) on c20_s1700; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1553-1562 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 44 | kerb | left | 1563-1570 | 0-0 | kerb 1563.2-1570.2 | left s 1563-1570: kerb_detect band reading over -10..+1.5 m, offsets -1.1..-0.5 m (piece of the run s 1533-1570) on c20_s1700; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1563-1570 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 45 | kerb | left | 1640-1649 | 0-0 | kerb 1640.4-1649.4 | left s 1640-1649: kerb_detect band reading over -10..+1.5 m, offsets -0.3..-0.1 m (piece of the run s 1640-1676) on c20_s1750, c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 46 | kerb | left | 1650-1660 | 0-0 | kerb 1650.4-1659.5 | left s 1650-1659: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.4 m (piece of the run s 1640-1676) on c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 47 | kerb | left | 1661-1670 | 0-0 | kerb 1660.5-1669.5 | left s 1660-1669: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 1640-1676) on c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 48 | kerb | left | 1671-1676 | 0-0 | kerb 1670.5-1675.5 | left s 1670-1676: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.6 m (piece of the run s 1640-1676) on c20_s1800; colour: t062.jpg (red / white; inventory row s 1645 left) |
| 49 | kerb | left | 1842-1848 | 0-0 | kerb 1842-1848 | left s 1842-1848: kerb_detect band reading over -10..+1.5 m, offsets -6.9..-6.0 m (piece of the run s 1842-1848) on c20_s1950; colour: t068.jpg (red / white / blue; inventory row s 1839 left) |
| 50 | kerb | left | 1960-1965 | 0-0 | kerb 1960.3-1965.3 | left s 1960-1965: kerb_detect band reading over -10..+1.5 m, offsets -0.9..-0.2 m (piece of the run s 1960-1965) on c20_s2100; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1960-1965 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 51 | kerb | left | 2519-2528 | 0-0 | kerb 2518.8-2527.8 | left s 2519-2528: kerb_detect band reading over -10..+1.5 m, offsets -0.1..+0.9 m (piece of the run s 2519-2538) on c20_s2650; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2519-2528 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 52 | kerb | left | 2529-2538 | 0-0 | kerb 2528.8-2537.8 | left s 2529-2538: kerb_detect band reading over -10..+1.5 m, offsets -0.9..-0.2 m (piece of the run s 2519-2538) on c20_s2650; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2529-2538 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 53 | kerb | left | 2673-2682 | 0-0 | kerb 2673.2-2682.2 | left s 2673-2682: kerb_detect band reading over -10..+1.5 m, offsets -0.2..+0.5 m (piece of the run s 2673-2740) on c20_s2800; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 54 | kerb | left | 2683-2692 | 0-0 | kerb 2683.2-2692.2 | left s 2683-2692: kerb_detect band reading over -10..+1.5 m, offsets -0.3..+0.0 m (piece of the run s 2673-2740) on c20_s2800; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 55 | kerb | left | 2693-2702 | 0-0 | kerb 2693.2-2702.3 | left s 2693-2702: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.3 m (piece of the run s 2673-2740) on c20_s2800, c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 56 | kerb | left | 2703-2712 | 0-0 | kerb 2703.3-2712.3 | left s 2703-2712: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 2673-2740) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 57 | kerb | left | 2713-2722 | 0-0 | kerb 2713.3-2722.3 | left s 2713-2722: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 2673-2740) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 58 | kerb | left | 2723-2732 | 0-0 | kerb 2723.3-2732.3 | left s 2723-2732: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 2673-2740) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 59 | kerb | left | 2733-2740 | 0-0 | kerb 2733.4-2740.4 | left s 2733-2740: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.2 m (piece of the run s 2673-2740) on c20_s2850; colour: t092.jpg (red / white / blue; inventory row s 2696 left) |
| 60 | kerb | left | 2837-2843 | 0-0 | kerb 2836.6-2842.6 | left s 2837-2843: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.2 m (piece of the run s 2837-2843) on c20_s2950; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2837-2843 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 61 | kerb | left | 2996-3005 | 0-0 | kerb 2996.1-3005.1 | left s 2996-3005: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.1 m (piece of the run s 2996-3008) on c20_s3100, c20_s3150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 2996-3005 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 62 | kerb | left | 3322-3331 | 0-0 | kerb 3321.9-3331 | left s 3322-3331: kerb_detect band reading over -10..+1.5 m, offsets -0.3..-0.1 m (piece of the run s 3322-3380) on c20_s3450; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 63 | kerb | left | 3332-3341 | 0-0 | kerb 3332-3341 | left s 3332-3341: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.4 m (piece of the run s 3322-3380) on c20_s3450; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 64 | kerb | left | 3342-3351 | 0-0 | kerb 3342-3351 | left s 3342-3351: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.5 m (piece of the run s 3322-3380) on c20_s3450; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 65 | kerb | left | 3352-3361 | 0-0 | kerb 3352-3361 | left s 3352-3361: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 3322-3380) on c20_s3450, c20_s3500; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 66 | kerb | left | 3362-3371 | 0-0 | kerb 3362-3371.1 | left s 3362-3371: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 3322-3380) on c20_s3500; colour: t110.jpg (red / white / blue; inventory row s 3329 left) |
| 67 | kerb | left | 3372-3380 | 0-0 | kerb 3372.1-3380.1 | left s 3372-3380: kerb_detect band reading over -10..+1.5 m, offsets -0.5..+0.0 m (piece of the run s 3322-3380) on c20_s3500; colour: colour unverified: no inventory kerb row on that side within 40 m of s 3372-3380 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 68 | kerb | left | 3461-3470 | 0-0 | kerb 3461.3-3470.3 | left s 3461-3470: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.3 m (piece of the run s 3461-3511) on c20_s3550, c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3479 left) |
| 69 | kerb | left | 3471-3480 | 0-0 | kerb 3471.3-3480.4 | left s 3471-3480: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 3461-3511) on c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3479 left) |
| 70 | kerb | left | 3481-3490 | 0-0 | kerb 3481.4-3490.4 | left s 3481-3490: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.4 m (piece of the run s 3461-3511) on c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3479 left) |
| 71 | kerb | left | 3491-3500 | 0-0 | kerb 3491.4-3500.4 | left s 3491-3500: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.5 m (piece of the run s 3461-3511) on c20_s3600; colour: t116.jpg (red / white / blue; inventory row s 3479 left) |
| 72 | kerb | left | 3501-3510 | 0-0 | kerb 3501.4-3510.4 | left s 3501-3510: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.5 m (piece of the run s 3461-3511) on c20_s3600, c20_s3650; colour: t116.jpg (red / white / blue; inventory row s 3479 left) |
| 73 | kerb | left | 3683-3692 | 0-0 | kerb 3682.9-3691.9 | left s 3683-3692: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.5 m (piece of the run s 3683-3717) on c20_s3800; colour: t124.jpg (red / white / blue; inventory row s 3725 left) |
| 74 | kerb | left | 3693-3702 | 0-0 | kerb 3692.9-3702 | left s 3693-3702: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.3 m (piece of the run s 3683-3717) on c20_s3800; colour: t124.jpg (red / white / blue; inventory row s 3725 left) |
| 75 | kerb | left | 3703-3712 | 0-0 | kerb 3703-3712 | left s 3703-3712: kerb_detect band reading over -10..+1.5 m, offsets -0.2..-0.2 m (piece of the run s 3683-3717) on c20_s3800, c20_s3850; colour: t124.jpg (red / white / blue; inventory row s 3725 left) |
| 76 | kerb | left | 3713-3717 | 0-0 | kerb 3713-3717 | left s 3713-3717: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.3 m (piece of the run s 3683-3717) on c20_s3850; colour: t124.jpg (red / white / blue; inventory row s 3725 left) |
| 77 | kerb | left | 3740-3749 | 0-0 | kerb 3740.1-3749.1 | left s 3740-3749: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.4 m (piece of the run s 3740-3755) on c20_s3850; colour: t124.jpg (red / white / blue; inventory row s 3725 left) |
| 78 | kerb | left | 3750-3755 | 0-0 | kerb 3750.1-3755.1 | left s 3750-3755: kerb_detect band reading over -10..+1.5 m, offsets -1.1..-0.6 m (piece of the run s 3740-3755) on c20_s3850, c20_s3900; colour: t124.jpg (red / white / blue; inventory row s 3725 left) |
| 79 | kerb | left | 3826-3835 | 0-0 | kerb 3826.3-3835.3 | left s 3826-3835: kerb_detect band reading over -10..+1.5 m, offsets -1.1..-0.7 m (piece of the run s 3826-3871) on c20_s3950; colour: t128.jpg (red / white / blue; inventory row s 3848 left) |
| 80 | kerb | left | 3836-3845 | 0-0 | kerb 3836.3-3845.3 | left s 3836-3845: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.6 m (piece of the run s 3826-3871) on c20_s3950; colour: t128.jpg (red / white / blue; inventory row s 3848 left) |
| 81 | kerb | left | 3846-3855 | 0-0 | kerb 3846.3-3855.4 | left s 3846-3855: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 3826-3871) on c20_s3950; colour: t128.jpg (red / white / blue; inventory row s 3848 left) |
| 82 | kerb | left | 3856-3865 | 0-0 | kerb 3856.4-3865.4 | left s 3856-3865: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.6 m (piece of the run s 3826-3871) on c20_s3950, c20_s4000; colour: t128.jpg (red / white / blue; inventory row s 3848 left) |
| 83 | kerb | left | 3866-3871 | 0-0 | kerb 3866.4-3871.4 | left s 3866-3871: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.6 m (piece of the run s 3826-3871) on c20_s4000; colour: t128.jpg (red / white / blue; inventory row s 3848 left) |
| 84 | kerb | left | 3962-3971 | 0-0 | kerb 3961.7-3970.7 | left s 3962-3971: kerb_detect band reading over -10..+1.5 m, offsets -1.0..-0.7 m (piece of the run s 3962-4015) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3981 left) |
| 85 | kerb | left | 3972-3981 | 0-0 | kerb 3971.7-3980.7 | left s 3972-3981: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.7 m (piece of the run s 3962-4015) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3981 left) |
| 86 | kerb | left | 3982-3991 | 0-0 | kerb 3981.7-3990.7 | left s 3982-3991: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 3962-4015) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3981 left) |
| 87 | kerb | left | 3992-4001 | 0-0 | kerb 3991.7-4000.8 | left s 3992-4001: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.5 m (piece of the run s 3962-4015) on c20_s4100; colour: t132.jpg (red / white / blue; inventory row s 3981 left) |
| 88 | kerb | left | 4002-4011 | 0-0 | kerb 4001.8-4010.8 | left s 4002-4011: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.5 m (piece of the run s 3962-4015) on c20_s4100, c20_s4150; colour: t132.jpg (red / white / blue; inventory row s 3981 left) |
| 89 | kerb | left | 4012-4015 | 0-0 | kerb 4011.8-4014.8 | left s 4012-4015: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.3 m (piece of the run s 3962-4015) on c20_s4150; colour: t132.jpg (red / white / blue; inventory row s 3981 left) |
| 90 | kerb | left | 4371-4380 | 0-0 | kerb 4370.8-4379.8 | left s 4371-4380: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.3 m (piece of the run s 4371-4405) on c20_s4500; colour: t142.jpg (red / white / blue; inventory row s 4371 left) |
| 91 | kerb | left | 4381-4390 | 0-0 | kerb 4380.8-4389.8 | left s 4381-4390: kerb_detect band reading over -10..+1.5 m, offsets -0.9..-0.3 m (piece of the run s 4371-4405) on c20_s4500; colour: t142.jpg (red / white / blue; inventory row s 4371 left) |
| 92 | kerb | left | 4391-4400 | 0-0 | kerb 4390.8-4399.8 | left s 4391-4400: kerb_detect band reading over -10..+1.5 m, offsets -0.9..+0.2 m (piece of the run s 4371-4405) on c20_s4500; colour: t142.jpg (red / white / blue; inventory row s 4371 left) |
| 93 | kerb | left | 4401-4405 | 0-0 | kerb 4400.8-4404.8 | left s 4401-4405: kerb_detect band reading over -10..+1.5 m, offsets +0.4..+0.9 m (piece of the run s 4371-4405) on c20_s4500; colour: t142.jpg (red / white / blue; inventory row s 4371 left) |
| 94 | kerb | right | 180-189 | 0-0 | kerb 179.5-188.5 | right s 179-189: kerb_detect band reading over -10..+1.5 m, offsets -0.7..+0.9 m (piece of the run s 179-268) on c20_s0300; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 95 | kerb | right | 190-199 | 0-0 | kerb 189.5-198.5 | right s 190-199: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.6 m (piece of the run s 179-268) on c20_s0300; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 96 | kerb | right | 200-209 | 0-0 | kerb 199.5-208.6 | right s 200-209: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.6 m (piece of the run s 179-268) on c20_s0300, c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 97 | kerb | right | 210-219 | 0-0 | kerb 209.6-218.6 | right s 210-219: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.7 m (piece of the run s 179-268) on c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 98 | kerb | right | 220-229 | 0-0 | kerb 219.6-228.6 | right s 220-229: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.6 m (piece of the run s 179-268) on c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 99 | kerb | right | 230-239 | 0-0 | kerb 229.6-238.6 | right s 230-239: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 179-268) on c20_s0350; colour: t010.jpg (red / white / blue; inventory row s 216 right) |
| 100 | kerb | right | 240-249 | 0-0 | kerb 239.6-248.7 | right s 240-249: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.6 m (piece of the run s 179-268) on c20_s0350; colour: t012.jpg (red / white / blue; inventory row s 256 right) |
| 101 | kerb | right | 250-259 | 0-0 | kerb 249.7-258.7 | right s 250-259: kerb_detect band reading over -10..+1.5 m, offsets -0.9..-0.9 m (piece of the run s 179-268) on c20_s0350, c20_s0400; colour: t012.jpg (red / white / blue; inventory row s 256 right) |
| 102 | kerb | right | 260-268 | 0-0 | kerb 259.7-267.7 | right s 260-268: kerb_detect band reading over -10..+1.5 m, offsets -0.9..-0.6 m (piece of the run s 179-268) on c20_s0400; colour: t012.jpg (red / white / blue; inventory row s 256 right) |
| 103 | kerb | right | 358-367 | 0-0 | kerb 358-367 | right s 358-367: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.6 m (piece of the run s 358-382) on c20_s0500; colour: colour unverified: no inventory kerb row on that side within 40 m of s 358-367 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 104 | kerb | right | 368-377 | 0-0 | kerb 368-377 | right s 368-377: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 358-382) on c20_s0500; colour: t018.jpg (red / white / blue; inventory row s 408 right) |
| 105 | kerb | right | 378-382 | 0-0 | kerb 378-382 | right s 378-382: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.7 m (piece of the run s 358-382) on c20_s0500; colour: t018.jpg (red / white / blue; inventory row s 408 right) |
| 106 | kerb | right | 394-403 | 0-0 | kerb 394.1-403.1 | right s 394-403: kerb_detect band reading over -10..+1.5 m, offsets -1.3..-1.2 m (piece of the run s 394-424) on c20_p0840; colour: t018.jpg (red / white / blue; inventory row s 408 right) |
| 107 | kerb | right | 404-413 | 0-0 | kerb 404.1-413.1 | right s 404-413: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.6 m (piece of the run s 394-424) on c20_p0840, c20_s0550; colour: t018.jpg (red / white / blue; inventory row s 408 right) |
| 108 | kerb | right | 414-423 | 0-0 | kerb 414.1-423.1 | right s 414-423: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.6 m (piece of the run s 394-424) on c20_s0550; colour: t018.jpg (red / white / blue; inventory row s 408 right) |
| 109 | kerb | right | 549-554 | 0-0 | kerb 548.5-553.5 | right s 548-553: kerb_detect band reading over -10..+1.5 m, offsets -5.3..-5.2 m (piece of the run s 548-553) on c20_s0700; colour: t025.jpg (red / white / blue; inventory row s 590 right) |
| 110 | kerb | right | 580-589 | 0-0 | kerb 579.6-588.6 | right s 580-589: kerb_detect band reading over -10..+1.5 m, offsets -2.7..-0.6 m (piece of the run s 580-609) on c20_s0700; colour: t025.jpg (red / white / blue; inventory row s 590 right) |
| 111 | kerb | right | 590-599 | 0-0 | kerb 589.6-598.6 | right s 590-599: kerb_detect band reading over -10..+1.5 m, offsets -0.7..+0.7 m (piece of the run s 580-609) on c20_s0700, c20_s0750; colour: t025.jpg (red / white / blue; inventory row s 590 right) |
| 112 | kerb | right | 600-609 | 0-0 | kerb 599.6-608.6 | right s 600-609: kerb_detect band reading over -10..+1.5 m, offsets +0.8..+1.5 m (piece of the run s 580-609) on c20_s0750; colour: t025.jpg (red / white / blue; inventory row s 590 right) |
| 113 | kerb | right | 1009-1018 | 0-0 | kerb 1008.7-1017.7 | right s 1009-1018: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.4 m (piece of the run s 1009-1027) on c20_s1150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1009-1018 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 114 | kerb | right | 1019-1027 | 0-0 | kerb 1018.7-1026.8 | right s 1019-1027: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.5 m (piece of the run s 1009-1027) on c20_s1150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1019-1027 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 115 | kerb | right | 1034-1043 | 0-0 | kerb 1033.8-1042.8 | right s 1034-1043: kerb_detect band reading over -10..+1.5 m, offsets -0.6..+0.6 m (piece of the run s 1034-1047) on c20_s1150; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1034-1043 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 116 | kerb | right | 1044-1047 | 0-0 | kerb 1043.8-1046.8 | right s 1044-1047: kerb_detect band reading over -10..+1.5 m, offsets +0.2..+0.6 m (piece of the run s 1034-1047) on c20_s1150, c20_s1200; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1044-1047 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 117 | kerb | right | 1164-1173 | 0-0 | kerb 1164.1-1173.2 | right s 1164-1173: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.2 m (piece of the run s 1164-1185) on c20_s1300; colour: t048.jpg (red / white; inventory row s 1175 right) |
| 118 | kerb | right | 1174-1183 | 0-0 | kerb 1174.2-1183.2 | right s 1174-1183: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.1 m (piece of the run s 1164-1185) on c20_s1300; colour: t048.jpg (red / white; inventory row s 1175 right) |
| 119 | kerb | right | 1289-1298 | 0-0 | kerb 1288.5-1297.5 | right s 1288-1297: kerb_detect band reading over -10..+1.5 m, offsets -1.2..-0.9 m (piece of the run s 1288-1309) on c20_s1400; colour: t052.jpg (red / white / blue; inventory row s 1304 right) |
| 120 | kerb | right | 1299-1308 | 0-0 | kerb 1298.5-1307.5 | right s 1298-1308: kerb_detect band reading over -10..+1.5 m, offsets -0.9..+0.0 m (piece of the run s 1288-1309) on c20_s1400, c20_s1450; colour: t052.jpg (red / white / blue; inventory row s 1304 right) |
| 121 | kerb | right | 1488-1497 | 0-0 | kerb 1488-1497 | right s 1488-1497: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.6 m (piece of the run s 1488-1510) on c20_s1600; colour: t058.jpg (red / white / blue; inventory row s 1492 right) |
| 122 | kerb | right | 1498-1507 | 0-0 | kerb 1498-1507.1 | right s 1498-1507: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.3 m (piece of the run s 1488-1510) on c20_s1600, c20_s1650; colour: t058.jpg (red / white / blue; inventory row s 1492 right) |
| 123 | kerb | right | 1774-1783 | 0-0 | kerb 1773.8-1782.8 | right s 1774-1783: kerb_detect band reading over -10..+1.5 m, offsets -0.3..+0.0 m (piece of the run s 1774-1814) on c20_s1900; colour: t066.jpg (white / red / blue; inventory row s 1773 right) |
| 124 | kerb | right | 1784-1793 | 0-0 | kerb 1783.8-1792.8 | right s 1784-1793: kerb_detect band reading over -10..+1.5 m, offsets -0.8..-0.3 m (piece of the run s 1774-1814) on c20_s1900; colour: t066.jpg (white / red / blue; inventory row s 1773 right) |
| 125 | kerb | right | 1794-1803 | 0-0 | kerb 1793.8-1802.8 | right s 1794-1803: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.4 m (piece of the run s 1774-1814) on c20_s1900, c20_s1950; colour: t066.jpg (white / red / blue; inventory row s 1773 right) |
| 126 | kerb | right | 1804-1813 | 0-0 | kerb 1803.9-1812.9 | right s 1804-1813: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.2 m (piece of the run s 1774-1814) on c20_s1950; colour: t066.jpg (white / red / blue; inventory row s 1773 right) |
| 127 | kerb | right | 1864-1872 | 0-0 | kerb 1864-1872 | right s 1864-1872: kerb_detect band reading over -10..+1.5 m, offsets +0.0..+0.2 m (piece of the run s 1864-1872) on c20_s2000; colour: t070.jpg (red / white / blue; inventory row s 1878 right) |
| 128 | kerb | right | 1922-1931 | 0-0 | kerb 1922.2-1931.2 | right s 1922-1931: kerb_detect band reading over -10..+1.5 m, offsets -3.4..-0.5 m (piece of the run s 1922-1933) on c20_s2050; colour: colour unverified: no inventory kerb row on that side within 40 m of s 1922-1931 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 129 | kerb | right | 2307-2316 | 0-0 | kerb 2307.2-2316.2 | right s 2307-2316: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.3 m (piece of the run s 2307-2343) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2313 right) |
| 130 | kerb | right | 2317-2326 | 0-0 | kerb 2317.2-2326.3 | right s 2317-2326: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 2307-2343) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2313 right) |
| 131 | kerb | right | 2327-2336 | 0-0 | kerb 2327.3-2336.3 | right s 2327-2336: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.1 m (piece of the run s 2307-2343) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2313 right) |
| 132 | kerb | right | 2337-2343 | 0-0 | kerb 2337.3-2343.3 | right s 2337-2343: kerb_detect band reading over -10..+1.5 m, offsets +0.1..+0.9 m (piece of the run s 2307-2343) on c20_s2450; colour: t082.jpg (red / white / blue; inventory row s 2313 right) |
| 133 | kerb | right | 2756-2765 | 0-0 | kerb 2756.4-2765.4 | right s 2756-2765: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 2756-2785) on c20_s2900; colour: t094.jpg (red / white / blue; inventory row s 2760 right) |
| 134 | kerb | right | 2766-2776 | 0-0 | kerb 2766.4-2775.5 | right s 2766-2775: kerb_detect band reading over -10..+1.5 m, offsets -1.4..-0.7 m (piece of the run s 2756-2785) on c20_s2900; colour: t094.jpg (red / white / blue; inventory row s 2760 right) |
| 135 | kerb | right | 2777-2786 | 0-0 | kerb 2776.5-2785.5 | right s 2776-2785: kerb_detect band reading over -10..+1.5 m, offsets -0.9..-0.4 m (piece of the run s 2756-2785) on c20_s2900; colour: t094.jpg (red / white / blue; inventory row s 2760 right) |
| 136 | kerb | right | 3391-3400 | 0-0 | kerb 3391.1-3400.1 | right s 3391-3400: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.5 m (piece of the run s 3391-3445) on c20_s3500; colour: t112.jpg (blue / white; inventory row s 3425 right) |
| 137 | kerb | right | 3401-3410 | 0-0 | kerb 3401.1-3410.2 | right s 3401-3410: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.3 m (piece of the run s 3391-3445) on c20_s3500, c20_s3550; colour: t112.jpg (blue / white; inventory row s 3425 right) |
| 138 | kerb | right | 3411-3420 | 0-0 | kerb 3411.2-3420.2 | right s 3411-3420: kerb_detect band reading over -10..+1.5 m, offsets -0.3..-0.2 m (piece of the run s 3391-3445) on c20_s3550; colour: t112.jpg (blue / white; inventory row s 3425 right) |
| 139 | kerb | right | 3421-3430 | 0-0 | kerb 3421.2-3430.2 | right s 3421-3430: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.3 m (piece of the run s 3391-3445) on c20_s3550; colour: t112.jpg (blue / white; inventory row s 3425 right) |
| 140 | kerb | right | 3431-3440 | 0-0 | kerb 3431.2-3440.3 | right s 3431-3440: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 3391-3445) on c20_s3550; colour: t114.jpg (red / white / blue; inventory row s 3445 right) |
| 141 | kerb | right | 3441-3445 | 0-0 | kerb 3441.3-3445.3 | right s 3441-3445: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.3 m (piece of the run s 3391-3445) on c20_s3550; colour: t114.jpg (red / white / blue; inventory row s 3445 right) |
| 142 | kerb | right | 3769-3778 | 0-0 | kerb 3769.1-3778.2 | right s 3769-3778: kerb_detect band reading over -10..+1.5 m, offsets +0.5..+0.7 m (piece of the run s 3769-3804) on c20_s3900; colour: t126.jpg (red / white / blue; inventory row s 3787 right) |
| 143 | kerb | right | 3779-3788 | 0-0 | kerb 3779.2-3788.2 | right s 3779-3788: kerb_detect band reading over -10..+1.5 m, offsets -0.1..+0.5 m (piece of the run s 3769-3804) on c20_s3900; colour: t126.jpg (red / white / blue; inventory row s 3787 right) |
| 144 | kerb | right | 3789-3798 | 0-0 | kerb 3789.2-3798.2 | right s 3789-3798: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.2 m (piece of the run s 3769-3804) on c20_s3900; colour: t126.jpg (red / white / blue; inventory row s 3787 right) |
| 145 | kerb | right | 3799-3804 | 0-0 | kerb 3799.2-3804.2 | right s 3799-3804: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.3 m (piece of the run s 3769-3804) on c20_s3900; colour: t126.jpg (red / white / blue; inventory row s 3787 right) |
| 146 | kerb | right | 3879-3889 | 0-0 | kerb 3879.4-3888.5 | right s 3879-3888: kerb_detect band reading over -10..+1.5 m, offsets -1.0..-0.5 m (piece of the run s 3879-3931) on c20_s4000; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 147 | kerb | right | 3890-3899 | 0-0 | kerb 3889.5-3898.5 | right s 3889-3898: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.3 m (piece of the run s 3879-3931) on c20_s4000; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 148 | kerb | right | 3900-3909 | 0-0 | kerb 3899.5-3908.5 | right s 3899-3909: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.2 m (piece of the run s 3879-3931) on c20_s4000, c20_s4050; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 149 | kerb | right | 3910-3919 | 0-0 | kerb 3909.5-3918.5 | right s 3910-3919: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.3 m (piece of the run s 3879-3931) on c20_s4050; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 150 | kerb | right | 3920-3929 | 0-0 | kerb 3919.5-3928.6 | right s 3920-3929: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.4 m (piece of the run s 3879-3931) on c20_s4050; colour: t130.jpg (red / white / blue; inventory row s 3914 right) |
| 151 | kerb | right | 4021-4030 | 0-0 | kerb 4020.8-4029.8 | right s 4021-4030: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 4021-4072) on c20_s4150; colour: t134.jpg (white / blue; inventory row s 4065 right) |
| 152 | kerb | right | 4031-4040 | 0-0 | kerb 4030.8-4039.9 | right s 4031-4040: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.2 m (piece of the run s 4021-4072) on c20_s4150; colour: t134.jpg (white / blue; inventory row s 4065 right) |
| 153 | kerb | right | 4041-4050 | 0-0 | kerb 4040.9-4049.9 | right s 4041-4050: kerb_detect band reading over -10..+1.5 m, offsets -0.2..-0.2 m (piece of the run s 4021-4072) on c20_s4150; colour: t134.jpg (white / blue; inventory row s 4065 right) |
| 154 | kerb | right | 4051-4060 | 0-0 | kerb 4050.9-4059.9 | right s 4051-4060: kerb_detect band reading over -10..+1.5 m, offsets -0.3..-0.2 m (piece of the run s 4021-4072) on c20_s4150; colour: t134.jpg (white / blue; inventory row s 4065 right) |
| 155 | kerb | right | 4061-4070 | 0-0 | kerb 4060.9-4069.9 | right s 4061-4070: kerb_detect band reading over -10..+1.5 m, offsets -5.0..-0.3 m (piece of the run s 4021-4072) on c20_s4150, c20_s4200; colour: t134.jpg (white / blue; inventory row s 4065 right) |
| 156 | kerb | right | 4087-4096 | 0-0 | kerb 4087-4096 | right s 4087-4096: kerb_detect band reading over -10..+1.5 m, offsets -0.2..-0.1 m (piece of the run s 4087-4120) on c20_s4200; colour: t134.jpg (white / blue; inventory row s 4065 right) |
| 157 | kerb | right | 4097-4106 | 0-0 | kerb 4097-4106 | right s 4097-4106: kerb_detect band reading over -10..+1.5 m, offsets -0.2..-0.1 m (piece of the run s 4087-4120) on c20_s4200; colour: t136.jpg (white / blue; inventory row s 4122 right) |
| 158 | kerb | right | 4107-4116 | 0-0 | kerb 4107-4116.1 | right s 4107-4116: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.2 m (piece of the run s 4087-4120) on c20_s4200, c20_s4250; colour: t136.jpg (white / blue; inventory row s 4122 right) |
| 159 | kerb | right | 4117-4120 | 0-0 | kerb 4117.1-4120.1 | right s 4117-4120: kerb_detect band reading over -10..+1.5 m, offsets -0.4..-0.2 m (piece of the run s 4087-4120) on c20_s4250; colour: t136.jpg (white / blue; inventory row s 4122 right) |
| 160 | kerb | right | 4170-4176 | 0-0 | kerb 4170.2-4176.2 | right s 4170-4176: kerb_detect band reading over -10..+1.5 m, offsets +0.3..+1.1 m (piece of the run s 4170-4176) on c20_s4300; colour: colour unverified: no inventory kerb row on that side within 40 m of s 4170-4176 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 161 | kerb | right | 4310-4319 | 0-0 | kerb 4309.6-4318.6 | right s 4310-4319: kerb_detect band reading over -10..+1.5 m, offsets -0.6..+0.0 m (piece of the run s 4310-4363) on c20_s4400, c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 162 | kerb | right | 4320-4329 | 0-0 | kerb 4319.6-4328.6 | right s 4320-4329: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.2 m (piece of the run s 4310-4363) on c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 163 | kerb | right | 4330-4339 | 0-0 | kerb 4329.6-4338.7 | right s 4330-4339: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.5 m (piece of the run s 4310-4363) on c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 164 | kerb | right | 4340-4349 | 0-0 | kerb 4339.7-4348.7 | right s 4340-4349: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 4310-4363) on c20_s4450; colour: t140.jpg (white / blue; inventory row s 4308 right) |
| 165 | kerb | right | 4350-4359 | 0-0 | kerb 4349.7-4358.7 | right s 4350-4359: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.5 m (piece of the run s 4310-4363) on c20_s4450; colour: colour unverified: no inventory kerb row on that side within 40 m of s 4350-4359 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 166 | kerb | right | 4360-4363 | 0-0 | kerb 4359.7-4362.7 | right s 4360-4363: kerb_detect band reading over -10..+1.5 m, offsets -1.2..-0.4 m (piece of the run s 4310-4363) on c20_s4450, c20_s4500; colour: colour unverified: no inventory kerb row on that side within 40 m of s 4360-4363 (the lap's kerbs are red / white / blue where the onboard shows them) |
| 167 | kerb | right | 4459-4464 | 0-0 | kerb 4459-4464 | right s 4459-4464: kerb_detect band reading over -10..+1.5 m, offsets -0.6..-0.5 m (piece of the run s 4459-4464) on c20_s4600; colour: t146.jpg (red / white / blue; inventory row s 4458 right) |
| 168 | kerb | right | 4473-4482 | 0-0 | kerb 4473-4482.1 | right s 4473-4482: kerb_detect band reading over -10..+1.5 m, offsets -0.7..-0.5 m (piece of the run s 4473-4495) on c20_s4600; colour: t146.jpg (red / white / blue; inventory row s 4458 right) |
| 169 | kerb | right | 4483-4492 | 0-0 | kerb 4483.1-4492.1 | right s 4483-4492: kerb_detect band reading over -10..+1.5 m, offsets -0.5..-0.3 m (piece of the run s 4473-4495) on c20_s4600; colour: t146.jpg (red / white / blue; inventory row s 4458 right) |
| 170 | kerb | right | 1878-1887 | 0-0 | kerb 1878.1-1887.1 | right s 1873-1882 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 27 readings) where kerb_detect missed the block line; colour: t070.jpg (judge r1 row: kerb on the right) |
| 171 | kerb | right | 1888-1897 | 0-0 | kerb 1888.1-1897.1 | right s 1883-1892 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 29 readings) where kerb_detect missed the block line; colour: t070.jpg (judge r1 row: kerb on the right) |
| 172 | kerb | right | 1898-1907 | 0-0 | kerb 1898.1-1907.1 | right s 1893-1902 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 18 readings) where kerb_detect missed the block line; colour: t070.jpg (judge r1 row: kerb on the right) |
| 173 | kerb | right | 1908-1915 | 0-0 | kerb 1908.1-1915.2 | right s 1903-1910 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 23 readings) where kerb_detect missed the block line; colour: t070.jpg (judge r1 row: kerb on the right) |
| 174 | kerb | right | 4418-4427 | 0-0 | kerb 4417.9-4426.9 | right s 4406-4415 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 23 readings) where kerb_detect missed the block line; colour: t144.jpg (judge r1 row: kerb on the right) |
| 175 | kerb | right | 4428-4437 | 0-0 | kerb 4427.9-4436.9 | right s 4416-4425 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 29 readings) where kerb_detect missed the block line; colour: t144.jpg (judge r1 row: kerb on the right) |
| 176 | kerb | right | 4438-4447 | 0-0 | kerb 4437.9-4447 | right s 4426-4435 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 32 readings) where kerb_detect missed the block line; colour: t144.jpg (judge r1 row: kerb on the right) |
| 177 | kerb | right | 4448-4457 | 0-0 | kerb 4448-4457 | right s 4436-4445 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 45 readings) where kerb_detect missed the block line; colour: t144.jpg (judge r1 row: kerb on the right) |
| 178 | kerb | right | 4458-4467 | 0-0 | kerb 4458-4467 | right s 4446-4455 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 48 readings) where kerb_detect missed the block line; colour: t144.jpg (judge r1 row: kerb on the right) |
| 179 | kerb | right | 4468-4470 | 0-0 | kerb 4468-4470 | right s 4456-4458 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 18 readings) where kerb_detect missed the block line; colour: t144.jpg (judge r1 row: kerb on the right) |
| 180 | kerb | left | 3728-3737 | 0-0 | kerb 3728-3737.1 | left s 3718-3727 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 11 readings) where kerb_detect missed the block line; colour: t124.jpg (judge r1 row: kerb on the left) |
| 181 | kerb | left | 3738-3747 | 0-0 | kerb 3738.1-3747.1 | left s 3728-3737 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 12 readings) where kerb_detect missed the block line; colour: t124.jpg (judge r1 row: kerb on the left) |
| 182 | kerb | left | 3748-3749 | 0-0 | kerb 3748.1-3749.1 | left s 3738-3739 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 4 readings) where kerb_detect missed the block line; colour: t124.jpg (judge r1 row: kerb on the left) |
| 183 | kerb | left | 1221-1230 | 0-0 | kerb 1221.3-1230.3 | left s 1218-1227 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 4 readings) where kerb_detect missed the block line; colour: t050.jpg (judge r1 row: kerb on the left) |
| 184 | kerb | left | 1231-1240 | 0-0 | kerb 1231.3-1240.3 | left s 1228-1237 (bands): c20 captures (c20_s2000 for 1873-1910 R, c20_s4500 / c20_s4550 for 4400-4458 R, c20_s3850 for 3718-3739 L, c20_s1300 / c20_s1350 for 1209-1238 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 6 readings) where kerb_detect missed the block line; colour: t050.jpg (judge r1 row: kerb on the left) |
| 185 | kerb | left | 534-544 | 0-0 | kerb 534.4-543.5 | left s 533-542 (bands): c20 captures (c20_s0650 / c20_s0700 for 526-546 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 19 readings) where kerb_detect missed the block line; colour: t022.jpg (judge r1 row: kerb on the left) |
| 186 | kerb | left | 545-548 | 0-0 | kerb 544.5-547.5 | left s 543-546 (bands): c20 captures (c20_s0650 / c20_s0700 for 526-546 L): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 8 readings) where kerb_detect missed the block line; colour: t022.jpg (judge r1 row: kerb on the left) |
| 187 | kerb | left | 732-741 | 0-0 | kerb 732-741 | left s 730-739 (bands): c20 captures (c20_s0850 / c20_s0900 for 695-765 L, stage3_evidence/t032cap.png): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 23 readings) where kerb_detect missed the block line; colour: t032.jpg (judge r1 row: kerb on the left) |
| 188 | kerb | left | 742-751 | 0-0 | kerb 742-751 | left s 740-749 (bands): c20 captures (c20_s0850 / c20_s0900 for 695-765 L, stage3_evidence/t032cap.png): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 20 readings) where kerb_detect missed the block line; colour: t032.jpg (judge r1 row: kerb on the left) |
| 189 | kerb | left | 752-761 | 0-0 | kerb 752-761 | left s 750-759 (bands): c20 captures (c20_s0850 / c20_s0900 for 695-765 L, stage3_evidence/t032cap.png): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 20 readings) where kerb_detect missed the block line; colour: t032.jpg (judge r1 row: kerb on the left) |
| 190 | kerb | left | 762-763 | 0-0 | kerb 762-763.1 | left s 760-761 (bands): c20 captures (c20_s0850 / c20_s0900 for 695-765 L, stage3_evidence/t032cap.png): the edge fit band reader (edges_spline.bands outer limit, -4..+1.5 m, 4 readings) where kerb_detect missed the block line; colour: t032.jpg (judge r1 row: kerb on the left) |
| 191 | station | right | 480-480 | 8-8 | marshal 'T1 exit' | c20_s0650: white roof 5.5 m2 in a dark tyre ring (compare/blob_scan.py, 0.4 m beyond the right edge at s 482); onboard t020 (0:20): canopy on posts on a tyre-faced mound close right; inventory s 477 right |
| 192 | station | right | 822-822 | 7-7 | marshal 'T2 to T3, east side' | c20_s0600: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 7.1 m beyond the right edge at s 820); onboard t034 (0:34): blue canopy on a tyre-faced mound ahead right; inventory s 834 right |
| 193 | station | right | 1016-1016 | 10-10 | marshal 'T3' | c20_s1150: white roof 5.6 m2 in a dark tyre ring (compare/blob_scan.py, 9.2 m beyond the right edge at s 1014); onboard t040 (0:40): blue canopy on posts on a tyre-faced mound close right; inventory s 996 right |
| 194 | station | right | 1180-1180 | 11-11 | marshal 'T4' | c20_s1300: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.6 m beyond the right edge at s 1173); onboard t046 (0:46): canopy on posts ahead right; inventory s 1186 right |
| 195 | station | right | 1497-1497 | 12-12 | marshal 'T5' | c20_s1550: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.8 m beyond the right edge at s 1492); onboard t058 (0:58): canopy on a tyre-faced mound right; inventory s 1524 right |
| 196 | station | right | 2075-2075 | 10-10 | marshal 'T6 (Riverside)' | c20_s2150: white roof 6.3 m2 in a dark tyre ring (compare/blob_scan.py, 10.4 m beyond the right edge at s 2069); onboard t074 (1:14): canopy on a tyre-faced mound ahead right; inventory s 2050 right |
| 197 | station | right | 2363-2363 | 19-19 | marshal 'T7' | c20_s2500: white roof 5.9 m2 in a dark tyre ring (compare/blob_scan.py, 19.2 m beyond the right edge at s 2358); onboard t082 (1:22): canopy on a mound ahead right; inventory s 2372 right |
| 198 | station | right | 2769-2769 | 10-10 | marshal 'T8' | c20_s2900: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 9.8 m beyond the right edge at s 2764); onboard t092 (1:32): canopy on posts ahead right; inventory s 2776 right |
| 199 | station | right | 3196-3196 | 11-11 | marshal 'north leg before T9' | c20_s3300: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 11.0 m beyond the right edge at s 3189); onboard not in the 2 s frames (t106-t108 look past it); roof and tyre ring on c20_s3300 / c20_s3350 |
| 200 | station | right | 3426-3426 | 14-14 | marshal 'T9 (Star Mazda)' | c20_s3500: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 13.6 m beyond the right edge at s 3420); onboard t112 (1:52): roofed platform on stilts ahead right; inventory s 3436 right |
| 201 | station | right | 3709-3709 | 8-8 | marshal 'T10' | c20_s3800: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 15.4 m beyond the right edge at s 3698); onboard t122 (2:02): station far ahead right; inventory s 3758 right |
| 202 | station | left | 4281-4281 | 9-9 | marshal 'T11 approach (Sunset)' | c20_s4350: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 5.0 m beyond the left edge at s 4272); onboard t138 (2:18): canopy on a tyre-faced mound ahead left; inventory s 4274 left |
| 203 | station | left | 246-246 | 42-42 | marshal 'T1 inside canopy' | c20_s0300 / c20_s0350: a white roof ~5 x 3 m among the trees inside T1, 42 m beyond the left edge at s 247 (compare/blob_scan.py; stage3_evidence/blob247.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60; judge r1 row) |
| 204 | station | left | 200-200 | 5-5 | marshal 'pit-wall end hut' | c20_s0300 / c20_s0350: white roof 7.8 m2 at the east end of the pit wall (compare/blob_scan.py, 5.2 m beyond the left edge at s 199; window stage3_evidence/cw_wallend.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60) |
| 205 | station | left | 2-2 | 4-4 | marshal 'starter's stand' | c20_s0050 / c20_s0100 / c20_s0150: the white structure on the pit wall at the timing line (blob_scan s 2, 3.4 m beyond the left edge); pit-lane video ucmXJu5QKFQ 22:19-22:28: the scaffold starter's stand with a canopy on the pit wall |
| 206 | mast | left | 3441-3441 | 161-161 | mast '' | OSM man_made=mast / communications tower node 10220517717; the lidar (CA_SanJoaquin_2021) has an isolated spike 49.5-49.7 m over the DEM there (30 cells, compare/stage3 lidar spike scan); onboard t106 (1:46): a tall thin pole far ahead on the north leg (inventory mast row s 3400 ahead, ahead_m 250) |
| 207 | building | left | 4688-13 (wraps) | 46-63 | building 0 '' 4.3 m | osm (pit-lane video ucmXJu5QKFQ 21:52-22:10 (t1312000, t1330000): the two-storey timing tower with the blue roof beside the pit lane; OSM footprint, lidar height) |
| 208 | building | left | 4685-11 (wraps) | 25-43 | structure 0 block 'timing tower' | OSM 765811057; pit-lane video ucmXJu5QKFQ 21:52-22:10 (t1312000, t1330000) and onboard t146-t152 (judge r2): tan / beige walls, a glazed band on the upper storey only, an exterior stair and balcony on the track side; inventory: control tower, 2 storeys, blue flat roof on posts |
| 209 | building | left | 4685-4697 | 34-35 | structure 1 fuel 'timing tower roof deck' | pit-lane video t1312000 / t1330000 and onboard t004 / t146-t152: the blue flat roof on posts over the tower deck, a broad overhang (1.5 m past the OSM footprint each side, judge r2) |
| 210 | cone_line | right | 4581-4583 | 0-4 | cone line 0 | closed road Pacific (OSM 34350988) mouth (onboard t150-t152 (judge r2 runoff, s 4607 R): cones across the front-straight crossover mouth) |
| 211 | cone_line | right | 1829-1831 | 0-1 | cone line 1 | closed road crossover (OSM 34351015) mouth (onboard t068 (judge r2 runoff_02, s 1824 R): cones across the crossover mouth) |
| 212 | cone_line | right | 140-160 | 2-2 | cone line 2 | onboard t006-t008 (judge r2, fwd_00): several orange cones on the paved shoulder right |
| 213 | cone_line | left | 895-905 | 1-2 | cone line 3 | onboard t036 (judge r2, fwd_02 / fwd_03): orange cones on the left |
| 214 | cone_line | right | 1780-1830 | 3-3 | cone line 4 | onboard t066-t068 (judge r2, fwd_06): a long line of cones separating the adjacent pavement (the Dog Leg / crossover mouth) on the right |
| 215 | cone_line | left | 3250-3300 | 1-2 | cone line 5 | onboard t108-t110 (judge r2, fwd_10 / fwd_11): orange cones along the left |
| 216 | cone_line | right | 3645-3655 | 1-2 | cone line 6 | onboard t122 (judge r2, fwd_12): orange cones on the right |
| 217 | cone_line | left | 4507-4669 | 3-5 | cone line 7 | pit-lane video t1267000-t1348000 (judge r2 pit_01 / pit_02): small cones along the pit wall, lane side, s 4478-4679 |
| 218 | cone_line | left | 4519-40 (wraps) | 20-22 | cone line 8 | pit-lane video t1249000-t1348000 (judge r2 pit_01 / pit_02): small cones along the paddock-side K-rail, lane side |
| 219 | cone_line | left | 752-772 | 3-3 | cone line 9 | onboard t030 / compare_sheets s0700, s0750 (fwd_02, side_02): a line of small orange cones on the pale apron left of the T2 approach (inventory cone_line row s 770 left, ahead_m 80); the "3-4 cones" of s0700 are this line seen from 60 m back |
| 220 | cone_line | left | 3196-3204 | 2-2 | cone line 10 | compare_sheets s3200 (fwd_10): three orange cones at a mouth on the left |
| 221 | cone_line | right | 4046-4054 | 3-3 | cone line 11 | compare_sheets s4050 (fwd_13): cones on the right apron, 20 m before the t134 cone at s 4071 |
| 222 | cone_line | right | 20-24 | 1-2 | cone line 12 | onboard t006.jpg (yellow, orange; inventory s 20 right: two cones, yellow and orange); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 223 | cone_line | right | 297-298 | 1-2 | cone line 13 | onboard t012.jpg (orange; inventory s 297 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 224 | cone_line | left | 533-534 | 1-1 | cone line 14 | onboard t022.jpg (orange; inventory s 533 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 225 | cone_line | left | 834-835 | 2-2 | cone line 15 | onboard t034.jpg (orange; inventory s 834 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 226 | cone_line | left | 973-974 | 1-1 | cone line 16 | onboard t038.jpg (orange; inventory s 973 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 227 | cone_line | right | 1040-1041 | 1-2 | cone line 17 | onboard t042.jpg (orange; inventory s 1040 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 228 | cone_line | right | 1307-1308 | 1-1 | cone line 18 | onboard t052.jpg (orange; inventory s 1307 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 229 | cone_line | right | 2158-2159 | 1-1 | cone line 19 | onboard t078.jpg (orange; inventory s 2158 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 230 | cone_line | left | 2696-2700 | 1-1 | cone line 20 | onboard t092.jpg (orange; inventory s 2696 left: two orange cones); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 231 | cone_line | right | 3439-3440 | 1-2 | cone line 21 | onboard t114.jpg (orange; inventory s 3439 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 232 | cone_line | right | 4071-4072 | 1-2 | cone line 22 | onboard t134.jpg (orange; inventory s 4071 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 233 | cone_line | right | 4575-4576 | 1-2 | cone line 23 | onboard t002.jpg (orange; inventory s 4575 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |
| 234 | cone_line | right | 4593-4594 | 1-2 | cone line 24 | onboard t150.jpg (orange; inventory s 4593 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb) |

###### Every inventory row and its outcome (101 rows)

| s (m) | t | side | kind | what | source | outcome |
|---|---|---|---|---|---|---|
| 21 | 0:06.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@6.0 | covered by barrier 0 (concrete); barrier 2 (concrete) |
| 21 | 0:06.0 | right | cone_line | two cones, yellow and orange | onboard:7QS2M-HGSI4@6.0 | covered by cone line 12 |
| 104 | 0:08.0 | left | wall | concrete K-rail, a dark (black) section at its east end | onboard:7QS2M-HGSI4@8.0 | covered by barrier 0 (concrete); barrier 3 (concrete) |
| 146 | 0:09.0 | right | cone_line | several orange cones on the paved shoulder | onboard:7QS2M-HGSI4@9.0 | covered by cone line 2 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 216 | 0:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@10.0 | covered by kerb 199.5-208.6; kerb 209.6-218.6 |
| 246 | 0:10.0 | left | station | canopy on posts over a low concrete platform | onboard:7QS2M-HGSI4@10.0 | covered by marshal 'T1 inside canopy' |
| 256 | 0:12.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@12.0 | covered by kerb 239.6-248.7; kerb 249.7-258.7 |
| 296 | 0:12.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@12.0 | covered by cone line 13 |
| 300 | 0:14.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@14.0 | covered by kerb 280.8-289.8; kerb 290.8-299.8 |
| 408 | 0:18.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@18.0 | covered by kerb 394.1-403.1; kerb 404.1-413.1 |
| 477 | 0:20.0 | right | station | corner station: canopy on posts on a tyre-walled earth mound | onboard:7QS2M-HGSI4@20.0 | covered by marshal 'T1 exit' |
| 477 | 0:20.0 | right | tyre_wall | tyres around the station mound | onboard:7QS2M-HGSI4@20.0 | covered by barrier 4 (tyres) |
| 531 | 0:22.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@22.0 | covered by cone line 14 |
| 531 | 0:22.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@22.0 | covered by kerb 534.4-543.5; kerb 544.5-547.5 |
| 574 | 0:24.0 | right | runoff | pale paved / concrete patch inside the hairpin | onboard:7QS2M-HGSI4@24.0 | surroundings (not a checked kind) |
| 590 | 0:25.0 | right | kerb | block line on the inside of the T2 hairpin apex | onboard:7QS2M-HGSI4@25.0 | covered by kerb 579.6-588.6; kerb 589.6-598.6 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 738 | 0:32.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@32.0 | covered by kerb 746-752; kerb 732-741 |
| 770 | 0:30.0 | left | cone_line | line of small cones | onboard:7QS2M-HGSI4@30.0 | covered by cone line 9 |
| 833 | 0:34.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@34.0 | covered by cone line 15 |
| 833 | 0:34.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@34.0 | covered by marshal 'T2 to T3, east side' |
| 893 | 0:37.0 | left | cone_line | orange cones on the left | onboard:7QS2M-HGSI4@37.0 | covered by cone line 3 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 972 | 0:38.0 | left | cone_line | single orange cone | onboard:7QS2M-HGSI4@38.0 | covered by cone line 16 |
| 972 | 0:38.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@38.0 | covered by kerb 954.6-963.6; kerb 964.6-973.6 |
| 996 | 0:40.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@40.0 | covered by kerb 974.6-983.6; kerb 984.6-993.7 |
| 996 | 0:40.0 | right | station | corner station: blue canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@40.0 | MISSING |
| 1041 | 0:42.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@42.0 | covered by cone line 17 |
| 1088 | 0:44.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@44.0 | covered by kerb 1082.9-1091.9 |
| 1175 | 0:48.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@48.0 | covered by kerb 1164.1-1173.2; kerb 1174.2-1183.2 |
| 1190 | 0:46.0 | right | station | corner station: canopy on posts | onboard:7QS2M-HGSI4@46.0 | covered by marshal 'T4' |
| 1224 | 0:50.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@50.0 | covered by kerb 1221.3-1230.3; kerb 1231.3-1240.3 |
| 1304 | 0:52.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@52.0 | covered by kerb 1288.5-1297.5; kerb 1298.5-1307.5 |
| 1309 | 0:52.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@52.0 | covered by cone line 18 |
| 1344 | 0:54.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@54.0 | covered by kerb 1330.6-1339.6; kerb 1340.6-1349.6 |
| 1476 | 0:56.0 | left | paint | white painted blocks at the left edge | onboard:7QS2M-HGSI4@56.0 | surroundings (not a checked kind) |
| 1492 | 0:58.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@58.0 | covered by kerb 1488-1497; kerb 1498-1507.1 |
| 1522 | 0:58.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@58.0 | MISSING |
| 1645 | 1:00.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@60.0 | covered by kerb 1640.4-1649.4; kerb 1650.4-1659.5 (corrected in first-centre round, 20 Oct 2026 (judge r1): ahead_m was 30) |
| 1645 | 1:02.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@62.0 | covered by kerb 1640.4-1649.4; kerb 1650.4-1659.5 |
| 1773 | 1:06.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@66.0 | covered by kerb 1773.8-1782.8; kerb 1783.8-1792.8 (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 1793 | 1:07.0 | right | cone_line | a long line of cones separating the adjacent pavement | onboard:7QS2M-HGSI4@67.0 | covered by cone line 4 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 1824 | 1:08.0 | right | cone_line | cones across the crossover mouth | onboard:7QS2M-HGSI4@68.0 | covered by cone line 1; cone line 4 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 1839 | 1:08.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@68.0 | covered by kerb 1842-1848 (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
| 1878 | 1:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@70.0 | covered by kerb 1864-1872; kerb 1878.1-1887.1 |
| 2022 | 1:12.0 | left | paint | white painted chevrons / blocks at the left edge | onboard:7QS2M-HGSI4@72.0 | surroundings (not a checked kind) |
| 2053 | 1:14.0 | right | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@74.0 | MISSING |
| 2158 | 1:18.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@78.0 | covered by cone line 19 |
| 2313 | 1:22.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@82.0 | covered by kerb 2307.2-2316.2; kerb 2317.2-2326.3 |
| 2373 | 1:22.0 | right | station | corner station: canopy on a mound | onboard:7QS2M-HGSI4@82.0 | covered by marshal 'T7' |
| 2697 | 1:32.0 | left | cone_line | two orange cones | onboard:7QS2M-HGSI4@92.0 | covered by cone line 20 |
| 2697 | 1:32.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@92.0 | covered by kerb 2673.2-2682.2; kerb 2683.2-2692.2 |
| 2760 | 1:34.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@94.0 | covered by kerb 2756.4-2765.4; kerb 2766.4-2775.5 |
| 2777 | 1:32.0 | right | station | corner station: canopy on posts | onboard:7QS2M-HGSI4@92.0 | covered by marshal 'T8' |
| 2857 | 1:36.0 | left | paint | white painted blocks at the left edge | onboard:7QS2M-HGSI4@96.0 | surroundings (not a checked kind) |
| 3196 | 1:47.0 | left | cone_line | three orange cones at a mouth | onboard:7QS2M-HGSI4@107.0 | covered by cone line 10 (corrected in first-centre round, 20 Oct 2026 (judge r1): ) (row added in true) |
| 3287 | 1:49.0 | left | cone_line | orange cones along the left | onboard:7QS2M-HGSI4@109.0 | covered by cone line 5 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 3329 | 1:50.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@110.0 | covered by kerb 3321.9-3331; kerb 3332-3341 |
| 3425 | 1:52.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@112.0 | covered by kerb 3401.1-3410.2; kerb 3411.2-3420.2 |
| 3440 | 1:52.0 | right | station | corner station: roofed platform on stilts | onboard:7QS2M-HGSI4@112.0 | covered by marshal 'T9 (Star Mazda)' |
| 3444 | 1:46.0 | ahead | mast | tall pole (light / camera mast) | onboard:7QS2M-HGSI4@106.0 | MISSING (corrected in stage-3 pass, 20 Oct 2026: ahead_m was 250) |
| 3445 | 1:54.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@114.0 | covered by cone line 21 |
| 3445 | 1:54.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@114.0 | covered by kerb 3421.2-3430.2; kerb 3431.2-3440.3 |
| 3479 | 1:56.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@116.0 | covered by kerb 3461.3-3470.3; kerb 3471.3-3480.4 |
| 3645 | 2:02.0 | right | cone_line | orange cones on the right | onboard:7QS2M-HGSI4@122.0 | covered by cone line 6 (corrected in round 3, 20 Oct 2026 (judge r2): ) (row added in true) |
| 3725 | 2:04.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@124.0 | covered by kerb 3703-3712; kerb 3713-3717 |
| 3765 | 2:02.0 | right | station | corner station | onboard:7QS2M-HGSI4@122.0 | MISSING |
| 3787 | 2:06.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@126.0 | covered by kerb 3769.1-3778.2; kerb 3779.2-3788.2 |
| 3848 | 2:08.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@128.0 | covered by kerb 3826.3-3835.3; kerb 3836.3-3845.3 |
| 3914 | 2:10.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@130.0 | covered by kerb 3899.5-3908.5; kerb 3909.5-3918.5 |
| 3981 | 2:12.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@132.0 | covered by kerb 3961.7-3970.7; kerb 3971.7-3980.7 |
| 4045 | 2:14.0 | right | cone_line | cones on the right apron | onboard:7QS2M-HGSI4@134.0 | covered by cone line 11 (corrected in first-centre round, 20 Oct 2026 (judge r1): ) (row added in true) |
| 4065 | 2:14.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@134.0 | covered by kerb 4040.9-4049.9; kerb 4050.9-4059.9 |
| 4070 | 2:14.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@134.0 | covered by cone line 22 |
| 4122 | 2:16.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@136.0 | covered by kerb 4107-4116.1; kerb 4117.1-4120.1 |
| 4273 | 2:18.0 | left | station | corner station: canopy on posts on a tyre-walled mound | onboard:7QS2M-HGSI4@138.0 | covered by marshal 'T11 approach (Sunset)' |
| 4308 | 2:20.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@140.0 | covered by kerb 4309.6-4318.6; kerb 4319.6-4328.6 |
| 4371 | 2:22.0 | left | kerb | flat painted kerb | onboard:7QS2M-HGSI4@142.0 | covered by kerb 4370.8-4379.8; kerb 4380.8-4389.8 |
| 4410 | 2:24.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@144.0 | covered by kerb 4417.9-4426.9 |
| 4458 | 2:26.0 | right | kerb | flat painted kerb | onboard:7QS2M-HGSI4@146.0 | covered by kerb 4459-4464; kerb 4473-4482.1 |
| 4502 | 0:00.0 | left | wall | concrete K-rail (Jersey) segments | onboard:7QS2M-HGSI4@0.0 | covered by barrier 0 (concrete) |
| 4502 | 0:00.0 | right | runoff | dirt, flat, open | onboard:7QS2M-HGSI4@0.0 | surroundings (not a checked kind) |
| 4573 | 0:02.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@2.0 | covered by cone line 0; cone line 23 |
| 4593 | 2:30.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@150.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4593 | 2:30.0 | right | cone_line | single orange cone | onboard:7QS2M-HGSI4@150.0 | covered by cone line 0; cone line 24 |
| 4599 | 2:28.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@148.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4643 | 0:04.0 | left | wall | concrete K-rail (Jersey) | onboard:7QS2M-HGSI4@4.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4662 | 2:32.0 | left | wall | concrete K-rail | onboard:7QS2M-HGSI4@152.0 | covered by barrier 0 (concrete); barrier 1 (concrete) |
| 4693 | 0:02.0 | left | building | control tower: 2 storeys, blue flat roof on posts over a deck | onboard:7QS2M-HGSI4@2.0 | covered by building 0 '' 4.3 m; structure 0 block 'timing tower' |
| 4695 | 0:04.0 | left | building | control tower | onboard:7QS2M-HGSI4@4.0 | covered by building 0 '' 4.3 m; structure 0 block 'timing tower' (corrected in stage-3 pass, 20 Oct 2026: ahead_m was none) |
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
