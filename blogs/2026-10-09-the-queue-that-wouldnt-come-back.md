---
title: "The Queue That Wouldn't Come Back"
date: 2026-10-09
author: p-rick research program
paper: p-025-collapse-law
---

# The Queue That Wouldn't Come Back

You know this outage. Traffic rises. Latency crosses a timeout. Clients re-send work the server hasn't finished. The re-sent work queues behind the original work, the queue deepens, latency rises further, more clients time out. Within minutes, a system that was comfortably handling its load is serving almost nothing.

And then — the part that defines the incident — the triggering traffic recedes, and *the system does not come back*.

Every runbook's darkest paragraph is about this state. Load shed. Fleet restart. The escalation that feels like admitting defeat because it is. The industry vocabulary is good — metastable failure, retry storm, congestion collapse — and the industry arithmetic is not: backoff tuned by feel, jitter applied on faith, retry budgets inherited from a library default nobody has read.

We wrote the arithmetic. Then an external audit tore the first draft of it apart — correctly — and we re-measured everything with error bars. The paper is [The Collapse Law](pdfs/p-025.pdf), and it is two formulas with a loop of hysteresis between them. This post is the honest version, including the parts where our own first draft was wrong.

## Formula one: the ceiling

Take the simplest system that has the pathology: one queue, service rate μ, arrivals λ, per-attempt timeout T, retries after backoff, give-up after R attempts. Timed-out work is not cancelled — the server finishes it anyway and the client throws the answer away. That waste is the amplification.

In steady state, the offered load and the timeout rate chase each other through one equation, and the equation's good solution *ceases to exist* at a load you can compute from two numbers you already have. Write θ = μT (the timeout measured in service times). The collapse ceiling is:

**λ_c = μ · θρ*²/(1 + θρ*)**, where θ(1−ρ*) = ln(1 + θρ*)

Tight deadlines make the timeout itself the scarce resource: a client willing to wait only two service times caps your effective capacity at a third of the server's. Patience is capacity — and it arrives logarithmically slowly (λ_c → μ(1 − (ln θ + 1)/θ)), so doubling the timeout buys you a few percent once θ is in the tens.

Two things the ceiling is *not*, and our first draft got one of them wrong:

It is not a number any configuration respects. The formula is the instant-re-offer worst case — the fluid limit where every timed-out attempt comes back immediately. Real clients back off, and a throttled retry stream *beats* the formula's amplification assumption. The ceiling is the existence boundary of the good state: above it, no policy holds the line even in principle; below it, whether you actually fall is a probability, not a promise. We measured that probability directly: at patient timeouts (θ = 5), the tipping curve saturates exactly at the ceiling — above it, every run falls; at tight timeouts (θ = 2), the curve hits 50% at two-thirds of the ceiling. The metastable wedge is widest when your deadlines are tightest. That's why the same system takes 3× the traffic on a good day and dies on a Tuesday.

And it is not policy-independent in the strong sense we first claimed. The retry budget R moves it a few percent once R is past ~5.3/ln(1+θρ*) attempts — and moves it *a lot* below that (at θ = 2, dropping from unlimited retries to R = 2 raises the ceiling 51%). Retry engineering is not capacity engineering, but it's adjacent.

## Formula two: the way back down

Here is the part I want every on-call engineer to have memorized, because it explains the runbook's most counterintuitive experience.

When the system is collapsed, nearly every attempt times out, so every job burns its full retry budget R before giving up. The storm's offered load is λR against capacity μ. Which means the collapsed state is *self-sustaining* — it does not need your traffic — as long as λR ≳ μ. The recovery threshold is:

**λ_r = μ/R**

At θ = 5, R = 6: collapse near 0.54μ, recovery below ≈ 0.17μ — and the *watchable* recovery, inside a dwell any controller actually waits, is 0.10μ. A system that falls at half its capacity must shed to a sixth to become recoverable and lower still to actually come back on a human timescale. That is why "we turned the traffic down and it didn't help" is not a hallucination — it is arithmetic. Between the two formulas is the hysteresis loop, the shape of every metastable postmortem ever written.

And there is a paradox hiding in R, the retry budget your platform team keeps raising out of kindness: every extra retry is extra food for the storm. R = 4 sustains itself below 0.25μ; R = 10 below 0.10μ. *Generosity makes collapse more survivable per job and less recoverable per system.* The formula prices the trade you were already making blind.

## The trap: unlimited retries

Here is the finding I'd put on a poster, new in the revision. The two formulas are the maximum and the endpoint of one curve — λ = μρ(1−q)/(1−q^R), the fixed-point curve of the whole system — and that curve has a property nobody told you: the hysteresis loop only *exists* when

**(R−1)·θ > 2**

Below that boundary there is no cliff at all — the system degrades continuously and recovers the moment load falls. Tight deadlines with a retry budget of two? No trap. Patient deadlines with a second try? Trapped. The runbook's darkest paragraph doesn't even apply to half the configuration space, and now you can tell which half you're in with one multiplication.

And the boundary's limit is the poster: **R = ∞ means λ_r = 0. The collapsed state never gives up because the clients never do.** We measured it: collapse the system deep, cut traffic to 5% of capacity, hold it there for three thousand service-times. With R = 6, the queue drains to zero. With unlimited retries, the queue *grew seventeen-fold* — 48,785 attempts deep at one-twentieth of the load that collapsed it. Every job that times out re-offers forever; the only population that can leave is the give-ups, and you removed it. Unlimited retries don't slow recovery down. They make load-shedding mathematically unable to work. Restart, or circuit-break the retry loop itself — there is no third exit.

## The knobs, priced (and two re-priced)

- **Backoff: have one.** At tight timeouts, instant retry collapses at half the ceiling; any backoff policy reads 61% of it. That's the robust separation in our multi-seed data.
- **Jitter: yes, but honestly.** It's anti-synchronization, and synchronization is what tips tight-timeout systems early. It buys back a quarter of the ceiling at θ = 2 — real money, not a ticket to λ_c. Our first draft claimed 81% from a single seed. Error bars exist for a reason.
- **Deterministic backoff: a retraction.** We reported fixed backoff collapsing 36% below instant retry — a resonance, we said, measurable. Across eight seeds it evaporates: the two are statistically indistinguishable, and at loose timeouts fixed backoff reads *above* instant retry, the direction backoff should go. The resonance mechanism is real; the constant was one seed's luck. Withdrawn. The folklore's defensible core is weaker and more useful: the emergency is not *which* backoff you chose — it is whether you have one at all.
- **Cap the queue inside the horizon.** This one got *stronger* under audit. We first said a cap of 2 "doubles the sustainable load" — a number above the server's capacity, which should have been embarrassing: the classifier was counting load shedding as survival. What the cap actually does is better: with L = 2 (at θ = 5), admitted attempts almost never time out, the amplification loop can't close (loop gain q_L·R = 0.75 < 1), and the system *stops having a collapse* — goodput degrades gracefully to min(λ, μ) instead of cratering to zero. A cap of 10 does nothing of the sort: it still craters. The rule has a closed form now: the cap works when the admitted-sojourn tail is small enough that R can't close the loop.
- **Treat the timeout as capacity.** λ_c(θ) is the real capacity curve of a deadline system. Choose T like you choose fleet size.

The paper has the seven experiments behind all of this — the multi-seed kernel, the tipping-probability curves, the policy grid, the ramp with the loop that never closes, the drain and trap measurements, the admission-cap goodput curves, the unified-curve validation — in a seeded file you can run in an afternoon, plus an appendix that lists every claim the audit killed and what replaced it.

Two formulas, three numbers you already have (μ, T, R), and one discipline: run below the ceiling, keep a backoff, cap the queue inside the horizon, keep R small enough to shed your way back down — and if anyone proposes unlimited retries, keep the restart runbook close, because arithmetic says that's the only exit left. The queue will not drain itself on your schedule. Now you can prove it.
