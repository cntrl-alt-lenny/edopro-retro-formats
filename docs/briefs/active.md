# Active brief

Status: **queued, not started**.

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
