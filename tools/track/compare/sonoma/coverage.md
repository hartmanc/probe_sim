# Sonoma: coverage gate on the current package (21 Oct 2026)

**Status after scenery round 5 (registry rev 93334503f0): PASS.** Coverage: 285 rows checked, 160 objects, MISSING 0 for
walls, fences, kerbs, tyre walls and bridges, UNSUPPORTED 0, 2 building rows ASSIGNED to the buildings round, 47 rows of
the non-failing kinds still MISSING (masts 24, stands 9, tyre stacks 7, cone lines 6, station 1), 1 HEIGHT mismatch
(advisory). Pit lane: 13 rows, all declared, all standing: PASS. What was placed, corrected and why, and every row's
outcome: `manifest.md`, "Round 5". The round-4 work list below is kept as the record of what the round started from.

Package `public/tracks/sonoma` at track-pipeline 0da269d (the build the owner drove), checked against `inventory.json` by `npx tsx tools/track/gates/run_coverage.ts public/tracks/sonoma tools/track/compare/sonoma/inventory.json <gate config>` (the gate config carries the pit_lane walls from `tools/track/tracks/sonoma/config.py`). Tolerance +-15 m. This list is the deliverable for the scenery round: every MISSING row of a must-cover kind is a fix, every UNSUPPORTED object needs a source or goes.

**Result: FAIL.** 284 rows checked (6 'ahead' rows without a distance skipped), 104 scenery objects.

| | wall | fence | kerb | tyre wall | bridge | tyre stack | stand | station | building | mast | cone line |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MISSING | 41 | 32 | 2 | 17 | 0 | 10 | 15 | 6 | 4 | 29 | 11 |
| UNSUPPORTED | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 0 | 8 |

Pit lane: 13 pit-lane wall rows, 0 undeclared in the config, 5 with no barrier in the package: **FAIL**.

## MISSING runs of the must-cover kinds (walls, fences, kerbs, tyre walls, bridges)

| kind | side | s (m) | rows | what (first row) | height | source |
|---|---|---|---|---|---|---|
| fence | left | 174-174 | 1 | chain-link | 2 | onboard:RAZip6S84CM@6.0 |
| fence | left | 381-420 | 2 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@12.0 |
| fence | left | 463-463 | 1 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@16.0 |
| fence | left | 655-655 | 1 | catch fence, curved-top posts, far left | 3.5 | onboard:RAZip6S84CM@22.0 |
| fence | left | 710-710 | 1 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@24.0 |
| fence | left | 900-909 | 2 | catch fence on the wall below the T3a-T4 stands | 3 | streetview:nA1oaDXwADSI7x-Pa-j4Ow@337 |
| fence | left | 1004-1004 | 1 | chain-link fence | 2.5 | onboard:RAZip6S84CM@36.0 |
| fence | left | 1051-1051 | 1 | chain-link fence with posts | 2.5 | onboard:RAZip6S84CM@38.0 |
| fence | left | 1189-1189 | 1 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@42.0 |
| fence | left | 1257-1257 | 1 | catch fence, curved-top posts, on a low wall | 3.5 | onboard:RAZip6S84CM@44.0 |
| fence | left | 1320-1320 | 1 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@46.0 |
| fence | left | 2314-2314 | 1 | fence on the far bank | 1.5 | onboard:RAZip6S84CM@78.0 |
| fence | left | 2371-2371 | 1 | fence on the bank top | 1.5 | onboard:RAZip6S84CM@80.0 |
| fence | left | 2440-2440 | 1 | catch fence on the bank wall |  | streetview:xXQqyp9Q9sWv9ZLN2ORYsA@108 |
| fence | left | 2497-2497 | 1 | fence along the hill | 1.5 | onboard:RAZip6S84CM@84.0 |
| fence | left | 2707-2707 | 1 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@90.0 |
| fence | left | 3018-3056 | 2 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@98.0 |
| fence | left | 3669-3699 | 2 | catch fence, curved-top posts | 3.5 | onboard:RAZip6S84CM@122.0 |
| fence | right | 174-174 | 1 | fence along the hill top | 1.5 | onboard:RAZip6S84CM@6.0 |
| fence | right | 1051-1051 | 1 | fence on the hill top | 1.5 | onboard:RAZip6S84CM@38.0 |
| fence | right | 1117-1117 | 1 | fence on the hill top | 1.5 | onboard:RAZip6S84CM@40.0 |
| fence | right | 1513-1513 | 1 | spectator fence on the bank top | 1.2 | onboard:RAZip6S84CM@52.0 |
| fence | right | 3119-3156 | 2 | catch fence on the wall, curved-top posts, cables | 4 | onboard:RAZip6S84CM@104.0 |
| fence | right | 3203-3203 | 1 | catch fence, curved-top posts | 4 | onboard:RAZip6S84CM@108.0 |
| fence | right | 4024-4024 | 1 | chain-link catch fence | 3 | onboard:RAZip6S84CM@0.0 |
| fence | right | 4092-4092 | 2 | chain-link catch fence | 3 | onboard:RAZip6S84CM@2.0 |
| kerb | left | 463-463 | 1 |  |  | onboard:RAZip6S84CM@16.0 |
| kerb | left | 1568-1568 | 1 |  |  | onboard:RAZip6S84CM@54.0 |
| tyre_wall | left | 266-266 | 1 | dark low wall / tyre wall round the outside of T2 | 0.8 | onboard:RAZip6S84CM@8.0 |
| tyre_wall | left | 330-330 | 1 | tyre / armco line far left at T2 |  | streetview:H9xspk4q_OoFIjVDhaMzDA@210 |
| tyre_wall | left | 1051-1051 | 1 | low dark wall / tyre line | 0.8 | onboard:RAZip6S84CM@38.0 |
| tyre_wall | left | 1117-1130 | 2 | black tyre stacks 2-3 high with a rail on top | 0.8 | onboard:RAZip6S84CM@40.0 |
| tyre_wall | left | 2202-2202 | 1 | black tyre wall line, recovery vehicles behind | 0.8 | onboard:RAZip6S84CM@74.0 |
| tyre_wall | left | 2371-2371 | 1 | dark low wall at the foot of the bank | 0.8 | onboard:RAZip6S84CM@80.0 |
| tyre_wall | left | 2434-2434 | 1 | dark low wall / tyre line at the foot of the bank | 0.8 | onboard:RAZip6S84CM@82.0 |
| tyre_wall | left | 3404-3404 | 1 | tyre bundles along the foot of the tall wall | 0.6 | onboard:RAZip6S84CM@114.0 |
| tyre_wall | right | 266-266 | 1 | low dark barrier line beyond the grass bank | 0.7 | onboard:RAZip6S84CM@8.0 |
| tyre_wall | right | 381-381 | 1 | dark tyre wall far right | 0.8 | onboard:RAZip6S84CM@12.0 |
| tyre_wall | right | 1513-1513 | 1 | dark low wall / tyre line at the foot of the spectator bank | 0.8 | onboard:RAZip6S84CM@52.0 |
| tyre_wall | right | 1568-1568 | 1 | dark low wall / tyre line | 0.8 | onboard:RAZip6S84CM@54.0 |
| tyre_wall | right | 1888-1888 | 1 | black tyre line | 0.7 | onboard:RAZip6S84CM@64.0 |
| tyre_wall | right | 2497-2497 | 1 | black-covered tyre barrier / dark panel wall | 1.3 | onboard:RAZip6S84CM@84.0 |
| tyre_wall | right | 3089-3089 | 1 | black covered tyre barrier | 1 | onboard:RAZip6S84CM@102.0 |
| tyre_wall | right | 3404-3404 | 1 | black tyre stacks 4 high, continuous | 1.1 | onboard:RAZip6S84CM@114.0 |
| wall | left | 266-266 | 1 | concrete Jersey end | 0.81 | onboard:RAZip6S84CM@8.0 |
| wall | left | 420-420 | 1 | low concrete wall at the foot of the terraces with a 'SONOMA TURN 2' style sign | 0.8 | onboard:RAZip6S84CM@14.0 |
| wall | left | 463-463 | 1 | low dark concrete wall at the foot of the terraces | 0.8 | onboard:RAZip6S84CM@16.0 |
| wall | left | 516-516 | 1 | low dark wall (tyre-faced or black concrete) at the foot of the bank | 0.8 | onboard:RAZip6S84CM@18.0 |
| wall | left | 655-655 | 1 | white low wall / armco end ahead-left | 0.8 | onboard:RAZip6S84CM@22.0 |
| wall | left | 710-710 | 1 | low dark concrete wall at the foot of the terraces | 0.8 | onboard:RAZip6S84CM@24.0 |
| wall | left | 900-909 | 2 | concrete wall below the stands |  | streetview:nA1oaDXwADSI7x-Pa-j4Ow@337 |
| wall | left | 968-1004 | 2 | light grey concrete wall end, catch fence | 1 | onboard:RAZip6S84CM@34.0 |
| wall | left | 1189-1189 | 1 | low dark wall far left | 0.8 | onboard:RAZip6S84CM@42.0 |
| wall | left | 1395-1395 | 1 | low dark wall far left | 0.8 | onboard:RAZip6S84CM@48.0 |
| wall | left | 2157-2157 | 1 | light blue-grey concrete wall end | 1 | onboard:RAZip6S84CM@72.0 |
| wall | left | 2215-2215 | 1 | concrete wall far left along the T7a stands |  | streetview:J6fsnW4hj4xCjQLzrgRGzA@54 |
| wall | left | 2268-2268 | 1 | low white wall at the foot of the terraces | 0.8 | onboard:RAZip6S84CM@76.0 |
| wall | left | 2440-2440 | 1 | concrete wall with a catch fence on the bank |  | streetview:xXQqyp9Q9sWv9ZLN2ORYsA@108 |
| wall | left | 2707-2707 | 1 | low dark concrete wall | 0.9 | onboard:RAZip6S84CM@90.0 |
| wall | left | 3018-3056 | 2 | light concrete wall | 1 | onboard:RAZip6S84CM@98.0 |
| wall | left | 3119-3119 | 1 | concrete wall with tall 'SONOMA RACEWAY' / Sunbelt board panels on top | 2.8 | onboard:RAZip6S84CM@104.0 |
| wall | left | 3492-3492 | 2 | light blue concrete Jersey wall (pit-in separation) | 0.9 | onboard:RAZip6S84CM@116.0 |
| wall | left | 3669-3669 | 1 | light blue concrete wall round the hairpin outside | 1 | onboard:RAZip6S84CM@122.0 |
| wall | right | 1051-1051 | 1 | light grey concrete wall at the foot of the bank | 1 | onboard:RAZip6S84CM@38.0 |
| wall | right | 1117-1117 | 1 | light grey concrete Jersey segments | 0.9 | onboard:RAZip6S84CM@40.0 |
| wall | right | 1395-1395 | 1 | light grey concrete Jersey segments | 0.9 | onboard:RAZip6S84CM@48.0 |
| wall | right | 1460-1500 | 2 | light grey concrete Jersey segments | 0.9 | onboard:RAZip6S84CM@50.0 |
| wall | right | 1956-1956 | 1 | light blue concrete wall beyond the Chute | 1 | onboard:RAZip6S84CM@66.0 |
| wall | right | 2314-2314 | 1 | light concrete wall with ad board | 1 | onboard:RAZip6S84CM@78.0 |
| wall | right | 2371-2371 | 1 | light grey concrete wall | 1 | onboard:RAZip6S84CM@80.0 |
| wall | right | 2434-2434 | 1 | light grey concrete wall | 1 | onboard:RAZip6S84CM@82.0 |
| wall | right | 2571-2571 | 1 | light grey concrete wall | 1 | onboard:RAZip6S84CM@86.0 |
| wall | right | 2644-2644 | 1 | dark wall with a 'SONOMA TURN 8' sign | 1 | onboard:RAZip6S84CM@88.0 |
| wall | right | 3089-3156 | 3 | light concrete wall with catch fence | 1 | onboard:RAZip6S84CM@102.0 |
| wall | right | 3203-3203 | 1 | light concrete wall | 1.1 | onboard:RAZip6S84CM@108.0 |
| wall | right | 3736-3736 | 1 | wall with ad boards far right | 1.5 | onboard:RAZip6S84CM@126.0 |
| wall | right | 3784-3784 | 1 | wall with Las Vegas / O'Reilly boards | 2.5 | onboard:RAZip6S84CM@128.0 |
| wall | right | 3843-3843 | 1 | wall with EchoPark boards | 2.5 | onboard:RAZip6S84CM@130.0 |

## HEIGHT mismatches (advisory)

- fence left s 2644: inventory 3 m (fence-post-ref) vs package 4 m (barrier 9 (concrete + 3 m fence) catch fence) [onboard:RAZip6S84CM@88.0]
- wall left s 3156: inventory 4 m (horizon-ratio) vs package 1 m (barrier 21 (concrete)) [onboard:RAZip6S84CM@106.0]
- wall left s 3203: inventory 4 m (horizon-ratio) vs package 1 m (barrier 21 (concrete)) [onboard:RAZip6S84CM@108.0]
- wall left s 3259: inventory 4 m (horizon-ratio) vs package 1 m (barrier 21 (concrete)) [onboard:RAZip6S84CM@110.0]
- wall left s 3326: inventory 3 m (horizon-ratio) vs package 1 m (barrier 21 (concrete)) [onboard:RAZip6S84CM@112.0]
- wall left s 3404: inventory 3.5 m (horizon-ratio) vs package 1 m (barrier 21 (concrete)) [onboard:RAZip6S84CM@114.0]
- wall left s 3577: inventory 5.2 m (door-ref) vs package 1 m (barrier 14 (concrete)) [onboard:RAZip6S84CM@118.0]
- wall left s 3600: inventory 5.2 m (horizon-ratio) vs package 1 m (barrier 14 (concrete)) [streetview:jrXpHaDfJT2APw6zcyBKRA@196]
- wall left s 3635: inventory 5.2 m (door-ref) vs package 1 m (barrier 14 (concrete)) [onboard:RAZip6S84CM@120.0]
- wall right s 3912: inventory 2.5 m (horizon-ratio) vs package 1 m (barrier 4 (concrete)) [onboard:RAZip6S84CM@132.0]

## Other MISSING runs (do not fail the gate: stands, stations, masts, tyre stacks, buildings, cone lines)

| kind | side | s (m) | rows | what (first row) | source |
|---|---|---|---|---|---|
| building | left | 91-91 | 1 | pit-exit building, red roof, glazed front | onboard:RAZip6S84CM@4.0 |
| building | left | 4092-4092 | 1 | pit garages, red roof | onboard:RAZip6S84CM@2.0 |
| building | right | 3259-3259 | 1 | tan buildings beyond the fence (infield) | onboard:RAZip6S84CM@110.0 |
| building | right | 3910-3910 | 1 | two-storey control tower building beyond the drag strip | streetview:QduY6QTXmw4JDevQVE_b-g@338 |
| cone_line | left | 968-968 | 1 | orange traffic cones across the Chute mouth | onboard:RAZip6S84CM@34.0 |
| cone_line | left | 2268-2268 | 1 | orange cones along the paved runoff | onboard:RAZip6S84CM@76.0 |
| cone_line | left | 2947-2947 | 1 | single orange cone on the grass (marker) | onboard:RAZip6S84CM@96.0 |
| cone_line | left | 3018-3018 | 1 | single orange cone on the grass (marker) | onboard:RAZip6S84CM@98.0 |
| cone_line | left | 3577-3577 | 1 | orange cones along the pit-in separation | onboard:RAZip6S84CM@118.0 |
| cone_line | left | 3912-3912 | 1 | orange cones in the pit lane | onboard:RAZip6S84CM@132.0 |
| cone_line | left | 3967-3967 | 1 | orange cones in the pit lane | onboard:RAZip6S84CM@134.0 |
| cone_line | right | 1888-1888 | 1 | orange cones | onboard:RAZip6S84CM@64.0 |
| cone_line | right | 2202-2202 | 1 | orange delineator posts (tall cones) on the island edge | onboard:RAZip6S84CM@74.0 |
| cone_line | right | 2268-2268 | 1 | orange delineator post at the island nose | onboard:RAZip6S84CM@76.0 |
| cone_line | right | 3660-3660 | 1 | traffic cone at the apron edge | streetview:jrXpHaDfJT2APw6zcyBKRA@196 |
| mast | left | 420-420 | 1 | light poles inside the fence line | onboard:RAZip6S84CM@14.0 |
| mast | left | 3699-3736 | 2 | light masts | onboard:RAZip6S84CM@124.0 |
| mast | left | 3843-3843 | 1 | light masts | onboard:RAZip6S84CM@130.0 |
| mast | left | 4024-4050 | 2 | light mast | onboard:RAZip6S84CM@0.0 |
| mast | right | 91-91 | 1 | light mast | onboard:RAZip6S84CM@4.0 |
| mast | right | 1568-1568 | 1 | light masts | onboard:RAZip6S84CM@54.0 |
| mast | right | 1626-1626 | 1 | light masts | onboard:RAZip6S84CM@56.0 |
| mast | right | 1687-1687 | 1 | light masts | onboard:RAZip6S84CM@58.0 |
| mast | right | 1742-1742 | 1 | light masts with tyre stacks at the base | onboard:RAZip6S84CM@60.0 |
| mast | right | 1810-1810 | 1 | light masts | onboard:RAZip6S84CM@62.0 |
| mast | right | 1888-1888 | 1 | light mast | onboard:RAZip6S84CM@64.0 |
| mast | right | 1956-1956 | 1 | light masts | onboard:RAZip6S84CM@66.0 |
| mast | right | 2268-2268 | 1 | light mast | onboard:RAZip6S84CM@76.0 |
| mast | right | 2314-2314 | 1 | light mast on a black block base | onboard:RAZip6S84CM@78.0 |
| mast | right | 2371-2371 | 1 | light masts | onboard:RAZip6S84CM@80.0 |
| mast | right | 2497-2497 | 1 | tall pole | onboard:RAZip6S84CM@84.0 |
| mast | right | 2571-2571 | 1 | light mast | onboard:RAZip6S84CM@86.0 |
| mast | right | 2707-2707 | 1 | light masts | onboard:RAZip6S84CM@90.0 |
| mast | right | 2773-2773 | 1 | light masts | onboard:RAZip6S84CM@92.0 |
| mast | right | 3089-3089 | 1 | light masts | onboard:RAZip6S84CM@102.0 |
| mast | right | 3156-3156 | 1 | light masts | onboard:RAZip6S84CM@106.0 |
| mast | right | 3326-3326 | 1 | light mast and flag pole | onboard:RAZip6S84CM@112.0 |
| mast | right | 3912-3912 | 1 | light mast and flag pole | onboard:RAZip6S84CM@132.0 |
| mast | right | 3967-3967 | 1 | light masts | onboard:RAZip6S84CM@134.0 |
| mast | right | 4024-4050 | 3 | light mast | onboard:RAZip6S84CM@0.0 |
| stand | left | 762-762 | 1 | concrete terraces (T3a-T4) | onboard:RAZip6S84CM@26.0 |
| stand | left | 2202-2202 | 1 | concrete terraces | onboard:RAZip6S84CM@74.0 |
| stand | left | 2707-2707 | 1 | concrete terraces (back straight) | onboard:RAZip6S84CM@90.0 |
| stand | left | 3967-3967 | 1 | main grandstand with suites deck and press box | onboard:RAZip6S84CM@134.0 |
| stand | left | 4024-4050 | 3 | bleachers with suites deck | onboard:RAZip6S84CM@0.0 |
| stand | right | 1395-1395 | 1 | spectator area on the bank with yellow railings / bleachers | onboard:RAZip6S84CM@48.0 |
| stand | right | 2033-2033 | 1 | concrete terraces on the T7a hill | onboard:RAZip6S84CM@68.0 |
| stand | right | 2112-2112 | 1 | concrete terraces with fence on top | onboard:RAZip6S84CM@70.0 |
| stand | right | 2157-2157 | 1 | concrete terraces with fence and light masts on top | onboard:RAZip6S84CM@72.0 |
| stand | right | 2854-2854 | 1 | grandstand far ahead-right (T11 area) | onboard:RAZip6S84CM@94.0 |
| stand | right | 2947-2947 | 1 | large grandstand with suites (T10/T11 infield side) | onboard:RAZip6S84CM@96.0 |
| stand | right | 3089-3119 | 2 | large grandstand with suites deck | onboard:RAZip6S84CM@102.0 |
| station | left | 381-381 | 1 | white marshal hut at the foot of the terraces | onboard:RAZip6S84CM@12.0 |
| station | left | 3492-3492 | 1 | marshal standing at a door in the tall wall | onboard:RAZip6S84CM@116.0 |
| station | right | 762-762 | 1 | white elevated marshal tower with roof | onboard:RAZip6S84CM@26.0 |
| station | right | 855-855 | 1 | white marshal post with roof | onboard:RAZip6S84CM@30.0 |
| station | right | 909-909 | 1 | white elevated marshal post with roof, on a platform | onboard:RAZip6S84CM@32.0 |
| station | right | 1320-1320 | 1 | marshal post with roof on the crest, vehicles parked | onboard:RAZip6S84CM@46.0 |
| tyre_stack | left | 3119-3119 | 1 | black tyre stack in front of the wall | onboard:RAZip6S84CM@104.0 |
| tyre_stack | right | 330-330 | 1 | brown block stacks far right (tyre bundles or hay bales) | onboard:RAZip6S84CM@10.0 |
| tyre_stack | right | 1395-1395 | 1 | long black tyre stack beside the station box | streetview:GMaTaipEd9Hm7fMNE26aGQ@215 |
| tyre_stack | right | 1626-1626 | 1 | single black tyre stacks on the runoff | onboard:RAZip6S84CM@56.0 |
| tyre_stack | right | 1687-1687 | 1 | black tyre stack | onboard:RAZip6S84CM@58.0 |
| tyre_stack | right | 3056-3056 | 1 | stack of 2 grey tyres on the apex | onboard:RAZip6S84CM@100.0 |
| tyre_stack | right | 3635-3699 | 4 | red/white painted barrier blocks / barrels on the apron | onboard:RAZip6S84CM@120.0 |

## UNSUPPORTED objects

| kind | side | s (m) | object | src |
|---|---|---|---|---|
| wall | right | 705-829 | barrier 0 (armco) | osm:380830042 |
| building | left | 409-414 | building 12 '' 3.2 m | osm |
| building | right | 3406-3432 | building 13 '' 12.5 m | osm |
| building | left | 157-191 | building 15 '' 6.6 m | osm |
| building | left | 2697-2700 | building 18 '' 3.2 m | osm |
| building | left | 2254-2259 | building 19 '' 4.3 m | osm |
| building | left | 483-490 | building 20 '' 7.5 m | lidar |
| building | left | 495-506 | building 21 '' 7.7 m | lidar |
| building | left | 815-818 | building 22 '' 7.7 m | lidar |
| building | left | 549-565 | building 23 '' 3.9 m | lidar |
| building | left | 818-821 | building 24 '' 7.7 m | lidar |
| building | left | 822-825 | building 25 '' 7.7 m | lidar |
| building | left | 3429-3446 | building 26 '' 3.6 m | lidar |
| building | left | 2152-2160 | building 27 '' 6.6 m | lidar |
| cone_line | right | 2800-2804 | cone line 0 | closed road 2020 fast bypass (8a to T10) mouth |
| cone_line | right | 3087-3090 | cone line 1 | closed road 2020 fast bypass (8a to T10) mouth |
| cone_line | left | 995-1001 | cone line 2 | closed road the Chute (NASCAR short course, T4 to T7) mouth |
| cone_line | left | 2159-2166 | cone line 3 | closed road the Chute (NASCAR short course, T4 to T7) mouth |
| cone_line | right | 3952-3954 | cone line 4 | closed road drag strip mouth |
| cone_line | right | 1680-1688 | cone line 5 | closed road drag strip mouth |
| cone_line | right | 3498-3504 | cone line 6 | closed road T11a shortcut mouth |
| cone_line | right | 3912-3915 | cone line 7 | closed road T11a shortcut mouth |

## Pit lane: walls with no barrier in the package

- left s 20: low white pit-box wall (box 8) [onboard:24of8fjjAug@296]
- right s 3610: Jersey barrier separating the pit-in lane from the track [onboard:24of8fjjAug@1452]
- left s 3680: concrete wall [onboard:24of8fjjAug@1458]
- left s 4010: low white pit-box wall with box numbers [onboard:24of8fjjAug@288]
- left s 4060: low white pit-box wall (boxes 16, 15) [onboard:24of8fjjAug@292]

Caveats: stations come from the time-to-station map (leave-one-out residuals 1-33 m, see inventory.md), so a row near the end of a package object can show as MISSING by a few metres; the side view sheets (compare_sheets/) settle each one. The cone lines the closed-road rule placed at the Chute, bypass, drag-strip and 11a mouths are UNSUPPORTED because no inventory row sees them and their src cites OSM only: confirm each on the onboard or a capture, or remove it.
