# Model Extinction: Behavioral Conservation for the Age of Disposable AI

**p-rick working paper P-011 · series III (continuity) · draft 1.0**

## Abstract

Humanity preserves its important artifacts with institutions we take for granted: the Internet Archive keeps web pages, Software Heritage keeps source code under a UNESCO partnership, the Library of Congress keeps recommended formats, Svalbard keeps seeds. A new class of artifact — the *behavior* of deployed AI models — has no conservation institution at all, and it is dying at a pace no software class has ever experienced. Providers deprecate models on timelines from weeks to a couple of years; fine-tuned derivatives are retired with them; the same model name silently changes behavior across releases; and when a model is gone, the thing that is gone is not code (which could be archived) but a *behavioral identity* — a distribution over outputs that products, workflows, legal decisions, and published research depended on. The consequences are already visible: products that break invisibly when behavior drifts; research that becomes unreproducible months after publication because the evaluated system no longer exists; an entire evaluation science (leaderboards, arena rankings) with no archival ground truth. Adjacent fields hold every component — model cards (describe, don't preserve), open-weight hosting (weights, not deployed behavior), eval methodology with proper statistics, system fingerprints acknowledging drift, routing layers that work around churn — and none composes them into conservation. We specify **behavioral conservation**: a *behavioral fingerprint* protocol (stratified, refresh-resistant eval suites producing score vectors with confidence regions, including consumer-supplied regression tests from downstream products); *equivalence testing* (statistical two-sided hypothesis tests deciding whether a replacement is behaviorally interchangeable with its predecessor, at stated confidence — the science that lets a deprecation be *audited*); *deprecation contracts* (notice periods, equivalence assessments, escape tiers for legal and research access); a public **extinction registry** (an IUCN-style red list of retired behavioral artifacts, with fingerprint evidence); and *inference-time provenance* (provider-signed behavioral identity on every response, generalizing the system-fingerprint idea from an undocumented API field into an inspectable standard). The gap is STRONG and unusually clean: no incumbent of any size exists, every component is individually proven, and demand is expressed constantly (by API consumers, benchmark maintainers, and procurement teams) while supply is zero. This is infrastructure research, not product research: the paper specifies the instruments; the institutions are the builders' problem, and we say so honestly.

## 1. Introduction

There is a vault in Svalbard that keeps seeds against the failure of agriculture. There is an archive in San Francisco that keeps the web against the failure of memory. There is an initiative with a UNESCO partnership that keeps source code against the failure of repositories. Every one of these institutions exists because someone noticed, in time, that a class of artifact was dying faster than anyone was saving it.

The class dying fastest right now is the behavior of AI models. The lifecycle of a deployed model has compressed to a software-biological extreme: announced, adopted, deprecated, gone — often within a year. OpenAI has deprecated entire model families (the GPT-3.5 and legacy GPT-4 lineages, and with them customer-trained fine-tunes); Anthropic and Google rotate model lines on similar cadences; the industry norm has become dated snapshots with sunset windows, after an episode in 2024 in which a provider announced deprecation timelines short enough that developers' production systems faced forced migration within months and pushed back publicly. Deprecation itself is not the sin — software retires software, always. The sin is that *nothing is kept*. When a model is retired, what vanishes is not a file. It is a behavioral identity: a distribution over responses that downstream products were tuned against, that research papers evaluated against, that court records and medical-triage pilots and hiring systems *acted* against. There is no archive, no registry, no fingerprint, no institution whose job it is to notice that a mind ceased to exist and record what it was.

The pattern is not hypothetical; it is the current operating mode:

- **Same-name drift.** In 2023, a wave of developer reports — followed by a Stanford/Berkeley-lineage study titled "Is GPT-4 Getting Worse? A Study on Drift" — documented measurable behavioral change in a model whose name had not changed. Providers eventually began exposing `system_fingerprint` fields on API responses, a de facto acknowledgment that the same model identifier denotes a moving behavioral target. (P-004 of this program treats drift-under-pressure as a degradation-contract problem; this paper treats *identity-over-versions* — the same distinction as behavior under load vs. behavior across releases, and the papers cross-reference rather than overlap.)
- **Fine-tune orphaning.** When base models retire, customer fine-tunes built on them are retired too. Organizations that invested in domain tuning discovered their model is a lease, not a possession, and the asset evaporates with the landlord's portfolio decision.
- **Unreproducible science.** A benchmark paper evaluates `model@version`; the version sunsets; the result becomes permanently unreproducible — the entire field's replication crisis compressed from decades to months. The AI Act's logging requirements for high-risk systems point at operational records, not behavioral archival, and the research community's reproducibility checklists presume the artifact still exists.
- **Silent product breakage.** Prompt pipelines, structured-output contracts, safety filters, and cost models are all fitted to a specific behavioral distribution. When the distribution moves, products degrade in ways their dashboards do not show (the errors are *correct-looking*), and the debugging folklore — "prompt rot," "my prompts stopped working" — is the sound of an entire profession discovering that their substrate is mortal and untracked.

The conservation sciences solved this shape of problem before, repeatedly, for other artifact classes. The life sciences solved it for *knowledge of behavior*: ethology's behavioral ethograms, conservation biology's population monitoring, the IUCN Red List's extinction risk categories and documentation standards. The archives solved it for media: the Library of Congress's Recommended Formats Statement is precisely a periodic, institution-published assessment of which formats are viable to preserve, maintained since 2011. Software Heritage solved it for code. What this paper does is move the pattern to the new artifact class, and specify the instruments the pattern needs when the artifact is a *behavior* rather than a *thing*.

The thesis in one sentence: **deployed AI behavior is the first major artifact class with a lifecycle measured in months, a dependents' list measured in millions, and no conservation instruments at all — and the instruments can be fully specified with today's evaluation science.**

## 2. What exactly is dying (and what is not)

The artifact needs definition, because the obvious candidates are wrong.

**Weights are not the artifact.** Open-weight models (Llama lineage, Mistral lineage) can be archived directly — HuggingFace already does it. But the vast majority of deployed commercial behavior exists only behind APIs, where weights are trade secrets and never published. If conservation requires weights, it conserves only the minority. Weights are also *insufficient*: serving stack, sampling defaults, quantization, guardrail layers, and system-prompt plumbing all shape deployed behavior — two servers of the same weights can behave differently. The artifact must be defined behaviorally, or it is not defined at all.

**The artifact is the input-output distribution.** We define a **behavioral identity** B(A, v) of a deployed artifact A at deployment configuration v: the distribution over responses induced across a specified input space — including the *variation* (temperature, sampling), not just a greedy map. The unit of conservation is B, measured through queries — which is exactly how the outside world (products, benchmarks, legal records) ever knew the model anyway. This reframing is the paper's foundational move: **conserve the observable, not the substrate.** The film archive's analogy is preserving the film *as screened* when the negative is legally unavailable — imperfect as ontology, correct as conservation.

Three corollaries follow. First, behavioral identity is *measurable* by anyone with API access, which makes conservation feasible even for closed models — the archivist never needs the weights, only the queries and budget. Second, behavioral identity is *versioned*: the same artifact name at different times denotes different B's, and the registry's job is to record the sequence with dates. Third, behavioral identity is *partial*: a finite eval suite estimates it with error; all downstream instruments (equivalence, drift, extinction evidence) therefore must carry confidence semantics — this is a feature to design around, not a defect to wish away.

## 3. The landscape: every component exists, the composition is empty

**Model documentation.** Model cards (Mitchell et al., 2019) are now industry-standard: training data, intended use, evaluation results. They *describe* — a snapshot of intentions and benchmarks at publication. They are not maintained across the artifact's lifetime, record nothing at deprecation, and are not maintained by any institution independent of the provider. A birth certificate is not a census, and it is certainly not an obituary.

**Open-weight hosting.** HuggingFace and peers preserve weights and cards for released models — genuinely important for open-lineage models, and the closest thing to an existing conservation institution. Coverage is partial (commercial API behavior lives outside it), and hosting does not fingerprint, test equivalence, or record extinction events.

**Evaluation methodology.** The methodology needed for rigorous measurement exists and is maturing fast: paired evaluation designs, bootstrap confidence intervals, and statistical significance practice for benchmark deltas (the "Adding Error Bars to Evals" engineering writeup from Anthropic, 2023, is representative of the methodological normalization). LMSYS Chatbot Arena supplies preference-scale measurement at population scale. None of this is organized as *conservation*: no fixed reference suites, no archival snapshots, no equivalence standard, no registry.

**Emerging fingerprinting research.** A research line on LLM fingerprinting and behavioral watermarking (2023–2024) asks model-identity questions at protocol scale; the work is adjacent and encouraging, but aimed at identification/authentication research problems, not lifecycle conservation.

**Operational workarounds.** The market is already behaving as if the gap exists: OpenRouter's model-alias routing with fallback layers is conservation's *folk practice* — an infrastructure symptom of the underlying absence; enterprise procurement increasingly writes model-version clauses into AI contracts (the demand side, already institutional); providers introduced dated snapshots and system fingerprints (the supply side, acknowledging the identity problem operationally). When folk practice, procurement demand, and provider concessions all exist and no standard connects them, that is the definition of missing infrastructure.

**Conservation precedents.** IUCN Red List (extinction-risk categories, documentation standards, independent assessor network); Library of Congress Recommended Formats Statement (periodic format-viability assessment); Software Heritage (universal source archive, UNESCO partnership); the Internet Archive. These are the institutional patterns the paper borrows, not cites as coverage.

VERDICT: **STRONG.** No incumbent conserves behavioral identity. Every measurement component is proven. Demand is expressed on all three sides (consumers, researchers, procurement). The gap is an institutional and standards vacuum, which is exactly the shape a research program can specify and a product cannot fill alone.

## 4. Why the gap persists

**Providers' incentive runs the other way.** Deprecation is the business model's hygiene: it retires maintenance burden, concentrates traffic on new capacity, and forces migration to metered successors. Every conservation instrument (notice periods, equivalence reports, archival access tiers) is a *cost on the party that owns the artifact*. Institutions fill incentive gaps; products don't.

**The artifact is legally invisible.** Weights are trade secrets; behavior is contractually ephemeral; no deposit, escrow, or archival obligation exists anywhere in AI law. The AI Act's high-risk logging duties are operational, not archival; records retention regimes were written for documents, not distributions. Conservation has always required the law to notice a class of artifact (deposit requirements for print, broadcast archives, legal-deposit libraries) — AI behavior has not been noticed yet.

**The measurement is genuinely hard, which read as "impossible."** Behavior spaces are infinite; evals are gameable and saturate; prompt-format sensitivity confounds. The field's response to measurement difficulty was benchmark churn (new suite each season) rather than archival discipline (fixed reference suites with refresh protocols — the standard tension in longitudinal measurement, solved by other fields decades ago: rotating-item banks, anchor designs, linking equating). §5 imports those designs.

**The dependents don't know they are dependents.** Products experience drift as "prompt rot" and rewrite around it; researchers experience extinction as "unreproducible" and move on; each absorbs the cost privately. No constituency formed because no one framed the losses as one class of event. This paper's contribution includes the framing.

## 5. The instruments

### 5.1 The behavioral fingerprint

A fingerprint F(A, v, t) is a *statistical estimate of behavioral identity* at time t, with the following protocol:

- **Stratified suite.** A maintained bank of probes stratified over the behavioral space (reasoning families, instruction-following, refusal behavior, calibration probes, format stability, adversarial-robustness sentinels, style/distribution probes for sampling variance). Stratification, not coverage: the goal is a representative *sample* of behavior, like a conservation census — never exhaustive.
- **Anchor + rotating design.** A fixed anchor stratum (never refreshed — the archival ground truth) plus rotating strata refreshed on a schedule, linked by equating items common to old and new banks (psychometrics' anchor linking). This is the refresh-resistance design: the fingerprint can evolve its bank without breaking longitudinal comparability — the exact property benchmark churn destroys and archival science requires.
- **Consumer-contributed regression strata.** Downstream products contribute their own behavioral contracts (the prompts whose distributions their product depends on) as private strata, run on their behalf with results visible only to them (confidentiality preserved) but *counted* in the aggregate signature. This is the design move that makes the fingerprint economically real: every product's regression suite becomes a conservation instrument.
- **Statistical form.** F is a score vector with per-stratum confidence intervals (paired bootstrap; the error-bars methodology the field has normalized). Two fingerprints are never compared pointwise; all comparisons are the tests of §5.2.

Cost is bounded and honest: a fingerprint is an eval run — hours of GPU, schedulable at low cadence (quarterly, and at every version event). Conservation, for behavior, has a metered price; the protocol prices it and budgets it rather than pretending it is free.

### 5.2 Equivalence testing

The deprecation audit's core question: *is the successor behaviorally interchangeable with the predecessor, for my purposes?* The protocol uses equivalence testing (two one-sided tests against a tolerance ε — TOST, the standard statistical machinery for demonstrating *sameness* rather than hoping a non-significant difference implies it):

- H₀: |ΔF| ≥ ε on the contracted strata; equivalence is demonstrated by rejecting both sides at stated confidence.
- Tolerance ε is *per-consumer configurable per stratum*: a medical-triage pipeline's refusal-stratum ε is tighter than a chat product's style-stratum ε. The public registry record uses the default ε; consumer audits use their own.
- Non-equivalence is *recorded, not adjudicated*: the registry's equivalence assessment for a model transition is evidence with confidence bounds, not a verdict with authority. (Adversarial note: stratum selection by the provider is an attack surface — the registry's default strata are therefore fixed by the standard, not the provider's choice.)

### 5.3 The extinction registry

An IUCN-style public registry of behavioral artifacts, maintained independently of any provider:

- **Status ladder:** ACTIVE (in service) → DEPRECATED-ANNOUNCED (sunset date recorded, final fingerprints scheduled) → EXTINCT-IN-WILD (unreachable through any API) → ARCHIVAL-ACCESS (an escrowed serving tier exists, §5.5).
- **Each entry:** fingerprint history with confidence intervals; deployment-config identifiers; equivalence assessments against predecessors/successors; deprecation timeline; and — for extinctions — whatever terminal evidence was captured before cutoff.
- **The red-list function:** periodic state-of-extinction report — which behavioral identities vanished this period, with dependents' exposure estimates (computed from public API-usage proxies and consumer-contributed counts, k-anonymized). The report is the instrument that turns private "prompt rot" losses into a public, countable phenomenon, the same way the IUCN's counts turn individual species losses into a biodiversity signal.

### 5.4 Inference-time provenance

Every API response carries a provider-signed **behavioral identity token**: model family, dated snapshot identifier, serving-config fingerprint class (the generalized, standardized `system_fingerprint` — turned from an undocumented field into an inspectable standard). Consequences: products can *audit* what they actually depended on (today they cannot); court records and research papers can cite the exact behavioral artifact (today they cite a name that outlives its own referent); drift becomes *attributable* (the delta between the token's identity and the product's fitted identity is machine-checkable). Signed tokens also give deprecation notices enforcement teeth: a sunset date is a *promise about future token classes*, and violations are observable by any third party.

### 5.5 Archival access tiers

Conservation's hard constraint: closed weights cannot be escrowed by third parties. The instruments above conserve the *observable*; the last instrument conserves *access*: a contractual archival-serving tier for extinct models — rate-limited, research-and-legal access, priced at cost — so that a behavioral identity, once extinct in the wild, remains reachable for replication, litigation, and audit. Precedents: legal deposit libraries (access-constrained preservation of copyrighted works); controlled-access archives in biobanking; the preservation access rules film archives negotiated with studios. Providers will resist; §8's objections confront it directly, and the design's fallback is honest: if archival serving never happens, the fingerprints, equivalence records, and registry still conserve the *knowledge* of what the artifact was — the ethogram without the living animal.

### 5.6 Deprecation contracts

The procurement-facing instrument, now writable with the above: minimum notice periods (notice measured from *public announcement* to last-availability); a published equivalence assessment of successor vs. deprecated artifact on the standard strata, at the standard ε; a final fingerprint event before cutoff; archival-access terms; and breach observability via the provenance tokens. Every clause is verifiable with the instruments of §5.1–5.4 — this is what makes it a *contract* rather than a hope. Enterprise buyers already write model-stability clauses; the contracts' current unenforceability (no equivalence standard exists to reference) is precisely the vacuum this specification fills.

## 6. Evaluation design

The specification is testable, and the evaluation is cheap relative to its claims:

1. **Fingerprint stability.** Run the anchor design against two versions of a stable model (no announced change): measurement variance must be within the protocol's predicted confidence bands — the instrument's noise floor, calibrated empirically.
2. **Drift detection replay.** Replay known drift episodes (the documented 2023–2024 same-name drift controversies, on models where historical outputs can be re-collected): the fingerprint's per-stratum deltas should have flagged the events at the strata where users reported them — the instrument's *sensitivity*, measured against ground truth the field already discussed publicly.
3. **Equivalence calibration.** Known successor pairs (models providers themselves presented as replacements) get the equivalence battery; the tests should discriminate — flag as non-equivalent the pairs where migration pain was publicly documented, pass the pairs where it was not. The discriminating power of ε, stratum choice, and confidence levels is the deliverable.
4. **Refresh resistance.** Rotate the non-anchor bank on schedule; verify anchor-linking keeps longitudinal comparability within bands (the psychometric equating property, empirically demonstrated).
5. **Cost budget.** Instrument the full quarterly fingerprint + version-event fingerprints for a mid-tier API model over a year; report the metered cost of conservation per artifact — the number that converts this from principle to line item.

## 7. What this is not

Three scope boundaries, stated to keep the specification honest. This is not an *open-weights advocacy* paper: open weights are one conservation path (and a good one), but the specification covers the closed-behavior majority that open-weight advocacy cannot reach. This is not a *leaderboard*: ranking models by capability is a live question; recording what existed, when, and what replaced it equivalently is a historical one. This is not *regulation*: the paper specifies instruments and standards; the coercive step (mandatory notices, deposit duties) is for legislatures, and the instruments are what any such legislation would reference if it ever comes. Research-first, in the program's sense: the papers specify what should exist; the institutions and builders come after.

## 8. Objections, confronted

**"Weights can't be escrowed, so nothing can."** The reframe of §2 dissolves this: behavioral identity is measurable without weights, by design, by anyone with access. The archive holds fingerprints, equivalence records, and access terms — not parameters. Film archives preserved the screened experience when negatives were unobtainable; the analogy is imperfect (films don't drift), and §5's confidence semantics exist precisely because the analogy's imperfection is the *scientific* content of this paper.

**"Evals are gameable; fingerprints will be gamed."** Gameability attacks the *ranking* use of evals, where stakes concentrate on a number. Conservation uses are different: anchor strata are never published as a ranking (no incentive to overfit a score that crowns nothing), consumer strata are private, and the registry records *evidence with error bars*, not medals. Adversarial provider behavior (serving a fingerprint-special mode) is bounded by anchor strata's fixed design and by §5.4's tokens binding identity at serving time; the honest bound remains: a determined provider can fool part of the instrument part of the time, which is why strata are standardized by the registry, not chosen by the provider.

**"Deprecation is legitimate infra hygiene."** It is — the paper never argues models must live forever. It argues that *deaths should be recorded, replacements audited, and dependents given the instruments to price their exposure*. The entire apparatus is compatible with rapid lifecycle churn; it is the *invisibility* of the churn that the apparatus removes.

**"Who maintains the registry?"** An institution, independent of providers, funded by the parties that bear the cost of extinction (research consortia, procurement federations, archives with mandates). The precedents (IUCN, LoC, Software Heritage) all solved the same institutional bootstrapping for prior artifact classes. This paper's job is the specification those institutions will reference; §7 says so explicitly.

**"Behavior is too stochastic to pin down."** Stochasticity is why the fingerprint measures *distributions with confidence regions* rather than outputs. The objection proves the design's necessity: it is exactly the instrument's statistical form. Fields with noisier artifacts (ecology's population estimates, epidemiology's surveillance) built longitudinal measurement on the same statistical machinery a century ago.

**"This will slow AI progress."** Transparency of lifecycle events does not slow anything except the specific practice of silent substitution. The 2024 pushback against compressed deprecation windows — from the developer community, in public — is the demand signal this specification answers. Progress that depends on dependents not noticing what changed is not the progress anyone should be defending.

## 9. Limitations

The behavioral-identity abstraction conserves observables, not mechanisms: post-hoc analysis of *why* a model behaved as it did (weights-level forensics) remains impossible for closed artifacts without archival serving (§5.5), which depends on provider cooperation the instruments cannot compel. Fingerprint cost bounds conservation coverage to artifacts someone will pay to conserve — the long tail of behavioral identities will go unrecorded, exactly as the long tail of most classes goes unrecorded in every archive. Confidence semantics make all claims interval-valued; a regulator wanting binary "equivalent/not-equivalent" verdicts will be disappointed by design. The registry's independence is a governance problem the specification assumes and cannot itself construct. And the whole apparatus presumes continued query access to live artifacts — for already-extinct models, conservation is retroactive and partial wherever the field's historical outputs were not systematically captured. These are the honest edges of the specification; they bound its coverage, not its correctness.

## 10. Conclusion

Every era's most valuable artifact class gets a conservation institution roughly one crisis late: print got legal deposit after the burnings, film got archives after the nitrate fires, code got Software Heritage after the repository disappearances. The current fastest-dying artifact class is deployed AI behavior, and the crisis is already here — unreproducible science, silently breaking products, unrecorded extinctions of systems that millions of decisions ran through — it is simply distributed as millions of private annoyances instead of one photogenic fire. This paper specifies the instruments that gather them into a single, countable, scientific phenomenon: the fingerprint that measures a mind, the equivalence test that audits a replacement, the registry that records an extinction, the token that proves what you depended on, and the contract that makes all of it enforceable. The seeds are in the vault. The code is in the archive. The behavior is in neither, and it is dying on schedule.

## 11. References

1. OpenAI deprecation notices and policy pages; dated-snapshot versioning practice (2023–2024); the `system_fingerprint` response field. [Provider records; high confidence; verification queued for specifics.]
2. "Is GPT-4 Getting Worse? A Study on Drift" (2023). Stanford/UC Berkeley-affiliated working paper, widely reported (e.g., Fortune, Vox coverage of model drift). [Working paper + press record; author list omitted pending verification pass.]
3. Anthropic engineering post, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations" (2023). [Engineering-methodology record; high confidence on content.]
4. LMSYS Chatbot Arena — preference-scale evaluation at population scale. [Platform record; high confidence.]
5. Mitchell, M., et al. (2019). "Model Cards for Model Reporting." *ACM Conference on Fairness, Accountability, and Transparency (FAT*)*. [Peer-reviewed; high confidence.]
6. Hugging Face — open-weight model hosting, model cards. [Platform record; high confidence.]
7. LLM fingerprinting and behavioral-identification research line (2023–2024). [Research line; PARTIAL confidence on specific papers; verification queued.]
8. OpenRouter — model routing, aliasing, and fallback behavior for API models. [Platform record; high confidence.]
9. IUCN Red List of Threatened Species — categories, criteria, and assessor network. [Institutional record; high confidence.]
10. Library of Congress, *Recommended Formats Statement* (issued 2011, updated periodically). [Institutional record; high confidence.]
11. Software Heritage — universal source-code archive, UNESCO partnership (Inria-initiated). [Institutional record; high confidence.]
12. Internet Archive / Wayback Machine. [Institutional record; high confidence.]
13. EU Artificial Intelligence Act — logging and record-keeping obligations for high-risk systems. [Legislative record; high confidence on the obligation class.]
14. Conservation-biology monitoring methodology: anchor designs, rotating-item banks, and equating/longitudinal-linking methods from psychometrics (survey-sampling and test-equating literature). [Methodological line; high confidence on the methods' existence.]
15. TOST / equivalence testing methodology: Schuirmann, D. J. (1987). "A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability." *Journal of Pharmacokinetics and Biopharmaceutics*, 15, 657–680. [Peer-reviewed; high confidence — the standard equivalence-test citation.]
16. Fine-tune deprecation episodes: OpenAI retirement of legacy fine-tuned models (2023 announcements). [Provider record; verification queued.]
17. p-rick P-004, *Degradation Contracts* (this program, 2026): runtime behavior under pressure — the within-version axis; this paper governs the across-version axis. [Program cross-reference.]
18. p-rick P-008 / P-010 (this program, 2026): the continuity-series protocol family — dead-hand triggers, escrow, and public ledgers pointed at devices, packages, and here, minds. [Program cross-references.]

*Working-paper note: references marked "verification queued" are recorded from domain knowledge at high confidence and await the program's live citation-verification pass (see agents.md); the verification ledger is maintained with the paper sources.*
