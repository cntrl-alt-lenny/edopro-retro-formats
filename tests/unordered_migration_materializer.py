"""Dedicated dry-run gate for the 47 researched unordered v1 records.

This module is deliberately separate from :mod:`migration_materializer`.
That module is the historical reproducibility proof for the completed 247
semantics-preserving migration; this module proves the intentionally
semantics-changing migration that will happen later.

The target constructor is still the audited low-level authority:
``migration_audit.candidate_v2_raw()``.  It is used here only in full-v2
mode: unordered records never use sugar and never acquire an ordering edge
from ``changes[]`` position.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from retroformats.cli import _report_errata
from retroformats.lflist import build_lflist, historical_identity, select_applicable_errata
from retroformats.model import Erratum, ErratumV2
from retroformats.repo import Repository
from retroformats.validate import Validator

from . import migration_audit as audit
from .migration_materializer import SCHEMA_PATH, build_shadow_repository, finding_location
from .schema_check import Registry, validate_erratum

SOURCE_COMMIT = "e7be46dbd92214140eb10d6d2a7d3e7a16bd9b62"
MANUAL_EXCLUDED_IDS = frozenset({"erratum-insect-imitation", "erratum-last-will"})
TARGET_SELECTOR = {
    "equivalent": False,
    "research_status": "already-researched",
    "migration_complexity": "unordered-researched",
}


class UnorderedMigrationGateError(AssertionError):
    """A frozen gate invariant failed; no canonical migration is attempted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UnorderedMigrationGateError(message)


def current_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def audit_scope(repo: Repository, audit_result: dict | None = None) -> dict[str, Any]:
    """Derive and freeze the 47 targets from existing audit facts only."""
    result = audit_result or audit.audit_corpus(repo)
    rows = result["rows"]
    remaining = [row for row in rows if row["equivalent"] is False]
    targets = [
        row
        for row in remaining
        if all(row.get(key) == value for key, value in TARGET_SELECTOR.items())
    ]
    manual = [row for row in remaining if row["id"] in MANUAL_EXCLUDED_IDS]
    _require(len(rows) == 49, f"audit rows changed: expected 49, got {len(rows)}")
    _require(len(remaining) == 49, f"remaining_v1 changed: expected 49, got {len(remaining)}")
    _require(len(targets) == 47, f"unordered target count changed: expected 47, got {len(targets)}")
    _require(
        {row["id"] for row in manual} == set(MANUAL_EXCLUDED_IDS),
        f"manual exclusions changed: {sorted(row['id'] for row in manual)}",
    )
    _require(
        {row["id"] for row in targets}.isdisjoint(MANUAL_EXCLUDED_IDS),
        "manual records entered the target set",
    )
    _require(
        sum(row["legacy_self_contradictory"] is True for row in targets) == 46,
        "target contradiction count changed",
    )
    _require(
        [row["id"] for row in targets if row["legacy_self_contradictory"] is not True]
        == ["erratum-yz-tank-dragon"],
        "the sole non-contradictory target is no longer YZ-Tank Dragon",
    )
    _require(
        all(row["legacy_self_contradictory"] is True for row in manual),
        "the frozen 48 self-contradictory accounting changed for manual records",
    )
    return {
        "source_commit": SOURCE_COMMIT,
        "audit_rows": rows,
        "remaining_v1": remaining,
        "targets": targets,
        "manual_excluded": sorted(MANUAL_EXCLUDED_IDS),
    }


def materialize(record: Erratum, repo: Repository) -> dict[str, Any]:
    """Build the exact future full-v2 payload for one target, dry-run only."""
    reference_identities = audit.derive_reference_identities(record, repo)
    raw = audit.candidate_v2_raw(record, reference_identities)
    _require("events" in raw and "event" not in raw, f"{record.id}: target is not full v2")
    _require("ordering" in raw, f"{record.id}: full-v2 ordering field missing")
    return {"$schema": SCHEMA_PATH, **raw}


def materialize_corpus(repo: Repository, scope: dict[str, Any]) -> dict[str, Any]:
    targets: dict[str, dict] = {}
    failures: list[dict] = []
    for row in scope["targets"]:
        record = repo.errata.get(row["id"])
        if not isinstance(record, Erratum):
            failures.append({"id": row["id"], "error": "target is not a live v1 record"})
            continue
        try:
            targets[record.id] = materialize(record, repo)
        except Exception as exc:  # report all targets together
            failures.append({"id": record.id, "error": f"{type(exc).__name__}: {exc}"})
    _require(not failures, f"target construction failed: {failures}")
    return {
        "targets": targets,
        "target_ids": sorted(targets),
        "manual_excluded": list(scope["manual_excluded"]),
        "construction_failures": failures,
        "sugar_count": sum("event" in raw for raw in targets.values()),
        "full_count": sum("events" in raw for raw in targets.values()),
    }


def _preservation_checks(record: Erratum, parsed: ErratumV2, repo: Repository) -> dict[str, bool]:
    """Use the audit's independent, field-aware preservation authorities."""
    expected_identities = audit._v1_expected_reference_identities(record, repo)
    return {
        "top_level": audit._top_level_preserved(record, parsed),
        "transitions_and_effective": audit._transition_preserved(record, parsed),
        "coverage": audit._coverage_preserved(record, parsed),
        "implementation_metadata": audit._metadata_preserved(record, parsed),
        "reference_identities": audit._reference_identity_preserved(
            record, parsed, expected_identities
        ),
        "all": audit._data_preserved(record, parsed, expected_identities),
    }


def verify_targets(repo: Repository, scope: dict[str, Any], materialized: dict[str, Any]) -> dict[str, Any]:
    """Schema-load-preservation gate over every generated target."""
    registry = Registry()
    schema_failures: list[dict] = []
    load_failures: list[dict] = []
    preservation_failures: list[dict] = []
    parsed: dict[str, ErratumV2] = {}
    for record_id, raw in materialized["targets"].items():
        errors = validate_erratum(raw, registry)
        if errors:
            schema_failures.append({"id": record_id, "errors": errors})
            continue
        try:
            parsed[record_id] = ErratumV2.load(raw, repo.errata[record_id].path)
        except Exception as exc:  # report, do not hide one bad target
            load_failures.append({"id": record_id, "error": f"{type(exc).__name__}: {exc}"})
    for record_id, parsed_record in parsed.items():
        checks = _preservation_checks(repo.errata[record_id], parsed_record, repo)
        if not checks["all"]:
            preservation_failures.append({"id": record_id, "checks": checks})

    validation_errors: list[dict] = []
    if not schema_failures and not load_failures:
        shadow = build_shadow_repository(repo, parsed)
        validator = Validator(shadow)
        validator.validate()
        location_to_id = {
            finding_location(repo, repo.errata[record_id].path): record_id
            for record_id in materialized["target_ids"]
        }
        validation_errors = [
            {"id": location_to_id[finding.location], "code": finding.code, "message": finding.message}
            for finding in validator.errors
            if finding.location in location_to_id
        ]
    return {
        "target_count": len(materialized["targets"]),
        "schema_failures": schema_failures,
        "load_failures": load_failures,
        "preservation_failures": preservation_failures,
        "shadow_validation_errors": validation_errors,
        "parsed": parsed,
    }


def _serial_state_set(states: frozenset | None) -> list[dict] | str:
    if states is None:
        return "contradictory"
    return audit._fmt_states(states)


def semantic_delta(repo: Repository, scope: dict[str, Any], parsed: dict[str, ErratumV2]) -> dict[str, Any]:
    """Exhaustive v1/v2 boundary contract; equality is intentionally not required."""
    snapshots: dict[str, list[dict]] = {}
    semantic_failures: list[dict] = []
    self_contradiction_proof: dict[str, dict] = {}
    for row in scope["targets"]:
        record = repo.errata[row["id"]]
        target = parsed[row["id"]]
        record_snapshots: list[dict] = []
        for day in audit.boundary_dates(record):
            v1_states = audit.v1_claimed_states(record, day)
            v2_states = audit.v2_claimed_states(target, day)
            v1_by_events = {events: sig for events, sig in v1_states}
            v2_by_events = {} if v2_states is None else {events: sig for events, sig in v2_states}
            # A semantic delta may add/remove event-set identities, but it may
            # not change the coverage attached to an event set that both
            # representations name.
            common = set(v1_by_events) & set(v2_by_events)
            changed_coverage = sorted(
                (sorted(events), v1_by_events[events], v2_by_events[events])
                for events in common
                if v1_by_events[events] != v2_by_events[events]
            )
            if changed_coverage:
                semantic_failures.append(
                    {"id": record.id, "date": day.isoformat(), "changed_coverage": changed_coverage}
                )
            if v1_states != v2_states:
                record_snapshots.append(
                    {
                        "date": day.isoformat(),
                        "v1": _serial_state_set(v1_states),
                        "v2": _serial_state_set(v2_states),
                        "v1_only": _serial_state_set(v1_states - (v2_states or frozenset())),
                        "v2_only": _serial_state_set((v2_states or frozenset()) - v1_states),
                    }
                )

            if record.id in self_contradiction_proof:
                continue
            selection = record.selection_at(day)
            if selection.state != "ambiguous":
                continue
            relevant = [record.changes[i] for i in audit._relevant_indices(record)]
            statuses = [audit.change_state_at(change, day) for change in relevant]
            for position in selection.candidates:
                impossible = any(status == audit.OLD for status in statuses[:position]) or any(
                    status == audit.NEW for status in statuses[position:]
                )
                if impossible:
                    events = frozenset(
                        audit._event_id(i) for i in audit._relevant_indices(record)[:position]
                    )
                    candidate = next(
                        (pair for pair in v1_states if pair[0] == events),
                        None,
                    )
                    if candidate is not None and (v2_states is None or candidate not in v2_states):
                        self_contradiction_proof[record.id] = {
                            "date": day.isoformat(),
                            "candidate": audit._fmt_states(frozenset({candidate})),
                            "statuses": statuses,
                        }
                        break
        snapshots[record.id] = record_snapshots

    delta_snapshots = sum(len(items) for items in snapshots.values())
    _require(not semantic_failures, f"coverage changed in semantic delta: {semantic_failures}")
    contradictory_ids = {
        row["id"] for row in scope["targets"] if row["legacy_self_contradictory"] is True
    }
    _require(
        contradictory_ids == set(self_contradiction_proof),
        "not every self-contradictory target has an exhaustive impossible-state proof",
    )
    return {
        "snapshots": snapshots,
        "records_with_delta": sum(bool(items) for items in snapshots.values()),
        "delta_snapshot_count": delta_snapshots,
        "semantic_failures": semantic_failures,
        "self_contradiction_proof": self_contradiction_proof,
    }


def structural_contract(repo: Repository, scope: dict[str, Any], parsed: dict[str, ErratumV2]) -> dict[str, Any]:
    """Prove event/DAG shape independently of v1/v2 outcome comparison."""
    failures: list[dict] = []
    event_counts = Counter()
    relevant_counts = Counter()
    ordering_shapes = Counter()
    authored_state_counts = Counter()
    authored_state_kinds = Counter()
    structural_state_kinds = Counter()
    for row in scope["targets"]:
        record = repo.errata[row["id"]]
        target = parsed[row["id"]]
        event_counts[len(target.events)] += 1
        relevant_counts[len(target.relevant_events())] += 1
        edge_count = len(target.raw_edges)
        ordering_shapes["empty" if edge_count == 0 else f"edges:{edge_count}"] += 1
        authored_state_counts[len(target.authored_states)] += 1
        for coverage in target.authored_states.values():
            authored_state_kinds[coverage.kind.value] += 1
        for state in target.structural_states():
            structural_state_kinds[target.state_for(state).coverage.kind.value] += 1

        if any(len(event.transitions) != 1 for event in target.events.values()):
            failures.append({"id": record.id, "error": "event merged multiple transitions"})
        if any(
            "cooccurrence_sources" in transition.raw
            for event in target.events.values()
            for transition in event.transitions
        ):
            failures.append({"id": record.id, "error": "invented cooccurrence_sources"})
        if "chains" in target.raw.get("ordering", {}):
            failures.append({"id": record.id, "error": "unordered target emitted ordering.chains"})
        expected_edges = set()
        changes = record.changes
        for before_index, before in enumerate(changes):
            for after_index, after in enumerate(changes):
                if before_index == after_index:
                    continue
                if audit.ordering_proof(
                    before.get("effective") or {"date": None},
                    after.get("effective") or {"date": None},
                ) == audit.PROVEN:
                    expected_edges.add((audit._event_id(before_index), audit._event_id(after_index)))
        actual_edges = {(edge["before"], edge["after"]) for edge in target.raw_edges}
        if actual_edges != expected_edges:
            failures.append(
                {
                    "id": record.id,
                    "error": "ordering differs from date-proven authority",
                    "actual": sorted(actual_edges),
                    "expected": sorted(expected_edges),
                }
            )
        if any(edge["basis"] != "date-proven" for edge in target.raw_edges):
            failures.append({"id": record.id, "error": "unexpected ordering basis"})
        relevant_ids = {event.id for event in target.relevant_events()}
        for state in target.structural_states():
            if state == relevant_ids:
                _require(
                    target.state_for(state).coverage.kind.value == "modern",
                    f"{record.id}: terminal state is not mechanically modern",
                )
            elif state not in target.authored_states:
                if target.state_for(state).coverage.kind.value != "unresolved":
                    failures.append(
                        {"id": record.id, "error": f"unauthored reachable state {sorted(state)} was guessed"}
                    )

    _require(not failures, f"structural contract failed: {failures}")
    return {
        "event_count_distribution": dict(sorted(event_counts.items())),
        "relevant_event_count_distribution": dict(sorted(relevant_counts.items())),
        "ordering_shape_distribution": dict(sorted(ordering_shapes.items())),
        "authored_state_count_distribution": dict(sorted(authored_state_counts.items())),
        "authored_state_kind_distribution": dict(sorted(authored_state_kinds.items())),
        "structural_state_kind_distribution": dict(sorted(structural_state_kinds.items())),
        "failures": failures,
    }


def _substitution_map(fmt, repo: Repository) -> dict[int, dict[str, Any] | None]:
    selected = select_applicable_errata(fmt, repo)
    pool = repo.pools[fmt.pool_id]
    result: dict[int, dict[str, Any] | None] = {}
    for card in pool.cards:
        override = selected.get(card.passcode)
        if override is None:
            result[card.passcode] = None
            continue
        passcode, variants = historical_identity(override.implementation)
        result[card.passcode] = {
            "erratum": override.erratum.id,
            "historical_passcode": passcode,
            "historical_variant_passcodes": list(variants),
        }
    return result


def shadow_consumers(repo: Repository, scope: dict[str, Any], materialized: dict[str, Any], parsed: dict[str, ErratumV2]) -> dict[str, Any]:
    """Run real builders, validator, substitution resolution, and reporting."""
    shadow = build_shadow_repository(repo, parsed)
    formats: dict[str, dict] = {}
    substitution_maps: dict[str, dict] = {}
    for fmt_id in sorted(repo.formats):
        fmt = repo.formats[fmt_id]
        if fmt.banlist_id not in repo.banlists or fmt.pool_id not in repo.pools:
            continue
        baseline_built = build_lflist(fmt, repo)
        shadow_built = build_lflist(shadow.formats[fmt_id], shadow)
        baseline_map = _substitution_map(fmt, repo)
        shadow_map = _substitution_map(shadow.formats[fmt_id], shadow)
        substitution_maps[fmt_id] = {
            "baseline": baseline_map,
            "shadow": shadow_map,
            "identical": baseline_map == shadow_map,
        }
        formats[fmt_id] = {
            "baseline_hash": baseline_built.hash,
            "shadow_hash": shadow_built.hash,
            "hash_identical": baseline_built.hash == shadow_built.hash,
            "text_identical": baseline_built.text == shadow_built.text,
            "entries_identical": baseline_built.entries == shadow_built.entries,
            "substitution_map_identical": baseline_map == shadow_map,
        }

    baseline_validator = Validator(repo)
    baseline_validator.validate()
    shadow_validator = Validator(shadow)
    shadow_validator.validate()
    baseline_errors = Counter(f.code for f in baseline_validator.errors)
    shadow_errors = Counter(f.code for f in shadow_validator.errors)
    baseline_warnings = Counter(f.code for f in baseline_validator.warnings)
    shadow_warnings = Counter(f.code for f in shadow_validator.warnings)
    warning_delta = {
        code: {"baseline": baseline_warnings.get(code, 0), "shadow": shadow_warnings.get(code, 0)}
        for code in sorted(set(baseline_warnings) | set(shadow_warnings))
        if baseline_warnings.get(code, 0) != shadow_warnings.get(code, 0)
    }
    warning_details = {
        code: {
            "records": sorted(
                {
                    record_id
                    for finding in [*baseline_validator.warnings, *shadow_validator.warnings]
                    if finding.code == code
                    for record_id, record in repo.errata.items()
                    if finding.location == finding_location(repo, record.path)
                }
            ),
            "classification": "unclassified-until-investigated",
        }
        for code in warning_delta
    }

    report_outputs: dict[str, str] = {}
    for label, check_repo in (("baseline", repo), ("shadow", shadow)):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            _report_errata(check_repo, verbose=True)
        report_outputs[label] = output.getvalue()

    return {
        "shadow_repository": shadow,
        "formats": formats,
        "substitution_maps": substitution_maps,
        "baseline_error_count": len(baseline_validator.errors),
        "shadow_error_count": len(shadow_validator.errors),
        "baseline_error_codes": dict(baseline_errors),
        "shadow_error_codes": dict(shadow_errors),
        "new_error_codes": {
            code: shadow_errors[code] - baseline_errors.get(code, 0)
            for code in shadow_errors
            if shadow_errors[code] > baseline_errors.get(code, 0)
        },
        "baseline_warning_count": len(baseline_validator.warnings),
        "shadow_warning_count": len(shadow_validator.warnings),
        "baseline_warning_codes": dict(baseline_warnings),
        "shadow_warning_codes": dict(shadow_warnings),
        "warning_code_delta": warning_delta,
        "warning_delta_details": warning_details,
        "report_outputs": report_outputs,
    }


def run_gate(repo: Repository | None = None) -> dict[str, Any]:
    repo = repo or Repository.load(audit.REPO_ROOT)
    scope = audit_scope(repo)
    materialized = materialize_corpus(repo, scope)
    verification = verify_targets(repo, scope, materialized)
    _require(not verification["schema_failures"], f"schema failures: {verification['schema_failures']}")
    _require(not verification["load_failures"], f"load failures: {verification['load_failures']}")
    _require(
        not verification["preservation_failures"],
        f"preservation failures: {verification['preservation_failures']}",
    )
    _require(
        not verification["shadow_validation_errors"],
        f"target validation errors: {verification['shadow_validation_errors']}",
    )
    parsed = verification["parsed"]
    semantics = semantic_delta(repo, scope, parsed)
    structural = structural_contract(repo, scope, parsed)
    consumers = shadow_consumers(repo, scope, materialized, parsed)
    _require(consumers["baseline_error_count"] == 0, "baseline validator has errors")
    _require(consumers["shadow_error_count"] == 0, "shadow validator has errors")
    _require(consumers["new_error_codes"] == {}, f"new validator errors: {consumers['new_error_codes']}")
    _require(consumers["warning_code_delta"] == {}, f"validator warning delta: {consumers['warning_code_delta']}")
    _require(materialized["sugar_count"] == 0 and materialized["full_count"] == 47, "target shape counts changed")
    _require(set(scope["manual_excluded"]) == MANUAL_EXCLUDED_IDS, "manual exclusion set changed")
    for manual_id in MANUAL_EXCLUDED_IDS:
        _require(repo.errata[manual_id] is consumers["shadow_repository"].errata[manual_id], f"{manual_id} was replaced")

    return {
        "source_commit": SOURCE_COMMIT,
        "current_head_at_run": current_head(repo.root),
        "target_ids": scope["targets"],
        "manual_excluded": scope["manual_excluded"],
        "materialized": {k: v for k, v in materialized.items() if k != "targets"},
        "target_payloads": materialized["targets"],
        "verification": {k: v for k, v in verification.items() if k != "parsed"},
        "structural": structural,
        "semantic_delta": semantics,
        "consumers": {k: v for k, v in consumers.items() if k != "shadow_repository"},
        "shadow_repository": consumers["shadow_repository"],
        "parsed": parsed,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    result = run_gate()
    print(json.dumps(result, indent=2, default=str))
