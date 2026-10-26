"""Opt-in bank-scaling rule for a reconstructed corner (config `profile_bank`; Mid-Ohio T4, round 4, 26 Oct 2026).

Where a survey predates a documented reconstruction that changed a corner's banking (Mid-Ohio T4: the 2019 lidar,
the operator's Oct-Nov 2024 rebuild "banking reduced from 4 to 2 degrees by removing 520 feet of track surface"),
the measured cross-section is rotated about its INSIDE edge so that the measured edge-to-edge (chord) bank toward
the inside is scaled by `factor` over a declared interval:

    z'(l) = z(l) - (1 - factor) * w(s) * max(g, 0) * d(l)

g is the chord slope from the inside edge up to the outside edge (m/m; > 0: banked toward the inside), d(l) the
lateral distance from the inside edge (0 at the inside edge, W at the outside edge), w(s) the along-track weight:
1 over the core (`length_m` centred on the measured bank peak), a smoothstep from 0 over `approach_m` before it
(`exit_m` after it, default 0). The crown (the cross-section's shape about the chord) is kept; the inside edge's
heights are kept exactly; only a bank toward the inside is scaled (an adverse slope is left as measured), so the
rule is continuous wherever the measured bank crosses zero.

The bank peak is measured, not declared: the station of the largest chord bank toward the inside (5-station mean)
within `search_m` of the projection of `anchor_latlon`. Every number in the rule is in the config with its source;
nothing here is a prescribed elevation. The heightfield carries the same change under the road, holds the outside
edge's change for `shoulder_m` beyond it and fades it out over `lateral_fade` m (the inside is unchanged), only at
cells whose foot on the centre lies inside the rule's interval. Absent (every other track): nothing runs.

    config: profile_bank=[{name, anchor_latlon, search_m (40), inside 'left'|'right', length_m, approach_m,
                           exit_m (0), factor (0.5), shoulder_m (2), lateral_fade (6), src, why, assumptions [...]}]
"""
import numpy as np
from scipy.spatial import cKDTree

STEP_MAX = 0.02   # m: largest change of the rule's delta between neighbouring stations (a step means a missing blend)


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def lateral(hl, hr, fractions):
    fr = np.asarray(fractions, float)
    return np.where(fr[None, :] < 0, -fr[None, :] * hl[:, None], -fr[None, :] * hr[:, None])   # + left


def rules(C, prof, hl, hr, cfg_rules, enu, fractions):
    """Resolve each config rule on this centre: peak station, interval, weights. Returns a list of dicts."""
    n = len(C)
    ds = np.linalg.norm(np.roll(C, -1, axis=0) - C, axis=1)
    sp = float(np.median(ds))
    W = hl + hr
    out = []
    for r in cfg_rules or []:
        for key in ('src', 'why', 'inside', 'length_m', 'approach_m', 'anchor_latlon'):
            if r.get(key) in (None, ''):
                raise ValueError(f"profile_bank {r.get('name')!r}: needs {key}")
        if r['inside'] not in ('left', 'right'):
            raise ValueError(f"profile_bank {r.get('name')!r}: inside must be left | right")
        factor = float(r.get('factor', 0.5))
        if not 0.0 <= factor <= 1.0:
            raise ValueError(f"profile_bank {r.get('name')!r}: factor must lie in [0, 1]")
        i_in, i_out = (len(fractions) - 1, 0) if r['inside'] == 'right' else (0, len(fractions) - 1)
        g = (prof[:, i_out] - prof[:, i_in]) / W          # chord slope up from the inside edge to the outside edge
        g5 = np.convolve(np.r_[g[-2:], g, g[:2]], np.ones(5) / 5, mode='valid')
        k0 = int(cKDTree(C).query(np.asarray(enu(*r['anchor_latlon'])))[1])
        m = int(np.ceil(float(r.get('search_m', 40)) / sp))
        cand = np.arange(k0 - m, k0 + m + 1) % n
        peak = int(cand[np.argmax(g5[cand])])
        half = float(r['length_m']) / 2
        app, ext = float(r['approach_m']), float(r.get('exit_m', 0.0))
        u = ((np.arange(n) - peak + n / 2) % n - n / 2) * sp      # signed metres from the peak along the lap
        w = np.where(np.abs(u) <= half, 1.0, 0.0)
        before = (u < -half) & (u >= -half - app)
        w[before] = _smooth((u[before] + half + app) / app)
        if ext > 0:
            after = (u > half) & (u <= half + ext)
            w[after] = _smooth((half + ext - u[after]) / ext)
        lo, hi = -half - app, half + ext
        ids = np.nonzero((u >= lo) & (u <= hi))[0]
        out.append(dict(name=r.get('name', 'bank rule'), inside=r['inside'], factor=factor, peak=peak, sp=sp, w=w,
                        g=g, i_in=i_in, i_out=i_out, u=u, lo_m=lo, hi_m=hi,
                        first=int(ids[np.argmin(u[ids])]), last=int(ids[np.argmax(u[ids])]),
                        core=(int((peak - round(half / sp)) % n), int((peak + round(half / sp)) % n)),
                        shoulder_m=float(r.get('shoulder_m', 2.0)), lateral_fade=float(r.get('lateral_fade', 6.0))))
    return out


def apply_profile(prof, hl, hr, resolved, fractions, log=print):
    """The scaled profile and the per-station delta at every profile column (n x 7)."""
    lat = lateral(hl, hr, fractions)
    delta = np.zeros_like(prof)
    reports = []
    for q in resolved:
        l_in = lat[:, q['i_in']]
        d = (lat - l_in[:, None]) * (1.0 if q['inside'] == 'right' else -1.0)   # 0 at the inside edge, W outside
        dq = -(1 - q['factor']) * q['w'][:, None] * np.maximum(q['g'], 0.0)[:, None] * d
        delta += dq
        step = float(np.abs(np.diff(np.r_[dq, dq[:1]], axis=0)).max())
        ch = np.nonzero(np.abs(dq).max(1) > 1e-6)[0]
        rad = np.degrees(np.arctan(q['g']))
        new_g = q['g'] - (1 - q['factor']) * q['w'] * np.maximum(q['g'], 0)
        rep = dict(name=q['name'], peak_station=q['peak'], peak_bank_deg=round(float(rad[q['peak']]), 2),
                   peak_bank_after_deg=round(float(np.degrees(np.arctan(new_g[q['peak']]))), 2),
                   interval_stations=[q['first'], q['last']], core_stations=list(q['core']),
                   interval_m=[round(q['lo_m'], 1), round(q['hi_m'], 1)],
                   changed_stations=[int(ch.min()), int(ch.max())] if len(ch) else None, n_changed=int(len(ch)),
                   outside_edge_max_drop_m=round(float(-dq[:, q['i_out']].min()), 3),
                   inside_edge_max_change_m=round(float(np.abs(dq[:, q['i_in']]).max()), 6),
                   centre_max_drop_m=round(float(-dq[:, len(fractions) // 2].min()), 3),
                   max_station_step_m=round(step, 4))
        if step > STEP_MAX:
            raise ValueError(f"profile_bank {q['name']}: the change steps {step:.3f} m between neighbouring stations "
                             f"(limit {STEP_MAX} m): the interval ends where the inside bank is not zero; declare exit_m")
        log(f"profile bank {q['name']}: peak s {q['peak']} ({rep['peak_bank_deg']} deg -> {rep['peak_bank_after_deg']} deg), "
            f"interval stations {q['first']}..{q['last']} (core {q['core'][0]}..{q['core'][1]}), changed {rep['changed_stations']}, "
            f"outside edge down {rep['outside_edge_max_drop_m']} m max, inside edge held ({rep['inside_edge_max_change_m']} m), "
            f"largest station step {rep['max_station_step_m']} m")
        reports.append(rep)
    return prof + delta, delta, reports


def heightfield(hf, box, dx, C, hl, hr, delta, resolved, fractions):
    """Carry the profile delta into the heightfield: under the road by fractional station and lateral position
    (linear between the profile columns), held `shoulder_m` beyond the outside edge then faded over `lateral_fade`;
    unchanged beyond the inside edge and at every cell whose foot station lies outside a rule's interval."""
    if not resolved:
        return hf, {}
    from geo import left_normals
    n = len(C)
    ny, nx = hf.shape
    out = hf.astype(float).ravel().copy()
    lat_cols = lateral(hl, hr, fractions)
    rep = {}
    for q in resolved:
        ids = np.nonzero(np.abs(delta).max(1) > 0)[0]
        if not len(ids):
            continue
        reach = float(np.max(np.maximum(hl, hr)[ids])) + q['shoulder_m'] + q['lateral_fade'] + 2 * dx
        x, y = np.meshgrid(box[0] + np.arange(nx) * dx, box[1] + np.arange(ny) * dx)
        xy = np.c_[x.ravel(), y.ravel()]
        near = cKDTree(C[ids]).query(xy, distance_upper_bound=reach)[0]
        cells = np.nonzero(np.isfinite(near))[0]
        P = xy[cells]
        _, nearest = cKDTree(C).query(P)
        choices = []
        for start in (nearest, (nearest - 1) % n):
            end = (start + 1) % n
            seg = C[end] - C[start]
            f = np.clip(((P - C[start]) * seg).sum(1) / (seg * seg).sum(1), 0, 1)
            foot = C[start] + f[:, None] * seg
            choices.append((start, f, foot, ((P - foot) ** 2).sum(1)))
        prev = choices[1][3] < choices[0][3]
        i0 = np.where(prev, choices[1][0], choices[0][0]); f = np.where(prev, choices[1][1], choices[0][1])
        foot = np.where(prev[:, None], choices[1][2], choices[0][2])
        i1 = (i0 + 1) % n
        nl = left_normals(C)
        nrm = (1 - f)[:, None] * nl[i0] + f[:, None] * nl[i1]
        nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        l = ((P - foot) * nrm).sum(1)
        # the delta across the section is linear in l between the edges (z' - z = -k * d(l), d linear in l)
        def at(k):
            lin, lout = lat_cols[k, q['i_in']], lat_cols[k, q['i_out']]
            din, dout = delta[k, q['i_in']], delta[k, q['i_out']]
            return lin, lout, din, dout
        a0, b0, c0, e0 = at(i0); a1, b1, c1, e1 = at(i1)
        lin = (1 - f) * a0 + f * a1; lout = (1 - f) * b0 + f * b1
        din = (1 - f) * c0 + f * c1; dout = (1 - f) * e0 + f * e1
        span = lout - lin
        t = (l - lin) / np.where(np.abs(span) > 1e-9, span, 1e-9)          # 0 inside edge, 1 outside edge
        beyond = np.abs(l - lin) - np.abs(span)                             # m beyond the outside edge (t > 1)
        fade = 1 - _smooth((beyond - q['shoulder_m']) / q['lateral_fade'])
        dz = np.where(t <= 0, din, np.where(t <= 1, din + t * (dout - din), dout * fade))
        inside_interval = q['w'][i0] + q['w'][i1] > 0
        dz = np.where(inside_interval, dz, 0.0)
        take = np.abs(dz) > 0
        out[cells[take]] += dz[take]
        st = np.where(f[take] < 0.5, i0[take], i1[take])
        rep[q['name']] = dict(cells=int(take.sum()), max_drop_m=round(float(-dz.min()), 3),
                              foot_stations=[int(st.min()), int(st.max())] if take.any() else None,
                              interval_stations=[q['first'], q['last']])
    res = out.reshape(hf.shape).astype(hf.dtype)
    # the cells whose stored value changed (a change below the float32 step of a cell's height does not store)
    return res, dict(rep, total_cells=int(np.count_nonzero(res != hf)))
