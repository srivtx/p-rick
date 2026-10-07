---
title: "The Spreadsheet Lied to You. It Was Designed To."
date: 2026-10-07
author: p-rick research program
paper: p-015-uncertain-document
---

# The Spreadsheet Lied to You. It Was Designed To.

In 2013, a graduate student asked for the spreadsheet behind a famous economics paper — the one whose threshold claim had anchored austerity budgets on two continents. Thomas Herndon found that the authors' Excel formula averaged the wrong rows. Five countries' data never entered the calculation. The correction swung the headline result.

The industry took one lesson: audit your spreadsheets. It's a fair lesson. Panko's research program spent decades auditing them: file-level error rates near 90%, cell error rates around 1–3%, stable since the nineties.

But the deeper lesson is the one nobody took: **the artifact's physics made the error invisible.** A cell holding a bare number says nothing about where it came from, what was included, how wrong it might be, or what happens downstream when it is wrong. The spreadsheet didn't fail because humans are careless. It failed because a point-estimate artifact is epistemically opaque *by construction* — it displays the fiction of exactness in every cell, and the fiction is exactly what everyone downstream believed.

## The laboratory solved this a century ago

No physicist reports "3.2." They report 3.2 ± 0.4, with the measurement protocol and the confidence stated, because metrology's GUM standard — the Guide to the Expression of Uncertainty in Measurement — has required it for a century. Every engineering discipline that touches matter runs on it.

The rooms where civilization's *actual* numbers do civilization's actual work — the budget, the project plan, the hospital summary, the policy memo, the news article — never imported the standard. Not because the math is hard. Because the artifact had no place to put the error bars, and the display culture had every incentive not to.

Because that's the real mechanism: a number displayed as "3.2" is *believed differently* than one displayed as "roughly three." The digits perform authority. The presentation science — Gigerenzer's natural frequencies, the calibration-training literature, the fact that the public reads probability-of-precipitation just fine — proved that civilians can read uncertainty *better* than false precision when the presentation is engineered. The office suite chose the form that manufactures confidence, and it was never a decision anyone remembers making.

## Where does the uncertainty actually go?

Here's what makes it an accounting problem: the uncertainty never disappears. Organizations *know* their estimates are fuzzy. So they pad — privately, in estimators' heads, personal multipliers passed down as folklore. The plan is a negotiation performed in point-estimate theater, and the padding lives in humans where no system can see it.

Every adjacent tool confirms the gap by its boundaries. Monte Carlo add-ons bolted distributions onto the grid for a trained priesthood in dedicated risk workbooks — while the organization's operative documents stayed point-native. Scenario tools like Causal made distribution-native *models* — islands you visit, while the numbers that actually circulate (deck, memo, contract) travel as bare points. Probabilistic programming gave the experts Stan and PyMC and gave civilians nothing. Interval arithmetic has been textbook-complete since 1966 and product-absent since 1966.

Uncertainty that doesn't survive copy-paste is uncertainty that dies at the organization's first boundary. Which is to say: immediately.

## The quant

The fix is a type. The document's atomic numeric type becomes the **quant**: {point, distribution, provenance, confidence, units, created-at}. A bare number becomes a quant whose distribution degenerated to a delta — the system flags it as *epistemically naked*, the way a linter flags an unhandled case.

Propagation is a tiered engine — interval arithmetic for the linear cases, Monte Carlo for the general, GUM's law as the first tier — and it's invisible. Civilians never see math. They see results whose honesty is *computed* rather than asserted by footnote.

The display contract is where the presentation science cashes out: "roughly 3.2k (90%: 2.1–4.6k)" with the full distribution one hover away. Charts render bands by default, not points. Calibrated language binds "very likely" to actual numbers, the way the IPCC does it.

The transport rule is the one that changes everything: quants survive copy-paste, export, and APIs. The deck pasted from the plan inherits the plan's intervals. The uncertainty rides the number across every boundary — the same trick units-of-measure types already pulled off in real compilers. If meters can ride a value, distributions can.

## The sharpest instrument: the ledger

The part no artifact has ever had: **retro-scoring its own numbers.** When outcomes arrive — the actual duration, the actual spend — the document system scores its own past claims. Brier-style, with bias decomposed: *this team's 90% intervals have covered 62% of outcomes over eight quarters. Intervals too narrow. Durations 12% optimistic at the 90-day horizon.*

Reference-class forecasting stops being a consultancy and becomes a query. Calibration training's literature says the feedback loop measurably improves estimators. Nobody has ever built the loop into the artifact — because point-native documents can't remember their own claims, the organization's estimation bias is invisible *by construction*, every quarter, forever. The gap is self-concealing. That's why it survived.

## The claim, precisely

Not that everything becomes fuzzy. Counts are counts; prices at the register are exact; the quant degrades to a delta with zero display overhead. The claim is narrower and harder: **the estimates stop impersonating the exact numbers.**

The number was never certain. The laboratory admitted it in the last century. The office, the hospital, and the ministry still run on the fiction — and the fix is a type, a display contract, and a ledger. All specified. Nowhere built. Yet.
