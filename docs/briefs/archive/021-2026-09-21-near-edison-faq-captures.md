# Active brief

Status: **accepted** (see Outcome).

Identifier: **`021-2026-09-21-near-edison-faq-captures`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (020 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — invariants, especially evidence before
   confidence and evidence being added to rather than replaced.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.
4. The archived brief
   [`020-2026-09-21-per-card-activation-dates.md`](archive/020-2026-09-21-per-card-activation-dates.md)
   with its Outcome, and the per-card table that round added to
   [`docs/research/edison-behaviour-gaps.md`](../research/edison-behaviour-gaps.md).
5. [`docs/format-schema.md`](../format-schema.md) on bounded intervals and
   state coverage.

Do not read the rest of `docs/research/`.

---

## MODE: HISTORICAL RESEARCH, with a data change explicitly authorized

## Goal

For the 33 records round 20 left ambiguous, establish whether Konami's Card FAQ
pages as captured **between the 2008-12-16 captures already read and the months
around the Edison snapshot (2010-04-24)** settle any card's activation state at
Edison — and record whatever the evidence supports. An evidenced "this source
family settles none of them" is a complete result and closes this line of work.

## Why this is next

Round 20 read the 2005 UDE replay and the 2008-12-16 Konami FAQ pages. A 2008
capture can only ever prove the *new* rule held by then. A capture from
2009–2010 that still shows the *old* rule for a card would prove the old rule
held at or near Edison. That matters more: those cards already have an
old-state implementation, so an old-state bound can change what the Edison
build actually selects, not only how the record is described. Nothing yet
establishes whether later captures exist for these pages, or whether they say
anything different; that is the question.

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Required investigation

1. **Establish what captures exist** of the Konami Card FAQ pages
   (`yugioh-card.com/en/gameplay/faqs/cardfaqs/default_*.html`) after
   2008-12-16 and up to about the end of 2010. Say how you enumerated them and
   what you found; if the archive's index cannot be queried, say so and what
   you did instead.
2. **For each of the 33 records, find its own entry** in those captures, and
   record the passage and served memento timestamp. Note in particular any
   entry whose text changed from the 2008-12-16 capture, and any entry that now
   addresses activation with nothing valid to find.
3. **Bound only what the evidence supports**, as in round 20: an old-state
   passage moves `old_attested_through` later; a new-state passage moves
   `new_attested_from` earlier; a capture date is never an effective date; one
   card's entry never dates another card.
4. **For every record whose Edison state becomes determinate, state what the
   Edison build selects before and after**, and whether that makes the shipped
   behaviour more or less historically faithful.

## Scope and authorization

- `data/errata/*.json` for records in the 33: chronology bounds, their
  citations and notes.
- **Coverage for a newly determinate state is authorized**: acknowledging a
  known gap with a true, specific reason, or pointing at an implementation the
  record already lists as covering that state. Nothing else about coverage or
  implementation strategy.
- `data/sources.json`, `docs/research/edison-behaviour-gaps.md`.
- `dist/` only by `python -m retroformats build`.
- Tests: only re-pinning values a legitimate data change moves, each with old
  value, new value and reason.

## Non-goals

- Records outside the 33, the five round 20 settled, and the
  deck-verification bracket.
- Sources other than the Konami Card FAQ page family. Other families
  (per-set rulings, judge materials, forum rulings) are a later decision.
- Custom scripts, validator or schema changes.

## Protected invariants

- Evidence before confidence; evidence added to, never replaced.
- GOAT hash `0x28E9FC02` unchanged; April 2005 and March 2010 banlist entry
  sets unchanged. Any Edison output change explained record by record.
- **Gates green at your head**: `validate` 0 errors, `build --check` clean,
  suite passing, CI green. If a gate cannot pass within this brief, stop and
  report; do not push past a check.

## When to stop

- If no captures of the FAQ pages exist in that window, or none of them changes
  any of the 33 records' state, record the search exactly and stop: that closes
  this source family.
- If a card's entry is ambiguous about activation, leave it and say why.

## Acceptance criteria

- The capture enumeration method and result stated.
- Every one of the 33 accounted for: changed with a quoted, time-stamped
  passage from its own entry, or unchanged with the reason.
- Every newly determinate record's Edison selection before and after, stated
  and reproducible.
- Every changed record's base and head versions side by side.
- All gates green.

## Required evidence

`python -m retroformats validate`, `build --check`, `report`, and
`python -m unittest discover -t . -s tests -v`, with real output and exit
status on Python 3.10 or newer. For every bound: URL, served memento timestamp,
passage. GOAT hash and both banlist entry sets confirmed unchanged.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/near-edison-faq-captures` from `origin/main`.
Focused commits; push the branch; never push `main`; never merge; never bypass
a local check. Before finishing, run
`git -C /Users/leo/Dev/edopro-retro-formats status --short` and confirm it
prints nothing. After your final commit and push, write your report from
inside `.worktrees/builder/` with
`python3 tools/report.py write --task 021-2026-09-21-near-edison-faq-captures`
(Python 3.10+), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus: how captures were enumerated and what
exists; a table with one row per record in the 33 (card, erratum id, entry
found and served timestamp, passage, bound before and after, Edison state and
Edison selection before and after); and every changed record's base and head
versions side by side.

---

## Outcome — accepted 2026-09-21, merged with owner approval

Head `9f3505ab51958f48b209148d01d5cf41288afc93`, base
`ff48d1f4312f1252f233a80bc558fa3a1dae4a4b`; accepted on the first delivery.

**Complete negative result.** The 12 HTTP-200 captures of the Konami Card FAQ
pages after 2008-12-16 repeat the 2008 content; none supplies an
activation-with-nothing-to-find ruling for any of the 33 records. No canonical
record changed. **This closes the Konami Card FAQ source family** for the
38-card cluster: 5 settled (round 20), 33 remain ambiguous with reasons
recorded per card.

**Accepted with one SHOULD FIX, carried into round 22:** the research text says
there were no 2009-2010 captures after the January rows. The timemaps also list
HTTP-302 rows through April 2009 (Brain confirmed: `default_ac` 2 × 200 and
4 × 302, last 2009-04-15; `default_st` 2 × 200 and 3 × 302, last 2009-04-29),
which redirect to non-FAQ pages. No conclusion changes, but a search
description must say what was actually searched.
