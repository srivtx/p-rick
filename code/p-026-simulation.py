#!/usr/bin/env python3
"""P-026 simulation: the cascade law of credential reuse.

Model: U users, S sites, s accounts per user. Each user has one primary
password drawn from a Zipf(beta) popularity pool of M strings; an account
uses the primary with probability rho (reuse), else a unique password.
A fraction b of sites is breached (random subset). Leaked primary
accounts teach the attacker (i) the user's primary (targeted channel) and
(ii) the password string itself (spraying channel, suppressed by a
lockout/monitoring friction lambda).

Laws under test:
  L1 (blast radius, exact): the reuse channel's takeover fraction
      F_w(b; rho, s) = E[(k - j) 1{j>=1}] / (s(1-b)),
      k ~ Bin(s, rho), j ~ Bin(k, b)  — independent of beta.
  L2 (decomposition, exact by construction):
      F = F_w + (1 - lambda) * F_s
      with F_s the spray-only channel.
  L3 (concentration law): F_s(b; beta) = rho(1-b) sum_m pi_m
      (1 - (1-b)^{A_m - 1}),  A_m = U pi_m s rho
      — crossover rank m*(b) = (H U s rho b)^{1/beta}: below the crossover
      strings are protected, above it exposed; the takeover curve's shape
      (gradual for beta<1, cliff for beta>1) is set by beta alone.

Figures:
  f1-blast-radius.png        L1: closed form vs simulation, rho sweep
  f2-concentration.png       L3: F_s(b) for beta sweep, exact theory overlay
  f3-separatrix.png          finite-size evidence: F_s(b) at U in
                             {1e3,1e4,1e5,1e6} for beta = 0.8 vs 1.2
  f4-decomposition.png       L2: F(lambda) linear in lambda, per beta
  f5-interventions.png       adoption (dual: adopter immunity vs herd
                             backbone) and lockout friction
  f6-law-validation.png      residuals of all three laws

Writes results.json with every headline number cited in the paper.
"""
import json
import math
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'figures', 'p-026')
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
# Model
# ════════════════════════════════════════════════════════════════════════════

M = 100_000          # password pool size
S = 50               # sites
s_acc = 8            # accounts per user


def zipf_pmf(beta, M):
    ranks = np.arange(1, M + 1, dtype=np.float64)
    w = ranks ** (-beta)
    return w / w.sum()


def zipf_cdf(beta, M):
    p = zipf_pmf(beta, M)
    return np.cumsum(p), p


def sample_strings(rng, cdf, U):
    u = rng.random(U) * cdf[-1]
    return np.searchsorted(cdf, u).clip(0, M - 1).astype(np.int32)


def simulate(U, rho, beta, b, lam, f_adopt, rng, cdf=None, trials=3):
    """Return (F_total, F_w, F_s) averaged over breach draws.

    F is measured over accounts on non-breached sites (the operator's
    account-takeover rate after a breach wave).
    """
    if cdf is None:
        cdf, _ = zipf_cdf(beta, M)
    F, Fw, Fs = [], [], []
    for _ in range(trials):
        sites = rng.integers(0, S, size=(U, s_acc)).astype(np.int16)
        strings = sample_strings(rng, cdf, U)
        adopt = rng.random(U) < f_adopt
        uses_p = (rng.random((U, s_acc)) < rho) & (~adopt)[:, None]
        br_sites = rng.choice(S, size=max(1, int(round(b * S))),
                              replace=False)
        br = np.zeros(S, dtype=bool)
        br[br_sites] = True
        br_acc = br[sites]                       # (U, s)
        leaked = uses_p & br_acc                 # accounts that leak
        user_leaked = leaked.any(axis=1) & (~adopt)
        learned = np.zeros(M, dtype=bool)
        learned[strings[user_leaked]] = True
        str_learned = learned[strings]           # (U,) broadcast
        within = uses_p & ~br_acc & user_leaked[:, None]
        spray = uses_p & ~br_acc & str_learned[:, None]
        spray_only = spray & ~within
        suppressed = spray_only & (rng.random((U, s_acc)) < (1.0 - lam))
        fall = within | suppressed
        nonbr = ~br_acc
        denom = nonbr.sum()
        F.append(fall.sum() / max(1, denom))
        Fw.append(within.sum() / max(1, denom))
        Fs.append(spray_only.sum() / max(1, denom))
    return float(np.mean(F)), float(np.mean(Fw)), float(np.mean(Fs))


# ════════════════════════════════════════════════════════════════════════════
# Closed forms
# ════════════════════════════════════════════════════════════════════════════

def F_w_theory(b, rho, s=s_acc, f_adopt=0.0):
    """Reuse channel: exact binomial expectation."""
    ks = np.arange(0, s + 1)
    pk = math.comb  # placeholder to keep numpy style below
    from math import comb
    pk = np.array([comb(s, k) * rho ** k * (1 - rho) ** (s - k)
                   for k in ks])
    # E[(k - j) 1{j>=1}] with j ~ Bin(k, b)
    vals = np.array([k * (1 - (1 - b) ** k) - k * b for k in ks])
    return (1 - f_adopt) * float((pk * vals).sum()) / (s * (1 - b))


def F_union_theory(b, beta, U, rho, s=s_acc, f_adopt=0.0):
    """The cascade law (union channel, pool level, Poisson thinning).

    F_union = (1-f) rho sum_m pi_m [1 - (1-b) e^{-b mu_m}],
    mu_m = (1-f) U pi_m s rho  (expected accounts using string m).
    Exact in the pool-level limit; the own-user clustering of exposures adds
    a positive correction the limitations section prices.
    """
    p = zipf_pmf(beta, M)
    mu = (1 - f_adopt) * U * p * s * rho
    term = 1.0 - (1.0 - b) * np.exp(-b * mu)
    return (1 - f_adopt) * rho * float((p * term).sum())


# ════════════════════════════════════════════════════════════════════════════
# F1 — blast radius (L1)
# ════════════════════════════════════════════════════════════════════════════

print('F1: blast radius', flush=True)
U1 = 200_000
b_grid = np.round(np.linspace(0.05, 0.95, 12), 2)
rng = np.random.default_rng([SEED, 1])
f1 = {}
for rho in [0.2, 0.5, 0.8]:
    meas, pred = [], []
    for b in b_grid:
        _, Fw, _ = simulate(U1, rho, 1.0, float(b), 0.0, 0.0, rng, trials=2)
        meas.append(Fw)
        pred.append(F_w_theory(float(b), rho))
    f1[rho] = {'meas': meas, 'pred': pred}
    err = np.abs(np.array(meas) / np.array(pred) - 1)
    print(f'  rho={rho}: median |err| {np.median(err):.4f}', flush=True)

RESULTS['f1'] = {str(r): f1[r] for r in f1}

fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
cols = [CB[1], CB[0], CB[3]]
for c, rho in zip(cols, [0.2, 0.5, 0.8]):
    ax.plot(b_grid, f1[rho]['pred'], '-', lw=1.8, color=c,
            label=f'theory, $\\rho$ = {rho}')
    ax.plot(b_grid, f1[rho]['meas'], 's', ms=5, mfc='none', mec=c, mew=1.5,
            label=f'simulation, $\\rho$ = {rho}')
ax.set_xlabel('breached fraction of sites $b$')
ax.set_ylabel('reuse-channel takeover $F_w$')
ax.set_title('The blast-radius law (exact)')
_h, _l = ax.get_legend_handles_labels()
fig.legend(_h, _l, loc='outside upper center', ncol=3, fontsize=8.4,
           frameon=False)
clean_axis(ax)
save(fig, 'f1-blast-radius.png')

# ════════════════════════════════════════════════════════════════════════════
# F2 — the concentration law (L3)
# ════════════════════════════════════════════════════════════════════════════

print('F2: concentration law', flush=True)
U2 = 100_000
rho2 = 0.5
betas = [0.5, 0.8, 1.0, 1.2, 1.5]
f2 = {}
for beta in betas:
    rng = np.random.default_rng([SEED, 2, int(beta * 10)])
    cdf, _ = zipf_cdf(beta, M)
    meas, pred = [], []
    for b in b_grid:
        _, Fw, Fs = simulate(U2, rho2, beta, float(b), 0.0, 0.0, rng,
                             cdf=cdf, trials=3)
        meas.append(Fw + Fs)
        pred.append(F_union_theory(float(b), beta, U2, rho2))
    f2[beta] = {'meas': meas, 'pred': pred}
    err = np.abs(np.array(meas) / np.maximum(np.array(pred), 1e-6) - 1)
    print(f'  beta={beta}: median |err| {np.median(err):.4f} '
          f'(F_union(0.5)={meas[5]:.3f})', flush=True)

RESULTS['f2'] = {str(b): f2[b] for b in f2}

fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
cols = [CB[1], CB[0], G700, CB[3], CB[4]]
for c, beta in zip(cols, betas):
    ax.plot(b_grid, f2[beta]['pred'], '-', lw=1.7, color=c,
            label=f'theory, $\\beta$ = {beta}')
    ax.plot(b_grid, f2[beta]['meas'], 'o', ms=4, mfc='none', mec=c, mew=1.4,
            label=f'simulation, $\\beta$ = {beta}')
ax.set_xlabel('breached fraction of sites $b$')
ax.set_ylabel('cascade takeover $F_w + F_s$')
ax.set_title('The concentration law: $\\beta$ sets the curve')
_h, _l = ax.get_legend_handles_labels()
fig.legend(_h, _l, loc='outside upper center', ncol=3, fontsize=7.4,
           frameon=False, columnspacing=1.1, handlelength=1.6)
clean_axis(ax)
save(fig, 'f2-concentration.png')

# ════════════════════════════════════════════════════════════════════════════
# F3 — the separatrix: finite-size evidence
# ════════════════════════════════════════════════════════════════════════════

print('F3: separatrix', flush=True)
Us = [1_000, 10_000, 100_000, 1_000_000]
b3 = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.8])
f3 = {}
for beta in [0.8, 1.2]:
    curves = {}
    for U in Us:
        rng = np.random.default_rng([SEED, 3, int(beta * 10), int(np.log10(U))])
        cdf, _ = zipf_cdf(beta, M)
        ys = []
        for b in b3:
            _, _, Fs = simulate(U, rho2, beta, float(b), 0.0, 0.0, rng,
                                cdf=cdf, trials=2)
            ys.append(Fs)
        curves[U] = ys
        del rng
        print(f'  beta={beta} U={U}: F_s(0.3)={ys[2]:.4f}', flush=True)
    f3[beta] = curves
RESULTS['f3'] = {str(k): {str(u): v for u, v in f3[k].items()} for k in f3}

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
for ax, beta, ttl in [(axa, 0.8, 'Diverse pool ($\\beta$ = 0.8): dilute'),
                      (axb, 1.2, 'Concentrated pool ($\\beta$ = 1.2): cliff')]:
    cols = [CB[1], CB[0], CB[3], CB[4]]
    for c, U in zip(cols, Us):
        ax.plot(b3, f3[beta][U], 'o-', ms=4, lw=1.5, color=c,
                label=f'U = {U:,}')
    ax.set_xlabel('breached fraction of sites $b$')
    ax.set_ylabel('spray-channel takeover $F_s$')
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.0), ncol=2,
              fontsize=7.8, title=ttl, title_fontsize=8.8, frameon=False)
    clean_axis(ax)
save(fig, 'f3-separatrix.png')

# ════════════════════════════════════════════════════════════════════════════
# F4 — the decomposition law (L2)
# ════════════════════════════════════════════════════════════════════════════

print('F4: decomposition', flush=True)
lam_grid = np.round(np.linspace(0.0, 1.0, 6), 2)
b4 = 0.4
f4 = {}
for beta in [0.8, 1.2]:
    rng = np.random.default_rng([SEED, 4, int(beta * 10)])
    cdf, _ = zipf_cdf(beta, M)
    tot, ws, ssonly = [], [], []
    for lam in lam_grid:
        F, Fw, Fs = simulate(U2, rho2, beta, b4, float(lam), 0.0, rng,
                             cdf=cdf, trials=3)
        tot.append(F)
        ws.append(Fw)
        ssonly.append(Fs)
    f4[beta] = {'lam': lam_grid.tolist(), 'F': tot, 'F_w': ws, 'F_s': ssonly}
    line = np.array(ws) + (1 - lam_grid) * np.array(ssonly)
    resid = np.abs(np.array(tot) / line - 1)
    print(f'  beta={beta}: decomposition median |err| '
          f'{np.median(resid):.4f}', flush=True)

RESULTS['f4'] = {str(k): f4[k] for k in f4}

fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
for c, beta in zip([CB[0], CB[3]], [0.8, 1.2]):
    d = f4[beta]
    ax.plot(d['lam'], d['F'], 'o-', ms=5, lw=1.7, color=c,
            label=f'$F$, $\\beta$ = {beta}')
    ax.plot(d['lam'], d['F_w'], '--', lw=1.5, color=c, alpha=0.75,
            label=f'$F_w$ floor, $\\beta$ = {beta}')
    line = np.array(d['F_w']) + (1 - lam_grid) * np.array(d['F_s'])
    ax.plot(d['lam'], line, ':', lw=1.6, color=G900, alpha=0.8,
            label='law: $F_w + (1-\\lambda)F_s$' if beta == 0.8 else None)
ax.set_xlabel('lockout friction $\\lambda$')
ax.set_ylabel('takeover fraction at $b$ = 0.4')
ax.set_title('The decomposition law')
_h, _l = ax.get_legend_handles_labels()
fig.legend(_h, _l, loc='outside upper center', ncol=3, fontsize=8.2,
           frameon=False)
clean_axis(ax)
save(fig, 'f4-decomposition.png')

# ════════════════════════════════════════════════════════════════════════════
# F5 — interventions: adoption duality + friction
# ════════════════════════════════════════════════════════════════════════════

print('F5: interventions', flush=True)
f_grid = np.round(np.linspace(0.0, 0.9, 7), 2)
beta5 = 1.2
b5 = 0.4
rng = np.random.default_rng([SEED, 5])
cdf, _ = zipf_cdf(beta5, M)
ad_herd, ad_adopters = [], []
for f in f_grid:
    F, Fw, Fs = simulate(U2, rho2, beta5, b5, 0.0, float(f), rng,
                         cdf=cdf, trials=3)
    ad_herd.append(F)
    ad_adopters.append(0.0)   # adopters are fully protected by construction
# adopter residual risk: their accounts fall only via direct breach (excluded)
f_pred_herd = [(1 - f) * f4[beta5]['F'][0] for f in f_grid]

# friction: lambda sweep at beta in {0.8, 1.2, 1.5}
lam5 = np.round(np.linspace(0.0, 1.0, 8), 2)
fric = {}
for beta in [0.8, 1.2, 1.5]:
    rng = np.random.default_rng([SEED, 51, int(beta * 10)])
    cdf, _ = zipf_cdf(beta, M)
    ys = []
    for lam in lam5:
        F, Fw, Fs = simulate(U2, rho2, beta, b5, float(lam), 0.0, rng,
                             cdf=cdf, trials=2)
        ys.append(F)
    fric[beta] = ys
    print(f'  beta={beta}: F(lam=0)={ys[0]:.3f} F(lam=1)={ys[-1]:.3f}',
          flush=True)

RESULTS['f5'] = {'f_grid': f_grid.tolist(), 'adoption_herd': ad_herd,
                 'adoption_pred': f_pred_herd,
                 'lam_grid': lam5.tolist(), 'friction': fric}

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
axa.plot(f_grid, f4[beta5]['F'][0] * (1 - f_grid), '-', lw=1.8, color=CB[0],
         label='law: $(1-f) F$')
axa.plot(f_grid, ad_herd, 's', ms=6, mfc='none', mec=CB[4], mew=1.6,
         label='simulation (herd)')
axa.set_xlabel('password-manager adoption $f$')
axa.set_ylabel('takeover fraction ($\\beta$=1.2, $b$=0.4)')
axa.legend(loc='lower left', bbox_to_anchor=(0, 1.0), fontsize=8.4,
           title='Adoption: linear for the herd', title_fontsize=8.8,
           frameon=False)
clean_axis(axa)

for c, beta in zip([CB[1], CB[3], CB[4]], [0.8, 1.2, 1.5]):
    axb.plot(lam5, fric[beta], 'o-', ms=4.5, lw=1.6, color=c,
             label=f'$\\beta$ = {beta}')
axb.set_xlabel('lockout friction $\\lambda$')
axb.set_ylabel('takeover fraction ($b$=0.4)')
axb.legend(loc='lower left', bbox_to_anchor=(0, 1.0), fontsize=8.4,
           title='Friction is the backbone defense', title_fontsize=8.8,
           frameon=False)
clean_axis(axb)
save(fig, 'f5-interventions.png')

# ════════════════════════════════════════════════════════════════════════════
# F6 — law validation summary
# ════════════════════════════════════════════════════════════════════════════

print('F6: validation summary', flush=True)
res = {}
# L1 residuals
r1 = []
for rho in [0.2, 0.5, 0.8]:
    m = np.array(f1[rho]['meas'])
    p = np.array(f1[rho]['pred'])
    r1.extend(np.abs(m / p - 1).tolist())
# L3 residuals
r3 = []
for beta in betas:
    m = np.array(f2[beta]['meas'])
    p = np.maximum(np.array(f2[beta]['pred']), 1e-9)
    r3.extend((np.abs(m / p - 1))[m > 0.01].tolist())
# L2 residuals
r2 = []
for beta in [0.8, 1.2]:
    d = f4[beta]
    line = np.array(d['F_w']) + (1 - lam_grid) * np.array(d['F_s'])
    r2.extend(np.abs(np.array(d['F']) / line - 1).tolist())

res = {'L1_median': float(np.median(r1)), 'L1_max': float(np.max(r1)),
       'L3_median': float(np.median(r3)), 'L3_max': float(np.max(r3)),
       'L3_n': len(r3), 'L2_median': float(np.median(r2)),
       'L2_max': float(np.max(r2))}
RESULTS['f6'] = res
print(f'  L1: median {res["L1_median"]:.4f} max {res["L1_max"]:.4f}')
print(f'  L2: median {res["L2_median"]:.4f} max {res["L2_max"]:.4f}')
print(f'  L3: median {res["L3_median"]:.4f} max {res["L3_max"]:.4f} '
      f'({res["L3_n"]} points)', flush=True)

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
# L1: pred vs meas
for c, rho in zip(cols, [0.2, 0.5, 0.8]):
    axa.plot(f1[rho]['pred'], f1[rho]['meas'], 'o', ms=5, color=c,
             label=f'$\\rho$ = {rho}')
lim = [0, max(max(f1[0.5]['pred']), max(f1[0.8]['meas'])) * 1.15]
axa.plot(lim, lim, '--', color=G400, lw=1.2)
axa.set_xlabel('blast-radius law $F_w$ (closed form)')
axa.set_ylabel('measured $F_w$')
axa.legend(loc='lower left', bbox_to_anchor=(0, 1.0), fontsize=8.4,
           title=f'L1: exact law (median |err| {res["L1_median"]:.1%})',
           title_fontsize=8.8, frameon=False)
clean_axis(axa)

# L3: pred vs meas
for c, beta in zip(cols, betas):
    m = np.array(f2[beta]['meas'])
    p = np.array(f2[beta]['pred'])
    keep = m > 0.002
    axb.plot(p[keep], m[keep], 'o', ms=5, color=c, label=f'$\\beta$ = {beta}')
limb = [0, 1.0]
axb.plot(limb, limb, '--', color=G400, lw=1.2)
axb.set_xlabel('cascade law $F_w + F_s$ (closed form)')
axb.set_ylabel('measured $F_w + F_s$')
axb.legend(loc='lower left', bbox_to_anchor=(0, 1.0), fontsize=8.4,
           title=f'L3: concentration law (median |err| '
                 f'{res["L3_median"]:.1%})',
           title_fontsize=8.8, frameon=False)
clean_axis(axb)
save(fig, 'f6-law-validation.png')

with open(os.path.join(OUT, 'results.json'), 'w') as f:
    json.dump(RESULTS, f, indent=1)
print('results.json written', flush=True)
print('DONE P-026')
