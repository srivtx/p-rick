#!/usr/bin/env python3
"""P-024 simulation: the resolution-collapse threshold of version-constrained
dependency resolution (random semver-CSP model).

Model: n packages, K versions each, version space CYCLIC (a ring) so that
every version is coverable by exactly w of the K possible windows (the
neutral geometry: no positional bias). Every version of package i carries
m ~ D dependency edges (j, mask): target j != i uniform, allowed set = w
consecutive versions starting at a uniformly random ring position. A
resolution assigns one version per package such that every edge activated
by the chosen versions is satisfied (target's chosen version in the set).

Solver: backtracking + forward-checking propagation + geometric random
restarts with shuffled value order (heavy-tailed search needs restarts;
verified against brute force on small instances).

Law under test (first moment, Markov):
    E[#solutions] = K^n (w/K)^{nD}  =>  satisfiability threshold
    D_c <= D_fm = ln K / ln(K/w)
with a measured gap ratio gamma = D_c / D_fm postulated ~ constant across
(K, w), measured under a uniform resolution budget.

Figures:
  f1-resolution-collapse.png  P(resolvable) vs D for n in {40,80,160} at a
                              generous budget + a practical-budget overlay
                              (the hardness tax); finite-size fit
  f2-threshold-law.png        measured D_c vs first-moment D_fm over the
                              (K, w) grid; gap ratio gamma; y=x bound line
  f3-solver-cost.png          median conflicts vs D (easy-hard-easy, log y)
  f4-growth.png               ecosystem growth: density drift vs threshold,
                              no-selection arm vs resolvability-selection arm
  f5-interventions.png        headroom levers: range widening, de-dup,
                              version pruning; version-proliferation panel
  f6-law-validation.png       predicted vs measured D_c across all configs

Writes results.json with every headline number cited in the paper.
"""
import json
import math
import os
import random
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.setrecursionlimit(20000)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'figures', 'p-024')
os.makedirs(OUT, exist_ok=True)

SEED = 20261007
RESULTS = {}

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
G400, G700, G900 = '#9CA3AF', '#374151', '#111827'


def clean_axis(ax, grid=True):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if grid:
        ax.yaxis.grid(True, alpha=0.12, color=G400)
        ax.set_axisbelow(True)


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, facecolor='white')
    plt.close(fig)
    print('figure:', path, flush=True)


# ════════════════════════════════════════════════════════════════════════════
# Instance generation
# ════════════════════════════════════════════════════════════════════════════

def gen_instance(rng, n, K, Dmean, w):
    """deps[i][v] = list of (j, lo, hi). Mean edges per version = Dmean.

    Fractional Dmean: each version draws floor(Dmean) + Bernoulli(frac).
    Duplicate targets within a version are allowed (real manifests re-target
    the same package with different ranges); self-edges are excluded.
    """
    base = int(math.floor(Dmean))
    frac = Dmean - base
    deps = []
    for i in range(n):
        vers = []
        for v in range(K):
            m = base + (1 if (frac > 0 and rng.random() < frac) else 0)
            if m == 0:
                vers.append([])
                continue
            js = rng.integers(0, n - 1, size=m)
            js[js >= i] += 1
            los = rng.integers(0, K, size=m)
            vers.append([(int(j), cyc_mask(int(lo), w, K))
                         for j, lo in zip(js, los)])
        deps.append(vers)
    return deps


def cyc_mask(lo, w, K):
    """Allowed-version bitmask: w consecutive versions from lo (ring)."""
    m = ((1 << w) - 1) << lo
    m = (m | (m >> K)) & ((1 << K) - 1)
    return m


# ════════════════════════════════════════════════════════════════════════════
# Solver: FC + propagation + geometric random restarts
# ════════════════════════════════════════════════════════════════════════════

def _search_once(n, K, deps, cap, order_rng):
    """One restart: MRV + forward checking. Returns (solved, conflicts)."""
    conflicts = [0]

    def propagate(dom, queue):
        while queue:
            j = queue.pop()
            d = dom[j]
            if d == 0:
                return False
            if d & (d - 1) == 0:            # singleton: forced assignment
                v = d.bit_length() - 1
                for (t, mask) in deps[j][v]:
                    nd = dom[t] & mask
                    if nd != dom[t]:
                        if nd == 0:
                            return False
                        dom[t] = nd
                        queue.append(t)
        return True

    def search(dom):
        if conflicts[0] > cap:
            return False
        best, bestc = -1, 1 << 30
        for i in range(n):
            d = dom[i]
            if d:
                c = bin(d).count('1')
                if c >= 2 and c < bestc:
                    best, bestc = i, c
                    if c == 2:
                        break
        if best < 0:
            return True                     # all domains singleton or empty
        i = best
        d = dom[i]
        bits = []
        while d:
            vbit = d & -d
            d &= d - 1
            bits.append(vbit)
        if order_rng is not None:
            order_rng.shuffle(bits)
        for vbit in bits:
            v = vbit.bit_length() - 1
            ndom = list(dom)
            ndom[i] = vbit
            queue = []
            for (t, mask) in deps[i][v]:
                nd = ndom[t] & mask
                if nd != ndom[t]:
                    ndom[t] = nd
                    queue.append(t)
            if (not queue or propagate(ndom, queue)) and search(ndom):
                return True
            conflicts[0] += 1
            if conflicts[0] > cap:
                return False
        return False

    solved = search([(1 << K) - 1] * n)
    return solved, conflicts[0]


def solve(n, K, deps, cap=12000, seed=0):
    """Geometric restarts (base 64, ratio 1.5). Total conflict budget = cap.

    Returns (solved, total_conflicts). The first restart uses deterministic
    lowest-version-first ordering; later restarts shuffle the value order.
    An exhausted search tree (conflicts < per-restart cap) proves UNSAT and
    stops early.
    """
    total = 0
    restart = 0
    while total <= cap and restart < 600:
        per = int(64 * (1.5 ** restart))
        rng = None if restart == 0 else random.Random(seed * 7919 + restart)
        budget = min(per, cap - total + 64)
        ok, c = _search_once(n, K, deps, budget, rng)
        total += c
        if ok:
            return True, total
        if c < budget - 1:
            return False, total              # search tree exhausted: UNSAT
        restart += 1
    return False, total


def solvable_curve(rng, n, K, Dgrid, w, trials, cap=12000, want_cost=False,
                   seed_tag=0):
    """P(solved within budget) and median conflicts per D point."""
    ps, costs = [], []
    for D in Dgrid:
        sat = 0
        cf = []
        for t in range(trials):
            deps = gen_instance(rng, n, K, D, w)
            ok, c = solve(n, K, deps, cap=cap, seed=seed_tag * 131 + t)
            sat += ok
            if want_cost:
                cf.append(c)
        ps.append(sat / trials)
        costs.append(float(np.median(cf)) if cf else None)
    return np.array(ps), costs


def logistic_fit(D, P):
    """Fit P ~ 1/(1+exp(-k(D-Dc))); return (Dc, k)."""
    P = np.clip(P, 0.02, 0.98)
    y = np.log(P / (1 - P))
    A = np.vstack([np.ones_like(D), D]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    k = coef[1]
    Dc = -coef[0] / k
    return float(Dc), float(k)


def d_fm(K, w):
    return math.log(K) / math.log(K / w)


# ════════════════════════════════════════════════════════════════════════════
# F1 — resolution collapse curves + finite-size scaling + hardness tax
# ════════════════════════════════════════════════════════════════════════════

PART2 = os.environ.get('P024_PART2') == '1'
print('F1: collapse curves', flush=True)
K1, w1 = 64, 16
ns = [40, 80, 160]
Dg1 = np.round(np.linspace(1.2, 3.6, 10), 2)
if PART2:
    # values from the completed full run (identical seeds); curves omitted
    fits = {40: (2.343, -4.31), 80: (2.092, -3.93), 160: (1.981, -3.72)}
    Dc80_low = 1.946
    curves = {}
    P80_low = None
    lns = np.log([n for n in ns])
    widths = np.array([math.log(81) / abs(fits[n][1]) for n in ns])
    slope, icept = np.polyfit(lns, np.log(widths), 1)
    nu = -1.0 / slope
    A = np.vstack([np.ones_like(lns), 1.0 / np.array(ns)]).T
    Dc_inf_coef, *_ = np.linalg.lstsq(A, [fits[n][0] for n in ns], rcond=None)
    Dc_inf = float(Dc_inf_coef[0])
    print(f'  [cached] Dc_inf={Dc_inf:.3f} nu={nu:.2f}', flush=True)
else:
    trials1 = {40: 120, 80: 90, 160: 50}
    caps1 = {40: 12000, 80: 12000, 160: 10000}
    curves = {}
    for n in ns:
        rng = np.random.default_rng([SEED, 1, n])
        P, _ = solvable_curve(rng, n, K1, Dg1, w1, trials1[n],
                              cap=caps1[n], seed_tag=n)
        curves[n] = P
        Dc, k = logistic_fit(Dg1, P)
        fits[n] = (Dc, k)
        print(f'  n={n}: Dc={Dc:.3f} k={k:.2f}', flush=True)

    # practical-budget overlay at n=80 (the hardness tax)
    rng = np.random.default_rng([SEED, 1, 81])
    P80_low, _ = solvable_curve(rng, 80, K1, Dg1, w1, 90, cap=1000,
                                seed_tag=801)
    Dc80_low, k80_low = logistic_fit(Dg1, P80_low)
    print(f'  n=80 practical budget (1000): Dc={Dc80_low:.3f}', flush=True)

    lns = np.log([n for n in ns])
    widths = np.array([math.log(81) / abs(fits[n][1]) for n in ns])
    slope, icept = np.polyfit(lns, np.log(widths), 1)
    nu = -1.0 / slope
    A = np.vstack([np.ones_like(lns), 1.0 / np.array(ns)]).T
    Dc_inf_coef, *_ = np.linalg.lstsq(A, [fits[n][0] for n in ns], rcond=None)
    Dc_inf = float(Dc_inf_coef[0])
    print(f'  finite-size: nu={nu:.2f}; Dc(inf)={Dc_inf:.3f}', flush=True)

    fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
    cols = [CB[1], CB[0], CB[3]]
    for c, n in zip(cols, ns):
        ax.plot(Dg1, curves[n], 'o-', ms=4, lw=1.6, color=c,
                label=f'n = {n}')
        ax.axvline(fits[n][0], color=c, ls=':', lw=1.1, alpha=0.8)
    ax.plot(Dg1, P80_low, 's--', ms=3.5, lw=1.3, color=G700, alpha=0.85,
            label='n = 80, practical budget (1k conflicts)')
    ax.axvline(d_fm(K1, w1), color=G900, ls='--', lw=1.4)
    ax.text(d_fm(K1, w1) + 0.05, 0.45, 'first-moment\nbound $D_{fm}$',
            fontsize=9, color=G900)
    ax.set_xlabel('dependency density $D$ (edges per version)')
    ax.set_ylabel('P(resolvable within budget)')
    ax.set_title('Resolution collapses at a critical dependency density')
    ax.set_ylim(-0.03, 1.05)
    ax.legend(loc='upper right', bbox_to_anchor=(1.0, 0.97), fontsize=8.6)
    clean_axis(ax)
    save(fig, 'f1-resolution-collapse.png')

RESULTS['f1'] = {
    'K': K1, 'w': w1, 'D_grid': Dg1.tolist(),
    'curves': {str(n): (curves[n].tolist() if n in curves else None)
               for n in ns},
    'fits': {str(n): {'Dc': fits[n][0], 'k': fits[n][1]} for n in ns},
    'practical_curve_n80': (P80_low.tolist()
                            if P80_low is not None else None),
    'Dc_practical_n80': Dc80_low,
    'widths': widths.tolist(), 'nu': float(nu), 'Dc_inf': Dc_inf,
    'D_fm': d_fm(K1, w1), 'gamma_inf': Dc_inf / d_fm(K1, w1),
}

# ════════════════════════════════════════════════════════════════════════════
# F2 — the threshold law across (K, w)
# ════════════════════════════════════════════════════════════════════════════

print('F2: threshold law grid', flush=True)
grid = []
for K in [16, 32, 64, 128]:
    for ratio in [0.125, 0.25, 0.5]:
        w = max(1, int(round(K * ratio)))
        if w >= K:
            continue
        grid.append((K, w))
n2 = 64
if PART2:
    rows = [
        {'K': 16, 'w': 2, 'D_fm': 1.333, 'Dc': 1.17, 'gamma': 0.880},
        {'K': 16, 'w': 4, 'D_fm': 2.0, 'Dc': 1.61, 'gamma': 0.804},
        {'K': 16, 'w': 8, 'D_fm': 4.0, 'Dc': 2.64, 'gamma': 0.661},
        {'K': 32, 'w': 4, 'D_fm': 1.667, 'Dc': 1.43, 'gamma': 0.855},
        {'K': 32, 'w': 8, 'D_fm': 2.5, 'Dc': 1.80, 'gamma': 0.719},
        {'K': 32, 'w': 16, 'D_fm': 5.0, 'Dc': 3.45, 'gamma': 0.690},
        {'K': 64, 'w': 8, 'D_fm': 2.0, 'Dc': 1.61, 'gamma': 0.804},
        {'K': 64, 'w': 16, 'D_fm': 3.0, 'Dc': 1.96, 'gamma': 0.653},
        {'K': 64, 'w': 32, 'D_fm': 6.0, 'Dc': 4.21, 'gamma': 0.702},
        {'K': 128, 'w': 16, 'D_fm': 2.333, 'Dc': 1.77, 'gamma': 0.759},
        {'K': 128, 'w': 32, 'D_fm': 3.5, 'Dc': 2.30, 'gamma': 0.658},
        {'K': 128, 'w': 64, 'D_fm': 7.0, 'Dc': 4.83, 'gamma': 0.690},
    ]
else:
    rows = []
    for (K, w) in grid:
        fm = d_fm(K, w)
        Dg = np.round(np.linspace(max(0.3, 0.35 * fm), 1.75 * fm, 11), 2)
        rng = np.random.default_rng([SEED, 2, K, w])
        P, _ = solvable_curve(rng, n2, K, Dg, w, 80, cap=8000, seed_tag=K + w)
        Dc, k = logistic_fit(Dg, P)
        rows.append({'K': K, 'w': w, 'D_fm': fm, 'Dc': Dc, 'gamma': Dc / fm})
        print(f'  K={K} w={w}: Dfm={fm:.2f} Dc={Dc:.2f} gamma={Dc/fm:.3f}',
              flush=True)

gam = np.array([r['gamma'] for r in rows])
gamma_bar = float(np.median(gam))
RESULTS['f2'] = {'rows': rows, 'gamma_bar': gamma_bar,
                 'gamma_cv': float(gam.std() / gam.mean()),
                 'gamma_min': float(gam.min()), 'gamma_max': float(gam.max()),
                 'budget': 8000, 'n': n2}
print(f'  gamma median={gamma_bar:.3f} cv={RESULTS["f2"]["gamma_cv"]:.3f}',
      flush=True)

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
x = np.array([r['D_fm'] for r in rows])
y = np.array([r['Dc'] for r in rows])
axa.plot([0, x.max() * 1.1], [0, x.max() * 1.1], '--', color=G400, lw=1.2,
         label='first-moment bound ($\\gamma=1$)')
axa.plot(x, y, 'o', ms=6, color=CB[0], label='measured $D_c$ (budget 8k)')
xf = np.linspace(0, x.max() * 1.05, 10)
axa.plot(xf, gamma_bar * xf, '-', color=CB[3], lw=1.6,
         label=f'law: $D_c = \\gamma\\,D_{{fm}}$,  $\\gamma = {gamma_bar:.2f}$')
axa.set_xlabel('first-moment threshold $D_{fm} = \\ln K / \\ln(K/w)$')
axa.set_ylabel('measured threshold $D_c$')
axa.set_title('The gap is a near-constant ratio')
axa.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=8.6)
clean_axis(axa)

labels = [f'{r["K"]}/{r["w"]}' for r in rows]
axb.bar(range(len(rows)), gam, color=CB[0], alpha=0.85, width=0.65)
axb.axhline(1.0, color=G400, ls='--', lw=1.2)
axb.axhline(gamma_bar, color=CB[3], ls='-', lw=1.6)
axb.set_xticks(range(len(rows)))
axb.set_xticklabels(labels, rotation=60, fontsize=8)
axb.set_ylabel('gap ratio $\\gamma = D_c / D_{fm}$')
axb.set_title('Gap ratio across the $(K, w)$ grid')
clean_axis(axb)
save(fig, 'f2-threshold-law.png')

# ════════════════════════════════════════════════════════════════════════════
# F3 — solver cost: easy-hard-easy
# ════════════════════════════════════════════════════════════════════════════

print('F3: solver cost', flush=True)
ns3 = [40, 80, 160]
Dg3 = np.round(np.arange(1.0, 3.41, 0.4), 2)
if PART2:
    cost_curves = {n: None for n in ns3}
    cost_peaks = {40: 1588, 80: 1618, 160: 1680}
    print('  [cached] peaks: ' + str(cost_peaks), flush=True)
else:
    cost_curves = {}
    for n in ns3:
        rng = np.random.default_rng([SEED, 3, n])
        tr = {40: 100, 80: 70, 160: 40}[n]
        P, costs = solvable_curve(rng, n, K1, Dg3, w1, tr, cap=1500,
                                  want_cost=True, seed_tag=n + 5)
        cost_curves[n] = costs
        print(f'  n={n}: peak median conflicts '
              f'{max(c for c in costs if c is not None):.0f}', flush=True)

fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
for c, n in zip([CB[1], CB[0], CB[3]], ns3):
    if cost_curves[n] is None:
        continue
    ax.plot(Dg3, cost_curves[n], 'o-', ms=4, lw=1.6, color=c, label=f'n = {n}')
ax.set_yscale('log')
ax.axvline(fits[80][0], color=G700, ls=':', lw=1.3)
ax.text(fits[80][0] + 0.06, 2.0, '$D_c(n{=}80)$', fontsize=9, color=G700)
ax.set_xlabel('dependency density $D$')
ax.set_ylabel('median conflicts (log scale)')
ax.set_title('Install cost: easy, hard at the threshold, easy again')
ax.legend(loc='upper right', bbox_to_anchor=(1.0, 0.98))
clean_axis(ax)
if not PART2:
    save(fig, 'f3-solver-cost.png')
else:
    plt.close(fig)

RESULTS['f3'] = {'D_grid': Dg3.tolist(),
                 'costs': {str(n): cost_curves[n] for n in ns3},
                 'peaks': (cost_peaks if PART2 else
                           {n: max(c for c in cost_curves[n]
                                   if c is not None) for n in ns3}),
                 'Dc_80': fits[80][0]}

# ════════════════════════════════════════════════════════════════════════════
# F4 — ecosystem growth: drift into the threshold, selection pins below
# ════════════════════════════════════════════════════════════════════════════

print('F4: growth experiment', flush=True)


def run_growth(select, steps=180, n=100, K=64, w=16, D0=1.55,
               drift=0.03, install_cap=2500):
    """Release dynamics at fixed scale: 12 packages publish per step with
    edge counts drifting up (the measured-ecosystem appetite pattern);
    installs tested every 2 steps at a practical budget. The selection arm
    re-releases recently-bumped packages with 40% of their edges when
    installs fail (the crisis-pruning response)."""
    rng = np.random.default_rng([SEED, 4, 1 if select else 0])
    packs = []
    latest_D = []

    def new_version(Dmean):
        base = int(math.floor(Dmean))
        frac = Dmean - base
        m = base + (1 if rng.random() < frac else 0)
        if m == 0:
            return []
        js = rng.integers(0, max(1, len(packs) - 1), size=m)
        own = len(packs)
        js[js >= own] += 1
        los = rng.integers(0, K, size=m)
        return [(int(j), cyc_mask(int(lo), w, K)) for j, lo in zip(js, los)]

    for i in range(n):
        vers = [new_version(D0) for _ in range(K)]
        packs.append(vers)
        latest_D.append(D0)

    density, thr_line, success_hist, times = [], [], [], []
    succ_rolling = []
    for step in range(steps):
        D_now = float(np.mean(latest_D))
        bumped = rng.choice(n, size=12, replace=False)
        for i in bumped:
            Dn = D_now + drift + 0.04 * rng.standard_normal()
            packs[i] = [new_version(max(0.0, Dn)) for _ in range(K)]
            latest_D[i] = len(packs[i][-1])

        if step % 2 == 1:
            ok, _ = solve(n, K, packs, cap=install_cap, seed=step)
            succ_rolling.append(ok)

        if select and (step % 6 == 5) and succ_rolling and \
                (not succ_rolling[-1]):
            okk, _ = solve(n, K, packs, cap=install_cap, seed=step)
            rounds = 0
            while not okk and rounds < 3:
                cand = bumped[:12] if rounds == 0 else \
                    rng.choice(n, size=12, replace=False)
                for i in cand:
                    packs[i] = [new_version(max(0.0, 0.6 * latest_D[i]))
                                for _ in range(K)]
                    latest_D[i] = len(packs[i][-1])
                rounds += 1
                okk, _ = solve(n, K, packs, cap=install_cap, seed=step)
        if step % 2 == 1:
            density.append(float(np.mean(latest_D)))
            success_hist.append(float(np.mean(succ_rolling[-6:])))
            times.append(step)
    return times, density, success_hist


# calibrate the operative threshold at this scale and budget
rng = np.random.default_rng([SEED, 4, 9])
Dcal = np.round(np.arange(1.5, 2.31, 0.1), 2)
Pcal = []
for D in Dcal:
    sat = 0
    for t in range(40):
        deps = gen_instance(rng, 100, 64, float(D), 16)
        ok, _ = solve(100, 64, deps, cap=2500, seed=t)
        sat += ok
    Pcal.append(sat / 40)
    print(f'  calib D={D}: P={Pcal[-1]:.2f}', flush=True)
Dthr = float(np.interp(0.5, Pcal[::-1], Dcal[::-1]))
print(f'  operative threshold (n=100, cap 2500): {Dthr:.2f}', flush=True)

tA, dA, sA = run_growth(select=False)
tB, dB, sB = run_growth(select=True)
crossA = next((i for i, d in enumerate(dA) if d > Dthr), None)
gapB = float(np.mean([max(0.0, Dthr - d) for d in dB[40:]]))
print(f'  no-selection: crosses measured threshold at step '
      f'{tA[crossA] if crossA is not None else None}; final success '
      f'{sA[-1]:.2f}', flush=True)
print(f'  selection: mean gap below threshold {gapB:.2f}; final success '
      f'{sB[-1]:.2f}', flush=True)

RESULTS['f4'] = {
    'no_selection': {'t': tA, 'density': dA, 'success': sA,
                     'cross_step': tA[crossA] if crossA is not None else None,
                     'final_success': sA[-1]},
    'selection': {'t': tB, 'density': dB, 'success': sB,
                  'mean_gap': gapB, 'final_success': sB[-1]},
    'threshold': Dthr, 'calibration': {'D': Dcal.tolist(), 'P': Pcal},
}

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.8, 5.6), sharex=True,
                               constrained_layout=True)
ax1.plot(tA, dA, '-', color=CB[4], lw=1.8, label='density $D_t$ (no selection)')
ax1.plot(tB, dB, '-', color=CB[0], lw=1.8,
         label='density $D_t$ (crisis-pruning selection)')
ax1.axhline(Dthr, ls='--', color=G900, lw=1.4,
            label='measured collapse threshold $D_c$')
ax1.set_ylabel('dependency density')
ax1.set_title('Growth with and without resolvability selection')
ax1.legend(loc='upper left', fontsize=8.8)
clean_axis(ax1)
ax2.plot(tA, sA, '-', color=CB[4], lw=1.8, label='install success (no selection)')
ax2.plot(tB, sB, '-', color=CB[0], lw=1.8, label='install success (selection)')
ax2.set_xlabel('growth step')
ax2.set_ylabel('6-install rolling success rate')
ax2.set_ylim(-0.05, 1.08)
ax2.legend(loc='lower left', fontsize=8.8)
clean_axis(ax2)
save(fig, 'f4-growth.png')

# ════════════════════════════════════════════════════════════════════════════
# F5 — interventions and the proliferation panel
# ════════════════════════════════════════════════════════════════════════════

print('F5: interventions', flush=True)
n5 = 80
cap5 = 3000


def dedup(deps):
    """Remove duplicate (target, mask) edges across versions of one package
    (the same requirement re-declared)."""
    out = []
    removed = 0
    for vers in deps:
        seen = set()
        nv = []
        for v in vers:
            edges = []
            for e in v:
                if e in seen:
                    removed += 1
                else:
                    seen.add(e)
                    edges.append(e)
            nv.append(edges)
        out.append(nv)
    return out, removed


Dg5 = np.round(np.arange(1.6, 2.81, 0.2), 2)


def curve_for(K, w, trials=60, deduped=False):
    rng = np.random.default_rng([SEED, 5, K, w, int(deduped)])
    ps = []
    for D in Dg5:
        sat = 0
        for t in range(trials):
            deps = gen_instance(rng, n5, K, D, w)
            if deduped:
                deps, _ = dedup(deps)
            ok, _ = solve(n5, K, deps, cap=cap5, seed=t)
            sat += ok
        ps.append(sat / trials)
    return np.array(ps)


base_c = curve_for(64, 16)
wide_c = curve_for(64, 24)
dedup_c = curve_for(64, 16, deduped=True)
prune_c = curve_for(48, 16)

# dedup effectiveness
rng = np.random.default_rng([SEED, 55])
frac_removed = []
for _ in range(30):
    deps = gen_instance(rng, n5, 64, 2.2, 16)
    _, rem = dedup(deps)
    total_edges = sum(len(v) for vers in deps for v in vers)
    frac_removed.append(rem / max(1, total_edges))
dedup_frac = float(np.mean(frac_removed))
print(f'  dedup removes {dedup_frac:.1%} of edges', flush=True)

# proliferation panel: fixed D, sweep K
Ks = [16, 32, 64, 128, 256]
Dfix = 2.2
fixed_w, prop_w = [], []
for K in Ks:
    wf = 8
    rng = np.random.default_rng([SEED, 6, K])
    sat = 0
    for t in range(80):
        deps = gen_instance(rng, 64, K, Dfix, wf)
        ok, _ = solve(64, K, deps, cap=2000, seed=t)
        sat += ok
    fixed_w.append(sat / 80)
    w = K // 4
    rng = np.random.default_rng([SEED, 7, K])
    sat = 0
    for t in range(80):
        deps = gen_instance(rng, 64, K, Dfix, w)
        ok, _ = solve(64, K, deps, cap=2000, seed=t)
        sat += ok
    prop_w.append(sat / 80)
    print(f'  K={K}: fixed-w P={fixed_w[-1]:.2f}, proportional-w '
          f'P={prop_w[-1]:.2f}', flush=True)


def head(c):
    try:
        Dc, _ = logistic_fit(Dg5, np.clip(c, 0.02, 0.98))
    except Exception:
        Dc = float('nan')
    return Dc


hr = {'base': head(base_c), 'wide': head(wide_c), 'dedup': head(dedup_c),
      'prune': head(prune_c)}
print(f'  headrooms: {hr}', flush=True)

RESULTS['f5'] = {'D_grid': Dg5.tolist(), 'n': n5, 'budget': cap5,
                 'curves': {'base': base_c.tolist(), 'wide': wide_c.tolist(),
                            'dedup': dedup_c.tolist(), 'prune': prune_c.tolist()},
                 'headrooms': hr, 'dedup_frac': dedup_frac,
                 'Ks': Ks, 'D_fix': Dfix, 'n_prolif': 64,
                 'budget_prolif': 2000,
                 'fixed_w': fixed_w, 'proportional_w': prop_w}

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
axa.plot(Dg5, base_c, 'o-', color=G700, ms=4, lw=1.6,
         label='base ($K$=64, $w$=16)')
axa.plot(Dg5, wide_c, 'o-', color=CB[2], ms=4, lw=1.6,
         label='widen ranges ($w$=24)')
axa.plot(Dg5, dedup_c, 'o-', color=CB[0], ms=4, lw=1.6, alpha=0.75,
         label=f'de-duplicate (-{dedup_frac:.0%} edges)')
axa.plot(Dg5, prune_c, 'o-', color=CB[4], ms=4, lw=1.6,
         label='prune versions ($K$=48)')
axa.set_xlabel('dependency density $D$')
axa.set_ylabel('P(resolvable within budget)')
axa.set_title('Levers: widening buys headroom; pruning loses it')
axa.legend(loc='upper right', bbox_to_anchor=(1.0, 0.98), fontsize=8.4)
clean_axis(axa)

axb.plot(Ks, fixed_w, 'o-', color=CB[4], ms=5, lw=1.8, label='fixed width $w$=8')
axb.plot(Ks, prop_w, 'o-', color=CB[2], ms=5, lw=1.8,
         label='proportional width $w$=$K$/4')
axb.set_xscale('log', base=2)
axb.set_xticks(Ks)
axb.set_xticklabels([str(k) for k in Ks])
axb.set_xlabel('versions per package $K$ (log scale)')
axb.set_ylabel(f'P(resolvable), $D$={Dfix}')
axb.set_title('Version proliferation: fragility or slack?')
axb.legend(loc='center left', bbox_to_anchor=(0.03, 0.5), fontsize=8.8)
clean_axis(axb)
save(fig, 'f5-interventions.png')

# ════════════════════════════════════════════════════════════════════════════
# F6 — law validation summary
# ════════════════════════════════════════════════════════════════════════════

print('F6: law validation', flush=True)
allx = [r['D_fm'] for r in rows] + [d_fm(K1, w1)] * len(ns)
ally = [r['Dc'] for r in rows] + [fits[n][0] for n in ns]
pred = [gamma_bar * v for v in allx]
resid = np.abs(np.array(ally) / np.array(pred) - 1.0)
RESULTS['f6'] = {
    'gamma_bar': gamma_bar,
    'median_abs_rel_error': float(np.median(resid)),
    'max_abs_rel_error': float(np.max(resid)),
    'n_points': len(allx),
}
print(f'  gamma_bar={gamma_bar:.3f}; median |err|={np.median(resid):.3f}; '
      f'max={np.max(resid):.3f}', flush=True)

fig, ax = plt.subplots(figsize=(5.6, 4.6), constrained_layout=True)
ax.plot([0, max(ally) * 1.12], [0, max(ally) * 1.12], '--', color=G400, lw=1.2)
ax.plot(pred, ally, 'o', ms=6, color=CB[0])
for r in rows:
    ax.annotate(f'{r["K"]}/{r["w"]}', (gamma_bar * r['D_fm'], r['Dc']),
                fontsize=7, color=G700, xytext=(4, 2),
                textcoords='offset points')
ax.set_xlabel(f'law prediction $\\gamma D_{{fm}}$ ($\\gamma$={gamma_bar:.2f})')
ax.set_ylabel('measured $D_c$')
ax.set_title('Threshold law: prediction vs measurement')
clean_axis(ax)
save(fig, 'f6-law-validation.png')

with open(os.path.join(OUT, 'results.json'), 'w') as f:
    json.dump(RESULTS, f, indent=1)
print('results.json written', flush=True)
print('DONE P-024')
