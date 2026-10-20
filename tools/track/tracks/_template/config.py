"""TEMPLATE for a new circuit (codify round, 20 Oct 2026): copy to tools/track/tracks/<id>/config.py, then fill it by
following .claude/skills/build-track/SKILL.md in its order. Only the layout and source keys are filled at the start. Every
geometry and scenery key starts empty, and its comment names the skill step that fills it FROM EVIDENCE (a clean z20
capture, an onboard time, a Street View panorama, OSM, the lidar). Nothing is copied from another circuit; Laguna's rules
(radius kerbs, brake boards, turn boards, flag stand, rule pit wall) are off. Format and defaults: tools/track/trackcfg.py.
Plain data; nothing here runs. Paths are relative to tools/track/.

The re-derivation test (tools/track/compare/REDERIVE.md) uses this file with Sonoma's layout and source keys filled in.
"""

CONFIG = dict(
    id='<id>',                                   # = public/tracks/<id>/ and tools/track/compare/<id>/
    name='<Circuit name>',
    direction='cw',                              # 'cw' | 'ccw' from above, as the Lemons layout is driven
    # ---------------------------------------------------------------- stage 0: frame and sources (SKILL 0.1, 0.2)
    origin=(0.0, 0.0),                           # lat0, lon0 of the local ENU frame (circuit centre; CONTRACTS section 1)
    osm_bbox=(0.0, 0.0, 0.0, 0.0),               # W, S, E, N of the OSM API map call (SKILL 0.2)
    osm_file='osm/osm.xml',                      # cached under cache/<id>/
    loop_ways=[],                                # the OSM highway=raceway ways of the LEMONS loop in driving order (SKILL 0.1)
    pit_lane_way='Pit Lane',                     # OSM name of the pit-lane way
    dem_tiles=[],                                # USGS 3DEP 1 m DEM tiles (SKILL 0.2)
    lidar_ept='',                                # Entwine point tiles of the same survey (usgs-lidar-public)
    lidar_survey='',                             # survey name; check its dates against the repave history (SKILL 0.2)
    dem13='',                                    # 1/3 arc-second tile (far terrain)
    logger_dir=None,                             # the team's logger analysis, or None (the no-logger path)
    start_finish_latlon=None,                    # the painted timing line on the clean captures (needed without logger)
    corners=[],                                  # (turn, name, dir, logger s | None, lat, lon[, window_m]) per corner (SKILL 0.1)
    named_straights=[],
    loop_check=dict(n_min=500, n_max=10000, official_m=None, elev_min=0, elev_max=500),
    captures=dict(                               # clean z20 captures (SKILL 0.3): register_clean.py, one common shift
        z20_dir=None,
        clean_dir='compare/<id>/satellite_clean', clean_index='tiles.json',
        mpp=0.0,                                 # metres per pixel at z20 at this latitude (measured on overlapping pairs)
        common_shift=None,                       # measured by register_clean.py -> satellite_clean/shift.json
        clean_mask='clean',
        exclude=[],                              # captures off by more than 0.5 m from both neighbours (SKILL 1.2)
    ),
    # recent video and survey sources (SKILL 0.4, 0.5): recorded here and in compare/<id>/inventory/source.json
    sources=dict(
        onboard=[],                              # recent (2024+) onboard of the Lemons layout: video ids with date and camera
        pit_lane_video=[],                       # recent video that drives the pit lane end to end (pit in, boxes, pit out)
        streetview='compare/<id>/streetview.md', # Street View / photo-sphere survey record (panorama ids, dates, headings)
        lemons_layout='',                        # the layout picture on the event's Lemons schedule page
    ),
    # ---------------------------------------------------------------- stage 1: geometry (SKILL stage 1)
    stations_ref=None,                           # (n, length_m) of the build the station numbers below refer to (SKILL 1.3)
    centre=dict(),                               # fit weights, bridge windows, pit merges (SKILL 1.3)
    spline=dict(),                               # the edge fit (SKILL 1.4); defaults in trackcfg.py
    features=[],                                 # (side, lo, hi, 'keep' | 'asphalt_end' | 'kerb', why) where the paint is ambiguous (SKILL 1.4)
    prior=dict(),                                # bridge windows, first_edge, interp (SKILL 1.4)
    shapes=[],                                   # measured half-width knots (SKILL 1.4)
    straights=[],                                # declared straights: a RANSAC paint line or parallel to a wall (SKILL 1.4)
    repave_fixes=[],                             # only where recent footage contradicts the survey (SKILL 1.6)
    gate=dict(),                                 # edge-gate thresholds and exemptions with the capture that shows the junction (SKILL 1.9)
    # ---------------------------------------------------------------- stage 2 (SKILL stage 2)
    ghosts=dict(),
    # ---------------------------------------------------------------- stage 3: scenery FROM EVIDENCE ONLY (SKILL stage 3)
    # No object without a cited `src`; every entry below is filled from the inventory, the captures and the footage, and
    # recorded in compare/<id>/manifest.md. The coverage gate fails on any inventory row with no object and no
    # disposition.
    scenery=dict(
        brake_board_corners=[],                  # boards only where the onboard shows them (SKILL 3.9)
        corner_boards=False,                     # turn boards only where the onboard shows them (SKILL 3.9)
        flagstand=False,                         # only where the onboard shows one (SKILL 3.9)
        pit_wall=dict(rule=False),               # pit-side walls are declared, never ruled (SKILL 3.5)
        kerb=dict(),                             # width, stripe_m, colours, palettes, profile {height, face, back} (SKILL 3.3)
        kerbs_declared=[],                       # every strip from kerb_detect.py on the captures + the onboard (SKILL 3.3)
        kerb_lines=[],                           # raised kerb lines on island kerb paint (SKILL 3.3)
        declared_walls=[],                       # walls, tyre walls, fences, cushions, movable barriers: measured lines,
                                                 # heights with h_src, colours, stack (SKILL 3.4)
        osm_barrier_overrides={},                # re-kind or drop an OSM wall on evidence (SKILL 3.4)
        tyre_facings=None,                       # dict(reach, off) where tyres face walls (SKILL 3.4)
        impact_barriers=[],                      # blocks at wall noses (SKILL 3.4)
        tyre_stacks=[],                          # free-standing stacks (SKILL 3.8)
        blocks=[],                               # free-standing concrete blocks (SKILL 3.8)
        marshal_posts=[],                        # corner stations confirmed on footage (SKILL 3.8)
        light_masts=[],                          # masts with base + shadow on a capture (SKILL 3.8; or structures type 'mast')
        cone_lines_declared=[],                  # cones on measured painted lines, colour / size / spacing from footage (SKILL 3.5, 3.8)
        pit_exit_cones=None,                     # on the measured blend line (SKILL 3.5)
        paint_lines_declared=[],                 # merge / blend lines measured on the captures (SKILL 3.5, 3.11)
        edge_line_cut=[],                        # where the edge paint is not the white line (SKILL 3.11)
        wall_boards=[],                          # boards with typed names per run, start / end from footage (SKILL 3.9)
        bridge_banners={},                       # 'NAME|#bg|#fg' per bridge face (SKILL 3.9, 3.10)
        ground_signs=[],                         # painted ground logos as typed text, from a full-lap capture scan (SKILL 3.9)
        bridge_stairs=False,                     # abutments and stairs to the ground (SKILL 3.10)
        closed_roads=[],                         # unused paved roads as track surface, painted edges, cones from footage (SKILL 3.6)
        closed_roads_clip_walls=False,
        paved_areas=[],                          # paved ground the ortho fills with vehicles (SKILL 3.6)
        pit_lane_clip_walls=False,               # the lane polygon stops at its walls (SKILL 3.5)
        terraces=[],                             # hillside stands from terrace_measure.py footprints (SKILL 3.7)
        grandstand_on_terrain=False,             # (SKILL 3.7)
        building_height_robust=True,             # p60 lidar heights (SKILL 3.7)
        building_overrides=[],                   # newer evidence over the lidar, logged (SKILL 3.7)
        building_evidence=[],                    # the 2026 source of each building, or its drop (SKILL 3.7)
        season_tint=None,                        # the footage's season on the published ortho (SKILL 3.2)
        gates=dict(allowed=[], paddock=[]),      # allowed runoff with the evidence that shows it open (SKILL 3.12)
    ),
    # ---------------------------------------------------------------- pit lane, first-class (SKILL 3.5)
    pit_lane=dict(lane=dict(source='osm'), walls=[], boxes=None, buildings=[], furniture=[]),
    # ---------------------------------------------------------------- structures kit (SKILL 3.7; tools/track/kit/README.md)
    structures=dict(suppress_osm=[], items=[]),
    # ---------------------------------------------------------------- app (SKILL stage 6)
    app=dict(short='<Short>', pace='cars/field/<id>/pace.json'),
)
