"""The REAL v1 -> v2 migration materializer (final pre-migration gate, task
section 7). Produces the EXACT target JSON shape a future migration commit
would write to `data/errata/<id>.json` for each of the 247 semantically-
equivalent records - dry run only, never writes canonical data.

Two target shapes, chosen deterministically per record, never guessed:

- **sugar** (180 records): the flattened single-event/single-transition
  `event`/`coverage` shape (`erratumV2Sugar` in the schema), for a record
  with exactly one event, one relevant transition, AND an authorable
  baseline coverage (sugar's `coverage` is schema-REQUIRED - a baseline
  whose v1 strategy is `unresolved` with no gap has nothing to author
  there, so such a record cannot use sugar even with one event; the
  current corpus has none, verified rather than assumed - see
  `is_sugar_eligible()`).
- **full v2** (67 records): `events{}`/`ordering`/`states[]`, for
  everything else - 35 one-relevant-event-with-nonrelevant-siblings + 11
  fully-ordered multi-relevant + 11 parity-only-identity (zero relevant
  events) + 10 pure cosmetic/engine (zero relevant events).

Reuses `migration_audit.candidate_v2_raw()` for the full-v2 shape
directly - it already builds exactly this dict, reviewed and tested
extensively by the semantic-audit half of this task. The sugar shape is
a flattening of that same dict, never a second, independently-derived
construction: `_to_sugar()` converts `candidate_v2_raw()`'s output rather
than re-deriving events/states from the v1 record a second time, so the
two shapes cannot silently drift apart from each other.

Never derives an ordering edge from v1 array position - `candidate_v2_raw()`
already guarantees that (`ordering_proof()`, date-based, is the only
evidence for an edge), and this module adds no ordering logic of its own.

Nothing here writes to `data/errata/`. This module is read-only, exactly
like `migration_audit.py`.
"""

from __future__ import annotations

from typing import Any

from retroformats.model import Erratum
from retroformats.repo import Repository

from . import migration_audit as audit

SCHEMA_PATH = "../../schemas/erratum.schema.json"
"""The exact `$schema` value every current v1 record carries (verified:
296/296, one value, `schemas/erratum.schema.json` - the SAME file that
defines the v2/sugar shapes too, see docs/research/erratum-v2-migration-
audit.md's `$schema` normalisation note). Pure editor-tooling metadata,
never read by any consumer; authored here purely for editor convenience,
matching the existing corpus convention."""


def is_sugar_eligible(record: Erratum) -> bool:
    """Exactly one event in total, exactly one relevant event, AND an
    authorable baseline coverage. The first two conditions match
    `migration_audit.compare()`'s existing `sugar_eligible` field; the
    third is this module's own addition, because sugar's `coverage` is
    schema-REQUIRED (`erratumV2Sugar`) while full v2's `states[]` has no
    such requirement - a record whose v1 baseline is `unresolved` with no
    gap has nothing to author there and cannot become sugar even with one
    event. The current 180-record corpus has none (verified, not assumed:
    `MaterializerShapeTest.test_every_sugar_eligible_record_has_an_
    authorable_baseline`), so this never actually demotes one of the 180 -
    but the tool must not depend on that staying true."""
    if len(record.changes) != 1:
        return False
    relevant = audit._relevant_indices(record)
    if len(relevant) != 1:
        return False
    impl = record.implementation_for_version(0)
    if impl is None:
        return False
    return audit._coverage_from_v1(impl) is not None


def _to_sugar(full_raw: dict) -> dict:
    """Flatten a single-event full-v2 raw dict (as `candidate_v2_raw()`
    builds it for a sugar-eligible record) into the `event`/`coverage`
    sugar shape `_desugar_v2_sugar()` (retroformats/model.py) inverts back
    to the same full shape. A pure reshaping of already-derived data -
    every field's VALUE comes from `full_raw`, none is re-derived from the
    v1 record here."""
    events = full_raw["events"]
    if len(events) != 1:
        raise ValueError(f"_to_sugar() requires exactly one event, got {len(events)}")
    (event_id, event), = events.items()
    transition = event["transitions"][0]
    sugar: dict[str, Any] = {k: v for k, v in full_raw.items() if k not in ("events", "ordering", "states")}
    sugar["event"] = {
        "effective": event["effective"],
        "kind": transition["kind"],
        "axis": transition["axis"],
        "historical_text": transition["historical_text"],
        "modern_text": transition["modern_text"],
        "summary": transition["summary"],
        "sources": list(transition["sources"]),
    }
    baseline = next((s for s in full_raw.get("states") or [] if not s.get("events")), None)
    if baseline is None:
        raise ValueError(
            "_to_sugar() requires an authored baseline ({}) coverage - the caller must check "
            "is_sugar_eligible() first, which verifies exactly this"
        )
    sugar["coverage"] = baseline["coverage"]
    # implementation_metadata[]'s `events` id lists reference the full
    # shape's opaque event id (e.g. "c0"); _desugar_v2_sugar() always
    # synthesises the literal id "event" for the sugar's one event, so
    # every occurrence of the old id is rewritten to match - never left
    # pointing at an id the sugar shape does not have.
    sugar["implementation_metadata"] = [
        {**entry, "events": ["event" if e == event_id else e for e in entry.get("events", [])]}
        for entry in full_raw.get("implementation_metadata", [])
    ]
    return sugar


def materialize(record: Erratum, repo) -> dict[str, Any]:
    """The exact target v1->v2 migration JSON for `record` - sugar when
    eligible, full v2 otherwise, `$schema` set for editor convenience.
    Dry run: builds and returns the raw dict, never writes it. Raises
    `migration_audit.MigrationMappingQuestion` for the same shapes
    `candidate_v2()` refuses to guess at (a stray or final-relevant
    `resulting_implementation`) - this function does not add a second,
    looser tolerance for those."""
    reference_identities = audit.derive_reference_identities(record, repo)
    full_raw = audit.candidate_v2_raw(record, reference_identities)
    target = _to_sugar(full_raw) if is_sugar_eligible(record) else full_raw
    return {"$schema": SCHEMA_PATH, **target}


def materialize_corpus(repo=None, rows: list[dict] | None = None) -> dict[str, Any]:
    """Every one of the 247 semantically-equivalent records' materialized
    target. The 49 non-equivalent records are deliberately EXCLUDED, never
    guessed at - `excluded_ids` names them so a caller can confirm the
    exclusion is exactly the frozen 49, not a silent drop of something
    else.

    `rows` lets a caller (the shadow-migration harness, section 8) pass in
    an already-computed `audit_corpus()["rows"]` rather than re-running
    the full corpus comparison a second time; `repo` likewise avoids a
    second `Repository.load()`. Both default to fresh values when the
    caller has none to share."""
    if repo is None:
        repo = Repository.load(audit.REPO_ROOT)
    if rows is None:
        rows = audit.audit_corpus()["rows"]

    targets: dict[str, dict] = {}
    shapes: dict[str, str] = {}
    for row in rows:
        if not row["equivalent"]:
            continue
        record = repo.errata[row["id"]]
        raw = materialize(record, repo)
        targets[row["id"]] = raw
        shapes[row["id"]] = "sugar" if "event" in raw else "full"

    excluded_ids = sorted(r["id"] for r in rows if not r["equivalent"])
    return {
        "targets": targets,
        "shapes": shapes,
        "sugar_ids": sorted(rid for rid, shape in shapes.items() if shape == "sugar"),
        "full_ids": sorted(rid for rid, shape in shapes.items() if shape == "full"),
        "excluded_ids": excluded_ids,
    }


def finding_location(repo, path) -> str:
    """The exact string `Validator.Finding.location` would carry for
    `path` under `repo.root` - replicates `Validator._emit()`'s own
    `str(location)[len(str(root)):].lstrip("/")` transformation exactly
    (raw OS path text, native separators - `\\data\\errata\\x.json` on
    Windows, NOT `pathlib`'s always-forward-slash `Path.relative_to()`
    rendering, which does not match a real `Finding.location` string on
    Windows at all). Callers that need to map a `Finding` back to the
    record/format that produced it must build their lookup with this
    function, not with `path.relative_to(repo.root)`."""
    root = str(repo.root)
    loc = str(path)
    if loc.startswith(root):
        loc = loc[len(root) :].lstrip("/")
    return loc


def build_shadow_repository(repo, replacement_records: dict[str, Any]):
    """A NEW `Repository` whose `errata` table replaces exactly the given
    records (keyed by id) and leaves every other field - banlists, pools,
    rule profiles, formats, sources, card index, products, release
    coverage/gaps, import report - IDENTICAL to `repo`'s (same objects,
    not copies: none of this is ever mutated). `repo` itself is never
    mutated either (a fresh `errata` dict is built via `dict(repo.errata)`
    then `.update()`-ed, `repo.errata` itself is untouched).

    Used by both `verify_materialized_corpus()` (section 9, semantic
    validation of the materialized targets alone) and the shadow-migration
    harness (section 8, the full baseline-vs-shadow consumer comparison) -
    one shared construction so the two cannot build subtly different
    shadow repositories."""
    shadow_errata = dict(repo.errata)
    shadow_errata.update(replacement_records)
    return Repository(
        root=repo.root,
        banlists=repo.banlists,
        pools=repo.pools,
        rule_profiles=repo.rule_profiles,
        errata=shadow_errata,
        formats=repo.formats,
        global_sources=repo.global_sources,
        format_sources=repo.format_sources,
        card_index=repo.card_index,
        products=repo.products,
        release_coverage=repo.release_coverage,
        release_gaps=repo.release_gaps,
        import_report=repo.import_report,
    )


def verify_materialized_corpus(repo=None, rows: list[dict] | None = None) -> dict[str, Any]:
    """Final pre-migration gate, task section 9: for every one of the 247
    materialized targets - pass the project's REAL erratum schema checker
    (`tests/schema_check.py`, the same one `tests/test_erratum_schema.py`
    uses), load it through `ErratumV2.load()` exactly like `Repository.
    load()` would, pass production semantic validation
    (`retroformats.validate.Validator`), and independently re-verify every
    preservation dimension `migration_audit._data_preserved()` checks -
    against the MATERIALIZED target specifically, not merely against
    `candidate_v2()`'s always-full-shape output, since the two can differ
    for the 180 sugar targets (a different event-id scheme; see
    `_metadata_preserved()`/`_transition_preserved()`'s `event_id` param).

    Returns exactly the summary shape this task's section 9 requires."""
    from retroformats.model import ErratumV2
    from retroformats.validate import Validator

    from .schema_check import Registry, validate_erratum

    if repo is None:
        repo = Repository.load(audit.REPO_ROOT)
    if rows is None:
        rows = audit.audit_corpus()["rows"]
    materialized = materialize_corpus(repo, rows)
    registry = Registry()

    schema_failures: list[dict] = []
    load_failures: list[dict] = []
    preservation_failures: list[dict] = []
    parsed: dict[str, ErratumV2] = {}

    for record_id, raw in materialized["targets"].items():
        errors = validate_erratum(raw, registry)
        if errors:
            schema_failures.append({"id": record_id, "errors": errors})
            continue  # cannot safely parse/preservation-check what failed schema
        record = repo.errata[record_id]
        try:
            parsed[record_id] = ErratumV2.load(raw, record.path)
        except Exception as exc:  # noqa: BLE001 - report, never crash the audit itself
            load_failures.append({"id": record_id, "error": f"{type(exc).__name__}: {exc}"})

    for record_id, v2 in parsed.items():
        record = repo.errata[record_id]
        shape = materialized["shapes"][record_id]
        # A materialized SUGAR target's one event is always named "event"
        # (_desugar_v2_sugar()'s own choice), never candidate_v2()'s
        # opaque "c0" - only relevant since a sugar record has exactly one
        # change, at index 0, by is_sugar_eligible()'s own definition.
        id_for = (lambda _i: "event") if shape == "sugar" else None
        expected_identities = audit._v1_expected_reference_identities(record, repo)
        ok = (
            audit._top_level_preserved(record, v2)
            and audit._transition_preserved(record, v2, id_for)
            and audit._coverage_preserved(record, v2)
            and audit._metadata_preserved(record, v2, id_for)
            and audit._reference_identity_preserved(record, v2, expected_identities)
        )
        if not ok:
            preservation_failures.append({"id": record_id, "shape": shape})

    # Semantic validation runs on a REPOSITORY, not a single record - build
    # a shadow repo whose errata table replaces exactly these 247 with
    # their parsed materialized targets, and validate that (never the
    # real on-disk repo, and never written back to it).
    validation_errors: list[dict] = []
    if len(parsed) == len(materialized["targets"]):  # only meaningful once everything parses
        shadow_repo = build_shadow_repository(repo, parsed)
        validator = Validator(shadow_repo)
        validator.validate()
        # Map each materialized record's OWN real on-disk path
        # (ErratumV2.load() above was given record.path explicitly, so a
        # materialized v2's Finding location is identical to its v1
        # original's) back to its id, using the EXACT string form
        # Validator._emit() produces (finding_location() - never
        # Path.relative_to(), which renders differently on Windows and
        # would never match a real Finding.location there), so errors are
        # attributed correctly rather than by fragile string containment.
        path_to_id = {finding_location(repo, repo.errata[rid].path): rid for rid in materialized["targets"]}
        # Only errors ON one of the 247 materialized records: the shadow
        # repo also re-validates the untouched 49 + everything else, which
        # must stay clean regardless (the shadow-migration harness, section
        # 8, checks that directly) - section 9 itself only asks about the
        # 247 this materializer actually generated.
        validation_errors = [
            {"id": path_to_id[e.location], "code": e.code, "message": e.message}
            for e in validator.errors
            if e.location in path_to_id
        ]

    return {
        "generated_target_count": len(materialized["targets"]),
        "sugar_target_count": len(materialized["sugar_ids"]),
        "full_target_count": len(materialized["full_ids"]),
        "schema_failures": schema_failures,
        "load_failures": load_failures,
        "preservation_failures": preservation_failures,
        "validation_errors": validation_errors,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    verification = verify_materialized_corpus()
    print(json.dumps({k: v for k, v in verification.items()}, indent=2, default=list))
