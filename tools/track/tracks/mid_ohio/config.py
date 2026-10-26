"""Mid-Ohio, Lemons 13-turn outer loop; stage-1 geometry checkpoint accepted 26 Oct 2026 (round 3, no red marks).

Owner clarification 25 Oct 2026: follow the black numbered circuit in the
supplied Lemons map, retaining T2 and the full back straight. Skip the grey
inner chicane only. Neither of the two short east/west crossovers is driven.
Sources and known 2019/2024 survey mismatch: sources.json beside this file.
No scenery, package publication, or downstream work before edge acceptance.
"""
CONFIG = dict(
    id='mid_ohio', name='Mid-Ohio Sports Car Course', direction='cw',
    origin=(40.689, -82.636),
    osm_bbox=(-82.646, 40.678, -82.625, 40.699),
    osm_file='osm/osm.xml',
    loop_ways=['1315957513', '1315957512', '1315957511',
               '444205375', '1315957515', '1315957514'],
    pit_lane_way='Pit Lane',
    dem_tiles=[
        'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/'
        'OH_Statewide_Phase1_2019_B19/TIFF/'
        'USGS_1M_17_x36y451_OH_Statewide_Phase1_2019_B19.tif'],
    lidar_ept='https://s3-us-west-2.amazonaws.com/usgs-lidar-public/OH_Statewide_Phase1_3_2019/',
    lidar_survey='OH_Statewide_Phase1_2019_B19',
    dem13='https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n41w083/USGS_13_n41w083.tif',
    logger_dir=None,
    # Two white timing stripes by starter stand, test_sf_google.jpg (25 Oct 2026),
    # centre pixel (439, 273), nominal z20 centre (40.6894, -82.6349).
    # Common Google-minus-NAIP shift (-0.60,0.00) m applied to the timing point.
    start_finish_latlon=(40.689491, -82.6352688918),
    # OSM corner anchors located against the owner's numbered map; curvature
    # peaks are solved by the pipeline, never hand-edited in the package.
    corners=[
        ('T1', None, 'left', None, 40.6892751, -82.6389541),
        ('T2', 'Keyhole', 'right', None, 40.6838814, -82.6396135),
        ('T3', None, 'right', None, 40.6883318, -82.6402738),
        ('T4', None, 'right', None, 40.6924266, -82.6379702),
        ('T5', 'Madness', 'left', None, 40.6920596, -82.6367073),
        ('T6', None, 'right', None, 40.6935527, -82.6362479),
        ('T7', None, 'left', None, 40.6936645, -82.6349499),
        ('T8', None, 'right', None, 40.6945062, -82.6338012),
        ('T9', None, 'right', None, 40.6945603, -82.6324936),
        ('T10', 'Thunder Valley', 'right', None, 40.6918825, -82.6321417, 90),
        ('T11', None, 'left', None, 40.6907241, -82.6330139),
        ('T12', 'Carousel', 'right', None, 40.6887509, -82.6327886),
        ('T13', None, 'left', None, 40.6893954, -82.6336601),
    ],
    # Lap length (owner's decision, 26 Oct 2026 evening: "the Buttonwillow rule"). The published 2.258 mi (3633.934 m;
    # operator midohio.com news 1084, Wikipedia, IMSA: the 13-turn "straight option" between T1 and the Keyhole) is
    # INFORMATION, not a gate: no source states the line or method it is measured on, and the built centre is -1.0 %
    # against it while the scale is confirmed to 0.1 % (compare/mid_ohio/round3.md "Length", r3/scale_check.py).
    # Independent measures of THIS loop instead: (1) the raw stitched OSM loop of loop_ways (3620.2 m; the built centre
    # -0.63 %), a gate here (osm_tol 1 %, as Buttonwillow's manifest check); (2) the N837 onboard's (OJaBJz18xEo,
    # 15 Apr 2026) Catalyst speed readout integrated over one lap between two S/F crossings (compare/mid_ohio/round4.md
    # "Speed-integrated lap"), recorded in the ledger beside the OSM check.
    loop_check=dict(n_min=3500, n_max=3750, official_m=None, osm_tol=0.01, elev_min=0, elev_max=100),
    captures=dict(clean_dir='compare/mid_ohio/satellite_clean', clean_index='tiles.json',
                  mpp=0.1132013752, common_shift=None, clean_mask='clean'),
    sources=dict(
        onboard=[], pit_lane_video=[], streetview='compare/mid_ohio/streetview.md',
        lemons_layout='https://registration.24hoursoflemons.com/userfiles/races/24HoL__TrackMap_Mid-Ohio.png'),
    stations_ref=(3595, 3589.22),
    centre=dict(pit_merge=False, pit_exit=dict(
        src='c20_s0200..c20_s0320 and 2026 N837 onboard t14/t16: hatched blend then raised red/white T1 kerb separates pit lane from course; automatic OSM lane-merge extent includes the inactive inside apron'),
        # Round 3 (owner's round-2 review, 26 Oct 2026: "Other than the pit straight, and the transitions onto and off
        # it, the fits were good"): a LOCAL refit (SKILL 1.4, Sonoma round 11 / 14B) over the stations his red covers
        # (3425..576 of the round-2 frame, through S/F) with ~30 stations beyond it; the global fit converges first
        # exactly as round 2 (no other key changed), then only this window is refitted with his red, everything
        # outside it held in world position (compare/mid_ohio/round3.md, held-edge table). restation 'index',
        # refit_final and centre_smooth as Sonoma round 14B part 1b (window-only options)
        restation='index',
        local=dict(window=(3395, 610), blend=15, refit_final=True, centre_smooth=1.0,
                   why='round 3: pit straight and its transitions from the owner\'s round-2 red (spline.owner_edges, owner/r2)')),
    # Owner's second-pass instruction: race edge at asphalt-to-kerb boundary,
    # all kerb colours; supersedes skill's outer-limit convention for this track.
    spline=dict(kerb_edge='inner', report_width=(12.192, 12.192),
                kerb_search=[('left', 285, 360, (-6, 1), 'c20_s0200..c20_s0320: inside kerb lies about 2–3m inside automatic apron boundary')],
                mask=[('left', 210, 255, 'c20_s0160/c20_s0200: overhead bridge occludes the painted boundary')],
                # Round 3: the owner's round-2 red (compare/mid_ohio/owner_review_r2/edge-marks.json, sha256 fa809758...,
                # 13 windows, 46 red / 50 green strokes) read from its vectors (compare/owner_edges.py --by-stroke
                # --vector-origin continuous, frames from owner_review_r2/frames.json, on tools/track/out/mid_ohio_r2) into
                # owner/r2/<window>.json and merged (owner/r2/merge.sh: compare/owner_merge.py with the recorded overlap
                # dispositions, --drop) into owner/r2/merged.json. His red sits on the asphalt side of every kerb (the
                # inner-kerb convention above): no kerb_inside shift. Used in the local refit only (centre.local).
                owner_edges=[dict(file='owner/r2/merged.json', chains=False, reach='drawn', project='foot', lo=3425, hi=576, local=True,
                                  windows=['owner/r2/w_s0000.json', 'owner/r2/w_s0125.json', 'owner/r2/w_s0250.json',
                                           'owner/r2/w_s0375.json', 'owner/r2/w_s0500.json', 'owner/r2/w_s3375.json',
                                           'owner/r2/w_s3500.json', 'owner/r2/close_s0220.json', 'owner/r2/close_s0320.json'],
                                  src='owner round-2 review red (compare/mid_ohio/owner_review_r2/edge-marks.json; owner/r2/merged.json), '
                                      'last corner exit / pit entry s ~3425 through S/F, the pit straight, bridge approach, T1 and T1 exit to s ~576')],
                # D5 APPROVED (owner, 26 Oct 2026 evening): the T1-exit right edge follows the kerb line; his round-two
                # arc (w_s0500, s 427-475) is set aside with his approval (owner/r2/merge.sh, round3.md D5).
                owner_measure='foot'),
    prior=dict(bridge_win=35),
    features=[
        ('left', 285, 360, 'kerb', 'c20_s0200..c20_s0320; N837 onboard t16: raised red/white T1 inside kerb separates pit exit, use its track-side band, not grass beyond apron'),
        ('right', 365, 480, 'kerb_yellow', 'c20_s0280..c20_s0440; continuous yellow T1 exit kerb, track-side painted limit'),
        ('left', 1010, 1120, 'kerb_yellow', 'c20_s0960..c20_s1080; continuous yellow T2 exit kerb, track-side painted limit'),
    ],
    shapes=[], straights=[], repave_fixes=[],
    # T4 2024 reconstruction (owner's decision, 26 Oct 2026 evening: "apply the bank-halving rule, flagged"). The 2019
    # lidar predates it. Operator, midohio.com news 1084 (19 Dec 2024): "banking was reduced from 4 to 2 degrees by
    # removing 520 feet of track surface and excavating up to 18 inches along the outside edge"; "the existing apex
    # curbing kept in place at driver's right"; "both sides of the track were regraded starting 400 feet before the
    # turn". Rule (profile_bank.py): over 520 ft (158.5 m) centred on the measured 2019 bank peak, the chord bank toward
    # the inside (right) halved about the inside edge, crown kept, a smoothstep over the 400 ft (121.9 m) before it.
    # Every element below 'assumptions' is an ASSUMPTION (compare/mid_ohio/round3.md T4 table; round4.md placement).
    profile_bank=[dict(
        name='T4 2024 reconstruction', anchor_latlon=(40.6924266, -82.6379702), search_m=40, inside='right',
        length_m=158.496, approach_m=121.92, exit_m=0.0, factor=0.5, shoulder_m=2.0, lateral_fade=6.0,
        src='midohio.com news 1084 (19 Dec 2024, Kokosing, 14 Oct - 8 Nov 2024); 2019 lidar bank 3.9-4.4 deg over s ~1950-1975 '
            '(round3.md); placement checked against the 2025 INDYCAR 360 lap (e25u_vjn1uM) and the 2026 IndyCar onboards '
            '(9Drr1VkE1_U) through T4 (round4.md)',
        why='the 2019 survey predates the 2024 T4 rebuild that halved its banking; the measured section rotated about the '
            'kept inside (apex kerb) edge instead of an invented height',
        assumptions=[
            'the rebuilt 158.5 m lies symmetric about the 2019 bank peak (the operator gives the length, not the position)',
            'the inside edge keeps its 2019 elevation (footprint and apex curbing kept: plan, not height)',
            'the chord bank toward the inside is halved everywhere in the interval (4 to 2 deg is the ratio at the peak); '
            'an adverse slope (T5 approach, from s ~2005) is left as measured',
            'the outside edge drops by the rotation (excavation = lowering; magnitude agrees with "up to 18 inches")',
            'smoothstep transition over the 400 ft regraded approach; no exit taper (the measured bank toward the inside '
            'is zero by s ~2005, inside the core)',
            'crown (the section shape about its chord) and the inside edge longitudinal profile unchanged',
            'run-off: the outside edge change held 2 m beyond the edge and faded over 6 m back to the 2019 ground (the '
            'operator\'s raise has no numbers)'])],
    profile_gaps=[dict(
        name='T1 approach footbridge', latlon=(40.689589, -82.638024),
        half_m=15, fit_m=7, lateral_fade=6,
        src='c20_s0160/c20_s0200; EPT3 class2+17 deck at road s230–236, 4.5m over road; clean road at s215–224 and242–251',
        why='Deck returns mislabeled ground hide the road. Interpolate only the occluded short profile from measured adjacent road heights/slopes; no assumed height.'),
    ],
    scenery=dict(brake_board_corners=[], corner_boards=False, flagstand=False,
                 pit_wall=dict(rule=False)),
    app=dict(short='Mid-Ohio', pace='cars/field/mid_ohio/pace.json'),
)
