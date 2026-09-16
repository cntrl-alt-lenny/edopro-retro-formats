---
description: Rehydrate as Brain in one shot -- read the contracts and durable state, derive all live state from git, check local setup, then summarize what's live and what's next.
argument-hint: []
allowed-tools: Read, Bash, Grep, Glob
---

Run the startup sequence in `docs/agents/roles/brain.md` and report back
concisely — do not dump file contents.

**Read (durable):**

1. `AGENTS.md` — topology, project invariants, evidence table.
2. `docs/agents/roles/brain.md` — your contract.
3. `docs/state.md` — durable context only. It intentionally contains no
   live state; do not quote a SHA or queue status from it.

**Derive (live — from git and the filesystem, never from a document):**

4. `git status`, current branch, `git fetch`, local HEAD vs `origin/main`.
5. `git worktree list` and `git branch -a` — is there an unmerged
   `builder/<scope>` branch, or a checkout under `.worktrees/`?
6. `docs/briefs/active.md` and `docs/briefs/delivered/` — what does the
   brief's own `Status:` line say, and is a delivered round waiting for
   adjudication? That comes first.
7. `python3 tools/report.py status --cwd .worktrees/builder` and
   `--cwd .worktrees/verifier` — the checkout-derived self-reports. Absent or
   stale means **unknown**, never "nothing happened"; fallbacks are in
   `docs/agents/report-handoff.md`.
8. CI for the exact head SHA of `main` and of any delivered branch.

**Check local setup:**

9. `git config --get core.hooksPath`. If it is not `.githooks`, configure it
   (`git config core.hooksPath .githooks`) and note in one line that you
   did. Routine local setup — do it, don't ask. Don't overstate it:
   `--no-verify` bypasses it, and CI is the backstop.

**Report** in a few short sections: **Repo state**, **In flight**,
**Setup** (only if something was configured or is missing), **Recommended
next action**. Synthesize — don't re-paste `docs/state.md`.
