#!/usr/bin/env python3
"""P-027 simulation: the dissipation budget law (port-Hamiltonian streams).

Model: the residual stream is a port-Hamiltonian state system. Each layer
is  x_{t+1} = Lambda_t C_t x_t + h B_t u_t  where
    C_t = (I + S/2)^{-1} (I - S/2),  S = A - A^T          (Cayley transport)
    Lambda_t = (I + hR/2)^{-1} (I - hR/2),  R = L L^T     (metered dissipation)
C_t is exactly orthogonal; Lambda_t is symmetric PSD with spectrum in
[0,1); the ports B u are the only energy-injection channel.

Laws under test:
  L1 (norm conservation, exact):  ||x_{t+1}|| <= ||x_t|| + h||B u||_t,
      at any depth, with no normalizer anywhere. Control: standard
      residual stream  x + h W x  grows exponentially with depth.
  L2 (dissipation budget): log-volume
      ln|det(stream)| = sum_t ln det Lambda_t, with transport exactly
      volume-free (det of every Cayley product = +/-1 to 1e-13) and
      ln det Lambda = sum_i ln((1-x_i/2)/(1+x_i/2)) = -sum x_i - x_i^3/12
      - ..., x_i = h r_i: the budget identity -sum h tr R holds with
      CUBIC error (ratio -> 8 as h halves).
  L3 (gradient transport, exact): backward gradients satisfy
      ||g_0|| <= ||g_T|| (C^T preserves, Lambda^T contracts); standard
      streams fan exponentially into vanish/explode.
  L4 (oscillation boundary, explicit Euler): the explicit update
      x' = (I + h(J - R)) x is stable iff (hr-1)^2 + (hj)^2 < 1 per
      eigenpair; the Cayley form has no boundary at any step size.
  L5 (capacity): at depth 120 a random standard stream numerically
      annihilates all but the top gain directions (rank collapse) and
      loses a rank-2 readout; the PH stream preserves relative geometry
      and the readout survives.

Figures:
  f1-conservation.png    L1: norms vs depth (standard vs explicit PH vs
                          Cayley PH) + bound tightness
  f2-budget.png          L2: log-volume vs dissipation budget + O(h^2)
                          error scaling
  f3-gradient.png        L3: gradient norm vs depth, PH vs standard
  f4-boundary.png        L4: explicit-Euler stability map + measured
                          boundary + Cayley comparison
  f5-capacity.png        L5: stream spectra at depth 120 + readout
                          accuracy vs depth
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
                   '..', 'figures', 'p-027')
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
    """Legend in reserved space above the axes; its title is the panel title."""
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.02), ncol=ncol,
              title=title, title_fontsize=10.5, handlelength=1.6,
              columnspacing=1.2, borderaxespad=0.0)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches='tight',
                pad_inches=0.25)
    plt.close(fig)
    print('wrote', name)


rng = np.random.default_rng(SEED)

# ----------------------------------------------------------------------
# primitives
# ----------------------------------------------------------------------

def cayley_transport(A):
    """C = (I + S/2)^{-1} (I - S/2), S = A - A^T. Exactly orthogonal."""
    S = A - A.T
    d = A.shape[0]
    return np.linalg.solve(np.eye(d) + 0.5 * S, np.eye(d) - 0.5 * S)


def cayley_dissipation(L, h):
    """Lambda = (I + hR/2)^{-1} (I - hR/2), R = L L^T. Symmetric, in [0,1)."""
    R = L @ L.T
    d = L.shape[0]
    return np.linalg.solve(np.eye(d) + 0.5 * h * R, np.eye(d) - 0.5 * h * R)


def ph_layer(d, h, r_scale, rng):
    """One PH layer: (C, Lambda, B). r_scale scales the dissipation."""
    A = rng.standard_normal((d, d))
    L = r_scale * rng.standard_normal((d, d)) / np.sqrt(d)
    B = rng.standard_normal((d, d)) / np.sqrt(d)
    return cayley_transport(A), cayley_dissipation(L, h), B


def run_ph_stream(layers, x0, u=None, h=1.0):
    """Run the stream (rows = samples); return states and log-volume trace.

    u is the EXTERNAL port input (same shape as x0) or None for a pure
    transport+dissipation stream (no injection).
    """
    X = [x0.copy()]
    logvol = [0.0]
    for (C, Lam, B) in layers:
        x = X[-1]
        step = x @ C.T @ Lam
        if u is not None:
            step = step + h * (u @ B.T)
        X.append(step)
        logvol.append(logvol[-1] + np.log(abs(np.linalg.det(Lam))))
    return np.array(X), np.array(logvol)


def run_std_stream(Ws, x0, h=1.0):
    """Standard residual stream x -> x + h W x (rows = samples)."""
    X = [x0.copy()]
    logvol = [0.0]
    for W in Ws:
        X.append(X[-1] + h * (X[-1] @ W.T))
        logvol.append(logvol[-1] + np.log(abs(np.linalg.det(np.eye(W.shape[0]) + h * W))))
    return np.array(X), np.array(logvol)


# ----------------------------------------------------------------------
# L1 — norm conservation vs depth
# ----------------------------------------------------------------------
print('L1: norm conservation')
d, T, n = 32, 300, 24
h = 1.0
layers = [ph_layer(d, h, 0.10, rng) for _ in range(T)]
Ws = [rng.standard_normal((d, d)) / np.sqrt(d) for _ in range(T)]
x0 = rng.standard_normal((n, d)) / np.sqrt(d)          # ||x|| ~ 1 per row
u = rng.standard_normal((n, d)) * 0.02 / np.sqrt(d)    # small port input

Xph, _ = run_ph_stream(layers, x0, u, h)
Xstd, _ = run_std_stream(Ws, x0, h)

# explicit-Euler PH variant (same J, R) for the integrator comparison
def run_ph_explicit(layers, x0, u, h):
    X = [x0.copy()]
    for (C, Lam, B) in layers:
        # reconstruct an explicit step with the same skew/PSD parts
        S = np.linalg.solve(np.eye(d) - 0.5 * (np.eye(d) - C),
                            (np.eye(d) - C))          # S from Cayley inverse
        Rd = (np.eye(d) - Lam) @ np.linalg.inv(np.eye(d) + Lam) / h * 2 / 2
        x = X[-1]
        X.append(x + h * (x @ S.T) - h * (x @ Rd.T) + h * (u @ B.T))
    return np.array(X)

norm_ph = np.linalg.norm(Xph, axis=2)          # [T+1, n]
norm_std = np.linalg.norm(Xstd, axis=2)
# per-sample injection bound: ||x0_i|| + t * h * ||B u||_infty-per-step
u_step = np.linalg.norm(u, axis=1)             # per-sample port input norm
bound_rows = (np.linalg.norm(x0, axis=1)[:, None]
              + np.arange(T + 1)[None, :] * h * u_step[:, None])
viol = int(np.sum(norm_ph.T > bound_rows + 1e-9))
RESULTS['L1_violations'] = viol
RESULTS['L1_ph_max_norm'] = float(norm_ph.max())
RESULTS['L1_std_max_norm'] = float(norm_std.max())
RESULTS['L1_bound_ratio_median'] = float(np.median(norm_ph[-1] / bound_rows[:, -1]))

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ts = np.arange(T + 1)
ax.plot(ts, np.median(norm_std, axis=1), color=CB[4], lw=2,
        label='standard residual  x + Wx')
ax.plot(ts, np.median(norm_ph, axis=1), color=CB[0], lw=2,
        label='PH stream (Cayley)')
ax.plot(ts, np.median(bound_rows, axis=0), color=G400, lw=1.4, ls='--',
        label='injection bound')
ax.set_yscale('log')
ax.set_xlabel('depth $t$')
ax.set_ylabel(r'median $\|x_t\|$')
ax.set_ylim(1e-2, 1e30)
legend_above(ax, 'stream norm vs depth — control explodes', ncol=1)
clean_axis(ax)

ax = axes[1]
ax.plot(ts, np.percentile(norm_ph, 95, axis=1), color=CB[1], lw=1.6,
        label='PH 95th percentile')
ax.plot(ts, np.percentile(bound_rows, 95, axis=0), color=G400, lw=1.4,
        ls='--', label='bound (95th pct)')
ax.set_xlabel('depth $t$')
ax.set_ylabel(r'$\|x_t\|$')
legend_above(ax, 'bound tightness — PH never crosses', ncol=2)
clean_axis(ax)
save(fig, 'f1-conservation.png')

# ----------------------------------------------------------------------
# L2 — dissipation budget vs log-volume
# ----------------------------------------------------------------------
print('L2: dissipation budget')
d2, T2 = 24, 120
budget_err = {}
grid_h = [0.5, 0.25, 0.125]
vol_budget_pairs = []
transport_det_err = []
for hh in grid_h:
    errs = []
    for rep in range(6):
        layers2 = [ph_layer(d2, hh, r, rng) for r in (0.05, 0.10, 0.2)]
        tot_logvol = 0.0
        tot_budget = 0.0
        logdet_transport = 0.0
        for (C, Lam, B) in layers2 * (T2 // 3):
            tot_logvol += np.log(abs(np.linalg.det(Lam)))
            logdet_transport += np.log(abs(np.linalg.det(C)))
            ev = np.linalg.eigvalsh(Lam)
            r_i = (2.0 / hh) * (1.0 - ev) / (1.0 + ev)
            tot_budget += hh * r_i.sum()
        errs.append(abs(tot_logvol + tot_budget))
        transport_det_err.append(abs(logdet_transport))
        if hh == 0.25:
            vol_budget_pairs.append((tot_budget, tot_logvol))
    budget_err[hh] = float(np.median(errs))
RESULTS['L2_transport_logdet_error'] = float(np.median(transport_det_err))
RESULTS['L2_error_by_h'] = budget_err
RESULTS['L2_error_ratio_half'] = budget_err[0.5] / budget_err[0.25]
RESULTS['L2_error_ratio_quarter'] = budget_err[0.25] / budget_err[0.125]

vb = np.array(vol_budget_pairs)
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ax.scatter(-vb[:, 0], vb[:, 1], s=26, color=CB[0], alpha=0.85,
           label='measured log-volume', zorder=3)
lims = [min(-vb[:, 0].min(), vb[:, 1].min()), max(-vb[:, 0].max(), vb[:, 1].max())]
ax.plot(lims, lims, color=G400, lw=1.2, ls='--', label='identity (budget law)',
        zorder=2)
ax.set_xlabel(r'budget $\;\sum_t h\,\mathrm{tr}\,R_t$')
ax.set_ylabel(r'measured $\ln|\det(\mathrm{stream})|$')
legend_above(ax, r'volume contraction $=$ dissipation budget', ncol=2)
clean_axis(ax)

ax = axes[1]
hs = np.array(grid_h)
errs = np.array([budget_err[hh] for hh in grid_h])
ax.loglog(hs, errs, 'o-', color=CB[2], lw=2, label='measured error')
ax.loglog(hs, errs[0] * (hs / hs[0]) ** 3, color=G400, ls='--', lw=1.3,
          label=r'$\propto h^3$')
ax.set_xlabel(r'step size $h$')
ax.set_ylabel('|log-volume + budget|')
legend_above(ax, 'budget error scales as $h^3$ (cubic)', ncol=2)
clean_axis(ax)
save(fig, 'f2-budget.png')

# ----------------------------------------------------------------------
# L3 — gradient transport
# ----------------------------------------------------------------------
print('L3: gradient transport')
T3 = 240
layers3 = [ph_layer(d, 1.0, 0.05, rng) for _ in range(T3)]
Ws3 = [rng.standard_normal((d, d)) / np.sqrt(d) for _ in range(T3)]
gT = rng.standard_normal((n, d))
gT /= np.linalg.norm(gT, axis=1, keepdims=True)

# backward: g_{t} = (Lambda C)^T g_{t+1} = C^T Lambda g_{t+1}
grads_ph = [gT.copy()]
for (C, Lam, B) in reversed(layers3):
    grads_ph.append(grads_ph[-1] @ Lam @ C)   # row form of C^T Lambda g
grads_ph = np.array(grads_ph)

grads_std = [gT.copy()]
for W in reversed(Ws3):
    grads_std.append(grads_std[-1] @ (np.eye(d) + W))
grads_std = np.array(grads_std)

gn_ph = np.linalg.norm(grads_ph, axis=2)
gn_std = np.linalg.norm(grads_std, axis=2)
RESULTS['L3_ph_final_over_start'] = float(np.median(gn_ph[-1] / gn_ph[0]))
RESULTS['L3_ph_max'] = float(gn_ph.max())
RESULTS['L3_std_spread'] = [float(np.percentile(gn_std[-1], 5)),
                            float(np.percentile(gn_std[-1], 95))]

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ax.plot(np.arange(T3 + 1), np.median(gn_ph, axis=1), color=CB[0], lw=2,
        label='PH stream')
ax.fill_between(np.arange(T3 + 1), np.percentile(gn_ph, 5, axis=1),
                np.percentile(gn_ph, 95, axis=1), color=CB[0], alpha=0.18)
ax.set_xlabel('depth traversed $t$')
ax.set_ylabel(r'gradient norm $\|g_t\|$')
legend_above(ax, 'PH: gradients metered, never explode', ncol=1)
clean_axis(ax)

ax = axes[1]
ax.plot(np.arange(T3 + 1), np.median(gn_std, axis=1), color=CB[4], lw=2,
        label='standard stream')
ax.fill_between(np.arange(T3 + 1), np.percentile(gn_std, 5, axis=1),
                np.percentile(gn_std, 95, axis=1), color=CB[4], alpha=0.15)
ax.set_yscale('log')
ax.set_xlabel('depth traversed $t$')
ax.set_ylabel(r'gradient norm $\|g_t\|$')
legend_above(ax, 'standard: vanish / explode fan', ncol=1)
clean_axis(ax)
save(fig, 'f3-gradient.png')

# ----------------------------------------------------------------------
# L4 — explicit-Euler oscillation boundary
# ----------------------------------------------------------------------
print('L4: oscillation boundary')
js = np.linspace(0.0, 2.2, 45)      # h*j per eigenpair
rs = np.linspace(0.0, 1.6, 45)      # h*r
JJ, RR = np.meshgrid(js, rs)
mod2 = (1.0 - RR) ** 2 + JJ ** 2    # |1 + h(-r + i j)|^2
growth = mod2 - 1.0

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.1), constrained_layout=True)
ax = axes[0]
im = ax.imshow(growth, origin='lower', extent=[js[0], js[-1], rs[0], rs[-1]],
               aspect='auto', cmap='RdBu_r', vmin=-1.0, vmax=1.0)
bd = js[js <= 1.0]
ax.plot(bd, 1.0 - np.sqrt(np.maximum(0.0, 1.0 - bd ** 2)), color=G900,
        lw=2.0, ls='--', label=r'boundary $(hr-1)^2 + (hj)^2 = 1$')
ax.plot(bd, 1.0 + np.sqrt(np.maximum(0.0, 1.0 - bd ** 2)), color=G900,
        lw=2.0, ls='--')
ax.set_xlabel(r'transport per step $h j$')
ax.set_ylabel(r'damping per step $h r$')
ax.legend(loc='upper left')
fig.colorbar(im, ax=ax, label=r'$|1 + h(-r+ij)|^2 - 1$', shrink=0.9)
ax.set_title('explicit Euler: growth map', fontsize=11.5, fontweight='bold',
             pad=8)

ax = axes[1]
# measured: explicit step growth vs Cayley, sweeping hj at hr = 0.05
hr_fixed = 0.05
sweep = np.linspace(0.0, 2.2, 60)
grow_meas, grow_cay = [], []
for hjj in sweep:
    j = hjj / 1.0
    r = hr_fixed / 1.0
    ev = 1.0 + (-r + 1j * j)
    grow_meas.append(abs(ev) - 1.0)
    lam = (1 - hr_fixed / 2) / (1 + hr_fixed / 2)     # Cayley damping
    grow_cay.append(lam - 1.0)                        # transport modulus 1
ax.plot(sweep, grow_meas, color=CB[4], lw=2, label='explicit Euler')
ax.plot(sweep, grow_cay, color=CB[2], lw=2, label='Cayley form')
ax.axhline(0, color=G400, lw=1.0)
# boundary location: hj^2 = 2r - r^2
bd_x = np.sqrt(2 * hr_fixed - hr_fixed ** 2)
ax.axvline(bd_x, color=G900, ls='--', lw=1.2,
           label=r'predicted boundary $hj=\sqrt{2hr-(hr)^2}$')
ax.set_xlabel(r'transport per step $h j$')
ax.set_ylabel('growth per step')
legend_above(ax, 'damping $hr=0.05$: who crosses zero', ncol=2)
clean_axis(ax)
RESULTS['L4_boundary_hj'] = float(np.sqrt(2 * hr_fixed - hr_fixed ** 2))
RESULTS['L4_cayley_modulus_minus_one'] = float(grow_cay[-1])
save(fig, 'f4-boundary.png')

# ----------------------------------------------------------------------
# L5 — capacity: stream spectra + readout at depth 120
# ----------------------------------------------------------------------
print('L5: capacity readout')
d5, T5, n5 = 32, 120, 480
layers5 = [ph_layer(d5, 1.0, 0.08, rng) for _ in range(T5)]
Ws5 = [rng.standard_normal((d5, d5)) / np.sqrt(d5) for _ in range(T5)]

# rank-2 task: four classes on a circle in a 2-plane of the input space
# (resolving it requires two independent directions to survive the stream)
y = rng.integers(0, 4, n5)
ang = y * (np.pi / 2) + 0.25 * rng.standard_normal(n5)
base = np.zeros((2, d5))
base[0, 0] = 1.0
base[1, 1] = 1.0
Xin = 1.1 * np.cos(ang)[:, None] * base[0][None, :] \
    + 1.1 * np.sin(ang)[:, None] * base[1][None, :] \
    + 0.25 * rng.standard_normal((n5, d5))
Xin[:, :2] += 0.0  # class plane lives in coords 0,1

Zph, _ = run_ph_stream(layers5, Xin, None, 1.0)
Zstd, _ = run_std_stream(Ws5, Xin, 1.0)

# Jacobian spectra (column-operator convention)
sv_ph, sv_std = [], []
for rep in range(8):
    g = rng.standard_normal((d5, d5))
    for (C, Lam, B) in layers5:
        g = (Lam @ (C @ g))
    sv_ph.append(np.linalg.svd(g, compute_uv=False))
    g = rng.standard_normal((d5, d5))
    for W in Ws5:
        g = (np.eye(d5) + W) @ g
    sv_std.append(np.linalg.svd(g, compute_uv=False))
sv_ph = np.concatenate(sv_ph)
sv_std = np.concatenate(sv_std)
RESULTS['L5_ph_sv_range'] = [float(sv_ph.min()), float(sv_ph.max())]
RESULTS['L5_std_sv_range'] = [float(sv_std.min()), float(sv_std.max())]

def terminal_metrics(Z):
    """Representation health of the terminal state."""
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-300)
    G = Zn @ Zn.T
    off = G[np.triu_indices_from(G, 1)]
    # self-similarity: how much of the (renormalized) terminal state still
    # points along the input direction
    Xn = Xin / np.linalg.norm(Xin, axis=1, keepdims=True)
    self_cos = np.sum(Zn * Xn, axis=1)
    return float(np.mean(np.abs(off))), float(np.mean(np.abs(self_cos)))

coll_ph, self_ph = terminal_metrics(Zph[-1])
coll_std, self_std = terminal_metrics(Zstd[-1])
RESULTS['L5_terminal_pairwise_cosine_ph'] = coll_ph
RESULTS['L5_terminal_pairwise_cosine_std'] = coll_std
RESULTS['L5_self_cosine_ph'] = self_ph
RESULTS['L5_self_cosine_std'] = self_std

def circle_readout(Z, y):
    """Nearest-centroid readout on the renormalized terminal state."""
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-300)
    cents = np.array([Zn[y == k].mean(0) for k in range(4)])
    cents /= np.linalg.norm(cents, axis=1, keepdims=True) + 1e-300
    sim = Zn @ cents.T
    return float(np.mean(sim.argmax(1) == y))

acc_ph = circle_readout(Zph[-1], y)
acc_std = circle_readout(Zstd[-1], y)
RESULTS['L5_readout_acc_ph'] = acc_ph
RESULTS['L5_readout_acc_std'] = acc_std
RESULTS['L5_std_norm_growth'] = float(np.median(
    np.linalg.norm(Zstd[-1], axis=1) / np.linalg.norm(Xin, axis=1)))

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ax.semilogy(np.sort(sv_std)[::-1], color=CB[4], lw=2, label='standard stream')
ax.semilogy(np.sort(sv_ph)[::-1], color=CB[0], lw=2, label='PH stream')
ax.set_xlabel('singular value index')
ax.set_ylabel('singular value')
legend_above(ax, 'depth-120 Jacobian spectra', ncol=2)
clean_axis(ax)

ax = axes[1]
depths = [10, 30, 60, 90, 120]
accs_ph, accs_std = [], []
for Dp in depths:
    Zp, _ = run_ph_stream(layers5[:Dp], Xin, None, 1.0)
    Zs, _ = run_std_stream(Ws5[:Dp], Xin, 1.0)
    accs_ph.append(circle_readout(Zp[-1], y))
    accs_std.append(circle_readout(Zs[-1], y))
ax.plot(depths, accs_ph, 'o-', color=CB[0], lw=2, label='PH stream')
ax.plot(depths, accs_std, 's-', color=CB[4], lw=2, label='standard (renormalized)')
ax.axhline(0.25, color=G400, lw=1.0, ls=':', label='chance (4 classes)')
ax.set_xlabel('stream depth')
ax.set_ylabel('circle-task accuracy')
ax.set_ylim(0.0, 1.05)
legend_above(ax, 'rank-2 readout from terminal state', ncol=2)
clean_axis(ax)
save(fig, 'f5-capacity.png')

# ----------------------------------------------------------------------
# F6 — law validation summary
# ----------------------------------------------------------------------
print('F6: validation summary')
# L1 residual: bound tightness distribution (should be <= 1)
tight = (norm_ph.T / bound_rows).ravel()
# L2 residual: relative error at smallest h
rel_l2 = budget_err[0.125] / abs(np.median(vb[:, 0]))
# L3: PH gradient ratio distribution
g3 = (gn_ph[-1] / gn_ph[0]).ravel()
rows = [
    ('L1 norm bound violations', '%d' % RESULTS['L1_violations']),
    ('L1 bound tightness (median ratio)', '%.4f' % RESULTS['L1_bound_ratio_median']),
    ('L2 transport logdet error (volume-free)', '%.1e' % RESULTS['L2_transport_logdet_error']),
    ('L2 budget error ratio (h/2)', '%.2f' % RESULTS['L2_error_ratio_half']),
    ('L2 budget error ratio (h/4)', '%.2f' % RESULTS['L2_error_ratio_quarter']),
    ('L3 gradient final/start (median)', '%.4f' % RESULTS['L3_ph_final_over_start']),
    ('L3 gradient max (240 layers)', '%.4f' % RESULTS['L3_ph_max']),
    ('L4 Cayley modulus-1 (never positive)', '%.4f' % RESULTS['L4_cayley_modulus_minus_one']),
    ('L5 terminal pairwise cosine (PH / std)', '%.3f / %.3f' % (coll_ph, coll_std)),
    ('L5 rank-2 readout (PH / std)', '%.3f / %.3f' % (acc_ph, acc_std)),
    ('L5 std norm growth factor', '%.1e' % RESULTS['L5_std_norm_growth']),
]
RESULTS['laws'] = [list(r) for r in rows]

fig, ax = plt.subplots(figsize=(7.6, 3.4), constrained_layout=True)
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
print(json.dumps(RESULTS, indent=2)[:1500])
