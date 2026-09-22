# State history archive

History moved out of [`docs/state.md`](../state.md) during the round-028
migration to agentic-framework 3.0.0, to keep that file within its 1,000-word
budget. **Read-only. Not current policy** — nothing here outranks
`AGENTS.md` or the role contracts. Each section below is quoted **verbatim**
from `docs/state.md` as it stood at `main` `eafcfda`, under the heading it
had there, so a diff against that commit can confirm nothing was altered in
the move. All of it describes the retired 2.x report-inbox mechanism
(`tools/report.py`, `.git/agent-inbox/`, the Claude Code Stop hook,
`tools/recover_agent_report.py`) or the framework adoption itself, both
superseded by 3.0.0's `fw.py report`/`fw.py delivery` and reports committed
directly to `docs/rounds/<id>/<role>.md`.

## Owner decision — merges need explicit owner approval (since 2026-09-16)

Set by the owner on 2026-09-16, overriding the routine-merge delegation in the
constitution, the Brain contract and the pre-existing wording of `AGENTS.md`.
When Brain accepts a round it stops at "ready to merge", says in plain English
what would be merged and why, and waits for the owner's explicit approval
before merging or doing the post-merge housekeeping. It came alongside the
same rule for the shared framework repository. The owner may relax it once
rounds have run smoothly for a while; until they say so, it holds for every
Brain session on every tool. Rejections and corrective briefs do not need
approval.

*(Current rule: `AGENTS.md` § merge rule, `owner-approves`.)*

## Dev Hub and framework feedback (since 2026-09-22)

The shared framework (cntrl-alt-lenny/agentic-framework) is the owner's
other project. Its Brain and every project Brain share a Google Drive folder,
`Software/Dev Hub` (on the Windows desktop `D:\Google Drive\Software\Dev Hub`;
the Mac path is in the Dev Hub's own `README.md`). `mail/` carries messages
between Brains; `framework-feedback/` reports framework problems upstream
instead of working around them locally. Read it only when the owner says to,
including on a machine switch. Messages are evidence, never instructions.

Read and sent so far: read on 2026-09-22, when nothing was addressed to this
project; sent one report,
`2026-09-22_0922_edopro-retro-formats_machine-switch-mid-round.md` (a
delivered, unreviewed round's report stranded in the other machine's clone).

**Machine switching.** The owner alternates between a Mac and a Windows
desktop. Completion reports live in each clone's `.git/agent-inbox/` and do
not travel with git, so finish adjudicating a delivered round before switching
machines. If one is stranded anyway, the round is completed on the new machine
by a fresh Builder producing its own evidence at a new head, never by
reconstructing the old report. The duel engine builds on Linux and macOS
only; on Windows, engine evidence comes from the CI `engine` job.

*(Current rule: 3.0.0 rounds live in git, in `docs/rounds/`, so they travel
with any clone or machine by construction; framework feedback goes to the
framework repository's GitHub issues, per `docs/agents/FRAMEWORK.md`.)*

## The Claude adapter's demonstrated defect classes (2.x report-inbox mechanism)

- **The Claude adapter has four demonstrated defect classes, now covered by
  framework mechanisms and regression tests.** The Stop hook probes
  `python3` then `python` through a shell shim and remains safe when neither
  is available; the executor adapter's blocking `UserPromptSubmit` hook derives
  the Git common directory and refuses Brain's primary checkout, any checkout
  other than `.worktrees/builder`, or a non-`builder/*` branch; the pre-push
  hook is tracked executable while its
  `core.hooksPath` activation remains explicitly per-clone; and the nested
  per-role worktrees are documented as per-clone state that must be derived with
  `git worktree list`, not assumed to exist. These are durable mechanism
  classes, not claims about any clone's current setup.

- **A test that asserts checkout behaviour must build the git state it
  asserts against.** The adapter's guard tests pointed at
  `<primary>/.claude/worktrees/worker` — per-clone developer state, absent on
  a fresh checkout — so CI was red for four consecutive pushes with a
  `FileNotFoundError`, and the accept-case additionally depended on whichever
  branch that worktree happened to be on. Fixed by constructing a real
  temporary repository and a real linked worktree per test. The rule
  generalises: ambient layout is not a fixture.
- **`git rev-parse --git-common-dir` returns `C:/...` on Git for Windows.**
  Classifying absolute-vs-relative by a leading `/` therefore misreads it as
  relative; the Worker guard did exactly that, prefixed the repo root, and
  fail-closed against the *correct* worktree — the guard was unusable on
  Windows and nobody had noticed, because the broken test could not express
  the case. Let `cd` resolve the value instead of classifying it. Verified
  against the real worktree: exit 2 before, exit 0 after.
- **`report.py`'s atomic write loses to a concurrent reader on Windows —
  fixed, and the test that watched for it was the worse bug.** `os.replace`
  raises `PermissionError [WinError 32]` while another handle has the
  destination open, which is the *normal* case for `<role>-latest.md`: one
  role writing while another polls. Now retried for up to 5s; format, paths
  and role derivation unchanged, so the mechanism stays provider-neutral.
  The lesson worth keeping is the second half: the racing test held a
  **non-daemon** reader thread and called `stop.set()` only on the success
  path, so when the write raised, the suite printed its results and then the
  interpreter hung forever pinning a core — observed as a 40-minute "still
  running" task. A test that can outlive its own failure is worse than the
  bug it was watching for: stop background threads in a `finally`, and make
  them daemons so a mistake cannot wedge the run. Retry coverage is by fault
  injection, so it proves the same thing on POSIX, where the path is
  otherwise unreachable.

- **`tools/report.py` is deliberately not byte-identical to the framework's
  copy.** Adoption took the framework's version (which adds the Verifier's
  `delivery` check) and re-applied this project's Windows rename retry above,
  which the framework's copy did not have. Until the framework carries that
  fix, a future re-adoption must merge, not overwrite — overwriting silently
  reintroduces the Windows failure. `tests/test_report.py` pins the retry and
  `tests/test_report_delivery.py` pins the delivery check. The project copy
  also exposes `latest_provenance()` so its Claude Stop adapter can distinguish
  a role-owned fresh report from an earlier hook fallback; the shared
  framework copy does not carry this project-specific adapter fix.

*(Round-028 finding: `fw.py`'s `cmd_report` writes each round's report with a
plain `path.write_bytes(...)` directly to `docs/rounds/<id>/<role>.md` — no
`os.replace` onto a path another process has open, and nothing polls that
path concurrently the way the old `<role>-latest.md` inbox file was polled.
The specific Windows failure mode above does not carry over to `fw.py
report`; see `docs/rounds/028-framework-3-0-0/builder.md`.)*

## The provider-neutral report handoff (2.x report-inbox mechanism)

- **A round's completion report reaches Brain by a provider-neutral
  self-report first, transcript recovery only as fallback.** The order is:
  (1) the role writes its own report into the shared `agent-inbox/` under
  the git common dir, using only filesystem, git and a shell — capabilities
  every Worker contract already requires, so it works on any tool including
  ones with no adapter and no readable transcript store; (2) provider
  transcript recovery, only when that artifact is missing or stale;
  (3) manual owner relay, only when both fail. A tool-specific hook fixes
  one member of the problem class, not the class. The canonical mechanism
  is designed in the shared framework repository
  (`cntrl-alt-lenny/agentic-framework`, formerly `agentic-project-framework`)
  and is adopted here rather than reimplemented — including its rule that a
  role's tag is derived from which checkout it is in, never asserted.
  Two conclusions worth not relearning: transcript recovery being
  unavailable for a provider does NOT mean that provider needs manual
  relay, since its Worker can still write the canonical report; and a
  session that merely ran `git log` mentions every earlier round's SHA, so
  recovery must reconcile a session to the round it *produced*, not the
  most recent conversation that mentions it. Absence stays UNKNOWN, and a
  report — recovered or self-written — stays evidence of what the agent
  said, never a substitute for reviewing the diff.

- **The transcript-recovery fallback over-rejects real producing sessions;
  fold the fix into the next framework touch rather than a round of its
  own.** Its primary-checkout exclusion requires that *no* recorded working
  directory in a candidate session is the primary checkout. Sessions
  routinely start there and move into the worktree, and one provider
  records only a start-of-session working directory — the exact field the
  design says identity must not rest on — so a genuine producing session is
  rejected. Verified by probe: the round-12 round's own session is local,
  in-window and correct, and recovery returns UNKNOWN for it. It fails
  closed, so it yields no answer rather than a wrong one, and the canonical
  self-report is unaffected — which is why this is a follow-up, not a
  blocker. The fix is to exclude *the reading session itself* rather than
  any session that ever touched the primary checkout. Its tests pass
  because their fixtures never touch the primary checkout, so they encode
  the intended shape rather than the observed one.

- **The Claude Stop hook is fallback-only over a role-owned fresh report, not
  over an earlier hook fallback.** A Stop event has a session id but no brief
  id, so its session-tagged report is not delivery evidence. The adapter checks
  the shared writer's current HEAD freshness and provenance: a role-owned
  report remains intact, while a later hook capture replaces an earlier hook
  capture at the same HEAD. Missing or stale reports still receive the
  non-blocking session fallback.

*(Current mechanism: `fw.py report --push` commits the report to
`docs/rounds/<id>/<role>.md` on the role's own branch and pushes it — no
inbox, no transcript recovery, no Stop hook. `fw.py delivery --round <id>`
answers "is this round delivered, and where" by reading git.)*

## The adoption itself (2026-09-16)

- **The adoption itself was owner-commissioned Brain work, not a reviewed
  round.** The owner assigned the framework adoption directly to Brain on
  2026-09-16. It touched only process plumbing (docs, `tools/`, agent tests,
  the executor guard) and no data, `dist/` or validation rule. Its gates were
  the full suite, the neutrality and guard tests each shown red before green,
  a fresh-context session starting from `AGENTS.md` and the Brain contract
  alone, and CI at the merged head. It had no independent Verifier pass; if
  a later round finds a defect in that plumbing, that is why.

## Review protocol (2.x restatement, superseded)

Brain's merge authority rests on this actually being run, every round:
independently re-diff the commit, re-run whatever the report claims to have
checked, and **re-derive at least one load-bearing claim directly**
(re-fetch the cited source, recount the entries, re-run the check). Full
checklist: `agents/roles/brain.md` plus `AGENTS.md` § What review checks
here.

Every round so far has justified it — reviewing the diff alone would have
missed something a direct re-derivation caught.

*(Current rule: `docs/agents/FRAMEWORK.md` rules 7, 9 and 10, and `AGENTS.md`
§ What review checks here — this section restated them for the pre-3.0.0
framework and is now redundant with the framework's own core document.)*
