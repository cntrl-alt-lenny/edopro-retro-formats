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
from typing import Any, Callable

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
# Final pre-migration gate, task section 4: the representation blocker this
# label named is gone (implementation_metadata[]/reference_identities[] now
# exist and are independently verified as preserved for all 11 records this
# category covers) - "blocked" is no longer an accurate word for a category
# that is representation-ready. Renamed to a descriptive, non-blocking label;
# the CLASSIFICATION itself (zero relevant events, a usable historical
# identity Coverage cannot represent) is unchanged and still worth naming.
COMPLEXITY_PARITY_ONLY_IDENTITY = "parity-only-reference-identity"
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


class MigrationMappingQuestion(Exception):
    """A v1 shape this migration has no frozen answer for. Raised rather
    than resolved by guessing: silently discarding the data, or
    force-mapping it onto a down-set the frozen design never defined, are
    both worse than stopping and asking."""


def stray_resulting_implementations(record: Erratum) -> list[tuple[int, str]]:
    """`(change index, kind)` for every `resulting_implementation` authored
    on a change that is NOT implementation-relevant.

    `_v1_metadata_occurrences()` maps a `resulting_implementation` onto the
    down-set its change CREATES - and a non-relevant change creates no
    event in that down-set vocabulary, so there is no defined v2 key for
    one. Rather than let such an object vanish silently (or invent a
    mapping), the corpus is checked and the question is raised. The current
    corpus has none; this exists so that stays a verified fact rather than
    an assumption."""
    return [
        (index, str(change.get("kind")))
        for index, change in enumerate(record.changes)
        if change.get("resulting_implementation") is not None
        and change.get("kind") not in IMPLEMENTATION_RELEVANT_KINDS
    ]


def final_relevant_resulting_implementations(record: Erratum) -> list[tuple[int, str]]:
    """`(change index, kind)` for a `resulting_implementation` authored on
    the record's FINAL implementation-relevant change specifically - a
    STRONGER, DIFFERENT check than `stray_resulting_implementations()`
    above (final pre-migration gate, task section 6): that check proves no
    `resulting_implementation` sits on a change that is not implementation-
    relevant at all; this one proves none sits on the *last* relevant one,
    which can be a real functional/ruling change and still be unmappable.

    v1's OWN `implementation_for_version()` never reads a value authored
    here: `version_index >= len(relevant_changes())` unconditionally
    returns `None` ("the modern card"), and the terminal version - the one
    the record's FINAL relevant change creates - IS `len(relevant_
    changes())`. So a `resulting_implementation` authored on the final
    relevant change is already DEAD in v1's own runtime, not merely
    unmapped by this migration. v2 does not give it anywhere to go either:
    the terminal (all-relevant-events) down-set unconditionally
    synthesises MODERN coverage (design doc's frozen terminal-state rule),
    never an authored substitution - so unlike the cosmetic/engine case,
    there is no "route it to the right down-set instead" fix available.
    Migrating such a value (to any down-set, on any guess) would invent an
    interpretation v1 itself never actually gave it. The current corpus
    has none (verified by `ResultingImplementationTerminalityTest`); this
    function exists so that stays a checked fact, not an assumption."""
    relevant_indices = _relevant_indices(record)
    if not relevant_indices:
        return []
    final_index = relevant_indices[-1]
    change = record.changes[final_index]
    if change.get("resulting_implementation") is not None:
        return [(final_index, str(change.get("kind")))]
    return []


def _v1_metadata_occurrences(record: Erratum) -> list[tuple[tuple[str, ...], dict, str]]:
    """Every v1 implementation OBJECT whose workflow/research metadata must
    survive migration, as `(ordered down-set event ids, implementation,
    label)`.

    Deliberately NOT `implementation_for_version()`. That function answers
    a COVERAGE question - "which implementation is EXECUTABLE for version
    k?" - and correctly returns None for version 0 of a zero-relevant
    record, because `{}` is then also the terminal/MODERN state and the
    modern executable needs no coverage authored for it. Metadata is a
    different question with a different answer. A record with zero
    implementation-relevant changes still has an AUTHORED record-level
    `implementation` carrying `status`/`tested`/`reason`/`gap.
    upstream_checked`/`gap.behavioural_impact`, and that authorship must
    survive even though the state it describes is terminal. Coverage
    occurrences and metadata occurrences are genuinely different concepts,
    so they do not share a lookup - conflating them is what lost the
    baseline metadata of all 21 zero-relevant records.

    Yields, in order:

      * `((), record.implementation, "baseline")` - ALWAYS, for every
        record, zero-relevant ones included. Baseline metadata maps to the
        empty down-set unconditionally. That remains true when `{}` is the
        terminal/MODERN state, and it does NOT imply a baseline COVERAGE
        state exists: the two arrays stay orthogonal exactly as designed.
      * one entry per implementation-relevant change that records a
        `resulting_implementation`, keyed by the down-set that change
        CREATES (the prefix of relevant event ids up to and INCLUDING it),
        labelled `resulting:<index into record.changes>`.

    The event ids are emitted in the legacy record's own positional order,
    which describes only the v1 state chain's claimed identity during
    migration. It is never evidence of v2 ordering - v2 ordering comes
    exclusively from date-proven edges."""
    relevant_indices = _relevant_indices(record)
    occurrences: list[tuple[tuple[str, ...], dict, str]] = [
        ((), dict(record.implementation or {}), "baseline")
    ]
    for position, change_index in enumerate(relevant_indices):
        resulting = record.changes[change_index].get("resulting_implementation")
        if not resulting:
            continue
        down_set = tuple(_event_id(i) for i in relevant_indices[: position + 1])
        occurrences.append((down_set, dict(resulting), f"resulting:{change_index}"))
    return occurrences


def candidate_v2(record: Erratum, reference_identities: list[dict] | None = None) -> ErratumV2:
    """The v2 record this v1 record would migrate to, under the rules in this
    module's docstring. `reference_identities` (task section 8) is derived
    SEPARATELY, from the repository's own format policies
    (`derive_reference_identities()`) - never hard-coded here - and merged
    in verbatim when the caller has one; most records pass none.

    A thin wrapper around `candidate_v2_raw()` (final pre-migration gate,
    task section 7): this function exists for SEMANTIC AUDIT (a parsed
    `ErratumV2` to query `.authored_states`/`.implementation_metadata`/
    `.reference_identities` against), while `candidate_v2_raw()` exists so
    `tests/migration_materializer.py` can build the exact target JSON the
    real migration would write without recreating this construction logic
    a second time - one implementation, two consumers, never two competing
    ones that could silently drift apart."""
    return ErratumV2.load(candidate_v2_raw(record, reference_identities), record.path)


def candidate_v2_raw(record: Erratum, reference_identities: list[dict] | None = None) -> dict:
    """The RAW full-v2 JSON dict `candidate_v2()` parses - exposed on its
    own (final pre-migration gate, task section 7) because it IS the exact
    full-v2 target shape the real migration materializer writes for every
    non-sugar-eligible record; the materializer only needs to additionally
    flatten it into sugar shape for the 180 records eligible for that.
    Never derives an event id, an ordering edge, or a state's down-set from
    v1 array POSITION as evidence of anything - only as a stable, opaque
    label (`_event_id`) or via `ordering_proof()`'s own date-based test."""
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

    # states[]: v1's positional version chain, read faithfully. Coverage
    # (executable) and implementation_metadata (workflow/research,
    # orthogonal - task section 2) are built from the SAME per-version v1
    # implementation object but land in two SEPARATE arrays, independently:
    # a version can produce a states[] entry, an implementation_metadata[]
    # entry, both, or neither.
    relevant_indices = _relevant_indices(record)
    stray = stray_resulting_implementations(record)
    if stray:
        raise MigrationMappingQuestion(
            f"{record.id}: resulting_implementation authored on non-implementation-relevant "
            f"change(s) {stray}; a non-relevant change creates no event, so there is no "
            "defined v2 down-set for its metadata - this needs a mapping decision, not a guess"
        )
    final_relevant = final_relevant_resulting_implementations(record)
    if final_relevant:
        raise MigrationMappingQuestion(
            f"{record.id}: resulting_implementation authored on the FINAL implementation-"
            f"relevant change {final_relevant} - dead in v1's own implementation_for_version() "
            "(version_index >= len(relevant_changes()) always returns None) and v2's terminal "
            "down-set unconditionally synthesises MODERN coverage; this needs a mapping "
            "decision, not a guess"
        )
    # states[] is a COVERAGE question, answered by implementation_for_version:
    # version 0 of a zero-relevant record is the terminal/MODERN state, which
    # correctly authors no coverage.
    states = []
    for version, _ in enumerate([None] + relevant_indices[:-1] if relevant_indices else [None]):
        impl = record.implementation_for_version(version)
        if impl is None:
            continue
        coverage = _coverage_from_v1(impl)
        if coverage is not None:
            states.append({"events": [_event_id(i) for i in relevant_indices[:version]], "coverage": coverage})
    # implementation_metadata[] is a different question with a different
    # answer, so it uses the metadata-occurrence vocabulary instead: baseline
    # metadata is authored on EVERY record and maps to `[]`, terminal or not.
    implementation_metadata = []
    for down_set, impl, _label in _v1_metadata_occurrences(record):
        metadata_entry = _implementation_metadata_from_v1(impl)
        if metadata_entry is not None:
            implementation_metadata.append({"events": list(down_set), **metadata_entry})
    raw = {
        "id": record.id,
        "modern_card": {"passcode": record.modern_card.passcode, "name": record.modern_card.name},
        "classification": record.classification,
        "events": events,
        "ordering": {"edges": edges} if edges else {},
        "states": states,
        "implementation_metadata": implementation_metadata,
        "reference_identities": list(reference_identities or []),
        "review": record.raw.get("review") or {"status": "imported"},
        "sources": list(record.sources),
    }
    # Final pre-migration gate, task section 5 (corrected by a later
    # review pass, correction 2): both schemas support these two top-level
    # fields, and they were not copied here at all before - carried across
    # VERBATIM when the v1 record actually authored one (the current
    # corpus has zero, per audit_corpus()'s own reported count below, but
    # this function must not depend on that staying true).
    #
    # KEY PRESENCE, never truthiness: both schemas permit an authored
    # empty string here, and `"notes": ""` is a different authored
    # document than notes being absent entirely - dropping an authored ""
    # IS data loss, exactly as much as dropping a non-empty value would
    # be. The original version of this code used `if record.raw.get(...)`
    # (falsy-check), which silently conflated the two - a construction/
    # checker self-confirmation bug: _top_level_preserved() used to make
    # the identical truthiness mistake, so neither side ever caught it.
    if "applicable_formats_note" in record.raw:
        raw["applicable_formats_note"] = record.raw["applicable_formats_note"]
    if "notes" in record.raw:
        raw["notes"] = record.raw["notes"]
    return raw


def derive_reference_identities(record: Erratum, repo) -> list[dict]:
    """Which `reference_identities[]` entries this record's candidate v2
    would carry, derived from the REPOSITORY'S OWN format policies (task
    section 8) - never hard-coded (no format id, `reference_id`, or
    `provenance_source` string is assumed by this function). For every
    format whose `reference_parity` declares a `reference_id` AND actually
    consumes this record's historical identity (the real v1
    `parity_override()` resolution - the same one `lflist.py` uses to
    build formats today, not a re-derived approximation of it), emit one
    entry - but ONLY for records with zero relevant events. The runtime and
    validator support `reference_identities` on any record, relevant
    events or none (task section 4: "a v2 record WITH relevant behavioural
    events is allowed to carry a reference_identity"), but this migration
    tool's SCOPE (section 8) is the 11 parity-only records specifically -
    the ones Coverage cannot represent at all. A record with relevant
    events already has a working Coverage-based representation of the same
    passcode; authoring a second, redundant `reference_identities` entry
    for it is not what this task asks the migration tooling to do, so this
    function does not emit one. Most records therefore emit none; today
    exactly the 11 parity-only records do, because only GOAT declares a
    `reference_id` - but this generalises to any future reference-parity
    format without special-casing GOAT."""
    from retroformats.lflist import in_reference, parity_override

    if record.relevant_changes():
        return []
    identities: list[dict] = []
    seen_reference_ids: set[str] = set()
    for fmt_id in sorted(repo.formats):
        fmt = repo.formats[fmt_id]
        parity = fmt.reference_parity
        if not parity or not parity.get("reference_id"):
            continue
        reference_id = parity["reference_id"]
        if reference_id in seen_reference_ids:
            continue
        if not in_reference(record, parity):
            continue
        usable = parity_override(record)
        if usable is None:
            continue
        seen_reference_ids.add(reference_id)
        identities.append(
            {
                "reference_id": reference_id,
                "provenance_source": parity.get("provenance_source") or "",
                "historical_passcode": usable.get("historical_passcode"),
                "historical_variant_passcodes": list(usable.get("historical_variant_passcodes", [])),
                "upstream": usable.get("upstream"),
                "script": usable.get("script"),
            }
        )
    return identities


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


def _implementation_metadata_from_v1(impl: dict) -> dict | None:
    """Maps ONE v1 implementation object's workflow/research fields onto
    the `implementation_metadata[]` entry it would author - independent of
    `_coverage_from_v1()`, which handles only the executable Coverage
    half. `status`/`tested`/`reason` map straight across; `gap.
    upstream_checked`/`gap.behavioural_impact` nest under `gap`, mirroring
    the schema exactly (representation-gaps.md's frozen shape, task
    section 2). Returns None when the implementation carries no metadata
    field at all - nothing to author, not an empty entry (the schema
    forbids an entry with only `events`)."""
    entry: dict[str, Any] = {}
    if impl.get("status") is not None:
        entry["status"] = impl["status"]
    if impl.get("tested") is not None:
        entry["tested"] = impl["tested"]
    if impl.get("reason") is not None:
        entry["reason"] = impl["reason"]
    gap = impl.get("gap") or {}
    gap_entry: dict[str, Any] = {}
    if gap.get("upstream_checked") is not None:
        gap_entry["upstream_checked"] = gap["upstream_checked"]
    if gap.get("behavioural_impact") is not None:
        gap_entry["behavioural_impact"] = gap["behavioural_impact"]
    if gap_entry:
        entry["gap"] = gap_entry
    return entry or None


# The exact v1 fields `_implementation_metadata_from_v1()` maps into
# `implementation_metadata[]`, and therefore the fields `metadata_
# inventory()` now reports as REPRESENTED (has_v2_destination: True) -
# a genuinely different answer than before this task's implementation
# landed. Any OTHER field `metadata_inventory()` discovers stays
# unrepresented, exactly as it should: this set is not "everything we
# might ever see," only what §2's frozen shape actually maps.
KNOWN_METADATA_FIELDS = frozenset({"status", "tested", "reason", "gap.upstream_checked", "gap.behavioural_impact"})


def _v1_expected_metadata_fields(impl: dict) -> dict:
    """What ONE raw v1 implementation object's workflow/research metadata
    must become, re-derived straight from the RAW object rather than by
    calling `_implementation_metadata_from_v1()`.

    Deliberately a second, independent reading of the same v1 fields, for
    the same reason `_v1_expected_coverage_fields()` is: a checker that
    re-ran the construction helper and compared it against its own output
    would confirm only that the helper agrees with itself. It would not
    notice the helper dropping a field."""
    expected: dict[str, Any] = {}
    for field_name in ("status", "tested", "reason"):
        if impl.get(field_name) is not None:
            expected[field_name] = impl[field_name]
    gap = impl.get("gap") or {}
    for field_name in ("upstream_checked", "behavioural_impact"):
        if gap.get(field_name) is not None:
            expected[f"gap.{field_name}"] = gap[field_name]
    return expected


def _metadata_preserved(
    record: Erratum, v2: ErratumV2, event_id: Callable[[int], str] | None = None
) -> bool:
    """Independent of `candidate_v2()`'s own construction, exactly like
    `_coverage_preserved()`: re-derive what each v1 implementation OBJECT
    should carry directly from the RAW v1 record, then check the REAL
    PARSED `ImplementationMetadata` in `v2.implementation_metadata`
    actually carries it. No implementation occurrence may silently
    disappear - baseline AND every resulting_implementation are checked,
    each against its own down-set, never collapsed into one.

    Uses the SAME occurrence vocabulary as `candidate_v2()`
    (`_v1_metadata_occurrences`) so the two cannot disagree about WHICH
    objects exist, but derives the expected VALUES independently, so they
    cannot jointly agree on a wrong one. Sharing the buggy
    `implementation_for_version()` lookup between construction and checker
    is precisely how the missing baseline metadata of 21 zero-relevant
    records self-confirmed as preserved.

    `event_id`, when given, maps a v1 change INDEX to the event id the
    PARSED `v2` actually uses for it - defaults to `_event_id` (this
    module's own opaque `c{index}` scheme). `candidate_v2()`'s output
    always uses that scheme, but `migration_materializer.py`'s SUGAR shape
    does not (`_desugar_v2_sugar()` always names a sugar record's one
    event `"event"`, never `"c0"`) - checking a materialized sugar target
    with the default id would look up a key that is never present and
    report a false failure, not a true one."""
    id_for = event_id or _event_id
    field_to_attr = {
        "status": "status",
        "tested": "tested",
        "reason": "reason",
        "gap.upstream_checked": "gap_upstream_checked",
        "gap.behavioural_impact": "gap_behavioural_impact",
    }
    # down_set_ids (from _v1_metadata_occurrences) is always expressed in
    # the DEFAULT _event_id scheme; this reverses that to translate into
    # whichever scheme `id_for` actually uses.
    default_to_index = {_event_id(i): i for i in _relevant_indices(record)}
    for down_set_ids, impl, _label in _v1_metadata_occurrences(record):
        expected = _v1_expected_metadata_fields(impl)
        if not expected:
            continue  # nothing authored for this state: nothing to check
        down_set = frozenset(id_for(default_to_index[default_id]) for default_id in down_set_ids)
        metadata = v2.implementation_metadata.get(down_set)
        if metadata is None:
            return False
        for field_name, value in expected.items():
            if getattr(metadata, field_to_attr[field_name], None) != value:
                return False
    return True


REFERENCE_IDENTITY_FIELDS = (
    "reference_id",
    "provenance_source",
    "historical_passcode",
    "historical_variant_passcodes",
    "upstream",
    "script",
)
"""Every field that is part of the assertion's identity, and therefore every
field `_reference_identity_preserved()` compares. `reference_id` (WHICH
reference) and `provenance_source` (WHERE the claim is sourced) are as much
of the identity as the passcode payload is: an entry carrying the right
passcode under the wrong reference_id is a different, wrong assertion, not a
preserved one."""


def _v1_expected_reference_identities(record: Erratum, repo) -> list[dict]:
    """The EXACT `reference_identities[]` entries this record must carry,
    re-derived from the repository's OWN format policies and the RAW v1
    implementation - independently of `derive_reference_identities()`,
    exactly as `_v1_expected_coverage_fields()` is independent of
    `_coverage_from_v1()`. A checker that re-ran the construction helper
    would confirm only that it agrees with itself.

    No format id, `reference_id` or `provenance_source` string is hard-coded
    (nothing here knows GOAT exists); membership is re-derived from raw
    provenance rather than by calling `in_reference()`.

    Raises `MigrationMappingQuestion` when two formats declare the SAME
    `reference_id` with different provenance - "whichever format sorts
    first wins" is a silent, arbitrary answer to a real configuration
    conflict."""
    impl = record.implementation or {}
    policies: dict[str, tuple[str, str]] = {}  # reference_id -> (provenance, format id)
    for fmt_id in sorted(repo.formats):
        parity = repo.formats[fmt_id].reference_parity
        if not parity or not parity.get("reference_id"):
            continue
        reference_id = parity["reference_id"]
        provenance = parity.get("provenance_source") or ""
        previous = policies.get(reference_id)
        if previous is not None and previous[0] != provenance:
            raise MigrationMappingQuestion(
                f"formats {previous[1]!r} and {fmt_id!r} both declare reference_id "
                f"{reference_id!r} but disagree on provenance_source "
                f"({previous[0]!r} vs {provenance!r}); refusing to pick one by sort order"
            )
        if previous is None:
            policies[reference_id] = (provenance, fmt_id)

    # Scope (task section 8): the parity-only records - zero relevant
    # events and a usable baseline historical identity Coverage cannot
    # represent at all.
    if record.relevant_changes():
        return []
    if impl.get("strategy") not in ("reuse-upstream", "custom-script"):
        return []
    passcode = impl.get("historical_passcode")
    if not passcode or not _is_valid_passcode(passcode):
        return []
    expected = []
    for reference_id in sorted(policies):
        provenance, _fmt_id = policies[reference_id]
        if provenance and provenance not in record.sources:
            continue  # this record is not part of that reference
        expected.append(
            {
                "reference_id": reference_id,
                "provenance_source": provenance,
                "historical_passcode": passcode,
                "historical_variant_passcodes": tuple(impl.get("historical_variant_passcodes", [])),
                "upstream": impl.get("upstream"),
                "script": impl.get("script"),
            }
        )
    return expected


def _reference_identity_preserved(
    record: Erratum, v2: ErratumV2, expected_identities: list[dict] | None = None
) -> bool:
    """Does the candidate carry EXACTLY the reference-identity assertions
    the v1 record and the repository's format policies imply - no missing
    entry, no EXTRA/invented one, no duplicate semantic key - matched by
    `reference_id`, then compared across every field in
    `REFERENCE_IDENTITY_FIELDS`?

    `expected_identities` comes from `_v1_expected_reference_identities()`,
    derived independently of the candidate's own input. When None (a caller
    that did not supply one - most callers pass a real, possibly-empty
    list), there is no expectation to check and this is trivially True, the
    same answer it gave for every non-parity record before.

    Final pre-migration gate, task section 3: the previous version only
    verified every EXPECTED entry exists - subset containment, not exact
    round-trip preservation. A candidate that also carried a second,
    unexpected (even if individually well-formed) entry passed just as
    cleanly as one that carried exactly what was expected. Migrated data
    must never silently gain an assertion nobody derived. The fix is an
    exact SET comparison of reference_id keys before any field is even
    looked at: `expected_ids == actual_ids`, not `expected_ids <= actual_ids`.

    Deliberately NOT "any entry with the same passcode payload": an entry
    carrying the right passcode under the wrong `reference_id`, or sourced
    to the wrong `provenance_source`, is a different assertion. Both are
    part of the identity, so both are compared."""
    if expected_identities is None:
        return True
    expected_ids = [e["reference_id"] for e in expected_identities]
    actual_ids = [r.reference_id for r in v2.reference_identities]
    if len(expected_ids) != len(set(expected_ids)):
        return False  # the independent expectation is not itself a valid set
    if len(actual_ids) != len(set(actual_ids)):
        return False  # candidate carries a duplicate semantic key - never preserved
    if set(actual_ids) != set(expected_ids):
        return False  # exact SET equality: no missing, no extra/invented entry
    expected_by_id = {e["reference_id"]: e for e in expected_identities}
    for identity in v2.reference_identities:
        expected = expected_by_id[identity.reference_id]
        for field_name in REFERENCE_IDENTITY_FIELDS:
            actual = getattr(identity, field_name)
            if field_name == "historical_variant_passcodes":
                actual = tuple(actual)
            if actual != expected[field_name]:
                return False
    return True


def _transition_preserved(
    record: Erratum, v2: ErratumV2, event_id: Callable[[int], str] | None = None
) -> bool:
    """Independent of `candidate_v2()`'s own construction: every change's
    COMPLETE `effective` block (not merely a derived OLD/AMBIGUOUS/NEW
    verdict) and its `historical_text`/`modern_text`/`summary`/`sources`
    must survive verbatim into its candidate event's sole transition.

    The `effective` block matters on its own, separately from the
    semantic-equivalence check elsewhere in this module: that check only
    probes finitely many derived boundary dates, and a corrupted
    `precision`/`old_attested_through`/`new_attested_from` field could
    easily leave every one of those probes unchanged while still being
    real historical-record loss - documentation the record no longer
    accurately carries, even if no CURRENT snapshot happens to expose it.

    `event_id`, when given, maps a v1 change INDEX to the event id the
    PARSED `v2` actually uses for it - see `_metadata_preserved()`'s
    docstring for why this is needed for a materialized SUGAR target."""
    id_for = event_id or _event_id
    for index, change in enumerate(record.changes):
        event = v2.events.get(id_for(index))
        if event is None or not event.transitions:
            return False
        expected_effective = dict(change.get("effective") or {"date": None})
        if dict(event.effective) != expected_effective:
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
    return True


def _top_level_preserved(record: Erratum, v2: ErratumV2) -> bool:
    """Independent of `candidate_v2()`'s own construction: every top-level
    field the v1 AND v2 schemas both support - `modern_card`,
    `classification`, `sources`, `review` (including `date`/`notes`),
    `applicable_formats_note` (when authored), `notes` (when authored) -
    must survive verbatim.

    Deliberately does NOT invent an absent `review` block as data loss:
    `candidate_v2()` synthesises `{"status": "imported"}` when the v1
    record never authored one at all (schema-legal: `review` is optional
    on `erratumV1`), which is the same "absent means imported" meaning the
    v1 schema itself already carries - not a fabrication of authored
    content. `audit_corpus()`'s summary reports how many CURRENT records
    actually take that path (`review_absent_count`), rather than assuming
    it is always zero.

    `$schema` is deliberately EXCLUDED from this check: it is pure
    editor-tooling metadata (points a JSON Schema-aware editor at the
    schema file; never read by Repository.load()/Validator/lflist.py -
    verified by grep, only the importers under retroformats/importers/
    write it), and every current v1 record's `$schema` already points at
    the exact same file (`schemas/erratum.schema.json`) that also defines
    the v2 shapes - so normalising it on migration is a documented,
    lossless no-op, never historical-data loss."""
    if v2.modern_card.passcode != record.modern_card.passcode:
        return False
    if v2.modern_card.name != record.modern_card.name:
        return False
    if v2.classification != record.classification:
        return False
    if list(v2.sources) != list(record.sources):
        return False
    expected_review = record.raw.get("review") or {"status": "imported"}
    if (v2.raw.get("review") or {}) != expected_review:
        return False
    for field_name in ("applicable_formats_note", "notes"):
        # KEY PRESENCE, never truthiness (final-gate correction 2): both
        # schemas permit an authored empty string, and `"notes": ""` is a
        # different authored document than notes being absent entirely -
        # `expected_value = record.raw.get(field_name)` followed by `if
        # expected_value:` used to conflate the two (a falsy check cannot
        # distinguish "" from missing), which is exactly the construction/
        # checker self-confirmation bug candidate_v2_raw() had: both sides
        # made the identical mistake, so neither ever caught it.
        authored_presence = field_name in record.raw
        migrated_presence = field_name in v2.raw
        if authored_presence != migrated_presence:
            return False
        if authored_presence and v2.raw[field_name] != record.raw[field_name]:
            return False
    return True


def _data_preserved(
    record: Erratum, v2: ErratumV2, expected_identities: list[dict] | None = None
) -> bool:
    """Migration must not silently drop documentation fields even where
    executable behaviour is unaffected: every top-level field the two
    schemas share (`_top_level_preserved`), every change's complete
    chronology and documentation text (`_transition_preserved`), every
    coverage field with a direct v2 representation (`_coverage_preserved`),
    every workflow/research metadata field (`_metadata_preserved`), and a
    parity-only record's identity into `reference_identities[]`
    (`_reference_identity_preserved`)."""
    return (
        _top_level_preserved(record, v2)
        and _transition_preserved(record, v2)
        and _coverage_preserved(record, v2)
        and _metadata_preserved(record, v2)
        and _reference_identity_preserved(record, v2, expected_identities)
    )


def metadata_inventory(errata: dict) -> list[dict]:
    """For every v1 implementation-metadata field with no v2 coverage
    destination: how many IMPLEMENTATION OBJECTS carry it, versus how many
    DISTINCT RECORDS - a v1 record can carry more than one implementation
    object (one baseline `implementation`, plus one `resulting_
    implementation` PER RELEVANT CHANGE THAT RECORDS ONE - Necrovalley
    alone has three), so "occurrences" and "records" are genuinely
    different counts and must be reported as such, never conflated as
    "records" the way a prior pass's `record_count` did, and never
    collapsed into ONE "resulting" slot the way an even-later prior pass's
    fix still did when a record had more than one resulting_implementation
    (the second silently overwrote the first before any baseline/resulting
    comparison ran).

    Every occurrence gets an EXACT, never-overwritten locator -
    `"baseline"` or `"resulting:<change-index>"` - so `records_with_
    multiple_distinct_values` genuinely compares every value the record
    carries (baseline AND every resulting_implementation, not just
    whichever was processed last) for state-specificity. Flags ANY field
    this function does not already recognise, rather than assuming the
    known list is exhaustive forever."""
    from collections import Counter, defaultdict

    known_reason_fields = {"reason", "sources"}  # -> gap_reason/gap_sources, already preserved
    known_impl_fields = {
        "strategy",
        "historical_passcode",
        "historical_variant_passcodes",
        "upstream",
        "script",
        "gap",
    }
    # field -> list of (record_id, locator, value). `locator` is EXACT and
    # NEVER shared between two distinct implementation objects on the same
    # record - "baseline" is unique per record by construction, and
    # "resulting:<index>" is unique per change index, so N resulting
    # objects on one record are N distinct list entries, never one
    # overwritten slot.
    occurrences: dict[str, list[tuple[str, str, object]]] = defaultdict(list)

    def _collect(record_id: str, impl: dict, locator: str) -> None:
        for key, value in impl.items():
            if key not in known_impl_fields or key in ("status", "tested"):
                occurrences[key].append((record_id, locator, value))
        gap = impl.get("gap") or {}
        for key, value in gap.items():
            if key not in known_reason_fields:
                occurrences[f"gap.{key}"].append((record_id, locator, value))

    for record in errata.values():
        if not isinstance(record, Erratum):
            continue
        _collect(record.id, record.implementation or {}, "baseline")
        for index, change in enumerate(record.changes):
            resulting = change.get("resulting_implementation")
            if resulting:
                _collect(record.id, resulting, f"resulting:{index}")

    inventory = []
    for field in sorted(occurrences):
        entries = occurrences[field]
        record_ids = {rid for rid, _, _ in entries}
        baseline_entries = [(rid, loc, v) for rid, loc, v in entries if loc == "baseline"]
        resulting_entries = [(rid, loc, v) for rid, loc, v in entries if loc != "baseline"]
        baseline_record_ids = {rid for rid, _, _ in baseline_entries}
        resulting_record_ids = {rid for rid, _, _ in resulting_entries}

        by_record: dict[str, list[tuple[str, object]]] = defaultdict(list)
        for rid, loc, value in entries:
            by_record[rid].append((loc, value))
        # ALL occurrences of one record compared together - baseline AND
        # every resulting:<index> - never just "the last one processed".
        multiple_occurrences = sorted(rid for rid, occs in by_record.items() if len(occs) > 1)
        multiple_distinct_values = sorted(
            rid
            for rid, occs in by_record.items()
            if len(occs) > 1 and len({repr(v) for _, v in occs}) > 1
        )

        values = [v for _, _, v in entries]
        distinct_values = {repr(v) for v in values}
        value_distribution = (
            {repr(v): c for v, c in Counter(values).items()} if len(distinct_values) <= 10 else None
        )
        # This task implemented `implementation_metadata[]` as the v2
        # destination for exactly `KNOWN_METADATA_FIELDS` (representation-
        # gaps.md's frozen shape) - those fields are REPRESENTED now, and
        # would NOT be lost on a migration that populates the array. Any
        # OTHER field this function discovers (the one-off bare `reason`
        # is already inside KNOWN_METADATA_FIELDS; a genuinely new,
        # unrecognised field would not be) stays reported as a real gap.
        has_destination = field in KNOWN_METADATA_FIELDS
        inventory.append(
            {
                "field": field,
                "implementation_occurrence_count": len(entries),
                "unique_record_count": len(record_ids),
                "unique_record_ids": sorted(record_ids),
                "baseline_occurrence_count": len(baseline_entries),
                "resulting_implementation_occurrence_count": len(resulting_entries),
                "unique_baseline_record_count": len(baseline_record_ids),
                "unique_resulting_record_count": len(resulting_record_ids),
                "representative_baseline_ids": sorted(baseline_record_ids)[:5],
                "representative_resulting_ids": sorted(resulting_record_ids)[:5],
                "representative_occurrences": [
                    {"record": rid, "locator": loc, "value": value} for rid, loc, value in entries[:5]
                ],
                "records_with_multiple_occurrences": multiple_occurrences,
                "records_with_multiple_distinct_values": multiple_distinct_values,
                "value_distribution": value_distribution,
                "has_v2_destination": has_destination,
                "would_be_lost_on_migration": not has_destination,
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


def compare(
    record: Erratum,
    reference_identities: list[dict] | None = None,
    expected_identities: list[dict] | None = None,
) -> dict:
    """Full-boundary comparison of one record. Returns the audit row.

    `reference_identities`, when given, is merged into the candidate v2
    (task section 8) so `_data_preserved()` can verify a parity-only
    record's identity actually round-trips. `expected_identities` is the
    INDEPENDENT expectation (`_v1_expected_reference_identities()`, derived
    from the repository's format policies and the raw v1 record) that the
    round-trip is checked against - deliberately not the same list, so a
    bug in the derivation cannot confirm itself."""
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
        v2 = candidate_v2(record, reference_identities)
    except Exception as exc:  # pragma: no cover - defensive
        row.update(
            sugar_eligible=False,
            ordering_structure="unknown",
            structural_state_count=0,
            proven_edge_count=0,
            top_level_preserved=False,
            transition_preserved=False,
            coverage_preserved=False,
            metadata_preserved=False,
            reference_identity_preserved=False,
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
    # Individually-reported sub-checks, alongside the combined verdict
    # `_data_preserved()` already computes (transition text/summary/
    # sources + all three of these) - so a caller can see WHICH kind of
    # preservation failed, not just that something did.
    # Reported separately from `metadata_preserved` because it is the exact
    # thing the first implementation got wrong: for a zero-relevant record
    # `{}` is the terminal/MODERN state, so the coverage lookup answers None
    # and the authored baseline metadata silently had nowhere to go.
    baseline_metadata = _v1_expected_metadata_fields(record.implementation or {})
    row["baseline_metadata_fields"] = sorted(baseline_metadata)
    row["baseline_metadata_represented"] = (
        v2.implementation_metadata.get(frozenset()) is not None if baseline_metadata else None
    )
    row["top_level_preserved"] = _top_level_preserved(record, v2)
    row["transition_preserved"] = _transition_preserved(record, v2)
    row["coverage_preserved"] = _coverage_preserved(record, v2)
    row["metadata_preserved"] = _metadata_preserved(record, v2)
    row["reference_identity_preserved"] = _reference_identity_preserved(record, v2, expected_identities)
    row["data_preserved"] = _data_preserved(record, v2, expected_identities)
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
            return CAT_PARITY_ONLY, RESEARCH_NOT_APPLICABLE, COMPLEXITY_PARITY_ONLY_IDENTITY
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
        reference_identities = derive_reference_identities(record, repo)
        expected_identities = _v1_expected_reference_identities(record, repo)
        rows.append(compare(record, reference_identities, expected_identities))
    parity_only_count = sum(1 for r in rows if r.get("category") == CAT_PARITY_ONLY)
    unpreserved_data_ids = sorted(r["id"] for r in rows if r.get("data_preserved") is False)
    unpreserved_metadata_ids = sorted(r["id"] for r in rows if r.get("metadata_preserved") is False)
    unpreserved_reference_identity_ids = sorted(
        r["id"] for r in rows if r.get("reference_identity_preserved") is False
    )
    equivalent_count = sum(1 for r in rows if r["equivalent"])
    # The records the review's finding 1 was about: zero implementation-
    # relevant changes, so `{}` is their only (terminal/MODERN) state.
    # Reported explicitly because "no relevant events" is exactly the case
    # where a coverage-shaped lookup answers None and authored baseline
    # metadata can vanish without any check noticing.
    zero_relevant = [r for r in rows if r["relevant_event_count"] == 0]
    zero_relevant_with_metadata = [r for r in zero_relevant if r["baseline_metadata_fields"]]
    # Final pre-migration gate, task section 4: REPRESENTATION readiness,
    # re-derived from the same per-row preservation evidence
    # `data_preservation_status`/`data_not_preserved_ids` already compute -
    # never hard-coded as "0 blocked", so a future regression in any of the
    # five preservation checks _data_preserved() ANDs together (top-level,
    # transition, coverage, metadata, reference-identity) would correctly
    # move a record out of "ready" rather than silently staying green.
    representation_ready_ids = sorted(r["id"] for r in rows if r["equivalent"] and r.get("data_preserved"))
    representation_blocked_ids = sorted(
        r["id"] for r in rows if r["equivalent"] and not r.get("data_preserved")
    )
    summary = {
        "records": len(rows),
        # SEMANTIC EQUIVALENCE: selection never changes at any chronology
        # boundary. Necessary, not sufficient, for migration readiness -
        # see representation_ready / representation_blocked /
        # data_preservation_status below. Equivalence is a claim about
        # SELECTION only; it says nothing on its own about whether every
        # field a v1 record carries has a place to go in v2 - that is what
        # representation_ready/data_preserved verify separately.
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
        "data_not_preserved_ids": unpreserved_data_ids,
        "top_level_not_preserved_ids": sorted(r["id"] for r in rows if r.get("top_level_preserved") is False),
        "transition_not_preserved_ids": sorted(r["id"] for r in rows if r.get("transition_preserved") is False),
        "metadata_not_preserved_ids": unpreserved_metadata_ids,
        "reference_identity_not_preserved_ids": unpreserved_reference_identity_ids,
        # CHRONOLOGY/SHAPE STRUCTURE - a narrower, purely structural fact
        # (does this record have a states[]-representable chronology at
        # all, set aside from the 11 parity-only-identity records whose
        # only representable fact is a reference_identities[] entry, not a
        # states[] one) - deliberately NOT the migration-readiness
        # headline (task section 4 correction: it used to be reported that
        # way, and the 11 parity-only records it excluded are NOT blocked
        # any more now that reference_identities[] exists - see
        # representation_ready/representation_blocked below for the real
        # headline).
        "chronology_shape_ready": equivalent_count - parity_only_count,
        "chronology_shape_ready_ids": sorted(
            r["id"] for r in rows if r["equivalent"] and r.get("category") != CAT_PARITY_ONLY
        ),
        # REPRESENTATION READINESS - the actual migration-readiness
        # headline (task section 4), re-derived from data_preserved above,
        # never asserted. Of the 247 semantically-equivalent records, ALL
        # 247 now have a verified v2 representation (180 sugar + 35 full-v2
        # one-relevant-event-with-nonrelevant-siblings + 11 fully-ordered
        # multi-relevant + 11 parity-only-identity + 10 pure cosmetic/
        # engine) - the representation gap this task closes was the ONLY
        # thing blocking the 11 parity-only records, and it is closed.
        "representation_ready": len(representation_ready_ids),
        "representation_ready_ids": representation_ready_ids,
        "representation_blocked": len(representation_blocked_ids),
        "representation_blocked_ids": representation_blocked_ids,
        # REPRESENTATION status for the two gaps this task closes (task
        # section 8): `implementation_metadata[]`/`reference_identities[]`
        # now exist in the v2 schema/runtime/validator/consumer, and this
        # audit's own candidate construction independently verifies every
        # record's v1 metadata/identity round-trips into them
        # (metadata_preserved/reference_identity_preserved per row).
        # "representation-implemented" is NOT "migrated" - no
        # data/errata/*.json record has actually been changed; this only
        # reports that a destination now exists and preservation is
        # verified against the CANDIDATE, not against real migrated data.
        # The 247 are REPRESENTATION-READY, never called "migrated" here.
        "data_preservation_status": "representation-implemented-not-migrated",
        "data_preservation_status_detail": (
            "implementation_metadata[]/reference_identities[] now exist (docs/research/"
            "erratum-v2-representation-gaps.md); metadata_not_preserved_ids, "
            "reference_identity_not_preserved_ids, top_level_not_preserved_ids and "
            "transition_not_preserved_ids below are empty, meaning every candidate v2 "
            "round-trips its v1 metadata/identity/top-level-fields/transition-text exactly. "
            "This figure is trustworthy only because construction and checker no longer "
            "share the coverage-shaped implementation_for_version() lookup: they did, so "
            "the baseline metadata of all 21 zero-relevant records was dropped by BOTH and "
            "self-confirmed as preserved. Metadata occurrences are now enumerated "
            "separately (_v1_metadata_occurrences) and the expected VALUES are re-derived "
            "from the raw v1 objects; see zero_relevant_* below for that population "
            "reported explicitly. All 247 semantically-equivalent records are "
            "REPRESENTATION-READY (representation_ready=247, representation_blocked=0); "
            "the 11 parity_only_identity records are a CLASSIFICATION, not a blocker, now "
            "that reference_identities[] exists. No data/errata/*.json record has been "
            "migrated - this is a readiness finding about the REPRESENTATION, not a "
            "migration status."
        ),
        "parity_only_identity_count": parity_only_count,
        "parity_only_identity_ids": sorted(r["id"] for r in rows if r.get("category") == CAT_PARITY_ONLY),
        "parity_only_unrepresented_count": len(unpreserved_reference_identity_ids),
        "metadata_unrepresented_count": len(unpreserved_metadata_ids),
        # Final pre-migration gate, task section 5 (corrected by a later
        # review pass, correction 2): corpus counts for the top-level
        # fields candidate_v2_raw() did not used to copy at all - DERIVED,
        # never assumed zero. (Currently 0/0: no canonical record authors
        # applicable_formats_note/notes yet, but this audit must not
        # depend on that staying true - see _top_level_preserved().)
        # AUTHORED PRESENCE, never truthiness - an authored "" is a
        # different authored document than the key being absent, and
        # counting only non-empty values would silently under-report an
        # authored-but-empty field as "not authored at all".
        "applicable_formats_note_count": sum(
            1 for r in repo.errata.values() if isinstance(r, Erratum) and "applicable_formats_note" in r.raw
        ),
        "notes_count": sum(1 for r in repo.errata.values() if isinstance(r, Erratum) and "notes" in r.raw),
        # review.notes/review.date corpus counts, and how many records take
        # the "review absent -> synthesise {status: imported}" normalisation
        # path _top_level_preserved() deliberately does not treat as loss.
        "review_notes_count": sum(
            1 for r in repo.errata.values() if isinstance(r, Erratum) and (r.raw.get("review") or {}).get("notes")
        ),
        "review_date_count": sum(
            1 for r in repo.errata.values() if isinstance(r, Erratum) and (r.raw.get("review") or {}).get("date")
        ),
        "review_absent_count": sum(
            1 for r in repo.errata.values() if isinstance(r, Erratum) and not r.raw.get("review")
        ),
        # Finding 1's population, and the proof it is now carried.
        "zero_relevant_count": len(zero_relevant),
        "zero_relevant_ids": sorted(r["id"] for r in zero_relevant),
        "zero_relevant_with_baseline_metadata_count": len(zero_relevant_with_metadata),
        "zero_relevant_baseline_metadata_represented_count": sum(
            1 for r in zero_relevant_with_metadata if r["baseline_metadata_represented"]
        ),
        "zero_relevant_baseline_metadata_unrepresented_ids": sorted(
            r["id"] for r in zero_relevant_with_metadata if not r["baseline_metadata_represented"]
        ),
        # Baseline metadata is authored on records of EVERY shape, not only
        # zero-relevant ones; this is the corpus-wide count.
        "baseline_metadata_represented_count": sum(1 for r in rows if r["baseline_metadata_represented"]),
        "baseline_metadata_unrepresented_ids": sorted(
            r["id"] for r in rows if r["baseline_metadata_represented"] is False
        ),
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
