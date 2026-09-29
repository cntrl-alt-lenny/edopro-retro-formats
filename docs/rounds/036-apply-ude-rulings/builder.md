## Verified

Commands were run with Python 3.13 (`python3` on the owner's Mac is 3.9, below the floor). "Head"
is `25de7ec`, the last code commit; this report is the only commit after it.

- **A. The gate records the decision; each new check fails without its change.**
  `python -m unittest tests.test_custom_cards.CustomCardValidationTest ...` → exit 0, 75 tests in
  the module at head. New codes: `custom-card.decision-source-not-ude`,
  `custom-card.decision-later-documents-missing`, `custom-card.decision-document-not-konami`,
  `sources.bad-ruling-class`; a contradicting finding in force by decision still gives
  `custom-card.contradicting-ruling-unaccepted`. Design: `data/sources.json` marks a source
  `ruling_class: ude-era-ruling` (a UDE card FAQ entry or Netrep answer, including the Konami-hosted
  copy of the FAQ) or `konami-document`; `in_force: by-decision` is accepted only for the first, must
  carry `later_konami_replacement: none-found` and `later_documents_checked` (registered
  `konami-document` sources). Red first: with the seven new tests written and the validator unchanged, four failed
  (five failures with subtests: `test_a_ude_era_ruling_can_be_recorded_as_in_force_by_the_owners_decision`,
  `test_the_decision_covers_only_a_source_marked_as_a_ude_era_ruling` twice, the contradiction test and the
  closed-set test); the other three passed vacuously (an unknown `in_force` value was already
  `rulings-check-malformed`), so each check was then removed in turn from the finished validator and
  the class run again:

  ```
  MUTATION: decision-source-not-ude check removed        -> 2 failing
  MUTATION: no-replacement statement not required        -> 2 failing
  MUTATION: documents-checked list not required          -> 3 failing
  MUTATION: documents need not be Konami documents       -> 3 failing
  MUTATION: by-decision contradiction needs no owner decision -> 1 failing
  MUTATION: registry ruling_class not checked            -> 1 failing
  MUTATION: by-decision basis not required               -> 1 failing
  ```

  The schema (`custom-card.schema.json`, `sources.schema.json`) and `docs/errata.md` document it.
  Nothing else in the gate changed.

- **The three `contradicting-ruling-range-unresolved` warnings are resolved** by removing the two
  cards that carried them (Goddess of Whim, Green Baboon). No live card records a ruling
  `by-decision` as a *contradiction*; five supporting findings use it.

- **`python -m retroformats validate`** → exit 0: `296 errata -> 0 errors, 542 warnings` (main: 0 errors,
  564). Sorted line diff against main, 28 lines gone and 6 added (the 6 include the summary line):
  - 3 gone, `custom-card.contradicting-ruling-range-unresolved` (`c600000004.json` once,
    `c600000006.json` twice): the cards are removed.
  - 22 gone, `format.erratum-known-divergence`, 11 for Edison and the same 11 for Tengu: Dark Master -
    Zorc, Gigantes, The Rock Spirit, Garuda the Wind Spirit, VW-Tiger Catapult, Gladiator Beast
    Heraklinos (now cosmetic-only records), and Dice Re-Roll, Machina Peacekeeper, Machina Gearframe,
    Elemental HERO Chaos Neos, Treeborn Frog (now generated). Edison 39 → 28, Tengu 33 → 22.
  - `format.parity-omits-historical` (GOAT): 2 gone (Goddess of Whim, Green Baboon: no historical state
    any more), 5 added (Dice Re-Roll, Machina Peacekeeper, Machina Gearframe, Elemental HERO Chaos
    Neos, Treeborn Frog: their chronology puts a historical state at 2005-04-01 and Ignis's GOAT list
    does not substitute them). The same noise round 031 recorded for its six; GOAT itself is unchanged.
  - No other code appears or disappears.

- **`python -m retroformats build --check`** → exit 0 at head (it reports `dist/` dirty on an
  uncommitted tree, as documented; clean after the commits).
- **`python -m unittest discover -t . -s tests -v`** → exit 0: `Ran 1110 tests`, `OK (skipped=62)`. All 62
  skips are `ocgcore + pinned checkouts not available`, the engine tests.
- **Engine.** `python scripts/engine_env.py prepare --dest DIR`, then `run --dest DIR --expect-at-least 62` →
  `engine-tests: executed=62 skipped=0 failures=0 errors=0 (required: at least 62 executed, 0 skipped)`,
  macOS. The floor moved 51 → 62, the net of six tests removed (Goddess of Whim 2, Green Baboon 4) and
  seventeen added (Dice Re-Roll 2, Machina Peacekeeper 3, Machina Gearframe 3, Elemental HERO Chaos Neos 2,
  Treeborn Frog 3, four modern-card tests); `test_the_required_count_is_the_number_of_engine_tests` pins it.
- **`python scripts/generate_format_atlas.py --check`** → exit 0 (`128 formats`).
  **`python3 tools/fw.py check`** → exit 0 (`0 error(s), 0 warning(s)`).
- **GOAT is byte-identical to main:** `git diff origin/main HEAD -- dist/lflists/2005-04-goat.lflist.conf` is
  empty; hash `0x28E9FC02`. **Hashes:** Edison `0xC2ED2D57` → `0x56875063`, Tengu `0x410A9E85` →
  `0x79D06437`. Pool card counts did not move (3674, 4563); no banlist file was touched.
- **Every changed line of the Edison list** (the Tengu list differs only by the Treeborn Frog count,
  3 there, 2 in Edison):
  ```
  -12538374 2 --Treeborn Frog                          +600000021 2 --Treeborn Frog (pre-errata)   (Frog, new card)
  -17032740 3 --Elemental HERO Chaos Neos              +600000020 3 --Elemental HERO Chaos Neos (pre-errata)
  -42940404 3 --Machina Gearframe                      +600000019 3 --Machina Gearframe (pre-errata)
  -78349103 3 --Machina Peacekeeper                    +600000018 3 --Machina Peacekeeper (pre-errata)
  -83241722 3 --Dice Re-Roll                           +600000016 3 --Dice Re-Roll (pre-errata)
  +46668237 3 --Green Baboon, Defender of the Forest   -600000006 3 --Green Baboon ... (pre-errata)  (card removed)
  +67959180 3 --Goddess of Whim                        -600000004 3 --Goddess of Whim (pre-errata)  (card removed)
  ```
  Tests re-derive each old value: `to_round_035()` and `CONVERTED_TO_FULL_V2` undo this round, so every
  earlier hash and count pin is still asserted (`tests/helpers.py`, `test_tengu_format.py` and the four
  other files that pin them).
- **CI at head `25de7ec`:** `https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36564328740`
  → `engine success` (`engine-tests: executed=62 skipped=0 failures=0 errors=0`), `check (3.10)` and
  `check (3.13)` success (`Ran 1110 tests`, `validate: ... 0 errors, 542 warnings`).
- **A red run for each new or changed script**, on a scratch branch whose `dist/scripts/c<code>.lua` is
  Ignis's script for the modern card (the `check` job also fails there, on `dist/` drift; the engine job is
  the evidence). Each is red under both formats and fails only the named class:
  - Dice Re-Roll `600000016`, `https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36564349658`:
    `test_a_second_activation_in_the_turn_gives_a_second_re_roll` ×2, `4 != 3`.
  - Machina Peacekeeper `600000018`, `.../runs/36564352505`, and Machina Gearframe `600000019`,
    `.../runs/36564355170`: `test_a_monster_carrying_a_union_cannot_be_given_a_second_one` and
    `test_a_union_cannot_be_given_to_a_monster_carrying_the_card`, ×2 each, `True is not false`.
  - Elemental HERO Chaos Neos `600000020`, `.../runs/36564357889`:
    `test_the_coin_effect_can_be_used_in_main_phase_2_under_the_period_card_only` ×2,
    `[True, True] != [True, False]`.
  - Treeborn Frog `600000021`, `.../runs/36564361326`:
    `test_a_negated_activation_can_be_made_again_in_the_same_standby_phase` ×2,
    `[600000021, 600000021] != [600000021]`.
  Branches: `scratch/036-red-dice-re-roll`, `-machina-peacekeeper`, `-machina-gearframe`,
  `-elemental-hero-chaos-neos`, `-treeborn-frog`; delete once the evidence is accepted.
  For the removed cards, the modern-card tests assert the lists' codes and that no generated row or
  script exists; restoring a generated code fails them (as in round 035).
- **Each derived script against its Ignis source** (header comments omitted), from `git`-tracked files:
  - Dice Re-Roll: the flag moves from the player (`Duel.GetFlagEffect(tp,id)` / `Duel.RegisterFlagEffect`) to
    the registered effect (`e:GetLabel()` / `e:SetLabel(1)`); description reads the alias's strings.
  - Elemental HERO Chaos Neos: `e1:SetCondition(s.coincon)` and `s.coincon` (`Duel.IsPhase(PHASE_MAIN1)`) removed;
    description reads the alias's strings.
  - Treeborn Frog: `e1:SetCountLimit(1)` removed; description reads the alias's strings.
  - Machina Peacekeeper, Machina Gearframe: `aux.AddUnionProcedure(c,f,false)` replaced by `s.AddUnionProcedure(c,f)`,
    a copy of `proc_union.lua`'s procedure with `Auxiliary.UnionTarget(f,true)` (the old one-Union rule)
    in the equip effect and `old_union=true` set on the card; unequip position and the destruction
    substitute are the current procedure's; description reads the alias's strings.
- **Every earlier passage is kept, by an automated check.** `tests/test_migration_materializer.py`
  (`check_round_036_edit`, `tests/fixtures/round-036-before/`, the twelve records as they stood on main)
  asserts, for each edited record: chronology, texts, ids and review status unchanged; sources only
  added; the old review notes a prefix of the new; each replaced summary present verbatim in the notes;
  the kinds after the edit exactly as pinned; and that every string of 25 characters or more in the old
  record survives verbatim in the new one. It caught two real losses while I worked (VW-Tiger
  Catapult's `coverage.gap_reason`, then a dropped sentence when I deleted one on purpose:
  `passages of the earlier record that are gone: /implementation_metadata[0]/gap/behavioural_impact`).
  The Dice Re-Roll, Peacekeeper, Gearframe and Frog records are pinned exactly (frozen target with only the
  coverage and implementation entry replaced, plus a fixed sentence saying which half of the gap
  statement the card leaves out).
- **The class scan.** A pattern over the 117 records with a functional transition (Special Summon wording,
  "Damage Step"), then reading each hit; a record whose texts use neither phrase was not read.

### Cards and records acted on (B, C, D)

| card / record | action | source read |
|---|---|---|
| Goddess of Whim `600000004` | record `cosmetic`; card removed; number retired | Konami-hosted card FAQ F-H (2008-12-15): "It can only be used once per turn, during your Main Phase." Not on Konami's lists. |
| Green Baboon `600000006` | record `cosmetic`; card removed; number retired. Nothing else differs from the modern card: the script differed from Ignis's only by the face-up filter. | Konami errata lists 2009-07-30 / 2010-01-05 / 2010-11-05 (Damage Step; one copy); UDE Netrep 2007-09-28 and card FAQ F-H (face-up). |
| Dark Master - Zorc `600000015` (never shipped) | 2012 transition `cosmetic`; Edison and Tengu stop reporting it | UDE Judge List thread 883212 (Netrep 2007-10-11): "You can only roll the 6-sided die once." |
| Second Coin Toss `600000017` (never shipped) | **stays a known gap, rulings cited**; multi-flip and own-tosses halves of its gap statement withdrawn | Card FAQ S-T (2008-12-15), four entries: own tosses only, all flips, each toss once, may redo a good toss. Ignis's script agrees with all four; only "do two copies have separate uses" is open and no ruling settles it. |
| Dice Re-Roll `600000016` | **ships** (round 034's script, test replaced) | Card FAQ D-E (2008-12-15) and UDE 2005-07-01: "you can use the effect of "Dice Re-Roll" once during the turn in which you activated it." |
| Gigantes, The Rock Spirit, Garuda the Wind Spirit, VW-Tiger Catapult, Gladiator Beast Heraklinos (round 034's numbers `600000010`–`600000014`, never shipped) | records `cosmetic`; nothing generated | The class answer of round 035, re-read this round: rulebook 7.1 ("You cannot use a card effect to Special Summon those monsters from your hand, Deck, or the Graveyard unless it was properly Special Summoned first."), Konami's article, Extreme Victory ruling; for VW-Tiger the VWXYZ-Dragon Catapult Cannon FAQ entry. |
| Dark Necrofear, Elemental HERO Chaos Neos, Fushioh Richie | class half of the summary withdrawn (verbatim in notes); transition stays functional on the other difference | Each card's own FAQ entry confirms the class (Monster Reborn; "can be Special Summoned from the Graveyard if it was first Special Summoned according to its text"; Premature Burial / Call of the Haunted). |
| Machina Peacekeeper `600000018`, Machina Gearframe `600000019` | **ship**: the one-Union Condition only | Advanced Game Play FAQ (2008-12-15); Cyber Phoenix entry, card FAQ A-C (2008-12-16); Delta Tri ruling, TSHD 2010-04-30 (Tengu only). The Attack Position clause is printed text only and is not implemented. |
| Elemental HERO Chaos Neos `600000020` | **ships**: coin effect in either Main Phase | Rulebook 7.1/7.2/8.0, Ignition Effect and Main Phase 2 passages (general rules); FAQ, Zorc entry (sibling). See Open questions. |
| Treeborn Frog `600000021` | **ships**: no use limit after a negation | Card FAQ S-T (2008-12-15): "If the effect of "Treeborn Frog" is negated, you can activate its effect again during the same Standby Phase and Special Summon it." |

Left alone (functional transition kept, looked at, reason): Anteater Eating Ant, Elemental HERO Divine Neos,
Evil HERO Dark Gaia, Masked Beast Des Gardius, XY-Dragon Cannon, XZ-Tank Cannon, YZ-Tank Dragon (era text
says "cannot be Special Summoned **except** by": the lock is what the FAQ and article keep, so the record is
supported); XYZ-Dragon Cannon (explicit "cannot be Special Summoned from the Graveyard"; the class answer is about
the Graveyard); Chaos Emperor Dragon - Envoy of the End (the record already says the era card revives);
Blue-Eyes Toon Dragon, Toon Mermaid, Toon Summoned Skull ("can only be Special Summoned while you control Toon World"
is a condition; their functional changes are the attack lock and Tribute counts); Wulf, Lightsworn Beast (no
restriction in the era); Michizure and My Body as a Shield (Damage Step: the era card cannot, the modern one can, which
the rulebook confirms); Nutrient Z (a window of its own). No card-specific ruling disagreed with a class answer,
so the stop condition never fired. Records touched, before → after on `main`:

| record | shape | classification | transition kinds | baseline coverage | implementation |
|---|---|---|---|---|---|
| `goddess-of-whim`, `green-baboon-defender-of-the-forest`, `vw-tiger-catapult` | v1 → v2 | functional → cosmetic | functional → cosmetic | custom-script or known-gap → none | partial or missing → complete |
| `dark-master-zorc`, `gigantes`, `the-rock-spirit`, `garuda-the-wind-spirit`, `gladiator-beast-heraklinos` | v2 | functional → cosmetic | c1 functional → cosmetic | known-gap → none | missing → complete |
| `dark-necrofear`, `fushioh-richie`, `second-coin-toss` | unchanged | functional | unchanged (summary narrowed, `c2` / `event`) | known-gap | missing (gap statement gains a dated withdrawal) |
| `elemental-hero-chaos-neos` | v1 | functional | unchanged (summary narrowed) | known-gap → custom-script | missing → partial |
| `dice-re-roll`, `machina-peacekeeper`, `machina-gearframe`, `treeborn-frog` | unchanged | functional | unchanged | known-gap → custom-script | missing → partial |

### D candidates examined and rejected, with verdicts

Thirty-three shared divergences; excluded the eight cards of B and C and Necrovalley (its record's state differs at
the two snapshots). Twenty examined and rejected (verdict is the same at Edison and Tengu; the full findings and
sources are in `docs/research/period-rulings-generated-scripts.md` section 11.4):

| card | verdict |
|---|---|
| A Hero Emerges | contradicted (card FAQ: a Special Summon-only monster is sent to the Graveyard, the modern behaviour) |
| Blackwing - Sirocco the Dawn | contradicted (Konami Crimson Crisis rulings: no Main Phase 2, boost lasts to the End Phase) |
| Blast Held by a Tribute | not addressed |
| Blaze Accelerator | contradicted (FAQ: the send is not a cost, the effect targets) |
| Tri-Blaze Accelerator | not addressed |
| Wild Fire | not addressed (one vs all) / contradicted (unconditional wipe and Token) |
| Boss Rush | contradicted (FAQ: no activation after a Normal Summon or Set) |
| D.D. Scout Plane | contradicted (FAQ: once per End Phase) |
| D.D. Survivor | contradicted (FAQ: once per turn); a supported difference the record does not list |
| Dark Necrofear | contradicted (recorded differences); two supported differences the record does not list |
| Ido the Supreme Magical Force | not addressed (Konami's note on Setting is OCG) |
| Masked Beast Des Gardius | not addressed |
| Mustering of the Dark Scorpions | not addressed |
| Red-Eyes Wyvern | not addressed / unresolved |
| Soul Rope (2015 difference) | not addressed |
| Swap Frog | not addressed; a second copy's activation is supported by inference and unrecorded |
| Totem Dragon | not addressed (sibling rulings only: Treeborn Frog, Sinister Serpent) |
| Trap of Darkness | not addressed |
| Elemental HERO Divine Neos | not addressed (the only ruling is OCG) |
| Evil HERO Dark Gaia | not addressed |

Zero-is-valid did not apply: four cards shipped of the up-to-six allowed (Peacekeeper, Gearframe, Chaos Neos, Frog;
Dice Re-Roll is part of B, not D). Passcodes are `600000018` to `600000021`.

## Not verified

- **The rejected candidates' verdicts at source.** They come from four delegated read-only research passes (six cards
  each). I re-read at source: Machina Peacekeeper, Machina Gearframe, Elemental HERO Chaos Neos, Treeborn Frog, every
  ruling of part B, and, as a spot check, A Hero Emerges and Blackwing - Sirocco the Dawn. I did not re-read the
  others. Two claims of the passes (Swap Frog's second copy; Dark Necrofear's and D.D. Survivor's unrecorded supported
  differences) rest on their reading alone and are recorded as findings, not acted on.
- **The Japanese first printing of Dark Master - Zorc** (transcribed on Yugipedia only) and the OCG-side of every card.
- **A real EDOPro client** loading `dist/`; Windows locally (CI's `engine` job runs on Linux; the duel engine builds
  on Linux and macOS only); Python 3.10 locally (CI's `check (3.10)` passed at head, and every changed file parses
  as 3.10 syntax).
- **`python -m retroformats materialize`**: no pool or release data was touched, so it was not run.
- **The GOAT-era behaviour of every card** (out of scope), and how the UDE card FAQ stood after 2009-02: the decision
  makes that a rule, not a finding (`docs/state.md`).
- **The unequip position of Machina Peacekeeper and Machina Gearframe, the opponent's die rolls for Dice Re-Roll, an
  already re-rolled result, and Chaos Neos's toss results**: not implemented or not tested; each card's
  `not_reproduced` says so.
- The nine cards "round 031 excluded": I could not identify nine. I excluded Night Assailant, the five Edison-only
  intermediate-state cards (none is in the shared 33) and Necrovalley, and examined the rest.

## Changed

- **Validator and schema (A only):** `retroformats/model.py`, `retroformats/validate.py` (`_check_decision_entry`,
  `_validate_source_registry`, the by-decision branch of `_check_rulings`), `schemas/custom-card.schema.json`,
  `schemas/sources.schema.json`, `docs/errata.md`, `tests/test_custom_cards.py`.
- **Data:** `data/sources.json` (`ruling_class` on 24 sources: 12 `ude-era-ruling`, 12 `konami-document`; one new source `konami-shining-darkness-rulings-2010-04`,
  dated notes on three); `data/errata/` (16 records, table above); `data/custom-cards/` (removed `c600000004`,
  `c600000006`; added `c600000016`, `c600000018`–`c600000021`, each a `.json` and `.lua`); `data/cards/index.json`.
- **Generated:** `dist/` (`retro-formats.cdb`, two lists, five scripts added and two removed, `LICENSES.md`,
  `dist/README.md`).
- **Tests:** `tests/engine/test_shared_historical_scripts.py`, `tests/engine/test_edison_historical_scripts.py`,
  `tests/helpers.py` and the pin files named above, `tests/test_migration_materializer.py`,
  `tests/fixtures/round-036-before/` (new), `tests/fixtures/research-citation-backlog.json` (one entry left, now
  registered); `.github/workflows/ci.yml` (`--expect-at-least 51` → `62` only).
- **Docs:** `docs/research/period-rulings-generated-scripts.md` (section 11 added, nothing deleted), `docs/roadmap.md`
  item 7, `docs/engine-testing.md`, `formats/2011-09-tengu/notes.md`, `README.md` (the licence sentence: six
  derived scripts, it named five stale ones). `docs/state.md` was not changed.
- Two pre-existing test helpers were adapted, not loosened: `_sixteen_cards` (now cycles the live cards) and the
  identity pairs.
- Round 034's branches are untouched; Dice Re-Roll's script was read from `origin/builder/034-shared-scripts-batch-2`.

## Open questions

1. **Elemental HERO Chaos Neos ships on a general Konami rule, not a card-specific ruling.** The rulebook says an Ignition
   Effect is used "during your Main Phase" and Main Phase 2 allows the same actions; the card FAQ applies that to Dark
   Master - Zorc; nothing names Chaos Neos's effect. I read a rulebook rule as a ruling, as the round-035 class
   answers do. If you want a card-specific ruling for every shipped card, removing this one card is a single
   revert (its record goes back to `known-gap`).
2. **VW-Tiger Catapult's 2018 rewording also adds explicit targeting to its discard effect.** The record never called it
   a difference and round 034 tested only the revival, so I followed the brief and made the record cosmetic. Whether
   the era effect targeted is unknown; a wrong "no difference" here would be silent.
3. **Second Coin Toss stays a gap.** The rulings agree with the modern card on everything they establish. The one thing
   left is whether two copies each get a redo on different tosses in one turn; "each toss once" does not say. Decide
   whether to leave it, or to accept the natural reading and ship a per-copy script.
4. **Three supported differences the erratum records do not list:** D.D. Survivor returning "during the next turn's End
   Phase", two Dark Necrofear rulings (Tailor of the Fickle / Collected Power, a negated Summon), and a second Swap Frog
   copy. Adding them means new transitions in those records; I did not.
5. **Machina Peacekeeper and Machina Gearframe ship the one-Union Condition only.** The "unequip in face-up Attack Position"
   clause is printed text with no ruling, so the card lets the controller pick the position, which the era text did not.
6. **Treeborn Frog's second FAQ entry** (a Frog summoned and sent away returns the same Standby Phase) already holds for
   the modern script, because a card that moved is new to its own "once per turn"; only the negation case differs, and that
   is what ships.
7. **Four cards shipped, not six.** The other twenty are rejected on evidence, with their verdicts above; none was
   shipped on printed text.
