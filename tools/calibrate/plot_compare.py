"""Speed vs s: sim lap against the driver A and optimal ghosts, with corner markers.

usage: uv run --python 3.12 --with matplotlib,numpy python tools/calibrate/plot_compare.py [out_dir]
writes tools/calibrate/compare.png
"""
import csv, json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = __file__.rsplit('/tools/', 1)[0]
out = sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/tools/calibrate/out'
rows = list(csv.DictReader(open(f'{out}/sim_lap.csv')))
col = lambda k: np.array([float(r[k]) for r in rows])
s, vs, ve, vo = col('s'), col('v_kmh'), col('driver_a_v_kmh'), col('optimal_v_kmh')
summary = json.load(open(f'{out}/summary.json'))
track = json.load(open(f'{ROOT}/public/tracks/laguna_seca/track.json'))

INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
C_SIM, C_EL, C_OPT = '#2a78d6', '#eb6834', '#1baf7a'
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': INK2, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'figure.facecolor': SURF, 'axes.facecolor': SURF})
fig, (ax, ad) = plt.subplots(2, 1, figsize=(15, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1.2], 'hspace': 0.08})
t = summary['lapTime']
ax.plot(s, ve, color=C_EL, lw=2, label='driver A ghost 1:59.32 (real)')
ax.plot(s, vo, color=C_OPT, lw=2, label='Optimal ghost 1:57.99')
ax.plot(s, vs, color=C_SIM, lw=2, label=f'Sim autopilot {int(t // 60)}:{t % 60:05.2f}')
for c in track['corners']:
    if c.get('turn') is None:
        continue
    for a in (ax, ad):
        a.axvline(c['s'], color=GRID, lw=1, zorder=0)
    ax.text(c['s'], 146 if c['turn'] == 'T8A' else 152, c['turn'], ha='left' if c['turn'] == 'T8A' else 'center', va='bottom', color=INK2, fontsize=9)
ax.set_ylim(30, 160)
ax.set_ylabel('speed (km/h)')
ax.grid(axis='y', color=GRID, lw=0.8)
ax.legend(loc='lower left', frameon=False, labelcolor=INK)
ax.set_title('Probe GT at Laguna Seca: sim lap on the ghost racing line vs logger ghosts', color=INK, loc='left')
for sp in ('top', 'right'):
    ax.spines[sp].set_visible(False); ad.spines[sp].set_visible(False)
ad.axhline(0, color=INK2, lw=1)
ad.plot(s, vs - ve, color=C_SIM, lw=2)
ad.set_ylabel('sim − driver A (km/h)')
ad.set_xlabel('distance from start/finish s (m)')
ad.grid(axis='y', color=GRID, lw=0.8)
ad.set_xlim(0, 3600)
fig.savefig(f'{ROOT}/tools/calibrate/compare.png', dpi=110, bbox_inches='tight')
print('wrote tools/calibrate/compare.png')
