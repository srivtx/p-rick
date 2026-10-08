---
title: "Your Data Has a Shelf Life. Nothing Tracks It."
date: 2026-10-07
author: p-rick research program
paper: p-018-epistemic-half-life
---

# Your Data Has a Shelf Life. Nothing Tracks It.

A package is undeliverable because a checkout form joined a 2019 address to a 2026 order. A hospital's emergency-contact field, captured at admission, quietly rots through a decade of moves and deaths — and presents itself with exactly the same authority as the patient's blood type. A compliance dashboard marks a vendor "certified" three certifications after the certificate died.

The data is available. The data is consistent. The data is wrong — and no integrity constraint ever built will notice, because this failure mode isn't corruption. It is *time*.

## The only industry that never learned about expiry

Food has sell-by dates. Medicine has lot numbers and recalls. Journalism runs corrections. Markets hard-code staleness bounds into matching engines — a stale quote is a regulatory concept, not a vibe. Software stores more facts about the world than all of those industries combined, and the database tuple has no concept whatsoever of perishability.

Codd's relational model is magnificent, and it baked in one assumption nobody has revisited in fifty years: a stored fact remains true. It doesn't. Addresses migrate, prices drift by the hour, credentials expire, certifications lapse, "current employer" fossilizes. The query planner — the most rigorous piece of logic machinery most companies own — will cheerfully join a fact that was verified yesterday with one that was last checked in 2019, and serve the result with identical confidence.

## Half-lives, not vibes

P-018's core move is small and load-bearing: facts should carry decay functions, and the first-class parameter should be a **half-life**. An address: a few years. A retail price: weeks. A stock quote: seconds. A blood type: effectively never. Confidence decays from capture through verification to deprecation, queries return *(value, confidence)* pairs, and joins inherit the worst of their inputs — the algebra composes.

The part people don't believe until they see it: the half-lives are already sitting in your logs. Every organization's change-data-capture stream contains the empirical decay curve of every fact class it maintains — the actuarial table of its own data, discarded as operational exhaust. Nobody ever aggregated it, because no query semantics existed that would make the statistic worth computing. Supply the semantics, and the statistics become load-bearing.

## The economics close the loop

Decay without verification is fatalism, so the paper budgets it: verification costs money — an API call, a letter, a nurse's minute — and the scheduler probes the facts whose expected confidence lift times downstream criticality is highest, per unit cost. The same discipline attention schedulers use for interruption, applied to re-checking facts.

And the funny part: this is the rare privacy paper where privacy and reliability point the same direction. Staleness is the enemy of both. Decay clocks schedule data minimization and data truthfulness on the same axis. One clock, two duties.

## Bitemporal is not the answer, and that matters

The obvious objection — "isn't this just bitemporal databases?" — is worth confronting head-on, because the near-miss is what keeps the gap invisible. Bitemporality records when facts were *believed*. It is a perfect ledger of the past. Staleness is about the future: the probability that an unrefreshed belief is still true, right now. One is retrospective, one is predictive. The 2019 address is served with immaculate transaction-time legitimacy and decaying truth, and no temporal feature ever standardized will say a word about it.

Facts expire. Every industry that stores facts about the world knows this, except the one with the most facts. P-018 is the specification for catching up: decay declarations, honest joins, budgeted verification, staleness as an outage class — visible, routed, owned — instead of a private disappointment discovered by an undeliverable package.
