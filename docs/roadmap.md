# Roadmap

Accuracy before breadth: a format is only "supported" when its data validates, its
sources are cited, and its generated assets are regression-tested. The order below
reflects that.

## Phase 1 — harden the two proof-of-concept formats

1. **Date the errata corpus.** All 211 imported errata records lack
   `date_effective` (the `erratum.undated` warnings). Research each card's errata
   date (Yugipedia card-errata pages are structured and citable), which
   (a) replaces GOAT's explicit include list with computed selection, and
   (b) automatically surfaces which pre-errata versions Edison needs
   (e.g. cards errata'd after 2010). Also classify each record properly
   (functional vs ruling) instead of the imported blanket `functional`.
2. **Cross-check the April 2005 banlist.** The GOAT banlist is currently derived from
   Ignis's whitelist counts. Transcribe the published April 2005 TCG list (Yugipedia
   `April 2005 Lists (TCG)`) with the existing importer, reconcile, upgrade
   `completeness` to `complete`/`verified`, and document any deliberate GOAT-community
   deviations if found.
3. **Verify March 2010 against the Konami archive snapshot** (Internet Archive was
   unreachable this session); upgrade the banlist to `verified`.
4. ~~**Materialise the Edison pool.**~~ **Done (2026-08-19).** `data/releases/`
   covers TCG 2002–2010 (369 products / 8,445 printings, Yugipedia per-territory
   dates + YGOPRODeck printings), Edison materialises to 3,673 cards with every
   boundary case explicitly resolved and sourced, the generated lflist is a full
   `$whitelist`, and regression tests lock cardinality + sixteen edge cases.
   See docs/releases.md. Follow-ups now tracked below (4a–4c).

   4a. **Upgrade release events from `reported` to `verified`** for the products
   that define format boundaries (ABPF, TSHD, DPKB, DPCT, the promo cutoffs) by
   citing period sources (archived Konami/UDE product pages) alongside Yugipedia.
   4b. **Per-artwork printing dates** (far-alias alternate arts like Arkana Dark
   Magician are currently absent from cutoff pools unless force-included; audit
   which mattered in-period and encode them).
   4c. **Duel Terminal ruling dossier**: the pool excludes DT01-machine-only cards
   per EdisonFormat.com's set list; collect period tournament-policy evidence
   (UDE/Konami floor rules) to upgrade that decision from community consensus to
   primary-sourced.
5. **Edison rules review.** Compare EdisonFormat.com's 13 rule differences against the
   ocgcore flag axes; decide whether the profile should add TCG-variant flags
   (`DUEL_TCG_FAST_EFFECT_IGNITION`, SEGOC flags, 6-step damage step) beyond plain
   MR1, with sources; record what the engine cannot reproduce in `known_gaps`.

## Phase 2 — framework completeness

6. **Deck-level validation tool**: check a `.ydk` against a format (pool + banlist +
   forbidden types + deck sizes) — gives players/tournament organisers a CLI check and
   gives tests a realistic fixture surface.
7. **cdb/script generation for `custom-script` errata**: when we need a historical
   card Ignis doesn't ship, generate `dist/databases/retro-<format>.cdb` rows
   (`alias` → modern, `ot=8`, our own reserved code range — pick one that cannot
   collide with 5047xxxxx/511YYYXXX/prerelease ranges and document it) plus script
   stubs, following the upstream blueprint in docs/research/ignis-goat.md.
8. **Ship as an EDOPro repo**: add a documented `user_configs.json` snippet +
   versioned release layout so `dist/` is consumable directly; test in a real client.
9. **CI**: GitHub Actions running validate + build --check + unittest (workflow file
   already included); add a link-checker for source URLs.
10. **Importer for Format Library formats list** (after maintainer contact): seed
    `formats/` skeletons for the ~90 catalogued formats with `implementation_status:
    missing`, so coverage is visible and contributors can pick tasks up.

## Phase 3 — more formats, by informativeness

11. A second whitelist-era format adjacent to GOAT (e.g. 2005-09) to prove banlist
    sharing and chronology links.
12. A Synchro-era chain (Tengu/Plant 2011) to exercise MR1-vs-MR2-era profile
    boundaries (TCG September 2011 list).
13. HAT (2014) — MR3, pool via releases; Dragon Ruler (2013) — errata-heavy.
14. Early-era formats (Yugi/Kaiba, Critter) — these stress the releases dataset
    (2002-2003) and pre-Advanced-format rules; expect new `known_gaps`.

## Upstream conversations worth having

- **Project Ignis**: the duplicated `511000868` line in GOAT.lflist.conf (cosmetic,
  but it makes the file's runtime hash differ from its entry set); whether they'd
  take an Edison whitelist/pre-errata contributions upstream; whether goat-entries
  conventions (5047xxxxx, ot=8) can be documented in the BabelCDB README.
- **EDOPro (edo9300)**: a mechanism for a repo/lflist to *suggest* duel flags & deck
  sizes for a list (today presets are compiled in; historical formats need manual
  host setup) — even an advisory `#rules:` comment convention would help lobbies.
- **Format Library (Daniel McNelis)**: API usage terms for bulk import; whether the
  Errata table is populated and could get a public route; Sets/Prints export.

## Engine-level regression testing (long-term)

ocgcore is scriptable headlessly (`OCG_CreateDuel` + Lua). A future `tests/engine/`
harness could replay scripted duel scenarios asserting era behaviours (ignition
priority windows, 2005 Cyber Jar resolution order, TER trap-monster absorption) —
the research notes identify exactly which flags/scripts encode each behaviour.
