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
