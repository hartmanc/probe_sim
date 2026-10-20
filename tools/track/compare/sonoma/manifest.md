# Sonoma: scenery evidence manifest (rederive run, 20 Oct 2026)

Built by the build-track skill from a clean config: inventory (`inventory.md`), Street View survey (`streetview.md`),
clean z20 captures (`satellite_clean/`, 80 captures, common shift 0.00 / +0.45 m), the March 2026 Lemons onboard
RAZip6S84CM and the 2025 pit-lane video 24of8fjjAug (frames only, headless Chrome, never downloaded), OSM and the
2022-24 lidar. Every config entry carries its `src`; the generated tables below list each object and each inventory
row's outcome. Round r1 = this run.

## Method per kind (SKILL stage 3)

- **Walls, tyre walls, fences** (3.4): every band was picked with `compare/wall_measure.py` (edge mode or a guide read
  off `capstrip.py` strips), checked on capstrip / capwin overlays, and confirmed on the onboard; rms and pick rate in
  each `src`. Heights by HEIGHTS.md methods (`h_src`); unread heights say `unmeasured`.
- **Kerbs** (3.3): `kerb_detect.py` (95 candidates) confirmed strip by strip on the capture strips (trailers parked on
  the edge make many grey false runs: rejected) and on the onboard; colour per strip from the frame named in
  `colour_src`; T5 inside is plain yellow (onboard 0:42).
- **Pit lane** (3.5): OSM lane, three declared walls (pit wall, pit-in outer board wall, pit-out wall), cones on the
  measured double-yellow blend line, edge line cut there, impact block at the pit-in nose.
- **Closed roads** (3.6): Chute, 2020 bypass, short T7, PWC lower hairpin, T11a, drag strip; cones only at the bypass
  mouth (onboard 1:32), delineators at the Chute and short-T7 mouths; open runoff listed in `gates.allowed` with the
  frame that shows it open.
- **Stands** (3.7): four terraces by `terrace_measure.py` ray mode (T2, T3a-T4, back straight, main grandstand).
- **Buildings**: robust lidar heights; each kept building cites a capture or the onboard row it was seen at
  (`building_evidence`); 11 with no 2026 source are dropped.
- **Masts**: 26 isolated lidar spikes (DSM - DEM 19-28 m) inside the capture coverage.

## Movable barriers

- `tyre_stacks` at s 2180 / 2192 left (onboard 1:14): loose black tyre stacks on the paddock edge left of T7. **movable**.

## Removed for lack of evidence

| object | why |
|---|---|
| T9 left wall (s 2559-2700, wall_measure bright) | the picks followed parked trailer edges on c20_s0165/s0220 (cw window, 20 Oct): not a wall; L1 dark wall covers the place |
| OSM armco rule on 380830042 / 380830043 | re-kinded to dark concrete on the capture's dark band (osm_barrier_overrides) |
| 11 buildings (lidar blobs at T2-T3 and behind the paddock, OSM sheds 90-270 m off) | no 2026 capture covers them and the onboard does not show them |
| Street View 2011 items (blue/white kerbs, yellow/blue T11 stacks, 2011 board names) | the 2026 onboard contradicts them (streetview.md) |

## Scans and captures examined

| scan | captures |
|---|---|
| left / right bands 0-650 | c20_s1595..s1980, c20_s2035..s2365 |
| T3-T4 | c20_s2420..s2750 |
| T5-Carousel | c20_s2750..s3410 |
| T6-T7 road, T7, T7a | c20_s3465..s4070 |
| T8-T9a | c20_s0055..c20_o0715 |
| T10-T12 | c20_s0715..s1540 |
| pit lane, front straight | c20_s1100..s1925 |

## Dispositions (SKILL 3.13)

| kind | side | s (m) | what | source | disposition |
|---|---|---|---|---|---|
| building | left | 112.8 | pit-out buildings, red roofs | onboard:RAZip6S84CM@4.0 | placed: pit-out building (the garage structure on OSM 1019839174 at s 176, seen ahead at 0:04 and abeam at 2:22) |
| cone_line | right | 2731.6 | orange cones at the bypass mouth | onboard:RAZip6S84CM@92.0 | placed: closed road 2020 bypass mouth (the mouth at s 2802; the 1:32 frame sees the cones ahead) |
| mast | right | 2280.9 | light mast | onboard:RAZip6S84CM@77.0 | placed: lidar spike s 2345.7 (the mast seen ahead right at 1:17-1:18) |
| mast | right | 2452.1 | light mast | onboard:RAZip6S84CM@84.0 | placed: lidar spike s 2421.6 (seen ahead right at 1:24) |
| stand | left | 371.7 | hillside terrace (T2) | onboard:RAZip6S84CM@12.0 | placed: terrace T2 terrace (seen ahead at 0:12; its measured front starts at s ~390) |
| stand | left | 2662.9 | back-straight terrace | onboard:RAZip6S84CM@90.0 | placed: terrace back-straight terrace (seen ahead at 1:30) |
| stand | left | 3966.8 | main grandstand | onboard:RAZip6S84CM@134.0 | placed: main grandstand (the grandstand structure, front at s 3995-7, seen across the pit lane at 2:14) |
| station | right | 401.0 | marshal post (white hut) | onboard:RAZip6S84CM@13.5 | placed: T2 post (at s 416 on c20_s2145, 15 m past the mapped row) |
| station | right | 805.0 | marshal tower (white hut on legs) | onboard:RAZip6S84CM@27.5 | placed: T3a tower (at s 830 on c20_s2530; the row's time map is +-25 m here) |
| tyre_stack | left | 836.7 | black tyre stacks at the terrace foot | onboard:RAZip6S84CM@29.0 | not resolvable: c20_s2475, c20_s2530 examined: the dark band at the terrace foot is the Jersey and its shadow (placed as the T3a Jersey); no free-standing stack can be told apart |

## Height mismatches (coverage gate, advisory) explained

| row | why |
|---|---|
| wall left s 3548, Jersey 0.81 m vs package 5.3 m | two walls at that station: the pit-in Jersey (0.81 m, part of `pit wall`) and the board wall 5.3 m behind it; the gate compares the row with the nearest left wall, the board wall |
| wall left s 3655, Street View 5.22 m vs package 1 m | the same pair at T11: the row is the board wall (Street View), the nearest object is the pit-wall Jersey; the board wall stands at 5.3 m |

## Judge round r1 findings dispositioned (judge_r1.md)

| finding | disposition |
|---|---|
| S/F chequered stripe and SONOMA RACEWAY ground logo; T11 infield ground logos (C15) | not placed this run: the 3.9 ground-logo scan of the whole lap was not done; owner list |
| pit side of the pit-in board wall (GENERAL TIRE, tyre stacks along the lane) | not placed: only one pit-in frame (24of8fjjAug 23:56) was captured; owner list |
| T3a and T7 tower shape (kit hut) | kit limitation (open tower on tall legs); owner list |
| grandstand tone, panel widths, T5 wall gaps, bypass cones as a line | accepted as OK_DIFFERENT |

## Generated tables
### Scenery objects of the checked kinds (116, from public/tracks/sonoma)

| # | kind | side | s (m) | out (m) | object | source |
|---|---|---|---|---|---|---|
| 1 | wall | right | 705-829 | 31-41 | barrier 0 (concrete) | osm:380830042 (dark wall line on c20_s2530/s2585 (wall_measure dark, rms 1.08 m) on the T3a outside) |
| 2 | wall | right | 822-976 | 12-35 | barrier 1 (concrete) | osm:380830043 (dark wall line on c20_s2585..s2750 (wall_measure dark, rms 1.08 m) on the T3a-T4 outside) |
| 3 | wall | left | 3563-85 (wraps) | 1-4 | barrier 2 (concrete) | declared: pit wall (wall_measure bright along the left edge on c20_s1155..s1265 (pit-in Jersey from s 3545, rms 0.28 m), c20_s1320..s1595 (T11-T12, rms 0.38 m), c20_s1595..s1870 (pit straight, rms 0.30 m, 99 % picked); onboard 1:56-2:16, 0:00-0:04; nose at s 92 (c20_s1870)) |
| 4 | tyre_wall | left | 3645-3711 | 1-3 | barrier 3 (tyres) | declared: T11 white tyres (wall_measure bright band on c20_s1265/s1320 (rms 0.44 m); onboard 2:04 (t124): white-wrapped stacked tyres on the T11 outside wall) |
| 5 | wall | left | 3470-3656 | 2-10 | barrier 4 (concrete) | declared: pit-in outer wall (wall_measure bright on c20_s1100..s1265 (the shed face beside the pit-in lane, rms 0.54 m, 32 % picked); onboard 1:56-2:00, pit-lane video 23:56) |
| 6 | wall | left | 90-269 | 2-13 | barrier 5 (concrete + 3 m fence) | declared: pit-out wall (wall_measure bright on c20_s1815..s1980 (rms 0.9-1.4 m); onboard 0:06 (t006) wall with catch fence; pit-lane video 5:02-5:06 O'Reilly boards, catch fence) |
| 7 | fence | left | 90-269 | 2-13 | barrier 5 (concrete + 3 m fence) catch fence | declared: pit-out wall (wall_measure bright on c20_s1815..s1980 (rms 0.9-1.4 m); onboard 0:06 (t006) wall with catch fence; pit-lane video 5:02-5:06 O'Reilly boards, catch fence) |
| 8 | wall | right | 3934-91 (wraps) | 2-4 | barrier 6 (concrete) | declared: drag-strip wall (wall_measure bright on c20_s1595..s1870 (rms 0.47 m, 95 % picked); onboard 2:14-0:04 right) |
| 9 | tyre_wall | right | 3929-3934 | 3-5 | barrier 7 (tyres) | declared: T12 right head tyres (onboard 2:11.5 (d131.5): white tyre stacks at the head of the right-hand (drag-strip) wall; on the measured wall line (c20_s1540)) |
| 10 | wall | right | 157-184 | 9-33 | barrier 8 (concrete) | declared: T1 runoff wall (wall_measure bright on c20_s1870/s1925 (rms 0.19 m, 68 % picked): the line between the T1 runoff and the drag strip) |
| 11 | tyre_wall | right | 220-263 | 10-31 | barrier 9 (tyres) | declared: T1 tyre arc (wall_measure dark on c20_s1925/s1980 (rms 1.17 m): the black tyre arc on the T1-T2 outside) |
| 12 | tyre_wall | left | 245-555 | 2-19 | barrier 10 (tyres + 2.5 m fence) | declared: T2 tyre wall (wall_measure dark band on c20_s1980..s2200 (rms 1.56-1.86 m); onboard 0:08-0:18 left, catch fence along the terrace foot) |
| 13 | fence | left | 245-555 | 2-19 | barrier 10 (tyres + 2.5 m fence) catch fence | declared: T2 tyre wall (wall_measure dark band on c20_s1980..s2200 (rms 1.56-1.86 m); onboard 0:08-0:18 left, catch fence along the terrace foot) |
| 14 | tyre_wall | right | 1510-1614 | 21-29 | barrier 11 (tyres) | declared: Carousel exit right tyres (wall_measure dark on c20_s3355/s3410 (rms 1.82 m); onboard 0:54 (t054) dark tyre lines far right) |
| 15 | wall | left | 725-944 | 6-13 | barrier 12 (concrete + 2.5 m fence) | declared: T3a Jersey (wall_measure dark band (Jersey and its shadow) on c20_s2475..s2585 (rms 1.09 m); onboard 0:29-0:32 left) |
| 16 | fence | left | 725-944 | 6-13 | barrier 12 (concrete + 2.5 m fence) catch fence | declared: T3a Jersey (wall_measure dark band (Jersey and its shadow) on c20_s2475..s2585 (rms 1.09 m); onboard 0:29-0:32 left) |
| 17 | wall | right | 1062-1485 | 3-23 | barrier 13 (concrete) | declared: T5 wall (wall_measure bright on c20_s2750..s3080 (rms 0.47 m, 67 % picked); onboard 0:38-0:48 right, at the bank foot) |
| 18 | tyre_wall | left | 1091-1161 | 1-26 | barrier 14 (tyres) | declared: T5 inside tyres (wall_measure dark band on c20_s2805/s2860 (rms 1.17 m); onboard 0:40 (t040) left) |
| 19 | tyre_wall | left | 1699-1713 | 2-2 | barrier 15 (tyres) | declared: T6-T7 head (onboard 0:58 (t058): the T6-T7 wall starts with a dark section; its first 12 m on the measured line (c20_s3465)) |
| 20 | wall | left | 1713-2149 | 1-3 | barrier 16 (concrete) | declared: T6-T7 wall (wall_measure bright along the left edge on c20_s3465..s3905 (rms 0.37 m, 72 % picked); onboard 0:58-1:12 left) |
| 21 | wall | right | 2345-2625 | 1-9 | barrier 17 (concrete) | declared: T8 right wall (wall_measure bright on c20_s4070..s0220 (rms 0.58-0.72 m); onboard 1:20-1:26 right) |
| 22 | wall | left | 2470-2595 | 13-19 | barrier 18 (concrete) | declared: T8a left dark wall (wall_measure dark band on c20_s0110..s0275 (rms 0.71 m); onboard 1:26 left, far) |
| 23 | wall | left | 2690-2805 | 12-18 | barrier 19 (concrete + 3.5 m fence) | declared: back straight dark wall (wall_measure dark band on c20_s0330..s0440 (rms 0.79 m); onboard 1:30-1:32 dark wall at the terrace foot, catch fence) |
| 24 | fence | left | 2690-2805 | 12-18 | barrier 19 (concrete + 3.5 m fence) catch fence | declared: back straight dark wall (wall_measure dark band on c20_s0330..s0440 (rms 0.79 m); onboard 1:30-1:32 dark wall at the terrace foot, catch fence) |
| 25 | wall | left | 2805-3040 | 6-13 | barrier 20 (concrete + 3.5 m fence) | declared: back straight wall (wall_measure bright on c20_o0440..c20_o0715 (rms 0.61 m, 58 % picked); onboard 1:32-1:40 left, catch fence 3.5 m posts) |
| 26 | fence | left | 2805-3040 | 6-13 | barrier 20 (concrete + 3.5 m fence) catch fence | declared: back straight wall (wall_measure bright on c20_o0440..c20_o0715 (rms 0.61 m, 58 % picked); onboard 1:32-1:40 left, catch fence 3.5 m posts) |
| 27 | wall | left | 3124-3462 | 7-16 | barrier 21 (concrete) | declared: T10 board wall (wall_measure bright on c20_s0715..s1100 (rms 0.61 m, 76 % picked); onboard 1:44-1:56 left, board panels to the top) |
| 28 | wall | right | 3092-3462 | 1-9 | barrier 22 (concrete + 4 m fence) | declared: T10 right wall (wall_measure bright on c20_s0715..s1100 (rms 0.71 m, 45 % picked); onboard 1:44-1:54 right, catch fence 4 m (HEIGHTS ex. 6)) |
| 29 | fence | right | 3092-3462 | 1-9 | barrier 22 (concrete + 4 m fence) catch fence | declared: T10 right wall (wall_measure bright on c20_s0715..s1100 (rms 0.71 m, 45 % picked); onboard 1:44-1:54 right, catch fence 4 m (HEIGHTS ex. 6)) |
| 30 | tyre_wall | right | 3344-3409 | 2-5 | barrier 23 (tyres) | declared: T10 exit tyres (onboard 1:54 (t114): black stacked tyres along the right fence; on the measured wall line (c20_s1045)) |
| 31 | fence | left | 427-565 | 52-69 | barrier 24 (fence + 1.8 m fence) | terrace T2 terrace top fence (terrace_measure.py ray mode on c20_s2035..s2310 (55 rays, row pitch 1.17 m, OSM 1414701939 fill); onboard 0:12-0:18 left) |
| 32 | fence | left | 782-985 | 38-57 | barrier 25 (fence + 1.8 m fence) | terrace T3a-T4 terrace top fence (terrace_measure.py ray mode on c20_s2420..s2750 (77 rays, row pitch 1.25 m, OSM 1414701938 fill); onboard 0:26-0:34 left) |
| 33 | fence | left | 2721-3013 | 39-57 | barrier 26 (fence + 1.8 m fence) | terrace back-straight terrace top fence (terrace_measure.py ray mode on c20_s0330..c20_o0715 (100 rays, row pitch 1.15 m, OSM 1414701936 fill); onboard 1:30-1:40 left) |
| 34 | kerb | right | 117-130 | 0-0 | kerb 116.7-129.7 | T1 exit right a: kerb_detect.py runs [50] (s 117-130) on c20_s1870; colour: onboard 0:05.5 (d005.5): red/white |
| 35 | kerb | right | 162-179 | 0-0 | kerb 161.6-178.6 | T1 exit right b: kerb_detect.py runs [52] (s 162-179) on c20_s1870, c20_s1925; colour: onboard 0:05.5 (d005.5): red/white |
| 36 | kerb | right | 204-220 | 0-0 | kerb 203.5-219.5 | T1 exit right c: kerb_detect.py runs [53] (s 204-220) on c20_s1925; colour: colour unverified: no local frame (onboard 0:06-0:07 shows the white line only; assumed red/white like its neighbours) |
| 37 | kerb | left | 329-373 | 0-0 | kerb 329.3-373.2 | T2 approach left: kerb_detect.py runs [3] (s 329-373) on c20_s2035, c20_s2090; colour: onboard 0:10 (t010): red/white |
| 38 | kerb | right | 412-451 | 0-0 | kerb 412.1-451 | T2 apex right: kerb_detect.py runs [55, 56] (s 412-451) on c20_s2145, c20_s2200; colour: onboard 0:13-0:14.5 (d013, t014): red/white |
| 39 | kerb | left | 435-613 | 0-0 | kerb 435-612.6 | T2 exit left: kerb_detect.py runs [5, 6, 7, 8, 10, 11] (s 435-613) on c20_s2145, c20_s2200, c20_s2255, c20_s2310, c20_s2365; colour: onboard 0:15.5-0:16 (d015.5, t016): red/white |
| 40 | kerb | left | 694-736 | 0-0 | kerb 694.4-736.3 | T3 apex left: kerb_detect.py runs [12] (s 694-736) on c20_s2420, c20_s2475; colour: onboard 0:23.5-0:24.5 (d023.5, t024): red/white |
| 41 | kerb | right | 781-814 | 0-0 | kerb 781.2-814.2 | T3a apex right: kerb_detect.py runs [63] (s 781-814) on c20_s2530; colour: onboard 0:27 (d027): red/white |
| 42 | kerb | left | 846-937 | 0-0 | kerb 846.1-936.9 | T3a-T4 left: kerb_detect.py runs [13] (s 846-937) on c20_s2585, c20_s2640, c20_s2695; colour: onboard 0:30-0:32 (t030, t032): red/white |
| 43 | kerb | right | 996-1028 | 0-0 | kerb 995.8-1027.7 | T4 apex right: kerb_detect.py runs [65] (s 996-1028) on c20_s2750; colour: onboard 0:35.5-0:36 (d035.5, t036): red/white |
| 44 | kerb | left | 1027-1094 | 0-0 | kerb 1026.7-1093.5 | T4 exit left: kerb_detect.py runs [14] (s 1027-1094) on c20_s2750, c20_s2805, c20_s2860; colour: onboard 0:37-0:38 (d037, t038): red/white |
| 45 | kerb | right | 1154-1279 | 0-0 | kerb 1154.4-1279.1 | T5 inside: kerb_detect.py runs [66, 67, 68] (s 1154-1279) on c20_s2860, c20_s2915, c20_s2970, c20_s3025; colour: onboard 0:41.5-0:43 (d041.5, t042): a plain yellow strip on the inside |
| 46 | kerb | left | 1591-1646 | 0-0 | kerb 1591.4-1646.3 | Carousel exit left: kerb_detect.py runs [21] (s 1591-1646) on c20_s3355, c20_s3410; colour: onboard 0:54-0:56 (t054, t056): red/white |
| 47 | kerb | right | 1721-1796 | 0-0 | kerb 1721.1-1796 | T6-T7 right: kerb_detect.py runs [70] (s 1721-1796) on c20_s3465, c20_s3520; colour: onboard 1:00 (t060): red/white |
| 48 | kerb | right | 2172-2201 | 0-0 | kerb 2172.1-2201.1 | T7 apex right: kerb_detect.py runs [71, 72] (s 2172-2201) on c20_s3905, c20_s3960; colour: onboard 1:12.5-1:13 (d072.5, d073): red/white |
| 49 | kerb | right | 2244-2292 | 0-0 | kerb 2244-2291.9 | T7a island: island kerb on c20_s3960/s4015 (the white-block ring round the island; kerb_detect misses it, it lies beyond the fitted edge band); colour: onboard 1:16.5-1:17 (d076.5, d077): red/white |
| 50 | kerb | left | 2300-2372 | 0-0 | kerb 2299.8-2371.7 | T8 approach left: kerb_detect.py runs [25, 26] (s 2300-2372) on c20_s0000, c20_s4015, c20_s4070; colour: onboard 1:18-1:20 (t078, t080): red/white |
| 51 | kerb | left | 2418-2454 | 0-0 | kerb 2417.6-2454.5 | T8 apex left: kerb_detect.py runs [27, 28] (s 2418-2454) on c20_s0055, c20_s0110; colour: onboard 1:22.5 (d082.5): red/white |
| 52 | kerb | right | 2479-2537 | 0-0 | kerb 2479.4-2537.3 | T8a apex right: kerb_detect.py runs [77, 78] (s 2479-2537) on c20_s0110, c20_s0165; colour: onboard 1:25-1:25.5 (d085, d085.5): red/white |
| 53 | kerb | left | 2600-2645 | 0-0 | kerb 2600.2-2645.1 | T9 approach left: kerb_detect.py runs [31] (s 2600-2645) on c20_s0220, c20_s0275; colour: onboard 1:28 (t088): red/white |
| 54 | kerb | right | 2692-2740 | 0-0 | kerb 2692-2739.8 | T9 apex right: kerb_detect.py runs [80] (s 2692-2740) on c20_s0330, c20_s0385; colour: onboard 1:30-1:31 (t090, d091): red/white |
| 55 | kerb | right | 3021-3076 | 0-0 | kerb 3021.2-3076.1 | 9a right: kerb_detect.py runs [85, 86] (s 3021-3076) on c20_o0660, c20_o0715; colour: onboard 1:40 (t100): red/white |
| 56 | kerb | left | 3060-3170 | 0-0 | kerb 3060.1-3169.9 | 9a left: kerb_detect.py runs [38] (s 3060-3170) on c20_o0715, c20_s0715, c20_s0770; colour: onboard 1:41.5-1:42 (d101.5, t102): red/white |
| 57 | kerb | right | 3220-3293 | 0-0 | kerb 3219.8-3292.6 | T10 apex right: kerb_detect.py runs [87] (s 3220-3293) on c20_s0825, c20_s0880, c20_s0935; colour: onboard 1:49.5-1:50 (d109.5, t110): red/white |
| 58 | kerb | left | 3339-3402 | 0-0 | kerb 3338.5-3402.4 | T10 exit left: kerb_detect.py runs [42, 43] (s 3338-3402) on c20_s0990, c20_s1045; colour: colour unverified: no local frame (onboard 1:52-1:54 look right, the strip is not in view) |
| 59 | kerb | right | 3629-3731 | 0-0 | kerb 3628.8-3730.6 | T11 apex right: kerb_detect.py runs [91, 92] (s 3629-3731) on c20_s1265, c20_s1320, c20_s1375; colour: onboard 2:02-2:04.5 (t122, d123, t124): red/white |
| 60 | station | right | 416-416 | 3-3 | marshal 'T2 post' | onboard 0:13.5 (d013.5) white hut at the T2 apex; its roof and shadow on c20_s2145 (inside, right) |
| 61 | station | right | 830-830 | 2-2 | marshal 'T3a tower' | onboard 0:25-0:28 white tower on legs right; roof and shadow on c20_s2530 |
| 62 | station | left | 2153-2153 | 4-4 | marshal 'T7 tower' | onboard 1:11.5-1:12.5 (d071.5, t072) white tower behind the wall left; roof and shadow on c20_s3850 |
| 63 | tyre_stack | right | 3046-3046 | 2-2 | tyres '' | onboard 1:40 (t100): a two-tyre stack right of the 9a kerb; place on c20_o0715 |
| 64 | tyre_stack | left | 2180-2180 | 3-3 | tyres '' | onboard 1:14 (t074): black tyre stacks along the paddock edge left of T7 (movable); c20_s3905 s 2180 |
| 65 | tyre_stack | left | 2192-2192 | 3-3 | tyres '' | onboard 1:14 (t074): black tyre stacks along the paddock edge left of T7 (movable); c20_s3905 s 2192 |
| 66 | tyre_stack | right | 3662-3662 | 1-1 | block '' | onboard 2:02-2:04 (t122, t124): red/white striped blocks at the T11 apex; white blocks on c20_s1320 s 3662 |
| 67 | tyre_stack | right | 3692-3692 | 1-1 | block '' | onboard 2:02-2:04 (t122, t124): red/white striped blocks at the T11 apex; white blocks on c20_s1320 s 3692 |
| 68 | mast | left | 45-45 | 33-33 | mast '' | lidar spike s 44.9 (DSM - DEM 21.8 m, isolated, lidar_grids); base and shadow on c20_s1760; light masts on the onboard throughout |
| 69 | mast | left | 117-117 | 25-25 | mast '' | lidar spike s 116.7 (DSM - DEM 21.6 m, isolated, lidar_grids); base and shadow on c20_s1815; light masts on the onboard throughout |
| 70 | mast | left | 180-180 | 16-16 | mast '' | lidar spike s 179.6 (DSM - DEM 24.7 m, isolated, lidar_grids); base and shadow on c20_s1870; light masts on the onboard throughout |
| 71 | mast | right | 1609-1609 | 69-69 | mast '' | lidar spike s 1609.4 (DSM - DEM 21.5 m, isolated, lidar_grids); base and shadow on c20_s3355; light masts on the onboard throughout |
| 72 | mast | right | 1689-1689 | 44-44 | mast '' | lidar spike s 1689.2 (DSM - DEM 21.9 m, isolated, lidar_grids); base and shadow on c20_s0440; light masts on the onboard throughout |
| 73 | mast | right | 1737-1737 | 27-27 | mast '' | lidar spike s 1737.1 (DSM - DEM 21.9 m, isolated, lidar_grids); base and shadow on c20_s3465; light masts on the onboard throughout |
| 74 | mast | left | 2237-2237 | 37-37 | mast '' | lidar spike s 2237.0 (DSM - DEM 21.5 m, isolated, lidar_grids); base and shadow on c20_s4015; light masts on the onboard throughout |
| 75 | mast | right | 2346-2346 | 22-22 | mast '' | lidar spike s 2345.7 (DSM - DEM 21.6 m, isolated, lidar_grids); base and shadow on c20_s0000; light masts on the onboard throughout |
| 76 | mast | right | 2422-2422 | 7-7 | mast '' | lidar spike s 2421.6 (DSM - DEM 21.7 m, isolated, lidar_grids); base and shadow on c20_s0055; light masts on the onboard throughout |
| 77 | mast | right | 2492-2492 | 15-15 | mast '' | lidar spike s 2492.4 (DSM - DEM 21.1 m, isolated, lidar_grids); base and shadow on c20_s0110; light masts on the onboard throughout |
| 78 | mast | right | 2573-2573 | 10-10 | mast '' | lidar spike s 2573.2 (DSM - DEM 18.9 m, isolated, lidar_grids); base and shadow on c20_s0220; light masts on the onboard throughout |
| 79 | mast | right | 2633-2633 | 14-14 | mast '' | lidar spike s 2633.1 (DSM - DEM 21.6 m, isolated, lidar_grids); base and shadow on c20_s0275; light masts on the onboard throughout |
| 80 | mast | right | 2861-2861 | 65-65 | mast '' | lidar spike s 2860.6 (DSM - DEM 22.1 m, isolated, lidar_grids); base and shadow on c20_s0550; light masts on the onboard throughout |
| 81 | mast | right | 2921-2921 | 70-70 | mast '' | lidar spike s 2921.4 (DSM - DEM 21.7 m, isolated, lidar_grids); base and shadow on c20_s0550; light masts on the onboard throughout |
| 82 | mast | right | 2980-2980 | 69-69 | mast '' | lidar spike s 2980.3 (DSM - DEM 21.8 m, isolated, lidar_grids); base and shadow on c20_s0605; light masts on the onboard throughout |
| 83 | mast | right | 3081-3081 | 36-36 | mast '' | lidar spike s 3081.1 (DSM - DEM 21.6 m, isolated, lidar_grids); base and shadow on c20_s0660; light masts on the onboard throughout |
| 84 | mast | right | 3106-3106 | 19-19 | mast '' | lidar spike s 3106.0 (DSM - DEM 24.6 m, isolated, lidar_grids); base and shadow on c20_s0715; light masts on the onboard throughout |
| 85 | mast | right | 3157-3157 | 27-27 | mast '' | lidar spike s 3156.9 (DSM - DEM 28.0 m, isolated, lidar_grids); base and shadow on c20_s0825; light masts on the onboard throughout |
| 86 | mast | right | 3321-3321 | 43-43 | mast '' | lidar spike s 3320.5 (DSM - DEM 28.0 m, isolated, lidar_grids); base and shadow on c20_s0935; light masts on the onboard throughout |
| 87 | mast | right | 3368-3368 | 14-14 | mast '' | lidar spike s 3368.4 (DSM - DEM 27.7 m, isolated, lidar_grids); base and shadow on c20_s0990; light masts on the onboard throughout |
| 88 | mast | left | 3477-3477 | 4-4 | mast '' | lidar spike s 3477.2 (DSM - DEM 24.9 m, isolated, lidar_grids); base and shadow on c20_s1100; light masts on the onboard throughout |
| 89 | mast | left | 3715-3715 | 36-36 | mast '' | lidar spike s 3714.7 (DSM - DEM 21.7 m, isolated, lidar_grids); base and shadow on c20_s1320; light masts on the onboard throughout |
| 90 | mast | left | 3755-3755 | 42-42 | mast '' | lidar spike s 3754.6 (DSM - DEM 21.7 m, isolated, lidar_grids); base and shadow on c20_s1375; light masts on the onboard throughout |
| 91 | mast | left | 3805-3805 | 41-41 | mast '' | lidar spike s 3805.5 (DSM - DEM 21.8 m, isolated, lidar_grids); base and shadow on c20_s1430; light masts on the onboard throughout |
| 92 | mast | left | 3854-3854 | 42-42 | mast '' | lidar spike s 3854.3 (DSM - DEM 21.8 m, isolated, lidar_grids); base and shadow on c20_s1485; light masts on the onboard throughout |
| 93 | mast | left | 3919-3919 | 24-24 | mast '' | lidar spike s 3919.2 (DSM - DEM 27.7 m, isolated, lidar_grids); base and shadow on c20_s1540; light masts on the onboard throughout |
| 94 | stand | left | 427-565 | 26-68 | terrace T2 terrace | terrace_measure.py ray mode on c20_s2035..s2310 (55 rays, row pitch 1.17 m, OSM 1414701939 fill); onboard 0:12-0:18 left |
| 95 | stand | left | 782-985 | 21-55 | terrace T3a-T4 terrace | terrace_measure.py ray mode on c20_s2420..s2750 (77 rays, row pitch 1.25 m, OSM 1414701938 fill); onboard 0:26-0:34 left |
| 96 | stand | left | 2721-3013 | 23-51 | terrace back-straight terrace | terrace_measure.py ray mode on c20_s0330..c20_o0715 (100 rays, row pitch 1.15 m, OSM 1414701936 fill); onboard 1:30-1:40 left |
| 97 | building | left | 3421-3658 | 20-129 | building 0 '' 4.5 m | osm (c20_s1210: roof and shadow on the 2026 capture (osm, 4.5 m, s 3602)) |
| 98 | building | left | 3830-3908 | 29-42 | building 1 '' 6.2 m | osm (c20_s1485: roof and shadow on the 2026 capture (osm, 6.2 m, s 3868)) |
| 99 | building | left | 3909-3963 | 18-42 | building 2 '' 8.7 m | osm (c20_s1540: roof and shadow on the 2026 capture (osm, 8.7 m, s 3935)) |
| 100 | building | left | 3745-3821 | 29-42 | building 3 '' 6.3 m | osm (c20_s1375: roof and shadow on the 2026 capture (osm, 6.3 m, s 3784)) |
| 101 | building | left | 3719-3728 | 32-41 | building 4 '' 6.5 m | osm (c20_s1320: roof and shadow on the 2026 capture (osm, 6.5 m, s 3723)) |
| 102 | building | left | 3478-3657 | 2-39 | building 5 '' 5.5 m | osm (c20_s1155: roof and shadow on the 2026 capture (osm, 5.5 m, s 3564)) |
| 103 | building | left | 3662-3692 | 22-64 | building 6 '' 4.7 m | osm (onboard 122.0 (glass-front building beyond the pit road): seen beside the track (osm, 4.7 m, s 3673)) |
| 104 | building | left | 3429-3446 | 63-69 | building 7 '' 3.6 m | lidar (c20_s1045: roof and shadow on the 2026 capture (lidar, 3.6 m, s 3438)) |
| 105 | stand | left | 3995-8 (wraps) | 33-60 | structure 0 grandstand 'main grandstand' | front and depth by terrace_measure.py ray mode on c20_s1540..s1760 (38 rays, seat field 17-26 m deep, row pitch 0.89 m); onboard 2:13-2:18 (t134-t136) and pit-lane video 4:48-4:52 (p288-p292): concrete bleachers with a glazed suites deck and a teal roof |
| 106 | building | left | 157-191 | 16-48 | structure 2 garage 'pit-out building' | OSM 1019839174 footprint; onboard 0:04 (t004) and pit-lane video 5:00 (p300): pale walls under a red roof |
| 107 | bridge | both | 295-295 | 0-0 | bridge 1382620985 (foot) deck 20.9 | lidar |
| 108 | cone_line | right | 2800-2804 | 0-1 | cone line 0 | closed road 2020 bypass mouth (onboard 1:32 (t092): orange cones across the bypass mouth (mouth on c20_s0385)) |
| 109 | cone_line | left | 985-1013 | 1-1 | cone line 1 | onboard 0:34 (t034): orange delineator pylons across the Chute mouth left (mouth on c20_s2695/s2750) |
| 110 | cone_line | right | 2182-2202 | 1-1 | cone line 2 | onboard 1:14-1:16 (t074, t076): orange delineator pylons at the short-T7 mouth right (c20_s3905/s3960) |
| 111 | cone_line | right | 2238-2250 | 1-1 | cone line 3 | onboard 1:16 (t076, d076.5): an orange delineator pylon at the island tip, the short-T7 mouth (c20_s3960) |
| 112 | cone_line | left | 2909-2910 | 1-2 | cone line 4 | onboard 1:36 (t096): a single orange marker cone on the left grass |
| 113 | cone_line | left | 3001-3002 | 2-2 | cone line 5 | onboard 1:38 (t098): a single orange marker cone on the left grass |
| 114 | cone_line | left | 3551-3612 | 0-1 | cone line 6 | onboard 1:58 (t118): orange cones along the pit-in separation line (c20_s1155) |
| 115 | cone_line | left | 3898-3910 | 1-1 | cone line 7 | onboard 2:12 (t132): orange cones at the SONOMA TURN 12 wall face (c20_s1540) |
| 116 | cone_line | left | 92-228 | -1-0 | cone line 8 | pit-lane video 24of8fjjAug 5:04 (p304): small yellow cones on the double yellow blend line; line measured on c20_s1815/s1870 (rms 0.13 m) |

### Every inventory row and its outcome (172 rows)

| s (m) | t | side | kind | what | source | outcome |
|---|---|---|---|---|---|---|
| 40 | 0:02.0 | left | wall | concrete pit wall | onboard:RAZip6S84CM@2.0 | covered by barrier 2 (concrete) |
| 40 | 0:02.0 | right | wall | concrete (drag-strip wall) | onboard:RAZip6S84CM@2.0 | covered by barrier 6 (concrete) |
| 81 | 2:20.0 | left | wall | concrete pit wall | onboard:RAZip6S84CM@140.0 | covered by barrier 2 (concrete); barrier 5 (concrete + 3 m fence) |
| 113 | 0:04.0 | left | building | pit-out buildings, red roofs | onboard:RAZip6S84CM@4.0 | MISSING, placed: pit-out building (the garage structure on OSM 1019839174 at s 176, seen ahead at 0:04 and abeam at 2:22) |
| 113 | 0:04.0 | left | wall | concrete pit wall | onboard:RAZip6S84CM@4.0 | covered by barrier 5 (concrete + 3 m fence) |
| 147 | 2:22.0 | left | building | red-roof building | onboard:RAZip6S84CM@142.0 | covered by structure 2 garage 'pit-out building' |
| 147 | 2:22.0 | left | wall | concrete pit wall | onboard:RAZip6S84CM@142.0 | covered by barrier 5 (concrete + 3 m fence) |
| 166 | 0:05.5 | right | kerb | kerb | onboard:RAZip6S84CM@5.5 | covered by kerb 161.6-178.6 |
| 186 | 0:06.0 | left | wall | concrete pit-out wall with catch fence | onboard:RAZip6S84CM@6.0 | covered by barrier 5 (concrete + 3 m fence) |
| 225 | 2:24.0 | left | wall | concrete pit-out wall | onboard:RAZip6S84CM@144.0 | covered by barrier 5 (concrete + 3 m fence) |
| 263 | 0:08.0 | both | boards | bridge banners | onboard:RAZip6S84CM@8.0 | surroundings (not a checked kind) |
| 263 | 0:08.0 | left | tyre_wall | tyre wall | onboard:RAZip6S84CM@8.0 | covered by barrier 10 (tyres + 2.5 m fence) |
| 263 | 0:08.0 | left | wall | Jersey stub | onboard:RAZip6S84CM@8.0 | covered by barrier 5 (concrete + 3 m fence) |
| 295 | 0:08.9 | ahead | bridge | footbridge | onboard:RAZip6S84CM@8.9 | covered by bridge 1382620985 (foot) deck 20.9 |
| 321 | 0:10.0 | left | kerb | kerb | onboard:RAZip6S84CM@10.0 | covered by kerb 329.3-373.2 |
| 321 | 0:10.0 | left | tyre_wall | tyre wall | onboard:RAZip6S84CM@10.0 | covered by barrier 10 (tyres + 2.5 m fence) |
| 372 | 0:12.0 | left | stand | hillside terrace (T2) | onboard:RAZip6S84CM@12.0 | MISSING, placed: terrace T2 terrace (seen ahead at 0:12; its measured front starts at s ~390) |
| 401 | 0:13.5 | right | station | marshal post (white hut) | onboard:RAZip6S84CM@13.5 | MISSING, placed: T2 post (at s 416 on c20_s2145, 15 m past the mapped row) (corrected in r1: 0 was s, 1 was i, 2 was d, 3 was e, 4 was  , 5 was l, 6 was e, 7 was f, 8 was t) |
| 405 |  | right | kerb | kerb | streetview:H9xspk4q_OoFIjVDhaMzDA@210 | covered by kerb 412.1-451 |
| 409 | 0:14.0 | left | fence | catch fence along the terrace foot | onboard:RAZip6S84CM@14.0 | covered by barrier 10 (tyres + 2.5 m fence) catch fence |
| 409 | 0:14.0 | left | tyre_wall | tyre wall | onboard:RAZip6S84CM@14.0 | covered by barrier 10 (tyres + 2.5 m fence) |
| 409 | 0:14.0 | right | kerb | kerb | onboard:RAZip6S84CM@14.0 | covered by kerb 412.1-451 |
| 454 | 0:16.0 | left | kerb | kerb | onboard:RAZip6S84CM@16.0 | covered by kerb 435-612.6 |
| 454 | 0:16.0 | left | stand | hillside terrace (T2) | onboard:RAZip6S84CM@16.0 | covered by terrace T2 terrace |
| 508 | 0:18.0 | left | tyre_wall | low dark barrier at the bank foot | onboard:RAZip6S84CM@18.0 | covered by barrier 10 (tyres + 2.5 m fence) |
| 574 | 0:20.0 | right | boards | boards on posts (brown/yellow) | onboard:RAZip6S84CM@20.0 | surroundings (not a checked kind) |
| 710 | 0:24.0 | left | kerb | kerb | onboard:RAZip6S84CM@24.0 | covered by kerb 694.4-736.3 |
| 801 | 0:27.3 | right | kerb | kerb | onboard:RAZip6S84CM@27.3 | covered by kerb 781.2-814.2 |
| 805 | 0:27.5 | right | station | marshal tower (white hut on legs) | onboard:RAZip6S84CM@27.5 | MISSING, placed: T3a tower (at s 830 on c20_s2530; the row's time map is +-25 m here) |
| 815 | 0:28.0 | left | stand | hillside terrace (T3a-T4) | onboard:RAZip6S84CM@28.0 | covered by terrace T3a-T4 terrace |
| 837 | 0:29.0 | left | tyre_stack | black tyre stacks at the terrace foot | onboard:RAZip6S84CM@29.0 | MISSING, not resolvable: c20_s2475, c20_s2530 examined: the dark band at the terrace foot is the Jersey and its shadow (placed as the T3a Jersey); no free-standing stack can be told apart |
| 861 | 0:30.0 | left | kerb | kerb | onboard:RAZip6S84CM@30.0 | covered by kerb 846.1-936.9 |
| 861 | 0:30.0 | left | wall | Jersey | onboard:RAZip6S84CM@30.0 | covered by barrier 12 (concrete + 2.5 m fence) |
| 917 | 0:32.0 | left | kerb | kerb | onboard:RAZip6S84CM@32.0 | covered by kerb 846.1-936.9 |
| 917 | 0:32.0 | left | wall | Jersey | onboard:RAZip6S84CM@32.0 | covered by barrier 12 (concrete + 2.5 m fence) |
| 974 | 0:34.0 | left | cone_line | delineator pylons across the Chute mouth | onboard:RAZip6S84CM@34.0 | covered by cone line 1 |
| 1009 | 0:36.0 | left | boards | O'Reilly board run across the infield | onboard:RAZip6S84CM@36.0 | surroundings (not a checked kind) |
| 1009 | 0:36.0 | right | kerb | kerb | onboard:RAZip6S84CM@36.0 | covered by kerb 995.8-1027.7 |
| 1053 | 0:38.0 | left | kerb | kerb | onboard:RAZip6S84CM@38.0 | covered by kerb 1026.7-1093.5 |
| 1053 | 0:38.0 | right | wall | Jersey at the bank foot | onboard:RAZip6S84CM@38.0 | covered by barrier 13 (concrete) |
| 1111 | 0:40.0 | left | tyre_wall | stacked tyres | onboard:RAZip6S84CM@40.0 | covered by barrier 14 (tyres) |
| 1111 | 0:40.0 | right | wall | concrete at the bank foot | onboard:RAZip6S84CM@40.0 | covered by barrier 13 (concrete) |
| 1184 | 0:42.0 | right | kerb | plain kerb strip | onboard:RAZip6S84CM@42.0 | covered by kerb 1154.4-1279.1 |
| 1184 | 0:42.0 | right | wall | concrete | onboard:RAZip6S84CM@42.0 | covered by barrier 13 (concrete) |
| 1262 | 0:44.0 | right | wall | concrete | onboard:RAZip6S84CM@44.0 | covered by barrier 13 (concrete) |
| 1337 | 0:46.0 | right | wall | concrete | onboard:RAZip6S84CM@46.0 | covered by barrier 13 (concrete) |
| 1425 | 0:48.0 | ahead | tower | tall dark tower (infield) | onboard:RAZip6S84CM@48.0 | surroundings (not a checked kind) |
| 1425 | 0:48.0 | right | wall | concrete | onboard:RAZip6S84CM@48.0 | covered by barrier 13 (concrete) |
| 1552 | 0:52.0 | left | tower | tall dark tower (infield, green light) | onboard:RAZip6S84CM@52.0 | surroundings (not a checked kind) |
| 1606 | 0:54.0 | left | kerb | kerb | onboard:RAZip6S84CM@54.0 | covered by kerb 1591.4-1646.3 |
| 1606 | 0:54.0 | right | tyre_wall | tyre lines | onboard:RAZip6S84CM@54.0 | covered by barrier 11 (tyres) |
| 1661 | 0:56.0 | left | kerb | kerb | onboard:RAZip6S84CM@56.0 | covered by kerb 1591.4-1646.3 |
| 1712 | 0:58.0 | left | wall | concrete with dark head section | onboard:RAZip6S84CM@58.0 | covered by barrier 16 (concrete) |
| 1712 | 0:58.0 | right | paint | drag strip lane line | onboard:RAZip6S84CM@58.0 | surroundings (not a checked kind) |
| 1767 | 1:00.0 | left | wall | Jersey | onboard:RAZip6S84CM@60.0 | covered by barrier 16 (concrete) |
| 1767 | 1:00.0 | right | kerb | kerb | onboard:RAZip6S84CM@60.0 | covered by kerb 1721.1-1796 |
| 1831 | 1:02.0 | left | wall | Jersey | onboard:RAZip6S84CM@62.0 | covered by barrier 16 (concrete) |
| 1902 | 1:04.0 | left | wall | Jersey | onboard:RAZip6S84CM@64.0 | covered by barrier 16 (concrete) |
| 1962 | 1:06.0 | left | wall | Jersey | onboard:RAZip6S84CM@66.0 | covered by barrier 16 (concrete) |
| 2032 | 1:08.0 | left | wall | Jersey | onboard:RAZip6S84CM@68.0 | covered by barrier 16 (concrete) |
| 2105 | 1:10.0 | left | boards | boards on posts behind the wall | onboard:RAZip6S84CM@70.0 | surroundings (not a checked kind) |
| 2105 | 1:10.0 | left | wall | Jersey | onboard:RAZip6S84CM@70.0 | covered by barrier 16 (concrete) |
| 2151 | 1:12.0 | ahead | boards | PIRELLI board | onboard:RAZip6S84CM@72.0 | surroundings (not a checked kind) |
| 2151 | 1:12.0 | left | station | marshal tower (white hut on legs) behind the wall | onboard:RAZip6S84CM@72.0 | covered by marshal 'T7 tower' |
| 2158 | 1:12.5 | right | kerb | kerb | onboard:RAZip6S84CM@72.5 | covered by kerb 2172.1-2201.1 |
| 2188 | 1:14.0 | left | tyre_stack | black tyre stacks along the paddock edge | onboard:RAZip6S84CM@74.0 | covered by tyres ''; tyres '' |
| 2188 | 1:14.0 | right | cone_line | delineator pylons at the island | onboard:RAZip6S84CM@74.0 | covered by cone line 2 |
| 2268 | 1:16.5 | right | kerb | island kerb | onboard:RAZip6S84CM@76.5 | covered by kerb 2244-2291.9 |
| 2281 | 1:17.0 | right | mast | light mast | onboard:RAZip6S84CM@77.0 | MISSING, placed: lidar spike s 2345.7 (the mast seen ahead right at 1:17-1:18) |
| 2297 | 1:18.0 | left | kerb | kerb | onboard:RAZip6S84CM@78.0 | covered by kerb 2299.8-2371.7 |
| 2338 | 1:20.0 | left | kerb | kerb | onboard:RAZip6S84CM@80.0 | covered by kerb 2299.8-2371.7 |
| 2338 | 1:20.0 | right | wall | concrete (far) | onboard:RAZip6S84CM@80.0 | covered by barrier 17 (concrete) |
| 2405 | 1:22.5 | left | kerb | kerb | onboard:RAZip6S84CM@82.5 | covered by kerb 2417.6-2454.5 |
| 2452 | 1:24.0 | right | mast | light mast | onboard:RAZip6S84CM@84.0 | MISSING, placed: lidar spike s 2421.6 (seen ahead right at 1:24) |
| 2483 | 1:25.0 | right | wall | dark concrete wall | onboard:RAZip6S84CM@85.0 | covered by barrier 17 (concrete) |
| 2497 | 1:25.5 | right | kerb | kerb | onboard:RAZip6S84CM@85.5 | covered by kerb 2479.4-2537.3 |
| 2514 | 1:26.0 | right | wall | concrete | onboard:RAZip6S84CM@86.0 | covered by barrier 17 (concrete) |
| 2591 | 1:28.0 | left | kerb | kerb | onboard:RAZip6S84CM@88.0 | covered by kerb 2600.2-2645.1 |
| 2591 | 1:28.0 | left | wall | concrete beyond grass | onboard:RAZip6S84CM@88.0 | covered by barrier 18 (concrete) |
| 2663 | 1:30.0 | left | stand | back-straight terrace | onboard:RAZip6S84CM@90.0 | MISSING, placed: terrace back-straight terrace (seen ahead at 1:30) |
| 2693 | 1:30.0 | left | wall | dark concrete at the terrace foot | onboard:RAZip6S84CM@90.0 | covered by barrier 19 (concrete + 3.5 m fence) (corrected in r1: 0 was a, 1 was b, 2 was e, 3 was a, 4 was m, 5 was  , 6 was a, 7 was t, 8 was  , 9 was 1, 10 was :, 11 was 3, 12 was 0) |
| 2693 | 1:30.0 | right | kerb | kerb | onboard:RAZip6S84CM@90.0 | covered by kerb 2692-2739.8 (corrected in r1: 0 was a, 1 was b, 2 was e, 3 was a, 4 was m, 5 was  , 6 was a, 7 was t, 8 was  , 9 was 1, 10 was :, 11 was 3, 12 was 0) |
| 2732 | 1:32.0 | left | fence | catch fence on the wall | onboard:RAZip6S84CM@92.0 | covered by barrier 19 (concrete + 3.5 m fence) catch fence; barrier 26 (fence + 1.8 m fence) |
| 2732 | 1:32.0 | right | cone_line | orange cones at the bypass mouth | onboard:RAZip6S84CM@92.0 | MISSING, placed: closed road 2020 bypass mouth (the mouth at s 2802; the 1:32 frame sees the cones ahead) |
| 2812 | 1:34.0 | left | fence | catch fence on the wall | onboard:RAZip6S84CM@94.0 | covered by barrier 19 (concrete + 3.5 m fence) catch fence; barrier 20 (concrete + 3.5 m fence) catch fence |
| 2812 | 1:34.0 | left | stand | back-straight terrace with shade roof | onboard:RAZip6S84CM@94.0 | covered by terrace back-straight terrace |
| 2812 | 1:34.0 | left | wall | concrete | onboard:RAZip6S84CM@94.0 | covered by barrier 19 (concrete + 3.5 m fence); barrier 20 (concrete + 3.5 m fence) |
| 2909 | 1:36.0 | left | cone_line | single marker cone | onboard:RAZip6S84CM@96.0 | covered by cone line 4 |
| 2909 | 1:36.0 | left | wall | concrete | onboard:RAZip6S84CM@96.0 | covered by barrier 20 (concrete + 3.5 m fence) |
| 3001 | 1:38.0 | left | cone_line | single marker cone | onboard:RAZip6S84CM@98.0 | covered by cone line 5 |
| 3001 | 1:38.0 | left | fence | catch fence | onboard:RAZip6S84CM@98.0 | covered by barrier 20 (concrete + 3.5 m fence) catch fence; barrier 26 (fence + 1.8 m fence) |
| 3001 | 1:38.0 | left | wall | concrete | onboard:RAZip6S84CM@98.0 | covered by barrier 20 (concrete + 3.5 m fence) |
| 3049 | 1:40.0 | right | kerb | kerb | onboard:RAZip6S84CM@100.0 | covered by kerb 3021.2-3076.1 |
| 3049 | 1:40.0 | right | tyre_stack | two-tyre stack | onboard:RAZip6S84CM@100.0 | covered by tyres '' |
| 3083 | 1:41.7 | left | kerb | kerb | onboard:RAZip6S84CM@101.7 | covered by kerb 3060.1-3169.9 |
| 3113 | 1:44.0 | left | boards | SONOMA RACEWAY / SUNBELT RENTALS / TOYOTA | onboard:RAZip6S84CM@104.0 | surroundings (not a checked kind) |
| 3113 | 1:44.0 | left | wall | tall board wall | onboard:RAZip6S84CM@104.0 | covered by barrier 21 (concrete) |
| 3113 | 1:44.0 | right | fence | catch fence on the wall | onboard:RAZip6S84CM@104.0 | covered by barrier 22 (concrete + 4 m fence) catch fence |
| 3113 | 1:44.0 | right | wall | concrete | onboard:RAZip6S84CM@104.0 | covered by barrier 22 (concrete + 4 m fence) |
| 3147 | 1:46.0 | left | wall | tall board wall | onboard:RAZip6S84CM@106.0 | covered by barrier 21 (concrete) |
| 3147 | 1:46.0 | right | fence | catch fence | onboard:RAZip6S84CM@106.0 | covered by barrier 22 (concrete + 4 m fence) catch fence |
| 3147 | 1:46.0 | right | wall | concrete | onboard:RAZip6S84CM@106.0 | covered by barrier 22 (concrete + 4 m fence) |
| 3188 | 1:48.0 | left | boards | TOYOTA | onboard:RAZip6S84CM@108.0 | surroundings (not a checked kind) |
| 3188 | 1:48.0 | left | wall | tall board wall | onboard:RAZip6S84CM@108.0 | covered by barrier 21 (concrete) |
| 3188 | 1:48.0 | right | fence | catch fence | onboard:RAZip6S84CM@108.0 | covered by barrier 22 (concrete + 4 m fence) catch fence |
| 3188 | 1:48.0 | right | wall | concrete | onboard:RAZip6S84CM@108.0 | covered by barrier 22 (concrete + 4 m fence) |
| 3229 | 1:49.7 | right | kerb | kerb | onboard:RAZip6S84CM@109.7 | covered by kerb 3219.8-3292.6 |
| 3238 | 1:50.0 | left | boards | HUMBOLDT / SAVE MART / ZMAX | onboard:RAZip6S84CM@110.0 | surroundings (not a checked kind) |
| 3238 | 1:50.0 | left | wall | tall board wall | onboard:RAZip6S84CM@110.0 | covered by barrier 21 (concrete) |
| 3238 | 1:50.0 | right | fence | catch fence | onboard:RAZip6S84CM@110.0 | covered by barrier 22 (concrete + 4 m fence) catch fence |
| 3238 | 1:50.0 | right | wall | concrete | onboard:RAZip6S84CM@110.0 | covered by barrier 22 (concrete + 4 m fence) |
| 3301 | 1:52.0 | left | boards | ZMAX | onboard:RAZip6S84CM@112.0 | surroundings (not a checked kind) |
| 3301 | 1:52.0 | left | wall | tall board wall | onboard:RAZip6S84CM@112.0 | covered by barrier 21 (concrete) |
| 3301 | 1:52.0 | right | fence | catch fence | onboard:RAZip6S84CM@112.0 | covered by barrier 22 (concrete + 4 m fence) catch fence |
| 3301 | 1:52.0 | right | wall | concrete | onboard:RAZip6S84CM@112.0 | covered by barrier 22 (concrete + 4 m fence) |
| 3374 | 1:54.0 | left | boards | ECHOPARK AUTOMOTIVE | onboard:RAZip6S84CM@114.0 | surroundings (not a checked kind) |
| 3374 | 1:54.0 | left | wall | tall board wall | onboard:RAZip6S84CM@114.0 | covered by barrier 21 (concrete) |
| 3374 | 1:54.0 | right | fence | catch fence | onboard:RAZip6S84CM@114.0 | covered by barrier 22 (concrete + 4 m fence) catch fence |
| 3374 | 1:54.0 | right | tyre_wall | stacked tyres along the fence | onboard:RAZip6S84CM@114.0 | covered by barrier 23 (tyres) |
| 3457 | 1:56.0 | left | boards | LAS VEGAS | onboard:RAZip6S84CM@116.0 | surroundings (not a checked kind) |
| 3457 | 1:56.0 | left | wall | tall board wall (pit-in / paddock) | onboard:RAZip6S84CM@116.0 | covered by barrier 4 (concrete); barrier 21 (concrete) |
| 3457 | 1:56.0 | left | wall | Jersey in front (pit-in separation) | onboard:RAZip6S84CM@116.0 | covered by barrier 4 (concrete); barrier 21 (concrete) |
| 3548 | 1:58.0 | left | boards | SAVE MART / LUCKY / FOODMAXX | onboard:RAZip6S84CM@118.0 | surroundings (not a checked kind) |
| 3548 | 1:58.0 | left | cone_line | orange cones along the pit-in line | onboard:RAZip6S84CM@118.0 | covered by cone line 6 |
| 3548 | 1:58.0 | left | wall | Jersey (pit-in separation) | onboard:RAZip6S84CM@118.0 | covered by barrier 4 (concrete) |
| 3616 | 2:00.0 | left | boards | COCA-COLA | onboard:RAZip6S84CM@120.0 | surroundings (not a checked kind) |
| 3616 | 2:00.0 | left | wall | Jersey | onboard:RAZip6S84CM@120.0 | covered by barrier 2 (concrete); barrier 4 (concrete) |
| 3655 |  | left | wall | board wall with Jersey in front | streetview:jrXpHaDfJT2APw6zcyBKRA@40 | covered by barrier 2 (concrete); barrier 4 (concrete) |
| 3657 | 2:02.0 | left | building | glass-front building beyond the pit road | onboard:RAZip6S84CM@122.0 | covered by building 0 '' 4.5 m; building 5 '' 5.5 m |
| 3657 | 2:02.0 | left | wall | concrete (outside of T11) | onboard:RAZip6S84CM@122.0 | covered by barrier 2 (concrete); barrier 4 (concrete) |
| 3657 | 2:02.0 | right | tyre_stack | striped concrete blocks at the apex | onboard:RAZip6S84CM@122.0 | covered by block '' |
| 3665 |  | right | tyre_stack | yellow/blue tyre stacks on the apron | streetview:jrXpHaDfJT2APw6zcyBKRA@196 | covered by block '' |
| 3677 | 2:03.3 | right | kerb | kerb | onboard:RAZip6S84CM@123.3 | covered by kerb 3628.8-3730.6 |
| 3688 | 2:04.0 | left | tyre_wall | white-wrapped stacked tyres on the wall | onboard:RAZip6S84CM@124.0 | covered by barrier 3 (tyres) |
| 3688 | 2:04.0 | right | tyre_stack | striped blocks | onboard:RAZip6S84CM@124.0 | covered by block '' |
| 3725 | 2:06.0 | left | building | pit garages, yellow with green roofs | onboard:RAZip6S84CM@126.0 | covered by building 4 '' 6.5 m |
| 3725 | 2:06.0 | left | wall | concrete (pit separation) | onboard:RAZip6S84CM@126.0 | covered by barrier 2 (concrete) |
| 3774 | 2:08.0 | left | wall | concrete (pit separation) | onboard:RAZip6S84CM@128.0 | covered by barrier 2 (concrete) |
| 3835 | 2:10.0 | left | building | pit garages | onboard:RAZip6S84CM@130.0 | covered by building 1 '' 6.2 m; building 3 '' 6.3 m |
| 3835 | 2:10.0 | left | wall | concrete (pit separation) | onboard:RAZip6S84CM@130.0 | covered by barrier 2 (concrete) |
| 3909 | 2:12.0 | left | cone_line | orange cones at the nose | onboard:RAZip6S84CM@132.0 | covered by cone line 7 |
| 3909 | 2:12.0 | left | wall | wall nose painted SONOMA TURN 12 | onboard:RAZip6S84CM@132.0 | covered by barrier 2 (concrete) |
| 3941 | 2:13.0 | left | building | 3-storey control building | onboard:RAZip6S84CM@133.0 | covered by building 2 '' 8.7 m |
| 3950 |  | left | building | T12 control tower building | streetview:QduY6QTXmw4JDevQVE_b-g@0 | covered by building 2 '' 8.7 m (corrected in r1: 0 was s, 1 was i, 2 was d, 3 was e, 4 was  , 5 was r, 6 was i, 7 was g, 8 was h, 9 was t) |
| 3967 | 2:14.0 | left | stand | main grandstand | onboard:RAZip6S84CM@134.0 | MISSING, placed: main grandstand (the grandstand structure, front at s 3995-7, seen across the pit lane at 2:14) |
| 3967 | 2:14.0 | left | wall | concrete with ECHOPARK painted face | onboard:RAZip6S84CM@134.0 | covered by barrier 2 (concrete) |
| 3967 | 2:14.0 | right | wall | concrete with ECHOPARK painted face | onboard:RAZip6S84CM@134.0 | covered by barrier 6 (concrete) |
| 4025 | 2:16.0 | left | wall | concrete pit wall | onboard:RAZip6S84CM@136.0 | covered by barrier 2 (concrete) |
| 4025 | 2:16.0 | right | wall | drag-strip Jersey | onboard:RAZip6S84CM@136.0 | covered by barrier 6 (concrete) |
| 4058 | 0:00.0 | both | paint | chequered S/F stripe | onboard:RAZip6S84CM@0.0 | surroundings (not a checked kind) |
| 4058 | 0:00.0 | left | stand | main grandstand with suites | onboard:RAZip6S84CM@0.0 | covered by structure 0 grandstand 'main grandstand' |
| 4058 | 0:00.0 | left | wall | concrete pit wall | onboard:RAZip6S84CM@0.0 | covered by barrier 2 (concrete) |
| 4058 | 0:00.0 | right | wall | concrete (drag-strip wall) | onboard:RAZip6S84CM@0.0 | covered by barrier 6 (concrete) |
| 4085 |  | left | wall | pit wall | streetview:5MY4xR9O7etAXEHnZCVnGQ@300 | covered by barrier 2 (concrete) |
| 4085 |  | right | wall | drag-strip wall | streetview:5MY4xR9O7etAXEHnZCVnGQ@300 | covered by barrier 6 (concrete) |
| 4093 | 2:18.0 | left | paint | SONOMA RACEWAY ground logo | onboard:RAZip6S84CM@138.0 | surroundings (not a checked kind) |
| 20 |  | right | wall | pit wall | onboard:24of8fjjAug@296 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 3, 3 was 0) |
| 50 |  | right | wall | pit wall | onboard:24of8fjjAug@298 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 9, 3 was 0) |
| 70 |  | left | building | red-roof pit-out building | onboard:24of8fjjAug@300 | pit lane: not a checked kind for the lap (corrected in r1: 0 was s, 1 was  , 2 was 1, 3 was 3, 4 was 0) |
| 95 |  | left | wall | concrete with catch fence and O'Reilly boards | onboard:24of8fjjAug@302 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 1, 3 was 6, 4 was 0) |
| 95 |  | right | wall | Jersey (pit-out separation) | onboard:24of8fjjAug@302 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 1, 3 was 6, 4 was 0) |
| 140 |  | left | wall | concrete with catch fence | onboard:24of8fjjAug@304 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 2, 3 was 0, 4 was 0) |
| 140 |  | right | cone_line | small yellow cones on the double yellow blend line | onboard:24of8fjjAug@304 | pit lane: not a checked kind for the lap (corrected in r1: 0 was s, 1 was  , 2 was 2, 3 was 0, 4 was 0) |
| 140 |  | right | paint | double yellow blend line | onboard:24of8fjjAug@304 | pit lane: not a checked kind for the lap (corrected in r1: 0 was s, 1 was  , 2 was 2, 3 was 0, 4 was 0) |
| 200 |  | left | wall | concrete with catch fence | onboard:24of8fjjAug@306 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 2, 3 was 4, 4 was 0) |
| 3560 |  | left | tyre_wall | black tyre stacks in front of the wall | onboard:24of8fjjAug@1436 | pit lane: not a checked kind for the lap |
| 3560 |  | left | wall | tall board wall (GENERAL TIRE) | onboard:24of8fjjAug@1436 | pit-lane gate (pit_lane.walls) |
| 3560 |  | right | tyre_wall | black tyre stacks between the pit-in lane and the track | onboard:24of8fjjAug@1436 | pit lane: not a checked kind for the lap |
| 3990 |  | left | paint | pit box lines | onboard:24of8fjjAug@288 | pit lane: not a checked kind for the lap (corrected in r1: 0 was s, 1 was  , 2 was 4, 3 was 0, 4 was 0, 5 was 0) |
| 3990 |  | right | wall | pit wall (track side) | onboard:24of8fjjAug@288 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 4, 3 was 0, 4 was 0, 5 was 0) |
| 4050 |  | left | stand | main grandstand beyond the boxes | onboard:24of8fjjAug@292 | pit lane: not a checked kind for the lap (corrected in r1: 0 was s, 1 was  , 2 was 4, 3 was 0, 4 was 6, 5 was 0) |
| 4050 |  | right | wall | pit wall | onboard:24of8fjjAug@292 | pit-lane gate (pit_lane.walls) (corrected in r1: 0 was s, 1 was  , 2 was 4, 3 was 0, 4 was 6, 5 was 0) |
