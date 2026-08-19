# edopro-retro-formats

**A source-backed historical Yu-Gi-Oh! preservation framework for [EDOPro](https://github.com/edo9300/edopro).**

The goal: reproduce formats from across the game's history — Goat, Edison, Tengu, HAT,
Dragon Ruler, and eventually far more obscure eras like Yugi/Kaiba or Critter — inside
EDOPro with the correct card pool, the correct Forbidden/Limited list, period-correct
card behaviour, and period-appropriate game rules. Not as a pile of hand-maintained
config files, but as a **framework**: canonical, cited data in; validated,
EDOPro-consumable assets out.

## Why a framework?

Historical formats keep being rebuilt by hand, one lflist at a time, with no shared
notion of *where a fact came from* or *whether it is still correct*. This repository
treats a format the way an archivist would:

- **Canonical intermediate representation.** A format is a small record tying together
  shared datasets: a banlist snapshot, a card-pool definition, a rule profile, and a set
  of card-behaviour overrides (errata). Shared facts are stored exactly once — the
  April 2005 banlist is one file, no matter how many formats reference it.
- **Provenance everywhere.** Every factual record cites sources from a registry
  (Konami lists via archives, Yugipedia, Project Ignis data at pinned git revisions,
  Format Library's API, EdisonFormat.com). Claims we could not source are marked as
  open questions, not silently invented. AI-generated text is never treated as
  historical evidence.
- **Generated, never hand-edited output.** `dist/` (EDOPro lflists, later cdb/scripts)
  is built deterministically from the canonical data. CI fails if `dist/` drifts.
- **Validation before breadth.** A card released after a format's cutoff must be
  rejected; a limited card must enforce its count; chronology must be consistent;
  every source reference must resolve. Accuracy over claiming hundreds of formats.

## Proof of concept status (what works today)

Two fixture formats exercise the whole pipeline end-to-end:

| | GOAT (`2005-04-goat`) | Edison (`2010-03-edison`) |
|---|---|---|
| Banlist | derived from Project Ignis's GOAT whitelist (cross-check vs the published April 2005 list still TODO) | **complete** — March 2010 TCG list transcribed from Yugipedia (which cites Konami's original), independently cross-checked against Format Library's API (exact match) |
| Card pool | **complete** — 1700 canonical cards imported from Project Ignis's community-vetted whitelist | **verified** — 3,673 cards *derived from release history* (everything TCG-released ≤ 2010-05-10 in any territory, with every boundary case explicitly resolved and sourced), cross-checked against two independent community pools |
| Rule profile | `DUEL_MODE_GOAT` (17 individual ocgcore flags, verified against `ocgapi_constants.h`) | `DUEL_MODE_MR1` baseline (open question: TCG-variant flags) |
| Errata | 211 historical card versions mapped to Project Ignis's `goat-entries.cdb` / `cards-unofficial.cdb` implementations | recorded as missing (dating the errata corpus is the next research task) |
| Generated lflist | **semantically identical to Project Ignis's `GOAT.lflist.conf`** — same 1704 code/count entries, same EDOPro banlist hash (`0x28e9fc02`) — regenerated from canonical data | full `$whitelist` enforcing pool + banlist together (post-Edison cards are rejected) |

Behind the Edison pool sits the project's first shared backbone dataset:
**`data/releases/`** — 369 TCG products (2002–2010) with per-territory,
precision-aware, cited release events and 8,445 printings, from which any
release-cutoff pool is derived and continuously re-verified. Adding release
coverage is how future formats get their pools for free; see
[docs/releases.md](docs/releases.md).

The key architectural point: **neither format is special**. GOAT is an import of an
existing reference implementation; Edison is built from primary-ish sources. A future
`1999-05-yugi-kaiba` or `2011-09-tengu` uses exactly the same records and tooling.

Run it yourself (Python 3.10+, standard library only — no installs; CI tests the
3.10 floor and the current release. Older interpreters may happen to work — macOS's
system 3.9 does today — but are not supported targets):

```console
$ python3 -m retroformats validate      # semantic checks over all canonical data
$ python3 -m retroformats build         # regenerate dist/ deterministically
$ python3 -m retroformats materialize   # derive release-cutoff pools from data/releases/
$ python3 -m retroformats report        # per-format status + release-data coverage
$ python3 -m unittest discover -t . -s tests   # 101 tests incl. the Ignis-parity and Edison regressions
```

## Repository layout

```
schemas/          JSON Schemas documenting every record type
data/
  banlists/       one file per historical F/L list snapshot (region + effective date)
  pools/          card-pool definitions (extensional lists or release-cutoff rules)
  rule-profiles/  reusable rules-era profiles mapped to ocgcore DUEL_* flags
  errata/         per-card historical-behaviour records (one file per card)
  releases/       per-product release events + printings (feeds cutoff pools)
  cards/          generated card index (passcode<->name/alias ground truth)
  sources.json    the provenance registry every record cites into
formats/<id>/     format records: format.json + notes.md (id = yyyy-mm-slug)
retroformats/     the toolchain (validate, build, importers) — pure stdlib Python
dist/             generated EDOPro assets (committed, reproducible, never hand-edited)
tests/            unit + integration tests, incl. vendored reference fixtures
docs/             architecture, EDOPro research, data-source policy, roadmap
```

## How EDOPro integration works

Verified against the EDOPro/ocgcore source (all citations in
[docs/edopro-research.md](docs/edopro-research.md)):

- **Banlists**: EDOPro loads every `*.conf` from `./lflists/` and from configured git
  repositories (`lflist_path`). Lists are identified network-wide by an
  order-independent hash of their `(code, count)` entries — so a regenerated list with
  identical entries is interoperable with the original. `$whitelist` lists ban
  everything not listed, which is how closed historical pools are enforced.
- **Historical card behaviour**: EDOPro requests the script `c<code>.lua` per card
  code, and cdb rows carry an `alias` linking variant codes to the modern card.
  Project Ignis already ships GOAT-era and pre-errata card versions under dedicated
  codes (`goat-entries.cdb`, `cards-unofficial.cdb`, `script/goat/`,
  `script/pre-errata/`); our errata records reference those implementations rather
  than duplicating them, and our generated whitelists substitute the historical code
  for the modern one (exactly as the upstream GOAT list does).
- **Rules**: ocgcore exposes individual `DUEL_*` behaviour flags (64-bit) and composite
  presets (`DUEL_MODE_GOAT`, `DUEL_MODE_MR1`, …). Rule profiles map each era to a flag
  set. Limitation: presets are compiled into the client — a data repo cannot add one,
  so hosts select the preset (or custom flags) manually; this is documented per format.
- **Distribution**: this repository is shaped so `dist/` can be consumed as an EDOPro
  repository entry (`lflist_path: "dist/lflists"`) via `config/user_configs.json`.
  Historical card data/scripts arrive through Project Ignis's own repos today.

## Accuracy philosophy

1. **Cite or mark open.** Every banlist entry, date, and behavioural claim traces to
   the source registry (`data/sources.json`). Unverifiable claims live in notes and the
   roadmap as open questions.
2. **Prefer structured sources.** Git repositories at pinned revisions, MediaWiki APIs,
   Format Library's JSON API — HTML scraping only as a last resort, cached and never
   committed.
3. **Distinguish kinds of difference.** Cosmetic text modernisation, functional errata,
   changed rulings, and rules-era differences are different things and are modelled
   differently (see [docs/format-schema.md](docs/format-schema.md)).
4. **Reuse vetted implementations.** Where Project Ignis already maintains a historical
   card implementation, we reference it (`reuse-upstream`) instead of forking it.
5. **Regression-test against references.** The generated GOAT list is asserted, in CI,
   to remain semantically identical to Project Ignis's — the community's
   battle-tested implementation is our baseline.

## Development status

Early skeleton, working end-to-end. See [docs/roadmap.md](docs/roadmap.md) for the
prioritised next steps (dating the errata corpus, release-date coverage to materialise
cutoff pools, cross-checking the April 2005 list, more formats).

## License

Code and original documentation: [MIT](LICENSE). Card names, card text, and game data
are © Konami and appear here as factual references for preservation and
interoperability. Imported data retains attribution to its source project (Project
Ignis, Yugipedia, Format Library, EdisonFormat.com) in `data/sources.json` and in each
record's provenance fields.
