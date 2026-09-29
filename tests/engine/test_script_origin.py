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

import re
import sqlite3
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


def _pinned_alias_of(babelcdb, code: int) -> set[int]:
    """Every alias the pinned BabelCDB databases give the row with id `code`."""
    aliases = set()
    for cdb in sorted(babelcdb.glob("*.cdb")):
        con = sqlite3.connect(f"file:{cdb}?mode=ro", uri=True)
        try:
            aliases.update(row[0] for row in con.execute("SELECT alias FROM datas WHERE id=?", (code,)))
        finally:
            con.close()
    return aliases


def upstream_is_tied_to_card(cardscripts, babelcdb, path: str, alias: int) -> bool:
    """Whether Ignis's script at `path` is the script of the card with passcode
    `alias` (round 034). The validator (`custom-card.upstream-not-own-script`)
    sees only the path and lets `official/c<alias>.lua` and any `pre-errata/`
    file through; this is the half that needs the checkout:

    - `official/c<alias>.lua` is the card's own script, if the file is there;
    - a `pre-errata/c<code>.lua` is tied to the card when Ignis's own database
      row for `code` aliases `alias` (Ignis's pre-errata variants have private
      codes such as 511002631, whose row aliases the real card, 26202165).

    Anything else is not tied."""
    if not (cardscripts / path).is_file():
        return False
    if path == f"official/c{alias}.lua":
        return True
    match = re.fullmatch(r"pre-errata/c(\d+)\.lua", path)
    return bool(match) and alias in _pinned_alias_of(babelcdb, int(match.group(1)))


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class ScriptOriginTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(REPO_ROOT)
        cls.cardscripts = H.repos_path() / "cardscripts"
        cls.babelcdb = H.repos_path() / "babelcdb"
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

    def test_every_derived_scripts_upstream_is_the_script_of_its_own_card(self):
        # Round 034: a derived record could credit any file at the pin. The validator rejects
        # a path that cannot be the card's own; the checkout shows the file is really tied to
        # the row's alias.
        derived = [c for c in self.cards if self._kind(c) == "derived"]
        self.assertTrue(derived, "no derived script to check; the test would pass vacuously")
        for card in derived:
            with self.subTest(passcode=card.passcode, name=card.name):
                path = card.raw["authorship"]["upstream"]["path"]
                self.assertTrue(
                    upstream_is_tied_to_card(self.cardscripts, self.babelcdb, path, card.alias),
                    f"{path} is not Project Ignis's script for {card.name} ({card.alias})",
                )

    def test_the_tie_check_accepts_the_cards_own_and_its_pre_errata_script_and_nothing_else(self):
        # Sangan: Ignis ships official/c26202165.lua and a pre-errata variant under its own
        # private code, 511002631, whose database row aliases 26202165.
        sangan, rescue_cat = 26202165, 14878871
        tied = lambda path, alias: upstream_is_tied_to_card(self.cardscripts, self.babelcdb, path, alias)
        self.assertTrue(tied(f"official/c{sangan}.lua", sangan))
        self.assertTrue(tied("pre-errata/c511002631.lua", sangan))
        self.assertFalse(tied(f"official/c{sangan}.lua", rescue_cat), "another card's script")
        self.assertFalse(tied("pre-errata/c511002631.lua", rescue_cat), "another card's pre-errata variant")
        self.assertFalse(tied("pre-errata/c511002992.lua", sangan), "Rescue Cat's variant is not Sangan's")
        self.assertFalse(tied(f"goat/c504700178.lua", sangan), "not a folder that qualifies")
        self.assertFalse(tied(f"official/c{sangan + 1}.lua", sangan + 1), "no such file at the pin")

    def test_the_repositorys_agpl_text_is_ignis_copying(self):
        self.assertEqual(
            (self.cardscripts / "COPYING").read_bytes(),
            (REPO_ROOT / "LICENSES" / "AGPL-3.0-or-later.txt").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
