"""Compare two circuit packages object by object (the re-derivation test, tools/track/compare/REDERIVE.md): per kind,
the reference package's objects matched by the candidate within 15 m, missing from it, and the candidate's extra
objects, the height differences of the matched ones; optionally a sheet index of side-by-side stills at the same poses.

    python3 -I tools/track/compare/compare_packages.py --ref public/tracks/sonoma --cand <worktree>/public/tracks/sonoma \\
        [--tol 15] [--share 0.5] [--out report.md] [--json report.json]
    uv run --python 3.12 --with pillow python -I tools/track/compare/compare_packages.py --ref ... --cand ... \\
        --stills-ref <compare_sheets of the ref> --stills-cand <stills of the cand, camera_walk.ts --replay> --sheets <dir>

Both packages must share the ENU frame (the same `origin`: a re-derivation keeps the layout keys). Objects come from
scenery.json (kerb strips from the package's own track.json edges), each a set of points sampled every 2 m; a reference
object is MATCHED when at least `share` (0.5) of its points lie within `tol` (15 m) of points of candidate objects of
the same kind, MISSING otherwise; a candidate object is EXTRA by the same rule the other way. Heights of matched pairs
(the candidate object sharing most points) differ when |dh| > max(0.3 m, 25 %), the coverage gate's rule.

Kinds: wall, tyre_wall, fence (barriers and catch fences), kerb (strips), kerb_line, station (marshal huts), mast,
tyre_stack, block, impact, board (signs, wall boards, structure boards), ground_sign, stand (terraces, grandstands),
building (OSM buildings, garages, blocks, fuel islands), tower (scoring towers), bridge, cone_line, paint_line,
closed_road, runoff_zone, paved_area, pit_lane. Stills: camera_walk.ts writes walk.json with every pose; shoot the
reference walk, then `--replay` it on the candidate's dev server so the poses are the same; the sheets pair the stills
by file name (reference left, candidate right). Stdlib only, except the sheets (Pillow).
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BARRIER_KIND = {"concrete": "wall", "armco": "wall", "pitwall": "wall", "wall": "wall", "tyres": "tyre_wall", "fence": "fence"}
LANDMARK_KIND = {"marshal": "station", "mast": "mast", "light": "mast", "tyres": "tyre_stack", "block": "block", "impact": "impact",
                 "sign": "board", "banner": "board", "brake": "board", "corner": "board", "flagstand": "station", "gantry": "bridge"}


def densify(P, step=2.0):
    """points along a polyline every `step` m (2D)"""
    out = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(d / step)))
        for k in range(n):
            out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    if P:
        out.append((P[-1][0], P[-1][1]))
    return out


def ring(P, step=2.0):
    P = [tuple(p[:2]) for p in P]
    return densify(P + P[:1], step) if len(P) > 2 else densify(P, step)


def obj(kind, pts, label, h=None, src=""):
    return {"kind": kind, "pts": [(round(p[0], 2), round(p[1], 2)) for p in pts], "label": label, "h": h, "src": src or ""}


def objects(sc, track=None):
    """Every scenery object of the compared kinds as {kind, pts [(x, y)], label, h, src}."""
    out = []
    for k, b in enumerate(sc.get("barriers", [])):
        kind = BARRIER_KIND.get(b.get("kind"), "wall")
        pts = densify([p[:2] for p in b["pts"]])
        out.append(obj(kind, pts, f"barrier {k} ({b.get('kind')})", b.get("h"), b.get("src")))
        if (b.get("fence") or 0) > 0 and kind != "fence":
            out.append(obj("fence", pts, f"barrier {k} catch fence", (b.get("h") or 0) + b["fence"], b.get("src")))
    strips = (sc.get("kerbs") or {}).get("strips", [])
    if strips and track:
        n, sp = track["n"], track["spacing_m"]
        for st in strips:
            edge = track["left"] if st["side"] > 0 else track["right"]
            i0, i1 = int(round(st["s0"] / sp)), int(round(st["s1"] / sp))
            if i1 < i0:
                i1 += n
            out.append(obj("kerb", [edge[i % n][:2] for i in range(i0, i1 + 1)], f"kerb {st['s0']}-{st['s1']} ({'left' if st['side'] > 0 else 'right'})",
                           None, st.get("src")))
    for k, kl in enumerate(sc.get("kerb_lines", [])):
        out.append(obj("kerb_line", densify([p[:2] for p in kl["pts"]]), f"kerb line {k}", kl.get("h"), kl.get("src")))
    for m in sc.get("landmarks", []):
        kind = LANDMARK_KIND.get(m.get("kind"))
        if kind:
            pts = [(m["x"], m["y"])] + ([(m["x2"], m["y2"])] if m.get("x2") is not None else [])
            out.append(obj(kind, pts, f"{m['kind']} '{m.get('text', '')}'", m.get("top", m.get("h")), m.get("src")))
    for g in sc.get("ground_signs", []):
        out.append(obj("ground_sign", [(g["x"], g["y"])], f"ground sign '{g.get('text', '')}'", None, g.get("src")))
    for t in sc.get("terraces", []):
        P = []
        for r in t.get("rows", []):
            P += [tuple(q[:2]) for q in r["pts"]] if r.get("pts") else [tuple(r["a"]), tuple(r["b"])]
        out.append(obj("stand", P, f"terrace {t.get('name', '')}", None, t.get("src")))
    for k, b in enumerate(sc.get("buildings", [])):
        kind = "stand" if b.get("kind") == "grandstand" else "building"
        out.append(obj(kind, ring(b["footprint"]), f"building {k} '{b.get('name', '')}'", b.get("h"), b.get("src")))
    for st in sc.get("structures", []) or []:
        t, name = st.get("type"), f"structure {st.get('type')} '{st.get('name', '')}'"
        fp = ((st.get("collide") or [{}])[0] or {}).get("footprint")
        if t == "grandstand":
            out.append(obj("stand", ring(fp) if fp else densify([st["a"], st["b"]]), name, None, st.get("src")))
        elif t in ("garage", "block", "fuel"):
            h = max(st.get("eave", 0), st.get("ridge", 0)) if t == "garage" else st.get("h", 0) + (st.get("fascia", 0) if t == "fuel" else 0)
            out.append(obj("building", ring(fp) if fp else [tuple(st["c"][:2])], name, h, st.get("src")))
        elif t == "mast":
            for a in st.get("at", []):
                out.append(obj("mast", [tuple(a[:2])], f"{name} at ({a[0]}, {a[1]})", st.get("h"), st.get("src")))
        elif t == "scoring_tower":
            out.append(obj("tower", [tuple(st["c"][:2])], name, st.get("h"), st.get("src")))
        elif t == "canopy":   # round 9: a round canopy on a raised terrace (a building-like structure)
            out.append(obj("building", [tuple(st["c"][:2])], name, st.get("h"), st.get("src")))
        elif t == "boards" and st.get("pts"):
            out.append(obj("board", densify([p[:2] for p in st["pts"]]), name, st.get("h"), st.get("src")))
        elif t == "fence" and st.get("pts"):
            out.append(obj("fence", densify([p[:2] for p in st["pts"]]), name, st.get("h"), st.get("src")))
    for br in sc.get("bridges", []):
        pts = densify([br["a"], br["b"]]) if br.get("a") and br.get("b") else []
        out.append(obj("bridge", pts, f"bridge {br.get('id')} ({br.get('kind')})", br.get("deck_z"), br.get("src", br.get("deck_src"))))
    for k, c in enumerate(sc.get("cone_lines", [])):
        out.append(obj("cone_line", densify([p[:2] for p in c["pts"]]), f"cone line {k}", None, c.get("src")))
    pec = sc.get("pit_exit_cones") or {}
    if pec.get("pts"):
        out.append(obj("cone_line", densify([p[:2] for p in pec["pts"]]), "pit-exit cones", None, pec.get("src")))
    for k, p in enumerate(sc.get("paint_lines", [])):
        out.append(obj("paint_line", densify([q[:2] for q in p["pts"]]), f"paint line {k}", None, p.get("src")))
    for p in (sc.get("paved_zones") or {}).get("parts", []):
        kind = "closed_road" if p.get("kind") == "closed_road" else "runoff_zone"
        out.append(obj(kind, densify([q[:2] for q in p["center"]]), f"{p.get('kind')} '{p.get('turn') or p.get('name') or ''}'", None, p.get("surface")))
    for a in sc.get("paved_areas", []):
        out.append(obj("paved_area", ring(a["poly"], 4.0), f"paved area '{a.get('name', '')}'", None, a.get("src")))
    for k, p in enumerate((sc.get("pit_lane") or {}).get("parts", [])):
        out.append(obj("pit_lane", densify([q[:2] for q in p["center"]]), f"pit lane part {k}", None, ""))
    return [o for o in out if o["pts"]]


class Grid:
    """points of several objects in tol-sized cells: which objects have a point within tol of a query point"""

    def __init__(self, objs, tol):
        self.tol, self.cells = tol, {}
        for j, o in enumerate(objs):
            for p in o["pts"]:
                self.cells.setdefault((int(math.floor(p[0] / tol)), int(math.floor(p[1] / tol))), []).append((p, j))

    def near(self, p):
        ci, cj, t2, hit = int(math.floor(p[0] / self.tol)), int(math.floor(p[1] / self.tol)), self.tol ** 2, {}
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for q, j in self.cells.get((ci + di, cj + dj), ()):
                    d2 = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
                    if d2 <= t2 and d2 < hit.get(j, math.inf):
                        hit[j] = d2
        return hit


def height_differs(h_ref, h_cand):
    return h_ref is not None and h_cand is not None and abs(h_cand - h_ref) > max(0.3, 0.25 * abs(h_ref))


def match(ref, cand, tol=15.0, share=0.5):
    """Per kind: {kind: {ref, cand, matched [(ref obj, cand obj, median offset m, dh)], missing [ref obj], extra [cand obj],
    heights [(ref obj, cand obj, dh)]}}."""
    kinds = sorted({o["kind"] for o in ref} | {o["kind"] for o in cand})
    rep = {}
    for k in kinds:
        R = [o for o in ref if o["kind"] == k]
        C = [o for o in cand if o["kind"] == k]
        gc, gr = Grid(C, tol), Grid(R, tol)
        r = {"ref": len(R), "cand": len(C), "matched": [], "missing": [], "extra": [], "heights": []}
        for o in R:
            hits, votes, dists = 0, {}, []
            for p in o["pts"]:
                nb = gc.near(p)
                if nb:
                    hits += 1
                    j = min(nb, key=nb.get)
                    votes[j] = votes.get(j, 0) + 1
                    dists.append(math.sqrt(nb[j]))
            if hits >= share * len(o["pts"]):
                b = C[max(votes, key=votes.get)]
                dists.sort()
                dh = None if o["h"] is None or b["h"] is None else round(b["h"] - o["h"], 2)
                r["matched"].append((o, b, round(dists[len(dists) // 2], 2), dh))
                if height_differs(o["h"], b["h"]):
                    r["heights"].append((o, b, dh))
            else:
                r["missing"].append(o)
        for o in C:
            hits = sum(1 for p in o["pts"] if gr.near(p))
            if hits < share * len(o["pts"]):
                r["extra"].append(o)
        rep[k] = r
    return rep


def station_fn(track):
    """(x, y) -> nearest station (m) of a package's centre, for the listings"""
    if not track:
        return lambda p: None
    C, sp = track["center"], track["spacing_m"]
    g = Grid([{"pts": [tuple(c[:2]) for c in C]}], 40.0)
    idx = {tuple(c[:2]): i for i, c in enumerate(C)}

    def f(p):
        best, bd = None, math.inf
        for q, _ in [x for di in (-1, 0, 1) for dj in (-1, 0, 1)
                     for x in g.cells.get((int(math.floor(p[0] / 40)) + di, int(math.floor(p[1] / 40)) + dj), ())]:
            d = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
            if d < bd:
                best, bd = q, d
        return None if best is None else round(idx[best] * sp)
    return f


def report_md(rep, ref_dir, cand_dir, tol, share, at):
    def hs(o):
        return "" if o["h"] is None else f", h {o['h']}"

    def where(o):
        p = o["pts"][len(o["pts"]) // 2]
        s = at(p)
        return f"({p[0]:.0f}, {p[1]:.0f})" + (f", s {s}" if s is not None else "")
    L = [f"# Package comparison: {cand_dir} against {ref_dir}", "",
         f"Objects of each kind sampled every 2 m; a reference object is matched when {share:.0%} of its points lie within {tol:g} m of "
         "candidate objects of its kind (tools/track/compare/compare_packages.py). Heights differ when |dh| > max(0.3 m, 25 %).", "",
         "| kind | ref | cand | matched | missing | extra | height diffs | median offset of matched (m) |", "|---|---|---|---|---|---|---|---|"]
    tot = [0, 0, 0, 0, 0, 0]
    for k, r in rep.items():
        offs = sorted(m[2] for m in r["matched"])
        L.append(f"| {k} | {r['ref']} | {r['cand']} | {len(r['matched'])} | {len(r['missing'])} | {len(r['extra'])} | {len(r['heights'])} | "
                 f"{offs[len(offs) // 2] if offs else '-'} |")
        for i, v in enumerate((r["ref"], r["cand"], len(r["matched"]), len(r["missing"]), len(r["extra"]), len(r["heights"]))):
            tot[i] += v
    L.append(f"| **all** | {tot[0]} | {tot[1]} | {tot[2]} | {tot[3]} | {tot[4]} | {tot[5]} | |")
    for title, key in (("Missing (in the reference, not in the candidate)", "missing"), ("Extra (in the candidate, not in the reference)", "extra")):
        L += ["", f"## {title}", ""]
        rows = [(k, o) for k, r in rep.items() for o in r[key]]
        L += [f"- {k}: {o['label']} at {where(o)}{hs(o)}: {o['src'][:120]}" for k, o in rows] or ["- none"]
    L += ["", "## Height differences (matched objects)", ""]
    rows = [(k, a, b, dh) for k, r in rep.items() for a, b, dh in r["heights"]]
    L += [f"- {k}: {a['label']} h {a['h']} -> {b['label']} h {b['h']} (dh {dh:+.2f} m) at {where(a)}" for k, a, b, dh in rows] or ["- none"]
    return "\n".join(L) + "\n"


def summary_json(rep):
    return {k: {"ref": r["ref"], "cand": r["cand"], "matched": len(r["matched"]), "missing": len(r["missing"]), "extra": len(r["extra"]),
                "heights": len(r["heights"]),
                "missing_objects": [o["label"] for o in r["missing"]], "extra_objects": [o["label"] for o in r["extra"]],
                "height_diffs": [[a["label"], b["label"], dh] for a, b, dh in r["heights"]]} for k, r in rep.items()}


def pair_stills(walk_ref, walk_cand):
    """shots of the reference walk paired with the candidate's by file name (the candidate replayed the same poses)"""
    cand = {s["file"]: s for s in walk_cand.get("shots", [])}
    return [(s, cand.get(s["file"])) for s in walk_ref.get("shots", [])]


def write_sheets(ref_dir, cand_dir, out, title_ref="REF", title_cand="CAND"):
    sys.path.insert(0, HERE)
    import make_compare_sheets as M  # noqa: E402  (Pillow)
    wr = read_json(os.path.join(ref_dir, "walk.json"))
    wc = read_json(os.path.join(cand_dir, "walk.json"))
    os.makedirs(out, exist_ok=True)
    pairs = pair_stills(wr, wc)
    index = []
    by_kind = {}
    for a, b in pairs:
        by_kind.setdefault(a["side"], []).append((a, b))
    for kind, ps in by_kind.items():
        for k in range(0, len(ps), 6):
            grp = ps[k:k + 6]
            items = [{"left": os.path.join(ref_dir, a["file"]), "right": os.path.join(cand_dir, b["file"]) if b else None,
                      "caption": [f"{a['side']} s {a['s']:.0f} m {a.get('label', '') or ''}"[:150], f"{a['file']}", "" if b else "no candidate still"],
                      "s": a["s"]} for a, b in grp]
            name = f"pkg_{kind}_{k // 6:02d}.jpg"
            M.sheet(items, f"{kind}: reference left, candidate right, s {grp[0][0]['s']:.0f}-{grp[-1][0]['s']:.0f} m", os.path.join(out, name))
            index.append((kind, name, grp[0][0]["s"], grp[-1][0]["s"], sum(1 for _, b in grp if b)))
    md = ["# Side-by-side stills at the same poses", "", f"Reference stills: {ref_dir} (left); candidate: {cand_dir} (right, `camera_walk.ts --replay`).",
          "Local only (ignored by git).", "", "| sheet | poses | stations (m) | candidate stills |", "|---|---|---|---|"]
    md += [f"| [{n}]({n}) | {k} | {a:.0f}-{b:.0f} | {c} |" for k, n, a, b, c in index]
    write_text(os.path.join(out, "index.md"), "\n".join(md) + "\n")
    return index


def read_json(path):
    with open(path) as fh:
        return json.load(fh)


def write_text(path, text):
    with open(path, "w") as fh:
        fh.write(text)


def load(d):
    tp = os.path.join(d, "track.json")
    return read_json(os.path.join(d, "scenery.json")), (read_json(tp) if os.path.exists(tp) else None)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref", required=True, help="reference package directory (scenery.json, track.json)")
    ap.add_argument("--cand", required=True, help="candidate package directory")
    ap.add_argument("--tol", type=float, default=15.0)
    ap.add_argument("--share", type=float, default=0.5)
    ap.add_argument("--out", help="write the markdown report here (default: stdout)")
    ap.add_argument("--json", help="write the per-kind summary as JSON here")
    ap.add_argument("--stills-ref", help="camera_walk output of the reference (walk.json + sim/)")
    ap.add_argument("--stills-cand", help="camera_walk --replay output of the candidate")
    ap.add_argument("--sheets", help="directory for the side-by-side sheets and their index.md")
    a = ap.parse_args(argv)
    sr, tr = load(a.ref)
    sc, tc = load(a.cand)
    rep = match(objects(sr, tr), objects(sc, tc), a.tol, a.share)
    md = report_md(rep, a.ref, a.cand, a.tol, a.share, station_fn(tr))
    if a.out:
        write_text(a.out, md)
    else:
        sys.stdout.write(md)
    if a.json:
        write_text(a.json, json.dumps(summary_json(rep), indent=1))
    if a.sheets:
        if not (a.stills_ref and a.stills_cand):
            raise SystemExit("--sheets needs --stills-ref and --stills-cand")
        idx = write_sheets(a.stills_ref, a.stills_cand, a.sheets)
        print(f"{len(idx)} sheets in {a.sheets} (index.md)", file=sys.stderr)
    tot = {k: sum(len(r[k]) for r in rep.values()) for k in ("matched", "missing", "extra", "heights")}
    print(f"compare_packages: matched {tot['matched']}, missing {tot['missing']}, extra {tot['extra']}, height diffs {tot['heights']}", file=sys.stderr)
    return rep


if __name__ == "__main__":
    main()
