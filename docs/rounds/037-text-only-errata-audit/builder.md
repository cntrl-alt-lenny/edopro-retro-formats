<!-- fw-report
round: 037-text-only-errata-audit
role: builder
branch: builder/037-text-only-errata-audit
head: 3bebab4fefc37ba08a944b59198768784547f86b
os: macOS 27.0
python: 3.13.15
written: 2026-09-29T13:30:52Z
-->
## Verified

Commands run with Python 3.13 (`python3` on the owner's Mac is 3.9, below the floor). "Head" is the last code commit,
`6f25094`, plus documentation commits after it; this report is the only commit after those. Research passes: twelve
read-only subagents each read a batch of dossiers (claim, script diff, corpus hits) against the corpus and wrote
structured findings; **every quoted passage (413 evidence entries) was machine-checked as a verbatim substring of the
converted archived document it cites** (`verify_results`, 0 problems), and I read every `contradicted` verdict, every
`supported` passage and every note the passes flagged, and overrode them where a passage did not say what the verdict
needed (below). The corpus documents were fetched from the archived captures in `data/sources.json` (Wayback `id_` URLs,
2026-09-29) and converted with `pdftotext` and a stdlib HTML parser; nothing was read from a live page.

- **The selection.** Re-derived from the raw `data/errata/*.json` by a script that reads no validator code (also
  `tests/test_errata_rulings_gate.py::LiveErratumRulingsGateTest`, on every run): 109 records have a `functional`
  transition, 106 of them cite no ruling-class source, and the brief's four conditions select **83: 61 reuse-upstream,
  19 known-gap, 3 none-needed (Diffusion Wave-Motion, Evil HERO Infernal Prodigy, Gaia Soul the Combustible
  Collective). The brief's number is right.** The per-transition gate the validator enforces selects **91**: eight more,
  which the four conditions leave out and I checked too. Six have an *undated* functional event (Anteatereatingant,
  Armored Glass, Curse of Royal, Dimension Distortion, Spirit's Invitation, YZ-Tank Dragon): their state at both snapshots
  is `ambiguous`, so the era card can be the one a list plays, but condition 3 (a date after Edison's snapshot) cannot
  select them. Two have a later functional change after an earlier one (Necrovalley: c1, c2, c3; Swords of Concealing
  Light: c2, c3): condition 3 reads the first. The goal (A: no record whose change applies at a snapshot is left without
  a check) needs them; the non-goal ("records outside the four conditions are left alone") would have left the gate
  a warning for ever. I chose the goal and flag it below.
- **Groups.** All four (reuse-upstream, known-gap, none-needed, the eight extras) were done completely.
- **A. The gate.** `python -m unittest tests.test_errata_rulings_gate` → 24 tests, OK. Red first, **as a warning with no
  record checked** (the introducing commit, `d57a2e8`; 3 failures of 22, the live tests and the severity test):
  ```
  FAIL: test_the_finding_is_an_error_not_a_warning (tests.test_errata_rulings_gate.ErratumRulingsGateTest.test_the_finding_is_an_error_not_a_warning)
  FAIL: test_every_record_in_scope_carries_a_check_on_each_transition (tests.test_errata_rulings_gate.LiveErratumRulingsGateTest.test_every_record_in_scope_carries_a_check_on_each_transition)
  FAIL: test_no_finding_of_the_gate_is_left_in_the_repository (tests.test_errata_rulings_gate.LiveErratumRulingsGateTest.test_no_finding_of_the_gate_is_left_in_the_repository)
  Ran 22 tests in 0.744s
  FAILED (failures=3)
  ```
  The gate then went through the data and became an error once every record in scope carried a check (`validate`:
  0 `erratum.rulings-check-missing`). Each rule fails without its change (mutations of the finished validator, then the
  class run again; outputs saved):
  ```
  MUTATION 1: the gate is never called                          -> 23 failing (of the 23 tests the class had then)
  MUTATION 2: severity back to a warning                        ->  1 failing: test_the_finding_is_an_error_not_a_warning
  MUTATION 3: contradictions never ask for an owner decision    ->  4 failing (in force, by decision, not-shown, cosmetic)
  MUTATION 4: a cosmetic transition is asked for a decision too ->  1 failing: test_a_cosmetic_transition_may_carry_the_check_that_made_it_cosmetic
  MUTATION 5: swap-frog.json loses its check                    ->  2 failing (the live tests) and `validate`: 1 error, erratum.rulings-check-missing
  ```
  Design: `Validator._check_rulings_body` is the generated cards' check and the errata records' check at once
  (same finding values, `in_force` values, `by-decision` conditions and `owner_decision` rule; codes under `erratum.`);
  `retroformats/model.py` gains `ERRATUM_RULINGS_GATE_FORMATS` and `ERRATUM_RULINGS_GATE_EXEMPT`; the flattened
  single-event shape carries the check (`_desugar_v2_sugar`). Documented in `schemas/erratum.schema.json` and
  `docs/errata.md`. Two decisions of mine, both in the brief's spirit and both tightening: (1) a cosmetic transition may
  carry the check that made it cosmetic without an owner decision (its contradicting findings are that evidence, not a
  claim a ruling contradicts); (2) a transition that cites a ruling source is **not** excused — only three, by name
  (Dark Necrofear's c2, Fushioh Richie's and Second Coin Toss's, checked in rounds 035 and 036 and left alone), are
  exempt. My first draft exempted every transition citing a ruling source; deleting a check from a record I had
  just edited did not fail (MUTATION 5's first run), which is why.
- **`python -m retroformats validate`** → exit 0: `validate: 3 formats, 3 banlists, 3 pools, 3 rule profiles, 296 errata -> 0 errors, 535 warnings` (main: `296 errata -> 0 errors, 542 warnings`).
  Sorted line diff against main, grouped by code (main → head: 22 gone, 7 added, 1 net summary line):
  - `erratum.functional-none-needed`: 2 gone (Diffusion Wave-Motion, Gaia Soul the Combustible Collective: now cosmetic-only).
  - `format.erratum-known-divergence`: 6 gone (A Hero Emerges, D.D. Scout Plane, Soul Rope, each at Edison and Tengu: modern-correct).
  - `format.erratum-modern-known-wrong`: 4 gone (Axe of Despair, Tyrant Dragon at both: their 2013 transition became cosmetic, so the modern state is possible).
  - `format.parity-omits-historical` (GOAT): 2 gone (Imperial Custom, Senet Switch: no historical state any more). GOAT itself is unchanged.
  - `format.erratum-unresolved-defaulted`: 4 added (the same two records, both snapshots: their remaining relevant event is undated, so the modern default applies).
  - `erratum.undated`: 2 added (Axe of Despair, Tyrant Dragon: same reason).
  - `erratum.contradicting-ruling-range-unresolved`: 1 added, the tracked question for Blaze Accelerator (one FAQ entry's lines conflict).
  No other code appears or disappears. 542 - 14 + 7 = 535.
- **`python -m retroformats build --check`** → exit 0 (it reports `dist/` dirty on an uncommitted tree, as documented; clean at head).
- **`python -m unittest discover -t . -s tests -v`** → exit 0: `Ran 1135 tests in 16.885s  OK (skipped=63)`. All 63 skips are the engine tests (no ocgcore).
- **Engine.** `python scripts/engine_env.py prepare --dest DIR`, then `run --dest DIR --expect-at-least 63` → `engine-tests: executed=63 skipped=0 failures=0 errors=0 (required: at least 63 executed, 0 skipped)`, macOS. Floor 62 → 63 (`.github/workflows/ci.yml`, `docs/engine-testing.md`), the net of one added test:
  `Round037CosmeticRecordsUseTheModernCardTest`, parametrised over both formats and both cards. Red first: with `dist/lflists/` put back to `origin/main`'s, it fails on `9995766 not found in {...}` (Edison, Imperial Custom); with Imperial Custom's variant code in a scenario, the cost destruction it asserts returns 0 instead of 1 (`BYCOST 0`), and Senet Switch's variant moves the monster to zone 3 where the modern card leaves it at 2.
- **`python scripts/generate_format_atlas.py --check`** → exit 0 (`128 formats`). **`python tools/fw.py check`** → exit 0 (`0 error(s), 0 warning(s)`).
- **GOAT is byte-identical to main:** `git diff origin/main HEAD -- dist/lflists/2005-04-goat.lflist.conf` is empty; hash `0x28E9FC02`. **Hashes:** Edison `0x56875063` → `0x58B75080`, Tengu `0x79D06437` → `0x77E064D4`. Pool card counts did not move (3674, 4563); no banlist file was touched.
- **Every changed line of the Edison and Tengu lists** (identical in both):
  ```
  -9995776  3 --Imperial Custom (pre-errata)      +9995766  3 --Imperial Custom
  -63394882 3 --Senet Switch (pre-errata)         +63394872 3 --Senet Switch
  ```
  Both are explained by a record in C (`imperial-custom`, `senet-switch`: made cosmetic on a ruling). Tests re-derive every old value: `to_round_036()` puts the two variants back and reproduces `0x56875063` / `0x79D06437`; `to_round_035()` now includes it, so the older pins (round 035 / 031 / 029) are still asserted (`tests/helpers.py`, and the pin files).
- **Every earlier passage is kept, by an automated check.** `tests/test_migration_materializer.py` (`check_round_037_edit`, `ROUND_037_EDITED`, `tests/fixtures/round-037-before/`, the 93 records as they stood on main) asserts, for each edited record: chronology, texts, ids and review status unchanged; sources only added; the old review notes a prefix of the new; each replaced summary present verbatim in the notes; the kinds after the edit exactly as pinned; coverage unchanged (or, for a cosmetic-only record, replaced with the old coverage and gap statement kept verbatim in the notes); and every string of 25 characters or more in the old record survives verbatim. Red first: with a sentence deleted from Dark Strike Fighter's notes the class fails: `erratum-dark-strike-fighter: the old review notes are kept verbatim`. The round-036 rule still runs on the records round 036 edited (the fixture is passed through `check_round_036_edit`).
- **CI at head `6f25094`** (every code and data change; the commits after it change documentation only): `https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36575344567` → `check (3.10)`, `check (3.13)` and `engine` success; the engine job's line: `engine-tests: executed=63 skipped=0 failures=0 errors=0 (required: at least 63 executed, 0 skipped)`; `check`: `Ran 1135 tests ... OK (skipped=63)` and `validate: ... 0 errors, 535 warnings`. The run at the final head (this report's commit) is named in the reply. No script changed, so there is no red run for one; the red evidence for the moved lists is the local run above.
- **The counts table** (records checked per group; differences per verdict, identical at both snapshots for every difference except Necrovalley's c1, which applies at Edison only and is `unresolved` on inference):

  | group | records | transitions made cosmetic | narrowed | differences supported | contradicted | unresolved |
  |---|---|---|---|---|---|---|
  | reuse-upstream | 61 | 5 | 1 | 48 | 9 | 64 |
  | known-gap | 19 | 5 | 6 | 2 | 15 | 28 |
  | none-needed | 3 | 2 | 0 | 0 | 2 | 1 |
  | extra (8) | 8 | 0 | 1 | 5 | 2 | 14 |
  | total | 91 | 12 | 8 | 55 | 28 | 107 |

  (A record can carry several differences; "contradicted" counts each, and the ones that rested on inference or a conflict between sources are already under "unresolved".)

### Every record changed, with its verdict, action and source

All 93 records carry a check (91 in scope, plus VW-Tiger Catapult and Dark Necrofear for part D); each record's check, verdicts and passages are in `docs/research/text-only-errata-audit.md`, section 5, and each record's review notes carry a dated paragraph. **Nineteen records were corrected** (12 have a transition made cosmetic, 8 were narrowed, Blackwing - Sirocco the Dawn both):

| record | action | ruling it rests on |
|---|---|---|
| A Hero Emerges | cosmetic | card FAQ A-C (2008-12-16): a Special Summon-only or Spirit monster selected "is sent to the Graveyard" |
| D.D. Scout Plane | cosmetic | card FAQ D-E: "can only activate once during the same End Phase"; "removed from play and then returned to the Graveyard with "Miracle Dig" ... not Special Summoned" |
| D.D. Survivor | first transition cosmetic; **second functional transition added** (part D) | card FAQ D-E: "can only be activated once per turn"; re-banished in the End Phase, "its effect will activate during the next turn's End Phase" |
| Diffusion Wave-Motion | cosmetic | card FAQ D-E and the 2005 page: cannot be activated "if there are no monsters on your opponent's side of the field" |
| Gaia Soul the Combustible Collective | cosmetic | card FAQ F-H and the 2005 page: "once per turn" |
| Imperial Custom | cosmetic; **list line moves back to the modern card** | Konami's Ancient Prophecy rulings (2009-08-11): an unpaid maintenance cost for Mirror Wall or Imperial Order still destroys it |
| Senet Switch | cosmetic; **list line moves back to the modern card** | card FAQ S-T: if the designated Monster Card Zone is occupied "the effect ... is not applied and the monster does not move" (its second claimed difference, Main Monster Zone only, is structural: five Monster Zones) |
| Soul Rope (c1) | cosmetic | Konami's rulebook 7.0-8.0 (only Counter Traps and ATK/DEF changers in the Damage Step; "destroyed" means battle or an effect): a class answer, as round 035's for its first transition |
| Axe of Despair (c2) | 2013 transition cosmetic | card FAQ F-H and the 2005 page: "Cards like "Axe of Despair"" prevent "Falling Down" from being destroyed, i.e. it counted as an Archfiend |
| Tyrant Dragon (c2) | 2013 transition cosmetic | card FAQ (D-E, P-R, S-T): the Dragon Tribute is "a condition on the Summoning of the card; it is not part of the effect" |
| Toon Summoned Skull (c2) | 2013 transition cosmetic | card FAQ A-C and the 2005 page: it is a "Special Summon-only" Archfiend for Archfiend's Roar |
| Blackwing - Sirocco the Dawn | c2 cosmetic; c0 narrowed to the sum-timing point | Konami's Crimson Crisis rulings (2009-02-27): "The ATK boost lasts until the End Phase"; "cannot activate its ATK boost in Main Phase 2" |
| Ancient Fairy Dragon | narrowed (Field Spells versus Field Zones dropped) | Konami's Ancient Prophecy rulings: destroys "both" Field Spells and Set ones; rulebook: Field Spells fill the Field Zone |
| Anteatereatingant | narrowed (once per turn, targeting dropped) | card FAQ A-C: "You can only activate this card's effect once per turn."; "targets 1 Spell or Trap Card" |
| Blaze Accelerator | narrowed (cost, no target dropped) | card FAQ A-C: "It is not a cost."; ""Blaze Accelerator's" effect targets." What remains has two conflicting lines |
| Boss Rush | narrowed (activation restriction, face-up dropped) | card FAQ A-C: no activation after a Normal Summon or Set; must be face-up when the monster is destroyed |
| Red-Eyes Wyvern | narrowed (the Necrovalley consequence dropped) | card FAQ L-O: "Necrovalley" negates "costs and effects that require removing cards from the Graveyard" |
| Tri-Blaze Accelerator | narrowed (paid as a cost dropped) | card FAQ (A-C, S-T): sending the Pyro monster "is not a cost" |
| Wild Fire | narrowed (unconditional wipe dropped) | card FAQ U-Z: if Blaze Accelerator is removed in response "Wild Fire's effect disappears" |

Part D (also in the table above where it changed a record): VW-Tiger Catapult's targeting is `unresolved` (no ruling on the card; two sibling rulings recorded as not counted), Dark Necrofear gains three rulings as evidence (no new transition: nothing shows a difference from the modern card) and a fourth finding, listed below; Swap Frog's second copy shows no difference (`does-not-address`, reason on the record); Machina Peacekeeper and Machina Gearframe: **no ruling supports the "unequip ... face-up Attack Position" clause**, the search is recorded on both cards' `rulings_check` and `not_reproduced`, the scripts are unchanged. Night Assailant: recorded, not acted on (below).

## Not verified

- **CI at the final head, and Linux and Windows.** The engine job runs on Linux; I ran the engine tests on macOS only. The run URL is in the reply.
- **Every `unresolved` search.** An `unresolved` verdict is a passage-free claim that nothing in the corpus addresses the difference. I checked the searches the passes recorded and re-ran a punctuation-insensitive name search over the whole corpus after the first pass missed "D. D. Scout Plane" and the dash in "Blackwing - Sirocco the Dawn" (both are now in the verdicts); I did not re-read every unresolved record's dossier myself. Absence is evidence about the search, not the world.
- **The UDE forums** are gone; only the nine threads Yugipedia links (three are cited) could be read. Yugipedia's pointer pages were read, not cited as sources.
- **Any script's behaviour.** The points where an Ignis script and a ruling disagree (below) are read from the script text, not run. No engine test exists for a variant script's unchanged behaviour; the two records whose lists moved are tested.
- **A real EDOPro client** loading `dist/`; Python 3.10 locally (CI's `check (3.10)` runs at the pushed head).
- **`python -m retroformats materialize`**: no pool or release data was touched, so it was not run.
- **The OCG side** of every card and the Japanese first printings.
- **`docs/state.md`** was not changed, as instructed.

## Changed

- **Validator, model, schema (A only):** `retroformats/validate.py` (`_check_erratum_rulings`, `_check_rulings_body` split out of `_check_rulings`, prefix and `claims_a_difference` parameters, `_check_decision_entry` takes the prefix), `retroformats/model.py` (`ERRATUM_RULINGS_GATE_FORMATS`, `ERRATUM_RULINGS_GATE_EXEMPT`, the desugaring carries `rulings_check`), `schemas/erratum.schema.json`, `docs/errata.md`.
- **Data:** `data/errata/` (93 records: 91 in scope plus VW-Tiger Catapult and Dark Necrofear), `data/sources.json` (14 sources added: ten Konami per-set ruling documents, three archived UDE judge-list threads, the Yugipedia pointer; `ruling_class: ude-era-ruling` on two FAQ pages already registered), `data/custom-cards/c600000018.json` and `c600000019.json` (the searched clause, `rulings_check` and `not_reproduced` only).
- **Generated:** `dist/lflists/2010-03-edison.lflist.conf`, `dist/lflists/2011-09-tengu.lflist.conf` (two lines each).
- **Tests:** `tests/test_errata_rulings_gate.py` (new, 24), `tests/test_migration_materializer.py` (`check_round_037_edit`), `tests/fixtures/round-037-before/` (93 records), `tests/helpers.py` (`to_round_036`, `ROUND_037_*`, `record_before_round_037`, `errors_without_the_frozen_exemption`), the hash and count pins in `tests/test_tengu_format.py`, `test_tengu_format_gate.py`, `test_yugi_kaiba_format_gate.py`, `test_ocg1999_release_certification.py`, `test_shadow_migration.py`, `test_unordered_canonical_migration.py`, `test_last_will_v2.py`(via the shared set), `tests/fixtures/research-citation-backlog.json` (ten URLs now registered), `tests/engine/test_shared_historical_scripts.py` (+1), `tests/engine/harness.py` and `test_edison_historical_scripts.py` (`MSG_SELECT_DISFIELD`).
  Test helpers that validate the frozen pre-migration corpora now exclude one code (`erratum.rulings-check-missing`), because those frozen records predate the rule and cannot carry a check; every other error is still counted.
- **Docs:** `docs/research/text-only-errata-audit.md` (new), a pointer in `docs/research/period-rulings-generated-scripts.md`, `docs/roadmap.md` item 7, `docs/errata.md`, `docs/engine-testing.md`, `formats/2011-09-tengu/notes.md`. `dist/README.md` needed no edit (its counts are unchanged). `docs/state.md` was not changed.
- **CI:** the engine floor only (`--expect-at-least 62` → `63`).

## Open questions

Judgements of mine for Brain or the owner:

1. **I checked eight records the brief's four conditions leave out** (six undated, two with a later functional change), because the goal (A) is per transition. They are additive checks only; only Anteatereatingant was also narrowed. If you want them out, drop them from `ROUND_037_EDITED`, restore them from the fixtures and exempt them by name.
2. **The gate exempts three transitions by name** rather than "anything that cites a ruling source" (why above).
3. **Night Assailant.** Left as recorded: functional c0 and c1, known gap at Edison, Ignis's pre-errata variant at Tengu. Its check records that both period sources rule that **both** of its effects target, and that the AST-080 "self-eligible" claim is contradicted by the same entry (so the c0 change looks cosmetic and the variant already plays as both snapshots on it); a second copy remains a legal retrieval (the by-name exclusion is a 2022 change, supported). Whether the effect was optional: no ruling in words; the timing rulings (it activates as a cost or mid-chain, where the FAQ says optional "when ... you can" effects miss timing) point to mandatory. Because that check records a contradicting ruling in force, the validator asks for an `owner_decision`; **I named the owner's own decision of 2026-09-23 (held back, stays a known gap, docs/state.md) in it. That decision was not made about this ruling. If you disagree, the alternative is to make c0 cosmetic, which would move Edison's list to Ignis's variant and Tengu's to modern.** Not shipped.
3. **A class answer applied at the edges.** Soul Rope's second transition and Senet Switch's second claimed difference rest on Konami's general rules (Damage Step, five Monster Zones), as round 035's class answers did; Imperial Custom's rests on one Konami sentence about maintenance costs (the other non-battle, non-effect destructions are unaddressed). Reverting any of the three is one record each. Imperial Custom and Senet Switch are the only two that change a list.
4. **Dark Necrofear's c2 is contradicted and I did not narrow it** (outside the audited set): the card FAQ (2008-12-16, A-C) says "that effect selects 1 target", against the summary's "no target". One record edit if you want it.
5. **Where an Ignis script and a ruling disagree** (read, not run; nothing edited, per the brief). These are the "contradicted on one point of a variant script" cases, in product terms:
   - Armored Cybern: the variant script destroys the target even when the equipped monster's ATK cannot be reduced, where the card FAQ says the effect then disappears (read from the script, not run).
   - Axe of Despair: the variant script (from the undated c0 ruling event, left alone) can return the card even after its trigger missed timing; the card FAQ (after Cyber Jar) says the timing has passed.
   - Big Shield Gardna: the variant script checks that the card is face-down only when the Spell is activated; the FAQ lets a Book of Moon chained to the Spell flip it face-down and still negate it (read from the script, not run).
   - Blue-Eyes Toon Dragon: at Level 5 the variant script requires one Tribute to be available but pays none; no ruling covers the case.
   - Dark Magician of Chaos: the variant script lets Skill Drain negate the leave-field banish; the UDE Skill Drain ruling says that effect is not negated.
   - Dark Strike Fighter: the variant script omits the Synchro revive limit; the rulebook and the Crimson Crisis ruling say a Synchro Monster cannot be revived without a proper Synchro Summon.
   - Future Fusion: the variant script appears to let contact-Fusion-only monsters be selected, which the card FAQ forbids (read from the script, not run).
   - Jirai Gumo: on an odd Life Point total the variant script leaves the controller one point less than the FAQ's rounding rule gives (the FAQ line is under Solemn Judgment, a different card).
   - Nutrient Z: the variant script offers the card from the hand; the rulebook says a Trap must be Set first (read from the script, not run).
   - Twin-Headed Behemoth: the variant script lets Skill Drain stop the revival's bookkeeping; the FAQ says the revival still happens under Skill Drain.
   - Diffusion Wave-Motion: Ignis's script (the modern implementation the list uses) lets the card be activated against an empty field; the FAQ says it cannot be. An implementation gap, not a history question.
   - Gaia Soul the Combustible Collective: Ignis's script (the modern implementation) has no once-per-turn limit on the Tribute effect; the FAQ says one. An implementation gap, not a history question.

6. **Thin evidence and conflicts, in plain product terms** (no data changed for any of these; the full text of what each rests on is in the research document, section 8). Where the card would do the same visible thing either way I say so:
   - Armored Cybern: whether the era card's destroy-instead effect covered only battle rests on a FAQ line about older Union monsters; no ruling names this 2010 Union.
   - Blue-Eyes Toon Dragon: no ruling on whether a Flip Summon after Book of Moon re-imposes the attack lock, or on Level-scaled Tributes; the variant is kept on the printed era text.
   - Brain Control: that the era card could take Extra Deck monsters rests on a ruling about Tuner's Scheme, not one on Brain Control; nothing addresses main-Deck Special Summon-only monsters.
   - Brionac: no ruling on either point (repeatable use; bouncing your own cards); the variant is kept on the printed era text.
   - Burning Land: no ruling on the standing destruction of Field Spells or on activating with none on the field; the variant is kept on the printed era text and the upstream author's comment.
   - Catapult Turtle: repeatable use rests on the general rule for Ignition Effects and the printed text; no ruling names the card on this point.
   - Chaos Emperor Dragon - Envoy of the End: no ruling on its 'cannot activate other cards' rider; repeatable use rests on the general rule for Ignition Effects.
   - Crush Card Virus: no ruling names the card; the variant is kept on the printed era text.
   - Dark Strike Fighter: repeatable use and use in Main Phase 2 rest on general rules and the printed text; no ruling names the card on either.
   - Destiny HERO - Disk Commander: no corpus document names the card; the variant is kept on the printed era text.
   - Gilasaurus: no ruling says whether the era effect targeted; the record dates the targeting wording to a 2012 printing, after both snapshots, so the variant may ship a post-snapshot design.
   - Imperial Custom: one Konami sentence settles maintenance-cost destruction only; other non-battle, non-effect destruction is not addressed. The list now uses the modern card.
   - Imperial Order: whether the 700 Life Point payment was due only in its controller's own Standby Phase rests on the printed text alone.
   - Makyura the Destructor: whether several Traps could be played from the hand in one turn and whether several Makyuras each grant it rest on the printed text alone.
   - Manga Ryu-Ran: no ruling; the variant script's Level thresholds differ between its condition and its Tribute selection (a Level 5 copy can be summoned for free).
   - Mysterious Puppeteer: no ruling on the Life Point gain from its own Summon; the variant is kept on the printed era text.
   - Night Assailant (held back, not shipped): both period sources rule that BOTH of its effects target (UDE card rulings page and its 2008-12 Konami-hosted copy). Whether the effect was optional or mandatory: no ruling in words; the timing rulings (it activates as a cost or mid-chain, where the FAQ says optional 'when...you can' effects miss timing) point to mandatory. The AST-080 'self-eligible' claim is contradicted by the same entry, so the c0 change looks cosmetic and Ignis's pre-errata script already matches both snapshots on it.
   - Paladin of White Dragon: no ruling on the attack ban's scope; the variant is kept on the printed era text.
   - Red-Eyes Darkness Metal Dragon: no corpus document names the card; the variant is kept on the printed era text.
   - Rescue Cat: no ruling on either point; the variant is kept on the printed era text.
   - Ring of Destruction: use on its controller's own turn, targeting your own monster, no Life Point ceiling and no once-per-turn limit rest on the printed text alone.
   - Sangan: the variant mapped to Edison and Tengu is the c0 pre-errata script, which has no Deck-verification step; the card FAQ and Konami's Machina Mayhem and Storm of Ragnarok rulings keep it in force. No ruling on a name lock or a once-per-turn limit.
   - Senet Switch: the second difference (Main Monster Zone only) is not a ruling; the rulebook shows five Monster Zones, so the two texts play alike. The list now uses the modern card.
   - Spirit Ryu: no corpus document names the card; whether its boost was Spell Speed 1 rests on the printed text and the upstream script's comment.
   - Stronghold the Moving Fortress: no ruling names the card; rulings on other cards' one-shot 'ATK becomes' effects favour set-not-add but suggest the variant's final-set is too strong for later modifiers.
   - Super Rejuvenation: no ruling on whose Tribute counts when the opponent Tributes your Dragon.
   - Toon Mermaid: neither the attack lock after a Normal or Flip Summon nor a Level-based Tribute is addressed; both are edge cases reachable only through effects that override its Summoning rules.
   - Toon Summoned Skull: the 'Summoned' versus 'Special Summoned' attack lock is decided only by inference (period rulings put Toon Monsters on the field by Special Summon).
   - Vampire Lord: no ruling on the once-per-turn clause and neither script implements it; whether it changes any play is a classification question.
   - Witch of the Black Forest: no ruling on repeated use or on a same-turn follow-up; the Deck-verification step is kept in force at both snapshots by Konami's own rulings.
   - Wulf, Lightsworn Beast: nothing names the card; whether any card in the pool could Special Summon it by a non-effect route is a pool question the corpus cannot answer.
   - Xy Dragon Cannon: whether the era card could return from banishment after a proper Summon is decided only by inference; the 2005 UDE page says 'except', the 2008 and 2009 FAQ pages name only the Extra Deck and the Graveyard, and no ruling names the banished zone.
   - Xyz Dragon Cannon: whether the era card could return from banishment after a proper Summon is decided only by inference; the 2005 UDE page says 'except', the 2008 and 2009 FAQ pages name only the Extra Deck and the Graveyard, and no ruling names the banished zone.
   - Xz Tank Cannon: whether the era card could return from banishment after a proper Summon is decided only by inference; the 2005 UDE page says 'except', the 2008 and 2009 FAQ pages name only the Extra Deck and the Graveyard, and no ruling names the banished zone.
   - Blast Held by a Tribute: no ruling on a Tribute-Set attacker.
   - Blaze Accelerator: one FAQ line says the Pyro monster must still be sent if the target is removed in response, another line in the same entry says the effect disappears. If the second governs the remaining difference is also cosmetic.
   - Boss Rush: whose destroyed monsters count, face-down monsters and Big Core rest on the printed text alone.
   - Elemental HERO Divine Neos: the only ruling is OCG; nothing TCG addresses the three claimed differences.
   - Evil HERO Dark Gaia: no ruling on combined versus original ATK or on the position change being mandatory.
   - Ido the Supreme Magical Force: that Setting was allowed under 'cannot Summon' rests on the rulebook's rule that a Set monster is not Summoned and a ruling on another card.
   - Masked Beast Des Gardius: never-revivable rests on the class rule for 'except' wording, not on a ruling naming the card; who may receive the Mask is unresolved.
   - Mustering of the Dark Scorpions: no ruling on the second Don Zaloog.
   - Red-Eyes Wyvern: the activation condition, targeting and the B. Chick exclusion rest on the printed text alone.
   - Soul Rope: no document names the card. The rulebook's Damage Step limit and its definition of 'destroyed' leave no case in which the era card triggered where the modern one does not; a card-specific Damage Step permission for Soul Rope would change that and the corpus shows none.
   - Swap Frog: no ruling on a face-down monster milled for its effect, or on the 'Frog the Jam' exclusion.
   - Totem Dragon: the re-activation after a negation rests on the FAQ's class ruling (Treeborn Frog), not an entry for the card.
   - Tri-Blaze Accelerator: a failed send or a failed destruction, and targeting, rest on the printed text; the sister card Blaze Accelerator is ruled to target with the same wording.
   - Wild Fire: destroying one versus all Blaze cards and Set copies rest on the printed text alone.
   - Evil HERO Infernal Prodigy: the FAQ says a second Tribute of the same copy loses the first End Phase draw, so play looks the same either way; that is an inference, not a ruling on the limit.
   - Necrovalley: at Edison, Konami's 2009 Raging Battle ruling (Lava Dragon's non-targeting effect does not resolve under Necrovalley) and the FAQ entries for Agido and Exchange of the Spirit say non-targeting Graveyard movers were already negated; the card's own FAQ sentence says only effects that target were. Whether the Konami document outranks it across the 2010 wording change is the owner's call.
   - YZ-Tank Dragon: the FAQ wording on the four contact-Fusion monsters changed between 2005 and 2008-12; whether the two-clause text was already in force at Edison is an inference.
   - Anteatereatingant: that the era card was unrevivable rests on the FAQ's class rule for 'except' wording, not on a ruling naming the card.
   - Armored Glass: period sources use 'Equip Spell Card' and 'Equip Card' inconsistently for equipped Union monsters; none names this card.
   - Dimension Distortion: nothing says whether the era card could take the opponent's banished monster; the restriction comes from an OCG-derived implementation.
   - Spirit's Invitation: who chooses the returned monster rests on the rulebook's general rule for 'select'; the shipped text is OCG-derived.
