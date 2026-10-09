#!/usr/bin/env python3
"""P-027 law tests: automated checks of every mathematical claim (audit response).

An external verification audit (2026-10-10) found that the harness validated
the laws only in the regimes where they happen to hold and carried one real
reconstruction bug. This suite makes each claim a checked assertion,
including the regimes the audit showed to be delicate:

  T1   Cayley transport is exactly orthogonal          C^T C = I
  T2   Cayley transport is volume-free                 |det C| = 1
  T3   Damping is a contraction, UNCONDITIONALLY       |lambda_i| < 1 for any
       R PSD and any h -- including h*lam_max(R) > 2
  T4   Damping nonnegativity has a boundary            lambda_i >= 0 iff
       h*r_i <= 2; R = 4I, h = 1 gives lambda = -1/3 (the audit's case)
  T5   The guarded builder enforces the budget         h*lam_max(R) <= cap
       => spectrum in (0, 1) by construction
  T6   Cayley round-trip S -> C -> S                   (regression guard for
       the inverse-transform used by the explicit-Euler comparison)
  T7   Damping round-trip R -> Lambda -> R             (regression guard for
       the factor-of-two bug the audit caught in the old Rd reconstruction)
  T8   The exact input-bound law                        ||x_L|| <= ||x_0|| +
       sum_t h||B_t u_t|| with per-layer u_t (the audit showed the old
       check used ||u|| -- T8b shows that proxy is NOT the theorem)
  T9   Budget meter error is cubic in h                ratio -> 8 as h halves
  T10  Gradient non-amplification                       ||(Lambda C)^T g|| <=
       ||g|| for any g (max over trials)
  T11  Explicit-Euler and Cayley steps agree to first order (they
       discretize the same system): ||Lambda C - (I - S - hR)|| = O(eps^2)

Run: python3 code/p-027-tests.py   (exit 0 = all laws hold)
"""
import sys

import numpy as np

SEED = 20261009
rng = np.random.default_rng(SEED)
D = 24
FAILURES = []


def report(name, ok, detail):
    line = ('PASS' if ok else 'FAIL')
    print(f'  {line}  {name:52s} {detail}')
    if not ok:
        FAILURES.append(name)


def cayley_transport(A):
    S = A - A.T
    d = A.shape[0]
    return np.linalg.solve(np.eye(d) + 0.5 * S, np.eye(d) - 0.5 * S)


def cayley_dissipation(L, h):
    R = L @ L.T
    d = L.shape[0]
    return np.linalg.solve(np.eye(d) + 0.5 * h * R, np.eye(d) - 0.5 * h * R)


print('P-027 law test suite (audit response, seed %d)' % SEED)
print()

# T1 -- orthogonality -------------------------------------------------
err = 0.0
for _ in range(20):
    C = cayley_transport(rng.standard_normal((D, D)) * 2.0)
    err = max(err, np.abs(C.T @ C - np.eye(D)).max())
report('T1  Cayley transport orthogonal (C^T C = I)',
       err < 1e-12, 'max err %.2e' % err)

# T2 -- volume-freeness -----------------------------------------------
err = 0.0
for _ in range(20):
    C = cayley_transport(rng.standard_normal((D, D)) * 2.0)
    err = max(err, abs(abs(np.linalg.det(C)) - 1.0))
report('T2  Cayley transport volume-free (|det C| = 1)',
       err < 1e-12, 'max err %.2e' % err)

# T3 -- contraction is unconditional ----------------------------------
worst = 0.0
for h in (0.1, 1.0, 3.0, 10.0):
    for scale in (0.05, 0.5, 2.0, 5.0):
        L = scale * rng.standard_normal((D, D)) / np.sqrt(D)
        Lam = cayley_dissipation(L, h)
        worst = max(worst, np.abs(np.linalg.eigvalsh(Lam)).max())
report('T3  |lambda(Lambda)| < 1 for ANY R PSD, any h',
       worst < 1.0, 'max |lambda| %.6f' % worst)

# T4 -- nonnegativity boundary (the audit's counterexample) -----------
L = 2.0 * np.eye(D)          # R = 4I, h = 1 -> eigenvalues of Lambda = -1/3
Lam = cayley_dissipation(L, 1.0)
ev = np.linalg.eigvalsh(Lam)
ok = np.all(ev < 0) and abs(ev[0] + 1.0 / 3.0) < 1e-12 and np.all(np.abs(ev) < 1)
report('T4  h*r > 2 flips the sign (R=4I, h=1 -> -1/3)',
       ok, 'lambda range [%.4f, %.4f]' % (ev.min(), ev.max()))
ok = np.linalg.eigvalsh(cayley_dissipation(0.5 * np.eye(D), 1.0)).min() > 0
report('T4b h*r < 2 keeps lambda positive (R=I, h=1)',
       ok, 'min lambda %.4f' % np.linalg.eigvalsh(
           cayley_dissipation(0.5 * np.eye(D), 1.0)).min())

# T5 -- guarded builder ------------------------------------------------
CAP = 1.0
min_ev, max_ev = np.inf, -np.inf
for _ in range(50):
    h = 1.0
    L = rng.standard_normal((D, D)) * 1.5
    R = L @ L.T
    lam_max = np.linalg.eigvalsh(R)[-1]
    if h * lam_max > CAP:                       # the guard used by ph_layer
        L = L * np.sqrt(CAP / (h * lam_max))
    Lam = cayley_dissipation(L, h)
    ev = np.linalg.eigvalsh(Lam)
    min_ev = min(min_ev, ev.min())
    max_ev = max(max_ev, ev.max())
report('T5  guarded builder: spectrum in (0,1) by construction',
       min_ev > 0 and max_ev < 1, 'spectrum [%.4f, %.6f]' % (min_ev, max_ev))

# T6 -- Cayley round-trip S -> C -> S ----------------------------------
err = 0.0
for _ in range(20):
    S = rng.standard_normal((D, D))
    S = S - S.T
    C = cayley_transport(S + np.eye(D) * 0)     # cayley takes A, S = A - A^T
    # feed S directly: A with A - A^T = S requires A = S/2
    C = np.linalg.solve(np.eye(D) + 0.5 * S, np.eye(D) - 0.5 * S)
    S2 = 2.0 * np.linalg.solve(np.eye(D) + C, np.eye(D) - C)  # 2 (I-C)(I+C)^{-1}
    err = max(err, np.abs(S2 - S).max())
report('T6  round-trip S -> C -> S exact',
       err < 1e-10, 'max err %.2e' % err)

# T7 -- damping round-trip R -> Lambda -> R ----------------------------
err = 0.0
for _ in range(20):
    h = rng.uniform(0.05, 1.5)
    L = rng.standard_normal((D, D)) * rng.uniform(0.1, 0.8)
    R = L @ L.T
    Lam = cayley_dissipation(L, h)
    R2 = (2.0 / h) * np.linalg.solve(np.eye(D) + Lam, np.eye(D) - Lam)
    err = max(err, np.abs(R2 - R).max() / max(1.0, np.abs(R).max()))
report('T7  round-trip R -> Lambda -> R exact (old bug: R/2)',
       err < 1e-10, 'max rel err %.2e' % err)

# T8 -- the exact input-bound law --------------------------------------
T, n = 80, 64
h = 1.0
layers = []
for _ in range(T):
    A = rng.standard_normal((D, D))
    L = 0.3 * rng.standard_normal((D, D)) / np.sqrt(D)
    R = L @ L.T
    if h * np.linalg.eigvalsh(R)[-1] > CAP:
        L = L * np.sqrt(CAP / (h * np.linalg.eigvalsh(R)[-1]))
    layers.append((cayley_transport(A), cayley_dissipation(L, h),
                   rng.standard_normal((D, D)) / np.sqrt(D)))
x0 = rng.standard_normal((n, D)) / np.sqrt(D)
# per-layer DISTINCT inputs u_t (the theorem's general form)
Us = [rng.standard_normal((n, D)) * 0.05 / np.sqrt(D) for _ in range(T)]

X = x0.copy()
bound = np.linalg.norm(x0, axis=1).copy()      # EXACT: sum_t h ||B_t u_t||
for t, (C, Lam, B) in enumerate(layers):
    X = X @ C.T @ Lam + h * (Us[t] @ B.T)
    bound = bound + h * np.linalg.norm(Us[t] @ B.T, axis=1)
norms = np.linalg.norm(X, axis=1)
viol = int(np.sum(norms > bound + 1e-9))
report('T8  exact bound ||x_L|| <= ||x_0|| + sum h||B_t u_t||',
       viol == 0, 'violations %d, tightness %.3f' % (viol, float(np.median(norms / bound))))

# T8b -- the ||u|| proxy is NOT the theorem ---------------------------
Bbig = 6.0 * np.eye(D) / np.sqrt(D)             # amplifying port
u = np.ones((1, D)) / np.sqrt(D)
x = np.zeros((1, D))
x_exact = x @ (layers[0][0].T @ layers[0][1].T) + h * (u @ Bbig.T)
proxy_bound = np.linalg.norm(x, axis=1) + h * np.linalg.norm(u, axis=1)
exact_bound = np.linalg.norm(x, axis=1) + h * np.linalg.norm(u @ Bbig.T, axis=1)
ok = (np.linalg.norm(x_exact, axis=1) > proxy_bound).all() and \
     (np.linalg.norm(x_exact, axis=1) <= exact_bound + 1e-9).all()
report('T8b ||u|| proxy violated, ||B u|| bound holds',
       ok, 'proxy misses by %.1fx' % float(np.linalg.norm(x_exact, axis=1)[0] / proxy_bound[0]))

# T9 -- budget meter error is cubic in h -------------------------------
L = 0.35 * rng.standard_normal((D, D)) / np.sqrt(D)
R = L @ L.T
errs = {}
for h in (0.4, 0.2, 0.1, 0.05):
    Lam = cayley_dissipation(L, h)
    errs[h] = abs(np.log(np.linalg.det(Lam)) + h * np.trace(R))
r1 = errs[0.2] / errs[0.1]
r2 = errs[0.1] / errs[0.05]
report('T9  budget error cubic: ratio -> 8 as h halves',
       6.0 < r2 < 9.5, 'ratios %.2f, %.2f' % (r1, r2))

# T10 -- gradient non-amplification -----------------------------------
worst = 0.0
for _ in range(40):
    C = cayley_transport(rng.standard_normal((D, D)))
    L = 0.4 * rng.standard_normal((D, D)) / np.sqrt(D)
    Lam = cayley_dissipation(L, 1.0)
    g = rng.standard_normal((64, D))
    worst = max(worst, np.linalg.norm(g @ Lam @ C, axis=1).max()
                / np.linalg.norm(g, axis=1).max())
report('T10 ||(Lambda C)^T g|| <= ||g|| (40 trials)',
       worst <= 1.0 + 1e-12, 'max ratio %.10f' % worst)

# T11 -- explicit and Cayley steps agree to first order ---------------
S = rng.standard_normal((D, D))
S = S - S.T
L = 0.3 * rng.standard_normal((D, D)) / np.sqrt(D)
R = L @ L.T
h = 1.0
e1, e2 = None, None
for eps in (0.08, 0.04):
    Se, Re = eps * S, eps * R
    C = np.linalg.solve(np.eye(D) + 0.5 * Se, np.eye(D) - 0.5 * Se)
    Lam = np.linalg.solve(np.eye(D) + 0.5 * h * Re, np.eye(D) - 0.5 * h * Re)
    err = np.abs(Lam @ C - (np.eye(D) - Se - h * Re)).max()
    if e1 is None:
        e1 = err
    else:
        e2 = err
ratio = e1 / e2
report('T11 explicit vs Cayley steps agree to O(eps^2)',
       3.5 < ratio < 4.5, 'error ratio %.2f (quad = 4)' % ratio)

print()
if FAILURES:
    print('FAILED: %d law(s): %s' % (len(FAILURES), ', '.join(FAILURES)))
    sys.exit(1)
print('ALL 13 LAW CHECKS PASS')
