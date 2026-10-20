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
    # ---------------------------------------------------------------- stage 3: scenery by rule only (no footage rounds yet)
    # ---------------------------------------------------------------- stage 3: scenery FROM EVIDENCE ONLY (20 Oct 2026)
    # Rule: no object without a cited source (owner, 20 Oct 2026, after the round-2 drive). Every kerb, wall, tyre wall,
    # fence, grandstand, corner station and cone line below names its source: a clean z20 capture (compare/sonoma/
    # satellite_clean, 2026 imagery, 0.117 m/px), the March 2026 Lemons onboard youtube.com/watch?v=RAZip6S84CM (m:ss),
    # a Street View panorama id (July 2011, checked against the onboard: the Dec 2023 - Feb 2024 repave repainted the
    # kerbs red / white and the walls light blue), or an OSM id. The object-by-object record is compare/sonoma/
    # manifest.md. No rule-placed kerbs, boards, flag stand or pit wall at Sonoma (the rules stay for Laguna).
    scenery=dict(
        brake_board_corners=[],      # no brake boards in the 2026 onboard at T2 (0:09-0:12), T4 (0:28-0:33), T7a (1:09-1:12), T11 (1:52-1:57)
        corner_boards=False,         # no turn boards either ("Turn 1" / "Turn 7" are painted on the road in Street View)
        flagstand=False,             # no starter's stand over the pit wall at the line (onboard 2:16-2:19)
        pit_wall=dict(rule=False),   # every pit-side wall is declared below from the captures
        # the pit-exit cone line starts where the pit wall AT the edge ends (its nose, s ~103), not at the pit-out lane's
        # paddock-side wall (c20_s1815 / c20_s1870: painted blend line from the nose to the merge)
        pit_exit_near_wall_only=True,
        # kerbs: red / white painted concrete in 2026 at every corner the onboard shows (0:10 T2 entry, 0:13 T2, 0:24 T3,
        # 0:30-0:38 T4, 0:55-1:00 Carousel, 1:12-1:16 T7 / 7a islands, 1:18-1:28 T8 / 8a / T9, 1:39-1:45 9a / T10,
        # 2:01-2:04 T11); the July 2011 Street View blue / white (H9xspk4q_OoFIjVDhaMzDA, J6fsnW4hj4xCjQLzrgRGzA,
        # xXQqyp9Q9sWv9ZLN2ORYsA) predates the repave. Blocks 0.95 m (16 px period on c20_o0715); 0.65 m wide, lying
        # just beyond the painted edge line (c20_s3355 Carousel apex, c20_s2530 3a: the blocks start at the line's outer
        # side), so each strip's band is centred 0.3 m beyond the edge. Profile: stepped concrete, higher than Laguna's
        # flat strip (owner: "more aggressive, you can feel it in the car"; Street View J6fsnW4hj4xCjQLzrgRGzA and
        # gd1SNdksCq5QZtwlsrzR7g show a sloped face of ~10-15 cm): 10 cm, its track-side face rising over 0.25 m, the
        # back dropping to the ground over 0.3 m. No green after-kerb strip (none in the captures or the onboard).
        kerb=dict(width=0.65, stripe_m=0.95, colors=['#b8433a', '#dedbd2'],
                  palettes={'red': ['#b8433a', '#dedbd2'], 'blue': ['#5b7ea8', '#d9d8cf']},
                  profile=dict(height=0.10, face=0.25, back=0.30)),
        # every strip: detected on the 2026 captures by compare/kerb_detect.py (block pattern) or seen on the straightened
        # strips (compare/capstrip.py), confirmed on the onboard; a, b = its ends on the edge (lat, lon)
        kerbs_declared=[
            dict(side='right', a=(38.1621761, -122.4558020), b=(38.1621947, -122.4559702), colors='red', off=0.3, name='T1 exit right, run 1 of the broken kerb',
                 src='c20_s1870 (detector run 116.7-129.7, block pattern), feature note c20_s1925'),
            dict(side='right', a=(38.1622014, -122.4561228), b=(38.1622035, -122.4562040), colors='red', off=0.3, name='T1 exit right, run 2',
                 src='c20_s1870 (detector 143.7-149.7)'),
            dict(side='right', a=(38.1622058, -122.4563328), b=(38.1621982, -122.4565440), colors='red', off=0.3, name='T1 exit right, run 3',
                 src='c20_s1870 / c20_s1925 (detector 161.6-178.6, red)'),
            dict(side='right', a=(38.1621861, -122.4568047), b=(38.1621940, -122.4570057), colors='red', off=0.3, name='T1 exit right, run 4',
                 src='c20_s1925 (detector 203.5-219.5)'),
            dict(side='left', a=(38.1616611, -122.4580486), b=(38.1613606, -122.4582911), colors='red', off=0.3, name='T2 entry, outside (owner_3)',
                 src='c20_s2090 / c20_s2035 blocks on the left edge (capstrip s300); onboard RAZip6S84CM 0:10 red/white kerb left on entry'),
            dict(side='right', a=(38.1612090, -122.4585461), b=(38.1610716, -122.4590163), colors='red', off=0.3, name='T2 apex',
                 src='c20_s2145 (detector 412.1-428.0, 436.0-451.0); onboard 0:13-0:14 red/white apex kerb right'),
            dict(side='right', a=(38.1619167, -122.4603232), b=(38.1622785, -122.4606472), colors='red', off=0.3, name='T3 approach, right',
                 src='c20_s2365 (detector 610.6-655.5, red); onboard 0:20.6-0:21 kerb on the right'),
            dict(side='left', a=(38.1624585, -122.4609959), b=(38.1625770, -122.4615314), colors='red', off=0.3, name='T3 apex',
                 src='c20_s2420 / c20_s2475 blocks on the left edge (capstrip s600); onboard 0:24 red/white kerb left'),
            dict(side='right', a=(38.1626675, -122.4617129), b=(38.1627262, -122.4622560), colors='red', off=0.3, name='T3a apex (right; no kerb on the left of 3a)',
                 src='c20_s2530 (detector 781.2-814.2) and blocks from 760 (capstrip s750)'),
            dict(side='left', a=(38.1629296, -122.4626566), b=(38.1637196, -122.4633060), colors='red', off=0.3, name='T4 entry, outside',
                 src='c20_s2585..s2750 blocks on the left edge (capstrip s750/s900); onboard 0:30-0:32 red/white kerb left'),
            dict(side='right', a=(38.1639939, -122.4633539), b=(38.1642332, -122.4631995), colors='red', off=0.3, name='T4 apex',
                 src='c20_s2750 (detector 995.8-1027.7, red); onboard 0:34-0:36 red/white apex kerb right'),
            dict(side='left', a=(38.1643028, -122.4633233), b=(38.1644968, -122.4625410), colors='red', off=0.3, name='T4 exit, outside',
                 src='c20_s2750..s2860 blocks on the left edge (capstrip s900/s1050); onboard 0:38 red/white kerb left'),
            dict(side='right', a=(38.1644932, -122.4618956), b=(38.1641441, -122.4607970), colors='red', off=0.3, name='T5 apex and exit',
                 src='c20_s2860..s2970 (detector 1154.4-1165.4, 1182.3-1261.2, red)'),
            dict(side='left', a=(38.1629847, -122.4582212), b=(38.1634238, -122.4580951), colors='red', off=0.3, name='Carousel (T6) apex',
                 src='c20_s3355 / c20_s3410 (detector 1591.4-1646.3); onboard 0:55 red/white kerb left'),
            dict(side='right', a=(38.1640788, -122.4583265), b=(38.1644928, -122.4590012), colors='red', off=0.3, name='Carousel exit, right',
                 src='c20_s3465 / c20_s3520 (detector 1721.1-1796.0, red); onboard 0:60 red/white kerb right'),
            dict(side='right', a=(38.1660531, -122.4625071), b=(38.1663429, -122.4623758), colors='red', off=0.3, name='T7 island (apex)',
                 src='c20_s3905 / c20_s3960 (detector 2172.1-2180.1, 2188.1-2201.1); satellite owner_9; onboard 1:12 red/white island kerb'),
            dict(side='right', a=(38.1663894, -122.4623279), b=(38.1664626, -122.4616350), colors='red', off=0.3, name="T7a island (O'Reilly)",
                 src='c20_s3960..s4070 (detector 2216.0-2223.0, 2324.8-2331.8; blocks along the island, capstrip s2250); onboard 1:16 red/white'),
            dict(side='left', a=(38.1667780, -122.4615777), b=(38.1662003, -122.4612627), colors='red', off=0.3, name='T7a exit, outside',
                 src='c20_s4015 / c20_s4070 / c20_s0000 (detector 2299.8-2309.8, 2315.8-2371.7); satellite owner_9 outer kerb'),
            dict(side='left', a=(38.1659810, -122.4609435), b=(38.1658234, -122.4606740), colors='red', off=0.3, name='T8 apex',
                 src='c20_s0055 (detector 2417.6-2440.5, red); onboard 1:18-1:20 red/white kerb left'),
            dict(side='right', a=(38.1657094, -122.4607681), b=(38.1652733, -122.4596928), colors='red', off=0.3, name='T8a apex',
                 src='c20_s0055..s0165 (detector 2441.5-2447.5, 2479.4-2505.4, 2523.3-2537.3; blocks capstrip s2400); onboard 1:22-1:24'),
            dict(side='left', a=(38.1655429, -122.4598331), b=(38.1651945, -122.4594269), colors='red', off=0.3, name='T8a exit, outside',
                 src='c20_s0165 / c20_s0220 (detector 2542.3-2572.2); onboard 1:26 red/white kerb left'),
            dict(side='left', a=(38.1650454, -122.4591963), b=(38.1649276, -122.4587442), colors='red', off=0.3, name='T9 apex',
                 src='c20_s0220 / c20_s0275 (detector 2600.2-2645.1, red); onboard 1:28'),
            dict(side='right', a=(38.1648360, -122.4582215), b=(38.1646912, -122.4577513), colors='red', off=0.3, name='T9 exit, outside',
                 src='c20_s0330 / c20_s0385 (detector 2692.0-2739.8, red)'),
            dict(side='right', a=(38.1630881, -122.4552904), b=(38.1629460, -122.4551790), colors='red', off=0.3, name='9a chicane, right-hand part apex',
                 src='c20_o0660 (detector 3021.2-3036.2, red); onboard 1:39 kerb right'),
            dict(side='left', a=(38.1628061, -122.4550548), b=(38.1624095, -122.4542271), colors='red', off=0.3, name='9a chicane left-hand part apex and on to T10',
                 src='c20_o0715 / c20_s0715 / c20_s0770 (detector 3060.1-3169.9); onboard 1:41 red/white kerb left'),
            dict(side='right', a=(38.1622297, -122.4537575), b=(38.1618148, -122.4531362), colors='red', off=0.3, name='T10 apex',
                 src='c20_s0825..s0935 (detector 3219.8-3292.6, red); onboard 1:45'),
            dict(side='left', a=(38.1614869, -122.4527961), b=(38.1609287, -122.4525711), colors='red', off=0.3, name='T10 exit, outside',
                 src='c20_s0990 / c20_s1045 (detector 3338.5-3369.4, 3379.4-3402.4)'),
            dict(side='right', a=(38.1590671, -122.4520153), b=(38.1589844, -122.4525287), colors='red', off=0.3, name='T11 hairpin apex',
                 src='c20_s1265..s1375 (detector 3628.8-3673.7, 3700.7-3730.6; blocks capstrip s3600); onboard 2:01-2:04 red/white'),
        ],
        # walls OSM does not map, measured on the clean captures with compare/wall_measure.py (bright concrete top or
        # dark tyre stack, picked every 0.5 m across a guide, median 9 + Gaussian 3 m), every 10 m. Wall paint: light
        # blue in 2026 (onboard 0:03, 0:58-1:12, 1:56-2:19).
        declared_walls=[
            dict(name='pit straight, pit-lane side, to its nose at T1', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='c20_s1595..s1870 bright band 2.0 m beyond the left edge (19 Oct); nose on c20_s1815 (s ~103); onboard 2:16-2:20',
                 latlon=[
                (38.1606469, -122.4535036), (38.1607541, -122.4536697), (38.1608652, -122.4538464),
                (38.1609772, -122.4540279), (38.1610893, -122.4542076), (38.1612006, -122.454387),
                (38.1613123, -122.4545663), (38.1614237, -122.4547457), (38.1615466, -122.4549429),
                (38.1616582, -122.455122), (38.1617703, -122.4553019), (38.1618793, -122.4554785),
                (38.1619647, -122.4556086)]),
            dict(name='pit-out lane, paddock side', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='c20_s1870 / c20_s1925, bright band along the lane outer side (wall_measure, 87 % picked, rms 0.30 m); onboard 2:23 / 0:06.5',
                 latlon=[
                (38.1619153, -122.4557708), (38.161916, -122.4558863), (38.1619357, -122.455998),
                (38.1619491, -122.456111), (38.1619592, -122.4562246), (38.1619666, -122.4563384),
                (38.1619792, -122.4564517), (38.1619856, -122.4565657), (38.1619903, -122.4566799),
                (38.1619944, -122.4567942), (38.1619986, -122.4568797),
                ]),
            dict(name='pit straight, drag-strip side', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='c20_s1595..s1870 bright band 2.3 m beyond the right edge (19 Oct); Street View 5MY4xR9O7etAXEHnZCVnGQ; onboard 2:17',
                 latlon=[
                # T12 exit to the timing line (c20_s1540 / c20_s1595, wall_measure along the right edge, 86 % picked, offset p50 1.7 m)
                (38.1604988, -122.4531009), (38.1605773, -122.4531593), (38.1606586, -122.4532076), (38.1607262, -122.4532828), (38.1607948, -122.453355), (38.1608526, -122.4534417), (38.1609081, -122.4535313), (38.160958, -122.4536264), (38.1610044, -122.4537248), (38.1610601, -122.4538148), (38.1611029, -122.4538595),
                (38.1611834, -122.4539958), (38.161300, -122.4541846), (38.161412, -122.4543637),
                (38.1615237, -122.4545429), (38.1616354, -122.4547222), (38.1617473, -122.4549012),
                (38.1618596, -122.4550797), (38.1619709, -122.4552587), (38.1620296, -122.4553516)]),
            dict(name='T6 to T7, left (Carousel exit along the drag strip and the T7 road)', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='c20_s3465..s3850 bright band at the asphalt end (wall_measure along the left edge, 83 % picked, rms 0.11 m, gaps bridged); onboard 0:58-1:12 light-blue wall, Toyota boards at 1:10',
                 latlon=[
                (38.163533, -122.4581187), (38.1636186, -122.4581558), (38.1637009, -122.4582033),
                (38.1637785, -122.4582623), (38.1638518, -122.4583299), (38.1639163, -122.4584107),
                (38.1639726, -122.4585003), (38.1640285, -122.4585899), (38.1640845, -122.4586792),
                (38.1641401, -122.458769), (38.1641959, -122.4588585), (38.1642518, -122.4589479),
                (38.1643076, -122.4590374), (38.1643635, -122.4591268), (38.1644192, -122.4592165),
                (38.1644751, -122.459306), (38.1645307, -122.4593958), (38.1645863, -122.4594854),
                (38.1646417, -122.4595752), (38.1646973, -122.459665), (38.1647531, -122.4597546),
                (38.1648089, -122.4598442), (38.1648632, -122.4599352), (38.1649184, -122.4600253),
                (38.1649736, -122.4601154), (38.1650283, -122.4602071), (38.1650491, -122.4602584),
                (38.1650717, -122.4603704), (38.165105, -122.4604769), (38.1651383, -122.4605649),
                (38.1651667, -122.4606364), (38.1652077, -122.4607378), (38.1652481, -122.4608395),
                (38.1652581, -122.4608713), (38.1652838, -122.4609506), (38.1653253, -122.4610524),
                (38.1653708, -122.4611512), (38.1654108, -122.4612535), (38.1654255, -122.4612953),
                (38.1654681, -122.4614023), (38.1655105, -122.461503), (38.1655508, -122.4616052),
                (38.1655902, -122.4617079), (38.1656276, -122.4618119), (38.1656699, -122.4619127),
                (38.1657118, -122.4620137), (38.1657519, -122.4621158), (38.1657757, -122.4621773),
                ]),
            dict(name='T7 approach, left tyre wall', kind='tyres', h=1.0, fence=0.0,
                 src='c20_s3850 / c20_s3905 dark tyre stack 4-10 m beyond the left edge (96 % picked, rms 0.35 m); Street View gd1SNdksCq5QZtwlsrzR7g',
                 latlon=[
                (38.1655798, -122.4617596), (38.1656263, -122.4618583), (38.1656577, -122.4619656),
                (38.1656929, -122.4620707), (38.1657243, -122.4621779), (38.1657594, -122.4622831),
                (38.1657918, -122.4623896), (38.1658239, -122.4624963), (38.1658571, -122.4626024),
                ]),
            dict(name='T5 to the T6 crest, right', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='c20_s2860..s3080 light wall line 3-6 m beyond the right edge (76 % picked); onboard 0:43-0:48.5 concrete wall on the right (not in the Jul 2011 Street View GMaTaipEd9Hm7fMNE26aGQ: built since)',
                 latlon=[
                (38.1644291, -122.4619012), (38.1644384, -122.4618115), (38.164431, -122.4616934),
                (38.1644188, -122.461581), (38.1643997, -122.4614694), (38.1643726, -122.4613603),
                (38.1643394, -122.4612537), (38.1642991, -122.461151), (38.1642483, -122.4610561),
                (38.1641907, -122.460968), (38.1641318, -122.4608838), (38.1640675, -122.4608067),
                (38.1639972, -122.4607368), (38.1639247, -122.4606692), (38.1638527, -122.4606005),
                (38.1637802, -122.4605327), (38.1637077, -122.4604649), (38.1636327, -122.4604017),
                (38.1635576, -122.4603389), (38.163482, -122.4602772), (38.1634056, -122.4602168),
                (38.1633771, -122.4601993),
                ]),
            dict(name='T8a to T9, left (the bank)', kind='tyres', h=1.0, fence=0.0,
                 src='c20_s0110 / c20_s0165 dark barrier ~20 m left (99 % picked, rms 0.34 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA',
                 latlon=[
                (38.1658696, -122.4602454), (38.1658579, -122.4601295), (38.165808, -122.4600325),
                (38.1657583, -122.4599381), (38.1657083, -122.4598453), (38.165655, -122.4597548),
                (38.1655975, -122.4596672), (38.1655336, -122.4595876), (38.1654633, -122.4595172),
                (38.1653939, -122.4594453), (38.1653256, -122.4593708), (38.1652641, -122.459286),
                (38.1652155, -122.4592262),
                ]),
            dict(name='T9, left (the bank)', kind='concrete', h=1.0, fence=3.0, color='#a9c9dd',
                 src='c20_s0220 / c20_s0275 bright wall ~19 m left (95 % picked, rms 0.27 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA (wall + catch fence on the bank)',
                 latlon=[
                (38.1652099, -122.4592275), (38.1651617, -122.4591306), (38.165111, -122.4590365),
                (38.1650715, -122.4589334), (38.165051, -122.4588218), (38.165043, -122.4587084),
                (38.1650435, -122.4585948), (38.1650446, -122.4584802), (38.165051, -122.4583666),
                (38.16505, -122.4582533), (38.1650495, -122.4582307),
                ]),
            dict(name='T8a, right (toward the 2020 bypass)', kind='tyres', h=1.0, fence=0.0,
                 src='c20_s0165 / c20_s0220 dark tyre stack 10-18 m right (95 % picked, rms 0.59 m); onboard 1:24',
                 latlon=[
                (38.1654018, -122.4600434), (38.1653398, -122.4599595), (38.1652854, -122.4598698),
                (38.1652292, -122.4597805), (38.1651585, -122.4597086), (38.1650985, -122.4596231),
                (38.1650363, -122.4595394), (38.1649822, -122.4594469), (38.164953, -122.4593883),
                ]),
            dict(name='T11 exit to T12, left (pit-road side)', kind='concrete', h=1.0, fence=0.0, color='#e6e4de',
                 src='c20_s1320..s1540 bright wall at the left edge from the hairpin exit (100 % picked, rms 0.14 m); onboard 2:06-2:11 white wall left',
                 latlon=[
                (38.1585718, -122.4524793), (38.1586504, -122.4525398), (38.1587351, -122.4525781),
                (38.1588199, -122.452612), (38.1589056, -122.4526456), (38.1589915, -122.4526799),
                (38.1590772, -122.4527143), (38.1591628, -122.4527488), (38.1592485, -122.4527829),
                (38.1593344, -122.4528166), (38.15942, -122.4528514), (38.1595056, -122.4528859),
                (38.1595913, -122.4529203), (38.1596769, -122.4529547), (38.1597626, -122.4529892),
                (38.1598482, -122.4530236), (38.1599339, -122.453058), (38.1600194, -122.4530928),
                (38.1601051, -122.4531273), (38.1601906, -122.4531635), (38.1602754, -122.453203),
                (38.1603584, -122.4532488), (38.1604392, -122.4533007), (38.1605176, -122.4533589),
                (38.1605909, -122.4534287), (38.1606552, -122.4535117), (38.1607059, -122.453593),
                ]),
            dict(name='drag strip, track (SW) side, past T1 to the Carousel exit', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd', drop_within=0.0,
                 src='c20_s1870 / c20_s1815 / c20_s0550 / c20_s3355: the bright wall along the drag strip SW edge (wall_measure along the paved part edge, 100 % picked, rms 0.22 m); Street View l9CetikWiRZTe2ONpwxrQQ; onboard 2:20',
                 latlon=[
                (38.1620296, -122.4553516), (38.1620416, -122.4554152), (38.1620972, -122.4555049),
                (38.162153, -122.4555944), (38.1622088, -122.455684), (38.1622647, -122.4557734),
                (38.1623204, -122.4558631), (38.1623763, -122.4559525), (38.1624322, -122.456042),
                (38.1624882, -122.4561313), (38.1625442, -122.4562206), (38.1626002, -122.45631),
                (38.1626561, -122.4563993), (38.1627123, -122.4564885), (38.1627683, -122.4565778),
                (38.1628243, -122.4566672), (38.1628803, -122.4567565), (38.1629364, -122.4568458),
                (38.1629925, -122.456935), (38.1630482, -122.4570246), (38.1631042, -122.457114),
                (38.1631601, -122.4572035), (38.163216, -122.4572929), (38.163272, -122.4573822),
                (38.1633278, -122.4574717), (38.1633839, -122.457561), (38.1634399, -122.4576504),
                (38.1634959, -122.4577396), (38.1635518, -122.4578291), (38.1636072, -122.4579189),
                (38.1636647, -122.4580082), (38.1637426, -122.4580595),
                ]),
            dict(name='drag strip, infield (NE) side', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd', drop_within=0.0,
                 src='c20_s0495..s1760: the bright wall along the drag strip NE edge (530 m, 100 % picked, rms 0.14 m); dropped where the course runs on the drag strip (Carousel exit)',
                 latlon=[
                (38.1608826, -122.4532313), (38.1609395, -122.4533196), (38.160999, -122.4534055),
                (38.1610561, -122.4534937), (38.1611097, -122.4535855), (38.161169, -122.4536715),
                (38.161225, -122.4537608), (38.1612808, -122.4538504), (38.1613364, -122.4539401),
                (38.1613921, -122.4540298), (38.1614481, -122.4541191), (38.1615038, -122.4542087),
                (38.1615595, -122.4542984), (38.1616154, -122.4543878), (38.1616712, -122.4544773),
                (38.1617269, -122.454567), (38.1617828, -122.4546564), (38.1618386, -122.454746),
                (38.1618943, -122.4548356), (38.1619503, -122.4549249), (38.1620061, -122.4550145),
                (38.1620621, -122.4551038), (38.1621177, -122.4551935), (38.1621737, -122.4552828),
                (38.1622295, -122.4553725), (38.1622851, -122.4554621), (38.162341, -122.4555516),
                (38.1623969, -122.4556411), (38.1624525, -122.4557307), (38.1625086, -122.45582),
                (38.1625646, -122.4559093), (38.1626206, -122.4559987), (38.1626759, -122.4560887),
                (38.1627319, -122.456178), (38.1627877, -122.4562676), (38.1628437, -122.4563569),
                (38.1628995, -122.4564465), (38.1629556, -122.4565357), (38.1630118, -122.4566248),
                (38.1630678, -122.4567141), (38.1631239, -122.4568034), (38.1631799, -122.4568928),
                (38.1632358, -122.4569822), (38.1632916, -122.4570717), (38.1633475, -122.4571611),
                (38.1634031, -122.4572509), (38.1634589, -122.4573405), (38.1635147, -122.45743),
                (38.1635708, -122.4575193), (38.1636269, -122.4576084), (38.163683, -122.4576977),
                (38.163739, -122.4577871), (38.1637951, -122.4578763), (38.1638513, -122.4579654),
                (38.1638569, -122.4579743),
                ]),
            dict(name='T11 entry, left: wall between the track and the pit-in lane', kind='concrete', h=1.0, fence=0.0, color='#c9473e',
                 src='c20_s1210 / c20_s1265 bright line 10.8 m left (93 % picked, rms 0.05 m); onboard 1:59 red / white painted concrete on the left',
                 latlon=[
                (38.1596288, -122.4520274), (38.1595436, -122.4519911), (38.1594586, -122.4519543),
                (38.1593734, -122.4519178), (38.1592884, -122.4518806), (38.1592035, -122.4518434),
                (38.1591185, -122.4518066), (38.159033, -122.4517702), (38.1589441, -122.451747),
                (38.1588895, -122.4517436),
                ]),
            dict(name='T11 hairpin, left tyre wall', kind='tyres', h=1.0, fence=0.0,
                 src='c20_s1265 / c20_s1320 white tyre band on the outside of the hairpin (69 % picked, rms 0.35 m); onboard 2:04 white tyre stacks left',
                 latlon=[
                (38.158888, -122.451793), (38.158799, -122.4517857), (38.1587102, -122.4518038),
                (38.1586262, -122.4518483), (38.1585597, -122.4519283), (38.1585112, -122.4520259),
                (38.1584808, -122.4521362), (38.1584838, -122.4522525), (38.1585119, -122.4523626),
                (38.1585634, -122.4524562), (38.1586344, -122.4525261), (38.1587172, -122.4525726),
                (38.1587582, -122.4525939),
                ]),
            dict(name='T3, right: low tyre-faced wall far out', kind='tyres', h=1.0, fence=0.0,
                 src='c20_s2365..s2475 dark line 34-36 m right (100 % picked, rms 0.70 m); Street View exOejoRD5-jF1wceBnhfjg',
                 latlon=[
                (38.1620501, -122.4600578), (38.1621207, -122.4601288), (38.1621945, -122.4601941),
                (38.1622675, -122.4602589), (38.1623428, -122.4603207), (38.1624177, -122.4603845),
                (38.1624908, -122.4604501), (38.162565, -122.4605126), (38.1626387, -122.460577),
                (38.1627147, -122.4606415), (38.1627769, -122.4607257), (38.1628303, -122.4608201),
                (38.1628642, -122.460928), (38.1629103, -122.4610284), (38.162927, -122.4611422),
                (38.1629533, -122.4612533), (38.1629609, -122.4613685), (38.1629611, -122.461484),
                (38.1629553, -122.4615987), (38.1629473, -122.4617129), (38.1629364, -122.4618264),
                (38.1629329, -122.4619396), (38.1629327, -122.4619453),
                ]),
            dict(name='T4 approach, left: wall and catch fence below the T3a-T4 stands', kind='concrete', h=1.0, fence=3.0, color='#a9c9dd',
                 src='c20_s2475..s2640 dark wall line 17-23 m left (97 % picked, rms 0.64 m); Street View nA1oaDXwADSI7x-Pa-j4Ow (wall + ~3 m catch fence left); onboard 0:28-0:32',
                 latlon=[
                (38.1624738, -122.4614233), (38.1624636, -122.4615377), (38.1624324, -122.4616472),
                (38.1624314, -122.461763), (38.1624202, -122.4618754), (38.1624141, -122.4619878),
                (38.1624179, -122.4620994), (38.1624335, -122.4622095), (38.1624569, -122.4623177),
                (38.162493, -122.4624242), (38.1625537, -122.4625099), (38.1626299, -122.4625736),
                (38.1627013, -122.4626409), (38.1627748, -122.4627036), (38.1628521, -122.4627608),
                (38.1629308, -122.4628152), (38.1630099, -122.4628689), (38.1630409, -122.462892),
                ]),
            dict(name='T4, right: tyre line beyond the runoff', kind='tyres', h=1.0, fence=0.0,
                 src='c20_s2640 / c20_s2695 dark tyre line 20-30 m right (79 % picked, rms 0.32 m)',
                 latlon=[
                (38.1629449, -122.462163), (38.1630084, -122.4622443), (38.1630649, -122.4623338),
                (38.1631408, -122.4623953), (38.1632225, -122.4624437), (38.1633035, -122.4624939),
                (38.1633815, -122.4625506), (38.1634589, -122.4626098), (38.1635328, -122.462675),
                (38.1636063, -122.4627406), (38.1636174, -122.4627504), (38.1637605, -122.4629255),
                (38.16382, -122.4630087), (38.1638613, -122.4630761),
                ]),
            dict(name='back straight, left: wall and catch fence at the foot of the stands', kind='concrete', h=1.0, fence=3.0, color='#a9c9dd',
                 src='c20_o0440..o0550 dark line ~25 m left at the foot of the stands (100 % picked, rms 1.06 m: the weakest measurement); onboard 1:33-1:36 light-blue wall with catch fence left',
                 latlon=[
                (38.1646464, -122.4571881), (38.164585, -122.4571034), (38.1645276, -122.4570133),
                (38.1644804, -122.4569149), (38.1644439, -122.456808), (38.1643735, -122.4567318),
                (38.1643314, -122.4566294), (38.1642626, -122.4565535), (38.1642054, -122.4564655),
                (38.1641488, -122.4563768), (38.1640949, -122.4562852), (38.1640334, -122.4562017),
                (38.1639759, -122.4561145), (38.1639173, -122.4560279), (38.1638602, -122.4559397),
                (38.1638257, -122.4558265), (38.1637677, -122.4557392), (38.1637073, -122.4556526),
                (38.1636444, -122.4555714), (38.1635815, -122.4554898), (38.1635175, -122.4554089),
                (38.163459, -122.4553375),
                ]),
            dict(name='back straight start, left tyre line', kind='tyres', h=1.0, fence=0.0,
                 src='c20_s0330 / c20_s0385 dark tyre line ~21 m left (78 % picked, rms 0.72 m)',
                 latlon=[
                (38.1650939, -122.4581954), (38.1650639, -122.4580853), (38.1650497, -122.4579728),
                (38.1650114, -122.4578695), (38.1649757, -122.4577658), (38.1649311, -122.4576678),
                (38.1648827, -122.4575726), (38.1648592, -122.4575312),
                ]),
            dict(name='T10 to T11, left wall with the ad boards', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='c20_s0825..s1100 dark wall line 10-22 m left (96 % picked, rms 0.76 m); Street View jrXpHaDfJT2APw6zcyBKRA (ad boards); onboard 1:46-1:57 (Sunbelt, Toyota, zMAX boards on the wall)',
                 latlon=[
                (38.1625428, -122.4542559), (38.1625395, -122.4541403), (38.1625247, -122.4540276),
                (38.1625058, -122.453916), (38.1624965, -122.4538018), (38.1624702, -122.4536924),
                (38.1624246, -122.4535929), (38.1623935, -122.4534861), (38.162358, -122.4533797),
                (38.1623083, -122.4532829), (38.1622458, -122.4531995), (38.1621692, -122.4531349),
                (38.162103, -122.4530595), (38.1620334, -122.452989), (38.1619606, -122.4529237),
                (38.1618849, -122.4528645), (38.1618062, -122.4528116), (38.161727, -122.4527591),
                (38.161642, -122.4527238), (38.1615634, -122.4526635), (38.1614796, -122.4526209),
                (38.1613925, -122.4525888), (38.1613003, -122.4525877), (38.1612115, -122.4525684),
                (38.1611243, -122.4525417), (38.1610372, -122.4525149), (38.1609531, -122.4524679),
                (38.1608659, -122.4524393), (38.1607769, -122.4524242), (38.1606905, -122.4523933),
                (38.160602, -122.4523738), (38.1605128, -122.4523564), (38.1604242, -122.4523371),
                (38.1603536, -122.4523199),
                ]),
            dict(name='T10 to T11, right wall and catch fence', kind='concrete', h=1.0, fence=3.0, color='#a9c9dd',
                 src='c20_s0880..s1045 bright line ~18 m right (55 % picked, rms 0.60 m, gaps bridged); onboard 1:43-1:52 concrete wall with catch fence on the right',
                 latlon=[
                (38.1621134, -122.4537615), (38.162081, -122.4536551), (38.1620705, -122.4536365),
                (38.161952, -122.4534516), (38.1618963, -122.4533595), (38.1618188, -122.4532991),
                (38.1617403, -122.4532436), (38.1616613, -122.4531909), (38.1615811, -122.453141),
                (38.1615002, -122.4530903), (38.1614173, -122.4530449), (38.1613475, -122.4530221),
                (38.1611374, -122.4529389), (38.1610518, -122.4529042), (38.1609663, -122.4528684),
                (38.1608779, -122.4528457), (38.1607915, -122.4528143), (38.1607144, -122.4527831),
                ]),
        ],
        # the hillside grandstands (OSM building=grandstand) as stepped concrete terraces on the DEM, with the top fence
        # the Street View and onboard show (T7a: J6fsnW4hj4xCjQLzrgRGzA, onboard 1:14; T3a-T4: nA1oaDXwADSI7x-Pa-j4Ow,
        # onboard 0:28-0:32; above T2: H9xspk4q_OoFIjVDhaMzDA, onboard 0:15; back straight / 9a: xkSrqJ5RaN9WFLncaiqaug,
        # onboard 1:33-1:36)
        grandstand_on_terrain=True,
        # building heights from a robust lidar statistic (p60 above the footprint's ground; p50 where p90 - p50 > 6 m; no
        # structure above 2.5 m: dropped): the p85 rule made the main grandstand at the line a 25.6 m block (timing tower,
        # masts and the stand's slope inside the OSM outline). Laguna keeps the old rule (byte-identical package).
        building_height_robust=True,
        terraces=[
            dict(name='T7a hill', osm='1414701937', src='OSM 1414701937; Street View J6fsnW4hj4xCjQLzrgRGzA (terraces, fence and light masts on top); onboard 1:14'),
            dict(name='T3a-T4', osm='1414701938', src='OSM 1414701938; Street View nA1oaDXwADSI7x-Pa-j4Ow (~20 concrete rows); onboard 0:28-0:32'),
            dict(name='above T2', osm='1414701939', src='OSM 1414701939; Street View H9xspk4q_OoFIjVDhaMzDA; onboard 0:15-0:16 (fence and light poles on top)'),
            dict(name='back straight / 9a', osm='1414701936', src='OSM 1414701936; Street View xkSrqJ5RaN9WFLncaiqaug; onboard 1:33-1:36'),
        ],
        # corner-worker stations measured on the captures (small raised platforms beside the track) and confirmed on the onboard
        marshal_posts=[
            dict(name='T6 hilltop', latlon=(38.1631039, -122.4600748), h=2.6, style='platform',
                 src='c20_s3135: a ~3 x 3 m platform with a box behind the right wall at the crest before the Carousel; Street View GMaTaipEd9Hm7fMNE26aGQ (Jul 2011): white box and tyre stack there (owner: "the one at the top of the hill just before T6")'),
            dict(name='T4', latlon=(38.1639325, -122.4631172), h=4.0,
                 src='c20_s2695: a raised hut on a platform 27 m right of the T4 approach (long shadow); onboard 0:33 white elevated post with roof on the right; Street View 3a panorama (Jul 2011) shows it ahead right'),
            dict(name='T7', latlon=(38.1659466, -122.4626554), h=4.0,
                 src='c20_s3905: a post at the end of the left wall at T7; onboard 1:11 raised white post with roof ahead'),
        ],
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

        # a closed road's paving stops at its walls (the drag strip's NAIP width reached under the pit-straight wall)
        closed_roads_clip_walls=True,
        # containment gate: paved surfaces the cars can really reach across open ground (no barrier in the captures or the
        # onboard), each with its evidence; everything else must be behind a barrier or a cone line
        gates=dict(allowed=[
            dict(target='pit lane', side='left', a=(38.1619904, -122.4554842), b=(38.1620676, -122.4556893),
                 why='the pit-wall nose at T1 (c20_s1815): beyond it the pit-out lane runs beside the track behind the painted blend line and its cones (pit_exit_cones) to the merge'),
            dict(target='the Chute (NASCAR short course, T4 to T7)', side='left', a=(38.1639396, -122.4634002), b=(38.1644795, -122.4623582),
                 why='T4 exit, left: open dirt paddock to the Chute, no barrier (c20_s2750 / c20_s2805; onboard 0:34-0:38: cones at the Chute mouth, open ground left)'),
            dict(target='the Chute (NASCAR short course, T4 to T7)', side='left', a=(38.1659159, -122.4623605), b=(38.1661564, -122.4626504),
                 why="T7, left: the Chute's T7 mouth is open asphalt behind its cone line (onboard 1:05-1:12; owner_9 satellite)"),
            dict(target='2020 fast bypass (8a to T10)', side='right', a=(38.1636829, -122.4580960), b=(38.1640913, -122.4585186),
                 why='Carousel exit, right: open infield to the bypass (c20_s3465; onboard 1:00 grass right)'),
            dict(target='2020 fast bypass (8a to T10)', side='right', a=(38.1644711, -122.4573275), b=(38.1625143, -122.4550067),
                 why='back straight, right: open dirt infield (paddock) to the bypass, no barrier (c20_o0440..o0660; onboard 1:33-1:38 open right)'),
            dict(target='drag strip', side='right', a=(38.1631111, -122.4580692), b=(38.1638457, -122.4581899),
                 why='Carousel exit: the course runs onto the drag-strip start; the drag strip toward the front straight is behind its cone line (onboard 0:58-1:00)'),
            dict(target='PWC lower hairpin', side='right', a=(38.1656123, -122.4615977), b=(38.1661994, -122.4613789),
                 why='inside T7 / 7a: paved runoff and the PWC hairpin are open pavement the cars may use (owner, 19 Oct; owner_9; Street View J6fsnW4hj4xCjQLzrgRGzA, gd1SNdksCq5QZtwlsrzR7g)'),
            dict(target='T11a shortcut', side='right', a=(38.1609734, -122.4526661), b=(38.1597720, -122.4522059),
                 why='T11 approach, right: the NASCAR infield is open paved ground to the 11a shortcut (Street View jrXpHaDfJT2APw6zcyBKRA: cones, tyre bundles at the 11a entry; onboard 1:56)'),
            dict(target='T11a shortcut', side='right', a=(38.1593620, -122.4527530), b=(38.1605086, -122.4532417),
                 why='T11 exit to T12, right: open paved NASCAR infield (onboard 2:06-2:11; c20_s1375..s1540)'),
        ]),
    ),
    # ---------------------------------------------------------------- app registry (src/scoreboard/config.ts)
    app=dict(short='Sonoma', pace='cars/field/sonoma/pace.json'),
)
