"""Regression tests for the release-pool materialisation command."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from .helpers import TempRepoTest, card, event, printing

ROOT = Path(__file__).resolve().parents[1]


class MaterializeCommandRegressionTest(TempRepoTest):
    def _seed(self, *, release_date="2005-01-01", pool_cards=None):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_product(
            code="OLD",
            release_events=[event("tcg-na", release_date)],
            printings=[printing(100, "Alpha", "OLD-EN001")],
        )
        self.add_product(
            code="NEW",
            release_events=[event("tcg-na", "2009-01-01")],
            printings=[printing(200, "Beta", "NEW-EN001")],
        )
        self.add_coverage()
        self.add_import_report()
        self.add_cutoff_pool(
            cards=pool_cards if pool_cards is not None else [card(100, "Alpha")]
        )

    def _run_materialize(self):
        return subprocess.run(
            [sys.executable, "-m", "retroformats", "--root", str(self.root), "materialize"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def test_stale_pool_is_rewritten_by_real_materialize_command(self):
        self._seed(pool_cards=[card(100, "Alpha"), card(200, "Beta")])
        before = json.loads((self.root / "data/pools/cut.json").read_text(encoding="utf-8"))
        self.assertEqual({100, 200}, {entry["passcode"] for entry in before["cards"]})

        result = self._run_materialize()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        after = json.loads((self.root / "data/pools/cut.json").read_text(encoding="utf-8"))
        self.assertEqual([100], [entry["passcode"] for entry in after["cards"]])

    def test_structurally_invalid_release_data_still_refuses_materialization(self):
        self._seed(
            release_date="not-a-date",
            pool_cards=[card(100, "Alpha"), card(200, "Beta")],
        )
        before = (self.root / "data/pools/cut.json").read_text(encoding="utf-8")
        result = self._run_materialize()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("releases.bad-date", result.stderr)
        self.assertIn("refusing to derive pools from invalid data", result.stderr)
        self.assertEqual(before, (self.root / "data/pools/cut.json").read_text(encoding="utf-8"))
