"""The unpainted-side edge gate (owner's decision, 20 Oct 2026; edge_gate.UNPAINTED / unpainted_side / bias_gate).

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

    def test_painted_side_keeps_the_old_gate(self):
        # the same ragged readings on a side whose evidence is painted lines: not unpainted, so the builder applies
        # FITTED's 90 % within 0.25 m, which these readings fail
        st, r = ragged()
        self.assertFalse(EG.unpainted_side([None] * len(st)))
        self.assertLess(np.mean(np.abs(r) <= 0.25), EG.FITTED['within'])
        self.assertEqual(EG.fitted_thresholds({})['within'], 0.90)


class Classification(unittest.TestCase):
    def test_threshold(self):
        self.assertTrue(EG.unpainted_side(['asphalt_end'] * 80 + ['kerb_band'] * 20))
        self.assertFalse(EG.unpainted_side(['asphalt_end'] * 79 + ['kerb_band'] * 21))
        self.assertFalse(EG.unpainted_side([]))

    def test_unpainted_thresholds_only_tighten(self):
        self.assertEqual(EG.unpainted_thresholds({})['covered'], 0.50)
        self.assertEqual(EG.unpainted_thresholds({'fit_covered': 0.7})['covered'], 0.7)
        self.assertEqual(EG.unpainted_thresholds({'fit_covered': 0.3})['covered'], 0.50)
        self.assertEqual(EG.unpainted_thresholds({})['wave_rms'], EG.FITTED['wave_rms'])

    def test_laguna_and_sonoma_are_not_unpainted(self):
        # their features tables: the share of each side's stations under asphalt_end stays far below the 80 % line
        for tid, n in (('laguna_seca', 3560), ('sonoma', 4090)):
            cfg = trackcfg.load(tid)
            for side in ('left', 'right'):
                kinds = []
                for s in range(n):
                    f = next((f[3] for f in cfg['features'] if f[0] == side and (s - f[1]) % n <= (f[2] - f[1]) % n), None)
                    kinds.append(f)
                self.assertFalse(EG.unpainted_side(kinds), (tid, side))


if __name__ == '__main__':
    unittest.main()
