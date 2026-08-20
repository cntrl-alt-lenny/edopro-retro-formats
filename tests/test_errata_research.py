"""Unit tests for the errata research normaliser's parsing layers."""

from __future__ import annotations

import unittest

from retroformats.importers.errata_research import (
    best_match,
    clean_lore,
    find_templates,
    parse_caption,
    parse_errata_tables,
    parse_smw_raw,
    template_params,
)

SAMPLE = """{{Navigation}}

== English ==
{{Errata table
| lore0  = When this card is sent to the Graveyard, <del>move</del> 1 monster.
| image0 = X-MRD.jpg
| cap0   = [[MRD-069]]<br />[[Metal Raiders]]

| lore1  = When this card is sent to the Graveyard, <del><ins>select</ins></del> 1 monster.
| image1 = X-SYE.jpg
| cap1   = [[SYE-018]]<br />[[Starter Deck: Yugi Evolution]]

| lore2  = When this card is sent to the Graveyard<ins>:</ins> <ins>add</ins> 1 monster.
| image2 = X-LC.png
| cap2   = [[MRD-069]]<br />[[Metal Raiders]]<br />''[[Legendary Collection]]''
}}

== Japanese ==
{{Errata table|lang=ja
| lore0  = このカード{{Ruby|墓|はか}}地<hr style="x"/><p>attack 1000</p>
| image0 = X-JP.jpg
| cap0   = [[Vol.6]]
}}
"""


class WikitextParsingTest(unittest.TestCase):
    def test_language_sections_and_tables(self):
        tables = parse_errata_tables(SAMPLE)
        self.assertEqual({"English", "Japanese"}, set(tables))
        self.assertEqual(3, len(tables["English"]))

    def test_diff_markup_content_is_kept(self):
        tables = parse_errata_tables(SAMPLE)
        v0, v1, v2 = tables["English"]
        self.assertEqual("When this card is sent to the Graveyard, move 1 monster.", v0["text"])
        # <del><ins>...</ins></del> marks text added in THIS version and
        # removed in the next - it IS part of this version's text.
        self.assertEqual("When this card is sent to the Graveyard, select 1 monster.", v1["text"])
        self.assertEqual("When this card is sent to the Graveyard: add 1 monster.", v2["text"])

    def test_caption_number_and_dating_set(self):
        tables = parse_errata_tables(SAMPLE)
        v0, _, v2 = tables["English"]
        self.assertEqual("MRD-069", v0["number"])
        self.assertEqual("Metal Raiders", v0["dating_set"])
        # A reprint caption's italic product link is the printing's real set.
        self.assertEqual(["Metal Raiders", "Legendary Collection"], v2["sets"])
        self.assertEqual("Legendary Collection", v2["dating_set"])

    def test_edition_qualifier_links_are_not_sets(self):
        cap = parse_caption("[[SDMM-EN003]]<br />[[Machina Mayhem Structure Deck]]<br />[[1st Edition]]")
        self.assertEqual("Machina Mayhem Structure Deck", cap["dating_set"])

    def test_ruby_and_layout_markup_stripped(self):
        tables = parse_errata_tables(SAMPLE)
        v0 = tables["Japanese"][0]
        self.assertEqual("このカード墓地", v0["text"])

    def test_nested_templates_do_not_break_param_split(self):
        params = template_params("Errata table|lang=ja|lore0=a{{Ruby|X|y}}b|cap0=[[A|B]]")
        self.assertEqual("a{{Ruby|X|y}}b", params["lore0"])
        self.assertEqual("[[A|B]]", params["cap0"])

    def test_find_templates_is_brace_balanced(self):
        bodies = find_templates("x {{Errata table|lore0={{Ruby|a|b}} c}} y", "Errata table")
        self.assertEqual(1, len(bodies))
        self.assertIn("{{Ruby|a|b}} c", bodies[0])


class SmwRawTest(unittest.TestCase):
    def test_precisions(self):
        self.assertEqual({"date": "2010-04-16", "precision": "day"}, parse_smw_raw("1/2010/4/16"))
        self.assertEqual({"date": "2010-04-01", "precision": "month"}, parse_smw_raw("1/2010/4"))
        self.assertEqual({"date": "2010-01-01", "precision": "year"}, parse_smw_raw("1/2010"))
        self.assertIsNone(parse_smw_raw("2/2010/4/16"))
        self.assertIsNone(parse_smw_raw(""))


class MatchingTest(unittest.TestCase):
    def test_exact_match_ignores_punctuation_and_case(self):
        versions = [{"index": 0, "text": "Destroy 1 monster; draw 1 card."}]
        match = best_match("destroy 1 monster draw 1 card", versions)
        self.assertTrue(match["exact"])
        self.assertEqual(0, match["index"])

    def test_fuzzy_match_reports_ratio(self):
        versions = [
            {"index": 0, "text": "Destroy one monster on the field."},
            {"index": 1, "text": "Completely unrelated text about tokens."},
        ]
        match = best_match("Destroy 1 monster on the field.", versions)
        self.assertEqual(0, match["index"])
        self.assertFalse(match["exact"])
        self.assertGreater(match["ratio"], 0.7)


if __name__ == "__main__":
    unittest.main()
