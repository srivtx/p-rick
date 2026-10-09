#!/usr/bin/env python3
"""P-025b: the unified finite-R collapse laws — fixed harness + new experiments.

Companion to code/p-025-simulation.py (v1.0 harness). This file keeps the
model identical (single FCFS server, rate mu=1; Poisson arrivals lambda;
per-attempt timeout T; policy backoff; give-up budget R; timed-out work is
still served) and repairs/adds the measurement layer:

 FIXES vs v1.0
  - per-attempt send times recorded; the timeout kernel is measured from the
    true sojourns of attempts completing inside a final window (v1.0 counted
    whole-run tallies on single seeds -> run-to-run sd ~33%, and the paper's
    quoted kernel numbers were not in results.json at all)
  - busy_time is actually accumulated (v1.0 had `busy_time += 0.0`), so
    utilization is measured, not inferred from completions
  - ONE bisection protocol (same horizon, steps, classifier) for every
    collapse measurement in the paper (v1.0 used different setups in F2 and
    F5, which is why "theta=5, jitter, uncapped" read 0.478 / 0.450 / 0.510
    in three different sections)
  - headline numbers are multi-seed (mean +/- spread); v1.0's policy grid was
    one seed per cell, so the fixed-backoff resonance penalty and several
    margins were single draws
  - the queue-cap experiment reports goodput-vs-load curves and crater
    thresholds, not a "collapse load" that exceeded mu (a classifier artifact:
    counting 80%-goodput load shedding as survival)

 NEW (F7): the unified finite-R fixed-point curve
      g_R(rho) = rho (1 - q) / (1 - q^R),   q = e^{-theta (1-rho)}
  whose maximum is the collapse ceiling lambda_c(R) and whose rho -> 1
  endpoint is the recovery threshold mu/R. One curve, two thresholds.
  Validated three ways: fixed-point R-shift at theta=2, an R-sweep of
  collapse loads, and the R=2 empty-hysteresis-band prediction.

Seed master: 20261009 (distinct from v1.0's 20261007 so the two harnesses
are independent draws, not replays).
"""
import heapq
import json
import math
import os
import random
import statistics as st
from collections import deque

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.environ.get('P025_OUT', os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'figures', 'p-025'))
os.makedirs(OUT, exist_ok=True)

SEED = 20261009
RESULTS = {}

def mkseed(*parts):
    z = SEED
    for p in parts:
        if p is None:
            q = 0
        elif isinstance(p, str):
            q = sum((i + 1) * ord(c) for i, c in enumerate(p))
        elif isinstance(p, float):
            q = int(p * 1000)
        else:
            q = int(p)
        z = (z * 1000003) ^ (q & 0xFFFFFFFF)
        z &= 0xFFFFFFFFFFFF
    return z


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


# closed-form pieces ---------------------------------------------------------

def rho_star(theta):
    r = 0.85
    for _ in range(80):
        g = theta * (1 - r) - math.log(1 + theta * r)
        gp = -theta - theta / (1 + theta * r)
        r -= g / gp
        r = min(max(r, 1e-9), 1 - 1e-9)
    return r


def lambda_c_closed(theta):
    r = rho_star(theta)
    return theta * r * r / (1 + theta * r)


def g_of_rho(rho, theta, R):
    """Unified fixed-point curve. R=None means infinite retries."""
    q = np.exp(-theta * (1.0 - rho))
    if R is None:
        return rho * (1.0 - q)
    return rho * (1.0 - q) / (1.0 - q**R)


def ceiling_R(theta, R):
    grid = np.linspace(1e-4, 1.0 - 1e-9, 400001)
    g = g_of_rho(grid, theta, R)
    i = int(g.argmax())
    return float(g[i]), float(grid[i])


def roots_of_lam(lam, theta, R=None):
    """Roots of g_R(rho) = lam on (0,1), by sign scanning."""
    grid = np.linspace(1e-4, 1.0 - 1e-9, 20001)
    g = g_of_rho(grid, theta, R)
    roots = []
    for i in range(len(grid) - 1):
        if (g[i] - lam) * (g[i + 1] - lam) < 0:
            # linear interp
            x0, x1, y0, y1 = grid[i], grid[i + 1], g[i], g[i + 1]
            roots.append(float(x0 + (lam - y0) * (x1 - x0) / (y1 - y0)))
    return roots


def backoff(policy, attempt, T, rng):
    if policy == 'none':
        return 0.0
    if policy == 'fixed':
        return 0.5 * T
    if policy == 'exp':
        return min(2.0 ** (attempt - 1), 8.0) * T
    if policy == 'jitter':
        return rng.uniform(0.0, min(2.0 ** attempt, 8.0) * T)
    raise ValueError(policy)


# simulator ------------------------------------------------------------------

class Sim:
    """Single-server FCFS queue with client timeouts, retries, give-ups.

    Repairs vs v1.0: per-attempt send times, true sojourn recording, real
    busy-time accumulation, fast-reject accounting.
    """

    def __init__(self, lam, T, policy, R, seed, qcap=None, preload=0):
        self.lam, self.T, self.policy, self.R = lam, T, policy, R
        self.qcap = qcap
        self.rng = random.Random(seed)
        self.heap = []
        self.seq = 0
        self.queue = deque()          # (aid, job, send_time)
        self.server_busy = False
        self.now = 0.0
        # metrics
        self.successes = 0
        self.giveups = 0
        self.arrivals = 0
        self.attempts = 0             # attempts spawned (incl. fast rejects)
        self.enqueued = 0             # attempts admitted to the queue
        self.fast_rejects = 0
        self.busy_time = 0.0
        self.inflight = 0
        self.wasted = 0               # completed after its client timed out
        self.completions = []         # (sojourn, timed_out) per completed attempt
        self.backoff_sum = 0.0
        self.backoff_n = 0
        self.events = 0
        self.preload = preload
        self.arr_seeded = False
        self.collapsed_flag = False
        for _ in range(self.preload):
            self.arrivals += 1
            self.inflight += 1
            job = {'left': self.R, 'tries': 0, 'last_aid': -1,
                   'timed_out': set()}
            self._spawn_attempt(job)

    def push(self, t, kind, payload=None):
        self.seq += 1
        heapq.heappush(self.heap, (t, self.seq, kind, payload))

    def _spawn_attempt(self, job):
        self.attempts += 1
        aid = self.attempts
        if self.qcap is not None and len(self.queue) >= self.qcap:
            self.fast_rejects += 1
            job['left'] -= 1
            if job['left'] > 0:
                b = backoff(self.policy, job['tries'], self.T, self.rng)
                self.backoff_sum += b
                self.backoff_n += 1
                self.push(self.now + b, 'retry', job)
            else:
                self.giveups += 1
                self.inflight -= 1
                job['left'] = -10**9
            return
        job['tries'] += 1
        job['last_aid'] = aid
        self.enqueued += 1
        self.queue.append((aid, job, self.now))
        self.push(self.now + self.T, 'to', (aid, job))
        self._maybe_start_service()

    def _maybe_start_service(self):
        if not self.server_busy and self.queue:
            self.server_busy = True
            aid, job, send = self.queue.popleft()
            self.push(self.now + self.rng.expovariate(1.0), 'done', (aid, job, send))

    def _next_service(self):
        if self.queue:
            aid, job, send = self.queue.popleft()
            self.push(self.now + self.rng.expovariate(1.0), 'done', (aid, job, send))
        else:
            self.server_busy = False

    def run(self, horizon, event_cap=500_000, inflight_cap=4000):
        if not self.arr_seeded:
            self.arr_seeded = True
            self.push(self.rng.expovariate(self.lam), 'arr', None)
        while self.heap and self.events < event_cap:
            evt = heapq.heappop(self.heap)
            if evt[0] > horizon:
                heapq.heappush(self.heap, evt)
                break
            if self.server_busy:
                self.busy_time += evt[0] - self.now
            self.now, _, kind, payload = evt
            self.events += 1
            if self.inflight > inflight_cap:
                self.collapsed_flag = True
                break
            if kind == 'arr':
                self.arrivals += 1
                self.inflight += 1
                job = {'left': self.R, 'tries': 0, 'last_aid': -1,
                       'timed_out': set()}
                self._spawn_attempt(job)
                self.push(self.now + self.rng.expovariate(self.lam), 'arr', None)
            elif kind == 'to':
                aid, job = payload
                if job['left'] >= 0 and aid == job['last_aid'] and \
                        aid not in job['timed_out']:
                    job['timed_out'].add(aid)
                    job['left'] -= 1
                    if job['left'] > 0:
                        b = backoff(self.policy, job['tries'], self.T, self.rng)
                        self.backoff_sum += b
                        self.backoff_n += 1
                        self.push(self.now + b, 'retry', job)
                    else:
                        self.giveups += 1
                        self.inflight -= 1
                        job['left'] = -10**9
            elif kind == 'retry':
                job = payload
                if job['left'] > 0:
                    self._spawn_attempt(job)
            elif kind == 'done':
                aid, job, send = payload
                if self.server_busy:
                    self._next_service()
                timed_out = aid in job['timed_out'] or job['left'] <= 0
                self.completions.append((self.now - send, timed_out))
                if aid == job['last_aid'] and job['left'] > 0 and \
                        aid not in job['timed_out']:
                    self.successes += 1
                    self.inflight -= 1
                    job['left'] = -10**9
                else:
                    self.wasted += 1
        return self

    # -- window measurement --------------------------------------------------

    def run_window(self, horizon, warm_frac=0.5, event_cap=500_000):
        """Run to `horizon`; return stats measured on the final (1-warm_frac)
        window only. Warmup excluded so late storms are not diluted."""
        warm_t = warm_frac * horizon
        self.run(warm_t, event_cap=event_cap)
        snap = self.snapshot()
        self.run(horizon, event_cap=event_cap)
        return self.window_stats(snap)

    def snapshot(self):
        n = len(self.completions)
        return {'t': self.now, 'arr': self.arrivals, 'succ': self.successes,
                'giveup': self.giveups, 'att': self.attempts,
                'enq': self.enqueued, 'rej': self.fast_rejects,
                'busy': self.busy_time, 'wasted': self.wasted,
                'comp_n': n, 'inflight': self.inflight,
                'collapsed': self.collapsed_flag}

    def window_stats(self, s0):
        dt = max(1e-9, self.now - s0['t'])
        arr = self.arrivals - s0['arr']
        succ = self.successes - s0['succ']
        att = self.attempts - s0['att']
        enq = self.enqueued - s0['enq']
        rej = self.fast_rejects - s0['rej']
        busy = self.busy_time - s0['busy']
        wasted = self.wasted - s0['wasted']
        comp = self.completions[s0['comp_n']:]
        n = len(comp)
        timed = sum(1 for _, to in comp if to)
        soj_mean = (sum(s for s, _ in comp) / n) if n else float('nan')
        return {
            'dt': dt, 'arr': arr, 'succ': succ, 'giveup': self.giveups - s0['giveup'],
            'att': att, 'enq': enq, 'rej': rej, 'busy': busy, 'wasted': wasted,
            'comp_n': n, 'timed': timed,
            'q_frac': (timed / n) if n > 0 else float('nan'),
            'goodput_ratio': (succ / arr) if arr > 0 else float('nan'),
            'busy_frac': busy / dt,
            'rho': (self.successes + self.wasted - s0['succ'] - s0['wasted']) / dt,
            'sojourn_mean': soj_mean,
            'amplification': (att / succ) if succ > 0 else float('inf'),
            'inflight': self.inflight,
            'collapsed_flag': self.collapsed_flag,
        }


# unified collapse protocol --------------------------------------------------

def classify(win, lam, qcap):
    """Goodput-80 classifier (v1.0's, applied uniformly); plus crater flag."""
    if win['collapsed_flag'] or win['arr'] < 10:
        collapsed = win['collapsed_flag']
    else:
        collapsed = win['succ'] < 0.8 * win['arr']
        if not collapsed and qcap is None:
            collapsed = win['busy_frac'] >= 0.95
    crater = (win['arr'] >= 10 and win['succ'] < 0.3 * win['arr']) \
        or win['collapsed_flag']
    return collapsed, crater


def bisect_lambda(T, policy, R, seed, qcap=None, lo=0.05, hi=1.4,
                  steps=9, horizon_mult=90, criterion='g80', warm_frac=0.78):
    """The ONE collapse-load bisection used everywhere in the paper."""
    for _ in range(steps):
        mid = 0.5 * (lo + hi)
        horizon = horizon_mult * (T + 1) + 150
        s = Sim(mid, T, policy, R, seed, qcap=qcap)
        win = s.run_window(horizon, warm_frac=warm_frac)
        coll, crater = classify(win, mid, qcap)
        fire = coll if criterion == 'g80' else crater
        if fire:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def multi_bisect(T, policy, R, seeds, qcap=None, criterion='g80',
                 horizon_mult=90, steps=9, lo=0.05, hi=1.4):
    vals = [bisect_lambda(T, policy, R, sd, qcap=qcap, steps=steps,
                          horizon_mult=horizon_mult, criterion=criterion,
                          lo=lo, hi=hi) for sd in seeds]
    return {'mean': st.mean(vals), 'sd': st.stdev(vals) if len(vals) > 1 else 0.0,
            'min': min(vals), 'max': max(vals), 'vals': vals}


# ============================================================================
# E1/F1 — kernel (multi-seed) and the fixed point on the good branch
# ============================================================================
print('F1: kernel + fixed-point curve (multi-seed)', flush=True)
TH1, T1 = 5.0, 5.0
lcs5 = lambda_c_closed(5.0)

# kernel: no-retry runs, 12 loads x 8 seeds, final-window sojourn-based q
kern = []
for lam in np.linspace(0.2, 0.92, 12):
    qs = []
    for sd in range(8):
        s = Sim(float(lam), T1, 'none', 1, mkseed(11, int(lam * 100), sd))
        win = s.run_window(3000.0, warm_frac=0.5, event_cap=2_000_000)
        if win['comp_n'] > 50:
            qs.append(win['q_frac'])
    kern.append({'lam': float(lam), 'q_mean': st.mean(qs),
                 'q_sd': st.stdev(qs), 'n': len(qs),
                 'q_theory': math.exp(-(1.0 - lam) * T1)})
    print(f"  kernel lam={lam:.3f}: q={kern[-1]['q_mean']:.4f}"
          f"+/-{kern[-1]['q_sd']:.4f} theory={kern[-1]['q_theory']:.4f}", flush=True)
kern_rel = [abs(k['q_mean'] - k['q_theory']) / k['q_theory'] for k in kern]
print(f"  kernel: median rel err = {st.median(kern_rel):.3f}", flush=True)
RESULTS['f1_kernel'] = kern
RESULTS['f1_kernel_median_relerr'] = st.median(kern_rel)

# fixed point: R=6, BOTH the fluid assumption's own policy ('none' =
# instant re-offer) and deployment jitter; tip = utilization far above root
fp_by_pol = {}
for pol_fp in ['none', 'jitter']:
    fp = []
    for lam in np.round(np.linspace(0.15, 0.40, 8), 3):
        rhos, tipped = [], 0
        for sd in range(8):
            s = Sim(float(lam), T1, pol_fp, 6, mkseed(12, pol_fp,
                                                      int(lam * 100), sd))
            win = s.run_window(400.0, warm_frac=0.5, event_cap=300_000)
            rts = roots_of_lam(float(lam), TH1, 6)
            pred = min(rts) if rts else float('nan')
            if win['collapsed_flag'] or win['busy_frac'] > pred + 0.25:
                tipped += 1
            else:
                rhos.append(win['busy_frac'])
        fp.append({'lam': float(lam), 'rho_mean': st.mean(rhos) if rhos else None,
                   'rho_sd': st.stdev(rhos) if len(rhos) > 1 else 0.0,
                   'rho_pred': pred, 'tipped_runs': tipped, 'n_ok': len(rhos)})
        print(f"  fp[{pol_fp}] lam={lam:.2f}: rho="
              f"{fp[-1]['rho_mean']} pred={pred:.3f} tipped {tipped}/8",
              flush=True)
    fp_by_pol[pol_fp] = fp
fp = fp_by_pol['none']
ok = [p for p in fp if p['rho_mean'] is not None]
errs = [abs(p['rho_mean'] - p['rho_pred']) / p['rho_pred'] for p in ok]
okj = [p for p in fp_by_pol['jitter'] if p['rho_mean'] is not None]
errsj = [abs(p['rho_mean'] - p['rho_pred']) / p['rho_pred'] for p in okj]
RESULTS['f1_fixedpoint'] = fp
RESULTS['f1_fixedpoint_jitter'] = fp_by_pol['jitter']
RESULTS['f1_fixedpoint_median_relerr'] = st.median(errs)
RESULTS['f1_fixedpoint_jitter_median_relerr'] = st.median(errsj)
RESULTS['f1_fixedpoint_n'] = len(ok)
print(f"  fixed point median rel err: none {st.median(errs):.3f} (n={len(ok)}), "
      f"jitter {st.median(errsj):.3f} (n={len(okj)})", flush=True)

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
rhos = np.linspace(0.02, 0.985, 300)
axa.plot(g_of_rho(rhos, TH1, None), rhos, '-', color=CB[0], lw=2.0,
         label='mean field $\\lambda(\\rho)$, $R\\to\\infty$')
axa.plot(g_of_rho(rhos, TH1, 6), rhos, '--', color=CB[1], lw=1.4,
         label='$g_6(\\rho)$ (finite $R$)')
rs5 = rho_star(5.0)
axa.plot([lcs5], [rs5], 'o', ms=9, color=CB[4], zorder=5)
axa.annotate('tangency $(\\lambda_c, \\rho^*)$', (lcs5, rs5), xytext=(-90, 14),
             textcoords='offset points', fontsize=9, color=CB[4],
             arrowprops=dict(arrowstyle='-', color=CB[4], lw=0.8))
px = [p['lam'] for p in ok]
py = [p['rho_mean'] for p in ok]
pe = [1.96 * p['rho_sd'] / math.sqrt(max(1, p['n_ok'])) for p in ok]
axa.errorbar(px, py, yerr=pe, fmt='s', ms=6, mfc='none', mec=CB[2], mew=1.6,
             elinewidth=1.2, capsize=3, label='sim: instant re-offer (8 seeds)',
             zorder=4)
pxj = [p['lam'] for p in okj]
pyj = [p['rho_mean'] for p in okj]
pej = [1.96 * p['rho_sd'] / math.sqrt(max(1, p['n_ok'])) for p in okj]
axa.errorbar(pxj, pyj, yerr=pej, fmt='D', ms=5, mfc='none', mec=CB[3], mew=1.5,
             elinewidth=1.1, capsize=3, label='sim: jittered retries', zorder=3)
axa.set_xlabel('offered load $\\lambda$ (per unit $\\mu$)')
axa.set_ylabel('server utilization $\\rho$')
axa.set_title(f'Fixed-point curve, $\\theta = \\mu T = {TH1:.0f}$, $R = 6$')
axa.legend(loc='lower right', fontsize=8.8)
clean_axis(axa)

kx = [k['lam'] for k in kern]
ky = [k['q_mean'] for k in kern]
ke = [1.96 * k['q_sd'] / math.sqrt(k['n']) for k in kern]
axb.errorbar(kx, ky, yerr=ke, fmt='s', ms=6, mfc='none', mec=CB[2], mew=1.6,
             elinewidth=1.2, capsize=3, label='simulation (8 seeds)', zorder=4)
rgrid = np.linspace(0.02, 0.95, 200)
axb.plot(rgrid, np.exp(-TH1 * (1 - rgrid)), '-', color=CB[0], lw=2.0,
         label='M/M/1: $q = e^{-\\mu(1-\\rho)T}$')
axb.set_xlabel('offered load $\\lambda$ (per unit $\\mu$; no-retry runs)')
axb.set_ylabel('timeout fraction $q$')
axb.set_title('The timeout kernel')
axb.legend(loc='upper left', fontsize=8.8)
clean_axis(axb)
save(fig, 'f1-fixed-point.png')

# ============================================================================
# E2/F2 — policy grid (multi-seed), horizon drift, burst separatrix
# ============================================================================
print('F2: policy grid + drift + separatrix', flush=True)
thetas = [2.0, 5.0, 20.0]
policies_grid = ['none', 'fixed', 'exp', 'jitter']
grid_meas = {}
for th in thetas:
    for pol in policies_grid:
        n_seeds = 8 if (th == 5.0 and pol in ('none', 'fixed')) else 5
        seeds = [mkseed(21, int(th), policies_grid.index(pol), k)
                 for k in range(n_seeds)]
        mb = multi_bisect(th, pol, 6, seeds, steps=9, horizon_mult=90)
        grid_meas[(th, pol)] = mb
        print(f"  theta={th:.0f} {pol}: {mb['mean']:.3f} +/- {mb['sd']:.3f} "
              f"[{mb['min']:.3f}, {mb['max']:.3f}]  ceiling "
              f"{lambda_c_closed(th):.3f}", flush=True)
RESULTS['f2_grid'] = {f'{t:.0f}|{p}': grid_meas[(t, p)]
                      for t in thetas for p in policies_grid}

# horizon drift: theta=5, jitter, 4 horizons x 3 seeds
drift = []
for hm in [30, 60, 120, 240]:
    seeds = [mkseed(22, hm, k) for k in range(3)]
    mb = multi_bisect(5.0, 'jitter', 6, seeds, steps=9, horizon_mult=hm)
    drift.append({'hm': hm, **mb})
    print(f"  horizon mult {hm}: {mb['mean']:.3f} +/- {mb['sd']:.3f}", flush=True)
RESULTS['f2_drift'] = drift

# burst separatrix: preload N synchronized attempts at 0.5 lambda_c
lam_fix = 0.5 * lcs5
rho_b = max(roots_of_lam(lam_fix, 5.0, 6))
L_b = rho_b / (1 - rho_b)
Nb_list = []
for k in range(3):
    lo, hi = 0, 80
    for _ in range(7):
        mid = (lo + hi) // 2
        s = Sim(lam_fix, 5.0, 'jitter', 6, mkseed(23, mid, k), preload=int(mid))
        s.run(40 * 5.0 + 100, event_cap=200_000)
        served = (s.successes + s.wasted) / max(1.0, s.now)
        coll = s.collapsed_flag or (s.arrivals >= 10 and
                                    s.successes < 0.8 * s.arrivals) or \
            (s.qcap is None and s.now > 50 and served >= 0.95)
        if coll:
            hi = mid
        else:
            lo = mid
    Nb_list.append(hi)
RESULTS['f2_separatrix'] = {'lam_fix': lam_fix, 'rho_b': rho_b,
                            'L_b_theory': L_b,
                            'Nb_seeds': Nb_list,
                            'Nb_mean': st.mean(Nb_list)}
print(f"  separatrix: mean-field L(rho_b)={L_b:.1f}, measured N_b "
      f"{st.mean(Nb_list):.1f} (seeds {Nb_list})", flush=True)

# E2d: direct measurement of the tipping probability P(collapse within
# horizon) — the honest form of the "metastability signature". The v1.0
# drift experiment's claim that readings cross the ceiling at theta=5 is
# withdrawn (below); P-tip is what a bisection threshold really estimates.
ptip = {}
for th_pt, lams_pt in [(2.0, np.round(np.arange(0.12, 0.331, 0.02), 3)),
                       (5.0, np.round(np.arange(0.30, 0.551, 0.025), 3))]:
    curve = []
    for lam in lams_pt:
        c = 0
        n = 24
        for sd in range(n):
            s = Sim(float(lam), float(th_pt), 'jitter', 6, 21000 + sd)
            win = s.run_window(90 * (th_pt + 1) + 150, warm_frac=0.78)
            coll, _ = classify(win, float(lam), None)
            if coll:
                c += 1
        curve.append({'lam': float(lam), 'p': c / n})
        print(f"  P-tip theta={th_pt:.0f} lam={lam:.3f}: {c}/{n}", flush=True)
    ptip[str(th_pt)] = curve
RESULTS['f2_ptip'] = ptip

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
th_c = np.linspace(1.0, 40, 200)
axa.plot(th_c, [lambda_c_closed(t) for t in th_c], '-', color=CB[0], lw=2.0,
         label='ceiling $\\lambda_c = \\mu\\theta\\rho^{*2}/(1+\\theta\\rho^*)$')
cols = dict(zip(policies_grid, [G700, CB[1], CB[3], CB[2]]))
mks = dict(zip(policies_grid, ['v', '^', 'D', 'o']))
for pol in policies_grid:
    ys = [grid_meas[(t, pol)]['mean'] for t in thetas]
    ye = [grid_meas[(t, pol)]['sd'] for t in thetas]
    axa.errorbar(thetas, ys, yerr=ye, fmt=mks[pol], ms=8, mfc='none',
                 mec=cols[pol], mew=1.8, elinewidth=1.3, capsize=3, ls='none',
                 label=f'{pol} retry (5-8 seeds)')
axa.set_xlabel('timeout slack $\\theta = \\mu T$')
axa.set_ylabel('collapse load (per unit $\\mu$)')
axa.set_title('The ceiling and the policy approach')
axa.legend(loc='lower right', fontsize=8.6)
clean_axis(axa)

for th_pt, col in [(2.0, CB[1]), (5.0, CB[2])]:
    curve = ptip[str(th_pt)]
    axb.plot([c['lam'] for c in curve], [c['p'] for c in curve], 'o-',
             ms=4, lw=1.6, color=col, label=f'$\\theta = {th_pt:.0f}$, jitter')
axb.axvline(lambda_c_closed(2.0), color=CB[1], ls='--', lw=1.2)
axb.axvline(lcs5, color=CB[2], ls='--', lw=1.2)
axb.annotate('ceiling 0.330', (lambda_c_closed(2.0) + 0.008, 0.45), fontsize=8.5,
             color=CB[1], rotation=90)
axb.annotate('ceiling 0.544', (lcs5 + 0.008, 0.45), fontsize=8.5,
             color=CB[2], rotation=90)
axb.set_xlabel('arrival load $\\lambda$ (per unit $\\mu$)')
axb.set_ylabel('P(collapse within horizon), 24 seeds')
axb.set_title('Tipping probability: the metastability signature')
axb.set_ylim(-0.04, 1.04)
axb.legend(loc='upper left', fontsize=8.8)
clean_axis(axb)
save(fig, 'f2-collapse-law.png')

# ============================================================================
# E3/F3 — hysteresis ramp, recovery thresholds, drain times, R=inf trap
# ============================================================================
print('F3: hysteresis + recovery', flush=True)
T3, R3 = 5.0, 6
policies = ['none', 'fixed', 'exp', 'jitter']


def ramp(policy, seed0, R=R3):
    s = Sim(0.15, T3, policy, R, seed0)
    s.run(20 * T3 + 40, event_cap=200_000)
    lams, rates, phase = [], [], []
    seq = (list(np.arange(0.15, 1.06, 0.075)) +
           list(np.arange(1.05, 0.031, -0.05)))
    for i, lam in enumerate(seq):
        s.lam = float(lam)
        a0, b0 = s.arrivals, s.successes
        s.run(s.now + 25 * T3 + 50, event_cap=400_000)
        arr = s.arrivals - a0
        suc = s.successes - b0
        rate = (suc / arr) if arr > 10 else (0.0 if s.collapsed_flag else 1.0)
        lams.append(float(lam))
        rates.append(rate)
        phase.append('up' if i < 13 else 'down')
    return lams, rates, phase


hyst = {}
for pol in policies:
    l, r, ph = ramp(pol, mkseed(3, policies.index(pol)))
    up = [x for x, p in zip(l, ph) if p == 'up']
    down = [x for x, p in zip(l, ph) if p == 'down']
    ru = [x for x, p in zip(r, ph) if p == 'up']
    rd = [x for x, p in zip(r, ph) if p == 'down']
    lam_up = next((x for x, y in zip(up, ru) if y < 0.5), None)
    lam_dn = next((x for x, y in zip(reversed(down), reversed(rd)) if y > 0.5),
                  None)
    hyst[pol] = {'lam': l, 'rate': r, 'phase': ph,
                 'lam_c_up': lam_up, 'lam_r': lam_dn}
    print(f'  {pol}: collapse at {lam_up}, recovery at {lam_dn}', flush=True)


def recovery_threshold(R, T=5.0, policy='jitter', lo=0.02, hi=0.45,
                       t_push=700.0, t_hold=2500.0, seed_fn=None):
    for _ in range(7):
        mid = 0.5 * (lo + hi)
        sd = seed_fn(mid) if seed_fn else mkseed(60, R, int(mid * 1000))
        s = Sim(0.55, T, policy, R, sd)
        s.run(t_push, event_cap=2_000_000)
        s.lam = mid
        s.run(s.now + t_hold, event_cap=2_000_000)
        recovered = (s.inflight < 50) and (len(s.queue) < 10)
        if recovered:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


rec_law = {}
for R in [4, 6, 10]:
    vals = [recovery_threshold(R, seed_fn=lambda m, R=R, k=k:
                                mkseed(60, R, int(m * 1000), k))
            for k in range(2)]
    rec_law[R] = {'lam_r_mean': st.mean(vals), 'lam_r_seeds': vals,
                  'pred': 1.0 / R}
    print(f"  R={R}: watchable recovery {st.mean(vals):.3f} "
          f"(sustaining boundary 1/R = {1.0/R:.3f})", flush=True)

drain_times = {}
for lam in [0.05, 0.1]:
    s = Sim(0.55, 5.0, 'jitter', 6, mkseed(61, int(lam * 1000)))
    s.run(700, event_cap=2_000_000)
    s.lam = lam
    t0 = s.now
    tr = None
    for _ in range(12):
        s.run(s.now + 500, event_cap=2_000_000)
        if s.inflight < 50 and len(s.queue) < 10:
            tr = s.now - t0
            break
    drain_times[lam] = tr
    print(f'  drain at lam={lam}: {tr}', flush=True)

# R = infinity: after a DEEP collapse, the state never drains by shedding
r_inf = {}
for Rv, rlab in [(6, '6'), (10**9, 'inf')]:
    s = Sim(0.9, 5.0, 'jitter', Rv, mkseed(62, rlab))
    s.run(400, event_cap=2_000_000)
    depth = len(s.queue)
    s.lam = 0.05
    s.run(s.now + 3000, event_cap=2_000_000)
    r_inf[rlab] = {'drained': s.inflight < 50 and len(s.queue) < 10,
                   'inflight_at_end': s.inflight,
                   'queue_at_end': len(s.queue), 'depth_at_shed': depth,
                   'dwell': 3000.0}
    print(f"  R={rlab}: depth {depth} at shed; after 3000 dwell "
          f"queue={len(s.queue)}, inflight={s.inflight} "
          f"(drained={r_inf[rlab]['drained']})", flush=True)

rec_law['drain_times'] = drain_times
rec_law['R_inf_trap'] = r_inf
hyst['recovery_law'] = {str(k): v for k, v in rec_law.items()}
RESULTS['f3'] = hyst

fig, (ax, axr) = plt.subplots(1, 2, figsize=(9.6, 4.4), constrained_layout=True)
cols = [G700, CB[1], CB[3], CB[2]]
for col, pol in zip(cols, policies):
    h = hyst[pol]
    up = [(x, y) for x, y, p in zip(h['lam'], h['rate'], h['phase']) if p == 'up']
    dn = [(x, y) for x, y, p in zip(h['lam'], h['rate'], h['phase']) if p == 'down']
    ax.plot([x for x, _ in up], [y for _, y in up], 'o-', ms=4, lw=1.6,
            color=col, label=f'{pol} (ramp up)')
    ax.plot([x for x, _ in dn], [y for _, y in dn], 's--', ms=4, lw=1.4,
            color=col, alpha=0.65, label=f'{pol} (ramp down)')
ax.set_xlabel('arrival load $\\lambda$ (per unit $\\mu$)')
ax.set_ylabel('job success rate')
ax.set_title('Collapse on the way up; no recovery in-dwell')
ax.axhline(0.5, color=G400, ls=':', lw=1.1)
ax.legend(loc='lower left', fontsize=7.2, ncol=2)
clean_axis(ax)

xs = [rec_law[R]['pred'] for R in [4, 6, 10]]
ys = [rec_law[R]['lam_r_mean'] for R in [4, 6, 10]]
axr.plot([0, 0.3], [0, 0.3], '--', color=G400, lw=1.2,
         label='sustaining boundary $\\lambda_r = 1/R$')
axr.plot(xs, ys, 'o', ms=9, color=CB[0], label='watchable recovery (2 seeds)')
for R, x, y in zip([4, 6, 10], xs, ys):
    axr.annotate(f'R={R}', (x, y), xytext=(6, 2), textcoords='offset points',
                 fontsize=9, color=G700)
axr.plot([0.0], [0.0], '*', ms=15, color=CB[4], zorder=5)
axr.annotate('R=$\\infty$: queue GROWS at 5% load\n(49k deep; restart only)',
             (0.145, 0.052), fontsize=8.5, color=CB[4], va='center')
axr.set_xlabel('sustaining boundary $\\mu/R$')
axr.set_ylabel('measured recovery-within-dwell')
dt = ', '.join(f"{v:.0f}" if v else "n/a" for v in drain_times.values())
axr.set_title(f'The give-up law (drain at 0.05: {dt} $\\tau$)')
axr.legend(loc='upper left', fontsize=8.6)
clean_axis(axr)
save(fig, 'f3-hysteresis.png')

# ============================================================================
# E4/F4 — policy margins (mean backoff measured, not assumed)
# ============================================================================
print('F4: policy margins', flush=True)
bmean = {}
for pol in policies_grid:
    s = Sim(0.30, 5.0, pol, 6, mkseed(41, pol))
    s.run(400.0, event_cap=300_000)
    bmean[pol] = s.backoff_sum / max(1, s.backoff_n)
    print(f"  mean backoff {pol}: {bmean[pol]:.2f} service-times", flush=True)
RESULTS['f4_backoff_mean'] = bmean

margins = {}
for (th, pol), mb in grid_meas.items():
    c = lambda_c_closed(th)
    ratios = [v / c for v in mb['vals']]
    margins[f'{th:.0f}|{pol}'] = {
        'ratio_mean': st.mean(ratios),
        'ratio_sd': st.stdev(ratios) if len(ratios) > 1 else 0.0,
        'ceiling': c}
RESULTS['f4_margins'] = margins

fig, ax = plt.subplots(figsize=(9.6, 4.4), constrained_layout=True)
w = 0.2
xpos = np.arange(len(policies_grid))
for i, th in enumerate(thetas):
    ys = [margins[f'{th:.0f}|{p}']['ratio_mean'] for p in policies_grid]
    ye = [margins[f'{th:.0f}|{p}']['ratio_sd'] for p in policies_grid]
    ax.bar(xpos + (i - 1) * w, ys, w, yerr=ye, capsize=3,
           color=[CB[1], CB[0], CB[3]][i], alpha=0.85,
           label=f'$\\theta = {th:.0f}$', error_kw=dict(elinewidth=1.2))
ax.axhline(1.0, color=G400, ls='--', lw=1.2)
ax.annotate('ceiling', (len(policies_grid) - 0.5, 1.02), fontsize=9,
            color=G700)
ax.set_xticks(xpos)
ax.set_xticklabels([f"{p}\n$\\bar B$={bmean[p]:.1f}" for p in policies_grid])
ax.set_ylabel('collapse margin $\\hat\\lambda_c / \\lambda_c$')
ax.set_title('Policy margins (mean of 5-8 seeds, +/- 1 sd)')
ax.legend(loc='upper left', fontsize=9)
clean_axis(ax)
save(fig, 'f4-policy-margins.png')

# ============================================================================
# E5/F5 — interventions: queue caps (goodput curves), timeout sweep
# ============================================================================
print('F5: interventions', flush=True)
# goodput-vs-load curves for capped and uncapped systems
cap_curve = {}
for L in [2, 5, 10, None]:
    rows = []
    for lam in np.arange(0.3, 1.35, 0.1):
        gps, bfs, rfs, amps, qfs = [], [], [], [], []
        for sd in range(2):
            s = Sim(float(lam), 5.0, 'jitter', 6, mkseed(51, str(L),
                                                          int(lam * 10), sd),
                    qcap=L)
            win = s.run_window(90 * 6 + 150, warm_frac=0.78)
            gps.append(win['goodput_ratio'])
            bfs.append(win['busy_frac'])
            rfs.append(win['rej'] / max(1, win['att']))
            amps.append(win['amplification'] if win['succ'] > 0 else 10.0)
            qfs.append(win['q_frac'])
        rows.append({'lam': float(lam), 'gp': st.mean(gps), 'busy': st.mean(bfs),
                     'rej': st.mean(rfs), 'amp': st.mean(amps),
                     'q': st.mean(qfs)})
    cap_curve[str(L)] = rows
    print(f"  L={L}: " + ' '.join(f"{r['lam']:.1f}:{r['gp']:.2f}" for r in rows),
          flush=True)
RESULTS['f5_cap_curve'] = cap_curve

# thresholds: goodput-80 and crater, per cap
cap_thr = {}
for L in [2, 5, 10, None]:
    seeds = [mkseed(52, str(L), k) for k in range(3)]
    g80 = multi_bisect(5.0, 'jitter', 6, seeds, qcap=L, criterion='g80')
    seeds2 = [mkseed(53, str(L), k) for k in range(3)]
    cr = multi_bisect(5.0, 'jitter', 6, seeds2, qcap=L, criterion='crater',
                      hi=1.4)
    cap_thr[str(L)] = {'g80': g80, 'crater': cr}
    print(f"  L={L}: g80 {g80['mean']:.3f}, crater {cr['mean']:.3f}", flush=True)
RESULTS['f5_cap_thresholds'] = cap_thr

# timeout sweep with the SAME protocol as everything else
to_curve = []
for th in [1.0, 2.0, 5.0, 10.0, 20.0]:
    seeds = [mkseed(55, int(th), k) for k in range(3)]
    mb = multi_bisect(th, 'jitter', 6, seeds, steps=9, horizon_mult=90)
    to_curve.append({'theta': th, 'mean': mb['mean'], 'sd': mb['sd'],
                     'theory': lambda_c_closed(th),
                     'relerr': (mb['mean'] - lambda_c_closed(th)) /
                     lambda_c_closed(th)})
    print(f"  theta={th:.0f}: meas {mb['mean']:.3f} +/- {mb['sd']:.3f} "
          f"theory {lambda_c_closed(th):.3f} relerr "
          f"{to_curve[-1]['relerr']:+.1%}", flush=True)
RESULTS['f5_timeout_curve'] = to_curve

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
lg = np.linspace(0.28, 1.34, 100)
axa.plot(lg, np.minimum(1.0, 1.0 / lg), '--', color=G400, lw=1.4,
         label='perfect shedder $\\min(\\lambda,\\mu)/\\lambda$')
for L, col, mk in [(2, CB[2], 'o'), (5, CB[3], 'D'), (10, CB[1], '^'),
                        (None, CB[4], 's')]:
    rows = cap_curve[str(L)]
    axa.plot([r['lam'] for r in rows], [r['gp'] for r in rows], mk + '-',
             ms=5, lw=1.5, color=col, label=f'cap $L$ = {L}')
axa.axhline(0.8, color=G400, ls=':', lw=1.1)
axa.axhline(0.3, color=G400, ls=':', lw=1.1)
axa.annotate('goodput-80 line', (0.32, 0.815), fontsize=8, color=G700)
axa.annotate('crater line', (0.32, 0.315), fontsize=8, color=G700)
axa.set_xlabel('arrival load $\\lambda$ (per unit $\\mu$)')
axa.set_ylabel('goodput ratio (completions / arrivals)')
axa.set_title('Queue caps: graceful vs crater ($\\theta=5$, jitter)')
axa.legend(loc='upper right', fontsize=8.6)
clean_axis(axa)

thx = [t['theta'] for t in to_curve]
thy = [t['mean'] for t in to_curve]
the = [t['sd'] for t in to_curve]
axb.errorbar(thx, thy, yerr=the, fmt='o', ms=8, mfc='none', mec=CB[2],
             mew=1.8, elinewidth=1.3, capsize=3, ls='none',
             label='measured (3 seeds)')
axb.plot(th_c, [lambda_c_closed(t) for t in th_c], '-', color=CB[0], lw=2.0,
         label='ceiling $\\lambda_c(\\theta)$')
for t in to_curve:
    axb.annotate(f"{t['relerr']:+.0%}", (t['theta'], t['mean']),
                 xytext=(4, -14), textcoords='offset points', fontsize=8.5,
                 color=G700)
axb.set_xscale('log')
axb.set_xlabel('timeout slack $\\theta = \\mu T$ (log)')
axb.set_ylabel('collapse load (per unit $\\mu$)')
axb.set_title('The ceiling vs measured collapse loads')
axb.legend(loc='upper left', fontsize=8.8)
clean_axis(axb)
save(fig, 'f5-interventions.png')

# ============================================================================
# E6/F6 — law validation scatter (fixed points + R-shift)
# ============================================================================
print('F6: validation scatter', flush=True)
fig, ax = plt.subplots(figsize=(6.4, 5.2), constrained_layout=True)
lims = [0.0, 0.6]
ax.plot(lims, lims, '--', color=G400, lw=1.2, label='$y = x$')
px = [p['rho_pred'] for p in ok]
py = [p['rho_mean'] for p in ok]
ax.plot(px, py, 's', ms=8, mfc='none', mec=CB[0], mew=1.6, ls='none',
        label='fixed points, $\\theta=5$, $R=6$')
ax.annotate(f'fixed points: median rel err '
            f'{RESULTS["f1_fixedpoint_median_relerr"]:.1%}',
            (0.03, 0.55), xycoords='axes fraction', fontsize=8.5, color=G700)
ax.set_xlabel('predicted utilization $\\rho$ (root of $g_R$)')
ax.set_ylabel('measured utilization (busy fraction, 8 seeds)')
ax.set_title('The fixed-point law')
ax.legend(loc='lower right', fontsize=8.8)
clean_axis(ax)
save(fig, 'f6-law-validation.png')

# ============================================================================
# E7/F7 — the unified finite-R curve: R-shift, R-sweep, fold boundary
# ============================================================================
print('F7: the unified curve', flush=True)
# (a) R-shift of the fixed point at theta=2, lambda=0.28.
# 'none' = instant re-offer, the fluid curve's own assumption: R=1,2 sit on
# the roots; R>=4 with instant re-offer is the resonance regime (tips).
# 'jitter' rows measure the deployment gap (throttled amplification).
rshift = []
for pol_rs, Rn, Rlab in [('none', 1, '1'), ('none', 2, '2'),
                         ('jitter', 1, '1j'), ('jitter', 2, '2j'),
                         ('jitter', 4, '4j'), ('jitter', None, 'infj')]:
    Rsim = Rn if Rn is not None else 10**9
    Rroot = Rn  # root of g_R
    rhos, tipped = [], 0
    for sd in range(8):
        s = Sim(0.28, 2.0, pol_rs, Rsim, mkseed(71, Rlab, sd))
        win = s.run_window(1000.0, warm_frac=0.5, event_cap=2_000_000)
        rts = roots_of_lam(0.28, 2.0, Rroot)
        pred = min(rts) if rts else float('nan')
        if win['collapsed_flag'] or win['busy_frac'] > pred + 0.25:
            tipped += 1
        else:
            rhos.append(win['busy_frac'])
    rshift.append({'policy': pol_rs, 'R': str(Rn) if Rn is not None else 'inf',
                   'rho_mean': st.mean(rhos) if rhos else None,
                   'rho_sd': st.stdev(rhos) if len(rhos) > 1 else 0.0,
                   'rho_pred': pred, 'tipped': tipped})
    print(f"  R-shift {pol_rs} R={rshift[-1]['R']}: rho_meas "
          f"{rshift[-1]['rho_mean']} pred {pred:.3f} tipped {tipped}/8",
          flush=True)
RESULTS['f7_rshift'] = rshift

# (b) R-sweep of collapse loads at theta=2 (+ theta=5, R=2)
rsweep = []
for th, Rn in [(2.0, 2), (2.0, 4), (2.0, 8), (5.0, 2)]:
    seeds = [mkseed(72, int(th), Rn, k) for k in range(3)]
    mb = multi_bisect(th, 'jitter', Rn, seeds, steps=9, horizon_mult=90)
    cR, rR = ceiling_R(th, Rn)
    rsweep.append({'theta': th, 'R': Rn, 'meas': mb['mean'], 'sd': mb['sd'],
                   'ceiling_R': cR, 'rho_star_R': rR, 'endpoint': 1.0 / Rn})
    print(f"  R-sweep theta={th:.0f} R={Rn}: meas {mb['mean']:.3f} "
          f"+/- {mb['sd']:.3f}, ceiling(R) {cR:.3f}, endpoint {1.0/Rn:.3f}",
          flush=True)
RESULTS['f7_rsweep'] = rsweep

# (c) R=2 at theta=2: empty hysteresis band (collapse ~ recovery ~ 0.5)
r2c = multi_bisect(2.0, 'jitter', 2, [mkseed(73, k) for k in range(3)],
                   steps=9, horizon_mult=90)
r2r_seeds = [recovery_threshold(2, T=2.0, lo=0.02, hi=0.75,
                                seed_fn=lambda m, k=k: mkseed(74, int(m*100), k))
             for k in range(2)]
r2_band = {'theta': 2.0, 'R': 2, 'collapse_g80': r2c['mean'],
           'collapse_sd': r2c['sd'],
           'recovery_mean': st.mean(r2r_seeds),
           'recovery_seeds': r2r_seeds,
           'ceiling_R': ceiling_R(2.0, 2)[0], 'endpoint': 0.5}
RESULTS['f7_r2_band'] = r2_band
print(f"  R=2, theta=2: collapse {r2c['mean']:.3f}, recovery "
      f"{st.mean(r2r_seeds):.3f} -> band empty "
      f"(ceiling=endpoint={r2_band['ceiling_R']:.3f})", flush=True)

# (d) fold-existence scan: bistability iff (R-1) theta > 2
fold_scan = []
for th in np.arange(0.25, 6.01, 0.25):
    for Rn in range(1, 13):
        cR, rr = ceiling_R(float(th), Rn)
        fold = cR > 1.0 / Rn + 1e-9
        fold_scan.append({'theta': float(th), 'R': Rn, 'fold': bool(fold),
                          'pred': (Rn - 1) * th > 2})
agree = sum(1 for f in fold_scan if f['fold'] == f['pred'])
RESULTS['f7_fold_scan'] = {'n': len(fold_scan), 'agree': agree,
                           'boundary': '(R-1)*theta = 2'}
print(f"  fold boundary (R-1)theta=2: {agree}/{len(fold_scan)} grid points "
      f"agree", flush=True)
# strict boundary: find where they disagree, if any
dis = [(f['theta'], f['R']) for f in fold_scan if f['fold'] != f['pred']]
if dis:
    print(f"  disagreements (theta, R): {dis[:10]}", flush=True)

# theory table for the paper
theory_tbl = []
for th in [2.0, 5.0, 20.0]:
    row = {'theta': th}
    for Rn in [1, 2, 4, 6, 10, None]:
        cR, rr = ceiling_R(th, Rn)
        row[str(Rn) if Rn else 'inf'] = (round(cR, 4), round(rr, 3),
                                          round(1.0 if Rn == 1 else
                                                (1.0 / Rn if Rn else 0.0), 4))
    theory_tbl.append(row)
RESULTS['f7_theory'] = theory_tbl

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.4), constrained_layout=True)
rhos = np.linspace(0.02, 0.999, 400)
for Rn, col in [(2, CB[4]), (4, CB[3]), (6, CB[1]), (10, CB[0]),
                (None, G900)]:
    axa.plot(g_of_rho(rhos, 5.0, Rn), rhos, '-', lw=1.8, color=col,
             label=f'$R = {"\\infty" if Rn is None else Rn}$')
    cR, rr = ceiling_R(5.0, Rn)
    axa.plot([cR], [rr], 'o', ms=7, mfc='white', mec=col, mew=1.8, zorder=5)
    axa.plot([1.0 / Rn if Rn else 0.0], [1.0], 'x', ms=8, mec=col, mew=2.0,
             zorder=5)
axa.plot([], [], 'o', ms=7, mfc='white', mec=G700, mew=1.8,
         label='ceiling $=\\max g_R$')
axa.plot([], [], 'x', ms=8, mec=G700, mew=2.0, ls='none',
         label='endpoint $= 1/R$')
axa.set_xlabel('load $\\lambda/\\mu$')
axa.set_ylabel('utilization $\\rho$')
axa.set_title('One curve, two thresholds ($\\theta = 5$)')
axa.set_xlim(0, 0.68)
axa.legend(loc='lower right', fontsize=8.4)
clean_axis(axa)

rx = [r['R'] for r in rsweep if r['theta'] == 2.0]
ry = [r['meas'] for r in rsweep if r['theta'] == 2.0]
re_ = [r['sd'] for r in rsweep if r['theta'] == 2.0]
axb.errorbar(rx, ry, yerr=re_, fmt='o', ms=9, mfc='none', mec=CB[2],
             mew=1.8, elinewidth=1.3, capsize=4, ls='none',
             label='measured collapse load (3 seeds)')
# smooth ceiling curve (fractional R interpolated between integer grids)
Rgrid = np.linspace(1.05, 8.0, 300)
cvals = []
for Rf in Rgrid:
    grid = np.linspace(1e-4, 1.0 - 1e-9, 20001)
    g = g_of_rho(grid, 2.0, None) if Rf > 1e6 else \
        g_of_rho(grid, 2.0, int(Rf)) if abs(Rf - round(Rf)) < 1e-9 else None
    if g is None:
        # fractional R: interpolate between floor and ceil
        lo, hi = int(Rf), int(Rf) + 1
        wgt = Rf - lo
        glo = g_of_rho(grid, 2.0, lo)
        ghi = g_of_rho(grid, 2.0, hi)
        gg = (1 - wgt) * glo + wgt * ghi
        cvals.append(float(gg.max()))
    else:
        cvals.append(float(g.max()))
axb.plot(Rgrid, cvals, '-', color=CB[0], lw=2.0,
         label='ceiling $\\lambda_c(R)$, $\\theta=2$')
axb.plot(Rgrid, 1.0 / Rgrid, '--', color=CB[4], lw=1.6,
         label='recovery endpoint $1/R$')
axb.set_xlabel('retry budget $R$')
axb.set_ylabel('load (per unit $\\mu$)')
axb.set_title('The $R$-sweep at $\\theta = 2$')
axb.annotate('band between the lines = hysteresis', (6.15, 0.045),
             fontsize=8.5, color=G700, va='bottom')
axb.legend(loc='upper right', fontsize=8.6)
clean_axis(axb)
save(fig, 'f7-unified-curve.png')

# ============================================================================
# dump + summary
# ============================================================================
with open(os.path.join(OUT, 'results.json'), 'w') as fh:
    json.dump(RESULTS, fh, indent=1, default=float)
print('\nresults.json written to', os.path.join(OUT, 'results.json'))

print('\n================= SUMMARY FOR THE PAPER =================')
print(f"kernel median rel err:      {RESULTS['f1_kernel_median_relerr']:.3f}")
print(f"fixed point median rel err: {RESULTS['f1_fixedpoint_median_relerr']:.3f}"
      f"  (n={RESULTS['f1_fixedpoint_n']})")
for k, v in RESULTS['f2_grid'].items():
    th, pol = k.split('|')
    print(f"grid {k}: {v['mean']:.3f}+/-{v['sd']:.3f} "
          f"[{v['min']:.3f},{v['max']:.3f}] / ceiling "
          f"{lambda_c_closed(float(th)):.3f}")
for d in drift:
    print(f"drift hm={d['hm']}: {d['mean']:.3f}+/-{d['sd']:.3f}")
for k, v in cap_thr.items():
    print(f"cap L={k}: g80 {v['g80']['mean']:.3f}, crater {v['crater']['mean']:.3f}")
for t in to_curve:
    print(f"sweep theta={t['theta']:.0f}: {t['mean']:.3f}+/-{t['sd']:.3f} "
          f"relerr {t['relerr']:+.1%}")
for r in rshift:
    print(f"R-shift R={r['R']}: meas {r['rho_mean']} pred {r['rho_pred']:.3f}")
for r in rsweep:
    print(f"R-sweep th={r['theta']:.0f} R={r['R']}: meas {r['meas']:.3f} "
          f"ceiling {r['ceiling_R']:.3f}")
print(f"R=2 band @ theta=2: collapse {r2_band['collapse_g80']:.3f} recovery "
      f"{r2_band['recovery_mean']:.3f} ceiling=endpoint "
      f"{r2_band['ceiling_R']:.3f}")
print(f"fold boundary: {agree}/{len(fold_scan)} agree")
for k, curve in ptip.items():
    print(f"P-tip theta={k}: " + ' '.join(f"{c['lam']:.2f}:{c['p']:.2f}"
                                          for c in curve))
print(f"R=inf trap: {RESULTS['f3']['recovery_law']['R_inf_trap']}")
