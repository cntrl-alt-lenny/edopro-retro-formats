# Active brief

Status: **complete** — landed as `525566a`, reviewed and merged 2026-09-01.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on completion move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (zero-padded, check the archive
for the last-used number) and replace it with the next one, or leave a
one-line "no brief queued" placeholder. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — coordination rules and the
   non-negotiable epistemic rules. They outrank convenience.
2. [`docs/agents/role-contracts.md`](../agents/role-contracts.md) — the
   Worker contract: your mode's rules, the ground rules, and the
   completion-report schema you must report back in.

Then this brief in full. Read only the further docs this brief scopes as
relevant — don't ingest `docs/research/` wholesale.

---

## MODE: IMPLEMENTATION

## Goal

Make a finished round's completion report reach Brain **whatever tool ran
the round**, by adopting the provider-neutral mechanism designed in the
sibling `agentic-project-framework` repository — not by inventing a second
protocol here.

Round 11 fixed this repository's Claude Code adapter, which helps only
when the Worker *is* Claude Code. Most rounds here deliberately are not.

**Scope discipline:** framework work only. No roadmap or canonical-data
work in this round.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

---

## The architecture — get this order right

1. **Canonical, provider-neutral self-report.** The role writes its own
   completion report into `<git-common-dir>/agent-inbox/` before finishing,
   using only filesystem, git and a shell — capabilities every Worker
   contract here already requires. This is the primary mechanism.
2. **Provider transcript recovery — fallback only**, when that artifact is
   missing or stale.
3. **Manual owner relay — only when both fail.**

An earlier Brain prototype had this backwards, treating transcript
recovery as primary. It is not. A transcript scraper depends on a
provider's internal storage surviving its next release; a role writing its
own file does not, and works on a tool that does not exist yet because it
never asks what tool is running.

## Adopt, do not re-invent

The mechanism already exists in
`/Users/leo/Dev/agentic-project-framework`, **PR #2**
(`worker/cross-provider-report-relay`, "Add a provider-neutral completion-report
mechanism"). Read `framework/reports.md`, `tools/report.py`,
`framework/git-and-isolation.md` and
`adapters/claude-code/hooks/save_agent_reply.py` on that branch before
writing anything here.

Reuse its schema and semantics faithfully:

- Inbox at `<git-common-dir>/agent-inbox/`, resolved via
  `git rev-parse --git-common-dir` so it is identical from any worktree.
- `<role>-latest.md` plus an append-only `<role>-log.md`.
- Role tag **derived from which checkout you are in**, never passed as an
  argument — that repository asserts the parameter's absence with a test.
- Atomic write (temp file + `os.replace`), so a reader never sees a torn
  report.
- Header stamping task, exact HEAD SHA at write time, timestamp, source.
- A `status` command comparing recorded SHA against current HEAD:
  fresh / stale / absent as exit codes, so staleness is a command rather
  than a field a reader parses by hand.
- Missing or stale means **UNKNOWN** — never "the round did nothing".

**Do not fork it.** If this repository needs something that repository's
version does not do, say so explicitly in your report so it can go back
upstream, rather than quietly diverging.

Two things you must decide and state rather than assume:

- **PR #2 is open, not merged.** Its schema could still move. Say how you
  handled that — vendored at a named commit, referenced, or reimplemented
  to the same contract — and what would need redoing if it changes.
- **Role-tag naming.** That framework calls the primary checkout
  `coordinator`; this repository's existing hook calls it `brain`, and its
  linked worktree `worker`. Converging on the framework's derivation may
  rename this repository's own inbox files. Pick one, state the reasoning,
  and make the existing Claude adapter agree with whatever you pick — two
  naming schemes writing to one directory is the failure this round exists
  to prevent.

## Converge the Claude adapter

`.claude/hooks/save_agent_reply.py` must stop being an independent
implementation. Per PR #2's own convergence step, the Stop hook should
extract only the thing that tool alone can provide — the transcript — and
hand the text to the shared writer. One writer, one schema, one place a
regression shows up.

## Make it a contract requirement

Writing the report is a Worker MUST, not a convenience: add it to
`docs/agents/role-contracts.md`'s Worker contract and to the
completion-report schema, so every future brief inherits it. It is
unenforceable against a session that ignores it — say so plainly rather
than implying otherwise; that is true of every MUST in these contracts.

## Transcript recovery — keep it, demote it

Brain's working prototype is at
`<git-common-dir>/agent-inbox/recover_agent_report.py`, with machine-local
provider roots beside it in `providers.local.json`. Both are untracked
runtime state. Promote the *mechanism*; keep every host-specific path out
of tracked files.

It is proven against real local sessions for **Claude Code** (per-session
JSONL transcripts carrying `cwd`, `gitBranch`, `sessionId`, `timestamp`)
and **Codex** (JSONL rollouts with a purpose-built
`task_complete.last_agent_message`).

**The round-identification rule is the part that matters.** A first
version returned round 11's session for a round 10 query, because round 11
had run `git log` and so mentioned round 10's branch and SHA. Mentioning a
round is not producing it. The current discriminator is a bounded time
anchor — the producing session's store is still being written shortly
after that round's own commit. Test that rule; do not inherit its 900-second
bound without justifying it. Two failure modes must be covered:

- Brain's own live session matches its own commits and must never be
  returned as a Worker report.
- A round whose Worker ran off this machine must return UNKNOWN. Round 10
  (`f355d79`, `worker/search-verification-interval`) is a real
  reproducible instance.

## Antigravity — correct the conclusion, don't repeat it

An earlier Brain conclusion said Antigravity "requires manual relay". That
conflated two different things and is wrong as stated. The correct split:

- **Transcript recovery is unavailable for it** on evidence: conversation
  content lives in undocumented binary blob columns
  (`steps.step_payload` / `metadata` / `render_info`) of a per-conversation
  SQLite database. That is the fragile opaque-store dependency this
  project declines. (Worth relaying upstream: PR #2 reports Antigravity as
  installed-but-never-launched with no data directory, so this is evidence
  that repository does not have.)
- **The canonical self-report works fine.** An Antigravity Worker with the
  normal filesystem/git/shell capabilities writes its own report like any
  other role. It needs no adapter and no transcript access.

Say that correctly wherever providers are discussed.

## Also land

The retrieval order as a documented procedure — self-report, then
transcript fallback, then manual relay — in `docs/agents/role-contracts.md`
or a new `docs/agents/report-handoff.md` as you judge best.

Tests, following `tests/test_push_readiness.py` and
`tests/test_claude_adapter.py`: fixture inboxes and fixture session stores
rather than dependence on any real one. Cover the atomic write, staleness
detection, role derivation, the round-identification rule, both named
failure modes, and a missing config returning UNKNOWN. Standard library
only.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`). Fetch
`origin/main`, branch from it (e.g. `worker/report-recovery`). Do not
merge to `main` yourself. Do not push. The round-11 guard will stop you if
you start in the primary checkout.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- What you adopted from `agentic-project-framework` PR #2 verbatim, what
  you adapted, and anything you deliberately did differently — with
  reasons, flagged for upstream.
- How you handled PR #2 being unmerged, and your role-tag naming decision.
- How the Claude Stop hook now converges on the shared writer.
- Your round-identification rule for the fallback path, what you tested it
  against, and your justification for any threshold.
- Confirmation both named failure modes return UNKNOWN, with output.
- The tests added, and confirmation each fails without its fix.
- Exact output of the full suite, `validate`, and `build --check`.
- For each of Claude Code, Codex and Antigravity: whether a report arrives
  by self-report, by transcript fallback, or needs manual relay.
- Anything left genuinely uncertain, stated as uncertain.
