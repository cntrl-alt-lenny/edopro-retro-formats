# 035-period-rulings-audit: Do period rulings support the generated historical scripts?

Tier: 2
Mode: research (`HISTORICAL RESEARCH`)
Supersedes: 034-shared-scripts-batch-2, in part. It was rejected unmerged
because its eight cards rest on reading the period English card text as the
period game behaviour. At review, period rulings contradicted at least two
of the eight, and three of the scripts round 031 already merged. Round
034's engineering (the upstream tie, the similarity pin and the cdb byte
fix) is not judged here; a later round salvages it from the unmerged branch
`builder/034-shared-scripts-batch-2`, which must not be changed.

## Goal

For each of the sixteen generated cards below, establish whether the
behaviour its script implements, where it differs from the modern card, is
**supported**, **contradicted** or **unresolved** by rulings in force at
Edison's snapshot (2010-04-24) and at Tengu's (2011-09-17). Where the record
claims the same behaviour for GOAT (2005-04-01), say so too.

Also answer the class question these cards share. In the TCG from 2005 to
2011, could a monster whose text read "This card cannot be Normal Summoned
or Set. This card can only be Special Summoned by …" be Special Summoned
from the Graveyard by another card's effect once it had been properly
Special Summoned? Or did that wording lock it permanently?

Then count, without adjudicating, how many other errata records classify a
change as `functional` from printed English text alone, citing no ruling.

**Why this is next.** Shipped Edison and Tengu lists already contain
scripts that period rulings appear to contradict. Every later script round
depends on the method this round settles.

## The sixteen cards

- Merged, on `main` (`data/custom-cards/`): Metalzoa, Super Vehicroid -
  Stealth Union, Goddess of Whim, Strike Ninja, Green Baboon, Defender of
  the Forest, Rise of the Snake Deity, Malefic Blue-Eyes White Dragon, Soul
  Rope.
- Round 034, unmerged: Gigantes, The Rock Spirit, Garuda the Wind Spirit,
  VW-Tiger Catapult, Gladiator Beast Heraklinos, Dark Master - Zorc, Dice
  Re-Roll, Second Coin Toss. Read their records and scripts from the branch
  with `git show origin/builder/034-shared-scripts-batch-2:<path>`, and each
  card's implemented difference from that branch's
  `docs/rounds/034-shared-scripts-batch-2/builder.md`.

## Context

- `AGENTS.md` (Epistemics above all), `docs/agents/FRAMEWORK.md`,
  `docs/agents/roles/worker.md`, `docs/state.md`.
- Each card's `data/errata/<slug>.json` record, its `data/custom-cards/`
  record and the script's header summary, which states what was changed.
- `docs/research/edison-behaviour-gaps.md` §2 asserts the strict-nomi
  reading from the wording pattern. It is a claim to test, not evidence.
- Leads found at review. Each is a pointer to re-check at its underlying
  source, not a conclusion:
  - Dark Master - Zorc: an Upper Deck Entertainment (UDE) Netrep answer
    dated 2007-10-11, archived at
    `http://web.archive.org/web/20071027075924/entertainment.upperdeck.com/community/forums/thread/883212.aspx`,
    says the die can be rolled only once per turn. The Japanese text has
    carried "１ターンに１度" since its first printing.
  - Second Coin Toss: Yugipedia's `Card Rulings:Second Coin Toss` lists UDE
    rulings saying it applies only to your own tosses, and that with
    several copies active each toss is redone only once.
  - Goddess of Whim: a UDE ruling on Yugipedia says its effect "can only be
    used once per turn".
  - Rise of the Snake Deity: a UDE judge-list thread (archived 2007-11-01,
    thread 830322) says it cannot be activated in the Damage Step.
  - Green Baboon: a UDE ruling on Yugipedia conditions the effect on the
    destroyed monster having been face-up.
  - Dice Re-Roll: a UDE ruling says its effect can be used once during the
    turn it was activated, which is a per-activation reading.
  - Gigantes, Gladiator Beast Heraklinos, Metalzoa, Malefic Blue-Eyes:
    Konami's OCG database rulings (current and undated) say each can be
    revived after a proper Special Summon. That is evidence about the OCG,
    not about the period TCG, unless a TCG source adopts it.
  - Project Ignis's GOAT list keeps the modern implementation of all eight
    round-034 cards (the `format.parity-omits-historical` warnings). This is
    weak, indirect evidence: a curator's choice, not a ruling.
- Tooling note, not evidence: Yugipedia refused one review tool with HTTP
  403, but its MediaWiki API answered, e.g.
  `https://yugipedia.com/api.php?action=parse&page=Card_Rulings:Gigantes&prop=wikitext&format=json`.
  Archived UDE and Konami pages load from `web.archive.org`.

Not worth reading: the engine harness, the generator and the validator.

## Evidence rules

- **Primary period sources decide**: archived UDE judge-list and Netrep
  answers, Konami TCG FAQ and rulings pages, official rulebooks, and
  tournament policy documents. Give each its URL, its archive capture date,
  and the passage you actually read, quoted briefly.
- **Yugipedia is a compilation.** Cite it as the pointer, and the source it
  cites for the claim. When a cited source cannot be opened, the claim stays
  unresolved, with that stated.
- **The ruling's date is not its range in force.** UDE administered TCG
  rulings until Konami took them over. Whether a UDE ruling still held at
  2010-04-24 or 2011-09-17 is a question to answer with evidence. Answer it
  once for the class if a source covers the class, not by assumption per
  card.
- **OCG rulings are evidence about the OCG.** They count for the TCG only
  where a TCG source adopts them.
- **Unknown stays unknown.** Absence of a ruling is not a ruling. Printed
  text with no ruling either way is `unresolved`, not `supported`.

## Scope and non-goals

In scope: one research document,
`docs/research/period-rulings-generated-scripts.md`, and supporting captures
under `docs/rounds/035-period-rulings-audit/attachments/` if useful.

Non-goals:

- No change to canonical data, formats, errata records, custom cards,
  scripts, tests, `dist/` or `docs/state.md`. Findings go in the research
  document only; the corrective round that follows acts on them.
- No change to the round-034 branch or its scratch branches.
- No new card candidates, and no adjudication of the other records the
  count finds.

## Invariants

- `AGENTS.md` § Non-negotiable project invariants, Epistemics: evidence
  before confidence. No converting a publication date into an effective
  date, a ruling's date into its range in force, or an OCG ruling into a
  TCG one.
- `AGENTS.md` § Evidence discipline: no suite run is evidence for a
  historical claim.

## Acceptance criteria

- For each of the sixteen cards, the document gives:
  - the implemented difference, in one sentence
  - a verdict at 2010-04-24 and at 2011-09-17 (supported, contradicted or
    unresolved), and at 2005-04-01 where the record claims GOAT behaviour
  - the sources for each verdict, with the passage read
  - a recommendation: keep the script, change it (and to what), revert to
    the modern card, or raise it with the owner as a thin-evidence call
- The class question is answered, or stated as unresolved with the best
  sources found on each side.
- The count of other text-only `functional` records, with the method used
  to count them.
- A short recommendation, as a proposal only, for a mechanism that would
  stop a text-only reading from reaching a script again.
- Every lead above is either confirmed at its underlying source or reported
  as not confirmed. None is copied through as settled.

## Required evidence

For every claim: the URL (and archive capture), and the passage actually
read. Also:

- `git diff --stat origin/main HEAD`, showing that only the research
  document and attachments changed
- `python3 tools/fw.py check`

Your report (`docs/rounds/035-period-rulings-audit/builder.md`) has the
Worker card's sections. Under Verified it gives the per-card verdict table,
so that it can be read without opening the research document.
