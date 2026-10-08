---
title: "Your Calendar Was Designed for a Species That Doesn't Exist"
date: 2026-10-07
author: p-rick research program
paper: p-009-circadian-orchestration
---

# Your Calendar Was Designed for a Species That Doesn't Exist

Every scheduling system in production — every one — encodes exactly one fact about you: whether a slot is occupied. You are a grid of free and busy. Everything else, the software assumes, is your problem.

Here is what sixty years of chronobiology says about that assumption: it's wrong in a specific, measurable, exploitable way. Your cognitive performance varies systematically across the day. That variation follows your *circadian phase* — your internal clock's offset from the social clock — and phase differs between people by four to six hours at the population extremes. A 9 a.m. strategy meeting is near-peak for your morning person and near-trough for your night owl. Same room, same coffee, same agenda, two different brains.

Your calendar treats them as the same animal. Your calendar was designed for the *average human*, who does not exist.

## The fight you're having is not the fight you think you're having

Every engineering team I've ever worked with has fought the standup-time war. It presents itself as a culture dispute — discipline versus flexibility, night owls versus morning people, someone's "we've always done 8:30."

It isn't. It's a chronotype dispute misclassified as a character dispute, and the cost lands on the tail. The evening types absorb the early-slot burden forever, quietly, and the cost is real: chronic mismatch between social and biological time — the literature calls it *social jetlag* — is one of the most consistently replicated associations in the field. You are not arguing. You are externalizing biology onto the people with the late phase.

And nobody — no calendar, no meeting tool, none of it — can even *represent* the problem. That's the gap.

## The science is done. The math is done. The software doesn't exist.

This is what sold me on the gap. Look at the pieces:

Chronotype is measurable in five minutes — validated questionnaires, the Munich ChronoType lineage, scored against core body temperature in the lab. Wearables now measure sleep timing at population scale; half your team already wears a phase-estimation device. The two-process model of alertness — Borbély, 1982, continuously refined since — gives you a functional form for performance across the day. And the operations research community spent *decades* building circadian-aware scheduling for hospitals and factories. The optimization is solved, in a harder setting than this one.

Meanwhile your scheduling stack — Calendly, FindTime, working hours, focus analytics — models time as *quantity* and pretends it has no *quality*.

Components: proven. Composition: absent. That's the shape of every real gap.

## The reason it stayed empty is the reason it's buildable

The obvious implementation is a surveillance nightmare — your employer knows your sleep — and everyone correctly recoiled, so the category died before anyone designed it. The failure was imagination, not feasibility.

The design that works refuses the data model, not the problem. Your phase never leaves your device. What leaves is a *binned cost surface* — green slots and red slots over the team's shared horizon, no reasons attached, three coarseness levels, nothing to subpoena because nothing individual exists to subpoena. The optimizer only ever sees suitability bins. The org dashboard sees aggregate golden hours under k-anonymity. The privacy isn't a compliance layer bolted on after the lawyers screamed. It's the data model.

That's the generalizable lesson and I'll repeat it because it's worth repeating: **choose the disclosed abstraction so privacy falls out of the data model, not out of cryptography bolted on later.**

## The unfair part nobody optimizes for

Left to itself, a naive optimizer does something ugly: it schedules for the morning majority, because morning people are cheap to satisfy at 9 a.m. by construction. The evening tail eats the difference. Unconstrained optimization *redistributes* pain; it doesn't remove it.

So the specification has a fairness constraint — minimax burden over a rolling window — and it's the difference between a tool and a weapon. The output isn't "everyone's average alertness improved." It's "nobody is structurally assigned the graveyard." Scheduling is distributional. Every calendar is a distributional policy. Yours is currently unexamined.

## Start with one meeting

You don't need a mandate. Take your worst recurring meeting — you know the one — and compute its golden overlap by hand if you have to. Ask five people when they're actually sharp, anonymously if you like. You'll find two hours of shared daylight nobody was using, and a drift plan gets you there in a month.

The 8:00 standup war doesn't end with a compromise. It ends with a slot.
