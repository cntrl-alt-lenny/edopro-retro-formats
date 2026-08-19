# The release dataset: how card legality is derived

`data/releases/` answers the question every historical card pool depends on:

> **Was card X legally obtainable, in territory scope S, on or before date D?**

It stores raw historical facts and *derives* availability, rather than storing
a single lossy "release date" per card - so a reprint can never overwrite a
card's original date, regional differences stay expressible, and a pool can be
recomputed from first principles at any time.

## The model

```
Product (data/releases/products/<id>.json - one file per product)
├── id            unique slug ("absolute-powerforce"). Set-code prefixes are
│                 NOT unique (a main set, its Sneak Peek card, and its Special
│                 Edition share one prefix), so the slug is the key.
├── code          the printed set-code prefix (ABPF, JUMP, DT01, ...)
├── kind          booster / structure / starter / tin / promo-* / ...
├── dating        "product" (normal sets: printings share the product events)
│                 or "per-printing" (serial promo series: each printing dated
│                 individually; an event-less printing is deliberately undated
│                 and grants nothing - safe for unresearched reprints)
├── release_events[]
│   ├── territory   tcg-na | tcg-eu | tcg-oce | tcg (source didn't say) | ocg-*
│   ├── date        ISO date, padded to the 1st for coarse precision
│   ├── precision   day | month | year   (from SMW raw values, never timestamps)
│   ├── status      verified | reported | disputed (disputed REQUIRES dispute[])
│   ├── kind        retail | event | distribution-start | prerelease
│   └── sources[]   registry ids; every event is cited
└── printings[]
    ├── passcode    canonical EDOPro passcode (see identity below)
    ├── name        modern canonical name (validator cross-checks the pair)
    ├── numbers[]   printed card numbers (ABPF-EN001, ...)
    └── release_events[]  optional per-printing override / serial-promo dates
```

`data/releases/coverage.json` states which territory/date windows the dataset
claims to cover **completely**. A release-cutoff pool can only be materialised
when its cutoff falls inside a claimed window - missing coverage is an explicit
error, never a silently smaller pool.

## Derivation rules

1. **Earliest event wins.** A card's availability at a date is decided by the
   earliest applicable event across all of its printings. Extra printings only
   ever add (later) events - reprints cannot postdate a card.
2. **Availability kinds.** `retail`, `event`, and `distribution-start` events
   grant availability; `prerelease` (sneak-peek) events are recorded but do
   not count.
3. **Territory scoping.** A TCG pool defaults to *all* TCG territories:
   historically, a card released anywhere in the TCG was tournament-legal
   TCG-wide (Europe-only Retro Pack cards were legal at US events - this is
   why Edison needs no special case for them). An unspecified `tcg` event
   satisfies any TCG territory and vice versa. Pools that genuinely track one
   territory's availability narrow `cutoff.territories`.
4. **Uncertainty is never resolved silently.** Precision and recorded disputes
   widen an event's possible date range. A card is in a cutoff pool only if
   some event's whole range is on or before the cutoff; if its only candidate
   events *straddle* the cutoff, the card is AMBIGUOUS and materialisation
   refuses to proceed until a sourced `cutoff.include`/`exclude` entry
   resolves it (Edison has exactly three such resolutions, at the JUMP-EN038
   promo boundary).
5. **Product-level exceptions.** `cutoff.exclude_products` discounts a whole
   product's availability with one sourced, reasoned entry - for a format
   defined against one territory's street date (The Shining Darkness's EU
   release falls inside Edison's NA-anchored window) or product classes a
   format's definition omits (Duel Terminal machines). Cards remain in the
   pool when a non-excluded product also released them in time.

## Card identity in printings

Printings are stored under **canonical EDOPro passcodes** (BabelCDB is the
identity authority):

- an alias within the ±10 artwork window accrues to its base card and is
  emitted as a `variant_passcodes` entry when in-period;
- a far alias (Arkana Dark Magician, "name-treated-as" cards like A Legendary
  Ocean) is its own canonical card - exactly matching Project Ignis's GOAT
  whitelist conventions;
- a printing that cannot be matched to BabelCDB is *reported*, never guessed.

## Materialisation

```
python -m retroformats materialize [pool-id ...]
```

writes the derived card list into each release-cutoff pool file. The committed
list is a **reviewable projection, not data**: the validator recomputes it from
the release facts on every run and fails on drift
(`pool.materialization-drift`), on missing coverage (`pool.no-coverage`), and
on unresolved boundary ambiguity (`pool.cutoff-ambiguous`). `build` then turns
a materialised pool into an EDOPro `$whitelist` enforcing pool and banlist
together.

## Importer workflow

```
python -m retroformats.importers.fetch_release_sources --cache <dir>   # network
python -m retroformats.importers.tcg_releases \
    --cache <dir> --babelcdb <BabelCDB clone> --through 2010-12-31     # offline
python -m retroformats.importers.card_index --babelcdb <BabelCDB clone>
python -m retroformats materialize && python -m retroformats build
```

The fetch stage downloads the YGOPRODeck bulk dumps (their documented
single-request pattern) and enumerates products via Yugipedia's `ask` API
(five English-family release-date properties, 1 req/s per their policy).
The normalise stage is offline and deterministic; raw caches never enter git.
Extending coverage past 2010 is re-running with a later `--through`.

### Source priority / conflict policy

| authority | source | why |
|---|---|---|
| dates | Yugipedia set pages | the only machine-readable per-territory (NA/EU/Oceanic/Worldwide) dates, with explicit precision |
| printings | YGOPRODeck bulk dump | complete per-card printing rosters with numbers |
| identity | BabelCDB `cards.cdb` | EDOPro's own passcode/alias space |

When YGOPRODeck's single per-set date matches a Yugipedia event exactly it is
added as a corroborating source on that event; when it matches nothing it goes
to the **import report** (`data/imported/releases-report.json`), not into the
canonical data - it is region-inconsistent (verified: EU for some sets, NA for
others) and sometimes bakes in Sneak Peek dates. When two sources genuinely
dispute a date that matters, the event carries `status: disputed` with the
alternatives recorded, and the ambiguity rules above take over.

## Known limitations

- **Per-artwork printing dates are not resolved**: the YGOPRODeck dump ties
  printings to cards, not artworks, so a far-alias alternate art first printed
  before a cutoff enters a pool only via a sourced `cutoff.include` (none has
  been needed yet; the comparison diff would surface them).
- Regional *set contents* differences below the product level (a card present
  only in one territory's printing of the same product) are not modelled yet.
- Products Yugipedia doesn't date fall back to the YGOPRODeck date as an
  unspecified-`tcg` day-precision event; a few promo products carry placeholder
  dates upstream (the import report and cutoff-ambiguity checks are the nets).
- OCG release events are modelled (`ocg-*` territories) but not yet imported;
  OCG availability never grants TCG legality either way.
- Coverage currently ends 2010-12-31 (Edison's needs); later formats extend it
  by re-running the importer.
