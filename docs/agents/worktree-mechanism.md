# Worktree mechanism

Brain and Worker use **separate sibling git worktrees of the same clone**,
not the same checkout with branch-switching. This exists because of a
real incident: a Worker round ran directly in the Brain session's
checkout, checked out its own branch there, and a later Brain session
didn't notice before committing unrelated work on top of it. Nothing was
lost (the mistake was caught before pushing), but it shouldn't have been
possible to make in the first place.

## Layout

```
C:\Users\leona\Dev\edopro-retro-formats           <- Brain's worktree, stays on main
C:\Users\leona\Dev\edopro-retro-formats-worker    <- Worker's worktree, detached HEAD by default
```

Both are worktrees of the same underlying repository (`git worktree list`
from either shows both). They share the same object database and remote,
so a `git fetch`/`git push` from either sees the other's history once
pushed. They do **not** share a working directory or index — Worker can
never accidentally check out a branch that Brain is also sitting on, and
Brain switching branches for its own review work can never disturb
Worker's uncommitted state.

## How to use it

**Brain**: always operate from the primary checkout
(`edopro-retro-formats`), on `main`. This is where independent review,
merging, and pushing happen.

**Worker**: when Worker runs locally on the same machine as Brain (as
opposed to a cloud/remote session, which is naturally isolated already),
point it at `edopro-retro-formats-worker` instead of the primary checkout.
At the start of each round, create the task branch there:

```
cd ../edopro-retro-formats-worker
git fetch origin
git checkout -b worker/<slug> origin/main
```

Worker commits to that branch and stops — it still never merges or
pushes its own work (see `AGENTS.md`). Once Brain accepts a round, Brain
merges from the *primary* worktree (`git merge --ff-only
worker/<slug>` or a cherry-pick, whichever produces a clean line), then
deletes the now-merged branch. The worker worktree itself is reusable
across rounds — it doesn't need recreating each time, just re-synced
(`git fetch && git checkout -b worker/<next-slug> origin/main`) once its
previous branch is merged and deleted.

## If Worker's branch needs deleting while checked out elsewhere

A worktree holds a lock on whatever branch it has checked out. If Brain
tries to delete a Worker branch while the worker worktree still has it
checked out, `git branch -d` will refuse. Either check the worker
worktree out onto something else first (`git -C
../edopro-retro-formats-worker checkout --detach main`), or just leave
the merged branch until the next round starts and reuses/replaces it —
it's harmless clutter, not a correctness risk.

## Removing the worktree

`git worktree remove ../edopro-retro-formats-worker` (from the primary
checkout) if it's ever no longer needed. Don't just `rm -rf` the
directory — that leaves stale worktree metadata in `.git/worktrees/`
that `git worktree remove --force` or `git worktree prune` would then
need to clean up anyway.
