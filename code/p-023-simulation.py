#!/usr/bin/env python3
"""P-023 simulation: generation loss — semantic drift of vector corpora.

Model: encoder upgrades are a per-generation transform
    phi_{g+1}(x) = normalize(R_g phi_g(x) + nu * eps)
where R_g is a global Givens rotation by angle delta (the isometry channel)
and eps is per-object jitter (the distortion channel).

LAW under test:  E[cos(phi_0(x), phi_g(x))] = lambda^g with
    lambda = lambda_rot * lambda_noise,
    lambda_rot = 1 - 2(1 - cos delta)/d   (dimension mercy)
    lambda_noise = (1 + nu^2)^(-1/2)
Anchoring: persistent landmarks re-embedded each generation give an
orthogonal Procrustes alignment A applied to the stale index, removing the
rotational channel exactly (up to finite-L estimation error ~ c/sqrt(L)).

Figures:
  f1-law-validation.png   D(g) = 1 - lambda^g across channels and levels
  f2-recall.png           recall@10: stale / anchored / re-embedded
  f3-decomposition.png    anchored + stale recall heatmaps over (nu, delta)
  f4-landmarks.png        recall vs landmark count L + 1/sqrt(L) law
  f5-dimension.png        pure-rotation drift vs dimension: kappa = 2(1-c)/d

Writes results.json with headline numbers cited in the paper.
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AGENT_OUT = '/home/z/my-project/repos/p-rick/figures/p-023'
if os.path.isdir('/home/z/my-project/repos/p-rick'):
    os.makedirs(AGENT_OUT, exist_ok=True)
    OUT = AGENT_OUT
else:
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'figures', 'p-023')
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

RESULTS = {}


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
# Corpus, encoder chain, alignment, retrieval
# ════════════════════════════════════════════════════════════════════════════

def unit_rows(X):
    return X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)


def make_corpus(M, n_clusters, d, sigma, rng):
    """sigma = TOTAL jitter norm (not per-coordinate): items sit at cosine
    ~1/(1+sigma^2) from their cluster center."""
    centers = unit_rows(rng.standard_normal((n_clusters, d)))
    per = M // n_clusters
    X = np.empty((per * n_clusters, d))
    for c in range(n_clusters):
        blk = c * per
        X[blk:blk + per] = centers[c] + sigma / np.sqrt(d) * rng.standard_normal((per, d))
    return unit_rows(X), centers, per


def givens(X, i, j, delta):
    """Rotate coordinates (i, j) by angle delta — a global isometry."""
    c, s = np.cos(delta), np.sin(delta)
    Y = X.copy()
    xi = X[:, i].copy()
    xj = X[:, j].copy()
    Y[:, i] = c * xi - s * xj
    Y[:, j] = s * xi + c * xj
    return Y


def step_transform(X, rng, delta, nu):
    """One encoder generation: global rotation by delta in a random plane +
    per-object jitter nu (renormalized). delta=0 or nu=0 disables a channel."""
    N, d = X.shape
    if delta > 0:
        i, j = rng.choice(d, size=2, replace=False)
        X = givens(X, i, j, delta)
    if nu > 0:
        X = X + nu / np.sqrt(d) * rng.standard_normal(X.shape)
        X = unit_rows(X)
    return X


def procrustes(X0, Y):
    """Orthogonal A minimizing sum ||A x0 - y||^2 over landmark rows.
    Returns A (d x d). Self-checked against an exact-rotation case."""
    C = X0.T @ Y                      # sum x_l y_l^T
    U, S, Vt = np.linalg.svd(C)
    return Vt.T @ U.T


def topk_indices(Q, X, k=10):
    """Row-wise top-k indices by dot product (Q . X^T)."""
    S = Q @ X.T
    return np.argpartition(-S, k, axis=1)[:, :k]


def recall_at_k(qt, xt, gold, k=10):
    """Mean |gold_i ∩ topk_i| / k for queries qt against index xt."""
    pred = topk_indices(qt, xt, k)
    hits = 0
    for r in range(len(qt)):
        hits += len(set(pred[r]) & set(gold[r]))
    return hits / (k * len(qt))


def drift_D(cur, stale):
    """D(g) = 1 - mean cos(phi_g(x), phi_0(x))."""
    return float(1.0 - np.mean((cur * stale).sum(1)))


# ════════════════════════════════════════════════════════════════════════════
# Procrustes self-check (pure rotation, noiseless)
# ════════════════════════════════════════════════════════════════════════════

rng0 = np.random.default_rng(1)
_X = unit_rows(rng0.standard_normal((512, 64)))
_Xr = givens(_X, 3, 17, 0.7)
_A = procrustes(_X, _Xr)
_err = float(np.abs(_A @ _X.T - _Xr.T).max())
print(f'procrustes self-check max err: {_err:.2e}', flush=True)
assert _err < 1e-8, 'Procrustes convention wrong — flip U/V'


# ════════════════════════════════════════════════════════════════════════════
# Experiment driver
# ════════════════════════════════════════════════════════════════════════════

def run_chain(M=5000, n_clusters=25, d=256, sigma=0.7, G=16,
              delta=0.0, nu=0.0, n_queries=250, anchor_L=None, seed=7):
    """Evolve corpus + queries through G generations. Returns dict with
    D(g) series and recall@10 series for stale / anchored systems."""
    rng = np.random.default_rng(seed)
    corpus, centers, per = make_corpus(M, n_clusters, d, sigma, rng)
    # queries: cluster centers + noise, 10 per cluster
    nq = min(n_queries, 10 * n_clusters)
    qcenters = np.repeat(centers, 10, axis=0)[:nq]
    queries = unit_rows(qcenters + sigma / np.sqrt(d) * rng.standard_normal((nq, d)))

    stale = corpus.copy()
    cur_c = corpus.copy()
    cur_q = queries.copy()
    D_series = [0.0]
    rec_stale, rec_anchor = [], []
    if anchor_L:
        lm = rng.choice(len(corpus), size=anchor_L, replace=False)
    for g in range(1, G + 1):
        cur_c = step_transform(cur_c, rng, delta, nu)
        cur_q = step_transform(cur_q, rng, delta, nu)
        D_series.append(drift_D(cur_c, stale))
        gold = topk_indices(cur_q, cur_c, 10)
        rec_stale.append(recall_at_k(cur_q, stale, gold))
        if anchor_L:
            A = procrustes(stale[lm], cur_c[lm])
            anchored = unit_rows(stale @ A.T)
            rec_anchor.append(recall_at_k(cur_q, anchored, gold))
    return {'D': D_series, 'recall_stale': rec_stale,
            'recall_anchor': rec_anchor}


# ── F1: the law D(g) = 1 - lambda^g across channels ─────────────────────────
print('== F1: drift law ==', flush=True)
F1_G = 16
f1_cfgs = []
for lam_loss in [0.005, 0.01, 0.02, 0.05]:          # noise-only, d=256
    nu = float(np.sqrt((1.0 / (1.0 - lam_loss) ** 2) - 1.0))
    f1_cfgs.append((f'noise, 1-lambda={lam_loss}', 0.0, nu, 256, lam_loss))
# rotation-only at same lambda=0.02 requires d=64 (max rot drift 4/d)
f1_cfgs.append(('rotation, 1-lambda=0.02', 0.0, 0.0, 64, 0.02))
# ^ set below: delta solved for d=64
f1_runs = {}
f1_theory = {}
for name, delta, nu, d, lam_loss in f1_cfgs:
    if name.startswith('rotation'):
        d = 64
        # solve delta: 1 - lambda = 2(1 - cos delta)/d
        c = 1.0 - lam_loss * d / 2.0
        delta = float(np.arccos(np.clip(c, -1, 1)))
        nu = 0.0
    r = run_chain(d=d, delta=delta, nu=nu, G=F1_G, anchor_L=None, seed=11)
    lam = 1.0 - lam_loss
    f1_runs[name] = r['D']
    f1_theory[name] = [float(1.0 - lam ** g) for g in range(F1_G + 1)]
    print(f'  {name}: D(16) meas={r["D"][-1]:.3f} theory={1-lam**F1_G:.3f}', flush=True)
RESULTS['f1'] = {'runs': f1_runs, 'theory': f1_theory}

# ── F2: recall@10 stale vs anchored vs re-embedded ──────────────────────────
print('== F2: recall decay ==', flush=True)
F2_G = 16
r_stale = run_chain(delta=2.35, nu=0.05, G=F2_G, anchor_L=None, seed=21)
r_anchor = run_chain(delta=2.35, nu=0.05, G=F2_G, anchor_L=4096, seed=21)
print(f'  stale recall: {[round(x,3) for x in r_stale["recall_stale"]]}', flush=True)
print(f'  anchor recall: {[round(x,3) for x in r_anchor["recall_anchor"]]}', flush=True)
RESULTS['f2'] = {'stale': r_stale['recall_stale'], 'anchor': r_anchor['recall_anchor'],
                 'D': r_anchor['D'], 'G': F2_G}

# ── F3: decomposition heatmaps at gen 10 ────────────────────────────────────
print('== F3: channel decomposition ==', flush=True)
F3_NUS = [0.05, 0.12, 0.20, 0.30, 0.42]
F3_DELTAS = [0.0, 0.35, 0.8, 1.6, 2.35]
anc_grid = np.zeros((len(F3_NUS), len(F3_DELTAS)))
stale_grid = np.zeros((len(F3_NUS), len(F3_DELTAS)))
for i, nu in enumerate(F3_NUS):
    for j, dl in enumerate(F3_DELTAS):
        rr = run_chain(delta=dl, nu=nu, G=10, anchor_L=4096, seed=31)
        anc_grid[i, j] = rr['recall_anchor'][-1]
        stale_grid[i, j] = rr['recall_stale'][-1]
    print(f'  nu={nu}: anchored={[round(x,2) for x in anc_grid[i]]}', flush=True)
RESULTS['f3'] = {'nus': F3_NUS, 'deltas': F3_DELTAS,
                 'anchored': anc_grid.tolist(), 'stale': stale_grid.tolist()}

# ── F4: landmark count law ~ c/sqrt(L) ──────────────────────────────────────
print('== F4: landmarks ==', flush=True)
F4_LS = [64, 128, 256, 512, 1024, 2048, 4096]
f4_rec = []
for L in F4_LS:
    rr = run_chain(M=10000, n_clusters=50, delta=0.5, nu=0.12, G=8,
                   anchor_L=L, seed=41)
    f4_rec.append(rr['recall_anchor'][-1])
    print(f'  L={L}: recall@10 = {f4_rec[-1]:.3f}', flush=True)
rr_st = run_chain(M=10000, n_clusters=50, delta=0.5, nu=0.12, G=8,
                  anchor_L=None, seed=41)
RESULTS['f4'] = {'L': F4_LS, 'recall': f4_rec,
                 'stale': rr_st['recall_stale'][-1]}

# ── F5: dimension mercy (pure rotation) ─────────────────────────────────────
print('== F5: dimension ==', flush=True)
F5_DS = [16, 64, 256, 1024]
F5_G = 30
f5_runs = {}
for d in F5_DS:
    rr = run_chain(d=d, delta=np.deg2rad(60), nu=0.0, G=F5_G, seed=51)
    lam = 1.0 - 2.0 * (1 - np.cos(np.deg2rad(60))) / d
    f5_runs[d] = rr['D']
    print(f'  d={d}: D(30) meas={rr["D"][-1]:.3f} theory={1-lam**F5_G:.3f}', flush=True)
RESULTS['f5'] = {'d': F5_DS, 'D': f5_runs, 'G': F5_G}

# ════════════════════════════════════════════════════════════════════════════
# Figures
# ════════════════════════════════════════════════════════════════════════════

# F1
fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
cols = [CB[0], CB[1], CB[2], CB[3], CB[5]]
for i, (name, D) in enumerate(f1_runs.items()):
    gs = np.arange(len(D))
    ax.plot(gs, np.maximum(D, 1e-4), color=cols[i], lw=2.0, marker='o', ms=3.5,
            label=name.replace('1-lambda', '$1-\\lambda$'))
    th = f1_theory[name]
    ax.plot(gs, np.maximum(th, 1e-4), color=cols[i], ls=':', lw=1.3, alpha=0.8)
ax.set_yscale('log')
ax.set_xlabel('generation $g$')
ax.set_ylabel('semantic drift $D(g)$')
ax.set_title('Generation loss: $D(g) = 1-\\lambda^g$ across channels')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8.8)
ax.text(6.5, 0.00016, 'dotted: law $1-\\lambda^g$', fontsize=8.5, color=G700)
clean_axis(ax, grid=False)
ax.yaxis.grid(True, alpha=0.12, color=G400)
save(fig, 'f1-law-validation.png')

# F2
fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
gs = np.arange(1, F2_G + 1)
ax.plot(gs, r_stale['recall_stale'], color=CB[3], lw=2.0, marker='o', ms=3.5,
        label='stale index (never re-embedded)')
ax.plot(gs, r_anchor['recall_anchor'], color=CB[0], lw=2.2, marker='o', ms=3.5,
        label='anchored (Procrustes, L=4096)')
ax.plot(gs, np.ones_like(gs), color=G700, ls=':', lw=1.8,
        label='full re-embed every generation')
ax2 = ax.twinx()
ax2.plot(gs, r_anchor['D'][1:], color=G400, lw=1.4, ls='--', alpha=0.85)
ax2.set_ylabel('drift $D(g)$', color=G700, fontsize=10)
ax2.tick_params(axis='y', colors=G700)
ax2.spines['top'].set_visible(False)
ax2.set_ylim(0, 1.0)
ax.set_xlabel('generation $g$')
ax.set_ylabel('recall@10')
ax.set_ylim(0, 1.05)
ax.set_title('Anchoring without re-embedding: recall held, cost ~0')
# rev 1.1: legend below the axes (the outside-right placement collided
# with the twin axis label)
ax.legend(bbox_to_anchor=(0.5, -0.18), loc='upper center', ncol=2,
          fontsize=8.6)
clean_axis(ax)
save(fig, 'f2-recall.png')

# F3 (two panels)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.2), sharey=True,
                               constrained_layout=True)
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list('rec', ['#0B3C5D', '#1B6CA8',
                                                 '#5FA8D3', '#CFE6F5', '#FFFFFF'])
for ax, grid, ttl in ((ax1, stale_grid, 'stale index'),
                      (ax2, anc_grid, 'anchored index (L=4096)')):
    im = ax.imshow(grid, cmap=cmap, aspect='auto', origin='lower', vmin=0, vmax=1,
                   extent=[F3_DELTAS[0] - 0.17, F3_DELTAS[-1] + 0.17,
                           F3_NUS[0] - 0.037, F3_NUS[-1] + 0.037])
    ax.set_xlabel('rotation angle $\\delta$ per generation (rad)')
    ax.set_title(ttl, fontsize=11)
    for i in range(len(F3_NUS)):
        for j in range(len(F3_DELTAS)):
            v = grid[i, j]
            ax.text(F3_DELTAS[j], F3_NUS[i], f'{v:.2f}', ha='center',
                    va='center', fontsize=7.5,
                    color='white' if v < 0.55 else G700)
ax1.set_ylabel('per-object jitter $\\nu$')
ax2.set_yticklabels([])
cb = fig.colorbar(im, ax=[ax1, ax2], shrink=0.85, pad=0.02)
cb.set_label('recall@10 after 10 generations', fontsize=9)
cb.outline.set_visible(False)
save(fig, 'f3-decomposition.png')

# F4
fig, ax = plt.subplots(figsize=(6.2, 4.2), constrained_layout=True)
ax.plot(F4_LS, f4_rec, color=CB[0], lw=2.0, marker='o', ms=4,
        label='anchored recall@10 (gen 8)')
c_fit = (1.0 - np.array(f4_rec)[-1]) * np.sqrt(F4_LS[-1])
ax.plot(F4_LS, 1.0 - c_fit * np.sqrt(256.0 / np.array(F4_LS, dtype=float)),
        color=G700, ls='--', lw=1.5,
        label='$1 - c\\sqrt{d/L}$ (alignment-error law)')
ax.axhline(rr_st['recall_stale'][-1], color=CB[3], ls=':', lw=1.6)
# rev 1.1: annotation above the line at the left edge (the old placement
# at x=5, y=stale-0.13 sat on the rising curve), harm zone shaded
ax.axvspan(40, 256, color=CB[3], alpha=0.07)
ax.text(70, 0.965,
        'harm zone ($L<d$):\nnoise-fit rotation is worse\nthan no alignment',
        fontsize=7.6, color=CB[3], va='top')
ax.text(70, rr_st['recall_stale'][-1] + 0.026,
        f'stale, no anchoring: {rr_st["recall_stale"][-1]:.2f}',
        fontsize=8.5, color=CB[3], ha='left', va='bottom')
ax.set_xscale('log')
ax.set_xlabel('landmark count $L$')
ax.set_ylabel('recall@10')
ax.set_ylim(0, 1.05)
ax.set_title('Landmark budget: error falls as $\\sqrt{d/L}$')
ax.legend(loc='upper right')
clean_axis(ax)
save(fig, 'f4-landmarks.png')

# F5
fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
cols = [CB[5], CB[3], CB[1], CB[0]]
for i, d in enumerate(F5_DS):
    D = f5_runs[d]
    gs = np.arange(len(D))
    ax.plot(gs, D, color=cols[i], lw=2.0, marker='o', ms=3, label=f'$d$={d}')
    lam = 1.0 - 2.0 * (1 - np.cos(np.deg2rad(60))) / d
    ax.plot(gs, 1.0 - lam ** gs, color=cols[i], ls=':', lw=1.2, alpha=0.8)
ax.set_xlabel('generation $g$')
ax.set_ylabel('semantic drift $D(g)$')
ax.set_title('Dimension mercy: rotations barely drift in high dimensions')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
ax.text(1.0, 0.92, '$\\kappa_{rot} = 2(1-\\cos\\delta)/d$', fontsize=9,
        color=G700, va='top')
clean_axis(ax)
save(fig, 'f5-dimension.png')

with open(os.path.join(OUT, 'results.json'), 'w') as f:
    json.dump(RESULTS, f, indent=1)
print('DONE — results.json written', flush=True)
