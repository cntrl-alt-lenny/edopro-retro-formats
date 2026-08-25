"""The decisive final pre-migration gate (task section 8): shadow-migrate
all 247 semantically-equivalent records IN MEMORY and compare every real
consumer's output against the untouched baseline.

Two in-memory repositories, built from the SAME on-disk data:

- **BASELINE**: `Repository.load()`, completely untouched - every record
  stays v1.
- **SHADOW**: the 247 semantically-equivalent records replaced by their
  ACTUAL migration-materializer targets (`migration_materializer.py`'s
  real sugar/full-v2 shapes, parsed through the real `ErratumV2.load()`,
  never `candidate_v2()`'s audit-only candidate); the 49 non-equivalent
  records are left untouched v1, exactly as they will be after the real
  (future) migration too, since this task migrates nothing else.

Every real consumer function (`build_lflist`, `Validator`) is run against
BOTH, unmodified - this module adds no special-cased "shadow mode" to any
consumer. Nothing here writes to `data/errata/`; both repositories are
built from the same on-disk files and neither is ever saved back.
"""

from __future__ import annotations

from typing import Any

from retroformats.lflist import build_lflist
from retroformats.model import ErratumV2
from retroformats.repo import Repository
from retroformats.validate import Validator

from . import migration_audit as audit
from . import migration_materializer as mm


def build_shadow_and_baseline(repo=None, rows: list[dict] | None = None):
    """`(baseline_repo, shadow_repo, materialized)` - the two repositories
    section 8 compares, plus the materializer result that built the
    shadow's replacement records (so a caller can inspect exactly what
    changed without recomputing it)."""
    if repo is None:
        repo = Repository.load(audit.REPO_ROOT)
    if rows is None:
        rows = audit.audit_corpus()["rows"]
    materialized = mm.materialize_corpus(repo, rows)
    parsed = {
        record_id: ErratumV2.load(raw, repo.errata[record_id].path)
        for record_id, raw in materialized["targets"].items()
    }
    shadow_repo = mm.build_shadow_repository(repo, parsed)
    return repo, shadow_repo, materialized


def compare_format_outputs(baseline_repo, shadow_repo) -> dict[str, Any]:
    """`build_lflist()` on BOTH repositories, for EVERY current format
    (task section 8's own words) whose banlist/pool are both resolvable -
    text/entries/hash, reported per format. A format this repository does
    not yet fully implement (banlist or pool still missing) is skipped
    identically to how `parity_only_consumption()`
    (`migration_audit.py`) already treats that case - not a shadow-
    migration concern."""
    results: dict[str, dict] = {}
    for fmt_id in sorted(baseline_repo.formats):
        fmt_baseline = baseline_repo.formats[fmt_id]
        if not (fmt_baseline.banlist_id in baseline_repo.banlists and fmt_baseline.pool_id in baseline_repo.pools):
            continue
        fmt_shadow = shadow_repo.formats[fmt_id]
        baseline_built = build_lflist(fmt_baseline, baseline_repo)
        shadow_built = build_lflist(fmt_shadow, shadow_repo)
        results[fmt_id] = {
            "baseline_hash": baseline_built.hash,
            "shadow_hash": shadow_built.hash,
            "hash_identical": baseline_built.hash == shadow_built.hash,
            "text_identical": baseline_built.text == shadow_built.text,
            "entries_identical": baseline_built.entries == shadow_built.entries,
            "codes_lost": sorted(set(baseline_built.entries) - set(shadow_built.entries)),
            "codes_gained": sorted(set(shadow_built.entries) - set(baseline_built.entries)),
        }
    return results


def compare_validation(baseline_repo, shadow_repo) -> dict[str, Any]:
    """Validator on BOTH repositories - required: zero new ERRORs on the
    shadow; the WARNING code/count delta is reported explicitly rather
    than silently accepted, so a genuine behavioural regression cannot
    hide inside "some warnings changed, that's expected for a format
    migration" hand-waving. A delta caused solely by v1/v2 diagnostic
    WORDING (same code, different message text) is distinguished from a
    delta in which CODES themselves appeared or disappeared - only the
    latter is inherently suspicious."""
    from collections import Counter

    baseline_validator = Validator(baseline_repo)
    baseline_validator.validate()
    shadow_validator = Validator(shadow_repo)
    shadow_validator.validate()

    baseline_error_codes = Counter(f.code for f in baseline_validator.errors)
    shadow_error_codes = Counter(f.code for f in shadow_validator.errors)
    new_error_codes = {
        code: shadow_error_codes[code] - baseline_error_codes.get(code, 0)
        for code in shadow_error_codes
        if shadow_error_codes[code] > baseline_error_codes.get(code, 0)
    }

    baseline_warning_codes = Counter(f.code for f in baseline_validator.warnings)
    shadow_warning_codes = Counter(f.code for f in shadow_validator.warnings)
    all_warning_codes = sorted(set(baseline_warning_codes) | set(shadow_warning_codes))
    warning_delta = {
        code: {"baseline": baseline_warning_codes.get(code, 0), "shadow": shadow_warning_codes.get(code, 0)}
        for code in all_warning_codes
        if baseline_warning_codes.get(code, 0) != shadow_warning_codes.get(code, 0)
    }

    return {
        "baseline_error_count": len(baseline_validator.errors),
        "shadow_error_count": len(shadow_validator.errors),
        "new_error_codes": new_error_codes,
        "baseline_warning_count": len(baseline_validator.warnings),
        "shadow_warning_count": len(shadow_validator.warnings),
        "warning_code_delta": warning_delta,
    }


def run_shadow_migration(repo=None, rows: list[dict] | None = None) -> dict[str, Any]:
    """The full section 8 gate in one call: build baseline/shadow, compare
    every format's `build_lflist()` output, compare `Validator` findings.
    Returns a report dict; makes no assertions itself (the caller/tests
    decide what counts as passing)."""
    baseline_repo, shadow_repo, materialized = build_shadow_and_baseline(repo, rows)
    return {
        "shadow_record_count": len(materialized["targets"]),
        "sugar_count": len(materialized["sugar_ids"]),
        "full_count": len(materialized["full_ids"]),
        "unchanged_v1_count": len(materialized["excluded_ids"]),
        "formats": compare_format_outputs(baseline_repo, shadow_repo),
        "validation": compare_validation(baseline_repo, shadow_repo),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(run_shadow_migration(), indent=2, default=str))
