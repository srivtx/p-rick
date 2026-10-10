#!/usr/bin/env python3
"""P-027 E6: end-to-end training experiment (answers the external audit).

The audit's central criticism: "a formula can be mathematically valid, the
code can implement it correctly, and the proposed architecture can still
fail to train a useful neural network. Those are three different things."
The original L5 measured an in-sample nearest-centroid score on RANDOM
(untrained) streams -- representation retention, not learning. This
harness trains the architecture end-to-end and tests generalization.

Trainable instantiation (sanctioned by paper section 3.2 -- nonlinearity
lives in the ports): the port input is a saturating read of the state,

    z_{t+1} = Lambda_t C_t z_t + h B_t tanh(W_t z_t + b_t)

Lambda and C are Cayley-parameterized exactly as the paper specifies
(differentiable through one linear solve each), with the damping guard
h*lam_max(R) <= 1 enforced by construction. tanh saturates the port: the
conservation law degrades from "budget = sum ||B u_t||" to the
design-readable bound "budget = sum h ||B_t|| sqrt(d)", measured below.

Baselines (all trained, same protocol, same width d=32):
  resnet      z' = z + W2 tanh(W1 z + b1)          (standard PyTorch init)
  resnet-ln   z' = z + W2 tanh(LN(W1 z + b1))      (normalized control)
  cayley      z' = C z + W2 tanh(W1 z + b1)        (orthogonal transport)

Audit protocol, implemented exactly:
  * train / validation / test split (3600 / 1200 / 1200)
  * learning rate selected per (model, depth, seed) ON VALIDATION
  * early stopping on validation accuracy, best checkpoint restored
  * 3 seeds per configuration; mean +- std reported on TEST
  * per-layer backward gradient norms measured on the TRAINED model
  * forward activation-norm growth measured on the TRAINED model

Tasks: circles-4 (the paper's own rank-2 task, depths 30/120/240) and
spirals-2 (harder, depth 120). Adam + cosine decay, batch 256.

Outputs: figures/p-027/training-results.json (incremental, resumable)
         figures/p-027/f7-training.png
Run:     python3 code/p-027b-training.py [--smoke] [--device=auto|cpu|cuda]
         [--models=ph,resnet,resnet-ln,resnet-tln,cayley]

Models:  the default grid is the paper's four (ph, resnet, resnet-ln,
         cayley) and is run when the flag is absent -- the landed 96-run
         results stay byte-identical. resnet-tln is the rev-1.2 follow-up
         ablation (paper Sections 4.6/8): a TRUNK-normalized (post-LN)
         ResNet, the placement that pins trunk scale per layer, at the
         price of making that scale a per-sample statistic.

Device note: parameters are initialized on CPU (seed-reproducible) and the
model is then moved to the requested device, so the ONLY device-dependent
numeric difference is float reduction order. Each run records its device.
"""
import json
import math
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(max(1, os.cpu_count() or 1))

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'figures', 'p-027')
os.makedirs(OUT, exist_ok=True)
RES_PATH = os.path.join(OUT, 'training-results.json')

D = 32
H = 1.0
SEEDS = [0, 1, 2]
LRS = [1e-3, 3e-3]
TASKS = {'circles4': [30, 120, 240], 'spirals2': [120]}
GRID_MODELS = ('ph', 'resnet', 'resnet-ln', 'cayley')  # the paper's default
EPOCHS = 50
PATIENCE = 10
BATCH = 256
N_TOTAL = 6000
SPLIT = (3600, 1200, 1200)


# ---------------------------------------------------------------- data
def make_circles4(rng, n, d=D):
    """The paper's rank-2 task: 4 classes on a circle in a 2-plane."""
    y = rng.integers(0, 4, n)
    ang = y * (np.pi / 2) + 0.25 * rng.standard_normal(n)
    e0 = np.zeros(d); e0[0] = 1.0
    e1 = np.zeros(d); e1[1] = 1.0
    X = (1.1 * np.cos(ang)[:, None] * e0[None, :]
         + 1.1 * np.sin(ang)[:, None] * e1[None, :]
         + 0.25 * rng.standard_normal((n, d)))
    return X.astype(np.float32), y.astype(np.int64)


def make_spirals2(rng, n, d=D):
    """Two interleaved Archimedean spirals in a 2-plane (harder task)."""
    t = rng.random(n)
    cls = rng.integers(0, 2, n)
    ang = cls * np.pi + t * 2.5 * 2 * np.pi
    r = 0.15 + 0.95 * t
    e0 = np.zeros(d); e0[0] = 1.0
    e1 = np.zeros(d); e1[1] = 1.0
    X = (r[:, None] * np.cos(ang)[:, None] * e0[None, :]
         + r[:, None] * np.sin(ang)[:, None] * e1[None, :]
         + 0.08 * rng.standard_normal((n, d)))
    return X.astype(np.float32), cls.astype(np.int64)


def split_data(task, seed):
    rng = np.random.default_rng(1000 + seed)
    gen = make_circles4 if task == 'circles4' else make_spirals2
    X, y = gen(rng, N_TOTAL)
    return ((X[:3600], y[:3600]), (X[3600:4800], y[3600:4800]),
            (X[4800:], y[4800:]))


# ---------------------------------------------------------------- layers
def cayley_C(A):
    S = A - A.T
    I = torch.eye(A.shape[0], device=A.device, dtype=A.dtype)
    return torch.linalg.solve(I + 0.5 * S, I - 0.5 * S)


class PHLayer(nn.Module):
    """z' = Lambda C z + h B tanh(W z + b)  (saturating port-Hamiltonian)."""
    def __init__(self, d, h=H, r_init=0.05):
        super().__init__()
        self.h, self.d = h, d
        self.A = nn.Parameter(torch.randn(d, d) * 0.5)
        self.L = nn.Parameter(torch.randn(d, d) * r_init / math.sqrt(d))
        self.W = nn.Parameter(torch.randn(d, d) / math.sqrt(d))
        self.b = nn.Parameter(torch.zeros(d))
        self.B = nn.Parameter(torch.randn(d, d) * 0.5 / math.sqrt(d))

    def forward(self, z):
        C = cayley_C(self.A)
        R = self.L @ self.L.T
        # damping guard (differentiable): h*lam_max(R) <= 1 by construction
        lam_max = torch.linalg.eigvalsh(R)[-1]
        scale = torch.clamp(1.0 / (self.h * lam_max + 1e-12), max=1.0)
        Lc = self.L * torch.sqrt(scale)
        R = Lc @ Lc.T
        I = torch.eye(self.d, device=z.device, dtype=z.dtype)
        Lam = torch.linalg.solve(I + 0.5 * self.h * R, I - 0.5 * self.h * R)
        u = torch.tanh(z @ self.W.T + self.b)
        return z @ C.T @ Lam + self.h * (u @ self.B.T)


class ResBlock(nn.Module):
    def __init__(self, d, ln=False):
        super().__init__()
        self.lin1 = nn.Linear(d, d)
        self.lin2 = nn.Linear(d, d)
        self.norm = nn.LayerNorm(d) if ln else nn.Identity()

    def forward(self, z):
        return z + self.lin2(torch.tanh(self.norm(self.lin1(z))))


class TrunkLNBlock(nn.Module):
    """Trunk-normalized residual block (post-LN placement) -- the rev-1.2
    follow-up ablation of Sections 4.6/8: z' = LN(z + W2 tanh(W1 z)).
    Unlike ResBlock(ln=True), which normalizes the BRANCH's pre-activation
    (the standard ResNet-with-LN placement, trunk un-normalized), this pins
    the TRUNK's scale every layer -- a per-sample statistic of the layer's
    data, so no port budget and no input-independent operator bound.
    Off the paper's default grid; enable with --models."""
    def __init__(self, d):
        super().__init__()
        self.lin1 = nn.Linear(d, d)
        self.lin2 = nn.Linear(d, d)
        self.norm = nn.LayerNorm(d)

    def forward(self, z):
        return self.norm(z + self.lin2(torch.tanh(self.lin1(z))))


class CayleyBlock(nn.Module):
    """Orthogonal transport + free residual block (control)."""
    def __init__(self, d):
        super().__init__()
        self.A = nn.Parameter(torch.randn(d, d) * 0.5)
        self.lin1 = nn.Linear(d, d)
        self.lin2 = nn.Linear(d, d)

    def forward(self, z):
        C = cayley_C(self.A)
        return z @ C.T + self.lin2(torch.tanh(self.lin1(z)))


class StreamNet(nn.Module):
    def __init__(self, model_name, depth, d=D, n_classes=4):
        super().__init__()
        if model_name == 'ph':
            layers = [PHLayer(d) for _ in range(depth)]
        elif model_name == 'resnet':
            layers = [ResBlock(d) for _ in range(depth)]
        elif model_name == 'resnet-ln':
            layers = [ResBlock(d, ln=True) for _ in range(depth)]
        elif model_name == 'resnet-tln':
            layers = [TrunkLNBlock(d) for _ in range(depth)]
        elif model_name == 'cayley':
            layers = [CayleyBlock(d) for _ in range(depth)]
        else:
            raise ValueError(model_name)
        self.layers = nn.ModuleList(layers)
        self.readout = nn.Linear(d, n_classes)

    def forward(self, x, zs_out=None):
        z = x
        for ly in self.layers:
            if zs_out is not None:
                zs_out.append(z)
            z = ly(z)
        if zs_out is not None:
            zs_out.append(z)
        return self.readout(z)

    def n_params(self):
        return sum(p.numel() for p in self.parameters())


# ---------------------------------------------------------------- training
def evaluate(model, X, y, bs=1024):
    model.eval()
    dev = next(model.parameters()).device
    correct = 0
    with torch.no_grad():
        for i in range(0, len(X), bs):
            xb = torch.from_numpy(X[i:i + bs]).to(dev)
            pred = model(xb).argmax(1).cpu().numpy()
            correct += int((pred == y[i:i + bs]).sum())
    return correct / len(X)


def train_run(model_name, task, depth, seed, lr, device='cpu', quiet=True):
    t0 = time.time()
    torch.manual_seed(seed)
    dev = torch.device(device)
    (Xtr, ytr), (Xva, yva), (Xte, yte) = split_data(task, seed)
    n_classes = 4 if task == 'circles4' else 2
    model = StreamNet(model_name, depth, n_classes=n_classes).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(
        opt, T_max=EPOCHS, eta_min=lr * 1e-3)
    steps = (len(Xtr) + BATCH - 1) // BATCH
    best_val, best_state, best_ep, bad = 0.0, None, 0, 0
    for ep in range(EPOCHS):
        model.train()
        idx = np.random.default_rng(seed * 1000 + ep).permutation(len(Xtr))
        for s in range(steps):
            sel = idx[s * BATCH:(s + 1) * BATCH]
            xb = torch.from_numpy(Xtr[sel]).to(dev)
            yb = torch.from_numpy(ytr[sel]).to(dev)
            loss = F.cross_entropy(model(xb), yb)
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()
        va = evaluate(model, Xva, yva)
        if va > best_val + 1e-9:
            best_val, best_ep, bad = va, ep, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    test_acc = evaluate(model, Xte, yte)

    # per-layer gradient statistics on the TRAINED model (audit request)
    model.train()
    dev = next(model.parameters()).device
    xb = torch.from_numpy(Xtr[:256]).to(dev).requires_grad_(True)
    yb = torch.from_numpy(ytr[:256]).to(dev)
    zs, gnorms = [], []
    out = model(xb, zs_out=zs)
    loss = F.cross_entropy(out, yb)
    for z in zs:
        z.register_hook(lambda g, store=gnorms: store.append(
            float(g.norm(dim=1).mean())))
    loss.backward()
    gL = gnorms[-1]
    grad_max_ratio = max(g / gL for g in gnorms)
    grad_min_ratio = min(g / gL for g in gnorms)

    # forward activation growth on the trained model
    model.eval()
    zs2 = []
    with torch.no_grad():
        model(xb, zs_out=zs2)
    n0 = float(zs2[0].detach().norm(dim=1).median())
    nL = float(zs2[-1].detach().norm(dim=1).median())
    fwd_growth = nL / max(n0, 1e-12)

    run = dict(task=task, model=model_name, depth=depth, seed=seed, lr=lr,
               device=str(dev), test_acc=test_acc, val_acc=best_val, best_epoch=best_ep,
               epochs_run=ep + 1, params=model.n_params(),
               grad_max_ratio=grad_max_ratio, grad_min_ratio=grad_min_ratio,
               fwd_growth=fwd_growth, wall_s=time.time() - t0)
    if not quiet:
        print('  %s' % json.dumps(run))
    return run


def save(runs, done=False, models=GRID_MODELS):
    summary = {}
    for task, depths in TASKS.items():
        summary[task] = {}
        for dp in depths:
            summary[task][str(dp)] = {}
            for m in models:
                cand = [r for r in runs if r['task'] == task
                        and r['depth'] == dp and r['model'] == m
                        and r['seed'] in SEEDS]
                by_seed = {}
                for r in cand:
                    k = r['seed']
                    if k not in by_seed or r['val_acc'] > by_seed[k]['val_acc']:
                        by_seed[k] = r
                pick = list(by_seed.values())
                if pick:
                    accs = [r['test_acc'] for r in pick]
                    gm = [r['grad_max_ratio'] for r in pick]
                    fg = [r['fwd_growth'] for r in pick]
                    summary[task][str(dp)][m] = dict(
                        test_acc=[float(np.mean(accs)), float(np.std(accs))],
                        grad_max_ratio=[float(np.mean(gm)), float(np.std(gm))],
                        fwd_growth=[float(np.mean(fg)), float(np.std(fg))],
                        val_acc=[float(np.mean([r['val_acc'] for r in pick])),
                                 float(np.std([r['val_acc'] for r in pick]))],
                        seeds=len(pick))
    doc = dict(config=dict(d=D, h=H, seeds=SEEDS, lrs=LRS, epochs=EPOCHS,
                           batch=BATCH, split=list(SPLIT), tasks=TASKS,
                           models=list(models)),
               runs=runs, summary=summary, complete=done)
    with open(RES_PATH, 'w') as f:
        json.dump(doc, f, indent=1)


def main():
    smoke = '--smoke' in sys.argv
    budget = None
    device = 'auto'
    models = GRID_MODELS
    for a in sys.argv:
        if a.startswith('--budget='):
            budget = float(a.split('=', 1)[1])
        if a.startswith('--device='):
            device = a.split('=', 1)[1].strip().lower()
        if a.startswith('--models='):
            models = tuple(m.strip() for m in a.split('=', 1)[1].split(',')
                           if m.strip())
    known = ('ph', 'resnet', 'resnet-ln', 'resnet-tln', 'cayley')
    bad = [m for m in models if m not in known]
    if bad:
        sys.exit('unknown --models entry: %s (known: %s)'
                 % (', '.join(bad), ', '.join(known)))
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if device.startswith('cuda') and not torch.cuda.is_available():
        print('cuda requested but unavailable; falling back to cpu')
        device = 'cpu'
    print('device: %s' % device, flush=True)
    t_start = time.time()
    runs = []
    if os.path.exists(RES_PATH):
        with open(RES_PATH) as f:
            runs = json.load(f).get('runs', [])
        print('resuming: %d completed runs on file' % len(runs))
    jobs = []
    for task, depths in TASKS.items():
        for dp in depths:
            for m in models:
                for sd in SEEDS:
                    for lr in LRS:
                        if any(r['task'] == task and r['depth'] == dp
                               and r['model'] == m and r['seed'] == sd
                               and abs(r['lr'] - lr) < 1e-12 for r in runs):
                            continue
                        jobs.append((m, task, dp, sd, lr))
    if smoke:
        jobs = jobs[:1]
    print('%d jobs to run' % len(jobs), flush=True)
    for i, (m, task, dp, sd, lr) in enumerate(jobs):
        if budget is not None and time.time() - t_start + 150 > budget:
            print('budget exhausted after %d jobs; exiting (resumable)'
                  % i, flush=True)
            break
        print('[%d/%d] %s depth=%d seed=%d lr=%g' %
              (i + 1, len(jobs), m, dp, sd, lr), flush=True)
        r = train_run(m, task, dp, sd, lr, device=device)
        runs.append(r)
        save(runs, models=models)
        print('    test %.3f  val %.3f  grad_max %.2f  fwd x%.2f  %.1fs' %
              (r['test_acc'], r['val_acc'], r['grad_max_ratio'],
               r['fwd_growth'], r['wall_s']), flush=True)
    if smoke:
        print('smoke run complete')
        return
    save(runs, True, models=models)
    make_figure(runs)
    print('wrote f7-training.png and training-results.json (complete)')


# ---------------------------------------------------------------- figure
def make_figure(runs):
    """Delegates to code/p-027-figures.py (torch-free, so f7 regenerates
    from training-results.json without the training stack)."""
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        'p027_figs', os.path.join(here, 'p-027-figures.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.make_figure(runs, OUT)


if __name__ == '__main__':
    main()
