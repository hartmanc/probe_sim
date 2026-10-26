# Mid-Ohio — first geometry round

Worktree: `/private/tmp/probe-sim-mid-ohio`, branch `mid-ohio`, based on `6f890b9`.
This is a stage-1 candidate, not an accepted circuit or a published app track.

## Layout decision

The owner's 25 Oct 2026 clarification is authoritative: retain the entire black
numbered loop in the supplied Lemons map. Drive from T1 down the long straight
to T2, then up the full back straight through T3. Omit only the grey inner chicane
before T2. Neither east/west short connector is part of the driven lap.

The six OSM ways in `tracks/mid_ohio/config.py` join exactly by shared node IDs.
Their smoothed OSM loop is 3622.952 m, against the operator's nominal 2.258 miles
(3633.934 m). This is source topology, not the final fitted length.

The official [2026 Lemons event](https://24hoursoflemons.com/race/?id=439) HTML
references `24HoL__TrackMap_Mid-Ohio.png`; that image URL returned HTTP 404 during
research. The owner-supplied reference and explicit clarification settle the loop.

## Evidence and provenance

`tracks/mid_ohio/sources.json` records the public source URLs, discovered recent
onboard candidates, the elevation datum, and construction history. Downloads,
reference images and video frames remain local and are never package textures.

- OSM API map: requested bounding box `(-82.646,40.678,-82.625,40.699)`.
- USGS 3DEP 1 m DEM: `OH_Statewide_Phase1_2019_B19`, UTM 17N / NAVD88.
- EPT cloud: `OH_Statewide_Phase1_3_2019`. TNM's vendor metadata link names
  subproject 8, but that EPT cloud is a remote patch. Survey footprint and local
  descendant hierarchy nodes establish subproject 3 as the actual circuit source.
- Ground texture source: USGS NAIP (public domain), six requested tiles.
- Measurement source: own clean Google Maps z20 captures, 40 m spacing, reference
  only, labels off, own throwaway headless Chrome profile. No owner's tab touched.
- Start/finish: the pair of narrow white stripes at the starter stand, preliminary
  clean-capture pixel `(439,273)` in `satellite_test/test_sf_google.jpg`. Google
  frame coordinate `(40.689491,-82.635276)`, to be registered with the common shift.
- Published repave width: 40 ft (12.192 m). It is an advisory width reference,
  not a clamp or a replacement for measured edge evidence.

## Known elevation limitation

The [operator's 2023 repave report](https://www.midohio.com/news-m/938-full-repave-of-racing-surface-completed-at-mid-ohio-sports-car-course)
records completion on 27 Oct 2023. The
[19 Dec 2024 construction report](https://www.midohio.com/news-m/1084-track-and-facility-improvements-completed-at-mid-ohio-sports-car-course)
records reconstruction of 520 ft (158.496 m) around T4: the existing apex kerb and
plan footprint were retained, banking reduced from 4 to 2 degrees, outside track
excavated by up to 18 in, and runoff raised and regraded. The 2019 cloud predates
both changes. No invented elevation correction has been applied; a passing
numeric profile gate cannot establish the rebuilt T4's current surface.

This outline checkpoint concerns plan edges. The T4 survey mismatch must be
resolved before a claim that the track drives like the current circuit.

## T1 approach bridge ground repair

The EPT cloud classifies part of the footbridge deck as class 2 (ground), alongside
class 17 (bridge). At provisional stations 230–236 the centre returns are about
7.96 m above start/finish, while the actual road immediately before and after is
about 3.45–3.65 m. Treating that deck as ground produced 26.5–30.2% false banking
and a 0.350 m profile step. The capture shows the overhead bridge at that location.

Config `profile_gaps` cites its measured latitude/longitude and a 15 m half-window
with clean 7 m endpoint slope samples. The opt-in builder excludes cloud samples
in that interval, joins each of the seven profile columns using the measured
endpoint heights and slopes, and carries the reconstructed banking/crown into
the heightfield with a controlled lateral fade. No height or banking is guessed.
The raw cloud and DEM remain cached unchanged. Other tracks have no opt-in.

On the 51-capture diagnostic fit, the repaired profile's worst column step was
0.023 m; inner/outer cross-slope maxima were 11.7%/11.4%; centre heightfield/profile
difference was 0.004 m median, 0.015 m p95. These are preliminary diagnostics, not
final whole-lap acceptance figures. Six focused tests cover deck rejection,
endpoint slope and bank continuity, nonaligned curved terrain, valid dimensions,
and empty-config identity. Independent parent review found and prompted removal
of nearest-station quantization in the first heightfield implementation.

## Step ledger

| Step | Record or current status |
|---|---|
| 0.1 loop | Owner clarification above; config's six shared-node OSM ways. Confirmed by 2026 N837 Motorsport onboard, decoded t20–50. |
| 0.2 sources | `tracks/mid_ohio/sources.json`; USGS metadata cached locally. |
| 0.3 captures | 91 clean z20 captures, 40 m spacing; final common shift (-0.60,0.00) m. |
| 0.4 recent videos | Primary N837 Motorsport 15 Apr 2026 onboard verified at sparse decoded timestamps; full inventory pending. |
| 0.5 Street View | Pending before scenery. |
| 0.6 two-second inventory | Pending before scenery; no objects placed. |
| 0.7 time-to-station map | Pending before scenery. |
| 0.8 pit / Street View rows | Pending before scenery. |
| 0.9 height methods | No scenery heights claimed. |
| 0.10 inventory validation | Pending before scenery. |
| 1.1 loop and frame | Config and shared-node stitching; initial source topology length above. |
| 1.2 capture registration | Full 91-capture registration: shift (-0.60,0.00) m, median of 77 peak>=8; seven weak repetitive-region matches are outliers, never per-capture corrections. |
| 1.3 centre fit | Final whole-lap painted-road midpoint refit in `out/mid_ohio`; 3589.152 m. |
| 1.4 fitted edges | Periodic edge fits on all 91 registered captures; `geometry_report_r1.json`. |
| 1.5 edge convention | Painted line where no kerb, outer limit of driveable flat kerb where present. |
| 1.6 elevation | DEM and EPT fetched; T4 reconstruction limitation above. |
| 1.7 corners | Thirteen OSM anchors against owner's numbering, signed curvature peaks solved by builder. |
| 1.8 roughness | Profile and cross-slope gates pass; max profile-column step 0.025 m. |
| 1.9 gates / owner outline | All edge gates pass; nominal-length gate fails. Owner drawing page `review_r1/edges.html` rebuilt from this candidate. |
| 1.10 hood sheet | Held behind mandatory owner edge checkpoint. |
| 1.11 derived data | Held behind mandatory owner edge checkpoint. |
| 1.12 shoulders | Held behind mandatory owner edge checkpoint. |
| 1.13 terrain override | No region declared; current T4 survey issue remains open. |
| 2.1–2.3 | Held behind mandatory owner edge checkpoint. |
| 3.1–3.13 | Held behind mandatory owner edge checkpoint; no scenery claimed. |
| 4.1–4.5 | Held behind mandatory owner edge checkpoint; no drive/preview published. |

## Final checkpoint result

The final builder wrote a **diagnostic, failed stage** with `--write-on-fail`: the
only remaining numeric failure is the nominal-length comparison, 3589.152 m
versus 3633.934 m (2.258 miles), 1.23% short. The geometry was not stretched and
no gate was relaxed. No package was copied into public/tracks, and no app track
registration, racing line, scenery or driving stage was built.

All edge/profile checks pass: 95.0% / 93.6% of associated left/right observations
within 0.25 m; coverage 81% / 84%; longest gaps 46 / 56 stations; rolling edge
waviness 0.024 / 0.029 m RMS; max profile-column step 0.025 m. Width median is
12.4 m (p5 12.0, p95 14.9). Per-window widths are in `edges_r1/windows.json`.

The initial automatic OSM pit merge incorrectly included the inside T1 apron.
The final config turns that heuristic off and constrains the T1 inner boundary
to the source-confirmed raised red/white kerb (captures and decoded onboard t16).
Continuous yellow kerbs on T1 and T2 exits are explicitly measured with opt-in
yellow-band evidence. The overhead bridge masks the affected left edge readings.

The 2019/2024 T4 banking mismatch remains open even though smoothness gates pass.
The owner's outline review and advice are the next required checkpoint.

Six bridge-repair tests, two yellow-kerb tests and four stage-isolation tests
passed; the parent independently reran all 14 focused tests successfully. The
Sonoma full reproduction was terminated to preserve the user's usage window;
Laguna reproduction was not started. Existing-package byte identity is therefore
not claimed. Both reproductions remain required before any future merge.

Independent final edge_gate rerun by parent exited 0: left/right RMS 0.030 /
0.022 m, max width steps 0.053 / 0.061 m. Exit-width advisories remain at T1
(+1.08 m), T2 (+2.36 m), T11 (+1.99 m); they are shown for owner review.

## Round 7 (27 Oct 2026): stage 3, the scenery

The object manifest, scans and ledgers of the scenery round are in `round7.md`. The coverage gate reads the disposition
lines below (`tools/track/manifest.py`); each is a MISSING inventory row of a kind the gate lets a disposition settle.

### Dispositions (coverage gate, SKILL 3.13)

| kind | side | s (m) | what | source | disposition |
|---|---|---|---|---|---|
| stand | right | 72 | covered grandstand, red roof | onboard:e25u_vjn1uM@26.0 | placed: T1 approach covered stand (the long covered stand 44-51 m right of s 93-183, seen across the run-off from s 72) |
| stand | right | 3530.9 | covered grandstand | onboard:OJaBJz18xEo@128.0 | placed: Main grandstand (covered) (s 3554-3593 right, 31 m out, seen ahead from s 3531) |
| stand | left | 1897.8 | aluminium bleachers | onboard:e25u_vjn1uM@74.0 | placed: T4 bleachers north (s ~1800-1850 left, 40 m out, seen behind from s 1898) |
| building | left | 3425.8 | starter tower | onboard:OJaBJz18xEo@124.0 | placed: Starter tower (s ~3592 left, 45 m out, seen ahead from the T13 exit) |
| building | left | 3495.6 | starter tower | onboard:e25u_vjn1uM@128.0 | placed: Starter tower (s ~3592 left, seen ahead) |
| building | left | 3495.9 | starter tower | onboard:OJaBJz18xEo@2.0 | placed: Starter tower (s ~3592 left, seen ahead) |
| building | left | 3557 | starter tower, 4 storeys | onboard:e25u_vjn1uM@130.0 | placed: Starter tower (s ~3592 left, seen ahead) |
| building | left | 418.9 | hospitality tents / covered stand, red roof | onboard:e25u_vjn1uM@36.0 | rejected: temporary hospitality tents of the IndyCar weekend (360 lap t036 left, 4 Jul 2025: white tents and a red-roofed canopy far across the infield); the 2026 Lemons onboard N837 t018-t020 shows open infield there and no 2026 capture covers the place (the NAIP's white tent roof is not a 2026 source) |
| mast | left | 294.8 | timber utility poles with lines, several | onboard:e25u_vjn1uM@32.0 | placed: timber utility pole (the two poles the 2019 lidar resolves on the T1 inside, s 252 and 366 left, 38-41 m out; c20_s0200-c20_s0280) |
| mast | right | 3557 | scaffold masts with TV cameras / flood lights | onboard:e25u_vjn1uM@130.0 | rejected: temporary TV and flood-light scaffold masts of the IndyCar weekend (360 lap t130 right, Jul 2025); the Apr 2026 Lemons onboard N837 t128 / t004 shows the fence and the grandstand with no scaffold masts |
| station | right | 154.4 | TV camera scaffold tower behind the fence | onboard:e25u_vjn1uM@28.0 | rejected: a temporary TV camera scaffold of the IndyCar weekend (360 lap t028 right, Jul 2025); the Apr 2026 Lemons onboard N837 t008 / t010 shows the fence and the stand with no scaffold |
| station | left | 998.7 | TV camera scaffold | onboard:e25u_vjn1uM@52.0 | rejected: a temporary TV camera scaffold behind the Keyhole boards (360 lap t052 left, Jul 2025); N837 t038 / t040 (Apr 2026) show the board wall with no scaffold behind it |
| station | left | 1337.8 | marshal post / scaffold behind the fence | onboard:e25u_vjn1uM@62.0 | rejected: a bare scaffold tower behind the fence (360 lap t062 left, Jul 2025: scaffold only, no hut); N837 t050 (Apr 2026) shows no structure there |
| station | left | 2147.1 | marshal post "5" | onboard:e25u_vjn1uM@84.0 | rejected: station 5 is a sign post with a temporary pop-up canopy (360 lap t084 left, Jul 2025); N837 t074 (Apr 2026) shows the '5' sign post only, no hut |
| station | left | 1527.4 | marshal post, yellow | onboard:OJaBJz18xEo@54.0 | placed: back-straight tower (yellow, red roof) (s ~1555 left behind the armco, seen ahead in t054) |
