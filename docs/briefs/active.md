# Active brief

Status: **queued, not started**.

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

## MODE: DATA/SCHEMA

## Goal

Resolve roadmap item 1e: Mind Master's TCG-vs-OCG card-identity gap.
Right now the Edison pool references passcode `96782886` (the canonical
row, which BabelCDB scopes OCG-only, `ot=1`) for a card whose actual TCG
printing (TDGS-EN016) EDOPro represents as a *separate* upstream entry
(`96782896`, `ot=2`, aliased to the canonical code). A TCG-format pool
referencing an OCG-only-scoped code is a card an EDOPro official-cards
room would reject. This is currently a single documented, allowlisted
exception in a test (`tests/test_repo_data.py::test_pool_cards_are_tcg_scoped_in_the_card_database`)
— not silently broken, but not actually fixed either. The goal is a
*general* rule for choosing the region-correct implementation of a
canonical card when release data maps a printing to a passcode BabelCDB
scopes for the wrong region — not a one-off patch that only happens to
fix Mind Master.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report.

## Why this is next

Three rounds so far (see `docs/agents/model-notes.md`) were all banlist
*verification* — bounded, single-file, no design decisions. This is
qualitatively different: it's a real card-identity/schema question the
roadmap explicitly says "needs a general rule," not a data-entry check.
Picked over roadmap 1a (125 undated-era-ruling records — much larger,
open-ended, needs period rulings documents that may not exist) as a
better-bounded next step: this has exactly one known instance today, a
concrete root cause, and an existing test that already names the
invariant it should eventually enforce without exception.

## Relevant context

Read:

- `docs/roadmap.md` item 1e (the paragraph starting "**Card identity:
  TCG-versus-OCG entries.**") — the problem statement as already
  diagnosed. Don't re-diagnose from scratch; verify it's still accurate
  against current data first (see "Required investigation").
- `tests/test_repo_data.py::test_pool_cards_are_tcg_scoped_in_the_card_database`
  — the current allowlist-based test and its docstring explaining the
  exact mechanism (BabelCDB's `ot` bitfield, `SCOPE_TCG = 0x2`).
- `docs/architecture.md`'s "Card identity model" section — canonical
  card / artwork variant / historical implementation definitions, and
  how the card index (`data/cards/index.json`) is generated.
- `retroformats/importers/card_index.py` — how the index is built from
  BabelCDB; this is almost certainly where any general fix needs to live
  (or a new importer step), since the index is generated, never
  hand-edited.
- `data/releases/` around how a printing maps to a canonical passcode
  (`docs/releases.md`) — the actual point where TDGS-EN016 gets mapped to
  `96782886` today; understand this before proposing a fix, since the fix
  might belong here instead of (or in addition to) the card index.

You do not need to read Tokyo Dome, Edison rules, or erratum v2 material
— unrelated to this task.

## Scope

1. **Confirm the gap still exists exactly as described.** Check
   `data/cards/index.json` (or regenerate it) for both `96782886` and
   `96782896`'s current `ot` values, and confirm the Edison pool really
   does reference `96782886`. Report if anything has already changed
   since the roadmap paragraph was written.
2. **Design the general rule**, not just a Mind Master patch. The core
   question: when a printing maps to a passcode whose BabelCDB `ot` scope
   doesn't include the format's own region, what should happen —
   automatically substitute the correctly-scoped upstream alias if one
   exists (like `96782896` here), flag it as a hard validator error
   requiring an explicit per-format override, something else? Consider
   at least two real approaches and their tradeoffs (a hand-search of
   whether other pool cards could hit this same class of gap in the
   future would strengthen whichever choice you make, but isn't required
   if it would blow the scope of this round — say so if you skip it).
3. **If a clear best approach exists, implement it** — likely touching
   `retroformats/importers/card_index.py` and/or the release-to-passcode
   mapping logic, plus removing Mind Master from the test's
   `known_exceptions` allowlist once it's genuinely fixed (the test
   should then pass with an empty exception set, or you've proven the
   general rule doesn't fully close this one case and should say so
   plainly rather than leave the exception silently in place while
   claiming the round succeeded).
4. **If the right general rule is genuinely ambiguous** (multiple
   reasonable designs with real tradeoffs and no clear winner from the
   codebase's own conventions), do not unilaterally pick one — implement
   nothing structural, and instead report the options with tradeoffs for
   Brain/the human to decide. A wrong-but-shipped general rule is worse
   than a well-documented open decision, since it would apply silently to
   every future case, not just Mind Master.

## Non-goals

- Do not touch `dist/` directly — regenerate via `python -m retroformats
  build` if the fix changes generated output.
- Do not touch banlist completeness/verification data (rounds 1-3's
  territory) — unrelated to this task.
- Do not invent a fix for cards other than Mind Master unless your
  investigation in step 1/2 finds a second real instance in current
  data — don't design purely hypothetically beyond what the actual data
  needs.

## Protected invariants

- `tests/test_repo_data.py`'s other tests, and the full suite, must still
  pass.
- The card index remains generated-only (`docs/architecture.md`: "never
  hand-edited") — any fix must be a code/importer change that produces
  the corrected index, not a hand-patched `data/cards/index.json`.
- `python -m retroformats validate` and `build --check` must still pass
  with zero errors, matching the rest of this project's error/warning
  discipline (warnings are fine, errors are not).

## Required investigation

1. Regenerate or directly inspect `data/cards/index.json`'s current
   entries for `96782886` and `96782896` before assuming the roadmap
   paragraph's description is still accurate.
2. Read how `retroformats/importers/card_index.py` decides which BabelCDB
   row becomes the canonical index entry for a given passcode, and
   whether it currently has any region-awareness at all.
3. Check whether any other current pool entry (across all three
   canonical formats, not just Edison) has the same `ot`-scope mismatch
   the test's allowlist mechanism would currently be silently permitting
   if it existed — the test only checks `pool-goat-2005-ignis` and
   `pool-edison-2010`; consider whether `pool-tengu-2011` should be
   checked too and isn't currently.

## Acceptance criteria

- Either: a general rule is implemented, Mind Master resolves through it
  (not a hardcoded special case), and the test's exception allowlist
  shrinks to empty — or: a clear, evidenced writeup of 2+ real design
  options with tradeoffs, explicitly not decided, for Brain to take to
  the human.
- No new pool/format regressions — GOAT and Edison's generated lflists
  must remain exactly what they were before this round unless the fix
  legitimately changes which passcode a card resolves to (in which case
  say so explicitly and show the before/after).
- Full test suite, validator, and `build --check` all pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/` inside the
project folder — see `docs/agents/worktree-mechanism.md`) if running
locally alongside a Brain session. Fetch `origin/main` and branch from
there (e.g. `worker/mind-master-card-identity`). Do not merge to `main`
yourself. Do not push unless asked.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Whether the gap still matches the roadmap's description, and what you
  found when you checked `pool-tengu-2011` too.
- If implemented: the general rule you chose, why, what you rejected and
  why, exact files changed, and confirmation the test's allowlist is now
  empty (or explain what's still not fully resolved).
- If not implemented (ambiguous case): the real options considered, with
  concrete tradeoffs — not a vague "it depends."
- Exact output of the three validation commands.
- Anything left genuinely uncertain.
