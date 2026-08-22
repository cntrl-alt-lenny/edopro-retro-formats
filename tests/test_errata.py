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


class OrderingConstraintTest(unittest.TestCase):
    """selection_at() computes a candidate *range* from the per-change
    OLD/AMBIGUOUS/NEW states via two aggregate counts (definite_new,
    definite_old), not by propagating each change's definite state to its
    neighbours. schemas/erratum.schema.json documents changes[] as "Ordered
    oldest-to-newest", which would license propagation IF a given pair of
    changes really is a validated chain: in a genuine chronological chain,
    an earlier change confirmed OLD (hasn't happened) forces every later
    change to also be OLD, and a later change confirmed NEW (has happened)
    forces every earlier change to also be NEW.

    Two of the four two-change orderings below ([OLD, AMBIGUOUS] and
    [AMBIGUOUS, NEW]) are exactly where that propagation would narrow the
    candidate range *if* changes[] were a validated chain for the pair in
    question; the other two ([NEW, AMBIGUOUS] and [AMBIGUOUS, OLD]) already
    produce a valid, non-contradictory candidate set regardless of whether
    the pair is a genuine chain or two independent axes, because a change
    happening earlier (or a later change not yet happening) does not
    constrain a neighbour on the other side either way.

    IMPORTANT - these are characterization tests, not correctness tests for
    the numeric candidate labels. They pin down what selection_at() *does*
    today; they do NOT establish that a given candidate index correctly
    represents any particular joint historical state, and they do NOT
    establish that any real multi-change record is a validated chain merely
    because changes[] lists two changes in some order. changes[] list order
    is not evidence of a real chronological relationship - it is exactly the
    representation this project's research documentation is investigating.
    Three real-record situations exist, and selection_at() cannot currently
    tell them apart:
    - a GENUINELY EVIDENCED CHAIN (all 41 divergence/B-partition records:
      every relevant change carries a real, specific effective.date, so the
      relative order is actually established, not merely listed) - here
      propagation would be safe if implemented, and the current output is
      either already correct (the [NEW, AMBIGUOUS] / [AMBIGUOUS, OLD]
      shapes) or would need genuine propagation to become correct (the
      [OLD, AMBIGUOUS] / [AMBIGUOUS, NEW] shapes);
    - a BUNDLED INDEPENDENT-AXIS pair (the 38-card failed-search/
      deck-verification cluster: each record's own review notes state its
      two changes are aspects of one ruling package, bundled in a single
      upstream script, and cannot be sequenced - Giant Rat, tested below, is
      one of 29 of the 38 with the [OLD, AMBIGUOUS] shape, where candidate 1
      is actively self-contradictory; 8 more plus Paladin of White Dragon
      list the same two axes in the opposite order and so do not exhibit a
      self-contradictory candidate at the Edison snapshot specifically,
      though the underlying independent-axis problem is identical) -
      propagation would be WRONG here: it would manufacture false certainty
      about which of two truly independent rulings had happened;
    - a MECHANICALLY-UNRELATED, ORDER-UNKNOWN pair (6 non-cluster-1 records
      in this project's known-wrong set - Axe of Despair, Tyrant Dragon,
      Vampire Lord, XY-/XYZ-/XZ- Dragon/Tank Cannon - each pairing one
      undated ruling with a separate, later, mechanically-unrelated dated
      erratum whose relative order is simply never evidenced, not merely
      unlisted) - propagation would ALSO be wrong here, for the same reason
      as the bundled case, even though these records are not "independent
      axes" in the bundled/substantive sense. Their candidate set happens to
      be non-contradictory at the Edison snapshot only because the dated
      member of each pair is confirmed not-yet-happened purely by its own
      far-future date, independent of any ordering fact; re-evaluated at a
      snapshot after that date, all 6 reproduce the identical
      self-contradictory-candidate symptom the bundled cluster shows at
      Edison - a snapshot-dependent coincidence, not evidence of a chain.

    This project deliberately does NOT patch selection_at() to propagate,
    because it cannot tell a genuinely evidenced chain apart from either
    kind of order-unresolved pair using changes[] alone. See
    docs/research/edison-behaviour-gaps.md (roadmap item 5c), "Selection-model
    ordering question" and "A/B/C/D partition"'s "The 6 non-cluster C records
    are NOT validated linear chains", for the full per-record analysis and
    the proposed (not yet chosen) data-model fix.
    """

    def test_earlier_definite_old_later_ambiguous_does_not_propagate(self):
        # [OLD, AMBIGUOUS] -- the Giant Rat shape. A true chain would force
        # change 1 to also be OLD (it cannot happen before change 0, which
        # is confirmed not to have happened yet), collapsing this to a
        # determinate historical version 0. Current selection_at instead
        # reports both 0 and 1, including a "candidate" (version 1) that
        # requires change 0 to be NEW -- directly contradicting change 0's
        # own definite OLD state at this snapshot.
        e = erratum_of(changes=[
            change(date=None, effective_old_attested_through="2011-02-02"),
            change(date=None),
        ])
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("ambiguous", sel.state)
        self.assertEqual((0, 1), sel.candidates)

    def test_earlier_ambiguous_later_definite_new_does_not_propagate(self):
        # [AMBIGUOUS, NEW] -- the mirror image. A true chain would force
        # change 0 to also be NEW (a later change cannot happen before an
        # earlier one), collapsing this to a determinate modern result.
        # Current selection_at instead reports both version 1 and modern.
        e = erratum_of(changes=[
            change(date=None),
            change(date=None, effective_new_attested_from="2005-01-01"),
        ])
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("ambiguous", sel.state)
        self.assertEqual((1, 2), sel.candidates)
        self.assertTrue(sel.modern_is_possible)

    def test_earlier_definite_new_later_ambiguous_is_already_correct(self):
        # [NEW, AMBIGUOUS] -- NOT a propagation gap. Change 0 having already
        # happened says nothing about whether change 1 also has; both
        # version 1 and modern are genuinely possible regardless of
        # chain-vs-independent-axis interpretation, matching current output.
        e = erratum_of(changes=[
            change(date=None, effective_new_attested_from="2005-01-01"),
            change(date=None),
        ])
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("ambiguous", sel.state)
        self.assertEqual((1, 2), sel.candidates)

    def test_earlier_ambiguous_later_definite_old_is_already_correct(self):
        # [AMBIGUOUS, OLD] -- also NOT a propagation gap. Change 1 not
        # having happened yet says nothing about whether change 0 already
        # has; both version 0 and version 1 are genuinely possible,
        # matching current output.
        e = erratum_of(changes=[
            change(date=None),
            change(date=None, effective_old_attested_through="2011-02-02"),
        ])
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("ambiguous", sel.state)
        self.assertEqual((0, 1), sel.candidates)

    def test_multiple_ambiguous_transitions_widen_the_candidate_range(self):
        # Three changes: the first definitely OLD, the remaining two both
        # completely undated. Each additional ambiguous transition widens
        # the candidate range by one with no upper propagation from change
        # 0's definite OLD state, showing how quickly an unpropagated chain
        # of ambiguous transitions widens.
        e = erratum_of(changes=[
            change(date=None, effective_old_attested_through="2011-02-02",
                   resulting_implementation=implementation(historical_passcode=510000001)),
            change(date=None, resulting_implementation=implementation(historical_passcode=510000002)),
            change(date=None),
        ])
        sel = e.selection_at(day("2010-04-24"))
        self.assertEqual("ambiguous", sel.state)
        self.assertEqual((0, 1, 2), sel.candidates)


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


class FormatPolicyTest(TempRepoTest):
    """The two standing decisions a format may state instead of maintaining a
    per-card list: reproducing a reference implementation, and how to resolve
    genuinely ambiguous chronology."""

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

    PARITY = {
        "reason": "this format reproduces an existing reference implementation",
        "sources": ["test-source"],
    }

    def test_reference_parity_substitutes_without_any_include_list(self):
        self._seed(review="reviewed", changes=[change(date=None)])  # ambiguous
        self.add_format(errata_overrides={"reference_parity": self.PARITY})
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(510000000, built.entries)
        self.assertNotIn(200, built.entries)
        validator = Validator(repo)
        validator.validate()
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))

    def test_reference_parity_substitutes_cosmetic_records_but_says_so(self):
        # The reference ships a period-text variant of a behaviourally equal
        # card: parity keeps it (that IS the reference), and warns.
        self._seed(
            review="reviewed",
            classification="cosmetic",
            changes=[change(kind="cosmetic", date="2011-07-01")],
        )
        self.add_format(errata_overrides={"reference_parity": self.PARITY})
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(510000000, built.entries)
        validator = Validator(repo)
        validator.validate()
        self.assertIn(
            "format.parity-substitutes-non-behavioural", {f.code for f in validator.warnings}
        )

    def test_reference_parity_warns_when_chronology_disagrees(self):
        # Change dated before the snapshot: our research says the modern card
        # was already in force, but the reference still ships the variant.
        self._seed(review="reviewed", changes=[change(date="2004-01-01")])
        self.add_format(errata_overrides={"reference_parity": self.PARITY})
        validator = Validator(Repository.load(self.root))
        validator.validate()
        self.assertIn(
            "format.parity-contradicts-chronology", {f.code for f in validator.warnings}
        )

    def test_reference_parity_respects_explicit_excludes(self):
        self._seed(review="reviewed", changes=[change(date=None)])
        self.add_format(
            errata_overrides={"reference_parity": self.PARITY, "exclude": ["erratum-beta"]}
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)
        self.assertNotIn(510000000, built.entries)

    def test_reference_parity_requires_reason_and_sources(self):
        self._seed(review="reviewed", changes=[change(date=None)])
        self.add_format(errata_overrides={"reference_parity": {"reason": "", "sources": []}})
        validator = Validator(Repository.load(self.root))
        validator.validate()
        self.assertIn("format.policy-unjustified", {f.code for f in validator.errors})

    def test_unresolved_policy_modern_keeps_modern_and_names_each_card(self):
        self._seed(review="reviewed", changes=[change(date=None)])
        self.add_format(
            errata_overrides={
                "unresolved_policy": {
                    "choice": "modern",
                    "reason": "no reference implementation exists for this format",
                    "sources": ["test-source"],
                }
            }
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(200, built.entries)
        self.assertNotIn(510000000, built.entries)
        validator = Validator(repo)
        validator.validate()
        self.assertEqual([], validator.errors, msg="\n".join(map(str, validator.errors)))
        warned = [
            f for f in validator.warnings if f.code == "format.erratum-unresolved-defaulted"
        ]
        self.assertEqual(1, len(warned))
        self.assertIn("Beta", warned[0].message)

    def test_unresolved_policy_historical_substitutes(self):
        self._seed(review="reviewed", changes=[change(date=None)])
        self.add_format(
            errata_overrides={
                "unresolved_policy": {
                    "choice": "historical",
                    "reason": "period behaviour is the default for this era",
                    "sources": ["test-source"],
                }
            }
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(510000000, built.entries)

    def test_without_a_policy_ambiguity_is_still_a_hard_error(self):
        self._seed(review="reviewed", changes=[change(date=None)])
        self.add_format()
        validator = Validator(Repository.load(self.root))
        validator.validate()
        self.assertIn("format.erratum-ambiguous", {f.code for f in validator.errors})

    def test_modern_fallback_is_flagged_when_modern_is_provably_wrong(self):
        """Found by adversarial review. When one change in a chain is dated
        and another is not, the evidence can be unable to say WHICH historical
        version applies while still proving the modern card is not one of
        them. An unresolved_policy of "modern" then picks a card we know is
        wrong, and that must be reported as a known divergence rather than as
        a neutral default."""
        self._seed(
            review="reviewed",
            changes=[
                change(kind="ruling", date=None),  # unresolved
                change(kind="functional", date="2015-07-16"),  # after the snapshot
            ],
        )
        self.add_format(
            errata_overrides={
                "unresolved_policy": {
                    "choice": "modern",
                    "reason": "conservative default",
                    "sources": ["test-source"],
                }
            }
        )
        repo = Repository.load(self.root)
        erratum = repo.errata["erratum-beta"]
        selection = erratum.selection_at(_dt.date(2005, 4, 1))
        self.assertEqual("ambiguous", selection.state)
        self.assertEqual((0, 1), selection.candidates)
        self.assertEqual(2, selection.modern_version)
        self.assertFalse(selection.modern_is_possible)
        validator = Validator(repo)
        validator.validate()
        codes = {f.code for f in validator.warnings}
        self.assertIn("format.erratum-modern-known-wrong", codes)
        self.assertNotIn("format.erratum-unresolved-defaulted", codes)

    def test_ordinary_ambiguity_still_reports_a_plain_default(self):
        # Single unresolved change: modern IS one of the candidates, so the
        # fallback is a neutral documented choice.
        self._seed(review="reviewed", changes=[change(date=None)])
        self.add_format(
            errata_overrides={
                "unresolved_policy": {
                    "choice": "modern",
                    "reason": "conservative default",
                    "sources": ["test-source"],
                }
            }
        )
        repo = Repository.load(self.root)
        selection = repo.errata["erratum-beta"].selection_at(_dt.date(2005, 4, 1))
        self.assertTrue(selection.modern_is_possible)
        validator = Validator(repo)
        validator.validate()
        codes = {f.code for f in validator.warnings}
        self.assertIn("format.erratum-unresolved-defaulted", codes)
        self.assertNotIn("format.erratum-modern-known-wrong", codes)

    def test_policy_does_not_override_resolved_chronology(self):
        # A dated change is not ambiguous: the policy must not touch it.
        self._seed(review="reviewed", changes=[change(date="2015-07-16")])
        self.add_format(
            errata_overrides={
                "unresolved_policy": {
                    "choice": "modern",
                    "reason": "conservative default",
                    "sources": ["test-source"],
                }
            }
        )
        repo = Repository.load(self.root)
        built = build_lflist(repo.formats["2005-04-test"], repo)
        self.assertIn(510000000, built.entries)  # chronology wins
        self.assertNotIn(200, built.entries)


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
