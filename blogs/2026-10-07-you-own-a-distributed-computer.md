---
title: "You Don't Own Five Computers. You Own One Bad Computer."
date: 2026-10-07
author: p-rick research program
paper: p-007-intermittent-compute-fabric
---

# You Don't Own Five Computers. You Own One Bad Computer.

Count the machines you own: phone, laptop, desktop, tablet, watch, maybe a console and a NAS. Add up the cores, the memory, the GPUs, the sensors. That aggregate is more compute than most startups had a decade ago.

Now watch how it actually behaves. Your phone strains to run a 7B model while the desktop GPU idles across the room. Your video call wants the phone's camera while the laptop does the processing — impossible, so the phone does both, badly. Your files are on the NAS, your working state in a sync folder, your compute rented from a cloud that bills monthly and reads by the byte. Two machines in the same room communicate through a server in another hemisphere.

Five islands, one owner, a metered bus between them. The fabric joining your own machines is worse than the fabric joining you to strangers.

## We tried to build this once. It died. Know why.

2012: the mobile offloading literature was thriving. MAUI moved methods to servers to save phone battery. CloneCloud partitioned computation via VM migration. Odyssey had done application-aware adaptation a decade earlier. Then the line went quiet, and the honest post-mortems read: NATs made reachability a thesis per session; running foreign code was a wound; binaries didn't port; battery economics favored just using the cloud; and — the real killer — no workload *needed* it. Sync services moved documents. Documents don't need remote execution.

Check those death conditions against today. Reachability: your personal mesh VPN solves it in a weekend — WireGuard underneath, identity on top. Execution: WASM and containers make code placement boring. Heterogeneity: place by capability match, not architecture match — the GPU job goes where the GPU is. Economics: the joules are already *bought*; the question is placement among owned machines, not rent-versus-battery. And the workload finally exists: local AI — divisible, placement-sensitive, privacy-shaped. Petals proved collaborative LLM serving over consumer GPUs. Every phone and laptop now ships an NPU.

Every death condition expired, and the field never looked back. That's the gap.

## What "one machine" actually means

The paper specifies it formally, but the mental model is simple. Your device set becomes a single schedulable machine with an unusual failure model — cores that sleep on their own schedule, join and leave unpredictably, and have energy budgets of their own.

That failure model is the design. A phone locking is not an error; it's *scheduled unavailability* — the scheduler's connectivity model treats it as input, resumable tasks checkpoint and move. Partitions aren't incidents; they're constraints — placement runs against predicted reachability windows, so a two-hour job lands on the desktop only if the model says the desktop will actually be there.

Around that: capability delegation — a scoped token by which the laptop's app borrows the phone's camera, with expiry, revocation, and an audit trail on both ends (Universal Control's feel, as an open API instead of a vendor's curated moment). A CRDT state layer where location is an implementation detail — your data is where the task is, or the task goes to the data, and energy prices the choice. And a policy surface that keeps the owner, not the platform, as the placement authority: *nothing of mine runs on the work laptop; GPU jobs only on wall power; my data never leaves my devices.*

Notice those three phrases. Placement policy. Energy preference. Privacy boundary. No consumer product on earth lets you say all three today, about your own machines, in one sentence.

## The window is two or three years

Here's the strategic claim. Distributed inference over owned devices is the fabric's killer workload, and it's arriving now — private AI, agent runtimes, model sharding across the phone's NPU and the desktop's GPU.

The closed implementations are converging on the same space from above: vendor continuity plus vendor AI stacks, annexing "your devices, one machine" into walled gardens, the same annexation that happened to synchronization a decade ago (nobody runs their own sync anymore; it's all iCloud and Dropbox). When the annexation completes, cross-device compute becomes one more thing you rent, on their terms, with their model of your data.

The open alternative has a trajectory we've already watched work: Home Assistant took the userspace fabric for sensors — no vendor blessing, one static binary, a community — to millions of installations. Mesh VPNs did the same for reachability. Homelabs do it for scheduling. The pieces are maintained by people, for people, right now.

What's missing is the composition: scheduler, capability protocol, task semantics — the programming model that turns five owned islands into one machine. That's the paper. The islands are real, the sea between them is drained, and the bridges are unbuilt.

The first one is the most valuable infrastructure nobody is building.
