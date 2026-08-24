# Two open v2 representation gaps — design research (not implemented)

**Status: research only. No schema, runtime, validator, or canonical data
changed by this document.** It exists to compare candidate representations
before either gap is designed for real, per the frozen architecture's own
discipline: UNKNOWN != GUESS applies to *how a fact should be represented*,
not only to *what the fact is*.

Two genuine representation gaps survive the pre-migration hardening passes
in `erratum-v2-migration-audit.md`, both discovered by that audit rather
than assumed going in:

1. **v1 implementation/research metadata with no v2 destination** —
   `status`, `tested`, `gap.upstream_checked`, `gap.behavioural_impact`,
   one bare `reason`. Demonstrably state-specific, not record-wide.
2. **Parity-only historical card identity** — 11 GOAT records where a
   reference implementation substitutes an old card entry for period-text
   reasons alone, with zero implementation-relevant behaviour to hang the
   fact on.

Both are compared against **the frozen architecture, unchanged**:

- event = chronology node; state identity = the relevant-event set;
  cosmetic/engine events participate in chronology but never in state
  identity;
- the terminal (all-relevant-events) state's coverage is unconditionally
  `MODERN`; an unauthored reachable non-terminal state is unconditionally
  `UNRESOLVED`;
- `Coverage` is a closed six-way semantic sum type;
- v1 and v2 stay separate until migration completes.

Neither proposal below touches any of that. Both are new, ORTHOGONAL
top-level concepts — read by tooling and format policy, never by
`selection_at()`, chronology, ordering, or `Coverage` parsing.

---

## 1. Corrected metadata inventory

(Full detail and worked examples also live in
`erratum-v2-migration-audit.md`; reproduced here because this document is
the design record for what to do about it.)

`metadata_inventory()`'s prior version conflated implementation-object
**occurrences** with **records** — a v1 record can carry more than one
implementation object (one baseline `implementation`, plus one
`resulting_implementation` per relevant change that records one), so
"`status`: 312" in a 296-record corpus was 312 occurrences across only 296
distinct records, not 312 records:

| field | occurrences | unique records | baseline / resulting | v2 destination | value distribution |
|---|---:|---:|---:|---|---|
| `status` | 312 | 296 | 296 / 12 | none | `complete`: 256, `missing`: 56 |
| `tested` | 252 | 240 | 236 / 12 | none | `false`: 248, `true`: 4 |
| `gap.upstream_checked` | 56 | 53 | 48 / 7 | none | `true`: 56 (uniform) |
| `gap.behavioural_impact` | 56 | 53 | 48 / 7 | none | free text, not tabulable |
| `reason` (bare, on one `none-needed` implementation) | 1 | 1 | 1 / 0 | none | free text, 1 record |

**12 records carry at least one `resulting_implementation`** (16
objects total, since some records have more than one relevant change):
`erratum-blue-eyes-toon-dragon`, `erratum-blue-eyes-ultimate-dragon`,
`erratum-dark-necrofear`, `erratum-insect-imitation`, `erratum-last-will`,
`erratum-necrovalley`, `erratum-night-assailant`, `erratum-rescue-cat`,
`erratum-sangan`, `erratum-swords-of-concealing-light`,
`erratum-witch-of-the-black-forest`, `erratum-yz-tank-dragon`.

**State-specificity is not hypothetical — it is directly observed:**

- **`status` differs between a record's baseline and at least one
  resulting implementation for 6 records**: `erratum-blue-eyes-toon-
  dragon`, `erratum-insect-imitation`, `erratum-last-will`, `erratum-
  necrovalley`, `erratum-night-assailant`, `erratum-yz-tank-dragon`.
- **`tested` differs for 1 record**: `erratum-rescue-cat`.
- **`gap.upstream_checked`/`gap.behavioural_impact` show no observed
  divergence** in the current corpus (`upstream_checked` is `true`
  everywhere it appears) — this is evidence of *coincidence*, not evidence
  the field is safely record-wide; it is still authored per implementation
  object.

### Worked example: Blue-Eyes Toon Dragon

```jsonc
// data/errata/blue-eyes-toon-dragon.json (abbreviated)
{
  "implementation": {
    "strategy": "reuse-upstream",
    "status": "complete",       // <- baseline: fully implemented
    "historical_passcode": ...
  },
  "changes": [
    {
      "kind": "functional",
      "resulting_implementation": {
        "strategy": "unresolved",
        "status": "missing",    // <- LATER state: NOT implemented
        "gap": { ... }
      }
    }
  ]
}
```

The baseline (pre-errata) version is fully reproduced upstream
(`status: complete`); the version created by its one relevant change is
NOT (`status: missing` — it becomes an acknowledged gap). One record, two
implementation objects, two different `status` values. **A record-level
field cannot represent this** — it would have to pick one value and either
overstate the baseline's completeness or understate it, silently. This is
the load-bearing fact that rules out any "just add a `review.status` field
to the erratum record" shortcut for problem 1, and is why the design below
is keyed by event-set, not by record.

### What the other fields mean

| field | question it answers | is it historical truth? | derivable in v2? | discard? |
|---|---|---|---|---|
| `status` | How complete is THIS implementation object? (`missing`/`stub`/`partial`/`complete`/`verified`) | No — workflow/confidence metadata about the research, not about the card | No — a human judgement about implementation completeness, not computable from chronology or coverage | **No.** Real, non-redundant information; retiring it would discard a currently-tracked confidence signal with no v2 replacement. |
| `tested` | Has this specific implementation actually been run/verified? | No — QA/workflow metadata | No | **No.** Same reasoning as `status`; a boolean QA flag with no mechanical substitute. |
| `gap.upstream_checked` | Did research actually confirm Project Ignis has no matching variant, or was it merely assumed? | No — research-provenance metadata about the INVESTIGATION, not the card | No — this is a fact about what research was done, not a computable property | **No.** Distinguishes "we looked and there is none" from "we didn't look" — losing it silently would make every gap look equally well-researched when they are not. |
| `gap.behavioural_impact` | What concretely differs from modern behaviour, in prose? | Partially — describes historical behaviour, but as free-text elaboration beyond what `gap_reason`/`gap_sources` already carry structurally | No — this is exactly the kind of nuance the structured fields cannot capture (see design doc's own §4 guidance to write concrete impact prose) | **No.** Duplicative with `gap_reason` in *topic* but not in *content* — reason answers "why is there a gap," behavioural_impact answers "what does that gap actually do." Both are already required by the schema for `gap`; only one (`reason`) has a v2 coverage destination. |
| `reason` (bare, `none-needed`) | Why was the modern implementation judged period-correct despite an available upstream variant? | Yes, partially — documents a researcher's judgement call, not the card's own history | No | **No**, for the one record it appears on — it is exactly the kind of "why we didn't substitute" rationale a future reviewer needs, and dropping it would make that decision unauditable. |

**No field in this inventory is recommended for retirement** (design
option D, below, is not applied to any of them) — every one carries
information a future migration, review, or research pass would otherwise
have to re-derive from scratch or lose outright. This conclusion is a
finding of the audit, not an assumption walked in with: each field's
disposition was checked individually rather than defaulting to "keep
everything."

---

## 2. Design comparison: state-specific implementation metadata

### Option A — extend every `Coverage` branch

Add `status`/`tested`/`gap_upstream_checked`/`gap_behavioural_impact` as
optional fields directly on `coverageReuseUpstream`, `coverageCustomScript`,
`coverageNoneNeeded`, `coverageKnownGap`.

**Fatal problem: `UNRESOLVED` is never authored.** It is exclusively the
mechanical default `_state_for()` synthesises for a reachable non-terminal
down-set with no matching `states[]` entry (design doc §4; frozen). There
is no `coverageUnresolved` branch to extend, because there is no authored
JSON object for an unresolved state at all — by construction, the schema
has nowhere for this metadata to live for exactly the down-sets most likely
to need it (an unresolved state is precisely where "did we check upstream?"
and "what would need to change?" matter most). This is not a minor gap: a
meaningful fraction of the corpus's `gap.upstream_checked`/`gap.
behavioural_impact` occurrences describe unresolved-with-acknowledged-gap
states, and even a genuinely-unauthored-and-truly-unresolved state (no
`gap` block at all) could plausibly want a "we haven't looked yet, here's
why" note — which option A cannot express even in principle.

Secondary problem: it also couples workflow metadata (`status`, `tested`)
to `Coverage`'s identity, which the frozen architecture keeps as a *closed
semantic sum type* — six kinds, meaning six *executable* answers. Widening
every branch with fields that never affect selection blurs that boundary
even where authoring is possible (`known-gap`, `reuse-upstream`, etc.),
making `Coverage` do two jobs (what to execute, and how well-researched it
is) instead of one.

**Rejected.**

### Option B — orthogonal metadata keyed by relevant-event set (recommended)

A new top-level array, structurally independent of `states[]`, keyed the
same way (`events`, a down-set of relevant event ids) but carrying only
descriptive/workflow fields, never anything `selection_at()` reads:

```jsonc
"implementation_metadata": [
  {
    "events": [],                          // baseline, e.g. Blue-Eyes Toon Dragon
    "status": "complete",
    "tested": false
  },
  {
    "events": ["c0"],                      // the resulting (post-change) state
    "status": "missing",
    "gap_upstream_checked": true,
    "gap_behavioural_impact": "Functional erratum: the Special Summon cost becomes a flat 'by Tributing 2 monsters' instead of 'the same number of monsters needed for a Tribute Summon (normally 2)'. The GOAT script computes the count from the card's current Level ('local amt=(lv>6 and 2) or (lv>4 and 1) or 0'), so with the Level reduced the era card is Special Summoned for 1 Tribute or none; the modern script hard-codes 2 in both its condition and its release selection.",
    "note": null
  }
]
```

(`gap_behavioural_impact` above is Blue-Eyes Toon Dragon's REAL
`gap.behavioural_impact` text, reproduced verbatim to show actual content,
not an invented placeholder — the field names around it are illustrative
shape only, per the naming caveat below.)

(Exact spelling of field names — `implementation_metadata` vs. e.g.
`research_metadata`, `gap_upstream_checked` vs. `upstream_checked` nested
under a `gap` sub-object — is an open naming question for whoever
implements this, not resolved here.)

**Why this satisfies the constraint option A cannot:** `implementation_
metadata` entries are not coverage. An entry MAY exist for a down-set whose
`Coverage` is mechanically `UNRESOLVED` (nothing in `authored_states`),
because the two arrays are parsed and validated independently —
`_state_for()`'s "unauthored reachable state -> UNRESOLVED" rule reads only
`states[]`, never touches this array, so the frozen rule is unchanged
verbatim. A `note` can exist for the terminal state too, without altering
`MODERN`'s synthesis (`_state_for()` still ignores whatever is authored at
the terminal down-set for *coverage* purposes; it just doesn't need to
ignore this SEPARATE array at all, since nothing reads it as coverage).

**Validation shape**, mirroring the pattern already used for `states[]`
(same error-code family, same primitives — `erratum.state-unknown-event`,
`erratum.state-duplicate-key`, `erratum.state-unreachable`):

- every `events` id must be a known, RELEVANT event id (unknown/non-relevant
  -> new error, same shape as `erratum.state-unknown-event`/`erratum.state-
  non-relevant-event`);
- no two entries may share the same `events` down-set (new error, same
  shape as `erratum.state-duplicate-key`);
- every `events` down-set must be structurally reachable
  (`erratum.state-unreachable`'s counterpart) — reusing `structural_
  states()`, the same function `states[]` validation already calls;
- `status` restricted to `IMPLEMENTATION_STATUSES`; `tested`/`gap_
  upstream_checked` boolean; `gap_behavioural_impact`/`note` free text.

**Risks, examined:**

- *Duplicated state keys relative to `states[]`.* Genuine but shallow: the
  two arrays use the same down-set vocabulary, so an author must keep two
  lists of `events` roughly (not necessarily exactly) in sync. Mitigated,
  not eliminated, by a validator INFO/WARN (not an ERROR — the two arrays
  are legitimately allowed to diverge, e.g. a metadata entry for an
  unresolved state has no `states[]` counterpart by definition) suggesting
  when a `states[]` entry has no matching metadata entry or vice versa.
- *Reachability/duplicate validation is new code, not free.* True, but it
  is a near-verbatim reuse of `_validate_v2_states()`'s existing logic
  against `structural_states()` — low implementation risk, not a new
  algorithm.
- *Possible drift from `states[]` over time.* An author edits one array and
  forgets the other. Same class of risk as any two related-but-independent
  arrays; no worse than the existing `changes[]`/`resulting_implementation`
  relationship in v1, which already has this property today and is exactly
  what proved the state-specificity claim above.

### Option C — let `states[]` entries carry metadata even when `coverage` is omitted

Allow a `states[]` entry to omit `coverage` and carry only metadata, or
add a `metadata` sub-object alongside `coverage` on the same entry.

**Investigated risk, confirmed real:** this blurs "unauthored reachable
state => UNRESOLVED" precisely because it makes "authored" ambiguous. Today
`authored_states.get(down_set)` returning `None` IS the definition of
unauthored; `_state_for()` uses exactly that to decide UNRESOLVED. If a
`states[]` entry can legitimately exist with `coverage` omitted (to carry
only metadata), `authored_states.get(down_set)` must be redefined to treat
"present in `states[]`, but with no `coverage` key" as *still* unauthored
for coverage purposes while simultaneously *authored* for metadata purposes
— two different meanings of "authored" attached to the same JSON array
entry, decided by which key you look at. That is a strictly worse
specification burden than Option B's two independent arrays (where
"authored" always means "has a matching entry in that array," full stop,
never a further per-key distinction), for the same net capability. It also
means a schema validator can no longer treat "does this `states[]` entry
have `coverage`" as required — a real, if small, weakening of the existing
closed-shape guarantee.

**Rejected** in favour of B: same expressiveness, worse specification
clarity.

### Option D — retire/derive some v1 workflow metadata

Evaluated per-field in section 1's table above. **Not recommended for any
field currently in the inventory** — every one carries information with no
computable substitute and demonstrated (or plausible, for the low-
occurrence fields) research value. This option remains open for a FUTURE
field the inventory surfaces, on a field-by-field basis with the same
burden of proof (show it is redundant/derivable, or show it has no project
value) — it is not a blanket policy.

### Recommendation: Option B

A new, independent, event-set-keyed `implementation_metadata[]` array.
Reasons, restated: it is the only option that can carry metadata for a
mechanically-UNRESOLVED state (A cannot); it keeps `Coverage`'s six-way sum
type semantically closed to *executable* meaning only, never workflow
metadata (A blurs this); it keeps "authored" unambiguous — a single,
uniform test ("does a matching array entry exist") rather than a
per-key-dependent one (C blurs this). Its risks (key duplication with
`states[]`, drift) are real but shallow and have a direct, low-risk
mitigation (a WARN-level cross-check, reusing existing validation
primitives) rather than a structural problem with the representation
itself.

---

## 3. Design comparison: parity-only historical identity

The 11 GOAT records assert "Project Ignis's reference list uses historical
card entry X for this card" with **zero functional/ruling behaviour
difference** — under the frozen architecture, zero relevant events means
the record's only structural state is `{}`, which IS the terminal state,
whose coverage is unconditionally synthesised `MODERN`. This is not a bug:
it follows directly from "cosmetic/engine events create no implementation-
state dimension," which is correct and frozen. The fact these 11 records
carry is not a fact about behaviour at all — it is a fact about **which
card entry a reference implementation displays/uses for provenance
reasons**, a category state Coverage was never designed to hold.

### Option A — record-level reference-identity/provenance mapping (recommended)

A new top-level array on the erratum record, orthogonal to `events{}`/
`ordering`/`states[]` entirely:

```jsonc
"reference_identities": [
  {
    "provenance_source": "ignis-lflists",
    "historical_passcode": 504700116,
    "historical_variant_passcodes": [],
    "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb + ProjectIgnis/CardScripts",
    "script": "goat/c504700116.lua"
  }
]
```

`provenance_source` reuses the SAME string convention `reference_parity`
format policy already uses (`fmt.reference_parity.provenance_source`,
checked today by `in_reference()` against `erratum.sources` membership) —
no new vocabulary, no new sourcing mechanism.

**Generalises beyond GOAT by construction**: the array can hold more than
one entry, one per reference implementation with its own provenance
identity for this card. A future format reproducing a DIFFERENT reference
list (a hypothetical `ocg-2007` format built from a different upstream
database) would add its own `provenance_source` entry to the SAME array,
on the SAME record, without touching GOAT's entry or GOAT's format
definition. A card with no parity-only identity at all simply has an empty
(or absent) array — nothing changes for the other 285 records.

**How `reference_parity` would consume it:** today, `_v2_parity_walk_
override()` walks `structural_states()` looking for the first usable
historical `Coverage`. The proposed addition is a NEW, EARLIER-OR-
FALLBACK resolution branch: when the format's `reference_parity.
provenance_source` matches an entry in `reference_identities`, that
entry's identity is used directly — no walk, no `Coverage` lookup, because
this fact was never a `Coverage` fact to begin with. (Whether it takes
priority over a genuine behavioural override when a record has BOTH is a
real open sub-question for implementation-time, not resolved here; none of
the current 11 records have any relevant events at all, so the question
does not arise for them today.)

**How the validator would verify provenance:**

- `provenance_source` must be non-empty, and (mirroring `in_reference()`'s
  existing convention) SHOULD appear in the record's own `sources` list —
  the same membership check already used to decide whether a record is
  "in" a reference format at all, not a new sourcing mechanism;
- `historical_passcode`/`historical_variant_passcodes` validated by the
  SAME `_is_valid_passcode()`/`_check_card_alias()` machinery already
  used for `Coverage`'s `historical_passcode` — no new passcode-validity
  logic;
- no two entries may share the same `provenance_source` (a record cannot
  claim two different identities for the same reference list — new error,
  shallow uniqueness check);
- (open question, not resolved here) whether a record with 1+ relevant
  events may ALSO carry `reference_identities`, and if so how a validator
  should cross-check it doesn't contradict a genuine behavioural
  `Coverage` claim for the same provenance passcode.

### Option B — format-local parity mapping

Each format needing parity carries its own `card_overrides: {passcode:
{historical_passcode, ...}}` map in its own definition file.

**Investigated and rejected**: does not scale past one format. If two
formats reproduce the SAME reference list (plausible — nothing in the
architecture forbids two format definitions pointing at the same
`provenance_source`), the SAME 11 mappings would need to be duplicated
verbatim in both format files, with no mechanism keeping them in sync —
exactly the kind of implicit-structure-carries-evidentiary-weight problem
the whole v2 redesign exists to eliminate (design doc's own stated
motivation). It also inverts the fact's natural owner: "which card entry
the reference list uses" is a fact about the CARD's provenance record, not
about the FORMAT that happens to reproduce it — a format should describe
*which* reference it reproduces (already true: `reference_parity.
provenance_source`), not re-author *what that reference contains* on a
per-format basis.

### Option C — special parity coverage/state exception

Add a seventh `Coverage` kind (e.g. `REFERENCE_ONLY`), or an exception
rule permitting the terminal state's coverage to be something other than
`MODERN` when a "parity" flag is set.

**This directly violates two named-frozen properties**: "terminal
relevant-event state = MODERN" (unconditionally, no exceptions today) and
"`Coverage` remains a closed semantic sum type" (a seventh kind is not
closed to six). The task's own constraint list marks both as frozen unless
the *architecture itself* — chronology, ordering, or `Coverage` meaning —
is being reopened, which this task explicitly forbids. **Rejected outright
without further evaluation**, precisely because evaluating it further
would already be reopening the architecture the task says not to reopen.

### Option D — a sidecar identity file

A separate top-level JSON file (e.g. `data/reference-identities.json`)
mapping modern passcode -> reference identity, outside any erratum record.

**Weaker than Option A for the same reason Option B is weaker than
keeping the fact on the card's own record**: it splits one card's data
across two files with no structural link between them beyond a passcode
string, breaking the established one-file-per-card convention every other
erratum fact already follows, and adding a second file an editor must
remember to update in lockstep with the erratum record it describes. It
has no advantage over Option A that survives this cost — a per-record
array achieves the same generality (multiple reference sources per card)
without the indirection.

### Recommendation: Option A

A new, record-level `reference_identities[]` array on the erratum record,
orthogonal to `events{}`/`ordering`/`states[]`/`Coverage` entirely. It
generalises beyond GOAT by construction (multiple entries, one per
reference source), reuses every validation primitive that already exists
(`_is_valid_passcode`, `_check_card_alias`, the `sources`-membership
convention `in_reference()` already implements) rather than inventing new
ones, and requires no change to the frozen `Coverage` sum type or the
terminal-state-is-MODERN rule — because the fact it carries was never a
`Coverage` fact.

---

## 4. Why both recommendations preserve the frozen architecture

| frozen property | implementation_metadata[] (Option B) | reference_identities[] (Option A) |
|---|---|---|
| event = chronology node | untouched — no new event concept | untouched |
| state identity = relevant-event set | untouched — metadata is keyed BY this identity, never redefines it | untouched — not keyed by state at all |
| cosmetic/engine events: chronology yes, state identity no | untouched | untouched |
| terminal state coverage = MODERN | untouched — metadata array never participates in `_state_for()` | untouched — the fact bypasses Coverage entirely rather than overriding it |
| unauthored reachable state = UNRESOLVED | untouched — `authored_states` lookup is unchanged; the new array is a second, independent lookup | not applicable (no relevant events involved) |
| `Coverage` is a closed six-way sum type | untouched — no new kind, no new field on any existing branch | untouched — no new kind |
| UNKNOWN != GUESS | both arrays are strictly additive/optional; absence means "not recorded," never inferred | same |
| v1/v2 separate until migration completes | both are v2-only proposals; v1 shape is unchanged by this document | same |

Neither proposal changes `selection_at()`, `ordering_proof()`,
`_reachable_down_sets()`, `_descendants_and_check_acyclic()`, or any
`Coverage` branch. Both are read only by tooling (`metadata_inventory()`'s
future successor) or by one narrowly-scoped format-policy consumer
(`reference_parity`) — never by chronology or selection.

---

## 5. Recommended minimal representation (summary)

1. **Implementation metadata**: `implementation_metadata: [{events: [...],
   status?, tested?, gap_upstream_checked?, gap_behavioural_impact?,
   note?}]` — new top-level array on `ErratumV2`, keyed by relevant-event
   down-set, validated against `structural_states()` the same way
   `states[]` already is, read by no runtime selection code.
2. **Parity-only identity**: `reference_identities: [{provenance_source,
   historical_passcode, historical_variant_passcodes?, upstream?,
   script?}]` — new top-level array on `ErratumV2`, validated with the
   SAME passcode/sources machinery `Coverage` already uses, consumed by
   `reference_parity` format resolution as a fact that bypasses `Coverage`
   rather than living inside it.

Both are additive, optional, and orthogonal to every existing v2 field.

---

## 6. Exact changes implementation would require (not made in this task)

**Schema (`schemas/erratum.schema.json`)**

- Add `implementation_metadata` (array, `additionalProperties: false`
  items, `events` required) to the `erratumV2` branch (full shape only —
  whether sugar-shaped records may use it, given they have at most one
  event and one non-terminal state, is an open question for whoever
  implements this).
- Add `reference_identities` (array, `additionalProperties: false` items,
  `provenance_source` + `historical_passcode` required) to the `erratumV2`
  branch, and decide whether v1 records may also carry it (v1 is legacy
  and not otherwise gaining new top-level fields, so the likely answer is
  no — the 11 current records would gain it only once migrated).

**Runtime (`retroformats/model.py`)**

- New frozen dataclasses (naming TBD): one for an `implementation_
  metadata[]` entry, one for a `reference_identities[]` entry — following
  the existing `HistoricalTransition`/`ImplementationCoverage` pattern
  (`.from_raw()` classmethod, thin, no computed logic beyond parsing).
- `ErratumV2.load()`: parse both arrays into two new fields on `ErratumV2`
  (e.g. `implementation_metadata: dict[frozenset[str], ...]`,
  `reference_identities: tuple[..., ...]`), alongside — never merged with
  — `authored_states`.
- No change to `_state_for()`, `selection_at()`, `structural_states()`, or
  `_reachable_down_sets()`.

**Validator (`retroformats/validate.py`)**

- New `_validate_v2_implementation_metadata()`, mirroring `_validate_v2_
  states()`: unknown/non-relevant event ids, duplicate down-set keys,
  unreachable down-sets (reusing `structural_states()`); a WARN-level
  cross-check against `states[]` for authors who likely meant to keep the
  two in sync.
- New `_validate_v2_reference_identities()`: `provenance_source` non-empty
  and present in `erratum.sources`; `historical_passcode`/`historical_
  variant_passcodes` validated via the existing `_safe_passcode`/`_check_
  card_alias` calls; no duplicate `provenance_source` within one record.

**Consumers (`retroformats/lflist.py`)**

- `implementation_metadata[]`: no consumer change required — it is
  descriptive only.
- `reference_identities[]`: `_v2_parity_walk_override()`/`parity_
  override()` gain a resolution branch checked against `fmt.reference_
  parity.provenance_source` before (or as a fallback to, TBD) the
  structural-state walk.

**Migration tooling (`tests/migration_audit.py`)**

- `_coverage_from_v1()`/`candidate_v2()` gain companion mappings: v1's
  `status`/`tested`/`gap.upstream_checked`/`gap.behavioural_impact`/bare
  `reason` -> `implementation_metadata[]` entries; the 11 parity-only
  records' baseline `reuse-upstream` claim -> a `reference_identities[]`
  entry instead of a discarded `states[]` entry.
- `metadata_inventory()` re-run after implementation should report an
  EMPTY inventory (every currently-unrepresented field now has a
  destination) — that emptiness becomes the acceptance criterion for
  closing this gap, not a subjective judgement call.
- `_data_preserved()`/`_coverage_preserved()` gain a third check
  alongside transition-text and coverage-field preservation.

No canonical `data/errata/*.json` record changes for any of this — the
gap is in the v2 REPRESENTATION, not in v1 data, which stays exactly as
it is until migration.

---

## 7. Migration sequencing after both gaps are resolved

This document is a proposal, not a decision — the sequencing below is
conditional on both designs being reviewed, decided, and IMPLEMENTED
(schema + runtime + validator + consumer + migration-tooling changes, all
listed above) in a separate, later task.

1. **Design review and decision** (human) on both representations —
   including the open sub-questions flagged above: exact field naming,
   whether sugar-shaped records may carry `implementation_metadata`,
   whether a record may carry `reference_identities` alongside genuine
   relevant events and how a validator should then cross-check it.
2. **Implement** the schema/runtime/validator/consumer changes in section
   6, as their own atomic commit(s) — not bundled with any canonical data
   migration.
3. **Re-run `tests/migration_audit.py`'s candidate construction** with
   both new fields wired into `candidate_v2()`, and confirm two things
   mechanically rather than by inspection: `metadata_inventory()` returns
   empty (nothing left with `has_v2_destination: false`), and every one of
   the 11 parity-only records' `reference_identities`-based candidate
   round-trips its `historical_passcode` exactly (a `_coverage_preserved
   ()`-style independent check, extended to the new array).
4. **Only then does canonical migration begin**, in the order the design
   document's §13 sequence already lays out — now genuinely gated on data
   preservation, not merely chronology/shape readiness:
   - the 180 sugar-eligible + 35 single-relevant-with-siblings + 11
     fully-ordered records (step 4), now migrating WITH their
     `implementation_metadata`/`reference_identities` fields populated;
   - the 11 parity-only records migrate alongside step 4 once `reference_
     identities` exists, rather than needing their own separate future
     step — the representation gap was the only thing blocking them,
     and once it is closed they are exactly as safe as the other 236;
   - the 47 already-researched unordered records (step 5);
   - the 2 manual-review records (step 6), after their order question is
     separately resolved by a human, unaffected by either representation
     gap.

**This task changes no schema, no runtime, no validator, no canonical
erratum record.** Both representations above are proposals for a FUTURE
task to implement, review, and only then migrate against.
