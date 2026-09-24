# 029-edison-historical-scripts: First Edison historical scripts

Tier: 2
Mode: implementation
Supersedes: 027-2026-09-22-edison-historical-scripts-slice, which was queued
in the retired `docs/briefs/active.md` and never started. Its task is
reissued here unchanged in substance. Only the mechanics changed, for
agentic-framework 3.0.0 (round 028).

## Goal

The first Edison cards play the way they did in 2010. This round builds the
path end to end:

1. a canonical record
2. a generated database row and script in `dist/`
3. Edison's list using the historical card
4. an engine test proving the behaviour

It uses that path for three cards. Breadth comes in later rounds; this one
proves the path is sound.

**Why this is next.** Edison ships the modern version of 87 cards whose 2010
behaviour differs. For 46 of them (`format.erratum-known-divergence`) the
historical state is already established. The only thing missing is an
implementation, because Project Ignis ships none, and that is the part this
project can close. The other 41 (`format.erratum-modern-known-wrong`) have an
undetermined historical version and are **out of scope**: there is nothing
definite to implement. Brain recounted both numbers from `validate` at
`main` when writing this brief.

## Context

Read before acting:

1. `AGENTS.md`: all project invariants, especially "historical truth and
   engine representability are separate axes", and the evidence table's
   rows for canonical data, `retroformats/` code and engine tests.
2. `docs/agents/FRAMEWORK.md` and `docs/agents/roles/worker.md` (the Builder
   holds the Worker contract).
3. `docs/roadmap.md` item 7.
4. `docs/architecture.md`'s card-identity section, which covers the reserved
   passcode range `600000000`–`699999999`.
5. `docs/research/ignis-goat.md` §4 and §6. They describe how Project Ignis
   ships historical cards: a cdb row aliasing the modern card, plus a full
   `c<passcode>.lua` script.
6. `docs/errata.md`.
7. `retroformats/model.py`, `retroformats/lflist.py` and
   `retroformats/validate.py`, wherever they handle the `custom-script`
   strategy and `format.erratum-known-divergence`.
8. `docs/engine-testing.md` and `tests/engine/`.

Not worth reading: the rest of `docs/research/`, beyond the cited sources of
the cards you consider.

### Card selection

Choose **three** cards from Edison's 46 known-divergence records. For each
one, before writing anything:

- Quote the period card text the record already cites, with its source, and
  state the behavioural difference from the modern card in one sentence.
- If the difference is wording only and the modern script already behaves
  the period way, the card is not a candidate. Note it and choose another.
  Report every card you rejected and why; that is useful evidence.
- Prefer cards whose difference an engine test can observe directly.

Do not change any record's chronology or historical state. If a record's
evidence looks wrong to you, stop on that card and report it. Do not fix it
in this round.

### Required investigation

1. **Licence.** This project is MIT-licensed, and Project Ignis's scripts are
   the obvious starting point for a historical script. Establish the licence
   of ProjectIgnis/CardScripts at the pinned revision, from its own licence
   file. Establish whether a script derived from one can be distributed in
   this repository's `dist/` under this project's licence. If it cannot, or
   it is unclear, **stop before committing any derived script** and report
   what the licence says; that is an owner decision. A script written from
   scratch against the engine's API is the alternative. Say which you did.
2. **Identity.** How a generated row is identified in the duel (as an alias
   of the modern card) and in deck building, so that the historical card
   counts as the same card for banlist limits. Also, how the validator's
   existing `card.reserved-passcode-collision` check applies to the new
   codes.
3. **Output layout.** Where the generated database and scripts go in `dist/`,
   so that an EDOPro client using this repository finds them, matching
   `docs/research/ignis-goat.md` §4 and `dist/README.md`. Generation stays
   standard-library only (`sqlite3` is).

## Scope and non-goals

In scope:

- The generator (roadmap item 7), inside `retroformats/` and wired into
  `python -m retroformats build`, so that `build --check` catches drift.
- The three cards' canonical records: an implementation using the
  `custom-script` strategy and a reserved passcode, recorded however the
  existing model expects.
- Generated `dist/databases/` and `dist/scripts/` output, never hand-edited.
- One engine test per card, in `tests/engine/`, that fails with the modern
  script and passes with the generated one. The CI engine job's required
  count rises accordingly. That rise is expected and is not a weakening.
- Tests for the generator itself, including one that fails if a generated
  script or row is missing or stale.
- Brief documentation of the path, where `docs/errata.md` or
  `docs/roadmap.md` item 7 describe it.

Non-goals:

- No change to GOAT or Tengu output. The GOAT hash `0x28E9FC02` must not
  move.
- No card beyond the three. No change to any chronology, and no
  `modern-known-wrong` card.
- No new dependency. No change to what the existing CI `check` job runs.

## Invariants

- **History and representability stay separate** (`AGENTS.md`). A card's
  record says what was true in 2010, and the script is an implementation of
  that. A script that only approximates the period behaviour must say so on
  the record, not be presented as exact.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`).
- **Validator** (`AGENTS.md` evidence table): 0 errors. The warning count
  falls by exactly the number of known-divergence cards resolved. Explain
  every warning that appears, disappears or changes.
- **GOAT parity** (`AGENTS.md`): if the hash moves, stop and report.

## Acceptance criteria

- Three Edison cards resolve to generated historical cards in
  `dist/lflists/2010-03-edison.lflist.conf`, each with a generated database
  row and script, and `build --check` is clean.
- For each card, an engine test fails with the modern script and passes with
  the generated one. This is shown in CI, because the engine does not build
  on Windows, with run URLs.
- The GOAT hash is unchanged, and the GOAT and Tengu lists are
  byte-identical to base.
- The licence question is answered from the licence file itself.

**When to stop:**

- The licence does not clearly allow distributing a derived script here.
- A card's period behaviour cannot be stated from its record's own sources.
- The engine cannot express the period behaviour without an approximation
  you cannot bound. Record that card as rejected and choose another. If every
  remaining candidate hits this, stop and report.

## Required evidence

- `python -m retroformats validate`: the counts, with each warning change
  explained.
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`
- The CI run at your final head, with the engine job's executed/skipped line.
- For each card: the red run (modern script) and the green run (generated
  script), with URLs.
- The Edison list diff.
- The licence file's relevant passage.

Scratch commits made to show a red CI run are fine, as long as they are
reverted on the branch and the net diff is free of them.

Your report (`docs/rounds/029-edison-historical-scripts/builder.md`) has the
Worker card's sections. Under Verified and Open questions it must also give:

- the licence finding, and whether the scripts are derived or original
- for each chosen card: the period text and source, the behavioural
  difference, its passcode, and its red and green runs
- every rejected candidate, and why
- how identity and deck limits work for the new codes
- the validator warning changes
- what the generated scripts still do not reproduce
