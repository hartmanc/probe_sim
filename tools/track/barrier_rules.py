"""Barrier rules of Sonoma round 12 (22 Oct 2026, judge r11 note N65 / N67), shared by build_scenery.py (the wall boards)
and scenery_post.py (the final pass over every barrier run). Pure numpy; tested in test_barrier_rules.py.

1. Hollows under a wall (N65, "the T10 to T11 boards step down between taller runs"). A barrier's base is the ground
   at its own line (CONTRACTS 2b), so a wall whose line crosses or runs along a ditch went down into it: the T10-T11
   boarded wall (declared, 166 points at 2 m) crosses the 3-4 m deep drainage ditch of the lidar DEM at s 3196-3218,
   its base fell from -0.60 m (s 3194.6) to -3.44 / -3.51 m and its top, and the boards on it, by up to 2.84 m. A wall
   is built level across such a hollow (on a culvert or footings), so its TOP follows the ground's upper hull there:
   inside a hollow at most `span` m wide at half its depth (along the run) whose ground drops at a slope of at least `slope`
   (rise over run between consecutive points) somewhere inside it and whose lips both stand `rise` m above its lowest
   ground (a one-sided drop is not a hollow), the top is lifted onto the chord between the lips;
   the base stays on the ground (the wall is drawn from the ground to its top). A gentle sag (every slope under
   `slope`) is ground the wall follows: no change (Laguna's 48 sags under walls and Armco have slopes 0.03-0.33).
   scenery.json: `top_z` [absolute z of the top per point] on a run with a lifted hollow (absent: ground + h).

2. Tyre rows on the road (N67, the T11-approach tyre head). The app draws a tyre run as two rows of 0.31 m stacks,
   row 0 on the line and row 1 0.6 m to the polyline's LEFT (src/app/scenery.ts; the physics collides at the same
   faces, src/physics/collision.ts TYRE_WALL). A run declared in driving order on the right of the track has the
   track on its left, so its row 1 stood toward the road: the T11-approach tyre wall's line is 0.55 m from the edge
   (the fitted-edge rule's minimum), its drawn face 0.37 m ON the road, and 0.73 m proud of the wall that ends on its
   head. Where the drawn track-side face would stand closer than `face_min` m to the edge, the run is reversed so its
   second row lies behind the line (unless a rigid wall stands within `wall_reach` m behind it: then the run is a
   facing and its rows belong in front)."""
import numpy as np

# the app's tyre-stack layout (src/app/scenery.ts TYRE_R, row offset 0.6; collision.ts TYRE_WALL)
TYRE_R = 0.31
TYRE_ROW = 0.6
RIGID = ("concrete", "pitwall", "armco")
HOLLOW_KINDS = ("concrete", "pitwall")   # walls built level across a hollow; Armco on posts and tyres follow the ground
HOLLOW_DEFAULTS = {"span": 30.0, "slope": 0.5, "rise": 0.3}


def hollow_lift(s, z, span=30.0, slope=0.5, rise=0.3):
    """Lift (m, >= 0) per point that puts the top of a wall level across the narrow, steep hollows of its ground
    profile z(s) (s: arclength along the run, increasing). The bridged profile is the upper hull of z over chords of
    at most `span` m; a contiguous stretch where it lies above z is a hollow, lifted only if a segment from its lip to
    its other lip drops at `slope` or more and both lips stand `rise` m or more above its lowest ground."""
    s = np.asarray(s, float)
    z = np.asarray(z, float)
    n = len(z)
    b = z.copy()
    for j in range(n):
        for k in range(j + 2, n):
            if s[k] - s[j] > span:
                break
            f = (s[j + 1:k] - s[j]) / max(s[k] - s[j], 1e-9)
            b[j + 1:k] = np.maximum(b[j + 1:k], z[j] + f * (z[k] - z[j]))
    d = b - z
    lift = np.zeros(n)
    seg = np.abs(np.diff(z)) / np.maximum(np.diff(s), 1e-9) if n > 1 else np.zeros(0)
    i = 0
    while i < n:
        if d[i] <= 1e-3:
            i += 1
            continue
        k = i
        while k + 1 < n and d[k + 1] > 1e-3:
            k += 1
        # the segments from the lip before the stretch to the lip after it; a hollow has a lip on BOTH sides standing
        # `rise` m above its lowest ground (the foot of a one-sided drop, an embankment, is not bridged: the wall-tops
        # gate shows it instead)
        a, e = max(i - 1, 0), min(k + 1, n - 1)
        low = z[i:k + 1].min()
        # and it is at most `span` m wide at half its depth (overlapping chords of a wider hollow, or the feet of two
        # drops, are not one hollow)
        deep = np.nonzero(d[i:k + 1] >= 0.5 * d[i:k + 1].max())[0]
        if (e > a and s[i + deep[-1]] - s[i + deep[0]] <= span and seg[a:e].max() >= slope
                and min(z[a], z[e]) - low >= rise):
            lift[i:k + 1] = d[i:k + 1]
        i = k + 1
    return lift


def run_lift(pts, span=30.0, slope=0.5, rise=0.3):
    """hollow_lift for a barrier polyline [[x, y, z], ...]."""
    P = np.asarray(pts, float)
    if len(P) < 3:
        return np.zeros(len(P))
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(P[:, :2], axis=0).T))]
    return hollow_lift(s, P[:, 2], span, slope, rise)


def barrier_tops(SC, cfg=None, log=print):
    """Final pass over scenery dict SC: `top_z` on every concrete / pit wall run with a lifted hollow (config scenery.barrier_hollows
    {span, slope}; absent: the defaults; False: off). Returns [(run index, points lifted, max lift)]."""
    if cfg is False:
        return []
    c = dict(HOLLOW_DEFAULTS, **(cfg or {}))
    rep = []
    for k, b in enumerate(SC.get("barriers", [])):
        b.pop("top_z", None)
        if b.get("kind") not in HOLLOW_KINDS or len(b.get("pts", [])) < 3:
            continue
        lift = run_lift(b["pts"], c["span"], c["slope"], c["rise"])
        if lift.max() <= 0:
            continue
        b["top_z"] = [round(float(p[2]) + float(b["h"]) + float(l), 2) for p, l in zip(b["pts"], lift)]
        rep.append((k, int((lift > 0).sum()), float(lift.max())))
        log(f"  barrier top across a hollow: run {k} ({b['kind']}, {str(b.get('src', ''))[:60]}): {int((lift > 0).sum())} "
            f"points lifted, max {lift.max():.2f} m (span {c['span']} m, slope {c['slope']})")
    return rep


def tyre_face_out(P, track_left, edge_dist):
    """Distance beyond the edge of a tyre run's drawn track-side face at each point: the line's own distance `edge_dist`
    less the row extent toward the track (row 1 on the polyline's left: TYRE_ROW + TYRE_R when the track is on the left,
    else TYRE_R)."""
    reach = np.where(np.asarray(track_left, bool), TYRE_ROW + TYRE_R, TYRE_R)
    return np.asarray(edge_dist, float) - reach
