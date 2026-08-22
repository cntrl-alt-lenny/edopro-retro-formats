# Edison card-behaviour triage (roadmap item 6)

**Purpose:** turn the two headline errata-warning counts for the Edison format
into an exact, per-card remediation map, so future research/implementation
work can be pointed at the highest-leverage shared cause instead of at
individual cards one at a time. This is an audit only - no card behaviour,
selection logic, or historical implementation changes in this milestone.

**Method:** every figure below is recomputed directly from the project's own
selection model (`retroformats.model.Erratum.selection_at`), not from memory
or from an earlier summary of this project. The exact extraction script's
logic is described in "Reproduced state" below; its output was independently
cross-checked against `python -m retroformats report -v`'s own live counts
and matches exactly. Per-card root-cause classification and the qualitative
fields (behavioural difference, chronology/implementation blocker,
recommended action) were produced by an LLM workflow given ONLY the precise
structured facts already in this project's own `data/errata/*.json` records -
no new web research was performed for this milestone, and no field below
states anything the underlying erratum record doesn't already support.

## Reproduced state

Recomputed from HEAD via `python -m retroformats report -v` and a direct
query against `Erratum.selection_at()` for the Edison snapshot
(2010-04-24), cross-checked against `python -m retroformats validate`'s
warning counts:

| Category | Validator warning code | Count |
|---|---|---|
| Known-wrong modern fallback | `format.erratum-modern-known-wrong` | **44** |
| Acknowledged implementation gap | `format.erratum-known-divergence` | **41** |
| Overlap between the two | — | **0** (mutually exclusive by construction - see below) |
| **Unique affected cards (union)** | | **85** |

**A note on the "48" figure carried into this milestone's brief:** it is real,
but it is not the Edison-applicable acknowledged-gap count. `python -m
retroformats report -v`'s own summary line reports "48 unresolved" as a
**global, project-wide** count of `implementation.strategy == "unresolved"`
erratum records (`errata: 296 records ... strategies: 14 none-needed, 234
reuse-upstream, 48 unresolved`) - i.e. every card anywhere in the corpus whose
implementation strategy hasn't been decided, regardless of whether that
card's chronology even resolves to the unresolved version at the Edison
snapshot specifically. Filtering to just the 48 that are also selected as
applicable at Edison's exact snapshot date removes 7: one (Amazoness Fighter)
resolves to the **modern** version at Edison, so the missing historical
implementation is irrelevant there; six (Anteatereatingant, Armored Glass,
Dimension Distortion, Fushioh Richie, Metalsilver Armor, Spirit's Invitation)
have **ambiguous** chronology at Edison where the modern card itself remains
a possible candidate, so they are not confidently "known-wrong" or a
confirmed gap either - they surface instead as the weaker
`format.erratum-unresolved-defaulted` warning (part of a separate, larger,
genuinely-uncertain population of 106 records not addressed by this
milestone; see "Out of scope" below). 48 − 7 = 41, exactly matching the live
`format.erratum-known-divergence` count. The task brief's "92-row list"
estimate (44 + 48) is likewise corrected to **85** once the true, Edison-
specific figures are used.

**Overlap:** structurally zero. The two validator warnings come from mutually
exclusive branches of the same selection check
(`retroformats/validate.py:769-876`): `format.erratum-known-divergence` fires
only when chronology is fully **determinate** at the snapshot (state
`"gap"`); `format.erratum-modern-known-wrong` fires only when chronology is
**ambiguous** at the snapshot (state `"ambiguous"`) but the modern version can
be ruled out anyway. A record cannot be in both states at once. Verified
empirically as well as structurally: the id sets have zero intersection.

**Out of scope for this milestone** (context, not part of the 85): 72 records
already have working historical substitutions in force at Edison (no
problem); 12 resolve cleanly to the modern card (no problem); 106 more are
`format.erratum-unresolved-defaulted` - ambiguous chronology where modern
remains a *possible* candidate, so nothing is yet *proven* wrong. That 106-
record population is a distinct, larger research problem (whether modern is
actually correct for each one is simply unknown) and is not analysed further
here. GOAT format comparison, verified rather than assumed: GOAT's
`format.json` sets `errata_overrides.reference_parity` (not
`unresolved_policy`) - its REAL card substitutions come from matching Project
Ignis's own reference GOAT list, not from the chronology-driven
ambiguous/gap selection this document analyses for Edison; disagreements
with that reference are reported separately, via
`format.parity-omits-historical` (21) / `format.parity-substitutes-non-behavioural`
(11), not via the two codes this document covers. `report -v`'s own
"known-wrong"/"divergence" figures per format are computed by the SAME raw
chronology-selection logic for both formats regardless of reference_parity,
so GOAT's numbers there can be read as "what Edison-style selection would
say" rather than GOAT's real behaviour: under that computation, GOAT's
acknowledged-gap set is **the identical 41 cards** (same erratum IDs - these
implementation gaps are era-independent, not a coincidence), while GOAT's
known-wrong count is always zero not because its chronology differs, but
because GOAT's `format.json` sets no `unresolved_policy.choice` at all - the
`policy == "modern"` condition the known-wrong check requires can never be
satisfied for GOAT, independent of what the chronology says. Edison's pool
is 3,673 cards; the 85 affected cards are about 2.3% of it.

## A/B/C/D partition

Per the task's framework:

| Partition | Definition | Count |
|---|---|---|
| **A. Chronology-only** | a working historical implementation already exists for at least one chronology-plausible version; only the date/source is missing | **44** (100% of known-wrong) |
| **B. Implementation-only** | chronology is fully resolved; the correct historical version has no usable implementation | **41** (100% of acknowledged-gap) |
| **C. Both unresolved** | chronology ambiguous AND no candidate version has an implementation | **0** |
| **D. Other / identity / engine issue** | blocker is not an ordinary card-script chronology/implementation gap | **0** |

This partition falls out cleanly along the two validator categories -
`format.erratum-modern-known-wrong` is *always* A (by definition: it can only
fire when chronology is ambiguous, which is the A/C-vs-B split's other axis;
the actual C/A distinction was checked per-record by testing whether
`Erratum.implementation_for_version(v)` returns a usable implementation - one
that isn't `strategy: "unresolved"` and, unless `strategy: "none-needed"`,
carries a `historical_passcode` - for at least one candidate `v`; every one of
the 44 passed) and `format.erratum-known-divergence` is *always* B (by the
model's own definition, state `"gap"` only exists when chronology is fully
determinate). No card required a D classification after review - none of the
85 turned out to be a card-identity, region-scoping, banlist, or engine-flag
problem masquerading as an errata gap.

## Root-cause clusters

Grouped by shared behavioural pattern, largest first. Every cluster below
accounts for all 85 cards exactly once (verified: 38+12+9+8+4+4+4+3+2+1 = 85).
"Leverage" states plainly what happens to the cluster's card count if the
ONE shared question that blocks it were resolved.


### 1. Failed-search / deck-verification behaviour — 38 cards, all partition A

**By far the largest cluster, and the highest-leverage item in the entire
inventory.** All 38 cards share the *identical* two-change structure in their
erratum records:

1. An **entirely undated** "era activation semantics" change: the
   goat/historical script variant lets the effect be activated even when no
   legitimate target/match exists (in Deck, hand, or GY, depending on the
   card) — modern requires a valid match to exist before allowing activation
   at all.
2. A change dated by the **same bracket on every single one of these 38
   cards** — `old_attested_through: 2011-02-02`, `new_attested_from:
   2019-04-03` — describing the accompanying procedure: on a proven failed
   search, the goat/historical script reveals and shuffles the relevant
   zone(s) (`Duel.GoatConfirm`) to prove the whiff to the opponent; the
   modern script does neither (it simply can't activate, so there's nothing
   to prove).

At the Edison snapshot (2010-04-24), change 2 already resolves determinately
(2010-04-24 predates 2011-02-02, so the *old* deck-verification procedure was
still in force) — it is change 1's total absence of any date that is the
actual source of the ambiguity: with change 2 pinned old, "modern" (which
needs *both* changes to have happened) is already provably wrong, but
whether change 1 had *also* already happened by April 2010 (making the
candidate version 1) or not (version 0) is genuinely unknown. This is the
existing project roadmap's own long-standing "close the search-verification
interval" item (roadmap 1b), now precisely reduced to a list of 38 named
cards it would resolve.

Every one of the 38 already has a working `reuse-upstream` implementation for
at least one candidate version (listed in the table below) — this cluster
needs **zero** new Lua/CDB work. **Leverage: one dated period source
(ideally a Konami ruling, judge-program communication, or tournament-policy
note from 2010-2018 narrowing when TCG rulings began requiring a legitimate
target to exist before these "search and reveal-on-failure" effects could be
activated) could resolve the chronology for all 38 at once**, if the source
speaks to the general rule rather than one specific card - several of the
per-card recommended actions below note this explicitly. A source specific
to only some of the 38 would still resolve those individually.


| Card | Passcode | Erratum ID | Missing valid-target check on | Existing implementation (all partition A) | Recommended action |
|---|---|---|---|---|---|
| A Deal with Dark Ruler | 6850209 | `erratum-a-deal-with-dark-ruler` | Berserk Dragon | `504700010` | locate a dated period ruling (2010-2019) on when A Deal with Dark Ruler's activation began requiring a valid… |
| Apprentice Magician | 9156135 | `erratum-apprentice-magician` | (see erratum record) | `504700013` | locate a dated period ruling on when Apprentice Magician's revival effect required a Level 2 or lower… |
| Armed Dragon LV3 | 980973 | `erratum-armed-dragon-lv3` | Armed Dragon LV5 | `504700003` | locate a dated period ruling on when Armed Dragon LV3's Standby Phase activation began requiring a valid… |
| Armed Dragon LV5 | 46384672 | `erratum-armed-dragon-lv5` | Armed Dragon LV7 | `504700075` | locate a dated period ruling on when Armed Dragon LV5's End Phase activation began requiring a valid 'Armed… |
| Birdface | 45547649 | `erratum-birdface` | Harpie Lady | `504700073` | locate a dated period ruling on when Birdface's battle-destruction trigger began requiring a valid 'Harpie… |
| Bubonic Vermin | 6104968 | `erratum-bubonic-vermin` | Bubonic Vermin | `504700008` | locate a dated period ruling on when Bubonic Vermin's FLIP effect began requiring a second copy to exist in… |
| Dark Mimic LV1 | 74713516 | `erratum-dark-mimic-lv1` | Dark Mimic LV3 | `504700129` | locate a dated period ruling or rulebook fixing when the no-eligible-target activation allowance for Dark… |
| Dark Scorpion - Meanae the Thorn | 74153887 | `erratum-dark-scorpion-meanae-the-thorn` | Dark Scorpion | `504700125` | locate a dated period ruling fixing when the no-eligible-'Dark Scorpion'-card activation allowance for… |
| Dedication through Light and Darkness | 69542930 | `erratum-dedication-through-light-and-darkness` | Dark Magician of Chaos | `504700113` | locate a dated period ruling fixing when the no-eligible-'Dark Magician of Chaos' activation allowance for… |
| Elegant Egotist | 90219263 | `erratum-elegant-egotist` | Harpie Lady | `504700157` | locate a dated period ruling fixing when the no-eligible-Harpie activation allowance for Elegant Egotist ended |
| Emblem of Dragon Destroyer | 6390406 | `erratum-emblem-of-dragon-destroyer` | Buster Blader | `504700009` | locate a dated period ruling fixing when the no-eligible-'Buster Blader' activation allowance for Emblem of… |
| Freed the Matchless General | 49681811 | `erratum-freed-the-matchless-general` | (see erratum record) | `504700082` | locate a dated period ruling fixing when the no-eligible-Warrior activation allowance for Freed the… |
| Fusion Sage | 26902560 | `erratum-fusion-sage` | Polymerization | `504700047` | locate a dated period ruling fixing when the no-eligible-'Polymerization' activation allowance for Fusion… |
| Giant Rat | 97017120 | `erratum-giant-rat` | (see erratum record) | `504700172` | locate a dated period ruling on when Giant Rat lost its no-target-required activation allowance for the… |
| Great Dezard | 88989706 | `erratum-great-dezard` | Fushioh Richie | `504700154` | locate a dated period ruling on when Great Dezard lost its no-target-required activation allowance for its… |
| Hand of Nephthys | 98446407 | `erratum-hand-of-nephthys` | Sacred Phoenix of Nephthys | `504700175` | locate a dated period ruling on when Hand of Nephthys lost its no-target-required activation allowance for… |
| Hero Signal | 22020907 | `erratum-hero-signal` | Elemental HERO | `504700031` | locate a dated period ruling on when Hero Signal lost its no-target-required activation allowance for its… |
| Horus the Black Flame Dragon LV4 | 75830094 | `erratum-horus-the-black-flame-dragon-lv4` | Horus the Black Flame Dragon LV6 | `504700132` | locate a dated period ruling on when Horus the Black Flame Dragon LV4 lost its no-target-required activation… |
| Manju of the Ten Thousand Hands | 95492061 | `erratum-manju-of-the-ten-thousand-hands` | (see erratum record) | `504700169` | locate a dated period ruling on when Manju of the Ten Thousand Hands lost its no-target-required activation… |
| Masked Dragon | 39191307 | `erratum-masked-dragon` | (see erratum record) | `504700064` | locate a dated period ruling on when Masked Dragon lost its no-target-required activation allowance for its… |
| Mother Grizzly | 57839750 | `erratum-mother-grizzly` | (see erratum record) | `504700093` | locate a dated period ruling or policy update narrowing the 2011-02-02..2019-04-03 window for when Mother… |
| Mystic Swordsman LV2 | 47507260 | `erratum-mystic-swordsman-lv2` | (see erratum record) | `504700077` | locate a dated period ruling or policy update narrowing the 2011-02-02..2019-04-03 window for when Mystic… |
| Mystic Swordsman LV4 | 74591968 | `erratum-mystic-swordsman-lv4` | (see erratum record) | `504700128` | locate a dated period ruling or policy update narrowing the 2011-02-02..2019-04-03 window for when Mystic… |
| Mystic Tomato | 83011277 | `erratum-mystic-tomato` | (see erratum record) | `504700142` | locate a dated period ruling or policy update narrowing the 2011-02-02..2019-04-03 window for when Mystic… |
| Ninjitsu Art of Transformation | 70861343 | `erratum-ninjitsu-art-of-transformation` | (see erratum record) | `504700115` | locate a dated period ruling or policy update narrowing the 2011-02-02..2019-04-03 window for when Ninjitsu… |
| Paladin of White Dragon | 73398797 | `erratum-paladin-of-white-dragon` | (see erratum record) | `504700119` | locate a dated period ruling or policy update narrowing the 2011-02-02..2019-04-03 window for when Paladin… |
| Pandemonium | 94585852 | `erratum-pandemonium` | (see erratum record) | `504700165` | locate a dated period ruling or policy update narrowing the 2011-02-02..2019-04-03 window for when… |
| Peten the Dark Clown | 52624755 | `erratum-peten-the-dark-clown` | (see erratum record) | `504700084` | locate a dated period ruling or tournament-policy note pinning when Deck/Hand verification for Peten's… |
| Pyramid Turtle | 77044671 | `erratum-pyramid-turtle` | (see erratum record) | `504700135` | locate a dated period ruling pinning when Deck verification for Pyramid Turtle's Special Summon trigger… |
| Skull Knight #2 | 15653824 | `erratum-skull-knight-2` | Skull Knight #2 | `504700022` | locate a dated period ruling pinning when Deck verification for Skull Knight #2's search ended (between… |
| Sonic Bird | 57617178 | `erratum-sonic-bird` | (see erratum record) | `504700092` | locate a dated period ruling pinning when Sonic Bird's fail-to-find allowance and Deck-verification… |
| Terraforming | 73628505 | `erratum-terraforming` | (see erratum record) | `504700121` | locate a dated period ruling pinning when Terraforming's fail-to-find allowance and Deck-verification… |
| Thunder Dragon | 31786629 | `erratum-thunder-dragon` | Thunder Dragon | `504700054` | locate a dated period ruling pinning when Thunder Dragon's zero-copy/no-target discard allowance and its… |
| Toon Table of Contents | 89997728 | `erratum-toon-table-of-contents` | Toon | `504700156` | locate a dated period ruling pinning when Toon Table of Contents' fail-to-find allowance and… |
| UFO Turtle | 60806437 | `erratum-ufo-turtle` | (see erratum record) | `504700098` | locate a dated period ruling establishing when UFO Turtle's trigger began requiring a valid… |
| Ultimate Insect LV1 | 49441499 | `erratum-ultimate-insect-lv1` | Ultimate Insect LV3 | `504700081` | locate a dated period ruling establishing when Ultimate Insect LV1's cost began requiring a… |
| Ultimate Insect LV3 | 34088136 | `erratum-ultimate-insect-lv3` | Ultimate Insect LV5 | `504700057` | locate a dated period ruling establishing when Ultimate Insect LV3's cost began requiring a… |
| Ultimate Insect LV5 | 34830502 | `erratum-ultimate-insect-lv5` | Ultimate Insect LV7 | `504700058` | locate a dated period ruling establishing when Ultimate Insect LV5's cost began requiring a… |


### 2. Other shared ruling-era changes — 12 cards, all partition B

Chronology is already resolved for all 12; each needs a **custom Lua script
that does not yet exist upstream**. Not one undifferentiated bucket — two
sub-patterns recur within it, independently identified by the diagnostic
pass from each card's own erratum text:

- **Nomi-to-semi-nomi wording revision** (~7 of 12: Elemental HERO Chaos
  Neos, Garuda the Wind Spirit, Gigantes, Gladiator Beast Heraklinos,
  Malefic Blue-Eyes White Dragon, Metalzoa, VW-Tiger Catapult): a TCG-wide
  errata wave converted strict "can only be Special Summoned by X" wording to
  "Must first be Special Summoned... by X," loosening a permanent lock into a
  one-time-procedure lock. Edison predates this wave; the Edison-era text is
  the strict version.
- **Union Condition removal** (2 of 12: Machina Gearframe, Machina
  Peacekeeper): the "a monster can only be equipped with 1 Union monster at a
  time" clause, printed on every period Union monster, was later dropped from
  reprints.
- Genuinely distinct: Dark Necrofear, Evil HERO Dark Gaia, Necrovalley (3).

**Leverage:** none of these need chronology research (already resolved) —
the leverage here is **implementation reuse**: a shared "strict Nomi lock"
Lua helper pattern could be written once and applied to the ~7
nomi-to-semi-nomi cards, and a shared "Union equip-restriction" helper to the
2 Union cards, cutting per-card script-writing effort even though each still
needs its own passcode, CDB row, and script file.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Dark Necrofear | 31829185 | `erratum-dark-necrofear` | **B** | none | no upstream implementation matches v4's text (the only candidate, the manga-only unofficial passcode 511004006, has a different summon… | write a custom Lua script restoring the strict Nomi lock and an untargeted End Phase equip/control-theft… |
| Elemental HERO Chaos Neos | 17032740 | `erratum-elemental-hero-chaos-neos` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs an EFFECT_SPSUMMON_CONDITION… | write a custom Lua script restoring the strict Fusion-only Nomi lock and an either-Main-Phase coin toss +… |
| Evil HERO Dark Gaia | 58332301 | `erratum-evil-hero-dark-gaia` | **B** | none | no upstream implementation exists at all (this card has no historical or unofficial variant of any kind); the historical script needs to… | write a custom Lua script that captures field ATK at the moment of Fusion Summon and makes the… |
| Garuda the Wind Spirit | 12800777 | `erratum-garuda-the-wind-spirit` | **B** | none | no upstream implementation exists at all (this card has no historical or unofficial variant of any kind); the historical script needs an… | write a custom Lua script restoring the strict Nomi lock (no revival after proper summon) + reserve a passcode |
| Gigantes | 47606319 | `erratum-gigantes` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must impose a permanent nomi… | write a custom Lua script enforcing a permanent (post-Summon-persistent) strict-nomi restriction disallowing… |
| Gladiator Beast Heraklinos | 27346636 | `erratum-gladiator-beast-heraklinos` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must impose a permanent nomi… | write a custom Lua script enforcing a permanent strict-nomi restriction on Special Summons after Heraklinos… |
| Machina Gearframe | 42940404 | `erratum-machina-gearframe` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must add a check refusing to… | write a custom Lua script enforcing the one-Union-monster-per-host equip restriction and forcing face-up… |
| Machina Peacekeeper | 78349103 | `erratum-machina-peacekeeper` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must add a check refusing to… | write a custom Lua script enforcing the one-Union-monster-per-host equip restriction and forcing face-up… |
| Malefic Blue-Eyes White Dragon | 9433350 | `erratum-malefic-blue-eyes-white-dragon` | **B** | none | No usable implementation exists: the only upstream match, passcode 513000068, is a different anime-only card with a different cost (sends… | write a custom Lua script enforcing the strict Deck-banish nomi (no later generic revival) and the… |
| Metalzoa | 50705071 | `erratum-metalzoa` | **B** | none | No upstream implementation exists for 50705071. A custom script must enforce the strict Deck-only nomi (Special Summon only via the… | write a custom Lua script enforcing the strict Deck-only nomi with no post-Summon revival, and reserve a… |
| Necrovalley | 47355498 | `erratum-necrovalley` | **B** | none | The only upstream historical Necrovalley (511002998) implements the later movement-scoped 2012 text with a re:GetHandler() self-move… | write a custom Lua script negating only effects that target a card in either Graveyard (the TU02-EN014 scope… |
| VW-Tiger Catapult | 58859575 | `erratum-vw-tiger-catapult` | **B** | none | Modern/upstream script's Special Summon procedure check must revert from the semi-Nomi 'restricts only the first Special Summon' condition… | write a custom Lua script for VW-Tiger Catapult enforcing a full Nomi restriction (Special Summonable only… |


### 3. Once-per-turn / name-lock changes — 9 cards, all partition B

Chronology already resolved for all 9; each needs a custom script that
removes an OPT (once-per-turn) guard, or a by-name lock, the modern script
carries but the period text/lineage does not. D.D. Scout Plane and D.D.
Survivor share an identical "End Phase return, no OPT guard" pattern; Dark
Master - Zorc, Dice Re-Roll, Goddess of Whim, and Second Coin Toss share an
"unrestricted die/coin redo effect" pattern; Totem Dragon and Treeborn Frog
share a "Standby Phase self-revival, no OPT" pattern; Strike Ninja is a
by-name-vs-per-copy lock distinction. **Leverage:** implementation-pattern
reuse across the sub-groups noted, not a single shared script.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| D.D. Scout Plane | 3773196 | `erratum-d-d-scout-plane` | **B** | none | The modern script gates the End Phase return with a once-per-turn guard that the SDDE/DR2-era text does not carry; a custom script must… | write a custom Lua script removing the once-per-turn guard on the End Phase return trigger + reserve a… |
| D.D. Survivor | 48092532 | `erratum-d-d-survivor` | **B** | none | The modern script gates the End Phase return with a once-per-turn guard that the pre-LCGX SDDE-era text does not carry; a custom script… | write a custom Lua script removing the once-per-turn guard on the End Phase return trigger + reserve a… |
| Dark Master - Zorc | 97642679 | `erratum-dark-master-zorc` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs to grant the die-roll effect with… | write a custom Lua script for the die-roll Ignition Effect with no once-per-turn cap (repeatable within a… |
| Dice Re-Roll | 83241722 | `erratum-dice-re-roll` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs to grant a per-copy (not per-turn)… | write a custom Lua script granting a per-copy, six-sided-die-only re-roll effect with no per-turn gain cap +… |
| Goddess of Whim | 67959180 | `erratum-goddess-of-whim` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must reproduce the unrestricted… | write a custom Lua script removing the once-per-turn limiter on the coin-toss ATK-double/halve Ignition… |
| Second Coin Toss | 36562627 | `erratum-second-coin-toss` | **B** | none | No usable implementation exists (upstream_implementations empty); a custom script must grant a per-copy (not by-name) once-per-turn redo,… | write a custom Lua script granting a per-copy (not by-name) once-per-turn coin-toss redo, reserve a passcode |
| Strike Ninja | 41006930 | `erratum-strike-ninja` | **B** | none | No usable implementation exists: the only upstream code, 153000011 'Strike Ninja (Deck Master)', carries the modern by-name once-per-turn… | write a custom Lua script restoring the per-copy (not by-name) once-per-turn limit on the self-banish… |
| Totem Dragon | 564541 | `erratum-totem-dragon` | **B** | none | Modern/upstream script behaviour must drop the once-per-turn registration on the Standby Phase revival trigger so a negated activation can… | write a custom Lua script for Totem Dragon's Standby Phase self-revival without an OPT limiter, preserving… |
| Treeborn Frog | 12538374 | `erratum-treeborn-frog` | **B** | none | Modern/upstream script's Standby Phase revival trigger must drop its once-per-turn registration so a negated activation can retrigger the… | write a custom Lua script for Treeborn Frog's Standby Phase self-revival without an OPT limiter, preserving… |


### 4. Target legality — 8 cards (7 partition B, 1 partition A)

What a targeted effect may legally target changed — mostly (7 of 8)
targeting-vs-non-targeting or scope-narrowing text errata with chronology
already resolved and no shared sub-pattern beyond the general category (each
needs its own bespoke script). One (XY-Dragon Cannon) is partition A -
chronology-only, sharing the Cannon-fusion contact-material question with
the cost-payment cluster below.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Masked Beast Des Gardius | 48948935 | `erratum-masked-beast-des-gardius` | **B** | none | No upstream implementation exists at all for 48948935. A custom script must make the Mask of Remnants equip a non-targeting, on-resolution… | write a custom Lua script implementing the non-targeting on-resolution equip-to-any-monster effect plus the… |
| Night Assailant | 16226786 | `erratum-night-assailant` | **B** | none | Upstream's only historical variant (cards-unofficial 16226796) already implements a SelectTarget exception excluding e:GetHandler(), which… | write a custom Lua script removing the SelectTarget self-exclusion so Night Assailant can legally target and… |
| Red-Eyes Wyvern | 67300516 | `erratum-red-eyes-wyvern` | **B** | none | No upstream implementation exists for 67300516. A custom script must make the GY revival a non-targeting, on-resolution selection, restore… | write a custom Lua script implementing the non-targeting on-resolution revival with the Red-Eyes B. Chick… |
| Super Vehicroid - Stealth Union | 3897065 | `erratum-super-vehicroid-stealth-union` | **B** | none | No usable implementation exists: the only upstream code, 511002959 'Super Vehicroid - Stealth Union (Anime)', is a distinct card granting… | write a custom Lua script restricting the equip-target filter to 'monster you control, except Machine-Type',… |
| Swap Frog | 9126351 | `erratum-swap-frog` | **B** | none | No usable implementation exists (upstream_implementations empty); a custom script must drop the face-up requirement from the field-mill… | write a custom Lua script dropping the face-up-only mill restriction and restoring the 'Frog the Jam'… |
| Trap of Darkness | 79766336 | `erratum-trap-of-darkness` | **B** | none | Modern/upstream script's Normal-Trap-in-GY target filter must drop the 'except Trap of Darkness' self-exclusion so a second copy of the… | write a custom Lua script for Trap of Darkness with a Normal-Trap-in-GY target filter that does not exclude… |
| Wild Fire | 68815401 | `erratum-wild-fire` | **B** | none | Modern/upstream script's destroy-target filter must narrow from 'all Blaze Accelerator cards you control' back to 'a single face-up Blaze… | write a custom Lua script for Wild Fire that destroys one face-up 'Blaze Accelerator' card as its target and… |
| XY-Dragon Cannon | 2111707 | `erratum-xy-dragon-cannon` | **A** | `504700007` | No source in the packet dates when (or whether) XY-Dragon Cannon's contact-fusion material eligibility was extended from Monster-Zone-only… | locate a dated period ruling on whether XY-Dragon Cannon's contact-fusion material could already include a… |


### 5. Cost/payment behaviour — 4 cards (2 partition A, 2 partition B)

XYZ-Dragon Cannon and XZ-Tank Cannon (partition A) share an unresolved
chronology question with XY-Dragon Cannon in the target-legality cluster
above: when TCG rulings on contact-fusion material eligibility for the
"Cannon" lineage changed - **a second, smaller shared-chronology
opportunity** (3 cards total across the two clusters) alongside the
headline search-verification one. Blaze Accelerator and Tri-Blaze
Accelerator (partition B) share a "Pyro-Type send must be an unconditional
activation cost, not a conditional resolution step" pattern needing a
custom script each.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Blaze Accelerator | 69537999 | `erratum-blaze-accelerator` | **B** | none | The modern script locks a PSCT target at activation and defers the Pyro-Type send into the resolution as a conditional step; a custom… | write a custom Lua script moving the Pyro-Type-to-GY send into an unconditional activation cost rather than… |
| Tri-Blaze Accelerator | 21420702 | `erratum-tri-blaze-accelerator` | **B** | none | Modern/upstream script must move the Pyro-Type monster's send from an activation-cost step to an unconditional resolution step, with the… | write a custom Lua script for Tri-Blaze Accelerator that pays the Pyro-Type send as an activation cost and… |
| XYZ-Dragon Cannon | 91998119 | `erratum-xyz-dragon-cannon` | **A** | `504700161` | An exact date or bounded interval for when the TCG ruling on contact-fusion material eligibility shifted from 'only monsters physically in… | locate a dated period ruling (Konami FAQ or Shonen Jump judge column) on whether Cannon-lineage… |
| XZ-Tank Cannon | 99724761 | `erratum-xz-tank-cannon` | **A** | `504700177` | An exact date or bounded interval for when the TCG ruling on contact-fusion material eligibility shifted from 'only monsters physically in… | locate a dated period ruling (Konami FAQ or Shonen Jump judge column) on whether Cannon-lineage… |


### 6. Activation-condition changes — 4 cards (1 partition A, 3 partition B)

No shared sub-pattern beyond the general category; each is a distinct
activation-legality question (Main-Phase gating, attacker-condition scope, a
Nomi condition, and a second-attack restriction on Tyrant Dragon).


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Blackwing - Sirocco the Dawn | 75498415 | `erratum-blackwing-sirocco-the-dawn` | **B** | none | The modern script gates the Ignition effect to a Main Phase-1-only activation location and applies an End-Phase reset to the granted ATK;… | write a custom Lua script removing the Main Phase 1-only activation gate and the End Phase ATK-gain expiry +… |
| Blast Held by a Tribute | 89041555 | `erratum-blast-held-by-a-tribute` | **B** | none | The modern script's activation check tests only whether the attacking monster was Tribute Summoned; a custom Edison-era script must widen… | write a custom Lua script widening the activation trigger to also accept an attack by a Tribute-Set monster… |
| The Rock Spirit | 76305638 | `erratum-the-rock-spirit` | **B** | none | No usable implementation exists (upstream_implementations empty; Project Ignis ships neither a GOAT nor a pre-errata variant); a custom… | write a custom Lua script enforcing the strict Nomi-only Special Summon condition with no later revival by… |
| Tyrant Dragon | 94568601 | `erratum-tyrant-dragon` | **A** | `504700164` | No dated period ruling establishes when (or whether) the 'first attack must have been against a monster, not direct' restriction on Tyrant… | locate a dated period ruling on whether Tyrant Dragon's second attack already required the first attack to… |


### 7. Genuinely card-specific errata — 4 cards, all partition B

No shared ruling-era pattern identified for any of these four - each is a
one-off text/functional erratum needing its own bespoke script (an archetype
membership addition, a disposal-branch condition change, a Fusion Material
filter, and a Summon-prevention effect scope change).


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| A Hero Emerges | 21597117 | `erratum-a-hero-emerges` | **B** | none | The modern script's 'Otherwise, send to GY' branch fires whenever the revealed monster cannot be Special Summoned; a custom Edison-era… | write a custom Lua script gating the disposal branch on 'not a Monster Card' rather than 'cannot be Special… |
| Elemental HERO Divine Neos | 31111109 | `erratum-elemental-hero-divine-neos` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs a Fusion Material filter and cost… | write a custom Lua script with an explicit Neos-only (excluding Neo Space) material/cost filter + reserve a… |
| Ido the Supreme Magical Force | 35984222 | `erratum-ido-the-supreme-magical-force` | **B** | none | no usable historical implementation exists upstream (the packet's one upstream entry, passcode 511003208 'Ido The Supreme Magical Force… | write a custom Lua script omitting EFFECT_CANNOT_MSET from the Summon-prevention effect and reserve a… |
| Mustering of the Dark Scorpions | 68191243 | `erratum-mustering-of-the-dark-scorpions` | **B** | none | No upstream implementation exists for 68191243. A custom script must restrict Special Summon eligibility to English card-name string… | write a custom Lua script restricting eligible targets to name-match("Dark Scorpion") plus the named Cliff… |


### 8. Trigger registration — 3 cards (1 partition A, 2 partition B)

Distinct from the miss-timing/EFFECT_FLAG_DELAY cluster below: these are
about *which event* a trigger is registered against or *what it checks*
(controller/face-up-state filters, REASON_EFFECT exclusions), not about
whether the trigger exempts itself from missing the timing.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Boss Rush | 66947414 | `erratum-boss-rush` | **B** | none | The modern script's trigger checks controller and face-up-this-turn flags on the destroyed 'B.E.S.' monster, adds a 'no Normal Summon this… | write a custom Lua script broadening the destruction trigger to either player's B.E.S./Big Core in any… |
| Soul Rope | 37383714 | `erratum-soul-rope` | **B** | none | No usable implementation exists: the only upstream code, 511001593 'Soul Rope (Anime)', is a distinct card matching no lineage version and… | write a custom Lua script removing the REASON_EFFECT cfilter check and adding EFFECT_FLAG_DAMAGE_STEP so… |
| Vampire Lord | 53839837 | `erratum-vampire-lord` | **A** | `504700087` | No source in the packet dates when (or whether) Vampire Lord's self-revival stopped being restricted to… | locate a dated period ruling on whether Vampire Lord's Standby Phase revival was already restricted to being… |


### 9. Damage Step activation windows — 2 cards, both partition B

Both need a custom script changing which event/condition a Damage-Step-
relevant trigger checks; no shared sub-pattern beyond the general category
given only two cards.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Green Baboon, Defender of the Forest | 46668237 | `erratum-green-baboon-defender-of-the-forest` | **B** | none | no usable historical implementation exists upstream (the packet's one upstream entry, passcode 511001661 'Green Baboon, Defender of the… | write a custom Lua script switching the trigger to EVENT_DESTROYED with no face-up filter and adding… |
| Rise of the Snake Deity | 16067089 | `erratum-rise-of-the-snake-deity` | **B** | none | No usable implementation exists: the packet's only upstream code, 511002525 'Rise of the Sacred Deity (Anime)', is a different card and… | write a custom Lua script removing the battle-destruction exclusion and adding… |


### 10. Miss-timing / EFFECT_FLAG_DELAY — 1 card, partition A

Axe of Despair: whether its Graveyard-send trigger was already exempt from
missing the timing (`EFFECT_FLAG_DELAY`) at Edison is chronology-only; the
existing goat-script implementation already reproduces the exemption if the
date confirms it applied by April 2010.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Axe of Despair | 40619825 | `erratum-axe-of-despair` | **A** | `504700068` | An exact date or bounded interval for when Axe of Despair's send-to-Graveyard trigger stopped being exempt from missing the timing (i.e.,… | locate a dated period ruling on when Axe of Despair's Graveyard-send trigger lost its exemption from missing… |

## Prioritisation

Two evidence-internal views, kept separate as instructed. No popularity,
"meta," or deck-prevalence claim appears anywhere below — this project has
not gathered sourced Edison-era tournament/deck data, and none is used here.

### Leverage priority (cards correctable per shared question/pattern)

| Rank | Cluster | Cards | What resolves it |
|---|---|---|---|
| 1 | Failed-search / deck-verification | **38** | one dated period source on the general "activate-without-a-valid-target" ruling |
| 2 | Cannon-lineage contact-fusion material (XY-/XYZ-/XZ- Dragon/Tank Cannon, split across target-legality + cost-payment above) | **3** | one dated period source on contact-fusion material eligibility for this lineage |
| 3 | Nomi-to-semi-nomi wording (within cluster 2) | **~7** | one reusable "strict Nomi lock" Lua pattern (chronology already resolved) |
| 4 | Union Condition removal (within cluster 2) | **2** | one reusable "Union equip restriction" Lua pattern (chronology already resolved) |
| 5 | Once-per-turn/name-lock sub-groups (D.D. pair; die/coin-redo quartet; Standby-revival pair) | **8** of 9 | up to 3 reusable OPT-removal patterns (chronology already resolved) |
| — | Everything else (target-legality remainder, activation-condition, card-specific, trigger-registration, damage-step, miss-timing) | **26** | no shared question or pattern found; bespoke per card |

Rows 1 and 2 are RESEARCH leverage (chronology questions); rows 3-5 are
IMPLEMENTATION leverage (shared script patterns, chronology already settled).
Row 1 alone accounts for 38/85 = 44.7% of every card this milestone covers.

### Severity priority (nature of the behavioural deviation, not frequency)

Ranked by what the deviation actually does to a legal play, most severe
first:

1. **Functional lockout — a legal action is entirely unavailable.** The
   effect cannot be activated at all in modern where period evidence says an
   Edison-era player could attempt it (even a doomed attempt, revealed as a
   proven whiff, was itself a legal, informative action). Covers the
   **38-card** failed-search/deck-verification cluster in full, plus the
   Main-Phase-gated and attacker-condition cards in
   activation-condition-changes (**Blackwing - Sirocco the Dawn, Blast Held
   by a Tribute** - 2 of 4).
2. **Wrong legal scope/frequency on an effect that DOES activate.** The
   effect works, but who/what it may target, or how often it may be used,
   differs from the period rule. Covers **once-per-turn-name-lock (9)**,
   **target-legality (8)**, **cost-payment-behaviour (4)**, and the
   nomi-to-semi-nomi/Union sub-patterns within other-shared-ruling-era-change
   (**9** of 12).
3. **Trigger timing/registration differences.** WHEN a chain window opens
   changes, not WHETHER an action is possible. Covers
   **trigger-registration (3)**, **miss-timing-effect-flag-delay (1)**,
   **damage-step-activation-windows (2)**.
4. **Card-specific, severity varies per card** - the remaining
   **card-specific-errata (4)** and the 3 genuinely-distinct
   other-shared-ruling-era-change cards (Dark Necrofear, Evil HERO Dark Gaia,
   Necrovalley) each need individual severity judgement; none fit a general
   tier.

Tallying: **~40 cards** in tier 1 (functional lockout, the most severe class)
- and the 38-card leverage-priority #1 cluster is *also* the severity-tier-1
majority, so the single highest-leverage research target and the single most
severe behavioural-deviation class are the same cluster. That convergence,
not a popularity judgement, is the basis for the recommendation below.

## Recommended next milestone

**Research and resolve the shared "activate-without-a-valid-target +
Deck-verification-on-whiff" chronology question for the 38-card
failed-search/deck-verification cluster.**

This is a RESEARCH task (matching the task brief's first example option), not
an implementation task - consistent with this milestone's explicit
instruction not to start custom-script work yet.

- **How many Edison cards it could correct:** up to 38 directly (44.7% of
  the 85 this audit covers, 86% of the 44 known-wrong records), each already
  backed by a working `reuse-upstream` implementation once its version index
  is determined - resolving the chronology is the *entire* remaining blocker
  for every one of them. A second, smaller opportunity of the same
  RESEARCH shape (3 cards: XY-/XYZ-/XZ- Dragon/Tank Cannon, the contact-
  fusion-material question) could be picked up in the same research pass at
  low marginal cost, for up to 41 cards total.
- **Why this outranks the alternatives:** it is simultaneously the top
  LEVERAGE item (38 cards from one shared question, vs. at most ~9 for any
  implementation-pattern cluster) and lands in the top SEVERITY tier
  (functional lockout - the deviation blocks a legal action outright, not
  merely its scope or timing). The next-largest cluster
  (other-shared-ruling-era-change, 12 cards) is already chronology-resolved
  and blocked purely on missing Lua/CDB implementations - exactly the kind
  of work this milestone's instructions say not to start yet. Every other
  cluster is smaller and less structurally uniform.
- **What evidence it would require:** a dated period source (2010-2018 TCG
  window - a Konami ruling/FAQ, judge-program communication, or tournament-
  policy note) establishing when TCG tournament rulings began requiring a
  legitimate target/match to already exist before these "search-type,
  reveal-on-failure" effects could legally be activated - ideally dated
  close enough to 2010-04-24 to resolve whether Edison itself falls before
  or after the transition, narrowing the currently wide-open interval
  bracketed only by `old_attested_through: 2011-02-02` /
  `new_attested_from: 2019-04-03`. This is squarely a continuation of this
  project's own pre-existing roadmap item 1a/1b ("chronology for the undated
  era rulings" / "close the search-verification interval"), now reduced from
  a vague generality to a precisely-scoped, 38-named-card target. No code
  changes are implied by this recommendation - only research, matching what
  this milestone was scoped to produce.

Not started in this commit, per the task's explicit instruction.
