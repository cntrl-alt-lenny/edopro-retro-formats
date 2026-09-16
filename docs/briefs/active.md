# Active brief

Status: **queued, not started**.

Identifier: **`015-2026-09-16-report-and-materialize-gates`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (014 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — topology, project invariants, and the
   evidence table for what you touch.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. [`docs/agents/reports.md`](../agents/reports.md) and
   [`docs/agents/roles/verifier.md`](../agents/roles/verifier.md) § Your inputs
   — how completion reports and the Verifier's delivery check are meant to
   work.

Then this brief in full. Do not read `docs/research/`; nothing here needs it.

---

## MODE: REGRESSION INVESTIGATION

## Goal

Two project mechanisms fail at exactly the moment they are needed. When this
round is done, both do what their own documentation says they do, each is
pinned by a test that fails on today's code, and nothing they are meant to
guard has become weaker.

## Why this is next

Both surfaced adjudicating round 14 (archived as
`docs/briefs/archive/014-2026-09-16-per-artwork-printing-dates.md`).

- **Defect 1 blocks the Verifier seat.** The Verifier's delivery check
  (`python3 tools/report.py delivery`) only accepts a Builder report whose
  recorded task matches the brief. It reads `<git-common-dir>/agent-inbox/builder-latest.md`.
  The Claude Code Stop hook (`.claude/hooks/save_agent_reply.py`) writes to
  that same file at the end of every session turn with assistant text, tagged
  with a session id instead of a task. Observed in round 14's inbox: the
  Verifier's own self-report was replaced ten seconds after it was written. A
  Builder that writes its report and then ends its turn normally can therefore
  leave its Verifier reporting "not delivered yet" indefinitely. `reports.md`
  and the hook's own docstring describe the hook as a *fallback for sessions
  that did not write a report*; the observed behaviour is not that.
- **Defect 2 blocks the next release-data round.** When committed pool files
  lag release data, `validate` emits `pool.materialization-drift` with the
  remedy "run: python -m retroformats materialize". `materialize` then refuses
  to run, citing that same finding among its blocking errors (exit 1). Round 14
  had to call the library function directly to get past it. Reproduced by
  Brain on a scratch copy of round 14's head with the two pools reverted.

Neither changes any historical data.

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Scope

- `.claude/hooks/save_agent_reply.py`, `tools/report.py` if the fix belongs
  there, and their tests (`tests/test_claude_adapter.py`,
  `tests/test_report.py`, `tests/test_report_delivery.py`, or a new test file).
- `retroformats/cli.py`'s `materialize` command, and a test for it.
- `docs/state.md` only to record a durable fact this round establishes, and
  `docs/agents/report-handoff.md` only if it becomes inaccurate.

## Non-goals

- **Do not edit anything under `docs/agents/` other than `report-handoff.md`.**
  Those are verbatim framework copies. If you conclude the framework's own
  mechanism is wrong, say so in your report; Brain relays it.
- Do not change any validator finding code, severity or condition in
  `retroformats/validate.py`.
- Do not touch `data/`, `formats/` or `dist/`, beyond scratch copies you
  create and discard to reproduce defect 2.
- Roadmap item 4b's incomplete far-alias enumeration is a separate, later
  brief. Leave it.

## Protected invariants

- **The delivery check must not get weaker.** It exists so a Verifier never
  reviews work the Builder did not deliver. Delivery still requires the named
  role's own report for the named task, recorded at the branch's exact head,
  with the branch strictly ahead of an ancestor base (`verifier.md` § Your
  inputs). A fix that lets a session-tagged or stale report count as delivery
  is a regression, not a fix.
- **A missing or stale report still means UNKNOWN** (`reports.md`).
- **The Stop hook stays non-blocking:** any error exits 0, and a session must
  always be able to end.
- **The report mechanism stays provider-neutral.** Roles are still derived
  from the checkout; no role, provider or task is asserted by the tool itself.
- **`materialize` must still refuse to derive from genuinely invalid data.**
  The gate exists (see its comment in `cli.py`) so malformed dates, broken
  references and unresolved coverage never reach a pool file. Only the
  question of whether drift in the very files `materialize` rewrites should
  block it is in scope.
- **`tools/report.py` is deliberately not byte-identical to the framework's
  copy** (`docs/state.md`). If you change it, record exactly what now differs
  there, so a later re-adoption merges instead of overwriting.
- Validator baseline 0 errors / 569 warnings; suite 1029 tests, OK, 25 skipped
  at the base. GOAT hash `0x28E9FC02` unchanged.

## Required investigation

Answer from the code and from reproduction, not from this brief:

1. For defect 1, establish under what exact conditions the hook replaces
   `<role>-latest.md`, and whether anything else reads that file or depends on
   the hook's current behaviour (Brain's `status` checks, the recovery tool,
   existing tests). Decide what the right behaviour is, with the invariants
   above, and say why. If the correct fix belongs in the shared framework
   mechanism rather than in this project's adapter, or needs both, say so. If
   the options are genuinely ambiguous and a wrong choice would be systemic,
   stop and present them.
2. For defect 2, establish which of the blocking error codes can be caused
   solely by stale committed pool content that `materialize` is about to
   rewrite, and which indicate data it must not derive from. Reproduce the
   refusal before changing anything.

Note a practical consequence: this project's hook runs from the checkout it is
in, so your own round's report goes through whichever hook version is in
`.worktrees/builder` when your session ends.

## Acceptance criteria

- A test that reproduces defect 1 through the real hook and the real delivery
  check, and fails on the base SHA.
- A test that reproduces defect 2 through the real `materialize` command, and
  fails on the base SHA.
- Both pass at your head. Every pre-existing test still passes unmodified,
  unless you show that the old assertion encoded the defect.
- A test showing `materialize` still refuses at least one kind of genuinely
  invalid data.
- A test showing a session-tagged report still does not count as delivery.
- Your own completion report is intact in `builder-latest.md` after your
  session ends, so the Verifier's delivery check passes without any manual
  step.

## Required evidence

Per `AGENTS.md`'s evidence table for agent tooling and `retroformats/` code:
`python -m unittest discover -t . -s tests -v`, `python -m retroformats
validate`, `python -m retroformats build --check`, each with real output and
exit status, on Python 3.10 or newer. For each new test, show its failing
output against the base code as well as its passing output.

## Git expectations

Work only in `.worktrees/builder/`. Branch `builder/report-and-materialize-gates`
from `origin/main`. Focused commits; push the branch; never push `main`; never
merge. After your final commit and push, write your report from inside
`.worktrees/builder/` with
`python3 tools/report.py write --task 015-2026-09-16-report-and-materialize-gates`
(use a Python 3.10+ interpreter), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus:

- For each defect: root cause in one paragraph, the options you considered,
  and why you chose yours.
- Whether you believe the shared framework's own copy of either mechanism has
  the same defect, and the evidence for that belief.
- Exactly what in `tools/report.py` now differs from the framework's copy, if
  anything.
