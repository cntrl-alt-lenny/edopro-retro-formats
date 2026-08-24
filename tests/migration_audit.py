"""Deterministic v1 -> v2 migration audit, computed from the CURRENT runtime.

This is the tool behind `docs/research/erratum-v2-migration-audit.md`. It
exists as code, re-runnable, rather than as numbers pasted into prose: the
migration partition is an OUTPUT derived from evidence, never an input
assumption carried forward from an earlier pass.

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

2. Compares v1 and candidate-v2 selection at EVERY chronology boundary the
   record can have. The comparison is exact and finite, not sampled: an
   event's OLD/AMBIGUOUS/NEW status only changes at the handful of dates its
   own evidence names, so the union of those dates (each probed at the day
   before, on, and the day after) covers every distinguishable snapshot.

3. Classifies the record by WHY it is or is not equivalence-safe.

Nothing here writes to data/errata/. The audit is read-only.
"""

from __future__ import annotations

import datetime as _dt
import json
from collections import Counter
from pathlib import Path

from retroformats.model import (
    IMPLEMENTATION_RELEVANT_KINDS,
    _precision_bounds,
    PROVEN,
    Coverage,
    Erratum,
    ErratumV2,
    SelectionError,
    ordering_proof,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- categories -------------------------------------------------------------
CAT_SUGAR = "sugar-eligible"
CAT_FULL_SINGLE = "full-v2-single-event"
CAT_MULTI_ORDERED = "full-v2-multi-event-ordered"
CAT_MULTI_UNORDERED = "full-v2-multi-event-unordered"
CAT_NONRELEVANT_CHRONOLOGY = "nonrelevant-event-constrains-relevant"
CAT_PARITY_ONLY = "parity-only-identity"
CAT_COSMETIC_ONLY = "no-historical-state"
CAT_BLOCKER = "manual-review-blocker"


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
    relevant_indices = [
        i for i, c in enumerate(record.changes) if c.get("kind") in IMPLEMENTATION_RELEVANT_KINDS
    ]
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


def _coverage_from_v1(impl: dict) -> dict:
    strategy = impl.get("strategy")
    if strategy == "reuse-upstream":
        return {
            "kind": "reuse-upstream",
            "historical_passcode": impl.get("historical_passcode"),
            "historical_variant_passcodes": list(impl.get("historical_variant_passcodes", [])),
            "upstream": impl.get("upstream") or "ProjectIgnis",
        }
    if strategy == "custom-script":
        return {
            "kind": "custom-script",
            "historical_passcode": impl.get("historical_passcode"),
            "historical_variant_passcodes": list(impl.get("historical_variant_passcodes", [])),
            "script": impl.get("script") or "dist/scripts/unknown.lua",
        }
    if strategy == "none-needed":
        return {"kind": "none-needed"}
    gap = impl.get("gap") or {}
    if strategy == "unresolved" and gap:
        return {
            "kind": "known-gap",
            "gap_reason": gap.get("reason") or "unspecified",
            "gap_sources": list(gap.get("sources") or ["ignis-babelcdb"]),
        }
    if strategy == "unresolved":
        # An unresolved v1 implementation with no acknowledged gap has no
        # authorable v2 coverage at all: 'unresolved' is never authored, it is
        # the mechanical default for an unauthored state. Returning None makes
        # the caller OMIT the state, which is exactly how v2 spells it.
        return None
    raise ValueError(f"no v2 coverage mapping for v1 strategy {strategy!r}")


# --- outcome comparison -----------------------------------------------------

def v1_outcome(record: Erratum, day: _dt.date) -> tuple:
    """What legacy v1 selection would execute at `day`, as a comparable
    tuple: the chronology verdict plus the concrete identity, if any."""
    selection = record.selection_at(day)
    if selection.state == "historical":
        impl = selection.implementation or {}
        return ("historical", impl.get("historical_passcode"),
                tuple(impl.get("historical_variant_passcodes", ())))
    if selection.state == "modern":
        return ("modern",)
    if selection.state == "gap":
        return ("gap",)
    return ("ambiguous", tuple(sorted(selection.candidates)))


def v2_outcome(record: ErratumV2, day: _dt.date) -> tuple:
    """The same question of the candidate v2 record, mapped onto the same
    vocabulary so the two are directly comparable."""
    try:
        selection = record.selection_at(day)
    except SelectionError:
        return ("contradictory",)
    all_relevant = frozenset(e.id for e in record.relevant_events())
    if selection.chronology == "determinate":
        state = selection.candidates[0]
        if state.events == all_relevant:
            return ("modern",)
        coverage = state.coverage
        if coverage.kind in (Coverage.REUSE_UPSTREAM, Coverage.CUSTOM_SCRIPT):
            return ("historical", coverage.historical_passcode,
                    tuple(coverage.historical_variant_passcodes))
        if coverage.kind == Coverage.NONE_NEEDED:
            return ("modern",)
        return ("gap",)
    # Ambiguous: compare the SET of plausible relevant-event down-sets, as
    # index-sets, against v1's candidate version indices.
    relevant_sorted = [e.id for e in record.relevant_events()]
    indices = []
    for candidate in selection.candidates:
        indices.append(len(candidate.events))
    return ("ambiguous", tuple(sorted(set(indices))))


def compare(record: Erratum) -> dict:
    """Full-boundary comparison of one record. Returns the audit row."""
    row: dict = {
        "id": record.id,
        "classification": record.classification,
        "changes": len(record.changes),
        "relevant_changes": len(record.relevant_changes()),
        "nonrelevant_changes": len(record.changes) - len(record.relevant_changes()),
        "baseline_strategy": (record.implementation or {}).get("strategy"),
        "baseline_passcode": (record.implementation or {}).get("historical_passcode"),
        "sources": list(record.sources),
        "change_kinds": [c.get("kind") for c in record.changes],
    }
    try:
        v2 = candidate_v2(record)
    except Exception as exc:  # pragma: no cover - defensive
        row.update(equivalent=False, reason=f"candidate-v2 construction failed: {exc}",
                   category=CAT_BLOCKER)
        return row
    row["proven_edges"] = len(v2.raw_edges)
    mismatches = []
    for day in boundary_dates(record):
        a, b = v1_outcome(record, day), v2_outcome(v2, day)
        if a != b:
            mismatches.append({"date": day.isoformat(), "v1": list(a), "v2": list(b)})
    row["equivalent"] = not mismatches
    row["mismatch_count"] = len(mismatches)
    row["first_mismatches"] = mismatches[:3]
    row["category"] = categorise(record, v2, row)
    return row


def categorise(record: Erratum, v2: ErratumV2, row: dict) -> str:
    relevant = row["relevant_changes"]
    total = row["changes"]
    if relevant == 0:
        # No implementation-relevant history at all. Whether this is merely a
        # cosmetic record or a parity-only IDENTITY question depends on
        # whether v1 still carries a usable historical passcode.
        impl = record.implementation or {}
        usable = impl.get("strategy") in ("reuse-upstream", "custom-script") and impl.get(
            "historical_passcode"
        )
        return CAT_PARITY_ONLY if usable else CAT_COSMETIC_ONLY
    if not row["equivalent"]:
        if row["nonrelevant_changes"] and _nonrelevant_is_implicated(record, v2):
            return CAT_NONRELEVANT_CHRONOLOGY
        return CAT_BLOCKER
    if total == 1 and relevant == 1:
        return CAT_SUGAR
    if relevant == 1:
        return CAT_FULL_SINGLE
    return CAT_MULTI_ORDERED if row["proven_edges"] else CAT_MULTI_UNORDERED


def _nonrelevant_is_implicated(record: Erratum, v2: ErratumV2) -> bool:
    """Would the record become equivalent if its cosmetic/engine changes were
    dropped entirely? If so, the difference is CAUSED by a non-relevant
    event's chronology participating in down-set reasoning - the exact
    behaviour a114ee3 introduced and the stale design text still denies."""
    trimmed_changes = [
        c for c in record.changes if c.get("kind") in IMPLEMENTATION_RELEVANT_KINDS
    ]
    if len(trimmed_changes) == len(record.changes):
        return False
    trimmed = Erratum.load({**record.raw, "changes": trimmed_changes}, record.path)
    try:
        trimmed_v2 = candidate_v2(trimmed)
    except Exception:  # pragma: no cover - defensive
        return False
    for day in boundary_dates(trimmed):
        if v1_outcome(trimmed, day) != v2_outcome(trimmed_v2, day):
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
        "categories": dict(Counter(r["category"] for r in rows)),
    }
    return {"summary": summary, "rows": rows}


def parity_only_consumption(rows: list[dict]) -> dict:
    """Objective 4: for every zero-relevant record that nevertheless carries a
    usable historical identity, does any CURRENT format actually consume that
    identity, and would dropping it change generated output?"""
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
