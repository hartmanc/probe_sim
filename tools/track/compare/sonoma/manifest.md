# Sonoma scenery evidence manifest (round 3, 20 Oct 2026; rounds 4 and 5 below)

Rule (owner, after the round-2 drive): **no object without a cited source.** Every kerb strip, wall, tyre wall, fence,
grandstand, corner station, sign and cone line in `public/tracks/sonoma/scenery.json` traces to a clean z20 capture
(`satellite_clean/c20_*`, 2026 imagery, 0.117 m/px), the March 2026 Lemons onboard youtube.com/watch?v=RAZip6S84CM
(m:ss), a Street View panorama id (July 2011, checked against the onboard because of the Dec 2023 - Feb 2024 repave)
or OSM. The config (`tools/track/tracks/sonoma/config.py`, `scenery`) carries the same source on every entry; this
table is generated from the published package. Tools: `compare/kerb_detect.py` (block pattern along both edges),
`compare/capstrip.py` (straightened capture strips), `compare/wall_measure.py` (wall / tyre line picked every 0.5 m
across a guide), `compare/capwin.py` (north-up window with the package drawn over it).

Not covered by the rule (unchanged, from data): trees (lidar + NAIP canopy check), buildings (OSM footprints; the four
OSM grandstands are now terraces), the footbridge at s 295 (OSM), painted edge lines (rule: the
captures show white edge lines everywhere except through kerbs), the pit lane and closed-road pavement (OSM ways).

## Building heights (fix round, 20 Oct 2026; config `scenery.building_height_robust`, Laguna off)

Height = the 60th percentile of the lidar surface above the footprint's ground (2022-24 survey), not the 85th; where
p90 - p50 > 6 m (a mast, tower or slope inside the outline) the p50, logged; a footprint with no lidar structure above
2.5 m (p90 < 2.5 m) is dropped, logged. Sonoma: all 24 OSM buildings re-measured, 4 dropped (OSM 1019835306,
1019837485, 1019838290, 1019838923: p90 0.0-0.2 m), 1 capped:

| OSM | where | before | after | lidar p50 / p60 / p90 | evidence |
|---|---|---|---|---|---|
| 262082790 'Sonoma Raceway' | 59 m left of s 4063 | 25.6 m | 9.3 m (capped) | 9.3 / 11.1 / 26.1 | c20_s1650 / s1705: the outline is the main grandstand bowl at the line (rows rising away from the track) with the suites and timing tower at its back; Street View 5MY4xR9O7etAXEHnZCVnGQ, QduY6QTXmw4JDevQVE_b-g: 2-3 storeys at the front. Still drawn as one 9.3 m block: handed to the buildings round (owner_22 reference: bleachers on a block-wall base, stair towers, glazed suites deck, timing tower); item 2 of round 4 dropped by the owner |
| 1019838438 | 13 m right of s 3419 (T11 approach) | 14.2 m | DROPPED (round 4, evidence override) | 11.7 / 12.5 / 14.2 | lidar (2022-24): a ~12 m structure. c20_s1045 (2026): a temporary white tent (~8 x 30 m) on part of the outline. Onboard RAZip6S84CM 1:53-1:55.6 (Mar 2026, newest): tyre stacks and fence at the edge, an ambulance and low cabins, open paved infield, no tent and no building. Source precedence: onboard wins, so no building (see 'Round 4') |
| 1019836595 | 44 m left of s 3923 (T12) | 9.8 m | 8.7 m | 8.6 / 8.7 / 9.9 | c20_s1540: flat-roofed building beside the T12 exit; Street View QduY6QTXmw4JDevQVE_b-g: two-storey buildings both sides |

Laguna (report only, its package unchanged): the rule would change 49 of its 52 OSM buildings (mostly -0.1 to -1 m,
'Tower' 14.4 -> 13.9 m, 220990689 6.7 -> 4.7, 639859972 7.6 -> 4.4) and drop 5 (639859968, 639859969, 773078645,
773078646, 1015992235).

## Removed for lack of evidence (round 2 -> round 3): 61 objects

| what | count | why |
|---|---|---|
| rule kerbs (apex + exit on every corner, Laguna's radius rule) | 30 strips | replaced by 28 detected and confirmed strips; e.g. T7 left (owner_7) has no kerb in owner_9 / c20_s3905 / Street View J6fsnW4hj4xCjQLzrgRGzA |
| green after-kerb strips (exit kerbs `paint 1.5`) | (on 15 of the 30) | no green paint beyond any kerb in the captures or the onboard |
| brake boards 3-2-1 at T2, T4, T7a, T11 | 12 | none in the onboard approaches (0:09-0:12, 0:28-0:33, 1:09-1:12, 1:52-1:57); the TURN 11 "1"/"2" boards stood in the pit-in lane |
| corner-number boards | 15 | none in the onboard; "Turn 1", "Turn 3a" are painted on the road (Street View) |
| starter's flag stand | 1 | Laguna rule; none over the pit wall at the line (onboard 2:16-2:19) |
| rule pit wall (OSM pit-lane extent, halfway) | 3 runs | closed the pit exit (owner_2); the pit-side walls are now measured |

Kept and re-measured from round 2: the two pit-straight walls (19 Oct wall_measure on c20_s1595..s1870); the
pit-lane-side one now ends at its nose at T1 (c20_s1815) instead of running on to the pit-out merge.

## Objects in the package (78 rows; round 3, historical: the current list is the generated table of round 5 at the end)

| # | kind | side | track s (m) | source | how measured |
|---|---|---|---|---|---|
| 1 | kerb (red/white, raised 10 cm) | right | 116-130 | T1 exit right, run 1 of the broken kerb: c20_s1870 (detector run 116.7-129.7, block pattern), feature note c20_s1925 | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 2 | kerb (red/white, raised 10 cm) | right | 143-150 | T1 exit right, run 2: c20_s1870 (detector 143.7-149.7) | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 3 | kerb (red/white, raised 10 cm) | right | 161-179 | T1 exit right, run 3: c20_s1870 / c20_s1925 (detector 161.6-178.6, red) | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 4 | kerb (red/white, raised 10 cm) | right | 202-220 | T1 exit right, run 4: c20_s1925 (detector 203.5-219.5) | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 5 | kerb (red/white, raised 10 cm) | left | 330-372 | T2 entry, outside (owner_3): c20_s2090 / c20_s2035 blocks on the left edge (capstrip s300); onboard RAZip6S84CM 0:10 red/white kerb left on entry | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 6 | kerb (red/white, raised 10 cm) | right | 398-451 | T2 apex: c20_s2145 (detector 412.1-428.0, 436.0-451.0); onboard 0:13-0:14 red/white apex kerb right | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 7 | kerb (red/white, raised 10 cm) | right | 605-656 | T3 approach, right: c20_s2365 (detector 610.6-655.5, red); onboard 0:20.6-0:21 kerb on the right | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 8 | kerb (red/white, raised 10 cm) | left | 690-745 | T3 apex: c20_s2420 / c20_s2475 blocks on the left edge (capstrip s600); onboard 0:24 red/white kerb left | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 9 | kerb (red/white, raised 10 cm) | right | 760-814 | T3a apex (right; no kerb on the left of 3a): c20_s2530 (detector 781.2-814.2) and blocks from 760 (capstrip s750) | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 10 | kerb (red/white, raised 10 cm) | left | 855-960 | T4 entry, outside: c20_s2585..s2750 blocks on the left edge (capstrip s750/s900); onboard 0:30-0:32 red/white kerb left | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 11 | kerb (red/white, raised 10 cm) | right | 990-1030 | T4 apex: c20_s2750 (detector 995.8-1027.7, red); onboard 0:34-0:36 red/white apex kerb right | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 12 | kerb (red/white, raised 10 cm) | left | 1025-1094 | T4 exit, outside: c20_s2750..s2860 blocks on the left edge (capstrip s900/s1050); onboard 0:38 red/white kerb left | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 13 | kerb (red/white, raised 10 cm) | right | 1150-1262 | T5 apex and exit: c20_s2860..s2970 (detector 1154.4-1165.4, 1182.3-1261.2, red) | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 14 | kerb (red/white, raised 10 cm) | left | 1591-1646 | Carousel (T6) apex: c20_s3355 / c20_s3410 (detector 1591.4-1646.3); onboard 0:55 red/white kerb left | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 15 | kerb (red/white, raised 10 cm) | right | 1721-1796 | Carousel exit, right: c20_s3465 / c20_s3520 (detector 1721.1-1796.0, red); onboard 0:60 red/white kerb right | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 16 | kerb (red/white, raised 10 cm) | right | 2150-2202 | T7 island (apex): c20_s3905 / c20_s3960 (detector 2172.1-2180.1, 2188.1-2201.1); satellite owner_9; onboard 1:12 red/white island kerb | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 17 | kerb (red/white, raised 10 cm) | right | 2208-2330 | T7a island (O'Reilly): c20_s3960..s4070 (detector 2216.0-2223.0, 2324.8-2331.8; blocks along the island, capstrip s2250); onboard 1:16 red/white | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 18 | kerb (red/white, raised 10 cm) | left | 2300-2372 | T7a exit, outside: c20_s4015 / c20_s4070 / c20_s0000 (detector 2299.8-2309.8, 2315.8-2371.7); satellite owner_9 outer kerb | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 19 | kerb (red/white, raised 10 cm) | left | 2410-2440 | T8 apex: c20_s0055 (detector 2417.6-2440.5, red); onboard 1:18-1:20 red/white kerb left | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 20 | kerb (red/white, raised 10 cm) | right | 2440-2550 | T8a apex: c20_s0055..s0165 (detector 2441.5-2447.5, 2479.4-2505.4, 2523.3-2537.3; blocks capstrip s2400); onboard 1:22-1:24 | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 21 | kerb (red/white, raised 10 cm) | left | 2520-2572 | T8a exit, outside: c20_s0165 / c20_s0220 (detector 2542.3-2572.2); onboard 1:26 red/white kerb left | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 22 | kerb (red/white, raised 10 cm) | left | 2600-2645 | T9 apex: c20_s0220 / c20_s0275 (detector 2600.2-2645.1, red); onboard 1:28 | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 23 | kerb (red/white, raised 10 cm) | right | 2692-2740 | T9 exit, outside: c20_s0330 / c20_s0385 (detector 2692.0-2739.8, red) | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 24 | kerb (red/white, raised 10 cm) | right | 3020-3045 | 9a chicane, right-hand part apex: c20_o0660 (detector 3021.2-3036.2, red); onboard 1:39 kerb right | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 25 | kerb (red/white, raised 10 cm) | left | 3060-3170 | 9a chicane left-hand part apex and on to T10: c20_o0715 / c20_s0715 / c20_s0770 (detector 3060.1-3169.9); onboard 1:41 red/white kerb left | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 26 | kerb (red/white, raised 10 cm) | right | 3215-3292 | T10 apex: c20_s0825..s0935 (detector 3219.8-3292.6, red); onboard 1:45 | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 27 | kerb (red/white, raised 10 cm) | left | 3338-3402 | T10 exit, outside: c20_s0990 / c20_s1045 (detector 3338.5-3369.4, 3379.4-3402.4) | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 28 | kerb (red/white, raised 10 cm) | right | 3615-3745 | T11 hairpin apex: c20_s1265..s1375 (detector 3628.8-3673.7, 3700.7-3730.6; blocks capstrip s3600); onboard 2:01-2:04 red/white | kerb_detect.py block pattern on the capture and/or capstrip.py, ends on the edge |
| 29 | armco | right | 705-829 | osm:380830042 | OSM polyline |
| 30 | armco | right | 822-976 | osm:380830043 | OSM polyline |
| 31 | concrete | left | 4098-1 (wraps) | declared: pit straight, pit-lane side, to its nose at T1 (c20_s1595..s1870 bright band 2.0 m beyond the left edge (19 Oct); nose on c20_s1815 (s ~103); onboard 2:16-2:20) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 32 | concrete | left | 106-208 | declared: pit-out lane, paddock side (c20_s1870 / c20_s1925, bright band along the lane outer side (wall_measure, 87 % picked, rms 0.30 m); onboard 2:23 / 0:06.5) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 33 | concrete | right | 4097-0 (wraps) | declared: pit straight, drag-strip side (c20_s1595..s1870 bright band 2.3 m beyond the right edge (19 Oct); Street View 5MY4xR9O7etAXEHnZCVnGQ; onboard 2:17) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 34 | concrete | left | 1659-2109 | declared: T6 to T7, left (Carousel exit along the drag strip and the T7 road) (c20_s3465..s3850 bright band at the asphalt end (wall_measure along the left edge, 83 % picked, rms 0.11 m, gaps bridged); onboard 0:58-1:12 light-blue wall, Toyota boards at 1:10) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 35 | tyres | left | 2066-2145 | declared: T7 approach, left tyre wall (c20_s3850 / c20_s3905 dark tyre stack 4-10 m beyond the left edge (96 % picked, rms 0.35 m); Street View gd1SNdksCq5QZtwlsrzR7g) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 36 | concrete | right | 1149-1363 | declared: T5 to the T6 crest, right (c20_s2860..s3080 light wall line 3-6 m beyond the right edge (76 % picked); onboard 0:43-0:48.5 concrete wall on the right (not in the Jul 2011 Street View GMaTaipEd9Hm7fMNE26aGQ: built since)) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 37 | tyres | left | 2478-2585 | declared: T8a to T9, left (the bank) (c20_s0110 / c20_s0165 dark barrier ~20 m left (99 % picked, rms 0.34 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 38 | concrete + 3.0 m fence | left | 2585-2690 | declared: T9, left (the bank) (c20_s0220 / c20_s0275 bright wall ~19 m left (95 % picked, rms 0.27 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA (wall + catch fence on the bank)) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 39 | tyres | right | 2515-2592 | declared: T8a, right (toward the 2020 bypass) (c20_s0165 / c20_s0220 dark tyre stack 10-18 m right (95 % picked, rms 0.59 m); onboard 1:24) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 40 | concrete | left | 3705-3964 | declared: T11 exit to T12, left (pit-road side) (c20_s1320..s1540 bright wall at the left edge from the hairpin exit (100 % picked, rms 0.14 m); onboard 2:06-2:11 white wall left) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 41 | concrete | right | 77-1669 | declared: drag strip, track (SW) side, past T1 to the Carousel exit (c20_s1870 / c20_s1815 / c20_s0550 / c20_s3355: the bright wall along the drag strip SW edge (wall_measure along the paved part edge, 100 % picked, rms 0.22 m); Street View l9CetikWiRZTe2ONpwxrQQ; onboard 2:20) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 42 | concrete | right | 4097-0 (wraps) | declared: drag strip, infield (NE) side (c20_s0495..s1760: the bright wall along the drag strip NE edge (530 m, 100 % picked, rms 0.14 m); dropped where the course runs on the drag strip (Carousel exit)) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 43 | concrete | left | 3555-3638 | declared: T11 entry, left: wall between the track and the pit-in lane (c20_s1210 / c20_s1265 bright line 10.8 m left (93 % picked, rms 0.05 m); onboard 1:59 red / white painted concrete on the left) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 44 | tyres | left | 3638-3724 | declared: T11 hairpin, left tyre wall (c20_s1265 / c20_s1320 white tyre band on the outside of the hairpin (69 % picked, rms 0.35 m); onboard 2:04 white tyre stacks left) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 45 | tyres | right | 600-780 | declared: T3, right: low tyre-faced wall far out (c20_s2365..s2475 dark line 34-36 m right (100 % picked, rms 0.70 m); Street View exOejoRD5-jF1wceBnhfjg) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 46 | concrete + 3.0 m fence | left | 735-876 | declared: T4 approach, left: wall and catch fence below the T3a-T4 stands (c20_s2475..s2640 dark wall line 17-23 m left (97 % picked, rms 0.64 m); Street View nA1oaDXwADSI7x-Pa-j4Ow (wall + ~3 m catch fence left); onboard 0:28-0:32) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 47 | tyres | right | 828-962 | declared: T4, right: tyre line beyond the runoff (c20_s2640 / c20_s2695 dark tyre line 20-30 m right (79 % picked, rms 0.32 m)) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 48 | concrete + 3.0 m fence | left | 2780-2990 | declared: back straight, left: wall and catch fence at the foot of the stands (c20_o0440..o0550 dark line ~25 m left at the foot of the stands (100 % picked, rms 1.06 m: the weakest measurement); onboard 1:33-1:36 light-blue wall with catch fence left) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 49 | tyres | left | 2692-2745 | declared: back straight start, left tyre line (c20_s0330 / c20_s0385 dark tyre line ~21 m left (78 % picked, rms 0.72 m)) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 50 | concrete | left | 3165-3470 | declared: T10 to T11, left wall with the ad boards (c20_s0825..s1100 dark wall line 10-22 m left (96 % picked, rms 0.76 m); Street View jrXpHaDfJT2APw6zcyBKRA (ad boards); onboard 1:46-1:57 (Sunbelt, Toyota, zMAX boards on the wall)) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 51 | concrete + 3.0 m fence | right | 3220-3420 | declared: T10 to T11, right wall and catch fence (c20_s0880..s1045 bright line ~18 m right (55 % picked, rms 0.60 m, gaps bridged); onboard 1:43-1:52 concrete wall with catch fence on the right) | wall_measure.py, every 0.5 m, median 9 + Gaussian 3 m |
| 52 | fence + 1.8 m fence | left | 2261-2274 | terrace T7a hill top fence (OSM 1414701937; Street View J6fsnW4hj4xCjQLzrgRGzA (terraces, fence and light masts on top); onboard 1:14) | top row of the terrace + 0.45 m |
| 53 | fence + 1.8 m fence | left | 812-836 | terrace T3a-T4 top fence (OSM 1414701938; Street View nA1oaDXwADSI7x-Pa-j4Ow (~20 concrete rows); onboard 0:28-0:32) | top row of the terrace + 0.45 m |
| 54 | fence + 1.8 m fence | left | 487-512 | terrace above T2 top fence (OSM 1414701939; Street View H9xspk4q_OoFIjVDhaMzDA; onboard 0:15-0:16 (fence and light poles on top)) | top row of the terrace + 0.45 m |
| 55 | fence + 1.8 m fence | left | 2735-2765 | terrace back straight / 9a top fence (OSM 1414701936; Street View xkSrqJ5RaN9WFLncaiqaug; onboard 1:33-1:36) | top row of the terrace + 0.45 m |
| 56 | grandstand terrace | left | near 2261-2291 | OSM 1414701937; Street View J6fsnW4hj4xCjQLzrgRGzA (terraces, fence and light masts on top); onboard 1:14 | OSM footprint; 65 rows of 0.9 m on the DEM |
| 57 | grandstand terrace | left | near 812-995 | OSM 1414701938; Street View nA1oaDXwADSI7x-Pa-j4Ow (~20 concrete rows); onboard 0:28-0:32 | OSM footprint; 59 rows of 0.9 m on the DEM |
| 58 | grandstand terrace | left | near 417-487 | OSM 1414701939; Street View H9xspk4q_OoFIjVDhaMzDA; onboard 0:15-0:16 (fence and light poles on top) | OSM footprint; 89 rows of 0.9 m on the DEM |
| 59 | grandstand terrace | left | near 2735-3146 | OSM 1414701936; Street View xkSrqJ5RaN9WFLncaiqaug; onboard 1:33-1:36 | OSM footprint; 74 rows of 0.9 m on the DEM |
| 60 | marshal post T6 hilltop | right | 1395 (16 m out) | c20_s3135: a ~3 x 3 m platform with a box behind the right wall at the crest before the Carousel; Street View GMaTaipEd9Hm7fMNE26aGQ (Jul 2011): white box and tyre stack there (owner: "the one at the top of the hill just before T6") | centre measured on the capture |
| 61 | marshal post T4 | right | 970 (21 m out) | c20_s2695: a raised hut on a platform 27 m right of the T4 approach (long shadow); onboard 0:33 white elevated post with roof on the right; Street View 3a panorama (Jul 2011) shows it ahead right | centre measured on the capture |
| 62 | marshal post T7 | left | 2152 (10 m out) | c20_s3905: a post at the end of the left wall at T7; onboard 1:11 raised white post with roof ahead | centre measured on the capture |
| 63 | cone line | - | 2800-2804 | closed road 2020 fast bypass (8a to T10) mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 64 | cone line | - | 3087-3090 | closed road 2020 fast bypass (8a to T10) mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 65 | cone line | - | 995-1001 | closed road the Chute (NASCAR short course, T4 to T7) mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 66 | cone line | - | 2159-2166 | closed road the Chute (NASCAR short course, T4 to T7) mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 67 | cone line | - | 3952-3954 | closed road drag strip mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 68 | cone line | - | 1680-1688 | closed road drag strip mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 69 | cone line | - | 3498-3504 | closed road T11a shortcut mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 70 | cone line | - | 3912-3915 | closed road T11a shortcut mouth (OSM closed road way; mouth where the paved part meets the edge) | closed_roads rule at each OSM mouth |
| 71 | pit-exit cone line | left | 100.8-240.5 | c20_s1815 / c20_s1870 painted blend line from the pit-wall nose to the merge; pit lane OSM 230287120 | the pit lane track-facing edge where it merges |
| 72 | paved zone (closed_road) | - | 2802-3089 | OSM closed road: 2020 fast bypass (8a to T10) | NAIP asphalt width, clipped at walls |
| 73 | paved zone (closed_road) | - | 998-2154 | OSM closed road: the Chute (NASCAR short course, T4 to T7) | NAIP asphalt width, clipped at walls |
| 74 | paved zone (closed_road) | - | 2154-2163 | OSM closed road: the Chute (NASCAR short course, T4 to T7) | NAIP asphalt width, clipped at walls |
| 75 | paved zone (closed_road) | - | 3953-1684 | OSM closed road: drag strip | NAIP asphalt width, clipped at walls |
| 76 | paved zone (runoff) | - | 2244-2343 | OSM closed road: T7 inside runoff | NAIP asphalt width, clipped at walls |
| 77 | paved zone (closed_road) | - | 3501-3914 | OSM closed road: T11a shortcut | NAIP asphalt width, clipped at walls |
| 78 | paved zone (closed_road) | - | 2211-2319 | OSM closed road: PWC lower hairpin | NAIP asphalt width, clipped at walls |

## The survey walk: every surveyed spot, placed / not placed

| spot | feature | placed? | evidence / why not |
|---|---|---|---|
| S/F, 5MY4xR9O7etAXEHnZCVnGQ | concrete walls both sides, no fence | placed (rows: pit straight walls) | c20_s1595..s1870; onboard 2:16-2:20 light blue |
| S/F | timing tower, light masts right | not placed (masts) | the tower is an OSM building; masts not measured on the captures this round |
| T1 approach, l9CetikWiRZTe2ONpwxrQQ | right wall along the drag strip | placed (drag strip SW wall, continues past the runoff) | c20_s1870 / s1815; onboard 2:20 |
| T1 | "Turn 1" painted on the road | not placed | no painted text unless legible in a 2026 reference (skill rule) |
| T1 exit runoff (owner_4) | barrier to the drag strip | placed | drag strip SW wall, 100 % picked; containment gate: no escape at s 0-112 |
| T1 exit right | broken red/white kerb (4 runs) | placed | kerb_detect on c20_s1870 / s1925 |
| pit exit merge (owner_2) | open merge, cone line | placed (wall ends at its nose, cones from 101 to 241) | c20_s1815 / s1870 / s1925; pit-connectivity gate passes |
| T2 approach, H9xspk4q_OoFIjVDhaMzDA | kerb outside on entry (owner_3) | placed (left 330-372) | capstrip blocks on c20_s2090 / s2035; onboard 0:10 |
| T2 | apex kerb right | placed | c20_s2145 |
| T2 | tyre / armco line far left | not placed | not resolvable on the 2026 captures this round (open dirt) |
| T2 | hillside stands above T2 | placed (terrace, 89 rows) | OSM 1414701939; onboard 0:15 |
| T3, exOejoRD5-jF1wceBnhfjg | low tyre-faced wall far right | placed (tyres 34-36 m right) | c20_s2365..s2475 |
| T3 | apex kerb left, kerb right on approach | placed | c20_s2420 / s2475, c20_s2365 |
| 3a (Street View "Turn 3a", Jul 2011, viewpoint 38.16261,-122.46182) | kerb | placed RIGHT ONLY (760-814) | c20_s2530 (detector 781-814); the left side shows no block pattern on c20_s2475 / s2530 and the panorama shows a kerb on the right only |
| T4 approach, nA1oaDXwADSI7x-Pa-j4Ow | left wall + catch fence below the stands | placed (concrete + 3 m fence) | c20_s2475..s2640 |
| T4 | grandstand terraces left | placed (59 rows) | OSM 1414701938 |
| T4 | corner station right | placed (marshal T4) | c20_s2695 hut with long shadow; onboard 0:33; 3a panorama |
| T4 | kerbs: outside on entry, apex, outside on exit | placed | c20_s2585..s2860 |
| T5, zCwjltSjI02eDZGZbVyrMg | left low dark wall (tyres) | not placed | the 2026 onboard 0:40 shows a tyre line far left, not resolved on the captures this round |
| T5 -> T6 crest | right concrete wall | placed | c20_s2860..s3080; onboard 0:43-0:48.5 (built after the 2011 Street View) |
| T6 hilltop (owner), GMaTaipEd9Hm7fMNE26aGQ | corner station | placed (platform) | c20_s3135 platform + box; panorama at heading 215 (not 60): white box and tyre stack right of the track |
| Carousel, ma3jBYjtYGtNBlTLjNz1LQ | far right armco, fence far left | not placed | not resolved on the captures this round |
| Carousel | apex kerb left, exit kerb right | placed | c20_s3355 / s3410, c20_s3465 / s3520 |
| T6 -> T7 (owner) | left wall all along | placed (446 m) | c20_s3465..s3850; onboard 0:58-1:12 |
| T7 approach, gd1SNdksCq5QZtwlsrzR7g | tyre walls left | placed | c20_s3850 / s3905 dark stack |
| T7 / 7a, J6fsnW4hj4xCjQLzrgRGzA | kerbs on the islands only, left side open | placed (islands right, 7a exit left); T7 left NOT placed | owner_9; c20_s3905..s4070 |
| T7 | corner station | placed (marshal T7) | c20_s3905; onboard 1:11 |
| T7 | paved runoff inside | placed (allowed runoff, no cones) | OSM 1494191150, owner |
| T7a hill | terraces, fence, light masts | terraces + top fence placed; masts not placed | OSM 1414701937 |
| T8 / 8a, xXQqyp9Q9sWv9ZLN2ORYsA | left wall + fence on the bank | placed (tyres at 8a, wall + 3 m fence at T9) | c20_s0110..s0275 |
| T8a | right tyre stack toward the bypass | placed | c20_s0165 / s0220 |
| T8, 8a, T9 | kerbs | placed (T8 apex, 8a apex + exit, T9 apex + exit) | detector on c20_s0055..s0385 |
| back straight / 9a, xkSrqJ5RaN9WFLncaiqaug; Gas0S2x3OzWj_AinwcVtAg (spectator walk, Jul 2011) | left wall + catch fence, stands | placed (wall + 3 m fence, terrace 74 rows) | c20_o0440..o0550 (weakest measurement, rms 1.06 m); Gas0S2x3OzWj_AinwcVtAg shows the wall, fence and terraces |
| back straight | right concrete wall | not placed | the 2026 captures show open dirt paddock to the bypass on the right (allowed runoff); the 2011 wall is not there |
| 9a chicane | kerbs right then left | placed | c20_o0660, c20_o0715 |
| 9a | tyre stack (onboard 1:40-1:42) | not placed | not resolved on the captures |
| T10 | apex kerb right, exit kerb left | placed | c20_s0825..s1045 |
| T10 -> T11 | left wall with ad boards, right wall + fence | walls placed; ad boards not placed | c20_s0825..s1100; board texts not legible enough this round |
| T11 approach, jrXpHaDfJT2APw6zcyBKRA | left wall (red/white), no board in the pit-in lane | placed; the TURN 11 board is gone | c20_s1210 / s1265; sign gate passes |
| T11 hairpin | tyre wall outside, apex kerb | placed | c20_s1265..s1375 |
| T11 | NASCAR infield / 11a | allowed runoff (open paved ground) | Street View jrXpHaDfJT2APw6zcyBKRA |
| T12, QduY6QTXmw4JDevQVE_b-g | left wall (pit-road side), right wall (drag-strip side) | placed | c20_s1320..s1595 |
| T12 -> S/F | drag strip | walled off (both drag strip walls) | containment gate |


## Round 4 (20 Oct 2026, owner drive notes 11-31; registry rev e8a9fb17b1)

Gates: edge left/right, world continuity, profile, barrier gaps, containment (0 escapes), pit connectivity (both paths, 0
crossings) and sign placement (94 checked, 0 misplaced) all pass. Laguna: its package is unchanged against main and the
pipeline's Laguna scenery.json is byte-identical before / after the builder changes (every new rule is config-gated).
The four hillside terraces are byte-identical.

### Evidence-declared building overrides (new rule, `scenery.building_overrides`)
Only where a newer source than the lidar contradicts it; each use logged by the build; an entry that matches nothing
fails the stage. Used once: OSM 1019838438 dropped (row above). Height of a tent was not needed: the March 2026 onboard,
the newest source, shows no structure there, so the 2026 tent is treated as temporary (not estimated from its shadow).

### Bright / dark barrier bands (owner note 11 rule): every outside-of-corner stretch examined
Scan: `/tmp`-side script along both edges 2-45 m out on the clean captures (narrow continuous bands, 0.3-1.6 m wide),
then each candidate measured with wall_measure.py on a guide and checked on the onboard. Placed (all `declared_walls`,
src carries %-picked and rms):

| stretch | side, offset | kind, h / fence | capture measure | onboard / Street View |
|---|---|---|---|---|
| T2 entry before the footbridge (owner_27/28) | L 11-21 m | tyres 1.0 | dark, 90 %, rms 0.74 | owner_28 Pit Out; 0:12 |
| T2 approach far left (round-3 'not placed') | L 23-30 m | tyres 1.0 | dark, 92 %, rms 0.27 | H9xspk4q_OoFIjVDhaMzDA; 0:12 |
| T2 exit, foot of the T2 stands | L 18-31 m | concrete 1.0 + 3.0 fence | dark, 97 %, rms 0.48 | 0:12-0:15.5 wall + fence posts |
| T2 exit to T3, foot of the hill (owner_11) | R 19-34 m | tyres 1.0 | dark, 76 %, rms 0.41 | 0:12, 0:18 barrier line right |
| T1 exit to T2, grass bank | R 19-33 m | tyres 1.0 | dark, 84 %, rms 0.44 | owner_28 (tyre line on the bank) |
| T5 left (round-3 'not placed') | L 14-45 m | tyres 1.0 | dark, 96 %, rms 0.49 | zCwjltSjI02eDZGZbVyrMg; 0:41 tyre wall left |
| T5 right, before the T5-T6 wall | R ~15 m | concrete 1.0 | dark, 99 %, rms 0.51 | 0:39 |
| T5 to T6 crest, left, beyond the paddock | L 21-45 m | concrete 1.0 + 3.0 fence | dark, 100 %, rms 0.18 | 0:39-0:44 |
| Carousel right (round-3 'armco, not placed') | R 23-45 m | tyres 1.0 | dark, 96 %, rms 0.32 | ma3jBYjtYGtNBlTLjNz1LQ (armco 2011); 0:50 |
| Carousel left fence (round-3 'not placed') | L 17-43 m | fence 2.0 | dark, 100 %, rms 1.12 (weak) | ma3jBYjtYGtNBlTLjNz1LQ; 0:50 |
| T8 left, up the bank | L 25-46 m | tyres 1.0 | dark, 99 %, rms 0.20 | 1:18.5 |
| T9 right, along the bypass | R 10-30 m | concrete 1.0 | bright, 73 %, rms 0.38 | 1:27 |
| 9a right (round-3 '9a tyre stack, not placed') | R ~16 m | tyres 1.0 | dark, 100 %, rms 0.53 | 1:42 |
| T11 approach right, at the edge | R 6-9 m | tyres 1.0 + 3.5 fence | dark, 97 %, rms 0.53 | 1:53-1:55 |

Examined, not placed: T10 outside left before s 3172 (bright line s 3075-3168: 48 % picked, 3 broken runs, rejected;
the existing wall from s 3172 with its boards and 1.2 m height is what owner_14 shows missing in round 3, see
r4_s3190_T10.jpg; whether the wall continues back to s 3100 needs a better capture); the bands at 30-45 m on the
back straight left (stand rows), T3a-T4 left (terrace rows), s 1700-2160 right (drag-strip lane lines and the Chute
edges) and s 3700-3960 left (pit-road paint): paint or stand rows, not barriers.

### Wall heights and fences (note 13): from the onboard against the hood line and Street View scale
Set with `h_src` on each entry: pit straight both sides 1.1 m, no fence; T6-T7 left 1.2 m with 2.0 m boards on posts;
T10-T11 left 1.2 m with a continuous row of 2.5 m boards; T10-T11 right 1.1 m + 3.5 m fence; T11 hairpin tyres + 3 m
fence; T11-T12 left 0.81 m (Jersey); pit-in outer walls 1.2 m; pit-in separation Jersey 0.81 m; pit-out paddock side
1.0 m + 2.0 m chain-link (owner_28, onboard 2:22.5). Not read, kept at 1.0 m: T7 tyres, T8a-T9 tyres, T9 wall + fence,
T8a right tyres, T3 tyres, T4 wall + fence and tyres, back straight wall + fence and tyres, drag-strip walls.

### Boards, pit-in, nose, cones (notes 15-16, 18, 3h)
`wall_boards` (plain colour panels, no logos, colours in onboard order): T10-T11 left (4 runs, 44 panels), both outer
pit-in walls (27 panels), T6-T7 left (20 panels on posts). Pit-in separation Jersey re-measured from its nose
(c20_s1210, 90 % picked, rms 0.15 m; round 3 had measured the OUTER wall and called it the separation wall, now renamed
'outer pit-in wall (garage side)'); yellow `impact` block (1 x 2 x 1 m) at its nose; cone line on the double white
line s 3525-3586; outer pit-in / pit-road walls round the hairpin outside (O2, Q: 71 % / 53 % picked; owner_18).
`pit_lane_clip_walls`: the lane polygon stops at its walls (182 edge points clipped). T11 outside tyre wall: the
round-3 row, now with its 3 m fence. Free-standing yellow / blue tyre stacks (owner_21, 2011): NOT placed; the 2026
onboard 2:01-2:04 shows red / white concrete blocks at the apex instead and the captures show no round shadows on the
apron, so no `tyre_stack` object was added (no dynamic prop either).

### Closed roads (note 12, 17): material and painted edges
surface asphalt: 2020 bypass, the Chute, PWC hairpin, T7 inside runoff; concrete: drag strip, T11a apron. Painted
edges by paint.measure along each part's centre: bypass both sides 244 / 276 stations; Chute 53 / 183 and 35 / 96;
drag strip 385 / 534; PWC 32 / 59; T11a apron none found (no lines drawn). No closed-road kerbs found by kerb_detect.
Cone lines at the mouths unchanged. Material seam beside the pit-in (owner_17): NOT fixed this round; diagnosis
pending (the light mottled surface is the pit-lane ribbon showing the ortho's lighter pit-lane paving, see
r4_s3600_pitin_lane_mid.jpg).

### Paddock smear (note 19)
Diagnosis: NAIP ortho content (the 2026 captures c20_s1485..s1650 show the paddock full of parked trailers and cars;
the smears sit where they are), not z-fighting. `paved_areas`: OSM 28825490 (amenity=parking) drawn as plain asphalt.

### Pit exit and merge (notes 24-26)
Re-read on c20_s1815/s1870 and onboard 2:20.5-2:22.5: the track-side pit wall does end at its nose at s ~103; beyond
it the lane runs behind the painted blend line and its cones, bounded on the paddock side by the light-blue wall
(now with a 2.0 m chain-link fence). Seam: lane and road edges coincide in plan and height along the merge (gap 0,
z equal to 1 mm, s 109-234), so there is no step; the lighter strip is material. Not changed this round. Owner_25:
the garage at the pit-exit end has a red metal roof (onboard 2:20.5 shows it too), for the buildings round.

### Footbridge (note 29)
`bridge_stairs` (Sonoma on, Laguna off): abutment from the DEM to the deck at each span end (5.3 m and 6.2 m) and a
stair flight 7.1 m on along the OSM way. Pier positions from shadows not measured (span ends from OSM/lidar).

### Corner stations (note 30)
Scan for bright 2-5 m blobs within 25 m of either edge: 111 candidates; 16 inspected on capwin windows: 14 are parked
trailers / vehicles (the 2026 captures were taken during an event), c20_s1148 area (T5 left, 22 m out, ~3 x 3 m white
roof with shadow) unconfirmed (not visible on the onboard at 0:41-0:42), c20_s3208 area (white hut inside the PWC
infield) not a trackside post. No new marshal posts placed. The owner's frame (owner_29) could not be matched with
confidence; the white blotch is baked into the NAIP ground texture and is most likely a parked vehicle in NAIP.

### T1 kerbs (note 31)
Kind 'blocks' (low grey blocks, drawn only, no physics kerb): right s ~130-161 between striped runs 1 and 3, left s
89-134 from the pit-wall nose (kerb_detect grey runs). Striped run 2 (143.7-149.7) folded into the block line.

### What else drives the 'feel' (candidates for the next round, no work done)
Enclosure per stretch (open T2-T6 hillside vs walled T10-T12 bowl; onboard 0:10-0:50 vs 1:43-2:20); hillside colour
(2026 green spring grass in the onboard vs the dry NAIP tan); catch fences on the T8a-T9 bank (Street View
xXQqyp9Q9sWv9ZLN2ORYsA); paddock density (trailers, tents along T5, T8, the back straight on the captures); light
masts (onboard 1:43-2:20, not measured: positions need pole shadows on the captures).


## Round 5 (21 Oct 2026): the coverage gate's work list

Work list: `compare/sonoma/coverage.md` (the gate on the round-4 package). Every MISSING row of a must-cover kind now has
an object measured on the evidence or a logged correction of its inventory row; every object has a source.
Gate results on `public/tracks/sonoma` (live on HEAD 52b091a, then on this package):

| | wall | fence | kerb | tyre wall | bridge | tyre stack | stand | station | building | mast | cone line |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MISSING before | 31 | 25 | 2 | 7 | 0 | 10 | 15 | 6 | 4 | 29 | 10 |
| MISSING after | 0 | 0 | 0 | 0 | 0 | 7 | 9 | 1 | 0 (2 ASSIGNED) | 25 | 6 |
| UNSUPPORTED before | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 12 | 0 | 8 |
| UNSUPPORTED after | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

HEIGHT mismatches: 13 before, 1 after (see below). Pit-lane gate: FAIL (3 box-wall rows with no barrier) before, PASS
after. Edge, barrier-gap, containment, pit-connectivity and sign gates pass.

### Time-to-station map (inventory/source.json `corrections`)
- **S/F 0:02.2 -> 0:00.0.** The anchor rested on "0:00 shows the same place as 2:16"; frames t000 / t136 / t138 say
  otherwise: in t000 the main grandstand's end, the press box and the first light mast sit as in t138 (chequered line
  under the hood), while t136 shows the grandstand much nearer (about 60 m before the line). With 0:02.2 the car
  averaged 45 m/s to the footbridge.
- **Footbridge 0:08.7 -> 0:09.0**, inside its timed bracket (0:08.5-0:09.0): t008 shows the paddock-side Jersey end 5 m
  away and the deck 30-40 m ahead (deck 4.2 m above the camera, 50 px above the horizon). The bridge's s 295 is right:
  on c20_s1980 the span crosses the left edge at s 290-295.
- Residuals (leave-one-out, profile interpolation): footbridge 49.0 -> 12.8 m (S/F-to-bridge speed 45.4 -> 32.8 m/s),
  T2 -14.2 -> -10.0 m; the other anchors unchanged (T3 -1.8, T3a 5.7, T4 -18.6, T5 32.7, T6 -11.3, T7 -28.4, T7a 8.6,
  T8 9.6, T8a -7.3, T9 9.3, T9a 19.1, T10 -15.3, T11 -0.6, T12 7.0 m). Still uncertain: 0:04 maps to s 137 while the
  frame shows the pit-wall nose (s ~92-103) just ahead, and 1:56 maps to s 3492 while the frame shows the pit-in Jersey
  abeam (its nose is at s 3586 on c20_s1210): the map is +-40 m there; rows from those frames were checked on the frames.

### Placed (config `scenery`, each entry's `src` names the captures and the onboard time)
- **Walls / tyre walls / fences (19 new declared runs, plus the pit-box wall below):** T4 approach wall and fence on to the Chute (876-985); T6-crest
  Jersey on to the Carousel paved area (1358-1460, 96 % picked, rms 0.05 m); drag strip NW far wall (1885-2100); tyre
  line across the drag strip continuation at the T7 fork (onboard 1:04); T7 wall on to the T7 post (2104-2150);
  tyre line behind the cones at the Chute's T7 mouth (onboard 1:12); T7 runoff wall below the T7a stands; T7a terrace
  foot (tyre band then low wall); T7a-T8 bank-foot tyre line (2292-2409); T7a-T9 bank-top fence and T5 bank-top fence
  (on the lidar DEM crest, the onboard showing the fence on the bank top: the one placement not measured on a capture);
  T8-8a right wall to the PWC road (2350-2510); T9-back straight wall and fence (2684-2785, the round-4 'T10 outside'
  gap's twin); back straight-9a wall and fence (2986-3046); 9a-T10 right concrete wall and catch fence (3128-3222; the
  round-4 '9a tyre wall' now ends at 3132 where the tyre band ends); **T10 entry board wall (3118-3168: the round-4
  leftover 'T10 outside wall before s 3172')**; tyre bundles at the foot of the T10-T11 boarded wall (3395-3468); drag
  strip catch fence near the line (4040-110); pit-out paddock wall extended to its Jersey end (207 -> 265).
- **Heights from the inventory (HEIGHTS.md):** pit-in outer walls 1.2 -> 2.7 m under 2.5 m boards = 5.2 m (door-ref,
  Street View 5.22 m); T10-entry boards to 3.2 m; boards on the far drag-strip wall at T12 / the front straight (2.5 m);
  fences: pit-out chain-link 3 -> 2 m, T9 left 4 -> 3 m, T11 hairpin 4 -> 3 m, T5 left tyre wall gains its 2.5 m
  chain-link. The coverage gate now counts wall-mounted boards toward a wall's height (boards on posts do not).
- **Kerbs:** T2 exit outside, 451-520 (kerb_detect red runs on c20_s2200 / s2255; onboard 0:16).
- **Pit lane:** box wall (pit lane left, 3988-30, 27 m left of the centre: the double bright line between the boxes and
  the crew area, 100 % picked, rms 0.03-0.07 m); the six other declared pit-lane walls name the scenery walls they are.
  One road material: `pit_lane.lane.match_track_tone` maps the ortho inside the lane polygon (18 010 px) from its median
  luminance 140 to the track's 117 (k 0.5, paint above the 97th percentile kept): the lighter pit-in surface (note 17)
  and the light strip at the pit-out merge (notes 24-26) take the track's tone; the seam is the lane polygon's edge, the
  measured lane boundary (OSM lane clipped at the track edge and its walls). Lane and track already met with no gap and
  no step at the merge (round 4), so the merge is one surface in plan, height and now tone.
- **Masts:** 4 light masts (20 m, the brief's default: no reference of known height in the same capture for the shadow
  method) whose bases and NW shadows the captures show (c20_s3465 / s0330, c20_s3465, c20_s0165 / s0220, c20_s1650 /
  s1705); 9 light poles of 4 m (inventory 0:14, fence-post-ref) behind the T2-exit wall, 20 m apart as in the frames.
- **Stations:** T2 exit hut (c20_s2200, s ~445, 31 m left; onboard 0:12). The owner's note-30 frame (owner_29) still
  matches no station with confidence (a left-hand bank with trees, paddock buildings far right; not the T2 hut, whose
  bank carries terraces).
- **Tyre stacks:** two at the Carousel exit (c20_s3300 / s3355; 0:56), grey pair at the 9a apex (1:40), one in front of
  the T10-entry wall (1:44). Drawn only (landmark 'tyres', not in the collision world).
- **Cone lines:** delineators on the T7a island edge (1:14-1:16); cones in front of the T7-fork tyre line (1:04).

### Removed / re-kinded (no evidence or contradicted)
- OSM 380830042 (T3 right) re-kinded armco -> tyres (OSM note "tire barrier", dark band on c20_s2475 / s2530);
  OSM 380830043 (T4 right) dropped: the same line as the measured T4 tyre line.
- Closed-road mouth cones: kept only at the Chute's T4 mouth (onboard 0:34) and T7 mouth (onboard 1:12); the six at the
  bypass, drag-strip and T11a mouths removed (no cones in the onboard or on the captures; the drag strip's T12 mouth is
  behind the continuous drag-strip wall, onboard 2:14; the bypass and T11a mouths are open paving in the onboard, already
  'allowed' runoff). The containment gate still passes with no escapes; its 'drag strip at the Carousel exit' allowance
  now says why without the cones (open dead-end paving, walled along the front straight).
- Buildings: 10 removed with no 2026 source (`building_evidence` drop: 8 outside the captures and not in the onboard,
  one vehicle on the road on c20_s1045, one tree canopy on c20_s3850); the pit-exit building cites c20_s1870 and the
  T2 hilltop shade roof the onboard 0:14 (row added).

### Inventory corrections (attrs.correction in observations.jsonl / streetview.jsonl; rows added are marked `added`)
Three rows were added from frames the first pass under-read: 1:12 cones and a black tyre line across the Chute's T7
mouth; 0:14 the shade roof on the T2 hilltop. Corrections (43 rows):

| s now (m) | t | side | kind | row | change | why |
|---|---|---|---|---|---|---|
| 169 | 0:04.0 | left | building | pit-exit building, red roof, glazed front | ahead_m: none -> 35 | frame t004: the red-roofed pit-exit building is ahead-left (frame left edge); its footprint on c20_s1870 is at s ~160-190 |
| 172 | 0:02.0 | left | building | pit garages, red roof | ahead_m: none -> 95 | frame t002: the red-roofed building is far ahead-left beyond the pit wall: the pit-exit building at s ~170 (c20_s1870), not a garage abeam |
| 200 | 0:06.0 | ahead | fence | fence along the hill top | side: right -> ahead, out_m: none -> 140 | frame t006: the fence runs along the hill top below the tower, far right-ahead; the lidar DEM puts that crest 130-150 m beyond the right edge (s 150-280), past the gate reach for a fence (80 m): background, not trackside; kept as an ahead row without a distance (the station is not fixed for an object that far out) |
| 414 | 0:12.0 | left | fence | catch fence, curved-top posts | ahead_m: none -> 35 | frame t012: the fence stands along the foot of the terraces AHEAD-left (the row note says so); the T2-exit wall and fence begin at s ~414 on c20_s2145 / c20_s2200, about 35 m ahead |
| 443 | 0:12.0 | left | station | white marshal hut at the foot of the terraces | ahead_m: none -> 64 | frame t012: the hut is ahead-left at the fence line; c20_s2200 shows a ~2 m white hut at the foot of the terraces at s ~445, 31 m left of the centre |
| 479 | 0:12.0 | right | tyre_wall | dark tyre wall far right | ahead_m: none -> 100 | frame t012: the dark tyre wall is far AHEAD-right along the foot of the hill (T2 exit / T3 approach, as the note says); the barrier line there begins at s ~481 (owner_11 line, c20_s2200 / c20_s2255) |
| 735 | 0:22.0 | left | fence | catch fence, curved-top posts, far left | ahead_m: none -> 80 | frame t022: the catch fence is far ahead-left on the wall that begins at s ~735 (c20_s2475) |
| 735 | 0:22.0 | left | wall | white low wall / armco end ahead-left | ahead_m: none -> 80 | frame t022: the low wall and its fence stand far ahead-left at the T3 apex area (the note says ahead); the wall below the T3a-T4 stands begins at s ~735 (c20_s2475) |
| 740 | 0:24.0 | left | fence | catch fence, curved-top posts | ahead_m: none -> 30 | frame t024: as the wall row of this frame (fence on the wall that begins at s ~735) |
| 740 | 0:24.0 | left | wall | low dark concrete wall at the foot of the terraces | ahead_m: none -> 30 | frame t024: the wall with its fence begins ahead-left (frame left edge, 25-40 m ahead); the wall below the T3a-T4 stands begins at s ~735 (c20_s2475) |
| 812 | 0:26.0 | left | stand | concrete terraces (T3a-T4) | ahead_m: none -> 50 | frame t026: the T3a-T4 terraces are ahead-left; their footprint (OSM 1414701938) begins at s ~812 |
| 909 | 0:32.0 | right | tyre_wall | dark concrete / tyre-faced wall | kind: wall -> tyre_wall | the row itself reads "dark concrete / tyre-faced wall"; the 2026 captures c20_s2640 / c20_s2695 show a dark tyre line beyond the T4 runoff there (OSM note "Tire barrier"), the barrier of row 0:30 of the same kind |
| 969 | 0:32.0 | right | station | white elevated marshal post with roof, on a platform | ahead_m: none -> 60 | frame t032: the T4 post beyond the runoff is ~60 m ahead-right; it stands at s ~970 (c20_s2695) |
| 970 | 0:26.0 | right | station | white elevated marshal tower with roof | ahead_m: none -> 207 | frame t026: the tower stands far ahead-right on the bank; it is the T4 post (c20_s2695, s ~970), the only roofed tower on that bank |
| 970 | 0:30.0 | right | station | white marshal post with roof | ahead_m: none -> 115 | frame t030: the post is ahead-right at T4 (the note says so): the T4 post at s ~970 (c20_s2695) |
| 998 | 0:34.0 | left | cone_line | orange traffic cones across the Chute mouth | ahead_m: none -> 30 | frame t034: 3-5 cones ahead-left across the Chute mouth (the note says ahead); the mouth meets the track at s ~995-1001 |
| 1081 | 0:38.0 | left | fence | chain-link fence with posts | ahead_m: none -> 30 | frame t038: the fence behind the T5 tyre wall begins 20-30 m ahead-left |
| 1081 | 0:38.0 | left | tyre_wall | low dark wall / tyre line | ahead_m: none -> 30 | frame t038: the tyre line begins ahead-left (frame left edge, 20-30 m ahead); the T5 tyre wall begins at s ~1082 (c20_s2805) |
| 1084 | 0:36.0 | left | fence | chain-link fence | ahead_m: none -> 80 | frame t036: the chain-link fence stands behind the T5 tyre wall seen ~80 m ahead (s ~1082 on) |
| 1084 | 0:36.0 | left | tyre_wall | low black wall with ad boards (Save Mart, others) | ahead_m: none -> 80, kind: wall -> tyre_wall | frames t036 / t038 / t040: the black barrier with ad boards beyond the Chute is the T5 tyre wall (black tyre stacks at 0:38-0:40), seen ~80 m ahead from 0:36; it begins at s ~1082 (c20_s2805) |
| 1229 | 0:42.0 | left | fence | catch fence, curved-top posts | ahead_m: none -> 40 | frame t042: as the wall row of this frame |
| 1229 | 0:42.0 | left | wall | low dark wall far left | ahead_m: none -> 40 | frame t042: the low dark wall with its fence is far ahead-left (the T5-T6 crest wall, which begins at s ~1226 on the 2026 captures) |
| 1395 | 0:46.0 | right | station | marshal post with roof on the crest, vehicles parked | ahead_m: none -> 75 | frame t046: the post is ahead on the crest (vehicles beside it); it is the T6 hilltop post at s ~1395 (c20_s3135) |
| 1500 |  | right | tyre_wall | armco far right at the Carousel | kind: wall -> tyre_wall | Street View is July 2011; the row note itself records that the March 2026 onboard 0:52-0:54 shows a dark tyre line there (Carousel right tyre-faced barrier on the 2026 captures from s ~1514) |
| 1513 | 0:52.0 | ahead | fence | spectator fence on the bank top | side: right -> ahead, out_m: none -> 100 | frame t052: the spectator fence stands on the bank top beyond the Carousel; the lidar DEM puts that crest ~100 m beyond the right edge (s 1480-1560), past the gate reach for a fence (80 m): background, kept as an ahead row without a distance |
| 1592 | 0:54.0 | left | kerb |  | ahead_m: none -> 25 | frame t054: the Carousel apex kerb is ahead-left (the note says so); it begins at s ~1591 (kerb_detect, c20_s3355) |
| 1938 | 1:04.0 | right | cone_line | orange cones | ahead_m: none -> 50 | frame t064: the cones stand in front of the tyre line across the drag strip continuation at the fork, ~40-60 m ahead |
| 1938 | 1:04.0 | right | tyre_wall | black tyre line | ahead_m: none -> 50 | frame t064: the black tyre line and cones lie across the drag strip continuation where the course forks left to T7, ~40-60 m ahead (base rows 12-20 px below the horizon) |
| 2237 | 1:14.0 | left | tyre_wall | black tyre wall line, recovery vehicles behind | ahead_m: none -> 35 | frame t074: the black tyre line with vehicles behind it is far ahead-left at the foot of the T7a terraces; the dark band there begins at s ~2234 (c20_s3960, vehicles parked in front) |
| 2262 | 1:14.0 | left | stand | concrete terraces | ahead_m: none -> 60 | frame t074: the T7a terraces are ahead-left; their footprint (OSM 1414701937) is at s ~2261-2291 |
| 2272 | 1:10.0 | ahead | stand | concrete terraces with fence on top | side: right -> ahead, ahead_m: none -> 160 | frame t070: as 1:08, the T7a terraces far ahead (s ~2261-2291, left of the track there) |
| 2272 | 1:12.0 | ahead | stand | concrete terraces with fence and light masts on top | side: right -> ahead, ahead_m: none -> 115 | frame t072: as 1:08, the T7a terraces ahead (s ~2261-2291, left of the track there) |
| 2273 | 1:08.0 | ahead | stand | concrete terraces on the T7a hill | side: right -> ahead, ahead_m: none -> 240 | frame t068: the T7a terraces are far ahead (the note says far right): they stand on the outside of the T7a exit, on the left of the track there (OSM 1414701937, s ~2261-2291) |
| 2354 | 1:18.0 | right | wall | light concrete wall with ad board | ahead_m: none -> 40 | frame t078: far right ahead: the T8 right wall between the track and the PWC road begins at s ~2350 (c20_s0000 / c20_s0055) |
| 2440 |  | left | tyre_wall | concrete wall with a catch fence on the bank | kind: wall -> tyre_wall | Street View is July 2011; the March 2026 onboard 1:20-1:24 (rows at 0:80-0:86) shows a dark low wall / tyre line at the foot of the bank there, not concrete (HEIGHTS.md rule: keep Street View only where the recent video shows the same structure) |
| 2517 | 1:24.0 | right | tyre_wall | black-covered tyre barrier / dark panel wall | ahead_m: none -> 20 | frame t084: the dark panel / tyre barrier is ahead-right; it begins at s ~2515 (c20_s0165) |
| 2591 | 1:26.0 | right | wall | light grey concrete wall | ahead_m: none -> 20 | frame t086: the light wall begins ~15-20 m ahead-right; the T9 right wall begins at s ~2591 (c20_s0220) |
| 2737 | 1:30.0 | left | stand | concrete terraces (back straight) | ahead_m: none -> 30 | frame t090: the back-straight terraces begin ahead-left; their footprint (OSM 1414701936) begins at s ~2735 |
| 3149 | 1:42.0 | right | wall | light concrete wall with catch fence | ahead_m: none -> 60 | frame t102: the light wall with its fence stands beyond the black tyre barrier, ahead-right; on c20_s0715 / c20_s0770 the dark tyre band ends at s ~3132 and the light wall runs on from there |
| 3952 | 2:12.0 | right | wall | wall with zMAX / Save Mart boards | ahead_m: none -> 40 | frame t132: the boarded wall is the far drag-strip wall, ~40 m ahead-right |
| 3965 | 2:10.0 | right | wall | wall with EchoPark boards | ahead_m: none -> 122 | frame t130: as t126, the boarded drag-strip wall at the T12 exit seen far ahead-right (boards from s ~3960) |
| 3965 | 2:08.0 | right | wall | wall with Las Vegas / O'Reilly boards | ahead_m: none -> 181 | frame t128: as t126, the boarded drag-strip wall at the T12 exit seen far ahead-right (boards from s ~3960) |
| 3966 | 2:06.0 | right | wall | wall with ad boards far right | ahead_m: none -> 229 | frame t126: the boarded wall is far ahead-right (vanishing point): the drag-strip walls at the T12 exit, whose boards begin at s ~3960 (c20_s1540); the NASCAR infield between is open paving (c20_s1375..s1540) |

### Assigned to the buildings round (the coverage gate's one marker; kind building only)

| kind | side | s (m) | what | source | outcome |
|---|---|---|---|---|---|
| building | right | 3258.9 | tan buildings beyond the fence (infield) | onboard:RAZip6S84CM@110.0 | assigned: buildings round |
| building | right | 3910.0 | two-storey control tower building beyond the drag strip | streetview:QduY6QTXmw4JDevQVE_b-g@338 | assigned: buildings round |

Also for the buildings round (not gate markers, kind stand / building already covered by an OSM block): the main
grandstand at the line (stand rows 0:00, 2:14, 2:16, Street View 4050; OSM 262082790, still one 9.3 m block), the
infield grandstand with suites at T10/T11 (stand rows 1:34-1:44 right), the pit garages, timing tower and paddock
buildings (rows 2:02-2:12 left, pit rows).

### Still MISSING (kinds that do not fail the gate) and why
- **Masts (25 rows):** positions not resolved on the captures (masts show only as thin shadows; along the front straight
  and the drag strip the shadows run parallel to the walls and lane lines, and the captures were taken during an event);
  placed only where base and shadow are clear.
- **Stands (9):** the main grandstand and the T10/T11 infield grandstand (buildings round, above); the Carousel bank
  spectator area (1:48, no footprint in OSM or on the captures).
- **Tyre stacks (7):** 0:10 brown blocks far right (confidence 0.4); the T6 hilltop stack (Street View 2011 only); 0:58
  a stack the captures do not place; the T11 apron blocks (2:00-2:04; not resolved on c20_s1265 / s1320).
- **Cone lines (6):** two single marker cones (1:36, 1:38), cones along the T7 runoff and the 7a island nose (1:16), pit-
  lane cones (2:12; pit furniture is schema only), the 2011 apron cone.
- **Station (1):** 1:56 'marshal standing at a door in the tall wall': a person at the pit-in wall door, no structure.

### HEIGHT mismatch left (advisory)
- wall left s 3492 (1:56, Jersey 0.9 m) against the 5.2 m pit-in outer wall: the Jersey's nose is at s 3586 on
  c20_s1210 and the 1:56 frame shows the Jersey abeam, so 1:56 maps ~90 m early (the time map's T10-T11 stretch; the car
  brakes for the hairpin). The row stands; the map needs a T11-approach anchor (the Jersey nose's passage) next round.

## Round 5 tables (generated: `npx tsx tools/track/gates/manifest_tables.ts public/tracks/sonoma tools/track/compare/sonoma/inventory.json <coverage config>`)

### Scenery objects of the checked kinds (160, from tools/track/out/sonoma_r3/work/scenery_tmp)

| # | kind | side | s (m) | out (m) | object | source |
|---|---|---|---|---|---|---|
| 1 | tyre_wall | right | 705-829 | 31-41 | barrier 0 (tyres) | osm:380830042 (T3 right, OSM note "tire barrier": c20_s2475 / c20_s2530 show the dark tyre band on this line, 37-47 m right of the centre (round 5)) |
| 2 | wall | left | 3953-92 (wraps) | 1-2 | barrier 1 (concrete) | declared: pit straight, pit-lane side, to its nose at T1 (c20_s1595..s1870 bright band 2.0 m beyond the left edge (19 Oct); nose on c20_s1815 (s ~103); onboard 2:16-2:20) |
| 3 | wall | left | 106-268 | 2-11 | barrier 2 (concrete + 1 m fence) | declared: pit-out lane, paddock side (c20_s1870 / c20_s1925, bright band along the lane outer side (wall_measure, 87 % picked, rms 0.30 m); onboard 2:23 / 0:06.5) |
| 4 | fence | left | 106-268 | 2-11 | barrier 2 (concrete + 1 m fence) catch fence | declared: pit-out lane, paddock side (c20_s1870 / c20_s1925, bright band along the lane outer side (wall_measure, 87 % picked, rms 0.30 m); onboard 2:23 / 0:06.5) |
| 5 | wall | right | 3919-77 (wraps) | 1-3 | barrier 3 (concrete) | declared: pit straight, drag-strip side (c20_s1595..s1870 bright band 2.3 m beyond the right edge (19 Oct); Street View 5MY4xR9O7etAXEHnZCVnGQ; onboard 2:17) |
| 6 | wall | left | 1659-2109 | 1-1 | barrier 4 (concrete) | declared: T6 to T7, left (Carousel exit along the drag strip and the T7 road) (c20_s3465..s3850 bright band at the asphalt end (wall_measure along the left edge, 83 % picked, rms 0.11 m, gaps bridged); onboard 0:58-1:12 light-blue wall, Toyota boards at 1:10) |
| 7 | tyre_wall | left | 2066-2145 | 3-9 | barrier 5 (tyres) | declared: T7 approach, left tyre wall (c20_s3850 / c20_s3905 dark tyre stack 4-10 m beyond the left edge (96 % picked, rms 0.35 m); Street View gd1SNdksCq5QZtwlsrzR7g) |
| 8 | wall | right | 1149-1363 | 3-7 | barrier 6 (concrete) | declared: T5 to the T6 crest, right (c20_s2860..s3080 light wall line 3-6 m beyond the right edge (76 % picked); onboard 0:43-0:48.5 concrete wall on the right (not in the Jul 2011 Street View GMaTaipEd9Hm7fMNE26aGQ: built since)) |
| 9 | tyre_wall | left | 2478-2585 | 13-19 | barrier 7 (tyres) | declared: T8a to T9, left (the bank) (c20_s0110 / c20_s0165 dark barrier ~20 m left (99 % picked, rms 0.34 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA) |
| 10 | wall | left | 2585-2690 | 11-14 | barrier 8 (concrete + 2 m fence) | declared: T9, left (the bank) (c20_s0220 / c20_s0275 bright wall ~19 m left (95 % picked, rms 0.27 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA (wall + catch fence on the bank)) |
| 11 | fence | left | 2585-2690 | 11-14 | barrier 8 (concrete + 2 m fence) catch fence | declared: T9, left (the bank) (c20_s0220 / c20_s0275 bright wall ~19 m left (95 % picked, rms 0.27 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA (wall + catch fence on the bank)) |
| 12 | tyre_wall | right | 2515-2592 | 6-12 | barrier 9 (tyres) | declared: T8a, right (toward the 2020 bypass) (c20_s0165 / c20_s0220 dark tyre stack 10-18 m right (95 % picked, rms 0.59 m); onboard 1:24) |
| 13 | wall | left | 3705-3964 | 1-3 | barrier 10 (concrete) | declared: T11 exit to T12, left (pit-road side) (c20_s1320..s1540 bright wall at the left edge from the hairpin exit (100 % picked, rms 0.14 m); onboard 2:06-2:11 white wall left) |
| 14 | wall | right | 77-1669 | 1-91 | barrier 11 (concrete) | declared: drag strip, track (SW) side, past T1 to the Carousel exit (c20_s1870 / c20_s1815 / c20_s0550 / c20_s3355: the bright wall along the drag strip SW edge (wall_measure along the paved part edge, 100 % picked, rms 0.22 m); Street View l9CetikWiRZTe2ONpwxrQQ; onboard 2:20) |
| 15 | wall | right | 2894-1688 (wraps) | 8-83 | barrier 12 (concrete) | declared: drag strip, infield (NE) side (c20_s0495..s1760: the bright wall along the drag strip NE edge (530 m, 100 % picked, rms 0.14 m); dropped where the course runs on the drag strip (Carousel exit)) |
| 16 | wall | left | 3555-3638 | 5-7 | barrier 13 (concrete) | declared: T11 entry, left: outer pit-in wall (garage side) (c20_s1210 / c20_s1265 bright line 10.8 m left (93 % picked, rms 0.05 m); onboard 1:59 red / white painted concrete on the left) |
| 17 | tyre_wall | left | 3638-3724 | 1-2 | barrier 14 (tyres + 2 m fence) | declared: T11 hairpin, left tyre wall (c20_s1265 / c20_s1320 white tyre band on the outside of the hairpin (69 % picked, rms 0.35 m); onboard 2:04 white tyre stacks left) |
| 18 | fence | left | 3638-3724 | 1-2 | barrier 14 (tyres + 2 m fence) catch fence | declared: T11 hairpin, left tyre wall (c20_s1265 / c20_s1320 white tyre band on the outside of the hairpin (69 % picked, rms 0.35 m); onboard 2:04 white tyre stacks left) |
| 19 | tyre_wall | right | 600-780 | 27-31 | barrier 15 (tyres) | declared: T3, right: low tyre-faced wall far out (c20_s2365..s2475 dark line 34-36 m right (100 % picked, rms 0.70 m); Street View exOejoRD5-jF1wceBnhfjg) |
| 20 | wall | left | 735-876 | 10-17 | barrier 16 (concrete + 3 m fence) | declared: T4 approach, left: wall and catch fence below the T3a-T4 stands (c20_s2475..s2640 dark wall line 17-23 m left (97 % picked, rms 0.64 m); Street View nA1oaDXwADSI7x-Pa-j4Ow (wall + ~3 m catch fence left); onboard 0:28-0:32) |
| 21 | fence | left | 735-876 | 10-17 | barrier 16 (concrete + 3 m fence) catch fence | declared: T4 approach, left: wall and catch fence below the T3a-T4 stands (c20_s2475..s2640 dark wall line 17-23 m left (97 % picked, rms 0.64 m); Street View nA1oaDXwADSI7x-Pa-j4Ow (wall + ~3 m catch fence left); onboard 0:28-0:32) |
| 22 | tyre_wall | right | 828-962 | 14-24 | barrier 17 (tyres) | declared: T4, right: tyre line beyond the runoff (c20_s2640 / c20_s2695 dark tyre line 20-30 m right (79 % picked, rms 0.32 m)) |
| 23 | wall | left | 2780-2990 | 15-21 | barrier 18 (concrete + 3 m fence) | declared: back straight, left: wall and catch fence at the foot of the stands (c20_o0440..o0550 dark line ~25 m left at the foot of the stands (100 % picked, rms 1.06 m: the weakest measurement); onboard 1:33-1:36 light-blue wall with catch fence left) |
| 24 | fence | left | 2780-2990 | 15-21 | barrier 18 (concrete + 3 m fence) catch fence | declared: back straight, left: wall and catch fence at the foot of the stands (c20_o0440..o0550 dark line ~25 m left at the foot of the stands (100 % picked, rms 1.06 m: the weakest measurement); onboard 1:33-1:36 light-blue wall with catch fence left) |
| 25 | tyre_wall | left | 2692-2745 | 14-16 | barrier 19 (tyres) | declared: back straight start, left tyre line (c20_s0330 / c20_s0385 dark tyre line ~21 m left (78 % picked, rms 0.72 m)) |
| 26 | wall | left | 3165-3470 | 2-15 | barrier 20 (concrete) | declared: T10 to T11, left wall with the ad boards (c20_s0825..s1100 dark wall line 10-22 m left (96 % picked, rms 0.76 m); Street View jrXpHaDfJT2APw6zcyBKRA (ad boards); onboard 1:46-1:57 (Sunbelt, Toyota, zMAX boards on the wall)) |
| 27 | wall | right | 3220-3420 | 10-12 | barrier 21 (concrete + 3.5 m fence) | declared: T10 to T11, right wall and catch fence (c20_s0880..s1045 bright line ~18 m right (55 % picked, rms 0.60 m, gaps bridged); onboard 1:43-1:52 concrete wall with catch fence on the right) |
| 28 | fence | right | 3220-3420 | 10-12 | barrier 21 (concrete + 3.5 m fence) catch fence | declared: T10 to T11, right wall and catch fence (c20_s0880..s1045 bright line ~18 m right (55 % picked, rms 0.60 m, gaps bridged); onboard 1:43-1:52 concrete wall with catch fence on the right) |
| 29 | tyre_wall | left | 320-412 | 16-23 | barrier 22 (tyres) | declared: T2 approach, far left: tyre line (2026 captures c20_s2090 / c20_s2145: wall_measure dark line, 92 % picked, rms 0.27 m; Street View H9xspk4q_OoFIjVDhaMzDA (tyre / armco line far left); onboard 0:12 low dark barrier far left) |
| 30 | wall | left | 414-552 | 11-26 | barrier 23 (concrete + 3 m fence) | declared: T2 exit, left: wall and catch fence at the foot of the T2 stands (2026 captures c20_s2145 / c20_s2200: wall_measure dark line, 97 % picked, rms 0.48 m; onboard 0:12-0:15.5 dark grey wall with catch-fence posts below the terraces) |
| 31 | fence | left | 414-552 | 11-26 | barrier 23 (concrete + 3 m fence) catch fence | declared: T2 exit, left: wall and catch fence at the foot of the T2 stands (2026 captures c20_s2145 / c20_s2200: wall_measure dark line, 97 % picked, rms 0.48 m; onboard 0:12-0:15.5 dark grey wall with catch-fence posts below the terraces) |
| 32 | tyre_wall | right | 481-592 | 17-26 | barrier 24 (tyres) | declared: T2 exit to T3, right: barrier line at the foot of the hill (owner_11) (2026 captures c20_s2255 / c20_s2310: wall_measure dark line, 76 % picked, rms 0.41 m; owner_11 (the light band in the sim ground); onboard 0:12 dark barrier line far right, 0:18 barrier line along the right toward T3; joins the T3 tyre wall at s 600) |
| 33 | wall | right | 1062-1150 | 9-11 | barrier 25 (concrete) | declared: T5, right: wall before the T5-T6 wall (2026 captures c20_s2805 / c20_s2860: wall_measure dark line, 99 % picked, rms 0.51 m; onboard 0:39 the light concrete wall on the right already runs before T5 (continues the T5-T6 wall)) |
| 34 | tyre_wall | left | 1082-1158 | 8-40 | barrier 26 (tyres + 1.5 m fence) | declared: T5, left: tyre wall (2026 captures c20_s2805 / c20_s2860: wall_measure dark line, 96 % picked, rms 0.49 m; Street View zCwjltSjI02eDZGZbVyrMg (left low dark wall, tyres); onboard 0:39 dark barrier far left) |
| 35 | fence | left | 1082-1158 | 8-40 | barrier 26 (tyres + 1.5 m fence) catch fence | declared: T5, left: tyre wall (2026 captures c20_s2805 / c20_s2860: wall_measure dark line, 96 % picked, rms 0.49 m; Street View zCwjltSjI02eDZGZbVyrMg (left low dark wall, tyres); onboard 0:39 dark barrier far left) |
| 36 | wall | left | 1226-1447 | 14-39 | barrier 27 (concrete + 3 m fence) | declared: T5 to the T6 crest, left: wall and catch fence beyond the paddock (2026 captures c20_s2970 / c20_s3080: wall_measure dark line, 100 % picked, rms 0.18 m; onboard 0:39-0:44 long low dark wall with catch fence far left) |
| 37 | fence | left | 1226-1447 | 14-39 | barrier 27 (concrete + 3 m fence) catch fence | declared: T5 to the T6 crest, left: wall and catch fence beyond the paddock (2026 captures c20_s2970 / c20_s3080: wall_measure dark line, 100 % picked, rms 0.18 m; onboard 0:39-0:44 long low dark wall with catch fence far left) |
| 38 | tyre_wall | right | 1514-1622 | 16-38 | barrier 28 (tyres) | declared: Carousel, right: tyre-faced barrier across the infield (2026 captures c20_s3245 / c20_s3300: wall_measure dark line, 96 % picked, rms 0.32 m; Street View ma3jBYjtYGtNBlTLjNz1LQ (far right barrier, armco in Jul 2011); onboard 0:50 low dark barrier across the infield (2026: tyre-faced)) |
| 39 | fence | left | 1470-1621 | 12-34 | barrier 29 (fence + 2 m fence) | declared: Carousel, left: trackside fence (2026 captures c20_s3190 / c20_s3300: wall_measure dark line, 100 % picked, rms 1.12 m; Street View ma3jBYjtYGtNBlTLjNz1LQ (trackside fence far left); onboard 0:50 fence posts far left) |
| 40 | tyre_wall | left | 2401-2482 | 21-38 | barrier 30 (tyres) | declared: T8, left: tyre line up the bank (to the T8a-T9 tyres) (2026 captures c20_s0000 / c20_s0055: wall_measure dark line, 99 % picked, rms 0.20 m; onboard 1:18.5 low dark line along the bank on the left; joins the T8a-T9 tyre wall) |
| 41 | wall | right | 2591-2628 | 4-6 | barrier 31 (concrete) | declared: T9, right: concrete wall along the 2020 bypass (part 1) (2026 captures c20_s0220 / c20_s0275: wall_measure bright line, 73 % picked, rms 0.38 m; onboard 1:27 light concrete wall on the right) |
| 42 | wall | right | 2637-2666 | 8-24 | barrier 32 (concrete) | declared: T9, right: concrete wall along the 2020 bypass (part 2) (2026 captures c20_s0220 / c20_s0275: wall_measure bright line, 73 % picked, rms 0.38 m; onboard 1:27 light concrete wall on the right) |
| 43 | tyre_wall | right | 3398-3455 | 1-1 | barrier 33 (tyres + 3.5 m fence) | declared: T11 approach, right: tyre wall and catch fence at the edge (2026 captures c20_s1045 / c20_s1100: wall_measure dark line, 97 % picked, rms 0.53 m; onboard 1:53-1:55 tyre stacks along the right edge with catch fence (an ambulance parked behind at 1:54.6)) |
| 44 | fence | right | 3398-3455 | 1-1 | barrier 33 (tyres + 3.5 m fence) catch fence | declared: T11 approach, right: tyre wall and catch fence at the edge (2026 captures c20_s1045 / c20_s1100: wall_measure dark line, 97 % picked, rms 0.53 m; onboard 1:53-1:55 tyre stacks along the right edge with catch fence (an ambulance parked behind at 1:54.6)) |
| 45 | tyre_wall | right | 3100-3132 | 9-11 | barrier 34 (tyres) | declared: 9a, right: tyre wall (2026 captures c20_s0715 / c20_s0770: wall_measure dark line, 100 % picked, rms 0.53 m; onboard 1:42 tyre wall ahead right before the T10 wall) |
| 46 | wall | left | 3485-3563 | 1-6 | barrier 35 (concrete) | declared: T11 approach, left: outer pit-in wall (from the split) (2026 captures c20_s1100 / c20_s1155: wall_measure bright line, 100 % picked, rms 0.30 m; Street View owner_15 (wall with ad boards along the pit-in lane, ~1 m wall); onboard 1:59 light-blue wall with ad boards behind the pit-in Jersey) |
| 47 | wall | left | 3587-3640 | 1-2 | barrier 36 (concrete) | declared: T11 entry, left: Jersey wall between the track and the pit-in lane (from its nose) (2026 captures c20_s1210 / c20_s1265: wall_measure bright line, 90 % picked, rms 0.15 m; owner_15 / owner_16 (wall between pit-in and track, nose with an impact barrier); onboard 1:59 red / white Jersey on the left; Jersey scale 0.81 m) |
| 48 | wall | left | 3625-3657 | 7-12 | barrier 37 (concrete) | declared: T11 hairpin, outside the pit road: outer wall (east) (2026 captures c20_s1265 / c20_s1320: wall_measure bright line, 71 % picked, rms 0.65 m; owner_18 (tall concrete wall on the outside of the pit-in lane); Street View jrXpHaDfJT2APw6zcyBKRA) |
| 49 | wall | left | 3667-3672 | 19-24 | barrier 38 (concrete) | declared: T11 hairpin, outside the pit road: outer wall (south) (part 1) (2026 captures c20_s1320: wall_measure dark line, 53 % picked, rms 0.51 m; owner_18 (tall concrete wall on the outside of the pit road behind the hairpin)) |
| 50 | wall | left | 3679-3704 | 18-37 | barrier 39 (concrete) | declared: T11 hairpin, outside the pit road: outer wall (south) (part 2) (2026 captures c20_s1320: wall_measure dark line, 53 % picked, rms 0.51 m; owner_18 (tall concrete wall on the outside of the pit road behind the hairpin)) |
| 51 | tyre_wall | left | 274-294 | 4-13 | barrier 40 (tyres) | declared: T2 entry, left: tyre wall before the footbridge (owner_27 / owner_28) (2026 captures c20_s1980 / c20_s2035: wall_measure dark line, 90 % picked, rms 0.74 m; owner_27 ("there is a tire wall missing here"); Street View owner_28 Pit Out (Jul 2011): tyre wall round the outside of T2 from before the footbridge; onboard 0:12 dark low barrier left) |
| 52 | tyre_wall | right | 224-306 | 10-24 | barrier 41 (tyres) | declared: T1 exit to T2, right: tyre line on the grass bank (owner_28) (part 1) (2026 captures c20_s1925 / c20_s1980: wall_measure dark line, 84 % picked, rms 0.44 m; Street View owner_28 Pit Out (tyre line on the grass bank to the right)) |
| 53 | tyre_wall | right | 318-340 | 25-28 | barrier 42 (tyres) | declared: T1 exit to T2, right: tyre line on the grass bank (owner_28) (part 2) (2026 captures c20_s1980 / c20_s2035: wall_measure dark line, 84 % picked, rms 0.44 m; Street View owner_28 Pit Out (tyre line on the grass bank to the right)) |
| 54 | wall | left | 872-985 | 10-12 | barrier 43 (concrete + 2.5 m fence) | declared: T4 approach, left: wall and catch fence on to the Chute (round 5) (c20_s2695 / c20_s2750: wall_measure bright, s 876-985 beyond the measured T4 approach wall, 56 % picked (three runs, gaps under 16 m bridged), rms 0.31 m; onboard 0:32 wall and fence abeam, 0:34 its end at the Chute; Street View nA1oaDXwADSI7x-Pa-j4Ow) |
| 55 | fence | left | 872-985 | 10-12 | barrier 43 (concrete + 2.5 m fence) catch fence | declared: T4 approach, left: wall and catch fence on to the Chute (round 5) (c20_s2695 / c20_s2750: wall_measure bright, s 876-985 beyond the measured T4 approach wall, 56 % picked (three runs, gaps under 16 m bridged), rms 0.31 m; onboard 0:32 wall and fence abeam, 0:34 its end at the Chute; Street View nA1oaDXwADSI7x-Pa-j4Ow) |
| 56 | wall | right | 1358-1460 | 1-4 | barrier 44 (concrete) | declared: T6 crest, right: Jersey on to the Carousel paved area (round 5) (c20_s3135 / c20_s3190: wall_measure bright 1.0 m beyond the right edge, s 1358-1460, 96 % picked, rms 0.05 m; onboard 0:48 Jersey abeam on the right, 0:50 its end where the paved area opens) |
| 57 | wall | right | 1885-2099 | 1-27 | barrier 45 (concrete) | declared: drag strip NW end: far wall beyond the fork (round 5) (c20_s3630 / c20_s3685 / c20_s3740: wall_measure bright along the drag strip NW end, three runs 54 % picked, rms 0.15 m (gaps of 32 and 69 m bridged: the onboard shows one continuous wall); onboard 1:04-1:06 light blue wall on the far side of the drag strip, right) |
| 58 | tyre_wall | right | 1934-1942 | 1-7 | barrier 46 (tyres) | declared: drag strip at the T7 fork: tyre line across the continuation (round 5) (onboard RAZip6S84CM 1:04: a black tyre line with cones across the drag strip continuation where the course forks left, ~40-60 m ahead; placed across the continuation at s ~1938 between the track edge and the measured far wall (c20_s3630; the 2026 captures, taken at another event, show the lanes open)) |
| 59 | wall | left | 2104-2150 | 1-2 | barrier 47 (concrete) | declared: T7 approach, left: wall on to the T7 post (round 5) (c20_s3850 / c20_s3905: wall_measure bright, s 2104-2150, 63 % picked, rms 0.80 m (parked vehicles); onboard 1:12 the light blue-grey wall runs to its end beside the T7 post) |
| 60 | tyre_wall | left | 2159-2165 | 1-8 | barrier 48 (tyres) | declared: the Chute's T7 mouth: tyre line behind the cones (round 5) (onboard RAZip6S84CM 1:12 (frame t072): two low black tyre lines with small orange cones across the paved Chute mouth ahead-left of T7, again far left at 1:14; placed 1.5 m behind the mouth cone line (the mouth from the OSM Chute way; c20_s3905 shows the mouth open at another event)) |
| 61 | wall | left | 2228-2232 | 6-56 | barrier 49 (concrete) | declared: T7, left: wall bounding the paved runoff below the T7a stands (round 5) (c20_s3960 / c20_s4015: wall_measure bright, 85 % picked, rms 0.57 m; Street View J6fsnW4hj4xCjQLzrgRGzA (concrete wall far left along the T7a stands)) |
| 62 | tyre_wall | left | 2234-2243 | 27-42 | barrier 50 (tyres) | declared: T7a, left: tyre line at the foot of the terraces (round 5) (c20_s3960 / c20_s4015: wall_measure dark, 100 % picked, rms 0.39 m: the first 21 m of the line at the foot of the T7a terraces is a black tyre band (vehicles parked in front of it); onboard 1:14 black tyre wall line far left with recovery vehicles behind) |
| 63 | wall | left | 2243-2262 | 18-27 | barrier 51 (concrete) | declared: T7a, left: low wall at the foot of the terraces (round 5) (c20_s3960 / c20_s4015: wall_measure dark (its shadow line), 100 % picked, rms 0.39 m, the light part of the line at the foot of the T7a terraces; onboard 1:16 low white wall at the foot of the terraces) |
| 64 | tyre_wall | left | 2292-2409 | 33-44 | barrier 52 (tyres) | declared: T7a to T8, left: tyre line at the foot of the bank (round 5) (c20_s0000 / c20_s4070: wall_measure dark, 100 % picked, rms 0.59 m, s 2292-2405 along the foot of the bank behind the paddock (joins the T8 tyre line); onboard 1:20-1:22 dark low wall / tyre line at the foot of the bank) |
| 65 | fence | left | 2290-2660 | 44-61 | barrier 53 (fence + 1.5 m fence) | declared: T7a to T9, left: fence on the bank top (round 5) (onboard RAZip6S84CM 1:18-1:26 (fence posts along the top of the bank on the left) at the bank crest from the lidar bare-earth DEM (crest = first point past the steepest rise where the slope falls under 12 %, 47-60 m beyond the edge, 100 % of stations; median 9 + Gaussian 3); Street View xXQqyp9Q9sWv9ZLN2ORYsA (catch fence on the bank)) |
| 66 | fence | right | 950-1200 | 24-48 | barrier 54 (fence + 2.5 m fence) | declared: T5, right: fence on the bank top (round 5) (onboard RAZip6S84CM 0:38-0:40 (fence along the top of the bank above the right wall) at the bank crest from the lidar bare-earth DEM (21-48 m beyond the edge; median 9 + Gaussian 3), s 1040-1200) |
| 67 | wall | right | 2348-2500 | 4-9 | barrier 55 (concrete) | declared: T8 to 8a, right: concrete wall to the PWC road (round 5) (c20_s0000 / c20_s0055 / c20_s0110: wall_measure bright, s 2350-2510, three runs 68-77 % picked, rms 0.78-0.84 m (gaps of 10 m bridged; trailers parked against it at another event); onboard 1:20-1:22 continuous light grey wall 6-10 m right) |
| 68 | wall | left | 2684-2785 | 12-15 | barrier 56 (concrete + 2.5 m fence) | declared: T9 to the back straight, left: wall and catch fence (round 5) (c20_s0330 / c20_s0385: wall_measure dark (the fence shadow band), s 2684-2785 between the T9 wall and the back-straight wall, 86 % picked, rms 0.79 m; onboard 1:30 continuous low wall with catch fence on the left) |
| 69 | fence | left | 2684-2785 | 12-15 | barrier 56 (concrete + 2.5 m fence) catch fence | declared: T9 to the back straight, left: wall and catch fence (round 5) (c20_s0330 / c20_s0385: wall_measure dark (the fence shadow band), s 2684-2785 between the T9 wall and the back-straight wall, 86 % picked, rms 0.79 m; onboard 1:30 continuous low wall with catch fence on the left) |
| 70 | wall | left | 2986-3046 | 11-21 | barrier 57 (concrete + 2.5 m fence) | declared: back straight to 9a, left: wall and catch fence (round 5) (c20_o0660 / c20_s0660: wall_measure bright, s 2986-3046, 79 % picked, rms 0.58 m; onboard 1:38 wall and catch fence abeam on the left, 1:40 with Sonoma Raceway boards) |
| 71 | fence | left | 2986-3046 | 11-21 | barrier 57 (concrete + 2.5 m fence) catch fence | declared: back straight to 9a, left: wall and catch fence (round 5) (c20_o0660 / c20_s0660: wall_measure bright, s 2986-3046, 79 % picked, rms 0.58 m; onboard 1:38 wall and catch fence abeam on the left, 1:40 with Sonoma Raceway boards) |
| 72 | wall | right | 3128-3222 | 9-13 | barrier 58 (concrete + 2.9 m fence) | declared: 9a to T10, right: concrete wall and catch fence (round 5) (c20_s0715 / c20_s0770: wall_measure bright, s 3128-3222 (where the 9a tyre band ends to the T10-T11 right wall), 91 % picked, rms 0.44 m; onboard 1:44 light concrete wall with catch fence on the right) |
| 73 | fence | right | 3128-3222 | 9-13 | barrier 58 (concrete + 2.9 m fence) catch fence | declared: 9a to T10, right: concrete wall and catch fence (round 5) (c20_s0715 / c20_s0770: wall_measure bright, s 3128-3222 (where the 9a tyre band ends to the T10-T11 right wall), 91 % picked, rms 0.44 m; onboard 1:44 light concrete wall with catch fence on the right) |
| 74 | wall | left | 3118-3169 | 20-29 | barrier 59 (concrete) | declared: T10 entry, left: board wall along the bypass edge (round 5) (c20_s0715 / c20_s0770: wall_measure bright along the bypass edge, s 3118-3168, 63 % picked, rms 0.75 m (round 4 rejected a line here at 48 %; this guide follows the bypass edge, which the onboard confirms); onboard 1:44 a SONOMA RACEWAY / Sunbelt board wall 15-20 m left with a tyre stack in front, joining the T10-T11 boarded wall) |
| 75 | tyre_wall | left | 3395-3468 | 2-6 | barrier 60 (tyres) | declared: T10 to T11, left: tyre bundles at the foot of the boarded wall (round 5) (c20_s0990 / c20_s1045: wall_measure dark in front of the boarded wall, s 3395-3468, 99 % picked, rms 0.59 m; onboard 1:54 tyre bundles along the foot of the EchoPark wall) |
| 76 | fence | right | 4042-109 (wraps) | 19-27 | barrier 61 (fence + 3 m fence) | declared: drag strip infield side: catch fence near the line (round 5) (onboard RAZip6S84CM 0:00, 0:02, 2:18 (chain-link catch fence on the far side of the drag strip, right) on the measured NE drag-strip wall (c20_s1595..s1760, the declared wall), s 4040-110) |
| 77 | wall | left | 3988-30 (wraps) | 18-19 | barrier 62 (concrete) | declared: pit lane, left: low white pit-box wall (round 5) (pit lane: inventory pit rows s 4010 / 4060 / 20: low white pit-box wall with box numbers (24of8fjjAug 4:48-4:56); measured on c20_s1595 / c20_s1650 / c20_s1705: the bright double line between the boxes and the crew area, 27 m left of the centre, wall_measure 100 % picked, rms 0.03-0.07 m) |
| 78 | fence | left | 2261-2274 | 67-74 | barrier 63 (fence + 1.8 m fence) | terrace T7a hill top fence (OSM 1414701937; Street View J6fsnW4hj4xCjQLzrgRGzA (terraces, fence and light masts on top); onboard 1:14) |
| 79 | fence | left | 812-836 | 44-47 | barrier 64 (fence + 1.8 m fence) | terrace T3a-T4 top fence (OSM 1414701938; Street View nA1oaDXwADSI7x-Pa-j4Ow (~20 concrete rows); onboard 0:28-0:32) |
| 80 | fence | left | 487-512 | 63-64 | barrier 65 (fence + 1.8 m fence) | terrace above T2 top fence (OSM 1414701939; Street View H9xspk4q_OoFIjVDhaMzDA; onboard 0:15-0:16 (fence and light poles on top)) |
| 81 | fence | left | 2735-2765 | 60-62 | barrier 66 (fence + 1.8 m fence) | terrace back straight / 9a top fence (OSM 1414701936; Street View xkSrqJ5RaN9WFLncaiqaug; onboard 1:33-1:36) |
| 82 | kerb | right | 116-130 | 0-0 | kerb 115.7-129.7 | T1 exit right, run 1 of the broken kerb: c20_s1870 (detector run 116.7-129.7, block pattern), feature note c20_s1925 |
| 83 | kerb | right | 130-162 | 0-0 | kerb 129.7-161.6 | T1 exit right, block line between the striped runs: c20_s1870 (kerb_detect grey run 143.7-149.7 and the dotted blocks from 130 to 161 between striped runs 1 and 3); owner_31 satellite |
| 84 | kerb | left | 89-134 | 0-0 | kerb 88.8-133.7 | T1 inside, block line from the pit-wall nose: c20_s1815 / c20_s1870 (kerb_detect grey run 88.8-133.7, offsets -0.5..+0.2 m); owner_31 satellite (dotted block line on the inside); onboard 2:22.5 |
| 85 | kerb | right | 161-179 | 0-0 | kerb 160.6-178.6 | T1 exit right, run 3: c20_s1870 / c20_s1925 (detector 161.6-178.6, red) |
| 86 | kerb | right | 203-220 | 0-0 | kerb 202.5-219.5 | T1 exit right, run 4: c20_s1925 (detector 203.5-219.5) |
| 87 | kerb | left | 330-372 | 0-0 | kerb 330.3-372.2 | T2 entry, outside (owner_3): c20_s2090 / c20_s2035 blocks on the left edge (capstrip s300); onboard RAZip6S84CM 0:10 red/white kerb left on entry |
| 88 | kerb | left | 451-520 | 0-0 | kerb 451-519.8 | T2 exit, outside (round 5): c20_s2200 / c20_s2255 (kerb_detect red runs 451.0-458.0 and 465.0-519.8, 91 % of the run, offsets -0.4..+1.0 m); onboard 0:16 long red/white kerb along the left after T2 |
| 89 | kerb | right | 398-451 | 0-0 | kerb 398.1-451 | T2 apex: c20_s2145 (detector 412.1-428.0, 436.0-451.0); onboard 0:13-0:14 red/white apex kerb right |
| 90 | kerb | right | 605-655 | 0-0 | kerb 604.6-655.5 | T3 approach, right: c20_s2365 (detector 610.6-655.5, red); onboard 0:20.6-0:21 kerb on the right |
| 91 | kerb | left | 690-745 | 0-0 | kerb 690.4-745.3 | T3 apex: c20_s2420 / c20_s2475 blocks on the left edge (capstrip s600); onboard 0:24 red/white kerb left |
| 92 | kerb | right | 760-814 | 0-0 | kerb 760.3-814.2 | T3a apex (right; no kerb on the left of 3a): c20_s2530 (detector 781.2-814.2) and blocks from 760 (capstrip s750) |
| 93 | kerb | left | 855-960 | 0-0 | kerb 855.1-959.8 | T4 entry, outside: c20_s2585..s2750 blocks on the left edge (capstrip s750/s900); onboard 0:30-0:32 red/white kerb left |
| 94 | kerb | right | 990-1030 | 0-0 | kerb 989.8-1029.7 | T4 apex: c20_s2750 (detector 995.8-1027.7, red); onboard 0:34-0:36 red/white apex kerb right |
| 95 | kerb | left | 1025-1095 | 0-0 | kerb 1024.7-1094.5 | T4 exit, outside: c20_s2750..s2860 blocks on the left edge (capstrip s900/s1050); onboard 0:38 red/white kerb left |
| 96 | kerb | right | 1150-1262 | 0-0 | kerb 1150.4-1262.2 | T5 apex and exit: c20_s2860..s2970 (detector 1154.4-1165.4, 1182.3-1261.2, red) |
| 97 | kerb | left | 1591-1646 | 0-0 | kerb 1591.4-1646.3 | Carousel (T6) apex: c20_s3355 / c20_s3410 (detector 1591.4-1646.3); onboard 0:55 red/white kerb left |
| 98 | kerb | right | 1721-1796 | 0-0 | kerb 1721.1-1796 | Carousel exit, right: c20_s3465 / c20_s3520 (detector 1721.1-1796.0, red); onboard 0:60 red/white kerb right |
| 99 | kerb | right | 2150-2202 | 0-0 | kerb 2150.2-2202.1 | T7 island (apex): c20_s3905 / c20_s3960 (detector 2172.1-2180.1, 2188.1-2201.1); satellite owner_9; onboard 1:12 red/white island kerb |
| 100 | kerb | right | 2208-2330 | 0-0 | kerb 2208-2329.8 | T7a island (O'Reilly): c20_s3960..s4070 (detector 2216.0-2223.0, 2324.8-2331.8; blocks along the island, capstrip s2250); onboard 1:16 red/white |
| 101 | kerb | left | 2300-2372 | 0-0 | kerb 2299.8-2371.7 | T7a exit, outside: c20_s4015 / c20_s4070 / c20_s0000 (detector 2299.8-2309.8, 2315.8-2371.7); satellite owner_9 outer kerb |
| 102 | kerb | left | 2410-2440 | 0-0 | kerb 2409.6-2440.5 | T8 apex: c20_s0055 (detector 2417.6-2440.5, red); onboard 1:18-1:20 red/white kerb left |
| 103 | kerb | right | 2440-2550 | 0-0 | kerb 2439.5-2550.3 | T8a apex: c20_s0055..s0165 (detector 2441.5-2447.5, 2479.4-2505.4, 2523.3-2537.3; blocks capstrip s2400); onboard 1:22-1:24 |
| 104 | kerb | left | 2520-2572 | 0-0 | kerb 2520.3-2572.2 | T8a exit, outside: c20_s0165 / c20_s0220 (detector 2542.3-2572.2); onboard 1:26 red/white kerb left |
| 105 | kerb | left | 2600-2645 | 0-0 | kerb 2600.2-2645.1 | T9 apex: c20_s0220 / c20_s0275 (detector 2600.2-2645.1, red); onboard 1:28 |
| 106 | kerb | right | 2692-2740 | 0-0 | kerb 2692-2739.8 | T9 exit, outside: c20_s0330 / c20_s0385 (detector 2692.0-2739.8, red) |
| 107 | kerb | right | 3020-3045 | 0-0 | kerb 3020.2-3045.2 | 9a chicane, right-hand part apex: c20_o0660 (detector 3021.2-3036.2, red); onboard 1:39 kerb right |
| 108 | kerb | left | 3060-3170 | 0-0 | kerb 3060.1-3169.9 | 9a chicane left-hand part apex and on to T10: c20_o0715 / c20_s0715 / c20_s0770 (detector 3060.1-3169.9); onboard 1:41 red/white kerb left |
| 109 | kerb | right | 3215-3292 | 0-0 | kerb 3214.8-3291.6 | T10 apex: c20_s0825..s0935 (detector 3219.8-3292.6, red); onboard 1:45 |
| 110 | kerb | left | 3338-3402 | 0-0 | kerb 3337.5-3402.4 | T10 exit, outside: c20_s0990 / c20_s1045 (detector 3338.5-3369.4, 3379.4-3402.4) |
| 111 | kerb | right | 3615-3745 | 0-0 | kerb 3614.9-3744.6 | T11 hairpin apex: c20_s1265..s1375 (detector 3628.8-3673.7, 3700.7-3730.6; blocks capstrip s3600); onboard 2:01-2:04 red/white |
| 112 | station | right | 1395-1395 | 10-10 | marshal 'T6 hilltop' | c20_s3135: a ~3 x 3 m platform with a box behind the right wall at the crest before the Carousel; Street View GMaTaipEd9Hm7fMNE26aGQ (Jul 2011): white box and tyre stack there (owner: "the one at the top of the hill just before T6") |
| 113 | station | right | 970-970 | 16-16 | marshal 'T4' | c20_s2695: a raised hut on a platform 27 m right of the T4 approach (long shadow); onboard 0:33 white elevated post with roof on the right; Street View 3a panorama (Jul 2011) shows it ahead right |
| 114 | station | left | 445-445 | 25-25 | marshal 'T2 exit' | c20_s2200: a ~2 m white hut at the foot of the T2 terraces, 31 m left of the centre at s ~445 (round 5); onboard 0:12 white marshal hut ahead-left at the fence line |
| 115 | station | left | 2152-2152 | 4-4 | marshal 'T7' | c20_s3905: a post at the end of the left wall at T7; onboard 1:11 raised white post with roof ahead |
| 116 | tyre_stack | right | 1629-1629 | 35-35 | tyres '' | c20_s3300 / c20_s3355: two dark stacks on the runoff right of the Carousel exit; onboard 0:56 single black tyre stacks on the runoff (0.8 m, tyre-ref) |
| 117 | tyre_stack | right | 1626-1626 | 39-39 | tyres '' | c20_s3300 / c20_s3355: the second stack; onboard 0:56 |
| 118 | tyre_stack | right | 3048-3048 | 1-1 | tyres '' | onboard 1:40: a stack of 2 grey tyres just past the 9a right apex kerb (kerb end s ~3045 on c20_o0660), 1.5 m outside the edge |
| 119 | tyre_stack | left | 3125-3125 | 10-10 | tyres '' | onboard 1:44: a black tyre stack in front of the T10-entry board wall at its start (s ~3125; wall on c20_s0715 / c20_s0770) |
| 120 | mast | right | 1732-1732 | 24-24 | mast '' | c20_s3465 / c20_s0330: mast base with its NW shadow between the drag strip and the infield (seen on both); onboard 1:00 light masts on the right |
| 121 | mast | right | 2635-2635 | 20-20 | mast '' | c20_s3465: mast base with its shadow beyond the drag strip, right of the Carousel exit; onboard 1:00-1:02 light masts on the right |
| 122 | mast | right | 2575-2575 | 13-13 | mast '' | c20_s0165 / c20_s0220: mast base on a black block base in the island between the drag strip and the T8 road; onboard 1:18 light mast on a black block base |
| 123 | mast | right | 4056-4056 | 50-50 | mast '' | c20_s1650 / c20_s1705: mast base with its NW shadow in the paddock beyond the drag strip at the line; Street View 5MY4xR9O7etAXEHnZCVnGQ (light masts both sides of the straight) |
| 124 | mast | left | 419-419 | 26-26 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 125 | mast | left | 431-431 | 25-25 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 126 | mast | left | 443-443 | 23-23 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 127 | mast | left | 456-456 | 22-22 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 128 | mast | left | 471-471 | 21-21 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 129 | mast | left | 488-488 | 22-22 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 130 | mast | left | 506-506 | 20-20 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 131 | mast | left | 525-525 | 19-19 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 132 | mast | left | 543-543 | 14-14 | mast '' | onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames) |
| 133 | stand | left | 2261-2291 | 46-73 | terrace T7a hill | OSM 1414701937; Street View J6fsnW4hj4xCjQLzrgRGzA (terraces, fence and light masts on top); onboard 1:14 |
| 134 | stand | left | 812-995 | 25-47 | terrace T3a-T4 | OSM 1414701938; Street View nA1oaDXwADSI7x-Pa-j4Ow (~20 concrete rows); onboard 0:28-0:32 |
| 135 | stand | left | 417-512 | 30-63 | terrace above T2 | OSM 1414701939; Street View H9xspk4q_OoFIjVDhaMzDA; onboard 0:15-0:16 (fence and light poles on top) |
| 136 | stand | left | 2735-3146 | 23-61 | terrace back straight / 9a | OSM 1414701936; Street View xkSrqJ5RaN9WFLncaiqaug; onboard 1:33-1:36 |
| 137 | building | left | 3991-38 (wraps) | 26-74 | building 0 'Sonoma Raceway' 9.3 m | osm |
| 138 | building | left | 3421-3658 | 20-129 | building 1 '' 4.5 m | osm |
| 139 | building | left | 3830-3908 | 29-42 | building 2 '' 6.2 m | osm |
| 140 | building | left | 3683-3692 | 177-213 | building 3 '' 5.2 m | osm |
| 141 | building | left | 3737-3791 | 105-122 | building 4 '' 6.7 m | osm |
| 142 | building | left | 3909-3963 | 18-42 | building 5 '' 8.7 m | osm |
| 143 | building | left | 3713-3733 | 62-113 | building 6 '' 6.8 m | osm |
| 144 | building | left | 3745-3821 | 29-42 | building 7 '' 6.3 m | osm |
| 145 | building | left | 3686-3690 | 54-87 | building 8 '' 6.4 m | osm |
| 146 | building | left | 3674-3674 | 188-196 | building 9 '' 2.5 m | osm |
| 147 | building | left | 3719-3728 | 32-41 | building 10 '' 6.5 m | osm |
| 148 | building | right | 3279-3314 | 36-53 | building 11 '' 3.2 m | osm |
| 149 | building | left | 409-414 | 78-98 | building 12 '' 3.2 m | osm (onboard 0:14 (frame t014): open shade roof on posts at the top of the T2 terraces (inventory row added in round 5)) |
| 150 | building | left | 3684-3689 | 86-99 | building 13 '' 4.5 m | osm |
| 151 | building | left | 157-191 | 16-49 | building 14 '' 6.6 m | osm (c20_s1870: the red-roofed metal pit-exit building (onboard 0:04 and 24of8fjjAug 5:00 red-roofed pit-exit building)) |
| 152 | building | left | 3478-3657 | 2-39 | building 15 '' 5.5 m | osm |
| 153 | building | left | 3662-3692 | 22-64 | building 16 '' 4.7 m | osm |
| 154 | bridge | both | 295-295 | 0-0 | bridge 1382620985 (foot) deck 20.9 | lidar |
| 155 | cone_line | left | 995-1001 | 0-5 | cone line 0 | closed road the Chute (NASCAR short course, T4 to T7) mouth (onboard 0:34: 3-5 orange cones across the Chute mouth ahead-left at T4 (inventory)) |
| 156 | cone_line | left | 2159-2166 | 0-6 | cone line 1 | closed road the Chute (NASCAR short course, T4 to T7) mouth (onboard 1:12: small orange cones in front of a black tyre line across the Chute mouth at T7 (inventory, added row)) |
| 157 | cone_line | right | 2196-2212 | 0-1 | cone line 2 | onboard 1:14-1:16 (round 5): orange delineator posts on the edge of the T7a island before its kerb (island on c20_s3960) |
| 158 | cone_line | right | 1932-1942 | 1-2 | cone line 3 | onboard 1:04 (round 5): orange cones in front of the tyre line across the drag strip continuation at the T7 fork |
| 159 | cone_line | left | 3525-3586 | 0-0 | cone line 4 | pit-in double white line, s 3525 to the nose at 3586 (c20_s1155 / c20_s1210; Street View owner_15 cones) |
| 160 | cone_line | left | 3966-240 (wraps) | 0-0 | cone line 5 | the pit lane's track-facing edge where it merges at its end (one-part pit lane) |

### Every inventory row and its outcome (423 rows)

| s (m) | t | side | kind | what | source | outcome |
|---|---|---|---|---|---|---|
| 0 | 0:00.0 | left | mast | light mast | onboard:RAZip6S84CM@0.0 | MISSING |
| 0 | 0:00.0 | left | stand | bleachers with suites deck | onboard:RAZip6S84CM@0.0 | MISSING |
| 0 | 0:00.0 | left | wall | concrete | onboard:RAZip6S84CM@0.0 | covered by barrier 1 (concrete); barrier 62 (concrete) |
| 0 | 0:00.0 | right | fence | chain-link catch fence | onboard:RAZip6S84CM@0.0 | covered by barrier 61 (fence + 3 m fence) |
| 0 | 0:00.0 | right | mast | light mast | onboard:RAZip6S84CM@0.0 | MISSING |
| 0 | 0:00.0 | right | paint | white edge line | onboard:RAZip6S84CM@0.0 | surroundings (not a checked kind) |
| 0 | 0:00.0 | right | wall | concrete | onboard:RAZip6S84CM@0.0 | covered by barrier 3 (concrete); barrier 12 (concrete) |
| 77 | 0:02.0 | left | wall | concrete | onboard:RAZip6S84CM@2.0 | covered by barrier 1 (concrete) |
| 77 | 0:02.0 | right | fence | chain-link catch fence | onboard:RAZip6S84CM@2.0 | covered by barrier 61 (fence + 3 m fence) |
| 77 | 0:02.0 | right | wall | concrete | onboard:RAZip6S84CM@2.0 | covered by barrier 3 (concrete); barrier 11 (concrete) |
| 134 | 0:04.0 | ahead | tower | Sonoma tower on the hill | onboard:RAZip6S84CM@4.0 | surroundings (not a checked kind) |
| 134 | 0:04.0 | left | boards | ad boards on the fence line | onboard:RAZip6S84CM@4.0 | surroundings (not a checked kind) |
| 134 | 0:04.0 | left | wall | concrete | onboard:RAZip6S84CM@4.0 | covered by barrier 2 (concrete + 1 m fence) |
| 134 | 0:04.0 | right | mast | light mast | onboard:RAZip6S84CM@4.0 | MISSING |
| 134 | 0:04.0 | right | runoff | paved, drag-strip junction | onboard:RAZip6S84CM@4.0 | surroundings (not a checked kind) |
| 169 | 0:04.0 | left | building | pit-exit building, red roof, glazed front | onboard:RAZip6S84CM@4.0 | covered by building 14 '' 6.6 m (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 172 | 0:02.0 | left | building | pit garages, red roof | onboard:RAZip6S84CM@2.0 | covered by building 14 '' 6.6 m (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 200 | 0:06.0 | ahead | bridge | footbridge with ad boards (Save Mart, GR, Sunoco, Las Vegas) | onboard:RAZip6S84CM@6.0 | skipped: 'ahead' without a distance |
| 200 | 0:06.0 | ahead | fence | fence along the hill top | onboard:RAZip6S84CM@6.0 | skipped: 'ahead' without a distance (corrected in scenery round 5 (21 Oct 2026): side was right, out_m was none) |
| 200 | 0:06.0 | left | cone_line | pit-exit cones, yellow/white, ~0.5 m | onboard:RAZip6S84CM@6.0 | covered by cone line 5 |
| 200 | 0:06.0 | left | fence | chain-link | onboard:RAZip6S84CM@6.0 | covered by barrier 2 (concrete + 1 m fence) catch fence |
| 200 | 0:06.0 | left | wall | concrete | onboard:RAZip6S84CM@6.0 | covered by barrier 2 (concrete + 1 m fence) |
| 200 | 0:06.0 | right | paint | white edge line | onboard:RAZip6S84CM@6.0 | surroundings (not a checked kind) |
| 200 | 0:06.0 | right | runoff | dry grass / dirt | onboard:RAZip6S84CM@6.0 | surroundings (not a checked kind) |
| 200 | 0:06.0 | right | wall | low dark wall / tyre line at the foot of the bank | onboard:RAZip6S84CM@6.0 | covered by barrier 11 (concrete) |
| 265 | 0:08.0 | left | paint | white edge line | onboard:RAZip6S84CM@8.0 | surroundings (not a checked kind) |
| 265 | 0:08.0 | left | tyre_wall | dark low wall / tyre wall round the outside of T2 | onboard:RAZip6S84CM@8.0 | covered by barrier 40 (tyres) |
| 265 | 0:08.0 | left | wall | concrete Jersey end | onboard:RAZip6S84CM@8.0 | covered by barrier 2 (concrete + 1 m fence) |
| 265 | 0:08.0 | right | tyre_wall | low dark barrier line beyond the grass bank | onboard:RAZip6S84CM@8.0 | covered by barrier 41 (tyres) |
| 285 | 0:08.0 | both | boards | ad boards on the bridge: Save Mart, Toyota GR x2, Sunoco, Las Vegas | onboard:RAZip6S84CM@8.0 | surroundings (not a checked kind) |
| 285 | 0:08.0 | both | bridge | truss footbridge on concrete piers both sides, ad-board fascia | onboard:RAZip6S84CM@8.0 | covered by bridge 1382620985 (foot) deck 20.9 |
| 323 | 0:10.0 | left | kerb | T2 entry outside kerb | onboard:RAZip6S84CM@10.0 | covered by kerb 330.3-372.2 |
| 323 | 0:10.0 | left | runoff | grass then dirt | onboard:RAZip6S84CM@10.0 | surroundings (not a checked kind) |
| 323 | 0:10.0 | right | paint | white edge line | onboard:RAZip6S84CM@10.0 | surroundings (not a checked kind) |
| 323 | 0:10.0 | right | runoff | grass | onboard:RAZip6S84CM@10.0 | surroundings (not a checked kind) |
| 323 | 0:10.0 | right | tyre_stack | brown block stacks far right (tyre bundles or hay bales) | onboard:RAZip6S84CM@10.0 | MISSING |
| 330 |  | left | tyre_wall | tyre / armco line far left at T2 | streetview:H9xspk4q_OoFIjVDhaMzDA@210 | covered by barrier 22 (tyres) |
| 379 | 0:12.0 | ahead | stand | concrete terraces up the hill above T2/T3 | onboard:RAZip6S84CM@12.0 | skipped: 'ahead' without a distance |
| 379 | 0:12.0 | left | paint | white edge line | onboard:RAZip6S84CM@12.0 | surroundings (not a checked kind) |
| 379 | 0:12.0 | right | paint | white edge line | onboard:RAZip6S84CM@12.0 | surroundings (not a checked kind) |
| 414 | 0:12.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@12.0 | covered by barrier 23 (concrete + 3 m fence) catch fence (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 420 | 0:14.0 | left | building | open shade roof on posts at the top of the T2 terraces, a tan block behind it | onboard:RAZip6S84CM@14.0 | covered by building 12 '' 3.2 m (row added in scenery round 5 (21 Oct 2026)) |
| 420 | 0:14.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@14.0 | covered by barrier 23 (concrete + 3 m fence) catch fence |
| 420 | 0:14.0 | left | mast | light poles inside the fence line | onboard:RAZip6S84CM@14.0 | covered by mast ''; mast '' |
| 420 | 0:14.0 | left | stand | concrete terraces, ~25 rows, stair aisles, shade roof on top | onboard:RAZip6S84CM@14.0 | covered by terrace above T2 |
| 420 | 0:14.0 | left | wall | low concrete wall at the foot of the terraces with a 'SONOMA TURN 2' style sign | onboard:RAZip6S84CM@14.0 | covered by barrier 23 (concrete + 3 m fence) |
| 420 | 0:14.0 | right | kerb | T2 apex/exit kerb right | onboard:RAZip6S84CM@14.0 | covered by kerb 398.1-451 |
| 420 | 0:14.0 | right | runoff | grass bank | onboard:RAZip6S84CM@14.0 | surroundings (not a checked kind) |
| 443 | 0:12.0 | left | station | white marshal hut at the foot of the terraces | onboard:RAZip6S84CM@12.0 | covered by marshal 'T2 exit' (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 463 | 0:16.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@16.0 | covered by barrier 23 (concrete + 3 m fence) catch fence |
| 463 | 0:16.0 | left | kerb | long kerb along the left after T2 (exit side) | onboard:RAZip6S84CM@16.0 | covered by kerb 451-519.8 |
| 463 | 0:16.0 | left | runoff | dirt strip then grass | onboard:RAZip6S84CM@16.0 | surroundings (not a checked kind) |
| 463 | 0:16.0 | left | stand | concrete terraces, stair rails, light poles | onboard:RAZip6S84CM@16.0 | covered by terrace above T2 |
| 463 | 0:16.0 | left | wall | low dark concrete wall at the foot of the terraces | onboard:RAZip6S84CM@16.0 | covered by barrier 23 (concrete + 3 m fence) |
| 463 | 0:16.0 | right | boards | row of large tan billboard backs / panels | onboard:RAZip6S84CM@16.0 | surroundings (not a checked kind) |
| 463 | 0:16.0 | right | paint | white edge line | onboard:RAZip6S84CM@16.0 | surroundings (not a checked kind) |
| 479 | 0:12.0 | right | tyre_wall | dark tyre wall far right | onboard:RAZip6S84CM@12.0 | covered by barrier 24 (tyres) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 516 | 0:18.0 | left | fence | fence along the hill top | onboard:RAZip6S84CM@18.0 | covered by barrier 23 (concrete + 3 m fence) catch fence; barrier 65 (fence + 1.8 m fence) |
| 516 | 0:18.0 | left | paint | white edge line | onboard:RAZip6S84CM@18.0 | surroundings (not a checked kind) |
| 516 | 0:18.0 | left | wall | low dark wall (tyre-faced or black concrete) at the foot of the bank | onboard:RAZip6S84CM@18.0 | covered by barrier 23 (concrete + 3 m fence) |
| 516 | 0:18.0 | right | boards | tan billboard panels in a row | onboard:RAZip6S84CM@18.0 | surroundings (not a checked kind) |
| 581 | 0:20.0 | left | runoff | grass bank rising | onboard:RAZip6S84CM@20.0 | surroundings (not a checked kind) |
| 581 | 0:20.0 | right | boards | tan billboard panels | onboard:RAZip6S84CM@20.0 | surroundings (not a checked kind) |
| 581 | 0:20.0 | right | paint | white edge line | onboard:RAZip6S84CM@20.0 | surroundings (not a checked kind) |
| 655 | 0:22.0 | right | paint | white edge line | onboard:RAZip6S84CM@22.0 | surroundings (not a checked kind) |
| 655 | 0:22.0 | right | runoff | dirt then grass | onboard:RAZip6S84CM@22.0 | surroundings (not a checked kind) |
| 655 | 0:22.0 | right | tyre_wall | dark low tyre-faced wall far right | onboard:RAZip6S84CM@22.0 | covered by barrier 15 (tyres) |
| 690 |  | right | tyre_wall | low dark tyre-faced wall far out | streetview:exOejoRD5-jF1wceBnhfjg@317 | covered by barrier 15 (tyres) |
| 710 | 0:24.0 | left | kerb | T3 apex kerb | onboard:RAZip6S84CM@24.0 | covered by kerb 690.4-745.3 |
| 710 | 0:24.0 | left | runoff | dirt then grass | onboard:RAZip6S84CM@24.0 | surroundings (not a checked kind) |
| 710 | 0:24.0 | right | runoff | grass, wide | onboard:RAZip6S84CM@24.0 | surroundings (not a checked kind) |
| 735 | 0:22.0 | left | fence | catch fence, curved-top posts, far left | onboard:RAZip6S84CM@22.0 | covered by barrier 16 (concrete + 3 m fence) catch fence (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 735 | 0:22.0 | left | wall | white low wall / armco end ahead-left | onboard:RAZip6S84CM@22.0 | covered by barrier 16 (concrete + 3 m fence) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 740 | 0:24.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@24.0 | covered by barrier 16 (concrete + 3 m fence) catch fence (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 740 | 0:24.0 | left | wall | low dark concrete wall at the foot of the terraces | onboard:RAZip6S84CM@24.0 | covered by barrier 16 (concrete + 3 m fence) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 763 | 0:26.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@26.0 | covered by barrier 16 (concrete + 3 m fence) catch fence |
| 763 | 0:26.0 | left | paint | white edge line | onboard:RAZip6S84CM@26.0 | surroundings (not a checked kind) |
| 763 | 0:26.0 | left | wall | low dark concrete wall | onboard:RAZip6S84CM@26.0 | covered by barrier 16 (concrete + 3 m fence) |
| 763 | 0:26.0 | right | paint | white edge line | onboard:RAZip6S84CM@26.0 | surroundings (not a checked kind) |
| 763 | 0:26.0 | right | runoff | grass bank | onboard:RAZip6S84CM@26.0 | surroundings (not a checked kind) |
| 811 | 0:28.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@28.0 | covered by barrier 16 (concrete + 3 m fence) catch fence; barrier 64 (fence + 1.8 m fence) |
| 811 | 0:28.0 | left | stand | concrete terraces | onboard:RAZip6S84CM@28.0 | covered by terrace T3a-T4 |
| 811 | 0:28.0 | left | wall | low concrete wall | onboard:RAZip6S84CM@28.0 | covered by barrier 16 (concrete + 3 m fence) |
| 811 | 0:28.0 | right | paint | white edge line | onboard:RAZip6S84CM@28.0 | surroundings (not a checked kind) |
| 811 | 0:28.0 | right | runoff | grass | onboard:RAZip6S84CM@28.0 | surroundings (not a checked kind) |
| 813 | 0:26.0 | left | stand | concrete terraces (T3a-T4) | onboard:RAZip6S84CM@26.0 | covered by terrace T3a-T4 (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 855 | 0:30.0 | left | fence | catch fence, curved-top posts on the wall | onboard:RAZip6S84CM@30.0 | covered by barrier 16 (concrete + 3 m fence) catch fence |
| 855 | 0:30.0 | left | kerb | T4 entry, outside, long | onboard:RAZip6S84CM@30.0 | covered by kerb 855.1-959.8 |
| 855 | 0:30.0 | left | stand | concrete terraces (T3a-T4), ~20 rows | onboard:RAZip6S84CM@30.0 | covered by terrace T3a-T4 |
| 855 | 0:30.0 | left | wall | light grey concrete wall | onboard:RAZip6S84CM@30.0 | covered by barrier 16 (concrete + 3 m fence) |
| 855 | 0:30.0 | right | boards | red ad boards on the barrier | onboard:RAZip6S84CM@30.0 | surroundings (not a checked kind) |
| 855 | 0:30.0 | right | runoff | dirt then grass | onboard:RAZip6S84CM@30.0 | surroundings (not a checked kind) |
| 855 | 0:30.0 | right | tyre_wall | dark tyre wall / black barrier line with red ad boards | onboard:RAZip6S84CM@30.0 | covered by barrier 17 (tyres) |
| 900 |  | left | fence | catch fence on the wall below the T3a-T4 stands | streetview:nA1oaDXwADSI7x-Pa-j4Ow@337 | covered by barrier 43 (concrete + 2.5 m fence) catch fence |
| 900 |  | left | wall | concrete wall below the stands | streetview:nA1oaDXwADSI7x-Pa-j4Ow@337 | covered by barrier 43 (concrete + 2.5 m fence) |
| 909 | 0:32.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@32.0 | covered by barrier 43 (concrete + 2.5 m fence) catch fence |
| 909 | 0:32.0 | left | kerb | T4 entry outside kerb continues | onboard:RAZip6S84CM@32.0 | covered by kerb 855.1-959.8 |
| 909 | 0:32.0 | left | wall | light grey concrete wall | onboard:RAZip6S84CM@32.0 | covered by barrier 43 (concrete + 2.5 m fence) |
| 909 | 0:32.0 | right | runoff | dirt, wide | onboard:RAZip6S84CM@32.0 | surroundings (not a checked kind) |
| 909 | 0:32.0 | right | tyre_wall | dark concrete / tyre-faced wall | onboard:RAZip6S84CM@32.0 | covered by barrier 17 (tyres) (corrected in scenery round 5 (21 Oct 2026): kind was wall) |
| 968 | 0:34.0 | ahead | boards | ad boards on a low wall beyond the Chute (red/white, Save Mart) | onboard:RAZip6S84CM@34.0 | surroundings (not a checked kind) |
| 968 | 0:34.0 | left | wall | light grey concrete wall end, catch fence | onboard:RAZip6S84CM@34.0 | covered by barrier 43 (concrete + 2.5 m fence) |
| 968 | 0:34.0 | right | paint | white edge line | onboard:RAZip6S84CM@34.0 | surroundings (not a checked kind) |
| 968 | 0:34.0 | right | runoff | dirt island inside T4 | onboard:RAZip6S84CM@34.0 | surroundings (not a checked kind) |
| 969 | 0:32.0 | right | station | white elevated marshal post with roof, on a platform | onboard:RAZip6S84CM@32.0 | covered by marshal 'T4' (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 970 | 0:26.0 | right | station | white elevated marshal tower with roof | onboard:RAZip6S84CM@26.0 | covered by marshal 'T4' (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 970 | 0:30.0 | right | station | white marshal post with roof | onboard:RAZip6S84CM@30.0 | covered by marshal 'T4' (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 998 | 0:34.0 | left | cone_line | orange traffic cones across the Chute mouth | onboard:RAZip6S84CM@34.0 | covered by cone line 0 (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1004 | 0:36.0 | left | runoff | grass then dirt | onboard:RAZip6S84CM@36.0 | surroundings (not a checked kind) |
| 1004 | 0:36.0 | right | kerb | T4 apex kerb | onboard:RAZip6S84CM@36.0 | covered by kerb 989.8-1029.7 |
| 1051 | 0:38.0 | left | kerb | T4 exit outside kerb | onboard:RAZip6S84CM@38.0 | covered by kerb 1024.7-1094.5 |
| 1051 | 0:38.0 | left | runoff | dirt then grass | onboard:RAZip6S84CM@38.0 | surroundings (not a checked kind) |
| 1051 | 0:38.0 | right | fence | fence on the hill top | onboard:RAZip6S84CM@38.0 | covered by barrier 54 (fence + 2.5 m fence) |
| 1051 | 0:38.0 | right | paint | white edge line | onboard:RAZip6S84CM@38.0 | surroundings (not a checked kind) |
| 1051 | 0:38.0 | right | wall | light grey concrete wall at the foot of the bank | onboard:RAZip6S84CM@38.0 | covered by barrier 25 (concrete) |
| 1081 | 0:38.0 | left | fence | chain-link fence with posts | onboard:RAZip6S84CM@38.0 | covered by barrier 26 (tyres + 1.5 m fence) catch fence (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1081 | 0:38.0 | left | tyre_wall | low dark wall / tyre line | onboard:RAZip6S84CM@38.0 | covered by barrier 26 (tyres + 1.5 m fence) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1084 | 0:36.0 | left | fence | chain-link fence | onboard:RAZip6S84CM@36.0 | covered by barrier 26 (tyres + 1.5 m fence) catch fence (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1084 | 0:36.0 | left | tyre_wall | low black wall with ad boards (Save Mart, others) | onboard:RAZip6S84CM@36.0 | covered by barrier 26 (tyres + 1.5 m fence) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none, kind was wall) |
| 1117 | 0:40.0 | left | paint | white edge line | onboard:RAZip6S84CM@40.0 | surroundings (not a checked kind) |
| 1117 | 0:40.0 | left | runoff | grass / dry grass | onboard:RAZip6S84CM@40.0 | surroundings (not a checked kind) |
| 1117 | 0:40.0 | left | tyre_wall | black tyre stacks 2-3 high with a rail on top | onboard:RAZip6S84CM@40.0 | covered by barrier 26 (tyres + 1.5 m fence) |
| 1117 | 0:40.0 | right | fence | fence on the hill top | onboard:RAZip6S84CM@40.0 | covered by barrier 54 (fence + 2.5 m fence) |
| 1117 | 0:40.0 | right | paint | white edge line | onboard:RAZip6S84CM@40.0 | surroundings (not a checked kind) |
| 1117 | 0:40.0 | right | wall | light grey concrete Jersey segments | onboard:RAZip6S84CM@40.0 | covered by barrier 25 (concrete) |
| 1130 |  | left | tyre_wall | low dark wall (tyres) on the outside of T5 | streetview:zCwjltSjI02eDZGZbVyrMg@80 | covered by barrier 26 (tyres + 1.5 m fence) |
| 1189 | 0:42.0 | left | runoff | grass, wide | onboard:RAZip6S84CM@42.0 | surroundings (not a checked kind) |
| 1189 | 0:42.0 | right | wall | light grey concrete Jersey segments | onboard:RAZip6S84CM@42.0 | covered by barrier 6 (concrete) |
| 1229 | 0:42.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@42.0 | covered by barrier 27 (concrete + 3 m fence) catch fence (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1229 | 0:42.0 | left | wall | low dark wall far left | onboard:RAZip6S84CM@42.0 | covered by barrier 27 (concrete + 3 m fence) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1257 | 0:44.0 | left | fence | catch fence, curved-top posts, on a low wall | onboard:RAZip6S84CM@44.0 | covered by barrier 27 (concrete + 3 m fence) catch fence |
| 1257 | 0:44.0 | left | runoff | grass | onboard:RAZip6S84CM@44.0 | surroundings (not a checked kind) |
| 1257 | 0:44.0 | right | wall | light grey concrete Jersey segments | onboard:RAZip6S84CM@44.0 | covered by barrier 6 (concrete) |
| 1320 | 0:46.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@46.0 | covered by barrier 27 (concrete + 3 m fence) catch fence |
| 1320 | 0:46.0 | left | runoff | grass | onboard:RAZip6S84CM@46.0 | surroundings (not a checked kind) |
| 1320 | 0:46.0 | right | wall | light grey concrete Jersey segments | onboard:RAZip6S84CM@46.0 | covered by barrier 6 (concrete) |
| 1395 |  | right | station | corner station: grey box beside a long black tyre stack on the bank | streetview:GMaTaipEd9Hm7fMNE26aGQ@215 | covered by marshal 'T6 hilltop' |
| 1395 |  | right | tyre_stack | long black tyre stack beside the station box | streetview:GMaTaipEd9Hm7fMNE26aGQ@215 | MISSING |
| 1395 | 0:48.0 | left | runoff | grass | onboard:RAZip6S84CM@48.0 | surroundings (not a checked kind) |
| 1395 | 0:48.0 | left | wall | low dark wall far left | onboard:RAZip6S84CM@48.0 | covered by barrier 27 (concrete + 3 m fence) |
| 1395 | 0:48.0 | right | boards | black sign panel on a post on the bank | onboard:RAZip6S84CM@48.0 | surroundings (not a checked kind) |
| 1395 | 0:48.0 | right | stand | spectator area on the bank with yellow railings / bleachers | onboard:RAZip6S84CM@48.0 | MISSING |
| 1395 | 0:48.0 | right | wall | light grey concrete Jersey segments | onboard:RAZip6S84CM@48.0 | covered by barrier 44 (concrete) |
| 1395 | 0:46.0 | right | station | marshal post with roof on the crest, vehicles parked | onboard:RAZip6S84CM@46.0 | covered by marshal 'T6 hilltop' (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1460 | 0:50.0 | left | paint | white edge line | onboard:RAZip6S84CM@50.0 | surroundings (not a checked kind) |
| 1460 | 0:50.0 | left | runoff | grass mound on the inside | onboard:RAZip6S84CM@50.0 | surroundings (not a checked kind) |
| 1460 | 0:50.0 | right | paint | white edge line | onboard:RAZip6S84CM@50.0 | surroundings (not a checked kind) |
| 1460 | 0:50.0 | right | wall | light grey concrete Jersey segments | onboard:RAZip6S84CM@50.0 | covered by barrier 44 (concrete) |
| 1500 |  | right | tyre_wall | armco far right at the Carousel | streetview:ma3jBYjtYGtNBlTLjNz1LQ@69 | covered by barrier 28 (tyres) (corrected in scenery round 5 (21 Oct 2026): kind was wall) |
| 1513 | 0:52.0 | ahead | fence | spectator fence on the bank top | onboard:RAZip6S84CM@52.0 | skipped: 'ahead' without a distance (corrected in scenery round 5 (21 Oct 2026): side was right, out_m was none) |
| 1513 | 0:52.0 | left | runoff | grass mound inside | onboard:RAZip6S84CM@52.0 | surroundings (not a checked kind) |
| 1513 | 0:52.0 | right | runoff | grass, wide | onboard:RAZip6S84CM@52.0 | surroundings (not a checked kind) |
| 1513 | 0:52.0 | right | tyre_wall | dark low wall / tyre line at the foot of the spectator bank | onboard:RAZip6S84CM@52.0 | covered by barrier 28 (tyres) |
| 1568 | 0:54.0 | ahead | boards | sign panel on a post at the Carousel infield | onboard:RAZip6S84CM@54.0 | surroundings (not a checked kind) |
| 1568 | 0:54.0 | right | mast | light masts | onboard:RAZip6S84CM@54.0 | MISSING |
| 1568 | 0:54.0 | right | tyre_wall | dark low wall / tyre line | onboard:RAZip6S84CM@54.0 | covered by barrier 28 (tyres) |
| 1593 | 0:54.0 | left | kerb | Carousel apex kerb, ahead-left | onboard:RAZip6S84CM@54.0 | covered by kerb 1591.4-1646.3 (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1626 | 0:56.0 | left | kerb | Carousel apex kerb, left | onboard:RAZip6S84CM@56.0 | covered by kerb 1591.4-1646.3 |
| 1626 | 0:56.0 | right | mast | light masts | onboard:RAZip6S84CM@56.0 | MISSING |
| 1626 | 0:56.0 | right | paint | white edge line | onboard:RAZip6S84CM@56.0 | surroundings (not a checked kind) |
| 1626 | 0:56.0 | right | runoff | paved then grass | onboard:RAZip6S84CM@56.0 | surroundings (not a checked kind) |
| 1626 | 0:56.0 | right | tyre_stack | single black tyre stacks on the runoff | onboard:RAZip6S84CM@56.0 | covered by tyres ''; tyres '' |
| 1687 | 0:58.0 | left | paint | grey/white painted blocks on the left edge (flat) | onboard:RAZip6S84CM@58.0 | surroundings (not a checked kind) |
| 1687 | 0:58.0 | left | wall | black wall section then light grey concrete wall | onboard:RAZip6S84CM@58.0 | covered by barrier 4 (concrete) |
| 1687 | 0:58.0 | right | mast | light masts | onboard:RAZip6S84CM@58.0 | MISSING |
| 1687 | 0:58.0 | right | paint | yellow centre line of the drag strip / NASCAR course | onboard:RAZip6S84CM@58.0 | surroundings (not a checked kind) |
| 1687 | 0:58.0 | right | tyre_stack | black tyre stack | onboard:RAZip6S84CM@58.0 | MISSING |
| 1742 | 1:00.0 | left | wall | light blue-grey concrete wall | onboard:RAZip6S84CM@60.0 | covered by barrier 4 (concrete) |
| 1742 | 1:00.0 | right | kerb | Carousel exit kerb, right | onboard:RAZip6S84CM@60.0 | covered by kerb 1721.1-1796 |
| 1742 | 1:00.0 | right | mast | light masts with tyre stacks at the base | onboard:RAZip6S84CM@60.0 | covered by mast '' |
| 1742 | 1:00.0 | right | runoff | dirt strip then grass bank | onboard:RAZip6S84CM@60.0 | surroundings (not a checked kind) |
| 1810 | 1:02.0 | left | wall | light blue-grey concrete wall | onboard:RAZip6S84CM@62.0 | covered by barrier 4 (concrete) |
| 1810 | 1:02.0 | right | mast | light masts | onboard:RAZip6S84CM@62.0 | MISSING |
| 1810 | 1:02.0 | right | paint | white edge line | onboard:RAZip6S84CM@62.0 | surroundings (not a checked kind) |
| 1810 | 1:02.0 | right | runoff | grass bank | onboard:RAZip6S84CM@62.0 | surroundings (not a checked kind) |
| 1888 | 1:04.0 | left | wall | light blue-grey concrete wall | onboard:RAZip6S84CM@64.0 | covered by barrier 4 (concrete) |
| 1888 | 1:04.0 | right | mast | light mast | onboard:RAZip6S84CM@64.0 | MISSING |
| 1888 | 1:04.0 | right | paint | yellow centre line, white edge line | onboard:RAZip6S84CM@64.0 | surroundings (not a checked kind) |
| 1938 | 1:04.0 | right | cone_line | orange cones | onboard:RAZip6S84CM@64.0 | covered by cone line 3 (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1938 | 1:04.0 | right | tyre_wall | black tyre line | onboard:RAZip6S84CM@64.0 | covered by barrier 46 (tyres) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 1956 | 1:06.0 | left | wall | light blue-grey concrete wall | onboard:RAZip6S84CM@66.0 | covered by barrier 4 (concrete) |
| 1956 | 1:06.0 | right | mast | light masts | onboard:RAZip6S84CM@66.0 | MISSING |
| 1956 | 1:06.0 | right | runoff | grass strip, then the Chute pavement | onboard:RAZip6S84CM@66.0 | surroundings (not a checked kind) |
| 1956 | 1:06.0 | right | wall | light blue concrete wall beyond the Chute | onboard:RAZip6S84CM@66.0 | covered by barrier 45 (concrete) |
| 2033 | 1:08.0 | left | wall | light blue-grey concrete wall | onboard:RAZip6S84CM@68.0 | covered by barrier 4 (concrete) |
| 2033 | 1:08.0 | right | runoff | grass then pavement | onboard:RAZip6S84CM@68.0 | surroundings (not a checked kind) |
| 2100 |  | left | tyre_wall | tyre walls left on the T7 approach | streetview:gd1SNdksCq5QZtwlsrzR7g@0 | covered by barrier 5 (tyres) |
| 2112 | 1:10.0 | left | boards | large Toyota ad boards on posts above the wall | onboard:RAZip6S84CM@70.0 | surroundings (not a checked kind) |
| 2112 | 1:10.0 | left | wall | light blue-grey concrete wall | onboard:RAZip6S84CM@70.0 | covered by barrier 4 (concrete); barrier 47 (concrete) |
| 2112 | 1:10.0 | right | runoff | grass then paved runoff | onboard:RAZip6S84CM@70.0 | surroundings (not a checked kind) |
| 2157 | 1:12.0 | ahead | tyre_wall | black tyre line across the T7 runoff, vehicles behind | onboard:RAZip6S84CM@72.0 | skipped: 'ahead' without a distance |
| 2157 | 1:12.0 | left | boards | Pirelli and red ad boards on a low wall | onboard:RAZip6S84CM@72.0 | surroundings (not a checked kind) |
| 2157 | 1:12.0 | left | station | white elevated marshal post on a platform with roof, portable toilet beside | onboard:RAZip6S84CM@72.0 | covered by marshal 'T7' |
| 2157 | 1:12.0 | left | wall | light blue-grey concrete wall end | onboard:RAZip6S84CM@72.0 | covered by barrier 47 (concrete) |
| 2157 | 1:12.0 | right | kerb | T7 island apex kerb | onboard:RAZip6S84CM@72.0 | covered by kerb 2150.2-2202.1 |
| 2167 | 1:12.0 | left | cone_line | orange cones in front of a black tyre line across the Chute's T7 mouth | onboard:RAZip6S84CM@72.0 | covered by cone line 1 (row added in scenery round 5 (21 Oct 2026)) |
| 2167 | 1:12.0 | left | tyre_wall | low black tyre line across the Chute's T7 mouth | onboard:RAZip6S84CM@72.0 | covered by barrier 48 (tyres) (row added in scenery round 5 (21 Oct 2026)) |
| 2202 | 1:14.0 | left | runoff | paved, wide (T7 inside runoff) | onboard:RAZip6S84CM@74.0 | surroundings (not a checked kind) |
| 2202 | 1:14.0 | right | cone_line | orange delineator posts (tall cones) on the island edge | onboard:RAZip6S84CM@74.0 | covered by cone line 2 |
| 2202 | 1:14.0 | right | kerb |  | onboard:RAZip6S84CM@74.0 | covered by kerb 2150.2-2202.1; kerb 2208-2329.8 |
| 2215 |  | left | wall | concrete wall far left along the T7a stands | streetview:J6fsnW4hj4xCjQLzrgRGzA@54 | covered by barrier 49 (concrete) |
| 2237 | 1:14.0 | left | tyre_wall | black tyre wall line, recovery vehicles behind | onboard:RAZip6S84CM@74.0 | covered by barrier 50 (tyres) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 2262 | 1:14.0 | left | stand | concrete terraces | onboard:RAZip6S84CM@74.0 | covered by terrace T7a hill (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 2268 | 1:16.0 | left | cone_line | orange cones along the paved runoff | onboard:RAZip6S84CM@76.0 | MISSING |
| 2268 | 1:16.0 | left | wall | low white wall at the foot of the terraces | onboard:RAZip6S84CM@76.0 | covered by barrier 51 (concrete) |
| 2268 | 1:16.0 | right | cone_line | orange delineator post at the island nose | onboard:RAZip6S84CM@76.0 | MISSING |
| 2268 | 1:16.0 | right | kerb | 7a island kerb, painted island beyond | onboard:RAZip6S84CM@76.0 | covered by kerb 2208-2329.8 |
| 2268 | 1:16.0 | right | mast | light mast | onboard:RAZip6S84CM@76.0 | MISSING |
| 2272 | 1:10.0 | ahead | stand | concrete terraces with fence on top | onboard:RAZip6S84CM@70.0 | covered by terrace T7a hill (corrected in scenery round 5 (21 Oct 2026): side was right, ahead_m was none) |
| 2272 | 1:12.0 | ahead | stand | concrete terraces with fence and light masts on top | onboard:RAZip6S84CM@72.0 | covered by terrace T7a hill (corrected in scenery round 5 (21 Oct 2026): side was right, ahead_m was none) |
| 2273 | 1:08.0 | ahead | stand | concrete terraces on the T7a hill | onboard:RAZip6S84CM@68.0 | covered by terrace T7a hill (corrected in scenery round 5 (21 Oct 2026): side was right, ahead_m was none) |
| 2314 | 1:18.0 | left | fence | fence on the far bank | onboard:RAZip6S84CM@78.0 | covered by barrier 53 (fence + 1.5 m fence) |
| 2314 | 1:18.0 | left | kerb | 7a exit outside kerb | onboard:RAZip6S84CM@78.0 | covered by kerb 2299.8-2371.7 |
| 2314 | 1:18.0 | left | runoff | pavement then grass | onboard:RAZip6S84CM@78.0 | surroundings (not a checked kind) |
| 2314 | 1:18.0 | right | mast | light mast on a black block base | onboard:RAZip6S84CM@78.0 | MISSING |
| 2314 | 1:18.0 | right | paint | white edge line | onboard:RAZip6S84CM@78.0 | surroundings (not a checked kind) |
| 2354 | 1:18.0 | right | wall | light concrete wall with ad board | onboard:RAZip6S84CM@78.0 | covered by barrier 55 (concrete) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 2371 | 1:20.0 | left | fence | fence on the bank top | onboard:RAZip6S84CM@80.0 | covered by barrier 53 (fence + 1.5 m fence) |
| 2371 | 1:20.0 | left | kerb | T8 apex kerb | onboard:RAZip6S84CM@80.0 | covered by kerb 2299.8-2371.7 |
| 2371 | 1:20.0 | left | tyre_wall | dark low wall at the foot of the bank | onboard:RAZip6S84CM@80.0 | covered by barrier 52 (tyres) |
| 2371 | 1:20.0 | right | mast | light masts | onboard:RAZip6S84CM@80.0 | MISSING |
| 2371 | 1:20.0 | right | wall | light grey concrete wall | onboard:RAZip6S84CM@80.0 | covered by barrier 55 (concrete) |
| 2435 | 1:22.0 | left | kerb | short kerb on the left ahead (T8 exit) | onboard:RAZip6S84CM@82.0 | covered by kerb 2409.6-2440.5 |
| 2435 | 1:22.0 | left | tyre_wall | dark low wall / tyre line at the foot of the bank | onboard:RAZip6S84CM@82.0 | covered by barrier 30 (tyres) |
| 2435 | 1:22.0 | right | wall | light grey concrete wall | onboard:RAZip6S84CM@82.0 | covered by barrier 55 (concrete) |
| 2440 |  | left | fence | catch fence on the bank wall | streetview:xXQqyp9Q9sWv9ZLN2ORYsA@108 | covered by barrier 53 (fence + 1.5 m fence) |
| 2440 |  | left | tyre_wall | concrete wall with a catch fence on the bank | streetview:xXQqyp9Q9sWv9ZLN2ORYsA@108 | covered by barrier 30 (tyres) (corrected in scenery round 5 (21 Oct 2026): kind was wall) |
| 2497 | 1:24.0 | left | fence | fence along the hill | onboard:RAZip6S84CM@84.0 | covered by barrier 53 (fence + 1.5 m fence) |
| 2497 | 1:24.0 | left | tyre_wall | dark low wall far left | onboard:RAZip6S84CM@84.0 | covered by barrier 7 (tyres); barrier 30 (tyres) |
| 2497 | 1:24.0 | right | kerb | 8a apex kerb | onboard:RAZip6S84CM@84.0 | covered by kerb 2439.5-2550.3 |
| 2497 | 1:24.0 | right | mast | tall pole | onboard:RAZip6S84CM@84.0 | MISSING |
| 2517 | 1:24.0 | right | tyre_wall | black-covered tyre barrier / dark panel wall | onboard:RAZip6S84CM@84.0 | covered by barrier 9 (tyres) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 2571 | 1:26.0 | left | fence | fence on the bank top | onboard:RAZip6S84CM@86.0 | covered by barrier 8 (concrete + 2 m fence) catch fence; barrier 53 (fence + 1.5 m fence) |
| 2571 | 1:26.0 | left | kerb | 8a exit outside kerb | onboard:RAZip6S84CM@86.0 | covered by kerb 2520.3-2572.2 |
| 2571 | 1:26.0 | left | tyre_wall | dark low wall / tyre line | onboard:RAZip6S84CM@86.0 | covered by barrier 7 (tyres) |
| 2571 | 1:26.0 | right | mast | light mast | onboard:RAZip6S84CM@86.0 | covered by mast '' |
| 2571 | 1:26.0 | right | paint | white edge line | onboard:RAZip6S84CM@86.0 | surroundings (not a checked kind) |
| 2591 | 1:26.0 | right | wall | light grey concrete wall | onboard:RAZip6S84CM@86.0 | covered by barrier 31 (concrete) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 2644 | 1:28.0 | left | fence | catch fence posts on the wall, fence up the bank | onboard:RAZip6S84CM@88.0 | covered by barrier 8 (concrete + 2 m fence) catch fence; barrier 53 (fence + 1.5 m fence) |
| 2644 | 1:28.0 | left | kerb | T9 apex kerb | onboard:RAZip6S84CM@88.0 | covered by kerb 2600.2-2645.1 |
| 2644 | 1:28.0 | left | wall | light grey concrete wall | onboard:RAZip6S84CM@88.0 | covered by barrier 8 (concrete + 2 m fence) |
| 2644 | 1:28.0 | right | runoff | grass, wide | onboard:RAZip6S84CM@88.0 | surroundings (not a checked kind) |
| 2644 | 1:28.0 | right | wall | dark wall with a 'SONOMA TURN 8' sign | onboard:RAZip6S84CM@88.0 | covered by barrier 32 (concrete) |
| 2707 | 1:30.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@90.0 | covered by barrier 56 (concrete + 2.5 m fence) catch fence |
| 2707 | 1:30.0 | left | wall | low dark concrete wall | onboard:RAZip6S84CM@90.0 | covered by barrier 56 (concrete + 2.5 m fence) |
| 2707 | 1:30.0 | right | kerb | T9 exit outside kerb | onboard:RAZip6S84CM@90.0 | covered by kerb 2692-2739.8 |
| 2707 | 1:30.0 | right | mast | light masts | onboard:RAZip6S84CM@90.0 | MISSING |
| 2707 | 1:30.0 | right | runoff | grass, wide | onboard:RAZip6S84CM@90.0 | surroundings (not a checked kind) |
| 2737 | 1:30.0 | left | stand | concrete terraces (back straight) | onboard:RAZip6S84CM@90.0 | covered by terrace back straight / 9a (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 2773 | 1:32.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@92.0 | covered by barrier 18 (concrete + 3 m fence) catch fence; barrier 56 (concrete + 2.5 m fence) catch fence |
| 2773 | 1:32.0 | left | paint | white edge line | onboard:RAZip6S84CM@92.0 | surroundings (not a checked kind) |
| 2773 | 1:32.0 | left | stand | concrete terraces with shade roofs on top | onboard:RAZip6S84CM@92.0 | covered by terrace back straight / 9a |
| 2773 | 1:32.0 | left | wall | dark then light concrete wall | onboard:RAZip6S84CM@92.0 | covered by barrier 18 (concrete + 3 m fence); barrier 56 (concrete + 2.5 m fence) |
| 2773 | 1:32.0 | right | mast | light masts | onboard:RAZip6S84CM@92.0 | MISSING |
| 2773 | 1:32.0 | right | runoff | grass, then the paved 2020 bypass | onboard:RAZip6S84CM@92.0 | surroundings (not a checked kind) |
| 2854 | 1:34.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@94.0 | covered by barrier 18 (concrete + 3 m fence) catch fence |
| 2854 | 1:34.0 | left | stand | concrete terraces with covered stands on top | onboard:RAZip6S84CM@94.0 | covered by terrace back straight / 9a |
| 2854 | 1:34.0 | left | wall | light concrete wall | onboard:RAZip6S84CM@94.0 | covered by barrier 18 (concrete + 3 m fence) |
| 2854 | 1:34.0 | right | runoff | grass, wide | onboard:RAZip6S84CM@94.0 | surroundings (not a checked kind) |
| 2854 | 1:34.0 | right | stand | grandstand far ahead-right (T11 area) | onboard:RAZip6S84CM@94.0 | MISSING |
| 2900 |  | left | fence | catch fence on the wall between the spectator walk and the track | streetview:Gas0S2x3OzWj_AinwcVtAg@170 | covered by barrier 18 (concrete + 3 m fence) catch fence |
| 2947 | 1:36.0 | left | cone_line | single orange cone on the grass (marker) | onboard:RAZip6S84CM@96.0 | MISSING |
| 2947 | 1:36.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@96.0 | covered by barrier 18 (concrete + 3 m fence) catch fence |
| 2947 | 1:36.0 | left | wall | light concrete wall | onboard:RAZip6S84CM@96.0 | covered by barrier 18 (concrete + 3 m fence) |
| 2947 | 1:36.0 | right | runoff | grass, wide | onboard:RAZip6S84CM@96.0 | surroundings (not a checked kind) |
| 2947 | 1:36.0 | right | stand | large grandstand with suites (T10/T11 infield side) | onboard:RAZip6S84CM@96.0 | MISSING |
| 3018 | 1:38.0 | left | cone_line | single orange cone on the grass (marker) | onboard:RAZip6S84CM@98.0 | MISSING |
| 3018 | 1:38.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@98.0 | covered by barrier 57 (concrete + 2.5 m fence) catch fence |
| 3018 | 1:38.0 | left | wall | light concrete wall | onboard:RAZip6S84CM@98.0 | covered by barrier 57 (concrete + 2.5 m fence) |
| 3018 | 1:38.0 | right | runoff | grass | onboard:RAZip6S84CM@98.0 | surroundings (not a checked kind) |
| 3056 | 1:40.0 | ahead | tyre_wall | black covered barrier sections | onboard:RAZip6S84CM@100.0 | skipped: 'ahead' without a distance |
| 3056 | 1:40.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@100.0 | covered by barrier 57 (concrete + 2.5 m fence) catch fence |
| 3056 | 1:40.0 | left | runoff | paved (bypass mouth) | onboard:RAZip6S84CM@100.0 | surroundings (not a checked kind) |
| 3056 | 1:40.0 | left | wall | concrete wall with 'Sonoma Raceway' ad boards | onboard:RAZip6S84CM@100.0 | covered by barrier 57 (concrete + 2.5 m fence) |
| 3056 | 1:40.0 | right | kerb | 9a right-hand apex kerb | onboard:RAZip6S84CM@100.0 | covered by kerb 3020.2-3045.2 |
| 3056 | 1:40.0 | right | tyre_stack | stack of 2 grey tyres on the apex | onboard:RAZip6S84CM@100.0 | covered by tyres '' |
| 3089 | 1:42.0 | left | boards | Toyota and other ad boards on the far wall | onboard:RAZip6S84CM@102.0 | surroundings (not a checked kind) |
| 3089 | 1:42.0 | left | kerb | 9a left-hand apex kerb | onboard:RAZip6S84CM@102.0 | covered by kerb 3060.1-3169.9 |
| 3089 | 1:42.0 | right | mast | light masts | onboard:RAZip6S84CM@102.0 | MISSING |
| 3089 | 1:42.0 | right | stand | large grandstand with suites deck | onboard:RAZip6S84CM@102.0 | MISSING |
| 3089 | 1:42.0 | right | tyre_wall | black covered tyre barrier | onboard:RAZip6S84CM@102.0 | covered by barrier 34 (tyres) |
| 3119 | 1:44.0 | left | kerb | 9a exit kerb, left | onboard:RAZip6S84CM@104.0 | covered by kerb 3060.1-3169.9 |
| 3119 | 1:44.0 | left | tyre_stack | black tyre stack in front of the wall | onboard:RAZip6S84CM@104.0 | covered by tyres '' |
| 3119 | 1:44.0 | left | wall | concrete wall with tall 'SONOMA RACEWAY' / Sunbelt board panels on top | onboard:RAZip6S84CM@104.0 | covered by barrier 59 (concrete) |
| 3119 | 1:44.0 | right | fence | catch fence on the wall, curved-top posts, cables | onboard:RAZip6S84CM@104.0 | covered by barrier 58 (concrete + 2.9 m fence) catch fence |
| 3119 | 1:44.0 | right | stand | grandstand with suites deck behind the fence | onboard:RAZip6S84CM@104.0 | MISSING |
| 3119 | 1:44.0 | right | wall | light concrete wall (SAFER-like) | onboard:RAZip6S84CM@104.0 | covered by barrier 58 (concrete + 2.9 m fence) |
| 3149 | 1:42.0 | right | wall | light concrete wall with catch fence | onboard:RAZip6S84CM@102.0 | covered by barrier 58 (concrete + 2.9 m fence) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 3157 | 1:46.0 | left | boards | Sunbelt Rentals, Toyota boards on the wall | onboard:RAZip6S84CM@106.0 | surroundings (not a checked kind) |
| 3157 | 1:46.0 | left | wall | concrete wall topped by tall ad-board panels (Sunbelt Rentals, Toyota) | onboard:RAZip6S84CM@106.0 | covered by barrier 20 (concrete); barrier 59 (concrete) |
| 3157 | 1:46.0 | right | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@106.0 | covered by barrier 58 (concrete + 2.9 m fence) catch fence |
| 3157 | 1:46.0 | right | mast | light masts | onboard:RAZip6S84CM@106.0 | MISSING |
| 3157 | 1:46.0 | right | wall | light concrete wall | onboard:RAZip6S84CM@106.0 | covered by barrier 58 (concrete + 2.9 m fence) |
| 3203 | 1:48.0 | left | boards | Toyota, Save Mart, zMAX boards | onboard:RAZip6S84CM@108.0 | surroundings (not a checked kind) |
| 3203 | 1:48.0 | left | wall | concrete wall topped by tall Toyota ad-board panels | onboard:RAZip6S84CM@108.0 | covered by barrier 20 (concrete) |
| 3203 | 1:48.0 | right | boards | small sign panel on a post | onboard:RAZip6S84CM@108.0 | surroundings (not a checked kind) |
| 3203 | 1:48.0 | right | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@108.0 | covered by barrier 58 (concrete + 2.9 m fence) catch fence |
| 3203 | 1:48.0 | right | kerb | T10 apex kerb | onboard:RAZip6S84CM@108.0 | covered by kerb 3214.8-3291.6 |
| 3203 | 1:48.0 | right | wall | light concrete wall | onboard:RAZip6S84CM@108.0 | covered by barrier 58 (concrete + 2.9 m fence) |
| 3259 | 1:50.0 | left | boards | Humboldt, Save Mart, zMAX boards | onboard:RAZip6S84CM@110.0 | surroundings (not a checked kind) |
| 3259 | 1:50.0 | left | wall | concrete wall topped by tall ad-board panels (Humboldt, Save Mart, zMAX) | onboard:RAZip6S84CM@110.0 | covered by barrier 20 (concrete) |
| 3259 | 1:50.0 | right | building | tan buildings beyond the fence (infield) | onboard:RAZip6S84CM@110.0 | ASSIGNED to the buildings round |
| 3259 | 1:50.0 | right | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@110.0 | covered by barrier 21 (concrete + 3.5 m fence) catch fence |
| 3259 | 1:50.0 | right | kerb | T10 apex/exit kerb right | onboard:RAZip6S84CM@110.0 | covered by kerb 3214.8-3291.6 |
| 3259 | 1:50.0 | right | wall | light concrete wall | onboard:RAZip6S84CM@110.0 | covered by barrier 21 (concrete + 3.5 m fence) |
| 3326 | 1:52.0 | left | kerb | T10 exit outside kerb, left | onboard:RAZip6S84CM@112.0 | covered by kerb 3337.5-3402.4 |
| 3326 | 1:52.0 | left | wall | concrete wall topped by tall ad-board panels (zMAX, EchoPark) | onboard:RAZip6S84CM@112.0 | covered by barrier 20 (concrete) |
| 3326 | 1:52.0 | right | building | infield buildings beyond the fence | onboard:RAZip6S84CM@112.0 | covered by building 11 '' 3.2 m |
| 3326 | 1:52.0 | right | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@112.0 | covered by barrier 21 (concrete + 3.5 m fence) catch fence |
| 3326 | 1:52.0 | right | mast | light mast and flag pole | onboard:RAZip6S84CM@112.0 | MISSING |
| 3326 | 1:52.0 | right | wall | concrete wall | onboard:RAZip6S84CM@112.0 | covered by barrier 21 (concrete + 3.5 m fence) |
| 3404 | 1:54.0 | left | tyre_wall | tyre bundles along the foot of the tall wall | onboard:RAZip6S84CM@114.0 | covered by barrier 60 (tyres) |
| 3404 | 1:54.0 | left | wall | tall wall with EchoPark board panels | onboard:RAZip6S84CM@114.0 | covered by barrier 20 (concrete) |
| 3404 | 1:54.0 | right | fence | catch fence on a concrete wall, curved-top posts | onboard:RAZip6S84CM@114.0 | covered by barrier 21 (concrete + 3.5 m fence) catch fence; barrier 33 (tyres + 3.5 m fence) catch fence |
| 3404 | 1:54.0 | right | tyre_wall | black tyre stacks 4 high, continuous | onboard:RAZip6S84CM@114.0 | covered by barrier 33 (tyres + 3.5 m fence) |
| 3404 | 1:54.0 | right | wall | concrete wall under the catch fence | onboard:RAZip6S84CM@114.0 | covered by barrier 21 (concrete + 3.5 m fence) |
| 3492 | 1:56.0 | left | station | marshal standing at a door in the tall wall | onboard:RAZip6S84CM@116.0 | MISSING |
| 3492 | 1:56.0 | left | wall | light blue concrete Jersey wall (pit-in separation) | onboard:RAZip6S84CM@116.0 | covered by barrier 35 (concrete) |
| 3492 | 1:56.0 | left | wall | tall concrete wall with Las Vegas / O'Reilly boards on top (outside of the pit-in lane) | onboard:RAZip6S84CM@116.0 | covered by barrier 35 (concrete) |
| 3492 | 1:56.0 | right | runoff | paved infield (T11a / NASCAR), painted lines | onboard:RAZip6S84CM@116.0 | surroundings (not a checked kind) |
| 3577 | 1:58.0 | left | cone_line | orange cones along the pit-in separation | onboard:RAZip6S84CM@118.0 | covered by cone line 4 |
| 3577 | 1:58.0 | left | paint | double white line at the pit-in split | onboard:RAZip6S84CM@118.0 | surroundings (not a checked kind) |
| 3577 | 1:58.0 | left | wall | light blue concrete Jersey wall (pit-in separation) | onboard:RAZip6S84CM@118.0 | covered by barrier 13 (concrete); barrier 35 (concrete) |
| 3577 | 1:58.0 | left | wall | tall concrete wall with Lucky / Save Mart / Pit Boss boards | onboard:RAZip6S84CM@118.0 | covered by barrier 13 (concrete); barrier 35 (concrete) |
| 3577 | 1:58.0 | right | runoff | paved infield | onboard:RAZip6S84CM@118.0 | surroundings (not a checked kind) |
| 3600 |  | left | wall | tall wall between the pit-in lane and the paddock: concrete base and Sprint board panels | streetview:jrXpHaDfJT2APw6zcyBKRA@196 | covered by barrier 13 (concrete); barrier 36 (concrete) |
| 3635 | 2:00.0 | ahead | fence | catch fence, curved-top posts on the T11 outside wall | onboard:RAZip6S84CM@120.0 | skipped: 'ahead' without a distance |
| 3635 | 2:00.0 | ahead | wall | light blue low wall round the T11 outside | onboard:RAZip6S84CM@120.0 | skipped: 'ahead' without a distance |
| 3635 | 2:00.0 | left | wall | light blue concrete Jersey wall | onboard:RAZip6S84CM@120.0 | covered by barrier 13 (concrete); barrier 36 (concrete) |
| 3635 | 2:00.0 | left | wall | tall wall with Coca-Cola / xfinity boards | onboard:RAZip6S84CM@120.0 | covered by barrier 13 (concrete); barrier 36 (concrete) |
| 3635 | 2:00.0 | right | runoff | paved infield apron, painted lines | onboard:RAZip6S84CM@120.0 | surroundings (not a checked kind) |
| 3635 | 2:00.0 | right | tyre_stack | red/white painted barrier blocks / barrels on the apron | onboard:RAZip6S84CM@120.0 | MISSING |
| 3640 |  | left | tyre_wall | continuous dark tyre wall round the outside of the hairpin, in front of the concrete wall and catch fence | streetview:jrXpHaDfJT2APw6zcyBKRA@196 | covered by barrier 14 (tyres + 2 m fence) |
| 3660 |  | right | cone_line | traffic cone at the apron edge | streetview:jrXpHaDfJT2APw6zcyBKRA@196 | MISSING |
| 3660 |  | right | tyre_stack | free-standing yellow / blue tyre stacks, 4 high, along the painted apron | streetview:jrXpHaDfJT2APw6zcyBKRA@196 | MISSING |
| 3669 | 2:02.0 | left | building | glazed two-storey paddock / hospitality building | onboard:RAZip6S84CM@122.0 | covered by building 1 '' 4.5 m; building 3 '' 5.2 m |
| 3669 | 2:02.0 | left | fence | catch fence, curved-top posts | onboard:RAZip6S84CM@122.0 | covered by barrier 14 (tyres + 2 m fence) catch fence |
| 3669 | 2:02.0 | left | tyre_wall | white tyre stacks along the far wall | onboard:RAZip6S84CM@122.0 | covered by barrier 14 (tyres + 2 m fence) |
| 3669 | 2:02.0 | left | wall | light blue concrete wall round the hairpin outside | onboard:RAZip6S84CM@122.0 | covered by barrier 37 (concrete); barrier 38 (concrete) |
| 3669 | 2:02.0 | right | kerb | T11 apex kerb | onboard:RAZip6S84CM@122.0 | covered by kerb 3614.9-3744.6 |
| 3669 | 2:02.0 | right | tyre_stack | red/white painted concrete blocks and a white water-filled barrier on the apron | onboard:RAZip6S84CM@122.0 | MISSING |
| 3699 | 2:04.0 | left | building | tan stucco garages with green metal roofs (paddock) | onboard:RAZip6S84CM@124.0 | covered by building 3 '' 5.2 m; building 6 '' 6.8 m |
| 3699 | 2:04.0 | left | fence | chain-link fence | onboard:RAZip6S84CM@124.0 | covered by barrier 14 (tyres + 2 m fence) catch fence |
| 3699 | 2:04.0 | left | mast | light masts | onboard:RAZip6S84CM@124.0 | MISSING |
| 3699 | 2:04.0 | left | tyre_wall | white-painted tyre wall, 2-3 high | onboard:RAZip6S84CM@124.0 | covered by barrier 14 (tyres + 2 m fence) |
| 3699 | 2:04.0 | right | kerb | T11 apex/exit kerb | onboard:RAZip6S84CM@124.0 | covered by kerb 3614.9-3744.6 |
| 3699 | 2:04.0 | right | tyre_stack | red/white painted concrete blocks | onboard:RAZip6S84CM@124.0 | MISSING |
| 3737 | 2:06.0 | left | building | long tan garage building, green roof, windows | onboard:RAZip6S84CM@126.0 | covered by building 4 '' 6.7 m; building 6 '' 6.8 m |
| 3737 | 2:06.0 | left | mast | light masts | onboard:RAZip6S84CM@126.0 | MISSING |
| 3737 | 2:06.0 | left | pit_lane | paved lane beyond the wall | onboard:RAZip6S84CM@126.0 | surroundings (not a checked kind) |
| 3737 | 2:06.0 | left | wall | white concrete wall (pit-road side) | onboard:RAZip6S84CM@126.0 | covered by barrier 10 (concrete) |
| 3737 | 2:06.0 | right | paint | white edge line | onboard:RAZip6S84CM@126.0 | surroundings (not a checked kind) |
| 3737 | 2:06.0 | right | runoff | paved (drag strip / infield) | onboard:RAZip6S84CM@126.0 | surroundings (not a checked kind) |
| 3784 | 2:08.0 | left | building | tan garages with green roofs | onboard:RAZip6S84CM@128.0 | covered by building 4 '' 6.7 m; building 7 '' 6.3 m |
| 3784 | 2:08.0 | left | pit_lane | pit lane with numbered boxes beyond the wall | onboard:RAZip6S84CM@128.0 | surroundings (not a checked kind) |
| 3784 | 2:08.0 | left | wall | white concrete wall (pit-road side) | onboard:RAZip6S84CM@128.0 | covered by barrier 10 (concrete) |
| 3784 | 2:08.0 | right | paint | white edge line | onboard:RAZip6S84CM@128.0 | surroundings (not a checked kind) |
| 3784 | 2:08.0 | right | runoff | paved, wide (drag strip side) | onboard:RAZip6S84CM@128.0 | surroundings (not a checked kind) |
| 3843 | 2:10.0 | left | building | garages and the control tower building | onboard:RAZip6S84CM@130.0 | covered by building 2 '' 6.2 m |
| 3843 | 2:10.0 | left | mast | light masts | onboard:RAZip6S84CM@130.0 | MISSING |
| 3843 | 2:10.0 | left | wall | white concrete wall (pit-road side) | onboard:RAZip6S84CM@130.0 | covered by barrier 10 (concrete) |
| 3843 | 2:10.0 | right | runoff | paved, wide | onboard:RAZip6S84CM@130.0 | surroundings (not a checked kind) |
| 3910 |  | left | building | two-storey suites building beyond the pit road | streetview:QduY6QTXmw4JDevQVE_b-g@338 | covered by building 2 '' 6.2 m; building 5 '' 8.7 m |
| 3910 |  | right | building | two-storey control tower building beyond the drag strip | streetview:QduY6QTXmw4JDevQVE_b-g@338 | ASSIGNED to the buildings round |
| 3912 | 2:12.0 | left | building | tan multi-storey glazed building (timing / control) | onboard:RAZip6S84CM@132.0 | covered by building 2 '' 6.2 m; building 5 '' 8.7 m |
| 3912 | 2:12.0 | left | cone_line | orange cones in the pit lane | onboard:RAZip6S84CM@132.0 | MISSING |
| 3912 | 2:12.0 | left | wall | white concrete wall (pit-road side), end ahead | onboard:RAZip6S84CM@132.0 | covered by barrier 10 (concrete) |
| 3912 | 2:12.0 | right | mast | light mast and flag pole | onboard:RAZip6S84CM@132.0 | MISSING |
| 3952 | 2:12.0 | right | wall | wall with zMAX / Save Mart boards | onboard:RAZip6S84CM@132.0 | covered by barrier 3 (concrete); barrier 12 (concrete) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 3965 | 2:10.0 | right | wall | wall with EchoPark boards | onboard:RAZip6S84CM@130.0 | covered by barrier 3 (concrete); barrier 12 (concrete) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 3965 | 2:08.0 | right | wall | wall with Las Vegas / O'Reilly boards | onboard:RAZip6S84CM@128.0 | covered by barrier 3 (concrete); barrier 12 (concrete) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 3966 | 2:06.0 | right | wall | wall with ad boards far right | onboard:RAZip6S84CM@126.0 | covered by barrier 3 (concrete); barrier 12 (concrete) (corrected in scenery round 5 (21 Oct 2026): ahead_m was none) |
| 3967 | 2:14.0 | left | cone_line | orange cones in the pit lane | onboard:RAZip6S84CM@134.0 | covered by cone line 5 |
| 3967 | 2:14.0 | left | stand | main grandstand with suites deck and press box | onboard:RAZip6S84CM@134.0 | MISSING |
| 3967 | 2:14.0 | left | wall | concrete pit wall wrapped green (EchoPark) | onboard:RAZip6S84CM@134.0 | covered by barrier 1 (concrete); barrier 10 (concrete) |
| 3967 | 2:14.0 | right | mast | light masts | onboard:RAZip6S84CM@134.0 | MISSING |
| 3967 | 2:14.0 | right | wall | concrete wall wrapped green (EchoPark, RESTART ZONE) | onboard:RAZip6S84CM@134.0 | covered by barrier 3 (concrete); barrier 12 (concrete) |
| 4024 | 2:16.0 | left | stand | main grandstand with suites deck (Sonoma Raceway sign) | onboard:RAZip6S84CM@136.0 | MISSING |
| 4024 | 2:16.0 | left | wall | concrete pit wall, light blue | onboard:RAZip6S84CM@136.0 | covered by barrier 1 (concrete); barrier 62 (concrete) |
| 4024 | 2:16.0 | right | boards | Sonoma Raceway / Toyota boards on the far drag-strip wall | onboard:RAZip6S84CM@136.0 | surroundings (not a checked kind) |
| 4024 | 2:16.0 | right | mast | light masts beyond the drag strip | onboard:RAZip6S84CM@136.0 | MISSING |
| 4024 | 2:16.0 | right | wall | concrete wall to the drag strip, light blue, ad panels | onboard:RAZip6S84CM@136.0 | covered by barrier 3 (concrete); barrier 12 (concrete) |
| 4050 |  | both | mast | light masts both sides of the straight | streetview:5MY4xR9O7etAXEHnZCVnGQ@300 | MISSING (left); covered by mast '' (right) |
| 4050 |  | left | stand | main grandstand behind the pit lane, open bleachers, suites deck, stair towers | streetview:5MY4xR9O7etAXEHnZCVnGQ@300 | MISSING |
| 4050 |  | left | wall | concrete pit wall at the line | streetview:5MY4xR9O7etAXEHnZCVnGQ@300 | covered by barrier 1 (concrete); barrier 62 (concrete) |
| 4050 |  | right | wall | concrete wall to the drag strip, Sonoma Raceway boards on its face | streetview:5MY4xR9O7etAXEHnZCVnGQ@300 | covered by barrier 3 (concrete); barrier 12 (concrete) |
| 4092 | 2:18.0 | both | paint | chequered start/finish line, green/white, SONOMA RACEWAY lettering | onboard:RAZip6S84CM@138.0 | surroundings (not a checked kind) |
| 4092 | 2:18.0 | left | wall | concrete pit wall, light blue | onboard:RAZip6S84CM@138.0 | covered by barrier 1 (concrete); barrier 62 (concrete) |
| 4092 | 2:18.0 | right | fence | chain-link catch fence beyond the drag strip | onboard:RAZip6S84CM@138.0 | covered by barrier 61 (fence + 3 m fence) |
| 4092 | 2:18.0 | right | wall | concrete wall with Cup Series / mural panels | onboard:RAZip6S84CM@138.0 | covered by barrier 3 (concrete); barrier 12 (concrete) |
| 20 |  | left | building | red-roofed metal pit-exit building ahead | onboard:24of8fjjAug@296 | pit lane: not a checked kind for the lap |
| 20 |  | left | wall | low white pit-box wall (box 8) | onboard:24of8fjjAug@296 | pit-lane gate (pit_lane.walls) |
| 20 |  | right | wall | white concrete pit wall | onboard:24of8fjjAug@296 | pit-lane gate (pit_lane.walls) |
| 100 |  | left | building | red-roofed metal building (pit exit, Farmers end) | onboard:24of8fjjAug@300 | pit lane: not a checked kind for the lap |
| 100 |  | left | fence | black steel fence round the pit-exit apron | onboard:24of8fjjAug@300 | pit lane: not a checked kind for the lap |
| 100 |  | left | tyre_stack | black tyre stack on the apron | onboard:24of8fjjAug@300 | pit lane: not a checked kind for the lap |
| 100 |  | right | wall | pit-wall nose: white Jersey segments curving right with the track | onboard:24of8fjjAug@300 | pit-lane gate (pit_lane.walls) |
| 160 |  | left | fence | catch fence on the wall, curved-top posts | onboard:24of8fjjAug@304 | pit lane: not a checked kind for the lap |
| 160 |  | left | wall | white concrete wall along the pit-out lane | onboard:24of8fjjAug@304 | pit-lane gate (pit_lane.walls) |
| 160 |  | right | cone_line | yellow cones on the double yellow blend line | onboard:24of8fjjAug@304 | pit lane: not a checked kind for the lap |
| 160 |  | right | paint | double yellow line between the pit-out lane and the track | onboard:24of8fjjAug@304 | pit lane: not a checked kind for the lap |
| 3560 |  | left | wall | tall grey wall (doors in its face) topped by board panels (Save Mart, Zip), Jersey barrier at its foot | onboard:24of8fjjAug@1446 | pit-lane gate (pit_lane.walls) |
| 3560 |  | right | cone_line | yellow cones on the double white line at the pit-in split | onboard:24of8fjjAug@1446 | pit lane: not a checked kind for the lap |
| 3570 |  | right | tyre_stack | red/white water-filled impact barriers at the separation-wall nose | onboard:24of8fjjAug@1446 | pit lane: not a checked kind for the lap |
| 3610 |  | left | wall | Jersey barrier in front of the tall board wall (Coca-Cola, GEICO) | onboard:24of8fjjAug@1452 | pit-lane gate (pit_lane.walls) |
| 3610 |  | right | wall | Jersey barrier separating the pit-in lane from the track | onboard:24of8fjjAug@1452 | pit-lane gate (pit_lane.walls) |
| 3680 |  | left | building | glazed paddock / hospitality buildings | onboard:24of8fjjAug@1458 | pit lane: not a checked kind for the lap |
| 3680 |  | left | fence | catch fence, curved-top posts | onboard:24of8fjjAug@1458 | pit lane: not a checked kind for the lap |
| 3680 |  | left | wall | concrete wall | onboard:24of8fjjAug@1458 | pit-lane gate (pit_lane.walls) |
| 3680 |  | right | fence | catch fence, curved-top posts | onboard:24of8fjjAug@1458 | pit lane: not a checked kind for the lap |
| 3680 |  | right | wall | concrete wall (the T11 outside wall seen from the lane) | onboard:24of8fjjAug@1458 | pit-lane gate (pit_lane.walls) |
| 3730 |  | ahead | building | tan stucco garages with green roofs | onboard:24of8fjjAug@1470 | pit lane: not a checked kind for the lap |
| 3730 |  | left | fence | chain-link fence | onboard:24of8fjjAug@1470 | pit lane: not a checked kind for the lap |
| 3730 |  | right | building | Sunoco fuel island with canopy and tall Sunoco sign | onboard:24of8fjjAug@1470 | pit lane: not a checked kind for the lap |
| 3730 |  | right | mast | light mast by the fuel island | onboard:24of8fjjAug@1470 | pit lane: not a checked kind for the lap |
| 3990 |  | left | building | two-storey tan timing building with external stairs, paddock gate | onboard:24of8fjjAug@284 | pit lane: not a checked kind for the lap |
| 3990 |  | left | fence | black steel paddock fence / gate | onboard:24of8fjjAug@284 | pit lane: not a checked kind for the lap |
| 4010 |  | left | stand | main grandstand with suites deck behind the boxes | onboard:24of8fjjAug@288 | pit lane: not a checked kind for the lap |
| 4010 |  | left | wall | low white pit-box wall with box numbers | onboard:24of8fjjAug@288 | pit-lane gate (pit_lane.walls) |
| 4010 |  | right | wall | white concrete pit wall, GEICO / RESTART ZONE boards along its top | onboard:24of8fjjAug@288 | pit-lane gate (pit_lane.walls) |
| 4060 |  | left | wall | low white pit-box wall (boxes 16, 15) | onboard:24of8fjjAug@292 | pit-lane gate (pit_lane.walls) |
| 4060 |  | right | mast | light masts beyond the pit wall | onboard:24of8fjjAug@292 | pit lane: not a checked kind for the lap |
| 4060 |  | right | wall | white concrete pit wall | onboard:24of8fjjAug@292 | pit-lane gate (pit_lane.walls) |
