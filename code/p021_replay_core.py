"""Verbatim function copies from p-021-simulation.py (rev 1.1 replay)."""
import numpy as np

ARANGE = None

def build_ecosystem(N, gamma, kmax, rng):
    """Acyclic registry: node 0 oldest; edge (src -> dst) = 'src depends on
    dst', src younger. Infection flows dst -> src, so the infection matrix is
    strictly triangular (nilpotent: spectral radius exactly 0 — the spectral
    threshold is vacuous; see paper Proposition 1). Dependents counts drawn
    iid from P(k) ∝ k^-gamma (age-decoupled popularity), capped by the number
    of younger nodes."""
    global ARANGE
    if ARANGE is None or len(ARANGE) < N:
        ARANGE = np.arange(max(N, 2))
    ks = np.arange(1, kmax + 1)
    w = ks.astype(float) ** (-gamma)
    cdf = np.cumsum(w)
    cdf /= cdf[-1]
    kin = ks[np.searchsorted(cdf, rng.random(N))]
    avail = (N - 1) - np.arange(N)
    kin = np.minimum(kin, avail)
    src_parts, dst_parts = [], []
    for j in range(N - 1):
        k = int(kin[j])
        if k <= 0:
            continue
        k = min(k, N - 1 - j)
        sources = rng.choice(ARANGE[j + 1:N], size=k, replace=False)
        src_parts.append(sources)
        dst_parts.append(np.full(k, j, dtype=np.int64))
    if not src_parts:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    return np.concatenate(src_parts), np.concatenate(dst_parts)

def beta_from_T(T, gamma):
    """Per-step infectivity making T the EXACT per-edge eventual transmission
    probability under recovery-first discrete SIR with per-step recovery gamma:
    P(edge fires) = beta(1-gamma)/(gamma + beta(1-gamma))."""
    return T * gamma / ((1.0 - gamma) * (1.0 - T))

def run_sir(src, dst, N, beta, gamma, rng, seed=None, max_t=300,
            track=False, intervene=None):
    state = np.zeros(N, dtype=np.int8)   # 0=S 1=I 2=R
    if seed is None:
        seed = int(rng.integers(N))
    state[seed] = 1
    E = len(src)
    frozen = np.zeros(E, dtype=bool)
    It = [1]
    for t in range(max_t):
        if intervene is not None:
            if 'pin_at' in intervene and t == intervene['pin_at']:
                frozen |= (rng.random(E) < intervene.get('pin_edges_p', 0.2))
            if 'yank_at' in intervene and t == intervene['yank_at']:
                frozen |= (dst == seed)
            if 'gamma2_at' in intervene and t == intervene['gamma2_at']:
                gamma = gamma * 2.0
        inf = state == 1
        if inf.any():
            rec = rng.random(N) < gamma
            state[inf & rec] = 2
        m = (state[dst] == 1) & (state[src] == 0) & (~frozen)
        if m.any():
            u = rng.random(int(m.sum())) < beta
            new = src[m][u]
            if len(new):
                state[new] = 1
        It.append(int((state == 1).sum()))
        if not (state == 1).any():
            break
    attack = float((state != 0).sum()) / N
    return attack, (np.array(It) if track else None)

def outbreak_stats(src, dst, N, T, gamma, rng, seeds, takeoff=0.01):
    beta = beta_from_T(T, gamma)
    att, out = 0.0, 0
    for s in range(seeds):
        a, _ = run_sir(src, dst, N, beta, gamma, rng, max_t=400)
        att += a
        out += (a > takeoff)
    return att / seeds, out / seeds
