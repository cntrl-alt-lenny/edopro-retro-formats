# Active brief

Status: **queued, not started**.

Identifier: **`020-2026-09-21-per-card-activation-dates`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (019 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — topology, the non-negotiable project
   invariants (especially evidence before confidence, and evidence being added
   to rather than replaced), and the evidence table.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.
4. The archived brief
   [`018-2026-09-20-search-activation-semantics.md`](archive/018-2026-09-20-search-activation-semantics.md)
   including its Outcome, and the section of
   [`docs/research/edison-behaviour-gaps.md`](../research/edison-behaviour-gaps.md)
   that round added.
5. [`docs/format-schema.md`](../format-schema.md) on how an erratum records a
   bounded interval (`old_attested_through` / `new_attested_from`).

Do not read the rest of `docs/research/`.

---

## MODE: HISTORICAL RESEARCH, with a data change explicitly authorized

This brief **authorizes changes to canonical errata records**, which the
research mode otherwise forbids — but only the ones described in Scope, and
only where a cited period source supports them.

## Goal

For the 38-card "search and reveal-on-failure" cluster, bound each card's
**activation-semantics** change as tightly as period per-card evidence allows,
and record those bounds on the canonical errata records — so that some of these
cards stop being ambiguous at the Edison snapshot, or are shown to remain so
with the reason stated.

## Why this is next

Round 18 established that no period source states one policy for the whole
class, and that period Konami and UDE FAQ pages *do* record per-card activation
rulings: a 2008 Konami Card FAQ capture treats Reinforcement of the Army and
Release Restraint differently on the same page. Those pages are organised by
card, so they can be read card by card. That makes this the first round since
the framework adoption whose output is a change to the project's historical
data, which is the work the roadmap exists for (item 1a).

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Required investigation

1. **Derive the population from the repository**: the cluster round 18 used,
   and for each record, the current state of its activation-semantics change
   (dated, bounded, or undated). State the count.
2. **For each card, look for its own entry** in period per-card rulings
   sources — at minimum the archived UDE card-rulings pages and the archived
   Konami Card FAQ pages, which are split across several alphabetical pages;
   use per-set rulings documents where a card has one. Record, per card, what
   each source says about activating with nothing valid to find, and the
   served archive timestamp of the capture you read.
3. **Turn only what the evidence supports into a bound.** A capture showing the
   old behaviour moves `old_attested_through` later; one showing the new
   behaviour moves `new_attested_from` earlier. A capture date is evidence of
   state at that date — never an effective date. A card with no entry stays as
   it is.
4. **State the effect at the Edison snapshot (2010-04-24)** for every record
   you change: determinately old, determinately new, or still ambiguous. Run
   the validator and the report to show it.

## Scope

- `data/errata/*.json` — only the activation-semantics chronology bounds, their
  source citations and notes, for records in the cluster.
- `data/sources.json` — records for every source you cite, stating what each
  does and does not establish.
- `docs/research/edison-behaviour-gaps.md` — the per-card findings.
- `dist/` — only by regeneration with `python -m retroformats build`, if the
  data change moves any generated output.

## Non-goals

- Do not change the deck-verification axis's bracket; round 10 settled it.
- Do not change any record's `implementation` strategy or coverage, write
  custom scripts, or touch records outside the cluster.
- Do not infer one card's date from another card's entry, however similar the
  script or wording. That is exactly the generalisation round 18 could not
  support.
- No validator, schema or test change, except updating a pinned count or hash
  that a legitimate data change moves — and then say which, and why the old
  value no longer holds.

## Protected invariants

- **Evidence before confidence** (`AGENTS.md`): a capture date is not an
  effective date; absence of an entry is not evidence of either state.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`). Every
  changed errata or source record keeps what it already cites.
- GOAT hash `0x28E9FC02` must not move. The April 2005 and March 2010 banlist
  entry sets must not change. If anything else in `dist/` moves, explain why
  from the data change.
- Validator baseline 0 errors, 569 warnings. Any change in the warning count is
  a finding to explain, not noise.

## When to stop

If a card's entry is ambiguous about activation — for example it describes
verification but not whether activation is allowed — record it as ambiguous and
do not bound it. If more than a handful of cards turn out to need a judgement
call, stop, finish the clear cases, and list the rest.

## Acceptance criteria

- Every one of the population's records is accounted for: bounded more
  tightly with a cited, time-stamped passage, or left unchanged with the
  reason.
- Every new or moved bound traces to a specific quoted passage from a specific
  served capture of that card's own entry.
- The Edison-snapshot effect is stated per changed record and reproducible with
  the validator and report.
- For every changed record, its base and head versions compared side by side.

## Required evidence

`python -m retroformats validate`, `python -m retroformats build --check`,
`python -m retroformats report`, and `python -m unittest discover -t . -s tests -v`,
with real output and exit status, on Python 3.10 or newer. For every bound: the
URL, the served memento timestamp and the passage read. The GOAT hash and both
banlist entry sets confirmed unchanged.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/per-card-activation-dates` from `origin/main`.
Focused commits; push the branch; never push `main`; never merge. Before
finishing, run `git -C /Users/leo/Dev/edopro-retro-formats status --short` and
confirm it prints nothing. After your final commit and push, write your report
from inside `.worktrees/builder/` with
`python3 tools/report.py write --task 020-2026-09-21-per-card-activation-dates`
(Python 3.10+), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus a table with one row per card in the
population: card, erratum id, activation bound before, bound after, source and
served timestamp, quoted passage, Edison-snapshot state before and after. Then
the list of cards left ambiguous and why, and every changed record's base and
head versions side by side.
