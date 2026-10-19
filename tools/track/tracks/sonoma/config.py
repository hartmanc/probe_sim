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
    # signed-curvature peak of the built centre within +-45 m of the anchor
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
        ('T9a', None, 'left', None, 38.164876, -122.458777),
        ('T10', None, 'right', None, 38.162108, -122.453349),
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
    # ---------------------------------------------------------------- stage 3: scenery by rule only (no footage rounds yet)
    scenery=dict(
        brake_board_corners=['T2', 'T4', 'T7a', 'T11'],
        # kerbs: blue and white flat concrete (owner, Street View inside T7; the z20 captures show white and grey-blue
        # blocks), measured on c20_o0715 (T10 inside, 0.117 m/px): 5 px wide = 0.55 m, block period 16 px = 1.9 m, so
        # 0.95 m blocks. Laguna keeps the defaults (0.9 m, 2 m, red / white).
        # walls OSM does not map: the pit straight (owner, 19 Oct 2026 drive), concrete Jersey walls without catch fence
        # (Street View 5MY4xR9O7etAXEHnZCVnGQ, compare/sonoma/streetview.md), measured on the
        # clean captures c20_s1595..s1870 as the bright 0.25-1.2 m band beyond each painted edge (tools/track/compare/
        # wall_measure: left 2.0 m off the edge at 235 of 271 stations, right 2.3 m at 243), every 10th station
        declared_walls=[
            dict(name='pit straight and pit-out lane, pit-lane side', kind='concrete', h=1.0, fence=0.0, latlon=[
                (38.1606469, -122.4535036), (38.1607541, -122.4536697), (38.1608652, -122.4538464),
                (38.1609772, -122.4540279), (38.1610893, -122.4542076), (38.1612006, -122.454387),
                (38.1613123, -122.4545663), (38.1614237, -122.4547457), (38.1615466, -122.4549429),
                (38.1616582, -122.455122), (38.1617703, -122.4553019), (38.1618793, -122.4554785),
                # on through T1 between the track and the pit-out lane to its end (c20_s1925, measured by hand on the
                # capture: the white wall line), where the lane merges on the left
                (38.1619426, -122.4560474), (38.1619637, -122.4563223), (38.1619848, -122.4565905),
                (38.1620069, -122.4568788)]),
            dict(name='pit straight, drag-strip side', kind='concrete', h=1.0, fence=0.0, latlon=[
                (38.1611834, -122.4539958), (38.1613003, -122.4541846), (38.161412, -122.4543637),
                (38.1615237, -122.4545429), (38.1616354, -122.4547222), (38.1617473, -122.4549012),
                (38.1618596, -122.4550797), (38.1619709, -122.4552587), (38.1620296, -122.4553516)]),
        ],
        # the hillside grandstands (OSM building=grandstand 1414701936-39) sit on the slope: height = terrain rise across
        # the footprint + the lidar structure height
        grandstand_on_terrain=True,
        kerb=dict(width=0.55, stripe_m=0.95, colors=['#5b7ea8', '#d9d8cf']),
        # the pit wall halfway between the track and the pit lane, along straights only (the pit road runs round the
        # OUTSIDE of the T11 hairpin; a wall 0.6 m off that edge put the hot-lap launch into it, owner 20 Oct 2026)
        pit_wall=dict(fence_until_m=120, at='midway', min_radius=150.0),
        # paved roads of the circuit the Lemons loop does not use: driveable pavement, coned off at each mouth (owner,
        # 19 Oct 2026: "the Chute pavement is missing")
        closed_roads=[
            dict(name='2020 fast bypass (8a to T10)', ways=['834728156', '116036857'], half_width=6.0),
            dict(name='the Chute (NASCAR short course, T4 to T7)', ways=['834724050', '230287122'], half_width=6.0),
            dict(name='drag strip', ways=['28825448'], half_width=9.0, max_half=12.0),
            # the paved runoff INSIDE T7 (the triangle inside the hairpin, round the short-T7 way): cars may use it
            # (owner), so no cones; the racing line stays on the track (cutting through adds distance)
            dict(name='T7 inside runoff', ways=['1494191150'], half_width=10.0, max_half=14.0, cones=False),
            dict(name='T11a shortcut', ways=['28825444'], half_width=6.0),
            dict(name='PWC lower hairpin', ways=['505454376'], half_width=5.0),
        ],
    ),
    # ---------------------------------------------------------------- app registry (src/scoreboard/config.ts)
    app=dict(short='Sonoma', pace='cars/field/sonoma/pace.json'),
)
