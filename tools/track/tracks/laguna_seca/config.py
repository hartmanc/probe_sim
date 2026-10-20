"""WeatherTech Raceway Laguna Seca: every per-circuit constant of the track pipeline (tools/track/build_track.py).

This is the worked example of a track config (format: tools/track/trackcfg.py, which documents each key and its
default). It is plain data: nothing here runs, the pipeline reads CONFIG. Values that were measured by hand on the
imagery or the footage say where they came from; values that were a script constant before 19 Oct 2026 name the
script. Paths are relative to tools/track/ unless absolute.
"""

CONFIG = dict(
    id='laguna_seca',
    name='WeatherTech Raceway Laguna Seca',
    direction='ccw',
    # ---------------------------------------------------------------- frame and sources (Stage 0)
    origin=(36.5843, -121.7535),                        # lat0, lon0 of the local ENU frame (CONTRACTS section 1)
    osm_bbox=(-121.775, 36.572, -121.735, 36.598),      # W, S, E, N of the OSM API map call
    cache_dir='cache',                                  # Laguna's downloads predate per-track cache folders
    osm_file='laguna_osm.xml',
    # The Lemons layout (24hoursoflemons.com schedule page, Laguna Seca: the full 11-turn circuit) is the whole
    # highway=raceway loop. These 8 ways, stitched by shared end nodes in this order, form it; "Pit Lane" (109859349)
    # is the pit lane, not part of the loop.
    loop_ways=['10464852', '1315957502', '1315957503', '1315957504', '1315957505', '1315957506', '1315957507',
               '1315957508'],
    pit_lane_way='Pit Lane',                            # OSM name of the pit-lane way (scenery: pit lane, pit wall)
    dem_tiles=[
        'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_AZ_FEMA_R9_Lidar_2017_D18/TIFF/'
        f'USGS_1M_10_{t}_CA_AZ_FEMA_R9_Lidar_2017_D18.tif' for t in ('x61y405', 'x61y406')],
    lidar_ept='https://s3-us-west-2.amazonaws.com/usgs-lidar-public/CA_FEMA_Z4_B1_2018/',   # same 2017 survey as the DEM
    lidar_survey='CA_AZ_FEMA_R9_Lidar_2017_D18',
    dem13='https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n37w122/USGS_13_n37w122.tif',
    # ---------------------------------------------------------------- logger laps (optional)
    logger_dir='/Users/cobyhartman/projects/starlink-go-pro/laps',   # read only; None = the no-logger path
    logger_drivers=['driver C', 'driver B', 'Coby', 'driver D', 'driver A'],     # race order (ghost colours)
    logger_sections=[0, 640, 920, 1340, 1760, 2200, 2820, 3100, None],  # defs.J of the logger analysis (None = lap end)
    logger_bad_gps_files=['0e98'],
    # Start/finish when there is no logger: the transponder line. Laguna's value is centreline.npy[0] (the logger's
    # lap line), 3.6 m from the painted line on the captures; for a new circuit, read it off the clean captures.
    start_finish_latlon=(36.586549, -121.756616),
    # ---------------------------------------------------------------- corners: (turn, name, dir, logger s, lat, lon)
    # logger s = traces2.ANCH / corners.CORN of the logger analysis (frame length 3558); lat/lon = the same anchor
    # (centreline.npy at that s), used when there is no logger. The corner is the curvature peak within +-45 m.
    corners=[
        ('T1', None, 'left', 240, 36.584592, -121.757715),
        ('T2', 'Andretti Hairpin', 'left', 520, 36.582589, -121.757066),
        ('T3', None, 'right', 790, 36.584861, -121.756753),
        ('T4', None, 'right', 1060, 36.584324, -121.753936),
        ('T5', None, 'left', 1530, 36.580226, -121.754285),
        ('T6', None, 'left', 1940, 36.580408, -121.749957),
        ('T7', None, 'right', 2360, 36.584025, -121.749183),
        ('T8', 'The Corkscrew (T8)', 'left', 2440, 36.584729, -121.749034),
        ('T8A', 'The Corkscrew (T8A)', 'right', 2490, 36.585037, -121.749423),
        ('T9', 'Rainey Curve', 'left', 2690, 36.586706, -121.749897),
        ('T10', None, 'right', 2950, 36.586493, -121.752633),
        ('T11', None, 'left', 3240, 36.588565, -121.754395),
    ],
    named_straights=[('Rahal Straight', 'T6', 'T7')],   # placed halfway between the two corners
    radius_check_skip=['T1', 'T7'],                     # flat-out kinks: no radius check against the driven line
    # Every station number below is a station of this config's geometry: n = 3560, length 3588.048 m (the accepted
    # package). A build with another station count (no logger: 3600) maps them by the fraction of the lap.
    stations_ref=(3560, 3588.048),
    # ---------------------------------------------------------------- stage 1: geometry
    loop_check=dict(n_min=3480, n_max=3680, official_m=3602, elev_min=45, elev_max=65),
    centre=dict(
        # v2: the logger's driven line moved toward the NAIP midpoint (build_laguna_v2.py FIT_A / FIT_B)
        naip_fit_a=1e6, naip_fit_b=1e3,
        # painted midpoint refit (rebuild_from_paint.py defaults; the 18 Oct run used these, the skill said 1e3)
        paint_fit_a=1e4, paint_fit_b=1e2, gps_margin=1.0, min_width=10.0,
        bridge_win=25,
        # shadows masked like the OSM bridges' when bridge_win > 0 (first-centre stations): the Rahal advertising
        # gantry (compare round 3)
        extra_shadow_stations=[2228],
    ),
    # Captures used to measure the painted midpoint for the centre refit (measure_paint.py, 18 Oct 2026): the 42 masked
    # z20 Maps screenshots, each registered against the ortho on its own. New circuits use the clean captures here.
    centre_captures='z20',
    centre_registration='per_capture',
    repave_fixes=[(1895, 2000, 1905, 1965, 'T6 sag (2017 lidar) -> crest (2023 repave)')],
    # Four artefacts of how the accepted package was built on 17-18 Oct 2026, applied only on the logger path (and not
    # with --no-reproduce) so that a rebuild reproduces it; they are not method, and new circuits leave this block out:
    reproduce=dict(
        # the pit-exit line's start (the refit keeps the old left edge from 40 stations before it): the accepted build took
        # the wall end from the stage-3 pit-wall RULE, the end of its fenced part 120 m past the line (scenery.pit_wall
        # fence_until_m), at first-centre station 120; this is that rule point, not a measurement (20 Oct 2026: stage 1
        # reads no scenery key; a measured wall end belongs in centre.pit_exit.wall_end_latlon)
        pit_exit_wall_end_latlon=(36.585547670, -121.757121091),
        centre_bridge_win=0,          # the centre was refitted (18 Oct, 10:08) before the bridge-shadow mask existed
        gps_margin_line='stale_refit_index',  # the paint step's GPS margin read a logged line measured on the refitted
                                      # centre (a stale ghost_line_debug.npz), index for index, as if on the first centre
        heightfield_centre='first',   # heightfield.bin is the first build's (17 Oct), never rebuilt after the refit
    ),
    # ---------------------------------------------------------------- captures (Google z20, reference only)
    captures=dict(
        z20_dir='compare/satellite', z20_index='z20_tiles.json', z20_mask='google_ui_2026_10_18',
        clean_dir='compare/satellite_clean', clean_index='tiles.json',
        mpp=0.11992,
        common_shift=(-0.3, 0.0),     # Google minus ortho, m: median of the 41 z20 registrations (paint_regs.json)
        clean_mask='clean_2026_10_18',  # also masks the mouse cursor of c20_a1..a3 (captures.py)
        exclude=['z20_s3400'],        # registration 1.3 m off its neighbours: never used for the per-capture apron widths
    ),
    # ---------------------------------------------------------------- edge spline fit (fit_edges_spline.py)
    spline=dict(
        # (lo, hi[, clean-capture name prefixes]): the T2 run (18 Oct, 20:04) had the z20 captures and the first clean
        # ones (c20_a1..a8, c20_s0450); the rest of the lap (20:37) all 51
        runs=[(240, 700, ['c20_a', 'c20_s']), (700, 3800)], knot=6, lam=30.0, huber=0.25, line_off=0.26, prior=0.03,
                init_stiff=30.0, captures='z20,clean'),
    # (side, first station, last station, feature, why). Stations are those of this config's geometry (n = 3560).
    features=[
        ('left', 2425, 2535, 'keep', 'Corkscrew: the S is too tight for the 6-station spline; the edge from the paint step is kept'),
        ('right', 2425, 2535, 'keep', 'Corkscrew, as the left side'),
        ('right', 3228, 3425, 'keep', 'T11 outside and exit: the fit cut inside the outer line and read the exit kerb by its inner side'),
        ('left', 3330, 3633, 'keep', 'front straight left: set by the declared straight below; the fit reached the wall base'),
        ('left', 3633, 3800, 'keep', 'pit-out merge to T1 (stations 73-240): the left edge includes the pit-out lane'),
        ('left', 478, 528, 'asphalt_end',
         "Andretti apex between the two apex kerbs: a pale painted band ~1.2 m wide with a thin white line on its outer "
         "side; the edge is the band's inner side (c20_a7/a8 profiles, station 500)"),
    ],
    # The spline's prior (its weak fallback and the centre of its search window) is the paint-step edge, except:
    prior=dict(
        bridge_win=35,                 # bridge shadows interpolated across +-35 stations (was fix_bridge_edges.py)
        bridge_skip=[37],              # the S/F footbridge (first-centre station): the pit-lane gaps hang off the edge there
        first_edge=[('left', 2060, 2236, 'Rahal straight left: the first-centre NAIP edge sat on the white line; the paint '
                     'step read the T6-exit / Rahal apron (was fix_rahal_left.py --ref main; after 2236 it used the paint sweep\'s T7-approach '
                     'kerb, which stays the paint-step prior here)')],
        interp=[('left', 3320, 3380, 'T11 exit to the front straight: the paint step read the pit-entry nose (a 2.6 m step); '
                 'the edge runs from the T11 exit to the declared straight (was fix_front_straight_left.py --clamp)')],
    ),
    # Measured shapes (fix_edge_shape.py): station:half-width knots, monotone cubic, blended over `blend` stations.
    shapes=[
        dict(side='left', knots=[(3280, 5.64), (3295, 5.44), (3310, 4.66), (3325, 4.64), (3340, 5.70), (3355, 5.73),
                                 (3370, 5.71), (3385, 6.48)], blend=2, fitted_only=True,
             why='T11 exit left to the pit entry: the dashed pit-entry blend line (z20_s3315/s3400, the accepted '
                 'package\'s edge, measured 18 Oct 2026); without logger laps the pit-entry lane beyond it shared the '
                 'paint step\'s reading. Fitted method only (the logger reproduction keeps its own steps here)'),
        dict(side='right', knots=[(3283, 4.2), (3310, 5.4), (3340, 7.0), (3360, 7.3), (3420, 7.9)], blend=2,
             why='T11 exit: kerb outer limit from the apex to 3360 (red/white on z20_s3315/s3400), white line beyond, '
                 'widening once to the straight at 4.0 m from the wall'),
    ],
    # Declared straights (fix_front_straight_lines.py as run on 18-19 Oct night: joins 3335,3350 / 3355,3395, ends
    # 40 / 15, blend 20): the painted line is straight; RANSAC line fit, joined in.
    straights=[
        dict(side='right', fit='paint', lo=3385, hi=30, join=(3335, 3350), end=40, blend=20, tol=0.15,
             why='front straight right: one painted line from the T11 green strip to T1'),
        dict(side='left', fit='pitwall', gap=1.98, lo=3390, hi=30, join=(3355, 3395), end=15, blend=20,
             why='front straight left: 1.98 m inside the straight pit wall (the median gap where the edge was straight, '
                 'stations 3460-10; fix_front_straight_left.py measured 2.01 m on z20_s3485)'),
    ],
    gate=dict(straight_rms=0.10, step=0.10, profile_step=0.10, spline_obs_within=0.85,
              exempt=[('left', 280, 330, 'pit-out lane splits off the track after T1 (junction, real)')],
              wall_gaps=[('left', 'pitwall', 3420, 40), ('right', 'concrete', 3420, 40)]),
    # ---------------------------------------------------------------- stage 2: ghosts and racing line
    ghosts=dict(margin=1.0, kerb_margin=1.0, nudge=0.3, jerk_w=3,
                implied_g_turns=['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T8A', 'T9', 'T10', 'T11'],
                implied_g_exempt=['T7'],              # a flat-out kink
                kappa_drivers=['driver A', 'Coby', 'driver D']),
    # ---------------------------------------------------------------- stage 3: scenery (build_scenery.py constants)
    scenery=dict(
        # the committed Laguna package predates the trees' imagery check (build_scenery.canopy_check); it stays off here so
        # the logger build reproduces that package; a build with it on reports what it would remove
        tree_imagery_check=False,
        tyre_corners=[('T2', 48, 62), ('T5', 44, 56), ('T8', 39, 21), ('T8A', 15, 55), ('T9', 45, 65), ('T11', 45, 50)],
        paved_runoff=[('T6', 15, 80), ('T9', 30, 75), ('T10', 20, 75)],
        brake_board_corners=['T2', 'T5', 'T8', 'T11'],
        no_exit_kerb=['T8'],                       # the Corkscrew's T8 exit is T8A's entry
        # the pit wall stands 0.6 m off the NAIP asphalt edge of the first build (asphalt runs to the wall there); the
        # painted edge is ~2 m inside it on the front straight
        pit_wall=dict(fence_until_m=120, end_after_line_m=260, at='first_edge'),
        oak=dict(corner='T8', side='left', text='Corkscrew oak'),
        gantry=dict(corner='T7', before_m=150),
        banner_boards=[('T1', -70, -1, 'PORSCHE', 10.0, 14.0), ('T6', 10, -1, 'PORSCHE', 8.0, None),
                       ('T7', 10, -1, 'WEATHERTECH', 10.0, None),
                       ('T11', -80, -1, 'MOTUL', 6.0, None), ('T11', -72, -1, 'LAGUNA SECA', 6.0, None),
                       ('T11', -64, -1, 'MICHELIN', 6.0, None), ('T11', -56, -1, 'TIRE RACK', 6.0, None)],
        bridge_banners={'60116334': [['MISSION', 'WEATHERTECH', 'MISSION', 'PORSCHE'], ['WEATHERTECH', 'LAGUNA SECA']],
                        '60116327': [['TIRE RACK'], ['TIRE RACK']],
                        '459576002': [['WEATHERTECH', 'AUTO. HOME. PET. FIND YOUR FIT.'], ['WEATHERTECH']]},
        bridge_default_banner='LAGUNA SECA',
        bridge_style={'60116327': 'arch'},
        hangars={'639859964': 'kinetic'},
        # post steps, in order (each was a fix_*.py / add_*.py script on 18 Oct 2026)
        shoulder_zones=[dict(side='right', lo=3330, hi=45, wall='concrete', turn='Front straight',
                             note='paved shoulder to the right-hand wall, T11 exit to past the S/F bridge (owner, Mustang onboard, 18 Oct 2026)')],
        aprons=[('T2 entry apron', 'right', 372, 452, 'braking apron right of the white line before the Andretti hairpin (z20_s0425, onboard T2_Andretti)'),
                ('T9 teal apron', 'left', 2668, 2752, 'teal-painted paved apron outside the white line on the T9 (Rainey) entry (clean captures c20_b2650/b2725)'),
                ('Rahal apron', 'left', 2026, 2330, 'pale paved apron left of the painted line from the T6 exit along the Rahal straight (z20_s2125/s2210, onboard Rahal_straight)')],
        # the 18 Oct apron widths were measured on the z20 captures with per-capture registrations (z20_s3400 left out)
        apron_captures='z20', apron_registration='per_capture',
        apron_max=10.0,
        pitwall_end=dict(lo=70, hi=180, why='hot-pit wall ends where the pit-out lane begins; painted strip only to T1'),
        pitwall_setback=dict(lo=3285, hi=3425, min=2.0, why='T11 exit pit-wall nose: OSM polyline cut across the paint'),
        pitwall_straight=dict(lo=3370, hi=30, fit_lo=3390, fit_hi=3589, tol=0.25, why='front-straight pit wall is straight (c20_b3400/b3475)'),
        edge_line_runs=[dict(side=-1, s0=250, s1=544, why='T2 approach right: continuous white line on c20_a1..a8')],
        kerb_extents=[dict(side=-1, kind='exit', near=3300, s0=3299.5, s1=3386.5, why='T11 exit kerb on the z20 captures')],
        pit_exit_cones=dict(s0=73.0, spacing=16.0),
    ),
    # ---------------------------------------------------------------- app registry (src/scoreboard/config.ts)
    app=dict(short='Laguna Seca', pace='cars/field/pace.json'),
)
