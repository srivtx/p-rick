<div align="center">

<img src="assets/favicon.svg" width="96" alt="the p-rick monogram"/>

# p-rick

**Software the world is missing — specified before anyone builds it.**

An independent research program. It hunts for genuine gaps in the software
landscape — categories with no incumbents, problems with large audiences,
theories nobody has written down — and does the research to close them:
gap verification against everything that exists, formal models, seeded
validation harnesses, typeset PDFs, and plain-language essays.

[![site](https://img.shields.io/website?down_message=offline&label=site&up_color=%233ddc97&up_message=online&url=https%3A%2F%2Fsrivtx.github.io%2Fp-rick%2Findex.html&style=flat-square)](https://srivtx.github.io/p-rick/)
[![papers](https://img.shields.io/badge/papers-30%20working-3b6ea5?style=flat-square)](https://srivtx.github.io/p-rick/papers.html)
[![law sets](https://img.shields.io/badge/law%20sets-10%20validated-8B7E5A?style=flat-square)](https://srivtx.github.io/p-rick/papers.html)
[![figures](https://img.shields.io/badge/figures-61%20reproducible-CC3311?style=flat-square)](figures/)
[![code license](https://img.shields.io/badge/code-MIT-3ddc97?style=flat-square)](LICENSE)
[![paper license](https://img.shields.io/badge/papers-CC%20BY%204.0-3ddc97?style=flat-square)](https://creativecommons.org/licenses/by/4.0/)
[![stars](https://img.shields.io/github/stars/srivtx/p-rick?style=flat-square&color=8B7E5A)](https://github.com/srivtx/p-rick/stargazers)
[![last commit](https://img.shields.io/github/last-commit/srivtx/p-rick?style=flat-square&color=3b6ea5)](https://github.com/srivtx/p-rick/commits/main)

**[Read the papers](https://srivtx.github.io/p-rick/papers.html)** ·
**[The newest law](https://srivtx.github.io/p-rick/paper/p030.html)** ·
[Essays](https://srivtx.github.io/p-rick/blog.html) ·
[The method](https://srivtx.github.io/p-rick/method.html) ·
[RSS](https://srivtx.github.io/p-rick/feed.xml)

</div>

---

## What this is

Every paper follows one discipline: state the gap as a **falsifiable claim with
named incumbents**, specify the missing system or derive the missing law, run a
seeded validation harness, and grade its own evidence honestly. Series I–V
specify missing systems. Series VI–VIII are the quantitative turn — derived
laws with reproducible figures. The operating rule is **research first;
products later**: papers and specifications before code, and product
directories only after the research freezes.

| | |
|---|---|
| **30 working papers** | each with a typeset PDF, a designed reading edition, and a companion essay |
| **10 validated law sets** | derived laws with closed forms, measured to named error bars |
| **61 reproducible figures** | every figure regenerates bit-exact from its seeded harness in `code/` |
| **0 incumbents found in-gap** | across all thirty gap verifications |
| **8 series, one arc** | from user-owned data to invented machinery |

The exclusions are hard rules: no toy projects, no deterministic wrappers, no
test suites, no verification gadgets whose only user is their own construction,
nothing AI-obsolete, no CRUD, no chatbot shells. The program specifies missing
*systems* — software that has never been built because nobody wrote down what
it would be.

## The headline laws

The five flagship results of the quantitative turn:

| Law | Statement | Validated |
|-----|-----------|-----------|
| **The collapse law** (P-025) | Retry storms have two thresholds — the ceiling **λ_c = μθρ*²/(1+θρ*)** and the recovery point **λ_r = μ/R** — the max and endpoint of one fixed-point curve. With unlimited retries, a collapsed system at 5% load *grows* its queue; restart is the only exit. | 6 experiments, multi-seed, audited rev 1.1 |
| **The dissipation budget law** (P-027) | Depth is rented, never owned: Cayley transport is exactly orthogonal (volume-free to 10⁻¹⁴), dissipation is the only contraction channel, ports are the only norm injection. Expressivity becomes a budget line. | Zero bound violations in 7,200 runs; control explodes to 10⁴³ |
| **The anchor law** (P-028) | Agentic maintenance has a floor **E[L∞] = (1−a)h²/(2(2ημ−(ημ)²)) + as²/2**, a ratchet invisible to behavior anchors, and a stability boundary **a*(h) ≈ 1 − κ/h²** — required coverage falls quadratically as models improve. | Exact to 1.7% median; boundary to 0.041 |
| **The lock-in law** (P-029) | Groupthink has a formula: agent collectives bifurcate at **K_c = T(1−λ)** — coupling and temperature exchange one-for-one, no useful middle. Locked confidence is a computable fixed point; the diversity firewall raises the threshold linearly. | Fixed point to 0.045%; 420 replicas |
| **The Green's function of context** (P-030) | Context rot has an object: the positional kernel's impulse response. The lost-in-the-middle dip lands on its closed form (2771 = 2771), and the monotonicity theorem says uniform recall is impossible with timescales alone — it takes a register. | Kernel to 0.037; dip exact; 96/96 windows |

## The papers

### Series VIII — machinery: mechanisms invented, not just found (current)

The program's second arc: new mechanisms — architectures, protocols, and design laws
for the computing that comes next — each invented, derived, and validated in a seeded
harness. Four papers, four law sets, 24 figures, all regenerable from `code/`.

| ID | Paper | The invented mechanism |
|----|-------|------------------------|
| **P-027** | [The Dissipation Budget Law](https://srivtx.github.io/p-rick/paper/p027.html) · [src](papers/p-027-dissipation-budget.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-027.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p027.html) · [figures](figures/p-027/) | The conservation architecture for depth: the residual stream as a port-Hamiltonian system — Cayley transport (exactly orthogonal, volume-free to 10⁻¹⁴ at any step size), metered dissipation (the only contraction channel: **ln\|det\| = −Σh·tr R + O(h³)**, expressivity as a budget line), ports as the only norm injection. Measured: **zero bound violations** in 7,200 runs while the control explodes to 10⁴³; gradient metering through 240 layers (max exactly 1.000); rank-2 readout at depth 120 at **98.1% ± 0.8 vs 38.3% ± 3.3, held-out over three seeds**. Rev 1.1 answers an external audit: four harness defects fixed, a 13-assertion law-test suite, and an end-to-end training experiment — **E6 complete, 96/96 runs** via the [Colab one-click harness](https://colab.research.google.com/github/srivtx/p-rick/blob/main/code/p-027-colab.ipynb): baseline parity at depth 240 with **no normalizer anywhere** (**97.3% ± 0.3** held-out vs ResNet 97.0 / ResNet+LN 97.4), the lowest forward norm growth of every architecture tested (31.8× vs 48.2× at depth 240), and the honest negative: spirals-2 unsolved by all four (57.6%). Rev 1.2 makes the normalization comparison precise — §4.6: LayerNorm guarantees a per-sample layer statistic, the stream an input-independent operator bound; the trained-model growth numbers exhibit the difference (LN 51.0× vs PH 31.8× at depth 240) — and the trunk-normalized follow-up ablation ships flag-gated in the harness. Site: [explainer — why no LayerNorm](https://srivtx.github.io/p-rick/layernorm.html). Integrator choice is normalization choice. |
| **P-028** | [The Anchor Law](https://srivtx.github.io/p-rick/paper/p028.html) · [src](papers/p-028-anchor-law.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-028.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p028.html) · [figures](figures/p-028/) | Agentic maintenance, computed: the floor **E[L∞] = (1−a)h²/(2(2ημ−(ημ)²)) + as²/2** (exact, 1.7% median), the ratchet **ρ_R = k·E max(0, N(δ,h²))** (0.17%, invisible to behavior anchors — 0.8% leak), and the stability boundary **a*(h) ≈ 1 − κ/h²** (0.041): required coverage falls quadratically as models improve. Tests are contraction, not verification; complexity budgets, not tests, stop the ratchet. |
| **P-029** | [The Lock-In Law](https://srivtx.github.io/p-rick/paper/p029.html) · [src](papers/p-029-lock-in-law.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-029.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p029.html) · [figures](figures/p-029/) | Groupthink has a formula: the collective bifurcates at **K_c = T(1−λ)** — coupling and temperature exchange one-for-one, no useful middle (mixed-phase coherence never exceeds 0.031 across 420 replicas). Locked confidence is the fixed point **m(1−λ) = K tanh(m/T)** (validated to **0.045%**); locking time ∝ ln N·T/(K−K_c); the diversity firewall **K_c(f) = T(1−(1−f)λ)** (0.020); the reset interval is the locking time. Top-p truncation: a reported null (1.06×) on binary collectives. |
| **P-030** | [The Green's Function of Context](https://srivtx.github.io/p-rick/paper/p030.html) · [src](papers/p-030-greens-function-context.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-030.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p030.html) · [figures](figures/p-030/) | Context rot has an object: the positional kernel's impulse response. The recall profile is the kernel smeared by noise (**0.037**); the lost-in-the-middle dip lands exactly on its closed form (**2771 = 2771**); windows collapse with load exactly as the extreme-value law computes (96/96, 75/75, 58/58); and the **monotonicity theorem** says uniform recall is impossible with timescales alone — it takes a **register**, which measures flat recall at floor 1.000 with order dead at the theoretical 0.500. The window-order law prices uniformity against order by the decade (0.92 → 0.60 vs law 0.95 → 0.61). |

### Series VII — collapse: critical thresholds where everyday infrastructure fails abruptly

Systems the field navigates by folklore, failing at thresholds nobody has written
down. Each paper derives the threshold, validates it in seeded simulation, and ships
the harness. 18 figures, all regenerable from `code/`.

| ID | Paper | The derived law |
|----|-------|-----------------|
| **P-024** | [Resolution Collapse](https://srivtx.github.io/p-rick/paper/p024.html) · [src](papers/p-024-resolution-collapse.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-024.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p024.html) · [figures](figures/p-024/) | Dependency resolution fails as a phase transition with the first-moment bound **D_c ≤ ln K / ln(K/w)** (exact on the cyclic version space, brute-force-verified) and a measured gap law **D_c ≈ 0.71·D_fm** under a uniform budget — the constant labeled configuration-specific per the program's post-P-023 rule. Version growth at fixed range width is fragility, at proportional width slow slack (the proliferation paradox); crisis-pruning feedback alone pins a growing ecosystem just below its collapse threshold (near-criticality as an emergent property); pruning old versions is the two-sided lever (removes satisfiability, buys searchability). |
| **P-025** | [The Collapse Law](https://srivtx.github.io/p-rick/paper/p025.html) · [src](papers/p-025-collapse-law.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-025.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p025.html) · [figures](figures/p-025/) | The retry storm's two thresholds — **rev 1.1, audited**: the ceiling **λ_c = μθρ*²/(1+θρ*)** and the recovery threshold **λ_r = μ/R** are the maximum and endpoint of one fixed-point curve, λ = μρ(1−q)/(1−q^R). New: bistability exists only when **(R−1)θ > 2**, and with unlimited retries λ_r = 0 — a collapsed system at 5% load *grows* its queue (measured 17-fold) instead of draining; restart is the only exit. Multi-seed re-measurement with error bars: tipping-probability curves saturate at the ceiling; queue caps inside the horizon eliminate the crater (loop gain q_L·R < 1). v1.0's single-seed claims (−36% backoff resonance, 81% jitter margin) withdrawn in Appendix B — the paper documents its own external audit. |
| **P-026** | [The Cascade Law of Credential Reuse](https://srivtx.github.io/p-rick/paper/p026.html) · [src](papers/p-026-credential-cascade.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-026.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p026.html) · [figures](figures/p-026/) | The account-takeover cascade computed: exact blast-radius law **F_w = E[(k−j)1{j≥1}]/(s(1−b))** (validated 0.2%), exact decomposition **F = F_w + (1−λ)F_s**, and the concentration law with a separatrix at popularity exponent **β\* ≈ 1** — dilute cascades below (risk grows with the user base), backbone cascades above (risk set by the first breach, where real corpora sit). Defense asymmetry: lockouts are the only herd lever; adoption's herd threshold is 99.997%. |

### Series VI — laws: from specification to derivation

The program's quantitative turn: not what should be built, but what is already
true and merely uncomputed. Each paper derives a law, validates it in seeded
simulation, and ships the harness. 16 figures, all regenerable from `code/`.

| ID | Paper | The derived law |
|----|-------|-----------------|
| **P-021** | [The Reproduction Number of Code](https://srivtx.github.io/p-rick/paper/p021.html) · [src](papers/p-021-reproduction-number-of-code.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-021.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p021.html) · [figures](figures/p-021/) | Epidemic thresholds for dependency-borne compromise: the spectral threshold on a registry DAG is exactly zero (nilpotence), the true threshold is the branching law **R₀ᵛ = T·⟨d⟩**, the thresholdless regime sits below degree exponent 2 — where real registries live — cascade-aware pinning buys herd immunity at one-eighth the random budget, and the registry yank has a two-step half-life. Validated across 28 configurations with a measured extinction drag θ ≈ 0.4–0.6. |
| **P-022** | [The Admission Law](https://srivtx.github.io/p-rick/paper/p022.html) · [src](papers/p-022-admission-law.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-022.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p022.html) · [figures](figures/p-022/) | The closed-form cache admission threshold under Zipf demand with transients: **τ\* = (1−f)W / (H·B^α)** — the threshold tracks stable evidence (not pollution, which any τ ≥ 2 excludes structurally), doors tighten with demand flatness, and the door legally disables itself when capacity covers the head. Dual: the capacity tax prices the unfiltered cache at f/(1−f) of its memory. Argmax matches the closed form within 1% where the choice matters; gains to 137%. |
| **P-023** | [Generation Loss](https://srivtx.github.io/p-rick/paper/p023.html) · [src](papers/p-023-generation-loss.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-023.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p023.html) · [figures](figures/p-023/) | The drift law for continually re-embedded vector corpora: **D(g) = 1−λ^g** with λ the product of an isometry channel (dimension-merced: 2(1−c)/d, removable exactly by Procrustes anchoring) and a distortion channel (dimension-free, un-alignable — the entire real cost of encoder churn). Validated to three decimals; anchored stale vectors hold ~2× recall at a rounding error of cost. **Rev 1.1:** the draft's "L≈8d" landmark constant is withdrawn and replaced by a derived estimation theorem — the panel budget is a four-factor law (accumulated distortion √g·ν, panel–corpus coverage mismatch, estimator class, tolerance) validated by knee-migration experiments (F6/F7, 6/7 predictions within 11%); an undersized panel is proven actively harmful (worse than no anchoring); new harness `code/p-023b-landmark-budget.py`. |

### Series V — promises: the guarantees software implies and never has to honor

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-017** | [The Revocation Protocol](https://srivtx.github.io/p-rick/paper/p017.html) · [src](papers/p-017-revocation-protocol.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-017.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p017.html) | Consent withdrawal as a propagation guarantee: grant objects with lineage, revocation events with coverage semantics, signed receipts, re-attestation cycles, canary audits, and the liability ladder that turns silence into evidence — the certificate ecosystem's short-lived-cert lesson applied to the most repeated promise in software. |
| **P-018** | [Epistemic Half-Life](https://srivtx.github.io/p-rick/paper/p018.html) · [src](papers/p-018-epistemic-half-life.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-018.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p018.html) | Truth decay semantics for stored data: decay functions with half-life families, confidence-aware queries, an honest join algebra, half-lives estimated from your own change streams, budgeted verification scheduling, and staleness as an outage class. |
| **P-019** | [Dormancy Engineering](https://srivtx.github.io/p-rick/paper/p019.html) · [src](papers/p-019-dormancy-engineering.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-019.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p019.html) | Software design for the long sleep: dormancy classes with declared wake bounds, the environment-drift ledger, the wake-probe ladder from checksums to germination tests, the exercise calendar, and the readiness contract for software that must work after years of not running. |
| **P-020** | [Blast Radius Engineering](https://srivtx.github.io/p-rick/paper/p020.html) · [src](papers/p-020-blast-radius-engineering.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-020.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p020.html) | Personal reliability engineering for correlated failure: the personal dependency graph, eight correlation classes, weighted blast radii, composite-availability arithmetic, budgeted decorrelation placement, the failure weather report, and the annual kill-one-root drill. |

### Series IV — assumptions: the quiet premises software runs on

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-012** | [The Complexity Ledger](https://srivtx.github.io/p-rick/paper/p012.html) · [src](papers/p-012-complexity-ledger.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-012.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p012.html) | Design as relocation, accounted: Tesler's conservation of complexity as a falsifiable theory, five measured sinks, double-entry relocation records, complexity budgets, and the consent principle that separates trades from externalities. |
| **P-013** | [Delegated Operation](https://srivtx.github.io/p-rick/paper/p013.html) · [src](papers/p-013-delegated-operation.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-013.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p013.html) | Multi-principal software: the operator principal, capability bundles instead of credential handover, a graduated autonomy ladder, drift detection, and succession semantics for the 53 million caregivers running someone else's digital life. |
| **P-014** | [Modality Failover](https://srivtx.github.io/p-rick/paper/p014.html) · [src](papers/p-014-modality-failover.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-014.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p014.html) | Cross-sensory redundancy for critical alerts: criticality classes, private capability profiles, k-of-n delivery, acknowledgment-gated escalation across modalities, devices, and people — RAID for the senses. |
| **P-015** | [The Uncertain Document](https://srivtx.github.io/p-rick/paper/p015.html) · [src](papers/p-015-uncertain-document.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-015.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p015.html) | Uncertainty as a native property of everyday numbers: the quant type, tiered propagation, a calibrated display contract, an assumption registry, and the calibration ledger that lets an organization learn its own bias. |
| **P-016** | [The Defaults Ledger](https://srivtx.github.io/p-rick/paper/p016.html) · [src](papers/p-016-defaults-ledger.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-016.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p016.html) | Governance for the strongest force in software: defaults manifests with provenance, drift notification, portable override registries, negotiation layers, and impact assessments for population-scale configuration. |

### Series III — continuity: what systems lose over time

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-008** | [The Afterlife of Devices](https://srivtx.github.io/p-rick/paper/p008.html) · [src](papers/p-008-afterlife-of-devices.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-008.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p008.html) | Vendor-death resilience for connected hardware: succession manifests, escrowed firmware with dead-hand release, threshold key ceremonies, a degradation ladder, and a hardware-guaranteed fossil mode. |
| **P-009** | [Circadian Orchestration](https://srivtx.github.io/p-rick/paper/p009.html) · [src](papers/p-009-circadian-orchestration.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-009.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p009.html) | Team scheduling on human biological time: private phase estimation, circadian cost functions, fairness-constrained placement, and the golden overlap — privacy by construction. |
| **P-010** | [The Bus Factor Protocol](https://srivtx.github.io/p-rick/paper/p010.html) · [src](papers/p-010-bus-factor-protocol.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-010.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p010.html) | Succession governance for package registries: legible maintainer state, policy as code, dormancy escalation, the anti-xz trust-elevation ladder, and a public continuity ledger. |
| **P-011** | [Model Extinction](https://srivtx.github.io/p-rick/paper/p011.html) · [src](papers/p-011-model-extinction.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-011.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p011.html) | Behavioral conservation for disposable AI: behavioral fingerprints, equivalence testing for replacements, an extinction registry, inference-time provenance, deprecation contracts. |

### Series II — systems

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-004** | [Degradation Contracts](https://srivtx.github.io/p-rick/paper/p004.html) · [src](papers/p-004-degradation-contracts.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-004.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p004.html) | A formal language + runtime that makes *how software behaves under resource pressure* declarable, enforceable, and auditable — instead of accidental. |
| **P-005** | [Provenance-Native Storage](https://srivtx.github.io/p-rick/paper/p005.html) · [src](papers/p-005-provenance-native-storage.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-005.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p005.html) | The file system as a causal ledger: every file remembers where it came from, what produced it, and what depends on it. |
| **P-006** | [The Attention Scheduler](https://srivtx.github.io/p-rick/paper/p006.html) · [src](papers/p-006-attention-scheduler.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-006.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p006.html) | Human attention as a first-class OS-schedulable resource: cost models, admission control, budgets with honesty pricing, latency guarantees, an attention ledger. |
| **P-007** | [The Intermittent Compute Fabric](https://srivtx.github.io/p-rick/paper/p007.html) · [src](papers/p-007-intermittent-compute-fabric.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-007.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p007.html) | One schedulable machine across a person's devices: partition-tolerant placement, capability delegation, ambient CRDT state — the host for local AI. |

### Series I — user-owned data & the economics of inattention (originated in srivtx/pocketveto, moved here)

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-001** | [The Personal Event Bus](https://srivtx.github.io/p-rick/paper/p001.html) · [src](papers/p-001-personal-event-bus.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-001.pdf) | User-owned middleware that captures and keeps ambient digital-life events (payment events, receipts, gate changes) instead of throwing them away. |
| **P-002** | [Consumer Entitlements as Dead Capital](https://srivtx.github.io/p-rick/paper/p002.html) · [src](papers/p-002-consumer-rights-dead-capital.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-002.pdf) | The personal entitlement engine: consumer rights as machine-readable objects with detection, valuation, and execution. |
| **P-003** | [The n=1 Cost-of-Living Index](https://srivtx.github.io/p-rick/paper/p003.html) · [src](papers/p-003-n1-cost-of-living-index.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-003.pdf) | A statistically defensible personal price index — the methodology layer no consumer software has. |

## The method

The full statement lives on the site: [the method page](https://srivtx.github.io/p-rick/method.html). The short version:

1. **The bar — four tests, all mandatory.** Real recurring problem; large audience; empty
   category (verified, falsifiable, incumbents named); specifiable (formal model, protocol,
   architecture — something a builder could implement and an evaluator could test).
2. **The exclusions — hard rules.** No toy projects. No deterministic wrappers, test suites,
   or verification gadgets whose only user is their own construction. Nothing AI-obsolete.
   No CRUD, no chatbot shells, no me-too products. The program specifies missing *systems*.
3. **Gap research before writing.** Every direction survives a landscape survey before a
   paper is started; directions that die in survey die quietly (the survey notes survive in
   the work log).
4. **Falsifiable gaps, not vibes.** "No system does X" is written so one search can refute it;
   "component PARTIAL, composition STRONG" is an honest verdict the program uses.
5. **Honest grading.** STRONG / PARTIAL / WEAK verdicts on the evidence, stated in the paper.
6. **Specification over prototype theater.** Formal models, architectures, and evaluation
   designs — the artifacts a builder actually needs — before any code.
7. **Red-team pass.** Adversarial review of novelty claims, headline figures, formal
   properties, and cross-paper consistency; findings are fixed, not footnoted.
8. **Essays with every paper.** Each paper has a companion essay in plain language, written
   the way technical leaders write, because research that nobody reads is a diary.
9. **Citation honesty.** References recorded from domain knowledge are marked *verification
   queued* and pass through a live-source verification ledger before final release.
10. **Automatic work tracking.** [`agents.md`](agents.md) is the session ledger — nobody has to
    remember or ask how long anything took.

## Repository layout

```
p-rick/
├── index.html            # the research site (GitHub Pages, dark + light mode)
├── papers.html, blog.html, method.html, 404.html
├── paper/p001–p030.html  # designed reading editions of every paper (generated)
├── blog/p001–p030.html   # essay pages (generated)
├── feed.xml, sitemap.xml, robots.txt, og-image.png
├── assets/               # style.css (dual theme) + paper.css + theme.js + reveal.js + favicon.svg
├── papers/               # paper sources (markdown)
├── pdfs/                 # typeset papers (PDF)
├── figures/              # series VI–VIII simulation figures + results.json (per paper)
├── code/                 # series VI–VIII reproduction harnesses (one file per paper)
├── blogs/                # essay sources (markdown)
├── tools/build_site.py   # regenerates blog pages + feed.xml + sitemap.xml
└── agents.md             # the automatic work ledger
```

The site deploys from the repo root on push to `main` (GitHub Pages, static, `.nojekyll`).

## Reproduce

Every paper opens as a full reading edition on the site — abstract, sticky contents with
scrollspy, numbered figures with captions, KaTeX-typeset math, theorem boxes, prev/next
navigation, and a BibTeX block. The typeset PDF stays the edition of record; the
markdown source is one click away on every page.

```bash
git clone https://github.com/srivtx/p-rick.git
cd p-rick

# regenerate any paper's figures + results.json (seeded, deterministic)
python3 code/p-027-simulation.py     # then diff against figures/p-027/

# regenerate the reading editions (paper/p001–p030.html) after editing papers/*.md
python3 tools/build_paper_pages.py

# regenerate blog pages, RSS feed, and sitemap after editing blogs/*.md
python3 tools/build_site.py

# P-027 E6 training sweep (96 runs, 4
# architectures, 3 seeds) runs off-box on a free Colab T4:
# https://colab.research.google.com/github/srivtx/p-rick/blob/main/code/p-027-colab.ipynb
```

Every figure regenerates bit-exact from its seeded harness: rerun any
`code/p-NNN-simulation.py` and diff. PDFs are typeset from `papers/*.md` via LaTeX
(Tectonic) with composed covers; sources of the conversion pipeline are kept by the
research program workspace and documented in `agents.md`.

## Citing

BibTeX for all thirty papers is on the site's [papers page](https://srivtx.github.io/p-rick/papers.html#cite).
Each entry cites the PDF (the typeset, canonical form).

## agents.md — automatic work tracking

Every work session (human, AI, or hybrid) appends one record to [`agents.md`](agents.md):
what was done, when, how long, and links to artifacts. Read the last record to see where
things stand; append a record when you finish work. The ledger is the source of truth for
effort, output, and lineage — so nobody has to know how long we have worked; the file knows.

## Program status

- **Series VIII complete (4 papers) — machinery: mechanisms invented, not just found.**
  The conservation architecture for depth (P-027), the convergence law of agentic
  maintenance (P-028), the lock-in transition of agent collectives (P-029), and the
  Green's function of context (P-030). Four law sets, four seeded harnesses, 24 figures;
  the program's second arc opens.
- Series VII complete (3 papers) — collapse: critical thresholds where everyday infrastructure
  fails abruptly. Dependency resolution's satisfiability threshold (P-024), the retry storm's
  capacity ceiling and recovery threshold (P-025), the credential cascade's concentration
  separatrix (P-026).
- Series VI complete (3 papers) — laws: from specification to derivation (P-023 rev 1.1:
  the L≈8d constant withdrawn and replaced by the Landmark Estimation Law).
- Series V complete (4 papers) — promises. Series IV complete (5 papers) — assumptions.
  Series III complete (4 papers) — continuity. Series II complete (4 papers) — systems.
  Series I complete (3 papers) — user-owned data: originated in `srivtx/pocketveto`, moved
  to this repository when the program outgrew its host.
- **Thirty papers, thirty essays, thirty PDFs, eight series, zero incumbents in-gap — and
  ten validated law sets with 61 reproducible figures.**
- **Next:** product directories (one per validated direction) — created only after the
  research is finished, per the program charter.

## License

MIT for code — see [LICENSE](LICENSE). Papers and essays: CC BY 4.0 for the text; cite the paper ID.

