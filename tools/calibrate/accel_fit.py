"""Full-throttle acceleration vs speed: logger ghosts (grade-corrected) vs the sim's flat-ground a(v).

usage: uv run --python 3.12 --with numpy python tools/calibrate/accel_fit.py tools/calibrate/out/summary.json [more summaries...]
"""
import json, sys
import numpy as np

ROOT = __file__.rsplit('/tools/', 1)[0]
G = 9.81
track = json.load(open(f'{ROOT}/public/tracks/laguna_seca/track.json'))
ghosts = json.load(open(f'{ROOT}/public/tracks/laguna_seca/ghosts.json'))
z = np.array(track['center'])[:, 2]
L = track['length_m']
sg = np.arange(len(ghosts['line']['offset_m'])) * ghosts['s_grid_m']
zg = np.interp(sg, np.arange(len(z)), z, period=L)
grade = np.gradient(zg, sg)

def ghost_acc(lap):
    v = np.array(lap['v_mps']); t = np.array(lap['t']); thr = np.array(lap['throttle'])
    # central differences over +-2 grid points (8 m), only where throttle is full for the whole window
    a = np.full_like(v, np.nan)
    for i in range(2, len(v) - 2):
        if thr[i - 2:i + 3].min() >= 0.9:
            a[i] = (v[i + 2] - v[i - 2]) / (t[i + 2] - t[i - 2]) + G * grade[i]
    return v, a

bins = np.arange(14, 44, 2.0)
def binned(v, a):
    out = []
    for lo in bins:
        m = (v >= lo) & (v < lo + 2) & np.isfinite(a)
        out.append(np.median(a[m]) if m.sum() >= 3 else np.nan)
    return np.array(out)

laps = {l['id']: l for l in ghosts['laps']}
rows = {}
for k in ['driver_a_best', 'optimal', 'coby_best', 'driver_b_best']:
    rows[k] = binned(*ghost_acc(laps[k]))
sims = {}
for p in sys.argv[1:]:
    sm = json.load(open(p))
    tab = np.array(sm['accTable'])
    sims[p] = np.interp(bins + 1, tab[:, 0], tab[:, 1])
print('v km/h   ' + '  '.join(f'{k[:8]:>8s}' for k in rows) + '  ' + '  '.join(f'sim{i}' .rjust(8) for i in range(len(sims))))
for j, lo in enumerate(bins):
    print(f'{(lo + 1) * 3.6:6.0f}   ' + '  '.join(f'{rows[k][j] / G:8.3f}' for k in rows) + '  ' + '  '.join(f'{s[j] / G:8.3f}' for s in sims.values()))


# ---------------------------------------------------------------------------
# Least-squares fit of torque scale k_T and CdA from the ghosts' full-throttle samples:
#   m_eff(G)·a + Crr·m·g = k_T·[η·T(rpm)·G/r] − CdA·[½ρv²]      (a grade-corrected)
car = json.load(open(f'{ROOT}/public/cars/probe_gt/car.json'))
m = car['mass']; r = car['wheel']['radius']; eta = car['drivetrain']['efficiency']
ratios = np.array(car['drivetrain']['gearRatios'])
Ie = car['engine']['inertia']; Iw = car['wheel']['spinInertia']
tc = car['engine']['torqueCurve']
rho = car['aero']['airDensity']; crr = car['rollingResistance']; crr2 = car['rollingResistanceSpeed']
A, b, wts = [], [], []
for k in ['driver_a_best', 'optimal', 'coby_best', 'driver_b_best']:
    lap = laps[k]
    v, a = ghost_acc(lap)
    rpm = np.array(lap['rpm'])
    for i in np.where(np.isfinite(a) & (v > 15))[0]:
        Gr = rpm[i] / 60 * 2 * np.pi / (v[i] / r)
        gi = np.argmin(np.abs(ratios - Gr))
        if abs(ratios[gi] / Gr - 1) > 0.08:
            continue  # clutch/shift sample
        G_ = ratios[gi]
        T = np.interp(rpm[i], tc['rpm'], tc['torque'])
        meff = m + (Ie * G_ ** 2 + 4 * Iw) / r ** 2
        A.append([eta * T * G_ / r, -0.5 * rho * v[i] ** 2])
        b.append(meff * a[i] + (crr + crr2 * v[i] ** 2) * m * G)
A = np.array(A); b = np.array(b)
x, *_ = np.linalg.lstsq(A, b, rcond=None)
res = b - A @ x
print(f'\nLS fit over {len(b)} full-throttle samples: torque scale {x[0]:.3f}, CdA {x[1]:.3f} m^2 '
      f'(Cd {x[1] / car["aero"]["frontalArea"]:.3f} at A={car["aero"]["frontalArea"]}), rms residual {np.sqrt((res ** 2).mean()) / m / G:.3f} g')
for fixed_k in [0.80, 0.85, 0.90, 0.95, 1.0]:
    cda = np.linalg.lstsq(A[:, 1:2], b - fixed_k * A[:, 0], rcond=None)[0][0]
    rr = b - fixed_k * A[:, 0] - cda * A[:, 1]
    print(f'  torque scale {fixed_k:.2f} -> CdA {cda:.3f} (Cd {cda / car["aero"]["frontalArea"]:.3f}), rms {np.sqrt((rr ** 2).mean()) / m / G:.3f} g')
