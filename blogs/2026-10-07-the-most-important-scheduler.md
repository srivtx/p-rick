---
title: "The Most Important Scheduler in Computing Hasn't Been Written"
date: 2026-10-07
author: p-rick research program
paper: p-006-attention-scheduler
---

# The Most Important Scheduler in Computing Hasn't Been Written

Fifty years of systems research gave us something beautiful: a body of theory that lets one machine serve thousands of competing requesters — fairly, with latency guarantees, starving none of them, with an audit trail you can check.

Then we took that theory and pointed it at everything except the thing computers are *for*.

CPU: scheduled. Memory: scheduled. Network packets: scheduled, with fairness proofs and bounded lateness. Human attention — the actual endpoint of every notification queue on earth — is handled by a toggle called Do Not Disturb and whatever volume settings you last touched in 2023.

## The engagement economy is an unscheduled queue

The architecture today: an app vendor's growth team submits an interruption directly to your working memory, whenever their A/B test says so. The platform applies a static filter. The interruption lands mid-task at a measured cost of roughly twenty-three minutes of resumption work — Mark's classic result, replicated for two decades — dozens of times a day, with no accounting anywhere.

No per-app record of interruptions delivered and cost inflicted. No admission control — the only one that exists is user rage, app by app, after the damage. No deadlines, so a filter that eats one urgent message destroys user trust forever and teaches them never to automate again. No guarantees at all.

Notice what this is. It's a machine serving thousands of competing requesters *unfairly, unaccountably, and without bounds* — the exact problem scheduling theory solved in 1973. We just never connected the queue to the theory.

## The research exists. It was never given an OS.

This is what should bother the systems community most. Every piece is published and proven.

Interruption science measured the cost curve and found the dominant variable: *when*. Delivery at task breakpoints — Iqbal and Bailey's OASIS line, Adamczyk & Bailey's studies — cuts interruption cost dramatically with zero change in content. Horvitz's Microsoft work built Bayesian best-time-to-interrupt models in 2003. Attelia detected breakpoints from phone sensors *in the wild* with double-digit reductions in perceived load.

The prediction machinery works. The cost model works. What was never built is the thing it plugs into: an OS service with a queue, a cost model, budgets, and guarantees. The field treated this as an interface problem for twenty years. It's a scheduler problem. Schedulers are specified by their guarantees, so here are the ones the paper states:

**Urgent bounded latency.** The urgent class — person-to-person, safety, 2FA — delivers within a deadline bound, always, by construction. This single property is why users can trust automation: it cannot silently eat the message that mattered.

**Starvation freedom.** Every admitted notification delivers within a worst-case window, so suppression is never silent. The failure mode that made users hate filters becomes structurally impossible.

**Honesty pricing.** Apps claim priority; apps get *charged* for their claims at realized cost. An app that cries urgent for content updates pays escalating rates until its urgent channel is rate-limited. This is the mechanism the engagement economy has never had: the marginal low-value notification becomes expensive in a currency the platform enforces.

And an **attention ledger** — every decision, every deferral, every reason — exportable. That's the audit surface regulators will eventually demand, and the daily "attention statement" users have never been offered: 46 interruptions, 71 minutes of focus protected, here's the per-app bill.

## The uncomfortable observation

Apple shipped "Reduce Interruptions." Android shipped notification cooldowns. The platforms are building exactly this system — closed, unaccountable, unexplainable, without a published scheduling semantics anywhere.

That's the real stakes. Either the field specifies attention scheduling now — deadlines, starvation-freedom, pricing, ledgers, the grammar of trust — or it gets specified by three product managers in private, as one more engagement lever, and closed implementations harden into permanence. The window is a couple of years.

And the AI era is about to make the queue worse in a way nobody has priced: agents. Your five assistants each "ping when they need input." Five new unthrottled queues, attached to your working memory, emitting at machine rate. The host-side admission layer for agentic computing is the attention scheduler, and it doesn't exist yet.

The queue is open. Someone should schedule it.
