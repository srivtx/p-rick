---
title: "The Agent Eats What You Don't Pin"
date: 2026-10-09
author: p-rick research program
paper: p-028-anchor-law
---

# The Agent Eats What You Don't Pin

You're about to hand your repository to an agent. Maybe you already have. The question you're actually asking, whether you've phrased it or not, is: *how many tests do I need first?*

The folklore answer is "good coverage," said with varying confidence. The real answer is arithmetic, and we wrote it down: [The Anchor Law](pdfs/p-028.pdf).

## The loop has a floor

Model the codebase as a point in a space with two halves: behavior (what the system does — the part tests can pin) and complexity (how much machinery it takes — the part that grows). One agent pass moves the behavior toward spec at your review rate, but every pass also injects entropy — the model's irreducible proposal variance, its temperature made structural — and the proposals lean toward addition: wrapping, guarding, special-casing. Machinery goes up. Almost nothing brings it down.

Tests are anchors. They pin a fraction $a$ of behavior to whatever it was doing the day they were written — including its bugs. The law that falls out of the model is exact and a little ruthless:

**The maintenance floor** = un-anchored noise (quadratic in agent entropy) + frozen legacy error (linear in coverage). The floor is *linear* in coverage. That linearity has a consequence nobody prices: anchors substitute for entropy at a fixed exchange rate, and the floor has a hard bottom — pin everything, and you've frozen the codebase exactly where it was, current bugs included. **Anchors preserve. They do not repair.**

## Three findings the folklore misses

**1. The boundary is quadratic.** Below a coverage level $a^*(h)$, the loop never converges — it degrades forever, passing your tests the whole way. And the required coverage falls with the *square* of agent entropy: halve the entropy, and the uncovered fraction you need drops by three quarters. In our harness parameters, a 50%-entropy agent needs 76% of behavior pinned; a 100%-entropy agent needs 96%. That curve is the contract you can sign with your agent fleet — the quantitative version of "how good does the model have to be before we lower the coverage bar."

**2. Tests do not stop the ratchet.** This is the one that surprised us, and the harness is blunt about it: behavior anchors left 99.2% of the complexity drift untouched. Orthogonal channels. Your test suite, at whatever coverage, is invisible to the mechanism that makes your codebase heavier every quarter. The instrument that stops it is a different kind of anchor: a complexity cap. A budget. A lint ceiling. "Reject any PR that grows the branch count" is not a style preference; it's the only pin that works on the channel that's actually drifting.

**3. Over-anchoring is also failure.** If the codebase was already out of spec when the anchors went in, no coverage number saves you — the frozen error sits above tolerance forever. Improvement has to come through the un-anchored channel first. Teams that answer every change-averse instinct with "lock it down more" are buying the legacy term with money they meant to spend on the noise term.

## The doctrine

So the practitioner's checklist, in order: coverage above the boundary (the quadratic curve tells you where), a complexity budget on the ratchet (tests can't do this job), and a review rate you're honest about (faster review is a better model, at the same exchange rate).

And the uncomfortable framing we'd leave you with: your tests were never verification. They're contraction. They don't prove the agent right — they bound how wrong it can drift before the pin catches. Below the boundary, every pass is rent the codebase pays to the entropy. Above it, the loop converges. The number in between is the paper.

*Read the paper: [The Anchor Law](pdfs/p-028.pdf) · [reading edition](../paper/p028.html) · [harness](https://github.com/srivtx/p-rick/blob/main/code/p-028-simulation.py)*
