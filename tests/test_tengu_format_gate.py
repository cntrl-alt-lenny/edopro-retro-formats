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

    def test_current_release_projection_is_lower_bound_not_certified_tengu_pool(self):
        index = ReleaseIndex.build(self.repo)
        source_pool = self.repo.pools["pool-edison-2010"]
        raw = dict(source_pool.raw)
        raw["id"] = "research-only-tengu-projection"
        raw["cutoff"] = dict(source_pool.cutoff)
        raw["cutoff"]["cutoff_date"] = "2011-09-17"
        pool = Pool.load(raw, Path("/tmp/research-only-tengu-projection.json"))
        evaluation = evaluate_cutoff(pool, self.repo, index)
        self.assertEqual(4037, len(evaluation.included))
        self.assertEqual(0, len(evaluation.ambiguous))
        self.assertIsNotNone(self.repo.release_coverage)
        self.assertFalse(self.repo.release_coverage.covers(_dt.date(2011, 9, 17), evaluation.scope, self.repo.release_gaps))

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
