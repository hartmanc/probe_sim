"""Mid-Ohio, Lemons 13-turn outer loop; stage-1 candidate, not accepted.

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
    loop_check=dict(n_min=3500, n_max=3750, official_m=3633.934, elev_min=0, elev_max=100),
    captures=dict(clean_dir='compare/mid_ohio/satellite_clean', clean_index='tiles.json',
                  mpp=0.1132013752, common_shift=None, clean_mask='clean'),
    sources=dict(
        onboard=[], pit_lane_video=[], streetview='compare/mid_ohio/streetview.md',
        lemons_layout='https://registration.24hoursoflemons.com/userfiles/races/24HoL__TrackMap_Mid-Ohio.png'),
    stations_ref=(3595, 3589.22),
    centre=dict(pit_merge=False, pit_exit=dict(
        src='c20_s0200..c20_s0320 and 2026 N837 onboard t14/t16: hatched blend then raised red/white T1 kerb separates pit lane from course; automatic OSM lane-merge extent includes the inactive inside apron')),
    spline=dict(report_width=(12.192, 12.192),
                kerb_search=[('left', 285, 360, (-6, 1), 'c20_s0200..c20_s0320: inside kerb lies about 2–3m inside automatic apron boundary')],
                mask=[('left', 210, 255, 'c20_s0160/c20_s0200: overhead bridge occludes the painted boundary')]),
    prior=dict(bridge_win=35),
    features=[
        ('left', 285, 360, 'kerb', 'c20_s0200..c20_s0320; N837 onboard t16: raised red/white T1 inside kerb separates pit exit, use its outer band, not grass beyond apron'),
        ('right', 365, 480, 'kerb_yellow', 'c20_s0280..c20_s0440; continuous yellow T1 exit kerb, outer painted limit'),
        ('left', 1010, 1120, 'kerb_yellow', 'c20_s0960..c20_s1080; continuous yellow T2 exit kerb, outer painted limit'),
    ],
    shapes=[], straights=[], repave_fixes=[],
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
