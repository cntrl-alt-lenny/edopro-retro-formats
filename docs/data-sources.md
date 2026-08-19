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

- Reliability note: Format Library's `previous`-status change markers disagreed with
  Yugipedia in 3 of 132 March-2010 entries (adjudicated via the September 2009 page —
  Yugipedia was right each time). Use FL for *current-list membership*, not deltas.

### Yugipedia

MediaWiki API (`action=parse&prop=wikitext`) exposes `{{Limitation list}}` templates
with structured fields (`forbidden`/`limited`/`semi_limited`/`no_longer_on_list`,
`start_date`/`end_date`, `prev`/`next`) — machine-parseable without HTML scraping
(`retroformats/importers/yugipedia_banlist.py`). Pages cite Konami's original list
URLs (via Internet Archive). Be a good API citizen: cache fetches, identify requests,
low volume.

### EdisonFormat.com

Prose site; used as the source for Edison's definition (name origin, 2010-03-01 →
2010-05-10 bounds, legal-set table, promo cutoffs, 13 rule differences). Claims are
quoted with URLs in `formats/2010-03-edison/` records. Internal inconsistency worth
knowing: its legal-sets table omits Duelist Pack Collection Tin 2010 (Starlight Road)
although its own linked card pool includes the card.

### Internet Archive

Konami's own 2010 list page is archived and cited (see `konami-limited-2010-03`).
Direct entry-by-entry verification against the archive snapshot is a roadmap item —
archive.org was not reachable from the environment this session.
