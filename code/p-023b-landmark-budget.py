#!/usr/bin/env python3
"""P-023b: the landmark budget law — knee-migration experiments (F6, F7).

Revision 1.1 of P-023 withdraws the draft's "L ~ 8d is the knee" reading:
8d is one configuration's fingerprint, not a law. The law is

    L* = (nu_eff / eps)^2 * Psi(panel spectrum) * [class factor]

with nu_eff = sqrt(g) * nu (accumulated per-object distortion at chain
position g), Psi = (2/d^2) * sum_{i!=j} lam_i/(lam_i+lam_j)^2 over the
landmark panel's covariance spectrum (Psi_iso = (d-1)/2), and class factor
1 for the orthogonal Procrustes family, ~2d/(d-1) for the affine family.

Experiments (paired-chain design: one corpus+chain per configuration, all
landmark counts L fitted on the same chain — removes between-L chain noise):

  E1   theorem check: measured angular MSE vs the closed forms
       (isotropic, anisotropic/Psi, affine) on synthetic pairs
  F6a  knee vs nu at chain lengths G in {2, 8, 32}
  F6b  knee vs panel conditioning, random panel vs whitened farthest-point
       selection (geometric kappa=100, kappa=1e4, spiked spectra)
  F6c  knee vs estimator class (orthogonal vs affine) and the floor the
       estimator class cannot reach (orthogonal fit on linear churn)
  F6d  knee vs tolerance theta (post-hoc, the deficit exponent)
  F7   measured knees vs the law's ratio predictions

Also re-renders F2/F4 with overlap-free layout (legend below plot,
annotations in clear space, the sub-dimension harm zone shaded).

Writes figures/p-023/f6-knee-migration.png, f7-law-summary.png,
f2-recall.png, f4-landmarks.png, and EXTENDS figures/p-023/results.json
(keys e1, f6a..f6d, f7, f4_harm, f_class_residuals).

Seeds: E1 2026; F6a 61/62, F6b 71/72, F6c 81/82 on PCG64.
NumPy + Matplotlib only. Float32 corpora, chunked top-k (3 GB RAM safe).
"""
import json
import os
import faulthandler

import numpy as np
import matplotlib
faulthandler.enable()
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
RES_PATH = os.path.join(OUT, 'results.json')
if os.path.exists(RES_PATH):
    with open(RES_PATH) as f:
        RESULTS = json.load(f)


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


# ---------------------------------------------------------------------------
# Corpus, churn, estimators
# ---------------------------------------------------------------------------

def unit_rows(X):
    return X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)


def make_corpus(M, n_clusters, d, sigma, rng, w=None):
    if w is None:
        centers = unit_rows(rng.standard_normal((n_clusters, d)))
    else:
        centers = unit_rows(rng.standard_normal((n_clusters, d)) * np.sqrt(w))
    per = M // n_clusters
    X = np.empty((per * n_clusters, d))
    for c in range(n_clusters):
        blk = c * per
        X[blk:blk + per] = centers[c] + sigma / np.sqrt(d) * rng.standard_normal((per, d))
    return unit_rows(X), centers, per


def givens(X, i, j, delta):
    c, s = np.cos(delta), np.sin(delta)
    Y = X.copy()
    xi, xj = X[:, i].copy(), X[:, j].copy()
    Y[:, i] = c * xi - s * xj
    Y[:, j] = s * xi + c * xj
    return Y


def step_rot(X, rng, delta, nu):
    N, d = X.shape
    if delta > 0:
        i, j = rng.choice(d, size=2, replace=False)
        X = givens(X, i, j, delta)
    if nu > 0:
        X = X + nu / np.sqrt(d) * rng.standard_normal(X.shape)
        X = unit_rows(X)
    return X


def step_lin(X, rng, s_scale, nu):
    d = X.shape[1]
    u = rng.uniform(-s_scale, s_scale, size=d)
    R1 = np.linalg.qr(rng.standard_normal((d, d)))[0]
    R2 = np.linalg.qr(rng.standard_normal((d, d)))[0]
    M = R1 @ np.diag(np.exp(u)) @ R2
    X = X @ M.T
    if nu > 0:
        X = X + nu / np.sqrt(d) * rng.standard_normal(X.shape)
    return X


def procrustes(X0, Y):
    C = (X0.T @ Y).astype(np.float64)
    U, S, Vt = np.linalg.svd(C)
    return (Vt.T @ U.T)


def procrustes_affine(X0, Y, ridge=1e-9):
    G = X0.T.astype(np.float64) @ X0 + ridge * len(X0) * np.eye(X0.shape[1])
    return np.linalg.solve(G, X0.T.astype(np.float64) @ Y)


def topk_indices(Q, X, k=10, chunk=256):
    """Row-wise top-k by dot product, query-chunked (memory-lean)."""
    X32 = np.ascontiguousarray(X, dtype=np.float32)
    out = np.empty((len(Q), k), dtype=np.int64)
    for a in range(0, len(Q), chunk):
        S = (np.ascontiguousarray(Q[a:a + chunk], dtype=np.float32) @ X32.T)
        out[a:a + chunk] = np.argpartition(-S, k, axis=1)[:, :k]
    return out


def recall_at_k(qt, xt, gold, k=10, gold_sets=None):
    pred = topk_indices(qt, xt, k)
    hits = 0
    for r in range(len(qt)):
        hits += len(set(pred[r]) & (gold_sets[r] if gold_sets else set(gold[r])))
    return hits / (k * len(qt))


def geom_spectrum(d, kappa):
    r = kappa ** (1.0 / (d - 1))
    w = r ** np.arange(d - 1, -1, -1)
    return w / w.sum() * d


def spiked_spectrum(d):
    w = np.ones(d)
    w[0] = d / 2.0
    return w


def psi_of(lam):
    d = len(lam)
    L = np.asarray(lam, dtype=float)
    S = L[:, None] + L[None, :]
    np.fill_diagonal(S, np.inf)
    with np.errstate(invalid='ignore', divide='ignore'):
        val = (L[:, None] / S ** 2)
    return float((2.0 / d ** 2) * np.nansum(val))


def achieved_spectrum(Xlm):
    C = np.cov(Xlm.T.astype(np.float64))
    lam = np.linalg.eigvalsh(C)
    lam = np.maximum(lam, 0.0)
    return lam / max(lam.sum(), 1e-12)


_ORDER_CACHE = {}


def whiten_farpoint_order(X, key):
    """Greedy farthest-point order in the corpus-whitened metric (cached).
    Distances via the dot-product trick (no diff matrices)."""
    if key in _ORDER_CACHE:
        return _ORDER_CACHE[key]
    C = np.cov(X.T.astype(np.float64))
    C += 1e-9 * np.eye(C.shape[0]) * np.trace(C)
    lam, V = np.linalg.eigh(C)
    Z = ((X - X.mean(0)) @ V @ np.diag(1.0 / np.sqrt(np.maximum(lam, 1e-12))
                                       )).astype(np.float32)
    n = len(Z)
    Zsq = (Z * Z).sum(1)
    first = int(np.argmax(Zsq))
    order = [first]
    mind = Zsq + Zsq[first] - 2.0 * (Z @ Z[first])
    for t in range(min(n, 8192) - 1):
        nxt = int(np.argmax(mind))
        order.append(nxt)
        np.minimum(mind, Zsq + Zsq[nxt] - 2.0 * (Z @ Z[nxt]), out=mind)
        mind[nxt] = -1.0
    arr = np.array(order[:8192])
    _ORDER_CACHE[key] = arr
    return arr


# ---------------------------------------------------------------------------
# Paired-chain driver: one chain per (config, seed); L-sweep on the same chain
# ---------------------------------------------------------------------------

def mismatch_penalty(Xlm, Xcorpus_sub):
    """Exact mismatch functional M/M_iso from empirical spectra.
    M = sum_{i!=j} lam_p_i * Sc_j / (lam_p_i + lam_p_j)^2 in the panel
    eigenframe; M_iso = (d^2 - d)/4. Equals 1 for a matched isotropic
    panel; >1 when the panel under-covers directions carrying corpus mass;
    <1 when the panel is matched to a concentrated corpus."""
    Cp = np.cov(Xlm.T.astype(np.float64))
    lam, U = np.linalg.eigh(Cp)
    lam = np.maximum(lam, 1e-9)
    lam = lam / lam.sum()
    Cc = np.cov(Xcorpus_sub.T.astype(np.float64))
    Sd = np.diag(U.T @ Cc @ U)
    Sd = np.maximum(Sd, 0.0)
    S = lam[:, None] + lam[None, :]
    np.fill_diagonal(S, np.inf)
    M = np.nansum(np.where(np.isfinite(S),
                            lam[:, None] * Sd[None, :] / S ** 2, 0.0))
    d = len(lam)
    return float(M / ((d * d - d) / 4.0))


def run_curve(Ls, d=256, M=20000, n_clusters=50, sigma=0.7, G=8,
              delta=0.5, nu=0.12, seed=61, w=None, panel='random',
              churn='rot', s_scale=0.15, estimator='orth', nq=1000):
    rng = np.random.default_rng(seed)
    corpus, centers, per = make_corpus(M, n_clusters, d, sigma, rng, w)
    cq = rng.integers(0, n_clusters, size=nq)
    queries = unit_rows(centers[cq] + sigma / np.sqrt(d) *
                        rng.standard_normal((nq, d)))
    if panel == 'random':
        lm_order = rng.permutation(len(corpus))
    elif panel == 'starved':
        # landmarks only from the first 32 clusters: a hot-region panel that
        # under-covers the corpus's remaining directions
        n_starve = min(32, n_clusters)
        lm_order = rng.permutation(n_starve * per)
    else:
        lm_order = whiten_farpoint_order(corpus, (seed, id(w)))
    stale = corpus.copy()
    cur_c = corpus.copy()
    cur_q = queries.copy()
    for g in range(G):
        if churn == 'rot':
            cur_c = step_rot(cur_c, rng, delta, nu)
            cur_q = step_rot(cur_q, rng, delta, nu)
        else:
            cur_c = step_lin(cur_c, rng, s_scale, nu)
            cur_q = step_lin(cur_q, rng, s_scale, nu)
    gold = topk_indices(cur_q, cur_c, 10)
    gold_sets = [set(g) for g in gold]
    rec_stale = recall_at_k(cur_q, stale, gold, gold_sets=gold_sets)
    recs, Ls_eff, psis, resids = [], [], [], []
    for L in Ls:
        lm = lm_order[:min(L, len(lm_order))]
        if estimator == 'orth':
            A = procrustes(stale[lm], cur_c[lm])
            anchored = stale @ A.T
        else:
            A = procrustes_affine(stale[lm], cur_c[lm])
            anchored = stale @ A
        recs.append(recall_at_k(cur_q, anchored, gold, gold_sets=gold_sets))
        Ls_eff.append(len(lm))
        Ao = procrustes(stale[lm], cur_c[lm])
        resids.append(float(np.mean(np.sum((stale[lm] @ Ao.T - cur_c[lm]) ** 2,
                                           axis=1))))
    psi_max = float(psi_of(achieved_spectrum(
        stale[lm_order[:min(max(Ls), len(lm_order))]])))
    return {'L': Ls_eff, 'recall': recs, 'recall_stale': float(rec_stale),
            'psi_max': psi_max, 'resid_orth': resids,
            'corpus_sub': corpus[rng.choice(len(corpus), size=2000,
                                            replace=False)],
            'lm_max': stale[lm_order[:min(max(Ls), len(lm_order))]]}


def avg_curves(curves):
    Ls = curves[0]['L']
    recs = np.mean([c['recall'] for c in curves], axis=0)
    psis = np.mean([c['psi_max'] for c in curves])
    resids = np.mean([c['resid_orth'] for c in curves], axis=0)
    mism = np.mean([mismatch_penalty(c['lm_max'], c['corpus_sub'])
                    for c in curves])
    return {'L': Ls, 'recall': list(recs),
            'psi_max': float(psis), 'mismatch': float(mism),
            'resid_orth': list(resids),
            'recall_stale': float(np.mean([c['recall_stale'] for c in curves]))}


def knee_from_curve(Ls, recs, theta_abs=0.010):
    Ls = np.asarray(Ls, dtype=float)
    recs = np.asarray(recs, dtype=float)
    floor = float(np.mean(recs[-2:]))
    deficit = floor - recs
    for i in range(len(Ls)):
        if deficit[i] <= theta_abs:
            if i == 0:
                return float(Ls[0]), floor
            return float(np.sqrt(Ls[i - 1] * Ls[i])), floor
    return None, floor


# ---------------------------------------------------------------------------
# E1: theorem check on synthetic pairs
# ---------------------------------------------------------------------------
print('== E1: theorem check ==', flush=True)
rngE = np.random.default_rng(2026)
e1 = {}
for d, L, nu in ((32, 400, 0.15), (64, 1000, 0.20)):
    A = np.linalg.qr(rngE.standard_normal((d, d)))[0]
    V = unit_rows(rngE.standard_normal((20, d)))
    errs = []
    for _ in range(300):
        X = unit_rows(rngE.standard_normal((L, d)))
        E = rngE.standard_normal((L, d)) * (nu / np.sqrt(d))
        Ah = procrustes(X, X @ A.T + E)
        D = Ah - A
        errs.append(float(np.mean(np.sum((V @ D.T) ** 2, axis=1))))
    meas = float(np.mean(errs))
    theory = (d - 1) * nu ** 2 / (2 * L)
    e1[f'orth-iso d={d}'] = {'measured': meas, 'theory': theory,
                             'ratio': meas / theory}
    print(f'  orth-iso d={d}: ratio={meas/theory:.3f}', flush=True)
for kappa in (100, 10000):
    d, L, nu = 32, 1200, 0.15
    r = kappa ** (1.0 / (d - 1))
    w = (r ** np.arange(d - 1, -1, -1))
    w = w / w.sum()
    A = np.linalg.qr(rngE.standard_normal((d, d)))[0]
    V = unit_rows(rngE.standard_normal((20, d)))
    errs = []
    for _ in range(300):
        X = unit_rows(rngE.standard_normal((L, d)) * np.sqrt(w))
        E = rngE.standard_normal((L, d)) * (nu / np.sqrt(d))
        Ah = procrustes(X, X @ A.T + E)
        D = Ah - A
        errs.append(float(np.mean(np.sum((V @ D.T) ** 2, axis=1))))
    meas = float(np.mean(errs))
    lam = w
    S = lam[:, None] + lam[None, :]
    np.fill_diagonal(S, np.inf)
    M = np.nansum(np.where(np.isfinite(S), lam[:, None] / S ** 2, 0.0))
    theory = (2 * nu ** 2 / (d * L)) * M / d
    psi = (2.0 / d ** 2) * M
    e1[f'orth-aniso kappa={kappa}'] = {
        'measured': meas, 'theory': theory, 'ratio': meas / theory,
        'psi_over_iso': psi / ((d - 1) / 2)}
    print(f'  orth-aniso kappa={kappa}: ratio={meas/theory:.3f}, '
          f'Psi/Psi_iso={psi/((d-1)/2):.2f}', flush=True)
d, L, nu = 32, 800, 0.15
B = (np.linalg.qr(rngE.standard_normal((d, d)))[0] @
     np.diag(np.exp(rngE.uniform(-0.1, 0.1, d))) @
     np.linalg.qr(rngE.standard_normal((d, d)))[0])
V = unit_rows(rngE.standard_normal((20, d)))
errs = []
for _ in range(300):
    X = unit_rows(rngE.standard_normal((L, d)))
    E = rngE.standard_normal((L, d)) * (nu / np.sqrt(d))
    Bh = procrustes_affine(X, X @ B + E)
    D = Bh - B
    errs.append(float(np.mean(np.sum((V @ D.T) ** 2, axis=1))))
meas = float(np.mean(errs))
theory = d * nu ** 2 / L
e1['affine-iso'] = {'measured': meas, 'theory': theory, 'ratio': meas / theory,
                    'class_factor_meas': meas / ((d - 1) * nu ** 2 / (2 * L))}
print(f'  affine-iso: ratio={meas/theory:.3f}, '
      f'class factor={meas/((d-1)*nu**2/(2*L)):.2f}', flush=True)
RESULTS['e1'] = e1

# ---------------------------------------------------------------------------
# F6a: knee vs nu at G in {2, 8, 32}
# ---------------------------------------------------------------------------
def checkpoint():
    with open(RES_PATH, 'w') as f:
        json.dump(RESULTS, f, indent=1)


print('== F6a: nu / G sweep ==', flush=True)
F6A_LS_STD = [32, 64, 128, 256, 512, 1024, 2048, 4096]
F6A_LS_BIG = [256, 512, 1024, 2048, 4096, 8192, 16384]
F6A_CFGS = [(0.03, 8, F6A_LS_STD), (0.06, 8, F6A_LS_STD),
            (0.12, 8, F6A_LS_STD), (0.24, 8, F6A_LS_BIG),
            (0.12, 2, F6A_LS_STD), (0.12, 32, F6A_LS_BIG)]
f6a = {}
for nu, G, Ls in F6A_CFGS:
    curve = avg_curves([run_curve(Ls, nu=nu, G=G, seed=s) for s in (61, 62)])
    knee, floor = knee_from_curve(curve['L'], curve['recall'])
    f6a[f'nu={nu},G={G}'] = {**curve, 'knee': knee, 'floor': floor,
                              'nu_eff': float(np.sqrt(G) * nu)}
    print(f'  nu={nu} G={G}: knee={knee}, floor={floor:.3f}, '
          f'recall={[round(x,3) for x in curve["recall"]]}', flush=True)
RESULTS['f6a'] = f6a
checkpoint()
# ---------------------------------------------------------------------------
# F6b: knee vs panel conditioning (d=64, nu=0.06, G=8)
# ---------------------------------------------------------------------------
print('== F6b: panel selection sweep ==', flush=True)
# Isotropic corpus (256 clusters fill all d=64 directions; sigma=0.25 keeps
# the intra-cluster jitter below the between-cluster scale). The theory:
# a MATCHED panel is forgiving (the harmonic kernel lambda_i*lambda_j/
# (lambda_i+lambda_j)^2 is spectrum-insensitive, and an anisotropic corpus
# with a matched random panel pays nothing), while a panel that
# UNDER-COVERS directions carrying corpus mass pays the full penalty.
# Panels: random (matched), whitened farthest-point (guaranteed coverage),
# starved (first 32 clusters only — the lazy 'pick from the hot region'
# heuristic). M = 20000/256 clusters gives the starved panel 2496 objects.
F6B_SIGMA = 0.25
F6B_LS = [32, 64, 128, 256, 512, 1024, 2048]
F6B_LS_STARVE = [32, 64, 128, 256, 512, 1024, 2048]
f6b = {}
for panel in ('random', 'whitened', 'starved'):
    Ls = F6B_LS_STARVE if panel == 'starved' else F6B_LS
    curve = avg_curves([run_curve(Ls, d=64, M=16000, n_clusters=256,
                                  sigma=F6B_SIGMA, G=8, nu=0.06, seed=s,
                                  panel=panel) for s in (71, 72)])
    knee, floor = knee_from_curve(curve['L'], curve['recall'])
    f6b[f'isotropic|{panel}'] = {**curve, 'knee': knee, 'floor': floor}
    print(f'  isotropic/{panel}: knee={knee}, floor={floor:.3f}, '
          f'mismatch={curve["mismatch"]:.2f}', flush=True)
    RESULTS['f6b'] = f6b
    checkpoint()
# matched-anisotropic control: spiked corpus, random panel (the forgiveness)
for name, w in (('spiked', spiked_spectrum(64)),
                ('geometric kappa=1e4', geom_spectrum(64, 10000))):
    curve = avg_curves([run_curve(F6B_LS, d=64, M=16000, n_clusters=256,
                                   sigma=F6B_SIGMA, G=8, nu=0.06, seed=s,
                                   w=w, panel='random') for s in (71, 72)])
    knee, floor = knee_from_curve(curve['L'], curve['recall'])
    f6b[f'{name}|random'] = {**curve, 'knee': knee, 'floor': floor}
    print(f'  {name}/random (matched): knee={knee}, floor={floor:.3f}',
          flush=True)
    RESULTS['f6b'] = f6b
    checkpoint()
RESULTS['f6b'] = f6b

# ---------------------------------------------------------------------------
# F6c: estimator class (d=64, nu=0.06, G=8, isotropic corpus)
# ---------------------------------------------------------------------------
print('== F6c: estimator class ==', flush=True)
f6c = {}
for churn in ('rot', 'lin'):
    for est in ('orth', 'affine'):
        curve = avg_curves([run_curve(F6B_LS, d=64, M=16000, n_clusters=256,
                                      sigma=F6B_SIGMA, G=8, nu=0.06, seed=s,
                                      churn=churn, estimator=est)
                            for s in (81, 82)])
        knee, floor = knee_from_curve(curve['L'], curve['recall'])
        f6c[f'{churn}/{est}'] = {**curve, 'knee': knee, 'floor': floor}
        print(f'  {churn}/{est}: knee={knee}, floor={floor:.3f}, '
              f'resid_orth={np.mean(curve["resid_orth"]):.4f}', flush=True)
        RESULTS['f6c'] = f6c
        checkpoint()
RESULTS['f6c'] = f6c
RESULTS['f_class_residuals'] = {
    'rot/orth': float(np.mean(f6c['rot/orth']['resid_orth'])),
    'lin/orth': float(np.mean(f6c['lin/orth']['resid_orth'])),
    'lin/affine_fit_residual_note': 'orthogonal-fit residual per landmark'}

# ---------------------------------------------------------------------------
# F6d: knee vs tolerance (post-hoc on nu=0.12, G=8)
# ---------------------------------------------------------------------------
print('== F6d: tolerance sweep ==', flush=True)
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
            k = float(Ls[i]) if i == 0 else float(np.sqrt(Ls[i - 1] * Ls[i]))
            break
    f6d_theta.append(theta)
    f6d_knee.append(k)
    print(f'  theta={theta}: knee={k}', flush=True)
RESULTS['f6d'] = {'theta': f6d_theta, 'knee': f6d_knee, 'floor': floor}

# ---------------------------------------------------------------------------
# F7: measured knees vs the law's ratio predictions
# ---------------------------------------------------------------------------
print('== F7: law summary ==', flush=True)
d_A, d_B = 256, 64
base_B = f6b['isotropic|random']['knee']
base_C = f6c['rot/orth']['knee']
f7_pts = []
for key in ('isotropic|random', 'isotropic|whitened', 'isotropic|starved'):
    v = f6b[key]
    if v['knee'] is None:
        continue
    pred = base_B * v['mismatch']
    f7_pts.append((key.replace('|', ' / '), v['knee'], pred, CB[1]))
for key, v in f6c.items():
    if v['knee'] is None:
        continue
    churn, est = key.split('/')
    cls = 2 * d_B / (d_B - 1) if est == 'affine' else 1.0
    pred = base_C * cls
    f7_pts.append((f'{churn} churn / {est} fit', v['knee'], pred, CB[2]))
# the nu/G panel enters through its own collapse (F6a): the knee is a
# single-variable power law in nu_eff; measured exponent reported in f6a_slope
neffs, knees_a = [], []
for key, v in f6a.items():
    if v['knee']:
        neffs.append(v['nu_eff'])
        knees_a.append(v['knee'])
if len(neffs) >= 3:
    slope_a = float(np.polyfit(np.log(neffs), np.log(knees_a), 1)[0])
else:
    slope_a = None
RESULTS['f6a_slope'] = slope_a
RESULTS['f7'] = [{'label': l, 'measured': m, 'predicted': p}
                 for l, m, p, _ in f7_pts]

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.6), constrained_layout=True)

# (a) knee vs accumulated distortion nu_eff — the (nu, G) collapse
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
ax.plot(tt, (ys[-1] * (tt / xs[-1]) ** sl), ls='-', lw=1.4, color=G700,
        label=f'collapse: $L^*\\propto\\nu_{{eff}}^{{{sl:.2f}}}$')
ax.plot(tt, (ys[0] * (tt / xs[0]) ** 2), ls=':', lw=1.3, color=CB[1],
        label='angular law: $\\nu_{eff}^2$')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('accumulated per-object distortion $\\nu_{eff}=\\sqrt{g}\\,\\nu$')
ax.set_ylabel('knee $L^*/d$')
ax.set_title('(a) knees collapse onto $\\nu_{eff}$ — sub-quadratically')
from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([0], [0], color=CB[2], lw=0, marker='o', label='$G$=2'),
    Line2D([0], [0], color=CB[0], lw=0, marker='o', label='$G$=8'),
    Line2D([0], [0], color=CB[3], lw=0, marker='o', label='$G$=32'),
    Line2D([0], [0], color=G700, lw=1.4,
           label=f'fit: $\\nu_{{eff}}^{{{sl:.2f}}}$'),
    Line2D([0], [0], color=CB[1], lw=1.3, ls=':', label='$\\nu_{{eff}}^2$ (law)'),
], loc='upper left', fontsize=8.2)
clean_axis(ax, grid=False)
ax.yaxis.grid(True, alpha=0.12, color=G400)

# (b) knee vs panel-corpus mismatch
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
OFFS = {'random panel (matched)': (9, 5),
         'whitened selection': (9, -13),
         'starved panel (hot region)': (10, 6),
         'spiked corpus, random (matched)': (10, -12),
         'anisotropic corpus, random (matched)': (10, 7)}
for x, y, lab in zip(xs, ys, labs):
    ax.annotate(lab, (x, y), textcoords='offset points',
                xytext=OFFS.get(lab, (9, 5)), fontsize=7.2, color=G700)
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

# (d) knee vs tolerance
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

save(fig, 'f6-knee-migration.png')

# F7
fig, ax = plt.subplots(figsize=(6.4, 5.4), constrained_layout=True)
for label, m, p, col in f7_pts:
    scale = d_B
    ax.plot(p / scale, m / scale, 'o', ms=7, color=col, alpha=0.9)
lo, hi = 0.5, 80
ax.plot([lo, hi], [lo, hi], ls='--', lw=1.2, color=G400)
ax.plot([lo, hi], [lo * 2, hi * 2], ls=':', lw=1.1, color=G400)
ax.plot([lo, hi], [lo / 2, hi / 2], ls=':', lw=1.1, color=G400)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_xlabel('predicted $L^*/d$ (law, one anchor per panel)')
ax.set_ylabel('measured $L^*/d$')
ax.set_title('Within a retrieval geometry, the law pins the knee')
ax.text(0.05, 0.93, 'dashed: perfect   dotted: $\\times$2 band',
        transform=ax.transAxes, fontsize=8.5, color=G700)
from matplotlib.lines import Line2D
handles = [Line2D([0], [0], color=CB[1], lw=0, marker='o',
                  label='conditioning sweep (b)'),
           Line2D([0], [0], color=CB[2], lw=0, marker='o',
                  label='class sweep (c)')]
ax.legend(handles=handles, loc='lower right', fontsize=8.5)
clean_axis(ax, grid=False)
ax.yaxis.grid(True, alpha=0.12, color=G400)
save(fig, 'f7-law-summary.png')

# F2 re-render
if 'f2' in RESULTS:
    f2 = RESULTS['f2']
    fig, ax = plt.subplots(figsize=(6.8, 4.8), constrained_layout=True)
    gs = np.arange(1, f2['G'] + 1)
    ax.plot(gs, f2['stale'], color=CB[3], lw=2.0, marker='o', ms=3.5,
            label='stale index (never re-embedded)')
    ax.plot(gs, f2['anchor'], color=CB[0], lw=2.2, marker='o', ms=3.5,
            label='anchored (Procrustes, $L$=4096)')
    ax.plot(gs, np.ones_like(gs), color=G700, ls=':', lw=1.8,
            label='full re-embed every generation')
    ax2 = ax.twinx()
    ax2.plot(gs, f2['D'][1:], color=G400, lw=1.4, ls='--', alpha=0.85)
    ax2.set_ylabel('drift $D(g)$', color=G700, fontsize=10)
    ax2.tick_params(axis='y', colors=G700)
    ax2.spines['top'].set_visible(False)
    ax2.set_ylim(0, 1.0)
    ax.set_xlabel('generation $g$')
    ax.set_ylabel('recall@10')
    ax.set_ylim(0, 1.05)
    ax.set_title('Anchoring without re-embedding: recall held, cost ~0')
    ax.legend(bbox_to_anchor=(0.5, -0.20), loc='upper center', ncol=2,
              fontsize=8.6)
    clean_axis(ax)
    save(fig, 'f2-recall.png')

# F4 re-render
if 'f4' in RESULTS:
    f4 = RESULTS['f4']
    fig, ax = plt.subplots(figsize=(6.4, 4.5), constrained_layout=True)
    Ls = np.asarray(f4['L'], dtype=float)
    recs = np.asarray(f4['recall'])
    ax.plot(Ls, recs, color=CB[0], lw=2.0, marker='o', ms=4,
            label='anchored recall@10 (gen 8)')
    c_fit = (1.0 - recs[-1]) * np.sqrt(Ls[-1])
    ax.plot(Ls, 1.0 - c_fit * np.sqrt(256.0 / Ls),
            color=G700, ls='--', lw=1.5,
            label='$1 - c\\sqrt{d/L}$ (alignment-error law)')
    ax.axhline(f4['stale'], color=CB[3], ls=':', lw=1.6)
    ax.axvspan(40, 256, color=CB[3], alpha=0.07)
    ax.text(70, 0.965, 'harm zone ($L<d$):\nnoise-fit rotation is worse\nthan no alignment at all',
            fontsize=7.6, color=CB[3], va='top')
    ax.text(70, f4['stale'] + 0.026,
            f'stale, no anchoring: {f4["stale"]:.2f}',
            fontsize=8.5, color=CB[3], ha='left', va='bottom')
    ax.annotate('parity', xy=(512, 0.4848), xytext=(170, 0.18),
                fontsize=8.0, color=G700,
                arrowprops=dict(arrowstyle='-', color=G400, lw=0.8))
    ax.annotate('knee $\\approx$ 4–8$d$', xy=(2048, 0.5288),
                xytext=(660, 0.28), fontsize=8.5, color=CB[0],
                arrowprops=dict(arrowstyle='-', color=CB[0], lw=0.8))
    ax.set_xscale('log')
    ax.set_xlabel('landmark count $L$')
    ax.set_ylabel('recall@10')
    ax.set_ylim(0, 1.05)
    ax.set_xlim(40, 6000)
    ax.set_title('Landmark budget: error falls as $\\sqrt{d/L}$ — then a floor')
    ax.legend(bbox_to_anchor=(0.5, -0.17), loc='upper center', ncol=1,
              fontsize=8.6)
    clean_axis(ax)
    save(fig, 'f4-landmarks.png')
    RESULTS['f4_harm'] = {
        'anchored_at_L64': float(recs[0]),
        'stale': float(f4['stale']),
        'harm_ratio': float(f4['stale'] / recs[0]),
        'parity_L': 512,
    }

with open(RES_PATH, 'w') as f:
    json.dump(RESULTS, f, indent=1)
print('DONE — results.json extended', flush=True)
