<div align="center">

# p-rick

**Software the world is missing — specified before anyone builds it.**

[![Site](https://img.shields.io/website?down_message=offline&label=research%20site&up_color=%233ddc97&up_message=online&url=https%3A%2F%2Fsrivtx.github.io%2Fp-rick%2Findex.html&style=flat-square)](https://srivtx.github.io/p-rick/)
[![Papers](https://img.shields.io/badge/papers-23%20working-8B7E5A?style=flat-square&labelColor=162032)](https://srivtx.github.io/p-rick/papers.html)
[![Series](https://img.shields.io/badge/series-6%20arcs-8B7E5A?style=flat-square&labelColor=162032)](https://srivtx.github.io/p-rick/papers.html)
[![Essays](https://img.shields.io/badge/essays-23-8B7E5A?style=flat-square&labelColor=162032)](https://srivtx.github.io/p-rick/blog.html)
[![Figures](https://img.shields.io/badge/figures-16%20validated-CC3311?style=flat-square&labelColor=162032)](figures/)
[![Reproducible](https://img.shields.io/badge/simulations-seeded%20%2B%20reproducible-009988?style=flat-square&labelColor=162032)](code/)
[![Papers license: CC BY 4.0](https://img.shields.io/badge/paper%20license-CC%20BY%204.0-3ddc97?style=flat-square)](https://creativecommons.org/licenses/by/4.0/)
[![Code license: MIT](https://img.shields.io/badge/code%20license-MIT-3ddc97?style=flat-square)](LICENSE)
[![RSS](https://img.shields.io/badge/RSS-feed-F26522?style=flat-square)](https://srivtx.github.io/p-rick/feed.xml)
[![GitHub stars](https://img.shields.io/github/stars/srivtx/p-rick?style=flat-square&color=8B7E5A&label=stars)](https://github.com/srivtx/p-rick/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/srivtx/p-rick?style=flat-square&color=162032)](https://github.com/srivtx/p-rick/commits/main)

[Research site](https://srivtx.github.io/p-rick/) · [Papers](https://srivtx.github.io/p-rick/papers.html) · [Blog](https://srivtx.github.io/p-rick/blog.html) · [The method](https://srivtx.github.io/p-rick/method.html) · [RSS](https://srivtx.github.io/p-rick/feed.xml)

</div>

---

**p-rick** is an independent research program that hunts for genuine gaps in the software
landscape — categories with no incumbents, problems with large audiences, theories nobody
has written down — and does the research to close them: landscape verification against
everything that exists, formal models, reference architectures, evaluation designs, and
honest confrontation with the reasons each gap survived. Every paper ships with a typeset
PDF and a plain-language essay written the way technical leaders write.

The program's operating rule is **research first; products later** — papers and
specifications before code, in separate directories, only after the research freezes.
Twenty-three working papers are published across six series. Series I-V specify
missing systems — each stating its gap as a
falsifiable claim with named incumbents and honest evidence grading. The bar, the
exclusions, and the red-team discipline are codified on
[the method page](https://srivtx.github.io/p-rick/method.html).

> The exclusions are hard rules: no toy projects, no deterministic wrappers, no test
> suites, no verification gadgets whose only user is their own construction, nothing
> AI-obsolete, no CRUD, no chatbot shells. The program specifies missing *systems* —
> software that has never been built because nobody wrote down what it would be.

## The papers

### Series VI — laws: from specification to derivation (current)

The program's quantitative turn: not what should be built, but what is already
true and merely uncomputed. Each paper derives a law, validates it in seeded
simulation, and ships the harness. 16 figures, all regenerable from `code/`.

| ID | Paper | The derived law |
|----|-------|-----------------|
| **P-021** | [The Reproduction Number of Code](papers/p-021-reproduction-number-of-code.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-021.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p021.html) · [figures](figures/p-021/) | Epidemic thresholds for dependency-borne compromise: the spectral threshold on a registry DAG is exactly zero (nilpotence), the true threshold is the branching law **R₀ᵛ = T·⟨d⟩**, the thresholdless regime sits below degree exponent 2 — where real registries live — cascade-aware pinning buys herd immunity at one-eighth the random budget, and the registry yank has a two-step half-life. Validated across 28 configurations with a measured extinction drag θ ≈ 0.4–0.6. |
| **P-022** | [The Admission Law](papers/p-022-admission-law.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-022.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p022.html) · [figures](figures/p-022/) | The closed-form cache admission threshold under Zipf demand with transients: **τ\* = (1−f)W / (H·B^α)** — the threshold tracks stable evidence (not pollution, which any τ ≥ 2 excludes structurally), doors tighten with demand flatness, and the door legally disables itself when capacity covers the head. Dual: the capacity tax prices the unfiltered cache at f/(1−f) of its memory. Argmax matches the closed form within 1% where the choice matters; gains to 137%. |
| **P-023** | [Generation Loss](papers/p-023-generation-loss.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-023.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p023.html) · [figures](figures/p-023/) | The drift law for continually re-embedded vector corpora: **D(g) = 1−λ^g** with λ the product of an isometry channel (dimension-mercied: 2(1−c)/d, removable exactly by Procrustes anchoring) and a distortion channel (dimension-free, un-alignable — the entire real cost of encoder churn). Validated to three decimals; anchored stale vectors hold ~2× recall at a rounding error of cost. **Rev 1.1:** the draft's "L≈8d" landmark constant is withdrawn and replaced by a derived estimation theorem — the panel budget is a four-factor law (accumulated distortion √g·ν, panel–corpus coverage mismatch, estimator class, tolerance) validated by knee-migration experiments (F6/F7, 6/7 predictions within 11%); an undersized panel is proven actively harmful (worse than no anchoring); new harness `code/p-023b-landmark-budget.py`. |

### Series V — promises: the guarantees software implies and never has to honor

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-017** | [The Revocation Protocol](papers/p-017-revocation-protocol.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-017.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p017.html) | Consent withdrawal as a propagation guarantee: grant objects with lineage, revocation events with coverage semantics, signed receipts, re-attestation cycles, canary audits, and the liability ladder that turns silence into evidence — the certificate ecosystem's short-lived-cert lesson applied to the most repeated promise in software. |
| **P-018** | [Epistemic Half-Life](papers/p-018-epistemic-half-life.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-018.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p018.html) | Truth decay semantics for stored data: decay functions with half-life families, confidence-aware queries, an honest join algebra, half-lives estimated from your own change streams, budgeted verification scheduling, and staleness as an outage class. |
| **P-019** | [Dormancy Engineering](papers/p-019-dormancy-engineering.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-019.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p019.html) | Software design for the long sleep: dormancy classes with declared wake bounds, the environment-drift ledger, the wake-probe ladder from checksums to germination tests, the exercise calendar, and the readiness contract for software that must work after years of not running. |
| **P-020** | [Blast Radius Engineering](papers/p-020-blast-radius-engineering.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-020.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p020.html) | Personal reliability engineering for correlated failure: the personal dependency graph, eight correlation classes, weighted blast radii, composite-availability arithmetic, budgeted decorrelation placement, the failure weather report, and the annual kill-one-root drill. |

### Series IV — assumptions: the quiet premises software runs on

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-012** | [The Complexity Ledger](papers/p-012-complexity-ledger.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-012.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p012.html) | Design as relocation, accounted: Tesler's conservation of complexity as a falsifiable theory, five measured sinks, double-entry relocation records, complexity budgets, and the consent principle that separates trades from externalities. |
| **P-013** | [Delegated Operation](papers/p-013-delegated-operation.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-013.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p013.html) | Multi-principal software: the operator principal, capability bundles instead of credential handover, a graduated autonomy ladder, drift detection, and succession semantics for the 53 million caregivers running someone else's digital life. |
| **P-014** | [Modality Failover](papers/p-014-modality-failover.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-014.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p014.html) | Cross-sensory redundancy for critical alerts: criticality classes, private capability profiles, k-of-n delivery, acknowledgment-gated escalation across modalities, devices, and people — RAID for the senses. |
| **P-015** | [The Uncertain Document](papers/p-015-uncertain-document.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-015.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p015.html) | Uncertainty as a native property of everyday numbers: the quant type, tiered propagation, a calibrated display contract, an assumption registry, and the calibration ledger that lets an organization learn its own bias. |
| **P-016** | [The Defaults Ledger](papers/p-016-defaults-ledger.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-016.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p016.html) | Governance for the strongest force in software: defaults manifests with provenance, drift notification, portable override registries, negotiation layers, and impact assessments for population-scale configuration. |

### Series III — continuity: what systems lose over time

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-008** | [The Afterlife of Devices](papers/p-008-afterlife-of-devices.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-008.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p008.html) | Vendor-death resilience for connected hardware: succession manifests, escrowed firmware with dead-hand release, threshold key ceremonies, a degradation ladder, and a hardware-guaranteed fossil mode. |
| **P-009** | [Circadian Orchestration](papers/p-009-circadian-orchestration.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-009.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p009.html) | Team scheduling on human biological time: private phase estimation, circadian cost functions, fairness-constrained placement, and the golden overlap — privacy by construction. |
| **P-010** | [The Bus Factor Protocol](papers/p-010-bus-factor-protocol.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-010.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p010.html) | Succession governance for package registries: legible maintainer state, policy as code, dormancy escalation, the anti-xz trust-elevation ladder, and a public continuity ledger. |
| **P-011** | [Model Extinction](papers/p-011-model-extinction.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-011.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p011.html) | Behavioral conservation for disposable AI: behavioral fingerprints, equivalence testing for replacements, an extinction registry, inference-time provenance, deprecation contracts. |

### Series II — systems

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-004** | [Degradation Contracts](papers/p-004-degradation-contracts.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-004.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p004.html) | A formal language + runtime that makes *how software behaves under resource pressure* declarable, enforceable, and auditable — instead of accidental. |
| **P-005** | [Provenance-Native Storage](papers/p-005-provenance-native-storage.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-005.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p005.html) | The file system as a causal ledger: every file remembers where it came from, what produced it, and what depends on it. |
| **P-006** | [The Attention Scheduler](papers/p-006-attention-scheduler.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-006.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p006.html) | Human attention as a first-class OS-schedulable resource: cost models, admission control, budgets with honesty pricing, latency guarantees, an attention ledger. |
| **P-007** | [The Intermittent Compute Fabric](papers/p-007-intermittent-compute-fabric.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-007.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p007.html) | One schedulable machine across a person's devices: partition-tolerant placement, capability delegation, ambient CRDT state — the host for local AI. |

### Series I — user-owned data & the economics of inattention (originated in srivtx/pocketveto, moved here)

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-001** | [The Personal Event Bus](papers/p-001-personal-event-bus.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-001.pdf) | User-owned middleware that captures and keeps ambient digital-life events (payment events, receipts, gate changes) instead of throwing them away. |
| **P-002** | [Consumer Entitlements as Dead Capital](papers/p-002-consumer-rights-dead-capital.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-002.pdf) | The personal entitlement engine: consumer rights as machine-readable objects with detection, valuation, and execution. |
| **P-003** | [The n=1 Cost-of-Living Index](papers/p-003-n1-cost-of-living-index.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-003.pdf) | A statistically defensible personal price index — the methodology layer no consumer software has. |

Each paper follows the same discipline: state the gap as a **falsifiable claim**, grade the
evidence (STRONG / PARTIAL / WEAK), survey the adjacent systems that solve one slice, design
the system that closes the gap, and confront the strongest objections — including the ones
that might kill the thesis. Papers are working drafts; the ledger of revisions is
[`agents.md`](agents.md).

## The method

The full statement lives on the site: [the method page](https://srivtx.github.io/p-rick/method.html). Summary:

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
├── blog/*.html           # essay pages (generated)
├── feed.xml, sitemap.xml, robots.txt, og-image.png
├── assets/               # style.css (dual theme) + theme.js + favicon.svg
├── papers/               # paper sources (markdown)
├── pdfs/                 # typeset papers (PDF)
├── figures/              # series VI simulation figures + results.json (per paper)
├── code/                 # series VI reproduction harnesses (one file per paper)
├── blogs/                # essay sources (markdown)
├── tools/build_site.py   # regenerates blog pages + feed.xml + sitemap.xml
└── agents.md             # the automatic work ledger
```

The site deploys from the repo root on push to `main` (GitHub Pages, static, `.nojekyll`).

### Build / regenerate

```bash
# regenerate blog pages, RSS feed, and sitemap after editing blogs/*.md
python3 tools/build_site.py
```

PDFs are typeset from `papers/*.md` via LaTeX (Tectonic) with composed covers; sources of the
conversion pipeline are kept by the research program workspace and documented in `agents.md`.

## Citing

BibTeX for all twenty papers is on the site's [papers page](https://srivtx.github.io/p-rick/papers.html#cite).
Each entry cites the PDF (the typeset, canonical form).

## agents.md — automatic work tracking

Every work session (human, AI, or hybrid) appends one record to [`agents.md`](agents.md):
what was done, when, how long, and links to artifacts. Read the last record to see where
things stand; append a record when you finish work. The ledger is the source of truth for
effort, output, and lineage — so nobody has to know how long we have worked; the file knows.

## Program status

- Series I complete (3 papers) — originated in `srivtx/pocketveto`, moved to this repository
  when the program outgrew its host.
- Series II complete (4 papers) — systems gaps (degradation, provenance, attention, fabric),
  unrelated to Series I's personal-data topic territory.
- Series III complete (4 papers) — continuity: what systems lose over time. Vendor death
  (devices), biological time (circadian orchestration), maintainer mortality (bus factor
  protocol), behavioral extinction (model conservation). Zero overlap with Series I/II
  territory; all four directions pass the bar with no incumbents in-gap.
- Series IV complete (5 papers) — assumptions: the quiet premises software runs on. Complexity
  conservation (the complexity ledger), single-principal identity (delegated operation),
  sensory availability (modality failover), point-estimate numbers (the uncertain document),
  default neutrality (the defaults ledger). Zero overlap with Series I–III territory.
- Series V complete (4 papers) — promises: the guarantees software implies and never has to
  honor. Withdrawal that propagates (the revocation protocol), facts that stay true
  (epistemic half-life), dormant software that wakes (dormancy engineering), independence
  under failure (blast radius engineering). Zero overlap with Series I–IV territory; all
  four directions pass the bar with no incumbents in-gap.
- **Twenty-three papers, twenty-three essays, twenty-three PDFs, six series, zero incumbents in-gap — and three validated laws with 16 reproducible figures.**
- **Next:** product directories (one per validated direction) — created only after the
  research is finished, per the program charter.

## License

MIT for code — see [LICENSE](LICENSE). Papers and essays: CC BY 4.0 for the text; cite the paper ID.
