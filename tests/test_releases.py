"""Unit tests for the release subsystem: availability derivation, cutoff
evaluation, materialisation cross-checks, and the release validators.

These use synthetic mini-repositories (tests/helpers.py); the guarantees over
the repository's real Edison data live in test_repo_data.py.
"""

from __future__ import annotations

import unittest

from retroformats.lflist import build_lflist
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import TempRepoTest, card, event, printing

CUTOFF = "2005-06-01"


def validate(root):
    validator = Validator(Repository.load(root))
    validator.validate()
    return validator


def error_codes(validator):
    return {f.code for f in validator.errors}


def warning_codes(validator):
    return {f.code for f in validator.warnings}


class CutoffTest(TempRepoTest):
    """evaluate_cutoff over synthetic release data."""

    def evaluate(self, pool_id="pool-cut"):
        repo = Repository.load(self.root)
        return evaluate_cutoff(repo.pools[pool_id], repo)

    def seed_cards(self, *cards):
        self.add_card_index(list(cards))

    def test_card_released_before_cutoff_is_included(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha", "OLD-EN001")])
        self.add_cutoff_pool()
        result = self.evaluate()
        self.assertIn(100, result.included)

    def test_card_released_on_cutoff_day_is_included(self):
        # the cutoff is inclusive: "released <= cutoff_date"
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="EDGE", release_events=[event("tcg-na", CUTOFF)],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool()
        self.assertIn(100, self.evaluate().included)

    def test_card_released_after_cutoff_is_excluded(self):
        self.seed_cards(card(100, "Alpha"), card(200, "Beta"))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_product(code="NEW", release_events=[event("tcg-na", "2005-08-01")],
                         printings=[printing(200, "Beta")])
        self.add_cutoff_pool()
        result = self.evaluate()
        self.assertIn(100, result.included)
        self.assertNotIn(200, result.included)
        self.assertNotIn(200, result.ambiguous)

    def test_later_reprint_cannot_postdate_a_card(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2004-03-01")],
                         printings=[printing(100, "Alpha")])
        self.add_product(code="NEW", release_events=[event("tcg-na", "2009-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool()
        self.assertIn(100, self.evaluate().included)

    def test_ocg_only_availability_is_not_tcg_legal(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="OCGSET", release_events=[event("ocg", "2003-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool()
        result = self.evaluate()
        self.assertNotIn(100, result.included)
        self.assertNotIn(100, result.ambiguous)

    def test_europe_only_release_counts_for_default_tcg_scope(self):
        # Retro Pack situation: released only in Europe, still TCG-legal.
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="RP", release_events=[event("tcg-eu", "2005-03-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool()
        self.assertIn(100, self.evaluate().included)

    def test_na_scoped_pool_ignores_europe_only_release(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="RP", release_events=[event("tcg-eu", "2005-03-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(territories=["tcg-na"])
        result = self.evaluate()
        self.assertNotIn(100, result.included)

    def test_umbrella_tcg_event_satisfies_na_scope(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="OLD", release_events=[event("tcg", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(territories=["tcg-na"])
        self.assertIn(100, self.evaluate().included)

    def test_earliest_regional_date_wins(self):
        # EU got the set first; a cutoff between the two dates includes the card.
        self.seed_cards(card(100, "Alpha"))
        self.add_product(
            code="SPLIT",
            release_events=[event("tcg-eu", "2005-05-20"), event("tcg-na", "2005-06-10")],
            printings=[printing(100, "Alpha")],
        )
        self.add_cutoff_pool()  # cutoff 2005-06-01
        self.assertIn(100, self.evaluate().included)

    def test_prerelease_event_grants_no_availability(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(
            code="SNK",
            release_events=[
                event("tcg-na", "2005-05-28", kind="prerelease"),
                event("tcg-na", "2005-06-15"),
            ],
            printings=[printing(100, "Alpha")],
        )
        self.add_cutoff_pool()  # cutoff 2005-06-01: sneak peek before, retail after
        result = self.evaluate()
        self.assertNotIn(100, result.included)
        self.assertNotIn(100, result.ambiguous)

    def test_month_precision_straddling_cutoff_is_ambiguous(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="VAGUE", release_events=[event("tcg-na", "2005-06-01", precision="month")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool()  # cutoff 2005-06-01 falls inside June 2005
        result = self.evaluate()
        self.assertIn(100, result.ambiguous)
        self.assertNotIn(100, result.included)

    def test_month_precision_fully_before_cutoff_is_included(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="VAGUE", release_events=[event("tcg-na", "2005-04-01", precision="month")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool()
        self.assertIn(100, self.evaluate().included)

    def test_disputed_dates_straddling_cutoff_are_ambiguous(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(
            code="DISP",
            release_events=[
                event(
                    "tcg-na",
                    "2005-05-30",
                    status="disputed",
                    dispute=[{"date": "2005-06-03", "sources": ["test-source"], "note": "other source"}],
                )
            ],
            printings=[printing(100, "Alpha")],
        )
        self.add_cutoff_pool()
        self.assertIn(100, self.evaluate().ambiguous)

    def test_explicit_include_resolves_ambiguity(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="VAGUE", release_events=[event("tcg-na", "2005-06-01", precision="month")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(
            include=[{"card": card(100, "Alpha"), "reason": "documented in period", "sources": ["test-source"]}]
        )
        result = self.evaluate()
        self.assertIn(100, result.included)
        self.assertNotIn(100, result.ambiguous)
        self.assertIn(100, result.forced_in)

    def test_specific_event_satisfies_umbrella_scope(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(territories=["tcg"])
        self.assertIn(100, self.evaluate().included)

    def test_forced_include_variants_ignore_excluded_products(self):
        # A forced-in card must not whitelist an artwork variant whose only
        # printing is in a product this pool explicitly excludes.
        self.seed_cards(card(100, "Alpha"), card(101, "Alpha", alias_of=100))
        self.add_product(code="EXC", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(101, "Alpha")])
        self.add_cutoff_pool(
            include=[{"card": card(100, "Alpha"), "reason": "documented", "sources": ["test-source"]}],
            exclude_products=[{"product": "exc", "reason": "machine-only", "sources": ["test-source"]}],
        )
        result = self.evaluate()
        self.assertIn(100, result.included)
        self.assertNotIn("variant_passcodes", result.included[100])

    def test_excluded_product_grants_no_availability(self):
        # A product-level exclusion removes its events, but cards stay in the
        # pool when another (non-excluded) product released them in time.
        self.seed_cards(card(100, "Alpha"), card(200, "Beta"))
        self.add_product(code="MACH", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha"), printing(200, "Beta")])
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-02-01")],
                         printings=[printing(200, "Beta")])
        self.add_cutoff_pool(
            exclude_products=[{"product": "mach", "reason": "machine-only distribution",
                               "sources": ["test-source"]}]
        )
        result = self.evaluate()
        self.assertNotIn(100, result.included)
        self.assertIn(200, result.included)

    def test_explicit_exclude_overrides_derivation(self):
        self.seed_cards(card(100, "Alpha"))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(
            exclude=[{"card": card(100, "Alpha"), "reason": "recalled in period", "sources": ["test-source"]}]
        )
        result = self.evaluate()
        self.assertNotIn(100, result.included)
        self.assertIn(100, result.forced_out)

    def test_artwork_variant_accrues_to_base_card(self):
        self.seed_cards(card(100, "Alpha"), card(101, "Alpha", alias_of=100))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(101, "Alpha")])
        self.add_cutoff_pool()
        result = self.evaluate()
        self.assertIn(100, result.included)
        self.assertEqual([101], result.included[100].get("variant_passcodes"))

    def test_variant_printed_after_cutoff_is_not_emitted(self):
        self.seed_cards(card(100, "Alpha"), card(101, "Alpha", alias_of=100))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_product(code="ALT", release_events=[event("tcg-na", "2009-01-01")],
                         printings=[printing(101, "Alpha")])
        self.add_cutoff_pool()
        result = self.evaluate()
        self.assertIn(100, result.included)
        self.assertNotIn("variant_passcodes", result.included[100])

    def test_far_alias_is_its_own_canonical_card(self):
        # e.g. Harpie Lady 1 aliases Harpie Lady for name purposes; it is a
        # distinct physical card with its own release history.
        self.seed_cards(card(100, "Alpha"), card(5000, "Alpha One", alias_of=100))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(5000, "Alpha One")])
        self.add_cutoff_pool()
        result = self.evaluate()
        self.assertIn(5000, result.included)
        self.assertNotIn(100, result.included)

    def test_per_printing_product_dates_each_card_individually(self):
        self.seed_cards(card(100, "Alpha"), card(200, "Beta"), card(300, "Gamma"))
        self.add_product(
            code="JUMP",
            kind="promo-subscription",
            dating="per-printing",
            release_events=[],
            printings=[
                printing(100, "Alpha", "JUMP-EN001", release_events=[event("tcg-na", "2005-01-01")]),
                printing(200, "Beta", "JUMP-EN050", release_events=[event("tcg-na", "2009-01-01")]),
                # undated reprint: contributes nothing, harms nothing
                printing(300, "Gamma", "JUMP-EN002"),
            ],
        )
        self.add_product(code="OLD", release_events=[event("tcg-na", "2004-01-01")],
                         printings=[printing(300, "Gamma")])
        self.add_cutoff_pool()
        result = self.evaluate()
        self.assertIn(100, result.included)
        self.assertNotIn(200, result.included)
        self.assertIn(300, result.included)  # via OLD, not the undated promo

    def test_evaluation_is_deterministic(self):
        self.seed_cards(card(100, "Alpha"), card(200, "Beta"))
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha"), printing(200, "Beta")])
        self.add_cutoff_pool()
        first = self.evaluate().cards()
        second = self.evaluate().cards()
        self.assertEqual(first, second)
        self.assertEqual([100, 200], [c["passcode"] for c in first])


class CoverageTest(TempRepoTest):
    """ReleaseCoverage.covers() - the gate on pool materialisation."""

    def load_coverage(self):
        from retroformats.repo import Repository

        return Repository.load(self.root).release_coverage

    def test_covers_inside_complete_window(self):
        import datetime as dt

        self.add_coverage()
        cov = self.load_coverage()
        self.assertTrue(cov.covers(dt.date(2005, 6, 1), frozenset({"tcg-na"})))

    def test_does_not_cover_outside_window(self):
        import datetime as dt

        self.add_coverage()
        cov = self.load_coverage()
        self.assertFalse(cov.covers(dt.date(2011, 1, 1), frozenset({"tcg-na"})))
        self.assertFalse(cov.covers(dt.date(2001, 1, 1), frozenset({"tcg-na"})))

    def test_partial_window_does_not_count(self):
        import datetime as dt

        self.add_coverage(windows=[{"territories": ["tcg"], "from": "2002-01-01",
                                    "through": "2010-12-31", "status": "partial"}])
        self.assertFalse(self.load_coverage().covers(dt.date(2005, 6, 1), frozenset({"tcg"})))

    def test_umbrella_window_covers_family_scope(self):
        import datetime as dt

        self.add_coverage(windows=[{"territories": ["tcg"], "from": "2002-01-01",
                                    "through": "2010-12-31", "status": "complete"}])
        cov = self.load_coverage()
        self.assertTrue(cov.covers(dt.date(2005, 6, 1), frozenset({"tcg-na", "tcg-eu"})))
        self.assertFalse(cov.covers(dt.date(2005, 6, 1), frozenset({"ocg"})))


class ReleaseValidationTest(TempRepoTest):
    def _seed_valid(self):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta"), card(300, "Gamma")])
        self.add_banlist(entries=[{"card": card(200, "Beta"), "status": "limited"}])
        self.add_pool(cards=[card(100, "Alpha"), card(200, "Beta"), card(300, "Gamma")])
        self.add_rule_profile()
        self.add_format()

    def test_valid_product_produces_no_errors(self):
        self._seed_valid()
        self.add_product(printings=[printing(100, "Alpha", "SET1-EN001")])
        validator = validate(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_unknown_printing_passcode_fails(self):
        self._seed_valid()
        self.add_product(printings=[printing(999, "Ghost")])
        self.assertIn("card.unknown-passcode", error_codes(validate(self.root)))

    def test_printing_name_mismatch_fails(self):
        self._seed_valid()
        self.add_product(printings=[printing(100, "Wrong Name")])
        self.assertIn("card.name-mismatch", error_codes(validate(self.root)))

    def test_duplicate_printing_fails(self):
        self._seed_valid()
        self.add_product(printings=[printing(100, "Alpha"), printing(100, "Alpha")])
        self.assertIn("releases.duplicate-printing", error_codes(validate(self.root)))

    def test_bad_territory_fails(self):
        self._seed_valid()
        self.add_product(release_events=[event("mars", "2005-01-01")])
        self.assertIn("releases.bad-territory", error_codes(validate(self.root)))

    def test_disputed_event_without_alternatives_fails(self):
        self._seed_valid()
        self.add_product(release_events=[event("tcg-na", "2005-01-01", status="disputed")])
        self.assertIn("releases.dispute-missing", error_codes(validate(self.root)))

    def test_per_printing_product_with_product_events_fails(self):
        self._seed_valid()
        self.add_product(dating="per-printing", release_events=[event("tcg-na", "2005-01-01")])
        self.assertIn("releases.dating-conflict", error_codes(validate(self.root)))

    def test_unsourced_event_fails(self):
        self._seed_valid()
        self.add_product(release_events=[{"territory": "tcg-na", "date": "2005-01-01", "sources": []}])
        self.assertIn("sources.missing", error_codes(validate(self.root)))

    def test_fully_undated_card_warns(self):
        self._seed_valid()
        self.add_product(dating="per-printing", release_events=[],
                         printings=[printing(100, "Alpha", "SET1-EN001")])
        self.assertIn("releases.card-undated", warning_codes(validate(self.root)))

    def test_bad_dispute_precision_fails(self):
        self._seed_valid()
        self.add_product(release_events=[event(
            "tcg-na", "2005-01-01", status="disputed",
            dispute=[{"date": "2005-06-01", "precision": "montth", "sources": ["test-source"]}],
        )])
        self.assertIn("releases.bad-precision", error_codes(validate(self.root)))

    def test_bad_pool_region_fails(self):
        self._seed_valid()
        self.add_pool(id="pool-typo", cards=[card(100, "Alpha")], region="TGC")
        self.assertIn("pool.bad-region", error_codes(validate(self.root)))

    def test_unresolved_exclude_product_fails(self):
        self._seed_valid()
        self.add_product(printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(
            exclude_products=[{"product": "no-such-product", "reason": "typo", "sources": ["test-source"]}]
        )
        self.assertIn("pool.unresolved-product", error_codes(validate(self.root)))

    def test_noncanonical_exception_passcode_fails(self):
        self._seed_valid()
        self.add_card_index([card(100, "Alpha"), card(101, "Alpha", alias_of=100),
                             card(200, "Beta"), card(300, "Gamma")])
        self.add_cutoff_pool(
            include=[{"card": card(101, "Alpha"), "reason": "promo", "sources": ["test-source"]}]
        )
        self.assertIn("pool.exception-noncanonical", error_codes(validate(self.root)))

    def test_malformed_exception_entry_reports_without_crashing(self):
        self._seed_valid()
        self.add_cutoff_pool(include=["not-a-dict"])
        validator = validate(self.root)  # must not raise
        self.assertIn("pool.bad-exception", error_codes(validator))

    def test_bad_event_date_reports_without_crashing_despite_materialised_pool(self):
        # The validator's contract: every problem becomes a Finding, even when
        # a materialised pool would otherwise make it recompute over bad data.
        self._seed_valid()
        self.add_coverage()
        self.add_product(release_events=[event("tcg-na", "not-a-date")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        validator = validate(self.root)  # must not raise
        self.assertIn("releases.bad-date", error_codes(validator))
        self.assertIn("pool.not-cross-checked", warning_codes(validator))

    def test_cutoff_exception_without_sources_fails(self):
        self._seed_valid()
        self.add_coverage()
        self.add_product(printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(include=[{"card": card(300, "Gamma"), "reason": "promo"}])
        self.assertIn("pool.exception-unsourced", error_codes(validate(self.root)))


class MaterializedPoolValidationTest(TempRepoTest):
    def _seed(self, pool_cards=None, coverage=True, **cutoff_kw):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha", "OLD-EN001")])
        self.add_product(code="NEW", release_events=[event("tcg-na", "2009-01-01")],
                         printings=[printing(200, "Beta", "NEW-EN001")])
        if coverage:
            self.add_coverage()
        self.add_cutoff_pool(cards=pool_cards, **cutoff_kw)

    def test_correct_materialisation_passes(self):
        self._seed(pool_cards=[card(100, "Alpha")])
        validator = validate(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_stale_materialisation_fails(self):
        self._seed(pool_cards=[card(100, "Alpha"), card(200, "Beta")])
        self.assertIn("pool.materialization-drift", error_codes(validate(self.root)))

    def test_missing_card_in_materialisation_fails(self):
        self._seed(pool_cards=[])
        # empty list is falsy -> treated as unmaterialised; use a wrong list instead
        self._seed(pool_cards=[card(200, "Beta")])
        codes = error_codes(validate(self.root))
        self.assertIn("pool.materialization-drift", codes)

    def test_materialised_pool_without_coverage_fails(self):
        self._seed(pool_cards=[card(100, "Alpha")], coverage=False)
        self.assertIn("pool.no-coverage", error_codes(validate(self.root)))

    def test_variant_drift_fails(self):
        self.add_card_index([card(100, "Alpha"), card(101, "Alpha", alias_of=100), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha"), printing(101, "Alpha")])
        # committed entry lacks the derived variant 101
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        self.assertIn("pool.materialization-drift", error_codes(validate(self.root)))

    def test_exclude_resolves_straddling_ambiguity(self):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_product(code="VAGUE", release_events=[event("tcg-na", "2005-06-01", precision="month")],
                         printings=[printing(200, "Beta")])
        self.add_cutoff_pool(
            cards=[card(100, "Alpha")],
            exclude=[{"card": card(200, "Beta"), "reason": "documented as later", "sources": ["test-source"]}],
        )
        validator = validate(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_unresolved_ambiguity_fails_validation(self):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_product(code="VAGUE", release_events=[event("tcg-na", "2005-06-01", precision="month")],
                         printings=[printing(200, "Beta")])
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        self.assertIn("pool.cutoff-ambiguous", error_codes(validate(self.root)))

    def test_whitelist_is_built_from_materialised_cutoff_pool(self):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_product(code="NEW", release_events=[event("tcg-na", "2009-01-01")],
                         printings=[printing(200, "Beta")])
        self.add_banlist(entries=[{"card": card(100, "Alpha"), "status": "limited"}])
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        self.add_format(pool="pool-cut")
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn("$whitelist", built.text)
        self.assertEqual({100: 1}, built.entries)


class ReleaseIndexTest(TempRepoTest):
    def test_unknown_printing_is_reported_not_guessed(self):
        self.add_card_index([card(100, "Alpha")])
        self.add_product(printings=[printing(100, "Alpha"), printing(999, "Ghost")])
        index = ReleaseIndex.build(Repository.load(self.root))
        self.assertIn(100, index.by_canonical)
        self.assertNotIn(999, index.by_canonical)
        self.assertEqual([("set1", 999, "Ghost")], index.unknown_printings)


if __name__ == "__main__":
    unittest.main()
