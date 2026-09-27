"""The origin and licence each generated script claims, checked against the
pinned Project Ignis CardScripts checkout (round 032).

A script labelled `original` in data/custom-cards/ is this repository's own
MIT work. Rounds 029 and 031 showed that a script written "from scratch" can
still reproduce Ignis's AGPL-3.0-or-later script for the same card from
memory, so the label is measured here rather than trusted: every `original`
script must stay below `ORIGINAL_MAX_RATIO` against Ignis's script for its
alias (retroformats/script_similarity.py says what is measured and why the
limit is where it is). A script that is too close is relabelled `derived`,
credited and kept under AGPL-3.0-or-later, or rewritten.

These tests need only the pinned CardScripts checkout, not the core, but they
live with the engine tests on purpose: the checkout exists there, and
`scripts/engine_env.py run` fails on any skip, so CI's `engine` job cannot
pass without running them. Prerequisites are those of tests/engine/harness.py.
"""

from __future__ import annotations

import unittest

from retroformats.repo import Repository
from retroformats.script_similarity import ORIGINAL_MAX_RATIO, measure, too_close

from . import harness as H

REPO_ROOT = H.dist_path().parent
UPSTREAM_FOLDERS = ("official", "goat", "pre-errata", "unofficial", "pre-release")


def _upstream_script(cardscripts, passcode: int):
    """Ignis's script for `passcode`, resolved by filename across the folders
    EDOPro searches (docs/research/ignis-goat.md section 4)."""
    for folder in UPSTREAM_FOLDERS:
        path = cardscripts / folder / f"c{passcode}.lua"
        if path.is_file():
            return path
    return None


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class ScriptOriginTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(REPO_ROOT)
        cls.cardscripts = H.repos_path() / "cardscripts"
        cls.cards = [cls.repo.custom_cards[p] for p in sorted(cls.repo.custom_cards)]

    def _kind(self, card) -> str:
        return card.raw["authorship"]["kind"]

    def test_every_original_script_measurably_differs_from_ignis_script_for_its_alias(self):
        originals = [c for c in self.cards if self._kind(c) == "original"]
        self.assertTrue(originals, "no original script to measure; the gate would pass vacuously")
        for card in originals:
            with self.subTest(passcode=card.passcode, name=card.name):
                upstream = _upstream_script(self.cardscripts, card.alias)
                # No upstream script means nothing was measured: fail rather
                # than pass, so a missing file never reads as independence.
                self.assertIsNotNone(upstream, f"no Ignis script c{card.alias}.lua at the pinned revision")
                similarity = measure(
                    (REPO_ROOT / card.script).read_text(encoding="utf-8"),
                    upstream.read_text(encoding="utf-8"),
                )
                self.assertFalse(
                    too_close(similarity),
                    f"{card.script} is labelled original but its line-sequence ratio against "
                    f"{upstream.relative_to(self.cardscripts)} is {similarity.ratio:.2f} "
                    f"(limit {ORIGINAL_MAX_RATIO}; {similarity.identical_lines} of {similarity.lines} "
                    f"code lines identical, {similarity.shared_windows} shared 4-line windows). "
                    "Label it derived, credited and AGPL-3.0-or-later, or rewrite it.",
                )

    def test_every_derived_scripts_upstream_file_exists_at_the_pinned_revision(self):
        # The validator checks the record against data/sources.json offline;
        # only the checkout can show the named file is really there.
        derived = [c for c in self.cards if self._kind(c) == "derived"]
        for card in derived:
            with self.subTest(passcode=card.passcode, name=card.name):
                upstream = card.raw["authorship"]["upstream"]
                self.assertEqual("ignis-cardscripts", upstream["source"])
                self.assertTrue(
                    (self.cardscripts / upstream["path"]).is_file(),
                    f"{upstream['path']} is not in CardScripts at {upstream['revision']}",
                )

    def test_the_repositorys_agpl_text_is_ignis_copying(self):
        self.assertEqual(
            (self.cardscripts / "COPYING").read_bytes(),
            (REPO_ROOT / "LICENSES" / "AGPL-3.0-or-later.txt").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
