# Track pipeline (Laguna Seca is the worked example)

One driver builds a circuit package in the format of `CONTRACTS.md` sections 1, 2 and 2b from a per-track config:

```sh
W='numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib,laspy[lazrs]'
uv run --python 3.12 --with "$W" python -I tools/track/build_track.py --track <id> [--stage geometry|ghosts|scenery|all] \
    [--no-logger] [--out tools/track/out/<id>] [--publish]
```

* **Config:** `tools/track/tracks/<id>/config.py` (one dict, `CONFIG`; data only). The keys and their defaults are documented
  in `trackcfg.py`; `tracks/laguna_seca/config.py` holds every constant the 17-18 Oct 2026 Laguna scripts had, each with
  where it came from.
* **Stages**, each printing a validation report and exiting 1 without writing its outputs when a check fails
  (`--write-on-fail` writes them anyway for diagnosis, still exits 1, and is never publishable):
  1. `geometry`: OSM loop (`geo.py`) -> first centre (`centre.py`: the logger's driven line moved toward the NAIP
     midpoint; without logger laps the OSM loop) -> painted edges on the captures (`paint.py`) -> centre refit and
     uniform stations (`recentre.py`) -> edges: the paint-step prior, measured shapes, one robust penalised spline per
     side (`edges_spline.py`), declared straights (`straights.py`) -> profile (DEM + lidar returns + `clean_profile` +
     repave crests) re-evaluated at the fitted edges -> heightfield, ortho, corners -> gates (`edge_gate.py`).
  2. `ghosts`: `tools/ghosts/build_ghosts.py --config <id>` (no logger: the racing line only, laps `[]`).
  3. `scenery`: `build_scenery.py`, then the post steps of `scenery_post.py`, then the edge and barrier gates.
* **Output:** a candidate package in `tools/track/out/<id>/` (plus `work/`: reports, previews, arrays). `--publish`
  copies it to `public/tracks/<id>/` (refuses to replace an existing package without `--overwrite-package`).
* **Checks of a candidate:** `compare_package.py --cand <dir> --ref <dir> [--by-corner]` (per-station centre, edge,
  height, racing-line differences; scenery counts), `edge_gate.py --track <dir> --config <id>`, and the autopilot
  `npx tsx tools/calibrate/drive.ts --track <dir> --alat 1.2 --learn 25 --bank --no-files [--ref-ghosts <ghosts.json>]`.
* **Captures:** `captures.py` (lists, masks, the one common Google-to-ortho shift), `register_clean.py --track <id>`
  (measures that shift), `sweep_paint.py` (paint check per station, anchored at the current edge).
* **Laguna dry runs (19 Oct 2026):** `tools/track/out/laguna_dryrun/README.md` (with the logger laps, against the
  accepted package) and the no-logger numbers there; the skill (`.claude/skills/build-track/SKILL.md`) has the summary.

The scripts that built Laguna one step at a time on 17-18 Oct 2026 (`build_laguna.py`, `build_laguna_v2.py`,
`rebuild_from_paint.py`, `fit_edges_spline.py`, the `fix_*.py` steps, `add_paved_aprons.py`, `remap_scenery.py`) are
in git history (commit a21695f); their method lives on in the modules above and their constants in the config.

## Data sources and licences

| Data | Source | Licence |
|---|---|---|
| Circuit geometry | OpenStreetMap, the 8 `highway=raceway` ways of the circuit (the pit lane is excluded), taken from the API `map` call for bbox -121.775,36.572,-121.735,36.598 | ODbL 1.0, © OpenStreetMap contributors |
| Elevation | USGS 3DEP 1 m DEM, CA_AZ_FEMA_R9_Lidar_2017_D18, tiles x61y405 and x61y406 (UTM 10N, NAVD88), read as windows over HTTP | Public domain (USGS) |
| Aerial image | USGS NAIP image service (`imagery.nationalmap.gov/.../USGSNAIPImagery/ImageServer`), about 0.6 m per pixel | Public domain (USGS/USDA) |
| Lidar point cloud (trees, building and bridge heights) | USGS 3DEP CA_AZ_FEMA_R9_Lidar_2017_D18 (the DEM's own survey), read as Entwine point tiles from the public `usgs-lidar-public/CA_FEMA_Z4_B1_2018` bucket on AWS: the 294 nodes over the ortho box, 8.3 M points. The rockyweb LAZ tiles hold the same survey, but downloads ran at about 40 KB/s | Public domain (USGS) |
| Far terrain | USGS 3DEP 1/3 arc-second DEM, tile n37w122 (COG, windowed read) | Public domain (USGS) |
| Far imagery | USGS NAIP image service, 5 × 5 km at 5 m/px | Public domain (USGS/USDA) |
| Start/finish, direction, lap data | The team's race-logger analysis in `~/projects/starlink-go-pro/laps` (read only): `centreline.npy`, `traces_warped.pkl`, `sections.pkl`, `official.pkl` | Team data |

## Cache

Downloads go to the track's cache folder (config `cache_dir`; Laguna `tools/track/cache/`, new tracks `tools/track/cache/<id>/`; gitignored): `laguna_osm.xml`, `dem_window.npz` (the merged DEM window),
`naip_tiles/` plus the stitched `naip_*.png`, `ept/` (lidar nodes), `lidar_points.npz`, `lidar_grids.npz`,
`dem13_window.npz` and `naip_far_*.png`. Delete a file to fetch it again. The scripts also write
`track_arrays.npz` there (intermediate arrays), and `preview_failed.png` when validation fails.

## Method notes

- **Centreline.** The OSM ways are stitched by shared end nodes into one loop. The loop is turned to match the
  logger's driving order (counter-clockwise), then fitted with a periodic smoothing spline and resampled.
- **Edges.** Each station is sampled across the track on the ortho at 0.3 m steps. Asphalt is cool neutral grey
  (red no higher than blue, brightness close to the centre's). A stretch longer than 1.8 m that is not asphalt
  ends the road. That includes warm dirt or grass, darker trees, barriers or shadow, and bright concrete run-off
  more than 1.5 m wide. Painted lines count as road. The half-widths go through a median filter over 41 m and
  then a Gaussian, and are clamped to 4.5–8.5 m. The centre is moved to the midpoint of the edges, two passes. The
  loop is then rolled so station 0 is the logger's start/finish and resampled to whole metres.
  **No fallback was needed:** about 93 % of stations found both edges directly; the rest were interpolated.
  The detected paved width has a median of 12.8 m (p5 9.7 m, p95 17 m). About 5.6 % of stations sit at the 8.5 m
  clamp, mostly where paved run-off or the pit-lane apron joins the track. The stored edges are symmetric about the
  centre (half-width = the mean of the two sides).
- **Elevation.** `z0_navd88` is the DEM height at the start/finish centre. The profile is sampled from the DEM
  smoothed with σ = 0.7 m. The heightfield is the unsmoothed DEM, bilinear, on a 2 m grid over the track box plus
  about 220 m. It has no holes. On the centreline it agrees with the profile to within 5 mm.
- **Banking.** The lidar shows real banking of 12–15 %, always toward the inside of the turn, at T5, the Corkscrew
  (T8/T8A) and through Rainey Curve. The 12 % cross-slope limit therefore became a hard limit of 16 %. Every station
  over 12 % is listed in the report and must be near-planar, which rules out DEM noise and edges sitting on a verge.
  The steepest grade along the track is 20 %, at the Corkscrew.
- **Corners.** Each corner is the signed-curvature peak within ±45 m of the logger's corner anchor
  (`traces2.ANCH` / `corners.CORN`), mapped into the track's s. Each entry has `name`, `turn`, `s`, `radius_m` and
  `dir`. "Rahal Straight" is placed halfway between T6 and T7.
- **Ghosts.** The script reproduces `export_dashboard.py`: lap times are scaled to the official MyLaps times, each
  driver's best clean lap is used, and the optimal lap is `optimal.solve` over clean laps from the good-GPS files,
  stitched section by section. The logger's distance (3558 m) maps onto the track's s by projecting
  `centreline.npy` onto the track centre. That mapping is smoothed and kept monotonic.
- **Racing line.** The line is a minimum-curvature line: bounded linear least squares on the second differences of
  the line points, with offsets kept 1 m inside the edges. It is then moved 30 % of the way toward the median line
  measured on the good-GPS laps: the best laps of Coby, driver D and driver A, and the optimal lap. The measured line came
  within a median of 1.8 m of the minimum-curvature line.

## Scenery (`build_scenery.py`)

The format is in CONTRACTS §2b. The script prints counts for each item and writes `previews/scenery.png`: trees in green,
OSM and lidar buildings in magenta and cyan, concrete walls white, Armco blue, tyres red, the pit wall yellow,
fences orange, kerbs red and bridges yellow.

- **Ortho grade.** `grade_ortho` in `geo.py` uses one black point for all three channels (taken from the
  0.5th percentile) and one white point. It then applies gamma 1.25 so the mid-tones stay close, a 25 % smoothstep
  S-curve, and +6 % saturation. Per-channel black points made the dry grass orange, so they are not used. The same
  grade is applied to `far_ortho.jpg`.
- **Lidar grids.** The survey has only ground (2), unclassified (1) and bridge-deck (17) classes; there are no
  vegetation or building classes. The script builds 1 m grids over the ortho box: the bare-earth DEM, the maximum of
  all points, the maximum of class-1 points, the maximum of class 17, and the share of class-1 returns that come from
  multi-return pulses. Lidar ground minus DEM has a median of -0.001 m.
- **Trees (1885).** Canopy = class-1 height above the DEM, over 2 m, with a multi-return share over 0.18 (roofs are
  single-return). Building footprints and anything within 1.5 m of the track edge are masked out. Crowns are
  local maxima of the smoothed canopy height over 3 m, at least about 4 m apart (9 × 9 window). Radius = √(area / π)
  of the canopy cells nearest each maximum, clamped to 1.2–11 m. Height p10/p50/p90 is 4.6 / 7 / 10.3 m. The
  largest crown on the inside of T8 is marked as the Corkscrew oak and raised to at least 13 m with a radius of
  at least 8 m.
- **Far trees (7000).** Outside the lidar box, these are dark, greenish blobs in the far NAIP image (5 m/px),
  strongest first, capped at 7000. Height comes from blob size (4.5–12 m). They are coarse and only meant for the
  hills on the horizon.
- **Buildings (54).** 52 come from OSM footprints. Height is the 85th percentile of the lidar surface above the DEM
  inside the footprint, falling back to `building:levels` × 3.2 m or 4 m. OSM kinds `grandstand`, `garage` and the
  5-storey "Tower" keep their kind. Two unmapped structures come from the lidar: compact, single-return blobs of
  45–6000 m² and at least 3 m from the edge, footprinted as minimum rotated rectangles.
- **Bridges (5).** These are OSM `bridge=yes` ways that cross the circuit: the S/F footbridge (s 37), footbridges at
  s 942 and s 1423, and road bridges at s 1852 and s 2617. Deck height is the median of class-17 points above the
  track, or of the surface between 3.5 and 12 m above it; the bridge at s 942 has no lidar deck and uses a default
  of 6 m. The span is the part of the way within 25 m of the edge, so the S/F bridge also covers the pit lane.
  Banner texts (MISSION / PORSCHE / WEATHERTECH on the S/F bridge, from the team's onboard frames) are in `BANNERS`.
- **Barriers.** Each OSM `barrier=wall` way is resampled at 2 m. Points on the track are dropped; points closer
  than 2 m to the edge are pushed out to 2 m. A run whose median distance is under 14 m is a concrete wall
  (1 m) with a 3 m catch fence. Further out, it is Armco. This is a heuristic, not detected from the ortho. Tyre
  walls are **hand-placed as metres before/after the track.json corner s** on the outside (from the corner direction) of T2, T5, T8, T8A, T9 (Rainey) and T11 (`TYRE_CORNERS`).
  They stand 1 m in front of the nearest outside OSM wall, or 12 m out if there is none. The pit wall
  (1.1 m concrete, 0.6 m off the left edge) follows the OSM "Pit Lane" way wherever it runs within 25 m on the
  left, from s 3210 round to s 561. It has a 3.5 m catch fence up to 120 m past the line. The paddock catch
  fence is the OSM `barrier=fence` way ("The Paddock").
- **Edge lines.** White 0.12 m lines, 0.15 m inside both edges, everywhere except through kerbs (±3 m) and where the OSM pit lane touches the left edge. They are not detected from the image: in NAIP at 0.6 m/px, asphalt (luminance about 150) and dry dirt (about 155–165) are almost the same brightness and differ only in hue, so a 0.12 m line does not show. On v2: left 2514 m and right 2822 m of 3560 m.
- **Pit lane.** Taken from the OSM "Pit Lane" way, resampled at 1 m and lightly smoothed. Half-widths come from
  the NAIP asphalt extent (`detect_edges`, clamped to 3–6 m); detection is too weak there, so in practice the 4 m
  fallback (8 m paved) applies. Any edge that falls inside the track is clamped onto the track edge and given the
  track's edge height, so the pit lane meets the track exactly. Stretches that run inside the track's own paved
  width are dropped: the v2 track already includes the pit-exit apron through T1. That leaves two parts: the
  entry from s≈3097 (before T11) round to s≈166 past S/F, and the exit from s≈281 round the inside of T2 to rejoin
  at s≈596. OSM puts the rejoin after T2, not before it. Cross-sections are a straight-line fit to the DEM, since
  pit lanes are flat; this removes lips from walls and garages. The track's left edge line is kept through the
  merges as the blend line.
- **Onboard comparison (`tools/track/compare/`).** `find_frames.py` maps logger GPS to video time and track s;
  `grab.py` extracts windscreen crops; `make_sheets.py` builds the `<corner>.jpg` side-by-side sheets. The sim
  frames in `compare/sim/` are canvas captures from the driver camera. From the footage:
  - **Paved runoff** (`PAVED_RUNOFF`, later than the 2017 lidar and NAIP): the outside of T6, T9 (Rainey) and
    T10. Each zone runs from the track edge to 1.5 m short of the outside wall (6–25 m, else 12 m), tapered at
    the ends, around a smoothed centreline with perpendicular edges. Its heights are the surface the car drives on
    there anyway: the track edge blending to the heightfield with the physics' smoothstep over 5 m. Paving only
    changes grip and look, so zone edges and tapered ends add no crease. An earlier flat DEM fit folded the kerbs
    and green paint at the zone ends.
  - **Bridge banners** (`BANNERS`): S/F bridge MISSION · WEATHERTECH · MISSION · PORSCHE; the T3–T4 bridge is the
    TIRE RACK arch (`BRIDGE_STYLE`); the bridge after T8A carries WeatherTech and "Auto. Home. Pet. Find Your Fit."
  - **Kinetic hangar:** the gabled hangar ahead-left on the T3 approach (`HANGARS`).
  - **Banner boards** (`BANNER_BOARDS`): PORSCHE at T1 and T6, WeatherTech at T7, ad boards along the T11 wall.
  - **Rahal gantry:** the two lattice towers with cables across the track near the end of Rahal straight.
- **Kerbs (21).** For every corner with a direction there is an apex kerb on the inside, half-length 0.9 × radius
  clamped to 28–45 m; fast kinks (radius over 120 m) get ±25 m. There is also an exit kerb on the outside from
  s + 15 m, 45–70 m long, with 1.5 m of green paint beyond it. Kerbs are 0.9 m wide and lie inside the edge (v2 edges include the kerbs), with red and white every 2 m and a dark seam against the asphalt.
- **Boards.** Brake boards 3-2-1 stand 150/100/50 m before T2, T5, T8 and T11, and corner-number boards 75 m
  before each turn, all on the outside. The starter's flag stand is on the pit wall 8 m before the S/F bridge.
  All of these are hand-placed by rule, not surveyed.
- **Far terrain.** 5 × 5 km at 10 m from the 1/3 arc-second DEM. Inside the near box the near heightfield is
  copied in so the seam matches.

Payload: `scenery.json` 0.38 MB + `far_heightfield.bin` 1.00 MB + `far_ortho.jpg` 0.29 MB = 1.7 MB new;
the regraded `ortho.jpg` is 1.30 MB.

**Re-running after a track rebuild.** Every placement is derived from `track.json`: its corners give the kerbs,
boards, tyre walls and Corkscrew oak; its edges give the OSM wall runs and the pit wall; its ortho box gives the
lidar area. The same single command regenerates all of `scenery.json`. If the ortho box changes, the lidar and
NAIP caches are re-fetched automatically, because they are keyed by the box.

**Close-range detail (app).** `scene.ts` generates two tileable 256 px detail maps at startup, each with albedo and
a normal map: asphalt with aggregate chips and pores on a 0.8 m tile, and dry grass, clods and pebbles on a 1.6 m
tile. They are multiplied over the ortho in world space and fade out between 30 and 80 m.

## v2 centreline (now the first centre of `centre.py`)

**Why.** The v1 centre was a spline through the coarse OSM nodes. It kinked at way junctions and corner nodes, and
recentring along its own normals kept the kinks. Its corner radii came out 20–70 % tighter than the driven line,
for example T6 at 34 m against 89 m. At ghost speeds that meant 1.5–2.2 g.

**Centre.** The shape comes from the logger's GPS-driven `centreline.npy`. Its curvature matches the IMU's
alat/v² with r = 0.98. The line is moved toward the imagery midpoint by a penalised least-squares fit along its
normals. A stiff second-difference term on the move keeps the driven curvature, and a third-difference term on the
positions removes kinks. The fit runs twice: the second pass uses edges re-detected along the pass-1 normals.
Within ±60 m of every corner, the minimum radius is within 15 % of `centreline.npy`'s (the limit is 25 %).

**Edges.** Each side is stored separately, so the left and right half-widths differ, by a median of 0.8 m and at
most 4.4 m. The profile fractions are piecewise: f < 0 scales the left half-width and f > 0 the right, which is
how `src/physics/track.ts` reads them. Note that `scene.ts` `buildRibbon` interpolates linearly from the left
edge to the right edge, so the visual mesh's middle vertex is the edge midpoint, not the centre. Kerbs, which blur
to bright pink at 0.6 m/px, now count as road, the same way painted lines do. The largest edge change between
adjacent stations is 0.41 m.

**Racing line.** The line is solved by bounded least squares with an active-set solver: curvature, plus 3×
curvature change, with the edges less 1 m as bounds. The bounds are a smoothed lower envelope of the edges. A
second bounded solve then pulls the line toward a 30 % blend with the measured good-GPS line. The previous v1
approach was a clipped blend, which put kinks where the measured line lay outside the bounds.

**Implied g.** The ghost builder prints a per-corner table of implied g, both plain (v²κ/g) and the tyre share
after the lidar banking: μ = (a − tan b)/(1 + a·tan b). T5, the Corkscrew and Rainey are banked 6–13 %. The
checks use the tyre share for "too tight" (it must be at most 1.3 at apexes and 1.35 anywhere) and the plain value
for "too straight" (it must be at least 0.9).

### 2017 lidar, 2023 repave: T6 sag removed

The elevation data is the 2017 lidar, but the circuit was fully repaved in 2023 (finished in June 2023). At the T6
apex the 2017 data shows a sag of about 0.4 m: a vertical radius of +230 m, which adds about 0.2 g of load at
120 km/h. The ground returns confirm the sag is in the survey. Coby drove the circuit in October 2026 and reports
that T6 is now a crest.

The config's `repave_fixes` (was `build_laguna_v2.py` `REPAVE_FIXES`) rebuild the centre height over s = 1895–2000 from its vertical curvature:

- **Crest zone (s = 1905–1965):** the curvature is crest or flat (z'' ≤ 0), never a hollow.
- **Rest of the window:** a gentle sag of R ≥ 1500 m at most.
- **Window ends:** heights and slopes match the original.
- **Cross-section:** the same height change is applied across the whole section, so the banking is unchanged. It
  is also carried into `heightfield.bin` under the road, fading out 2–12 m beyond the edges.

The fix needs a wider window than the requested 1910–1970. The grade is +1.8 % at both 1910 and 1970, and the road
climbs on into Rahal Straight. A pure crest between those two points could therefore not meet both ends, so the
grade increase now happens after the apex instead of in a hollow at it.

No other hollow was treated. The other places where the racing line sits more than 0.2 m below a 50 m chord are
grade changes, such as the foot of a slope or the start of a climb. They are not local dips: a profile detrended at
a 25 m scale has no hollow over 0.2 m apart from the Corkscrew and Rainey, which are kept, along with T10 and the T1
crest.

The profile is also pulled onto the lidar ground returns (`lidar_correct`). Profile points at the very edge that
sit on a kerb face or berm are replaced with the road plane extended out to the edge.

### Profile clean-up (`clean_profile`)

In the first lidar-corrected profile, consecutive 1 m stations were noisy to about 1–2 cm. Most of this came from
3–5-return medians and from zero corrections where a station had no returns, which then got smoothed together with
real corrections. That noise implied vertical radii of 20–150 m almost everywhere, with single-station steps of up
to 15 cm. Drivers felt it as "dips at apexes".

The fix has three parts:

- **Lidar correction:** gaps are now filled along s, then the correction gets a 7-station median and a 4 m
  Gaussian.
- **Cross-section:**
  - The edge points may sit at most 4 cm off the line fitted to the five inner points. This replaces the earlier
    0.15 m snap.
  - Every point may sit at most 2 cm off the section's quadratic (banking plus crown).
- **Along s:** each column gets a 5-station median and a 1.5 m Gaussian.

Results on the racing line:

- Stations where the 1 m second difference implies a radius under 150 m dropped from 539 to 37, all of them in the
  Corkscrew, where the crest and drop are real at R ≈ 45–80 m.
- The minimum 1 m radius at the apexes is now 155–570 m; it was 26–170 m.

`tools/track/previews/profile_roughness.png` shows the before and after.
