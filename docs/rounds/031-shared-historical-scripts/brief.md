# 031-shared-historical-scripts: Historical scripts for cards shared by Edison and Tengu

Tier: 2
Mode: implementation
Supersedes: none

## Goal

A batch of cards plays as it did in 2010–2011 in **both** Edison and Tengu,
using the generated-card path rounds 029–030 built. Each card is a generated
database row plus an original script, and an engine test proves it. This
round is about breadth: the path exists and is not to be redesigned.

**Why this is next.** At `main`, `validate` reports 44 Edison
`format.erratum-known-divergence` warnings. For 38 of those cards the record's
historical state also applies at Tengu's snapshot (2011-09-17); Tengu has
exactly those 38 and no others. Brain recounted both numbers from `validate`
at `main` when writing this brief. Until now, scripting any of the 38 was
blocked because it would change Tengu's list. **The owner decided on
2026-09-24 that Tengu's list may change** for a card whose record says its
historical state applies there (`docs/state.md`, card scripts and licence).

## Context

Read before acting:

1. `AGENTS.md`, `docs/agents/FRAMEWORK.md`, `docs/agents/roles/worker.md`.
2. `docs/state.md`, section "Owner decision — card scripts and licence".
3. `docs/roadmap.md` item 7 and `docs/errata.md` "Generated historical
   cards". These describe the path and its two known hazards: the Tengu
   coupling, now allowed, and GOAT's structural parity walk.
4. `docs/rounds/029-edison-historical-scripts/` and
   `docs/rounds/030-edison-two-historical-scripts/`: briefs and all reports.
   029's rejection is the reason for the licence rule below.
5. `retroformats/custom_cards.py`, the `custom-card.*` rules in
   `retroformats/validate.py`, `data/custom-cards/`, and
   `tests/engine/test_edison_historical_scripts.py` as the pattern to follow.
6. `docs/engine-testing.md`.

Not worth reading: `docs/research/` beyond the cited sources of the cards you
consider.

**Do not open or read any Project Ignis card script.** This covers
`official/`, `pre-errata/` and any other script for any card you consider.
You may run Ignis's scripts in the engine as the modern side of a
comparison. You may read the engine's shared API files (`constant.lua`,
`utility.lua`, `proc_*.lua`), which round 029 also used.

## Card selection

Choose **six** cards from the 38 shared ones. At least three is acceptable if
candidates are rejected; do no more than eight. For each card, before
writing anything:

- Quote the period text the record already cites, with its source. State the
  behavioural difference from the modern card in one sentence. Confirm from
  the record's own chronology that the same historical state applies at both
  Edison's snapshot (2010-04-24) and Tengu's (2011-09-17).
- **Reject** a card if any of these hold:
  - the modern script already behaves the period way (the difference is
    wording only)
  - the observable difference depends on behaviour its record's sources do
    not establish
  - the engine cannot express the difference without an approximation you
    cannot bound
- Prefer cards whose difference an engine test can observe directly and
  simply. Prefer cards with no existing entry in Project Ignis's GOAT list;
  see the GOAT hazard in `docs/errata.md`.
- Report every card you considered and rejected, and why.

Do not change any record's chronology, historical state, sources or review
fields. If a record's evidence looks wrong, stop on that card and report it.

## Scope and non-goals

In scope:

- The chosen cards' `data/custom-cards/` records and scripts. Passcodes
  start at `600000004`: `600000003` stays unassigned, held for Night
  Assailant.
- The erratum records' coverage changes, following 029/030's pattern.
- Where a card needs one to keep GOAT unchanged, an exact
  `reference_identities` entry, citing a fact the repository already holds.
- Regenerated `dist/`, both lists included.
- One engine test class per card: the modern behaviour and the generated
  behaviour in the same scenario, plus a control where useful. Raise the
  CI engine floor by exactly the tests added.
- Updates to the test pins that track the Edison and Tengu lists and the
  corpus counts. As in 029/030, every pin must still assert the old value,
  reconstructed from the new one, and nothing may be loosened.
  `tests/test_migration_materializer.py` pins exact expected content for
  each edited record, as round 030 set up.
- `docs/roadmap.md` item 7, `docs/errata.md`, `dist/README.md` and
  `docs/engine-testing.md`, updated to say what is now true.

Non-goals:

- No change to the generator, validator rules or harness, except a small,
  reported fix for a defect you hit. Stop and report anything bigger.
- No Night Assailant. None of the five intermediate-state Edison-only cards.
  No card outside the 38.
- No GOAT change. The GOAT hash `0x28E9FC02` must not move. If it would,
  drop that card or give it the exact reference identity; never re-pin.
- No new dependency. No change to what the CI `check` job runs.

## Invariants

- **Licence** (`docs/state.md`): every script is original. It is written
  from the record's period text and the engine API, never adapted from a
  Project Ignis script, and its `authorship` note says how it was written.
- **History and representability stay separate** (`AGENTS.md`). Each
  record's `not_reproduced` names everything the script assumes beyond its
  sources, and `fidelity` says `approximate` unless it is exact.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`).
- **Validator:** 0 errors. For each card, one Edison and one Tengu
  `format.erratum-known-divergence` warning go. A GOAT
  `format.parity-omits-historical` warning may appear for a card whose state
  applies at 2005-04-01 and that Ignis's GOAT list does not substitute, as
  for Metalzoa and Stealth Union. Explain every other change line by line
  against `main`.

## Acceptance criteria

- Each chosen card resolves to its generated code in both
  `dist/lflists/2010-03-edison.lflist.conf` and
  `dist/lflists/2011-09-tengu.lflist.conf`, with the modern card's count in
  each list. No other line in either list changes. `build --check` is
  clean.
- The GOAT list is byte-identical to `main`, and its hash is unchanged.
- For each card, an engine test fails when the generated script behaves
  like the modern card, and passes at head. Show this with CI runs; scratch
  commits made for red runs are fine if they are reverted on the branch.
- CI is green at your final head, with the engine job's
  `executed=… skipped=0` line.

**When to stop:** fewer than three of the 38 qualify, or a card's historical
state is not the same at both snapshots after all.

## Required evidence

- `python -m retroformats validate`: counts, and a sorted warning-line diff
  against `main`.
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`: the count and skips.
- `python scripts/engine_env.py prepare`, then `run --expect-at-least N`,
  on macOS or Linux.
- The CI run URL at your final head, and a red run URL per card.
- `git diff main HEAD -- dist/lflists/`: every changed line.
- The old and new hashes for the Edison and Tengu lists.

Your report (`docs/rounds/031-shared-historical-scripts/builder.md`) has the
Worker card's sections. Under Verified it also gives, for each chosen card:

- the period text and its source
- the behavioural difference
- the passcode
- the chronology showing the same state at both snapshots
- the red and green runs
- what the script does not reproduce

Give every rejected candidate, with the reason.
