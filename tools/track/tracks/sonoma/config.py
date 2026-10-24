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

# Round 6 (orchestrator F7 / S6): the walls the inventory records as "light blue" / "light blue-grey" read white-grey with
# a faint blue in the 2026 onboard (frames t060, t116, t130, t136: pale painted concrete under the camera's blue cast); the
# round-4 #a9c9dd drew them saturated blue. One pale blue-grey for all of them.
WALL_PALE_BLUE = '#d3dbe0'
# Round 6 (orchestrator S5): tyre walls are black-covered stacks (inventory: black tyre wall / dark tyre line rows), so every
# Sonoma tyre run carries its colour (the app's default black with a white pair every 12 stacks is Laguna's rule); the
# T11 hairpin's are white (onboard 2:01.5-2:03.5, white tyre stacks in front of the wall)
TYRE_BLACK, TYRE_WHITE = '#161616', '#dedede'

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
    centre=dict(extra_shadow_stations=[4084], width_cap=21.0,   # the shared drag-strip start pavement is ~19-20 m
                # the pit merge's inputs (stage 1 reads no scenery key, 20 Oct 2026). The accepted geometry (19 Oct 18:05)
                # took its wall end from the round-3 declared pit-side wall: it stands within 6 m of the left edge to
                # first-centre station 209, so the pit-exit line ran along the left edge from s 211 to the merge (s 240).
                # This is that point. Rounds 5-7e re-measured the T1 pit side (the nose at s ~103, a short pit-side wall
                # s 134-158 on c20_s1815 / c20_s1870, the blend line s 158-222: scenery.pit_exit_cones); moving the
                # stage-1 inputs to them is a geometry change (a new stage-1 pass), not made here. Round 8 (owner note
                # 59): there is no nose at s ~103; the pit wall is continuous to s ~158 (scenery only, geometry unchanged)
                pit_exit=dict(wall_end_latlon=(38.162006860, -122.456878843),
                              src='round-3 declared wall "pit straight and pit-out lane, pit-lane side" (c20_s1595..s1870 '
                                  'bright band 2.0 m beyond the left edge; its T1 run measured by hand on c20_s1925, the '
                                  'white wall line): its last point within 6 m of the left edge, first-centre station 209 '
                                  '(the accepted 19 Oct 18:05 build, config 9d6f3c1)'),
                # round 11 (owner notes 64 / 69): the Carousel-exit-to-T7 straights (the `local` straights below) are
                # refitted inside this window only, the accepted geometry held outside it (the refit loop's limit cycles
                # at the T7 hairpin and 9a and the uniform re-stationing would otherwise move the whole lap by up to 2.6 m)
                # round 14B (owner, round-13 drive: his red on the T1-T2 outline windows): a second local window round
                # T1 (config 114-383, his red 143-356 with the blend outside it), refitted after the first with
                # everything outside it held; the first window's refit is exactly round 11's (centre.local list form)
                local=[dict(window=(1643, 2091), blend=15,
                            why='round 11: the Carousel exit to T7 straights only (owner notes 64 / 69)'),
                       dict(window=(114, 383), blend=15,
                            why='round 14B: T1-T2 edges from the owner\'s red (spline.owner_edges, owner/r14)')]),
    loop_check=dict(n_min=3900, n_max=4250, official_m=4088, elev_min=20, elev_max=80),
    captures=dict(
        z20_dir=None,
        clean_dir='compare/sonoma/satellite_clean', clean_index='tiles.json',
        mpp=0.11738,                 # z20 at 38.163 N; overlapping captures measure 0.11749 (68 pairs, median)
        common_shift=None,           # measured by register_clean.py -> satellite_clean/shift.json
        clean_mask='clean',
        exclude=[],
    ),
    spline=dict(runs=None, knot=6, lam=30.0, huber=0.25, line_off=0.26, prior=0.03, init_stiff=30.0, captures='clean',
                # round 14B (owner, round-13 drive, 23 Oct 2026; compare/sonoma/owner_findings.md "Round 13 drive"): his
                # red on the T1-T2 outline windows (drawing page 6nG9T3NgsVajJPNSKkwhAc, read back 20:25 PDT; strokes in
                # compare/sonoma/owner_edges_r14/), both asphalt edges through s ~144-356. compare/owner_edges.py per drawn
                # window (w_s0250 at 0.12 m/px, close_s0175 / close_s0205 at 0.06 m/px; frames from frames.json,
                # checked against capwin re-renders of public/tracks/sonoma: zero offset, JPEG noise only; pixels kept
                # only on his stroke vectors, strokes.json) into owner/r14/<window>.json; compare/owner_merge.py
                # cross-fades them into owner/r14/merged.json (left 207 stations 144-357, right 192 stations 145-337 of
                # the round-14A package; 17 stations where two windows differ by > 0.3 m, his stroke repeatability).
                # Where he drew, his red wins (the fit's readings there replaced, his line anchored, OWNER_W); the
                # detected edge elsewhere; one global spline per side, refitted in the second local window only.
                # What it changes: the pit-side (left) edge's early blend toward the pit-exit lane at s ~205-225 ("this
                # concave section ... is not here") and its step onto the merged pit-exit lane at s ~228-233; the
                # paddock-side (right) excursion into the mouth at s ~165-185 and the 0.3-0.6 m bulge at s ~212-235.
                # His red sits on the asphalt edge, inside the kerbs; the right 180-260 'kerb' feature already puts the
                # edge on the kerb runs' inner side here, so no kerb shift (kerb_inside) is applied.
                owner_edges=[dict(file='owner/r14/merged.json', lo=143, hi=356, local=True,
                                  windows=['owner/r14/w_s0250.json', 'owner/r14/close_s0175.json', 'owner/r14/close_s0205.json'],
                                  src='owner round-13 drive red on edges windows w_s0250, close_s0175, close_s0205 '
                                      '(compare/sonoma/owner_edges_r14/*_marked.png, local), s 144-356')],
                # his red arc across the paddock-side mouth at s ~166-179 (owner_mouths.py --across: his green, the
                # access road's edge, ends on the arc at s 166; the arc rejoins his edge line at s 179): the course
                # boundary there and a cone line ("Put a few cones there"); the owner-reference gates leave its
                # stations +-12 out (edge_gate.OWNER_REF)
                owner_mouths='owner/r14/mouths.json'),
    # Carousel exit (T6) to the T7 approach, stations ~1680-2060 (onboard youtube.com/watch?v=RAZip6S84CM 0:55-1:09):
    # the course is bounded by the PAVEMENT, not by cones or a painted line. On the shared drag-strip start (to ~1880) the
    # car runs right of the yellow lane line with the red/white kerb as the right edge (0:59-1:01) and crosses the lane
    # line (1:03-1:04) toward the T7 road, whose left edge is the blue concrete wall at the asphalt's end (1:06-1:09,
    # c20_s3685/s3740: no painted line on that side) and whose right edge is the white line along the drag strip.
    features=[
        ('right', 180, 260, 'kerb', 'T1 exit right: the edge is the inner side of the blue/white kerb runs and the painted '
                                    'wedges between them (c20_s1925); the bright wedge pulled the paint finder outward '
                                    '(rolling wave 0.044 m at 218-228)'),
        ('left', 1860, 2060, 'asphalt_end', 'T7 road left edge: asphalt ends at the concrete wall, no painted line',
         dict(replaced_by_local=True)),
        # round 11 (the local refit, centre.local): the T7 road's asphalt-end zone starts at the fork vertex (config 1901),
        # not at 1860: from 1860 to the vertex the left edge is the drag strip's SW painted line, ~0.33 m wide, which the
        # clean captures show unbroken to the vertex (compare/sonoma/round11/edge_1872.png on c20_s3575 / c20_s0220 /
        # c20_s3630; strip_part1-2.png); read there as an asphalt end it gave edge readings 0.3 m outside the line at
        # 1868-1890 on every capture (c20_s0220, s0275, s3575, s3630, s3685)
        ('left', 1901, 2060, 'asphalt_end', 'T7 road left edge from the fork vertex: asphalt ends at the concrete wall, no painted line',
         dict(local=True)),
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
        # ---- round 11 (owner notes 64 and 69, 21-22 Oct 2026; the local refit, centre.local): "I don't think this line
        # should be wiggly. It should be straight"; "I don't think this section going to T7 is wavy like this"; owner_69's
        # satellite: both edges dead straight from the Carousel to T7. The clean captures show two straight legs 11 deg
        # apart (the drag strip at 141.6 deg, the T7 road at 152.9 deg), each between straight lines of one width:
        # (1) the T7 road's left line from the fork vertex (config 1901, where its asphalt end meets the drag strip's SW
        # paint line) on: the asphalt end lies on that line from the vertex to the T7 braking zone (c20_s0110 / c20_s0165 /
        # c20_s3630 / c20_s3685; compare/sonoma/round11/axisL_T7road.png); the free fit over the junction chorded 1-3 m
        # inside it at 1910-1995. Same line as the entry above (parallel to the T7 road's right line, one width).
        dict(side='left', fit='parallel', ref_side='right', ref_lo=1985, ref_hi=2095, lo=1901, hi=1984, join=(1901, 1906),
             end=1984, local=True,
             why='T7 road left from the fork vertex: the asphalt end on the T7 road left line (round 11, owner notes 64 / 69)'),
        # (2) the drag-strip leg from the Carousel exit to the fork (config 1716-1897/1899): the full drag strip between its
        # two straight painted edge lines (compare/sonoma/round11/strip_part0-2.png on c20_s0165 / c20_s0220 / c20_s3410 /
        # c20_s3465: the SW line on the left; the NE line, red / white blocks outside it, on the right). The free fit waved
        # +-0.2 m (left) and bowed +-0.4 m (right). Buttonwillow round 8's straights fit: the LEFT (SW) line read once
        # (RANSAC; a first try read the right line first and its RANSAC ran from the red / white blocks outside the NE
        # line at 1720-1800, where the line itself is not detected beside them, to the paint at 1840-1904: 0.7 deg off,
        # compare/sonoma/round11/axisR_cand.png), the right PARALLEL to it at its own readings' median distance
        # (width_shared: one width), read once. The NE paint is parallel to the SW line at 18.3-18.45 m from the Carousel
        # exit to config 1827 (current 1835), then curves in by ~1.4 m toward the fork (16.9 m at 1900; every overlapping
        # capture agrees: axisL_drag.png): the one-width line ends there and the free fit follows that paint; the left
        # line ends at config 1878 (current 1886): over the last ~20 m before the vertex the painted edge turns into the
        # fork corner (edge readings 0.3-0.5 m outside the straight line at current 1887-1905 on every capture), so the
        # fit follows that corner (the junction, gate exemption left 1860-1980) into the T7 road's line at the vertex.
        dict(side='left', fit='paint', lo=1716, hi=1878, join=(1716, 1721), end=1878, tol=0.15, once=True, local=True,
             why='drag-strip leg left: the SW painted edge line is straight (round 11, owner notes 64 / 69)'),
        dict(side='right', fit='paint', lo=1716, hi=1827, join=(1716, 1721), end=1827, tol=0.15, once=True, width_shared=True,
             local=True, why='drag-strip leg right: the NE painted edge line, parallel to the left one (one width; round 11, owner notes 64 / 69)'),
    ],
    gate=dict(straight_rms=0.10, step=0.10, profile_step=0.10, spline_obs_within=0.85,
              exempt=[('left', 3480, 3610, 'pit-in lane splits off on the left before T11 (dashed blend line, c20_s1155): '
                       'the edge steps in by ~5 m over 60 m as the lane leaves (junction, real)'),
                      ('left', 160, 260, 'pit-out lane joins on the left after T1 (c20_s1870/s1925; junction, real)'),
                      # round 14B (the owner's red and green at T1, owner/r14): the paddock access road's mouth on the right,
                      # as Buttonwillow's mouth exemptions (about +-20 stations round the mouth)
                      ('right', 145, 198, 'mouth of the paddock access road at T1 (round 14B: the owner\'s green, the road\'s pavement edge, '
                       'ends on his red arc at s 166, the arc rejoins his edge line at s 179; close_s0175 on c20_s1870 / c20_s1925); junction, real'),
                      ('left', 1860, 1980, 'the T7 road forks off the drag strip to the left (c20_s3685/s3740; junction, real)')]),
    # ---------------------------------------------------------------- stage 1: terrain override (round 14A, 23 Oct 2026)
    # Owner, round-13 drive (compare/sonoma/owner_findings.md): from the T7 approach the inactive paving (the Chute, the
    # short-T7 road, the paddock) sits on another level from the course, with a ridge where it meets it, the kerbed island
    # reads as a trough and the paving beside the T7 kerb steps down; "we might have to deviate from the lidar scan ...
    # The key thing is that the active and inactive track surfaces actually go together in a sensical way". Rule: every
    # paved surface touching the course joins it with no step, ridge or trough, the islands between them on the same
    # smooth surface; where the lidar disagrees, the lidar loses. Cause (compare/sonoma/round14a/LEDGER.md): the zones'
    # 7-point linear profiles and the 5 m shoulder blend over the raw bare-earth DEM (old paving edges, berms, trailers,
    # 0.1-0.5 m), a phantom paved plateau at the T7 inside runoff's start (zero-length stations), and the Chute built on
    # the creek bed under its bridge (the DEM is bare earth; the deck is class-17 returns, up to 6.9 m higher).
    # Inside the polygon: one thin-plate surface (tools/track/terrain_override.py) held on the course and its cross-slope
    # 1 m beyond the edges, pulled to it over 4 m, robust (biweight) to the lidar ground beyond with a 40 m cutoff, the
    # Chute's bridge deck returns where it has them; stiff to the lidar outside over 15 m (6 m fade beside the deck).
    # The polygon: the junction and islands right of T7-T7a from the T7 apex island (s ~2110) round to the T7a exit
    # (s ~2350), the drag strip's continuation to its fork, the T7 inside runoff, the O'Reilly island, the paddock lot
    # left of T7-T7a to the wall below the T7a stands (c20_s3850 / c20_s3905 / cap_-430_430), the T7a outside paddock
    # (c20_s3960 / c20_s4015), and the Chute from its T7 mouth across its bridge to its far abutment (the Chute zone + 4.5 m;
    # lidar class 17); the course's left edge + 1 m along T6-T7 and T7a-T8 (the creek bank and the T8 bank stay lidar).
    terrain_override=[
        dict(name='T7 complex', margin=15.0, ramp=1.5, edge_hold=1.0, edge_band=4.0, smooth_m=40.0, deck_returns=True, deck_fade=6.0,
             latlon=[(38.1657812, -122.4621941), (38.1658190, -122.4622957), (38.1658764, -122.4624488), (38.1659223, -122.4625562),
                     (38.1659663, -122.4626865), (38.1659106, -122.4627436), (38.1658405, -122.4628156), (38.1657713, -122.4628876),
                     (38.1657013, -122.4629584), (38.1656312, -122.4630304), (38.1655611, -122.4631012), (38.1654929, -122.4631755),
                     (38.1654497, -122.4632886), (38.1653860, -122.4633549), (38.1654479, -122.4634531), (38.1655126, -122.4633869),
                     (38.1656087, -122.4633583), (38.1656797, -122.4632886), (38.1657498, -122.4632166), (38.1658198, -122.4631458),
                     (38.1658890, -122.4630738), (38.1659591, -122.4630030), (38.1660292, -122.4629310), (38.1660849, -122.4628739),
                     (38.1662394, -122.4630384), (38.1663921, -122.4632098), (38.1666167, -122.4631983), (38.1668996, -122.4629813),
                     (38.1666301, -122.4623849), (38.1666867, -122.4623483), (38.1667721, -122.4622763), (38.1668511, -122.4621792),
                     (38.1668960, -122.4620912), (38.1669266, -122.4619747), (38.1669293, -122.4618467), (38.1669032, -122.4617393),
                     (38.1669760, -122.4616217), (38.1669041, -122.4614617), (38.1667604, -122.4613817), (38.1666526, -122.4614160),
                     (38.1666050, -122.4614811), (38.1662591, -122.4615463), (38.1658908, -122.4621221)],
             src='owner round-13 drive (owner_findings.md, Round 13 drive); 2026 clean captures c20_s3850..s4015 and round 13B survey '
                 'windows for the paving extents; lidar CA_NorthernCA_B22 ground (DEM) and bridge-deck (class 17) returns',
             why='the inactive paving, the islands and the course on one smooth surface (round 14A)'),
    ],
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
        # round 14B (judge r14a: the edge line along the drag-strip continuation toward T7 vanished under the draped zone;
        # the paint lines measured on the 2026 captures took their zone's centre height or the raw heightfield and lay
        # -0.45 .. +0.26 m off the driven surface): every ground mark's stored height on the package's own driven surface
        # after the terrain-override drape (tools/track/gates/groundMarks.ts), paint lines 0.008 m up as the edge lines
        marks_on_surface=dict(lift=0.008, src='round 14B, judge r14a regression (strip_continuation_to_T7)'),
        brake_board_corners=[],      # no brake boards in the 2026 onboard at T2 (0:09-0:12), T4 (0:28-0:33), T7a (1:09-1:12), T11 (1:52-1:57)
        corner_boards=False,         # no turn boards either ("Turn 1" / "Turn 7" are painted on the road in Street View)
        flagstand=False,             # no starter's stand over the pit wall at the line (onboard 2:16-2:19)
        pit_wall=dict(rule=False),   # every pit-side wall is declared below from the captures
        # the pit-exit cone line starts where the pit wall AT the edge ends (round 8, owner note 59: the wall is continuous
        # to its downstream end at s ~158, where the double yellow blend line starts), not at the pit-out lane's paddock-side
        # wall; the declared line (pit_exit_cones.latlon) sets it at Sonoma
        pit_exit_near_wall_only=True,
        # kerbs (round 7e, owner note 58: colour per strip from its frame, colour_src on each strip; T5 inside is plain
        # yellow): red / white painted concrete in 2026 at the corners the onboard shows (0:10 T2 entry, 0:13 T2, 0:24 T3,
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
                  palettes={'red': ['#b8433a', '#dedbd2'], 'blue': ['#5b7ea8', '#d9d8cf'], 'yellow': ['#c9a83e', '#c9a83e']},
                  # round 7e (owner note 58): every strip's colour and pattern from footage at that strip, with its frame
                  require_colour_src=True,
                  profile=dict(height=0.05, face=0.25, back=0.60)),
        # every strip: detected on the 2026 captures by compare/kerb_detect.py (block pattern) or seen on the straightened
        # strips (compare/capstrip.py), confirmed on the onboard; a, b = its ends on the edge (lat, lon)
        kerbs_declared=[
            dict(side='right', a=(38.1621761, -122.4558020), b=(38.1621947, -122.4559702), colors='red', off=0.3, name='T1 exit right, run 1 of the broken kerb',
                 colour_src="colour unverified: no frame (t002 / t004 do not resolve it; the owner's 2025 video at 0:17-0:19 looks past it)",
                 src='c20_s1870 (detector run 116.7-129.7, block pattern), feature note c20_s1925'),
            # T1 kerb blocks (round 4, owner note 31): the dotted line of low grey blocks between the two striped
            # sections on the outside, kind 'blocks' (drawn as blocks, no physics kerb); kerb_detect.py runs (grey, block
            # period ~1.9 m) confirmed on capstrip s 40-250. Round 8 (owner note 59): the inside 'block line from the
            # pit-wall nose' (s 88-133, c20_s1815 / c20_s1870) was the pit wall's K-rail segment tops, not kerb blocks;
            # that entry is gone and the wall runs on through it (round 9: 'pit straight, pit-lane side: K-rail from the island ...')
            dict(side='right', a=(38.1621947, -122.4559701), b=(38.1622059, -122.4563447), kind='blocks', off=0.6, name='T1 exit right, block line between the striped runs',
                 colour_src='colour unverified: no local frame (t002 / t004; grey blocks from the captures)',
                 src='c20_s1870 (kerb_detect grey run 143.7-149.7 and the dotted blocks from 130 to 161 between striped runs 1 and 3); owner_31 satellite'),
            dict(side='right', a=(38.1622058, -122.4563328), b=(38.1621982, -122.4565440), colors='red', off=0.3, name='T1 exit right, run 3',
                 colour_src="colour unverified: no frame (t004 / t006 behind or not resolved; the owner's 2025 video at 0:17-0:19 looks past it)",
                 src='c20_s1870 / c20_s1925 (detector 161.6-178.6, red)'),
            dict(side='right', a=(38.1621861, -122.4568047), b=(38.1621940, -122.4570057), colors='red', off=0.3, name='T1 exit right, run 4',
                 colour_src="colour unverified: no frame (t004 / t006 not resolved; the owner's 2025 video at 0:17-0:19 looks past it)",
                 src='c20_s1925 (detector 203.5-219.5)'),
            dict(side='left', a=(38.1616611, -122.4580486), b=(38.1613606, -122.4582911), colors='red', off=0.3, name='T2 entry, outside (owner_3)',
                 colour_src='t010: red / white blocks, left',
                 src='c20_s2090 / c20_s2035 blocks on the left edge (capstrip s300); onboard RAZip6S84CM 0:10 red/white kerb left on entry'),
            dict(side='left', a=(38.1609628, -122.459043), b=(38.1612976, -122.4597386), colors='red', off=0.3, name='T2 exit, outside (round 5)',
                 colour_src='t016: red / white blocks, left',
                 src='c20_s2200 / c20_s2255 (kerb_detect red runs 451.0-458.0 and 465.0-519.8, 91 % of the run, offsets -0.4..+1.0 m); onboard 0:16 long red/white kerb along the left after T2'),
            dict(side='right', a=(38.1612090, -122.4585461), b=(38.1610716, -122.4590163), colors='red', off=0.3, name='T2 apex',
                 colour_src='t014: red / white blocks, right',
                 src='c20_s2145 (detector 412.1-428.0, 436.0-451.0); onboard 0:13-0:14 red/white apex kerb right'),
            dict(side='right', a=(38.1619167, -122.4603232), b=(38.1622785, -122.4606472), colors='red', off=0.3, name='T3 approach, right',
                 colour_src="colour unverified: video shows no kerb at the mapped time (possible station offset): owner's May 2025 Radical onboard fEcQdo0ucL8 (checked by the orchestrator in his own tab, muted; frames not saved) 0:26 (11:33.27) shows plain grass and a white line on the right; t018-t022 resolve none; kept because c20_s2365 at 0.05 m/px shows a painted block pattern along the right edge over the detected run (kerb_detect 610.6-655.5)",
                 src='c20_s2365 (detector 610.6-655.5, red); onboard 0:20.6-0:21 kerb on the right'),
            dict(side='left', a=(38.1624585, -122.4609959), b=(38.1625770, -122.4615314), colors='red', off=0.3, name='T3 apex',
                 colour_src='t024: red / white blocks, left',
                 src='c20_s2420 / c20_s2475 blocks on the left edge (capstrip s600); onboard 0:24 red/white kerb left'),
            dict(side='right', a=(38.1626675, -122.4617129), b=(38.1627262, -122.4622560), colors='red', off=0.3, name='T3a apex (right; no kerb on the left of 3a)',
                 colour_src="owner's May 2025 Radical onboard fEcQdo0ucL8 (checked by the orchestrator in his own tab, muted; frames not saved) 0:33 (clock 11:33.34): red / white blocks, right",
                 src='c20_s2530 (detector 781.2-814.2) and blocks from 760 (capstrip s750)'),
            dict(side='left', a=(38.1629296, -122.4626566), b=(38.1637196, -122.4633060), colors='red', off=0.3, name='T4 entry, outside',
                 colour_src='t030 / t032: red / white blocks, left',
                 src='c20_s2585..s2750 blocks on the left edge (capstrip s750/s900); onboard 0:30-0:32 red/white kerb left'),
            dict(side='right', a=(38.1639939, -122.4633539), b=(38.1642332, -122.4631995), colors='red', off=0.3, name='T4 apex',
                 colour_src="t036: red / white blocks, right; owner's May 2025 Radical onboard fEcQdo0ucL8 (checked by the orchestrator in his own tab, muted; frames not saved) 0:36 (11:33.37): red / white blocks",
                 src='c20_s2750 (detector 995.8-1027.7, red); onboard 0:34-0:36 red/white apex kerb right'),
            dict(side='left', a=(38.1643028, -122.4633233), b=(38.1644968, -122.4625410), colors='red', off=0.3, name='T4 exit, outside',
                 colour_src='t038: red / white blocks, left',
                 src='c20_s2750..s2860 blocks on the left edge (capstrip s900/s1050); onboard 0:38 red/white kerb left'),
            dict(side='right', a=(38.1644932, -122.4618956), b=(38.1641441, -122.4607970), colors='yellow', pattern='plain', off=0.3, name='T5 apex and exit',
                 colour_src='t042: a plain yellow continuous strip on the right at the wall foot (sampled rgb 180, 175, 88 in the graded frame); owner note 58 (owner_58, May 2025 onboard fEcQdo0ucL8, reference only: plain yellow, rgb 182, 159, 95); #c9a83e between the two',
                 src='c20_s2860..s2970 (detector 1154.4-1165.4, 1182.3-1261.2, red)'),
            dict(side='left', a=(38.1629847, -122.4582212), b=(38.1634238, -122.4580951), colors='red', off=0.3, name='Carousel (T6) apex',
                 colour_src='t054 / t056: red / white blocks, left',
                 src='c20_s3355 / c20_s3410 (detector 1591.4-1646.3); onboard 0:55 red/white kerb left'),
            dict(side='right', a=(38.1640788, -122.4583265), b=(38.1644928, -122.4590012), colors='red', off=0.3, name='Carousel exit, right',
                 colour_src='t060: red / white blocks, right',
                 src='c20_s3465 / c20_s3520 (detector 1721.1-1796.0, red); onboard 0:60 red/white kerb right'),
            dict(side='right', a=(38.1660531, -122.4625071), b=(38.1663429, -122.4623758), colors='red', off=0.3, name='T7 island (apex)',
                 colour_src='t072: red / white blocks, right (island tip)',
                 src='c20_s3905 / c20_s3960 (detector 2172.1-2180.1, 2188.1-2201.1); satellite owner_9; onboard 1:12 red/white island kerb'),
            # round 11 (owner note 63: "not clear to me if this kerb should be here to block off the 'normal' T7 (just cones)"):
            # the strip started at s ~2213, before the mouth of the normal T7 (the paved area between the T7 island and the
            # O'Reilly island), so it ran 40-50 m across that open mouth; the captures show the blocks only round the
            # O'Reilly island from its nose (c20_s3960 / c20_s0000, compare/sonoma/round11/win_t7mouth.png), and onboard 1:14
            # (t074) shows the orange delineator posts across the mouth, no kerb: the strip now starts on the edge abreast of
            # the island's nose (s ~2264, the edge point 0.19 m from the first block); the posts (s 2196-2212) stay
            dict(side='right', a=(38.1667273, -122.4620163), b=(38.1664626, -122.4616350), colors='red', off=0.3, name="T7a island (O'Reilly)",
                 colour_src='t076: red / white blocks, right',
                 src='c20_s3960..s4070 (detector 2216.0-2223.0, 2324.8-2331.8; blocks along the island, capstrip s2250); onboard 1:16 red/white'),
            dict(side='left', a=(38.1667780, -122.4615777), b=(38.1662003, -122.4612627), colors='red', off=0.3, name='T7a exit, outside',
                 colour_src='t078: red / white blocks, left',
                 src='c20_s4015 / c20_s4070 / c20_s0000 (detector 2299.8-2309.8, 2315.8-2371.7); satellite owner_9 outer kerb'),
            dict(side='left', a=(38.1659810, -122.4609435), b=(38.1658234, -122.4606740), colors='red', off=0.3, name='T8 apex',
                 colour_src='t082: red / white blocks, left',
                 src='c20_s0055 (detector 2417.6-2440.5, red); onboard 1:18-1:20 red/white kerb left'),
            dict(side='right', a=(38.1657094, -122.4607681), b=(38.1652733, -122.4596928), colors='red', off=0.3, name='T8a apex',
                 colour_src='t084: red / white blocks, right (small, ahead)',
                 src='c20_s0055..s0165 (detector 2441.5-2447.5, 2479.4-2505.4, 2523.3-2537.3; blocks capstrip s2400); onboard 1:22-1:24'),
            dict(side='left', a=(38.1655429, -122.4598331), b=(38.1651945, -122.4594269), colors='red', off=0.3, name='T8a exit, outside',
                 colour_src='t086: red / white blocks, left',
                 src='c20_s0165 / c20_s0220 (detector 2542.3-2572.2); onboard 1:26 red/white kerb left'),
            dict(side='left', a=(38.1650454, -122.4591963), b=(38.1649276, -122.4587442), colors='red', off=0.3, name='T9 apex',
                 colour_src='t088: red / white blocks, left',
                 src='c20_s0220 / c20_s0275 (detector 2600.2-2645.1, red); onboard 1:28'),
            dict(side='right', a=(38.1648360, -122.4582215), b=(38.1646912, -122.4577513), colors='red', off=0.3, name='T9 exit, outside',
                 colour_src='t090: red / white blocks, right',
                 src='c20_s0330 / c20_s0385 (detector 2692.0-2739.8, red)'),
            dict(side='right', a=(38.1630881, -122.4552904), b=(38.1629460, -122.4551790), colors='red', off=0.3, name='9a chicane, right-hand part apex',
                 colour_src='t100: red / white blocks, right',
                 src='c20_o0660 (detector 3021.2-3036.2, red); onboard 1:39 kerb right'),
            dict(side='left', a=(38.1628061, -122.4550548), b=(38.1624095, -122.4542271), colors='red', off=0.3, name='9a chicane left-hand part apex and on to T10',
                 colour_src='t102 / t104: red / white blocks, left',
                 src='c20_o0715 / c20_s0715 / c20_s0770 (detector 3060.1-3169.9); onboard 1:41 red/white kerb left'),
            dict(side='right', a=(38.1622297, -122.4537575), b=(38.1618148, -122.4531362), colors='red', off=0.3, name='T10 apex',
                 colour_src="t108 / t110: red / white blocks, right; owner's May 2025 Radical onboard fEcQdo0ucL8 (checked by the orchestrator in his own tab, muted; frames not saved) 1:25-1:27 (11:34.26-28): continuous red / white along the right edge through T10 past the Toyota and Humboldt / Save Mart boards",
                 src='c20_s0825..s0935 (detector 3219.8-3292.6, red); onboard 1:45'),
            dict(side='left', a=(38.1614869, -122.4527961), b=(38.1609287, -122.4525711), colors='red', off=0.3, name='T10 exit, outside',
                 colour_src="colour unverified: video shows no kerb at the mapped time (possible station offset): owner's May 2025 Radical onboard fEcQdo0ucL8 (checked by the orchestrator in his own tab, muted; frames not saved) 1:27 (11:34.28) shows the board wall and a white line on the left; t110-t114 hidden or behind; kept because c20_s0990 at 0.05 m/px shows a painted block pattern along the left edge over the detected runs (3338.5-3402.4)",
                 src='c20_s0990 / c20_s1045 (detector 3338.5-3369.4, 3379.4-3402.4)'),
            dict(side='right', a=(38.1590671, -122.4520153), b=(38.1589844, -122.4525287), colors='red', off=0.3, name='T11 hairpin apex',
                 colour_src='t122 / t124: red / white blocks, right',
                 src='c20_s1265..s1375 (detector 3628.8-3673.7, 3700.7-3730.6; blocks capstrip s3600); onboard 2:01-2:04 red/white'),
        ],
        # walls OSM does not map, measured on the clean captures with compare/wall_measure.py (bright concrete top or
        # dark tyre stack, picked every 0.5 m across a guide, median 9 + Gaussian 3 m), every 10 m. Wall paint: light
        # blue in 2026 (onboard 0:03, 0:58-1:12, 1:56-2:19).
        declared_walls=[
            # round 8 (owner note 59, 20 Oct 2026: "I'm pretty sure the wall on the left side of the pit straight extends all
            # the way up to the red arrow and through the yellow line. Anything else would be extremely dangerous."): the
            # track / pit-lane separation wall is ONE continuous run from the front straight to its downstream end at s ~158,
            # where the double yellow blend line starts (pit_exit_cones / paint_lines_declared). There is no nose at s ~92 and
            # no painted block line after it: the "dotted block line s 88-133" on c20_s1815 / c20_s1870 is the K-rail's segment
            # tops (bright tops, dark joints), and s 134-158 is its solid section. Kind 'pitwall': from s ~94 the wall stands
            # AT the fitted edge (measured -0.2..0.0 m), so the push-out rule stands it at the pit-wall minimum + 0.05 m
            # (0.35 m, each point logged) instead of 0.55 m. Its only end near the merge is downstream (s ~158), which the
            # wall-ends gate does not check; its upstream end is the front-straight start (s ~3953)
            # round 9 (judge r8, K-rail stretch height): the same measured line as two runs joined end to end at the island
            # vertex (s ~85, where the island's pit-lane side line meets the track-side line and the segmented Jersey starts):
            # the front-straight wall s 3953-85 and the K-rail s 85-158. The 2017 lidar does NOT step there (DSM - DEM, 3 x 3 m
            # max every 2 m along the line: median 0.85 m on both stretches); the split is where the wall type changes on the
            # captures and in the pit video (t0296 a continuous wall, t0300 white Jersey segments with gaps). The Jersey run's
            # upstream end is joined to the front-straight run's downstream end (the same point), so the wall-ends gate
            # covers it without an allowance
            dict(name='pit straight, pit-lane side: front-straight wall to the island', kind='pitwall', h=1.1, fence=0.0, h_src='onboard 2:14-2:17: wall top level with the hood line at 2-3 m (SAFER-type ~1.1 m, Street View 5MY4xR9O7etAXEHnZCVnGQ ~1 m); no catch fence. Lidar 2017 DSM - DEM along the line (3 x 3 m max every 2 m, 115 samples): median 0.85 m (p25 0.83, p75 0.87), lower than the onboard reading and no step from the K-rail; round 10 (the orchestrator\'s reading, judge r9): the pit video 24of8fjjAug t0288 (the lane at the GEICO boards) shows the wall top at about a parked SUV\'s sill, ~1.0-1.1 m, so the lidar\'s 0.85 m median there is read as a ground-offset artefact on the lane side (the 3 x 3 m max over a cell whose DEM is the higher lane / track ground); 1.1 m kept', color=WALL_PALE_BLUE,
                 src='c20_s1595..s1870 bright band 2.0 m beyond the left edge (19 Oct), s 3953-76; round 8 (owner note 59): the pit-lane side line of the island converging to the track-side line (wall_measure.py along the left edge, offset 1.0-3.0 m, s 40-96: 92 % picked, rms 0.05 m; points s 79-85); round 9: ends at the island vertex s ~85, joined there to the K-rail run; onboard 2:16-2:20; 24of8fjjAug t0296 (a continuous wall on the right of the lane)',
                 latlon=[
                (38.1606469, -122.4535036), (38.1607541, -122.4536697), (38.1608652, -122.4538464),
                (38.1609772, -122.4540279), (38.1610893, -122.4542076), (38.1612006, -122.454387),
                (38.1613123, -122.4545663), (38.1614237, -122.4547457), (38.1615466, -122.4549429),
                (38.1616582, -122.455122), (38.1617703, -122.4553019), (38.1618793, -122.4554785),
                # round 8: the island's pit-lane side line converging (s 79-85)
                (38.1618922, -122.4554972), (38.1619034, -122.4555152), (38.1619144, -122.4555336), (38.1619249, -122.4555526)]),
            dict(name='pit straight, pit-lane side: K-rail from the island to the blend line', kind='pitwall', h=0.85, fence=0.0, h_src='lidar 2017 DSM - DEM along the line (3 x 3 m max every 2 m, 33 samples, s 85-157): median 0.85 m (p25 0.83, p75 0.89); 24of8fjjAug t0300: white Jersey segments with gaps, about the hood height (inventory pit row s 100: 0.9 m, jersey-ref); round 7f shadow on c20_s1815 ~0.8 m', color=WALL_PALE_BLUE,
                 src='round 8 (owner note 59: "I\'m pretty sure the wall on the left side of the pit straight extends all the way up to the red arrow and through the yellow line. Anything else would be extremely dangerous."): the wall at the edge from the island (s ~85, joined to the front-straight run) to the blend line start (wall_measure.py along the left edge, offset -0.6..1.0 m, s 90-158: 84 % picked, rms 0.05 m, p90 0.09 m, offset beyond the edge p50 -0.05 m; s 92-133 the K-rail segment tops 80 % picked, rms 0.15 m; s 134-158 the solid section 98 % picked, rms 0.03 m) to s ~158, 0.3 m from pit_exit_cones.latlon[0]; 24of8fjjAug t0300 (segmented Jersey from the island), pit row s 100 (Jersey segments curving with the track)',
                 latlon=[
                (38.1619249, -122.4555526),
                (38.1619515, -122.4555892), (38.1619667, -122.4556308), (38.1619791, -122.4556738), (38.1619895, -122.4557177),
                (38.1619984, -122.455762), (38.1620063, -122.4558067), (38.1620133, -122.4558516), (38.1620193, -122.4558968),
                (38.1620246, -122.4559421), (38.1620289, -122.4559875), (38.1620316, -122.4560332), (38.1620334, -122.4560789),
                (38.1620349, -122.4561246), (38.1620363, -122.4561703), (38.1620377, -122.456216), (38.1620387, -122.4562617),
                (38.1620393, -122.4562959)]),
            # round 9 (judge r8, pit-out catch fence): one wall, two runs joined end to end at the vertex s ~151: the low
            # chain-link along the pit-exit apron (s 106-151; 24of8fjjAug t0300 / inventory pit row s 100: the black steel
            # apron fence, low) and the catch fence from s ~151 to the wall's Jersey end (t0304 / inventory pit row s 160)
            dict(name='pit-out lane, paddock side', kind='concrete', h=1.0, fence=1.0, color=WALL_PALE_BLUE, h_src='onboard 2:22.5: low light-blue wall with a chain-link fence behind it along the pit-out lane; Street View owner_28 Pit Out (low white wall, chain-link fence beyond); round 5: the chain-link fence is 2.0 m to its top (inventory 0:06, fence-post-ref), so 1.0 m over the 1.0 m wall (was 2.0)',
                 src='c20_s1870 / c20_s1925, bright band along the lane outer side (wall_measure, 87 % picked, rms 0.30 m); onboard 2:23 / 0:06.5; round 9: its first 45 m (s 106-151), the low chain-link along the pit-exit apron (24of8fjjAug t0300: the low black steel fence round the apron, inventory pit row s 100), joined at s ~151 to the catch-fence run below',
                 latlon=[
                (38.1619153, -122.4557708), (38.161916, -122.4558863), (38.1619357, -122.455998),
                (38.1619491, -122.456111), (38.1619592, -122.4562246)]),
            dict(name='pit-out lane, paddock side: wall with the catch fence (round 9)', kind='concrete', h=1.0, fence=1.8, color=WALL_PALE_BLUE,
                 fence_arm=dict(len=0.5, deg=45.0),
                 h_src='wall 1.0 m as the run before it; catch fence measured against the wall face beneath each post (same depth, so the ratio holds): 24of8fjjAug t0304 (pit-out, reference only), nearest post at frame x ~180: wall face 82 px, the post 148 px above the wall top to its bend and 180 px to the top of its angled arm (1.8 x and 2.2 x); onboard RAZip6S84CM t006 (from the track, March 2026), post at x ~80: wall 26 px, 47 px to the bend, 52 px to the top (1.8 x, 2.0 x). Round 10: the vertical mesh 1.8 m over the 1.0 m wall (to the bend), then the angled arms (fence_arm, the kit option added in round 10): 0.5 m at 45 deg leaning toward the lane, the arm rising 0.39 m on t0304 (32 px over the 82 px face) and ~0.2 m on t006, tip ~3.15 m (round 9 drew a vertical 2.1 m to 3.1 m). The inventory reads 4.0 m (pit row s 160) and 2.0 m (t006 row s 184), both estimates; the frame ratios are the measurement',
                 src='c20_s1870 / c20_s1925, bright band along the lane outer side (wall_measure, 87 % picked, rms 0.30 m); onboard 2:23 / 0:06.5; round 9 (judge r8 row "pit-out catch fence"): from s ~151 to the Jersey end, the 3-4 m-class mesh catch fence with angled tops on the wall (24of8fjjAug t0304: mesh from the frame\'s left edge, beside the round red canopy, to the end of the lane; inventory pit row s 160 "catch fence on the wall, curved-top posts")',
                 latlon=[
                (38.1619592, -122.4562246), (38.1619666, -122.4563384), (38.1619792, -122.4564517), (38.1619856, -122.4565657),
                (38.1619903, -122.4566799), (38.1619944, -122.4567942), (38.1619986, -122.4568797),
                # round 5: on to its Jersey end before the footbridge (c20_s1925 / c20_s1980 wall_measure bright, 85 % picked,
                # rms 0.31 m; onboard 0:08 'the paddock-side wall of the pit-out lane ends here', Jersey end 5 m away)
                (38.1620017, -122.4569719), (38.1620076, -122.4570863), (38.1619978, -122.4572003), (38.1619769, -122.4573118),
                (38.1619426, -122.4574171), (38.1619172, -122.457483),
                ]),
            dict(name='T12 exit, right: L-shaped wall closing the drag strip mouth (round 7)', kind='concrete', h=1.1, fence=0.0, color=WALL_PALE_BLUE,
                 h_src='as the pit straight drag-strip side wall (onboard 2:14-2:17, ~1.1 m)',
                 src='c20_s1540: a light 1 m concrete band, L-shaped: 8 m along the right edge (s 3903-3910, wall_measure along the right edge, 54 % picked, rms 0.39 m) then across the drag strip to its NE side (wall_measure bright, 90 % picked, rms 1.03 m; vehicles parked behind it); round 5: onboard 2:14 the drag strip T12 mouth is behind the drag-strip wall; the pit straight drag-strip side wall starts 9 m on, 3 m out, lapped behind this head (owner note 39 rule)',
                 latlon=[(38.160394, -122.4528664), (38.160391, -122.4528951), (38.1603825, -122.4529276), (38.1603721, -122.4529595), (38.1603631, -122.4529919),
                         (38.1603547, -122.4530244), (38.1603465, -122.4530571), (38.1603479, -122.453067), (38.1603637, -122.4530791), (38.1603802, -122.4530884),
                         (38.1603972, -122.4530955), (38.1604103, -122.4530998)]),
            # round 7f left the s 134-158 pit-side wall out (as a short run its upstream end at s 134 failed the wall-ends gate);
            # round 8 (owner note 59) places it as the last section of the continuous pit-lane side wall above, so it has no
            # upstream end of its own
            # round 13 (owner note 136, 23 Oct 2026: on the start/finish straight the wall on the right "should stand right
            # against the painted edge line"; the ortho's white line runs the whole length where the wall base is, the model
            # stood back from it with a joggle). Measured on the package: the wall stood 1.2-2.5 m beyond the edge (p50
            # 2.23 m) with a 1.3 m step at s 4000-4008 (1.13 -> 2.44 m) and a 1.9 m step onto the drag-strip wall at s 77-82
            # (2.49 -> 0.55 m). On the clean captures the bright band (the line and the wall top) lies AT the fitted edge from
            # s ~3950 to the T1 kink (wall_measure --edge right: the bright band 0.06 m beyond the edge at s 4004-4098). The
            # wall is now the edge + 0.55 m (the barrier-gap minimum and its margin) from s 3950 to its end at s 77, blended
            # in over s 3926-3950 from the measured T12-exit line (2.1 m out at s 3926), where the captures show the drag
            # strip's mouth wall diverging from the edge; its head (s 3919-3926) stays joined to the L-shaped mouth wall.
            # The edge and the straight's painted width do not change.
            dict(name='pit straight, drag-strip side', kind='concrete', h=1.1, fence=0.0,
                 at_edge=dict(side='right', off=0.55, a=(38.1605166, -122.453247), b=(38.1606905, -122.4534063), c=(38.1619547, -122.4554186)), h_src='onboard 2:14-2:17: as the pit-lane side wall, ~1.1 m, no catch fence on it (the posts at 2:17 stand beyond the drag strip)', color=WALL_PALE_BLUE,
                 src='c20_s1595..s1870 bright band 2.3 m beyond the right edge (19 Oct); Street View 5MY4xR9O7etAXEHnZCVnGQ; onboard 2:17',
                 latlon=[
                # T12 exit to the timing line (c20_s1540 / c20_s1595, wall_measure along the right edge, 86 % picked, offset p50 1.7 m)
                (38.1604988, -122.4531009), (38.1605773, -122.4531593), (38.1606586, -122.4532076), (38.1607262, -122.4532828), (38.1607948, -122.453355), (38.1608526, -122.4534417), (38.1609081, -122.4535313), (38.160958, -122.4536264), (38.1610044, -122.4537248), (38.1610601, -122.4538148), (38.1611029, -122.4538595),
                (38.1611834, -122.4539958), (38.161300, -122.4541846), (38.161412, -122.4543637),
                (38.1615237, -122.4545429), (38.1616354, -122.4547222), (38.1617473, -122.4549012),
                (38.1618596, -122.4550797), (38.1619709, -122.4552587), (38.1620296, -122.4553516)]),
            dict(name='T6 to T7, left: black cushion section at the head of the wall (round 7)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 h_src='onboard 0:58 (t058): the black section stands about as high as the light concrete wall after it (~1 m)',
                 src='c20_s3410 / c20_s3465: wall_measure dark band at the end of the Carousel-exit asphalt, s 1684-1720, 7.8 m beyond the left edge angling in to the wall line (99 % picked, rms 0.82 m); onboard 0:58 (t058) a black cushioned section first, then the light grey concrete wall; t056 no wall; inventory row s 1687 "black wall section then light grey concrete wall"',
                 latlon=[(38.1636995, -122.4583088), (38.1637272, -122.4583114), (38.1637547, -122.4583170), (38.1637803, -122.4583295), (38.1638038, -122.4583474),
                         (38.1638294, -122.4583685), (38.1638528, -122.4583863), (38.1638759, -122.4584043), (38.1638994, -122.4584211), (38.1639239, -122.4584367),
                         (38.1639439, -122.4584531)]),
            dict(name='T6 to T7, left (Carousel exit along the drag strip and the T7 road)', kind='concrete', h=1.2, fence=0.0, h_src='onboard 1:09: light-blue wall a little above the hood line at 1-2 m (~1.2 m), ad boards on posts behind it (wall_boards)', color=WALL_PALE_BLUE,
                 src='c20_s3465..s3850 bright band at the asphalt end (wall_measure along the left edge, 83 % picked, rms 0.11 m, gaps bridged); onboard 0:58-1:12 light-blue wall, Toyota boards at 1:10',
                 # round 7 (owner note 41): the head s 1659-1720 dropped: it followed the painted edge line (wall_measure bright
                # 1656-1700 sits 0.15-0.3 m inside the fitted edge); t056 shows no wall there and t058 a black section first:
                # the run now starts where the measured black cushion meets it (s ~1720)
                cut='round 7: starts at s 1720 behind the black cushion section (see the tyres run at its head)',
                latlon=[
                (38.1639439, -122.4584531),
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
            dict(name='T7 approach, left tyre wall', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='c20_s3850 / c20_s3905 dark tyre stack 4-10 m beyond the left edge (96 % picked, rms 0.35 m); Street View gd1SNdksCq5QZtwlsrzR7g',
                 latlon=[
                (38.1655798, -122.4617596), (38.1656263, -122.4618583), (38.1656577, -122.4619656),
                (38.1656929, -122.4620707), (38.1657243, -122.4621779), (38.1657594, -122.4622831),
                (38.1657918, -122.4623896), (38.1658239, -122.4624963), (38.1658571, -122.4626024),
                ]),
            # round 7 (owner note 39): ONE run from before T5 to the crest. Was two runs ('T5, right: wall before the T5-T6
            # wall', c20_s2805 / s2860 dark line 99 %, rms 0.51 m, s 1062-1150; and this one from s 1149) whose joint stepped
            # 2.6 m toward the track: the downstream start's end face stood exposed. The joint s 1115-1192 re-measured across
            # the capture boundary (wall_measure dark, sguide 16.6 -> 11.5 m right, 100 % picked, rms 0.87 m; trailers parked
            # at the joint on c20_s2860); onboard 0:42-0:44 (t042 / t044) one continuous light-grey wall, no step.
            dict(name='T5 to the T6 crest, right', kind='concrete', h=1.0, fence=0.0, color=WALL_PALE_BLUE,
                 src='c20_s2805..s3080: s 1062-1112 dark line (99 % picked, rms 0.51 m), s 1115-1192 dark line re-measured across the capture boundary (100 %, rms 0.87 m), then the light wall line 3-6 m beyond the right edge (76 % picked); onboard 0:39-0:48.5 one continuous light concrete wall on the right (t042 / t044; not in the Jul 2011 Street View GMaTaipEd9Hm7fMNE26aGQ: built since)',
                 latlon=[
                (38.1642349, -122.4628430), (38.1642667, -122.4627355), (38.1642887, -122.4626247), (38.1643083, -122.4625131),
                (38.1643267, -122.4624011), (38.1643439, -122.4622888),
                (38.1643497, -122.4622479), (38.1643569, -122.4622031), (38.1643634, -122.462158), (38.1643695, -122.462113), (38.1643763, -122.4620682),
                (38.1643836, -122.4620235), (38.1643929, -122.4619792), (38.1644049, -122.4619361), (38.1644088, -122.46189), (38.1644119, -122.4618443),
                (38.1644162, -122.4618018), (38.1644211, -122.461757), (38.1644252, -122.4617117), (38.1644274, -122.4616661), (38.1644266, -122.4616201),
                (38.1644228, -122.4615745), (38.1644166, -122.4615292), (38.1644082, -122.4614846), (38.1644046, -122.461468),
                (38.1643726, -122.4613603),
                (38.1643394, -122.4612537), (38.1642991, -122.461151), (38.1642483, -122.4610561),
                (38.1641907, -122.460968), (38.1641318, -122.4608838), (38.1640675, -122.4608067),
                (38.1639972, -122.4607368), (38.1639247, -122.4606692), (38.1638527, -122.4606005),
                (38.1637802, -122.4605327), (38.1637077, -122.4604649), (38.1636327, -122.4604017),
                (38.1635576, -122.4603389), (38.163482, -122.4602772), (38.1634056, -122.4602168),
                (38.1633771, -122.4601993),
                ]),
            dict(name='T8a to T9, left (the bank)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='c20_s0110 / c20_s0165 dark barrier ~20 m left (99 % picked, rms 0.34 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA',
                 latlon=[
                (38.1658696, -122.4602454), (38.1658579, -122.4601295), (38.165808, -122.4600325),
                (38.1657583, -122.4599381), (38.1657083, -122.4598453), (38.165655, -122.4597548),
                (38.1655975, -122.4596672), (38.1655336, -122.4595876), (38.1654633, -122.4595172),
                (38.1653939, -122.4594453), (38.1653256, -122.4593708), (38.1652641, -122.459286),
                (38.1652155, -122.4592262),
                ]),
            dict(name='T9, left (the bank)', kind='concrete', h=1.0, fence=2.0, color=WALL_PALE_BLUE, h_src='round 5: catch fence 3.0 m to its top (inventory 1:28, fence-post-ref), so 2.0 m over the 1.0 m wall (was 3.0)',
                 src='c20_s0220 / c20_s0275 bright wall ~19 m left (95 % picked, rms 0.27 m); Street View xXQqyp9Q9sWv9ZLN2ORYsA (wall + catch fence on the bank)',
                 latlon=[
                (38.1652099, -122.4592275), (38.1651617, -122.4591306), (38.165111, -122.4590365),
                (38.1650715, -122.4589334), (38.165051, -122.4588218), (38.165043, -122.4587084),
                (38.1650435, -122.4585948), (38.1650446, -122.4584802), (38.165051, -122.4583666),
                (38.16505, -122.4582533), (38.1650495, -122.4582307),
                ]),
            # round 8 (owner notes 53, 60, 61): the 8a corner station's track-side wall, measured as ONE continuous wall from the
            # crossover road at 8a (s ~2515; the 'T8 to 8a, right' wall ends at s ~2510 on the far side of that road, so it is
            # not joined: gates.allowed lists the gap) along the paddock where the trailers park to its SE end ~6 m past the
            # tower (s ~2667). It replaces round 5's 'T9, right: concrete wall along the 2020 bypass' parts 1 / 2 (the same
            # wall, measured in two pieces with a 9 m gap at a parked trailer) and round 5's 'T8a, right' tyre line, which left
            # the dark band after s ~2550 and ran 3-5 m behind the wall in the grass (c20_s0220). The black tyre facing stands
            # on its track face where the captures show the black band and the onboard the black wall (two facings below).
            dict(name='T8a to T9, right: the 8a station wall along the paddock (round 8)', kind='concrete', h=1.0, fence=0.0, color=WALL_PALE_BLUE,
                 h_src='inventory t086 / t088: light grey / dark concrete wall 1.0 m (jersey-ref); lidar 2017 DSM - DEM along the measured line (3 x 3 m max, every 2 m): median 1.08 m, p25 1.02, p75 1.11 (the facing included)',
                 src='owner note 61 (tools/track/tracks/sonoma/owner/t8a_station.json: red line 1, "the dark line with its shadow", 34.7 m, s 2641-2667, 18.5-30.8 m right; drawn only near the tower, the wall continues NW); compare/wall_measure.py bright along the owner line (100 % picked, rms 0.03 m) and on along the wall NW to the 8a crossover road on c20_s0165 / c20_s0220 / c20_s0275: 166 m, 93 % of profiles picked, rms 0.06 m (search 0.6 m about the final line; the robust pass that set it: 99 % picked, 98 % kept within 0.4 m of a 15 m running median, rms 0.04 m; parked trailers rejected), s 2515 (20.3 m right) to s 2667 (30.7 m right) on the 8a-T9 pass, s 1922-1766 (34-48 m right) seen from the drag strip; onboard t084 (black facing ahead right), t086 (light grey wall begins, s ~2591), t088 (dark wall with a SONOMA TURN 8 sign, s ~2644); owner_52 (May 2025 onboard 1:14, reference only): the station behind the wall with a dark tyre facing in front of it',
                 latlon=[(38.1653836, -122.4600643), (38.1653631, -122.4600268), (38.1653423, -122.4599895), (38.1653211, -122.4599526),
                         (38.1653, -122.4599156), (38.1652784, -122.4598792), (38.1652568, -122.4598426), (38.1652356, -122.4598057),
                         (38.1652142, -122.4597689), (38.1651928, -122.4597322), (38.1651712, -122.4596957), (38.1651496, -122.4596593),
                         (38.1651276, -122.4596231), (38.1651054, -122.4595871), (38.1650829, -122.4595515), (38.1650604, -122.4595159),
                         (38.1650369, -122.4594813), (38.1650139, -122.4594462), (38.1649908, -122.4594112), (38.1649679, -122.459376),
                         (38.1649452, -122.4593406), (38.1649232, -122.4593044), (38.1649028, -122.4592669), (38.1648827, -122.4592289),
                         (38.1648639, -122.45919), (38.1648447, -122.4591514), (38.1648266, -122.4591119), (38.1648088, -122.4590722),
                         (38.1647914, -122.4590322), (38.1647737, -122.4589925), (38.1647563, -122.4589525), (38.1647398, -122.4589119),
                         (38.1647249, -122.4588703), (38.1647091, -122.4588292), (38.1646968, -122.4587863), (38.1646837, -122.4587438),
                         (38.1646713, -122.4587009), (38.1646591, -122.4586579), (38.1646469, -122.4586149), (38.1646349, -122.4585718),
                         (38.1646227, -122.4585288), (38.1646105, -122.4584859), (38.1646044, -122.4584644)]),
            dict(name='T8a, right: black tyre facing on the 8a station wall (NW part, round 8)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 h_src='lidar 2017 DSM - DEM along the wall (facing included): 1.0-1.1 m; inventory t084 "black-covered tyre barrier / dark panel wall" (1.3 m, jersey-ref, read high)',
                 src='c20_s0165 / c20_s0220: the black band on the wall\'s track face from the wall\'s NW end at the 8a crossover road to s ~2590 (compare/wall_measure.py dark along the wall + 0.9 m: 74 m, 99 % of profiles picked, rms 0.39 m; robust pass 89 % kept, rms 0.24 m; a 2026 trailer parked against the wall hides ~18 m at s ~2545-2560, the onboard t084 shows one continuous black wall); s 2515 (19.5 m right) to s 2590 (8.4 m right); snapped onto the wall\'s track face by tyre_facings',
                 latlon=[(38.1653873, -122.460054), (38.1653677, -122.4600156), (38.1653476, -122.4599777), (38.1653269, -122.4599404),
                         (38.1653053, -122.4599038), (38.1652835, -122.4598675), (38.1652617, -122.4598312), (38.1652388, -122.4597958),
                         (38.1652126, -122.4597637), (38.1651868, -122.4597311), (38.1651655, -122.4596945), (38.1651483, -122.4596538),
                         (38.165131, -122.4596131), (38.1651102, -122.4595758), (38.1650878, -122.45954), (38.165065, -122.4595046),
                         (38.1650419, -122.4594696), (38.1650185, -122.4594349), (38.1649961, -122.4593992), (38.1649855, -122.4593808)]),
            dict(name='T9, right: black tyre facing in front of the 8a station (round 8)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 h_src='inventory t088: dark wall 1.0 m (jersey-ref); lidar 2017 DSM - DEM along the wall: 1.0-1.1 m',
                 src='owner note 53 ("a white hut with a roof standing BEHIND the concrete wall ... with a dark tyre facing on the wall in front of it", owner_52, May 2025 onboard 1:14, reference only) and owner note 61 (red line 1: "the dark line with its shadow"); c20_s0275: the black band on the wall\'s track face along the owner\'s line (compare/wall_measure.py dark: 38 m, 100 % of profiles picked, rms 0.42 m; along the owner line itself 100 % picked, +0.60 m from the wall top); s 2636 (16.5 m right) to s 2665 (28.2 m right); onboard t088: dark wall with a SONOMA TURN 8 sign (the sign is not placed: no legible frame of it locally); snapped onto the wall\'s track face by tyre_facings',
                 latlon=[(38.1647374, -122.4588882), (38.164723, -122.4588464), (38.1647096, -122.4588039), (38.1646969, -122.4587612),
                         (38.1646841, -122.4587185), (38.1646725, -122.4586752), (38.1646634, -122.4586308), (38.1646539, -122.4585866),
                         (38.1646426, -122.4585432), (38.1646302, -122.4585003), (38.1646254, -122.4584843)]),
            # the T6-facing wall (owner note 61, red line 0: "the wall facing T6 runs all the way across the red line I drew
            # (protects the station from people losing control at T6)"): measured both ways along the owner's line until its
            # line ends on the captures: NW at the tower (0.8 m past the owner's drawn end; the 2017 lidar shows no wall in the
            # 14 m between it and the track-side wall), SE 125 m past the owner's drawn end to the paved area by the 2020
            # bypass. One continuous Jersey under the tower (no gap at the station; the tower's deck and roof stand over it)
            dict(name='T9 to the back straight, right: T6-facing Jersey under the 8a station (round 8)', kind='concrete', h=0.85, fence=0.0,
                 h_src='lidar 2017 DSM - DEM along the measured line (3 x 3 m max, every 2 m): median 0.84 m (p25 0.78, p75 0.91) over the owner\'s drawn part, 0.8-1.0 m over the SE extension (a 30 m stretch reads 2.8-3.0 m: vehicles parked against it in 2017), the tower block 3.8-4.1 m where it stands over the wall; a Jersey (0.81 m)',
                 src='owner note 61 (tools/track/tracks/sonoma/owner/t8a_station.json: red line 0, 48.8 m, bearing 304, fit 0.38 m rms, s 2652-2714 on the 8a-T9 pass = s 1781-1732 on the drag strip, 38-42 m right; the tower\'s centre 1.7 m from it); compare/wall_measure.py bright along the owner line and both extensions on c20_s0275 / c20_s0330 / c20_s0385 / c20_s3465 / c20_o0440: 179 m, 100 % of profiles picked, rms 0.05 m (search 0.6 m about the final line; robust pass 98 % kept, rms 0.04 m); s 2653 (28.7 m right, at the tower) to s 2864 (48.6 m right of the back straight), s ~1780 (37.9 m right) seen from the drag strip; colour unverified (light concrete top on the captures; no local frame shows its face)',
                 latlon=[(38.164612, -122.4586603), (38.1645911, -122.4586231), (38.1645725, -122.4585839), (38.1645562, -122.4585432),
                         (38.164538, -122.4585038), (38.1645178, -122.458466), (38.164497, -122.4584287), (38.1644762, -122.4583914),
                         (38.1644553, -122.4583543), (38.1644341, -122.4583173), (38.164413, -122.4582803), (38.1643919, -122.4582433),
                         (38.1643709, -122.4582063), (38.16435, -122.4581691), (38.1643291, -122.4581319), (38.1643081, -122.4580948),
                         (38.1642871, -122.4580578), (38.1642661, -122.4580206), (38.1642453, -122.4579834), (38.1642245, -122.4579461),
                         (38.1642037, -122.4579089), (38.1641829, -122.4578716), (38.1641617, -122.4578347), (38.1641402, -122.4577981),
                         (38.164119, -122.4577611), (38.1640985, -122.4577236), (38.164078, -122.4576862), (38.1640571, -122.4576491),
                         (38.1640361, -122.4576119), (38.1640151, -122.4575749), (38.1639939, -122.4575379), (38.1639728, -122.4575009),
                         (38.1639518, -122.4574639), (38.1639309, -122.4574267), (38.16391, -122.4573895), (38.1638891, -122.4573523),
                         (38.1638688, -122.4573146), (38.1638488, -122.4572767), (38.163829, -122.4572386), (38.1638097, -122.4572),
                         (38.1637911, -122.4571609), (38.1637732, -122.4571213), (38.163755, -122.4570819), (38.1637357, -122.4570433),
                         (38.1637155, -122.4570055), (38.1637003, -122.4569772)]),
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
            # round 13 (owner note 136): its head at s 77-88 at the edge + 0.55 m too, continuing the S/F wall with no joggle
            dict(name='drag strip, track (SW) side, past T1 to the Carousel exit', kind='concrete', h=1.0, fence=0.0, color=WALL_PALE_BLUE, drop_within=0.0,
                 at_edge=dict(side='right', off=0.55, a=(38.1619547, -122.4554186), b=(38.1619547, -122.4554186), c=(38.1620091, -122.4555231)),
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
            dict(name='drag strip, infield (NE) side', kind='concrete', h=1.0, fence=0.0, color=WALL_PALE_BLUE, drop_within=0.0,
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
            dict(name='T11 entry, left: outer pit-in wall (garage side)', kind='concrete', h=2.7, fence=0.0, color=WALL_PALE_BLUE, h_src='this is the OUTER pit-in wall (10.8 m left, beside the garage), not the track-side one; round 5: 5.2 m to the board top (HEIGHTS.md examples 3 and 4: Street View jrXpHaDfJT2APw6zcyBKRA 5.22 m, onboard 1:56 door-ref 5.0-5.6 m), the concrete face 2.7 m (it holds 2.03 m doors) under 2.5 m boards (wall_boards); was 1.2 m',
                 src='c20_s1210 / c20_s1265 bright line 10.8 m left (93 % picked, rms 0.05 m); onboard 1:59 red / white painted concrete on the left',
                 latlon=[
                # round 7 (owner note 37): re-measured to where the wall curves away behind T11 (wall_measure bright,
                # sguide s 3560-3655 at 10.3-17 m left, 83 % picked, rms 0.05 m, c20_s1210 / c20_s1265); the straight
                # round-5 line ended 1-3 m inside the lane where the real wall bends out (its end stood in the lane)
                (38.1595862, -122.4520093), (38.1595308, -122.4519856), (38.1594775, -122.4519625), (38.1594255, -122.4519400),
                (38.1593735, -122.4519176), (38.1593216, -122.4518949), (38.1592672, -122.4518714), (38.1592163, -122.4518490),
                (38.1591610, -122.4518250), (38.1591092, -122.4518023), (38.1590572, -122.4517802), (38.1590035, -122.4517582),
                (38.1589515, -122.4517375), (38.1588959, -122.4517173), (38.1588466, -122.4517025),
                ]),
            dict(name='T11 hairpin, left tyre wall', kind='tyres', color=TYRE_WHITE, h=0.8, stack=2, fence=2.2, h_src='round 7 (owner note 38): onboard 2:02-2:04 (t122 / t124) the white-wrapped stacks are two tyres high, 0.8 m (inventory, tyre-ref); the fence top stays 3.0 m; onboard 2:01.5-2:03.5: white tyre stacks ~1 m in front of the light-blue wall with a catch fence; round 5: fence top 3.0 m, between the 3.5 m catch fence at 2:02 and the 2.5 m chain-link at 2:04 (inventory, fence-post-ref; was 4.0)',
                 src='c20_s1265 / c20_s1320 white tyre band on the outside of the hairpin (69 % picked, rms 0.35 m); onboard 2:04 white tyre stacks left',
                 latlon=[
                (38.158888, -122.451793), (38.158799, -122.4517857), (38.1587102, -122.4518038),
                (38.1586262, -122.4518483), (38.1585597, -122.4519283), (38.1585112, -122.4520259),
                (38.1584808, -122.4521362), (38.1584838, -122.4522525), (38.1585119, -122.4523626),
                (38.1585634, -122.4524562), (38.1586344, -122.4525261), (38.1587172, -122.4525726),
                (38.1587582, -122.4525939),
                ]),
            dict(name='T3, right: low tyre-faced wall far out', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
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
            # round 13 (owner note 133: "The T4 wall seems set back, too. Note wall position vs. dark texture"): the wall stood
            # 1.8-3.4 m beyond the dark wall line at s 757-792 (s 776: wall 14.5 m out, capture band 11.1, ortho 12.1) and
            # 0.9-1.3 m at s 835-853; re-measured along the band (captures, dark, search 1.5 m: 72 % picked, rms 0.23 m, two
            # runs; over s ~785-826, where the band steps out 3 m round the stand's stair and the capture picks fall under the
            # contrast floor, the band measured on the package ortho: 72 % picked, rms 0.13 m)
            dict(name='T4 approach, left: wall and catch fence below the T3a-T4 stands', kind='concrete', h=1.0, fence=3.0, color=WALL_PALE_BLUE,
                 src='round 13: c20_s2475 / c20_s2530 wall_measure along the dark wall line, 72 % picked, rms 0.23 m (owner_133); was: c20_s2475..s2640 dark wall line 17-23 m left (97 % picked, rms 0.64 m); Street View nA1oaDXwADSI7x-Pa-j4Ow (wall + ~3 m catch fence left); onboard 0:28-0:32',
                 latlon=[(38.1624659, -122.4614208), (38.1624676, -122.4615123), (38.1624653, -122.4616038), (38.1624611, -122.461695), (38.1624547, -122.461786), (38.1624457, -122.4618769), (38.1624414, -122.4619682), (38.1624406, -122.461994), (38.1624378, -122.4620399), (38.1624361, -122.4620856), (38.1624342, -122.4621307), (38.1624335, -122.4621768), (38.1624359, -122.462223), (38.1624435, -122.4622679), (38.1624517, -122.4623124), (38.1624661, -122.4623543), (38.1624842, -122.4623939), (38.1625045, -122.4624316), (38.1625281, -122.4624661), (38.1625544, -122.4624973), (38.1625823, -122.4625224), (38.1626119, -122.4625472), (38.1626268, -122.4625597), (38.1626617, -122.4626016), (38.1627223, -122.4626506), (38.1627849, -122.4626955), (38.1628459, -122.462744), (38.162907, -122.4627922), (38.162968, -122.4628403), (38.1630099, -122.4628736)]),
            dict(name='T4, right: tyre line beyond the runoff', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='c20_s2640 / c20_s2695 dark tyre line 20-30 m right (79 % picked, rms 0.32 m)',
                 latlon=[
                (38.1629449, -122.462163), (38.1630084, -122.4622443), (38.1630649, -122.4623338),
                (38.1631408, -122.4623953), (38.1632225, -122.4624437), (38.1633035, -122.4624939),
                (38.1633815, -122.4625506), (38.1634589, -122.4626098), (38.1635328, -122.462675),
                (38.1636063, -122.4627406), (38.1636174, -122.4627504), (38.1637605, -122.4629255),
                (38.16382, -122.4630087), (38.1638613, -122.4630761),
                ]),
            dict(name='back straight, left: wall and catch fence at the foot of the stands', kind='concrete', h=1.0, fence=3.0, color=WALL_PALE_BLUE,
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
            dict(name='back straight start, left tyre line', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='c20_s0330 / c20_s0385 dark tyre line ~21 m left (78 % picked, rms 0.72 m)',
                 latlon=[
                (38.1650939, -122.4581954), (38.1650639, -122.4580853), (38.1650497, -122.4579728),
                (38.1650114, -122.4578695), (38.1649757, -122.4577658), (38.1649311, -122.4576678),
                (38.1648827, -122.4575726), (38.1648592, -122.4575312),
                ]),
            dict(name='T10 to T11, left wall with the ad boards', kind='concrete', h=1.2, fence=0.0, h_src='onboard 1:43-1:55: wall ~1.2 m under a continuous row of ~2.5 m ad boards (wall_boards); owner note 13/14 "much higher"', color=WALL_PALE_BLUE,
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
            dict(name='T10 to T11, right wall and catch fence', kind='concrete', h=1.1, fence=3.5, h_src='onboard 1:43.2-1:50: concrete ~1.1 m, catch-fence posts about three wall heights above it (~3.5 m)', color=WALL_PALE_BLUE,
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
            # round 13 (the run-gaps gate): its end stood 4.1 m short of the re-measured T2 wall's head (s ~413, 19 m left), the
            # dark band continuous between them on c20_s2145: it now ends on the wall's first point
            dict(name='T2 approach, far left: tyre line', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='2026 captures c20_s2090 / c20_s2145: wall_measure dark line, 92 % picked, rms 0.27 m; Street View H9xspk4q_OoFIjVDhaMzDA (tyre / armco line far left); onboard 0:12 low dark barrier far left',
                 latlon=[(38.1615844, -122.4577948), (38.1615100, -122.4578627), (38.1614389, -122.4579328), (38.1613691, -122.4580008), (38.1612978, -122.4580688), (38.1612243, -122.4581356), (38.1611504, -122.4582001), (38.1610760, -122.4582644), (38.1610046, -122.4583342), (38.1609319, -122.4584037), (38.1609059, -122.4584364), (38.1608722, -122.4584547)]),
            # round 13 (owner note 132, 23 Oct 2026: "Part of the T2 wall sits back from where it appears in the satellite
            # photo"): measured per station on the package ortho and the clean captures (the darkest 0.6-2 m band along the
            # track normal), the wall stood 2.9-4.7 m beyond the dark wall line at s 481-527 (s 499: wall 19.8 m out, ortho
            # band 15.1, capture band 15.6) and 1.2-2.5 m beyond it at s 414 / 536; re-measured along that band (wall_measure
            # --sguide on the band, dark, search 1.5 m, captures: 82 % picked, rms 0.33 m). The old line had locked on the
            # stands' foot behind it over the middle third
            dict(name='T2 exit, left: wall and catch fence at the foot of the T2 stands', kind='concrete', h=1.0, fence=3.0, color='#6f7a82',
                 src='round 13: c20_s2145 / c20_s2200 wall_measure along the dark wall line, 82 % picked, rms 0.33 m (owner_132); was: 2026 captures c20_s2145 / c20_s2200: wall_measure dark line, 97 % picked, rms 0.48 m; onboard 0:12-0:15.5 dark grey wall with catch-fence posts below the terraces',
                 latlon=[(38.1608722, -122.4584547), (38.1608072, -122.4584958), (38.1607781, -122.4585779), (38.1607711, -122.4586685), (38.1607612, -122.4587591), (38.1607601, -122.4588505), (38.1607622, -122.4589418), (38.1607718, -122.4590324), (38.1607892, -122.4591211), (38.1608124, -122.4592078), (38.1608431, -122.4592906), (38.160875, -122.4593725), (38.1609155, -122.4594479), (38.1609623, -122.4595173), (38.1610117, -122.4595836), (38.1610591, -122.4596523), (38.1611077, -122.4597196), (38.1611585, -122.4597843), (38.1612104, -122.4598474), (38.161262, -122.459911), (38.1613151, -122.4599727), (38.1613682, -122.4600343), (38.1614244, -122.4600915), (38.161428, -122.4600949)]),
            # round 13 (the run-gaps gate on the round-12 package): its end stood 7.9 m short of the T3 tyre wall's head (s ~596,
            # 25 m right) although "joins the T3 tyre wall at s 600"; c20_s2310 / c20_s2365 show the dark band continuous, so
            # the run now ends ON the T3 run's first point
            dict(name='T2 exit to T3, right: barrier line at the foot of the hill (owner_11)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='2026 captures c20_s2255 / c20_s2310: wall_measure dark line, 76 % picked, rms 0.41 m; owner_11 (the light band in the sim ground); onboard 0:12 dark barrier line far right, 0:18 barrier line along the right toward T3; joins the T3 tyre wall at s 600',
                 latlon=[(38.1613087, -122.4591967), (38.1613739, -122.4592754), (38.1614416, -122.4593507), (38.1615062, -122.4594303), (38.1615667, -122.4595146), (38.1616270, -122.4595999), (38.1616905, -122.4596811), (38.1617575, -122.4597574), (38.1618249, -122.4598330), (38.1618928, -122.4599079), (38.1619612, -122.4599821), (38.1619891, -122.4600113), (38.1620501, -122.4600578)]),
            dict(name='T5, left: tyre wall', kind='tyres', color=TYRE_BLACK, h=1.0, fence=1.5, h_src='round 5: chain-link fence behind the tyre stacks, 2.5 m to its top (inventory 0:36 / 0:38, fence-post-ref)',
                 src='2026 captures c20_s2805 / c20_s2860: wall_measure dark line, 96 % picked, rms 0.49 m; Street View zCwjltSjI02eDZGZbVyrMg (left low dark wall, tyres); onboard 0:39 dark barrier far left',
                 latlon=[(38.1648083, -122.4628124), (38.1647511, -122.4627218), (38.1647308, -122.4626081), (38.1646947, -122.4625013), (38.1646847, -122.4623865), (38.1646845, -122.4622722), (38.1646828, -122.4621581), (38.1646788, -122.4620444), (38.1646778, -122.4619303), (38.1646730, -122.4618174), (38.1646717, -122.4618062)]),
            dict(name='T5 to the T6 crest, left: wall and catch fence beyond the paddock', kind='concrete', h=1.0, fence=3.0, color='#5d6266',
                 src='2026 captures c20_s2970 / c20_s3080: wall_measure dark line, 100 % picked, rms 0.18 m; onboard 0:39-0:44 long low dark wall with catch fence far left',
                 latlon=[(38.1646874, -122.4608403), (38.1646360, -122.4607461), (38.1645828, -122.4606548), (38.1645317, -122.4605628), (38.1644772, -122.4604752), (38.1644168, -122.4603947), (38.1643505, -122.4603208), (38.1642841, -122.4602453), (38.1642147, -122.4601730), (38.1641425, -122.4601049), (38.1640681, -122.4600410), (38.1639945, -122.4599754), (38.1639190, -122.4599135), (38.1638407, -122.4598570), (38.1637615, -122.4598068), (38.1636782, -122.4597633), (38.1635930, -122.4597251), (38.1635126, -122.4596930), (38.1634263, -122.4596605), (38.1633402, -122.4596260), (38.1632538, -122.4595914), (38.1631673, -122.4595589), (38.1630828, -122.4595193), (38.1630006, -122.4594703), (38.1629308, -122.4594152)]),
            dict(name='Carousel, right: tyre-faced barrier across the infield', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='2026 captures c20_s3245 / c20_s3300: wall_measure dark line, 96 % picked, rms 0.32 m; Street View ma3jBYjtYGtNBlTLjNz1LQ (far right barrier, armco in Jul 2011); onboard 0:50 low dark barrier across the infield (2026: tyre-faced)',
                 latlon=[(38.1622039, -122.4588419), (38.1622255, -122.4587309), (38.1622553, -122.4586227), (38.1623030, -122.4585253), (38.1623564, -122.4584336), (38.1624127, -122.4583449), (38.1624782, -122.4582677), (38.1625456, -122.4581945), (38.1626151, -122.4581251), (38.1626880, -122.4580575), (38.1627618, -122.4579958), (38.1628388, -122.4579389), (38.1629189, -122.4578909), (38.1630010, -122.4578456), (38.1630843, -122.4578067), (38.1631693, -122.4577726), (38.1631736, -122.4577708)]),
            dict(name='Carousel, left: trackside fence', kind='fence', h=0.0, fence=2.0,
                 src='2026 captures c20_s3190 / c20_s3300: wall_measure dark line, 100 % picked, rms 1.12 m; Street View ma3jBYjtYGtNBlTLjNz1LQ (trackside fence far left); onboard 0:50 fence posts far left',
                 latlon=[(38.1628193, -122.4592713), (38.1627947, -122.4591583), (38.1627963, -122.4590400), (38.1628182, -122.4589248), (38.1628573, -122.4588192), (38.1629139, -122.4587269), (38.1629728, -122.4586395), (38.1630406, -122.4585575), (38.1631286, -122.4585162), (38.1632203, -122.4584975), (38.1632768, -122.4584977)]),
            dict(name='T8, left: tyre line up the bank (to the T8a-T9 tyres)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='2026 captures c20_s0000 / c20_s0055: wall_measure dark line, 99 % picked, rms 0.20 m; onboard 1:18.5 low dark line along the bank on the left; joins the T8a-T9 tyre wall',
                 latlon=[(38.1662930, -122.4607413), (38.1662218, -122.4606714), (38.1661547, -122.4605954), (38.1660895, -122.4605163), (38.1660270, -122.4604362), (38.1659724, -122.4603494), (38.1659225, -122.4602539), (38.1658914, -122.4601844)]),
            # round 11 (owner note 67, owner_67_missing_wall_dark_line.png: "Seems like there is a wall missing along this dark
            # texture line. Without it, there is a tire wall that abruptly starts, with an end that someone could smash into at
            # speed. As a general rule, the wall transition shown in the sim generally don't exist because they are extremely
            # dangerous"): the dark line converging across the verge onto the head of the T11-approach tyre wall is that wall:
            # concrete with its catch fence, the tyres standing in front of it at the edge
            # round 14B (owner, round-13 drive at T10: "I don't think this separate wall is sitting out by T10 ... Seems likely
            # that a section of wall is missing. I see a dark texture that looks like a missing tire wall"): round 11's line
            # began at (403.5, -139), 5.5 m inside the outer wall's line and 4.8 m from the edge, its head facing traffic
            # (passed by the wall-ends gate as 'tapered': 4.8 m out at the head, 3.3 m 10 m on). Re-measured on the
            # captures with a guide along the dark line the straightened strip shows (compare/capstrip.py s 3240-3420,
            # right): ONE line leaving the outer wall's line at s ~3324 and converging smoothly to the tyre wall's head at
            # the edge (s 3398), the "dark texture" the owner saw being that wall's own line in the ground image; the
            # round-11 picks between s 3335 and 3390 had run onto the parked trucks along its track side. Onboard t112: the
            # pale wall with its catch fence angling in across the grass toward the edge.
            dict(name='T11 approach, right: wall and catch fence onto the tyre wall (round 11)', kind='concrete', h=1.1, fence=3.5,
                 color=WALL_PALE_BLUE,
                 h_src='onboard RAZip6S84CM 1:52 (t112): the pale wall with its catch fence angling in across the grass toward the edge, '
                       'its top at the tyre stacks\' top (4 tyres, ~1 m) where it meets them at 1:54 (t114); as the T10-T11 wall (1.1 m, fence ~3.5 m)',
                 src='round 14B: 2026 captures c20_s0935 / c20_s0990 / c20_s1045: wall_measure dark line on the s-guide 3290-3398 (from the outer '
                     'wall\'s line, -18.7 m, to the tyre head, -7.4 m), 104 m, 99 % picked, contrast p50 78, rms 0.41 m; kept from s ~3324, '
                     'where it leaves the outer wall (run 28, 0.5 m away: joined), to the tyre wall\'s head (joined); the bright top '
                     '(97 % picked, rms 0.72 m) on the same line within 0.5-1 m; was round 11\'s (403.5, -139)..(425.9, -197.0), its '
                     'head 5.5 m inside this line (compare/sonoma/round11/win_3385.png)',
                 latlon=[(38.1614790, -122.4530847), (38.1614414, -122.4530526), (38.1614025, -122.4530230), (38.1613616, -122.4529994), (38.1613213, -122.4529738), (38.1612807, -122.4529496), (38.1612384, -122.4529301), (38.1611962, -122.4529102), (38.1611547, -122.4528886), (38.1611141, -122.4528646), (38.1610730, -122.4528415), (38.1610327, -122.4528164), (38.1609930, -122.4527897), (38.1609530, -122.4527638), (38.1609296, -122.4527463), (38.1609312, -122.4527310)]),
            dict(name='T11 approach, right: tyre wall and catch fence at the edge', kind='tyres', color=TYRE_BLACK, h=1.0, fence=3.5,
                 src='2026 captures c20_s1045 / c20_s1100: wall_measure dark line, 97 % picked, rms 0.53 m; onboard 1:53-1:55 tyre stacks along the right edge with catch fence (an ambulance parked behind at 1:54.6)',
                 latlon=[(38.1609312, -122.4527310), (38.1608446, -122.4527009), (38.1607590, -122.4526659), (38.1606736, -122.4526305), (38.1605876, -122.4525984), (38.1604991, -122.4525756), (38.1604404, -122.4525457)]),
            dict(name='9a, right: tyre wall', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0, cut='round 5: ends at s ~3132 where the dark tyre band ends on c20_s0715 / c20_s0770; the light concrete wall with its catch fence runs on from there (onboard 1:42-1:44)',
                 src='2026 captures c20_s0715 / c20_s0770: wall_measure dark line, 100 % picked, rms 0.53 m; onboard 1:42 tyre wall ahead right before the T10 wall',
                 latlon=[(38.1623750, -122.4551039), (38.1623515, -122.4549909), (38.1623267, -122.4548812), (38.1623041, -122.4547707), (38.1622884, -122.4547052)]),
            dict(name='T11 approach, left: outer pit-in wall (from the split)', kind='concrete', h=2.7, fence=0.0, color=WALL_PALE_BLUE, h_src='round 5: the same tall wall as the garage-side part (HEIGHTS.md examples 3 and 4, 5.2 m to the board top; onboard 1:56 shows its doors and a marshal at one): 2.7 m concrete under 2.5 m boards; was 1.2 m',
                 src='2026 captures c20_s1100 / c20_s1155: wall_measure bright line, 100 % picked, rms 0.30 m; Street View owner_15 (wall with ad boards along the pit-in lane, ~1 m wall); onboard 1:59 light-blue wall with ad boards behind the pit-in Jersey',
                 latlon=[(38.1602279, -122.4522589), (38.1601428, -122.4522222), (38.1600546, -122.4521985), (38.1599666, -122.4521740), (38.1598813, -122.4521374), (38.1597964, -122.4520999), (38.1597112, -122.4520635), (38.1596261, -122.4520267), (38.1595623, -122.4519992)]),
            dict(name='T10-T11 / pit-in outer wall: light-blue Jersey at its foot (round 7)', kind='concrete', h=0.9, fence=0.0, color=WALL_PALE_BLUE,
                 h_src='inventory 1:56 (t116): light-blue Jersey segments 0.9 m at the foot of the tall boarded wall (jersey-ref)',
                 src='onboard RAZip6S84CM 1:55-1:58 (t114 tyre bundles end, t116 / t118 the light-blue Jersey at the foot of the LAS VEGAS / O\'REILLY wall); the time anchor of round 6 (s 3468, Chrome captures 1:54.5-1:56.0) puts its start where the tyre bundles end; line: the declared outer walls (T10-T11 boarded wall, outer pit-in wall from the split; c20_s1100 / c20_s1155) offset 0.35 m into the lane, s 3468-3563 (the Jersey is not resolved separately on the captures: it stands against the wall)',
                 latlon=[(38.1603703, -122.4523280), (38.1603180, -122.4523069), (38.1602660, -122.4522816), (38.1602100, -122.4522555),
                         (38.1601536, -122.4522311), (38.1600957, -122.4522136), (38.1600375, -122.4521978), (38.1599793, -122.4521816),
                         (38.1599224, -122.4521593), (38.1598660, -122.4521348), (38.1598097, -122.4521100), (38.1597532, -122.4520857),
                         (38.1596968, -122.4520615), (38.1596403, -122.4520371), (38.1595839, -122.4520127), (38.1595613, -122.4520030)]),
            dict(name='T11 entry, left: Jersey wall between the track and the pit-in lane (from its nose)', kind='concrete', h=0.81, fence=0.0, color='#c9473e',
                 src='2026 captures c20_s1210 / c20_s1265: wall_measure bright line, 90 % picked, rms 0.15 m; owner_15 / owner_16 (wall between pit-in and track, nose with an impact barrier); onboard 1:59 red / white Jersey on the left; Jersey scale 0.81 m',
                 latlon=[(38.1593423, -122.4519695), (38.1592572, -122.4519328), (38.1591705, -122.4519022), (38.1590843, -122.4518703), (38.1589987, -122.4518373), (38.1589111, -122.4518114), (38.1588705, -122.4518113)]),
            dict(name='T11 hairpin, outside the pit road: outer wall (east)', kind='concrete', h=1.2, fence=0.0, color=WALL_PALE_BLUE,
                 src='2026 captures c20_s1265 / c20_s1320: wall_measure bright line, 71 % picked, rms 0.65 m; owner_18 (tall concrete wall on the outside of the pit-in lane); Street View jrXpHaDfJT2APw6zcyBKRA',
                 cut='round 7: starts at its second measured point, which lies 0.3 m from the re-measured garage-side wall (one wall); the first pick stood 2.5 m off that line (rms 0.65 m run)',
                 latlon=[(38.1589451, -122.4517340), (38.1588574, -122.4517030), (38.1587676, -122.4516937), (38.1586770, -122.4517000), (38.1586275, -122.4517082)]),
            dict(name='T11 hairpin, outside the pit road: outer wall (south) (part 1)', kind='concrete', h=1.2, fence=0.0, color=WALL_PALE_BLUE,
                 src='2026 captures c20_s1320: wall_measure dark line, 53 % picked, rms 0.51 m; owner_18 (tall concrete wall on the outside of the pit road behind the hairpin)',
                 latlon=[(38.1584146, -122.4517271), (38.1583969, -122.4518406), (38.1583891, -122.4518614)]),
            dict(name='T11 hairpin, outside the pit road: outer wall (south) (part 2)', kind='concrete', h=1.2, fence=0.0, color=WALL_PALE_BLUE,
                 src='2026 captures c20_s1320: wall_measure dark line, 53 % picked, rms 0.51 m; owner_18 (tall concrete wall on the outside of the pit road behind the hairpin)',
                 latlon=[(38.1583472, -122.4520171), (38.1583292, -122.4521300), (38.1583196, -122.4522436), (38.1583277, -122.4523591), (38.1583333, -122.4524733), (38.1583327, -122.4525882), (38.1583217, -122.4527018), (38.1583222, -122.4527076)]),
            dict(name='T2 entry, left: tyre wall before the footbridge (owner_27 / owner_28)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='2026 captures c20_s1980 / c20_s2035: wall_measure dark line, 90 % picked, rms 0.74 m; owner_27 ("there is a tire wall missing here"); Street View owner_28 Pit Out (Jul 2011): tyre wall round the outside of T2 from before the footbridge; onboard 0:12 dark low barrier left',
                 latlon=[(38.1618462, -122.4575074), (38.1618430, -122.4576228), (38.1618430, -122.4577255)]),
            # round 13 (owner note 131, 23 Oct 2026: "There is a gap in the tire wall on the other side of the bridge, right side of
            # circuit"): parts 1 and 2 (rounds 3-4) were one tyre line split by wall_measure where the footbridge deck and its
            # shadow cross it (a 13.5 m gap, s 306-318, 10-25 m right). c20_s1980 / c20_s2035 show one continuous black band
            # passing under the deck; re-measured as one run along the old two (wall_measure dark, search 2 m: 142 m guided,
            # 94 % picked, rms 0.50 m, shift from the old line p50 +0.09 m; the 8.5 m it does not pick, under the deck, joined). The run-gaps gate (round 13) now fails on such a gap.
            # Round 13 (owner notes 127 / 128: "Some of the T1 tire / concrete barriers are missing - I believe that's what this
            # gray / black texture across the grass is ... It starts to the left of the access road and goes up to where we have
            # some of it already in the model"): the run's head continues 42 m back up the paddock corner as the dark curved band
            # on the ortho (s ~200-224, 15-25 m right of the edge, from the access road at the stands' corner to the old head).
            # The z20 captures are label-masked there, so it is measured on the package ortho (wall_measure --ortho, dark,
            # search 2 m: 99 % picked, rms 0.21 m) and joined to the head of the re-measured run. Type and height as the run it
            # continues (black tyres, 1.0 m): the onboard frame owner_128 shows it as the same low black line
            dict(name='T1 exit to T2, right: tyre line on the grass bank (owner_28), one run under the footbridge (round 13)', kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0,
                 src='package ortho (round 13): the head from the access road, wall_measure --ortho dark, rms 0.21 m (owner_127 / owner_128); 2026 captures c20_s1980 / c20_s2035: wall_measure dark line, 94 % picked, rms 0.50 m (round 13, one run); Street View owner_28 Pit Out (tyre line on the grass bank to the right); owner_131',
                 latlon=[(38.1627176, -122.4570536), (38.1627084, -122.457013), (38.1626781, -122.4569886), (38.162644, -122.4569706), (38.1626086, -122.4569627), (38.1625706, -122.4569649), (38.1625363, -122.4569787), (38.162502, -122.4569927), (38.1624693, -122.4570143), (38.1624384, -122.4570378), (38.1624065, -122.4570634), (38.162393, -122.4570785), (38.1623951, -122.4570779), (38.1623773, -122.4571304), (38.1623387, -122.4572049), (38.1622854, -122.4572749), (38.1622602, -122.4573606), (38.1622426, -122.4574506), (38.1622231, -122.4575387), (38.162204, -122.4576269), (38.1621852, -122.4577151), (38.1621632, -122.4578021), (38.1621351, -122.4578863), (38.1621094, -122.4579719), (38.1620937, -122.4580616), (38.1620537, -122.4581376), (38.1620082, -122.4582084), (38.1619696, -122.4582858), (38.1619259, -122.4583588), (38.1618807, -122.4584305), (38.1618317, -122.4584985)]),
            # ---- round 5 (21 Oct 2026): the coverage gate's MISSING rows (compare/sonoma/coverage.md), each measured with
            # compare/wall_measure.py on the named 2026 captures (or derived where said) and tied to its inventory rows
            # round 13 (owner note 133: "...that wall should extend all the way down to the short shute area"): the wall stood
            # 0.6-1.6 m beyond the ortho's dark line at s 872-912 and 1.4-3.4 m at s 922-981, and ended at s 985, 17 m short
            # of the Chute's mouth. Re-measured on the package ortho (the captures' band is faint here: contrast 21-54; ortho
            # wall_measure --ortho --sguide, dark, search 1.5 m: 66 % picked, rms 0.22 m) and extended along the same line,
            # which turns north along the dirt / pavement boundary, to 1.0 m short of the Chute's paving at its mouth (s ~1000)
            dict(name='T4 approach, left: wall and catch fence on to the Chute (round 5)', kind='concrete', h=1.0, fence=2.5, color=WALL_PALE_BLUE,
                 h_src='round 13: package ortho wall_measure along the dark wall line, 66 % picked, rms 0.22 m, extended to 1 m short of the Chute paving (owner_133); was: inventory 0:30-0:34: light grey concrete wall 1.0 m (jersey-ref) with catch fence 3.5 m to its top (fence-post-ref)',
                 src='c20_s2695 / c20_s2750: wall_measure bright, s 876-985 beyond the measured T4 approach wall, 56 % picked (three runs, gaps under 16 m bridged), rms 0.31 m; onboard 0:32 wall and fence abeam, 0:34 its end at the Chute; Street View nA1oaDXwADSI7x-Pa-j4Ow',
                 latlon=[(38.1630057, -122.4628661), (38.1630671, -122.4629135), (38.1631284, -122.4629614), (38.1631908, -122.4630066), (38.1632519, -122.4630543), (38.1633147, -122.4630991), (38.1633779, -122.4631422), (38.1634372, -122.4631937), (38.1634974, -122.4632437), (38.1635587, -122.4632914), (38.1636195, -122.4633402), (38.1636808, -122.4633879), (38.163741, -122.4634376), (38.1638023, -122.4634855), (38.163863, -122.4635343), (38.1639247, -122.4635828), (38.1639952, -122.4636092), (38.1640616, -122.4635948)]),
            dict(name='T6 crest, right: Jersey on to the Carousel paved area (round 5)', kind='concrete', h=0.9, fence=0.0, color='#c9c9c4',
                 h_src='inventory 0:46-0:50: light grey concrete Jersey segments 0.9 m (jersey-ref)',
                 src='c20_s3135 / c20_s3190: wall_measure bright 1.0 m beyond the right edge, s 1358-1460, 96 % picked, rms 0.05 m; onboard 0:48 Jersey abeam on the right, 0:50 its end where the paved area opens',
                 latlon=[(38.1634226, -122.4602245), (38.1633499, -122.4601568), (38.1632764, -122.4600909), (38.1632014, -122.460028),
                         (38.1631256, -122.4599668), (38.1630498, -122.4599057), (38.1629731, -122.4598463), (38.1628974, -122.4597854),
                         (38.1628231, -122.4597217), (38.1627516, -122.4596522), (38.162684, -122.459575), (38.162658, -122.4595345)]),
            dict(name='drag strip NW end: far wall beyond the fork (round 5)', kind='concrete', h=1.0, fence=0.0, color=WALL_PALE_BLUE,
                 h_src='inventory 1:06: light blue concrete wall 1.0 m (jersey-ref)',
                 src='c20_s3685 / c20_s3740: wall_measure bright along the drag strip NW end, the third measured run only (s 2081-2100, 30-33 m right of the centre); onboard 1:04-1:06 (t064 / t066) the low white wall stands on the far side of the drag strip continuation, 30 m or more from the T7 road',
                 cut='round 7 (owner note 36): the round-5 line began at s 1885, 0.5 m beyond the right edge, on the drag strip\'s NE paint / concrete edge (the bright line c20_s3630 shows): t062 / t064 show grass right off that edge and no wall before the fork; the first two measured runs and the 69 m bridge between them are dropped, the third run (the wall the footage shows) kept',
                 latlon=[(38.165956, -122.4617028), (38.166008, -122.461796), (38.1660575, -122.4618781)]),
            # round 7e (owner note 57): the round-5 'tyre line across the continuation' (s 1934-1942) was a misread of t064; the
            # continuation is closed by a line of orange pylons (cone_lines_declared below, style 'delineator')
            dict(name='T7 approach, left: wall on to the T7 post (round 5)', kind='concrete', h=1.2, fence=0.0, color=WALL_PALE_BLUE,
                 h_src='as the T6 to T7 wall (onboard 1:09: ~1.2 m)',
                 src='c20_s3850 / c20_s3905: wall_measure bright, s 2104-2150, 63 % picked, rms 0.80 m (parked vehicles); onboard 1:12 the light blue-grey wall runs to its end beside the T7 post',
                 latlon=[(38.1657502, -122.4621356), (38.1657957, -122.4622344), (38.1658423, -122.4623324), (38.1658771, -122.4624379),
                         (38.1659144, -122.4625419), (38.1659438, -122.4626138)]),
            dict(name="the Chute's T7 mouth: tyre line behind the cones (round 5)", kind='tyres', color=TYRE_BLACK, h=0.6, fence=0.0,
                 h_src='inventory 1:12 (added row): low black tyre line, 0.6 m (tyre-ref)',
                 src='onboard RAZip6S84CM 1:12 (frame t072): two low black tyre lines with small orange cones across the paved Chute mouth ahead-left of T7, again far left at 1:14; placed 1.5 m behind the mouth cone line (the mouth from the OSM Chute way; c20_s3905 shows the mouth open at another event)',
                 latlon=[(38.1660984, -122.4628055), (38.1660851, -122.4627847), (38.1660717, -122.4627639), (38.1660584, -122.4627431),
                         (38.166045, -122.4627224), (38.1660317, -122.4627016)]),
            # round 7c (owner, item H): a MOVABLE Jersey line with a black tyre facing across the paddock pavement left of T7
            dict(name='T7, left: movable Jersey across the paddock pavement (round 7c, movable)', kind='concrete', h=0.9, fence=0.0, color='#e6e4de',
                 h_src='HEIGHTS.md Jersey 0.81-0.9 m; owner_54 shows a low white Jersey line', src='owner placement 20 Oct 2026 on the capture render (owner_53_T7_far_barrier_marked.png) + May 2025 onboard 1:02 (owner_54, reference only): MOVABLE, set out for road races, absent from the 2026 drag-season capture',
                 latlon=[(38.1666856, -122.4624694), (38.1663600, -122.4627744)]),
            dict(name='T7, left: black tyre facing on the movable Jersey (round 7c, movable)', kind='tyres', color=TYRE_BLACK, h=0.9, fence=0.0,
                 h_src='owner_54: black tyre facing as high as the Jersey', src='owner placement 20 Oct 2026 on the capture render (owner_53_T7_far_barrier_marked.png) + May 2025 onboard 1:02 (owner_54, reference only): MOVABLE, set out for road races, absent from the 2026 drag-season capture; placed on the Jersey line, the facing rule puts it on its track side',
                 latlon=[(38.1666856, -122.4624694), (38.1663600, -122.4627744)]),
            dict(name='T7, left: wall bounding the paved runoff below the T7a stands (round 5)', kind='concrete', h=1.0, fence=0.0, color='#e6e4de',
                 h_src='height not read (1.0 m default; the Street View row gives none)',
                 src='c20_s3960 / c20_s4015: wall_measure bright, 85 % picked, rms 0.57 m; Street View J6fsnW4hj4xCjQLzrgRGzA (concrete wall far left along the T7a stands)',
                 latlon=[(38.1668994, -122.4629129), (38.166845, -122.4628215), (38.1667931, -122.462728), (38.1667492, -122.4626282),
                         (38.1666955, -122.4625373), (38.1666442, -122.4624436), (38.1666416, -122.4624389)]),
            dict(name='T7a, left: tyre line at the foot of the terraces (round 5)', kind='tyres', color=TYRE_BLACK, h=0.8, fence=0.0,
                 h_src='inventory 1:14: black tyre wall line 0.8 m (tyre-ref)',
                 src='c20_s3960 / c20_s4015: wall_measure dark, 100 % picked, rms 0.39 m: the first 21 m of the line at the foot of the T7a terraces is a black tyre band (vehicles parked in front of it); onboard 1:14 black tyre wall line far left with recovery vehicles behind',
                 latlon=[(38.1668627, -122.4627568), (38.1668723, -122.4626432), (38.1668947, -122.4625312)]),
            dict(name='T7a, left: low wall at the foot of the terraces (round 5)', kind='concrete', h=0.8, fence=0.0, color='#e6e4de',
                 h_src='inventory 1:16: low white wall 0.8 m (jersey-ref)',
                 src='c20_s3960 / c20_s4015: wall_measure dark (its shadow line), 100 % picked, rms 0.39 m, the light part of the line at the foot of the T7a terraces; onboard 1:16 low white wall at the foot of the terraces',
                 latlon=[(38.1668947, -122.4625312), (38.1669342, -122.4624265),
                         (38.1669743, -122.4623242), (38.1670134, -122.4622213), (38.1670306, -122.4621747)]),
            dict(name='T7a to T8, left: tyre line at the foot of the bank (round 5)', kind='tyres', color=TYRE_BLACK, h=0.8, fence=0.0,
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
            dict(name='T8 to 8a, right: concrete wall to the PWC road (round 5)', kind='concrete', h=1.0, fence=0.0, color=WALL_PALE_BLUE,
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
            dict(name='back straight to 9a, left: wall and catch fence (round 5)', kind='concrete', h=1.0, fence=2.5, color=WALL_PALE_BLUE,
                 h_src='inventory 1:38-1:40: light concrete wall 1.0 m (jersey-ref), catch fence 3.5 m to its top (fence-post-ref)',
                 src='c20_o0660 / c20_s0660: wall_measure bright, s 2986-3046, 79 % picked, rms 0.58 m; onboard 1:38 wall and catch fence abeam on the left, 1:40 with Sonoma Raceway boards',
                 latlon=[(38.1635069, -122.455342), (38.1634471, -122.4552569), (38.1633834, -122.4551765), (38.1633219, -122.4550927),
                         (38.1632699, -122.4549987), (38.1631973, -122.454928), (38.1631105, -122.4548934), (38.1631062, -122.4548916),
                         (38.1630317, -122.4548843), (38.1629581, -122.4548937)]),
            dict(name='9a to T10, right: concrete wall and catch fence (round 5)', kind='concrete', h=1.1, fence=2.9, color=WALL_PALE_BLUE,
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
            dict(name='T10 to T11, left: tyre bundles at the foot of the boarded wall (round 5)', kind='tyres', color=TYRE_BLACK, h=0.6, fence=0.0,
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
        # round 6 (owner O3, approved quick version): the summer NAIP's dry grass shifted to the March green of the 2026
        # onboard, on the published ortho.jpg / far_ortho.jpg only, as the stage's last step (build_scenery.season_tint;
        # spec compare/sonoma/season_tint_mockup.py). Limits: ploughed fields go green too; one uniform green.
        season_tint=dict(enabled=True, green=(0.38, 0.47, 0.24), warm=(0.06, 0.20), bright=(0.25, 0.45), sat_max=0.55,
                         sat_soft=0.25, dark=0.88,
                         # round 11 (owner note 65: "the grass is not green, which seems to imply a feature is missing or a
                         # painted-on sign in the grass is missing"): the March 2026 onboard at T10 shows both verges green
                         # grass from the edge to the walls and no painted sign (RAZip6S84CM 1:44 t104, 1:46 t106, 1:50 t110);
                         # the summer NAIP's pale dry ground there escaped the tint (ortho (0.50-0.61, 0.51-0.62, 0.36-0.50),
                         # saturation 0.12-0.34): ground colour zones, the tint at full strength on the ground pixels
                         zones=[dict(side='right', s=(3140, 3330), off=(0.5, 12.0),
                                     src='onboard RAZip6S84CM 1:44-1:50 (t104, t106, t110): green grass right of T10 to the wall and catch fence'),
                                dict(side='left', s=(3140, 3260), off=(0.5, 12.0),
                                     src='onboard RAZip6S84CM 1:44-1:46 (t104, t106): green grass left of T10 to the boarded wall and its tyre bundles')]),
        # building heights from a robust lidar statistic (p60 above the footprint's ground; p50 where p90 - p50 > 6 m; no
        # structure above 2.5 m: dropped): the p85 rule made the main grandstand at the line a 25.6 m block (timing tower,
        # masts and the stand's slope inside the OSM outline). Laguna keeps the old rule (byte-identical package).
        building_height_robust=True,
        # evidence-declared building overrides (20 Oct 2026, round 4): only where a newer source contradicts the 2022-24
        # lidar (precedence: recent onboard > 2026 satellite > NAIP > OSM > lidar); each use is logged by the build
        building_overrides=[
            dict(osm='1019835273', plain=True,
                 src='round 6 (orchestrator S2): the long flat-roofed shed east of the T10-T11 straight (4.4-5.0 m, lidar 2022-24) '
                     'drew with two rows of office windows over the boarded wall; the onboard 1:52-1:58 (t112-t118) shows no '
                     'storeys or glazing above the boards, and c20_s1100 / c20_s1155 / c20_s1210 a plain light roof: plain walls'),
            dict(osm='1019838438', drop=True,
                 src='T11 approach, 1-6 m right of the right edge at s 3414-3440: the lidar (2022-24) has a ~12.5 m structure; '
                     'the 2026 capture c20_s1045 shows a temporary white hospitality tent (~8 x 30 m) on part of the outline; the '
                     'March 2026 onboard RAZip6S84CM 1:53-1:55.6 shows neither: tyre stacks and catch fence at the edge, an '
                     'ambulance and low cabins behind them, then open paved infield. The onboard is the newest source, so no '
                     'building stands here'),
        ],
        # OSM walls the evidence re-kinds or drops (round 5): OSM notes both T3 / T4 lines as 'tire barrier'
        osm_barrier_overrides={
            '380830042': dict(kind='tyres', color=TYRE_BLACK, h=1.0, fence=0.0, src='T3 right, OSM note "tire barrier": c20_s2475 / c20_s2530 show the dark tyre band on this line, 37-47 m right of the centre (round 5)'),
            '380830043': dict(drop=True, src='T4 right: the same tyre line as the measured declared wall "T4, right: tyre line beyond the runoff" (c20_s2640 / c20_s2695, within 1-2 m of it), OSM note "Tire barrier" (round 5)'),
        },
        # the evidence for the buildings the coverage gate checks (round 5): kept with their capture / onboard source, or
        # removed where neither the 2026 captures nor the onboard show them
        building_evidence=[
            dict(contains=(38.1617509, -122.456482), src='c20_s1870: the red-roofed metal pit-exit building (onboard 0:04 and 24of8fjjAug 5:00 red-roofed pit-exit building)'),
            dict(contains=(38.1603944, -122.4579624), src='onboard 0:14 (frame t014): open shade roof on posts at the top of the T2 terraces (inventory row added in round 5)'),
            dict(contains=(38.1615502, -122.4535441), src='c20_s0935: the flat-roofed 21 x 22 m infield building (grey roof, vehicles at its east side) 42-62 m right of s 3290-3320; lidar 3.2-3.5 m; onboard 1:52 (frame t112): a small grey building with a window beyond the fence at the right edge (round 6)'),
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
        # hillside terraces (round 6): footprints MEASURED on the 2026 captures (compare/terrace_measure.py ray mode: the row
        # texture's lower and upper edge per ray, the DEM crest less 3 m where the captures end), not OSM: the OSM outlines
        # cut straight rows across curved banks (20-36 % of the tread buried in the terrain, the rest floating up to 3.7 m)
        # and ran over the road and trees past s 3030 (back straight). `osm` marks the slab the terrace replaces and fills
        # the rays at a stand's end where the captures stop below the bank's crest (terrace_measure.py --fill-osm; 15 rays
        # at T2's near end, 19 at T7a's east end, 4 at T3a, 5 on the back straight; listed per ray in the tool's JSON).
        terraces=[
            dict(name='T7a hill', osm='1414701937', run=1.1,
                 src='measured footprint (round 6): compare/terrace_measure.py --thr 0.35 --guide xy:-480,462;-452,464;-420,471;-390,481;-370,495;-355,510 (the curved low wall below the stand on capwin.py) --reach 80 --fill-osm 1414701937: the row texture (period 1.1-1.25 m) on c20_s3960 / c20_s4015 (lower rows; the upper part is outside the captures: DEM crest - 3 m); row pitch 1.11 m on the rays; Street View J6fsnW4hj4xCjQLzrgRGzA (terraces, fence and light masts on top); onboard 1:12-1:14',
                 front=[(38.166979, -122.462924), (38.1669809, -122.4628898), (38.1669739, -122.4628548), (38.1669758, -122.4628206), (38.1669683, -122.4627915), (38.1669672, -122.4627659), (38.1669724, -122.4627355), (38.1669782, -122.4627021), (38.1669839, -122.4626686), (38.1669897, -122.4626351), (38.1669998, -122.4626028), (38.16701, -122.4625706), (38.1670245, -122.4625395), (38.1670303, -122.462506), (38.1670448, -122.462475), (38.1670538, -122.4624488), (38.167064, -122.4624261), (38.1670719, -122.462396), (38.1670847, -122.4623653), (38.1670975, -122.4623346), (38.1671102, -122.4623039), (38.1671188, -122.4622713), (38.1671315, -122.4622406), (38.1671401, -122.4622081), (38.1671486, -122.4621756), (38.1671574, -122.4621486), (38.1671582, -122.4621425), (38.1671642, -122.4621339), (38.1671783, -122.4621046), (38.1671937, -122.4620765), (38.1672092, -122.4620484), (38.1672246, -122.4620204), (38.1672401, -122.4619923), (38.1672552, -122.4619648), (38.1672628, -122.4619502), (38.1672733, -122.4619377), (38.1672924, -122.4619135), (38.1673114, -122.4618892), (38.1673305, -122.461865), (38.1673495, -122.4618408), (38.1673686, -122.4618165)],
                 back=[(38.1670521, -122.4629306), (38.167054, -122.4628964), (38.167076, -122.4628641), (38.1671272, -122.4628343), (38.1671458, -122.4628182), (38.1671736, -122.4628163), (38.167255, -122.4628142), (38.1672651, -122.4627819), (38.1672709, -122.4627484), (38.1672767, -122.4627149), (38.1672842, -122.4626819), (38.1672978, -122.4626506), (38.1673097, -122.4626189), (38.1673225, -122.4625873), (38.1673353, -122.4625558), (38.1673408, -122.4625435), (38.1673431, -122.4625387), (38.1673506, -122.4625141), (38.1673633, -122.4624834), (38.1673727, -122.4624513), (38.1673846, -122.4624202), (38.1673991, -122.4623902), (38.1674085, -122.4623581), (38.1674187, -122.4623263), (38.1674298, -122.4622948), (38.1674362, -122.4622772), (38.1674194, -122.462321), (38.1674071, -122.4623502), (38.1674219, -122.4623215), (38.1674322, -122.4622888), (38.1674439, -122.4622574), (38.1674542, -122.4622248), (38.1674587, -122.4621869), (38.1674732, -122.4621605), (38.1674665, -122.4621693), (38.1674588, -122.4621736), (38.167474, -122.4621445), (38.1674855, -122.4621106), (38.1674969, -122.4620767), (38.1675064, -122.4620403), (38.1675172, -122.4620056)]),
            dict(name='T3a-T4', osm='1414701938', run=1.25,
                 src='measured footprint (round 6): compare/terrace_measure.py --thr 0.35 --side left --s0 740 --s1 1010 --guide-lat 20 --fill-osm 1414701938: the row texture (period 1.1-1.25 m) on c20_s2530..c20_s2695 (the whole field, top walkway and fence captured); row pitch 1.25 m on the rays; Street View nA1oaDXwADSI7x-Pa-j4Ow (~20 concrete rows); onboard 0:26-0:32',
                 front=[(38.1622291, -122.461944), (38.162277, -122.4619849), (38.1623197, -122.462023), (38.162322, -122.462062), (38.1623253, -122.4621013), (38.1623299, -122.4621407), (38.162336, -122.4621801), (38.1623479, -122.4622177), (38.1623568, -122.4622562), (38.1623672, -122.4622941), (38.1623789, -122.4623314), (38.1623719, -122.4623804), (38.1623829, -122.4624199), (38.1623991, -122.4624557), (38.1624091, -122.4624968), (38.1624277, -122.4625307), (38.1624474, -122.4625635), (38.1624678, -122.4625948), (38.1624954, -122.462617), (38.16252, -122.4626415), (38.1625417, -122.4626687), (38.1625667, -122.4626906), (38.1625948, -122.462707), (38.1626171, -122.4627309), (38.1626395, -122.4627541), (38.162662, -122.4627766), (38.16269, -122.4627895), (38.1627126, -122.4628108), (38.1627379, -122.462827), (38.1627606, -122.4628475), (38.1627859, -122.4628629), (38.1628087, -122.4628827), (38.1628316, -122.4629023), (38.1628569, -122.4629168), (38.1628797, -122.4629359), (38.162905, -122.4629501), (38.1629302, -122.462964), (38.162953, -122.4629827), (38.1629758, -122.4630013), (38.163001, -122.463015), (38.1630238, -122.4630334), (38.1630465, -122.4630518), (38.1630596, -122.4630895), (38.1630823, -122.4631079), (38.163105, -122.4631263), (38.1631373, -122.4631255), (38.1631647, -122.4631343), (38.1631946, -122.4631384), (38.1632172, -122.4631569), (38.1632397, -122.4631755), (38.1632622, -122.4631941), (38.1632823, -122.4632176), (38.1633048, -122.4632364), (38.1633274, -122.4632552), (38.1633549, -122.4632644), (38.1633775, -122.4632831), (38.1634051, -122.4632923), (38.1634278, -122.4633109), (38.1634456, -122.4633391), (38.1634635, -122.4633673), (38.1634862, -122.4633858), (38.1635088, -122.4634042), (38.1635288, -122.4634274), (38.1635486, -122.4634507), (38.1635707, -122.4634693), (38.1635901, -122.4634929), (38.163612, -122.463512), (38.163634, -122.4635314), (38.1636537, -122.4635558), (38.1636739, -122.4635803), (38.1636949, -122.463605), (38.1637191, -122.4636248), (38.1637442, -122.463644), (38.1637702, -122.4636625), (38.1637972, -122.4636799), (38.163825, -122.4636959), (38.1638536, -122.4637105), (38.1638709, -122.4637723)],
                 back=[(38.1621492, -122.4619423), (38.1621563, -122.4619872), (38.162162, -122.462033), (38.1621698, -122.462079), (38.1621756, -122.4621258), (38.1621812, -122.4621734), (38.1621974, -122.4622189), (38.1622065, -122.4622662), (38.1622174, -122.4623131), (38.1622166, -122.4623658), (38.1622188, -122.4624188), (38.1622346, -122.4624654), (38.1622457, -122.4625152), (38.1622655, -122.4625589), (38.1622829, -122.4626041), (38.1623088, -122.4626414), (38.1623321, -122.4626801), (38.1623595, -122.4627133), (38.1623904, -122.4627402), (38.1624246, -122.4627609), (38.1624491, -122.4627916), (38.1624737, -122.4628208), (38.1624895, -122.4628615), (38.1625143, -122.4628882), (38.162539, -122.4629138), (38.1625635, -122.4629383), (38.1625906, -122.4629575), (38.1626202, -122.4629711), (38.1626469, -122.4629887), (38.1626708, -122.4630102), (38.1626947, -122.4630313), (38.1627185, -122.463052), (38.1627421, -122.4630723), (38.1627657, -122.4630922), (38.1627867, -122.4631166), (38.1628076, -122.4631407), (38.1628284, -122.4631647), (38.1628468, -122.4631933), (38.1628408, -122.4632698), (38.1628638, -122.4632885), (38.1628867, -122.4633071), (38.1629095, -122.4633255), (38.1629322, -122.4633439), (38.1629548, -122.4633623), (38.1629749, -122.4633853), (38.1629949, -122.4634083), (38.1630171, -122.4634265), (38.1630381, -122.463447), (38.163059, -122.4634676), (38.1630787, -122.4634907), (38.163091, -122.4635281), (38.1631132, -122.4635466), (38.1631356, -122.4635652), (38.1631483, -122.4636032), (38.1631614, -122.4636413), (38.1631845, -122.4636605), (38.1632078, -122.4636797), (38.1632384, -122.4636845), (38.1632666, -122.4636939), (38.1632897, -122.4637127), (38.1633123, -122.4637311), (38.1633343, -122.4637491), (38.1633581, -122.4637619), (38.1633812, -122.4637742), (38.1634038, -122.4637864), (38.1634238, -122.4638036), (38.1634441, -122.4638213), (38.1634705, -122.4638307), (38.1634959, -122.4638462), (38.1635232, -122.4638632), (38.1635503, -122.4638862), (38.1635798, -122.4639101), (38.1636116, -122.4639345), (38.163646, -122.4639589), (38.1636709, -122.4640134), (38.1637107, -122.4640364), (38.1637681, -122.4640041), (38.163819, -122.4639839)]),
            dict(name='above T2', osm='1414701939', run=1.15,
                 src='measured footprint (round 6): compare/terrace_measure.py --thr 0.35 --side left --s0 400 --s1 600 --guide-lat 25 --fill-osm 1414701939: the row texture (period 1.1-1.25 m) on c20_s2090..c20_s2255 (lower two thirds; above, the DEM crest - 3 m); row pitch 1.17 m on the rays; Street View H9xspk4q_OoFIjVDhaMzDA; onboard 0:14-0:16 (rows from the catch fence at the foot of the bank, fence and light poles on top)',
                 front=[(38.1607126, -122.4586454), (38.160708, -122.4586849), (38.1607034, -122.458724), (38.1606989, -122.458763), (38.1606997, -122.4588028), (38.1607004, -122.4588421), (38.1606984, -122.4588809), (38.1606977, -122.4589198), (38.1606982, -122.4589587), (38.1607, -122.4589975), (38.160703, -122.4590361), (38.1607072, -122.4590745), (38.1607127, -122.4591125), (38.1607192, -122.4591502), (38.1607269, -122.4591875), (38.1607356, -122.4592242), (38.1607454, -122.4592603), (38.1607518, -122.459298), (38.1607634, -122.4593331), (38.1607758, -122.4593675), (38.1607928, -122.4593986), (38.1608063, -122.4594314), (38.1608204, -122.4594636), (38.1608349, -122.4594952), (38.1608422, -122.4595322), (38.1608574, -122.4595628), (38.1608729, -122.4595929), (38.1608886, -122.4596225), (38.1609044, -122.4596518), (38.1609205, -122.4596808), (38.1609367, -122.4597096), (38.1609531, -122.4597381), (38.1609697, -122.4597665), (38.1609937, -122.4597877), (38.1610142, -122.4598122), (38.161035, -122.4598364), (38.1610524, -122.4598639), (38.16107, -122.4598911), (38.161088, -122.4599182), (38.1611129, -122.4599375), (38.1611345, -122.4599601), (38.1611629, -122.4599747), (38.1611814, -122.4600005), (38.1612001, -122.460026), (38.1612189, -122.4600512), (38.1612378, -122.4600763), (38.1612568, -122.4601011), (38.1612279, -122.460186), (38.1612186, -122.4602471), (38.1612348, -122.4602758), (38.1612384, -122.4603207), (38.1612515, -122.4603533), (38.1612647, -122.4603858), (38.1612716, -122.4604265), (38.1612818, -122.4604632), (38.1613014, -122.4604875), (38.1612931, -122.4605489)],
                 back=[(38.1604382, -122.4585411), (38.1604268, -122.4585937), (38.160417, -122.4586468), (38.1604394, -122.458707), (38.1604484, -122.458762), (38.1604569, -122.4588155), (38.1604651, -122.4588677), (38.1604732, -122.4589188), (38.1604811, -122.458969), (38.160489, -122.4590186), (38.1604928, -122.459068), (38.1604982, -122.4591171), (38.1604485, -122.4591802), (38.1604547, -122.4592317), (38.1604598, -122.4592834), (38.1604706, -122.4593329), (38.1604834, -122.4593807), (38.1604366, -122.4594584), (38.1604442, -122.459511), (38.1604584, -122.4595589), (38.160474, -122.4596045), (38.1604918, -122.4596476), (38.1605099, -122.459689), (38.1605273, -122.4597291), (38.1605447, -122.4597676), (38.1605629, -122.4598041), (38.1605802, -122.4598399), (38.1605982, -122.4598739), (38.1606161, -122.459907), (38.1606978, -122.4598819), (38.1607264, -122.4599032), (38.1607514, -122.4599273), (38.1607693, -122.459958), (38.1607876, -122.4599885), (38.160792, -122.4600331), (38.160811, -122.4600638), (38.1608303, -122.4600942), (38.1608464, -122.460128), (38.1608307, -122.4601966), (38.1608512, -122.4602269), (38.1608718, -122.4602567), (38.1608939, -122.4602846), (38.1609186, -122.4603088), (38.160942, -122.460334), (38.1609789, -122.4603421), (38.1610188, -122.4603454), (38.1610422, -122.4603679), (38.1610623, -122.4603939), (38.1610823, -122.4604196), (38.1611022, -122.4604449), (38.1611251, -122.4604658), (38.1611416, -122.4604947), (38.161155, -122.4605275), (38.161159, -122.4605726), (38.1611789, -122.4605972), (38.1611987, -122.4606218), (38.16125, -122.4606055)]),
            dict(name='back straight / 9a', osm='1414701936', run=1.15,
                 src='measured footprint (round 6): compare/terrace_measure.py --thr 0.35 --side left --s0 2690 --s1 3070 --guide-lat 18 --fill-osm 1414701936: the row texture (period 1.1-1.25 m) on c20_o0440..c20_o0550, c20_s0605 (the whole field; it ends at s ~3030 where the access road and trees begin); row pitch 1.15 m on the rays; Street View xkSrqJ5RaN9WFLncaiqaug; onboard 1:30-1:36',
                 front=[(38.1651939, -122.457662), (38.1651795, -122.4576245), (38.1651645, -122.4575876), (38.1651449, -122.457554), (38.1651288, -122.4575183), (38.165112, -122.457483), (38.1650758, -122.4574638), (38.1650545, -122.4574334), (38.1650365, -122.4574004), (38.1650179, -122.457368), (38.164999, -122.4573362), (38.1649796, -122.457305), (38.1649565, -122.4572782), (38.1649333, -122.4572523), (38.1649132, -122.4572233), (38.1648931, -122.457195), (38.1648761, -122.4571635), (38.1648689, -122.4571208), (38.1648489, -122.4570945), (38.1648292, -122.457069), (38.16481, -122.4570444), (38.1647915, -122.4570206), (38.1647835, -122.4569857), (38.1647668, -122.4569636), (38.1647509, -122.4569421), (38.1647326, -122.4569249), (38.1647149, -122.4569076), (38.164701, -122.4568862), (38.1646872, -122.4568642), (38.1646734, -122.4568412), (38.1646593, -122.4568171), (38.1646449, -122.4567917), (38.1646301, -122.4567652), (38.1646075, -122.4567443), (38.1645881, -122.4567192), (38.1645683, -122.4566936), (38.1645481, -122.4566677), (38.1645313, -122.4566383), (38.1645106, -122.4566123), (38.1644932, -122.4565831), (38.1644651, -122.4565645), (38.1644405, -122.456543), (38.1644019, -122.4565363), (38.1643774, -122.4565158), (38.16436, -122.4564885), (38.1643426, -122.4564614), (38.1643391, -122.4564201), (38.1643218, -122.4563935), (38.1643046, -122.4563669), (38.1642839, -122.4563441), (38.1642667, -122.4563177), (38.1642461, -122.456295), (38.1642289, -122.4562685), (38.1642116, -122.4562421), (38.1641633, -122.4562484), (38.1641253, -122.4562439), (38.164108, -122.4562174), (38.1640907, -122.456191), (38.1640872, -122.45615), (38.1640699, -122.4561236), (38.1640526, -122.4560973), (38.1640319, -122.4560747), (38.1640147, -122.4560484), (38.1639974, -122.4560221), (38.1639905, -122.4559848), (38.1639733, -122.4559585), (38.163956, -122.4559322), (38.1639353, -122.4559095), (38.1638938, -122.4559087), (38.1638765, -122.4558823), (38.1638592, -122.455856), (38.1638555, -122.4558149), (38.1638381, -122.4557886), (38.1638207, -122.4557623), (38.1637999, -122.4557398), (38.1637791, -122.4557173), (38.1637446, -122.4557096), (38.1637274, -122.4556835), (38.1637102, -122.4556573), (38.1637208, -122.455602), (38.1637072, -122.4555722), (38.1636937, -122.4555423), (38.1636766, -122.4555158), (38.1636594, -122.4554892), (38.1636386, -122.4554661), (38.1636107, -122.4554503), (38.1635896, -122.4554272), (38.1635717, -122.4554005), (38.1635538, -122.4553739), (38.1635357, -122.4553476), (38.1635176, -122.4553215), (38.1634996, -122.4552957), (38.1634819, -122.4552702), (38.1634543, -122.4552563), (38.1634373, -122.4552312), (38.1634207, -122.4552062), (38.1634045, -122.455181), (38.1633851, -122.4551588), (38.1633656, -122.4551358), (38.1633459, -122.4551121), (38.1633283, -122.4550851), (38.1633101, -122.4550578), (38.1632918, -122.4550294), (38.1632724, -122.4550012), (38.1632518, -122.4549736), (38.1632314, -122.4549447), (38.1632093, -122.4549169), (38.1631856, -122.4548904), (38.1631614, -122.4548632), (38.1631332, -122.4548427), (38.1631037, -122.4548248), (38.1630717, -122.454815), (38.1630382, -122.4548138), (38.1630052, -122.4548162)],
                 back=[(38.165272, -122.4576149), (38.1652567, -122.4575751), (38.1652628, -122.4575211), (38.1652656, -122.457468), (38.1652557, -122.4574231), (38.1652373, -122.4573844), (38.1652182, -122.4573462), (38.1652023, -122.4573055), (38.1651821, -122.4572686), (38.1651643, -122.4572297), (38.1651432, -122.4571943), (38.1651231, -122.4571581), (38.1651013, -122.4571244), (38.1650794, -122.4570916), (38.1650573, -122.4570596), (38.1650313, -122.4570334), (38.1650095, -122.4570037), (38.164988, -122.456975), (38.1649671, -122.4569476), (38.1649469, -122.4569214), (38.1649307, -122.4568925), (38.1649189, -122.4568611), (38.1649054, -122.4568353), (38.1648899, -122.456815), (38.1648759, -122.4567958), (38.1648698, -122.4567703), (38.164858, -122.456753), (38.1648466, -122.4567355), (38.1648352, -122.4567173), (38.1648176, -122.4567031), (38.1648036, -122.4566829), (38.1647887, -122.4566606), (38.1647745, -122.4566352), (38.1647543, -122.4566127), (38.1647385, -122.456584), (38.1647102, -122.4565649), (38.1646857, -122.4565412), (38.1646645, -122.4565138), (38.1646466, -122.456483), (38.1646284, -122.4564523), (38.16461, -122.4564218), (38.1645916, -122.4563919), (38.1645732, -122.4563624), (38.1645549, -122.4563334), (38.1645368, -122.4563051), (38.164519, -122.4562773), (38.1644944, -122.4562573), (38.1644769, -122.4562304), (38.1644561, -122.4562074), (38.1644354, -122.4561845), (38.1644148, -122.4561618), (38.1643976, -122.4561354), (38.164377, -122.4561126), (38.1643562, -122.4560897), (38.1643354, -122.4560668), (38.1643181, -122.4560403), (38.1643007, -122.4560136), (38.1642833, -122.455987), (38.1642694, -122.4559568), (38.164252, -122.4559304), (38.1642347, -122.455904), (38.1642174, -122.4558777), (38.1642002, -122.4558514), (38.164183, -122.4558252), (38.1641658, -122.455799), (38.1641485, -122.4557727), (38.1641313, -122.4557464), (38.164114, -122.45572), (38.1641027, -122.4556868), (38.1640853, -122.4556602), (38.1640581, -122.4556438), (38.1640405, -122.4556172), (38.1640195, -122.4555943), (38.1639951, -122.4555752), (38.1639777, -122.455549), (38.163957, -122.4555266), (38.1639399, -122.4555008), (38.1639196, -122.4554789), (38.1639028, -122.4554533), (38.1638826, -122.4554314), (38.1638624, -122.4554093), (38.1638421, -122.4553869), (38.1638216, -122.4553642), (38.1638043, -122.4553374), (38.1637832, -122.4553138), (38.1637651, -122.4552862), (38.1637419, -122.4552635), (38.1637212, -122.4552379), (38.1637024, -122.4552101), (38.1636857, -122.4551804), (38.1636671, -122.4551535), (38.1636462, -122.4551305), (38.1636287, -122.4551054), (38.1636101, -122.4550836), (38.1635911, -122.4550644), (38.1635701, -122.4550487), (38.1635531, -122.4550295), (38.1635319, -122.4550136), (38.1635121, -122.454994), (38.1634897, -122.4549734), (38.1634505, -122.4549654), (38.1634101, -122.4549562), (38.1633687, -122.4549467), (38.1633299, -122.4549346), (38.1633069, -122.4549039), (38.163282, -122.4548736), (38.1632567, -122.4548422), (38.1632293, -122.4548122), (38.1632028, -122.4547779), (38.1631698, -122.4547539), (38.163135, -122.4547328), (38.1630943, -122.4547325), (38.1630543, -122.4547362), (38.1630155, -122.4547443)]),
        ],
        # corner-worker stations measured on the captures (small raised platforms beside the track) and confirmed on the onboard
        marshal_posts=[
            dict(name='T6 hilltop', latlon=(38.1631039, -122.4600748), h=3.8, color='#2f5d9e',
                 h_src='round 7 (owner note 40): an elevated hut, the roof ~2.5 m over the ~1 m wall (owner_39, May 2025 onboard, reference only): deck 1.2 m, roof top ~3.6 m; white walls, blue lower band, open front, roof overhang',
                 src='c20_s3135: a ~3 x 3 m platform with a box behind the right wall at the crest before the Carousel; Street View GMaTaipEd9Hm7fMNE26aGQ (Jul 2011): white box and tyre stack there (owner: "the one at the top of the hill just before T6")'),
            dict(name='T4', latlon=(38.1639325, -122.4631172), h=4.0,
                 src='c20_s2695: a raised hut on a platform 27 m right of the T4 approach (long shadow); onboard 0:33 white elevated post with roof on the right; Street View 3a panorama (Jul 2011) shows it ahead right'),
            dict(name='T2 exit', latlon=(38.1607335, -122.4589865), h=3.0,
                 src='c20_s2200: a ~2 m white hut at the foot of the T2 terraces, 31 m left of the centre at s ~445 (round 5); onboard 0:12 white marshal hut ahead-left at the fence line'),
            # round 8 (owner notes 60-61): the 8a station is a brown-roofed TOWER over the T6-facing wall at the SE end of the
            # track-side wall, not round 7c's '8a outside' hut (s 2483, 10.9 m left, among the campers: a camper, note 60, removed).
            # Footprint and heading from the owner's green outline digitised in owner/t8a_station.json (frame s 2600, half 90,
            # 0.12 m/px, the capwin mapping): 4.0 x 3.5 m, long axis bearing 280.6, read as the roof seen from above, so the hut
            # is w 2.8 x d 2.3 under the kit's 0.6 m overhang; its open front faces bearing 10.6 (square to the long axis,
            # toward the 8a-T9 pass). Height: the 2017 lidar block over the footprint, 3.5-4.1 m (roof falling to the SE),
            # so h 4.0 (the kit's roof top is h - 0.19 m = 3.81 m)
            # round 9 (judge r8, the owner's first notice): style 'deck', the kit's open viewing deck (a solid lighter lower
            # storey to a sill, an open deck under a broad flat roof overhanging 0.9 m at the front), as owner_52 shows it
            dict(name='8a (T9) station tower', latlon=(38.1645832, -122.4585614), h=4.0, w=2.8, d=2.3, heading_deg=10.6,
                 roof='#3a2917', color='#dcdfe2', style='deck',
                 h_src='lidar 2017 DSM - DEM over the footprint (1 m grid): a 4 x 4 m block 3.5-4.1 m above the ground (p90 3.65 m, max 4.06 m; the roof falling to the SE), i.e. roof top ~3.8 m; h 4.0 puts the kit\'s roof top at 3.81 m (deck 1.4 m, over the 0.85 m Jersey)',
                 src='owner note 61 (tools/track/tracks/sonoma/owner/t8a_station.json, green outline on the s 2600 window: 4.0 x 3.5 m, long axis 280.6 deg, centre (38.1645832, -122.4585614) = ENU (-84.15, 209.63); s 2659, 32.2 m right on the 8a-T9 pass; s 1772, 40.7 m right on the drag strip); "The tower\'s roof sits over the wall" (1.7 m from the T6-facing wall line); c20_s0275: the dark roof square with its NW shadow, roof pixels median rgb (58, 41, 23), a dark brown (owner note 60: "brown-roofed"); owner_52 (May 2025 onboard 1:14, reference only): a white roofed hut behind the track-side wall; white walls, no coloured band read (color white); round 9: owner_52 (May 2025 onboard 1:14, reference only) shows a broad brown overhanging roof over a dark OPEN viewing deck (the background visible through it between corner posts) above a lighter solid lower storey, drawn as style \'deck\''),
            dict(name='9a, stand foot', latlon=(38.1632923, -122.4549874), h=3.0,
                 src='round 7 (owner note 49, corrected): onboard t098 and the owner crop owner_49_9a_station_crop.jpg: a small hut at the base of the back-straight terraces near their 9a end, behind the catch fence, the marker cone on the verge in front of it; position from the frame (s ~3025, 28 m left, between the wall line and the terrace foot): not resolved on c20_s0605 / c20_s0660 / c20_o0660 (event trailers parked there); band colour not readable (default)'),
            dict(name='T7', latlon=(38.1659466, -122.4626554), h=4.9, color='#dcdfe2',  # round 7: t072 white hut, no coloured band
                 src='c20_s3905: a post at the end of the left wall at T7; onboard 1:11 raised white post with roof ahead; round 6 (orchestrator S4): onboard 1:12 (t072) the hut stands on legs about as tall as itself, ~2.5 m (the kit draws legs h - 2.4 m)'),
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
        # the pit-out blend line (round 7e, owner notes 55-56; was round 7's line along the fitted edge, which bent 6 m out
        # with the edge's merge bulge after s 205 and closed the lane): the STRAIGHT continuation of the short pit-side wall
        # past T1. That wall (s 134-158, 22.9 m, a white top with a dark north shadow on c20_s1815 / c20_s1870, the owner's
        # 'visible wall segment' in owner_56; since round 8, owner note 59, the solid last section of the continuous pit-lane
        # side wall, whose K-rail runs on upstream through s 88-133) is measured as a line (656 picks at 0.035 m/px, rms 0.055 m, heading 177.9 deg);
        # the double yellow starts at its west end ('the nose', s 158) and runs straight. Its direction: the paint visible on
        # c20_s1870 / c20_s1925 for 52 m past the wall (103 of 103 picks, straight fit rms 0.044 m, heading 179.1 deg: 1.1 deg
        # off the wall toward the track; the owner's red line sits 0.9 deg off his wall strip the same way). Its length: the
        # owner's drawing, red line 839 px against the 304 px wall strip (x 2.76), on the measured 22.9 m wall = 63.3 m,
        # s 158-222 (vehicles hide the paint beyond 52 m). Beyond its end the lane is open to the track (no line). Cones: the
        # 2025 pit-out video 24of8fjjAug t=304 (small yellow cones on the double yellow, 15-20 m apart; 17 m).
        pit_exit_cones=dict(latlon=[(38.1620421, -122.4562996), (38.1620425, -122.4563325), (38.1620429, -122.4563653), (38.1620433, -122.4563982), (38.1620438, -122.4564311), (38.1620442, -122.4564639), (38.1620446, -122.4564968), (38.1620450, -122.4565297), (38.1620455, -122.4565626), (38.1620459, -122.4565954), (38.1620463, -122.4566283), (38.1620467, -122.4566612), (38.1620472, -122.4566941), (38.1620476, -122.4567269), (38.1620480, -122.4567598), (38.1620484, -122.4567927), (38.1620489, -122.4568256), (38.1620493, -122.4568584), (38.1620497, -122.4568913), (38.1620502, -122.4569242), (38.1620506, -122.4569570), (38.1620510, -122.4569899), (38.1620514, -122.4570228)], spacing=17.0, color='#e5c21e', size=0.5,
                            src='round 7e (owner notes 55-56): the straight pit-out blend line from the west end of the pit-side wall s 134-158 (c20_s1815 / c20_s1870), along the paint on c20_s1870 / c20_s1925 (100 % picked, rms 0.044 m), 63.3 m (owner_56 drawing scaled by the wall), s 158-222; 2025 pit-out video 24of8fjjAug t=304: small yellow cones (~0.5 m) on the double yellow line, 15-20 m apart (17 m used); t=300: none before the nose'),
        paint_lines_declared=[
            # round 13 part B (owner note 135): the centre line of the drag strip's continuation past the T7 fork (a light grey
            # solid line on c20_s3740..s3960, from the T7 junction to ~70 m short of the fork)
            dict(latlon=[(38.1663426, -122.4621473), (38.1663200, -122.4621118), (38.1662976, -122.4620761), (38.1662752, -122.4620403), (38.1662530, -122.4620044), (38.1662306, -122.4619686), (38.1662084, -122.4619327), (38.1661861, -122.4618968), (38.1661639, -122.4618609), (38.1661415, -122.4618251), (38.1661192, -122.4617893), (38.1660969, -122.4617535), (38.1660745, -122.4617177), (38.1660522, -122.4616819), (38.1660300, -122.4616460), (38.1660078, -122.4616100), (38.1659856, -122.4615741), (38.1659633, -122.4615383), (38.1659411, -122.4615023), (38.1659189, -122.4614664), (38.1658966, -122.4614305), (38.1658743, -122.4613946), (38.1658521, -122.4613588), (38.1658298, -122.4613230), (38.1658075, -122.4612871), (38.1657852, -122.4612513), (38.1657629, -122.4612154), (38.1657407, -122.4611794), (38.1657185, -122.4611435), (38.1656963, -122.4611076), (38.1656739, -122.4610718), (38.1656514, -122.4610362), (38.1656288, -122.4610007), (38.1656062, -122.4609652), (38.1655836, -122.4609296), (38.1655610, -122.4608941), (38.1655384, -122.4608586), (38.1655158, -122.4608230), (38.1654989, -122.4607964)], width=0.12, color='#cfcfc8',
                 src='c20_s3740 / c20_s3795 / c20_s3905 / c20_s3960: the continuation centre line, wall_measure bright 175 m, 85 % picked, rms 0.02 m (round 13 part B)'),
            dict(latlon=[(38.1620421, -122.4562996), (38.1620425, -122.4563325), (38.1620429, -122.4563653), (38.1620433, -122.4563982), (38.1620438, -122.4564311), (38.1620442, -122.4564639), (38.1620446, -122.4564968), (38.1620450, -122.4565297), (38.1620455, -122.4565626), (38.1620459, -122.4565954), (38.1620463, -122.4566283), (38.1620467, -122.4566612), (38.1620472, -122.4566941), (38.1620476, -122.4567269), (38.1620480, -122.4567598), (38.1620484, -122.4567927), (38.1620489, -122.4568256), (38.1620493, -122.4568584), (38.1620497, -122.4568913), (38.1620502, -122.4569242), (38.1620506, -122.4569570), (38.1620510, -122.4569899), (38.1620514, -122.4570228)], width=0.1, double=0.3, color='#d9b42a',
                 src='round 7e pit-out blend line (as the pit-exit cones: straight from the pit-side wall s 134-158, c20_s1815 / c20_s1870 / c20_s1925, owner_56); colour: the 2025 pit-out video 24of8fjjAug t=304 (double yellow)'),
        ],
        # round 10 (judge r9, the pit-out lane surface): no track shoulder on the left where the pit-out lane runs against the
        # edge past the K-rail to the merge (the shoulder rows rose through the lane as pale patches; see pit_lane.lane)
        track_shoulder_cut=[dict(side='left', s=(150, 240), why='the pit-out lane runs against the left edge (t0304: one plain surface)'),
                            # round 11 (owner note 68, owner_68_T11_texture.png: "Texture issue before T11"): the same cause at
                            # the pit-in: the lane's track-facing side is at the left edge (gap 0) from s 3522 to s ~3635, and
                            # the track ribbon's left shoulder rows (draping the ortho's lane paint) rose through the lane as
                            # pale patches (compare/sonoma/round11/stills/n68_left_before.jpg); onboard 1:55-1:57 and the
                            # captures c20_s1155 / c20_s1210 show one dark surface to the cone line
                            dict(side='left', s=(3515, 3640), why='the pit-in lane runs against the left edge from s 3522 to s ~3635 (round 11, owner note 68)')],
        edge_line_cut=[dict(side='left', s=(88, 242), why='the pit-out: the continuous pit wall stands at the edge from s ~88 to s ~158 (round 8, owner note 59: its K-rail segment tops s 88-133, read in earlier rounds as a dotted block line that broke the line from s 88.8, then its solid section s 134-158; the cut starts at s 88, was 100), then the declared double yellow blend line (s 158-222, 2025 pit-out video t=304) and the open merge beyond its end (owner note 56: no line), not the white edge line')],
        # raised kerbs round the T7 complex islands off the lap (round 7b, owner note 45): the capture's red / white kerb paint
        # measured as lines (wall_measure bright along the painted blocks, capture shift applied), drawn raised so the ortho's
        # flat kerb paint never shows under a partial strip
        kerb_lines=[
            dict(latlon=[(38.1667106, -122.4620068), (38.1666918, -122.461982), (38.1666742, -122.461956), (38.166659, -122.4619276), (38.1666438, -122.4619002), (38.166626, -122.4618744), (38.1666101, -122.4618461), (38.1665948, -122.4618172), (38.1665754, -122.4617939), (38.1665542, -122.4617719), (38.1665356, -122.4617471), (38.1665181, -122.461721), (38.1665005, -122.461695), (38.1664828, -122.4616691), (38.1664651, -122.4616433), (38.1664622, -122.461639)],
                 width=1.0, colors='red', src="c20_s3960 / c20_s0000: red / white kerb blocks along the O'Reilly island's lower edge (the T7 inside runoff / PWC road side), wall_measure bright 100 % picked, rms 0.91 m"),
            # round 13 part B (owner note 135): re-measured on the blocks round the small island's nose and NE edge (the round-7b
            # line stood ~1 m off them on its NE edge and stopped at the nose)
            dict(latlon=[(38.1663919, -122.4620844), (38.1664031, -122.4621022), (38.1664144, -122.4621200), (38.1664258, -122.4621377), (38.1664372, -122.4621553), (38.1664486, -122.4621730), (38.1664606, -122.4621904), (38.1664726, -122.4622074), (38.1664850, -122.4622240), (38.1665039, -122.4622300), (38.1665168, -122.4622124), (38.1665178, -122.4621892), (38.1665193, -122.4621664), (38.1665211, -122.4621437), (38.1665235, -122.4621210), (38.1665201, -122.4620978), (38.1665140, -122.4620763), (38.1665078, -122.4620548), (38.1665012, -122.4620335), (38.1664942, -122.4620124), (38.1664863, -122.4619908), (38.1664769, -122.4619712), (38.1664675, -122.4619517), (38.1664579, -122.4619324), (38.1664480, -122.4619133), (38.1664379, -122.4618944), (38.1664274, -122.4618758), (38.1664166, -122.4618574), (38.1664057, -122.4618391), (38.1663950, -122.4618207), (38.1663871, -122.4618067)],
                 width=1.0, colors='red', src='c20_s3960 / c20_s0000: red / white kerb blocks round the nose and NE edge of the island between the short-T7 road and the drag-strip road (round 13 part B: wall_measure bright, 81 % picked, rms 0.18 m, 60 m; was round 7b, 1 m off); onboard t076 red / white kerb round the nose')
        ],
        # painted ground logos (round 7b, owner note 46): the name typed in the observed colours, no logo artwork; footprint and
        # reading direction measured on the clean captures (capture shift applied)
        ground_signs=[
            # round 13 part B (owner note 135): no red panel: the 2026 captures show white outlined lettering on the island's dark
            # painted surface (the red was the NAIP year's island); the island is retextured dark (ortho_pave)
            dict(latlon=(38.1666431, -122.4618119), length=17.0, height=7.5, heading=135.0, text="O'Reilly", fg='#ffffff',
                 src="c20_s0000 / c20_s3960: an O'Reilly logo painted inside the T7a hairpin island (white lettering with an outline, ~17 x 7.5 m, reading NW); the summer NAIP shows it as a red patch (owner_45 'red splotch'); red panel / white letters"),
            dict(latlon=(38.1588939, -122.4521769), length=18.0, height=4.5, heading=8.7, text='TOYOTA', fg='#ffffff',
                 src='c20_s1320 / c20_s1265: TOYOTA lettering painted in the T11 hairpin infield (white, ~18 m, reading ENE); the red emblem beside it is logo artwork, not drawn'),
            # round 7c: the smaller names above TOYOTA (c20_s1265 at 0.04 m/px; the illegible ones are not placed)
            dict(latlon=(38.1589594, -122.4523855), length=6.8, height=3.0, heading=15.0, text='CW', fg='#ffffff', src='c20_s1265: CW lettering in the T11 infield (row above Coca-Cola)'),
            dict(latlon=(38.1589289, -122.4522850), length=6.2, height=2.0, heading=15.0, text='Coca-Cola', fg='#ffffff', src='c20_s1265: Coca-Cola script in the T11 infield, white'),
            dict(latlon=(38.1589540, -122.4521982), length=6.5, height=2.0, heading=20.0, text='xfinity', fg='#ffffff', src='c20_s1265: xfinity lettering in the T11 infield, white'),
            dict(latlon=(38.1590007, -122.4522142), length=3.2, height=3.2, heading=15.0, text='TNT', fg='#1a1a1a', bg='#f4f3ef', src='c20_s1265: the TNT roundel in the T11 infield (white disc, dark letters; drawn as a square panel)'),
            dict(latlon=(38.1590115, -122.4523901), length=6.0, height=1.6, heading=15.0, text='PIT BOSS', fg='#ffffff', src='c20_s1265: PIT BOSS lettering in the T11 infield (top-left row, partly legible)'),
            dict(latlon=(38.1588066, -122.4521872), length=24.0, height=5.5, heading=14.3, text='Save Mart', fg='#ffffff',
                 src='c20_s1320 / c20_s1265: Save Mart lettering painted in the T11 hairpin infield (white, ~24 m)'),
        ],
        # tyre runs in front of a wall are facings of it (round 7b, owner note 48): stacks against the wall line, never side by
        # side at an offset (the captures put the dark tyre band and the bright wall top 1-2.5 m apart: one is the stack, the
        # other the concrete behind it); the wall-ends / facing gate checks it
        tyre_facings=dict(reach=2.6, off=0.55),
        # free-standing concrete blocks (round 7, owner note 38): kind 'block' (drawn only), w across, d along the track
        blocks=[
            # the onboard (higher precedence than the captures) puts them at the apex: two large red / white striped blocks on
            # the inside apron beside the apex kerb (t120 ahead, t122 / t124 abeam right); positions from the frames (1.6 m
            # beyond the right edge at s ~3668 and ~3684); the 2026 captures (another event) show three such blocks at the
            # OUTSIDE edge instead (c20_s1320, s ~3679, 0.6-1.3 m inside the left edge): not placed there (moveable furniture)
            dict(latlon=(38.1587344, -122.4520929), w=1.0, d=1.6, h=1.0, style='striped', color='#c8202c',
                 src='onboard RAZip6S84CM 2:00-2:04 (t120 / t122 / t124): large red / white striped concrete block at the T11 apex beside the kerb (inventory rows s 3638-3699 right); c20_s1320 shows the same blocks (dark bands, ~1.6 m) moved to the outside edge at another event'),
            dict(latlon=(38.1587122, -122.4521780), w=1.0, d=1.6, h=1.0, style='striped', color='#c8202c',
                 src='onboard RAZip6S84CM 2:02-2:04 (t122 / t124): the second striped block at the apex (see the first); c20_s1320'),
            # round 7b (item F): the three blocks the 2026 capture shows at the OUTSIDE apron edge of the hairpin (c20_s1320,
            # bright 1.6 m boxes with dark joints, s ~3678-3681, 0.6-1.3 m inside the fitted left edge); onboard t122: white
            # blocks along the apron edge
            dict(latlon=(38.1585091, -122.4521152), w=1.0, d=1.6, h=0.8, style='plain', color='#f0efea',
                 src='c20_s1320: block 1 of 3 at the outside apron edge of T11 (s ~3681, 10.2 m left of the centre, capture shift applied); onboard 2:02 (t122) white blocks along the apron edge'),
            dict(latlon=(38.1585091, -122.4520926), w=1.0, d=1.6, h=0.8, style='plain', color='#f0efea', src='c20_s1320: block 2 of 3 (see block 1)'),
            dict(latlon=(38.1585107, -122.4520700), w=1.0, d=1.6, h=0.8, style='plain', color='#f0efea', src='c20_s1320: block 3 of 3 (see block 1)'),
        ],
        # free-standing tyre stacks (round 5): the ones the onboard shows that the captures place
        tyre_stacks=[
            dict(latlon=(38.1640111, -122.4576293), h=0.8, src='round 6 (orchestrator S3): onboard 0:58 (t058) a black tyre stack at the foot of the light mast on the Carousel-exit runoff (0.8 m, tyre-ref; inventory s 1687 right); the mast is the lidar spike at (-1.5, 146.5) confirmed on c20_s3355 (structure kit masts), the stack 1.2 m track-side of its base'),
            dict(latlon=(38.1632399, -122.4575474), h=0.84, src='c20_s3300 / c20_s3355: two dark stacks on the runoff right of the Carousel exit; onboard 0:56 single black tyre stacks on the runoff (0.8 m, tyre-ref)'),
            dict(latlon=(38.1631995, -122.4575097), h=0.84, src='c20_s3300 / c20_s3355: the second stack; onboard 0:56'),
            dict(latlon=(38.1629302, -122.4551972), h=0.42, color='#8a8d90', src='onboard 1:40: a stack of 2 grey tyres just past the 9a right apex kerb (kerb end s ~3045 on c20_o0660), 1.5 m outside the edge'),
            dict(latlon=(38.1625828, -122.4546884), h=0.63, src='onboard 1:44: a black tyre stack in front of the T10-entry board wall at its start (s ~3125; wall on c20_s0715 / c20_s0770)'),
        ],
        # advertising boards on the walls as plain coloured panels, no logos (20 Oct 2026, round 4; owner notes 13 / 15):
        # colours in the order the onboard shows them, track s from the onboard time (+-20 m), panel heights from the
        # Street View scale (owner_15: ~2.5 m boards on a ~1 m wall)
        # the T2 footbridge's fascia (round 6, owner O2 / orchestrator F6): onboard 0:06-0:08 (t006, t008) toward oncoming cars:
        # Save Mart (white, red lettering), TOYOTA GAZOO Racing (red, white), TOYOTA GAZOO Racing (white, black), SUNOCO (blue,
        # yellow), LAS VEGAS (navy, white); the far face is not seen in the footage (the same set)
        bridge_banners={'1382620985': [
            ['Save Mart|#f4f3ef|#c8202c', 'TOYOTA GAZOO Racing|#d6262c|#ffffff', 'TOYOTA GAZOO Racing|#f4f3ef|#1a1a1a', 'SUNOCO|#1f3f99|#f5d000', 'LAS VEGAS|#1d2230|#f3f3f0'],
            ['Save Mart|#f4f3ef|#c8202c', 'TOYOTA GAZOO Racing|#d6262c|#ffffff', 'TOYOTA GAZOO Racing|#f4f3ef|#1a1a1a', 'SUNOCO|#1f3f99|#f5d000', 'LAS VEGAS|#1d2230|#f3f3f0']]},
        # Round 6 (owner O2, Laguna's rule): every board carries the sponsor NAME the footage shows on that run, typed as plain
        # bold text in the observed background / text colours (no logo artwork or emblems); names cycle per 6 m panel.
        # Observed colours from the 2026 onboard frames named in each src (manifest "Boards" table).
        wall_boards=[
            # round 9 (judge r8, "SONOMA TURN 8" row): typed white lettering on a grey panel on the station-side wall's track
            # face, from onboard t088 (RAZip6S84CM 1:28, inventory row s 2644 right "dark wall with a 'SONOMA TURN 8' sign"):
            # the grey panel (graded rgb ~146, 168, 154: a neutral grey under the frame's green cast) with SONOMA TURN 8 in white
            # sits on the dark wall between the camera and the station. Length: in t088 the panel is 142 px against the
            # 1.0 m wall's 17 px face height at that place, i.e. at least 8.4 m (foreshortened: a lower bound), the text ~70 %
            # of it; drawn as one 7.7 m panel on the black facing (the wall's track face there) at s 2641-2647, 0.15-0.85 m
            # above the ground. The small logo mark left of the text is not drawn (no logo art)
            # round 10 (judge r9, the panel still): drawn 0.12 m off the facing's measured line, the panel stood inside the
            # rendered tyre stacks (two rows 0.6 m apart from 0.55 m off the wall, their fronts ~1.43 m out) and showed in no
            # still; `off` 0.7 puts it on the stacks' front (~1.5 m from the wall line), where t088 shows the lettering:
            # on the face of the dark barrier. Size, height, text and colours unchanged
            dict(wall='T9, right: black tyre facing in front of the 8a station (round 8)', s=(2641, 2647), h=0.7, base=0.15, panel=9.0, off=0.7,
                 names=[('SONOMA TURN 8', '#8f9392', '#ffffff')],
                 src='onboard RAZip6S84CM t088 (1:28): white SONOMA TURN 8 lettering on a grey panel on the dark wall beside the 8a station (inventory row s 2644 right)'),
            dict(wall='T10 to T11, left wall with the ad boards', s=(3172, 3235), h=2.5,
                 names=[('SONOMA RACEWAY', '#1d2a3a', '#ffffff')],
                 src='onboard 1:43.2-1:44.5 (t104): dark navy SONOMA RACEWAY boards along the T10 entry wall'),
            dict(wall='T10 to T11, left wall with the ad boards', s=(3235, 3262), h=2.5,
                 names=[('SUNBELT RENTALS', '#3aa635', '#ffffff')],
                 src='onboard 1:46 (t106): green SUNBELT RENTALS boards (white lettering)'),
            dict(wall='T10 to T11, left wall with the ad boards', s=(3262, 3335), h=2.5,
                 names=[('TOYOTA', '#f4f3ef', '#1a1a1a'), ('HUMBOLDT', '#f4f3ef', '#1d2a3a'), ('SAVE MART', '#f4f3ef', '#c8202c'), ('zMAX', '#c8202c', '#ffffff')],
                 src='onboard 1:48-1:50 (t108, t110): white TOYOTA boards (black lettering), white Humboldt (navy), white SAVE MART (red), zMAX on red'),
            dict(wall='T10 to T11, left wall with the ad boards', s=(3335, 3478), h=2.5,
                 names=[('EchoPark', '#22262b', '#ffffff'), ('zMAX', '#c8202c', '#ffffff')],
                 src='onboard 1:52-1:55 (t112, t114; inventory s 3335 and 3421): dark EchoPark AUTOMOTIVE boards (white / green lettering), zMAX; to the Jersey start at s 3478'),
            dict(wall='T11 approach, left: outer pit-in wall (from the split)', s=(3485, 3563), h=2.5,
                 names=[('LAS VEGAS', '#1a1a1a', '#f3f3f0'), ('LAS VEGAS', '#1a1a1a', '#f3f3f0'), ("O'REILLY", '#1f6b3a', '#ffffff')],
                 src="onboard 1:56 (t116): black LAS VEGAS boards (white lettering), then green O'Reilly"),
            dict(wall='T11 entry, left: outer pit-in wall (garage side)', s=(3563, 3646), h=2.5,
                 names=[('Lucky', '#f4f3ef', '#c8202c'), ('SAVE MART', '#f4f3ef', '#c8202c'), ('PIT BOSS', '#1a1a1a', '#f3f3f0'), ('Coca-Cola', '#1a1a1a', '#ffffff'), ('xfinity', '#f4f3ef', '#1a1a1a')],
                 src='onboard 1:58-2:00 (t118, t120): white Lucky / SAVE MART COMPANIES (red lettering), black PIT BOSS, black Coca-Cola, xfinity'),
            # F4 (owner, inventory 0:58-1:10): the T6-T7 wall is plain up to s ~2105; the TOYOTA boards on posts above the wall
            # stand at 1:10 (s 2112), the Pirelli / red boards on the low wall at its end at 1:12 (s 2157)
            dict(wall='T7 approach, left: wall on to the T7 post (round 5)', s=(2105, 2140), h=2.5, base=1.6,
                 names=[('TOYOTA', '#f4f3ef', '#1a1a1a')],
                 src='onboard 1:10 (t070): large white TOYOTA boards with red frames on posts above the wall (~2.5 m, inventory s 2112)'),
            dict(wall='T7 approach, left: wall on to the T7 post (round 5)', s=(2140, 2150), h=0.9, base=0.15,
                 names=[('PIRELLI', '#f5d000', '#1a1a1a'), ('', '#b8202a', '#ffffff')], panel=5.0,
                 src='onboard 1:12 (t072): Pirelli (yellow) and red boards on the face of the low wall at the wall end (inventory s 2157, wall 1 m: the boards do not rise above it)'),
            dict(wall='T10 entry, left: board wall along the bypass edge (round 5)', s=(3118, 3168), h=2.2,
                 names=[('SONOMA RACEWAY', '#1d2a3a', '#ffffff'), ('SONOMA RACEWAY', '#1d2a3a', '#ffffff'), ('SUNBELT RENTALS', '#3aa635', '#ffffff'), ('TOYOTA', '#f4f3ef', '#1a1a1a')],
                 src='onboard 1:44-1:46 (round 5, t104 / t106): SONOMA RACEWAY (dark navy), SUNBELT RENTALS (green) and TOYOTA (white) boards; 3.2 m to the top, between the 2.8 m read at 1:44 and the 4.0 m at 1:46 where they join the T10 wall (inventory, horizon-ratio)'),
            dict(wall='drag strip, infield (NE) side', s=(3925, 4098), h=1.5,
                 names=[('LAS VEGAS', '#1a1a1a', '#f3f3f0'), ("O'REILLY", '#1f6b3a', '#ffffff'), ('EchoPark', '#3aa635', '#ffffff'), ('zMAX', '#c8202c', '#ffffff'), ('TOYOTA', '#f4f3ef', '#1a1a1a'), ('SONOMA RACEWAY', '#1d2a3a', '#ffffff')],
                 src="onboard 2:08-2:18 (round 5, t126-t136): LAS VEGAS (black), O'Reilly and EchoPark (green), zMAX (red), TOYOTA (white) and SONOMA RACEWAY boards on the far drag-strip wall; 2.5 m to the top (inventory 2:08-2:12, horizon-ratio)"),
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
            # round 14B (owner, round-13 drive, 23 Oct 2026 20:30 PDT): his red arc across the paddock-side mouth at T1 is the
            # course boundary there and a cone line, "Put a few cones there" (compare/sonoma/owner_edges_r14/close_s0175, his
            # green the access road's edge ending on it); the line is his arc (tracks/sonoma/owner/r14/mouths.json, s 166-179
            # of the round-14A package, 13.4 m): four cones 4.4 m apart; no frame shows cones there (his instruction), so the
            # default orange cone
            dict(latlon=[(38.1622051, -122.4563919), (38.1622007, -122.4564155), (38.1621960, -122.4564389), (38.1621927, -122.4564623), (38.1621904, -122.4564855), (38.1621892, -122.4565087), (38.1621892, -122.4565317), (38.1621893, -122.4565432)], spacing=4.4,
                 src='owner round-13 drive: his red arc across the paddock-side mouth at T1, "Put a few cones there" (owner/r14/mouths.json, '
                     'compare/sonoma/owner_edges_r14/close_s0175_marked.png, local); cones on his line'),
            # round 7 (owner note 49): the single orange marker cone on the left verge before the 9a chicane; onboard t096 shows
            # it ~85 m ahead by the wall, t098 ~15 m ahead mid-verge (the same cone: the car covers ~80 m in 2 s); position
            # from t098's perspective (between the edge and the wall, nearer the edge); none in t090-t094
            dict(side='left', s=(3031, 3032), off=6.4, spacing=10.0, size=0.5,
                 src='onboard RAZip6S84CM 1:36-1:38 (t096 / t098; owner_49 crop): one orange cone ~0.5 m on the grass verge left before 9a, ~6 m beyond the edge (frame perspective); not resolved on c20_s0605 / c20_o0660'),
            # round 7b (note 45): cones across the short-T7 (PWC) road where it leaves the T7 paved area (its mouth is 22 m off
            # the track, so the closed-road mouth rule finds none): onboard 1:14 (t074) orange cones ahead-right across it
            dict(latlon=[(38.1663154, -122.4622045), (38.1663858, -122.4621335)], spacing=2.5,
                 src='onboard RAZip6S84CM 1:14 (t074): orange cones across the short-T7 road at the T7 hairpin; line across the road\'s first section (OSM 505454376, NAIP width)'),
            # round 7f: tall delineator posts, not traffic cones (t074 / t076, local frames)
            dict(side='right', s=(2196, 2212), off=0.5, spacing=5.0, color='#e0561c', size=1.0, style='delineator',
                 src='onboard 1:14-1:16 (round 5): orange delineator posts on the edge of the T7a island before its kerb (island on c20_s3960); round 7f: t074 zoomed shows 4 tall orange posts with white bands along the island edge (4 posts over the 16 m line: spacing 5 m), 1 m (inventory 1:14 cone-ref)'),
            dict(side='right', s=(2275, 2276), off=1.2, spacing=10.0, color='#e0561c', size=1.0, style='delineator',
                 src='T7a island-nose delineator post (round 7f): onboard 1:16 (t076) one tall orange post with white bands ahead-right beside the red / white island kerb, ~10-15 m ahead of the frame station (s ~2262, compare_sheets/onboard.json), just beyond the kerb band (0.65 m centred 0.3 m out); position from the frame only, +-15 m'),
            # round 7e (owner note 57): orange PYLONS (tall delineator posts, ~1 m, white bands) close the drag strip continuation
            # at the T7 fork, across the strip's mouth (track edge to the strip's far paved edge, c20_s3630); no tyres
            dict(latlon=[(38.1652055, -122.4603712), (38.1652389, -122.4603487), (38.1652723, -122.4603262), (38.1653057, -122.4603037)], spacing=1.7, color='#e0561c', size=1.0, style='delineator',
                 src='owner note 57 (May 2025 onboard fEcQdo0ucL8 0:57, reference only: a line of orange pylons, no tyre barrier); onboard RAZip6S84CM t064: 7 orange posts with white bands across the mouth (spacing 1.7 m); the line runs ACROSS the strip at its mouth (perpendicular to the strip, heading 62 deg: the first cross-section of the closed road drag strip past the T7 fork, where it leaves the course at s ~1942), from the track right edge to 1 m past the strip far paved edge, 12.6 m; the round-5 tyre line ran 30 deg off the strip own direction'),
            # round 7 (owner note 37): ON the measured solid double line, 0.3 m to its track side, from where the dashed
            # blend line turns solid (s ~3510) to the Jersey nose; the round-5 line ran 0.4 m outside the fitted track edge,
            # which at the lane mouth lies along the outer wall, so it started inside the lane and converged into the wall
            dict(latlon=[(38.1599952, -122.4522528), (38.1599571, -122.4522378), (38.1599222, -122.4522242), (38.1598878, -122.4522103),
                         (38.1598522, -122.4521957), (38.1598150, -122.4521807), (38.1597808, -122.4521668), (38.1597427, -122.4521515),
                         (38.1597080, -122.4521375), (38.1596713, -122.4521228), (38.1596333, -122.4521076), (38.1595966, -122.4520929),
                         (38.1595618, -122.4520788), (38.1595240, -122.4520627), (38.1594903, -122.4520467), (38.1594540, -122.4520287),
                         (38.1594191, -122.4520115), (38.1593854, -122.4519953), (38.1593685, -122.4519874), (38.1593423, -122.4519695)], spacing=4.0,
                 src='pit-in double white line measured on c20_s1155 / c20_s1210 (wall_measure bright, sguide s 3500-3586 at ~4 m left, 94 % picked, rms 0.15 m), s 3510-3584; cones on it: Street View owner_15, onboard 1:58 (t118) cones ahead-right along the line'),
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
                 # round 13 part B (owner note 135): the T7 mouth part's painted lines wandered into a trailer parked along its SE wall
                 # (c20_s3850 / c20_s3905); no line is measurable there, so none is drawn on that part
                 part_overrides=[dict(near=(38.1660238, -122.4628784), paint=False,
                                      src='c20_s3850 / c20_s3905: trailers parked along the mouth; paint.measure ran into them (round 13 part B)')],
                 mouth_cones=[dict(near=(38.1639925, -122.4635092), src='onboard 0:34: 3-5 orange cones across the Chute mouth ahead-left at T4 (inventory)'),
                              dict(near=(38.1660875, -122.4627527), src='onboard 1:12: small orange cones in front of a black tyre line across the Chute mouth at T7 (inventory, added row)')]),
            dict(name='drag strip', ways=['28825448'], half_width=9.0, max_half=12.0, surface='concrete', paint=True,
                 mouth_cones=[]),
            # round 7e (owner note 57: 'per our previous discussion, the pavement should be modeled as race track'): the drag
            # strip's continuation past the T7 fork (OSM raceway 834724051, from the course at s 1878 through the fork node to the
            # node at the T7 hairpin, s ~2216) was unpaved ground
            # in the sim (the ortho's pale concrete); now the circuit's road material with its painted lines (closed_roads rule,
            # edges_from_paint), stopped at its walls; its mouth is closed by the pylon line (cone_lines_declared)
            dict(name='drag strip past the T7 fork', ways=['834724051:316916576:4954006091'], half_width=9.0, max_half=12.0, surface='asphalt', paint=True,
                 edges_from_paint=True, mouth_cones=[],
                 src='OSM 834724051 (raceway, the straight NW continuation of the drag strip); c20_s3630 / c20_s3685 / c20_s3740: paved strip with lane paint beyond the fork; owner note 57 (May 2025 onboard fEcQdo0ucL8 0:57, reference only); onboard t064 / t066 asphalt with painted lane lines'),
            # the paved runoff INSIDE T7 (the triangle inside the hairpin, round the short-T7 way): cars may use it
            # (owner), so no cones; the racing line stays on the track (cutting through adds distance)
            # round 13 part B (owner note 135): no painted edges and no paint-measured paving edges: it is an open junction (the
            # 2026 captures show plain asphalt between the islands), so paint.measure found the islands' kerbs and stray marks
            # and drew five white lines across it and paving edges over the islands (round 7b had paint / edges_from_paint True)
            dict(name='T7 inside runoff', ways=['1494191150'], half_width=10.0, max_half=14.0, cones=False, surface='asphalt', paint=False),  # round 7b (note 45): painted edges like a real road; still open (owner, 19 Oct)
            dict(name='T11a shortcut', ways=['28825444'], half_width=6.0, surface='concrete', paint=True, mouth_cones=[]),
            # round 13 part B (owner note 135): the 'PWC lower hairpin' road (OSM 505454376, its T7 section; asphalt since round 11)
            # is no longer a zone: its OSM line loops round the small island's nose, so its strip lay over the island and over the
            # T7 inside runoff, and the two zones' shoulders painted over each other (the raw-ortho band of owner_135). On the 2026
            # captures it is the same open junction as the T7 inside runoff, which covers it; the paving round the island's nose is
            # the retextured ground of ortho_pave. Was:
            # # round 13 part B (owner note 135): paint False, as the T7 inside runoff (the same open junction)
            # dict(name='PWC lower hairpin', ways=['505454376'], half_width=5.0, surface='concrete', paint=False,
            # part_overrides=[dict(near=(38.1663500, -122.4621700), surface='asphalt',
            # src="round 11 (owner note 63: \"Weirdness at T7 where part of the track is not in-use. It should have the same texture as everything else\"): the road's T7 section (the normal T7, closed by the cones of t074) is the track's dark asphalt with its centre line on c20_s3960 / c20_s0000 (compare/sonoma/round11/win_t7mouth.png) and grey asphalt at onboard 1:14 (t074), not pale concrete")],
            # # (round 11: the round-7e override near (38.16555, -122.4607) matched no part of this road: part_overrides was
            # # read nowhere until now; that place is the 'drag strip past the T7 fork' road, declared asphalt above)
            # mouth_cones=[]),
        ],

        # a closed road's paving stops at its walls (the drag strip's NAIP width reached under the pit-straight wall)
        closed_roads_clip_walls=True,
        # the pit lane stops at the walls that bound it (round 4: the pit-in Jersey and outer wall; owner notes 15-16, 24)
        pit_lane_clip_walls=True,
        # bridges meet the banks: abutments and stair flights at both span ends (round 4, owner note 29)
        bridge_stairs=True,
        # round 13 (owner note 130, 23 Oct 2026: "There is a gray texture under the bridge. I believe this is the bridge in
        # satellite photos, but we have of course already modeled the bridge"): the ortho is filled from the surrounding
        # ground under every modelled structure's footprint (bridge decks and stairs, buildings, the structure kit's
        # stands and garages), grown by `margin` (bridge decks by `bridge_margin`: a raised deck's image leans in the NAIP)
        # round 13A fix (judge r13a N127 / N130 / N131: a pale gravel-looking ribbon under the tyre walls on both bridge banks
        # and under the new T1 tyre wall): every tyre / wall run too, a band 1.8 m either side of its line swept along the
        # sun's shadow over its height (the shadow vector from the footbridge deck's measured shadow)
        ortho_inpaint=dict(margin=1.5, bridge_margin=3.0, barriers=dict(kinds=('tyres', 'concrete', 'pitwall', 'armco'), half=1.8)),
        # round 13 part B (owner note 135, 23 Oct 2026: "This T7 complex with un-used track looks very bad ... Not a mismatch of
        # textures and geometries"): the NAIP ortho is of another year; its junction paint (arrows, curved and cross lines),
        # pale patches, parked trailers' shadows and the red O'Reilly island showed through the closed paved surfaces, and
        # paving left as ground read lighter than the same paving drawn as a zone. Inside the complex's outline the paving
        # is read on the 2026 captures (dark unsaturated asphalt with its white paint and red / white kerb blocks; NAIP rule
        # where no capture covers the paddock lot's west end), closed over parked vehicles, the raced track excluded, and
        # retextured: under the closed-road zones the track paving's own ortho tone, under paving left as ground that tone
        # graded as the road shader grades it (terrain_gain), so it reads as one surface; no paint is kept (the 2026 lines
        # are drawn: closed-road edge lines, the continuation's centre line, the kerb lines). Evidence and ledger:
        # compare/sonoma/round13b/LEDGER.md
        ortho_pave=dict(terrain_gain=(0.87, 0.78, 0.81), track_shoulder=5.0, regions=[
            # round 13A fix (judge r13a N126: "large angular black slivers and intersecting seams cross the new paving"): the
            # T1 paved runoff's ground image repainted in the track's paving tone, its outline the apron zone itself
            dict(name='T1 outside paved runoff', zone='T1 outside paved runoff', mask='all', fill='paving', exclude_track=0.3,
                 src='the apron of scenery.aprons (round 13A, owner note 126); c20_s1815 / c20_s1870 / c20_s1925: one dark asphalt '
                     'surface from the T1 edge to the drag-strip wall, no paint'),
            # round 13B second pass (judge r13b N135 PARTLY): the ground paving read browner and grainier than the road: its tone
            # calibrated on the same rendered still (turn_2290: road 112.9 / 111.3 / 123.0 against ground paving 101.5 / 94.3 /
            # 113.7 with the shared terrain_gain; ground_gain = terrain_gain x their ratio), a near-flat grain (1.0), the skipped
            # patches filled (mask not_ground: everything in the outline but the 2026 dirt, grass and trees is paving, so the trailers, the tent and their shadows go; holes up to 800 m2), the
            # repaint taken up to the track edge (exclude_track 0) and the first 1.5 m beyond it kept in the road's tone (mouths)
            dict(name='T7 complex paving', mask='not_ground', close=2.5, min_area=150.0, exclude_track=0.0, feather=20.0, clip_zones=True,
                 ground_gain=(0.97, 0.92, 0.88), grain=1.0, fill_holes=800.0, shoulder_keep=1.5,
                 # the outline follows the paddock lot's SW bank and the Chute's two sides (trees in deep shadow there read as asphalt)
                 latlon=[(38.1669221, -122.4644551), (38.1667604, -122.4638267), (38.1664370, -122.4633469), (38.1661316, -122.4630384),
                         (38.1658441, -122.4631983), (38.1655926, -122.4633697), (38.1654129, -122.4630841), (38.1656914, -122.4629470),
                         (38.1659878, -122.4627071), (38.1657992, -122.4613703), (38.1664729, -122.4611989), (38.1671916, -122.4613132),
                         (38.1672365, -122.4618844), (38.1670299, -122.4623986), (38.1669221, -122.4629127), (38.1675060, -122.4639981),
                         (38.1673712, -122.4645694)],
                 src='c20_s3850 / c20_s3905 / c20_s3960 / c20_s4015 / c20_s0000 paving (round 13 part B survey windows '
                     'compare/sonoma/round13b/survey/cap_*.png); onboard t072 / t074 / t076 plain dark asphalt in the junction'),
            dict(name="O'Reilly island: its dark painted surface", mask='all', fill='paving', ground_gain=(0.97, 0.92, 0.88), grain=1.0,
                 latlon=[(38.1667200, -122.4620273), (38.1667536, -122.4619530), (38.1667514, -122.4618502), (38.1667245, -122.4617702),
                         (38.1666840, -122.4617245), (38.1666077, -122.4616845), (38.1665538, -122.4616674), (38.1664909, -122.4616531),
                         (38.1664774, -122.4616445), (38.1665223, -122.4617359), (38.1665807, -122.4618387), (38.1666436, -122.4619359),
                         (38.1666975, -122.4620044)],
                 src="c20_s3960 / c20_s0000 at 0.05 m/px: the island's outline at the outer side of its red / white kerb blocks; its "
                     "inside a dark painted surface with white outlined O'REILLY lettering (the NAIP year's red island replaced)"),
            dict(name="small island nose: green painted band", mask='all', fill='#5aa586',
                 latlon=[(38.1665053, -122.4622238), (38.1665156, -122.4622135), (38.1665156, -122.4621175), (38.1664738, -122.4621861),
                         (38.1664927, -122.4622169)],
                 src='onboard t076: a mint-green band inside the red / white kerb at the island nose; c20_s3960: the dark green patch '
                     'at the nose (measured outline)'),
        ]),
        # round 13: the unmodelled-ground-lines gate (tools/track/gates/ground_lines.py; the owner's rule of 23 Oct 2026, "if we
        # are modeling textures in a long line on the ground, it's likely we are missing a feature"). Contrast 40 and 30 m
        # (16 / 20 flooded every track: 79 Sonoma, 113 Laguna findings, mostly paths, stand tiers and roof edges). On the
        # round-12 package it fails on the owner's own findings: the T1 tyre wall (s 216-224 right, from the run's head), the
        # T2 wall base (s 462-550 left), the T4 wall base and its missing end (s 819-856, 968-992 left). Every finding left
        # on this package was looked at on the 2026 captures and the ortho (contact sheets compare/sonoma/round13a/ground_lines_*.jpg):
        ground_lines=dict(contrast=40.0, min_len=30.0, dispositions=[
            # round 13 part B (owner note 135): the two T7-complex dispositions of round 13A (s 2170-2215 left, a NAIP-year
            # temporary structure in the paddock; s 2280-2315 left, the T7a paddock paving edge) are gone with the lines: the
            # paving there is retextured from the 2026 captures (ortho_pave)
            dict(side='left', s=(455, 560), tone='pale', what='lit concrete beside the T2 wall',
                 why="the wall stands on the ortho's dark line since round 13 (owner note 132); the pale strip 1.7-2.4 m beyond "
                     "it (profiles at s 414-544) is the lit walkway / wall top at the foot of the T2 stands, ground, not a barrier"),
            dict(side='left', s=(735, 830), tone='pale', what='lit concrete beside the T4 approach wall',
                 why="as at T2: the wall on the dark line (owner note 133), the pale strip 1.4-2.3 m beyond it is the walkway at "
                     "the foot of the T3a-T4 stands (profiles s 748-870)"),
            dict(side='left', s=(905, 985), tone='pale', what='lit concrete beside the T4-to-Chute wall',
                 why="the wall on the dark line (owner note 133); the pale strip 1.3-1.5 m beyond it (profiles s 872-944)"),
            dict(side='left', s=(2322, 2490), tone='dark', what='grass tone line beyond the T7a-T8 tyre lines',
                 why="the two tyre lines stand on the bank's dark band within 0.5 m (profiles s 2322-2476, ortho and c20_s0000 "
                     "/ c20_s0055); the line the gate reads is a fainter mowing / grass-tone edge 1-3 m beyond them"),
            dict(side='left', s=(3440, 3485), tone='pale', what='roof edge of the T10-T11 shed',
                 why="the shed's light roof edge (OSM 1019839490, the structure kit's shed) beside a tree row, 48-57 m left"),
            dict(side='left', s=(3190, 3460), tone='any', what='the T10-T11 boarded wall: its 2.5 m ad boards and their shadow',
                 why="the boarded wall (judged in rounds 10-12) is measured on the 2026 captures (c20_s0825..s1100); the NAIP "
                     "shows the boards' lit tops leaning away by relief and their 3 m shadow beyond the wall (the sun in the "
                     "WSW: the footbridge deck's shadow lies +6.5, +4.0 m from it), lines 2-6 m outside the modelled wall"),
            dict(side='right', s=(3335, 3395), tone='dark', what="shadow of the T11-approach wall and catch fence",
                 why="the round-11 wall with its 3.5 m catch fence on the right: with the sun in the WSW its shadow falls on the "
                     "track side, 1-4 m in front of the wall"),
            dict(side='left', s=(985, 1015), tone='dark', what='edge of the dirt paddock road by the Chute',
                 why='c20_s2695: a path edge with trucks parked along it, no barrier (the T4 wall ends at the Chute paving)'),
            dict(side='left', s=(3590, 3655), tone='dark', what='shadow of the pit garages roof',
                 why='the long garage roof (the structure kit\'s pit garages) casts its shadow on the paddock lane 26-40 m left'),
            dict(side='right', s=(2860, 2920), tone='pale', what='a pale strip 57-60 m right of the back straight',
                 why='a curved light concrete strip round an infield service yard behind the 9a buildings on the 2026 captures; at the '
                     'outer limit of the band, behind buildings; not checked against the onboard, not placed: for the owner'),
        ]),
        # round 13 (owner note 126, "I don't think the track bends back in like this at T1"): the edge there is the
        # painted course boundary (the kerb runs and the dotted block line, c20_s1870 / c20_s1925, unchanged), but the
        # asphalt beyond it is a paved runoff triangle on the outside of T1, from where the edge leaves the drag-strip
        # wall (s ~85) to the diagonal kerb at s ~185, bounded by the drag-strip wall and the paddock dirt; it was
        # ground texture, so the course looked as if it narrowed. Measured by the apron walker on the package ortho (the
        # 2026 captures are label-masked over most of it and their warm asphalt reads as the paddock dirt's colour)
        aprons=[('T1 outside paved runoff', 'right', 84, 186, 'paved runoff triangle beyond the T1 right edge to the drag-strip '
                 'wall and the paddock dirt (c20_s1815 / c20_s1870 / c20_s1925; owner note 126)',
                 # wider than a label-free capture covers: walked on the package ortho. Round 13A fix (judge r13a N126, the
                 # drag-strip wall at its far side read 0-0.2 m tall instead of ~0.8 m): ground=True, level with the road at the
                 # edge, then on the lidar ground (the plane from the edge stood 0.6-0.8 m above the wall's base)
                 dict(source='ortho', max=40.0, ground=True, ground_blend=5.0, smooth=5.0))],   # smooth: no folded strip (dark wedges)
        # containment gate: paved surfaces the cars can really reach across open ground (no barrier in the captures or the
        # onboard), each with its evidence; everything else must be behind a barrier or a cone line
        gates=dict(
            # round 13 (the run-gaps gate): holes in a barrier line that stay, each with its evidence
            openings=[dict(latlon=(38.1583683, -122.4519388), why='T11 hairpin outer wall (south), parts 1 / 2, 14.4 m apart at s ~3674, '
                           '18 m left: the lidar ground steps 1.0 m in 2 m across the hole (a joined wall fails the wall-tops gate, '
                           '0.51 m per m) and c20_s1320 cannot settle whether the dark line there is the wall or the level change; '
                           'left open for the owner (round 13)')],
            allowed=[
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
            # round 7e (owner note 57): the drag strip's continuation past the fork is paved now; its mouth is closed by the
            # pylon line, and these stretches see it across open ground (no barrier in the captures or the onboard)
            dict(target='drag strip past the T7 fork', side='right', a=(38.1651699, -122.4602071), b=(38.1664136, -122.4623056),
                 why='T7 road, right (from the fork, beside the pylon line\'s track end): open grass between the T7 road and the drag strip continuation, no wall (round 7, owner note 36: t062 / t064 / t066 show grass right off the edge and no wall; c20_s3630 / c20_s3685 / c20_s3740)'),
            dict(target='drag strip past the T7 fork', side='right', a=(38.1667539, -122.4619088), b=(38.1662644, -122.4615375),
                 why='T7a exit to T8, right: open grass and paddock down to the strip\'s NW end (onboard t076 / t078: no barrier on the right; c20_s3960 / c20_s4015)'),
            dict(target='drag strip past the T7 fork', side='right', a=(38.1655508, -122.4600987), b=(38.1654029, -122.4598397),
                 why='8a, right: the crossover road to the drag strip (OSM raceway 380830038) meets 8a in the gap between the measured T8-8a concrete wall (ends s ~2510) and the 8a station wall with its black tyre facing (begins s ~2515, c20_s0110 / c20_s0165; round 8)'),
            # round 13 part B: the 'PWC lower hairpin' zone is gone (closed_roads above); the rays it stopped now cross the open junction
            # to the drag strip's continuation: the same open paving (c20_s3905 / c20_s3960 plain asphalt between the islands; onboard
            # t074 / t076 cones across the short-T7 road and delineator posts on the course edge, no barrier between)
            dict(target='drag strip past the T7 fork', side='right', a=(38.1664317, -122.4624026), b=(38.1668365, -122.4618640),
                 why='inside T7 / 7a (s ~2208-2278): the open junction between the T7 island, the small island and the O\'Reilly island is paving to the continuation, no barrier (c20_s3905 / c20_s3960; onboard t074 / t076: cones and posts only; round 13 part B, was the PWC lower hairpin zone)'),
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
        # round 10 (judge r9, the pit-out lane surface): s 150-222, the pit-out lane past the K-rail beside the double yellow,
        # is one plain surface in the 2025 pit-out video (t0304: uniform pavement, no markings but the double yellow and its
        # cones). Round 9's stills showed pale patches there from two causes, found by hiding meshes in pose_walk.ts: (1) the
        # TRACK ribbon's left shoulder rows (dirt look) rising through the lane (hiding the 'track' mesh made the lane
        # uniform) -> scenery.track_shoulder_cut; (2) the app's rule pit-box lines, drawn every 10 lane stations along the
        # whole of Sonoma's one-part lane -> `no_box_lines` here
        lane=dict(source='osm', match_track_tone=dict(k=0.5, paint=0.97),
                  no_box_lines=[dict(s=(150, 222), why='t0304: no box lines in the pit-out lane past the K-rail')]),
        # geometry (round 5): a wall with latlon is built here; one that is a declared scenery wall names it (declared=...)
        walls=[
            dict(side='left', s0=4000, s1=30, h=0.6, material='pitbox_wall', name='pit lane, left: low white pit-box wall (round 5)',
                 src='inventory pit rows s 4010 / 4060 / 20: low white pit-box wall with box numbers (24of8fjjAug 4:48-4:56); measured on c20_s1595 / c20_s1650 / c20_s1705: the bright double line between the boxes and the crew area, 27 m left of the centre, wall_measure 100 % picked, rms 0.03-0.07 m',
                 latlon=[(38.1607186, -122.4539335), (38.1607745, -122.454023), (38.1608304, -122.4541124), (38.1608862, -122.4542019),
                         (38.1609419, -122.4542916), (38.1609976, -122.4543812), (38.1610533, -122.4544708), (38.1611091, -122.4545604),
                         (38.1611648, -122.45465), (38.1612207, -122.4547395), (38.1612764, -122.4548291), (38.1613294, -122.4549142),
                         (38.161335, -122.4549232), (38.1613905, -122.455013), (38.1614464, -122.4551025), (38.1614997, -122.4551873)]),
            dict(side='right', s0=4000, s1=85, h=1.1, material='concrete', declared='pit straight, pit-lane side: front-straight wall to the island',
                 src='inventory pit rows s 4010 / 4060 / 20: white concrete pit wall with GEICO boards (24of8fjjAug 4:48-5:00); Street View 5MY4xR9O7etAXEHnZCVnGQ 1.08 m; round 8 (owner note 59): continuous with the K-rail (round 9: two runs joined at the island, s ~85)'),
            dict(side='right', s0=85, s1=158, h=0.85, material='jersey', declared='pit straight, pit-lane side: K-rail from the island to the blend line',
                 src='inventory pit row s 100: the pit-wall nose, white Jersey segments curving right with the track (24of8fjjAug 5:00, t0300; 0.9 m jersey-ref); round 8 (owner note 59): continuous to s ~158, where the double yellow blend line starts'),
            dict(side='left', s0=150, s1=170, h=1.0, fence=1.8, material='concrete', declared='pit-out lane, paddock side: wall with the catch fence (round 9)',
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
                      '1019836718', '1019839490'],
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
            # pit-exit building (the "Farmers" end): grey metal walls, low mono-pitch roof rising to the track side, red roof
            # edge. Round 9 (judge r8, pit-exit building): 24of8fjjAug t0300 (reference only) shows its end from the pit lane:
            # the red-edged roof sloping from low (paddock side) to high (track side), grey cladding above a continuous DARK
            # frontage band (~2.0-4.0 m, the low end's eave at its top) and a lighter strip below; no blue window rows and no
            # red mid-wall band (the round-6 windows and trim band are dropped). Heights stay the lidar's (4.2 m to 8.2 m: the
            # frame's high end stands ~2.2 x the low end, the lidar 1.95 x). Colours: the frame's shaded east face reads rgb
            # (65, 66, 75) above, (20, 21, 30) in the band, (57, 58, 63) below (drawn lifted for the shading: #6f7277, #1c1d24)
            dict(type='garage', name='Pit-exit building', osm='1019839174', eave=4.2, ridge=8.2, mono='track',
                 wall='#6f7277', roof='#8e9396', trim='#b23a2e', trim_h=0.0,
                 band=dict(z0=2.0, z1=4.0, color='#1c1d24'),
                 # round 10 (judge r9, frontage): the lane-side (track) face in bays: an upper storey of glazed bays with pale
                 # frames under the red roof edge (t0304: glass in white-framed bays, ~3.5 m apart against the 3 m mesh
                 # panels) over the dark band, and ground-level openings every other bay (t0300: a grey door in the end's
                 # lower part, the frontage open below the band); the wall between the glazing reads as the framing
                 windows=dict(side='track', pitch=3.6, w=3.0, h=2.4, z=4.5, color='#8c9eab'),
                 doors=dict(side='track', pitch=7.2, w=2.6, h=1.9, color='#3d4248'),
                 src='OSM 1019839174; c20_s1870 (ribbed grey roof with a red edge, red round canopy beside); onboard '
                     'RAZip6S84CM 0:04 (red roof edge, glazed front, grey walls; inventory s 91 left); 2025 24of8fjjAug '
                     '4:56 (red roof line at the pit exit); round 9: 24of8fjjAug t0300 (the end face: red-edged mono roof, '
                     'grey cladding, a dark frontage band, no window rows); round 10: t0304 (the lane-side face: glazed upper bays in '
                     'white frames, openings below), t0300 (a door in the lower part); Street View owner_25 (2011)',
                 h_src='lidar: roof from 4.2 m (paddock side) to 8.2 m (track side); t0300: the high end ~2.2 x the low end'),
            # round 9 (judge r8, pit-exit building row): the round red canopy on a raised terrace at the building's west end,
            # beside the pit-out lane. Centre and size on c20_s1870 (a red disc 10 m across, ENU centre (78.5, -92.5), its open
            # centre ~2.5 m dark; median red rgb (169, 89, 77)); heights from the 2017 lidar (DSM - DEM over the disc: the roof
            # 6.3 m at its west rim to 8.8 m at its east rim, i.e. ~7.6 m at the centre, tilted ~14 deg up toward the east; the
            # open centre reads 2.9-3.2 m, the terrace under it); 24of8fjjAug t0304 (reference only): the ring roof of red
            # panels on a steel ring, open in the middle, above the catch fence beside the building
            dict(type='canopy', name='Pit-exit round canopy', at=(38.1618691, -122.4567031), d=10.0, h=7.6, hole=2.5,
                 tilt_deg=14.0, tilt_bearing=90.0, color='#a9594d', post_color='#9aa0a6', posts=6,
                 deck=dict(h=3.0, d=10.5, color='#b9b6ae'),
                 # round 10 (judge r9, the open terrace): the terrace is a slab on posts, open beneath (t0304: open space and
                 # posts under the ring), with its stair leaving south from its west half (c20_s1870 / c20_s1925: a 2.5 m
                 # hatched flight from under the canopy southward, ~8 m; lidar 2017 1.0-1.7 m along it, x ~76, y -98..-106)
                 deck_posts=8, stair=dict(bearing_deg=180.0, w=2.5, run=8.0, lateral=1.8),
                 src='c20_s1870 (the round red canopy beside the pit-exit building: centre, 10 m disc, open centre); lidar 2017 '
                     '(canopy surface 6.3-8.8 m, terrace 2.9-3.2 m through the open centre); 2025 24of8fjjAug t0304 (red ring '
                     'roof on a steel ring with an open middle, on a raised terrace beside the building; round 10: open beneath, on '
                     'posts); c20_s1870 / c20_s1925 (round 10: the stair flight south from the terrace)',
                 h_src='lidar 2017 DSM - DEM over the disc (1 m grid): 6.3-8.8 m, rising to the east; 2.9-3.2 m in the open centre (the terrace)'),
            # round 6 (orchestrator S2): the long single-storey shed directly behind the T10-T11 boarded wall (left of s
            # 3478-3700): the OSM box drew as a two-storey glazed block towering over the wall; the onboard 1:54-1:58 shows
            # only the 5.2 m boarded wall with the hills behind (the shed's roof sits at the boards' top)
            dict(type='garage', name='T10-T11 shed behind the boarded wall', osm='1019839490', eave=5.5, ridge=5.6,
                 wall='#d9d8d2', roof='#c9c8c2', trim='#d9d8d2', trim_h=0.0,
                 src='OSM 1019839490 (a 12 x 250 m rectangle, 3016 m2); c20_s1100 / c20_s1155 / c20_s1210: a long flat light '
                     'roof directly behind the boarded wall; onboard RAZip6S84CM 1:54-1:58 (frames t114-t118): only the '
                     'boarded wall (5.2 m) and the hills behind, no storeys or glazing above it',
                 h_src='lidar 2022-24 over the outline: p50 5.5 m, p90 6.2 m (flat roof)'),
            # round 6 (owner O1 / orchestrator F1): the scoring tower on the Carousel hill (onboard 0:04-0:06 ahead-right on the
            # hill past T1, 0:52-0:56 beside the Carousel): a tall slender dark column on a white-rimmed square base
            dict(type='scoring_tower', name='Scoring tower (Carousel hill)', at=(38.1626443, -122.4577737), heading_deg=135.0,
                 w=4.6, d=4.6, h=27.6, color='#45474a', plinth=dict(w=5.6, h=0.8, color='#e3e1db'),
                 head=dict(h=1.5, w=4.9, d=4.9, color='#2e3033'),
                 src='lidar 2022-24: an isolated 27.5-27.9 m spike (DSM - DEM), 33 cells over 10 m in a 5.7 x 4.9 m rectangle at '
                     '(-15.2, -6.2) ENU, axis 135 deg, nearest track s 1584 (50 m right); c20_s3300 / c20_s3245: a ~5.6 m '
                     'white-rimmed square base with a long 4-5 m wide shadow to the north-west (the capture puts the base ~10 m '
                     'SE of the lidar top; the lidar position is used, as for the masts); onboard RAZip6S84CM 0:06 (t006): a '
                     'tall slender dark grey rectangular column on the hill; 0:50-0:52 (t050, t052) closer: a straight column ~1:5 with a '
                     'darker capped top, no head wider than the column (the orchestrator\'s pylon description has a wider '
                     'position-board head; the frames show only the cap, modelled 0.3 m proud; the Alamy reference 2R6P462 is '
                     'no longer on the site)',
                 h_src='lidar spike 27.5-27.9 m above the DEM; width / height ~1/6 in the t006 frame (4.6 m)'),
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
                 colors=['#23439a'], panel=3.0, names=[('RESTART ZONE', '#23439a', '#ffffff'), ('GEICO', '#23439a', '#ffffff')],
                 src='2025 24of8fjjAug 4:48 (blue board band along the pit wall top, RESTART ZONE panel; inventory pit '
                     'row s 4010)', h_src='about 0.8 of the 1.1 m wall below it (24of8fjjAug 4:48)'),
            dict(type='boards', name='Pit wall boards (green)', side='left', s0=4060, s1=4098, lat=(4.0, 15.0), h=0.85,
                 colors=['#3aa635'], panel=3.0, names=[('EchoPark', '#3aa635', '#ffffff')],
                 src='onboard RAZip6S84CM 2:15 (green panels on the pit wall at the line, both sides; t134: EchoPark on the green wrap)',
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
            # hillside terraces: the rows (scenery.terraces, measured footprints since round 6) dressed with bench strips,
            # stair aisles with hand rails and the shade roofs the onboard shows on top. Round 6: benches and aisles in
            # concrete / bleacher greys (the orchestrator's sheets: T7a read as a brown wedge); shade fractions along the
            # front line (back straight: the dark roofs at s 2897-2915 and 2932-2940 on c20_o0495 / c20_o0550); the bench is a
            # 0.15 m concrete seat lip, not a 0.4 m bench (onboard 0:14 / 0:29 / 1:31: bare concrete steps with a thin dark
            # line per row; 0.4 m benches hid the rows from the track)
            dict(type='terrace_dress', terrace='above T2', bench=dict(color='#b3b1aa', h=0.15, depth=0.45),
                 aisles=dict(pitch=45.0, w=1.4, color='#c4c1b8', rail='#8c9196'),
                 shades=[dict(f0=0.0, f1=0.12, rows=6, h=2.8, color='#5b5f63')],
                 src='onboard RAZip6S84CM 0:14-0:16 (concrete terraces, stair aisles with hand rails, a dark shade roof on '
                     'top at the far end); Street View H9xspk4q_OoFIjVDhaMzDA'),
            dict(type='terrace_dress', terrace='T3a-T4', bench=dict(color='#b9b5ab', h=0.15, depth=0.45),
                 aisles=dict(pitch=40.0, w=1.4, color='#cfccc4', rail='#8c9196'),
                 src='onboard RAZip6S84CM 0:26-0:30 (light concrete terraces, ~20 rows); Street View nA1oaDXwADSI7x-Pa-j4Ow'),
            dict(type='terrace_dress', terrace='T7a hill', bench=dict(color='#b5b2aa', h=0.15, depth=0.45),
                 aisles=dict(pitch=40.0, w=1.4, color='#c8c6bf', rail='#8c9196'),
                 src='onboard RAZip6S84CM 1:12-1:14 (tan terraces, fence and light masts on top); Street View '
                     'J6fsnW4hj4xCjQLzrgRGzA (owner_8: stepped rows with stair aisles)'),
            dict(type='terrace_dress', terrace='back straight / 9a', bench=dict(color='#b0aea7', h=0.15, depth=0.45),
                 aisles=dict(pitch=40.0, w=1.4, color='#c4c1b8', rail='#8c9196'),
                 shades=[dict(f0=0.52, f1=0.58, rows=5, h=2.8, color='#5b5f63'), dict(f0=0.62, f1=0.66, rows=5, h=2.8, color='#5b5f63')],
                 src='onboard RAZip6S84CM 1:30-1:34 (concrete terraces with shade roofs / covered stands on top); Street '
                     'View xkSrqJ5RaN9WFLncaiqaug; captures c20_o0495..o0550 (dark roofs at the top edge)'),
        ]),
    # ---------------------------------------------------------------- app registry (src/scoreboard/config.ts)
    app=dict(short='Sonoma', pace='cars/field/sonoma/pace.json'),
)
