# Worktree mechanism

Brain and Worker share **one visible project folder**
(`edopro-retro-formats`), but Worker's actual working directory is a
**nested git worktree inside it**, not the same checkout with
branch-switching. This exists because of a real incident: a Worker round
ran directly in Brain's own checkout, checked out its own branch there,
and a later Brain session didn't notice before committing unrelated work
on top of it. Nothing was lost (the mistake was caught before pushing),
but it shouldn't have been possible to make in the first place.

An earlier version of this mechanism used a separate sibling folder
(`edopro-retro-formats-worker`, next to `edopro-retro-formats` in `Dev/`).
The human project owner rejected that layout — pointed at a sibling
project's own multi-agent setup, which keeps everything inside one
top-level folder via a nested `.claude/worktrees/` directory. This file
now describes that same pattern, adapted to this project's two roles.

## Layout

```
edopro-retro-formats/                          <- the only folder that exists in Dev/
├── (Brain's working directory — stays on main)
└── .claude/worktrees/worker/                  <- Worker's worktree, detached HEAD by default
```

Both are worktrees of the same underlying repository (`git worktree list`
from either shows both). They share the same object database and remote,
so a `git fetch`/`git push` from either sees the other's history once
pushed. They do **not** share a working directory or index — Worker can
never accidentally check out a branch that Brain is also sitting on, and
Brain switching branches for its own review work can never disturb
Worker's uncommitted state. `.claude/worktrees/` is gitignored (see
`.gitignore`) so it never shows up as clutter in `git status` from the
primary checkout — without that entry, git does **not** automatically
exclude a nested worktree from status output, it just looks like an
untracked directory.

The nested worktree already exists (created once via `git worktree add
--detach .claude/worktrees/worker main`); it doesn't need recreating on a
fresh clone unless it's missing — check `git worktree list` first.

## How to use it

**Brain**: always operate from the primary checkout root
(`edopro-retro-formats/`), on `main`. This is where independent review,
merging, and pushing happen.

**Worker**: when Worker runs locally on the same machine as Brain (as
opposed to a cloud/remote session, which is naturally isolated already),
point it at `edopro-retro-formats/.claude/worktrees/worker` instead of
the project root. At the start of each round, create the task branch
there:

```
cd .claude/worktrees/worker
git fetch origin
git checkout -b worker/<slug> origin/main
```

Worker commits to that branch and stops — it still never merges or
pushes its own work (see `AGENTS.md`). Once Brain accepts a round, Brain
merges from the *primary* checkout (`git merge --ff-only worker/<slug>`,
which is a clean fast-forward whenever Worker branched from a current
`origin/main`), then deletes the now-merged branch. The nested worktree
itself is reusable across rounds — it doesn't need recreating each time,
just re-synced (`git fetch && git checkout -b worker/<next-slug>
origin/main`) once its previous branch is merged and deleted.

## If Worker's branch needs deleting while checked out elsewhere

A worktree holds a lock on whatever branch it has checked out. If Brain
tries to delete a Worker branch while the nested worktree still has it
checked out, `git branch -d` will refuse. Either check the nested
worktree out onto something else first (`git -C
.claude/worktrees/worker checkout --detach main`), or just leave the
merged branch until the next round starts and reuses/replaces it — it's
harmless clutter, not a correctness risk.

## Removing the worktree

`git worktree remove .claude/worktrees/worker` (from the primary
checkout) if it's ever no longer needed. Don't just `rm -rf` the
directory — that leaves stale worktree metadata in `.git/worktrees/`
that `git worktree remove --force` or `git worktree prune` would then
need to clean up anyway.

## Cross-device consistency

This layout is meant to be identical on every machine the human project
owner works from (currently a Windows desktop and an M1 MacBook Pro) —
the whole point of writing it down here rather than leaving it as
session-local knowledge. On a fresh clone on any device: `cd
edopro-retro-formats && git worktree add --detach
.claude/worktrees/worker main` once, then follow "How to use it" above.
Nothing about this mechanism is OS-specific.
