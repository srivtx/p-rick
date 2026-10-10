# Series VI — reproduction harnesses

One file per paper. Each regenerates every figure and the `results.json`
aggregate file cited in the paper's text (deterministic; PCG64 seeded).

| paper | file | figures | runtime |
|-------|------|---------|---------|
| P-021 | `p-021-simulation.py` | `figures/p-021/` (6) + results.json | ~6 min |
| P-022 | `p-022-simulation.py` | `figures/p-022/` (5) + results.json | ~6 min |
| P-023 | `p-023-simulation.py` | `figures/p-023/` (5) + results.json | ~2 min |

Requirements: NumPy, Matplotlib. Run from the repository root:

    python3 code/p-021-simulation.py

(The scripts resolve their output directory relative to the repo when the
agent workspace path is absent, so they run unmodified after checkout.)

# P-027 — law suite, training, and the real-data evaluation

| purpose | file | notes |
|---------|------|-------|
| laws + figures 1–6 | `p-027-simulation.py` | NumPy + Matplotlib, seed 20261009 |
| 13-assertion law suite | `p-027-tests.py` | runs on CPU in seconds; the math check, independent of any benchmark |
| E6 end-to-end training | `p-027b-training.py` | PyTorch; 96-run four-architecture sweep (landed, all CPU — see the device note in the file); `--models=resnet-tln` adds the E6b trunk-LN ablation; **CUDA is required when requested — the harness hard-exits instead of falling back to CPU** |
| figure 7 (torch-free) | `p-027-figures.py` | regenerates f7 from `training-results.json` |
| figure 6 (collision fix replay) | `p-027-f6-replay.py` | re-renders f6 from `results.json`; same fix patched into the simulation |
| E7 real-data training | `p-027c-cifar.py` | PyTorch, **CUDA required by default**; CIFAR-10/100, five families (ph, resnet, resnet-ln, resnet-tln, cayley), depths 12/48/96, seeds 0–2, LR grid {3e-4, 1e-3} selected on validation; records the full metric ledger (losses, per-layer activation/gradient profiles, NaN/divergence events, params, wall-clock, throughput, peak memory, device + versions); every trained PH run self-checks the port budget on real batches |
| E7 pre-registration | `../figures/p-027/e7-preregistration.json` | decision rules written before any run — the harness refuses to start without it |
| figure 8 (torch-free) | `p-027d-cifar-figures.py` | regenerates f8 from `cifar-results.json` |
| Colab entry (E6/E6b) | `p-027-colab.ipynb` | one-click T4; GPU asserted before the sweep |
| Colab entry (E6b + E7/E8) | `p-027-cifar-colab.ipynb` | one-click T4; GPU hard-required; runs the law suite FIRST, then E6b (24 runs), a time projection, then the E7a sweep (90 runs, resumable); applies the pre-registered decision rules mechanically at the end; E8 (CIFAR-100) gated behind a flag |

Run E7a locally (any CUDA box):

    python3 code/p-027c-cifar.py --device=cuda

The results files (`figures/p-027/training-results.json`,
`figures/p-027/cifar-results.json`) are incremental and resumable: every
completed run is saved, and re-running skips what is already on file.
Wall-clock, throughput, and memory columns are GPU-only by policy — CPU
runs are visible in the file (the `device` field) and excluded from the
efficiency comparisons.
