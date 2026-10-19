"""Compare a candidate track package with a reference one, per station (dry runs of build_track.py).

    uv run --python 3.12 --with numpy python -I tools/track/compare_package.py --cand <dir> [--ref public/tracks/<id>]
        [--json out.json] [--runs 0.30] [--by-corner]

Every candidate station is placed on the reference by projecting its centre point onto the reference centre
(fractional station); the reference values are interpolated there. Prints: n, spacing, length, station 0 distance;
centre offset (lateral distance of the candidate centre from the reference centre polyline); left and right edge
offsets (candidate edge point minus the reference edge point at the same fractional station, along the candidate's
normal, + = outward); heights of the profile columns (all 7, and the centre); the racing line (world position of each
line point against the reference line, lateral); the optimal and real ghost lap times; scenery part counts. Stretches
where an edge differs by more than --runs metres are listed with their station range, peak and mean.
"""
import argparse
import json
import os

import numpy as np


def load(d):
    T = json.load(open(os.path.join(d, 'track.json')))
    g = os.path.join(d, 'ghosts.json'); s = os.path.join(d, 'scenery.json')
    return T, (json.load(open(g)) if os.path.exists(g) else None), (json.load(open(s)) if os.path.exists(s) else None)


def normals(C):
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True)
    return np.c_[-t[:, 1], t[:, 0]], t


def project(P, Q):
    """fractional station on closed polyline P and signed lateral (+left) of points Q."""
    from scipy.spatial import cKDTree
    nl, t = normals(P)
    _, i = cKDTree(P).query(Q)
    rel = Q - P[i]
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    return (i + (rel * t[i]).sum(1) / seg[i]) % len(P), (rel * nl[i]).sum(1)


def interp_rows(A, u):
    n = len(A); i = np.floor(u).astype(int) % n; j = (i + 1) % n; f = (u - np.floor(u))[:, None]
    return A[i] * (1 - f) + A[j] * f


def runs(d, n, thr):
    out = []; big = np.abs(d) > thr
    if not big.any(): return out
    k = int(np.argmin(big)) if not big.all() else 0
    s = None
    for j in range(k, k + n + 1):
        b = big[j % n]
        if b and s is None: s = j
        elif not b and s is not None:
            seg = d[np.arange(s, j) % n]
            out.append(dict(s0=s % n, s1=(j - 1) % n, len=j - s, peak=float(seg[np.argmax(np.abs(seg))]), mean=float(seg.mean())))
            s = None
    return out


def compare(cand, ref, thr=0.30):
    Tc, Gc, Sc = load(cand); Tr, Gr, Sr = load(ref)
    Cc = np.array(Tc['center'])[:, :2]; Cr = np.array(Tr['center'])[:, :2]
    n = len(Cc); nlc, _ = normals(Cc)
    u, lat = project(Cr, Cc)
    res = dict(n=(Tc['n'], Tr['n']), spacing=(Tc['spacing_m'], Tr['spacing_m']), length=(Tc['length_m'], Tr['length_m']),
               station0_m=float(np.linalg.norm(Cc[0] - Cr[0])), station_shift=dict(p50=float(np.median(np.abs(((u - np.arange(n)) + n / 2) % n - n / 2))),
                                                                                   max=float(np.abs(((u - np.arange(n)) + n / 2) % n - n / 2).max())))
    res['centre'] = dict(rms=float(np.sqrt(np.mean(lat ** 2))), max=float(np.abs(lat).max()), at=int(np.argmax(np.abs(lat))))
    for side, sg in (('left', 1), ('right', -1)):
        Ec = np.array(Tc[side])[:, :2]; Er = interp_rows(np.array(Tr[side])[:, :2], u)
        d = sg * ((Ec - Er) * nlc).sum(1)
        res[side] = dict(rms=float(np.sqrt(np.mean(d ** 2))), max=float(np.abs(d).max()), at=int(np.argmax(np.abs(d))),
                         over=runs(d, n, thr), d=d)
    Zc = np.array(Tc['profile']['z']); Zr = interp_rows(np.array(Tr['profile']['z']), u)
    dz = Zc - Zr
    res['height'] = dict(centre_rms=float(np.sqrt(np.mean(dz[:, 3] ** 2))), centre_max=float(np.abs(dz[:, 3]).max()),
                         all_rms=float(np.sqrt(np.mean(dz ** 2))), all_max=float(np.abs(dz).max()),
                         all_at=[int(v) for v in np.unravel_index(np.argmax(np.abs(dz)), dz.shape)],
                         z0=(Tc['z0_navd88'], Tr['z0_navd88']))
    hc = os.path.join(cand, 'heightfield.bin'); hr_ = os.path.join(ref, 'heightfield.bin')
    if os.path.exists(hc) and Tc['heightfield'] == Tr['heightfield']:
        a = np.fromfile(hc, np.float32); b = np.fromfile(hr_, np.float32)
        res['heightfield'] = dict(max=float(np.abs(a - b).max()), cells_over_1cm=int(np.sum(np.abs(a - b) > 0.01)), identical=bool(np.array_equal(a, b)))
    res['corners'] = [(a.get('turn') or a['name'], a['s'], b['s'], a.get('radius_m'), b.get('radius_m')) for a, b in zip(Tc['corners'], Tr['corners'])]
    if Gc and Gr:
        def line_world(T, G):
            C = np.array(T['center'])[:, :2]; nl, _ = normals(C); m = len(G['line']['offset_m'])
            st = np.arange(m) * G['s_grid_m'] / T['spacing_m']; i = np.round(st).astype(int) % len(C)
            return C[i] + np.array(G['line']['offset_m'])[:, None] * nl[i]
        Lc, Lr = line_world(Tc, Gc), line_world(Tr, Gr)
        _, dl = project(Lr, Lc)
        res['line'] = dict(rms=float(np.sqrt(np.mean(dl ** 2))), max=float(np.abs(dl).max()), at_grid=int(np.argmax(np.abs(dl))), d=dl)
        res['laps'] = {l['id']: (l['lap_time_s'], next((r['lap_time_s'] for r in Gr['laps'] if r['id'] == l['id']), None)) for l in Gc['laps']}
        res['line_identical'] = Gc['line']['offset_m'] == Gr['line']['offset_m']
    if Sc and Sr:
        def counts(S):
            c = {}
            for k, v in S.items():
                if k in ('far', 'notes', 'version', 'units', 'sources'): continue
                if isinstance(v, list): c[k] = len(v)
                elif isinstance(v, dict):
                    for kk in ('parts', 'strips', 'runs', 'pts'):
                        if kk in v: c[k] = len(v[kk]); break
                    if 'data' in v: c[k] = len(v['data']) // v.get('stride', 5)
            b = {}
            for x in S.get('barriers', []): b[x['kind']] = b.get(x['kind'], 0) + 1
            c.update({f'barriers.{k}': v for k, v in sorted(b.items())})
            l = {}
            for x in S.get('landmarks', []): l[x['kind']] = l.get(x['kind'], 0) + 1
            c.update({f'landmarks.{k}': v for k, v in sorted(l.items())})
            return c
        cc, cr = counts(Sc), counts(Sr)
        res['scenery'] = {k: (cc.get(k), cr.get(k)) for k in sorted(set(cc) | set(cr))}
    return res


def curvature(P, sigma):
    """signed curvature of closed polyline P (per metre), Gaussian-smoothed over sigma metres of arc"""
    from scipy.ndimage import gaussian_filter1d
    t = np.roll(P, -1, 0) - P; seg = np.linalg.norm(t, axis=1); h = np.arctan2(t[:, 1], t[:, 0])
    dh = np.angle(np.exp(1j * (h - np.roll(h, 1)))); k = dh / np.maximum((seg + np.roll(seg, 1)) / 2, 1e-6)
    return gaussian_filter1d(k, sigma / max(np.median(seg), 1e-6), mode='wrap')


def by_corner(cand, ref, win=60.0, sigma=7.5):
    """Per reference corner (s +-win m): centre and racing-line lateral offset (rms, worst) of the candidate from the
    reference, and the minimum radius of each centre and line (curvature smoothed over sigma m)."""
    Tc, Gc, _ = load(cand); Tr, Gr, _ = load(ref)
    Cc = np.array(Tc['center'])[:, :2]; Cr = np.array(Tr['center'])[:, :2]; nr = len(Cr)
    u, lat = project(Cr, Cc)
    def line_world(T, G):
        C = np.array(T['center'])[:, :2]; nl, _ = normals(C); m = len(G['line']['offset_m'])
        st = np.arange(m) * G['s_grid_m'] / T['spacing_m']; i = np.round(st).astype(int) % len(C)
        return C[i] + np.array(G['line']['offset_m'])[:, None] * nl[i]
    Lc, Lr = line_world(Tc, Gc), line_world(Tr, Gr)
    ul, dl = project(Lr, Lc)          # fractional index on the reference line (grid points)
    ul_st = ul * Gr['s_grid_m'] / Tr['spacing_m']
    kc, kr = curvature(Cc, sigma), curvature(Cr, sigma); klc, klr = curvature(Lc, sigma), curvature(Lr, sigma)
    rows = []
    for c in Tr['corners']:
        if not c.get('dir'): continue
        s0 = c['s'] / Tr['spacing_m']; w = win / Tr['spacing_m']
        inw = lambda x: np.abs(((x - s0) + nr / 2) % nr - nr / 2) <= w
        mc, ml = inw(u), inw(ul_st)
        mr = inw(np.arange(nr)); mlr = inw(np.arange(len(Lr)) * Gr['s_grid_m'] / Tr['spacing_m'])
        rows.append(dict(turn=c['turn'], s=c['s'],
                         centre_rms=float(np.sqrt(np.mean(lat[mc] ** 2))), centre_worst=float(np.abs(lat[mc]).max()),
                         line_rms=float(np.sqrt(np.mean(dl[ml] ** 2))), line_worst=float(np.abs(dl[ml]).max()),
                         R_centre=(float(1 / np.abs(kc[mc]).max()), float(1 / np.abs(kr[mr]).max())),
                         R_line=(float(1 / np.abs(klc[ml]).max()), float(1 / np.abs(klr[mlr]).max()))))
    whole = dict(centre_rms=float(np.sqrt(np.mean(lat ** 2))), centre_worst=float(np.abs(lat).max()),
                 line_rms=float(np.sqrt(np.mean(dl ** 2))), line_worst=float(np.abs(dl).max()),
                 length=(Tc['length_m'], Tr['length_m']))
    return rows, whole


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cand', required=True); ap.add_argument('--ref', default=None)
    ap.add_argument('--json', default=None); ap.add_argument('--runs', type=float, default=0.30)
    ap.add_argument('--by-corner', action='store_true', help='per-corner centre / line offsets and minimum radii')
    a = ap.parse_args()
    if a.by_corner:
        rows, whole = by_corner(a.cand, a.ref)
        print('turn    s      centre rms/worst   line rms/worst    R centre cand/ref    R line cand/ref')
        for r in rows:
            print(f"{r['turn']:5s} {r['s']:7.1f}   {r['centre_rms']:5.2f} / {r['centre_worst']:5.2f}    {r['line_rms']:5.2f} / {r['line_worst']:5.2f}"
                  f"    {r['R_centre'][0]:6.1f} / {r['R_centre'][1]:6.1f}    {r['R_line'][0]:6.1f} / {r['R_line'][1]:6.1f}")
        print('whole lap', json.dumps(whole))
        if a.json: json.dump(dict(rows=rows, whole=whole), open(a.json, 'w'), indent=1)
        return
    ref = a.ref or os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'tracks', json.load(open(os.path.join(a.cand, 'track.json')))['name'])
    r = compare(a.cand, ref, a.runs)
    show = {k: v for k, v in r.items()}
    for side in ('left', 'right'):
        show[side] = {k: v for k, v in r[side].items() if k != 'd'}
    if 'line' in r: show['line'] = {k: v for k, v in r['line'].items() if k != 'd'}
    print(json.dumps(show, indent=1, default=float))
    if a.json:
        json.dump(show, open(a.json, 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
