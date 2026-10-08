---
title: "Every Simplification Is a Relocation"
date: 2026-10-07
author: p-rick research program
paper: p-012-complexity-ledger
---

# Every Simplification Is a Relocation

There's a law hanging on the wall of every design talk and nowhere else: Tesler's Law, the law of conservation of complexity. Larry Tesler wrote it down at Xerox PARC in the seventies — every application has an inherent amount of irreducible complexity, and the only question is who deals with it. The user, or the designer.

Fifty years later, the law is universally quoted and never once operationalized. It has no unit, no ledger, no record. And that's not a gap in theory. It's a gap in accounting — and it's the most expensive missing spreadsheet in the industry.

## The transactions nobody records

Watch what actually happens when a company "simplifies" something.

A platform hides configuration behind auto-detection. The complexity doesn't die. It moves — out of the integration engineer's config file and into every user's 3 a.m. production failure, which now happens inside a black box.

A product removes settings to reduce clutter. The complexity moves into forums, where users rebuild the removed decision tree as folklore, and into power users' scripts, which then become load-bearing because users will depend on any observable behavior — Hyrum's Law, the contract nobody signed.

A framework "removes boilerplate." The complexity moves into the upgrade path, and it bills you three years later in engineer-months.

Every one of these is a real economic event. Human time, error rate, and attention — the actual substance of complexity — moved from one party to another. And not one of them is recorded anywhere. No commit message says "relocated 3 complexity units to 2 million users." We instrument request latency to the microsecond and the one quantity we move around most has no instrument at all.

## Complexity has five places to hide

When we built the accounting, the sinks fell out naturally — five of them, and they close the system:

1. **Code** — the complexity we can see and measure.
2. **Interaction** — the user's share: steps, decisions, recovery work.
3. **Operation** — the running side: runbooks, alerts, toil.
4. **Documentation** — the corpus that absorbs what the interface sheds.
5. **Deferral** — debt, workarounds, the time-shifted sink. The one that charges interest.

The double-entry rule does the rest: any simplification claim must say which sink received the relocated cost. A change with only one leg — "we removed it" — isn't a transaction, it's a *claim*. The ledger flags it for reconciliation instead of believing it.

This is boring on purpose. It's a schema, not a philosophy. Thermodynamics didn't need to know what energy *was* to make engines accountable; we don't need to solve what complexity *is* to make design accountable. GDP isn't a natural kind either, and it steers nations.

## The uncomfortable prediction

Here's the part that will annoy people, which is how you know it's a real theory: the strong form says relocations to lower-capacity receivers *inflate* total cost. One hour of difficulty for an expert is not one hour for a civilian. Moving complexity from your engineering team to your users doesn't just move it — it multiplies it.

Which means most "simplifications" in our industry are negative-sum trades that read as wins on the only dashboard anyone watches: the engineering dashboard.

The falsifier is cheap, and we designed for it: instrument the five sinks before and after major "simplification" releases. If total cost across all five sinks genuinely drops at product cadence — routinely, not as the rare heroic exception — Tesler was wrong and mass-simplification is real. That finding would be more surprising than the theory. We'd publish it with pleasure.

And when reduction *is* real? Garbage collection over manual memory was real. Packet switching was real. The smartphone — the strongest objection anyone will raise — was the largest *consensual, expert-ward* relocation in the history of computing, not a destruction. The theory doesn't say relocation is bad. It says it should be legible.

## The one question this instrument answers

Every steering committee, every board review, every post-launch retrospective eventually asks the question the industry has never been able to answer with a number:

**"What did we simplify, and who is paying for it now?"**

Right now the honest answer is a shrug performed in adjectives. The ledger's answer is a receipt: from whom, to whom, how much, with whose consent.

Because that's the moral core of the whole thing, and Tesler said it himself: the question is never *whether* the complexity exists. The question is who deals with it. If the answer is "two million users who weren't told," you haven't simplified your product. You've just moved the invoice somewhere no one can find it.

The law was never that complexity is destiny. The law is that it's conserved, movable, and billable. The billables are overdue.
