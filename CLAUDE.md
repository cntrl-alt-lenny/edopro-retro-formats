# CLAUDE.md

Bootstrap only. This file exists because Claude Code auto-loads
`CLAUDE.md` but not `AGENTS.md`, so without it every session depends on
someone remembering to point at the right onboarding files. The
coordination contract itself is **not** duplicated here — keep this file
tiny, and put durable rules in the documents it points to.

**Read [`AGENTS.md`](AGENTS.md) first.** It is the canonical coordination
contract (roles, merge authority, and the project's non-negotiable
epistemic rules) and it outranks anything else in the repository.

Then, depending on what you are doing in this session:

- **Operating as Brain** (project intelligence: architecture, sequencing,
  writing Worker briefs, independently reviewing Worker rounds) — read
  [`.claude/agents/brain.md`](.claude/agents/brain.md), then
  [`docs/state.md`](docs/state.md) for live project state. `/status` runs
  that rehydration for you.
- **Executing a Worker brief** — read
  [`.claude/agents/worker.md`](.claude/agents/worker.md), then your
  assigned brief in [`docs/briefs/active.md`](docs/briefs/active.md).
  Read only what the brief scopes; do not ingest the whole
  `docs/research/` corpus by default.
- **Just answering a question about the repo** — `docs/state.md` plus the
  specific doc the question is about is usually enough.

Two things that catch people out, both learned the hard way here:

- Brain and a locally-run Worker must not share one working directory —
  see [`docs/agents/worktree-mechanism.md`](docs/agents/worktree-mechanism.md).
- Local hooks are convenience, not enforcement; CI is the backstop — see
  [`docs/agents/push-gate.md`](docs/agents/push-gate.md).
