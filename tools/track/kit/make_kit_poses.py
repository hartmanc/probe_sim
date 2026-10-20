"""Poses of the object kit's reference stills (tools/track/kit/README.md): one pose per kit object, aimed at one
instance of it in a package (the accepted Sonoma package by default), for compare/pose_walk.ts.

    python3 -I tools/track/kit/make_kit_poses.py [--package public/tracks/sonoma] [--out tools/track/kit/sonoma_poses.json]
    npx vite --port 5180 --strictPort &   # dev server of the package's worktree
    npx tsx tools/track/compare/pose_walk.ts --track sonoma --poses tools/track/kit/sonoma_poses.json \\
        --out tools/track/kit/stills --tag sonoma --port 5180

Each pose stands `d` metres from the instance's point on the line toward the nearest track centre point (so the hood
camera looks at the side the driver sees; on that centre point when `d` is None or the object is nearer the track), facing it, the camera pitched by `pitch` degrees; z is sampled from the drive
surface in the page. `along` poses stand on a surface's own centre line looking along it. The poses file is tracked so
a still can be retaken after a kit change; the stills are local (git-ignored).
"""
import argparse
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def mid(P):
    return P[len(P) // 2][:2]


def find(lst, pred, what):
    for x in lst:
        if pred(x):
            return x
    raise SystemExit(f"no instance for {what}")


def targets(sc, tr):
    B, LM, ST = sc["barriers"], sc["landmarks"], sc.get("structures", [])
    bar = lambda key: find(B, lambda b: key in b.get("src", ""), key)  # noqa: E731
    lm = lambda kind, f=lambda m: True: find(LM, lambda m: m["kind"] == kind and f(m), kind)  # noqa: E731
    st = lambda typ, name=None: find(ST, lambda s: s["type"] == typ and (name is None or s.get("name") == name), typ)  # noqa: E731
    k_strip = sc["kerbs"]["strips"][0]
    i = int(round((k_strip["s0"] + k_strip["s1"]) / 2 / tr["spacing_m"]))
    kerb_pt = (tr["left"] if k_strip["side"] > 0 else tr["right"])[i][:2]
    bridge = sc["bridges"][0]
    road = find(sc["paved_zones"]["parts"], lambda p: p.get("kind") == "closed_road" and "bypass" in (p.get("turn") or ""), "closed road")
    runoff = find(sc["paved_zones"]["parts"], lambda p: p.get("kind") == "runoff", "paved runoff")
    pec = sc["pit_exit_cones"]["pts"]
    imp = lm("impact")
    return [
        ("wall_concrete_endcap", bar("pit straight, pit-lane side")["pts"][-1][:2], 9, 0),
        ("wall_catch_fence", mid(bar("T10 to T11, right wall and catch fence")["pts"]), 14, 5),
        ("wall_jersey_impact", (imp["x"], imp["y"]), 12, 0),
        ("tyres_black_stacked", mid(bar("9a, right: tyre wall")["pts"]), 10, 0),
        ("tyres_white_stacked", mid(bar("T11 hairpin, left tyre wall")["pts"]), 10, 0),
        ("tyre_cushion_head", bar("T6 to T7, left: black cushion")["pts"][0][:2], 10, 0),
        ("movable_jersey_facing", mid(bar("movable Jersey")["pts"]), 14, 0),
        ("fence_standalone", mid(bar("Carousel, left: trackside fence")["pts"]), None, 5),
        ("cones_orange", mid(sc["cone_lines"][0]["pts"]), 9, -5),
        ("cones_yellow_small", mid(pec), 8, -5),
        ("tyre_stack", (lm("tyres")["x"], lm("tyres")["y"]), None, 0),
        ("block_striped", (lm("block", lambda m: m.get("style") == "striped")["x"], lm("block", lambda m: m.get("style") == "striped")["y"]), 9, 0),
        ("block_plain", (lm("block", lambda m: m.get("style") == "plain")["x"], lm("block", lambda m: m.get("style") == "plain")["y"]), 9, 0),
        ("marshal_hut", (lm("marshal", lambda m: m.get("text") == "T6 hilltop")["x"], lm("marshal", lambda m: m.get("text") == "T6 hilltop")["y"]), 16, 5),
        ("grandstand", tuple(st("grandstand")["a"][:2]), 70, 8),
        ("terrace", mid(find(sc["terraces"], lambda t: t["name"] == "T3a-T4", "terrace")["rows"][0]["pts"]), 40, 10),
        ("garage_row", tuple(st("garage", "Pit garages north")["c"][:2]), 30, 3),
        ("flat_block", tuple(st("block")["c"][:2]), 35, 3),
        ("fuel_island", tuple(st("fuel")["c"][:2]), 22, 3),
        ("light_mast", tuple(st("mast")["at"][0][:2]), None, 18),
        ("boards_on_wall", (lm("sign", lambda m: m.get("text") == "SONOMA RACEWAY")["x"], lm("sign", lambda m: m.get("text") == "SONOMA RACEWAY")["y"]), 10, 3),
        ("boards_structure", mid(st("boards")["pts"]), 9, 0),
        ("ground_sign", (sc["ground_signs"][0]["x"], sc["ground_signs"][0]["y"]), None, -5),
        ("bridge_abutments", tuple(bridge["ends"][0]["at"][:2]), 22, 5),
        ("bridge_banners", ((bridge["a"][0] + bridge["b"][0]) / 2, (bridge["a"][1] + bridge["b"][1]) / 2), 40, 4),
        ("scoring_tower", tuple(st("scoring_tower")["c"][:2]), 80, 14),
        ("kerb_strip", kerb_pt, 9, -6),
        ("kerb_line_raised", mid(sc["kerb_lines"][0]["pts"]), 9, -6),
        ("paint_line_declared", mid(sc["paint_lines"][0]["pts"]), 8, -6),
        ("osm_building", tuple(sc["buildings"][0]["footprint"][0][:2]), None, 3),
        ("closed_road_surface", ("along", road), 0, -3),
        ("paved_runoff_surface", ("along", runoff), 0, -3),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--package", default=os.path.join(ROOT, "public/tracks/sonoma"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools/track/kit/sonoma_poses.json"))
    a = ap.parse_args()
    sc = json.load(open(os.path.join(a.package, "scenery.json")))
    tr = json.load(open(os.path.join(a.package, "track.json")))
    C = [c[:2] for c in tr["center"]]
    poses = []
    for name, tgt, d, pitch in targets(sc, tr):
        if isinstance(tgt[0], str):           # along a surface's centre line, from its middle
            P = tgt[1]["center"]
            k = len(P) // 2
            a_, b_ = P[max(0, k - 3)], P[min(len(P) - 1, k + 3)]
            poses.append(dict(name=name, x=round(P[k][0], 2), y=round(P[k][1], 2), z=None,
                              heading=round(math.atan2(b_[1] - a_[1], b_[0] - a_[0]), 4), yaw=0, pitch=pitch))
            continue
        tx, ty = tgt
        c = min(C, key=lambda q: (q[0] - tx) ** 2 + (q[1] - ty) ** 2)
        ux, uy = c[0] - tx, c[1] - ty
        l = math.hypot(ux, uy) or 1.0
        if d is None or d > l:                # on the track: the nearest centre point
            x, y = c[0], c[1]
        else:
            x, y = tx + ux / l * d, ty + uy / l * d
        poses.append(dict(name=name, x=round(x, 2), y=round(y, 2), z=None, heading=round(math.atan2(ty - y, tx - x), 4), yaw=0, pitch=pitch,
                          target=[round(tx, 2), round(ty, 2)]))
    with open(a.out, "w") as fh:
        json.dump(poses, fh, indent=1)
    print(f"{len(poses)} poses -> {a.out}")


if __name__ == "__main__":
    main()
