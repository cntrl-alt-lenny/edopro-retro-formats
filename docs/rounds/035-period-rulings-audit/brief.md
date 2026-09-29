# 035-period-rulings-audit: Check the generated scripts against period rulings, correct what they contradict, and gate future scripts on rulings

Tier: 2
Mode: research, then data and implementation
Supersedes: 034-shared-scripts-batch-2. It was rejected unmerged because its
eight cards rest on reading the period English card text as the period game
behaviour. At review, period rulings contradicted at least two of the eight,
and three of the scripts round 031 already merged. Its engineering (the
upstream tie, the similarity pin and the cdb byte fix) was sound; part D
carries it over.

## Goal

When this round is done:

- **A. Research.** For every generated card, a documented verdict on
  whether period rulings support, contradict, or leave unresolved what its
  script does.
- **B. A gate.** No generated card can exist without a recorded rulings
  check.
- **C. Corrections.** Every merged script that a period ruling clearly
  contradicts is corrected.
- **D. Carry-over.** Round 034's engineering is on `main`.
- **E. New cards.** The round-034 cards that the evidence supports ship.

The owner asked for one larger round, so that one independent review covers
all of it. Do the parts in the order A to E; each part's evidence goes in
the report.

## The sixteen cards

- **Merged**, on `main` in `data/custom-cards/`: Metalzoa, Super Vehicroid -
  Stealth Union, Goddess of Whim, Strike Ninja, Green Baboon, Defender of
  the Forest, Rise of the Snake Deity, Malefic Blue-Eyes White Dragon, Soul
  Rope.
- **Round 034, unmerged**, on `origin/builder/034-shared-scripts-batch-2`:
  Gigantes, The Rock Spirit, Garuda the Wind Spirit, VW-Tiger Catapult,
  Gladiator Beast Heraklinos, Dark Master - Zorc, Dice Re-Roll, Second Coin
  Toss. Their records, scripts and tests are on that branch (use `git show`
  or `git checkout <branch> -- <path>`), and each card's implemented
  difference is in that branch's
  `docs/rounds/034-shared-scripts-batch-2/builder.md`. Never push to that
  branch.

## Context

- `AGENTS.md` (Epistemics above all), `docs/agents/FRAMEWORK.md`,
  `docs/agents/roles/worker.md`, and `docs/state.md` (card scripts and
  licence).
- The pattern to follow: `docs/rounds/031-shared-historical-scripts/` and
  `docs/rounds/032-derived-scripts-licence/`, plus round 034's branch
  (`git log origin/main..origin/builder/034-shared-scripts-batch-2`).
- Each card's `data/errata/<slug>.json` and `data/custom-cards/` record, and
  the script header's summary of what was changed.
- `docs/research/edison-behaviour-gaps.md` §2 asserts the strict-nomi
  reading from the wording pattern. It is a claim to test, not evidence.
- On the owner's Mac, `python3` is 3.9, below this project's floor. Use a
  3.10+ interpreter, such as `/opt/homebrew/bin/python3.13`, for project
  commands.

### Leads found at review

Each lead is a pointer to re-check at its underlying source, not a
conclusion.

- **Dark Master - Zorc:** an Upper Deck Entertainment (UDE) Netrep answer
  dated 2007-10-11, archived at
  `http://web.archive.org/web/20071027075924/entertainment.upperdeck.com/community/forums/thread/883212.aspx`,
  says the die can be rolled only once per turn. The Japanese text has
  carried "１ターンに１度" since its first printing.
- **Second Coin Toss:** Yugipedia's `Card Rulings:Second Coin Toss` lists
  UDE rulings. The card applies only to your own tosses, and with several
  copies active each toss is redone only once.
- **Goddess of Whim:** a UDE ruling on Yugipedia says its effect "can only
  be used once per turn".
- **Rise of the Snake Deity:** a UDE judge-list thread (archived
  2007-11-01, thread 830322) says it cannot be activated in the Damage
  Step.
- **Green Baboon:** a UDE ruling on Yugipedia conditions the effect on the
  destroyed monster having been face-up.
- **Dice Re-Roll:** a UDE ruling says its effect can be used once during
  the turn it was activated, which is a per-activation reading.
- **Gigantes, Gladiator Beast Heraklinos, Metalzoa, Malefic Blue-Eyes:**
  Konami's OCG database rulings (current and undated) say each can be
  revived after a proper Special Summon. That is OCG evidence, not period
  TCG evidence, unless a TCG source adopts it.
- **Project Ignis's GOAT list** keeps the modern implementation of all eight
  round-034 cards (the `format.parity-omits-historical` warnings). This is
  weak, indirect evidence: a curator's choice, not a ruling.

Tooling note, not evidence: Yugipedia refused one review tool with HTTP
403, but its MediaWiki API answered. For example:
`https://yugipedia.com/api.php?action=parse&page=Card_Rulings:Gigantes&prop=wikitext&format=json`.
Archived UDE and Konami pages load from `web.archive.org`.

## Evidence rules

These apply to every part.

- **Primary period sources decide.** These are archived UDE judge-list and
  Netrep answers, Konami TCG FAQ and rulings pages, official rulebooks, and
  tournament policy documents. Give each its URL, its archive capture date,
  and the passage you actually read, quoted briefly. Add each source you
  rely on to `data/sources.json`.
- **Yugipedia is a compilation.** Cite it as the pointer, and the source it
  cites for the claim. If that source cannot be opened, the claim stays
  unresolved, and you say so.
- **A ruling's date is not its range in force.** UDE administered TCG
  rulings until Konami took them over. Whether a UDE ruling still held at
  2010-04-24 or 2011-09-17 needs evidence. Answer it once for the class if
  a source covers the class; do not assume it card by card.
- **OCG rulings are evidence about the OCG.** They count for the TCG only
  where a TCG source adopts them.
- **Unknown stays unknown.** Absence of a ruling is not a ruling. Printed
  text with no ruling either way is `unresolved`, not `supported`.

## A. Research

Write `docs/research/period-rulings-generated-scripts.md`. For each of the
sixteen cards, give:

- the implemented difference from the modern card, in one sentence
- a verdict (supported, contradicted or unresolved) at Edison's snapshot
  (2010-04-24) and at Tengu's (2011-09-17), and at GOAT's (2005-04-01)
  where the record claims GOAT behaviour
- the sources for each verdict, with the passage read
- the action taken in C or E, or the reason for none

Also:

- **Answer the class question.** In the TCG from 2005 to 2011, could a
  monster whose text read "This card cannot be Normal Summoned or Set. This
  card can only be Special Summoned by …" be Special Summoned from the
  Graveyard by another card's effect once it had been properly Special
  Summoned? Or did that wording lock it permanently? If you cannot answer,
  give the best sources on each side.
- **Measure the class.** Count, without adjudicating, how many other errata
  records call a change `functional` from printed English text alone,
  citing no ruling. Say how you counted.
- **Resolve every lead above**: confirmed at its underlying source, or
  reported as not confirmed. None is copied through as settled.

## B. The rulings gate

Make the validator reject a `data/custom-cards/` record that has no
recorded rulings check.

Each record states which period rulings sources were searched, and what
each found about the card's implemented difference, with the passages.
Each finding says whether it supports or contradicts that difference, or
does not address it. When nothing was found, the record says what was
searched.

The validator also rejects a record that cites a contradicting ruling and
does not name an owner decision accepting it.

Design the field and the codes. Document them in
`schemas/custom-card.schema.json` and `docs/errata.md`. Show each new check
failing first. This tightens the rules and loosens none.

## C. Correct the merged cards

**When to act.** Act on a card only when both of these hold:

- at least one primary period TCG ruling in force at the snapshot
  contradicts the script's difference
- nothing but printed text supports the difference

Anything weaker, or any conflict between period sources, is a thin-evidence
call. Change no data for it, and list it for the owner, stated in product
terms: what the card would do either way, and what each rests on.

**What to do**, depending on what the ruling says:

- **The period behaviour matches the modern card.** Correct the erratum
  record: add the ruling as evidence and change the transition's
  classification, and with it the historical state at the snapshots. Keep
  every existing passage, and move the old summary into the review notes
  with the date and the reason. Then remove the generated card, so the
  lists use the modern code again. Retire its passcode as `600000003` is
  retired, never to be reused. Remove its engine tests, or replace them
  with one asserting that the modern card is used. This brief authorizes
  both for such cards only.
- **The ruling describes a third behaviour, neither modern nor the
  script's.** Change the script to match the ruling, if an engine test can
  observe the difference. Otherwise return the record to `known-gap`, with
  the ruling cited.
- **Supported or unresolved.** Keep the card, and complete its rulings
  record for B.

Every remaining record, merged or new, must pass B.

## D. Carry over round 034's engineering

Bring these onto this branch, adapted as needed, with their tests and their
failing-first evidence re-shown:

- commit `45de718`: the upstream tie (`custom-card.upstream-not-own-script`)
  and the similarity pin
- commit `073828d`: the cdb bytes independent of the SQLite version

Keep the similarity limit at 0.40. Round 034's other gap is still out of
scope: the gate measures an `original` script only against its own alias's
Ignis script. It stays recorded as open in `docs/roadmap.md` item 7.

## E. Ship the round-034 cards the evidence supports

Bring over a round-034 card only if its verdict is `supported` at both
snapshots. Use its record, script and tests from the branch, and give it a
rulings record for B. If its script needs a change to match a ruling, the
rules for a third behaviour in C apply. Passcodes keep their round-034
numbers; a card not shipped leaves its number unassigned and retired.

## Scope and non-goals

What may change:

- the research document
- `data/errata/` records, `data/custom-cards/` and `data/sources.json`, for
  the sixteen cards only
- the validator and the schema documentation for B
- the generator, for D only
- engine and unit tests
- the CI engine floor, which moves by exactly the net number of engine
  tests added and removed
- regenerated `dist/`
- the hash and count pins, rebuilt so that every old value is still
  asserted where it can still be reached
- `docs/roadmap.md` item 7, `docs/errata.md`, `dist/README.md`,
  `docs/engine-testing.md`, `formats/2011-09-tengu/notes.md`, and a dated
  note in `docs/research/edison-behaviour-gaps.md` §2 (add to it; delete
  nothing)

Non-goals:

- No card outside the sixteen.
- No adjudication of the other records the count in A finds.
- No GOAT change: the hash `0x28E9FC02` must not move. If it would, stop on
  that card.
- No new dependency, and no change to what CI's `check` job runs.
- No change to `docs/state.md`; Brain records the owner's decisions.

**When to stop.**

- If the evidence leaves most verdicts unresolved, do A, B (with every
  record passing it as an honest "searched; nothing found"), and D. Then
  report; that is a complete round.
- If a correction in C would change a card's state at a snapshot where the
  ruling is not shown to be in force, stop on that card and put it on the
  owner's list.

## Invariants

- **Epistemics** (`AGENTS.md`). Evidence before confidence. Never convert a
  ruling's date into its range in force, or an OCG ruling into a TCG one.
  No suite run is evidence for a historical claim.
- **Evidence in a record is added to, never replaced** (`AGENTS.md`). Your
  report compares each changed record with its previous version.
- **No rule is loosened** (`AGENTS.md`).
- **Licence** (`docs/state.md`). Every remaining script is `derived` or
  passes the `original` gate.
- **The validator ends with 0 errors.** Explain every warning added or
  removed, line by line against `main`.

## Acceptance criteria

- The research document meets A, and every lead is resolved.
- B's checks each have a test that fails without them. Every remaining
  record passes.
- Each card changed in C, and each card shipped in E, has:
  - a verdict resting on a quoted primary source
  - an engine test that fails on the wrong behaviour and passes at head,
    under both formats, shown with CI runs (red on a scratch branch)
- D's checks each fail without their change. `build --check` is clean in
  CI on Python 3.10 and 3.13.
- The GOAT list is byte-identical to `main`.
- Every line that changes in the Edison and Tengu lists is explained by a
  card in C or E.
- CI is green at the final head, with the engine job's
  `executed=… skipped=0` line.
- The owner's thin-evidence list is in the report, in plain product terms.

## Required evidence

- `python -m retroformats validate`: counts, and a sorted warning-line diff
  against `main`
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`: the count and the skips
- `python scripts/engine_env.py prepare`, then `run --expect-at-least N`
- `python scripts/generate_format_atlas.py --check`
- `python3 tools/fw.py check`
- `git diff main HEAD -- dist/lflists/`: every changed line
- the old and new Edison and Tengu hashes
- the CI run URL at the final head, and a red run URL for each changed or
  new card
- for each derived script, its `diff` against the Ignis source
- for each changed record, its diff against `main`, with what was added and
  what (if anything) was reclassified and why

Your report (`docs/rounds/035-period-rulings-audit/builder.md`) has the
Worker card's sections. Under Verified, it gives the per-card verdict table
and the action taken, so that it can be read without opening the research
document. Under Open questions, it gives the owner's thin-evidence list.
