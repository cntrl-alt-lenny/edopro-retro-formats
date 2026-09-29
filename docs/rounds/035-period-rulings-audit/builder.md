<!-- fw-report
round: 035-period-rulings-audit
role: builder
branch: builder/035-period-rulings-audit
head: b74b504973b9cad958f1de7bfc570bd5943471ac
os: macOS 27.0
python: 3.9.6
written: 2026-09-29T10:34:25Z
-->
## Verified

Every project command ran with Python 3.13.15 (Homebrew; `python3` on this machine is 3.9.6, below the project floor), on macOS arm64, on branch `builder/035-period-rulings-audit`. `python3 tools/fw.py start --role builder --round 035-period-rulings-audit` → exit 0. Base `origin/main` = `d5ff978`. **Code head `b74b504`**; the report commit above it touches only this file. CI at the code head: `https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36555947252` → `engine`, `check (3.10)`, `check (3.13)` all success; engine `engine-tests: executed=51 skipped=0 failures=0 errors=0 (required: at least 51 executed, 0 skipped)`; `Ran 1091 tests … OK (skipped=51)` on the check jobs; `build --check` step green on both Python versions.

### Per-card verdicts and the action taken (part A; sources and passages: `docs/research/period-rulings-generated-scripts.md`)

"Contradicted" is used only where a Konami-authored document that was current at the snapshot says the opposite. Rows marked "range not shown" rest on UDE card FAQ / Netrep answers whose range in force at 2010-04-24 or 2011-09-17 is unresolved for the whole class (the FAQ was Konami-hosted 2008-12-15, identical on both hosts in 2009-02, and no capture of either host is later; Konami's Gameplay page of 2010-03-22 and 2011-09-18 does not link it). n/a = the record's own chronology puts the erratum before that snapshot.

| # | card | script's difference | GOAT | Edison | Tengu | action |
|---|---|---|---|---|---|---|
| 1 | Metalzoa `600000001` | never revivable | unresolved | **contradicted** | n/a (erratum 2011-08-13) | **C: card removed, record cosmetic** |
| 2 | Super Vehicroid - Stealth Union `600000002` | equips only your own monster | n/a | unresolved (printed text only) | n/a (erratum 2011-06-01) | none; rulings record added |
| 3 | Goddess of Whim `600000004` | no once-per-turn limit | unresolved | unresolved (2008-12 ruling contradicts; range not shown) | same | none; owner list |
| 4 | Strike Ninja `600000005` | limit per copy | unresolved | unresolved (no ruling) | unresolved | none; rulings record added |
| 5 | Green Baboon `600000006` | (a) Damage Step activation; (b) no face-up requirement | n/a | (a) **contradicted** (Konami errata lists); (b) unresolved (UDE; range not shown) | same | **C: (a) removed from the script; (b) kept, owner list** |
| 6 | Rise of the Snake Deity `600000007` | Damage Step activation, so battle destruction triggers it | n/a | **contradicted** (Konami rulebook; UDE Netrep agrees) | **contradicted** | **C: card removed, record cosmetic** |
| 7 | Malefic Blue-Eyes `600000008` | never revivable | n/a | **contradicted** | **contradicted** (Konami Extreme Victory rulings 2011-05-12) | **C: card removed, record cosmetic** |
| 8 | Soul Rope `600000009` | (a) Damage Step; (b) any destruction, not only by a card effect | n/a | (a) **contradicted**; (b) no ruling | same | **C: (a) record cosmetic, card removed; (b) `known-gap` again** |
| 9 | Gigantes `600000010` | strict nomi | unresolved | **contradicted** | **contradicted** | E: not shipped; number retired |
| 10 | The Rock Spirit `600000011` | strict nomi | unresolved | **contradicted** | **contradicted** | E: not shipped; retired |
| 11 | Garuda the Wind Spirit `600000012` | strict nomi | unresolved | **contradicted** | **contradicted** | E: not shipped; retired |
| 12 | VW-Tiger Catapult `600000013` | strict nomi | n/a | **contradicted** | **contradicted** | E: not shipped; retired |
| 13 | Gladiator Beast Heraklinos `600000014` | strict nomi | n/a | **contradicted** | **contradicted** (erratum 2011-10-04 follows Tengu) | E: not shipped; retired |
| 14 | Dark Master - Zorc `600000015` | no per-turn limit on rolling | unresolved | unresolved (Netrep 2007-10-11 contradicts; range not shown) | same | E: not shipped (not `supported`); owner list |
| 15 | Dice Re-Roll `600000016` | each copy grants a re-roll | unresolved | unresolved (a UDE ruling supports; range not shown) | same | E: not shipped (not `supported`) |
| 16 | Second Coin Toss `600000017` | each copy redoes a toss | unresolved | unresolved (a UDE ruling contradicts; range not shown) | same | E: not shipped; owner list |

The class answers (research §3, §4, §5):
- **Nomi.** In the TCG a monster whose text reads "cannot be Normal Summoned or Set. This card can only be Special Summoned by …" could be revived after one proper Special Summon; only "cannot be Special Summoned **except** by …" locked it. Konami's rulebook (v7.0 capture 2008-12-30, v7.1 2010-03-30, v7.2 2011-05-16, v8.0 linked from Konami's own page captured 2011-09-18; phrase-searched in each): "You cannot use a card effect to Special Summon those monsters from your hand, Deck, or the Graveyard unless it was properly Special Summoned first." Konami's Extreme Victory rulings (compiled 2011-05-12) for Meklord Astro Dragon Asterisk, text "can only be Special Summoned by": "If you Special Summon this card correctly, it can later be Special Summoned back from the Graveyard." Konami's strategy article (page-printed date 2009-12-07; **earliest capture 2015-11-06, so the date is the page's claim**) draws the same line. GOAT: unresolved (the UDE page captured 2005-07-01 already has the entries; a capture date is not an effective date). The community "strict nomi" reading of `edison-behaviour-gaps.md` §2 has no period TCG source; a dated note is added there, nothing deleted.
- **Damage Step.** Konami's rulebook v7.0–8.0: "During the Damage Step, you can only activate Counter Trap Cards, or cards with effects that directly change a monster's ATK or DEF."
- **UDE rulings' range in force: unresolved** (above).
- **Class count** (§7): of the 120 records with a `functional` transition (104 excluding these sixteen), none carries a ruling-type source on the functional transition; 80 also never mention a ruling, FAQ, Netrep answer or judge list in their functional summaries or review notes; 22 are corroborated by the EdisonFormat.com list (a community list). Counted by a script over `sources`/`summary`/`review.notes`; not adjudicated.
- **Leads** (§8): Zorc, Second Coin Toss, Goddess of Whim, Rise of the Snake Deity, Green Baboon and Dice Re-Roll **confirmed at their underlying UDE/Konami source** (with corrections below); the four OCG revival rulings **confirmed at Konami's OCG database** (OCG only); Ignis's GOAT list **partly confirmed**: it carries the modern code of six of the eight round-034 cards, and VW-Tiger and Heraklinos are not in it.

### Part B: the gate

- The ten new gate tests, failing first (before the rule existed): `tests.test_custom_cards.CustomCardValidationTest` → `Ran 40 tests … FAILED (failures=28)` (28 failing test or subtest results), one per rejected shape, e.g. `AssertionError: 'custom-card.rulings-check-malformed' not found in set()`; with the rule: `Ran 40 tests … OK`.
- Codes: `custom-card.rulings-check-missing`, `custom-card.rulings-check-malformed` (errors); `custom-card.contradicting-ruling-unaccepted` (error: `contradicts` + `in_force: shown` and no complete `owner_decision`); `custom-card.contradicting-ruling-range-unresolved` (warning: `contradicts` + `not-shown`); an unknown source id is the existing `sources.unresolved`. Field documented in `schemas/custom-card.schema.json` and `docs/errata.md` ("The rulings gate"). A schema edit alone enforces nothing; the rule is in `retroformats/validate.py`.
- **The gate on the real data, before the corrections** (all eight records given honest checks, the four cards C removes still present): `validate` → `ERROR [custom-card.contradicting-ruling-unaccepted]` for Metalzoa (2), Green Baboon (1), Rise of the Snake Deity (1), Malefic Blue-Eyes (3), Soul Rope (1) = 8 errors, exactly the five cards C corrects; nothing else.
- After C every remaining record passes. `tests.test_custom_cards.LiveGeneratedOutputTest.test_every_live_record_passes_the_rulings_gate` pins it.

### Commands (final tree)

- `python -m retroformats validate` → exit 0, `0 errors, 564 warnings` (main: `0 errors, 563`). Sorted `WARNING`/`ERROR`-line diff against `main` (main's `validate` run in this checkout before any change), complete, explained line by line:
  - **new (3)** `custom-card.contradicting-ruling-range-unresolved`: `c600000004.json` `searched[0]` (Goddess of Whim: the 2008-12 FAQ says once per turn); `c600000006.json` `searched[0]` and `searched[1]` (Green Baboon: the Netrep answer and the FAQ entry on a face-down Beast). Each is a tracked owner question, by design.
  - **new (2)** `format.erratum-known-divergence` for Soul Rope, one for `formats/2010-03-edison` and one for `formats/2011-09-tengu` (its residual 2015 difference is a known gap again).
  - **gone (4)** `format.parity-omits-historical` for `formats/2005-04-goat`: Malefic Blue-Eyes White Dragon, Metalzoa, Rise of the Snake Deity, Soul Rope (the warning said a historical state applied at 2005-04-01 that Ignis's list does not substitute; these records no longer carry a usable historical implementation: three are cosmetic-only, and Soul Rope's baseline is a known gap).
  - 563 + 3 + 2 − 4 = 564. Edison's known divergences 38 → 39, Tengu's 32 → 33 (Soul Rope). No other line differs.
- `python -m retroformats materialize` → pools unchanged (Edison 3674, Tengu 4563); `git status` clean afterwards. `python -m retroformats build --check` → exit 0 at head (also exit 0 under the system Python 3.9.6, and in CI on 3.10 and 3.13).
- `python -m unittest discover -t . -s tests -v` → `Ran 1091 tests … OK (skipped=51)`; the 51 skips are exactly the engine tests (main: 1081 / skipped 59).
- `python scripts/engine_env.py prepare --dest <scratch>` → exit 0; `run --dest <scratch> --expect-at-least 51` → `engine-tests: executed=51 skipped=0 failures=0 errors=0 (required: at least 51 executed, 0 skipped)`. **Floor 59 → 51** (`.github/workflows/ci.yml`, `docs/engine-testing.md`) = the net: removed 6 Metalzoa tests, 3 Rise, 4 Malefic, 2 Soul Rope (15); added 4 (`RetiredCardsUseTheModernCardTest`: one each for Metalzoa, Malefic, Rise, Soul Rope), 1 Green Baboon (two copies) and round 034's 2 `test_script_origin` tests (7); 59 − 15 + 7 = 51. The corrected Green Baboon Damage Step test replaces its old one one-for-one. `tests.test_engine_env.WorkflowTest.test_the_required_count_is_the_number_of_engine_tests` passes.
- `python scripts/generate_format_atlas.py --check` → exit 0. `python3 tools/fw.py check` → `0 error(s), 0 warning(s)`.
- **Hashes** (`build_lflist`): Edison `0x9CC869A4` → **`0xC2ED2D57`**; Tengu `0x45A6E446` → **`0x410A9E85`**; GOAT `0x28E9FC02` unchanged, and `git diff origin/main HEAD -- dist/lflists/2005-04-goat.lflist.conf` is empty. Each old value is still asserted: swapping the removed cards' generated codes back in (`swap_retired_forward`, `tests/helpers.py`) reproduces Edison `0x9CC869A4` (all four) and Tengu `0x45A6E446` (Rise, Malefic, Soul Rope; Metalzoa was never in Tengu's list); from there `swap_back` reproduces the round-031 and pre-round-029 values (`0xD5E90AFA`, `0x8432B710`, Tengu `0x0C878718`).
- `git diff origin/main HEAD -- dist/lflists/` — every changed line, and each is explained by a card in C:
  ```
  2010-03-edison.lflist.conf            2011-09-tengu.lflist.conf
  +50705071 3 --Metalzoa                (none: Metalzoa was never in Tengu's list)
  +16067089 3 --Rise of the Snake Deity +16067089 3 --Rise of the Snake Deity
  +9433350 3 --Malefic Blue-Eyes …      +9433350 3 --Malefic Blue-Eyes …
  +37383714 3 --Soul Rope               +37383714 3 --Soul Rope
  -600000001 3 --Metalzoa (pre-errata)  (none)
  -600000007 3 --Rise …(pre-errata)     -600000007 3 --Rise … (pre-errata)
  -600000008 3 --Malefic … (pre-errata) -600000008 3 --Malefic … (pre-errata)
  -600000009 3 --Soul Rope (pre-errata) -600000009 3 --Soul Rope (pre-errata)
  ```
  (each modern code added with count 3, its generated code removed). `dist/databases/retro-formats.cdb` loses four rows; `dist/scripts/` loses `c600000001/7/8/9.lua` and `c600000006.lua` loses one line; `dist/scripts/LICENSES.md` loses four rows. `data/cards/index.json`: regenerated with `python -m retroformats.importers.card_index --babelcdb <pinned BabelCDB>` → only the four rows removed.

### Part C: failing first, and the red runs

- **Green Baboon** (script change): the corrected test `test_a_beast_destroyed_by_battle_offers_neither_card_in_the_damage_step` fails on the round-031 script: locally `AssertionError: True is not false : so is the period card: Konami's lists say so` (edison and tengu); CI red run `https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36555978062` (scratch branch `scratch/035-red-green-baboon`: head plus `EFFECT_FLAG_DAMAGE_STEP` restored in the canonical and dist script; `check` jobs green, `engine-tests: executed=51 skipped=0 failures=2 errors=0`).
- **The four removed cards** (`RetiredCardsUseTheModernCardTest`, under both formats): red run `https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36556011921` (scratch branch `scratch/035-red-retired-cards`: the four generated codes put back in the Edison list and the three Tengu carried; `engine-tests: executed=51 skipped=0 failures=14 errors=0`, failures in `test_metalzoa_…`, `test_malefic_blue_eyes_…`, `test_rise_of_the_snake_deity_…`, `test_soul_rope_…`, every one an `AssertionError: <modern code> not found in {…listed codes…}`); the `check (3.13)` job is red there too, because `dist/` no longer matches canonical data. Green at head: run `…/36555947252` above. I pushed that one branch with `--no-verify` (the local pre-push hook blocks a red `dist/`, by design).
- The preservation rule (materializer test) was mutation-checked: altering the retained old summary in `soul-rope.json`'s review notes makes `test_every_target_matches_the_real_on_disk_file_exactly` fail; restored.

### Part D: round 034's engineering, carried over (each failing first)

- `45de718` (cherry-picked; ci.yml floor conflict resolved at 51): **the upstream tie** `custom-card.upstream-not-own-script`. Validator test (round 034's, added in `17ca8c3`), rule removed: `tests.test_custom_cards.CustomCardValidationTest.test_a_derived_scripts_upstream_must_be_the_script_of_its_own_card` → `FAILED (failures=11)`, `AssertionError: 'custom-card.upstream-not-own-script' not found in set()` for each rejected path; with the rule `OK`. Engine test, `c600000004.json`'s `upstream.path` pointed at Strike Ninja's script: `ERROR [custom-card.upstream-not-own-script] … 'official/c41006930.lua' is not the script of the card this row aliases`, and `FAIL: test_every_derived_scripts_upstream_is_the_script_of_its_own_card … AssertionError: False is not true : official/c41006930.lua is not Project Ignis's script for Goddess of Whim (Retro Formats) (67959180)`; restored. **The similarity pin**, limit 0.40 kept: with `ORIGINAL_MAX_RATIO = 0.45`, `FAIL: test_the_similarity_limit_is_not_changed_without_a_brief … AssertionError: 0.4 != 0.45` and `FAIL: test_the_limit_is_what_too_close_compares_against`; restored (a stale `.pyc` briefly hid the restore; cleared).
- `073828d` (cherry-picked without its dist file): **the cdb bytes independent of the SQLite version**. The live database now holds four rows and fits in three pages, so the two page-splitting tests build a sixteen-row database of their own (`LiveGeneratedOutputTest._sixteen_cards`); with `_zero_unused_page_space` disabled, `FAIL: test_database_bytes_carry_no_stale_bytes_in_unused_page_space … AssertionError: b'\x00\x00…' != b'\n\xa3\x08A…'`; with it, `OK`. `build --check` exit 0 under Python 3.13.15 and 3.9.6 here and in CI on Linux 3.10 and 3.13.
- The similarity gate's other gap (an `original` script is measured only against its own alias's Ignis script) stays open, in `docs/roadmap.md` item 7 and `docs/engine-testing.md`. Not touched.

### Each derived script against its Ignis source

Ignis `official/` at `383bfbd62cefc0a28e075acfb78b0bb8203b94c7` (the pinned checkout; `diff -u`, header lines elided where they are pure notices):
- **`c600000004.lua` (Goddess of Whim)**: unchanged this round. Differences: the 14-line notice header added; `aux.Stringid(id,0)` → `aux.Stringid(67959180,0)`; `e1:SetCountLimit(1)` removed.
- **`c600000005.lua` (Strike Ninja)**: unchanged this round. Header added; `aux.Stringid(id,0)` → `aux.Stringid(41006930,0)`; `e1:SetCountLimit(1,id)` → `e1:SetCountLimit(1)`.
- **`c600000006.lua` (Green Baboon)**: header added (its `Modified by` line now dated 2026-09-29 and stating only the face-up difference); `aux.Stringid(id,0)` → `aux.Stringid(46668237,0)`; `c:IsMonster() and c:IsRace(RACE_BEAST) and c:IsPreviousControler(tp) and c:IsPreviousPosition(POS_FACEUP)` → the same without `and c:IsPreviousPosition(POS_FACEUP)`. Against `main`'s copy of the script, the only code change is the removal of `e1:SetProperty(EFFECT_FLAG_DAMAGE_STEP)`, plus the header's `Modified by` line.
- **`c600000002.lua` (Stealth Union)** is `original` (MIT); no upstream; measured by `test_script_origin` (passes).

### Each changed record against `main`

The five `data/errata/` records and what changed (a sorted preservation rule now pins it: `tests/test_migration_materializer.py` `check_round_035_edit`: every round-031 passage survives, chronology unchanged, old summaries and implementation notes kept verbatim in `review.notes`, no source dropped):
- **`metalzoa.json`, `malefic-blue-eyes-white-dragon.json`, `rise-of-the-snake-deity.json`**: single-event sugar → full v2 (the sugar cannot carry a cosmetic transition, `model._desugar_v2_sugar`); `classification` and the transition's `kind` `functional` → `cosmetic`; `states[]`/`coverage` (`custom-script`) removed; one `implementation_metadata` entry `complete`, `tested: false`; **added** sources (Konami rulebook v7.1/v8.0, the Konami article, the Extreme Victory rulings, the card FAQ page, the UDE thread, the OCG database, as fits); **kept**: `effective`, `historical_text`, `modern_text`, every previous source, the whole previous `review.notes`; **moved** into `review.notes`, verbatim, with date and reason: the old transition summary, the round-029/031 implementation note and the old gap statement; new `summary` states the reading and its limits.
- **`soul-rope.json`**: `c0` (2012-09-29, the Damage Step words) `functional` → `cosmetic`, old summary moved to `review.notes`; `c1` (2015) stays `functional`; baseline state `custom-script` → `known-gap` (with reason and sources); metadata `partial` → `missing` with a new gap statement; sources added; the earlier review's own caveat ("the packet establishes … not that era policy independently permitted Damage Step activation") is resolved against the rulebook, in the notes.
- **`green-baboon-defender-of-the-forest.json`**: nothing reclassified. Added to `event.sources` and `sources`: the three Konami errata lists, the FAQ page, the UDE thread, the rulebook; appended to `review.notes` the Damage Step evidence, the face-up half, the "only 1 copy" bullet; appended to `implementation_metadata.reason` and `gap.behavioural_impact` a dated withdrawal of the Damage Step half. Nothing replaced.
- `data/custom-cards/`: four records deleted with their scripts; `c600000006.json`/`.lua` (script, `authorship.modified`, `not_reproduced`, `rulings_check`); `c600000002/4/5.json` gain `rulings_check`.

## Not verified

- A real EDOPro client loading `dist/`; Windows; Python 3.10 locally (CI `check (3.10)` passed at the code head).
- The Konami strategy article's text at its printed date: the earliest capture is 2015-11-06. Its role is corroboration; the anchors are the rulebook (four captures, 2008-12-30 to 2011-11-19) and the Extreme Victory rulings.
- **Whether any UDE card ruling stood at 2010-04-24 or 2011-09-17.** Nothing read shows it or withdraws it. Yugipedia says Konami later deemed them unofficial, citing a login-walled Konami Judge forum thread whose archived copy is the login page; the claim and its date are unestablished.
- The GOAT-era behaviour for the class, and the Damage Step position of any card-specific Konami exception not found; a separate ruling on a Trap's timing *after* the Damage Step ends (the engine handles it as for the modern card).
- The Japanese first printing of Dark Master - Zorc ("１ターンに１度"): read at Yugipedia's transcription, the printing itself not opened.
- Several Konami per-set ruling PDFs (Machina Mayhem, Starlight Road/Hidden Arsenal/Warriors' Strike/Starter Deck 2009, The Shining Darkness, Duelist Revolution, Absolute Powerforce, Stardust Overdrive, Ancient Prophecy, Raging Battle, Crimson Crisis) timed out from the Internet Archive; the five read (Extreme Victory, Hidden Arsenal 3, Storm of Ragnarok, Gold Series 3 / Tag Force 5, Starstrike Blast) hold none of the sixteen cards.
- Engine coverage is scenario coverage only: Green Baboon's "only 1 copy" bullet is a control test in one scenario (Dark Hole, two copies); Soul Rope's residual 2015 difference is unobservable here and is a `known-gap`.
- The 104-record class count is a script over source ids and text, not a reading of the sources.
- The `check` jobs of the `scratch/035-red-retired-cards` run are red by construction (see above); the `scratch/035-red-green-baboon` run's are green.

## Changed

- `docs/research/period-rulings-generated-scripts.md` (new): part A. `data/sources.json`: eighteen sources (Konami rulebook v8.0, Gameplay pages 2010-03-22 and 2011-09-18, three errata lists, Extreme Victory rulings, the strategy article, four Konami-hosted card FAQ pages, the UDE-hosted FAQ U–Z, three UDE Judge List threads, the Yugipedia rulings pointer, the Konami OCG database pages). `tests/fixtures/research-citation-backlog.json`: two entries removed (now registered), as the ratchet allows.
- `retroformats/model.py`, `retroformats/validate.py`, `schemas/custom-card.schema.json`, `docs/errata.md`: part B. `retroformats/custom_cards.py`: part D (cdb bytes). `retroformats/validate.py`: part D (upstream tie).
- `data/errata/*` (five), `data/custom-cards/*` (four deleted, four edited), `data/cards/index.json`, `dist/` (regenerated): part C.
- Tests: `tests/helpers.py` (`ROUND_035_RETIRED`, `RETIRED_PASSCODES`, `swap_retired_forward`, `swap_back`, …), `test_custom_cards.py` (the gate tests, retired-number and live-gate tests, upstream-tie and cdb tests), `test_tengu_format.py`, `test_tengu_format_gate.py`, `test_ocg1999_release_certification.py`, `test_yugi_kaiba_format_gate.py`, `test_shadow_migration.py`, `test_unordered_canonical_migration.py`, `test_last_will_v2.py`, `test_migration_materializer.py`, `test_script_similarity.py` (new, carried over), `tests/engine/test_shared_historical_scripts.py`, `test_edison_historical_scripts.py`, `test_script_origin.py`. Every old pin value is still asserted where it can be reached; nothing was deleted without a replacement named above; no rule loosened.
- `.github/workflows/ci.yml` and `docs/engine-testing.md`: floor 59 → 51. `docs/roadmap.md` item 7, `dist/README.md`, `formats/2011-09-tengu/notes.md`, a dated note in `docs/research/edison-behaviour-gaps.md` §2 (added, nothing deleted). `docs/state.md` **not changed**.

## Open questions

**The owner's thin-evidence list, in plain terms.** I changed no data for any of these (the round's rule); each is a product decision. A class decision comes first, because it settles most of them:

0. **Did the UDE-era card rulings still hold at Edison and Tengu?** They were published by UDE, mirrored by Konami on its own site on 2008-12-15, and no later copy of them exists. If you say they held unless Konami replaced them (as Konami did for Green Baboon's Damage Step), items 1–5 resolve themselves as below; if you say they did not, the printed English text stands. Nothing I found decides it.
1. **Goddess of Whim** (in both lists). Now: it can be activated as often as you like in a turn, chaining coin tosses. The other reading: once per turn, as the modern card. Rests on: printed text with no limit (now) versus the 2008-12 card FAQ, "It can only be used once per turn, during your Main Phase" (other reading).
2. **Green Baboon** (both lists). Now: it can come back when your Beast is destroyed *face-down* (for example by Torrential Tribute), because the printed text has no face-up requirement. The other reading: it cannot. Rests on: printed text (now) versus a UDE Netrep answer of 2007-09-28 and the card FAQ (other reading). Konami's own lists say nothing on it.
3. **Dark Master - Zorc** (not shipped; both lists use the modern card, one die roll per turn). The unshipped alternative is rolling repeatedly in a Main Phase, resting on the English printed text; against it, a UDE Netrep answer of 2007-10-11 and the Japanese printing's "once per turn" (OCG). If you accept item 0, the modern card is already right and nothing changes.
4. **Second Coin Toss** (not shipped; the modern card, limited by name). The alternative (each copy redoes a toss) rests on the printed "once per turn" per card; a UDE ruling says each toss can be redone once.
5. **Dice Re-Roll** (not shipped; modern: one re-roll per turn). The alternative, each copy giving its own re-roll, is what a UDE ruling supports and the printed text reads; not shipped because its range is not shown. If you accept item 0, it becomes a candidate.
6. **Super Vehicroid - Stealth Union** (Edison) equips only your own monsters, and **Strike Ninja** allows one use per copy, from printed text; no ruling either way was found. Left as they are.
7. **Soul Rope**: the modern card is used. The only difference left (the 2015 "by a card effect") is not observable in ordinary play; it is a `known-gap`.
8. **Elsewhere.** 104 other records call a change functional from printed text alone (none cites a ruling). Round 035 adjudicated none of them; whether to audit them is yours.

**For Brain.**
- **Premise corrections.** The brief's Rise lead points at thread `830322`, the post of 2007-08-31; the answer is the post of 2007-08-17 in that thread (the capture holds both). Project Ignis's GOAT list carries six of the eight round-034 cards, not all eight. Zorc's "once per turn" is in the Netrep answer, not in the card FAQ. Green Baboon: a further finding beyond the lead, Konami's lists forbid the Damage Step, contradicting the earlier FAQ.
- The rulings gate's severity choice: `contradicts` + `not-shown` is a **warning**, not an error, because the brief keeps thin-evidence cards unchanged yet requires them to pass; three warnings result (Goddess 1, Green Baboon 2). If you want the owner decision recorded in `owner_decision` once made, the field exists.
- Two scratch branches on `origin` from this round are not cleaned up: `scratch/035-red-green-baboon`, `scratch/035-red-retired-cards` (delete once the red evidence is accepted). Round 034's eight `scratch/034-red-*` branches and `builder/034-shared-scripts-batch-2` are untouched.
- The citation-registry ratchet needed workarounds for wayback URLs with query strings (the registry's original-URL extraction drops the query): the original URL is repeated in the source's `notes`. Not a framework problem; noted.
- Focused commits: research; the gate plus corrections (one commit, because the live-data tests couple them); the upstream tie; its validator test; the cdb bytes; the docs. `build --check` and the full suite are green at head (checked at each pushed head in CI).
