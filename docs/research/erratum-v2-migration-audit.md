# v1 → v2 errata migration audit

**Status: pre-migration. No canonical record has been migrated.**

Every number below is DERIVED by `tests/migration_audit.py` from the runtime
as implemented today, and re-derived on every test run by
`tests/test_migration_audit.py`. The machine-readable form of this report is
`erratum-v2-migration-audit.json` beside this file.

Re-run with:

```bash
python -m tests.migration_audit
```

## Correction: the previous pass's "296 of 296" was wrong

The prior version of this audit compared v1 and candidate-v2 outcomes by
reducing a v2 ambiguous candidate to `len(candidate.events)` and comparing
that INTEGER against v1's positional candidate index. That is invalid: it
silently equates two different historical states whenever they happen to
have the same number of events — `{verification-event}` and
`{activation-event}` both have length 1, so the old comparator called them
the same state even though they are not. It produced a false 296-of-296
equivalence claim and a false "247 does not survive" conclusion.

**The corrected comparator does a genuine SET comparison** of
`(event-identity, coverage-signature)` pairs — `{A}` and `{B}` compare
unequal even when both have size 1 — and it changes the headline result:

| | previous (wrong) pass | this pass |
|---|---:|---:|
| Mechanically equivalent | 296 of 296 | **247 of 296** |
| Not equivalent | 0 | **49** |

`CardinalityCollapseRegressionTest` in `tests/test_migration_audit.py` pins
the exact shape of the old bug (`{A}` vs `{B}`, equal size, must compare
unequal) so it cannot silently return.

**This is not a new, unrelated finding — it exactly reproduces the frozen
design document's own numbers**, computed independently by this corrected
comparator rather than assumed as an input:

| figure | design doc (`erratum-state-model-v2.md` §3/§7) | this audit, derived |
|---|---:|---:|
| Mechanically equivalent / safe | 247 | **247** ✓ |
| Not equivalent / order-aware migration needed | 49 | **49** ✓ (same 49 ids) |
| Self-contradictory legacy symptom | 48 | **48** ✓ (same 48 ids) |
| Trivial (0–1 relevant changes) | 236 | **236** ✓ |
| Genuinely, exactly, exhaustively ordered | 11 | **11** ✓ (same 11 ids, by name) |
| Sole record in the 49 not in the 48 | YZ-Tank Dragon | **YZ-Tank Dragon** ✓ |

Five independently-checked figures, all exact. This does not "prove" either
computation correct in isolation, but it is strong convergent evidence: the
design document's hand-worked analysis (§3's per-record proofs, §7's exact
boundary test) and this audit's from-scratch, code-derived comparator were
built independently and landed on the same partition, down to the specific
record ids.

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
  record asserts about implementations — used only for coverage, never as
  ordering evidence;
- **historical_text/modern_text/summary/sources are carried across
  verbatim** — `_data_preserved()` checks this independently of the outcome
  comparison, so a migration that got the executable behaviour right but
  silently dropped documentation would still be caught;
- **no field the v2 coverage schema requires is fabricated.** A v1
  implementation missing `upstream`/`script`/`gap.reason`/`gap.sources`
  raises `MigrationDataMissing` rather than substituting a plausible-looking
  default. No record in the corpus exercises this path today (verified by
  scan and by the audit run itself — 0 records hit it), but the tool does
  not depend on that staying true.

It then compares v1's CLAIMED semantic states against v2's REAL semantic
states at **every chronology boundary the record can have**. "Claimed"
means: v1's positional label `k` asserts that the first `k` relevant changes
(array order) occurred and the rest did not — restated in v2's event-id
vocabulary purely so the two are comparable; this does **not** turn array
order into v2 ordering evidence, it only asks what the legacy label meant,
then checks whether v2's real, chronology-and-structure-derived candidate
set actually contains that state, with the same coverage. The enumeration of
boundaries is exact and finite, not sampled: each event's OLD/AMBIGUOUS/NEW
status is piecewise constant, changing only at the handful of dates its own
evidence names, so probing each named date (and the day either side) covers
every distinguishable snapshot.

Separately, the audit implements design doc §7's **exact** self-contradiction
test, not an approximation of it: v1's own positional candidate `k` at a
snapshot is self-contradictory if it claims a transition occurred that is
independently confirmed OLD, or claims one has not occurred that is
independently confirmed NEW. This is a different question from equivalence
— YZ-Tank Dragon is not equivalent (49) yet never self-contradictory (not in
the 48), because its problem is *incompleteness* (v1's model cannot express
a real state at all), not a false claim.

## The derived partition

| category | count | what it means for migration |
|---|---:|---|
| `sugar-eligible` | **180** | exactly one event in total, and it is functional/ruling — the flattened sugar shape fits |
| `full-v2-single-event` | **35** | one *relevant* change, but cosmetic/engine changes beside it, so 2+ events |
| `full-v2-multi-event-ordered` | **11** | 2+ relevant events, structurally a single total chain — v1's linear model and v2's real chronology agree at every boundary |
| `manual-review-blocker` | **49** | 2+ relevant events, not fully ordered — v1's positional label and v2's real chronology genuinely disagree at some boundary; needs order-aware migration, not a rename |
| `parity-only-identity` | **11** | zero relevant events, yet a usable historical passcode — a **separate, independent BLOCKER** (see below); trivially "equivalent" in the weak sense (both sides always select modern), which is exactly why equivalence alone does not certify safety |
| `no-historical-state` | **10** | zero relevant events, no historical identity — pure cosmetic/engine, nothing to preserve |
| **total** | **296** | |

**Ordering structure** (never "has any proven edge" — a 3-event partial
order would have one without being total):

| structure | count |
|---|---:|
| `zero-relevant` (0 relevant events) | 21 |
| `single-event` (exactly 1 relevant event) | 215 |
| `fully-ordered` (relevant down-sets form one total chain) | 11 |
| `no-proven-ordering` (relevant down-sets form the full power set) | 49 |
| `partial-order` | 0 (none in the current corpus) |

Every one of the 49 `no-proven-ordering` records is also the 49
`manual-review-blocker` records — in the current corpus, "not fully ordered"
and "not equivalent" coincide exactly (see `test_ordering_structure_never_
conflates_any_edge_with_fully_ordered`, which checks this is a fact about
the data, not an assumption the code makes).

## Why the 49 are not equivalent — the actual mechanism

v1's positional model over *n* relevant changes offers exactly `n + 1`
candidates: the array prefixes `{}`, `{first}`, `{first,second}`, …,
`{all}`. When the events are NOT provably totally ordered, v2's real
down-set space is larger than `n + 1` — up to the full power set, `2^n` — so
v1's linear model both (a) cannot express states outside its `n + 1`
prefixes, and (b) can claim a prefix that is independently disprovable once
each transition's own chronology is checked directly, rather than only in
aggregate.

**Worked example — Giant Rat, at Edison (2010-04-24).** Two relevant
ruling changes: *verification* (bounded chronology, confirmed OLD — has not
occurred — at Edison, since `old_attested_through` is 2011-02-02) and
*activation* (fully undated, permanently ambiguous). v1's positional label
`1` claims the FIRST-listed change — verification — occurred. But
verification's own status at Edison is independently confirmed OLD: v1's
claim is not merely unproven, it is impossible. v2's real chronology instead
proves the only plausible non-baseline state is `{activation}` — the
opposite candidate. Both are singletons (same cardinality), different
identity: exactly the bug the corrected comparator exists to catch. Giant
Rat is one of the 48 (self-contradictory) as well as the 49 (not
equivalent).

**Worked example — YZ-Tank Dragon, permanently.** Two relevant changes
(contact-fusion material zone; nomi-vs-semi-nomi condition), both entirely
undated on both sides — `change_state_at()` returns AMBIGUOUS forever, so no
transition's status is ever independently confirmable either way. v1's
positional label can therefore never be *disproven* — YZ-Tank Dragon is
**not** one of the 48. But v1's three candidates (`{}`, `{material-rule}`,
`{material-rule,summon-rule}`) were never the full state space: two
genuinely unordered events admit the full power set, `{}`, `{material-
rule}`, `{summon-rule}`, `{material-rule,summon-rule}` — four states, and
v1's array-prefix model structurally cannot name `{summon-rule}` alone at
all, correct or not. This is YZ-Tank Dragon's real defect: not a wrong
answer, an *incomplete* one. It is the sole record in the 49 that is not in
the 48 (`test_yz_tank_dragon_is_the_sole_49_minus_48_exception`).

**Worked example — Sangan, Witch of the Black Forest.** Both fully dated
(no undated events at all) and *still* not fully ordered: Sangan's ruling
change has a bounded attestation window (2011-02-02 .. 2019-04-03) that
overlaps neither direction against its functional change's exact date
(2016-09-15) — `ordering_proof()` returns INCONCLUSIVE both ways. Being
dated does not imply being ordered; `ordering_structure` — not
`proven_edge_count`, which can be nonzero from an unrelated cosmetic
sibling — is the correct check (`SanganAndWitchWorkedExamplesTest`).

**Worked example — Necrovalley, the safe fully-ordered case.** Four
relevant functional changes, every one exactly dated to a distinct day —
every pair is directly date-comparable, so `structural_state_count` is
exactly `5 = 4 + 1`, a single total chain. `ordering_structure` is
`fully-ordered`, and the record is equivalent: v1's linear model and v2's
real chronology agree at every boundary, because there is only one
chronologically-consistent chain to agree on.

**A safe one-change (sugar-eligible) record — any of the 180.** With a
single relevant event and no siblings, v1's two candidates (`{}`, `{that
event}`) and v2's two structural down-sets are the same two sets by
construction; there is no room for the two models to diverge.

## Why this had to be re-derived at all

Commit `a114ee3` corrected v2 selection so that ALL events — not only
relevant ones — participate in chronology and order consistency, with only
functional/ruling events surviving the projection into a `HistoricalState`'s
identity. The design document previously claimed cosmetic/engine events
were filtered out *before* down-set reasoning; that was false in the
implemented runtime. `AuditSensitivityTest` exhibits a record — built with a
researcher-INFERENCE edge, which `candidate_v2()` itself never emits — where
this genuinely changes the answer: a cosmetic event's confirmed-NEW status
collapses an otherwise-ambiguous relevant event to a single determinate
state.

**This correction did not, on its own, cause the 49 mismatches above.**
`ProvenEdgesAddNoConstraintTest` proves exhaustively that a date-*proven*
edge — the only kind `candidate_v2()` ever emits — can never add a
constraint beyond what the two events' own independently-computed statuses
already impose. The 49 mismatches come entirely from a different mechanism:
v1's positional model asserting a specific array-prefix state that v2's
real (possibly unordered) chronology either cannot express or can disprove
directly — the Giant Rat / YZ-Tank Dragon mechanism above, not the
full-event-participation correction. The two corrections are orthogonal;
conflating them was part of what the previous (wrong) 296-of-296 pass got
wrong.

## The audit is not vacuous

Two independent mutation tests, per this task's required adversarial
checks: deliberately break the migration in a specific forbidden way and
require the comparator to detect *more* non-equivalence than the genuine,
already-present 49.

| deliberate defect | records detected as non-equivalent |
|---|---:|
| baseline (no mutation) | 49 |
| ordering copied from `changes[]` array position (forbidden shortcut C) | **58** |
| `states[]` coverage shifted by one event (forbidden shortcut D) | **55** |

Both mutations break strictly more records than the real, unmutated
migration — proving the detection power is real, not merely inherited from
records that were already flagged. `CardinalityCollapseRegressionTest`
additionally proves the comparator would have caught its own prior bug
(equal-cardinality, different-identity states compare unequal), directly on
Giant Rat's real data.

## The 11 parity-only identity records — a SEPARATE, independent BLOCKER

**Selection equivalence does not imply migration-data-preserving safety —
these 11 prove it.** Each has **zero implementation-relevant changes** yet
carries a usable historical passcode, because Project Ignis's reference list
ships an old card entry for *period text* even where behaviour is identical.
Because they have no relevant events, both v1 and v2 select "modern" at
every boundary — they are counted in the 247 "equivalent" above — but that
equivalence is about *selection*, not about *what identity survives being
authored in v2 at all*.

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
are consumed today** by `2005-04-goat` through its `reference_parity`
policy. Dropping their historical identity changes generated output: 11
historical codes disappear from GOAT's list and the 11 corresponding modern
codes appear in their place, breaking entry-for-entry parity with Project
Ignis's `GOAT.lflist.conf`. Edison is unaffected (0 codes changed) —
re-verified this pass, unchanged from the prior finding.

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
bug — it follows directly from the frozen rule that cosmetic/engine events
create no implementation-state dimension, which is correct. It means
parity-only historical identity is a **different kind of fact** from state
coverage: "which card entry the reference list uses for this card," not "how
this card behaved in some era."

**No new schema field is proposed here.** Migrating these 11 as-is would
silently discard canonical historical identity data *and* break GOAT
parity. How parity-only identity should be represented remains an explicit
open decision.

## Data preservation and no-fabrication (task objective 7)

- **`_data_preserved()` checked for all 296 records: 0 failures.**
  `historical_text`/`modern_text`/`summary`/`sources` survive candidate
  construction verbatim for every record, not merely the executable
  strategy.
- **`_coverage_from_v1()` fabricates nothing.** The prior pass's fallback
  defaults (`upstream or "ProjectIgnis"`, `script or "dist/scripts/unknown
  .lua"`, `gap.reason or "unspecified"`, `gap.sources or ["ignis-babelcdb"]`)
  are removed; a v1 implementation missing a field v2's coverage schema
  requires now raises `MigrationDataMissing` and is reported as
  `manual-review-blocker` rather than migrated with an invented value. A
  corpus scan (and the audit run itself) confirms 0 of the 296 records
  exercise this path today — this is a robustness fix for future records,
  not a change to any current classification.

## Malformed-identity hardening (task objective 8)

5f7d2da fixed `historical_passcode=None`. A **present but non-integer or
out-of-range** value (a typo, or a passcode outside the schema's 1..
4294967295) was still not fully fail-safe:

- `ImplementationCoverage.from_raw()` keeps the field RAW, and production
  validation did `int(hist)`/`int(variant)` with no guard — a crash inside
  the validator itself, not a reported finding.
- `_usable_v2()`/`_malformed_substitution()`/`_executable_outcome()` treated
  any non-`None` value as usable, so a malformed identity could be selected
  as the chosen override and reach `historical_identity()` unguarded,
  raising `MalformedHistoricalIdentity` — the correct exception type, but
  uncaught outside `select_applicable_errata()`'s problem-reporting path.
- v1's own `Erratum.selection_at()` had the same gap: a non-integer
  `historical_passcode` still produced `state="historical"`, bypassing the
  existing safe "no usable passcode → gap" fallback that a *missing*
  passcode already triggers.

All three are now closed by one shared authority, `_is_valid_passcode()`
(schema's `passcode` def: integer, 1..4294967295) in `model.py`, used by
`lflist.py`'s selection functions, `validate.py`'s `_safe_passcode()` guard
(replacing every unguarded `int(...)` call, v1 and v2 alike), and this
audit's own `_v1_coverage_signature`/`_v2_coverage_signature`. A malformed
passcode is now handled identically to a missing one everywhere: the
validator reports `erratum.malformed-passcode` and continues; a direct
build (no validator run first) fails as `ErrataSelectionError`, never a bare
`ValueError`/`TypeError`/`MalformedHistoricalIdentity`; v1's `selection_at()`
falls back to its existing `"gap"` state.

## What is safe to migrate, and what is not

- **Mechanically equivalent (selection never changes): 247 of 296** — 180
  sugar-eligible, 35 single-relevant-with-cosmetic-siblings, 11
  fully-ordered multi-event, 11 parity-only, 10 pure cosmetic/engine.
- **Blocked on order-aware research, not equivalent: 49 of 296** — v1's
  positional label and v2's real chronology genuinely disagree at some
  boundary for these records; migrating them as a rename would be wrong,
  not merely imprecise. Exact ids in `erratum-v2-migration-audit.json`'s
  `not_equivalent_ids`.
- **Blocked on a representation decision, independent of equivalence: 11**
  parity-only identity records — equivalent in selection, but v2 as frozen
  cannot store the identity at all.
- **Self-contradictory under the legacy schema (informational, not a
  blocker by itself): 48 of the 49** — the specific symptom of v1's model
  actively asserting a false answer, as opposed to YZ-Tank Dragon's
  incompleteness. All 48 are already inside the 49.

Equivalence is necessary but not sufficient for safe migration: the 11
parity-only records are equivalent yet still blocked, exactly the
distinction the previous pass's "everything is 296/296, ship it" framing
would have missed even if the comparator bug had not existed.
