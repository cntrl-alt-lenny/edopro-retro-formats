# Two v2 representation gaps — design, and now implementation

**Status: IMPLEMENTED. Canonical migration NOT started.** The design
comparison below (sections 1-5) was written, reviewed, and — after one
correction (section 3's `reference_id`, below) — accepted; sections 6-7 now
describe what was actually built (`implementation_metadata[]`,
`reference_identities[]`, their validators, and their consumer/precedence
wiring), not a proposal. **No `data/errata/*.json` record has been
migrated** — the schema/runtime/validator/consumer changes exist so a
future migration has somewhere to put this data, and this task's own
migration-audit tooling independently verifies every one of the 247
semantically-equivalent records' v1 metadata/identity round-trips into the
new representation, but the canonical data itself is untouched, and the
247/49/48 partition (`erratum-v2-migration-audit.md`) is unchanged by any
of this.

Two genuine representation gaps survived the pre-migration hardening passes
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

**Corrected TWICE now.** First: `metadata_inventory()`'s original version
conflated implementation-object **occurrences** with **records**. Second:
even after that fix, it counted `resulting_implementation_occurrence_count`
as the number of *records* with a resulting implementation, not the number
of resulting-implementation *objects* (Necrovalley alone contributes
three), and — more seriously — it silently overwrote one record's earlier
`resulting_implementation` value with a later one before ever comparing it
to the baseline, so a record whose FIRST resulting state diverged but whose
LAST happened to match baseline was invisible to the divergence check. The
fix gives every occurrence an exact, never-collapsed locator (`"baseline"`
or `"resulting:<change-index>"`) and compares ALL of a record's occurrences
together, not just the last one processed:

| field | occurrences | unique records | baseline / resulting occ | unique baseline / resulting records | v2 destination (now) | value distribution |
|---|---:|---:|---:|---:|---|---|
| `status` | 312 | 296 | 296 / 16 | 296 / 12 | `implementation_metadata[]` | `complete`: 256, `missing`: 56 |
| `tested` | 252 | 240 | 236 / 16 | 236 / 12 | `implementation_metadata[]` | `false`: 248, `true`: 4 |
| `gap.upstream_checked` | 56 | 53 | 48 / 8 | 48 / 7 | `implementation_metadata[]` | `true`: 56 (uniform) |
| `gap.behavioural_impact` | 56 | 53 | 48 / 8 | 48 / 7 | `implementation_metadata[]` | free text, not tabulable |
| `reason` (bare, on one `none-needed` implementation) | 1 | 1 | 1 / 0 | 1 / 0 | `implementation_metadata[]` | free text, 1 record |

**12 distinct records carry at least one `resulting_implementation`** (16
occurrences total, since some records have more than one relevant change):
`erratum-blue-eyes-toon-dragon`, `erratum-blue-eyes-ultimate-dragon`,
`erratum-dark-necrofear`, `erratum-insect-imitation`, `erratum-last-will`,
`erratum-necrovalley`, `erratum-night-assailant`, `erratum-rescue-cat`,
`erratum-sangan`, `erratum-swords-of-concealing-light`,
`erratum-witch-of-the-black-forest`, `erratum-yz-tank-dragon`.

**State-specificity is not hypothetical — it is directly observed, and the
fix found a record the previous "corrected" pass missed:**

- **`status` differs between a record's baseline and at least one
  resulting implementation for 7 records** (was reported as 6): `erratum-
  blue-eyes-toon-dragon`, `erratum-insect-imitation`, `erratum-last-will`,
  `erratum-necrovalley`, `erratum-night-assailant`, `erratum-swords-of-
  concealing-light`, `erratum-yz-tank-dragon`. **`erratum-swords-of-
  concealing-light`** is the one the overwrite bug hid: baseline is
  `complete`, its first resulting_implementation is `missing`, its second
  and third are `complete` again — the old "keep only the last value seen"
  comparison saw complete-vs-complete and missed the genuine divergence at
  the first change entirely.
- **`tested` differs for 1 record**: `erratum-rescue-cat`.
- **`gap.behavioural_impact` differs for 2 records**: `erratum-dark-
  necrofear`, `erratum-necrovalley`.
- **`gap.upstream_checked` shows no observed divergence** in the current
  corpus (`upstream_checked` is `true` everywhere it appears) — this is
  evidence of *coincidence*, not evidence the field is safely record-wide;
  it is still authored per implementation object.

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

### Option B — orthogonal metadata keyed by relevant-event set (recommended, and implemented)

A new top-level array, structurally independent of `states[]`, keyed the
same way (`events`, a down-set of relevant event ids) but carrying only
descriptive/workflow fields, never anything `selection_at()` reads. **This
is the frozen, implemented shape** (task section 2) — `status`/`tested`/
`reason` map straight across from v1's own field names (the v1 bare
`reason` field keeps its own name; it is NOT renamed to a generic `note`),
and `gap.upstream_checked`/`gap.behavioural_impact` nest under `gap`,
mirroring v1's `implementation.gap` shape exactly:

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
    "gap": {
      "upstream_checked": true,
      "behavioural_impact": "Functional erratum: the Special Summon cost becomes a flat 'by Tributing 2 monsters' instead of 'the same number of monsters needed for a Tribute Summon (normally 2)'. The GOAT script computes the count from the card's current Level ('local amt=(lv>6 and 2) or (lv>4 and 1) or 0'), so with the Level reduced the era card is Special Summoned for 1 Tribute or none; the modern script hard-codes 2 in both its condition and its release selection."
    }
  }
]
```

(`gap.behavioural_impact` above is Blue-Eyes Toon Dragon's REAL
`gap.behavioural_impact` text, reproduced verbatim to show actual
content, not an invented placeholder.)

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

### Recommendation: Option B — implemented, WITHOUT a cross-array warning

A new, independent, event-set-keyed `implementation_metadata[]` array.
Reasons, restated: it is the only option that can carry metadata for a
mechanically-UNRESOLVED state (A cannot); it keeps `Coverage`'s six-way sum
type semantically closed to *executable* meaning only, never workflow
metadata (A blurs this); it keeps "authored" unambiguous — a single,
uniform test ("does a matching array entry exist") rather than a
per-key-dependent one (C blurs this).

**Decided against, on implementation: no WARN-level cross-check between
`states[]` and `implementation_metadata[]`.** This document originally
proposed one as a mitigation for the two arrays' key duplication/drift
risk. Rejected before being built (task section 10): the arrays are
DELIBERATELY independent — a state legitimately has coverage with no
metadata, metadata with no (or mechanically-UNRESOLVED) coverage, or both
— and a cross-array WARN would fire for every one of the hundreds of
legitimate cases across the corpus where a record simply never authored
metadata at all, drowning the one real signal (an actually malformed
entry) in noise. `_validate_v2_implementation_metadata()` therefore checks
ONLY that an authored entry is internally well-formed, never that a state
also has (or lacks) a counterpart in the other array.

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

### Option A — record-level reference-identity/provenance mapping (recommended, and implemented)

A new top-level array on the erratum record, orthogonal to `events{}`/
`ordering`/`states[]` entirely.

**Corrected once, before implementation: keyed by `reference_id`, NOT
solely by `provenance_source`.** The first version of this design used only
`provenance_source` as the identity key. That conflates two different
questions: `provenance_source` names an entire pinned SOURCE (e.g. the
whole `ignis-lflists` repository), which can in principle host more than
one distinct reference LIST — GOAT's `GOAT.lflist.conf` today, a
hypothetical second historical reference list tomorrow, both still cited
via `ignis-lflists`. Keying by `provenance_source` alone could not
distinguish "reference X, sourced from repository R" from "reference Y,
also sourced from repository R." The corrected shape adds a separate,
stable `reference_id`:

```jsonc
"reference_identities": [
  {
    "reference_id": "project-ignis-goat",
    "provenance_source": "ignis-lflists",
    "historical_passcode": 504700116,
    "historical_variant_passcodes": [],
    "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb + ProjectIgnis/CardScripts",
    "script": "goat/c504700116.lua"
  }
]
```

- `reference_id` identifies WHICH reference implementation/list (e.g.
  `"project-ignis-goat"`, GOAT's exact value once implemented) —
  independent of where its assertions are sourced from.
- `provenance_source` reuses the SAME string convention `reference_parity`
  format policy already used for its own `provenance_source` (`fmt.
  reference_parity.provenance_source`, checked by `in_reference()` against
  `erratum.sources` membership) — no new sourcing mechanism, just no
  longer doing double duty as an identity key too.
- The two are never interchangeable: one provenance source can host more
  than one reference list, and (in principle) one reference could draw on
  more than one provenance source over time — `provenance_source`
  uniqueness is never identity uniqueness.
- A format's own `reference_parity` gains the matching field:
  `{"reference_id": "project-ignis-goat", "provenance_source":
  "ignis-lflists", ...}` — implemented for GOAT (section 7).

**Generalises beyond GOAT by construction**: the array can hold more than
one entry, one per reference implementation this card has an identity
claim for. A future format reproducing a DIFFERENT reference list (a
hypothetical `ocg-2007` format built from a different reference,
potentially even the SAME `provenance_source`) would add its own
`reference_id`-keyed entry to the SAME array, on the SAME record, without
touching GOAT's entry or GOAT's format definition. A card with no
parity-only identity at all simply has an empty (or absent) array —
nothing changes for the other 285 records.

**How `reference_parity` consumes it (implemented; frozen precedence,
section 4 below):** an exact, matching `reference_identities[]` entry
(same `reference_id` as the format's `reference_parity.reference_id`)
outranks the structural `_v2_parity_walk_override()` walk for that same
reference — it is a different, more specific kind of fact ("reference X
uses card entry Y"), not a heuristic guess at one. A record with relevant
behavioural events MAY also carry a `reference_identities` entry; the
migration tooling itself only emits one for the 11 zero-relevant-event
records (section 8), since a record with relevant events already has a
working Coverage-based representation and a second, redundant entry is not
what this task's migration scope calls for — but the schema/runtime/
validator impose no such restriction, precisely so a future record with
both genuine behavioural chronology AND a documented reference-provenance
divergence can express both.

**How the validator verifies provenance (implemented):**

- `reference_id` must be non-empty, and unique within one record's
  `reference_identities[]` (`erratum.reference-identity-missing-id` /
  `erratum.reference-identity-duplicate-id`);
- `provenance_source` must be non-empty, resolve through the source
  registry (mirroring `_check_sources()`'s existing convention:
  `erratum.reference-identity-missing-provenance` / `sources.unresolved`),
  and appear in the record's own `sources` list
  (`erratum.reference-identity-provenance-not-in-sources`);
- `historical_passcode`/`historical_variant_passcodes` validated by the
  SAME `_safe_passcode()`/`_check_card_alias()` machinery `Coverage`'s
  `historical_passcode` already uses — no new passcode-validity logic —
  including the +/-10 artwork-variant rule
  (`erratum.variant-out-of-range`);
- `historical_passcode` must not equal `modern_card.passcode`
  (`erratum.reference-identity-matches-modern`) — if the reference uses
  the modern card, no entry is necessary at all;
- `upstream` is required non-empty (`erratum.reference-identity-missing-
  upstream`).

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

### Recommendation: Option A — implemented, `reference_id`-keyed

A new, record-level `reference_identities[]` array on the erratum record,
orthogonal to `events{}`/`ordering`/`states[]`/`Coverage` entirely, keyed
by `reference_id` (WHICH reference) with `provenance_source` (WHERE it is
sourced from) kept as a separate field, never doing double duty as the
identity key. It generalises beyond GOAT by construction (multiple
entries, one per reference), reuses every validation primitive that
already exists (`_is_valid_passcode`, `_check_card_alias`, the `sources`-
membership convention `in_reference()`/`_check_sources()` already
implement) rather than inventing new ones, and requires no change to the
frozen `Coverage` sum type or the terminal-state-is-MODERN rule — because
the fact it carries was never a `Coverage` fact.

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

Neither changes `selection_at()`, `ordering_proof()`,
`_reachable_down_sets()`, `_descendants_and_check_acyclic()`, or any
`Coverage` branch. Both are read only by tooling (`metadata_inventory()`,
`tests/migration_audit.py`'s candidate construction) or by one narrowly-
scoped format-policy consumer (`reference_parity`) — never by chronology or
selection.

### Frozen reference-parity precedence (implemented)

For a v2 erratum under a format's `reference_parity`:

1. an explicit format `exclude` still wins outright;
2. explicit `include` semantics remain exactly as before this task;
3. if the format's `reference_parity` declares a `reference_id` AND this
   erratum has a matching `reference_identities[]` entry (same
   `reference_id`): **that exact identity is used**, before any structural
   check;
4. otherwise, fall back to the existing provenance-membership +
   `_v2_parity_walk_override()` structural-walk behaviour, unchanged;
5. ordinary chronology resolution remains after parity, exactly as before.

**A matching-but-malformed identity, or one whose `provenance_source`
contradicts the format's own, fails safe** — reported as a problem, never
silently replaced by falling through to the structural walk (`_reference_
identity_override()` returns a distinct sentinel for "no match, fall
through" versus "matched but invalid, do not fall through"). A record with
relevant behavioural events is allowed to carry a `reference_identities`
entry too; if it disagrees with the record's own chronology-derived
Coverage, reference parity still wins for that format (it is format-
DEFINING, exactly like the existing structural-walk policy already is) —
the validator surfaces the divergence as a finding, not a hard error,
matching the existing `format.parity-*` philosophy of reporting disagreement
rather than forbidding it.

---

## 5. Recommended minimal representation (summary, as implemented)

1. **Implementation metadata**:
   ```jsonc
   "implementation_metadata": [
     {"events": [...], "status": "...", "tested": false, "reason": "...",
      "gap": {"upstream_checked": true, "behavioural_impact": "..."}}
   ]
   ```
   New top-level array on `ErratumV2` (full v2 AND sugar), keyed by
   relevant-event down-set (sugar: `[]` baseline, `["event"]` terminal),
   validated against `structural_states()` the same way `states[]` already
   is, read by no runtime selection code. At least one field besides
   `events` is required per entry — an entry with only `events` is
   rejected. `status`/`tested`/`reason` map straight across from v1;
   `gap.upstream_checked`/`gap.behavioural_impact` nest under `gap`,
   mirroring the v1 `implementation.gap` shape.
2. **Parity-only identity**:
   ```jsonc
   "reference_identities": [
     {"reference_id": "...", "provenance_source": "...",
      "historical_passcode": ..., "historical_variant_passcodes": [...],
      "upstream": "...", "script": "..."}
   ]
   ```
   New top-level array on `ErratumV2` (full v2 AND sugar — orthogonal to
   event shape), validated with the SAME passcode/sources machinery
   `Coverage` already uses, consumed by `reference_parity` format
   resolution as a fact that bypasses `Coverage` rather than living inside
   it, per the frozen precedence above.

Both are additive, optional, and orthogonal to every existing v2 field.

---

## 6. Exact changes this task implemented

**Schema (`schemas/erratum.schema.json`, `schemas/format.schema.json`)**

- New `$defs`: `implementationMetadataEntry` (required `events`,
  `minProperties: 2`; optional `status`/`tested`/`reason`/`gap`) and
  `referenceIdentity` (required `reference_id`/`provenance_source`/
  `historical_passcode`/`upstream`; optional `historical_variant_
  passcodes`/`script`).
- `implementation_metadata`/`reference_identities` array properties added
  to BOTH `erratumV2` and `erratumV2Sugar` — sugar support was resolved to
  YES (task section 2): without it, the 180 sugar-eligible records could
  not carry their baseline `status`/`tested` metadata and sugar would stop
  being a genuine 1:1 shape for them.
- `format.schema.json`'s `reference_parity` gains an optional
  `reference_id` string property.
- v1's `erratumV1`/`implementation` shape is untouched — neither array is
  added there; v1 keeps its existing inline fields exactly as they are.

**Runtime (`retroformats/model.py`)** — implemented

- Two new frozen dataclasses, following the existing `HistoricalTransition`/
  `ImplementationCoverage` pattern (`.from_raw()` classmethod, thin, no
  computed logic beyond parsing): `ImplementationMetadata` (`events`,
  `status`, `tested`, `reason`, `gap_upstream_checked`,
  `gap_behavioural_impact`, `raw`) and `ReferenceIdentity` (`reference_id`,
  `provenance_source`, `historical_passcode`,
  `historical_variant_passcodes`, `upstream`, `script`, `raw`).
- `ErratumV2` gains `implementation_metadata: dict[frozenset[str],
  ImplementationMetadata]` and `reference_identities: tuple[
  ReferenceIdentity, ...]`, parsed in `.load()` alongside — never merged
  into — `authored_states`. A new `metadata_for(down_set)` accessor mirrors
  `state_for()` but performs NO synthesis: absence returns `None`, never a
  default.
- `_desugar_v2_sugar()` needed no change at all: both new top-level keys
  already pass through its existing "copy every key except `event`/
  `coverage`" behaviour.
- No change to `_state_for()`, `selection_at()`, `structural_states()`, or
  `_reachable_down_sets()` — verified by a dedicated test
  (`test_metadata_never_changes_coverage_or_selection`) that strips
  `implementation_metadata` from a real candidate and confirms
  `selection_at()`'s output is byte-identical either way.

**Validator (`retroformats/validate.py`)** — implemented

- `_validate_v2_implementation_metadata()`, mirroring `_validate_v2_
  states()` exactly: unknown/non-relevant event ids
  (`erratum.metadata-unknown-event`/`erratum.metadata-non-relevant-event`),
  duplicate down-set keys including permutations
  (`erratum.metadata-duplicate-key`), unreachable down-sets
  (`erratum.metadata-unreachable`, reusing `structural_states()`),
  repeated ids within one `events` array
  (`erratum.metadata-events-duplicate`, in `_validate_v2_shape()`
  alongside the existing `states[]` version of the same check), an entry
  with no field besides `events` (`erratum.metadata-empty`), and bad
  `status`/`tested`/`reason`/`gap` types
  (`erratum.metadata-bad-status`/`erratum.metadata-bad-type`/
  `erratum.metadata-bad-gap`). **No cross-array warning** for a state
  present in one array but not the other (task section 10) — the two are
  deliberately independent, and absence is never an error.
- `_validate_v2_reference_identities()`: unique `reference_id`
  (`erratum.reference-identity-duplicate-id`), `provenance_source`
  resolves through the source registry AND appears in the record's own
  `sources` (`sources.unresolved`/`erratum.reference-identity-provenance-
  not-in-sources`), strict passcode/variant validation via the existing
  `_safe_passcode()`/`_check_card_alias()`, the +/-10 artwork-variant rule,
  `historical_passcode != modern_card.passcode`
  (`erratum.reference-identity-matches-modern`), required `upstream`.
- `_validate_v2_parity()` now threads `fmt.reference_parity` through to
  `parity_override()` and surfaces any fail-safe problem (malformed match,
  or `provenance_source` mismatch) as `erratum.reference-identity-invalid`
  — the format-specific consumption check, distinct from the record-level
  well-formedness checks above.

**Consumers (`retroformats/lflist.py`)** — implemented

- `implementation_metadata[]`: no consumer change — descriptive only,
  confirmed by the same selection-equivalence test above.
- `SelectedOverride.implementation` widened to a THREE-way union: `dict |
  ImplementationCoverage | ReferenceIdentity` — never a fake `Coverage` or
  fake v1 dict. `historical_identity()` gained a third `isinstance`
  branch, reading a `ReferenceIdentity` through the same strict,
  non-coercive `_is_valid_passcode()` lens as the other two; the whitelist
  builder itself needed zero changes (it only ever calls
  `historical_identity(override.implementation)`).
- `_v2_parity_walk_override()`/`parity_override()` gained an optional
  `parity`/`problems` parameter and a new `_reference_identity_override()`
  helper implementing the frozen precedence above, with a `_NO_REFERENCE_
  ID_MATCH` sentinel distinguishing "no match, fall through" from "matched
  but invalid, fail safe" — `None` alone could not carry that distinction,
  since it is also the walk's own "nothing found" result.

**Migration tooling (`tests/migration_audit.py`)** — implemented

- `_implementation_metadata_from_v1()` maps one v1 implementation OBJECT's
  workflow fields onto an `implementation_metadata[]` entry;
  `candidate_v2()` builds both `states[]` and `implementation_metadata[]`
  from the SAME per-version v1 implementation object, independently (a
  version can produce a `states[]` entry, a metadata entry, both, or
  neither).
- `derive_reference_identities(record, repo)` computes candidate
  `reference_identities[]` entries FROM THE REPOSITORY'S OWN format
  policies (never a hard-coded `"project-ignis-goat"` string) — for every
  format whose `reference_parity` declares a `reference_id` and actually
  consumes this record via the real `parity_override()` resolution, scoped
  to records with zero relevant events (the 11 parity-only records
  specifically; a record with relevant events already has a working
  Coverage-based representation, so this migration tooling does not also
  emit a redundant entry for it, even though the runtime/validator allow
  one).
- `metadata_inventory()`'s `has_v2_destination`/`would_be_lost_on_
  migration` now reflect the real destination: all five known fields
  (`status`/`tested`/`reason`/`gap.upstream_checked`/`gap.behavioural_
  impact`) report `has_v2_destination: True` — a genuinely unrecognised
  future field would still report `False`.
- `_metadata_preserved()`/`_reference_identity_preserved()` — new,
  independent preservation checks (re-deriving expectations from the raw
  v1 record, then checking the REAL parsed candidate, exactly like the
  existing `_coverage_preserved()`), wired into `_data_preserved()`
  alongside it. Mutation tests (dropped `status`, wrong reference-identity
  passcode) confirm both have real teeth.
- **Result, confirmed by `audit_corpus()`**: `metadata_unrepresented_
  count == 0`, `parity_only_unrepresented_count == 0`, every one of the
  247 semantically-equivalent records' `data_preserved` is `True` — **and
  247/49/48 are unchanged**, because none of this touches equivalence
  logic at all.

No canonical `data/errata/*.json` record changes — the gap was in the v2
REPRESENTATION, not in v1 data, which remains exactly as it was.

---

## 7. Migration sequencing — representation is ready; migration has not started

1. ~~Design review and decision~~ **done** — the `reference_id` correction
   in section 3 was made before implementation, not after.
2. ~~Implement the schema/runtime/validator/consumer changes~~ **done**,
   in this same task, as one atomic commit alongside this document's
   corrections — not bundled with any canonical data migration.
3. ~~Re-run `tests/migration_audit.py`'s candidate construction~~ **done**
   — `metadata_unrepresented_count`/`parity_only_unrepresented_count` are
   both `0`, confirmed mechanically, not by inspection.
4. **Canonical migration itself has NOT begun**, and remains gated on a
   separate, later decision to start it. Once it does, the design
   document's §13 sequence applies, now genuinely data-preservation-ready
   rather than merely chronology/shape-ready, for **all 247** semantically
   equivalent records — not only 236:
   - the 180 sugar-eligible + 35 single-relevant-with-siblings + 11
     fully-ordered records (step 4), migrating WITH their
     `implementation_metadata`/`reference_identities` fields populated;
   - the 11 parity-only records migrate alongside step 4 (no longer a
     separate blocked step): each becomes a full-v2 record with its
     cosmetic/engine events, no `states[]` (zero relevant events — nothing
     for `states[]` to describe), `implementation_metadata[]` for any
     workflow fields it carries, and exactly the one `reference_identities[]`
     entry this task's tooling already derives and verifies;
   - the **10 pure cosmetic/engine, no-historical-state records** — an
     earlier version of this document's migration list omitted them
     entirely. They migrate the same shape as the 11 parity-only records
     minus `reference_identities[]` (nothing to reference — no format
     substitutes them at all): `events{}` for their cosmetic/engine
     chronology nodes, `ordering` proven where the dates allow it, no
     `states[]` (zero relevant events), `implementation_metadata[]`
     preserving whatever workflow metadata they carry;
   - the 47 already-researched unordered records (step 5);
   - the 2 manual-review records (step 6), after their order question is
     separately resolved by a human, unaffected by either representation
     gap.

**Full accounting of the 247**: 180 + 35 + 11 (fully-ordered) + 11
(parity-only) + 10 (pure cosmetic/engine) = 247. Every one of them now has
a verified-preserving v2 representation available; none has actually been
migrated.
