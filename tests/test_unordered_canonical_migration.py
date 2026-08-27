"""Live proof for the canonical migration of the researched unordered 47.

The v1 side of the semantic proof is reconstructed from the frozen
pre-migration evidence.  The live repository is never compared to itself as
if that could establish an intentional semantic delta.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from collections import Counter
from pathlib import Path

from retroformats.importers.card_index import collect_referenced_passcodes
from retroformats.lflist import build_lflist
from retroformats.model import Erratum, ErratumV2
from retroformats.repo import Repository
from retroformats.validate import Validator

from . import migration_audit as audit
from . import unordered_migration_materializer as gate
from .pre_migration_fixture import load_pre_migration_repo
from .schema_check import Registry, validate_erratum


SOURCE_COMMIT = "b0b8b7d8cc129e827fd684b3d880f6fcaedb80d9"
HISTORICAL_POST_COMMIT = "dec24733359358d993ab275ad4ec3ea7ef95044e"
HISTORICAL_MANUAL_IDS = {"erratum-insect-imitation", "erratum-last-will"}
CURRENT_REMAINING_V1_IDS = set()


def _pre_migration_rows():
    return audit.audit_corpus(load_pre_migration_repo())["rows"]


def _target_rows(rows):
    return [
        row
        for row in rows
        if all(row.get(key) == value for key, value in gate.TARGET_SELECTOR.items())
    ]


def _pre_migration_gate_repo(live, frozen, rows):
    """Recreate the approved 247-v2/49-v1 gate input without disk writes."""
    frozen_v1_ids = {row["id"] for row in rows if not row["equivalent"]}
    return Repository(
        root=live.root,
        banlists=live.banlists,
        pools=live.pools,
        rule_profiles=live.rule_profiles,
        errata={
            **{rid: record for rid, record in live.errata.items() if isinstance(record, ErratumV2)},
            **{rid: frozen.errata[rid] for rid in frozen_v1_ids},
        },
        formats=live.formats,
        global_sources=live.global_sources,
        format_sources=live.format_sources,
        card_index=live.card_index,
        products=live.products,
        release_coverage=live.release_coverage,
        release_gaps=live.release_gaps,
        import_report=live.import_report,
        load_errors=[],
    )


class UnorderedCanonicalMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.live = Repository.load(cls.root)
        cls.frozen = load_pre_migration_repo()
        cls.rows = _pre_migration_rows()
        cls.targets = _target_rows(cls.rows)
        cls.target_ids = {row["id"] for row in cls.targets}
        cls.pre_gate_repo = _pre_migration_gate_repo(cls.live, cls.frozen, cls.rows)
        cls.gate_result = gate.run_gate(cls.pre_gate_repo)
        cls.manifest = json.loads(
            (cls.root / "docs/research/erratum-v2-unordered-migration-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        cls.raw = {
            json.loads(path.read_text(encoding="utf-8"))["id"]: json.loads(
                path.read_text(encoding="utf-8")
            )
            for path in sorted((cls.root / "data/errata").glob("*.json"))
        }

    def test_canonical_corpus_and_exact_remaining_v1(self):
        v2 = {rid for rid, record in self.live.errata.items() if isinstance(record, ErratumV2)}
        v1 = {rid for rid, record in self.live.errata.items() if isinstance(record, Erratum)}
        self.assertEqual(296, len(v2))
        self.assertEqual(CURRENT_REMAINING_V1_IDS, v1)

    def test_exact_discriminator_counts(self):
        counts = Counter(
            key for raw in self.raw.values() for key in ("changes", "events", "event") if key in raw
        )
        self.assertEqual(0, counts.get("changes", 0))
        self.assertEqual(116, counts["events"])
        self.assertEqual(180, counts["event"])
        for raw in self.raw.values():
            self.assertEqual(1, sum(key in raw for key in ("changes", "events", "event")))

    def test_selector_is_exactly_the_approved_47_and_excludes_manual_two(self):
        self.assertEqual(47, len(self.targets))
        self.assertEqual(self.target_ids, set(self.gate_result["parsed"]))
        self.assertTrue(self.target_ids.isdisjoint(HISTORICAL_MANUAL_IDS))
        self.assertEqual(HISTORICAL_MANUAL_IDS, {
            row["id"] for row in self.rows if not row["equivalent"]
        } - self.target_ids)
        self.assertEqual(46, sum(row["legacy_self_contradictory"] is True for row in self.targets))
        self.assertEqual(
            ["erratum-yz-tank-dragon"],
            [row["id"] for row in self.targets if not row["legacy_self_contradictory"]],
        )

    def test_every_target_is_exact_approved_full_v2_payload(self):
        for row in self.targets:
            rid = row["id"]
            expected = gate.materialize(self.frozen.errata[rid], self.frozen)
            actual = self.raw[rid]
            # The migration payload remains authoritative for every semantic
            # field.  This cleanup intentionally permits only the separately
            # audited explanatory review.notes prose to be clarified after
            # migration; no event/chronology/runtime data may differ.
            expected_review = dict(expected.get("review", {}))
            actual_review = dict(actual.get("review", {}))
            expected_review.pop("notes", None)
            actual_review.pop("notes", None)
            expected["review"] = expected_review
            actual_semantic = dict(actual)
            actual_semantic["review"] = actual_review
            self.assertEqual(expected, actual_semantic, rid)
            self.assertIn("events", actual)
            self.assertNotIn("event", actual)
            self.assertNotIn("changes", actual)
            self.assertEqual(len(self.frozen.errata[rid].changes), len(actual["events"]), rid)

    def test_manifest_matches_actual_files_and_source_hashes(self):
        self.assertEqual(SOURCE_COMMIT, self.manifest["source_commit"])
        self.assertEqual(47, self.manifest["target_count"])
        self.assertEqual(0, self.manifest["sugar_count"])
        self.assertEqual(47, self.manifest["full_count"])
        self.assertEqual(self.target_ids, {entry["id"] for entry in self.manifest["records"]})
        for entry in self.manifest["records"]:
            path = self.root / entry["path"]
            self.assertEqual(entry["post_migration_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            source_bytes = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{entry['path']}"])
            self.assertEqual(entry["pre_migration_sha256"], hashlib.sha256(source_bytes).hexdigest())
            self.assertNotEqual(entry["pre_migration_sha256"], entry["post_migration_sha256"])

    def test_exactly_47_errata_paths_changed_from_source_and_manual_bytes_unchanged(self):
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", SOURCE_COMMIT, HISTORICAL_POST_COMMIT, "--", "data/errata"], text=True
        ).splitlines()
        changed_ids = {
            json.loads((self.root / path).read_text(encoding="utf-8"))["id"] for path in changed
        }
        self.assertEqual(self.target_ids, changed_ids)
        for rid in HISTORICAL_MANUAL_IDS:
            path = self.root / "data" / "errata" / f"{rid.removeprefix('erratum-')}.json"
            expected = subprocess.check_output(["git", "show", f"{HISTORICAL_POST_COMMIT}:{path.relative_to(self.root).as_posix()}"])
            source = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{path.relative_to(self.root).as_posix()}"])
            self.assertEqual(source, expected, rid)
            historical_raw = json.loads(expected)
            self.assertIn("changes", historical_raw)
            self.assertNotIn("events", historical_raw)
            self.assertNotIn("event", historical_raw)

    def test_shape_distribution_and_no_cooccurrence_or_invented_ordering(self):
        self.assertEqual({"2": 41, "3": 5, "4": 1}, self.manifest["event_count_distribution"])
        self.assertEqual({"2": 46, "3": 1}, self.manifest["relevant_event_count_distribution"])
        self.assertEqual({"0": 41, "1": 5, "2": 1}, self.manifest["ordering_edge_count_distribution"])
        for rid in self.target_ids:
            raw = self.raw[rid]
            self.assertNotIn("chains", raw["ordering"], rid)
            for event in raw["events"].values():
                self.assertNotIn("cooccurrence_sources", event, rid)
                self.assertEqual(1, len(event["transitions"]), rid)
        self.assertEqual([], self.gate_result["structural"]["failures"])

    def test_gate_failures_semantic_delta_and_yz_fourth_state(self):
        self.assertEqual([], self.gate_result["verification"]["schema_failures"])
        self.assertEqual([], self.gate_result["verification"]["load_failures"])
        self.assertEqual([], self.gate_result["verification"]["preservation_failures"])
        self.assertEqual([], self.gate_result["verification"]["shadow_validation_errors"])
        self.assertEqual(47, self.gate_result["semantic_delta"]["records_with_delta"])
        self.assertEqual(46, len(self.gate_result["semantic_delta"]["self_contradiction_proof"]))
        yz = self.gate_result["parsed"]["erratum-yz-tank-dragon"]
        self.assertEqual(4, len(yz.structural_states()))
        self.assertEqual("unresolved", yz.state_for(frozenset({"c1"})).coverage.kind.value)
        self.assertEqual([], self.gate_result["semantic_delta"]["semantic_failures"])

    def test_manifest_aggregates(self):
        self.assertEqual(46, self.manifest["self_contradictory"])
        self.assertEqual(1, self.manifest["yz_incomplete"])
        self.assertEqual("erratum-yz-tank-dragon", self.manifest["sole_incomplete_id"])
        self.assertEqual({"1": 44, "2": 3}, self.manifest["authored_state_count_distribution"])
        for entry in self.manifest["records"]:
            parsed = self.gate_result["parsed"][entry["id"]]
            self.assertEqual(len(parsed.events), entry["event_count"])
            self.assertEqual(len(parsed.relevant_events()), entry["relevant_event_count"])
            self.assertEqual(len(parsed.raw_edges), entry["ordering_edge_count"])
            self.assertEqual(len(parsed.authored_states), entry["authored_state_count"])

    def test_all_296_v2_records_schema_valid_and_repository_loads(self):
        self.assertEqual([], self.live.load_errors)
        registry = Registry()
        failures = {}
        for rid, record in self.live.errata.items():
            if not isinstance(record, ErratumV2):
                continue
            errors = validate_erratum(self.raw[rid], registry)
            if errors:
                failures[rid] = errors
        self.assertEqual({}, failures)

    def test_union_of_old_new_and_manual_sets_is_all_296(self):
        old = {row["id"] for row in self.rows if row["equivalent"]}
        self.assertEqual(296, len(old | self.target_ids | HISTORICAL_MANUAL_IDS))
        self.assertEqual(set(self.live.errata), old | self.target_ids | HISTORICAL_MANUAL_IDS)
        self.assertEqual(set(), old & self.target_ids)
        self.assertEqual(set(), old & HISTORICAL_MANUAL_IDS)
        self.assertEqual(set(), self.target_ids & HISTORICAL_MANUAL_IDS)

    def test_live_outputs_validator_substitutions_and_card_index_match_pre_gate(self):
        for fmt_id in sorted(self.live.formats):
            fmt = self.live.formats[fmt_id]
            if fmt.banlist_id not in self.live.banlists or fmt.pool_id not in self.live.pools:
                continue
            before = build_lflist(self.pre_gate_repo.formats[fmt_id], self.pre_gate_repo)
            after = build_lflist(fmt, self.live)
            self.assertEqual((before.text, before.entries, before.hash), (after.text, after.entries, after.hash))
            self.assertEqual(
                gate._substitution_map(self.pre_gate_repo.formats[fmt_id], self.pre_gate_repo),
                gate._substitution_map(fmt, self.live),
                fmt_id,
            )
            if fmt_id == "2005-04-goat":
                self.assertEqual(0x28E9FC02, after.hash)
            if fmt_id == "2010-03-edison":
                self.assertEqual(3673, len(self.live.pools[fmt.pool_id].cards))
        before_validator = Validator(self.pre_gate_repo)
        after_validator = Validator(self.live)
        before_validator.validate()
        after_validator.validate()
        self.assertEqual([], before_validator.errors)
        self.assertEqual([], after_validator.errors)
        self.assertEqual(
            Counter({"format.erratum-modern-known-wrong": 2}),
            Counter(f.code for f in after_validator.warnings)
            - Counter(f.code for f in before_validator.warnings),
        )
        self.assertEqual(
            Counter({"format.erratum-unresolved-defaulted": 2}),
            Counter(f.code for f in before_validator.warnings)
            - Counter(f.code for f in after_validator.warnings),
        )
        refs = collect_referenced_passcodes(self.live)
        self.assertEqual([], sorted(refs - set(self.live.card_index.by_passcode)))


if __name__ == "__main__":
    unittest.main()
