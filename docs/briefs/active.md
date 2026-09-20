# Active brief

Status: **queued, not started**.

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
