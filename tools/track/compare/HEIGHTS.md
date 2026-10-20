# Measuring heights at eye level (every circuit)

Walls at the default 1 m, a tent extruded to 12 m and a bridge floating in the air (Sonoma, 19 Oct 2026) all came from
heights nobody measured. Every height in an inventory row (`tools/track/compare/<id>/inventory.json`, `attrs.h_m`) cites
one of the methods below in `attrs.h_method`; `inventory.py` refuses a height without one and counts the rows marked
`unmeasured`. The helper is `tools/track/inventory/heights.py` (standard library; examples below are its real output).
Reference imagery is reference only: measure on it, never texture with it, never commit it.

## The geometry

A level pinhole camera at height `H` above flat ground. Rows are counted down from the top of the image.

- **Horizon row** `y_h`: Street View with pitch 0 (`...,90t` in the URL) puts it on the middle row of the view (829 px
  tall window: 414.5). On an onboard frame use the vanishing point of a straight, level stretch of road, or the far
  horizon line; a camera pitched down puts it below the middle.
- **Horizon ratio** (`horizon-ratio`, `heights.py horizon`): an object standing on the camera's ground, base row `y_b`,
  top row `y_t`: **h = H (y_b - y_t) / (y_b - y_h)**. The focal length cancels, so the FOV is not needed. Valid only
  when the base is visible and on the camera's level: not on a bank, a terrace or behind a barrier.
- **Reference** (`*-ref`, `heights.py ref`): an object of known size at the same distance (standing against the object
  or on the same base row): **h = h_ref (y_b - y_t) / (y_b,ref - y_t,ref)**.
- **Camera height from a reference** (`heights.py camh`): an onboard camera's `H` is unknown (hood, roof, windscreen):
  **H = h_ref (y_b,ref - y_h) / (y_b,ref - y_t,ref)** from a Jersey barrier or a cone near the object, then the horizon
  ratio with that `H`.
- **Distance** (`heights.py dist`): d = H f / (y_b - y_h), f = (image height / 2) / tan(vertical FOV / 2); with a known
  distance (map) and the base not on the camera's level: **h = d (y_b - y_t) / f** (`heights.py angles`).
- **Shadow** (`shadow`, `heights.py shadow`): on a satellite capture, h = shadow length x tan(sun elevation); the sun
  elevation from the capture date and time (NOAA equations in `sun_elevation`), or, when the capture time is unknown
  (Google imagery), from an object of known height in the same capture: tan(e) = h_ref / shadow_ref.

## Known sizes (`heights.KNOWN`)

| object | height | note |
|---|---|---|
| Street View camera (car-mounted rig) | 2.5 m | checked below on a formula car (1.00 m) and a cone (0.42 m) |
| Jersey barrier | 0.81 m | 32 in; the most common reference beside the track |
| SAFER barrier / pit wall | 1.1-1.2 m | |
| catch-fence posts | 3-4 m | curved-top posts included; count the cables (about 0.3-0.4 m apart) as a check |
| traffic cone | 0.70 m (28 in), 0.46 m (18 in) | |
| formula car (roll hoop) | 0.9 m | |
| person | 1.7 m | |
| door | 2.03 m | US standard 80 in |
| tyre stack layer | 0.21 m | one passenger tyre lying flat |
| building storey | 3.0-3.5 m | count storeys on Street View; use 3.2 |

## Worked examples (Sonoma, 20 Oct 2026)

1. **Wall, Street View** (`horizon-ratio`). Pit wall at the line, panorama 5MY4xR9O7etAXEHnZCVnGQ, heading 300, pitch 0,
   window 1200 x 829 (horizon 414.5). Left wall at the image edge: top row 565, base row 680:
   `heights.py horizon --top 565 --bottom 680 --horizon 414.5 --cam 2.5` -> **1.08 m**. The right (drag-strip) wall at
   x 1000 gives 0.92-0.95 m. Check of the camera height on the T11 panorama jrXpHaDfJT2APw6zcyBKRA: formula car rows
   458 / 487 -> 1.00 m, 18 in cone rows 590 / 625 -> 0.42 m: the 2.5 m rig height holds.
2. **Wall with board panels, onboard** (`camh` then `horizon-ratio`). T10 outside wall, March 2026 onboard
   RAZip6S84CM at 1:50 (frame `inventory/frames/t110.jpg`, 1200 x 829 screen capture). Horizon (far road and hills) row
   460. The dark Jersey base under the boards: top 492, base 527 -> `camh --ref-top 492 --ref-bottom 527 --horizon 460
   --ref-h 0.81` -> camera 1.55 m. Board top 355 at the same column: `horizon --top 355 --bottom 527 --horizon 460 --cam
   1.55` -> **3.98 m** (0.8 m concrete + 3.2 m boards). The package has these walls at 1.0 m (owner note 13: "the walls
   at and following T10 are much higher").
3. **Tall wall, Street View** (`horizon-ratio`). The wall between the pit-in lane and the paddock (Sprint boards in
   2011), panorama jrXpHaDfJT2APw6zcyBKRA heading 196: base row 459, board top 366 -> **5.22 m**.
4. **Same wall, onboard, door reference** (`door-ref`) and a rejected measurement. 2026 onboard at 1:56 (`t116.jpg`):
   a door in the wall face, top row 461, its base hidden behind the Jersey barrier at rows 530-545; the board top 339 at
   the same column: `ref --top 339 --bottom 545 --ref-top 461 --ref-bottom 545 --ref-h 2.03` -> 4.98 m, with the base at
   530 -> 5.62 m: **5.0-5.6 m**, agreeing with example 3. The horizon ratio on the 2025 pit-in video (24of8fjjAug 24:06,
   base hidden behind the Jersey, base row taken from the Jersey's) gave 3.3-4.5 m: **never take the base from a nearer
   object**; that error is the 1 m default wall in disguise.
5. **Tyre stack, Street View** (`horizon-ratio`). Yellow / blue stack on the T11 apron, jrXpHaDfJT2APw6zcyBKRA: rows
   465 / 492 -> **0.87 m** (4 layers of 0.21 m).
6. **Fence** (`fence-post-ref`). Catch-fence posts on the bank walls (onboard 0:12-0:30, 1:30-1:38, 1:44-1:55): the
   curved post top stands 3.5-4.5 times the height of the 0.81-1.0 m wall below it at the same column -> **3.5-4.0 m**;
   recorded 3.5 m on the hillside walls and 4.0 m on the T10-T11 walls (taller relative to the wall).
7. **Kerb** (`horizon-ratio`, upper bound). T2 entry kerb, panorama H9xspk4q_OoFIjVDhaMzDA heading 210: at base row
   720 one pixel is 2.5 / (720 - 414.5) = 0.8 cm; no step is visible at either kerb edge (under 2 px) -> **flat, under
   2 cm** in 2011. A raised kerb shows its face: a 10 cm face would be 12 px there. The 2026 onboard shows red / white
   kerbs with a rounded outer face; their profile comes from the survey (config `scenery.kerb.profile`), not from this.
8. **Building** (`storeys`). Count storeys on Street View (QduY6QTXmw4JDevQVE_b-g: two-storey suites and control
   buildings at T12) x 3.2 m -> **6.4 m**; cross-check with the lidar p60 (`scenery.building_height_robust`, manifest).
   A white tent on the 2026 capture over a 2022-24 lidar footprint is the case to check on Street View and the onboard
   before trusting the lidar's 12 m.
9. **Shadow** (`shadow`). There is no capture time for the Google captures, so the sun comes from a known height in the
   same capture (a Jersey wall's shadow width, a building measured by lidar), or from the date and time of a NAIP frame.
   The helper's arithmetic: a light mast at Sonoma on 14 Jun 2025 at 19:30 UTC (sun 72.8 deg) casting a 6.3 m shadow is
   `shadow --len 6.3 --lat 38.161 --lon -122.455 --utc 2025-06-14T19:30` -> 20.4 m (an illustration of the call, not a
   measurement).

## Rules

- A height on a bank, a terrace or behind a barrier: use a reference standing against it (a door, a person, a fence
  post), or the distance from the map with `angles`; never the horizon ratio with a borrowed base row.
- Street View is old (Sonoma: July 2011); a height measured on it is kept only where the 2026 onboard shows the same
  structure (the same doors, the same wall line).
- Record the rows used in the inventory note so the measurement can be repeated.
