# CLAUDE.md

Bootstrap only. This file exists because Claude Code auto-loads
`CLAUDE.md` but not `AGENTS.md`. It carries no rules of its own — keep it
tiny, and put durable rules in the documents it points to.

**Read [`AGENTS.md`](AGENTS.md) first.** It is this project's coordination
document: the declared topology (Brain, Builder, Verifier), the
non-negotiable project invariants, and the evidence each change must
produce. It outranks anything else in the repository.

Then read the contract for the seat you were given, from
[`docs/agents/roles/`](docs/agents/roles/):

- **Brain** — [`brain.md`](docs/agents/roles/brain.md). `/status` runs the
  rehydration sequence.
- **Builder** — [`worker.md`](docs/agents/roles/worker.md) (the Builder
  holds the Worker contract), then your brief in
  [`docs/briefs/active.md`](docs/briefs/active.md).
- **Verifier** — [`verifier.md`](docs/agents/roles/verifier.md). Do not
  read the Builder's report before your first pass.
- **Just answering a question about the repo** — `docs/state.md` plus the
  specific document the question is about is usually enough.

Files under `.claude/` are adapter mechanics for this one tool and never
redefine a contract.
