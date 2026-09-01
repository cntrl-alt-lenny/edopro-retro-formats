# Active brief

Status: **queued, not started**.

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

Land, as tracked and tested repository code, the **cross-provider report
recovery** that Brain currently runs from an untracked prototype.

Round 11 fixed the Claude Code adapter so a *Claude Code* Worker writes
`<git-common-dir>/agent-inbox/worker-latest.md`. That does nothing for a
Worker round run on another provider — which is most of them here, and is
deliberate (`AGENTS.md` values model diversity). Today the owner relays
those reports by hand. A working prototype already recovers them from the
provider's own local session store; this round makes it real code.

**Scope discipline:** this is framework work. Do not combine roadmap or
canonical-data work with it.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

## The prototype to promote

Brain's working prototype lives at
`<git-common-dir>/agent-inbox/recover_agent_report.py`, with its
machine-local provider roots in
`<git-common-dir>/agent-inbox/providers.local.json`. Read both. They are
untracked runtime state, not a deliverable — **promote the mechanism, keep
the machine-specific paths out of the repository.** Nothing naming a
provider's install location on a particular host may enter a tracked file.

Proven working against real local sessions:

- **Claude Code** — one JSONL transcript per session; every record carries
  `cwd`, `gitBranch`, `sessionId`, `timestamp`. Final response is the last
  assistant text record.
- **Codex** — JSONL rollouts; `event_msg` / `task_complete` carries a
  purpose-built `last_agent_message`. Note `session_meta` records only
  START-of-session `cwd`/branch, so identity cannot rest on it.

Excluded, and record why rather than silently omitting: **Antigravity**
stores conversation content in undocumented binary blob columns of a
per-conversation SQLite database. Parsing that is precisely the fragile
opaque-provider-database dependency this project rules out. It stays
manual relay until a supported export exists.

## The rule that matters most

**Identify the round, never "the most recent conversation."** The
prototype earned this the hard way: a first version returned round 11's
session for a round 10 query, because round 11 had run `git log` and so
mentioned round 10's branch and SHA. Mentioning a round is not producing
it.

The prototype's current discriminator is a time anchor: the producing
session's store is still being written within a bounded window after the
round's own commit; anything outside that window only *read* the SHA.
Reconcile on repository/worktree path, branch, exact head SHA and
timestamp together.

Treat that discriminator as a starting point you must test, not as
settled. If you can find a stronger or more direct signal, use it and say
why. If you keep the time anchor, justify the bound rather than inheriting
900 seconds because the prototype used it.

Two failure modes to cover explicitly:

- **Brain's own live session** matches its own commits. It must never be
  returned as a Worker report.
- **A round whose Worker ran off this machine** (cloud, or a provider with
  no local store) must return UNKNOWN and ask for a relay — never the
  nearest plausible session. Round 10 (`f355d79`,
  `worker/search-verification-interval`) is a real, reproducible instance:
  its producing session exists in no local store.

## Preserve these rules exactly

- **Absence is UNKNOWN**, never "the agent did nothing".
- **A recovered report is evidence, not ground truth** — it is what the
  agent *said*, to be checked against the diff, never a substitute for
  reviewing the diff. `AGENTS.md` § Working discipline already states the
  general form of this; the recovery path must not create an exception.
- **Ambiguity is reported, not resolved by guessing.**

## Also land

The retrieval **order** as a documented procedure, in
`docs/agents/role-contracts.md` or a new `docs/agents/report-handoff.md`
as you judge best: (1) shared inbox; (2) determine the provider for that
role — stated by the owner, else inferred from the round record, else ask;
(3) recover from that provider's local store; (4) ask for a manual paste
only when those fail.

Tests, following `tests/test_push_readiness.py` and
`tests/test_claude_adapter.py`: fixture session stores rather than a
dependency on any real one, covering each supported provider, the
round-identification rule, both failure modes above, and a missing config
returning UNKNOWN. Standard library only.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`). Fetch
`origin/main`, branch from it (e.g. `worker/report-recovery`). Do not
merge to `main` yourself. Do not push. The round-11 guard will stop you if
you start in the primary checkout.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Where the mechanism lives and how a host supplies its own provider paths
  without touching a tracked file.
- Your round-identification rule, what you tested it against, and your
  justification for any threshold.
- Confirmation both named failure modes return UNKNOWN, with output.
- The tests added, and confirmation each fails without its fix.
- Exact output of the full suite, `validate`, and `build --check`.
- Which providers a Worker report can now be recovered from automatically,
  and which still need a manual relay.
- Anything left genuinely uncertain, stated as uncertain.
