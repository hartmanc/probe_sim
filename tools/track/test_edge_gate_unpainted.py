"""The within gate per evidence kind (owner's decision, 20 Oct 2026; edge_gate.per_kind_gate / bias_gate /
asphalt_end_majority).

    uv run --python 3.12 --with pytest,numpy python -I -m pytest -q tools/track/test_edge_gate_unpainted.py
"""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import edge_gate as EG  # noqa: E402
import trackcfg  # noqa: E402


def ragged(n=2000, per=2, spread=1.0, shift=0.0, seed=3):
    rng = np.random.default_rng(seed)
    st = np.repeat(np.arange(n), per)
    return st, rng.uniform(-spread, spread, len(st)) + shift


class BiasGate(unittest.TestCase):
    def test_ragged_zero_bias_passes(self):
        st, r = ragged()
        g = EG.bias_gate(st, r, 2000)
        self.assertTrue(g['ok'], g)
        self.assertGreaterEqual(g['share'], 0.9)
        # the spread is large (the edge's own), and is only printed
        self.assertGreater(g['spread'][2], 0.8)

    def test_shifted_fails(self):
        st, r = ragged(shift=0.4)
        g = EG.bias_gate(st, r, 2000)
        self.assertFalse(g['ok'], g)
        self.assertGreater(abs(g['worst'][0]), 0.25)

    def test_sparse_windows_do_not_count(self):
        st = np.arange(0, 2000, 10); r = np.zeros(len(st))   # 4-5 readings per 41-station window
        g = EG.bias_gate(st, r, 2000)
        self.assertEqual(g['windows'], 0); self.assertFalse(g['ok'])

    def test_painted_readings_keep_fitted(self):
        # ragged readings that are all painted / kerb: judged by FITTED's 90 % within 0.25 m, which they fail
        st, r = ragged()
        g = EG.per_kind_gate([None] * len(st), st, r, 2000)
        self.assertIsNone(g['bias']); self.assertFalse(g['ok'])
        self.assertEqual(EG.fitted_thresholds({})['within'], 0.90)


class PerKind(unittest.TestCase):
    def mixed(self, kerb_good=True):
        # 60 % asphalt_end readings (ragged, unbiased) and 40 % kerb readings (sharp, or ragged)
        rng = np.random.default_rng(5)
        st_a = np.repeat(np.arange(2000), 3); r_a = rng.uniform(-1, 1, len(st_a))
        st_k = np.repeat(np.arange(2000), 2); r_k = rng.normal(0, 0.05 if kerb_good else 0.6, len(st_k))
        kinds = ['asphalt_end'] * len(st_a) + ['kerb_band'] * len(st_k)
        return kinds, np.r_[st_a, st_k], np.r_[r_a, r_k]

    def test_mixed_side_judged_per_kind(self):
        kinds, st, r = self.mixed()
        g = EG.per_kind_gate(kinds, st, r, 2000)
        self.assertAlmostEqual(g['ae_share'], 0.6)
        self.assertTrue(g['bias']['ok']); self.assertTrue(g['painted']['ok']); self.assertTrue(g['ok'])
        # the old pooled share would have failed: well under 90 % of all readings within 0.25 m
        self.assertLess(np.mean(np.abs(r) <= 0.25), 0.9)

    def test_kerb_readings_alone_decide_the_painted_measure(self):
        kinds, st, r = self.mixed(kerb_good=False)
        g = EG.per_kind_gate(kinds, st, r, 2000)
        self.assertTrue(g['bias']['ok']); self.assertFalse(g['painted']['ok']); self.assertFalse(g['ok'])

    def test_few_painted_readings_are_not_gated(self):
        g = EG.per_kind_gate([None] * 50, np.arange(50), np.ones(50), 2000)
        self.assertIsNone(g['painted']['ok']); self.assertTrue(g['ok'])

    def test_majority_sets_coverage(self):
        self.assertTrue(EG.asphalt_end_majority(['asphalt_end'] * 60 + ['kerb_band'] * 40))
        self.assertFalse(EG.asphalt_end_majority(['asphalt_end'] * 50 + ['kerb_band'] * 50))
        self.assertFalse(EG.asphalt_end_majority([]))
        self.assertEqual(EG.unpainted_thresholds({})['covered'], 0.50)
        self.assertEqual(EG.unpainted_thresholds({'fit_covered': 0.7})['covered'], 0.7)
        self.assertEqual(EG.unpainted_thresholds({'fit_covered': 0.3})['covered'], 0.50)
        self.assertEqual(EG.unpainted_thresholds({})['wave_rms'], EG.FITTED['wave_rms'])

    def test_laguna_and_sonoma_stay_painted_sides(self):
        # each has one short asphalt_end zone (Laguna left 478-528, Sonoma's T7 wall left 1860-2060): far from a
        # majority of either side's stations, so coverage stays at 60 % and FITTED's share holds over their painted
        # and kerb readings; the zone's own readings get the bias gate
        for tid, n in (('laguna_seca', 3560), ('sonoma', 4090)):
            cfg = trackcfg.load(tid)
            for side in ('left', 'right'):
                kinds = [next((f[3] for f in cfg['features'] if f[0] == side and (s_ - f[1]) % n <= (f[2] - f[1]) % n), None)
                         for s_ in range(n)]
                self.assertFalse(EG.asphalt_end_majority(kinds), (tid, side))
                self.assertLess(sum(k == 'asphalt_end' for k in kinds) / n, 0.06, (tid, side))
        st, r = ragged(spread=0.1)
        g = EG.per_kind_gate([None] * len(st), st, r, 2000)
        self.assertEqual(g['ae'], 0); self.assertIsNone(g['bias'])
        self.assertAlmostEqual(g['painted']['within'], float(np.mean(np.abs(r) <= 0.25)))


if __name__ == '__main__':
    unittest.main()
