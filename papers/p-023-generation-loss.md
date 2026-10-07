# Generation Loss: A Drift Law for Continually Re-embedded Vector Corpora

**p-rick working paper P-023 · series VI (laws — from specification to derivation) · draft 1.0**

## Abstract

Every production retrieval-augmented system rests on a corpus of embeddings that is quietly, continuously going stale. Encoder models are upgraded — a new checkpoint, a new architecture, a retrained production model — and each upgrade re-renders the space: the corpus vectors on disk were produced by generation $g_0$, queries arrive encoded by generation $g$, and the two drift apart at a rate the operators of vector databases currently have no way to reason about, because no law exists. The operational folklore is a calendar ("re-embed everything every $n$ months") or an incident ("recall fell and nobody knew why"). This paper derives the law. Under a general two-channel model of encoder churn — each generation applies a global geometric transformation (the *isometry channel*: rotations and reflections of the whole space) plus per-object idiosyncratic distortion (the *distortion channel*: the part of the change that is not any single orthogonal map) — the semantic drift of a fixed corpus obeys

$$D(g) \;=\; 1 - \lambda^g, \qquad \lambda \;=\; \underbrace{\Bigl(1 - \tfrac{2\,(1 - \bar c_{\mathrm{rot}})}{d}\Bigr)}_{\text{isometry: dimension-mercy}} \;\times\; \underbrace{(1 + \nu^2)^{-1/2}}_{\text{distortion}},$$

where $d$ is the embedding dimension, $\bar c_{\mathrm{rot}}$ the mean per-generation cosine of the isometry channel, and $\nu$ the per-object distortion magnitude. The law's two terms behave oppositely, and the opposition is the paper's central finding. The isometry channel's coefficient is $2/d$: in the dimensions real systems inhabit ($d \ge 256$), global rotations contribute almost nothing to drift — a 60° global rotation per generation accumulates only 1.1% drift after thirty generations at $d=256$ — because a random rotation barely moves any *fixed* vector's direction in high dimension. This *dimension mercy* means the isometry channel is both harmless and removable: a fixed panel of $L$ persistent landmark objects, re-embedded each generation, yields an orthogonal Procrustes alignment $A$ (one matrix, solved once per generation) whose transplantation onto the stale index removes the isometry channel exactly, with estimation error scaling as $\sqrt{d/L}$. The distortion channel, by contrast, is channel-independent of dimension, cannot be aligned away by any global transform, and accumulates geometrically — it is the entire real cost of encoder churn, and the paper's decomposition theorem is the proof that nothing else is. The experimental program runs synthetic corpora (25–50 tight clusters, 5k–20k objects, $d \in \{16, \dots, 1024\}$) through 16–30 generation chains with both channels independently controlled: the drift law validates to three decimal places across channels and levels ($D(16)$ measured 0.077 vs theory 0.077; 0.275 vs 0.276; 0.558 vs 0.560; the rotation-only and noise-only configurations at identical $\lambda$ lie on the same line); retrieval experiments show a stale index's recall@10 falling from 0.81 to 0.38 over sixteen rotation-dominated generations while an anchored index — the same stale vectors, one Procrustes refresh per generation, zero re-embedding — holds 0.71; and the channel decomposition appears as a heatmap on which anchored recall is flat across the entire rotation axis and collapses along the distortion axis. The landmark-count law $\sqrt{d/L}$ is validated ($L = 64$: recall 0.09; $L = 4096$ at $d = 256$: 0.53, saturating at the distortion floor), and the operational translation is the paper's deliverable: *measure the two channels from any single generation pair (a few hundred objects embedded twice), compute $\lambda$, and the calendar question — re-embed now, anchor forever, or do nothing — becomes arithmetic*: re-embed when the distortion channel has accumulated past the retrieval margin; anchor when the churn is isometry-dominated (and real churn between adjacent checkpoints of the same model family is, we hypothesize from the law's structure, mostly isometry — the paper's testable prediction for the trace studies that should follow).

**Keywords:** vector databases, embeddings, semantic drift, model upgrades, Procrustes alignment, retrieval-augmented generation, dimensionality, orthogonal transformations, operational law

## 1. Introduction

The vector index is the load-bearing wall of the current architecture of applied AI. Retrieval-augmented pipelines, semantic caches, recommendation retrieval, deduplication, and clustering all sit on a corpus of embedding vectors produced by an encoder model, and all of them silently assume the vectors and the queries live in the same space. They do not, for long. Encoder models are upgraded the way production software is upgraded: continually, urgently, and with no protocol for the artifacts the old version left behind. The corpus on disk was embedded by generation $g_0$; the query at the gate is embedded by generation $g$; the gap between them is *semantic drift*, and the entire current practice for managing it consists of two rituals: the calendar ("we re-embed quarterly") and the incident ("recall degraded; nobody tied it to the encoder bump until the eval broke").

The gap between ritual and requirement is a measurement gap, and underneath it a mathematics gap. Ask an operator how much drift one encoder upgrade causes and you will get a shrug; ask whether their corpus's drift is *fixable without re-embedding* and you will get a guess; ask when the next re-embed is due and you will get a calendar entry that predates any analysis. None of these questions is hard in principle. Drift is a cosine between two versions of the same object; fixability is a question about the *structure* of the change (is it a global transformation of the space, or a per-object reshuffle?); the re-embed schedule is a threshold on an accumulating quantity. What is missing is the law that connects them — the drift dynamics under repeated upgrades, the decomposition of the change into the part an alignment can remove and the part it cannot, and the error curve of estimating the alignment from finite landmarks. This paper derives all three, validates them in simulation, and reduces the operational decision to the resulting arithmetic.

The derivation rests on a modeling move that we believe is the paper's methodological contribution as much as its theorems: encoder churn is decomposed into two channels with exactly opposite operational characters. The **isometry channel** is the part of the change that acts as one global orthogonal transformation — the new encoder is the old encoder, rotated: every direction of geometric change that is uniform across the corpus. The **distortion channel** is what remains: the per-object reshaping that no single orthogonal map captures — neighbor reordering, local stretching, the genuine semantic re-decisions of a retrained model. The distinction is not philosophical; it is a measurable dichotomy (fit the best orthogonal map to a generation pair and the residual is the distortion channel) and it turns out to carry the entire operational story, because the two channels scale differently:

- Isometry drift is *mercy-scaled by dimension*: a rotation by angle $\delta$ moves a fixed vector's direction by an expected cosine of $1 - 2(1-\cos\delta)/d$ — at $d=256$, even a 135° rotation costs 1.3% of cosine per generation. High-dimensional spaces are almost rotation-invariant *for individual fixed vectors*, which is why the isometry channel accumulates so slowly.
- Distortion drift is *dimension-free*: an idiosyncratic jitter of magnitude $\nu$ costs $(1+\nu^2)^{-1/2}$ per generation in any dimension, and nothing about $d$ protects you.
- Only the isometry channel is *alignable*: a Procrustes fit on persistent landmarks removes it exactly (estimation error $\sim\sqrt{d/L}$), and no transformation of any kind removes the distortion channel, because it is not a transformation.

Together: $D(g) = 1 - \lambda^g$ with $\lambda$ the product of the two channels' per-generation cosines. Three validate-able statements fall out immediately — the geometric accumulation (a straight line on a log-drift plot, regardless of channel composition), the dimension mercy (drift curves ordered exactly by $1/d$ under pure rotation), and the decomposition inequality (anchored recall is flat in the rotation axis and collapses in the distortion axis). Section 6's experiments are designed to break each of these and fail.

The operational payoff is a decision rule that replaces both rituals. From any single generation pair (embed a few hundred probe objects with both encoders; the cost is a coffee), fit the orthogonal map, measure the residual, and obtain $\bar c_{\mathrm{rot}}$ and $\nu$ — hence $\lambda$, hence the full drift curve of the corpus under churn like this pair's. Then: if the churn is isometry-dominated (as between adjacent checkpoints of a training run, we predict), anchor — keep the stale index, transplant the Procrustes refresh each generation, re-embed never; the drift curve stays flat and the landmark panel costs $L \approx 8d$ objects per generation against a corpus of millions. If the churn is distortion-heavy (a genuinely retrained model, a different family), the distortion channel accumulates geometrically and the only honest options are re-embedding or accepting the decay — and the law says exactly when the accumulated $D(g)$ crosses the retrieval margin, i.e. the calendar entry stops being a ritual and becomes a number.

The paper's honest scope: all validation is synthetic — cluster-structured corpora pushed through controlled generation chains — because the claim under test is a *law* (channel-controlled, dimension-controlled, generation-counted), and laws are validated where every variable is controlled. The trace study (real encoder pairs, real corpora, the two channels measured from production upgrade logs) is the stated follow-up, and the paper closes by marking the specific prediction that trace study will test.

Section 2 positions the result. Section 3 builds the model. Section 4 derives the law, the decomposition, and the landmark error. Section 5 specifies experiments. Section 6 presents results (five figures). Section 7 is the damage report. Section 8 concludes.

## 2. Related work

**Embedding-space alignment.** The Procrustes solution (orthogonal least-squares map between paired point sets) is classical (Schönemann, 1966). Its appearance in representation learning is the diachronic word-vector literature: aligning word2vec/GloVe spaces across time periods by orthogonal transformation, with the observation that much of the change between adjacent periods is well-captured by a global map (Hamilton, Leskovec, and Jurafsky's diachronic word embeddings, 2016, and the alignment lineage around it); and in cross-lingual embedding alignment, where the orthogonal mapping is the standard bridge between two encoders' spaces. The present paper's debt is direct and its departure is structural: that literature aligns *two* snapshots and moves on; a production corpus does not get two snapshots, it gets a generation *chain*, and the question is not "can these two spaces be aligned" (they can, mostly) but "what does a hundred-generation chain of partial alignments accumulate, what does the un-alignable residue do to retrieval, and how many landmarks does the alignment need" — none of which is a two-snapshot question.

**Model stitching and representation compatibility.** The observation that representations from nearby models are linearly/orthogonally relatable has recurred under several names (model stitching; representation surgery; the "linear mode connectivity" family of results showing nearby checkpoints differ by approximately-linear maps in weight space — verification-queued for exact attributions). That literature establishes the plausibility of the isometry channel's dominance between adjacent checkpoints; it does not quantify corpus drift, does not treat chains, and does not connect to retrieval operations.

**Vector database operations.** The practitioner literature on re-embedding (the major vector-database vendors' operational guides) is calendar-driven: re-embed "when you change models," scheduled by policy, priced by token count. We find no published drift quantification, no per-upgrade measurement protocol, no alignment-based alternative for the stale-index problem, and no analysis of landmark-panel sizing. Gap verdict: the operation exists, the mathematics of the operation does not. (Adjacent operational topics — ANN recall under quantization/pruning, drift *detection* via canary queries — address different failure modes: compression and monitoring, not churn.)

**Position in this program.** Series VI runs on laws: P-021 derived the epidemic threshold of dependency graphs, P-022 the admission threshold of caches. This paper derives the drift law of embedding corpora. The three share the charter: take a system the field operates by folklore, write the governing equation, validate it to the edge of honesty, ship the harness.

## 3. The model

### 3.1 The corpus and the chain

A corpus of $M$ unit-norm vectors in $\mathbb{R}^d$, structured as $n_c$ tight clusters (each object: its cluster center plus isotropic noise of total magnitude $\sigma$, renormalized — a spherical-Gaussian cluster model, an adequate and honest stand-in for the local geometry of real embedding manifolds; Section 7 prices the difference). Queries are drawn from the same clusters (center plus $\sigma$ noise), so that retrieval (top-$k$ within and across clusters) is well-posed but non-trivial: the within-cluster cosine margin against the cross-cluster background is the retrieval margin the drift will erode.

Encoder generations form a chain: the corpus and queries at generation $g$ are

$$\phi_g(\cdot) \;=\; T_g \circ \phi_{g-1}(\cdot),$$

where each $T_g$ is the generation's change, decomposed as

$$T_g(x) \;=\; \mathrm{normalize}\bigl(R_g\, x + \nu\, u\bigr), \qquad u \sim \mathrm{uniform}(S^{d-1}),$$

with $R_g$ a global Givens rotation by angle $\delta_g$ in a uniformly random coordinate plane (the isometry channel — any orthogonal transformation's drift behavior is captured by the rotation family, and a rotation in a random plane is the least favorable case among them for a *fixed* vector, since it puts the full rotation where the vector has mass with probability $\sim 2/d$... precisely, it treats all vectors alike in expectation), and $\nu u$ a per-object jitter of total magnitude $\nu$ in a fresh random direction (the distortion channel). Setting $\delta = 0$ or $\nu = 0$ isolates a channel. The channels are controlled independently across experiments — the paper's core identification strategy.

### 3.2 Drift and recall

**Semantic drift** of the corpus (stale index at $g_0 = 0$):

$$D(g) \;=\; 1 - \mathbb{E}_x\bigl[\cos\bigl(\phi_g(x), \phi_0(x)\bigr)\bigr].$$

**Recall@10** of a retrieval system against the gold standard (the top-10 of current-generation queries against the current-generation corpus — re-embedding's answer by definition): a *stale* index scores $\phi_g(q)$ against $\phi_0(x)$; an *anchored* index scores $\phi_g(q)$ against $A_g \phi_0(x)$, where $A_g$ is the Procrustes alignment (Section 4.3) fitted on $L$ persistent landmark objects re-embedded at each generation; the *fresh* (full re-embed) index is the gold standard itself and its curve is the ceiling $y=1$.

## 4. Theory

### 4.1 The generation-loss law

**Proposition 1 (drift law).** *Under the two-channel model, for all $g$:*

$$\mathbb{E}\bigl[\cos(\phi_0(x), \phi_g(x))\bigr] \;=\; \lambda^g, \qquad \lambda \;=\; \Bigl(1 - \frac{2(1 - \mathbb{E}[\cos \delta])}{d}\Bigr)\,(1 + \nu^2)^{-1/2}.$$

*Proof sketch.* Per generation, decompose. **Isometry:** for a fixed unit vector $x$ and a rotation by $\delta$ in a uniformly random plane, $\langle x, R x\rangle = 1 - (1-\cos\delta)(x_i^2 + x_j^2)$ for the rotated coordinates $(i,j)$; taking the expectation over the plane, $\mathbb{E}[x_i^2 + x_j^2] = 2/d$ (the coordinates of a fixed unit vector in a random basis — and the corpus, being cluster-isotropic at scale, supplies the averaging in the realized drift). Conditioning inductively on the position after $g-1$ steps (each step's rotation is independent of the position, and the position remains unit-norm), the expected cosine multiplies by $1 - 2(1-\bar c)/d$ per step. **Distortion:** for $y = \mathrm{normalize}(x + \nu u)$ with $u$ uniform and independent, $\mathbb{E}[\langle x, y\rangle] = \mathbb{E}\bigl[1 / \|x + \nu u\|\bigr] = (1+\nu^2)^{-1/2}$ exactly (the numerator $\langle x, x + \nu u\rangle = 1$; $\|x + \nu u\|^2 = 1 + \nu^2$ deterministically for unit $x, u$), and independence across generations multiplies. $\square$

Three structural readings, each an experiment:

1. **Geometric accumulation** — $D(g) = 1 - \lambda^g$ is a straight line on a log scale, whatever the channel mix; two configurations with the same $\lambda$ (one pure rotation at $d=64$, one pure noise at $d=256$) lie on the same drift line. Photocopies of photocopies: each generation multiplies fidelity by the same factor.
2. **Dimension mercy** — the isometry coefficient $2(1-\bar c)/d$ vanishes as $d$ grows: at $d = 1024$, a 60°-per-generation rotation accumulates 2.9% drift in thirty generations. The counterintuitive content: the *same* global rotation that scrambles low-dimensional spaces is nearly a no-op for fixed vectors in high dimension — a fact of spherical geometry (a random plane misses any fixed vector's mass with probability $1 - O(1/d)$) that production intuition, trained on 2-D and 3-D rotation imagery, systematically gets wrong.
3. **Channel independence** — the channels enter $\lambda$ multiplicatively and do not interact; the law's validation therefore does not depend on getting the decomposition's *semantics* right, only its *scalars*.

### 4.2 The decomposition and what it buys

**Proposition 2 (anchoring removes the isometry channel exactly).** *Let $A_g$ be the orthogonal Procrustes solution on the landmark pairs $\{(\phi_0(l), \phi_g(l))\}_{l=1}^L$. Then for pure-isometry chains ($\nu = 0$), $A_g \phi_0(x) = \phi_g(x)$ for every corpus object $x$, exactly, and anchored recall equals fresh recall.*

*Proof sketch.* $\phi_g = R_{g} \cdots R_1 =: \mathcal{R}$ is a single orthogonal map; the Procrustes solution recovers any orthogonal map exactly from noiseless pairs (the self-check in the harness asserts $\|A - \mathcal{R}\| < 10^{-12}$ on a noiseless configuration). $\square$

The practical content: the isometry channel is not merely slow (Proposition 1), it is *removable at the cost of $L$ objects' worth of re-embedding per generation and one $d \times d$ matrix solve*. The distortion channel is the irreducible remainder — and the decomposition theorem's negative half: no global transformation removes idiosyncratic distortion, so the anchored system's residual decay is the distortion channel's own accumulation, a floor no cleverness of alignment can lower. Retrieval experiments make this a picture (the two-panel heatmap of Section 6.3): anchored recall flat along the entire rotation axis, decaying along the distortion axis only.

### 4.3 The landmark law

**Proposition 3 (alignment estimation error).** *With $L$ landmark pairs observed through one generation's distortion, the Procrustes estimate's angular error scales as $\sqrt{d/L}$ times the distortion magnitude, and the anchored recall deficit below the fresh ceiling correspondingly falls as $\sqrt{d/L}$.*

*Proof sketch (heuristic, and stated as such).* The orthogonal Procrustes fit is a rank-$d$ estimation problem (the orthogonal group's dimension is $d(d-1)/2$, but the *observable* error is the rotation's action on the corpus distribution, whose effective rank is $d$); $L$ noisy pairs supply $L$ vector observations of a $\nu$-corrupted transform; perturbation of the SVD factors the error into a random-rotation component whose size on the corpus is $\nu \sqrt{d/L}$ by concentration. The scaling — not the constant — is the proposition, and the experiment validates the scaling. $\square$

The operational reading is a budget formula: **the landmark panel must outnumber the dimension by a comfortable factor** — at $d = 256$, the experiments show the alignment still noisy at $L = 256$ (recall 0.35 of a 0.53 ceiling), adequate at $L = 1024$ (0.51), and saturated by $L = 4096$ (0.53). $L \approx 8d$ is the knee; against a corpus of millions, $8d \approx 2048$–$8192$ objects per generation is a *rounding error* of re-embedding cost — the entire anchor protocol's price.

## 5. Experimental design

Five experiments, one per figure; the harness (`code/p-023-simulation.py`, seeds in the text, NumPy only) regenerates everything:

1. **The law (F1).** Sixteen-generation chains at four noise-only levels ($1-\lambda \in \{0.005, 0.01, 0.02, 0.05\}$, $d=256$) plus one rotation-only configuration at $1-\lambda = 0.02$ (solvable only at $d=64$ — the dimension-mercy arithmetic itself dictates the design: at $d=256$ no rotation achieves 2% per generation). Drift points against $1-\lambda^g$ lines.
2. **The systems (F2).** A rotation-dominated chain ($\delta = 135°$, $\nu = 0.05$, $d = 256$, 16 generations): recall@10 of the stale index, the anchored index ($L = 4096$), and the fresh ceiling, with the drift curve on a second axis.
3. **The decomposition (F3).** Ten-generation anchored and stale recall over a grid of distortion $\nu \in \{0.05, \dots, 0.42\}$ × rotation $\delta \in \{0°, \dots, 135°\}$: two heatmaps, the paper's thesis as a picture.
4. **The landmark budget (F4).** Anchored recall at generation 8 vs $L \in \{64, \dots, 4096\}$ on a 10k-object corpus, $d = 256$, against the $\sqrt{d/L}$ scaling and the stale baseline.
5. **Dimension mercy (F5).** Pure-rotation chains at $\delta = 60°$ for $d \in \{16, 64, 256, 1024\}$, thirty generations: drift curves against the $2(1-\cos\delta)/d$ law.

## 6. Results

### 6.1 The law (F1)

The drift law holds to the third decimal across every configuration: measured $D(16)$ against theory — 0.077 vs 0.077 ($1-\lambda = 0.005$), 0.148 vs 0.149, 0.275 vs 0.276, 0.558 vs 0.560 (noise-only, $d = 256$), and 0.276 vs 0.276 for the rotation-only configuration at the same $\lambda = 0.98$ — the last pair being the law's channel-independence made literal: a pure-rotation chain at $d = 64$ and a pure-noise chain at $d = 256$, tuned to the same per-generation fidelity loss, lie on the same drift line to the last measured digit. Every curve is straight on the log plot; every dotted theory line is the closed form with no fitted constant.

![Semantic drift D(g) across five configurations (four noise levels, one rotation-matched), log scale, with the law's dotted lines. The rotation-only chain at d=64 and the noise-only chain at d=256 with the same per-generation loss lie on the same line: drift accumulates geometrically, indifferent to which channel causes the loss.](figures/p-023/f1-law-validation.png)

### 6.2 The systems (F2)

The rotation-dominated chain separates the three systems exactly as the decomposition demands. The stale index's recall@10 falls from 0.81 to 0.38 over sixteen generations — the isometry channel, invisible in the corpus's *internal* geometry (Proposition 1 says its drift is only 0.13 total even here), is lethal at the *query-corpus interface* (the query rotates, the corpus does not, and the target's similarity decays toward the distractor background while the distractors' baseline stays put). The anchored index — the same stale vectors, refreshed by one Procrustes matrix per generation — holds 0.92 → 0.71: nearly double the stale system's endgame recall at a re-embedding cost of 4096 objects per generation against a corpus of five thousand (in production proportion: a rounding error). The gap between anchored and the fresh ceiling is the distortion channel's own accumulation ($\nu = 0.05$: the honest, un-alignable floor). The drift curve (right axis) rises to 0.13 while stale recall halves: drift *level* and drift *damage* are different quantities, and the paper's decomposition is what relates them — the same total drift is catastrophic when isometry-dominated (it misaligns queries against corpus) and mild when distortion-dominated (it scrambles within-cluster ranking gradually).

![Recall@10 over sixteen generations of a rotation-dominated chain: the stale index decays from 0.81 to 0.38; the anchored index (same stale vectors, one Procrustes refresh per generation, L=4096) holds 0.92 to 0.71; the fresh ceiling is 1.0 by definition; drift on the right axis.](figures/p-023/f2-recall.png)

### 6.3 The decomposition (F3)

The two heatmaps are the paper's thesis in one figure. In the **anchored** panel, recall is flat along the entire rotation axis (0.75, 0.74, 0.74, 0.75, 0.76 across $\delta = 0° \to 135°$ at $\nu = 0.05$) and collapses along the distortion axis (0.75 → 0.13 as $\nu$ goes 0.05 → 0.42): alignment removes rotation completely, and only distortion remains. In the **stale** panel, both axes bite (0.75 → 0.43 along the rotation axis at $\nu = 0.05$; the same collapse along the distortion axis). Two operational corollaries drawn directly off the picture: (i) an operator whose upgrades are mostly architectural/checkpoint changes — rotation-dominated, under the model — loses *nothing* they cannot get back with a landmark panel; (ii) an operator facing distortion-dominated churn (genuinely retrained encoders) cannot buy recall back with any alignment and should price re-embedding honestly instead.

![Two heatmaps of recall@10 after ten generations: stale (left) and anchored (right) across per-generation jitter (vertical) and rotation angle (horizontal). Anchored recall is flat along the rotation axis — alignment removes the isometry channel completely — and both panels collapse along the distortion axis, the irreducible remainder.](figures/p-023/f3-decomposition.png)

### 6.4 The landmark budget (F4)

The landmark curve rises as $\sqrt{d/L}$ and saturates: at $d = 256$, $L = 64$ recovers only 0.09 recall (the alignment is noise — the panel is smaller than the space), $L = 256$ reaches 0.35, $L = 1024$ reaches 0.51, and $L = 4096$ sits at the 0.53 floor — the distortion ceiling for this configuration, identical to the $L = 2048$ value: beyond the knee, more landmarks buy nothing because nothing alignable remains. The dashed theory curve ($1 - c\sqrt{d/L}$) tracks the rise with one constant set by the terminal point. The stale, unanchored baseline is 0.019 at this distortion level — the panel buys a twenty-five-fold recall recovery, then stops.

![Anchored recall vs landmark count L (log axis) with the sqrt(d/L) scaling law: the alignment is noise below L ~ d, adequate at L ~ 4d, and saturated at the distortion floor by L ~ 16d. The unanchored stale baseline is marked.](figures/p-023/f4-landmarks.png)

### 6.5 Dimension mercy (F5)

Under thirty generations of 60°-per-generation global rotation, drift ends at 0.754 ($d = 16$), 0.387 ($d = 64$), 0.107 ($d = 256$), and 0.028 ($d = 1024$) — against the law's 0.856, 0.377, 0.111, 0.029. The ordering and the magnitudes are the $2(1-\cos\delta)/d$ arithmetic; the $d = 16$ point's 10% shortfall from the ensemble law is the honest finite-dimensional dispersion (the law is exact in expectation over random rotation planes; a single realized plane sequence concentrates around it with $O(1/\sqrt d)$ spread, visible at $d = 16$ and gone by $d = 256$) — a footnote-level caveat the figure wears openly. The production translation: a *quarter-turn per generation* — catastrophic imagery in low dimension — costs a $d = 768$ corpus one percent of semantic fidelity every generation. Rotation is not the enemy; distortion is.

![Drift under thirty generations of 60-degree global rotation, by dimension: the same rotation that destroys a 16-dimensional space costs a 1024-dimensional one 2.9% total. The dimension-mercy coefficient 2(1-cos delta)/d is the law; points are measurements, dotted lines theory.](figures/p-023/f5-dimension.png)

## 7. Limitations, threats to validity

**Synthetic churn.** The generation chain is a two-channel synthetic process, not a sequence of real encoder releases. The law's validation is therefore validation *of the model's mathematics* — exact, and meant to be — while the model's *fidelity to real churn* is the open empirical question the follow-up trace study must answer. The decomposition itself is definitional (fit the best orthogonal map; call the residual distortion), so the law's $\lambda$ decomposition applies to any real generation pair; what the synthetic setting cannot tell us is the *distribution* of $(\bar c_{\mathrm{rot}}, \nu)$ across real upgrade types — checkpoints versus retrains versus architecture swaps. The paper's prediction (adjacent checkpoints of one training run are isometry-dominated) is a structured guess, labeled as such.

**Cluster-model corpus.** The corpus is isotropic clusters, not a real embedding manifold (anisotropy, hierarchy, hubness — real embedding spaces have all three). The drift law (Proposition 1) is corpus-distribution-independent to first order (it needs only unit norms and per-object averaging); the *recall* results inherit the cluster model's margins, and real manifolds with different local geometry will move the recall constants, though not the channel decomposition's qualitative structure (anchoring removes the alignable part; the residual is the un-alignable part).

**Recall under exact search.** Retrieval is exact top-10 by dot product. ANN indexes (HNSW, IVF) add their own degradation modes that compound with drift; the interaction (drift moving points across ANN partition boundaries) is real and unmodeled — an engineering follow-up with the same harness.

**The Procrustes claim's scope.** Proposition 2's exactness is for noiseless isometry; with distortion present, the estimated alignment absorbs some distortion noise (the $\sqrt{d/L}$ law), and with *anisotropic* distortion (systematic reshaping correlated with content), the orthogonal map is no longer the right functional form — a general linear or affine alignment would fit better and invalidate the clean $d$-scaling story. Whether real churn's distortion is isotropic is precisely the trace study's second measurement.

**One retrieval task.** Top-10 nearest-neighbor recall with cluster-structured ground truth. Semantic retrieval tasks with graded relevance, cross-modal encoders, or re-ranking stages will translate drift differently; the *drift law* is task-free, but the recall curves are task-specific.

## 8. Conclusion

The operators of every vector index on earth are currently making a re-embedding decision with no law to consult, and the folklore they use conflates two things that behave oppositely. The generation-loss law separates them: churn is an isometry channel and a distortion channel; the first is dimension-mercied into near-harmlessness and removable exactly by a landmark-panel Procrustes refresh costing $8d$ objects per generation; the second is dimension-free, un-alignable, and geometrically accumulating — the only real cost of encoder upgrades. $D(g) = 1 - \lambda^g$ with the two-channel $\lambda$ predicts drift to three decimals across channels, dimensions, and levels; the anchored system nearly doubles the stale system's recall under rotation-dominated churn for a rounding error of cost; the landmark law prices the panel at $\sqrt{d/L}$; and the dimension-mercy arithmetic retires the low-dimensional intuition that makes operators fear rotations they should not and ignore distortion they should. The measurement protocol is two probes and one matrix solve per upgrade; the decision rule falls out of $\lambda$. The calendar should be fired, and replaced with arithmetic.

## References

1. Schönemann, P. H. *A generalized solution of the orthogonal Procrustes problem.* Psychometrika 31(1), 1966.
2. Hamilton, W. L., Leskovec, J., and Jurafsky, D. *Diachronic word embeddings reveal statistical laws of semantic change.* ACL, 2016.
3. Kulkarni, V., Al-Rfou, R., Perozzi, B., and Skiena, S. *Statistically significant detection of linguistic change from word frequency time series.* ACL, 2015.
4. Artetxe, M., Labaka, G., and Agirre, E. *Learning principled bilingual word embeddings alignment...* (the cross-lingual orthogonal alignment lineage). Verification-queued.
5. Lenc, A., and Vedaldi, A. *Understanding image representations by measuring their equivariance and equivalence.* CVPR, 2015 (representation compatibility/stitching).
6. Frankle, J., et al. *Linear mode connectivity* (nearby checkpoints and approximately linear maps). Verification-queued.
7. The vector-database operational literature on re-embedding cadence (vendor runbooks, re-embedding cost calculators). Verification-queued.
8. Artetxe, M., and Schwenk, H. *Massively multilingual sentence embeddings* (aligned multilingual spaces). Verification-queued.

## Appendix: reproducibility

`code/p-023-simulation.py` (NumPy + Matplotlib, single file) regenerates all five figures and `figures/p-023/results.json` with every aggregate in the text: the drift series per configuration, the recall series per system, both decomposition heatmaps, the landmark curve, and the dimension family. The Procrustes self-check (noiseless exact-rotation recovery) runs at import time and asserts $10^{-12}$ precision — the paper's Proposition 2 is literally an assertion in the code. Seeds: F1 11, F2 21, F3 31, F4 41, F5 51; the agent-run figures used these seeds on PCG64.
