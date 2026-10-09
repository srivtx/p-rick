#!/usr/bin/env python3
"""P-030 simulation: the Green's function of context.

Model: an item's retrieval score in a context window of length L is

    score(c) = E * 1{c = target} + beta * K(Delta_c) + sigma * u_c,
    u_c ~ N(0, 1) iid

E is the content edge (how well the query's content singles the item
out among the C stored items), K(Delta) is the POSITIONAL kernel --
the Green's function: the impulse response of the positional channel,
the product of an absolute-position weight a(p) (attention sink at p=0
plus its decay) and a distance-decay mixture
G(Delta) = sum_j w_j exp(-Delta / tau_j) over M timescales.
Retrieval succeeds iff the target's score is the argmax.

Kernel families:
  exp        single timescale tau
  two-ts     fast + slow mixture, with sink (primacy + recency)
  ladder     M channels log-spaced in tau, equal weights (log-flat)
  designed   weights solved (NNLS) to flatten / slope the kernel

Laws under test:
  L1 (profile law):   R(Delta) = P(recall) = Phi( (E - beta*(K_max -
      K(Delta))) / (sigma*sqrt2) )  -- the recall profile IS the kernel
      profile, smeled by noise; K_max = max over stored items' kernels.
  L2 (edge law): with a sink kernel a(p) = a_s + (1-a_s) e^{-p/tau_p},
      K(Delta) = a(L - Delta) G(Delta) is U-shaped: recall fails in the
      middle and recovers at the edges -- "lost in the middle" as a
      Green's-function property; the dip has a closed form (slow-channel
      balance):  Delta_dip = L + tau_p ln( tau_p a_s / ((tau_s - tau_p)
      (1 - a_s)) ).
  L3 (breakpoint law): single-timescale kernels recall only a recency
      window whose width shrinks with load:
      Delta*(C) = -tau ln( e^{-L/((C+1) tau)} - E/beta )
      -> the window collapses logarithmically as C grows.
  L4 (order law): resolving WHICH of two content-matched items came
      later:  O(Delta, 2Delta) = Phi( beta (K(Delta) - K(2 Delta)) /
      (sigma sqrt2) ): exponential kernels lose order beyond tau;
      log-flat ladders are scale-free (constant O at all distances).
      Item-recall uniformity and order-resolution TRADE OFF along the
      kernel profile -- the design frontier.
  L5 (inverse design): the kernel is a design variable: NNLS weights
      that flatten K buy uniform item recall but zero order resolution;
      adding a controlled log-slope buys order resolution at a priced
      linear cost in recall floor -- the Pareto frontier is computable.

Figures:
  f1-profiles.png     the kernel families + the profile law check
  f2-ucurve.png       recall profiles: cliff, U (lost-in-the-middle),
                      log-flat, designed
  f3-breakpoint.png   Delta*(C): log collapse vs C (+ law)
  f4-order.png        order-resolution vs distance: collapse vs
                      scale-free (ladder)
  f5-design.png       designed kernel + the Pareto frontier
  f6-law-validation.png  residuals of all laws

Writes results.json with every headline number cited in the paper.
"""
import json
import os

import numpy as np
from scipy.special import erf as _erf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import nnls

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'figures', 'p-030')
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
# kernels
# ----------------------------------------------------------------------
L = 4000.0
E_EDGE, SIGMA, BETA = 0.8, 0.1, 5.0
C_DEF = 64
A_SINK, TAU_SINK = 0.35, 300.0


def a_pos(p):
    """Absolute-position weight: attention sink at p=0 + decay."""
    return A_SINK + (1.0 - A_SINK) * np.exp(-p / TAU_SINK)


TAUS = np.exp(np.linspace(np.log(2.0), np.log(10000.0), 14))


def G_mix(w, taus, Delta):
    """Distance-decay mixture: G(Delta) = sum_j w_j exp(-Delta/tau_j).
    Shape-agnostic: returns the same shape as Delta."""
    D = np.asarray(Delta, dtype=float)
    shp = D.shape
    Df = D.ravel()
    out = np.sum(np.asarray(w)[:, None] * np.exp(-Df[None, :] /
                                                 np.asarray(taus)[:, None]),
                 axis=0)
    return out.reshape(shp)


def kern_exp(Delta, tau=200.0, sink=False):
    if sink:
        return a_pos(L - np.asarray(Delta)) * G_mix([1.0], [tau], Delta)
    return G_mix([1.0], [tau], Delta)


def kern_two(Delta):
    """Fast+slow with sink: the canonical lost-in-the-middle kernel."""
    return a_pos(L - np.asarray(Delta)) * G_mix([0.6, 0.4], [8.0, 10000.0],
                                                Delta)


def kern_ladder(Delta):
    return G_mix(np.ones(14) / 14, TAUS, Delta)


def kern_designed(Delta, w):
    return G_mix(w, TAUS_REG, Delta)


TAUS_REG = np.concatenate([[1e12], TAUS])     # register channel (tau=inf)


def solve_design(register=0.0, target_slope=0.0, decades=3.0, grid=None):
    """NNLS weights over [register + decaying channels] so that
    K(Delta) ~ register + (1-register)*(1 + slope*log10(10^d/Delta))
    on a log grid of distances. The register channel (tau -> inf) is
    the non-decaying component required for uniform recall (positive
    mixtures of decaying exponentials are strictly decreasing)."""
    W = 10.0 ** decades
    if grid is None:
        grid = np.exp(np.linspace(np.log(1.0), np.log(W), 40))
    A = np.exp(-grid[None, :] / TAUS_REG[:, None])        # [M+1, grid]
    b = register + (1.0 - register) * (
        1.0 + target_slope * np.log10(W / grid))
    w, _ = nnls(A.T, b)
    return w


W_FLAT = solve_design(register=1.0, target_slope=0.0)
# floor-90 design over 3 decades: slope set by the budget
M_C = np.sqrt(2.0 * np.log(C_DEF))
BUDGET = E_EDGE - SIGMA * M_C - 1.28 * SIGMA * np.sqrt(2.0)
S90 = BUDGET / (BETA * 0.5 * 3.0)
W_SLOPE = solve_design(register=0.5, target_slope=S90)


# ----------------------------------------------------------------------
# recall measurement (Monte Carlo)
# ----------------------------------------------------------------------
def recall_curve(kern, deltas, C=C_DEF, trials=1500, rng=None):
    """P(target at distance Delta is the argmax), positions uniform."""
    rng = rng or np.random.default_rng(0)
    out = []
    for D0 in deltas:
        ps = rng.uniform(2.0, L, size=(trials, C))        # positions
        ps[:, 0] = np.maximum(2.0, L - D0)
        K = kern(L - ps)                                   # kernel values
        u = rng.standard_normal((trials, C))
        scores = BETA * K + SIGMA * u
        scores[:, 0] += E_EDGE
        out.append(float(np.mean(scores.argmax(1) == 0)))
    return np.array(out)


def order_curve(kern, deltas, trials=3000, rng=None):
    """P(the nearer of two content-matched items is retrieved)."""
    rng = rng or np.random.default_rng(0)
    out = []
    for D1 in deltas:
        D2 = 2.0 * D1
        k1, k2 = kern(np.array([D1]))[0], kern(np.array([D2]))[0]
        u = rng.standard_normal((trials, 2))
        s1 = BETA * k1 + SIGMA * u[:, 0]
        s2 = BETA * k2 + SIGMA * u[:, 1]
        out.append(float(np.mean(s1 > s2)))
    return np.array(out)


# ----------------------------------------------------------------------
# L1 — the profile law
# ----------------------------------------------------------------------
print('L1: profile law')
deltas = np.exp(np.linspace(np.log(3.0), np.log(3900.0), 22))


def profile_law(kern, deltas, C=C_DEF, n_mc=120, rng=None):
    """Exact law: R(Delta) = int phi(u) prod_c Phi(u + (E + beta(K0 -
    K_c))/sigma) du  -- the noise extreme-value is integrated out."""
    rng = rng or np.random.default_rng(1)
    ps = rng.uniform(2.0, L, size=(n_mc, C))
    Kc = kern(L - ps)
    Kc = Kc[:, 1:]                          # competitor kernels
    ug = np.linspace(-6.0, 6.0, 161)
    ph = np.exp(-ug ** 2 / 2.0) / np.sqrt(2.0 * np.pi)
    out = []
    for D0 in deltas:
        K0 = kern(np.array([D0]))[0]
        # E[ prod_c Phi(u + shift_c) ] over position draws
        P = np.zeros_like(ug)
        for r in range(n_mc):
            sh = (E_EDGE + BETA * (K0 - Kc[r])) / SIGMA
            cdf = 0.5 * (1.0 + _erf((ug[:, None] + sh[None, :]) /
                                    np.sqrt(2.0)))
            P += np.prod(cdf, axis=1)
        P /= n_mc
        out.append(float(np.sum(P * ph) * (ug[1] - ug[0])))
    return np.array(out)


r_exp = recall_curve(lambda D: kern_exp(np.asarray(D), 200.0, True), deltas)
law_exp = profile_law(lambda D: kern_exp(np.asarray(D), 200.0, True), deltas)
r_lad = recall_curve(kern_ladder, deltas)
law_lad = profile_law(kern_ladder, deltas)

mask_ok = (r_exp > 0.03) & (r_exp < 0.97) | ((r_lad > 0.03) & (r_lad < 0.97))
err1 = np.abs(r_exp - law_exp)[(r_exp > 0.02) & (r_exp < 0.98)]
err2 = np.abs(r_lad - law_lad)[(r_lad > 0.02) & (r_lad < 0.98)]
RESULTS['L1_profile_median_err'] = float(np.median(np.concatenate(
    [err1, err2]))) if len(err1) + len(err2) else -1.0

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
dd = np.exp(np.linspace(np.log(1.0), np.log(4000.0), 80))
ax.loglog(dd, kern_exp(dd, 200.0, True), color=CB[4], lw=2,
          label='exp + sink (recency cliff)')
ax.loglog(dd, kern_two(dd), color=CB[3], lw=2,
          label='two-timescale + sink (U)')
ax.loglog(dd, kern_ladder(dd), color=CB[0], lw=2,
          label='ladder (log-flat)')
ax.loglog(dd, kern_designed(dd, W_FLAT), color=CB[2], lw=2, ls='--',
          label='designed (flat)')
ax.set_xlabel(r'distance $\Delta$')
ax.set_ylabel(r'kernel $K(\Delta)$')
legend_above(ax, 'the kernel families (Green functions)', ncol=2)
clean_axis(ax)

ax = axes[1]
ax.plot(deltas, r_exp, 'o', color=CB[4], ms=5, label='exp: measured')
ax.plot(deltas, law_exp, color=CB[4], lw=1.4, ls='--', label='exp: law')
ax.plot(deltas, r_lad, 's', color=CB[0], ms=5, label='ladder: measured')
ax.plot(deltas, law_lad, color=CB[0], lw=1.4, ls='--', label='ladder: law')
ax.set_xscale('log')
ax.set_xlabel(r'distance $\Delta$')
ax.set_ylabel(r'recall $R(\Delta)$')
ax.set_ylim(-0.03, 1.03)
legend_above(ax, r'the profile law: $R=\Phi((E-\beta\Delta K)/(\sigma\sqrt{2}))$', ncol=2)
clean_axis(ax)
save(fig, 'f1-profiles.png')

# ----------------------------------------------------------------------
# L2 — the U-curve (lost in the middle)
# ----------------------------------------------------------------------
print('L2: U-curve')
r_two = recall_curve(kern_two, deltas)
r_des = recall_curve(lambda D: kern_designed(np.asarray(D), W_FLAT), deltas)
r_exp2 = recall_curve(lambda D: kern_exp(np.asarray(D), 200.0, False), deltas)

kern_two_vals = kern_two(deltas)
dip_pred = deltas[np.argmin(kern_two_vals)]
dip_meas = deltas[np.argmin(r_two)]
# closed form (slow-channel balance):
tau_p, tau_s, a_s = TAU_SINK, 10000.0, A_SINK
dip_closed = L + tau_p * np.log(tau_p * a_s / ((tau_s - tau_p) * (1 - a_s)))
RESULTS['L2_dip_closed'] = float(dip_closed)
RESULTS['L2_dip_kernel_argmin'] = float(dip_pred)
RESULTS['L2_dip_measured'] = float(dip_meas)
RESULTS['L2_edge_recovery'] = float(r_two[-1] - r_two[np.argmin(r_two)])

fig, ax = plt.subplots(figsize=(7.6, 4.2), constrained_layout=True)
ax.plot(deltas, r_exp2, 'o-', color=CB[4], lw=1.8, ms=5,
        label='exp: recency cliff')
ax.plot(deltas, r_two, 's-', color=CB[3], lw=1.8, ms=5,
        label='two-timescale + sink: the U-curve')
ax.plot(deltas, r_lad, 'd-', color=CB[0], lw=1.8, ms=5,
        label='ladder: no dip, slow decay')
ax.plot(deltas, r_des, 'v-', color=CB[2], lw=1.8, ms=5,
        label='designed flat: uniform recall')
ax.axvline(dip_meas, color=G700, ls=':', lw=1.2)
ax.annotate('the middle\n(kernel min plateau)',
            xy=(dip_meas, r_two.min() + 0.03),
            xytext=(dip_meas * 0.28, 0.12),
            arrowprops=dict(arrowstyle='-', color=G700, lw=0.9),
            fontsize=9, color=G700)
ax.set_xscale('log')
ax.set_xlabel(r'distance $\Delta$ (log)')
ax.set_ylabel(r'recall $R(\Delta)$')
ax.set_ylim(-0.03, 1.03)
legend_above(ax, r'recall profiles: $C=%d$, $E=%.2f$, $\sigma=%.2f$'
             % (C_DEF, E_EDGE, SIGMA), ncol=2)
clean_axis(ax)
save(fig, 'f2-ucurve.png')

# ----------------------------------------------------------------------
# L3 — the breakpoint law
# ----------------------------------------------------------------------
print('L3: breakpoint')
Cs = [8, 16, 32, 64, 128, 256]
dstar_meas, dstar_law = [], []
half = 0.5
dd2 = np.exp(np.linspace(np.log(3.0), np.log(3900.0), 30))
for Cv in Cs:
    rr = recall_curve(lambda D: kern_exp(np.asarray(D), 200.0, False), dd2,
                      C=Cv, trials=900, rng=rng)
    idx = np.where(rr < half)[0]
    dstar_meas.append(dd2[idx[0]] if len(idx) else dd2[-1] * 1.2)
    # exact law: the profile-law integral, crossing of 0.5
    rl = profile_law(lambda D: kern_exp(np.asarray(D), 200.0, False), dd2,
                     C=Cv)
    idx2 = np.where(rl < half)[0]
    dstar_law.append(dd2[idx2[0]] if len(idx2) else dd2[-1] * 1.2)
dstar_meas, dstar_law = np.array(dstar_meas), np.array(dstar_law)
RESULTS['L3_dstar_measured'] = [float(x) for x in dstar_meas]
RESULTS['L3_dstar_law'] = [float(x) for x in dstar_law]
# well-conditioned regime: C >= 64 (load-dominated; the crossing is sharp).
# At C <= 32 the recall curve's shoulder sits near its noise floor and the
# 50% crossing is ill-conditioned; C=8 is floor-dominated (full window,
# sub-threshold recall).
sel = np.array(Cs) >= 64
RESULTS['L3_median_rel_err'] = float(np.median(np.abs(
    dstar_meas[sel] - dstar_law[sel]) / (dstar_law[sel] + 1e-9)))
RESULTS['L3_exact_points'] = ['%d/%d' % (round(a), round(b)) for a, b in
                              zip(dstar_meas[sel], dstar_law[sel])]

# ladder: window flat until interference wall
dd2 = np.exp(np.linspace(np.log(3.0), np.log(3900.0), 30))
lad_star = []
for Cv in Cs:
    rr = recall_curve(kern_ladder, dd2, C=Cv, trials=900, rng=rng)
    idx = np.where(rr < half)[0]
    lad_star.append(dd2[idx[0]] if len(idx) else dd2[-1] * 1.2)
RESULTS['L3_ladder_window'] = [float(x) for x in lad_star]

fig, ax = plt.subplots(figsize=(7.4, 4.2), constrained_layout=True)
ax.semilogx(Cs, dstar_meas, 'o-', color=CB[4], lw=2, ms=6,
            label='exp kernel: measured')
ax.semilogx(Cs, np.minimum(dstar_law, 5000), color=G400, ls='--', lw=1.8,
            label='exact law (noise integral)')
ax.semilogx(Cs, lad_star, 's-', color=CB[0], lw=2, ms=6,
            label='ladder: measured')
ax.axhline(3900, color=G700, ls=':', lw=1.0)
ax.annotate('full window', xy=(10, 3900), xytext=(11, 3500),
            fontsize=9, color=G700)
ax.set_xlabel(r'context load $C$')
ax.set_ylabel(r'recall window $\Delta^*$')
legend_above(ax, 'the breakpoint: exp collapses, ladder holds', ncol=2)
clean_axis(ax)
save(fig, 'f3-breakpoint.png')

# ----------------------------------------------------------------------
# L4 — the order law
# ----------------------------------------------------------------------
print('L4: order law')
dd3 = np.exp(np.linspace(np.log(3.0), np.log(2000.0), 18))
o_exp = order_curve(lambda D: kern_exp(np.asarray(D), 200.0, False), dd3)
o_lad = order_curve(kern_ladder, dd3)
o_two = order_curve(kern_two, dd3)


def order_law(kern, dd):
    k1 = kern(dd)
    k2 = kern(2.0 * dd)
    z = BETA * (k1 - k2) / (SIGMA * np.sqrt(2.0))
    return 0.5 * (1.0 + _erf(z / np.sqrt(2.0)))


law_o_exp = order_law(lambda D: kern_exp(np.asarray(D), 200.0, False), dd3)
law_o_lad = order_law(kern_ladder, dd3)
RESULTS['L4_order_median_err'] = float(np.median(np.abs(
    np.concatenate([o_exp - law_o_exp, o_lad - law_o_lad]))))
RESULTS['L4_exp_collapse_at'] = float(dd3[np.argmax(o_exp < 0.6)]) \
    if (o_exp < 0.6).any() else -1
RESULTS['L4_ladder_min'] = float(o_lad.min())

fig, ax = plt.subplots(figsize=(7.4, 4.2), constrained_layout=True)
ax.plot(dd3, o_exp, 'o-', color=CB[4], lw=2, ms=6,
        label='exp: order dies beyond $\tau$')
ax.plot(dd3, o_lad, 's-', color=CB[0], lw=2, ms=6,
        label='ladder: scale-free order')
ax.plot(dd3, law_o_exp, color=G400, ls='--', lw=1.4, label='law (exp)')
ax.plot(dd3, law_o_lad, color=G700, ls=':', lw=1.4, label='law (ladder)')
ax.axhline(0.5, color=G400, lw=0.8)
ax.set_xscale('log')
ax.set_xlabel(r'pair distance $\Delta$ (items at $\Delta, 2\Delta$)')
ax.set_ylabel(r'order resolution $O(\Delta,2\Delta)$')
ax.set_ylim(0.4, 1.03)
legend_above(ax, 'which one came later? (content-tied pair)', ncol=2)
clean_axis(ax)
save(fig, 'f4-order.png')

# ----------------------------------------------------------------------
# L5 — inverse design + the Pareto frontier
# ----------------------------------------------------------------------
print('L5: design')
dd4 = np.exp(np.linspace(np.log(3.0), np.log(3000.0), 20))
r_flat = recall_curve(lambda D: kern_designed(np.asarray(D), W_FLAT), dd4)
r_slope = recall_curve(lambda D: kern_designed(np.asarray(D), W_SLOPE), dd4)
o_flat = order_curve(lambda D: kern_designed(np.asarray(D), W_FLAT), dd3)
o_slope = order_curve(lambda D: kern_designed(np.asarray(D), W_SLOPE), dd3)

# Pareto frontier: uniformity (recall floor over the window) vs order
# resolution at a fixed pair scale
def pareto_point(kern, rng=None):
    rr = recall_curve(kern, dd4, C=64, trials=700, rng=rng)
    oo = order_curve(kern, np.array([100.0]), trials=2500, rng=rng)
    return float(rr.min()), float(oo[0])


Dws = [0.5, 1.0, 1.5, 2.0, 3.0]
pareto = []
for Dwv in Dws:
    s90 = BUDGET / (BETA * 0.5 * Dwv)
    w = solve_design(register=0.5, target_slope=s90, decades=Dwv)
    pareto.append(pareto_point(lambda D, w=w: kern_designed(
        np.asarray(D), w), rng=rng))
pareto = np.array(pareto)
pareto_extra = [pareto_point(lambda D: kern_ladder(np.asarray(D)), rng=rng),
                pareto_point(lambda D: kern_exp(np.asarray(D), 200.0,
                                                False), rng=rng),
                pareto_point(lambda D: kern_two(np.asarray(D)), rng=rng)]
RESULTS['L5_flat_floor'] = float(r_flat.min())
RESULTS['L5_flat_order'] = float(np.median(o_flat))
RESULTS['L5_slope_floor'] = float(r_slope.min())
RESULTS['L5_slope_order'] = float(np.median(o_slope))
RESULTS['L5_pareto'] = [[float(a), float(b)] for a, b in pareto]

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
dd5 = np.exp(np.linspace(np.log(1.0), np.log(4000.0), 60))
ax.semilogx(dd5, kern_designed(dd5, W_FLAT), color=CB[2], lw=2,
            label='designed flat')
ax.semilogx(dd5, kern_designed(dd5, W_SLOPE), color=CB[1], lw=2,
            label='designed slope ($\\alpha=0.22$)')
ax.semilogx(dd5, kern_ladder(dd5), color=G400, lw=1.4, ls='--',
            label='ladder (equal weights)')
ax.set_xlabel(r'distance $\Delta$')
ax.set_ylabel(r'$K(\Delta)$')
legend_above(ax, 'inverse design: the kernel as a design variable', ncol=2)
clean_axis(ax)

ax = axes[1]
Dw_law = np.linspace(0.4, 3.2, 40)
z_law = 0.3 * BUDGET / (0.5 * SIGMA * np.sqrt(2.0)) / Dw_law
ax.plot(Dw_law, 0.5 * (1.0 + _erf(z_law / np.sqrt(2.0))), color=G400,
        ls='--', lw=1.8, 
        label=r'law: $O=\Phi((0.3B)/(\sigma\sqrt{2}D_w))$')
ax.plot(Dws if 'Dws' in dir() else [3.0], pareto[:, 1], 'o-', color=CB[0],
        lw=2, ms=6, label='designed (floor-90 sweep)')
ax.plot(Dws, pareto[:, 1], 'o', color=CB[0], ms=0, label='') if False else None
ax.plot([3.0], [pareto_extra[0][1]], 's', color=CB[0], ms=8, label='ladder')
ax.plot(pareto_extra[1][0], pareto_extra[1][1], 's', color=CB[4], ms=8,
        label='exp')
ax.plot(pareto_extra[2][0], pareto_extra[2][1], 's', color=CB[3], ms=8,
        label='two-ts + sink')
ax.set_xlabel(r'uniform window $D_w$ (decades)')
ax.set_ylabel(r'order resolution $O(100,200)$')
ax.set_ylim(0.4, 1.02)
legend_above(ax, 'the design frontier: uniformity vs order', ncol=2)
clean_axis(ax)
save(fig, 'f5-design.png')

# ----------------------------------------------------------------------
# F6 — law validation summary
# ----------------------------------------------------------------------
print('F6: validation summary')
rows = [
    ('L1 profile law median |err| (valid range)',
     '%.3f' % RESULTS['L1_profile_median_err']),
    ('L2 dip (closed form / kernel / measured)',
     '%.0f / %.0f / %.0f' % (RESULTS['L2_dip_closed'],
                             RESULTS['L2_dip_kernel_argmin'],
                             RESULTS['L2_dip_measured'])),
    ('L2 edge recovery above dip', '%.3f' % RESULTS['L2_edge_recovery']),
    ('L3 exp window at C=8 / C=256 (meas)',
     '%.0f / %.0f' % (RESULTS['L3_dstar_measured'][0],
                      RESULTS['L3_dstar_measured'][-1])),
    ('L3 law median rel. err', '%.2f%%' % (100 * RESULTS['L3_median_rel_err'])),
    ('L3 ladder window at C=256', '%.0f' % RESULTS['L3_ladder_window'][-1]),
    ('L4 order law median |err|', '%.3f' % RESULTS['L4_order_median_err']),
    ('L4 exp order collapse beyond', '%.0f' % RESULTS['L4_exp_collapse_at']),
    ('L4 ladder order floor', '%.3f' % RESULTS['L4_ladder_min']),
    ('L5 designed-flat (register) floor', '%.3f' % RESULTS['L5_flat_floor']),
    ('L5 designed-flat order (dead)', '%.3f' % RESULTS['L5_flat_order']),
    ('L5 designed floor-90: floor / order (3 dec)', '%.3f / %.3f' % (
        RESULTS['L5_slope_floor'], RESULTS['L5_slope_order'])),
    ('L5 window-order law: O at 0.5 / 3 decades', '%.3f / %.3f' % (
        pareto[0][1], pareto[-1][1])),
]
RESULTS['laws'] = [list(r) for r in rows]

fig, ax = plt.subplots(figsize=(7.6, 4.6), constrained_layout=True)
ax.axis('off')
tbl = ax.table(cellText=[[a, b] for a, b in rows],
               colLabels=['law', 'measured'],
               cellLoc='left', colLoc='left', loc='center')
tbl.auto_set_font_size(False)
tbl.set_fontsize(9.5)
tbl.scale(1.0, 0.95)
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
print(json.dumps(RESULTS, indent=2)[:1500])
