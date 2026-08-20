"""Unit tests for the semantic validator, using synthetic mini-repositories."""

from __future__ import annotations

import unittest

from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import TempRepoTest, card


def run_validation(root):
    validator = Validator(Repository.load(root))
    validator.validate()
    return validator


def codes(validator):
    return {f.code for f in validator.findings}


def error_codes(validator):
    return {f.code for f in validator.errors}


class ValidRepoTest(TempRepoTest):
    def _seed_valid(self):
        self.add_card_index(
            [
                card(100, "Alpha"),
                card(101, "Alpha", alias_of=100),
                card(200, "Beta"),
                card(300, "Gamma"),
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
        self.add_format()

    def test_clean_repo_has_no_errors(self):
        self._seed_valid()
        validator = run_validation(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_unknown_source_reference_fails(self):
        self._seed_valid()
        self.add_pool(id="pool-test", cards=[card(100, "Alpha")], sources=["nope"])
        self.assertIn("sources.unresolved", error_codes(run_validation(self.root)))

    def test_card_name_mismatch_fails(self):
        self._seed_valid()
        self.add_banlist(entries=[{"card": card(200, "Wrong Name"), "status": "limited"}])
        self.assertIn("card.name-mismatch", error_codes(run_validation(self.root)))

    def test_unknown_passcode_fails(self):
        self._seed_valid()
        self.add_banlist(entries=[{"card": card(999, "Ghost"), "status": "limited"}])
        self.assertIn("card.unknown-passcode", error_codes(run_validation(self.root)))

    def test_duplicate_banlist_entry_fails(self):
        self._seed_valid()
        self.add_banlist(
            entries=[
                {"card": card(200, "Beta"), "status": "limited"},
                {"card": card(200, "Beta"), "status": "forbidden"},
            ]
        )
        self.assertIn("banlist.duplicate-card", error_codes(run_validation(self.root)))

    def test_banlist_not_yet_in_force_fails(self):
        self._seed_valid()
        self.add_banlist(effective_date="2005-06-01")  # after the format snapshot 2005-04-01
        self.assertIn("format.banlist-not-in-force", error_codes(run_validation(self.root)))

    def test_superseded_banlist_fails(self):
        self._seed_valid()
        self.add_banlist(superseded_by_date="2005-03-01")  # on/before snapshot
        self.assertIn("format.banlist-superseded", error_codes(run_validation(self.root)))

    def test_restricted_card_missing_from_pool_warns(self):
        self._seed_valid()
        self.add_pool(cards=[card(100, "Alpha", variant_passcodes=[101]), card(300, "Gamma")])
        validator = run_validation(self.root)
        self.assertIn("format.restricted-card-outside-pool", {f.code for f in validator.warnings})

    def test_variant_out_of_artwork_range_fails(self):
        self._seed_valid()
        self.add_card_index(
            [card(100, "Alpha"), card(200, "Beta"), card(300, "Gamma"), card(150, "Alpha", alias_of=100)]
        )
        self.add_pool(
            cards=[
                card(100, "Alpha", variant_passcodes=[150]),
                card(200, "Beta"),
                card(300, "Gamma"),
            ]
        )
        self.assertIn("pool.variant-out-of-range", error_codes(run_validation(self.root)))

    def test_composite_mode_macro_in_flags_fails(self):
        self._seed_valid()
        self.add_rule_profile(engine={"preset": "DUEL_MODE_MR1", "flags": ["DUEL_MODE_MR1"]})
        self.assertIn("rules.composite-flag", error_codes(run_validation(self.root)))

    def test_chronology_order_violation_fails(self):
        self._seed_valid()
        self.add_banlist(id="tcg-2004-10", effective_date="2004-10-01")
        self.add_pool(id="pool-older", cards=[card(100, "Alpha")])
        self.add_format(
            id="2004-10-older",
            banlist="tcg-2004-10",
            pool="pool-older",
            period={"start": "2004-10-01", "end": None, "snapshot": "2004-10-01"},
            chronology={"previous": "2005-04-test", "next": None},
        )
        self.assertIn("format.chronology-order", error_codes(run_validation(self.root)))

    def test_unresolved_reference_fails(self):
        self._seed_valid()
        self.add_format(banlist="tcg-9999-01")
        self.assertIn("format.unresolved-banlist", error_codes(run_validation(self.root)))

    def test_unreviewed_erratum_warns_but_does_not_block(self):
        self._seed_valid()
        self.add_erratum(
            id="erratum-alpha",
            modern=card(100, "Alpha"),
            impl={"strategy": "unresolved", "status": "missing"},
            review="imported",
        )
        validator = run_validation(self.root)
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))
        self.assertIn("erratum.unreviewed", {f.code for f in validator.warnings})

    def test_reviewed_undated_erratum_warns_and_ambiguity_blocks(self):
        self._seed_valid()
        self.add_erratum(
            id="erratum-alpha",
            modern=card(100, "Alpha"),
            impl={"strategy": "unresolved", "status": "missing"},
            review="reviewed",
        )
        validator = run_validation(self.root)
        self.assertIn("erratum.undated", {f.code for f in validator.warnings})
        # The format snapshot falls inside the (fully unknown) transition
        # interval; selection must refuse rather than guess.
        self.assertIn("format.erratum-ambiguous", error_codes(validator))


if __name__ == "__main__":
    unittest.main()
