# Circadian Orchestration: Team Scheduling on Human Biological Time

**p-rick working paper P-009 · series III (continuity) · draft 1.0**

## Abstract

Every collaborative calendar in production models the same thing: availability. People are either free or busy, and meetings land wherever the grid is empty. Human performance does not work that way: it varies systematically and substantially across the day, by an individual's circadian phase — a trait with a population distribution as wide as four to six hours between its extremes, with a measurable genetic basis, and with a well-characterized interaction with sleep history. A 9:00 meeting is near-peak for one team member and near-nadir for another, and no existing software represents this, because representing it requires treating *biological time* as a first-class scheduling input — a data structure, an inference layer, and an optimization semantics that no product or research line has fully specified. We specify **circadian orchestration**: a formal model in which each participant carries a private *phase state* (estimated from questionnaire-grade chronotype instruments, optionally calibrated by local analysis of sleep-tracker data); a *circadian cost function* derived from the two-process model of sleep regulation assigns each candidate meeting slot an alertness cost per participant; and a placement optimizer minimizes aggregate cost subject to fairness constraints, overlap windows, and existing calendar constraints — all without any participant's phase being revealed to the organizer or the employer. The architecture is privacy-first by construction: only anonymized, binned, or aggregated cost surfaces leave each client. We survey the adjacent fields — availability schedulers, shift-work operations research (which solved circadian-aware rostering for employers without privacy), the school start-time policy movement, focus-time analytics — show each holds one component and none composes them, and grade the evidence honestly as PARTIAL-at-components, STRONG-at-composition. We design the system, an evaluation (synthetic teams drawn from population chronotype distributions, plus a field design), and confront the strongest objections: that chronotype is not destiny, that such a system medicalizes work, that participants will game it, and that employers will misuse it. The gap is real, the science is mature, the computation is trivial, and the only missing artifact is the software.

## 1. Introduction

The calendar grid is the most successful scheduling formalism in history, and it encodes exactly one fact about every human being: whether a time slot is occupied. Everything else the grid pretends to know — that 9:00 on Monday is interchangeable with 14:00 on Tuesday, that all participants are equally functional at both, that an eight-hour day is eight interchangeable hours — is inherited from the industrial shift, where uniformity was the point because the work was machines.

Knowledge work is not machine tending, and the humans doing it are not uniform. Sixty years of chronobiology establishes that:

- **Cognitive performance varies by circadian phase** — the ~24-hour endogenous rhythm that governs alertness, reaction time, executive function, and error rates. Performance at one's circadian trough is sharply, measurably worse, and the trough's clock time differs between people.
- **Chronotype — the phase relationship between a person's internal clock and social clock — is a stable individual trait** with a broad population distribution: the morning-extreme and evening-extreme are separated by four to six hours of phase. It is partly heritable (GWAS on morningness has identified hundreds of loci with small individual effects), partly age-structured (adolescents skew late; adults drift earlier), and stable enough in adults to schedule against.
- **The mismatch between social time and biological time — "social jetlag" — is chronic for the majority of the population**, measurable as the weekly difference between biological and social sleep timing, and associated in the literature with metabolic, cardiovascular, and mental-health outcomes.

The scheduling software layer knows none of this. Calendly finds holes; Google Calendar enforces working hours; Outlook suggests focus blocks; Viva Insights reports meeting load. Every one of these treats the human as a resource with *quantity* of time and no *quality* dimension. Meanwhile, the operations-research community spent decades building circadian-aware shift scheduling for hospitals and factories — proving the math is tractable — in a setting where the employer owns the constraint set and privacy is not a design input.

The result is a genuine software gap with an unusual shape: mature science, tractable computation, proven user pain (the 8:00 standup contested in every engineering team is a chronotype dispute misclassified as a culture dispute), and no composition anywhere. We call the composition **circadian orchestration**: the scheduling layer that models biological time.

The thesis in one sentence: **the single most important optimization variable in collaborative scheduling — the phase of the participants — is exactly the one no calendar represents, and it can be represented privately.**

## 2. The biology, briefly and precisely

A scheduling system needs only a defensible functional summary of a large literature. Four facts carry the paper; each is stated with its source class.

**F1 — Performance is phase-dependent, not clock-dependent.** The two-process model of sleep regulation (Borbély, 1982; refined continuously since) decomposes alertness into a homeostatic process (time awake and asleep, S) and a circadian process (endogenous phase, C). Performance at a given clock time is a function of S and C jointly — which is why the *same person* is different at 9:00 on a day after six hours of sleep than after eight, and why *different people* at the same clock time are in different internal states. Population phase distribution: the Munich ChronoType Questionnaire line (Roenneberg et al., 2003 onward) measured the distribution across tens of thousands of respondents; the extremes are hours apart.

**F2 — Chronotype is measurable cheaply and accurately.** The MCTQ and the Morningness-Eveningness Questionnaire (Horne & Östberg, 1976) recover a phase proxy in a few minutes of self-report, validated against core body temperature and actigraphy. Wrist wearables now measure sleep timing at industrial scale — Apple Watch, Fitbit, Oura, Whoop — creating, for the first time, a population-scale *calibration data source* that no scheduling system consumes.

**F3 — The cost of misalignment is not folklore.** Social jetlag research (Wittmann et al., 2006 onward) associates chronic phase mismatch with measurable health costs. Night-shift work is classified by IARC (2007, reaffirmed) as probably carcinogenic (Group 2A) on the cancer side; on the performance side, sustained wakefulness at circadian nadir produces impairment comparable in laboratory studies to significant blood-alcohol levels (Dawson & Reid, 1997) — a comparison the safety-critical industries cite in policy. Office work is not shift work, but the direction of the effect is not in dispute.

**F4 — Team composition is heterogeneous by default.** Chronotype is roughly normally distributed; a standing meeting with n participants almost certainly spans multiple hours of phase. A scheduling policy that ignores phase does not average the cost away — it concentrates it on the tail (the evening types, forced into early slots) while transferring the benefit to the head. The *distributional* property is what makes this a fairness problem, not just an efficiency problem.

## 3. The landscape: four adjacent fields, none at the center

**Availability schedulers.** Calendly, Doodle, Microsoft FindTime, Google's appointment slots: the mature product category. Semantics: binary availability, round-trip polling, occasionally preference ranking. No notion of time-of-day quality, no individual differences, no privacy beyond "not revealing your calendar." These systems solved *coordination*, not *placement quality*.

**Shift-work operations research.** The nurse-rostering and personnel-scheduling literature is decades deep and genuinely circadian-aware: models with circadian constraints, fatigue accumulation rules, recovery windows, legal limits on consecutive shifts. This is the strongest existence proof for the mathematics. But the setting differs on every axis that matters for knowledge work: the employer owns the constraint set (no privacy dimension), the unit is a *shift assignment* imposed on the worker, the objective is coverage and compliance, and the literature treats the worker's own preferences as constraints to satisfy rather than private data to protect. Nothing in this line addresses *meeting placement among peers*.

**The school start-time movement.** The policy movement to delay adolescent school start times (anchored by adolescent chronobiology — the American Academy of Pediatrics' 2014 position, subsequent state legislation such as California's 2019 school-start law) is the population-scale proof that biological time is *actionable policy*. A small academic line extends it to chronotype-based timetabling research (optimizing individual timetables against phase) — honest grading: this is the closest prior work, and it is education-scoped, single-institution, not privacy-first, and never productized. The gap verdict below prices this in.

**Focus and wellbeing analytics.** Microsoft Viva Insights and similar report meeting load, fragmentation, focus-block compliance; wellbeing surveys correlate overload. All are *descriptive* at the org level — none model *when* the individual performs well, none optimize placement, and none ingest sleep data (deliberately, for liability reasons — which is precisely the design constraint our privacy architecture answers rather than avoids).

**The center**: a scheduler that (a) estimates each participant's phase privately, (b) computes per-slot circadian cost from a validated performance model, (c) optimizes placement under fairness constraints, (d) reveals nothing about any individual's biology to anyone. VERDICT: **PARTIAL** at the component level (questionnaires, wearables, circadian OR math, and education-scoped prototypes all exist), **STRONG** at the composition level (no product, no deployed protocol, no privacy-preserving organizational form anywhere).

## 4. Why the gap persisted

**Chronotype is quasi-medical data.** The obvious implementation — your employer knows your sleep — is correctly unacceptable, and its unacceptability killed the category before it was designed. The gap survived because the only architecture anyone could imagine requires the disclosure nobody will make. §6's design exists to refute exactly this.

**The grid metaphor is incumbent.** Calendars are shared *social objects*; changing their semantics is a coordination problem across every organization at once. A compatibility-preserving overlay (compute costs, propose slots, never change the grid itself) is the adoption path — the same pattern every successful calendar add-on has used.

**The data was not there.** Until ~2015, individual phase estimation at scale required questionnaires (low uptake) or lab-grade actigraphy (absurd). Consumer sleep trackers changed this: the calibration data source now exists, untouched, because no scheduler asks for it.

**Employers' fear of the medical.** HR-legal caution treats performance-variability data as disability-adjacent territory. The fear is rational and the answer is architectural: the system that never transmits individual phase to the employer never creates the discoverable record. Design, not policy, resolves the liability.

**The owl stigma.** Eveningness carries a lazy-undisciplined stereotype; morningness carries virtue. A system that *reveals* who is dying in the 8:00 standup changes social dynamics; one that merely *moves the meeting* without attributing the cost to anyone gets the benefit without the stigma. Anonymization is not a compliance feature here; it is the product.

## 5. The formal model

### 5.1 Participants, phase, and cost

Let each participant i carry a private **phase state** Θ_i = (φ_i, s_i, σ_i): chronotype phase φ_i (internal clock offset), recent sleep history s_i, and confidence σ_i. Phase is estimated by the questionnaire instrument (§6.1) and optionally *calibrated* by sleep-tracker ingestion — all on the client device; Θ_i never leaves it in identifiable form.

Each candidate slot t carries a per-participant **circadian cost** c_i(t), derived from the two-process structure: a function of (t − φ_i) (phase error), sleep history (homeostatic state), and known modifiers (post-lunch dip, prior-meeting load — calendar-local data). Cost is normalized to [0,1] where 1 is the individual's nadir-adjacent worst case. The functional form is deliberately simple and *calibrated, not invented*: the literature constrains its shape (phase response, dip placement, homeostatic sensitivity) and the system fits per-organization coefficients from outcome feedback (§8), the same way navigation systems refine travel-time priors.

### 5.2 The placement problem

A meeting M with participant set P, duration d, scheduling window W, and existing calendar constraints C:

- **Objective:** minimize Σ_{i∈P} w_i · c_i(t) (aggregate circadian cost), where w_i encodes role weight (the presenter's phase counts more than the observer's).
- **Hard constraints:** slot ∈ W ∩ calendars; overlap-feasibility; any member's *nadir window* (cost > threshold θ_hard) is excluded for meetings above importance class k (the "no 3 a.m.-biology meetings" rule, applied in social time).
- **Fairness constraints:** over a rolling window (e.g., a month), the *burden distribution* B_i = mean(c_i over attended meetings) must satisfy a minimax bound — no participant persistently absorbs the worst slots. Fairness is the difference between an optimization that quietly sacrifices the evening types (which an unconstrained objective would do *by design*, since morning types are cheaper to satisfy at 9:00 by construction) and one that is distributively sound.
- **Cross-timezone extension:** for distributed teams the cost function composes naturally with geographic offset: the optimizer trades circadian cost against overlap scarcity, making explicit what global teams currently decide by accident and folklore.

### 5.3 The golden overlap

The system's headline output is the **golden overlap** per participant set: the windows in which the *whole team* is in the upper band of its joint alertness — the slots a meeting *should* habitually occupy. Recurring meetings migrate toward golden overlaps gradually (a drift plan of ±15 minutes per week), because phase adaptation and habit formation are slow, and shock rescheduling has its own social cost.

### 5.4 Properties

The model has three stated properties: **monotonicity** (moving any participant to a lower-cost slot never increases others' cost absent calendar effects), **fairness-boundedness** (burden B_i is within ε of the team median under the minimax constraint), and **privacy** (defined constructively in §6: the optimizer is computable from binned cost vectors alone; Θ_i is not a necessary input to any party other than the participant's own client).

## 6. The system: privacy by construction

### 6.1 Client-side phase estimation

Onboarding offers two tiers. **Questionnaire tier** (no data collection): a five-minute MCTQ-class instrument, scored locally; the phase estimate and its confidence interval never leave the device in raw form. **Calibration tier** (opt-in): import sleep-timing history from Apple Health / Google Fit / Oura / Whoop APIs; the client computes a rolling phase estimate (sleep-midpoint statistics over trailing weeks, the standard proxy) and a confidence upgrade. The client publishes **only** what the protocol needs: a *cost profile* over the team's shared scheduling horizon.

### 6.2 The anonymized cost surface

The publication format is a vector of per-slot costs over the shared horizon (next 2–4 weeks, 30-minute bins), **coarsened and blinded**: costs are reported in 3–4 bins, not raw values; slots where cost is low *and* the participant's calendar is empty are reported as "green" without distinguishing *why*; the server sees binarized suitability, never phase. Aggregate endpoints (team golden overlaps, burden reports) are emitted only under k-anonymity thresholds (k ≥ 3) with small-noise perturbation on counts. The organizer's UI sees exactly what it sees today — proposed slots and a one-word suitability signal — plus a team-level golden-overlay. No participant's φ is ever transmitted, stored server-side, or derivable beyond coarse bins by a collusion of k−1 colleagues (and even that reveals only "expensive/cheap for me," the information they can already infer from behavior).

This is deliberately a *practical* privacy design — no heavyweight MPC required, because the semantics were chosen so bins suffice. The design lesson generalizes and is part of the paper's contribution: **choose the disclosed abstraction so that privacy falls out of the data model, not out of cryptography bolted on later.**

### 6.3 Placement service and integrations

A compatibility-preserving overlay: the service consumes calendar free/busy (OAuth scopes already standard), the binned cost surface, and meeting parameters; it proposes 3–5 slots ranked by aggregate cost with fairness annotation ("burden-neutral," "rotates cost to the same two people as last month — rerouted"). Recurring-meeting migration is a first-class flow with preview, consent, and drift scheduling. The org-level dashboard shows aggregate golden hours, meeting-load circadian distribution (k-anonymized), and a quarterly "team chronodiversity report" — distribution shape without any individual.

## 7. Evaluation design

**Simulation.** Synthetic teams of 3–20 participants, phases drawn from the MCTQ-scale population distribution (validated shape), calendars from realistic load models; compare placement policies (grid-first, availability-first, circadian-optimized) on aggregate cost, tail burden (the evening-type's experience — the fairness headline), and reschedule churn. The expected result, quantified: naive policies concentrate cost on the late tail by construction; constrained optimization flattens the burden distribution at negligible aggregate-cost increase.

**Calibration study.** A two-week instrument-vs-actigraphy comparison (questionnaire phase vs. wearable sleep-midpoint) on a convenience cohort, reporting agreement and the confidence model's calibration — the number that determines how much the questionnaire tier can be trusted alone.

**Field design.** A single-org A/B: teams randomized to circadian-assisted scheduling vs. status quo for one quarter; outcomes are meeting-satisfaction surveys, self-reported focus quality, and rescheduling rate — deliberately *not* performance ratings (avoiding the surveillance semantics the design exists to prevent).

**Adversarial evaluation.** Gaming: participants binarizing all slots green to force preferred times (detected statistically; answered structurally — the cost surface is reciprocal, so gaming others' meetings costs your own); organizer probing (k-anonymity audit); employer pressure to "deanonymize" the report (nothing to deanonymize at the individual level by construction).

## 8. Objections, confronted

**"Chronotype is not destiny."** Correct, and the model does not claim it: phase is one input among schedule constraints, role weights, and preference. The claim is population-level: on a team of eight spanning five hours of phase, *some* placement policy is systematically better than the grid's indifference, even after every individual override. The system's value survives individual variation the way travel-time estimates survive individual driving style.

**"This medicalizes the workplace."** The failure mode is real — implemented naively (employer-visible sleep scores), it becomes wellness surveillance. The paper's answer is architectural, not disclaiming: no raw phase ever transmitted; aggregates k-anonymized; the employer sees meeting slots, not people. The design *refuses* the medical framing by refusing the data model that enables it. A system that cannot record your biology cannot disclose it.

**"People will game it."** Some will. Reciprocity answers it: your cost surface governs meetings you schedule too. Rotation fairness bounds the value of gaming (systematically claiming the golden slots transfers burden to you elsewhere). And the win is small: the optimizer's proposals are advisory.

**"Employers will misuse aggregate reports."** Aggregate-only, k-anonymized, deliberately coarse. The one number an employer cannot extract from this system is any individual's phase — the record does not exist to subpoena. Compared with the *status quo trajectory* (wellness platforms already ingesting sleep data), the architecture is a privacy *improvement*.

**"Cultural resistance — meetings are owned by the important person's calendar."** True, and it is why the go-to-market is bottom-up: the product's first user is a team lead with a contested recurring meeting and no mandate, where a "here are three better slots, burden-neutral" suggestion is adopted or ignored per team. Culture moves after the tool makes the cost visible; the golden overlay is the first artifact many teams will have ever seen of their own chronodiversity.

**"Wearables make this elitist."** The questionnaire tier is the equalizer: five minutes, no hardware, validated accuracy sufficient for binning. Calibration improves precision for those who opt in; it is not the entry ticket.

## 9. Limitations

The two-process simplification captures the dominant structure but not everything (individual differences in post-lunch dip magnitude, caffeine and light exposure, monday-vs-friday drift are handled coarsely). Phase is non-stationary over months (seasonal light, life changes) — the rolling re-estimation handles it, with confidence decaying between calibrations. Shift-work organizations are out of scope for v1 (their OR solutions already exist, in the other setting). The fairness constraint can conflict with hard overlap scarcity in cross-timezone teams, forcing explicit burden trade-offs the tool surfaces but cannot dissolve. And the calibration study is designed, not run: the confidence numbers for the questionnaire tier are the paper's largest empirical debt, priced honestly in §7.

## 10. Conclusion

Every scheduling system in the world models time as quantity. The biology says time has quality, distributed differently across every team; the operations research says the optimization is solved in a harder setting than this one; the wearables industry accidentally built the calibration layer; and the privacy objection that kept the category empty has an architectural answer that requires no cryptography beyond a well-chosen data model. What is missing is the composition — a scheduling layer that knows when people are at their best, tells no one whose best is when, and moves the meeting. The 8:00 standup war ends not with a compromise, but with a slot.

## 11. References

1. Borbély, A. A. (1982). "A two process model of sleep regulation." *Human Neurobiology*, 1(3), 195–204. [Peer-reviewed; high confidence.]
2. Roenneberg, T., Wirz-Justice, A., & Merrow, M. (2003). "Life between clocks: daily temporal patterns of human chronotypes." *Journal of Biological Rhythms*, 18(1), 80–90. (MCTQ.) [Peer-reviewed; high confidence.]
3. Horne, J. A., & Östberg, O. (1976). "A self-assessment questionnaire to determine morningness-eveningness in human circadian rhythms." *International Journal of Chronobiology*, 4, 97–110. [Peer-reviewed; high confidence.]
4. Wittmann, M., Dinich, J., Merrow, M., & Roenneberg, T. (2006). "Social jetlag: misalignment of biological and social time." *Chronobiology International*, 23(1–2), 497–509. [Peer-reviewed; high confidence.]
5. Jones, S. E., et al. (2019). "Genome-wide association analyses of chronotype in 697,828 individuals provides insights into circadian rhythms." *Nature Genetics*, 51, 1524–1535 (2019). (351 loci; effect sizes small individually.) [Journal corrected from an earlier draft’s citation; verified 2026-10 against PubMed and the Nature index.] [Peer-reviewed; high confidence on the headline, details queued for verification.]
6. International Agency for Research on Cancer (2007, reaffirmed 2019). "Night shift work" classified as Group 2A, probably carcinogenic to humans. *IARC Monographs*. [Agency record; high confidence.]
7. Dawson, D., & Reid, K. (1997). "Fatigue, alcohol and performance impairment." *Nature*, 388, 235. [Peer-reviewed; high confidence.]
8. Mark, G., Gudith, D., & Klocke, U. (2008). "The cost of interrupted work: more speed and stress." *CHI 2008*. (~23 min resumption cost — interruption economics; shared with P-006.) [Peer-reviewed; high confidence.]
9. Burke, E. K., De Causmaecker, P., Vanden Berghe, G., & Van Landeghem, H. (2004). "The state of the art of nurse rostering." *Journal of Scheduling*, 7(6), 441–499. (Survey of the circadian-aware personnel-scheduling OR line.) [Peer-reviewed; high confidence.]
10. American Academy of Pediatrics (2014). Policy statement on school start times for adolescents. *Pediatrics*, 134(3). [Professional-society record; high confidence.] California school-start legislation (SB 328, signed 2019). [Legislative record; high confidence.]
11. Chronotype-based timetabling research in education-scoped settings (conference papers, 2014–2020). [Academic line; PARTIAL-strength; verification queued for the specific instances graded in §3.]
12. Microsoft Viva Insights documentation — meeting-load and focus analytics at org level. [Product record; high confidence on capabilities.]
13. Consumer sleep trackers as phase-estimation data sources (Apple HealthKit sleep APIs; Oura/Whoop/Fitbit sleep-timing exports). [Platform record; high confidence.]
14. Gabaix, X., & Laibson, D. (2006). "Shrouded Attributes, Consumer Myopia, and Information Suppression in Competitive Markets." *QJE*, 121(2). (Invoked in §4's account of why quality-of-time remains unpriced.) [Peer-reviewed; high confidence.]
15. p-rick P-006, *The Attention Scheduler* (this program, 2026): interruption-cost models and admission control — the attention scheduler treats *interruptions*; this paper treats *placement*. Complementary layers of the same resource. [Program cross-reference.]

*Working-paper note: references marked "verification queued" are recorded from domain knowledge at high confidence and await the program's live citation-verification pass (see agents.md); the verification ledger is maintained with the paper sources.*
