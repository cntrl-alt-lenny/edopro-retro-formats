---
name: worker
description: Single execution role for edopro-retro-formats. Executes exactly one Brain-authored brief per invocation, in whichever MODE the brief specifies (implementation, historical research, source verification, adversarial audit, data/schema work, regression investigation, documentation). Use for a self-contained brief that fits in one context; for a brief that needs its own branch and commits for Brain to review independently, launch a standalone session instead (see "Launching Worker" below).
tools: "*"
model: sonnet
hooks:
  UserPromptSubmit:
    - matcher: ""
      hooks:
        - type: command
          command: "sh .claude/hooks/check_worker_checkout.sh"
---

# Worker role — Claude Code adapter

**The Worker contract is not in this file.** It lives in
[`docs/agents/role-contracts.md`](../../docs/agents/role-contracts.md) —
vendor-neutral, because this project runs Worker on whichever model the
owner chooses. This file only adds Claude Code launch mechanics.

The blocking `UserPromptSubmit` hook above derives the Git common directory,
current checkout, and branch before the first Worker prompt is processed. It
refuses to continue unless the session is in the nested
`.claude/worktrees/worker/` worktree on a `worker/*` branch. If it blocks,
restart the session from that worktree and branch it from `origin/main`.

If you are executing a brief right now:

1. Read [`AGENTS.md`](../../AGENTS.md).
2. Read [`docs/agents/role-contracts.md`](../../docs/agents/role-contracts.md)
   — modes, ground rules, and the completion-report contract.
3. Read your brief (`docs/briefs/active.md` unless pointed elsewhere).

The `model: sonnet` pin above is an adapter artifact — Claude Code
frontmatter syntax, only meaningful inside a Claude Code session. It does
not define the role, and a Worker round run on another vendor's model is
equally valid (see `AGENTS.md`).

## Launching Worker

**Effort is not a declarative field in an agent file as of this writing** —
this frontmatter can pin the *model* but not a reasoning-effort tier. Two
real ways to run a Claude Worker at explicit high effort:

1. **Brain dispatches via the Workflow tool**, when orchestration is
   already appropriate: an `agent()` call with
   `{ agentType: 'worker', model: 'sonnet', effort: 'high' }` pins both
   model and effort. Good for a self-contained brief that fits in one
   context and doesn't need its own branch lifecycle.
2. **A human launches a standalone session** (Claude Code or any other
   vendor's agentic tool) for a brief that needs its own branch and
   commits: start a session, select the model/effort at launch, and open
   with the brief. This is the expected path for most real rounds.

Whichever is used, the working directory matters: **if a Worker runs on
the same machine as a Brain session sharing this clone, it must run in the
nested worktree**, not Brain's checkout — see
[`worktree-mechanism.md`](../../docs/agents/worktree-mechanism.md). Brain
states the correct directory in the prompt it hands the human, so this is
normally already handled by the time a Worker session starts.

Do not invent a third mechanism (e.g. a made-up frontmatter `effort:` key)
if neither fits — document the gap instead of guessing.
