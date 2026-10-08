---
title: "Your Senses Have No Failover"
date: 2026-10-07
author: p-rick research program
paper: p-014-modality-failover
---

# Your Senses Have No Failover

There's a photo that circulates after apartment fires in the deaf community: a smoke alarm on the ceiling, intact, having done its job perfectly. It sounded. Nobody heard it.

The hardware worked. The system failed silently — and the silence is the design.

The fire-safety numbers behind that photo are architectural, not anecdotal: adults over 65 die in home fires at more than double the general rate, and roughly 15% of adults report hearing difficulty. But those are the *permanent* channel failures. The situational ones hit everyone: the phone buzzing once across the bedroom at 3 a.m., the visual flash buried under a fullscreen game, the headphones on, the factory floor at 95 dB, the phone in a pocket on a motorcycle.

Engineers have a word for what every one of those scenarios is: **channel death**. And we have a whole discipline for what to do about it — everywhere except the human sensory layer.

## The one component guaranteed to fail, wired with no backup

Storage has RAID. Networks have multipath. Power has backup feeds. Flight control has dissimilar redundancy — the aviation tradition of making critical paths fail in *different ways*, because two things that fail the same way fail together.

And the one component in the stack with a known, large, *growing* failure rate — human perception of a single channel — is wired as a single string: app to OS to one speaker, or one LED, or one vibration motor. Out. No health check, no failover, no acknowledgment, no escalation. The person asleep is not a user state in any notification system on earth; it's an assumed absence.

Three assumptions make this invisible. The channel is available. The channel's state is known. Delivery equals receipt. The third one is the killer: no civilian alert system asks whether the message was *perceived*. There's no acknowledgment, so there's no escalation on silence, so there's no audit of the silence.

The hospitals learned what that absence breeds — they call it alarm fatigue, hundreds of unactioned alarms per shift, desensitized staff, and the critical signal drowning in its own redundancy. ECRI ranked alarm hazards at the *top* of health-technology hazards, year after year. The Joint Commission wrote a national safety goal about it. That's what happens when you maximize alert count with no perception model and no escalation grammar.

## The fragments have existed for decades

The deaf community built the answer as hardware: strobes, bed shakers, wearable receivers — cross-modal delivery, proven, per-room, purchase by purchase. The retrofit market solved the device and never the protocol.

Emergency broadcasting solved the message layer: OASIS's Common Alerting Protocol — one alert, many delivery paths — and the unique tone-plus-vibration pattern that emergency broadcasts carry. CAP standardized the message. The receiving end — which sense, which device, whether the human noticed — is outside the standard.

On-call systems solved the semantics: acknowledgment-gated escalation, walk the graph until someone confirms, timing budgets, audit. Twenty years of production-hardening — pointed at engineers' phones, never at humans' senses.

The on-call world made the bargain decades ago: for the alerts that matter, silence must mean something. Every hospital and every paged engineer accepted it. Our phones run the opposite bargain: for every alert, silence means nothing, because no alert is ever confirmed by anyone.

## RAID for the senses

The specification composes the fragments into a platform protocol:

**Criticality classes** — advisory, action, life-safety — *granted* by the platform to accredited senders, never self-declared. The exact governance emergency broadcasters already run, one layer down.

**A capability profile**: local, private, per-person. Which channels are live *right now* — headphone state, noise floor, sleep schedule, driving. A routing table, never a diagnosis. Your biology stays on your device; only the routing leaves the table.

**k-of-n delivery**: life-safety alerts land on two concurrently healthy channels simultaneously — sound plus haptic plus visual, not serially. The RAID-1 principle. Sensory substitution science proved the brain doesn't care which channel arrives; Bach-y-Rita's work licensed this biologically in the sixties.

**Acknowledgment-gated escalation**: delivered ≠ perceived ≠ acted, and the protocol stops conflating them. No acknowledgment in the latency window, the alert walks: remaining modalities, then devices — wearable, bedside, car, TV — then the room, then *people*: housemates, neighbors on a consented mesh, emergency contacts, and finally the services pathway for life-safety. Terminate on receipt, record the audit event.

**A governor**, because the safety layer must not become the engagement economy's next conquest: escalation budgets, sender demotion telemetry, silence-debt accounting. The clinical alarm-fatigue literature wrote the failure mode; the governor is the correctness requirement.

## The number that matters

The evaluation's headline deliverable is a wall-clock number: a life-safety alert fires at 3 a.m. for a sleeping user, phone charging out of reach, wearable on wrist — how many minutes does the walk take, and at which step does the house learn its person didn't notice?

Every component exists in some adjacent world. The composition is one product decision in any platform team's scope. The first platform that ships it will have answered a question the fire statistics have been asking for a hundred years:

The alarm sounded. Did anyone receive it?
