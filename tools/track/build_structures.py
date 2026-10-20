"""Parametric structures for scenery.json (the buildings round, 21 Oct 2026): reads a track config's top-level
`structures` section and writes scenery.json `structures`, drawn by the app's structure kit (src/app/structures.ts).
Called by build_scenery.main at the end of stage 3, before scenery.json is written; a config without the section leaves
the package byte-identical (Laguna).

Config (every entry carries `src`, the evidence; geometry from OSM where mapped, else lat/lon measured on the 2026
captures with compare/capwin.py; heights by tools/track/compare/HEIGHTS.md or the lidar, cited in `h_src`):

    structures=dict(
        suppress_osm=[way id, ...],     # OSM building boxes a structure replaces (each must match; logged)
        items=[
            dict(type='grandstand', front=[(lat, lon), (lat, lon)], base=..., rows=..., ...),   # see the kit
            dict(type='garage' | 'block' | 'fuel', osm=way id | rect=dict(c=(lat, lon), heading_deg, l, w), ...),
            dict(type='mast', at=[(lat, lon, h), ...], heads=[3, 2]),   # lamps face the nearest track point
            dict(type='boards', side='left'|'right', s0, s1, lat=(a, b), h, colors, panel),   # on the barrier there
            dict(type='paint', runs=[dict(a=(lat, lon), b=(lat, lon), pitch, depth, w)], color),   # pit-box lines
            dict(type='terrace_dress', terrace=name, ...),            # passed through
            dict(type='scoring_tower', at=(lat, lon), heading_deg, w, d, h, color, head=dict(h, w, d, color)?, plinth=dict(w, h, color)?)
            dict(type='fence', pts=[(lat, lon), ...], h),
        ])

Sides: `doors.side` / `windows.side` may be 'track' or 'away' (the long side facing / turned from the nearest track
point); the builder resolves them to +1 / -1 of the kit's frame. Solid structures get `collide` outlines (the physics
treats them like buildings). Trees inside a structure's outline (+1 m) and lidar-only building boxes whose centre falls
in one are dropped (logged).
"""
import math

import numpy as np

import geo as bl

log = bl.log


def rnd(v, d=2):
    return float(round(float(v), d))


def _enu(ll):
    x, y = bl.enu(float(ll[0]), float(ll[1]))
    return np.array([float(x), float(y)])


def _rect_from_osm(osm, wid):
    from shapely.geometry import Polygon
    w = next((w for w in osm.ways if w["id"] == str(wid)), None)
    if w is None:
        raise SystemExit(f"structures: OSM way {wid} not found")
    r = Polygon(w["xy"]).minimum_rotated_rectangle
    P = np.array(r.exterior.coords)[:4]
    e1, e2 = P[1] - P[0], P[2] - P[1]
    ax = e1 if np.linalg.norm(e1) >= np.linalg.norm(e2) else e2
    return P.mean(0), math.atan2(ax[1], ax[0]), float(max(np.linalg.norm(e1), np.linalg.norm(e2))), \
        float(min(np.linalg.norm(e1), np.linalg.norm(e2)))


def _rect(osm, it):
    if it.get("osm"):
        c, hd, l, w = _rect_from_osm(osm, it["osm"])
    else:
        r = it["rect"]
        c, hd, l, w = _enu(r["c"]), math.radians(r["heading_deg"]), float(r["l"]), float(r["w"])
    return c, hd, it.get("l", l), it.get("w", w)


def _corners(c, hd, l, w, pad=0.0):
    u = np.array([math.cos(hd), math.sin(hd)]); n = np.array([-u[1], u[0]])
    a, b = l / 2 + pad, w / 2 + pad
    return np.array([c - u * a - n * b, c + u * a - n * b, c + u * a + n * b, c - u * a + n * b])


def _toward_track(trk, c, hd):
    """+1 when the nearest track point lies on the frame's +d (left of heading) side, else -1."""
    i, _, _ = trk.project(np.asarray(c)[None])
    v = trk.C[i[0], :2] - c
    n = np.array([-math.sin(hd), math.cos(hd)])
    return 1 if float(v @ n) > 0 else -1


def _side(spec, s_track):
    s = spec.get("side", 0)
    if s == "track":
        return s_track
    if s == "away":
        return -s_track
    return int(s)


def _ground(trk, P):
    P = np.atleast_2d(P)
    return float(np.min(trk.ground(P[:, 0], P[:, 1])))


def _poly(P):
    return [[rnd(x, 2), rnd(y, 2)] for x, y in P]


def grandstand(trk, it):
    a, b = _enu(it["front"][0]), _enu(it["front"][1])
    L = float(np.linalg.norm(b - a)); ut = (b - a) / L
    n = np.array([-ut[1], ut[0]])
    mid = (a + b) / 2
    i, _, _ = trk.project(mid[None])
    if float((trk.C[i[0], :2] - mid) @ n) > 0:   # dir points away from the track
        n = -n
    z = float(np.median(trk.ground(*(a[None] + (b - a)[None] * np.linspace(0, 1, 15)[:, None]).T)))
    out = {k: v for k, v in it.items() if k not in ("front", "h_src", "replaces")}
    out.update({"a": [rnd(a[0]), rnd(a[1])], "b": [rnd(b[0]), rnd(b[1])], "dir": [rnd(n[0], 5), rnd(n[1], 5)], "z": rnd(z)})
    su = it.get("suites")
    dback = max(su["d1"] + su.get("back", {}).get("depth", 0), 0) if su else it["base"]["depth"] + it["rows"]["n"] * it["rows"]["depth"]
    htop = max(su["roof"][:3]) if su else it["rows"]["z0"] + it["rows"]["n"] * it["rows"]["rise"]
    fp = [a, b, b + n * dback, a + n * dback]
    out["collide"] = [{"footprint": _poly(fp), "z": rnd(z), "h": rnd(htop, 1)}]
    log(f"structure grandstand '{it['name']}': front {L:.1f} m, {it['rows']['n']} rows, depth {dback:.1f} m, top {htop:.1f} m, "
        f"z {z:.2f}")
    return out, fp


def boxlike(trk, osm, it):
    c, hd, l, w = _rect(osm, it)
    fp = _corners(c, hd, l, w)
    z = _ground(trk, fp)
    st = _toward_track(trk, c, hd)
    out = {k: v for k, v in it.items() if k not in ("osm", "rect", "h_src", "pylon_at")}
    out.update({"c": [rnd(c[0]), rnd(c[1])], "heading": rnd(hd, 5), "l": rnd(l), "w": rnd(w), "z": rnd(z)})
    for key in ("doors", "windows"):
        if key in it:
            out[key] = dict(it[key], side=_side(it[key], st))
    if it["type"] == "garage" and it.get("mono") is not None:
        out["mono"] = _side({"side": it["mono"]}, st)
    if it["type"] == "fuel" and it.get("pylon_at"):
        p = _enu(it["pylon_at"]) - c
        u = np.array([math.cos(hd), math.sin(hd)]); n = np.array([-u[1], u[0]])
        out["pylon"] = dict(it["pylon"], at=[rnd(p @ u), rnd(p @ n)])
    h = {"garage": lambda: max(it["eave"], it["ridge"]) + it.get("parapet", 0), "block": lambda: it["h"] + it.get("parapet", 0),
         "fuel": lambda: it["h"] + it["fascia"] + it.get("hip", 0)}[it["type"]]()
    out["collide"] = [{"footprint": _poly(fp), "z": rnd(z), "h": rnd(h, 1)}] if it["type"] != "fuel" else \
        [{"footprint": _poly(_corners(c + np.array([math.cos(hd), math.sin(hd)]) * t, hd, 0.4, 0.4)), "z": rnd(z), "h": rnd(it["h"], 1)}
         for t in np.linspace(-l / 2 + 1, l / 2 - 1, max(1, it["posts"]))]
    log(f"structure {it['type']} '{it['name']}': {l:.1f} x {w:.1f} m, heading {math.degrees(hd):.1f} deg, top {h:.1f} m, "
        f"z {z:.2f}, faces the track on side {st:+d}")
    return out, fp


def masts(trk, it):
    at = []
    for ll in it["at"]:
        p = _enu(ll[:2])
        i, _, _ = trk.project(p[None])
        v = trk.C[i[0], :2] - p
        at.append([rnd(p[0]), rnd(p[1]), rnd(_ground(trk, p)), rnd(math.atan2(v[1], v[0]), 4)])
    hs = sorted({float(ll[2]) for ll in it["at"]})
    out = []
    # one descriptor per height (the kit draws one height per entry)
    for h in hs:
        pts = [a for a, ll in zip(at, it["at"]) if float(ll[2]) == h]
        out.append({k: v for k, v in it.items() if k not in ("at", "h_src")} | {"at": pts, "h": rnd(h, 1)})
    log(f"structure masts '{it.get('name', '')}': {len(at)} masts, heights {', '.join(f'{h:.1f}' for h in hs)} m")
    return out


def boards(trk, it, barriers):
    """Panels on the barrier that runs on `side` within lateral `lat` of the track between stations s0..s1."""
    sp = trk.sp
    lo, hi = it["lat"]
    sgn = 1 if it["side"] == "left" else -1
    best = None
    for b in barriers:
        if b["kind"] not in ("concrete", "pitwall"):
            continue
        P = np.array(b["pts"], float)
        i, lat, _ = trk.project(P[:, :2])
        s = i * sp
        L = trk.n * sp
        ins = ((s - it["s0"]) % L) <= ((it["s1"] - it["s0"]) % L)
        ok = ins & (sgn * lat >= lo) & (sgn * lat <= hi)
        if ok.sum() >= 2 and (best is None or ok.sum() > best[1].sum()):
            best = (b, ok, P)
    if best is None:
        raise SystemExit(f"structures boards '{it.get('name', '')}': no barrier on the {it['side']} between s {it['s0']} and {it['s1']}")
    b, ok, P = best
    idx = np.nonzero(ok)[0]
    # longest contiguous run
    runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
    run = max(runs, key=len)
    pts = [[rnd(x), rnd(y), rnd(z)] for x, y, z in P[run]]
    out = {k: v for k, v in it.items() if k not in ("side", "s0", "s1", "lat", "h_src")}
    out.update({"pts": pts, "z0": rnd(b["h"])})
    log(f"structure boards '{it.get('name', '')}': {len(pts)} points on barrier ({b['kind']}, {b['h']} m, src {b.get('src', '')[:50]}...)")
    return out


def paint(trk, it):
    rects, zs = [], []
    for r in it["runs"]:
        a, b = _enu(r["a"]), _enu(r["b"])
        L = float(np.linalg.norm(b - a)); ut = (b - a) / L
        n = np.array([-ut[1], ut[0]])
        mid = (a + b) / 2
        i, _, _ = trk.project(mid[None])
        if float((trk.C[i[0], :2] - mid) @ n) > 0:
            n = -n   # boxes extend away from the track
        k = max(1, int(round(L / r["pitch"])))
        hd_l = math.atan2(n[1], n[0])
        for j in range(k + 1):
            p = a + ut * (L * j / k) + n * (r["depth"] / 2)
            rects.append([rnd(p[0]), rnd(p[1]), rnd(hd_l, 4), rnd(r["depth"]), rnd(r["w"], 3)])
        # the box front line along the run
        p = (a + b) / 2
        rects.append([rnd(p[0]), rnd(p[1]), rnd(math.atan2(ut[1], ut[0]), 4), rnd(L + r["w"]), rnd(r["w"], 3)])
    for rc in rects:
        zs.append(rnd(_ground(trk, np.array(rc[:2]))))
    out = {k: v for k, v in it.items() if k not in ("runs", "h_src")}
    out.update({"rects": rects, "z": zs})
    log(f"structure paint '{it.get('name', '')}': {len(rects)} rectangles in {len(it['runs'])} runs")
    return out


def apply(trk, osm, sc, cfg):
    """Add `structures` to the scenery dict `sc` (before it is written) and drop what they replace."""
    from shapely.geometry import Point, Polygon
    sup = [str(x) for x in cfg.get("suppress_osm", [])]
    for wid in sup:
        w = next((w for w in osm.ways if w["id"] == wid), None)
        if w is None:
            raise SystemExit(f"structures.suppress_osm: OSM way {wid} not found")
        xy = w["xy"][:-1] if np.linalg.norm(w["xy"][0] - w["xy"][-1]) < 0.5 else w["xy"]
        key = [[rnd(x, 1), rnd(y, 1)] for x, y in xy]
        hit = [k for k, b in enumerate(sc["buildings"]) if b["src"] == "osm" and b["footprint"] == key]
        if not hit:
            raise SystemExit(f"structures.suppress_osm: OSM building {wid} is not among the scenery's buildings")
        for k in reversed(hit):
            b = sc["buildings"].pop(k)
            log(f"structures: OSM building {wid} ({b['name'] or 'unnamed'}, {b['h']} m box) suppressed, replaced by a structure")
    out, outlines = [], []
    for it in cfg.get("items", []):
        if not it.get("src"):
            raise SystemExit(f"structures: {it.get('type')} '{it.get('name', '')}' has no src (evidence)")
        t = it["type"]
        if t == "grandstand":
            o, fp = grandstand(trk, it); out.append(o); outlines.append(fp)
        elif t in ("garage", "block", "fuel"):
            o, fp = boxlike(trk, osm, it); out.append(o); outlines.append(fp)
        elif t == "mast":
            out += masts(trk, it)
        elif t == "scoring_tower":
            # round 6 (owner O1 / orchestrator F1): a slender scoring tower, column (+ optional head board) on a plinth
            p = _enu(it["at"])
            out.append({k: v for k, v in it.items() if k not in ("at", "h_src")} | {"c": [rnd(p[0]), rnd(p[1])], "z": rnd(_ground(trk, p))})
            log(f"structure scoring tower '{it.get('name', '')}': {it['w']} x {it['d']} m, {it['h']} m at ({p[0]:.1f}, {p[1]:.1f})")
        elif t == "boards":
            out.append(boards(trk, it, sc["barriers"]))
        elif t == "paint":
            out.append(paint(trk, it))
        elif t == "fence":
            P = np.array([_enu(ll) for ll in it["pts"]])
            out.append({k: v for k, v in it.items() if k != "h_src"} | {"pts": [[rnd(x), rnd(y), rnd(_ground(trk, np.array([x, y])))] for x, y in P]})
        elif t == "terrace_dress":
            if not any(tr["name"] == it["terrace"] for tr in sc.get("terraces", [])):
                raise SystemExit(f"structures: terrace '{it['terrace']}' not in the scenery")
            out.append({k: v for k, v in it.items() if k != "h_src"})
        else:
            raise SystemExit(f"structures: unknown type {t}")
    polys = [Polygon(fp).buffer(1.0) for fp in outlines]
    # lidar-only boxes inside a structure
    keep = []
    for b in sc["buildings"]:
        c = np.mean(np.array(b["footprint"]), axis=0)
        if b["src"] == "lidar" and any(p.contains(Point(*c)) for p in polys):
            log(f"structures: lidar box at ({c[0]:.0f}, {c[1]:.0f}) {b['h']} m inside a structure, dropped")
            continue
        keep.append(b)
    sc["buildings"] = keep
    # trees inside a structure's outline
    tr = sc["trees"]
    D = np.array(tr["data"]).reshape(-1, tr["stride"])
    inside = np.array([any(p.contains(Point(x * tr["scale"], y * tr["scale"])) for p in polys) for x, y in D[:, :2]], bool) \
        if len(D) else np.zeros(0, bool)
    if inside.any():
        tr["data"] = [int(v) for v in D[~inside].ravel()]
        log(f"structures: {int(inside.sum())} trees inside structure outlines dropped")
    sc["structures"] = out
    log(f"structures: {len(out)} descriptors ({', '.join(sorted({o['type'] for o in out}))})")
    return sc
