# Sonoma round 14D: the owner's decisions of 25 Oct 2026 and the round-14B judge's non-gate rows

Branch `sonoma-r14d`, from `integration` 893c961. Scenery only. Nothing pushed or deployed.

**Package rev e1c10d4ef5** (was f399cda140), lap 4105.328 m. `src/scoreboard/config.ts` TRACKS.sonoma `rev` is updated.

The work was built on battery (82-86 %) on the owner's instruction of 25 Oct: "Don't wait on power, just go." The rest of the
health rule held: one heavy process at a time, 1-minute load 1.2-3.1, no other vitest running, 11 GB free.

Frames are in `round14d/frames/` and stills in `round14d/stills/`, both local and reference only, never committed. The frames
were captured in the agent's own Chrome tab from the watch page, muted and paused, each drawn from the video element onto a
canvas. Measurements: `round14d/measurements.json` and `round14d/t11_profiles.json` (committed evidence).

## 1. T11 hairpin outside: a deep tyre wall and a thick white wall, no apron (owner)

The owner (OWNER_NOTES.md): "there is a deep tire wall at T11 ... from just before station 3648 (so it can encapsulate the
white wall section), all the way around the outside of T11. There is no apron. I think the white is just a thick wall (maybe
a SAFER barrier)". The 6 ft in his frame is the tyre wall's END.

### Measured

**The band (2026 captures).**
- Source: `compare/profile_measure.py` (new) on c20_s1265 / c20_s1320 / c20_s1375, every 4 stations outward from the left
  edge; output `t11_profiles.json`.
- One light run starts at s 3648 (k 3650) and ends at s ~3730.
- It runs from 0.1-0.6 m to 3.6-3.8 m beyond the edge at s 3650-3700.
- It narrows to 2.2-2.9 m at s 3704-3728, where the exit wall comes in.

**The white wall's width.** At s 3734-3744 the white exit wall ('T11 exit to T12, left') leaves the band. There it reads
0.96 m wide (k 3736 / 3740 / 3744).

**The onboard.**
- 7hJizPBNrJ4 (a Porsche GT3 RS lap uploaded 16 Aug 2019, before the 2023-24 repave). T11 of lap 3 is at video t 5-9.5, and
  the owner's frame is t 7.5. A black tyre wall runs round the whole outside from where the white wall at the entry ends
  (t 6.5-9.5).
- RAZip6S84CM (March 2026) shows a light-blue face round the outside from the entry, with the catch fence posts set back behind
  it (t121.5 / t122.5 / t123.25). It shows white stacks from s ~3698 to the exit (t123.25 / t124).
- Source precedence: **the 2026 onboard sets the colours; the owner's decision sets the structure.**

**Heights.**
- Stacks: two tyres, 0.8 m (t122 / t124).
- White wall: 0.81 m, as the exit wall it joins.
- Fence top: 3.0 m.
- Fence posts: curved-top (inventory s 3638 / 3670).

### Declared

| run | form | line beyond the left edge | s |
|---|---|---|---|
| 'T11 hairpin outside: deep tyre wall (round 14D)' | 4 tyre rows, 0.8 m; light blue (#d3dbe0), white section from 69.9 m along (s ~3698) | front row 0.55 m, face 0.24 m (on his red); back face 2.66 m | 3645 (joined to the Jersey's tail) - 3704 |
| 'T11 hairpin outside: thick white wall behind the tyre wall (round 14D)' | concrete, w 0.96 m, h 0.81, fence 2.2 with curved-top arms | line 3.30 m, back face 3.78 m (the band's outer edge); straight in to the exit wall's head at s 3712 (joined) | 3646-3712 |
| 'T11 hairpin, left tyre wall' (round 7) | its last four points, the 2-row white facing along the exit wall | snapped by tyre_facings as before | 3710-3730 |

- **Tyre line to wall line: 2.68-2.72 m.** tyre_facings snaps any tyre point within 2.6 m of a rigid line onto it, and the
  side-by-side gate fails a parallel tyre run 0.8-2.5 m off a wall. This spacing clears both.
- **The owner's step.** Neither line takes a point inside his 1.1 m step at s 3647-3651.
- **The pit-lane walls entry** for the T11 outside wall (pit row s 3680) now names the white wall.
- **The pit lane's paving moved.** Its right edge (`pit_lane.lane.to_walls`) now reaches this wall's back face at lane rows
  140-227, up to 0.85 m nearer the course than before. Pit connectivity and lane clearance pass.
- **Not done.** From s ~3704 to 3712 the band is too narrow for four rows, so up to ~1 m of ground remains between the edge and
  the 2-row facing there.

Stills: t11_outside_entry, t11_outside_mid, t11_outside_high (the four rows and the white wall behind), t11_exit_lookback,
hairpin_3640 / 3680 / 3720.

Tool support (identical without the new keys):
- **`rows` on a tyre run.** The app draws row k at k x 0.6 m to the polyline's left. The builder passes `rows` and `w`
  through. The gates `tyreFaces` and `joinFaces` measure the drawn row extent, and `joinFaces` the wall's own half width (w / 2).
- **`w` on a concrete run:** the wall's drawn thickness.
- **Tyre colour `pattern` / `sections`** (the app).
- **The physics is untouched.** It collides with rows 0 and 1, so row 0 is the contact face and the rows behind it cannot be
  reached.

## 2. T9A right-hander: kerb 24 (owner; corrects the round-14B judge agent's FALSE)

Measured on RAZip6S84CM at 0.25-0.5 s, 99.0-101.5 s:
- At t100.0 the right front is on the kerb's last blocks. The kerb ends abeam the two grey tyres (landmark s 3047).
- At t100.25 only the white line on the grass remains.
- The car is on the kerb at the onboard's s ~3050, as the owner says. The station map reads several metres early there.
- **The kerb ends at s 3046, not 3044.** Nothing in the 2026 frames shows a kerb beyond the grey tyres.
- s 3046.0 is the round-14B `kerb_inside` world point (219.96, 28.24). The fitted edge already carries the kerb's 0.65 m to
  there, so **no geometry change** was needed. The strip went 3044 -> 3046 as a physics kerb with the track's profile.
- The captures cannot place the end: trucks are parked over the apex on c20_o0660 / c20_s0660.

**Kerb traversal gate (Probe at line speed; all passes, the gate test in the full vitest run):**

| pass | max roll | plain road | on the strip | wheel lift by the strip |
|---|---|---|---|---|
| kerb 24 R s3019-3046, line -1 / 0 / +1 m | 3.65 / 4.76 / 4.60 deg | the same | 0 ms (the line clears the apex kerb) | 0 |
| kerb 24, crossing at 5 deg | 3.62 deg | 2.93 | 954 ms | 11 ms |
| kerb 24, crossing at 10 deg | 5.61 deg | 5.50 | 493 ms | 344 ms |
| kerb 25 L s3062-3174, line -1 / 0 / +1 m | 14.02 / 8.27 / 6.41 deg | 14.00 / 7.95 / 6.41 | 169-189 ms | 181-191 ms (advisory) |

No pass rolls past 15 deg or rolls over. Kerb 25's 14.0 deg at line -1 m is the plain road's own roll there, not the kerb's.

Stills: t9a_kerb24_apex, t9a_kerb24_end_high.

## 3. T1 service-road mouth: no cones, a white line (owner)

"Delete the cones entirely. There should be a white painted line that follows the outside arc of the track at the service
road mouth."
- `owner_mouths_r14` has cones=False, so no cone line is drawn.
- His arc (owner/r14/mouths.json) lies on the fitted right edge (-0.27 .. +0.25 m).
- **The kerb hides a line on the arc.** Red / white kerb run 3 (s 161-179, c20_s1870) covers 0-0.63 m beyond the edge there,
  and its raised back falls 0.6 m further (profile back 0.6).
- The first two builds drew the line on the arc and then at 0.72 m. Both were hidden (stills t1_mouth_arc_high).
- The 0.12 m white line now follows his arc at 1.30 m beyond the edge, at the foot of the kerb's back.
- Over open ground the drawn 3 m terrain mesh rose over the line. The app now draws a paint line 0.008 m over the drawn terrain
  where that lies higher (`paintLineZ`, with a test). On ribbons and zones the line is unchanged, because the drawn terrain
  is sunk below them.
- The inventory has no row citing cones at this mouth, so nothing was corrected.

Stills: t1_mouth_arc, t1_mouth_arc_high (cones gone), t1_mouth_line_close_after (the line beyond the kerb).

## 4. The T4 wall head at left s 736 (owner, decisions page Q3: "cushion")

- A 2.0 m black tyre cushion stands on the wall's line extended upstream from 0.5 m before the head. 2.0 m is the size of the
  lap's other cushion, the drag-strip bundle.
- tyre_facings stands it 0.55 m to the track side of the line. Published points: (-331.90, -25.57), (-333.92, -25.52).
- `gates.known_exposures` is now empty.
- The wall-ends gate: "s 736 joined to tyres run 24". Wall-tyre joins: s 736 wall -0.68 (not proud).

Stills: t4_cushion_720, end_735_T4_left.

## 5. The round-14B judge's non-gate rows

| row | checked against | change | still |
|---|---|---|---|
| A10 / A11 T7 road left: edge line and pale shoulder | t066 / t068 / t070 / t072: dark asphalt to the wall's foot, no paint; t064: the drag strip's SW line runs to the fork | `edge_line_cut` and `track_shoulder_cut` left s 1909-2150 (the fork vertex to the T7 approach wall's end) | t7_left_2060, t7_approach_wall_left: the line is gone |
| B7 / B8 T9A mouth | render t9a_mouth_line_high / t9a_mouth_close; c20_s0660 / c20_o0660 / c20_o0715 | **The course line along the arc is drawn and clear.** What read badly was the ground between the arc and the escape road: dirt, grass and a seam. The captures show dark asphalt there. It is repainted as paving (ortho_pave, 219 m2, texture only; its physics surface is still ground). Two items stay as before: the escape road's own blotch (zone texture) at its start, and the V where its lines meet the course line, which no capture resolves. | t9a_mouth_close |
| C1 pit-in separation | s3600 crop, t119.5 (red / white panels over tyre tops), t119.5-t121 (the Jersey light blue to the hairpin) | A 2-row tyre facing on the Jersey's line, 0.55 m to the track side, s 3592-3604, red / white in turn every 1.25 m. The Jersey is light blue (it was red). From s 3606 the Jersey stands 0.55 m from the edge, which leaves no room for a facing on the course side. Inventory row added. | pitin_facing_3590 |
| C3 T11 exit infield seam | stills hairpin_3760 / 3800, t11_infield_3780; RAZip6S84CM t126 / t128 (one grey asphalt beyond the white line); c20_s1210 / s1375 / s1430 (paved infield and lot) | Right s 3738-3812, 0.1-20 m out, repainted in the paving tone (texture only). ground_gain (0.65, 0.62, 0.63) is calibrated on t11_infield_3780 to ~1.15 x the road. The near seam is gone. The lot further on (s > 3812) still reads paler (left as before). | t11_infield_3780, hairpin_3760 / 3800 |
| A5 pit-out panels | t004.0 / t004.5: red panels with white logos on the paddock-side wall across the pit-out lane | Plain red panels (no logo art), 2 m long, 0.55 m tall, 0.4 m up, s 111-150: 17 panels | **Not seen** in the stills: the near pit wall hides them from the hood poses tried (pitout_panels_120 / 130) |
| A3 T2 footbridge | s0250 / t008: open truss, lattice ends at both piers, no roof | `bridge_style` 'truss' (app): no roof, a top chord each side, lattice ends over 4.5 m at each pier | footbridge_260, footbridge_close: the roof is gone |
| A15 T7 Toyota boards | s2100 / t070 | The panels alternate: red with white TOYOTA, then white with dark TOYOTA | t7_approach_wall_left |
| B12 T10-entry boards | t103.5 / t104.5 / t105.5 | One 14 m SONOMA RACEWAY panel, two green SUNBELT RENTALS panels, then small white TOYOTA panels | t10_boards_3110 |
| B14 fence posts | the inventory's "curved-top posts" rows | `fence_arm` (0.5 m at 45 deg, as measured at the pit-out) on the ten fenced walls those rows lie on, and on the T11 white wall | fence_arms_3300 |

## Gate table (stage 3, publish run; gate CLI on `public/tracks/sonoma`, every gate ok, exit 0)

| gate | result |
|---|---|
| edge gate L / R | ok, rms 0.040 / 0.046 m |
| world continuity L / R | ok, 0.0164 / 0.0184 m (4 declared junction corners exempt, as before) |
| profile | ok, 0.028 m |
| owner reference L / R, width, band L / R | ok, 0.350 / 0.379 m, 0.392 m, 0.160 / 0.122 m |
| barrier gaps | ok, min 0.34 m over 77 runs |
| containment | ok, 0 escapes (1282 onto allowed runoff) |
| pit connectivity, sign placement | ok (151 signs) |
| wall ends | ok, 43 checked, 43 joined / cushioned / lapped / tapered, **0 exposed (T4 s 736: joined to the cushion), 0 known exposures**, 0 degenerate |
| tyre facings / tyre faces | ok, 0 / 0 |
| wall tops | ok, 42 runs, 118 boards |
| wall-tyre joins | ok, 8 joins, none proud (s 3645 tyres +0.13, s 736 wall -0.68, the rest as before) |
| run gaps | ok, 8 openings, 0 holes |
| pavement joins / smoothness / kerbs on surface | ok, 0.0056 m 1.63 deg / 0.0099 m / 0.71 deg |
| ground marks on surface | ok, 2447 paint-line, 11868 edge-line, 680 ground-sign vertices at 0.008 m |
| cones off the surface | ok, 54 cones on 9 lines (the T1 mouth line gone), deepest 0.08 m |
| coverage | ok, 285 rows, 216 objects, MISSING 0, UNSUPPORTED 0 |
| pit lane, ground lines | ok |

Build history:
- **Run 1** failed run gaps: a 1.2 m hole between the Jersey's tail and the tyre wall.
- **Run 2** failed wall ends and run gaps: two tyre runs end to end left a 2.9 m hole after resampling. Fixed by making one run
  with a white section.
- **Run 3** passed. It was published, and the stills from it gave B7 / C3 and the T1 line.
- **Run 4** passed (the repaint regions) and was published.
- **The publish run** passed with the T1 line at 1.30 m and the calibrated T11 tone, and gave rev e1c10d4ef5.

No --write-on-fail package was ever published.

## Identity proofs

- `git status` on `public/tracks/sonoma` shows only scenery.json and ortho.jpg modified.
- sha256 (first 16) identical to rev f399cda140:
  - track.json 2c043135a7b27767
  - heightfield.bin 97d4a67a9c4d2341
  - ghosts.json 633900fd843035b9
  - far_heightfield.bin 06c30baa16dc5183
  - far_ortho.jpg 211982db8a8b9c13
- out and public are cmp-identical after the publish.
- **ortho.jpg** differs by more than 8 grey levels in 15274 px. That is the three repaint regions and the barrier bands under
  the new and changed runs; the rest is JPEG re-encode ripple.
- **scenery.json against f399cda140:**
  - barriers 73 -> 77: the deep tyre wall, the white wall, the pit-in facing, the T4 cushion; run 20 trimmed; the Jersey
    recoloured; fence arms on 11 walls.
  - one bridge restyled.
  - cone lines 9 -> 8: the T1 mouth.
  - edge lines: the T7 cut.
  - kerbs: kerb 24 s1.
  - landmarks 154 -> 175: wall boards.
  - paint lines +1: the T1 mouth.
  - track_shoulder_cut +1.
  - pit_lane right edge at the T11 outside (above).

## Tests

- `npm run build`: clean (tsc and vite).
- `npx vitest run`: 63 files, **523 passed**, 0 failed. Six of these tests are new: gates rows / w (2), app rows, wall width,
  truss and paintLineZ (4). The first full run failed only the registry rev test, before `config.ts` took the new rev; after
  it the run is clean.
- The kerb traversal gate (part of the run) passes on every track; the T9A numbers are above.
- Python (`pytest tools/track -q`): **94 passed**, 0 skipped. The brief's 91 passed + 3 skipped: the 3 data tests run now that
  the worktree has the caches.

## Inventory and manifest

- `inventory.json`: five rows (attrs.round '14D'), stations on the inventory's own lap:
  - T11 tyre wall 3643.5 and 3693.5;
  - T11 white wall 3643.5;
  - pit-in facing 3591.5;
  - T4 cushion 734.
- `inventory/source.json`: 7hJizPBNrJ4 under `secondary_videos`.
- `manifest.md`: a round-14D table of every object and its evidence.

## Stills (`round14d/stills/`, `<pose>_before.jpg` = rev f399cda140, `<pose>_after.jpg` = rev e1c10d4ef5)

- **Earlier rounds' poses:** round 14B's 20 + 3, and round 14C's 7.
- **New poses:**
  - T11: t11_outside_entry / mid / high, t11_exit_lookback, t11_infield_3780.
  - T9A: t9a_kerb24_apex, t9a_kerb24_end_high, t9a_mouth_line_high, t9a_mouth_close.
  - Pit lane: pitin_facing_3590, pitout_panels_120 / 130.
  - T2 footbridge: footbridge_260, footbridge_close.
  - The rest: t4_cushion_720, t10_boards_3110, t7_left_2060, fence_arms_3300, t1_mouth_line_close (after only).
- Poses: `/tmp/r14d/poses.json` (local).

## For the owner

1. **The T11 tyre wall's colour.** His 2019 video shows it black. The March 2026 onboard shows a light-blue face from the
   entry and white stacks from s ~3698, and that is what is drawn. He may prefer black.
2. **The T11 wall depth.** Four rows (2.4 m) plus the 0.96 m white wall fill the 3.4-3.8 m band at s 3650-3700. From s 3704
   the band narrows and the old 2-row facing stays: up to ~1 m of ground at s 3704-3712.
3. **The T1 mouth line** stands just outside kerb run 3 (1.30 m from the edge), because a line on his arc lies under the kerb.
4. **The T9A mouth strip** between the arc and the escape road looks like asphalt now but drives as ground. Extending the
   escape road's paved zone to the arc would change the drivable surface; not done.
5. **Kerb 24 ends at s 3046.** The 2026 onboard shows no kerb past the grey tyres.
