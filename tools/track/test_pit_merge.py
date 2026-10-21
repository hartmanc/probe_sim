"""Stage 1 reads no stage-3 key (20 Oct 2026): the pit merge's inputs come from centre.pit_exit and stage-1 evidence,
never from the scenery builder's barriers() / pit_exit_cones(), so config_id('geometry') covers everything stage 1 reads.

python3 -I -m pytest -q tools/track/test_pit_merge.py   (the source checks need nothing beyond the standard library; the
data checks need numpy, scipy and pillow, the track caches and the published packages, and are skipped without them)
"""
import ast
import copy
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)


def _functions(path):
    tree = ast.parse(open(path).read())
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _calls(fn):
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                out.add(f'{f.value.id}.{f.attr}')
            elif isinstance(f, ast.Name):
                out.add(f.id)
    return out


def _names(fn):
    return {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}


STAGE3_READERS = {'BS.barriers', 'BS.pit_exit_cones', 'BS.configure', 'BS.main', 'BS.declared_cone_lines', 'BS.closed_roads'}


def test_stage_geometry_calls_no_scenery_reader():
    fns = _functions(os.path.join(HERE, 'build_track.py'))
    for name in ('stage_geometry', 'fitted_method', 'pit_merge_inputs'):
        bad = _calls(fns[name]) & STAGE3_READERS
        assert not bad, f'{name} calls stage-3 readers {sorted(bad)}'
    assert 'BS.configure_geometry' in _calls(fns['stage_geometry'])
    assert 'pit_merge_inputs' in _calls(fns['stage_geometry'])


def test_stage1_scenery_functions_read_no_stage3_config():
    fns = _functions(os.path.join(HERE, 'build_scenery.py'))
    for name in ('pit_lane', 'lane_parts', 'pit_exit_line', '_one_part_stretch', '_one_part_line',
                 '_two_part_stretch', '_two_part_line', 'pit_wall_line', '_pit_wall_rule', 'bridge_stations'):
        bad = _names(fns[name]) & {'SC_CFG', 'PIT_CFG', 'PIT_EXIT', 'STRUCT_CFG', 'PITWALL_EDGE', 'TYRE_CORNERS', 'barriers'}
        assert not bad, f'build_scenery.{name} reads {sorted(bad)}'
    # configure_geometry leaves every stage-3 section empty
    cg = fns['configure_geometry']
    src = '\n'.join(ast.unparse(st) for st in cg.body[1:])          # without the docstring
    assert 'SC_CFG, PIT_CFG, STRUCT_CFG, PIT_EXIT = ({}, {}, None, {})' in src
    assert "'scenery'" not in src and "'pit_lane'" not in src and "'structures'" not in src
    # the stage-1 entry points call only stage-1 helpers
    allowed = {'_one_part_stretch', '_one_part_line', '_two_part_stretch', '_two_part_line', '_pit_wall_rule'}
    for name in ('pit_exit_line', 'pit_wall_line'):
        helpers = {c for c in _calls(fns[name]) if c.startswith('_')}
        assert helpers <= allowed, f'{name} calls {sorted(helpers - allowed)}'


def test_geometry_hash_covers_the_pit_exit_key():
    for m in ('numpy', 'scipy', 'PIL'):
        pytest.importorskip(m)
    import trackcfg
    from build_track import config_id
    cfg = trackcfg.load('sonoma')
    base = config_id(cfg)
    c2 = copy.deepcopy(cfg)
    del c2['scenery'], c2['pit_lane']
    assert config_id(c2) == base                       # stage-3 sections are outside the hash ...
    c3 = copy.deepcopy(cfg)
    c3['centre']['pit_exit'] = dict(c3['centre']['pit_exit'], wall_end_latlon=(38.1620, -122.4560))
    assert config_id(c3) != base                       # ... the pit merge's key is inside it


def _data_or_skip(track):
    for m in ('numpy', 'scipy', 'PIL', 'requests'):
        pytest.importorskip(m)
    import trackcfg
    cfg = trackcfg.load(track)
    pkg = os.path.join(ROOT, 'public', 'tracks', track)
    osm = os.path.join(cfg.cache, cfg['osm_file'])
    if not (os.path.exists(os.path.join(pkg, 'track.json')) and os.path.exists(osm)):
        pytest.skip(f'{track}: no published package or OSM cache here')
    return cfg, pkg


def _inputs(cfg, pkg, configure):
    import numpy as np
    import build_scenery as BS
    import build_track as BT
    import geo as B
    B.configure(cfg)
    configure(cfg, pkg)
    T = json.load(open(os.path.join(pkg, 'track.json')))
    hf = np.fromfile(os.path.join(pkg, 'heightfield.bin'), np.float32).reshape(T['heightfield']['ny'], T['heightfield']['nx'])
    trk = BS.Track(T, hf)
    osm = BS.Osm()
    BT.REPRO = dict(cfg.get('reproduce') or {}) if cfg.logger else {}
    pit, line = BT.pit_merge_inputs(cfg, trk, osm)
    pw = BS.pit_wall_line(trk, osm)
    return pit, line, pw


@pytest.mark.parametrize('track', ['sonoma', 'laguna_seca'])
def test_merge_inputs_do_not_depend_on_scenery_or_pit_lane(track):
    cfg, pkg = _data_or_skip(track)
    import numpy as np
    import build_scenery as BS
    if cfg['centre'].get('pit_exit') is None and not (cfg.get('reproduce') or {}).get('pit_exit_wall_end_latlon'):
        pytest.skip(f'{track}: no pit_exit key')
    # with the full stage-3 configuration loaded into the scenery builder ...
    full = _inputs(cfg, pkg, BS.configure)
    # ... and with the scenery and pit_lane sections deleted from the config
    bare_cfg = copy.deepcopy(cfg)
    del bare_cfg['scenery'], bare_cfg['pit_lane']
    bare = _inputs(bare_cfg, pkg, BS.configure_geometry)
    (pit_a, line_a, pw_a), (pit_b, line_b, pw_b) = full, bare
    assert line_a is not None and line_b is not None
    assert (line_a['s0'], line_a['s1']) == (line_b['s0'], line_b['s1'])
    assert np.array_equal(np.array(line_a['pts']), np.array(line_b['pts']))
    assert json.dumps(pit_a, sort_keys=True) == json.dumps(pit_b, sort_keys=True)
    assert (pw_a is None and pw_b is None) or np.array_equal(pw_a, pw_b)


def test_measured_line_is_used_as_given():
    cfg, pkg = _data_or_skip('sonoma')
    import numpy as np
    import build_scenery as BS
    ll = cfg['scenery']['pit_exit_cones']['latlon']        # Sonoma's round-7e measured blend line, as a test input
    c2 = copy.deepcopy(cfg)
    c2['centre']['pit_exit'] = dict(line_latlon=ll, src='test')
    del c2['scenery'], c2['pit_lane']
    _, line, _ = _inputs(c2, pkg, BS.configure_geometry)
    assert len(line['pts']) == len(ll)
    import geo as B
    x, y = B.enu(np.array(ll)[:, 0], np.array(ll)[:, 1])
    assert np.abs(np.array(line['pts'])[:, :2] - np.c_[x, y]).max() <= 0.005 + 1e-9
