"""Tests for the decisive final pre-migration gate (task section 8):
shadow-migrating all 247 semantically-equivalent records in memory and
comparing every real consumer's output against the untouched baseline.
"""

from __future__ import annotations

import unittest

from retroformats.repo import Repository

from . import migration_audit as audit
from . import migration_materializer as mm
from . import shadow_migration as sm

IGNIS_GOAT_MAP_HASH = 0x28E9FC02


class ShadowMigrationTest(unittest.TestCase):
    """Computed once per class - a full shadow-migration pass (materialize
    247 targets, build two repositories, run build_lflist() + Validator on
    both) is the most expensive check in this task, and every test below
    reads the SAME immutable result."""

    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(audit.REPO_ROOT)
        cls.audit_result = audit.audit_corpus()
        cls.rows = cls.audit_result["rows"]
        cls.report = sm.run_shadow_migration(cls.repo, cls.rows)

    def test_shadow_record_counts(self):
        self.assertEqual(247, self.report["shadow_record_count"])
        self.assertEqual(180, self.report["sugar_count"])
        self.assertEqual(67, self.report["full_count"])
        self.assertEqual(49, self.report["unchanged_v1_count"])

    def test_goat_is_byte_identical_and_matches_the_pinned_hash(self):
        goat = self.report["formats"]["2005-04-goat"]
        self.assertTrue(goat["hash_identical"])
        self.assertTrue(goat["text_identical"])
        self.assertTrue(goat["entries_identical"])
        self.assertEqual([], goat["codes_lost"])
        self.assertEqual([], goat["codes_gained"])
        self.assertEqual(IGNIS_GOAT_MAP_HASH, goat["baseline_hash"])
        self.assertEqual(IGNIS_GOAT_MAP_HASH, goat["shadow_hash"])

    def test_edison_is_byte_identical(self):
        edison = self.report["formats"]["2010-03-edison"]
        self.assertTrue(edison["hash_identical"])
        self.assertTrue(edison["text_identical"])
        self.assertTrue(edison["entries_identical"])
        self.assertEqual([], edison["codes_lost"])
        self.assertEqual([], edison["codes_gained"])
        self.assertEqual(edison["baseline_hash"], edison["shadow_hash"])

    def test_every_current_format_was_compared(self):
        """No silent skip: exactly the formats/ directory's contents."""
        self.assertEqual({"2005-04-goat", "2010-03-edison"}, set(self.report["formats"]))

    def test_zero_new_validation_errors(self):
        validation = self.report["validation"]
        self.assertEqual(0, validation["baseline_error_count"])
        self.assertEqual(0, validation["shadow_error_count"])
        self.assertEqual({}, validation["new_error_codes"])

    def test_warning_delta_is_exactly_one_explained_case(self):
        """The full corrected picture (final-gate corrections 1 and the
        earlier shadow-migration pass): TWO codes used to inflate this
        delta beyond the one legitimate case -
        `format.parity-omits-historical` (+43, a real validator bug found
        and fixed - see ParityOmitsHistoricalFalsePositiveTest in
        test_erratum_v2_representation.py) and `erratum.functional-none-
        needed` (4 -> 0, ported to `_validate_erratum_v2()` in
        FunctionalNoneNeededV2Test in test_erratum_v2_consumers.py,
        preserving the SAME v1 invariant across the representation
        boundary rather than losing it). With both fixed, exactly ONE
        code remains, and it is a legitimate representation change, not
        lost coverage: `erratum.no-behavioural-change-with-override`
        (11 -> 0) fires in v1 for a zero-relevant-event record whose
        strategy is reuse-upstream/custom-script - EXACTLY the 11
        parity-only-identity records (verified: the corpus locations
        match 1:1, see the next test). v2 represents this fact properly
        via `reference_identities[]` instead of flagging it as a
        computed-selection oddity; the warning is superseded by the
        representation this task built, not silently dropped."""
        delta = self.report["validation"]["warning_code_delta"]
        self.assertEqual(
            {"erratum.no-behavioural-change-with-override": {"baseline": 11, "shadow": 0}},
            delta,
        )
        self.assertNotIn("format.parity-omits-historical", delta)
        self.assertNotIn("erratum.functional-none-needed", delta)

    def test_the_11_vanished_override_warnings_are_exactly_the_parity_only_records(self):
        parity_only_ids = {r["id"] for r in self.rows if r["equivalent"] and r["category"] == audit.CAT_PARITY_ONLY}
        self.assertEqual(11, len(parity_only_ids))

        from retroformats.validate import Validator

        baseline_validator = Validator(self.repo)
        baseline_validator.validate()
        # This warning is emitted at the ERRATUM's own path (unlike the
        # parity warnings above, which use the format's path), so the
        # location string identifies which record triggered it directly.
        # Maps EVERY record, not just the 11 parity-only ones, so an
        # unexpected extra location would show up as a real mismatch
        # rather than being silently filtered away.
        path_to_id = {
            mm.finding_location(self.repo, record.path): record.id for record in self.repo.errata.values()
        }
        warned_ids = {
            path_to_id[f.location]
            for f in baseline_validator.warnings
            if f.code == "erratum.no-behavioural-change-with-override"
        }
        self.assertEqual(parity_only_ids, warned_ids)


if __name__ == "__main__":
    unittest.main()
