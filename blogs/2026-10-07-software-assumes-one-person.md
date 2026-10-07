---
title: "Software Assumes You're One Person. Half of Humanity Isn't."
date: 2026-10-07
author: p-rick research program
paper: p-013-delegated-operation
---

# Software Assumes You're One Person. Half of Humanity Isn't.

Fifty-three million Americans are unpaid family caregivers. That's the AARP's number, and it counts the people running a parent's phone plan from another city, the adult children doing their mother's banking over a video call, the spouses managing medications through portals designed for exactly one human: the patient.

Watch how that banking actually happens. The parent shares their screen. The child operates the parent's bank through the parent's mouse for forty minutes, reading statements aloud, catching timeout screens. Every layer of authentication the bank ever built — device fingerprinting, fraud detection, "unusual login" heuristics — is right there, watching this happen, wrong about all of it.

The industry's fraud model classifies this scene as account takeover. Millions of times a week, the attack the model is trained on is a daughter helping her father.

## The assumption underneath everything

The single-principal assumption: one account, one human, present and able. Unix inherited it from the terminal. OAuth generalized it. Every consumer product on earth ships inside it. And it's not four assumptions, it's one with four faces: identity equals actor. Presence equals capability. Consent is continuous. Account equals person equals life.

Each face is false in caregiving, in childhood, in illness, in every human arrangement where the person *operating* the software isn't the person the software is *for*. The last third of life runs entirely on this failure. So does childhood. So does half of every household.

And here's the thing that should stop every security team cold: the workaround the world actually built is the *worst possible architecture* — shared passwords on notepads, credentials in family vaults, months-long sessions on foreign devices. If an attacker designed the ideal compromise of a banking relationship, it would look exactly like eldercare in 2026. The users built it because we never gave them the protocol. The notepad password is our architecture, executed by civilians.

## The pieces all exist

Email has had delegated access for two decades — a real operator pattern, sitting right there, never spread to the rest of the product.

Parental controls built the machinery: approval workflows, consent between devices, per-category grants. Wrong authority direction for eldercare, wrong privacy model — a nine-year-old's surveillance-grade visibility is an assault on a seventy-nine-year-old's dignity — but the gears are real.

Enterprise solved the whole pattern decades ago: RBAC, break-glass, audit trails, just-in-time access. Priced for organizations, never ported to households. OAuth solved delegation for *applications* and spent a decade letting its "delegated authorization" vocabulary confuse everyone about *humans*.

Six mature fragments. Zero compositions. That's the gap, and it survived for the most honest reason in this whole essay: **the security orthodoxy classified the use case as the threat.** "Someone else is in the account" is the canonical attack. Nobody's data model had a second legitimate principal, so it became a support exception — the agent who quietly helps grandma's caregiver and asks no questions. Exceptions don't become protocols by accretion.

## The protocol, in one breath

An **operator** principal with their own authentication, linked to the primary through a *grant*, not a credential. Operation as **capability bundles** — acts, in the product's own vocabulary: view statements, schedule payment under X, refill the prescription. Never the password itself.

A **graduated ladder**: observe → advise → co-act → act within bounds → break-glass. Escalation needs consent when capacity exists; *de-escalation needs nobody's* — the asymmetry that keeps dignity intact.

Every grant time-boxed, device-bound, purpose-scoped. Every act in an audit log the *primary owns* — readable, exportable, shareable with an attorney. And — this is the part no current architecture even imagines — **drift detection aimed at the operator**, because the operator's session is now the crown jewels, and because the elder-abuse literature tells us the threat often arrives holding a legitimate grant. Bounds cap the blast radius. The audit log creates the evidence that today's notepad-based abuse never leaves. Drift detection catches the slow creep.

Then the ends, because grants end: revocation at one gesture, handover ceremonies between siblings, and a death transition that settles the grant like an estate instead of a suspension email.

## Why now

The demographic clock runs one direction. The consent column on every transaction — consensual, disclosed, or externality — is the same instrument the environmental movement needed when rivers caught fire: not a prohibition on relocation, just a record of who paid.

The technology question is settled. The identity question is the last one anyone changes, which is why it's the one worth specifying now, in public, before someone ships it badly and calls it family sharing.

One account, one human was never a description of humans. It was a description of terminals. The terminals are gone. The assumption is still here, and 53 million people are operating its failure every week with a notepad and a video call.
