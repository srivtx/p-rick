#!/usr/bin/env python3
"""P-027 E7 figure: f8-cifar.png, regenerated from cifar-results.json.

Torch-free on purpose (the repo's reproducibility bar): the figure
regenerates from the committed results file without the training stack.
The harness (code/p-027c-cifar.py) delegates here after its sweep.

Panels (CIFAR-10 unless the file says otherwise):
  (a) held-out test accuracy vs depth (mean +- 1 std, 3 seeds, LR
      selected on validation); diverged runs marked x at chance level
  (b) forward activation growth vs depth: median ||z_L|| / ||z_0|| on a
      log axis — the PH stream's own quantity, measured per position
  (c) backward gradient envelope vs depth: min--max band of the
      per-layer ratio ||g_t|| / ||g_L|| referenced to the readout-side
      gradient (ratios > 1 = backward amplification)
  (d) efficiency: seconds per training epoch vs depth, with parameter
      count and peak memory in the legend title

Run: python3 code/p-027d-cifar-figures.py
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'figures', 'p-027')
RES_PATH = os.path.join(OUT, 'cifar-results.json')

STYLES = {'ph': ('#0077BB', 'o', 'PH-Net (ours)'),
          'resnet': ('#CC3311', 's', 'ResNet'),
          'resnet-ln': ('#009988', 'D', 'ResNet + LN (branch)'),
          'resnet-tln': ('#AA3377', 'v', 'ResNet + LN (trunk)'),
          'cayley': ('#EE7733', '^', 'Cayley-Net')}


def make_figure(runs, out=OUT, dataset='cifar10'):
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

    runs = [r for r in runs if r['dataset'] == dataset]
    depths = sorted(set(r['depth'] for r in runs))
    n_classes = 100 if dataset == 'cifar100' else 10
    chance = 1.0 / n_classes

    def clean(ax):
        ax.yaxis.grid(True, alpha=0.12, color=G400)
        ax.set_axisbelow(True)

    def best_by_seed(dp, m):
        cand = [r for r in runs if r['depth'] == dp and r['model'] == m]
        by = {}
        for r in cand:
            if r['seed'] not in by or r['best_val_acc'] > \
                    by[r['seed']]['best_val_acc']:
                by[r['seed']] = r
        return list(by.values())

    fig, axes = plt.subplots(2, 2, figsize=(9.8, 7.6),
                             constrained_layout=True)

    # (a) accuracy vs depth
    ax = axes[0][0]
    for m, (c, mk, lab) in STYLES.items():
        dps, mu, sd = [], [], []
        for dp in depths:
            pick = best_by_seed(dp, m)
            if pick:
                dps.append(dp)
                accs = [r['test_acc'] for r in pick]
                mu.append(np.mean(accs)); sd.append(np.std(accs))
        if dps:
            ax.errorbar(dps, mu, yerr=sd, color=c, marker=mk, lw=2,
                        capsize=3, label=lab)
            div = [dp for dp in depths
                   if any(r['diverged'] for r in best_by_seed(dp, m))]
            if div:
                ax.plot(div, [chance] * len(div), marker='x', ms=9,
                        mew=2.2, color=c, lw=0, label=lab + ' diverged')
    ax.axhline(chance, color=G400, lw=1.0, ls=':')
    ax.set_xlabel('depth L')
    ax.set_ylabel('held-out test accuracy')
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks(depths)
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.02), ncol=2,
              title='%s: trained nets, 3 seeds, LR on validation'
              % dataset, title_fontsize=10)
    clean(ax)

    # (b) forward activation growth vs depth
    ax = axes[0][1]
    for m, (c, mk, lab) in STYLES.items():
        dps, mu, sd = [], [], []
        for dp in depths:
            pick = best_by_seed(dp, m)
            if pick:
                dps.append(dp)
                g = [r['act_growth'] for r in pick]
                mu.append(np.mean(g)); sd.append(np.std(g))
        if dps:
            ax.errorbar(dps, mu, yerr=sd, color=c, marker=mk, lw=2,
                        capsize=3, label=lab)
    ax.axhline(1.0, color=G900, lw=1.0, ls='--')
    ax.set_yscale('log')
    ax.set_xticks(depths)
    ax.set_xlabel('depth L')
    ax.set_ylabel(r'median $\|z_L\| / \|z_0\|$')
    ax.set_title('forward norm growth (trained)', fontsize=11.5)
    clean(ax)

    # (c) backward gradient envelope vs depth
    ax = axes[1][0]
    for m, (c, mk, lab) in STYLES.items():
        dps, mn, mx = [], [], []
        for dp in depths:
            pick = best_by_seed(dp, m)
            if pick:
                dps.append(dp)
                mn.append(np.mean([r['grad_min_ratio'] for r in pick]))
                mx.append(np.mean([r['grad_max_ratio'] for r in pick]))
        if dps:
            ax.fill_between(dps, mn, mx, color=c, alpha=0.16, lw=0)
            ax.plot(dps, mx, marker=mk, color=c, lw=2, label=lab)
            ax.plot(dps, mn, marker=mk, color=c, lw=1.3, ls='--', alpha=0.9)
    ax.axhline(1.0, color=G900, lw=1.0, ls='--')
    ax.set_yscale('log')
    ax.set_xticks(depths)
    ax.set_xlabel('depth L')
    ax.set_ylabel(r'$\|g_t\| / \|g_L\|$, min$-$max')
    ax.set_title('backward envelope (solid max / dashed min)',
                 fontsize=11.5)
    clean(ax)

    # (d) efficiency: seconds per epoch vs depth
    ax = axes[1][1]
    for m, (c, mk, lab) in STYLES.items():
        dps, mu = [], []
        for dp in depths:
            pick = best_by_seed(dp, m)
            gpu = [r for r in pick if r['device'].startswith('cuda')]
            if gpu:
                dps.append(dp)
                mu.append(np.mean([r['sec_per_epoch'] for r in gpu]))
        if dps:
            p = pick[0]['params'] / 1e6
            ax.plot(dps, mu, marker=mk, color=c, lw=2,
                    label='%s (%.1fM)' % (lab, p))
    ax.set_yscale('log')
    ax.set_xticks(depths)
    ax.set_xlabel('depth L')
    ax.set_ylabel('seconds / training epoch')
    ax.set_title('GPU wall-clock per epoch + parameter count',
                 fontsize=11.5)
    clean(ax)

    fig.savefig(os.path.join(out, 'f8-cifar.png'), bbox_inches='tight',
                pad_inches=0.25)
    plt.close(fig)


if __name__ == '__main__':
    doc = json.load(open(RES_PATH))
    make_figure(doc['runs'], OUT, dataset=doc['config']['dataset'])
    print('wrote', os.path.join(OUT, 'f8-cifar.png'))
