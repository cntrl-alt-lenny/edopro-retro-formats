"""Reproducibility checks for the research-only Tengu format gate.

These tests intentionally do not create a format, banlist, pool, or rule
profile.  They prove only the researched inputs and the current architecture's
ability to evaluate a proposed snapshot in memory.
"""

from __future__ import annotations

import datetime as _dt
import json
import unittest
from pathlib import Path

from retroformats.model import ErratumV2, Pool
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs" / "research" / "tengu-format-source-packet.json"


class TenguResearchGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(ROOT)
        cls.packet = json.loads(PACKET.read_text(encoding="utf-8"))

    def test_gate_has_no_canonical_tengu_artifacts(self):
        self.assertFalse(any(ROOT.glob("formats/*tengu*")))
        self.assertFalse(any((ROOT / "data" / "banlists").glob("**/*tengu*")))
        self.assertFalse(any((ROOT / "data" / "pools").glob("*tengu*")))
        self.assertFalse(any((ROOT / "data" / "rule-profiles").glob("*tengu*")))

    def test_researched_banlist_packet_is_exactly_sized_and_internally_consistent(self):
        banlist = self.packet["banlist"]
        self.assertIn("yugioh-card.com", banlist["source"])
        self.assertEqual(51, len(banlist["forbidden"]))
        self.assertEqual(65, len(banlist["limited"]))
        self.assertEqual(18, len(banlist["semi_limited"]))
        self.assertEqual(7, len(banlist["unlimited_changes"]))
        all_codes = [row["passcode"] for key in ("forbidden", "limited", "semi_limited", "unlimited_changes") for row in banlist[key]]
        self.assertEqual(len(all_codes), len(set(all_codes)))
        self.assertEqual(85602018, next(row["passcode"] for row in banlist["forbidden"] if row["name"] == "Last Will"))

    def test_all_296_errata_evaluate_at_proposed_snapshot_without_runtime_changes(self):
        self.assertEqual([], [str(e) for e in self.repo.load_errors])
        self.assertEqual(296, len(self.repo.errata))
        self.assertTrue(all(isinstance(e, ErratumV2) for e in self.repo.errata.values()))
        snapshot = _dt.date(2011, 9, 17)
        selections = {eid: e.selection_at(snapshot) for eid, e in self.repo.errata.items()}
        self.assertEqual(126, sum(s.chronology == "determinate" for s in selections.values()))
        self.assertEqual(170, sum(s.chronology == "ambiguous" for s in selections.values()))
        self.assertEqual(161, sum(s.modern_is_possible for s in selections.values() if s.chronology == "ambiguous"))
        self.assertEqual(9, sum(not s.modern_is_possible for s in selections.values() if s.chronology == "ambiguous"))

    def test_certified_release_projection_is_fresh_not_edison_derived(self):
        self.assertIsNotNone(self.repo.release_coverage)
        self.assertTrue(
            self.repo.release_coverage.covers(
                _dt.date(2011, 9, 17),
                frozenset({"tcg", "tcg-na", "tcg-eu", "tcg-oce"}),
                self.repo.release_gaps,
            )
        )
        index = ReleaseIndex.build(self.repo)
        raw = {
            "$schema": "../../schemas/pool.schema.json",
            "id": "research-only-tengu-projection",
            "region": "TCG",
            "kind": "release-cutoff",
            "cutoff": {
                "cutoff_date": "2011-09-17",
                "territories": ["tcg", "tcg-na", "tcg-eu", "tcg-oce"],
                "include": [
                    {
                        "card": {"passcode": 37115575, "name": "Malefic Truth Dragon"},
                        "reason": "JUMP-EN048 is identified as a March 2011 release by the official card database.",
                        "sources": ["konami-card-database"],
                    }
                ],
                "exclude": [],
                "exclude_products": [
                    {
                        "product": product,
                        "reason": "Research-only policy: Duel Terminal machine exclusives and Sneak Peek participation products are not used as ordinary retail pool authority.",
                        "sources": ["konami-event-faqs-2009-2010"],
                    }
                    for product in (
                        "duel-terminal-4",
                        "duel-terminal-5",
                        "duel-terminal-5a",
                        "storm-of-ragnarok-sneak-peek-participation-card",
                        "extreme-victory-sneak-peek-participation-card",
                        "generation-force-sneak-peek-participation-card",
                    )
                ],
            },
        }
        pool = Pool.load(raw, Path("/tmp/research-only-tengu-projection.json"))
        evaluation = evaluate_cutoff(pool, self.repo, index)
        self.assertEqual(4563, len(evaluation.included))
        self.assertEqual(0, len(evaluation.ambiguous))
        self.assertEqual(0, len(index.unknown_printings))
        excluded = {entry["product"] for entry in raw["cutoff"]["exclude_products"]}
        self.assertNotIn("the-shining-darkness", excluded)
        self.assertNotIn("shonen-jump-may-2010-subscription-bonus", excluded)

        self.assertEqual(4593, index.dated_canonical_count())

    def test_packet_records_the_certified_projection_and_import_audit(self):
        certification = self.packet["release_certification"]
        self.assertTrue(certification["coverage_certified"])
        self.assertEqual(411, certification["ledger_products"])
        self.assertEqual(41, certification["new_pre_toronto_products"])
        self.assertEqual(4563, certification["candidate_pool"]["included_cards"])
        self.assertEqual(0, certification["candidate_pool"]["ambiguous_cards"])
        self.assertEqual(0, certification["candidate_pool"]["unknown_printings"])
        self.assertEqual(0, certification["import_anomalies"]["unresolved_pool_impacting_gaps"])

    def test_release_ledger_has_the_2011_products_and_import_anomalies_accounted(self):
        expected = {
            "collectible-tins-2011-wave-1", "demo-pack", "dragunity-legion-structure-deck",
            "duel-terminal-4", "duel-terminal-5", "duel-terminal-5a",
            "duelist-league-3-participation-cards", "duelist-pack-collection-tin-2011",
            "duelist-pack-crow", "duelist-pack-yusei-3", "extreme-victory",
            "extreme-victory-sneak-peek-participation-card", "generation-force",
            "generation-force-sneak-peek-participation-card", "generation-force-special-edition",
            "gold-series-4-pyramids-edition", "hidden-arsenal-4-trishula-s-triumph",
            "hidden-arsenal-special-edition", "lost-sanctuary-structure-deck",
            "shonen-jump-june-july-2011-subscription-bonus", "shonen-jump-vol-9-issue-3-promotional-card",
            "shonen-jump-vol-9-issue-4-promotional-card", "shonen-jump-vol-9-issue-6-promotional-card",
            "shonen-jump-vol-9-issue-8-promotional-card", "starter-deck-dawn-of-the-xyz",
            "storm-of-ragnarok", "storm-of-ragnarok-sneak-peek-participation-card",
            "storm-of-ragnarok-special-edition", "turbo-pack-booster-five", "turbo-pack-booster-six",
            "world-championship-2011-card-pack", "yu-gi-oh-3d-bonds-beyond-time-dvd-promotional-card",
            "yu-gi-oh-3d-bonds-beyond-time-movie-pack", "yu-gi-oh-3d-bonds-beyond-time-theater-distribution-card",
            "yu-gi-oh-5d-s-volume-1-promotional-card",
            "yu-gi-oh-5d-s-world-championship-2011-over-the-nexus-promotional-cards",
            "yu-gi-oh-championship-series-2011-prize-card", "yu-gi-oh-gx-volume-6-promotional-card",
            "yu-gi-oh-gx-volume-7-promotional-card", "yu-gi-oh-gx-volume-9-promotional-card",
            "yu-gi-oh-world-championship-qualifier-national-championships-2011-prize-cards",
        }
        self.assertEqual(41, len(expected))
        self.assertTrue(expected.issubset(self.repo.products))
        self.assertEqual(411, len(self.repo.products))
        self.assertEqual(404, self.repo.import_report["stats"]["products_written"])
        self.assertEqual(34, self.repo.import_report["stats"]["yugipedia_only_products"])
        subjects = {s for g in self.repo.release_gaps for s in g.raw["subjects"]}
        self.assertIn("Yu-Gi-Oh! 3D Bonds Beyond Time Blu-ray promotional card", subjects)
        self.assertIn("Yu-Gi-Oh! World Championship 2011 prize cards", subjects)

    def test_proposed_flags_are_declared_research_inputs_not_hidden_runtime_changes(self):
        self.assertEqual(
            {
                "DUEL_OCG_OBSOLETE_IGNITION",
                "DUEL_1ST_TURN_DRAW",
                "DUEL_1_FACEUP_FIELD",
                "DUEL_SPSUMMON_ONCE_OLD_NEGATE",
                "DUEL_RETURN_TO_DECK_TRIGGERS",
                "DUEL_CANNOT_SUMMON_OATH_OLD",
            },
            set(self.packet["proposed_engine_flags"]),
        )


if __name__ == "__main__":
    unittest.main()
