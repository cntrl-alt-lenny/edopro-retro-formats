"""The similarity limit that decides whether a generated script may be labelled
`original` (roadmap item 7, rounds 032 and 034).

The limit is the whole gate: `tests/engine/test_script_origin.py` fails an
`original` script whose line-sequence ratio against Project Ignis's script for
its alias reaches it. Raise it and a script that copies AGPL-3.0-or-later code
passes as MIT, so nothing else in the suite would notice. It is pinned here.
"""

from __future__ import annotations

import unittest

from retroformats import script_similarity
from retroformats.script_similarity import ORIGINAL_MAX_RATIO, Similarity, too_close


class OriginalMaxRatioIsPinnedTest(unittest.TestCase):
    def test_the_similarity_limit_is_not_changed_without_a_brief(self):
        """`ORIGINAL_MAX_RATIO` must be 0.40. Changing it needs a brief that names
        that as its purpose (AGENTS.md: no validation rule is loosened without
        one); do not edit this number to make a script pass.

        Round 032's calibration, each script against Ignis's official script for its
        alias at CardScripts 383bfbd6 (docs/rounds/032-derived-scripts-licence/builder.md):

        - measured too close, and found by review to be adaptations (so `derived`):
          Goddess of Whim 0.72, Soul Rope 0.71, Night Assailant 0.69, Green Baboon 0.61,
          Rise of the Snake Deity 0.58, Strike Ninja 0.51
        - accepted as original: Stealth Union 0.31, Metalzoa 0.27, Malefic Blue-Eyes 0.13

        0.40 sits in the gap between 0.31 and 0.51, nearer the accepted side, so a
        borderline script is flagged rather than passed: a false flag costs a relabel to
        `derived`; a false pass is mislicensed code.
        """
        self.assertEqual(
            0.40,
            ORIGINAL_MAX_RATIO,
            "ORIGINAL_MAX_RATIO is 0.40 and changing it needs a brief that says so: it is the only "
            "thing that keeps a script adapted from Project Ignis's from being labelled original (MIT). "
            f"It is {ORIGINAL_MAX_RATIO} now. Round 032's calibration is in this test's docstring.",
        )

    def test_the_limit_is_what_too_close_compares_against(self):
        # The pin above would mean nothing if too_close() read some other number.
        def at(ratio):
            return Similarity(ratio=ratio, identical_lines=0, lines=1, shared_windows=0, windows=0)

        self.assertFalse(too_close(at(0.39)))
        self.assertTrue(too_close(at(0.40)), "the limit itself is too close: the comparison is >=")
        self.assertTrue(too_close(at(0.51)), "the lowest ratio round 032 found to be an adaptation")
        self.assertFalse(too_close(at(0.31)), "the highest ratio round 032 accepted as original")
        self.assertIs(script_similarity.ORIGINAL_MAX_RATIO, ORIGINAL_MAX_RATIO)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
