"""Unit tests for the TCG release importer's pure normalisation logic.

No network, no real cache: tiny synthetic source structures exercising the
rules documented in retroformats/importers/tcg_releases.py.
"""

from __future__ import annotations

import unittest

from retroformats.importers.tcg_releases import (
    SRC_YGOPRODECK,
    SRC_YUGIPEDIA,
    build_products,
    canonical_passcode,
    parse_smw_raw,
    product_kind,
)


def cdb_row(name, alias=0, ot=3):
    return {"name": name, "alias": alias, "ot": ot, "desc": ""}


def ygo_card(cid, name, sets, images=None, ctype="Effect Monster"):
    return {
        "id": cid,
        "name": name,
        "type": ctype,
        "card_sets": [{"set_name": s, "set_code": c} for s, c in sets],
        "card_images": [{"id": i} for i in (images or [cid])],
    }


def smw(title, printouts):
    return {title: {"printouts": printouts}}


def date_value(raw):
    return [{"timestamp": "0", "raw": raw}]


class ParseSmwRawTest(unittest.TestCase):
    def test_day_month_year_precision(self):
        self.assertEqual(("2010-02-16", "day"), parse_smw_raw("1/2010/2/16"))
        self.assertEqual(("2002-12-01", "month"), parse_smw_raw("1/2002/12"))
        self.assertEqual(("2010-01-01", "year"), parse_smw_raw("1/2010"))

    def test_invalid_forms_return_none(self):
        self.assertIsNone(parse_smw_raw(""))
        self.assertIsNone(parse_smw_raw("2/2010/1/1"))  # non-Gregorian calendar model
        self.assertIsNone(parse_smw_raw("1/2010/13"))


class CanonicalPasscodeTest(unittest.TestCase):
    def test_prefers_alias_zero_base_from_images(self):
        # Dark Magician pattern: top-level id is an alt art; base sits in card_images.
        cdb = {46986420: cdb_row("Dark Magician", alias=46986414),
               46986414: cdb_row("Dark Magician")}
        card = ygo_card(46986420, "Dark Magician", [], images=[46986420, 46986414])
        self.assertEqual(46986414, canonical_passcode(card, cdb))

    def test_near_alias_resolves_to_base_not_in_dump(self):
        cdb = {101: cdb_row("Alpha", alias=100), 100: cdb_row("Alpha")}
        card = ygo_card(101, "Alpha", [], images=[101])
        self.assertEqual(100, canonical_passcode(card, cdb))

    def test_far_alias_is_its_own_card(self):
        cdb = {295517: cdb_row("A Legendary Ocean", alias=22702055),
               22702055: cdb_row("Umi")}
        card = ygo_card(295517, "A Legendary Ocean", [])
        self.assertEqual(295517, canonical_passcode(card, cdb))

    def test_unmatched_returns_none(self):
        self.assertIsNone(canonical_passcode(ygo_card(999, "Ghost", []), {}))


class ProductKindTest(unittest.TestCase):
    def test_mappings(self):
        self.assertEqual("promo-tournament", product_kind("Shonen Jump Championship 2009 Prize Card", None))
        self.assertEqual("promo-subscription", product_kind("Shonen Jump Vol. 8, Issue 3 promotional card", None))
        self.assertEqual("tin", product_kind("Collectible Tins 2008 Wave 1", None))
        self.assertEqual("booster", product_kind("Absolute Powerforce", "Booster pack"))
        self.assertEqual("structure", product_kind("Machina Mayhem Structure Deck", "Structure Deck"))


class BuildProductsTest(unittest.TestCase):
    CDB = {
        100: cdb_row("Alpha"),
        200: cdb_row("Beta"),
        300: cdb_row("Gamma"),
    }

    def cache(self, sets, cards, yugipedia_results):
        return {
            "sets": sets,
            "cards": cards,
            "yugipedia": {"en": yugipedia_results},
            "manifest": {},
        }

    def test_yugipedia_dates_govern_with_regional_split(self):
        cache = self.cache(
            sets=[{"set_name": "Test Set", "set_code": "TST", "tcg_date": "2005-01-05"}],
            cards=[ygo_card(100, "Alpha", [("Test Set", "TST-EN001")])],
            yugipedia_results=smw("Test Set", {
                "North American English release date": date_value("1/2005/1/10"),
                "European English release date": date_value("1/2005/1/5"),
                "English set prefix": ["TST"],
                "Set type": [{"fulltext": "Booster pack"}],
            }),
        )
        records, report = build_products(cache, self.CDB, "2010-12-31")
        (record,) = records
        by_territory = {e["territory"]: e for e in record["release_events"]}
        self.assertEqual({"tcg-na", "tcg-eu"}, set(by_territory))
        self.assertEqual("2005-01-10", by_territory["tcg-na"]["date"])
        # ygoprodeck's date equals the EU date -> corroborates that event only
        self.assertIn(SRC_YGOPRODECK, by_territory["tcg-eu"]["sources"])
        self.assertNotIn(SRC_YGOPRODECK, by_territory["tcg-na"]["sources"])
        self.assertEqual([], report["date_discrepancies"])
        self.assertEqual([{"passcode": 100, "name": "Alpha", "numbers": ["TST-EN001"]}],
                         record["printings"])

    def test_ygoprodeck_only_product_falls_back_to_umbrella_tcg(self):
        cache = self.cache(
            sets=[{"set_name": "Orphan Set", "set_code": "ORP", "tcg_date": "2006-06-06"}],
            cards=[], yugipedia_results={},
        )
        (record,), _ = build_products(cache, self.CDB, "2010-12-31")
        (event,) = record["release_events"]
        self.assertEqual(("tcg", "2006-06-06", [SRC_YGOPRODECK]),
                         (event["territory"], event["date"], event["sources"]))

    def test_date_discrepancy_is_reported_not_encoded(self):
        cache = self.cache(
            sets=[{"set_name": "Test Set", "set_code": "TST", "tcg_date": "2005-02-01"}],
            cards=[],
            yugipedia_results=smw("Test Set", {
                "North American English release date": date_value("1/2005/1/10"),
            }),
        )
        (record,), report = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual(1, len(record["release_events"]))  # only the Yugipedia event
        self.assertEqual(1, len(report["date_discrepancies"]))

    def test_coarse_precision_padded_match_is_not_corroboration(self):
        # Yugipedia says "May 2010" (month precision, padded to 2010-05-01);
        # YGOPRODeck says 2010-05-01. That is consistent, but it must neither
        # add YGOPRODeck as a corroborating source nor report a discrepancy.
        cache = self.cache(
            sets=[{"set_name": "Vague Set", "set_code": "VAG", "tcg_date": "2010-05-01"}],
            cards=[],
            yugipedia_results=smw("Vague Set", {
                "North American English release date": date_value("1/2010/5"),
            }),
        )
        (record,), report = build_products(cache, self.CDB, "2010-12-31")
        (ev,) = record["release_events"]
        self.assertEqual("month", ev["precision"])
        self.assertEqual([SRC_YUGIPEDIA], ev["sources"])
        self.assertEqual([], report["date_discrepancies"])

    def test_year_precision_product_spanning_window_start_is_kept(self):
        # padded "2002" starts 2002-01-01, before the TCG's 2002-03 launch;
        # the pre-TCG skip must use the latest possible date, not the padding.
        cache = self.cache(
            sets=[{"set_name": "Vague 2002", "set_code": "V02", "tcg_date": "2002-06-01"}],
            cards=[],
            yugipedia_results=smw("Vague 2002", {
                "North American English release date": date_value("1/2002"),
            }),
        )
        records, report = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual(["vague-2002"], [r["id"] for r in records])
        self.assertEqual([], report["skipped_products"])

    def test_sneak_peek_distribution_is_kind_event(self):
        cache = self.cache(
            sets=[{"set_name": "Test Set Sneak Peek Participation Card", "set_code": "TST",
                   "tcg_date": "2005-01-01"}],
            cards=[], yugipedia_results={},
        )
        (record,), _ = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual("event", record["release_events"][0]["kind"])

    def test_unmatched_yugipedia_products_are_reported(self):
        cache = self.cache(
            sets=[],
            cards=[],
            yugipedia_results=smw("Ghost Product", {
                "North American English release date": date_value("1/2005/1/10"),
            }),
        )
        _, report = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual(["Ghost Product"], report["yugipedia_only_products"])

    def test_window_filtering(self):
        cache = self.cache(
            sets=[
                {"set_name": "Too New", "set_code": "NEW", "tcg_date": "2011-01-01"},
                {"set_name": "Pre TCG", "set_code": "OLD", "tcg_date": "2001-01-01"},
                {"set_name": "In Window", "set_code": "IN", "tcg_date": "2005-01-01"},
            ],
            cards=[], yugipedia_results={},
        )
        records, report = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual(["in-window"], [r["id"] for r in records])
        self.assertEqual([{"product": "Pre TCG", "reason": "predates the TCG (2001-01-01)"}],
                         report["skipped_products"])

    def test_tokens_and_unmatched_cards_are_reported_not_guessed(self):
        cache = self.cache(
            sets=[{"set_name": "Test Set", "set_code": "TST", "tcg_date": "2005-01-05"}],
            cards=[
                ygo_card(100, "Alpha Token", [("Test Set", "TST-EN050")], ctype="Token"),
                ygo_card(999, "Ghost", [("Test Set", "TST-EN051")]),
            ],
            yugipedia_results={},
        )
        (record,), report = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual([], record["printings"])
        self.assertEqual(1, report["non_playable_skipped"])
        self.assertEqual(1, len(report["unmatched_cards"]))

    def test_reprint_rows_merge_numbers(self):
        cache = self.cache(
            sets=[{"set_name": "Test Set", "set_code": "TST", "tcg_date": "2005-01-05"}],
            cards=[ygo_card(100, "Alpha", [("Test Set", "TST-EN001"), ("Test Set", "TST-ENSE1")])],
            yugipedia_results={},
        )
        (record,), _ = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual([{"passcode": 100, "name": "Alpha", "numbers": ["TST-EN001", "TST-ENSE1"]}],
                         record["printings"])

    def test_output_is_deterministic(self):
        cache = self.cache(
            sets=[
                {"set_name": "B Set", "set_code": "BBB", "tcg_date": "2005-01-05"},
                {"set_name": "A Set", "set_code": "AAA", "tcg_date": "2004-01-05"},
            ],
            cards=[ygo_card(100, "Alpha", [("B Set", "BBB-EN001"), ("A Set", "AAA-EN001")])],
            yugipedia_results={},
        )
        first, _ = build_products(cache, self.CDB, "2010-12-31")
        second, _ = build_products(cache, self.CDB, "2010-12-31")
        self.assertEqual(first, second)
        self.assertEqual(["a-set", "b-set"], [r["id"] for r in first])


if __name__ == "__main__":
    unittest.main()
