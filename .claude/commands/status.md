---
description: Rehydrate as Brain in one shot -- read the contracts and durable state, derive all live state from git, check local setup, then summarize what's live and what's next.
argument-hint: []
allowed-tools: Read, Bash, Grep, Glob
---

Run Brain's rehydration sequence (rationale:
`.claude/agents/brain.md` and `docs/agents/role-contracts.md`) and report
back concisely — do not dump file contents.

**Read (durable):**

1. `AGENTS.md` — coordination rules and epistemics.
2. `docs/agents/role-contracts.md` — your actual contract.
3. `docs/state.md` — durable context only. It intentionally contains no
   live state; do not quote a SHA or queue status from it.

**Derive (live — from git and the filesystem, never from a document):**

4. `git status`, current branch, `git fetch`, local HEAD vs `origin/main`.
5. `git worktree list` and `git branch -a` — is there an unmerged
   `worker/<slug>` branch, or a Worker round sitting in
   `.claude/worktrees/worker/`?
6. `docs/briefs/active.md` — does a brief exist, and what does its own
   `Status:` line say? This is the only source of truth for whether work
   is queued.
7. `.git/agent-inbox/worker-latest.md` if it exists — Claude Code Worker
   rounds only. Check its timestamp. Absent or stale means **unknown**,
   never "nothing happened."

**Check local setup:**

8. `git config --get core.hooksPath`.
   - Prints `.githooks` → the pre-push data/build gate is active; say
     nothing about it.
   - Anything else or empty → not active in this clone (fresh clone, or a
     different machine). Configure it: `git config core.hooksPath
     .githooks`, then note in one line that you did. This is routine local
     setup on the owner's own repo — do it, don't ask, and don't hand them
     a command to run.
   - Either way don't overstate it: `--no-verify` bypasses it and there is
     no server-side enforcement, so CI is the real backstop.

**Report** in a few short sections: **Repo state** (branch, sync, anything
unmerged), **In flight** (what's queued or awaiting review, from
`active.md` and git), **Setup** (only if something was configured or is
missing), **Recommended next action**. Synthesize — don't re-paste
`docs/state.md`.

If a Worker round is awaiting review, say so first: that's the next
action, not a new task.
