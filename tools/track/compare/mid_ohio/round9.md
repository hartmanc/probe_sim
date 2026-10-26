# Mid-Ohio round 9: the control tower with its red pyramid roof, and the starter's stand

Opus 5.5, 27 Oct 2026, branch `mid-ohio` (from c75544d, package rev cf609d6a3e). The owner: "Please have the agent model
the Mid Ohio control tower ... It should have the red pyramid roof". One object (with the starter's stand beside it);
nothing else changes: track.json, heightfield.bin and ghosts.json stay byte-identical to round 5, and no other scenery
entry changed.

Reference: owner-supplied photo, ARCA 2024, pit straight
(`/Users/cobyhartman/.claude/jobs/dc9b3c29/tmp/ref_mo_tower/pitbox-midohio2024-owner-ref.jpg`, the orchestrator's
1200 x 682 screenshot; reference only, never a texture, not copied into the worktree, not committed), with the N837 t127 /
t129 frames (Apr 2026), the 360 lap t022 / t024 (Jul 2025) and the 2019 lidar (round8.md 1c: roof 19 x 18 m, eaves 17 m,
top over 20 m, 24 m with the mast).

## What the photo shows and how it is declared

| element | photo | declaration (`structures`, config.py) |
|---|---|---|
| body | tan masonry, roughly square, four storeys of window bands | block 13 x 13 m, 4 storeys to 10.0 m, wall #c9b59a, dark window bands (`band_frac` 0.40-0.82) |
| galleries | two open galleries wrapped round all four sides, railings, people | `wrap_decks` at 12.2 and 14.6 m, 2.6 m out (to the column line), dark 1.05 m railings, grey floors |
| sponsor band | a blue band on the lower gallery on every side, "COOPER TIRES" white on blue | new opt-in `banner` {half 9.1, z 10.0, h 2.2, names [('COOPER TIRES', '#1f4fa0', '#ffffff')]}: typed text panels on all four faces (no logo artwork, the Laguna rule) |
| frame | black corner columns from the ground to the eaves, standing outside the body | new opt-in `columns` {half 8.9, z1 17.0, 0.45 m, #1c1e21} |
| roof | a large red pyramid (hip, no ridge) roof with wide eaves well outside the body | `hip` {rise 5.5, overhang 3.0 (eaves 19 m square, the lidar's 19 x 18 m), z 17.0 (the lidar eaves; new opt-in `hip.z`), colour #c8302a}; ridge 0 = a pyramid |
| crow's nest | a small open platform with railings and a flag pole above the apex | new opt-in `nest` {2.2 m square at 23.0 m on four legs from the apex, rails 1.1 m, pole 4.5 m} |
| starter's stand | left of the tower on the pit wall: a small red-roofed cabin on a tall open black scaffold, a white board under the cabin ("ZINSSER"), a green flag | new opt-in structure type `starter_stand` {6.5 x 2.6 m cabin on 7.6 m legs with cross braces, cabin 2.0 m, red roof slab, the typed board 'ZINSSER' red on white under the cabin}, at its post on the pit wall (c20_s3560 / c20_s0000; N837 t130, 360 t024); replaces round 7's box on a post |

Proportions from the photo at 0.066 m/px (the 17 m lidar eaves over ~258 px from the ground): the body to ~10 m, the band
~10-12 m, the galleries above to the eaves, the apex ~22.5 m, the nest ~23-25 m; the stand against the 1.04 m pit wall
(~0.06 m/px): the board's bottom ~5.8 m, the cabin floor 7.6 m, its roof ~9.6 m. Not modelled: the flags (the green
starter's flag, the US flag on the pole), the people, the gallery railings' open mesh (solid dark rails), the
stand's small side boards.

## Kit changes (opt-in, every other track unchanged by construction)

`src/app/structures.ts`: block keys `columns`, `banner`, `nest`, `hip.z` (absent on every other block); the structure
type `starter_stand` (no other track declares it); the label pass draws a block's `banner` and a stand's `board` (only
when present). `tools/track/build_structures.py`: passes `starter_stand` through with its ground height. Proof: the
structure soups of Sonoma, Laguna and Buttonwillow hash the same before and after (`r7/soup_hash.ts`: f71411f3c2e78626,
e3b0c44298fc1c14, 3da76e09e950dd5a).

## Stills and the side-by-side sheet (from the published package)

`compare_sheets_r9/` (local): `sheet_tower_r9.jpg` (the photo crop beside the sim from the infield; N837 t129 beside the
sim hood at s 3550; the 360 lap t024 left beside the sim turned left at s 3557; the photo's stand beside the sim's stand
and tower), and the poses `tower_close_r9`, `stand_close_r9`, `photo_view*_r9`. Shot after the last publish
(scenery.json written 16:04:24, the sheet 16:04:40).

Judged against the photo and the frames: the red pyramid roof with wide eaves over open galleries on black corner
columns, the blue COOPER TIRES band on all four sides, the crow's nest and mast, the tan body, and the starter's stand on
its scaffold with the ZINSSER board read as the real ones. Differences left: no flags; the galleries' rails are solid;
the body's window bands are more regular than the photo's.

## Gates, proofs, registry, tests

`build_track.py --track mid_ohio --stage scenery --publish` exit 0, every line `[ok]` (21, ground lines strict, 0 open;
coverage 251 rows, 0 MISSING, 0 UNSUPPORTED; the four 'placed' dispositions name 'Control tower'). On the package:
`run_gates.ts`, `run_coverage.ts`, `edge_gate.py` exit 0.

**Package rev eeee12ff99** (registry `mid_ohio.rev`).

Identity: track.json, heightfield.bin, ghosts.json `cmp`-identical to round 5; Sonoma stage 3 from its published files:
scenery.json and far_heightfield.bin identical; Laguna stage 3 on its reproduction: four outputs identical to the
b5343d7 builder's; Buttonwillow `--stage all --out tools/track/out/bw_idcheck` (rc 0): all seven files identical to
`public/tracks/buttonwillow`; structure soups of the three identical (above).

Tests: `npm run build` ok; full `npx vitest run` 64 files, 537 tests passed.

## Open

The flags, the open railing mesh, the irregular window pattern of the photo; everything round 8 left open stands.
