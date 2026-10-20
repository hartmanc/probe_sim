# Sonoma scenery evidence manifest (round 3, 20 Oct 2026)

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

## Objects in the package (78 rows)

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

## Structures (buildings round, 21 Oct 2026; config `structures`, tools/track/build_structures.py, app src/app/structures.ts)

The owner: "The sim course resembles Sonoma, but it doesn't feel like Sonoma"; "Our pit lane looks nothing like Sonoma";
"the building agent should model the actual grand stands"; "Use recent video as a benchmark". The OSM boxes of the
grandstand, the pit and paddock garages, the pit-exit building, the T12 building and the fuel canopy are replaced by the
parametric structure kit (plain colours, no logos, no imagery). Precedence for looks: 2026 onboard RAZip6S84CM > 2025
pit-lane video 24of8fjjAug > 2026 captures > Street View (2011 / 2017). Heights: lidar 2022-24, DSM - DEM profiles across
each outline every 2 m (method below), cross-checked with HEIGHTS.md storeys.

| structure | footprint source | heights and method | look (source) |
|---|---|---|---|
| Main grandstand (replaces OSM 262082790, a 9.3 m block) | front line of the block-wall base, 145 m, fitted on the seat field of c20_s1595..s1760 (141 x 31 m in plan, axis -38.8 deg); OSM outline 144 m | lidar profile across the outline: seats 2.0 m at the front to 12.0 m 29 m back (31 rows of 0.9 m rising 0.307 m from 2.6 m; base 2.2 m); suites roof 24.0 m front, 26.2 m ridge, 23.2 m back; rear 20 m; deck floor 14 m (top row + 2 m), glass 15.2-21.6 m (two storeys); tower 29.8 m over t -52..-14 m (lidar 29.5-30.1 m) | sand seats, grey deck, dark glass, green tower with blue glass (onboard 2:15); 13 aisle heads at 11 m (captures); steel stairs at both ends (24of8fjjAug 4:56, owner_22); plain white / blue base panels (owner_22, 2017); 4 light clusters on the roof (owner_22, onboard 2:15; positions along the roof approximate) |
| Pit garages north / south (OSM 1019835464, 1019837060) | OSM rectangles 74.6 x 12.8 m, 75.5 x 13.0 m | lidar: eaves 3.9-4.5 m (4.3), ridge 7.0-7.1 m | tan stucco, GREEN metal roofs (onboard 2:04-2:08, 2026; the 2026 captures show the roofs dark, the onboard shows green), red trim band (owner_20, 2011), window row on the lane side (onboard 2:05), roll-up doors on the paddock side (24of8fjjAug 24:40) |
| Paddock garages west / south (OSM 1019836533, 1019836718) | OSM rectangles 54.4 x 16.8, 56.2 x 21.4 m | lidar: eaves 5.0 m, ridge 7.7-7.8 m | tan, green roofs (NAIP; 24of8fjjAug 24:30-24:40 grey-green) |
| Pit-exit building (OSM 1019839174) | OSM 29.1 x 29.0 m | lidar: mono-pitch roof 4.2 m (paddock side) to 8.2 m (track side) | grey ribbed walls and roof, RED roof edge, glazed track side (onboard 0:04; c20_s1870 grey roof with a red edge; owner_25, 2011, red curved roof line) |
| T12 two-storey building (OSM 1019836595) | OSM 32.2 x 14.0 m | 2 storeys x 3.2 m + 0.5 m parapet = 8.4 m (HEIGHTS.md example 8); lidar flat 8.3-8.9 m | tan, window bands (onboard 2:12; Street View QduY6QTXmw4JDevQVE_b-g) |
| Fuel island (OSM 1019838109) | OSM 15.2 x 6.9 m | lidar: canopy edges 5.6-6.0 m, hip top 6.9 m (canopy 4.8 + fascia 0.9 + hip 1.2); pylon 9 m against the 21 m mast beside it | cream canopy, grey-green hip roof (24of8fjjAug 24:30); plain blue pylon with a yellow panel (no logo) |
| 28 light masts | isolated lidar spikes (DSM - DEM > 15 m, local max, ring median low), each checked on a 28 x 28 m capture window: lamp head displaced along the view and a long shadow to the north-west (c20_s1760 ... c20_s1485, listed in the config `src`); two on the T7a hill outside the captures (Street View J6fsnW4hj4xCjQLzrgRGzA) | spike height - 0.7 m (the kit's head top): 18.2-27.4 m | grey poles, 3 x 2 lamp heads facing the nearest track point |
| Pit wall boards | the pit-side barrier between s 3960 and 4098, found by side and lateral 4-15 m (robust to wall edits) | 0.85 m panels on the 1.1 m wall | blue (24of8fjjAug 4:48), green at the line (onboard 2:15) |
| Pit-box lines | straightened strip of the 2026 captures along the pit lane, peaks of the white-line brightness: three runs (317-388, 504-619, 634-705 m from the pit-in), pitch 8.95 / 8.84 / 8.85 m, box front line 6.6 m and the box wall 11.5 m off the lane centre | painted, 0.12 m | white |
| Terrace dressing (above T2, T3a-T4, T7a hill, back straight / 9a) | the existing terrace rows (rule unchanged) | bench strips 0.4 m on each row, seated on the drawn terrain | stair aisles with hand rails every 40-45 m (onboard 0:14-0:16, 0:26-0:30, 1:12-1:14, 1:30-1:34; positions along the rows not measured); shade roofs on top above T2 (one, at the far end) and on the back straight (two; onboard 1:32-1:34, positions approximate) |

Suppressed OSM boxes (logged by the build): 262082790, 1019835464, 1019837060, 1019836595, 1019838109, 1019839174,
1019836533, 1019836718. No lidar box or tree stood inside a structure outline.

Coverage gate, building / stand / mast rows (report only; the gate fails on the scenery round's kinds): MISSING mast 29 ->
20, stand 15 -> 12, building 4 -> 4; UNSUPPORTED building 12 -> 11 (none of the structures is unsupported). Still missing:
the pit-exit building rows at s 91 and 4092 (the building stands at s 160-190, seen ahead), the drag-strip masts on the
right of the front straight (no lidar spike and no capture shadow found), the T10-T11 infield grandstand and buildings
(s 2854-3119 right, 3259 right), the T12 control tower beyond the drag strip (s 3910 right).

Not sourced / not built: the drag-strip masts; fences (the scenery round's); the dark scoring pylon at the Carousel
(s 1584, a 28 m lidar spike with a solid shadow: not a mast); the hospitality building OSM 1363693902 stays an OSM box.
Finding for the terrace rule (not changed here): the T2 terrace starts ~30 m up the bank in the sim; the onboard (0:14)
shows the rows from the catch fence at the foot of the bank.
