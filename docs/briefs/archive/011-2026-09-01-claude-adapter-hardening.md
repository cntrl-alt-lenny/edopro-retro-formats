# Active brief

Status: **complete** — landed as `b9c1064`, reviewed and merged 2026-09-01.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on completion move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (zero-padded, check the archive
for the last-used number) and replace it with the next one, or leave a
one-line "no brief queued" placeholder. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — coordination rules and the
   non-negotiable epistemic rules. They outrank convenience.
2. [`docs/agents/role-contracts.md`](../agents/role-contracts.md) — the
   Worker contract: your mode's rules, the ground rules, and the
   completion-report schema you must report back in.

Then this brief in full. Read only the further docs this brief scopes as
relevant — don't ingest `docs/research/` wholesale.

---

## MODE: IMPLEMENTATION

## Goal

Repair four **demonstrated** defects in this repository's own Claude Code
adapter. Both have already caused real damage in a live round, so this is
the "real project development exposed a concrete problem" exception in
`docs/state.md`'s operating policy — not framework polish.

This round is **narrowly framework-focused**. Do not combine any roadmap
or canonical-data work with it.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

---

## Defect 1 — the Stop hook depends on one hard-coded interpreter name

`.claude/settings.json` runs `python .claude/hooks/save_agent_reply.py`.
On a host where the `python` name does not exist but `python3` does, the
hook exits 127 and silently writes nothing, so
`.git/agent-inbox/worker-latest.md` is never produced and Brain silently
loses every Worker report. The script itself is correct — only the launch
is not portable.

Do **not** simply swap `python` for `python3`. `settings.json`'s own
description records that the reverse host also exists in this project
(a host with no `python3` on PATH at all), which is why the current value
is what it is. Either direction hard-coded breaks one of the two.

**The pattern to follow already exists in this repository.**
`.githooks/pre-push` solves exactly this: a `/bin/sh` shim that probes
`python3`, falls back to `python`, and degrades with a clear message when
neither is present rather than silently no-opping. Its header comment
states the principle — a hook that silently no-ops because the
interpreter name is wrong is worse than no hook. Reuse that pattern
rather than inventing a second one, and if you conclude it cannot be
reused as-is for a Claude Code `Stop` hook, say why explicitly instead of
substituting your own approach silently.

Test the realistic host cases, not just the one you are running on:
`python3` only, `python` only, both present, neither present. Neither
present must degrade cleanly and must never block a session from ending —
`save_agent_reply.py`'s own docstring is normative on that point.

---

## Defect 2 — a Worker can run in Brain's primary checkout (the important one)

`AGENTS.md` § Working discipline records this failure: a Worker round ran
in Brain's own checkout and a later Brain session committed on top of it.
**It has now happened twice.** The second time, a Worker round created and
switched to its branch inside the primary checkout while a Brain session
was working there, and a Brain bookkeeping commit landed on the Worker's
branch instead of `main`.

The existing prevention is an instruction to re-check `git branch` /
`git status`. Two occurrences is sufficient evidence that an instruction
is not prevention. **Replace it with a mechanism.**

Requirements:

- Before any Worker work begins, **derive from Git** whether the session
  is in the intended isolated Worker checkout/worktree and on an
  appropriate Worker branch. Derive it — do not trust an environment
  variable a Worker could forget to set, and do not ask the Worker to
  self-declare.
- If the session is actually in the primary/Brain checkout, **fail
  closed**: stop clearly and visibly *before* anything is modified, with a
  message that says what is wrong and what to do instead. Failing closed
  matters more than being clever about recovery.
- Decide and state where the check belongs so that it actually runs
  before work starts. Consider the adapter's own launch path and
  `.claude/agents/worker.md`; if you conclude no available hook point can
  guarantee "before modification", say so plainly rather than shipping a
  check that only fires sometimes — a partial guard that reads as
  prevention is worse than a documented gap.
- Do not make this depend on the Stop hook from Defect 1. They must be
  independent.

`docs/agents/worktree-mechanism.md` defines the intended layout
(`.claude/worktrees/worker/`, nested, one project folder — an owner
preference recorded in `docs/state.md`).

---

## Defect 3 — the pre-push gate is tracked non-executable, so it never runs

Found while pushing round 10's acceptance commit. `.githooks/pre-push` is
tracked mode `100644`, so even in a clone with `core.hooksPath=.githooks`
correctly set, Git skips it:

    hint: The '.githooks/pre-push' hook was ignored because it's not set
    as executable.

The gate has therefore been inactive in this clone the whole time,
reporting as "configured" to anyone who checked `core.hooksPath` — the
same silent-no-op class as Defect 1, in a different mechanism. Fix the
tracked mode (`git update-index --chmod=+x`, so it is the *committed* mode
that changes, not just the local file), and add a regression test that
asserts the tracked mode rather than the working-tree mode, since only the
tracked one survives a fresh clone.

While you are there: `docs/agents/push-gate.md` and `.githooks/pre-push`'s
own activation comment both tell a reader to set `core.hooksPath` and stop
there. If setting it is not by itself sufficient to make the gate run, say
so where those instructions are.

---

## Defect 4 — a durable doc asserts per-clone setup as if it were repo state

`docs/agents/worktree-mechanism.md` states: *"The nested worktree already
exists (created once via `git worktree add --detach
.claude/worktrees/worker main`); it doesn't need recreating on a fresh
clone unless it's missing."* On this clone it did **not** exist, and the
round-11 Worker correctly stopped because of it — Brain had to create it
before the round could start.

A worktree is per-clone state, not repository state: `.claude/worktrees/`
is gitignored precisely so it is never committed, so *no* clone gets one
by cloning. The sentence is therefore wrong in the same way the phrases
`tests/test_state_doc_is_durable.py` bans from `docs/state.md` are wrong —
a durable doc asserting per-machine setup status. Fourth instance of the
same family this round already covers: setup that silently isn't there,
described as though it is.

Correct the wording so it describes how to *derive* whether the worktree
exists and create it if not, rather than asserting it does. Then consider
whether the durability guard should extend beyond `docs/state.md` to the
other `docs/agents/*.md` framework docs — if you conclude it should not,
say why; a guard that covers one file because that is the file someone
happened to write a test for is not a defensible boundary.

This pairs directly with Defect 2: the fail-closed check tells a Worker it
is in the wrong place, and this tells whoever reads the docs how the right
place comes to exist.

---

## Method

**Reproduce both defects before fixing either.** For Defect 1 that means
demonstrating the silent 127 on a host missing the configured interpreter
name; for Defect 2, demonstrating that a Worker-style session in the
primary checkout is currently not stopped. Record what you actually ran
and what it produced. A fix whose defect was never reproduced is not
accepted this round.

Then fix the **defect classes**, per `AGENTS.md`: not "make it work on
this laptop" and not "guard the one path that broke."

Add regression tests. `tests/test_push_readiness.py` is the precedent for
testing hook behaviour in this repository — follow its shape. Both fixes
must be covered, and the Defect 2 test must assert the fail-closed
behaviour, not merely that a helper function exists. Standard library
only, as everywhere else here.

Run the full suite (`python3 -m unittest discover -t . -s tests`), plus
`validate` and `build --check` to confirm you changed nothing canonical.

## Documentation

Update the durable framework docs — `docs/agents/worktree-mechanism.md`,
`docs/agents/push-gate.md` and `docs/state.md` as applicable — with
**host-independent facts only**. `tests/test_state_doc_is_durable.py`
enforces this and will fail on per-machine claims; do not name which
machine has which interpreter, and do not record live or per-host setup
state. The durable fact is the *class*: the adapter must not depend on one
interpreter name, and Worker isolation is enforced mechanically rather
than by instruction.

If the instruction in `AGENTS.md` § Working discipline is now backed by a
mechanism, update its wording to say so. Do not delete the incident
record — it is why the mechanism exists.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`, see
`docs/agents/worktree-mechanism.md`) if running locally alongside a Brain
session. Fetch `origin/main` and branch from there
(e.g. `worker/adapter-hardening`). Do not merge to `main` yourself.
Do not push.

The nested worktree at `.claude/worktrees/worker/` was created by Brain on
2026-09-01 after a Worker round stopped because it was missing; it exists
now, so start there. If your own Defect 2 guard stops you when you start
this round, that is a successful reproduction — record it and proceed in a
correct worktree.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Defect 1: how you reproduced the silent failure; the launch mechanism
  you chose and why; the result for each of the four host cases
  (`python3` only, `python` only, both, neither); whether you reused
  `.githooks/pre-push`'s pattern and, if not, why not.
- Defect 2: how you reproduced the unguarded case; what you derive from
  Git and how; where the check runs and your evidence that it runs before
  any modification; what happens on failure; any case you could not cover.
- Defect 4: the corrected wording, and your reasoning on whether the
  durability guard should extend to the other framework docs.
- Defect 3: confirmation the tracked mode changed (not just the working
  tree), and that a fresh clone would get an executable hook.
- The regression tests added, and confirmation each one fails without its
  fix.
- Exact output of the full suite, `validate`, and `build --check`, plus
  confirmation `dist/` is unchanged.
- Which durable docs you changed, and confirmation
  `tests/test_state_doc_is_durable.py` passes.
- Anything left genuinely uncertain, stated as uncertain.
