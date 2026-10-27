# Mid-Ohio round 10: the far tree lines, the T4 tyre wall and the hot-lap start

Sonnet 5.5, 26 Oct 2026, branch `mid-ohio` (from 42020ed, package rev eeee12ff99). Three owner items of the round-9 drive: "the far
tree lines are missing" (the brief), "I don't think the carousel is a good place to start the hot lap" and "a tire wall at the far
end of China Beach ... the tell-tale black line on the ground" (both from the orchestrator). Road, line, AI and the round-8 near
trees unchanged: `track.json`, `heightfield.bin`, `ghosts.json` `cmp`-identical to the round-9 package (and so to round 5).

**Package rev ea1a07f8bd** (registry `mid_ohio.rev`).

## 1. Diagnosis: why the far trees are missing

Evidence: the 360 lap (Jul 2025) left / right at t36-t40 (T1-Keyhole straight), t64-t70 (back straight), t74-t82 (T4-T6), t102-t110
(Thunder Valley), t128 / t26-t32 (pit straight); the IndyCar t30-t40 and N837 frames. They show a continuous tree line on the horizon
300-600 m out to the right of the T1-Keyhole straight, woods behind the catch fence on the back straight left, tree walls both sides
through T4-T6 and Thunder Valley, a low broken line behind the pit straight; the back straight right (infield) is open with isolated
trees and one pine stand. `r10/far_diag.py` on the round-9 package (`r10/far_diag_pkg_r9.json`): per compass sector (45 deg about the
circuit centre), the ring 230-600 m and 600-1200 m from the centre line, outside the near (lidar) box.

| sector | OSM forest | NAIP dark | 2019 lidar canopy | far trees (r9) | crown cover (r9) |
|---|---|---|---|---|---|
| N | 0.00 | 0.18 | 0.68 | 88 | 0.06 |
| NE | 0.00 | 0.13 | 0.26 | 88 | 0.04 |
| E | 0.00 | 0.13 | 0.58 | 72 | 0.04 |
| SE | 0.00 | 0.14 | 0.41 | 20 | 0.04 |
| S | 0.00 | 0.14 | 0.35 | 98 | 0.06 |
| SW | 0.00 | 0.08 | 0.26 | 85 | 0.04 |
| W | 0.00 | 0.14 | 0.50 | 99 | 0.07 |
| NW | 0.00 | 0.12 | 0.59 | 49 | 0.07 |

(230-600 m band; the lidar column is the canopy share (CHM over 2 m, multi-return) of the same band, measured on the thinned
cloud of section 2.) Causes, in order:

1. **Lidar extent.** The cached cloud covers x -590..560, y -790..850 m: only about 225 m beyond the track on every side. Beyond it
   nothing but the far layer exists; the frames' horizon lines stand 300-600 m out.
2. **The far layer cannot see a stand.** `far_trees` takes local dark blobs of the 5 m NAIP (luminance 18 under a 125 m local mean):
   the same failure round 8 found for the near trees; in a continuous wood the local mean is the wood, so only edges and gaps
   register. Crown cover in the 230-600 m ring is 4-7 % against 26-68 % lidar canopy. The 7000 cap is not the cause (7049
   candidates, 49 cut).
3. **OpenStreetMap has no woodland there.** 24 `landuse=forest` objects (fetched read-only, `r10/osm_wood.json`, ODbL, already in
   `track.json` sources): none within 600 m of the circuit in any sector; 0.07-0.23 forest share only in N, NE, E beyond 600 m.
   (No `natural=wood` or `wood=*` exists in the area.)

## 2. The fix (opt-in `scenery.far_canopy`, `build_scenery.far_canopy`; Mid-Ohio config only)

- **Lidar ring** (box -1100..1100 x -1250..1350): the same 2019 EPT dataset, octree nodes down to depth 10 (592 nodes, thinned
  cloud), 2 m cells (ground = lowest class 2, canopy = highest class 1, multi-return share), the round-8 crown method (peaks,
  nearest-owner area, `tree_min` radius 2 m / height 5 m, window 14 m: the far layer's density), outside the near box. 3885 crowns;
  the NAIP blobs inside the ring are dropped (the lidar says where the canopy is).
- **Beyond the ring**: the OSM polygons filled with crowns at the cover and the crown size the lidar measures inside the polygons
  that lie within the ring (183 crowns in 8.6 ha: cover 0.67, rms radius 10 m, heights from those crowns), a jittered grid at
  21.6 m, 4434 crowns in 2.07 km2. The frames fix only the kind of line (continuous), not its density.
- **Kept**: the NAIP blobs outside the ring and outside the polygons (4769), so the far layer there is as it was. The far ortho's
  classification is used only for those existing blobs; it adds no tree (it agrees with neither OSM nor lidar there).
- Heights are the lidar's where it exists, else those measured crowns'. Nothing within the near box; the app's existing clearance of
  the course, pit lane and paved zones stays; nothing within 225 m of the track at all.

## 3. Before / after counts (230-600 m ring; the 600-1200 m ring in `far_diag_mid_ohio_r10.json`)

| sector | lidar canopy | far trees before | cover before | far trees after | cover after |
|---|---|---|---|---|---|
| N | 0.68 | 88 | 0.06 | 331 | 0.47 |
| NE | 0.26 | 88 | 0.04 | 193 | 0.18 |
| E | 0.58 | 72 | 0.04 | 306 | 0.40 |
| SE | 0.41 | 20 | 0.04 | 73 | 0.32 |
| S | 0.35 | 98 | 0.06 | 226 | 0.27 |
| SW | 0.26 | 85 | 0.04 | 181 | 0.18 |
| W | 0.50 | 99 | 0.07 | 293 | 0.39 |
| NW | 0.59 | 49 | 0.07 | 125 | 0.42 |

Whole far layer 7000 -> 13088 (4769 NAIP kept, 3885 lidar, 4434 OSM). Cover is the sum of crown discs over the band (overlap
ignored), so it runs about 70 % of the lidar canopy where the cloud is thinned to 14 m spacing. 600-1200 m: N 0.06 -> 0.21, NE
0.05 -> 0.27, E 0.05 -> 0.15, NW 0.06 -> 0.28, W 0.04 -> 0.19.

## 4. The T4 tyre wall (China Beach)

Frames: 360 t76-t80 left and t76 ahead show a dark low continuous wall under the catch fence along the far edge of the sand; N837
t66-t68 too. Tyres are not resolved in them. The 2022 NAIP ortho shows it clearly: a black line with white-topped tyres along the far
(north-east) edge of the sand from its west corner to the head of the T4-exit armco (OSM 1315208939), 64-88 m beyond the edge (the
c20 captures do not reach it). It was not in the package and no ground-line disposition named it (the gate looks 2-60 m out;
findings 44 / 45 at s 1951-1966 are the sand's own edge). Declared as `kind='tyres'`, h 1.0 m (declaration: a little under the 1.2 m
armco in the frames), default colour rule (black with a white pair every 12 stacks; the ortho's white is more frequent, left as it
is), 93 m, traced by `r10/trace_t4_tyres.py` (the sand's edge going out plus half the wall), its last point 0.75 m off the armco's
end so the faces meet flush (wall-tyre join gate). Coverage needed an inventory row: `tyre_wall left s 2010` added to
`inventory.json` from the 360 t78 left frame (marked as a round-10 hand addition). Gates with it: tyre facings, wall-tyre joins,
containment, barrier gaps, coverage all ok (first attempt failed the facings and the joins; fixed as above).

## 5. The hot-lap start

`mid_ohio.start` = `{ s_m: 3500, speed: ROLLING_START_SPEED }` (was 230 m before T13, s 3224, in the Carousel), registry comment quotes
the owner. The racing line at the T13 exit (`ghosts.json`, min-curvature): radius 66 m at s 3450, 144 at 3480, 218 at 3500, 361 at
3530, 597 at 3550, 1668 at 3570, so the line straightens (radius over 500 m) at about s 3545; 3500 is the brief's expected spot
(the launch is the autopilot on the line, 3 s, LAUNCH_S, so the car is on the straight when the driver gets it). Measured on the
HotlapSim (`launchUntil` 3 s of full throttle): start speed 22.0 m/s, hand-over at s 3572.7 at 27.1 m/s, 24 m before the line at
s 3597.5; the car crosses the line at ~27 m/s under the driver's control (the old start handed over at s 3299). Note for the owner:
at the hand-over the racing line runs at -5.0 m on a 6.1 m half width, and two wheels read off the track there from s ~3553 (starts
3480-3520); a start at 3460 hands over at 3534 with all four on, still in the exit (radius ~400). Left at 3500 as briefed.

## 6. Gates, proofs, tests

`build_track.py --track mid_ohio --stage scenery --publish --overwrite-package` (stage 3 only, out dir `out/mid_ohio_r10` from the
round-8 out): exit 0, 21 lines `[ok]` (ground lines strict, 0 open; coverage 252 rows, 0 MISSING, 0 UNSUPPORTED). On the package:
`run_gates.ts` (config `/tmp/mo7/g9.json`) rc 0, `run_coverage.ts` (inventory.json, `/tmp/mo7/c9.json`) rc 0, `edge_gate.py` rc 0.
`track.json`, `heightfield.bin`, `ghosts.json` `cmp`-identical to the round-9 package; only `scenery.json` changed (far ortho and far
heightfield identical).

Identity (the builder change is opt-in: absent `far_canopy` returns the far trees unchanged): Sonoma stage 3 from its published
files (`--write-on-fail`, out dir copy of `sonoma_r7chk`): `scenery.json`, `far_heightfield.bin` identical to `public/tracks/sonoma`;
Laguna stage 3 on its reproduction (copy of `laguna_r8chk`): all four outputs identical to the reference outputs (rc 1 as for the
reproduction); `git diff` on `public/tracks/{sonoma,laguna_seca,buttonwillow}` empty; `soup_hash.ts sonoma laguna_seca
buttonwillow`: f71411f3c2e78626 / e3b0c44298fc1c14 / 3da76e09e950dd5a, unchanged. Finding: at HEAD (42020ed) the Sonoma build
crashed in `build_structures.apply` (Sonoma's fuel island declares `hip=1.2`, a number, and the round-8 opt-in `hip` code called
`.get` on it); fixed (`isinstance(hip, dict)`), which is what makes the Sonoma proof possible. Buttonwillow's `--stage all` check was
not re-run (not in the brief; its package diff and soup are unchanged and it does not read `far_canopy`).

Tests: full `npx vitest run` 64 files, 538 tests passed (no timeout); `npm run build` ok.

## 7. Sheets

`compare_sheets_r10/` (local, index with the rev and the times): owner spot, back straight both sides, Thunder Valley, pit straight,
China Beach braking zone, each sim still beside the 360 / IndyCar / N837 frame, two-line judgements. Crowns read tall and narrow
beside the frames' round oaks (the far card geometry with lidar heights); the lines are there.

## Open

Crown shape of the far cards; the OSM fill cover is the lidar's inside-polygon measurement, not a pixel measure of the frames; the
tyre wall's white pattern and height are declarations; the start's off-track wheels at the hand-over (section 5).
