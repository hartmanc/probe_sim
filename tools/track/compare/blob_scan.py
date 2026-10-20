"""Station / hut scan on the clean captures (build-track 3.8): bright roof blobs 2-6 m across within `reach` m of the track
edges, with the share of dark pixels in a ring 1.5-5 m around them (a tyre-faced mound reads dark). Every capture is
scanned; prints one line per capture with its candidates (station, side, metres beyond the edge, roof size, ring dark
share, lat/lon) for the 3.8 ledger. Candidates only: each is confirmed on a capture window and the onboard.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/blob_scan.py --track <id> --pkg <dir> [--json out]
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import captures as CAP  # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--reach', type=float, default=45.0); ap.add_argument('--json', default=None)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track); mpp = cfg['captures']['mpp']
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]; n = len(C)
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True); NL = np.c_[-tg[:, 1], tg[:, 0]]
    hl = ((L - C) * NL).sum(1); hr = -((R - C) * NL).sum(1); kd = cKDTree(C); sp = T['spacing_m']
    lat0, lon0 = cfg['origin']; Rr = 6378137.0; cl = math.cos(math.radians(lat0))
    found = []; per = {}
    for t in CAP.capture_list(cfg, 'clean'):
        im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32); H, W = im.shape[:2]; mask = t['mask'](H, W)
        lum = im.mean(2); white = (im.min(2) > 205) & mask
        lab, nlab = ndi.label(white); per[t['name']] = []
        for k, sl in enumerate(ndi.find_objects(lab), 1):
            area = (lab[sl] == k).sum() * mpp * mpp
            if not (3.0 <= area <= 40.0): continue
            ys, xs = np.nonzero(lab[sl] == k); cy, cx = ys.mean() + sl[0].start, xs.mean() + sl[1].start
            ext = max(np.ptp(xs), np.ptp(ys)) * mpp
            if ext > 8.0: continue
            r0, r1 = int(1.5 / mpp), int(5.0 / mpp)
            yy, xx = np.ogrid[:H, :W]; d = np.hypot(yy - cy, xx - cx)
            ring = (d >= r0 + ext / 2 / mpp) & (d <= r1 + ext / 2 / mpp) & mask
            dark = float((lum[ring] < 95).mean()) if ring.any() else 0.0
            wx = t['x'] - t['dx'] + (cx - W / 2) * mpp; wy = t['y'] - t['dy'] - (cy - H / 2) * mpp
            dd, i = kd.query([wx, wy]); lat = float(((np.array([wx, wy]) - C[i]) * NL[i]).sum())
            side = 'left' if lat > 0 else 'right'; beyond = abs(lat) - (hl[i] if lat > 0 else hr[i])
            if beyond < 0 or beyond > a.reach: continue
            rec = dict(capture=t['name'], s=round(i * sp, 1), side=side, beyond_m=round(beyond, 1), roof_m2=round(area, 1), ring_dark=round(dark, 2),
                       x=round(wx, 1), y=round(wy, 1), lat=round(lat0 + math.degrees(wy / Rr), 7), lon=round(lon0 + math.degrees(wx / (Rr * cl)), 7))
            per[t['name']].append(rec); found.append(rec)
    # one candidate per object (within 4 m), the record seen on most captures
    objs = []
    for r in sorted(found, key=lambda r: -r['ring_dark']):
        o = next((o for o in objs if math.hypot(o['x'] - r['x'], o['y'] - r['y']) < 4.0), None)
        if o: o['captures'].append(r['capture']); continue
        objs.append({**r, 'captures': [r['capture']]})
    objs.sort(key=lambda o: o['s'])
    for o in objs:
        print(f"s {o['s']:7.1f} {o['side']:5s} {o['beyond_m']:5.1f} m beyond  roof {o['roof_m2']:5.1f} m2  dark ring {o['ring_dark']:.2f}  ({o['lat']}, {o['lon']})  on {', '.join(o['captures'][:3])}")
    print(f"{len(objs)} candidates from {len(per)} captures ({sum(1 for v in per.values() if not v)} with none)")
    if a.json: json.dump({'per_capture': per, 'objects': objs}, open(a.json, 'w'), indent=0)


if __name__ == '__main__':
    main()
