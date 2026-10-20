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
    # ways against their node order ('way:from:to' with from after to). PROVISIONAL until the onboard check (0.1).
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
    # PROVISIONAL (stage 0.1): no painted timing line on the 2026 captures; the starter's stand on the pit wall
    # (c20_s0150, the white hut on the wall at px 455, 195) abeam on the track centre. Checked on the onboard (0.7).
    start_finish_latlon=(35.488784, -119.544507),
    # PROVISIONAL: numbering from the Lemons layout picture (11 turns), anchors = curvature peaks of the OSM loop
    corners=[
        ('T1', None, 'left', None, 35.489327, -119.541013),
        ('T2', None, 'right', None, 35.491661, -119.541518),
        ('T3', None, 'right', None, 35.488903, -119.539226),
        ('T4', None, 'right', None, 35.487572, -119.539383),
        ('T5', None, 'left', None, 35.486640, -119.542040),
        ('T6', None, 'right', None, 35.486400, -119.547530),
        ('T7', None, 'right', None, 35.486594, -119.549386),
        ('T8', None, 'right', None, 35.491056, -119.550794),
        ('T9', None, 'right', None, 35.496565, -119.549311),
        ('T10', None, 'left', None, 35.493800, -119.548300),
        ('T11', None, 'left', None, 35.488595, -119.547712),
    ],
    named_straights=[],
    # Race #13 CW: 3.000 mi = 4828 m (en.wikipedia.org/wiki/Buttonwillow_Raceway_Park, 20 Oct 2026). MyLaps' 3.1 mi is the
    # venue's default length (the same for every Buttonwillow event), not this layout's. The stitched OSM loop is 4701 m.
    loop_check=dict(n_min=4500, n_max=5100, official_m=4828, elev_min=50, elev_max=120),
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
    spline=dict(),                               # the edge fit (SKILL 1.4); defaults in trackcfg.py
    features=[],                                 # (side, lo, hi, 'keep' | 'asphalt_end' | 'kerb', why) where the paint is ambiguous (SKILL 1.4)
    prior=dict(),                                # bridge windows, first_edge, interp (SKILL 1.4)
    shapes=[],                                   # measured half-width knots (SKILL 1.4)
    straights=[],                                # declared straights: a RANSAC paint line or parallel to a wall (SKILL 1.4)
    repave_fixes=[],                             # only where recent footage contradicts the survey (SKILL 1.6)
    gate=dict(),                                 # edge-gate thresholds and exemptions with the capture that shows the junction (SKILL 1.9)
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
