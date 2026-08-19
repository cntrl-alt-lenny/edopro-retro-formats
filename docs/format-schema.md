# Format schema guide

JSON Schemas in [schemas/](../schemas/) are the formal reference; this page explains
the intent and the modelling decisions. All records share two conventions:

- **Card references** are `{"passcode": <int>, "name": "<modern English name>"}` —
  deliberately redundant; the validator cross-checks both against the generated card
  index so a typo in either field is an error, not silent corruption.
- **`sources`** arrays cite ids in `data/sources.json` (or the format's own
  `sources.json`); at least one per record, all must resolve.

## Format (`formats/<id>/format.json`)

The id is `yyyy-mm-slug` (`2005-04-goat`), chronologically sortable and equal to the
directory name. A format is mostly references:

```jsonc
{
  "id": "2010-03-edison",
  "name": "Edison Format",
  "region": "TCG",
  "period": {
    "start": "2010-03-01",     // first day the defining conditions held
    "end": "2010-05-10",       // last day (null while unresearched)
    "snapshot": "2010-04-24"   // THE reference date for cutoff/errata computations
  },
  "chronology": { "previous": null, "next": null },   // format ids; validator checks order + symmetry
  "banlist": "tcg-2010-03",                // -> data/banlists/tcg/2010-03.json
  "card_pool": "pool-edison-2010",         // -> data/pools/
  "rule_profile": "rules-tcg-mr1-edison",  // -> data/rule-profiles/
  "errata_policy": "computed",
  "errata_overrides": { "include": [], "exclude": [], "sources": [] },
  "defining_events": [...],
  "relevant_products": ["ABPF", "DPKB"],   // codes in data/releases/
  "implementation_status": { "banlist": "complete", "card_pool": "stub", ... },
  "sources": [...]
}
```

`snapshot` is the one date used for computations (card-pool cutoffs, errata
applicability). `start`/`end` describe the era for humans and chronology checks.

## Banlist (`data/banlists/<region>/<yyyy-mm>.json`)

One historical F/L list snapshot, id `tcg-2010-03`. Entries carry `card` + `status`
(`forbidden`/`limited`/`semilimited`); unlisted cards are unlimited. `effective_date`
and `superseded_by_date` let the validator prove the list was actually in force on a
format's snapshot date. Banlists are region-scoped facts, independent of formats and
of implementation details — always modern passcodes, never pre-errata codes.

## Card pool (`data/pools/*.json`)

Two kinds:

- `extensional` — explicit list of canonical cards, each optionally with
  `variant_passcodes` (artwork variants within ±10, recorded so whitelist generation
  can reproduce reference lists code-for-code). Used when a vetted pool definition
  exists (GOAT ← Ignis whitelist).
- `release-cutoff` — `{"cutoff": {"cutoff_date": ..., "include": [...], "exclude": [...]}}`:
  everything released by the date, plus/minus cited exceptions. Materialised against
  `data/releases/` once coverage exists (Edison is waiting on this).

## Rule profile (`data/rule-profiles/*.json`)

A reusable rules-era description mapped to the engine:

- `engine.preset` — the ocgcore composite macro when one matches exactly
  (`DUEL_MODE_GOAT`); null for custom sets.
- `engine.flags` — the individual `DUEL_*` flags (composite macros are rejected by
  the validator; tests assert the expansion matches the preset for the pinned core).
- `engine.starting_lp`/`starting_hand`/`draw_count` — `OCG_Player` fields, not flags.
- `client` — what EDOPro (not the core) enforces: `forbidden_card_types`, deck size
  ranges. Hosts must set these manually; they cannot ship in a data repo.
- `differences_from_modern` — human-readable, per-flag, cited.
- `known_gaps` — historical rules the current engine **cannot** reproduce, so the
  claim of accuracy is bounded and honest.

Many formats share one profile. Do not fork a profile per format; fork only when a
sourced rules difference demands it.

## Erratum (`data/errata/<card>.json`)

One file per card that ever needs historical consideration. Fields that matter:

- `classification`:
  - `functional` — printed/official text change altering behaviour → needs a
    historical implementation;
  - `cosmetic` — PSCT/wording modernisation → explicitly records that the modern
    script is period-correct (absence of a record means "not reviewed", not "no
    erratum");
  - `ruling` — behaviour changed with no text change (e.g. 2005 failed-search
    verification) → script- or engine-level handling;
  - `engine` — differences produced by rules eras → handled by rule profiles, not
    card overrides.
- `changes[]` — oldest→newest; each with `date_effective` (when the NEW behaviour
  started — the key field for computed applicability), `historical_text`,
  `modern_text`, `summary`, `sources`. Texts are transcribed from cited databases,
  never paraphrased from memory (`null` until transcribed).
- `implementation` — `strategy` (`none-needed` / `reuse-upstream` / `custom-script` /
  `unresolved`), `historical_passcode` (+ `historical_variant_passcodes` for alt arts
  of the historical version), `upstream`, `script`, `status`, `tested`.

**Applicability is computed**: a format at snapshot S uses the historical version iff
S < the earliest `date_effective`. While dates are unresearched, a format may pin
`errata_overrides.include` (GOAT currently includes all 211 imported overrides,
mirroring the Ignis reference); dated changes should progressively empty that list.

## Releases (`data/releases/*.json`)

Product release dates per region with per-product sources and an explicit `coverage`
status, so a cutoff pool can honestly refuse to materialise until coverage is
adequate.

## Card index (`data/cards/index.json`)

Generated (never hand-edited) from BabelCDB for exactly the passcodes referenced
anywhere in the repo: `passcode`, `name`, `alias_of`, `ot`. It is the ground truth
for validation and records the source repo + commit.
