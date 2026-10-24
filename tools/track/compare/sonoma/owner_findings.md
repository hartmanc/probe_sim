# Sonoma: owner findings (Coby), by checkpoint

## Checkpoint 1 (19 Oct 2026, first look at the branch build, before driving)
- "Otherwise recognizable where that car is at" (front straight, launch).
- **No trees on the infield / drag-strip area.** The rule-based tree pass put tall trees between the front straight
  and the drag strip; Coby remembers none there. Check every tree blob against the NAIP / Google imagery (dark
  canopy visible) and drop the ones the lidar invented (light poles, timing tower, fences, grandstand frames).
- **Model Sonoma's garages** (the paddock garage rows behind the pit lane): red roofs, from OSM footprints with lidar
  heights and a roof colour taken from the satellite (needs a per-building colour / kind in the config).

## Checkpoint 1 drive (19 Oct 2026, preview of 6791f97)
- **Hot-lap start:** comes out of the T11 hairpin and slams into a wall. (Per-track start + check why a wall is reachable.)
- **LAYOUT WRONG at 8a/9/9a/10.** Lemons runs the IndyCar layout, not the fast Turn 10 (the NASCAR layout). Driving
  through 8a toward the back straight put the car in the dirt. Layout picture:
  https://registration.24hoursoflemons.com/userfiles/races/26_sonoma.png
- **The Chute (NASCAR short course between T4 and T7) pavement is missing.** Rule: every paved part of the circuit that
  exists but is not in use (the Chute, the drag strip, the fast-T10 variant, unused 9/9a options) gets race-track
  pavement in the sim, blocked off with cones.
- **T1 through T2 feels correct; the pit exit looks a little screwed up.**
- **Pit straight walls missing on both sides** (almost the whole straight; see Google Maps: grandstand on driver's left
  just before start/finish, pit lane left, drag strip right, T12 at the right). Many other walls and the corner-worker
  stands are missing (scenery).
- **T7 / 7a feels completely wrong.** There is a lot of run-off pavement on the inside of T7 and cars are typically
  allowed to go way off there (adding that distance is not beneficial anyway, so the line stays on the track). The
  approach to T7 is STRAIGHT on both sides; the sim's left edge has waviness there.
- Question answered: agents can use Google Maps Street View / user photo spheres on the circuit (e.g. the T7 approach
  panorama gd1SNdksCq5QZtwlsrzR7g) via Chrome screenshots as reference imagery (reference only, never textures).
- **Kerbs:** Sonoma's kerbs are BLUE and white (not red/white), low flat concrete, narrow (~0.5-0.6 m), blocks ~1 m long,
  faded and rubbered, with dirt right behind them (Street View on the T7 inside). "Gives the track a different feel than
  Laguna." Per-track kerb colours / width / block length belong in the config.

## Round 13 drive (23 Oct 2026, 19:05 PDT, preview probe-acdxuugxf)
- **T7 complex: better, but the terrain / elevation still mismatches.** His screenshot from the T7 approach (hot lap,
  car stopped): the inactive pavement on the left (the Chute / short-T7 road) sits on a different level from the
  racing surface, with a visible ridge where the dark inactive block meets the course; the island with the red/white
  kerbs reads as a trough (green strip below the kerbs); the blue/white kerb run and the right-hand paddock pavement step
  down at their edges. His words: "we might have to deviate from the lidar scan, if that's what's causing these
  problems. The key thing is that the active and inactive track surfaces actually go together in a sensical way that
  doesn't break immersion." Rule: every inactive paved surface that touches the course joins it with no step and no
  trough, even where that means leaving the lidar.
- **T10: a separate concrete wall end juts out into traffic.** From the grass on the driver's right past T10 (off
  track, looking along the outer wall): the long outer wall on the right stops, and a short free-standing concrete wall
  piece stands in the gap with its end facing oncoming cars; a dark strip on the ground beside it looks like a tyre
  wall that was not built. His words: "I don't think this separate wall is sitting out by T10. As discussed before,
  we should be skeptical of any concrete wall ends that jut out into traffic. This would kill someone if they ran into
  it at speed. Seems likely that a section of wall is missing. I see a dark texture that looks like a missing tire
  wall." Rule (reaffirmed): a wall end facing traffic is a missing section or a missing tyre wall, never a feature.
  Round 14 part B.
- **T1 edges from his strokes** (drawing page 6nG9T3NgsVajJPNSKkwhAc, read back 20:25 PDT, filed in
  `compare/sonoma/owner_edges_r14/`): red = both asphalt edges through s ~150-330; the round-13 fit's bulge toward the
  pit lane on the right at s ~195-250 is wrong ("I don't think this concave section on the right hand of the track is
  here"), and so is its excursion into the paddock-side truck area on the left. Green = the pit-lane edge and the
  paddock access roads (closed pavement). The red arc into the paddock-side mouth at s ~175 is the boundary and gets a
  cone line: "Put a few cones there".
