"""Unit tests of the package comparison (tools/track/compare/compare_packages.py):
python3 -I -m unittest discover -s tools/track/compare -p 'test_compare_packages.py'"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_packages as CP  # noqa: E402


def track():
    """a straight 200 m 'track' along +x, edges at y +-5, 1 m stations"""
    n = 201
    return {"n": n, "spacing_m": 1.0, "center": [[x, 0, 0] for x in range(n)], "left": [[x, 5, 0] for x in range(n)],
            "right": [[x, -5, 0] for x in range(n)]}


def wall(x0, x1, y, h=1.0, kind="concrete", fence=0.0):
    return {"kind": kind, "h": h, "fence": fence, "pts": [[x0, y, 0], [x1, y, 0]], "src": "test"}


class MatchTest(unittest.TestCase):
    def test_within_tolerance_is_matched_beyond_is_missing_and_extra(self):
        ref = CP.objects({"barriers": [wall(0, 100, -8)]})
        near = CP.objects({"barriers": [wall(0, 100, -14)]})          # 6 m off: matched
        far = CP.objects({"barriers": [wall(0, 100, -30)]})           # 22 m off: missing + extra
        r = CP.match(ref, near)["wall"]
        self.assertEqual((len(r["matched"]), len(r["missing"]), len(r["extra"])), (1, 0, 0))
        self.assertAlmostEqual(r["matched"][0][2], 6.0, places=1)
        r = CP.match(ref, far)["wall"]
        self.assertEqual((len(r["matched"]), len(r["missing"]), len(r["extra"])), (0, 1, 1))

    def test_partial_overlap_needs_half_the_points(self):
        ref = CP.objects({"barriers": [wall(0, 100, -8)]})
        self.assertEqual(len(CP.match(ref, CP.objects({"barriers": [wall(0, 60, -8)]}))["wall"]["matched"]), 1)
        self.assertEqual(len(CP.match(ref, CP.objects({"barriers": [wall(0, 30, -8)]}))["wall"]["missing"]), 1)

    def test_kinds_do_not_mix_and_catch_fences_count_as_fences(self):
        ref = CP.objects({"barriers": [wall(0, 100, -8, fence=3.0)]})
        cand = CP.objects({"barriers": [wall(0, 100, -8, kind="tyres")]})
        rep = CP.match(ref, cand)
        self.assertEqual(len(rep["wall"]["missing"]), 1)
        self.assertEqual(len(rep["fence"]["missing"]), 1)
        self.assertEqual(len(rep["tyre_wall"]["extra"]), 1)
        self.assertEqual(ref[1]["h"], 4.0)

    def test_height_differences_use_the_coverage_rule(self):
        ref = CP.objects({"barriers": [wall(0, 100, -8, h=1.0), wall(0, 100, 8, h=4.0)]})
        cand = CP.objects({"barriers": [wall(0, 100, -8, h=1.2), wall(0, 100, 8, h=2.5)]})
        r = CP.match(ref, cand)["wall"]
        self.assertEqual(len(r["heights"]), 1)
        self.assertEqual(r["heights"][0][2], -1.5)
        self.assertTrue(CP.height_differs(1.0, 1.31))
        self.assertFalse(CP.height_differs(1.0, 1.25))

    def test_points_kerbs_and_structures(self):
        sc = {"landmarks": [{"kind": "marshal", "x": 50, "y": 12, "h": 3.8, "text": "T1"}, {"kind": "sign", "x": 10, "y": 6, "text": "A"}],
              "kerbs": {"strips": [{"side": 1, "s0": 20, "s1": 40, "src": "c20"}]},
              "structures": [{"type": "mast", "name": "Light masts", "at": [[60, 30, 1, 0]], "h": 20}, {"type": "paint", "name": "boxes"}]}
        o = CP.objects(sc, track())
        kinds = sorted(x["kind"] for x in o)
        self.assertEqual(kinds, ["board", "kerb", "mast", "station"])
        kerb = next(x for x in o if x["kind"] == "kerb")
        self.assertEqual(kerb["pts"][0], (20, 5))
        self.assertEqual(len(kerb["pts"]), 21)
        moved = CP.objects({**sc, "landmarks": [{"kind": "marshal", "x": 50, "y": 40, "h": 3.8}]}, track())
        r = CP.match(o, moved)
        self.assertEqual(len(r["station"]["missing"]), 1)
        self.assertEqual(len(r["board"]["missing"]), 1)

    def test_report_and_stills_pairing(self):
        ref = CP.objects({"barriers": [wall(0, 100, -8)]})
        rep = CP.match(ref, [])
        md = CP.report_md(rep, "a", "b", 15, 0.5, CP.station_fn(track()))
        self.assertIn("| wall | 1 | 0 | 0 | 1 | 0 | 0 | - |", md)
        self.assertIn("s 50", md)
        js = CP.summary_json(rep)
        self.assertEqual(js["wall"]["missing"], 1)
        pairs = CP.pair_stills({"shots": [{"file": "sim/a.jpg"}, {"file": "sim/b.jpg"}]}, {"shots": [{"file": "sim/b.jpg"}]})
        self.assertEqual([(a["file"], b and b["file"]) for a, b in pairs], [("sim/a.jpg", None), ("sim/b.jpg", "sim/b.jpg")])

    def test_cli_on_two_package_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            for name, y in (("ref", -8), ("cand", -9)):
                os.makedirs(os.path.join(d, name))
                with open(os.path.join(d, name, "scenery.json"), "w") as fh:
                    json.dump({"barriers": [wall(0, 100, y)]}, fh)
                with open(os.path.join(d, name, "track.json"), "w") as fh:
                    json.dump(track(), fh)
            out, js = os.path.join(d, "r.md"), os.path.join(d, "r.json")
            CP.main(["--ref", os.path.join(d, "ref"), "--cand", os.path.join(d, "cand"), "--out", out, "--json", js])
            with open(js) as fh:
                self.assertEqual(json.load(fh)["wall"]["matched"], 1)
            with open(out) as fh:
                self.assertIn("| **all** | 1 | 1 | 1 | 0 | 0 | 0 | |", fh.read())


if __name__ == "__main__":
    unittest.main()
