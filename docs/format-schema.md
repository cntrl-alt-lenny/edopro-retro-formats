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
  "errata_overrides": {                    // standing policy + last-resort per-card pins
    "unresolved_policy": { "choice": "modern", "reason": "...", "sources": [...] },
    "include": [], "exclude": [], "sources": []
  },
  "defining_events": [...],
  "relevant_products": ["ABPF", "DPKB"],   // codes in data/releases/
  "implementation_status": { "banlist": "complete", "card_pool": "verified", ... },
  "sources": [...]
}
```

`snapshot` is the one date used for computations (card-pool cutoffs, errata
applicability). `start`/`end` describe the era for humans and chronology checks.
`errata_overrides` holds two shapes for a standing, sourced policy —
`reference_parity` (this format reproduces an existing reference implementation, so it
substitutes whatever the reference does; GOAT's shape) or `unresolved_policy` (what to
do when a record's chronology cannot decide at this snapshot; Edison's shape, shown
above) — plus the always-available `include`/`exclude` per-card adjudications of last
resort. See [errata.md](errata.md) for the selection logic these feed.

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
- `release-cutoff` — `{"cutoff": {"cutoff_date": ..., "territories": [...], "include": [...], "exclude": [...], "exclude_products": [...]}}`:
  everything released by the date in the scoped territories, plus/minus cited
  exceptions. `python -m retroformats materialize` derives `cards` from
  `data/releases/` once coverage certifies the cutoff/scope (Edison's pool is
  materialised this way today — 3,673 cards; see [releases.md](releases.md)).

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

One file per card that ever needs historical consideration. This is a summary of the
current (versioned) shape — [errata.md](errata.md) is authoritative for the full data
model, the fail-safe selection algorithm, and the research/review pipeline.

A card's history is a **chain of versions**: a baseline (`implementation`), then one
new version per entry in `changes[]` (oldest → newest; the last one is the modern
card). Fields that matter:

- `classification` — the *dominant* kind across `changes[]` (severity order
  `functional` > `ruling` > `engine` > `cosmetic`; the validator enforces agreement):
  - `functional` — printed/official text changed **and** resolves differently → needs
    a historical implementation for the era before it;
  - `ruling` — official interpretation/procedure changed, text unchanged → needs one
    too (e.g. 2005-era failed-search Deck verification);
  - `cosmetic` — wording/PSCT modernisation, same resolution → **never** substitutes;
    the modern script is period-correct (absence of a record means "not reviewed",
    not "no erratum");
  - `engine` — the game rules changed, not the card → **never** substitutes; belongs
    to a rule profile.
- `changes[]` — each entry has its own `kind` (only `functional`/`ruling` changes can
  substitute a card), an `effective` chronology object (`date` + `precision` +
  `status: verified|reported` with required `corroboration` when verified, or
  `old_attested_through`/`new_attested_from` for a bounded interval when no point date
  is known — never invent one), `historical_text`/`modern_text` transcribed from cited
  databases (never paraphrased; `null` until transcribed), `summary`, `sources`, and
  optionally `resulting_implementation` when the version the change *creates* is
  itself historical (needed for cards errata'd more than once).
- `implementation` (baseline) / `changes[].resulting_implementation` (later versions)
  — each an object: `strategy` (`none-needed` / `reuse-upstream` / `custom-script` /
  `unresolved`), `historical_passcode` (+ `historical_variant_passcodes`), `upstream`,
  `script`, `status`, `tested` (set only once an executed engine test demonstrates the
  behaviour — see [engine-testing.md](engine-testing.md)), and `gap` (required when
  `strategy: unresolved` — an *acknowledged*, sourced divergence nothing reproduces
  yet, as opposed to a silently unfinished one).
- `review.status` — `imported` (mechanically created; applies only through an
  explicit `errata_overrides.include`) or `reviewed` (chronology/classification
  confirmed by a human; participates in computed selection, and an unresolved
  transition becomes a hard error rather than a silent guess).

**Applicability is computed and fail-safe**: `Erratum.selection_at(snapshot)` returns
`modern`, `historical`, `gap` (determinate era, no usable implementation), or
`ambiguous` — and ambiguous selection refuses rather than guessing. A format
additionally states standing policy: `reference_parity` (substitute whatever an
existing reference implementation substitutes — GOAT's shape) or `unresolved_policy`
(what to do when chronology alone cannot decide — Edison's shape); per-card
`errata_overrides.include`/`exclude` remain available as adjudications of last resort.

## Releases (`data/releases/products/*.json`, `coverage.json`, `gaps.json`)

Per-product, per-territory release events and printings (`products/`), a coverage
window claiming which date/territory ranges are dated completely (`coverage.json`),
and a gap ledger accounting for every anomaly the importer detects
(`gaps.json`) — together they let a release-cutoff pool honestly refuse to
materialise until coverage is *certified*, not merely asserted. See
[releases.md](releases.md) for the full model.

## Card index (`data/cards/index.json`)

Generated (never hand-edited) from BabelCDB for exactly the passcodes referenced
anywhere in the repo: `passcode`, `name`, `alias_of`, `ot`. It is the ground truth
for validation and records the source repo + commit.
