# Active brief

Status: **active — delivered once, returned for correction (Amendment 1 below)**.

Identifier: **`018-2026-09-20-search-activation-semantics`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (017 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — topology, the non-negotiable project
   invariants, and the evidence table.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract), and its RESEARCH mode rules, which
   this project calls HISTORICAL RESEARCH.
3. This brief in full.

Then, and only as far as this brief needs them:
[`docs/research/edison-behaviour-gaps.md`](../research/edison-behaviour-gaps.md)
— the sections on the 38-card class, its A/B/C/D partition and the
"leverage" discussion — and the archived brief
[`010-2026-09-01-search-verification-interval.md`](archive/010-2026-09-01-search-verification-interval.md)
with its outcome. Do not read the rest of `docs/research/`.

---

## MODE: HISTORICAL RESEARCH

## Goal

Establish what period evidence says, if anything, about when the **activation
semantics** of "search and reveal-on-failure" effects changed — the axis that
is currently completely undated — and whether one historical policy governed
the whole class or each card was decided separately. An evidenced negative is
a complete result.

## Why this is next

Round 10 (merged) established that the *other* axis of this class, deck
verification, is already dated well enough: Edison sits determinately in the
old era, and narrowing that bracket further would not change a single
classification. The ambiguity comes entirely from the undated activation axis.
The same research records that 38 cards share both axes and one upstream
script pattern, and that a single period source could therefore resolve all of
them at once — but explicitly marks "one shared policy" as plausible and
**not confirmed**. That is the question this round answers.

The roadmap still describes item 1b as the high-leverage one. That is the
opposite of what the merged research says, which is Part B.

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Part A — the historical question

Frame it as a question, not a hypothesis to confirm.

1. **Define the population from the repository, not from this brief.** Derive
   the card set and the two axes yourself from the research document and the
   errata records, and state how many records you actually found. If it is not
   38, that is a finding.
2. **Establish whether the activation-semantics change was a single policy
   event or per-card.** Both answers are useful. So is "no period source
   settles it".
3. **Look for period evidence with provenance**: Konami/UDE judge materials,
   period rulings compilations, per-set rulings documents, official FAQ pages,
   archived tournament-policy documents. For anything you find, state what it
   actually proves — a document's date, the date it describes, and whether it
   is contemporary or retrospective are three different things.
4. **Say what a failed search proves.** It is evidence about the search, never
   proof that no such policy existed. If you cannot narrow it, record exactly
   what you searched, how, and what each source did and did not establish, the
   way round 10 did.

## Part B — correct one roadmap rationale

Roadmap item 1b says narrowing the 2011-02-02..2019-04-03 verification bracket
"would firm up a large group of records at once". The merged research in
`edison-behaviour-gaps.md` says narrowing it "would not change this cluster's
classification at all". Re-read both yourself, decide which is supported, and
correct whichever is wrong — including, if that is what the evidence shows,
the research document rather than the roadmap. Do not change the item's
status; item 1b stays open either way unless Part A closes it.

## Scope

`docs/research/edison-behaviour-gaps.md` (or a new research document if your
findings genuinely do not belong in it, with a pointer from the existing one),
`docs/roadmap.md` item 1b's rationale, and `data/sources.json` for any source
you actually cite.

## Non-goals

- **No canonical data, schema or errata record changes.** HISTORICAL RESEARCH
  mode forbids them, and this brief does not authorize an exception. If your
  findings would change an erratum's chronology, report that as the recommended
  next round; do not make the change.
- No `dist/` regeneration, no validator or test changes.
- Do not reopen the verification-axis bracket itself; round 10 settled its
  relevance.
- Do not re-derive round 10's ambiguity tables for their own sake.

## Protected invariants

- **Evidence before confidence** (`AGENTS.md`). Do not convert plausible into
  proven, retrospective into contemporary, publication date into effective
  date, or a shared script pattern into a shared historical policy.
- **A shared upstream implementation is engine evidence, not historical
  evidence.** That 38 cards use one script pattern says how EDOPro models them
  today; it says nothing on its own about 2010 policy.
- Every source you cite gets a real record in `data/sources.json` with what it
  does and does not establish; validator `sources.missing` applies.
- Validator baseline: 0 errors, 569 warnings. Suite at base: 1034 tests, OK,
  25 skipped. GOAT hash `0x28E9FC02`.

## When to stop

If the evidence supports a class-wide answer for some cards but not others, say
so with the split rather than generalising. If you find a source that would
change canonical records, stop at the finding and report it.

## Acceptance criteria

- A stated, sourced answer to Part A's question, or an explicit, specific
  account of a failed search — with, in either case, what it does and does not
  establish for the class.
- The population derived and stated from the repository.
- Part B's contradiction resolved in whichever direction the evidence supports,
  with the reasoning visible.
- No canonical data, schema, errata, `dist/` or test change.

## Required evidence

Per `AGENTS.md`'s evidence table for research documents: for every claim, the
URL or file and the passage you actually read. Plus
`python -m retroformats validate`, `python -m retroformats build --check` and
`python -m unittest discover -t . -s tests -v` with real output and exit status
on Python 3.10 or newer, and `git status --short data/ formats/ dist/` showing
no unexpected change.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/search-activation-semantics` from `origin/main`.
Focused commits; push the branch; never push `main`; never merge. Before
finishing, run `git -C /Users/leo/Dev/edopro-retro-formats status --short` and
confirm it prints nothing. After your final commit and push, write your report
from inside `.worktrees/builder/` with
`python3 tools/report.py write --task 018-2026-09-20-search-activation-semantics`
(Python 3.10+), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus:

- the population you derived, and how;
- every source searched, with what each did and did not establish;
- your answer to "one policy or per-card", stated at the confidence the
  evidence supports;
- what you deliberately left for a later round, especially anything that would
  touch canonical records.

---

## Amendment 1 — 2026-09-20, after Brain's first adjudication

The first delivery, `fef67eede396ef9d2cef3e8d4d556e89ba5dd9ac` on
`builder/search-activation-semantics`, was **not accepted**. The round stays
open on the same branch and identifier. Continue from `fef67ee`; do not rewrite
or force-push history. This amendment lives on `origin/main`: read it with
`git show origin/main:docs/briefs/active.md`.

**The research finding itself stands and is not reopened.** Brain independently
re-fetched the Konami Card FAQ capture and read both passages: Reinforcement of
the Army "cannot activate … if you do not have any Level 4 or lower
Warrior-Type monsters remaining in your Deck", while Release Restraint "you can
still activate this card … but you will need to show your cards to your
opponent to confirm". A same-capture per-card split, exactly as reported, and
correctly not generalised to the 38-card class. What follows is provenance,
which in this project is not a formality.

### 1. A cited source has no record — BLOCKER

`docs/research/edison-behaviour-gaps.md` cites
`web.archive.org/web/20081215054634/…/cardfaqs/default_st.html` for the Skilled
White Magician withdrawal, one of the three passages the per-card finding rests
on. `data/sources.json` has no record for it; the new record covers
`default_pr.html` only. Brain confirmed the passage is really there and that no
record exists. Register it properly, stating what it does and does not
establish, as the project requires of every cited source.

### 2. The cited capture is not the capture that gets served

`http://web.archive.org/web/20081215065604/…/default_pr.html` **302-redirects to
the `20081216162327` capture** — 2008-12-16, not 2008-12-15. Brain observed the
redirect and read the page it serves. The new source record, its id
(`konami-card-faq-2008-12-15`), and the research text all assert 2008-12-15.
The `default_st.html` URL, by contrast, returns 200 at its own timestamp.

For each archived source this round cites, establish the timestamp actually
served, and make the record and the research text say that. If an exact-capture
URL exists for the `default_pr.html` content, prefer it; if the content is only
available at a later capture, say so plainly. A nearest-capture redirect is a
different document date, which is the distinction this project exists to keep.

### 3. A date label that may describe the wrong thing — SHOULD FIX

The research text and `data/sources.json`'s `konami-set-rulings-archive` record
label the Starstrike Blast rulings evidence `2010-11-16`. The Verifier fetched
that PDF and reports it says "Compiled as of November 4, 2010". Brain could not
re-derive this: the archive index query returned nothing in that session, so
treat both readings as unverified.

Fetch the document yourself. Establish what date it states about itself, and
whether `2010-11-16` is its compilation date, the set's release date, or
something else. Then make both the record and the research text say which is
which. Do the same check for the `2011-02-02` Storm of Ragnarok label, since
that date is load-bearing: it is what attests the old verification state.
Correct the pre-existing record if it is wrong; that is in scope now.

### Unchanged

Mode, scope, non-goals and evidence requirements are as above: still no
canonical data, errata, schema, `dist/` or test change — `data/sources.json`
and the research and roadmap documents only. The report covers the whole round
from base `7a304d3e1d0e8ea2bf556a47b74a706119675684`, and must state, for every
archived URL it cites, the capture timestamp actually served.
