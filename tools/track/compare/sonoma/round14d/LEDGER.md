# Sonoma round 14D: the owner's decisions of 25 Oct 2026 and the round-14B judge's non-gate rows

Branch `sonoma-r14d`, from `integration` 893c961. Scenery only. Nothing pushed or deployed.

**Package rev 3cf8227da0** (was f399cda140; e1c10d4ef5, 59abee785b and 97b83d1378 were this round's earlier publishes,
held by the three reviews: see the last three sections), lap 4105.328 m. `src/scoreboard/config.ts` TRACKS.sonoma `rev` is updated.

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
- **The pit lane's paving moved.** (Corrected in the review, item 4.) The lane is CLIPPED at walls
  (`scenery.pit_lane_clip_walls`; `to_walls` is not used at Sonoma). It now stops 0.3 m (along the clip ray) short of the
  thick wall's back face, at lane rows 140-229. See the last section.
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
- (Review item 1: the render-time lift `paintLineZ` of the first publish is removed. The line shows without it, so the drawn
  heights are the stored ones the ground-marks gate checks. See the last section.)
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


## Review of 25 Oct (GPT 6 Astra, via the coordinator): HOLD, one blocker and four fixes; fixed and re-published as rev 59abee785b

The finding, in one line: a drawn face or height that a gate, the collision or the pit lane does not use.

**1. BLOCKER, the paint lines' render-time lift: removed.**
- The app had lifted a paint strip's corners to max(stored z, drawn terrain + 0.008). The ground-marks gate checks the stored
  heights, so the gate did not certify what was drawn.
- That lift turned out not to be needed. The first publish's diagnosis framed the camera so it never looked 1.3 m beyond the
  kerb, so it did not show whether the line was buried.
- **Test without the lift.** The same pose (`/tmp/r14d/dbg/t1_line_down_nolift.jpg`) against the same pose with the paint
  lines hidden (`..._nopaint.jpg`) differs in 6054 px. Those pixels are the white line along the kerb's outer foot, visible at
  its stored height.
- So `paintLineZ` and its test are gone. The app draws paint lines at their stored heights again, which is what
  `groundMarksGate` measures (0 .. 0.01 m above the driven surface; every vertex at 0.008).
- No lift remains to certify against the drawn terrain, and no gate changed.

**2. FIX, the thick wall's collision: it is now its two faces.**
- `build_scenery.thick_wall_faces` turns a declared concrete wall with `w` into two concrete runs: the front face (w / 2 toward
  the track) and the back face (w / 2 beyond). The physics collides with both as it does with any wall; the physics code is
  unchanged.
- The front run carries `box` {w, side}: the app draws the 0.96 m box from it. The back run is `hidden`: it draws no body, and
  its fence (with the curved arms) is drawn.
- **Proof on the collision world** (`createCollisionWorld` on the package, `/tmp/r14d/coll.ts`,
  `/tmp/r14d/kt/collision_faces.json`): sampled points on both drawn faces lie 0.000 m from a collision segment. Contact begins
  at the 0.10 m skin, so a car stops 0.10 m short of the visible face on either side, the track's or the pit lane's.
- Gates:
  - `sideBySide` skips a `hidden` back face. The box is faced from its front face; without the skip, the back face 0.96 m
    further on read as a second wall beside the facing. Test: the same facing passes with the back face hidden and fails with
    it not hidden.
  - The gates' w / 2 reading of round 14D's first diff is gone, because no run carries `w` now. `joinFaces` is back to the
    kinds' half thickness.

**3. FIX, the new keys are validated in the builder.**
- `build_scenery.validate_declared_wall` fails the build when `rows` is not an integer 1-8 on a tyre run (0, 9, 20, 2.5, "4",
  True and rows on a wall are all rejected). It also fails when `w` is on anything but a concrete run (Armco, tyres, pit wall,
  fence) or is not > 0.
- Tests: `tools/track/test_r14d_walls.py`, 11 cases.
- The app's clamp stays, but it can no longer see a value outside 1-8.
- `rows` on a run also means its last row is the facing row:
  - **tyre_facings** places the last row `off` in front of the wall and keeps row 0 that far before it.
  - **sideBySide** samples the last row's line.
  - **Without `rows`**, both behave as before (tests).

**4. FIX, the pit lane at the thick wall.**
- The lane is clipped at the back face run, so the margin is now taken from the visible back face.
- One gap was left: the back face's head stood inside the lane, between a clipped edge row and the unclipped row before it.
  That failed pit connectivity, "inside the lane".
- New config-gated rule `scenery.pit_lane_clip_heads` (Sonoma only; absent: as before): a wall end inside the strip between two
  edge rows brings both rows in to the margin short of it. Test: the row before a wall head is clipped only with the rule.
- **Measured on the published lane** (`/tmp/r14d/scripts/lanechk.py`):
  - no back-face vertex lies inside the lane.
  - the lane's right edge is 0.275 m or more from the back face (perpendicular). The clip's 0.30 m is taken along each edge
    row's ray from the lane centre, so on the curve the perpendicular gap reads up to 0.025 m less.
- **Pit connectivity and the lane paths: ok** (0 obstacles).
- **Other lane rows the head rule moved:**
  - left s ~3567: rows 62-63, 0.37 m, at the pit-in separation's nose.
  - right s ~157: rows 794-795, 0.65 m, at the pit-out K-rail's end.
  - At both, a wall end stood inside the lane before, and the lane surface now stops 0.3 m short of it.
- **T11 lane rows:** 140-143 and 151-229 moved, by up to 2.31 m. The lane had reached into the band.
- **The wall's head moved to s 3652**, past the owner's step. At s 3646 its front face stood within 1 m of the pit-in lane's
  path behind the Jersey. The tyre wall's head and the Jersey's tail cover s 3645-3652.

**5. FIX (owner to rule), the T1 line: read on the 2026 captures.**
- Crops (local): `frames/t1_mouth_c20_s1870_crop.png` (c20_s1870 / s1925 / s1815 at 0.04 m/px) and `..._overlay.png`, and
  `frames/t1_mouth_c20_native.png` at 0.117 m/px.
- What they show:
  - Kerb run 3's red / white blocks continue round the outside arc across the service-road mouth.
  - The dirt meets the kerb's outer side directly; **no painted line is resolved outside the kerb**.
  - The course's white edge line runs to the kerb from the left and a light strip lies along the kerb's track side. At
    0.117 m/px it cannot be told from the kerb's white blocks.
- **So the line stays at the kerb's outer foot** (1.30 m beyond the edge, his arc pushed out past the kerb and its 0.6 m back).
- **For the owner:** the capture shows the kerb across the mouth and no line beyond it. He can rule whether the white line
  belongs there, along the kerb's track side, or nowhere (the kerb itself bounding the arc).
- Still `stills/t1_mouth_line_along_after.jpg` (from s 158 along the arc): the white line runs continuously along the kerb's
  outer side.

**6. FIX, s 3704-3712 (no ground between the edge and the stacks).**
- The band reads 2.92 / 2.84 m out at k 3704 / 3708 (t11_profiles.json), light from the edge. That is tyres and wall, not
  ground.
- **Deep tyre wall:** it now ends at s 3700.
- **Thick wall:** it comes in over s 3700-3702 to a 2.18 m centre line (front face 1.70 m, back face 2.66 m) and joins the exit
  wall's head at s 3712.
- **Exit facing:** the round-7 run is now a white 2-row facing (`rows` 2) from s 3700 to 3730. Its front row is 0.55 m beyond
  the edge (face 0.24 m) and its back row stands against the thick wall's front face.
- Stills `t11_outside_high`, `hairpin_3720`, `t11_exit_lookback`: the stacks run continuously from the hairpin to the exit.

**7. Test count reconciled.** I ran vitest on a copy of the branch base 893c961 (`git archive` into `/tmp/r14d/base2`,
node_modules linked). It gives 515 tests, 2 of which fail there only because the archive has no audio assets. Now: 522.
- **5 new tests:**
  - barrier-sections:
    - "tyre rows: absent 2 (the old two rows), else the given count, 1-8"
    - "thick wall box: drawn between the front face run and the back face w m to its side"
    - "truss end sections: verticals and diagonals over the first and last 4.5 m only, at both piers"
  - scenerygates:
    - "rows absent: the 2-row extent as before; rows 4 toward the track put the face 1.2 m nearer"
    - "side by side: a run with rows faces a wall with its last row; without rows, by its polyline as before"
- **2 generated tests:** `tyrewall.test.ts` makes one "a 12 m/s square hit stops outside the stacks" case per tyre run of each
  package, and Sonoma now has two more tyre runs (runs 23 and 24).

### Re-verification (rev 59abee785b)

- **Stage 3**, publish run: every gate ok (`/tmp/r14d/logs/publish4.log`).
  - barrier gaps 0.34 m over 78 runs.
  - wall ends: 44 checked, 0 exposed, 0 degenerate.
  - tyre facings 0; tyre faces 0.
  - wall-tyre joins: 8, none proud.
  - run gaps: 10 openings, 0 holes.
  - pit connectivity ok; lane paths 0 obstacles.
  - ground marks 0.008 .. 0.008 m.
  - coverage: MISSING 0, UNSUPPORTED 0, 217 objects.
  - pit lane, ground lines: ok.
- **Gate CLI** on `public/tracks/sonoma`: 14 ok, 0 FAIL, exit 0. Coverage CLI exit 0.
- **Build runs:**
  - Review run 1: pit connectivity and side by side.
  - Run 2: pit connectivity and side by side, after the start moved to s 3652.
  - Run 3: pit connectivity, start at s 3655.
  - Run 4: pit connectivity, start at s 3659.5.
  - Run 5: passed, with `pit_lane_clip_heads` and the start back at s 3652.
  - No --write-on-fail package was published.
- **Identity:** track.json, heightfield.bin, ghosts.json, far_heightfield.bin and far_ortho.jpg are unchanged (git status
  shows only scenery.json and ortho.jpg against e1c10d4ef5); out and public are cmp-identical.
- **Builds and tests:**
  - `npm run build` clean.
  - `npx vitest run`: 63 files, 522 passed, 0 failed.
  - Python: 105 passed (94 + 11 in test_r14d_walls.py).
- **Health:** the full vitest, the baseline vitest and the two reporter runs were started at 1-minute loads of 8.6 / 9.0 with
  the Buttonwillow round building beside them; the rule says under 8. Builds and stills ran at 4-5. The power source came
  back during the review fixes (84 %, charging).


## Second review (GPT 6 Astra, 25 Oct): items 1, 3, 6, 7 closed; 4, 5 open; A-F; fixed and re-published as rev 97b83d1378

**A. BLOCKER, four drawn rows against two collided rows: fixed in the builder (physics unchanged).**
- `build_scenery.stacked_tyre_runs` emits a declared tyre run with `rows` > 2 as rows / 2 runs of two rows back to back. Each
  run is drawn and collided as the physics already does a tyre run.
- Member k stands k x 1.2 m behind the declared line and carries `rows` 2 and `stack_of` {id, k, n}. (`stack` was already the
  key for tyres per stack; the first try reused it and the build caught the clash.)
- Colour sections are carried over by length.
- `rows` must be an even integer 2-8 in the config. An odd count fails the build, because the physics collides every run as two
  rows. Each emitted run has 2.
- tyre_facings leaves stack members as declared.
- The side-by-side gate checks only the rear member, against the wall behind it.
- Tests: "a four-row run is two collided two-row runs" (Python); the stacked-wall gate case (vitest), where the front member
  without its tag is a finding.

**Proof on the collision world** (`/tmp/r14d/coll2.ts`, `/tmp/r14d/kt/stack_collision.json`):
- At sampled stations along the deep wall, each drawn row has a collision face at its depth, within 0.004 m:
  - row 0's track face at -0.21 m;
  - row 1's back at +0.81 m;
  - row 2's front at +0.99 m;
  - row 3's back at +2.01 m.
- In each case contact begins 0.10 m inside the drawn face.
- The rear member's last row stands 0.38-0.61 m in front of the white wall's front face: a facing (within 0.8 m).
- sideBySide on the package: 0 findings.

**B. FIX, the side-by-side skip: replaced by an explicit pair.**
- The builder tags the two faces of a thick wall with one `wall_id` and `face` 'front' / 'back'.
- The gate evaluates the pair once. Its distance from a tyre sample is the nearer face (the face exposed on the sample's side;
  the box lies between them), and its joints are both faces' ends.
- Regression: a 2-row run whose rows stand 1.6 m behind the back face (2.56 m from the front face, outside the band) is a
  finding, tagged or untagged. Round 14D's first fix (skip every hidden face) missed it.

**C. FIX, joinFaces at a face run.** A run tagged `face` is the drawn face: no 0.18 m half thickness is added. Test: the same
join reads 0.31 m (was 0.31 - 0.18).

**D. FIX, the lane clearance is enforced.**
- With `pit_lane_clip_heads`, the 0.3 m margin holds as a segment-to-segment clearance on the stored (rounded) lane edges,
  crossings included (shapely distance = 0). Every edge segment nearer a wall, tyre or Armco run has both its rows brought in
  along their rays until it clears.
- `build_scenery.clearance_report`: the published lane's minimum clearance is **0.300 m**. Before, it was 0.003 m on
  rev 59abee785b and 0.275 m at T11.
- Tests: an oblique wall between rows; a wall bowing between rays.
- The lane rows this moved, against 59abee785b (the physics' pit-lane surface narrows by the same amounts):
  - mostly 0.03-0.05 m all along both lane edges;
  - 0.48-0.62 m at left s ~3537, s ~3657 and s ~169-179, and at right s ~97;
  - 1.43 m at right s ~3639 (the T11 head).
- Pit connectivity ok, 0 obstacles.

**E. FIX, sections on a thick wall.** Rejected in `validate_declared_wall` (`sections` or `pattern` together with `w`).
Tests: both rejections.

**F. NOTE, the thick wall's end caps.**
- The two face runs end 0.96 / 0.97 m apart (the published end points), and each end carries a 0.08 m collision post.
- That leaves a 0.80 / 0.81 m nominal opening, or 0.60 / 0.61 m with the 0.10 m contact skin on each side, against the car's
  1.72 m width.
- A car cannot enter between the faces from either end. The drawn box closes both ends with its caps.

**G.** The T1 line stays at the kerb's outer foot, pending the owner's ruling.

### Re-verification (rev 97b83d1378)

- **Stage 3**, publish run: every gate ok.
  - barrier gaps 0.34 m over 79 runs.
  - wall ends: 45 checked, 0 exposed.
  - tyre facings 0; tyre faces 0.
  - wall-tyre joins: 9, none proud. The new one, s 3645, rear stack member -1.07 m.
  - run gaps: 0 holes.
  - pit connectivity ok.
  - ground marks 0.008 m.
  - coverage: MISSING 0, UNSUPPORTED 0, 218 objects.
- **Gate CLI**: 14 ok, 0 FAIL, exit 0. Coverage CLI exit 0.
- **Identity:** track.json, heightfield.bin, ghosts.json and the far files are unchanged; out and public are cmp-identical.
- **Builds and tests:**
  - `npm run build` clean.
  - `npx vitest run`: 525 passed, 0 failed. Against the base's 515:
    - 7 named new: 3 barrier-sections, 4 scenerygates (rows extent, side by side with rows and the face pair, the stacked
      wall, the join at a face run).
    - 3 generated tyrewall.test.ts cases: Sonoma runs 23-25, one more than before, the stack's second member.
  - Python: 108 passed (test_r14d_walls.py: 14).
- **Stills** (after): t11_outside_high / mid / entry, hairpin_3680 / 3720, t11_exit_lookback, pitin_facing_3590. The four rows
  are drawn as two members, unchanged to the eye.
- **Health:** this pass ran on power (93 % charging), loads 2.8-5.7.


## Third review (GPT 6 Astra, 25 Oct): HOLD, three HIGH findings (gates loosened by the stacked representation); fixed, rev 3cf8227da0

Each finding came with a reproducer Astra ran.

**1. Wall ends and run gaps: a group is ONE wall** (`sceneryGates.groupOf`).
- A group is either the members of a stacked tyre wall (`stack_of`) or the two faces of a thick wall (`wall_id`).
- No member of a group joins, cushions, laps or protects another member of it, in `exposedEnds` and in `runGaps` (gap pairs
  and the lapping-run test). Each member's head, the group's end envelope, needs protection from outside the group.
- Regressions (vitest):
  - a bare straight two-member stack reports both heads exposed (untagged, the members cover each other);
  - a bare box (two faces 0.96 m apart) reports both heads;
  - a stack head joined by a wall that is not the stack is still joined.
- Published T11:
  - **both stack members' heads (s 3645) are "joined to concrete run 47"**, the pit-in separation Jersey. Before, they
    certified each other.
  - the thick wall's front face head (s 3652) is joined to the stack's rear member (run 21).
  - its back face head is "lapped by tyres run 20" (0.5 m out vs 3.8 m). Before, it was joined to its own front face.
  - Wall ends: 45 checked, 0 exposed.

**2. Side by side, and the facing placement of a stack.**
- The gate no longer drops any member globally. A tyre run on its own, or a stack's members together, is one unit whose
  candidate lines are each run's row 0 and, for a run with `rows`, its last row.
- Against each wall the unit is evaluated on the candidate line nearest that wall: the row exposed toward it.
- Regression: a wall 1.5 m IN FRONT of a stack is a finding, tagged or untagged. The rear-member, behind-the-stack and
  face-pair cases still behave as in the second review.
- `tyre_facings` places a stack as one wall. The rear member is placed by its last row against the wall behind. The members in
  front follow it point by point at the row spacing. The barrier-gap minimum is held on the front member's row 0.
- Test: a stack within reach of a wall has its rear last row 0.55 m in front of the wall, with the front member 1.2 m before
  it.

**Placements changed under the group facing rule: none.**
- At T11 the rear member's last row stands 0.38-0.61 m in front of the white wall's front face.
- Placing it at 0.55 m would bring the front member's row 0 within 0.55 m of the edge, so every point keeps its declared place.
- Every other tyre run is placed as before. Against rev 97b83d1378, all 79 barrier runs are point for point identical.

**3. The lane clearance is a postcondition, corrected along the perpendicular, against every barrier.**
- **The correction.** It moves an edge segment's two rows along the perpendicular from the nearest run point by the deficit
  (+0.011 m). That direction is flipped toward the lane's centre line where the edge lies beyond the run, or where it crosses
  one. It runs to 50 passes.
- **Every barrier.** The src filter is gone, so the declared cone lines passed as runs count too.
- **Postconditions.** `clip_parts_at_walls` fails the build on any residual segment under the margin. The stage checks
  `clearance_report` again after the clip and fails below 0.3 m.
- Regressions (Python):
  - Astra's case (centres (0,0),(0,1); left edges (10,0),(10,1); wall (-10,-0.51)-(20,0.09)) ends at 0.31 m. The ray-wise loop
    stopped at 0.147 m.
  - an unlabelled run is cleared.
  - an edge just beyond a wall is brought back inside it, never pushed out.
- **Published:** "pit lane: edge clearance to every barrier run 0.300 m (>= 0.3, a postcondition)".
- **Lane rows moved against 97b83d1378:** 68 left and 94 right by more than 1 cm. Most are 1-2 cm.
  - 0.53 m at right s ~3573.
  - 0.24-0.29 m at s ~3543 left, s ~3641 right, s ~3657 left and s ~170 left. At s ~3657 the left edge moved 0.28 m outward,
    round the outer wall (east)'s end, to its 0.3 m clearance.
  - 0.24 m at s ~98 right.
- **Lane width at T11** (rows 150-229): 5.34-7.62 m (5.34-7.57 before).

**Unchanged on Astra's word:** the 0.02 m nominal overlap between members (the row spacing), the +0.13 m join at s 3645, the T1
line (the owner is asked).

### Re-verification (rev 3cf8227da0)

- **Stage 3** publish run: every gate ok.
  - wall ends 45 / 0 exposed.
  - tyre facings 0.
  - wall-tyre joins: 9, none proud.
  - run gaps: 10 openings, 0 holes.
  - pit connectivity ok.
  - lane clearance postcondition 0.300 m.
  - coverage: MISSING 0, UNSUPPORTED 0.
- **Gate CLI**: 14 ok, 0 FAIL. Coverage CLI exit 0.
- **Identity:** track.json, heightfield.bin, ghosts.json and the far files are unchanged; out and public are cmp-identical.
- **Collision world:** every drawn row of the stack still has a face at its depth (within 0.004 m). The thick wall's faces sit
  0.000 m from collision segments.
- **Builds and tests:**
  - `npm run build` clean.
  - `npx vitest run`: 527 passed, 0 failed. That is the base's 515, plus 9 named new tests (3 barrier-sections, 6 scenerygates),
    plus 3 generated tyre-wall cases (Sonoma runs 23-25).
  - Python: 112 passed (test_r14d_walls.py: 18).
- **Health:** on power, loads 3.3-5.8.
