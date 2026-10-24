# Buttonwillow judge round r3 (20 Oct 2026, ~20:00 PDT)

Judge: **GPT 6 Astra through codex** (same invocation as r2), seven batches of seven sheets over the 49 sheets of round 3, two
streams, 19:35-19:54; prompt and raw tables in `judge_r3/` (`prompt.md`, `astra_b1..b7.md`). Package: branch buttonwillow
773b8a4 (merge 849c19f), rev e08631e61f, 4697.634 m. The orchestrator (Claude) verified the round first (tests, build, Laguna
+ Sonoma diffs, fresh stage-1 run byte-identical with 24 gate lines ok, Acceptance 6 on the merged branch: Sonoma byte for
byte, Laguna heightfield + d4e8634710813961, TS gates + coverage ok, hood set 1.10 PASS on the new zones), then checked Astra's
rows against the package, the stills and the frames. Pit sheets 03-05 and runoff_04 carry no frame or no logged object:
unjudged.

## What the orchestrator settled

| row | finding | check |
|---|---|---|
| "kerb MISSING" at 600 R, 1300 R, 1450 L, 1500 R (fwd), 1304-1309 R and 4065-4122 R (side) | the strips exist (580-609 R, 1288-1308 R, 1429-1478 L, 1482-1507 R, 4087-4120 R) but are SHORT runs that end 7-10 m past the camera, inside the hood's blind zone, while the onboard's block lines run on 30-60 m (T2 apex to ~640, T4 exit past 1330, 1430 to the T5 apex, the T5 inside kerb to its exit, 4065-4122 R per the inventory). The side still at 1309 R shows its strip beside the car; the forward still at the same station cannot | TRUE as **kerb run extents**, not missing objects: measure every run's start and end on the captures and the onboard, one table, extend the strips |
| 7 strips still inside the road (550-556 L -2.7 m, 583-590 L -2.8, 1842-1848 L -6.1, 548-554 R -5.3, 600-609 R +1.25, 1922-1931 R -3.0, 4061-4070 R -3.75) | Astra fwd_13 4050 R: "broad isolated pale blocks extending into the asphalt" = the 4061-4070 R strip drawn 3.75 m inside the edge | TRUE: each is a block line the edge must reach (zone) or a false detection to drop |
| pit-lane cone runs (pit_01 4513-4589 R EXTRA) | the package has 162 + 219 cones along both K-rails; the pit video frame at 21:43 (t1303000) shows a few cones at the tower's foot and none along the walls | TRUE (EXTRA): keep only the cones the frames show |
| timing tower (fwd_15, side_12/13, pit_01/02, runoff_01) | now tan with a blue roof and a red/white K-rail in front (big step from r2), but an elongated box along the track with a continuous dark upper band; the pit video (t1303000) and t150-152 show a COMPACT two-storey building, the upper storey an open deck with posts and railing under a deep roof overhang, divided glazing, external stair on the track side, ~8 m | TRUE: footprint from the capture, not the OSM box; upper storey as an open deck |
| stations | r2 said "enclosed cabins", r3 says "open frame over a tan/black pedestal" and names stations whose footage HAS a dark / blue lower body (T8 2762 R clearly on the frame; 2250 R, 3150 R, 3350 R, 3650 R) or a pale substantial base (450, 800, 1000, 2000-2050 R) | TRUE per station: the lower body comes from each station's own frame (open / blue-panelled / pale base); the mound as a rounded earth mound with its tyre face, not a rectangular pedestal (side_01 477 R); the pit-wall stand (4679-4690 R) a compact raised platform with rails, a ladder and a small canopy |
| paved aprons "MISSING" at 350 L, 650 L, 1700 L (fwd), 574 R hard-edged and pale (side_02) | the onboard shows broad paved aprons (the T1-exit apron, the T2 outer loop, the T5 exit apron) where the sim reads as unpaved; the T2 inside patch has an angular, much paler boundary | CHECK: each is a paved zone with a pavement look and a soft edge, or it is not paved |
| cones | FALSE (placed, too small for the sheet): 150 R (side_00 146 shows them), 300 R, 550 L, 900 L (side_03 893 shows them), 1050 R, 2150 R, 2700 L, 4550 / 4600 R. TRUE or CHECK: 3200 R (a cone on the right, fwd_10), the 3200-3250 L cluster density (several vs one), 1920 R and 2000 R beside kerbs, 2200 R, 2800 L (back_04), 4573 R EXTRA (a line where the onboard has one cone: the 4575 / 4593 singles + the 4607 mouth read as one line), the runoff closures still open from r2: 170 R (a clear row defining the paved branch), 294 R, 46 R, 4068 R | as marked |
| pit lane (pit_00-02) | paddock mesh fence ~1.5 m along the entry 4294-4340 L MISSING; the entry shelter 4317-4340 R MISSING; a pale verge between the lane and the left wall where the footage has pavement to the wall; the separation-barrier nose at 4489 R bulky and rounded vs a square block; ground-coloured patches on the entry strip (NAIP texture) | TRUE / CHECK on the pit video frames |
| back_07 4200 (driving-left) | a long dark tyre barrier under the trees, 0.7-1.0 m, MISSING | CHECK on c20_s4300 and t136-t138 |
| masts 3500 R (floodlight head), 3256 R | still open from r2 | kit item (a light cluster) / capture pin |
| kerb colour at distance (1648 L, 1831 L "no blue") | the blue reads dark at 50 m+; the close frames match the new palette | low priority, note |
| T10 3750-3800 | r2's open question: the agent showed the two hood frames were the same video frame and the captures + t126 put the line on the right; Astra r3 repeats the r2 row | FALSE (settled in round 3) |
| widths: T2 534-632 (6.65 m) and T4 1034-1115 (8.8 m) | the inside edges on the block lines; the outer edges at tone changes | HELD for the owner's mark-ups (sent 19:45) |

## Ten worst rows of the lap (orchestrator's order)

1. Kerb runs far shorter than the block lines (T2 apex, T4 exit, 1430-1500 L, the T5 inside kerb, 4065-4122 R): a systematic extent pass.
2. The timing tower's shape (elongated box, closed upper band) against the compact open-deck building in the footage.
3. The stations' lower bodies: one open-canopy style for all where the frames show dark / blue bodies at T8, T9, T10 and others, and rectangular pedestals for the mounds.
4. Pit lane: hundreds of cones along both walls the video does not show; the pale verge; the barrier nose; the entry fence and shelter.
5. Seven kerb strips drawn inside the road (up to 6 m), visible as pale blocks on the asphalt.
6. Paved aprons at the T1 exit, the T2 outer loop and the T5 exit reading as dirt; the T2 inside patch hard-edged.
7. Cone rows the footage shows (3200 R, the 3200-3250 L cluster, 1920 R, 2000 R, 2800 L) and the runoff closures still open (170 R, 294 R, 46 R, 4068 R).
8. The tyre barrier under the trees on the T11 approach (back_07 4200), if the capture confirms it.
9. The floodlight head on the 3500 R mast; the 3256 R mast.
10. Kerb colour / block length at distance.

Settled since r2: the T2 inside block line is a kerb zone with strips and a paved patch; the K-rails carry their red sections;
the tower is tan with a blue roof; the three exits hold; the hood set passes; the geometry rebuilds byte for byte on the merged
pipeline, and Sonoma and Laguna still rebuild to their references.
