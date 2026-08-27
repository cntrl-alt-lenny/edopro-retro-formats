"""Independent regressions for the Last Will manual adjudication.

These assertions pin the researched event decomposition and its consequences;
they do not build a candidate payload and compare it with itself.
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

from . import unordered_migration_materializer as gate
from .pre_migration_fixture import load_pre_migration_repo
from .schema_check import Registry, validate_erratum


SOURCE_COMMIT = "e294086d9f9096e82aca12ecdf1fa272e5a0b758"
LAST_WILL_ID = "erratum-last-will"


def _with_last_will(repo: Repository, record) -> Repository:
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


class LastWillV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.repo = Repository.load(cls.root)
        cls.record = cls.repo.errata[LAST_WILL_ID]
        cls.raw = json.loads(cls.record.path.read_text(encoding="utf-8"))
        cls.frozen = load_pre_migration_repo()
        cls.old = cls.frozen.errata[LAST_WILL_ID]
        cls.before = _with_last_will(cls.repo, cls.old)

    def test_live_record_is_full_v2_and_corpus_is_complete(self):
        self.assertIsInstance(self.record, ErratumV2)
        self.assertEqual(296, len(self.repo.errata))
        self.assertEqual(296, sum(isinstance(r, ErratumV2) for r in self.repo.errata.values()))
        self.assertEqual(0, sum(isinstance(r, Erratum) for r in self.repo.errata.values()))
        counts = Counter(
            key for raw in (
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((self.root / "data/errata").glob("*.json"))
            )
            for key in ("changes", "events", "event")
            if key in raw
        )
        self.assertEqual(0, counts.get("changes", 0))
        self.assertEqual(116, counts["events"])
        self.assertEqual(180, counts["event"])
        self.assertNotIn("changes", self.raw)

    def test_exact_event_decomposition_and_cooccurrence(self):
        self.assertEqual({"c0", "c1", "c2"}, set(self.record.events))
        self.assertEqual(
            {
                "c0": [("functional", "retroactivity"), ("functional", "usage-window")],
                "c1": [("ruling", "search-activation-legality")],
                "c2": [("ruling", "search-reveal-procedure")],
            },
            {
                event_id: [(t.kind, t.axis) for t in event.transitions]
                for event_id, event in self.record.events.items()
            },
        )
        self.assertEqual(
            ["yugipedia-card-errata", "yugipedia-set-pages"],
            self.raw["events"]["c0"]["cooccurrence_sources"],
        )
        self.assertNotIn("cooccurrence_sources", self.raw["events"]["c1"])
        self.assertNotIn("cooccurrence_sources", self.raw["events"]["c2"])

    def test_ordering_is_exact_and_unproven_mutation_is_rejected(self):
        self.assertEqual({"chains": [["c0", "c2"]]}, self.raw["ordering"])
        self.assertEqual(
            "proven",
            ordering_proof(self.record.events["c0"].effective, self.record.events["c2"].effective),
        )
        for before, after in (("c0", "c1"), ("c1", "c0"), ("c1", "c2"), ("c2", "c1")):
            self.assertEqual(
                "inconclusive",
                ordering_proof(self.record.events[before].effective, self.record.events[after].effective),
            )

        mutated = copy.deepcopy(self.raw)
        mutated["ordering"] = {"chains": [["c0", "c1"]]}
        bad = ErratumV2.load(mutated, self.record.path)
        validator = Validator(_with_last_will(self.repo, bad))
        validator.validate()
        self.assertIn("erratum.ordering-chain-not-proven", {finding.code for finding in validator.errors})

    def test_declaration_order_does_not_change_selection(self):
        reversed_raw = copy.deepcopy(self.raw)
        reversed_raw["events"] = dict(reversed(list(reversed_raw["events"].items())))
        reversed_record = ErratumV2.load(reversed_raw, self.record.path)
        for snapshot in (dt.date(2005, 4, 1), dt.date(2010, 4, 24), dt.date(2020, 1, 1)):
            self.assertEqual(
                {c.events for c in self.record.selection_at(snapshot).candidates},
                {c.events for c in reversed_record.selection_at(snapshot).candidates},
            )

    def test_state_space_and_coverage_are_exact(self):
        expected = {
            frozenset(),
            frozenset({"c0"}),
            frozenset({"c1"}),
            frozenset({"c0", "c1"}),
            frozenset({"c0", "c2"}),
            frozenset({"c0", "c1", "c2"}),
        }
        self.assertEqual(expected, set(self.record.structural_states()))
        self.assertEqual(Coverage.REUSE_UPSTREAM, self.record.state_for(frozenset()).coverage.kind)
        self.assertEqual(504700147, self.record.state_for(frozenset()).coverage.historical_passcode)
        self.assertEqual(Coverage.KNOWN_GAP, self.record.state_for(frozenset({"c0"})).coverage.kind)
        for events in expected - {frozenset(), frozenset({"c0"}), frozenset({"c0", "c1", "c2"})}:
            self.assertEqual(Coverage.UNRESOLVED, self.record.state_for(events).coverage.kind)
        self.assertEqual(Coverage.MODERN, self.record.state_for(frozenset({"c0", "c1", "c2"})).coverage.kind)
        self.assertEqual({frozenset(), frozenset({"c0"})}, set(self.record.authored_states))

    def test_goat_and_edison_candidates_and_historical_identity(self):
        goat = self.record.selection_at(dt.date(2005, 4, 1))
        self.assertEqual({frozenset(), frozenset({"c1"})}, {c.events for c in goat.candidates})
        self.assertFalse(goat.modern_is_possible)
        edison = self.record.selection_at(dt.date(2010, 4, 24))
        self.assertEqual(
            {frozenset({"c0"}), frozenset({"c0", "c1"})},
            {c.events for c in edison.candidates},
        )
        self.assertFalse(edison.modern_is_possible)
        self.assertEqual(Coverage.KNOWN_GAP, edison.candidates[0].coverage.kind)
        self.assertEqual(504700147, self.raw["states"][0]["coverage"]["historical_passcode"])
        self.assertEqual("goat/c504700147.lua", self.raw["states"][0]["coverage"]["script"])

    def test_schema_repository_references_and_terminal_behavior(self):
        self.assertEqual([], validate_erratum(self.raw, Registry()))
        self.assertEqual([], self.repo.load_errors)
        validator = Validator(self.repo)
        validator.validate()
        self.assertEqual([], validator.errors)
        self.assertEqual([], sorted(collect_referenced_passcodes(self.repo) - set(self.repo.card_index.by_passcode)))

    def test_outputs_pool_and_warning_delta_match_frozen_v1_baseline(self):
        for fmt_id in sorted(self.repo.formats):
            before = build_lflist(self.before.formats[fmt_id], self.before)
            after = build_lflist(self.repo.formats[fmt_id], self.repo)
            self.assertEqual((before.text, before.entries, before.hash), (after.text, after.entries, after.hash), fmt_id)
            self.assertEqual(
                gate._substitution_map(self.before.formats[fmt_id], self.before),
                gate._substitution_map(self.repo.formats[fmt_id], self.repo),
                fmt_id,
            )
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

    def test_last_will_metadata_and_historical_fixture_are_preserved(self):
        old_bytes = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:data/errata/last-will.json"])
        self.assertEqual(old_bytes, self.old.path.read_bytes())
        self.assertIsInstance(self.old, Erratum)
        self.assertEqual(self.old.raw["modern_card"], self.raw["modern_card"])
        self.assertEqual(self.old.raw["classification"], self.raw["classification"])
        self.assertEqual(self.old.raw["sources"], self.raw["sources"])
        self.assertEqual(self.old.raw["implementation"]["historical_passcode"], 504700147)
        self.assertEqual(self.raw["implementation_metadata"][0]["status"], "complete")
        self.assertEqual(self.raw["implementation_metadata"][1]["events"], ["c0"])
        self.assertTrue(self.raw["implementation_metadata"][1]["gap"]["upstream_checked"])

    def test_manual_model_requires_cooccurrence_source(self):
        mutated = copy.deepcopy(self.raw)
        mutated["events"]["c0"].pop("cooccurrence_sources")
        self.assertTrue(validate_erratum(mutated, Registry()))


if __name__ == "__main__":
    unittest.main()
