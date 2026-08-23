"""End-to-end tests for the temporary v1/v2 consumer compatibility layer
(implementation step 3 of docs/research/erratum-state-model-v2.md's frozen
design): validate.py's v2 record/format checks, lflist.py's v2 selection
and override semantics, and the permanent v2 validator invariants — all
exercised through the REAL consumer functions (Validator,
select_applicable_errata, build_lflist) over a synthetic repository built
with tests/helpers.py, not by calling model.py in isolation.

No canonical record uses the v2 shape yet, so every fixture here is
constructed fresh. Scenario letters match the task's own enumeration.
"""

from __future__ import annotations

import datetime as _dt
import unittest

from retroformats.lflist import (
    ErrataSelectionError,
    build_lflist,
    historical_identity,
    select_applicable_errata,
)
from retroformats.model import Coverage
from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import TempRepoTest, card, v2_coverage, v2_event, v2_transition


def day(s: str) -> _dt.date:
    return _dt.date.fromisoformat(s)


class V2ConsumerTestBase(TempRepoTest):
    """A minimal banlist/pool/rules/format fixture, snapshot 2005-04-01,
    so erratum event dates can be chosen relative to it (before/after)
    without needing to override period in every test."""

    def _standard_fixture(self, pool_cards=(), **fmt_kw):
        self.add_banlist()
        self.add_pool(cards=list(pool_cards))
        self.add_rule_profile()
        self.add_format(**fmt_kw)

    def _repo(self) -> Repository:
        return Repository.load(self.root)

    def _fmt(self, repo: Repository):
        return repo.formats["2005-04-test"]

    def _errors(self, repo: Repository, code: str | None = None):
        v = Validator(repo)
        v.validate()
        errs = v.errors
        return [e for e in errs if code is None or e.code == code]

    def _warnings(self, repo: Repository, code: str | None = None):
        v = Validator(repo)
        v.validate()
        warns = v.warnings
        return [w for w in warns if code is None or w.code == code]


class DeterminateCoverageKindsTest(V2ConsumerTestBase):
    """A-D: what lflist.py does for each coverage kind of a determinate
    (non-ambiguous) v2 selection."""

    def test_A_reuse_upstream_substitutes_historical_passcode(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2020-01-01"})},  # future: OLD at 2005-04-01
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000123)}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertEqual(historical_identity(overrides[200].implementation), (511000123, ()))
        built = build_lflist(fmt, repo)
        self.assertIn(511000123, built.entries)
        self.assertNotIn(200, built.entries)

    def test_B_none_needed_keeps_modern_card(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2020-01-01"})},
            states=[{"events": [], "coverage": v2_coverage(kind="none-needed")}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)
        built = build_lflist(fmt, repo)
        self.assertIn(200, built.entries)

    def test_C_known_gap_surfaces_divergence_and_keeps_modern(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2020-01-01"})},
            states=[{"events": [], "coverage": v2_coverage(kind="known-gap")}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)  # acknowledged gap: modern stands in
        self.assertTrue(self._warnings(repo, "format.erratum-known-divergence"))
        built = build_lflist(fmt, repo)
        self.assertIn(200, built.entries)

    def test_D_unresolved_fails_safe(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        # No states[] entry at all for {} -> mechanically UNRESOLVED.
        self.add_erratum_v2(events={"e1": v2_event(effective={"date": "2020-01-01"})})
        repo = self._repo()
        fmt = self._fmt(repo)
        with self.assertRaises(ErrataSelectionError):
            select_applicable_errata(fmt, repo)
        self.assertTrue(self._errors(repo, "format.erratum-implementation-gap"))


class AmbiguousPolicyTest(V2ConsumerTestBase):
    """E-I: unresolved_policy semantics for an ambiguous v2 selection."""

    def _ambiguous_two_event_fixture(self, second_coverage=None):
        # A: dated in the future relative to the 2005-04-01 snapshot -> OLD,
        # so no candidate may include A -> {} and {B} survive, {A}/{A,B} do not.
        # B: undated -> permanently ambiguous.
        events = {
            "A": v2_event(effective={"date": "2020-01-01"}),
            "B": v2_event(effective={"date": None}),
        }
        states = [{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000001)}]
        if second_coverage is not None:
            states.append({"events": ["B"], "coverage": second_coverage})
        self.add_erratum_v2(events=events, ordering={}, states=states)

    def test_E_ambiguous_no_policy_fails_safe(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self._ambiguous_two_event_fixture()
        repo = self._repo()
        fmt = self._fmt(repo)
        with self.assertRaises(ErrataSelectionError):
            select_applicable_errata(fmt, repo)
        self.assertTrue(self._errors(repo, "format.erratum-ambiguous"))

    def test_F_ambiguous_modern_policy_modern_possible(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "unresolved_policy": {"choice": "modern", "reason": "test", "sources": ["test-source"]}
            },
        )
        # Both events undated -> {}, {A}, {B}, {A,B} all survive -> modern (the
        # terminal {A,B}) IS among the candidates.
        self.add_erratum_v2(
            events={"A": v2_event(), "B": v2_event()},
            ordering={},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream")}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)
        self.assertTrue(self._warnings(repo, "format.erratum-unresolved-defaulted"))
        self.assertFalse(self._warnings(repo, "format.erratum-modern-known-wrong"))

    def test_G_ambiguous_modern_policy_modern_impossible_known_wrong(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "unresolved_policy": {"choice": "modern", "reason": "test", "sources": ["test-source"]}
            },
        )
        self._ambiguous_two_event_fixture()  # terminal {A,B} excluded: A is OLD
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)  # modern still chosen, explicitly
        self.assertTrue(self._warnings(repo, "format.erratum-modern-known-wrong"))

    def test_H_ambiguous_historical_policy_one_unambiguous_outcome(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "unresolved_policy": {"choice": "historical", "reason": "test", "sources": ["test-source"]}
            },
        )
        # One relevant, undated event: candidates are {} and {event} (=
        # terminal). Exactly one non-modern candidate -> trivially agrees.
        self.add_erratum_v2(
            events={"e1": v2_event()},
            ordering={},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000009)}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertEqual(historical_identity(overrides[200].implementation), (511000009, ()))
        self.assertTrue(self._warnings(repo, "format.erratum-unresolved-defaulted"))

    def test_I_ambiguous_historical_policy_disagreeing_outcomes_fails_safe(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "unresolved_policy": {"choice": "historical", "reason": "test", "sources": ["test-source"]}
            },
        )
        # {} -> passcode 511000001, {B} -> a DIFFERENT passcode: disagreement.
        self._ambiguous_two_event_fixture(
            second_coverage=v2_coverage(kind="reuse-upstream", historical_passcode=511000002)
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        with self.assertRaises(ErrataSelectionError):
            select_applicable_errata(fmt, repo)
        self.assertTrue(self._errors(repo, "format.erratum-historical-policy-unresolved"))


class IncludeExcludeTest(V2ConsumerTestBase):
    """J-L: explicit per-card errata_overrides.include/exclude semantics."""

    def test_J_include_selects_baseline_when_plausible(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={"include": ["erratum-v2-beta"]},
        )
        self.add_erratum_v2(
            events={"e1": v2_event()},  # undated, ambiguous -- irrelevant, include wins outright
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000042)}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertEqual(historical_identity(overrides[200].implementation), (511000042, ()))

    def test_K_include_when_baseline_impossible_warns_contradiction(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={"include": ["erratum-v2-beta"]},
        )
        # Event dated in the PAST relative to 2005-04-01 snapshot -> always
        # confirmed NEW -> the only chronology-consistent candidate is the
        # terminal (modern) state, never baseline.
        self.add_erratum_v2(events={"e1": v2_event(effective={"date": "2000-01-01"})})
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)  # baseline has no usable coverage anyway
        self.assertTrue(self._warnings(repo, "format.erratum-include-contradicts-chronology"))

    def test_L_exclude_while_modern_impossible_warns_contradiction(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={"exclude": ["erratum-v2-beta"]},
        )
        # Event dated in the FUTURE -> always OLD -> only baseline {} survives,
        # a determinate non-modern (historical) state, while excluded.
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2020-01-01"})},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream")}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)  # exclude wins outright
        self.assertTrue(self._warnings(repo, "format.erratum-exclude-contradicts-chronology"))


class ReferenceParityTest(V2ConsumerTestBase):
    """M: the deterministic structural walk, proven declaration-order
    invariant as the task explicitly requires."""

    def _parity_events(self, reversed_order: bool):
        a = v2_event()
        b = v2_event()
        return {"B": b, "A": a} if reversed_order else {"A": a, "B": b}

    def _run(self, reversed_order: bool):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "reference_parity": {"reason": "test", "sources": ["test-source"]}
            },
        )
        self.add_erratum_v2(
            events=self._parity_events(reversed_order),
            ordering={},
            states=[
                {"events": [], "coverage": v2_coverage(kind="none-needed")},  # not usable
                {"events": ["A"], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000077)},
            ],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        return historical_identity(overrides[200].implementation)

    def test_M_parity_walk_selects_first_usable_state(self):
        self.assertEqual(self._run(reversed_order=False), (511000077, ()))

    def test_M_parity_walk_is_invariant_under_declaration_order(self):
        forward = self._run(reversed_order=False)
        self.setUp()  # fresh temp root for the second fixture
        reversed_ = self._run(reversed_order=True)
        self.assertEqual(forward, reversed_)


class OrderingValidationTest(V2ConsumerTestBase):
    """N-P: the ordering-edge PROVEN/CONTRADICTED/basis invariants (6-7)."""

    def test_N_chain_not_proven_is_an_error(self):
        self._standard_fixture()
        self.add_erratum_v2(
            events={
                "A": v2_event(
                    effective={"date": None, "old_attested_through": "2011-02-02", "new_attested_from": "2019-04-03"}
                ),
                "B": v2_event(effective={"date": "2016-09-15"}),
            },
            ordering={"chains": [["A", "B"]]},  # Sangan's own shape: inconclusive
        )
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.ordering-chain-not-proven"))

    def test_O_contradicted_edge_errors_regardless_of_basis(self):
        self._standard_fixture()
        self.add_erratum_v2(
            events={
                "A": v2_event(effective={"date": "2015-01-01"}),
                "B": v2_event(effective={"date": "2005-01-01"}),  # B provably precedes A
            },
            ordering={
                "edges": [
                    {"before": "A", "after": "B", "basis": "researcher-inference", "note": "deliberately wrong"}
                ]
            },
        )
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.ordering-contradicted"))

    def test_P_directly_sourced_inconclusive_edge_is_accepted(self):
        self._standard_fixture()
        self.add_erratum_v2(
            events={
                "A": v2_event(
                    effective={"date": None, "old_attested_through": "2011-02-02", "new_attested_from": "2019-04-03"}
                ),
                "B": v2_event(effective={"date": "2016-09-15"}),
            },
            ordering={
                "edges": [
                    {
                        "before": "A",
                        "after": "B",
                        "basis": "directly-sourced",
                        "note": "a period document states the order",
                        "sources": ["test-source"],
                    }
                ]
            },
        )
        repo = self._repo()
        self.assertFalse(self._errors(repo, "erratum.ordering-contradicted"))
        self.assertFalse(self._errors(repo, "erratum.ordering-basis-unproven"))
        self.assertFalse(self._errors(repo, "erratum.ordering-edge-unjustified"))


class StateKeyValidationTest(V2ConsumerTestBase):
    """Q-S: state-key invariants (3, 4, 5)."""

    def test_Q_duplicate_semantic_state_keys_is_an_error(self):
        self._standard_fixture()
        self.add_erratum_v2(
            events={"A": v2_event(), "B": v2_event()},
            ordering={},
            states=[
                {"events": ["A", "B"], "coverage": v2_coverage(kind="none-needed")},
                {"events": ["B", "A"], "coverage": v2_coverage(kind="known-gap")},
            ],
        )
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.state-duplicate-key"))

    def test_R_unreachable_state_key_is_an_error(self):
        self._standard_fixture()
        # A -> B via a PROVEN chain (both exactly dated) makes {B} alone
        # structurally unreachable: B's own predecessor A must be present too.
        self.add_erratum_v2(
            events={
                "A": v2_event(effective={"date": "2005-01-01"}),
                "B": v2_event(effective={"date": "2010-01-01"}),
            },
            ordering={"chains": [["A", "B"]]},
            states=[{"events": ["B"], "coverage": v2_coverage(kind="none-needed")}],
        )
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.state-unreachable"))

    def test_S_non_terminal_modern_coverage_is_an_error(self):
        self._standard_fixture()
        self.add_erratum_v2(
            events={"A": v2_event(), "B": v2_event()},
            ordering={},
            states=[{"events": ["A"], "coverage": {"kind": "modern"}}],
        )
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.non-terminal-modern"))


class CooccurrenceValidationTest(V2ConsumerTestBase):
    """T: invariant 10, enforced by the production validator directly
    (Repository.load() never runs the JSON Schema)."""

    def test_T_two_transition_event_without_cooccurrence_sources_is_an_error(self):
        self._standard_fixture()
        self.add_erratum_v2(
            events={
                "e1": v2_event(transitions=[v2_transition(axis="a"), v2_transition(axis="b")])
                # cooccurrence_sources deliberately omitted
            }
        )
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.cooccurrence-unsourced"))


if __name__ == "__main__":
    unittest.main()
