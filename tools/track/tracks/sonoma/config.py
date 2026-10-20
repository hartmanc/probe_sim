"""Sonoma Raceway in its 24 Hours of Lemons configuration: every per-circuit constant of the track pipeline
(tools/track/build_track.py; format in tools/track/trackcfg.py, Laguna's config is the worked example).

Built without logger laps (the team has not raced here): the centre is the painted-road midpoint, the racing line the
pure minimum-curvature line. Plain data; nothing here runs. Paths are relative to tools/track/.

The Lemons loop (24hoursoflemons.com/race/?id=450, layout picture registration.24hoursoflemons.com/userfiles/races/
26_sonoma.png, 2026 season; confirmed on the March 2026 Lemons onboard youtube.com/watch?v=RAZip6S84CM): clockwise,
start/finish on the front straight; T1 left kink, T2 right at the bottom of the hill, up to T3 (left) / T3a (right),
T4 right, T5 right, the Carousel (T6, a long left), the straight along the trees (not the drag strip) to T7 and the
7a hairpin round the O'Reilly island, the T8 / T8a esses, the back straight to the 9a left-right (the 2020 fast bypass is not used), T10 right, down to the T11 hairpin (not the 11a shortcut), T12 kink onto the front straight. No chute (T4 to T7).
The pit lane ("Pit Road") leaves before the T11 hairpin (outside it), runs behind the wall on the left of the front
straight and rejoins on the left at T1.
"""

CONFIG = dict(
    id='sonoma',
    name='Sonoma Raceway',
    direction='cw',
    # ---------------------------------------------------------------- frame and sources (Stage 0)
    origin=(38.1627, -122.4576),                        # lat0, lon0 of the local ENU frame (circuit centre)
    osm_bbox=(-122.470, 38.150, -122.440, 38.175),      # W, S, E, N of the OSM API map call (19 Oct 2026)
    osm_file='osm/osm.xml',
    # The Lemons loop in driving order from the T7a hairpin exit: the long circuit way 505453048 (T7a exit -> T8 -> 8a ->
    # the back straight -> the 9a left-right -> T10 -> T11 -> front straight -> T1-T6 Carousel), then 1494191149 (the
    # straight to T7) and 913592144 (T7 / 7a round the O'Reilly island). 20 Oct 2026, owner's drive: Lemons runs the
    # IndyCar 9a, not the 2020 fast bypass (834728156 'Sonoma Raceway 2020' + 116036857, the grey curve after 8a in the
    # layout picture); onboard youtube.com/watch?v=RAZip6S84CM 1:34-1:39 the long back straight with an orange cone on
    # the left at the closed bypass, 1:40-1:42 the 9a left-right with the tyre stack, 1:43-1:46 T10 (Sunbelt banner).
    # Not driven (paved, coned off, built as paved zones): the bypass, 1494191150 (short T7), 505454376 (PWC lower
    # hairpin), 28825444 (T11a shortcut), 834724050 / 230287122 (the Chute), the Dragstrip 28825448.
    loop_ways=['505453048', '1494191149', '913592144'],
    pit_lane_way='Pit Road',                            # OSM 230287120: pit-in before T11 (outside it) to after T1
    dem_tiles=['https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_NorthernCA_B22/TIFF/'
               'USGS_1M_10_x54y423_CA_NorthernCA_B22.tif'],
    # the DEM's own survey (collected 26 Aug 2022 - 4 Jul 2024, published 24 Mar 2026). Sonoma's road course was fully
    # repaved Dec 2023 - Feb 2024 (milled ~1.5 in and relaid, finished 29 Feb 2024): grades unchanged to centimetres
    lidar_ept='https://s3-us-west-2.amazonaws.com/usgs-lidar-public/CA_NorthernCA_1_B22/',
    lidar_survey='CA_NorthernCA_B22',
    dem13='https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n39w123/USGS_13_n39w123.tif',
    # ---------------------------------------------------------------- no logger laps
    logger_dir=None,
    # the chequered timing line on the front straight (clean captures c20_s1705 / c20_s1760, within 0.4 m of each other)
    start_finish_latlon=(38.161529, -122.454728),
    # ---------------------------------------------------------------- corners: (turn, name, dir, logger s, lat, lon)
    # anchors = curvature peaks of the OSM loop (numbering from the Lemons layout picture); the corner is the
    # signed-curvature peak of the built centre within +-45 m of the anchor (an optional 7th element: another window, m)
    corners=[
        ('T1', None, 'left', None, 38.162039, -122.455626),
        ('T2', None, 'right', None, 38.161040, -122.458817),
        ('T3', None, 'left', None, 38.162598, -122.461150),
        ('T3a', None, 'right', None, 38.162605, -122.462125),
        ('T4', None, 'right', None, 38.164137, -122.463412),
        ('T5', None, 'right', None, 38.164477, -122.461334),
        ('T6', 'The Carousel', 'left', None, 38.162885, -122.458188),
        ('T7', None, 'right', None, 38.166066, -122.462731),
        ('T7a', 'T7a hairpin', 'right', None, 38.166843, -122.461834),
        ('T8', None, 'left', None, 38.166248, -122.461437),
        ('T8a', None, 'right', None, 38.165612, -122.460091),
        # T9: the fast left after 8a (s ~2644; this anchor was mislabelled T9a until 20 Oct 2026). T9a: the 9a chicane at
        # the end of the back straight, a right (R ~22 m, s ~3043) then a left (R ~21 m, s ~3083); the corner is its
        # slow point on the racing line, the left (onboard youtube.com/watch?v=RAZip6S84CM 1:39-1:41: right-hand entry
        # kerb, red/white kerb on the left-hand part). T10: the long right after the chicane (onboard 1:43-1:46, the
        # Sunbelt banners), a near-constant R ~100 m arc whose centreline curvature peak (s ~3217) lies 14 m before its
        # slow point on the racing line (s ~3231): anchor at the slow point, window 3 m. Windows in metres (7th element).
        ('T9', None, 'left', None, 38.164873, -122.458761),
        ('T9a', '9a chicane', 'left', None, 38.162615, -122.455133, 15),
        ('T10', None, 'right', None, 38.162223, -122.453568, 3),
        ('T11', 'T11 hairpin', 'right', None, 38.158643, -122.452193),
        ('T12', None, 'left', None, 38.160569, -122.453276),
    ],
    named_straights=[],
    # ---------------------------------------------------------------- stage 1: geometry
    # 2.52 mi full course (4056 m, the circuit) plus the T7a hairpin round the O'Reilly island, which the full course
    # takes short (OSM: 121 m round the island against 89 m for the short T7): 4088 m. MyLaps lists the event as 2.51 mi.
    # station numbers in this config refer to the frozen centre in stations_ref.json (the 19 Oct build) and are mapped
    # onto every build by world position
    stations_ref=(4090, 4101.037),
    centre=dict(extra_shadow_stations=[4084], width_cap=21.0),   # the shared drag-strip start pavement is ~19-20 m
    loop_check=dict(n_min=3900, n_max=4250, official_m=4088, elev_min=20, elev_max=80),
    captures=dict(
        z20_dir=None,
        clean_dir='compare/sonoma/satellite_clean', clean_index='tiles.json',
        mpp=0.11738,                 # z20 at 38.163 N; overlapping captures measure 0.11749 (68 pairs, median)
        common_shift=None,           # measured by register_clean.py -> satellite_clean/shift.json
        clean_mask='clean',
        exclude=[],
    ),
    spline=dict(runs=None, knot=6, lam=30.0, huber=0.25, line_off=0.26, prior=0.03, init_stiff=30.0, captures='clean'),
    # Carousel exit (T6) to the T7 approach, stations ~1680-2060 (onboard youtube.com/watch?v=RAZip6S84CM 0:55-1:09):
    # the course is bounded by the PAVEMENT, not by cones or a painted line. On the shared drag-strip start (to ~1880) the
    # car runs right of the yellow lane line with the red/white kerb as the right edge (0:59-1:01) and crosses the lane
    # line (1:03-1:04) toward the T7 road, whose left edge is the blue concrete wall at the asphalt's end (1:06-1:09,
    # c20_s3685/s3740: no painted line on that side) and whose right edge is the white line along the drag strip.
    features=[
        ('right', 180, 260, 'kerb', 'T1 exit right: the edge is the inner side of the blue/white kerb runs and the painted '
                                    'wedges between them (c20_s1925); the bright wedge pulled the paint finder outward '
                                    '(rolling wave 0.044 m at 218-228)'),
        ('left', 1860, 2060, 'asphalt_end', 'T7 road left edge: asphalt ends at the concrete wall, no painted line'),
    ],
    # bridge shadow: the T2 footbridge is in OSM (station ~296). Station 4084 is NOT a bridge (corrected 20 Oct 2026; there
    # is no footbridge at the line): it is the chequered start/finish stripe painted across the road (c20_s1705), which
    # the paint detectors read as edge lines; it is masked the same way.
    prior=dict(bridge_win=35, extra_bridges=[4084]),
    shapes=[],
    # the front straight from the T12 exit to the T1 kink: both painted edges are straight lines (c20_s1595..s1870)
    straights=[
        dict(side='left', fit='paint', lo=3995, hi=55, join=(3995, 4005), end=55, tol=0.15,
             why='front straight left: the painted line along the pit wall is straight'),
        dict(side='right', fit='paint', lo=3995, hi=55, join=(3995, 4005), end=55, tol=0.15,
             why='front straight right: the painted line is straight'),
        # the T7 road from the fork to the T7 braking zone is straight (c20_s3740/s3795): its right edge is the white line
        # along the drag strip; its left edge (asphalt to the concrete wall, no paint) runs parallel to it
        dict(side='right', fit='paint', lo=1985, hi=2095, join=(1985, 1990), end=2095, tol=0.15,
             why='T7 road right: the white line along the drag strip is straight'),
        dict(side='left', fit='parallel', ref_side='right', ref_lo=1985, ref_hi=2095, lo=1985, hi=2095, join=(1985, 1990),
             end=2095, why='T7 road left: the wall-side asphalt edge runs parallel to the right line (onboard 1:06-1:09)'),
    ],
    gate=dict(straight_rms=0.10, step=0.10, profile_step=0.10, spline_obs_within=0.85,
              exempt=[('left', 3480, 3610, 'pit-in lane splits off on the left before T11 (dashed blend line, c20_s1155): '
                       'the edge steps in by ~5 m over 60 m as the lane leaves (junction, real)'),
                      ('left', 160, 260, 'pit-out lane joins on the left after T1 (c20_s1870/s1925; junction, real)'),
                      ('left', 1860, 1980, 'the T7 road forks off the drag strip to the left (c20_s3685/s3740; junction, real)')]),
    # ---------------------------------------------------------------- stage 2: racing line only (no logger laps)
    ghosts=dict(margin=1.0, kerb_margin=1.0, nudge=0.3, jerk_w=3),
    # ---------------------------------------------------------------- sources (SKILL 0.4, 0.5)
    # recent video and survey sources (SKILL 0.4, 0.5): recorded here and in compare/<id>/inventory/source.json
    sources=dict(
        onboard=['RAZip6S84CM'],  # March 2026 Lemons race, hood camera, one full lap                              # recent (2024+) onboard of the Lemons layout: video ids with date and camera
        pit_lane_video=['24of8fjjAug'],  # 2025 HPDE: pit out to T1 (~4:56-5:04), pit in (~24:30)                       # recent video that drives the pit lane end to end (pit in, boxes, pit out)
        streetview='compare/sonoma/streetview.md', # Street View / photo-sphere survey record (panorama ids, dates, headings)
        lemons_layout='https://registration.24hoursoflemons.com/userfiles/races/26_sonoma.png',                        # the layout picture on the event's Lemons schedule page
    ),
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
    app=dict(short='Sonoma', pace='cars/field/sonoma/pace.json'),
)
