# Package comparison: /Users/cobyhartman/dev/probe_sim-wt/rederive-sonoma/public/tracks/sonoma against /Users/cobyhartman/dev/probe_sim-wt/track-pipeline/public/tracks/sonoma

Objects of each kind sampled every 2 m; a reference object is matched when 50% of its points lie within 15 m of candidate objects of its kind (tools/track/compare/compare_packages.py). Heights differ when |dh| > max(0.3 m, 25 %).

| kind | ref | cand | matched | missing | extra | height diffs | median offset of matched (m) |
|---|---|---|---|---|---|---|---|
| block | 5 | 2 | 2 | 3 | 0 | 0 | 4.24 |
| board | 125 | 84 | 106 | 19 | 3 | 16 | 3.54 |
| bridge | 1 | 1 | 1 | 0 | 0 | 0 | 0.0 |
| building | 17 | 9 | 9 | 8 | 1 | 0 | 0.04 |
| closed_road | 7 | 9 | 7 | 0 | 1 | 0 | 0.0 |
| cone_line | 9 | 9 | 4 | 5 | 5 | 0 | 1.23 |
| fence | 22 | 9 | 13 | 9 | 0 | 3 | 2.58 |
| ground_sign | 8 | 0 | 0 | 8 | 0 | 0 | - |
| impact | 1 | 1 | 0 | 1 | 1 | 0 | - |
| kerb | 30 | 26 | 28 | 2 | 0 | 0 | 0.0 |
| kerb_line | 2 | 0 | 0 | 2 | 0 | 0 | - |
| mast | 41 | 26 | 28 | 13 | 1 | 0 | 0.0 |
| paint_line | 25 | 25 | 25 | 0 | 0 | 0 | 0.0 |
| paved_area | 1 | 0 | 0 | 1 | 0 | 0 | - |
| pit_lane | 1 | 1 | 1 | 0 | 0 | 0 | 0.0 |
| runoff_zone | 1 | 0 | 0 | 1 | 0 | 0 | - |
| stand | 5 | 4 | 3 | 2 | 0 | 0 | 1.36 |
| station | 6 | 3 | 1 | 5 | 2 | 1 | 1.22 |
| tower | 1 | 1 | 1 | 0 | 0 | 0 | 3.71 |
| tyre_stack | 5 | 3 | 1 | 4 | 2 | 0 | 1.11 |
| tyre_wall | 24 | 8 | 7 | 17 | 3 | 0 | 2.57 |
| wall | 38 | 16 | 24 | 14 | 4 | 4 | 1.79 |
| **all** | 375 | 237 | 261 | 114 | 23 | 24 | |

## Missing (in the reference, not in the candidate)

- block: block '' at (480, -467), s 3681, h 0.8: c20_s1320: block 1 of 3 at the outside apron edge of T11 (s ~3681, 10.2 m left of the centre, capture shift applied); on
- block: block '' at (482, -467), s 3680, h 0.8: c20_s1320: block 2 of 3 (see block 1)
- block: block '' at (484, -466), s 3678, h 0.8: c20_s1320: block 3 of 3 (see block 1)
- board: sign 'zMAX' at (367, -189), s 3971, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'EchoPark' at (344, -171), s 4001, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'zMAX' at (340, -167), s 4007, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'TOYOTA' at (335, -164), s 4013, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'SONOMA RACEWAY' at (330, -160), s 4018, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'LAS VEGAS' at (326, -156), s 4024, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'O'REILLY' at (321, -153), s 4030, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'EchoPark' at (317, -149), s 4036, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'zMAX' at (312, -145), s 4042, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'TOYOTA' at (308, -142), s 4048, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'SONOMA RACEWAY' at (303, -138), s 4054, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'LAS VEGAS' at (298, -135), s 4059, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'O'REILLY' at (294, -131), s 4065, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'EchoPark' at (289, -127), s 4071, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'zMAX' at (285, -124), s 4077, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'TOYOTA' at (280, -120), s 4083, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'SONOMA RACEWAY' at (276, -117), s 4089, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: sign 'LAS VEGAS' at (271, -113), s 4094, h 2.5: wall board on drag strip, infield (NE) side (onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and Ech
- board: structure boards 'Pit wall boards (green)' at (261, -151), s 4079, h 0.85: onboard RAZip6S84CM 2:15 (green panels on the pit wall at the line, both sides; t134: EchoPark on the green wrap)
- building: building 1 '' at (494, -660), h 5.2: osm
- building: building 2 '' at (471, -524), h 6.4: osm
- building: building 3 '' at (574, -633), h 2.5: osm
- building: building 4 '' at (365, -126), s 3307, h 3.2: osm (c20_s0935: the flat-roofed 21 x 22 m infield building (grey roof, vehicles at its east side) 42-62 m right of s 329
- building: building 5 '' at (-39, -250), h 3.2: osm (onboard 0:14 (frame t014): open shade roof on posts at the top of the T2 terraces (inventory row added in round 5))
- building: building 6 '' at (477, -568), h 4.5: osm
- building: structure garage 'Paddock garage west' at (334, -456), h 7.8: OSM 1019836533; NAIP ortho (green roof); 2025 24of8fjjAug 24:40 (tan garages, grey-green roofs, paddock); inventory s 36
- building: structure garage 'Paddock garage south' at (332, -476), h 7.7: OSM 1019836718; NAIP ortho (green roof); 2025 24of8fjjAug 24:30 (tan building, hip roof, beside the fuel island); invent
- cone_line: cone line 1 at (-450, 375), s 2163: closed road the Chute (NASCAR short course, T4 to T7) mouth (onboard 1:12: small orange cones in front of a black tyre l
- cone_line: cone line 2 at (224, 47), s 3032: onboard RAZip6S84CM 1:36-1:38 (t096 / t098; owner_49 crop): one orange cone ~0.5 m on the grass verge left before 9a, ~6
- cone_line: cone line 3 at (-400, 407), s 2212: onboard RAZip6S84CM 1:14 (t074): orange cones across the short-T7 road at the T7 hairpin; line across the road's first s
- cone_line: cone line 5 at (-376, 450), s 2276: T7a island-nose delineator post (round 7f): onboard 1:16 (t076) one tall orange post with white bands ahead-right beside
- cone_line: cone line 6 at (-239, 285), s 1938: owner note 57 (May 2025 onboard fEcQdo0ucL8 0:57, reference only: a line of orange pylons, no tyre barrier); onboard RAZ
- fence: barrier 10 catch fence at (-94, 261), s 2651, h 3.0: declared: T9, left (the bank) (c20_s0220 / c20_s0275 bright wall ~19 m left (95 % picked, rms 0.27 m); Street View xXQqy
- fence: barrier 16 catch fence at (482, -468), s 3680, h 3.0: declared: T11 hairpin, left tyre wall (c20_s1265 / c20_s1320 white tyre band on the outside of the hairpin (69 % picked,
- fence: barrier 27 catch fence at (-414, 221), s 1117, h 2.5: declared: T5, left: tyre wall (2026 captures c20_s2805 / c20_s2860: wall_measure dark line, 96 % picked, rms 0.49 m; Str
- fence: barrier 28 catch fence at (-202, 134), s 1327, h 4.0: declared: T5 to the T6 crest, left: wall and catch fence beyond the paddock (2026 captures c20_s2970 / c20_s3080: wall_m
- fence: barrier 30 (fence) at (-100, 23), s 1537, h 0.0: declared: Carousel, left: trackside fence (2026 captures c20_s3190 / c20_s3300: wall_measure dark line, 100 % picked, rm
- fence: barrier 56 (fence) at (-226, 386), s 2477, h 0.0: declared: T7a to T9, left: fence on the bank top (round 5) (onboard RAZip6S84CM 1:18-1:26 (fence posts along the top of 
- fence: barrier 57 (fence) at (-417, 158), s 1099, h 0.0: declared: T5, right: fence on the bank top (round 5) (onboard RAZip6S84CM 0:38-0:40 (fence along the top of the bank abo
- fence: barrier 64 (fence) at (241, -89), s 34, h 0.0: declared: drag strip infield side: catch fence near the line (round 5) (onboard RAZip6S84CM 0:00, 0:02, 2:18 (chain-link
- fence: barrier 66 (fence) at (-427, 519), s 2260, h 0.0: terrace T7a hill top fence (measured footprint (round 6): compare/terrace_measure.py --thr 0.35 --guide xy:-480,462;-452
- ground_sign: ground sign 'O'Reilly' at (-369, 439), s 2301: c20_s0000 / c20_s3960: an O'Reilly logo painted inside the T7a hairpin island (white lettering with an outline, ~17 x 7.
- ground_sign: ground sign 'TOYOTA' at (475, -424), s 3637: c20_s1320 / c20_s1265: TOYOTA lettering painted in the T11 hairpin infield (white, ~18 m, reading ENE); the red emblem b
- ground_sign: ground sign 'CW' at (456, -416), s 3739: c20_s1265: CW lettering in the T11 infield (row above Coca-Cola)
- ground_sign: ground sign 'Coca-Cola' at (465, -420), s 3732: c20_s1265: Coca-Cola script in the T11 infield, white
- ground_sign: ground sign 'xfinity' at (473, -417), s 3624: c20_s1265: xfinity lettering in the T11 infield, white
- ground_sign: ground sign 'TNT' at (471, -412), s 3617: c20_s1265: the TNT roundel in the T11 infield (white disc, dark letters; drawn as a square panel)
- ground_sign: ground sign 'PIT BOSS' at (456, -411), s 3744: c20_s1265: PIT BOSS lettering in the T11 infield (top-left row, partly legible)
- ground_sign: ground sign 'Save Mart' at (474, -433), s 3686: c20_s1320 / c20_s1265: Save Mart lettering painted in the T11 hairpin infield (white, ~24 m)
- impact: impact '' at (492, -373), s 3586, h 1.0: Street View owner_15 (Jul 2011): yellow impact barrier at the nose of the pit-in wall; nose position c20_s1210 (start of
- kerb: kerb 88.8-133.7 (left) at (157, -77), s 112: T1 inside, block line from the pit-wall nose: c20_s1815 / c20_s1870 (kerb_detect grey run 88.8-133.7, offsets -0.5..+0.2
- kerb: kerb 604.6-655.5 (right) at (-254, -68), s 631: T3 approach, right: c20_s2365 (detector 610.6-655.5, red); onboard 0:20.6-0:21 kerb on the right; colour: colour unverif
- kerb_line: kerb line 0 at (-369, 433), s 2310: c20_s3960 / c20_s0000: red / white kerb blocks along the O'Reilly island's lower edge (the T7 inside runoff / PWC road s
- kerb_line: kerb line 1 at (-385, 422), s 2231: c20_s3960 / c20_s0000: red / white kerb blocks round the tip and upper edge of the island between the short-T7 road and 
- mast: mast '' at (320, -112), s 4056, h 20.0: c20_s1650 / c20_s1705: mast base with its NW shadow in the paddock beyond the drag strip at the line; Street View 5MY4xR
- mast: mast '' at (-79, -212), s 419, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-98, -217), s 431, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-119, -217), s 443, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-138, -213), s 456, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-157, -204), s 471, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-174, -195), s 488, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-189, -181), s 506, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-203, -167), s 525, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: mast '' at (-214, -150), s 543, h 4.0: onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the mea
- mast: structure mast 'Light masts' at (-480.5, 481.5) at (-480, 482), h 20.5: lidar 2022-24 spikes; captures c20_s1760 c20_s1815 c20_s1870 c20_s3355 c20_o0440 c20_s3520 c20_s4015 c20_s0000 c20_s0055
- mast: structure mast 'Light masts' at (-525.5, 517.5) at (-526, 518), h 20.7: lidar 2022-24 spikes; captures c20_s1760 c20_s1815 c20_s1870 c20_s3355 c20_o0440 c20_s3520 c20_s4015 c20_s0000 c20_s0055
- mast: structure mast 'Light masts' at (318.5, -104.5) at (318, -104), s 3217, h 27.4: lidar 2022-24 spikes; captures c20_s1760 c20_s1815 c20_s1870 c20_s3355 c20_o0440 c20_s3520 c20_s4015 c20_s0000 c20_s0055
- paved_area: paved area 'paddock behind the pit garages' at (157, -101), s 105: OSM 28825490 (amenity=parking); 2026 captures c20_s1485..s1650: dark asphalt with painted bays and parked trailers
- runoff_zone: runoff 'T7 inside runoff' at (-374, 425), s 2318: asphalt
- stand: terrace T7a hill at (-422, 502), s 2258: measured footprint (round 6): compare/terrace_measure.py --thr 0.35 --guide xy:-480,462;-452,464;-420,471;-390,481;-370,
- stand: structure grandstand 'Main grandstand' at (281, -266), s 3987: OSM 262082790 footprint; 2026 captures c20_s1595..s1760 (seat field, 13 aisle heads at 11 m); lidar 2022-24 profiles acr
- station: marshal 'T6 hilltop' at (-217, 45), s 1395, h 3.8: c20_s3135: a ~3 x 3 m platform with a box behind the right wall at the crest before the Carousel; Street View GMaTaipEd9
- station: marshal 'T4' at (-483, 137), s 970, h 4.0: c20_s2695: a raised hut on a platform 27 m right of the T4 approach (long shadow); onboard 0:33 white elevated post with
- station: marshal 'T2 exit' at (-121, -219), s 445, h 3.0: c20_s2200: a ~2 m white hut at the foot of the T2 terraces, 31 m left of the centre at s ~445 (round 5); onboard 0:12 wh
- station: marshal '8a outside' at (-229, 340), s 2483, h 3.6: round 7c (owner note / item 1): the owner's May 2025 onboard at 1:14 (owner_52_T8_station_video.png, reference only): a 
- station: marshal '9a, stand foot' at (229, 66), s 3025, h 3.0: round 7 (owner note 49, corrected): onboard t098 and the owner crop owner_49_9a_station_crop.jpg: a small hut at the bas
- tyre_stack: tyres '' at (-3, 146), s 1689, h 0.8: round 6 (orchestrator S3): onboard 0:58 (t058) a black tyre stack at the foot of the light mast on the Carousel-exit run
- tyre_stack: tyres '' at (5, 60), s 1629, h 0.84: c20_s3300 / c20_s3355: two dark stacks on the runoff right of the Carousel exit; onboard 0:56 single black tyre stacks o
- tyre_stack: tyres '' at (8, 56), s 1626, h 0.84: c20_s3300 / c20_s3355: the second stack; onboard 0:56
- tyre_stack: tyres '' at (255, -13), s 3125, h 0.63: onboard 1:44: a black tyre stack in front of the T10-entry board wall at its start (s ~3125; wall on c20_s0715 / c20_s07
- tyre_wall: barrier 0 (tyres) at (-338, 30), s 737, h 1.0: osm:380830042 (T3 right, OSM note "tire barrier": c20_s2475 / c20_s2530 show the dark tyre band on this line, 37-47 m ri
- tyre_wall: barrier 7 (tyres) at (-400, 336), s 2105, h 1.0: declared: T7 approach, left tyre wall (c20_s3850 / c20_s3905 dark tyre stack 4-10 m beyond the left edge (96 % picked, r
- tyre_wall: barrier 9 (tyres) at (-180, 321), s 2528, h 1.0: declared: T8a to T9, left (the bank) (c20_s0110 / c20_s0165 dark barrier ~20 m left (99 % picked, rms 0.34 m); Street Vi
- tyre_wall: barrier 11 (tyres) at (-184, 273), s 2560, h 1.0: declared: T8a, right (toward the 2020 bypass) (c20_s0165 / c20_s0220 dark tyre stack 10-18 m right (95 % picked, rms 0.5
- tyre_wall: barrier 17 (tyres) at (-283, 15), s 701, h 1.0: declared: T3, right: low tyre-faced wall far out (c20_s2365..s2475 dark line 34-36 m right (100 % picked, rms 0.70 m); S
- tyre_wall: barrier 19 (tyres) at (-436, 81), s 898, h 1.0: declared: T4, right: tyre line beyond the runoff (c20_s2640 / c20_s2695 dark tyre line 20-30 m right (79 % picked, rms 0
- tyre_wall: barrier 21 (tyres) at (-22, 257), s 2716, h 1.0: declared: back straight start, left tyre line (c20_s0330 / c20_s0385 dark tyre line ~21 m left (78 % picked, rms 0.72 m)
- tyre_wall: barrier 26 (tyres) at (-177, -117), s 540, h 1.0: declared: T2 exit to T3, right: barrier line at the foot of the hill (owner_11) (2026 captures c20_s2255 / c20_s2310: wa
- tyre_wall: barrier 31 (tyres) at (-253, 375), s 2443, h 1.0: declared: T8, left: tyre line up the bank (to the T8a-T9 tyres) (2026 captures c20_s0000 / c20_s0055: wall_measure dark 
- tyre_wall: barrier 34 (tyres) at (433, -224), s 3426, h 1.0: declared: T11 approach, right: tyre wall and catch fence at the edge (2026 captures c20_s1045 / c20_s1100: wall_measure 
- tyre_wall: barrier 35 (tyres) at (237, -41), s 3115, h 1.0: declared: 9a, right: tyre wall (2026 captures c20_s0715 / c20_s0770: wall_measure dark line, 100 % picked, rms 0.53 m; o
- tyre_wall: barrier 44 (tyres) at (-68, -88), s 329, h 1.0: declared: T1 exit to T2, right: tyre line on the grass bank (owner_28) (part 2) (2026 captures c20_s1980 / c20_s2035: wa
- tyre_wall: barrier 49 (tyres) at (-451, 375), s 2163, h 0.6: declared: the Chute's T7 mouth: tyre line behind the cones (round 5) (onboard RAZip6S84CM 1:12 (frame t072): two low bla
- tyre_wall: barrier 51 (tyres) at (-440, 424), s 2203, h 0.9: declared: T7, left: black tyre facing on the movable Jersey (round 7c, movable) (owner placement 20 Oct 2026 on the capt
- tyre_wall: barrier 53 (tyres) at (-439, 465), s 2240, h 0.8: declared: T7a, left: tyre line at the foot of the terraces (round 5) (c20_s3960 / c20_s4015: wall_measure dark, 100 % pi
- tyre_wall: barrier 55 (tyres) at (-302, 441), s 2321, h 0.8: declared: T7a to T8, left: tyre line at the foot of the bank (round 5) (c20_s0000 / c20_s4070: wall_measure dark, 100 % 
- tyre_wall: barrier 63 (tyres) at (455, -222), s 3431, h 0.6: declared: T10 to T11, left: tyre bundles at the foot of the boarded wall (round 5) (c20_s0990 / c20_s1045: wall_measure 
- wall: barrier 3 (concrete) at (398, -262), s 3902, h 1.1: declared: T12 exit, right: L-shaped wall closing the drag strip mouth (round 7) (c20_s1540: a light 1 m concrete band, L
- wall: barrier 10 (concrete) at (-94, 261), s 2651, h 1.0: declared: T9, left (the bank) (c20_s0220 / c20_s0275 bright wall ~19 m left (95 % picked, rms 0.27 m); Street View xXQqy
- wall: barrier 13 (concrete) at (82, 13), h 1.0: declared: drag strip, track (SW) side, past T1 to the Carousel exit (c20_s1870 / c20_s1815 / c20_s0550 / c20_s3355: the 
- wall: barrier 14 (concrete) at (181, -42), s 101, h 1.0: declared: drag strip, infield (NE) side (c20_s0495..s1760: the bright wall along the drag strip NE edge (530 m, 100 % pi
- wall: barrier 25 (concrete) at (-157, -202), s 472, h 1.0: declared: T2 exit, left: wall and catch fence at the foot of the T2 stands (2026 captures c20_s2145 / c20_s2200: wall_me
- wall: barrier 28 (concrete) at (-202, 134), s 1327, h 1.0: declared: T5 to the T6 crest, left: wall and catch fence beyond the paddock (2026 captures c20_s2970 / c20_s3080: wall_m
- wall: barrier 33 (concrete) at (-93, 221), s 2653, h 1.0: declared: T9, right: concrete wall along the 2020 bypass (part 2) (2026 captures c20_s0220 / c20_s0275: wall_measure bri
- wall: barrier 40 (concrete) at (507, -478), s 3670, h 1.2: declared: T11 hairpin, outside the pit road: outer wall (south) (part 1) (2026 captures c20_s1320: wall_measure dark lin
- wall: barrier 41 (concrete) at (458, -487), s 3693, h 1.2: declared: T11 hairpin, outside the pit road: outer wall (south) (part 2) (2026 captures c20_s1320: wall_measure dark lin
- wall: barrier 47 (concrete) at (-367, 368), s 2090, h 1.0: declared: drag strip NW end: far wall beyond the fork (round 5) (c20_s3685 / c20_s3740: wall_measure bright along the dr
- wall: barrier 50 (concrete) at (-440, 425), s 2203, h 0.9: declared: T7, left: movable Jersey across the paddock pavement (round 7c, movable) (owner placement 20 Oct 2026 on the c
- wall: barrier 52 (concrete) at (-444, 453), s 2230, h 1.0: declared: T7, left: wall bounding the paved runoff below the T7a stands (round 5) (c20_s3960 / c20_s4015: wall_measure b
- wall: barrier 54 (concrete) at (-416, 475), s 2253, h 0.8: declared: T7a, left: low wall at the foot of the terraces (round 5) (c20_s3960 / c20_s4015: wall_measure dark (its shado
- wall: barrier 65 (concrete) at (265, -176), s 4059, h 0.6: declared: pit lane, left: low white pit-box wall (round 5) (pit lane: inventory pit rows s 4010 / 4060 / 20: low white p

## Extra (in the candidate, not in the reference)

- board: sign 'TOYOTA' at (-384, 332), s 2089, h 1.6: wall board on T6-T7 wall (onboard 1:09.9-1:10 (t070): boards on posts behind the T7 wall, TOYOTA red / white panels and 
- board: sign 'ECHOPARK' at (375, -215), s 3950, h 0.9: wall board on drag-strip wall (onboard 2:13.5-2:14 (d133.5, t134): green ECHOPARK panels on the right wall face, RESTART
- board: sign 'ECHOPARK' at (332, -180), s 4005, h 0.9: wall board on drag-strip wall (onboard 2:13.5-2:14 (d133.5, t134): green ECHOPARK panels on the right wall face, RESTART
- building: building 7 '' at (516, -218), s 3446, h 3.6: lidar (c20_s1045: roof and shadow on the 2026 capture (lidar, 3.6 m, s 3438))
- closed_road: closed_road 'drag strip' at (-505, 488): concrete
- cone_line: cone line 0 at (31, 179), s 2802: closed road 2020 bypass mouth (onboard 1:32 (t092): orange cones across the bypass mouth (mouth on c20_s0385))
- cone_line: cone line 3 at (-394, 440), s 2244: onboard 1:16 (t076, d076.5): an orange delineator pylon at the island tip, the short-T7 mouth (c20_s3960)
- cone_line: cone line 4 at (127, 124), s 2910: onboard 1:36 (t096): a single orange marker cone on the left grass
- cone_line: cone line 5 at (197, 65), s 3002: onboard 1:38 (t098): a single orange marker cone on the left grass
- cone_line: cone line 7 at (383, -266), s 3904: onboard 2:12 (t132): orange cones at the SONOMA TURN 12 wall face (c20_s1540)
- impact: impact '' at (484, -350), s 3562, h 0.84: pit-lane video 24of8fjjAug 23:56 (p1436): black tyre stacks at the pit-in separation nose (the Jersey starts at s 3560 o
- mast: mast '' at (354, -262), s 3919, h 27.7: lidar spike s 3919.2 (DSM - DEM 27.7 m, isolated, lidar_grids); base and shadow on c20_s1540; light masts on the onboard
- station: marshal 'T2 post' at (-96, -173), s 416, h 3.0: onboard 0:13.5 (d013.5) white hut at the T2 apex; its roof and shadow on c20_s2145 (inside, right)
- station: marshal 'T3a tower' at (-416, 14), s 830, h 3.5: onboard 0:25-0:28 white tower on legs right; roof and shadow on c20_s2530
- tyre_stack: tyres '' at (-447, 399), s 2180, h 0.84: onboard 1:14 (t074): black tyre stacks along the paddock edge left of T7 (movable); c20_s3905 s 2180
- tyre_stack: tyres '' at (-439, 411), s 2192, h 0.84: onboard 1:14 (t074): black tyre stacks along the paddock edge left of T7 (movable); c20_s3905 s 2192
- tyre_wall: barrier 7 (tyres) at (388, -231), s 3933, h 0.84: declared: T12 right head tyres (onboard 2:11.5 (d131.5): white tyre stacks at the head of the right-hand (drag-strip) wa
- tyre_wall: barrier 10 (tyres) at (-76, -200), s 414, h 0.84: declared: T2 tyre wall (wall_measure dark band on c20_s1980..s2200 (rms 1.56-1.86 m); onboard 0:08-0:18 left, catch fenc
- tyre_wall: barrier 23 (tyres) at (418, -178), s 3377, h 1.05: declared: T10 exit tyres (onboard 1:54 (t114): black stacked tyres along the right fence; on the measured wall line (c20
- wall: barrier 0 (concrete) at (-338, 30), s 737, h 1.0: osm:380830042 (dark wall line on c20_s2530/s2585 (wall_measure dark, rms 1.08 m) on the T3a outside)
- wall: barrier 1 (concrete) at (-436, 81), s 898, h 1.0: osm:380830043 (dark wall line on c20_s2585..s2750 (wall_measure dark, rms 1.08 m) on the T3a-T4 outside)
- wall: barrier 8 (concrete) at (101, -35), s 169, h 0.9: declared: T1 runoff wall (wall_measure bright on c20_s1870/s1925 (rms 0.19 m, 68 % picked): the line between the T1 runo
- wall: barrier 18 (concrete) at (-182, 324), s 2525, h 1.0: declared: T8a left dark wall (wall_measure dark band on c20_s0110..s0275 (rms 0.71 m); onboard 1:26 left, far)

## Height differences (matched objects)

- board: sign 'EchoPark' h 3.7 -> sign 'LAS VEGAS' h 5.3 (dh +1.60 m) at (461, -258), s 3467
- board: sign 'TOYOTA' h 2.5 -> sign 'TOYOTA' h 1.6 (dh -0.90 m) at (-401, 342), s 2109
- board: sign 'TOYOTA' h 2.5 -> sign 'TOYOTA' h 1.6 (dh -0.90 m) at (-406, 345), s 2114
- board: sign 'TOYOTA' h 2.5 -> sign 'SAFETY-KLEEN' h 1.6 (dh -0.90 m) at (-411, 348), s 2120
- board: sign 'TOYOTA' h 2.5 -> sign 'TOYOTA' h 1.6 (dh -0.90 m) at (-416, 350), s 2126
- board: sign 'TOYOTA' h 2.5 -> sign 'TOYOTA' h 1.6 (dh -0.90 m) at (-421, 352), s 2131
- board: sign 'TOYOTA' h 2.5 -> sign 'SAFETY-KLEEN' h 1.6 (dh -0.90 m) at (-426, 355), s 2137
- board: sign 'PIRELLI' h 0.9 -> sign 'SAFETY-KLEEN' h 1.6 (dh +0.70 m) at (-432, 358), s 2144
- board: sign '' h 0.9 -> sign 'SAFETY-KLEEN' h 1.6 (dh +0.70 m) at (-437, 360), s 2148
- board: sign 'LAS VEGAS' h 2.5 -> sign 'ECHOPARK' h 0.9 (dh -1.60 m) at (380, -201), s 3956
- board: sign 'O'REILLY' h 2.5 -> sign 'ECHOPARK' h 0.9 (dh -1.60 m) at (376, -197), s 3961
- board: sign 'EchoPark' h 2.5 -> sign 'ECHOPARK' h 0.9 (dh -1.60 m) at (371, -193), s 3966
- board: sign 'TOYOTA' h 2.5 -> sign 'ECHOPARK' h 0.9 (dh -1.60 m) at (362, -185), s 3977
- board: sign 'SONOMA RACEWAY' h 2.5 -> sign 'ECHOPARK' h 0.9 (dh -1.60 m) at (358, -182), s 3983
- board: sign 'LAS VEGAS' h 2.5 -> sign 'ECHOPARK' h 0.9 (dh -1.60 m) at (353, -178), s 3990
- board: sign 'O'REILLY' h 2.5 -> sign 'ECHOPARK' h 0.9 (dh -1.60 m) at (349, -175), s 3996
- fence: barrier 2 catch fence h 2.0 -> barrier 5 catch fence h 4.0 (dh +2.00 m) at (84, -79), s 189
- fence: barrier 59 catch fence h 3.5 -> barrier 19 catch fence h 4.5 (dh +1.00 m) at (-6, 248), s 2732
- fence: barrier 60 catch fence h 3.5 -> barrier 20 catch fence h 4.5 (dh +1.00 m) at (227, 64), s 3025
- station: marshal 'T7' h 4.9 -> marshal 'T7 tower' h 3.5 (dh -1.40 m) at (-442, 361), s 2152
- wall: barrier 15 (concrete) h 2.7 -> barrier 4 (concrete) h 0.8 (dh -1.90 m) at (503, -388), s 3604
- wall: barrier 22 (concrete) h 1.2 -> barrier 21 (concrete) h 0.8 (dh -0.40 m) at (421, -102), s 3309
- wall: barrier 36 (concrete) h 2.7 -> barrier 4 (concrete) h 0.8 (dh -1.90 m) at (478, -314), s 3525
- wall: barrier 39 (concrete) h 1.2 -> barrier 4 (concrete) h 0.8 (dh -0.40 m) at (517, -436), s 3646
