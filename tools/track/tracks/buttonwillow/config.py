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
        prior_shift=[
        dict(knots=[(35.4893901, -119.5410498, 0), (35.4894769, -119.5410212, 2.5), (35.4895652, -119.5410012, 5.0), (35.4896543, -119.540987, 6.0), (35.4897438, -119.5409781, 7.5), (35.4898336, -119.5409745, 8.5), (35.4899234, -119.5409765, 9.5), (35.490013, -119.5409837, 10.5), (35.4901023, -119.5409954, 11.0), (35.4901912, -119.5410112, 11.0), (35.4902795, -119.5410313, 10.0), (35.4903673, -119.5410549, 8.5), (35.4904547, -119.5410801, 7.8), (35.4905419, -119.5411067, 7.5), (35.4906282, -119.5411372, 6.5), (35.4907138, -119.5411707, 6.0), (35.4907997, -119.5412029, 4.5), (35.4909712, -119.5412684, 4.0), (35.4911326, -119.5413641, 3.0), (35.4912799, -119.5414904, 1.5), (35.4914422, -119.5415832, 0)],
             blend=0, src='T1 exit s 340-580: the pale surface west of the block line (ruler_t1 / ruler_t1b on c20_s0450-c20_s0700; onboard t016-t022 blocks on the right)'),
        dict(knots=[(35.4949012, -119.5478938, 0), (35.4948119, -119.5479049, -1.3), (35.4947229, -119.5479203, -2.0), (35.4946339, -119.5479353, -3.0), (35.4945443, -119.5479422, -5.8), (35.4944548, -119.5479345, -8.3), (35.4943662, -119.5479161, -10.6), (35.494277, -119.5479037, -10.9), (35.4941874, -119.547909, -8.8), (35.4940992, -119.5479297, -5.3), (35.4940121, -119.5479567, -1.8), (35.493925, -119.5479835, 0)],
             blend=0, src='T10 s 3670-3780: the pale surface west of the block line (ruler_t10 on c20_s3800 / c20_s3850; onboard t122-t126 blocks on the left)'),
        dict(knots=[(35.488704, -119.5478922, 0), (35.4886483, -119.5478058, 2.0), (35.4886036, -119.5477102, 4.5), (35.4885706, -119.5476077, 6.6), (35.4885481, -119.547501, 8.0), (35.4885335, -119.5473921, 9.8), (35.4885234, -119.5472825, 11.2), (35.4885162, -119.5471725, 12.1), (35.4885114, -119.5470624, 13.1), (35.4885093, -119.5469521, 13.8), (35.4885103, -119.5468418, 14.3), (35.488514, -119.5467315, 14.4), (35.4885207, -119.5466215, 13.0), (35.488532, -119.5465121, 12.0), (35.4885482, -119.5464036, 11.0), (35.4885739, -119.5461854, 10.8), (35.4885768, -119.5459648, 11.7), (35.4885954, -119.5457455, 11.1), (35.4886266, -119.5455282, 9.2), (35.4886596, -119.5453113, 7.0), (35.4886837, -119.5450928, 5.8), (35.4886868, -119.5448722, 3.0), (35.4886971, -119.544652, 0)],
             blend=0, src='T11 exit and the front straight s 4380-4680: the pale surface north of the block line to the pit-wall median (ruler_t11 on c20_s4500-c20_s4600; onboard t142-t148 blocks on the right); past s 4500 the shift follows where the fitted front-straight centre already lay (run 20)'),
    ]),
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
                kerb_search=[
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
                      ('right', 468, 498, 'c20_s0650: corner station mound beside the right edge at s ~475-492')]),
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
        ('left', 1198, 1218, 'kerb_band', 'kerb_detect run s 1205-1217 off -0.1..+0.3 m (c20_s1300, c20_s1350)'),
        ('left', 1241, 1274, 'kerb_band', 'kerb_detect run s 1248-1273 off -0.5..+0.3 m (c20_s1350, c20_s1400)'),
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
        dict(side='left', fit='asphalt_end', lo=4525, hi=180, join=(4525, 4535), end=180, tol=0.25,
             detector=dict(jump=8.0, sat_max=40.0, lo=-1.2, hi=2.0),
             why='front straight left: straight asphalt end at the pit-wall median (c20_s4600-c20_s0250)'),
        dict(side='right', fit='asphalt_end', lo=4525, hi=180, join=(4525, 4535), end=180, tol=0.25,
             detector=dict(jump=8.0, sat_max=40.0, lo=-1.2, hi=2.0),
             why='front straight right: straight asphalt-to-dirt edge between the crossovers (c20_s4600-c20_s0250)'),
    ],
    repave_fixes=[],                             # only where recent footage contradicts the survey (SKILL 1.6)
    gate=dict(exempt=[
        ('right', 1370, 1435, "mirror of the left exemption 1380-1430: as the left edge steps out to the T4-T5 apron at the block line's end (s 1387, stage3_evidence/cw_1348.png on c20_s1450 / c20_s1500) the centre and its normals swing, so the right half-width changes 0.17 m per station with no feature on the right edge; the world-continuity gate on the right edge polyline is the physical check and passes; junction, real"),
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
        brake_board_corners=[],                  # none in the onboard (t000-t158): no 3-2-1 boards before any corner
        corner_boards=False,                     # no turn-number boards in the onboard
        flagstand=False,                         # the starter's stand is placed as a station (marshal_posts), not by rule
        pit_wall=dict(rule=False),
        # kerbs: flat painted concrete beyond the asphalt edge, blocks of red / white / blue / white (onboard t014, t018,
        # t044, t116: blue, white, red, white, ~1.0 m each; the block pair period on the captures 1.82-2.27 m,
        # compare round 3), the band ~0.9 m across (kerb_detect offsets); no raised profile (the onboard shows the car
        # riding over them flat; no face at the asphalt joint on t014); no green after-kerb paint
        kerb=dict(width=0.9, stripe_m=1.0, colors=['#b8433a', '#dedbd2'],
                  palettes={'rwb': ['#c4463b', '#e2dfd6', '#4a7ccc'], 'wb': ['#4a7ccc', '#e2dfd6']}, require_colour_src=True),
        # kerb strips in pieces of <= 10 m with each piece's own offset (regenerated on the round-3 geometry, run 32, judge r2 false detections dropped; 
        # kerb_detect's band reading over -10..+1.5 m from the edge, -16 m at the T1 exit; block lines 1-16 m inside an edge
        # kept only where an onboard kerb row of that side lies within 40 m)
        kerbs_declared=[
            dict(side='left', a=(35.4890464, -119.541446), b=(35.4890842, -119.5413744), colors='rwb', off=-0.53, name='left s 284-293',
                 colour_src='t014.jpg (red / white / blue; inventory row s 300 left)',
                 src='extent pass (judge r3) on c20_s0400: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 284-323, was 281-320)'),
            dict(side='left', a=(35.4890892, -119.541367), b=(35.4891404, -119.5413054), colors='rwb', off=-0.45, name='left s 294-303',
                 colour_src='t014.jpg (red / white / blue; inventory row s 300 left)',
                 src='extent pass (judge r3) on c20_s0400: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 284-323, was 281-320)'),
            dict(side='left', a=(35.4891467, -119.5412991), b=(35.4892069, -119.5412461), colors='rwb', off=-0.45, name='left s 304-313',
                 colour_src='t014.jpg (red / white / blue; inventory row s 300 left)',
                 src='extent pass (judge r3) on c20_s0450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 284-323, was 281-320)'),
            dict(side='left', a=(35.4892139, -119.5412407), b=(35.4892794, -119.5411962), colors='rwb', off=-0.49, name='left s 314-323',
                 colour_src='t014.jpg (red / white / blue; inventory row s 300 left)',
                 src='extent pass (judge r3) on c20_s0450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 284-323, was 281-320)'),
            dict(side='left', a=(35.491096, -119.5414338), b=(35.4911595, -119.5414855), colors='rwb', off=-0.53, name='left s 535-544',
                 colour_src='t022.jpg (red / white / blue; inventory row s 531 left)',
                 src='extent pass (judge r3) on c20_s0650: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 535-545, was 534-556)'),
            dict(side='left', a=(35.4912083, -119.5403517), b=(35.491132, -119.5403162), colors='rwb', off=0.37, name='left s 738-747',
                 colour_src='t032.jpg (white / red; inventory row s 738 left)',
                 src='extent pass (judge r3) on c20_s0850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 738-763, was 732-763)'),
            dict(side='left', a=(35.4911236, -119.5403123), b=(35.4910486, -119.5402773), colors='rwb', off=-0.25, name='left s 748-757',
                 colour_src='t032.jpg (white / red; inventory row s 738 left)',
                 src='extent pass (judge r3) on c20_s0900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 738-763, was 732-763)'),
            dict(side='left', a=(35.4910403, -119.5402734), b=(35.4909987, -119.5402536), colors='rwb', off=-0.61, name='left s 758-763',
                 colour_src='t032.jpg (white / red; inventory row s 738 left)',
                 src='extent pass (judge r3) on c20_s0900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 738-763, was 732-763)'),
            dict(side='left', a=(35.4894735, -119.5394843), b=(35.4893982, -119.5394473), colors=['#b8433a', '#dedbd2'], off=-0.73, name='left s 947-956',
                 colour_src='t038.jpg (white / red; inventory row s 972 left)',
                 src='extent pass (judge r3) on c20_s1100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 947-1008, was 944-1004)'),
            dict(side='left', a=(35.4893899, -119.5394432), b=(35.4893152, -119.539406), colors=['#b8433a', '#dedbd2'], off=-0.43, name='left s 957-966',
                 colour_src='t038.jpg (white / red; inventory row s 972 left)',
                 src='extent pass (judge r3) on c20_s1100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 947-1008, was 944-1004)'),
            dict(side='left', a=(35.4893069, -119.5394019), b=(35.4892326, -119.5393645), colors=['#b8433a', '#dedbd2'], off=-0.41, name='left s 967-976',
                 colour_src='t038.jpg (white / red; inventory row s 972 left)',
                 src='extent pass (judge r3) on c20_s1100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 947-1008, was 944-1004)'),
            dict(side='left', a=(35.4892244, -119.5393604), b=(35.4891502, -119.5393221), colors=['#b8433a', '#dedbd2'], off=-0.49, name='left s 977-986',
                 colour_src='t038.jpg (white / red; inventory row s 972 left)',
                 src='extent pass (judge r3) on c20_s1100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 947-1008, was 944-1004)'),
            dict(side='left', a=(35.4891419, -119.5393178), b=(35.4890665, -119.5392786), colors=['#b8433a', '#dedbd2'], off=-0.51, name='left s 987-996',
                 colour_src='t040.jpg (red / white / blue; inventory row s 996 left)',
                 src='extent pass (judge r3) on c20_s1100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 947-1008, was 944-1004)'),
            dict(side='left', a=(35.489058, -119.5392743), b=(35.4889782, -119.5392376), colors=['#b8433a', '#dedbd2'], off=-0.41, name='left s 997-1006',
                 colour_src='t040.jpg (red / white / blue; inventory row s 996 left)',
                 src='extent pass (judge r3) on c20_s1150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 947-1008, was 944-1004)'),
            dict(side='left', a=(35.4883134, -119.5395725), b=(35.4882607, -119.5395998), colors='rwb', off=-0.33, name='left s 1086-1093',
                 colour_src='t044.jpg (red / white / blue; inventory row s 1088 left)',
                 src='extent pass (judge r3) on c20_s1200: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1086-1093, was 1083-1092)'),
            dict(side='left', a=(35.4881506, -119.5396201), b=(35.4880961, -119.5396116), colors='rwb', off=0.23, name='left s 1107-1114',
                 colour_src='t044.jpg (red / white / blue; inventory row s 1088 left)',
                 src='extent pass (judge r3) on c20_s1250: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1107-1114, was 1105-1114)'),
            dict(side='left', a=(35.4873658, -119.5393703), b=(35.4872902, -119.5394169), colors='rwb', off=-0.25, name='left s 1200-1209',
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='extent pass (judge r3) on c20_s1350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1200-1211, was 1199-1208)'),
            dict(side='left', a=(35.4871299, -119.539527), b=(35.4870581, -119.5395742), colors='rwb', off=0.11, name='left s 1229-1238',
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='extent pass (judge r3) on c20_s1350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1229-1269, was 1221-1266)'),
            dict(side='left', a=(35.4870501, -119.5395793), b=(35.4869783, -119.5396238), colors='rwb', off=-0.01, name='left s 1239-1248',
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='extent pass (judge r3) on c20_s1350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1229-1269, was 1221-1266)'),
            dict(side='left', a=(35.4869703, -119.5396286), b=(35.4868982, -119.539672), colors='rwb', off=-0.21, name='left s 1249-1258',
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='extent pass (judge r3) on c20_s1400: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1229-1269, was 1221-1266)'),
            dict(side='left', a=(35.4868901, -119.5396769), b=(35.4868168, -119.5397236), colors='rwb', off=-0.53, name='left s 1259-1268',
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='extent pass (judge r3) on c20_s1400: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1229-1269, was 1221-1266)'),
            dict(side='left', a=(35.4865464, -119.5403864), b=(35.4865519, -119.5404876), colors='rwb', off=-0.45, name='left s 1334-1343',
                 colour_src='t054.jpg (red / white / blue; inventory row s 1344 left)',
                 src='extent pass (judge r3) on c20_s1450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1334-1394, was 1331-1394)'),
            dict(side='left', a=(35.4865525, -119.5404988), b=(35.4865572, -119.5405991), colors='rwb', off=-0.45, name='left s 1344-1353',
                 colour_src='t054.jpg (red / white / blue; inventory row s 1344 left)',
                 src='extent pass (judge r3) on c20_s1450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1334-1394, was 1331-1394)'),
            dict(side='left', a=(35.4865577, -119.5406102), b=(35.4865611, -119.5407105), colors='rwb', off=-0.49, name='left s 1354-1363',
                 colour_src='t054.jpg (red / white / blue; inventory row s 1344 left)',
                 src='extent pass (judge r3) on c20_s1500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1334-1394, was 1331-1394)'),
            dict(side='left', a=(35.4865614, -119.5407217), b=(35.4865644, -119.5408218), colors='rwb', off=-0.45, name='left s 1364-1373',
                 colour_src='t054.jpg (red / white / blue; inventory row s 1344 left)',
                 src='extent pass (judge r3) on c20_s1500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1334-1394, was 1331-1394)'),
            dict(side='left', a=(35.4865647, -119.5408329), b=(35.4865685, -119.540932), colors='rwb', off=-0.41, name='left s 1374-1383',
                 colour_src='t054.jpg (red / white / blue; inventory row s 1344 left)',
                 src='extent pass (judge r3) on c20_s1500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1334-1394, was 1331-1394)'),
            dict(side='left', a=(35.486569, -119.540943), b=(35.4865743, -119.5410413), colors='rwb', off=-0.33, name='left s 1384-1393',
                 colour_src='t054.jpg (red / white / blue; inventory row s 1344 left)',
                 src='extent pass (judge r3) on c20_s1500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1334-1394, was 1331-1394)'),
            dict(side='left', a=(35.486599, -119.5414607), b=(35.486602, -119.5415605), colors='rwb', off=0.23, name='left s 1431-1440',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1431-1440 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1431-1475, was 1429-1478)'),
            dict(side='left', a=(35.4866023, -119.5415715), b=(35.4866042, -119.5416702), colors='rwb', off=0.07, name='left s 1441-1450',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1441-1450 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1431-1475, was 1429-1478)'),
            dict(side='left', a=(35.4866044, -119.5416811), b=(35.4866062, -119.5417784), colors='rwb', off=-0.25, name='left s 1451-1460',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1451-1460 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1431-1475, was 1429-1478)'),
            dict(side='left', a=(35.4866064, -119.5417892), b=(35.4866078, -119.5418869), colors='rwb', off=-0.53, name='left s 1461-1470',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1461-1470 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1431-1475, was 1429-1478)'),
            dict(side='left', a=(35.486608, -119.5418978), b=(35.4866086, -119.5419422), colors='rwb', off=-0.73, name='left s 1471-1475',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1471-1475 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1431-1475, was 1429-1478)'),
            dict(side='left', a=(35.486838, -119.5425841), b=(35.4868881, -119.5426586), colors='rwb', off=-0.41, name='left s 1536-1545',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1536-1545 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1650: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1536-1570, was 1533-1570)'),
            dict(side='left', a=(35.4868936, -119.5426669), b=(35.4869425, -119.542743), colors='rwb', off=-0.37, name='left s 1546-1555',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1546-1555 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1700: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1536-1570, was 1533-1570)'),
            dict(side='left', a=(35.486948, -119.5427515), b=(35.4869983, -119.5428287), colors='rwb', off=-0.45, name='left s 1556-1565',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1556-1565 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1700: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1536-1570, was 1533-1570)'),
            dict(side='left', a=(35.487004, -119.5428373), b=(35.4870269, -119.5428716), colors='rwb', off=-0.41, name='left s 1566-1570',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1566-1570 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1700: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1536-1570, was 1533-1570)'),
            dict(side='left', a=(35.4874301, -119.5434792), b=(35.4874641, -119.5435582), colors=['#b8433a', '#dedbd2'], off=-0.05, name='left s 1642-1651',
                 colour_src='t060.jpg (red / white; inventory row s 1645 left)',
                 src='extent pass (judge r3) on c20_s1750: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1642-1677, was 1640-1676)'),
            dict(side='left', a=(35.4874676, -119.5435672), b=(35.4874963, -119.5436509), colors=['#b8433a', '#dedbd2'], off=-0.45, name='left s 1652-1661',
                 colour_src='t062.jpg (red / white; inventory row s 1645 left)',
                 src='extent pass (judge r3) on c20_s1800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1642-1677, was 1640-1676)'),
            dict(side='left', a=(35.4874991, -119.5436605), b=(35.4875211, -119.5437496), colors=['#b8433a', '#dedbd2'], off=-0.57, name='left s 1662-1671',
                 colour_src='t062.jpg (red / white; inventory row s 1645 left)',
                 src='extent pass (judge r3) on c20_s1800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1642-1677, was 1640-1676)'),
            dict(side='left', a=(35.4875231, -119.5437598), b=(35.4875304, -119.5438011), colors=['#b8433a', '#dedbd2'], off=-0.69, name='left s 1672-1677',
                 colour_src='t062.jpg (red / white; inventory row s 1645 left)',
                 src='extent pass (judge r3) on c20_s1800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1642-1677, was 1640-1676)'),
            dict(side='left', a=(35.4874379, -119.5455018), b=(35.4873983, -119.5455728), colors='rwb', off=-6.65, name='left s 1837-1846',
                 colour_src='t068.jpg (red / white / blue; inventory row s 1839 left)',
                 src='extent pass (judge r3) on c20_s1950: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1837-1848, was 1842-1848)'),
            dict(side='left', a=(35.489095, -119.5499305), b=(35.4891413, -119.5499557), colors='rwb', off=-0.45, name='left s 2532-2538',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 2532-2538 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s2650: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2532-2538, was 2519-2538)'),
            dict(side='left', a=(35.4902321, -119.550554), b=(35.4903045, -119.5506005), colors='rwb', off=0.25, name='left s 2671-2680',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='extent pass (judge r3) on c20_s2800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2671-2740, was 2673-2740)'),
            dict(side='left', a=(35.4903126, -119.5506056), b=(35.4903859, -119.5506505), colors='rwb', off=-0.37, name='left s 2681-2690',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='extent pass (judge r3) on c20_s2800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2671-2740, was 2673-2740)'),
            dict(side='left', a=(35.4903941, -119.5506554), b=(35.490468, -119.5506985), colors='rwb', off=-0.49, name='left s 2691-2700',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='extent pass (judge r3) on c20_s2800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2671-2740, was 2673-2740)'),
            dict(side='left', a=(35.4904762, -119.5507032), b=(35.4905506, -119.5507451), colors='rwb', off=-0.61, name='left s 2701-2710',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='extent pass (judge r3) on c20_s2850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2671-2740, was 2673-2740)'),
            dict(side='left', a=(35.4905589, -119.5507497), b=(35.4906355, -119.5507894), colors='rwb', off=-0.33, name='left s 2711-2720',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='extent pass (judge r3) on c20_s2850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2671-2740, was 2673-2740)'),
            dict(side='left', a=(35.4906442, -119.5507935), b=(35.490725, -119.5508272), colors='rwb', off=-0.45, name='left s 2721-2730',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='extent pass (judge r3) on c20_s2850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2671-2740, was 2673-2740)'),
            dict(side='left', a=(35.4907342, -119.5508304), b=(35.4908195, -119.550853), colors='rwb', off=-0.37, name='left s 2731-2740',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='extent pass (judge r3) on c20_s2850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2671-2740, was 2673-2740)'),
            dict(side='left', a=(35.4916237, -119.5504418), b=(35.4916865, -119.5503925), colors='rwb', off=-0.63, name='left s 2837-2846',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 2837-2846 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s2950: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2837-2856, was 2837-2843)'),
            dict(side='left', a=(35.4929379, -119.5497467), b=(35.4930057, -119.5497351), colors='rwb', off=-0.45, name='left s 2999-3007',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 2999-3007 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s3150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2999-3007, was 2996-3005)'),
            dict(side='left', a=(35.4959311, -119.5496033), b=(35.4960115, -119.5495999), colors='rwb', off=-0.33, name='left s 3334-3343',
                 colour_src='t110.jpg (red / white / blue; inventory row s 3329 left)',
                 src='extent pass (judge r3) on c20_s3450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3334-3380, was 3322-3380)'),
            dict(side='left', a=(35.4960203, -119.5495995), b=(35.4960998, -119.5495961), colors='rwb', off=-0.41, name='left s 3344-3353',
                 colour_src='t110.jpg (red / white / blue; inventory row s 3329 left)',
                 src='extent pass (judge r3) on c20_s3450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3334-3380, was 3322-3380)'),
            dict(side='left', a=(35.4961087, -119.5495958), b=(35.4961899, -119.5495939), colors='rwb', off=-0.53, name='left s 3354-3363',
                 colour_src='t110.jpg (red / white / blue; inventory row s 3329 left)',
                 src='extent pass (judge r3) on c20_s3500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3334-3380, was 3322-3380)'),
            dict(side='left', a=(35.4961991, -119.5495937), b=(35.4962842, -119.5495892), colors='rwb', off=-0.53, name='left s 3364-3373',
                 colour_src='t110.jpg (red / white / blue; inventory row s 3329 left)',
                 src='extent pass (judge r3) on c20_s3500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3334-3380, was 3322-3380)'),
            dict(side='left', a=(35.4962938, -119.5495882), b=(35.4963526, -119.5495788), colors='rwb', off=-0.09, name='left s 3374-3380',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 3374-3380 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s3500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3334-3380, was 3322-3380)'),
            dict(side='left', a=(35.4965927, -119.5487678), b=(35.4965312, -119.5486934), colors='rwb', off=-0.29, name='left s 3463-3472',
                 colour_src='t116.jpg (red / white / blue; inventory row s 3479 left)',
                 src='extent pass (judge r3) on c20_s3600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3463-3513, was 3461-3510)'),
            dict(side='left', a=(35.4965244, -119.5486856), b=(35.4964638, -119.5486186), colors='rwb', off=-0.53, name='left s 3473-3482',
                 colour_src='t116.jpg (red / white / blue; inventory row s 3479 left)',
                 src='extent pass (judge r3) on c20_s3600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3463-3513, was 3461-3510)'),
            dict(side='left', a=(35.4964572, -119.5486113), b=(35.4963982, -119.5485453), colors='rwb', off=-0.53, name='left s 3483-3492',
                 colour_src='t116.jpg (red / white / blue; inventory row s 3479 left)',
                 src='extent pass (judge r3) on c20_s3600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3463-3513, was 3461-3510)'),
            dict(side='left', a=(35.4963916, -119.5485379), b=(35.4963331, -119.5484706), colors='rwb', off=-0.43, name='left s 3493-3502',
                 colour_src='t116.jpg (red / white / blue; inventory row s 3479 left)',
                 src='extent pass (judge r3) on c20_s3600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3463-3513, was 3461-3510)'),
            dict(side='left', a=(35.4963267, -119.5484631), b=(35.4962685, -119.5483942), colors='rwb', off=-0.61, name='left s 3503-3512',
                 colour_src='t116.jpg (red / white / blue; inventory row s 3479 left)',
                 src='extent pass (judge r3) on c20_s3650: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3463-3513, was 3461-3510)'),
            dict(side='left', a=(35.4948094, -119.5478483), b=(35.4947289, -119.5478752), colors='rwb', off=-0.49, name='left s 3684-3693',
                 colour_src='t124.jpg (red / white / blue; inventory row s 3725 left)',
                 src='extent pass (judge r3) on c20_s3800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3684-3755, was 3683-3717)'),
            dict(side='left', a=(35.4947202, -119.5478784), b=(35.4946426, -119.5479067), colors='rwb', off=-0.57, name='left s 3694-3703',
                 colour_src='t124.jpg (red / white / blue; inventory row s 3725 left)',
                 src='extent pass (judge r3) on c20_s3800: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3684-3755, was 3683-3717)'),
            dict(side='left', a=(35.4945512, -119.5479381), b=(35.4944786, -119.5479575), colors='rwb', off=-0.29, name='left s 3714-3723',
                 colour_src='t124.jpg (red / white / blue; inventory row s 3725 left)',
                 src='extent pass (judge r3) on c20_s3850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3684-3755, was 3683-3717)'),
            dict(side='left', a=(35.4944706, -119.5479592), b=(35.4943987, -119.5479685), colors='rwb', off=-0.25, name='left s 3724-3733',
                 colour_src='t124.jpg (red / white / blue; inventory row s 3725 left)',
                 src='extent pass (judge r3) on c20_s3850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3684-3755, was 3683-3717)'),
            dict(side='left', a=(35.4943906, -119.5479688), b=(35.4943175, -119.547965), colors='rwb', off=-0.45, name='left s 3734-3743',
                 colour_src='t124.jpg (red / white / blue; inventory row s 3725 left)',
                 src='extent pass (judge r3) on c20_s3850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3684-3755, was 3683-3717)'),
            dict(side='left', a=(35.4943093, -119.5479639), b=(35.4942335, -119.5479473), colors='rwb', off=-0.45, name='left s 3744-3753',
                 colour_src='t124.jpg (red / white / blue; inventory row s 3725 left)',
                 src='extent pass (judge r3) on c20_s3850: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3684-3755, was 3683-3717)'),
            dict(side='left', a=(35.4934763, -119.5481157), b=(35.4934073, -119.5481448), colors='rwb', off=-0.45, name='left s 3838-3847',
                 colour_src='t128.jpg (red / white / blue; inventory row s 3848 left)',
                 src='extent pass (judge r3) on c20_s3950: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3838-3871, was 3826-3871)'),
            dict(side='left', a=(35.4933995, -119.5481474), b=(35.493328, -119.5481636), colors='rwb', off=-0.45, name='left s 3848-3857',
                 colour_src='t128.jpg (red / white / blue; inventory row s 3848 left)',
                 src='extent pass (judge r3) on c20_s3950: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3838-3871, was 3826-3871)'),
            dict(side='left', a=(35.4933198, -119.5481647), b=(35.493245, -119.5481685), colors='rwb', off=-0.61, name='left s 3858-3867',
                 colour_src='t128.jpg (red / white / blue; inventory row s 3848 left)',
                 src='extent pass (judge r3) on c20_s4000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3838-3871, was 3826-3871)'),
            dict(side='left', a=(35.4932365, -119.5481684), b=(35.4932106, -119.5481676), colors='rwb', off=-0.37, name='left s 3868-3871',
                 colour_src='t128.jpg (red / white / blue; inventory row s 3848 left)',
                 src='extent pass (judge r3) on c20_s4000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3838-3871, was 3826-3871)'),
            dict(side='left', a=(35.4923969, -119.5484645), b=(35.4923272, -119.5485048), colors='rwb', off=-0.53, name='left s 3965-3974',
                 colour_src='t132.jpg (red / white / blue; inventory row s 3981 left)',
                 src='extent pass (judge r3) on c20_s4100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3965-4018, was 3962-4015)'),
            dict(side='left', a=(35.4923194, -119.5485088), b=(35.4922483, -119.5485392), colors='rwb', off=-0.55, name='left s 3975-3984',
                 colour_src='t132.jpg (red / white / blue; inventory row s 3981 left)',
                 src='extent pass (judge r3) on c20_s4100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3965-4018, was 3962-4015)'),
            dict(side='left', a=(35.4921597, -119.5485624), b=(35.492086, -119.5485695), colors='rwb', off=-0.33, name='left s 3995-4004',
                 colour_src='t132.jpg (red / white / blue; inventory row s 3981 left)',
                 src='extent pass (judge r3) on c20_s4100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3965-4018, was 3962-4015)'),
            dict(side='left', a=(35.4920777, -119.5485697), b=(35.4920026, -119.5485651), colors='rwb', off=-0.45, name='left s 4005-4014',
                 colour_src='t132.jpg (red / white / blue; inventory row s 3981 left)',
                 src='extent pass (judge r3) on c20_s4100: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3965-4018, was 3962-4015)'),
            dict(side='left', a=(35.4919942, -119.548564), b=(35.4919688, -119.5485601), colors='rwb', off=-0.55, name='left s 4015-4018',
                 colour_src='t132.jpg (red / white / blue; inventory row s 3981 left)',
                 src='extent pass (judge r3) on c20_s4150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3965-4018, was 3962-4015)'),
            dict(side='left', a=(35.4888339, -119.5479321), b=(35.4887729, -119.547897), colors='rwb', off=-0.25, name='left s 4374-4383',
                 colour_src='t142.jpg (red / white / blue; inventory row s 4371 left)',
                 src='extent pass (judge r3) on c20_s4500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4374-4405, was 4371-4405)'),
            dict(side='left', a=(35.4887668, -119.5478919), b=(35.4887196, -119.5478341), colors='rwb', off=-0.73, name='left s 4384-4393',
                 colour_src='t142.jpg (red / white / blue; inventory row s 4371 left)',
                 src='extent pass (judge r3) on c20_s4500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4374-4405, was 4371-4405)'),
            dict(side='left', a=(35.4887153, -119.5478265), b=(35.488688, -119.5477497), colors='rwb', off=-0.09, name='left s 4394-4403',
                 colour_src='t142.jpg (red / white / blue; inventory row s 4371 left)',
                 src='extent pass (judge r3) on c20_s4500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4374-4405, was 4371-4405)'),
            dict(side='right', a=(35.4888259, -119.5424676), b=(35.4888336, -119.542368), colors='rwb', off=-0.45, name='right s 187-196',
                 colour_src='t010.jpg (red / white / blue; inventory row s 216 right)',
                 src='extent pass (judge r3) on c20_s0300: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.4888344, -119.5423568), b=(35.4888413, -119.5422563), colors='rwb', off=-0.53, name='right s 197-206',
                 colour_src='t010.jpg (red / white / blue; inventory row s 216 right)',
                 src='extent pass (judge r3) on c20_s0300: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.488842, -119.5422451), b=(35.4888483, -119.5421445), colors='rwb', off=-0.49, name='right s 207-216',
                 colour_src='t010.jpg (red / white / blue; inventory row s 216 right)',
                 src='extent pass (judge r3) on c20_s0350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.488849, -119.5421334), b=(35.4888552, -119.5420345), colors='rwb', off=-0.45, name='right s 217-226',
                 colour_src='t010.jpg (red / white / blue; inventory row s 216 right)',
                 src='extent pass (judge r3) on c20_s0350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.4888558, -119.5420236), b=(35.4888614, -119.5419272), colors='rwb', off=-0.49, name='right s 227-236',
                 colour_src='t010.jpg (red / white / blue; inventory row s 216 right)',
                 src='extent pass (judge r3) on c20_s0350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.4888619, -119.5419166), b=(35.4888664, -119.5418205), colors='rwb', off=-0.37, name='right s 237-246',
                 colour_src='t012.jpg (red / white / blue; inventory row s 256 right)',
                 src='extent pass (judge r3) on c20_s0350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.4888668, -119.5418097), b=(35.4888716, -119.5417098), colors='rwb', off=-0.45, name='right s 247-256',
                 colour_src='t012.jpg (red / white / blue; inventory row s 256 right)',
                 src='extent pass (judge r3) on c20_s0350: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.4888723, -119.5416983), b=(35.4888825, -119.541592), colors='rwb', off=-0.45, name='right s 257-266',
                 colour_src='t012.jpg (red / white / blue; inventory row s 256 right)',
                 src='extent pass (judge r3) on c20_s0400: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.4888842, -119.54158), b=(35.4888882, -119.5415557), colors='rwb', off=-0.25, name='right s 267-269',
                 colour_src='t012.jpg (red / white / blue; inventory row s 256 right)',
                 src='extent pass (judge r3) on c20_s0400: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 187-269, was 180-268)'),
            dict(side='right', a=(35.4895778, -119.5409754), b=(35.4896615, -119.5409789), colors='rwb', off=-0.41, name='right s 360-369',
                 colour_src='t018.jpg (red / white / blue; inventory row s 408 right)',
                 src='extent pass (judge r3) on c20_s0500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 360-380, was 358-382)'),
            dict(side='right', a=(35.4896707, -119.5409796), b=(35.4897533, -119.5409878), colors='rwb', off=-0.45, name='right s 370-379',
                 colour_src='t018.jpg (red / white / blue; inventory row s 408 right)',
                 src='extent pass (judge r3) on c20_s0500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 360-380, was 358-382)'),
            dict(side='right', a=(35.4899297, -119.5410182), b=(35.490011, -119.5410385), colors='rwb', off=-1.05, name='right s 398-407',
                 colour_src='t018.jpg (red / white / blue; inventory row s 408 right)',
                 src='extent pass (judge r3) on c20_p0840: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 398-424, was 394-423)'),
            dict(side='right', a=(35.4900198, -119.5410407), b=(35.4900971, -119.5410582), colors='rwb', off=-0.37, name='right s 408-417',
                 colour_src='t018.jpg (red / white / blue; inventory row s 408 right)',
                 src='extent pass (judge r3) on c20_s0550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 398-424, was 394-423)'),
            dict(side='right', a=(35.4901055, -119.5410598), b=(35.4901562, -119.5410677), colors='rwb', off=-0.45, name='right s 418-424',
                 colour_src='t018.jpg (red / white / blue; inventory row s 408 right)',
                 src='extent pass (judge r3) on c20_s0550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 398-424, was 394-423)'),
            dict(side='right', a=(35.4914759, -119.5416079), b=(35.4915477, -119.5416041), colors='rwb', off=-0.85, name='right s 582-591',
                 colour_src='t025.jpg (red / white / blue; inventory row s 590 right)',
                 src='extent pass (judge r3) on c20_s0700: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 582-605, was 580-609)'),
            dict(side='right', a=(35.4915554, -119.5416018), b=(35.4916185, -119.541565), colors='rwb', off=0.03, name='right s 592-601',
                 colour_src='t025.jpg (red / white / blue; inventory row s 590 right)',
                 src='extent pass (judge r3) on c20_s0700: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 582-605, was 580-609)'),
            dict(side='right', a=(35.4916246, -119.5415593), b=(35.4916416, -119.5415405), colors='rwb', off=-0.57, name='right s 602-605',
                 colour_src='t025.jpg (red / white / blue; inventory row s 590 right)',
                 src='extent pass (judge r3) on c20_s0750: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 582-605, was 580-609)'),
            dict(side='right', a=(35.4889036, -119.5393515), b=(35.4888333, -119.5393341), colors='rwb', off=-0.45, name='right s 1011-1020',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1011-1020 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1011-1046, was 1009-1027)'),
            dict(side='right', a=(35.4888255, -119.5393333), b=(35.4887562, -119.5393373), colors='rwb', off=-0.73, name='right s 1021-1030',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1021-1030 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1011-1046, was 1009-1027)'),
            dict(side='right', a=(35.4887486, -119.539339), b=(35.4886827, -119.5393656), colors='rwb', off=-0.13, name='right s 1031-1040',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1031-1040 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1011-1046, was 1009-1027)'),
            dict(side='right', a=(35.4886756, -119.5393697), b=(35.4886409, -119.5393933), colors='rwb', off=0.45, name='right s 1041-1046',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1041-1046 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s1150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1011-1046, was 1009-1027)'),
            dict(side='right', a=(35.4876634, -119.5394601), b=(35.4875965, -119.5394396), colors=['#b8433a', '#dedbd2'], off=-0.49, name='right s 1166-1175',
                 colour_src='t048.jpg (red / white; inventory row s 1175 right)',
                 src='extent pass (judge r3) on c20_s1300: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1166-1188, was 1164-1183)'),
            dict(side='right', a=(35.4875888, -119.5394383), b=(35.4875177, -119.5394352), colors=['#b8433a', '#dedbd2'], off=-0.37, name='right s 1176-1185',
                 colour_src='t048.jpg (red / white; inventory row s 1175 right)',
                 src='extent pass (judge r3) on c20_s1300: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1166-1188, was 1164-1183)'),
            dict(side='right', a=(35.4875096, -119.5394358), b=(35.4874934, -119.5394377), colors=['#b8433a', '#dedbd2'], off=-0.21, name='right s 1186-1188',
                 colour_src='t048.jpg (red / white; inventory row s 1175 right)',
                 src='extent pass (judge r3) on c20_s1300: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1166-1188, was 1164-1183)'),
            dict(side='right', a=(35.4867178, -119.5400237), b=(35.4866853, -119.5400976), colors='rwb', off=-0.41, name='right s 1295-1305',
                 colour_src='t052.jpg (red / white / blue; inventory row s 1304 right)',
                 src='extent pass (judge r3) on c20_s1400: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1285-1311, was 1288-1308)'),
            dict(side='right', a=(35.4866823, -119.5401064), b=(35.4866693, -119.5401515), colors='rwb', off=-0.25, name='right s 1306-1311',
                 colour_src='t052.jpg (red / white / blue; inventory row s 1304 right)',
                 src='extent pass (judge r3) on c20_s1450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1285-1311, was 1288-1308)'),
            dict(side='right', a=(35.4867281, -119.5421091), b=(35.4867434, -119.5421943), colors='rwb', off=-0.63, name='right s 1491-1500',
                 colour_src='t058.jpg (red / white / blue; inventory row s 1492 right)',
                 src='extent pass (judge r3) on c20_s1600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1491-1510, was 1488-1507)'),
            dict(side='right', a=(35.4867459, -119.5422034), b=(35.4867767, -119.542281), colors='rwb', off=-0.29, name='right s 1501-1510',
                 colour_src='t058.jpg (red / white / blue; inventory row s 1492 right)',
                 src='extent pass (judge r3) on c20_s1650: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1491-1510, was 1488-1507)'),
            dict(side='right', a=(35.4876239, -119.5448841), b=(35.4876136, -119.54498), colors='rwb', off=-0.09, name='right s 1776-1785',
                 colour_src='t066.jpg (white / red / blue; inventory row s 1773 right)',
                 src='extent pass (judge r3) on c20_s1900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1776-1815, was 1774-1813)'),
            dict(side='right', a=(35.4876129, -119.5449907), b=(35.4876092, -119.545088), colors='rwb', off=-0.57, name='right s 1786-1795',
                 colour_src='t066.jpg (white / red / blue; inventory row s 1773 right)',
                 src='extent pass (judge r3) on c20_s1900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1776-1815, was 1774-1813)'),
            dict(side='right', a=(35.4876091, -119.5450989), b=(35.4876096, -119.5451988), colors='rwb', off=-0.49, name='right s 1796-1805',
                 colour_src='t066.jpg (white / red / blue; inventory row s 1773 right)',
                 src='extent pass (judge r3) on c20_s1900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1776-1815, was 1774-1813)'),
            dict(side='right', a=(35.4876097, -119.5452102), b=(35.4876073, -119.5453144), colors='rwb', off=-0.21, name='right s 1806-1815',
                 colour_src='t066.jpg (white / red / blue; inventory row s 1773 right)',
                 src='extent pass (judge r3) on c20_s1950: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1776-1815, was 1774-1813)'),
            dict(side='right', a=(35.4873921, -119.5458176), b=(35.4873308, -119.5458861), colors='rwb', off=0.35, name='right s 1863-1872',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='extent pass (judge r3) on c20_s2000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1916, was 1864-1872)'),
            dict(side='right', a=(35.4873239, -119.5458935), b=(35.4872623, -119.5459589), colors='rwb', off=-0.25, name='right s 1873-1882',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='extent pass (judge r3) on c20_s2000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1916, was 1864-1872)'),
            dict(side='right', a=(35.4872554, -119.5459661), b=(35.4871944, -119.546031), colors='rwb', off=-0.17, name='right s 1883-1892',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='extent pass (judge r3) on c20_s2000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1916, was 1864-1872)'),
            dict(side='right', a=(35.4871877, -119.5460382), b=(35.4871288, -119.5461045), colors='rwb', off=0.15, name='right s 1893-1902',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='extent pass (judge r3) on c20_s2000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1916, was 1864-1872)'),
            dict(side='right', a=(35.4871224, -119.546112), b=(35.4870667, -119.5461806), colors='rwb', off=0.19, name='right s 1903-1912',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='extent pass (judge r3) on c20_s2050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1916, was 1864-1872)'),
            dict(side='right', a=(35.4870607, -119.5461883), b=(35.487043, -119.5462118), colors='rwb', off=0.15, name='right s 1913-1916',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='extent pass (judge r3) on c20_s2050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1916, was 1864-1872)'),
            dict(side='right', a=(35.4870372, -119.5462196), b=(35.4869862, -119.5462913), colors='rwb', off=-0.09, name='right s 1917-1926',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='extent pass (judge r3) on c20_s2050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1955, was 1878-1915)'),
            dict(side='right', a=(35.4869807, -119.5462993), b=(35.4869324, -119.5463731), colors='rwb', off=-0.57, name='right s 1927-1936',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1927-1936 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s2050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1955, was 1878-1915)'),
            dict(side='right', a=(35.4869272, -119.5463815), b=(35.4868806, -119.5464585), colors='rwb', off=-1.13, name='right s 1937-1946',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 1937-1946 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s2050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 1863-1955, was 1878-1915)'),
            dict(side='right', a=(35.4871616, -119.5497643), b=(35.4872331, -119.5497979), colors='rwb', off=-0.21, name='right s 2309-2318',
                 colour_src='t082.jpg (red / white / blue; inventory row s 2313 right)',
                 src='extent pass (judge r3) on c20_s2450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2309-2338, was 2307-2343)'),
            dict(side='right', a=(35.4873225, -119.5498334), b=(35.4873968, -119.5498574), colors='rwb', off=0.11, name='right s 2329-2338',
                 colour_src='t082.jpg (red / white / blue; inventory row s 2313 right)',
                 src='extent pass (judge r3) on c20_s2450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2309-2338, was 2307-2343)'),
            dict(side='right', a=(35.4909962, -119.5507328), b=(35.491071, -119.5507226), colors='rwb', off=-0.33, name='right s 2759-2768',
                 colour_src='t094.jpg (red / white / blue; inventory row s 2760 right)',
                 src='extent pass (judge r3) on c20_s2900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2759-2786, was 2756-2786)'),
            dict(side='right', a=(35.4911606, -119.5506954), b=(35.4912154, -119.5506698), colors='rwb', off=-0.29, name='right s 2779-2786',
                 colour_src='t094.jpg (red / white / blue; inventory row s 2760 right)',
                 src='extent pass (judge r3) on c20_s2900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 2759-2786, was 2756-2786)'),
            dict(side='right', a=(35.4964278, -119.5494081), b=(35.4964833, -119.5493584), colors='wb', off=-0.57, name='right s 3393-3402',
                 colour_src='t112.jpg (blue / white; inventory row s 3425 right)',
                 src='extent pass (judge r3) on c20_s3500: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3393-3445, was 3391-3445)'),
            dict(side='right', a=(35.4964888, -119.549352), b=(35.4965328, -119.5492884), colors='wb', off=-0.41, name='right s 3403-3412',
                 colour_src='t112.jpg (blue / white; inventory row s 3425 right)',
                 src='extent pass (judge r3) on c20_s3550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3393-3445, was 3391-3445)'),
            dict(side='right', a=(35.496537, -119.5492808), b=(35.4965678, -119.5492083), colors='wb', off=-0.29, name='right s 3413-3422',
                 colour_src='t112.jpg (blue / white; inventory row s 3425 right)',
                 src='extent pass (judge r3) on c20_s3550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3393-3445, was 3391-3445)'),
            dict(side='right', a=(35.4965704, -119.5491999), b=(35.4965851, -119.5491228), colors='wb', off=-0.49, name='right s 3423-3432',
                 colour_src='t112.jpg (blue / white; inventory row s 3425 right)',
                 src='extent pass (judge r3) on c20_s3550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3393-3445, was 3391-3445)'),
            dict(side='right', a=(35.4965857, -119.5491141), b=(35.4965807, -119.5490364), colors='wb', off=-0.53, name='right s 3433-3442',
                 colour_src='t114.jpg (red / white / blue; inventory row s 3445 right)',
                 src='extent pass (judge r3) on c20_s3550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3393-3445, was 3391-3445)'),
            dict(side='right', a=(35.496579, -119.5490279), b=(35.4965749, -119.5490111), colors='wb', off=-0.49, name='right s 3443-3445',
                 colour_src='t114.jpg (red / white / blue; inventory row s 3445 right)',
                 src='extent pass (judge r3) on c20_s3550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3393-3445, was 3391-3445)'),
            dict(side='right', a=(35.4940462, -119.548028), b=(35.4939735, -119.5480253), colors='rwb', off=0.83, name='right s 3772-3781',
                 colour_src='t126.jpg (red / white / blue; inventory row s 3787 right)',
                 src='extent pass (judge r3) on c20_s3900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3772-3804, was 3769-3804)'),
            dict(side='right', a=(35.4939655, -119.548026), b=(35.4938951, -119.5480404), colors='rwb', off=-0.37, name='right s 3782-3791',
                 colour_src='t126.jpg (red / white / blue; inventory row s 3787 right)',
                 src='extent pass (judge r3) on c20_s3900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3772-3804, was 3769-3804)'),
            dict(side='right', a=(35.4938875, -119.5480429), b=(35.4938193, -119.5480726), colors='rwb', off=-0.53, name='right s 3792-3801',
                 colour_src='t126.jpg (red / white / blue; inventory row s 3787 right)',
                 src='extent pass (judge r3) on c20_s3900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3772-3804, was 3769-3804)'),
            dict(side='right', a=(35.4938119, -119.5480766), b=(35.4937969, -119.5480851), colors='rwb', off=-0.63, name='right s 3802-3804',
                 colour_src='t126.jpg (red / white / blue; inventory row s 3787 right)',
                 src='extent pass (judge r3) on c20_s3900: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3772-3804, was 3769-3804)'),
            dict(side='right', a=(35.4930641, -119.5483083), b=(35.4929894, -119.5483128), colors='rwb', off=-0.45, name='right s 3887-3896',
                 colour_src='t130.jpg (red / white / blue; inventory row s 3914 right)',
                 src='extent pass (judge r3) on c20_s4000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3887-3930, was 3879-3929)'),
            dict(side='right', a=(35.4929813, -119.5483139), b=(35.4929093, -119.5483311), colors='rwb', off=-0.45, name='right s 3897-3907',
                 colour_src='t130.jpg (red / white / blue; inventory row s 3914 right)',
                 src='extent pass (judge r3) on c20_s4000: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3887-3930, was 3879-3929)'),
            dict(side='right', a=(35.4929014, -119.5483337), b=(35.4928312, -119.5483632), colors='rwb', off=-0.53, name='right s 3908-3917',
                 colour_src='t130.jpg (red / white / blue; inventory row s 3914 right)',
                 src='extent pass (judge r3) on c20_s4050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3887-3930, was 3879-3929)'),
            dict(side='right', a=(35.4928234, -119.548367), b=(35.4927536, -119.5484055), colors='rwb', off=-0.37, name='right s 3918-3927',
                 colour_src='t130.jpg (red / white / blue; inventory row s 3914 right)',
                 src='extent pass (judge r3) on c20_s4050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3887-3930, was 3879-3929)'),
            dict(side='right', a=(35.4927458, -119.5484102), b=(35.4927303, -119.5484196), colors='rwb', off=-0.47, name='right s 3928-3930',
                 colour_src='t130.jpg (red / white / blue; inventory row s 3914 right)',
                 src='extent pass (judge r3) on c20_s4050: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 3887-3930, was 3879-3929)'),
            dict(side='right', a=(35.4919077, -119.5486984), b=(35.4918265, -119.5486816), colors='wb', off=-0.69, name='right s 4023-4032',
                 colour_src='t134.jpg (white / blue; inventory row s 4065 right)',
                 src='extent pass (judge r3) on c20_s4150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4917294, -119.5486612), b=(35.4916501, -119.5486457), colors='wb', off=-0.41, name='right s 4043-4052',
                 colour_src='t134.jpg (white / blue; inventory row s 4065 right)',
                 src='extent pass (judge r3) on c20_s4150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4916413, -119.548644), b=(35.4915615, -119.5486289), colors='wb', off=-0.41, name='right s 4053-4062',
                 colour_src='t134.jpg (white / blue; inventory row s 4065 right)',
                 src='extent pass (judge r3) on c20_s4150: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4915526, -119.5486272), b=(35.4914725, -119.5486119), colors='wb', off=-0.45, name='right s 4063-4072',
                 colour_src='t134.jpg (white / blue; inventory row s 4065 right)',
                 src='extent pass (judge r3) on c20_s4200: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4914636, -119.5486102), b=(35.4913833, -119.5485948), colors='wb', off=-0.45, name='right s 4073-4082',
                 colour_src='t134.jpg (white / blue; inventory row s 4065 right)',
                 src='extent pass (judge r3) on c20_s4200: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4913744, -119.5485931), b=(35.491294, -119.5485779), colors='wb', off=-0.41, name='right s 4083-4092',
                 colour_src='t134.jpg (white / blue; inventory row s 4065 right)',
                 src='extent pass (judge r3) on c20_s4200: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4912851, -119.5485762), b=(35.4912045, -119.5485612), colors='wb', off=-0.41, name='right s 4093-4102',
                 colour_src='t136.jpg (white / blue; inventory row s 4122 right)',
                 src='extent pass (judge r3) on c20_s4200: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4911955, -119.5485596), b=(35.4911149, -119.548545), colors='wb', off=-0.45, name='right s 4103-4112',
                 colour_src='t136.jpg (white / blue; inventory row s 4122 right)',
                 src='extent pass (judge r3) on c20_s4200: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4023-4114, was 4021-4070)'),
            dict(side='right', a=(35.4910881, -119.5485402), b=(35.4910435, -119.5485322), colors='wb', off=-0.49, name='right s 4115-4120',
                 colour_src='t136.jpg (white / blue; inventory row s 4122 right)',
                 src='extent pass (judge r3) on c20_s4250: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4042-4120, was 4087-4120)'),
            dict(side='right', a=(35.4893383, -119.5482122), b=(35.4892574, -119.5482022), colors='wb', off=-0.29, name='right s 4313-4322',
                 colour_src='t140.jpg (white / blue; inventory row s 4308 right)',
                 src='extent pass (judge r3) on c20_s4450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4313-4364, was 4310-4363)'),
            dict(side='right', a=(35.4892483, -119.548201), b=(35.4891663, -119.5481887), colors='wb', off=-0.59, name='right s 4323-4332',
                 colour_src='t140.jpg (white / blue; inventory row s 4308 right)',
                 src='extent pass (judge r3) on c20_s4450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4313-4364, was 4310-4363)'),
            dict(side='right', a=(35.4891572, -119.5481871), b=(35.4890766, -119.5481715), colors='wb', off=-0.57, name='right s 4333-4342',
                 colour_src='t140.jpg (white / blue; inventory row s 4308 right)',
                 src='extent pass (judge r3) on c20_s4450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4313-4364, was 4310-4363)'),
            dict(side='right', a=(35.4890678, -119.5481696), b=(35.488988, -119.5481505), colors='wb', off=-0.33, name='right s 4343-4352',
                 colour_src='t140.jpg (white / blue; inventory row s 4308 right)',
                 src='extent pass (judge r3) on c20_s4450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4313-4364, was 4310-4363)'),
            dict(side='right', a=(35.4889791, -119.5481481), b=(35.4888969, -119.5481223), colors='wb', off=-0.45, name='right s 4353-4362',
                 colour_src="colour unverified: no inventory kerb row on that side within 40 m of s 4353-4362 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='extent pass (judge r3) on c20_s4450: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4313-4364, was 4310-4363)'),
            dict(side='right', a=(35.4885588, -119.547608), b=(35.4885531, -119.5475031), colors='rwb', off=-0.53, name='right s 4418-4427',
                 colour_src='t144.jpg (white / blue / red; inventory row s 4410 right)',
                 src='extent pass (judge r3) on c20_s4550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
            dict(side='right', a=(35.4885528, -119.5474917), b=(35.4885512, -119.5473906), colors='rwb', off=-0.41, name='right s 4428-4437',
                 colour_src='t144.jpg (white / blue / red; inventory row s 4410 right)',
                 src='extent pass (judge r3) on c20_s4550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
            dict(side='right', a=(35.4885512, -119.5473795), b=(35.4885526, -119.5472803), colors='rwb', off=-0.29, name='right s 4438-4447',
                 colour_src='t146.jpg (red / white / blue; inventory row s 4458 right)',
                 src='extent pass (judge r3) on c20_s4550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
            dict(side='right', a=(35.4885529, -119.5472693), b=(35.488557, -119.54717), colors='rwb', off=-0.45, name='right s 4448-4457',
                 colour_src='t146.jpg (red / white / blue; inventory row s 4458 right)',
                 src='extent pass (judge r3) on c20_s4550: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
            dict(side='right', a=(35.4885575, -119.5471589), b=(35.4885632, -119.547059), colors='rwb', off=-0.49, name='right s 4458-4467',
                 colour_src='t146.jpg (red / white / blue; inventory row s 4458 right)',
                 src='extent pass (judge r3) on c20_s4600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
            dict(side='right', a=(35.4885638, -119.5470479), b=(35.4885701, -119.5469482), colors='rwb', off=-0.49, name='right s 4468-4477',
                 colour_src='t146.jpg (red / white / blue; inventory row s 4458 right)',
                 src='extent pass (judge r3) on c20_s4600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
            dict(side='right', a=(35.4885709, -119.5469371), b=(35.4885778, -119.5468385), colors='rwb', off=-0.37, name='right s 4478-4487',
                 colour_src='t146.jpg (red / white / blue; inventory row s 4458 right)',
                 src='extent pass (judge r3) on c20_s4600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
            dict(side='right', a=(35.4885786, -119.5468276), b=(35.4885848, -119.5467408), colors='rwb', off=-0.29, name='right s 4488-4496',
                 colour_src='t146.jpg (red / white / blue; inventory row s 4458 right)',
                 src='extent pass (judge r3) on c20_s4600: the block line followed on the clean captures with the edge fit band reader (edges_spline.bands outer limits, -10..+1.5 m, >= 2 capture rows per station; run measured s 4418-4496, was 4418-4492)'),
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
                 sections=[dict(from_m=286.0, to_m=292.0, color='#3b3a38')],
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
            dict(name='pit entry paddock fence', kind='fence', h=1.5, fence=1.5, color='#9aa0a4',
                 h_src='person-ref on the pit-lane video t1231000-t1240000: chest-high mesh',
                 src='c20_s4400 / c20_p0180 / c20_p0240 (the lane entry) and pit-lane video ucmXJu5QKFQ 20:31-20:40 (t1231000, t1240000; judge r3 pit_00): a ~1.5 m mesh fence along the paddock side of the pit entry; placed 1.0 m beyond the lane part\'s paddock-side edge at track s 4290-4362',
                 latlon=[[35.4895475, -119.5480695], [35.4895302, -119.5480617], [35.489513, -119.5480542], [35.4894958, -119.5480467], [35.4894788, -119.5480393], [35.4894631, -119.5480324], [35.4894499, -119.5480256], [35.4894375, -119.548017], [35.4894235, -119.5480056], [35.4894085, -119.5479929], [35.4893934, -119.54798], [35.4893783, -119.5479673], [35.4893625, -119.5479538], [35.489348, -119.5479416], [35.4893332, -119.5479291], [35.4893185, -119.5479166], [35.4893042, -119.5479045], [35.489291, -119.5478926], [35.4892782, -119.5478801], [35.489265, -119.5478666], [35.4892516, -119.5478524], [35.4892379, -119.5478379], [35.4892243, -119.5478235], [35.4892107, -119.5478092], [35.4891971, -119.5477949], [35.4891834, -119.5477804], [35.4891698, -119.5477661], [35.4891565, -119.5477519], [35.489144, -119.5477383], [35.4891327, -119.5477249], [35.4891215, -119.5477103], [35.4891099, -119.5476944], [35.4890979, -119.547678], [35.489086, -119.5476615], [35.4890741, -119.5476451], [35.4890622, -119.5476285], [35.4890506, -119.5476124], [35.4890401, -119.5475973], [35.4890314, -119.5475832]]),
            dict(name='T11 approach tree-line tyre barrier', kind='tyres', h=0.85, fence=0.0, color='#202020',
                 h_src='tyre-ref: three to four tyres high on the back view (judge r3 back_07, 0.7-1.0 m)',
                 src='c20_s4300 (stage3_evidence/tyre4200.png): a long dark tyre line under the trees ~27 m beyond the left edge at s ~4150-4260; judge r3 back_07 (looking back at 4200); onboard t136-t138 (dark line under the trees, left)',
                 latlon=[(35.4907449, -119.5480121), (35.490594, -119.5479922), (35.4904215, -119.5479724), (35.4902274, -119.5479393), (35.490055, -119.5478995), (35.4899256, -119.5478664), (35.4898394, -119.5478201)]),
        ],
        osm_barrier_overrides={},
        tyre_facings=None,
        impact_barriers=[
            dict(wall='pit wall, front straight', end='start', w=1.8, d=2.6, h=0.9, color='#e4dfd2', style='rounded',   # judge r3: bulky, rounded, pale (pit video t1240000)
                 src='pit-lane video ucmXJu5QKFQ 20:40 (t1240000): a sand / dirt berm piled against the pit wall head where the pit-in lane meets it; onboard s4500 / t148: the wall head low and light ahead left'),
        ],
        tyre_stacks=[],
        blocks=[],
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
            dict(name='pit-in station', latlon=(35.4887617, -119.5465905), h=3.9, w=2.0, color='#cfd4d8', style='canopy', mound_h=0.5,
                 base_color='#cfc6b2', pole=True, body_h=1.2, body_color='#e8e6e0',
                 h_src='person-ref against the pit-wall K-rail (0.81 m) on the pit-lane video t1240000',
                 src="pit-lane video ucmXJu5QKFQ 20:40 (t1240000): a canopy on one pole over a small white 'CAC CLUB' cabinet on a pale base at the pit-wall head (judge r3 pit_00, the entry shelter); c20_s4550 / c20_s4600: the white roof at the wall head (compare/blob_scan.py, s 4511 left 8.5 m); pit row s 4320 corrected to 4508"),
            dict(name='T1 inside canopy', latlon=(35.4893951, -119.5418382), h=2.8, w=5.0, color='#e8e6e0', style='canopy', mound_h=0.3,
                 h_src='person-ref: a canopy on posts over a low concrete platform (onboard t010, ~one storey)',
                 src="c20_s0300 / c20_s0350: a white roof ~5 x 3 m among the trees inside T1, 42 m beyond the left edge at s 247 (compare/blob_scan.py; stage3_evidence/blob247.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60; judge r1 row)"),
            dict(name='pit-wall end hut', latlon=(35.4890197, -119.5423407), h=2.6, color='#e8e6e0', style='canopy', mound_h=0.3,
                 h_src='person-ref: a one-storey white hut with a canopy over a low concrete platform (onboard t010, people beside it)',
                 src="c20_s0300 / c20_s0350: white roof 7.8 m2 at the east end of the pit wall (compare/blob_scan.py, 5.2 m beyond the left edge at s 199; window stage3_evidence/cw_wallend.png); onboard t010 (0:10): canopy on posts over a low concrete platform ahead left (inventory station row s 246 left, ahead_m 60)"),
            dict(name="starter's stand", latlon=(35.4888807, -119.5445092), h=4.4, w=1.6, color='#e8e6e0', style='platform', stair=True, roof=True,  # judge r3: a compact raised platform, deck ~1.8 m, rails, a ladder and a small canopy (pit video t1339000 / t1348000)
                
                 h_src='person-ref: people stand on its deck at about the wall-top-plus-3 m line (pit-lane video 22:19-22:28, t1339000 / t1348000)',
                 src="c20_s0050 / c20_s0100 / c20_s0150: the white structure on the pit wall at the timing line (blob_scan s 2, 3.4 m beyond the left edge); pit-lane video ucmXJu5QKFQ 22:19-22:28: the scaffold starter's stand with a canopy on the pit wall"),
        ],
        light_masts=[
            dict(latlon=(35.4981168, -119.5486443), h=49.5, style='flood',   # judge r3: the head reads as a light cluster on the onboard (s3350 / t106)
                 src='OSM man_made=mast / communications tower node 10220517717; the lidar (CA_SanJoaquin_2021) has an isolated spike 49.5-49.7 m over the DEM there (30 cells, compare/stage3 lidar spike scan); onboard t106 (1:46): a tall thin pole far ahead on the north leg (inventory mast row s 3400 ahead, ahead_m 250)'),
        ],
        cone_lines_declared=[
            # single orange (and one yellow) marker cones at turn-ins and road mouths, as the onboard shows them
            dict(side='right', s=(40, 54), off=0.8, spacing=3.5, size=0.7,
                 src='judge r3 runoff (s 46 R): cones across the front-straight crossover (OSM 34351026) mouth on the right; onboard t006 (the two cones at the mouth, inventory s 20-24 R)'),
            dict(side='right', s=(1914, 1915), off=1.5, spacing=4.0, size=0.7,
                 src='compare_sheets onboard s1900 (t 70.76): an orange cone beside the end of the right kerb (judge r3 1920 R)'),
            dict(side='right', s=(3199, 3200), off=1.5, spacing=4.0, size=0.7,
                 src='compare_sheets onboard s3200 (t 107.15): an orange cone at the right edge (judge r3 fwd_10 3200 R)'),
            # judge r2 (GPT 6 Astra + orchestrator): cones the frames show that the package lacked (positions along the track
            # from the frame's time map, +-15 m)
            dict(side='right', s=(140, 160), off=2.0, spacing=5.0, size=0.7,
                 src='onboard t006-t008 (judge r2, fwd_00): several orange cones on the paved shoulder right'),
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
            dict(latlon=[(35.4890355, -119.5446533), (35.4890434, -119.5445333)], spacing=4.0, size=0.46, color='#e8c21c',
                 src='pit-lane video t1303000 (21:43): three yellow cones at the timing tower foot, lane side of the paddock K-rail (judge r3 pit_01)'),
            # judge r1 (orchestrator, 20 Oct 2026): cones the onboard shows that the package lacked; placed from the frames
            # at the sheet stations (temporary items, absent on the 2026 captures; along-track position +-15 m)
            dict(side='left', s=(752, 772), off=3.0, spacing=4.0, size=0.45,
                 src='onboard t030 / compare_sheets s0700, s0750 (fwd_02, side_02): a line of small orange cones on the pale apron left of the T2 approach (inventory cone_line row s 770 left, ahead_m 80); the "3-4 cones" of s0700 are this line seen from 60 m back'),
            dict(side='left', s=(3196, 3204), off=2.0, spacing=4.0, size=0.7,
                 src='compare_sheets s3200 (fwd_10): three orange cones at a mouth on the left'),
            dict(side='right', s=(4046, 4054), off=3.0, spacing=4.0, size=0.7,
                 src='compare_sheets s4050 (fwd_13): cones on the right apron, 20 m before the t134 cone at s 4071'),
            dict(side='right', s=(20, 24), off=1.5, spacing=4.0, size=0.7,
                 src='onboard t006.jpg (yellow, orange; inventory s 20 right: two cones, yellow and orange); position along the track from the time map (+-10-30 m), 1.5 m beyond the edge from the frame (the cones stand on the dirt next to the edge or the kerb)'),
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
            dict(name='outer T2 loop (OSM 39224609)', ways=['39224609'], half_width=5.5, surface='asphalt', mouth_cones=[],
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
        paved_areas=[
            dict(name='pit entry strip', surface='asphalt', latlon=[[35.4895399, -119.5480754], [35.4895314, -119.5480718], [35.489523, -119.5480683], [35.4895144, -119.5480646], [35.489506, -119.5480611], [35.4894974, -119.5480574], [35.489489, -119.5480539], [35.4894806, -119.5480503], [35.4894722, -119.5480467], [35.4894641, -119.5480432], [35.4894565, -119.5480398], [35.4894495, -119.5480363], [35.489443, -119.5480326], [35.4894368, -119.5480285], [35.4894304, -119.5480239], [35.4894237, -119.5480186], [35.4894167, -119.5480129], [35.4894094, -119.5480068], [35.4894021, -119.5480006], [35.4893947, -119.5479943], [35.4893873, -119.5479882], [35.4893799, -119.5479819], [35.4893725, -119.5479757], [35.4893651, -119.5479694], [35.4893578, -119.5479631], [35.4893503, -119.5479569], [35.4893429, -119.5479506], [35.4893355, -119.5479444], [35.4893281, -119.5479382], [35.4893207, -119.5479319], [35.4893134, -119.5479257], [35.4893061, -119.5479195], [35.489299, -119.5479135], [35.4892922, -119.5479074], [35.4892855, -119.5479013], [35.489279, -119.547895], [35.4892725, -119.5478886], [35.4892659, -119.5478819], [35.4892592, -119.547875], [35.4892525, -119.5478678], [35.4892457, -119.5478607], [35.4892389, -119.5478536], [35.4892321, -119.5478463], [35.4892253, -119.5478391], [35.4892184, -119.5478319], [35.4892117, -119.5478248], [35.4892049, -119.5478176], [35.489198, -119.5478104], [35.4891912, -119.5478032], [35.4891844, -119.547796], [35.4891776, -119.5477888], [35.4891708, -119.5477816], [35.489164, -119.5477745], [35.4891573, -119.5477674], [35.4891506, -119.5477602], [35.4891441, -119.5477533], [35.4891379, -119.5477464], [35.489132, -119.5477396], [35.4891263, -119.5477326], [35.4891206, -119.5477254], [35.4891149, -119.5477177], [35.489109, -119.5477099], [35.4891032, -119.5477017], [35.4890972, -119.5476936], [35.4890912, -119.5476853], [35.4890853, -119.5476771], [35.4890793, -119.5476689], [35.4890733, -119.5476606], [35.4890674, -119.5476524], [35.4890614, -119.5476442], [35.4890555, -119.5476359], [35.4890495, -119.5476277], [35.4890438, -119.5476197], [35.4890382, -119.5476118], [35.4890331, -119.5476042], [35.4890283, -119.5475968], [35.489024, -119.5475894], [35.4890199, -119.5475817], [35.4889591, -119.5476287], [35.4889647, -119.5476393], [35.4889709, -119.5476498], [35.4889771, -119.5476596], [35.4889834, -119.547669], [35.4889896, -119.5476777], [35.4889957, -119.5476862], [35.4890018, -119.5476946], [35.4890077, -119.5477028], [35.4890137, -119.547711], [35.4890196, -119.5477193], [35.4890256, -119.5477276], [35.4890316, -119.5477357], [35.4890376, -119.547744], [35.4890435, -119.5477523], [35.4890495, -119.5477606], [35.4890557, -119.5477689], [35.4890618, -119.5477773], [35.4890683, -119.5477859], [35.4890751, -119.5477945], [35.4890821, -119.5478031], [35.4890892, -119.5478113], [35.4890963, -119.5478192], [35.4891034, -119.5478267], [35.4891103, -119.5478341], [35.4891171, -119.5478414], [35.4891239, -119.5478486], [35.4891308, -119.5478558], [35.4891376, -119.5478629], [35.4891444, -119.5478702], [35.4891512, -119.5478774], [35.4891581, -119.5478846], [35.4891648, -119.5478917], [35.4891716, -119.5478989], [35.4891785, -119.5479061], [35.4891853, -119.5479132], [35.4891921, -119.5479204], [35.4891989, -119.5479277], [35.4892058, -119.5479349], [35.4892127, -119.5479422], [35.4892197, -119.5479494], [35.4892269, -119.5479568], [35.4892343, -119.5479642], [35.489242, -119.5479715], [35.4892497, -119.5479786], [35.4892574, -119.5479854], [35.489265, -119.5479919], [35.4892725, -119.5479983], [35.48928, -119.5480046], [35.4892874, -119.5480109], [35.4892948, -119.5480172], [35.4893022, -119.5480234], [35.4893096, -119.5480296], [35.4893209, -119.5480357], [35.4893209, -119.5480357], [35.4893298, -119.5480374], [35.4893388, -119.5480391], [35.4893477, -119.5480408], [35.4893568, -119.5480426], [35.4893657, -119.5480443], [35.4893748, -119.548046], [35.489384, -119.5480477], [35.4893931, -119.5480495], [35.4894023, -119.5480514], [35.4894115, -119.5480531], [35.4894206, -119.5480551], [35.4894299, -119.548057], [35.4894391, -119.548059], [35.4894485, -119.548061], [35.4894577, -119.5480631], [35.489467, -119.5480653], [35.4894763, -119.5480675], [35.4894856, -119.5480697], [35.4894948, -119.548072], [35.4895042, -119.5480744], [35.4895134, -119.5480769], [35.4895226, -119.5480793], [35.4895318, -119.5480818]],
                 src='the pit lane part between its edges at track s 4290-4362 (judge r3 pit_00: the NAIP 2022 ground-coloured patches between the white lines; the pit video t1231000-t1240000 shows continuous asphalt)'),
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
            dict(contains=(35.4896585, -119.5454773), drop=True, src='no 2026 source: 29 x 8 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4897631, -119.5436739), drop=True, src='no 2026 source: 28 x 7 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4900634, -119.545886), drop=True, src='no 2026 source: 20 x 7 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4900867, -119.5455277), drop=True, src='no 2026 source: 30 x 9 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4901442, -119.5443856), drop=True, src='no 2026 source: 16 x 9 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4910066, -119.5464487), drop=True, src='no 2026 source: 18 x 37 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4909536, -119.5459547), drop=True, src='no 2026 source: 32 x 19 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4909886, -119.5453399), drop=True, src='no 2026 source: 29 x 19 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4911432, -119.5449521), drop=True, src='no 2026 source: 20 x 50 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4912851, -119.5454006), drop=True, src='no 2026 source: 20 x 33 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4912087, -119.5451689), drop=True, src='no 2026 source: 4 x 14 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4913637, -119.546265), drop=True, src='no 2026 source: 60 x 18 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4915986, -119.543098), drop=True, src='no 2026 source: 33 x 16 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4916938, -119.547039), drop=True, src='no 2026 source: 11 x 16 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
            dict(contains=(35.4919274, -119.546024), drop=True, src='no 2026 source: 19 x 12 m lidar (2021) structure in the paddock, outside every clean capture (the z20 set covers the track corridor); the pit-lane video (t1240000-t1366000) and the onboard (t000-t008) show the paddock behind the K-rail full of trailers, cars and trees with no building attributable to this footprint'),
        ],
        season_tint=None,
        gates=dict(allowed=[
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
                  to_walls=dict(reach=4.0)),   # judge r3 pit_01 / pit_02: pavement from the lane to both K-rails (pit video t1249000-t1348000)
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
    structures=dict(suppress_osm=['765811057'], items=[
        # judge r3: the pit-lane video t1303000 (21:43) and t150-t152 show a two-storey building whose upper storey is set
        # back behind an open deck with posts and a railing, divided glazing, an exterior stair on the track side, the
        # deep blue roof over it; the capture (stage3_evidence/tower_cap.png on c20_s0050 / c20_p0420) shows the roof at
        # ~25 x 20 m, the OSM footprint the walls
        dict(type='block', name='timing tower', osm='765811057', h=3.2, storeys=1, parapet=0.0,
             wall='#cdb892', band='#3a4756', roof='#9c9a94', bands=[0], band_frac=[0.35, 0.75], mullions_m=2.0, deck_rail=True,
             balcony=dict(side='track', z=3.2, depth=0.8, color='#cdb892', stair=True),
             src='OSM 765811057 (the walls); pit-lane video t1303000 / t1312000 / t1330000 and onboard t146-t152: tan ground storey with windows, the open deck on its roof with a railing, the exterior stair on the track side',
             h_src='storey 3.2 m (HEIGHTS.md); the deck on its roof'),
        dict(type='block', name='timing tower upper storey', rect=dict(c=(35.4891529, -119.5445723), heading_deg=3.83, l=17.0, w=11.0),
             base=3.2, h=2.8, storeys=1, wall='#cdb892', band='#2e3a48', roof='#9c9a94', bands=[0], band_frac=[0.1, 0.9], mullions_m=1.2,
             src='pit-lane video t1303000: the upper storey set back behind the deck, divided glazing (the window frames read as mullions)',
             h_src='storey 2.8 m under the roof deck; the lidar top of the footprint 9.8 m includes the roof'),
        dict(type='fuel', name='timing tower roof deck', rect=dict(c=(35.4891529, -119.5445723), heading_deg=3.83, l=25.2, w=20.0),
             h=6.4, fascia=0.6, canopy='#2f5d9e', fascia_color='#2f5d9e',
             posts=3, islands=0,
             src='pit-lane video t1312000 / t1330000 and onboard t004 / t146-t152: the blue flat roof on posts over the tower deck, a broad overhang (1.5 m past the OSM footprint each side, judge r2)',
             h_src='lidar: the footprint top 9.8 m (scenery building_height_robust), roof 0.5 m'),
    ]),
    # ---------------------------------------------------------------- app (SKILL stage 6)
    app=dict(short='Buttonwillow', pace='cars/field/buttonwillow/pace.json'),
)
