# Roadmap

Accuracy before breadth: a format is only "supported" when its data validates, its
sources are cited, and its generated assets are regression-tested. The order below
reflects that.

## Phase 1 — harden the two proof-of-concept formats

1. ~~**Date the errata corpus.**~~ **Done (2026-08-20).** The corpus is now a
   reviewed, source-backed, date-aware dataset: 296 records (211 imported + 85
   found by sweeping the Edison-legal pool), every one reviewed, classified
   155 ruling / 120 functional / 21 cosmetic, with 113 exact dates, 58 bounded
   chronologies and 125 explicitly unresolved. GOAT's 211-entry include list is
   gone (one sourced parity policy, parity unchanged) and Edison computes 72
   historical implementations from evidence alone. See docs/errata.md.
   Follow-ups below (1a-1e).

   1a. **Chronology for the undated era rulings.** 125 records are unresolved,
   almost all undated era *rulings* carried by upstream GOAT scripts —
   damage-step activation windows, miss-timing registration, trigger
   registration. Konami never announced these per card, so they need period
   rulings documents (UDE Judge's List archives, Metagame.com judge columns,
   per-set rulings PDFs). Each one resolved shrinks Edison's
   `unresolved_policy` fallback.
   1b. **Close the search-verification interval.** The old state is attested
   through 2011-02-02 and the modern policy from 2019-04-03; no announcement of
   the change was found. Narrowing this would firm up a large group of records
   at once (both GOAT and Edison already sit determinately in the old era).
   1c. **The 48 acknowledged implementation gaps** — period behaviours nothing
   upstream reproduces. Each is a candidate for roadmap item 7 (`custom-script`
   generation) once a reserved passcode range is chosen.
   1d. **Contribute back upstream.** 21 cards where our chronology says GOAT
   should use a historical version but Project Ignis's list leaves them modern
   (`format.parity-omits-historical`), plus the cases where its variant is
   behaviourally identical to the modern card (`upstream-variant-cosmetic`).

   1e. **Card identity: TCG-versus-OCG entries.** Mind Master (96782886) is in
   the Edison pool but BabelCDB scopes it OCG-only (`ot=1`) and ships the TCG
   version as a *separate* entry (96782896, `ot=2`, aliased). Our release data
   maps its TDGS-EN016 printing to the canonical code, so the pool references
   a card EDOPro would reject in an official-cards room. This is a card-identity
   question, not errata chronology: it needs a general rule for choosing the
   region-correct implementation of a canonical card.
   `tests/test_repo_data.py::test_pool_cards_are_tcg_scoped_in_the_card_database`
   pins the invariant with this single documented exception.
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

   4a. ~~Upgrade boundary release events to `verified`~~ **Done (2026-08-20).**
   All five Edison boundary products (plus the TSHD Sneak Peek and both new EU
   dates) are now curated records verified against archived 2010 Konami product
   pages with explicit Tournament Legal Date fields.
   4b. **Per-artwork printing dates** (far-alias alternate arts like Arkana Dark
   Magician are currently absent from cutoff pools unless force-included; audit
   which mattered in-period and encode them).
   4c. ~~Duel Terminal ruling dossier~~ **Done (2026-08-20).** Period policy
   recovered: DT machine exclusives were illegal in sanctioned play (2009-2010
   event FAQs, Konami's 2010-03-19 article, the June 2010 WCQ FAQ's card list);
   the pool exclusion is now primary-sourced.
   4d. **Coverage certification shipped (2026-08-20):** the gap ledger
   (data/releases/gaps.json) makes "complete" coverage an earned invariant -
   all 45 importer-detected anomalies audited (1 roster recovered and imported,
   the rest proven harmless with evidence, mechanically recomputed where
   checkable). Future importer runs that surface new anomalies fail validation
   until the ledger accounts for them.
5. ~~**Edison rules review.**~~ **Done (2026-08-21).** Every GOAT-composite flag was
   independently checked against period Konami rulebooks (2008/2010/2011 editions,
   bracketing Edison) rather than assumed from GOAT or from EdisonFormat.com's naming.
   Two flags are confirmed necessary and added, each backed by a period source and an
   engine test that fails without it: `DUEL_TCG_FAST_EFFECT_IGNITION` (the TCG's broader
   ignition-priority condition lasted until 2012, two years after Edison) and
   `DUEL_0_ATK_DESTROYED` (the 0-ATK tie exception wasn't added until May 2011). Four
   more were confirmed *not* needed — the modern ocgcore default already matches 2010
   TCG play, so adding them would have imported behaviour Edison never had:
   `DUEL_6_STEP_BATLLE_STEP`/`DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP`,
   `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET`, `DUEL_STORE_ATTACK_REPLAYS`. The profile
   (`data/rule-profiles/tcg-mr1-edison.json`) is now a custom 8-flag combination rather
   than a bare `DUEL_MODE_MR1` alias. See `docs/research/edison-rules.md` for the full
   evidence table and the adversarial review. Follow-up below (5a).

   5a. **SEGOC ordering remains unresolved.** The period-primary Official Rulebook
   (stable 2008-2011) describes a simple two-tier simultaneous-trigger order with no
   mandatory/optional split and no trigger-order tiebreak, directly contradicting
   EdisonFormat.com's claimed four-tier structure, which is traceable only to a 2012
   forum thread (not a period document). `DUEL_TCG_SEGOC_NONPUBLIC` and
   `DUEL_TCG_SEGOC_FIRSTTRIGGER` are left out of the profile pending better evidence —
   candidate lead: an unlocated Konami rulebook edition between v8.0 (Nov 2011) and v10
   (2017) that may be where the stricter structure actually entered print. Three smaller
   flags (`DUEL_USE_TRAPS_IN_NEW_CHAIN`, `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE`,
   `DUEL_CAN_REPOS_IF_NON_SUMPLAYER`) are similarly left unresolved in `known_gaps` for
   lack of any period source in either direction.

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
- **Format Library (Daniel McNelis)**: API usage terms for bulk import; Sets/Prints
  export. On errata specifically, the question is now sharper than "is the table
  populated": the repository's `erratas` table has no reader or writer anywhere in
  the codebase, while the period card texts that DO exist live per printing in
  `Print.description` and are deliberately excluded from the card API response.
  Worth asking whether those per-print texts could be exposed, and what the
  unused Errata model's `effectiveDate`/`expirationDate` were intended to mean.
  Details in `data/sources.json` (`formatlibrary-source`).

## Engine-level regression testing

~~long-term~~ **Shipped (2026-08-20).** `tests/engine/` drives the real ocgcore
(OCG API 11) through ctypes with the pinned BabelCDB card data and CardScripts,
building board states with the core's own `Debug.*` API. Eight tests assert era
*gameplay*, each pairing a historical implementation against the modern one:
Sangan's failed-search Deck reveal, Sangan's and Rescue Cat's post-errata hard
once-per-turn, and Imperial Order's optional-versus-forced maintenance. See
docs/engine-testing.md.

Next steps, in value order:

- **Coverage.** Four implementations across three records are behaviourally
  tested; 234 reuse upstream implementations that are not. Prioritise the cards
  Edison actually substitutes.
- **Untested behaviour classes.** Damage-step activation legality (the largest
  single group of unresolved era rulings — a scenario reaching the Battle Phase
  would let those records be verified as well as dated), equip survival when
  the target leaves, and miss-timing/`EFFECT_FLAG_DELAY` trigger registration.
- **CI.** The engine tests skip without `RETROFORMATS_OCGCORE`, keeping the main
  suite stdlib-only. A separate CI job could fetch DeltaBagooska's
  `libocgcore.so` and the pinned checkouts to run them on Linux.
- **A 64-bit Windows core.** DeltaBagooska ships only a 32-bit `ocgcore.dll`, so
  Windows contributors must use WSL today.
