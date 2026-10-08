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

We wrote the arithmetic. The paper is [The Collapse Law](pdfs/p-025-collapse-law.pdf), and it is two formulas with a loop of hysteresis between them.

## Formula one: the ceiling

Take the simplest system that has the pathology: one queue, service rate μ, arrivals λ, per-attempt timeout T, retries after backoff, give-up after R attempts. Timed-out work is not cancelled — the server finishes it anyway and the client throws the answer away. That waste is the amplification.

In steady state, the offered load and the timeout rate chase each other through one equation, and the equation's good solution *ceases to exist* at a load you can compute from two numbers you already have. Write θ = μT (the timeout measured in service times). The collapse ceiling is:

**λ_c = μ · θρ*²/(1 + θρ*)**, where θ(1−ρ*) = ln(1 + θρ*)

Two consequences, both uncomfortable.

First: **no retry policy appears in the formula.** Backoff, jitter, budget — none of it moves the ceiling. Retry engineering is real, but it is not capacity engineering. If you are above λ_c, the good steady state does not exist, and you cannot backoff your way to it. The ceiling is the *timeout's* arithmetic: tight deadlines make the timeout itself the scarce resource. A client willing to wait only two service times caps your effective capacity at a third of the server's. Patience is capacity.

Second: the ceiling is where every policy *converges*. We measured instant retry, fixed backoff, exponential, full jitter. At loose timeouts they all sit within a few percent of each other at the ceiling. The interesting differences live below it, in who *reaches* the ceiling and who collapses early — and there the folklore gets one thing right and one thing badly wrong.

The right thing: **jitter**. At tight timeouts (θ = 2), instant retry collapses at half the ceiling — synchronized timeout cohorts re-offer together, cross the shallow separatrix, and tip the queue. Full jitter buys it back to 81% of ceiling. Jitter matters most exactly where you can least afford the storm.

The wrong thing: **deterministic backoff**. A fixed delay after timeout re-synchronizes the cohort — it resonates. At moderate timeouts, fixed backoff collapsed *36% below* instant retry. The polite, deterministic retry your library calls "exponential backoff" without jitter can be worse than hammering.

## Formula two: the way back down

Here is the part I want every on-call engineer to have memorized, because it explains the runbook's most counterintuitive experience.

When the system is collapsed, nearly every attempt times out, so every job burns its full retry budget R before giving up. The storm's offered load is λR against capacity μ. Which means the collapsed state is *self-sustaining* — it does not need your traffic — as long as λR ≳ μ. The recovery threshold is:

**λ_r ≈ μ/R**

At θ = 5, R = 6: collapse at 0.54μ, recovery below ≈ 0.17μ. A system that falls at half its capacity must shed to a sixth to get back. That is why "we turned the traffic down and it didn't help" is not a hallucination — it is arithmetic. Between the two formulas is the hysteresis loop, the shape of every metastable postmortem ever written.

And there is a paradox hiding in R, the retry budget your platform team keeps raising out of kindness: every extra retry is extra food for the storm. R = 4 recovers below 0.25μ; R = 10 below 0.10μ. *Generosity makes collapse more survivable per job and less recoverable per system.* The formula prices the trade you were already making blind.

Below λ_r the queue does drain — eventually. We measured the drain: a storm a few hundred attempts deep takes two thousand service-times to empty at one-twentieth of capacity. No load-shedding controller dwells that long. Below the recovery threshold, patience works; near it, the drain rate μ−λR goes to zero and patience is a theory. The exits are three: shed *deep* (below μ/R and then wait), restart, or never fall.

## The knobs, priced

- **Jitter: always.** It is anti-synchronization, and synchronization is what tips tight-timeout systems at half their ceiling.
- **Never deterministic backoff.** It resonates. This is measurable and it is 36%.
- **Cap the queue inside the horizon.** Admission caps work only when L ≲ μT — a cap of 2 doubled the sustainable load at θ = 5 in our runs, while a cap of 10 bought *nothing*, because admitted attempts still timed out while rejected ones burned retries. The worst of both doors.
- **Treat the timeout as capacity.** λ_c(θ) is the real capacity curve of a deadline system. Choose T like you choose fleet size.

The paper has the six experiments behind all of this — the kernel validation, the policy grid, the ramp with the loop that never closes, the drain measurements, the admission caps, the residuals — in a single seeded file you can run in an afternoon.

Two formulas, four numbers you already have (μ, T, R, and your current load), and one discipline: run below the ceiling, jitter the retries, cap the queue inside the horizon, and when you fall, shed below μ/R or restart. The queue will not drain itself on your schedule. Now you can prove it.
