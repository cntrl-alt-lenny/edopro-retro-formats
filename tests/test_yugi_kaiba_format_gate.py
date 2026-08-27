"""Research-only gate for the proposed early OCG Tokyo Dome snapshot."""

from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from retroformats.model import Coverage, ErratumV2
from retroformats.repo import Repository


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "research" / "yugi-kaiba-format-source-packet.json"


class YugiKaibaResearchGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        cls.repo = Repository.load(ROOT)

    def test_packet_is_research_only_and_rejects_requested_label(self):
        self.assertEqual("research-gate-only", self.packet["status"])
        self.assertEqual("blocked", self.packet["canonicalization"])
        self.assertEqual("rejected", self.packet["target_recommendation"]["requested_label_verdict"])
        self.assertFalse(self.packet["scope"]["canonical_format_created"])

    def test_recommendation_is_the_pre_event_ocg_japan_snapshot(self):
        target = self.packet["target_recommendation"]
        self.assertEqual("1999-08-tokyo-dome", target["id"])
        self.assertEqual("ocg-jp", target["region"])
        self.assertEqual("1999-08-25", target["snapshot"])
        self.assertEqual("1999-08-26", target["event"]["date"])
        self.assertIsNone(target["previous"])

    def test_source_references_are_unique_and_resolvable(self):
        sources = self.packet["sources"]
        ids = [source["id"] for source in sources]
        self.assertEqual(len(ids), len(set(ids)))
        known = set(ids)

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "source_ids":
                        for source_id in child:
                            self.assertIn(source_id, known)
                    else:
                        walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(self.packet)
        for source in sources:
            self.assertTrue(source["url"].startswith(("http://", "https://")))

    def test_product_chronology_has_event_day_after_cutoff(self):
        entries = self.packet["product_chronology"]
        dates = [date.fromisoformat(entry["date"]) for entry in entries]
        self.assertEqual(dates, sorted(dates))
        self.assertLess(date.fromisoformat("1999-08-25"), dates[-1])
        self.assertIn("Tokyo Dome event and attendee/prize cards", entries[-1]["products"])

    def test_rules_and_architecture_keep_gaps_explicit(self):
        rules = self.packet["rules"]
        topics = {fact["topic"] for fact in rules["facts"]}
        self.assertIn("deck_out", topics)
        self.assertIn("battle_damage", topics)
        self.assertIn("chain_and_spell_speed", topics)
        self.assertIn("higher-LP-wins-deck-out", rules["candidate_core_flags"]["known_gaps"])
        self.assertFalse(self.packet["architecture"]["schema_change_required"])
        self.assertFalse(self.packet["architecture"]["runtime_change_required"])
        self.assertTrue(self.packet["architecture"]["format_local_approximation_required"])

    def test_frozen_errata_are_all_v2_and_accounted_at_snapshot(self):
        errata = list(self.repo.errata.values())
        self.assertEqual(296, len(errata))
        self.assertTrue(all(isinstance(record, ErratumV2) for record in errata))

        snapshot = date(1999, 8, 25)
        determinate = []
        ambiguous = []
        for record in errata:
            selection = record.selection_at(snapshot)
            (determinate if selection.chronology == "determinate" else ambiguous).append(selection)

        audit = self.packet["errata_audit"]
        self.assertEqual(296, audit["total"])
        self.assertEqual(146, len(determinate))
        self.assertEqual(150, len(ambiguous))
        self.assertEqual(146, audit["chronology"]["determinate"])
        self.assertEqual(150, audit["chronology"]["ambiguous"])

        determinate_modern = sum(selection.is_modern for selection in determinate)
        determinate_historical = len(determinate) - determinate_modern
        self.assertEqual(21, determinate_modern)
        self.assertEqual(125, determinate_historical)
        self.assertEqual(21, audit["determinate"]["modern"])
        self.assertEqual(125, audit["determinate"]["historical"])

        self.assertEqual(104, sum(selection.modern_is_possible for selection in ambiguous))
        self.assertEqual(46, sum(not selection.modern_is_possible for selection in ambiguous))
        self.assertEqual(104, audit["ambiguous"]["modern_possible"])
        self.assertEqual(46, audit["ambiguous"]["modern_impossible"])

        coverage_occurrences = {}
        candidate_occurrences = 0
        for selection in ambiguous:
            candidate_occurrences += len(selection.candidates)
            for candidate in selection.candidates:
                kind = candidate.coverage.kind.value
                coverage_occurrences[kind] = coverage_occurrences.get(kind, 0) + 1
        self.assertEqual(302, candidate_occurrences)
        self.assertEqual(302, audit["ambiguous"]["candidate_occurrences"])
        self.assertEqual(
            {"reuse-upstream": 144, "unresolved": 47, "known-gap": 7, "modern": 104},
            coverage_occurrences,
        )
        self.assertEqual(coverage_occurrences, audit["ambiguous"]["candidate_coverage_occurrences"])

    def test_current_repository_has_no_ocg_ledger_or_early_canonical_artifacts(self):
        self.assertEqual(0, sum(1 for product in self.repo.products.values() if any(event.territory.startswith("ocg") for event in product.events)))
        self.assertEqual(3, len(self.repo.formats))
        self.assertFalse((ROOT / "formats" / "1999-08-tokyo-dome").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "ocg-1999-07.json").exists())
        self.assertFalse((ROOT / "data" / "pools" / "1999-08-tokyo-dome.json").exists())
        self.assertFalse((ROOT / "data" / "rule-profiles" / "1999-08-tokyo-dome.json").exists())

    def test_coverage_gate_does_not_promote_modern_fallback_to_certification(self):
        audit = self.packet["errata_audit"]
        policy = audit["modern_policy_effect"]
        self.assertTrue(policy["explicit_policy_required"])
        self.assertEqual(150, policy["ambiguous_records_left_unresolved"])
        self.assertFalse(policy["certifiable"])
        self.assertEqual(Coverage.UNRESOLVED.value, "unresolved")


if __name__ == "__main__":
    unittest.main()
