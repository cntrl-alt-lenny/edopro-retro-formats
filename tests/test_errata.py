"""Unit tests for errata chronology, version selection, and fail-safe
applicability — the guarantees the historical-behaviour dataset makes.

Selection semantics under test (retroformats/model.py):
- a format snapshot BEFORE a change's effective chronology uses the old
  version; ON or AFTER the effective date it uses the new one;
- month/year-precise dates widen into intervals, bounded chronology uses
  attestation dates, and a snapshot inside any unresolved interval is
  AMBIGUOUS — selection refuses to guess;
- only functional and ruling changes are implementation-relevant; cosmetic
  and engine changes never substitute a historical passcode;
- multi-change cards select the version whose era contains the snapshot,
  including intermediate versions via resulting_implementation, and surface
  an implementation gap when the needed version has none.
"""

from __future__ import annotations

import datetime as _dt
import unittest
from pathlib import Path

from retroformats.lflist import ErrataSelectionError, build_lflist, select_applicable_errata
from retroformats.model import AMBIGUOUS, NEW, OLD, Erratum, change_state_at
from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import TempRepoTest, card, change, implementation


def erratum_of(**kw) -> Erratum:
    raw = {
        "id": kw.pop("id", "erratum-x"),
        "modern_card": kw.pop("modern_card", {"passcode": 200, "name": "Beta"}),
        "classification": kw.pop("classification", "functional"),
        "changes": kw.pop("changes"),
        "implementation": kw.pop(
            "implementation",
            {"strategy": "reuse-upstream", "historical_passcode": 510000000, "status": "complete"},
        ),
        "review": {"status": "reviewed"},
        "sources": ["test-source"],
    }
    raw.update(kw)
    return Erratum.load(raw, Path("x.json"))


def day(s: str) -> _dt.date:
    return _dt.date.fromisoformat(s)


class ChangeStateTest(unittest.TestCase):
    def test_day_precision_boundary(self):
        ch = change(date="2010-05-01")
        self.assertEqual(OLD, change_state_at(ch, day("2010-04-30")))
        # On the effective date itself the NEW behaviour applies.
        self.assertEqual(NEW, change_state_at(ch, day("2010-05-01")))
        self.assertEqual(NEW, change_state_at(ch, day("2010-05-02")))

    def test_month_precision_widens_to_interval(self):
        ch = change(date="2010-05-01", effective_precision="month")
        self.assertEqual(OLD, change_state_at(ch, day("2010-04-30")))
        self.assertEqual(AMBIGUOUS, change_state_at(ch, day("2010-05-15")))
        self.assertEqual(NEW, change_state_at(ch, day("2010-05-31")))

    def test_year_precision(self):
        ch = change(date="2012-01-01", effective_precision="year")
        self.assertEqual(OLD, change_state_at(ch, day("2011-12-31")))
        self.assertEqual(AMBIGUOUS, change_state_at(ch, day("2012-06-01")))
        self.assertEqual(NEW, change_state_at(ch, day("2012-12-31")))

    def test_bounded_chronology(self):
        ch = change(
            date=None,
            effective_old_attested_through="2008-09-02",
            effective_new_attested_from="2011-07-01",
        )
        self.assertEqual(OLD, change_state_at(ch, day("2008-09-02")))
        self.assertEqual(AMBIGUOUS, change_state_at(ch, day("2010-04-24")))
        self.assertEqual(NEW, change_state_at(ch, day("2011-07-01")))

    def test_unknown_chronology_is_always_ambiguous(self):
        ch = change(date=None)
        self.assertEqual(AMBIGUOUS, change_state_at(ch, day("1999-01-01")))
        self.assertEqual(AMBIGUOUS, change_state_at(ch, day("2030-01-01")))


class SelectionTest(unittest.TestCase):
    def test_dated_erratum_selects_historical_before_and_modern_after(self):
        e = erratum_of(changes=[change(date="2015-07-16")])
        before = e.selection_at(day("2010-04-24"))
        self.assertEqual("historical", before.state)
        self.assertEqual(510000000, before.implementation["historical_passcode"])
        self.assertEqual(0, before.version_index)
        on = e.selection_at(day("2015-07-16"))
        self.assertEqual("modern", on.state)
        after = e.selection_at(day("2020-01-01"))
        self.assertEqual("modern", after.state)

    def test_cosmetic_changes_never_substitute(self):
        e = erratum_of(
            classification="cosmetic",
            changes=[change(kind="cosmetic", date="2011-07-01")],
            implementation={"strategy": "none-needed", "status": "complete"},
        )
        self.assertEqual("modern", e.selection_at(day("2005-04-01")).state)

    def test_engine_changes_never_substitute(self):
        e = erratum_of(
            classification="engine",
            changes=[change(kind="engine", date="2008-03-01")],
            implementation={"strategy": "none-needed", "status": "complete"},
        )
        self.assertEqual("modern", e.selection_at(day("2005-04-01")).state)

    def test_mixed_kinds_only_relevant_changes_count(self):
        # A cosmetic PSCT rewording between two functional changes must not
        # create a phantom version boundary.
        e = erratum_of(
            changes=[
                change(kind="functional", date="2007-01-01"),
                change(kind="cosmetic", date="2011-07-01"),
                change(kind="functional", date="2015-07-16",
                       resulting_implementation=None),
            ],
        )
        # 2010: after change 1 (functional), cosmetic irrelevant, before the
        # 2015 functional change -> version 1, which has no recorded
        # implementation -> gap.
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("gap", sel.state)
        self.assertEqual(1, sel.version_index)

    def test_multiple_revisions_select_correct_version(self):
        v1_impl = implementation(historical_passcode=510000001)
        e = erratum_of(
            changes=[
                change(kind="functional", date="2007-01-01", resulting_implementation=v1_impl),
                change(kind="functional", date="2015-07-16"),
            ],
        )
        goat = e.selection_at(day("2005-04-01"))
        self.assertEqual("historical", goat.state)
        self.assertEqual(0, goat.version_index)
        self.assertEqual(510000000, goat.implementation["historical_passcode"])
        edison = e.selection_at(day("2010-04-24"))
        self.assertEqual("historical", edison.state)
        self.assertEqual(1, edison.version_index)
        self.assertEqual(510000001, edison.implementation["historical_passcode"])
        modern = e.selection_at(day("2016-01-01"))
        self.assertEqual("modern", modern.state)

    def test_ambiguous_chronology_blocks_selection(self):
        e = erratum_of(changes=[change(date="2010-04-01", effective_precision="month")])
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("ambiguous", sel.state)
        self.assertEqual((0,), sel.ambiguous_changes)

    def test_ambiguity_in_an_irrelevant_change_does_not_block(self):
        e = erratum_of(
            changes=[
                change(kind="cosmetic", date=None),
                change(kind="functional", date="2015-07-16"),
            ],
            classification="functional",
        )
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("historical", sel.state)

    def test_unresolved_strategy_is_a_gap(self):
        e = erratum_of(
            changes=[change(date="2015-07-16")],
            implementation={"strategy": "unresolved", "status": "missing"},
        )
        self.assertEqual("gap", e.selection_at(day("2010-04-24")).state)

    def test_none_needed_is_an_accepted_modern_stand_in(self):
        e = erratum_of(
            classification="ruling",
            changes=[change(kind="ruling", date="2011-07-01")],
            implementation={"strategy": "none-needed", "status": "complete"},
        )
        sel = e.selection_at(day("2005-04-01"))
        self.assertEqual("modern", sel.state)


class FormatSelectionTest(TempRepoTest):
    def _seed(self, **erratum_kw):
        self.add_card_index(
            [
                card(100, "Alpha"),
                card(200, "Beta"),
                card(300, "Gamma"),
                card(510000000, "Beta (Pre-Errata)", alias_of=200, ot=8),
                card(510000001, "Beta (Mid)", alias_of=200, ot=8),
            ]
        )
        self.add_banlist(entries=[{"card": card(200, "Beta"), "status": "limited"}])
        self.add_pool(cards=[card(100, "Alpha"), card(200, "Beta"), card(300, "Gamma")])
        self.add_rule_profile()
        self.add_erratum(**erratum_kw)
        self.add_format()

    def test_unreviewed_record_needs_explicit_include(self):
        self._seed(review="imported")
        repo = Repository.load(self.root)
        fmt = repo.formats["2005-04-test"]
        self.assertEqual({}, select_applicable_errata(fmt, repo))
        self.add_format(errata_overrides={"include": ["erratum-beta"], "exclude": []})
        repo = Repository.load(self.root)
        selected = select_applicable_errata(repo.formats["2005-04-test"], repo)
        self.assertEqual({200}, set(selected))

    def test_reviewed_ambiguous_record_fails_the_build(self):
        self._seed(review="reviewed")  # default change: no chronology at all
        repo = Repository.load(self.root)
        fmt = repo.formats["2005-04-test"]
        with self.assertRaises(ErrataSelectionError):
            build_lflist(fmt, repo)
        validator = Validator(repo)
        validator.validate()
        self.assertIn("format.erratum-ambiguous", {f.code for f in validator.errors})

    def test_reviewed_gap_fails_the_build_and_exclude_documents_it(self):
        self._seed(
            review="reviewed",
            changes=[change(date="2015-07-16")],
            impl={"strategy": "unresolved", "status": "missing"},
        )
        repo = Repository.load(self.root)
        with self.assertRaises(ErrataSelectionError):
            build_lflist(repo.formats["2005-04-test"], repo)
        self.add_format(errata_overrides={"include": [], "exclude": ["erratum-beta"]})
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)  # modern card stays, documented deviation

    def test_acknowledged_gap_keeps_modern_card_and_warns(self):
        # A behaviour we KNOW differs but cannot reproduce: the record must
        # say so explicitly. Then the format keeps the modern card, the
        # divergence is visible as a warning, and the build does not fail.
        self._seed(
            review="reviewed",
            changes=[change(date="2015-07-16")],
            impl={
                "strategy": "unresolved",
                "status": "missing",
                "gap": {
                    "reason": "Project Ignis ships no historical version of this card",
                    "upstream_checked": True,
                    "sources": ["test-source"],
                },
            },
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)  # modern card, knowingly
        validator = Validator(repo)
        validator.validate()
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))
        self.assertIn("format.erratum-known-divergence", {f.code for f in validator.warnings})

    def test_gap_acknowledgement_requires_reason_and_sources(self):
        self._seed(
            review="reviewed",
            changes=[change(date="2015-07-16")],
            impl={"strategy": "unresolved", "status": "missing", "gap": {"reason": "", "sources": []}},
        )
        validator = Validator(Repository.load(self.root))
        validator.validate()
        self.assertIn("erratum.gap-unjustified", {f.code for f in validator.errors})

    def test_gap_on_a_resolved_strategy_is_an_error(self):
        self._seed(
            review="reviewed",
            changes=[change(date="2015-07-16")],
            impl={
                "strategy": "reuse-upstream",
                "historical_passcode": 510000000,
                "status": "complete",
                "gap": {"reason": "x", "sources": ["test-source"]},
            },
        )
        validator = Validator(Repository.load(self.root))
        validator.validate()
        self.assertIn("erratum.gap-with-implementation", {f.code for f in validator.errors})

    def test_dated_boundary_governs_whitelist_substitution(self):
        self._seed(review="reviewed", changes=[change(date="2005-04-02")])
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)  # snapshot 04-01
        self.assertIn(510000000, built.entries)
        self.assertNotIn(200, built.entries)
        # Move the snapshot onto the effective date: modern applies.
        self.add_format(period={"start": "2005-04-02", "end": None, "snapshot": "2005-04-02"})
        self.add_banlist(effective_date="2005-04-01")
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)
        self.assertNotIn(510000000, built.entries)

    def test_modern_and_historical_are_never_both_legal(self):
        self._seed(review="reviewed", changes=[change(date="2015-07-16")])
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(510000000, built.entries)
        self.assertNotIn(200, built.entries)
        self.assertEqual(1, built.entries[510000000])  # banlist count transfers

    def test_banlist_count_transfers_to_selected_intermediate_version(self):
        self._seed(
            review="reviewed",
            changes=[
                change(date="2004-01-01",
                       resulting_implementation=implementation(historical_passcode=510000001)),
                change(date="2015-07-16"),
            ],
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        # Snapshot 2005-04-01 is between the two changes: version 1 applies.
        self.assertIn(510000001, built.entries)
        self.assertEqual(1, built.entries[510000001])
        self.assertNotIn(510000000, built.entries)
        self.assertNotIn(200, built.entries)

    def test_historical_version_does_not_survive_after_its_era(self):
        self._seed(review="reviewed", changes=[change(date="2005-01-01")])
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)  # snapshot after erratum
        self.assertIn(200, built.entries)
        self.assertNotIn(510000000, built.entries)


class FormatValidationTest(TempRepoTest):
    def _seed(self, **erratum_kw):
        self.add_card_index(
            [
                card(100, "Alpha"),
                card(200, "Beta"),
                card(300, "Gamma"),
                card(510000000, "Beta (Pre-Errata)", alias_of=200, ot=8),
            ]
        )
        self.add_banlist(entries=[{"card": card(200, "Beta"), "status": "limited"}])
        self.add_pool(cards=[card(100, "Alpha"), card(200, "Beta"), card(300, "Gamma")])
        self.add_rule_profile()
        self.add_erratum(**erratum_kw)

    def _validator(self):
        validator = Validator(Repository.load(self.root))
        validator.validate()
        return validator

    def test_cosmetic_record_with_substitution_warns_and_never_computes(self):
        self._seed(
            classification="cosmetic",
            changes=[change(kind="cosmetic", date="2011-07-01")],
        )
        self.add_format()
        v = self._validator()
        self.assertIn(
            "erratum.no-behavioural-change-with-override", {f.code for f in v.warnings}
        )
        # Computed selection must never substitute it - only an explicit
        # include can (reference-parity for period-text variants).
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)
        self.assertNotIn(510000000, built.entries)
        self.add_format(errata_overrides={"include": ["erratum-beta"], "exclude": []})
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(510000000, built.entries)
        self.assertNotIn(200, built.entries)

    def test_engine_record_with_substitution_warns_and_never_computes(self):
        self._seed(
            classification="engine",
            changes=[change(kind="engine", date="2008-03-01")],
        )
        self.add_format()
        v = self._validator()
        self.assertIn(
            "erratum.no-behavioural-change-with-override", {f.code for f in v.warnings}
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)
        self.assertNotIn(510000000, built.entries)

    def test_classification_must_match_dominant_kind(self):
        self._seed(
            classification="cosmetic",
            changes=[change(kind="functional", date="2015-07-16")],
        )
        self.add_format()
        v = self._validator()
        self.assertIn("erratum.classification-mismatch", {f.code for f in v.errors})

    def test_inverted_attestation_bounds_fail(self):
        self._seed(
            changes=[
                change(
                    date=None,
                    effective_old_attested_through="2012-01-01",
                    effective_new_attested_from="2011-01-01",
                )
            ]
        )
        self.add_format(errata_overrides={"include": ["erratum-beta"], "exclude": []})
        v = self._validator()
        self.assertIn("erratum.bounds-inverted", {f.code for f in v.errors})

    def test_bounds_contradicting_date_fail(self):
        self._seed(
            changes=[
                change(
                    date="2011-01-01",
                    effective_old_attested_through="2012-01-01",
                )
            ]
        )
        self.add_format(errata_overrides={"include": ["erratum-beta"], "exclude": []})
        v = self._validator()
        self.assertIn("erratum.bounds-contradict-date", {f.code for f in v.errors})

    def test_changes_must_be_ordered_oldest_to_newest(self):
        self._seed(
            changes=[
                change(kind="functional", date="2015-01-01"),
                change(kind="functional", date="2007-01-01"),
            ]
        )
        self.add_format()
        v = self._validator()
        self.assertIn("erratum.changes-out-of-order", {f.code for f in v.errors})

    def test_final_change_must_not_record_an_implementation(self):
        self._seed(
            changes=[
                change(date="2015-01-01",
                       resulting_implementation=implementation(historical_passcode=510000000)),
            ]
        )
        self.add_format()
        v = self._validator()
        self.assertIn("erratum.modern-implementation-recorded", {f.code for f in v.errors})

    def test_alias_mismatch_is_an_error(self):
        self._seed(modern=card(100, "Alpha"), id="erratum-alpha")
        # historical 510000000 aliases 200 (Beta), not Alpha.
        self.add_format()
        v = self._validator()
        self.assertIn("erratum.alias-mismatch", {f.code for f in v.errors})

    def test_unindexed_historical_passcode_warns(self):
        self._seed(impl=implementation(historical_passcode=599999999))
        self.add_format(errata_overrides={"include": [], "exclude": ["erratum-beta"]})
        v = self._validator()
        self.assertIn("erratum.historical-passcode-unindexed", {f.code for f in v.warnings})

    def test_include_contradicting_chronology_warns(self):
        self._seed(changes=[change(date="2004-01-01")])  # modern by 2005-04-01
        self.add_format(errata_overrides={"include": ["erratum-beta"], "exclude": []})
        v = self._validator()
        self.assertIn(
            "format.erratum-include-contradicts-chronology", {f.code for f in v.warnings}
        )

    def test_redundant_include_warns(self):
        self._seed(changes=[change(date="2015-07-16")])
        self.add_format(errata_overrides={"include": ["erratum-beta"], "exclude": []})
        v = self._validator()
        self.assertIn("format.erratum-include-redundant", {f.code for f in v.warnings})


if __name__ == "__main__":
    unittest.main()
