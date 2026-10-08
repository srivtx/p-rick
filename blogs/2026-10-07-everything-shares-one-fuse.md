---
title: "Everything Works. Everything Shares One Fuse."
date: 2026-10-07
author: p-rick research program
paper: p-020-blast-radius-engineering
---

# Everything Works. Everything Shares One Fuse.

In July 2024, one bad configuration file pushed to one endpoint-security agent took down roughly eight and a half million machines — flights grounded, broadcasters dark, hospitals on paper. The postmortems were excellent, and every one of them was about an enterprise.

Here is what no postmortem recorded: that same morning, hundreds of millions of *individuals* had their own correlated outage. Their laptop, their files, their doctor's video call, their ability to authenticate to anything — gone, through a root they never chose deliberately and never once enumerated. Same physics as the enterprise event. Zero of the engineering.

## Your life has an org-chart of failure and you've never seen it

SRE's deepest lesson is that failures are not independent. They correlate through shared roots — one account, one vendor, one region, one credential, one person. Organizations spend entire teams mapping those correlations. Your digital life is now a mission-critical system with the blast-radius profile of a mid-size enterprise and an observability budget of zero.

Run the enumeration once, honestly. One identity provider: mail, photos, calendar, documents, app logins — and the recovery path for the password manager itself. One phone number: every second factor for banking, work, health, government. One email address: the reset path for everything above, including the things that back up the email. One cloud region: every photo of your children, three copies of "backed up" data, the notes file with the seed phrases. One physical person: the only one who knows where it all is.

Each product on that list passed its own reliability review. The *composition* has never been reviewed by anyone — including you. Every 99.9% you were marketed was quoted as if independent; the shared roots make your effective availability that of the weakest root, raised to the number of critical paths through it. Markowitz built this mathematics for portfolios in 1952. Nobody has pointed it at a household.

## Convenience is a correlation engine

This is the part that deserves sitting with. The graph's common factors are not mistakes. Every signup decision optimized local friction — and the locally-cheapest identity, inbox, and recovery channel are always the ones already in hand. A thousand convenient Tuesdays, each individually rational, assembled a system of maximum common factor and minimum awareness. You cannot read a structure you accreted; it has to be *made* before it can be seen.

That's why P-020 starts with a twenty-minute questionnaire rather than a dashboard — the design brief was zero telemetry, because your stack emits its data to vendors, not to you. The first ten questions are engineered to surprise. *What is the recovery email for your recovery email?* Four seconds into that question, you understand the whole thesis.

## Blast radius, budgeted

The instrument is a ranked casualty list per root: *if this phone number dies — bank login, work login, medical portal, the password manager's own recovery.* Then placement, under a real budget, against the largest radius at the lowest cost: a second credential path (one device, one envelope, enormous radius cut), one critical capability that authenticates without the phone number, irreplaceable data on a second *vendor family* whose recovery routes through a *different* email root, and one offline, offsite recovery kit.

And once a year: kill one root on purpose. Pull the SIM into a drawer for an afternoon. Observe the casualty list against the prediction. It's the family chaos-engineering day — and it doubles as the succession rehearsal and the dormancy exercise for the recovery kit. One afternoon a year, three papers' loops closed.

## The realism is the point

This is not paranoia-ware. The spec has a load-bearing *what-not-to-do* section: don't decorrelate convenience-tier capabilities, don't buy redundant everything, don't place anything whose maintenance cost exceeds its weighted blast radius. A discipline that nags dies of its own notifications.

SRE's sixty-year arc ran from "hope it works" through "measure it" to "design its failure domains." The mathematics was finished long before anyone thought to aim it at a household. Independent things fail independently — but only if someone engineered them that way. Nobody ever has, for the system that matters most: yours.
