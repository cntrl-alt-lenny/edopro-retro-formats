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
| Card pool | **complete** — 1700 canonical cards imported from Project Ignis's community-vetted whitelist | **verified** — 3,673 cards *derived from release history* under certified coverage, cross-checked against two independent community pools, with the boundary dates, Duel Terminal exclusion, and promo cutoff corroborated by archived period Konami documents (including the event's own FAQ) |
| Rule profile | `DUEL_MODE_GOAT` (17 individual ocgcore flags, verified against `ocgapi_constants.h`) | **partial** — a custom MR1-era 7-flag profile (not the bare `DUEL_MODE_MR1` preset), including the researched `DUEL_0_ATK_DESTROYED` addition; Ignition Effect Priority is represented by a documented approximation because no existing ocgcore flag reproduces it exactly; SEGOC (`DUEL_TCG_SEGOC_*`) and several smaller flag questions remain explicitly unresolved rather than guessed — see [docs/research/edison-rules.md](docs/research/edison-rules.md) |
| Errata | **complete** — every substitution derived from one sourced parity policy instead of a 211-entry hand list; still entry-for-entry identical to the reference | **partial** — 72 historical implementations *computed* from evidence, with no hand-written Edison errata list |
| Generated lflist | **semantically identical to Project Ignis's `GOAT.lflist.conf`** — same 1704 code/count entries, same EDOPro banlist hash (`0x28e9fc02`) — regenerated from canonical data | full `$whitelist` enforcing pool + banlist together (post-Edison cards are rejected) |

Behind both formats' card *behaviour* sits the second backbone dataset:
**`data/errata/`** — 296 per-card historical-behaviour records, each reviewed
rather than imported, distinguishing genuine text errata (functional) from
period *rulings*, from pure wording modernisation (cosmetic). The canonical
errata corpus is now fully represented in v2: all 296 records are in the **v2
historical-event DAG** (180 as flattened
single-event sugar, 116 as the full `events{}`/`ordering`/`states[]` shape) —
an explicit graph of dated/undated historical events with a provable
partial order, replacing the old assumption that `changes[]`'s array
position meant anything. Insect Imitation and Last Will were independently
adjudicated and migrated to v2. The 47 already-researched unordered records
were migrated as separate events with no ordering edge where the evidence
does not establish one; no new research or architecture work was needed.
See
[docs/research/erratum-state-model-v2.md](docs/research/erratum-state-model-v2.md)
for the model and [docs/roadmap.md](docs/roadmap.md) for current status and
the remaining manual cases. Chronology carries its own uncertainty across
both shapes:
some changes/events are exactly dated, some hold bounded "old attested
through A, new attested from B" intervals, and some are explicitly
unresolved. **Selection never silently guesses** — absent an explicit,
sourced format policy, a snapshot inside an unresolved transition interval
blocks selection/build outright; a format *may* adjudicate such
uncertainty explicitly through its own sourced `errata_overrides` policy
(Edison's, for instance, documents a conservative "keep modern" default),
and every card the policy touches is named individually by the validator
and `report`, never silently absorbed. Applicability is *computed*:
Edison's historical implementations fall out of the evidence with no
hand-written list, and GOAT's 211-entry list was replaced by a single
sourced statement while staying byte-identical to the Project Ignis
reference. See [docs/errata.md](docs/errata.md).

Behind the Edison pool sits the project's first shared backbone dataset:
**`data/releases/`** — 370 TCG products (2002–2010) with per-territory,
precision-aware, cited release events and 8,446 printings, from which any
release-cutoff pool is derived and continuously re-verified. Coverage
completeness is an **earned invariant**: a gap ledger accounts for every
importer-detected anomaly, unresolved gaps block pool materialisation, and
harmlessness claims are mechanically recomputed — so when the project claims
complete coverage for a date and territory, the tooling can defend it. Pools
additionally declare a `legality_basis` separating physical availability from
tournament-legality policy (the Edison boundary dates, the Duel Terminal
exclusion, and Europe-only legality are corroborated by archived period Konami
and UDE documents). See [docs/releases.md](docs/releases.md).

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
$ python3 -m retroformats report        # per-format status, errata certification, coverage
$ python3 -m retroformats report -v     # ...plus which cards each format substitutes
$ python3 -m unittest discover -t . -s tests -v   # schema, runtime (v1+v2), build, reference-parity,
                                                   # and migration regressions
```

## Repository layout

```
schemas/          JSON Schemas documenting every record type
data/
  banlists/       one file per historical F/L list snapshot (region + effective date)
  pools/          card-pool definitions (extensional lists or release-cutoff rules)
  rule-profiles/  reusable rules-era profiles mapped to ocgcore DUEL_* flags
  errata/         per-card historical-behaviour records (one file per card):
                  kinds, precision-aware chronology, per-version implementations
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
   differently (see [docs/format-schema.md](docs/format-schema.md)). Only functional
   and ruling changes can substitute a historical card; a rewording never does.
6. **Fail safe on uncertainty.** When a format's snapshot falls inside an unresolved
   transition interval, selection refuses rather than guessing old or new. A format
   may state one sourced policy for such cases, and every card it touches is named.
7. **Tested means executed.** `implementation.tested` is set only where a headless
   ocgcore test demonstrates the historical behaviour (see
   [docs/engine-testing.md](docs/engine-testing.md)) — never because a script exists.
4. **Reuse vetted implementations.** Where Project Ignis already maintains a historical
   card implementation, we reference it (`reuse-upstream`) instead of forking it.
5. **Regression-test against references.** The generated GOAT list is asserted, in CI,
   to remain semantically identical to Project Ignis's — the community's
   battle-tested implementation is our baseline.

## Development status

Working end-to-end with two certified backbone datasets (releases, errata) and
two proof formats (GOAT, Edison) — both remain the project's end-to-end
regression targets as the errata model evolves underneath them. The
errata-model migration to the v2 historical-event DAG covers **all 296
records**: the 247-record semantics-preserving pass, the subsequent 47
already-researched unordered-event migration, and the later adjudications of
Insect Imitation and Last Will. This completes the representation migration,
but does not claim that every historical chronology or implementation is
resolved, every warning is eliminated, or every erratum is perfectly
reproduced (see
[docs/research/erratum-state-model-v2.md](docs/research/erratum-state-model-v2.md)
and [docs/roadmap.md](docs/roadmap.md)). The card-index importer retains v1
support for historical fixtures and backwards compatibility. See
[docs/roadmap.md](docs/roadmap.md) for the full prioritised next-steps list
(the April 2005 banlist cross-check, broader behavioural test coverage, more
formats, and unresolved historical implementation gaps).

## License

Code and original documentation: [MIT](LICENSE). Card names, card text, and game data
are © Konami and appear here as factual references for preservation and
interoperability. Imported data retains attribution to its source project (Project
Ignis, Yugipedia, Format Library, EdisonFormat.com) in `data/sources.json` and in each
record's provenance fields.
