# Active brief

Status: **active — delivered once, returned for correction (Amendment 1 below)**.

Identifier: **`019-2026-09-20-readme-badges`** — use exactly this string as
`--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (018 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — topology, project invariants, evidence
   table.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full, then `README.md`.

The house README standard lives in the **framework repository**, not this one:
`standards/readme.md` in `cntrl-alt-lenny/agentic-framework`. Read it there
(the local clone is at `/Users/leo/Dev/agentic-framework`; do not modify that
repository). Do not read `docs/research/`.

---

## MODE: IMPLEMENTATION

## Goal

Every badge in this README states a fact that is true right now because it is
read from somewhere real, and the badge row matches the house standard. The
README's words, shape, length and the format banner stay as they are.

## Why this is next

Brain compared this README against the standard and found the gap small:
length (471 words), section shape, the credits and the generated format banner
already match, and the banner is exactly the kind of live progress graphic the
standard asks for. Two things do not:

- the **license badge is hand-typed** (`img.shields.io/badge/license-MIT-…`),
  and the standard requires anything that can change to be read live. Brain
  confirmed GitHub recognises this repository's LICENSE as MIT and that the
  live form already renders "license: MIT";
- there is **no progress badge**, though the standard lists one in the badge
  order and this repository computes real per-format status.

The owner has approved both. The CI badge is *not* a defect: the standard's own
source table specifies GitHub's Actions badge for CI, so leave it.

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Scope

`README.md`; whatever small generator, data file and test the progress badge
needs; `.github/workflows/ci.yml` **only if** your chosen approach genuinely
requires it, subject to the constraint below.

## Non-goals

- **No rewrite.** Do not restructure sections, reword prose, change the
  banner, or move content into `docs/`. Length and shape already pass.
- **No news-style panels** — no "What's New", timelines or recent-commit
  feeds. This is an explicit owner decision: live progress or status graphics
  are wanted, activity feeds are not.
- No change to the CI badge, the Python floor badge (a static runtime-floor
  badge is allowed by the standard), or the banner image.
- Do not add a release badge; this repository has no releases.
- Do not modify the framework repository.
- No canonical data, errata, `dist/` or validator change.

## Protected invariants

- **A badge must not be able to lie.** Anything that can change is read from
  GitHub or from generated repository state. Nothing that can go stale is
  typed into the README by hand.
- **Whatever the progress badge reports must be generated from canonical
  state and guarded by a test**, the way `dist/` and the atlas already are: if
  the data changes and the badge's source file is not regenerated, something
  must fail. A badge nobody can prove is current is the defect this round
  exists to remove.
- **Enforcement stays as strong as it is.** Adding a CI step is fine. If your
  approach would need new workflow permissions, a new branch pushed to by CI,
  or any change to what CI gates, **stop and report that instead** — that is
  the owner's decision, not this round's. An approach that needs none of it is
  available.
- Badge order from the standard, skipping ones this project has no source for:
  CI → progress → language → license. Four badges, `flat` style; every badge
  links to its evidence; the license label is spelled `license`.
- Validator baseline 0 errors / 569 warnings; suite at base 1034 tests, OK, 25
  skipped; GOAT hash `0x28E9FC02` unchanged.

## Required investigation

1. Read the standard yourself and list what it actually requires of a badge
   row, rather than taking this brief's summary for it.
2. Decide what the progress badge should *measure*. `python -m retroformats
   report` prints per-format status across four axes; `formats/*/format.json`
   holds `implementation_status`. Pick something honest and legible that a
   reader can interpret without this repository's vocabulary, and say why you
   chose it over the alternatives. Do not invent a number that overstates
   completeness — this project's own epistemics apply to its landing page.
3. Establish how the badge reads that value, and how the value stays current.
   State what happens if someone changes canonical data and forgets.

## Acceptance criteria

- Every badge in the README resolves to a real image and reflects something
  real: CI from the workflow, progress from generated state, license from
  GitHub, the runtime floor static and correct.
- The progress badge's source data is generated, not hand-written, and a test
  fails if it is stale.
- Badge order, `flat` style, `license` spelling, and every badge linking to
  its evidence.
- README prose, structure, length and banner unchanged apart from the badge
  row. `git diff` on `README.md` shows the badge block and nothing else.
- No new CI permissions, no new CI-written branch, and no change to what CI
  gates — or, if you believe one is genuinely required, no such change made
  and the question reported instead.

## Required evidence

- Each badge URL requested directly, with its HTTP status and what the
  rendered badge says (shields returns SVG containing the text).
- The command that regenerates the progress badge's data, its real output, and
  proof the guard fails when the data is stale — show it red, then green.
- `python -m retroformats validate`, `python -m retroformats build --check`,
  `python -m unittest discover -t . -s tests -v`, with real output and exit
  status, on Python 3.10 or newer.
- `git diff --stat <base>..<head>`.

## When to stop

If an honest progress measure cannot be derived without a judgement call about
what "complete" means for this project, stop and present the options rather
than picking one.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/readme-badges` from `origin/main`. Focused commits;
push the branch; never push `main`; never merge. Before finishing, run
`git -C /Users/leo/Dev/edopro-retro-formats status --short` and confirm it
prints nothing. After your final commit and push, write your report from
inside `.worktrees/builder/` with
`python3 tools/report.py write --task 019-2026-09-20-readme-badges`
(Python 3.10+), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus:

- the badge row before and after, with each badge's source and what it
  currently renders;
- what the progress badge measures, why that measure, and what keeps it
  current;
- anything in the standard this README still does not meet, stated plainly
  rather than left for a reader to notice.

---

## Amendment 1 — 2026-09-21, after Brain's first adjudication

The first delivery, `8d0ae1ac7c5c2607707611439aea5b334885ba5b` on
`builder/readme-badges`, was **not accepted**. Most of it stands and is not
reopened: the count is correct (Brain re-derived 3 + 2 + 2 = 7 of 12 from
`python -m retroformats report`), the generated file is guarded and the guard
was shown red then green, CI is untouched, and only the badge row of the
README changed. Continue on the same branch from `8d0ae1a`; do not rewrite
history. This amendment lives on `origin/main`: read it with
`git show origin/main:docs/briefs/active.md`.

Two things break this brief's own first invariant — *a badge must not be able
to lie*.

### 1. The badges' alt text is hand-typed

The progress badge's image is live, but its `alt` attribute reads
`Progress: 7/12 areas`, and the license badge's reads `license: MIT`. Alt text
is what screen readers announce and what anyone reading the raw README sees.
When a format's status changes, the image updates and the alt text keeps
saying the old number, and nothing fails. Make alt text that cannot go stale,
or make staleness fail a test; choose, and say why.

### 2. The progress badge does not say what it counts

"progress 7/12 areas" means three canonical formats times four implementation
axes. The README places it directly above a banner covering a 128-format
catalogue, so an ordinary reader can take it as overall project progress,
which would overstate it badly. The brief asked for a measure "a reader can
interpret without this repository's vocabulary". Make the badge itself, not a
linked file, say what it counts — within what a single shields badge can
legibly hold — and justify the wording in your report. If you conclude no
single-badge wording can be both honest and legible, stop and present the
options.

### Note, not a change request

`tests/test_progress_badge.py` pins today's value (7, 12, "7/12 areas"). That
matches this project's habit of pinning counts so that a change is deliberate,
and it may stay. If you keep it, make its failure message say what else must
be updated when the value legitimately changes.

### Unchanged

Everything else in the brief, including: no CI permissions, no CI-written
branch, no change to what CI gates; no prose, structure or banner change.
The report covers the whole round from base
`42d8cee0e903a6e4f02ac0f2b8d138aa32153ea3`.
