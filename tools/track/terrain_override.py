"""Terrain override (Sonoma round 14A, 23 Oct 2026; config key `terrain_override`, stage 1).

The owner's rule after the round-13 drive: every paved surface that touches the course (closed roads, paddock lots, the
islands between them) joins the racing surface with no step, no ridge and no trough, and the ground between those
surfaces lies on the same smooth surface; where the lidar disagrees, the lidar loses.

Inside a declared region polygon the heightfield is replaced by ONE smooth surface S, solved on the heightfield's own
2 m grid:
  - on the course and `edge_hold` m beyond each edge, S is the course itself: the profile inside the edges and, beyond
    them, the edge height continued with the edge third's cross-slope (C1 with the course: height and cross-slope match
    at the edge, so nothing creases there); out to `edge_band` m it is pulled to that continuation, fading;
  - elsewhere S minimises a thin-plate bending energy plus a robust (Tukey biweight, IRLS) misfit to the lidar ground
    (the bare-earth DEM the heightfield is built from). The bending weight is set by `smooth_m`, the shortest wavelength
    the surface keeps from the lidar: shorter bumps and hollows (old paving edges, trailers left in the ground class,
    vegetation, grading of another year) are not followed, and the biweight drops points more than ~4.7 robust sigmas
    off (kerb blocks, berms, parked vehicles);
  - with `deck_returns`, a bridge's deck (the low percentile of the lidar's class-17 returns per cell, its interior
    cells, held) is the road instead of the creek bed the DEM shows under it; the bed within `deck_reach` m of the deck
    carries no data, and beside the deck outside the polygon the surface is carried out flat and faded to the lidar
    over `deck_fade` m (Sonoma's Chute crosses the creek on a bridge);
  - outside the polygon S is held to the lidar, stiffening outward over `margin` m (no ditch or bank beyond the region
    is filled), and blends back to the raw heightfield by the margin's end.
The surface the car drives on inside the region is then this heightfield itself (scenery.json `terrain_override`, the
physics drops its 5 m shoulder blend there, src/physics/track.ts), and the paved parts are draped on it in stage 3.

Config (a list; absent = no change, every other track's heightfield byte for byte):
  terrain_override=[dict(name, latlon=[(lat, lon), ...] polygon, margin=15.0, ramp=1.5 (m inside the polygon over which
                         the physics goes from its shoulder blend to this surface; stage 3 / app), edge_hold=1.0,
                         edge_band=4.0, smooth_m=40.0, robust_sigma_min=0.03, margin_weight=100.0, deck_returns=False,
                         deck_weight=100.0, deck_reach=8.0, deck_fade=6.0, src, why)]
"""
import numpy as np


def polygon_xy(region, enu, track=None):
    """The region's polygon in ENU. follow_edge (Sonoma round 14B part 1b) [dict(side, i0, i1, off)]: the vertices i0..i1
    stand on the course edge + off m; on a built course (track: the C, left, right arrays) they are re-made there, one
    point every 2 m between the stations of vertices i0 and i1, so a moved edge carries the boundary with it (the owner's
    red moved T7a's left edge up to 3 m beyond the round-14A boundary). Absent, or without a track: the declared points."""
    P = np.array([enu(lat, lon) for lat, lon in region["latlon"]], float)
    fe = region.get("follow_edge")
    if not fe or track is None:
        return P
    C, L, R = (np.asarray(a, float)[:, :2] for a in track)
    n = len(C)
    from scipy.spatial import cKDTree
    kd = cKDTree(C)
    out, k = [], 0
    for e in sorted(fe, key=lambda e: e["i0"]):
        out.extend(P[k:e["i0"]])
        E = L if e["side"] == "left" else R
        u = E - C; u /= np.maximum(np.linalg.norm(u, axis=1, keepdims=True), 1e-9)
        s0, s1 = int(kd.query(P[e["i0"]])[1]), int(kd.query(P[e["i1"]])[1])
        span = (s1 - s0) % n if (s1 - s0) % n < n // 2 else -((s0 - s1) % n)
        ks = [(s0 + j) % n for j in (range(0, span + 1, 2) if span >= 0 else range(0, span - 1, -2))]
        if ks[-1] != s1 % n:
            ks.append(s1 % n)
        out.extend(E[ks] + float(e.get("off", 1.0)) * u[ks])
        k = e["i1"] + 1
    out.extend(P[k:])
    return np.array(out, float)


def inside_polygon(P, poly):
    """Even-odd point-in-polygon for points P (m, 2) against a closed polygon (k, 2)."""
    x, y = P[:, 0], P[:, 1]
    ins = np.zeros(len(P), bool)
    k = len(poly)
    for a in range(k):
        x1, y1 = poly[a]
        x2, y2 = poly[(a + 1) % k]
        c = ((y1 > y) != (y2 > y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        ins ^= c & (x < xc)
    return ins


def boundary_distance(P, poly):
    """Distance from each point to the polygon's boundary (m)."""
    d = np.full(len(P), np.inf)
    k = len(poly)
    for a in range(k):
        A, B = poly[a], poly[(a + 1) % k]
        AB = B - A
        L2 = max(float(AB @ AB), 1e-12)
        t = np.clip(((P - A) @ AB) / L2, 0, 1)
        Q = A + t[:, None] * AB
        d = np.minimum(d, np.hypot(*(P - Q).T))
    return d


def smooth01(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def course_surface(P, C, hl, hr, prof, fractions):
    """The course's surface at points P, as the physics evaluates it (src/physics/track.ts: nearest station, the closer
    of its two segments, the profile interpolated across and along), continued beyond the edges with each edge third's
    cross-slope. Returns (z, d_out): d_out = distance beyond the nearer edge (negative on the course)."""
    from scipy.spatial import cKDTree

    n = len(C)
    C = np.asarray(C, float)[:, :2]
    nxt = np.roll(C, -1, 0)
    seg = nxt - C
    sl = np.maximum(np.linalg.norm(seg, axis=1), 1e-9)
    tx, ty = seg[:, 0] / sl, seg[:, 1] / sl
    _, s = cKDTree(C).query(P)
    best = np.full(len(P), np.inf)
    SEG = np.zeros(len(P), int)
    T = np.zeros(len(P))
    LAT = np.zeros(len(P))
    for k in (0, 1):
        sg = (s - 1) % n if k == 0 else s
        dx, dy = P[:, 0] - C[sg, 0], P[:, 1] - C[sg, 1]
        t = (dx * tx[sg] + dy * ty[sg]) / sl[sg]
        tc = np.clip(t, 0, 1)
        px, py = dx - tc * sl[sg] * tx[sg], dy - tc * sl[sg] * ty[sg]
        d = px * px + py * py
        m = d < best
        best[m] = d[m]
        SEG[m] = sg[m]
        T[m] = tc[m]
        LAT[m] = (-dx * ty[sg] + dy * tx[sg])[m]
    j = (SEG + 1) % n
    half = np.where(LAT > 0, hl[SEG] + T * (hl[j] - hl[SEG]), hr[SEG] + T * (hr[j] - hr[SEG]))
    f = -LAT / half
    fr = np.asarray(fractions, float)
    fc = np.clip(f, fr[0], fr[-1])
    zrow = prof[SEG] * (1 - T)[:, None] + prof[j] * T[:, None]   # profile across, interpolated along
    z = np.array([np.interp(fc[q], fr, zrow[q]) for q in range(len(P))])
    # beyond an edge: the edge height plus the edge third's cross-slope times the distance beyond it
    d_out = (np.abs(f) - 1) * half
    third = half * (fr[-1] - fr[-2])
    sl_left = (zrow[:, 0] - zrow[:, 1]) / third      # dz per metre outward on the left
    sl_right = (zrow[:, -1] - zrow[:, -2]) / third
    beyond = d_out > 0
    z = np.where(beyond, z + np.where(f < 0, sl_left, sl_right) * d_out, z)
    return z, d_out


def _tps_matrix(ids, shape, h):
    """Discrete thin-plate energy sum(Sxx^2 + 2 Sxy^2 + Syy^2) * area over every stencil whose nodes are all in the
    domain, as a sparse quadratic form on the domain nodes (ids: (ny, nx) node -> unknown index, -1 outside)."""
    import scipy.sparse as sp

    ny, nx = shape
    rows, cols, vals = [], [], []
    r = 0

    def add(entries, w):
        nonlocal r
        for c, v in entries:
            rows.append(r)
            cols.append(c)
            vals.append(v * w)
        r += 1

    I, J = np.nonzero(ids >= 0)
    w = h / (h * h)    # sqrt(area) / h^2: (second difference / h^2)^2 * h^2
    for i, j in zip(I, J):
        c = ids[i, j]
        if 0 < j < nx - 1 and ids[i, j - 1] >= 0 and ids[i, j + 1] >= 0:
            add([(ids[i, j - 1], 1), (c, -2), (ids[i, j + 1], 1)], w)
        if 0 < i < ny - 1 and ids[i - 1, j] >= 0 and ids[i + 1, j] >= 0:
            add([(ids[i - 1, j], 1), (c, -2), (ids[i + 1, j], 1)], w)
        if i < ny - 1 and j < nx - 1 and ids[i + 1, j] >= 0 and ids[i, j + 1] >= 0 and ids[i + 1, j + 1] >= 0:
            add([(c, 1), (ids[i + 1, j + 1], 1), (ids[i + 1, j], -1), (ids[i, j + 1], -1)], w * np.sqrt(2))
    D = sp.csr_matrix((vals, (rows, cols)), shape=(r, int(ids.max()) + 1))
    return (D.T @ D).tocsr()


def deck_heights(P, dx, points, z0, raw_at, log=print):
    """Per node (P: node centres on the dx grid): the 20th percentile of the lidar's bridge-deck returns (class 17) in its cell,
    in the heightfield's frame (NAVD88 - z0, less the survey's ground-minus-DEM offset), NaN where a cell has fewer
    than 2. A paved road on a bridge (Sonoma's Chute over the creek) is its deck, not the creek bed the bare-earth DEM
    shows under it."""
    d = np.load(points)
    x0, y0 = P[:, 0].min() - dx, P[:, 1].min() - dx
    x1, y1 = P[:, 0].max() + dx, P[:, 1].max() + dx
    m = (d["x"] >= x0) & (d["x"] <= x1) & (d["y"] >= y0) & (d["y"] <= y1)
    X, Y, Z, Cl = d["x"][m].astype(float), d["y"][m].astype(float), d["z"][m].astype(float) - z0, d["c"][m]
    g = Cl == 2
    off = float(np.median(Z[g] - raw_at(X[g], Y[g]))) if g.sum() > 50 else 0.0
    out = np.full(len(P), np.nan)
    k = Cl == 17
    if not k.any():
        return out, off, 0
    gx0, gy0 = P[:, 0].min(), P[:, 1].min()
    nxw = int(round((P[:, 0].max() - gx0) / dx)) + 1
    key = np.round((Y[k] - gy0) / dx).astype(int) * nxw + np.round((X[k] - gx0) / dx).astype(int)
    pk = np.round((P[:, 1] - gy0) / dx).astype(int) * nxw + np.round((P[:, 0] - gx0) / dx).astype(int)
    zk = Z[k] - off
    order = np.argsort(key)
    key, zk = key[order], zk[order]
    uk, start, cnt = np.unique(key, return_index=True, return_counts=True)
    # a low percentile per cell: the deck surface, not its parapets and railings (returns classed as deck too)
    med = {int(u): float(np.percentile(zk[a:a + c], 20)) for u, a, c in zip(uk, start, cnt) if c >= 2}
    for i, q in enumerate(pk):
        if int(q) in med:
            out[i] = med[int(q)]
    return out, off, int(np.isfinite(out).sum())


def solve_region(hf, x0, y0, dx, region, enu, C, hl, hr, prof, fractions, log=print, points=None, z0=None, track=None):
    """The override of one region on heightfield hf (ny, nx; modified copy returned) and its report."""
    import scipy.sparse as sp
    from scipy.sparse.linalg import spsolve

    margin = float(region.get("margin", 15.0))
    band = float(region.get("edge_band", 4.0))
    Lw = float(region.get("smooth_m", 40.0))
    sig_min = float(region.get("robust_sigma_min", 0.03))
    poly = polygon_xy(region, enu, track)
    ny, nx = hf.shape
    # window of nodes around the polygon (+ margin + a stencil)
    pad = margin + 3 * dx
    j0 = max(int(np.floor((poly[:, 0].min() - pad - x0) / dx)), 0)
    j1 = min(int(np.ceil((poly[:, 0].max() + pad - x0) / dx)), nx - 1)
    i0 = max(int(np.floor((poly[:, 1].min() - pad - y0) / dx)), 0)
    i1 = min(int(np.ceil((poly[:, 1].max() + pad - y0) / dx)), ny - 1)
    JJ, II = np.meshgrid(np.arange(j0, j1 + 1), np.arange(i0, i1 + 1))
    P = np.c_[x0 + JJ.ravel() * dx, y0 + II.ravel() * dx]
    ins = inside_polygon(P, poly)
    dist = boundary_distance(P, poly)
    w_out = np.where(ins, 1.0, smooth01(1 - dist / margin))      # final blend weight S vs the raw heightfield
    dom = ins | (dist < margin + 2 * dx)                          # solve domain: the polygon and its margin
    raw = hf[i0:i1 + 1, j0:j1 + 1].astype(float).ravel()
    data = raw.copy()
    n_deck = 0
    nodata = np.zeros(len(P), bool)
    deck_use = np.zeros(len(P), bool)
    beside = np.zeros(len(P), bool)
    if region.get("deck_returns"):
        if not points or z0 is None:
            raise SystemExit(f"terrain override '{region['name']}': deck_returns needs the lidar point cache")
        from scipy.ndimage import map_coordinates

        def raw_at(X, Y):
            return map_coordinates(hf.astype(float), [(Y - y0) / dx, (X - x0) / dx], order=1, mode="nearest")
        deck, off, n_deck = deck_heights(P, dx, points, z0, raw_at, log=log)
        from scipy.ndimage import binary_erosion
        # the deck's own edge cells (its kerbs, parapets, half-covered cells) are left out: the surface runs on from
        # the deck's inside to its edges
        inner = binary_erosion(np.isfinite(deck).reshape(JJ.shape), iterations=1).ravel()
        use = inner & ins
        data[use] = deck[use]
        deck_use = use
        # round the deck (within `deck_reach` m of a deck return) the bare earth is the creek bed under the bridge, not the
        # road: no data there (the surface is carried across from the deck); further on (an approach on fill) the DEM is
        # the road again
        from scipy.ndimage import binary_dilation
        has = np.isfinite(deck).reshape(JJ.shape)
        near = binary_dilation(has, iterations=int(np.ceil(float(region.get("deck_reach", 8.0)) / dx))).ravel()
        nodata = ins & near & ~np.isfinite(deck)
        # beside the deck, outside the polygon, the creek bed is not the road either: no lidar pull there (the surface
        # runs on from the deck), and it fades to the lidar over `deck_fade` m, not the margin (the deck's embankment)
        fade = float(region.get("deck_fade", 6.0))
        beside = binary_dilation(has, iterations=int(np.ceil((margin + 2 * dx) / dx))).ravel() & ~ins
        dom &= ~beside       # not solved there: the deck's surface is carried out flat from the nearest node inside
        w_out = np.where(beside, smooth01(1 - dist / fade), w_out)
        log(f"terrain override '{region['name']}': {int(use.sum())} nodes take the bridge-deck returns (class 17) instead of the "
            f"bare earth (deck up to {np.nanmax(deck[use] - raw[use]) if use.any() else 0:.2f} m above it; ground-minus-DEM offset {off:+.3f} m)")
    zc, dout = course_surface(P, C, hl, hr, prof, fractions)
    # the course itself (inside the polygon) is held; its continuation beyond the edges is a strong pull fading out over
    # `edge_band` m, so the surface leaves the course's cross-slope gradually (C1 at the edge, no kink where it ends)
    hold = float(region.get("edge_hold", 1.0))
    fixed = dom & ins & (dout <= hold)
    cont = dom & ins & (dout > hold) & (dout <= band)
    w_cont = np.where(cont, float(region.get("edge_weight", 100.0)) * (1 - np.clip((dout - hold) / max(band - hold, 1e-6), 0, 1)) ** 2, 0.0)
    ids = np.full(P.shape[0], -1)
    ids[dom] = np.arange(dom.sum())
    shape = JJ.shape
    Q = _tps_matrix(ids.reshape(shape), shape, dx)
    lam = (Lw / (2 * np.pi)) ** 4                                 # cutoff wavelength smooth_m: lam k^4 = 1 at k = 2 pi / L
    nd = int(dom.sum())
    zd = data[dom]
    fx = fixed[dom]
    free = ~fx
    S = np.where(fx, zc[dom], zd)
    ins_d = ins[dom]
    nod_d = nodata[dom]
    deck_d = deck_use[dom]
    cont_d, wcont_d, zc_d = cont[dom], w_cont[dom], zc[dom]
    dist_d = np.where(ins, 0.0, dist)[dom]
    # outside the polygon (the margin) the surface keeps to the lidar: a non-robust misfit stiffening from 1 at the
    # polygon to `margin_weight` at the margin's edge, so the margin fills no ditch or bank beyond the region and the
    # surface's bend toward the lidar (a bank's toe beyond the region's edge) falls in the margin, not inside
    wts = np.ones(nd)
    w_margin = float(region.get("margin_weight", 100.0))
    # the deck returns are the road itself (a bridge deck is laid smooth): held like the margin, never rejected
    w_deck = float(region.get("deck_weight", 100.0))
    for it in range(8):
        wd = np.where(nod_d, 0.0, np.where(ins_d, wts, np.maximum(w_margin * smooth01(dist_d / margin), 1.0)))
        wd = np.where(deck_d, w_deck, wd)
        wd = np.where(cont_d, wcont_d, wd)
        A = lam * Q + sp.diags(np.where(free, wd * dx * dx, 0.0))   # misfit per unit area, like the bending energy
        b = np.where(free, wd * dx * dx * np.where(cont_d, zc_d, zd), 0.0)
        # eliminate the fixed nodes (the course and its continuation)
        Aff = A[free][:, free]
        Afx = A[free][:, fx]
        S[free] = spsolve(Aff.tocsc(), b[free] - Afx @ S[fx])
        res = zd - S
        r_free = res[free & ins_d & ~nod_d & ~cont_d]
        sig = max(1.4826 * np.median(np.abs(r_free - np.median(r_free))), sig_min)
        c = 4.685 * sig
        u = res / c
        wts = np.where(np.abs(u) < 1, (1 - u * u) ** 2, 0.0)
    out = hf.copy()
    Sfull = raw.copy()
    Sfull[dom] = S
    ext = beside & (w_out > 0)
    if ext.any():
        from scipy.spatial import cKDTree
        _, nn = cKDTree(P[dom & ins]).query(P[ext])
        Sfull[ext] = Sfull[np.nonzero(dom & ins)[0][nn]]
    new = w_out * Sfull + (1 - w_out) * raw
    out[i0:i1 + 1, j0:j1 + 1] = new.reshape(shape).astype(hf.dtype)
    dz = (new - raw)[ins]
    rep = {"name": region["name"], "nodes_inside": int(ins.sum()), "deck_nodes": int(n_deck), "nodes_solved": nd, "nodes_on_course_band": int(fixed.sum()),
           "smooth_m": Lw, "robust_sigma_m": round(float(sig), 3), "rejected_share": round(float((wts[free & ins_d & ~nod_d & ~cont_d] == 0).mean()), 3),
           "change_inside_m": {"p50_abs": round(float(np.median(np.abs(dz))), 3), "p95_abs": round(float(np.percentile(np.abs(dz), 95)), 3),
                               "max_raise": round(float(dz.max()), 3), "max_cut": round(float(-dz.min()), 3)}}
    log(f"terrain override '{region['name']}': {rep['nodes_inside']} nodes inside ({rep['nodes_on_course_band']} held on the course and "
        f"its {hold:g} m continuation, pulled to it out to {band:g} m), smooth {Lw:g} m, robust sigma {sig:.3f} m, {rep['rejected_share'] * 100:.0f} % of the lidar "
        f"nodes rejected; change inside: p50 {rep['change_inside_m']['p50_abs']:.3f} m, p95 {rep['change_inside_m']['p95_abs']:.3f} m, "
        f"raised up to {rep['change_inside_m']['max_raise']:.2f} m, cut up to {rep['change_inside_m']['max_cut']:.2f} m")
    return out, rep


def apply(hf, box, dx, regions, enu, C, hl, hr, prof, fractions, log=print, points=None, z0=None, track=None):
    """Every region of config `terrain_override` on the heightfield (a modified copy) and the reports. No regions: hf
    itself, untouched."""
    if not regions:
        return hf, []
    reps = []
    for r in regions:
        hf, rep = solve_region(hf, box[0], box[1], dx, r, enu, C, hl, hr, prof, fractions, log=log, points=points, z0=z0, track=track)
        reps.append(rep)
    return hf, reps


def scenery_regions(regions, enu, track=None):
    """scenery.json `terrain_override` (read by the physics, the app and the gates): the polygons in ENU and their ramp."""
    return {"regions": [{"name": r["name"], "ramp": float(r.get("ramp", 5.0)),
                         "poly": [[round(float(x), 2), round(float(y), 2)] for x, y in polygon_xy(r, enu, track)]} for r in regions]}


def weight(P, sc_regions):
    """The physics' weight of the override surface at points P (1 deep inside a region, 0 outside it, smoothstep over
    the region's `ramp` inside its boundary); the max over the regions. Mirrors src/physics/track.ts."""
    P = np.atleast_2d(np.asarray(P, float))[:, :2]
    w = np.zeros(len(P))
    for r in (sc_regions or {}).get("regions", []):
        poly = np.array(r["poly"], float)
        ins = inside_polygon(P, poly)
        if not ins.any():
            continue
        d = boundary_distance(P[ins], poly)
        w[ins] = np.maximum(w[ins], smooth01(d / max(r["ramp"], 1e-6)))
    return w


def drape_parts(SC, T, hf, sc_regions, log=print):
    """Stage 3: the paved zones and pit-lane parts inside an override region lie on its surface. Every profile point of a
    part (the 7 fractions across each station, as the physics places them) takes w * heightfield + (1 - w) * its built
    height, w the physics' override weight there (1 deep inside, 0 outside), so a zone, the ground beside it and the
    course are one surface in the region and the zone keeps its built profile outside it. Returns the points moved."""
    H = T["heightfield"]
    ny, nx = H["ny"], H["nx"]

    def ground(P):
        from scipy.ndimage import map_coordinates
        return map_coordinates(hf, [(P[:, 1] - H["y0"]) / H["dx"], (P[:, 0] - H["x0"]) / H["dx"]], order=1, mode="nearest")

    moved, dmax = 0, 0.0
    for key in ("pit_lane", "paved_zones"):
        blk = SC.get(key)
        if not blk:
            continue
        fr = np.asarray(blk["fractions"], float)
        for p in blk["parts"]:
            Cc = np.asarray(p["center"], float)[:, :2]
            if (weight(Cc, sc_regions) > 0).any():
                # a part in the region loses its zero-length stations (repeated centres where both edges were clamped onto
                # one track station): the physics reads a zero-length segment's lateral as 0, i.e. every point whose
                # nearest station it is as paved at the part's centre height (Sonoma's T7 inside runoff start: a phantom
                # paved plateau ~0.5 m above the ground over the island's nose, round 14A)
                keep = [0]
                for j in range(1, len(Cc)):
                    if np.hypot(*(Cc[j] - Cc[keep[-1]])) >= 0.05:
                        keep.append(j)
                if len(keep) < len(Cc):
                    log(f"terrain override: part '{p.get('turn')}': {len(Cc) - len(keep)} zero-length stations removed")
                    for k_ in ("center", "left", "right", "profile_z", "gap_left", "gap_right"):
                        if k_ in p and isinstance(p[k_], list) and len(p[k_]) == len(Cc):
                            p[k_] = [p[k_][j] for j in keep]
                    p["n"] = len(keep)
                    Cc = Cc[keep]
            Lc = np.asarray(p["left"], float)[:, :2]
            Rc = np.asarray(p["right"], float)[:, :2]
            pts = np.array([[Cc[j] + (Lc[j] - Cc[j]) * (-f) if f < 0 else Cc[j] + (Rc[j] - Cc[j]) * f for f in fr] for j in range(len(Cc))])
            flat = pts.reshape(-1, 2)
            w = weight(flat, sc_regions).reshape(len(Cc), len(fr))
            if not (w > 0).any():
                continue
            z0 = np.asarray(p["profile_z"], float)
            zn = w * ground(flat).reshape(z0.shape) + (1 - w) * z0
            moved += int((w > 0).sum())
            dmax = max(dmax, float(np.abs(zn - z0).max()))
            p["profile_z"] = [[round(float(v), 3) for v in r] for r in zn]
            ci = len(fr) // 2
            for k_, col in (("center", ci), ("left", 0), ("right", len(fr) - 1)):
                p[k_] = [[a[0], a[1], round(float(z), 3)] for a, z in zip(p[k_], zn[:, col])]
    log(f"terrain override: {moved} paved-part profile points draped on the override surface (largest change {dmax:.3f} m)")
    return moved
