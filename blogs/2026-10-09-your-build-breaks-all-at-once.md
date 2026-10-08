---
title: "Your Build Breaks All at Once, Not Gradually"
date: 2026-10-09
author: p-rick research program
paper: p-024-resolution-collapse
---

# Your Build Breaks All at Once, Not Gradually

There is a kind of Tuesday every engineering organization knows. A routine minor release lands. Nothing in the changelog is interesting. And by afternoon, `install` is hanging for a non-trivial fraction of your users — not failing with a clear error, *hanging* — and the incident channel assembles the usual hypotheses: cache, network, someone's proxy.

It's almost never the proxy. It's the resolver, and the resolver was never the problem until, one dependency bump at a time, it was.

We treat dependency resolution as infrastructure — reliable by default, boring by design. The manifest names packages, each version of each package names *other* packages with version *ranges*, and something in the toolchain picks one version per package so every range is happy. What that something is actually doing is solving a constraint-satisfaction problem, thousands of times a day, whose difficulty is a function of three numbers your ecosystem has been drifting for two decades: how many packages, how many versions each, how many dependencies each version declares.

We wrote down what happens when those numbers drift far enough. The paper is [Resolution Collapse](pdfs/p-024-resolution-collapse.pdf), and the headline is the shape, not the number.

## The shape: a phase transition

Resolution failure is not gradual. Below a critical dependency density, resolutions exist and the solver finds them in milliseconds. Above it, resolutions *cease to exist* — not "are slow," not "need a smarter resolver": the constraint graph has no satisfying assignment, and no algorithm recovers what combinatorics has taken away. The transition between those two regimes is sharp, the same sharpness the theory community has measured in random SAT for thirty years.

The threshold has a formula's shadow over it. In the model, the expected number of valid resolutions is $K^n (w/K)^{nD}$ — $K$ versions per package, $w$ the width of the compatibility ranges, $D$ the dependencies each version declares. Setting the expectation to one gives the boundary:

**D ≤ ln K / ln(K/w)**

Three logarithms. Read them as an operator would. The numerator is your version count; the denominator is how *tolerant* your ranges are. The entire safety margin of your ecosystem is the ratio of those two logs.

Below that bound, our measurements put the real threshold at a gap constant times the formula — γ around 0.7, and I want to be careful here, because this program learned in public what an unlabeled constant costs: **γ is configuration-specific.** It moves with range ratios and solver budgets. The logarithms are the law; the constant is a reading, not a law of nature. (That sentence is in the paper too. So is the grid that shows the constant wobbling.)

## The finding that fights back: version proliferation

Here is the result that every release manager should sit with. At *fixed* compatibility width, adding versions to your packages makes resolution **harder** — the threshold *falls*. Every new version is mostly new constraints (its dependencies) and only partly new slack (one more choice). At fixed width, the constraints win.

At *proportional* width — ranges that widen as the version count grows, which is roughly what caret semantics does for free — proliferation is slow slack, and the threshold rises as $\ln K$.

We ran this as a panel: same density, sweep the version count, two range policies. Fixed width: resolvability falls from 1.0 to 0.0 as versions go from 16 to 256. Proportional width: resolvability climbs the whole way. Version growth is fragility or safety depending entirely on whether your compatibility story grows with it. If you take one practice from this essay: your caret ranges are not syntax sugar. They are the ecosystem's immune system against its own release cadence.

## The parable: ecosystems hold themselves at the edge

The experiment I find hardest to shake off is the growth run. Two ecosystems, both growing — new packages arriving, incumbents releasing versions whose dependency counts drift upward (which is the measured pattern in every real registry). One arm has no feedback. Its density crosses the critical threshold around step 120 and install success goes to zero. Permanently. For sixty further growth steps, releases keep shipping and nothing installs, because nothing in the growth dynamic pauses to ask the resolver's opinion.

The other arm has one rule: when installs start failing, roll back the most recent version bumps. That arm's density tracks the threshold from below, with a mean gap of 0.13 density units, for the entire run. Install success holds at 1.00.

I am not claiming npm is self-organized critical. I am claiming something weaker and more useful: *failure feedback alone is sufficient to hold an ecosystem near its critical boundary* — and near-critical is exactly where "the build that hangs forever" lives, where the solver's cost peaks, where a single unlucky release tips you over. The ecosystems that feel perpetually fragile and the ecosystems that feel fine may be the same system, one wavelength apart.

## What to actually do

Compute your distance to the threshold. The fragility index is three logarithms and a density reading from your own metadata: packages, versions per package, mean edges per version, mean range width. If the number is small, you have your explanation for the next Tuesday.

And know which levers move which direction. Widening compatibility ranges is the *only* lever that moves the bound itself — it bought nearly a full density unit in our runs. De-duplicating re-declared requirements buys about the size of the duplication. Pruning old versions is the genuinely two-sided one: it removes choice-slack (bad for satisfiability, and the bound says so) but it also makes the remaining search cheaper (good for the budgets real pipelines run) — we measured it *hurting* at generous solver budgets and *helping* at practical ones. Do it for security; call it what it is; and if your installs are already hanging, the cure is range-widening or rollback, not hygiene.

The folklore has always treated resolver failure as weather. It's climate. It has a number, the number is computable from your own registry, and the distance between you and it is a maintenance decision.

The paper, with the solver, the grid, the growth runs, and every constant honestly labeled, is [here](pdfs/p-024-resolution-collapse.pdf).
