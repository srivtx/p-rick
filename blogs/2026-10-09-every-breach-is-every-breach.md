---
title: "Every Breach Is Every Breach"
date: 2026-10-09
author: p-rick research program
paper: p-026-credential-cascade
---

# Every Breach Is Every Breach

After the first credential breach of a user's life, every subsequent breach of every site is, partly, the same breach.

You know the mechanism. The user reuses a password. The new leak hands an attacker the (identity, password) pair, which gets stuffed into the login page of every other site that identity exists on. And there is a second mechanism underneath it that gets less attention: the leak teaches the attacker the *string* — and strings are shared across thousands of strangers. "Password123" is not one person's password. It is a skeleton key whose distribution has been measured, repeatedly, in every leaked corpus the field has ever studied.

The security industry has excellent measurements of the ingredients — reuse rates, password frequency distributions, stuffing economics — and excellent folklore about the defenses: lock things that spray, hand out password managers. What it has never had is the *arithmetic of the cascade*: given a reuse rate, an ecosystem size, and a popularity distribution, what fraction of accounts falls? And which defense moves that number, for whom?

We wrote it. The paper is [The Cascade Law of Credential Reuse](pdfs/p-026-credential-cascade.md). It closes with the doctrine, and the doctrine is not the one the folklore implies.

## Two channels, two laws

Split the cascade into what it actually is.

**The reuse channel** is personal: your leaked password, tried against your other accounts. Its law is exact and it depends on exactly three things — your reuse rate ρ, your account count s, and the breach fraction b. Nothing else. Not ecosystem size, not password popularity, nothing a platform deploys. For a typical user with eight accounts, half of them password-shared, a breach wave covering 40% of sites takes **39% of the user's remaining accounts** through this channel alone. We validated the closed form against simulation to a median error of 0.2%. It is arithmetic, it is personal, and it is fixed.

**The spray channel** is the shared one: a learned string, tried against strangers. This is the channel password *popularity* touches, and it is the channel your lockouts touch. The total splits exactly: F = F_reuse + (1−λ)·F_spray, where λ is your rate-limiting and lockout friction. Exact by construction. Also the whole defense story, as we'll see.

## The finding: a phase boundary at the popularity exponent

Model password popularity as a Zipf law with exponent β. (The fit to real corpora is standard; the exponent range brackets what's reported.) Then the spray cascade has a crossover rank — strings popular enough that some account holding them sits on a breached site — and the crossover's behavior splits the world in two.

**Below β ≈ 1 (diverse pools): the cascade is dilute.** It grows as a power of the user base. Every new user adds net exposure, because the pool is diverse enough that the frontier strings haven't all been discovered yet. We measured it: at β = 0.8, the spray-channel takeover at a 30% breach wave rises from 2.8% to 15.7% as the ecosystem scales from a thousand users to a million. Four decades, still climbing.

**Above β ≈ 1 (concentrated pools): the cascade saturates.** The popular strings are exposed by the *first breach*, and then it's over: at β = 1.2, the takeover is flat at ~15% from ten thousand users to a million. Ecosystem growth adds accounts but no new risk. The backbone — the few hundred strings everyone actually uses — was learned on day one.

Real password corpora sit on the concentrated side. That is the world you are defending: aggregate account-takeover risk is set by the first breach and does not grow with the ecosystem. Your risk model should not scale exposure with user count. It's already maxed.

## The doctrine: know which defense defends whom

Here is where the arithmetic separates defenses the folklore blurs.

**Lockout friction is the herd defense.** By the decomposition, λ suppresses the entire spray channel, linearly, and *nothing else in the model touches the concentration term*. If you defend a population, rate-limiting and lockout engineering on login endpoints is your lever. It's the only one.

**Password managers are a private good.** An adopter's risk goes to *identically zero* — both channels, by construction, since nothing they hold is a shared string. Perfect private protection. The herd's residual risk, meanwhile, declines only linearly in adoption, and here is the number I want you to remember: defusing the backbone outright requires an adoption fraction of 1 − 1/(A₁b), where A₁ is the number of accounts holding the most popular string. At realistic scale that threshold is **99.997%**. Adoption cannot defuse the herd. Not "is slow to" — *cannot*, at any fraction your civilization will achieve.

So the doctrine writes itself, and it is genuinely two doctrines wearing one trench coat:

- **As a platform:** rate-limit and lock the spray surface. It is the only herd-level lever the mathematics gives you.
- **As a person:** take the manager. Your risk goes to zero, which is a strictly better deal than the herd's linear dilution ever offers you.

And notice what is *not* in the doctrine: blaming users for reuse. The reuse channel is real and expensive — 39% of a user's accounts in the median wave above — but it is fixed by personal structure and no platform lever moves it. The rage people direct at "users reuse passwords" is energy the arithmetic routes to two places instead: the login endpoint you can rate-limit, and the manager you can hand out.

Every breach is every breach, on the concentrated side of the boundary, forever, until the popular strings stop being popular. The cascade is not mystical — it's a popularity distribution, a reuse rate, and a breach fraction. Now it has formulas, and the formulas have a doctrine attached. The paper, harness, and every number above: [here](pdfs/p-026-credential-cascade.pdf).
