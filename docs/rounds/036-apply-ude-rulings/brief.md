# 036-apply-ude-rulings: Apply the owner's period-rulings decision, correct the records it and round 035 settle, and ship new cards the rulings support

Tier: 2
Mode: data and implementation, with research for part D
Supersedes: none

## Goal

On 2026-09-29 the owner decided that a generated script follows period
rulings, not printed text alone. Under that decision, UDE-era card rulings
count at Edison and Tengu unless a later Konami document replaced them
(`docs/state.md`, "Owner decisions — card scripts").

When this round is done:

- **A. The gate** can record that decision.
- **B. The five cards** round 035 left open on it are settled.
- **C. The errata records** whose "functional" change round 035's class
  answer shows was never functional in play are corrected, so the lists
  stop claiming divergences that did not exist.
- **D. New cards.** Up to six more shared Edison/Tengu cards whose period
  behaviour a ruling supports now ship.

The owner asked for large rounds with one review. Do the parts in order,
and put each part's evidence in the report.

## Context

- `AGENTS.md`, `docs/agents/FRAMEWORK.md`, `docs/agents/roles/worker.md`,
  `docs/state.md`.
- `docs/research/period-rulings-generated-scripts.md` (round 035): the
  sources, the passages, and both class answers. §3 covers "can only be
  Special Summoned by", §4 the Damage Step, §5 the range of UDE rulings, and
  §6 each card. Its sources are already in `data/sources.json`.
- `docs/rounds/035-period-rulings-audit/`: the brief and both reports, for
  the pattern of a correction (reclassify, keep every passage, remove the
  generated card, retire its passcode, replace its engine tests with a
  modern-card test).
- The rulings gate: `rulings_check` in `schemas/custom-card.schema.json`,
  `docs/errata.md` ("The rulings gate"), `retroformats/validate.py`.
- Round 034's Dice Re-Roll and Second Coin Toss work: record, script and
  tests on `origin/builder/034-shared-scripts-batch-2`. Read it with
  `git show`; never push to that branch.
- On the owner's Mac, `python3` is 3.9. Use `/opt/homebrew/bin/python3.13`
  for project commands.
- Tooling note: Yugipedia's MediaWiki API and `web.archive.org` both
  answered in round 035. Yugipedia is only a pointer; cite the source it
  points to.

## A. Record the decision in the gate

Today a UDE ruling can only be marked `in_force: not-shown`, which leaves a
warning (`custom-card.contradicting-ruling-range-unresolved`). Make the
gate able to record that a finding is in force by the owner's decision:

- The validator accepts this only for a source that is a UDE-era ruling
  (design how a source is identified as one; `data/sources.json` is the
  place).
- The entry must say that no later Konami document found replaces the
  ruling on the same point, and name the Konami documents checked.
- A contradicting finding in force by decision still needs an
  `owner_decision`, exactly as one shown in force does. A decision about
  which rulings count is not a decision to ship a contradicted script.

Document it in the schema and in `docs/errata.md`. Show each new check
failing first. This tightens nothing and loosens nothing else.

## B. Settle the five cards

For each card, apply §6 of the research document under the decision, and
re-read the ruling at its source before acting:

- **Goddess of Whim** (`600000004`, merged). The 2008-12-15 FAQ says "once
  per turn", which matches the modern card. Correct it as round 035
  corrected Metalzoa.
- **Green Baboon, Defender of the Forest** (`600000006`, merged). The one
  remaining difference is the face-up requirement, which the UDE Netrep
  answer and the FAQ require, as the modern card does. If nothing else
  still differs from the modern card, correct it as above. If something
  does, say what, and keep only that.
- **Dark Master - Zorc** (no generated card). The UDE Netrep answer of
  2007-10-11 matches the modern card. Correct its errata record's
  classification, so that Edison and Tengu stop reporting a divergence.
- **Second Coin Toss** (no generated card). The UDE rulings limit it to
  your own tosses, and let each toss be redone once, even with several
  copies. Establish whether that differs from the modern card, which is
  once per turn by name, in anything an engine test can observe:
  - If it does not differ, correct the record.
  - If it does, the rulings describe a third behaviour. Ship a script for
    exactly that behaviour, starting from round 034's (passcode
    `600000017`), with a test showing that behaviour.
  - Otherwise, return the record to `known-gap`, with the rulings cited.
- **Dice Re-Roll** (`600000016`, round 034, unmerged). The FAQ supports a
  per-activation re-roll. Ship it from round 034's work, but test only
  what the rulings establish. Round 034's test scenario re-rolls an
  already re-rolled result, which no ruling covers; replace it if nothing
  supports it.

Super Vehicroid - Stealth Union and Strike Ninja had no ruling either way.
They stay as they are.

## C. Correct the records the class answers settle

Round 035's class answers are Konami documents current at both snapshots.
The rulebook v7.1/v8 revival rule and the Extreme Victory ruling cover
"can only be Special Summoned by". The rulebook's list of what may be
activated covers the Damage Step. Apply them across the errata corpus:

- **Correct as cosmetic.** Every record whose only functional change is
  one of those two, as round 035 corrected Metalzoa and Rise of the Snake
  Deity. This includes the five nomi cards round 034 proposed: Gigantes,
  The Rock Spirit, Garuda the Wind Spirit, VW-Tiger Catapult and Gladiator
  Beast Heraklinos.
- **Keep the other differences.** A record with one of those changes plus
  another keeps the other. Add the class evidence to its notes, and narrow
  its summary to what is still functional.
- **Stop when a card-specific ruling disagrees.** If a card-specific
  ruling or an exception disagrees with the class answer, stop on that
  record and list it.

Keep every existing passage. Move each replaced summary into the review
notes, with the date and the reason. Report every record you touched,
compared with `main`, and every record you looked at and left alone, with
the reason.

## D. New cards the rulings support

From the shared Edison/Tengu divergences `validate` reports at the start
of this round, excluding every card above and the nine round 031 excluded,
ship up to six cards:

- **Only `supported` cards ship.** A card ships only if its difference
  from the modern card is `supported` at both snapshots by a period ruling
  in force, under the decision in A. Printed text alone is not enough:
  round 035 found text-only readings wrong for twelve of sixteen cards.
- **Research is the work.** Record every card you examine, with the
  sources searched and what they found, in a new section of the research
  document, including the ones you reject.
- **Build as before.** Every shipped card follows rounds 031, 032 and 035:
  - `derived` from Ignis's script for its alias
  - a full `rulings_check`
  - passcodes from `600000018` upward
  - one engine test class under both formats, with a red run on a scratch
    branch
  - the lists changing only by the swap
- **Zero is a valid result.** If fewer than six qualify, ship those that
  do, and report the rest with their verdicts.

## Scope and non-goals

What may change:

- `data/errata/`, `data/custom-cards/` and `data/sources.json`
- `data/cards/index.json` (regenerated)
- the validator and schema documentation, for A only
- engine and unit tests
- the CI engine floor, which moves by exactly the net number of engine
  tests added and removed
- regenerated `dist/`
- the hash and count pins, rebuilt so that every old value is still
  asserted where it can still be reached
- `docs/research/period-rulings-generated-scripts.md` (add to it; delete
  nothing)
- `docs/roadmap.md` item 7, `docs/errata.md`, `dist/README.md`,
  `docs/engine-testing.md` and `formats/2011-09-tengu/notes.md`

This brief authorizes, for the cards corrected in B and C only:

- deleting a generated card
- retiring its passcode (never to be reused)
- replacing its engine tests with a test that the modern card is used

Non-goals:

- No GOAT change: the hash `0x28E9FC02` must not move. If it would, stop
  on that card.
- No change to the round-034 branches, and no new dependency.
- No change to what CI's `check` job runs, and none to `docs/state.md`.
- No reclassification in C on anything but the two class answers. The
  audit of the other text-only records is not this round.
- Night Assailant and the nine excluded cards stay out.

## Invariants

- **Epistemics** (`AGENTS.md`). The owner's decision covers UDE rulings'
  range in force, nothing else. It does not make a Yugipedia line a source,
  an OCG ruling a TCG one, or printed text a ruling. No suite run is
  evidence for a historical claim.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`).
- **No rule is loosened** (`AGENTS.md`). Every remaining generated card
  passes the gate.
- **Licence** (`docs/state.md`). Every script is `derived`, or passes the
  `original` gate.
- **The validator ends with 0 errors.** Explain every warning added or
  removed, line by line against `main`.

## Acceptance criteria

- A's checks each fail without their change.
- The three `contradicting-ruling-range-unresolved` warnings are resolved:
  by the corrections in B, or recorded as decided.
- Each card in B has:
  - its action
  - the ruling re-read at its source, with the passage quoted
  - for a shipped or changed script, an engine test red on the wrong
    behaviour and green at head, under both formats, shown with CI runs
- Every record corrected in C is listed with its diff against `main`, and
  every record examined and left alone with its reason. An automated check
  that every earlier passage is kept verbatim covers all of them. Round 035
  used one in `tests/test_migration_materializer.py`; extend it or add one.
- Every card shipped in D has a `supported` verdict at both snapshots
  resting on a quoted, in-force period ruling.
- The GOAT list is byte-identical to `main`. Every changed line in the
  Edison and Tengu lists is explained by a card in B or D.
- CI is green at the final head, with the engine job's
  `executed=… skipped=0` line.

## Required evidence

- `python -m retroformats validate`: counts, and a sorted warning-line diff
  against `main`, with each change explained
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`: the count and the skips
- `python scripts/engine_env.py prepare`, then `run --expect-at-least N`
- `python scripts/generate_format_atlas.py --check`
- `python3 tools/fw.py check`
- `git diff main HEAD -- dist/lflists/`: every changed line
- the old and new Edison and Tengu hashes
- the CI run URL at the final head, and a red run URL for each new or
  changed script
- for each derived script, its `diff` against the Ignis source

Your report (`docs/rounds/036-apply-ude-rulings/builder.md`) has the Worker
card's sections. Under Verified, it gives:

- a table of every card and record acted on in B, C and D, with the action
  and the source
- the D candidates you rejected, with their verdicts

Under Open questions, it gives anything that needs the owner, in plain
product terms.
