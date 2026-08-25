"""Tests for the migration manifest (final migration gate, task section
6): provenance for exactly which files the real canonical migration
changed, derived from the live repository, never hand-maintained.
"""

from __future__ import annotations

import unittest

from retroformats.model import Erratum, ErratumV2
from retroformats.repo import Repository

from . import migration_audit as audit
from . import migration_manifest as mfst
from .pre_migration_fixture import PRE_MIGRATION_COMMIT, load_pre_migration_repo


class MigrationManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(audit.REPO_ROOT)
        cls.manifest = mfst.generate_manifest(cls.repo)

    def test_counts(self):
        self.assertEqual(247, self.manifest["migrated_count"])
        self.assertEqual(180, self.manifest["sugar_count"])
        self.assertEqual(67, self.manifest["full_count"])
        self.assertEqual(49, self.manifest["remaining_v1_count"])
        self.assertEqual(247, len(self.manifest["records"]))

    def test_source_commit_is_the_documented_pre_migration_commit(self):
        self.assertEqual(PRE_MIGRATION_COMMIT, self.manifest["source_commit"])

    def test_manifest_ids_equal_current_v2_ids(self):
        manifest_ids = {r["id"] for r in self.manifest["records"]}
        live_v2_ids = {rid for rid, r in self.repo.errata.items() if isinstance(r, ErratumV2)}
        self.assertEqual(live_v2_ids, manifest_ids)

    def test_manifest_ids_equal_the_frozen_247_migrated_ids(self):
        pre_migration_rows = audit.audit_corpus(load_pre_migration_repo())["rows"]
        frozen_247 = {r["id"] for r in pre_migration_rows if r["equivalent"]}
        manifest_ids = {r["id"] for r in self.manifest["records"]}
        self.assertEqual(frozen_247, manifest_ids)

    def test_remaining_v1_ids_equal_the_frozen_49(self):
        pre_migration_rows = audit.audit_corpus(load_pre_migration_repo())["rows"]
        frozen_49 = sorted(r["id"] for r in pre_migration_rows if not r["equivalent"])
        self.assertEqual(frozen_49, self.manifest["remaining_v1_ids"])
        live_v1_ids = sorted(rid for rid, r in self.repo.errata.items() if isinstance(r, Erratum))
        self.assertEqual(frozen_49, live_v1_ids)

    def test_no_overlap_between_migrated_and_remaining(self):
        manifest_ids = {r["id"] for r in self.manifest["records"]}
        remaining_ids = set(self.manifest["remaining_v1_ids"])
        self.assertEqual(set(), manifest_ids & remaining_ids)

    def test_union_is_all_296_canonical_errata(self):
        manifest_ids = {r["id"] for r in self.manifest["records"]}
        remaining_ids = set(self.manifest["remaining_v1_ids"])
        self.assertEqual(296, len(manifest_ids | remaining_ids))
        self.assertEqual(set(self.repo.errata), manifest_ids | remaining_ids)

    def test_shape_field_matches_the_raw_on_disk_discriminator(self):
        """Independent of `generate_manifest()`'s own `record.authored_
        shape` read (checking the manifest against THAT would only prove
        the manifest agrees with itself, via the same in-memory object,
        never with reality) - re-parses the RAW JSON TEXT directly and
        checks its actual top-level `event`/`events` key, exactly like
        `CanonicalShapeTest` in test_shadow_migration.py does."""
        import json

        for entry in self.manifest["records"]:
            path = audit.REPO_ROOT / entry["path"]
            raw = json.loads(path.read_text(encoding="utf-8"))
            has_event = "event" in raw
            has_events = "events" in raw
            self.assertEqual(1, has_event + has_events, f"{entry['id']}: expected exactly one discriminator")
            expected_shape = "sugar" if has_event else "full"
            self.assertEqual(expected_shape, entry["shape"], entry["id"])

    def test_every_record_hash_matches_the_actual_file(self):
        problems = mfst.verify_manifest_against_disk(self.manifest, self.repo)
        self.assertEqual([], problems)

    def test_a_tampered_hash_is_detected(self):
        """The verifier must have real teeth."""
        tampered = dict(self.manifest)
        tampered["records"] = [dict(r) for r in self.manifest["records"]]
        tampered["records"][0]["sha256"] = "0" * 64
        problems = mfst.verify_manifest_against_disk(tampered, self.repo)
        self.assertEqual(1, len(problems))
        self.assertIn(tampered["records"][0]["id"], problems[0])


if __name__ == "__main__":
    unittest.main()
