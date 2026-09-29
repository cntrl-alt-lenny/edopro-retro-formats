# 037-text-only-errata-audit: Check the text-only "functional" errata records against period rulings

Tier: 2
Mode: research, then data and implementation
Supersedes: none

## Goal

At `main`, 105 errata records classify a later errata as a `functional`
change (one that altered how the card plays), yet cite no ruling-type
source on that change. Rounds 035 and 036 checked nine records of this
kind against period rulings, and found seven wrong or overstated.

These records decide what the lists ship. 72 of them have coverage
`reuse-upstream`, which makes Edison or Tengu use one of Project Ignis's
historical variant scripts in place of the modern card. So a wrong
`functional` call changes how a card plays in a shipped list, not just a
warning.

When this round is done:

- **A. A gate.** No record whose `functional` change applies at Edison's or
  Tengu's snapshot is left without a recorded rulings check.
- **B. Every record in scope has been checked** against the fixed corpus of
  period ruling sources below, with a verdict.
- **C. Corrections.** Records a period ruling contradicts are corrected,
  and records a ruling supports carry that ruling as evidence.
- **D. Round 036's leftover questions** are settled where evidence allows.

The owner wants large rounds with one review. Do the parts in the order A
to D, and put each part's evidence in the report.

## Scope: which records

Take every `data/errata/*.json` record at the start of the round that
meets all four conditions:

1. It has a transition of kind `functional`.
2. That transition cites no source whose `ruling_class` is set in
   `data/sources.json`.
3. Its first `functional` change takes effect after Edison's snapshot
   (2010-04-24), so it can affect Edison's or Tengu's list.
4. It is not linked to a generated card in `data/custom-cards/` (seven at
   `main`): the rulings gate already covers those.

Brain's count at `main` is 83 records: 61 `reuse-upstream`, 19 `known-gap`
and 3 `none-needed`. Re-derive it yourself, and say so if you get a
different number.

List the records the selection finds, with the method, before starting B.
GOAT-only records (a change before 2010-04-24) are out of scope: GOAT's
list is entry-for-entry parity with Ignis's, and does not read them.

**Order of work**, so that a round cut short still does the most important
part first:

1. `reuse-upstream` records, which change what a list ships
2. `known-gap` records
3. `none-needed` records

If the round runs long, finish a whole group, and report every group not
done as not done. A group done completely is better than all of them done
halfway.

## The search corpus

For each record, search these period sources. All are already in
`data/sources.json`.

- **The card FAQ.** The Konami-hosted copies of the UDE card FAQ, 2008-12
  to 2009-01, one page per letter range (`konami-card-faq-*`), and the
  UDE-hosted copy (`ude-card-faq-2009-02-26-uz`, `ude-card-rulings-archive`).
- **Konami's errata lists:** `konami-errata-list-2009-07-30`,
  `konami-errata-list-2010-01-05`, `konami-errata-list-2010-11-05`.
- **Konami's rulebooks:** `konami-rulebook-2008-v70`,
  `konami-official-rulebook-v71-2010`,
  `konami-official-rulebook-v72-2011-dragunity`,
  `konami-official-rulebook-v8-2011`.
- **Konami's per-set ruling documents**, linked from the Gameplay page
  captures `konami-gameplay-page-2010-03-22` and
  `konami-gameplay-page-2011-09-18`, and `konami-set-rulings-archive`.
- **UDE judge-list threads**, reached through Yugipedia's
  `Card_Rulings:<name>` pages via its MediaWiki API. Yugipedia is only a
  pointer: cite the archived thread, never the wiki line.

A source outside this corpus may be used when found, provided it meets the
same rules. Add it to `data/sources.json` with its `ruling_class`.

## Evidence rules

These are round 035's and 036's rules, and the owner's decision of
2026-09-29 (`docs/state.md`, "Period rulings"):

- **What counts.** A UDE-era ruling counts at Edison and Tengu unless a
  later Konami document replaced it. A Konami document current at the
  snapshot outranks an earlier UDE ruling on the same point.
- **What does not.** An OCG ruling is not a TCG one. A Yugipedia line is
  not a source. A ruling's date is not its range in force, except as the
  owner's decision provides.
- **Absence proves nothing.** No ruling found means `unresolved`, and the
  existing `functional` call stands. Printed text differences are real
  evidence of a text change. The question is only whether rulings show the
  card played differently.
- **Quote what you read.** Every verdict other than `unresolved` quotes the
  passage read, with the URL and the archive capture.

## A. A rulings check for errata records

Extend round 035's rulings gate to errata records. Every `functional`
transition that applies at Edison's or Tengu's snapshot must carry a
rulings check:

- the difference it claims, in one sentence
- the corpus sources searched, and what each found

Use the same finding values, `in_force` values and `owner_decision` rules
as `rulings_check` in `schemas/custom-card.schema.json`. Reuse the model
and validator code rather than copying it.

- **When to error.** The validator errors when a transition in scope has no
  check, or when a check records a contradicting ruling in force with no
  `owner_decision`.
- **How to introduce it.** Introduce it as a warning, turn it into an
  error only once every record in scope carries a check, and show it
  failing first both ways.
- **If the round is cut short**, the rule stays a warning, and the report
  says so. Then it is not an error for records nobody checked.

Document it in `schemas/erratum.schema.json` and `docs/errata.md`.

## B. Check every record in scope

For each record, first state the claimed difference. For a `reuse-upstream`
record, state what the substituted Ignis variant script actually does
differently from Ignis's modern script, from a `diff` of the two at the
pinned CardScripts revision; that is what the list ships. Then search the
corpus and give a verdict at each snapshot the record applies at:

- **`supported`:** a ruling in force says the card played the way the
  record claims.
- **`contradicted`:** a ruling in force says it played as the modern card
  does, or says the variant script is wrong on a point it implements.
- **`unresolved`:** nothing in the corpus addresses the difference.

Record every card in a new research document,
`docs/research/text-only-errata-audit.md`, including the unresolved ones,
with the sources searched. That is what makes a sample reviewable.

## C. Act on the verdicts

Follow round 035's part C, which rounds 035 and 036 applied:

- **`contradicted`, and the period behaviour matches the modern card.**
  Reclassify the transition `cosmetic`, with the ruling added as evidence.
  Keep every existing passage, and move the replaced summary into the
  review notes with the date and the reason. For a `reuse-upstream` record,
  the list then uses the modern card again. For a `known-gap` record, the
  divergence warning goes.
- **`contradicted` on one point of a variant script, with the rest still
  functional.** If the variant still implements a supported or unresolved
  difference, keep using it, and list the contradicted point for the owner.
  Do not edit Ignis's script, and do not write a replacement script in this
  round.
- **`supported`.** Add the ruling to the transition's sources and to its
  rulings check. Nothing else changes.
- **`unresolved`.** Record the search in the rulings check. Nothing else
  changes.

**Thin evidence goes to the owner.** Anything thin, or any conflict between
period sources, is the owner's call. Change no data for it, and list it in
plain product terms: what the card would do either way, and what each
rests on.

## D. Round 036's leftover questions

- **VW-Tiger Catapult:** did the era discard effect target? Search the
  corpus. If a ruling says it did not target, record the difference as a
  new `functional` transition in that record, with the ruling; it becomes a
  known gap. If a ruling says it targeted, add it as evidence of the
  cosmetic call. If there is no ruling, record the search.
- **Missing differences.** Round 036 found three supported differences
  that the erratum records do not list:
  - D.D. Survivor returning "during the next turn's End Phase"
  - two Dark Necrofear rulings: Tailor of the Fickle / Collected Power, and
    a negated Summon
  - a second Swap Frog copy

  Add each to its record as evidence, as a new transition only if the
  ruling shows play differed from the modern card, and give its state at
  each snapshot. No new generated card.
- **Machina Peacekeeper and Machina Gearframe:** search the corpus for the
  "unequip … in face-up Attack Position" clause. If a ruling in force
  supports it, change the two generated scripts to implement it, with an
  engine test red on the current behaviour. If there is no ruling, record
  the search on the cards' `rulings_check`.

## Scope and non-goals

What may change:

- `data/errata/` records in scope, the three records named in D, and
  `data/sources.json`
- the two Machina generated cards, for D only
- the model, the validator and the schema documentation, for A only
- tests
- regenerated `dist/`
- the hash and count pins, rebuilt so that every old value is still
  asserted where it can still be reached
- `docs/research/text-only-errata-audit.md` (new), and a pointer to it in
  `docs/research/period-rulings-generated-scripts.md`
- `docs/roadmap.md`, `docs/errata.md`, `dist/README.md`,
  `docs/engine-testing.md` and `formats/2011-09-tengu/notes.md`
- the CI engine floor, only by the net number of engine tests added in D

Non-goals:

- No new generated card, and no edit to any Ignis script.
- No change to generated cards other than the two Machina cards.
- Records outside the four scope conditions are left alone, apart from the
  three named in D.
- No GOAT change: the hash `0x28E9FC02` must not move. If it would, stop
  on that record.
- No change to what CI's `check` job runs, no new dependency, and no
  change to `docs/state.md`.
- Night Assailant stays held back. If the audit finds a ruling on its open
  questions (whether the effect was optional, whether it targeted), report
  it for the owner; do not ship it.
- Second Coin Toss stays as round 036 left it.

## Invariants

- **Epistemics** (`AGENTS.md`). No suite run is evidence for a historical
  claim.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`). An
  automated check covers every record changed this round, as
  `tests/test_migration_materializer.py` did for rounds 035 and 036.
  Extend it, and show it failing on a deleted passage.
- **No rule is loosened** (`AGENTS.md`). A's rule tightens.
- **The validator ends with 0 errors.** Explain every warning added or
  removed, line by line against `main`, grouped by code, with each count.

## Acceptance criteria

- The selection is listed with its method, and every group is marked done
  or not done.
- A's rule has a test that fails without it, both as a warning and as an
  error. It is an error only if every record in scope carries a check.
- Every checked record has a verdict at each snapshot it applies at, with
  the sources searched. Every non-`unresolved` verdict quotes its passage.
- Every record changed in C is listed with its diff against `main`, and
  the passages-kept check covers it.
- For every `reuse-upstream` record reclassified, the report shows the
  list line that moves back to the modern code, and a duel-engine check
  that the modern card is now used. One parametrised test over all of them
  is fine.
- The GOAT list is byte-identical to `main`. Every changed line in the
  Edison and Tengu lists is explained by a record in C or a card in D.
- CI is green at the final head, with the engine job's
  `executed=… skipped=0` line.

## Required evidence

- the selection script's output and the count per group
- `python -m retroformats validate`: counts, and a sorted warning-line diff
  against `main`, grouped by code
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`: the count and the skips
- `python scripts/engine_env.py prepare`, then `run --expect-at-least N`
- `python scripts/generate_format_atlas.py --check`
- `python3 tools/fw.py check`
- `git diff main HEAD -- dist/lflists/`: every changed line
- the old and new Edison and Tengu hashes
- the CI run URL at the final head, and a red run URL for any changed
  script
- the failing-first runs for A and for the passages-kept check

Your report (`docs/rounds/037-text-only-errata-audit/builder.md`) has the
Worker card's sections. Under Verified, it gives:

- a counts table: records checked per group, and verdicts per snapshot
- every record changed, with its verdict, action and source

Under Open questions, it gives the owner's thin-evidence list, in plain
product terms.
