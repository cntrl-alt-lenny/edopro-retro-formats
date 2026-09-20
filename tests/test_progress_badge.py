import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_progress_badge.py"
BADGE = ROOT / "docs" / "assets" / "progress-badge.json"


class ProgressBadgeTest(unittest.TestCase):
    def test_checked_in_badge_is_current(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_badge_counts_the_four_implementation_areas(self):
        payload = json.loads(BADGE.read_text(encoding="utf-8"))
        self.assertEqual(payload["source"], "formats/*/format.json implementation_status")
        self.assertEqual(payload["complete_or_verified_areas"], 7)
        self.assertEqual(payload["total_areas"], 12)
        self.assertEqual(payload["message"], "7/12 areas")
        self.assertEqual(len(payload["formats"]), 3)


if __name__ == "__main__":
    unittest.main()
