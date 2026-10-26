"""Mid-Ohio, Lemons 13-turn outer loop; stage-1 geometry checkpoint accepted 26 Oct 2026 (round 3, no red marks).

Owner clarification 25 Oct 2026: follow the black numbered circuit in the
supplied Lemons map, retaining T2 and the full back straight. Skip the grey
inner chicane only. Neither of the two short east/west crossovers is driven.
Sources and known 2019/2024 survey mismatch: sources.json beside this file.
No scenery, package publication, or downstream work before edge acceptance.
"""
# round 7: the red stacked armco's colour (sunlit, N837 t016 / t022) and the red / white kerb profile (round7.md)
ARMCO_RED = '#8c4a42'
KERB_RAISED = dict(height=0.05, face=0.25, back=0.3)   # OWNER QUESTION (round 7): the red / white kerb height is NOT measured (no frame resolves it); 5 cm is Sonoma's driven profile, declared; the owner judges it in the drive

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
    # ---------------------------------------------------------------- stage 3 (round 7, 26-27 Oct 2026): scenery from the evidence
    # (compare/mid_ohio/round7.md: the object manifest with the evidence per object, the kerb table, the gate table)
    scenery=dict(brake_board_corners=[], corner_boards=False, flagstand=False,
        pit_wall=dict(rule=False),
        # KERBS (step 1). The race edges are the asphalt-facing face of every kerb (owner's decision 2), so every kerb lies in
        # a band BEYOND the edge: kerb.inside False (build_scenery: scenery.json kerbs.inside; the physics' kerbBandCentre,
        # the app's buildKerbs and terrainGates read it) and each strip's measured `off` / `width` from the edge outward.
        # Widths and extents from the capture band scan (compare/mid_ohio/r7/kerb_scan.py -> kerb_scan.json, kerb_cfg.py);
        # colours from the 2025-26 footage: the sunlit 2025 360 lap (t054 left, t130 right: yellow (224-234, 173-181, 11-23), red
        # (185-187, 75-84, 58-66); IndyCar t022 yellow (227, 193, 68)) over the overcast N837 (t042: (200, 164, 62) / (201, 64, 58));
        # the app's kerb paint fades every colour 8-33 % toward concrete, so the sunlit values are used (judge r7 F1: the
        # round-7 first build's N837 palette read washed out); types: the red / white blocks are a
        # low raised concrete kerb (N837 t016 / IndyCar t030: a rounded outer face shows, the yellow ones show none); its height is
        # NOT measured (no frame resolves it): declared 0.05 m over a 0.25 m face, Sonoma's 5 cm profile that drives), the
        # yellow and the red outer bands flush paint (N837 t042, 360 t036 / t054: no face, the ground beyond at the same level)
        kerb=dict(inside=False, width=1.5, stripe_m=1.0, require_colour_src=True, run_max_step=0.1,
                  # block length 1.0 m (c20_s0880: Keyhole blocks 10 px at 0.1 m/px each colour)
                  palettes={'rw': ['#c8443c', '#e2ddd4'], 'yel': ['#e2b21c', '#e2b21c'], 'red': ['#c8443c', '#c8443c']}),
        kerbs_declared=[
            dict(name='T1 inside (apex) kerb', side='left', a=(40.6893731, -82.6387078), b=(40.6890514, -82.6390576), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED,
                 colour_src='e25u_vjn1uM@32.0 (T1 inside kerb, red/white, flat; s 295, direct); OJaBJz18xEo@16.0 (T1 inside kerb, red/white; s 339, direct); 9Drr1VkE1_U@90.0 (T1 kerb, red/white; s 341, corroborate)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s0240, c20_s0280: redwhite paint s 299-348 (50 m) beyond the left race edge, band median 2.30 m (p25-p75 2.27-2.50); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T2 (Keyhole) exit kerb', side='left', a=(40.6843447, -82.6402211), b=(40.6849879, -82.6402483), off=0.53, width=1.05,
                 colors='yel', pattern='plain',
                 colour_src='9Drr1VkE1_U@102.0 (T2 exit kerb, yellow; s 1035, corroborate); e25u_vjn1uM@54.0 (T2 exit kerb, yellow, flat; s 1044, direct); 9Drr1VkE1_U@34.0 (T2 exit kerb, yellow with red band; s 1050, direct); OJaBJz18xEo@42.0 (T2 exit kerb, yellow with red band; s 1066, direct); 9Drr1VkE1_U@168.0 (T2 exit kerb, yellow; s 1074, corroborate); e25u_vjn1uM@56.0 (yellow exit kerb ends; s 1101, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s0960, c20_s1000, c20_s1040: yellow paint s 1030-1102 (72 m) beyond the left race edge, band median 2.20 m (p25-p75 2.10-2.20); yellow band 0.00-1.05 m beyond the edge'),
            dict(name='T2 (Keyhole) exit kerb, red outer band', side='left', a=(40.6843447, -82.6402211), b=(40.6849879, -82.6402483), off=1.6, width=1.1,
                 colors='red', pattern='plain',
                 colour_src='9Drr1VkE1_U@102.0 (T2 exit kerb, yellow; s 1035, corroborate); e25u_vjn1uM@54.0 (T2 exit kerb, yellow, flat; s 1044, direct); 9Drr1VkE1_U@34.0 (T2 exit kerb, yellow with red band; s 1050, direct); OJaBJz18xEo@42.0 (T2 exit kerb, yellow with red band; s 1066, direct); 9Drr1VkE1_U@168.0 (T2 exit kerb, yellow; s 1074, corroborate); e25u_vjn1uM@56.0 (yellow exit kerb ends; s 1101, direct)',
                 src="kerb band scan (r7/kerb_scan.py) on c20_s0960, c20_s1000, c20_s1040: yellow paint s 1030-1102 (72 m) beyond the left race edge, band median 2.20 m (p25-p75 2.10-2.20); red outer band 1.05-2.15 m beyond the edge (red share 0.93 at the band's outer side)"),
            dict(name='T4 exit kerb', side='left', a=(40.6923722, -82.6375099), b=(40.6922377, -82.637211), off=0.72, width=1.45,
                 colors='yel', pattern='plain',
                 colour_src='9Drr1VkE1_U@48.0 (yellow kerb; s 1989, direct); e25u_vjn1uM@78.0 (yellow kerb; s 1995, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s1920, c20_s1960: yellow paint s 2013-2042 (29 m) beyond the left race edge, band median 1.30 m (p25-p75 1.20-1.40); yellow band 0.00-1.45 m beyond the edge'),
            dict(name='T5 (Madness) apex kerb', side='left', a=(40.6921153, -82.6367477), b=(40.6923372, -82.6363622), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='9Drr1VkE1_U@184.0 (T5 kerb, red/white; s 2070, corroborate); 9Drr1VkE1_U@50.0 (T5 kerb, red/white; s 2082, direct); e25u_vjn1uM@82.0 (T5 apex kerb, red/white; s 2100, direct); OJaBJz18xEo@72.0 (T5 apex kerb, red/white; s 2105, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2040, c20_s2080: redwhite paint s 2087-2138 (51 m) beyond the left race edge, band median 1.70 m (p25-p75 1.50-1.80); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T7 exit / T8 approach kerb', side='left', a=(40.6937377, -82.6353788), b=(40.6937718, -82.6348462), off=0.78, width=1.55,
                 colors='yel', pattern='plain',
                 colour_src='e25u_vjn1uM@92.0 (yellow kerb; s 2371, direct); OJaBJz18xEo@84.0 (yellow kerb; s 2391, direct); 9Drr1VkE1_U@192.0 (yellow kerb; s 2407, corroborate); 9Drr1VkE1_U@58.0 (yellow kerb; s 2411, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2280, c20_s2320, c20_s2360: yellow paint s 2352-2402 (50 m) beyond the left race edge, band median 1.20 m (p25-p75 0.20-1.50); yellow band 0.00-1.55 m beyond the edge'),
            dict(name='T8 crest kerb', side='left', a=(40.6940104, -82.634438), b=(40.694118, -82.6342986), off=0.57, width=1.15,
                 colors='yel', pattern='plain', edge_line=True,
                 colour_src='colour from the capture only (no inventory frame within 25 m)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2400: yellow paint s 2446-2464 (18 m) beyond the left race edge, band median 1.10 m (p25-p75 1.00-1.10); yellow band 0.00-1.15 m beyond the edge'),
            dict(name='T8 exit kerb', side='left', a=(40.6945858, -82.6331316), b=(40.694594, -82.6326941), off=0.68, width=1.35,
                 colors='yel', pattern='plain', edge_line=True,
                 colour_src='9Drr1VkE1_U@196.0 (yellow kerb; s 2603, corroborate); OJaBJz18xEo@92.0 (yellow kerb; s 2610, direct); e25u_vjn1uM@100.0 (yellow kerb; s 2616, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2520, c20_s2560: yellow paint s 2578-2615 (37 m) beyond the left race edge, band median 0.30 m (p25-p75 0.20-0.85); yellow band 0.00-1.35 m beyond the edge'),
            dict(name='T9 exit kerb', side='left', a=(40.6938219, -82.631962), b=(40.6933065, -82.6319459), off=0.42, width=0.85,
                 colors='yel', pattern='plain',
                 colour_src='e25u_vjn1uM@104.0 (T9 exit kerb, yellow and red; s 2722, direct); OJaBJz18xEo@98.0 (T9 exit kerb, yellow and red; s 2746, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2680, c20_s2720: yellow paint s 2727-2784 (58 m) beyond the left race edge, band median 1.80 m (p25-p75 1.70-1.90); yellow band 0.00-0.85 m beyond the edge'),
            dict(name='T9 exit kerb, red outer band', side='left', a=(40.6938219, -82.631962), b=(40.6933065, -82.6319459), off=1.15, width=0.6,
                 colors='red', pattern='plain',
                 colour_src='e25u_vjn1uM@104.0 (T9 exit kerb, yellow and red; s 2722, direct); OJaBJz18xEo@98.0 (T9 exit kerb, yellow and red; s 2746, direct)',
                 src="kerb band scan (r7/kerb_scan.py) on c20_s2680, c20_s2720: yellow paint s 2727-2784 (58 m) beyond the left race edge, band median 1.80 m (p25-p75 1.70-1.90); red outer band 0.85-1.45 m beyond the edge (red share 0.70 at the band's outer side)"),
            dict(name='T11 apex kerb', side='left', a=(40.690808, -82.6329107), b=(40.6905538, -82.6328899), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='OJaBJz18xEo@110.0 (red/white kerb; s 3103, direct); e25u_vjn1uM@114.0 (red/white kerb; s 3109, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s3040, c20_s3080: redwhite paint s 3082-3114 (32 m) beyond the left race edge, band median 1.60 m (p25-p75 1.50-1.80); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T13 apex kerb', side='left', a=(40.6892089, -82.6335395), b=(40.6893548, -82.6338338), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='e25u_vjn1uM@126.0 (T13 kerb, red/white; s 3447, direct); OJaBJz18xEo@126.0 (T13 kerb; s 3474, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s3400: redwhite paint s 3440-3474 (35 m) beyond the left race edge, band median 1.60 m (p25-p75 1.50-1.80); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T1 exit kerb', side='right', a=(40.6887929, -82.6392941), b=(40.6881052, -82.6392825), off=0.57, width=1.15,
                 colors='yel', pattern='plain',
                 colour_src='9Drr1VkE1_U@22.0 (T1 exit kerb, yellow; s 374, direct); 9Drr1VkE1_U@156.0 (T1 exit kerb, yellow; s 394, corroborate); e25u_vjn1uM@36.0 (T1 exit kerb, yellow, flat (rumble strip); s 419, direct); OJaBJz18xEo@20.0 (T1 exit kerb, yellow, with red outer band; s 440, direct); 9Drr1VkE1_U@92.0 (T1 exit kerb, yellow; s 447, corroborate)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s0320, c20_s0360: yellow paint s 382-458 (76 m) beyond the right race edge, band median 2.10 m (p25-p75 1.90-2.20); yellow band 0.00-1.15 m beyond the edge'),
            dict(name='T1 exit kerb, red outer band', side='right', a=(40.6887929, -82.6392941), b=(40.6881052, -82.6392825), off=1.65, width=1.0,
                 colors='red', pattern='plain',
                 colour_src='9Drr1VkE1_U@22.0 (T1 exit kerb, yellow; s 374, direct); 9Drr1VkE1_U@156.0 (T1 exit kerb, yellow; s 394, corroborate); e25u_vjn1uM@36.0 (T1 exit kerb, yellow, flat (rumble strip); s 419, direct); OJaBJz18xEo@20.0 (T1 exit kerb, yellow, with red outer band; s 440, direct); 9Drr1VkE1_U@92.0 (T1 exit kerb, yellow; s 447, corroborate)',
                 src="kerb band scan (r7/kerb_scan.py) on c20_s0320, c20_s0360: yellow paint s 382-458 (76 m) beyond the right race edge, band median 2.10 m (p25-p75 1.90-2.20); red outer band 1.15-2.15 m beyond the edge (red share 0.81 at the band's outer side)"),
            dict(name='T2 (Keyhole) apex kerb', side='right', a=(40.6843903, -82.6390733), b=(40.6842427, -82.6400604), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='9Drr1VkE1_U@98.0 (Keyhole kerb, red/white; s 890, corroborate); 9Drr1VkE1_U@30.0 (Keyhole kerb, red/white; s 902, direct); OJaBJz18xEo@34.0 (Keyhole kerb, red/white; s 906, direct); e25u_vjn1uM@48.0 (Keyhole kerb, red/white, long; s 912, direct); 9Drr1VkE1_U@164.0 (Keyhole kerb, red/white; s 930, corroborate); OJaBJz18xEo@36.0 (Keyhole kerb, red/white; s 943, direct); e25u_vjn1uM@50.0 (Keyhole kerb, red/white, long; s 958, direct); 9Drr1VkE1_U@100.0 (Keyhole kerb, red/white; s 966, corroborate); 9Drr1VkE1_U@32.0 (Keyhole kerb, red/white; s 974, direct); 9Drr1VkE1_U@166.0 (Keyhole kerb, red/white; s 998, corroborate); e25u_vjn1uM@52.0 (Keyhole kerb, red/white, long; s 999, direct); OJaBJz18xEo@40.0 (Keyhole kerb, red/white; s 1019, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s0800, c20_s0840, c20_s0880, c20_s0920, c20_s0960: redwhite paint s 872-1016 (145 m) beyond the right race edge, band median 1.60 m (p25-p75 1.50-1.70); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T4 apex kerb', side='right', a=(40.6922728, -82.638195), b=(40.6923428, -82.6378698), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='e25u_vjn1uM@76.0 (T4 apex kerb, red/white (kept in the 2024 rebuild); s 1952, direct); 9Drr1VkE1_U@116.0 (T4 apex kerb, red/white; s 1955, corroborate); OJaBJz18xEo@66.0 (T4 apex kerb, red/white; s 1973, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s1880, c20_s1920: redwhite paint s 1950-1984 (34 m) beyond the right race edge, band median 1.70 m (p25-p75 1.50-1.80); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T6 kerb', side='right', a=(40.6924231, -82.636193), b=(40.6928274, -82.6361939), off=0.57, width=1.15,
                 colors='yel', pattern='plain', edge_line=True,
                 colour_src='e25u_vjn1uM@84.0 (T6 kerb, yellow; s 2147, direct); OJaBJz18xEo@76.0 (yellow kerb; s 2198, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2080, c20_s2120: yellow paint s 2150-2194 (44 m) beyond the right race edge, band median 1.30 m (p25-p75 1.20-1.50); yellow band 0.00-1.15 m beyond the edge'),
            dict(name='T7 apex kerb', side='right', a=(40.6934713, -82.6361889), b=(40.693627, -82.6359261), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='9Drr1VkE1_U@54.0 (red/white kerb; s 2252, direct); OJaBJz18xEo@80.0 (red/white kerb; s 2295, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2200, c20_s2240: redwhite paint s 2270-2304 (35 m) beyond the right race edge, band median 1.90 m (p25-p75 1.70-2.00); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T8 apex kerb', side='right', a=(40.6943311, -82.6338816), b=(40.6944591, -82.6335559), off=0.62, width=1.25,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='OJaBJz18xEo@88.0 (red/white kerb; s 2504, direct); 9Drr1VkE1_U@60.0 (red/white kerb; s 2512, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2440, c20_s2480: redwhite paint s 2506-2541 (36 m) beyond the right race edge, band median 1.50 m (p25-p75 0.60-1.60); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T9 apex kerb', side='right', a=(40.6944727, -82.6324879), b=(40.694211, -82.6321729), off=0.72, width=1.45,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='OJaBJz18xEo@94.0 (red/white kerb; s 2653, direct); e25u_vjn1uM@102.0 (T9 apex kerb, red/white; s 2664, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s2600, c20_s2640: redwhite paint s 2634-2681 (47 m) beyond the right race edge, band median 1.50 m (p25-p75 1.40-1.60); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='T11 exit kerb', side='right', a=(40.6902937, -82.632895), b=(40.6898254, -82.6324943), off=0.62, width=1.25,
                 colors='yel', pattern='plain', edge_line=True,
                 colour_src='OJaBJz18xEo@112.0 (yellow kerb; s 3149, direct); e25u_vjn1uM@116.0 (yellow kerb; s 3172, direct); OJaBJz18xEo@114.0 (yellow kerb; s 3204, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s3080, c20_s3120, c20_s3160: yellow paint s 3140-3203 (62 m) beyond the right race edge, band median 0.45 m (p25-p75 0.30-1.10); yellow band 0.00-1.25 m beyond the edge'),
            dict(name='T12 (Carousel) apex kerb', side='right', a=(40.6888651, -82.6325633), b=(40.6888974, -82.6331215), off=0.82, width=1.65,
                 colors='rw', pattern='blocks', profile=KERB_RAISED, edge_line=True,
                 colour_src='OJaBJz18xEo@120.0 (Carousel kerb, red/white; s 3341, direct); e25u_vjn1uM@122.0 (Carousel kerb, red/white; s 3351, direct); e25u_vjn1uM@16.0 (Carousel kerb, red/white; s 3372, direct); OJaBJz18xEo@122.0 (red/white kerb; s 3378, direct); e25u_vjn1uM@124.0 (red/white kerb; s 3395, direct); 9Drr1VkE1_U@82.0 (Carousel / T13 kerb, red/white; s 3408, corroborate); 9Drr1VkE1_U@12.0 (Carousel kerb, red/white; s 3410, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s3280, c20_s3320: redwhite paint s 3329-3390 (60 m) beyond the right race edge, band median 1.60 m (p25-p75 1.50-1.70); band from the edge (inner face = race edge) to the outer limit of the red blocks'),
            dict(name='pit-straight kerb (T13 exit)', side='right', a=(40.689506, -82.6342701), b=(40.6895367, -82.6349989), off=0.82, width=1.65,
                 colors='yel', pattern='plain',
                 colour_src='9Drr1VkE1_U@148.0 (yellow kerb; s 3523, corroborate); e25u_vjn1uM@22.0 (yellow kerb; s 3528, direct); OJaBJz18xEo@128.0 (yellow kerb; s 3531, direct); 9Drr1VkE1_U@84.0 (yellow kerb; s 3544, corroborate); e25u_vjn1uM@130.0 (yellow kerb; s 3557, direct); OJaBJz18xEo@4.0 (yellow kerb; s 3559, direct)',
                 src='kerb band scan (r7/kerb_scan.py) on c20_s3480, c20_s3520: yellow paint s 3514-3575 (62 m) beyond the right race edge, band median 1.50 m (p25-p75 1.40-1.60); yellow band 0.00-1.65 m beyond the edge'),
        ],

        # the red / white kerb on the inactive chicane's inside edge (inventory row 360 t042 right, corrected round 7 to kind
        # paint: a closed road's kerb, not a course kerb): measured on c20_s0560 / c20_s0600 (capwin windows centre (-274,
        # -300) at 0.05 m/px and (-265.2, -322.2) at 0.1 m/px, the block band's centre picked every ~4 m; the capture's common
        # registration shift of 0.6 m is not removed: a drawn-only kerb on a closed road)
        kerb_lines=[dict(latlon=[(40.6862804, -82.6392313), (40.6862377, -82.6392431), (40.6861973, -82.6392579), (40.6861613, -82.6392728),
                                 (40.6861276, -82.6392876), (40.6860917, -82.6393083), (40.6860607, -82.6393314)],
                         width=0.9, colors='rw', src='chicane re-join kerb: c20_s0560 / c20_s0600 block band; 360 lap t042 right (red / white kerb at the chicane re-join)')],
        # BARRIERS (step 3). OSM maps the circuit's barrier lines (2025 mapping, ways 13152089xx): their positions are checked
        # on the clean captures (the barrier scan, round7.md: every capture, both sides) and each run gets its kind, height
        # and fence from the footage. The barrier round the lap is red stacked W-beam armco (360 lap, N837, IndyCar: 'armco
        # (stacked W-beam), red' on 111 rows; three beams, 360 t042 left), 1.2 m: three 0.31 m beams over ~0.27 m (360 t042
        # left: horizon ratio 1.4 m with the 1.7 m camera, posts / armco ratio 2.4 with the 3.5 m fence -> 1.45 m; the
        # round-4 readings 0.8 and 1.3 m; +-0.25 m), colour from the sunlit frames N837 t016 / t022 (110-162, 59-100,
        # 53-88): ARMCO_RED. No tyre walls (none in any video).
        osm_barrier_overrides={
            '1315208923': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src="red stacked armco with the catch fence, right of the pit straight to T1 and on to the back straight (inventory rows right s 0-160: 360 t024-t030 right, N837 t006-t010; 'catch fence over the armco', t026 right)"),
            '1315208924': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco at the T13 exit, right (360 lap lead-in t018-t020 right: armco beyond the grass; c20_s3400 band)'),
            '1315208925': dict(drop=True, src='superseded by the measured pit wall (declared_walls \'pit wall\'): the OSM line runs 0.8 m on the lane side of the wall top on c20_s0000 / c20_s0080 / c20_s0120 and crosses into the lane at the footbridge (pit connectivity, round 7 build 1)'),
            '1315208926': dict(drop=True, src='rejected: the line behind the pit boxes (OSM wall); the 360 lap t026-t030 left shows the boxes open to the paddock (tents, people, the hospitality building) with no wall line over the lane, c20_s0000 shows a row of small objects, not a wall top'),
            '1315208927': dict(drop=True, src='rejected: as OSM 1315208926 (the line behind the pit boxes; 360 t026-t028 left, c20_s0000)'),
            '1315208928': dict(drop=True, src='rejected: as OSM 1315208926 (the line behind the pit boxes; 360 t024-t026 left, c20_s3560 / c20_s0000)'),
            '1315208929': dict(drop=True, src='rejected: as OSM 1315208926 (the line behind the pit boxes; 360 t128-t130 left, c20_s3480 / c20_s3520)'),
            '1315208930': dict(kind='concrete', h=1.04, fence=0.0, color='#e6e4de', src='white concrete wall on the pit-entry side at the T13 exit (IndyCar A t012 left, s 3410: concrete wall, white; N837 t000 left: T13 exit, pit-lane side wall); height as the pit wall it continues (lidar 1.04 m)'),
            '1315208931': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence, left of the Carousel and T11-T12 (360 t120 left s 3302: armco + catch fence on curved posts; N837 t106 left armco)'),
            '1315208932': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco left from Thunder Valley to T11 (N837 t106 left s 3000: armco, red; 360 t110-t112 left: grass to the armco)'),
            '1315208933': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence left at the PERMCO footbridge (360 t108 left s 2880: armco + catch fence on curved posts, Velo banners on the bridge; N837 t102 left armco)'),
            '1315208934': dict(kind='concrete', h=0.8, fence=0.0, color='#e6e4de', src='white concrete wall left from the T9 exit to the PERMCO footbridge (360 t104-t106 left: concrete wall, white, 0.8 m horizon-ratio; N837 t096-t098 left; IndyCar A t064 left)'),
            '1315208935': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco left behind the T8-T9 sand trap (360 t098 left s 2551 armco; c20_s2520 / c20_s2560 the band 38-48 m out)'),
            '1315208936': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence left over the T8 crest (360 t094-t098 left s 2427-2551: armco + catch fence on curved posts, the RV paddock behind)'),
            '1315208937': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence left through T7 (360 t090 left s 2314: catch fence on curved posts, Honda boards; t092 left)'),
            '1315208938': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src="red armco left at T6 (360 t084-t088 left s 2147-2269: armco (stacked W-beam), red; marshal post '5')"),
            '1315208939': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco left from the T4 exit to T6 (N837 t068 / t074 left s 2015-2146: armco, red)'),
            '1315208940': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco left on the T4 approach in front of the aluminium bleachers (360 t072-t074 left s 1813-1898: armco (stacked W-beam), red; N837 t059 / t060 left: the catch-fence posts over the armco, judge r7 F14)'),
            '1315208941': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence left of the back straight (360 t062-t070 left s 1338-1718: armco + catch fence on curved posts, the paddock / RVs behind; N837 t050-t058 left)'),
            '1315208942': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence left at T3 (N837 t052 / t054 left s 1439-1527: armco + catch fence; 360 t064-t066 left; c20_s1480 / c20_s1520: the armco and fence line)'),
            '1315208943': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence left from the Keyhole exit along the return straight (360 t056-t064 left s 1101-1433, N837 t044-t050 left: armco + catch fence on curved posts)'),
            '1315208944': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco left round the outside of the Keyhole behind the sand trap, carrying the board wall (360 t048-t052 left s 912-999: board walls Honda / Firestone / Velo / PERMCO on the armco line)'),
            '1315208945': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src="red armco with the catch fence left before the Keyhole (360 t044-t046 left s 783-863: armco + catch fence on curved posts; brake board '300')"),
            '1315208946': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence left from the T1 exit (360 t038-t042 left s 493-680: armco + catch fence on curved posts; N837 t022-t028 left)'),
            '1315208947': dict(drop=True, src='replaced by declared_walls \'T1 inside armco\' (its OSM nodes west of the footbridge: under the bridge the 2019 class-2 returns include the deck, so the wall top stepped 1.85 m at s 238, wall-tops gate round 7 build 2)'),
            '1315208948': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right of the back straight between the T1 run-off and the straight (c20_s1480-c20_s1600 band 20 m out; IndyCar C t174 left / the 360 t064-t068 ahead views: the armco line across the infield)'),
            '1315208949': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src="red armco right of the back straight on the T4 approach (N837 t060 right s 1792: armco, red; 360 t072 right: grass to it, brake board '300')"),
            '1315208950': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right at T4 (360 t078 right s 1995: armco (stacked W-beam), red, far)'),
            '1315208951': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right from T5 to T6 (N837 t074 right s 2146: armco, red)'),
            '1315208952': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right from T6 to T8 (c20_s2240-c20_s2440 band 8-38 m out; 360 t088-t094 right: grass to the armco)'),
            '1315208953': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right at T8 (c20_s2480 band 18-21 m out; 360 t096 right)'),
            '1315208954': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right from T8 to T9 (c20_s2520-c20_s2600 band 12-23 m out; 360 t100-t102 right: armco (stacked W-beam), red at T9)'),
            '1315208955': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right at T9 (360 t102 right s 2664: armco (stacked W-beam), red)'),
            '1315208956': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=2.3, src='red armco with the catch fence right from T9 through Thunder Valley to T11 (360 t104-t112 right s 2722-3053: armco + catch fence on curved posts; N837 t104-t108 right)'),
            '1315208957': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco right outside the Carousel (c20_s3280-c20_s3400 band 11-41 m out; 360 t016-t018 right: grass to it)'),
            '1315208969': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='a short red armco pair in the infield between the T1-Keyhole straight and the return straight, 26 m out (c20_s0440 / c20_s1280: two parallel 50 m runs 6 m apart, OSM barrier=wall); not in any onboard view'),
            '1315208970': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='the second run of the infield armco pair (c20_s0440 / c20_s1280)'),
            '1315208971': dict(kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0, src='red armco behind the Keyhole sand trap, outer line (c20_s0880 / c20_s0920 band 30-56 m out; 360 t048-t050 left beyond the gravel)'),
            '1315208958': dict(osm_fence=True, fence=2.4, src='perimeter fence on the left from T11 round to T8 behind the armco (c20_s2800 / c20_s2840: the line through the trees beyond the wall; height unmeasured, 2.4 m kept, manifest)'),
            '1315208959': dict(osm_fence=True, fence=2.4, src='spectator fence behind the armco left from the T1 exit to the Keyhole (c20_s0520: the thin line 6 m behind the armco; height unmeasured, 2.4 m kept, manifest)'),
            '1315208960': dict(osm_fence=True, fence=2.4, src='spectator fence behind the armco left of the return straight (c20_s1120: the line beside the path; height unmeasured, 2.4 m kept, manifest)'),
            '1315208963': dict(osm_fence=True, fence=2.4, src='spectator fence left at T6 behind the armco (c20_s2160: the line beside the hut; height unmeasured, 2.4 m kept, manifest)'),
            '1315208965': dict(osm_fence=True, fence=2.4, src='the fence round the T4-approach bleachers (c20_s1800: along the bleachers; height unmeasured, 2.4 m kept, manifest)'),
            '1315208966': dict(osm_fence=True, fence=2.4, src='the fence round the T4-approach bleachers, far side (c20_s1800 / c20_s1760; height unmeasured, 2.4 m kept, manifest)'),
            '1315208967': dict(osm_fence=True, fence=2.4, src='spectator fence right behind the armco round the outside of the lap (c20_s2720 / c20_s2680: the post shadows 6 m behind the armco; height unmeasured, 2.4 m kept, manifest)'),
            '1315208972': dict(osm_fence=True, drop=True, src='dropped: OSM only, 55-68 m beyond the Keyhole outside, off the clean captures (no 2026 evidence)'),
            '1315208973': dict(osm_fence=True, drop=True, src='dropped: OSM only, 55-117 m beyond the Keyhole outside, off the clean captures (no 2026 evidence)'),
            '1424624790': dict(osm_fence=True, drop=True, src='dropped: an OSM industrial-area fence 333-357 m from the track, off the clean captures'),
        },
        declared_walls=[
            # the pit wall between the track and the pit lane, measured on the clean captures (compare/wall_measure.py): along the
            # grass island between the pit-in lane and the T13 exit (--guide 202.7,17.7;192,28;181.5,38.55 --feature bright: 100 %
            # picked, rms 0.11 m) to its nose beside the T13 kerb's end (c20_s3400, s ~3477), then along the pit straight (--edge
            # left --lo 3380 --hi 3594 and --lo 0 --hi 218 --off 0.8,4.0 --feature bright, points west of the nose: the wall top
            # 1.0-1.2 m beyond the left edge, 99 % picked, rms 0.22 m) to its end 15 m before the footbridge, where the painted ladder line takes over (c20_s0120); h 1.04 m (2019 lidar 1.04 m, r5/lidar_heights.json; the 360 lap t026 left re-read
            # 1.03-1.08 m, round7.md); white (360 t024-t028 left, t128 left: white concrete slabs, 'NTT INDYCAR SERIES' 2025 dress),
            # no fence on it (t026 left)
            dict(name='T1 inside armco', kind='armco', h=1.2, rails=3, color=ARMCO_RED, fence=0.0,
                 latlon=[(40.6884389, -82.6389956), (40.6888109, -82.6389646), (40.6889153, -82.6389413), (40.6890535, -82.6388637), (40.6891903, -82.6387532), (40.6892741, -82.6386407), (40.6893344, -82.6384972), (40.6893718, -82.6383583), (40.6893944, -82.6382391)],
                 src='OSM 1315208947 nodes to 9 m west of the footbridge (the last point on the way); low red armco on the T1 inside beyond the pit-exit lane and the infield grass (360 lap t032-t034 left s 295-358; N837 t016-t018 left); c20_s0200-c20_s0320 the line'),
            # the tyre cushion at the head of the armco right of the T3 kink (c20_s1400 / c20_s1440: a bundle of tyres, round
            # tops visible, about 2 x 6 m, at the south end of OSM 1315208948, 26 m right of the track)
            # the capture wins over the brief's 'no tyre walls' (that was a reading of the videos; the orchestrator, 27 Oct 2026): kept
            dict(name='T3 armco head cushion', kind='tyres', h=0.84, fence=0.0, color='#161616',
                 latlon=[(40.6883487, -82.6398503), (40.6884071, -82.6398385)],
                 src='c20_s1400 / c20_s1440: the tyre bundle at the head of the armco (OSM 1315208948)', h_src='4 tyres (0.21 m) assumed: the capture shows the bundle, not its height'),
            dict(name='pit-in barrier', kind='concrete', h=1.0, fence=0.0, color='#1d1d1f',
                 latlon=[(40.6888221, -82.6333765), (40.6888536, -82.6333998), (40.6888866, -82.6334184), (40.6889208, -82.6334335), (40.6889552, -82.633448), (40.6889883, -82.6334667), (40.6890211, -82.6334879), (40.6890532, -82.6335093), (40.6890841, -82.6335336), (40.6891142, -82.6335598), (40.6891437, -82.6335874), (40.6891548, -82.6335978)],
                 src='c20_s3360 / c20_s3400 dark line (wall_measure.py); 360 lap t018 left; N837 t125; IndyCar A t012 left (pit-entry side wall)',
                 h_src='about the pit wall beside it (1.0 m) in N837 t125'),
            dict(name='pit wall', kind='pitwall', h=1.04, fence=0.0, color='#e6e4de',
                 latlon=[(40.6891548, -82.6335978), (40.6891773, -82.6336411), (40.689204, -82.6336731), (40.6892298, -82.633706), (40.6892553, -82.6337397), (40.6892806, -82.6337734), (40.6893054, -82.6338076), (40.6893292, -82.6338433), (40.6893379, -82.6338569), (40.6893538, -82.6339361), (40.6893711, -82.6340531), (40.689372, -82.6341723), (40.6893833, -82.6342902), (40.6893902, -82.6344083), (40.6893951, -82.6345265), (40.6894019, -82.6346446), (40.6894071, -82.634763), (40.6894129, -82.6348813), (40.6894178, -82.6349996), (40.6894214, -82.635118), (40.6894189, -82.6352249), (40.6894134, -82.6352742), (40.6894318, -82.6353915), (40.6894373, -82.6355097), (40.6894427, -82.635628), (40.6894485, -82.6357462), (40.6894536, -82.6358645), (40.6894567, -82.6359829), (40.6894622, -82.6361012), (40.6894654, -82.6362197), (40.6894702, -82.6363379), (40.6894737, -82.6364563), (40.6894776, -82.6365747), (40.6894857, -82.6366928), (40.6894883, -82.6368112), (40.689492, -82.6369296), (40.6895007, -82.6370476), (40.6895054, -82.6371659), (40.6895101, -82.6372843), (40.6895144, -82.6374027), (40.6895177, -82.6375213), (40.6895203, -82.6376397), (40.6895228, -82.6377581), (40.6895232, -82.6377782)],
                 src='c20_s3400-c20_s0200 wall top (wall_measure.py); 360 lap e25u_vjn1uM t020-t030 left, t128-t130 left; N837 t000-t010 left; inventory pit rows s 3496-216',
                 h_src='lidar 2019 1.04 m (r5/lidar_heights.json); horizon ratio 360 t026 left 1.03-1.08 m (camera 1.7 m, horizon from the heads in the lane)'),
        ],
        tyre_facings=None, blocks=[],
        # second judge m7: the three yellow water-filled barrels at the pit-in barrier's head as three 0.9 m cylinders (a yellow
        # stack) in a line ahead of its head (360 lap t017-t018 left), not one box
        tyre_stacks=[dict(latlon=(40.6888174, -82.633373), h=0.9, w=0.9, style='tyres', color='#e2c21e', src='360 lap t017-t018 left: yellow impact barrel at the pit-in barrier head; c20_s3360 (the barrier head)'), dict(latlon=(40.6888096, -82.6333672), h=0.9, w=0.9, style='tyres', color='#e2c21e', src='360 lap t017-t018 left: yellow impact barrel at the pit-in barrier head; c20_s3360 (the barrier head)'), dict(latlon=(40.6888017, -82.6333614), h=0.9, w=0.9, style='tyres', color='#e2c21e', src='360 lap t017-t018 left: yellow impact barrel at the pit-in barrier head; c20_s3360 (the barrier head)')],
        # the black-faced barrier along the grass island at the pit-in (c20_s3360 / c20_s3400: the dark line between the island and
        # the pit-in lane, wall_measure.py --guide 221,-20;212.2,0.2;202.7,17.7 --feature dark, 100 % picked, rms 0.56 m), joined to
        # the pit wall's island run; 360 lap t018 left (2025): a HONDA banner over it and three yellow impact barrels at its
        # head; N837 t125 (Apr 2026): its smooth black face (belting over the barrier: tyres not visible, drawn as a black wall)
        impact_barriers=[],
        # PIT EXIT (step 4): no cones on the pit-exit merge (360 t030-t034 left, N837 t014-t016: the ladder paint and the T1
        # inside kerb, no cones)
        pit_exit_cones=dict(draw=False, src='no cones on the pit exit (360 lap t030-t034 left; N837 t014 / t016): the ladder line and the raised T1 inside kerb separate the lane'),
        edge_line_cut=[],
        # the painted ladder between the pit exit and the track from the pit wall's end to the T1 inside kerb (c20_s0080-c20_s0280:
        # two white lines about 0.8 m apart with white rungs every ~1.2 m, its inner line on the race edge; kerb_scan.py over
        # s 240-298: white 0.0-0.4 m and 0.8-1.0 m beyond the edge; 360 lap t030-t032 left, N837 t014 'white hatched pit-exit
        # blend'); the two long lines drawn, the rungs not (the kit has no ladder pattern)
        paint_lines_declared=[dict(latlon=[(40.689529, -82.6377819), (40.6895299, -82.6378173), (40.6895309, -82.6378525), (40.6895317, -82.6378878), (40.6895323, -82.637923), (40.6895328, -82.6379582), (40.6895331, -82.6379933), (40.6895332, -82.6380283), (40.6895332, -82.638063), (40.6895331, -82.6380975), (40.6895327, -82.6381316), (40.689532, -82.6381654), (40.6895306, -82.6381988), (40.6895285, -82.6382318), (40.6895255, -82.6382643), (40.6895216, -82.6382965), (40.6895167, -82.6383284), (40.6895107, -82.6383599), (40.6895037, -82.6383909), (40.6894954, -82.6384216), (40.6894861, -82.6384518), (40.6894757, -82.6384815), (40.6894645, -82.6385108), (40.6894526, -82.6385398), (40.68944, -82.6385684), (40.6894269, -82.6385968), (40.6894132, -82.6386248), (40.689399, -82.6386524), (40.689384, -82.6386795)], width=0.15, double=0.8, color='#e8e8e4',
                                   src='pit-exit ladder line: c20_s0080-c20_s0280 (r7/kerb_scan.py profile, s 240-298 left); 360 lap t030-t032 left; N837 t014')],
        bridge_stairs=True,
        # judge r7 F9: the banners the footage shows on the two footbridges, typed names (no logo artwork)
        bridge_banners={'444205416': [['Firestone|#f2f2ee|#c8202c'], ['HONDA|#c8302a|#f2f2ee']],
                        '444205419': [['VELO|#2f6db3|#f2f2ee', 'VELO|#2f6db3|#f2f2ee'], ['PERMCO|#2f6db3|#f2f2ee', 'Pumps and Motors|#e8ecef|#2f4f7a']]},   # faces in the OSM way's frame (app: face 0 on the way's left); round 8 sheet fwd_s2800 showed VELO on the approach: swapped, so PERMCO / Pumps and Motors faces oncoming cars (N837 t100-t101) and VELO the far face (360 back t108)
        # CLOSED ROADS (step 2): the owner's GREEN strokes of round 2 (owner/r2/merged.json green_enu_xy: the extra paved
        # boundaries) are the paving edges (edges_from_green) of the unused roads OSM maps as raceway ways: the inner chicane
        # (444205376) and the two T1-T3 connectors (444205377 / 444205378). Grey asphalt a touch lighter than the racing
        # surface (360 t040 / t042 / t064; tone measured on the captures, round7.md); no cones at their mouths (360 t040 ahead,
        # t042 right, t064 right: open mouths) -> mouth_cones [] and the containment rays onto them listed in gates.allowed
        owner_green=dict(file='owner/r2/merged.json', reach=4.0, along=1.0),
        closed_roads=[
            dict(edges_from_green=True, name='inner chicane (OSM 444205376)', ways=['444205376'], half_width=4.5, surface='apron',   # boundary audit r7 B2: the ortho's own tone read as pale gravel at hood level with dark NAIP blotches; 'apron' is pale weathered asphalt with the grain (360 t040 / t064: grey asphalt a touch lighter than the course)
                
                 mouth_cones=[dict(near=(40.6860895, -82.6392579), src='N837 OJaBJz18xEo t026 / t027 (Lemons, Apr 2026): four orange cones across the chicane mouth where it rejoins on the right (judge r7 F4); the 2025 360 lap t040-t042 shows it open (IndyCar weekend)')],
                 src='OSM 444205376; the owner green strokes w_s0625 / w_s0750 / w_s0875; c20_s0560-c20_s0840: the unused inner chicane, grey asphalt; 360 t040 / t042 right'),
            dict(edges_from_green=True, name='T1-T3 connector, south (OSM 444205377)', ways=['444205377'], half_width=4.5, surface='apron',   # boundary audit r7 B2: the ortho's own tone read as pale gravel at hood level with dark NAIP blotches; 'apron' is pale weathered asphalt with the grain (360 t040 / t064: grey asphalt a touch lighter than the course)
                 mouth_cones=[],
                 src='OSM 444205377; the owner green strokes w_s1250; c20_s1280 / c20_s0480: the unused connector between the T1-Keyhole straight and the return straight; 360 t064 right'),
            dict(edges_from_green=True, name='T1-T3 connector, north (OSM 444205378)', ways=['444205378'], half_width=4.5, surface='apron',   # boundary audit r7 B2: the ortho's own tone read as pale gravel at hood level with dark NAIP blotches; 'apron' is pale weathered asphalt with the grain (360 t040 / t064: grey asphalt a touch lighter than the course)
                 mouth_cones=[],
                 src='OSM 444205378; the owner green strokes w_s0500 / w_s1250; c20_s0440 / c20_s1360: the unused connector at the T1 exit; 360 t064 right (the connector meets the track)'),
        ],
        # MARSHAL POSTS, MASTS, CONES, BOARDS (step 3; the station / furniture / logo ledgers in round7.md)
        marshal_posts=[
            dict(name='back-straight tower (yellow, red roof)', latlon=(40.6889739, -82.640214), h=5.6, w=2.6, color='#d9b23a', roof='#b8443a',
                 src='N837 OJaBJz18xEo t054 (Apr 2026): a yellow two-level marshal tower with a red roof and stairs behind the left armco, '
                     'ahead of the HONDA billboard; c20_s1520: its red roof and shadow behind the armco gap at s ~1555 left',
                 h_src='two levels in t054 (deck ~3 m, roof ~5.6 m against the 1.2 m armco in front)'),
        ],
        light_masts=[
            dict(latlon=(40.6888518, -82.6387189), h=8.3, src='timber utility pole on the T1 inside (360 t032 left: timber utility poles with lines; N837 t016: the pole with cross-arms left); lidar 2019 isolated spike 8.3 m at (-229.5, -16.5); c20_s0240 / c20_s0280: the pole and its long shadow'),
            dict(latlon=(40.689247, -82.6381976), h=9.9, src='timber utility pole on the T1 inside by the footbridge (360 t032 left; N837 t014-t016); lidar 2019 isolated spike 9.9 m at (-185.5, 27.5); c20_s0200 / c20_s0240: the pole and its shadow'),
        ],
        tree_mast_clear=dict(radius=4.0),
        cone_lines_declared=[
            dict(side='left', s=(836, 846), off=2.0, spacing=10.0, size=0.7, color='#e8641e',
                 src='N837 OJaBJz18xEo t029 / t030 (Apr 2026): two orange cones on the left verge at the end of the Keyhole braking zone (judge r7 F4; the station from the frames, about 30-50 m ahead of t029 / t030, sigma ~15 m)'),
            dict(side='left', s=(1872, 1882), off=3.0, spacing=10.0, size=0.7, color='#e8641e',
                 src='N837 OJaBJz18xEo t062 (Lemons Mid-West Crisis, Apr 2026): two orange cones on the grass left at the T4 braking zone (inventory row s 1876 left); the station from the N837 time map (sigma 14.8 m)'),
        ],
        # distance boards: tall white boards with stacked black digits on the catch-fence posts at the armco (N837 t029-t031,
        # t059-t060, t106; 360 t028 / t044 / t072 / t112), 0.7 x 1.8 m, 0.6 m in front of the barrier line; the app stacks a
        # multi-digit board's numerals (judge r7 F5)
        brake_boards_declared=[
            dict(side='right', s=154, off=5.9, text='200', w=0.7, h=1.8, src='360 lap e25u_vjn1uM t028 right: "200" board before T1 (inventory row s 154); on the fence posts at the armco (6.5 m out)'),
            dict(side='left', s=790, off=8.6, text='300', w=0.7, h=1.8, src='N837 OJaBJz18xEo t029 (Apr 2026) and 360 t044 left: "300" on the fence before the Keyhole (inventory rows s 783 / 798); boards 100 ft apart (360 t044-t045.5: 300 at ~790, 100 at ~855)'),
            dict(side='left', s=825, off=7.7, text='200', w=0.7, h=1.8, src='N837 t030 (Apr 2026): "200" on the left fence before the Keyhole; judge r7 F3 (no inventory row: added with this source)'),
            dict(side='left', s=858, off=8.0, text='100', w=0.7, h=1.8, src='N837 t031 and 360 t045.5 left: "100" before the Keyhole; judge r7 F3'),
            dict(side='left', s=1776, off=9.9, text='500', w=0.7, h=1.8, src='N837 t059 (Apr 2026): "500" on the fence beside the T4-approach bleachers; boards 100 ft (30.5 m) apart back from the "100" the 360 lap crosses at t 74.0 (s ~1898, round4.md); judge r7 F3'),
            dict(side='left', s=1806, off=10.5, text='400', w=0.7, h=1.8, src='N837 t060: "400"; judge r7 F3'),
            dict(side='left', s=1837, off=11.1, text='300', w=0.7, h=1.8, src='360 lap t072 left and N837 t060: "300" (inventory row s 1813 left, sigma 20 m)'),
            dict(side='left', s=1867, off=11.6, text='200', w=0.7, h=1.8, src='N837 t060-t061 (beyond the 300); judge r7 F3'),
            dict(side='left', s=1898, off=12.2, text='100', w=0.7, h=1.8, src='360 lap t074: the "100" board crossed at s ~1898 (round4.md T4 placement)'),
            dict(side='right', s=1776, off=9.9, text='500', w=0.7, h=1.8, src='360 lap t070.5 right (second judge crop t4boards): a "500" board on the right fence before T4'),
            dict(side='left', s=2146, off=4.0, text='5', w=0.8, h=0.8, src='station 5 number post (second judge m10: the post is permanent, N837 t074 left shows it; the 2025 canopy was temporary)'),
            dict(side='right', s=1837, off=9.9, text='300', w=0.7, h=1.8, src='360 lap t072 right: "300" board right on the T4 approach (inventory row s 1813 right)'),
            dict(side='right', s=3022, off=2.1, text='200', w=0.7, h=1.8, src='N837 t106 (Apr 2026): "200" on the right fence before T11; judge r7 F3'),
            dict(side='right', s=3053, off=5.3, text='100', w=0.7, h=1.8, src='360 lap t112 right: "100" before T11 (inventory row s 3053)'),
        ],
        # sponsor boards as typed names in the observed colours (the Laguna rule; no logo artwork): hoardings standing IN FRONT of
        # the armco (round 8: 0.45 m in front from the ground; round 7 put them 0.3 m behind, hidden), 2.0 m panels (360 t050-t052 / N837 t038-t040: the hoardings stand at the armco and rise above it)
        wall_boards=[
            dict(wall='osm:1315208944', s=(905, 1050), h=2.0, base=0.0, off=0.45, panel=6.0,
                 names=[('PERMCO', '#2a5aa8', '#f2f2ee'), ('HRC', '#dcdcd8', '#a3262a'), ('SUMMIT', '#dcdcd8', '#c8202c'), ('HONDA', '#c8302a', '#f2f2ee'),
                        ('START', '#1a1a1a', '#f2f2ee'), ("O'REILLY", '#c8302a', '#2e9e48'), ('HRC', '#e8e8e6', '#a3262a')],
                 src='N837 OJaBJz18xEo t038-t040 (Apr 2026): the Keyhole outside board wall PERMCO, HRC, SUMMIT, HONDA, START, O\'REILLY, HRC; 360 t048-t054 left (2025: HONDA, Firestone, Velo, PERMCO); inventory rows s 912-1044 left'),
            dict(wall='osm:1315208940', s=(1915, 1949), h=2.0, base=0.0, off=0.45, panel=6.0,
                 names=[('HONDA', '#c8302a', '#f2f2ee')],
                 src='360 lap t074-t076 left: Honda board wall along the T4 outside; N837 t064 left sponsor boards; inventory rows s 1898-1952 left'),
            dict(wall='osm:1315208951', s=(2050, 2110), h=1.2, base=0.0, off=0.45, panel=6.0,
                 names=[('HONDA', '#f2f2ee', '#c8302a'), ('HONDA', '#f2f2ee', '#c8302a')],
                 src='360 lap t080 right: HONDA HONDA HONDA board wall on the T5 hillside (red text on white, black base) standing IN FRONT of the armco (second judge M2: round 7 put the panels 0.3 m behind the 1.2 m armco, hidden; pose still t5board); t082 right Honda boards; inventory rows s 2051-2100 right'),
            dict(wall='osm:1315208937', s=(2280, 2380), h=1.5, base=0.0, off=0.45, panel=6.0,
                 names=[('Firestone', '#e8e8e6', '#b3242a'), ('HONDA', '#c8302a', '#f2f2ee')],
                 src='360 lap t088-t092 left: Firestone then Honda boards through T7; inventory rows s 2269-2371 left'),
            dict(wall='osm:1315208923', s=(3555, 3596), h=2.0, base=0.0, off=0.45, panel=8.0,
                 names=[('HONDA', '#c8302a', '#f2f2ee')],
                 src='360 lap t130 right: the large HONDA board wall after the main grandstand (white text on red); inventory row s 3557 right'),
            dict(wall='osm:1315208942', s=(1500, 1557), h=2.0, base=0.0, off=0.45, panel=6.0,
                 names=[('HONDA', '#c8302a', '#f2f2ee'), ('NTT DATA', '#1f3f8f', '#f2f2ee')],
                 src='360 lap t066 left: Honda and NTT Data boards on the fence; N837 t054 left: the HONDA billboard; inventory rows s 1527-1528 left'),
            # judge r7 F16-F18: boards the sheets showed missing
            dict(wall='osm:1315208943', s=(963, 1070), h=2.0, base=0.0, off=0.45, panel=6.0,
                 names=[('PERMCO', '#2a5aa8', '#f2f2ee'), ('VELO', '#2f6db3', '#f2f2ee'), ('SUMMIT', '#dcdcd8', '#c8202c'), ('HONDA', '#c8302a', '#f2f2ee'),
                        ('START', '#1a1a1a', '#f2f2ee'), ("O'REILLY", '#c8302a', '#2e9e48'), ('HRC', '#e8e8e6', '#a3262a'), ('Firestone', '#e8e8e6', '#b3242a')],
                 src='round 8 full-walk judge (row_s1035_left): the Keyhole-exit board wall continues past OSM 944 onto 943; 360 lap t053-t055 left (PERMCO, VELO, HONDA, START, O\'REILLY, HRC, Firestone), N837 t040-t042'),
            dict(wall='osm:1315208956', s=(3048, 3058), h=1.6, base=1.4, off=0.05, panel=6.0, names=[('VELO', '#2f6db3', '#f2f2ee')],
                 src='360 lap t112 right (Jul 2025): a blue VELO banner high on the catch fence before T11 (second judge m9)'),
            dict(wall='pit wall', s=(150, 212), h=0.9, base=0.05, off=-0.25, panel=6.0, single=True, names=[('VELO', '#2f6db3', '#f2f2ee')],
                 src='360 lap t028-t029.5 left (Jul 2025): VELO banners on the pit wall toward the footbridge (inventory pit row s 154); judge r7 runoff_00'),
            dict(wall='pit-in barrier', s=(3405, 3452), h=1.2, base=0.0, off=0.15, panel=6.0, names=[('HONDA', '#f2f2ee', '#c8302a')],
                 src='360 lap t017-t018.5 left: HONDA banners along the pit-in barrier (red text on white; inventory row s 3422 left); judge r7 side_33'),
            dict(wall='osm:1315208933', s=(2860, 2916), h=1.6, base=1.4, off=0.05, panel=6.0, names=[('VELO', '#2f6db3', '#f2f2ee')],
                 src='360 lap t108 left (Jul 2025): VELO banners on the fence at the PERMCO bridge (inventory row s 2880 left); judge r7 side_28'),
        ],
        pit_lane_clip_walls=True,
        zones_meet_edge=True,    # round 7: the closed roads' ends meet the course at their mouths (no dirt wedge; the owner's green turns into the mouth)
        paved_zones_over=True,   # round 7: the closed roads drawn over the course shoulders at their mouths
        pit_lane_clip_heads=True,   # round 7: the lane edge clears the pit wall's end where the ladder line takes over (pit connectivity, build 5)
        # judge r7 F12: tree shadows the 2022 NAIP baked into the road (dark patches the hood camera sees, fwd s 2150 and the back
        # straight 1330-1600); found by r7 road-luminance scan (road median per station 15+ below its 101-station median), each
        # stretch +-4 stations painted to the road's median ('dark'); the bridge shadow at s 221-227 is left (a real shadow there)
        ortho_paint_over=[
            dict(latlon=[(40.6895791, -82.6322178), (40.6895529, -82.6322073), (40.6895266, -82.6321969), (40.6895001, -82.6321866), (40.6894733, -82.6321767), (40.6894462, -82.6321673), (40.6894186, -82.6321587), (40.6893905, -82.6321511), (40.689362, -82.6321447), (40.689333, -82.6321399), (40.6893036, -82.6321369), (40.6892739, -82.6321358), (40.6892441, -82.6321369), (40.6892143, -82.6321401), (40.6891846, -82.6321454), (40.6891552, -82.6321529), (40.6891261, -82.6321624), (40.6890975, -82.6321738), (40.6890694, -82.632187), (40.6890419, -82.6322019), (40.6890151, -82.6322184), (40.6890642, -82.6323476), (40.6890863, -82.632334), (40.6891087, -82.6323219), (40.6891315, -82.6323115), (40.6891546, -82.6323026), (40.6891779, -82.6322954), (40.6892015, -82.6322899), (40.6892253, -82.632286), (40.6892493, -82.6322838), (40.6892734, -82.6322832), (40.6892977, -82.6322841), (40.6893221, -82.6322865), (40.6893467, -82.6322902), (40.6893714, -82.6322952), (40.6893963, -82.6323012), (40.6894213, -82.6323082), (40.6894465, -82.6323161), (40.6894718, -82.6323246), (40.6894972, -82.6323337), (40.6895226, -82.6323432), (40.6895481, -82.632353)], src='round 8 full-walk judge (back_s3300, second judge m14): a pale NAIP blotch on the road at s ~3250-3280'),
            dict(latlon=[(40.6895791, -82.6322178), (40.6895529, -82.6322073), (40.6895266, -82.6321969), (40.6895001, -82.6321866), (40.6894733, -82.6321767), (40.6894462, -82.6321673), (40.6894186, -82.6321587), (40.6893905, -82.6321511), (40.689362, -82.6321447), (40.689333, -82.6321399), (40.6893036, -82.6321369), (40.6892739, -82.6321358), (40.6892441, -82.6321369), (40.6892143, -82.6321401), (40.6891846, -82.6321454), (40.6891552, -82.6321529), (40.6891261, -82.6321624), (40.6890975, -82.6321738), (40.6890694, -82.632187), (40.6890419, -82.6322019), (40.6890151, -82.6322184), (40.6890642, -82.6323476), (40.6890863, -82.632334), (40.6891087, -82.6323219), (40.6891315, -82.6323115), (40.6891546, -82.6323026), (40.6891779, -82.6322954), (40.6892015, -82.6322899), (40.6892253, -82.632286), (40.6892493, -82.6322838), (40.6892734, -82.6322832), (40.6892977, -82.6322841), (40.6893221, -82.6322865), (40.6893467, -82.6322902), (40.6893714, -82.6322952), (40.6893963, -82.6323012), (40.6894213, -82.6323082), (40.6894465, -82.6323161), (40.6894718, -82.6323246), (40.6894972, -82.6323337), (40.6895226, -82.6323432), (40.6895481, -82.632353)], dark=True, src='round 8 second walk (back_s3300): the dark half of the same NAIP blotch on the road at s ~3250-3280'),
            dict(latlon=[(40.6893908, -82.6353164), (40.6893908, -82.6352335), (40.6894671, -82.6352335), (40.6894671, -82.6353164)], on='any', all=True, src='boundary audit r7 B1: the red post of the starter\'s stand (c20_s3560 / c20_s0000) baked into the ortho as a red smear on the pit lane beside the modelled stand (edge_L_0000)'),
            dict(latlon=[(40.6841975, -82.6401885), (40.6842264, -82.6401988), (40.6842555, -82.640207), (40.6842845, -82.6402132), (40.6843134, -82.6402177), (40.684342, -82.6402208), (40.6843703, -82.6402229), (40.684384, -82.6400846), (40.6843583, -82.6400834), (40.684333, -82.6400812), (40.6843081, -82.6400778), (40.6842837, -82.6400729), (40.6842599, -82.6400664), (40.6842366, -82.640058)], dark=True, src='road-luminance scan s 1018-1029: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6870129, -82.6403402), (40.6870399, -82.640341), (40.6870668, -82.6403418), (40.6870938, -82.6403425), (40.6871207, -82.6403433), (40.6871477, -82.640344), (40.6871503, -82.6402015), (40.6871233, -82.6402005), (40.6870964, -82.6401995), (40.6870694, -82.6401985), (40.6870424, -82.6401975), (40.6870155, -82.6401965)], dark=True, src='road-luminance scan s 1330-1337: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6871656, -82.6403445), (40.6871926, -82.6403453), (40.6872195, -82.6403462), (40.6872465, -82.6403471), (40.6872735, -82.640348), (40.6873005, -82.6403489), (40.6873275, -82.6403499), (40.6873545, -82.6403508), (40.6873658, -82.640208), (40.6873389, -82.6402074), (40.687312, -82.6402067), (40.6872851, -82.640206), (40.6872582, -82.6402052), (40.6872312, -82.6402044), (40.6872043, -82.6402035), (40.6871773, -82.6402025)], dark=True, src='road-luminance scan s 1347-1361: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6873635, -82.6403511), (40.6873906, -82.6403519), (40.6874176, -82.6403528), (40.6874446, -82.6403535), (40.6874717, -82.6403542), (40.6874987, -82.6403548), (40.6875257, -82.6403554), (40.6875451, -82.6402114), (40.6875182, -82.640211), (40.6874913, -82.6402105), (40.6874644, -82.64021), (40.6874375, -82.6402095), (40.6874106, -82.640209), (40.6873838, -82.6402084)], dark=True, src='road-luminance scan s 1369-1381: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6876788, -82.6403577), (40.6877058, -82.640358), (40.6877328, -82.6403583), (40.6877598, -82.6403585), (40.6877868, -82.6403587), (40.6878138, -82.6403588), (40.6878409, -82.6403589), (40.6878681, -82.6403588), (40.6878953, -82.6403587), (40.6878947, -82.6402142), (40.687868, -82.6402144), (40.6878412, -82.6402144), (40.6878144, -82.6402143), (40.6877875, -82.6402142), (40.6877606, -82.640214), (40.6877337, -82.6402137), (40.6877067, -82.6402135), (40.6876797, -82.6402132)], dark=True, src='road-luminance scan s 1404-1420: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6879682, -82.6403578), (40.6879956, -82.6403572), (40.6880231, -82.6403563), (40.6880507, -82.6403552), (40.6880782, -82.6403538), (40.6881057, -82.640352), (40.6881063, -82.6402029), (40.68808, -82.6402056), (40.6880537, -82.6402079), (40.6880273, -82.6402098), (40.6880009, -82.6402113), (40.6879745, -82.6402125)], dark=True, src='road-luminance scan s 1436-1444: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6891701, -82.6400383), (40.6891958, -82.6400259), (40.6892214, -82.6400134), (40.6892469, -82.6400007), (40.6892724, -82.6399879), (40.6892978, -82.6399751), (40.6892752, -82.6398338), (40.6892502, -82.6398464), (40.6892252, -82.6398588), (40.6892002, -82.639871), (40.6891752, -82.6398832), (40.6891502, -82.6398952)], dark=True, src='road-luminance scan s 1571-1580: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6892809, -82.6399837), (40.6893062, -82.6399708), (40.6893316, -82.639958), (40.6893568, -82.6399452), (40.689382, -82.6399324), (40.6894072, -82.6399196), (40.6894323, -82.6399069), (40.6894574, -82.6398941), (40.6894825, -82.6398814), (40.6894512, -82.6397439), (40.689426, -82.6397568), (40.6894008, -82.6397697), (40.6893756, -82.6397826), (40.6893504, -82.6397955), (40.6893253, -82.6398084), (40.6893002, -82.6398212), (40.6892752, -82.6398338), (40.6892502, -82.6398464)], dark=True, src='road-luminance scan s 1584-1601: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6924388, -82.6377565), (40.6924322, -82.6377189), (40.6924246, -82.6376818), (40.6924158, -82.6376452), (40.692406, -82.6376092), (40.6923055, -82.6376609), (40.6923141, -82.6376919), (40.6923216, -82.6377231), (40.6923281, -82.6377546), (40.6923335, -82.6377863)], dark=True, src='road-luminance scan s 1995-1999: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6923638, -82.636352), (40.6923873, -82.6363451), (40.6924114, -82.6363398), (40.6924359, -82.6363359), (40.6924608, -82.6363331), (40.6924862, -82.6363312), (40.6925118, -82.6363301), (40.6925378, -82.6363295), (40.692564, -82.6363295), (40.6925904, -82.6363297), (40.6926169, -82.6363302), (40.6926436, -82.6363309), (40.6926703, -82.6363318), (40.692697, -82.6363329), (40.6927237, -82.6363341), (40.6927504, -82.6363355), (40.6927771, -82.636337), (40.6928038, -82.6363387), (40.6928305, -82.6363405), (40.6928572, -82.6363426), (40.692884, -82.6363447), (40.6929108, -82.636347), (40.6929358, -82.6362032), (40.6929088, -82.6362008), (40.6928818, -82.6361985), (40.6928547, -82.6361961), (40.6928276, -82.6361939), (40.6928005, -82.6361918), (40.6927733, -82.6361899), (40.6927461, -82.6361882), (40.6927189, -82.6361867), (40.6926917, -82.6361854), (40.6926645, -82.6361844), (40.6926373, -82.6361837), (40.6926099, -82.6361832), (40.6925825, -82.636183), (40.6925549, -82.6361832), (40.6925271, -82.6361839), (40.6924991, -82.6361852), (40.6924708, -82.6361872), (40.6924422, -82.6361903), (40.6924133, -82.6361946), (40.6923843, -82.6362005), (40.6923552, -82.6362083)], dark=True, src='road-luminance scan s 2144-2151, widened to 2140-2205 after the judge r7 re-shoot (fwd s 2150: the tree shadow runs on to ~2200)'),
            dict(latlon=[(40.6933683, -82.6363683), (40.6933978, -82.6363639), (40.6934274, -82.6363573), (40.6934571, -82.6363482), (40.6934865, -82.6363362), (40.6935155, -82.6363211), (40.6934718, -82.6361886), (40.6934505, -82.6361996), (40.6934284, -82.6362085), (40.6934055, -82.6362156), (40.693382, -82.6362209), (40.6933579, -82.6362246)], dark=True, src='road-luminance scan s 2257-2264: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6937375, -82.6359318), (40.6937423, -82.6358936), (40.693746, -82.6358558), (40.6937488, -82.6358183), (40.693751, -82.6357811), (40.6937526, -82.635744), (40.6937536, -82.6357071), (40.6937541, -82.6356702), (40.6936442, -82.6356589), (40.6936439, -82.6356932), (40.6936431, -82.6357274), (40.6936418, -82.6357614), (40.69364, -82.6357951), (40.6936378, -82.6358285), (40.693635, -82.6358613), (40.6936316, -82.6358936)], dark=True, src='road-luminance scan s 2309-2323: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6914662, -82.6323613), (40.6914429, -82.6323809), (40.6914197, -82.632401), (40.6913968, -82.6324214), (40.6913741, -82.6324423), (40.6914308, -82.6325699), (40.6914525, -82.6325502), (40.6914743, -82.632531), (40.6914963, -82.6325121), (40.6915185, -82.6324935)], dark=True, src='road-luminance scan s 2995-3000: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6905286, -82.6328795), (40.6905047, -82.6328684), (40.6904811, -82.6328563), (40.6904577, -82.6328432), (40.6904345, -82.6328292), (40.6904115, -82.6328144), (40.6903631, -82.6329434), (40.6903888, -82.6329593), (40.6904148, -82.6329743), (40.6904413, -82.6329884), (40.690468, -82.6330016), (40.6904951, -82.6330138)], dark=True, src='road-luminance scan s 3119-3126: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6904345, -82.6328292), (40.6904115, -82.6328144), (40.6903888, -82.6327989), (40.6903663, -82.6327826), (40.6903441, -82.6327656), (40.690322, -82.6327478), (40.6903001, -82.6327294), (40.6902783, -82.6327104), (40.6902017, -82.6328189), (40.6902248, -82.6328391), (40.6902482, -82.632859), (40.6902721, -82.6328783), (40.6902964, -82.632897), (40.6903211, -82.6329151), (40.6903461, -82.6329323), (40.6903716, -82.6329488)], dark=True, src='road-luminance scan s 3131-3146: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6887462, -82.6330931), (40.6887627, -82.6331272), (40.6887808, -82.6331596), (40.6888003, -82.6331902), (40.6888211, -82.6332191), (40.6888429, -82.6332462), (40.6888656, -82.6332715), (40.688889, -82.6332951), (40.6889129, -82.6333172), (40.6889865, -82.6332121), (40.6889656, -82.6331943), (40.6889454, -82.6331757), (40.6889262, -82.6331559), (40.688908, -82.633135), (40.688891, -82.6331128), (40.6888753, -82.6330893), (40.688861, -82.6330646), (40.6888481, -82.6330388)], dark=True, src='road-luminance scan s 3379-3397: a tree shadow on the NAIP road (judge r7 F12)'),
            dict(latlon=[(40.6893567, -82.6338433), (40.6893621, -82.6338753), (40.6893665, -82.6339082), (40.6893703, -82.6339417), (40.6893738, -82.6339758), (40.6894829, -82.6339716), (40.6894799, -82.6339353), (40.6894769, -82.6338985), (40.6894737, -82.6338612), (40.68947, -82.6338233)], dark=True, src='road-luminance scan s 3477-3482: a tree shadow on the NAIP road (judge r7 F12)'),
        ],
        # the unmodelled-ground-lines scan (round 13 gate, gates/ground_lines.py): every one of the 107 findings of the round-7
        # package reviewed on its ortho crop (round7.md section 13) and dispositioned; the key makes the gate strict on this track
        ground_lines=dict(dispositions=[
            # round 8: the lines the grass tone made visible (r8 build 5 crops, round8.md 2a)
            dict(side='left', s=(2595.0, 2618.0), tone='dark', what='the armco and its shadow (modelled OSM run within 2-6 m)', why='accepted as built: the T8-T9 back armco (OSM 1315208935, 38-48 m out) and its shadow, found after the round-8 grass hue (build 8)'),
            dict(side='left', s=(468.0, 489.0), tone='pale', what='paddock service road edge beyond the fence', why='accepted as built: the paddock road 32-34 m out behind the T1-exit fence (as round-7 finding 2 of this stretch), found after the round-8 grass hue (build 8)'),
            dict(side='left', s=(2822.0, 2859.0), tone='dark', what='paddock service road edge beside the trees (beyond the fence)', why='accepted as built: found after the round-8 grass tone lifted the grass beside it (r8 finding 0, 42-59 m out); paddock service road edge beside the trees (beyond the fence)'),
            dict(side='left', s=(2864.0, 2914.0), tone='dark', what='the armco and its shadow (modelled OSM run within 2-6 m)', why='accepted as built: found after the round-8 grass tone lifted the grass beside it (r8 finding 1, 5-8 m out); the armco and its shadow (modelled OSM run within 2-6 m)'),
            dict(side='left', s=(3060.1, 3101.1), tone='dark', what='the edge of the ploughed field beyond the PERMCO-bridge fence (off the circuit)', why='accepted as built: found after the round-8 grass tone lifted the grass beside it (r8 finding 2, 19-25 m out); the edge of the ploughed field beyond the PERMCO-bridge fence (off the circuit)'),
            dict(side='left', s=(3124.2, 3209.2), tone='dark', what='the armco and its shadow (modelled OSM run within 2-6 m)', why='accepted as built: found after the round-8 grass tone lifted the grass beside it (r8 finding 3, 13-20 m out); the armco and its shadow (modelled OSM run within 2-6 m)'),
            dict(side='left', s=(3367.3, 3388.3), tone='dark', what='the armco head and the parked vehicles behind it at T11 (the 2022 NAIP)', why='accepted as built: found after the round-8 grass tone lifted the grass beside it (r8 finding 4, 17-31 m out); the armco head and the parked vehicles behind it at T11 (the 2022 NAIP)'),
            dict(side='left', s=(1268.9, 1301.9), tone='dark', what='the armco and its shadow (modelled OSM run within 2-6 m)', why='accepted as built: found after the round-8 grass tone lifted the grass beside it (r8 finding 5, 8-9 m out); the armco and its shadow (modelled OSM run within 2-6 m)'),
            dict(side='left', s=(510.4, 539.4), tone='pale', what='the pit-in island wall and its shadow (modelled: pit wall, pit-in barrier)', why='accepted as built: found after the round-8 grass tone lifted the grass beside it (r8 finding 6, 31-34 m out); the pit-in island wall and its shadow (modelled: pit wall, pit-in barrier)'),
            dict(side='left', s=(0.0, 27.0), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 0, 23-24 m out)'),
            dict(side='left', s=(4.0, 24.0), tone='pale', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 1, 43-60 m out)'),
            dict(side='left', s=(101.1, 128.1), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 2, 37-41 m out)'),
            dict(side='left', s=(102.1, 141.1), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 3, 28-33 m out)'),
            dict(side='left', s=(112.1, 140.1), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 4, 32-36 m out)'),
            dict(side='left', s=(148.1, 182.1), tone='dark', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 5, 27-30 m out)'),
            dict(side='left', s=(222.2, 227.2), tone='dark', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 6, 14-60 m out)"),
            dict(side='left', s=(229.2, 231.2), tone='pale', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 7, 28-56 m out)"),
            dict(side='left', s=(237.2, 240.2), tone='dark', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 8, 17-49 m out)"),
            dict(side='left', s=(398.3, 420.3), tone='dark', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 9, 46-60 m out)'),
            dict(side='left', s=(412.3, 441.3), tone='pale', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 10, 40-60 m out)'),
            dict(side='left', s=(416.3, 442.3), tone='dark', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 11, 43-60 m out)'),
            dict(side='left', s=(422.3, 440.3), tone='dark', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 12, 37-49 m out)'),
            dict(side='left', s=(427.3, 446.3), tone='pale', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 13, 25-35 m out)'),
            dict(side='left', s=(575.4, 632.4), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 14, 55-59 m out)'),
            dict(side='left', s=(639.4, 671.5), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 15, 56-59 m out)'),
            dict(side='left', s=(734.5, 760.5), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 16, 12-12 m out)'),
            dict(side='left', s=(866.6, 913.6), tone='pale', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 17, 18-28 m out)"),
            dict(side='left', s=(872.6, 930.6), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 18, 2-5 m out)"),
            dict(side='left', s=(916.6, 932.6), tone='pale', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 19, 32-36 m out)'),
            dict(side='left', s=(931.6, 961.7), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 20, 2-4 m out)"),
            dict(side='left', s=(960.7, 973.7), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 21, 6-41 m out)'),
            dict(side='left', s=(962.7, 1004.7), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 22, 19-40 m out)'),
            dict(side='left', s=(965.7, 974.7), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 23, 41-52 m out)'),
            dict(side='left', s=(967.7, 984.7), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 24, 43-54 m out)'),
            dict(side='left', s=(975.7, 1003.7), tone='pale', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 25, 9-13 m out)"),
            dict(side='left', s=(987.7, 1020.7), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 26, 3-5 m out)"),
            dict(side='left', s=(999.7, 1009.7), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 27, 39-44 m out)'),
            dict(side='left', s=(1014.7, 1036.7), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 28, 35-41 m out)'),
            dict(side='left', s=(1018.7, 1055.7), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 29, 51-55 m out)'),
            dict(side='left', s=(1024.7, 1050.7), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 30, 5-8 m out)"),
            dict(side='left', s=(1029.7, 1088.8), tone='pale', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 31, 2-4 m out)"),
            dict(side='left', s=(1064.7, 1122.8), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 32, 31-36 m out)'),
            dict(side='left', s=(1080.7, 1120.8), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 33, 38-51 m out)'),
            dict(side='left', s=(1102.8, 1266.9), tone='pale', what='the armco itself in the NAIP', why='accepted as built: the bright or dark band of the armco beam; the modelled OSM run lies within 2-6 m of it (finding 34, 9-16 m out)'),
            dict(side='left', s=(1127.8, 1265.9), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 35, 32-38 m out)'),
            dict(side='left', s=(1686.2, 1750.2), tone='pale', what='the armco itself in the NAIP', why='accepted as built: the bright or dark band of the armco beam; the modelled OSM run lies within 2-6 m of it (finding 36, 6-6 m out)'),
            dict(side='left', s=(1798.2, 1836.3), tone='dark', what="the bleachers' rows or their pad", why='accepted as built: the seat rows / gravel pad of the T4 bleachers (modelled as structures) seen in the ortho (finding 37, 22-23 m out)'),
            dict(side='left', s=(1815.3, 1855.3), tone='pale', what="the bleachers' rows or their pad", why='accepted as built: the seat rows / gravel pad of the T4 bleachers (modelled as structures) seen in the ortho (finding 38, 18-23 m out)'),
            dict(side='left', s=(1841.3, 1938.3), tone='pale', what='the armco itself in the NAIP', why='accepted as built: the bright or dark band of the armco beam; the modelled OSM run lies within 2-6 m of it (finding 39, 10-17 m out)'),
            dict(side='left', s=(1867.3, 1888.3), tone='pale', what='mown line or footpath in the grass', why='accepted as built: a mowing stripe or worn footpath in the infield / verge (ortho crop); no object in the footage (finding 40, 20-23 m out)'),
            dict(side='left', s=(1905.3, 1948.3), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 41, 15-28 m out)'),
            dict(side='left', s=(1913.3, 1951.4), tone='dark', what="the bleachers' rows or their pad", why='accepted as built: the seat rows / gravel pad of the T4 bleachers (modelled as structures) seen in the ortho (finding 42, 22-37 m out)'),
            dict(side='left', s=(1925.3, 1953.4), tone='pale', what="the bleachers' rows or their pad", why='accepted as built: the seat rows / gravel pad of the T4 bleachers (modelled as structures) seen in the ortho (finding 43, 21-35 m out)'),
            dict(side='left', s=(1951.4, 1966.4), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 44, 28-52 m out)"),
            dict(side='left', s=(1953.4, 1964.4), tone='pale', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 45, 35-48 m out)"),
            dict(side='left', s=(2055.4, 2163.5), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 46, 31-44 m out)'),
            dict(side='left', s=(2177.5, 2209.5), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 47, 46-58 m out)'),
            dict(side='left', s=(2181.5, 2202.5), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 48, 40-50 m out)'),
            dict(side='left', s=(2184.5, 2261.6), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 49, 12-22 m out)'),
            dict(side='left', s=(2205.5, 2229.5), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 50, 50-60 m out)'),
            dict(side='left', s=(2270.6, 2282.6), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 51, 14-22 m out)'),
            dict(side='left', s=(2526.7, 2607.8), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 52, 50-60 m out)'),
            dict(side='left', s=(2608.8, 2628.8), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 53, 50-53 m out)'),
            dict(side='left', s=(2629.8, 2639.8), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 54, 53-60 m out)'),
            dict(side='left', s=(2632.8, 2707.9), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 55, 2-3 m out)"),
            dict(side='left', s=(2755.9, 2800.9), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 56, 25-28 m out)'),
            dict(side='left', s=(2783.9, 2805.9), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 57, 33-36 m out)'),
            dict(side='left', s=(2839.0, 2870.0), tone='pale', what="the PERMCO footbridge's abutment and stairs", why='accepted as built: the bridge footprint (modelled with bridge_stairs) (finding 58, 3-10 m out)'),
            dict(side='left', s=(2941.0, 2994.1), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 59, 30-40 m out)'),
            dict(side='left', s=(2947.0, 2965.1), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 60, 25-27 m out)'),
            dict(side='left', s=(2949.0, 2994.1), tone='dark', what='mown line or footpath in the grass', why='accepted as built: a mowing stripe or worn footpath in the infield / verge (ortho crop); no object in the footage (finding 61, 8-12 m out)'),
            dict(side='left', s=(3001.1, 3021.1), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 62, 42-60 m out)'),
            dict(side='left', s=(3098.1, 3122.2), tone='pale', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 63, 9-28 m out)"),
            dict(side='left', s=(3177.2, 3222.2), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 64, 35-60 m out)'),
            dict(side='left', s=(3237.2, 3331.3), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 65, 27-48 m out)'),
            dict(side='left', s=(3311.3, 3328.3), tone='dark', what='paddock tents / parked trailers', why='accepted as built: temporary paddock objects in the 2022 NAIP (finding 66, 33-42 m out)'),
            dict(side='left', s=(3345.3, 3358.3), tone='dark', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 67, 50-54 m out)'),
            dict(side='left', s=(3354.3, 3366.3), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 68, 55-60 m out)'),
            dict(side='left', s=(3389.3, 3460.4), tone='dark', what='the pit-in island and its barrier', why="accepted as built: the white island wall / the pit-in barrier's shadow and the lane's edge paint (modelled: pit wall, pit-in barrier, pit lane paving) (finding 69, 18-37 m out)"),
            dict(side='left', s=(3403.4, 3474.4), tone='pale', what='the pit-in island and its barrier', why="accepted as built: the white island wall / the pit-in barrier's shadow and the lane's edge paint (modelled: pit wall, pit-in barrier, pit lane paving) (finding 70, 5-10 m out)"),
            dict(side='left', s=(3404.4, 3433.4), tone='dark', what='the pit-in island and its barrier', why="accepted as built: the white island wall / the pit-in barrier's shadow and the lane's edge paint (modelled: pit wall, pit-in barrier, pit lane paving) (finding 71, 10-12 m out)"),
            dict(side='left', s=(3411.4, 3438.4), tone='dark', what='the pit-in island and its barrier', why="accepted as built: the white island wall / the pit-in barrier's shadow and the lane's edge paint (modelled: pit wall, pit-in barrier, pit lane paving) (finding 72, 28-34 m out)"),
            dict(side='left', s=(3426.4, 3470.4), tone='dark', what='the pit-in island and its barrier', why="accepted as built: the white island wall / the pit-in barrier's shadow and the lane's edge paint (modelled: pit wall, pit-in barrier, pit lane paving) (finding 73, 2-5 m out)"),
            dict(side='left', s=(3534.4, 3568.5), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 74, 23-25 m out)'),
            dict(side='right', s=(86.1, 108.1), tone='dark', what='building edge or its shadow', why='accepted as built: a building footprint or its shadow in the NAIP (ortho crop); the building is modelled or off the scenery band (finding 75, 46-52 m out)'),
            dict(side='right', s=(148.1, 185.1), tone='dark', what='asphalt shoulder seam at the right edge', why='accepted as built: a dark strip beside the right edge of the pit straight (c20_s0120); the 360 lap t028 right shows grass to the armco, no object (finding 76, 2-3 m out)'),
            dict(side='right', s=(215.1, 218.2), tone='pale', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 77, 14-51 m out)"),
            dict(side='right', s=(225.2, 227.2), tone='dark', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 78, 4-36 m out)"),
            dict(side='right', s=(232.2, 234.2), tone='pale', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 79, 27-55 m out)"),
            dict(side='right', s=(235.2, 236.2), tone='dark', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 80, 33-57 m out)"),
            dict(side='right', s=(235.2, 238.2), tone='pale', what="the T1 footbridge's access road and its shadow", why="accepted as built: the bridge's approach road under / beside the deck (OSM 444205416) and the deck's shadow; not a barrier (360 t030) (finding 81, 33-60 m out)"),
            dict(side='right', s=(282.2, 376.3), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 82, 2-4 m out)"),
            dict(side='right', s=(399.3, 471.3), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 83, 5-12 m out)"),
            dict(side='right', s=(401.3, 451.3), tone='pale', what="the kerb's outer edge / sand beside it", why='accepted as built: the outer limit of a modelled kerb band and the sand beyond it (finding 84, 2-3 m out)'),
            dict(side='right', s=(1125.8, 1176.8), tone='pale', what='mown line or footpath in the grass', why='accepted as built: a mowing stripe or worn footpath in the infield / verge (ortho crop); no object in the footage (finding 85, 4-7 m out)'),
            dict(side='right', s=(1140.8, 1178.8), tone='dark', what='mown line or footpath in the grass', why='accepted as built: a mowing stripe or worn footpath in the infield / verge (ortho crop); no object in the footage (finding 86, 2-3 m out)'),
            dict(side='right', s=(1489.0, 1603.1), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 87, 16-31 m out)'),
            dict(side='right', s=(1591.1, 1628.1), tone='pale', what='dark enclosure inside the T3-right armco outline', why="accepted as built: a dark 25 x 3 m object inside the barrier outline OSM 1315208948 traces; no frame of the four videos shows it (OPEN: tyres or a ditch, for the owner's drive) (finding 88, 11-18 m out)"),
            dict(side='right', s=(1602.1, 1634.1), tone='pale', what='dark enclosure inside the T3-right armco outline', why="accepted as built: a dark 25 x 3 m object inside the barrier outline OSM 1315208948 traces; no frame of the four videos shows it (OPEN: tyres or a ditch, for the owner's drive) (finding 89, 20-22 m out)"),
            dict(side='right', s=(1607.1, 1634.1), tone='dark', what='dark enclosure inside the T3-right armco outline', why="accepted as built: a dark 25 x 3 m object inside the barrier outline OSM 1315208948 traces; no frame of the four videos shows it (OPEN: tyres or a ditch, for the owner's drive) (finding 90, 26-29 m out)"),
            dict(side='right', s=(1684.2, 1942.3), tone='pale', what='the armco itself in the NAIP', why='accepted as built: the bright or dark band of the armco beam; the modelled OSM run lies within 2-6 m of it (finding 91, 10-18 m out)'),
            dict(side='right', s=(1716.2, 1736.2), tone='pale', what='mown line or footpath in the grass', why='accepted as built: a mowing stripe or worn footpath in the infield / verge (ortho crop); no object in the footage (finding 92, 25-26 m out)'),
            dict(side='right', s=(1764.2, 1768.2), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 93, 40-60 m out)'),
            dict(side='right', s=(2053.4, 2075.4), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 94, 11-13 m out)'),
            dict(side='right', s=(2110.5, 2157.5), tone='pale', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 95, 12-20 m out)'),
            dict(side='right', s=(2129.5, 2136.5), tone='dark', what="the T5 scoring pylon's shadow", why="accepted as built: the long shadow of the 30.7 m pylon (modelled, structures 'T5 scoring pylon') (finding 96, 42-60 m out)"),
            dict(side='right', s=(2132.5, 2136.5), tone='pale', what="the T5 scoring pylon's shadow", why="accepted as built: the long shadow of the 30.7 m pylon (modelled, structures 'T5 scoring pylon') (finding 97, 40-59 m out)"),
            dict(side='right', s=(2718.9, 2832.0), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 98, 2-21 m out)'),
            dict(side='right', s=(2780.9, 2801.9), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 99, 8-11 m out)'),
            dict(side='right', s=(3060.1, 3134.2), tone='dark', what='gravel trap / grass boundary', why="accepted as built: the edge between the grass verge and the sand / gravel trap (inventory runoff rows: 'grass then sand/gravel'); ground classes come from the ortho (finding 100, 2-4 m out)"),
            dict(side='right', s=(3087.1, 3239.2), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 101, 23-30 m out)'),
            dict(side='right', s=(3103.1, 3454.4), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 102, 39-60 m out)'),
            dict(side='right', s=(3479.4, 2.0), tone='dark', what="the kerb's outer edge / sand beside it", why='accepted as built: the outer limit of a modelled kerb band and the sand beyond it (finding 103, 2-4 m out)'),
            dict(side='right', s=(3482.4, 3502.4), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 104, 15-17 m out)'),
            dict(side='right', s=(3503.4, 3.0), tone='dark', what='shadow of the modelled armco / catch fence', why='accepted as built: the NAIP band beside a modelled barrier run (within 2-6 m): the armco or fence and its shadow; the run is modelled from OSM and the footage (finding 105, 14-18 m out)'),
            dict(side='right', s=(3586.5, 3597.5), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 106, 55-60 m out)'),
            dict(side='right', s=(0.0, 93.1), tone='pale', what='paddock / service road edge or curb', why='accepted as built: beyond the barriers and fences, in the paddock or on a service path the course cannot reach (ortho crop, judge r7 ground-lines review); no barrier there in the footage (finding 106, 55-60 m out)'),
        ]),
        # round 8 (owner's drive: "some grass is missing or is inexplicably dark or gray"; round8.md 1a): the NAIP grass is dull
        # and dark (median luminance ~62 on the near ortho, 60-95 % of the 3-40 m bands under 70) against the in-season grass
        # of the 2026 clean captures (median of 3.4 M grass pixels over all 91 captures (86.0, 103.0, 87.0), r8/capture_grass.json);
        # the grass pixels (no lidar canopy or roof over them) take that tone at their own relative luminance. Target: the
        # captures' luminance (98) with the hue between the captures' (B / G 0.84) and the in-season frames' (N837 t026-t104
        # (104-122, 116-140, 55-97) and the 360 lap t040-t110: B / G 0.32-0.70, R / G 0.78-0.90): R / G 0.85, B / G 0.65 ->
        # (93, 110, 71). The first round-8 pass on the captures' own hue (86, 103, 87) still read grey-blue at hood level
        # (compare_sheets_r8 fwd_00, round8.md 3)
        grass_tone=dict(target=(93.0, 110.0, 71.0), chm_max=1.0, strength=1.0, local_m=40.0, deblock_px=1.0, contrast=0.7, mask_px=4.0,
                        src='2026 clean captures, grass median over all 91 (r8/capture_grass.json); 360 lap / N837 frames: green grass in season'),
        # round 8 (owner: "there should be a lot more trees, or denser trees, especially by the back straight and going through
        # Thunder Valley"; round8.md 1b): the NAIP imagery check rejected 2491 of 3729 lidar crowns (67 %: the dull NAIP grass
        # and the leaf-off canopy fail its "darker than the 35th percentile" test), so the modelled crown cover was 20-25 % of
        # the 2019 lidar canopy; off, with poles, masts and fence posts kept out by their crown size (the Buttonwillow rule)
        tree_imagery_check=False, tree_min=dict(radius=2.0, height=5.0),
        building_height_robust=True,
        # buildings: every kept OSM / lidar footprint with its evidence (capture or the NAIP ortho; round7.md building table)
        building_evidence=[
            dict(contains=(40.6891402, -82.6358293), src='c20_s0000 / c20_s3560: white-walled pit garage block with a red roof band behind the pit boxes (OSM 1315208900; 360 t026 left: red roofs behind the lane)'),
            dict(contains=(40.689207, -82.6373252), src='c20_s0080 / c20_s0040: white-walled pit garage block with a red roof band (OSM 1315208901; 360 t028 left)'),
            dict(contains=(40.6889612, -82.6365921), src='c20_s0000 / c20_s0040 (partly masked) and the NAIP ortho: the red-roofed paddock garage row (OSM 1315208902)'),
            dict(contains=(40.689144, -82.6378098), src='c20_s0120: the white building by the footbridge with the red-roofed hut beside it (OSM 1315208907)'),
            dict(contains=(40.6884299, -82.6360532), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: red hip roof behind the pit garages (OSM 1315208903; the clean captures mask it)'),
            dict(contains=(40.6884502, -82.6358023), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: red hip roof behind the pit garages (OSM 1315208904)'),
            dict(contains=(40.6881841, -82.635811), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: red roof in the paddock (OSM 1315208905)'),
            dict(contains=(40.6879316, -82.6363622), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: red roof in the paddock (OSM 1315208906)'),
            dict(contains=(40.6831959, -82.6382394), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: red-roofed hut by the Keyhole access road (OSM 1315208909)'),
            dict(contains=(40.6858892, -82.6344985), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: the large orange-roofed paddock building (OSM 1315208913)'),
            dict(contains=(40.6864487, -82.6346476), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: the white paddock building complex (OSM 1315208914)'),
            dict(contains=(40.6866376, -82.6342379), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: the white paddock building complex (OSM 1315208915)'),
            dict(contains=(40.6909467, -82.6378841), src='NAIP ortho: the red-roofed building at the picnic area right of the back straight (OSM 1315208918; c20_s1720 partly)'),
            dict(contains=(40.6917512, -82.6362013), src='c20_s2040: the red hip-roofed building right of T5 (OSM 1315208919)'),
            dict(contains=(40.6942655, -82.6349278), src='c20_s2400: the small red-roofed hut left of T8 behind the armco (OSM 1315208920)'),
            dict(contains=(40.6919104, -82.6339771), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: the toilet block in the infield, grey roof (OSM 1315208976)'),
            dict(contains=(40.6879265, -82.6371551), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: the white tent roof in the paddock (lidar box 4.1 m; 360 t036 left: the hospitality tents beyond the infield)'),
            dict(contains=(40.6909529, -82.6346376), drop=True, src='no 2026 source (the clean captures mask it, no onboard frame shows it): NAIP ortho: the red roof among the trees in the infield (lidar box 3.1 m)'),
        ],
        building_overrides=[dict(osm='1315208919', plain=True, src='second judge m11: the building right of T5 is a dark-roofed open pavilion in 360 t082 right (Jul 2025), not a windowed office; c20_s2040 shows its red hip roof; drawn plain (no window facade), its lidar height kept')],
        marks_on_surface=dict(lift=0.008, src='round 7: every ground mark on the driven surface (Sonoma round 14B rule)'),
        gates=dict(
            known_exposures=[dict(side='left', latlon=(40.6893944, -82.6382391), reason='the T1 inside armco runs to the footbridge\'s abutment, which is drawn (bridge_stairs) but is not a barrier object; the run is stopped 9 m short of it because the 2019 ground under the deck is contaminated',
                                  evidence='c20_s0160 / c20_s0200: the armco line meets the abutment; 360 lap t030 left (the abutment and the red barrier to it)'),
                             dict(side='left', latlon=(40.6926723, -82.636436), reason='the armco left from the T4 exit to T6 begins at the access-road mouth 9 m beyond the edge with no cushion or block',
                                  evidence='c20_s2120 / c20_s2080: the armco head beside the paved access road; N837 t074 left (the station-5 post, the armco from the road on)')],
            openings=[dict(latlon=(40.6926543, -82.6318867), why='the PERMCO footbridge\'s left abutment stands in the 6 m gap between the armco and the white concrete wall (c20_s2800: the bridge and its shadow across the gap)')],
            allowed=[
            dict(target='inner chicane (OSM 444205376)', side='right', a=(40.6861954, -82.6391461), b=(40.6844459, -82.6390081),
                 why='the unused inner chicane meets the track at open mouths with no barrier or cones (360 t040 ahead / t042 right; c20_s0600 / c20_s0840: open grass between); a Lemons car may cross it, as the real one could'),
            dict(target='inner chicane (OSM 444205376)', side='right', a=(40.6844459, -82.6390081), b=(40.6866009, -82.6402517),
                 why='the inner chicane seen across the open Keyhole infield (c20_s0880-c20_s1200: grass, no barrier between)'),
            dict(target='T1-T3 connector, north (OSM 444205378)', side='right', a=(40.6886666, -82.6392166), b=(40.6874985, -82.6391807),
                 why='the T1-exit connector mouth is open (360 t038-t040 right, c20_s0440: no barrier or cones)'),
            dict(target='T1-T3 connector, north (OSM 444205378)', side='right', a=(40.6873197, -82.6402782), b=(40.6886778, -82.6401542),
                 why='the connector meets the return straight at an open mouth (360 t064 right, c20_s1360: no barrier or cones)'),
            dict(target='T1-T3 connector, south (OSM 444205377)', side='right', a=(40.6873817, -82.6391765), b=(40.6861415, -82.6391443),
                 why='the south connector meets the T1-Keyhole straight at an open mouth (c20_s0560: no barrier or cones)'),
            dict(target='T1-T3 connector, south (OSM 444205377)', side='right', a=(40.6861337, -82.6402302), b=(40.6873557, -82.6402793),
                 why='the south connector meets the return straight at an open mouth (c20_s1240 / c20_s1280: no barrier or cones)'),
            dict(target='pit lane', side='left', a=(40.6887509, -82.6329141), b=(40.6889961, -82.6333026),
                 why='the pit-in: the lane leaves the track at the T13 exit on one pavement, then runs beyond the grass island whose black barrier begins at s ~3405 (360 lap t018-t020 left; c20_s3360 / c20_s3400: no barrier before it)'),
            dict(target='pit lane', side='left', a=(40.6895821, -82.6375776), b=(40.6895931, -82.6381108),
                 why='the pit-out: past the pit wall\'s end at the footbridge abutment the lane runs beside the track separated by the painted ladder line, then by the T1 inside kerb (360 t030-t032 left, N837 t014; c20_s0120 / c20_s0160)'),
        ]),
    ),
    # PIT LANE (step 4). The OSM 'Pit Lane' way (444205379) from the pit-in at the T13 exit (s ~3370) along the pit straight,
    # under the footbridge and round the T1 inside to the pit-out after T1 (s ~380), as the hand-off has it; no 2024+ video
    # drives the lane (round 4: none found; the 2026 race broadcast x5Fk-R-e_Zc not surveyed), so the lane is surveyed from
    # the track (the 360 lap's left views t020-t034, N837 t014-t016) and the clean captures (c20_s3400-c20_s0360). Sides as
    # driven down the lane: the pit wall stands on its RIGHT (between the lane and the track)
    pit_lane=dict(
        lane=dict(source='osm', match_track_tone=dict(k=0.8, paint=0.97)),   # round 8 (second judge m14, the pit-out seam): k 0.5 -> 0.8
        walls=[
            dict(side='right', a=(40.6891509, -82.6336089), b=(40.6895232, -82.6377782), h=1.04, material='concrete', declared='pit wall',
                 src='the pit wall (declared_walls \'pit wall\', measured on the captures): 360 lap t020-t030 left (white concrete pit wall from the RESTART board at the T13 exit to the footbridge abutment), pit rows s 3496-216; h 1.04 m (2019 lidar; the 360 t026 left re-read 1.03-1.08 m)'),
        ],
        boxes=None, buildings=[], furniture=[],
    ),
    # STRUCTURES (step 3; kit tools/track/kit/README.md): the stands, the starter tower and the starter's stand at the line
    structures=dict(suppress_osm=['1315208899', '1315208916', '1315208917', '1315208900', '1315208901'], items=[
        # the two pit-garage blocks behind the pit boxes (judge r7 F13: drawn as grey two-storey window boxes from OSM): white
        # walls under a red roof band, single storey (360 t026-t028 left; c20_s0000 / c20_s0080: white roofs with a red band on the
        # track side); lidar eave 5.3-5.4 m (building_height_robust, round 7 build log)
        dict(type='garage', name='Pit garages east', osm='1315208900', eave=4.4, ridge=5.4, wall='#e6e3dc', roof='#e3e1dc', trim='#c0483c', trim_h=0.9,
             doors=dict(side='track', pitch=4.0, w=3.2, h=3.0, color='#cfccc5'),
             src='OSM 1315208900; c20_s0000 / c20_s3560 (white roof, red band); 360 lap t026 left (red roof bands behind the lane)',
             h_src='lidar p60 5.4 m (round 7 build log); single storey in t026'),
        dict(type='garage', name='Pit garages west', osm='1315208901', eave=4.4, ridge=5.3, wall='#e6e3dc', roof='#e3e1dc', trim='#c0483c', trim_h=0.9,
             doors=dict(side='track', pitch=4.0, w=3.2, h=3.0, color='#cfccc5'),
             src='OSM 1315208901; c20_s0080 / c20_s0040 (white roof, red band); 360 lap t028 left',
             h_src='lidar p60 5.3 m (round 7 build log); single storey in t028'),
        # the main grandstand right of the pit straight before the line: a two-tier covered stand under a red roof (360 t024 right,
        # t130 right; N837 t004 / t128): its roof on c20_s3480 / c20_s3520 (OSM 1315208916, 39.8 m along the track); the roof
        # 6.3-6.9 m above the ground (2019 lidar, r5/lidar_heights.json)
        dict(type='grandstand', name='Main grandstand (covered)', front=[(40.6897429, -82.634738), (40.6897711, -82.6352081)],
             base=dict(h=1.0, depth=1.0, color='#8f9296', walk='#a9a69f', rail='#5d6166'),
             rows=dict(n=7, depth=0.85, rise=0.6, z0=1.4, seat='#9a9ea3', riser='#6f7378', back=0.4),
             cover=dict(z0=6.3, z1=6.3, d0=-0.4, d1=7.3, color='#b8443a', fascia='#c4503f', under='#4f5256', post='#3c3f43', posts=8.0,
                        band=dict(z=3.2, h=0.5, color='#c4503f')),
             rear=dict(color='#6b6e72'),
             src='360 lap e25u_vjn1uM t024 / t130 right: the two-tier covered grandstand, red roof edges and a red middle band; N837 t004 / t128; c20_s3480 / c20_s3520: the red roof 40 x ~7 m (OSM 1315208916)',
             h_src='2019 lidar: roof 6.3-6.9 m over the ground (r5/lidar_heights.json); two tiers in the frames'),
        # the second covered stand behind the T1 approach (360 t028 right: a long low covered stand with a red roof far behind
        # the fence; OSM 1315208917 89 m; NAIP ortho red roof); lidar 6.7 m at its front sloping to 4.5 m at the back
        dict(type='grandstand', name='T1 approach covered stand', front=[(40.6899084, -82.63636), (40.690004, -82.6374071)],
             base=dict(h=0.8, depth=1.0, color='#8f9296'),
             rows=dict(n=12, depth=1.0, rise=0.3, z0=1.1, seat='#9a9ea3', riser='#6f7378', back=0.4),
             cover=dict(z0=6.2, z1=4.6, d0=-0.4, d1=14.0, color='#b8443a', fascia='#c4503f', under='#4f5256', post='#3c3f43', posts=9.0),
             src='360 lap t028 right (the red-roofed stand far behind the fence), inventory rows s 72-90 right; NAIP ortho: the red roof 89 x 14 m (OSM 1315208917)',
             h_src='2019 lidar: 6.7 m at the front to 4.5 m at the back (r5/lidar_heights.json)'),
        # the aluminium bleachers on the T4 approach, left (360 t072-t074 left: open aluminium bleachers behind the armco and the
        # catch fence, ~15 rows; c20_s1760 / c20_s1800: the grey seat field; OSM leisure=bleachers 1315208964 / 1315208921);
        # 2019 lidar box 4.8 m over the north one
        dict(type='grandstand', name='T4 bleachers north', front=[(40.6926231, -82.638648), (40.6922059, -82.6388404)],
             base=dict(h=0.6, depth=1.0, color='#c3c7cc'), rows=dict(n=15, depth=0.8, rise=0.33, z0=0.9, seat='#dfe2e6', riser='#b4b8bd', back=0.0),
             aisles=dict(pitch=12.0, w=1.2, color='#b5b8bc'), self_lit=True,   # judge r7 F19: rows face away from the sun (plain Lambert rendered them dark)
             src='360 lap t072-t074 left (aluminium bleachers, inventory rows s 1792-1898 left); c20_s1760 / c20_s1800; OSM 1315208964',
             h_src='2019 lidar box 4.8 m (building_height_robust log); 14 rows of 0.3 m in t072 left'),
        dict(type='grandstand', name='T4 bleachers south', front=[(40.6915309, -82.6392064), (40.6911479, -82.6394012)],
             base=dict(h=0.6, depth=1.0, color='#c3c7cc'), rows=dict(n=15, depth=0.8, rise=0.33, z0=0.9, seat='#dfe2e6', riser='#b4b8bd', back=0.0),
             aisles=dict(pitch=12.0, w=1.2, color='#b5b8bc'), self_lit=True,   # judge r7 F19: rows face away from the sun (plain Lambert rendered them dark)
             src='N837 t060 left (aluminium bleachers on the T4 approach, inventory row s 1792 left); c20_s1720 / c20_s1760; OSM 1315208921',
             h_src='as the north bleachers (same rows in the frames)'),
        # the control tower behind the pit lane at the line (round 8, owner's drive: "Control tower doesn't look like the control
        # tower"; round8.md 1c). Frames: N837 t004 / t128-t129 (Apr 2026), 360 lap t022 ahead / t024 left / h0046 (Jul 2025): a
        # dark brown shaft, two upper storeys of dark glazing wrapped by decks with white fascia, a red hip roof with a mast and
        # flag. Lidar 2019 (r8/tower_lidar): the roof 19 x 18 m (x 48..67, y 0..18 ENU), its eaves 17 m and its top over 20 m
        # (24 m with the mast) above the ground. Massing: a 10 x 10 m shaft to 10.5 m (3 storeys), the upper block 13 x 13 m
        # from 10.5 to 16.8 m (2 storeys) with decks 1.5 m out at both floors, the hip roof 3 m out (19 m eaves) rising 5 m.
        # No logo artwork; the deck fascia boards are left plain (the lettering is not legible in the frames)
        dict(type='block', name='Control tower', rect=dict(c=(40.6890853, -82.6353188), heading_deg=-3.39, l=11.0, w=11.0),
             h=17.0, storeys=5, wall='#c4b29b', band='#2b2e33', roof='#c4b29b', bands=[3, 4], band_frac=[0.1, 0.92],
             wrap_decks=[dict(z=10.2, depth=1.2, color='#ecebe6', rail=1.0), dict(z=13.6, depth=1.2, color='#3a3d42', rail=1.0)],
             hip=dict(rise=4.5, overhang=4.0, color='#c4483c'),
             src='second judge M1 / owner note: N837 t127 / t129 (Apr 2026): a slender square tan-grey shaft (side wall (105, 102, 109) overcast; 360 t024 (131, 128, 123) in sun) the full height, two upper levels of open, dark decks with a white fascia board between, a red hip roof with a lattice mast; lidar 2019: the roof 19 x 18 m over the shaft, eaves 17 m, top over 20 m (24 m with the mast)',
             h_src='lidar 2019: eaves 17 m; 5 storeys of 3.4 m; the hip rising 4.5 m to 21.5 m'),
        # the starter's stand over the pit wall at the line: a cabin on black steel legs with boards (360 t022 / t024: HONDA, 2025;
        # N837 t130: PERMCO, Apr 2026); its red post on the pit wall on c20_s3560 / c20_s0000 at (61.2, 47.8) ENU
        # the scoring pylon right of T5 (inventory rows 'scoring pylon' s 1989-2105 right; 360 t078-t082, N837 t067-t072: a tall
        # slender dark tower with a lit position column); 2019 lidar: 256 returns over a 4 x 4 m square at (7.1, 336.7) ENU,
        # top 30.7 m above the ground (judge r7 F6)
        dict(type='scoring_tower', name='T5 scoring pylon', at=(40.6920247, -82.6359157), heading_deg=0.0, w=3.8, d=3.8, h=30.7,
             color='#3a3c40', plinth=dict(w=4.6, h=0.6, color='#cfcdc6'), head=dict(h=1.2, w=4.0, d=4.0, color='#2a2c2f'),
             src='lidar 2019 isolated column 4 x 4 m, 30.7 m (r7 judge F6); 360 lap t078-t082 ahead / right, N837 t067-t072; c20_s2080 its shadow',
             h_src='lidar 2019 top 30.7 m above the class-2 ground'),
        dict(type='scoring_tower', name='S/F starter stand', at=(40.6894294, -82.635275), heading_deg=-3.39, w=1.2, d=1.2, h=6.0, color='#202224',
             head=dict(h=2.6, w=6.0, d=3.0, color='#2a5aa8'),
             src='N837 OJaBJz18xEo t130 (Apr 2026): the PERMCO-boarded stand on black legs over the pit wall at the line; 360 t022 ahead / t024 left (2025, HONDA boards); c20_s3560 / c20_s0000: its post on the pit wall',
             h_src='legs ~6 m and a ~2.6 m cabin against the 13 m starter tower beside it in t130 / t024'),
    ]),
    app=dict(short='Mid-Ohio', pace='cars/field/mid_ohio/pace.json'),
)
