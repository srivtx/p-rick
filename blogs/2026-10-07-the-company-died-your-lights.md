---
title: "The Company Died. Your Lights Didn't Get the Memo."
date: 2026-10-07
author: p-rick research program
paper: p-008-afterlife-of-devices
---

# The Company Died. Your Lights Didn't Get the Memo.

In April 2023, a company called Insteon shut down. No announcement, no transition plan. Somewhere north of a decade of installed hardware — hubs, dimmers, locks, sensors sitting in people's walls and ceilings — went dark in an afternoon, because all of it depended on a server somewhere that nobody was paying for anymore.

The physical hardware was fine. The light switches worked. The locks moved. The failure was not electrical, mechanical, or even software in the usual sense. It was *organizational*: a $40 piece of electronics with a fifteen-year lifespan was coupled, invisibly and permanently, to a corporate lifespan of a few years, and nobody had written down what happens when the arithmetic goes bad.

Everyone called it an outrage. Nobody called it what it actually is: a specification failure.

## We solved this exact problem in 1985

Here's the part that convinced me this is a real gap and not just bad vendor behavior. The solution's components all exist, and some of them are *boring*.

Enterprise software has had source-code escrow since the 1980s. You buy a million-dollar system from a startup, and the contract says: the code goes into a vault at a third party, and if the vendor goes bankrupt or stops supporting you, the vault opens. Routine. Unglamorous. Litigated into predictability over four decades. We have a whole escrow *industry*.

The French now mandate a repairability score printed on certain electronics, like a nutrition label. The EU is legislating how long vendors must supply updates. The right-to-repair movement is winning, state by state. Home Assistant volunteers reverse-engineer dead devices for fun and write local firmware replacements — the Insteon resurrection was literally community work. Cryptographers can split a signing key between five independent parties so any three can act.

Every single component of "your house survives the company that built it" exists in production somewhere. Escrow. Dead-hand triggers. Threshold keys. Longevity labels. Hardware interlocks. Degradation ladders — we specified those in P-004 of this program.

What doesn't exist is the composition. And the composition is the product.

## Why the gap survived every scandal

The uncomfortable economics: you can't see longevity at purchase time, so the market can't price it. There's a clean economics literature on this — *shrouded attributes*. Anything a buyer can't observe, competition over-supplies. Cloud coupling saves the vendor a few dollars per unit and costs you the entire device two years later. Every "outrage cycle" happens after the sale, so it changes nothing.

The second reason is timing, and it's crueler. Community takeover needs the firmware, the specs, and the signing keys — things only the *alive* vendor can give you, delivered precisely when a dying vendor has the least interest and capacity to give them. The only window to arm the rescue is while everyone's happy. Which means the mechanism has to be built into the sale, not negotiated at the funeral.

That's the whole design insight in one line: **escrow at sale, not goodwill at death.**

## What the paper actually specifies

The device succession manifest — a signed, public declaration of what works locally, what needs the vendor's cloud, and what happens when the vendor goes quiet. The dead-hand release: renewal proofs published to a public log, and *silence* — bankruptcy filings, expired certificates, a lapsed domain — is the release trigger. No goodwill required, because nobody alive is required.

The hardest part is keys, and the folklore says it's impossible — "you can't just give away firmware signing keys." You can. You burn a *commitment to a future quorum* into the device at manufacture, and when the vendor dies, a threshold of pre-committed stewards generates the succession root. Standard threshold cryptography. The only novelty is institutional: a boot chain that finally admits the vendor is mortal.

And at the bottom of the ladder, physics: a fossil mode, manufactured into the hardware, guaranteeing the lock still locks and the thermostat still heats with all software dead. The floor of the contract is a deadbolt, not a policy.

## Who moves first

Not consumers — consumers can't see the attribute yet. Hotels can. Property managers can. Municipalities can. They buy devices in fleets of thousands, hold them for a decade, and already read lifecycle terms in contracts; that's where enterprise escrow came from. One procurement checkbox — "must ship a succession manifest" — and the market starts sorting. The label follows the fleet. It always does.

If you run infrastructure for buildings, this is the paper to hand your vendor. Not because it's philosophy — because it's a purchase order waiting to happen.

The devices were always ready to outlive their makers. Now the protocol is too.
