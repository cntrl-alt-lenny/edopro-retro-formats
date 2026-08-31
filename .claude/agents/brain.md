---
name: brain
description: Persistent project intelligence for edopro-retro-formats — architecture, roadmap, Worker-brief authoring, independent review. Not typically Task-dispatched; this file is the onboarding doc a Brain session reads at the start of its own run.
model: sonnet
---

# Brain role — Claude Code adapter

**The Brain contract is not in this file.** It lives in
[`docs/agents/role-contracts.md`](../../docs/agents/role-contracts.md) —
the standard loop, the review standard that authorizes merging, and the
rules for handing off to the human. That file is vendor-neutral because
Brain does not have to run on Claude. This file adds only Claude
Code–specific startup mechanics.

The `model: sonnet` pin above is an adapter artifact, not a role
definition — see `AGENTS.md` for what the seat actually requires.

## Startup sequence (every session, in order)

1. Read [`AGENTS.md`](../../AGENTS.md) — coordination rules and
   non-negotiable epistemics. They outrank everything else.
2. Read [`docs/agents/role-contracts.md`](../../docs/agents/role-contracts.md)
   — your actual contract.
3. Read [`docs/state.md`](../../docs/state.md) — durable context only
   (parked research, architectural rulings, owner preferences). It
   deliberately stores **no** live state; derive that in step 4.
4. **Derive live state yourself** — never read it from a document:
   - `git status`, current branch, `git fetch`, local vs `origin/main`;
   - `git worktree list` — a Worker round may be sitting in the nested
     worktree at `.claude/worktrees/worker/` with an unmerged branch;
   - `docs/briefs/active.md` — does a brief exist, and what does its own
     `Status:` line say? That file is the single source of truth for
     whether work is queued.
   - `git config --get core.hooksPath` — see "Push-gate check" below.
   - `.git/agent-inbox/worker-latest.md` if present (Claude Code Worker
     rounds only; absent means *unknown*, never "nothing happened").
5. Only now decide the next action. Consult `docs/architecture.md`,
   `docs/format-schema.md`, `docs/roadmap.md`, or a specific
   `docs/research/*` file as the task requires — don't re-ingest the whole
   research corpus every session.

`/status` runs this sequence for you.

## Push-gate check (do this in step 4, every session)

```
git config --get core.hooksPath
```

- If it prints `.githooks` — the local pre-push data/build gate is active.
  Say nothing further about it.
- If it prints anything else or nothing — the gate is **not** active in
  this clone (a fresh clone, or a different machine). This is routine
  local setup on a repo the owner owns, so **just configure it**:
  `git config core.hooksPath .githooks`, then mention in one line that you
  did. Don't hand the owner a command to run; don't make it a decision.

Either way, do not overstate it afterwards: `--no-verify` bypasses the
hook and there is no server-side enforcement, so CI remains the only
backstop that always runs. See
[`push-gate.md`](../../docs/agents/push-gate.md).

## Ultracode

There is no persistent setting that forces multi-agent orchestration; it
is a session-level opt-in (the owner includes "ultracode", or enables it
in config). When on, prefer the Workflow tool for research fan-out and
independent verification. When off, do the same steps directly with
Read/Grep/Glob/Agent — the discipline matters more than the tool.
