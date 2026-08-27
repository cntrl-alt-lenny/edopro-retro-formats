# Tengu Format source and implementation gate

Status: research gate only. This commit extends and certifies the shared TCG
release ledger through the proposed snapshot, but creates no canonical Tengu
format, banlist, pool, or rule profile.

## Recommendation

Use format id `2011-09-tengu`, displayed as **Tengu Format** (alias: Tengu
Plant), with an inclusive TCG snapshot of `2011-09-17`, the first day of YCS
Toronto. Konami's event coverage places YCS Toronto on September 17–18, 2011;
the event article describes it as the first YCS under the new list and calls
out the new Xyz cards. Format Library independently records `2011-09-17`,
September 2011, TCG, and YCS Toronto. TenguFormat.com makes the same community
definition.

This is a community-retrospective format definition, not a claim that every
territory had identical shelf availability on that day. The release ledger
therefore uses all English-family TCG territory events and the repository's
existing availability model.

Sources: [Konami Toronto coverage](https://yugiohblog.konami.com/category/ycs/11-09-toronto/),
[Konami Toronto event article](https://yugiohblog.konami.com/2011/ycs/ycs-toronto-first-timers-2/),
[Format Library Tengu API](https://formatlibrary.com/api/formats/tengu),
[TenguFormat.com](https://tenguformat.com/ycs-toronto-2011/).

## Evidence labels and reproducibility

* **Primary historical fact** means official Konami product, event, list or
  rulebook material.
* **Community convention** means Format Library or TenguFormat.com evidence
  about what retro players call Tengu.
* **Implementation evidence** means the pinned importer, BabelCDB, EDOPro or
  ocgcore source. It describes executable behaviour, not automatically the
  date a historical rule changed.
* **Inference** is an explicit conclusion from those sources.
* **Unresolved** is not silently converted into a date or legality claim.

The raw fetch cache is intentionally not committed. The committed
`data/imported/releases-report.json`, product records, coverage window, gap
ledger, and card index are deterministic outputs of the offline importer and
identity importer. The gate test reconstructs the proposed pool in memory; it
does not create a Tengu pool file.

## Banlist

The official [2011 September 1 list](https://www.yugioh-card.com/japan/event/limitregulation/?list=201109)
is the primary cross-check. Its TCG column contains 51 Forbidden, 65 Limited,
and 18 Semi-Limited cards, with seven cards released to Unlimited. The OCG
column has one additional Forbidden card (Sixth Sense); it is not copied into
the TCG packet. Format Library's
[September 2011 TCG API record](https://formatlibrary.com/api/banlists/september-2011?category=TCG)
and TenguFormat.com's [banlist page](https://tenguformat.com/banlist/) agree on
the TCG counts and identities.

The exact modern passcodes and names are in
[`tengu-format-source-packet.json`](tengu-format-source-packet.json). That
packet is a research artifact, not canonical banlist data. The next
implementation task should create one TCG list with effective date
`2011-09-01` after checking the packet against the card index.

## Snapshot and release-ledger certification

The proposed cutoff is `2011-09-17`, scope
`tcg`, `tcg-na`, `tcg-eu`, and `tcg-oce`. `Generation Force` is the latest
core booster before the snapshot, but “through GENF” is not by itself a pool
rule: the ledger includes all dated TCG products and promos through the
cutoff.

Official product pages were used as boundary cross-checks for [Storm of
Ragnarok](https://www.yugioh-card.com/en/products/past_products/stor/),
[Extreme Victory](https://www.yugioh-card.com/en/products/past_products/exvc/),
[Hidden Arsenal 4](https://www.yugioh-card.com/en/products/past_products/ha04/),
[Dawn of the Xyz](https://www.yugioh-card.com/en/products/past_products/starter2011/),
[GENF](https://www.yugioh-card.com/en/products/past_products/genf/),
[Hidden Arsenal Special Edition](https://www.yugioh-card.com/en/products/past_products/ha-se/),
[2011 tins](https://www.yugioh-card.com/en/products/past_products/tin-2011w1-wz/),
and the [2011 product archive](https://www.yugioh-card.com/en/products/past_products/others-archives/).
The ledger retains regional events rather than collapsing them: for example,
GENF is 2011-08-16 in North America and 2011-08-12 in Europe/Oceania, while
the GENF Special Edition has 2011-09-15 European/Oceanic events and a
2011-09-20 North American event. The Special Edition contributes no new card
at the cutoff because its two cards were already available earlier.

The real importer was run offline through `2011-09-17` against the fetched
Yugipedia/YGOPRODeck inputs and the pinned BabelCDB checkout. Existing product
bytes were unchanged; 41 new product records were added.

| certified quantity | result |
|---|---:|
| product records | 411 (404 generated + 7 curated) |
| importer printings | 9,338 |
| importer release events | 585 |
| canonical release printings | 9,339 (including the existing curated WC2004 roster) |
| canonical release events | 587 (including the existing curated WC2004 roster) |
| card-index rows | 4,841 |
| unmatched cards | 8, all pre-2011 one-of-a-kind prizes |
| products without printings | 4, all already-ledgered prize/non-card products |
| Yugipedia-only products | 34, including two newly accounted-for 2011 products |
| unresolved pool-impacting gaps | 0 |

The two newly reported Yugipedia-only products are harmless by explicit gap
records: the 2011 Blu-ray promo repeats the earlier Movie Pack
`Malefic Red-Eyes Black Dragon`, and the 2011 World Championship prize set is
not an ordinary tournament-legal product. `Malefic Truth Dragon` is the one
boundary ambiguity: its coarse JUMP-EN048 ledger date is resolved by the
[official card database](https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=9042&ope=2&request_locale=en),
which identifies the TCG printing as March 2011. The research-only pool uses
that sourced include, so no card remains ambiguous at the cutoff.

The fresh candidate pool has **4,563 cards**, zero boundary ambiguities, and
zero unknown printings. It excludes only the period-supported Duel Terminal
4/5/5a machine-only product events and the three Sneak Peek participation
products. The latter exclusions are explicit legality policy, not a change to
release facts; each participation card also has an ordinary earlier release,
so the exclusions do not alter the count. No Edison product exclusions are
reused.

Validation remains error-free. The warning count changes from 360 to 361:
the only new finding is `releases.number-prefix` for `DPCT-EN005` stored under
the `DPC5` Duelist Pack Collection Tin 2011 record. This is an upstream
set-membership bookkeeping discrepancy preserved by the importer, not a
pool-coverage failure; no existing warning disappears.

TenguFormat.com's downloadable [card JSON](https://tenguformat.com/wp-content/uploads/database/allCardsTengu.json)
contains 5,035 current records, 4,572 with a current `tcg_date` on or before
the proposed date. It is a useful community cross-check, not a pinned
historical whitelist: it uses modern/alias identities and current dates, and
differs from the ledger projection by six identities plus fifteen
community-only identities. Those differences are reported, not silently
forced into the release data.

## Rule-profile gate

Recommendation: a future explicit MR2-era TCG profile, with the existing
Edison ignition-priority approximation documented as an engine limitation.
All proposed constants exist in the pinned
[`ocgapi_constants.h`](https://github.com/edo9300/ygopro-core/blob/46779fbe40e6a9bd8967f5dc6a03f4eaa6550d57/ocgapi_constants.h).

Proposed flags:

* `DUEL_1ST_TURN_DRAW`
* `DUEL_1_FACEUP_FIELD`
* `DUEL_SPSUMMON_ONCE_OLD_NEGATE`
* `DUEL_RETURN_TO_DECK_TRIGGERS`
* `DUEL_CANNOT_SUMMON_OATH_OLD`
* `DUEL_OCG_OBSOLETE_IGNITION` — separate, least-wrong approximation only

The first five are the pinned core's MR2-era expansion. The ignition flag is
not presented as exact TCG history: TCG ignition priority remained in force
at Toronto, but the current core couples the OCG obsolete location gate to a
broader model and cannot express the exact TCG window without a core change.
Do not enable `DUEL_TCG_FAST_EFFECT_IGNITION`; it grants a broader post-chain
window. Omit Edison’s `DUEL_0_ATK_DESTROYED`: the v7.2 rulebook change was
already in force by 2011.

The v8.0 rulebook supports ordinary early-Xyz behaviour: same-Level face-up
monsters are overlaid, materials are underneath the Xyz monster, detach sends
the material to the Graveyard, materials are not cards on the field, and
Tokens cannot be Xyz materials. Current ocgcore has native Xyz handling and no
separate early-Xyz flag. No additional historical engine flag is justified by
this gate. Fine-grained SEGOC/private-trigger/trap-timing questions remain
unresolved rather than guessed.

## Erratum-selection audit

All 296 canonical v2 errata evaluate at the snapshot without runtime changes:

| selection result | records |
|---|---:|
| determinate MODERN | 33 |
| determinate `reuse-upstream` | 52 |
| determinate `known-gap` | 38 |
| determinate `none-needed` | 3 |
| ambiguous, modern possible | 161 |
| ambiguous, modern impossible | 9 |
| unresolved candidate-state occurrences | 89 |

The existing Edison-style unresolved policy would select 52 historical
passcodes, but that is an audit result rather than a Tengu override decision.
No per-format erratum override is created by this gate.

## Edison → Tengu comparison

| dimension | Edison (`2010-04-24`) | proposed Tengu (`2011-09-17`) |
|---|---|---|
| pool method | community retrospective, Edison cutoff | certified all-TCG release cutoff |
| release ledger | through 2010-12-31 | through 2011-09-17 |
| pool projection | existing materialised Edison pool | fresh 4,563-card research projection |
| list | March 2010 | September 2011, 51/65/18 |
| rules | MR1-era TCG profile | MR2-era profile plus ignition approximation |
| Xyz | unavailable | legal, native core handling |
| errata data | same 296-record v2 corpus | same corpus evaluated at a later date |
| unresolved historical states | represented by v2 | represented by v2; not overridden here |

The difference is produced by the shared release ledger and snapshot, not by
hand-authoring a Tengu card list.

## Architecture verdict

**Existing architecture is sufficient for the proposed Tengu implementation
inputs.** A future canonical implementation needs only new data files and
tests: `formats/2011-09-tengu/format.json` and sources, a September 2011 TCG
banlist, a certified release-cutoff pool with the documented policy entries,
an explicit TCG MR2-era rule profile, and format-specific tests/reporting.

No change to `retroformats/model.py`, `retroformats/lflist.py`,
`retroformats/validate.py`, `schemas/`, or generated `dist/` is required by
this gate. The only known approximation is in the existing ocgcore
ignition-priority behavior. If exact TCG ignition behavior is later required,
that is an engine/core task, not a data-file workaround.

Unresolved work for the next implementation task is limited to final review of
the policy wording and community-pool differences, and creation of the
canonical Tengu data files. This gate does not authorize that implementation.
