# 028-framework-3-0-0: Move to agentic-framework 3.0.0

Tier: 2
Mode: implementation (framework update)
Supersedes: none. Round 027 (Edison historical scripts, queued in
`docs/briefs/active.md`) was never started and is not superseded; Brain
re-issues it under `docs/rounds/` after this round merges.

## Goal

The project runs on agentic-framework 3.0.0, in exactly the setup it will
keep. No half-state is left for a later round:

- Every step of the 3.0.0 "What an adopter must do" list in the framework's
  `CHANGELOG.md` is done.
- `docs/agents/framework.json` pins 3.0.0. No `.framework` copy, no retired
  framework file and no 2.x-only document is left, apart from the
  `docs/briefs/` history the 3.0.0 steps say to keep.
- `AGENTS.md` is the single entry point. It declares `Merge rule:
  owner-approves`, points at `docs/agents/FRAMEWORK.md`, carries every project
  rule (including any rule that lives only in `CLAUDE.md`, the `.claude/`
  seat files or a document this round deletes), does not tie seats to
  `.worktrees/` folders, does not mention the Dev Hub, and is under 2,500
  words.
- `CLAUDE.md` is a pointer to `AGENTS.md`.
- `docs/state.md` is within its 1,000-word budget. History has moved to an
  archive document.
- The full test suite and `fw.py check` are green, with the output pasted.

## Context

**Tools.** Until this round lands, the project has no `tools/fw.py`. Run
the copy in a clone of the framework at tag `v3.0.0`, made in a temporary
folder outside this project and not next to it. That folder is called
`<framework>` below; `<checkout>` is your checkout of this project:

- `python3 <framework>/tools/fw.py --cwd <checkout> <command> ...`
- `python3 <framework>/tools/adopt.py <checkout> --update [--dry-run]`

Once the update is committed, `<checkout>/tools/fw.py` is the same file and
either copy may be used. `fw.py` and `adopt.py` run on Python 3.9 or newer.
This project's suite needs 3.10 or newer. On a machine whose `python3` is
older, run the suite with an explicit 3.10+ interpreter and say which one
you used.

**Seat names.** The Builder holds the Worker card. In every `fw.py` command
its role is `builder`, so `fw.py start` puts it on `builder/028-framework-3-0-0`
and its report is `docs/rounds/028-framework-3-0-0/builder.md`.

**Read:** `<framework>/CHANGELOG.md` (the 3.0.0 section),
`<framework>/framework/FRAMEWORK.md`, `<framework>/framework/roles/worker.md`,
this project's `AGENTS.md`, `CLAUDE.md` and `docs/state.md`, and each file in
the inventory below before you change it. **Not worth reading:**
`docs/research/`, `data/`, and `docs/briefs/archive/`, except to check
links.

**Brain's dry run, at `main` `eafcfda`** (`adopt.py . --update --dry-run`)
plans the following:

- It creates `FRAMEWORK.md`, `tools/fw.py`, `tests/test_framework.py`,
  `docs/rounds/README.md` and `.claude/agents/verifier.md`.
- It replaces the three role cards.
- It writes `.framework` copies beside `.claude/agents/brain.md`,
  `.claude/agents/worker.md` and `.claude/commands/status.md`.
- It removes seven unedited 2.x files.
- It keeps 14 more files because they were edited here or are still
  referenced. Each of those is covered in the inventory.
- It flags two links in `AGENTS.md`, to `kickoff.md` and `lifecycle.md`.
- It does not mention `tools/recover_agent_report.py`,
  `.claude/hooks/check_worker_checkout.sh`, the project's own documents in
  `docs/agents/`, or the project's tests of 2.x tooling.
- The dry run does not print the release's adopter steps. The real run does.

**Baseline at `main` `eafcfda`**, from Python 3.13 on macOS:
`python -m unittest discover -t . -s tests` gives `Ran 1067 tests`, `OK
(skipped=25)`. `fw.py check` finds 2 errors and 2 warnings: the state
budget, a Windows drive path in the state document's Dev Hub section, no
merge-rule line, and `AGENTS.md` at 2,826 words.

## Scope and non-goals

**May change:** `AGENTS.md`, `CLAUDE.md`, `docs/state.md`, a new archive
document for state history (suggested: `docs/archive/state-history.md`),
`docs/agents/**`, `docs/rounds/README.md`, `docs/archive/`, `.claude/**`,
agent tooling in `tools/`, the agent-tooling tests named in the inventory,
`.gitignore`, and the comments and docstrings (not the behaviour) of
`.githooks/pre-push` and `scripts/check_push_readiness.py`. May also change
`docs/briefs/README.md` (one history note) and
`docs/briefs/delivered/.gitkeep`.

**Must not change:**

- Product content: `data/`, `formats/`, `dist/`, `schemas/`,
  `retroformats/`, `scripts/` (other than the docstring above),
  `docs/research/`, product tests, and `.github/workflows/`.
- The behaviour of the push gate.
- `docs/briefs/active.md` (Brain retires it when it re-issues 027) and
  `docs/briefs/archive/` (history, left as written).
- Framework files, other than through `adopt.py` and the 3.0.0 steps. Do not
  hand-edit `docs/agents/FRAMEWORK.md`, `docs/agents/roles/*`,
  `tools/fw.py`, `tests/test_framework.py` or `docs/agents/framework.json`.
  Do not raise `settings.state_words`.

**No product clean-up**, even when you see some. List it under Open
questions instead.

**If the framework blocks the update** (a contradiction, a tool bug, or a
step that cannot be followed as written): stop. File an issue with the
framework repository's "Framework feedback" form. Report it. Do not work
around it.

## Leftover inventory

Brain believes every file below is left over from the 2.x framework. Decide
each one. The default is Brain's recommendation; where you do otherwise,
give your reason. Anything else you find that belongs to the 2.x framework
gets the same treatment and is added to your report's table.

Removing a regression test here is a named purpose of this brief, as
`AGENTS.md` requires. It applies only to the tests listed, and only because
the thing they test is retired.

| # | Path | Recommendation | Reason |
|---|---|---|---|
| 1 | `docs/agents/briefs.md`, `kickoff.md`, `lifecycle.md`; `tools/authority.py`, `neutrality.py`, `textblocks.py`; `tests/test_role_neutrality.py` | Removed by `adopt.py`; let it. | Unedited 2.x copies. 3.0.0 removes the wording scanners that `test_role_neutrality.py` tests. |
| 2 | `docs/agents/CONSTITUTION.md`, `adapters.md`, `evidence.md`, `git-and-isolation.md`, `reports.md`, `state.md`, `topologies.md`, `roles/README.md` | Delete, after removing the references `adopt.py` names and moving any project-specific content into `AGENTS.md`. | 2.x documents that 3.0.0 replaces with `FRAMEWORK.md` and the role cards. |
| 3 | `docs/agents/model-notes.md`, `push-gate.md`, `report-handoff.md` | Delete (the owner's instruction). Move only project-specific rules into `AGENTS.md`. | `push-gate.md`: a line or two on the pre-push gate goes into `AGENTS.md` § What is actually enforced. It runs `validate` and `build --check`, is opt-in per clone through `core.hooksPath`, can be bypassed with `--no-verify`, and is not a tool hook, for the reason given. `model-notes.md` is a dated log, not rules; git history keeps it. Move any standing rule it contains; if there is none, say so. `report-handoff.md` describes the retired report inbox. |
| 4 | `.claude/agents/brain.md`, `.claude/agents/worker.md`, `.claude/commands/status.md` | Replace each with its `.framework` copy, then delete the copy. | 3.0.0 adapter files only point. The project content in them: `model: sonnet` pins (tool configuration; the owner picks models per session, so drop them and record that); the `core.hooksPath` check (fold into `AGENTS.md`); an Ultracode note (tool-specific; drop); the checkout-guard hook (see 5). |
| 5 | `.claude/hooks/check_worker_checkout.sh` | Delete. | It refuses any session outside `.worktrees/builder` on a `builder/*` branch. That contradicts 3.0.0 seats working from any checkout. |
| 6 | `.claude/settings.json`, `.claude/hooks/run_python.sh`, `.claude/hooks/save_agent_reply.py` | Delete. | 3.0.0 retires the Stop hook, because seats commit their own reports. `settings.json` holds only that hook. |
| 7 | `tools/report.py`, `tools/recover_agent_report.py` | Delete. | Replaced by `fw.py report` and `fw.py delivery`. The `.git/agent-inbox/` handoff is gone. `report.py` carried a Windows rename-retry fix for a reader polling the inbox. Establish whether `fw.py report` has the same exposure, and state what you found and how. |
| 8 | `tests/test_report.py`, `test_report_delivery.py`, `test_report_recovery.py` | Delete, together with the tools they test. | Their subject is retired (7). |
| 9 | `tests/test_claude_adapter.py` | Delete the Stop-hook, shim and checkout-guard tests along with their subjects. Keep the pre-push executable-bit test (`TrackedHookModeTest`), moved into `tests/test_push_readiness.py`. | The push gate stays, so its guard stays. |
| 10 | `tests/test_state_doc_is_durable.py` | Keep only the check that `fw.py check` lacks, which is the live-queue phrases in `docs/state.md`. Drop the rest, or delete the file and give a reason. | It requires `docs/briefs/active.md` to exist, which 3.0.0 retires, and it scans `docs/agents/`. `tests/test_framework.py` now covers the budget and stored commit ids. |
| 11 | `tests/test_push_readiness.py` | Keep. Make its `.claude/settings.json` test pass when the file is absent, rather than skip. | Outside the engine tests, a skip is a finding in this project. |
| 12 | `.githooks/pre-push`, `scripts/check_push_readiness.py` | Keep. Repoint their `docs/agents/push-gate.md` references to `AGENTS.md`. | This is the project's push gate, not a framework file. |
| 13 | `.gitignore` | Keep `.worktrees/`. Drop `.claude/worktrees/` and the comment's link to `git-and-isolation.md`. | Linked checkouts nested in the project stay optional, and the owner prefers one folder. The other entry is a pre-adoption location. |
| 14 | `docs/archive/agents-pre-framework/` | Delete, along with the pointer to it in `AGENTS.md`. | Pre-framework history, superseded twice. It links to files this round deletes. Git history keeps it. |
| 15 | `docs/briefs/README.md`; `docs/briefs/delivered/.gitkeep` | README: keep as history, with one line at the top saying new rounds live in `docs/rounds/`. `.gitkeep`: delete. | 3.0.0 step 6. The "delivered" stage no longer exists. |
| 16 | `docs/briefs/active.md` | Do not touch. | Brain retires it when it re-issues 027. |
| 17 | `.claude/commands/atlas.md`, `report.md` | Keep. Confirm they reference nothing retired. | Project conveniences, not framework files. |
| 18 | `CLAUDE.md` | Replace with the framework's pointer (`@AGENTS.md` plus its one sentence). Move its project hint ("to answer a question, `docs/state.md` plus the relevant document") into `AGENTS.md` if you judge it useful. | 3.0.0 step 4. |

## AGENTS.md requirements

**It keeps, in substance:**

- the non-negotiable project invariants (epistemics, and data and mechanism)
- the evidence table, with its agent-tooling and coordination rows updated
  to the files that exist after this round
- "for historical claims, the suite structurally cannot fail"
- what review checks here
- the project-specific working discipline, for example "evidence in a
  record is added to, never replaced"
- the project's two additions to the owner-reserved actions
- why this project has a standing Verifier
- the Builder name and the `builder` role name
- `HISTORICAL RESEARCH` mapped onto the 3.0.0 `research` mode

**It gains:**

- the `Merge rule: owner-approves` line. The 2026-09-16 owner decision is
  exactly this rule, so the long authority paragraph shrinks to it.
- a pointer to `docs/agents/FRAMEWORK.md` and the role cards
- a statement that seats work from any checkout and `fw.py start` places
  them, and that `.worktrees/<role>/` inside this folder is an optional
  convenience, never required
- 3.0.0 Verifier behaviour: the Verifier commits only its report, on its own
  branch
- that framework feedback goes to the framework repository's "Framework
  feedback" issue form

**It loses:**

- text that restates the framework: the authority model, the round
  lifecycle, brief identifiers, `report.py`, checkout mechanics, framework
  precedence
- the Claude executor-guard row of the enforcement table
- links to deleted files
- any mention of the Dev Hub

Keep the dated caveat on the branch-protection line.

## docs/state.md requirements

**Keep:** the rulings; the canonical-formats table; the GOAT anchor; Edison's
intentional `partial`; parked Tokyo Dome (condense it, but keep the pool
digest under `## Historical anchors`); the frozen erratum v2; the standing
role-chats decision; the operating policy's standing rules; the sequencing
judgements; the owner preferences; and the fact that the engine builds on
Linux and macOS only, so Windows engine evidence comes from CI.

**Replace:** the live-state table's `docs/briefs/active.md` rows, with
`fw.py status` and `docs/rounds/`.

**Remove:**

- the Dev Hub section (it also causes the Windows drive path error). Say
  instead that framework feedback goes to GitHub issues.
- the merge-approval section, reduced to a pointer to the `AGENTS.md` merge
  rule
- 2.x-mechanism history: the report handoff, the Stop hook, transcript
  recovery, the `report.py` divergence, the adapter defect classes, and the
  account of the adoption itself. Move these verbatim to the archive
  document, or drop them as obsolete and say so.

**In the report:** the framework requires every sentence added and removed
to be listed. For sections moved verbatim to the archive, list them by
heading and say they moved verbatim, so a diff can confirm it. List every
other sentence you added, removed or reworded.

## Invariants

- `AGENTS.md` § Non-negotiable project invariants holds throughout. No data,
  `dist/`, validation rule or GOAT anchor moves.
- No regression test is removed or weakened except those named in the
  inventory, for the reason given there (`AGENTS.md`).
- Framework files change only through `adopt.py` and the 3.0.0 steps (the
  owner, and FRAMEWORK.md rule 14).
- Owner preferences in `docs/state.md` still hold: one project folder, and
  organised copy-paste blocks.

## Acceptance criteria

1. `adopt.py <checkout> --update` was run without `--dry-run`, from a clone
   at `v3.0.0`. Its full output is in the report.
2. At the final head, `adopt.py <checkout> --update --dry-run` plans no
   `create`, `replace`, `beside` or `remove`, no "delete it" keeps, and no
   link fixes.
3. At the final head, `fw.py status` shows 3.0.0 pinned and no locally
   edited framework files. Its only legacy note is `docs/briefs/active.md`.
4. `fw.py check` finds 0 errors and 0 warnings.
5. The full suite is green. Its only skips are the engine tests. The test
   count is compared with the baseline, and every removed test is accounted
   for by the inventory.
6. `validate` and `build --check` give the same error and warning counts as
   at `main`. `git diff --stat` against `main` touches no path outside the
   scope.
7. Every row of the inventory is decided, with a reason.
8. The leftover grep below finds nothing.
9. `AGENTS.md` is under 2,500 words, and `docs/state.md` is at most 1,000.
10. The report has a table accounting for every project rule that was in
    `AGENTS.md`, `CLAUDE.md`, the `.claude/` seat files and the deleted
    `docs/agents/` documents. Each rule is either in the new `AGENTS.md` or
    `docs/state.md`, or listed as dropped, with a reason: covered by the
    framework, or obsolete.
11. CI at the pushed head is reported for both jobs.

## Required evidence

Paste each command with its real output and exit status, at a stated
commit. Use a 3.10+ interpreter for `python`.

```
python3 <framework>/tools/adopt.py <checkout> --update
python3 <framework>/tools/adopt.py <checkout> --update --dry-run
python3 <framework>/tools/fw.py --cwd <checkout> status
python3 <framework>/tools/fw.py --cwd <checkout> check
python -m unittest discover -t . -s tests -v
python -m retroformats validate
python -m retroformats build --check
git diff --stat origin/main...HEAD
git grep -nE "tools/(report|recover_agent_report|authority|neutrality|textblocks)\.py|docs/agents/(CONSTITUTION|adapters|briefs|evidence|git-and-isolation|kickoff|lifecycle|model-notes|push-gate|report-handoff|reports|state|topologies)\.md|roles/README|agent-inbox|save_agent_reply|check_worker_checkout|run_python\.sh|agents-pre-framework|Dev Hub" -- . ":!docs/briefs/archive" ":!docs/briefs/active.md" ":!docs/rounds/028-framework-3-0-0" ":!docs/archive/state-history.md"
```

Also give word counts for `AGENTS.md` and `docs/state.md`, and the CI run
for the pushed head.
