---
title: "Every File You Own Forgot Who It Is"
date: 2026-10-07
author: p-rick research program
paper: p-005-provenance-native-storage
---

# Every File You Own Forgot Who It Is

Take any file on your machine. The important one — the contract, the report, the dataset, the PDF your lawyer sent. Now ask it a simple question: *where did you come from?*

The file knows its size. It knows its modification time. Everything causal — which site or app delivered it, which process wrote it, from which inputs, through which transformations, on which of your devices — is gone. It was knowable at the moment of creation, by the kernel that mediated every byte, and it was thrown away.

We built a civilization-scale archive and gave it total amnesia about its own provenance.

## This was solved in 2006. Then nothing shipped.

Here's the part that should make every systems person sit up. In 2006, the FAST community published PASS — the Provenance-Aware Storage System. Kernel-level capture of file lineage, with single-digit overhead. A whole research line followed: LineageFS, Hi-Fi, CamFlow. Whole-system provenance became a *solved capture problem* twenty years ago.

Zero of it shipped to users. Not a reduced version. None.

The barriers were real in 2006: provenance required kernel patches; disks were small; binaries were opaque; there was no query interface a human would touch. The paper's core argument is that every one of those barriers has quietly expired — kernel event interfaces are now blessed (eBPF on Linux, EndpointSecurity on macOS, ETW on Windows: the EDR industry runs on them), storage is cheap, content-addressing dedupes the ledger, and on-device models can annotate what binaries don't declare.

The gap between "provenance is capturable" and "users have provenance" is now the most valuable unfilled space in client systems. And the AI era just made it mandatory.

## The four amnesias

The paper names four working failures. See how many you felt this week.

**Origin amnesia.** Windows keeps one bit — "came from the internet" (Mark of the Web, a feature from the year 2000). No endpoint, no chain, nothing for files arriving by sync, messaging, or archives. The phishing question — "did this document come from that domain?" — is unanswerable at the layer where users need it, in the exact decade it became the question.

**Process amnesia.** A folder of documents got corrupted. Which app did it? Today: forensics. With a causal ledger: a query.

**Reproduction amnesia.** The transformation `report.xlsx = f(a.csv, b.csv)` leaves no trace of f, a, or b. Version control preserves *states*, never the causal edges between them. Your work is reproducible only if you impose monastic discipline, which is to say, it isn't.

**Impact amnesia.** Nothing can tell you what breaks if you delete a directory. So you hoard. Storage bloat is partly a *causality* failure wearing a psychology costume.

## Why now is different: C2PA taught the market to want this

Content Credentials — the C2PA coalition — did something genuinely historic: it taught camera makers, AI vendors, and platforms that *provenance is a selling point*. Signed history attached to media at creation.

But look at what it covers. Pixels at the moment of creation. Now look at what your life is made of: the report assembled from three sources by an AI, the dataset curated by an agent, the file that passed through two machines. Derived artifacts, assembled artifacts, *transformed* artifacts — the majority of value, with no provenance story at all, because a creation certificate cannot say "this PDF came from those spreadsheets, on this laptop, via this process."

That's not a C2PA competitor. That's the next layer down: the causal chain, recorded by the OS, queryable by the user, shareable on demand. C2PA proved the appetite. The file system should collect.

## The design, in one breath

An append-only, content-addressed event ledger living next to your files: every persistent write recorded with its actor and inputs; every ingress with its channel and endpoint; applications can *declare* transforms through a small API (kernel guarantees facts, apps volunteer meanings); a query algebra on top answering the five questions people already ask in degraded forms — *where did this come from, what breaks if I delete this, reproduce this, what did this app touch, what came from that site* — and surfaces where users already live: the file inspector, the share sheet, the delete confirmation, the search bar.

The surveillance objection is the live one, and the design answers it architecturally: the ledger is local, encrypted, and — this matters — *redactable with integrity preserved*. Provenance systems copied from blockchains get forgetting wrong; a personal ledger must be more forgettable than the files it describes, or it's a liability. The paper spends its threat model there.

The pitch to any platform team reading this: the capture substrate your security team already runs, pointed at the user instead of the vendor. The EDR inversion. First platform to ship it creates the honest-AI trust layer everyone is currently writing manifestos about.

Your files have been trying to tell you where they came from for twenty years. The kernel was listening the whole time. Someone should write it down.
