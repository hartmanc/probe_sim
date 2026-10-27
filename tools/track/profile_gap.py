"""Opt-in measured bridge gaps in road profiles; no prescribed elevations.

A short occluded road interval is reconstructed from the clean road at either
end, preserving measured height, longitudinal slope, cross-slope and crown.
The raw cloud is retained; class-2 deck returns in the interval are excluded
from the profile's lidar correction. Empty config leaves earlier builds intact.
"""
import numpy as np
from scipy.interpolate import CubicHermiteSpline
from scipy.spatial import cKDTree


def windows(C, repairs, enu):
    out = []
    n = len(C)
    ds = np.linalg.norm(np.roll(C, -1, axis=0) - C, axis=1)
    spacing = float(np.median(ds))
    for r in repairs or []:
        if not r.get('src') or not r.get('why'):
            raise ValueError('profile gap needs cited src and why')
        for key in ('half_m', 'fit_m', 'lateral_fade'):
            value = float(r.get(key, {'fit_m': 7, 'lateral_fade': 6}.get(key, 0)))
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f'profile gap {key} must be positive and finite')
        center = np.asarray(enu(*r['latlon']))
        k = int(cKDTree(C).query(center)[1])
        half = int(np.ceil(float(r['half_m']) / spacing))
        fit = int(np.ceil(float(r.get('fit_m', 7)) / spacing))
        if half < 2 or fit < 3 or 2 * (half + fit) >= n:
            raise ValueError('profile gap must have clean endpoint samples on a short interval')
        out.append(dict(name=r.get('name', 'bridge'), k=k, half=half, fit=fit,
                        ids=np.arange(k-half, k+half+1) % n,
                        spacing=spacing, lateral_fade=float(r.get('lateral_fade', 6))))
    return out


def mask(n, wins):
    m = np.zeros(n, dtype=bool)
    for w in wins:
        m[w['ids']] = True
    return m


def repair(prof, wins, log=print):
    out = prof.copy()
    n = len(out)
    for w in wins:
        k, h, f, ds = (w[a] for a in ('k', 'half', 'fit', 'spacing'))
        a, b = k-h, k+h
        # Endpoint slopes come entirely from the clean side of each endpoint.
        il = np.arange(a-f, a+1); ir = np.arange(b, b+f+1)
        sl = np.polyfit((il-a)*ds, out[il % n], 1)[0]
        sr = np.polyfit((ir-b)*ds, out[ir % n], 1)[0]
        spline = CubicHermiteSpline([0, (b-a)*ds], out[[a % n, b % n]], [sl, sr], axis=0)
        new = spline(np.arange(b-a+1)*ds)
        if not np.isfinite(new).all():
            raise ValueError('profile gap has non-finite clean endpoints')
        delta = np.abs(new-out[w['ids']]).max()
        out[w['ids']] = new
        log(f"profile gap {w['name']}: stations {a % n}..{b % n}, "
            f"measured endpoint heights/slopes, max repair {delta:.3f} m")
    return out


def heightfield(hf, box, dx, C, hl, hr, prof, wins):
    """Carry the repaired road plane under the bridge, fading laterally outside.

    Two metres at each clean end blend to the unchanged raw terrain. Across the
    road the quadratic cross-profile retains its measured banking and crown.
    """
    if not wins:
        return hf
    from geo import left_normals, FRACTIONS
    ny, nx = hf.shape
    x, y = np.meshgrid(box[0]+np.arange(nx)*dx, box[1]+np.arange(ny)*dx)
    xy = np.c_[x.ravel(), y.ravel()]
    _, nearest = cKDTree(C).query(xy)
    # Project onto either adjacent segment, then keep fractional station. A
    # nearest-station surface makes a staircase on grades between grid samples.
    choices = []
    for start in (nearest, (nearest-1) % len(C)):
        end = (start+1) % len(C)
        seg = C[end]-C[start]
        f = np.clip(((xy-C[start])*seg).sum(axis=1)/(seg*seg).sum(axis=1), 0, 1)
        foot = C[start]+f[:,None]*seg
        choices.append((start, f, foot, ((xy-foot)**2).sum(axis=1)))
    use_previous = choices[1][3] < choices[0][3]
    idx = np.where(use_previous, choices[1][0], choices[0][0])
    f = np.where(use_previous, choices[1][1], choices[0][1])
    foot = np.where(use_previous[:,None], choices[1][2], choices[0][2])
    nxt = (idx+1) % len(C)
    nl = left_normals(C)
    normal = (1-f[:,None])*nl[idx]+f[:,None]*nl[nxt]
    normal /= np.linalg.norm(normal,axis=1)[:,None]
    lateral = ((xy-foot)*normal).sum(axis=1)
    width_l = (1-f)*hl[idx]+f*hl[nxt]
    width_r = (1-f)*hr[idx]+f*hr[nxt]
    out = hf.astype(float).ravel().copy()
    for w in wins:
        u = ((idx+f-w['k']+len(C)/2) % len(C)-len(C)/2)*w['spacing']
        h = w['half']*w['spacing']
        along = np.clip((h-np.abs(u))/2, 0, 1)
        along = along*along*(3-2*along)
        half = np.where(lateral >= 0, width_l, width_r)
        across = np.clip((half+2+w['lateral_fade']-np.abs(lateral))/w['lateral_fade'], 0, 1)
        across = across*across*(3-2*across)
        take = (along > 0) & (across > 0)
        qi, qj, ff, ll = idx[take], nxt[take], f[take], lateral[take]
        coefficients = {}
        fr = np.asarray(FRACTIONS)
        for station in np.unique(np.r_[qi, qj]):
            lat = -fr*np.where(fr < 0, hl[station], hr[station])
            coefficients[station] = np.polyfit(lat, prof[station], 2)
        co0 = np.array([coefficients[k] for k in qi])
        co1 = np.array([coefficients[k] for k in qj])
        co = (1-ff[:,None])*co0+ff[:,None]*co1
        target = co[:,0]*ll**2+co[:,1]*ll+co[:,2]
        weight = along[take]*across[take]
        out[take] += weight*(target-out[take])
    return out.reshape(hf.shape).astype(hf.dtype)
