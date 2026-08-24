# v1 → v2 errata migration audit

**Status: pre-migration. No canonical record has been migrated.**

Every number below is DERIVED by `tests/migration_audit.py` from the runtime
as implemented today, and re-derived on every test run by
`tests/test_migration_audit.py`. Nothing here is carried forward from the
earlier pass — the previous "247 safe" figure was deliberately *not* used as
an input, and it did not survive as an output. The machine-readable form of
this report is `erratum-v2-migration-audit.json` beside this file.

Re-run with:

```bash
python -m tests.migration_audit
```

## Why this had to be re-derived

Commit `a114ee3` corrected v2 selection to:

> ALL events participate in chronology/order consistency, THEN the result is
> projected onto functional/ruling event ids for implementation state.

The design document still said cosmetic/engine events were *filtered out
before* down-set reasoning. That was false in the implemented runtime, and it
matters: a cosmetic/engine-only event never appears in a `HistoricalState`'s
identity, but it still happened-or-didn't at a snapshot, so it can force a
relevant predecessor to have occurred, or forbid a relevant successor —
through the ordering DAG. Any equivalence claim made under the old reading
therefore had to be proved again, not assumed.

## What the audit does

Per v1 record, it builds the candidate v2 record migration would produce:

- **one event per `changes[]` entry, including cosmetic and engine ones** —
  every historical change is a chronology node even when it creates no
  implementation-state dimension;
- **event ids are opaque labels.** Array position is never ordering
  evidence; `c0` preceding `c1` in the file asserts nothing;
- **co-occurrence is never invented.** *n* changes become *n* separate
  events, never one bundled event;
- **`ordering` edges only where `ordering_proof()` returns PROVEN** from the
  two events' own chronology, checked over every ordered pair in both
  directions;
- **`states[]` maps v1's positional version chain onto event down-sets.**
  v1's semantics *are* positional, so reading them is faithful to what the
  record asserts about implementations — and it is used only for coverage,
  never as ordering evidence.

It then compares v1 selection against candidate-v2 selection at **every
chronology boundary the record can have**. The enumeration is exact and
finite, not sampled: each event's OLD/AMBIGUOUS/NEW status is piecewise
constant, changing only at the handful of dates its own evidence names, so
probing each named date (and the day either side) covers every
distinguishable snapshot.

## The derived partition

| category | count | what it means for migration |
|---|---:|---|
| `sugar-eligible` | **180** | exactly one event in total, and it is functional/ruling — the flattened sugar shape fits |
| `full-v2-single-event` | **35** | one *relevant* change, but cosmetic/engine changes beside it, so 2+ events |
| `full-v2-multi-event-ordered` | **17** | 2+ relevant events with at least one date-PROVEN ordering edge |
| `full-v2-multi-event-unordered` | **43** | 2+ relevant events, no ordering provable from chronology |
| `parity-only-identity` | **11** | zero relevant events, yet a usable historical passcode — **BLOCKERS**, see below |
| `no-historical-state` | **10** | zero relevant events and no historical identity — pure cosmetic/engine records |
| **total** | **296** | |

**Mechanical equivalence: 296 of 296.** Every record's v1 selection and its
candidate-v2 selection agree at every boundary. That is stronger than the old
claim, and it is a derived result, not an assumption.

### Why equivalence comes out total — and why that is not a blind spot

The migration emits *only* date-proven ordering edges, and such an edge can
never add a constraint the two events' own statuses do not already impose:

> If `before < after` is date-proven, then `first_confirmed_new(before) ≤
> last_confirmed_old(after)`. So at any snapshot where `after` is NEW,
> `before` is already NEW; and at any snapshot where `before` is OLD, `after`
> is already OLD.

`tests/test_migration_audit.py::ProvenEdgesAddNoConstraintTest` asserts this
exhaustively over a grid of exact/month/year/bounded/undated chronologies at
165 probe dates per ordered pair. Full-event down-set reasoning and
relevant-only reasoning therefore cannot diverge *for a migrated record*.

The corresponding risk is that the comparison is simply insensitive. It is
not: `AuditSensitivityTest` constructs a record where full-event semantics
genuinely differ — a cosmetic event confirmed NEW, ordered after an undated
relevant event by a **researcher-inference** edge — and shows v1 says
`ambiguous` where v2 says `modern`, with the audit's own comparison detecting
it. The difference is reachable; migrated records just never create the
non-date-proven edges that reach it.

### The audit is not vacuous

Sensitivity was also checked by mutation: deliberately breaking the migration
and requiring the audit to notice.

| deliberate defect | records detected as non-equivalent |
|---|---:|
| ordering copied from `changes[]` array position (the shortcut this task forbids) | **58 of 296** |
| `states[]` version chain shifted by one | 8 of 296 |

The first is the important one: it both proves the comparison has teeth and
quantifies the harm of the forbidden shortcut — inferring order from array
position would change selection behaviour for 58 records.
`AuditIsNotVacuousTest` keeps that guarantee.

**Consequence for the design document's corrected rule:** cosmetic/engine
events participating in chronology is real and observable, but it can only
change an outcome through an ordering edge that chronology does not itself
prove. Migration never authors one.

## The 11 parity-only identity records — migration BLOCKERS

These v1 records have **no implementation-relevant changes** yet carry a
usable historical passcode, because Project Ignis's reference list ships an
old card entry for *period text* even where behaviour is identical:

| record | classification | historical passcode |
|---|---|---:|
| `erratum-bubble-crash` | cosmetic | 504700100 |
| `erratum-chaosrider-gustaph` | cosmetic | 504700078 |
| `erratum-cipher-soldier` | cosmetic | 504700139 |
| `erratum-dark-jeroid` | cosmetic | 504700159 |
| `erratum-injection-fairy-lily` | cosmetic | 504700138 |
| `erratum-kazejin` | cosmetic | 504700101 |
| `erratum-mirage-knight` | cosmetic | 504700080 |
| `erratum-nobleman-of-crossout` | cosmetic | 504700116 |
| `erratum-nobleman-of-extermination` | cosmetic | 504700025 |
| `erratum-shinato-king-of-a-higher-plane` | cosmetic | 504700148 |
| `erratum-suijin` | cosmetic | 504700174 |

All eleven are `reuse-upstream`, all cite `ignis-lflists`, and **all eleven
are consumed today** by `2005-04-goat` through its `reference_parity` policy.

**Current output depends on them.** Dropping their historical identity
changes the generated GOAT list: 11 historical codes disappear and the 11
corresponding modern codes appear in their place, breaking the entry-for-entry
parity with Project Ignis's `GOAT.lflist.conf` that
`tests/test_repo_data.py::test_goat_matches_ignis_reference` asserts. Edison
is unaffected (0 codes changed).

### The minimum representation problem

v2 as frozen **cannot store this identity as ordinary state coverage**:

1. a cosmetic/engine-only record has zero implementation-relevant events;
2. so its only structural state is `{}`;
3. so `{}` *is* the terminal (all-relevant-events) state;
4. so its coverage is unconditionally synthesised as `MODERN`, and any
   authored `reuse-upstream` coverage on `{}` is discarded;
5. so `_v2_parity_walk_override()` can never find a usable override on such a
   record.

`ParityOnlyIdentityIsUnrepresentableTest` asserts each step. This is not a
bug in the runtime — it follows directly from the frozen rule that
cosmetic/engine events create no implementation-state dimension, which is
correct. It means parity-only historical identity is a **different kind of
fact** from state coverage: it is "which card entry the reference list uses
for this card", not "how this card behaved in some era".

**No new schema field is proposed here.** Per the task's scope, inventing a
`parity_variant` field without review is out of bounds. These 11 records are
recorded as blockers: migrating them without first deciding how parity-only
identity is represented would silently discard canonical historical identity
data *and* break GOAT parity.

## Reconciliation with the previous audit's numbers

| previous figure | reproducible now? | what the evidence says |
|---|---|---|
| **247 "mechanically equivalence-safe"** | **No — superseded** | Equivalence is now **296/296**. But 247 was also used as "records that can use single-event sugar", and *that* reading drops to **180**. |
| **236 trivial** | Yes, as "≤ 1 relevant change" | 236 records have at most one relevant change. Under full-event semantics 35 of them still have cosmetic/engine events beside it, and 21 have no relevant change at all — so only 180 are single-event. |
| **11 ordered multi-event** | **No — now 17** | 17 records with 2+ relevant events have at least one date-PROVEN edge; 43 have none. The old 11/49 split is superseded by 17/43. |
| **49 order-aware/nontrivial** | Arithmetically (296 − 247), not structurally | The structurally meaningful figure is **60** records with 2+ relevant events. Coincidentally, 49 is also the number of records that are ambiguous-with-modern-excluded at some boundary — a *different* 49, and treating the two as the same number would be an error. |
| **48 "self-contradictory candidate" symptom** | **Not reproducible** | No natural definition reproduces 48. Nearby measurements: 49 records ambiguous-with-modern-excluded at some boundary; 46 at either format snapshot; 46 at GOAT; 44 at Edison. Recorded as unresolved rather than matched to a convenient figure. |

### Are 48 and 49 exhaustive for their old meanings?

**No.** Under the implemented full-event model, neither set exhausts the
migration-relevant exceptions:

- the **11 parity-only blockers** appear in neither set — they have zero
  relevant changes, so no order-aware taxonomy would have caught them, and
  they are not ambiguity symptoms;
- the **35 records with one relevant change but extra cosmetic/engine
  events** are sugar-ineligible under full-event semantics, and were counted
  as trivially-safe before;
- the ordered/unordered split itself moved (11/49 → 17/43) once ordering was
  derived from `ordering_proof()` rather than assumed.

Equivalence, however, is *broader* than previously claimed: all 296 records
migrate without changing any selection outcome.

## What is safe to migrate, and what is not

- **Safe, mechanically equivalent: 296/296** — no record's selection changes.
- **Blocked on a representation decision: 11** parity-only identity records,
  because migrating them as-is would discard the identity and break GOAT
  parity.
- **Shape guidance:** 180 sugar, 105 full v2 with authored states
  (35 + 17 + 43 + 10), 11 pending the parity decision.

Equivalence is necessary but not sufficient: a record can migrate without
changing behaviour and still lose data, which is exactly what the 11
blockers demonstrate.
