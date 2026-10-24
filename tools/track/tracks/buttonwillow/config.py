"""Buttonwillow Raceway Park in its 24 Hours of Lemons configuration: every per-circuit constant of the track pipeline
(tools/track/build_track.py; format in tools/track/trackcfg.py). Built from the template (tracks/_template/config.py)
by following .claude/skills/build-track/SKILL.md in its order, without logger laps (the team's logger data is Laguna
only): the centre is the painted-road midpoint, the racing line the pure minimum-curvature line. Plain data; nothing here
runs. Paths are relative to tools/track/.

The Lemons loop (stage 0.1): "Button Turrible 2026", 24hoursoflemons.com/race/?id=454, 26-27 Sep 2026 (MyLaps event
3731897, race session 12906863). Layout picture registration.24hoursoflemons.com/userfiles/races/26_buttonwillow.png
(404 on the live server on 20 Oct 2026; read from its Wayback copy web.archive.org/web/20260111111352id_/..., sha1
66affc15b9af2f9d02abc69bc04db22a0618349c; the 2027 event's picture userfiles/races/buttonwillow27.png, race/?id=485, is
the same drawing): eleven numbered turns, start/finish on the straight through the middle of the site with the arrow
pointing east, the pit lane drawn alongside it on the north side from T11 to T1: CLOCKWISE (shoelace on the picture's
turn points: positive area in image coordinates). The 2026 onboards call it "13CW" (Buttonwillow Race #13 clockwise).

STATUS 20 Oct 2026: stage 0 complete; stage 1 stops at the fitted-edge gates (coverage >= 60 %, observations within
0.25 m >= 90 %): Buttonwillow has no painted edge line and its asphalt meets dusty dirt in a ragged edge (run 5: 48-50 %
and 75-78 %). No package. The record and the options are in tools/track/compare/buttonwillow/manifest.md.
"""

# the round-10 kerb zones beside the owner's red (compare/owner_kerbs.py over owner/r10/merged.json on the round-9
# package tools/track/out/bw_r9e, then each matched to the onboard-confirmed stage-3 kerb run it belongs to; stations of
# stations_ref): (side, lo, hi, shift) with shift = the block band's outer limit from his red (m, median over the zone).
# Not placed: the declared runs with no band beside his red (left 538-560, 2837-2843, 3458-3505; right 1161-1182,
# 1294-1299: the blocks lie away from his line) and the detected bands with no onboard-confirmed run (left 1956-1961,
# 3105-3111; right 392-399, 1984-2005, 3672-3678, 3761-3772, 4410-4417: candidates for the owner).
OWNER_KERBS_R10 = [
    ('left', 280, 322, 1.35),   # band +0.05..+1.35 m from his red, strip 0.95 m; run left s 283-322 (onboard-confirmed stage-3 run); c20_s0400, c20_s0450
    ('left', 742, 749, 0.55),   # band +0.25..+0.55 m from his red, strip 0.3 m; run left s 745-767 (onboard-confirmed stage-3 run); c20_s0850, c20_s0900
    ('left', 941, 1004, 0.65),   # band -0.35..+0.65 m from his red, strip 0.65 m; run left s 954-1011 (onboard-confirmed stage-3 run); c20_s1050, c20_s1100
    ('left', 1079, 1109, 0.95),   # band +0.05..+1.00 m from his red, strip 0.8 m; run left s 1089-1116 (onboard-confirmed stage-3 run); c20_s1200, c20_s1250
    ('left', 1192, 1260, 0.95),   # band +0.05..+0.95 m from his red, strip 0.55 m; run left s 1203-1272 (onboard-confirmed stage-3 run); c20_s1300, c20_s1350
    ('left', 1324, 1388, 0.85),   # band -0.10..+0.85 m from his red, strip 0.85 m; run left s 1338-1396 (onboard-confirmed stage-3 run); c20_s1450, c20_s1500
    ('left', 1422, 1472, 0.95),   # band +0.15..+0.95 m from his red, strip 0.8 m; run left s 1449-1479 (onboard-confirmed stage-3 run); c20_s1550, c20_s1600
    ('left', 1528, 1565, 0.85),   # band -0.25..+0.85 m from his red, strip 0.85 m; run left s 1541-1574 (onboard-confirmed stage-3 run); c20_s1650, c20_s1700
    ('left', 1636, 1670, 0.85),   # band -0.15..+0.85 m from his red, strip 0.85 m; run left s 1653-1680 (onboard-confirmed stage-3 run); c20_s1750, c20_s1800
    ('left', 1836, 1844, 0.55),   # band -0.15..+0.55 m from his red, strip 0.55 m; run left s 1843-1851 (onboard-confirmed stage-3 run); c20_s1950
    ('left', 2513, 2531, 0.95),   # band +0.15..+0.95 m from his red, strip 0.85 m; run left s 2539-2544 (onboard-confirmed stage-3 run); c20_s2650
    ('left', 2671, 2734, 1.15),   # band +0.15..+1.15 m from his red, strip 0.98 m; run left s 2689-2746 (onboard-confirmed stage-3 run); c20_s2800, c20_s2850
    ('left', 2989, 3001, 0.7),   # band +0.00..+0.70 m from his red, strip 0.7 m; run left s 3005-3013 (onboard-confirmed stage-3 run); c20_s3100, c20_s3150
    ('left', 3315, 3373, 1.05),   # band -0.05..+1.05 m from his red, strip 1.05 m; run left s 3340-3383 (onboard-confirmed stage-3 run); c20_s3450, c20_s3500
    ('left', 3676, 3747, 0.55),   # band +0.05..+1.25 m from his red, strip 0.75 m; run left s 3691-3760 (onboard-confirmed stage-3 run); c20_s3800, c20_s3850
    ('left', 3818, 3861, 1.25),   # band -0.05..+1.25 m from his red, strip 1.15 m; run left s 3845-3876 (onboard-confirmed stage-3 run); c20_s3950, c20_s4000
    ('left', 3953, 4004, 1.25),   # band +0.05..+1.25 m from his red, strip 1.2 m; run left s 3972-4024 (onboard-confirmed stage-3 run); c20_s4100, c20_s4150
    ('left', 4361, 4395, 1.0),   # band +0.05..+1.00 m from his red, strip 0.93 m; run left s 4381-4406 (onboard-confirmed stage-3 run); c20_s4500
    ('right', 183, 267, 1.25),   # band -0.25..+1.25 m from his red, strip 1.25 m; run right s 188-268 (onboard-confirmed stage-3 run); c20_s0300, c20_s0350
    ('right', 357, 376, 1.15),   # band +0.25..+1.15 m from his red, strip 0.9 m; run right s 360-376 (onboard-confirmed stage-3 run); c20_s0500
    ('right', 408, 427, 0.95),   # band +0.05..+0.95 m from his red, strip 0.9 m; run right s 410-424 (onboard-confirmed stage-3 run); c20_p0840, c20_s0550
    ('right', 583, 609, 1.25),   # band +0.15..+1.25 m from his red, strip 0.82 m; run right s 584-604 (onboard-confirmed stage-3 run); c20_s0700, c20_s0750
    ('right', 1005, 1042, 1.35),   # band +0.25..+1.40 m from his red, strip 1.1 m; run right s 1020-1049 (onboard-confirmed stage-3 run); c20_s1150, c20_s1200
    ('right', 1482, 1504, 1.15),   # band +0.05..+1.15 m from his red, strip 1.1 m; run right s 1495-1515 (onboard-confirmed stage-3 run); c20_s1600, c20_s1650
    ('right', 1768, 1810, 0.8),   # band +0.15..+1.35 m from his red, strip 0.9 m; run right s 1779-1818 (onboard-confirmed stage-3 run); c20_s1900, c20_s1950
    ('right', 1858, 1864, 1.25),   # band +0.25..+1.25 m from his red, strip 0.9 m; run right s 1868-1933 (onboard-confirmed stage-3 run); c20_s2000
    ('right', 2301, 2338, 1.15),   # band +0.25..+1.15 m from his red, strip 1.0 m; run right s 2315-2340 (onboard-confirmed stage-3 run); c20_s2450
    ('right', 2750, 2780, 0.55),   # band -0.25..+0.55 m from his red, strip 0.55 m; run right s 2765-2792 (onboard-confirmed stage-3 run); c20_s2900
    ('right', 3384, 3439, 0.85),   # band -0.05..+0.85 m from his red, strip 0.85 m; run right s 3400-3451 (onboard-confirmed stage-3 run); c20_s3500, c20_s3550
    ('right', 3784, 3796, 1.45),   # band +0.35..+1.45 m from his red, strip 1.1 m; run right s 3794-3810 (onboard-confirmed stage-3 run); c20_s3900
    ('right', 3870, 3922, 1.45),   # band +0.25..+1.55 m from his red, strip 1.25 m; run right s 3894-3935 (onboard-confirmed stage-3 run); c20_s4000, c20_s4050
    ('right', 4013, 4110, 0.85),   # band +0.15..+0.85 m from his red, strip 0.45 m; run right s 4030-4127 (onboard-confirmed stage-3 run); c20_s4150, c20_s4200
    ('right', 4331, 4351, 1.25),   # band +0.15..+1.25 m from his red, strip 1.1 m; run right s 4321-4370 (onboard-confirmed stage-3 run); c20_s4450
    ('right', 4450, 4493, 0.95),   # band +0.05..+0.95 m from his red, strip 0.72 m; run right s 4424-4501 (onboard-confirmed stage-3 run); c20_s4600
]

CONFIG = dict(
    id='buttonwillow',
    name='Buttonwillow Raceway Park',
    direction='cw',                              # the Lemons layout picture: clockwise (module docstring)
    # ---------------------------------------------------------------- stage 0: frame and sources (SKILL 0.1, 0.2)
    origin=(35.4908, -119.5447),                 # lat0, lon0 of the local ENU frame (circuit centre; CONTRACTS section 1)
    osm_bbox=(-119.556, 35.478, -119.530, 35.500),   # W, S, E, N of the OSM API map call (20 Oct 2026)
    osm_file='osm/osm.xml',                      # cached under cache/<id>/
    # The Lemons loop in driving order from the front straight (stage 0.1; OSM 20 Oct 2026). Clockwise drives several
    # ways against their node order ('way:from:to' with from after to). Confirmed on the 2026 Lemons onboard
    # youtube.com/watch?v=7QS2M-HGSI4: its Garmin Catalyst minimap is the GPS trace of the driven lap; an affine fit of the
    # trace (frame t100) against five candidate loops gives OSM -> trace p95 6.3 m (max 50 m, at the Lost Hill / drag
    # strip join) for this loop, against 17 m with the 39224609 loop at T2, 37 m with the drag strip instead of Lost
    # Hill, 46 m with the Dog Leg instead of the Club Corner / Bus Stop / Truck Stop hump, and 64 m with the Sweeper
    # instead of the Star Mazda Turn. The Lemons picture shows the same hump, the Lost Hill bulge and the long north leg.
    loop_ways=[
        '34350797:393994623:393994620',   # front straight (unnamed), west -> east
        '39224614',                       # Sunrise: T1 left, north
        '34351074',                       # Off Ramp: T2 (the hook at the north-east)
        '39224473',                       # I-5: south along the east side
        '39224466',                       # Cotton Corners: T3 / T4
        '39224406',                       # Grapevine: T5, west
        '39224483:469885808:393994724',   # Dog Leg, its east end only
        '34351010',                       # Club Corner: up into the hump
        '39224375',                       # Bus Stop
        '39224371',                       # Truck Stop: down to Riverside
        '39224492:469884764:469885942',   # Riverside: T6 / T7, west then north
        '39224505:469885942:469886349',   # Lost Hill: T8, the western bulge
        '34351305:469886349:394000753',   # Drag Strip, its north end
        '39224620:394000753:393994662',   # Star Mazda Turn: T9 at the top
        '39224510',                       # Esses: T10, south
        '39224519',                       # Sunset: T11 onto the front straight
    ],
    pit_lane_way='Pit / Fire Road',              # OSM 39224587: from the Sunset / Zorros junction along the north side to Off Ramp
    # USGS 3DEP 1 m DEM of CA_SanJoaquin_2021_A21 (UTM 11N, NAVD88; published 20 Jan 2024): the box straddles the
    # 3,930,000 m northing and the 270,000 m easting, so four tiles (read as windows over HTTP)
    dem_tiles=[
        'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_SanJoaquin_2021_A21/TIFF/'
        'USGS_1M_11_x26y394_CA_SanJoaquin_2021_A21.tif',
        'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_SanJoaquin_2021_A21/TIFF/'
        'USGS_1M_11_x26y393_CA_SanJoaquin_2021_A21.tif',
        'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_SanJoaquin_2021_A21/TIFF/'
        'USGS_1M_11_x27y394_CA_SanJoaquin_2021_A21.tif',
        'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_SanJoaquin_2021_A21/TIFF/'
        'USGS_1M_11_x27y393_CA_SanJoaquin_2021_A21.tif',
    ],
    # the DEM's own survey: flown 24 Feb - 22 Mar 2021 (sciencebase 640046fbd34edc0ffaf4c5bb), published 1 Mar 2023;
    # Entwine tiles CA_SanJoaquin_6_2021 (the sub-block over Buttonwillow)
    lidar_ept='https://s3-us-west-2.amazonaws.com/usgs-lidar-public/CA_SanJoaquin_6_2021/',
    lidar_survey='CA_SanJoaquin_2021_A21',
    dem13='https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n36w120/USGS_13_n36w120.tif',
    logger_dir=None,                             # the team's logger analysis, or None (the no-logger path)
    # the timing line: no painted line on the 2026 captures; the timing loop's two saw cuts cross the track directly below
    # the starter's stand on the pit wall (c20_s0150, px x 450; the stand is the scaffold tower on the wall in the pit-lane
    # video ucmXJu5QKFQ 22:19-22:28). The point is where that line crosses the road's centre: round 4 moved it from the
    # first centre (ENU 16.2, -232.9, which sat 4-7 m toward the right edge once the front straight was fitted) to the
    # fitted centre of run 8 (ENU 15.7, -225.7); the line itself is unchanged. The onboard's Catalyst lap line (lap 21
    # starts at 0:05.47; GPS dot at 0:06 at s ~31) lies within 10 m of it.
    start_finish_latlon=(35.4887722, -119.5445271),
    # numbering from the Lemons layout picture (11 turns): the picture's turn circles mapped onto the first centre by an
    # affine fit on T1, T2, T9 and T11 (residual of the others 0-25 m), each anchored at the curvature peak of the
    # picture's direction nearest to it (20 Oct 2026, first centre work/v2): T5 is the right-hander at the end of
    # Grapevine (not the left into Club Corner, which has no peak), T10 the left of the Esses at s ~3823.
    corners=[
        ('T1', None, 'left', None, 35.488998, -119.541433),
        ('T2', None, 'right', None, 35.491670, -119.541540),
        ('T3', None, 'right', None, 35.488712, -119.539278),
        ('T4', None, 'right', None, 35.487701, -119.539421),
        ('T5', None, 'right', None, 35.486712, -119.542282),
        ('T6', None, 'right', None, 35.486314, -119.548485),
        ('T7', None, 'right', None, 35.487341, -119.549927),
        ('T8', None, 'right', None, 35.491136, -119.550774),
        ('T9', 'Star Mazda', 'right', None, 35.496627, -119.548964),
        ('T10', None, 'left', None, 35.493539, -119.548124),
        ('T11', 'Sunset', 'left', None, 35.488787, -119.547978),
    ],
    named_straights=[],
    # Lap length: there is no official figure for this layout to better than ~3 %. The operator's site
    # (buttonwillowraceway.com/track-info/, 20 Oct 2026) gives no length for Race #13 (its map brp-track-map-race-13-
    # outline.png is this loop); Wikipedia says "3.000 mi (4.828 km)", a conversion of a rounded "3.0 mi"; lapmeta.com
    # lists 13CW at 4.43 km and 13CCW at 4.83 km; MyLaps' 3.1 mi is the venue default (Classic track, East + West loops
    # combined, the operator's own figure). Independent measures of THIS loop: the stitched OSM loop 4701 m; the 2026
    # onboard (7QS2M-HGSI4) Catalyst speed readout integrated over lap 21 (2 s steps, trapezoid) 4650 m on the driven
    # line, which runs ~1 % inside the centre. So official_m stays None (no 1 % gate against a rounded figure) and the
    # length is checked against those two in the manifest: the built centre must lie within 1 % of OSM.
    # elevation: the San Joaquin valley floor is flat: the lidar profile spans 3.5 m (z0 76.7 m NAVD88)
    loop_check=dict(n_min=4500, n_max=5100, official_m=None, elev_min=1, elev_max=15),
    captures=dict(                               # clean z20 captures (SKILL 0.3): register_clean.py, one common shift
        z20_dir=None,
        clean_dir='compare/buttonwillow/satellite_clean', clean_index='tiles.json',
        mpp=0.12156,                             # z20 at 35.49 N (Web Mercator: 0.149291 x cos(lat))
        common_shift=None,                       # measured by register_clean.py -> satellite_clean/shift.json
        clean_mask='clean',
        exclude=[],                              # captures off by more than 0.5 m from both neighbours (SKILL 1.2)
    ),
    # recent video and survey sources (SKILL 0.4, 0.5): recorded here and in compare/<id>/inventory/source.json
    sources=dict(
        # round 8: two more onboards (reference only, frames by the headless route, local): the CCW lap and a CW coaching lap
        video_ccw="youtube _7QwJdGQtaE: 'NASA SoCal HPDE 2 - Buttonwillow Classic CCW 4/5/2025 - Session 1' (Fast Car Seats, uploaded 2025-04-07), hood camera, counter-clockwise; used for the infield fence (t138-t140, t1344-t1372), the T2-outside tyre wall (t286 / t288) and kerb faces",
        video_cw_ftd="youtube XIxXIvsDz3s: Full Throttle Driving Academy coaching lap, Catalyst overlay, clockwise (frames t440-t620); used for the T2 concrete patch (t475), kerb faces (t476, t560) and widths",
        onboard=[],                              # recent (2024+) onboard of the Lemons layout: video ids with date and camera
        pit_lane_video=[],                       # recent video that drives the pit lane end to end (pit in, boxes, pit out)
        streetview='compare/buttonwillow/streetview.md',
        lemons_layout='registration.24hoursoflemons.com/userfiles/races/26_buttonwillow.png (race/?id=454, Button Turrible 2026, 26-27 Sep 2026; Wayback 20260111111352): clockwise',
        mylaps='speedhive event 3731897, race session 12906863 (105 cars classified; best 2:15.252 GT Poorty Racing; #619 Anal Corkscrew Probe P15, best 2:29.956, 287 laps)',
        naip='m_3511936_ne_11_060_20220608 (NAIP 8 Jun 2022, 0.6 m)',
    ),
    # ---------------------------------------------------------------- stage 1: geometry (SKILL stage 1)
    stations_ref=(4692, 4697.78),   # the run-20 centre (stations_ref.json): the station numbers below refer to it (SKILL 1.3)
    # the pit-out merge (round 6 / stage 3 pass, 1.10 review item 1): the pit lane comes round the inside of T1 and
    # shares the pavement with the track from ~s 432 to ~527, between two lines of white kerb blocks (the left kerb
    # band ending at s 432, c20_s0500 / c20_p0840; the block line starting at s 527, c20_s0650, sheet
    # edge_sheets/pitout_merge_470-540). There is no painted blend line and no cone on the shared pavement (captures
    # c20_s0600 / c20_s0650; onboard 0:18-0:22, frames t018-t022: one wide asphalt surface). The pipeline's rule put the
    # blend boundary on the OSM pit way's own edge, 1.5-3 m inside the shared pavement (width 7.66 m at 509). The
    # boundary is the straight line joining the two block lines' ends, measured on the captures.
    # the first centre (SKILL 1.2): at T1 exit, T10 and T11 exit the OSM way runs on the paved apron beside the circuit
    # (the dark pavement beyond the white / red / blue block line); the flying lap runs on the pale surface on the other
    # side of the blocks (onboard 0:16-0:22, 2:02-2:08, 2:22-2:28). Knots: points of the OSM first centre with the
    # lateral shift (+ left) of the real pavement's midline, measured on the capture windows with a 2 m ruler across the
    # first centre every 10 m (compare/buttonwillow/stage3_evidence/ruler_t1.png, ruler_t1b.png, ruler_t10.png,
    # ruler_t11.png; midline between the block line and the pale surface's asphalt end). The edges stay fitted.
    # (round 5's centre.pit_merge_line from the block line's end at s 432 is dropped: that block line is the right edge)
    centre=dict(
        # the pit-exit blend line's start (stage 1 key, SKILL Acceptance 6 merge eefd5b3): the pit wall's east end, where
        # the K-rail stops at the crossover past the starter's hut (wall_measure.py --edge left 0-300 on c20_s0250 /
        # c20_s0300, stage3_evidence/cw_wallend.png); the lane joins the track only at s ~384-409 (the T1 exit), so
        # pit_exit_line logs this end as outside the merge stretch and the detected line is unchanged
        pit_exit=dict(wall_end_latlon=(35.4890148, -119.5422713),
                      src='the K-rail east end at the crossover, wall_measure.py on c20_s0250 / c20_s0300 (cw_wallend.png)'),
        # round 10 (23 Oct 2026): ONE whole-lap shift from the owner's midline (SKILL 1.9 "add centre.prior_shift knots
        # from his midline"): the owner drew red on both sides of all 41 round-9 outline windows (owner/r10/merged.json);
        # a knot every 10 first-centre stations where he drew both lines, the shift = his midline (the mean of his two
        # lines) minus the unshifted first centre, interpolated round the loop (periodic). It replaces the five stretch
        # shifts of rounds 2-5 (T1 exit / T10 / T11 rulers, the T2 and T4 owner midlines): his round-10 red supersedes
        # them, and the round-5 T4 drawing (owner/t4_edges.json) lies 2.5-4.9 m off the asphalt his round-10 red follows
        # (p50 / max distance between the two drawings), so its knots started the T4 fit on the wrong pavement.
        prior_shift=[dict(periodic=True, blend=0, knots=[
            (35.4887069, -119.5445201, 7.6), (35.4887137, -119.5444101, 7.59), (35.4887181, -119.5442999, 7.83), (35.4887213, -119.5441897, 8.2),
            (35.4887262, -119.5440795, 8.42), (35.4887341, -119.5439696, 8.22), (35.4887431, -119.5438598, 7.81), (35.4887514, -119.54375, 7.45),
            (35.4887584, -119.54364, 7.35), (35.4887644, -119.5435299, 7.42), (35.4887724, -119.54342, 7.31), (35.4887852, -119.5433109, 6.68),
            (35.4888009, -119.5432022, 5.66), (35.488811, -119.5430927, 5.28), (35.4888097, -119.5429824, 6.26), (35.4888023, -119.5428725, 7.73),
            (35.4888003, -119.5427622, 8.74), (35.4888083, -119.5426524, 8.62), (35.4888226, -119.5425435, 7.61), (35.4888391, -119.542435, 6.36),
            (35.4888568, -119.5423269, 4.92), (35.4888761, -119.5422191, 3.51), (35.4888938, -119.542111, 2.28), (35.4889052, -119.5420016, 1.8),
            (35.4889125, -119.5418916, 1.77), (35.4889233, -119.5417821, 1.37), (35.4889382, -119.5416733, 0.5), (35.4889567, -119.5415654, -0.77),
            (35.4889857, -119.5414611, -1.38), (35.4890308, -119.5413659, -1.83), (35.489089, -119.541282, -1.86), (35.4891552, -119.5412075, -0.99),
            (35.4892277, -119.5411424, 0.24), (35.4893064, -119.5410895, 1.44), (35.4893901, -119.5410498, 2.36), (35.4894769, -119.5410212, 3.18),
            (35.4895652, -119.5410012, 4.21), (35.4896543, -119.540987, 5.8), (35.4897438, -119.5409781, 7.34), (35.4898336, -119.5409745, 9.42),
            (35.4899234, -119.5409765, 9.83), (35.490013, -119.5409837, 12.62), (35.4901023, -119.5409954, 12.28), (35.4901912, -119.5410112, 12.34),
            (35.4902795, -119.5410313, 11.98), (35.4903673, -119.5410549, 11.39), (35.4904547, -119.5410801, 10.69), (35.4905419, -119.5411067, 9.81),
            (35.4906282, -119.5411372, 8.66), (35.4907138, -119.5411707, 7.14), (35.4907997, -119.5412029, 5.72), (35.4908859, -119.5412342, 4.4),
            (35.4909712, -119.5412684, 2.83), (35.4910544, -119.5413102, 1.25), (35.4911326, -119.5413641, 0.88), (35.491206, -119.5414277, 2.06),
            (35.4912799, -119.5414904, 4.43), (35.4913583, -119.5415441, 5.91), (35.4914422, -119.5415832, 7.28), (35.4915308, -119.5415994, 8.0),
            (35.4916189, -119.5415818, 4.61), (35.4916922, -119.5415199, 0.86), (35.4917346, -119.5414237, -1.16), (35.4917449, -119.5413145, -0.99),
            (35.4917344, -119.5412051, -0.34), (35.4917111, -119.5410986, 0.4), (35.4916778, -119.5409962, 0.54), (35.4916352, -119.5408991, 0.16),
            (35.4915834, -119.540809, -0.34), (35.4915262, -119.540724, -0.29), (35.491469, -119.5406389, -0.68), (35.4914113, -119.5405544, -1.92),
            (35.4913447, -119.5404806, -2.79), (35.4912663, -119.5404273, -2.49), (35.4911823, -119.5403881, -1.76), (35.4910981, -119.5403499, -1.69),
            (35.4910144, -119.5403097, -1.76), (35.4909313, -119.540268, -1.87), (35.4908489, -119.5402239, -2.08), (35.4907682, -119.5401757, -2.71),
            (35.4906892, -119.5401231, -3.83), (35.490611, -119.5400688, -5.13), (35.4905315, -119.5400174, -6.13), (35.4904499, -119.5399712, -6.62),
            (35.490367, -119.539929, -6.69), (35.4902832, -119.5398891, -6.52), (35.490199, -119.5398507, -6.2), (35.4901148, -119.5398123, -5.88),
            (35.490031, -119.5397725, -5.73), (35.4899476, -119.5397316, -5.64), (35.4898642, -119.5396904, -5.59), (35.4897808, -119.5396496, -5.52),
            (35.4896973, -119.5396091, -5.42), (35.489614, -119.5395677, -5.37), (35.4895314, -119.5395243, -5.51), (35.4894493, -119.5394794, -5.79),
            (35.4893663, -119.5394373, -5.81), (35.4892808, -119.5394035, -5.06), (35.4891937, -119.5393769, -3.63), (35.4891065, -119.5393503, -2.17),
            (35.48902, -119.5393206, -1.0), (35.4889333, -119.5392916, 0.2), (35.4888452, -119.5392705, 0.84), (35.4887556, -119.5392674, 0.22),
            (35.488668, -119.5392907, -0.95), (35.4885874, -119.5393389, -2.41), (35.4885137, -119.5394018, -3.28), (35.4884421, -119.5394684, -3.81),
            (35.4883684, -119.5395316, -4.76), (35.4882895, -119.539584, -6.64), (35.4882044, -119.5396191, -6.9), (35.4881155, -119.5396336, -4.13),
            (35.4880263, -119.5396233, -0.29), (35.4879424, -119.5395848, 1.2), (35.4878666, -119.5395259, 0.65), (35.4877911, -119.5394662, -0.02),
            (35.487709, -119.5394218, 0.97), (35.4876213, -119.5393987, 2.83), (35.4875316, -119.5393952, 3.27), (35.4874427, -119.5394099, 1.24),
            (35.4873566, -119.5394412, -0.81), (35.4872729, -119.539481, -2.0), (35.4871902, -119.5395241, -2.86), (35.4871094, -119.5395722, -3.21),
            (35.4870313, -119.5396267, -2.94), (35.4869554, -119.5396858, -2.17), (35.4868815, -119.5397484, -1.04), (35.4868097, -119.5398147, 0.45),
            (35.4867433, -119.5398889, 1.27), (35.4866879, -119.5399755, 2.01), (35.4866424, -119.5400707, 1.24), (35.4866025, -119.5401695, -0.95),
            (35.4865714, -119.5402729, -3.43), (35.4865539, -119.5403809, -5.37), (35.4865484, -119.540491, -6.39), (35.4865497, -119.5406013, -6.76),
            (35.4865548, -119.5407115, -6.7), (35.4865621, -119.5408214, -6.43), (35.4865705, -119.5409313, -5.99), (35.4865786, -119.5410411, -5.58),
            (35.4865862, -119.5411511, -5.27), (35.486593, -119.5412611, -5.03), (35.4865989, -119.5413712, -4.83), (35.4866046, -119.5414813, -4.75),
            (35.4866114, -119.5415913, -4.57), (35.4866206, -119.541701, -4.18), (35.486632, -119.5418104, -3.29), (35.4866445, -119.5419197, -2.31),
            (35.4866575, -119.5420289, -1.27), (35.4866723, -119.5421377, -0.09), (35.4866965, -119.5422438, 0.38), (35.4867381, -119.5423412, 0.11),
            (35.4867943, -119.5424272, -0.43), (35.4868546, -119.542509, -0.4), (35.4869132, -119.5425926, -0.26), (35.4869703, -119.5426778, -0.23),
            (35.4870283, -119.542762, -0.02), (35.4870877, -119.5428448, 0.43), (35.4871456, -119.5429291, 0.69), (35.4871994, -119.5430174, 0.37),
            (35.4872514, -119.5431074, -0.18), (35.4873053, -119.5431957, -0.5), (35.4873606, -119.5432826, -0.6), (35.4874131, -119.543372, -1.11),
            (35.4874586, -119.5434671, -3.11), (35.4874945, -119.5435682, -4.08), (35.4875196, -119.543674, -5.1), (35.4875351, -119.5437827, -6.21),
            (35.4875469, -119.5438921, -6.67), (35.4875651, -119.544, -5.74), (35.4875941, -119.5441044, -3.18), (35.487621, -119.5442095, -0.3),
            (35.4876311, -119.544319, 0.74), (35.4876271, -119.5444291, 0.47), (35.4876172, -119.5445388, -0.0), (35.4876056, -119.5446482, -0.1),
            (35.4875969, -119.544758, 0.74), (35.4875923, -119.5448682, 2.29), (35.4875865, -119.5449782, 3.23), (35.4875771, -119.545088, 3.11),
            (35.4875684, -119.5451978, 2.31), (35.4875625, -119.5453079, 1.1), (35.4875562, -119.5454179, -0.73), (35.4875405, -119.5455264, -1.47),
            (35.4875073, -119.5456287, -0.21), (35.4874598, -119.5457222, 3.56), (35.4874035, -119.5458081, 5.91), (35.4873386, -119.5458842, 6.67),
            (35.4872669, -119.5459506, 6.14), (35.4871926, -119.5460125, 4.77), (35.4871179, -119.5460739, 3.17), (35.4870458, -119.5461397, 1.68),
            (35.486979, -119.5462134, 0.84), (35.4869159, -119.5462919, 0.38), (35.4868535, -119.5463713, -0.17), (35.4867916, -119.5464512, -0.78),
            (35.4867319, -119.5465336, -1.16), (35.4866758, -119.5466197, -0.99), (35.4866244, -119.5467102, -0.03), (35.4865803, -119.5468063, 1.41),
            (35.4865475, -119.5469089, 3.1), (35.4865238, -119.5470153, 3.37), (35.4864992, -119.5471214, 2.69), (35.4864701, -119.5472257, 1.43),
            (35.4864435, -119.5473311, 0.43), (35.4864235, -119.5474386, 0.22), (35.4864045, -119.5475464, 0.22), (35.4863847, -119.5476541, 0.23),
            (35.4863673, -119.5477623, 0.47), (35.4863523, -119.5478711, 0.72), (35.4863387, -119.5479801, 0.85), (35.486327, -119.5480895, 0.86),
            (35.4863179, -119.5481992, 0.86), (35.486312, -119.5483093, 0.85), (35.4863108, -119.5484196, 0.63), (35.4863168, -119.5485297, 0.29),
            (35.4863302, -119.5486387, -0.04), (35.4863496, -119.5487464, -0.51), (35.486376, -119.5488519, -0.85), (35.48641, -119.5489539, -0.82),
            (35.4864512, -119.5490519, -0.58), (35.4864991, -119.5491452, -0.06), (35.4865526, -119.5492339, 0.53), (35.4866084, -119.5493203, 0.76),
            (35.4866644, -119.5494066, 0.41), (35.4867222, -119.549491, -0.39), (35.4867845, -119.5495704, -1.14), (35.4868518, -119.5496434, -1.61),
            (35.4869233, -119.5497102, -1.99), (35.4869986, -119.5497703, -2.28), (35.4870781, -119.5498216, -1.96), (35.487161, -119.549864, -1.31),
            (35.487246, -119.5498995, -0.86), (35.4873332, -119.5499259, -0.76), (35.4874223, -119.5499393, -0.62), (35.487512, -119.5499445, -0.85),
            (35.4876016, -119.5499521, -1.95), (35.4876909, -119.549964, -3.47), (35.4877805, -119.5499724, -4.68), (35.4878703, -119.5499736, -5.17),
            (35.4879601, -119.5499695, -5.25), (35.4880497, -119.5499626, -5.06), (35.4881392, -119.5499534, -4.61), (35.4882286, -119.5499418, -3.99),
            (35.4883178, -119.5499289, -3.39), (35.488407, -119.5499161, -2.77), (35.4884963, -119.5499046, -2.3), (35.4885858, -119.5498952, -2.01),
            (35.4886755, -119.549889, -2.0), (35.4887653, -119.5498869, -2.41), (35.4888551, -119.5498901, -3.26), (35.4889446, -119.5498997, -4.75),
            (35.4890333, -119.5499166, -6.66), (35.4891209, -119.5499411, -6.44), (35.4892071, -119.5499718, -4.92), (35.4892921, -119.5500077, -3.8),
            (35.4893759, -119.5500472, -3.21), (35.4894589, -119.5500894, -2.98), (35.4895415, -119.550133, -2.8), (35.4896237, -119.5501773, -2.69),
            (35.4897055, -119.550223, -2.7), (35.4897865, -119.5502708, -2.94), (35.4898679, -119.5503173, -3.05), (35.4899517, -119.550357, -2.55),
            (35.4900368, -119.5503924, -1.54), (35.4901206, -119.5504321, -0.82), (35.4902023, -119.5504778, -0.77), (35.4902836, -119.5505247, -0.93),
            (35.4903654, -119.5505702, -0.94), (35.4904477, -119.5506147, -0.82), (35.4905301, -119.5506585, -0.74), (35.490613, -119.5507009, -0.57),
            (35.4906969, -119.5507402, -0.32), (35.4907824, -119.5507741, -0.17), (35.4908702, -119.5507973, -0.4), (35.4909597, -119.5508047, -0.41),
            (35.4910493, -119.5507971, -0.34), (35.4911371, -119.5507747, -0.19), (35.4912212, -119.5507361, 0.21), (35.4913006, -119.5506846, 0.42),
            (35.4913754, -119.5506236, 0.23), (35.4914469, -119.5505568, -0.31), (35.491519, -119.5504911, -1.41), (35.4915951, -119.5504325, -3.41),
            (35.491674, -119.5503799, -5.26), (35.4917544, -119.5503305, -5.75), (35.4918356, -119.5502834, -4.98), (35.4919167, -119.5502359, -4.05),
            (35.4919957, -119.5501835, -2.64), (35.4920732, -119.5501276, -0.89), (35.4921527, -119.5500764, 0.05), (35.4922352, -119.5500329, 0.26),
            (35.4923185, -119.5499916, 0.19), (35.4924009, -119.5499478, 0.27), (35.4924827, -119.5499021, 0.42), (35.4925647, -119.5498571, 0.53),
            (35.4926461, -119.5498104, 0.78), (35.4927264, -119.5497608, 1.35), (35.4928081, -119.5497152, 1.64), (35.4928939, -119.5496827, 1.3),
            (35.4929827, -119.5496667, 0.6), (35.4930724, -119.5496613, -0.08), (35.4931621, -119.549656, -0.24), (35.4932517, -119.5496485, 0.21),
            (35.4933414, -119.5496415, 0.38), (35.4934311, -119.5496364, 0.3), (35.4935209, -119.5496342, -0.0), (35.4936107, -119.5496341, -0.36),
            (35.4937005, -119.5496325, -0.53), (35.4937903, -119.5496285, -0.51), (35.4938801, -119.5496259, -0.6), (35.4939699, -119.5496264, -0.98),
            (35.4940598, -119.5496262, -1.29), (35.4941496, -119.549623, -1.36), (35.4942393, -119.5496187, -1.32), (35.4943291, -119.5496153, -1.31),
            (35.4944188, -119.5496108, -1.23), (35.4945084, -119.5496021, -0.9), (35.4945978, -119.5495911, -0.29), (35.4946874, -119.5495847, -0.09),
            (35.4947772, -119.5495819, -0.17), (35.4948668, -119.5495738, 0.18), (35.494956, -119.5495606, 1.01), (35.4950456, -119.549554, 1.3),
            (35.4951354, -119.5495572, 0.65), (35.4952251, -119.5495614, -0.07), (35.495315, -119.5495604, -0.33), (35.4954047, -119.5495561, -0.29),
            (35.4954945, -119.5495511, -0.17), (35.495584, -119.5495426, 0.28), (35.4956733, -119.5495311, 0.99), (35.495763, -119.5495247, 1.22),
            (35.4958528, -119.5495253, 0.83), (35.4959426, -119.5495261, 0.4), (35.4960325, -119.5495257, 0.1), (35.4961223, -119.5495281, -0.49),
            (35.4962121, -119.5495301, -1.02), (35.4963016, -119.5495224, -0.63), (35.4963893, -119.5494991, 0.42), (35.4964717, -119.5494556, 0.78),
            (35.4965434, -119.5493896, 0.39), (35.4965981, -119.5493026, 0.05), (35.4966328, -119.5492011, 0.46), (35.4966461, -119.5490923, 0.32),
            (35.4966346, -119.5489833, -0.06), (35.4965972, -119.5488834, -0.43), (35.4965395, -119.5487991, -1.01), (35.4964737, -119.5487241, -1.04),
            (35.4964074, -119.5486497, -0.96), (35.4963408, -119.5485757, -0.85), (35.4962715, -119.5485055, -0.28), (35.4962016, -119.5484362, 0.39),
            (35.496136, -119.5483609, 0.34), (35.4960753, -119.5482796, -0.49), (35.4960128, -119.5482004, -0.97), (35.4959432, -119.5481307, -0.76),
            (35.4958664, -119.5480737, -0.44), (35.4957844, -119.5480287, 0.05), (35.4956997, -119.5479924, 0.46), (35.4956136, -119.5479607, 0.38),
            (35.4955267, -119.5479327, 0.07), (35.4954388, -119.5479103, -0.05), (35.4953499, -119.5478948, -0.01), (35.4952603, -119.5478861, 0.18),
            (35.4951705, -119.5478835, 0.43), (35.4950807, -119.5478846, 0.63), (35.4949909, -119.5478877, 0.17), (35.4949012, -119.5478938, -0.72),
            (35.4948119, -119.5479049, -1.47), (35.4947229, -119.5479203, -2.62), (35.4946339, -119.5479353, -3.89), (35.4945443, -119.5479422, -6.01),
            (35.4944548, -119.5479345, -8.74), (35.4943662, -119.5479161, -11.3), (35.494277, -119.5479037, -11.44), (35.4941874, -119.547909, -8.26),
            (35.4940992, -119.5479297, -4.43), (35.4940121, -119.5479567, -0.83), (35.493925, -119.5479835, 1.65), (35.4938378, -119.54801, 2.04),
            (35.4937515, -119.5480407, 0.77), (35.4936667, -119.5480769, -0.57), (35.4935814, -119.5481113, -2.09), (35.4934938, -119.5481354, -4.62),
            (35.4934046, -119.5481486, -6.59), (35.4933152, -119.5481596, -7.27), (35.4932267, -119.5481778, -5.83), (35.4931394, -119.5482041, -2.71),
            (35.4930523, -119.5482308, -0.19), (35.4929646, -119.5482549, 0.99), (35.4928771, -119.5482796, 1.12), (35.4927903, -119.5483083, 0.41),
            (35.4927061, -119.5483464, -0.45), (35.4926256, -119.5483952, -0.61), (35.4925476, -119.54845, -0.19), (35.4924684, -119.5485019, -0.06),
            (35.4923852, -119.5485436, -1.07), (35.4922995, -119.5485764, -1.94), (35.4922126, -119.5486046, -1.99), (35.4921244, -119.5486252, -1.5),
            (35.4920348, -119.5486296, -1.21), (35.4919454, -119.5486188, -1.06), (35.4918562, -119.548606, -0.59), (35.4917665, -119.5486021, 0.64),
            (35.4916767, -119.548604, 2.25), (35.4915869, -119.5486006, 3.31), (35.4914977, -119.5485876, 3.54), (35.491409, -119.5485701, 3.46),
            (35.4913205, -119.5485514, 3.28), (35.4912325, -119.5485294, 2.78), (35.4911448, -119.5485054, 2.1), (35.4910565, -119.548485, 1.76),
            (35.4909676, -119.5484699, 1.91), (35.4908785, -119.548456, 2.17), (35.4907894, -119.5484413, 2.38), (35.4907006, -119.5484252, 2.44),
            (35.4906128, -119.5484018, 1.81), (35.490526, -119.5483737, 0.73), (35.4904379, -119.5483523, 0.32), (35.4903489, -119.5483366, 0.52),
            (35.49026, -119.5483212, 0.65), (35.4901708, -119.5483083, 1.01), (35.4900813, -119.5482984, 1.64), (35.4899921, -119.5482857, 2.02),
            (35.4899035, -119.5482674, 1.88), (35.4898153, -119.548247, 1.55), (35.4897271, -119.5482258, 1.16), (35.4896393, -119.5482027, 0.58),
            (35.4895512, -119.548181, 0.17), (35.4894622, -119.5481663, 0.6), (35.4893727, -119.5481566, 1.4), (35.4892833, -119.5481459, 1.81),
            (35.4891942, -119.5481319, 1.9), (35.4891055, -119.5481147, 1.73), (35.4890175, -119.5480928, 1.2), (35.4889309, -119.5480636, 0.72),
            (35.4888474, -119.548023, -0.03), (35.4887707, -119.5479659, -1.52), (35.488704, -119.5478922, -2.4), (35.4886483, -119.5478058, -1.06),
            (35.4886036, -119.5477102, 2.01), (35.4885706, -119.5476077, 5.49), (35.4885481, -119.547501, 7.65), (35.4885335, -119.5473921, 9.24),
            (35.4885234, -119.5472825, 10.46), (35.4885162, -119.5471725, 11.58), (35.4885114, -119.5470624, 12.81), (35.4885093, -119.5469521, 13.91),
            (35.4885103, -119.5468418, 14.55), (35.488514, -119.5467315, 14.78), (35.4885207, -119.5466215, 14.68), (35.488532, -119.5465121, 14.11),
            (35.4885482, -119.5464036, 12.93), (35.4885643, -119.5462951, 11.81), (35.4885739, -119.5461854, 11.32), (35.4885758, -119.5460751, 11.87),
            (35.4885769, -119.5459648, 12.7), (35.4885833, -119.5458548, 12.83), (35.4885954, -119.5457455, 12.15), (35.4886105, -119.5456367, 11.26),
            (35.4886266, -119.5455282, 10.12), (35.4886431, -119.5454198, 9.01), (35.4886596, -119.5453113, 7.87), (35.4886745, -119.5452025, 6.86),
            (35.4886837, -119.5450928, 6.52), (35.4886861, -119.5449825, 6.97), (35.4886868, -119.5448722, 7.58), (35.4886904, -119.544762, 7.86),
            (35.4886971, -119.544652, 7.82), (35.4887053, -119.5445421, 7.64),
        ], src="round 10: the owner's midline (owner/r10/merged.json, his red on both sides of the 41 edges_r9 windows) minus the unshifted first centre, every 10 stations (470 knots)")]),
    # the edge fit (SKILL 1.4): defaults, plus the asphalt-end detector tuned to Buttonwillow's pale dusty dirt (20 Oct
    # 2026, eight stretches of the captures: jump 8 / sat 40 / window -2..+2 m hit 81 % of stations, 98 % within 0.25 m
    # of the median over captures; the defaults 65 % / 99 %, and from the NAIP prior they often miss the window)
    # round 3: the -2.0 m inner window let the edge creep inward a little more each refit (run 5: the front straight
    # down to 1-2 m half-widths at s 4524-4560 and 4656-30); back to the detector's -1.2 m
    # report_by_kind / report_width: report-only numbers for the owner's gate decision (no gate reads them); the
    # operator's Classic-track width is 36-55 ft = 10.97-16.76 m (buttonwillowraceway.com/track-info/)
    # mask (round 5): the marshal post's tyre-faced earth mound beside the left edge on the T11 approach (c20_s4400, sheet
    # edge_sheets/step_left4265: the mound stands at s ~4255-4268, 2-4 m off the asphalt) pulled the asphalt-end
    # readings outward there and left a 0.100 m step at 4267 just before the pit-in exemption; its stations' readings
    # are not used (the fit carries the edge across from both sides)
    # lam 60 / huber 0.15 (round 5; defaults 30 / 0.25): on the ragged unpainted edges the readings jump 0.3-0.5 m between
    # the asphalt end and a dust line along the Riverside straight (right 2050-2131, left ~2466; sheets w_right,
    # w_left), which the default spline followed (waviness 0.056 m, steps 0.101-0.105 m); a stiffer spline with a
    # tighter robust loss runs through the middle of them
    spline=dict(lam=60.0, huber=0.15, asphalt_end=dict(jump=7.0, sat_max=40.0, lo=-1.2, hi=2.0), report_by_kind=True, report_width=(10.97, 16.76),
                # the block-line kerb zones' search windows (offsets from the current edge; features below cite the evidence)
                # the owner's traced edges (21 Oct 2026; compare/owner_edges.py from his drawings on capwin frames, the JSON in
                # tracks/buttonwillow/owner/): his red lines dominate the fit in their windows (the 'owner edge' gate holds it);
                # kerb_inside: stations where he drew on the track side of a block line (the extent pass's block runs), moved
                # outward by the kerb width so the strip stays inside the edge
                # round 10 (23 Oct 2026): the owner's red on both sides of every round-9 outline window (41 windows: 38 of 150 m
                # at 0.12 m/px every 125 m, 3 close-ups at 0.06 m/px; compare/edge_draw_page.py strokes rendered onto the
                # windows, compare/owner_edges.py per window into owner/r10/<window>.json, compare/owner_merge.py into
                # owner/r10/merged.json: overlapping windows cross-faded by the distance from each frame's border; the T2
                # runoff left 583-644, where he drew no red ("the round-9 fit is right there"), filled from his round-5 T2
                # drawing owner/t2_edges.json). His red IS the asphalt edge on the track side of every kerb; the kerb is part of
                # the racing surface, so where the captures show a band beside his red (compare/owner_kerbs.py, owner/r10/
                # kerbs.json, each zone an onboard-confirmed scenery.kerbs_declared run) his reading moves out to the band's
                # outer limit (kerb_inside (side, lo, hi, shift), the shift ramped in outside the zone at <= 0.08 m / station,
                # edges_spline.KERB_STEP) and the kit's strip lies between his red and the edge. The whole lap in two
                # entries (one file); the T2 / T4 drawings of round 5 are superseded.
                owner_edges=[
                    dict(file='owner/r10/merged.json', lo=0, hi=2345, kerb_inside=OWNER_KERBS_R10,
                         src="owner round-10 red on the 41 edges_r9 windows (compare/buttonwillow/owner_edges_r10/*_marked.png, local), s 0-2345"),
                    dict(file='owner/r10/merged.json', lo=2346, hi=4691, kerb_inside=OWNER_KERBS_R10,
                         src="owner round-10 red on the 41 edges_r9 windows (compare/buttonwillow/owner_edges_r10/*_marked.png, local), s 2346-4691"),
                ],
                kerb_search=[
                    ('left', 1830, 1856, (-8.0, 1.5), 'the Dog Leg separation block line on the left (round 5 retry): the white blocks 4-7 m inside the fitted left edge, which ran round the Dog Leg branch beyond them (stage3_evidence/dog1843.png on c20_s1900 / c20_s1950; onboard t068)'),
                    ('left', 1198, 1274, (-8.0, 1.5), 'T4-exit left block line s ~1203-1274 (c20_s1300 / c20_s1350; stage3_evidence/gap1215_r32.png, round 5)'),
                     ('right', 1289, 1315, (-4.0, 1.5), 'right block line 1.7 m inside the edge (judge r2 strip list; k22_1286.png on c20_s1400)'),
                     ('right', 574, 606, (-9.0, 1.5), 'T2 hairpin inside block line (judge r2 row 1; capture t2_595.png on c20_s0700 / c20_s0750, orchestra'),
                     ('right', 1160, 1185, (-4.0, 1.5), 'T4 right block line 2 m inside the edge (judge r2 strip list; k22_1175.png on c20_s1300)'),
                     ('right', 1912, 1930, (-4.0, 1.5), 'right block line 2.2 m inside the edge (judge r2 strip list; k22_1920.png on c20_s2050)'),
                     ('left', 1440, 1472, (-4.0, 1.5), 'left block line 1.5-2.75 m inside the edge (judge r2 strip list; k22_1456.png on c20_s1550 / c20_s16'),
                     ('left', 1525, 1566, (-4.0, 1.5), 'T5 left block line 1.8-2.0 m inside the edge (judge r2 strip list; k22_1546.png on c20_s1650 / c20_s'),
                     ('left', 3818, 3868, (-4.0, 1.5), 'T10 exit left block line 1.7-2.3 m inside the edge (judge r2 strip list; k22_3843.png on c20_s3950)'),
                     ('right', 1322, 1376, (-1.5, 6.0), 'warm_end over a wider window (run 29: asphalt_end over -1.2..+6 m crept out into the dirt, 39 m wide): the right asphalt (R-B +9..+16) runs 1.5-4.5 m past the fitted right edge before the warm dirt (R-B +22..+31) at s 1320-1372 (compare/buttonwillow/stage3_evidence/width_profiles.txt, c20_s1450 / c20_s1500): the T4-T5 width under 10.97 m was the edge stopping short'),
                     ('right', 1011, 1037, (-3.0, 1.5), 'T3 exit blocks on the right edge: 10 readings only, the curve 0.3 m outside their outer limit (oc_1020 on c20_s1150); a window that holds the whole band on every capture'),
                     ('right', 1863, 1879, (-3.0, 2.0), "the Dog Leg separation blocks on the right edge: the curve 0.36 m inside their outer limit (oc_1866 on c20_s2000); a window that holds the whole band"),
                     ('right', 355, 432, (-18.0, 1.5), 'T1 exit: the white block line from 4 m inside the right edge at s 361 to the left edge at '),
                     ('left', 528, 556, (-10.0, 1.5), 'block line 2.7-6.6 m inside the left edge at s 540-560 (cw_533); onboard t022 (0:22): red '),
                     ('left', 1076, 1112, (-10.0, 1.5), 'block line 5.4-6.5 m inside the left edge (cw_1086); onboard t044 (0:44): red / white / bl'),
                     ('left', 1318, 1392, (-10.0, 1.5), 'block line 4.6-8.6 m inside the left edge, along the middle of the paved strip (cw_1348); '),
                     ('right', 1760, 1810, (-10.0, 1.5), 'block line 0-5.4 m inside the right edge where the Dog Leg leaves (cw_1751, cw_1824); onbo'),
                     ('left', 3675, 3760, (-12.0, 1.5), 'block line 1.3-1.8 m inside the left edge (c20_s3800); onboard t124 (2:04): red / white / '),
                     ('left', 3948, 4010, (-10.0, 1.5), 'block line 1.3-1.8 m inside the left edge (c20_s4100 / c20_s4150); onboard t132 (2:12): re'),
                     ('right', 4050, 4112, (-10.0, 1.5), 'block line 1.5-5.5 m inside the right edge (c20_s4150 .. c20_s4250); onboard t134 / t136 ('),
                     ('right', 4402, 4492, (-10.0, 1.5), 'block line 5.6-8.0 m inside the right edge (c20_s4500 / c20_s4550); onboard t144 / t146 (2'),
                ],
                mask=[  # (left 4250-4272, the T11-approach station mound, dropped in the first-centre round: on the shifted-centre geometry the
                      # mound stands ~8 m beyond the fitted left edge (stage3_evidence/gap4255.png on c20_s4400) and the mask left a 71-station gap)
                      # stage-3 pass: the T1-exit corner station's tyre-faced mound right beside the right edge (c20_s0650,
                      # sheet edge_sheets/pitout_merge_470-540: the fitted right edge ran through the mound, its roof
                      # 0.4 m beyond the edge in compare/blob_scan.py)
                      ('right', 468, 498, 'c20_s0650: corner station mound beside the right edge at s ~475-492')],
                # round 9 (owner lap 3 note 27): the width-prior edge model (width_model.py). The asphalt-end detector reads
                # the far side of the bleached shoulder (asphalt and dirt within ~18 grey levels on the 2026 captures), so
                # after the fitted method converges the edges are re-placed: kerb anchors at the painted block band's
                # INSIDE line (the owner's convention), the detector's outward bias measured through them and removed,
                # one width per section, the weaker side placed at that width from the stronger. The sections are the
                # lap split at the junctions below (side, lo, hi, kind, evidence); in a junction range the local width is
                # measured and blended into the neighbouring sections over `blend` stations. The ranges are those of
                # gate.exempt (OSM ways leaving the road for 12 m or more, measured with a ray test on the asphalt-end
                # build, each mouth on its capture) plus the T1-exit apron and the owner's traced windows
                # evidence_passes 1 (round 9 run 2 read the evidence a second time around the placed edges: the bias went to
                # ~0 and every section width rose ~0.5 m, the edges back in the shoulder at s 4180 / 4354 / 4475 on the
                # captures; kerb_expect: the band's centre from the edge searched around, -0.45 m on the pass-1 edge)
                width_model=dict(kerb_offs=(-5.0, 1.5), kerb_expect=(-0.45, 0.45), kerb_min_len=6, w_kerb=10.0, w_owner=40.0,
                                 mid_knot=6, mid_lam=300.0, local_half=15, blend=25, anchor_w=20.0, min_obs=15, evidence_passes=1, agree_conf=0.6,
                                 junctions=[
                    ('right', 8, 68, 'mouth', 'OSM 34351026 (infield connector) mouth; c20_s0050 / c20_s0100'),
                    ('right', 125, 185, 'mouth', 'OSM 34351042 (Atlantic) mouth, the front straight crossover; c20_s0200 / c20_s0250'),
                    ('left', 380, 540, 'pit-out', 'the pit lane rejoins on the left after T1 (c20_s0450, c20_s0500, c20_p0840)'),
                    ('both', 480, 695, 'owner', "T2 hairpin: the owner's traced edges (rounds 5 / 10: owner/t2_edges.json, then owner/r10/merged.json; the range 25 stations wider at each end of the round-5 window 505-670 for the blend into the sections), which also cover the outer T2 loop mouth (OSM 39224609, left 593-653)"),
                    ('left', 726, 786, 'mouth', 'OSM 39224609 (the outer T2 loop) mouth; c20_s0800 / c20_s0850'),
                    ('both', 1017, 1181, 'owner', "T4: the owner's traced edges (rounds 5 / 10: owner/t4_edges.json, then owner/r10/merged.json; the round-5 window 1042-1156, 25 stations wider at each end for the blend)"),
                    ('right', 1365, 1435, 'apron', 'the T4-T5 block line ends against the paved apron at s 1387 (stage3_evidence/cw_1348.png on c20_s1450 / c20_s1500)'),
                    ('left', 1380, 1430, 'apron', 'the T4-T5 paved apron, its asphalt end 4.6 m further out (cw_1348.png on c20_s1450 / c20_s1500)'),
                    ('left', 1477, 1537, 'mouth', 'OSM 39224483 (Dog Leg) mouth; c20_s1550 / c20_s1600'),
                    ('right', 1640, 1713, 'mouth', 'OSM 34351042 (Atlantic) and 34351026 (infield connector) mouths; c20_s1750 / c20_s1800'),
                    ('right', 1796, 1862, 'mouth', 'OSM 34351015 (infield connector) and 34350988 (Pacific) mouths, where the Dog Leg leaves (cw_1751, cw_1824 on c20_s1900 / c20_s1950)'),
                    ('left', 1964, 2024, 'mouth', 'OSM 39224483 (Dog Leg) mouth; c20_s2050 / c20_s2100'),
                    ('right', 2516, 2576, 'mouth', 'OSM 34351305 (Drag Strip, south part) mouth; c20_s2600 / c20_s2650'),
                    ('right', 2939, 2999, 'mouth', 'OSM 34351305 (Lost Hill rejoins) mouth; c20_s3050'),
                    ('right', 3202, 3262, 'mouth', 'OSM 34351309 (Sweeper) mouth; c20_s3300'),
                    ('right', 3619, 3679, 'mouth', 'OSM 34351309 (Sweeper) mouth; c20_s3700 / c20_s3750'),
                    ('right', 4108, 4190, 'mouth', 'OSM 34351301 (Zorros Corners) mouth, the paved fillet from s ~4115 (c20_s4250)'),
                    ('left', 4270, 4330, 'pit-in', 'the Pit / Fire Road (OSM 39224587) leaves on the left before T11 (pit-lane video ucmXJu5QKFQ 20:31; c20_s4400)'),
                    ('right', 4572, 4632, 'mouth', 'OSM 34350988 (Pacific) mouth, a front straight crossover; c20_s4650'),
                    ('right', 4637, 4697, 'mouth', 'OSM 34351015 (infield connector) mouth, a front straight crossover; c20_s0000 / c20_s0050'),
                ])),
    # Buttonwillow has no painted edge lines (every 2026 capture and the onboard: asphalt straight to dirt), so the edge
    # is where the dark asphalt ends, everywhere except at kerbs, where it is the kerb's outer limit (SKILL 1.5). The kerb
    # zones come from compare/kerb_detect.py on the asphalt-end build (run 3, 20 Oct 2026: runs with their outer limit
    # 0.3 m or more beyond that edge and 9 m or longer, +-4 stations); they come first because the first matching feature
    # wins. Kind 'kerb_band': the red / white / blue blocks read grey on the captures (kerb_detect colour 'grey'), so the
    # red-only 'kerb' kind found nothing there. Stations are those of the first centre (4692, station 0 at the timing line).
    features=[
        ('right', 574, 606, 'kerb_band', 'block line, search window (-9.0, 1.5): T2 hairpin inside block line (judge r2 row 1; capture t2_595.png on c20_s0700 / c20_s0750, orchestrator windows cw_618_zoom / cw_630; onboard 0:25.3 ahead-right): the fitted right edge ran ~6-7 m beyond the blocks onto the pale paved patch inside the hairpin'),
        ('right', 1160, 1185, 'kerb_band', 'block line, search window (-4.0, 1.5): T4 right block line 2 m inside the edge (judge r2 strip list; k22_1175.png on c20_s1300)'),
        ('right', 1912, 1930, 'kerb_band', 'block line, search window (-4.0, 1.5): right block line 2.2 m inside the edge (judge r2 strip list; k22_1920.png on c20_s2050)'),
        ('left', 1440, 1472, 'kerb_band', 'block line, search window (-4.0, 1.5): left block line 1.5-2.75 m inside the edge (judge r2 strip list; k22_1456.png on c20_s1550 / c20_s1600)'),
        ('left', 1525, 1566, 'kerb_band', 'block line, search window (-4.0, 1.5): T5 left block line 1.8-2.0 m inside the edge (judge r2 strip list; k22_1546.png on c20_s1650 / c20_s1700)'),
        ('left', 3818, 3868, 'kerb_band', 'block line, search window (-4.0, 1.5): T10 exit left block line 1.7-2.3 m inside the edge (judge r2 strip list; k22_3843.png on c20_s3950)'),
        ('right', 1322, 1376, 'warm_end', 'T4-T5 right: grey asphalt (R-B +9..+16) to warm dirt (+22..+31) 1.5-4.5 m past the run-27 edge (stage3_evidence/width_profiles.txt on c20_s1450 / c20_s1500); warm_end does not creep in the dirt'),
        # stage-3 pass (20 Oct 2026): block-line kerbs laid on wider pavement, the paved apron beyond fitted as track by
        # asphalt_end; the edge is the blocks' outer limit (SKILL 1.5), found with a per-zone search window
        ('right', 355, 432, 'kerb_band', 'block line, search window (-18.0, 1.5) (spline.kerb_search): T1 exit: the white block line from 4 m inside the right edge at s 361 to the left edge at s 425 (stage3_evidence/cw_400ov.png, cw_t1raw.png); the flying lap runs west of it with the blocks on its right, converging (onboard 0:16-0:18, s0350 / s0400 / t016 / t018); the dark pavement east of it is a paved apron inside T1'),
        ('left', 528, 556, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 0-2.8 m inside the left edge at s 530-552, where the blocks end (oc_555 on c20_s0650 / c20_s0700: the readings past 552 were the parked cars and the outer-loop junction, median +0.36 m off the curve; first-centre round); onboard t022 (0:22): red / white / blue kerb close left, running ahead'),
        ('left', 1076, 1112, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 5.4-6.5 m inside the left edge (cw_1086); onboard t044 (0:44): red / white / blue kerb on the left through the left-hander'),
        ('left', 1318, 1392, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 4.6-8.6 m inside the left edge, along the middle of the paved strip (cw_1348); onboard t054 (0:54): red / white / blue kerb on the left, the car right of it'),
        ('right', 1760, 1810, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 0-5.4 m inside the right edge where the Dog Leg leaves (cw_1751, cw_1824); onboard t066 (1:06): white / red / blue kerb ahead right'),
        ('left', 3675, 3760, 'kerb_band', 'block line, search window (-12.0, 1.5) (spline.kerb_search): block line 1.3-1.8 m inside the left edge (c20_s3800); onboard t124 (2:04): red / white / blue kerb on the left'),
        ('left', 3948, 4010, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 1.3-1.8 m inside the left edge (c20_s4100 / c20_s4150); onboard t132 (2:12): red / white / blue kerb on the left'),
        ('right', 4050, 4112, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 1.5-5.5 m inside the right edge (c20_s4150 .. c20_s4250); onboard t134 / t136 (2:14-2:16): white / blue kerb on the right'),
        ('right', 4402, 4492, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 5.6-8.0 m inside the right edge (c20_s4500 / c20_s4550); onboard t144 / t146 (2:24-2:26): kerb on the right'),
        ('left', 277, 327, 'kerb_band', 'kerb_detect run s 282-324 off +0.1..+1.0 m (c20_s0400, c20_s0450)'),
        ('left', 356, 389, 'kerb_band', 'kerb_detect run s 362-387 off +0.1..+1.0 m (c20_s0500)'),
        # (left 393-432 dropped in the stage-3 pass: that block line is the RIGHT edge of the pale T1-exit surface, below)
        ('left', 745, 766, 'kerb_band', 'kerb_detect run s 751-764 off +0.3..+0.6 m (c20_s0850, c20_s0900)'),
        ('left', 947, 1017, 'kerb_band', 'kerb_detect run s 954-1016 off -0.2..+0.7 m (c20_s1050, c20_s1100)'),
        ('left', 1198, 1274, 'kerb_band', 'block line, search window (-8.0, 1.5) (spline.kerb_search): kerb_detect runs s 1205-1217 and 1248-1273 (c20_s1300 .. c20_s1400), one continuous block line s ~1203-1274 on c20_s1300 (stage3_evidence/gap1215_r32.png; round 5: with the T4 owner edge the left curve left it for the apron outer boundary 6 m out, a 63-station gap with no reading)'),
        ('left', 1830, 1856, 'kerb_band', 'block line, search window (-8.0, 1.5) (spline.kerb_search): the Dog Leg separation blocks (c20_s1900 / c20_s1950, stage3_evidence/dog1843.png; onboard t068)'),
        ('left', 1641, 1684, 'kerb_band', 'kerb_detect run s 1649-1684 off +0.0..+0.8 m (c20_s1750, c20_s1800)'),
        ('left', 2515, 2542, 'kerb_band', 'kerb_detect run s 2526-2545 off +0.0..+0.8 m (c20_s2650)'),
        ('left', 2671, 2746, 'kerb_band', 'kerb_detect run s 2681-2748 off +0.2..+1.1 m (c20_s2800, c20_s2850)'),
        ('left', 2993, 3013, 'kerb_band', 'kerb_detect run s 3004-3017 off -0.3..+0.5 m (c20_s3100, c20_s3150)'),
        ('left', 3318, 3385, 'kerb_band', 'kerb_detect run s 3330-3389 off +0.1..+1.0 m (c20_s3450, c20_s3500)'),
        ('left', 3458, 3515, 'kerb_band', 'kerb_detect run s 3470-3520 off +0.0..+0.7 m (c20_s3550, c20_s3600)'),
        ('left', 4364, 4394, 'kerb_band', 'kerb_detect run s 4378-4400 off +0.1..+0.9 m (c20_s4500)'),
        # (left 4470-4501 dropped in the first-centre round: those blocks are the RIGHT limit of the T11-exit surface, onboard t146)
        ('right', 189, 273, 'kerb_band', 'kerb_detect run s 194-270 off -0.3..+1.1 m (c20_s0300, c20_s0350)'),
        ('right', 583, 623, 'kerb_band', 'kerb_detect run s 588-621 off -0.4..+0.5 m (c20_s0700, c20_s0750)'),
        ('right', 1011, 1037, 'kerb_band', 'kerb_detect run s 1018-1036 off +0.3..+1.1 m (c20_s1150)'),
        ('right', 1036, 1058, 'kerb_band', 'kerb_detect run s 1042-1056 off +0.4..+1.2 m (c20_s1150)'),
        ('right', 1287, 1317, 'kerb_band', 'kerb_detect run s 1294-1316 off +0.4..+1.0 m (c20_s1400, c20_s1450)'),
        ('right', 1487, 1517, 'kerb_band', 'kerb_detect run s 1495-1517 off -0.1..+0.7 m (c20_s1600, c20_s1650)'),
        ('right', 1800, 1820, 'kerb_band', 'kerb_detect run s 1808-1821 off -1.3..+0.3 m (c20_s1900, c20_s1950)'),
        ('right', 1863, 1879, 'kerb_band', 'kerb_detect run s 1872-1880 off +0.1..+0.7 m (c20_s2000)'),
        ('right', 2305, 2349, 'kerb_band', 'kerb_detect run s 2315-2351 off +0.1..+1.1 m (c20_s2450)'),
        ('right', 2754, 2791, 'kerb_band', 'kerb_detect run s 2764-2794 off -0.4..+0.5 m (c20_s2900)'),
        ('right', 3387, 3450, 'kerb_band', 'kerb_detect run s 3399-3454 off +0.0..+0.9 m (c20_s3500, c20_s3550)'),
        ('right', 3734, 3757, 'kerb_band', 'kerb_detect run s 3747-3762 off +0.0..+1.1 m (c20_s3850)'),
        ('right', 3779, 3807, 'kerb_band', 'kerb_detect run s 3792-3812 off +0.0..+0.9 m (c20_s3900)'),
        ('right', 3874, 3932, 'kerb_band', 'kerb_detect run s 3887-3937 off +0.1..+1.1 m (c20_s4000, c20_s4050)'),
        ('right', 4014, 4054, 'kerb_band', 'kerb_detect run s 4028-4060 off -1.1..+0.3 m (c20_s4150)'),
        ('right', 4303, 4364, 'kerb_band', 'kerb_detect run s 4317-4370 off +0.1..+0.9 m (c20_s4400, c20_s4450)'),
        ('left', 0, 4691, 'asphalt_end', 'no painted edge line at Buttonwillow: asphalt to dirt (captures, onboard)'),
        ('right', 0, 4691, 'asphalt_end', 'no painted edge line at Buttonwillow: asphalt to dirt (captures, onboard)'),
    ],
    # the mouths of the roads the course does not use (OSM ways touching the loop, measured on the asphalt-end build
    # with a ray test: every highway way that leaves the road for 12 m or more): the NAIP prior bulges into each mouth
    # and asphalt_end then finds the far side of the other road, so the prior is interpolated across +-22 stations
    prior=dict(interp=[
        ('left', 1385, 1429, 'the T4-T5 block line ends against the paved apron at s 1387 (c20_s1500): the prior is carried across the step'),
        ('right', 16, 60, 'mouth of OSM 34351026 (infield connector): the prior is carried across it'),
        ('right', 133, 177, 'mouth of OSM 34351042 (Atlantic): the prior is carried across it'),
        ('left', 601, 645, 'mouth of OSM 39224609 (the outer T2 loop): the prior is carried across it'),
        ('left', 734, 778, 'mouth of OSM 39224609 (the outer T2 loop): the prior is carried across it'),
        ('left', 1485, 1529, 'mouth of OSM 39224483 (Dog Leg): the prior is carried across it'),
        ('right', 1648, 1692, 'mouth of OSM 34351042 (Atlantic): the prior is carried across it'),
        ('right', 1661, 1705, 'mouth of OSM 34351026 (infield connector): the prior is carried across it'),
        ('right', 1804, 1848, 'mouth of OSM 34351015 (infield connector): the prior is carried across it'),
        ('right', 1810, 1854, 'mouth of OSM 34350988 (Pacific): the prior is carried across it'),
        ('left', 1972, 2016, 'mouth of OSM 39224483 (Dog Leg): the prior is carried across it'),
        ('right', 2524, 2568, 'mouth of OSM 34351305 (Drag Strip, south part): the prior is carried across it'),
        ('right', 2947, 2991, 'mouth of OSM 34351305 (Drag Strip, south part (Lost Hill rejoins)): the prior is carried across it'),
        ('right', 3210, 3254, 'mouth of OSM 34351309 (Sweeper): the prior is carried across it'),
        ('right', 3627, 3671, 'mouth of OSM 34351309 (Sweeper): the prior is carried across it'),
        ('right', 4112, 4182, 'mouth of OSM 34351301 (Zorros Corners): the prior is carried across it; from 4112 since round 4 (c20_s4250: the paved fillet of the mouth starts at s ~4115)'),
        ('right', 4580, 4624, 'mouth of OSM 34350988 (Pacific): the prior is carried across it'),
        ('right', 4645, 4689, 'mouth of OSM 34351015 (infield connector): the prior is carried across it'),
    ]),
    shapes=[],                                   # measured half-width knots (SKILL 1.4)
    # the front straight from after the pit-wall head (s ~4525) to the T1 kerb (180) is one straight line on both sides
    # on every capture (c20_s4600 .. c20_s0250): left the asphalt's end at the pit-wall median, right asphalt to dirt
    # between the infield crossovers. Declared as a straight fitted to the asphalt-end readings (round 4). Why: run 6's
    # centre never converged, swinging 0.06-0.075 m at stations 39-40 and 166, the mouths of the infield connector
    # 34351026 and Atlantic 34351042 on the right, and its waviness at 61-124 / 150-183 left is the free fit following
    # the gravel median. Round 3's run 7 started this line at 4470, inside the T11 exit curve, and was worse.
    straights=[
        # round 8 (owner lap 2 note 23, "I don't think the front straight is this wide"): the racing surface is the DARK
        # band of constant width; the pale strip between it and the pit-wall K-rail is not racing surface (a paved shoulder,
        # drawn as the runoff zone 'front straight pale strip'). The right (south) edge: the asphalt-to-dirt line, read
        # once; the left: the dark-to-pale tone step (the asphalt_end detector, i.e. the first brightness step outward,
        # read from 7 m inside the old edge at the K-rail median), PARALLEL to the right line (width_shared)
        dict(side='right', fit='asphalt_end', lo=4525, hi=180, join=(4525, 4535), end=180, tol=0.25, once=True,
             detector=dict(jump=8.0, sat_max=40.0, lo=-1.2, hi=2.0),
             why='front straight right: straight asphalt-to-dirt edge between the crossovers (c20_s4600-c20_s0250)'),
        dict(side='left', fit='asphalt_end', lo=4525, hi=180, join=(4525, 4535), end=180, tol=0.25, once=True, width_shared=True,
             detector=dict(jump=8.0, sat_max=40.0, lo=-7.0, hi=0.3),
             why='front straight left: the dark / pale tone step, parallel to the right edge (owner lap 2 note 23; c20_s4600-c20_s0250)'),
        # Sunset (round 8, owner lap 2 notes 6 / 8: "Sunset doesn't have this bulge. It's pretty straight on either side",
        # both edges drawn straight on his map from past the Zorro's Corners mouth to the West Pit In/Out junction):
        # straight on both sides from the downstream end of the mouth exemption (4190) to before the pit-in split
        # (current s ~4290 = config 4279), measured on c20_s4250 / c20_s4300 / c20_s4350 (stage3_evidence/sunset_r8.png).
        # RANSAC over the asphalt-end readings: the 4230-4247 right readings (current 4241-4258: lighter, rutted dirt
        # beside the asphalt, no structure) and the left bay at 4241-4270 (the T11-approach station mound area, 2-8 m
        # off the asphalt) fall outside the line
        dict(side='left', fit='asphalt_end', lo=4192, hi=4276, join=(4192, 4202), end=4276, tol=0.25, once=True,
             detector=dict(jump=8.0, sat_max=40.0, lo=-3.5, hi=0.3),   # read once (`once`), from 3.5 m inside the edge outward: the first asphalt end, not the rutted dirt beyond the bulge (run 80 with (-1.2, 2.0) refit after refit: 19 m wide; run 82 with (-1.5, 0.6) once: 16.3 m)
             why='Sunset left: straight asphalt-to-dirt edge, owner lap 2 (c20_s4250-c20_s4350)'),
        dict(side='right', fit='asphalt_end', lo=4192, hi=4276, join=(4192, 4202), end=4276, tol=0.25, once=True,
             detector=dict(jump=8.0, sat_max=40.0, lo=-3.5, hi=0.3),   # read once (`once`), from 3.5 m inside the edge outward: the first asphalt end, not the rutted dirt beyond the bulge (run 80 with (-1.2, 2.0) refit after refit: 19 m wide; run 82 with (-1.5, 0.6) once: 16.3 m)
             why='Sunset right: straight dark-asphalt edge, owner lap 2 (c20_s4250-c20_s4350)'),
        # the drag-strip leg toward T9 (round 8, owner lap 2 note 20: a straight strip of constant width; the fit wandered
        # 11.1-16.5 m onto the pale dirt beside it): straight on both sides from where the strip's full width begins past
        # the T8 rejoin (c20_s3050: current s ~3030) to the T9 entry (c20_s3400 / c20_s3450: the curve starts ~3385),
        # stage3_evidence/drag_r8.jpg
        dict(side='left', fit='asphalt_end', lo=3022, hi=3374, join=(3022, 3032), end=3374, tol=0.25, once=True,
             detector=dict(jump=8.0, sat_max=40.0, lo=-3.5, hi=0.3),
             why='drag strip left: straight asphalt edge, owner lap 2 note 20 (c20_s3050-c20_s3400)'),
        dict(side='right', fit='asphalt_end', lo=3022, hi=3374, join=(3022, 3032), end=3374, tol=0.25, once=True, width_shared=True,   # owner note 21: one width end to end
             detector=dict(jump=8.0, sat_max=40.0, lo=-3.5, hi=0.3),
             why='drag strip right: straight asphalt edge, owner lap 2 note 20 (c20_s3050-c20_s3400)'),
    ],
    repave_fixes=[],                             # only where recent footage contradicts the survey (SKILL 1.6)
    gate=dict(exempt=[
        ('right', 1365, 1435, "round 8: from 1365 (was 1370): with the front-straight / Sunset / drag-strip straights the stations moved and the same swing reached 1368 (run 84: 0.101 m at current 1377 = config 1368; the same apron step on cw_1348.png); mirror of the left exemption 1380-1430: as the left edge steps out to the T4-T5 apron at the block line's end (s 1387, stage3_evidence/cw_1348.png on c20_s1450 / c20_s1500) the centre and its normals swing, so the right half-width changes 0.17 m per station with no feature on the right edge; the world-continuity gate on the right edge polyline is the physical check and passes; junction, real"),
        ('left', 1380, 1430, "the T4-T5 block line ends at s 1387 against the paved apron, whose asphalt end runs 4.6 m further out (stage3_evidence/cw_1348.png on c20_s1450 / c20_s1500); the edge steps out like a road mouth; junction, real"),
        ('right', 8, 68, 'mouth of OSM 34351026 (infield connector); junction, real'),
        ('right', 125, 185, 'mouth of OSM 34351042 (Atlantic); junction, real'),
        ('left', 593, 653, 'mouth of OSM 39224609 (the outer T2 loop); junction, real'),
        ('left', 726, 786, 'mouth of OSM 39224609 (the outer T2 loop); junction, real'),
        ('left', 1477, 1537, 'mouth of OSM 39224483 (Dog Leg); junction, real'),
        ('right', 1640, 1700, 'mouth of OSM 34351042 (Atlantic); junction, real'),
        ('right', 1653, 1713, 'mouth of OSM 34351026 (infield connector); junction, real'),
        ('right', 1796, 1856, 'mouth of OSM 34351015 (infield connector); junction, real'),
        ('right', 1802, 1862, 'mouth of OSM 34350988 (Pacific); junction, real'),
        ('left', 1964, 2024, 'mouth of OSM 39224483 (Dog Leg); junction, real'),
        ('right', 2516, 2576, 'mouth of OSM 34351305 (Drag Strip, south part); junction, real'),
        ('right', 2939, 2999, 'mouth of OSM 34351305 (Drag Strip, south part (Lost Hill rejoins)); junction, real'),
        ('right', 3202, 3262, 'mouth of OSM 34351309 (Sweeper); junction, real'),
        ('right', 3619, 3679, 'mouth of OSM 34351309 (Sweeper); junction, real'),
        ('right', 4108, 4190, 'mouth of OSM 34351301 (Zorros Corners); junction, real. Round 4: c20_s4250 (sheet edge_sheets/step_right4124) shows the paved fillet of the mouth starting at s ~4115 on the right, so the range starts there (was 4130, from the OSM node +-30)'),
        ('right', 4572, 4632, 'mouth of OSM 34350988 (Pacific); junction, real'),
        ('right', 4637, 4697, 'mouth of OSM 34351015 (infield connector); junction, real'),
        ('left', 4270, 4330, 'pit-in: the Pit / Fire Road (OSM 39224587) leaves on the left before T11 (pit-lane video ucmXJu5QKFQ 20:31); junction, real'),
        ('left', 380, 540, 'pit-out: the pit lane rejoins on the left after T1 (c20_s0450, c20_s0500, c20_p0840); junction, real'),
    ]),
    # ---------------------------------------------------------------- stage 2 (SKILL stage 2)
    ghosts=dict(),
    # ---------------------------------------------------------------- stage 3: scenery FROM EVIDENCE ONLY (stage-3 pass,
    # 20 Oct 2026). Every object names its source: a clean z20 capture c20_..., an onboard time / frame of 7QS2M-HGSI4
    # (t###), the pit-lane video ucmXJu5QKFQ, OSM or the lidar. The record is compare/buttonwillow/manifest.md (with its
    # step, barrier, station, furniture and logo ledgers). No rule objects: no brake, turn or distance boards, no flag
    # stand, no rule pit wall (the onboard shows none of them).
    scenery=dict(
        # round 10 (23 Oct 2026, stage-3 evidence, read by no builder yet): the junction mouths the owner closed with red on
        # the round-9 outline windows (compare/owner_mouths.py over owner/r10/merged.json: two contacts of his green with
        # his red on one side and his red between them). Each is the course boundary there and, unless cones=False, a cone
        # line ON his red (cone colour, size and spacing from the footage in the scenery pass, SKILL 3.5 / 3.8; the line
        # replaces any offset-from-edge cone rule). Stations of stations_ref; line_latlon one point per ~2 m.
        owner_mouths_r10=[
            dict(side='left', lo=29, hi=41, kind='red across', cones=True, width_m=12.34,
                 src="his red across the mouth: the course boundary and a cone line; no declared junction (a paddock / pit-road opening on his green)",
                 line_latlon=[(35.4888471, -119.5442179), (35.4888487, -119.5441955), (35.48885, -119.544173), (35.4888512, -119.5441503), (35.4888527, -119.5441276), (35.4888541, -119.5441049), (35.4888555, -119.544082)]),
            dict(side='left', lo=206, hi=213, kind='red across', cones=True, width_m=6.05,
                 src="his red across the mouth: the course boundary and a cone line; no declared junction (a paddock / pit-road opening on his green)",
                 line_latlon=[(35.4889591, -119.5422604), (35.4889612, -119.5422383), (35.4889623, -119.5422161), (35.4889639, -119.542194)]),
            dict(side='left', lo=634, hi=636, kind='kink', cones=True, width_m=18.89,
                 src="the T2 runoff (owner: 'no mans land', drivers use it; no red across it): cones only across the alternative section's mouth, from the kink of his green to his other green line; no declared junction (a paddock / pit-road opening on his green)",
                 line_latlon=[(35.4917879, -119.5412307), (35.4918048, -119.541241), (35.4918217, -119.5412513), (35.4918386, -119.5412616), (35.4918555, -119.5412719), (35.4918724, -119.5412822), (35.4918892, -119.5412925), (35.4919061, -119.5413028), (35.491923, -119.5413131), (35.4919399, -119.5413234)]),
            dict(side='left', lo=693, hi=734, kind='red across', cones=True, width_m=42.12,
                 src="his red across the mouth: the course boundary and a cone line; owner T2 hairpin: the owner's traced edges (owner/t2_edges.json, w; mouth OSM 39224609 (the outer T2 loop) mouth; c20_s0800 / c20_s085",
                 line_latlon=[(35.4915255, -119.5406303), (35.4915133, -119.5406132), (35.4915004, -119.5405967), (35.4914866, -119.5405812), (35.4914731, -119.5405651), (35.491459, -119.5405496), (35.4914445, -119.5405346), (35.4914297, -119.5405199), (35.4914148, -119.540505), (35.4913995, -119.5404907), (35.491384, -119.5404767), (35.4913681, -119.5404631), (35.4913523, -119.5404495), (35.4913355, -119.5404375), (35.4913188, -119.5404256), (35.4913021, -119.5404137), (35.4912853, -119.5404021), (35.4912682, -119.5403914), (35.491251, -119.5403812), (35.4912337, -119.5403718), (35.4912163, -119.5403626)]),
            dict(side='left', lo=1494, hi=1514, kind='red across', cones=True, width_m=22.2,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 39224483 (Dog Leg) mouth; c20_s1550 / c20_s1600",
                 line_latlon=[(35.4866364, -119.5422303), (35.4866426, -119.5422542), (35.4866497, -119.5422777), (35.4866578, -119.5423008), (35.4866666, -119.5423234), (35.486676, -119.5423457), (35.4866866, -119.5423668), (35.4866977, -119.5423874), (35.4867089, -119.5424076), (35.4867212, -119.5424266), (35.486736, -119.5424425)]),
            dict(side='left', lo=1960, hi=1993, kind='red across', cones=True, width_m=32.9,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 39224483 (Dog Leg) mouth; c20_s2050 / c20_s2100",
                 line_latlon=[(35.4866818, -119.5465308), (35.4866701, -119.5465467), (35.4866584, -119.5465626), (35.4866469, -119.5465789), (35.4866351, -119.5465949), (35.4866232, -119.5466112), (35.4866109, -119.5466272), (35.4865985, -119.5466436), (35.4865856, -119.5466596), (35.4865725, -119.5466758), (35.4865597, -119.5466927), (35.4865488, -119.546712), (35.4865381, -119.5467316), (35.486527, -119.5467511), (35.4865159, -119.5467708), (35.4865049, -119.5467908), (35.4864939, -119.546811)]),
            dict(side='left', lo=4270, hi=4304, kind='red across', cones=False, width_m=34.36,
                 src="his red across the mouth: the course boundary and a cone line; pit-in the Pit / Fire Road (OSM 39224587) leaves on the left before; the pit entry: the Pit / Fire Road leaves on the left before T11 and the cars drive into it (pit-lane video ucmXJu5QKFQ 20:31); his red here is the course edge, no cones",
                 line_latlon=[(35.4896494, -119.5481346), (35.4896317, -119.548131), (35.4896139, -119.5481277), (35.4895961, -119.5481241), (35.4895782, -119.5481211), (35.4895603, -119.5481173), (35.4895424, -119.5481134), (35.4895245, -119.5481094), (35.4895065, -119.5481052), (35.4894886, -119.5481011), (35.4894706, -119.5480971), (35.4894525, -119.5480932), (35.4894346, -119.5480893), (35.4894166, -119.5480855), (35.4893986, -119.5480818), (35.4893807, -119.5480781), (35.4893628, -119.5480746), (35.489345, -119.5480714)]),
            dict(side='left', lo=4475, hi=4528, kind='red across', cones=True, width_m=50.63,
                 src="his red across the mouth: the course boundary and a cone line; no declared junction (a paddock / pit-road opening on his green)",
                 line_latlon=[(35.4886933, -119.5469025), (35.4886945, -119.5468805), (35.4886956, -119.5468583), (35.4886967, -119.546836), (35.488698, -119.5468136), (35.4886996, -119.5467912), (35.4887009, -119.5467687), (35.488702, -119.5467461), (35.4887031, -119.5467236), (35.4887043, -119.5467009), (35.4887062, -119.5466784), (35.4887074, -119.5466558), (35.4887085, -119.5466332), (35.4887096, -119.5466107), (35.4887107, -119.5465882), (35.4887118, -119.5465657), (35.4887139, -119.5465433), (35.488715, -119.5465211), (35.4887161, -119.5464988), (35.4887171, -119.5464767), (35.4887182, -119.5464546), (35.4887193, -119.5464326), (35.4887214, -119.5464107), (35.4887225, -119.5463888), (35.4887236, -119.546367), (35.4887247, -119.5463452)]),
            dict(side='left', lo=4655, hi=4669, kind='red across', cones=True, width_m=14.18,
                 src="his red across the mouth: the course boundary and a cone line; no declared junction (a paddock / pit-road opening on his green)",
                 line_latlon=[(35.4888061, -119.5449387), (35.4888076, -119.5449165), (35.4888091, -119.5448943), (35.4888102, -119.5448719), (35.4888112, -119.5448496), (35.4888125, -119.5448273), (35.488814, -119.544805), (35.4888151, -119.5447827)]),
            dict(side='right', lo=30, hi=40, kind='red across', cones=True, width_m=9.83,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351026 (infield connector) mouth; c20_s0050 / c20_s010",
                 line_latlon=[(35.4887414, -119.544185), (35.4887429, -119.5441632), (35.4887443, -119.5441414), (35.4887456, -119.5441197), (35.4887466, -119.5440982), (35.488749, -119.5440769)]),
            dict(side='right', lo=154, hi=186, kind='red across', cones=True, width_m=32.1,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351042 (Atlantic) mouth, the front straight crossover;",
                 line_latlon=[(35.4888192, -119.542822), (35.4888201, -119.5427998), (35.4888218, -119.5427778), (35.4888232, -119.5427557), (35.4888244, -119.5427336), (35.4888259, -119.5427116), (35.4888274, -119.5426895), (35.4888287, -119.5426674), (35.48883, -119.5426453), (35.4888314, -119.5426232), (35.4888329, -119.5426011), (35.4888337, -119.542579), (35.4888348, -119.5425568), (35.488836, -119.5425348), (35.4888369, -119.5425127), (35.4888378, -119.5424906), (35.4888392, -119.5424687)]),
            dict(side='right', lo=1643, hi=1677, kind='red across', cones=True, width_m=35.85,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351042 (Atlantic) and 34351026 (infield connector) mou",
                 line_latlon=[(35.487551, -119.5434622), (35.4875597, -119.5434828), (35.4875684, -119.5435035), (35.4875764, -119.5435246), (35.4875843, -119.5435459), (35.4875918, -119.5435673), (35.4875989, -119.5435891), (35.4876057, -119.543611), (35.4876125, -119.5436329), (35.4876183, -119.5436552), (35.4876241, -119.5436776), (35.4876299, -119.5437), (35.4876346, -119.5437226), (35.4876394, -119.5437454), (35.4876442, -119.543768), (35.487648, -119.5437908), (35.4876521, -119.5438135), (35.4876552, -119.5438364)]),
            dict(side='right', lo=1811, hi=1835, kind='red across', cones=True, width_m=29.24,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351015 (infield connector) and 34350988 (Pacific) mout",
                 line_latlon=[(35.4876056, -119.5453206), (35.4876104, -119.5453434), (35.4876146, -119.5453668), (35.4876172, -119.545391), (35.4876193, -119.5454157), (35.4876196, -119.545441), (35.4876184, -119.5454665), (35.4876158, -119.5454923), (35.4876123, -119.5455182), (35.487607, -119.5455438), (35.4876003, -119.5455691), (35.4875919, -119.5455936), (35.4875822, -119.5456175), (35.4875714, -119.5456405)]),
            dict(side='right', lo=2524, hi=2551, kind='red across', cones=True, width_m=29.58,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351305 (Drag Strip, south part) mouth; c20_s2600 / c20",
                 line_latlon=[(35.4891096, -119.5497892), (35.4891279, -119.5497995), (35.4891462, -119.5498093), (35.4891641, -119.5498193), (35.4891819, -119.549829), (35.4891994, -119.5498391), (35.4892168, -119.549849), (35.4892341, -119.5498587), (35.4892513, -119.5498684), (35.4892682, -119.5498783), (35.489285, -119.5498881), (35.4893017, -119.5498976), (35.4893181, -119.5499075), (35.4893344, -119.5499171), (35.4893501, -119.5499277)]),
            dict(side='right', lo=2963, hi=3006, kind='red across', cones=True, width_m=43.46,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351305 (Lost Hill rejoins) mouth; c20_s3050",
                 line_latlon=[(35.4926625, -119.5497441), (35.4926793, -119.5497352), (35.4926961, -119.5497263), (35.492713, -119.5497173), (35.49273, -119.5497084), (35.4927469, -119.5496989), (35.4927643, -119.5496907), (35.4927817, -119.5496824), (35.4927994, -119.549675), (35.4928172, -119.5496676), (35.4928351, -119.5496608), (35.4928531, -119.5496541), (35.492871, -119.5496472), (35.4928891, -119.5496411), (35.4929073, -119.5496354), (35.4929257, -119.5496305), (35.492944, -119.5496253), (35.4929624, -119.5496209), (35.4929808, -119.5496163), (35.4929992, -119.549612), (35.4930176, -119.5496082), (35.4930362, -119.5496053)]),
            dict(side='right', lo=3216, hi=3240, kind='red across', cones=True, width_m=24.09,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351309 (Sweeper) mouth; c20_s3300",
                 line_latlon=[(35.4949295, -119.5495091), (35.4949476, -119.5495089), (35.4949657, -119.5495083), (35.4949837, -119.5495075), (35.4950018, -119.549507), (35.4950198, -119.5495056), (35.4950379, -119.5495056), (35.4950559, -119.5495043), (35.4950739, -119.5495037), (35.4950919, -119.5495035), (35.4951099, -119.5495023), (35.4951279, -119.5495011), (35.4951458, -119.5495004)]),
            dict(side='right', lo=3653, hi=3673, kind='red across', cones=True, width_m=19.39,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351309 (Sweeper) mouth; c20_s3700 / c20_s3750",
                 line_latlon=[(35.4950424, -119.5479404), (35.4950252, -119.5479434), (35.4950079, -119.547946), (35.4949908, -119.5479491), (35.4949735, -119.547952), (35.4949563, -119.547955), (35.4949391, -119.5479585), (35.4949219, -119.5479619), (35.4949047, -119.5479648), (35.4948873, -119.547968), (35.49487, -119.5479711)]),
            dict(side='right', lo=4152, hi=4165, kind='red across', cones=True, width_m=12.08,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351301 (Zorros Corners) mouth, the paved fillet from s",
                 line_latlon=[(35.4906843, -119.5484558), (35.4906665, -119.5484528), (35.4906485, -119.5484496), (35.4906306, -119.5484463), (35.4906128, -119.548443), (35.4905948, -119.5484398), (35.490577, -119.5484366)]),
            dict(side='right', lo=4571, hi=4599, kind='red across', cones=True, width_m=28.09,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34350988 (Pacific) mouth, a front straight crossover; c2",
                 line_latlon=[(35.4886451, -119.5458555), (35.4886462, -119.5458334), (35.4886475, -119.5458113), (35.4886492, -119.5457893), (35.4886503, -119.5457672), (35.4886516, -119.5457451), (35.4886527, -119.545723), (35.4886538, -119.5457009), (35.4886548, -119.5456788), (35.488656, -119.5456567), (35.4886572, -119.5456346), (35.4886589, -119.5456126), (35.4886602, -119.5455905), (35.4886613, -119.5455684), (35.4886613, -119.5455463)]),
            dict(side='right', lo=4659, hi=4669, kind='red across', cones=True, width_m=9.98,
                 src="his red across the mouth: the course boundary and a cone line; mouth OSM 34351015 (infield connector) mouth, a front straight cro",
                 line_latlon=[(35.4886992, -119.5448841), (35.4887003, -119.5448621), (35.4887015, -119.5448401), (35.4887032, -119.5448182), (35.4887045, -119.5447962), (35.4887058, -119.5447743)]),
        ],
        brake_board_corners=[],                  # none in the onboard (t000-t158): no 3-2-1 boards before any corner
        corner_boards=False,                     # no turn-number boards in the onboard
        flagstand=False,                         # the starter's stand is placed as a station (marshal_posts), not by rule
        pit_wall=dict(rule=False),
        # kerbs: flat painted concrete beyond the asphalt edge, blocks of red / white / blue / white (onboard t014, t018,
        # t044, t116: blue, white, red, white, ~1.0 m each; the block pair period on the captures 1.82-2.27 m,
        # compare round 3), the band ~0.9 m across (kerb_detect offsets); no raised profile (the onboard shows the car
        # riding over them flat; no face at the asphalt joint on t014); no green after-kerb paint
        # round 8, the owner's kerb-height decision (lap 2 notes 1-3, 19, 22): "Most Buttonwillow kerbs are not just flat
        # extensions of the pavement"; raised by default unless a frame shows flat: 10 cm, 0.15 m face, 0.30 m back on every
        # run ('default raised, no resolving frame': the 2021 lidar does not resolve kerb tops, stage3_evidence/
        # kerb_heights_lidar_r8.json; the closest frames, t116 and the third video's t476 / t560, show faces but no
        # measurable height); the T9 apex keeps its measured 6 cm (t114, its own profile); widths per run from the capture band
        kerb=dict(width=0.9, stripe_m=1.0, colors=['#b8433a', '#dedbd2'], profile=dict(height=0.10, face=0.15, back=0.30),
                  palettes={'rwb': ['#c4463b', '#e2dfd6', '#4a7ccc'], 'wb': ['#4a7ccc', '#e2dfd6']}, require_colour_src=True),
        # kerb runs: see kerbs_declared below (round 5; the round-4 pieces of <= 10 m each with its own offset are gone)
        kerbs_declared=[
            # kerb RUNS (round 5, the owner's lap 1: "a lot of weird, disjointed kerbs"): one run per block line from the
            # extent pass on the round-5 edges (tools: the band reader's per-station outer limits, the band centre 0.45 m
            # inside; build_scenery.kerb_run smooths the offset over ~10 m and publishes one strip with per-station
            # offsets, max step gated at kerb.run_max_step); the round-4 strips (161 pieces of 10 m) are replaced
            dict(side='left', line_latlon=[(35.4890403, -119.5414453), (35.489049, -119.5414293), (35.4890564, -119.5414125), (35.489065, -119.5413966), (35.4890742, -119.5413809), (35.489084, -119.5413657), (35.4890949, -119.5413515), (35.4891061, -119.5413376), (35.4891176, -119.5413238), (35.4891298, -119.5413108), (35.4891421, -119.5412977), (35.489155, -119.5412852), (35.4891683, -119.5412732), (35.4891817, -119.5412613), (35.4891954, -119.5412497), (35.4892095, -119.5412387), (35.4892223, -119.541225), (35.4892376, -119.5412161), (35.4892517, -119.541205), (35.4892675, -119.5411977), (35.4892752, -119.5411936)], colors='rwb', name='run left s 283-322', width=0.5,   # band width 0.52 m (p25-p75 0.45-0.52, 10 readings on the clean captures, round 8)
               
                 colour_src='t014.jpg (red / white / blue; inventory row s 300 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s0400 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4910984, -119.5414236), (35.4911112, -119.5414352), (35.4911238, -119.5414477), (35.4911365, -119.5414604), (35.4911478, -119.5414756), (35.4911597, -119.5414904), (35.4911706, -119.541507), (35.4911768, -119.5415146), (35.4911959, -119.5415378), (35.4912087, -119.5415538), (35.491222, -119.5415698), (35.4912358, -119.5415855)], colors='rwb', name='run left s 536-549', width=0.6,   # band width 0.6 m (p25-p75 0.47-0.8, 16 readings on the clean captures, round 8)
               
                 colour_src='t022.jpg (red / white / blue; inventory row s 531 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s0650 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; extended to s ~558 (judge r5 fwd_01 550 L): c20_s0650 shows the block line continuing ~9 m past the end of the band reader, at the last offset of the run'),
            dict(side='left', line_latlon=[(35.4911807, -119.5403341), (35.4911631, -119.5403277), (35.4911454, -119.540322), (35.4911278, -119.5403164), (35.491111, -119.5403087), (35.4910936, -119.5403031), (35.4910769, -119.5402952), (35.4910609, -119.5402857), (35.491044, -119.5402789), (35.4910266, -119.5402737), (35.4910097, -119.5402667), (35.4909928, -119.54026)], colors='rwb', name='run left s 745-767', width=1.05,   # band width 1.04 m (p25-p75 0.75-1.17, 24 readings on the clean captures, round 8)
               
                 colour_src='t032.jpg (white / red; inventory row s 738 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s0900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4894373, -119.539475), (35.4894211, -119.5394653), (35.4894049, -119.5394555), (35.489388, -119.5394477), (35.4893709, -119.5394405), (35.4893547, -119.5394305), (35.4893381, -119.5394221), (35.4893211, -119.5394146), (35.4893047, -119.5394057), (35.4892881, -119.5393974), (35.4892715, -119.5393891), (35.4892549, -119.5393809), (35.4892384, -119.5393727), (35.4892219, -119.5393644), (35.4892055, -119.5393562), (35.4891889, -119.5393484), (35.4891724, -119.5393405), (35.4891566, -119.5393307), (35.4891396, -119.5393241), (35.4891234, -119.539315), (35.4891073, -119.5393058), (35.4890907, -119.5392976), (35.4890742, -119.5392884), (35.4890575, -119.5392797), (35.4890406, -119.5392709), (35.4890235, -119.5392619), (35.4890058, -119.5392542), (35.4889876, -119.5392472), (35.4889694, -119.5392393), (35.48896, -119.5392364)], colors=['#b8433a', '#dedbd2'], name='run left s 954-1011',
                 colour_src='t040.jpg (red / white / blue; inventory row s 996 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1100 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4883199, -119.5395787), (35.4883061, -119.5395871), (35.488292, -119.539594), (35.4882776, -119.5395994), (35.488263, -119.5396032), (35.4882483, -119.5396054), (35.4882335, -119.539606), (35.4882187, -119.5396052), (35.4882039, -119.5396029), (35.4881891, -119.5395994), (35.4881744, -119.5395946), (35.4881597, -119.5395888), (35.488145, -119.539582), (35.4881302, -119.5395744), (35.4881228, -119.5395703)], colors='rwb', name='run left s 1089-1116',
                 colour_src='t044.jpg (red / white / blue; inventory row s 1088 left)',
                 src='kerb run (owner lap 1): the round-4 strip extent on c20_s1250; the band reader found no line on the new edge: band centre 0.45 m inside the edge'),
            dict(side='left', line_latlon=[(35.4873622, -119.5393527), (35.4873455, -119.5393637), (35.4873291, -119.5393751), (35.4873129, -119.5393867), (35.4872969, -119.5393984), (35.487281, -119.5394102), (35.4872655, -119.5394225), (35.48725, -119.5394348), (35.4872346, -119.539447), (35.4872192, -119.5394592), (35.4872039, -119.5394714), (35.4871885, -119.5394834), (35.4871732, -119.5394954), (35.4871578, -119.5395072), (35.4871425, -119.539519), (35.4871271, -119.5395306), (35.487111, -119.5395409), (35.4870949, -119.539551), (35.4870788, -119.5395609), (35.4870626, -119.5395708), (35.4870467, -119.539581), (35.4870309, -119.5395912), (35.487015, -119.5396012), (35.4869985, -119.5396098), (35.4869832, -119.539621), (35.4869676, -119.5396314), (35.4869515, -119.5396408), (35.4869358, -119.5396509), (35.4869203, -119.5396617), (35.4869053, -119.5396737), (35.486889, -119.5396831), (35.486873, -119.5396933), (35.4868567, -119.5397033), (35.4868409, -119.5397147), (35.4868248, -119.5397258), (35.4868166, -119.5397312)], colors='rwb', name='run left s 1203-1272', width=0.75,   # band width 0.76 m (p25-p75 0.6-0.88, 33 readings on the clean captures, round 8)
               
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1350 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4865519, -119.5403896), (35.4865507, -119.5404122), (35.4865527, -119.5404346), (35.4865543, -119.5404569), (35.4865561, -119.5404792), (35.4865569, -119.5405014), (35.4865582, -119.5405236), (35.4865591, -119.5405457), (35.48656, -119.5405679), (35.4865606, -119.54059), (35.4865612, -119.5406122), (35.4865618, -119.5406343), (35.486564, -119.5406563), (35.4865644, -119.5406785), (35.4865648, -119.5407006), (35.4865655, -119.5407227), (35.4865659, -119.5407448), (35.4865665, -119.5407669), (35.4865671, -119.5407889), (35.4865671, -119.540811), (35.4865683, -119.540833), (35.4865694, -119.5408549), (35.4865704, -119.5408768), (35.4865711, -119.5408987), (35.4865714, -119.5409206), (35.4865729, -119.5409424), (35.4865745, -119.5409643), (35.486574, -119.5409862), (35.4865747, -119.5410081), (35.4865763, -119.5410299)], colors='rwb', name='run left s 1338-1396',
                 colour_src='t054.jpg (red / white / blue; inventory row s 1344 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4866058, -119.5416842), (35.4866063, -119.5417055), (35.4866072, -119.5417267), (35.4866079, -119.5417479), (35.4866089, -119.541769), (35.4866097, -119.5417902), (35.4866106, -119.5418114), (35.4866116, -119.5418326), (35.4866122, -119.5418541), (35.4866125, -119.5418756), (35.4866135, -119.5418973), (35.4866144, -119.5419193), (35.4866164, -119.5419415)], colors='rwb', name='run left s 1449-1479', width=0.65,   # band width 0.64 m (p25-p75 0.6-0.64, 26 readings on the clean captures, round 8)
               
                 colour_src='colour unverified: no inventory kerb row on that side within 40 m of s 1449-1479',
                 src='kerb run (owner lap 1): the block line followed on c20_s1600 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; round 8: the first 6 m dropped (with the new edges the left edge steps out to the T4-T5 apron at the run start, the edge-relative offset ramped 0.12 m per station over the step gate; the blocks there stand at the old edge, an open row)'),
            dict(side='left', line_latlon=[(35.4868471, -119.5425864), (35.4868571, -119.5426044), (35.4868685, -119.5426206), (35.4868795, -119.5426371), (35.4868907, -119.5426534), (35.4869006, -119.5426711), (35.4869122, -119.5426872), (35.4869225, -119.5427047), (35.4869336, -119.5427213), (35.486944, -119.5427389), (35.4869552, -119.5427557), (35.486966, -119.5427731), (35.4869774, -119.54279), (35.4869887, -119.5428071), (35.4870003, -119.542824), (35.4870115, -119.5428414), (35.4870236, -119.5428581), (35.4870297, -119.5428663)], colors='rwb', name='run left s 1541-1574', width=1.15,   # band width 1.16 m (p25-p75 1.04-1.2, 45 readings on the clean captures, round 8)
               
                 colour_src='colour unverified: no inventory kerb row on that side within 40 m of s 1541-1574',
                 src='kerb run (owner lap 1): the block line followed on c20_s1700 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4874573, -119.543538), (35.4874655, -119.5435555), (35.4874732, -119.5435734), (35.4874804, -119.5435917), (35.4874876, -119.5436101), (35.4874949, -119.5436284), (35.4875003, -119.5436479), (35.4875064, -119.543667), (35.4875119, -119.5436865), (35.4875171, -119.5437061), (35.4875216, -119.5437261), (35.4875269, -119.5437459), (35.4875307, -119.5437661), (35.4875357, -119.5437862), (35.4875375, -119.5437965)], colors=['#b8433a', '#dedbd2'], name='run left s 1653-1680',
                 colour_src='t062.jpg (red / white; inventory row s 1645 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1800 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4874867, -119.5455455), (35.48748, -119.5455642), (35.4874711, -119.5455813), (35.4874568, -119.5455938), (35.487444, -119.5456071)], colors='rwb', name='run left s 1843-1851', profile=dict(height=0.0, face=0.15, back=0.30),   # round 8 checkpoint 4: flat separation blocks (the coordinator, pending the owner's answer): no CW frame shows them raised (t066-t068 show the painted blocks only); at 10 cm the car rolls over here (sweep: 180 deg at line -1 m on 1868-1933 R with every face 0.15-0.60 m)
                width=1.1,   # band width 1.12 m (p25-p75 1.04-1.25, 12 readings on the clean captures, round 8)
               
                 colour_src='t068.jpg (red / white / blue; inventory row s 1839 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1950 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4891044, -119.5499298), (35.4891199, -119.5499379), (35.4891355, -119.5499463), (35.4891438, -119.5499494)], colors='rwb', name='run left s 2539-2544',
                 colour_src='colour unverified: no inventory kerb row on that side within 40 m of s 2539-2544',
                 src='kerb run (owner lap 1): the block line followed on c20_s2650 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4903283, -119.5506139), (35.4903448, -119.5506233), (35.4903614, -119.5506325), (35.4903781, -119.5506412), (35.4903947, -119.5506505), (35.4904115, -119.550659), (35.490428, -119.5506683), (35.4904442, -119.5506782), (35.4904606, -119.5506879), (35.4904768, -119.5506977), (35.4904938, -119.5507054), (35.4905099, -119.5507159), (35.4905269, -119.5507236), (35.4905429, -119.5507344), (35.4905593, -119.5507442), (35.4905755, -119.5507548), (35.4905927, -119.5507626), (35.4906093, -119.5507724), (35.4906265, -119.550781), (35.4906437, -119.5507893), (35.4906616, -119.5507961), (35.4906794, -119.5508038), (35.4906973, -119.5508112), (35.4907154, -119.5508181), (35.4907337, -119.5508246), (35.4907522, -119.5508305), (35.4907708, -119.5508369), (35.4907895, -119.5508428), (35.490809, -119.5508438), (35.4908183, -119.5508476)], colors='rwb', name='run left s 2689-2746', width=1.1,   # band width 1.12 m (p25-p75 1.01-1.24, 50 readings on the clean captures, round 8)
               
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s2850 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4916648, -119.5503963), (35.4916777, -119.5503825), (35.4916911, -119.5503692), (35.4917059, -119.550359)], colors='rwb', name='run left s 2849-2855',
                 colour_src='colour unverified: no inventory kerb row on that side within 40 m of s 2849-2855',
                 src='kerb run (owner lap 1): the block line followed on c20_s2950 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4929388, -119.5497446), (35.492955, -119.5497402), (35.4929714, -119.5497346), (35.4929883, -119.5497324), (35.4930052, -119.5497295)], colors='rwb', name='run left s 3005-3013', width=1.1,   # band width 1.1 m (p25-p75 0.93-1.15, 10 readings on the clean captures, round 8)
               
                 colour_src='colour unverified: no inventory kerb row on that side within 40 m of s 3005-3013',
                 src='kerb run (owner lap 1): the block line followed on c20_s3150 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4959299, -119.5495995), (35.4959478, -119.5495976), (35.4959658, -119.5495962), (35.4959835, -119.5495928), (35.4960012, -119.5495893), (35.496019, -119.5495935), (35.4960367, -119.5495941), (35.4960543, -119.5495933), (35.4960719, -119.5495928), (35.4960896, -119.5495921), (35.4961072, -119.5495919), (35.496125, -119.5495905), (35.4961428, -119.5495901), (35.4961608, -119.5495893), (35.4961789, -119.5495881), (35.4961972, -119.5495876), (35.4962156, -119.5495821), (35.4962342, -119.549586), (35.4962531, -119.5495865), (35.4962721, -119.5495859), (35.4962913, -119.5495847), (35.4963106, -119.5495826), (35.4963206, -119.549584)], colors='rwb', name='run left s 3340-3383', width=1.25,   # band width 1.24 m (p25-p75 1.16-1.28, 51 readings on the clean captures, round 8)
               
                 colour_src='t110.jpg (red / white / blue; inventory row s 3329 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s3500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4965872, -119.5487644), (35.4965731, -119.5487478), (35.4965591, -119.5487316), (35.4965457, -119.5487151), (35.496531, -119.5487007), (35.4965176, -119.5486851), (35.4965038, -119.5486705), (35.4964906, -119.5486551), (35.4964771, -119.5486407), (35.4964636, -119.5486262), (35.4964502, -119.5486118), (35.4964365, -119.5485979), (35.4964226, -119.5485844), (35.4964106, -119.5485683), (35.4963981, -119.5485529), (35.4963855, -119.5485376), (35.4963728, -119.5485222), (35.4963598, -119.5485075), (35.4963438, -119.5484963), (35.4963301, -119.5484821), (35.4963202, -119.5484631), (35.496307, -119.5484482), (35.4962941, -119.5484329), (35.4962805, -119.5484185), (35.4962672, -119.5484037)], colors='rwb', name='run left s 3470-3518', width=0.75,   # band width 0.76 m (p25-p75 0.64-1.14, 55 readings on the clean captures, round 8)
                  # round 8: raised 10 cm per the owner (lap 2 note 1) lifts a wheel in the traversal gate (215-562 ms); held flat pending the gate decision (report)

                 colour_src='t116.jpg (red / white / blue; inventory row s 3479 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s3600 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; raised (round 8): owner lap 2: raised, aggressive; height from the owner pending (10 cm, the 6 cm of the apex run the floor; t114-t118 at full resolution show no resolvable face: t116, the closest frame, has a soft 2-3 px white-to-asphalt edge)'),
            dict(side='left', line_latlon=[(35.4947997, -119.5478563), (35.4947813, -119.5478611), (35.4947633, -119.5478667), (35.4947461, -119.5478749), (35.4947285, -119.5478816), (35.4947111, -119.547888), (35.4946935, -119.5478937), (35.4946761, -119.5478994), (35.4946588, -119.547905), (35.4946418, -119.5479112), (35.4946249, -119.5479172), (35.4946081, -119.5479231), (35.4945915, -119.5479287), (35.494575, -119.5479342), (35.4945587, -119.5479394), (35.4945424, -119.5479444), (35.4945263, -119.547949), (35.4945104, -119.5479533), (35.4944945, -119.5479573), (35.4944787, -119.5479608), (35.494463, -119.5479636), (35.4944474, -119.5479663), (35.4944317, -119.5479681), (35.4944162, -119.5479712), (35.4944005, -119.5479724), (35.4943848, -119.5479731), (35.4943691, -119.5479732), (35.4943532, -119.5479731), (35.4943371, -119.5479729), (35.4943211, -119.5479708), (35.4943049, -119.5479685), (35.4942885, -119.5479656), (35.494272, -119.5479622), (35.4942553, -119.5479579), (35.4942381, -119.5479548), (35.4942298, -119.5479516)], colors='rwb', name='run left s 3691-3760',
                 colour_src='t124.jpg (red / white / blue; inventory row s 3725 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s3850 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4934757, -119.5481219), (35.4934603, -119.5481288), (35.4934448, -119.5481354), (35.4934294, -119.5481419), (35.4934138, -119.5481476), (35.493398, -119.5481528), (35.4933823, -119.5481579), (35.4933662, -119.5481615), (35.4933502, -119.5481654), (35.4933341, -119.5481692), (35.4933178, -119.5481722), (35.4933013, -119.5481737), (35.4932846, -119.5481742), (35.4932679, -119.5481761), (35.4932509, -119.5481729), (35.4932339, -119.5481714), (35.4932253, -119.5481707)], colors='rwb', name='run left s 3845-3876', width=0.75,   # band width 0.74 m (p25-p75 0.61-0.8, 18 readings on the clean captures, round 8)
               
                 colour_src='t128.jpg (red / white / blue; inventory row s 3848 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s3950 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.4923911, -119.5484772), (35.4923752, -119.5484853), (35.4923592, -119.5484931), (35.4923441, -119.548503), (35.4923281, -119.5485104), (35.4923126, -119.5485188), (35.4922968, -119.5485261), (35.4922812, -119.5485341), (35.4922647, -119.5485388), (35.4922486, -119.5485442), (35.4922328, -119.5485509), (35.4922162, -119.5485536), (35.4922, -119.548558), (35.4921839, -119.5485627), (35.4921675, -119.548566), (35.4921511, -119.5485683), (35.4921346, -119.5485694), (35.4921183, -119.5485723), (35.4921017, -119.5485731), (35.4920852, -119.548574), (35.4920686, -119.548574), (35.492052, -119.5485738), (35.4920353, -119.5485734), (35.4920185, -119.5485724), (35.4920017, -119.548571), (35.4919848, -119.5485686), (35.4919761, -119.5485695)], colors='rwb', name='run left s 3972-4024',
                 colour_src='t132.jpg (red / white / blue; inventory row s 3981 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s4100 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='left', line_latlon=[(35.488828, -119.5479367), (35.4888149, -119.5479272), (35.4888011, -119.5479197), (35.4887881, -119.5479106), (35.4887749, -119.5479019), (35.4887614, -119.5478931), (35.4887474, -119.5478842), (35.4887463, -119.5478603), (35.4887244, -119.5478588), (35.4887149, -119.5478437), (35.4887069, -119.5478273), (35.4887024, -119.5478086), (35.4886992, -119.5477894), (35.4886976, -119.54778)], colors='rwb', name='run left s 4381-4406', width=1.05,   # band width 1.04 m (p25-p75 0.8-1.14, 35 readings on the clean captures, round 8)
               
                 colour_src='t142.jpg (red / white / blue; inventory row s 4371 left)',
                 src='kerb run (owner lap 1): the block line followed on c20_s4500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4888311, -119.5424477), (35.4888338, -119.5424259), (35.4888364, -119.5424039), (35.4888373, -119.5423818), (35.4888387, -119.5423597), (35.4888399, -119.5423376), (35.4888415, -119.5423154), (35.4888437, -119.5422933), (35.4888443, -119.542271), (35.4888461, -119.5422488), (35.4888471, -119.5422264), (35.4888488, -119.5422042), (35.4888505, -119.5421819), (35.4888517, -119.5421597), (35.4888529, -119.5421374), (35.4888543, -119.5421152), (35.4888557, -119.5420931), (35.4888567, -119.542071), (35.4888581, -119.542049), (35.48886, -119.5420273), (35.4888612, -119.5420055), (35.4888627, -119.5419839), (35.4888634, -119.5419623), (35.4888644, -119.5419408), (35.4888656, -119.5419194), (35.4888665, -119.541898), (35.4888673, -119.5418767), (35.4888684, -119.5418553), (35.4888696, -119.541834), (35.488872, -119.5418125), (35.4888725, -119.5417907), (35.4888728, -119.5417689), (35.4888741, -119.5417468), (35.4888746, -119.5417244), (35.4888762, -119.5417018), (35.4888775, -119.5416788), (35.4888793, -119.5416557), (35.4888809, -119.5416321), (35.4888837, -119.5416084), (35.4888854, -119.5415843), (35.4888907, -119.5415605)], colors='rwb', name='run right s 188-268', width=1.3,   # band width 1.28 m (p25-p75 1.08-1.4, 117 readings on the clean captures, round 8)
               
                 colour_src='t012.jpg (red / white / blue; inventory row s 256 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s0350 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4895832, -119.5409801), (35.4896019, -119.5409797), (35.4896205, -119.54098), (35.489639, -119.5409814), (35.4896573, -119.5409824), (35.4896757, -119.5409842), (35.4896939, -119.5409873), (35.4897122, -119.5409894), (35.4897305, -119.5409916)], colors='rwb', name='run right s 360-376', width=1.1,   # band width 1.08 m (p25-p75 0.72-1.15, 22 readings on the clean captures, round 8)
               
                 colour_src='t018.jpg (red / white / blue; inventory row s 408 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s0500 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4900404, -119.5410523), (35.4900579, -119.5410549), (35.4900752, -119.5410577), (35.4900921, -119.5410611), (35.490109, -119.5410648), (35.4901258, -119.5410683), (35.4901426, -119.541072), (35.490159, -119.5410795)], colors='rwb', name='run right s 410-424',
                 colour_src='t018.jpg (red / white / blue; inventory row s 408 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s0550 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4914797, -119.5416132), (35.4914933, -119.5416189), (35.4915073, -119.54162), (35.4915212, -119.5416196), (35.4915349, -119.5416177), (35.4915481, -119.541613), (35.4915606, -119.5416063), (35.4915725, -119.5415984), (35.4915837, -119.5415893), (35.4915947, -119.5415797), (35.4916052, -119.5415694)], colors='rwb', name='run right s 584-604', width=0.6,   # band width 0.6 m (p25-p75 0.54-0.72, 19 readings on the clean captures, round 8)
               
                 colour_src='t025.jpg (red / white / blue; inventory row s 590 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s0700 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4888585, -119.5393313), (35.4888433, -119.5393278), (35.4888282, -119.5393254), (35.4888129, -119.5393241), (35.4887977, -119.539324), (35.4887824, -119.539325), (35.4887672, -119.5393271), (35.488752, -119.5393305), (35.4887369, -119.5393351), (35.4887223, -119.5393422), (35.4887081, -119.5393506), (35.4886935, -119.5393585), (35.4886794, -119.5393682), (35.488666, -119.5393798), (35.4886521, -119.5393908), (35.4886468, -119.5393993)], colors='rwb', name='run right s 1020-1049', width=1.05,   # band width 1.04 m (p25-p75 0.76-1.16, 18 readings on the clean captures, round 8)
               
                 colour_src='colour unverified: no inventory kerb row on that side within 40 m of s 1020-1049',
                 src='kerb run (owner lap 1): the block line followed on c20_s1150 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4876748, -119.5394222), (35.4876593, -119.5394181), (35.4876437, -119.5394148), (35.4876281, -119.5394124), (35.4876125, -119.5394108), (35.4875968, -119.5394101), (35.4875812, -119.5394102), (35.4875656, -119.5394111), (35.48755, -119.5394127), (35.4875343, -119.539415), (35.4875186, -119.539418), (35.4875029, -119.5394217), (35.487495, -119.5394237)], colors=['#b8433a', '#dedbd2'], name='run right s 1168-1191',
                 colour_src='t048.jpg (red / white; inventory row s 1175 right)',
                 src='kerb run (owner lap 1): the round-4 strip extent on c20_s1300; the band reader found no line on the new edge: band centre 0.45 m inside the edge'),
            dict(side='right', line_latlon=[(35.4866915, -119.5400635), (35.4866863, -119.5400815), (35.4866808, -119.5400993), (35.4866787, -119.5401086)], colors='rwb', name='run right s 1304-1309',
                 colour_src='t052.jpg (red / white / blue; inventory row s 1304 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1450 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4867214, -119.5421104), (35.4867265, -119.5421294), (35.4867287, -119.5421489), (35.4867313, -119.5421681), (35.4867352, -119.542187), (35.4867403, -119.5422053), (35.4867463, -119.5422232), (35.4867528, -119.5422408), (35.4867607, -119.5422576), (35.4867706, -119.542273), (35.4867776, -119.5422905)], colors='rwb', name='run right s 1495-1515',
                 colour_src='t058.jpg (red / white / blue; inventory row s 1492 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1650 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4876216, -119.5448778), (35.4876216, -119.5448992), (35.4876138, -119.5449193), (35.4876131, -119.5449404), (35.4876106, -119.5449614), (35.4876071, -119.5449823), (35.4876064, -119.5450035), (35.4876057, -119.5450246), (35.4876049, -119.5450459), (35.487605, -119.5450673), (35.4876044, -119.5450888), (35.487604, -119.5451104), (35.4876049, -119.5451321), (35.4876046, -119.545154), (35.4876054, -119.545176), (35.4876031, -119.5451984), (35.4876068, -119.5452206), (35.4876075, -119.5452432), (35.4876072, -119.545266), (35.4876079, -119.545289), (35.4876073, -119.5453005)], colors='rwb', name='run right s 1779-1818',
                 colour_src='t066.jpg (white / red / blue; inventory row s 1773 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s1900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4873973, -119.5458164), (35.487384, -119.5458325), (35.4873685, -119.5458448), (35.4873555, -119.545861), (35.487342, -119.5458759), (35.4873269, -119.5458882), (35.4873137, -119.5459036), (35.487299, -119.545916), (35.4872853, -119.5459301), (35.4872717, -119.5459442), (35.4872583, -119.5459586), (35.4872454, -119.5459737), (35.4872322, -119.5459881), (35.4872193, -119.5460029), (35.4872062, -119.5460174), (35.4871935, -119.5460323), (35.4871809, -119.5460472), (35.4871685, -119.5460625), (35.4871554, -119.5460766), (35.4871428, -119.5460913), (35.48713, -119.5461057), (35.4871174, -119.5461203), (35.4871052, -119.5461354), (35.487093, -119.5461505), (35.4870808, -119.5461653), (35.4870686, -119.5461803), (35.4870566, -119.5461954), (35.487045, -119.546211), (35.487033, -119.546226), (35.4870212, -119.5462412), (35.4870096, -119.5462567), (35.4869971, -119.5462713), (35.4869861, -119.5462873), (35.4869806, -119.5462954)], colors='rwb', name='run right s 1868-1933', profile=dict(height=0.0, face=0.15, back=0.30),   # round 8 checkpoint 4: flat separation blocks (the coordinator, pending the owner's answer): no CW frame shows them raised (t066-t068 show the painted blocks only); at 10 cm the car rolls over here (sweep: 180 deg at line -1 m on 1868-1933 R with every face 0.15-0.60 m)
                width=0.7,   # band width 0.68 m (p25-p75 0.6-0.8, 92 readings on the clean captures, round 8)
               
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s2000 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4871588, -119.5497655), (35.487175, -119.5497722), (35.4871907, -119.5497806), (35.4872064, -119.549789), (35.4872221, -119.5497972), (35.4872379, -119.5498057), (35.4872541, -119.5498123), (35.48727, -119.5498199), (35.4872862, -119.5498265), (35.4873022, -119.5498341), (35.4873186, -119.5498393), (35.4873351, -119.5498444), (35.4873517, -119.5498489), (35.4873602, -119.5498499)], colors='rwb', name='run right s 2315-2340', width=1.1,   # band width 1.12 m (p25-p75 0.93-1.19, 18 readings on the clean captures, round 8)
               
                 colour_src='t082.jpg (red / white / blue; inventory row s 2313 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s2450 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4909945, -119.5507366), (35.4910112, -119.5507347), (35.4910279, -119.5507328), (35.4910447, -119.5507314), (35.4910615, -119.5507294), (35.4910788, -119.5507298), (35.4910947, -119.5507218), (35.4911112, -119.5507175), (35.4911276, -119.5507127), (35.4911439, -119.5507074), (35.4911601, -119.5507016), (35.4911761, -119.5506953), (35.4911914, -119.5506865), (35.4912064, -119.5506772), (35.4912147, -119.5506748)], colors='rwb', name='run right s 2765-2792',
                 colour_src='t094.jpg (red / white / blue; inventory row s 2760 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s2900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4964347, -119.5494086), (35.4964487, -119.5494004), (35.496461, -119.5493888), (35.4964731, -119.5493773), (35.4964851, -119.5493655), (35.4964957, -119.5493517), (35.4965061, -119.5493379), (35.4965158, -119.5493235), (35.4965248, -119.5493084), (35.4965326, -119.5492923), (35.4965412, -119.5492772), (35.4965505, -119.5492626), (35.4965577, -119.5492464), (35.4965642, -119.5492299), (35.4965694, -119.5492128), (35.4965754, -119.5491963), (35.4965802, -119.5491792), (35.4965827, -119.5491614), (35.4965873, -119.5491443), (35.4965887, -119.5491265), (35.4965894, -119.5491088), (35.4965908, -119.549091), (35.4965897, -119.5490734), (35.4965892, -119.5490556), (35.4965862, -119.5490382), (35.4965838, -119.5490205), (35.4965803, -119.5490124)], colors='wb', name='run right s 3400-3451', profile=dict(height=0.06, face=0.15, back=0.3),
                 colour_src='t114.jpg (red / white / blue; inventory row s 3445 right)',
                 src="kerb run (owner lap 1): the block line followed on c20_s3550 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run; raised: onboard t114 (1:52) shows the T9 apex kerb's sloped track-side face 10-15 px tall at base row ~555 (horizon row ~265), camera 1.49 m from the CRX ahead in t116 (roof 1.29 m, 76 px at base row 363): horizon ratio 0.05-0.08 m, 0.06 m used (compare/HEIGHTS.md); the exit kerb (t116, 3463-3512 L) shows a face of 1-2 px (<= 0.02 m): flat"),
            dict(side='right', line_latlon=[(35.4939224, -119.5480304), (35.4939067, -119.5480325), (35.4938911, -119.5480355), (35.4938758, -119.5480414), (35.4938608, -119.5480486), (35.4938453, -119.5480536), (35.4938304, -119.5480615), (35.4938153, -119.5480691), (35.4937999, -119.5480764)], colors='rwb', name='run right s 3794-3810', width=1.1,   # band width 1.12 m (p25-p75 1.0-1.16, 18 readings on the clean captures, round 8)
               
                 colour_src='t126.jpg (red / white / blue; inventory row s 3787 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s3900 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4930618, -119.5482991), (35.493045, -119.5483041), (35.4930283, -119.5483056), (35.4930117, -119.5483067), (35.4929953, -119.5483081), (35.492979, -119.5483103), (35.4929619, -119.5483066), (35.4929457, -119.5483102), (35.4929297, -119.548315), (35.4929145, -119.5483245), (35.4928975, -119.548324), (35.4928815, -119.5483294), (35.4928657, -119.5483359), (35.4928495, -119.5483413), (35.4928338, -119.5483488), (35.4928203, -119.5483634), (35.4928052, -119.5483727), (35.4927897, -119.5483813), (35.4927736, -119.5483884), (35.4927573, -119.5483954), (35.4927427, -119.548407), (35.4927351, -119.5484121)], colors='rwb', name='run right s 3894-3935', width=0.55,   # band width 0.56 m (p25-p75 0.48-0.85, 28 readings on the clean captures, round 8)
               
                 colour_src='t130.jpg (red / white / blue; inventory row s 3914 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s4050 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4919081, -119.5486898), (35.4918898, -119.5486871), (35.4918716, -119.5486834), (35.4918537, -119.5486796), (35.4918357, -119.5486768), (35.4918179, -119.5486732), (35.4918, -119.5486707), (35.4917824, -119.5486669), (35.4917648, -119.5486632), (35.4917473, -119.5486596), (35.4917297, -119.5486565), (35.4917121, -119.5486537), (35.4916946, -119.54865), (35.4916774, -119.5486444), (35.4916595, -119.5486435), (35.4916419, -119.5486403), (35.4916244, -119.5486364), (35.4916067, -119.5486333), (35.4915891, -119.5486291), (35.4915716, -119.5486244), (35.4915538, -119.5486215), (35.491536, -119.5486186), (35.4915181, -119.5486161), (35.4915003, -119.5486127), (35.4914825, -119.5486093), (35.4914648, -119.5486046), (35.4914469, -119.5486016), (35.491429, -119.5485986), (35.4914111, -119.5485956), (35.4913932, -119.5485922), (35.4913754, -119.5485889), (35.4913575, -119.5485855), (35.4913396, -119.5485821), (35.4913217, -119.5485788), (35.4913038, -119.5485754), (35.4912861, -119.5485712), (35.4912681, -119.5485685), (35.4912502, -119.5485647), (35.4912322, -119.5485623), (35.4912144, -119.5485585), (35.4911966, -119.5485543), (35.491179, -119.548549), (35.4911608, -119.5485479), (35.4911428, -119.5485457), (35.4911251, -119.548542), (35.4911073, -119.5485383), (35.4910895, -119.5485351), (35.4910719, -119.548531), (35.4910546, -119.5485252), (35.4910453, -119.5485267)], colors='wb', name='run right s 4030-4127', width=0.7,   # band width 0.68 m (p25-p75 0.56-0.8, 81 readings on the clean captures, round 8)
               
                 colour_src='t136.jpg (white / blue; inventory row s 4122 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s4200 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4893237, -119.5482085), (35.4893057, -119.5482068), (35.4892877, -119.5482028), (35.4892697, -119.5481997), (35.4892515, -119.5481964), (35.4892333, -119.5481934), (35.4892152, -119.5481899), (35.4891973, -119.5481844), (35.4891788, -119.548184), (35.4891607, -119.5481811), (35.4891429, -119.5481767), (35.4891249, -119.5481748), (35.4891071, -119.5481715), (35.4890894, -119.5481688), (35.4890718, -119.5481656), (35.4890543, -119.5481622), (35.4890367, -119.5481592), (35.4890191, -119.5481555), (35.4890015, -119.5481508), (35.4889838, -119.5481467), (35.488966, -119.5481411), (35.488948, -119.5481355), (35.4889301, -119.5481278), (35.4889119, -119.5481213), (35.4888933, -119.5481149), (35.4888843, -119.5481097)], colors='wb', name='run right s 4321-4370', width=1.15,   # band width 1.16 m (p25-p75 1.04-1.28, 72 readings on the clean captures, round 8)
               
                 colour_src='t140.jpg (white / blue; inventory row s 4308 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_s4450 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
            dict(side='right', line_latlon=[(35.4885643, -119.5476145), (35.4885614, -119.5475911), (35.4885606, -119.5475677), (35.4885597, -119.5475445), (35.4885635, -119.5475216), (35.4885577, -119.5474986), (35.4885568, -119.5474758), (35.488556, -119.5474532), (35.4885549, -119.5474306), (35.4885546, -119.5474081), (35.4885563, -119.5473858), (35.488558, -119.5473636), (35.488554, -119.5473411), (35.4885547, -119.5473189), (35.4885548, -119.5472968), (35.4885558, -119.5472746), (35.4885569, -119.5472525), (35.4885579, -119.5472305), (35.4885598, -119.5472084), (35.4885612, -119.5471863), (35.4885613, -119.5471641), (35.4885624, -119.547142), (35.48857, -119.5471204), (35.4885658, -119.5470979), (35.4885671, -119.5470758), (35.4885689, -119.5470538), (35.4885694, -119.5470317), (35.4885709, -119.5470096), (35.4885721, -119.5469877), (35.488574, -119.5469659), (35.4885745, -119.546944), (35.4885769, -119.5469223), (35.4885779, -119.5469005), (35.4885787, -119.5468789), (35.4885795, -119.5468572), (35.4885811, -119.5468356), (35.4885821, -119.546814), (35.4885838, -119.5467924), (35.488586, -119.5467708), (35.488586, -119.5467599)], colors='rwb', name='run right s 4424-4501',
                 colour_src='t144.jpg (white / blue / red; inventory row s 4410 right)',
                 src='kerb run (owner lap 1): the block line followed on c20_p0240 with the band reader (edges_spline.bands outer limits, the band centre 0.45 m inside), one continuous run'),
        ],
        kerb_lines=[],
        declared_walls=[
            # the pit wall: white K-rail (Jersey) segments with red panels between the front straight and the pit lane,
            # measured with compare/wall_measure.py (--edge left, bright band 3.5-3.7 m beyond the left edge)
            dict(name='pit wall, front straight', kind='concrete', h=0.81, fence=0.0, color='#e4e2dc',
                 # judge r2: white K-rail segments with red ones between (onboard t002-t006, t148, s4550; pit-lane video
                 # t1240000-t1330000: two white 6.1 m segments to one red, the 20 ft CalTrans K-rail), and a dark section
                 # near s 101 (onboard t004 / t006: ~6 m of dark, scorched or painted panel) at 286-292 m along the run
                 pattern=dict(colors=['#e4e2dc', '#e4e2dc', '#b8433a'], period_m=18.3),
                 # judge r8 (cp6): the pit-in end (the nose) is two unpainted beige K-rail segments (2 x 6.1 m) under the berm, then the
                 # station and the white / red pattern (pit-lane video t1240000)
                 sections=[dict(from_m=0.0, to_m=12.2, color='#c9bc9c'), dict(from_m=286.0, to_m=292.0, color='#3b3a38')],
                 h_src='jersey-ref: the onboard t004 wall is a K-rail (0.81 m); camh 1.05 m from it',
                 src='wall_measure.py --edge left 4490-4693 (88 % picked, offset p50 3.56 m) and 0-300 (75 %, p50 3.74 m) on c20_s4550..c20_s0300; onboard t000-t008, t148-t158 (white K-rail with red panels); pit-lane video 20:40-22:28 (on the right of the lane)',
                 latlon=[(35.4887467, -119.5466176), (35.4887756, -119.5463925), (35.4887872, -119.5461735), (35.4887997, -119.5459532),
                         (35.4888121, -119.5457331), (35.4888245, -119.545513), (35.4888375, -119.5452929), (35.4888504, -119.5450728),
                         (35.4888629, -119.5448526), (35.4888756, -119.5446326), (35.4888859, -119.5445371), (35.4888939, -119.5443166),
                         (35.4889064, -119.5440964), (35.4889189, -119.5438763), (35.488932, -119.5436563), (35.4889447, -119.5434362),
                         (35.4889573, -119.543216), (35.4889707, -119.542996), (35.4889828, -119.5427758), (35.4889963, -119.5425558),
                         (35.4890124, -119.542336), (35.4890148, -119.5422713)]),
            # the wall ends 6 m past the starter's hut, at the concrete crossover to the pit lane (c20_s0250 window at
            # 35.48906,-119.54215: the K-rail stops at the crossover; wall_measure's picks beyond it, s 214-237, followed
            # the pit lane's edge, not a wall)
            # the paddock-side K-rail along the north side of the pit lane, with openings to the paddock (the gaps in the picks)
            dict(name='pit lane, paddock side, west', kind='concrete', h=0.81, fence=0.0, color='#e4e2dc',
                 pattern=dict(colors=['#e4e2dc', '#e4e2dc', '#b8433a'], period_m=18.3),   # red / white K-rail (pit video t1249000-t1312000, judge r2 pit_01)
                 h_src='jersey-ref: a K-rail like the pit wall (pit-lane video 20:49, t1249000: both walls the same height)',
                 src='wall_measure.py --edge left 4490-4693 --off 12,30 (68 % picked, 20.8 m beyond the left edge) on c20_s4600 / c20_p0360; pit-lane video 20:49-21:52 (Jersey wall on the left of the lane)',
                 latlon=[(35.4889157, -119.5464997), (35.4889363, -119.5462801), (35.4889488, -119.54606), (35.4889616, -119.5458399),
                         (35.4889738, -119.5456197), (35.4889864, -119.5453996), (35.4889993, -119.5451795), (35.489005, -119.5450805)]),
            dict(name='pit lane, paddock side, tower', kind='concrete', h=0.81, fence=0.0, color='#e4e2dc',
                 pattern=dict(colors=['#e4e2dc', '#e4e2dc', '#b8433a'], period_m=18.3),   # red / white K-rail (pit video t1249000-t1312000, judge r2 pit_01)
                 h_src='jersey-ref (as the west run)',
                 src='wall_measure.py --edge left (175-210 m and 0-42 m runs, 21 m beyond the left edge) on c20_p0420 / c20_p0480; pit-lane video 21:52 (the wall at the tower, a yellow cone at its foot)',
                 latlon=[(35.4890129, -119.5449429), (35.489031, -119.5447233), (35.4890355, -119.5445633), (35.4890427, -119.544551),
                         (35.48906, -119.5443313), (35.489061, -119.5441102)]),
            dict(name='pit lane, paddock side, east', kind='concrete', h=0.81, fence=0.0, color='#e4e2dc',
                 pattern=dict(colors=['#e4e2dc', '#e4e2dc', '#b8433a'], period_m=18.3),   # red / white K-rail (pit video t1249000-t1312000, judge r2 pit_01)
                 h_src='jersey-ref (as the west run)',
                 src='wall_measure.py --edge left 0-300 --off 12,30 (54-196 m run, 21 m beyond the left edge) on c20_p0540 / c20_p0600',
                 latlon=[(35.4890699, -119.5439506), (35.489083, -119.5437306), (35.489096, -119.5435105), (35.4891084, -119.5432903),
                         (35.4891212, -119.5430702), (35.4891339, -119.5428501), (35.4891471, -119.5426301)]),
            # the tyre face of the T1-exit corner station's earth mound, right beside the right edge (onboard t020, 0:20:
            # tyres round the mound, inventory tyre_wall row s 477 right; c20_s0600 / c20_s0650: the dark tyre ring round
            # the station roof, compare/blob_scan.py 1.3 m beyond the edge); the mound's track-side face 0.8 m beyond
            # the edge, its ends turning away from the track
            dict(name='T1-exit station mound tyres', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref: one to two tyres high on the onboard t020 (0.4 m per tyre)',
                 src='onboard t020 (0:20); c20_s0600 / c20_s0650 (the tyre ring round the station roof); position: 0.8 m beyond the fitted right edge at s 474-488, the mound face',
                 latlon=[(35.4906055, -119.5410192), (35.4906059, -119.5410526), (35.4906305, -119.5410667), (35.4906638, -119.5410826),
                         (35.4906971, -119.5410982), (35.4907226, -119.5411075), (35.4907385, -119.5410817)]),
            # judge r8 (cp6): the pale protective surround the frames show round the stations without a declared ring (a ring of 3.5 m radius,
            # pale tyres 0.8 m, as the T3 / T5 rings); 2776 R (t092 does not show the station) and 3202 R left without one
            dict(name='station 826 surround', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref against the station base on t034',
                 src='onboard t034: a low pale surround round the station (stage3_evidence/station_crops.jpg); c20_s0600: a dark tyre ring round the white roof (blob_scan); 3.5 m radius as the T3 ring',
                 latlon=[(35.4904386, -119.5401737), (35.4904506, -119.5401767), (35.4904608, -119.540185), (35.4904677, -119.5401976), (35.49047, -119.5402123), (35.4904677, -119.5402271), (35.4904608, -119.5402396), (35.4904506, -119.540248), (35.4904386, -119.5402509), (35.4904266, -119.540248), (35.4904164, -119.5402396), (35.4904096, -119.5402271), (35.4904072, -119.5402123), (35.4904096, -119.5401976), (35.4904164, -119.540185), (35.4904266, -119.5401767), (35.4904386, -119.5401737)]),
            dict(name='station 1185 surround', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref against the station base on t046',
                 src='onboard t046: a low pale surround round the station (stage3_evidence/station_crops.jpg); c20_s1300: a dark tyre ring round the white roof (blob_scan); 3.5 m radius as the T3 ring',
                 latlon=[(35.4875581, -119.5395148), (35.4875701, -119.5395178), (35.4875803, -119.5395261), (35.4875871, -119.5395387), (35.4875895, -119.5395534), (35.4875871, -119.5395682), (35.4875803, -119.5395807), (35.4875701, -119.5395891), (35.4875581, -119.5395921), (35.487546, -119.5395891), (35.4875358, -119.5395807), (35.487529, -119.5395682), (35.4875266, -119.5395534), (35.487529, -119.5395387), (35.4875358, -119.5395261), (35.487546, -119.5395178), (35.4875581, -119.5395148)]),
            dict(name='station 2370 surround', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref against the station base on t082',
                 src='onboard t082: a low pale surround round the station (stage3_evidence/station_crops.jpg); c20_s2500: a dark tyre ring round the white roof (blob_scan); 3.5 m radius as the T3 ring',
                 latlon=[(35.487615, -119.5496438), (35.4876271, -119.5496467), (35.4876373, -119.5496551), (35.4876441, -119.5496676), (35.4876465, -119.5496824), (35.4876441, -119.5496972), (35.4876373, -119.5497097), (35.4876271, -119.5497181), (35.487615, -119.549721), (35.487603, -119.5497181), (35.4875928, -119.5497097), (35.487586, -119.5496972), (35.4875836, -119.5496824), (35.487586, -119.5496676), (35.4875928, -119.5496551), (35.487603, -119.5496467), (35.487615, -119.5496438)]),
            dict(name='station 3433 surround', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref against the station base on t112',
                 src='onboard t112: a low pale surround round the station (stage3_evidence/station_crops.jpg); c20_s3500: a dark tyre ring round the white roof (blob_scan); 3.5 m radius as the T3 ring',
                 latlon=[(35.4964593, -119.5490965), (35.4964713, -119.5490995), (35.4964815, -119.5491078), (35.4964883, -119.5491204), (35.4964907, -119.5491351), (35.4964883, -119.5491499), (35.4964815, -119.5491625), (35.4964713, -119.5491708), (35.4964593, -119.5491738), (35.4964473, -119.5491708), (35.4964371, -119.5491625), (35.4964302, -119.5491499), (35.4964279, -119.5491351), (35.4964302, -119.5491204), (35.4964371, -119.5491078), (35.4964473, -119.5490995), (35.4964593, -119.5490965)]),
            dict(name='station 3716 surround', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref against the station base on t122',
                 src='onboard t122: a low pale surround round the station (stage3_evidence/station_crops.jpg); c20_s3800: a dark tyre ring round the white roof (blob_scan); 3.5 m radius as the T3 ring',
                 latlon=[(35.4946445, -119.5481377), (35.4946566, -119.5481406), (35.4946668, -119.548149), (35.4946736, -119.5481615), (35.494676, -119.5481763), (35.4946736, -119.5481911), (35.4946668, -119.5482036), (35.4946566, -119.5482119), (35.4946445, -119.5482149), (35.4946325, -119.5482119), (35.4946223, -119.5482036), (35.4946155, -119.5481911), (35.4946131, -119.5481763), (35.4946155, -119.5481615), (35.4946223, -119.548149), (35.4946325, -119.5481406), (35.4946445, -119.5481377)]),
            dict(name='T3 station mound tyres', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref: one to two tyres high round the mound (onboard t040 (0:40))',
                 src='c20_s1100 / c20_s1150: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t040 (0:40) (inventory station row s 996 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)',
                 latlon=[(35.4888477, -119.5394132), (35.4888613, -119.539417), (35.4888723, -119.5394277), (35.4888784, -119.5394432), (35.4888784, -119.5394604), (35.4888723, -119.5394759), (35.4888613, -119.5394866), (35.4888477, -119.5394904), (35.4888341, -119.5394866), (35.4888231, -119.5394759), (35.488817, -119.5394604), (35.488817, -119.5394432), (35.4888231, -119.5394277), (35.4888341, -119.539417), (35.4888477, -119.5394132)]),
            dict(name='T5 station mound tyres', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref: one to two tyres high round the mound (onboard t058 (0:58))',
                 src='c20_s1600: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t058 (0:58) (inventory station row s 1525 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)',
                 latlon=[(35.4868397, -119.5420956), (35.4868533, -119.5420994), (35.4868643, -119.5421101), (35.4868704, -119.5421256), (35.4868704, -119.5421428), (35.4868643, -119.5421583), (35.4868533, -119.542169), (35.4868397, -119.5421728), (35.4868261, -119.542169), (35.4868151, -119.5421583), (35.486809, -119.5421428), (35.486809, -119.5421256), (35.4868151, -119.5421101), (35.4868261, -119.5420994), (35.4868397, -119.5420956)]),
            dict(name='T6 (Riverside) station mound tyres', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref: one to two tyres high round the mound (onboard t074 (1:14))',
                 src='c20_s2150: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t074 (1:14) (inventory station row s 2054 right: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)',
                 latlon=[(35.4865323, -119.5476852), (35.4865459, -119.547689), (35.4865569, -119.5476997), (35.486563, -119.5477152), (35.486563, -119.5477324), (35.4865569, -119.5477479), (35.4865459, -119.5477586), (35.4865323, -119.5477624), (35.4865187, -119.5477586), (35.4865077, -119.5477479), (35.4865016, -119.5477324), (35.4865016, -119.5477152), (35.4865077, -119.5476997), (35.4865187, -119.547689), (35.4865323, -119.5476852)]),
            dict(name='T11 approach (Sunset) station mound tyres', kind='tyres', h=0.8, fence=0.0, color='#d2cab8',
                 h_src='tyre-ref: one to two tyres high round the mound (onboard t138 (2:18))',
                 src='c20_s4400: the dark tyre ring round the station roof (compare/blob_scan.py); onboard t138 (2:18) (inventory station row s 4273 left: a canopy on a tyre-walled mound); a ring of 3.5 m radius round the roof centroid, the mound size on the capture (judge r1 row)',
                 latlon=[(35.4896673, -119.547986), (35.4896809, -119.5479898), (35.4896919, -119.5480005), (35.489698, -119.548016), (35.489698, -119.5480332), (35.4896919, -119.5480487), (35.4896809, -119.5480594), (35.4896673, -119.5480632), (35.4896537, -119.5480594), (35.4896427, -119.5480487), (35.4896366, -119.5480332), (35.4896366, -119.548016), (35.4896427, -119.5480005), (35.4896537, -119.5479898), (35.4896673, -119.547986)]),
            # judge r5 pit_00 / fwd_14 (round 6): the fence stands on the paddock boundary under the tree line, not by the
            # lane: the pit video t1231000 (20:31) shows its posts at the left beside the parked trucks under the trees, the
            # verge between it and the lane open dirt; traced on the tree line's lane-side edge on c20_s4400 / c20_p0180
            # (stage3_evidence/fence_r6.png): 20-27 m from the lane's paddock-side edge, not the round-4 1.0 m
            dict(name='pit entry paddock fence', kind='fence', h=1.5, fence=1.5, color='#9aa0a4',
                 h_src='person-ref on the pit-lane video t1231000-t1240000: chest-high mesh',
                 src='pit-lane video t1231000 (20:31): the mesh fence along the paddock boundary under the trees left of the pit entry; the line on the tree line lane-side edge, c20_s4400 / c20_p0180',
                 latlon=[[35.4895693, -119.5477186], [35.4894292, -119.5476259], [35.4893214, -119.5475333], [35.4892351, -119.5474141], [35.489192, -119.5473479]]),
            # round 8 (owner lap 2 note 12): the tyre wall round the OUTSIDE of the T2 hairpin, beyond the outer-loop pavement:
            # the CCW onboard _7QwJdGQtaE t286 / t288 shows a long black tyre wall there with the paddock buildings behind
            # it and cones on the pavement; traced on c20_s0700 / c20_s0750 (the dark band beyond the outer loop,
            # structure_stills/../stage3_evidence/t2tyres_r8.png, 115 m, the capture ends at its north-east end)
            dict(name='T2 outside tyre wall', kind='tyres', h=1.0, fence=0.0, color='#202020',
                 h_src='tyre-ref: stacks of about four tyres (0.25 m each) on the CCW onboard t286 / t288',
                 src='c20_s0700 / c20_s0750: the dark tyre band beyond the outer T2 loop; CCW onboard _7QwJdGQtaE t286 / t288 (black tyre wall behind the outer-loop pavement)',
                 latlon=[[35.4921475, -119.541314], [35.4921268, -119.5413669], [35.4920819, -119.5414221], [35.4920531, -119.5414729], [35.4920334, -119.5415236], [35.4920154, -119.5415677], [35.492001, -119.5416141], [35.4919849, -119.5416593], [35.4919687, -119.541709], [35.4919489, -119.5417531], [35.4919292, -119.5418016], [35.4919004, -119.5418458], [35.4918753, -119.5419009], [35.4918465, -119.5419517], [35.491798, -119.5420245], [35.4917513, -119.5420642], [35.4916965, -119.5420995], [35.4916381, -119.5421172], [35.4915717, -119.5421194], [35.4915088, -119.5420951], [35.4914657, -119.5420819]]),
            dict(name='T11 approach tree-line tyre barrier', kind='tyres', h=0.85, fence=0.0, color='#202020',
                 h_src='tyre-ref: three to four tyres high on the back view (judge r3 back_07, 0.7-1.0 m)',
                 src='c20_s4300 (stage3_evidence/tyre4200.png): a long dark tyre line under the trees ~27 m beyond the left edge at s ~4150-4260; judge r3 back_07 (looking back at 4200); onboard t136-t138 (dark line under the trees, left)',
                 latlon=[(35.4907449, -119.5480121), (35.490594, -119.5479922), (35.4904215, -119.5479724), (35.4902274, -119.5479393), (35.490055, -119.5478995), (35.4899256, -119.5478664), (35.4898394, -119.5478201)]),
        ],
        osm_barrier_overrides={},
        tyre_facings=None,
        impact_barriers=[
            dict(wall='pit wall, front straight', end='start', w=1.8, d=3.4, h=0.9, overlap=0.8, color='#e4dfd2', style='rounded',   # judge r5: wraps the wall's square end (one continuous nose with the station on it)   # judge r3: bulky, rounded, pale (pit video t1240000)
                 src='pit-lane video ucmXJu5QKFQ 20:40 (t1240000): a sand / dirt berm piled against the pit wall head where the pit-in lane meets it; onboard s4500 / t148: the wall head low and light ahead left'),
        ],
        tyre_stacks=[],
        blocks=[
            dict(latlon=[(35.4918004, -119.5416784), (35.4918179, -119.5416483)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4918179, -119.5416483), (35.49183, -119.5416142)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.49183, -119.5416142), (35.4918432, -119.5415824)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4918432, -119.5415824), (35.4918561, -119.5415506)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4918561, -119.5415506), (35.4918676, -119.5415186)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4918676, -119.5415186), (35.4918802, -119.541487)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4918802, -119.541487), (35.491894, -119.5414555)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.491894, -119.5414555), (35.4919084, -119.5414234)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4919084, -119.5414234), (35.4919223, -119.5413903)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4919223, -119.5413903), (35.4919364, -119.5413563)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4919364, -119.5413563), (35.4919525, -119.5413211)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4919525, -119.5413211), (35.4919666, -119.5412851)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4919666, -119.5412851), (35.491981, -119.541248)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.491981, -119.541248), (35.491996, -119.5412098)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.491996, -119.5412098), (35.4920109, -119.5411707)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
            dict(latlon=[(35.4920109, -119.5411707), (35.4920239, -119.5411312)], every=2.0, w=0.5, d=1.0, h=0.12, style='plain', color='#ecebe6',
                 src='the outer-loop block line beyond the T2 runoff (traced on the owner frame of c20_s0700 / c20_s0750; owner/t2_edges.json green ends); drawn only, not a track kerb'),
        ],
        # corner stations: a canopy roof on posts on a tyre-faced earth mound (the 'bunkers'); the station ledger in the manifest
        # judge r2 (GPT 6 Astra): the frames t020, t034, t040, t046, t058, t074, t082, t092, t112, t122, t138 show OPEN canopies on
        # four posts over the mounds, no walls: style 'canopy' (kit), mound ~1.2 m (person scale on t020 / t040), roof underside
        # 2.2 m over it; the starter's stand on the pit wall is a raised platform with railings and an access stair (pit video 22:19)
        marshal_posts=[
            dict(name='T1 exit', latlon=(35.4906672, -119.5410779), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#e8e6e0',  # judge r3: t020: a white cabinet with a club sign; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s0650: white roof 5.5 m2 in a dark tyre ring (compare/blob_scan.py, 0.4 m beyond the right edge at s 482); onboard t020 (0:20): canopy on posts on a tyre-faced mound close right; inventory s 477 right'),
            dict(name='T2 to T3, east side', latlon=(35.4904386, -119.5402123), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2b4a78',  # judge r3: t034: a blue cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s0600: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 7.1 m beyond the right edge at s 820); onboard t034 (0:34): blue canopy on a tyre-faced mound ahead right; inventory s 834 right'),
            dict(name='T3', latlon=(35.4888477, -119.5394518), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#3a4350',  # judge r3: t040: a dark cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s1150: white roof 5.6 m2 in a dark tyre ring (compare/blob_scan.py, 9.2 m beyond the right edge at s 1014); onboard t040 (0:40): blue canopy on posts on a tyre-faced mound close right; inventory s 996 right'),
            dict(name='T4', latlon=(35.4875581, -119.5395534), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2f3a48',  # judge r3: t046: a dark cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s1300: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.6 m beyond the right edge at s 1173); onboard t046 (0:46): canopy on posts ahead right; inventory s 1186 right'),
            dict(name='T5', latlon=(35.4868397, -119.5421342), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#e8e6e0',  # judge r3: t058: a white cabinet with a sign; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s1550: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.8 m beyond the right edge at s 1492); onboard t058 (0:58): canopy on a tyre-faced mound right; inventory s 1524 right'),
            dict(name='T6 (Riverside)', latlon=(35.4865323, -119.5477238), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#d9d6cf',  # judge r3: t074: a pale cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s2150: white roof 6.3 m2 in a dark tyre ring (compare/blob_scan.py, 10.4 m beyond the right edge at s 2069); onboard t074 (1:14): canopy on a tyre-faced mound ahead right; inventory s 2050 right'),
            dict(name='T7', latlon=(35.487615, -119.5496824), h=4.4, color='#7fa6d6', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2f3a48',  # judge r3: t082: a dark cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s2500: white roof 5.9 m2 in a dark tyre ring (compare/blob_scan.py, 19.2 m beyond the right edge at s 2358); onboard t082 (1:22): canopy on a mound ahead right; inventory s 2372 right'),
            dict(name='T8', latlon=(35.4910638, -119.5506143), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2b3f66',  # judge r3: t092 (judge r3): a dark blue body; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s2900: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 9.8 m beyond the right edge at s 2764); onboard t092 (1:32): canopy on posts ahead right; inventory s 2776 right'),
            dict(name='north leg before T9', latlon=(35.4946878, -119.5493983), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2f3a48',  # judge r3: no frame: the common dark cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s3300: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 11.0 m beyond the right edge at s 3189); onboard not in the 2 s frames (t106-t108 look past it); roof and tyre ring on c20_s3300 / c20_s3350'),
            dict(name='T9 (Star Mazda)', latlon=(35.4964593, -119.5491351), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2f3a48',  # judge r3: t112: a dark cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s3500: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 13.6 m beyond the right edge at s 3420); onboard t112 (1:52): roofed platform on stilts ahead right; inventory s 3436 right'),
            dict(name='T10', latlon=(35.4946445, -119.5481763), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2f3a48',  # judge r3: t122: a dark cabinet; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s3800: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 15.4 m beyond the right edge at s 3698); onboard t122 (2:02): station far ahead right; inventory s 3758 right'),
            dict(name='T11 approach (Sunset)', latlon=(35.4896673, -119.5480246), h=4.4, color='#cfd4d8', style='canopy', mound_h=0.9, base_color='#cfc6b2', pole=True, body_h=1.6, body_color='#2f3a48',  # judge r3: t138: a dark cabinet on a pale round base; a pale round base and a canopy on one pole (zoomed frames, stage3_evidence/station_crops.jpg)
                
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s4350: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 5.0 m beyond the left edge at s 4272); onboard t138 (2:18): canopy on a tyre-faced mound ahead left; inventory s 4274 left'),
            # judge r5 pit_01 4490 R: on t1231000 / t1240000 the station stands ON the broad concrete head of the separation
            # barrier, one continuous end with the berm; moved from 1.7 m beside the wall onto its line, 1.6 m from its start
            dict(name='pit-in station', latlon=(35.4887475, -119.5465999), h=3.9, w=2.0, color='#cfd4d8', style='canopy', mound_h=0.5,
                 base_color='#cfc6b2', pole=True, body_h=1.2, body_color='#e8e6e0',
                 h_src='person-ref against the pit-wall K-rail (0.81 m) on the pit-lane video t1240000',
                 src="pit-lane video ucmXJu5QKFQ 20:40 (t1240000): a canopy on one pole over a small white 'CAC CLUB' cabinet on a pale base at the pit-wall head (judge r3 pit_00, the entry shelter); c20_s4550 / c20_s4600: the white roof at the wall head (compare/blob_scan.py, s 4511 left 8.5 m); pit row s 4320 corrected to 4508"),
            dict(name='T1 inside canopy', latlon=(35.4893951, -119.5418382), h=2.8, w=5.0, color='#e8e6e0', style='canopy', mound_h=0.3,
                 h_src='person-ref: a canopy on posts over a low concrete platform (onboard t010, ~one storey)',
                 src="c20_s0300 / c20_s0350: a white roof ~5 x 3 m among the trees inside T1, 42 m beyond the left edge at s 247 (compare/blob_scan.py; stage3_evidence/blob247.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60; judge r1 row)"),
            dict(name='pit-wall end hut', latlon=(35.4890197, -119.5423407), h=2.6, color='#e8e6e0', style='canopy', mound_h=0.3,
                 h_src='person-ref: a one-storey white hut with a canopy over a low concrete platform (onboard t010, people beside it)',
                 src="c20_s0300 / c20_s0350: white roof 7.8 m2 at the east end of the pit wall (compare/blob_scan.py, 5.2 m beyond the left edge at s 199; window stage3_evidence/cw_wallend.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60)"),
            dict(name="starter's stand", latlon=(35.4888807, -119.5445092), h=4.4, w=1.6, color='#e8e6e0', style='platform', stair=True, roof=True, fine=True,   # judge r5 side_13 4693 L: a fine scaffold frame on t1339000 (thin tubes, X braces, a thin roof on four thin posts)
                 # judge r3: a compact raised platform, deck ~1.8 m, rails, a ladder and a small canopy (pit video t1339000 / t1348000)
                
                 h_src='person-ref: people stand on its deck at about the wall-top-plus-3 m line (pit-lane video 22:19-22:28, t1339000 / t1348000)',
                 src="c20_s0050 / c20_s0100 / c20_s0150: the white structure on the pit wall at the timing line (blob_scan s 2, 3.4 m beyond the left edge); pit-lane video ucmXJu5QKFQ 22:19-22:28: the scaffold starter's stand with a canopy on the pit wall"),
        ],
        light_masts=[
            dict(latlon=(35.4981168, -119.5486443), h=49.5, style='lattice',   # judge r3: the head reads as a light cluster on the onboard (s3350 / t106); judge r5: a lattice tower, not a pole (fwd_11 3400 L)
                 src='OSM man_made=mast / communications tower node 10220517717; the lidar (CA_SanJoaquin_2021) has an isolated spike 49.5-49.7 m over the DEM there (30 cells, compare/stage3 lidar spike scan); onboard t106 (1:46): a tall thin pole far ahead on the north leg (inventory mast row s 3400 ahead, ahead_m 250)'),
        ],
        cone_lines_declared=[
            # single orange (and one yellow) marker cones at turn-ins and road mouths, as the onboard shows them
            # round 8 (owner lap 2 note 24): the t006 cones re-read; they replace the round-3 row at 0.8 m and the s 20 / 24 pair (the same cones)
            dict(side='right', s=(40, 41), off=3.8, spacing=4.0, size=0.7, color='#e8c21c', 
                 src='onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, orange, orange) in a line PARALLEL to the right edge ~3.8 m out on the shoulder at the front-straight crossover mouth (the vanishing-point ratio of all four 0.24: one line at one offset), not across it; this one yellow'),
            dict(side='right', s=(45, 46), off=3.8, spacing=4.0, size=0.7, color='#e6e4de', 
                 src='onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, orange, orange) in a line PARALLEL to the right edge ~3.8 m out on the shoulder at the front-straight crossover mouth (the vanishing-point ratio of all four 0.24: one line at one offset), not across it; this one white'),
            dict(side='right', s=(50, 51), off=3.8, spacing=4.0, size=0.7, 
                 src='onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, orange, orange) in a line PARALLEL to the right edge ~3.8 m out on the shoulder at the front-straight crossover mouth (the vanishing-point ratio of all four 0.24: one line at one offset), not across it; this one orange'),
            dict(side='right', s=(55, 56), off=3.8, spacing=4.0, size=0.7, 
                 src='onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, orange, orange) in a line PARALLEL to the right edge ~3.8 m out on the shoulder at the front-straight crossover mouth (the vanishing-point ratio of all four 0.24: one line at one offset), not across it; this one orange'),
            dict(side='right', s=(1914, 1915), off=1.5, spacing=4.0, size=0.7,
                 src='compare_sheets onboard s1900 (t 70.76): an orange cone beside the end of the right kerb (judge r3 1920 R)'),
            dict(side='right', s=(3199, 3200), off=1.5, spacing=4.0, size=0.7,
                 src='compare_sheets onboard s3200 (t 107.15): an orange cone at the right edge (judge r3 fwd_10 3200 R)'),
            # judge r2 (GPT 6 Astra + orchestrator): cones the frames show that the package lacked (positions along the track
            # from the frame's time map, +-15 m)
            # (round 8, owner lap 2 note 24 'weird cones blocking nothing before T1': the 140-160 R line from t006-t008 is gone: t008 at
            # full resolution shows small dark posts beyond the edge there, no orange cones; the t006 cones are the s 40-55 row above)
            dict(side='left', s=(895, 905), off=1.5, spacing=5.0, size=0.7,
                 src='onboard t036 (judge r2, fwd_02 / fwd_03): orange cones on the left'),
            dict(side='right', s=(1780, 1830), off=3.0, spacing=6.0, size=0.7,
                 src='onboard t066-t068 (judge r2, fwd_06): a long line of cones separating the adjacent pavement (the Dog Leg / crossover mouth) on the right'),
            dict(side='left', s=(3250, 3300), off=1.5, spacing=8.0, size=0.7,
                 src='onboard t108-t110 (judge r2, fwd_10 / fwd_11): orange cones along the left'),
            dict(side='right', s=(3645, 3655), off=1.5, spacing=5.0, size=0.7,
                 src='onboard t122 (judge r2, fwd_12): orange cones on the right'),
            # judge r3 (EXTRA): the long pit-lane cone runs are dropped; the pit video t1303000 (21:43) shows a few yellow cones at
            # the timing tower's foot by the paddock-side K-rail, none along the walls
            # judge r5 (round 6): the pit-lane cones from the frames. t1267000 (21:07) shows a row of small orange cones along
            # the paddock-side (left) wall ahead of the tower, at the wall foot, about 10 m apart (abeam s ~4600-4660);
            # t1312000 (21:52) / t1339000 two at the tower's foot, one yellow, one orange. Replaces round 4's three yellow
            dict(latlon=[(35.4889724, -119.5455606), (35.489007, -119.5450089)], spacing=10.0, size=0.46,
                 src='pit-lane video t1267000 (21:07): six small orange cones along the left (paddock-side) wall ahead of the tower, at the wall foot (0.4 m off it, at the edge of the lane paving, which now stops 0.3 m short of the wall; the pit-connectivity gate keeps the lane itself clear), ~10 m apart (judge r5 pit_01 / pit_02)'),
            dict(latlon=[(35.4890292, -119.5446559), (35.4890294, -119.5446504)], spacing=4.0, size=0.46, color='#c6e21e',
                 src='pit-lane video t1312000 / t1339000: the fluorescent yellow-green cone at the tower foot (judge r8: t1312000), 0.4 m off the paddock-side wall'),
            dict(latlon=[(35.4890306, -119.5446117), (35.4890308, -119.5446062)], spacing=4.0, size=0.46,
                 src='pit-lane video t1312000 / t1339000: the orange cone beside it at the tower foot'),
            # judge r1 (orchestrator, 20 Oct 2026): cones the onboard shows that the package lacked; placed from the frames
            # at the sheet stations (temporary items, absent on the 2026 captures; along-track position +-15 m)
            dict(side='left', s=(752, 772), off=3.0, spacing=4.0, size=0.45,
                 src='onboard t030 / compare_sheets s0700, s0750 (fwd_02, side_02): a line of small orange cones on the pale apron left of the T2 approach (inventory cone_line row s 770 left, ahead_m 80); the "3-4 cones" of s0700 are this line seen from 60 m back'),
            dict(side='left', s=(3198, 3202), off=2.0, spacing=4.0, size=0.7,
                 src='compare_sheets s3200 (fwd_10): orange cones at a mouth on the left; judge r5 fwd_10 3200 L: onboard t108 shows two (was three)'),
            dict(side='right', s=(4046, 4054), off=3.0, spacing=4.0, size=0.7,
                 src='compare_sheets s4050 (fwd_13): cones on the right apron, 20 m before the t134 cone at s 4071'),
            dict(side='right', s=(297, 298), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t012.jpg (orange; inventory s 297 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='left', s=(533, 534), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t022.jpg (orange; inventory s 533 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='left', s=(834, 835), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t034.jpg (orange; inventory s 834 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='left', s=(973, 974), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t038.jpg (orange; inventory s 973 left: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='right', s=(1040, 1041), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t042.jpg (orange; inventory s 1040 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='right', s=(1307, 1308), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t052.jpg (orange; inventory s 1307 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='right', s=(2158, 2159), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t078.jpg (orange; inventory s 2158 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='left', s=(2696, 2700), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t092.jpg (orange; inventory s 2696 left: two orange cones); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='right', s=(3439, 3440), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t114.jpg (orange; inventory s 3439 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='right', s=(4071, 4072), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t134.jpg (orange; inventory s 4071 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='right', s=(4575, 4576), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t002.jpg (orange; inventory s 4575 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
            dict(side='right', s=(4593, 4594), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t150.jpg (orange; inventory s 4593 right: single orange cone); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
        ],
        pit_exit_cones=dict(draw=False, src='no cones on the pit-out merge (onboard 0:18-0:22, t018-t022; captures c20_s0600 / c20_s0650)'),
        paint_lines_declared=[],
        edge_line_cut=[],
        wall_boards=[],
        bridge_banners={},
        ground_signs=[],
        bridge_stairs=False,
        # paved roads of the circuit the Lemons loop does not use: driveable pavement (SKILL 3.6), the parts inside the
        # track dropped by the builder; surface from the captures (the front-straight crossovers pale concrete on
        # c20_s0150 / c20_s0200 / c20_s4600, the rest grey asphalt); no painted edges (none on the captures); cones only at
        # the mouths the onboard shows coned (t006: two cones at the 34351026 mouth; t002: an orange cone at Pacific's)
        # judge r2 (C17): the crossovers drew much paler than the track (surface concrete, from the pale captures) where the
        # onboard (t002-t006, t150-t152, t066-t068) shows a modest difference: the onboard outranks the captures, so they
        # take the asphalt tone
        closed_roads=[
            # round 8 (owner lap 2 note 15): the paddock lanes (OSM service parking aisles / driveways inside the paddock,
            # Slow Ln and the rows; confirmed on the 2026 z20 paddock captures satellite_paddock/pad_0..pad_7), paved in
            # the paddock's pale tone; none meets the track (no mouths, no cones); the ones beside the pit lane left out
            dict(name='paddock lanes', ways=['10409812', '10409813', '10419514', '39224594', '39224625', '765811048', '765811049',
                                             '765811050', '765811051', '765811052', '765811053', '765811055'],
                 half_width=4.0, surface='apron', mouth_cones=[],
                 src='OSM service ways in the paddock; satellite_paddock/pad_0-pad_7 (2026 z20, headless maps captures)'),
            dict(name='front-straight crossover (OSM 34351026)', ways=['34351026'], half_width=4.0, surface='asphalt',
                 mouth_cones=[],   # the onboard's cones at its mouth (t006) are the cone_lines_declared entry at s 20-24 right
                 src='OSM 34351026; c20_s0150 / c20_s0200: pale concrete road south from the front straight'),
            dict(name='Atlantic (OSM 34351042)', ways=['34351042'], half_width=4.0, surface='asphalt',
                 mouth_cones=[dict(near=(35.4888057, -119.5425265), src='judge r3 runoff_01 (s 170 R): a clear row of cones closing the paved branch; onboard t010-t012')],
                 src='OSM 34351042; c20_s0250 / c20_s0300: pale concrete road south-west from the front straight'),
            dict(name='Pacific (OSM 34350988)', ways=['34350988'], half_width=4.0, surface='asphalt',
                 mouth_cones=[],   # judge r3 (4573 R EXTRA): the r2 mouth cones made the 4575 / 4593 singles read as one spaced line where the onboard (t002, t150) shows a single cone; dropped   # the onboard's cone at its mouth (t002) is the cone_lines_declared entry at s 4575 right
                 src='OSM 34350988; c20_s4650 / c20_s4700: pale concrete road south from the front straight'),
            dict(name='crossover (OSM 34351015)', ways=['34351015'], half_width=4.0, surface='asphalt',
                 mouth_cones=[dict(near=(35.487584, -119.5454944), src='onboard t068 (judge r2 runoff_02, s 1824 R): cones across the crossover mouth')],
                 src='OSM 34351015; c20_s0000 / c20_s0050: pale concrete road south from the front straight'),
            # surface 'apron' (judge r5 runoff_04 623 R): the unused loop is the pale weathered pavement of the onboard, the same
            # look as the T2 runoff that overlaps it (one material: no tone band where the two zones meet)
            dict(name='outer T2 loop (OSM 39224609)', ways=['39224609'], half_width=5.5, surface='apron', mouth_cones=[],
                 src='OSM 39224609; c20_s0700 / c20_s0750 / c20_s0800: the outer hairpin road round the T2 pond, asphalt with white kerb blocks'),
            dict(name='Dog Leg (OSM 39224483, west of the T5 turn)', ways=['39224483:469884764:393994724'], half_width=5.5, surface='asphalt', mouth_cones=[],
                 src='OSM 39224483; c20_s1650 .. c20_s2100: the straight asphalt road the course leaves at T5 and rejoins after Truck Stop'),
            dict(name='Sweeper (OSM 34351309)', ways=['34351309'], half_width=5.5, surface='asphalt', mouth_cones=[],
                 src='OSM 34351309; c20_s3350 .. c20_s3600: the inner loop inside Star Mazda'),
            dict(name='Zorros Corners (OSM 34351301)', ways=['34351301'], half_width=5.5, surface='asphalt', mouth_cones=[],
                 src='OSM 34351301; c20_s4250 / c20_s4300: the road from the drag strip to Sunset'),
            dict(name='drag strip, south part (OSM 34351305)', ways=['34351305:469886349:469885942'], half_width=6.0, surface='asphalt', mouth_cones=[],
                 src='OSM 34351305; c20_s2600 .. c20_s3000: the straight the course leaves for Lost Hill'),
        ],
        closed_roads_clip_walls=False,
        # the T2 runoff (round 5): the owner marked it as legitimate pavement (green end lines, owner/t2_edges.json): "a car can
        # legally go all the way up to the outside kerb at T2, it's used as a run-off in the Lemons configuration"; a drivable
        # zone from the fitted left edge (his red line) out to the outer-loop block line between his two green lines
        # judge r5 (round 6): NAIP marks on the fitted road painted over in the ortho (stage 3; outlines measured on the
        # package ortho, stage3_evidence/smears_r6.jpg); only road pixels brighter than the road's median there change
        ortho_paint_over=[
        # round 8 cp5: the boundary-audit seam rows (boundary_sheets/, the poses named in each src): ortho patches, 12 m boxes on the boundary point
            dict(latlon=[(35.4887457, -119.5467111), (35.4887457, -119.5465787), (35.4888535, -119.5465787), (35.4888535, -119.5467111)], on='any', dark=True, src='boundary audit: the dark blotch on the ground beside the pit lane (right, ~175 m along it) (pit_pit-right_0175)'),
            dict(latlon=[(35.4888773, -119.543736), (35.4888773, -119.5436036), (35.4889851, -119.5436036), (35.4889851, -119.543736)], on='any', all=True, src='boundary audit: the green-toned ground beside the pit-wall K-rail (front straight, pale strip west ~75 m) (zone_front-straight-pal-left_0075)'),
            dict(latlon=[(35.4876109, -119.5438109), (35.4876109, -119.5436785), (35.4877187, -119.5436785), (35.4877187, -119.5438109)], on='any', src='boundary audit: the yellow-tan NAIP patch on the front-straight crossover (left, ~125 m) (zone_front-straight-cro-left_0125)'),
            dict(latlon=[(35.4871503, -119.5458944), (35.4871503, -119.545762), (35.4872581, -119.545762), (35.4872581, -119.5458944)], on='any', dark=True, src='boundary audit: the dark brown ground patch at the Dog Leg (left edge ~1900) (edge_L_1900)'),
            # round 8 (owner lap 2 note 19): the dark diagonal stripe across the road on the Cotton approach is a DARK NAIP mark
            # at ~s 1095 (the round-7 paint-over there recolours bright marks only and matches the road median); painted over
            dict(latlon=[(35.4886311, -119.5394737), (35.4886311, -119.5393523), (35.4885143, -119.5393523), (35.4885143, -119.5394737)], dark=True, src='owner lap 2 note 19: the dark diagonal NAIP mark on the road at ~s 1095 (stage3_evidence/stripe1100_r8.png)'),
            # judge r6 (round 7): the NAIP yellow hatch in the pit-entry gore (pit_00 4294-4318 R, open since r2) and the
            # chevrons at the drag-strip crossing (fwd_08 2550 R, open since r3), off the road: on='any'
            dict(latlon=[(35.4895828, -119.5481191), (35.4895828, -119.5478764), (35.4893133, -119.5478764), (35.4893133, -119.5481191)], on='any', tone='road', src='pit_00 4294-4318 R: the NAIP 2022 yellow hatch in the gore between the track and the pit-entry lane; round 8 (owner lap 2 note 7): recoloured to the road tone (the gore is paved, pit video t1231000); the hatch paint itself left out'),
            dict(latlon=[(35.4895702, -119.5499307), (35.4895702, -119.549688), (35.4892558, -119.549688), (35.4892558, -119.5499307)], on='any', src='fwd_08 2550 R: the NAIP chevrons on the drag-strip crossing'),
            dict(latlon=[(35.491772, -119.5503996), (35.491772, -119.5503003), (35.4916552, -119.5503003), (35.4916552, -119.5503996)], src='fwd_09 2800-2850 L: a broad white mark on the road (NAIP 2022)'),
            dict(latlon=[(35.491251, -119.5507086), (35.491251, -119.5506313), (35.4911791, -119.5506313), (35.4911791, -119.5507086)], src='the same stretch, the second mark at s ~2850'),
            dict(latlon=[(35.4883332, -119.5396337), (35.4883332, -119.5395454), (35.4880727, -119.5395454), (35.4880727, -119.5396337)], src='T4 ~1100: the NAIP kerb blocks now inside the owner-traced right edge'),
            dict(latlon=[(35.4875418, -119.539456), (35.4875418, -119.5394009), (35.4874789, -119.5394009), (35.4874789, -119.539456)], src='T4 exit ~1203: NAIP blocks on the road (first)'),
            dict(latlon=[(35.4873891, -119.5394229), (35.4873891, -119.5393457), (35.4872813, -119.5393457), (35.4872813, -119.5394229)], src='T4 exit ~1203: NAIP blocks on the road (second)'),
        ],
        aprons_meet_road=True,   # judge r6 back_05 3000: the apron outlines clipped to the road, no fade along the road edge (no tan bites)
        # round 8 (owner lap 2 note 16, the big willows T9 -> T11): the NAIP canopy check rejected 243 of 273 lidar crowns, the
        # infield tree rows among them; off, with a minimum crown instead (poles, masts, fence posts have no 3 m crown)
        tree_imagery_check=False, tree_min=dict(radius=3.0, height=6.0),
        # round 8 (owner lap 2 note 18): the crack-seal lines measured on the clean captures (build_scenery.surface_marks)
        surface_marks=dict(max=1200, min_len=3.0, contrast=9),   # cp5: 14 -> 9 (111 marks did not show at hood level)
        zone_end_feather=True,   # judge r8 (cp6): the square-cut paved-zone ends on the dirt (1800 R, 3600 R) fade out
        zones_meet_edge=True,    # judge r5: the crossover mouths (side_00 21 / 46 / 146 R, fwd_15 4600-4650 R) showed a dirt wedge between the zone's end and the edge
        paved_zones_over=True,   # texture pass (owner lap 1): the crossovers and the T2 runoff drew dirt blotches where the track's / a neighbour zone's shoulder lay over them (structure_stills/textures_r5)
        runoff_zones=[
            # round 8 (owner lap 2 note 23): the pale paved strip between the front straight's dark racing surface and the
            # pit-wall K-rail (c20_s4600-c20_s0250): pavement, not racing surface; from the new left edge out to the
            # K-rail's line (the declared wall), two pieces either side of the lap's start
            dict(name='front straight pale strip west', side='left', s=(4536, 4700), surface='apron', outer_latlon=[(35.4887467, -119.5466176), (35.4887756, -119.5463925), (35.4887872, -119.5461735), (35.4887997, -119.5459532), (35.4888121, -119.5457331), (35.4888245, -119.545513), (35.4888375, -119.5452929), (35.4888504, -119.5450728), (35.4888629, -119.5448526), (35.4888756, -119.5446326), (35.4888859, -119.5445371), (35.4888939, -119.5443166), (35.4889064, -119.5440964), (35.4889189, -119.5438763), (35.488932, -119.5436563), (35.4889447, -119.5434362), (35.4889573, -119.543216), (35.4889707, -119.542996), (35.4889828, -119.5427758), (35.4889963, -119.5425558), (35.4890124, -119.542336), (35.4890148, -119.5422713)],
                 src='c20_s4550-c20_s4650: the pale paved strip between the dark track and the pit-wall K-rail (owner lap 2 note 23, his map mark-up)'),
            dict(name='front straight pale strip east', side='left', s=(2, 190), surface='apron', outer_latlon=[(35.4887467, -119.5466176), (35.4887756, -119.5463925), (35.4887872, -119.5461735), (35.4887997, -119.5459532), (35.4888121, -119.5457331), (35.4888245, -119.545513), (35.4888375, -119.5452929), (35.4888504, -119.5450728), (35.4888629, -119.5448526), (35.4888756, -119.5446326), (35.4888859, -119.5445371), (35.4888939, -119.5443166), (35.4889064, -119.5440964), (35.4889189, -119.5438763), (35.488932, -119.5436563), (35.4889447, -119.5434362), (35.4889573, -119.543216), (35.4889707, -119.542996), (35.4889828, -119.5427758), (35.4889963, -119.5425558), (35.4890124, -119.542336), (35.4890148, -119.5422713)],
                 src='c20_s0050-c20_s0250: the pale paved strip between the dark track and the pit-wall K-rail (owner lap 2 note 23, his map mark-up)'),
            # surface 'apron' (judge r5): pale weathered asphalt with grain, the look of the aprons and of the outer T2 loop
            # it overlaps (round 5's 'asphalt' cut a dark band across the pale pavement, runoff_04 623 R)
            dict(name='T2 runoff', side='left', s=(605, 640), surface='apron', outer_latlon=[(35.4916435, -119.5418451), (35.4918004, -119.5416784), (35.4918179, -119.5416483), (35.49183, -119.5416142), (35.4918432, -119.5415824), (35.4918561, -119.5415506), (35.4918676, -119.5415186), (35.4918802, -119.541487), (35.491894, -119.5414555), (35.4919084, -119.5414234), (35.4919223, -119.5413903), (35.4919364, -119.5413563), (35.4919525, -119.5413211), (35.4919666, -119.5412851), (35.491981, -119.541248), (35.491996, -119.5412098), (35.4920109, -119.5411707), (35.4920239, -119.5411312), (35.4919238, -119.5410508)],
                 src="owner/t2_edges.json (the owner's green end lines, s 579-608 and 635-647) and the outer-loop block line traced on the owner's frame of the 2026 capture (white blocks 12-34 m left, s 608-642; c20_s0700 / c20_s0750)"),
        ],
        paved_areas=[
            # (the 'pit entry strip' paved area is gone, round 5 texture pass: the pit lane, paved to its walls since round 4,
            # covers 99.8 % of it (499 of 501 m2), and the strip drew a flat untextured grey slab over the lane's asphalt,
            # judge r4's near-black before that; structure_stills/textures_r5/area_pit_entry_strip_*)
            # round 8 (owner lap 2 note 17): the pale smooth concrete slab beside the T2 inside kerb at the hairpin exit (his map
            # arrow; the third onboard XIxXIvsDz3s t=475 shows it between the kerb and the dark asphalt): the pale component
            # beside the kerb on c20_s0700 (stage3_evidence/t2patch_r8.png, 7.6 m2; the part under the parked car not resolved)
            dict(name='T2 concrete patch', surface='concrete', look='concrete', latlon=[[35.4915506, -119.5416408], [35.4915478, -119.541639], [35.491576, -119.5416192], [35.4915894, -119.5416055], [35.4916028, -119.5415961], [35.4916275, -119.5415666], [35.491634, -119.5415702], [35.4916311, -119.5415763], [35.4916184, -119.5415874], [35.4916146, -119.5415958], [35.4916076, -119.5416], [35.4916038, -119.5416072], [35.4915978, -119.5416094], [35.4915743, -119.5416284], [35.4915506, -119.5416408]],
                 src='c20_s0700 pale slab beside the T2 inside kerb; owner map owner_lap2_t2_concrete_patch_map.png; onboard XIxXIvsDz3s t=475'),
            # round 8 (owner lap 2 notes 7 / 9): the pit-in gore is paved (pit video t1231000: plain asphalt with the painted hatch);
            # the ortho shows dirt in part of it: a paved area in the lane's measured tone over the hatch outline
            dict(name='pit-in gore', surface='asphalt', look='lane', latlon=[[35.4895828, -119.5481191], [35.4895828, -119.5478764], [35.4893133, -119.5478764], [35.4893133, -119.5481191]],
                 src='pit-lane video t1231000: the paved gore between the track and the pit-in lane; outline = the round-7 hatch paint-over outline (stage3_evidence/hatch_chevrons_r7.jpg)'),
            dict(name='apron left s 1305-1456', surface='apron', latlon=[[35.4865724, -119.5400424], [35.4865658, -119.5400664], [35.4865602, -119.5400906], [35.4865555, -119.5401149], [35.4865517, -119.5401392], [35.4865487, -119.5401635], [35.4865464, -119.5401877], [35.4865448, -119.5402117], [35.4865437, -119.5402356], [35.4865432, -119.5402593], [35.4865431, -119.5402828], [35.4865434, -119.5403061], [35.486544, -119.5403293], [35.4865448, -119.5403523], [35.4865458, -119.5403751], [35.486547, -119.5403978], [35.4865481, -119.5404203], [35.4865494, -119.5404428], [35.4865506, -119.5404652], [35.4865519, -119.5404876], [35.4865531, -119.5405099], [35.4865542, -119.5405322], [35.4865553, -119.5405545], [35.4865563, -119.5405768], [35.4865572, -119.5405991], [35.4865581, -119.5406214], [35.4865589, -119.5406436], [35.4865597, -119.5406659], [35.4865604, -119.5406882], [35.4865611, -119.5407105], [35.4865617, -119.5407328], [35.4865624, -119.5407551], [35.486563, -119.5407773], [35.4865637, -119.5407996], [35.4865644, -119.5408218], [35.4865651, -119.5408439], [35.4865659, -119.540866], [35.4865667, -119.5408881], [35.4865676, -119.5409101], [35.4865685, -119.540932], [35.4865695, -119.5409539], [35.4865706, -119.5409758], [35.4865718, -119.5409977], [35.486573, -119.5410195], [35.4865743, -119.5410413], [35.4865756, -119.5410631], [35.486577, -119.5410849], [35.4865784, -119.5411068], [35.4865798, -119.5411286], [35.4865813, -119.5411505], [35.4865828, -119.5411725], [35.4865842, -119.5411945], [35.4865857, -119.5412165], [35.4865872, -119.5412386], [35.4865886, -119.5412607], [35.48659, -119.5412828], [35.4865913, -119.541305], [35.4865926, -119.5413272], [35.4865939, -119.5413494], [35.4865951, -119.5413717], [35.4865962, -119.5413939], [35.4865972, -119.5414162], [35.4865982, -119.5414384], [35.486599, -119.5414607], [35.4865998, -119.5414829], [35.4866005, -119.5415051], [35.4866012, -119.5415273], [35.4866017, -119.5415494], [35.4866023, -119.5415715], [35.4866027, -119.5415936], [35.4866032, -119.5416155], [35.4866036, -119.5416375], [35.486604, -119.5416593], [35.4866044, -119.5416811], [35.4866048, -119.5417028], [35.4866052, -119.5417245], [35.4865905, -119.5417197], [35.4865887, -119.5416979], [35.4865868, -119.5416761], [35.4865849, -119.5416542], [35.4865828, -119.5416322], [35.4865806, -119.5416101], [35.4865784, -119.5415879], [35.4865762, -119.5415657], [35.486574, -119.5415435], [35.4865717, -119.5415212], [35.4865696, -119.5414989], [35.4865674, -119.5414766], [35.4865654, -119.5414544], [35.4865634, -119.5414322], [35.4865615, -119.54141], [35.4865596, -119.541388], [35.4865579, -119.541366], [35.4865563, -119.5413441], [35.4865547, -119.5413224], [35.4865532, -119.5413007], [35.4865518, -119.5412791], [35.4865504, -119.5412576], [35.4865491, -119.5412362], [35.4865478, -119.5412149], [35.4865465, -119.5411936], [35.4865452, -119.5411724], [35.4865438, -119.5411512], [35.4865424, -119.54113], [35.4865409, -119.5411088], [35.4865385, -119.5410769], [35.4865367, -119.5410557], [35.4865347, -119.5410344], [35.4865325, -119.5410131], [35.4865302, -119.5409918], [35.4865277, -119.5409704], [35.4865249, -119.5409489], [35.486522, -119.5409274], [35.4865189, -119.5409059], [35.4865157, -119.5408843], [35.4865123, -119.5408626], [35.4865088, -119.5408408], [35.4865052, -119.5408188], [35.4865016, -119.5407968], [35.4864979, -119.5407747], [35.4864943, -119.5407524], [35.4864907, -119.54073], [35.4864873, -119.5407074], [35.4864839, -119.5406846], [35.4864823, -119.5406732], [35.4864792, -119.5406501], [35.4864764, -119.540627], [35.4864738, -119.5406036], [35.4864716, -119.5405801], [35.4864697, -119.5405564], [35.4864683, -119.5405325], [35.4864677, -119.5405206], [35.4864668, -119.5404965], [35.4864665, -119.5404724], [35.4864666, -119.5404483], [35.4864673, -119.5404241], [35.4864684, -119.5403999], [35.4864702, -119.5403757], [35.4864724, -119.5403515], [35.4864753, -119.5403275], [35.4864787, -119.5403035], [35.4864827, -119.5402797], [35.4864872, -119.540256], [35.4864922, -119.5402325], [35.4864979, -119.5402092], [35.486504, -119.5401861], [35.4865107, -119.5401632], [35.486518, -119.5401405], [35.4865298, -119.540107], [35.4865384, -119.540085], [35.4865474, -119.5400632], [35.486557, -119.5400417]],
                 src='the T4-T5 apron beside the block line (cw_1348.png): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 9.6 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
            dict(name='apron left s 3701-3783', surface='apron', latlon=[[35.4946596, -119.5479004], [35.4946426, -119.5479067], [35.4946258, -119.5479128], [35.494609, -119.5479188], [35.4945923, -119.5479246], [35.4945758, -119.5479302], [35.4945594, -119.5479355], [35.4945431, -119.5479406], [35.4945268, -119.5479454], [35.4945107, -119.5479498], [35.4944946, -119.5479539], [35.4944786, -119.5479575], [35.4944626, -119.5479607], [35.4944466, -119.5479634], [35.4944306, -119.5479657], [35.4944147, -119.5479673], [35.4943987, -119.5479685], [35.4943826, -119.547969], [35.4943665, -119.5479689], [35.4943502, -119.5479682], [35.4943339, -119.5479669], [35.4943175, -119.547965], [35.494301, -119.5479625], [35.4942844, -119.5479595], [35.4942676, -119.5479559], [35.4942506, -119.5479518], [35.4942335, -119.5479473], [35.4942163, -119.5479424], [35.4941988, -119.5479373], [35.4941812, -119.547932], [35.4941633, -119.5479266], [35.4941452, -119.5479212], [35.4941268, -119.5479159], [35.4941082, -119.5479109], [35.4940893, -119.5479063], [35.4940702, -119.547902], [35.4940508, -119.5478983], [35.4940312, -119.5478953], [35.4940115, -119.547893], [35.4939915, -119.5478914], [35.4939714, -119.5478907], [35.4939513, -119.5478909], [35.493953, -119.5478732], [35.4939713, -119.5478684], [35.4939989, -119.5478617], [35.4940173, -119.5478575], [35.4940357, -119.5478537], [35.4940636, -119.5478485], [35.4940822, -119.5478454], [35.4941009, -119.5478427], [35.4941292, -119.5478393], [35.4941481, -119.5478375], [35.494167, -119.5478362], [35.4941861, -119.5478354], [35.4942051, -119.547835], [35.4942242, -119.5478352], [35.4942433, -119.5478359], [35.4942623, -119.5478371], [35.4942813, -119.5478388], [35.4942907, -119.5478398], [35.4943096, -119.5478422], [35.4943283, -119.547845], [35.4943376, -119.5478465], [35.4943469, -119.5478482], [35.4943561, -119.5478499], [35.4943653, -119.5478516], [35.4943836, -119.5478553], [35.4943926, -119.5478572], [35.4944106, -119.5478611], [35.4944196, -119.5478631], [35.4944374, -119.547867], [35.4944462, -119.5478689], [35.4944637, -119.5478726], [35.4944812, -119.5478761], [35.4944985, -119.5478793], [35.4945071, -119.5478808], [35.4945243, -119.5478834], [35.4945414, -119.5478856], [35.4945585, -119.5478872], [35.4945755, -119.5478883], [35.4946009, -119.5478888], [35.4946178, -119.5478884], [35.4946347, -119.5478874], [35.4946515, -119.5478858]],
                 src='the T10 apron east of the block line (t10b.png, ruler_t10.png): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 11.0 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
            dict(name='apron right s 356-512', surface='apron', latlon=[[35.4895399, -119.5409759], [35.4895589, -119.5409754], [35.4895778, -119.5409754], [35.4895966, -119.5409756], [35.4896152, -119.5409762], [35.4896338, -119.5409771], [35.4896523, -119.5409782], [35.4896707, -119.5409796], [35.4896891, -119.5409811], [35.4897074, -119.5409828], [35.4897257, -119.5409847], [35.4897441, -119.5409867], [35.4897625, -119.5409889], [35.489781, -119.5409912], [35.4897995, -119.5409937], [35.4898181, -119.5409965], [35.4898367, -119.5409995], [35.4898553, -119.5410027], [35.489874, -119.5410062], [35.4898926, -119.54101], [35.4899112, -119.541014], [35.4899297, -119.5410182], [35.4899481, -119.5410226], [35.4899663, -119.5410271], [35.4899843, -119.5410317], [35.4900021, -119.5410363], [35.4900198, -119.5410407], [35.4900372, -119.5410451], [35.4900545, -119.5410492], [35.4900716, -119.541053], [35.4900886, -119.5410566], [35.4901055, -119.5410598], [35.4901224, -119.5410628], [35.4901393, -119.5410654], [35.4901562, -119.5410677], [35.4901732, -119.5410698], [35.4901902, -119.5410716], [35.4902074, -119.5410732], [35.4902247, -119.5410747], [35.4902422, -119.5410761], [35.4902598, -119.5410775], [35.4902776, -119.5410788], [35.4902956, -119.5410803], [35.4903138, -119.5410819], [35.4903321, -119.5410837], [35.4903505, -119.5410857], [35.490369, -119.541088], [35.4903875, -119.5410906], [35.4904061, -119.5410936], [35.4904247, -119.5410969], [35.4904433, -119.5411005], [35.4904618, -119.5411045], [35.4904803, -119.5411088], [35.4904986, -119.5411134], [35.4905168, -119.5411182], [35.4905349, -119.5411232], [35.4905528, -119.5411284], [35.4905706, -119.5411337], [35.4905883, -119.5411391], [35.4906058, -119.5411445], [35.4906232, -119.5411498], [35.4906406, -119.5411551], [35.4906579, -119.5411603], [35.4906751, -119.5411653], [35.4906923, -119.5411702], [35.4907095, -119.5411748], [35.4907267, -119.5411793], [35.490744, -119.5411835], [35.4907613, -119.5411876], [35.4907787, -119.5411914], [35.4907962, -119.5411951], [35.4908138, -119.5411987], [35.4908315, -119.5412022], [35.4908494, -119.5412057], [35.4908675, -119.5412092], [35.4908857, -119.5412129], [35.4909041, -119.5412168], [35.4909226, -119.541221], [35.4909412, -119.5412257], [35.4909421, -119.5412084], [35.4909244, -119.5412012], [35.4909069, -119.5411942], [35.4908807, -119.5411841], [35.4908634, -119.5411774], [35.4908462, -119.5411708], [35.4908292, -119.5411641], [35.4908122, -119.5411573], [35.4907953, -119.5411505], [35.4907784, -119.5411435], [35.4907617, -119.5411364], [35.4907449, -119.5411291], [35.4907282, -119.5411217], [35.4907116, -119.5411142], [35.4906949, -119.5411066], [35.4906782, -119.5410988], [35.4906615, -119.541091], [35.4906449, -119.5410831], [35.4906282, -119.5410751], [35.4906114, -119.5410671], [35.4905947, -119.541059], [35.4905779, -119.541051], [35.4905611, -119.5410429], [35.4905443, -119.5410349], [35.4905275, -119.5410269], [35.4905106, -119.541019], [35.4904852, -119.5410073], [35.4904682, -119.5409996], [35.4904512, -119.540992], [35.4904342, -119.5409845], [35.490417, -119.5409771], [35.4903912, -119.5409663], [35.4903739, -119.5409593], [35.4903565, -119.5409525], [35.4903389, -119.5409458], [35.4903213, -119.5409393], [35.4903035, -119.5409331], [35.4902855, -119.540927], [35.4902674, -119.5409213], [35.4902491, -119.5409158], [35.4902307, -119.5409106], [35.4902214, -119.5409082], [35.4902027, -119.5409035], [35.4901839, -119.5408992], [35.4901744, -119.5408973], [35.490165, -119.5408954], [35.4901554, -119.5408936], [35.4901363, -119.5408904], [35.4901172, -119.5408876], [35.4901076, -119.5408863], [35.4900883, -119.5408842], [35.490069, -119.5408825], [35.4900594, -119.5408818], [35.4900401, -119.5408808], [35.4900209, -119.5408801], [35.4900016, -119.5408799], [35.4899824, -119.54088], [35.4899536, -119.540881], [35.4899345, -119.540882], [35.4899155, -119.5408835], [35.4898965, -119.5408852], [35.4898776, -119.5408873], [35.4898493, -119.540891], [35.4898306, -119.5408937], [35.489812, -119.5408968], [35.4897935, -119.5409001], [35.4897751, -119.5409036], [35.4897568, -119.5409072], [35.4897386, -119.5409111], [35.4897114, -119.5409171], [35.4896934, -119.5409213], [35.4896755, -119.5409255], [35.4896577, -119.5409298], [35.4896399, -119.5409341], [35.4896222, -119.5409385], [35.4896045, -119.5409429], [35.4895868, -119.5409473], [35.4895603, -119.5409539], [35.4895426, -119.5409583]],
                 src='the T1-exit apron east of the block line (cw_400ov.png, ruler_t1.png): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 15.7 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
            dict(name='apron right s 553-624', surface='apron', latlon=[[35.4912754, -119.5414674], [35.4912883, -119.541482], [35.4913012, -119.5414963], [35.4913143, -119.5415101], [35.4913275, -119.5415233], [35.491341, -119.541536], [35.4913548, -119.5415479], [35.4913688, -119.5415591], [35.4913832, -119.5415694], [35.491398, -119.5415787], [35.491413, -119.541587], [35.4914284, -119.5415941], [35.491444, -119.5416001], [35.4914599, -119.5416047], [35.4914759, -119.5416079], [35.4914921, -119.5416097], [35.4915082, -119.54161], [35.4915242, -119.5416088], [35.49154, -119.5416061], [35.4915554, -119.5416018], [35.4915705, -119.5415961], [35.491585, -119.5415889], [35.491599, -119.5415803], [35.4916122, -119.5415704], [35.4916246, -119.5415593], [35.4916362, -119.541547], [35.4916468, -119.5415337], [35.4916565, -119.5415194], [35.4916653, -119.5415044], [35.491673, -119.5414886], [35.4916796, -119.5414721], [35.4916853, -119.5414551], [35.49169, -119.5414377], [35.4916937, -119.5414199], [35.4916965, -119.5414018], [35.4916983, -119.5413834], [35.4916839, -119.5413886], [35.491679, -119.5414052], [35.4916732, -119.5414211], [35.4916663, -119.5414364], [35.4916586, -119.5414509], [35.4916499, -119.5414646], [35.4916452, -119.5414711], [35.4916353, -119.5414834], [35.4916245, -119.5414947], [35.491613, -119.541505], [35.491607, -119.5415097], [35.4915945, -119.5415183], [35.4915815, -119.5415259], [35.4915748, -119.5415292], [35.491561, -119.541535], [35.4915539, -119.5415375], [35.4915395, -119.5415415], [35.4915395, -119.5415415], [35.4915248, -119.5415444], [35.4915098, -119.5415462], [35.4915022, -119.5415466], [35.491487, -119.5415467], [35.4914717, -119.5415457], [35.491464, -119.5415448], [35.4914485, -119.5415422], [35.4914331, -119.5415386], [35.4914178, -119.541534], [35.4914025, -119.5415285], [35.4913874, -119.5415221], [35.4913724, -119.5415148], [35.4913576, -119.5415068], [35.4913429, -119.5414979], [35.4913284, -119.5414883], [35.491314, -119.5414781], [35.4912998, -119.5414672], [35.4912857, -119.5414557]],
                 src='the T2 hairpin inside patch (t2_595.png), worn edge (judge r3 side_02): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 5.8 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
            dict(name='apron right s 1165-1239', surface='apron', latlon=[[35.4876705, -119.5394633], [35.4876561, -119.5394571], [35.4876415, -119.5394517], [35.4876267, -119.5394469], [35.4876117, -119.5394429], [35.4875965, -119.5394396], [35.4875811, -119.5394372], [35.4875655, -119.5394355], [35.4875497, -119.5394346], [35.4875338, -119.5394345], [35.4875177, -119.5394352], [35.4875015, -119.5394367], [35.4874852, -119.539439], [35.4874689, -119.539442], [35.4874526, -119.5394458], [35.4874362, -119.5394504], [35.4874198, -119.5394556], [35.4874035, -119.5394615], [35.4873873, -119.5394681], [35.4873711, -119.5394752], [35.487355, -119.5394829], [35.487339, -119.5394912], [35.4873231, -119.5395], [35.4873073, -119.5395092], [35.4872917, -119.5395189], [35.4872762, -119.539529], [35.4872608, -119.5395394], [35.4872455, -119.5395503], [35.4872303, -119.5395614], [35.4872153, -119.5395729], [35.4872003, -119.5395847], [35.4871854, -119.5395967], [35.4871706, -119.5396089], [35.4871558, -119.5396213], [35.4871411, -119.5396339], [35.4871263, -119.5396467], [35.4871116, -119.5396595], [35.4870968, -119.5396723], [35.4871081, -119.5396845], [35.4871239, -119.5396739], [35.4871397, -119.5396633], [35.4871554, -119.5396528], [35.4871711, -119.5396425], [35.4871868, -119.5396323], [35.4872024, -119.5396222], [35.487218, -119.5396123], [35.4872336, -119.5396026], [35.4872492, -119.5395931], [35.4872649, -119.5395838], [35.4872805, -119.5395748], [35.4872961, -119.5395659], [35.4873118, -119.5395573], [35.4873275, -119.5395489], [35.4873433, -119.5395408], [35.4873591, -119.5395329], [35.4873749, -119.5395254], [35.4873907, -119.5395181], [35.4874065, -119.5395113], [35.4874224, -119.5395047], [35.4874383, -119.5394986], [35.4874542, -119.539493], [35.48747, -119.5394878], [35.4874859, -119.5394831], [35.4874859, -119.5394831], [35.4875017, -119.539479], [35.4875176, -119.5394755], [35.4875333, -119.5394727], [35.4875491, -119.5394705], [35.4875569, -119.5394697], [35.4875726, -119.5394686], [35.4875881, -119.5394683], [35.4876036, -119.5394687], [35.4876189, -119.53947], [35.4876342, -119.539472], [35.4876493, -119.5394749], [35.4876643, -119.5394786]],
                 src='the T4 apron beyond the block line (k22_1175.png): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 4.4 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
            dict(name='apron right s 2963-3025', surface='apron', latlon=[[35.4926068, -119.5497827], [35.4926232, -119.5497735], [35.4926396, -119.5497642], [35.4926561, -119.5497547], [35.4926727, -119.5497453], [35.4926894, -119.5497358], [35.4927063, -119.5497264], [35.4927233, -119.549717], [35.4927404, -119.5497079], [35.4927577, -119.5496989], [35.4927752, -119.5496903], [35.4927928, -119.5496819], [35.4928106, -119.5496739], [35.4928285, -119.5496662], [35.4928466, -119.549659], [35.4928648, -119.5496521], [35.492883, -119.5496457], [35.4929013, -119.5496396], [35.4929196, -119.5496339], [35.492938, -119.5496286], [35.4929563, -119.5496235], [35.4929746, -119.5496187], [35.4929928, -119.5496141], [35.493011, -119.5496097], [35.493029, -119.5496054], [35.493047, -119.5496012], [35.4930649, -119.549597], [35.4930827, -119.5495929], [35.4931005, -119.5495887], [35.4931182, -119.5495846], [35.4931358, -119.5495804], [35.4931535, -119.5495763], [35.4931491, -119.5495592], [35.4931314, -119.5495602], [35.4931137, -119.549561], [35.4930958, -119.5495619], [35.4930778, -119.5495626], [35.4930596, -119.5495635], [35.4930412, -119.5495645], [35.4930227, -119.5495657], [35.4930039, -119.5495672], [35.4929849, -119.5495691], [35.4929657, -119.5495715], [35.4929464, -119.5495745], [35.4929269, -119.5495782], [35.4929073, -119.5495827], [35.4928976, -119.5495852], [35.492878, -119.5495909], [35.4928586, -119.5495974], [35.4928393, -119.5496048], [35.4928202, -119.5496131], [35.4928015, -119.5496221], [35.492783, -119.549632], [35.492765, -119.5496426], [35.4927474, -119.5496537], [35.4927302, -119.5496654], [35.4927134, -119.5496774], [35.4926971, -119.5496898], [35.4926811, -119.5497023], [35.4926654, -119.5497149], [35.49265, -119.5497274], [35.4926348, -119.5497399], [35.4926198, -119.5497521], [35.4926049, -119.5497641]],
                 src='the paved shoulder at the drag-strip rejoin (c20_s3100): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 5.0 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
            dict(name='apron right s 4133-4208', surface='apron', latlon=[[35.4909285, -119.5485117], [35.4909109, -119.5485084], [35.4908933, -119.5485052], [35.4908757, -119.5485018], [35.4908581, -119.5484984], [35.4908406, -119.548495], [35.490823, -119.5484915], [35.4908054, -119.5484879], [35.4907877, -119.5484843], [35.4907701, -119.5484807], [35.4907524, -119.548477], [35.4907347, -119.5484732], [35.4907169, -119.5484695], [35.4906991, -119.5484657], [35.4906813, -119.5484619], [35.4906635, -119.5484581], [35.4906456, -119.5484544], [35.4906277, -119.5484507], [35.4906098, -119.548447], [35.4905919, -119.5484433], [35.490574, -119.5484397], [35.4905562, -119.5484362], [35.4905383, -119.5484327], [35.4905204, -119.5484293], [35.4905025, -119.548426], [35.4904847, -119.5484228], [35.4904668, -119.5484196], [35.490449, -119.5484166], [35.4904312, -119.5484137], [35.4904134, -119.5484108], [35.4903956, -119.5484081], [35.4903778, -119.5484055], [35.49036, -119.5484031], [35.4903422, -119.5484007], [35.4903244, -119.5483984], [35.4903065, -119.5483963], [35.4902887, -119.5483943], [35.4902709, -119.5483923], [35.4902757, -119.548411], [35.4902931, -119.5484144], [35.4903106, -119.5484179], [35.4903279, -119.5484217], [35.4903453, -119.5484257], [35.4903626, -119.5484298], [35.49038, -119.5484342], [35.4903973, -119.5484387], [35.4904146, -119.5484435], [35.490432, -119.5484483], [35.4904495, -119.5484533], [35.4904669, -119.5484584], [35.4904845, -119.5484635], [35.4905021, -119.5484686], [35.4905199, -119.5484737], [35.4905377, -119.5484788], [35.4905557, -119.5484837], [35.4905738, -119.5484885], [35.490592, -119.548493], [35.4906103, -119.5484973], [35.4906287, -119.5485014], [35.4906472, -119.5485052], [35.4906657, -119.5485086], [35.4906843, -119.5485117], [35.4906936, -119.5485131], [35.4907122, -119.5485157], [35.4907215, -119.5485168], [35.49074, -119.5485189], [35.4907585, -119.5485206], [35.4907769, -119.5485221], [35.4907951, -119.5485233], [35.4908134, -119.5485242], [35.4908315, -119.5485249], [35.4908495, -119.5485256], [35.4908673, -119.5485261], [35.4908851, -119.5485265], [35.4909028, -119.548527], [35.4909205, -119.5485274]],
                 src='the Zorros Corners mouth fillet (c20_s4250): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 4.5 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
            dict(name='apron right s 4406-4529', surface='apron', latlon=[[35.4885797, -119.5477527], [35.4885746, -119.5477284], [35.4885703, -119.5477042], [35.4885666, -119.5476799], [35.4885635, -119.5476558], [35.4885609, -119.5476318], [35.4885588, -119.547608], [35.4885571, -119.5475843], [35.4885556, -119.5475609], [35.4885545, -119.5475377], [35.4885535, -119.5475146], [35.4885528, -119.5474917], [35.4885522, -119.547469], [35.4885517, -119.5474465], [35.4885514, -119.547424], [35.4885512, -119.5474017], [35.4885512, -119.5473795], [35.4885513, -119.5473574], [35.4885515, -119.5473353], [35.4885518, -119.5473133], [35.4885523, -119.5472913], [35.4885529, -119.5472693], [35.4885536, -119.5472473], [35.4885545, -119.5472252], [35.4885554, -119.5472032], [35.4885564, -119.547181], [35.4885575, -119.5471589], [35.4885587, -119.5471368], [35.4885599, -119.5471146], [35.4885612, -119.5470923], [35.4885625, -119.5470701], [35.4885638, -119.5470479], [35.4885652, -119.5470257], [35.4885666, -119.5470035], [35.488568, -119.5469813], [35.4885694, -119.5469592], [35.4885709, -119.5469371], [35.4885724, -119.5469151], [35.4885739, -119.5468932], [35.4885755, -119.5468713], [35.488577, -119.5468494], [35.4885786, -119.5468276], [35.4885802, -119.5468059], [35.4885818, -119.5467842], [35.4885833, -119.5467625], [35.4885848, -119.5467408], [35.4885861, -119.546719], [35.4885873, -119.5466973], [35.4885883, -119.5466755], [35.4885891, -119.5466536], [35.4885897, -119.5466317], [35.4885901, -119.5466097], [35.4885903, -119.5465877], [35.4885902, -119.5465655], [35.48859, -119.5465433], [35.4885896, -119.5465211], [35.488589, -119.5464987], [35.4885884, -119.5464763], [35.4885878, -119.5464538], [35.4885872, -119.5464313], [35.4885867, -119.5464088], [35.4885864, -119.5463862], [35.4885702, -119.5463928], [35.4885659, -119.5464116], [35.4885584, -119.5464396], [35.4885528, -119.5464583], [35.4885466, -119.5464772], [35.4885366, -119.5465059], [35.4885295, -119.5465254], [35.4885221, -119.5465452], [35.4885144, -119.5465655], [35.4885028, -119.546597], [35.4884952, -119.5466186], [35.4884915, -119.5466297], [35.4884843, -119.5466522], [35.4884775, -119.5466754], [35.4884712, -119.546699], [35.4884656, -119.5467232], [35.4884631, -119.5467354], [35.4884586, -119.5467601], [35.4884549, -119.546785], [35.4884533, -119.5467975], [35.4884509, -119.5468226], [35.4884492, -119.5468476], [35.4884486, -119.5468601], [35.488448, -119.546885], [35.488448, -119.5468974], [35.4884484, -119.546922], [35.4884494, -119.5469462], [35.4884508, -119.5469702], [35.4884526, -119.5469938], [35.4884547, -119.5470171], [35.488457, -119.5470402], [35.4884595, -119.5470629], [35.4884621, -119.5470853], [35.4884647, -119.5471075], [35.4884673, -119.5471295], [35.4884699, -119.5471514], [35.4884724, -119.5471731], [35.4884748, -119.5471947], [35.4884772, -119.5472163], [35.4884794, -119.5472378], [35.4884816, -119.5472594], [35.4884837, -119.547281], [35.4884857, -119.5473026], [35.4884878, -119.5473243], [35.4884898, -119.5473462], [35.4884919, -119.5473681], [35.4884941, -119.5473901], [35.4884964, -119.5474123], [35.4884988, -119.5474346], [35.4885014, -119.547457], [35.4885043, -119.5474795], [35.4885073, -119.5475021], [35.4885125, -119.5475362], [35.4885163, -119.5475589], [35.4885205, -119.5475817], [35.488525, -119.5476045], [35.4885299, -119.5476273], [35.4885352, -119.5476501], [35.488541, -119.5476728], [35.4885504, -119.5477067], [35.4885572, -119.5477292], [35.4885646, -119.5477515]],
                 src='the T11-exit apron south of the block line (cw_4430.png, ruler_t11.png): between the fitted edge and the run-20 asphalt-end edge (stations_ref.json), up to 14.2 m; the onboard shows broad paved aprons (judge r3 paved-apron rows)'),
        ],
        pit_lane_clip_walls=True,
        terraces=[],
        grandstand_on_terrain=False,
        building_height_robust=True,
        building_overrides=[
            dict(contains=(35.4893226, -119.5445323), plain=True,
                 src='OSM 765811056 behind the timing tower: plain white walls on the pit-lane video t1312000 / t1330000 (no window rows)'),
        ],
        building_evidence=[
            dict(contains=(35.4893364, -119.5445599), src='pit-lane video ucmXJu5QKFQ 21:52-22:10 (t1312000, t1330000): the two-storey timing tower with the blue roof beside the pit lane; OSM footprint, lidar height'),
            dict(contains=(35.4891529, -119.544572), src='pit-lane video ucmXJu5QKFQ 21:52-22:10 (t1312000, t1330000): the two-storey timing tower with the blue roof beside the pit lane; OSM footprint, lidar height'),
            dict(contains=(35.4896585, -119.5454773), drop=True, src='round 7: drawn as the structures item "paddock shade roof" (open, on posts) instead of a solid block; 29 x 8 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4897631, -119.5436739), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_2 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 28 x 7 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4900634, -119.545886), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_0 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 20 x 7 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4900867, -119.5455277), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_0 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 30 x 9 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4901442, -119.5443856), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_1 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 16 x 9 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4910066, -119.5464487), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_3 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 18 x 37 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4909536, -119.5459547), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_3 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 32 x 19 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4909886, -119.5453399), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_4 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 29 x 19 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4911432, -119.5449521), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_4 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 20 x 50 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4912851, -119.5454006), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_4 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 20 x 33 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4912087, -119.5451689), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_4 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 4 x 14 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4913637, -119.546265), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_3 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 60 x 18 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4915986, -119.543098), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_6 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 33 x 16 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4916938, -119.547039), src='round 8 (owner lap 2 note 15): confirmed on the 2026 z20 capture of the paddock satellite_paddock/pad_7 (headless maps capture; the earlier "no 2026 source" predates it); lidar (2021) footprint and height, plain; was: no 2026 source: 11 x 16 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4919274, -119.546024), drop=True, src='no 2026 source: 19 x 12 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
        ],
        season_tint=None,
        gates=dict(allowed=[
            dict(target='paddock lanes', side='left', a=(35.4899733, -119.5411053), b=(35.4915679, -119.541668),
                 why='round 8: the paddock lanes (pale paved closed road) lie 94-110 m beyond the edge across the infield dirt; OPEN: the infield chain-link fence the CCW onboard shows (owner notes 10 / 11) is not yet placed, it will close these rays'),
            dict(target='paddock lanes', side='left', a=(35.4909381, -119.5484441), b=(35.4896508, -119.5481949),
                 why='round 8: the paddock lanes (pale paved closed road) lie 94-110 m beyond the edge across the infield dirt; OPEN: the infield chain-link fence the CCW onboard shows (owner notes 10 / 11) is not yet placed, it will close these rays'),
            dict(target='T2 runoff', side='left', a=(35.4914, -119.54166), b=(35.49178, -119.54103),
                 why="the T2 runoff the owner marked as legitimate pavement (owner/t2_edges.json green lines)"),
            dict(target='Sweeper (OSM 34351309)', side='right', a=(35.4946775, -119.5479825), b=(35.4943975, -119.5480562),
                 why='open infield from T10 across to the Sweeper loop, no barrier (c20_s3800 / c20_s3850; onboard t122-t124: open ground right); rays reach it 109 m out on the first-centre geometry'),
            dict(target='pit lane', side='left', a=(35.4889016, -119.5423787), b=(35.4889427, -119.5417733),
                 why="past the pit wall's east end at the starter's hut the crossover and an open earth strip lie between the track and the pit lane, no barrier (stage3_evidence/cw_wallend.png on c20_s0250 / c20_s0300; onboard t010: open ground left past the hut)"),
            dict(target='pit lane', side='left', a=(35.4905, -119.54105), b=(35.4910, -119.54135),
                 why='the pit-out merge: the lane joins the track on one pavement with no barrier (c20_s0600 / c20_s0650; onboard t018-t022)'),
            dict(target='Atlantic (OSM 34351042)', side='left', a=(35.4873996, -119.5432816), b=(35.4875254, -119.5435093),
                 why='open infield between the track and the concrete Atlantic road, no barrier (c20_s1750 / c20_s1800)'),
            dict(target='Dog Leg (OSM 39224483, west of the T5 turn)', side='left', a=(35.4866696, -119.5420864), b=(35.4874984, -119.5434481),
                 why='the Dog Leg runs beside and across the open infield from T5 to Truck Stop with no barrier (c20_s1650-c20_s2100; onboard t058-t072: open dirt, white kerb blocks only)'),
            dict(target='Dog Leg (OSM 39224483, west of the T5 turn)', side='left', a=(35.4875308, -119.5435269), b=(35.4864821, -119.5470559),
                 why='the Dog Leg runs beside and across the open infield from T5 to Truck Stop with no barrier (c20_s1650-c20_s2100; onboard t058-t072: open dirt, white kerb blocks only)'),
            dict(target='front-straight crossover (OSM 34351026)', side='left', a=(35.4873795, -119.5432549), b=(35.4875868, -119.5437362),
                 why='open infield between the crossover and the track, no barrier (c20_s0150 / c20_s0200 / c20_s1800-c20_s1900; onboard t006: two cones at its mouth, open dirt beside)'),
            dict(target='outer T2 loop (OSM 39224609)', side='left', a=(35.4913759, -119.5415961), b=(35.4909241, -119.5402922),
                 why='the outer T2 loop round the pond, open dirt between it and the track, no barrier (c20_s0650-c20_s0850; onboard t020-t032: open ground left)'),
            dict(target='pit lane', side='left', a=(35.4889184, -119.5421388), b=(35.4903837, -119.5410577),
                 why='the pit lane where it has no wall: the pit-in split before T11 (pit-lane video 20:31-20:40: the lane leaves the track with no wall until the pit-wall head) and the pit-out round the inside of T1, sharing the pavement with the track beside the white kerb blocks (c20_s0450-c20_s0650; onboard t016-t022)'),
            dict(target='pit lane', side='left', a=(35.4893967, -119.5481311), b=(35.4886485, -119.546407),
                 why='the pit lane where it has no wall: the pit-in split before T11 (pit-lane video 20:31-20:40: the lane leaves the track with no wall until the pit-wall head) and the pit-out round the inside of T1, sharing the pavement with the track beside the white kerb blocks (c20_s0450-c20_s0650; onboard t016-t022)'),
            dict(target='Atlantic (OSM 34351042)', side='right', a=(35.4887925, -119.5441857), b=(35.4888995, -119.5424026),
                 why='open infield to the concrete Atlantic road, no barrier (c20_s0250 / c20_s0300 and c20_s1800; onboard t010-t016: open dirt right)'),
            dict(target='Atlantic (OSM 34351042)', side='right', a=(35.4873795, -119.5432549), b=(35.4876024, -119.5438449),
                 why='open infield to the concrete Atlantic road, no barrier (c20_s0250 / c20_s0300 and c20_s1800; onboard t010-t016: open dirt right)'),
            dict(target='crossover (OSM 34351015)', side='right', a=(35.4887723, -119.5445269), b=(35.4887912, -119.5442077),
                 why='open infield to the concrete crossover, no barrier (c20_s0000 / c20_s4700 and c20_s1900; onboard t004 / t068: open dirt right)'),
            dict(target='crossover (OSM 34351015)', side='right', a=(35.4876117, -119.5439546), b=(35.4874916, -119.5455266),
                 why='open infield to the concrete crossover, no barrier (c20_s0000 / c20_s4700 and c20_s1900; onboard t004 / t068: open dirt right)'),
            dict(target='crossover (OSM 34351015)', side='right', a=(35.4887141, -119.5455066), b=(35.4887768, -119.5444499),
                 why='open infield to the concrete crossover, no barrier (c20_s0000 / c20_s4700 and c20_s1900; onboard t004 / t068: open dirt right)'),
            dict(target='drag strip, south part (OSM 34351305)', side='right', a=(35.4890891, -119.5498709), b=(35.4928773, -119.5496895),
                 why='the old drag strip parallel to Lost Hill and Riverside, open dirt between, no barrier (c20_s2600-c20_s3050; onboard t084-t100: open ground right)'),
            dict(target='drag strip, south part (OSM 34351305)', side='right', a=(35.4929105, -119.5482515), b=(35.4905803, -119.5483943),
                 why='the old drag strip parallel to Lost Hill and Riverside, open dirt between, no barrier (c20_s2600-c20_s3050; onboard t084-t100: open ground right)'),
            dict(target='front-straight crossover (OSM 34351026)', side='right', a=(35.4887723, -119.5445269), b=(35.4888408, -119.5433712),
                 why='open infield between the crossover and the track, no barrier (c20_s0150 / c20_s0200 / c20_s1800-c20_s1900; onboard t006: two cones at its mouth, open dirt beside)'),
            dict(target='front-straight crossover (OSM 34351026)', side='right', a=(35.4875686, -119.5436508), b=(35.4875946, -119.5448795),
                 why='open infield between the crossover and the track, no barrier (c20_s0150 / c20_s0200 / c20_s1800-c20_s1900; onboard t006: two cones at its mouth, open dirt beside)'),
            dict(target='front-straight crossover (OSM 34351026)', side='right', a=(35.4887506, -119.5448902), b=(35.4887768, -119.5444499),
                 why='open infield between the crossover and the track, no barrier (c20_s0150 / c20_s0200 / c20_s1800-c20_s1900; onboard t006: two cones at its mouth, open dirt beside)'),
            dict(target='Pacific (OSM 34350988)', side='right', a=(35.4875457, -119.5453166), b=(35.4873891, -119.5457067),
                 why='open infield to the concrete Pacific road, no barrier (c20_s4650 / c20_s4700 and c20_s1900; onboard t002: an orange cone at its mouth, open dirt right)'),
            dict(target='Pacific (OSM 34350988)', side='right', a=(35.4886376, -119.546449), b=(35.4887572, -119.5447801),
                 why='open infield to the concrete Pacific road, no barrier (c20_s4650 / c20_s4700 and c20_s1900; onboard t002: an orange cone at its mouth, open dirt right)'),
            dict(target='Sweeper (OSM 34351309)', side='right', a=(35.4946875, -119.5495846), b=(35.4961511, -119.5495265),
                 why='the Sweeper loop inside Star Mazda, open dirt between it and the track, no barrier (c20_s3350-c20_s3700; onboard t108-t122: open ground right)'),
            dict(target='Sweeper (OSM 34351309)', side='right', a=(35.4963127, -119.54952), b=(35.4965951, -119.5493105),
                 why='the Sweeper loop inside Star Mazda, open dirt between it and the track, no barrier (c20_s3350-c20_s3700; onboard t108-t122: open ground right)'),
            dict(target='Sweeper (OSM 34351309)', side='right', a=(35.496647, -119.5490802), b=(35.4946199, -119.54794),
                 why='the Sweeper loop inside Star Mazda, open dirt between it and the track, no barrier (c20_s3350-c20_s3700; onboard t108-t122: open ground right)'),
            dict(target='Zorros Corners (OSM 34351301)', side='right', a=(35.4888405, -119.5498415), b=(35.4892535, -119.5499594),
                 why='open dirt between Zorros Corners and Sunset / the drag strip, no barrier (c20_s4200-c20_s4350 and c20_s2650; onboard t128-t136: open ground right)'),
            dict(target='Zorros Corners (OSM 34351301)', side='right', a=(35.4912008, -119.5485186), b=(35.4888995, -119.5480436),
                 why='open dirt between Zorros Corners and Sunset / the drag strip, no barrier (c20_s4200-c20_s4350 and c20_s2650; onboard t128-t136: open ground right)'),
        ], paddock=[]),
    ),
    # ---------------------------------------------------------------- pit lane, first-class (SKILL 3.5)
    pit_lane=dict(
        lane=dict(source='osm', match_track_tone=dict(k=0.5, paint=0.97),
                  to_walls=dict(reach=6.0),    # judge r3 pit_01 / pit_02: pavement from the lane to both K-rails (pit video t1249000-t1348000); reach 4 -> 6 m (judge r5: the paddock-side wall stands 4.1-5.3 m past the left edge at x -150..+9, a tan strip on pit_01 / pit_02)
                  no_edge_line=['left'],
                  # round 8 (owner lap 2 note 9): no pit-box lines: the pit video t1249000-t1339000 shows the lane between
                  # the K-rails with no transverse box lines (and the rule had painted them on the pit-in and pit-out roads)
                  boxes=[]),      # judge r5: t1267000 / t1312000 show pavement to the paddock-side wall base and no white line on the left
        walls=[
            dict(side='right', a=(35.4887467, -119.5466176), b=(35.4890148, -119.5422713), h=0.81, material='jersey',
                 declared='pit wall, front straight', src='pit-lane video ucmXJu5QKFQ 20:40-22:28 (the K-rail on the right of the lane); inventory pit rows s 4497-4655 right'),
            dict(side='left', a=(35.4889157, -119.5464997), b=(35.489005, -119.5450805), h=0.81, material='jersey',
                 declared='pit lane, paddock side, west', src='pit-lane video 20:49-21:07 (t1249000, t1267000: the K-rail on the left); inventory pit rows s 4528 / 4579 left'),
            dict(side='left', a=(35.4890129, -119.5449429), b=(35.489061, -119.5441102), h=0.81, material='jersey',
                 declared='pit lane, paddock side, tower', src='pit-lane video 21:52 (t1312000: the wall at the tower); inventory pit row s 4655 left'),
            dict(side='left', a=(35.4890699, -119.5439506), b=(35.4891471, -119.5426301), h=0.81, material='jersey',
                 declared='pit lane, paddock side, east', src='c20_p0540 / c20_p0600 (the wall line north of the lane)'),
        ],
        boxes=None,
        buildings=[],
        furniture=[],
    ),
    # ---------------------------------------------------------------- structures kit (SKILL 3.7; tools/track/kit/README.md)
    # the timing tower at the line (judge r1 row 1): OSM 765811057, a two-storey building with a blue flat roof on posts
    # over its top deck (inventory rows t002 / t004 and pit row s 4655: 2 storeys, blue roof on posts, ~8 m; pit-lane
    # video t1312000 / t1330000: beige-white walls, a glazed upper storey, the blue roof on posts over the deck); the lidar
    # top of the footprint 9.8 m (robust, building_height_robust). Drawn as a 2-storey block plus a canopy roof on posts,
    # not the generic window-row box
    structures=dict(suppress_osm=['765811057', '765811056'], items=[
        # judge r3: the pit-lane video t1303000 (21:43) and t150-t152 show a two-storey building whose upper storey is set
        # back behind an open deck with posts and a railing, divided glazing, an exterior stair on the track side, the
        # deep blue roof over it; the capture (stage3_evidence/tower_cap.png on c20_s0050 / c20_p0420) shows the roof at
        # ~25 x 20 m, the OSM footprint the walls
        # judge r5 (round 6): the round-5 open deck glazed both storeys of the whole 25 x 19 m roof outline; the pit video
        # (t1312000 21:52, t1339000) shows a COMPACT tower, ~14 m along the lane: a solid tan lower storey with a door and
        # a few windows, the upper storey set back behind a deck with a railing, windows between posts, a deep blue roof
        # overhang on posts, the exterior stair at its west (near) end; west of it a low flat-roofed structure (the shade
        # roof at the frame's left edge). Footprints measured on c20_p0420 / c20_s0050 (structure_stills/tower_cap_r6.png):
        # the white roof outline 25 x 19 m at heading 3.83 deg, the tower its east 14 m, the low structure the west 11 m
        # and a 5 m strip behind the tower
        dict(type='block', name='timing tower', rect=dict(c=(35.4891199, -119.5444765), heading_deg=183.83, l=14.0, w=14.0),
             h=3.2, storeys=1, parapet=0.0, wall='#cdb892', band='#3a3530', roof='#9c9a94', bands=[], deck_rail=True,
             windows=dict(w=1.2, pitch=4.5, z0=1.0, z1=2.2), doors_at=[dict(face=-1, at=-3.0, w=1.0, h=2.1), dict(face=2, at=2.0, w=1.0, h=2.1)],
             balcony=dict(side='track', z=3.2, depth=0.8, color='#cdb892', stair=True),
             src='pit-lane video t1312000 / t1339000 (judge r5): solid tan lower storey with a door and a few windows, the deck on its roof with a railing, the exterior stair at the west end; footprint on c20_p0420 / c20_s0050',
             h_src='storey 3.2 m (HEIGHTS.md); the deck on its roof'),
        dict(type='block', name='timing tower upper storey', rect=dict(c=(35.4891471, -119.5444732), heading_deg=3.83, l=11.0, w=8.0),
             base=3.2, h=2.8, storeys=1, wall='#cdb892', band='#2e3a48', roof='#9c9a94', bands=[],
             windows=dict(w=1.6, pitch=2.2, z0=0.8, z1=2.3, faces=[-1, 2, -2]), doors_at=[dict(face=-1, at=4.2, w=0.9, h=2.1, color='#5a4636')],
             src='pit-lane video t1312000 / t1339000: the upper storey set back behind the deck, windows between dark posts on the lane side and the ends (glazed upper storey only)',
             h_src='storey 2.8 m under the roof; the lidar top of the footprint 9.8 m includes the roof'),
        # round 8 (owner lap 2 note 14): the AWNING stands directly BEHIND the tower (north, toward Slow Ln), not beside it:
        # his CCW frame and his map ('Starter's Tower'); the OSM 765811056 footprint (23.6 x 17.4 m, the ribbed roof on the
        # capture, c20_p0420), lidar top 4.3 m: an open shade roof on posts (the round-6 / 7 annexes beside and behind the
        # tower are gone; the lane side west of the tower: open frontage and a tent on t1312000, not placed)
        dict(type='fuel', name='tower awning', rect=dict(c=(35.4893366, -119.5445599), heading_deg=3.83, l=23.6, w=17.4),
             h=3.9, fascia=0.4, canopy='#c9cbcd', fascia_color='#9da0a3', posts=6, islands=0, edge_posts=True,
             src='OSM 765811056 footprint behind the tower; c20_p0420 (the ribbed roof); owner lap 2 note 14 (his CCW frame and map); pit-lane video t1312000',
             h_src='lidar: the footprint top 4.3 m (roof 0.4 m)'),
        # judge r8 (cp6): the west 11 m of the 25 x 19 m roof outline beside the tower at the lane: an open shade roof on posts
        # (pit video t1312000: open frontage, a tent), as in round 7; the awning (OSM 765811056) stays behind the tower
        dict(type='fuel', name='timing tower west shade roof', rect=dict(c=(35.4891348, -119.544616), heading_deg=3.83, l=11.0, w=19.0),
             h=2.6, fascia=0.2, canopy='#b5b2aa', fascia_color='#5b5852', posts=4, islands=0, edge_posts=True,
             src='the west 11 m of the 25 x 19 m roof outline on c20_p0420 / c20_s0050 beside the tower; pit video t1312000: open frontage with a tent',
             h_src='2.6 m: below the tower deck on t1312000 (HEIGHTS.md storeys)'),
        dict(type='fuel', name='timing tower roof', rect=dict(c=(35.4891244, -119.5444769), heading_deg=3.83, l=17.0, w=16.0),   # judge r8 (cp6): back to the compact tower (pit video t1312000 / t1339000: 12-15 m along the lane, a projecting roof): the tower is the east 14 m of the 25 x 19 m roof outline, its roof 1.5 m over its walls
             h=6.1, fascia=0.9, canopy='#2f5d9e', fascia_color='#27508a', posts=6, islands=0,   # judge r6 fwd_15: a deep roof (0.9 m fascia) sitting on the upper storey, not a thin slab above it
             src='pit-lane video t1312000 / t1339000: the deep blue roof on posts over the tower, ~1.5 m overhang past its walls (the 14 m tower, not the 25 m outline)',
             h_src='lidar: the footprint top 9.8 m (scenery building_height_robust), roof 0.5 m'),
        # judge r6 (pit_02 4640, r6_tower_from_lane): the shade roof read as a white block from the lane: thin posts along both
        # long edges (open frontage, t1312000), a dark thin fascia
        # judge r6 fwd_00 0 L (round 7): the pit video t1267000 (21:07) and t1303000 (21:43) show a long, low, dark shade roof
        # on posts in the paddock behind the paddock-side K-rail west of the tower (the onboard t000 the same line of roofs
        # past the wall); the only roofed structure there in the lidar is the 29 x 8 m footprint at (35.4896585,
        # -119.5454773), 3.7 m (the 2026 clean captures stop short of it): drawn there, open on its posts, dark roof. The
        # pop-up tents and the parked trailers are not placed (temporary)
        dict(type='fuel', name='paddock shade roof', rect=dict(c=(35.4896585, -119.5454773), heading_deg=3.83, l=29.0, w=8.0),
             h=3.0, fascia=0.3, canopy='#55585b', fascia_color='#45484b', posts=6, islands=0, edge_posts=True,
             src='pit-lane video t1267000 / t1303000: the long low dark shade roof on posts behind the paddock-side K-rail west of the tower; footprint and height from the lidar (2021) structure there, 29 x 8 m, 3.7 m',
             h_src='lidar 3.7 m top; the roof underside at 3.0 m'),
    ]),
    # ---------------------------------------------------------------- app (SKILL stage 6)
    app=dict(short='Buttonwillow', pace='cars/field/buttonwillow/pace.json'),
)
