"""Painted road edges for the centre refit (stage 1 geometry; was measure_paint.py, 18 Oct 2026).

For every station and every Google capture covering it: sample the image along the station's normal (0.1 m steps,
-16..+16 m), classify each sample as road (asphalt: low saturation, brightness near this section's own asphalt) or
not (white edge line, kerb paint, green verge, dirt, pale runoff, grass), start at the racing line (or the centre when
there is none) and walk outward on each side until the next 1.2 m holds under 35 % road; carry the edge over a
red/white kerb band. Each capture is shifted Google -> ortho first: by its own registration against the graded ortho
(per_capture, how Laguna's centre was refitted on 18 Oct 2026; median Google - NAIP 0.3 m) or by the config's one
common shift. Median over captures. Returns lat_left, lat_right (signed lateral of each painted edge from the given
centre line, + = left) and the per-station count; register() is also used by register_clean.py.
"""
import numpy as np
from PIL import Image, ImageFilter


def register(g, t, ORT, O, mpp):
    """Google - ortho offset (m) by phase correlation of edge maps at 0.3 m/px."""
    S = 0.3; W = int(1440 * mpp / S); H = int(725 * mpp / S)
    mx = (O['x1'] - O['x0']) / O['width_px']; my = (O['y1'] - O['y0']) / O['height_px']
    def edges(a):
        b = np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)).filter(ImageFilter.FIND_EDGES), float)
        return (b - b.mean()) / (b.std() + 1e-6)
    Ga = np.asarray(g.convert('L').resize((W, H)), float)
    x0 = t['x'] - W / 2 * S; y1 = t['y'] + H / 2 * S
    px0 = (x0 - O['x0']) / mx; py0 = (O['y1'] - y1) / my
    Oa = np.asarray(ORT.crop((int(px0), int(py0), int(px0 + W * S / mx) + 1, int(py0 + H * S / my) + 1)).resize((W, H)), float)
    m = np.ones((H, W)); m[:int(H * 0.8), :int(W * 0.33)] = 0; m[:int(H * 0.09), :] = 0; m[:, :int(W * 0.06)] = 0
    m[int(H * 0.8):, int(W * 0.88):] = 0; m[int(H * 0.93):, :] = 0
    w = np.outer(np.hanning(H), np.hanning(W)) * m
    F = np.fft.fft2(edges(Ga) * w) * np.conj(np.fft.fft2(edges(Oa) * w)); r = np.fft.ifft2(F / (np.abs(F) + 1e-6)).real
    iy, ix = np.unravel_index(r.argmax(), r.shape)
    if iy > H // 2: iy -= H
    if ix > W // 2: ix -= W
    return ix * S, -iy * S, r.max() / r.std()

def measure(C, line, captures, ortho_img, O, mpp, registration='per_capture', log=print):
    """C: (n, 2) centre; line: (n,) lateral start of the walk (racing line, 0 = centre); captures: dicts with path, x, y,
    mask (callable H, W -> bool) and dx, dy (the common shift, used unless registration == 'per_capture');
    ortho_img: the graded ortho (PIL image) with its track.json `ortho` block O."""
    n = len(C)
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    MPP = mpp
    ORT = ortho_img.convert('L')
    lats = np.arange(-16, 16.0001, 0.1); L0 = np.searchsorted(lats, 0)
    meas = [[] for _ in range(n)]; regs = []
    for t in captures:
        g = Image.open(t['path']).convert('RGB')
        if registration == 'per_capture':
            dx, dy, pk = register(g, t, ORT, O, mpp)
            if pk < 8: dx = dy = 0.0
        else:
            dx, dy, pk = t['dx'], t['dy'], 0.0
        regs.append((t['name'], dx, dy, pk))
        im = np.asarray(g).astype(np.int16); H, W = im.shape[:2]; mask = t['mask'](H, W)
        # a feature at world p appears in Google at p + (dx, dy): sample Google there
        X = C[:, 0:1] + lats[None, :] * NL[:, 0:1] + dx; Y = C[:, 1:2] + lats[None, :] * NL[:, 1:2] + dy
        px = np.round(W / 2 + (X - t['x']) / MPP).astype(int); py = np.round(H / 2 - (Y - t['y']) / MPP).astype(int)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        for i in np.where(ok.all(1))[0]:
            if not mask[py[i], px[i]].all(): continue
            v = im[py[i], px[i]]; br = v.mean(1); sat = v.max(1) - v.min(1)
            li = int(np.clip(np.searchsorted(lats, line[i]), 15, len(lats) - 16))
            core = slice(li - 15, li + 16)
            # road = any unsaturated grey (rubbered line and sun-bleached asphalt alike); not road = dirt / kerb red /
            # green verge (saturated) or white paint (bright)
            white = (br > 200) & (sat < 35)
            road = (sat < 30) & ~white & (br > 35)
            if road[core].mean() < 0.6:
                # the logged line can sit on the inside paint at an apex: start from the nearest solid asphalt instead
                cs0 = np.r_[0, np.cumsum(road)]
                good = [k for k in range(15, len(lats) - 16) if (cs0[k + 16] - cs0[k - 15]) / 31 >= 0.85]
                if not good: continue
                li = min(good, key=lambda k: abs(k - li))
                if abs(lats[li] - line[i]) > 6: continue
                core = slice(li - 15, li + 16)
            ref = np.median(br[core][road[core]])
            win = 20
            cs = np.r_[0, np.cumsum(road)]
            def walk(dirn):
                k = li
                while 0 <= k + dirn * win < len(lats) and 0 <= k < len(lats):
                    a, b = (k, k + win) if dirn > 0 else (k - win + 1, k + 1)
                    if (cs[b] - cs[a]) / win < 0.3:      # leaving the road onto dirt, kerb or verge
                        j = k
                        while 0 <= j < len(lats) and road[j]: j += dirn
                        return j - dirn
                    if white[k]:                          # a painted line: an edge if the surface beyond it is not this asphalt
                        j = k
                        while 0 <= j < len(lats) and white[j]: j += dirn
                        seg = slice(min(j, j + dirn * 15), max(j, j + dirn * 15) + 1)
                        if 0 <= j + dirn * 15 < len(lats):
                            beyond = br[seg][road[seg]]
                            if road[seg].mean() < 0.5 or (len(beyond) and abs(np.median(beyond) - ref) > 18):
                                return k - dirn
                        k = j; continue
                    k += dirn
                return None
            kl, kr = walk(+1), walk(-1)
            if kl is None or kr is None: continue
            # kerbs are driveable pavement: carry the edge over a red/white kerb band (<= 1.5 m) beyond the paint
            gb = np.abs(v[:, 1] - v[:, 2])
            red = (v[:, 0] > 100) & (v[:, 0] - v[:, 1] > 25) & (v[:, 0] - v[:, 2] > 20) & (gb < 20)   # dirt has G >> B
            kerbc = red | ((br > 140) & (sat < 45) & (gb < 20))
            def over_kerb(k, dirn):
                j = k + dirn; last = k; seen_red = False
                while 0 <= j < len(lats) and abs(j - k) <= 15:
                    a, b = sorted((j, j + dirn * 3))
                    if a < 0 or b >= len(lats): break
                    if kerbc[a:b + 1].mean() >= 0.5:
                        seen_red |= bool(red[j]); last = j; j += dirn
                    else: break
                return last if seen_red and abs(last - k) >= 4 else k
            kl2, kr2 = over_kerb(kl, +1), over_kerb(kr, -1)
            el, er = lats[kl2], lats[kr2]
            if not (6.0 <= el - er <= 20.0): continue
            meas[i].append((el, er))
    lat_l = np.full(n, np.nan); lat_r = np.full(n, np.nan); cnt = np.zeros(n, int)
    for i in range(n):
        if meas[i]:
            a = np.array(meas[i]); lat_l[i] = np.median(a[:, 0]); lat_r[i] = np.median(a[:, 1]); cnt[i] = len(a)
    have = cnt > 0
    log('paint: stations measured %d / %d from %d captures' % (have.sum(), n, len(regs)))
    if regs:
        log('paint: google-ortho offset median dx %.2f dy %.2f' % tuple(np.median([[r[1], r[2]] for r in regs], 0)))
    w = lat_l - lat_r
    if have.any():
        log('paint: painted width p5/50/95', np.nanpercentile(w, [5, 50, 95]).round(2),
            '; midpoint offset from centre |mid| p50/p90/max', np.nanpercentile(np.abs((lat_l + lat_r) / 2), [50, 90, 100]).round(2))
    return dict(lat_left=lat_l, lat_right=lat_r, count=cnt, line=line, regs=regs)
