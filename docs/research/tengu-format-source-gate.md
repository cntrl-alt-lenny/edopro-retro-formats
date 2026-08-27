# Tengu Format source and implementation gate

Status: research gate only. No Tengu format, pool, banlist, rule profile, or
generated output is canonical in this commit.

## Recommendation in one paragraph

Use `2011-09-tengu`, displayed as **Tengu Format** (aliases: Tengu Plant),
with a TCG snapshot of `2011-09-17`, the first day of YCS Toronto. The event
was held September 17–18, 2011, and Konami's contemporary coverage calls it a
new format under the new Forbidden & Limited List and the newly released Xyz
cards. The community definition agrees: Format Library records `2011-09-17`,
September 2011, TCG, and YCS Toronto; TenguFormat.com describes the same event
and Generation Force boundary.

This gate does **not** recommend creating the format yet. The current release
ledger is certified only through `2010-12-31`. Its in-memory projection at the
proposed date is 4,037 cards after the existing Edison exclusions, but that is
an incomplete lower bound, not a defensible Tengu pool. The next implementation
task must first extend and certify the release ledger through the snapshot.

## Source hierarchy and evidence labels

Claims below are labelled as follows:

* **Primary historical fact** — official Konami product, event, rulebook, or
  list material.
* **Community convention** — Format Library or TenguFormat.com definition,
  useful for reproducing what retro players mean by Tengu but not a substitute
  for release or policy evidence.
* **Implementation evidence** — pinned EDOPro/Project Ignis source or this
  repository's tested machinery; it describes executable behaviour, not by
  itself when a historical rule changed.
* **Inference** — a conclusion drawn from the evidence and explicitly marked.
* **Unresolved** — the evidence is not sufficient to claim a fact.

The research used official Konami event/product/rulebook material first,
period or archived policy material where available, then the two community
format definitions, Yugipedia/other lineage material for discovery, and the
project's pinned engine/repository evidence. The packet next to this document
contains the exact researched September 2011 TCG banlist identities; it is a
research artifact, not a file under `data/banlists/`.

## Snapshot and defining event

* **Primary historical fact:** Konami's Toronto coverage category identifies
  “Championship Series – Toronto, Canada” on September 17–18, 2011. The event
  article dated September 17 says it is the first YCS under the new list and
  highlights the new Xyz monsters in Generation Force.
* **Community convention:** Format Library's API identifies format 24 as
  “Tengu”, date `2011-09-17`, category TCG, banlist “September 2011”, and event
  “YCS Toronto - September 2011”. TenguFormat.com identifies YCS Toronto 2011
  as September 17, 2011 and describes Generation Force as the latest core set.
* **Recommendation:** snapshot `2011-09-17`, inclusive, TCG. This is the day-1
  tournament snapshot, not a claim that every card physically obtainable in
  every territory had an identical shelf date.

Sources: [Konami Toronto coverage category](https://yugiohblog.konami.com/category/ycs/11-09-toronto/),
[Konami Toronto first-timers article](https://yugiohblog.konami.com/2011/ycs/ycs-toronto-first-timers-2/),
[Format Library Tengu API](https://formatlibrary.com/api/formats/tengu),
[TenguFormat.com](https://tenguformat.com/),
[TenguFormat YCS Toronto page](https://tenguformat.com/ycs-toronto-2011/).

## September 2011 TCG list

**Primary historical fact:** Konami's September 1, 2011 historical list page
labels the list “2011 Sep 1 applicable list”. It displays OCG and TCG columns
side by side. The OCG column has 52 Forbidden cards because it includes
Sixth Sense; the TCG column has 51 because Sixth Sense is not in the TCG
column. The TCG counts are therefore:

| status | count |
| --- | ---: |
| Forbidden | 51 |
| Limited | 65 |
| Semi-Limited | 18 |
| cards released from the list | 7 |

The exact names and passcodes are in
[`tengu-format-source-packet.json`](tengu-format-source-packet.json). The
packet is independently cross-checked against Format Library's TCG API
response: 51/65/18 and the same seven release-to-unlimited entries. The packet
uses modern canonical card identities, not Format Library's internal row IDs.

Sources: [Konami historical September 2011 list](https://www.yugioh-card.com/japan/event/limitregulation/?list=201109),
[Format Library September 2011 TCG list API](https://formatlibrary.com/api/banlists/september-2011?category=TCG),
[TenguFormat list](https://tenguformat.com/banlist/).

No canonical banlist file is created in this gate. The next task should create
one TCG list with effective date `2011-09-01`, after checking the packet against
the repository card index for any historical-identity exceptions.

## Card-pool cutoff and release-ledger result

The project rule is to derive a pool from per-product, per-territory release
events and then materialise a reviewable projection. A core-set label is not
itself a legality rule. The recommended cutoff is the event snapshot date,
`2011-09-17`, with the project's default all-TCG territory scope, followed by
explicit product-policy exclusions/includes where period evidence demands them.

Relevant official product anchors found:

| product | Konami tournament-legal date | consequence |
| --- | --- | --- |
| Storm of Ragnarok | 2011-02-08 | before snapshot |
| Hidden Arsenal 4 | 2011-04-19 | before snapshot |
| Extreme Victory | 2011-05-10 | before snapshot; includes Reborn Tengu and Tour Guide |
| Gold Series 4 | 2011-07-01 | before snapshot |
| Starter Deck: Dawn of the Xyz | 2011-07-12 | before snapshot; Xyz introduction product |
| Hidden Arsenal Special Edition | 2011-08-02 | before snapshot; variant/repack product must be ledger-audited |
| Generation Force | 2011-08-16 | before snapshot; first Xyz core booster |
| first-wave 2011 tins | 2011-08-30 | before snapshot; promos and reprints must be ledger-audited |
| Generation Force Special Edition | 2011-09-20 | after snapshot; exclude from Toronto |
| second-wave 2011 tins | 2011-11-01 | after snapshot; exclude from Toronto |

Sources: [GENF](https://www.yugioh-card.com/en/products/past_products/genf/),
[Dawn of the Xyz](https://www.yugioh-card.com/en/products/past_products/starter2011/),
[Storm of Ragnarok](https://www.yugioh-card.com/en/products/past_products/stor/),
[Extreme Victory](https://www.yugioh-card.com/en/products/past_products/exvc/),
[Hidden Arsenal 4](https://www.yugioh-card.com/en/products/past_products/ha04/),
[Hidden Arsenal Special Edition](https://www.yugioh-card.com/en/products/past_products/ha-se/),
[2011 product archive](https://www.yugioh-card.com/en/products/past_products/others-archives/),
[first-wave Wind-Up Zenmaister Tin](https://www.yugioh-card.com/en/products/past_products/tin-2011w1-wz/),
[GENF Special Edition](https://www.yugioh-card.com/en/products/past_products/genf-se/).

The live repository currently contains no 2011 product records and declares
release coverage complete only through `2010-12-31`. Running the real
`ReleaseIndex` and `evaluate_cutoff()` in memory against the current data gives:

* 4,143 dated canonical cards before the Edison pool's product/policy
  exclusions;
* 4,037 included cards after reusing those existing exclusions;
* 0 current boundary ambiguities;
* 0 unknown printings;
* coverage certification: **false** for `2011-09-17`.

The 4,037 figure is deliberately reported as an **incomplete lower bound**.
It does not contain GENF, Dawn of the Xyz, 2011 tins, later 2011 promos, or
other 2011 records missing from the ledger. The implementation task must add
the missing product/release/printing evidence and rerun the importer and gap
ledger. It must then compare the derived set with the community pools at
Format Library/TenguFormat.com; no machine-readable community whitelist was
used as canonical input here.

Unresolved release work includes the complete 2011 product inventory, exact
TCG territory/date events, promo and tin contents, Special Edition/repack
semantics, tournament-product releases, and any artwork/passcode aliases at
the boundary. The current ledger's absence of those records is the gap; it is
not evidence that those cards were illegal.

## Rule-profile research

The proposed profile is a custom explicit profile based on the Master Rule 2
era, with the historical TCG ignition-priority approximation already documented
for Edison. It should not be declared a bare “MR2” preset without documenting
the TCG/OCG divergence.

Proposed flags, all present in the pinned `ocgapi_constants.h` at core commit
`46779fbe40e6a9bd8967f5dc6a03f4eaa6550d57`:

`DUEL_OCG_OBSOLETE_IGNITION`, `DUEL_1ST_TURN_DRAW`,
`DUEL_1_FACEUP_FIELD`, `DUEL_SPSUMMON_ONCE_OLD_NEGATE`,
`DUEL_RETURN_TO_DECK_TRIGGERS`, and `DUEL_CANNOT_SUMMON_OATH_OLD`.

The client constraints should remain 40–60 Main Deck, 0–15 Extra Deck, and
0–15 Side Deck. The forbidden card types should be `TYPE_PENDULUM` and
`TYPE_LINK`; `TYPE_XYZ` is legal. The 2011 rulebook's Extra Deck section
allows up to 15 Xyz/Synchro/Fusion cards and its Xyz section describes
face-up same-Level materials, stacking, and detaching to the Graveyard.

| historical rule question | source/evidence | engine treatment | result |
| --- | --- | --- | --- |
| Master Rule generation | 2011 Rulebook v8.0; product/event timing | explicit MR2-era flags | exact for the ordinary rules represented by those flags |
| first-turn draw | v8.0 turn structure; core constant | `DUEL_1ST_TURN_DRAW` | retained |
| one face-up Field Spell | v8.0 field-zone text; core constant | `DUEL_1_FACEUP_FIELD` | retained |
| Xyz Summon/materials/detach | v8.0 pp. 12–13 and 45; current core Xyz data structures | `TYPE_XYZ`, normal current Xyz processing | ordinary 2011 rules expressible; no special historical Xyz flag found |
| Extra Deck and Side Deck sizes | v8.0 deck rules | client limits 15/15 | exact as stated |
| summon-negation once-per-turn behavior | Edison profile/core | `DUEL_SPSUMMON_ONCE_OLD_NEGATE` | retained pending a Tengu-specific contrary source |
| return-to-deck triggers | Edison profile/core | `DUEL_RETURN_TO_DECK_TRIGGERS` | retained pending a Tengu-specific contrary source |
| old summon-oath restrictions | Edison profile/core | `DUEL_CANNOT_SUMMON_OATH_OLD` | retained pending a Tengu-specific contrary source |
| ignition priority | TCG history places removal on 2012-04-25; Toronto predates it | `DUEL_OCG_OBSOLETE_IGNITION` only as the existing least-wrong approximation | not exact: core couples summon gate and Monster-Zone location |
| SEGOC | v8.0 says turn-player effects then opponent effects; finer TCG details unresolved in Edison research | no extra SEGOC flag | do not guess |
| private/non-public triggers | no period source strong enough for the candidate flags | no extra flag | unresolved |
| Trap activation in a new Chain | no Tengu-specific period proof found in this gate | no `DUEL_USE_TRAPS_IN_NEW_CHAIN` addition | unresolved |
| repositioning by non-turn player | no Tengu-specific period proof found | no extra flag | unresolved |
| 0-ATK battle | v7.2 added the “neither destroyed” exception before Toronto | omit Edison-only `DUEL_0_ATK_DESTROYED` | Tengu uses the later exception |
| End Phase handling | no change source found at the boundary | current core default | no separate Tengu setting justified |

The exact pinned constants are in [ocgapi_constants.h](https://github.com/edo9300/ygopro-core/blob/46779fbe40e6a9bd8967f5dc6a03f4eaa6550d57/ocgapi_constants.h)
and the coupled ignition gate is in [processor.cpp](https://github.com/edo9300/ygopro-core/blob/46779fbe40e6a9bd8967f5dc6a03f4eaa6550d57/ocgcore/processor.cpp).
The contemporary rulebook copy used for page-level inspection is
[Rulebook v8.0](https://ms.yugipedia.com/3/36/Rulebook_v8.0_updated.pdf).

### Ignition Priority conclusion

**Primary/period fact:** TCG ignition priority remained in force at Toronto;
the TCG change is independently reported as April 25, 2012, whereas the OCG
change occurred with the earlier OCG Master Rule 2 transition. The project’s
Edison dossier provides the strongest local analysis of the exact TCG behavior.

**Recommendation:** retain `DUEL_OCG_OBSOLETE_IGNITION` as the least-wrong
compatibility approximation, explicitly mark it as an engine gap, and do not
enable `DUEL_TCG_FAST_EFFECT_IGNITION`. The latter grants a window after any
chain end and is too broad; the former has the correct Summon gate but the
wrong location restriction. Exact TCG behavior would require a core change,
which is out of scope and must not be hidden in Tengu data.

### Xyz conclusion

The 2011 rulebook directly supports the ordinary early-Xyz model: same-Level
face-up monsters are overlaid, materials are underneath the Xyz monster, and
detaching sends a material to the Graveyard. It also states that Xyz materials
are not cards on the field, that tokens cannot be Xyz materials, and that an
Xyz monster leaving the field sends its materials to the Graveyard. The pinned
core has native Xyz material and detach handling and no separate “early Xyz”
flag. No source found in this gate establishes a TCG-specific early-Xyz
behavior that the current data profile can or must toggle. Card-specific
rulings still need ordinary test coverage in the implementation task.

## 296-record erratum audit

This was run entirely in memory at `2011-09-17`; it did not create a Tengu
format or alter any record. Every canonical record loaded as `ErratumV2`.

| result | records |
| --- | ---: |
| determinate MODERN | 33 |
| determinate `reuse-upstream` | 52 |
| determinate `known-gap` | 38 |
| determinate `none-needed` | 3 |
| determinate total | 126 |
| ambiguous, MODERN possible | 161 |
| ambiguous, MODERN impossible | 9 |
| ambiguous total | 170 |
| records with an unresolved candidate implementation | 47 |
| unresolved candidate-state occurrences | 89 |

Under the existing Edison-style explicit `unresolved_policy: modern`, the
determinately historical substitutions would be 52 upstream passcodes; the
exact card/passcode result is reproducible with:

```console
python3 - <<'PY'
import datetime as d
from pathlib import Path
from retroformats.repo import Repository
from retroformats.model import ErratumV2
from retroformats.lflist import select_applicable_errata
from dataclasses import replace
r = Repository.load(Path('.'))
f = replace(r.formats['2010-03-edison'], id='research-tengu', snapshot='2011-09-17',
            reference_parity=None, errata_include=[], errata_exclude=[])
print(len(select_applicable_errata(f, r)))
for code, o in sorted(select_applicable_errata(f, r).items()):
    print(code, o.implementation.historical_passcode)
PY
```

That output is an audit of what the current policy would do, not a decision
that the future Tengu format should adopt that policy. A canonical Tengu
format must either supply a sourced unresolved policy or leave the 170
ambiguous cases visibly unresolved; it must not create per-card overrides to
silence diagnostics. The 170 diagnostic IDs are mechanically the records whose
`selection_at(date)` result is ambiguous, and the test added by this gate
pins the total and the 161/9 modern-possibility split.

The audit answers the central architecture question: the v2 erratum database
does make the format’s historical substitutions largely automatic where
chronology is determinate, but it does not erase unresolved chronology or
implementation gaps. That residual uncertainty is represented by the existing
selection model rather than a Tengu-specific abstraction.

## Edison → Tengu comparison

| dimension | Edison (`2010-04-24`) | proposed Tengu (`2011-09-17`) |
| --- | --- | --- |
| event | SJC Edison | YCS Toronto |
| pool | 3,673 verified cards | not yet certifiable; current incomplete projection 4,037 |
| list | March 2010 | September 2011, 51/65/18 |
| Xyz | illegal | legal; first Xyz-era snapshot |
| first-turn draw | yes | yes |
| Field Spell | one face-up | one face-up |
| 0-ATK tie | both destroyed (`DUEL_0_ATK_DESTROYED`) | neither destroyed; omit Edison flag |
| ignition priority | TCG behavior, approximated by OCG-obsolete flag | same TCG behavior and same approximation |
| erratum audit | older snapshot with Edison policy | 126 determinate, 170 ambiguous at this date |
| engine gap | exact TCG ignition priority and several unresolved flags | same ignition gap; no new historical flag found |

The pool and list differences are historical inputs, not independent format
hand-authoring. The only expected rule-profile flag change from Edison is
removal of `DUEL_0_ATK_DESTROYED`; Xyz is enabled by allowing `TYPE_XYZ`, not by
inventing a new engine mode.

## Architecture stress-test verdict

**A — existing repository architecture is sufficient for a truthful canonical
Tengu data implementation**, subject to two explicitly separate qualifications:

1. The release dataset must be extended and certified through September 17,
   2011 before a pool can be materialised. This is missing source data, not a
   model deficiency demonstrated by this gate.
2. Pinned `ygopro-core` cannot express the exact historical TCG ignition
   priority because its two relevant dimensions are coupled. The existing
   rule-profile vocabulary can record this as a known engine gap and retain a
   least-wrong approximation; exact duel-engine fidelity would require a
   future core change, which this gate does not authorize.

No deficiency requiring a change to `retroformats/model.py`,
`retroformats/lflist.py`, `retroformats/validate.py`, or `schemas/` was found.
No per-format erratum override is justified by this gate.

## Exact next implementation work

The next task should create only after review:

* `formats/2011-09-tengu/format.json` and its format source record;
* a certified TCG September 2011 banlist under `data/banlists/tcg/`;
* a release-derived, materialised Tengu pool under `data/pools/` after the
  2011 ledger extension and gap certification;
* a Tengu rule profile under `data/rule-profiles/`, with the six explicit
  flags above and the ignition approximation documented as a known gap;
* generated `dist/` output and focused tests only after the source data passes
  validation.

This gate intentionally created none of those canonical files and did not
modify the 296 errata, runtime, schemas, existing formats, or `dist/`.

## Reproducibility checks

The research-only checks are in
[`tests/test_tengu_format_gate.py`](../../tests/test_tengu_format_gate.py).
They verify that no Tengu artifacts exist, the packet has exact internal list
counts and unique identities, all 296 v2 errata evaluate at the proposed
snapshot, and the current release projection remains explicitly uncertified.
They do not use a network request or mutate the repository.

At gate time the normal live invariants remain: canonical errata `296 v2 / 0
v1`, GOAT hash `0x28E9FC02`, Edison pool `3,673`, and no canonical Tengu data.
