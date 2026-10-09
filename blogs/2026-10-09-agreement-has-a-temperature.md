---
title: "Agreement Has a Temperature"
date: 2026-10-09
author: p-rick research program
paper: p-029-lock-in-law
---

# Agreement Has a Temperature

You've seen the transcript. Five agents, seeded with different takes on a question. Round one: real disagreement, three positions on the board. Round four: a majority has crystallized. Round seven: the dissenters' language has softened into hedged agreement, and by round ten the collective has one confident answer — right or wrong — and everyone's fine with it.

The industry calls this groupthink and manages it by feel: "mix the models," "keep the temperature up," "reset the context sometimes." All correct. All useless without numbers. So: [The Lock-In Law](pdfs/p-029.pdf).

## $K/T$: the one dial

The minimal collective — binary positions, public statements, shared board, memory — turns out to carry a textbook phase transition, and the control parameter is one you can compute from your deployment config. Coupling $K$ is how much of each agent's next belief comes from what the others just said (a shared-scratchpad agent has high $K$; a private-notes agent, low). Temperature $T$ is the sampler temperature you already set. The transition sits at:

$$K_c = T(1 - \lambda)$$

with $\lambda$ the context memory. Below it, the collective stays mixed — genuinely, stably mixed: across 420 replica collectives in our harness, coherence below threshold never exceeded 0.03. Above it, lock. **There is no useful middle.** No configuration is both exploratory and decisive. One dial, one cliff.

That's the reframe worth internalizing: "creative temperature" and "conservative context architecture" are the same dial read from two ends. Share more board, and you've lowered the temperature of consensus without anyone deciding to agree. The collective doesn't groupthink; it *condenses*.

## Four numbers you can compute before round one

**The final confidence** is a fixed point: $m^*(1-\lambda) = K\tanh(m^*/T)$. We measured it at 0.570 against the law's 0.570 — 0.045% error, the cleanest number the program's harnesses have produced. You can know how unanimous the room will get before it speaks.

**The locking time** scales as $\ln N \cdot T/(K - K_c)$. The $\ln N$ is the part that stings: double the fleet, buy only $\ln 2$ more exploration time. Bigger teams do not meaningfully resist condensation — every "we added more agents and they still converged" anecdote is this term.

**The firewall:** run a fraction $f$ of your agents on fresh contexts every round — different models, session wipes, anything that decorrelates memory — and the threshold rises linearly: $K_c(f) = T(1-(1-f)\lambda)$. At our parameters, 40% fresh agents nearly double the coupling the collective tolerates. Diversity isn't a vibe; it's structural defense with a computable level.

**The reset interval:** wipe beliefs every $\Delta$ rounds and the collective stays exploratory if and only if $\Delta$ beats the locking time. The boundary on the map tracks $\tau_{lock}(K)$ — "how often should we restart the session" is a line on a plot, not a superstition.

## The folklore that didn't survive

We tested the truncation story — "top-p pruning causes premature consensus" — directly. On binary collectives: 1.06×. Essentially nothing. The mechanism the folklore needs is minority *option* removal from a multi-option board, which is a different machine; the paper leaves it as a written prediction rather than laundering a null into a claim. (The program's bar: nulls get reported as nulls.)

The design rules that fall out cost nothing but architecture: mixed fleet above the firewall fraction, private-before-public emission, resets inside the locking window, and a $K/T$ you chose on purpose. The scariest line in the paper is also the shortest: agents don't agree because they're right. They agree because you built a condenser.

*Read the paper: [The Lock-In Law](pdfs/p-029.pdf) · [reading edition](../paper/p029.html) · [harness](https://github.com/srivtx/p-rick/blob/main/code/p-029-simulation.py)*
