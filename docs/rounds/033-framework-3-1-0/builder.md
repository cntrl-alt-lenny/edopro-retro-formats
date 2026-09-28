# Builder report — 033-framework-3-1-0

The one personal path in `adopt.py`'s output (its first line, the project folder) is shown as `<project>`; nothing else is altered.

Work head: `58bc135` (two commits on `origin/main` `36a5c9c`: `e9b1a93` the
`adopt.py` update, `58bc135` the project wording). Framework clone: tag
`v3.1.0` (tag object `6359ebf`, commit `eca1306`), in a temporary directory
outside this project.

## Verified

- Changelog step 1, dry run — `python3 tools/adopt.py <project> --update --dry-run` (from the `v3.1.0` clone) → exit 0. Complete output:

```text
update: <project> -> agentic-framework 3.1.0 (from 3.0.0)
  replace docs/agents/FRAMEWORK.md
  replace docs/agents/roles/brain.md
  replace docs/agents/roles/worker.md
  replace docs/agents/roles/verifier.md
  replace tools/fw.py
  replace tests/test_framework.py
  same    .claude/agents/brain.md
  same    .claude/agents/verifier.md
  same    .claude/agents/worker.md
  same    .claude/commands/status.md
  keep    AGENTS.md  (project-owned)
  keep    docs/state.md  (project-owned)
  keep    docs/rounds/README.md  (project-owned)
  keep    .gitattributes  (project-owned)
  keep    .githooks/pre-push  (project-owned)
  keep    CLAUDE.md  (project-owned)
  other   .claude/commands/atlas.md  (the project's own, beside files the framework installs)
  other   .claude/commands/report.md  (the project's own, beside files the framework installs)
  record  docs/agents/framework.json

If an 'other' file does the job of a framework file beside it (two seat files for one
seat, say), delete one of the two. An update never re-creates a file deleted there.

What each release asks of this project:

--- 3.1.0 ---
Run this as one Tier 1 round (Worker, then Brain re-derives), with no other
round in flight.

1. From a clone of the framework at `v3.1.0`, run
   `python3 tools/adopt.py <project> --update --dry-run`, then without
   `--dry-run`. Expect `replace` lines for framework files. A `gone` line is a
   file the project deleted, and stays deleted. For each `other` line in
   `.claude/agents/`, if it is a second seat file for one seat, delete one of
   the two.
2. If the project's `AGENTS.md` has its own prompt-header rule (from issue
   #26), delete it: `FRAMEWORK.md` now carries it.
3. Optionally, if the project has a fast check that reports can break (a
   link test, say), name it in `docs/agents/framework.json` under
   `settings`, as `"report_check": "<command>"`.
4. Run `python3 tools/fw.py status` and check that each round in flight is
   shown seat by seat and that the last line starts with `next:`.

dry run: nothing written
```

- Changelog step 1, real run — `python3 tools/adopt.py <project> --update` → exit 0. Complete output:

```text
update: <project> -> agentic-framework 3.1.0 (from 3.0.0)
  replace docs/agents/FRAMEWORK.md
  replace docs/agents/roles/brain.md
  replace docs/agents/roles/worker.md
  replace docs/agents/roles/verifier.md
  replace tools/fw.py
  replace tests/test_framework.py
  same    .claude/agents/brain.md
  same    .claude/agents/verifier.md
  same    .claude/agents/worker.md
  same    .claude/commands/status.md
  keep    AGENTS.md  (project-owned)
  keep    docs/state.md  (project-owned)
  keep    docs/rounds/README.md  (project-owned)
  keep    .gitattributes  (project-owned)
  keep    .githooks/pre-push  (project-owned)
  keep    CLAUDE.md  (project-owned)
  other   .claude/commands/atlas.md  (the project's own, beside files the framework installs)
  other   .claude/commands/report.md  (the project's own, beside files the framework installs)
  record  docs/agents/framework.json

If an 'other' file does the job of a framework file beside it (two seat files for one
seat, say), delete one of the two. An update never re-creates a file deleted there.

What each release asks of this project:

--- 3.1.0 ---
Run this as one Tier 1 round (Worker, then Brain re-derives), with no other
round in flight.

1. From a clone of the framework at `v3.1.0`, run
   `python3 tools/adopt.py <project> --update --dry-run`, then without
   `--dry-run`. Expect `replace` lines for framework files. A `gone` line is a
   file the project deleted, and stays deleted. For each `other` line in
   `.claude/agents/`, if it is a second seat file for one seat, delete one of
   the two.
2. If the project's `AGENTS.md` has its own prompt-header rule (from issue
   #26), delete it: `FRAMEWORK.md` now carries it.
3. Optionally, if the project has a fast check that reports can break (a
   link test, say), name it in `docs/agents/framework.json` under
   `settings`, as `"report_check": "<command>"`.
4. Run `python3 tools/fw.py status` and check that each round in flight is
   shown seat by seat and that the last line starts with `next:`.
```

  No `gone` lines. The two `other` lines are `.claude/commands/atlas.md` and
  `.claude/commands/report.md`, the project's own `/atlas` and `/report`
  commands; neither is in `.claude/agents/` and neither duplicates a
  framework file, so nothing was deleted. No `.framework` copy was written
  (`find . -name '*.framework'` outside `.worktrees/` → nothing), so no
  framework file here was locally edited. `git diff --stat` after the run
  touched exactly the six `replace` files plus `docs/agents/framework.json`
  (release `3.0.0` → `3.1.0` and the six new hashes). `.gitignore` already
  ignores `.worktrees/`.

- Changelog step 2 — `grep -niE 'header|· ROUND|DONE|STOPPED' AGENTS.md` →
  only line 66 ("Round 13 is the…") and line 207 ("Round 18 needed…"),
  neither a rule. `AGENTS.md` has no prompt-header rule; nothing deleted.

- Changelog step 3 — no project check a report file can break. The only
  tests reading `docs/rounds/` are `tests/test_framework.py` (the framework's
  own, which `fw.py report` already covers) and
  `tests/test_state_doc_is_durable.py` (reads `docs/state.md` only). No
  `report_check` added.

- Changelog step 4 and acceptance — `python3 tools/fw.py status` at `58bc135`, pushed → exit 0:

```text
Framework
  pinned to agentic-framework 3.1.0 (https://github.com/cntrl-alt-lenny/agentic-framework)
  up to date with the latest release (3.1.0)
Merge rule
  owner-approves
Rounds
  in flight: 033-framework-3-1-0 (Tier 1)
    builder: started on origin/builder/033-framework-3-1-0, no report yet
  5 round(s) merged under docs/rounds/, latest by name: 032-derived-scripts-licence
This machine
  on builder/033-framework-3-1-0; no uncommitted changes
  safe to leave this machine: yes
Checks
  all project checks pass
Command form on this machine: python3 tools/fw.py <command>
next: wait for the Builder of round 033-framework-3-1-0 to finish; if its chat has stopped, send it the same prompt again as message 2
```

  The round in flight is shown seat by seat (Tier 1, so one seat: builder),
  and the last line starts with `next:`.

- `python3 tools/fw.py check` → exit 0: `0 error(s), 0 warning(s)`.
  `docs/state.md` is 998 words by `wc -w` against `state_words: 1000`.

- `python3 tools/fw.py prompt --round 033-framework-3-1-0 --role builder` → exit 0. First line is the header:

```text
edopro-retro-formats · ROUND 033 · BUILDER

You are the Builder for edopro-retro-formats, round 033-framework-3-1-0. Work inside this project's folder on this machine (clone https://github.com/cntrl-alt-lenny/edopro-retro-formats if it is not here): from its main checkout run git worktree add --detach .worktrees/builder-033 origin/main and work in that folder, never in a copy beside the project. In a cloud workspace, work in the clone it gives you.

In that folder, first run python3 tools/fw.py start --role builder --round 033-framework-3-1-0 (use py -3 or python if python3 is not found) and stop if it fails. Then read AGENTS.md, docs/agents/FRAMEWORK.md, docs/agents/roles/worker.md and docs/rounds/033-framework-3-1-0/brief.md, and carry out the brief.

Finish, even if you stop early, by writing docs/rounds/033-framework-3-1-0/builder.md and running python3 tools/fw.py report --role builder --round 033-framework-3-1-0 --push. End your final reply with exactly one line: edopro-retro-formats · ROUND 033 · BUILDER · DONE — report pushed at <commit>, or STOPPED or BLOCKED with the reason.
```

- Full suite — `python3.13 -m unittest discover -t . -s tests -v` → exit 0:
  `Ran 1081 tests in 120.643s` / `OK (skipped=59)`. All 59 skips carry the
  reason `ocgcore + pinned checkouts not available` (the expected engine
  skips); no other skips. Includes `tests/test_framework.py` and
  `tests/test_push_readiness.py`.

- `python3.13 -m retroformats validate` → exit 0:
  `validate: 3 formats, 3 banlists, 3 pools, 3 rule profiles, 296 errata -> 0 errors, 563 warnings`
  (matches the brief's 0 / 563; no new warning codes).

- `python3.13 -m retroformats build --check` → exit 0 (built the three
  lflists; no drift). `git diff --stat origin/main -- dist data formats` →
  empty, so the GOAT list and every banlist entry set are unchanged; the
  suite's `test_goat_output_matches_the_pinned_pre_migration_hash`,
  `test_goat_is_byte_identical_and_matches_the_pinned_hash` and
  `test_29_goat_output_remains_byte_identical_and_hash_pinned` pass
  (`0x28E9FC02`).

- CI at work head `58bc135` — https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36445967920
  → `success`: `engine` success, `check (3.13)` success, `check (3.10)` success.

## Not verified

- CI at the report commit that `fw.py report --push` creates on top of
  `58bc135` (it changes only this file); its run did not exist when this was
  written. Brain should check CI at the literal final head.
- The engine job's `executed=… skipped=…` line was not read; only the job's
  conclusion. Engine tests were not run locally (no engine files changed).
- Whether `fw.py report` prints the closing line: recorded in my final
  message, not here, since it runs after this file is written.

## Changed

- `docs/agents/FRAMEWORK.md`, `docs/agents/roles/{brain,worker,verifier}.md`,
  `tools/fw.py`, `tests/test_framework.py` — replaced by `adopt.py` with the
  3.1.0 copies; not edited by hand.
- `docs/agents/framework.json` — written by `adopt.py`: release 3.1.0 and
  new hashes. `settings` unchanged.
- `AGENTS.md` § Topology — one sentence:
  - Old: "Linked worktrees nested under `.worktrees/<role>/` inside this one project folder (`git worktree add --detach .worktrees/<role> origin/main`) are this project's usual convenience — never required, and `.worktrees/` is git-ignored, per-clone state (check `git worktree list`, don't assume it exists)."
  - New: "Linked worktrees nested under `.worktrees/<role>-<number>/` inside this one project folder (the seat prompt from `fw.py prompt` gives the command) are this project's usual convenience — never required, and `.worktrees/` is git-ignored, per-clone state (check `git worktree list`, don't assume it exists)."
- `docs/state.md` "Owner preferences" — one sentence:
  - Removed: "**One project folder** — no siblings; per-role worktrees nest under `.worktrees/` (`AGENTS.md` § Topology)."
  - Added: "**One project folder** — no siblings; per-seat worktrees nest under `.worktrees/<role>-<number>` (`AGENTS.md` § Topology)."

No project sentence says framework updates are always Tier 2
(`grep -niE 'tier|update|upgrade|adopt' AGENTS.md docs/state.md` → only
unrelated hits: evidence "tier C", "Tier review depth proportionally", "An
unreviewed second run… parked, not adopted"), so nothing else changed.

## Open questions

- `.gitignore`'s comment on `.worktrees/` points to "AGENTS.md § Checkouts",
  a section that does not exist (it is § Topology). Out of this brief's
  scope; left as is.
- The seat prompt's worktree number is the round number (`builder-033`), so
  I wrote `<role>-<number>` as the changelog does rather than naming it.
