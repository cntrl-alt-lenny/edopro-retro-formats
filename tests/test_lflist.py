"""Unit tests for lflist generation: parsing, hashing, override mapping, determinism."""

from __future__ import annotations

import unittest

from retroformats.lflist import build_lflist, lflist_hash, parse_lflist
from retroformats.repo import Repository

from .helpers import TempRepoTest, card, change


class ParseAndHashTest(unittest.TestCase):
    def test_parse_round_trip(self):
        text = "#[X]\n!X\n$whitelist\n#forbidden\n100 0 --A\n200 1 --B\n300 3 --C\n"
        self.assertEqual({"X": {100: 0, 200: 1, 300: 3}}, parse_lflist(text))

    def test_parse_multiple_lists_and_junk(self):
        text = "ignored 1\n!A\n1 0\n!B\n2 2 trailing junk\nnot-a-code x\n"
        self.assertEqual({"A": {1: 0}, "B": {2: 2}}, parse_lflist(text))

    def test_hash_is_order_independent(self):
        a = lflist_hash({100: 0, 200: 1, 300: 3})
        b = lflist_hash(dict(reversed(list({100: 0, 200: 1, 300: 3}.items()))))
        self.assertEqual(a, b)

    def test_hash_differs_on_count_change(self):
        self.assertNotEqual(lflist_hash({100: 0}), lflist_hash({100: 1}))


class WhitelistBuildTest(TempRepoTest):
    def _seed(self):
        self.add_card_index(
            [
                card(100, "Alpha"),
                card(101, "Alpha", alias_of=100),
                card(200, "Beta"),
                card(300, "Gamma"),
                card(510000000, "Beta (Pre-Errata)", alias_of=200, ot=8),
            ]
        )
        self.add_banlist(
            entries=[
                {"card": card(200, "Beta"), "status": "limited"},
                {"card": card(300, "Gamma"), "status": "forbidden"},
            ]
        )
        self.add_pool(
            cards=[
                card(100, "Alpha", variant_passcodes=[101]),
                card(200, "Beta"),
                card(300, "Gamma"),
            ]
        )
        self.add_rule_profile()
        self.add_erratum(
            id="erratum-beta",
            modern=card(200, "Beta"),
            changes=[change(date="2010-01-01", summary="nerfed")],
        )
        self.add_format()

    def test_override_replaces_modern_code_and_variants_are_emitted(self):
        self._seed()
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        # Beta's erratum post-dates the 2005 snapshot -> historical code, limited.
        # Alpha unlimited with artwork variant. Gamma forbidden, pinned at 0.
        self.assertEqual(
            {100: 3, 101: 3, 510000000: 1, 300: 0},
            built.entries,
        )
        self.assertNotIn(200, built.entries)  # modern Beta must NOT be legal
        parsed = parse_lflist(built.text)
        self.assertEqual({"Retro 2005-04-test": built.entries}, parsed)
        self.assertIn("$whitelist", built.text)

    def test_erratum_dated_before_snapshot_does_not_apply(self):
        self._seed()
        # Move the format after the erratum date: modern text applies.
        self.add_format(period={"start": "2011-01-01", "end": None, "snapshot": "2011-01-01"},
                        id="2005-04-test")
        # keep banlist in force
        self.add_banlist(effective_date="2005-04-01")
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)
        self.assertNotIn(510000000, built.entries)

    def test_explicit_exclude_wins_over_include(self):
        self._seed()
        self.add_format(
            errata_overrides={"include": ["erratum-beta"], "exclude": ["erratum-beta"]},
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)

    def test_build_is_deterministic(self):
        self._seed()
        repo = Repository.load(self.root)
        fmt = repo.formats["2005-04-test"]
        self.assertEqual(build_lflist(fmt, repo).text, build_lflist(fmt, repo).text)

    def test_banlist_only_build_for_cutoff_pools(self):
        self._seed()
        self.add_pool(
            id="pool-test",
            kind="release-cutoff",
            cards=[],
            cutoff={"cutoff_date": "2005-04-01"},
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertNotIn("$whitelist", built.text)
        self.assertEqual({300: 0, 200: 1}, built.entries)


if __name__ == "__main__":
    unittest.main()
