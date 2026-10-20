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
    stations_ref=None,                           # (n, length_m) of the build the station numbers below refer to (SKILL 1.3)
    # the pit-out merge (round 6 / stage 3 pass, 1.10 review item 1): the pit lane comes round the inside of T1 and
    # shares the pavement with the track from ~s 432 to ~527, between two lines of white kerb blocks (the left kerb
    # band ending at s 432, c20_s0500 / c20_p0840; the block line starting at s 527, c20_s0650, sheet
    # edge_sheets/pitout_merge_470-540). There is no painted blend line and no cone on the shared pavement (captures
    # c20_s0600 / c20_s0650; onboard 0:18-0:22, frames t018-t022: one wide asphalt surface). The pipeline's rule put the
    # blend boundary on the OSM pit way's own edge, 1.5-3 m inside the shared pavement (width 7.66 m at 509). The
    # boundary is the straight line joining the two block lines' ends, measured on the captures.
    centre=dict(pit_merge_line=dict(latlon=[(35.4902035, -119.5410911), (35.4910048, -119.5413669)],
                                    src='left kerb band end at s 432 (c20_s0500 / c20_p0840) to the block line start at s 527 (c20_s0650); no paint between')),
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
                     # set aside after stage-1 runs 17 and 19 (manifest, stage-3 round): ('right', 355, 432, (-18.0, 1.5), 'T1 exit: the white block line from 4 m inside the right edge at s 361 to the left edge at '),
                     ('left', 540, 582, (-10.0, 1.5), 'block line 2.7-6.6 m inside the left edge at s 540-560 (cw_533); onboard t022 (0:22): red '),
                     ('left', 1076, 1112, (-10.0, 1.5), 'block line 5.4-6.5 m inside the left edge (cw_1086); onboard t044 (0:44): red / white / bl'),
                     # set aside after stage-1 run 17 (manifest, stage-3 round): ('left', 1318, 1392, (-10.0, 1.5), 'block line 4.6-8.6 m inside the left edge, along the middle of the paved strip (cw_1348); '),
                     ('right', 1760, 1810, (-10.0, 1.5), 'block line 0-5.4 m inside the right edge where the Dog Leg leaves (cw_1751, cw_1824); onbo'),
                     ('left', 3675, 3712, (-10.0, 1.5), 'block line 1.3-1.8 m inside the left edge (c20_s3800); onboard t124 (2:04): red / white / '),
                     ('left', 3948, 4010, (-10.0, 1.5), 'block line 1.3-1.8 m inside the left edge (c20_s4100 / c20_s4150); onboard t132 (2:12): re'),
                     ('right', 4050, 4112, (-10.0, 1.5), 'block line 1.5-5.5 m inside the right edge (c20_s4150 .. c20_s4250); onboard t134 / t136 ('),
                     # set aside after stage-1 run 17 (manifest, stage-3 round): ('right', 4402, 4445, (-10.0, 1.5), 'block line 5.6-8.0 m inside the right edge (c20_s4500 / c20_s4550); onboard t144 / t146 (2'),
                ],
                mask=[('left', 4250, 4272, 'c20_s4400: marshal post mound beside the left edge at s ~4255-4268'),
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
        # stage-3 pass (20 Oct 2026): block-line kerbs laid on wider pavement, the paved apron beyond fitted as track by
        # asphalt_end; the edge is the blocks' outer limit (SKILL 1.5), found with a per-zone search window
        # set aside after stage-1 runs 17 and 19 (manifest, stage-3 round): ('right', 355, 432, 'kerb_band', 'block line, search window (-18.0, 1.5) (spline.kerb_search): T1 exit: the white block line from 4 m inside the right edge at s 361 to the left edge at s 425 (stage3_evidence/cw_400ov.png, cw_t1raw.png); the flying lap runs west of it with the blocks on its right, converging (onboard 0:16-0:18, s0350 / s0400 / t016 / t018); the dark pavement east of it is a paved apron inside T1'),
        ('left', 540, 582, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 2.7-6.6 m inside the left edge at s 540-560 (cw_533); onboard t022 (0:22): red / white / blue kerb close left, running ahead'),
        ('left', 1076, 1112, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 5.4-6.5 m inside the left edge (cw_1086); onboard t044 (0:44): red / white / blue kerb on the left through the left-hander'),
        # set aside after stage-1 run 17 (manifest, stage-3 round): ('left', 1318, 1392, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 4.6-8.6 m inside the left edge, along the middle of the paved strip (cw_1348); onboard t054 (0:54): red / white / blue kerb on the left, the car right of it'),
        ('right', 1760, 1810, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 0-5.4 m inside the right edge where the Dog Leg leaves (cw_1751, cw_1824); onboard t066 (1:06): white / red / blue kerb ahead right'),
        ('left', 3675, 3712, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 1.3-1.8 m inside the left edge (c20_s3800); onboard t124 (2:04): red / white / blue kerb on the left'),
        ('left', 3948, 4010, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 1.3-1.8 m inside the left edge (c20_s4100 / c20_s4150); onboard t132 (2:12): red / white / blue kerb on the left'),
        ('right', 4050, 4112, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 1.5-5.5 m inside the right edge (c20_s4150 .. c20_s4250); onboard t134 / t136 (2:14-2:16): white / blue kerb on the right'),
        # set aside after stage-1 run 17 (manifest, stage-3 round): ('right', 4402, 4445, 'kerb_band', 'block line, search window (-10.0, 1.5) (spline.kerb_search): block line 5.6-8.0 m inside the right edge (c20_s4500 / c20_s4550); onboard t144 / t146 (2:24-2:26): kerb on the right'),
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
                  palettes={'rwb': ['#b8433a', '#dedbd2', '#3c62a8']}, require_colour_src=True),
        kerbs_declared=[
            dict(side='left', a=(35.489041, -119.5414792), b=(35.4892736, -119.541204), colors='rwb', off=-0.5, name='left s 280-322',
                 colour_src='t014.jpg (red / white / blue; inventory row s 301 left)',
                 src='kerb_detect run s 280-322 (43 m, 100 %, offsets -1.0..+0.0 m) on c20_s0400, c20_s0450'),
            dict(side='left', a=(35.4899879, -119.5410605), b=(35.4901533, -119.5410784), colors='rwb', off=-0.55, name='left s 406-426',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 406-426 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 406-426 (21 m, 100 %, offsets -1.1..+0.0 m) on c20_p0840, c20_s0550'),
            dict(side='left', a=(35.4911375, -119.5403192), b=(35.491087, -119.5402956), colors='rwb', off=-0.3, name='left s 744-750',
                 colour_src='t032.jpg (white / red; inventory row s 738 left)',
                 src='kerb_detect run s 744-750 (7 m, 100 %, offsets -0.4..-0.2 m) on c20_s0850, c20_s0900'),
            dict(side='left', a=(35.4894908, -119.539494), b=(35.4889697, -119.5392355), colors='rwb', off=-0.6, name='left s 942-1004',
                 colour_src='t038.jpg (white / red; inventory row s 973 left)',
                 src='kerb_detect run s 942-1004 (63 m, 100 %, offsets -1.0..-0.2 m) on c20_s1050, c20_s1100, c20_s1150'),
            dict(side='left', a=(35.4873784, -119.5393707), b=(35.4872749, -119.5394268), colors='rwb', off=-0.2, name='left s 1192-1204',
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='kerb_detect run s 1192-1204 (13 m, 100 %, offsets -0.5..+0.1 m) on c20_s1300, c20_s1350'),
            dict(side='left', a=(35.4870268, -119.5395943), b=(35.4868255, -119.5397175), colors='rwb', off=-0.4, name='left s 1236-1260',
                 colour_src='t050.jpg (red / white / blue; inventory row s 1224 left)',
                 src='kerb_detect run s 1236-1260 (26 m, 100 %, offsets -0.9..+0.1 m) on c20_s1350, c20_s1400'),
            dict(side='left', a=(35.4865896, -119.5417295), b=(35.4866056, -119.5419779), colors='rwb', off=-1.3, name='left s 1450-1473',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 1450-1473 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 1450-1473 (24 m, 100 %, offsets -1.5..-1.1 m) on c20_s1600'),
            dict(side='left', a=(35.4868341, -119.5425984), b=(35.4870086, -119.5428681), colors='rwb', off=-1.4, name='left s 1532-1564',
                 colour_src='t060.jpg (red / white; inventory row s 1580 left)',
                 src='kerb_detect run s 1532-1564 (33 m, 100 %, offsets -1.5..-1.3 m) on c20_s1650, c20_s1700'),
            dict(side='left', a=(35.4874237, -119.5434651), b=(35.4875287, -119.5437833), colors='rwb', off=-0.45, name='left s 1636-1670',
                 colour_src='t062.jpg (red / white; inventory row s 1645 left)',
                 src='kerb_detect run s 1636-1670 (35 m, 100 %, offsets -0.9..+0.0 m) on c20_s1750, c20_s1800'),
            dict(side='left', a=(35.4889918, -119.5498988), b=(35.4891424, -119.5499572), colors='rwb', off=-0.1, name='left s 2513-2532',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 2513-2532 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 2513-2532 (20 m, 95 %, offsets -0.9..+0.7 m) on c20_s2650'),
            dict(side='left', a=(35.4902467, -119.5505646), b=(35.4908263, -119.550853), colors='rwb', off=-0.5, name='left s 2667-2735',
                 colour_src='t092.jpg (red / white / blue; inventory row s 2696 left)',
                 src='kerb_detect run s 2667-2735 (69 m, 100 %, offsets -1.0..+0.0 m) on c20_s2800, c20_s2850'),
            dict(side='left', a=(35.4916258, -119.5504396), b=(35.4916611, -119.5504117), colors='rwb', off=-0.25, name='left s 2831-2836',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 2831-2836 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 2831-2836 (6 m, 100 %, offsets -0.4..-0.1 m) on c20_s2950'),
            dict(side='left', a=(35.4929126, -119.5497522), b=(35.4930127, -119.5497362), colors='rwb', off=-0.5, name='left s 2990-3002',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 2990-3002 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 2990-3002 (13 m, 100 %, offsets -1.0..+0.0 m) on c20_s3100, c20_s3150'),
            dict(side='left', a=(35.4939375, -119.5496866), b=(35.4939901, -119.5496804), colors='rwb', off=-1.15, name='left s 3105-3111',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 3105-3111 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 3105-3111 (7 m, 100 %, offsets -1.5..-0.8 m) on c20_s3250'),
            dict(side='left', a=(35.4958179, -119.5496042), b=(35.4963563, -119.549579), colors='rwb', off=-0.4, name='left s 3315-3374',
                 colour_src='t110.jpg (red / white / blue; inventory row s 3329 left)',
                 src='kerb_detect run s 3315-3374 (60 m, 100 %, offsets -0.9..+0.1 m) on c20_s3450, c20_s3500'),
            dict(side='left', a=(35.4966051, -119.5487848), b=(35.4962748, -119.5484017), colors='rwb', off=-0.5, name='left s 3455-3505',
                 colour_src='t116.jpg (red / white / blue; inventory row s 3475 left)',
                 src='kerb_detect run s 3455-3505 (51 m, 100 %, offsets -0.8..-0.2 m) on c20_s3550, c20_s3600, c20_s3650'),
            dict(side='left', a=(35.4935504, -119.5480627), b=(35.4933962, -119.548131), colors='rwb', off=-1.38, name='left s 3820-3840',
                 colour_src='t128.jpg (red / white / blue; inventory row s 3854 left)',
                 src='kerb_detect run s 3820-3840 (21 m, 100 %, offsets -1.5..-1.3 m) on c20_s3950'),
            dict(side='left', a=(35.4888567, -119.5479467), b=(35.4886949, -119.5477995), colors='rwb', off=-0.45, name='left s 4363-4389',
                 colour_src='t142.jpg (red / white / blue; inventory row s 4370 left)',
                 src='kerb_detect run s 4363-4389 (27 m, 100 %, offsets -1.0..+0.1 m) on c20_s4500'),
            dict(side='left', a=(35.4885839, -119.546979), b=(35.4886016, -119.5467772), colors='rwb', off=-0.85, name='left s 4468-4489',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 4468-4489 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 4468-4489 (22 m, 100 %, offsets -1.3..-0.4 m) on c20_s4600'),
            dict(side='right', a=(35.4888189, -119.5425498), b=(35.4888868, -119.541564), colors='rwb', off=-0.65, name='right s 179-268',
                 colour_src='t010.jpg (red / white / blue; inventory row s 216 right)',
                 src='kerb_detect run s 179-268 (90 m, 100 %, offsets -1.3..+0.0 m) on c20_s0300, c20_s0350, c20_s0400'),
            dict(side='right', a=(35.4906265, -119.5410658), b=(35.4906772, -119.5410869), colors='rwb', off=-0.8, name='right s 477-483',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 477-483 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 477-483 (7 m, 100 %, offsets -1.0..-0.6 m) on c20_s0600'),
            dict(side='right', a=(35.4889197, -119.5393677), b=(35.4888108, -119.539346), colors='rwb', off=-1.3, name='right s 1006-1020',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 1006-1020 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 1006-1020 (15 m, 100 %, offsets -1.5..-1.1 m) on c20_s1150'),
            dict(side='right', a=(35.4887501, -119.5393515), b=(35.4886417, -119.5394004), colors='rwb', off=-0.05, name='right s 1028-1043',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 1028-1043 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 1028-1043 (16 m, 88 %, offsets -0.5..+0.4 m) on c20_s1150'),
            dict(side='right', a=(35.4876801, -119.5394583), b=(35.4875173, -119.5394259), colors='rwb', off=0.45, name='right s 1158-1178',
                 colour_src='t048.jpg (red / white; inventory row s 1172 right)',
                 src='kerb_detect run s 1158-1178 (21 m, 90 %, offsets +0.1..+0.8 m) on c20_s1300'),
            dict(side='right', a=(35.4867192, -119.5400382), b=(35.4866778, -119.5401328), colors='rwb', off=-1.0, name='right s 1290-1300',
                 colour_src='t052.jpg (red / white / blue; inventory row s 1302 right)',
                 src='kerb_detect run s 1290-1300 (12 m, 100 %, offsets -1.4..-0.6 m) on c20_s1400, c20_s1450'),
            dict(side='right', a=(35.4867262, -119.5420782), b=(35.4867761, -119.542281), colors='rwb', off=-0.65, name='right s 1483-1505',
                 colour_src='t058.jpg (red / white / blue; inventory row s 1494 right)',
                 src='kerb_detect run s 1483-1505 (23 m, 100 %, offsets -1.1..-0.2 m) on c20_s1600, c20_s1650'),
            dict(side='right', a=(35.487625, -119.5452088), b=(35.4876092, -119.5452973), colors='rwb', off=-1.0, name='right s 1800-1808',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 1800-1808 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 1800-1808 (9 m, 100 %, offsets -1.4..-0.6 m) on c20_s1900, c20_s1950'),
            dict(side='right', a=(35.4873878, -119.5458186), b=(35.4873339, -119.5458816), colors='rwb', off=0.25, name='right s 1858-1866',
                 colour_src='t070.jpg (red / white / blue; inventory row s 1878 right)',
                 src='kerb_detect run s 1858-1866 (9 m, 100 %, offsets -0.1..+0.6 m) on c20_s2000'),
            dict(side='right', a=(35.4869671, -119.5463038), b=(35.4869317, -119.5463503), colors='rwb', off=0.5, name='right s 1923-1929',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 1923-1929 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 1923-1929 (7 m, 100 %, offsets +0.3..+0.7 m) on c20_s2050'),
            dict(side='right', a=(35.4871439, -119.5497551), b=(35.4874344, -119.5498694), colors='rwb', off=-0.15, name='right s 2301-2337',
                 colour_src='t082.jpg (red / white / blue; inventory row s 2312 right)',
                 src='kerb_detect run s 2301-2337 (37 m, 100 %, offsets -0.9..+0.6 m) on c20_s2450'),
            dict(side='right', a=(35.4909692, -119.550734), b=(35.4912109, -119.5506715), colors='rwb', off=-0.7, name='right s 2750-2780',
                 colour_src='t094.jpg (red / white / blue; inventory row s 2757 right)',
                 src='kerb_detect run s 2750-2780 (31 m, 97 %, offsets -1.2..-0.2 m) on c20_s2900'),
            dict(side='right', a=(35.4964169, -119.5494155), b=(35.4965745, -119.5490097), colors='rwb', off=-0.45, name='right s 3385-3439',
                 colour_src='t112.jpg (blue / white; inventory row s 3421 right)',
                 src='kerb_detect run s 3385-3439 (55 m, 100 %, offsets -0.9..+0.0 m) on c20_s3500, c20_s3550'),
            dict(side='right', a=(35.4948805, -119.5479958), b=(35.4948268, -119.5480016), colors='rwb', off=-1.35, name='right s 3672-3678',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 3672-3678 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 3672-3678 (7 m, 100 %, offsets -1.5..-1.2 m) on c20_s3800'),
            dict(side='right', a=(35.4943486, -119.547965), b=(35.4942112, -119.5479634), colors='rwb', off=-0.05, name='right s 3730-3746',
                 colour_src="colour unverified: no inventory kerb row on that side within 15 m of s 3730-3746 (the lap's kerbs are red / white / blue where the onboard shows them)",
                 src='kerb_detect run s 3730-3746 (17 m, 100 %, offsets -0.9..+0.8 m) on c20_s3850, c20_s3900'),
            dict(side='right', a=(35.4939736, -119.548012), b=(35.4937965, -119.5480859), colors='rwb', off=-0.3, name='right s 3774-3796',
                 colour_src='t126.jpg (red / white / blue; inventory row s 3788 right)',
                 src='kerb_detect run s 3774-3796 (23 m, 91 %, offsets -0.9..+0.3 m) on c20_s3900'),
            dict(side='right', a=(35.4931326, -119.5483093), b=(35.4927224, -119.5484244), colors='rwb', off=-0.45, name='right s 3872-3922',
                 colour_src='t130.jpg (red / white / blue; inventory row s 3914 right)',
                 src='kerb_detect run s 3872-3922 (52 m, 100 %, offsets -0.9..+0.0 m) on c20_s4000, c20_s4050'),
            dict(side='right', a=(35.4919325, -119.5487026), b=(35.4916085, -119.5486511), colors='rwb', off=-0.58, name='right s 4012-4048',
                 colour_src='t134.jpg (white / blue; inventory row s 4066 right)',
                 src='kerb_detect run s 4012-4048 (38 m, 100 %, offsets -1.1..-0.1 m) on c20_s4150'),
            dict(side='right', a=(35.4893631, -119.5482158), b=(35.4889094, -119.5481261), colors='rwb', off=-0.55, name='right s 4302-4352',
                 colour_src='t140.jpg (white / blue; inventory row s 4308 right)',
                 src='kerb_detect run s 4302-4352 (51 m, 100 %, offsets -1.0..-0.1 m) on c20_s4400, c20_s4450'),
        ],
        kerb_lines=[],
        declared_walls=[
            # the pit wall: white K-rail (Jersey) segments with red panels between the front straight and the pit lane,
            # measured with compare/wall_measure.py (--edge left, bright band 3.5-3.7 m beyond the left edge)
            dict(name='pit wall, front straight', kind='concrete', h=0.81, fence=0.0, color='#e4e2dc',
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
                 h_src='jersey-ref: a K-rail like the pit wall (pit-lane video 20:49, t1249000: both walls the same height)',
                 src='wall_measure.py --edge left 4490-4693 --off 12,30 (68 % picked, 20.8 m beyond the left edge) on c20_s4600 / c20_p0360; pit-lane video 20:49-21:52 (Jersey wall on the left of the lane)',
                 latlon=[(35.4889157, -119.5464997), (35.4889363, -119.5462801), (35.4889488, -119.54606), (35.4889616, -119.5458399),
                         (35.4889738, -119.5456197), (35.4889864, -119.5453996), (35.4889993, -119.5451795), (35.489005, -119.5450805)]),
            dict(name='pit lane, paddock side, tower', kind='concrete', h=0.81, fence=0.0, color='#e4e2dc',
                 h_src='jersey-ref (as the west run)',
                 src='wall_measure.py --edge left (175-210 m and 0-42 m runs, 21 m beyond the left edge) on c20_p0420 / c20_p0480; pit-lane video 21:52 (the wall at the tower, a yellow cone at its foot)',
                 latlon=[(35.4890129, -119.5449429), (35.489031, -119.5447233), (35.4890355, -119.5445633), (35.4890427, -119.544551),
                         (35.48906, -119.5443313), (35.489061, -119.5441102)]),
            dict(name='pit lane, paddock side, east', kind='concrete', h=0.81, fence=0.0, color='#e4e2dc',
                 h_src='jersey-ref (as the west run)',
                 src='wall_measure.py --edge left 0-300 --off 12,30 (54-196 m run, 21 m beyond the left edge) on c20_p0540 / c20_p0600',
                 latlon=[(35.4890699, -119.5439506), (35.489083, -119.5437306), (35.489096, -119.5435105), (35.4891084, -119.5432903),
                         (35.4891212, -119.5430702), (35.4891339, -119.5428501), (35.4891471, -119.5426301)]),
        ],
        osm_barrier_overrides={},
        tyre_facings=None,
        impact_barriers=[],
        tyre_stacks=[],
        blocks=[],
        # corner stations: a canopy roof on posts on a tyre-faced earth mound (the 'bunkers'); the station ledger in the manifest
        marshal_posts=[
            dict(name='T1 exit', latlon=(35.4906672, -119.5410779), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s0650: white roof 5.5 m2 in a dark tyre ring (compare/blob_scan.py, 0.4 m beyond the right edge at s 482); onboard t020 (0:20): canopy on posts on a tyre-faced mound close right; inventory s 477 right'),
            dict(name='T2 to T3, east side', latlon=(35.4904386, -119.5402123), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s0600: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 7.1 m beyond the right edge at s 820); onboard t034 (0:34): blue canopy on a tyre-faced mound ahead right; inventory s 834 right'),
            dict(name='T3', latlon=(35.4888477, -119.5394518), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s1150: white roof 5.6 m2 in a dark tyre ring (compare/blob_scan.py, 9.2 m beyond the right edge at s 1014); onboard t040 (0:40): blue canopy on posts on a tyre-faced mound close right; inventory s 996 right'),
            dict(name='T4', latlon=(35.4875581, -119.5395534), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s1300: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.6 m beyond the right edge at s 1173); onboard t046 (0:46): canopy on posts ahead right; inventory s 1186 right'),
            dict(name='T5', latlon=(35.4868397, -119.5421342), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s1550: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 11.8 m beyond the right edge at s 1492); onboard t058 (0:58): canopy on a tyre-faced mound right; inventory s 1524 right'),
            dict(name='T6 (Riverside)', latlon=(35.4865323, -119.5477238), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s2150: white roof 6.3 m2 in a dark tyre ring (compare/blob_scan.py, 10.4 m beyond the right edge at s 2069); onboard t074 (1:14): canopy on a tyre-faced mound ahead right; inventory s 2050 right'),
            dict(name='T7', latlon=(35.487615, -119.5496824), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s2500: white roof 5.9 m2 in a dark tyre ring (compare/blob_scan.py, 19.2 m beyond the right edge at s 2358); onboard t082 (1:22): canopy on a mound ahead right; inventory s 2372 right'),
            dict(name='T8', latlon=(35.4910638, -119.5506143), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s2900: white roof 5.7 m2 in a dark tyre ring (compare/blob_scan.py, 9.8 m beyond the right edge at s 2764); onboard t092 (1:32): canopy on posts ahead right; inventory s 2776 right'),
            dict(name='north leg before T9', latlon=(35.4946878, -119.5493983), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s3300: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 11.0 m beyond the right edge at s 3189); onboard not in the 2 s frames (t106-t108 look past it); roof and tyre ring on c20_s3300 / c20_s3350'),
            dict(name='T9 (Star Mazda)', latlon=(35.4964593, -119.5491351), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s3500: white roof 5.8 m2 in a dark tyre ring (compare/blob_scan.py, 13.6 m beyond the right edge at s 3420); onboard t112 (1:52): roofed platform on stilts ahead right; inventory s 3436 right'),
            dict(name='T10', latlon=(35.4946445, -119.5481763), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s3800: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 15.4 m beyond the right edge at s 3698); onboard t122 (2:02): station far ahead right; inventory s 3758 right'),
            dict(name='T11 approach (Sunset)', latlon=(35.4896673, -119.5480246), h=3.0, color='#2f5d9e',
                 h_src='deck top: the canopy stands on a ~1.5 m earth mound (the tyre ring) with ~1.5 m posts; storeys / person scale on the onboard frames, unmeasured to better than +-0.5 m',
                 src='c20_s4350: white roof 5.4 m2 in a dark tyre ring (compare/blob_scan.py, 5.0 m beyond the left edge at s 4272); onboard t138 (2:18): canopy on a tyre-faced mound ahead left; inventory s 4274 left'),
            dict(name="starter's stand", latlon=(35.4888807, -119.5445092), h=4.0, color='#e8e6e0',
                 h_src='person-ref: people stand on its deck at about the wall-top-plus-3 m line (pit-lane video 22:19-22:28, t1339000 / t1348000)',
                 src="c20_s0050 / c20_s0100 / c20_s0150: the white structure on the pit wall at the timing line (blob_scan s 2, 3.4 m beyond the left edge); pit-lane video ucmXJu5QKFQ 22:19-22:28: the scaffold starter's stand with a canopy on the pit wall"),
        ],
        light_masts=[],
        cone_lines_declared=[
            # single orange (and one yellow) marker cones at turn-ins and road mouths, as the onboard shows them
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
        closed_roads=[
            dict(name='front-straight crossover (OSM 34351026)', ways=['34351026'], half_width=4.0, surface='concrete',
                 mouth_cones=[],   # the onboard's cones at its mouth (t006) are the cone_lines_declared entry at s 20-24 right
                 src='OSM 34351026; c20_s0150 / c20_s0200: pale concrete road south from the front straight'),
            dict(name='Atlantic (OSM 34351042)', ways=['34351042'], half_width=4.0, surface='concrete', mouth_cones=[],
                 src='OSM 34351042; c20_s0250 / c20_s0300: pale concrete road south-west from the front straight'),
            dict(name='Pacific (OSM 34350988)', ways=['34350988'], half_width=4.0, surface='concrete',
                 mouth_cones=[],   # the onboard's cone at its mouth (t002) is the cone_lines_declared entry at s 4575 right
                 src='OSM 34350988; c20_s4650 / c20_s4700: pale concrete road south from the front straight'),
            dict(name='crossover (OSM 34351015)', ways=['34351015'], half_width=4.0, surface='concrete', mouth_cones=[],
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
        paved_areas=[],
        pit_lane_clip_walls=True,
        terraces=[],
        grandstand_on_terrain=False,
        building_height_robust=True,
        building_overrides=[],
        building_evidence=[],
        season_tint=None,
        gates=dict(allowed=[
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
        lane=dict(source='osm', match_track_tone=dict(k=0.5, paint=0.97)),
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
    structures=dict(suppress_osm=[], items=[]),
    # ---------------------------------------------------------------- app (SKILL stage 6)
    app=dict(short='Buttonwillow', pace='cars/field/buttonwillow/pace.json'),
)
