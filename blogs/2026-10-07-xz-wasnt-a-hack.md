---
title: "xz Wasn't a Hack. It Was a Retirement."
date: 2026-10-07
author: p-rick research program
paper: p-010-bus-factor-protocol
---

# xz Wasn't a Hack. It Was a Retirement.

In March 2024, the world learned that a compression library at the base of nearly every Linux distribution had been backdoored. The postmortems called it a supply-chain compromise. OpenSSF called for hardening. Registries rolled out more provenance attestations, more signing, more artifact integrity.

All of that is good, and all of it missed the point, because the layer that actually failed was not the artifacts. It was the people.

Reconstructed from the maintainer's own archived messages: one exhausted maintainer, carrying a foundational library alone for years, watched a helpful stranger arrive and quietly, competently, take the weight off. Patches arrived. Response times improved. Eventually the stranger had commit rights, then release rights, then the keys. Then he shipped a backdoor through the ordinary release process, with the ordinary signatures, passing the ordinary reviews.

The security industry called it an attack, because that's the vocabulary it has. Read it as a *governance event* instead: a burned-out maintainer executed a succession process — "the tired guy hands the keys to whoever helped" — and the succession process is exactly what the attacker exploited. The code was never compromised. The *maintainership* was.

xz wasn't a hack. It was a retirement, weaponized.

## Registries govern names. Nobody governs the humans.

Every registry on earth — npm, PyPI, crates.io, Maven — has mature machinery for code identity: namespaces, signing, 2FA, provenance, reproducible builds. Zero machinery for *maintainership continuity*. A package with one exhausted maintainer who last touched it in 2019 is, from the registry's point of view, identical to a package with six active maintainers and a documented succession plan.

That's not a metaphor. It's a data model. Maintainer state is simply not a field.

So the most important state in the software supply chain — who holds the keys, are they still alive in the project, what happens when they stop — transitions through private messages between strangers. We have an entire security industry hardening the layer the incidents did not break, while the layer every postmortem walked through runs on folklore. Ask "what do we do when the maintainer disappears" on any forum, any year, and you'll get the same thread, answered from scratch, every time.

## The incident record is one event in five coats

left-pad, 2016: one person's morning mood deleted a dependency of hundreds of thousands of builds — because the graph sat on one human. event-stream, 2018: an uninterested author transferred his package to a helpful stranger with zero oversight; the stranger attacked Bitcoin wallets downstream. That's the xz attack, six years earlier, in months instead of years. colors and node-ipc, 2022: live maintainers weaponized their own packages — a different lesson, honestly scoped in the paper: rogue owners are a different problem from departed ones.

Five coats, one shape: the registry had no model of the maintainership, so the maintainership went to whoever ended up holding the keys, and the blast radius was set in a private chat.

## The protocol, in three moves

**Make maintainer state legible.** A state machine — ACTIVE, DECAYING, DORMANT, ORPHANED — with per-package thresholds, surfaced in the registry UI and API. Not a judgment; a timestamp. Today, staleness is invisible. It shouldn't be.

**Succession policy as code.** A signed manifest per package: who has publish authority, what happens on dormancy, who inherits, with what review window. Bus factor stops being an anecdote and becomes an attribute your CI can query: *fail the build if a production dependency is DORMANT without a declared successor.*

**The anti-xz ladder.** Any *newly elevated* maintainer — by transfer or takeover — releases under co-signature and a public delay-locked review window for their first 90 days. The event-stream hijack fails here outright: transfer, then immediately malicious publish — now structurally impossible. The xz attack gets slower and visible: the transfer event itself is published, and the attacker must sustain 90 days of co-signed, publicly-reviewed releases while the community watches the succession it is currently blind to.

Notice the precision of the one intervention with teeth: new *publishes* freeze in the review window. Installs never pause. A governance layer that breaks the ecosystem to save it would be worse than the disease.

## "Just fork it" misunderstands the asset

The asset is the *name*. Consumers resolve `event-stream`, not a content hash. A fork without the name re-fights the discovery battle the registry exists to settle — which is why succession governance must live at the registry layer, and why "just fork it" has never once rescued an ecosystem's dependency graph in a decade of trying.

The kernel knows this, by the way. Linux's maintainership hierarchy — layered, documented, with succession as routine — is open source's own existence proof that continuity governance is native to the culture when scale demands it. The protocol productizes what Linus's tree practices informally.

The machinery exists. The incidents wrote the requirements. The missing piece was writing the layer down. So it's written down.
