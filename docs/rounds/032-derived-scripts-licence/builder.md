## Verified

All project commands ran with `/opt/homebrew/bin/python3.13` (`python3` here is 3.9) on macOS arm64, on branch `builder/032-derived-scripts-licence`, code head `2e5abb5d4ec1481fbd33c77c80478aef7ae96129` (pushed; the report commit above it touches only this file). `python3 tools/fw.py start --role builder --round 032-derived-scripts-licence` → exit 0 at `fb726e3`. I read Project Ignis's scripts for the five cards (allowed this round), their `COPYING` and `README.md`, all from the pinned checkout `scripts/engine_env.py prepare` fetched (`git rev-parse HEAD` = `383bfbd62cefc0a28e075acfb78b0bb8203b94c7`).

### Commands

- `python -m retroformats validate` → exit 0, `0 errors, 563 warnings`. Warning diff against `3a3b409` (validated in a scratch worktree at that commit, same interpreter): the sorted `WARNING`/`ERROR` lines are identical (`diff` exit 0). No new codes.
- `python -m retroformats build --check` → exit 0 at head.
- `python -m unittest discover -t . -s tests -v` → exit 0, `Ran 1081 tests … OK (skipped=59)`; all 59 skips are `ocgcore + pinned checkouts not available` (the engine tests). 3a3b409 had 1069 / 56: +9 in `tests/test_custom_cards.py` (net: 2 old authorship tests replaced by 10, plus 1 licence-files test) and +3 engine tests.
- `python scripts/engine_env.py prepare --dest <scratch>/engine` → exit 0 (ocgcore built from the pinned source, Apple clang 21). `run --dest … --expect-at-least 59` → exit 0: `engine-tests: executed=59 skipped=0 failures=0 errors=0 (required: at least 59 executed, 0 skipped)`.
- CI at the code head: https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/36334182654 (`2e5abb5`): `check (3.10)`, `check (3.13)`, `engine` all success; engine log: `engine-tests: executed=59 skipped=0 failures=0 errors=0 (required: at least 59 executed, 0 skipped)`, and the three `test_script_origin` tests each `... ok`.
- `git diff 3a3b409 HEAD -- dist/lflists/ dist/databases/` → empty (Edison, Tengu and GOAT lists and `retro-formats.cdb` byte-identical, so the GOAT hash `0x28E9FC02` and every list entry set are unchanged). `git diff --quiet 3a3b409 HEAD -- data/errata formats` → exit 0: no erratum record, chronology or evidence changed.
- `python scripts/generate_format_atlas.py --check` → exit 0. `python3 tools/fw.py check` → `0 error(s), 0 warning(s)`.
- Engine floor 56 → 59 = the three tests added in `tests/engine/test_script_origin.py`; `tests/test_engine_env.py::test_the_required_count_is_the_number_of_engine_tests` passes.

### Behaviour unchanged, and still red on the modern script

With the rebased scripts, all 56 pre-existing engine tests pass unchanged (run above). I then replaced each rebased script in `dist/scripts/` with Ignis's modern `official/c<alias>.lua` and ran `engine_env.py run` (each reverted afterwards; `git status` clean):

| generated script ← modern script | failing tests (each under `edison` and `tengu`) |
|---|---|
| `c600000004` ← `c67959180` | `test_the_period_card_can_be_activated_again_in_the_same_turn` (failures=2) |
| `c600000005` ← `c41006930` | `test_two_copies_can_each_use_the_effect_in_the_same_turn` (failures=2) |
| `c600000006` ← `c46668237` | `test_a_beast_destroyed_by_battle_offers_the_period_card_but_not_the_modern_one`, `test_a_face_down_beast_destroyed_lets_the_period_card_special_summon_itself` (failures=4) |
| `c600000007` ← `c16067089` | `test_vennominon_destroyed_in_battle_lets_the_period_card_summon_vennominaga` (failures=2) |
| `c600000009` ← `c37383714` | `test_a_monster_destroyed_in_battle_lets_the_period_card_special_summon_from_the_deck` (failures=2) |

Each line was `engine-tests: executed=56 skipped=0 failures=N errors=0` (these ran before the three new tests existed).

### The five upstream diffs

`diff -u <pinned CardScripts>/<upstream.path> data/custom-cards/c<passcode>.lua`. Each is the header plus the period edit; the only other edit is `aux.Stringid(id,0)` → `aux.Stringid(<modern code>,0)` where upstream has one, because the generated row carries no strings (the `.cdb` must stay byte-identical) and `id` is the generated passcode. Ignis's own `pre-errata/` scripts do the same (e.g. `c511002631.lua`: `aux.Stringid(26202165,0)`). Every line of upstream is otherwise kept, including its original two name lines.

```diff
--- CardScripts@383bfbd6:official/c67959180.lua
+++ data/custom-cards/c600000004.lua
@@ -1,14 +1,27 @@
+--SPDX-License-Identifier: AGPL-3.0-or-later
+--Goddess of Whim (historical implementation, Retro Formats)
+--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c67959180.lua
+--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
+--Modified by edopro-retro-formats on 2026-09-27: removed the once-per-turn limit, which the 2012 erratum added; the effect description is read from the modern card's strings.
+--This modified file is licensed, like its upstream, under the GNU Affero General
+--Public License, version 3 or (at your option) any later version. The licence
+--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
+--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
+--
+--Period text: "Toss a coin and call Heads or Tails. Call it right and this card's ATK
+--will be doubled during this turn. Call it wrong and it will be halved during this turn."
+--
+--See data/custom-cards/c600000004.json for what this script does not reproduce.
 --きまぐれの女神
 --Goddess of Whim
 local s,id=GetID()
 function s.initial_effect(c)
 	--Toss a coin and either double or halve ATK
 	local e1=Effect.CreateEffect(c)
-	e1:SetDescription(aux.Stringid(id,0))
+	e1:SetDescription(aux.Stringid(67959180,0))
 	e1:SetCategory(CATEGORY_COIN)
 	e1:SetType(EFFECT_TYPE_IGNITION)
 	e1:SetRange(LOCATION_MZONE)
-	e1:SetCountLimit(1)
 	e1:SetTarget(s.target)
 	e1:SetOperation(s.operation)
 	c:RegisterEffect(e1)
--- CardScripts@383bfbd6:official/c41006930.lua
+++ data/custom-cards/c600000005.lua
@@ -1,15 +1,30 @@
+--SPDX-License-Identifier: AGPL-3.0-or-later
+--Strike Ninja (historical implementation, Retro Formats)
+--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c41006930.lua
+--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
+--Modified by edopro-retro-formats on 2026-09-27: the use limit is per copy (SetCountLimit(1), not SetCountLimit(1,id)), as the period text carries no name qualifier; the effect description is read from the modern card's strings.
+--This modified file is licensed, like its upstream, under the GNU Affero General
+--Public License, version 3 or (at your option) any later version. The licence
+--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
+--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
+--
+--Period text: "You can remove this card from play until the End Phase of this turn by
+--removing 2 DARK monsters in your Graveyard from play. You can use this effect during
+--either player's turn. You can only use this effect once per turn."
+--
+--See data/custom-cards/c600000005.json for what this script does not reproduce.
 --速攻の黒い忍者
 --Strike Ninja
 local s,id=GetID()
 function s.initial_effect(c)
 	--remove
 	local e1=Effect.CreateEffect(c)
-	e1:SetDescription(aux.Stringid(id,0))
+	e1:SetDescription(aux.Stringid(41006930,0))
 	e1:SetCategory(CATEGORY_REMOVE)
 	e1:SetType(EFFECT_TYPE_QUICK_O)
 	e1:SetRange(LOCATION_MZONE)
 	e1:SetCode(EVENT_FREE_CHAIN)
-	e1:SetCountLimit(1,id)
+	e1:SetCountLimit(1)
 	e1:SetCost(s.rmcost)
 	e1:SetTarget(s.rmtg)
 	e1:SetOperation(s.rmop)
--- CardScripts@383bfbd6:official/c46668237.lua
+++ data/custom-cards/c600000006.lua
@@ -1,14 +1,30 @@
+--SPDX-License-Identifier: AGPL-3.0-or-later
+--Green Baboon, Defender of the Forest (historical implementation, Retro Formats)
+--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c46668237.lua
+--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
+--Modified by edopro-retro-formats on 2026-09-27: no face-up requirement, and activation allowed in the Damage Step (EFFECT_FLAG_DAMAGE_STEP), as the period text has neither restriction; the effect description is read from the modern card's strings.
+--This modified file is licensed, like its upstream, under the GNU Affero General
+--Public License, version 3 or (at your option) any later version. The licence
+--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
+--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
+--
+--Period text: "When a Beast-Type monster you control is destroyed and sent to the
+--Graveyard, you can pay 1000 Life Points to Special Summon this card from your hand or
+--the Graveyard."
+--
+--See data/custom-cards/c600000006.json for what this script does not reproduce.
 --森の番人グリーン・バブーン
 --Green Baboon, Defender of the Forest
 local s,id=GetID()
 function s.initial_effect(c)
 	--spsummon
 	local e1=Effect.CreateEffect(c)
-	e1:SetDescription(aux.Stringid(id,0))
+	e1:SetDescription(aux.Stringid(46668237,0))
 	e1:SetCategory(CATEGORY_SPECIAL_SUMMON)
 	e1:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_TRIGGER_O)
 	e1:SetRange(LOCATION_HAND|LOCATION_GRAVE)
 	e1:SetCode(EVENT_TO_GRAVE)
+	e1:SetProperty(EFFECT_FLAG_DAMAGE_STEP)
 	e1:SetCondition(s.condition)
 	e1:SetCost(Cost.PayLP(1000))
 	e1:SetTarget(s.target)
@@ -16,7 +32,7 @@
 	c:RegisterEffect(e1)
 end
 function s.cfilter(c,tp)
-	return c:IsMonster() and c:IsRace(RACE_BEAST) and c:IsPreviousControler(tp) and c:IsPreviousPosition(POS_FACEUP)
+	return c:IsMonster() and c:IsRace(RACE_BEAST) and c:IsPreviousControler(tp)
 		and c:IsPreviousLocation(LOCATION_MZONE) and (c:GetPreviousRaceOnField()&RACE_BEAST)~=0
 end
 function s.condition(e,tp,eg,ep,ev,re,r,rp)
--- CardScripts@383bfbd6:official/c16067089.lua
+++ data/custom-cards/c600000007.lua
@@ -1,3 +1,18 @@
+--SPDX-License-Identifier: AGPL-3.0-or-later
+--Rise of the Snake Deity (historical implementation, Retro Formats)
+--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c16067089.lua
+--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
+--Modified by edopro-retro-formats on 2026-09-27: activation allowed in the Damage Step (EFFECT_FLAG_DAMAGE_STEP), so destruction by battle also triggers it, as the period text has no "except by battle".
+--This modified file is licensed, like its upstream, under the GNU Affero General
+--Public License, version 3 or (at your option) any later version. The licence
+--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
+--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
+--
+--Period text: "Activate only when a face-up "Vennominon the King of Poisonous Snakes"
+--you control is destroyed. Special Summon 1 "Vennominaga the Deity of Poisonous Snakes"
+--from your hand or Deck."
+--
+--See data/custom-cards/c600000007.json for what this script does not reproduce.
 --蛇神降臨
 --Rise of the Snake Deity
 local s,id=GetID()
@@ -7,6 +22,7 @@
 	e1:SetCategory(CATEGORY_SPECIAL_SUMMON)
 	e1:SetType(EFFECT_TYPE_ACTIVATE)
 	e1:SetCode(EVENT_DESTROYED)
+	e1:SetProperty(EFFECT_FLAG_DAMAGE_STEP)
 	e1:SetCondition(s.condition)
 	e1:SetTarget(s.target)
 	e1:SetOperation(s.activate)
--- CardScripts@383bfbd6:official/c37383714.lua
+++ data/custom-cards/c600000009.lua
@@ -1,3 +1,17 @@
+--SPDX-License-Identifier: AGPL-3.0-or-later
+--Soul Rope (historical implementation, Retro Formats)
+--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c37383714.lua
+--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
+--Modified by edopro-retro-formats on 2026-09-27: no "by a card effect" requirement (REASON_EFFECT), and activation allowed in the Damage Step (EFFECT_FLAG_DAMAGE_STEP), as the period text has neither restriction.
+--This modified file is licensed, like its upstream, under the GNU Affero General
+--Public License, version 3 or (at your option) any later version. The licence
+--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
+--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
+--
+--Period text: "Activate only by paying 1000 Life Points when a monster you control is
+--destroyed and sent to the Graveyard, Special Summon 1 Level 4 monster from your Deck."
+--
+--See data/custom-cards/c600000009.json for what this script does not reproduce.
 --魂の綱
 --Soul Rope
 local s,id=GetID()
@@ -7,6 +21,7 @@
 	e1:SetCategory(CATEGORY_SPECIAL_SUMMON)
 	e1:SetType(EFFECT_TYPE_ACTIVATE)
 	e1:SetCode(EVENT_TO_GRAVE)
+	e1:SetProperty(EFFECT_FLAG_DAMAGE_STEP)
 	e1:SetCondition(s.condition)
 	e1:SetCost(Cost.PayLP(1000))
 	e1:SetTarget(s.target)
@@ -14,7 +29,7 @@
 	c:RegisterEffect(e1)
 end
 function s.cfilter(c,tp)
-	return c:IsReason(REASON_EFFECT) and c:IsReason(REASON_DESTROY) and c:IsMonster()
+	return c:IsReason(REASON_DESTROY) and c:IsMonster()
 		and c:IsPreviousControler(tp) and c:IsPreviousLocation(LOCATION_MZONE)
 end
 function s.condition(e,tp,eg,ep,ev,re,r,rp)
```

### Similarity (item 5)

`retroformats/script_similarity.py`: code lines (comments and blank lines dropped, whitespace collapsed), `difflib.SequenceMatcher(autojunk=False)` line ratio; shared 4-line windows reported only. It reproduces the round-031 Verifier's ratios exactly. Each script against Ignis's script for its alias at `383bfbd6`:

| script | upstream | ratio | identical lines | shared 4-line windows | gate (≥ 0.40 flags) |
|---|---|---|---|---|---|
| Night Assailant, removed (`8f1deb6:data/custom-cards/c600000003.lua`) | `official/c16226786.lua` | 0.69 | 36 of 49 | 11 of 46 | FLAG |
| Goddess of Whim, round 031 (`3a3b409:…c600000004.lua`) | `official/c67959180.lua` | 0.72 | 23 of 32 | 4 of 29 | FLAG |
| Strike Ninja, round 031 (`3a3b409:…c600000005.lua`) | `official/c41006930.lua` | 0.51 | 21 of 39 | 1 of 36 | FLAG |
| Green Baboon, round 031 (`3a3b409:…c600000006.lua`) | `official/c46668237.lua` | 0.61 | 21 of 38 | 2 of 35 | FLAG |
| Rise of the Snake Deity, round 031 (`3a3b409:…c600000007.lua`) | `official/c16067089.lua` | 0.58 | 22 of 39 | 3 of 36 | FLAG |
| Soul Rope, round 031 (`3a3b409:…c600000009.lua`) | `official/c37383714.lua` | 0.71 | 27 of 41 | 8 of 38 | FLAG |
| Metalzoa (head, original) | `official/c50705071.lua` | 0.27 | 11 of 47 | 0 of 44 | pass |
| Super Vehicroid - Stealth Union (head, original) | `official/c3897065.lua` | 0.31 | 25 of 87 | 1 of 84 | pass |
| Malefic Blue-Eyes White Dragon (head, original) | `official/c9433350.lua` | 0.13 | 6 of 68 | 0 of 65 | pass |

(The five derived scripts at head are, by construction, nearly identical to upstream; the gate measures only `original` ones.) **Threshold 0.40**: the gap in the calibration is 0.31 (highest accepted) to 0.51 (lowest flagged). 0.40 is just below the midpoint, deliberately nearer the accepted side: a false flag costs a relabel to `derived`, a false pass costs mislicensed code. The 4-line-window count does not separate the cases (Strike Ninja 1, Stealth Union 1), so it does not decide.

The gate is `tests/engine/test_script_origin.py::test_every_original_script_measurably_differs_from_ignis_script_for_its_alias`; a missing upstream file fails rather than passes. **Red run**: I restored round 031's five scripts and records (`git show 3a3b409:data/custom-cards/c60000000{4,5,6,7,9}.{lua,json}`, all labelled original) and ran the module with the engine environment; afterwards restored the files (`cmp` clean):

```
FAIL: test_every_original_script_measurably_differs_from_ignis_script_for_its_alias (tests.engine.test_script_origin.ScriptOriginTest.test_every_original_script_measurably_differs_from_ignis_script_for_its_alias) (passcode=600000004, name='Goddess of Whim (Retro Formats)')
AssertionError: True is not false : data/custom-cards/c600000004.lua is labelled original but its line-sequence ratio against official/c67959180.lua is 0.72 (limit 0.4; 23 of 32 code lines identical, 4 shared 4-line windows). Label it derived, credited and AGPL-3.0-or-later, or rewrite it.
FAIL: test_every_original_script_measurably_differs_from_ignis_script_for_its_alias (tests.engine.test_script_origin.ScriptOriginTest.test_every_original_script_measurably_differs_from_ignis_script_for_its_alias) (passcode=600000005, name='Strike Ninja (Retro Formats)')
AssertionError: True is not false : data/custom-cards/c600000005.lua is labelled original but its line-sequence ratio against official/c41006930.lua is 0.51 (limit 0.4; 21 of 39 code lines identical, 1 shared 4-line windows). Label it derived, credited and AGPL-3.0-or-later, or rewrite it.
FAIL: test_every_original_script_measurably_differs_from_ignis_script_for_its_alias (tests.engine.test_script_origin.ScriptOriginTest.test_every_original_script_measurably_differs_from_ignis_script_for_its_alias) (passcode=600000006, name='Green Baboon, Defender of the Forest (Retro Formats)')
AssertionError: True is not false : data/custom-cards/c600000006.lua is labelled original but its line-sequence ratio against official/c46668237.lua is 0.61 (limit 0.4; 21 of 38 code lines identical, 2 shared 4-line windows). Label it derived, credited and AGPL-3.0-or-later, or rewrite it.
FAIL: test_every_original_script_measurably_differs_from_ignis_script_for_its_alias (tests.engine.test_script_origin.ScriptOriginTest.test_every_original_script_measurably_differs_from_ignis_script_for_its_alias) (passcode=600000007, name='Rise of the Snake Deity (Retro Formats)')
AssertionError: True is not false : data/custom-cards/c600000007.lua is labelled original but its line-sequence ratio against official/c16067089.lua is 0.58 (limit 0.4; 22 of 39 code lines identical, 3 shared 4-line windows). Label it derived, credited and AGPL-3.0-or-later, or rewrite it.
FAIL: test_every_original_script_measurably_differs_from_ignis_script_for_its_alias (tests.engine.test_script_origin.ScriptOriginTest.test_every_original_script_measurably_differs_from_ignis_script_for_its_alias) (passcode=600000009, name='Soul Rope (Retro Formats)')
AssertionError: True is not false : data/custom-cards/c600000009.lua is labelled original but its line-sequence ratio against official/c37383714.lua is 0.71 (limit 0.4; 27 of 41 code lines identical, 8 shared 4-line windows). Label it derived, credited and AGPL-3.0-or-later, or rewrite it.
Ran 3 tests in 0.066s
FAILED (failures=5)
```

Night Assailant is not a record any more, so the test cannot load it; its 0.69 in the table is the same `measure()`/`too_close()` the test calls.

### Validator (item 4) — failing without the rule

`custom-card.authorship-not-original` is gone; `_check_authorship` in `retroformats/validate.py` emits `custom-card.bad-authorship` (record) and `custom-card.authorship-header-mismatch` (script header). With the call replaced by `pass` (then restored from a copy), `python -m unittest tests.test_custom_cards`:

```
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='upstream')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='upstream__path')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='upstream__revision')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='upstream__source')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='upstream__copyright')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='licence')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='modified')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='modified__date')
FAIL: test_a_derived_script_needs_upstream_path_revision_licence_and_notices (missing='modified__summary')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='upstream__revision', value='0000000000000000000000000000000000000000')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='upstream__source', value='test-source')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='upstream__path', value='../official/c200.lua')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='upstream__path', value='official/c200.txt')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='licence', value='MIT')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='modified__date', value='27 September 2026')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='modified__summary', value=' ')
FAIL: test_a_derived_scripts_fields_must_be_the_real_ones (field='upstream__copyright', value='')
FAIL: test_a_derived_scripts_header_must_match_the_record (dropped='--SPDX-License-Identifier: AGPL-3.0-or-later')
FAIL: test_a_derived_scripts_header_must_match_the_record (dropped='--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c200.lua')
FAIL: test_a_derived_scripts_header_must_match_the_record (dropped='--Copyright (C) 2020  Project Ignis contributors.')
FAIL: test_a_derived_scripts_header_must_match_the_record (dropped='--Modified by edopro-retro-formats on 2026-09-27: removed the use limit.')
FAIL: test_a_derived_scripts_header_must_match_the_record (changed='revision in the header')
FAIL: test_a_derived_scripts_header_must_match_the_record (changed='the header states a line only after the code starts')
FAIL: test_an_original_script_is_mit (licence=None)
FAIL: test_an_original_script_is_mit (licence='AGPL-3.0-or-later')
FAIL: test_an_original_script_is_mit (licence='GPL-2.0')
FAIL: test_an_original_script_names_no_upstream
FAIL: test_an_original_scripts_header_must_not_name_an_upstream
FAIL: test_an_original_scripts_header_must_state_its_licence (lua='--script\n')
FAIL: test_an_original_scripts_header_must_state_its_licence (lua='--SPDX-License-Identifier: AGPL-3.0-or-later\n')
FAIL: test_an_original_scripts_header_must_state_its_licence (lua='local s,id=GetID()\n')
FAIL: test_authorship_kind_is_original_or_derived
FAIL: test_missing_authorship_fails
Ran 50 tests in 1.001s
FAILED (failures=33)
```

With the rule: `Ran 50 tests … OK`. For `original` it is stricter than before (kind still must be `original`, plus `licence: MIT`, no `upstream`/`modified`, first line `--SPDX-License-Identifier: MIT`, no `--Upstream:` line). For `derived` it requires `upstream.source` ∈ `CUSTOM_CARD_DERIVABLE_SOURCES` (only `ignis-cardscripts`), `upstream.revision` = that source's pin in `data/sources.json`, a relative `.lua` path, a copyright notice, `licence` = the upstream's (`AGPL-3.0-or-later`), `modified.date` (YYYY-MM-DD) and `modified.summary`; and the leading comment block must start with the SPDX line and contain, verbatim, `--Upstream: <source url>/blob/<revision>/<path>`, `--<copyright>` and `--Modified by edopro-retro-formats on <date>: <summary>`.

### Malefic Blue-Eyes (item 6): inconclusive; record unchanged

Read through Yugipedia's API (`action=parse&prop=wikitext`), 2026-09-27:

- `https://yugipedia.com/wiki/Card_Errata:Malefic_Blue-Eyes_White_Dragon`: English table, printing 1 caption "DPKB-EN023 / Duelist Pack: Kaiba / (Unlimited Edition) / Silver Dragon Value Box", text using "Must first be Special Summoned (from your hand) by banishing". The caption pairs the Unlimited Edition with the Value Box; it gives no separate date.
- `https://yugipedia.com/wiki/Duelist_Pack:_Kaiba`: "na_release_date = April 20, 2010"; "The English set was reprinted with Problem-Solving Card Text on the cards in the Silver Dragon Value Box, Duelist Pack: Yugi & Kaiba Special Edition, Yugi's Collector Box, Kaiba's Collector Box, and Yugi & Kaiba Collector Box." Its gallery lists English "1st Edition" and a separate English "Unlimited Edition" gallery.
- Release dates of those reprints, from their pages: Silver Dragon Value Box NA 2013-09-13 ("This bundle reprinted Duelist Pack: Kaiba with Problem-Solving Card Text", contents "4 Duelist Pack: Kaiba booster packs (Unlimited Edition)"); Duelist Pack: Yugi & Kaiba Special Edition NA 2013-10-25; Yugi's Collector Box NA 2017-09-15; Kaiba's Collector Box NA 2017-11-17; Yugi & Kaiba Collector Box EU 2018-03-29.
- `https://yugipedia.com/wiki/Banish`: "known as remove from play prior to Problem-Solving Card Text", citing Konami's "Problem-Solving Card Text, Part 2" of May 23, 2011.

Finding: every English reprint I found that carries the corrected text is dated 2013-09-13 or later, and the Value Box contained Unlimited Edition DPKB packs. I found **no evidence** of an English Unlimited printing with the corrected wording before 2011-09-17. That is not proof that none exists: the corrected text's PSCT vocabulary was announced 2011-05-23, which does not by itself exclude a printing between then and 2011-09-17, and I did not find a dated source for the English Unlimited Edition as such. Inconclusive, so per the brief the record is unchanged. The Verifier's reading stands: the Value Box is the earliest dated English source for the corrected text.

## Not verified

- Whether a derived script distributed under AGPL-3.0-or-later inside an otherwise-MIT repository meets every AGPL obligation (for example section 13 for network use). I followed the brief: SPDX, upstream path and revision, Ignis's README copyright notice, a dated modification notice, and the licence text in the repository and in `dist/scripts/`. I am not a lawyer.
- Behaviour of the derived scripts beyond the engine tests. Rebasing on upstream changed some untested behaviour relative to round 031's scripts; each is now stated in `not_reproduced` (see Changed). Most notable: Green Baboon no longer has `EFFECT_FLAG_DELAY`, so it can miss the timing (Open question 1).
- A real EDOPro client loading `dist/scripts/` with the extra `LICENSES.md`/`LICENSE-*.txt` files in it. EDOPro looks scripts up by `c<code>.lua` filename, so I expect other files to be ignored, but I did not check that in a client.
- The Yugipedia pages are live pages, not pinned revisions; I did not look for sources outside Yugipedia for item 6.
- Python 3.10 locally (CI's `check (3.10)` passed at the head). Windows.
- The round-031 `scratch/031-red-*` branches: still on origin, not touched.

## Changed

- `data/custom-cards/c600000004/5/6/7/9.lua`: rebased on Ignis's `official/` script at `383bfbd6` with only the period edit (diffs above) and an AGPL header. `.json`: `authorship` → `kind: derived`, `licence: AGPL-3.0-or-later`, `upstream {source, path, revision, copyright}`, `modified {date: 2026-09-27, summary}`, new `note`. **Old notes (all five) were** "Written from the record's period text and the ocgcore Lua API, not derived from any Project Ignis CardScripts file, whose licence is AGPL-3.0-or-later (ProjectIgnis/CardScripts COPYING at the ignis-cardscripts pin). Round 031: no Project Ignis card script was opened while writing it; constant.lua and utility.lua (the engine's shared API) were read, and the modern card's behaviour was only observed by running it in the engine harness." followed by, for Goddess and Strike Ninja, "A derived script would need an owner licensing decision."; for Green Baboon "The erratum record's summary says which event and flags an upstream script uses; the same behaviour is written here with ordinary engine API. A derived script would need an owner licensing decision."; for Rise the same with "notes describe which event and flag"; for Soul Rope "notes describe which event, flag and filter". **New note (all five, with each file's path)**: "Adapted from Project Ignis's script for the modern card, official/c<alias>.lua at the ignis-cardscripts pin, by applying only the period difference the erratum record states (the summary above) and pointing the effect description at the modern card's strings, because this generated row carries none. It is licensed AGPL-3.0-or-later like its upstream (LICENSES/AGPL-3.0-or-later.txt); the rest of this repository stays MIT. Round 031 labelled it original, written without opening any Project Ignis card script; round 031's review measured that version as too close to this upstream file to be independent, and the owner decided on 2026-09-27 that such scripts are credited, labelled derived and kept under the upstream's licence. Round 032 rebased it on the upstream file itself." The old note is corrected because it is shown to be wrong (the brief allows this); the history is kept in the new one.
- `not_reproduced` corrected where it described round 031's script rather than upstream's (old → new):
  - Goddess [1] "Halving rounds the result up. That is a convention of the game…" → "Halving is the upstream script's c:GetAttack()/2; how the engine rounds half of an odd ATK is not something the record's sources state…".
  - Strike Ninja [1]: kept its first sentence, added "The cost filter is the upstream script's: face-up DARK monsters in the Graveyard, or on the field only while an effect such as Spirit Elimination applies (aux.SpElimFilter), never this card itself."
  - Green Baboon [1] "The race of a Beast destroyed face-down is read from the engine's record of the monster's race on the field…" → "As in the upstream script, the destroyed monster must be a Beast both in the Graveyard and by the engine's record of its race on the field…"; [2] "The script does not count it, so this card must already be in the hand or Graveyard when another Beast is destroyed." → "As in the upstream script, it is not offered when this card is itself among the cards sent to the Graveyard in that event, even if another Beast was destroyed with it."; new [3] on the missing `EFFECT_FLAG_DELAY` (can miss the timing; round 031 used the delayed form; not established, not tested).
  - Rise [2]: added that the Summon then counts as a proper Summon of Vennominaga (`CompleteProcedure`), as upstream, and that later revival is not tested.
  - Soul Rope: unchanged (still accurate).
- `data/custom-cards/c600000001/2/8.lua`: first line `--SPDX-License-Identifier: MIT` added, nothing else. `.json`: `licence: MIT` added; note's last clause changed. Old (Metalzoa, Stealth Union) "…Round 029 investigation; a derived script would need an owner licensing decision." → "…Round 029 investigation. Round 032 measured it against Project Ignis's script for its alias at the ignis-cardscripts pin: line-sequence ratio 0.27 [0.31], under the 0.40 limit tests/engine/test_script_origin.py enforces for an original script (retroformats/script_similarity.py)." Malefic: its final sentence "A derived script would need an owner licensing decision." → the same measurement sentence with 0.13; the round-031 sentences before it are kept.
- `retroformats/model.py`: `CUSTOM_CARD_ORIGINAL_LICENCE`, `CUSTOM_CARD_DERIVABLE_SOURCES`. `retroformats/validate.py`: `_check_authorship` replaces the `authorship-not-original` check. `schemas/custom-card.schema.json`: the `authorship` object documented (documentation only).
- `retroformats/custom_cards.py`: generates `dist/scripts/LICENSES.md` (every script's licence and origin, from the records) and copies the licence texts for the licences in use to `dist/scripts/LICENSE-MIT.txt` (root `LICENSE`) and `dist/scripts/LICENSE-AGPL-3.0-or-later.txt`; they are generated outputs, so the stale-file guard covers them.
- `LICENSES/AGPL-3.0-or-later.txt`: byte copy of CardScripts `COPYING` at the pin (SHA-256 `8486a10c…07ef` both; also checked by an engine test). Root `LICENSE` unchanged (still MIT, so GitHub's licence detection is unaffected).
- `retroformats/script_similarity.py` (new): the measure and `ORIGINAL_MAX_RATIO = 0.40` with its calibration. `tests/engine/test_script_origin.py` (new, 3 tests): the gate; each derived upstream file exists in the pinned checkout; the AGPL text equals Ignis's `COPYING`.
- `tests/test_custom_cards.py`: the two old authorship tests replaced by ten covering both kinds and the header; the live test now pins which cards are original/derived and each first line; new test that the licence files and notice in `dist/scripts/` match. No other test changed.
- `.github/workflows/ci.yml` and `docs/engine-testing.md`: floor 56 → 59; a "Script origin" section.
- `dist/scripts/*`: regenerated. `dist/README.md`, `README.md` (Licence section), `docs/errata.md` ("Generated historical cards"), `docs/roadmap.md` item 7: which scripts are derived/AGPL and which original/MIT, and where the licence texts are. `docs/state.md` not changed.

## Open questions

1. **Green Baboon's missing-the-timing.** Round 031's script used `EFFECT_FLAG_DELAY`; Ignis's has none, and the brief said to apply only the period edits, so the derived script can now miss the timing ("When … you can"). Whether the 2010 card could miss the timing is not established by the record; it is disclosed in `not_reproduced` and untested. If Brain wants round 031's behaviour back, that is one more documented edit.
2. **Untested behaviour now follows upstream rather than round 031** (Strike Ninja's Spirit Elimination support and self-exclusion, Green Baboon refusing when it is itself among the destroyed cards, Vennominaga counted as properly Summoned, Goddess's halving). All are disclosed per card; none is a historical claim.
3. **`derived` revision must equal the current pin.** If `ignis-cardscripts` is re-pinned, every derived record fails validation until it is re-checked against the new revision. I chose that on purpose (the header claims the pinned revision, and the gate compares at the pin), but it makes a pin bump a deliberate multi-file change.
4. **BabelCDB's licence**, one line as the brief asks: I did not examine it; the `.cdb` rows copy only numeric stats plus our own name and text.
5. Night Assailant: a derived script is now allowed, so the only thing still holding it back is the period evidence (updated in the roadmap wording). No change to it this round.
