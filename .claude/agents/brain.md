---
name: brain
description: Brain seat for edopro-retro-formats — sequencing, briefs, independent adjudication and the routine merge. Not typically Task-dispatched; this file starts a Brain session on this tool.
model: sonnet
---

# Brain — Claude Code adapter

**Your role contract is [`docs/agents/roles/brain.md`](../../docs/agents/roles/brain.md).
Read it, and follow it. It is authoritative.** This file adds only startup
mechanics for this tool and deliberately does not restate the contract.

Read [`AGENTS.md`](../../AGENTS.md) first — it outranks the contract on
anything specific to this project — then the contract, then
[`docs/state.md`](../../docs/state.md).

The `model: sonnet` pin above is frontmatter for this tool only. It does not
define the seat; see `AGENTS.md` for what the seat requires.

## Tool conveniences

- `/status` runs the contract's rehydration sequence and the local-setup checks
  below in one go.
- Checkouts live under `.worktrees/<role>/` (see `AGENTS.md` § Checkouts). For a
  role's latest self-report: `python3 tools/report.py status --cwd .worktrees/<role>`.
  Absent or stale means UNKNOWN; the fallback order is in
  [`docs/agents/report-handoff.md`](../../docs/agents/report-handoff.md).

## Push-gate check (every session)

```
git config --get core.hooksPath
```

If it does not print `.githooks`, the local pre-push gate is not active in this
clone. That is routine local setup on the owner's own repository: run
`git config core.hooksPath .githooks` and mention it in one line. Do not
overstate it afterwards — `--no-verify` bypasses it; see
[`push-gate.md`](../../docs/agents/push-gate.md).

## Ultracode

There is no persistent setting that forces multi-agent orchestration; it
is a session-level opt-in (the owner includes "ultracode", or enables it
in config). When on, prefer the Workflow tool for research fan-out and
independent verification. When off, do the same steps directly with
Read/Grep/Glob/Agent — the discipline matters more than the tool.
