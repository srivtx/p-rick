---
title: "The Software You'll Need in Ten Years Is Rotting in a Drawer"
date: 2026-10-07
author: p-rick research program
paper: p-019-dormancy-engineering
---

# The Software You'll Need in Ten Years Is Rotting in a Drawer

There is a boot stick in a drawer in a data center in Mumbai. Minimal OS, system image, six laminated steps. It has not been booted since it was sealed. An amateur radio club keeps emergency firmware that was "refreshed annually" in principle and untouched for three years in practice. A law firm's evidence vault holds encrypted containers and the tool that reads them, four years into a sleep that may end in a courtroom.

These artifacts share one property that outranks every difference: they get used exactly when everything else has already failed. The boot stick boots when the hospital is down. The firmware configures when the network is gone. That moment of maximum dependence is their moment of minimum preparation — and the years in between are not neutral. The drawer is not a vault. It is a slow-fire furnace with excellent marketing.

## Two mature regimes, and a hole between them

The industry handles time in two ways. Always-on: CI, canaries, chaos drills — systems prove themselves by never stopping. Archival: Software Heritage preserves sources for historians, treating executability as a bonus. Both work.

Neither covers the drawer. The boot stick cannot run continuously — being offline *is its security model*. It is not a source tree you recompile — its entire value is turning on with zero build infrastructure, in a building that may not have a network. Dormant software must be preserved like an archive and operational like a service, while being neither. That intersection has no name, no metrics, and no discipline. P-019 gives it all three: **dormancy engineering**.

## What actually kills sleeping software

Four channels, each enumerable, each with its own sensor. **Capability drift**: the TLS cipher the old handshake speaks, the syscall that got removed, the cloud endpoint that 404s — the world edits itself on a clock. **Credential expiry**: certificates, tokens, signing keys die politely in the dark while nobody looks; the 2021 root-certificate expiry that knocked legacy devices off the web is the public demonstration that clock-time kills stopped systems. **Media decay**: the USB stick — the most popular emergency-kit medium on earth — is among the *worst* storage media for multi-year dormancy. **Knowledge decay**: the six laminated steps outlive the one engineer who knew why step four has a 90-second timeout.

The seed vaults solved this decades ago — for seeds. They don't just store; they germination-test samples on a schedule, measuring *viability*, not presence. That distinction — checksums prove the bits, germination proves they still grow — is the entire thesis, transplanted.

## The discipline, in one paragraph

Declare a dormancy class with a wake bound: this kit wakes within four hours, exercised semiannually. Maintain a drift ledger — the actuarial table of your dependencies' observed churn. Run a probe ladder: cheap presence checks monthly, capability checks quarterly (TLS handshakes against your endpoints, from an isolated box, without waking the artifact), full exercises annually against a representative workload. Version a readiness manifest that names a *role*, not a person, as owner. And at the end, the consumer of the artifact — the hospital administrator, the judge, the emergency coordinator — gets one sentence they can act on: *this will wake within four hours; here is the proof it still can.*

## "Just containerize it" is the illusion doing the most damage

A container is a snapshot of an environment contract — and the other party keeps editing the terms. Registries purge unused images. Base images churn under CVE pressure. The image freezes your side of a deal the world rewrites annually. The drift ledger is precisely the missing other side.

The always-on regime won the culture so completely that "stopped" became a failure to page about rather than a regime to engineer. Meanwhile the folk answer — "just boot it once a year" — is right, the way "just eat less" is right. The unpriced parts are the whole discipline: who owns the calendar across reorganizations, what counts as a pass, what happens on a partial pass, who renews the credentials. Institutions that run calendar-based assurance for decades — arsenals, seed banks — prove it's doable. Software, the most churn-dependent artifact class we've ever produced, is the last one still filing its emergency kits under a laminated promise.
