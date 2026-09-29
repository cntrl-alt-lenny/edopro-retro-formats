# 039-necrovalley-and-variant-fixes: Apply the owner's Necrovalley decision, and fix the shipped scripts that period rulings contradict

Tier: 2
Mode: data and implementation
Supersedes: none

## Goal

When this round is done:

- **A. Necrovalley** at Edison records the owner's decision of
  2026-09-29.
- **B. The scripts Edison and Tengu ship** no longer contradict a period
  ruling in force on any point round 037 found, wherever the ruling is
  clear and an engine test can show the difference. On each such point,
  the list uses a generated card that follows the ruling, in place of the
  Project Ignis script it ships today.
- **C.** Round 038's leftover defects are fixed.

The owner wants large rounds with one review. Do the parts in order, and
put each part's evidence in the report.

## Context

- `AGENTS.md`, `docs/agents/FRAMEWORK.md`, `docs/agents/roles/worker.md`,
  `docs/state.md` ("Owner decisions — card scripts").
- `docs/research/text-only-errata-audit.md`: section 5 has each record's
  verdicts, section 9 the script disagreements, and section 11 is round
  038. `docs/research/period-rulings-generated-scripts.md` covers rounds
  035 and 036.
- `docs/rounds/038-rulings-followups/`: both reports. The Verifier's
  Necrovalley finding is the background to A.
- The pattern for a generated card: rounds 031, 032, 035 and 036 (their
  briefs and reports under `docs/rounds/`), `data/custom-cards/`,
  `retroformats/custom_cards.py`, the `custom-card.*` rules in
  `retroformats/validate.py`, `tests/engine/test_shared_historical_scripts.py`
  and `tests/engine/test_script_origin.py`.
- On the owner's Mac, `python3` is 3.9. Use `/opt/homebrew/bin/python3.13`.
  Yugipedia's MediaWiki API and `web.archive.org` answer; Yugipedia is only
  a pointer.

## A. Necrovalley at Edison: the owner's decision

Round 038 applied rule 1 and narrowed Necrovalley's Edison claim on
Konami's Raging Battle ruling (compiled 2009-05-27). That ruling negates
Lava Dragon's non-targeting effect. It was written for the card's older
"affect" wording.

On 2026-09-29 the owner decided that, for Necrovalley at Edison, the TU02
reprint outranks that ruling. The reprint is `c0`, released 2010-01-09,
and its text negates only effects that "target" a card in the Graveyard.
It is Konami's later statement of the card's text in force at Edison's
snapshot. The 2008-12 FAQ line ("will NOT negate effects that do not
target") agrees with it.

So at Edison, Necrovalley negated only effects that target a card in a
Graveyard.

- **Restore the claims.** Restore that claim in `c0`'s and `c1`'s
  summaries and in the gap statements round 038 narrowed. Keep every
  passage round 038 added, and move each replaced summary into the review
  notes, with the date and the owner's decision.
- **Record the decision.** In the rulings check, the Raging Battle finding
  becomes a `contradicts` finding accepted by an `owner_decision` dated
  2026-09-29. Record that decision in the owner's terms: the later reprint
  of the card's own text governs over a ruling written for the earlier
  wording.
- **Keep the decision narrow.** It is about Necrovalley. Do not generalise
  it into a rule for other cards. If another card raises the same
  question, list it for the owner.
- **The list does not change.** Necrovalley stays a known gap at Edison.
  Say so, and show that no list line moves because of A.

## B. Fix the shipped scripts that a ruling contradicts

Round 037 listed twelve points where a script a list ships disagrees with a
period ruling (section 9 of `docs/research/text-only-errata-audit.md`).
Each script is either an Ignis variant the list substitutes, or Ignis's
modern script:

| card | script shipped today | the point |
|---|---|---|
| Armored Cybern | `pre-errata/c511003055.lua` | destroys even when the ATK cannot be reduced |
| Axe of Despair | `goat/c504700068.lua` | returns after its trigger missed timing |
| Big Shield Gardna | `official/c65240394.lua` | face-down checked at activation only |
| Blue-Eyes Toon Dragon | `goat/c504700086.lua` | Level 5 Tribute (no ruling) |
| Dark Magician of Chaos | `pre-errata/c511001039.lua` | Skill Drain stops the leave-field banish |
| Dark Strike Fighter | `pre-errata/c511000229.lua` | no Synchro revive limit |
| Future Fusion | `pre-errata/c511002997.lua` | contact-Fusion-only monsters selectable |
| Jirai Gumo | `goat/c504700190.lua` | odd Life Point rounding (ruling under another card) |
| Nutrient Z | `goat/c504700051.lua` | playable from the hand |
| Twin-Headed Behemoth | `pre-errata/c511000868.lua` | Skill Drain stops the revival |
| Diffusion Wave-Motion | modern, `official/c87880531.lua` | activatable against an empty field |
| Gaia Soul the Combustible Collective | modern, `official/c51355346.lua` | no once-per-turn limit |

**For each point, decide first.** Re-read the ruling at its archived
capture, and read the script at the pinned CardScripts revision. Then fix
the point only if all of these hold:

- A ruling in force at the snapshot addresses the point. That can be a
  UDE-era ruling under the owner's decision, or a Konami document. A
  ruling filed under another card, or a general rule, qualifies only if
  its words cover this card's case directly. Say which applies.
- The shipped script really does what the point says. Round 037 read
  several of these from the script text without running them, so confirm
  each one in the duel engine before fixing it.
- An engine test can show the difference under the format or formats that
  ship the script.

If not, record why in the research document and leave the card as it is.
Blue-Eyes Toon Dragon and Jirai Gumo are expected to fail the first
condition. Confirm that, or show otherwise.

**How to fix a point** (the pattern of rounds 031 to 036):

- **Start from the script shipped today**, and change only the ruled
  point. Every other behaviour of the shipped script stays, including the
  historical differences round 037 recorded for it.
- **Make it a generated card:**
  - `derived`, AGPL-3.0-or-later, crediting the upstream file it started
    from, with the full header
  - a record in `data/custom-cards/` with passcodes from `600000022`
    upward
  - a `rulings_check` covering every difference the script implements
    from the modern card: the variant's differences, with the evidence
    round 037 recorded, and the fixed point
  - `not_reproduced`
  - one engine test class that fails on the script shipped today and
    passes on the new one, under every format that ships it, with a red
    run on a scratch branch
- **The list swaps** the code it ships today for the generated code, with
  the same count. Nothing else in either list moves.
- **The errata record's coverage** moves to `custom-script`, for the
  states the generated card covers. Keep every passage, as rounds 035 to
  038 did.
- **If a gate is too narrow, tighten it; never loosen it:**
  - **The script-origin tie.** `custom-card.upstream-not-own-script`
    accepts only `official/c<alias>.lua` and `pre-errata/c<n>.lua`. Four
    of these start from `goat/`, and Big Shield Gardna from an `official/`
    file under another number. Extend the rule so that it accepts any
    CardScripts file whose own row in a pinned BabelCDB database aliases
    the card. Check the path shape offline, and the database tie in the
    engine tests, as round 034 did for `pre-errata/`. Show it rejecting a
    file tied to another card.
  - **The rulings check.** If `rulings_check` on a generated card holds
    only one difference, extend it to several, keeping every existing
    rule.
- **GOAT must not move.** Several of these cards are GOAT-era. The GOAT
  list is parity with Ignis's, and its hash `0x28E9FC02` must not move. If
  a generated card would enter the GOAT list, stop on that card and report
  it.

## C. Round 038's leftovers

- `tests/test_tengu_format.py`: `test_6_pool_is_exactly_4562_cards`
  asserts 4563. Rename it so the name says what it checks. The one-card
  difference is round 14's addition, recorded in `docs/roadmap.md`
  item 12.
- `data/sources.json`: none of the eight `konami-card-faq-near-edison-*`
  sources has a `ruling_class`, although they are later captures of the
  Konami-hosted UDE FAQ and the YZ-Tank Dragon check cites one. Confirm
  each is a copy of that FAQ. If it is, give it the class the 2008-12-15/16
  copies carry (`ude-era-ruling`); if not, say what it is. Check the
  validator is content.

## Scope and non-goals

What may change:

- `data/errata/` (Necrovalley, and the records of the cards fixed in B)
- `data/custom-cards/`, `data/sources.json` and `data/cards/index.json`
  (regenerated)
- the validator and the schema documentation, for the two gate extensions
  in B only
- engine and unit tests
- the CI engine floor, which moves by exactly the net number of engine
  tests added
- regenerated `dist/`
- the hash and count pins, rebuilt so that every old value is still
  asserted where it can still be reached
- the research documents (add; delete nothing)
- `docs/roadmap.md`, `docs/errata.md`, `dist/README.md`,
  `docs/engine-testing.md` and `formats/2011-09-tengu/notes.md`

Non-goals:

- No edit to any Ignis file. The generated card is the fix.
- No card outside the twelve, and no new historical difference. B fixes
  the ruled point only.
- No change to `docs/state.md`, to what CI's `check` job runs, or to the
  GOAT list. No new dependency.
- Night Assailant stays held back, and Second Coin Toss stays as it is.

## Invariants

- **Epistemics** (`AGENTS.md`). The owner's Necrovalley decision is about
  Necrovalley only. No suite run is evidence for a historical claim.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`).
  Extend the passages-kept check to every record changed here, and show it
  failing on a deleted passage.
- **No rule is loosened** (`AGENTS.md`). Both gate changes accept
  strictly more well-tied cases, and still reject every mis-tied one.
- **Licence** (`docs/state.md`). Every new script is `derived` and
  credited.
- **The validator ends with 0 errors.** Explain every warning added or
  removed, line by line against `main`, grouped by code.

## Acceptance criteria

- **A** is done as described, and no list line moves because of it.
- **Every one of the twelve points has an outcome:** fixed, or left with
  the reason.
- **Each fixed point has:**
  - the ruling quoted at its archived capture
  - an engine run showing the shipped script does what the point says
  - the generated card's `diff` against the file it started from
  - a red run on a scratch branch and a green run at head, under each
    format that ships it
- **Each gate extension** has a test that rejects a mis-tied case, and
  fails without the change.
- **The lists.** GOAT is byte-identical to `main`. Every changed line in
  the Edison and Tengu lists is one of B's swaps.
- **CI** is green at the final head, with the engine job's
  `executed=… skipped=0` line.

## Required evidence

- `python -m retroformats validate`: counts, and a sorted warning-line diff
  against `main`, grouped by code
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`: the count and the skips
- `python scripts/engine_env.py prepare`, then `run --expect-at-least N`
- `python scripts/generate_format_atlas.py --check`
- `python3 tools/fw.py check`
- `git diff main HEAD -- dist/lflists/`: every changed line
- the old and new Edison and Tengu hashes
- the CI run URL at the final head, and a red run URL per fixed card
- the failing-first runs for each gate extension and for the passages-kept
  check

Your report (`docs/rounds/039-necrovalley-and-variant-fixes/builder.md`)
has the Worker card's sections. Under Verified, it gives a table of the
twelve points: outcome, ruling, format(s), passcode, and red and green
runs. Under Open questions, it gives anything that needs the owner, in
plain product terms.
