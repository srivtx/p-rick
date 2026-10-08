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
