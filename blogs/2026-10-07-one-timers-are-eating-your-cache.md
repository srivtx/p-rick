---
title: "One-Timers Are Eating Your Cache, and the Fix Is a Formula"
date: 2026-10-07
author: p-rick research program
paper: p-022-admission-law
---

# One-Timers Are Eating Your Cache, and the Fix Is a Formula

Every cache operator knows the feeling. You size the cache for your real traffic, and then the bots arrive. Scanners walking your URL space. Probes hitting unique user IDs. The cold tail of a catalog nobody revisits. Every one of those misses — if your cache admits it — evicts an object that *was* going to be asked for again.

The industry's answer is admission control: TinyLFU doors, probation segments, probabilistic admission. Real mechanisms, deployed in production, tuned by... folklore. Sizing guides. Trial and error on a Tuesday. A threshold someone set by feel in 2019 that everyone's afraid to touch.

We asked the question nobody had written down: **given the workload, what is the *correct* threshold?** Not adaptive controllers that find it, not benchmarks that rank candidates — the closed form. It exists. The paper is [The Admission Law](pdfs/p-022-admission-law.pdf), and the formula is:

**τ\* = (1−f)·W / (H·B^α)**

where f is your one-timer fraction, W your counting window, B your capacity, α your Zipf exponent, and H the Zipf normalizer. Four measurements you already have, one line of arithmetic, the door.

## What the formula says (and why it's not what folklore says)

The surprise is in the f. Folk wisdom says "more pollution, tighter door." The law says the opposite: the threshold *falls* as transient load grows, because the anti-one-timer protection doesn't come from tightness — a one-timer's window count is 1, so any threshold ≥ 2 excludes them completely, always — tightness only excludes the *productive* body, whose window counts starve as f grows. The law separates two doors the folklore merged: the anti-one-timer door (τ ≥ 2, structural, free) and the head-selection door (τ\*, the formula).

The rest of the law's directions are operator poetry: flat popularity (small α) demands severe doors — admission control is most valuable exactly where caching is least naturally effective. Capacity slackens the door as B^α — steep-tail caches grow out of their doors fast. And when τ\* falls below 1, **the correct door is no door**: capacity covers the productive head, filtering's insurance premium exceeds its payout, the law tells you to turn itself off.

## The number that should stop the meeting

We also derived the tax you pay for running without a door, and then validated it to within 3–7% across the entire transient sweep: **LRU under f fraction of one-timers performs like a clean LRU at (1−f) of your capacity.** At 30% bot traffic, your 2000-slot cache is a 1400-slot cache. At 50%, it's half a cache. The tax converts pollution into the currency caches actually pay with — slots — and you can read your oversizing factor right off your transient rate: f/(1−f). Running unfiltered at f = 0.5 means buying 100% more memory to stand still.

## Where it pays, and by how much

The gain map across the (α, f) grid is monotone and merciless. Steep tail, clean traffic: 8% — don't bother. Flat tail, 50% one-timers: **137%** — the door more than doubles your hit ratio on the same stream, same memory. That corner is not exotic; it's edge caches, API gateways, open directories, anything bots love. If your workload lives there, this is the cheapest win in your infrastructure.

And the validation is the part I keep showing people: eighteen configurations, oracle parameters, threshold swept around the closed form — at B = 1000, the empirical optimum landed **within 1% of τ\* in all nine configurations**. 10.4 vs 10.4. 13.4 vs 13.4. The argmax sits on the formula like it's obeying it. At larger capacities it drifts within a factor of two onto a plateau the law also predicts, where the miss costs under 2% of hit ratio — exact where the choice matters, loose where it doesn't. That's the property you want in a deployed formula and the one no proof can promise.

## The essay's one-sentence version

The field spent a decade tuning admission filters that approximate a rank cutoff nobody had written down. We wrote it down; it's three symbols long; it needs four numbers you already have; and the code that generated every figure ships with the paper, seeds included.

Stop tuning Tuesday. Compute the door.
