# Sonoma round 14D: the owner's decisions of 25 Oct 2026 and the round-14B judge's non-gate rows

Branch `sonoma-r14d` (from `integration` 893c961; package rev f399cda140 before). Scenery only. Nothing pushed or deployed.

**State: UNBUILT.** The Mac was on battery (86-89 %, discharging) for the whole of this pass, so no stage build, test run or
render was launched (the owner's machine-health rule). The config, the measurements, the inventory rows and the tool changes
are committed (WIP commit b11ce1a). The gate table, the kerb test numbers, the identity proofs, the stills and the package
rev follow when the power source is back.

Frames: `round14d/frames/` (local, reference only, never committed), captured in the agent's own Chrome tab from the watch
page, muted and paused, the frame drawn from the video element onto a canvas. Measurements: `round14d/measurements.json` and
`round14d/t11_profiles.json` (committed evidence).

## 1. T11 hairpin outside: a deep tyre wall and a thick white wall, no apron (owner)

The owner (OWNER_NOTES.md): "there is a deep tire wall at T11 ... from just before station 3648 (so it can encapsulate the
white wall section), all the way around the outside of T11. There is no apron. I think the white is just a thick wall (maybe
a SAFER barrier)". His correction: the 6 ft in his frame is the tyre wall's END.

Measured:
- **The band (2026 captures).** `compare/profile_measure.py` on c20_s1265 / c20_s1320 / c20_s1375, every 4 stations from the
  left edge outward, gives `t11_profiles.json`. One light run starts at s 3648 (k 3650) and ends at s ~3730. It runs from
  0.1-0.6 m to 3.6-3.8 m beyond the edge at s 3650-3700, and to 2.2-2.9 m at s 3704-3728, where the exit wall comes in.
  Before s 3646 there is only the Jersey's 1.0-1.4 m.
- **The white wall's width.** At s 3734-3744 the white exit wall ('T11 exit to T12, left') leaves the band. There it reads
  0.96 m wide (k 3736 / 3740 / 3744: -0.16..+0.84, -0.04..+0.92, -0.08..+0.88 m).
- **The onboard.**
  - 7hJizPBNrJ4 (a Porsche GT3 RS lap uploaded 16 Aug 2019, before the 2023-24 repave). T11 of lap 3 is at video t 5-9.5;
    the owner's frame is t 7.5. At t 6.5-9.5 a dark (black) tyre wall runs round the whole outside, from where the white
    wall at the entry ends.
  - RAZip6S84CM (March 2026). t121.5 / t122.5 / t123.25: a light-blue face round the outside from the entry, with the catch
    fence posts set back behind it. t123.25 / t124: white stacks from s ~3698 to the exit.
  - Source precedence: the 2026 onboard sets the colours, the owner's decision sets the structure.
- **Heights.** The stacks are two tyres high, 0.8 m (t122 / t124, round 7). The white wall is 0.81 m, the same as the exit
  wall it joins (onboard 2:07). The fence top stays at 3.0 m (rounds 5 / 7). The fence posts are curved-top (inventory s
  3638 / 3670).

Declared (config `declared_walls`):

| run | rows / width | line (m beyond the left edge) | s | colour |
|---|---|---|---|---|
| deep tyre wall, light-blue face | 4 rows | front row 0.55 (face 0.24, on his red); back face 2.66 | 3645.5-3698 | light blue (#d3dbe0) |
| deep tyre wall, white stacks | 4 rows | the same | 3698-3704 | white |
| thick white wall | w 0.96 m, h 0.81, fence 2.2 with curved-top arms | 3.30 (back face 3.78, the band's outer edge); then straight to the exit wall's head at s 3712 (joined) | 3645.5-3712 | #e6e4de |
| old 'T11 hairpin, left tyre wall' | 2 rows | its last four declared points, snapped onto the exit wall by tyre_facings as before | 3708-3730 | white |

- **Why 2.75 m between the tyre line and the wall line.** tyre_facings moves any tyre point within 2.6 m of a rigid line onto
  it, and the side-by-side gate fails a parallel tyre run 0.8-2.5 m off a wall. At 2.672 / 2.718 m (checked on the declared
  polylines) neither applies, and the back row's face (2.66 m) stands 0.12 m in front of the wall's face (2.78 m).
- **No apron.** The tyres fill the band from the edge to the white wall.
- **Left as before.** From s 3704 the band narrows to 2.2-2.9 m and the white exit wall comes in to 1.6-2.3 m. Four rows do not
  fit there. The round-7 2-row white facing (snapped onto the exit wall) stays, so up to ~1 m of ground remains between the
  edge and the stacks at s ~3704-3712.
- **The pit-lane walls entry** for the T11 outside wall (pit row s 3680) now names the thick white wall.

Tool support (identical without the new keys):
- `rows` on a tyre run: the app draws row k at k x 0.6 m to the polyline's left. The builder passes `rows` and `w` through.
  The gates `tyreFaces` and `joinFaces` measure the drawn extent, and `joinFaces` the wall's own half width.
- `w` on a concrete run: its drawn thickness.
- The physics is untouched. It collides with rows 0 and 1 as before, so the front face (row 0) is the contact face. The back
  rows stand behind it and cannot be reached.

## 2. T9A right-hander: kerb 24 (owner; corrects the judge agent's round-14B FALSE)

The owner: "Onboard RAZip6S84CM at s ~3050 looks to have his front right tire on the kerb."

Measured on RAZip6S84CM at 0.25-0.5 s around 100 s (frames RA_t099.0-100.0_kerb24.jpg, RA_t099.75-100.25_kerb24_end.jpg):
- At t99.5 the kerb lies ahead at the apex.
- At t100.0 the right front is on the kerb's last blocks, and the kerb ends abeam the stack of two grey tyres (landmark s 3047,
  1.5 m out).
- At t100.25 only the white line on the grass remains.

So the owner is right that the car is on the kerb at the onboard's s ~3050. The onboard station map reads several metres early
there, and this is the kerb's end. The kerb runs to **s 3046**, not 3044. Nothing in the 2026 frames shows a kerb beyond the
grey tyres.

The new end is the round-14B `kerb_inside` world point (219.96, 28.24) at s 3046.0, where the fitted edge already carries the
kerb's 0.65 m (the "extra racing surface"). So **no geometry change** is needed: the strip is extended 3044 -> 3046 as a
physics kerb with the track's profile. The captures cannot place the end: trucks are parked over the apex on c20_o0660 /
c20_s0660. Width 0.65 m (t100: about one tyre stack's width).

The kerb traversal test at T9A follows the build.

## 3. T1 service-road mouth: no cones, a white line (owner)

"Delete the cones entirely. There should be a white painted line that follows the outside arc of the track at the service
road mouth."
- `scenery.owner_mouths_r14` has cones=False, so owner_mouth_cones draws no line for it.
- A `paint_lines_declared` row draws a 0.12 m white line on his arc: owner/r14/mouths.json, the same 8 points. It is draped by
  marks_on_surface like every other ground mark.
- The inventory has no row citing cones at this mouth, so no row was corrected.

## 4. The T4 wall head at left s 736 (owner, decisions page Q3)

"Cushion", the owner's choice, knowing that c20_s2420 shows the head bare.
- A 2.0 m black tyre cushion goes on the wall's line extended upstream from 0.5 m before the head (head ENU -334.42, -26.06).
  2.0 m is the size of the lap's other cushion, the drag-strip bundle. tyre_facings stands it 0.55 m to the track side, as it
  did the bundle.
- `gates.known_exposures` is now empty, so the wall-ends gate must pass the head by the cushion.
- Inventory row: s 734 left, tyre_wall.

## 5. The round-14B judge's non-gate rows

| row | verified against | change |
|---|---|---|
| A10 / A11 T7 road left: edge line and pale shoulder | t066 / t068 / t070 / t072: dark asphalt to the wall's foot, no paint; t064: the drag strip's SW line to the fork | `edge_line_cut` and `track_shoulder_cut` left s 1909-2150 (fork vertex to the T7 approach wall's end) |
| B7 T9A mouth: the course line fades along the arc | needs a still (the line is declared to s 3059) | pending the build: cause to find on the render |
| C1 pit-in separation: red / white wrapped tyres | s3600 crop, t119.5 (red / white panels over tyre tops), t119.5-t121 (the Jersey light blue to the hairpin) | a 2-row tyre facing on the Jersey's line 0.55 m to the track side, s 3592-3604, red / white in turn every 1.25 m (tyre colour sections, a new app path); the Jersey light blue (was red). From s 3606 the Jersey stands 0.55 m from the edge: no room for a facing on the course side. Inventory row s 3591.5 (inventory lap) |
| C3 T11 infield apron seam | needs the stills (hairpin_3760 / 3800) | pending the build |
| A5 pit wall panels s 111-150 | t004.0 / t004.5: red panels with white logos on the upper face of the paddock-side wall across the pit-out lane | plain red panels 2 m long, 0.55 m tall, 0.4 m up (`wall_boards`); no logo art |
| A3 T2 footbridge | s0250 / t008: the boards hang on the span, lattice end sections at both piers, no roof | `bridge_style` 'truss': no roof, a top chord each side, lattice ends over 4.5 m at each pier (app) |
| A15 T7 Toyota boards | s2100 / t070: red with white TOYOTA, then white with dark TOYOTA | the names alternate |
| B12 T10-entry boards | t103.5 / t104.5 / t105.5: one long SONOMA RACEWAY panel, two green SUNBELT RENTALS, then small white TOYOTA panels | three `wall_boards` rows (14 m / 2 x 5 m / 3 m panels) |
| B14 catch-fence posts | the inventory's "curved-top posts" rows (s 414-3421, 3638 / 3670) | `fence_arm` (0.5 m at 45 deg, as measured at the pit-out) on the ten fenced walls those rows lie on, and on the new T11 white wall |

Unchanged by the owner's decisions: the T4-approach head now has its cushion (item 4); the T9A junction-corner exemptions; the
chicane line margin; the AI.

## Inventory and manifest

- `inventory.json`: five rows added (attrs.round '14D'), each with its source.
  - T11 tyre wall 3643.5 and 3693.5, and the white wall 3643.5, all on the inventory lap (the package's lap reads +6.5 m from
    T9A on).
  - The pit-in facing 3591.5.
  - The T4 cushion 734.
- `inventory/source.json`: 7hJizPBNrJ4 recorded under `secondary_videos`.
- `manifest.md`: a round-14D table of every object and its evidence (before the dispositions).

## Pending (power)

- Stage 3 (`build_track.py --track sonoma --stage scenery --out tools/track/out/sonoma_r14d`) until every gate passes, then
  `--publish`.
- The gate CLI on the package, `npm run build`, `npx vitest run`, the Python tests, the kerb traversal numbers at T9A.
- The identity proofs: track.json, heightfield.bin and ghosts.json against f399cda140.
- The stills, B7 and C3, the rev in `src/scoreboard/config.ts`.
