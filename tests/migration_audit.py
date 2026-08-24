"""Deterministic v1 -> v2 migration audit, computed from the CURRENT runtime.

This is the tool behind `docs/research/erratum-v2-migration-audit.md`. It
exists as code, re-runnable, rather than as numbers pasted into prose: the
migration partition is an OUTPUT derived from evidence, never an input
assumption carried forward from an earlier pass.

**Corrected pass**: the first version of this tool compared v1 and candidate-
v2 outcomes by collapsing a v2 ambiguous candidate down to `len(candidate
.events)` and comparing that INTEGER against v1's positional candidate index.
That is invalid - it is exactly the cardinality abstraction v2 exists to
replace, and it silently equates two candidates that are not the same state
(`{A}` and `{B}` both have length 1). It produced a false 296/296 equivalence
claim. The comparison below is a genuine SET comparison of (event-identity,
coverage-signature) pairs: `{A}` and `{B}` compare unequal even though they
are the same size, and a v1-claimed state that v2's real chronology proves
impossible is reported as a real mismatch, not laundered through an integer.

What it does, per v1 record:

1. Builds the *candidate* v2 record the migration would produce:
   - ONE event per v1 change, including cosmetic/engine changes, because
     every historical change is a chronology node even when it creates no
     implementation-state dimension (the a114ee3 correction);
   - event ids are opaque labels, never an ordering claim;
   - `ordering` edges ONLY where `ordering_proof()` PROVES the relation from
     the two events' own chronology. Array position is never evidence, and
     co-occurrence is never invented: n changes become n separate events.
   - `states[]` mapping v1's positional version chain onto event down-sets.
     v1's own semantics ARE positional, so this is a faithful reading of
     what the v1 record asserts about implementations - it is not used as
     ordering evidence.
   - historical_text/modern_text/summary/sources are carried across
     verbatim, never just the executable strategy - `_data_preserved()`
     checks this independently of the outcome comparison (this task: "audit
     preservation ... rather than checking executable behaviour alone").
   - no field the v2 coverage schema requires is ever fabricated: a v1
     implementation missing `upstream`/`script`/`gap.reason`/`gap.sources`
     raises `MigrationDataMissing` rather than substituting a
     plausible-looking placeholder (UNKNOWN != GUESS). No record in the
     current 296-record corpus exercises this path (verified by scan); the
     tool must not depend on that staying true.

2. Compares v1's CLAIMED semantic states against v2's REAL semantic states at
   EVERY chronology boundary the record can have. "Claimed" means: v1's
   positional label `k` asserts that the first `k` relevant changes (in
   array order) occurred and the rest did not - restated in v2's event-id
   vocabulary so the two are directly comparable, purely for audit purposes.
   This does NOT turn array order into v2 ordering evidence; it only asks
   what the legacy label meant, then checks whether v2's real, chronology-
   and-structure-derived candidate set contains that exact state, with the
   exact same coverage. The comparison is exact and finite, not sampled: an
   event's OLD/AMBIGUOUS/NEW status only changes at the handful of dates its
   own evidence names, so the union of those dates (each probed at the day
   before, on, and the day after) covers every distinguishable snapshot.

3. Separately, exactly reproduces design doc section 7's legacy-48 self-
   contradiction test: v1's own positional candidate `k` is self-
   contradictory at a snapshot if it claims a transition occurred that is
   independently confirmed OLD, or claims one has not occurred that is
   independently confirmed NEW. This is a DIFFERENT question from
   equivalence (a record can be self-contradictory yet still equivalent to
   v2 once v2 excludes the impossible candidate, or vice versa) and is
   reported as its own field, never folded into "equivalent".

4. Classifies the record by WHY it is or is not equivalence-safe, and
   reports orthogonal structural facts (sugar eligibility, ordering
   structure - none/partial/fully-ordered, never "has any edge") separately
   rather than forcing every record into one overloaded label.

Nothing here writes to data/errata/. The audit is read-only.
"""

from __future__ import annotations

import datetime as _dt
import json
from collections import Counter
from pathlib import Path

from retroformats.model import (
    IMPLEMENTATION_RELEVANT_KINDS,
    NEW,
    OLD,
    PROVEN,
    Coverage,
    Erratum,
    ErratumV2,
    ImplementationCoverage,
    SelectionError,
    _is_valid_passcode,
    _precision_bounds,
    change_state_at,
    ordering_proof,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- categories (a coarse, human-legible summary label - see the orthogonal
# fields on each row - research_status, migration_complexity,
# parity_only_identity, ordering_structure - for the facts it is derived
# from) ----------------------------------------------------------------------
CAT_SUGAR = "sugar-eligible"
CAT_FULL_SINGLE = "full-v2-single-event"
CAT_MULTI_ORDERED = "full-v2-multi-event-ordered"
CAT_MULTI_UNORDERED = "full-v2-multi-event-unordered"
CAT_NONRELEVANT_CHRONOLOGY = "nonrelevant-event-constrains-relevant"
CAT_PARITY_ONLY = "parity-only-identity"
CAT_COSMETIC_ONLY = "no-historical-state"
# The 49 not-equivalent records are NOT uniformly "manual review": the
# frozen design document's own taxonomy (section 7) already researched 47 of
# them (38 bundled/shared-package + 9 mechanically-distinct order-unknown -
# that finer split is itself a research label with no computable signal in
# the data, so this audit does not attempt to reproduce it); only 2
# (Insect Imitation, Last Will) are blocked on an actual human decision
# about a researcher-inferred order. Two distinct categories, not one.
CAT_RESEARCHED_NONTRIVIAL = "researched-nontrivial"
CAT_MANUAL_REVIEW = "manual-review-blocker"

# The exact 2 records the design document names as genuinely blocked on a
# human §5.6 decision (a researcher-inferred order, not yet promoted to a
# proven or authored `basis`) - matching the document's own explicit,
# already-published classification. This is NOT re-derived from a heuristic
# (the document itself says the finer 38/9 split has no computable signal),
# and it is not new research: it is the same 2 ids the frozen document
# already names by name in section 7.
MANUAL_REVIEW_IDS = frozenset({"erratum-insect-imitation", "erratum-last-will"})

RESEARCH_NOT_APPLICABLE = "not-applicable"
RESEARCH_ALREADY_RESEARCHED = "already-researched"
RESEARCH_NEEDS_MANUAL_REVIEW = "needs-manual-review"

COMPLEXITY_TRIVIAL_RENAME = "trivial-rename"
COMPLEXITY_PROVEN_CHAIN = "proven-chain"
COMPLEXITY_UNORDERED_RESEARCHED = "unordered-researched"
COMPLEXITY_UNORDERED_MANUAL_REVIEW = "unordered-manual-review"
COMPLEXITY_UNORDERED_EQUIVALENT = "unordered-equivalent"  # none in the current corpus; see categorise()
COMPLEXITY_PARITY_ONLY_BLOCKED = "parity-only-blocked"
COMPLEXITY_NO_HISTORICAL_STATE = "no-historical-state"

# --- ordering structure: "has a proven edge" is NOT "fully ordered" --------
ORDER_ZERO = "zero-relevant"
ORDER_SINGLE = "single-event"
ORDER_NONE = "no-proven-ordering"
ORDER_PARTIAL = "partial-order"
ORDER_FULL = "fully-ordered"


class MigrationDataMissing(ValueError):
    """A v1 record's authored implementation lacks a field v2's coverage
    schema requires. Raised rather than papered over with a plausible-
    looking default (`upstream or "ProjectIgnis"` and similar were removed
    for exactly this reason) - UNKNOWN != GUESS applies to this tool's own
    output, not only to canonical data."""


def _event_id(index: int) -> str:
    """An opaque label. Deliberately NOT derived from array position in a way
    any consumer could read as order - `e0 < e1` is not an ordering claim,
    and the audit never treats it as one."""
    return f"c{index}"


def boundary_dates(record: Erratum) -> list[_dt.date]:
    """Every date at which some change's OLD/AMBIGUOUS/NEW status can flip,
    plus one day either side of each. `change_state_at()` is piecewise
    constant between these, so probing them is exhaustive rather than a
    sample."""
    marks: set[_dt.date] = set()
    for change in record.changes:
        effective = change.get("effective") or {}
        for key in ("date", "old_attested_through", "new_attested_from"):
            value = effective.get(key)
            if not value:
                continue
            try:
                day = _dt.date.fromisoformat(str(value))
            except ValueError:
                continue
            marks.add(day)
            if key == "date":
                # BOTH ends of the precision-widened interval, computed with
                # the runtime's own function rather than re-derived here: a
                # month/year-precise date need not be the 1st, so the
                # interval START is its own boundary and is not implied by
                # the recorded date. (No corpus record exercises that today;
                # the audit must not depend on that staying true.)
                lo, hi = _precision_bounds(str(value), str(effective.get("precision") or "day"))
                marks.add(lo)
                marks.add(hi)
    probes: set[_dt.date] = {_dt.date(1996, 1, 1), _dt.date(2099, 1, 1)}
    for mark in marks:
        for delta in (-1, 0, 1):
            probes.add(mark + _dt.timedelta(days=delta))
    return sorted(probes)


def _relevant_indices(record: Erratum) -> list[int]:
    return [i for i, c in enumerate(record.changes) if c.get("kind") in IMPLEMENTATION_RELEVANT_KINDS]


def candidate_v2(record: Erratum) -> ErratumV2:
    """The v2 record this v1 record would migrate to, under the rules in this
    module's docstring."""
    events: dict[str, dict] = {}
    for index, change in enumerate(record.changes):
        events[_event_id(index)] = {
            "effective": dict(change.get("effective") or {"date": None}),
            "transitions": [
                {
                    "kind": change.get("kind"),
                    "axis": change.get("axis"),
                    "historical_text": change.get("historical_text"),
                    "modern_text": change.get("modern_text"),
                    "summary": change.get("summary", ""),
                    "sources": list(change.get("sources", [])),
                }
            ],
        }
    # Ordering: ONLY date-proven relations, over every pair in both
    # directions. Never array position, never "the author listed them in
    # this order so they must have happened in it".
    edges = []
    ids = list(events)
    for before in ids:
        for after in ids:
            if before == after:
                continue
            if ordering_proof(events[before]["effective"], events[after]["effective"]) == PROVEN:
                edges.append({"before": before, "after": after, "basis": "date-proven"})

    # states[]: v1's positional version chain, read faithfully.
    relevant_indices = _relevant_indices(record)
    states = []
    for version, _ in enumerate([None] + relevant_indices[:-1] if relevant_indices else [None]):
        impl = record.implementation_for_version(version)
        if impl is None:
            continue
        coverage = _coverage_from_v1(impl)
        if coverage is None:
            continue  # unauthored state: v2 defaults it to UNRESOLVED
        down_set = [_event_id(i) for i in relevant_indices[:version]]
        states.append({"events": down_set, "coverage": coverage})
    raw = {
        "id": record.id,
        "modern_card": {"passcode": record.modern_card.passcode, "name": record.modern_card.name},
        "classification": record.classification,
        "events": events,
        "ordering": {"edges": edges} if edges else {},
        "states": states,
        "review": record.raw.get("review") or {"status": "imported"},
        "sources": list(record.sources),
    }
    return ErratumV2.load(raw, record.path)


def _coverage_from_v1(impl: dict) -> dict | None:
    """Maps a v1 implementation to the v2 coverage it would author. Every
    branch reads only fields the v1 record actually carries; none fabricates
    a default. `strategy == "unresolved"` with no gap returns None (no v2
    coverage is authored at all - v2's own UNRESOLVED default applies,
    exactly matching what "unresolved, undocumented" already means).

    Optional fields the coverage schema permits are carried across when v1
    actually authored them - `script` on reuse-upstream and `upstream` on
    custom-script are both in `COVERAGE_FIELDS`' *allowed* set, not just
    required. Dropping an authored optional field is exactly as much data
    loss as dropping a required one; the two v1-corpus strategies currently
    in use (`reuse-upstream`, `none-needed`, `unresolved` - `custom-script`
    does not appear in the corpus yet) both commonly carry a `script`
    alongside `upstream` (242 of 242 reuse-upstream implementations, per a
    corpus scan), so this is not a hypothetical edge case."""
    strategy = impl.get("strategy")
    if strategy == "reuse-upstream":
        passcode, upstream = impl.get("historical_passcode"), impl.get("upstream")
        if not passcode or not upstream:
            raise MigrationDataMissing(
                "reuse-upstream implementation is missing "
                f"{'historical_passcode' if not passcode else 'upstream'} - v2 cannot author "
                "this coverage without inventing a value"
            )
        coverage = {
            "kind": "reuse-upstream",
            "historical_passcode": passcode,
            "historical_variant_passcodes": list(impl.get("historical_variant_passcodes", [])),
            "upstream": upstream,
        }
        if impl.get("script"):
            coverage["script"] = impl["script"]
        return coverage
    if strategy == "custom-script":
        passcode, script = impl.get("historical_passcode"), impl.get("script")
        if not passcode or not script:
            raise MigrationDataMissing(
                "custom-script implementation is missing "
                f"{'historical_passcode' if not passcode else 'script'} - v2 cannot author "
                "this coverage without inventing a value"
            )
        coverage = {
            "kind": "custom-script",
            "historical_passcode": passcode,
            "historical_variant_passcodes": list(impl.get("historical_variant_passcodes", [])),
            "script": script,
        }
        if impl.get("upstream"):
            coverage["upstream"] = impl["upstream"]
        return coverage
    if strategy == "none-needed":
        return {"kind": "none-needed"}
    gap = impl.get("gap") or {}
    if strategy == "unresolved" and gap:
        reason, sources = gap.get("reason"), gap.get("sources")
        if not reason or not sources:
            raise MigrationDataMissing(
                "unresolved implementation's gap is missing "
                f"{'reason' if not reason else 'sources'} - v2 cannot author this known-gap "
                "coverage without inventing a value"
            )
        return {"kind": "known-gap", "gap_reason": reason, "gap_sources": list(sources)}
    if strategy == "unresolved":
        # An unresolved v1 implementation with no acknowledged gap has no
        # authorable v2 coverage at all: 'unresolved' is never authored, it is
        # the mechanical default for an unauthored state. Returning None makes
        # the caller OMIT the state, which is exactly how v2 spells it.
        return None
    raise ValueError(f"no v2 coverage mapping for v1 strategy {strategy!r}")


# Fields on a v1 implementation (or its `gap` sub-object) that have a direct
# semantic representation in v2's coverage schema, per strategy. Used by
# `_coverage_preserved()` below to check preservation INDEPENDENTLY of
# `_coverage_from_v1()` - re-derived from the raw v1 record, then checked
# against the REAL, already-parsed `ImplementationCoverage` the candidate
# actually carries, not against `_coverage_from_v1()`'s own intermediate
# dict. A bug in `_coverage_from_v1()` itself (e.g. silently dropping
# `script`) would otherwise go undetected by a check that only re-verified
# its own output against its own input.
def _v1_expected_coverage_fields(impl: dict) -> dict:
    strategy = impl.get("strategy")
    if strategy == "reuse-upstream":
        expected = {
            "historical_passcode": impl.get("historical_passcode"),
            "historical_variant_passcodes": tuple(impl.get("historical_variant_passcodes", [])),
            "upstream": impl.get("upstream"),
        }
        if impl.get("script"):
            expected["script"] = impl["script"]
        return expected
    if strategy == "custom-script":
        expected = {
            "historical_passcode": impl.get("historical_passcode"),
            "historical_variant_passcodes": tuple(impl.get("historical_variant_passcodes", [])),
            "script": impl.get("script"),
        }
        if impl.get("upstream"):
            expected["upstream"] = impl["upstream"]
        return expected
    if strategy == "none-needed":
        return {}
    gap = impl.get("gap") or {}
    if strategy == "unresolved" and gap:
        return {"gap_reason": gap.get("reason"), "gap_sources": tuple(gap.get("sources") or ())}
    return {}  # unresolved without a gap: nothing authored, nothing to preserve


def _coverage_preserved(record: Erratum, v2: ErratumV2) -> bool:
    """Independent of `candidate_v2()`'s own construction: re-derive what
    each v1 implementation SHOULD carry directly from the v1 record, then
    check the REAL PARSED v2 `ImplementationCoverage` in `v2.authored_states`
    actually carries it - catching a bug in `candidate_v2()`/
    `_coverage_from_v1()` itself, not merely confirming they agree with
    themselves."""
    relevant_indices = _relevant_indices(record)
    versions = [None] + relevant_indices[:-1] if relevant_indices else [None]
    for version, _ in enumerate(versions):
        impl = record.implementation_for_version(version)
        if impl is None:
            continue
        expected = _v1_expected_coverage_fields(impl)
        if not expected:
            continue  # none-needed / unauthored unresolved: nothing to check
        down_set = frozenset(_event_id(i) for i in relevant_indices[:version])
        coverage = v2.authored_states.get(down_set)
        if coverage is None:
            return False
        for field, value in expected.items():
            actual = getattr(coverage, field, None)
            if field == "historical_variant_passcodes":
                actual = tuple(actual)
            if actual != value:
                return False
    return True


def _data_preserved(record: Erratum, v2: ErratumV2) -> bool:
    """Migration must not silently drop documentation fields even where
    executable behaviour is unaffected: every change's historical_text,
    modern_text, summary and sources must survive verbatim into its
    candidate event's sole transition, AND every coverage field with a
    direct v2 representation (§_coverage_preserved) must survive too."""
    for index, change in enumerate(record.changes):
        event = v2.events.get(_event_id(index))
        if event is None or not event.transitions:
            return False
        transition = event.transitions[0]
        if transition.historical_text != change.get("historical_text"):
            return False
        if transition.modern_text != change.get("modern_text"):
            return False
        if transition.summary != change.get("summary", ""):
            return False
        if tuple(transition.sources) != tuple(change.get("sources", [])):
            return False
    return _coverage_preserved(record, v2)


# v1 implementation/gap metadata with NO direct representation in v2's
# coverage schema at all (COVERAGE_FIELDS is closed per kind - these simply
# have no destination field, not a bug to fix by widening a dict). Reported
# by `metadata_inventory()` as an explicit, honest gap - UNKNOWN != DISCARD:
# this is not proposed as a schema addition, only surfaced as a fact a
# migration decision must eventually confront.
UNREPRESENTED_METADATA_FIELDS = ("status", "tested", "gap.upstream_checked", "gap.behavioural_impact")


def metadata_inventory(errata: dict) -> list[dict]:
    """For every v1 implementation-metadata field with no v2 coverage
    destination: how many records carry it, which ones (a sample), and
    confirmation that migrating today would silently lose it. Also flags
    ANY field on an implementation or its `gap` this function does not
    already know about, rather than silently assuming the known list is
    exhaustive forever."""
    from collections import defaultdict

    known_reason_fields = {"reason", "sources"}  # -> gap_reason/gap_sources, already preserved
    known_impl_fields = {
        "strategy",
        "historical_passcode",
        "historical_variant_passcodes",
        "upstream",
        "script",
        "gap",
    }
    field_records: dict[str, list[str]] = defaultdict(list)
    for record in errata.values():
        if not isinstance(record, Erratum):
            continue
        impls = [record.implementation or {}]
        for change in record.changes:
            resulting = change.get("resulting_implementation")
            if resulting:
                impls.append(resulting)
        for impl in impls:
            for key in impl:
                if key not in known_impl_fields:
                    field_records[key].append(record.id)
                elif key == "status" or key == "tested":
                    field_records[key].append(record.id)
            gap = impl.get("gap") or {}
            for key in gap:
                if key not in known_reason_fields:
                    field_records[f"gap.{key}"].append(record.id)
    inventory = []
    for field in sorted(field_records):
        ids = field_records[field]
        inventory.append(
            {
                "field": field,
                "record_count": len(ids),
                "representative_ids": sorted(set(ids))[:5],
                "has_v2_destination": False,
                "would_be_lost_on_migration": True,
            }
        )
    return inventory


# --- semantic outcome comparison ---------------------------------------------
# A "state" is compared as (frozenset of event ids, coverage signature) - NEVER
# as an integer, a cardinality, or a version index. Two states with the same
# `len(events)` but different identities (`{A}` vs `{B}`) are different states.

def _v1_coverage_signature(impl: dict | None) -> tuple:
    """What v1's OWN `selection_at()` determinate branch treats this
    implementation as executing, restated as a comparable tuple - mirrors
    that branch's exact logic rather than a reinvented rule, so "claimed"
    can never silently drift from what v1 actually does when determinate.

    Distinguishes coverage KIND, not merely final executable identity:
    reuse-upstream and custom-script at the same passcode are different
    migration-data claims (different `COVERAGE_FIELDS` shapes, different
    provenance), so they get different tags even though both execute as a
    substitution today. A known-gap is never conflated with a bare
    unresolved state merely because both currently fall back to modern
    execution - a known-gap additionally carries the reason/sources that
    document it, and two DIFFERENT known-gap reasons on the same record
    must not compare equal either."""
    if impl is None:
        return ("unresolved",)
    strategy = impl.get("strategy")
    if strategy == "unresolved":
        gap = impl.get("gap")
        if gap:
            return ("known-gap", gap.get("reason"), tuple(gap.get("sources") or ()))
        return ("unresolved",)
    if strategy == "none-needed":
        return ("none-needed",)
    passcode = impl.get("historical_passcode")
    if not passcode or not _is_valid_passcode(passcode):
        return ("unresolved",)
    variants = tuple(impl.get("historical_variant_passcodes", ()))
    tag = "custom-script" if strategy == "custom-script" else "reuse-upstream"
    return (tag, passcode, variants)


def _v1_claimed_state(record: Erratum, relevant_indices: list[int], k: int) -> tuple:
    """What v1's positional label `k` CLAIMS, for audit purposes ONLY: the
    down-set of the first `k` relevant events (array order) is v1's own
    positional assumption about which transitions occurred, restated in
    v2's event-id vocabulary so it is directly comparable to a REAL v2
    candidate's `.events` identity. This does NOT turn array order into v2
    ordering evidence - it only asks what the legacy label meant."""
    events = frozenset(_event_id(i) for i in relevant_indices[:k])
    if k >= len(relevant_indices):
        return events, ("modern",)
    return events, _v1_coverage_signature(record.implementation_for_version(k))


def v1_claimed_states(record: Erratum, day: _dt.date) -> frozenset:
    """Every (event-set, coverage-signature) pair v1 claims is plausible at
    `day` - the full SET, not its size: one pair for a determinate
    selection, one per candidate index for an ambiguous one."""
    relevant_indices = _relevant_indices(record)
    selection = record.selection_at(day)
    if selection.state == "ambiguous":
        ks = selection.candidates
    elif selection.version_index is not None:
        ks = (selection.version_index,)
    else:
        ks = (len(relevant_indices),)  # no relevant changes: always terminal/modern
    return frozenset(_v1_claimed_state(record, relevant_indices, k) for k in ks)


def _v2_coverage_signature(coverage: ImplementationCoverage) -> tuple:
    """The v2-side counterpart of `_v1_coverage_signature()` - same
    vocabulary, same kind-level distinctions, so the two are directly
    comparable rather than both collapsing onto a shared coarser scheme."""
    if coverage.kind == Coverage.MODERN:
        return ("modern",)
    if coverage.kind == Coverage.NONE_NEEDED:
        return ("none-needed",)
    if coverage.kind in (Coverage.REUSE_UPSTREAM, Coverage.CUSTOM_SCRIPT):
        if not coverage.historical_passcode or not _is_valid_passcode(coverage.historical_passcode):
            return ("unresolved",)
        tag = "custom-script" if coverage.kind == Coverage.CUSTOM_SCRIPT else "reuse-upstream"
        return (tag, coverage.historical_passcode, tuple(coverage.historical_variant_passcodes))
    if coverage.kind == Coverage.KNOWN_GAP:
        return ("known-gap", coverage.gap_reason, tuple(coverage.gap_sources))
    return ("unresolved",)  # Coverage.UNRESOLVED


def v2_claimed_states(record: ErratumV2, day: _dt.date) -> frozenset | None:
    """The REAL v2 candidate set at `day`: every structurally-and-
    chronologically-consistent `HistoricalState`'s own (events, coverage)
    identity, read directly off `selection_at()` - never reduced to a
    cardinality. None means the candidate is contradictory at this
    snapshot."""
    try:
        selection = record.selection_at(day)
    except SelectionError:
        return None
    return frozenset((c.events, _v2_coverage_signature(c.coverage)) for c in selection.candidates)


def _fmt_states(states) -> list[dict]:
    return [
        {"events": sorted(events), "coverage": list(sig)}
        for events, sig in sorted(states, key=lambda pair: (len(pair[0]), sorted(pair[0])))
    ]


def _ordering_structure(relevant_count: int, structural_state_count: int) -> str:
    """none/partial/fully-ordered, from the RELEVANT-event down-set count the
    ordering DAG structurally produces - never "has any proven edge", which
    conflates a partial order (some pair proven, others not) with a total
    one."""
    if relevant_count == 0:
        return ORDER_ZERO
    if relevant_count == 1:
        return ORDER_SINGLE
    if structural_state_count == relevant_count + 1:
        return ORDER_FULL
    if structural_state_count == 2**relevant_count:
        return ORDER_NONE
    return ORDER_PARTIAL


def _legacy_self_contradictory(record: Erratum, relevant_indices: list[int]) -> bool:
    """Design doc section 7's EXACT test, implemented directly rather than
    approximated: at some boundary date, v1's own `selection_at()` offers a
    candidate index `k` that claims relevant transitions `0..k-1` occurred
    and `k..end` did not, while at least one transition's OWN,
    independently-computed OLD/AMBIGUOUS/NEW status contradicts that claim.
    This is the "48" definition - never redefined as a proxy (modern-
    excluded-at-some-format, ambiguous-at-a-snapshot, candidate count)."""
    if len(relevant_indices) < 2:
        return False  # self-contradiction requires an unproven-order pair
    relevant_changes = [record.changes[i] for i in relevant_indices]
    for day in boundary_dates(record):
        selection = record.selection_at(day)
        if selection.state != "ambiguous":
            continue
        statuses = [change_state_at(c, day) for c in relevant_changes]
        for k in selection.candidates:
            occurred, not_occurred = statuses[:k], statuses[k:]
            if any(s == OLD for s in occurred) or any(s == NEW for s in not_occurred):
                return True
    return False


def compare(record: Erratum) -> dict:
    """Full-boundary comparison of one record. Returns the audit row."""
    relevant_indices = _relevant_indices(record)
    impl = record.implementation or {}
    row: dict = {
        "id": record.id,
        "classification": record.classification,
        "event_count": len(record.changes),
        "relevant_event_count": len(relevant_indices),
        "nonrelevant_event_count": len(record.changes) - len(relevant_indices),
        "baseline_strategy": impl.get("strategy"),
        "baseline_passcode": impl.get("historical_passcode"),
        "sources": list(record.sources),
        "change_kinds": [c.get("kind") for c in record.changes],
    }
    row["parity_only_identity"] = (
        not relevant_indices
        and impl.get("strategy") in ("reuse-upstream", "custom-script")
        and bool(impl.get("historical_passcode"))
        and _is_valid_passcode(impl.get("historical_passcode"))
    )
    row["no_historical_state"] = not relevant_indices and not row["parity_only_identity"]

    try:
        v2 = candidate_v2(record)
    except Exception as exc:  # pragma: no cover - defensive
        row.update(
            sugar_eligible=False,
            ordering_structure="unknown",
            structural_state_count=0,
            proven_edge_count=0,
            data_preserved=False,
            legacy_self_contradictory=None,
            equivalent=False,
            semantic_equivalent=False,
            mismatch_count=None,
            first_mismatches=[],
            contradictory_at=[],
            reason=f"candidate-v2 construction failed: {exc}",
            category=CAT_MANUAL_REVIEW,
            research_status=RESEARCH_NEEDS_MANUAL_REVIEW,
            migration_complexity=COMPLEXITY_UNORDERED_MANUAL_REVIEW,
        )
        return row

    row["proven_edge_count"] = len(v2.raw_edges)
    row["structural_state_count"] = len(v2.structural_states())
    row["ordering_structure"] = _ordering_structure(len(relevant_indices), row["structural_state_count"])
    row["sugar_eligible"] = row["event_count"] == 1 and row["relevant_event_count"] == 1
    row["data_preserved"] = _data_preserved(record, v2)
    row["legacy_self_contradictory"] = _legacy_self_contradictory(record, relevant_indices)

    mismatches = []
    contradictory_at = []
    for day in boundary_dates(record):
        v1_set = v1_claimed_states(record, day)
        v2_set = v2_claimed_states(v2, day)
        if v2_set is None:
            contradictory_at.append(day.isoformat())
            mismatches.append({"date": day.isoformat(), "v1": _fmt_states(v1_set), "v2": "contradictory"})
            continue
        if v1_set != v2_set:
            mismatches.append(
                {
                    "date": day.isoformat(),
                    "v1": _fmt_states(v1_set),
                    "v2": _fmt_states(v2_set),
                    "v1_only": _fmt_states(v1_set - v2_set),
                    "v2_only": _fmt_states(v2_set - v1_set),
                }
            )
    row["equivalent"] = not mismatches
    row["semantic_equivalent"] = row["equivalent"]  # explicit alias (task's own vocabulary)
    row["mismatch_count"] = len(mismatches)
    row["first_mismatches"] = mismatches[:5]
    row["contradictory_at"] = contradictory_at
    category, research_status, migration_complexity = categorise(row, record, v2)
    row["category"] = category
    row["research_status"] = research_status
    row["migration_complexity"] = migration_complexity
    return row


def categorise(row: dict, record: Erratum, v2: ErratumV2) -> tuple[str, str, str]:
    """(category, research_status, migration_complexity) - three views of
    the same row kept in one function so they can never disagree with each
    other. `category` is a coarse, human-legible summary; the 49
    not-equivalent records are NOT uniformly `manual-review-blocker` - only
    the 2 the frozen design document names (`MANUAL_REVIEW_IDS`) are; the
    other (currently 47) already have a documented research classification
    in section 7's taxonomy, even though its finer 38/9 split is not itself
    computable from the data."""
    if row["relevant_event_count"] == 0:
        if row["parity_only_identity"]:
            return CAT_PARITY_ONLY, RESEARCH_NOT_APPLICABLE, COMPLEXITY_PARITY_ONLY_BLOCKED
        return CAT_COSMETIC_ONLY, RESEARCH_NOT_APPLICABLE, COMPLEXITY_NO_HISTORICAL_STATE
    if not row["equivalent"]:
        if row["nonrelevant_event_count"] and _nonrelevant_is_implicated(record, v2):
            return CAT_NONRELEVANT_CHRONOLOGY, RESEARCH_NEEDS_MANUAL_REVIEW, COMPLEXITY_UNORDERED_MANUAL_REVIEW
        if record.id in MANUAL_REVIEW_IDS:
            return CAT_MANUAL_REVIEW, RESEARCH_NEEDS_MANUAL_REVIEW, COMPLEXITY_UNORDERED_MANUAL_REVIEW
        return CAT_RESEARCHED_NONTRIVIAL, RESEARCH_ALREADY_RESEARCHED, COMPLEXITY_UNORDERED_RESEARCHED
    if row["sugar_eligible"]:
        return CAT_SUGAR, RESEARCH_NOT_APPLICABLE, COMPLEXITY_TRIVIAL_RENAME
    if row["relevant_event_count"] == 1:
        return CAT_FULL_SINGLE, RESEARCH_NOT_APPLICABLE, COMPLEXITY_TRIVIAL_RENAME
    if row["ordering_structure"] == ORDER_FULL:
        return CAT_MULTI_ORDERED, RESEARCH_NOT_APPLICABLE, COMPLEXITY_PROVEN_CHAIN
    # Equivalent, 2+ relevant events, not fully ordered: none in the current
    # corpus (every such record is non-equivalent there - see
    # test_ordering_structure_never_conflates_any_edge_with_fully_ordered),
    # but the label must still be honest if one ever appears.
    return CAT_MULTI_UNORDERED, RESEARCH_NOT_APPLICABLE, COMPLEXITY_UNORDERED_EQUIVALENT


def _nonrelevant_is_implicated(record: Erratum, v2: ErratumV2) -> bool:
    """Would the record become equivalent if its cosmetic/engine changes were
    dropped entirely? If so, the difference is CAUSED by a non-relevant
    event's chronology participating in down-set reasoning - the exact
    behaviour a114ee3 introduced and the stale design text used to deny."""
    trimmed_changes = [c for c in record.changes if c.get("kind") in IMPLEMENTATION_RELEVANT_KINDS]
    if len(trimmed_changes) == len(record.changes):
        return False
    trimmed = Erratum.load({**record.raw, "changes": trimmed_changes}, record.path)
    try:
        trimmed_v2 = candidate_v2(trimmed)
    except Exception:  # pragma: no cover - defensive
        return False
    for day in boundary_dates(trimmed):
        if v1_claimed_states(trimmed, day) != v2_claimed_states(trimmed_v2, day):
            return False
    return True


# --- corpus driver ----------------------------------------------------------

def audit_corpus(errata_dir: Path | None = None) -> dict:
    from retroformats.repo import Repository

    repo = Repository.load(REPO_ROOT)
    rows = []
    for record in sorted(repo.errata.values(), key=lambda e: e.id):
        if not isinstance(record, Erratum):
            continue  # already v2; nothing to migrate
        rows.append(compare(record))
    parity_only_count = sum(1 for r in rows if r.get("category") == CAT_PARITY_ONLY)
    equivalent_count = sum(1 for r in rows if r["equivalent"])
    summary = {
        "records": len(rows),
        # SEMANTIC EQUIVALENCE: selection never changes at any chronology
        # boundary. Necessary, not sufficient, for migration readiness -
        # see immediately_migratable/parity_only_blocked below.
        "equivalent": equivalent_count,
        "semantic_equivalent": equivalent_count,  # explicit alias
        "not_equivalent": sum(1 for r in rows if not r["equivalent"]),
        "not_equivalent_ids": sorted(r["id"] for r in rows if not r["equivalent"]),
        "legacy_self_contradictory_count": sum(1 for r in rows if r.get("legacy_self_contradictory")),
        "legacy_self_contradictory_ids": sorted(r["id"] for r in rows if r.get("legacy_self_contradictory")),
        "sugar_eligible_count": sum(1 for r in rows if r.get("sugar_eligible")),
        "ordering_structure": dict(Counter(r.get("ordering_structure") for r in rows)),
        "categories": dict(Counter(r["category"] for r in rows)),
        "research_status": dict(Counter(r.get("research_status") for r in rows)),
        "migration_complexity": dict(Counter(r.get("migration_complexity") for r in rows)),
        "data_not_preserved_ids": sorted(r["id"] for r in rows if r.get("data_preserved") is False),
        # CURRENT DATA-PRESERVING MIGRATION READINESS: equivalence is
        # necessary but not sufficient. Of the 247 semantically equivalent
        # records, 11 (parity-only identity) are STILL blocked on a
        # representation decision - they are equivalent in SELECTION but
        # v2 as frozen cannot store the identity at all. Do not report 247
        # as "safe to migrate" without this qualifier.
        "immediately_migratable": equivalent_count - parity_only_count,
        "parity_only_blocked": parity_only_count,
        "parity_only_blocked_ids": sorted(r["id"] for r in rows if r.get("category") == CAT_PARITY_ONLY),
        "nontrivial_migration_scope": sum(1 for r in rows if not r["equivalent"]),
        "nontrivial_already_researched": sum(1 for r in rows if r.get("category") == CAT_RESEARCHED_NONTRIVIAL),
        "nontrivial_needs_manual_review": sum(1 for r in rows if r.get("category") == CAT_MANUAL_REVIEW),
        "nontrivial_needs_manual_review_ids": sorted(
            r["id"] for r in rows if r.get("category") == CAT_MANUAL_REVIEW
        ),
    }
    summary["metadata_inventory"] = metadata_inventory(repo.errata)
    return {"summary": summary, "rows": rows}


def parity_only_consumption(rows: list[dict]) -> dict:
    """Objective 4 (prior pass) / kept separate and re-verified in this pass:
    for every zero-relevant record that nevertheless carries a usable
    historical identity, does any CURRENT format actually consume that
    identity, and would dropping it change generated output? Selection
    equivalence (above) does NOT imply this is safe to migrate - it is
    checked independently, and is not gated on the equivalence result."""
    from retroformats.lflist import build_lflist, select_applicable_errata
    from retroformats.repo import Repository

    repo = Repository.load(REPO_ROOT)
    parity_ids = [r["id"] for r in rows if r["category"] == CAT_PARITY_ONLY]
    detail = []
    for record_id in parity_ids:
        record = repo.errata[record_id]
        impl = record.implementation or {}
        consumers = []
        for fmt_id in sorted(repo.formats):
            fmt = repo.formats[fmt_id]
            try:
                selected = select_applicable_errata(fmt, repo)
            except Exception:
                continue
            override = selected.get(record.modern_card.passcode)
            if override is None or override.erratum.id != record_id:
                continue
            via = "explicit-include" if record_id in fmt.errata_include else (
                "reference_parity" if fmt.reference_parity else "computed"
            )
            consumers.append({"format": fmt_id, "via": via,
                              "emits": impl.get("historical_passcode")})
        detail.append({
            "id": record_id,
            "modern_card": record.modern_card.name,
            "modern_passcode": record.modern_card.passcode,
            "classification": record.classification,
            "strategy": impl.get("strategy"),
            "historical_passcode": impl.get("historical_passcode"),
            "sources": list(record.sources),
            "change_kinds": [c.get("kind") for c in record.changes],
            "consumed_by": consumers,
        })
    # Would dropping every one of them change generated output?
    baseline = {}
    for fmt_id in sorted(repo.formats):
        fmt = repo.formats[fmt_id]
        if fmt.banlist_id in repo.banlists and fmt.pool_id in repo.pools:
            baseline[fmt_id] = build_lflist(fmt, repo).entries
    stripped_repo = Repository.load(REPO_ROOT)
    for record_id in parity_ids:
        stripped_repo.errata[record_id].implementation = {
            "strategy": "none-needed", "status": "complete"
        }
    after = {}
    for fmt_id in sorted(stripped_repo.formats):
        fmt = stripped_repo.formats[fmt_id]
        if fmt.banlist_id in stripped_repo.banlists and fmt.pool_id in stripped_repo.pools:
            after[fmt_id] = build_lflist(fmt, stripped_repo).entries
    impact = {}
    for fmt_id in baseline:
        lost = sorted(set(baseline[fmt_id]) - set(after.get(fmt_id, {})))
        gained = sorted(set(after.get(fmt_id, {})) - set(baseline[fmt_id]))
        impact[fmt_id] = {"codes_lost": lost, "codes_gained": gained,
                          "output_changes": bool(lost or gained)}
    return {"records": detail, "dist_impact": impact}


if __name__ == "__main__":  # pragma: no cover
    result = audit_corpus()
    result["parity_only"] = parity_only_consumption(result["rows"])
    out = REPO_ROOT / "docs" / "research" / "erratum-v2-migration-audit.json"
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2))
    print("parity-only records:", len(result["parity_only"]["records"]))
    print("dist impact:", json.dumps(result["parity_only"]["dist_impact"], indent=1))
    print("wrote", out)
