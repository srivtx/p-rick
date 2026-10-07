---
title: "Your Dependencies Have an R₀. Nobody Computed It."
date: 2026-10-07
author: p-rick research program
paper: p-021-reproduction-number-of-code
---

# Your Dependencies Have an R₀. Nobody Computed It.

When a package gets compromised, our industry tells stories. Event-stream. ua-parser-js. The 2024 wave. We narrate the blast radius afterward, with the reverence of historians describing a battle nobody tried to model before it started.

Epidemiologists don't do this. In 2020, nobody waited for the outbreak to finish to start talking about R₀ — the reproduction number, the count of new infections each infection causes. R₀ below 1, the disease dies on its own. Above 1, it grows. That single number decides whether you're having an incident or a catastrophe, and it's computable *before* either.

We ran the mathematics on package registries, and the result is a paper: [The Reproduction Number of Code](pdfs/p-021-reproduction-number-of-code.pdf). Three findings, one of them embarrassing for the industry, one of them useful tonight, and one of them a clock nobody is watching.

## First, the embarrassing one

You know what everyone computes on dependency graphs to gauge systemic risk? The spectral radius. It's the textbook move — the number that determines whether epidemics go macroscopic on networks.

**On a dependency graph, it's exactly zero. Always.** Dependency graphs are DAGs — acyclic by construction, because you can't depend on a package that depends on you. A triangular matrix's eigenvalues are all zero. Every spectral "risk score" computed on a registry snapshot is certifying safety in the same breath as it certifies nothing. It's not an approximation that's slightly off. It's a category error, and it's sitting in slide decks right now.

## The number that actually matters

The correct threshold on a DAG is embarrassingly simple: **R₀ = T × ⟨d⟩** — the per-edge transmission probability times the average number of dependents per package. One infected build propagating into twenty downstream builds per cycle, at a one-in-twenty transmission rate, is exactly critical.

We validated this in simulation across 28 configurations — outbreak probability against the Galton–Watson prediction, and the law tracks with a systematic drag we measured rather than hid (θ ≈ 0.4–0.6: the law over-predicts danger, which is the correct direction for a safety bound).

Here's the part that should keep registry operators up: real registries are heavy-tailed, and for exponents below 2 — which is where the reported npm/PyPI numbers live — the mean dependents count *grows with registry size*. The threshold falls toward zero as the registry grows. In the limit: no safe transmission rate. Finite size is the only mercy. We watched it happen: sixteen-fold registry growth, threshold halved.

## The finding you can use tonight

Two numbers, straight out of the paper:

**The pinning budget.** If your ecosystem is supercritical at R₀ = 11, random pinning needs 91% of packages locked to bring it below 1 — that's the herd-immunity arithmetic, and it's why "everyone should pin" is a fantasy. But pinning the *right* packages — by dependents count, or one level deeper, by cascade reachability — collapses the cascade at **one-eighth of the budget**. Top decile by dependents. That's the allowlist. And the signal doesn't even need to be clean: we added 30% noise to the popularity data and it barely mattered.

**The response clock.** This is the one that made me sit back. We ran paired epidemics — same random stream, interventions at different times. A registry *yank* is worth nothing after about five cascade steps. After the first couple of steps, the compromised package isn't the frontier anymore; the cascade has moved to younger, mid-popularity packages the yank can't touch. The yank's half-life is between one and two steps. If your detection-to-yank pipeline is slower than your ecosystem's build cadence — by even a little — you're not running a containment process. You're running a press release.

## Why this is a laws paper

The series I–V of this program specified missing systems. This one does something different: it writes down mathematics that was already true. The dependency graph was measurable for a decade. The SIR model is seventy years old. The branching threshold is textbook. Nobody put them together and handed registry operators arithmetic they could run tonight.

Every figure in the paper regenerates from one file with published seeds. The formulas need two telemetry numbers registries already have or could collect in a week: mean dependents count and patch-latency distribution. Compute your R₀. Find out which regime you're in. The answer is either "you're safe, here's the margin" or "you're supercritical, here's the pinning budget and the response clock" — and you'd know *before* the next event-stream, instead of after.

That's the whole thesis: stop narrating outbreaks. Start computing them.
