"""Unit tests of the inventory tools: python3 -I -m unittest discover -s tools/track/inventory -p 'test_*.py'"""
import datetime as dt
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heights  # noqa: E402
import inventory  # noqa: E402


def ring(n=400, r=60.0):
    C = [[r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), 0.0] for k in range(n)]
    return {'center': C, 'spacing_m': 2 * math.pi * r / n, 'n': n, 'corners': [{'turn': 'T1', 's': 100.0}]}


class TimeMapTest(unittest.TestCase):
    A = [{'name': 'S/F', 't': 2.0, 's': 0.0}, {'name': 'X', 't': 12.0, 's': 300.0}, {'name': 'end', 't': 22.0, 's': 400.0}]

    def test_linear_hits_anchors_and_folds(self):
        tm = inventory.TimeMap(self.A, 400.0)
        self.assertAlmostEqual(tm.s(12.0), 300.0)
        self.assertAlmostEqual(tm.s(7.0), 150.0)
        self.assertAlmostEqual(tm.s(1.0), tm.s(21.0))          # before the first crossing = the end of the lap
        self.assertAlmostEqual(tm.t(150.0), 7.0)
        self.assertAlmostEqual(tm.s(tm.t(333.0)), 333.0, places=6)

    def test_profile_keeps_anchors(self):
        tr = ring()
        tm = inventory.TimeMap(self.A, 400.0, inventory.speed_profile(tr), tr['spacing_m'])
        self.assertAlmostEqual(tm.s(12.0), 300.0, places=3)
        self.assertAlmostEqual(tm.s(tm.t(123.0)), 123.0, places=3)

    def test_rejects_unordered(self):
        with self.assertRaises(ValueError):
            inventory.TimeMap([{'name': 'a', 't': 1, 's': 10}, {'name': 'b', 't': 2, 's': 5}], 100)

    def test_residuals(self):
        r = inventory.TimeMap(self.A, 400.0).residuals()
        self.assertEqual(r[0]['name'], 'X')
        self.assertAlmostEqual(r[0]['loo_residual_m'], 100.0)    # linear from S/F to end predicts 200 at t 12
        self.assertAlmostEqual(r[0]['v_in'], 30.0)


class StrictSegmentTest(unittest.TestCase):
    """extra_maps (Mid-Ohio round 4): a segment that starts mid-lap and crosses S/F; no folding outside it."""
    def test_segment_crosses_sf_and_refuses_outside(self):
        A = [{'name': 'TV', 't': 10.0, 's': 300.0}, {'name': 'S/F', 't': 14.0, 's': 400.0}, {'name': 'T1', 't': 16.0, 's': 450.0}]
        tm = inventory.TimeMap(A, 400.0, strict=True)
        self.assertAlmostEqual(tm.s(12.0), 350.0)
        self.assertAlmostEqual(tm.s(15.0), 25.0)                # past S/F: wrapped into the lap
        with self.assertRaises(ValueError):
            tm.s(9.0)
        with self.assertRaises(ValueError):
            tm.s(16.5)


class UncertaintyTest(unittest.TestCase):
    """position_uncertainty (Mid-Ohio round 5): sigma from the bracketing anchors' leave-one-out residuals; a map whose
    largest residual exceeds corroborate_over_m marks its rows 'corroborate'; explicit-s rows use their video's map."""
    GOOD = [{'name': 'S/F', 't': 0.0, 's': 0.0}, {'name': 'a', 't': 10.0, 's': 105.0}, {'name': 'b', 't': 20.0, 's': 200.0},
            {'name': 'end', 't': 40.0, 's': 400.0}]
    WEAK = [{'name': 'p', 't': 0.0, 's': 0.0}, {'name': 'q', 't': 10.0, 's': 160.0}, {'name': 'r', 't': 20.0, 's': 200.0}]

    def test_sigma_and_placement(self):
        g = inventory.TimeMap(self.GOOD, 400.0)
        w = inventory.TimeMap(self.WEAK, 400.0, strict=True)
        res = {r['name']: abs(r['loo_residual_m']) for r in g.residuals()}
        self.assertEqual(inventory.sigma_at(g, 5.0), round(res['a'], 1))            # S/F has none: anchor a's
        self.assertEqual(inventory.sigma_at(g, 15.0), round(max(res['a'], res['b']), 1))
        rows = [{'t': 5.0, 'map': 'weak'}, {'t': 15.0}, {'t': None, 'source': 'onboard:vg@15'},
                {'t': None, 'source': 'streetview:x@0'}]
        inventory.add_uncertainty(rows, {'primary': ('vg', g), 'weak': ('vw', w)}, {'corroborate_over_m': 40})
        self.assertEqual(rows[0]['placement'], 'corroborate')                        # |residual| 60 m > 40 m
        self.assertEqual(rows[0]['sigma_s_m'], 60.0)
        self.assertEqual(rows[1]['placement'], 'direct')
        self.assertEqual(rows[2]['sigma_s_m'], rows[1]['sigma_s_m'])                 # explicit s: its video's map at t
        self.assertIsNone(rows[3]['sigma_s_m'])
        self.assertEqual(rows[3]['placement'], 'corroborate')


class RowTest(unittest.TestCase):
    def test_validation(self):
        ok = {'t': 2, 'side': 'left', 'kind': 'wall', 'confidence': 0.9, 'attrs': {'h_m': 1.0, 'h_method': 'jersey-ref'}}
        self.assertEqual(inventory.validate_row(ok, 'x'), [])
        self.assertTrue(inventory.validate_row({**ok, 'attrs': {'h_m': 1.0}}, 'x'))           # a height needs a method
        self.assertTrue(inventory.validate_row({**ok, 'kind': 'shrub'}, 'x'))
        self.assertTrue(inventory.validate_row({k: v for k, v in ok.items() if k != 't'} | {'s': 5}, 'x'))  # s needs a source


class HeightsTest(unittest.TestCase):
    def test_horizon_ratio(self):
        self.assertAlmostEqual(heights.height_horizon(366, 459, 414.5, 2.5), 5.22, places=2)
        self.assertAlmostEqual(heights.height_horizon(414.5, 500, 414.5, 2.5), 2.5)           # top on the horizon = camera height
        with self.assertRaises(ValueError):
            heights.height_horizon(100, 400, 414.5, 2.5)

    def test_reference_and_camera(self):
        self.assertAlmostEqual(heights.height_reference(339, 545, 461, 545, 2.03), 4.98, places=2)
        H = heights.camera_height(492, 527, 460, 0.81)
        self.assertAlmostEqual(heights.height_horizon(492, 527, 460, H), 0.81, places=6)

    def test_distance_and_angles(self):
        f = heights.focal_px(800, 90)
        self.assertAlmostEqual(f, 400.0)
        d = heights.distance_horizon(500, 400, 2.0, 800, 90)
        self.assertAlmostEqual(d, 8.0)
        self.assertAlmostEqual(heights.height_angles(300, 500, 400, 800, 90, d), 4.0)

    def test_sun(self):
        # Sonoma, summer solstice, solar noon (about 20:10 UTC): elevation ~ 90 - 38.16 + 23.44 = 75.3
        e = heights.sun_elevation(38.161, -122.455, dt.datetime(2025, 6, 21, 20, 10))
        self.assertAlmostEqual(e, 75.3, delta=0.6)
        self.assertAlmostEqual(heights.height_shadow(10, 45), 10.0)


if __name__ == '__main__':
    unittest.main()
