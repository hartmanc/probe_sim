"""Equirectangular (360 deg) frame -> perspective (pinhole) view for a given heading, pitch, roll and field of view
(build-track stage 0.6 with a 360 deg onboard; Mid-Ohio round 4, the INDYCAR 360 lap e25u_vjn1uM).

Frame convention: column x spans longitude -180..+180 deg left to right (x = W/2 is longitude 0, the frame's own
"forward"), row y spans latitude +90 (top) .. -90 (bottom). A view's yaw is measured from that forward direction,
positive to the RIGHT (clockwise seen from above), pitch positive UP, roll positive clockwise in the view. `yaw0` is the
longitude of the car's straight-ahead in the frame (measured once per video from a straight: the vanishing point),
so `yaw` in the CLI is relative to the car: 0 ahead, 90 right, -90 left, 180 back.

    uv run --python 3.12 --with numpy,pillow python -I tools/track/inventory/equirect.py \
        --frames <dir of t###.jpg equirect frames> --out <dir> [--yaw0 0] [--pitch -5] [--fov 100] [--size 960x600]
        [--views ahead:0,right:90,back:180,left:-90]
    writes <out>/t###_<view>.jpg for every frame (reference only, never committed)

numpy + PIL only; bilinear sampling with longitude wrap-around. Reads reference imagery, writes reference imagery.
"""
import argparse
import glob
import os

import numpy as np
from PIL import Image


def rays(out_w, out_h, fov_deg):
    """Unit view rays (camera frame: x right, y up, z forward) for an out_w x out_h pinhole of horizontal fov."""
    f = (out_w / 2) / np.tan(np.radians(fov_deg) / 2)
    u = np.arange(out_w) + 0.5 - out_w / 2
    v = np.arange(out_h) + 0.5 - out_h / 2
    U, V = np.meshgrid(u, v)
    d = np.stack([U / f, -V / f, np.ones_like(U)], axis=-1)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def rotation(yaw_deg, pitch_deg, roll_deg=0.0):
    """Camera-to-world rotation: roll about the view axis, then pitch (up +) about x, then yaw (right +) about y."""
    y, p, r = np.radians([yaw_deg, pitch_deg, roll_deg])
    Rz = np.array([[np.cos(r), np.sin(r), 0], [-np.sin(r), np.cos(r), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(p), np.sin(p)], [0, -np.sin(p), np.cos(p)]])
    Ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    return Ry @ Rx @ Rz


def lonlat(yaw_deg, pitch_deg, fov_deg, out_w, out_h, roll_deg=0.0):
    d = rays(out_w, out_h, fov_deg) @ rotation(yaw_deg, pitch_deg, roll_deg).T
    lon = np.arctan2(d[..., 0], d[..., 2])                  # + right
    lat = np.arcsin(np.clip(d[..., 1], -1, 1))              # + up
    return lon, lat


def sample(eq, lon, lat):
    """Bilinear sample of an H x W (x C) equirectangular array at longitudes / latitudes (radians)."""
    H, W = eq.shape[:2]
    x = (lon / (2 * np.pi) + 0.5) * W - 0.5
    y = (0.5 - lat / np.pi) * H - 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = x - x0; fy = y - y0
    x1 = (x0 + 1) % W; x0 = x0 % W
    y1 = np.clip(y0 + 1, 0, H - 1); y0 = np.clip(y0, 0, H - 1)
    if eq.ndim == 3:
        fx = fx[..., None]; fy = fy[..., None]
    e = eq.astype(np.float32)
    top = e[y0, x0] * (1 - fx) + e[y0, x1] * fx
    bot = e[y1, x0] * (1 - fx) + e[y1, x1] * fx
    return top * (1 - fy) + bot * fy


def view(eq, yaw_deg, pitch_deg=0.0, fov_deg=90.0, out_w=960, out_h=600, roll_deg=0.0):
    """Perspective view (out_h x out_w, same channels and dtype as eq) looking at yaw / pitch from the frame's centre."""
    lon, lat = lonlat(yaw_deg, pitch_deg, fov_deg, out_w, out_h, roll_deg)
    out = sample(eq, lon, lat)
    return np.clip(np.rint(out), 0, 255).astype(eq.dtype) if eq.dtype == np.uint8 else out.astype(eq.dtype)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--frames', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--yaw0', type=float, default=0.0, help="longitude (deg, + right) of the car's straight-ahead")
    ap.add_argument('--pitch', type=float, default=0.0); ap.add_argument('--roll', type=float, default=0.0)
    ap.add_argument('--fov', type=float, default=100.0); ap.add_argument('--size', default='960x600')
    ap.add_argument('--views', default='ahead:0,right:90,back:180,left:-90')
    ap.add_argument('--glob', default='t*.jpg'); ap.add_argument('--quality', type=int, default=85)
    a = ap.parse_args()
    w, h = (int(v) for v in a.size.split('x'))
    views = [(k, float(v)) for k, v in (p.split(':') for p in a.views.split(','))]
    os.makedirs(a.out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(a.frames, a.glob)))
    cache = {}
    for fp in files:
        eq = np.asarray(Image.open(fp).convert('RGB'))
        stem = os.path.splitext(os.path.basename(fp))[0]
        for name, yaw in views:
            key = (eq.shape, name)
            if key not in cache:
                cache[key] = lonlat(a.yaw0 + yaw, a.pitch, a.fov, w, h, a.roll)
            img = np.clip(np.rint(sample(eq, *cache[key])), 0, 255).astype(np.uint8)
            Image.fromarray(img).save(os.path.join(a.out, f'{stem}_{name}.jpg'), quality=a.quality)
    print(f'{len(files)} frames x {len(views)} views -> {a.out}')


if __name__ == '__main__':
    main()
