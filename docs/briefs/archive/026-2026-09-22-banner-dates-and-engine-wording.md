# Active brief

Status: **accepted** (see Outcome).

Identifier: **`026-2026-09-22-banner-dates-and-engine-wording`** — use exactly
this string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (025 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — the epistemic invariants, especially
   "publication date → effective date" and "unknowns stay unknown".
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.
4. `scripts/generate_format_atlas.py` (the banner renderer),
   `tests/test_format_atlas.py`, `docs/format-atlas-progress.json`, and the
   `period` object in each `formats/*/format.json`.
5. `docs/engine-testing.md`, the "CI covers Linux x86-64 only" paragraph.

---

## MODE: IMPLEMENTATION

Two small, unrelated corrections, bundled to save a round. Keep them in
separate commits.

## Part 1 — the banner shows dates this project doesn't claim

### Problem

Each banner row shows a date taken from the Format Library catalogue (for
example `05.08` for Goat, `10.04` for Edison). Those are that site's dates, not
this project's: Goat's canonical `period.start` is April 2005, Edison's March
2010. A project whose purpose is historical accuracy should not print, next to
its own formats, a date that disagrees with its own records and doesn't say
whose it is. `YY.MM` is also hard to read on a banner.

### Goal

Every date on the banner is either this project's own canonical date or
clearly not presented as one, and reads plainly (e.g. `Apr 2005`).

### Requirements

- Canonical formats show the month and year of their own `period.start`, read
  from `formats/*/format.json`. Establish yourself that `period.start` is the
  right field (what `notes` and the schema say it means) and say so in the
  report; if it is not, stop and report rather than choosing another.
- Research-only rows have no canonical period. Show a date only if the
  project's research-progress data already records one with a source; do not
  add a date by copying the catalogue's value into it. If no sourced date
  exists, show no date, or a label that makes clear it is not an established
  date. Say which you chose and why.
- A test fails if a canonical row's banner date disagrees with its
  `period.start`. Show it red in a scratch copy, then green.
- The banner otherwise stays as round 25 left it. The full atlas is out of
  scope and must stay byte-identical.

## Part 2 — an unevidenced line in the engine-testing notes

`docs/engine-testing.md` says the pinned engine "also builds and passes on
macOS arm64 (that is how it was first exercised)". No evidence of that
survives in the project. Reword it so it claims only what is evidenced — CI
covers Linux x86-64; other platforms are untested here — unless you can
produce the evidence yourself in this round, in which case include it and
say how. Do not change anything else in that document.

## Non-goals

- No change to canonical data, `dist/`, the full atlas, the progress badge,
  or any format's status.
- No change to CI or the engine helper.

## Acceptance criteria

- Banner rows show `Mon YYYY` dates from `period.start` for the three
  canonical formats, and the research row follows the rule above.
- `python scripts/generate_format_atlas.py --check` clean; full atlas
  byte-identical to base.
- The date test shown red, then green.
- The engine-testing line claims nothing unevidenced.

## Required evidence

`python scripts/generate_format_atlas.py --check`; the full suite
`python -m unittest discover -t . -s tests -v`; `python -m retroformats
validate` (0 errors / 569 warnings) and `python -m retroformats build
--check`; the red/green demonstration; the full atlas's SHA-256 at base and
head; the URL of `docs/assets/format-banner.svg` on the pushed branch; and a
rendered image of the banner saved **inside `.worktrees/builder/`** outside
any tracked path (for example `.worktrees/builder/.review/banner.png`,
untracked and uncommitted), with its full path given in the report, so the
reviewer can find it.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/banner-dates-and-engine-wording` from
`origin/main`. Focused commits; push the branch; never push `main`; never
merge; never bypass a local check. After your final commit and push, write
your report from inside `.worktrees/builder/` with
`python3 tools/report.py write --task 026-2026-09-22-banner-dates-and-engine-wording`
(`python` where `python3` does not resolve), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus: what `period.start` means and where that
is stated; what the research row shows and why; the red/green demonstration;
the atlas hashes; the image's path; and the exact before/after text of the
engine-testing line.

## Outcome — accepted 2026-09-22, merged with owner approval

Head `dba5c002cfcdb87553d4ea525acc190538f0e9ce`, base
`f91a6efaafe72bda73da4f12b50d8afba4f6d6e9`.

**Result.** Canonical banner rows show `period.start` as `Mon YYYY` (Apr 2005,
Mar 2010, Sep 2011); Tokyo Dome shows no date because no sourced one exists.
`docs/engine-testing.md` now says only Linux x86-64 CI is evidenced.

**Brain re-derived:** moved Edison's `period.start` in a scratch copy; the new
date test and the freshness test both went red, and green on restore. Viewed
the rendered banner at the path the report gave.

**Carried forward, non-blocking:** banner rows are still ordered by the
catalogue's date rather than `period.start` (same order today); the date test
names the three canonical formats explicitly, so a fourth would not be covered
automatically.
