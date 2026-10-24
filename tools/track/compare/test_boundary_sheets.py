"""boundary_sheets.poses: every pose name unique (round 11: the paddock-lane, pale-strip and crossover parts shared their
labels and 214 round-10 stills were overwritten)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boundary_sheets as BS  # noqa: E402


def _part(y0, turn):
    return dict(turn=turn, kind='closed_road', center=[[0, y0, 0], [60, y0, 0]], left=[[0, y0 + 3, 0], [60, y0 + 3, 0]],
                right=[[0, y0 - 3, 0], [60, y0 - 3, 0]])


def test_parts_of_one_road_get_unique_names(tmp_path):
    pkg = tmp_path / 'pkg'; pkg.mkdir()
    C = [[float(x), 0.0, 0.0] for x in range(0, 200, 2)] + [[float(x), 40.0, 0.0] for x in range(198, -1, -2)]
    T = dict(center=C, left=[[x, y + 5, z] for x, y, z in C], right=[[x, y - 5, z] for x, y, z in C])
    S = dict(paved_areas=[], paved_zones=dict(parts=[_part(-20, 'paddock lanes'), _part(-40, 'paddock lanes'), _part(-60, 'Atlantic')]),
             pit_lane=dict(parts=[_part(80, 'pit'), _part(100, 'pit')]))
    json.dump(T, open(pkg / 'track.json', 'w')); json.dump(S, open(pkg / 'scenery.json', 'w'))
    out = tmp_path / 'out'
    BS.poses(str(pkg), str(out), 25)
    P = json.load(open(out / 'poses.json'))
    names = [p['name'] for p in P]
    assert len(names) == len(set(names))
    assert any(n.startswith('zone_paddock-lanes-left-p00_') for n in names)
    assert any(n.startswith('zone_paddock-lanes-left-p01_') for n in names)
    assert any(n.startswith('zone_Atlantic-left_') for n in names)       # a single part keeps its plain label
    assert any(n.startswith('pit_pit-right-p01_') for n in names)
