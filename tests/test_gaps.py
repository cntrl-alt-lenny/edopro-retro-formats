"""The coverage-certification invariant: "complete" must be EARNED.

A coverage window's status flag alone never certifies a cutoff; the gap
ledger (data/releases/gaps.json) must show that no unresolved
pool-impacting gap could alter availability at that cutoff/scope, every
importer-detected anomaly must be accounted for, and resolutions must be
justified - mechanically recomputed where possible.
"""

from __future__ import annotations

import unittest

from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import TempRepoTest, card, event, gap, printing


def validate(root):
    validator = Validator(Repository.load(root))
    validator.validate()
    return validator


def error_codes(validator):
    return {f.code for f in validator.errors}


class GapCertificationTest(TempRepoTest):
    """A materialised pool exists; gaps decide whether coverage certifies."""

    def _seed(self, *gaps_records, pool_cards=None):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha", "OLD-EN001")])
        self.add_import_report()
        self.add_cutoff_pool(cards=pool_cards if pool_cards is not None else [card(100, "Alpha")])
        if gaps_records:
            self.add_gaps(*gaps_records)

    def test_unresolved_overlapping_gap_blocks_certification(self):
        # gap possibly from 2005-03-01 <= cutoff 2005-06-01 -> pool cannot certify
        self._seed(gap())
        codes = error_codes(validate(self.root))
        self.assertIn("pool.no-coverage", codes)
        self.assertIn("coverage.gap-unresolved", codes)

    def test_resolved_safe_gap_does_not_block(self):
        self._seed(gap(
            status="resolved-safe",
            resolution={
                "rationale": "no-playable-cards",
                "detail": "contains only tokens",
                "sources": ["test-source"],
            },
        ))
        validator = validate(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_gap_after_cutoff_does_not_block_earlier_format(self):
        # gap can only begin 2005-07-01, after the 2005-06-01 cutoff; the pool
        # certifies, but the coverage window claiming complete through
        # 2010-12-31 still cannot (the gap sits inside the window's claim).
        self._seed(gap(possible_from="2005-07-01"))
        codes = error_codes(validate(self.root))
        self.assertNotIn("pool.no-coverage", codes)
        self.assertIn("coverage.gap-unresolved", codes)

    def test_unrelated_territory_gap_does_not_block_scoped_pool(self):
        self.add_card_index([card(100, "Alpha")])
        self.add_rule_profile()
        self.add_coverage(windows=[{"territories": ["tcg-na"], "from": "2002-01-01",
                                    "through": "2010-12-31", "status": "complete"}])
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(cards=[card(100, "Alpha")], territories=["tcg-na"])
        self.add_gaps(gap(territories=["ocg"]))
        codes = error_codes(validate(self.root))
        self.assertNotIn("pool.no-coverage", codes)
        self.assertNotIn("coverage.gap-unresolved", codes)

    def test_eu_gap_blocks_all_tcg_scoped_pool(self):
        # default TCG scope counts EU availability, so an EU gap is relevant
        self._seed(gap(territories=["tcg-eu"]))
        self.assertIn("pool.no-coverage", error_codes(validate(self.root)))

    def test_resolution_requires_detail_and_sources(self):
        self._seed(gap(status="resolved-safe",
                       resolution={"rationale": "no-playable-cards", "detail": "", "sources": []}))
        self.assertIn("gaps.unjustified", error_codes(validate(self.root)))

    def test_unresolved_gap_must_not_carry_resolution(self):
        self._seed(gap(resolution={"rationale": "no-playable-cards", "detail": "x",
                                   "sources": ["test-source"]}))
        self.assertIn("gaps.resolution-unexpected", error_codes(validate(self.root)))

    def test_cards_available_earlier_is_recomputed_not_trusted(self):
        # Beta has NO earlier availability in the dataset, so claiming the gap
        # harmless via cards-available-earlier must fail mechanically.
        self._seed(gap(
            status="resolved-safe",
            resolution={
                "rationale": "cards-available-earlier",
                "detail": "Beta was already out (false claim)",
                "cards": [{"passcode": 200, "name": "Beta"}],
                "sources": ["test-source"],
            },
        ))
        self.assertIn("gaps.not-harmless", error_codes(validate(self.root)))

    def test_cards_available_earlier_passes_when_provable(self):
        # Alpha is provably available 2005-01-01 via OLD, before the gap's
        # 2005-03-01 earliest possible date.
        self._seed(gap(
            status="resolved-safe",
            resolution={
                "rationale": "cards-available-earlier",
                "detail": "Alpha shipped in OLD first",
                "cards": [{"passcode": 100, "name": "Alpha"}],
                "sources": ["test-source"],
            },
        ))
        validator = validate(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_cards_available_earlier_requires_cards(self):
        self._seed(gap(
            status="resolved-safe",
            resolution={"rationale": "cards-available-earlier",
                        "detail": "trust me", "sources": ["test-source"]},
        ))
        self.assertIn("gaps.unjustified", error_codes(validate(self.root)))

    def test_roster_imported_requires_existing_product_with_printings(self):
        self._seed(gap(
            status="resolved-imported",
            resolution={"rationale": "roster-imported", "detail": "imported",
                        "product": "no-such-product", "sources": ["test-source"]},
        ))
        self.assertIn("gaps.import-missing", error_codes(validate(self.root)))

    def test_roster_imported_with_real_product_passes(self):
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_product(code="REC", curated=True,
                         release_events=[event("tcg-na", "2005-02-01")],
                         printings=[printing(200, "Beta", "REC-EN001")])
        self.add_import_report(curated_covered_products=["Test Product REC"])
        self.add_cutoff_pool(cards=[card(100, "Alpha"), card(200, "Beta")])
        self.add_gaps(gap(
            subjects=["Test Product REC"],  # must name the recovering product
            status="resolved-imported",
            resolution={"rationale": "roster-imported", "detail": "recovered from set page",
                        "product": "rec", "sources": ["test-source"]},
        ))
        validator = validate(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_roster_imported_must_name_the_recovering_product(self):
        # pointing the resolution at an unrelated real product must fail
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_import_report()
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        self.add_gaps(gap(
            status="resolved-imported",
            resolution={"rationale": "roster-imported", "detail": "recovered",
                        "product": "old", "sources": ["test-source"]},
        ))
        self.assertIn("gaps.import-mismatch", error_codes(validate(self.root)))

    def test_provenance_only_gap_does_not_block(self):
        # provenance-only is legitimate only for kind 'other'
        self._seed(gap(kind="other", impact="provenance-only"))
        codes = error_codes(validate(self.root))
        self.assertNotIn("pool.no-coverage", codes)
        self.assertNotIn("coverage.gap-unresolved", codes)

    def test_provenance_only_cannot_launder_pool_kinds(self):
        # a missing-product gap is a pool-membership question by definition;
        # tagging it provenance-only must be rejected, not silently exempted
        self._seed(gap(impact="provenance-only"))
        self.assertIn("gaps.bad-impact", error_codes(validate(self.root)))

    def test_empty_territories_is_rejected_and_blocks_conservatively(self):
        self._seed(gap(territories=[]))
        codes = error_codes(validate(self.root))
        self.assertIn("gaps.no-territories", codes)
        self.assertIn("pool.no-coverage", codes)  # blocks() treats [] as everywhere

    def test_missing_import_report_blocks_certification(self):
        self.add_card_index([card(100, "Alpha")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_cutoff_pool(cards=[card(100, "Alpha")])  # no report written
        self.assertIn("coverage.no-import-report", error_codes(validate(self.root)))

    def test_stale_import_report_fails(self):
        self._seed()
        self.add_import_report(stats={"products_written": 99, "curated_preserved": 0})
        self.assertIn("coverage.report-stale", error_codes(validate(self.root)))

    def test_harmlessness_proof_is_territory_scoped(self):
        # Alpha is available early - but only in Europe; an NA gap cannot be
        # proven harmless by EU availability.
        self.add_card_index([card(100, "Alpha"), card(200, "Beta")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-eu", "2005-01-01")],
                         printings=[printing(100, "Alpha", "OLD-EN001")])
        self.add_import_report()
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        self.add_gaps(gap(
            territories=["tcg-na"],
            status="resolved-safe",
            resolution={"rationale": "cards-available-earlier", "detail": "EU-only proof",
                        "cards": [{"passcode": 100, "name": "Alpha"}], "sources": ["test-source"]},
        ))
        self.assertIn("gaps.not-harmless", error_codes(validate(self.root)))

    def test_variant_passcode_in_resolution_is_canonicalised(self):
        # citing the artwork variant (101) must not falsely block: availability
        # accrues to the base card (100).
        self.add_card_index([card(100, "Alpha"), card(101, "Alpha", alias_of=100)])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="OLD", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha", "OLD-EN001")])
        self.add_import_report()
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        self.add_gaps(gap(
            status="resolved-safe",
            resolution={"rationale": "cards-available-earlier", "detail": "variant cited",
                        "cards": [{"passcode": 101, "name": "Alpha"}], "sources": ["test-source"]},
        ))
        validator = validate(self.root)
        self.assertNotIn("gaps.not-harmless", error_codes(validator))

    def test_repackaging_bundle_cannot_precede_contents(self):
        self.add_card_index([card(100, "Alpha")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="BASE", release_events=[event("tcg-na", "2005-06-01")],
                         printings=[printing(100, "Alpha")])
        self.add_import_report()
        self.add_cutoff_pool(cutoff_date="2005-07-01", cards=[card(100, "Alpha")])
        self.add_gaps(gap(
            possible_from="2005-03-01",  # claims the bundle could predate its contents
            status="resolved-safe",
            resolution={"rationale": "repackaging-only", "detail": "bundle of BASE",
                        "products": ["base"], "sources": ["test-source"]},
        ))
        self.assertIn("gaps.not-harmless", error_codes(validate(self.root)))

    def test_repackaging_after_contents_passes(self):
        self.add_card_index([card(100, "Alpha")])
        self.add_rule_profile()
        self.add_coverage()
        self.add_product(code="BASE", release_events=[event("tcg-na", "2005-01-01")],
                         printings=[printing(100, "Alpha")])
        self.add_import_report()
        self.add_cutoff_pool(cards=[card(100, "Alpha")])
        self.add_gaps(gap(
            possible_from="2005-03-01",
            status="resolved-safe",
            resolution={"rationale": "repackaging-only", "detail": "bundle of BASE",
                        "products": ["base"], "sources": ["test-source"]},
        ))
        validator = validate(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_curated_covered_product_still_requires_a_gap_record(self):
        # a curated stub shrinking the yugipedia-only list must not erase the
        # anomaly: the report's curated_covered key still demands accounting
        self.add_card_index([card(100, "Alpha")])
        self.add_rule_profile()
        self.add_pool(cards=[card(100, "Alpha")])
        self.add_import_report(curated_covered_products=["Recovered Thing"])
        self.assertIn("gaps.unaccounted", error_codes(validate(self.root)))


class GapAccountingTest(TempRepoTest):
    """Every anomaly the importer detected must have a gap record."""

    def _seed(self):
        self.add_card_index([card(100, "Alpha")])
        self.add_rule_profile()
        self.add_pool(cards=[card(100, "Alpha")])

    def test_unaccounted_report_product_fails(self):
        self._seed()
        self.add_import_report(yugipedia_only_products=["Mystery Promo Set"])
        self.assertIn("gaps.unaccounted", error_codes(validate(self.root)))

    def test_accounted_report_product_passes(self):
        self._seed()
        self.add_import_report(yugipedia_only_products=["Mystery Promo Set"])
        self.add_gaps(gap(subjects=["Mystery Promo Set"]))
        self.assertNotIn("gaps.unaccounted", error_codes(validate(self.root)))

    def test_unaccounted_unmatched_card_fails(self):
        self._seed()
        self.add_import_report(unmatched_cards=[{"ygoprodeck_id": 1, "name": "Ghost", "sets": ["X"]}])
        self.assertIn("gaps.unaccounted", error_codes(validate(self.root)))

    def test_one_gap_can_account_for_many_subjects(self):
        self._seed()
        self.add_import_report(products_without_printings=["A", "B"])
        self.add_gaps(gap(subjects=["A", "B"]))
        self.assertNotIn("gaps.unaccounted", error_codes(validate(self.root)))


class GapCoversUnitTest(TempRepoTest):
    def test_covers_consults_gaps(self):
        import datetime as dt

        self.add_coverage()
        self.add_gaps(gap())
        repo = Repository.load(self.root)
        cov = repo.release_coverage
        day = dt.date(2005, 6, 1)
        scope = frozenset({"tcg-na"})
        self.assertTrue(cov.covers(day, scope))  # without gaps: window alone
        self.assertFalse(cov.covers(day, scope, repo.release_gaps))

    def test_gap_with_unparseable_date_blocks_conservatively(self):
        import datetime as dt

        self.add_coverage()
        self.add_gaps(gap(possible_from="not-a-date"))
        repo = Repository.load(self.root)
        self.assertFalse(
            repo.release_coverage.covers(dt.date(2005, 6, 1), frozenset({"tcg-na"}), repo.release_gaps)
        )


if __name__ == "__main__":
    unittest.main()
