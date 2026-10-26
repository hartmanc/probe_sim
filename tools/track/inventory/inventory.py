"""Eye-level feature inventory of a circuit (stage "inventory", before scenery; build-track skill).

The inventory is what the place looks like at eye level, frame by frame round one lap of a RECENT onboard video (plus
Street View / photo-sphere rows for what the video cannot show, plus pit-lane rows from a video that drives the lane):
every wall, fence, kerb, tyre wall, tyre stack, stand, station, bridge, building, mast, cone line, board, painted line
and runoff on each side. Each row is tied to a lap station s by a time-to-station map: the corner apexes (and the
start/finish crossings) are anchored to the package's corner stations (track.json corners) and t -> s is piecewise
linear between the anchors. The coverage gate (tools/track/gates/coverageGate.ts) checks scenery.json against it.

Inputs, all under tools/track/compare/<id>/inventory/ (tracked; the frames are not):
  source.json           the lap video (id, S/F crossing times), the anchors [{name, t, corner | s}], the observation
                        files, the frames folder
  observations.jsonl    one row per line, written while stepping the video (2 s steps): {t, side, kind, attrs,
                        confidence, note}; rows with an explicit s instead of t (Street View, a second video) carry
                        {s, source, frame} and need no time map
  extra_maps (optional, Mid-Ohio round 4): more videos (or segments of one compilation), each with its own time map
                        [{name, video {id, url, title, date, camera}, anchors, observations, frames, frame_pattern,
                        interp}]; their anchors need explicit s (or sf / corner), may start anywhere on the lap and run
                        past L (a segment that starts in Thunder Valley crosses S/F at s = L); their rows' t must lie
                        inside the segment's first..last anchor (no folding). Absent: the output is unchanged.
Outputs: tools/track/compare/<id>/inventory.json (rows: t, s, side, kind, attrs, confidence, frame, source, note; plus
the anchors, their leave-one-out residuals and the frame list) and inventory.md (the readable table).

    python3 -I tools/track/inventory/inventory.py --track sonoma            # validate, map, write json + md
    python3 -I tools/track/inventory/inventory.py --track sonoma --times 50 # onboard times of every 50 m step (json)

Standard library only (runs with the system python). Never reads or writes imagery; frames are only referenced.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK_DIR = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(TRACK_DIR, '..', '..'))

# kinds of row. PHYSICAL kinds are objects the scenery must place (coverage gate); the rest describe the surroundings.
PHYSICAL = ('wall', 'fence', 'kerb', 'tyre_wall', 'tyre_stack', 'stand', 'station', 'bridge', 'building', 'mast',
            'cone_line')
OTHER = ('boards', 'paint', 'runoff', 'tower', 'pit_lane', 'sign')
KINDS = PHYSICAL + OTHER
SIDES = ('left', 'right', 'both', 'ahead')
# how a height was obtained (tools/track/compare/HEIGHTS.md); 'unmeasured' is allowed but counted and listed
HEIGHT_METHODS = ('jersey-ref', 'safer-ref', 'fence-post-ref', 'tyre-ref', 'cone-ref', 'person-ref', 'car-ref',
                  'door-ref', 'horizon-ratio', 'storeys', 'shadow', 'lidar', 'unmeasured')
SCOPES = ('lap', 'pit')


# ------------------------------------------------------------------ time-to-station map
def speed_profile(track, a_lat=8.0, a_acc=2.5, a_brk=7.0, v_max=45.0, smooth=10):
    """A plain car's speed (m/s) at every station from the centreline curvature: v = sqrt(a_lat / kappa) capped at
    v_max, then forward (a_acc) and backward (a_brk) passes round the closed loop. Only its SHAPE is used: between two
    anchors the time is shared out in proportion to the profile's own time, so the anchors hold exactly and the car
    slows where the road bends."""
    C = track['center']; n = len(C); ds = track['spacing_m']
    xs = [sum(C[(i + k) % n][0] for k in range(-smooth, smooth + 1)) / (2 * smooth + 1) for i in range(n)]
    ys = [sum(C[(i + k) % n][1] for k in range(-smooth, smooth + 1)) / (2 * smooth + 1) for i in range(n)]
    v = []
    h = max(3, smooth)
    for i in range(n):
        ax, ay = xs[(i - h) % n], ys[(i - h) % n]; bx, by = xs[i], ys[i]; cx, cy = xs[(i + h) % n], ys[(i + h) % n]
        a = math.hypot(bx - ax, by - ay); b = math.hypot(cx - bx, cy - by); c = math.hypot(cx - ax, cy - ay)
        cross = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
        k = 2 * cross / max(a * b * c, 1e-9)
        v.append(min(v_max, math.sqrt(a_lat / k) if k > 1e-6 else v_max))
    for _ in range(2):
        for i in range(1, 2 * n):
            j, p = i % n, (i - 1) % n
            v[j] = min(v[j], math.sqrt(v[p] ** 2 + 2 * a_acc * ds))
        for i in range(2 * n - 2, -1, -1):
            j, q = i % n, (i + 1) % n
            v[j] = min(v[j], math.sqrt(v[q] ** 2 + 2 * a_brk * ds))
    return v


class TimeMap:
    """t -> s over anchors (t ascending, s ascending within one lap). The first and last anchors are the start/finish
    crossings (s = 0 and s = L); a time outside [t0, t1] is folded into the lap by the lap time. Between two anchors
    the map is piecewise linear in the speed profile's own time (interp 'profile', default when a profile is given:
    the car slows into corners) or in t itself (interp 'linear')."""

    def __init__(self, anchors, length, profile=None, spacing=1.0, strict=False):
        self.strict = strict   # a partial lap (a segment): no folding, a time outside the anchors is an error
        a = sorted(anchors, key=lambda q: q['t'])
        if len(a) < 2:
            raise ValueError('need at least two anchors')
        for p, q in zip(a, a[1:]):
            if not (q['t'] > p['t'] and q['s'] > p['s']):
                raise ValueError(f"anchors not increasing: {p['name']} (t {p['t']}, s {p['s']}) -> {q['name']} (t {q['t']}, s {q['s']})")
        self.a, self.L = a, float(length)
        self.t0, self.t1 = a[0]['t'], a[-1]['t']
        self.lap = self.t1 - self.t0
        self.cum = None
        if profile:
            # cumulative profile time at every station, over two laps (anchors may run past L)
            n = len(profile); cum = [0.0]
            for i in range(2 * n):
                cum.append(cum[-1] + spacing / profile[i % n])
            self.cum, self.sp, self.n = cum, spacing, n

    def _T(self, s):
        """profile time at station s (s may exceed L, up to 2L)"""
        x = s / self.sp; i = int(math.floor(x)); f = x - i
        i = max(0, min(i, len(self.cum) - 2))
        return self.cum[i] + f * (self.cum[i + 1] - self.cum[i])

    def _S(self, T):
        lo, hi = 0, len(self.cum) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if self.cum[m] <= T: lo = m
            else: hi = m
        f = (T - self.cum[lo]) / max(self.cum[lo + 1] - self.cum[lo], 1e-12)
        return (lo + f) * self.sp

    def fold(self, t):
        if self.t0 <= t <= self.t1:
            return t, 0
        if self.strict:
            raise ValueError(f't {t} outside the anchored segment {self.t0}..{self.t1}')
        k = math.floor((t - self.t0) / self.lap)
        return t - k * self.lap, k

    def _interp_s(self, p, q, tt):
        f = (tt - p['t']) / (q['t'] - p['t'])
        if self.cum is None:
            return p['s'] + (q['s'] - p['s']) * f
        Tp, Tq = self._T(p['s']), self._T(q['s'])
        return self._S(Tp + f * (Tq - Tp))

    def _interp_t(self, p, q, s):
        if self.cum is None:
            return p['t'] + (q['t'] - p['t']) * (s - p['s']) / (q['s'] - p['s'])
        Tp, Tq = self._T(p['s']), self._T(q['s'])
        return p['t'] + (q['t'] - p['t']) * (self._T(s) - Tp) / (Tq - Tp)

    def s(self, t):
        """Station (0 <= s < L) at video time t."""
        tt, _ = self.fold(t)
        a = self.a
        for p, q in zip(a, a[1:]):
            if tt <= q['t']:
                return self._interp_s(p, q, tt) % self.L
        return a[-1]['s'] % self.L

    def t(self, s):
        """Video time (within [t0, t1]) at station s."""
        a = self.a
        s0 = a[0]['s']
        s = (s - s0) % self.L + s0
        for p, q in zip(a, a[1:]):
            if s <= q['s']:
                return self._interp_t(p, q, s)
        return a[-1]['t']

    def residuals(self):
        """Leave-one-out: each inner anchor's s predicted from its two neighbours by the same interpolation (m), and
        the mean speed of each segment (m/s): a wrong anchor shows as a large residual and an implausible speed."""
        out = []
        a = self.a
        for k in range(1, len(a) - 1):
            p, q, r = a[k - 1], a[k], a[k + 1]
            pred = self._interp_s(p, r, q['t'])
            lin = p['s'] + (r['s'] - p['s']) * (q['t'] - p['t']) / (r['t'] - p['t'])
            out.append({'name': q['name'], 't': q['t'], 's': q['s'], 'loo_pred_s': round(pred, 1),
                        'loo_residual_m': round(q['s'] - pred, 1), 'loo_residual_linear_m': round(q['s'] - lin, 1),
                        'v_in': round((q['s'] - p['s']) / (q['t'] - p['t']), 1),
                        'v_out': round((r['s'] - q['s']) / (r['t'] - q['t']), 1)})
        return out


def anchors_from(src, track):
    """Anchors with s: {name, t, corner: turn} -> the package corner's s; {name, t, s} as given; 'S/F' -> 0 / L."""
    turns = {c['turn']: c for c in track['corners']}
    L = track['n'] * track['spacing_m']
    out = []
    for a in src['anchors']:
        q = dict(a)
        if 'corner' in a:
            if a['corner'] not in turns:
                raise ValueError(f"anchor {a['name']}: no corner {a['corner']!r} in track.json")
            q['s'] = turns[a['corner']]['s']
        elif a.get('sf') == 'start':
            q['s'] = 0.0
        elif a.get('sf') == 'end':
            q['s'] = L
        if 's' not in q:
            raise ValueError(f"anchor {a['name']}: needs corner, sf or s")
        out.append(q)
    return out, L


# ------------------------------------------------------------------ rows
def validate_row(r, where):
    errs = []
    if r.get('kind') not in KINDS:
        errs.append(f'{where}: kind {r.get("kind")!r} not in {KINDS}')
    if r.get('side') not in SIDES:
        errs.append(f'{where}: side {r.get("side")!r} not in {SIDES}')
    c = r.get('confidence')
    if not isinstance(c, (int, float)) or not 0 <= c <= 1:
        errs.append(f'{where}: confidence {c!r} not in [0, 1]')
    if 't' not in r and 's' not in r:
        errs.append(f'{where}: needs t (video time) or s (station)')
    if 's' in r and 't' not in r and not r.get('source'):
        errs.append(f'{where}: a row placed by s needs a source (panorama id, video id and time)')
    at = r.get('attrs', {})
    if not isinstance(at, dict):
        errs.append(f'{where}: attrs must be an object')
    elif 'h_m' in at:
        if not isinstance(at['h_m'], (int, float)) or not 0 < at['h_m'] < 100:
            errs.append(f'{where}: h_m {at["h_m"]!r} out of range')
        if at.get('h_method') not in HEIGHT_METHODS:
            errs.append(f'{where}: a height needs h_method in {HEIGHT_METHODS} (HEIGHTS.md), got {at.get("h_method")!r}')
    if r.get('scope', 'lap') not in SCOPES:
        errs.append(f'{where}: scope {r.get("scope")!r} not in {SCOPES}')
    return errs


def load_rows(path):
    rows = []
    for k, line in enumerate(open(path), 1):
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        r = json.loads(line)
        r['_where'] = f'{os.path.basename(path)}:{k}'
        rows.append(r)
    return rows


def build(track_id, root=ROOT, pkg=None):
    cdir = os.path.join(root, 'tools', 'track', 'compare', track_id)
    idir = os.path.join(cdir, 'inventory')
    src = json.load(open(os.path.join(idir, 'source.json')))
    # pkg: the package whose track.json gives the stations (default the published one; a new circuit has none before
    # stage 3, so its first inventory maps onto the geometry stage's candidate, tools/track/out/<id>)
    track = json.load(open(os.path.join(pkg or os.path.join(root, 'public', 'tracks', track_id), 'track.json')))
    anchors, L = anchors_from(src, track)
    prof = speed_profile(track) if src.get('interp', 'profile') == 'profile' else None
    tm = TimeMap(anchors, L, prof, track['spacing_m'])
    video = src['video']
    frames_dir = os.path.join(idir, src.get('frames', 'frames'))
    rows, errs, warn = [], [], []
    for f in src['observations']:
        for r in load_rows(os.path.join(idir, f)):
            errs += validate_row(r, r['_where'])
            if errs and errs[-1].startswith(r['_where']):
                continue
            out = {k: r[k] for k in ('side', 'kind', 'attrs', 'confidence') if k in r}
            out.setdefault('attrs', {})
            if 't' in r:
                out['t'] = r['t']
                s = tm.s(r['t']) + float(out['attrs'].get('ahead_m', 0.0))
                out['s'] = round(s % L, 1)
                out['source'] = r.get('source', f"onboard:{video['id']}@{r['t']:.1f}")
                out['frame'] = r.get('frame', src.get('frame_pattern', 't{t:03d}.jpg').format(t=int(round(r['t']))))
            else:
                out['t'] = None
                out['s'] = round(float(r['s']) % L, 1)
                out['source'] = r['source']
                out['frame'] = r.get('frame', '')
            out['scope'] = r.get('scope', 'lap')
            if r.get('note'):
                out['note'] = r['note']
            if out['frame'] and not os.path.exists(os.path.join(frames_dir, out['frame'])):
                warn.append(f"{r['_where']}: frame {out['frame']} not in {frames_dir} (frames are local only)")
            rows.append(out)
    extra = []
    for m in src.get('extra_maps', []):
        q_anchors, _ = anchors_from(m, track)
        m_prof = (prof or speed_profile(track)) if m.get('interp', 'profile') == 'profile' else None
        mtm = TimeMap(q_anchors, L, m_prof, track['spacing_m'], strict=True)
        mdir = os.path.join(idir, m.get('frames', 'frames'))
        n_rows = 0
        for f in m.get('observations', []):
            for r in load_rows(os.path.join(idir, f)):
                errs += validate_row(r, r['_where'])
                if errs and errs[-1].startswith(r['_where']):
                    continue
                if 't' not in r:
                    errs.append(f"{r['_where']}: a row of extra map {m['name']} needs t")
                    continue
                try:
                    s_ = mtm.s(r['t'])
                except ValueError as e:
                    errs.append(f"{r['_where']}: {e}")
                    continue
                out = {k: r[k] for k in ('side', 'kind', 'attrs', 'confidence') if k in r}
                out.setdefault('attrs', {})
                out['t'] = r['t']
                out['s'] = round((s_ + float(out['attrs'].get('ahead_m', 0.0))) % L, 1)
                out['source'] = r.get('source', f"onboard:{m['video']['id']}@{r['t']:.1f}")
                out['frame'] = r.get('frame', m.get('frame_pattern', 't{t:03d}.jpg').format(t=int(round(r['t']))))
                out['map'] = m['name']
                out['scope'] = r.get('scope', 'lap')
                if r.get('note'):
                    out['note'] = r['note']
                if out['frame'] and not os.path.exists(os.path.join(mdir, out['frame'])):
                    warn.append(f"{r['_where']}: frame {out['frame']} not in {mdir} (frames are local only)")
                rows.append(out)
                n_rows += 1
        extra.append({'name': m['name'], 'video': m['video'], 'interp': 'profile' if m_prof else 'linear',
                      'anchors': [{k: a[k] for k in ('name', 't', 's') if k in a} for a in mtm.a],
                      'anchor_residuals': mtm.residuals(), 'rows': n_rows,
                      'covers_s': [round(mtm.a[0]['s'] % L, 1), round(mtm.a[-1]['s'] % L, 1)],
                      'covers_t': [mtm.t0, mtm.t1]})
    rows.sort(key=lambda q: (q['scope'], q['s'], q['side'], q['kind']))
    frames = sorted({(q['t'], q['frame']) for q in rows if q['t'] is not None and 'map' not in q})
    unmeasured = [q for q in rows if q['attrs'].get('h_method') == 'unmeasured']
    inv = {
        'track': track_id, 'length_m': round(L, 2),
        'video': video, 'anchors': [{k: a[k] for k in ('name', 't', 's') if k in a} for a in tm.a],
        'anchor_residuals': tm.residuals(),
        'interp': 'profile' if prof else 'linear',
        'frames': [{'t': t, 'frame': f, 's': round(tm.s(t), 1)} for t, f in frames],
        'kinds': {'physical': list(PHYSICAL), 'other': list(OTHER)},
        'height_methods': list(HEIGHT_METHODS),
        'rows': rows,
        'counts': count(rows),
        'unmeasured_heights': len(unmeasured),
    }
    if extra:
        inv['extra_maps'] = extra
    return inv, tm, errs, warn


def count(rows):
    c = {}
    for r in rows:
        c[r['kind']] = c.get(r['kind'], 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


def mmss(t):
    return '' if t is None else f'{int(t // 60)}:{t % 60:04.1f}'


def markdown(inv):
    L = []
    v = inv['video']
    L.append(f"# {inv['track']}: eye-level feature inventory")
    L.append('')
    L.append(f"Generated by `tools/track/inventory/inventory.py --track {inv['track']}` from `inventory/observations*.jsonl`; "
             f"do not edit by hand. Lap video: {v.get('url', v['id'])} ({v.get('title', '')}, {v.get('date', '')}), "
             f"start/finish crossings at {mmss(inv['anchors'][0]['t'])} and {mmss(inv['anchors'][-1]['t'])}. "
             f"Frames (reference only, never committed): `inventory/frames/`. Heights cite the method of "
             f"`tools/track/compare/HEIGHTS.md`.")
    L.append('')
    L.append(f"{len(inv['frames'])} lap frames, {len(inv['rows'])} rows; by kind: "
             + ', '.join(f'{k} {n}' for k, n in inv['counts'].items())
             + f"; heights unmeasured: {inv['unmeasured_heights']}.")
    L.append('')
    L.append('## Time-to-station anchors')
    L.append('')
    L.append(f"Interpolation between anchors: {inv.get('interp')} (profile: shared out by a curvature speed profile's own time, so "
             "the car slows into corners; the residual is leave-one-out: the anchor's s predicted from its neighbours).")
    L.append('')
    L.append('| anchor | video t | track s (m) | leave-one-out predicted s | residual (m) | residual if linear in t (m) | speed in / out (m/s) |')
    L.append('|---|---|---|---|---|---|---|')
    res = {r['name']: r for r in inv['anchor_residuals']}
    for a in inv['anchors']:
        r = res.get(a['name'])
        L.append(f"| {a['name']} | {mmss(a['t'])} | {a['s']:.1f} | {r['loo_pred_s'] if r else '-'} | "
                 f"{r['loo_residual_m'] if r else '-'} | {r['loo_residual_linear_m'] if r else '-'} | {(str(r['v_in']) + ' / ' + str(r['v_out'])) if r else '-'} |")
    for m in inv.get('extra_maps', []):
        v = m['video']
        L.append('')
        L.append(f"### Time map: {m['name']} ({v.get('url', v['id'])}, {v.get('date', '')}; video {mmss(m['covers_t'][0])}-"
                 f"{mmss(m['covers_t'][1])}, s {m['covers_s'][0]:.0f} -> {m['covers_s'][1]:.0f}; {m['rows']} rows; {m['interp']})")
        L.append('')
        L.append('| anchor | video t | track s (m) | leave-one-out predicted s | residual (m) | residual if linear in t (m) | speed in / out (m/s) |')
        L.append('|---|---|---|---|---|---|---|')
        res = {r['name']: r for r in m['anchor_residuals']}
        for a in m['anchors']:
            r = res.get(a['name'])
            L.append(f"| {a['name']} | {mmss(a['t'])} | {a['s']:.1f} | {r['loo_pred_s'] if r else '-'} | "
                     f"{r['loo_residual_m'] if r else '-'} | {r['loo_residual_linear_m'] if r else '-'} | {(str(r['v_in']) + ' / ' + str(r['v_out'])) if r else '-'} |")
    for scope, title in (('lap', 'Rows round the lap'), ('pit', 'Pit-lane rows')):
        rows = [r for r in inv['rows'] if r['scope'] == scope]
        if not rows:
            continue
        L.append('')
        L.append(f'## {title} ({len(rows)})')
        L.append('')
        L.append('| s (m) | t | side | kind | what | height | conf | source | note |')
        L.append('|---|---|---|---|---|---|---|---|---|')
        for r in rows:
            a = r['attrs']
            what = ', '.join(str(a[k]) for k in ('type', 'colour', 'raised') if k in a)
            h = f"{a['h_m']} m ({a.get('h_method')})" if 'h_m' in a else ''
            L.append(f"| {r['s']:.0f} | {mmss(r['t'])} | {r['side']} | {r['kind']} | {what} | {h} | {r['confidence']} | "
                     f"{r['source']} | {r.get('note', '').replace('|', '/')} |")
    L.append('')
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--track', required=True)
    ap.add_argument('--times', type=float, default=0, help='print the video time of every STEP m station (json) and exit')
    ap.add_argument('--check', action='store_true', help='validate only, write nothing')
    ap.add_argument('--pkg', default=None, help='package dir with track.json (default public/tracks/<id>)')
    args = ap.parse_args()
    inv, tm, errs, warn = build(args.track, pkg=args.pkg)
    if args.times:
        n = int(inv['length_m'] // args.times) + 1
        print(json.dumps([{'s': round(k * args.times, 1), 't': round(tm.t(k * args.times), 2)} for k in range(n)
                          if k * args.times < inv['length_m']]))
        return 0
    for w in warn[:10]:
        print('warn:', w)
    if len(warn) > 10:
        print(f'warn: ... {len(warn) - 10} more')
    if errs:
        for e in errs:
            print('ERROR:', e)
        print(f'{len(errs)} errors; nothing written')
        return 1
    print(f"inventory {args.track}: {len(inv['frames'])} lap frames, {len(inv['rows'])} rows; " + ', '.join(f'{k} {n}' for k, n in inv['counts'].items()))
    print('anchors (leave-one-out residual m, speed in/out m/s):')
    for r in inv['anchor_residuals']:
        print(f"  {r['name']:<10} t {r['t']:6.1f}  s {r['s']:7.1f}  residual {r['loo_residual_m']:+7.1f} (linear {r['loo_residual_linear_m']:+7.1f})  v {r['v_in']:5.1f} / {r['v_out']:5.1f}")
    for m in inv.get('extra_maps', []):
        print(f"{m['name']}: {m['rows']} rows, anchors (leave-one-out residual m, speed in/out m/s):")
        for r in m['anchor_residuals']:
            print(f"  {r['name']:<10} t {r['t']:6.1f}  s {r['s']:7.1f}  residual {r['loo_residual_m']:+7.1f} (linear {r['loo_residual_linear_m']:+7.1f})  v {r['v_in']:5.1f} / {r['v_out']:5.1f}")
    if args.check:
        return 0
    cdir = os.path.join(ROOT, 'tools', 'track', 'compare', args.track)
    json.dump(inv, open(os.path.join(cdir, 'inventory.json'), 'w'), indent=1)
    open(os.path.join(cdir, 'inventory.md'), 'w').write(markdown(inv))
    print(f'wrote {cdir}/inventory.json, inventory.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
