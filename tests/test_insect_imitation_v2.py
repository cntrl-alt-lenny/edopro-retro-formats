"""Independent regression tests for the Insect Imitation adjudication.

The expected three-event shape is asserted directly from the research
conclusion.  This deliberately does not call a constructor and compare its
output with itself.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import subprocess
import unittest
from collections import Counter
from pathlib import Path

from retroformats.importers.card_index import collect_referenced_passcodes
from retroformats.lflist import build_lflist
from retroformats.model import Coverage, Erratum, ErratumV2, ordering_proof
from retroformats.repo import Repository
from retroformats.validate import Validator

from .pre_migration_fixture import load_pre_migration_repo
from .schema_check import Registry, validate_erratum


SOURCE_COMMIT = "e960cf0e70bf1b03b8e9c4ce4ffa23a7c9a73267"
INSECT_ID = "erratum-insect-imitation"
LAST_WILL_ID = "erratum-last-will"


def _with_erratum(repo: Repository, record) -> Repository:
    return Repository(
        root=repo.root,
        banlists=repo.banlists,
        pools=repo.pools,
        rule_profiles=repo.rule_profiles,
        errata={**repo.errata, record.id: record},
        formats=repo.formats,
        global_sources=repo.global_sources,
        format_sources=repo.format_sources,
        card_index=repo.card_index,
        products=repo.products,
        release_coverage=repo.release_coverage,
        release_gaps=repo.release_gaps,
        import_report=repo.import_report,
        load_errors=[],
    )


class InsectImitationV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.repo = Repository.load(cls.root)
        cls.insect = cls.repo.errata[INSECT_ID]
        cls.raw = json.loads(cls.insect.path.read_text(encoding="utf-8"))
        cls.frozen = load_pre_migration_repo()
        cls.old_insect = cls.frozen.errata[INSECT_ID]
        cls.before = _with_erratum(cls.repo, cls.old_insect)

    def test_last_will_is_untouched_from_adjudication_baseline(self):
        historical = self.frozen.errata[LAST_WILL_ID]
        expected = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:data/errata/last-will.json"])
        self.assertEqual(expected, historical.path.read_bytes())
        self.assertIsInstance(historical, Erratum)

    def test_three_separate_events_and_no_cooccurrence(self):
        self.assertIsInstance(self.insect, ErratumV2)
        self.assertEqual({"c0", "c1", "c2"}, set(self.insect.events))
        self.assertEqual(
            {
                "c0": ("functional", "summon-position"),
                "c1": ("ruling", "search-activation-legality"),
                "c2": ("ruling", "search-reveal-procedure"),
            },
            {
                event_id: (event.transitions[0].kind, event.transitions[0].axis)
                for event_id, event in self.insect.events.items()
            },
        )
        for event in self.raw["events"].values():
            self.assertEqual(1, len(event["transitions"]))
            self.assertNotIn("cooccurrence_sources", event)

    def test_only_date_proven_ordering_edge_is_position_before_verification(self):
        self.assertEqual({"chains": [["c0", "c2"]]}, self.raw["ordering"])
        self.assertEqual(
            "proven",
            ordering_proof(self.insect.events["c0"].effective, self.insect.events["c2"].effective),
        )
        for before, after in (("c0", "c1"), ("c1", "c0"), ("c1", "c2"), ("c2", "c1")):
            self.assertEqual(
                "inconclusive",
                ordering_proof(self.insect.events[before].effective, self.insect.events[after].effective),
            )

    def test_state_space_and_coverage_are_independently_pinned(self):
        expected_states = {
            frozenset(),
            frozenset({"c0"}),
            frozenset({"c1"}),
            frozenset({"c0", "c1"}),
            frozenset({"c0", "c2"}),
            frozenset({"c0", "c1", "c2"}),
        }
        self.assertEqual(expected_states, set(self.insect.structural_states()))
        self.assertEqual(Coverage.REUSE_UPSTREAM, self.insect.state_for(frozenset()).coverage.kind)
        self.assertEqual(504700171, self.insect.state_for(frozenset()).coverage.historical_passcode)
        self.assertEqual(Coverage.KNOWN_GAP, self.insect.state_for(frozenset({"c0"})).coverage.kind)
        for state in expected_states - {frozenset(), frozenset({"c0"}), frozenset({"c0", "c1", "c2"})}:
            self.assertEqual(Coverage.UNRESOLVED, self.insect.state_for(state).coverage.kind)
        self.assertEqual(Coverage.MODERN, self.insect.state_for(frozenset({"c0", "c1", "c2"})).coverage.kind)
        self.assertEqual({frozenset(), frozenset({"c0"})}, set(self.insect.authored_states))
        self.assertEqual({frozenset(), frozenset({"c0"})}, set(self.insect.implementation_metadata))

    def test_goat_and_edison_candidate_sets(self):
        goat = self.insect.selection_at(dt.date(2005, 4, 1))
        self.assertEqual({frozenset(), frozenset({"c1"})}, {c.events for c in goat.candidates})
        self.assertFalse(goat.modern_is_possible)
        self.assertEqual(
            {frozenset({"c0"}), frozenset({"c0", "c1"})},
            {c.events for c in self.insect.selection_at(dt.date(2010, 4, 24)).candidates},
        )
        edison = self.insect.selection_at(dt.date(2010, 4, 24))
        self.assertFalse(edison.modern_is_possible)
        self.assertEqual(Coverage.KNOWN_GAP, edison.candidates[0].coverage.kind)

    def test_authored_data_and_metadata_survive_the_split(self):
        old = self.old_insect.raw
        self.assertEqual(old["modern_card"], self.raw["modern_card"])
        self.assertEqual(old["classification"], self.raw["classification"])
        self.assertEqual(old["sources"], self.raw["sources"][: len(old["sources"])])
        self.assertEqual(old["changes"][0]["effective"]["date"], self.raw["events"]["c0"]["effective"]["date"])
        self.assertEqual(old["changes"][0]["effective"]["precision"], self.raw["events"]["c0"]["effective"]["precision"])
        self.assertEqual(old["changes"][0]["effective"]["status"], self.raw["events"]["c0"]["effective"]["status"])
        self.assertEqual(old["changes"][0]["historical_text"], self.raw["events"]["c0"]["transitions"][0]["historical_text"])
        self.assertEqual(old["changes"][0]["modern_text"], self.raw["events"]["c0"]["transitions"][0]["modern_text"])
        self.assertEqual(old["changes"][1]["historical_text"], self.raw["events"]["c1"]["transitions"][0]["historical_text"])
        self.assertEqual(old["changes"][1]["historical_text"], self.raw["events"]["c2"]["transitions"][0]["historical_text"])
        self.assertEqual(504700171, self.raw["states"][0]["coverage"]["historical_passcode"])
        self.assertEqual("complete", self.raw["implementation_metadata"][0]["status"])
        self.assertTrue(self.raw["implementation_metadata"][1]["gap"]["upstream_checked"])

    def test_schema_repository_and_references_are_clean(self):
        self.assertEqual([], validate_erratum(self.raw, Registry()))
        self.assertEqual([], self.repo.load_errors)
        self.assertEqual([], sorted(collect_referenced_passcodes(self.repo) - set(self.repo.card_index.by_passcode)))
        validator = Validator(self.repo)
        validator.validate()
        self.assertEqual([], validator.errors)

    def test_outputs_and_warning_delta_match_the_documented_consequence(self):
        for fmt_id in sorted(self.repo.formats):
            before = build_lflist(self.before.formats[fmt_id], self.before)
            after = build_lflist(self.repo.formats[fmt_id], self.repo)
            self.assertEqual((before.text, before.entries, before.hash), (after.text, after.entries, after.hash), fmt_id)
        self.assertEqual(0x28E9FC02, build_lflist(self.repo.formats["2005-04-goat"], self.repo).hash)
        self.assertEqual(3673, len(self.repo.pools[self.repo.formats["2010-03-edison"].pool_id].cards))
        before_validator = Validator(self.before)
        after_validator = Validator(self.repo)
        before_validator.validate()
        after_validator.validate()
        self.assertEqual([], before_validator.errors)
        self.assertEqual([], after_validator.errors)
        self.assertEqual(
            Counter({"format.erratum-modern-known-wrong": 1}),
            Counter(f.code for f in after_validator.warnings) - Counter(f.code for f in before_validator.warnings),
        )
        self.assertEqual(
            Counter({"format.erratum-unresolved-defaulted": 1}),
            Counter(f.code for f in before_validator.warnings) - Counter(f.code for f in after_validator.warnings),
        )

    def test_adversarial_unproven_edge_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        mutated["ordering"] = {"chains": [["c0", "c1"]]}
        bad = ErratumV2.load(mutated, self.insect.path)
        bad_repo = _with_erratum(self.repo, bad)
        validator = Validator(bad_repo)
        validator.validate()
        self.assertIn("erratum.ordering-chain-not-proven", {finding.code for finding in validator.errors})


if __name__ == "__main__":
    unittest.main()
