# Active brief

Status: **queued, not started**.

Identifier: **`017-2026-09-16-roadmap-reconciliation`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (016 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — topology, project invariants, evidence
   table.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.

Then [`docs/roadmap.md`](../roadmap.md) in full, and each archived brief in
`docs/briefs/archive/` **only as far as an open roadmap item needs it**. Do
not read `docs/research/` wholesale; open a research document only when a
roadmap item or archived outcome points at it for a specific claim.

---

## MODE: DOCUMENTATION

## Goal

Every item in `docs/roadmap.md` states its true status at the base SHA —
done, partly done, or open — with a pointer to the evidence, so the next piece
of project work can be chosen from the roadmap without re-checking it.

## Why this is next

Sequencing depends on the roadmap, and it has already misled a round: round
13's brief re-opened work that had been finished and merged, because the
roadmap never recorded it. Brain found the same pattern again while choosing
this round, and did not investigate it fully:

- item 1e (Mind Master card identity) still reads as open, while archived
  brief 004 and commit history suggest a mechanism for it was merged in
  round 4;
- items 6, 8 and 9 read as open, while archived briefs 007 and 008, a
  `check-deck` command and a CI workflow suggest at least part of each exists.

Treat those as leads to establish, not conclusions. There may be more; the
roadmap has never been reconciled as a whole.

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Scope

`docs/roadmap.md` only.

## Non-goals

- No code, data, schema, test, `dist/` or `docs/agents/` change.
- No new research. If an item's status depends on a question no merged work
  answered, the item is open — say so; do not investigate the question.
- Do not reorder, reprioritise, add or delete roadmap items. Sequencing is
  Brain's. Report anything you think should change instead.
- `docs/state.md` is Brain's; report anything in it you find contradicted.

## Protected invariants

- **Repository state outranks every narrative, including this roadmap and the
  archived briefs.** An archived "accepted" outcome says a round was merged; it
  does not prove what the code does now. For every item you mark done or
  partly done, check the present tree at the base SHA — the command exists,
  the file exists, the test exists and passes — and cite it.
- **Do not upgrade.** "A brief was written for it" is not "done"; "a mechanism
  exists" is not "done" if the item asked for more than the mechanism. Where
  the item's own wording asked for several things, account for each.
- **Keep history.** Mark completed items the way the roadmap already does
  (struck title, `Done (<date>)`, a short evidence sentence). Do not rewrite
  the substance of existing accepted records such as 4b's.

## Required investigation

For each numbered and lettered item in `docs/roadmap.md`:

1. What did the item ask for, in its own words?
2. What merged work, if any, addresses it — commit, archived brief and
   outcome?
3. What does the tree at the base SHA actually contain for it, checked
   directly?
4. Therefore: done, partly done (and exactly what remains), or open.

## Acceptance criteria

- Every roadmap item has a status that matches the tree at the base SHA,
  with an evidence pointer for anything not plainly open.
- Nothing is marked done that the tree does not support.
- The four leads above are each explicitly resolved one way or the other.
- No file other than `docs/roadmap.md` changes.

## Required evidence

- For each status change: the command or file check you ran at the base SHA
  and its real output.
- `python -m unittest discover -t . -s tests -v` at your head, on Python 3.10
  or newer, with real output and exit status (the roadmap is not under test,
  but nothing else should have changed).
- `git diff --stat <base>..<head>` showing only `docs/roadmap.md`.

## When to stop

If an item's status turns on a judgement about what the item *meant* rather
than on what exists — for example, whether an item is done when its core
landed but an optional part did not — do not pick. Record it as open with the
exact question, and list it in your report.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/roadmap-reconciliation` from `origin/main`. Focused
commits; push the branch; never push `main`; never merge. Before finishing, run
`git -C /Users/leo/Dev/edopro-retro-formats status --short` and confirm it
prints nothing. After your final commit and push, write your report from inside
`.worktrees/builder/` with
`python3 tools/report.py write --task 017-2026-09-16-roadmap-reconciliation`
(Python 3.10+), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus a table with one row per roadmap item:
item, previous status, new status, evidence (commit / archived brief / tree
check), and what remains if partly done. Then a list of judgement calls left
open, and anything you found contradicted in `docs/state.md`.
