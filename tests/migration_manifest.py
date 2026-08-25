"""Generates `docs/research/erratum-v2-migration-manifest.json` (final
migration gate, task section 6) - provenance for WHICH files the real
247-record canonical migration changed, derived from the ACTUAL live
repository state, never a hand-maintained id list.

This is NOT a second source of historical truth: the frozen pre-migration
evidence lives in `tests.pre_migration_fixture`/`docs/research/erratum-v2-
migration-audit-pre-migration.json`, and this manifest only records WHICH
of those records became which shape, plus a content hash of each
migrated file for tamper/drift detection.
"""

from __future__ import annotations

import hashlib
from typing import Any

from retroformats.model import Erratum, ErratumV2

from . import migration_audit as audit
from .pre_migration_fixture import PRE_MIGRATION_COMMIT


def generate_manifest(repo=None) -> dict[str, Any]:
    """The manifest dict - derived entirely from `repo` (default: the LIVE
    on-disk repository), never hand-maintained."""
    from retroformats.repo import Repository

    if repo is None:
        repo = Repository.load(audit.REPO_ROOT)

    records = []
    for record_id in sorted(repo.errata):
        record = repo.errata[record_id]
        if not isinstance(record, ErratumV2):
            continue
        shape = "sugar" if record.authored_shape == "sugar" else "full"
        rel_path = str(record.path.relative_to(repo.root)).replace("\\", "/")
        sha256 = hashlib.sha256(record.path.read_bytes()).hexdigest()
        records.append({"id": record_id, "path": rel_path, "shape": shape, "sha256": sha256})

    remaining_v1 = sorted(rid for rid, r in repo.errata.items() if isinstance(r, Erratum))
    sugar_count = sum(1 for r in records if r["shape"] == "sugar")
    full_count = sum(1 for r in records if r["shape"] == "full")

    return {
        "source_commit": PRE_MIGRATION_COMMIT,
        "migrated_count": len(records),
        "sugar_count": sugar_count,
        "full_count": full_count,
        "remaining_v1_count": len(remaining_v1),
        "remaining_v1_ids": remaining_v1,
        "records": records,
    }


def verify_manifest_against_disk(manifest: dict[str, Any], repo=None) -> list[str]:
    """Every hash in `manifest["records"]` re-checked against the actual
    current file bytes. Returns a list of mismatch descriptions (empty
    means every file matches its recorded hash)."""
    from retroformats.repo import Repository

    if repo is None:
        repo = Repository.load(audit.REPO_ROOT)
    problems = []
    for entry in manifest["records"]:
        path = repo.root / entry["path"]
        if not path.exists():
            problems.append(f"{entry['id']}: {entry['path']} does not exist")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            problems.append(f"{entry['id']}: sha256 mismatch (manifest {entry['sha256']}, actual {actual})")
    return problems


if __name__ == "__main__":  # pragma: no cover
    import json

    manifest = generate_manifest()
    out = audit.REPO_ROOT / "docs" / "research" / "erratum-v2-migration-manifest.json"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"migrated_count={manifest['migrated_count']} sugar_count={manifest['sugar_count']} "
          f"full_count={manifest['full_count']} remaining_v1_count={manifest['remaining_v1_count']}")
    print(f"wrote {out}")
