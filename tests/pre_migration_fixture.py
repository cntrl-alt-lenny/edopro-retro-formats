"""The frozen PRE-MIGRATION v1 corpus (canonical migration commit
1937239d9fd0ebfb47dc850f298c11c3a60679b0's approved HEAD, immediately
before the real 247-record migration) - preserved as historical evidence,
task section 5/7 of the final migration gate.

WHY this exists: `tests/migration_audit.py`'s comparator, `tests/
migration_materializer.py`'s materializer, and their test suites were
built and exhaustively verified against the full 296-record all-v1
corpus - hundreds of tests exercise real, specific edge cases (ordering
proofs, cardinality-collapse detection, self-contradiction detection,
reference-identity precedence, top-level preservation) using actual
named canonical records. After the migration, `data/errata/` naturally
contains only the 49 records that were NOT migrated (still v1) - running
`audit_corpus()` against the LIVE repository now correctly reports 49
records, not 296, because it was always designed to audit "whatever v1
records currently exist" (skipping ErratumV2 records entirely - "already
v2; nothing to migrate"). That is the RIGHT behaviour for the live
repository, but it means the rich 296-record regression surface that
proved the migration was safe would otherwise silently vanish from test
coverage the moment migration landed.

This module loads a REPOSITORY-SHAPED object whose `errata` table is the
frozen pre-migration snapshot (`tests/fixtures/pre_migration_errata_1937239/`,
extracted via `git archive 1937239 -- data/errata` and verified byte-for-
byte identical to the pre-migration on-disk files by sha256 before this
module was written) while every OTHER field - banlists, pools, rule
profiles, formats, sources, card index, products, release coverage/gaps -
is reused from the LIVE repository, because none of those were touched by
the migration (only `data/errata/*.json` changed, and only for 247 of its
296 files).

Tests that need to prove a fact about the FROZEN PRE-MIGRATION EVIDENCE
(e.g. "the pre-migration corpus really did have 247 semantically-
equivalent records") should use `load_pre_migration_repo()` here, never
`Repository.load(REPO_ROOT)` - the latter now returns the POST-MIGRATION
LIVE repository (247 v2 + 49 v1) and must never be silently treated as
if it were still all-v1. Tests that need to prove a fact about the LIVE
repository should keep using `Repository.load(REPO_ROOT)` directly, exactly
as before - this module is not a replacement for that.

This fixture is a permanent, immutable historical snapshot. It is never
regenerated and never updated - it is provenance, not a second source of
ongoing truth.
"""

from __future__ import annotations

from pathlib import Path

from retroformats.model import DataError, load_erratum_record
from retroformats.repo import Repository, _read_json

from . import migration_audit as audit

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "pre_migration_errata_1937239"
FIXTURE_ERRATA_DIR = FIXTURE_ROOT / "data" / "errata"

PRE_MIGRATION_COMMIT = "1937239d9fd0ebfb47dc850f298c11c3a60679b0"


def verify_fixture_matches_commit() -> list[str]:
    """Independent cross-check that `FIXTURE_ROOT` really was extracted
    from `PRE_MIGRATION_COMMIT` - re-extracts `data/errata/` from that
    exact commit via `git archive` (the same tool the fixture was
    originally built with, but run fresh here, not trusted from memory)
    into a temp directory, then compares it byte-for-byte against the
    committed fixture. Returns a list of mismatch descriptions (empty
    means every fixture file matches that commit's real tree exactly).

    Deliberately does NOT compare against the fixture by re-deriving the
    fixture's own hash and checking it against itself - that would only
    prove the fixture agrees with itself. `git archive` reads the actual
    git object database, independent of anything this module trusts
    about its own fixture directory."""
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        result = subprocess.run(
            ["git", "-C", str(audit.REPO_ROOT), "archive", PRE_MIGRATION_COMMIT, "--", "data/errata"],
            capture_output=True,
        )
        if result.returncode != 0:
            return [
                f"git archive {PRE_MIGRATION_COMMIT} failed (is it a real commit in this repo's "
                f"history?): {result.stderr.decode('utf-8', errors='replace')}"
            ]
        archive_path = tmp_path / "archive.tar"
        archive_path.write_bytes(result.stdout)
        import tarfile

        with tarfile.open(archive_path) as tar:
            # trusted local `git archive` output, not untrusted input - the
            # `filter` kwarg (PEP 706, Python 3.12+) is used when available
            # to avoid the extraction-time DeprecationWarning without
            # requiring it on older supported interpreters.
            try:
                tar.extractall(tmp_path, filter="data")
            except TypeError:
                tar.extractall(tmp_path)

        extracted_dir = tmp_path / "data" / "errata"
        extracted_files = {p.name: p for p in extracted_dir.glob("*.json")}
        fixture_files = {p.name: p for p in FIXTURE_ERRATA_DIR.glob("*.json")}

        problems = []
        if set(extracted_files) != set(fixture_files):
            problems.append(
                f"file set mismatch: commit has {len(extracted_files)}, fixture has "
                f"{len(fixture_files)}, symmetric difference "
                f"{sorted(set(extracted_files) ^ set(fixture_files))[:10]}"
            )
        for name in sorted(set(extracted_files) & set(fixture_files)):
            if extracted_files[name].read_bytes() != fixture_files[name].read_bytes():
                problems.append(f"{name}: fixture content does not match {PRE_MIGRATION_COMMIT}'s real tree")
        return problems


def load_pre_migration_repo() -> Repository:
    """The frozen 296-record all-v1 repository, as it existed at
    `PRE_MIGRATION_COMMIT` - errata from the frozen fixture, everything
    else reused from the live on-disk repository (banlists/pools/rule_
    profiles/formats/sources/card_index/products/release_coverage/
    release_gaps/import_report - none of these were touched by the
    migration, so the live copies are byte-identical to what they were
    pre-migration)."""
    live = Repository.load(audit.REPO_ROOT)

    errata: dict = {}
    load_errors: list = []
    for path in sorted(FIXTURE_ERRATA_DIR.glob("*.json")):
        try:
            raw = _read_json(path)
            record = load_erratum_record(raw, path)
        except DataError as exc:
            load_errors.append(exc)
            continue
        if record.id in errata:
            load_errors.append(DataError(path, f"duplicate id {record.id!r}"))
            continue
        errata[record.id] = record

    # Fail loudly here, not silently: a malformed fixture file would
    # otherwise land in load_errors and every caller would need to
    # remember to check it (only one of ~30 call sites across the test
    # suite ever did, for the LIVE repo - none did for this one). This
    # fixture is a frozen, verified-once snapshot; any load error here
    # is unconditionally a bug in the fixture itself, never something a
    # caller should have to tolerate.
    if load_errors:
        raise AssertionError(f"pre-migration fixture failed to load cleanly: {load_errors}")
    if len(errata) != 296:
        raise AssertionError(f"pre-migration fixture must have exactly 296 records, got {len(errata)}")

    return Repository(
        root=live.root,
        banlists=live.banlists,
        pools=live.pools,
        rule_profiles=live.rule_profiles,
        errata=errata,
        formats=live.formats,
        global_sources=live.global_sources,
        format_sources=live.format_sources,
        card_index=live.card_index,
        products=live.products,
        release_coverage=live.release_coverage,
        release_gaps=live.release_gaps,
        import_report=live.import_report,
        load_errors=load_errors,
    )
