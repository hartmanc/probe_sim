"""The unpainted-side edge gate (owner's decision, 20 Oct 2026; edge_gate.UNPAINTED / asphalt_end_majority /
side_within_gate / bias_gate / per_kind_report).

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
        st, r = ragged()
        rep = dict(assoc_kind=[None] * len(st), assoc_x=st, assoc_res=r, within_gated=float(np.mean(np.abs(r) <= 0.25)), assoc_share=0.9)
        g = EG.side_within_gate(rep, 2000, EG.fitted_thresholds({}))
        self.assertFalse(g['unpainted']); self.assertIsNone(g['bias']); self.assertFalse(g['ok'])


class SideRule(unittest.TestCase):
    def mixed(self, kerb_shift=0.0):
        # 60 % asphalt_end readings and 40 % kerb readings, both ragged (grey block bands blur like the asphalt end)
        rng = np.random.default_rng(5)
        st_a = np.repeat(np.arange(2000), 3); r_a = rng.uniform(-1, 1, len(st_a))
        st_k = np.repeat(np.arange(2000), 2); r_k = rng.normal(kerb_shift, 0.3, len(st_k))
        kinds = ['asphalt_end'] * len(st_a) + ['kerb_band'] * len(st_k)
        st = np.r_[st_a, st_k]; r = np.r_[r_a, r_k]
        return dict(assoc_kind=kinds, assoc_x=st, assoc_res=r, within_gated=float(np.mean(np.abs(r) <= 0.25)), assoc_share=0.9)

    def test_unpainted_side_pools_all_readings_in_the_bias_gate(self):
        rep = self.mixed()
        g = EG.side_within_gate(rep, 2000, EG.fitted_thresholds({}))
        self.assertTrue(g['unpainted']); self.assertTrue(g['ok'])
        self.assertLess(rep['within_gated'], 0.9)   # the painted share would have failed
        pk = EG.per_kind_report(rep['assoc_kind'], rep['assoc_res'])   # report only
        self.assertAlmostEqual(pk['asphalt_end']['share'], 0.6)

    def test_off_centre_kerb_zone_still_caught(self):
        # kerb readings sitting 0.6 m off the curve over the whole side move every window's median
        rep = self.mixed(kerb_shift=1.5)
        self.assertFalse(EG.side_within_gate(rep, 2000, EG.fitted_thresholds({}))['ok'])

    def test_majority_and_coverage(self):
        self.assertTrue(EG.asphalt_end_majority(['asphalt_end'] * 60 + ['kerb_band'] * 40))
        self.assertFalse(EG.asphalt_end_majority(['asphalt_end'] * 50 + ['kerb_band'] * 50))
        self.assertFalse(EG.asphalt_end_majority([]))
        self.assertEqual(EG.unpainted_thresholds({})['covered'], 0.50)
        self.assertEqual(EG.unpainted_thresholds({'fit_covered': 0.7})['covered'], 0.7)
        self.assertEqual(EG.unpainted_thresholds({'fit_covered': 0.3})['covered'], 0.50)
        self.assertEqual(EG.unpainted_thresholds({})['wave_rms'], EG.FITTED['wave_rms'])

    def test_laguna_and_sonoma_painted_computation_unchanged(self):
        # their sides are painted under both the old 80 % classification and the majority rule (asphalt_end under 6 %
        # of each side's stations), and the painted gate is the original formula: within_gated >= 0.90 and assoc >= 0.85
        for tid, n in (('laguna_seca', 3560), ('sonoma', 4090)):
            cfg = trackcfg.load(tid)
            for side in ('left', 'right'):
                kinds = [next((f[3] for f in cfg['features'] if f[0] == side and (s_ - f[1]) % n <= (f[2] - f[1]) % n), None)
                         for s_ in range(n)]
                self.assertFalse(EG.asphalt_end_majority(kinds), (tid, side))
                self.assertLess(sum(k == 'asphalt_end' for k in kinds) / n, 0.06, (tid, side))
        rng = np.random.default_rng(9)
        G = EG.fitted_thresholds({})
        for _ in range(200):
            wg, a = float(rng.uniform(0.8, 1.0)), float(rng.uniform(0.8, 1.0))
            kinds = [None] * 95 + ['asphalt_end'] * 5
            rep = dict(assoc_kind=kinds, assoc_x=np.arange(100), assoc_res=np.zeros(100), within_gated=wg, assoc_share=a)
            self.assertEqual(EG.side_within_gate(rep, 3560, G)['ok'], wg >= G['within'] and a >= G['assoc'])


if __name__ == '__main__':
    unittest.main()
