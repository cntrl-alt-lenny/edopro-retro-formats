# Retired: this project's pre-framework agent documents

**Read-only history. Not current policy.** Nothing in this directory is
normative, and nothing here outranks [`AGENTS.md`](../../../AGENTS.md) or the
canonical role contracts in [`docs/agents/roles/`](../../agents/roles/).

On 2026-09-16 this project adopted the shared agentic framework
(`cntrl-alt-lenny/agentic-framework`). These files were the project's own,
hand-written predecessors, and they were retired rather than deleted:

| Retired file | Superseded by |
|---|---|
| `role-contracts.md` | [`docs/agents/roles/brain.md`](../../agents/roles/brain.md), [`worker.md`](../../agents/roles/worker.md) and [`verifier.md`](../../agents/roles/verifier.md) for the generic contracts; the project-specific parts (mode names, the review checklist for historical data, the exact validation commands) moved into [`AGENTS.md`](../../../AGENTS.md). |
| `worktree-mechanism.md` | [`docs/agents/git-and-isolation.md`](../../agents/git-and-isolation.md) for the rule; `AGENTS.md` § Checkouts for this project's layout. The nested checkout moved from `.claude/worktrees/worker/` to `.worktrees/<role>/`, one per seat. |

Archived briefs and `docs/agents/model-notes.md` still link to these paths by
their old location, and name the old `Worker` seat and `worker/<slug>` branches.
That is a record of what happened, and is deliberately left as written.
