#!/usr/bin/env python3
"""P-027 E6 figure: f7-training.png, regenerated from training-results.json.

Torch-free on purpose: the figure regenerates from the committed results
file without the training stack (the repo's reproducibility bar). The
training harness (code/p-027b-training.py) delegates here after its sweep.

Panels:
  (a) circles-4 held-out accuracy vs depth (mean +- 1 std, 3 seeds)
  (b) spirals-2 at depth 120 (bars, 3 seeds)
  (c) backward gradient envelope vs depth: min--max band of the per-layer
      ratio ||g_t|| / ||g_L|| measured on the trained models (solid = max,
      dashed = min, band between). All four architectures train without
      backward amplification (max = 1.000, the readout boundary); the min
      side is where the trained nets actually sit.
  (d) forward norm growth vs depth (median ||z_L|| / ||z_0||, trained)

Run: python3 code/p-027-figures.py
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'figures', 'p-027')
RES_PATH = os.path.join(OUT, 'training-results.json')

STYLES = {'ph': ('#0077BB', 'o', 'PH-Net (ours)'),
          'resnet': ('#CC3311', 's', 'ResNet'),
          'resnet-ln': ('#009988', 'D', 'ResNet + LN'),
          'resnet-tln': ('#AA3377', 'v', 'ResNet trunk-LN'),
          'cayley': ('#EE7733', '^', 'Cayley-Net')}


def make_figure(runs, out=OUT):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    G400, G900 = '#9CA3AF', '#111827'
    plt.rcParams.update({
        'font.sans-serif': ['DejaVu Sans'], 'axes.unicode_minus': False,
        'figure.facecolor': '#FFFFFF', 'axes.facecolor': '#FFFFFF',
        'axes.edgecolor': '#E5E7EB', 'axes.linewidth': 0.8,
        'axes.spines.top': False, 'axes.spines.right': False,
        'xtick.major.size': 0, 'ytick.major.size': 0,
        'xtick.labelsize': 10, 'ytick.labelsize': 10,
        'axes.labelsize': 11, 'axes.titlesize': 12.5,
        'axes.titleweight': 'bold', 'axes.titlepad': 10,
        'legend.frameon': False, 'legend.fontsize': 9.5,
        'figure.dpi': 200, 'savefig.dpi': 200,
        'savefig.facecolor': '#FFFFFF', 'savefig.pad_inches': 0.2,
    })

    TASKS = {'circles4': [30, 120, 240], 'spirals2': [120]}

    def clean(ax):
        ax.yaxis.grid(True, alpha=0.12, color=G400)
        ax.set_axisbelow(True)

    def best_by_seed(task, dp, m):
        cand = [r for r in runs if r['task'] == task and r['depth'] == dp
                and r['model'] == m]
        by = {}
        for r in cand:
            if r['seed'] not in by or r['val_acc'] > by[r['seed']]['val_acc']:
                by[r['seed']] = r
        return list(by.values())

    fig, axes = plt.subplots(2, 2, figsize=(9.8, 7.6), constrained_layout=True)

    # (a) circles-4 accuracy vs depth
    ax = axes[0][0]
    for m, (c, mk, lab) in STYLES.items():
        dps, mu, sd = [], [], []
        for dp in TASKS['circles4']:
            pick = best_by_seed('circles4', dp, m)
            if pick:
                dps.append(dp)
                accs = [r['test_acc'] for r in pick]
                mu.append(np.mean(accs)); sd.append(np.std(accs))
        if dps:  # skip models with no landed runs (empty legend entries)
            ax.errorbar(dps, mu, yerr=sd, color=c, marker=mk, lw=2, capsize=3,
                        label=lab)
    ax.axhline(0.25, color=G400, lw=1.0, ls=':')
    ax.set_xlabel('depth L')
    ax.set_ylabel('held-out test accuracy')
    ax.set_ylim(0.0, 1.05)
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.02), ncol=2,
              title='circles-4: trained nets, 3 seeds', title_fontsize=10.5)
    clean(ax)

    # (b) spirals-2 at depth 120
    ax = axes[0][1]
    names, mu, sd, cols = [], [], [], []
    for m, (c, mk, lab) in STYLES.items():
        pick = best_by_seed('spirals2', 120, m)
        if pick:
            accs = [r['test_acc'] for r in pick]
            names.append(lab); mu.append(np.mean(accs))
            sd.append(np.std(accs)); cols.append(c)
    ax.bar(range(len(names)), mu, yerr=sd, color=cols, width=0.62,
           capsize=3)
    ax.axhline(0.5, color=G400, lw=1.0, ls=':')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace(' (ours)', '') for n in names], fontsize=9)
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel('held-out test accuracy')
    ax.set_title('spirals-2 at depth 120 (3 seeds)', fontsize=11.5)
    clean(ax)

    # (c) backward gradient envelope vs depth (trained models)
    ax = axes[1][0]
    for m, (c, mk, lab) in STYLES.items():
        dps, mn, mx = [], [], []
        for dp in TASKS['circles4']:
            pick = best_by_seed('circles4', dp, m)
            if pick:
                dps.append(dp)
                mn.append(np.mean([r['grad_min_ratio'] for r in pick]))
                mx.append(np.mean([r['grad_max_ratio'] for r in pick]))
        if dps:  # skip models with no landed runs (empty legend entries)
            ax.fill_between(dps, mn, mx, color=c, alpha=0.16, lw=0)
            ax.plot(dps, mx, marker=mk, color=c, lw=2, label=lab)
            ax.plot(dps, mn, marker=mk, color=c, lw=1.3, ls='--', alpha=0.9)
    ax.axhline(1.0, color=G900, lw=1.0, ls='--')
    ax.set_yscale('log')
    ax.set_xlabel('depth L')
    ax.set_ylabel(r'$\|g_t\| / \|g_L\|$, min$-$max')
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.02), ncol=2,
              title='backward envelope, trained (solid max / dashed min)',
              title_fontsize=10)
    clean(ax)

    # (d) forward norm growth vs depth
    ax = axes[1][1]
    for m, (c, mk, lab) in STYLES.items():
        dps, mu = [], []
        for dp in TASKS['circles4']:
            pick = best_by_seed('circles4', dp, m)
            if pick:
                dps.append(dp)
                mu.append(np.mean([r['fwd_growth'] for r in pick]))
        if dps:  # skip models with no landed runs (empty legend entries)
            ax.plot(dps, mu, marker=mk, color=c, lw=2, label=lab)
    ax.axhline(1.0, color=G900, lw=1.0, ls='--')
    ax.set_yscale('log')
    ax.set_xlabel('depth L')
    ax.set_ylabel(r'median $\|z_L\| / \|z_0\|$')
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.02), ncol=2,
              title='forward norm growth (trained)', title_fontsize=10.5)
    clean(ax)

    fig.savefig(os.path.join(out, 'f7-training.png'), bbox_inches='tight',
                pad_inches=0.25)
    plt.close(fig)


if __name__ == '__main__':
    runs = json.load(open(RES_PATH))['runs']
    make_figure(runs)
    print('wrote', os.path.join(OUT, 'f7-training.png'))
