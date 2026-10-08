---
title: "We Preserve Films and Seeds. Not Minds."
date: 2026-10-07
author: p-rick research program
paper: p-011-model-extinction
---

# We Preserve Films and Seeds. Not Minds.

There's a vault in Svalbard that keeps seeds against the collapse of agriculture. There's an archive in San Francisco that keeps the web against the collapse of memory. There's an initiative with a UNESCO partnership that keeps source code against the collapse of repositories — Software Heritage, an archive of billions of source files, precisely so that no repository's death means the code's death.

We are, as a civilization, quite good at noticing when a class of artifact starts dying faster than anyone is saving it. We built institutions for print, film, seeds, code, and web pages.

The fastest-dying artifact class on earth right now is the behavior of deployed AI models. And there is no institution. There isn't even the *instrument*.

## The lifespan of a mind, measured in months

Every API model you can name is on a deprecation conveyor. Model families announced, adopted, deprecated, gone — often inside a year. When OpenAI retired legacy GPT-3.5 and GPT-4 lines, customer *fine-tunes* went with them: organizations that spent real money training a domain model discovered it was a lease, and the landlord called in the portfolio. Providers now ship dated snapshots with sunset windows after a 2024 episode where compressed timelines pushed production teams into forced migrations — the developers' public pushback was the loudest demand signal this gap has ever produced.

And here's the part that makes it categorically worse than ordinary software deprecation: when a model is retired, the thing that dies is not code. Code could be archived. The thing that dies is a *behavioral identity* — a distribution over outputs that your products were tuned against, your prompts were fitted to, your published benchmarks measured, your legal and medical and hiring pipelines *acted on*.

Products break *invisibly* — the errors look correct, the dashboards stay green, and an entire profession has invented a name for the symptom: prompt rot. Research becomes unreproducible months after publication, because the evaluated system no longer exists anywhere. Court records cite a model name that outlived its own referent. None of these losses show up in anyone's incident channel, because nobody is counting them. That's what an extinction event looks like when the species has no census.

## The reframe that makes it solvable

The obvious objection: you can't archive a closed model — the weights are trade secrets, and even with weights, serving stack, guardrails, and sampling defaults all shape behavior.

Both true, and both answered by the same reframe, which is the core of the paper: **conserve the observable, not the substrate.** Film archives preserved the screened experience when the negatives were legally unobtainable. Ecologists have always studied populations through *observation* — censuses, not corpses. Behavioral identity is measurable by anyone with API access: you run a stratified, anchor-linked probe suite and get a score vector with confidence regions. A fingerprint. The archivist never needs the weights. The archivist needs the queries and a GPU budget.

With fingerprints, everything else falls out. Equivalence testing — the standard statistical machinery we already use to prove two things are *the same*, two one-sided tests, used in pharmacology since 1987 — becomes the deprecation audit: is the successor behaviorally interchangeable with the predecessor, at stated confidence, per stratum? A provider saying "seamless replacement" is suddenly making a falsifiable claim with a published method behind it.

And my favorite design move: consumer-supplied regression strata. Every product's own test suite — the prompts whose distributions the product depends on — becomes a private stratum of the public fingerprint. Your regression tests become conservation instruments. Millions of private eval suites, federated into a census.

## The registry is the institution the field doesn't have yet

What the specification adds up to is an extinction registry. IUCN-style: a public, provider-independent record of behavioral artifacts — ACTIVE, DEPRECATED-ANNOUNCED, EXTINCT-IN-WILD — with fingerprint history, equivalence assessments for every succession, and a periodic state-of-extinction report. Which minds vanished this quarter. How many dependents were exposed. The report is what turns millions of private "my prompts stopped working" moments into a public, countable phenomenon. You cannot govern what you refuse to count.

Plus the piece providers can ship *today*, cheaply, and one already half-shipped by accident: inference-time provenance. A signed behavioral identity token on every response — model family, dated snapshot, serving-config class. OpenAI's `system_fingerprint` field is this idea in embryo: an undocumented field, an accident of engineering honesty. Make it a standard, and a research paper can cite the exact behavioral artifact it evaluated, and a product can audit what it actually depended on, and a sunset date becomes a *promise that third parties can verify*.

## Why nobody did it

The incentives point exactly against it: every conservation instrument is a cost on the party that owns the artifact, and deprecation is the business model's hygiene. Fine. Conservation has *always* required someone other than the owner to notice the dying — the film archives fought the studios, the legal-deposit libraries fought the publishers, Software Heritage exists because Inria noticed, not GitHub. The institutions bootstrapped after the crisis, always one crisis late.

The crisis is here. It's just distributed as millions of private annoyances instead of one photogenic fire.

The seeds are in the vault. The code is in the archive. The behavior is in neither. We specified the instruments — the fingerprint that measures a mind, the equivalence test that audits its replacement, the registry that counts its deaths. The rest is institution-building, which is somebody's very fundable problem.
