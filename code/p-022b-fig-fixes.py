#!/usr/bin/env python3
"""Re-render p-022 F3 with adaptive cell-text contrast (rev 1.1).

Defect fixed: the % annotations on low-|gain| cells used a fixed grey that
collides with near-white cell backgrounds in the top-right region. The fix
chooses white or near-black text per cell from the cell's rendered
luminance. Data comes verbatim from figures/p-022/results.json (f3).
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'figures', 'p-022')

r = json.load(open(os.path.join(OUT, 'results.json')))
f3 = r['f3']
gain = np.asarray(f3['gain'])
FS = f3['fs']
ALPHAS = f3['alphas']

plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans'], 'axes.unicode_minus': False,
    'figure.facecolor': '#FFFFFF', 'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#E5E7EB', 'axes.linewidth': 0.8,
    'axes.spines.top': False, 'axes.spines.right': False,
    'xtick.major.size': 0, 'ytick.major.size': 0,
    'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'axes.labelsize': 11, 'axes.titlesize': 12.5,
    'axes.titleweight': 'bold', 'axes.titlepad': 10,
    'figure.dpi': 200, 'savefig.dpi': 200,
    'savefig.facecolor': '#FFFFFF', 'savefig.pad_inches': 0.2,
})
G700 = '#374151'

cmap = LinearSegmentedColormap.from_list('gn', ['#CC3311', '#F5C0B0',
                                                '#FFFFFF', '#BFD9E8', '#0B5730'])
norm = TwoSlopeNorm(vmin=min(-0.05, gain.min()), vcenter=0.0,
                    vmax=max(0.05, gain.max()))

fig, ax = plt.subplots(figsize=(6.6, 4.6), constrained_layout=True)
im = ax.imshow(gain, cmap=cmap, norm=norm, aspect='auto', origin='lower',
               extent=[FS[0] - 0.05, FS[-1] + 0.05,
                       ALPHAS[0] - 0.05, ALPHAS[-1] + 0.05])
amax = max(abs(gain.max()), abs(gain.min()))
for ai in range(len(ALPHAS)):
    for fi in range(len(FS)):
        v = gain[ai, fi]
        rgba = np.array(cmap(norm(v)))
        lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
        col = 'white' if lum < 0.55 else '#111827'
        ax.text(FS[fi], ALPHAS[ai], f'{v*100:.0f}%', ha='center', va='center',
                fontsize=8.2, color=col,
                fontweight='bold' if abs(v) == amax else 'normal')
ax.set_xlabel('transient fraction $f$')
ax.set_ylabel('Zipf exponent $\\alpha$')
ax.set_title('Gain of the admission law over LRU')
cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.04)
cb.set_label('relative hit-ratio gain', fontsize=9)
cb.outline.set_visible(False)
path = os.path.join(OUT, 'f3-gain-heatmap.png')
fig.savefig(path, dpi=200, facecolor='white')
plt.close(fig)
print('figure:', path, flush=True)
