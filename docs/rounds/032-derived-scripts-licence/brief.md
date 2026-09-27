# 032-derived-scripts-licence: Ship round 031's cards with honest script licensing

Tier: 2
Mode: implementation
Supersedes: 031-shared-historical-scripts, rejected at
`3a3b40967a2f`. Its data, lists and engine tests are sound, but five of its
six scripts are labelled "original" while matching Project Ignis's
AGPL-3.0-or-later scripts closely. Brain re-measured this at CardScripts
`383bfbd6`: Soul Rope 0.71, Goddess of Whim 0.72, Green Baboon 0.61, Rise of
the Snake Deity 0.58, Strike Ninja 0.51. The removed Night Assailant script
measured 0.69. Only Malefic Blue-Eyes (0.13) is clearly independent. The
Builder had not opened the Ignis files; the model reproduced them from
memory. **The owner decided on 2026-09-27** that scripts adapted from
Ignis's are allowed. They are labelled `derived`, credited to their source
file, and kept under AGPL-3.0-or-later. Everything else in the repository
stays MIT (`docs/state.md`, card scripts and licence).

## Goal

Round 031's six cards land, and every generated script states its origin
and licence truthfully:

- **derived:** adapted from a named Ignis file, and under AGPL-3.0-or-later
- **original:** measurably different from Ignis's script for the same card

A mechanism, not a reviewer's measurement, keeps an `original` label honest
from now on.

## Context

- This branch starts from round 031's delivered work. Read
  `docs/rounds/031-shared-historical-scripts/` (brief and both reports) and
  `docs/rounds/029-edison-historical-scripts/verifier.md`, which defines the
  similarity measure (line-sequence ratio after normalisation, plus shared
  4-line windows).
- `AGENTS.md`, `docs/agents/FRAMEWORK.md`, `docs/agents/roles/worker.md`,
  `docs/state.md`.
- The `custom-card.*` rules in `retroformats/validate.py`,
  `schemas/custom-card.schema.json`, `retroformats/custom_cards.py`, the
  root `LICENSE`, `README.md` and `dist/README.md`.
- ProjectIgnis/CardScripts at the pinned revision: `COPYING`, `README.md`,
  and the `official/` scripts of the five cards to be relabelled. **In this
  round you may read Project Ignis's scripts**; the earlier ban existed only
  to keep scripts original.

## Scope and non-goals

In scope:

1. **Rebase the five close scripts on Ignis's actual files.** The five are
   Goddess of Whim, Soul Rope, Green Baboon, Rise of the Snake Deity and
   Strike Ninja.
   - Start each from the Ignis `official/` script at the pinned revision,
     and apply only the edits the period behaviour needs.
   - The diff against the upstream file should then be the documented era
     change, and nothing a reviewer has to guess at.
   - Behaviour must not change: every existing engine test must still pass
     unchanged, and still fail on the modern script.
2. **Label and credit them.** Each derived script's header carries:
   - an SPDX line, `AGPL-3.0-or-later`
   - the upstream path and pinned revision
   - Project Ignis's copyright notice as its README states it
   - a notice that this project modified it, with the date and a one-line
     summary of the change (AGPL-3.0 section 5(a))

   Its `authorship` in the card record says the same in fields the
   validator can check. Design the fields; `kind` becomes `original` or
   `derived`.
3. **Licence files.**
   - The AGPL-3.0 text goes into the repository, copied from Ignis's
     `COPYING` at the pin.
   - The root `LICENSE` or `README.md`, and `dist/README.md`, state plainly
     which files are AGPL-3.0-or-later (the derived scripts and their `dist/`
     copies) and that everything else stays MIT.
   - Put this where a user who downloads `dist/scripts/` alone would still
     see it.
4. **Validator.** Replace `custom-card.authorship-not-original`. This is a
   rule change this brief authorises. The new rule accepts:
   - `original`
   - `derived`, when the upstream path, revision and licence are present,
     and the script's header matches them

   Anything else is an error. Show that each new check fails without the
   rule.
5. **Similarity gate for `original`.** Add a test that measures each
   `original` script against Ignis's script for its alias at the pinned
   CardScripts revision. It fails when a script is too close.
   - It lives with the engine tests, where the pinned checkout exists, so
     CI's `engine` job runs it and a skip fails.
   - Choose and justify the threshold, but it must classify these known
     cases correctly:
     - **flag:** the removed Night Assailant script
       (`git show 8f1deb6:data/custom-cards/c600000003.lua`) and round
       031's five close scripts
       (`git show 3a3b409:data/custom-cards/c60000000{4,5,6,7,9}.lua`)
     - **pass:** Metalzoa, Stealth Union and Malefic Blue-Eyes
   - Show it failing on one flagged case.
   - Raise the engine floor by exactly the tests added.
6. **Malefic Blue-Eyes, one bounded research check.** Round 031's Verifier
   noted that Yugipedia's errata table lists the corrected wording under
   "DPKB-EN023, Unlimited Edition". If an English printing carried it before
   2011-09-17, Tengu's state would differ from Edison's.
   - Establish, with cited passages, when that printing appeared.
   - If there is evidence it predates 2011-09-17, stop on Malefic and
     report; do not change the record.
   - If the evidence is inconclusive, say so plainly and leave the record
     as it is.
7. Docs: `docs/errata.md`, `docs/roadmap.md` item 7 and `dist/README.md` say
   what is now true about origin and licence.

Non-goals:

- No new card, no Night Assailant, and no change to any record's chronology
  or evidence (item 6 is research only).
- No change to Edison, Tengu or GOAT list content. The lists, hashes and
  `.cdb` rows stay exactly as round 031 delivered them, and the GOAT hash
  `0x28E9FC02` must not move.
- The misleading GOAT `format.parity-omits-historical` warning for cards
  released after 2005 is a later round; leave it alone.
- Don't relicense anything other than the derived scripts.
- Don't examine BabelCDB's licence beyond one line in Open questions on
  what its repository states. The `.cdb` rows copy only numeric stats and
  our own name and text.

## Invariants

- History and representability stay separate (`AGENTS.md`). Relabelling
  changes no behaviour and no historical claim.
- Evidence in a record is added to, never replaced (`AGENTS.md`). The old
  `authorship` note may be corrected, because it is shown to be wrong; the
  report quotes each old and new note.
- No validation rule is loosened without a brief naming it (`AGENTS.md`).
  This brief names the authorship rule. The replacement must be at least as
  strict for `original`, and add checks for `derived`.
- Validator: 0 errors, and the warning count stays at 563, as at round 031's
  head. Explain any difference.

## Acceptance criteria

- Every generated script's header and record state its origin and licence,
  and the validator rejects a mismatch.
- `git diff` of each derived script against its Ignis source (the report
  includes all five) shows only the period change and the header.
- The similarity gate passes at head, flags every known close case, and CI's
  `engine` job runs it with 0 skipped.
- The Edison, Tengu and GOAT lists and `retro-formats.cdb` are
  byte-identical to `3a3b409`. All engine tests pass in CI at the final head.
- The licence is visible in the repository root and in `dist/`.

## Required evidence

- `python -m retroformats validate`, with counts and a warning diff against
  `3a3b409`.
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`
- `python scripts/engine_env.py prepare`, then `run --expect-at-least N`.
- The CI run URL at your final head, with the engine job's
  `executed=… skipped=0` line.
- `git diff 3a3b409 HEAD -- dist/lflists/ dist/databases/`, which must be
  empty.
- The five upstream diffs.
- The similarity table for all eight scripts, plus the flagged historical
  cases.
- The failing runs for the new rule and for the gate.
- Item 6's finding, with URLs and the passages read.

Your report (`docs/rounds/032-derived-scripts-licence/builder.md`) has the
Worker card's sections.
