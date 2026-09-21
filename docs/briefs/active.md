# Active brief

Status: **active — delivered once, returned for correction (Amendment 1 below)**.

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

---

## Amendment 1 — 2026-09-21, after Brain's first adjudication

The first delivery, `1733d7c8c0450d7c736794094cba5ce416ad6739` on
`builder/per-card-activation-dates`, was **not accepted**, because the
repository is not valid at that head: `validate` reports five
`format.erratum-implementation-gap` errors, `build --check` refuses to build,
the suite fails, and CI is red.

**The historical work stands and is not reopened.** The Verifier confirmed each
of the five bounds against the card's own period entry, and Brain independently
re-fetched the Fusion Sage capture (HTTP 200, memento 2008-12-16 16:23:13 GMT)
and read: "You cannot activate 'Fusion Sage' if you do not have any copies of
'Polymerization' in your Deck." The records keep everything they cited before.

**The failure is this brief's defect, not the Builder's.** Bounding the
activation axis makes state `c1` (activation new, verification still old)
determinate at the Edison snapshot for five records, and the validator requires
a determinate state with no implementation to be acknowledged on the record.
The brief forbade touching coverage, so a valid delivery was impossible. This
amendment removes that conflict.

### Now authorized, for exactly these five records

Freed the Matchless General, Fusion Sage, Horus the Black Flame Dragon LV4,
Thunder Dragon, Toon Table of Contents:

1. **Acknowledge the gap for state `c1`** using the project's existing
   mechanism — coverage `known-gap` with a stated reason — the same way the
   existing acknowledged divergences are recorded. The reason must be true and
   specific: say what the modern implementation reproduces and what it does not.
   Brain's reading, to be checked rather than copied: the modern script already
   enforces the new activation requirement, and what it cannot reproduce is the
   old procedure of letting the opponent verify the Deck.
2. **Establish what Edison actually ships for each of the five, before and
   after.** Previously these records were ambiguous at the snapshot; say what
   the build selected then and what it selects now, and whether that is more or
   less historically faithful.
3. **Re-pin only what legitimately moves** — Edison's divergence and warning
   counts, any Edison hash, any `dist/` output — regenerating `dist/` with
   `python -m retroformats build`. For every test you re-pin, give the old
   value, the new value, and the one-line reason it moved.

Not authorized: any other record, any validator or schema change, any
implementation strategy other than acknowledging these five gaps, any custom
script.

### Gates must be green

The delivery must have `validate` at 0 errors, `build --check` clean, the full
suite passing, and CI green at the head. The GOAT hash `0x28E9FC02` and the
April 2005 and March 2010 banlist entry sets must still be unchanged.

**If a gate cannot be satisfied within the brief, stop and report — do not
push past it.** The first delivery bypassed the local pre-push check with
`--no-verify` to deliver red work. It was disclosed, and CI caught it, but the
right move when the brief and a gate conflict is to stop and say so.

### Unchanged

Continue on the same branch from `1733d7c`; do not rewrite history. The report
covers the whole round from base `b5a5c0065c8179e80b23998f9455976fda9796d0`,
with every changed record's base and head versions side by side.
