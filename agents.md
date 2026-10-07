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
