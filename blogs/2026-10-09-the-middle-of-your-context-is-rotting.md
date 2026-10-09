---
title: "The Middle of Your Context Is Rotting (Design It Away)"
date: 2026-10-09
author: p-rick research program
paper: p-030-greens-function-context
---

# The Middle of Your Context Is Rotting (Design It Away)

Lost in the middle is one of the most replicated findings of the long-context era: stuff at the beginning of your prompt gets recalled, stuff at the end gets recalled, and the middle quietly rots. Then the rot deepens as you fill the window. The field's response has been tuning — flatter biases here, an extension scheme there — adjusting the symptom against benchmarks.

We think the whole thing is easier once you name the object underneath. A context window has a **Green's function**: the impulse response of its positional channel, the effective weight an item retains as a function of distance behind the query. Call it $K(\Delta)$. The paper — [The Green's Function of Context](pdfs/p-030.pdf) — shows that once you have $K$, every pathology is a closed-form functional of it. The recall profile *is* the kernel, smeared by noise. Measure the kernel; you've measured the model's memory.

## The U-curve has an address

The canonical kernel — a fast timescale for recency, a slow one for primacy, an attention sink at the window head — is U-shaped, and the recall curve inherits the U. The paper derives the dip's location in closed form: where the sink's growth balances the slow channel's decay. In the harness: predicted 2771, measured 2771. The most famous curve in long-context evaluation is one line of calculus.

## The theorem nobody wrote

Here's the finding I'd bet the paper on. A positional kernel built from decaying timescales — any number of them, any weights — is **strictly decreasing**. Monotone. A positive mixture of exponentials cannot be uniform on any interval. Which means:

**Uniform recall is impossible with timescales alone.** You cannot schedule your way to a flat memory. Ladders of timescales (the state-space machinery everyone's adopting) decay a power of three per decade — flatter than any single scale, still rotting.

Uniform recall requires a channel that doesn't decay at all — a **register**: a permanent component that holds every item at equal weight, with the decaying ladder riding on top for discrimination. In the harness, the register kernel measured flat recall at floor 1.000 across three decades at load, with order-resolution dead at the theoretical 0.500. Two retrieval functions, two channels, one kernel.

## The trade

And of course it's not free. The register holds everything equally — it can't tell you which of two similar things came *last*. That's the decaying ladder's job. The law: uniformity and order trade linearly in decades of window — hold a 90% recall floor over half a decade and you keep 0.92 order resolution; stretch the uniform window to three decades and order falls to 0.60. Every decade of "remember everything equally" costs the same slice of "remember what order it happened in." Measured 0.92 → 0.60 against the law's 0.95 → 0.61.

So the design space is a frontier, not a free lunch — and that's the point. Right now every architecture lands somewhere on this frontier by accident, by gradient descent on something else. The paper's proposal: pick your task mix (item recall vs. order resolution), solve the inverse problem for the kernel weights — it's a least-squares on a channel basis, minutes of compute — and take your position on the frontier on purpose.

Context rot isn't a defect. It's the Green's function of a kernel nobody designed. Design the kernel, and the pathology becomes a specification.

*Read the paper: [The Green's Function of Context](pdfs/p-030.pdf) · [reading edition](../paper/p030.html) · [harness](https://github.com/srivtx/p-rick/blob/main/code/p-030-simulation.py)*
