#!/usr/bin/env python3
"""P-027 E7: real-data evaluation (CIFAR-10 first, CIFAR-100 gated).

Registered question (figures/p-027/e7-preregistration.json, written BEFORE
any run): does the port-Hamiltonian stream's operator-bound architecture
offer better stability or trainability at depth on real data, without
unacceptable losses in predictive performance, training speed, or memory?

The E6 audit experiment (p-027b-training.py) settled synthetic tasks at
width 32: the architecture trains to parity at depth 240 with no
normalizer in the stream. The standing objection — Section 8 of the paper
and the layernorm explainer's own "where this could be wrong" list — is
scale: nothing there competes on real data. This harness is that test.

Mechanism-preserving adaptation (the design constraint: the stream's
defining update survives, only its substrate changes):

  stem    (shared by every family, normalization-free, linear):
          Conv3x3(3->d, s2) -> MaxPool2 -> Conv3x3(d->d) -> MaxPool2
          => state z is a d x 8 x 8 feature map

  stream  one block per layer, families differ ONLY in the trunk update;
          all non-PH families share the identical branch
          g(z) = Conv1x1( tanh( Conv3x3(z) ) )  so capacity stays matched:

            ph         z' = Lambda_t C_t z + h B_t tanh(Conv3x3_t(z))
            cayley     z' = C_t z + g(z)
            resnet     z' = z + g(z)
            resnet-ln  z' = z + Conv1x1(tanh(LN(Conv3x3(z))))     (branch LN)
            resnet-tln z' = LN(z + g(z))                          (trunk LN)

          C_t, Lambda_t are Cayley-parameterized on CHANNELS (1x1 maps),
          the same exact-orthogonal / exact-contraction machinery as the
          dense harness, differentiable through one linear solve each,
          damping guard h*lam_max(R) <= 1 enforced by construction.
          Because C, Lambda, B act on channels only, the port budget
          holds PER POSITION exactly:

            ||z_L(p)|| <= ||z_0(p)|| + sum_t h ||B_t u_t(p)||

          The Conv3x3 inside the port input u_t mixes a 3x3 neighborhood,
          but the per-step triangle inequality never needed u_t to be
          local — spatial receptive field grows through the ports while
          the transported state stays under law. Every trained PH run
          self-checks this bound on real batches (violation count must
          be 0 and is recorded).

Protocol (identical for every family, tuning budget matched):
  * CIFAR-10 45000/5000/10000 train/val/test; split rng 1000+seed
  * standard per-channel normalization; RandomCrop(32, 4) + HFlip on
    train only; test set NEVER used for selection or tuning
  * learning-rate grid {3e-4, 1e-3} — the same two candidates for every
    architecture; per-(model, depth, seed) selection on validation
  * Adam, cosine decay to lr*1e-3, batch 256, weight decay 0,
    NO gradient clipping anywhere (instability must be observable)
  * 30 epochs, early stopping on validation accuracy (patience 8),
    best checkpoint restored, test evaluated once at the end
  * depths {12, 48, 96}; seeds {0, 1, 2}; d = 64

Metrics recorded per run (the audit's stage-3 list):
  train/val loss + accuracy history, final test loss + accuracy
  per-layer activation-norm profile (median over batch and positions of
  the per-position channel norm — the theorem's own quantity)
  per-layer gradient-norm profile (mean over batch of the flattened
  block-input gradient norm), max/min ratio to the readout gradient
  instability ledger: NaN event count, divergence flag + epoch, all
  failed runs kept in the results file
  parameter count, wall-clock, seconds/epoch, images/sec, peak CUDA
  memory
  device, GPU name, torch + cudnn versions

Device policy — the fix for the E6 lesson (all 96 E6 runs ran on CPU
because the tiny d=32 grid is launch-overhead-bound and the notebook's
benchmark honestly preferred CPU): this harness REQUIRES CUDA by
default. --device=auto means "cuda, and exit loudly if absent". CPU is
available only as an explicit --device=cpu for --smoke portability
checks; every run records its device, so a CPU E7 run is visible in the
file and excluded from the GPU wall-clock comparisons.

Outputs: figures/p-027/cifar-results.json (incremental, resumable)
         figures/p-027/f8-cifar.png  (via code/p-027d-cifar-figures.py,
         torch-free, regenerates from the results file)

Run:  python3 code/p-027c-cifar.py                 # E7a: CIFAR-10 grid
      python3 code/p-027c-cifar.py --smoke         # 1 job, any device
      python3 code/p-027c-cifar.py --dataset=cifar100 --depths=48,96
      python3 code/p-027c-cifar.py --budget=5400   # stop cleanly, resumable
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

torch.set_num_threads(max(1, (os.cpu_count() or 1) // 2))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'figures', 'p-027')
os.makedirs(OUT, exist_ok=True)
RES_PATH = os.path.join(OUT, 'cifar-results.json')
PREREG_PATH = os.path.join(OUT, 'e7-preregistration.json')

D = 64                # stream width (channels)
H = 1.0               # port step size (paper's default)
SPATIAL = 8           # feature-map side after the shared stem
MODELS = ('ph', 'resnet', 'resnet-ln', 'resnet-tln', 'cayley')
EPOCHS = 30
PATIENCE = 8
BATCH = 256
EVAL_BATCH = 512
LRS = [3e-4, 1e-3]
SEEDS = [0, 1, 2]
DEPTH_GRID = {'cifar10': [12, 48, 96], 'cifar100': [48, 96]}
N_CLASSES = {'cifar10': 10, 'cifar100': 100}
# standard CIFAR normalization (fixed constants, no leakage)
MEAN_STD = {'cifar10': ((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
            'cifar100': ((0.5071, 0.4865, 0.4409), (0.2673, 0.2564, 0.2762))}
TRAIN_N = 45000
VAL_N = 5000


# ---------------------------------------------------------------- data
def build_loaders(dataset, seed, data_root='data'):
    """45k/5k/10k split; rng 1000+seed (the E6 convention, so seed variance
    includes split variance — same treatment for every family)."""
    from torchvision import datasets, transforms
    mean, std = MEAN_STD[dataset]
    cls = (datasets.CIFAR10 if dataset == 'cifar10'
           else datasets.CIFAR100)
    train_tf = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    plain_tf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    base = cls(root=data_root, train=True, download=True)
    g = torch.Generator().manual_seed(1000 + seed)
    idx = torch.randperm(len(base), generator=g).tolist()
    tr_idx, va_idx = idx[:TRAIN_N], idx[TRAIN_N:TRAIN_N + VAL_N]

    train_ds = cls(root=data_root, train=True, download=False,
                   transform=train_tf)
    val_ds = cls(root=data_root, train=True, download=False,
                 transform=plain_tf)
    test_ds = cls(root=data_root, train=False, download=True,
                  transform=plain_tf)
    train_ds = torch.utils.data.Subset(train_ds, tr_idx)
    val_ds = torch.utils.data.Subset(val_ds, va_idx)

    kw = dict(num_workers=2, pin_memory=True, persistent_workers=True)
    train_ld = torch.utils.data.DataLoader(
        train_ds, batch_size=BATCH, shuffle=True, drop_last=False, **kw)
    val_ld = torch.utils.data.DataLoader(
        val_ds, batch_size=EVAL_BATCH, shuffle=False, **kw)
    test_ld = torch.utils.data.DataLoader(
        test_ds, batch_size=EVAL_BATCH, shuffle=False, **kw)
    return train_ld, val_ld, test_ld


# ---------------------------------------------------------------- layers
def cayley_C(A):
    """Exact orthogonal map on channels: C = (I - S/2)^-1 (I + S/2), S skew."""
    d = A.shape[0]
    S = A - A.transpose(0, 1)
    I = torch.eye(d, device=A.device, dtype=A.dtype)
    return torch.linalg.solve(I + 0.5 * S, I - 0.5 * S)


class ConvPHLayer(nn.Module):
    """z' = Lambda C z + h B tanh(Conv3x3(z))  — the PH stream on maps.

    C: Cayley transport on channels (exact orthogonal, any parameters).
    Lambda: Cayley of -h R/2 with R = L L^T (exact symmetric contraction,
    spectrum in (-1, 1)); damping guard h lam_max(R) <= 1 by construction.
    B: 1x1 port; u = tanh(Conv3x3(z)) is the saturating port input.
    """
    def __init__(self, d, h=H, r_init=0.05):
        super().__init__()
        self.h, self.d = h, d
        self.A = nn.Parameter(torch.randn(d, d) * 0.5)
        self.L = nn.Parameter(torch.randn(d, d) * r_init / math.sqrt(d))
        self.B = nn.Parameter(torch.randn(d, d) * 0.5 / math.sqrt(d))
        self.conv = nn.Conv2d(d, d, kernel_size=3, padding=1)

    def forward(self, z, port_inj=None):
        C = cayley_C(self.A)
        R = self.L @ self.L.T
        lam_max = torch.linalg.eigvalsh(R)[-1]
        scale = torch.clamp(1.0 / (self.h * lam_max + 1e-12), max=1.0)
        Lc = self.L * torch.sqrt(scale)
        R = Lc @ Lc.T
        I = torch.eye(self.d, device=z.device, dtype=z.dtype)
        Lam = torch.linalg.solve(I + 0.5 * self.h * R, I - 0.5 * self.h * R)
        u = torch.tanh(self.conv(z))
        # 1x1-equivalent application of the channel operators:
        zc = torch.einsum('cd,bdhw->bchw', C, z)
        out = torch.einsum('cd,bdhw->bchw', Lam, zc)
        # port: B acts on channels of u (1x1 conv via matrix)
        out = out + self.h * torch.einsum('cd,bdhw->bchw', self.B, u)
        if port_inj is not None:
            # per-position port injection norm ||B u(p)|| * h, for the
            # exact budget check (the theorem's own quantity)
            Bu = torch.einsum('cd,bdhw->bchw', self.B, u)
            port_inj.append(self.h * Bu.flatten(2).norm(dim=1))  # (B, HW)
        return out


class ConvCayleyLayer(nn.Module):
    """z' = C z + g(z) — orthogonal transport, free branch (control)."""
    def __init__(self, d):
        super().__init__()
        self.A = nn.Parameter(torch.randn(d, d) * 0.5)
        self.branch = ConvBranch(d)

    def forward(self, z):
        C = cayley_C(self.A)
        return torch.einsum('cd,bdhw->bchw', C, z) + self.branch(z)


class ConvBranch(nn.Module):
    """g(z) = Conv1x1(tanh(Conv3x3(z))) — shared by all non-PH families,
    so capacity is matched and only the trunk update differs."""
    def __init__(self, d, ln=False):
        super().__init__()
        self.conv3 = nn.Conv2d(d, d, kernel_size=3, padding=1)
        self.conv1 = nn.Conv2d(d, d, kernel_size=1)
        self.norm = nn.LayerNorm(d) if ln else nn.Identity()

    def forward(self, z):
        a = self.conv3(z)                       # (B, d, H, W)
        a = self.norm(a.transpose(1, 3)).transpose(1, 3)  # LN over channels
        return self.conv1(torch.tanh(a))


class ConvResLayer(nn.Module):
    """z' = z + g(z) — the standard residual stream."""
    def __init__(self, d, ln=False, tln=False):
        super().__init__()
        self.branch = ConvBranch(d, ln=ln)
        self.trunk_norm = nn.LayerNorm(d) if tln else nn.Identity()

    def forward(self, z):
        out = z + self.branch(z)
        if self.trunk_norm is not None and not isinstance(
                self.trunk_norm, nn.Identity):
            out = self.trunk_norm(out.transpose(1, 3)).transpose(1, 3)
        return out


class StreamNet(nn.Module):
    """Shared stem -> L stream blocks -> GAP -> linear head."""
    def __init__(self, model_name, depth, d=D, n_classes=10, in_ch=3):
        super().__init__()
        self.model_name = model_name
        self.stem = nn.Sequential(
            nn.Conv2d(in_ch, d, kernel_size=3, stride=2, padding=1),
            nn.MaxPool2d(2),
            nn.Conv2d(d, d, kernel_size=3, padding=1),
            nn.MaxPool2d(2),
        )
        if model_name == 'ph':
            layers = [ConvPHLayer(d) for _ in range(depth)]
        elif model_name == 'cayley':
            layers = [ConvCayleyLayer(d) for _ in range(depth)]
        elif model_name == 'resnet':
            layers = [ConvResLayer(d) for _ in range(depth)]
        elif model_name == 'resnet-ln':
            layers = [ConvResLayer(d, ln=True) for _ in range(depth)]
        elif model_name == 'resnet-tln':
            layers = [ConvResLayer(d, tln=True) for _ in range(depth)]
        else:
            raise ValueError(model_name)
        self.layers = nn.ModuleList(layers)
        self.head = nn.Linear(d, n_classes)

    def forward(self, x, zs_out=None, port_inj=None):
        z = self.stem(x)
        for ly in self.layers:
            if zs_out is not None:
                zs_out.append(z)
            if port_inj is not None and isinstance(ly, ConvPHLayer):
                z = ly(z, port_inj=port_inj)
            else:
                z = ly(z)
        if zs_out is not None:
            zs_out.append(z)
        return self.head(z.mean(dim=(2, 3)))

    def n_params(self):
        return sum(p.numel() for p in self.parameters())


# ---------------------------------------------------------------- metrics
def channel_norm_stats(z):
    """Median over (batch, positions) of the per-position channel norm —
    the theorem's quantity for the conv adaptation."""
    return float(z.flatten(2).norm(dim=1).median())


def evaluate(model, loader, dev, return_loss=False):
    model.eval()
    correct, total, loss_sum = 0, 0, 0.0
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(dev, non_blocking=True), yb.to(dev,
                                                          non_blocking=True)
            out = model(xb)
            loss_sum += float(F.cross_entropy(out, yb, reduction='sum'))
            correct += int((out.argmax(1) == yb).sum())
            total += yb.numel()
    acc = correct / total
    return (acc, loss_sum / total) if return_loss else acc


def train_run(model_name, dataset, depth, seed, lr, device='cuda',
              epochs=EPOCHS, data_root='data', quiet=True):
    t0 = time.time()
    dev = torch.device(device)
    torch.manual_seed(seed)
    if dev.type == 'cuda':
        torch.cuda.manual_seed_all(seed)
        torch.cuda.reset_peak_memory_stats()
    train_ld, val_ld, test_ld = build_loaders(dataset, seed, data_root)

    model = StreamNet(model_name, depth, n_classes=N_CLASSES[dataset]).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(
        opt, T_max=epochs, eta_min=lr * 1e-3)

    # NaN/divergence ledger: non-finite losses are counted and skipped;
    # eight events (or a loss above 1e4) marks the run diverged. Failed
    # runs stay in the results file with their flags — they are reported,
    # not discarded.
    hist, best_val, best_state, best_ep, bad = [], -1.0, None, 0, 0
    nan_events, diverged, diverged_ep = 0, False, None
    train_wall = 0.0
    for ep in range(epochs):
        model.train()
        te0 = time.time()
        running, seen = 0.0, 0
        for xb, yb in train_ld:
            xb = xb.to(dev, non_blocking=True)
            yb = yb.to(dev, non_blocking=True)
            out = model(xb)
            loss = F.cross_entropy(out, yb)
            if not torch.isfinite(loss):
                nan_events += 1
                opt.zero_grad(set_to_none=True)
                if nan_events >= 8:
                    diverged, diverged_ep = True, ep
                continue
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            running += float(loss) * yb.numel()
            seen += yb.numel()
            if diverged:
                break
        train_wall += time.time() - te0
        train_loss = running / max(seen, 1)
        va, vl = evaluate(model, val_ld, dev, return_loss=True)
        hist.append(dict(epoch=ep, train_loss=train_loss, val_loss=vl,
                         val_acc=va))
        if not quiet:
            print('    ep %02d  train %.3f  val %.3f/%.3f'
                  % (ep, train_loss, vl, va), flush=True)
        if math.isfinite(va) and va > best_val + 1e-9:
            best_val, best_ep, bad = va, ep, 0
            best_state = {k: v.detach().clone()
                          for k, v in model.state_dict().items()}
        else:
            bad += 1
        if diverged or (loss > 1e4) or bad >= PATIENCE:
            if loss > 1e4:
                diverged, diverged_ep = True, ep
            break
        sched.step()
    if best_state is not None:
        model.load_state_dict(best_state)
    test_acc, test_loss = evaluate(model, test_ld, dev, return_loss=True)

    # ---- profiles on the trained model (the audit's stage-3 measurements)
    model.eval()
    probe = next(iter(val_ld))
    xb = probe[0][:256].to(dev)
    zs, gnorms, port_inj = [], [], []
    out = model(xb, zs_out=zs, port_inj=port_inj
                if model_name == 'ph' else None)
    loss = F.cross_entropy(out, probe[1][:256].to(dev))
    for z in zs:
        z.register_hook(lambda g, store=gnorms: store.append(
            float(g.flatten(1).norm(dim=1).mean())))
    loss.backward()
    act_profile = [channel_norm_stats(z.detach()) for z in zs]
    # backward fires hooks z_L-first; store is [g_zL, ..., g_z0].
    # Normalize to depth order [z_0 ... z_L] and reference the READOUT-side
    # gradient (t = L): ratios > 1 mean backward amplification.
    grad_profile = list(reversed(gnorms))
    gL = grad_profile[-1]
    grad_max_ratio = max(g / gL for g in grad_profile)
    grad_min_ratio = min(g / gL for g in grad_profile)
    act_growth = act_profile[-1] / max(act_profile[0], 1e-12)

    # ---- the theorem's own check on real data (PH only)
    port_violations, tightness = None, None
    if model_name == 'ph':
        with torch.no_grad():
            zs2, inj2 = [], []
            model(xb, zs_out=zs2, port_inj=inj2)
        # per position: ||z_L(p)|| <= ||z_0(p)|| + sum_t h ||B u_t(p)||
        z0 = zs2[0].flatten(2).norm(dim=1)        # (B, HW)
        zL = zs2[-1].flatten(2).norm(dim=1)
        bound = z0 + sum(inj2)                    # (B, HW)
        port_violations = int((zL > bound * (1 + 1e-4)).sum())
        tightness = float((zL / bound).median())

    peak_mem = (torch.cuda.max_memory_allocated() / 1e6
                if dev.type == 'cuda' else None)
    gpu_name = (torch.cuda.get_device_name(0)
                if dev.type == 'cuda' else None)
    images_seen = (best_ep + 1) * TRAIN_N
    run = dict(
        exp='e7', dataset=dataset, model=model_name, depth=depth, seed=seed,
        lr=lr, device=str(dev), gpu_name=gpu_name,
        torch_version=torch.__version__,
        cudnn_version=(torch.backends.cudnn.version()
                       if dev.type == 'cuda' else None),
        test_acc=test_acc, test_loss=test_loss, best_val_acc=best_val,
        best_epoch=best_ep, epochs_run=ep + 1,
        diverged=diverged, diverged_epoch=diverged_ep, nan_events=nan_events,
        train_loss_history=[round(h['train_loss'], 4) for h in hist],
        val_acc_history=[round(h['val_acc'], 4) for h in hist],
        params=model.n_params(),
        wall_s=round(time.time() - t0, 1),
        train_wall_s=round(train_wall, 1),
        sec_per_epoch=round(train_wall / max(ep + 1, 1), 2),
        images_per_sec=round(images_seen / max(train_wall, 1e-9), 1),
        peak_mem_mb=round(peak_mem, 1) if peak_mem else None,
        act_profile=[round(v, 4) for v in act_profile],
        grad_profile=[round(v, 6) for v in grad_profile],
        act_growth=round(act_growth, 4),
        grad_max_ratio=round(grad_max_ratio, 4),
        grad_min_ratio=round(grad_min_ratio, 4),
        port_violations=port_violations,
        budget_tightness=tightness and round(tightness, 4),
    )
    if not quiet:
        print('  %s' % json.dumps({k: v for k, v in run.items()
                                   if k not in ('act_profile',
                                                'grad_profile',
                                                'train_loss_history',
                                                'val_acc_history')}))
    return run


# ---------------------------------------------------------------- driver
def load_runs():
    if os.path.exists(RES_PATH):
        with open(RES_PATH) as f:
            return json.load(f).get('runs', [])
    return []


def save(runs, done=False, config=None):
    summary = {}
    for m in MODELS:
        for dp in config['depths']:
            cand = [r for r in runs if r['dataset'] == config['dataset']
                    and r['depth'] == dp and r['model'] == m
                    and r['seed'] in config['seeds']]
            by_seed = {}
            for r in cand:
                k = r['seed']
                if k not in by_seed or r['best_val_acc'] > \
                        by_seed[k]['best_val_acc']:
                    by_seed[k] = r
            pick = list(by_seed.values())
            if pick:
                accs = [r['test_acc'] for r in pick]
                summary['%s|%d' % (m, dp)] = dict(
                    test_acc=[float(np.mean(accs)), float(np.std(accs))],
                    act_growth=[float(np.mean([r['act_growth']
                                               for r in pick])),
                                float(np.std([r['act_growth'] for r in pick]))],
                    grad_max=[float(np.mean([r['grad_max_ratio']
                                             for r in pick]))],
                    wall_s=[float(np.mean([r['wall_s'] for r in pick]))],
                    peak_mem_mb=[float(np.mean([r['peak_mem_mb'] or 0
                                                for r in pick]))],
                    params=pick[0]['params'],
                    diverged=sum(1 for r in pick if r['diverged']),
                    nan_events=sum(r['nan_events'] for r in pick),
                    port_violations=(sum(r['port_violations'] or 0
                                         for r in pick)
                                     if m == 'ph' else None),
                    seeds=len(pick))
    doc = dict(config=config, preregistration=PREREG_PATH, runs=runs,
               summary=summary, complete=done)
    with open(RES_PATH, 'w') as f:
        json.dump(doc, f, indent=1)


def main():
    smoke = '--smoke' in sys.argv
    dataset, device, budget, epochs = 'cifar10', 'auto', None, EPOCHS
    models, seeds, lrs, depths = MODELS, SEEDS, LRS, None
    for a in sys.argv:
        if a.startswith('--dataset='):
            dataset = a.split('=', 1)[1].strip()
        elif a.startswith('--device='):
            device = a.split('=', 1)[1].strip().lower()
        elif a.startswith('--models='):
            models = tuple(m.strip() for m in a.split('=', 1)[1].split(',')
                           if m.strip())
        elif a.startswith('--seeds='):
            seeds = [int(v) for v in a.split('=', 1)[1].split(',')]
        elif a.startswith('--lrs='):
            lrs = [float(v) for v in a.split('=', 1)[1].split(',')]
        elif a.startswith('--depths='):
            depths = [int(v) for v in a.split('=', 1)[1].split(',')]
        elif a.startswith('--epochs='):
            epochs = int(a.split('=', 1)[1])
        elif a.startswith('--budget='):
            budget = float(a.split('=', 1)[1])

    if depths is None:
        depths = DEPTH_GRID[dataset]
    bad = [m for m in models if m not in MODELS]
    if bad:
        sys.exit('unknown --models entry: %s (known: %s)'
                 % (', '.join(bad), ', '.join(MODELS)))

    # ---- device policy: GPU required, no silent CPU fallback (E6 lesson)
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'MISSING'
    if device == 'cuda' and not torch.cuda.is_available():
        sys.exit('\n*** CUDA GPU REQUIRED but not available. ***\n'
                 'E7 must run on GPU (all wall-clock/throughput comparisons '
                 'are GPU-only).\nColab: Runtime -> Change runtime type -> '
                 'T4 GPU -> Save, then rerun.\nFor a portability smoke test '
                 'only: --smoke --device=cpu\n')
    if device.startswith('cuda'):
        torch.backends.cudnn.benchmark = True
    print('device: %s' % device, flush=True)
    if device.startswith('cuda'):
        print('gpu: %s (%.1f GB)  torch %s  cudnn %s'
              % (torch.cuda.get_device_name(0),
                 torch.cuda.get_device_properties(0).total_memory / 2**30,
                 torch.__version__,
                 torch.backends.cudnn.version()), flush=True)

    if not os.path.exists(PREREG_PATH):
        sys.exit('missing %s — the pre-registration must exist before any '
                 'E7 run' % PREREG_PATH)
    with open(PREREG_PATH) as f:
        print('pre-registration: %s (registered %s, status: %s)'
              % (PREREG_PATH, json.load(f)['registered_at'],
                 'no E7 runs yet' if not load_runs() else 'runs exist'),
              flush=True)

    config = dict(dataset=dataset, depths=depths, seeds=seeds, lrs=lrs,
                  models=list(models), epochs=epochs, patience=PATIENCE,
                  batch=BATCH, d=D, h=H, split=[TRAIN_N, VAL_N, 10000],
                  optimizer='adam+cosine', weight_decay=0.0,
                  grad_clip='none (instability must be observable)',
                  augmentation='RandomCrop(32,4)+HFlip (train only)',
                  device_policy='cuda required',
                  lrs_selected_on='validation')

    t_start = time.time()
    runs = load_runs()
    print('resuming: %d completed E7 runs on file' % len(runs), flush=True)
    jobs = []
    for dp in depths:
        for m in models:
            for sd in seeds:
                for lr in lrs:
                    if any(r['dataset'] == dataset and r['depth'] == dp
                           and r['model'] == m and r['seed'] == sd
                           and abs(r['lr'] - lr) < 1e-12 for r in runs):
                        continue
                    jobs.append((m, dp, sd, lr))
    if smoke:
        jobs = jobs[:1]
    print('%d jobs to run (%s, depths %s, models %s)'
          % (len(jobs), dataset, depths, ','.join(models)), flush=True)

    for i, (m, dp, sd, lr) in enumerate(jobs):
        if budget is not None and time.time() - t_start + 300 > budget:
            print('budget exhausted after %d jobs; exiting (resumable)'
                  % i, flush=True)
            break
        print('[%d/%d] %s depth=%d seed=%d lr=%g'
              % (i + 1, len(jobs), m, dp, sd, lr), flush=True)
        r = train_run(m, dataset, dp, sd, lr, device=device, epochs=epochs)
        runs.append(r)
        save(runs, config=config)
        print('    test %.3f  val %.3f  growth %.2fx  gmax %.2f  '
              'nan %d  %d img/s  %.1fs'
              % (r['test_acc'], r['best_val_acc'], r['act_growth'],
                 r['grad_max_ratio'], r['nan_events'], r['images_per_sec'],
                 r['wall_s']), flush=True)

    if smoke:
        print('smoke run complete')
        return
    save(runs, True, config=config)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'f', os.path.join(HERE, 'p-027d-cifar-figures.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        mod.make_figure(runs, OUT, dataset=config['dataset'])
        print('wrote f8-cifar.png and cifar-results.json', flush=True)
    except Exception as e:
        print('figure generation deferred (torch-free script): %s' % e)


if __name__ == '__main__':
    main()
