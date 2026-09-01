# Data sources and provenance policy

## The rules

1. **Every factual record cites sources.** Each banlist, pool, rule profile, erratum,
   release, and format record carries a `sources` array of ids resolving into
   `data/sources.json` (or a format-local `sources.json`). The validator fails on
   unresolved references and on records with no sources.
2. **Pin what you read.** Repository sources record the git commit; wiki/API sources
   record the URL and retrieval date (and page/revision ids where available).
3. **Raw caches never enter git.** Importers read fetched files (API JSON, cloned
   repos) and write only the distilled canonical records. Re-running an importer
   against the same pinned source must be deterministic.
4. **AI output is not evidence.** Model-generated text is never recorded as a
   historical fact. Facts enter the datasets only via importers reading real sources
   or humans transcribing cited material. Where a summary sentence appears in a
   `notes` field, it describes the data, it does not source it.
5. **Mark what you don't know.** Unverified claims go to `notes`/`known_gaps`/roadmap
   as open questions. `completeness`/`implementation_status` fields say how much a
   record claims (`missing`/`stub`/`partial`/`complete`/`verified` — `verified`
   requires two independent sources or an executable test).

## Source tiers

| tier | examples | use |
|---|---|---|
| official | Konami F/L list pages (via Internet Archive), rulebooks | ground truth where reachable |
| wiki | Yugipedia (MediaWiki API) | primary transcription source; pages cite Konami originals |
| community-project | Project Ignis LFLists / BabelCDB / CardScripts | reference implementations; battle-tested but curated |
| community-site | Format Library, EdisonFormat.com | format definitions, dates, pools; cross-check where possible |
| repository/dataset | pinned git revisions of any of the above | machine imports |

Cross-checking across tiers upgrades confidence: the March 2010 banlist was
transcribed from Yugipedia and independently matched byte-for-byte against Format
Library's API before being marked `complete`.

## Surveyed sources (2026-08-19)

### Project Ignis repositories

- **LFLists** — current lists only (TCG/OCG/Traditional/World/Speed/Rush + GOAT).
  GOAT is the sole historical list and is hand-maintained (Rush/Speed whitelists are
  generated in BabelCDB CI; no GOAT generator exists upstream).
- **BabelCDB** — `cards.cdb` (canonical card identities), `goat-entries.cdb`
  (191 GOAT versions), `cards-unofficial.cdb` (incl. 67 "(Pre-Errata)" cards).
  Passcode policy documented in its README (511YYYXXX unofficial range, ±10 artwork
  aliases); the 5047xxxxx GOAT range is undocumented convention.
- **CardScripts** — `goat/`, `pre-errata/` script trees; `Duel.GoatConfirm` helper.
- **Distribution / DeltaBagooska** — how content reaches players (configs.json repos).

### Format Library (formatlibrary.com)

Open-source NX monorepo ([danielmcnelis/formatlibrary](https://github.com/danielmcnelis/formatlibrary)),
Express + Sequelize/Postgres. **The repo contains schema only — the live API is the
data source** (migrations are schema-only; the seed script creates no card data).
Verified endpoints:

- `GET /api/formats/` — ~90 format records (name, date, banlist name, category, era,
  event, description) — a candidate skeleton for our formats/ tree.
- `GET /api/banlists/:name?category=TCG` (e.g. `april-2005`) — full banlist; entries
  include the card's `artworkId` == passcode. Note: the sibling
  `/api/banlists/cards/:date` route does *not* dash-convert its parameter.
- `GET /api/cards?...` — filter DSL, ≤100/page; cards carry `konamiCode`, `ypdId`,
  `artworkId`, `tcgDate`, `ocgDate` (id-field equivalence verified for one card only —
  spot-check more before relying on it).
- Sets/Prints models carry `releaseDate`/`legalDate` — the natural source for
  `data/releases/` coverage.
- An `Errata` model exists (time-ranged card texts: `effectiveDate`/`expirationDate`)
  but has **no public GET route**; worth asking the maintainer about.
- Licensing: `package.json` says MIT but the repo has no LICENSE file, and there is no
  stated API usage policy. **Before any bulk import (~70 banlists, ~13k cards), contact
  the maintainer (Daniel McNelis) and agree on terms + rate limits.** Single-record
  probes for cross-checking are fine and were done respectfully (< 10 requests).

- Reliability note: Format Library's `previous`-status change markers are unreliable
  as a class. They disagreed with Yugipedia in 3 of 132 March-2010 entries and the
  current April-2005 response has six cards marked `previous: unlimited` where
  Yugipedia says `not yet released`. Use FL for *current-list membership*, not deltas;
  the canonical source records name the affected source snapshots.

### Yugipedia

MediaWiki API (`action=parse&prop=wikitext`) exposes `{{Limitation list}}` templates
with structured fields (`forbidden`/`limited`/`semi_limited`/`no_longer_on_list`,
`start_date`/`end_date`, `prev`/`next`) — machine-parseable without HTML scraping
(`retroformats/importers/yugipedia_banlist.py`). Pages cite Konami's original list
URLs (via Internet Archive). Be a good API citizen: cache fetches, identify requests,
low volume.

**Set pages (surveyed 2026-08-19, now the release-date authority):** Semantic
MediaWiki `action=ask` works, and set pages carry distinct `North American English
release date` / `European English release date` / `Oceanic` / `Worldwide` /
`English release date` properties. One `ask` query enumerates every TCG product in a
date window (384 for 2002–2010). **Parse dates from the SMW `raw` field
(`1/YYYY[/M[/D]]`) — precision is encoded there; the accompanying timestamp silently
pads to the 1st.** Set card lists (`Set Card Lists:<Set> (TCG-XX)`) are
semicolon-delimited `{{Set list}}` wikitext; card-number pages redirect to card
pages (used to spot-verify printings). The published API policy (1 req/s, descriptive
UA with contact, ~30-day caching, `recentchanges` for sync) explicitly names card
database building as an anticipated use.

### YGOPRODeck (db.ygoprodeck.com, surveyed 2026-08-19)

`cardinfo.php?misc=yes` with zero filters is their documented single-request bulk
download (14,516 cards, ~25 MB); `cardsets.php` lists all sets. **Printings authority
only.** Verified pitfalls: the per-set `tcg_date` is region-inconsistent (EU for
Absolute Powerforce/The Shining Darkness, NA for Generation Force/Duelist Revolution)
and `misc_info.tcg_date` sometimes bakes in Sneak Peek dates; promo sets can carry
`YYYY-MM-01`/`YYYY-01-01` placeholders; the top-level card `id` is not always the
canonical printed passcode (match against the full `card_images[].id` list); set-code
prefixes collide across 142 groups (join by `set_name`). Its `misc_info.formats`
Edison tag was used as a comparison target — with adjudicated false negatives (15
confirmed pre-cutoff cards missing) and internal inconsistency on Duel Terminal
cards.

### Other structured sources (surveyed, not currently ingested)

- **YGOJSON** (iconmaster5326/YGOJSON, MIT, bulk ZIPs): the only other source with
  explicit `na`/`eu` set dates; snapshot was ~4 months stale at survey time. Good
  future cross-check.
- **YGOResources** (db.ygoresources.com): mirrors Konami's own DB; per-locale
  `prints[]` with dates per card. Etiquette requires incremental use (revision
  manifest); best for adjudicating individual conflicts.
- **yaml-yugi** (DawnbrandBots, git, daily): per-locale set membership per card, no
  dates; `yaml-yugi-limit-regulation` holds banlist history (TCG lists carry
  EMEA effective dates — mind NA divergence).
- **Konami DB** (db.yugioh-card.com): authoritative but HTML-only behind a WAF, one
  date per locale with no NA/EU split; manual spot-checks only.
- **Community Edison whitelists** (comparison targets, cached in research notes):
  termitaklk's hand-maintained pre-errata whitelist (independent lineage; agreed with
  our derivation on all 15 adjudicated keepers) and SantiagoRivera92/TimeWizard
  (generated from YGOPRODeck set dates; includes all Duel Terminal cards).

### EdisonFormat.com

Prose site; used as the source for Edison's definition (name origin, 2010-03-01 →
2010-05-10 bounds, legal-set table, promo cutoffs, 13 rule differences). Claims are
quoted with URLs in `formats/2010-03-edison/` records. Internal inconsistency worth
knowing: its legal-sets table omits Duelist Pack Collection Tin 2010 (Starlight Road)
although its own linked card pool includes the card.

### Period tournament-policy documents (surveyed 2026-08-20)

Recovered via the Internet Archive during the release-data certification pass
(registry ids `konami-product-pages-2010-archive`, `sjc-edison-2010-faq`,
`ude-tournament-policy-appendix-a`, `konami-event-faqs-2009-2010`):

- **UDE Tournament Appendix A** (Nov 2005 / Apr 2006 / Aug 2008 revisions):
  worldwide-simultaneous TCG legality, OCG/Asian-English ban, foreign-language
  allowance, the dated Currently-Legal product/promo lists (including
  Europe-only products and "DTP1 (reprints)").
- **Konami premier-event FAQs 2009-2010** (US Nationals 2009, Regionals,
  2010 US WCQ): the Konami-era legality mechanism - per-event dated lists; the
  Duel Terminal machine-exclusive prohibition; Europe-only video-game promos
  explicitly legal at US events.
- **Archived 2010 Konami product pages** (US + UK): explicit "Launch Date /
  Konami Tournament Legal Date" fields for every Edison boundary product, plus
  the Sneak Peek event pages.
- **The 75th SJC (Edison) FAQ** (captured 2010-04-11): the event's own card
  pool, promo cutoffs, and illegal-DT list.

These are the project's model for what `verified` means: period, primary,
archived, and cited. Local copies live in the (uncommitted) research cache;
each registry entry records the capture URLs.

### Internet Archive

Konami's own 2010 list page is archived and cited (see `konami-limited-2010-03`).
Direct entry-by-entry verification against the archive snapshot is a roadmap item —
archive.org was not reachable from the environment this session.
