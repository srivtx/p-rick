---
title: "Your Embeddings Are Photocopies of Photocopies"
date: 2026-10-07
author: p-rick research program
paper: p-023-generation-loss
---

# Your Embeddings Are Photocopies of Photocopies

Somewhere in your infrastructure is a corpus of embedding vectors. Millions of them, on disk, in an index. They were produced by encoder generation 17. Your queries are arriving encoded by generation 19.

Nobody knows the exact cost of that gap. I mean this literally — not "nobody has noticed," but *nobody has the mathematics to price it*. The vector database vendors give you a calendar: "re-embed when you change models," scheduled by policy, priced by token count. When recall degrades, the debugging guide suggests checking your chunk size.

We wrote the missing mathematics. The paper is [Generation Loss](pdfs/p-023-generation-loss.pdf), and its core is one law with a twist that production intuition gets exactly backwards.

## The law

Model every encoder upgrade as two channels. The **isometry channel** is the part of the change that acts as one global rotation of the whole space — the new encoder is the old encoder, turned. The **distortion channel** is everything else: the per-object reshaping, the genuine semantic re-decisions of a retrained model.

Drift accumulates geometrically — a photocopy of a photocopy — and the per-generation fidelity loss is:

**λ = (1 − 2(1−c)/d) × (1+ν²)^(−1/2)**

The first factor is the isometry channel. The second is distortion. They behave *oppositely*, and the opposition is the finding.

## The twist: rotations are (mostly) harmless

Here's what production intuition — trained on 2-D and 3-D rotation imagery — gets wrong. A 60° global rotation per generation sounds catastrophic. At d = 256, thirty generations of it accumulate **1.1% drift**. At d = 1024, 2.9%. A 135° rotation — a quarter turn of your entire embedding space — costs 1.3% of cosine per generation.

Why? A random rotation in high dimension barely moves any *fixed* vector. The rotation acts in a random plane; any specific vector has mass in that plane with probability ~2/d. High-dimensional spaces are almost rotation-invariant for individual points. We call it *dimension mercy*, and it retires a fear you shouldn't have.

What you *should* fear is the distortion channel — dimension-free, geometric, and un-alignable by any transformation, because it isn't one. That's the entire real cost of encoder churn.

## The free lunch that isn't folklore

Because the isometry channel is a global rotation, it's removable *exactly*: keep a panel of L persistent landmark objects, re-embed just those each generation, solve one Procrustes alignment, and multiply the refresh into your stale index. No re-embedding of the corpus. The error of the estimated alignment falls as √(d/L) — the budget formula says your landmark panel should outnumber your dimension by about 8×. At d = 768 that's ~6000 objects per generation. Against a corpus of millions, it's a rounding error.

In simulation: a stale index's recall@10 fell from 0.81 to 0.38 over sixteen rotation-dominated generations. The anchored index — the *same stale vectors*, one matrix refresh per generation — held 0.71. Nearly double the endgame recall for a rounding error of cost. And the two-channel heatmap is the cleanest figure in the paper: anchored recall is flat across the *entire* rotation axis (0.75 to 0.76 from 0° to 135°) and collapses along the distortion axis. Rotation: removed. Distortion: the floor.

## The decision rule that replaces the calendar

The protocol costs one coffee: embed a few hundred probe objects with both encoders, fit the orthogonal map, measure the residual. You now have c and ν. Compute λ. You now have the entire drift curve of your corpus under churn like this pair's.

Then the calendar question becomes arithmetic. Isometry-dominated churn (which is what we predict — as a labeled, testable prediction — for adjacent checkpoints of the same training run): anchor forever, re-embed never. Distortion-heavy churn (a genuinely retrained model): the law tells you exactly when accumulated drift crosses your retrieval margin, so the re-embed date is derived, not decreed.

Every claim in this post is validated to three decimals in the paper — the drift law matched simulation at 0.077/0.077, 0.275/0.276, 0.558/0.560 across channels, and a rotation-only chain and a noise-only chain tuned to the same λ lie on the *same line*. One file regenerates every figure. The Procrustes self-check is literally an assertion in the code.

Fire the calendar. Hire the arithmetic.
