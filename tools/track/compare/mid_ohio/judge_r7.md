# Mid-Ohio round 7: judge table (compare_sheets_r7)

Judge: the builder agent (Opus 5.5), with the JUDGE.md prompt and checklist. **GPT 6 Astra was not available** (the
brief: "Astra is unavailable: the orchestrator judges too"); a builder judging its own sheets is the weak case JUDGE.md
warns about, so the orchestrator's independent pass over `compare_sheets_r7/` (local, 67 sheets: fwd 18, side 36, back 6,
pit 5, runoff 2) is still required before the owner drives.

Sheets: `camera_walk.ts` (356 stills of the published package: fwd 72 every 50 m, rows left 112 / right 101, back 36,
pit 25, runoff 9) and `r7/make_sheets.py` (SIM left; the N837 hood frame of Apr 2026 and the 2025 360 lap at the mapped
station right; the pit lane has no driving video, so its references are the 360 lap's left views from the track).
Every sheet was read; the first pass (build 9) gave the findings below, fixed in builds 10-11, and the fixed places
were re-shot (`/tmp` stills, the replayed walk).

## Findings (first pass) and their disposition

| # | sheet | s (m) | side | kind | onboard shows | sim showed | verdict | fix |
|---|---|---|---|---|---|---|---|---|
| F1 | side_04, fwd_05 | 382-458, 1030-1102 | R, L | kerb | saturated yellow (224-234, 173-193, 11-68) and red kerb paint in sun | washed-out yellow / pink (palette from the overcast N837) | WRONG_COLOUR | palettes from the sunlit 2025 frames (`rw` #c8443c / #e2ddd4, `yel` #e2b21c, `red` #c8443c) |
| F2 | fwd_05 | 1100 | L | kerb | yellow kerb with red outer band | the same, faded | OK_DIFFERENT after F1 | - |
| F3 | fwd_03-04, fwd_09, fwd_15 | 790-858, 1776-1898, 3022-3053 | L, L, R | sign | 300 / 200 / 100 boards before the Keyhole, 500 / 400 / 300 / 200 / 100 before T4, 200 / 100 before T11 (N837 t029-t031, t059-t060, t106) | one board each where the inventory had a row | MISSING | 12 boards from the frames (`brake_boards_declared`), 100 ft spacing back from the 360 lap's 100 board at T4 |
| F4 | fwd_03 | 680 | R | cone_line | four orange cones across the chicane mouth (N837 t026-t027, Apr 2026) | open mouth | MISSING | `closed_roads[inner chicane].mouth_cones` (and two cones left at s ~840, t029-t030); inventory rows added (`added`, round 7) |
| F5 | fwd_09 | 1800 | L/R | sign | stacked digits ("3 / 0 / 0") on tall boards | one big "0" (the 3-2-1 board texture) | WRONG_TYPE | app `boardTexture`: multi-digit boards stack their digits (opt-in by text length; Laguna's one-digit boards unchanged) |
| F6 | fwd_10 | 2000-2100 | R | tower | the tall scoring pylon right of T5 | nothing (the inventory's 'tower' kind is not a placed kind) | MISSING | structure 'T5 scoring pylon' from the 2019 lidar column (4 x 4 m, 30.7 m) |
| F7 | fwd_17 | 3500-3560 | L | building | starter tower: tan / brown walls, red hip roof, slender | a 17.6 m dark cube | WRONG_COLOUR / size | walls 10.5 m square under the roof's footprint, tan wall colour |
| F8 | fwd_17 | 3550 | L | tower | the starter's stand: a cabin with boards on black legs | a blue box on a post | OK_DIFFERENT | kept (the kit's scoring_tower; colour of the 2026 PERMCO boards) |
| F9 | fwd_14 | 2800-2850 | ahead | bridge | PERMCO / Pumps and Motors banner (N837 t100-t101) | plain deck | MISSING | `bridge_banners` (PERMCO face, VELO far face from back_04) and Firestone / HONDA on the T1 footbridge |
| F10 | fwd_04 | 900-950 | L | boards | the Keyhole board wall | present (PERMCO, HRC, SUMMIT, HONDA, START, O'REILLY) | OK | - |
| F11 | fwd_01 | 200-250 | L | paint | the pit-exit ladder line | missing | MISSING | `paint_lines_declared` (two 0.15 m lines 0.8 m apart; rungs not drawn) |
| F12 | fwd_07, fwd_10 | 1330-1600, 2150 | road | road_edge | clean asphalt | dark tree shadows baked into the 2022 NAIP road | WRONG (C17, C21) | `ortho_paint_over` dark on 17 stretches found by a road-luminance scan; 2140-2205 widened after the re-shoot |
| F13 | side_00, pit_00 | 0-200 | L | building | single-storey white pit garages with red roof bands | grey two-storey window boxes | WRONG_TYPE | structures 'Pit garages east / west' (garage kit, white walls, red band, doors) |
| F14 | side_19 | 1792-1898 | L | fence | catch fence over the armco in front of the bleachers (N837 t059-t060) | armco only | MISSING | fence 2.3 m on OSM 1315208940; inventory row added |
| F15 | back_04 | 2900 | ahead | bridge | VELO on the PERMCO bridge's far face | PERMCO | WRONG | far face VELO |
| F16 | runoff_00 | 212 | L | boards | VELO banners on the pit wall toward the footbridge | plain wall | MISSING | `wall_boards` on 'pit wall' s 150-212 |
| F17 | side_33 | 3410-3426 | L | boards | HONDA banners along the pit-in barrier, yellow barrels at its head | black barrier (boards first drawn behind it) | MISSING | `wall_boards` on 'pit-in barrier', off 0.15 (re-shot: visible) |
| F18 | side_28 | 2870-2880 | L | boards | VELO banners on the fence at the bridge | none | MISSING | `wall_boards` on OSM 1315208933 |
| F19 | side_19 | 1813 | L | stand | silver aluminium bleachers | dark grey slab (shaded rows) | OK_DIFFERENT | rendering: the rows face the track; lit from behind in the stills; open |
| F20 | fwd_00, pit_00 | 0-130 | L | paint | the lane's white box lines, people and tents (event dress) | plain lane | OK_DIFFERENT | event dress not modelled; the rule box lines are drawn |
| F21 | side_09-11 | 890-1019 | R | kerb | long red / white Keyhole apex kerb | present, raised 5 cm | OK | - |
| F22 | fwd_12 | 2400-2460 | L | kerb | yellow T7-exit / T8 crest kerbs | present | OK | - |
| F23 | side_23 | 2146 | L | station | station 5 sign post with a pop-up canopy (2025) | none | OK_DIFFERENT | dispositioned (manifest: temporary) |
| F24 | side_00-02 | 0-200 | R | stand | covered grandstand with two tiers | covered stand with roof and middle band | OK | - |

Ten worst (first pass): F12 (shadows on the road at hood level), F1 (kerb colour), F3 (the board rows the owner brakes by),
F13 (pit garages), F6 (the pylon), F7 (tower), F4 (event cones), F17, F9, F14. All fixed in builds 10-11 except F19
(rendering, open) and F8 / F20 (acceptable).

## Checklist (C1-C21), per sheet group, final package

| group | C1 ends | C2 joins | C3 facings | C4 extents | C5 heights | C6 bands | C7 contain | C8 cones | C9 pit | C10 blend | C11 kerbs | C12 stands | C13 huts | C14 boards | C15 logos | C16 movable | C17 tone | C18 closed | C19 supports | C20 bldg | C21 ground |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fwd 00-17 | ok (2 known exposures) | ok | n/a | ok | ok (armco 1.2 m, fences 3.5 m) | FINDING: ground-line advisory 107 open | ok | ok after F4 | ok | ok after F11 | ok after F1 | ok | ok | ok after F3 / F9 | n/a | n/a | ok after F12 | ok | ok | ok after F7 | ok after F12 |
| side 00-35 | ok | ok | n/a | ok | ok | as fwd | ok | ok | n/a | n/a | ok | FINDING F19 (look) | ok (one tower) | ok after F16-F18 | n/a | n/a | ok | ok | ok | ok after F13 | ok |
| back 00-05 | ok | ok | n/a | ok | ok | as fwd | ok | ok | n/a | n/a | ok | ok | n/a | ok after F15 | n/a | n/a | ok | ok | ok | ok | ok |
| pit 00-04 | ok | ok | n/a | ok | ok (pit wall 1.04 m) | n/a | ok | n/a | ok (open end to end, gate) | ok | ok | n/a | n/a | ok | n/a | n/a | lane a touch paler than the track in some stills (match_track_tone k 0.5): open | n/a | ok | ok | ok |
| runoff 00-01 | ok | ok | n/a | ok | ok | n/a | ok (allowed, no barrier in the footage) | ok | n/a | n/a | n/a | n/a | n/a | ok | n/a | n/a | ok | ok (grey asphalt) | n/a | n/a | ok |

C6: the unmodelled-ground-lines scan is advisory on this track (no `scenery.ground_lines` config): 107 lines (35
barrier-related) are listed in the build log and not dispositioned this round (open, round7.md).
