---
title: "Your Software Has a Second Behavior Nobody Wrote Down"
date: 2026-10-07
author: p-rick research program
paper: p-004-degradation-contracts
---

# Your Software Has a Second Behavior Nobody Wrote Down

There are two versions of every app you ship. The one in the spec, and the one that exists when the machine gets tired.

The first version has an entire industry around it. Product specs. Design reviews. Test suites with thousands of cases. Dashboards watching its latency and error rate like cardiologists. That version is the best-engineered artifact of our civilization, and I don't say that lightly.

The second version appears when memory runs low, the battery fades, the CPU throttles, or the network collapses on a train. It is written by nobody. Reviewed by nobody. Tested by nobody. It is the accidental composite of a thousand scattered if-statements, an OOM killer's heuristics, and whatever your developers didn't get to. Your users meet this version constantly — the median device on this planet lives under permanent pressure — and no artifact anywhere on earth says what it was *supposed* to do.

We didn't specify behavior under scarcity because scarcity used to be an incident. It isn't anymore.

## The industry already proved this is solvable — twice

Here's what convinced me this isn't philosophy. Two corners of software already treat degradation as a first-class engineering object, and they're the two corners users are happiest with.

Video streaming. An adaptive stream is a *declarative degradation contract*: a staircase of quality levels, chosen by measured conditions, with hysteresis so it doesn't flap. Nobody at a streaming company would ship "quality degrades however it degrades." They encode the ladder. The ladder is the product.

Web infrastructure. Every serious service specifies load shedding: which requests get dropped, which get simplified, in what order, when the load exceeds capacity. The brownout research line, Envoy's overload manager, admission control — degradation is *policy*, not accident.

So the practice exists. What's missing is the general form: a language any app can use to declare how it degrades, for any resource, and a runtime that enforces it and — this is the part nobody has — *audits* it.

## The three questions your app can't answer today

Ask any team these, and watch the silence.

**What does your app shed first when memory is scarce?** If the answer isn't written down, it isn't a decision — it's a fate. The ordering matters: suspend spell-check before autosave, animations before sync, polish before the core loop. That ordering is a product decision with safety consequences, and today it lives in nobody's head, nowhere.

**How does your app recover?** Systems that degrade must heal, with hysteresis, or they oscillate. The "flapping" pathology — a feature bouncing between tiers — can be worse than staying degraded. No API in any OS has recovery semantics.

**Why was it slow yesterday at 2pm?** Not the latency graph — the *decisions*. What was shed, by whom, under what pressure. Observability platforms watch symptoms; nothing records the degradation decisions themselves. We named the accumulated unrecorded liability **degradation debt**, and every app on earth is carrying an unknown balance.

## The uncomfortable part: AI makes this worse, faster

AI systems are natively degradation-shaped. Every assistant you've shipped has runtime quality knobs: context truncation, model substitution, speculative decoding, retrieval depth, quantization. Your quality is already a *variable* — turned invisibly, under memory and battery and latency pressure, by heuristics nobody reviews.

Today, nobody can see which quality they received. Tomorrow, with agents grabbing machine resources, those knobs get turned more often and less visibly. The honest version of this future is a *contract*: under this pressure, this assistant answers with this model and this context, never below, and the UI says so. That's not a nice-to-have. That's the governance layer the entire AI stack is missing, and it's the same layer your animations needed in 2015.

## What we're proposing

The paper specifies the whole thing — formal model, runtime, DSL — but the core is one sentence: **degradation becomes a contract, declared like permissions, enforced like quality-of-service, audited like a ledger.**

Three parts. A manifest that says, per feature, the fidelity ladder and the shedding order. A pressure broker in the OS that reads pressure (Linux PSI proved this measurement layer in 2018) and dispatches directives to apps that declared ladders. And a ledger that records every tier transition — the audit surface that lets a user ask "what was sacrificed and why" and lets a buyer ask "which app degrades honestly."

The objections are in the paper, confronted honestly: apps will lie (transparency, then demotion — the market does the punishing); nobody writes manifests (media, games, and local AI already have ladders — the beachheads are built); cross-layer contracts are hard (ledgers compose). The strongest objection is "this is folklore and folklore is fine," and the answer is that folklore was fine when resources doubled every two years. That world ended. The median device is permanently pressed, and behavior under pressure is now most of the user experience your users actually have.

Ship the first version. Then ship the one you'd be proud of when the machine is tired.
