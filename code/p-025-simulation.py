#!/usr/bin/env python3
"""P-025 simulation: the collapse law for timeout-retry systems.

Model: single FCFS server (rate mu), Poisson client arrivals (rate lambda),
per-attempt client timeout T, retry after policy backoff, give-up after R
attempts. Timed-out work is still served (wasted) — the retry amplification
loop that drives congestion collapse.

Mean-field law under test (instantaneous re-offer, no give-up):
    steady state:  lambda = mu * rho * (1 - q(rho)),   q = e^{-mu(1-rho)T}
    tangency:      mu*T*(1-rho*) = ln(1 + mu*T*rho*)
    collapse load: lambda_c = mu * theta * rho*^2 / (1 + theta*rho*),
                   theta = mu*T

Experiments (mu = 1 throughout):
  f1-fixed-point.png     measured steady rho on the good branch vs the
                         lambda(rho) curve; q(rho) validation inset
  f2-collapse-law.png    measured collapse threshold vs the closed form,
                         duration drift + separatrix depth check
  f3-hysteresis.png      ramp-up/ramp-down success loops, 4 policies
  f4-policy-margins.png  collapse threshold per policy (margin over worst
                         case), mean backoff overlay
  f5-interventions.png   queue-cap admission control; timeout scaling vs law
  f6-law-validation.png  prediction vs measurement across all configs

Writes results.json with every headline number cited in the paper.
"""
import heapq
import json
import math
import os
import random
from collections import deque

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'figures', 'p-025')
os.makedirs(OUT, exist_ok=True)

SEED = 20261007
RESULTS = {}

def mkseed(*parts):
    """Deterministic int seed from heterogeneous parts."""
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


# ════════════════════════════════════════════════════════════════════════════
# Closed-form pieces
# ════════════════════════════════════════════════════════════════════════════

def rho_star(theta):
    """Newton on theta(1-rho) = ln(1+theta rho)."""
    r = 0.85
    for _ in range(60):
        g = theta * (1 - r) - math.log(1 + theta * r)
        gp = -theta - theta / (1 + theta * r)
        r -= g / gp
        r = min(max(r, 1e-9), 1 - 1e-9)
    return r


def lambda_c_closed(theta):
    r = rho_star(theta)
    return theta * r * r / (1 + theta * r)


def lam_of_rho(rho, theta):
    return rho * (1 - np.exp(-theta * (1 - rho)))


def roots_of_lam(lam, theta):
    """Both fixed points of lambda = rho(1-q) for lam < lambda_c."""
    xs = np.linspace(0.001, 0.999, 2000)
    ys = lam_of_rho(xs, theta) - lam
    sign = np.sign(ys)
    roots = []
    for i in range(len(xs) - 1):
        if sign[i] != sign[i + 1] and sign[i] * sign[i + 1] <= 0:
            a, b = xs[i], xs[i + 1]
            for _ in range(50):
                m = 0.5 * (a + b)
                if (lam_of_rho(a, theta) - lam) * (lam_of_rho(m, theta) - lam) <= 0:
                    b = m
                else:
                    a = m
            roots.append(0.5 * (a + b))
    return roots


# ════════════════════════════════════════════════════════════════════════════
# Discrete-event simulator
# ════════════════════════════════════════════════════════════════════════════

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


class Sim:
    """Single-server FCFS queue with client timeouts, retries, give-ups."""

    def __init__(self, lam, T, policy, R, seed, qcap=None, preload=0):
        self.lam, self.T, self.policy, self.R = lam, T, policy, R
        self.qcap = qcap
        self.rng = random.Random(seed)
        self.heap = []
        self.seq = 0
        self.queue = deque()
        self.server_busy = False
        self.now = 0.0
        # metrics
        self.successes = 0
        self.giveups = 0
        self.arrivals = 0
        self.attempts = 0
        self.busy_time = 0.0
        self.inflight = 0
        self.backoff_sum = 0.0
        self.backoff_n = 0
        self.wasted = 0
        self.sojourns = []          # successful attempts: response time
        self.events = 0
        self.preload = preload
        self.arr_seeded = False
        # time-series buckets
        self.ts_t, self.ts_inflight, self.ts_succ = [], [], []
        self._succ_window = []
        self.collapsed_flag = False
        # preload: fill the queue with fresh attempts (separatrix probing)
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
            # fast reject: client sees an error now, backs off, loses an attempt
            job['left'] -= 1
            if job['left'] > 0:
                b = backoff(self.policy, job['tries'], self.T, self.rng)
                self.backoff_sum += b
                self.backoff_n += 1
                self.push(self.now + b, 'retry', job)
            else:
                self.giveups += 1
                self.inflight -= 1
            return
        job['tries'] += 1
        job['last_aid'] = aid
        self.queue.append((aid, job))
        self.push(self.now + self.T, 'to', (aid, job))
        self._maybe_start_service()

    def _maybe_start_service(self):
        if not self.server_busy and self.queue:
            self.server_busy = True
            aid, job = self.queue.popleft()
            self.push(self.now + self.rng.expovariate(1.0), 'done', (aid, job))

    def _next_service(self):
        if self.queue:
            aid, job = self.queue.popleft()
            self.push(self.now + self.rng.expovariate(1.0), 'done', (aid, job))
        else:
            self.server_busy = False

    def run(self, horizon, event_cap=500_000, inflight_cap=4000):
        # seed the arrival chain exactly once (absolute time is only valid
        # on the first call; later calls resume the pending chain)
        if not self.arr_seeded:
            self.arr_seeded = True
            self.push(self.rng.expovariate(self.lam), 'arr', None)
        while self.heap and self.events < event_cap:
            evt = heapq.heappop(self.heap)
            if evt[0] > horizon:
                heapq.heappush(self.heap, evt)   # keep for a later run() call
                break
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
                aid, job = payload
                if self.server_busy:
                    self._next_service()
                if aid == job['last_aid'] and job['left'] > 0 and \
                        aid not in job['timed_out']:
                    # response arrived before the client's timeout
                    self.successes += 1
                    self.inflight -= 1
                    self.sojourns.append(self.now - job.get('send', self.now))
                    job['left'] = -10**9
                else:
                    self.wasted += 1
                self.busy_time += 0.0
        return self

    def stats(self, window_frac=0.25):
        W = self.now * window_frac
        succ_rate = self.successes / max(1e-9, self.now * window_frac) \
            if self.now > 0 else 0.0
        rho = 1.0 if self.collapsed_flag else None
        return {
            'successes': self.successes,
            'giveups': self.giveups,
            'arrivals': self.arrivals,
            'attempts': self.attempts,
            'inflight': self.inflight,
            'events': self.events,
            'collapsed_flag': self.collapsed_flag,
            'succ_rate_total': self.successes / max(1, self.arrivals),
            'mean_backoff': (self.backoff_sum / self.backoff_n)
                            if self.backoff_n else 0.0,
            'wasted_work_frac': self.wasted / max(1, self.attempts),
        }


def is_collapsed(sim, lam):
    """Legacy whole-run test (kept for the preload probe)."""
    if sim.collapsed_flag:
        return True
    if sim.arrivals < 10:
        return False
    if sim.successes < 0.8 * sim.arrivals:
        return True
    if sim.qcap is None and sim.now > 50:
        served = (sim.successes + sim.wasted) / max(1.0, sim.now)
        if served >= 0.95:
            return True
    return False


def run_and_classify(T, policy, R, seed, lam, horizon, qcap=None,
                     event_cap=500_000, preload=0):
    """Run warmup + final window; classify collapse on the final window only
    (whole-run averages dilute storms that develop late in the run)."""
    s = Sim(lam, T, policy, R, seed, qcap=qcap, preload=preload)
    s.run(0.78 * horizon, event_cap=event_cap)
    a0, sc0, w0 = s.arrivals, s.successes, s.wasted
    t0 = s.now
    s.run(horizon, event_cap=event_cap)
    dt = max(1e-9, s.now - t0)
    arr = s.arrivals - a0
    succ = s.successes - sc0
    served = succ + (s.wasted - w0)
    if s.collapsed_flag:
        return s, True
    if arr < 10:
        return s, False
    collapsed = succ < 0.8 * arr
    if not collapsed and qcap is None:
        collapsed = (served / dt) >= 0.95
    return s, collapsed


def bisect_lambda(T, policy, R, seed0, qcap=None, lo=0.05, hi=1.15,
                  steps=9, horizon_mult=60, event_cap=500_000):
    for _ in range(steps):
        mid = 0.5 * (lo + hi)
        horizon = horizon_mult * (T + 1) + 150
        s, coll = run_and_classify(T, policy, R, seed0, mid, horizon,
                                   qcap=qcap, event_cap=event_cap)
        if coll:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# ════════════════════════════════════════════════════════════════════════════
# F1 — the fixed-point curve, validated on the good branch
# ════════════════════════════════════════════════════════════════════════════

print('F1: fixed-point curve', flush=True)
theta = 5.0
T1 = theta
lcs = lambda_c_closed(theta)
lam_grid = np.round(np.linspace(0.15, 0.70 * lcs, 8), 3)
pts, f1_res = [], []
for lam in lam_grid:
    s = Sim(float(lam), T1, 'jitter', 10**9, mkseed(11, int(lam * 1000)))
    s.run(60 * T1 + 100, event_cap=300_000)
    rho_srv = (s.successes + s.wasted) / max(1.0, s.now)
    rate = s.successes / max(1, s.arrivals)
    tipped = (rate < 0.95) or s.collapsed_flag
    rts = roots_of_lam(float(lam), theta)
    rho_pred = min(rts) if rts else float('nan')
    pts.append((float(lam), rho_srv, not tipped))
    f1_res.append({'lam': float(lam), 'rho_srv': rho_srv,
                   'rho_pred': rho_pred, 'tipped': bool(tipped)})
    print(f'  lam={lam:.2f}: rho_srv={rho_srv:.3f} '
          f'(pred {rho_pred:.3f}){" TIPPED" if tipped else ""}', flush=True)
# q(rho) validation inset: no-retry runs
qpts = []
for lam in np.linspace(0.2, 0.9, 7):
    s = Sim(float(lam), T1, 'none', 1, mkseed(12, int(lam * 1000)))
    s.run(200 * T1, event_cap=200_000)
    done = s.successes + s.wasted
    if done > 100:
        qpts.append((float(lam), 1.0 - s.successes / done))
qpts = np.array(qpts)

RESULTS['f1'] = {'theta': theta, 'lambda_c_closed': lcs,
                 'points': [(a, b) for a, b, _ in pts],
                 'residuals': f1_res, 'q_points': qpts.tolist()}

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
rhos = np.linspace(0.02, 0.985, 300)
axa.plot(lam_of_rho(rhos, theta), rhos, '-', color=CB[0], lw=2.0,
         label='mean field $\\lambda(\\rho)$')
rs = rho_star(theta)
axa.plot([lcs], [rs], 'o', ms=9, color=CB[4], zorder=5)
axa.annotate('tangency\n$(\\lambda_c, \\rho^*)$', (lcs, rs), xytext=(-60, 16),
             textcoords='offset points', fontsize=9, color=CB[4],
             arrowprops=dict(arrowstyle='-', color=CB[4], lw=0.8))
px = [p[0] for p in pts if p[2]]
py = [p[1] for p in pts if p[2]]
axa.plot(px, py, 's', ms=6, mfc='none', mec=CB[2], mew=1.6,
         label='simulation (steady branch)')
axa.set_xlabel('offered load $\\lambda$ (per unit $\\mu$)')
axa.set_ylabel('server utilization $\\rho$')
axa.set_title(f'Fixed-point curve, $\\theta = \\mu T = {theta:.0f}$')
axa.legend(loc='lower right', fontsize=8.8)
clean_axis(axa)

rgrid = np.linspace(0.02, 0.95, 200)
axb.plot(rgrid, np.exp(-theta * (1 - rgrid)), '-', color=CB[0], lw=2.0,
         label='M/M/1: $q = e^{-\\mu(1-\\rho)T}$')
axb.plot(qpts[:, 0], qpts[:, 1], 's', ms=6, mfc='none', mec=CB[2], mew=1.6,
         label='simulation (no-retry runs)')
axb.set_xlabel('offered load $\\lambda$ (per unit $\\mu$)')
axb.set_ylabel('timeout fraction $q$')
axb.set_title('The timeout kernel')
axb.legend(loc='upper left', fontsize=8.8)
clean_axis(axb)
save(fig, 'f1-fixed-point.png')

# ════════════════════════════════════════════════════════════════════════════
# F2 — the collapse law: threshold, duration drift, separatrix
# ════════════════════════════════════════════════════════════════════════════

print('F2: the ceiling and how close each policy gets', flush=True)
thetas = [2.0, 5.0, 20.0]
policies_grid = ['none', 'fixed', 'exp', 'jitter']
grid_meas = {}
lawv = {th: lambda_c_closed(th) for th in thetas}
for th in thetas:
    for pol in policies_grid:
        grid_meas[(th, pol)] = bisect_lambda(
            th, pol, 6, mkseed(21, int(th), policies_grid.index(pol)),
            steps=8, horizon_mult=90)
    print(f'  theta={th:.0f} (ceiling {lawv[th]:.3f}): ' +
          ' '.join(f'{p}={grid_meas[(th, p)]:.3f}' for p in policies_grid),
          flush=True)

# duration drift at theta=5, jitter (metastable tipping evidence)
drift = []
for hm in [30, 60, 120]:
    lc = bisect_lambda(5.0, 'jitter', 6, mkseed(22, hm), horizon_mult=hm)
    drift.append((hm, lc))
    print(f'  horizon mult {hm}: lambda_c {lc:.3f}', flush=True)

# worst-case burst separatrix: preload N synchronized attempts (jitter)
lam_fix = 0.5 * lambda_c_closed(5.0)
rts = roots_of_lam(lam_fix, 5.0)
rho_b = max(rts) if rts else float('nan')
L_b = rho_b / (1 - rho_b)
lo, hi = 0, 80
for _ in range(8):
    mid = (lo + hi) // 2
    s = Sim(lam_fix, 5.0, 'jitter', 6, mkseed(23, int(mid)),
            preload=int(mid))
    s.run(40 * 5.0 + 100, event_cap=200_000)
    if is_collapsed(s, lam_fix):
        hi = mid
    else:
        lo = mid
Nb_meas = hi

RESULTS['f2'] = {
    'thetas': thetas, 'ceiling': {f'{t:.0f}': lawv[t] for t in thetas},
    'measured': {f'{t:.0f}|{p}': grid_meas[(t, p)]
                 for t in thetas for p in policies_grid},
    'approach': {f'{t:.0f}|{p}': grid_meas[(t, p)] / lawv[t]
                 for t in thetas for p in policies_grid},
    'drift': drift, 'lam_fix': lam_fix, 'rho_b': rho_b, 'L_b_theory': L_b,
    'N_b_measured': Nb_meas,
}
print(f'  burst separatrix: theory L(rho_b)={L_b:.1f}, '
      f'measured N_b={Nb_meas}', flush=True)

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
th_c = np.linspace(1.0, 40, 200)
axa.plot(th_c, [lambda_c_closed(t) for t in th_c], '-', color=CB[0], lw=2.0,
         label='ceiling $\\lambda_c = \\mu\\theta\\rho^{*2}/(1+\\theta\\rho^*)$')
cols = dict(zip(policies_grid, [G700, CB[1], CB[3], CB[2]]))
mks = dict(zip(policies_grid, ['v', '^', 'D', 'o']))
for pol in policies_grid:
    axa.plot(thetas, [grid_meas[(t, pol)] for t in thetas], mks[pol], ms=8,
             mfc='none', mec=cols[pol], mew=1.8, ls='none',
             label=f'{pol} retry')
axa.set_xlabel('timeout slack $\\theta = \\mu T$')
axa.set_ylabel('collapse load (per unit $\\mu$)')
axa.set_title('The ceiling and the policy approach')
axa.legend(loc='lower right', fontsize=8.6)
clean_axis(axa)

axb.plot([d[0] for d in drift], [d[1] for d in drift], 'o-', ms=6, lw=1.6,
         color=CB[0], label='measured $\\lambda_c(D)$ (jitter)')
axb.axhline(lawv[5.0], color=CB[4], ls='--', lw=1.5, label='ceiling')
axb.set_xscale('log')
axb.set_xlabel('simulation horizon multiplier $D/T$ (log)')
axb.set_ylabel('measured collapse load')
axb.set_title('Duration drift ($\\theta$=5, jitter)')
axb.legend(loc='lower right', fontsize=8.8)
clean_axis(axb)
save(fig, 'f2-collapse-law.png')


# ════════════════════════════════════════════════════════════════════════════
# F3 — hysteresis loops
# ════════════════════════════════════════════════════════════════════════════

print('F3: hysteresis', flush=True)
T3, R3 = 5.0, 6
policies = ['none', 'fixed', 'exp', 'jitter']


def ramp(policy, seed0, R=R3):
    """Sequential ramp with persistent state: lambda up then down."""
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

# the recovery law: lambda_r ~ mu / R. The give-up budget R sets the load
# the collapsed state can sustain on its own (offered ~ lam*R vs mu); below
# it the residual queue drains at rate (mu - lam*R), which takes time
# proportional to the storm depth — far longer than any practical dwell.
def recovery_threshold(R, T=5.0, policy='jitter', lo=0.02, hi=0.45,
                       t_push=700.0, t_hold=2500.0):
    for _ in range(7):
        mid = 0.5 * (lo + hi)
        s = Sim(0.55, T, policy, R, mkseed(60, R, int(mid * 1000)))
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
    lam_r = recovery_threshold(R)
    rec_law[R] = {'lam_r': lam_r, 'pred': 1.0 / R}
    print(f'  R={R}: recovery threshold {lam_r:.3f} (law 1/R = {1.0/R:.3f})',
          flush=True)

# drain-time evidence at R=6: recovery takes ~ residual queue / (mu - lam R)
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
    print(f'  drain at lam={lam}: {tr} s', flush=True)
rec_law['drain_times'] = drain_times
hyst['recovery_law'] = {str(k): (v if isinstance(v, dict) else v)
                        for k, v in rec_law.items()}

RESULTS['f3'] = hyst

fig, (ax, axr) = plt.subplots(1, 2, figsize=(9.6, 4.4), constrained_layout=True)
cols = [G700, CB[1], CB[3], CB[2]]
for col, pol in zip(cols, policies):
    h = hyst[pol]
    up = [(x, y) for x, y, p in zip(h['lam'], h['rate'], h['phase'])
          if p == 'up']
    dn = [(x, y) for x, y, p in zip(h['lam'], h['rate'], h['phase'])
          if p == 'down']
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
ys = [rec_law[R]['lam_r'] for R in [4, 6, 10]]
axr.plot([0, 0.3], [0, 0.3], '--', color=G400, lw=1.2, label='law $\\lambda_r = 1/R$')
axr.plot(xs, ys, 'o', ms=9, color=CB[0])
for R, x, y in zip([4, 6, 10], xs, ys):
    axr.annotate(f'R={R}', (x, y), xytext=(6, 2), textcoords='offset points',
                 fontsize=9, color=G700)
dt = ', '.join(f'{v:.0f}s' if v else 'n/a'
               for v in rec_law['drain_times'].values())
axr.set_xlabel('give-up budget law $1/R$')
axr.set_ylabel('measured recovery load $\\lambda_r$')
axr.set_title(f'The recovery law (drain at 0.05: {dt})')
axr.legend(loc='upper left', fontsize=8.6)
clean_axis(axr)
save(fig, 'f3-hysteresis.png')

# ════════════════════════════════════════════════════════════════════════════
# F4 — policy margins
# ════════════════════════════════════════════════════════════════════════════

print('F4: policy margins', flush=True)
policies = policies_grid
Bbar = {}
for pol in policies:
    s = Sim(0.6 * lambda_c_closed(5.0), 5.0, pol, 6,
            mkseed(44, policies.index(pol)))
    s.run(30 * 5 + 60, event_cap=200_000)
    Bbar[pol] = s.stats()['mean_backoff']

RESULTS['f4'] = {
    'margins': {f'{t:.0f}|{p}': grid_meas[(t, p)] / lawv[t]
                for t in thetas for p in policies},
    'Bbar': Bbar,
}

fig, ax = plt.subplots(figsize=(6.8, 4.4), constrained_layout=True)
xpos = np.arange(len(policies))
w = 0.26
for i, th in enumerate(thetas):
    vals = [grid_meas[(th, p)] / lawv[th] for p in policies]
    ax.bar(xpos + (i - 1) * w, vals, width=w, color=CB[i],
           label=f'$\\theta$ = {th:.0f}', alpha=0.9)
    for x, v in zip(xpos + (i - 1) * w, vals):
        ax.text(x, v + 0.01, f'{v:.2f}', ha='center', fontsize=7.5, color=G700)
ax.axhline(1.0, color=G400, ls='--', lw=1.2)
ax.set_xticks(xpos)
ax.set_xticklabels([f'{p}\n($\\bar B$={Bbar[p]:.1f}$T$)' for p in policies],
                   fontsize=9)
ax.set_ylabel('collapse margin $\\lambda_c^{eff} / \\lambda_c$')
ax.set_title('Retry policies buy back collapse margin')
ax.legend(loc='upper left', fontsize=9)
clean_axis(ax)
save(fig, 'f4-policy-margins.png')


# ════════════════════════════════════════════════════════════════════════════
# F5 — interventions
# ════════════════════════════════════════════════════════════════════════════

print('F5: interventions', flush=True)
caps = [2, 5, 10, 20, None]
cap_curve = []
for L in caps:
    lc = bisect_lambda(5.0, 'jitter', 6, mkseed(5, str(L)), qcap=L, steps=7)
    cap_curve.append((L, lc))
    print(f'  queue cap {L}: lambda_c {lc:.3f}', flush=True)

Ts = [1.0, 2.0, 5.0, 10.0, 20.0]
to_curve = []
for t in Ts:
    lc = bisect_lambda(t, 'jitter', 6, mkseed(6, int(t)), steps=7)
    to_curve.append((t, lc))
    print(f'  T={t:.0f}: lambda_c {lc:.3f} (ceiling {lambda_c_closed(t):.3f})',
          flush=True)

RESULTS['f5'] = {'cap_curve': [(str(a), b) for a, b in cap_curve],
                 'timeout_curve': to_curve,
                 'ceiling_curve': [[t, lambda_c_closed(t)] for t in Ts]}

fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
xs = [i for i, _ in enumerate(caps)]
axa.plot(xs, [v for _, v in cap_curve], 'o-', ms=6, lw=1.8, color=CB[0])
axa.set_xticks(xs)
axa.set_xticklabels(['2', '5', '10', '20', '$\\infty$'])
axa.set_xlabel('queue-cap admission limit $L$ (in-system attempts)')
axa.set_ylabel('collapse load $\\lambda_c$')
axa.set_title('Admission control lifts the collapse load ($\\theta$=5)')
clean_axis(axa)

th_g = np.linspace(0.5, 30, 100)
axb.plot(th_g, [lambda_c_closed(t) for t in th_g], '-', color=CB[0], lw=2.0,
         label='ceiling (closed form)')
axb.plot([t for t, _ in to_curve], [v for _, v in to_curve], 's', ms=7,
         mfc='none', mec=CB[4], mew=1.8, label='measured (jitter retry)')
axb.set_xlabel('timeout slack $\\theta = \\mu T$')
axb.set_ylabel('collapse load $\\lambda_c$')
axb.set_title('Timeout scaling tracks the ceiling')
axb.legend(loc='lower right', fontsize=8.8)
clean_axis(axb)
save(fig, 'f5-interventions.png')


# ════════════════════════════════════════════════════════════════════════════
# F6 — law validation summary
# ════════════════════════════════════════════════════════════════════════════

print('F6: validation summary', flush=True)
predR, measR = [], []
for r in f1_res:
    if not r['tipped'] and not math.isnan(r['rho_pred']):
        predR.append(r['rho_pred'])
        measR.append(r['rho_srv'])
res = np.abs(np.array(measR) / np.array(predR) - 1.0) if predR else [0.0]
appr = {f'{t:.0f}|{p}': grid_meas[(t, p)] / lawv[t]
        for t in thetas for p in policies_grid}
RESULTS['f6'] = {
    'fixed_point_pred': predR, 'fixed_point_meas': measR,
    'fixed_point_median_rel_err': float(np.median(res)),
    'fixed_point_n': len(predR),
    'ceiling_approach': appr,
    'jitter_approach': {f'{t:.0f}': appr[f'{t:.0f}|jitter'] for t in thetas},
    'sync_gap': {f'{t:.0f}': appr[f'{t:.0f}|none'] for t in thetas},
}
ja = RESULTS['f6']['jitter_approach']
sg = RESULTS['f6']['sync_gap']
print(f'  fixed-point curve: median |err| {np.median(res):.3f} '
      f'({len(predR)} points)', flush=True)
print('  jitter/ceiling: ' + ' '.join(f'{k}:{v:.2f}' for k, v in ja.items()),
      flush=True)
print('  none/ceiling: ' + ' '.join(f'{k}:{v:.2f}' for k, v in sg.items()),
      flush=True)

fig, ax = plt.subplots(figsize=(5.6, 4.6), constrained_layout=True)
lim = [0, float(max(predR + measR)) * 1.15] if predR else [0, 1]
ax.plot(lim, lim, '--', color=G400, lw=1.2)
ax.plot(predR, measR, 'o', ms=8, color=CB[0])
ax.set_xlabel('mean-field prediction $\\rho_g$')
ax.set_ylabel('measured steady utilization')
ax.set_title('Fixed-point law: prediction vs measurement')
clean_axis(ax)
save(fig, 'f6-law-validation.png')


with open(os.path.join(OUT, 'results.json'), 'w') as f:
    json.dump(RESULTS, f, indent=1)
print('results.json written', flush=True)
print('DONE P-025')
