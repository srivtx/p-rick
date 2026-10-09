#!/usr/bin/env python3
"""P-021 simulation: epidemic thresholds for dependency-borne compromise.

Synthetic package-ecosystem DAGs with power-law dependents-per-package,
vectorized discrete-time SIR (recovery before transmission), six figures:

  f1-degree-distributions.png  CCDF of dependents per package, exponent family
  f2-phase-transition.png      outbreak probability vs T, three registry sizes
  f3-threshold-heatmap.png     outbreak probability over (exponent, T) + law
  f4-immunization.png          mean compromised fraction vs pinned fraction
  f5-interventions.png         I(t): baseline / patch / lockfile / registry yank
  f6-law-validation.png        GW survival prediction vs measured outbreak probability

Theory under test (correct for DAGs where the spectral radius is identically
zero by nilpotence): the branching-mean law  R0^v = T * <d>  with threshold
T_c = 1/<d>; per-edge T is made EXACT via beta = T*gamma/((1-gamma)(1-T)).

Writes results.json with headline numbers cited in the paper.
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AGENT_OUT = '/home/z/my-project/repos/p-rick/figures/p-021'
if os.path.isdir('/home/z/my-project/repos/p-rick'):
    os.makedirs(AGENT_OUT, exist_ok=True)
    OUT = AGENT_OUT
else:
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'figures', 'p-021')
    os.makedirs(OUT, exist_ok=True)

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

ARANGE = None


def build_ecosystem(N, gamma, kmax, rng):
    """Acyclic registry: node 0 oldest; edge (src -> dst) = 'src depends on
    dst', src younger. Infection flows dst -> src, so the infection matrix is
    strictly triangular (nilpotent: spectral radius exactly 0 — the spectral
    threshold is vacuous; see paper Proposition 1). Dependents counts drawn
    iid from P(k) ∝ k^-gamma (age-decoupled popularity), capped by the number
    of younger nodes."""
    global ARANGE
    if ARANGE is None or len(ARANGE) < N:
        ARANGE = np.arange(max(N, 2))
    ks = np.arange(1, kmax + 1)
    w = ks.astype(float) ** (-gamma)
    cdf = np.cumsum(w)
    cdf /= cdf[-1]
    kin = ks[np.searchsorted(cdf, rng.random(N))]
    avail = (N - 1) - np.arange(N)
    kin = np.minimum(kin, avail)
    src_parts, dst_parts = [], []
    for j in range(N - 1):
        k = int(kin[j])
        if k <= 0:
            continue
        k = min(k, N - 1 - j)
        sources = rng.choice(ARANGE[j + 1:N], size=k, replace=False)
        src_parts.append(sources)
        dst_parts.append(np.full(k, j, dtype=np.int64))
    if not src_parts:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    return np.concatenate(src_parts), np.concatenate(dst_parts)


def beta_from_T(T, gamma):
    """Per-step infectivity making T the EXACT per-edge eventual transmission
    probability under recovery-first discrete SIR with per-step recovery gamma:
    P(edge fires) = beta(1-gamma)/(gamma + beta(1-gamma))."""
    return T * gamma / ((1.0 - gamma) * (1.0 - T))


def run_sir(src, dst, N, beta, gamma, rng, seed=None, max_t=300,
            track=False, intervene=None):
    state = np.zeros(N, dtype=np.int8)   # 0=S 1=I 2=R
    if seed is None:
        seed = int(rng.integers(N))
    state[seed] = 1
    E = len(src)
    frozen = np.zeros(E, dtype=bool)
    It = [1]
    for t in range(max_t):
        if intervene is not None:
            if 'pin_at' in intervene and t == intervene['pin_at']:
                frozen |= (rng.random(E) < intervene.get('pin_edges_p', 0.2))
            if 'yank_at' in intervene and t == intervene['yank_at']:
                frozen |= (dst == seed)
            if 'gamma2_at' in intervene and t == intervene['gamma2_at']:
                gamma = gamma * 2.0
        inf = state == 1
        if inf.any():
            rec = rng.random(N) < gamma
            state[inf & rec] = 2
        m = (state[dst] == 1) & (state[src] == 0) & (~frozen)
        if m.any():
            u = rng.random(int(m.sum())) < beta
            new = src[m][u]
            if len(new):
                state[new] = 1
        It.append(int((state == 1).sum()))
        if not (state == 1).any():
            break
    attack = float((state != 0).sum()) / N
    return attack, (np.array(It) if track else None)


def outbreak_stats(src, dst, N, T, gamma, rng, seeds, takeoff=0.01):
    beta = beta_from_T(T, gamma)
    att, out = 0.0, 0
    for s in range(seeds):
        a, _ = run_sir(src, dst, N, beta, gamma, rng, max_t=400)
        att += a
        out += (a > takeoff)
    return att / seeds, out / seeds


def gw_survival(dst, N, T, iters=800):
    """Galton-Watson survival prediction from the EMPIRICAL dependents
    distribution: extinction q* solves q = f(1-T+Tq) with f the pgf."""
    kin = np.bincount(dst, minlength=N)
    Pk = np.bincount(kin, minlength=int(kin.max()) + 1).astype(float)
    Pk /= Pk.sum()
    kk = np.arange(len(Pk))
    q = 0.9
    for _ in range(iters):
        s = 1.0 - T + T * q
        qn = float(np.sum(Pk * s ** kk))
        if abs(qn - q) < 1e-12:
            q = qn
            break
        q = qn
    return 1.0 - q


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


def main():
    rng = np.random.default_rng(20261007)
    GAMMA_EPID = 0.20
    RESULTS = {}

    # ── F1: degree families ────────────────────────────────────────────────
    print('== F1 ==', flush=True)
    F1_FAMILY = [1.3, 1.8, 2.3, 3.0]
    F1_N = 20000
    f1_data = {}
    for g in F1_FAMILY:
        kmax = min(max(int(F1_N ** (1.0 / (g - 1.0))), 8), 4000)
        src, dst = build_ecosystem(F1_N, g, kmax, rng)
        kin = np.bincount(dst, minlength=F1_N)
        f1_data[g] = (kin, len(src), len(src) / F1_N)
        print(f'  gamma={g} kmax={kmax} edges={len(src)} mean_d={len(src)/F1_N:.2f}', flush=True)
    RESULTS['f1'] = {str(g): {'edges': int(f1_data[g][1]),
                              'mean_dependents': float(f1_data[g][2])}
                     for g in F1_FAMILY}

    # ── F2: outbreak probability vs N (gamma_d = 1.7) ──────────────────────
    print('== F2 ==', flush=True)
    F2_GAMMA = 1.7
    F2_SIZES = [2000, 8000, 32000]
    F2_T = np.linspace(0.02, 0.50, 15)
    f2_prob, f2_mean, f2_seeds = {}, {}, {}
    for N in F2_SIZES:
        kmax = min(N // 4, 8000)
        src, dst = build_ecosystem(N, F2_GAMMA, kmax, rng)
        md = len(dst) / N
        f2_mean[N] = md
        seeds = 60 if N <= 8000 else 28
        f2_seeds[N] = seeds
        probs = []
        for T in F2_T:
            _, p = outbreak_stats(src, dst, N, T, GAMMA_EPID, rng, seeds)
            probs.append(p)
        f2_prob[N] = np.array(probs)
        print(f'  N={N} mean_d={md:.1f} Tc={1/md:.3f} P={np.round(probs, 2)}', flush=True)
    RESULTS['f2'] = {str(N): {'mean_dependents': float(f2_mean[N]),
                              'T_c_theory': float(1.0 / f2_mean[N]),
                              'seeds': f2_seeds[N]} for N in F2_SIZES}

    # ── F3: heatmap (gamma_d, T) of outbreak probability ───────────────────
    print('== F3 ==', flush=True)
    F3_N = 20000
    F3_GAMMAS = [1.6, 1.9, 2.2, 2.5, 2.8, 3.1]
    F3_T = np.array([0.02, 0.04, 0.07, 0.10, 0.15, 0.20, 0.28, 0.36, 0.45, 0.55])
    f3_grid = np.zeros((len(F3_GAMMAS), len(F3_T)))
    f3_mean = []
    f3_graphs = {}
    for gi, g in enumerate(F3_GAMMAS):
        src, dst = build_ecosystem(F3_N, g, 2500, rng)
        md = len(dst) / F3_N
        f3_mean.append(md)
        f3_graphs[gi] = (src, dst, md)
        for ti, T in enumerate(F3_T):
            _, p = outbreak_stats(src, dst, F3_N, T, GAMMA_EPID, rng, 30)
            f3_grid[gi, ti] = p
        print(f'  gamma={g} mean_d={md:.1f} P={np.round(f3_grid[gi], 2)}', flush=True)
    RESULTS['f3'] = {'gammas': F3_GAMMAS, 'T': F3_T.tolist(),
                     'mean_dependents': [float(m) for m in f3_mean],
                     'outbreak_prob': f3_grid.tolist()}

    # ── F4: immunization (gamma_d = 1.9) ───────────────────────────────────
    print('== F4 ==', flush=True)
    F4_N, F4_T = 20000, 0.50
    F4_P = np.linspace(0.0, 0.92, 20)
    src, dst, md19 = f3_graphs[0]
    R0_F4 = F4_T * md19
    dep = np.bincount(dst, minlength=F4_N).astype(float)
    twohop = np.bincount(dst, weights=dep[src], minlength=F4_N)
    noisy = dep * (1.0 + 0.30 * rng.standard_normal(F4_N))
    strategies = {
        'random packages': rng.permutation(F4_N),
        'noisy popularity signal': np.argsort(-noisy),
        'exact dependents count': np.argsort(-dep),
        '2-hop cascade score': np.argsort(-twohop),
    }
    f4_curves = {}
    for name, order in strategies.items():
        ys = []
        for p in F4_P:
            n_imm = int(round(p * F4_N))
            keep = np.ones(F4_N, dtype=bool)
            keep[order[:n_imm]] = False
            m = keep[src] & keep[dst]
            a, _ = outbreak_stats(src[m], dst[m], F4_N, F4_T, GAMMA_EPID,
                                  rng, 26)
            ys.append(a)
        f4_curves[name] = np.array(ys)
        print(f'  {name}: {np.round(ys, 3)}', flush=True)
    RESULTS['f4'] = {'R0': float(R0_F4), 'mean_dependents': float(md19),
                     'herd_random': float(max(0.0, 1.0 - 1.0 / R0_F4)),
                     'p': F4_P.tolist(),
                     'curves': {k: v.tolist() for k, v in f4_curves.items()}}

    # ── F5: temporal interventions, conditioned on outbreak seeds ─────────
    print('== F5 ==', flush=True)
    F5_T, F5_SEEDS, F5_MAXT = 0.45, 16, 120
    src, dst, md_f5 = f3_graphs[1]
    beta = beta_from_T(F5_T, GAMMA_EPID)
    dep_f5 = np.bincount(dst, minlength=F4_N)
    lo, hi = np.percentile(dep_f5[dep_f5 > 0], [75, 99.5])
    hubpool = np.where((dep_f5 >= lo) & (dep_f5 <= hi))[0]
    print(f'  hub pool (p75-p99.5): {len(hubpool)} packages', flush=True)
    # paired design: every run of a given seed uses the same rng stream, so
    # baseline and interventions see identical draws until intervention time
    takeoff_seeds = []
    tries = 0
    while len(takeoff_seeds) < F5_SEEDS and tries < 120:
        tries += 1
        sd = int(rng.choice(hubpool))
        a, _ = run_sir(src, dst, F4_N, beta, GAMMA_EPID,
                       np.random.default_rng(100003 * sd + 17), seed=sd,
                       max_t=F5_MAXT)
        if a > 0.01:
            takeoff_seeds.append(sd)
    print(f'  screened {tries} hub seeds -> {len(takeoff_seeds)} outbreaks', flush=True)
    runs = {
        'patch rate doubled': 'gamma2_at',
        'lockfiles pin 20% of edges': 'pin_at',
        'registry yank of seed': 'yank_at',
    }
    F5_TS = [0, 1, 2, 4, 7, 10, 15, 25]
    # paired runs: same per-seed rng stream for baseline and every intervention
    base_attack = []
    for sd in takeoff_seeds:
        a, _ = run_sir(src, dst, F4_N, beta, GAMMA_EPID,
                       np.random.default_rng(100003 * sd + 17), seed=sd,
                       max_t=F5_MAXT)
        base_attack.append(a)
    base_attack = float(np.mean(base_attack))
    print(f'  baseline mean attack = {base_attack:.4f}', flush=True)
    f5_curves = {}
    for name, key in runs.items():
        ys = []
        for t in F5_TS:
            att = []
            for sd in takeoff_seeds:
                itv = {key: t}
                if key == 'pin_at':
                    itv['pin_edges_p'] = 0.20
                a, _ = run_sir(src, dst, F4_N, beta, GAMMA_EPID,
                               np.random.default_rng(100003 * sd + 17),
                               seed=sd, max_t=F5_MAXT, intervene=itv)
                att.append(a)
            ys.append(float(np.mean(att)))
        f5_curves[name] = np.array(ys)
        print(f"  {name}: {np.round(ys, 4)}", flush=True)
    RESULTS['f5'] = {'baseline_attack': base_attack,
                     't_grid': F5_TS,
                     'curves': {k: v.tolist() for k, v in f5_curves.items()}}
    RESULTS['f5']['mean_dependents'] = float(md_f5)
    RESULTS['f5']['R0'] = float(F5_T * md_f5)

    # ── F6: growth-based R0 vs branching theory ────────────────────────────
    print('== F6 ==', flush=True)
    F6_N = 10000
    f6_gw, f6_meas, f6_cfg = [], [], []
    for g in [1.6, 1.9, 2.4, 3.1]:
        src, dst = build_ecosystem(F6_N, g, 2500, rng)
        md = len(dst) / F6_N
        for T in [0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50]:
            p_gw = gw_survival(dst, F6_N, T)
            _, p_m = outbreak_stats(src, dst, F6_N, T, GAMMA_EPID, rng, 60)
            f6_gw.append(p_gw)
            f6_meas.append(p_m)
            f6_cfg.append((g, T))
            print(f'  g={g} T={T}: GW={p_gw:.3f} meas={p_m:.3f} (mean_d={md:.1f})', flush=True)
    ratios = [m / g for m, g in zip(f6_meas, f6_gw) if g > 0.05 and m > 0]
    RESULTS['f6'] = {'gw': [float(x) for x in f6_gw],
                     'measured': [float(x) for x in f6_meas],
                     'configs': [list(c) for c in f6_cfg],
                     'drag_theta': float(np.median(ratios)) if ratios else None}

    # ── F6b: age-coupling penalty kappa ─────────────────────────────────────
    print('== F6b ==', flush=True)
    src_r, dst_r, _ = f3_graphs[1]
    ks = np.arange(1, 2501)
    wc = ks.astype(float) ** (-1.9)
    cdfc = np.cumsum(wc)
    cdfc /= cdfc[-1]
    kin = ks[np.searchsorted(cdfc, rng.random(F3_N))]
    kin = np.sort(kin)[::-1]
    kin = np.minimum(kin, (F3_N - 1) - np.arange(F3_N))
    sp, dp = [], []
    for j in range(F3_N - 1):
        k = int(kin[j])
        if k <= 0:
            continue
        k = min(k, F3_N - 1 - j)
        s = rng.choice(ARANGE[j + 1:F3_N], size=k, replace=False)
        sp.append(s)
        dp.append(np.full(k, j, dtype=np.int64))
    src_a = np.concatenate(sp)
    dst_a = np.concatenate(dp)
    age_ratios = []
    for T in [0.30, 0.45, 0.55]:
        _, pr = outbreak_stats(src_r, dst_r, F3_N, T, GAMMA_EPID, rng, 80)
        _, pa = outbreak_stats(src_a, dst_a, F3_N, T, GAMMA_EPID, rng, 80)
        if pr > 0.05 and pa > 0:
            age_ratios.append(pa / pr)
            print(f'  T={T}: P_random={pr:.3f} P_agecoupled={pa:.3f} ratio={pa/pr:.2f}', flush=True)
    RESULTS['age_survival_ratio'] = [float(r) for r in age_ratios]

    # ══════════════════════ figures ════════════════════════════════════════
    # F1
    fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
    for i, g in enumerate(F1_FAMILY):
        kin = f1_data[g][0]
        ksrt = np.sort(kin[kin > 0])
        ccdf = 1.0 - np.arange(1, len(ksrt) + 1) / len(ksrt)
        ax.plot(ksrt, np.maximum(ccdf, 0.6 / len(ksrt)), color=CB[i], lw=1.8,
                label=f'$\\gamma_d$={g}  ($\\langle d\\rangle$={f1_data[g][2]:.1f})')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('dependents per package $k$')
    ax.set_ylabel('$P(K \\geq k)$')
    ax.set_title('Dependent-count distributions of the registry family')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    clean_axis(ax, grid=False)
    ax.yaxis.grid(True, alpha=0.12, color=G400)
    save(fig, 'f1-degree-distributions.png')

    # F2 (rev 1.1: threshold labels live in the legend, not as rotated
    # in-plot text that collides with the theory lines and curves)
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
    clean_axis(ax)
    save(fig, 'f2-phase-transition.png')

    # F3
    fig, ax = plt.subplots(figsize=(6.8, 4.6), constrained_layout=True)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        'epi', ['#FFFFFF', '#CFE6F5', '#5FA8D3', '#1B6CA8', '#0B3C5D'])
    im = ax.imshow(f3_grid, cmap=cmap, aspect='auto', origin='lower',
                   extent=[F3_T[0], F3_T[-1], F3_GAMMAS[0] - 0.15,
                           F3_GAMMAS[-1] + 0.15], vmin=0, vmax=1.0)
    g_dense = np.linspace(F3_GAMMAS[0], F3_GAMMAS[-1], 200)
    T_dense = np.interp(g_dense, F3_GAMMAS, 1.0 / np.array(f3_mean))
    ax.plot(T_dense, g_dense, color='#CC3311', lw=2.0, ls='--')
    ax.text(0.03, 3.02, '$R_0^v = T\\,\\langle d\\rangle = 1$\n(branching law, conservative)',
            fontsize=9, color='#CC3311', fontweight='bold', va='top')
    ax.set_xlabel('per-edge transmissibility $T$')
    ax.set_ylabel('degree exponent $\\gamma_d$')
    ax.set_title('Outbreak regime: branching law vs simulation')
    ax.set_xticks(np.round(np.linspace(0.02, 0.55, 6), 2))
    cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.03)
    cb.set_label('outbreak probability', fontsize=9)
    cb.outline.set_visible(False)
    save(fig, 'f3-threshold-heatmap.png')

    # F4
    fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
    for i, name in enumerate(strategies):
        ax.plot(F4_P * 100, f4_curves[name] * 100, color=CB[i], lw=2.0,
                marker='o', ms=3.5, label=name)
    pc = RESULTS['f4']['herd_random'] * 100
    ax.axvline(pc, color=G700, ls=':', lw=1.3)
    ymax = max(v.max() for v in f4_curves.values()) * 100
    ax.text(pc + 1.2, ymax * 0.55, f'random herd budget\n$p_c = 1-1/R_0^v$ = {pc:.0f}%',
            fontsize=8.5, color=G700)
    ax.set_xlabel('pinned (immunized) fraction of packages — %')
    ax.set_ylabel('mean compromised fraction — %')
    ax.set_ylim(0, ymax * 1.25)
    ax.set_title('Cascade-aware pinning dominates random pinning')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title='targeting', fontsize=8.8)
    clean_axis(ax)
    save(fig, 'f4-immunization.png')

    # F5: response-time curves
    fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
    ax.axhline(base_attack * 100, color=G400, ls='--', lw=1.4)
    ax.text(21.5, base_attack * 100 + 0.9,
            f'no action: {base_attack*100:.1f}% compromised', fontsize=8.5,
            color=G700)
    for i, (name, ys) in enumerate(f5_curves.items()):
        ax.plot(F5_TS, ys * 100, color=CB[i], lw=2.0, marker='o', ms=4,
                label=name)
    ax.set_xlabel('intervention step (registry response time)')
    ax.set_ylabel('mean final compromised fraction — %')
    ax.set_title('The response window closes fast: act early or watch')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8.8)
    clean_axis(ax)
    save(fig, 'f5-interventions.png')

    # F6: survival scatter
    fig, ax = plt.subplots(figsize=(5.6, 4.6), constrained_layout=True)
    colors = {1.6: CB[0], 1.9: CB[1], 2.4: CB[2], 3.1: CB[3]}
    for g in colors:
        xs, ys = [], []
        for (gg, T), x, y in zip(f6_cfg, f6_gw, f6_meas):
            if gg == g:
                xs.append(x)
                ys.append(y)
        if xs:
            ax.scatter(xs, ys, s=46, color=colors[g], alpha=0.9,
                       edgecolors='white', linewidths=0.8, zorder=3,
                       label=f'$\\gamma_d$={g}')
    ax.plot([0, 1], [0, 1], color=G400, ls='--', lw=1.2, zorder=2)
    if RESULTS['f6']['drag_theta']:
        th = RESULTS['f6']['drag_theta']
        ax.plot([0, 1], [0, th], color='#CC3311', ls=':', lw=1.6, zorder=2)
        ax.text(0.55, 0.12, f'extinction drag\n$\\theta \\approx {th:.2f}$',
                fontsize=8.5, color='#CC3111', va='bottom')
    ax.set_xlabel('Galton–Watson survival prediction')
    ax.set_ylabel('measured outbreak probability')
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_title('Branching law: directional, with a measured drag')
    ax.text(0.05, 0.95, '$y = x$', fontsize=9, color=G700)
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    clean_axis(ax, grid=True)
    ax.xaxis.grid(True, alpha=0.12, color=G400)
    save(fig, 'f6-law-validation.png')

    with open(os.path.join(OUT, 'results.json'), 'w') as f:
        json.dump(RESULTS, f, indent=1)
    print('DONE — results.json written', flush=True)


if __name__ == '__main__':
    main()
