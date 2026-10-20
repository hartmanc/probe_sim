"""Sample the clean z20 captures (reference only) at world points: for each point the capture where it sits most central
and unmasked, shifted by that capture's registration (captures.capture_list). Shared by the evidence tools of the
scenery round (kerb_detect.py, wall_measure.py, capwin.py).
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import captures as CAP  # noqa: E402


class Sampler:
    def __init__(self, cfg, which='clean'):
        self.tiles = CAP.capture_list(cfg, which)
        self.mpp = cfg['captures']['mpp']
        self._img = {}

    def image(self, t):
        if t['name'] not in self._img:
            im = np.asarray(Image.open(t['path']).convert('RGB'))
            self._img[t['name']] = (im, t['mask'](*im.shape[:2]))
        return self._img[t['name']]

    def sample(self, X, Y, group=None):
        """RGB (..., 3) at world points X, Y (same shape) and the capture index used (-1 = none). `group`: an int
        array of X's shape whose members must all come from one capture (a whole profile), else per point."""
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        sh = X.shape
        X = X.ravel(); Y = Y.ravel()
        out = np.full((len(X), 3), np.nan, np.float32)
        best = np.full(len(X), np.inf)
        used = np.full(len(X), -1)
        g = None if group is None else np.asarray(group).ravel()
        for ti, t in enumerate(self.tiles):
            if 'size' not in t:
                with Image.open(t['path']) as im_:
                    t['size'] = im_.size
            Wt, Ht = t['size']
            px = Wt / 2 + (X + t['dx'] - t['x']) / self.mpp
            py = Ht / 2 - (Y + t['dy'] - t['y']) / self.mpp
            inside = (px >= 1) & (px < Wt - 2) & (py >= 1) & (py < Ht - 2)
            if not inside.any():
                continue
            im, m = self.image(t)
            ok = inside.copy()
            ok[inside] = m[np.round(py[inside]).astype(int), np.round(px[inside]).astype(int)]
            sc = np.abs(px / Wt - 0.5) + np.abs(py / Ht - 0.5)
            if g is not None:
                # a group is taken from this capture only if every member is inside it; score = the group's worst
                gid = g
                allok = np.ones(gid.max() + 1, bool)
                np.logical_and.at(allok, gid, ok)
                gsc = np.zeros(gid.max() + 1)
                np.maximum.at(gsc, gid, np.where(ok, sc, 9))
                ok = allok[gid]
                sc = gsc[gid]
            take = ok & (sc < best)
            if not take.any():
                continue
            out[take] = CAP.bilinear(im, px[take], py[take])
            best[take] = sc[take]
            used[take] = ti
        return out.reshape(sh + (3,)), used.reshape(sh)
