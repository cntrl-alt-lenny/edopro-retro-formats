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
| `researched-nontrivial` | **47** | 2+ relevant events, not fully ordered, not equivalent — needs order-aware migration, but ALREADY has a documented research classification (design doc §7's 38 bundled + 9 mechanically-distinct; the finer split between those two has no computable signal in the data and is not reproduced here) |
| `manual-review-blocker` | **2** | the same non-equivalence, but blocked on an actual HUMAN decision — `erratum-insect-imitation`, `erratum-last-will`, named explicitly in design doc §7 as needing a researcher-inferred order to be reviewed before any `ordering` edge can be authored |
| `parity-only-identity` | **11** | zero relevant events, yet a usable historical passcode — a **separate, independent BLOCKER** (see below); trivially "equivalent" in the weak sense (both sides always select modern), which is exactly why equivalence alone does not certify safety |
| `no-historical-state` | **10** | zero relevant events, no historical identity — pure cosmetic/engine, nothing to preserve |
| **total** | **296** | |

**The 49 not-equivalent records are not uniformly "manual review."** A
prior pass's category collapsed all 49 into one `manual-review-blocker`
label, which overstates the blocker: 47 of them already have a documented
research classification (they need an order-aware migration script, not
more research), and only 2 are genuinely awaiting a human decision. Three
orthogonal fields on every row make this explicit without forcing one
overloaded label to carry all of it: `research_status`
(`not-applicable`/`already-researched`/`needs-manual-review`),
`migration_complexity` (`trivial-rename`/`proven-chain`/`unordered-
researched`/`unordered-manual-review`/`parity-only-blocked`/`no-historical-
state`), and `ordering_structure`.

**Ordering structure** (never "has any proven edge" — a 3-event partial
order would have one without being total):

| structure | count |
|---|---:|
| `zero-relevant` (0 relevant events) | 21 |
| `single-event` (exactly 1 relevant event) | 215 |
| `fully-ordered` (relevant down-sets form one total chain) | 11 |
| `no-proven-ordering` (relevant down-sets form the full power set) | 49 |
| `partial-order` | 0 (none in the current corpus) |

Every one of the 49 `no-proven-ordering` records is also one of the 49
not-equivalent records (47 `researched-nontrivial` + 2 `manual-review-
blocker`) — in the current corpus, "not fully ordered" and "not equivalent"
coincide exactly (see `test_ordering_structure_never_
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

## Data preservation and no-fabrication (task objective 1)

**Corrected pass: the previous "0 failures" claim was checking too little.**
`_data_preserved()` verified `historical_text`/`modern_text`/`summary`/
`sources` on transitions but not coverage fields at all — `_coverage_from_v1
()` silently dropped `script` on `reuse-upstream` coverage, even though the
schema's `coverageReuseUpstream` explicitly allows it as optional. Giant
Rat's baseline implementation is the concrete counterexample the task names
(`historical_passcode: 504700172`, `upstream: ...`, `script:
"goat/c504700172.lua"` — only the first two survived migration). This was
not a one-off: **242 of 242 `reuse-upstream` implementations in the corpus
carry a `script` field**, so every one of them was silently losing it.

- **Fixed.** `_coverage_from_v1()` now carries `script` (optional on
  `reuse-upstream`) and `upstream` (optional on `custom-script`) whenever
  v1 actually authored them — never fabricated when absent.
- **`_coverage_preserved()` — a NEW, independent check.** It does not trust
  `candidate_v2()`'s own construction: it re-derives what each v1
  implementation *should* carry directly from the raw v1 record
  (`_v1_expected_coverage_fields()`), then checks the REAL, already-parsed
  `ImplementationCoverage` in `v2.authored_states` — so a bug in
  `_coverage_from_v1()` itself (exactly what happened here) is caught, not
  just a bug in whether the tool agrees with itself.
  `CoveragePreservationTest.test_check_is_independent_of_construction_a_
  dropped_script_is_detected` proves this by mutation: monkeypatching
  `_coverage_from_v1()` to drop `script` again, and confirming
  `_coverage_preserved()` notices.
- **`_data_preserved()` now checks both**: transition text/summary/sources
  AND coverage-field preservation. **Re-verified for all 296 records: 0
  failures**, after the fix.
- **`_coverage_from_v1()` still fabricates nothing.** A v1 implementation
  missing a REQUIRED field (`historical_passcode`/`upstream` on
  reuse-upstream, `historical_passcode`/`script` on custom-script,
  `gap.reason`/`gap.sources` on an acknowledged gap) raises
  `MigrationDataMissing` rather than substituting a plausible-looking
  default. 0 of the 296 records exercise this path today.

### Implementation metadata with NO v2 destination — an honest inventory

Not every v1 implementation field maps onto v2's coverage schema.
`COVERAGE_FIELDS` is closed per kind (`additionalProperties: false` in the
schema), so these fields have **no destination to migrate into at all** —
not a bug `_coverage_from_v1()` could fix, a genuine representation gap.
**No schema extension is proposed here** — `metadata_inventory()` only
reports the fact:

| field | records carrying it | representative ids | v2 destination? | lost on migration? |
|---|---:|---|---|---|
| `status` | 312 (all) | `erratum-a-cat-of-ill-omen`, `erratum-a-deal-with-dark-ruler`, … | **no** | **yes** |
| `tested` | 252 | `erratum-a-cat-of-ill-omen`, `erratum-a-deal-with-dark-ruler`, … | **no** | **yes** |
| `gap.upstream_checked` | 56 | `erratum-a-hero-emerges`, `erratum-amazoness-fighter`, … | **no** | **yes** |
| `gap.behavioural_impact` | 56 | `erratum-a-hero-emerges`, `erratum-amazoness-fighter`, … | **no** | **yes** |
| `reason` (bare, on a `none-needed` implementation) | 1 | `erratum-spiritual-energy-settle-machine` | **no** | **yes** |

`status`/`tested` are v1's implementation-completeness workflow fields
(`missing`/`stub`/`partial`/`complete`/`verified`, and a tested/untested
flag) — orthogonal to *what* the implementation is, which is all v2's
coverage sum type records. `gap.upstream_checked`/`gap.behavioural_impact`
document HOW a known gap was investigated, beyond the `gap_reason`/
`gap_sources` v2's `known-gap` coverage does carry. The bare `reason` is a
single record's ad hoc justification for a `none-needed` decision, which
`none-needed` coverage (closed to just `{kind}`) has no field for either.
**This is a migration decision, explicitly flagged as unresolved rather
than silently discarded or answered by inventing a field.**
`metadata_inventory()` also flags any implementation/gap field it does not
already recognise, so a future field is reported rather than silently
missed.

## Coverage signature distinguishes coverage KIND, not just final identity (task objective 3)

**Corrected pass.** The comparator's coverage signature previously
collapsed `reuse-upstream` and `custom-script` at the same passcode into a
shared `("historical", passcode, variants)` tag, and both `known-gap` and
`unresolved` compared as equal-shaped `("gap", ...)` tuples distinguished
only by a sub-tag. That is too weak for a migration-DATA audit (as opposed
to an executable-behaviour one): `reuse-upstream` and `custom-script` are
different `COVERAGE_FIELDS` shapes with different provenance (upstream's
implementation vs. this project's own script), and two different
`known-gap` states must not be treated as the same fact merely because both
currently fall back to modern execution.

**Fixed.** `_v1_coverage_signature()`/`_v2_coverage_signature()` now tag by
kind explicitly: `("reuse-upstream", passcode, variants)`,
`("custom-script", passcode, variants)`, `("none-needed",)`,
`("known-gap", reason, sources)`, `("unresolved",)`, `("modern",)` — six
genuinely distinct signatures, not four. `known-gap` additionally carries
its `reason`/`sources`, so two different acknowledged gaps on the same
record compare unequal, not merely different from `unresolved`.

**Re-running the full 296-record audit under the fine-grained signature
changes nothing** — 247/49/48 are unchanged. That is expected, not
suspicious: the current corpus has no `custom-script` implementation at
all (242 `reuse-upstream`, 56 `unresolved`, 14 `none-needed` — 0
`custom-script`), and `_coverage_from_v1()` maps strategy to coverage kind
1:1 faithfully, so no real record's kind ever disagreed across v1/v2 to
begin with. The fix matters for correctness and for catching a *future*
regression, which is exactly what the mutation test below proves it does.

**Mutation regression**
(`CoverageKindDistinctionTest.test_mutation_swapping_coverage_kind_is_
detected`): take a real, currently-equivalent `reuse-upstream` sugar
record (`erratum-a-cat-of-ill-omen`), swap its candidate's coverage kind to
`custom-script` at the **same** passcode, and re-run the comparator. It now
reports the record non-equivalent — confirming the signature genuinely
carries kind identity into the comparison, not just the final passcode.

## Malformed-identity hardening (task objective 2)

5f7d2da fixed `historical_passcode=None` (missing). This pass's own first
attempt at "present but malformed" used `_is_valid_passcode(value) = 1 <=
int(value) <= 4294967295` — **coercive, not schema-equivalent**: `int("123")
== 123`, `int(True) == 1`, `int(1.5) == 1` would all have silently become
"valid" passcodes, none of which the schema's `type: integer` actually
permits.

**Corrected to match this project's own schema semantics exactly**, not a
re-guessed notion of "integer". `tests/schema_check.py` — the project's
dependency-free JSON Schema subset checker, run against `schemas/*.json` in
CI — defines `type: integer` as `isinstance(v, int) and not isinstance(v,
bool)`: never a coercive cast, never a bool (an `int` subclass in Python
but never a JSON integer), never a float even when integral (`123.0` is a
JSON `number`, not a JSON `integer`, and this project's own checker does not
treat it as one). `_is_valid_passcode()` now mirrors that exactly:

```python
def _is_valid_passcode(value):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    return 1 <= value <= 4294967295
```

Pinned by `PasscodeValiditySchemaAgreementTest`, which runs 15 sample
values (`"123"`, `"not-a-passcode"`, `1.5`, `123.0`, `True`, `False`, `0`,
`-1`, `4294967296`, the boundaries `1`/`4294967295`, an ordinary passcode,
`None`, a list, a dict) through BOTH `_is_valid_passcode()` and
`schema_check.validate()` against the real `passcode` `$def` and asserts
they agree on every one — so the two cannot silently diverge again.

Used consistently as the single authority in `model.py` (`Erratum.
selection_at()`'s gap fallback), `lflist.py` (`_usable`/`_usable_v2`/
`_malformed_substitution`/`_executable_outcome`, all inheriting the strict
check automatically since they already delegated to it), and `validate.py`
(`_safe_passcode()`, rewritten to call `_is_valid_passcode()` directly on
the RAW value instead of `int()`-coercing first and only range-checking
the result — the previous version's coercion would have silently
re-admitted a numeric string). A malformed passcode — missing, non-integer,
a bool, a non-integral float, or out of range — is handled identically
everywhere: the validator reports `erratum.malformed-passcode` and
continues; a direct build (no validator run first) fails as
`ErrataSelectionError`, never a bare `ValueError`/`TypeError`/
`MalformedHistoricalIdentity`/silent coercion; v1's `selection_at()` falls
back to its existing `"gap"` state.

## What is safe to migrate, and what is not

**Do not report "247 safe to migrate."** Semantic equivalence and current
data-preserving migration readiness are different questions, and
conflating them is exactly what the previous pass's framing risked.

**SEMANTIC EQUIVALENCE** (selection never changes at any chronology
boundary):

- **247 of 296** — 180 sugar-eligible, 35 single-relevant-with-cosmetic-
  siblings, 11 fully-ordered multi-event, 11 parity-only, 10 pure
  cosmetic/engine.
- **49 of 296 not equivalent** — v1's positional label and v2's real
  chronology genuinely disagree at some boundary; migrating them as a
  rename would be wrong, not merely imprecise. Exact ids in
  `erratum-v2-migration-audit.json`'s `not_equivalent_ids`.

**CURRENT DATA-PRESERVING MIGRATION READINESS** (equivalence is necessary,
not sufficient — the 11 parity-only records prove it: equivalent in
selection, but v2 as frozen cannot store their identity at all):

- **236 immediately migratable** — 180 sugar-eligible + 35 single-relevant-
  with-cosmetic-siblings + 11 fully-ordered multi-event, none of which
  carry a parity-only representation problem.
- **11 parity-only equivalent-but-blocked** — see above; blocked on a
  representation decision, not on chronology.
- **49 nontrivial semantic migrations, not a rename** — split further, so
  the scope of *actual remaining human work* is visible rather than
  buried inside one "manual review" label:
  - **47 already researched** — design doc §7's taxonomy (38
    bundled/shared-package + 9 mechanically-distinct order-unknown; that
    finer split is a research label with no computable signal in the
    data and is not reproduced by this audit) already classifies every
    one of them. No new research is needed; they need an order-aware
    migration script.
  - **2 need manual research** — `erratum-insect-imitation`,
    `erratum-last-will` — blocked on a human decision about whether their
    researcher-inferred order should become an authored `basis`-carrying
    edge.
- **10 pure cosmetic/engine, no historical state** — equivalent, and
  nothing to migrate at all (no historical identity exists to preserve).

**Self-contradictory under the legacy schema (informational, orthogonal to
the above, not a blocker by itself): 48 of the 49** — the specific symptom
of v1's model actively asserting a false answer, as opposed to YZ-Tank
Dragon's incompleteness. All 48 are already inside the 49.

**Implementation metadata with no v2 destination** (`status`, `tested`,
`gap.upstream_checked`, `gap.behavioural_impact`, one record's ad hoc
`reason`) is a separate, still-open representation question affecting up
to all 296 records regardless of the equivalence/readiness split above —
see the inventory table earlier in this document. Not blocking, not
resolved: reported honestly as unknown.
