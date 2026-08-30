---
description: Rehydrate as Brain in one shot -- read AGENTS.md, docs/state.md, the current git/GitHub state, and docs/briefs/active.md, then summarize what's live and what's next.
argument-hint: []
allowed-tools: Read, Bash, Grep, Glob
---

Run Brain's standard rehydration sequence (see `.claude/agents/brain.md`
"Startup sequence" for the full rationale) and report back concisely,
not by dumping every file:

1. Read `AGENTS.md` and `docs/state.md`.
2. Check live repo state: current branch, `git status`, `git fetch`, and
   whether local `main` matches `origin/main`. If `docs/state.md`'s
   pinned SHA is stale, say so plainly rather than silently trusting it.
3. Check `docs/briefs/active.md` -- is a brief queued, in progress
   (a branch matching its expected name exists locally or on `origin`),
   or is the placeholder empty ("no brief queued")?
4. If `.git/agent-inbox/worker-latest.md` exists (see
   `.claude/hooks/save_agent_reply.py` -- only present if a Worker round
   ran as a Claude Code session), check its timestamp. If it's newer
   than the last brief-archive event, surface it -- it may be a
   completed round nobody has reviewed yet.

Report back in a few short sections: **Repo state** (branch/SHA
sync), **In-flight** (what's queued/running, from where), **Parked /
do-not-reopen reminders worth repeating** (only if something in
`docs/state.md` is directly relevant right now), **Recommended next
action**. Do not re-paste large chunks of `docs/state.md` verbatim --
synthesize.
