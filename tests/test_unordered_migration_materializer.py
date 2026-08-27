"""Regression contract for the 47-record unordered v2 pre-migration gate."""

from __future__ import annotations

import subprocess
import unittest

from retroformats.model import Coverage, Erratum, ErratumV2
from retroformats.repo import Repository

from . import migration_audit as audit
from . import unordered_migration_materializer as gate
from .pre_migration_fixture import load_pre_migration_repo

SOURCE_COMMIT = "e7be46dbd92214140eb10d6d2a7d3e7a16bd9b62"
GATE_COMMIT = "2f1c17864330407a858b9588e8fdb0a2da500ec7"
HISTORICAL_PROTECTED_PATHS = (
    "data/errata",
    "data/banlists",
    "data/pools",
    "data/releases",
    "data/rule-profiles",
    "formats",
    "dist",
    "retroformats",
    "schemas",
)
GATE_FILES = frozenset(
    {
        "docs/research/erratum-v2-unordered-migration-gate.md",
        "tests/test_unordered_migration_materializer.py",
        "tests/unordered_migration_materializer.py",
    }
)

FROZEN_TARGET_IDS = frozenset(
    {
        "erratum-a-deal-with-dark-ruler",
        "erratum-apprentice-magician",
        "erratum-armed-dragon-lv3",
        "erratum-armed-dragon-lv5",
        "erratum-axe-of-despair",
        "erratum-birdface",
        "erratum-bubonic-vermin",
        "erratum-dark-mimic-lv1",
        "erratum-dark-scorpion-meanae-the-thorn",
        "erratum-dedication-through-light-and-darkness",
        "erratum-elegant-egotist",
        "erratum-emblem-of-dragon-destroyer",
        "erratum-freed-the-matchless-general",
        "erratum-fusion-sage",
        "erratum-giant-rat",
        "erratum-great-dezard",
        "erratum-hand-of-nephthys",
        "erratum-hero-signal",
        "erratum-horus-the-black-flame-dragon-lv4",
        "erratum-manju-of-the-ten-thousand-hands",
        "erratum-masked-dragon",
        "erratum-mother-grizzly",
        "erratum-mystic-swordsman-lv2",
        "erratum-mystic-swordsman-lv4",
        "erratum-mystic-tomato",
        "erratum-ninjitsu-art-of-transformation",
        "erratum-paladin-of-white-dragon",
        "erratum-pandemonium",
        "erratum-peten-the-dark-clown",
        "erratum-pyramid-turtle",
        "erratum-sangan",
        "erratum-skull-knight-2",
        "erratum-sonic-bird",
        "erratum-terraforming",
        "erratum-thunder-dragon",
        "erratum-toon-table-of-contents",
        "erratum-tyrant-dragon",
        "erratum-ufo-turtle",
        "erratum-ultimate-insect-lv1",
        "erratum-ultimate-insect-lv3",
        "erratum-ultimate-insect-lv5",
        "erratum-vampire-lord",
        "erratum-witch-of-the-black-forest",
        "erratum-xy-dragon-cannon",
        "erratum-xyz-dragon-cannon",
        "erratum-xz-tank-cannon",
        "erratum-yz-tank-dragon",
    }
)


class UnorderedMigrationGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The gate is historical proof.  Reconstruct its approved input
        # after canonical migration from the live 247 v2 records plus the
        # frozen 49-record v1 evidence; never reinterpret the 294-v2 live
        # repository as a pre-migration corpus.
        live = Repository.load(audit.REPO_ROOT)
        frozen = load_pre_migration_repo()
        frozen_rows = audit.audit_corpus(frozen)["rows"]
        frozen_v1_ids = {row["id"] for row in frozen_rows if not row["equivalent"]}
        cls.repo = Repository(
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
        cls.manual_bytes = {
            record_id: cls.repo.errata[record_id].path.read_bytes()
            for record_id in gate.MANUAL_EXCLUDED_IDS
        }
        cls.result = gate.run_gate(cls.repo)
        cls.scope = gate.audit_scope(cls.repo)
        cls.target_ids = {row["id"] for row in cls.scope["targets"]}
        cls.targets = cls.result["target_payloads"]
        cls.parsed = cls.result["parsed"]
        cls.shadow = cls.result["shadow_repository"]

    def test_source_and_exact_audit_selector(self):
        self.assertEqual(gate.SOURCE_COMMIT, SOURCE_COMMIT)
        self.assertEqual(gate.GATE_COMMIT, GATE_COMMIT)
        self.assertEqual(gate.SOURCE_COMMIT, self.result["source_commit"])
        self.assertEqual(FROZEN_TARGET_IDS, self.target_ids)
        self.assertEqual(47, len(self.target_ids))
        self.assertEqual(
            gate.MANUAL_EXCLUDED_IDS,
            {row["id"] for row in self.scope["remaining_v1"]} - self.target_ids,
        )
        self.assertEqual(gate.MANUAL_EXCLUDED_IDS, set(self.result["manual_excluded"]))

    def test_contradiction_accounting_is_46_plus_yz(self):
        rows = {row["id"]: row for row in self.scope["targets"]}
        self.assertEqual(46, sum(row["legacy_self_contradictory"] is True for row in rows.values()))
        self.assertEqual(["erratum-yz-tank-dragon"], [rid for rid, row in rows.items() if not row["legacy_self_contradictory"]])
        self.assertEqual(
            {"erratum-insect-imitation", "erratum-last-will"},
            {row["id"] for row in self.scope["remaining_v1"] if row["id"] not in self.target_ids},
        )

    def test_every_target_is_full_v2_and_has_one_event_per_change(self):
        self.assertEqual(0, self.result["materialized"]["sugar_count"])
        self.assertEqual(47, self.result["materialized"]["full_count"])
        for record_id, raw in self.targets.items():
            record = self.repo.errata[record_id]
            self.assertIn("events", raw, record_id)
            self.assertNotIn("event", raw, record_id)
            self.assertNotIn("coverage", raw, record_id)
            self.assertEqual(len(record.changes), len(raw["events"]), record_id)
            self.assertTrue(all(len(event["transitions"]) == 1 for event in raw["events"].values()), record_id)
            self.assertTrue(
                all("cooccurrence_sources" not in event for event in raw["events"].values()),
                record_id,
            )

    def test_shape_and_distribution_are_exact(self):
        self.assertEqual({2: 41, 3: 5, 4: 1}, self.result["structural"]["event_count_distribution"])
        self.assertEqual({2: 46, 3: 1}, self.result["structural"]["relevant_event_count_distribution"])
        self.assertEqual({"empty": 41, "edges:1": 5, "edges:2": 1}, self.result["structural"]["ordering_shape_distribution"])
        self.assertEqual({1: 44, 2: 3}, self.result["structural"]["authored_state_count_distribution"])

    def test_ordering_is_only_date_proven_and_never_array_position(self):
        for row in self.scope["targets"]:
            record = self.repo.errata[row["id"]]
            target = self.parsed[row["id"]]
            expected = set()
            for before_index, before in enumerate(record.changes):
                for after_index, after in enumerate(record.changes):
                    if before_index == after_index:
                        continue
                    if audit.ordering_proof(
                        before.get("effective") or {"date": None},
                        after.get("effective") or {"date": None},
                    ) == audit.PROVEN:
                        expected.add((f"c{before_index}", f"c{after_index}"))
            actual = {(edge["before"], edge["after"]) for edge in target.raw_edges}
            self.assertEqual(expected, actual, record.id)
            self.assertTrue(all(edge["basis"] == "date-proven" for edge in target.raw_edges), record.id)

        # Giant Rat is a named self-contradictory example: the two relevant
        # events stay separate and unordered even though v1 listed them in a
        # positionally meaningful sequence.
        self.assertEqual({}, self.targets["erratum-giant-rat"]["ordering"])

    def test_unauthored_reachable_states_are_unresolved_and_terminal_is_modern(self):
        for record_id, target in self.parsed.items():
            relevant = {event.id for event in target.relevant_events()}
            for state in target.structural_states():
                coverage = target.state_for(state).coverage
                if state == relevant:
                    self.assertEqual(Coverage.MODERN, coverage.kind, record_id)
                elif state not in target.authored_states:
                    self.assertEqual(Coverage.UNRESOLVED, coverage.kind, (record_id, sorted(state)))

    def test_independent_data_preservation_gate_is_empty(self):
        verification = self.result["verification"]
        self.assertEqual(47, verification["target_count"])
        self.assertEqual([], verification["schema_failures"])
        self.assertEqual([], verification["load_failures"])
        self.assertEqual([], verification["preservation_failures"])
        self.assertEqual([], verification["shadow_validation_errors"])

    def test_semantic_delta_is_explicit_and_self_contradictions_are_proven(self):
        delta = self.result["semantic_delta"]
        self.assertEqual(47, delta["records_with_delta"])
        self.assertGreater(delta["delta_snapshot_count"], 0)
        self.assertEqual([], delta["semantic_failures"])
        self.assertEqual(46, len(delta["self_contradiction_proof"]))
        self.assertEqual(
            {row["id"] for row in self.scope["targets"] if row["legacy_self_contradictory"]},
            set(delta["self_contradiction_proof"]),
        )

        # Differences may add/remove event-set identities, but common event
        # sets retain the exact v1 coverage signature.
        for snapshots in delta["snapshots"].values():
            for snapshot in snapshots:
                v1 = {tuple(item["events"]): tuple(item["coverage"]) for item in snapshot["v1"]}
                v2 = {tuple(item["events"]): tuple(item["coverage"]) for item in snapshot["v2"]}
                self.assertEqual({key: v1[key] for key in v1.keys() & v2.keys()}, {key: v2[key] for key in v1.keys() & v2.keys()})

    def test_yz_has_three_v1_states_and_four_v2_structural_states(self):
        record = self.repo.errata["erratum-yz-tank-dragon"]
        target = self.parsed[record.id]
        v1_states = {
            frozenset(item["events"])
            for day in audit.boundary_dates(record)
            for item in audit._fmt_states(audit.v1_claimed_states(record, day))
        }
        v2_states = set(target.structural_states())
        self.assertEqual(3, len(v1_states))
        self.assertEqual({frozenset(), frozenset({"c0"}), frozenset({"c1"}), frozenset({"c0", "c1"})}, v2_states)
        self.assertIn(frozenset({"c1"}), v2_states)
        self.assertNotIn(frozenset({"c1"}), v1_states)

    def test_schema_load_and_shadow_corpus_counts(self):
        self.assertTrue(all(isinstance(record, ErratumV2) for record in self.parsed.values()))
        shadow_v2 = {rid for rid, record in self.shadow.errata.items() if isinstance(record, ErratumV2)}
        shadow_v1 = {rid for rid, record in self.shadow.errata.items() if isinstance(record, Erratum)}
        self.assertEqual(294, len(shadow_v2))
        self.assertEqual(2, len(shadow_v1))
        self.assertEqual(gate.MANUAL_EXCLUDED_IDS, shadow_v1)

    def test_manual_records_are_exactly_untouched_objects_and_bytes(self):
        for record_id, original_bytes in self.manual_bytes.items():
            self.assertIs(self.repo.errata[record_id], self.shadow.errata[record_id], record_id)
            self.assertIsInstance(self.shadow.errata[record_id], Erratum, record_id)
            self.assertEqual(original_bytes, self.repo.errata[record_id].path.read_bytes(), record_id)

    def test_all_current_format_outputs_and_substitution_maps_are_identical(self):
        self.assertEqual({"2005-04-goat", "2010-03-edison"}, set(self.result["consumers"]["formats"]))
        for fmt_id, outcome in self.result["consumers"]["formats"].items():
            self.assertTrue(outcome["text_identical"], fmt_id)
            self.assertTrue(outcome["entries_identical"], fmt_id)
            self.assertTrue(outcome["hash_identical"], fmt_id)
            self.assertTrue(outcome["substitution_map_identical"], fmt_id)
        goat = self.result["consumers"]["formats"]["2005-04-goat"]
        self.assertEqual(0x28E9FC02, goat["baseline_hash"])
        self.assertEqual(goat["baseline_hash"], goat["shadow_hash"])

        for fmt_id, maps in self.result["consumers"]["substitution_maps"].items():
            self.assertEqual(maps["baseline"], maps["shadow"], fmt_id)
            self.assertTrue(maps["identical"], fmt_id)

    def test_validator_has_zero_errors_and_no_warning_delta(self):
        consumers = self.result["consumers"]
        self.assertEqual(0, consumers["baseline_error_count"])
        self.assertEqual(0, consumers["shadow_error_count"])
        self.assertEqual({}, consumers["new_error_codes"])
        self.assertEqual({}, consumers["warning_code_delta"])
        self.assertEqual(consumers["baseline_warning_codes"], consumers["shadow_warning_codes"])

    def test_report_logic_runs_for_294_v2_and_2_v1(self):
        reports = self.result["consumers"]["report_outputs"]
        self.assertIn("v2 (historical-event DAG): 247 records", reports["baseline"])
        self.assertIn("v2 (historical-event DAG): 294 records", reports["shadow"])
        self.assertIn("errata: 49 records", reports["baseline"])
        self.assertIn("errata: 2 records", reports["shadow"])

    def test_historical_scope_has_no_canonical_or_runtime_changes(self):
        """The proof remains true after later canonical migrations land."""
        changed = subprocess.check_output(
            [
                "git",
                "-C",
                str(audit.REPO_ROOT),
                "diff",
                "--name-only",
                "--diff-filter=ACDMRTUXB",
                SOURCE_COMMIT,
                GATE_COMMIT,
                "--",
                *HISTORICAL_PROTECTED_PATHS,
            ],
            text=True,
        )
        self.assertEqual([], [line for line in changed.splitlines() if line])

    def test_gate_commit_changed_files_are_exactly_the_gate_files(self):
        changed = subprocess.check_output(
            [
                "git",
                "-C",
                str(audit.REPO_ROOT),
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "--diff-filter=ACDMRTUXB",
                "-r",
                GATE_COMMIT,
            ],
            text=True,
        )
        self.assertEqual(GATE_FILES, {line for line in changed.splitlines() if line})


if __name__ == "__main__":
    unittest.main()
