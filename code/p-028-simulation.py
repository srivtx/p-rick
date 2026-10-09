#!/usr/bin/env python3
"""P-028 simulation: the anchor law of agentic maintenance.

Model: a codebase is a point in a metric space. Behavior coordinates
b in R^m (what the system does, pinned by tests/invariants) and
complexity coordinates c in R^k (how much machinery it takes).
One agent pass = a noisy maintenance step (spec distance is per-
coordinate normalized: L = ||b||^2 / (2m)):

    b_i <- (1 - eta*mu) b_i + xi_i        (xi ~ N(0, h^2))  [i not anchored]
    b_i <- b_i^ref                          [i anchored: reverted to the
                                             behavior the anchors pin]
    c_j <- c_j + max(0, zeta_j)            (zeta ~ N(delta, h^2))  [ratchet]
    c_j <- min(c_j + max(0, zeta_j), cap)  [under a complexity cap]

h is the agent's proposal entropy, eta*mu the review/learning rate,
a the anchor coverage (fraction of behavior coordinates enforced).

Laws under test:
  L1 (floor law): the maintenance floor is exactly
        E[L_inf] = (1-a) h^2 / (2(2 eta mu - (eta mu)^2))
                   + a s^2 / 2
      (s the scale of pinned reference behavior) -- a linear trade:
      un-anchored noise against frozen legacy error. The floor is
      linear in a, so exactly ONE boundary edge exists: anchors
      substitute for entropy or they cannot help at all.
  L2 (ratchet law): un-anchored complexity drifts linearly,
        E[C_t] = C_0 + rho_R t, rho_R = k E max(0, N(delta, h^2)),
      untouched by behavior anchors, pinned only by an explicit cap.
  L3 (boundary law): stable maintenance (floor < L_tol) iff
        a > a*(h) = (N - L_tol) / (N - Gamma),
        N = h^2 / (2(2 eta mu - (eta mu)^2)),  Gamma = s^2/2,
      with the strong-anchor asymptote a* ~ 1 - 2 L_tol (2 eta mu -
      (eta mu)^2) / h^2 -- the uncovered requirement falls
      QUADRATICALLY in agent entropy: halving h quarters it. If
      Gamma > L_tol no coverage suffices: anchors preserve, they
      do not repair.
  L4 (substitution law): the boundary as a design curve:
      required process burden against model quality, per review rate.

Figures:
  f1-ratchet.png         L2: complexity vs passes (ratchet / anchor / cap)
  f2-floor.png           L1: floor vs h per coverage, log-log slope 2
  f3-boundary.png        L3: success map in (a, h) + predicted boundaries
  f4-trajectories.png    L(t) trajectories in the four regimes
  f5-substitution.png    L4: a_min(h) curves + the two-anchor doctrine
  f6-law-validation.png  residuals of all laws

Writes results.json with every headline number cited in the paper.
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'figures', 'p-028')
os.makedirs(OUT, exist_ok=True)

SEED = 20261009
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


def legend_above(ax, title=None, ncol=3):
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.02), ncol=ncol,
              title=title, title_fontsize=10.5, handlelength=1.6,
              columnspacing=1.2, borderaxespad=0.0)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches='tight', pad_inches=0.25)
    plt.close(fig)
    print('wrote', name)


rng = np.random.default_rng(SEED)

# ----------------------------------------------------------------------
# core simulator
# ----------------------------------------------------------------------
M, K = 10, 6            # behavior dims, complexity dims
ETA_MU = 0.30           # review rate per pass (eta * mu)
T_RUN = 2000
N_SEED = 48
L_TOL = 0.12            # maintenance tolerance (stable iff floor < tol)
LEG_S = 0.40            # legacy scale: pinned coords hold N(0, s^2) refs


def simulate(a, h, t_run=T_RUN, n_seed=8, cap=None, delta=0.04,
             eta_mu=ETA_MU, rng=None):
    """Run n_seed maintenance trajectories. Returns L_t, C_t arrays.

    L = ||b||^2 / (2m): per-coordinate spec distance (normalized).
    """
    rng = rng or np.random.default_rng(0)
    n_anchor = int(round(a * M))
    b_ref = LEG_S * rng.standard_normal((n_seed, M))
    Ls = np.zeros((t_run + 1, n_seed))
    Cs = np.zeros((t_run + 1, n_seed))
    b = b_ref.copy()          # start at the pinned reference behavior
    c = 0.5 * rng.random((n_seed, K))
    Ls[0] = (b ** 2).sum(1) / (2.0 * M)
    Cs[0] = c.sum(1)
    for t in range(1, t_run + 1):
        xi = h * rng.standard_normal((n_seed, M))
        b_new = (1.0 - eta_mu) * b + xi
        if n_anchor > 0:
            b_new[:, :n_anchor] = b_ref[:, :n_anchor]
        b = b_new
        zeta = delta + h * rng.standard_normal((n_seed, K))
        c_new = c + np.maximum(0.0, zeta)
        if cap is not None:
            c_new = np.minimum(c_new, cap)
        c = c_new
        Ls[t] = (b ** 2).sum(1) / (2.0 * M)
        Cs[t] = c.sum(1)
    return Ls, Cs


def floor_theory(a, h, eta_mu=ETA_MU, s2=LEG_S ** 2):
    noise = (1.0 - a) * h ** 2 / (2.0 * (2.0 * eta_mu - eta_mu ** 2))
    legacy = a * s2 / 2.0
    return noise + legacy


def rho_theory(h, delta=0.04):
    """E max(0, N(delta, h^2)) per complexity coordinate."""
    from math import erf, sqrt, pi
    z = delta / h
    return h * (z * (0.5 * (1.0 + erf(z / sqrt(2)))) +
                np.exp(-z ** 2 / 2.0) / np.sqrt(2.0 * pi))


# ----------------------------------------------------------------------
# L2 — the ratchet law
# ----------------------------------------------------------------------
print('L2: ratchet')
t_r = 1500
L_no, C_no = simulate(0.0, 0.5, t_r, 12, cap=None, rng=rng)
L_anch, C_anch = simulate(0.6, 0.5, t_r, 12, cap=None, rng=rng)
L_cap, C_cap = simulate(0.6, 0.5, t_r, 12, cap=2.0, rng=rng)
rho_meas = (C_no[-1].mean() - C_no[0].mean()) / t_r
rho_th = K * rho_theory(0.5, 0.04)
RESULTS['L2_rho_measured'] = float(rho_meas)
RESULTS['L2_rho_theory'] = float(rho_th)
RESULTS['L2_rho_rel_err'] = float(abs(rho_meas - rho_th) / rho_th)
RESULTS['L2_anchor_leak'] = float((C_anch[-1].mean() - C_no[-1].mean()) /
                                  max(1e-9, C_no[-1].mean() - C_no[0].mean()))
RESULTS['L2_cap_pin'] = float(C_cap[-1].mean())
t_pin = (2.0 - 0.25) / rho_theory(0.5, 0.04)   # passes until the cap binds
RESULTS['L2_t_pin'] = float(t_pin)

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ts = np.arange(0, t_r + 1, 1)
ax.plot(ts, C_no.mean(1), color=CB[4], lw=2, label='no anchors')
ax.plot(ts, C_anch.mean(1), color=CB[0], lw=2,
        label='behavior anchors a=0.6')
ax.plot(ts, C_cap.mean(1), color=CB[2], lw=2, label='behavior + complexity cap')
ax.plot(ts, C_no[0].mean() + rho_th * ts, color=G400, ls='--', lw=1.4,
        label=r'law: $C_0 + \rho_R\, t$')
ax.plot(ts, np.minimum(C_cap[0].mean() + rho_th * ts, K * 2.0), color=G700,
        ls=':', lw=1.6, label=r'law: pinned at $k\cdot$cap')
ax.set_xlabel('agent passes $t$')
ax.set_ylabel(r'complexity $\mathbb{E}[C_t]$')
legend_above(ax, 'the ratchet: only caps stop it', ncol=2)
clean_axis(ax)

ax = axes[1]
# ratchet rate vs entropy h, measured vs theory
hs = np.linspace(0.05, 1.2, 12)
rr = []
for hh in hs:
    _, Cc = simulate(0.0, hh, 900, 8, cap=None, rng=rng)
    rr.append((Cc[-1].mean() - Cc[0].mean()) / 900)
rr = np.array(rr)
ax.plot(hs, K * np.array([rho_theory(hh) for hh in hs]), color=G400,
        ls='--', lw=1.6, label=r'law: $k\,\mathbb{E}\max(0,\mathcal{N}(\delta,h^2))$')
ax.plot(hs, rr, 'o', color=CB[2], ms=6, label='measured')
ax.set_xlabel(r'agent entropy $h$')
ax.set_ylabel(r'ratchet rate $\rho_R$')
legend_above(ax, 'ratchet rate vs proposal entropy', ncol=2)
clean_axis(ax)
RESULTS['L2_rate_fit_max_rel_err'] = float(np.max(np.abs(rr -
                       K * np.array([rho_theory(hh) for hh in hs])) /
                       (K * np.array([rho_theory(hh) for hh in hs]) + 1e-12)))
save(fig, 'f1-ratchet.png')

# ----------------------------------------------------------------------
# L1 — the floor law
# ----------------------------------------------------------------------
print('L1: floor')
hs_f = np.array([0.1, 0.2, 0.4, 0.8, 1.6])
as_f = [0.0, 0.3, 0.6, 0.9]
floors = {}
t_burn, t_avg = 1200, 600
for a in as_f:
    floors[a] = []
    for hh in hs_f:
        Ls, _ = simulate(a, hh, t_burn, 12, rng=rng)
        floors[a].append(Ls[-t_avg:].mean())
    floors[a] = np.array(floors[a])

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
for a, col in zip(as_f, [CB[4], CB[3], CB[1], CB[0]]):
    ax.loglog(hs_f, floors[a], 'o-', color=col, lw=1.8, ms=6,
              label='a = %.1f (measured)' % a)
    ax.loglog(hs_f, np.array([floor_theory(a, hh) for hh in hs_f]),
              color=col, ls='--', lw=1.1)
ax.loglog(hs_f, np.array([floor_theory(0.0, hh) for hh in hs_f]),
          color=G400, lw=0.0, label='law (dashed)')
ax.set_xlabel(r'agent entropy $h$')
ax.set_ylabel(r'maintenance floor $\mathbb{E}[L_\infty]$')
legend_above(ax, 'floor vs entropy: slope 2, split by coverage', ncol=2)
clean_axis(ax)

ax = axes[1]
# floor vs coverage at fixed h: the linear trade
hh_fix = 0.6
as_dense = np.linspace(0.0, 1.0, 11)
fl = []
for a in as_dense:
    Ls, _ = simulate(a, hh_fix, t_burn, 12, rng=rng)
    fl.append(Ls[-t_avg:].mean())
fl = np.array(fl)
ax.plot(as_dense, fl, 'o', color=CB[2], ms=6, label='measured')
ax.plot(as_dense, [floor_theory(a, hh_fix) for a in as_dense],
        color=G400, ls='--', lw=1.6,
        label=r'law: $(1-a)$ noise $+$ $a$ legacy')
ax.set_xlabel(r'anchor coverage $a$')
ax.set_ylabel(r'floor $\mathbb{E}[L_\infty]$')
ax.axhline(L_TOL, color=G900, ls=':', lw=1.2, label='tolerance $L_{tol}$')
legend_above(ax, 'the trade: noise floor against frozen legacy', ncol=2)
clean_axis(ax)

# residuals of the floor law across the (a, h) grid
res = []
for a in as_f:
    for hh, fm in zip(hs_f, floors[a]):
        res.append(abs(fm - floor_theory(a, hh)) /
                   (floor_theory(a, hh) + 1e-12))
RESULTS['L1_floor_max_rel_err'] = float(np.max(res))
RESULTS['L1_floor_median_rel_err'] = float(np.median(res))
save(fig, 'f2-floor.png')

# ----------------------------------------------------------------------
# L3 — the boundary law: success map in (a, h)
# ----------------------------------------------------------------------
print('L3: boundary')
a_grid = np.linspace(0.0, 1.0, 21)
h_grid = np.logspace(-1, 0.2, 15)          # 0.1 .. ~1.58
ok = np.zeros((len(a_grid), len(h_grid)))
for ia, a in enumerate(a_grid):
    for ih, hh in enumerate(h_grid):
        Ls, _ = simulate(a, hh, 1000, 6, rng=rng)
        ok[ia, ih] = Ls[-400:].mean() < L_TOL

# predicted boundary: a*(h) = (N - L_tol)/(N - Gamma), exact for the
# linear floor; Gamma = s^2/2 = 0.08 < L_tol = 0.12 so the boundary
# lives inside [0,1] and rises with h.
def N_noise(h, eta_mu=ETA_MU):
    return h ** 2 / (2.0 * (2.0 * eta_mu - eta_mu ** 2))

def a_min_pred(h, eta_mu=ETA_MU, l_tol=L_TOL, s2=LEG_S ** 2):
    N = N_noise(h, eta_mu)
    G = s2 / 2.0
    if N <= G:
        return 0.0
    return float(np.clip((N - l_tol) / (N - G), 0.0, 1.0))

fig, ax = plt.subplots(figsize=(7.4, 4.4), constrained_layout=True)
im = ax.imshow(ok.T, origin='lower', aspect='auto', cmap='RdYlGn', vmin=0, vmax=1,
               extent=[a_grid[0], a_grid[-1], np.log10(h_grid[0]),
                       np.log10(h_grid[-1])])
ax.set_yticks([-1, -0.5, 0, 0.2])
ax.set_yticklabels(['0.1', '0.32', '1.0', '1.58'])
hlin = np.logspace(-1, 0.2, 100)
ax.plot([a_min_pred(hh) for hh in hlin], np.log10(hlin),
        color=G900, lw=2.2, ls='--',
        label=r'exact law: $a^*(h)=\frac{N-L_{tol}}{N-\Gamma}$')
ax.plot([max(0.0, 1.0 - 2.0 * L_TOL * (2.0 * ETA_MU - ETA_MU ** 2) / hh ** 2)
         for hh in hlin], np.log10(hlin), color=CB[0], lw=1.6, ls=':',
        label=r'asymptote: $1-\kappa/h^2$')
ax.set_xlabel(r'anchor coverage $a$')
ax.set_ylabel(r'agent entropy $h$ (log)')
ax.legend(loc='upper right', bbox_to_anchor=(1.0, 1.0))
ax.set_title('stable maintenance: floor < tolerance', fontsize=12,
             fontweight='bold', pad=10)
save(fig, 'f3-boundary.png')

# boundary residual: measured a_min from the floor curve's crossing of
# L_tol (low-noise), compared with the prediction a_min(h)
meas_amin, pred_amin = [], []
for hh in [0.45, 0.55, 0.65, 0.85, 1.05, 1.25]:
    a_dense = np.linspace(0.0, 1.0, 21)
    fl_h = []
    for a in a_dense:
        Ls, _ = simulate(a, hh, 1000, 12, rng=rng)
        fl_h.append(Ls[-400:].mean())
    fl_h = np.array(fl_h)
    below = np.where(fl_h < L_TOL)[0]
    if len(below) > 0 and 0.05 < a_min_pred(hh) < 0.95:
        i0 = below[0]
        if i0 == 0:
            meas_amin.append(0.0)
        else:  # linear interpolation on the crossing
            a0, a1 = a_dense[i0 - 1], a_dense[i0]
            f0, f1 = fl_h[i0 - 1], fl_h[i0]
            meas_amin.append(a0 + (f0 - L_TOL) / (f0 - f1) * (a1 - a0))
        pred_amin.append(a_min_pred(hh))
meas_amin, pred_amin = np.array(meas_amin), np.array(pred_amin)
if len(meas_amin):
    RESULTS['L3_boundary_median_err'] = float(np.median(np.abs(
        meas_amin - pred_amin)))
    RESULTS['L3_boundary_n_points'] = int(len(meas_amin))
RESULTS['L3_asymptote_kappa'] = float(2 * L_TOL * (2 * ETA_MU - ETA_MU ** 2))

# ----------------------------------------------------------------------
# L4/L5 — trajectories + substitution
# ----------------------------------------------------------------------
print('L4/L5: trajectories and substitution')
cases = [
    ('a=0.2, h=0.5  (under-anchored)', 0.2, 0.5, CB[4]),
    ('a=0.8, h=0.5  (stable)', 0.8, 0.5, CB[2]),
    ('a=0.6, h=1.0  (high-entropy)', 0.6, 1.0, CB[3]),
    ('a=0.98, h=1.0  (near-total anchors)', 0.98, 1.0, CB[0]),
]
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
for lab, a, hh, col in cases:
    Ls, _ = simulate(a, hh, 800, 24, rng=rng)
    med = np.median(Ls, axis=1)
    q1, q3 = np.percentile(Ls, 25, axis=1), np.percentile(Ls, 75, axis=1)
    ax.plot(np.arange(801), med, color=col, lw=1.8, label=lab)
    ax.fill_between(np.arange(801), q1, q3, color=col, alpha=0.15, lw=0)
ax.axhline(L_TOL, color=G900, ls=':', lw=1.2)
ax.set_yscale('log')
ax.set_xlabel('agent passes $t$')
ax.set_ylabel(r'spec distance $L_t$ (median, IQR band)')
legend_above(ax, 'failure regimes and the stable regime', ncol=2)
clean_axis(ax)

ax = axes[1]
# substitution curve: a_min vs h for several review rates eta*mu
hh_s = np.logspace(-0.55, 0.2, 60)
for em, col, lab in [(0.15, CB[1], r'$\eta\mu=0.15$'),
                     (0.30, CB[0], r'$\eta\mu=0.30$'),
                     (0.60, CB[2], r'$\eta\mu=0.60$')]:
    a_star = [float(np.clip(
        (N_noise(hh, em) - L_TOL) / (N_noise(hh, em) - LEG_S ** 2 / 2),
        0.0, 1.0)) for hh in hh_s]
    ax.plot(hh_s, a_star, color=col, lw=2, label=lab)
ax.plot(hh_s, [max(0.0, 1.0 - 2.0 * L_TOL * (2.0 * ETA_MU - ETA_MU ** 2) / hh ** 2)
         for hh in hh_s], color=G400, lw=1.2, ls=':',
        label=r'asymptote $1-\kappa/h^2$ ($\eta\mu=0.3$)')
# measured points from the L3 map (ETA_MU case)
if len(meas_amin):
    ax.plot(h_grid[:len(meas_amin)], meas_amin, 'o', color=CB[4], ms=6,
            label='measured boundary')
ax.set_xscale('log')
ax.set_xlabel(r'agent entropy $h$')
ax.set_ylabel(r'required coverage $a_{min}$')
ax.set_ylim(-0.03, 1.03)
legend_above(ax, r'substitution: the burden curve $a^*(h)$', ncol=2)
clean_axis(ax)
RESULTS['L4_boundary_examples'] = [float(a_min_pred(0.5)), float(a_min_pred(1.0))]
RESULTS['L3_gamma'] = float(LEG_S ** 2 / 2.0)
save(fig, 'f4-trajectories.png')
save(fig, 'f5-substitution.png')

# ----------------------------------------------------------------------
# F6 — law validation summary
# ----------------------------------------------------------------------
print('F6: validation summary')
rows = [
    ('L2 ratchet rate measured / law', '%.4f / %.4f' % (
        RESULTS['L2_rho_measured'], RESULTS['L2_rho_theory'])),
    ('L2 ratchet rate rel. error', '%.2f%%' % (
        100 * RESULTS['L2_rho_rel_err'])),
    ('L2 behavior-anchor leak (fraction of ratchet)', '%.1e' % (
        abs(RESULTS['L2_anchor_leak']))),
    ('L2 cap pin level (cap = 2.0)', '%.3f' % RESULTS['L2_cap_pin']),
    ('L1 floor law median rel. err', '%.2f%%' % (
        100 * RESULTS['L1_floor_median_rel_err'])),
    ('L1 floor law max rel. err', '%.2f%%' % (
        100 * RESULTS['L1_floor_max_rel_err'])),
    ('L3 boundary median |err| in coverage', '%.3f' % (
        RESULTS.get('L3_boundary_median_err', -1))),
    ('L3 boundary points', '%d' % RESULTS.get('L3_boundary_n_points', 0)),
    ('L4 boundary a*(0.5) / a*(1.0)', '%.3f / %.3f' % tuple(
        RESULTS['L4_boundary_examples'])),
]
RESULTS['laws'] = [list(r) for r in rows]

fig, ax = plt.subplots(figsize=(7.6, 3.2), constrained_layout=True)
ax.axis('off')
tbl = ax.table(cellText=[[a, b] for a, b in rows],
               colLabels=['law', 'measured'],
               cellLoc='left', colLoc='left', loc='center')
tbl.auto_set_font_size(False)
tbl.set_fontsize(9.5)
tbl.scale(1.0, 1.5)
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_facecolor('#F3F4F6')
        cell.set_text_props(fontweight='bold')
    cell.set_edgecolor('#E5E7EB')
ax.set_title('law validation — all laws measured in this harness',
             fontsize=12, fontweight='bold', pad=14)
save(fig, 'f6-law-validation.png')

with open(os.path.join(OUT, 'results.json'), 'w') as f:
    json.dump(RESULTS, f, indent=2)
print('wrote results.json')
print(json.dumps(RESULTS, indent=2)[:1400])
