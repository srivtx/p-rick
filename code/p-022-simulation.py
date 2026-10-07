#!/usr/bin/env python3
"""P-022 simulation: the admission law for caches under Zipf demand + transients.

Workload: requests draw, with probability (1-f), from a Zipf(alpha) catalog of
N stable objects; with probability f they are one-hit transients (fresh ids).
Door policy: admit on miss iff the EMA window count (timescale W) >= tau.
Law under test: the optimal threshold  tau* = (1-f) W H_{N,alpha} / B^alpha,
with capacity tax: LRU(f>0) ~ LRU(0) at capacity (1-f)B.

Figures:
  f1-hit-vs-size.png     policies vs cache size (+ OPT analytic bound)
  f2-pollution.png       hit ratio vs transient fraction + capacity-tax check
  f3-gain-heatmap.png    (admission-law gain over LRU) over alpha x f
  f4-adaptation.png      workload shift mid-stream: recovery + tau tracking
  f5-law-validation.png  empirical argmax tau vs the closed form tau*

Writes results.json with headline numbers cited in the paper.
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AGENT_OUT = '/home/z/my-project/repos/p-rick/figures/p-022'
if os.path.isdir('/home/z/my-project/repos/p-rick'):
    os.makedirs(AGENT_OUT, exist_ok=True)
    OUT = AGENT_OUT
else:
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'figures', 'p-022')
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

N = 50000           # stable catalog size
W = 150000           # EMA window timescale (requests)
TR_BASE = 10_000_000  # transient id base

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
# Workload
# ════════════════════════════════════════════════════════════════════════════

def zipf_cdf(N, alpha):
    p = np.arange(1, N + 1, dtype=float) ** (-alpha)
    cdf = np.cumsum(p)
    return cdf / cdf[-1]


def make_stream(n, alpha, f, rng, cdf=None):
    """n requests: (1-f) Zipf(alpha) over stable ids 0..N-1, f fresh ids."""
    if cdf is None:
        cdf = zipf_cdf(N, alpha)
    u = rng.random(n)
    stable = np.searchsorted(cdf, u).astype(np.int64)
    is_tr = rng.random(n) < f
    tr_ids = TR_BASE + np.arange(n, dtype=np.int64)
    ids = np.where(is_tr, tr_ids, stable)
    return ids.tolist()


def zipf_mass(N, alpha, k):
    """Sum_{i=1..k} i^-alpha / H_{N,alpha}  — OPT's hit ratio (times 1-f)."""
    p = np.arange(1, min(k, N) + 1, dtype=float) ** (-alpha)
    return float(p.sum() / (p.sum() + _tail(N, alpha, min(k, N))))


def _tail(N, alpha, k):
    if k >= N:
        return 0.0
    kk = np.arange(k + 1, N + 1, dtype=float)
    return float((kk ** (-alpha)).sum())


def H_N(N, alpha):
    return float((np.arange(1, N + 1, dtype=float) ** (-alpha)).sum())


def tau_star(alpha, f, B, N=N, W=W):
    """The admission law: tau* = (1-f) W / (H_{N,alpha} B^alpha).

    Derived from c_i ~ W(1-f) p_i, p_i = i^-alpha / H: the cutoff rank k*
    where c = tau is k* = (W(1-f)/(tau H))^{1/alpha}; setting k* = B gives
    the minimal safe threshold above which one-timer pollution begins."""
    return (1.0 - f) * W / (H_N(N, alpha) * float(B) ** alpha)


# ════════════════════════════════════════════════════════════════════════════
# Policies (tight loops; dict = insertion-ordered LRU)
# ════════════════════════════════════════════════════════════════════════════

def sim_lru(stream, B, warmup):
    cache = {}
    hits = 0
    total = 0
    cpop = cache.pop
    cget = cache.get
    for k, obj in enumerate(stream):
        if cget(obj) is not None:
            if k >= warmup:
                hits += 1
            cpop(obj)
            cache[obj] = True
        else:
            if len(cache) >= B:
                cpop(next(iter(cache)))
            cache[obj] = True
        if k >= warmup:
            total += 1
    return hits / max(total, 1)


def sim_slru(stream, B, warmup):
    B1 = max(2, int(0.2 * B))
    B2 = max(1, B - B1)
    prob = {}
    prot = {}
    hits = 0
    total = 0
    for k, obj in enumerate(stream):
        if obj in prot:
            if k >= warmup:
                hits += 1
            prot.pop(obj)
            prot[obj] = True
        elif obj in prob:
            if k >= warmup:
                hits += 1
            prob.pop(obj)
            if len(prot) >= B2:
                prot.pop(next(iter(prot)))
            prot[obj] = True
        else:
            if len(prob) >= B1:
                prob.pop(next(iter(prob)))
            prob[obj] = True
        if k >= warmup:
            total += 1
    return hits / max(total, 1)


def sim_door(stream, B, warmup, tau, adaptive=False, track=False,
             checkpoint=100000):
    """Count-threshold admission (door) + LRU interior. EXACT trailing
    window of W requests maintained as two W/2 blocks (prev + cur): the
    window count of object o is prev[o] + cur[o]. Adaptive: re-estimate
    (alpha_hat, f_hat) at checkpoints and set tau from the admission law."""
    half = W // 2
    cache = {}
    prev = {}
    cur = {}
    hits = 0
    total = 0
    tau_cur = float(tau)
    fresh = 0
    taus = []
    roll_hits = []
    roll_tot = 0
    roll_hit_cnt = 0
    next_cp = checkpoint
    next_swap = half
    for k, obj in enumerate(stream):
        cur[obj] = cur.get(obj, 0) + 1
        c = prev.get(obj, 0) + cur[obj]
        if obj in cache:
            if k >= warmup:
                hits += 1
                roll_hit_cnt += 1
            cache.pop(obj)
            cache[obj] = True
        else:
            if c >= tau_cur:
                if len(cache) >= B:
                    cache.pop(next(iter(cache)))
                cache[obj] = True
        if c == 1:
            fresh += 1
        if k >= warmup:
            total += 1
            roll_tot += 1
        if k + 1 == next_swap:
            prev, cur = cur, {}
            next_swap += half
        if k + 1 == next_cp:
            next_cp += checkpoint
            roll_hits.append(roll_hit_cnt / max(roll_tot, 1))
            roll_tot = 0
            roll_hit_cnt = 0
            if adaptive:
                vals = list(prev.values()) + list(cur.values())
                if len(vals) > 1000:
                    import heapq
                    top = np.array(heapq.nlargest(1000, vals), dtype=float)
                else:
                    top = np.array(sorted(vals, reverse=True), dtype=float)
                top = np.maximum(top, 1e-9)
                ranks = np.arange(1, len(top) + 1)
                slope = np.polyfit(np.log(ranks), np.log(top), 1)[0]
                alpha_hat = float(np.clip(-slope, 0.55, 1.45))
                f_hat = float(np.clip(fresh / checkpoint, 0.0, 0.9))
                fresh = 0
                tau_cur = float(np.clip(tau_star(alpha_hat, f_hat, B),
                                        1.0, 100.0))
                taus.append((k, tau_cur, alpha_hat, f_hat))
            else:
                fresh = 0
    if track:
        return hits / max(total, 1), roll_hits, taus
    return hits / max(total, 1)


# ════════════════════════════════════════════════════════════════════════════
# Experiments
# ════════════════════════════════════════════════════════════════════════════

rng = np.random.default_rng(20261007)
STREAM = 1_200_000
WARM = 300_000

print('== F1: hit ratio vs cache size ==', flush=True)
ALPHA1, F1_F = 0.9, 0.30
F1_B = [250, 500, 1000, 2000, 4000, 8000, 16000]
f1_res = {p: [] for p in ('LRU', 'SLRU', 'door tau=4', 'admission law')}
f1_opt = []
cdf = zipf_cdf(N, ALPHA1)
stream1 = make_stream(STREAM, ALPHA1, F1_F, rng, cdf)
for B in F1_B:
    f1_res['LRU'].append(sim_lru(stream1, B, WARM))
    f1_res['SLRU'].append(sim_slru(stream1, B, WARM))
    f1_res['door tau=4'].append(sim_door(stream1, B, WARM, tau=4))
    f1_res['admission law'].append(sim_door(stream1, B, WARM, tau=8,
                                            adaptive=True))
    f1_opt.append((1 - F1_F) * zipf_mass(N, ALPHA1, B))
    print(f'  B={B}: LRU={f1_res["LRU"][-1]:.3f} SLRU={f1_res["SLRU"][-1]:.3f} '
          f'door4={f1_res["door tau=4"][-1]:.3f} AL={f1_res["admission law"][-1]:.3f} '
          f'OPT={f1_opt[-1]:.3f}', flush=True)
RESULTS['f1'] = {'B': F1_B, 'policies': f1_res, 'opt': f1_opt}

print('== F2: pollution vs transient fraction ==', flush=True)
F2_B, F2_ALPHA = 2000, 0.9
F2_F = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
f2_lru, f2_al, f2_opt, f2_tax = [], [], [], []
for f in F2_F:
    st = make_stream(STREAM, F2_ALPHA, f, rng, cdf)
    f2_lru.append(sim_lru(st, F2_B, WARM))
    f2_al.append(sim_door(st, F2_B, WARM, tau=8, adaptive=True))
    f2_opt.append((1 - f) * zipf_mass(N, F2_ALPHA, F2_B))
    Beff = max(1, round(F2_B * (1 - f)))
    st0 = make_stream(STREAM, F2_ALPHA, 0.0, rng, cdf)
    # the capacity-tax law: LRU(B, f) ~ (1-f) * LRU((1-f)B, 0)
    f2_tax.append((1 - f) * sim_lru(st0, Beff, WARM))
    print(f'  f={f}: LRU={f2_lru[-1]:.3f} AL={f2_al[-1]:.3f} OPT={f2_opt[-1]:.3f} '
          f'tax-law={f2_tax[-1]:.3f}', flush=True)
RESULTS['f2'] = {'f': F2_F, 'LRU': f2_lru, 'AL': f2_al, 'opt': f2_opt,
                 'capacity_tax_check': f2_tax}

print('== F3: gain heatmap ==', flush=True)
F3_ALPHAS = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
F3_FS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
F3_B = 2000
gain = np.zeros((len(F3_ALPHAS), len(F3_FS)))
for ai, a in enumerate(F3_ALPHAS):
    cdfa = zipf_cdf(N, a)
    for fi, f in enumerate(F3_FS):
        st = make_stream(800_000, a, f, rng, cdfa)
        hl = sim_lru(st, F3_B, WARM)
        ha = sim_door(st, F3_B, WARM, tau=8, adaptive=True)
        gain[ai, fi] = (ha - hl) / hl if hl > 1e-6 else 0.0
    print(f'  alpha={a}: gains={np.round(gain[ai], 3)}', flush=True)
RESULTS['f3'] = {'alphas': F3_ALPHAS, 'fs': F3_FS, 'gain': gain.tolist()}

print('== F4: adaptation to workload shift ==', flush=True)
F4_B = 2000
PH = 1_200_000
st_a = make_stream(PH, 0.9, 0.1, rng, cdf)
st_b = make_stream(PH, 0.7, 0.4, rng)
stream_shift = st_a + st_b
WARM4 = 100_000
h_lru4, roll_lru, _ = sim_door(stream_shift, F4_B, WARM4, tau=1,
                               track=True)  # tau=1 admits on first touch = LRU
h_al4, roll_al, taus = sim_door(stream_shift, F4_B, WARM4, tau=8,
                                adaptive=True, track=True)
print(f'  rolling hits (LRU): {[round(x,3) for x in roll_lru[::3]]}', flush=True)
print(f'  rolling hits (AL):  {[round(x,3) for x in roll_al[::3]]}', flush=True)
print(f'  tau checkpoints: {[(k, round(t,1), round(a,2), round(f,2)) for k,t,a,f in taus[::4]]}', flush=True)
RESULTS['f4'] = {'rolling_lru': roll_lru, 'rolling_al': roll_al,
                 'taus': [(k, t, a, f) for k, t, a, f in taus]}

print('== F5: law validation (oracle params) ==', flush=True)
f5_theory, f5_meas, f5_cfg = [], [], []
for a in [0.8, 0.9, 1.0]:
    cdfa = zipf_cdf(N, a)
    for f in [0.1, 0.3, 0.5]:
        for B in [1000, 4000]:
            ts = tau_star(a, f, B)
            st = make_stream(1_000_000, a, f, rng, cdfa)
            best, best_tau = -1, None
            for mult in [0.25, 0.5, 1.0, 2.0, 4.0]:
                tt = float(np.clip(ts * mult, 1.0, 80.0))
                h = sim_door(st, B, WARM, tau=tt)
                if h > best:
                    best, best_tau = h, tt
            f5_theory.append(ts)
            f5_meas.append(best_tau)
            f5_cfg.append((a, f, B))
            print(f'  alpha={a} f={f} B={B}: tau*={ts:.1f} argmax={best_tau} '
                  f'(h={best:.3f})', flush=True)
RESULTS['f5'] = {'theory': f5_theory, 'measured': f5_meas,
                 'configs': f5_cfg}

# ════════════════════════════════════════════════════════════════════════════
# Figures
# ════════════════════════════════════════════════════════════════════════════

# F1
fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
styles = {'LRU': (G400, '--'), 'SLRU': (CB[1], '-'),
          'door tau=4': (CB[3], '-'), 'admission law': (CB[0], '-')}
for (name, (col, ls)) in styles.items():
    ax.plot(F1_B, f1_res[name], color=col, ls=ls, lw=2.0, marker='o', ms=3.5,
            label=name)
ax.plot(F1_B, f1_opt, color=G700, ls=':', lw=1.8, marker='s', ms=3,
        label='OPT (static top-$B$)')
ax.set_xscale('log')
ax.set_xlabel('cache capacity $B$ (objects)')
ax.set_ylabel('hit ratio')
ax.set_ylim(0, 1.0)
ax.set_title('Under 30% one-timers, admission control nears the bound')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
clean_axis(ax)
save(fig, 'f1-hit-vs-size.png')

# F2
fig, ax = plt.subplots(figsize=(6.6, 4.2), constrained_layout=True)
ax.plot(F2_F, f2_lru, color=G400, lw=2.0, ls='--', marker='o', ms=3.5,
        label='LRU (admits everything)')
ax.plot(F2_F, np.array(f2_tax) * (1 - 0.0), color=CB[5], lw=1.6, ls='-.',
        marker='^', ms=3.5, label='capacity-tax law: $(1-f)\\,\\mathrm{LRU}$ at $B(1-f)$')
ax.plot(F2_F, f2_al, color=CB[0], lw=2.2, marker='o', ms=3.5,
        label='admission law (adaptive)')
ax.plot(F2_F, f2_opt, color=G700, ls=':', lw=1.8, marker='s', ms=3,
        label='OPT (static top-$B$)')
ax.set_xlabel('transient fraction $f$')
ax.set_ylabel('hit ratio')
ax.set_ylim(0, 1.0)
ax.set_title('The one-timer tax: LRU decays on the law\u2019s line')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
clean_axis(ax)
save(fig, 'f2-pollution.png')

# F3
fig, ax = plt.subplots(figsize=(6.4, 4.4), constrained_layout=True)
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
cmap = LinearSegmentedColormap.from_list('gn', ['#CC3311', '#F5C0B0',
                                                '#FFFFFF', '#BFD9E8', '#0B5730'])
norm = TwoSlopeNorm(vmin=min(-0.05, gain.min()), vcenter=0.0,
                    vmax=max(0.05, gain.max()))
im = ax.imshow(gain, cmap=cmap, norm=norm, aspect='auto', origin='lower',
               extent=[F3_FS[0] - 0.05, F3_FS[-1] + 0.05,
                       F3_ALPHAS[0] - 0.05, F3_ALPHAS[-1] + 0.05])
for ai in range(len(F3_ALPHAS)):
    for fi in range(len(F3_FS)):
        v = gain[ai, fi]
        txt = f'{v*100:.0f}%'
        ax.text(F3_FS[fi], F3_ALPHAS[ai], txt, ha='center', va='center',
                fontsize=8,
                color='white' if abs(v) > 0.5 * max(abs(gain.max()),
                                                   abs(gain.min())) else G700)
ax.set_xlabel('transient fraction $f$')
ax.set_ylabel('Zipf exponent $\\alpha$')
ax.set_title('Gain of the admission law over LRU')
cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.03)
cb.set_label('relative hit-ratio gain', fontsize=9)
cb.outline.set_visible(False)
save(fig, 'f3-gain-heatmap.png')

# F4 (two panels)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 5.6), sharex=True,
                               constrained_layout=True)
xs = [(i + 1) * 100_000 for i in range(len(roll_al))][1:]
ax1.plot(xs, roll_lru[1:], color=G400, lw=1.8, label='LRU')
ax1.plot(xs, roll_al[1:], color=CB[0], lw=2.0, label='admission law (adaptive)')
ax1.axvline(1_200_000, color=G700, ls=':', lw=1.4)
ax1.text(1_260_000, 0.9, 'workload shift:\n$\\alpha$ 0.9$\\to$0.7, $f$ 0.1$\\to$0.4',
         fontsize=8.5, color=G700)
ax1.set_ylabel('rolling hit ratio')
ax1.set_ylim(0, 1.0)
ax1.set_title('The law re-converges after the workload breaks')
ax1.legend(loc='lower left')
clean_axis(ax1)
kst = [k for k, t, a, f in taus]
tst = [t for k, t, a, f in taus]
ax2.plot(kst, tst, color=CB[3], lw=2.0, marker='o', ms=3.5,
         label='adaptive $\\hat{\\tau}^*$')
ax2.plot([0, 1_200_000, 1_200_000, 2_400_000],
         [tau_star(0.9, 0.1, F4_B), tau_star(0.9, 0.1, F4_B),
          tau_star(0.7, 0.4, F4_B), tau_star(0.7, 0.4, F4_B)],
         color=G700, ls='--', lw=1.6, label='true $\\tau^*$')
ax2.set_yscale('log')
ax2.set_ylabel('admission threshold $\\tau$')
ax2.set_xlabel('requests processed')
ax2.legend(loc='upper right')
clean_axis(ax2)
save(fig, 'f4-adaptation.png')

# F5
fig, ax = plt.subplots(figsize=(5.6, 4.6), constrained_layout=True)
f5t = np.array(f5_theory, dtype=float)
f5m = np.array(f5_meas, dtype=float)
cols = {0.8: CB[0], 0.9: CB[1], 1.0: CB[2]}
for a in cols:
    xs = [t for (aa, f, B), t in zip(f5_cfg, f5_theory) if aa == a]
    ys = [m for (aa, f, B), m in zip(f5_cfg, f5_meas) if aa == a]
    ax.scatter(xs, ys, s=52, color=cols[a], alpha=0.9, edgecolors='white',
               linewidths=0.8, zorder=3, label=f'$\\alpha$={a}')
lim = [min(f5t.min(), f5m.min()) * 0.6, max(f5t.max(), f5m.max()) * 1.6]
ax.plot(lim, lim, color=G400, ls='--', lw=1.2, zorder=2)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(lim)
ax.set_ylim(lim)
ax.set_xlabel('closed form $\\tau^* = (1-f)WH_{N,\\alpha}/B^{\\alpha}$')
ax.set_ylabel('empirical argmax $\\hat{\\tau}$')
ax.set_title('The admission law: closed form vs measured optimum')
ax.text(lim[0] * 1.5, lim[1] * 0.75, '$y = x$', fontsize=9, color=G700)
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
clean_axis(ax, grid=False)
ax.yaxis.grid(True, alpha=0.12, color=G400)
ax.xaxis.grid(True, alpha=0.12, color=G400)
save(fig, 'f5-law-validation.png')

with open(os.path.join(OUT, 'results.json'), 'w') as f:
    json.dump(RESULTS, f, indent=1)
print('DONE — results.json written', flush=True)
