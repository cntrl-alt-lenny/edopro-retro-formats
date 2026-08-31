# Architecture

## The pipeline

```
external sources                canonical data                    generated output
────────────────                ──────────────                    ────────────────
ProjectIgnis/LFLists   ─┐
ProjectIgnis/BabelCDB  ─┤ importers   data/banlists/*.json  ─┐
Yugipedia (MediaWiki)  ─┼──────────►  data/pools/*.json      │ build    dist/lflists/*.lflist.conf
Format Library API     ─┤             data/rule-profiles/    ├────────► dist/databases/   (future)
EdisonFormat.com       ─┘             data/errata/*.json     │          dist/scripts/     (future)
                                      data/releases/         │
        every record cites ──────►    data/sources.json     ─┘
                                      formats/<id>/format.json
                                          │
                                          ▼
                                      validator (referential integrity, chronology,
                                      card identity, provenance, pool/banlist coherence)
```

Three layers, with strict rules about what may flow between them:

1. **Importers** (`retroformats/importers/`) read external sources and write canonical
   records, stamping the exact revision consulted (git commit, API URL + date) into
   provenance fields. Importers must be re-runnable and deterministic for a pinned
   source. Raw downloads are caches and never enter git.
2. **Canonical data** (`data/`, `formats/`) is the single source of truth. It references
   cards by their **modern canonical passcode** plus name (redundant on purpose — the
   validator cross-checks the pair against the generated card index, so a typo in
   either field is caught). Implementation details like pre-errata card codes never
   appear in banlists or pools; they live in the errata table.
3. **Build** (`retroformats/build.py`, `lflist.py`) turns canonical data into EDOPro
   assets deterministically: fixed section order, passcode-sorted entries, no
   timestamps. `dist/` is committed so the repo is directly consumable, and CI fails
   if a rebuild changes it (`python -m retroformats build --check`).

## The record types

| record | file | keyed by | shared? |
|---|---|---|---|
| banlist snapshot | `data/banlists/<region>/<yyyy-mm>.json` | region + effective date | yes — many formats can point at one list |
| card pool | `data/pools/*.json` | pool id | yes |
| rule profile | `data/rule-profiles/*.json` | profile id | yes — one profile serves every format in its era |
| erratum | `data/errata/<card>.json` | modern card | global — applicability per format is *computed* |
| product release | `data/releases/products/<id>.json` | product slug (set-code prefixes are not unique) | global — one dataset serves every cutoff pool; `curated` records survive re-imports |
| release coverage | `data/releases/coverage.json` | — | gates which cutoffs are materialisable |
| gap ledger | `data/releases/gaps.json` | gap id | certification: unresolved gaps block coverage; resolutions are evidence-backed and mechanically recomputed where checkable |
| format | `formats/<id>/format.json` | `yyyy-mm-slug` | ties the above together |
| sources | `data/sources.json` (+ per-format `sources.json`) | source id | global registry + local extensions |

Design rules that keep formats cheap to add:

- **A format is mostly references.** `2010-03-edison` contains ~40 lines of JSON: the
  period, pointers to `tcg-2010-03` / `pool-edison-2010` / `rules-tcg-mr1-edison`,
  status flags, and sources. Adding `2010-09-...` later reuses the same rule profile
  and much of the same infrastructure.
- **Nothing is format-specific unless it must be.** Errata applicability is computed
  per record from each change's `effective` chronology vs the format's snapshot date
  (see [errata.md](errata.md)). A format states standing policy rather than
  hand-listing cards: `reference_parity` (GOAT — substitute whatever the reproduced
  reference substitutes) or `unresolved_policy` (Edison — what to do when chronology
  is genuinely ambiguous). Per-card `include`/`exclude` remain available as
  adjudications of last resort, reported by the validator when they agree or disagree
  with computed selection.
- **Two pool representations.** *Extensional* (explicit passcode list — used when a
  vetted external definition exists, like Ignis's GOAT whitelist) and *release-cutoff*
  (a rule — "everything TCG-released ≤ 2010-05-10" — plus sourced exceptions).
  `python -m retroformats materialize` derives a cutoff pool's card list from
  `data/releases/` and writes it into the pool file as a **reviewable projection**;
  the validator recomputes it on every run and fails on drift, missing coverage,
  or boundary dates too imprecise to call (which must be resolved by explicit,
  sourced include/exclude entries — see [releases.md](releases.md)). Edison is
  built this way end-to-end.

## Card identity model

This mirrors how EDOPro/ocgcore actually work (citations in `edopro-research.md`):

- A **canonical card** is its modern passcode (`cards.cdb` row with `alias = 0`).
- **Artwork variants** are passcodes whose cdb `alias` points at the base within ±10
  (`CARD_ARTWORK_VERSIONS_OFFSET`). EDOPro treats them as the same functional card.
  Pools record them as `variant_passcodes` so generated whitelists can reproduce
  reference lists code-for-code.
- **Historical implementations** (pre-errata / era-behaviour versions) are separate
  cdb rows with far-away codes, `alias` → modern code, `ot = 8` (`SCOPE_ILLEGAL`), and
  their own Lua script. Upstream conventions: `504700000+` for `goat-entries.cdb`
  "(GOAT)" cards, `511YYYXXX` or `modern+10` for `cards-unofficial.cdb` "(Pre-Errata)"
  cards. Our erratum records point at these (`strategy: reuse-upstream`) or, later, at
  our own (`custom-script`).
- **This project's own reserved passcode range**, for `custom-script` records
  roadmap item 7 will generate: `600000000`–`699999999` (`RESERVED_PASSCODE_RANGE`,
  `retroformats/model.py`), chosen and proven collision-free in round 9. Every
  BabelCDB `*.cdb` file at the pinned `ignis-babelcdb` revision was surveyed
  (24,702 unique passcodes total, 301–810000114) — every other hundred-million
  decade has at least one occupied code; this one has none. It also clears every
  *documented* upstream convention (not just observed occupancy), per BabelCDB's
  own `README.md` at that revision: prerelease OCG/TCG `10ZZYYXXX`
  (100000000–109999999), Rush Duel `160ZYYXXX` (160000000–169999999), Speed Duel
  `30ZYYYXXX` (300000000–309999999), and the unofficial-cards reorganisation
  target `511YYYXXX` (511000000–511999999) — none of which touch the 6xx range.
  Real official Konami passcodes are 8 digits (`cards.cdb`'s own observed max is
  99995595) and so can never reach 9-digit territory at all. `retroformats/validate.py`
  rejects any canonical passcode reference inside this range today
  (`card.reserved-passcode-collision`) — nothing may use it until item 7's
  generation exists and deliberately does.
- The **card index** (`data/cards/index.json`) is generated from BabelCDB for exactly
  the passcodes this repo references, so validation is self-contained without
  shipping a full card database.

## The whitelist build algorithm

For a format with a materialised pool (extensional, or release-cutoff once
`materialize` has run — both GOAT and Edison qualify today), `retroformats/lflist.py`:

1. maps banlist statuses onto pool cards (`forbidden`→0, `limited`→1,
   `semilimited`→2, unlisted→3);
2. selects applicable errata via each record's fail-safe computed selection
   (`select_applicable_errata` in `errata.md`) — chronology vs. the format's snapshot,
   the format's `reference_parity`/`unresolved_policy` standing policy, and any
   per-card `include`/`exclude` adjudication;
3. for a selected substitution, emits **only** the historical passcode(s) — the modern
   implementation would behave incorrectly, and a whitelist bans anything unlisted
   (this reproduces upstream's choice: modern Chaos Emperor Dragon simply does not
   appear in the GOAT list);
4. for everything else, emits the canonical passcode plus recorded artwork variants
   (whitelists only auto-extend to aliases within ±10, so variants are explicit);
5. sorts each section by passcode and emits the `#[name] / !name / $whitelist` header.

The result for GOAT is entry-for-entry identical to Project Ignis's hand-maintained
list — `tests/test_repo_data.py` locks that in as a regression test, including the
EDOPro content hash (`0x28e9fc02`), which is order-independent and name-independent,
so the regenerated list is network-compatible with the reference.

(Caveat we discovered: Ignis's shipped file duplicates one line — `511000868` — and
EDOPro's line-folding XOR cancels duplicated identical lines out of its *runtime*
hash, so the file as shipped hashes differently in-client than its deduplicated
entry set. Worth an upstream issue; tracked in the roadmap.)

Both fixture formats build full `$whitelist` lists today: GOAT from its imported
extensional pool, Edison from its release-cutoff pool once `materialize` has derived
`cards` from `data/releases/` (see [releases.md](releases.md)). For a format whose
pool cannot yet be materialised — no coverage over its cutoff/scope, or an unresolved
release-data gap — the build degrades honestly instead of refusing outright: a plain
Forbidden/Limited blacklist whose header states that pool enforcement is pending.

## Validation

`retroformats/validate.py` — every finding has a stable code (`sources.unresolved`,
`format.banlist-not-in-force`, `pool.variant-out-of-range`, …). Errors fail the build;
warnings are tracked TODOs (e.g. `erratum.undated`). Current invariants:

- referential integrity: formats → banlists/pools/profiles/errata, all source refs
  resolve, chronology links resolve and are date-ordered symmetric;
- card identity: every passcode/name pair matches the card index; erratum historical
  codes must alias their modern card; pool variants must be within the ±10 window;
- temporal coherence: the referenced banlist must be in force on the snapshot date and
  not superseded; erratum change dates parse; snapshot within the period;
- pool/banlist coherence: a limited/semilimited card missing from an extensional pool
  is flagged;
- provenance: every record cites ≥1 resolvable source; releases carry per-product
  sources;
- determinism: `build --check` + the `test_dist_is_up_to_date` test forbid hand-edited
  or stale `dist/` content.

## Deviations from the original sketch

- The Python package lives at the top level (`retroformats/`) instead of `tools/`, so
  `python -m retroformats` works with zero installation; importers are a subpackage
  rather than a `tools/import/` directory.
- `generated/` is named `dist/`, because it doubles as the EDOPro-consumable payload
  root.
- There is no `data/cards/` hand-maintained dataset; the card index is generated, and
  full card data stays where it already lives (BabelCDB).
