"""A format's `notes` state no count that a record edit can move (round 038, part B2).

Round 037's review found two `notes` fields that still said "exactly 52 historical implementations ... 161 ...
9" (Tengu) and "currently 72 historical implementations" (Edison) while the tests pinned other numbers: nothing
read the strings, so they went stale in silence, and Tengu's card count had drifted the same way. The counts
belong to the computed report (`python -m retroformats report -v`) and to the pins in the tests; a note points
there. Two designs were open: a test that recomputes each number a note states and fails on drift, or a note
with no such number. The second was chosen: a note cannot go stale about a number it does not carry, and a
recomputing test would have to parse prose. This test keeps a count from coming back.
"""

from __future__ import annotations

import json
import re
import unittest

from .helpers import REPO_ROOT

# A number attached to a thing the records or the pool change: cards, implementations, defaults, fallbacks,
# substitutions, divergences; or "exactly N".
COUNT = re.compile(
    r"(?:\bexactly\s+\d|\b\d[\d,]*\s+(?:[\w-]+\s+){0,3}"
    r"(?:cards?|implementations?|substitutions?|defaults?|fallbacks?|divergences?|records?))",
    re.IGNORECASE,
)


# The two formats whose errata are computed from the records. GOAT's note mentions "the old 211-entry ... list",
# which is history it replaced, not a count of anything it computes now.
COMPUTED_ERRATA_FORMATS = ("2010-03-edison", "2011-09-tengu")


class FormatNotesStateNoCountsTest(unittest.TestCase):
    def _notes(self):
        for format_id in COMPUTED_ERRATA_FORMATS:
            path = REPO_ROOT / "formats" / format_id / "format.json"
            yield path, json.loads(path.read_text(encoding="utf-8")).get("notes") or ""

    def test_the_pattern_finds_the_counts_round_037_found(self):
        for stale in (
            "exactly 52 historical implementations are substituted",
            "surfacing 161 ambiguous-modern-possible defaults and 9 modern-impossible known-wrong fallbacks",
            "currently 72 historical implementations are substituted",
            "certified coverage (4,562 cards)",
        ):
            with self.subTest(stale=stale):
                self.assertIsNotNone(COUNT.search(stale))

    def test_no_format_note_states_a_count(self):
        found = {
            path.parent.name: [m.group(0) for m in COUNT.finditer(notes)]
            for path, notes in self._notes()
            if COUNT.search(notes)
        }
        self.assertEqual({}, found, "a format note states a count; point to `python -m retroformats report -v` instead")


if __name__ == "__main__":
    unittest.main()
