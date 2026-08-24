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
# fields on each row for the facts it is derived from) ----------------------
CAT_SUGAR = "sugar-eligible"
CAT_FULL_SINGLE = "full-v2-single-event"
CAT_MULTI_ORDERED = "full-v2-multi-event-ordered"
CAT_MULTI_UNORDERED = "full-v2-multi-event-unordered"
CAT_NONRELEVANT_CHRONOLOGY = "nonrelevant-event-constrains-relevant"
CAT_PARITY_ONLY = "parity-only-identity"
CAT_COSMETIC_ONLY = "no-historical-state"
CAT_BLOCKER = "manual-review-blocker"

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
    exactly matching what "unresolved, undocumented" already means)."""
    strategy = impl.get("strategy")
    if strategy == "reuse-upstream":
        passcode, upstream = impl.get("historical_passcode"), impl.get("upstream")
        if not passcode or not upstream:
            raise MigrationDataMissing(
                "reuse-upstream implementation is missing "
                f"{'historical_passcode' if not passcode else 'upstream'} - v2 cannot author "
                "this coverage without inventing a value"
            )
        return {
            "kind": "reuse-upstream",
            "historical_passcode": passcode,
            "historical_variant_passcodes": list(impl.get("historical_variant_passcodes", [])),
            "upstream": upstream,
        }
    if strategy == "custom-script":
        passcode, script = impl.get("historical_passcode"), impl.get("script")
        if not passcode or not script:
            raise MigrationDataMissing(
                "custom-script implementation is missing "
                f"{'historical_passcode' if not passcode else 'script'} - v2 cannot author "
                "this coverage without inventing a value"
            )
        return {
            "kind": "custom-script",
            "historical_passcode": passcode,
            "historical_variant_passcodes": list(impl.get("historical_variant_passcodes", [])),
            "script": script,
        }
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


def _data_preserved(record: Erratum, v2: ErratumV2) -> bool:
    """Migration must not silently drop documentation fields even where
    executable behaviour is unaffected: every change's historical_text,
    modern_text, summary and sources must survive verbatim into its
    candidate event's sole transition."""
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
    return True


# --- semantic outcome comparison ---------------------------------------------
# A "state" is compared as (frozenset of event ids, coverage signature) - NEVER
# as an integer, a cardinality, or a version index. Two states with the same
# `len(events)` but different identities (`{A}` vs `{B}`) are different states.

def _v1_coverage_signature(impl: dict | None) -> tuple:
    """What v1's OWN `selection_at()` determinate branch treats this
    implementation as executing, restated as a comparable tuple - mirrors
    that branch's exact logic rather than a reinvented rule, so "claimed"
    can never silently drift from what v1 actually does when determinate."""
    if impl is None or impl.get("strategy") == "unresolved":
        gap = (impl or {}).get("gap")
        return ("gap", "known") if gap else ("gap", "unresolved")
    if impl.get("strategy") == "none-needed":
        return ("modern",)
    passcode = impl.get("historical_passcode")
    if not passcode or not _is_valid_passcode(passcode):
        return ("gap", "unresolved")
    return ("historical", passcode, tuple(impl.get("historical_variant_passcodes", ())))


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
    if coverage.kind in (Coverage.MODERN, Coverage.NONE_NEEDED):
        return ("modern",)
    if coverage.kind in (Coverage.REUSE_UPSTREAM, Coverage.CUSTOM_SCRIPT):
        if not coverage.historical_passcode or not _is_valid_passcode(coverage.historical_passcode):
            return ("gap", "unresolved")
        return ("historical", coverage.historical_passcode, tuple(coverage.historical_variant_passcodes))
    if coverage.kind == Coverage.KNOWN_GAP:
        return ("gap", "known")
    return ("gap", "unresolved")  # UNRESOLVED


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
            mismatch_count=None,
            first_mismatches=[],
            contradictory_at=[],
            reason=f"candidate-v2 construction failed: {exc}",
            category=CAT_BLOCKER,
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
    row["mismatch_count"] = len(mismatches)
    row["first_mismatches"] = mismatches[:5]
    row["contradictory_at"] = contradictory_at
    row["category"] = categorise(row, record, v2)
    return row


def categorise(row: dict, record: Erratum, v2: ErratumV2) -> str:
    if row["relevant_event_count"] == 0:
        return CAT_PARITY_ONLY if row["parity_only_identity"] else CAT_COSMETIC_ONLY
    if not row["equivalent"]:
        if row["nonrelevant_event_count"] and _nonrelevant_is_implicated(record, v2):
            return CAT_NONRELEVANT_CHRONOLOGY
        return CAT_BLOCKER
    if row["sugar_eligible"]:
        return CAT_SUGAR
    if row["relevant_event_count"] == 1:
        return CAT_FULL_SINGLE
    return CAT_MULTI_ORDERED if row["ordering_structure"] == ORDER_FULL else CAT_MULTI_UNORDERED


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
    summary = {
        "records": len(rows),
        "equivalent": sum(1 for r in rows if r["equivalent"]),
        "not_equivalent": sum(1 for r in rows if not r["equivalent"]),
        "not_equivalent_ids": sorted(r["id"] for r in rows if not r["equivalent"]),
        "legacy_self_contradictory_count": sum(1 for r in rows if r.get("legacy_self_contradictory")),
        "legacy_self_contradictory_ids": sorted(r["id"] for r in rows if r.get("legacy_self_contradictory")),
        "sugar_eligible_count": sum(1 for r in rows if r.get("sugar_eligible")),
        "ordering_structure": dict(Counter(r.get("ordering_structure") for r in rows)),
        "categories": dict(Counter(r["category"] for r in rows)),
        "data_not_preserved_ids": sorted(r["id"] for r in rows if r.get("data_preserved") is False),
    }
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
