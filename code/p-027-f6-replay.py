#!/usr/bin/env python3
"""Re-render P-027 F6 (law-validation ledger) from results.json with a
collision-free layout. Data is bit-identical to the harness run; only the
table/title geometry changes.

Defect (figure QA, 2026-10-10): the header cell "measured" collided with
the axes title "law validation — all laws measured in this harness".
Cause: ax.table(loc='center') + tbl.scale(1.0, 1.5) lets the table's rows
overflow the axes bounding box upward, into the title's pad region. Fix:
give the table an explicit bbox (which bounds every row inside the axes)
and place the title with modest pad above it. The same fix is patched
into code/p-027-simulation.py for future full re-runs.

Run: python3 code/p-027-f6-replay.py
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'figures', 'p-027')
d = json.load(open(os.path.join(OUT, 'results.json')))
rows = [tuple(r) for r in d['laws']]

G400, G900 = '#9CA3AF', '#111827'
plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans'], 'axes.unicode_minus': False,
    'figure.facecolor': '#FFFFFF', 'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#E5E7EB', 'axes.linewidth': 0.8,
    'xtick.major.size': 0, 'ytick.major.size': 0,
    'figure.dpi': 200, 'savefig.dpi': 200,
    'savefig.facecolor': '#FFFFFF',
})

fig, ax = plt.subplots(figsize=(7.6, 3.6), constrained_layout=True)
ax.axis('off')
tbl = ax.table(cellText=[[a, b] for a, b in rows],
               colLabels=['law', 'measured'],
               cellLoc='left', colLoc='left',
               bbox=[0.0, 0.0, 1.0, 1.0])   # bbox mode: rows cannot leave
tbl.auto_set_font_size(False)                # the axes box -> no collision
tbl.set_fontsize(9.5)
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_facecolor('#F3F4F6')
        cell.set_text_props(fontweight='bold')
    cell.set_edgecolor('#E5E7EB')
    cell.PAD = 0.03
ax.set_title('law validation — all laws measured in this harness',
             fontsize=12, fontweight='bold', pad=8)

fig.savefig(os.path.join(OUT, 'f6-law-validation.png'), bbox_inches='tight',
            pad_inches=0.25)
plt.close(fig)
print('wrote', os.path.join(OUT, 'f6-law-validation.png'))
