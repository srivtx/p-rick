# p-rick — an independent research program on missing software

> Software the world is **missing**, specified before anyone builds it.

**p-rick** finds and specifies software categories that do not exist yet — gaps where a real
problem meets a large audience and no incumbent — and does the research to close them:
landscape verification, formal models, reference architectures, evaluation designs, and
honest confrontation with the reasons each gap survived. Every paper ships with a PDF and a
plain-language essay. Research first; products later, in separate directories, only after the
research is done.

**Site (dark mode + light mode): <https://srivtx.github.io/p-rick/>**

---

## The papers

### Series II — systems (current)

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-004** | [Degradation Contracts](papers/p-004-degradation-contracts.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-004.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p004.html) | A formal language + runtime that makes *how software behaves under resource pressure* declarable, enforceable, and auditable — instead of accidental. |
| **P-005** | [Provenance-Native Storage](papers/p-005-provenance-native-storage.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-005.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p005.html) | The file system as a causal ledger: every file remembers where it came from, what produced it, and what depends on it. |
| **P-006** | [The Attention Scheduler](papers/p-006-attention-scheduler.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-006.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p006.html) | Human attention as a first-class OS-schedulable resource: cost models, admission control, budgets with honesty pricing, latency guarantees, an attention ledger. |
| **P-007** | [The Intermittent Compute Fabric](papers/p-007-intermittent-compute-fabric.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-007.pdf) · [essay](https://srivtx.github.io/p-rick/blog/p007.html) | One schedulable machine across a person's devices: partition-tolerant placement, capability delegation, ambient CRDT state — the host for local AI. |

### Series I — user-owned data & the economics of inattention (originated in srivtx/pocketveto, moved here)

| ID | Paper | The missing thing |
|----|-------|-------------------|
| **P-001** | [The Personal Event Bus](papers/p-001-personal-event-bus.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-001.pdf) | User-owned middleware that captures and keeps ambient digital-life events (payment events, receipts, gate changes) instead of throwing them away. |
| **P-002** | [Consumer Entitlements as Dead Capital](papers/p-002-consumer-rights-dead-capital.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-002.pdf) | The personal entitlement engine: consumer rights as machine-readable objects with detection, valuation, and execution. |
| **P-003** | [The n=1 Cost-of-Living Index](papers/p-003-n1-cost-of-living-index.md) · [PDF](https://srivtx.github.io/p-rick/pdfs/p-003.pdf) | A statistically defensible personal price index — the methodology layer no consumer software has. |

Each paper follows the same discipline: state the gap as a **falsifiable claim**, grade the
evidence (strong / partial / weak), survey the adjacent systems that solve one slice, design
the system that closes the gap, and confront the strongest objections — including the ones
that might kill the thesis. Papers are working drafts; the ledger of revisions is
[`agents.md`](agents.md).

## The method

1. **Gap research before writing.** Every direction survives a landscape survey before a
   paper is started; directions that die in survey die quietly (the survey notes survive in
   the work log).
2. **Falsifiable gaps, not vibes.** "No system does X" is written so one search can refute it.
3. **Honest grading.** STRONG / PARTIAL / WEAK verdicts on the evidence, stated in the paper.
4. **Specification over prototype theater.** Formal models, architectures, and evaluation
   designs — the artifacts a builder actually needs — before any code.
5. **Essays with every paper.** Each paper has a companion essay in plain language, written
   the way technical leaders write, because research that nobody reads is a diary.
6. **Automatic work tracking.** [`agents.md`](agents.md) is the session ledger — nobody has to
   remember or ask how long anything took.

## Repository layout

```
p-rick/
├── index.html            # the research site (GitHub Pages, dark + light mode)
├── papers.html, blog.html, blog/*.html
├── assets/               # style.css (dual theme) + theme.js
├── papers/               # paper sources (markdown)
├── pdfs/                 # typeset papers (PDF)
├── blogs/                # essay sources (markdown)
├── tools/build_site.py   # regenerates blog pages from blogs/*.md
└── agents.md             # the automatic work ledger
```

The site deploys from the repo root on push to `main` (GitHub Pages, static, `.nojekyll`).

### Build / regenerate

```bash
# regenerate blog pages after editing blogs/*.md
python3 tools/build_site.py
```

PDFs are typeset from `papers/*.md` via LaTeX (Tectonic) with composed covers; sources of the
conversion pipeline are kept by the research program workspace and documented in `agents.md`.

## agents.md — automatic work tracking

Every work session (human, AI, or hybrid) appends one record to [`agents.md`](agents.md]:
what was done, when, how long, and links to artifacts. Read the last record to see where
things stand; append a record when you finish work. The ledger is the source of truth for
effort, output, and lineage — so nobody has to know how long we have worked; the file knows.

## Program status

- Series I complete (3 papers) — originated in `srivtx/pocketveto`, moved to this repository
  when the program outgrew its host.
- Series II complete (4 papers) — researched, written, and published from this repository:
  systems gaps (degradation, provenance, attention, fabric), unrelated to Series I's
  personal-data topic territory.
- **Next:** product directories (one per validated direction) — created only after the
  research is finished, per the program charter.

## License

MIT — see [LICENSE](LICENSE). Papers and essays: CC BY 4.0 for the text; cite the paper ID.
