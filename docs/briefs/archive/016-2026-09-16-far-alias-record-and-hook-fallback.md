# Active brief

Status: **accepted** (second delivery; see Outcome).

Identifier: **`016-2026-09-16-far-alias-record-and-hook-fallback`** — use exactly
this string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (015 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — topology, project invariants, and the
   evidence table for what you touch.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. The two archived briefs this round follows up, **including their Outcome
   sections**:
   [`014-2026-09-16-per-artwork-printing-dates.md`](archive/014-2026-09-16-per-artwork-printing-dates.md)
   and
   [`015-2026-09-16-report-and-materialize-gates.md`](archive/015-2026-09-16-report-and-materialize-gates.md).
4. For Part A only: [`docs/agents/reports.md`](../agents/reports.md).

Do not read `docs/research/` beyond the one file Part B names.

---

Two parts, judged together in one review. They are unrelated in subject;
they are bundled because each is small and both are corrections to rounds just
accepted.

## Part A — MODE: IMPLEMENTATION

### Goal

The Claude Code Stop hook's fallback capture works again for every session
that ends without writing its own report, while a role's own report still
survives its session ending.

### Why

Round 15 made the hook skip its fallback whenever the checkout already has a
report fresh at the current HEAD. Freshness does not consider who wrote that
report. So when the existing fresh report is itself an earlier session's hook
capture, a later session ending at the same HEAD is captured nowhere — not in
`<role>-latest.md` and not in `<role>-log.md` — and
`python3 tools/report.py status` presents the earlier session's text as fresh.
Brain reproduced this with the real hook in a throwaway repository: two
sessions, same HEAD, one capture. Before round 15 both were captured.

### Scope

`.claude/hooks/save_agent_reply.py`, its tests in `tests/test_claude_adapter.py`,
and the round-15 note about the hook in `docs/state.md`, which is incomplete
until this is fixed. `tools/report.py` only if the right fix genuinely belongs
there; if so, record the new divergence from the framework copy in
`docs/state.md`.

### Protected invariants

- Everything round 15 protected still holds: the delivery check still requires
  the role's own report for the named task at the exact head; a session-tagged
  report never counts as delivery; the hook never blocks a session from ending.
- A report a role wrote for itself is never replaced by a hook capture at the
  same HEAD.
- Nothing under `docs/agents/` is edited in this round.

### Acceptance criteria

- A test reproducing the lost second capture, through the real hook, that
  fails on the base code.
- Round 15's two hook tests still pass unmodified.
- A test showing a role's own report still survives a later hook run at the
  same HEAD.

## Part B — MODE: SOURCE VERIFICATION

### Goal

Roadmap item 4b's audit record describes the far-alias class as it actually
is in the pinned card database, and any in-scope case that record surfaces is
settled on evidence.

### Why

Round 14 enumerated far aliases from `data/cards/index.json`, which only holds
passcodes this repository already references, and recorded the result as
exhaustive. Querying the pinned database directly finds more rows. The roadmap
now carries a review note saying the record is incomplete. See round 14's
Outcome.

### Required investigation

1. **Enumerate from the pinned BabelCDB revision itself** (`data/sources.json`'s
   `ignis-babelcdb`), not from any file derived in this repository. Say which
   database files you queried and why those, confirm what you downloaded is
   that revision, and give the query. Cover every canonical pool, and say how
   an extensional pool differs from a release-cutoff pool for this question.
2. **Classify every real (non-engine-internal) far-alias row** whose base card
   is in a canonical pool, using round 14's split: (a) pure alternate artwork,
   (b) region/scope variant, (c) functionally distinct card. Show the basis for
   each classification.
3. **For each row that is not already in the pool it would belong to,
   establish from a cited source whether it had a TCG printing on or before
   that pool's cutoff.** Establish dates; do not take them from this brief or
   from either earlier report. (One earlier review gave a first-print date for
   Lemuria, the Forgotten City that Brain could not reconcile with the set it
   appears in. Treat all prior dates as unverified.)
4. Establish whether this enumeration can be made repeatable without network
   access in the test suite. Report what you find; do not build it unless it
   is small, offline and clearly within this scope.

### Scope

`docs/roadmap.md` item 4b (replace the incomplete record and its review note
with what you establish), `docs/research/tengu-format-community-diff.json`
only if its 4b-related entry is affected, and — only if step 3 finds an
in-scope printing on or before a cutoff — the release/printing records that
let the pool derive it, exactly as round 14 did.

### Protected invariants

- No pool entry is hand-added; no `force_include`.
- If nothing new is in scope, change no data. "No further gaps" with the full
  enumeration behind it is a complete result.
- GOAT hash `0x28E9FC02` unchanged; banlist entry sets unchanged.
- A community list or wiki summary is not a first-print date; a set's own
  release record is.

## Shared

### Base

Cut from `origin/main`; record the literal starting SHA.

### Non-goals

- The shared framework repository. If you believe its copy of anything here is
  wrong, say so in the report.
- Any validator code, severity or condition.
- Any other roadmap item.

### When to stop

If Part A's right behaviour is genuinely ambiguous, or Part B surfaces a case
whose classification or date cannot be settled from sources, stop that part,
state the options or the open question, and finish the other part.

### Required evidence

`python -m unittest discover -t . -s tests -v`, `python -m retroformats
validate`, `python -m retroformats build --check`, with real output and exit
status on Python 3.10 or newer. For Part A's new test, its failing output on
the base code too. For Part B, the enumeration query and its full output, and
for every date the URL and the passage you read. A green suite is not evidence
for any Part B claim.

### Git expectations

Work only in `.worktrees/builder/`. Branch
`builder/far-alias-record-and-hook-fallback` from `origin/main`. Focused
commits; push the branch; never push `main`; never merge. After your final
commit and push, write your report from inside `.worktrees/builder/` with
`python3 tools/report.py write --task 016-2026-09-16-far-alias-record-and-hook-fallback`
(Python 3.10+), as well as displaying it.

### Completion-report schema

The Worker contract's report, plus: for Part A, root cause and options
considered; for Part B, the full classified table (passcode, name, base, pool,
class, in pool already?, first TCG print and source where needed), and what
you changed versus deliberately left.

---

## Amendment 1 — 2026-09-16, after Brain's first adjudication

The first delivery, `88f12f9b8a90a5f59f830e2d2e5837cbabe4e9f2` on
`builder/far-alias-record-and-hook-fallback`, was **not accepted**. The round
stays open on the same branch and identifier. The brief above is unchanged;
this amendment adds only what must be closed before it can be reviewed.

### What is still missing

**Part B, Required investigation step 3, was done for one row only.** The
delivered record dates the Arkana Dark Magician row. Step 3 applies to *every*
row not already in the pool it would belong to, whatever its class, because a
functionally distinct card with a pre-cutoff TCG printing belongs in a
release-cutoff pool just the same — and round 14 showed that exactly this kind
of printing can be mis-mapped in release data. Seven rows are absent from
Edison and Tengu and have no dated evidence in the record:

- 2819435 Pacifis, the Phantasm City
- 10000100 Black Luster Soldier (vanilla identity)
- 26534688 Magellanica, the Deep Sea City
- 28306253 Angry Burger
- 34103656 Lemuria, the Forgotten City
- 74335036 Fusion Substitute
- 82616239 Light Water Dragon

For each, establish from a cited source whether it had a TCG printing on or
before each release-cutoff pool's cutoff, and record the answer and source in
roadmap item 4b. Where the repository already rules on one (for example in
`data/releases/gaps.json`), cite that ruling and check it rather than
re-researching around it. If any has a qualifying printing, the brief's
Part B scope already covers what to do. If one cannot be settled from sources,
record it as open. Do not take any date from earlier reports or reviews.

**Part A needs no further work unless you find a defect in it.**

### Process defects in the first delivery — do not repeat

- **An edit landed in Brain's primary checkout.** The session patched
  `/Users/leo/Dev/edopro-retro-formats/.claude/hooks/save_agent_reply.py` — the
  primary checkout, not `.worktrees/builder/` — then made the same edit in the
  Builder checkout, and did not undo or report the first. Brain has reverted
  it. Every write must be inside `.worktrees/builder/`; before finishing, run
  `git -C /Users/leo/Dev/edopro-retro-formats status --short` and confirm it
  is empty, and say so in the report.
- **The round ran in the same session as the previous round.** Run this
  amendment in a fresh session.

### How to proceed

Continue on the existing branch from `88f12f9`; do not rewrite or force-push
its history. This amendment lives on `origin/main`, not on your branch: read it
with `git show origin/main:docs/briefs/active.md`. Push, then write your
report with the same identifier. The report must cover the whole round from
base `00f1642c964fa5a1a5c85a53521643c3fc30e2fe`, not only the new commits.

---

## Outcome — accepted 2026-09-16 on second delivery, merged

**First delivery, `88f12f9`: returned, not accepted.** Brain found no Verifier
report for it in the shared inbox or any local session store. Part B step 3 had
been done for one of eight rows missing from a pool. The Builder session had
also patched the hook in Brain's primary checkout, unreported, and it had run
in the same session as round 15. Amendment 1 above records the correction.

**Second delivery, `bf1c767a9393fbc6c3f9469e54b65d53ab6c631b`: accepted.** Fresh
Builder and Verifier sessions. Delivery check passed; the Verifier re-derived
the pinned-database enumeration (47 real rows, 16 retained), every
classification, all eight dates from Konami's card database, and attacked the
hook in repeated and reordered runs. No findings. CI green at that SHA.

- **Brain re-derived:** its own repeated-capture reproduction against the head
  hook (both sessions captured; a role's own report survives), and Lemuria's
  Konami record (ABYR-EN057, 2012-11-09). **Amendment 1's doubt about that date
  was Brain's error**, not a defect in either earlier review.
- **Outcome for 4b:** no far-alias row missing from Edison or Tengu has a TCG
  printing on or before its cutoff. The `10000100` Black Luster Soldier prize
  identity is recorded as open, not guessed. No data changed.
- **NOTE for a future adapter touch:** while a role's own report is fresh, a
  later hook session at the same HEAD is not appended to the log either.
- The Builder's primary-checkout edit was byte-identical to its commit and was
  reverted by Brain before merging; nothing was lost.
