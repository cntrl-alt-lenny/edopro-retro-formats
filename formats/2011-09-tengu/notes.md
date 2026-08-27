# Tengu Format (2011-09-tengu)

The TCG format named for Reborn Tengu and Tengu Plant decks at the start of the
September 1, 2011 Forbidden/Limited list era, snapshot at September 17, 2011 - the
first day of YCS Toronto 2011 (the defining premier event that introduced Xyz
Monsters to premier competitive play).

Tengu is the project's third canonical format. It stress-tests the repository
architecture across a major rules era boundary: Master Rule 2, the introduction of
Xyz Monsters, a 4,562-card certified release pool, an official 51/65/18 banlist,
and the evaluation of the 296-record v2 errata corpus at a late 2011 snapshot.

## Data status

- **Banlist `tcg-2011-09` — complete.** Sourced from the official Konami
  September 1, 2011 list (51 forbidden / 65 limited / 18 semi-limited) and
  cross-checked against Format Library and TenguFormat.com. The seven cards moved
  to Unlimited are historical research provenance and are not emitted as
  restricted entries.
- **Pool `pool-tengu-2011` — verified (4,562 cards).** Materialised from
  data/releases/ under certified coverage through 2011-09-17 across all TCG
  territories (`tcg`, `tcg-na`, `tcg-eu`, `tcg-oce`), with zero release ambiguities
  and zero unknown printings. Product exclusions are period-supported: Duel
  Terminal 4/5/5a machine-only cards excluded under KDE Tournament Policy v1.1
  (2011), and Sneak Peek participation cards excluded under official product-archive
  evidence. Escuridao (YG09-EN001) is absent because its official TCG release date
  was 2012-08-07. Generation Force cards and early Xyz monsters are legal.
- **Rules `rules-tcg-mr2-tengu` — partial.** Uses Master Rule 2 baseline flags:
  `DUEL_1ST_TURN_DRAW`, `DUEL_1_FACEUP_FIELD`, `DUEL_SPSUMMON_ONCE_OLD_NEGATE`,
  `DUEL_RETURN_TO_DECK_TRIGGERS`, and `DUEL_CANNOT_SUMMON_OATH_OLD`, plus
  `DUEL_OCG_OBSOLETE_IGNITION` as a documented engine approximation for 2011 TCG
  Ignition Effect Priority. `DUEL_0_ATK_DESTROYED` is omitted (Version 7.2
  rulebook was already in force) and `DUEL_TCG_FAST_EFFECT_IGNITION` is deliberately
  not enabled.
- **Errata — partial, and computed.** Applicability is computed from each record's
  evidence against the 2011-09-17 snapshot:
  - 126 determinate records: 33 modern, 52 historical substitutions (`reuse-upstream`),
    38 acknowledged divergences (`known-gap`), 3 `none-needed`.
  - 170 ambiguous records: handled by `errata_overrides.unresolved_policy` (choice: `modern`),
    surfacing 161 ambiguous-modern-possible defaults and 9 modern-impossible
    known-wrong fallbacks.
  - Zero hand-authored erratum overrides; all 52 historical substitutions arise
    mechanically from the canonical v2 errata corpus.
- **Chronology.** Left null until adjacent canonical formats are implemented.

## EDOPro Host Settings

| Setting | Value |
|---|---|
| Banlist | `Retro 2011-09-tengu` (whitelist / pool-enforcing) |
| Duel Rule preset | `Master Rule 2` |
| Allowed cards | `Anything goes` (historical cards are `ot=8`) |
| Forbidden card types | `TYPE_PENDULUM`, `TYPE_LINK` |

