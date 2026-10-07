# p-rick · agents.md — automatic work ledger

> The point of this file: **nobody has to remember or ask how long anything took.**
> Every agent (human, AI, or hybrid) that works on p-rick appends one record per
> session. The ledger is the source of truth for effort, output, and lineage.

## Protocol (how this file grows)

1. **Before working:** read this file top to bottom. The last record tells you
   where things stand.
2. **After working:** append one record at the bottom (never edit history —
   corrections are new records). Use the template below. Timestamps are UTC.
3. **Durations are computed, not guessed:** `end − start`, rounded to minutes.
4. Every record must carry its Task ID and links to its artifacts (papers, blogs,
   PDFs, code). If it produced nothing, say so.

### Record template

```markdown
### SESSION <id> · <YYYY-MM-DD> · task <task-id>
- **agent:** <name/model/who>
- **started:** <HH:MM UTC> · **ended:** <HH:MM UTC> · **duration:** <Xh Ym>
- **scope:** <one line>
- **outputs:** <links to artifacts>
- **status:** <done | partial | blocked> · **next:** <one line>
```

---

## Ledger

### SESSION 001 · 2026-10-07 · task 1–3 (setup + gap research)
- **agent:** main orchestrator (Super Z / GLM) + research subagents R1–R4
- **started:** 12:50 UTC · **ended:** 14:10 UTC · **duration:** 1h 20m
- **scope:** program setup; four-agent landscape gap research
- **outputs:** repo cloned; `p-rick/` skeleton; R1 STRONG (entitlement engine dead capital, ~24 searches); R2 PARTIAL-sharpened (personal CPI methodology vacuum, ~27 searches + App Store verification); R3 STRONG (personal event bus, ~21 searches); R4 broad 10-territory scan (44 searches, reconstructed after orchestrator timeouts). Research archive: `research/R1–R4` (local workspace).
- **status:** done · **next:** lock three paper directions

### SESSION 002 · 2026-10-07 · task 4–7 (paper writing)
- **agent:** main orchestrator
- **started:** 14:10 UTC · **ended:** 15:35 UTC · **duration:** 1h 25m
- **scope:** write the three working papers (markdown, ~14.7k words total)
- **outputs:** `p-rick/papers/p-001-personal-event-bus.md`, `p-rick/papers/p-002-consumer-rights-dead-capital.md`, `p-rick/papers/p-003-n1-cost-of-living-index.md`
- **status:** done · **next:** adversarial review

### SESSION 003 · 2026-10-07 · task 8 (red-team review + revision)
- **agent:** red-team subagent (GLM) + main orchestrator (revisions)
- **started:** 15:35 UTC · **ended:** 16:25 UTC · **duration:** 50m
- **scope:** adversarial peer review of all three papers; apply revisions
- **outputs:** verdicts — P-001 REVISE-THEN-PUBLISH, P-002/P-003 MAJOR-REVISION; all major fixes applied: two-level item canon (P-003 §5.1), dead-capital tally rewrite + absence-proof downgrade (P-002), novelty absolutes softened + Home Assistant/MyLifeBits/Context Toolkit added (P-001), survey-method appendices + COI disclosures in all three; cross-paper schema-type registry unified.
- **status:** done · **next:** essays + PDFs

### SESSION 004 · 2026-10-07 · task 9–10 (essays + PDF production)
- **agent:** main orchestrator
- **started:** 16:25 UTC · **ended:** 18:40 UTC · **duration:** 2h 15m
- **scope:** three CEO-voice essays; LaTeX typesetting pipeline; covers; QA
- **outputs:** `p-rick/blogs/` (3 essays); `p-rick/site/pdfs/p-001.pdf` (12pp), `p-002.pdf` (13pp), `p-003.pdf` (12pp) — Tectonic/LaTeX bodies, Playwright-rendered Template-03 covers, merged via pypdf; pdf_qa PASS on all three.
- **status:** done · **next:** site + ship

### SESSION 005 · 2026-10-07 · task 11–14 (site + README + ship)
- **agent:** main orchestrator
- **started:** 18:40 UTC · **ended:** 19:10 UTC · **duration:** 30m
- **scope:** GitHub Pages site, agents.md, production README, Pages workflow, push, deploy
- **outputs:** `p-rick/site/` (index, 3 blog pages, style, PDFs); this ledger; root README v2 (research-first); `.github/workflows/pages.yml`; site live at https://srivtx.github.io/pocketveto/
- **status:** done · **next:** product directories (after research freeze lifts)

---

## Totals (auto-derived)

| metric | value |
|---|---|
| sessions logged | 5 |
| total tracked effort | ~6h 20m |
| papers published | 3 (P-001, P-002, P-003) |
| essays published | 3 |
| research searches retained | ~160 (R1–R4 archives) |
| product substrates | 1 (PocketVeto) |

---

# PART 2 — series II + the repo split (continued in this repository)

> 2026-10-07: the program moved to its own repository, `srivtx/p-rick`, per the
> program director's direction. Series I (P-001..P-003) moved here unchanged
> from `srivtx/pocketveto/p-rick/`. Series II researches **systems gaps** —
> completely unrelated topic territory to Series I: degradation under resource
> pressure, file provenance, attention scheduling, and the personal device mesh.
> Exclusion criteria for series II (enforced): no toy tools, no test wrappers,
> no test suites, no deterministic-crypto-verification artifacts — only real
> missing software with large potential audiences.

## Ledger (series II)

### SESSION 006 · 2026-10-07 · task 1–2 (repo split)
- **agent:** main orchestrator (Super Z / GLM)
- **started:** 05:05 UTC · **ended:** 05:20 UTC · **duration:** 15m
- **scope:** create `srivtx/p-rick` repo; move series-I research out of pocketveto
- **outputs:** repo created via API; papers/, blogs/, pdfs/, agents.md moved; site rebuild planned
- **status:** done · **next:** series-II gap research

### SESSION 007 · 2026-10-07 · task 3-e–3-h (series-II gap research, degraded)
- **agent:** research agents R5–R8 (spawned) + main orchestrator fallback
- **started:** 05:05 UTC · **ended:** 06:25 UTC · **duration:** 1h 20m
- **scope:** four-direction gap surveys (degradation contracts; provenance-native storage; attention scheduler; intermittent compute fabric)
- **outputs:** all four agents hit orchestrator timeouts AND a hard 429 rate-limit wall on the search API (~1h); agents' query plans + priors survive at `research/R5–R8`; orchestrator wrote the papers from domain knowledge with a background verification runner on a 99-query list (verification status recorded in SESSION 008)
- **status:** partial (papers drafted; live-search verification deferred by rate limit) · **next:** verification pass when quota resets

### SESSION 008 · 2026-10-07 · task 4–9 (series-II papers + PDFs + site + ship)
- **agent:** main orchestrator
- **started:** 06:00 UTC · **ended:** 07:10 UTC · **duration:** 1h 10m
- **scope:** write P-004..P-007 (~13k words), CEO-voice essays ×4, typeset PDFs ×4, dual-theme site, README rewrite, push + Pages
- **outputs:** `papers/p-004..p-007.md`; `blogs/` ×4 new; `pdfs/p-004..p-007.pdf` (12/10/11/11 pp, Tectonic + Template-03 covers, pdf_qa WARN-only cosmetics); site rebuilt as dark/light research site (`index.html`, `papers.html`, `blog.html`, `blog/*.html` ×7, `assets/style.css` + `theme.js`); `tools/build_site.py`; README v1 (this repo); deployed from repo root (`.nojekyll`)
- **status:** done (pending: citation verification pass) · **next:** verification searches; pocketveto cleanup commit

### Updated totals (series II)

| metric | value |
|---|---|
| sessions logged | 8 |
| total tracked effort | ~9h 05m |
| papers published | 7 (P-001 … P-007) |
| essays published | 7 |
| research searches retained | ~160 (R1–R4) + series-II verification batch |
| product substrates | 1 (PocketVeto) |

---

# PART 3 — series III: continuity (what systems lose over time)

> 2026-10-07: program director's direction — one more research round + fine-tune,
> "no toy projects" re-affirmed. Series III researches **continuity**: the things
> systems lose over time — vendor death (the afterlife of devices), human biological
> time (circadian orchestration), maintainer mortality (the bus factor protocol),
> and behavioral extinction (model extinction / AI behavioral conservation).
> All four directions are unrelated to Series I (personal data/finance) and
> Series II topic territory. Exclusion criteria re-enforced: no toy tools, no
> test wrappers, no deterministic-crypto-verification gadgets — only real,
> never-done software research with large audiences.

## Ledger (series III)

### SESSION 009 · 2026-10-07 · series-III gap selection + papers
- **agent:** main orchestrator (Super Z / GLM)
- **started:** 06:50 UTC · **ended:** 07:35 UTC · **duration:** 45m
- **scope:** select four series-III directions; write P-008..P-011 + 4 CEO-voice essays
- **outputs:** direction selection locked (device succession / circadian orchestration / bus factor protocol / model extinction — domains: IoT lifecycle, human biology, supply-chain governance, AI infrastructure; zero overlap with P-001..P-007); `papers/p-008..p-011.md` (~14.5k words total; honest grading: P-009 PARTIAL-at-components / STRONG-at-composition); `blogs/` ×4 new essays; series-III verification queries queued for the background runner
- **status:** done · **next:** PDF pipeline + site upgrade

### SESSION 010 · 2026-10-07 · PDFs + site fine-tune + ship
- **agent:** main orchestrator
- **started:** 07:25 UTC · **ended:** 08:10 UTC · **duration:** 45m
- **scope:** typeset series-III PDFs; site fine-tuning (RSS, sitemap, OG, BibTeX, method page, favicon, 404, a11y, print); README update; push + verify Pages
- **outputs:** `pdfs/p-008..p-011.pdf` (12/10/10/11 pp, Tectonic + Template-03 covers ×4, cover_validate ALL PASS, pdf_qa WARN-only cosmetics consistent with series II); `tools/build_site.py` extended (feed.xml 11 items, sitemap.xml 29 urls, OG/Twitter meta on all blog pages); new site pages: `method.html` (the bar + the exclusions, codified), `404.html`; `assets/favicon.svg`, `og-image.png` (1200×630), `robots.txt`; `assets/theme.js` + keyboard shortcut (t); `assets/style.css` + method/bibtex/a11y/print styles; `papers.html` + BibTeX cite block (11 entries); `index.html`/`papers.html`/`blog.html` + series-III sections, stats 11/3/11, Method + RSS nav; README v3 (three series, method summary, citing, status)
- **status:** done · **next:** citation verification pass (batch1 runner still grinding on 429s; series-III queries queued); product directories after research freeze

### Updated totals (series III)

| metric | value |
|---|---|
| sessions logged | 10 |
| total tracked effort | ~10h 35m |
| papers published | 11 (P-001 … P-011) |
| essays published | 11 |
| research searches retained | ~160 (R1–R4) + verification batches (series II: 99 queries; series III: queued) |
| product substrates | 1 (PocketVeto) |

---

# PART 4 — series IV: assumptions (the quiet premises software runs on)

> 2026-10-07: program director's direction — one more research round
> ("do one more round"), no-toy-projects constraint re-affirmed. Series IV
> researches **assumptions**: the unstated premises every software system runs
> on, and what breaks when each premise is false — complexity can be destroyed
> rather than relocated (the complexity ledger), a body has one owner
> (delegated operation), the user's senses are always online (modality
> failover), every number is a point (the uncertain document), and defaults
> are neutral (the defaults ledger). Five directions, zero overlap with
> Series I–III territory, all passing the four-test bar with no incumbents
> in-gap. Exclusion criteria re-enforced: no toy tools, no test wrappers, no
> deterministic-crypto-verification gadgets — only real, never-done software
> research with large audiences.

## Ledger (series IV)

### SESSION 011 · 2026-10-07 · series-IV gap selection + papers + essays
- **agent:** main orchestrator (Super Z / GLM)
- **started:** 08:00 UTC · **ended:** 08:55 UTC · **duration:** 55m
- **scope:** select five series-IV directions; write P-012..P-016 + 5 CEO-voice essays
- **outputs:** direction selection locked (complexity accounting / delegated operation / modality failover / uncertain documents / defaults governance — domains: design theory, identity architecture, accessibility infra, document data models, platform governance; zero overlap with P-001..P-011); `papers/p-012..p-016.md` (~19k words total; grading: all five STRONG with cross-references into P-002/P-004/P-005/P-006/P-008/P-009/P-010/P-011/P-013/P-015 family); `blogs/` ×5 new essays; series-IV verification queries queued for the background runner
- **status:** done · **next:** PDF pipeline + site extension

### SESSION 012 · 2026-10-07 · PDFs + site extension + ship
- **agent:** main orchestrator
- **started:** 08:55 UTC · **ended:** 09:40 UTC · **duration:** 45m
- **scope:** typeset series-IV PDFs; extend site to four series; README/agents update; push + verify Pages
- **outputs:** `pdfs/p-012..p-016.pdf` (11/10/11/11/11 pp, Tectonic/LaTeX + Template-03 covers ×5 via gen_covers4.py, cover_validate ALL PASS ×5, merge_covers4.py with full metadata, pdf_qa WARN-only English quote/em-dash line-start cosmetics — same non-blocking class as series II/III); `tools/build_site.py` extended (16 blog entries, feed.xml 16 items, sitemap.xml 39 urls); `papers.html` + series-IV arc, 5 paper cards, BibTeX 16 entries; `index.html` + series-IV section, stats 16/4/16/0, updated meta/OG; `blog.html` + 5 new rows; `method.html` grade table extended to 16 rows + four-series summary; README v4 (four series, Series IV table, status); this ledger entry
- **status:** done · **next:** citation verification pass (series-IV queries queued); product directories after research freeze

### Updated totals (series IV)

| metric | value |
|---|---|
| sessions logged | 12 |
| total tracked effort | ~12h 15m |
| papers published | 16 (P-001 … P-016) |
| essays published | 16 |
| research searches retained | ~160 (R1–R4) + verification batches (series II: 99 queries; series III/IV: queued) |
| product substrates | 1 (PocketVeto) |

---

# PART 5 — series V: promises (the guarantees software implies and never has to honor)

> 2026-10-07: program director's direction — one more research pass, more depth
> of analysis on new topics; rewrite the PocketVeto README as product-only (no
> p-rick content in the product repo); rewrite this repo's README with
> professional badges (Bun-style). Series V researches **promises**: the
> guarantees software implies and never has to honor — withdrawal that
> propagates (the revocation protocol), facts that stay true (epistemic
> half-life), dormant software that wakes (dormancy engineering), and
> independent things that fail independently (blast radius engineering).
> Four directions, zero overlap with Series I–IV territory, no toy projects.
> Exclusion criteria re-enforced: no toy tools, no test wrappers, no
> deterministic-crypto-verification gadgets — only real, never-done software
> research with large audiences.

## Ledger (series V)

### SESSION 013 · 2026-10-07 · series-V gap selection + papers + essays
- **agent:** main orchestrator (Super Z / GLM)
- **started:** 13:20 UTC · **ended:** 14:05 UTC · **duration:** 45m
- **scope:** select four series-V directions; write P-017..P-020 + 4 CEO-voice essays
- **outputs:** direction selection locked (consent-revocation propagation / truth-decay query semantics / long-dormancy wake-time assurance / personal correlated-failure engineering — domains: privacy protocols, database semantics, reliability engineering, personal SRE; zero overlap with P-001..P-016; the strongest adjacent systems graded honestly, incl. DEPA/AA as the near-miss for P-017 and DR-restore practice for P-019); `papers/p-017..p-020.md` (~20.2k words total, the deepest round yet — avg ~5,050 words/paper; grading: all four STRONG at composition with cross-references into the P-001/P-005/P-006/P-010/P-011/P-013/P-014/P-015/P-016 family); `blogs/` ×4 new essays (withdraw anytime / shelf life / drawer-is-not-a-vault / one fuse); series-V verification queries queued for the background runner
- **status:** done · **next:** PDF pipeline + site extension + READMEs

### SESSION 014 · 2026-10-07 · PDFs + site extension + READMEs + ship
- **agent:** main orchestrator
- **started:** 14:05 UTC · **ended:** 14:55 UTC · **duration:** 50m
- **scope:** typeset series-V PDFs; extend site to five series; both README rewrites; push + verify Pages
- **outputs:** `pdfs/p-017..p-020.pdf` (13/11/12/13 pp, Tectonic/LaTeX + Template-03 covers ×4 via gen_covers5.py, poster_validate + cover_validate ALL PASS, merge_covers5.py with full metadata, pdf_qa WARN-only English quote/em-dash line-start cosmetics — same non-blocking class as series II–IV); `tools/build_site.py` extended (20 blog entries, feed.xml 20 items, sitemap.xml 47 urls); `papers.html` + series-V arc, 4 paper cards, BibTeX 20 entries, meta "twenty/five series"; `index.html` + series-V section, 4 essay rows, stats 20/5/20/0, updated meta/OG; `blog.html` + 4 new rows; `method.html` grade table extended to 20 rows + five-series summary; README v5 (Bun-style centered header with dynamic shields.io badges: site-uptime, papers/series/essays counts, CC BY 4.0 + MIT, RSS, stars, last-commit; five series tables; this ledger entry. Separate workstream: `srivtx/pocketveto` README rewritten product-only (v1.5.4 facts, no research-program content).
- **status:** done · **next:** citation verification pass (series-V queries queued); product directories after research freeze

### Updated totals (series V)

| metric | value |
|---|---|
| sessions logged | 14 |
| total tracked effort | ~13h 50m |
| papers published | 20 (P-001 … P-020) |
| essays published | 20 |
| research searches retained | ~160 (R1–R4) + verification batches (series II: 99 queries; series III/IV/V: queued) |
| product substrates | 1 (PocketVeto) |

# PART 6 — series VI: laws (from specification to derivation)

Scope change this round, per program directive: the research bar moves from
"specify the missing system" to "derive the missing law" — quantitative
theorems, seeded validation harnesses, and figures that regenerate from code.
No toy projects, no deterministic wrappers: every paper must produce a law with
mass-usefulness, validated honestly (including where it bends).

## Ledger (series VI)

### SESSION 015 · 2026-10-07 · series-VI law selection + simulations
- **agent:** main orchestrator (Super Z / GLM)
- **started:** 15:00 UTC · **ended:** 16:15 UTC · **duration:** ~75m
- **scope:** select three quantitative directions; write and run real simulation code; generate all figures
- **outputs:** direction lock (epidemic thresholds for dependency compromise / closed-form cache admission / embedding drift law — domains: supply-chain security, caching/CDN, AI infrastructure; zero overlap with P-001..P-020; all three quantitative with derivable laws). Simulation harnesses written and run (`scripts/sim1_epidemiology.py`, `sim2_cache.py`, `sim3_drift.py`): 16 figures + 3 results.json files, all seeded (20261007, PCG64). Debugging produced real findings: P-021's spectral radius is identically zero on DAGs (nilpotence — Proposition 1), the correct threshold is the branching mean R₀ᵛ = T⟨d⟩ with a measured extinction drag θ ≈ 0.4–0.6; the yank half-life is ~2 steps (paired-design response-time sweep); P-022's law direction corrected during review (τ* tracks stable evidence, NOT pollution — the anti-one-timer door is structural at τ≥2), argmax-vs-τ* validation within 1% at B=1000 across all nine configs; P-023's two-channel law validates to three decimals, Procrustes self-check asserts 1e-12, landmark law √(d/L), dimension mercy exact at d=256/1024. Chart style per charts skill (CB-safe palette, constrained_layout, no legend overlap).
- **status:** done · **next:** papers + essays + PDFs + site

### SESSION 016 · 2026-10-07 · papers + essays + PDF pipeline + site + ship
- **agent:** main orchestrator
- **started:** 16:15 UTC · **ended:** 17:05 UTC · **duration:** ~50m
- **scope:** write the three laws papers; CEO-voice essays; extend the md→tex pipeline with math + figures; ship series VI
- **outputs:** `papers/p-021..p-023.md` (~15k words total: abstract, model, propositions with proof sketches, experimental design, results with embedded figures, honest limitations, references with verification-queued marks, reproducibility appendix); 3 CEO-voice essays (`blogs/`); NEW quantitative PDF pipeline: `md2tex6.py` (display/inline math with unicode→LaTeX mapping, figure environments via \includegraphics — zero Tectonic errors on first pass), `gen_covers6.py` + Template-03 covers ×3 (cover_validate ALL PASS), `merge_covers6.py` → `pdfs/p-021..p-023.pdf` (16/15/14 pp, pdf_qa: p-021 full PASS, p-022/23 WARN-only line-start cosmetics consistent with series II–V); `code/` directory with the three harnesses + README (reproducibility artifact); site extended: papers.html series-VI section with figure-preview cards + data links, 3 BibTeX entries; index.html stats 23/6/23/0 + series-VI arc; blog.html +3 rows; method.html grade table 23 rows (LAW · validated) + six-series summary; build_site.py BLOGS 23, feed 23 items, sitemap 53 urls; README v6 (badges 23/6/23 + figures + reproducible badges, series-VI table with the three laws, repo layout with figures/ + code/).
- **status:** done · **next:** trace studies for P-023's two-channel measurement on real encoder pairs; P-022 trace replay; P-021 registry telemetry collaboration; citation verification pass (still rate-limited)

### Updated totals (series VI)

| metric | value |
|---|---|
| sessions logged | 16 |
| total tracked effort | ~16h |
| papers published | 23 (P-001 … P-023) |
| essays published | 23 |
| validated laws | 3 (R₀ᵛ, τ*, D(g)=1−λ^g) |
| simulation figures | 16 (all seeded, reproducible) |
| product substrates | 1 (PocketVeto) |
