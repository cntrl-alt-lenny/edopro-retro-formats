# 033-framework-3-1-0: Update to agentic-framework 3.1.0

Tier: 1
Mode: implementation
Supersedes: none

## Goal

This project runs agentic-framework 3.1.0, following the "What an adopter
must do" steps of the 3.1.0 section in the framework's `CHANGELOG.md`. After
the update, `python3 tools/fw.py status` shows each round in flight seat by
seat and ends with a `next:` line.

**Why this is next.** `fw.py status` reports 3.1.0 as available. The release
implements the owner's feedback,
[agentic-framework#26](https://github.com/cntrl-alt-lenny/agentic-framework/issues/26):
prompt headers, the `next:` line, `fw.py prompt`, and superseded rounds no
longer shown as in flight. It also fixes issues this project reported.

**Why Tier 1.** 3.1.0's changelog makes a minor update Tier 1: a Worker,
then Brain re-derives, with no Verifier. The update never overwrites a
locally edited framework file, and the project's own checks run. The owner
asked on 2026-09-28 for the update to run as that section describes. The
3.0.0 `FRAMEWORK.md` this project runs today still says every update is
Tier 2; 3.1.0 replaces that text.

## Context

- The framework's `CHANGELOG.md` at tag `v3.1.0`: the whole "3.1.0" section,
  and especially "What an adopter must do". Clone the framework at `v3.1.0`
  outside this project folder, for example in a temporary directory.
- `AGENTS.md`, `docs/agents/FRAMEWORK.md`, `docs/agents/roles/worker.md`,
  `docs/state.md`, `docs/agents/framework.json`.
- `docs/rounds/028-framework-3-0-0/`, how the previous update round went.

## Scope and non-goals

In scope, in the changelog's order:

1. Run `python3 tools/adopt.py <this project> --update --dry-run` from the
   framework clone at `v3.1.0`, then run it without `--dry-run`. Put the
   complete output of both runs in the report.
   - A `gone` line is a file this project deleted; it stays deleted.
   - For each `other` line in `.claude/agents/`, establish whether it is a
     second seat file for one seat, and delete one of the two only if it
     is. This project's seat files are `brain.md`, `verifier.md` and
     `worker.md`; the Builder holds the Worker contract.
2. Establish whether `AGENTS.md` carries a prompt-header rule of its own.
   One was drafted on 2026-09-27 but never merged, so none is expected. If
   one is present, delete it.
3. Step 3 is optional: a `settings.report_check` in
   `docs/agents/framework.json`. Add one only if this project has a fast
   check that a report file can break. If you find none, say so and add
   nothing.
4. Run `python3 tools/fw.py status` and check both points in step 4 of the
   changelog: each round in flight is shown seat by seat, and the last line
   starts with `next:`.
5. **Project wording that 3.1.0 now contradicts.** Where `AGENTS.md` or
   `docs/state.md` restates something 3.1.0 changes, update the smallest
   amount of wording, and list each sentence changed. At least these:
   - `AGENTS.md` § Topology and `docs/state.md` "One project folder": seat
     checkouts are now `.worktrees/<role>-<number>`, not
     `.worktrees/<role>`.
   - Anything that says framework updates are always Tier 2.

   Don't restate framework text in project files; point to it.

Non-goals:

- **No edits to framework files** (`docs/agents/`, `tools/fw.py`,
  `tools/adopt.py` and adapter copies) other than what `adopt.py` writes
  (`FRAMEWORK.md` rule 14). If `adopt.py` writes a `.framework` copy beside
  a locally edited file, stop and report it rather than merging it by hand.
- No change to product code, canonical data, `dist/` or tests beyond what
  the update itself installs.
- No new framework feedback issues unless the update itself fails. If it
  does, record the problem in the report and file it on the framework's
  "Framework feedback" form.

## Invariants

- Framework files are never edited locally (`FRAMEWORK.md` rule 14).
- `docs/state.md` stays within its word budget, and `fw.py check` passes.
- Product behaviour is unchanged: `validate` 0 errors and 563 warnings,
  `build --check` clean, and the GOAT hash `0x28E9FC02` unchanged.

## Acceptance criteria

- `docs/agents/framework.json` pins 3.1.0, and `fw.py status` says it is up
  to date.
- `fw.py status` output matches changelog step 4. Show it with this round in
  flight.
- `python3 tools/fw.py prompt --round 033-framework-3-1-0 --role builder`
  prints a prompt whose first line is the
  `edopro-retro-formats · ROUND 033 · BUILDER` header. Show the output.
- `fw.py check` passes, and the full suite passes, including
  `tests/test_framework.py` and `tests/test_push_readiness.py`.
- CI is green at your final head.

## Required evidence

- Both `adopt.py` runs, with complete output.
- `python3 tools/fw.py status` and `python3 tools/fw.py check`.
- The `fw.py prompt` output above.
- `python -m unittest discover -t . -s tests -v`, with the count and skips.
- `python -m retroformats validate` and `python -m retroformats build --check`.
- The CI run URL at your final head.
- Each project-owned sentence changed (item 5), with its old and new text.

Your report (`docs/rounds/033-framework-3-1-0/builder.md`) has the Worker
card's sections. After the update, `fw.py report` should itself print the
closing line; say whether it did.
