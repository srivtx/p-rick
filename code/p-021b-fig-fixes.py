#!/usr/bin/env python3
"""Re-render p-021 F2 with overlap-free annotations (rev 1.1).

Defect fixed: the rotated per-N $T_c$ text labels overlapped the dotted
theory lines and the rising outbreak curves near x in [0.05, 0.12].
The threshold values now live in the legend labels; the vertical dotted
lines stay. Curves are reproduced EXACTLY by replaying the original
harness's rng consumption (seed 20261007: F1's four ecosystem builds,
then F2's three builds + cascade draws) — identical to the published run.

Also extends figures/p-021/results.json with the F2 curve arrays and the
T grid (f2.T, f2.<N>.prob) so future re-renders need no replay.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ── replay the original experiment sequence (F1 rng consumption, then F2) ──
import p021_replay_core as core   # functions copied verbatim from the harness

rng = np.random.default_rng(20261007)
GAMMA_EPID = 0.20

# F1: four families (rng consumption only — figures not re-rendered)
F1_FAMILY = [1.3, 1.8, 2.3, 3.0]
F1_N = 20000
for g in F1_FAMILY:
    kmax = min(max(int(F1_N ** (1.0 / (g - 1.0))), 8), 4000)
    core.build_ecosystem(F1_N, g, kmax, rng)

# F2: the experiment whose curves the figure needs
F2_GAMMA = 1.7
F2_SIZES = [2000, 8000, 32000]
F2_T = np.linspace(0.02, 0.50, 15)
f2_prob, f2_mean = {}, {}
for N in F2_SIZES:
    kmax = min(N // 4, 8000)
    src, dst = core.build_ecosystem(N, F2_GAMMA, kmax, rng)
    md = len(dst) / N
    f2_mean[N] = md
    seeds = 60 if N <= 8000 else 28
    probs = []
    for T in F2_T:
        _, p = core.outbreak_stats(src, dst, N, T, GAMMA_EPID, rng, seeds)
        probs.append(p)
    f2_prob[N] = np.array(probs)
    print(f'N={N} mean_d={md:.1f} Tc={1/md:.3f} P={np.round(probs, 2)}', flush=True)

# ── the fixed figure ───────────────────────────────────────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans'],
    'axes.unicode_minus': False,
    'figure.facecolor': '#FFFFFF', 'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#E5E7EB', 'axes.linewidth': 0.8,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': False,
    'xtick.major.size': 0, 'ytick.major.size': 0,
    'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'axes.labelsize': 11, 'axes.titlesize': 12.5,
    'axes.titleweight': 'bold', 'axes.titlepad': 10,
    'legend.frameon': False, 'legend.fontsize': 9.5,
    'figure.dpi': 200, 'savefig.dpi': 200,
    'savefig.facecolor': '#FFFFFF', 'savefig.pad_inches': 0.2,
})
CB = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']
G400, G700 = '#9CA3AF', '#374151'

OUT = os.path.join(HERE, '..', 'figures', 'p-021')
fig, ax = plt.subplots(figsize=(6.8, 4.4), constrained_layout=True)
for i, N in enumerate(F2_SIZES):
    Tc = 1.0 / f2_mean[N]
    ax.plot(F2_T, f2_prob[N], color=CB[i], lw=2.0, marker='o', ms=3.5,
            label=f'$N$={N:,}, $\\langle d\\rangle$={f2_mean[N]:.1f}, '
                  f'$T_c$={Tc:.3f}')
    ax.axvline(Tc, color=CB[i], ls=':', lw=1.1, alpha=0.8)
ax.set_xlabel('per-edge transmissibility $T$')
ax.set_ylabel('outbreak probability')
ax.set_ylim(-0.03, 1.03)
ax.set_xlim(0, 0.52)
ax.set_title('The threshold law: heavier-tailed registries burn easier',
              loc='left')
ax.legend(loc='upper left', fontsize=8.8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.yaxis.grid(True, alpha=0.12, color=G400)
ax.set_axisbelow(True)
path = os.path.join(OUT, 'f2-phase-transition.png')
fig.savefig(path, dpi=200, facecolor='white')
plt.close(fig)
print('figure:', path, flush=True)

# ── extend results.json with the curve arrays ─────────────────────────────
RES_PATH = os.path.join(OUT, 'results.json')
with open(RES_PATH) as f:
    RESULTS = json.load(f)
RESULTS['f2']['T'] = [float(t) for t in F2_T]
for N in F2_SIZES:
    RESULTS['f2'][str(N)]['prob'] = [float(p) for p in f2_prob[N]]
with open(RES_PATH, 'w') as f:
    json.dump(RESULTS, f, indent=1)
print('results.json extended with f2 curves', flush=True)
