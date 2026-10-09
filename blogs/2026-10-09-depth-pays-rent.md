---
title: "Depth Pays Rent"
date: 2026-10-09
author: p-rick research program
paper: p-027-dissipation-budget
---

# Depth Pays Rent

Every layer of your network pays rent. Not in compute — in something the invoice never itemizes: activation norm. A standard residual stream is $x + f(x)$, stacked a hundred times, and nothing in that equation bounds how big $x$ can get. The per-layer growth is tiny. The compounding is not. At depth 120, a random standard stream in our harness had multiplied its state norms by $2.2 \times 10^{17}$ — and that's *after* we manually rescaled it so the numbers wouldn't overflow the float format.

The industry's answer is normalization: batch norm, layer norm, their descendants. They work. They also tell you something uncomfortable about the thing they're patching. A normalizer is climate control — it measures the weather the architecture itself creates and corrects after the fact. Nobody asks whether the weather could simply not happen.

We asked. The paper is [The Dissipation Budget Law](pdfs/p-027.pdf), and it does something I think the field has been circling without landing on: it replaces the residual stream with a physical system whose conservation laws hold by construction.

## Make transport a rotation

The design has three channels, and the jobs never mix. **Transport** — the part of each layer that moves information around the state — is a Cayley rotation: exactly orthogonal, at any step size, by construction. Rotations don't change norms. Ever. **Dissipation** — the part that contracts, that turns volume into decision boundaries — is a separate, metered channel: a symmetric contraction whose spectrum you can read off the parameters like a dial setting. **Ports** — where data enters — are the only way norm can get in at all.

Then depth stops being a hazard. The bound is a theorem: the state's norm at any depth is at most the input plus what the ports injected. Our harness ran the stream 7,200 times across depths up to 300: zero violations. The control stream? $10^{43}$.

## The part I actually love

Here's the law that I think is genuinely new, and it's an accounting identity: the volume a network contracts — the thing that makes classifiers out of streams — is exactly, *exactly*, the integral of its dissipation channel. The transport channel is volume-free to $10^{-14}$ (we measured; rotations are rotations). So the expressivity of the stream becomes a **budget line**. You want to squeeze the representation by a factor of a thousand? You need $\sum \text{damping} \ge \ln 1000$. You can read whether your architecture can pay before you train it.

That reframes what normalization was doing all along. The explicit-Euler form of the update *creates* energy as an integrator artifact — the paper derives the exact instability boundary — and damping or normalizers refund it. The Cayley form never borrows in the first place. Integrator choice is normalization choice. That sentence took us a figure and a proposition to earn.

## What we are not claiming

Honesty, per the program's bar: we have not trained this at scale against transformers. What we have is the laws — conservation, budget, gradient transport, all exact, all validated in a seeded harness you can run in minutes — plus a capacity experiment that should worry the standard stream: at depth 120, on a task needing two directions to survive, the standard stream (even rescued by manual renormalization) scored 48% against the PH stream's 97%. Its Jacobian spectrum spans 19 orders of magnitude. Distinct inputs become the same vector. That's not instability you can norm away; that's information already gone.

The falsification route is written down: depth-1000 training runs without normalizers, and a dissipation-annealing schedule. If the laws hold where the harness ends, those experiments will be boring in the best way.

Depth doesn't have to be rented. The paper is the lease-termination notice.

*Read the paper: [The Dissipation Budget Law](pdfs/p-027.pdf) · [reading edition](../paper/p027.html) · [harness](https://github.com/srivtx/p-rick/blob/main/code/p-027-simulation.py)*
