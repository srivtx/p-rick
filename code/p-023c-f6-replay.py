#!/usr/bin/env python3
"""Re-render P-023 F6 (knee-migration) from results.json with collision-free
panel-(b) labels. Data is bit-identical to the harness run; only annotation
placement changes."""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE = '/home/z/my-project/p-rick-work'
OUT = os.path.join(BASE, 'figures', 'p-023')
d = json.load(open(os.path.join(OUT, 'results.json')))
f6a, f6b, f6c = d['f6a'], d['f6b'], d['f6c']

CB = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']
G400, G700, G900 = '#9CA3AF', '#374151', '#111827'
d_A, d_B = 256, 64


def clean_axis(ax, grid=True):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if grid:
        ax.yaxis.grid(True, alpha=0.12, color=G400)
        ax.set_axisbelow(True)


plt.rcParams.update({
    'font.size': 9.5, 'axes.titlesize': 10.5, 'axes.labelsize': 9.5,
    'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5,
    'axes.edgecolor': G700, 'axes.linewidth': 0.8,
    'xtick.color': G700, 'ytick.color': G700,
    'text.color': G900, 'axes.labelcolor': G900,
})

fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.6), constrained_layout=True)

# (a) knee vs accumulated distortion nu_eff
ax = axes[0, 0]
for key, v in f6a.items():
    if not v['knee']:
        continue
    G = float(key.split(',')[1].split('=')[1])
    col = {2: CB[2], 8: CB[0], 32: CB[3]}[int(G)]
    ax.plot(v['nu_eff'], v['knee'] / d_A, 'o', ms=7, color=col)
neffs = sorted(set(round(v['nu_eff'], 4) for v in f6a.values()))
kn = {}
for v in f6a.values():
    if v['knee']:
        kn.setdefault(round(v['nu_eff'], 4), []).append(v['knee'])
xs = sorted(kn)
ys = [np.mean(kn[x]) for x in xs]
sl = np.polyfit(np.log(xs), np.log(ys), 1)[0]
tt = np.exp(np.linspace(np.log(min(xs) * 0.9), np.log(max(xs) * 1.1), 40))
ax.plot(tt, (ys[-1] * (tt / xs[-1]) ** sl), ls='-', lw=1.4, color=G700)
ax.plot(tt, (ys[0] * (tt / xs[0]) ** 2), ls=':', lw=1.3, color=CB[1])
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('accumulated per-object distortion $\\nu_{eff}=\\sqrt{g}\\,\\nu$')
ax.set_ylabel('knee $L^*/d$')
ax.set_title('(a) knees collapse onto $\\nu_{eff}$ — sub-quadratically')
ax.legend(handles=[
    Line2D([0], [0], color=CB[2], lw=0, marker='o', label='$G$=2'),
    Line2D([0], [0], color=CB[0], lw=0, marker='o', label='$G$=8'),
    Line2D([0], [0], color=CB[3], lw=0, marker='o', label='$G$=32'),
    Line2D([0], [0], color=G700, lw=1.4,
           label=f'fit: $\\nu_{{eff}}^{{{sl:.2f}}}$'),
    Line2D([0], [0], color=CB[1], lw=1.3, ls=':', label='$\\nu_{eff}^2$ (law)'),
], loc='upper left', fontsize=8.2)
clean_axis(ax, grid=False)
ax.yaxis.grid(True, alpha=0.12, color=G400)

# (b) knee vs panel-corpus mismatch — labels fanned out, no collisions
ax = axes[0, 1]
panels_b = [('isotropic|random', 'random panel (matched)', CB[0], 'o'),
            ('isotropic|whitened', 'whitened selection', CB[1], 's'),
            ('isotropic|starved', 'starved panel (hot region)', CB[3], '^'),
            ('spiked|random', 'spiked corpus, random (matched)', CB[2], 'D'),
            ('geometric kappa=1e4|random', 'anisotropic corpus, random (matched)',
             CB[4], 'v')]
xs, ys, labs = [], [], []
for key, lab, col, mk in panels_b:
    v = f6b.get(key)
    if v and v['knee']:
        xs.append(v['mismatch'])
        ys.append(v['knee'] / d_B)
        labs.append(lab)
        ax.plot(v['mismatch'], v['knee'] / d_B, marker=mk, ms=8, lw=0,
                color=col)
tt = np.linspace(0.2, max(xs) * 1.2, 50)
base_k = f6b['isotropic|random']['knee'] / d_B
ax.plot(tt, base_k * tt, ls=':', lw=1.4, color=G700,
        label='$L^*\\propto$ mismatch (law)')
# (dx, dy, ha) — the three matched markers sit at one point; fan the labels:
# right-above, right-below, and left. Starved label above-right of its marker.
OFFS = {'random panel (matched)': (10, 7, 'left'),
        'whitened selection': (10, -17, 'left'),
        'starved panel (hot region)': (11, 9, 'left'),
        'spiked corpus, random (matched)': (-10, -3, 'right'),
        'anisotropic corpus, random (matched)': (10, 8, 'left')}
for x, y, lab in zip(xs, ys, labs):
    dx, dy, ha = OFFS.get(lab, (9, 5, 'left'))
    ax.annotate(lab, (x, y), textcoords='offset points',
                xytext=(dx, dy), fontsize=7.2, color=G700, ha=ha)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('panel-corpus mismatch $M/M_{iso}$ (measured)')
ax.set_ylabel('knee $L^*/d$')
ax.set_title('(b) matched panels are free; starved panels pay')
ax.legend(bbox_to_anchor=(0.5, -0.30), loc='upper center', ncol=2,
          fontsize=8.5)
clean_axis(ax, grid=False)
ax.yaxis.grid(True, alpha=0.12, color=G400)

# (c) estimator class
ax = axes[1, 0]
for key, col, mk in (('rot/orth', CB[0], 'o'), ('lin/orth', CB[3], '^'),
                     ('rot/affine', CB[1], 's'), ('lin/affine', CB[2], 'D')):
    v = f6c[key]
    ax.plot([l / d_B for l in v['L']], v['recall'], marker=mk, ms=4.5,
            lw=1.6, color=col,
            label={'rot/orth': 'rotation churn, orthogonal fit',
                   'lin/orth': 'linear churn, orthogonal fit (mismatched)',
                   'rot/affine': 'rotation churn, affine fit',
                   'lin/affine': 'linear churn, affine fit'}[key])
ax.set_xscale('log')
ax.set_xlabel('landmark count $L/d$')
ax.set_ylabel('anchored recall@10 (gen 8)')
ax.set_title('(c) budget set by estimator class; floor by containment')
ax.legend(bbox_to_anchor=(0.5, -0.32), loc='upper center', ncol=2,
          fontsize=8.0)
clean_axis(ax)

# (d) knee vs tolerance — recomputed from the stored nu=0.12,G=8 curve
curve = f6a['nu=0.12,G=8']
Ls = np.asarray(curve['L'], dtype=float)
recs = np.asarray(curve['recall'])
floor = float(np.mean(recs[-2:]))
deficit = floor - recs
f6d_theta, f6d_knee = [], []
for theta in (0.005, 0.010, 0.020, 0.040):
    k = None
    for i in range(len(Ls)):
        if deficit[i] <= theta:
            k = float(Ls[i]) if i == 0 else float(
                np.exp(0.5 * (np.log(Ls[i]) + np.log(Ls[i - 1]))))
            break
    f6d_theta.append(theta)
    f6d_knee.append(k)
ax = axes[1, 1]
xs = [t for t, k in zip(f6d_theta, f6d_knee) if k]
ys = [k / d_A for t, k in zip(f6d_theta, f6d_knee) if k]
ax.plot(xs, ys, 'o-', ms=6, lw=1.6, color=CB[5])
if len(xs) >= 2:
    sl = np.polyfit(np.log(xs), np.log(ys), 1)[0]
    tt = np.exp(np.linspace(np.log(min(xs)), np.log(max(xs)), 40))
    ax.plot(tt, ys[-1] * (tt / xs[-1]) ** sl, ls=':', lw=1.3, color=G700)
    ax.text(0.32, 0.18, f'slope $\\approx$ {sl:.2f}',
            transform=ax.transAxes, fontsize=9, color=G700)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('knee tolerance $\\theta$ (recall deficit)')
ax.set_ylabel('knee $L^*/d$')
ax.set_title('(d) the knee depends on the tolerance you choose')
clean_axis(ax, grid=False)
ax.yaxis.grid(True, alpha=0.12, color=G400)

path = os.path.join(OUT, 'f6-knee-migration.png')
fig.savefig(path, dpi=200, facecolor='white')
print('saved', path)
