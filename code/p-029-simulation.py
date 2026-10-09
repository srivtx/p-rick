#!/usr/bin/env python3
"""P-029 simulation: the lock-in law (phase transition in agent collectives).

Model: N agents hold a scalar belief b_i in [-1, 1] (position on a binary
issue). Each round:

  1. emission: agent i publicly emits +1 with probability
         p_i = (1 + tanh(b_i / T)) / 2
     (T is the sampling temperature: the same knob as an LLM's softmax
     temperature). Optional top-p truncation: if p_i >= p_top the agent
     emits its majority option deterministically.
  2. board: everyone reads the emission mean m_hat = (1/N) sum e_i.
  3. update: b_i <- clip(lambda b_i + K m_hat, -1, 1)
     (lambda is belief memory; K is the coupling - the share of each
     agent's next-belief determined by what the others just said).

Coherence: m(t) = |mean_i b_i(t)|.

Laws under test:
  L1 (lock-in law): the mean-field map b' = lambda b + K tanh(b/T)
     bifurcates at  K_c = T (1 - lambda):  below it the collective stays
     mixed (Ornstein-Uhlenbeck fluctuations of order 1/sqrt(N)); above
     it locks to a collective position. No middle ground: the transition
     is sharp in the K/T ratio.
  L2 (order-parameter law): above threshold the locked coherence is
         m* : m (1 - lambda) = K tanh(m/T)
     -> pitchfork scaling m*^2 = 3 T^2 (K - K_c)/K near the boundary.
  L3 (locking-time law): from initial diversity ~ 1/sqrt(N),
         tau_lock ~ T ln(N m_target) / (K - K_c)  -> tau proportional
     to 1/(K - K_c) and to ln N.
  L4 (firewall law): a fraction f of agents with lambda_i = 0 (fresh
     contexts every round) raises the threshold linearly:
         K_c(f) = T (1 - (1-f) lambda)  -- the diversity firewall.
  L5 (refresher law): resetting beliefs toward zero at interval Delta
     prevents lock-out only if Delta beats the growth time:
         Delta < Delta* ~ tau_lock  -> the maintainable-exploration
     schedule; and Delta* scales as 1/(K - K_c).

Figures:
  f1-dynamics.png        m(t) below / near / above the threshold
  f2-bifurcation.png     m_inf vs K: measured vs the pitchfork law
  f3-locking-time.png    tau vs (K-K_c) and vs ln N
  f4-firewall.png        K_c(f) measured vs linear law + truncation speedup
  f5-refresher.png       locked map in (Delta, K) + boundary law
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
                   '..', 'figures', 'p-029')
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
T_TEMP = 0.5            # emission temperature
LAM = 0.7               # belief memory
KC = T_TEMP * (1 - LAM) # = 0.15


# move m_star above collect (needed inside)
def m_star(K, T=T_TEMP, lam=LAM):
    """Locked coherence: solve m (1-lam) = K tanh(m/T)."""
    if K <= T * (1 - lam):
        return 0.0
    m = 0.5
    for _ in range(200):
        f = m * (1 - lam) - K * np.tanh(m / T)
        fp = (1 - lam) - K / T * (1 - np.tanh(m / T) ** 2)
        m = m - f / fp
        m = min(max(m, 1e-6), 1.0)
    return m


def collect(N=200, K=0.20, T=T_TEMP, lam=LAM, t_run=2000, n_rep=1,
            f_fresh=0.0, p_top=None, reset_every=None, reset_beta=0.85,
            b0_scale=0.08, rng=None, return_traj=False):
    """Run the collective. Returns (m_inf, tau_lock, m_trajectory).

    Locking is measured RELATIVE to the mean-field fixed point m*(K):
    tau fires when m crosses 0.7 m* and holds above 0.5 m*.
    Reset (if any) resamples beliefs to fresh diversity scale b0_scale.
    """
    rng = rng or np.random.default_rng(0)
    fresh = rng.random(N) < f_fresh
    lam_vec = np.where(fresh, 0.0, lam)
    mstar = m_star(K, T, lam)
    thr_hi = 0.7 * mstar if mstar > 1e-6 else 0.7
    thr_lo = 0.5 * mstar if mstar > 1e-6 else 0.5
    tau = None
    m_traj = np.zeros(t_run + 1)
    b = b0_scale * rng.standard_normal(N)
    m_traj[0] = abs(b.mean())
    for t in range(1, t_run + 1):
        p = 0.5 * (1.0 + np.tanh(b / T))
        if p_top is not None:
            det_pos = p >= p_top
            det_neg = p <= 1.0 - p_top
            e = np.where(det_pos, 1.0, np.where(det_neg, -1.0, 0.0))
            free = ~(det_pos | det_neg)
            e[free] = np.where(rng.random(free.sum()) < p[free], 1.0, -1.0)
        else:
            e = np.where(rng.random(N) < p, 1.0, -1.0)
        m_hat = e.mean()
        b = np.clip(lam_vec * b + K * m_hat, -1.0, 1.0)
        if reset_every is not None and t % reset_every == 0:
            b = b0_scale * rng.standard_normal(N)
        m_traj[t] = abs(b.mean())
        if tau is None and t > 50 and m_traj[t] > thr_hi:
            window = m_traj[max(0, t - 100):t + 1]
            if window.min() > thr_lo:
                tau = t
    m_inf = m_traj[-400:].mean()
    if return_traj:
        return m_inf, tau, m_traj
    return m_inf, tau


# ----------------------------------------------------------------------
# L1 — dynamics below / near / above
# ----------------------------------------------------------------------
print('L1: dynamics')
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
t_show = 900
for ratio, col in [(0.70, CB[2]), (0.95, CB[1]), (1.05, CB[3]), (1.40, CB[4])]:
    K = ratio * KC
    _, _, traj = collect(K=K, t_run=t_show, return_traj=True, rng=rng)
    ax.plot(np.arange(t_show + 1), traj, color=col, lw=1.6,
            label=r'$K/K_c = %.2f$' % ratio)
ax.set_xlabel('round $t$')
ax.set_ylabel(r'coherence $m(t)$')
ax.set_ylim(0, 1.02)
legend_above(ax, 'one collective, four couplings', ncol=2)
clean_axis(ax)

ax = axes[1]
# many replicas at K/Kc = 0.9 vs 1.1: the sharpness
for ratio, col, lab in [(0.90, CB[2], r'$K/K_c=0.9$: stays mixed'),
                        (1.10, CB[4], r'$K/K_c=1.1$: locks')]:
    finals = []
    for rep in range(30):
        m_inf, _ = collect(K=ratio * KC, t_run=600, rng=rng)
        finals.append(m_inf)
    ax.scatter([ratio] * 30, finals, s=14, color=col, alpha=0.55,
               label=lab + ' (%d replicas)' % 30)
ax.set_xlabel(r'$K/K_c$')
ax.set_ylabel(r'final coherence $m_\infty$')
ax.set_xlim(0.8, 1.2)
ax.set_ylim(-0.03, 1.03)
legend_above(ax, 'the transition is sharp, not gradual', ncol=2)
clean_axis(ax)
save(fig, 'f1-dynamics.png')

# ----------------------------------------------------------------------
# L2 — bifurcation curve
# ----------------------------------------------------------------------
print('L2: bifurcation')
ratios = np.linspace(0.6, 2.0, 29)
m_meas = []
for ratio in ratios:
    mm = []
    for rep in range(14):
        m_inf, _ = collect(K=ratio * KC, t_run=1200, rng=rng)
        mm.append(m_inf)
    m_meas.append(np.mean(mm))
m_meas = np.array(m_meas)
m_law = np.array([m_star(r * KC) for r in ratios])
RESULTS['L2_measured_at_1.4'] = float(m_meas[np.argmin(np.abs(ratios - 1.4))])
RESULTS['L2_law_at_1.4'] = float(m_star(1.4 * KC))
RESULTS['L2_rel_err_above_threshold'] = float(np.median(np.abs(
    (m_meas - m_law)[ratios > 1.15] / (m_law[ratios > 1.15] + 1e-9))))
RESULTS['L2_mixed_below'] = float(m_meas[ratios < 0.95].max())

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ax.plot(ratios, m_law, color=G400, ls='--', lw=1.8,
        label=r'law: $m^*: m(1-\lambda) = K\tanh(m/T)$')
ax.plot(ratios, m_meas, 'o', color=CB[0], ms=5.5, label='measured (N=200)')
ax.axvline(1.0, color=G700, ls=':', lw=1.2, label=r'$K_c = T(1-\lambda)$')
ax.set_xlabel(r'$K/K_c$')
ax.set_ylabel(r'coherence $m_\infty$')
ax.set_ylim(0, 1.03)
legend_above(ax, 'the bifurcation curve', ncol=2)
clean_axis(ax)

ax = axes[1]
near = ratios[(ratios > 1.0) & (ratios < 1.5)]
ax.plot(near, (3 * T_TEMP ** 2 * (near * KC - KC) / (near * KC)),
        color=G400, ls='--', lw=1.8, label=r'pitchfork: $3T^2(K-K_c)/K$')
sel = (ratios > 1.0) & (ratios < 1.5)
ax.plot(ratios[sel], m_meas[sel] ** 2, 'o', color=CB[3], ms=5.5,
        label='measured $m^2$')
ax.set_xlabel(r'$K/K_c$')
ax.set_ylabel(r'$m_\infty^2$')
legend_above(ax, 'near-threshold pitchfork scaling', ncol=2)
clean_axis(ax)
save(fig, 'f2-bifurcation.png')

# ----------------------------------------------------------------------
# L3 — locking time
# ----------------------------------------------------------------------
print('L3: locking time')
ds = np.linspace(1.10, 2.0, 14)
taus = []
for ratio in ds:
    tt = []
    for rep in range(12):
        _, tau = collect(K=ratio * KC, t_run=4000, rng=rng)
        tt.append(tau if tau is not None else 4000)
    taus.append(np.median(tt))
taus = np.array(taus)
Ks = ds * KC
g = (Ks - KC) / T_TEMP                    # growth rate
B0 = 0.08 / np.sqrt(200)
tau_law = np.array([np.log(0.7 * m_star(K) / B0) for K in Ks]) / g
RESULTS['L3_tau_fit_slope'] = float(np.polyfit(1.0 / g, taus, 1)[0])
RESULTS['L3_tau_law_slope'] = float(np.median(tau_law * g))
RESULTS['L3_tau_rel_err'] = float(np.median(np.abs(taus - tau_law) /
                                            (tau_law + 1e-9)))

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ax.plot(1.0 / g, taus, 'o', color=CB[0], ms=6, label='measured (median of 12)')
ax.plot(1.0 / g, tau_law, color=G400, ls='--', lw=1.8,
        label=r'law: $\ln(0.7m^*/b_0)\cdot T/(K-K_c)$')
ax.set_xlabel(r'$T/(K-K_c)$')
ax.set_ylabel(r'locking time $\tau_{lock}$')
legend_above(ax, r'locking time $\propto 1/(K-K_c)$', ncol=2)
clean_axis(ax)

ax = axes[1]
Ns = [50, 100, 200, 400, 800, 1600]
tN = []
for Nv in Ns:
    tt = []
    for rep in range(10):
        _, tau = collect(N=Nv, K=1.5 * KC, t_run=4000, rng=rng)
        tt.append(tau if tau is not None else 4000)
    tN.append(np.median(tt))
ax.semilogx(Ns, tN, 'o-', color=CB[2], lw=1.8, ms=6, label='measured')
ax.semilogx(Ns, np.log(0.7 * m_star(1.5 * KC) / (0.08 / np.sqrt(Ns))) /
            ((1.5 * KC - KC) / T_TEMP),
            color=G400, ls='--', lw=1.8, label=r'law: $\propto \ln N$')
ax.set_xlabel(r'collective size $N$')
ax.set_ylabel(r'locking time $\tau_{lock}$')
legend_above(ax, r'growth from initial diversity $1/\sqrt{N}$', ncol=2)
clean_axis(ax)
RESULTS['L3_tau_vs_lnN_fit'] = [float(x) for x in np.polyfit(
    np.log(Ns), tN, 1)]
save(fig, 'f3-locking-time.png')

# ----------------------------------------------------------------------
# L4 — the diversity firewall + truncation speedup
# ----------------------------------------------------------------------
print('L4: firewall')
fs = np.linspace(0.0, 0.8, 9)
kc_meas = []
for f in fs:
    # measure K_c as the K where m_inf crosses 0.3 (scan K)
    K_scan = np.linspace(0.05, 0.55, 11)
    mm = []
    for K in K_scan:
        vals = []
        for rep in range(8):
            m_inf, _ = collect(K=K, t_run=900, f_fresh=f, rng=rng)
            vals.append(m_inf)
        mm.append(np.mean(vals))
    mm = np.array(mm)
    idx = np.where(mm > 0.3)[0]
    kc_meas.append(K_scan[idx[0]] if len(idx) else K_scan[-1])
kc_meas = np.array(kc_meas)
kc_law = T_TEMP * (1 - (1 - fs) * LAM)
RESULTS['L4_firewall_median_err'] = float(np.median(np.abs(kc_meas - kc_law)))

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), constrained_layout=True)
ax = axes[0]
ax.plot(fs, kc_law, color=G400, ls='--', lw=1.8,
        label=r'law: $K_c(f) = T(1-(1-f)\lambda)$')
ax.plot(fs, kc_meas, 'o', color=CB[0], ms=6, label='measured')
ax.set_xlabel(r'fresh-context fraction $f$')
ax.set_ylabel(r'measured threshold $K_c$')
legend_above(ax, 'the diversity firewall', ncol=2)
clean_axis(ax)

ax = axes[1]
ps = [1.0, 0.95, 0.9, 0.8, 0.7, 0.6]
tts = []
for p in ps:
    tt = []
    for rep in range(12):
        _, tau = collect(K=1.3 * KC, t_run=3000, p_top=p, rng=rng)
        tt.append(tau if tau is not None else 3000)
    tts.append(np.median(tt))
ax.plot(ps, tts, 'o-', color=CB[3], lw=1.8, ms=6, label='measured')
b_sat = T_TEMP * np.arctanh(2 * np.array(ps) - 1)
ax2 = ax.twinx()
ax2.plot(ps, b_sat, color=CB[1], ls=':', lw=1.6,
         label=r'$b_{sat}=T\,\mathrm{atanh}(2p-1)$')
ax2.set_ylabel(r'saturation belief $b_{sat}$', color=CB[1])
ax2.tick_params(axis='y', colors=CB[1])
ax.set_xlabel(r'top-$p$ truncation')
ax.set_ylabel(r'locking time (median of 12)')
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc='lower left', bbox_to_anchor=(0.0, 1.02),
          ncol=2, title='truncation speeds up consensus', title_fontsize=10.5,
          frameon=False, borderaxespad=0.0)
clean_axis(ax)
RESULTS['L4_truncation_speedup'] = float(tts[0] / tts[-1]) if tts[-1] > 0 else 0.0
save(fig, 'f4-firewall.png')

# ----------------------------------------------------------------------
# L5 — the refresher schedule
# ----------------------------------------------------------------------
print('L5: refresher')
Ds = np.array([10, 20, 40, 70, 120, 200, 400])
Ks_r = np.array([1.10, 1.25, 1.5, 2.0]) * KC
locked = np.zeros((len(Ds), len(Ks_r)))
for iD, D in enumerate(Ds):
    for iK, K in enumerate(Ks_r):
        vals = []
        for rep in range(8):
            m_inf, _ = collect(K=K, t_run=2400, reset_every=int(D),
                                  rng=rng)
            vals.append(m_inf)
        locked[iD, iK] = np.mean(vals) > 0.5 * m_star(K)

fig, ax = plt.subplots(figsize=(7.4, 4.2), constrained_layout=True)
im = ax.imshow(locked, origin='lower', aspect='auto', cmap='RdYlGn',
               vmin=0, vmax=1,
               extent=[Ks_r[0], Ks_r[-1], np.log10(Ds[0]), np.log10(Ds[-1])])
ax.set_yticks([1, 1.5, 2, 2.3])
ax.set_yticklabels(['10', '32', '100', '200'])
# boundary law: Delta* = tau_lock(K) (from L3 law)
Kc_grid = np.linspace(Ks_r[0], Ks_r[-1], 60)
tau_b = np.array([np.log(0.7 * m_star(K) / B0) for K in Kc_grid]) / (
    (Kc_grid - KC) / T_TEMP)
ax.plot(Kc_grid, np.log10(np.maximum(10, np.minimum(400, tau_b))),
        color=G900, lw=2.2, ls='--',
        label=r'law: $\Delta^* \approx \tau_{lock}(K)$')
ax.set_xlabel(r'coupling $K$')
ax.set_ylabel(r'reset interval $\Delta$ (log)')
ax.legend(loc='upper left')
ax.set_title('locked (red) vs exploratory (green) under resets',
             fontsize=12, fontweight='bold', pad=10)
save(fig, 'f5-refresher.png')

# boundary residual: for each K column, measured Delta* (first locked D)
# vs tau_law
errs = []
for iK, K in enumerate(Ks_r):
    col = locked[:, iK]
    idx = np.where(col)[0]
    if len(idx) > 0:
        d_meas = Ds[idx[0]]
        tau_b_k = np.log(0.7 * m_star(K) / B0) / ((K - KC) / T_TEMP)
        errs.append(abs(np.log10(d_meas) - np.log10(max(10, min(400, tau_b_k)))))
RESULTS['L5_boundary_median_log_err'] = float(np.median(errs)) if errs else -1

# ----------------------------------------------------------------------
# F6 — law validation summary
# ----------------------------------------------------------------------
print('F6: validation summary')
rows = [
    ('L2 m* at K/Kc=1.4 (measured/law)', '%.3f / %.3f' % (
        RESULTS['L2_measured_at_1.4'], RESULTS['L2_law_at_1.4'])),
    ('L2 m* rel. error above threshold (median)', '%.2f%%' % (
        100 * RESULTS['L2_rel_err_above_threshold'])),
    ('L2 max coherence below K_c', '%.3f' % RESULTS['L2_mixed_below']),
    ('L3 tau prefactor (fit / deterministic law)', '%.2f / %.2f' % (
        RESULTS['L3_tau_fit_slope'], RESULTS['L3_tau_law_slope'])),
    ('L3 tau-vs-lnN slope (measured)', '%.2f' % (
        RESULTS['L3_tau_vs_lnN_fit'][0])),
    ('L4 firewall median |err| in K_c', '%.4f' % RESULTS['L4_firewall_median_err']),
    ('L4 top-p truncation effect (binary: ~1 = none)', '%.2fx' % RESULTS['L4_truncation_speedup']),
    ('L5 refresher boundary log10 err (median)', '%.3f' % (
        RESULTS['L5_boundary_median_log_err'])),
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
print(json.dumps(RESULTS, indent=2)[:1200])
