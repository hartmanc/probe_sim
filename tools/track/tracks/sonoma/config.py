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
        # side), so each strip's band is centred 0.3 m beyond the edge. Profile: raised concrete, higher than Laguna's
        # flat strip (owner: "more aggressive, you can feel it in the car"). 5 cm, the track-side face rising over
        # 0.25 m, the back easing to the ground over 0.6 m (20 Oct 2026, was 10 cm / 0.25 / 0.30, which rolled the car:
        # compare/sonoma/kerb_rollover.md). Evidence for the lower kerb: the July 2011 Street View notes read "low flat
        # concrete" (compare/sonoma/streetview.md), the owner's T7 panorama (owner_8, gd1SNdksCq5QZtwlsrzR7g) shows the
        # island dirt level with the kerb top (no drop behind it) and a low lip on the track side; a 5 cm lip at 30-45 deg
        # enveloped by the 0.316 m tyre (sqrt(2 r h) = 0.18 m) is felt as a ~0.25 m ramp. The earlier "10-15 cm" was
        # most likely the sloped face's width, not its height. No green after-kerb strip (none in the captures or the onboard).
        kerb=dict(width=0.65, stripe_m=0.95, colors=['#b8433a', '#dedbd2'],
                  palettes={'red': ['#b8433a', '#dedbd2'], 'blue': ['#5b7ea8', '#d9d8cf']},
                  profile=dict(height=0.05, face=0.25, back=0.60)),
        # every strip: detected on the 2026 captures by compare/kerb_detect.py (block pattern) or seen on the straightened
        # strips (compare/capstrip.py), confirmed on the onboard; a, b = its ends on the edge (lat, lon)
        kerbs_declared=[
            dict(side='right', a=(38.1621761, -122.4558020), b=(38.1621947, -122.4559702), colors='red', off=0.3, name='T1 exit right, run 1 of the broken kerb',
                 src='c20_s1870 (detector run 116.7-129.7, block pattern), feature note c20_s1925'),
            # T1 kerb blocks (round 4, owner note 31): the dotted line of low grey blocks between the two striped
            # sections on the outside and along the inside from the pit-wall nose, kind 'blocks' (drawn as blocks, no
            # physics kerb); kerb_detect.py runs (grey, block period ~1.9 m) confirmed on capstrip s 40-250
            dict(side='right', a=(38.1621947, -122.4559701), b=(38.1622059, -122.4563447), kind='blocks', off=0.6, name='T1 exit right, block line between the striped runs',
                 src='c20_s1870 (kerb_detect grey run 143.7-149.7 and the dotted blocks from 130 to 161 between striped runs 1 and 3); owner_31 satellite'),
            dict(side='left', a=(38.1619492, -122.4555792), b=(38.1620304, -122.4560332), kind='blocks', off=-0.15, name='T1 inside, block line from the pit-wall nose',
                 src='c20_s1815 / c20_s1870 (kerb_detect grey run 88.8-133.7, offsets -0.5..+0.2 m); owner_31 satellite (dotted block line on the inside); onboard 2:22.5'),
            dict(side='right', a=(38.1622058, -122.4563328), b=(38.1621982, -122.4565440), colors='red', off=0.3, name='T1 exit right, run 3',
                 src='c20_s1870 / c20_s1925 (detector 161.6-178.6, red)'),
            dict(side='right', a=(38.1621861, -122.4568047), b=(38.1621940, -122.4570057), colors='red', off=0.3, name='T1 exit right, run 4',
                 src='c20_s1925 (detector 203.5-219.5)'),
            dict(side='left', a=(38.1616611, -122.4580486), b=(38.1613606, -122.4582911), colors='red', off=0.3, name='T2 entry, outside (owner_3)',
                 src='c20_s2090 / c20_s2035 blocks on the left edge (capstrip s300); onboard RAZip6S84CM 0:10 red/white kerb left on entry'),
            dict(side='left', a=(38.1609628, -122.459043), b=(38.1612976, -122.4597386), colors='red', off=0.3, name='T2 exit, outside (round 5)',
                 src='c20_s2200 / c20_s2255 (kerb_detect red runs 451.0-458.0 and 465.0-519.8, 91 % of the run, offsets -0.4..+1.0 m); onboard 0:16 long red/white kerb along the left after T2'),
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
            dict(name='pit straight, pit-lane side, to its nose at T1', kind='concrete', h=1.1, fence=0.0, h_src='onboard 2:14-2:17: wall top level with the hood line at 2-3 m (SAFER-type ~1.1 m, Street View 5MY4xR9O7etAXEHnZCVnGQ ~1 m); no catch fence', color='#a9c9dd',
                 src='c20_s1595..s1870 bright band 2.0 m beyond the left edge (19 Oct); nose on c20_s1815 (s ~103); onboard 2:16-2:20',
                 latlon=[
                (38.1606469, -122.4535036), (38.1607541, -122.4536697), (38.1608652, -122.4538464),
                (38.1609772, -122.4540279), (38.1610893, -122.4542076), (38.1612006, -122.454387),
                (38.1613123, -122.4545663), (38.1614237, -122.4547457), (38.1615466, -122.4549429),
                (38.1616582, -122.455122), (38.1617703, -122.4553019), (38.1618793, -122.4554785),
                (38.1619647, -122.4556086)]),
            dict(name='pit-out lane, paddock side', kind='concrete', h=1.0, fence=1.0, color='#a9c9dd', h_src='onboard 2:22.5: low light-blue wall with a chain-link fence behind it along the pit-out lane; Street View owner_28 Pit Out (low white wall, chain-link fence beyond); round 5: the chain-link fence is 2.0 m to its top (inventory 0:06, fence-post-ref), so 1.0 m over the 1.0 m wall (was 2.0)',
                 src='c20_s1870 / c20_s1925, bright band along the lane outer side (wall_measure, 87 % picked, rms 0.30 m); onboard 2:23 / 0:06.5',
                 latlon=[
                (38.1619153, -122.4557708), (38.161916, -122.4558863), (38.1619357, -122.455998),
                (38.1619491, -122.456111), (38.1619592, -122.4562246), (38.1619666, -122.4563384),
                (38.1619792, -122.4564517), (38.1619856, -122.4565657), (38.1619903, -122.4566799),
                (38.1619944, -122.4567942), (38.1619986, -122.4568797),
                # round 5: on to its Jersey end before the footbridge (c20_s1925 / c20_s1980 wall_measure bright, 85 % picked,
                # rms 0.31 m; onboard 0:08 'the paddock-side wall of the pit-out lane ends here', Jersey end 5 m away)
                (38.1620017, -122.4569719), (38.1620076, -122.4570863), (38.1619978, -122.4572003), (38.1619769, -122.4573118),
                (38.1619426, -122.4574171), (38.1619172, -122.457483),
                ]),
            dict(name='pit straight, drag-strip side', kind='concrete', h=1.1, fence=0.0, h_src='onboard 2:14-2:17: as the pit-lane side wall, ~1.1 m, no catch fence on it (the posts at 2:17 stand beyond the drag strip)', color='#a9c9dd',
                 src='c20_s1595..s1870 bright band 2.3 m beyond the right edge (19 Oct); Street View 5MY4xR9O7etAXEHnZCVnGQ; onboard 2:17',
                 latlon=[
                # T12 exit to the timing line (c20_s1540 / c20_s1595, wall_measure along the right edge, 86 % picked, offset p50 1.7 m)
                (38.1604988, -122.4531009), (38.1605773, -122.4531593), (38.1606586, -122.4532076), (38.1607262, -122.4532828), (38.1607948, -122.453355), (38.1608526, -122.4534417), (38.1609081, -122.4535313), (38.160958, -122.4536264), (38.1610044, -122.4537248), (38.1610601, -122.4538148), (38.1611029, -122.4538595),
                (38.1611834, -122.4539958), (38.161300, -122.4541846), (38.161412, -122.4543637),
                (38.1615237, -122.4545429), (38.1616354, -122.4547222), (38.1617473, -122.4549012),
                (38.1618596, -122.4550797), (38.1619709, -122.4552587), (38.1620296, -122.4553516)]),
            dict(name='T6 to T7, left (Carousel exit along the drag strip and the T7 road)', kind='concrete', h=1.2, fence=0.0, h_src='onboard 1:09: light-blue wall a little above the hood line at 1-2 m (~1.2 m), ad boards on posts behind it (wall_boards)', color='#a9c9dd',
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
            dict(name='T9, left (the bank)', kind='concrete', h=1.0, fence=2.0, color='#a9c9dd', h_src='round 5: catch fence 3.0 m to its top (inventory 1:28, fence-post-ref), so 2.0 m over the 1.0 m wall (was 3.0)',
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
            dict(name='T11 exit to T12, left (pit-road side)', kind='concrete', h=0.81, fence=0.0, h_src='onboard 2:07: low white Jersey-section wall (Jersey 0.81 m)', color='#e6e4de',
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
            dict(name='T11 entry, left: outer pit-in wall (garage side)', kind='concrete', h=2.7, fence=0.0, color='#a9c9dd', h_src='this is the OUTER pit-in wall (10.8 m left, beside the garage), not the track-side one; round 5: 5.2 m to the board top (HEIGHTS.md examples 3 and 4: Street View jrXpHaDfJT2APw6zcyBKRA 5.22 m, onboard 1:56 door-ref 5.0-5.6 m), the concrete face 2.7 m (it holds 2.03 m doors) under 2.5 m boards (wall_boards); was 1.2 m',
                 src='c20_s1210 / c20_s1265 bright line 10.8 m left (93 % picked, rms 0.05 m); onboard 1:59 red / white painted concrete on the left',
                 latlon=[
                (38.1596288, -122.4520274), (38.1595436, -122.4519911), (38.1594586, -122.4519543),
                (38.1593734, -122.4519178), (38.1592884, -122.4518806), (38.1592035, -122.4518434),
                (38.1591185, -122.4518066), (38.159033, -122.4517702), (38.1589441, -122.451747),
                (38.1588895, -122.4517436),
                ]),
            dict(name='T11 hairpin, left tyre wall', kind='tyres', h=1.0, fence=2.0, h_src='onboard 2:01.5-2:03.5: white tyre stacks ~1 m in front of the light-blue wall with a catch fence; round 5: fence top 3.0 m, between the 3.5 m catch fence at 2:02 and the 2.5 m chain-link at 2:04 (inventory, fence-post-ref; was 4.0)',
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
            dict(name='T10 to T11, left wall with the ad boards', kind='concrete', h=1.2, fence=0.0, h_src='onboard 1:43-1:55: wall ~1.2 m under a continuous row of ~2.5 m ad boards (wall_boards); owner note 13/14 "much higher"', color='#a9c9dd',
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
            dict(name='T10 to T11, right wall and catch fence', kind='concrete', h=1.1, fence=3.5, h_src='onboard 1:43.2-1:50: concrete ~1.1 m, catch-fence posts about three wall heights above it (~3.5 m)', color='#a9c9dd',
                 src='c20_s0880..s1045 bright line ~18 m right (55 % picked, rms 0.60 m, gaps bridged); onboard 1:43-1:52 concrete wall with catch fence on the right',
                 latlon=[
                (38.1621134, -122.4537615), (38.162081, -122.4536551), (38.1620705, -122.4536365),
                (38.161952, -122.4534516), (38.1618963, -122.4533595), (38.1618188, -122.4532991),
                (38.1617403, -122.4532436), (38.1616613, -122.4531909), (38.1615811, -122.453141),
                (38.1615002, -122.4530903), (38.1614173, -122.4530449), (38.1613475, -122.4530221),
                (38.1611374, -122.4529389), (38.1610518, -122.4529042), (38.1609663, -122.4528684),
                (38.1608779, -122.4528457), (38.1607915, -122.4528143), (38.1607144, -122.4527831),
                ]),
            # ---- round 4 (20 Oct 2026, owner drive notes 11, 13-18): barrier lines read on the 2026 captures as a
            # continuous dark tyre / wall band (or bright wall top) parallel to the track, measured with
            # compare/wall_measure.py on a guide, each confirmed on the March 2026 onboard (manifest: 'bright / dark bands')
            dict(name='T2 approach, far left: tyre line', kind='tyres', h=1.0, fence=0.0,
                 src='2026 captures c20_s2090 / c20_s2145: wall_measure dark line, 92 % picked, rms 0.27 m; Street View H9xspk4q_OoFIjVDhaMzDA (tyre / armco line far left); onboard 0:12 low dark barrier far left',
                 latlon=[(38.1615844, -122.4577948), (38.1615100, -122.4578627), (38.1614389, -122.4579328), (38.1613691, -122.4580008), (38.1612978, -122.4580688), (38.1612243, -122.4581356), (38.1611504, -122.4582001), (38.1610760, -122.4582644), (38.1610046, -122.4583342), (38.1609319, -122.4584037), (38.1609059, -122.4584364)]),
            dict(name='T2 exit, left: wall and catch fence at the foot of the T2 stands', kind='concrete', h=1.0, fence=3.0, color='#6f7a82',
                 src='2026 captures c20_s2145 / c20_s2200: wall_measure dark line, 97 % picked, rms 0.48 m; onboard 0:12-0:15.5 dark grey wall with catch-fence posts below the terraces',
                 latlon=[(38.1608628, -122.4584495), (38.1607944, -122.4585276), (38.1607720, -122.4586405), (38.1607615, -122.4587526), (38.1607583, -122.4588653), (38.1607634, -122.4589784), (38.1607724, -122.4590914), (38.1608055, -122.4591971), (38.1608410, -122.4593007), (38.1608838, -122.4593999), (38.1609205, -122.4595061), (38.1609742, -122.4595982), (38.1610319, -122.4596863), (38.1610953, -122.4597681), (38.1611587, -122.4598494), (38.1612262, -122.4599260), (38.1613073, -122.4599791), (38.1613792, -122.4600480), (38.1614253, -122.4600936)]),
            dict(name='T2 exit to T3, right: barrier line at the foot of the hill (owner_11)', kind='tyres', h=1.0, fence=0.0,
                 src='2026 captures c20_s2255 / c20_s2310: wall_measure dark line, 76 % picked, rms 0.41 m; owner_11 (the light band in the sim ground); onboard 0:12 dark barrier line far right, 0:18 barrier line along the right toward T3; joins the T3 tyre wall at s 600',
                 latlon=[(38.1613087, -122.4591967), (38.1613739, -122.4592754), (38.1614416, -122.4593507), (38.1615062, -122.4594303), (38.1615667, -122.4595146), (38.1616270, -122.4595999), (38.1616905, -122.4596811), (38.1617575, -122.4597574), (38.1618249, -122.4598330), (38.1618928, -122.4599079), (38.1619612, -122.4599821), (38.1619891, -122.4600113)]),
            dict(name='T5, right: wall before the T5-T6 wall', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='2026 captures c20_s2805 / c20_s2860: wall_measure dark line, 99 % picked, rms 0.51 m; onboard 0:39 the light concrete wall on the right already runs before T5 (continues the T5-T6 wall)',
                 latlon=[(38.1642349, -122.4628430), (38.1642667, -122.4627355), (38.1642887, -122.4626247), (38.1643083, -122.4625131), (38.1643267, -122.4624011), (38.1643439, -122.4622888), (38.1643607, -122.4621764), (38.1643769, -122.4620647), (38.1644014, -122.4619554), (38.1644056, -122.4618934)]),
            dict(name='T5, left: tyre wall', kind='tyres', h=1.0, fence=1.5, h_src='round 5: chain-link fence behind the tyre stacks, 2.5 m to its top (inventory 0:36 / 0:38, fence-post-ref)',
                 src='2026 captures c20_s2805 / c20_s2860: wall_measure dark line, 96 % picked, rms 0.49 m; Street View zCwjltSjI02eDZGZbVyrMg (left low dark wall, tyres); onboard 0:39 dark barrier far left',
                 latlon=[(38.1648083, -122.4628124), (38.1647511, -122.4627218), (38.1647308, -122.4626081), (38.1646947, -122.4625013), (38.1646847, -122.4623865), (38.1646845, -122.4622722), (38.1646828, -122.4621581), (38.1646788, -122.4620444), (38.1646778, -122.4619303), (38.1646730, -122.4618174), (38.1646717, -122.4618062)]),
            dict(name='T5 to the T6 crest, left: wall and catch fence beyond the paddock', kind='concrete', h=1.0, fence=3.0, color='#5d6266',
                 src='2026 captures c20_s2970 / c20_s3080: wall_measure dark line, 100 % picked, rms 0.18 m; onboard 0:39-0:44 long low dark wall with catch fence far left',
                 latlon=[(38.1646874, -122.4608403), (38.1646360, -122.4607461), (38.1645828, -122.4606548), (38.1645317, -122.4605628), (38.1644772, -122.4604752), (38.1644168, -122.4603947), (38.1643505, -122.4603208), (38.1642841, -122.4602453), (38.1642147, -122.4601730), (38.1641425, -122.4601049), (38.1640681, -122.4600410), (38.1639945, -122.4599754), (38.1639190, -122.4599135), (38.1638407, -122.4598570), (38.1637615, -122.4598068), (38.1636782, -122.4597633), (38.1635930, -122.4597251), (38.1635126, -122.4596930), (38.1634263, -122.4596605), (38.1633402, -122.4596260), (38.1632538, -122.4595914), (38.1631673, -122.4595589), (38.1630828, -122.4595193), (38.1630006, -122.4594703), (38.1629308, -122.4594152)]),
            dict(name='Carousel, right: tyre-faced barrier across the infield', kind='tyres', h=1.0, fence=0.0,
                 src='2026 captures c20_s3245 / c20_s3300: wall_measure dark line, 96 % picked, rms 0.32 m; Street View ma3jBYjtYGtNBlTLjNz1LQ (far right barrier, armco in Jul 2011); onboard 0:50 low dark barrier across the infield (2026: tyre-faced)',
                 latlon=[(38.1622039, -122.4588419), (38.1622255, -122.4587309), (38.1622553, -122.4586227), (38.1623030, -122.4585253), (38.1623564, -122.4584336), (38.1624127, -122.4583449), (38.1624782, -122.4582677), (38.1625456, -122.4581945), (38.1626151, -122.4581251), (38.1626880, -122.4580575), (38.1627618, -122.4579958), (38.1628388, -122.4579389), (38.1629189, -122.4578909), (38.1630010, -122.4578456), (38.1630843, -122.4578067), (38.1631693, -122.4577726), (38.1631736, -122.4577708)]),
            dict(name='Carousel, left: trackside fence', kind='fence', h=0.0, fence=2.0,
                 src='2026 captures c20_s3190 / c20_s3300: wall_measure dark line, 100 % picked, rms 1.12 m; Street View ma3jBYjtYGtNBlTLjNz1LQ (trackside fence far left); onboard 0:50 fence posts far left',
                 latlon=[(38.1628193, -122.4592713), (38.1627947, -122.4591583), (38.1627963, -122.4590400), (38.1628182, -122.4589248), (38.1628573, -122.4588192), (38.1629139, -122.4587269), (38.1629728, -122.4586395), (38.1630406, -122.4585575), (38.1631286, -122.4585162), (38.1632203, -122.4584975), (38.1632768, -122.4584977)]),
            dict(name='T8, left: tyre line up the bank (to the T8a-T9 tyres)', kind='tyres', h=1.0, fence=0.0,
                 src='2026 captures c20_s0000 / c20_s0055: wall_measure dark line, 99 % picked, rms 0.20 m; onboard 1:18.5 low dark line along the bank on the left; joins the T8a-T9 tyre wall',
                 latlon=[(38.1662930, -122.4607413), (38.1662218, -122.4606714), (38.1661547, -122.4605954), (38.1660895, -122.4605163), (38.1660270, -122.4604362), (38.1659724, -122.4603494), (38.1659225, -122.4602539), (38.1658914, -122.4601844)]),
            dict(name='T9, right: concrete wall along the 2020 bypass (part 1)', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='2026 captures c20_s0220 / c20_s0275: wall_measure bright line, 73 % picked, rms 0.38 m; onboard 1:27 light concrete wall on the right',
                 latlon=[(38.1649727, -122.4593844), (38.1649175, -122.4592939), (38.1648682, -122.4591981), (38.1648298, -122.4590942), (38.1647990, -122.4589867), (38.1647950, -122.4589764)]),
            dict(name='T9, right: concrete wall along the 2020 bypass (part 2)', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 src='2026 captures c20_s0220 / c20_s0275: wall_measure bright line, 73 % picked, rms 0.38 m; onboard 1:27 light concrete wall on the right',
                 latlon=[(38.1647501, -122.4588643), (38.1647131, -122.4587603), (38.1646824, -122.4586526), (38.1646386, -122.4585525), (38.1646043, -122.4584656)]),
            dict(name='T11 approach, right: tyre wall and catch fence at the edge', kind='tyres', h=1.0, fence=3.5,
                 src='2026 captures c20_s1045 / c20_s1100: wall_measure dark line, 97 % picked, rms 0.53 m; onboard 1:53-1:55 tyre stacks along the right edge with catch fence (an ambulance parked behind at 1:54.6)',
                 latlon=[(38.1609312, -122.4527310), (38.1608446, -122.4527009), (38.1607590, -122.4526659), (38.1606736, -122.4526305), (38.1605876, -122.4525984), (38.1604991, -122.4525756), (38.1604404, -122.4525457)]),
            dict(name='9a, right: tyre wall', kind='tyres', h=1.0, fence=0.0, cut='round 5: ends at s ~3132 where the dark tyre band ends on c20_s0715 / c20_s0770; the light concrete wall with its catch fence runs on from there (onboard 1:42-1:44)',
                 src='2026 captures c20_s0715 / c20_s0770: wall_measure dark line, 100 % picked, rms 0.53 m; onboard 1:42 tyre wall ahead right before the T10 wall',
                 latlon=[(38.1623750, -122.4551039), (38.1623515, -122.4549909), (38.1623267, -122.4548812), (38.1623041, -122.4547707), (38.1622884, -122.4547052)]),
            dict(name='T11 approach, left: outer pit-in wall (from the split)', kind='concrete', h=2.7, fence=0.0, color='#a9c9dd', h_src='round 5: the same tall wall as the garage-side part (HEIGHTS.md examples 3 and 4, 5.2 m to the board top; onboard 1:56 shows its doors and a marshal at one): 2.7 m concrete under 2.5 m boards; was 1.2 m',
                 src='2026 captures c20_s1100 / c20_s1155: wall_measure bright line, 100 % picked, rms 0.30 m; Street View owner_15 (wall with ad boards along the pit-in lane, ~1 m wall); onboard 1:59 light-blue wall with ad boards behind the pit-in Jersey',
                 latlon=[(38.1602279, -122.4522589), (38.1601428, -122.4522222), (38.1600546, -122.4521985), (38.1599666, -122.4521740), (38.1598813, -122.4521374), (38.1597964, -122.4520999), (38.1597112, -122.4520635), (38.1596261, -122.4520267), (38.1595623, -122.4519992)]),
            dict(name='T11 entry, left: Jersey wall between the track and the pit-in lane (from its nose)', kind='concrete', h=0.81, fence=0.0, color='#c9473e',
                 src='2026 captures c20_s1210 / c20_s1265: wall_measure bright line, 90 % picked, rms 0.15 m; owner_15 / owner_16 (wall between pit-in and track, nose with an impact barrier); onboard 1:59 red / white Jersey on the left; Jersey scale 0.81 m',
                 latlon=[(38.1593423, -122.4519695), (38.1592572, -122.4519328), (38.1591705, -122.4519022), (38.1590843, -122.4518703), (38.1589987, -122.4518373), (38.1589111, -122.4518114), (38.1588705, -122.4518113)]),
            dict(name='T11 hairpin, outside the pit road: outer wall (east)', kind='concrete', h=1.2, fence=0.0, color='#a9c9dd',
                 src='2026 captures c20_s1265 / c20_s1320: wall_measure bright line, 71 % picked, rms 0.65 m; owner_18 (tall concrete wall on the outside of the pit-in lane); Street View jrXpHaDfJT2APw6zcyBKRA',
                 latlon=[(38.1590349, -122.4517413), (38.1589451, -122.4517340), (38.1588574, -122.4517030), (38.1587676, -122.4516937), (38.1586770, -122.4517000), (38.1586275, -122.4517082)]),
            dict(name='T11 hairpin, outside the pit road: outer wall (south) (part 1)', kind='concrete', h=1.2, fence=0.0, color='#a9c9dd',
                 src='2026 captures c20_s1320: wall_measure dark line, 53 % picked, rms 0.51 m; owner_18 (tall concrete wall on the outside of the pit road behind the hairpin)',
                 latlon=[(38.1584146, -122.4517271), (38.1583969, -122.4518406), (38.1583891, -122.4518614)]),
            dict(name='T11 hairpin, outside the pit road: outer wall (south) (part 2)', kind='concrete', h=1.2, fence=0.0, color='#a9c9dd',
                 src='2026 captures c20_s1320: wall_measure dark line, 53 % picked, rms 0.51 m; owner_18 (tall concrete wall on the outside of the pit road behind the hairpin)',
                 latlon=[(38.1583472, -122.4520171), (38.1583292, -122.4521300), (38.1583196, -122.4522436), (38.1583277, -122.4523591), (38.1583333, -122.4524733), (38.1583327, -122.4525882), (38.1583217, -122.4527018), (38.1583222, -122.4527076)]),
            dict(name='T2 entry, left: tyre wall before the footbridge (owner_27 / owner_28)', kind='tyres', h=1.0, fence=0.0,
                 src='2026 captures c20_s1980 / c20_s2035: wall_measure dark line, 90 % picked, rms 0.74 m; owner_27 ("there is a tire wall missing here"); Street View owner_28 Pit Out (Jul 2011): tyre wall round the outside of T2 from before the footbridge; onboard 0:12 dark low barrier left',
                 latlon=[(38.1618462, -122.4575074), (38.1618430, -122.4576228), (38.1618430, -122.4577255)]),
            dict(name='T1 exit to T2, right: tyre line on the grass bank (owner_28) (part 1)', kind='tyres', h=1.0, fence=0.0,
                 src='2026 captures c20_s1925 / c20_s1980: wall_measure dark line, 84 % picked, rms 0.44 m; Street View owner_28 Pit Out (tyre line on the grass bank to the right)',
                 latlon=[(38.1624065, -122.4570844), (38.1623691, -122.4571903), (38.1623026, -122.4572695), (38.1622666, -122.4573742), (38.1622368, -122.4574815), (38.1622123, -122.4575920), (38.1621887, -122.4577016), (38.1621601, -122.4578097), (38.1621259, -122.4579154), (38.1621035, -122.4580230), (38.1620621, -122.4581284), (38.1620569, -122.4581378)]),
            dict(name='T1 exit to T2, right: tyre line on the grass bank (owner_28) (part 2)', kind='tyres', h=1.0, fence=0.0,
                 src='2026 captures c20_s1980 / c20_s2035: wall_measure dark line, 84 % picked, rms 0.44 m; Street View owner_28 Pit Out (tyre line on the grass bank to the right)',
                 latlon=[(38.1619844, -122.4582623), (38.1619265, -122.4583509), (38.1618636, -122.4584335), (38.1618208, -122.4584846)]),
            # ---- round 5 (21 Oct 2026): the coverage gate's MISSING rows (compare/sonoma/coverage.md), each measured with
            # compare/wall_measure.py on the named 2026 captures (or derived where said) and tied to its inventory rows
            dict(name='T4 approach, left: wall and catch fence on to the Chute (round 5)', kind='concrete', h=1.0, fence=2.5, color='#a9c9dd',
                 h_src='inventory 0:30-0:34: light grey concrete wall 1.0 m (jersey-ref) with catch fence 3.5 m to its top (fence-post-ref)',
                 src='c20_s2695 / c20_s2750: wall_measure bright, s 876-985 beyond the measured T4 approach wall, 56 % picked (three runs, gaps under 16 m bridged), rms 0.31 m; onboard 0:32 wall and fence abeam, 0:34 its end at the Chute; Street View nA1oaDXwADSI7x-Pa-j4Ow',
                 latlon=[(38.1629985, -122.4628819), (38.1630796, -122.4629321), (38.163157, -122.4629901), (38.1631686, -122.4629989),
                         (38.1632948, -122.4630979), (38.1633717, -122.463157), (38.1634476, -122.4632181), (38.1635225, -122.4632813),
                         (38.1635918, -122.4633451), (38.1636557, -122.4633982), (38.1637355, -122.463452), (38.1638102, -122.4635138),
                         (38.1638874, -122.4635702)]),
            dict(name='T6 crest, right: Jersey on to the Carousel paved area (round 5)', kind='concrete', h=0.9, fence=0.0, color='#c9c9c4',
                 h_src='inventory 0:46-0:50: light grey concrete Jersey segments 0.9 m (jersey-ref)',
                 src='c20_s3135 / c20_s3190: wall_measure bright 1.0 m beyond the right edge, s 1358-1460, 96 % picked, rms 0.05 m; onboard 0:48 Jersey abeam on the right, 0:50 its end where the paved area opens',
                 latlon=[(38.1634226, -122.4602245), (38.1633499, -122.4601568), (38.1632764, -122.4600909), (38.1632014, -122.460028),
                         (38.1631256, -122.4599668), (38.1630498, -122.4599057), (38.1629731, -122.4598463), (38.1628974, -122.4597854),
                         (38.1628231, -122.4597217), (38.1627516, -122.4596522), (38.162684, -122.459575), (38.162658, -122.4595345)]),
            dict(name='drag strip NW end: far wall beyond the fork (round 5)', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 h_src='inventory 1:06: light blue concrete wall 1.0 m (jersey-ref)',
                 src='c20_s3630 / c20_s3685 / c20_s3740: wall_measure bright along the drag strip NW end, three runs 54 % picked, rms 0.15 m (gaps of 32 and 69 m bridged: the onboard shows one continuous wall); onboard 1:04-1:06 light blue wall on the far side of the drag strip, right',
                 latlon=[(38.1649784, -122.4598073), (38.1650344, -122.4598966), (38.1650903, -122.4599843), (38.1651446, -122.4600733),
                         (38.1652006, -122.4601639), (38.1652486, -122.4602608), (38.1653888, -122.460571), (38.1654331, -122.4606709),
                         (38.1654834, -122.4607656), (38.1655392, -122.4608555), (38.1655951, -122.460946), (38.1656393, -122.4610241),
                         (38.165956, -122.4617028), (38.166008, -122.461796), (38.1660575, -122.4618781)]),
            dict(name='drag strip at the T7 fork: tyre line across the continuation (round 5)', kind='tyres', h=0.7, fence=0.0,
                 h_src='inventory 1:04: black tyre line 0.7 m (tyre-ref)',
                 src='onboard RAZip6S84CM 1:04: a black tyre line with cones across the drag strip continuation where the course forks left, ~40-60 m ahead; placed across the continuation at s ~1938 between the track edge and the measured far wall (c20_s3630; the 2026 captures, taken at another event, show the lanes open)',
                 latlon=[(38.1651955, -122.4603197), (38.1652344, -122.4603494), (38.1652741, -122.4603766)]),
            dict(name='T7 approach, left: wall on to the T7 post (round 5)', kind='concrete', h=1.2, fence=0.0, color='#a9c9dd',
                 h_src='as the T6 to T7 wall (onboard 1:09: ~1.2 m)',
                 src='c20_s3850 / c20_s3905: wall_measure bright, s 2104-2150, 63 % picked, rms 0.80 m (parked vehicles); onboard 1:12 the light blue-grey wall runs to its end beside the T7 post',
                 latlon=[(38.1657502, -122.4621356), (38.1657957, -122.4622344), (38.1658423, -122.4623324), (38.1658771, -122.4624379),
                         (38.1659144, -122.4625419), (38.1659438, -122.4626138)]),
            dict(name="the Chute's T7 mouth: tyre line behind the cones (round 5)", kind='tyres', h=0.6, fence=0.0,
                 h_src='inventory 1:12 (added row): low black tyre line, 0.6 m (tyre-ref)',
                 src='onboard RAZip6S84CM 1:12 (frame t072): two low black tyre lines with small orange cones across the paved Chute mouth ahead-left of T7, again far left at 1:14; placed 1.5 m behind the mouth cone line (the mouth from the OSM Chute way; c20_s3905 shows the mouth open at another event)',
                 latlon=[(38.1660984, -122.4628055), (38.1660851, -122.4627847), (38.1660717, -122.4627639), (38.1660584, -122.4627431),
                         (38.166045, -122.4627224), (38.1660317, -122.4627016)]),
            dict(name='T7, left: wall bounding the paved runoff below the T7a stands (round 5)', kind='concrete', h=1.0, fence=0.0, color='#e6e4de',
                 h_src='height not read (1.0 m default; the Street View row gives none)',
                 src='c20_s3960 / c20_s4015: wall_measure bright, 85 % picked, rms 0.57 m; Street View J6fsnW4hj4xCjQLzrgRGzA (concrete wall far left along the T7a stands)',
                 latlon=[(38.1668994, -122.4629129), (38.166845, -122.4628215), (38.1667931, -122.462728), (38.1667492, -122.4626282),
                         (38.1666955, -122.4625373), (38.1666442, -122.4624436), (38.1666416, -122.4624389)]),
            dict(name='T7a, left: tyre line at the foot of the terraces (round 5)', kind='tyres', h=0.8, fence=0.0,
                 h_src='inventory 1:14: black tyre wall line 0.8 m (tyre-ref)',
                 src='c20_s3960 / c20_s4015: wall_measure dark, 100 % picked, rms 0.39 m: the first 21 m of the line at the foot of the T7a terraces is a black tyre band (vehicles parked in front of it); onboard 1:14 black tyre wall line far left with recovery vehicles behind',
                 latlon=[(38.1668627, -122.4627568), (38.1668723, -122.4626432), (38.1668947, -122.4625312)]),
            dict(name='T7a, left: low wall at the foot of the terraces (round 5)', kind='concrete', h=0.8, fence=0.0, color='#e6e4de',
                 h_src='inventory 1:16: low white wall 0.8 m (jersey-ref)',
                 src='c20_s3960 / c20_s4015: wall_measure dark (its shadow line), 100 % picked, rms 0.39 m, the light part of the line at the foot of the T7a terraces; onboard 1:16 low white wall at the foot of the terraces',
                 latlon=[(38.1668947, -122.4625312), (38.1669342, -122.4624265),
                         (38.1669743, -122.4623242), (38.1670134, -122.4622213), (38.1670306, -122.4621747)]),
            dict(name='T7a to T8, left: tyre line at the foot of the bank (round 5)', kind='tyres', h=0.8, fence=0.0,
                 h_src='inventory 1:20: dark low wall 0.8 m (jersey-ref)',
                 src='c20_s0000 / c20_s4070: wall_measure dark, 100 % picked, rms 0.59 m, s 2292-2405 along the foot of the bank behind the paddock (joins the T8 tyre line); onboard 1:20-1:22 dark low wall / tyre line at the foot of the bank',
                 latlon=[(38.1670743, -122.4614152), (38.1670237, -122.4613205), (38.1669716, -122.4612278), (38.1668862, -122.4611955),
                         (38.1668026, -122.4611536), (38.1667216, -122.4611014), (38.1666454, -122.4610399), (38.1665686, -122.4609802),
                         (38.166491, -122.4609226), (38.166416, -122.4608597), (38.1663421, -122.4607947), (38.1662731, -122.4607214),
                         (38.1662385, -122.4606849)]),
            dict(name='T7a to T9, left: fence on the bank top (round 5)', kind='fence', h=0.0, fence=1.5,
                 h_src='inventory 1:18-1:26: fence on the bank top, 1.5 m (unmeasured: the rows give no reference; kept)',
                 src='onboard RAZip6S84CM 1:18-1:26 (fence posts along the top of the bank on the left) at the bank crest from the lidar bare-earth DEM (crest = first point past the steepest rise where the slope falls under 12 %, 47-60 m beyond the edge, 100 % of stations; median 9 + Gaussian 3); Street View xXQqyp9Q9sWv9ZLN2ORYsA (catch fence on the bank)',
                 latlon=[(38.1672231, -122.4613534), (38.1670028, -122.4611617), (38.1668328, -122.4610058), (38.1667088, -122.4608869), (38.1666337, -122.4608174), (38.1665966, -122.460782), (38.1665853, -122.4607685), (38.1665871, -122.4607675), (38.1665824, -122.4607651), (38.1665537, -122.4607406), (38.1665004, -122.4606829), (38.1664373, -122.4606015), (38.1663783, -122.4605174), (38.1663301, -122.460447), (38.1662958, -122.4603943), (38.1662737, -122.4603619), (38.16626, -122.4603436), (38.1662434, -122.4603199), (38.1662063, -122.460255), (38.1661479, -122.4601318), (38.1660835, -122.4599697), (38.1660186, -122.4597963), (38.165955, -122.4596276), (38.1658912, -122.459467), (38.1658173, -122.4593253), (38.1657354, -122.4592058), (38.1656584, -122.4591023), (38.1655966, -122.4590161), (38.1655565, -122.4589488), (38.165534, -122.4589024), (38.1655207, -122.4588693), (38.1655095, -122.458839), (38.165497, -122.4588058), (38.1654847, -122.458767), (38.1654757, -122.4587287), (38.1654704, -122.4586986), (38.1654659, -122.4586764), (38.1654614, -122.4586403)]),
            dict(name='T5, right: fence on the bank top (round 5)', kind='fence', h=0.0, fence=2.5,
                 h_src='inventory 0:38: chain-link fence with posts 2.5 m (fence-post-ref)',
                 src='onboard RAZip6S84CM 0:38-0:40 (fence along the top of the bank above the right wall) at the bank crest from the lidar bare-earth DEM (21-48 m beyond the edge; median 9 + Gaussian 3), s 1040-1200',
                 latlon=[(38.1639517, -122.4629725), (38.1639382, -122.4628885), (38.1638931, -122.4627569), (38.16396, -122.4626495), (38.1641443, -122.4625934), (38.1641771, -122.46249), (38.1641155, -122.4623559), (38.1640479, -122.4622213), (38.1640469, -122.4621012), (38.1640545, -122.4620059), (38.1640598, -122.4619276), (38.1640634, -122.4618657), (38.1640671, -122.4618101), (38.1640687, -122.4617495), (38.1640666, -122.4616797), (38.1640619, -122.461606), (38.1640494, -122.4615382)]),
            dict(name='T8 to 8a, right: concrete wall to the PWC road (round 5)', kind='concrete', h=1.0, fence=0.0, color='#a9c9dd',
                 h_src='inventory 1:20-1:22: light grey concrete wall 1.0 m (jersey-ref)',
                 src='c20_s0000 / c20_s0055 / c20_s0110: wall_measure bright, s 2350-2510, three runs 68-77 % picked, rms 0.78-0.84 m (gaps of 10 m bridged; trailers parked against it at another event); onboard 1:20-1:22 continuous light grey wall 6-10 m right',
                 latlon=[(38.1662731, -122.4616245), (38.1662058, -122.4615408), (38.1661216, -122.4614937), (38.1660785, -122.4614341),
                         (38.1660084, -122.4613532), (38.1659485, -122.4612678), (38.165895, -122.4611751), (38.1658408, -122.4610836),
                         (38.1657791, -122.4610011), (38.165718, -122.4609179), (38.1656743, -122.4608188), (38.1656356, -122.4607177),
                         (38.1655975, -122.460616), (38.1655579, -122.4605121), (38.1655429, -122.4603933), (38.1655415, -122.460275),
                         (38.1654993, -122.4601682), (38.1654862, -122.4601439)]),
            dict(name='T9 to the back straight, left: wall and catch fence (round 5)', kind='concrete', h=1.0, fence=2.5, color='#5d6266',
                 h_src='inventory 1:30: low dark concrete wall 0.9 m (jersey-ref), catch fence 3.5 m to its top (fence-post-ref)',
                 src='c20_s0330 / c20_s0385: wall_measure dark (the fence shadow band), s 2684-2785 between the T9 wall and the back-straight wall, 86 % picked, rms 0.79 m; onboard 1:30 continuous low wall with catch fence on the left',
                 latlon=[(38.1650646, -122.4583139), (38.1650565, -122.458199), (38.1650545, -122.4580861), (38.1650483, -122.4579719),
                         (38.1650184, -122.4578636), (38.1649777, -122.4577615), (38.1649274, -122.4576671), (38.1648753, -122.4575753),
                         (38.1648231, -122.4574842), (38.1647666, -122.4573975), (38.1647152, -122.4573029), (38.164654, -122.4572192),
                         (38.1646096, -122.4571626)]),
            dict(name='back straight to 9a, left: wall and catch fence (round 5)', kind='concrete', h=1.0, fence=2.5, color='#a9c9dd',
                 h_src='inventory 1:38-1:40: light concrete wall 1.0 m (jersey-ref), catch fence 3.5 m to its top (fence-post-ref)',
                 src='c20_o0660 / c20_s0660: wall_measure bright, s 2986-3046, 79 % picked, rms 0.58 m; onboard 1:38 wall and catch fence abeam on the left, 1:40 with Sonoma Raceway boards',
                 latlon=[(38.1635069, -122.455342), (38.1634471, -122.4552569), (38.1633834, -122.4551765), (38.1633219, -122.4550927),
                         (38.1632699, -122.4549987), (38.1631973, -122.454928), (38.1631105, -122.4548934), (38.1631062, -122.4548916),
                         (38.1630317, -122.4548843), (38.1629581, -122.4548937)]),
            dict(name='9a to T10, right: concrete wall and catch fence (round 5)', kind='concrete', h=1.1, fence=2.9, color='#a9c9dd',
                 h_src='inventory 1:44-1:48: light concrete wall 1.1 m (jersey-ref) with catch fence 4.0 m to its top (fence-post-ref)',
                 src='c20_s0715 / c20_s0770: wall_measure bright, s 3128-3222 (where the 9a tyre band ends to the T10-T11 right wall), 91 % picked, rms 0.44 m; onboard 1:44 light concrete wall with catch fence on the right',
                 latlon=[(38.1622887, -122.4547553), (38.1622686, -122.4546437), (38.1622507, -122.4545315), (38.1622352, -122.4544188),
                         (38.162217, -122.4543071), (38.1622103, -122.4541926), (38.162198, -122.4540795), (38.1621747, -122.4539676),
                         (38.162136, -122.4538626), (38.1621101, -122.4537527), (38.1621082, -122.4537475)]),
            dict(name='T10 entry, left: board wall along the bypass edge (round 5)', kind='concrete', h=1.0, fence=0.0, color='#5d6266',
                 h_src='inventory 1:44-1:46: 2.8-4.0 m to the board top (horizon-ratio): 1.0 m wall under 2.2 m boards (wall_boards)',
                 src='c20_s0715 / c20_s0770: wall_measure bright along the bypass edge, s 3118-3168, 63 % picked, rms 0.75 m (round 4 rejected a line here at 48 %; this guide follows the bypass edge, which the onboard confirms); onboard 1:44 a SONOMA RACEWAY / Sunbelt board wall 15-20 m left with a tyre stack in front, joining the T10-T11 boarded wall',
                 latlon=[(38.1627604, -122.454702), (38.162717, -122.4546005), (38.1626631, -122.4545065), (38.1626192, -122.454406),
                         (38.162607, -122.4542885), (38.1625989, -122.4542076)]),
            dict(name='T10 to T11, left: tyre bundles at the foot of the boarded wall (round 5)', kind='tyres', h=0.6, fence=0.0,
                 h_src='inventory 1:54: tyre bundles 0.6 m (tyre-ref)',
                 src='c20_s0990 / c20_s1045: wall_measure dark in front of the boarded wall, s 3395-3468, 99 % picked, rms 0.59 m; onboard 1:54 tyre bundles along the foot of the EchoPark wall',
                 latlon=[(38.1610051, -122.4525256), (38.1609177, -122.4524996), (38.1608296, -122.4524769), (38.1607425, -122.4524495),
                         (38.1606587, -122.452404), (38.1605724, -122.4523714), (38.1604839, -122.4523507), (38.1603952, -122.4523309),
                         (38.160373, -122.4523263)]),
            dict(name='drag strip infield side: catch fence near the line (round 5)', kind='fence', h=0.0, fence=3.0,
                 h_src='inventory 0:00 / 0:02 / 2:18: chain-link catch fence 3.0 m (fence-post-ref)',
                 src='onboard RAZip6S84CM 0:00, 0:02, 2:18 (chain-link catch fence on the far side of the drag strip, right) on the measured NE drag-strip wall (c20_s1595..s1760, the declared wall), s 4040-110',
                 latlon=[(38.1613921, -122.4540298), (38.1614481, -122.4541191), (38.1615038, -122.4542087), (38.1615595, -122.4542984), (38.1616154, -122.4543878), (38.1616712, -122.4544773), (38.1617269, -122.454567), (38.1617828, -122.4546564), (38.1618386, -122.454746), (38.1618943, -122.4548356), (38.1619503, -122.4549249), (38.1620061, -122.4550145), (38.1620621, -122.4551038), (38.1621177, -122.4551935), (38.1621737, -122.4552828), (38.1622295, -122.4553725), (38.1622851, -122.4554621), (38.162341, -122.4555516), (38.1623969, -122.4556411)]),
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
        # evidence-declared building overrides (20 Oct 2026, round 4): only where a newer source contradicts the 2022-24
        # lidar (precedence: recent onboard > 2026 satellite > NAIP > OSM > lidar); each use is logged by the build
        building_overrides=[
            dict(osm='1019838438', drop=True,
                 src='T11 approach, 1-6 m right of the right edge at s 3414-3440: the lidar (2022-24) has a ~12.5 m structure; '
                     'the 2026 capture c20_s1045 shows a temporary white hospitality tent (~8 x 30 m) on part of the outline; the '
                     'March 2026 onboard RAZip6S84CM 1:53-1:55.6 shows neither: tyre stacks and catch fence at the edge, an '
                     'ambulance and low cabins behind them, then open paved infield. The onboard is the newest source, so no '
                     'building stands here'),
        ],
        # OSM walls the evidence re-kinds or drops (round 5): OSM notes both T3 / T4 lines as 'tire barrier'
        osm_barrier_overrides={
            '380830042': dict(kind='tyres', h=1.0, fence=0.0, src='T3 right, OSM note "tire barrier": c20_s2475 / c20_s2530 show the dark tyre band on this line, 37-47 m right of the centre (round 5)'),
            '380830043': dict(drop=True, src='T4 right: the same tyre line as the measured declared wall "T4, right: tyre line beyond the runoff" (c20_s2640 / c20_s2695, within 1-2 m of it), OSM note "Tire barrier" (round 5)'),
        },
        # the evidence for the buildings the coverage gate checks (round 5): kept with their capture / onboard source, or
        # removed where neither the 2026 captures nor the onboard show them
        building_evidence=[
            dict(contains=(38.1617509, -122.456482), src='c20_s1870: the red-roofed metal pit-exit building (onboard 0:04 and 24of8fjjAug 5:00 red-roofed pit-exit building)'),
            dict(contains=(38.1603944, -122.4579624), src='onboard 0:14 (frame t014): open shade roof on posts at the top of the T2 terraces (inventory row added in round 5)'),
            dict(contains=(38.1673048, -122.45762), drop=True, src='OSM 3.2 m outline 273 m left of s 2698: outside the 2026 z20 captures and not in the onboard'),
            dict(contains=(38.1678842, -122.4631081), drop=True, src='OSM 4.3 m outline 151 m left of s 2256 (above the T7a hill): outside the 2026 z20 captures and not in the onboard'),
            dict(contains=(38.1599354, -122.4604477), drop=True, src='lidar blob (7.5 m, 91 m2) 164 m left of s 486, in the trees above the T2 terraces: outside the z20 captures; the onboard (0:14-0:18) shows trees there, no building'),
            dict(contains=(38.1600455, -122.4606619), drop=True, src='lidar blob (7.7 m, 242 m2) 165 m left of s 501, in the trees above the T2 terraces: outside the z20 captures; the onboard (0:14-0:18) shows trees there, no building'),
            dict(contains=(38.1603338, -122.4615908), drop=True, src='lidar blob (3.9 m) 196 m left of s 557: outside the z20 captures and not in the onboard'),
            dict(contains=(38.1602669, -122.4647859), drop=True, src='lidar blob (7.7 m) 346 m left of s 816: outside the z20 captures and not in the onboard'),
            dict(contains=(38.160589, -122.4647464), drop=True, src='lidar blob (7.7 m) 316 m left of s 819: outside the z20 captures and not in the onboard'),
            dict(contains=(38.160721, -122.4649418), drop=True, src='lidar blob (7.7 m) 317 m left of s 823: outside the z20 captures and not in the onboard'),
            dict(contains=(38.1608079, -122.4517355), drop=True, src='lidar blob (3.6 m, 49 m2) 73 m left of s 3438: c20_s1045 shows open road there (a vehicle in the 2022-24 survey)'),
            dict(contains=(38.1656768, -122.4631581), drop=True, src='lidar blob (6.6 m, 925 m2) 63 m left of s 2155: c20_s3850 / c20_s3905 show tree canopy there, no roof'),
        ],
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
            dict(name='T2 exit', latlon=(38.1607335, -122.4589865), h=3.0,
                 src='c20_s2200: a ~2 m white hut at the foot of the T2 terraces, 31 m left of the centre at s ~445 (round 5); onboard 0:12 white marshal hut ahead-left at the fence line'),
            dict(name='T7', latlon=(38.1659466, -122.4626554), h=4.0,
                 src='c20_s3905: a post at the end of the left wall at T7; onboard 1:11 raised white post with roof ahead'),
        ],
        # light masts (round 5, 21 Oct 2026): only those whose base and shadow the 2026 captures show (a thin shadow pointing
        # NW from the base, with the lamp frame's wider shadow at its end); heights not measurable on the captures (no
        # reference of known height in the same capture), so the stadium-mast default 20 m (build-track brief; HEIGHTS.md
        # cannot do better here) and 4 m for the light poles at the T2 terrace foot (inventory 0:14, fence-post-ref)
        light_masts=[
            dict(latlon=(38.1643089, -122.4582638), h=20.0, src='c20_s3465 / c20_s0330: mast base with its NW shadow between the drag strip and the infield (seen on both); onboard 1:00 light masts on the right'),
            dict(latlon=(38.1646502, -122.4589253), h=20.0, src='c20_s3465: mast base with its shadow beyond the drag strip, right of the Carousel exit; onboard 1:00-1:02 light masts on the right'),
            dict(latlon=(38.165015, -122.4596063), h=20.0, src='c20_s0165 / c20_s0220: mast base on a black block base in the island between the drag strip and the T8 road; onboard 1:18 light mast on a black block base'),
            dict(latlon=(38.1616939, -122.4539417), h=20.0, src='c20_s1650 / c20_s1705: mast base with its NW shadow in the paddock beyond the drag strip at the line; Street View 5MY4xR9O7etAXEHnZCVnGQ (light masts both sides of the straight)'),
            dict(latlon=(38.1607974, -122.4585026), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.1607508, -122.4587225), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.1607489, -122.4589554), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.160786, -122.4591811), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.1608642, -122.4593901), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.1609525, -122.4595898), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.1610718, -122.4597621), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.1612016, -122.4599209), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
            dict(latlon=(38.1613529, -122.460044), h=4.0, src='onboard 0:14-0:16 (light poles inside the fence line at the foot of the T2 terraces, ~4 m, fence-post-ref) along the measured T2-exit wall (c20_s2145 / c20_s2200), 1.5 m behind it every 20 m (pole spacing in the frames)'),
        ],
        # free-standing tyre stacks (round 5): the ones the onboard shows that the captures place
        tyre_stacks=[
            dict(latlon=(38.1632399, -122.4575474), h=0.84, src='c20_s3300 / c20_s3355: two dark stacks on the runoff right of the Carousel exit; onboard 0:56 single black tyre stacks on the runoff (0.8 m, tyre-ref)'),
            dict(latlon=(38.1631995, -122.4575097), h=0.84, src='c20_s3300 / c20_s3355: the second stack; onboard 0:56'),
            dict(latlon=(38.1629302, -122.4551972), h=0.42, color='#8a8d90', src='onboard 1:40: a stack of 2 grey tyres just past the 9a right apex kerb (kerb end s ~3045 on c20_o0660), 1.5 m outside the edge'),
            dict(latlon=(38.1625828, -122.4546884), h=0.63, src='onboard 1:44: a black tyre stack in front of the T10-entry board wall at its start (s ~3125; wall on c20_s0715 / c20_s0770)'),
        ],
        # advertising boards on the walls as plain coloured panels, no logos (20 Oct 2026, round 4; owner notes 13 / 15):
        # colours in the order the onboard shows them, track s from the onboard time (+-20 m), panel heights from the
        # Street View scale (owner_15: ~2.5 m boards on a ~1 m wall)
        wall_boards=[
            dict(wall='T10 to T11, left wall with the ad boards', s=(3172, 3235), h=2.5, colors=['#1d2a3a'],
                 src='onboard 1:43.2-1:44.5 dark navy board along the T10 entry wall'),
            dict(wall='T10 to T11, left wall with the ad boards', s=(3235, 3262), h=2.5, colors=['#3f9b3c'],
                 src='onboard 1:43.2-1:44.5 green boards after it'),
            dict(wall='T10 to T11, left wall with the ad boards', s=(3262, 3335), h=2.5, colors=['#ecebe6', '#ecebe6', '#b8202a'],
                 src='onboard 1:44.5-1:50 white boards with red ones between'),
            dict(wall='T10 to T11, left wall with the ad boards', s=(3335, 3400), h=2.5, colors=['#22262b'],
                 src='onboard 1:53-1:54 dark boards toward T11'),
            dict(wall='T11 approach, left: outer pit-in wall (from the split)', s=(3485, 3563), h=2.5,
                 colors=['#b8202a', '#1f3a2a', '#ecebe6', '#22262b'],
                 src='Street View owner_15 (red, dark green, white boards on the pit-in wall, Jul 2011); onboard 1:59 dark / white / red boards'),
            dict(wall='T11 entry, left: outer pit-in wall (garage side)', s=(3563, 3646), h=2.5,
                 colors=['#22262b', '#ecebe6', '#22262b', '#b8202a'],
                 src='onboard 1:59 dark, white, dark, red boards above the light-blue pit-in wall'),
            dict(wall='T6 to T7, left (Carousel exit along the drag strip and the T7 road)', s=(1990, 2105), h=2.0, base=1.6,
                 colors=['#ecebe6', '#d8467e', '#2a4fa8', '#b8202a'],
                 src='onboard 1:09-1:11 boards on posts above the light-blue wall (white, pink, blue, red)'),
            dict(wall='T10 entry, left: board wall along the bypass edge (round 5)', s=(3118, 3168), h=2.2,
                 colors=['#1d2a3a', '#1d2a3a', '#3f9b3c', '#ecebe6'],
                 src='onboard 1:44-1:46 (round 5): SONOMA RACEWAY (dark navy), Sunbelt (green) and Toyota (white) boards; 3.2 m to the top, between the 2.8 m read at 1:44 and the 4.0 m at 1:46 where they join the T10 wall (inventory, horizon-ratio)'),
            dict(wall='drag strip, infield (NE) side', s=(3925, 4098), h=1.5,
                 colors=['#22262b', '#3f9b3c', '#3f9b3c', '#b8202a', '#ecebe6'],
                 src='onboard 2:08-2:18 (round 5): Las Vegas (black), O\'Reilly and EchoPark (green), zMAX (red), Toyota (white) boards on the far drag-strip wall; 2.5 m to the top (inventory 2:08-2:12, horizon-ratio)'),
        ],
        # round 5 (21 Oct 2026): boards on the new T10-entry wall and on the far drag-strip wall at T12 / the front straight
        # the nose of the pit-in separation wall: a yellow water-filled impact barrier before the concrete (owner_15)
        impact_barriers=[
            dict(wall='T11 entry, left: Jersey wall between the track and the pit-in lane (from its nose)', end='start',
                 w=1.0, d=2.0, h=1.0, color='#e8c21c',
                 src='Street View owner_15 (Jul 2011): yellow impact barrier at the nose of the pit-in wall; nose position c20_s1210 (start of the measured wall)'),
        ],
        # the cone line along the double white line between the track and the pit-in lane, from where the lanes part
        # to the nose (owner_15: cones on the double line; c20_s1155 / c20_s1210: the solid double line from s ~3525)
        cone_lines_declared=[
            dict(side='right', s=(2196, 2212), off=0.5, spacing=5.0,
                 src='onboard 1:14-1:16 (round 5): orange delineator posts on the edge of the T7a island before its kerb (island on c20_s3960)'),
            dict(side='right', s=(1932, 1942), off=1.5, spacing=4.0,
                 src='onboard 1:04 (round 5): orange cones in front of the tyre line across the drag strip continuation at the T7 fork'),
            dict(side='left', s=(3525, 3586), off=0.4, spacing=4.0,
                 src='pit-in double white line, s 3525 to the nose at 3586 (c20_s1155 / c20_s1210; Street View owner_15 cones)'),
        ],
        # paved paddock behind the pit lane (owner_19: the NAIP ortho shows the parked trailers and cars as coloured
        # smears on the ground there): plain asphalt over the terrain, OSM amenity=parking outline
        paved_areas=[
            dict(osm='28825490', name='paddock behind the pit garages', surface='asphalt',
                 src='OSM 28825490 (amenity=parking); 2026 captures c20_s1485..s1650: dark asphalt with painted bays and parked trailers'),
        ],
        # paved roads of the circuit the Lemons loop does not use: driveable pavement, coned off at each mouth (owner,
        # 19 Oct 2026: "the Chute pavement is missing")
        # surface (round 4, owner notes 12 / 17: "usable track, just not in use"): the circuit's road material for the
        # asphalt ones, pale concrete where the 2026 captures show concrete (the drag strip lanes on c20_s1705 /
        # c20_s3880 strips; the T11a apron round the shortcut on c20_s1100 / c20_s1155, lighter than the track with
        # parking bays); paint=True: its painted edge lines from the captures (closed_road_paint in build_scenery.py)
        closed_roads=[
            # mouth_cones (round 5): cones only at the mouths the onboard shows coned; the rest are open in the 2026 evidence
            dict(name='2020 fast bypass (8a to T10)', ways=['834728156', '116036857'], half_width=6.0, surface='asphalt', paint=True,
                 mouth_cones=[]),
            dict(name='the Chute (NASCAR short course, T4 to T7)', ways=['834724050', '230287122'], half_width=6.0, surface='asphalt', paint=True,
                 mouth_cones=[dict(near=(38.1639925, -122.4635092), src='onboard 0:34: 3-5 orange cones across the Chute mouth ahead-left at T4 (inventory)'),
                              dict(near=(38.1660875, -122.4627527), src='onboard 1:12: small orange cones in front of a black tyre line across the Chute mouth at T7 (inventory, added row)')]),
            dict(name='drag strip', ways=['28825448'], half_width=9.0, max_half=12.0, surface='concrete', paint=True,
                 mouth_cones=[]),
            # the paved runoff INSIDE T7 (the triangle inside the hairpin, round the short-T7 way): cars may use it
            # (owner), so no cones; the racing line stays on the track (cutting through adds distance)
            dict(name='T7 inside runoff', ways=['1494191150'], half_width=10.0, max_half=14.0, cones=False, surface='asphalt'),
            dict(name='T11a shortcut', ways=['28825444'], half_width=6.0, surface='concrete', paint=True, mouth_cones=[]),
            dict(name='PWC lower hairpin', ways=['505454376'], half_width=5.0, surface='asphalt', paint=True, mouth_cones=[]),
        ],

        # a closed road's paving stops at its walls (the drag strip's NAIP width reached under the pit-straight wall)
        closed_roads_clip_walls=True,
        # the pit lane stops at the walls that bound it (round 4: the pit-in Jersey and outer wall; owner notes 15-16, 24)
        pit_lane_clip_walls=True,
        # bridges meet the banks: abutments and stair flights at both span ends (round 4, owner note 29)
        bridge_stairs=True,
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
                 why='Carousel exit: the course runs onto the drag strip; the drag strip toward the front straight is open pavement in the 2026 evidence (c20_s3410; no cones there in the onboard either, so round 5 removed the rule cone line) and a dead end, walled along the front straight and at T12 (onboard 2:12-2:18)'),
            dict(target='PWC lower hairpin', side='right', a=(38.1656123, -122.4615977), b=(38.1661994, -122.4613789),
                 why='inside T7 / 7a: paved runoff and the PWC hairpin are open pavement the cars may use (owner, 19 Oct; owner_9; Street View J6fsnW4hj4xCjQLzrgRGzA, gd1SNdksCq5QZtwlsrzR7g)'),
            dict(target='T11a shortcut', side='right', a=(38.1609734, -122.4526661), b=(38.1597720, -122.4522059),
                 why='T11 approach, right: the NASCAR infield is open paved ground to the 11a shortcut (Street View jrXpHaDfJT2APw6zcyBKRA: cones, tyre bundles at the 11a entry; onboard 1:56)'),
            dict(target='T11a shortcut', side='right', a=(38.1593620, -122.4527530), b=(38.1605086, -122.4532417),
                 why='T11 exit to T12, right: open paved NASCAR infield (onboard 2:06-2:11; c20_s1375..s1540)'),
        ]),
    ),
    # ---------------------------------------------------------------- pit lane (trackcfg.py pit_lane; 21 Oct 2026)
    # Only what the eye-level inventory gives (tools/track/compare/sonoma/inventory.md, pit-lane rows from the 2025 HPDE
    # video youtube.com/watch?v=24of8fjjAug and the 2026 onboard): stations abeam on the lap, sides as driven down the
    # lane. Round 5: each wall has geometry (latlon, measured on the captures) or names the declared scenery wall it is.
    pit_lane=dict(
        # one road material (round 5, owner notes 17, 24-26): the ortho's lighter pit-lane paving and paint smears are
        # mapped onto the track asphalt's tone inside the lane polygon (build_scenery.pit_tone_match)
        lane=dict(source='osm', match_track_tone=dict(k=0.5, paint=0.97)),
        # geometry (round 5): a wall with latlon is built here; one that is a declared scenery wall names it (declared=...)
        walls=[
            dict(side='left', s0=4000, s1=30, h=0.6, material='pitbox_wall', name='pit lane, left: low white pit-box wall (round 5)',
                 src='inventory pit rows s 4010 / 4060 / 20: low white pit-box wall with box numbers (24of8fjjAug 4:48-4:56); measured on c20_s1595 / c20_s1650 / c20_s1705: the bright double line between the boxes and the crew area, 27 m left of the centre, wall_measure 100 % picked, rms 0.03-0.07 m',
                 latlon=[(38.1607186, -122.4539335), (38.1607745, -122.454023), (38.1608304, -122.4541124), (38.1608862, -122.4542019),
                         (38.1609419, -122.4542916), (38.1609976, -122.4543812), (38.1610533, -122.4544708), (38.1611091, -122.4545604),
                         (38.1611648, -122.45465), (38.1612207, -122.4547395), (38.1612764, -122.4548291), (38.1613294, -122.4549142),
                         (38.161335, -122.4549232), (38.1613905, -122.455013), (38.1614464, -122.4551025), (38.1614997, -122.4551873)]),
            dict(side='right', s0=4000, s1=105, h=1.1, material='concrete', declared='pit straight, pit-lane side, to its nose at T1',
                 src='inventory pit rows s 4010 / 4060 / 20 / 100: white concrete pit wall with GEICO boards, Jersey nose curving with the track (24of8fjjAug 4:48-5:00); Street View 5MY4xR9O7etAXEHnZCVnGQ 1.08 m'),
            dict(side='left', s0=150, s1=170, h=1.1, fence=4.0, material='concrete', declared='pit-out lane, paddock side',
                 src='inventory pit row s 160: white wall with a catch fence along the pit-out lane (24of8fjjAug 5:04)'),
            dict(side='left', s0=3550, s1=3615, h=5.2, material='board_wall', declared='T11 entry, left: outer pit-in wall (garage side)',
                 src='inventory pit rows s 3560 / 3610: tall wall with doors and board panels, Jersey at its foot (24of8fjjAug 24:06-24:12; onboard RAZip6S84CM 1:56; Street View jrXpHaDfJT2APw6zcyBKRA 5.2 m)'),
            dict(side='right', s0=3600, s1=3620, h=0.9, material='jersey', declared='T11 entry, left: Jersey wall between the track and the pit-in lane (from its nose)',
                 src='inventory pit row s 3610: Jersey barrier between the pit-in lane and the track (24of8fjjAug 24:12); the separation starts at the water barriers at s ~3570'),
            dict(side='left', s0=3670, s1=3690, h=1.0, fence=4.0, material='concrete', declared='T11 hairpin, outside the pit road: outer wall (south) (part 2)',
                 src='inventory pit row s 3680: wall and catch fence, paddock buildings behind (24of8fjjAug 24:18)'),
            dict(side='right', s0=3670, s1=3690, h=1.1, fence=4.0, material='concrete', declared='T11 hairpin, left tyre wall',
                 src='inventory pit row s 3680: the T11 outside wall and catch fence seen from the lane (24of8fjjAug 24:18)'),
        ],
        furniture=[
            dict(kind='water_barrier', s=3570, side='right', src='inventory pit row s 3570: red / white water-filled barriers at the separation nose (24of8fjjAug 24:06; owner note 15)'),
            dict(kind='cone_line', s=3560, side='right', src='inventory pit row s 3560: yellow cones on the double white line (24of8fjjAug 24:06)'),
            dict(kind='cone_line', s=160, side='right', src='inventory pit row s 160: yellow cones on the double yellow blend line (24of8fjjAug 5:04)'),
            dict(kind='fuel', s=3730, side='right', src='inventory pit row s 3730: Sunoco fuel island, canopy and sign (24of8fjjAug 24:30; owner note 20)'),
        ],
    ),
    # ---------------------------------------------------------------- structures (build_structures.py; 21 Oct 2026)
    # The buildings round: the structure kit (src/app/structures.ts) declared from evidence; every source and method is
    # in compare/sonoma/manifest.md "Structures". Heights: lidar 2022-24 (DSM - DEM profiles across each outline) checked
    # against HEIGHTS.md storeys; colours from the 2026 onboard RAZip6S84CM and the 2025 pit-lane video 24of8fjjAug
    # (newer than Street View 2011/2017 where they differ). Plain colours only.
    structures=dict(
        # OSM boxes a structure replaces: the main grandstand block, the two pit-road garage rows, the T12 two-storey
        # building, the fuel canopy, the pit-exit building, the two paddock garages
        suppress_osm=['262082790', '1019835464', '1019837060', '1019836595', '1019838109', '1019836533',
                      '1019836718'],
        items=[
            dict(type='grandstand', name='Main grandstand',
                 # front face of the block-wall base, 145 m (the seat field fitted on c20_s1595..s1760: 141 x 31 m in
                 # plan, axis heading -38.8 deg; the suites roof spans 148 m in the lidar; OSM 262082790 is 144 m)
                 front=[(38.1614898, -122.455306), (38.1606742, -122.4540143)],
                 base=dict(h=2.2, depth=1.5, color='#a8a59c', walk='#b3b0a8', rail='#6d7176',
                           panels=dict(colors=['#f2f2ee', '#1f3f8f'], w=8.0, h=1.3, gap=12.0, z=0.5)),
                 rows=dict(n=31, depth=0.9, rise=0.307, z0=2.6, seat='#e0d6ae', riser='#a7a397', back=0.42),
                 aisles=dict(pitch=11.0, w=1.3, color='#b9b6ae'),
                 towers=dict(w=6.0, d0=18.0, depth=9.0, h=14.0, steel='#8a8f94', cap='#4a4f54'),
                 suites=dict(d0=30.0, d1=47.0, floor=14.0, glass=[15.2, 21.6], roof=[24.0, 26.2, 23.2, 0.53],
                             color='#8a8f93', glass_color='#4d5d6b', roof_color='#4a4f54', columns=10.0,
                             back=dict(depth=5.0, h=20.0), lights=dict(t=[12.0, 50.0, 95.0, 133.0], h=3.5)),
                 tower=dict(t0=20.5, t1=58.5, d0=30.0, d1=47.0, z0=24.0, h=29.8, color='#3f7a52', glass='#3b6f9a',
                            roof='#2f4a37'),
                 rear=dict(color='#b5ad9c'),
                 src='OSM 262082790 footprint; 2026 captures c20_s1595..s1760 (seat field, 13 aisle heads at 11 m); lidar '
                     '2022-24 profiles across the outline (seats 2.0 m at the front to 12.0 m at 29 m back, suites roof '
                     '24.0-26.2 m, rear 20 m, tower 29.5-30.1 m over t -52..-14 m); onboard RAZip6S84CM 2:15 (sand seats, '
                     'grey deck, green tower with blue glass); 2025 video 24of8fjjAug 4:48-4:56 (end stairs, deck lights); '
                     'Street View 5MY4xR9O7etAXEHnZCVnGQ, owner_22 (2017: block-wall base, panels, stair towers)',
                 h_src='lidar profiles (method: DSM - DEM across the outline every 2 m); storeys check: deck floor 14 m = '
                       'top seat row + 2 m, glass 2 storeys of 3.2 m'),
            # pit-road garage rows (T11 exit to T12, left of the pit lane): tan stucco, green metal roofs, red trim
            dict(type='garage', name='Pit garages north', osm='1019835464', eave=4.3, ridge=7.0,
                 wall='#d8c393', roof='#4c7a55', trim='#a8322b', trim_h=0.35,
                 windows=dict(side='track', pitch=2.6, w=1.2, h=1.0, z=2.4, color='#3a4654'),
                 doors=dict(side='away', pitch=5.2, w=3.6, h=3.0, color='#d6d4cf'),
                 src='OSM 1019835464; c20_s1430..s1485 (ridged roof, light masts on the paddock side); onboard '
                     'RAZip6S84CM 2:04-2:08 (tan stucco, green metal roofs, window row; inventory s 3699-3784); 2025 '
                     '24of8fjjAug 24:40 (roll-up door on the paddock side); Street View owner_20 (2011, red trim band)',
                 h_src='lidar: eaves 4.1-4.5 m, ridge 7.1 m along the outline\'s centre'),
            dict(type='garage', name='Pit garages south', osm='1019837060', eave=4.3, ridge=7.0,
                 wall='#d8c393', roof='#4c7a55', trim='#a8322b', trim_h=0.35,
                 windows=dict(side='track', pitch=2.6, w=1.2, h=1.0, z=2.4, color='#3a4654'),
                 doors=dict(side='away', pitch=5.2, w=3.6, h=3.0, color='#d6d4cf'),
                 src='OSM 1019837060; c20_s1375..s1430; onboard RAZip6S84CM 2:04-2:06 (tan stucco, green roofs); '
                     '2025 24of8fjjAug 24:30 (garages ahead at the fuel island)',
                 h_src='lidar: eaves 3.9-4.5 m, ridge 7.0 m'),
            dict(type='garage', name='Paddock garage west', osm='1019836533', eave=5.0, ridge=7.8,
                 wall='#d8c393', roof='#4c7a55', trim='#a8322b', trim_h=0.35,
                 doors=dict(side=0, pitch=5.2, w=3.6, h=3.2, color='#d6d4cf'),
                 src='OSM 1019836533; NAIP ortho (green roof); 2025 24of8fjjAug 24:40 (tan garages, grey-green roofs, '
                     'paddock); inventory s 3699 left (tan stucco garages with green metal roofs, paddock)',
                 h_src='lidar: eaves 5.0-5.2 m, ridge 7.8 m'),
            dict(type='garage', name='Paddock garage south', osm='1019836718', eave=5.0, ridge=7.7,
                 wall='#d8c393', roof='#4c7a55', trim='#a8322b', trim_h=0.35,
                 doors=dict(side=0, pitch=5.2, w=3.6, h=3.2, color='#d6d4cf'),
                 src='OSM 1019836718; NAIP ortho (green roof); 2025 24of8fjjAug 24:30 (tan building, hip roof, beside '
                     'the fuel island); inventory s 3699-3736 left',
                 h_src='lidar: eaves 4.8-5.6 m, ridge 7.7 m'),
            # pit-exit building (the "Farmers" end): grey metal walls, low mono-pitch roof rising to the glazed track side,
            # red roof edge
            dict(type='garage', name='Pit-exit building', osm='1019839174', eave=4.2, ridge=8.2, mono='track',
                 wall='#9a9d9f', roof='#8e9396', trim='#b23a2e', trim_h=0.45,
                 windows=dict(side='track', pitch=3.0, w=2.8, h=2.2, z=4.6, color='#3b6f9a'),
                 src='OSM 1019839174; c20_s1870 (ribbed grey roof with a red edge, red round canopy beside); onboard '
                     'RAZip6S84CM 0:04 (red roof edge, glazed front, grey walls; inventory s 91 left); 2025 24of8fjjAug '
                     '4:56 (red roof line at the pit exit); Street View owner_25 (2011)',
                 h_src='lidar: roof from 4.2 m (paddock side) to 8.2 m (track side)'),
            # T12: the two-storey flat-roof building at the pit-road end of the grandstand
            dict(type='block', name='T12 two-storey building', osm='1019836595', h=7.9, storeys=2, parapet=0.5,
                 wall='#d4c49c', band='#34495a', roof='#a3a39e',
                 src='OSM 1019836595; c20_s1540 (flat roof); Street View QduY6QTXmw4JDevQVE_b-g (two-storey suites and '
                     'control buildings at T12); onboard RAZip6S84CM 2:12 (tan multi-storey glazed building)',
                 h_src='storeys 2 x 3.2 m + parapet (HEIGHTS.md example 8); lidar flat 8.3-8.9 m'),
            dict(type='fuel', name='Fuel island', osm='1019838109', h=4.8, fascia=0.9, hip=1.2, hip_color='#7d8a7e',
                 canopy='#ece9df', fascia_color='#ece9df', posts=3, islands=2,
                 pylon_at=(38.1585228, -122.4528985),
                 pylon=dict(h=9.0, w=2.6, color='#1f3f7a', panel='#e5b622'),
                 src='OSM 1019838109; 2025 24of8fjjAug 24:30 (cream canopy, grey-green hip roof, tall plain-panel sign '
                     'pylon beside the light mast; inventory pit row s 3730); onboard RAZip6S84CM 2:04 (canopy left); '
                     'owner_20 (2011)',
                 h_src='lidar: canopy edges 5.6-6.0 m, hip top 6.9 m; pylon 9 m against the 21 m mast beside it (24:30)'),
            # light masts: isolated lidar spikes (DSM - DEM over 15 m, local maximum, ring median low), each confirmed
            # on the 2026 captures (lamp head displaced along the view, long shadow to the north-west); h = spike - 0.7 m
            # (the lamp head's top above the kit's mast height)
            dict(type='mast', name='Light masts', heads=[3, 2], at=[(38.1614918, -122.4554235, 21.1), (38.1617882, -122.4559034, 20.9), (38.161905, -122.4565317, 24.0),
                (38.1628842, -122.4572515, 20.8), (38.164016, -122.4576171, 21.2), (38.1643574, -122.4582798, 21.2),
                (38.1670254, -122.4630898, 20.5), (38.1668727, -122.4626899, 20.8), (38.1673488, -122.4636039, 20.7),
                (38.1662349, -122.4617988, 20.9), (38.1657588, -122.460999, 21.0), (38.1654533, -122.4602335, 20.4),
                (38.1650491, -122.4596051, 18.2), (38.1647077, -122.4589425, 20.9), (38.1635579, -122.4571601, 21.4),
                (38.1631806, -122.4566688, 21.0), (38.1628572, -122.4561547, 21.1), (38.1625428, -122.4556292, 20.9),
                (38.1622823, -122.4550465, 23.9), (38.1620757, -122.4544638, 27.3), (38.1617613, -122.4539611, 27.4),
                (38.1614558, -122.4534584, 27.3), (38.1611504, -122.4529785, 27.0), (38.160297, -122.4522702, 24.2),
                (38.1584914, -122.4528757, 21.0), (38.1589226, -122.4531499, 21.0), (38.1593628, -122.4533213, 21.1),
                (38.159776, -122.4534926, 21.1)],
                 src='lidar 2022-24 spikes; captures c20_s1760 c20_s1815 c20_s1870 c20_s3355 c20_o0440 c20_s3520 '
                     'c20_s4015 c20_s0000 c20_s0055 c20_s0110 c20_s0220 c20_s0275 c20_s0550 c20_s0605 c20_s0660 '
                     'c20_s0715 c20_s0770 c20_s0880 c20_s0935 c20_s0990 c20_s1100 c20_s1320 c20_s1375 c20_s1430 '
                     'c20_s1485 (lamp heads and shadows); T7a hill top (two outside the captures): Street View '
                     'J6fsnW4hj4xCjQLzrgRGzA (light masts on top); inventory mast rows',
                 h_src='lidar spike height'),
            # pit wall boards: plain panels along the pit wall's top (no logos)
            dict(type='boards', name='Pit wall boards (blue)', side='left', s0=3960, s1=4060, lat=(4.0, 15.0), h=0.85,
                 colors=['#23439a'], panel=3.0,
                 src='2025 24of8fjjAug 4:48 (blue board band along the pit wall top, RESTART ZONE panel; inventory pit '
                     'row s 4010)', h_src='about 0.8 of the 1.1 m wall below it (24of8fjjAug 4:48)'),
            dict(type='boards', name='Pit wall boards (green)', side='left', s0=4060, s1=4098, lat=(4.0, 15.0), h=0.85,
                 colors=['#3aa635'], panel=3.0,
                 src='onboard RAZip6S84CM 2:15 (green panels on the pit wall at the line, both sides)',
                 h_src='about 0.8 of the wall (onboard 2:15)'),
            # pit-box lines: the box front line along the lane and a cross line every box, measured on a straightened
            # strip of the 2026 captures along the pit lane (peaks of the white-line brightness; front line 6.6 m and
            # the box wall 11.5 m off the lane centre)
            dict(type='paint', name='Pit boxes', color='#eeeeea', runs=[
                dict(a=(38.1592388, -122.4529714), b=(38.1598501, -122.4532217), pitch=8.95, depth=4.8, w=0.12),
                dict(a=(38.1607036, -122.4538208), b=(38.161346, -122.4548485), pitch=8.84, depth=4.8, w=0.12),
                dict(a=(38.1614318, -122.4549866), b=(38.1618282, -122.455619), pitch=8.85, depth=4.8, w=0.12)],
                 src='captures c20_s1430..s1485 and c20_s1595..s1760 (box lines; runs along the lane 317-388, 504-619 and '
                     '634-705 m from the pit-in, the gap at 619-634 m is the start-line crossing); 2025 24of8fjjAug 4:48'),
            # hillside terraces: the existing rows (terraces rule) dressed with bench strips, stair aisles with hand rails
            # and the shade roofs the onboard shows on top
            dict(type='terrace_dress', terrace='above T2', bench=dict(color='#b3ada1', h=0.4, depth=0.4),
                 aisles=dict(pitch=45.0, w=1.4, color='#c4c1b8', rail='#8c9196'),
                 shades=[dict(f0=0.0, f1=0.12, rows=6, h=2.8, color='#5b5f63')],
                 src='onboard RAZip6S84CM 0:14-0:16 (concrete terraces, stair aisles with hand rails, a dark shade roof on '
                     'top at the far end); Street View H9xspk4q_OoFIjVDhaMzDA'),
            dict(type='terrace_dress', terrace='T3a-T4', bench=dict(color='#b9b5ab', h=0.4, depth=0.4),
                 aisles=dict(pitch=40.0, w=1.4, color='#cfccc4', rail='#8c9196'),
                 src='onboard RAZip6S84CM 0:26-0:30 (light concrete terraces, ~20 rows); Street View nA1oaDXwADSI7x-Pa-j4Ow'),
            dict(type='terrace_dress', terrace='T7a hill', bench=dict(color='#b49f78', h=0.4, depth=0.4),
                 aisles=dict(pitch=40.0, w=1.4, color='#c9b892', rail='#8c9196'),
                 src='onboard RAZip6S84CM 1:12-1:14 (tan terraces, fence and light masts on top); Street View '
                     'J6fsnW4hj4xCjQLzrgRGzA (owner_8: stepped rows with stair aisles)'),
            dict(type='terrace_dress', terrace='back straight / 9a', bench=dict(color='#a39d91', h=0.4, depth=0.4),
                 aisles=dict(pitch=40.0, w=1.4, color='#c4c1b8', rail='#8c9196'),
                 shades=[dict(f0=0.55, f1=0.62, rows=5, h=2.8, color='#5b5f63'), dict(f0=0.7, f1=0.78, rows=5, h=2.8, color='#5b5f63')],
                 src='onboard RAZip6S84CM 1:30-1:34 (concrete terraces with shade roofs / covered stands on top); Street '
                     'View xkSrqJ5RaN9WFLncaiqaug; captures c20_o0495..o0550 (dark roofs at the top edge)'),
        ]),
    # ---------------------------------------------------------------- app registry (src/scoreboard/config.ts)
    app=dict(short='Sonoma', pace='cars/field/sonoma/pace.json'),
)
