# Sonoma: scenery evidence manifest (rederive run, 20 Oct 2026)

Built by the build-track skill from a clean config: inventory (`inventory.md`), Street View survey (`streetview.md`),
clean z20 captures (`satellite_clean/`, 80 captures, common shift 0.00 / +0.45 m), the March 2026 Lemons onboard
RAZip6S84CM and the 2025 pit-lane video 24of8fjjAug (frames only, headless Chrome, never downloaded), OSM and the
2022-24 lidar. Every config entry carries its `src`; the generated tables below list each object and each inventory
row's outcome. Round r1 = this run.

## Method per kind (SKILL stage 3)

- **Walls, tyre walls, fences** (3.4): every band was picked with `compare/wall_measure.py` (edge mode or a guide read
  off `capstrip.py` strips), checked on capstrip / capwin overlays, and confirmed on the onboard; rms and pick rate in
  each `src`. Heights by HEIGHTS.md methods (`h_src`); unread heights say `unmeasured`.
- **Kerbs** (3.3): `kerb_detect.py` (95 candidates) confirmed strip by strip on the capture strips (trailers parked on
  the edge make many grey false runs: rejected) and on the onboard; colour per strip from the frame named in
  `colour_src`; T5 inside is plain yellow (onboard 0:42).
- **Pit lane** (3.5): OSM lane, three declared walls (pit wall, pit-in outer board wall, pit-out wall), cones on the
  measured double-yellow blend line, edge line cut there, impact block at the pit-in nose.
- **Closed roads** (3.6): Chute, 2020 bypass, short T7, PWC lower hairpin, T11a, drag strip; cones only at the bypass
  mouth (onboard 1:32), delineators at the Chute and short-T7 mouths; open runoff listed in `gates.allowed` with the
  frame that shows it open.
- **Stands** (3.7): four terraces by `terrace_measure.py` ray mode (T2, T3a-T4, back straight, main grandstand).
- **Buildings**: robust lidar heights; each kept building cites a capture or the onboard row it was seen at
  (`building_evidence`); 11 with no 2026 source are dropped.
- **Masts**: 26 isolated lidar spikes (DSM - DEM 19-28 m) inside the capture coverage.

## Movable barriers

- `tyre_stacks` at s 2180 / 2192 left (onboard 1:14): loose black tyre stacks on the paddock edge left of T7. **movable**.

## Removed for lack of evidence

| object | why |
|---|---|
| T9 left wall (s 2559-2700, wall_measure bright) | the picks followed parked trailer edges on c20_s0165/s0220 (cw window, 20 Oct): not a wall; L1 dark wall covers the place |
| OSM armco rule on 380830042 / 380830043 | re-kinded to dark concrete on the capture's dark band (osm_barrier_overrides) |
| 11 buildings (lidar blobs at T2-T3 and behind the paddock, OSM sheds 90-270 m off) | no 2026 capture covers them and the onboard does not show them |
| Street View 2011 items (blue/white kerbs, yellow/blue T11 stacks, 2011 board names) | the 2026 onboard contradicts them (streetview.md) |

## Scans and captures examined

| scan | captures |
|---|---|
| left / right bands 0-650 | c20_s1595..s1980, c20_s2035..s2365 |
| T3-T4 | c20_s2420..s2750 |
| T5-Carousel | c20_s2750..s3410 |
| T6-T7 road, T7, T7a | c20_s3465..s4070 |
| T8-T9a | c20_s0055..c20_o0715 |
| T10-T12 | c20_s0715..s1540 |
| pit lane, front straight | c20_s1100..s1925 |

## Dispositions (SKILL 3.13)

| kind | side | s (m) | what | source | disposition |
|---|---|---|---|---|---|
| building | left | 112.8 | pit-out buildings, red roofs | onboard:RAZip6S84CM@4.0 | placed: red-roof building (the OSM footprint at s 176, seen ahead at 0:04 and abeam at 2:22) |
| cone_line | right | 2731.6 | orange cones at the bypass mouth | onboard:RAZip6S84CM@92.0 | placed: closed road 2020 bypass mouth (the mouth at s 2802; the 1:32 frame sees the cones ahead) |
| mast | right | 2280.9 | light mast | onboard:RAZip6S84CM@77.0 | placed: lidar spike s 2345.7 (the mast seen ahead right at 1:17-1:18) |
| mast | right | 2452.1 | light mast | onboard:RAZip6S84CM@84.0 | placed: lidar spike s 2421.6 (seen ahead right at 1:24) |
| stand | left | 371.7 | hillside terrace (T2) | onboard:RAZip6S84CM@12.0 | placed: terrace T2 terrace (seen ahead at 0:12; its measured front starts at s ~390) |
| stand | left | 2662.9 | back-straight terrace | onboard:RAZip6S84CM@90.0 | placed: terrace back-straight terrace (seen ahead at 1:30) |
| stand | left | 3966.8 | main grandstand | onboard:RAZip6S84CM@134.0 | placed: terrace main grandstand (seen across the pit lane at 2:14) |
| station | right | 401.0 | marshal post (white hut) | onboard:RAZip6S84CM@13.5 | placed: T2 post (at s 416 on c20_s2145, 15 m past the mapped row) |
| station | right | 805.0 | marshal tower (white hut on legs) | onboard:RAZip6S84CM@27.5 | placed: T3a tower (at s 830 on c20_s2530; the row's time map is +-25 m here) |
| tyre_stack | left | 836.7 | black tyre stacks at the terrace foot | onboard:RAZip6S84CM@29.0 | not resolvable: c20_s2475, c20_s2530 examined: the dark band at the terrace foot is the Jersey and its shadow (placed as the T3a Jersey); no free-standing stack can be told apart |
