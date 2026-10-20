# Buttonwillow Street View / photo-sphere survey (build-track stage 0.5, 20 Oct 2026)

**Result: no Street View or photo sphere on the circuit.** Nothing in `inventory/streetview.jsonl` comes from Street View;
the eye-level evidence is the 2026 Lemons onboard (`inventory/source.json`) and the 2026 pit-lane video.

## How it was checked

`tools/track/compare/headless_capture.ts svcover` (headless Chrome, throwaway profile): Google Maps satellite with the
pegman pressed, which draws the coverage overlay (blue lines = Street View, dotted = photo paths, dots = photo spheres).
Screenshots are reference only and stay local (`compare/buttonwillow/streetview/`, ignored).

| view | centre (lat, lon), zoom | what the overlay shows |
|---|---|---|
| `coverage_z16.jpg` | 35.4908, -119.5447, z16 (the whole circuit and paddock) | Street View only along **Cal Club Rd**, the public access road entering from the north and ending in the paddock (x ~ -150 m of the ENU origin), and on I-5 to the north-east. No line on any part of the circuit, the pit lane or the infield. One map pin with photos at the paddock ("Buttonwillow Raceway Park") and the POI "Starter's Tower" (the control tower), both business photo pins, not photo spheres on the track. |
| `coverage_tower_z19.jpg` | 35.48915, -119.54459, z19 (the tower and the front straight) | No dot or line on the pit lane, the pit wall or the front straight. Google labels the road north of the pit wall "Pit Lane", the track west of the tower "Sunset", and the infield connector roads south of the straight "Pacific" and "Atlantic" (OSM names too). |

## Per place (corners and major features)

| place | panorama | why not |
|---|---|---|
| every corner T1-T11, the front straight, the pit lane, the control tower, the corner stations | none | no coverage (above) |
| Cal Club Rd (north access road) | not opened | 200-250 m from the nearest track edge (the T9-T11 leg) across the paddock and dirt: no height or object on the track could be read from it |

## Consequence for the build

- Heights come from the onboard (camera height 1.05 m from the pit-wall Jersey, `compare/HEIGHTS.md` camh / horizon
  ratio), from storeys, and from the lidar; none from the 2.5 m Street View camera.
- Source precedence is unchanged (recent onboard > 2026 captures > NAIP > OSM > lidar); there is simply no Street View
  tier here. This is recorded in the manifest's survey walk.
