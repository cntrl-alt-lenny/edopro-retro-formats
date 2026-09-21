import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_progress_badge.py"
BADGE = ROOT / "docs" / "assets" / "progress-badge.json"
README = ROOT / "README.md"
EXPECTED_COUNTS = (7, 12, "7/12 complete")
EXPECTED_ALT_TEXT = [
    "CI status",
    "Canonical implementation-area progress",
    "Python runtime",
    "License",
]


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
        self.assertEqual(
            (
                payload["complete_or_verified_areas"],
                payload["total_areas"],
                payload["message"],
            ),
            EXPECTED_COUNTS,
            "If canonical statuses legitimately change, regenerate docs/assets/progress-badge.json and update EXPECTED_COUNTS here.",
        )
        self.assertEqual(len(payload["formats"]), 3)

    def test_badge_alt_text_contains_no_live_values(self):
        html = README.read_text(encoding="utf-8")
        badge_row = re.search(r"<p>\n(.*?)</p>", html, re.DOTALL).group(1)
        actual = re.findall(r'<img\b[^>]*\balt="([^"]+)"', badge_row)
        self.assertEqual(
            actual,
            EXPECTED_ALT_TEXT,
            "Badge alt text is intentionally value-free; update this static-description list only if badge meaning changes.",
        )


if __name__ == "__main__":
    unittest.main()
