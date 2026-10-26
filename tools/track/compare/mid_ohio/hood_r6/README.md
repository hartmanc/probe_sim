# Mid-Ohio hood sheet, round 6 (26 Oct 2026)

The build-track SKILL 1.10 driver's-eye sheet, made before stage 2 is accepted. The sim's hood camera on the local package
`public/tracks/mid_ohio` (round 5: stage 1 geometry + stage 2 racing line, rev 05d6072129, the uncommitted stand-in;
no scenery) sits beside the N837 Lemons hood-camera frame (OJaBJz18xEo, Apr 2026) and the 2025 INDYCAR 360 lap's ahead
view (e25u_vjn1uM, pace-car roof) at the same station.

How the stills were made: `tools/track/compare/camera_walk.ts --replay hood_r6/walk_plan.json --camera hood --port 5183`.
It uses its own headless Chrome with a throwaway muted profile; the dev server ran from this worktree. The car is placed
with `__sim.vehicle.reset` on the centre, facing the lap. For T8 and T4, a second still puts it on the solver's line
(ghosts.json offset). There is also a hood walk on the line at s 2380-2580 (T8) and s 1830-1890 (T4 entry), and a still
60 m before the T8 crest.

How the stations were chosen (`r6/stations.py`):
- Apex = the package corner's s.
- Entry / exit = where the centre's curvature falls below half the corner's peak, clamped to 20-80 m from the apex.
- Straights = the four longest corner-to-corner runs, at their midpoints.
- Frames = the nearest extracted frame to each map's time at that station.

How the sheets and page were made: `r6/make_sheets.py` (captions `r6/captions.json`) and `r6/make_index.py` (`index.html`,
`t8_crest.png`, `t8_walk.png`, `t4_entry_walk.png`). `r6/t8_overlay.py` makes `t8_overlay.png`. The images and frames
are local only (reference imagery, ignored by git). This README, `frames.json`, `walk_plan.json` and `index.html` are
tracked.

Time-map confidence (inventory `position_uncertainty`):
- N837 map: largest leave-one-out residual 14.8 m, so its rows are **direct**.
- 360-lap map: 20.4 m, also **direct**.
- Both maps are under the 40 m corroborate threshold, so every sheet carries a 360 frame.
- The per-sheet sigma below is the bracketing anchors' residual.
- Frame spacing adds up to ~15 m: N837 has a frame every 1 s; the 360 lap every 0.5 s.

| sheet | corner | s (m) | N837 frame (its s, sigma) | 360 frame (its s, sigma) |
|---|---|---|---|---|
| sheet_00_overview | all stations over the package ortho | | | |
| sheet_01_T8_entry | T8 entry | 2499 | t088.jpg (2504, 8 m, direct) | h0192_ahead.jpg (2495, 20 m, direct) |
| sheet_02_T8_apex | T8 apex | 2521 | t089.jpg (2527, 8 m, direct) | h0194_ahead.jpg (2524, 20 m, direct) |
| sheet_03_T8_exit | T8 exit | 2546 | t090.jpg (2552, 8 m, direct) | h0196_ahead.jpg (2551, 20 m, direct) |
| sheet_04_T4_entry | T4 entry | 1931 | t064.jpg (1935, 15 m, direct) | h0150_ahead.jpg (1928, 20 m, direct) |
| sheet_05_T4_apex | T4 apex | 1961 | t065.jpg (1955, 15 m, direct) | h0153_ahead.jpg (1961, 20 m, direct) |
| sheet_06_T4_exit | T4 exit | 2003 | t067.jpg (1993, 15 m, direct) | h0157_ahead.jpg (2008, 8 m, direct) |
| sheet_07_T13_T1 | T13-T1 mid | 79 | t008.jpg (90, 14 m, direct) | h0052_ahead.jpg (72, 18 m, direct) |
| sheet_08_T1_entry | T1 entry | 277 | t014.jpg (281, 14 m, direct) | h0063_ahead.jpg (279, 20 m, direct) |
| sheet_09_T1_apex | T1 apex | 357 | t017.jpg (364, 14 m, direct) | h0068_ahead.jpg (358, 20 m, direct) |
| sheet_10_T1_exit | T1 exit | 379 | t018.jpg (387, 11 m, direct) | h0069_ahead.jpg (372, 20 m, direct) |
| sheet_11_T1_T2 | T1-T2 mid | 628 | t026.jpg (648, 11 m, direct) | h0082_ahead.jpg (629, 20 m, direct) |
| sheet_12_T2_entry | T2 entry | 878 | t032.jpg (868, 11 m, direct) | h0093_ahead.jpg (877, 20 m, direct) |
| sheet_13_T2_apex | T2 apex | 958 | t037.jpg (961, 11 m, direct) | h0100_ahead.jpg (958, 20 m, direct) |
| sheet_14_T2_exit | T2 exit | 1028 | t040.jpg (1019, 11 m, direct) | h0107_ahead.jpg (1032, 20 m, direct) |
| sheet_15_T2_T3 | T2-T3 mid | 1226 | t047.jpg (1226, 11 m, direct) | h0119_ahead.jpg (1227, 20 m, direct) |
| sheet_16_T3_entry | T3 entry | 1424 | t052.jpg (1439, 11 m, direct) | h0128_ahead.jpg (1433, 20 m, direct) |
| sheet_17_T3_apex | T3 apex | 1445 | t052.jpg (1439, 11 m, direct) | h0129_ahead.jpg (1457, 20 m, direct) |
| sheet_18_T3_exit | T3 exit | 1507 | t054.jpg (1527, 15 m, direct) | h0131_ahead.jpg (1504, 20 m, direct) |
| sheet_19_T3_T4 | T3-T4 mid | 1719 | t058.jpg (1704, 15 m, direct) | h0140_ahead.jpg (1718, 20 m, direct) |
| sheet_20_T5_entry | T5 entry | 2070 | t070.jpg (2066, 15 m, direct) | h0161_ahead.jpg (2066, 8 m, direct) |
| sheet_21_T5_apex | T5 apex | 2100 | t072.jpg (2105, 15 m, direct) | h0164_ahead.jpg (2100, 8 m, direct) |
| sheet_22_T5_exit | T5 exit | 2150 | t074.jpg (2146, 15 m, direct) | h0168_ahead.jpg (2147, 20 m, direct) |
| sheet_23_T6_entry | T6 entry | 2254 | t078.jpg (2256, 15 m, direct) | h0175_ahead.jpg (2257, 20 m, direct) |
| sheet_24_T6_apex | T6 apex | 2282 | t079.jpg (2277, 15 m, direct) | h0177_ahead.jpg (2280, 20 m, direct) |
| sheet_25_T6_exit | T6 exit | 2309 | t081.jpg (2316, 15 m, direct) | h0180_ahead.jpg (2314, 20 m, direct) |
| sheet_26_T7_entry | T7 entry | 2367 | t083.jpg (2367, 15 m, direct) | h0184_ahead.jpg (2371, 20 m, direct) |
| sheet_27_T7_apex | T7 apex | 2387 | t084.jpg (2391, 15 m, direct) | h0185_ahead.jpg (2385, 20 m, direct) |
| sheet_28_T7_exit | T7 exit | 2409 | t085.jpg (2416, 8 m, direct) | h0187_ahead.jpg (2412, 20 m, direct) |
| sheet_29_T9_entry | T9 entry | 2622 | t092.jpg (2610, 8 m, direct) | h0200_ahead.jpg (2616, 20 m, direct) |
| sheet_30_T9_apex | T9 apex | 2643 | t093.jpg (2634, 8 m, direct) | h0202_ahead.jpg (2642, 20 m, direct) |
| sheet_31_T9_exit | T9 exit | 2675 | t095.jpg (2672, 14 m, direct) | h0205_ahead.jpg (2677, 20 m, direct) |
| sheet_32_T10_entry | T10 entry | 2905 | t103.jpg (2902, 14 m, direct) | h0217_ahead.jpg (2903, 20 m, direct) |
| sheet_33_T10_apex | T10 apex | 2931 | t104.jpg (2932, 14 m, direct) | h0218_ahead.jpg (2925, 20 m, direct) |
| sheet_34_T10_exit | T10 exit | 2961 | t105.jpg (2965, 12 m, direct) | h0220_ahead.jpg (2968, 20 m, direct) |
| sheet_35_T11_entry | T11 entry | 3057 | t108.jpg (3061, 12 m, direct) | h0224_ahead.jpg (3053, 20 m, direct) |
| sheet_36_T11_apex | T11 apex | 3086 | t109.jpg (3083, 12 m, direct) | h0226_ahead.jpg (3082, 20 m, direct) |
| sheet_37_T11_exit | T11 exit | 3131 | t111.jpg (3125, 12 m, direct) | h0230_ahead.jpg (3139, 20 m, direct) |
| sheet_38_T12_entry | T12 entry | 3271 | t117.jpg (3281, 12 m, direct) | h0238_ahead.jpg (3276, 20 m, direct) |
| sheet_39_T12_apex | T12 apex | 3351 | t121.jpg (3358, 12 m, direct) | h0244_ahead.jpg (3351, 20 m, direct) |
| sheet_40_T12_exit | T12 exit | 3402 | t123.jpg (3400, 12 m, direct) | h0035_ahead.jpg (3408, 18 m, direct) |
| sheet_41_T13_entry | T13 entry | 3433 | t124.jpg (3426, 12 m, direct) | h0037_ahead.jpg (3436, 18 m, direct) |
| sheet_42_T13_apex | T13 apex | 3454 | t125.jpg (3450, 12 m, direct) | h0039_ahead.jpg (3460, 18 m, direct) |
| sheet_43_T13_exit | T13 exit | 3478 | t126.jpg (3474, 4 m, direct) | h0041_ahead.jpg (3484, 18 m, direct) |

Notes:
- The N837 frames t062-t065 (T4) carry a YouTube player overlay. For the T4 apex, judge from the 360 still.
- N837 shows the T3 entry and apex in one frame (t052).
- The T12 exit and T13 360 frames come from the 360 video's lead-in lap (t 17.5-20.5, before its S/F crossing); the map
  covers that stretch from its Carousel anchor.
