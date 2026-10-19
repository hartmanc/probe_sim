"""Google satellite captures (reference only, never textures) for the track pipeline: the capture lists, their masks
and the one common Google-to-ortho shift (tools/track/build_track.py; the method is in the build-track skill).

Two kinds, both z20 (0.12 m/px) 1440x725 screenshots with the centre lat/lon in a tile index:
  z20   - Maps screenshots with the UI visible (Laguna, 18 Oct 2026): UI rectangles masked (mask 'google_ui_2026_10_18').
  clean - UI hidden by page CSS, labels off (18 Oct evening on): only the Layers button, logo, attribution, one control
          and the cursor are masked. Laguna's set also masks the cursor of c20_a1..a3 on every capture
          (mask 'clean_2026_10_18'); new circuits park the cursor in a corner and use mask 'clean'.
Every capture is shifted by ONE common Google-minus-ortho shift (captures agree with each other to a pixel; per-capture
registrations against a 0.6 m ortho are noise). A clean capture's tile index carries rel_dx/rel_dy relative to that
frame (register_clean.py).
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def mask_google_ui_2026_10_18(H, W):
    """Google Maps UI on the z20 captures (search panel, chips, controls)."""
    m = np.ones((H, W), bool)
    m[:590, :470] = False; m[:62, :] = False; m[:, :78] = False; m[575:, 1265:] = False; m[675:, :] = False; m[610:, 85:180] = False
    return m


def mask_clean(H, W):
    """clean captures (UI hidden by page CSS, labels off): only the Layers button, logo, attribution, one control"""
    m = np.ones((H, W), bool)
    m[620:712, 85:178] = False; m[675:712, 695:815] = False; m[705:, 850:] = False; m[575:620, 1380:1430] = False; m[:30, 1420:] = False
    return m


def mask_clean_2026_10_18(H, W):
    m = mask_clean(H, W)
    m[222:268, 705:745] = False   # mouse cursor on c20_a1..a3 (taken before it was parked in the corner)
    return m


MASKS = {'google_ui_2026_10_18': mask_google_ui_2026_10_18, 'clean': mask_clean, 'clean_2026_10_18': mask_clean_2026_10_18}


def bilinear(im, px, py):
    H, W = im.shape[:2]
    x0 = np.clip(np.floor(px).astype(int), 0, W - 2); y0 = np.clip(np.floor(py).astype(int), 0, H - 2)
    fx = (px - x0)[..., None]; fy = (py - y0)[..., None]
    a = im[y0, x0]; b = im[y0, x0 + 1]; c = im[y0 + 1, x0]; d = im[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def capture_list(cfg, which, shift=None):
    """Captures as dicts {name, path, x, y, dx, dy, mask}. which: 'z20', 'clean' or 'z20,clean'. dx, dy = the common
    Google-minus-ortho shift (config captures.common_shift, or `shift` as measured by register_clean.py) plus, for a
    clean capture, its rel_dx/rel_dy. A feature at world p appears in a capture at p + (dx, dy)."""
    cc = cfg['captures']
    if shift is None and cc['common_shift'] is None and cc.get('clean_dir'):
        sj = os.path.join(cfg.path(cc['clean_dir']), 'shift.json')   # measured by register_clean.py
        if not os.path.exists(sj):
            raise SystemExit(f"captures: {sj} missing and config captures.common_shift is None: run "
                             f"register_clean.py --track {cfg['id']} --write (no silent (0, 0) shift)")
        shift = json.load(open(sj))['common_shift']
    sx, sy = shift if shift is not None else cc['common_shift']
    out = []
    if 'z20' in which and cc.get('z20_dir'):
        d = cfg.path(cc['z20_dir'])
        for t in json.load(open(os.path.join(d, cc['z20_index']))):
            out.append(dict(name=t['name'], path=os.path.join(d, t['name'] + '_google.jpg'), x=t['x'], y=t['y'],
                            dx=sx, dy=sy, mask=MASKS[cc.get('z20_mask') or 'google_ui_2026_10_18'], kind='z20'))
    if 'clean' in which and cc.get('clean_dir'):
        d = cfg.path(cc['clean_dir'])
        idx = os.path.join(d, cc['clean_index'])
        if not os.path.exists(idx):
            raise SystemExit(f"captures: clean capture index {idx} missing")
        if True:
            T = json.load(open(idx))
            unreg = [t['name'] for t in T if 'rel_dx' not in t]
            if unreg:
                raise SystemExit(f"captures: {len(unreg)} clean captures without registration ({', '.join(unreg[:5])}...): "
                                 f"run register_clean.py --track {cfg['id']} --write")
            for t in T:
                out.append(dict(name=t['name'], path=os.path.join(d, t['name'] + '_google.jpg'), x=t['x'], y=t['y'],
                                dx=sx + t['rel_dx'], dy=sy + t['rel_dy'], mask=MASKS[cc.get('clean_mask') or 'clean'],
                                kind='clean'))
    return out
