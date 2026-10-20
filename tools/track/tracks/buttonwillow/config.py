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
    # video ucmXJu5QKFQ 22:19-22:28), taken on the first centre (ENU 16.2, -232.9). The onboard's Catalyst lap line (lap
    # 21 starts at 0:05.47; GPS dot at 0:06 at s ~31) lies within 10 m of it.
    start_finish_latlon=(35.4887078, -119.5445213),
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
        onboard=[],                              # recent (2024+) onboard of the Lemons layout: video ids with date and camera
        pit_lane_video=[],                       # recent video that drives the pit lane end to end (pit in, boxes, pit out)
        streetview='compare/buttonwillow/streetview.md',
        lemons_layout='registration.24hoursoflemons.com/userfiles/races/26_buttonwillow.png (race/?id=454, Button Turrible 2026, 26-27 Sep 2026; Wayback 20260111111352): clockwise',
        mylaps='speedhive event 3731897, race session 12906863 (105 cars classified; best 2:15.252 GT Poorty Racing; #619 Anal Corkscrew Probe P15, best 2:29.956, 287 laps)',
        naip='m_3511936_ne_11_060_20220608 (NAIP 8 Jun 2022, 0.6 m)',
    ),
    # ---------------------------------------------------------------- stage 1: geometry (SKILL stage 1)
    stations_ref=None,                           # (n, length_m) of the build the station numbers below refer to (SKILL 1.3)
    centre=dict(),                               # fit weights, bridge windows, pit merges (SKILL 1.3)
    # the edge fit (SKILL 1.4): defaults, plus the asphalt-end detector tuned to Buttonwillow's pale dusty dirt (20 Oct
    # 2026, eight stretches of the captures: jump 8 / sat 40 / window -2..+2 m hit 81 % of stations, 98 % within 0.25 m
    # of the median over captures; the defaults 65 % / 99 %, and from the NAIP prior they often miss the window)
    spline=dict(asphalt_end=dict(jump=8.0, sat_max=40.0, lo=-2.0, hi=2.0)),
    # Buttonwillow has no painted edge lines (every 2026 capture and the onboard: asphalt straight to dirt), so the edge
    # is where the dark asphalt ends, everywhere except at kerbs, where it is the kerb's outer limit (SKILL 1.5). The kerb
    # zones come from compare/kerb_detect.py on the asphalt-end build (run 3, 20 Oct 2026: runs with their outer limit
    # 0.3 m or more beyond that edge and 9 m or longer, +-4 stations); they come first because the first matching feature
    # wins. Kind 'kerb_band': the red / white / blue blocks read grey on the captures (kerb_detect colour 'grey'), so the
    # red-only 'kerb' kind found nothing there. Stations are those of the first centre (4692, station 0 at the timing line).
    features=[
        ('left', 277, 327, 'kerb_band', 'kerb_detect run s 282-324 off +0.1..+1.0 m (c20_s0400, c20_s0450)'),
        ('left', 356, 389, 'kerb_band', 'kerb_detect run s 362-387 off +0.1..+1.0 m (c20_s0500)'),
        ('left', 393, 432, 'kerb_band', 'kerb_detect run s 399-430 off +0.3..+1.0 m (c20_p0840, c20_s0550)'),
        ('left', 745, 766, 'kerb_band', 'kerb_detect run s 751-764 off +0.3..+0.6 m (c20_s0850, c20_s0900)'),
        ('left', 947, 1017, 'kerb_band', 'kerb_detect run s 954-1016 off -0.2..+0.7 m (c20_s1050, c20_s1100)'),
        ('left', 1198, 1218, 'kerb_band', 'kerb_detect run s 1205-1217 off -0.1..+0.3 m (c20_s1300, c20_s1350)'),
        ('left', 1241, 1274, 'kerb_band', 'kerb_detect run s 1248-1273 off -0.5..+0.3 m (c20_s1350, c20_s1400)'),
        ('left', 1641, 1684, 'kerb_band', 'kerb_detect run s 1649-1684 off +0.0..+0.8 m (c20_s1750, c20_s1800)'),
        ('left', 2515, 2542, 'kerb_band', 'kerb_detect run s 2526-2545 off +0.0..+0.8 m (c20_s2650)'),
        ('left', 2671, 2746, 'kerb_band', 'kerb_detect run s 2681-2748 off +0.2..+1.1 m (c20_s2800, c20_s2850)'),
        ('left', 2993, 3013, 'kerb_band', 'kerb_detect run s 3004-3017 off -0.3..+0.5 m (c20_s3100, c20_s3150)'),
        ('left', 3318, 3385, 'kerb_band', 'kerb_detect run s 3330-3389 off +0.1..+1.0 m (c20_s3450, c20_s3500)'),
        ('left', 3458, 3515, 'kerb_band', 'kerb_detect run s 3470-3520 off +0.0..+0.7 m (c20_s3550, c20_s3600)'),
        ('left', 4364, 4394, 'kerb_band', 'kerb_detect run s 4378-4400 off +0.1..+0.9 m (c20_s4500)'),
        ('left', 4470, 4501, 'kerb_band', 'kerb_detect run s 4485-4508 off +0.0..+0.9 m (c20_s4600)'),
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
        ('right', 4138, 4182, 'mouth of OSM 34351301 (Zorros Corners): the prior is carried across it'),
        ('right', 4580, 4624, 'mouth of OSM 34350988 (Pacific): the prior is carried across it'),
        ('right', 4645, 4689, 'mouth of OSM 34351015 (infield connector): the prior is carried across it'),
    ]),
    shapes=[],                                   # measured half-width knots (SKILL 1.4)
    straights=[],                                # declared straights: a RANSAC paint line or parallel to a wall (SKILL 1.4)
    repave_fixes=[],                             # only where recent footage contradicts the survey (SKILL 1.6)
    gate=dict(exempt=[
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
        ('right', 4130, 4190, 'mouth of OSM 34351301 (Zorros Corners); junction, real'),
        ('right', 4572, 4632, 'mouth of OSM 34350988 (Pacific); junction, real'),
        ('right', 4637, 4697, 'mouth of OSM 34351015 (infield connector); junction, real'),
        ('left', 4270, 4330, 'pit-in: the Pit / Fire Road (OSM 39224587) leaves on the left before T11 (pit-lane video ucmXJu5QKFQ 20:31); junction, real'),
        ('left', 380, 540, 'pit-out: the pit lane rejoins on the left after T1 (c20_s0450, c20_s0500, c20_p0840); junction, real'),
    ]),
    # ---------------------------------------------------------------- stage 2 (SKILL stage 2)
    ghosts=dict(),
    # ---------------------------------------------------------------- stage 3: scenery FROM EVIDENCE ONLY (SKILL stage 3)
    # No object without a cited `src`; every entry below is filled from the inventory, the captures and the footage, and
    # recorded in compare/<id>/manifest.md. The coverage gate fails on any inventory row with no object and no
    # disposition.
    scenery=dict(
        brake_board_corners=[],                  # boards only where the onboard shows them (SKILL 3.9)
        corner_boards=False,                     # turn boards only where the onboard shows them (SKILL 3.9)
        flagstand=False,                         # only where the onboard shows one (SKILL 3.9)
        pit_wall=dict(rule=False),               # pit-side walls are declared, never ruled (SKILL 3.5)
        kerb=dict(),                             # width, stripe_m, colours, palettes, profile {height, face, back} (SKILL 3.3)
        kerbs_declared=[],                       # every strip from kerb_detect.py on the captures + the onboard (SKILL 3.3)
        kerb_lines=[],                           # raised kerb lines on island kerb paint (SKILL 3.3)
        declared_walls=[],                       # walls, tyre walls, fences, cushions, movable barriers: measured lines,
                                                 # heights with h_src, colours, stack (SKILL 3.4)
        osm_barrier_overrides={},                # re-kind or drop an OSM wall on evidence (SKILL 3.4)
        tyre_facings=None,                       # dict(reach, off) where tyres face walls (SKILL 3.4)
        impact_barriers=[],                      # blocks at wall noses (SKILL 3.4)
        tyre_stacks=[],                          # free-standing stacks (SKILL 3.8)
        blocks=[],                               # free-standing concrete blocks (SKILL 3.8)
        marshal_posts=[],                        # corner stations confirmed on footage (SKILL 3.8)
        light_masts=[],                          # masts with base + shadow on a capture (SKILL 3.8; or structures type 'mast')
        cone_lines_declared=[],                  # cones on measured painted lines, colour / size / spacing from footage (SKILL 3.5, 3.8)
        pit_exit_cones=None,                     # on the measured blend line (SKILL 3.5)
        paint_lines_declared=[],                 # merge / blend lines measured on the captures (SKILL 3.5, 3.11)
        edge_line_cut=[],                        # where the edge paint is not the white line (SKILL 3.11)
        wall_boards=[],                          # boards with typed names per run, start / end from footage (SKILL 3.9)
        bridge_banners={},                       # 'NAME|#bg|#fg' per bridge face (SKILL 3.9, 3.10)
        ground_signs=[],                         # painted ground logos as typed text, from a full-lap capture scan (SKILL 3.9)
        bridge_stairs=False,                     # abutments and stairs to the ground (SKILL 3.10)
        closed_roads=[],                         # unused paved roads as track surface, painted edges, cones from footage (SKILL 3.6)
        closed_roads_clip_walls=False,
        paved_areas=[],                          # paved ground the ortho fills with vehicles (SKILL 3.6)
        pit_lane_clip_walls=False,               # the lane polygon stops at its walls (SKILL 3.5)
        terraces=[],                             # hillside stands from terrace_measure.py footprints (SKILL 3.7)
        grandstand_on_terrain=False,             # (SKILL 3.7)
        building_height_robust=True,             # p60 lidar heights (SKILL 3.7)
        building_overrides=[],                   # newer evidence over the lidar, logged (SKILL 3.7)
        building_evidence=[],                    # the 2026 source of each building, or its drop (SKILL 3.7)
        season_tint=None,                        # the footage's season on the published ortho (SKILL 3.2)
        gates=dict(allowed=[], paddock=[]),      # allowed runoff with the evidence that shows it open (SKILL 3.12)
    ),
    # ---------------------------------------------------------------- pit lane, first-class (SKILL 3.5)
    pit_lane=dict(lane=dict(source='osm'), walls=[], boxes=None, buildings=[], furniture=[]),
    # ---------------------------------------------------------------- structures kit (SKILL 3.7; tools/track/kit/README.md)
    structures=dict(suppress_osm=[], items=[]),
    # ---------------------------------------------------------------- app (SKILL stage 6)
    app=dict(short='Buttonwillow', pace='cars/field/buttonwillow/pace.json'),
)
