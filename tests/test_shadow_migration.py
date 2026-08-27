"""Tests for the decisive final pre-migration gate (task section 8):
shadow-migrating semantically-equivalent records in memory and comparing
every real consumer's output against an untouched baseline.

**POST-MIGRATION SPLIT (task section 7)**: the real 247-record canonical
migration has happened (commit immediately after
1937239d9fd0ebfb47dc850f298c11c3a60679b0). Two DIFFERENT questions, two
DIFFERENT test classes, never conflated:

- `ShadowMigrationReproducibilityTest` - shadow-migrates the FROZEN
  pre-migration snapshot (`tests.pre_migration_fixture.
  load_pre_migration_repo()`) and compares it against ITSELF as baseline.
  This is now a REPRODUCIBILITY proof, not a live pre-migration gate: it
  confirms that running the materializer today, against the exact
  pre-migration input, still produces the exact migration that was
  actually performed - not merely that it once did.
- `PostMigrationLiveRepositoryTest` - pins the CURRENT, LIVE, on-disk
  repository's guarantees DIRECTLY (`Repository.load(audit.REPO_ROOT)`,
  no shadow/baseline comparison at all, because there is nothing left to
  compare against: the shadow IS the real repository now). Exactly 294
  `ErratumV2` + 2 `Erratum`, exactly 180 sugar-shaped + 114 full-v2
  canonical files, all schema-valid, the live repository validates
  cleanly, and GOAT/Edison output is pinned to the same values the
  pre-migration baseline had.

Never fabricate a live all-v1 "current corpus" - that is precisely the
mistake this split exists to avoid.
"""

from __future__ import annotations

import unittest

from retroformats.lflist import build_lflist
from retroformats.model import Erratum, ErratumV2
from retroformats.repo import Repository
from retroformats.validate import Validator

from . import migration_audit as audit
from . import migration_materializer as mm
from . import shadow_migration as sm
from .pre_migration_fixture import load_pre_migration_repo
from .schema_check import Registry, validate_erratum

IGNIS_GOAT_MAP_HASH = 0x28E9FC02


class ShadowMigrationReproducibilityTest(unittest.TestCase):
    """Computed once per class - a full shadow-migration pass (materialize
    the frozen snapshot's 247 targets, build two repositories, run
    build_lflist() + Validator on both) is expensive, and every test below
    reads the SAME immutable result.

    Baseline and shadow are both derived from the SAME frozen pre-
    migration snapshot here (never the live repository - see the module
    docstring), so this class proves REPRODUCIBILITY: today's materializer
    output, compared against the pre-migration baseline it was originally
    verified against, is unchanged."""

    @classmethod
    def setUpClass(cls):
        cls.repo = load_pre_migration_repo()
        cls.audit_result = audit.audit_corpus(cls.repo)
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


class CanonicalShapeTest(unittest.TestCase):
    """Task section 10: direct tests over the RAW `data/errata/*.json`
    files (not the parsed objects - the shape discriminator is a fact
    about the JSON text itself) proving the migration's topology and the
    v1/v2 representation boundary, without re-implementing the schema."""

    @classmethod
    def setUpClass(cls):
        import json

        cls.raw_by_id: dict[str, dict] = {}
        for path in sorted((audit.REPO_ROOT / "data" / "errata").glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            cls.raw_by_id[doc["id"]] = doc
        cls.pre_migration_rows = audit.audit_corpus(load_pre_migration_repo())["rows"]
        cls.by_id = {r["id"]: r for r in cls.pre_migration_rows}
        cls.frozen_49 = {r["id"] for r in cls.pre_migration_rows if not r["equivalent"]}
        cls.frozen_247 = {r["id"] for r in cls.pre_migration_rows if r["equivalent"]}
        cls.unordered_47 = {
            r["id"]
            for r in cls.pre_migration_rows
            if all(r.get(key) == value for key, value in {
                "equivalent": False,
                "research_status": "already-researched",
                "migration_complexity": "unordered-researched",
            }.items())
        }
        cls.manual_2 = {"erratum-insect-imitation", "erratum-last-will"}
        cls.parity_only_ids = {
            r["id"] for r in cls.pre_migration_rows if r["equivalent"] and r["category"] == audit.CAT_PARITY_ONLY
        }

    def test_every_record_has_exactly_one_discriminator(self):
        for rid, doc in self.raw_by_id.items():
            discriminators = [k for k in ("changes", "events", "event") if k in doc]
            self.assertEqual(1, len(discriminators), f"{rid}: discriminators {discriminators}")

    def test_discriminator_counts(self):
        by_discriminator = {"changes": 0, "events": 0, "event": 0}
        for doc in self.raw_by_id.values():
            for key in by_discriminator:
                if key in doc:
                    by_discriminator[key] += 1
        self.assertEqual({"changes": 2, "events": 114, "event": 180}, by_discriminator)

    def test_no_migrated_record_retains_legacy_fields(self):
        for rid in self.frozen_247 | self.unordered_47:
            doc = self.raw_by_id[rid]
            self.assertNotIn("changes", doc, rid)
            self.assertNotIn("implementation", doc, rid)

    def test_no_remaining_v1_record_gains_v2_fields(self):
        for rid in self.manual_2:
            doc = self.raw_by_id[rid]
            for key in ("events", "event", "states", "implementation_metadata", "reference_identities"):
                self.assertNotIn(key, doc, f"{rid}: unexpectedly carries v2 key {key!r}")

    def test_every_v1_and_v2_id_is_accounted_for(self):
        self.assertEqual(set(self.raw_by_id), self.frozen_247 | self.unordered_47 | self.manual_2)
        self.assertEqual(set(), (self.frozen_247 | self.unordered_47) & self.manual_2)

    def test_all_11_parity_only_records_carry_their_reference_identity(self):
        self.assertEqual(11, len(self.parity_only_ids))
        for rid in self.parity_only_ids:
            doc = self.raw_by_id[rid]
            identities = doc.get("reference_identities") or []
            self.assertEqual(1, len(identities), rid)
            entry = identities[0]
            for field in ("reference_id", "provenance_source", "historical_passcode", "upstream"):
                self.assertIn(field, entry, f"{rid}: reference_identities[0] missing {field!r}")

    def test_implementation_metadata_is_preserved_where_authored(self):
        """Every one of the 247 migrated records had SOME authored
        baseline metadata pre-migration (verified against the frozen
        snapshot: baseline_metadata_represented_count == 296, none
        unrepresented) - the migrated file must still carry a non-empty
        implementation_metadata[] with a baseline ([]) entry."""
        missing = []
        for rid in self.frozen_247 | self.unordered_47:
            doc = self.raw_by_id[rid]
            metadata = doc.get("implementation_metadata") or []
            baseline_entries = [e for e in metadata if not e.get("events")]
            if not baseline_entries:
                missing.append(rid)
        self.assertEqual([], missing)


class PostMigrationLiveRepositoryTest(unittest.TestCase):
    """Task section 7: the LIVE, current, on-disk repository's guarantees,
    pinned DIRECTLY - no shadow/baseline comparison, because the shadow
    IS the real repository now. Computed once per class; the live
    repository is loaded fresh (never the frozen pre-migration fixture)."""

    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(audit.REPO_ROOT)
        assert not cls.repo.load_errors, cls.repo.load_errors
        cls.v2_records = {rid: r for rid, r in cls.repo.errata.items() if isinstance(r, ErratumV2)}
        cls.v1_records = {rid: r for rid, r in cls.repo.errata.items() if isinstance(r, Erratum)}
        cls.sugar_records = {
            rid: r for rid, r in cls.v2_records.items() if r.authored_shape == "sugar"
        }
        cls.full_records = {rid: r for rid, r in cls.v2_records.items() if r.authored_shape == "full"}
        cls.validator = Validator(cls.repo)
        cls.validator.validate()

    def test_exactly_294_v2_and_2_v1(self):
        self.assertEqual(296, len(self.repo.errata))
        self.assertEqual(294, len(self.v2_records))
        self.assertEqual(2, len(self.v1_records))

    def test_exactly_180_sugar_and_114_full(self):
        self.assertEqual(180, len(self.sugar_records))
        self.assertEqual(114, len(self.full_records))
        self.assertEqual(len(self.v2_records), len(self.sugar_records) + len(self.full_records))

    def test_the_two_remaining_v1_ids_are_the_manual_records(self):
        self.assertEqual({"erratum-insect-imitation", "erratum-last-will"}, set(self.v1_records))

    def test_all_294_v2_records_are_schema_valid(self):
        """Re-validates the ACTUAL on-disk JSON (raw file content), not
        the parsed object - the same schema checker
        test_erratum_schema.py uses."""
        import json

        registry = Registry()
        failures = {}
        for rid, record in self.v2_records.items():
            raw = json.loads(record.path.read_text(encoding="utf-8"))
            errors = validate_erratum(raw, registry)
            if errors:
                failures[rid] = errors
        self.assertEqual({}, failures)

    def test_live_repository_validates_with_zero_errors(self):
        self.assertEqual([], self.validator.errors)

    def test_goat_output_matches_the_pinned_pre_migration_hash(self):
        fmt = self.repo.formats["2005-04-goat"]
        built = build_lflist(fmt, self.repo)
        self.assertEqual(IGNIS_GOAT_MAP_HASH, built.hash)

    def test_edison_output_matches_the_pre_migration_hash(self):
        """Edison has no external reference hash to pin against (unlike
        GOAT's IGNIS_GOAT_MAP_HASH) - pinned instead against the frozen
        pre-migration snapshot's own build_lflist() output, computed
        fresh here rather than hard-coded, so a real behavioural change
        in either the runtime or the data would be caught, not silently
        re-pinned."""
        pre_repo = load_pre_migration_repo()
        pre_fmt = pre_repo.formats["2010-03-edison"]
        pre_built = build_lflist(pre_fmt, pre_repo)

        fmt = self.repo.formats["2010-03-edison"]
        built = build_lflist(fmt, self.repo)

        self.assertEqual(pre_built.hash, built.hash)
        self.assertEqual(pre_built.text, built.text)
        self.assertEqual(pre_built.entries, built.entries)

    def test_dist_is_byte_identical_to_a_fresh_build(self):
        """build --check's own guarantee, re-verified directly: rebuilding
        from the live repository must reproduce dist/ byte-for-byte."""
        for fmt_id in ("2005-04-goat", "2010-03-edison"):
            fmt = self.repo.formats[fmt_id]
            built = build_lflist(fmt, self.repo)
            on_disk = (audit.REPO_ROOT / "dist" / "lflists" / f"{fmt_id}.lflist.conf").read_text(
                encoding="utf-8"
            )
            self.assertEqual(built.text, on_disk, fmt_id)

    def test_fixture_matches_the_real_pre_migration_commit(self):
        """Independent of the fixture's own content: re-extracts `data/
        errata/` fresh from `PRE_MIGRATION_COMMIT` via `git archive`
        (reading the actual git object database, not trusting anything
        this module remembers about its own fixture directory) and
        compares byte-for-byte. A test that only compared
        `PRE_MIGRATION_COMMIT` against a hardcoded copy of the same
        literal would be tautological - this instead proves the frozen
        fixture really is what that commit hash says it is."""
        from .pre_migration_fixture import verify_fixture_matches_commit

        problems = verify_fixture_matches_commit()
        self.assertEqual([], problems)


if __name__ == "__main__":
    unittest.main()
