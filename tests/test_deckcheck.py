"""Tests for the check-deck CLI subcommand (retroformats.deckcheck).

The most important test here is `test_checker_agrees_with_shipped_lists`:
it builds a deck directly from each format's OWN dist/lflists/*.lflist.conf
entries and confirms the checker reports it clean. That is the regression
that keeps this checker and the generated artifact from drifting apart -
see the module docstring in retroformats/deckcheck.py.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from retroformats.deckcheck import ParsedDeck, check_deck, parse_ydk
from retroformats.lflist import parse_lflist
from retroformats.repo import Repository

REPO_ROOT = Path(__file__).resolve().parents[1]
DECKS = Path(__file__).resolve().parent / "fixtures" / "decks"


class ParseYdkTest(unittest.TestCase):
    def test_main_extra_side_split(self):
        text = "#main\n100\n#extra\n200\n!side\n300\n"
        deck = parse_ydk(text)
        self.assertEqual((100,), deck.main)
        self.assertEqual((200,), deck.extra)
        self.assertEqual((300,), deck.side)

    def test_only_the_literal_hash_extra_line_switches_sections(self):
        # "#main" is not special-cased at all in the real client
        # (gframe/deck_manager.cpp:272-300) - it is just a comment, exactly
        # like "#created by ..."; lines before any marker default to main.
        text = "#created by someone\n100\n#main\n200\n"
        deck = parse_ydk(text)
        self.assertEqual((100, 200), deck.main)

    def test_any_bang_line_switches_to_side_not_just_bang_side(self):
        text = "#main\n100\n!whatever\n200\n"
        deck = parse_ydk(text)
        self.assertEqual((100,), deck.main)
        self.assertEqual((200,), deck.side)

    def test_crlf_and_blank_lines_are_tolerated(self):
        text = "#main\r\n100\r\n\r\n200\r\n#extra\r\n300\r\n"
        deck = parse_ydk(text)
        self.assertEqual((100, 200), deck.main)
        self.assertEqual((300,), deck.extra)

    def test_leading_digit_run_is_parsed_trailing_junk_ignored(self):
        # Mirrors std::stoul's leading-prefix parse (deck_manager.cpp:296-299):
        # a real .ydk never has trailing text, but the client would still
        # accept it, and a line with no LEADING digit is silently skipped.
        text = "#main\n  12345678 stray text\nnotanumber\n"
        deck = parse_ydk(text)
        self.assertEqual((12345678,), deck.main)

    def test_unparseable_and_comment_lines_are_skipped(self):
        text = "#main\n#just a comment\n\nabc\n100\n"
        deck = parse_ydk(text)
        self.assertEqual((100,), deck.main)


class CheckDeckFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(REPO_ROOT)
        cls.fmt = cls.repo.formats["2005-04-goat"]

    def _check(self, filename):
        text = (DECKS / filename).read_text(encoding="utf-8")
        deck = parse_ydk(text)
        return check_deck(deck, self.fmt, self.repo)

    def test_legal_deck_has_no_findings(self):
        result = self._check("goat_legal.ydk")
        self.assertEqual([], result.findings, msg=result.findings)
        self.assertTrue(result.legal)

    def test_overcount_is_flagged(self):
        result = self._check("goat_overcount.ydk")
        codes = {f.code for f in result.findings}
        self.assertIn("deck.overcount", codes)
        self.assertFalse(result.legal)

    def test_unlisted_card_is_flagged(self):
        result = self._check("goat_unlisted_card.ydk")
        codes = {f.code for f in result.findings}
        self.assertIn("deck.illegal-card", codes)

    def test_wrong_deck_size_is_flagged(self):
        result = self._check("goat_wrong_size.ydk")
        codes = {f.code for f in result.findings}
        self.assertIn("deck.bad-size", codes)

    def test_modern_instead_of_substituted_is_explained(self):
        result = self._check("goat_modern_instead_of_substituted.ydk")
        substituted = [f for f in result.findings if f.code == "deck.substituted-card"]
        self.assertEqual(1, len(substituted))
        # The explanation must name the legal historical passcode, not just
        # reject the modern one - that is the whole point of Part B.
        self.assertIn("504700000", substituted[0].message)

    def test_reverse_direction_historical_code_not_used_by_this_format(self):
        # 511003023 (Ultimate Offering, Pre-Errata) is a real BabelCDB
        # historical identity that GOAT's own reference does NOT whitelist
        # (see formats/2005-04-goat/notes.md on Ultimate Offering) - its
        # modern alias 80604091 IS legal here instead.
        result = self._check("goat_reverse_historical.ydk")
        findings = [f for f in result.findings if f.code == "deck.wrong-historical-identity"]
        self.assertEqual(1, len(findings))
        self.assertIn("80604091", findings[0].message)


class CheckerAgreesWithShippedListTest(unittest.TestCase):
    """The regression that matters most: build a deck straight from each
    format's own dist/lflists/<id>.lflist.conf entries (not from canonical
    data) and confirm the checker calls it clean. If the checker and
    build_lflist() ever disagree, this is what catches it."""

    def test_checker_agrees_with_shipped_lists(self):
        repo = Repository.load(REPO_ROOT)
        for fmt_id, fmt in repo.formats.items():
            with self.subTest(fmt_id=fmt_id):
                lflist_path = REPO_ROOT / "dist" / "lflists" / f"{fmt_id}.lflist.conf"
                text = lflist_path.read_text(encoding="utf-8")
                lists = parse_lflist(text)
                (entries,) = lists.values()
                client = (repo.rule_profiles[fmt.rule_profile_id].raw or {}).get("client", {}) or {}
                main_min = client["main_deck"][0]

                playable = sorted(code for code, count in entries.items() if count >= 1)
                main_codes: list[int] = []
                counts_used: dict[int, int] = {}
                for code in playable:
                    if len(main_codes) >= main_min:
                        break
                    key = repo.card_index.alias_of(code) or code
                    if counts_used.get(key, 0) >= entries[code]:
                        continue  # would collide with another code sharing its alias root
                    main_codes.append(code)
                    counts_used[key] = counts_used.get(key, 0) + 1
                self.assertEqual(main_min, len(main_codes), f"{fmt_id}: could not build a minimal legal deck")

                deck = ParsedDeck(main=tuple(main_codes), extra=(), side=())
                result = check_deck(deck, fmt, repo)
                self.assertEqual([], result.findings, msg=f"{fmt_id}: {result.findings}")


if __name__ == "__main__":
    unittest.main()
