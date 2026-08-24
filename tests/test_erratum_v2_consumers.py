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

from .helpers import TempRepoTest, card, change, v2_coverage, v2_event, v2_transition


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
        # terminal (modern) state, never baseline. The baseline carries a
        # usable coverage so what is under test is the CONTRADICTION
        # diagnostic, not the separate unresolved-coverage failure.
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2000-01-01"})},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000077)}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        # The include is honoured - it is an explicit adjudication - but the
        # disagreement with chronology is reported rather than hidden.
        self.assertEqual(historical_identity(overrides[200].implementation), (511000077, ()))
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


class MalformedHistoricalIdentityTest(V2ConsumerTestBase):
    """Objective 1: a coverage that CLAIMS a substitution but records no
    historical_passcode must never reach `historical_identity()` as
    `int(None)`. `_usable_v2()` now checks the passcode exactly as legacy
    `_usable()` always did, and a direct build refuses rather than crashing
    - it must not depend on the validator having been run first."""

    def test_reuse_upstream_without_passcode_is_not_usable(self):
        from retroformats.lflist import _usable_v2
        from retroformats.model import ImplementationCoverage

        broken = ImplementationCoverage(kind=Coverage.REUSE_UPSTREAM, historical_passcode=None)
        self.assertIsNone(_usable_v2(broken))
        ok = ImplementationCoverage(kind=Coverage.REUSE_UPSTREAM, historical_passcode=511000042)
        self.assertIs(_usable_v2(ok), ok)

    def test_historical_identity_raises_instead_of_int_none(self):
        from retroformats.lflist import MalformedHistoricalIdentity, historical_identity
        from retroformats.model import ImplementationCoverage

        broken = ImplementationCoverage(kind=Coverage.CUSTOM_SCRIPT, historical_passcode=None)
        with self.assertRaises(MalformedHistoricalIdentity):
            historical_identity(broken)
        with self.assertRaises(MalformedHistoricalIdentity):
            historical_identity({"strategy": "reuse-upstream"})

    def test_executable_outcome_never_agrees_on_a_missing_passcode(self):
        from retroformats.lflist import _executable_outcome
        from retroformats.model import ImplementationCoverage

        broken = ImplementationCoverage(kind=Coverage.REUSE_UPSTREAM, historical_passcode=None)
        self.assertIsNone(_executable_outcome(broken))

    def test_direct_build_fails_cleanly_on_malformed_determinate_coverage(self):
        """The regression: build_lflist called WITHOUT the validator first."""
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2020-01-01"})},  # OLD at snapshot
            states=[{"events": [], "coverage": {"kind": "reuse-upstream"}}],  # no passcode
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        with self.assertRaises(ErrataSelectionError) as ctx:
            build_lflist(fmt, repo)
        self.assertIn("no historical_passcode", str(ctx.exception))

    def test_direct_build_fails_cleanly_on_malformed_parity_coverage(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "reference_parity": {"reason": "reproduces a reference list", "sources": ["test-source"]}
            },
        )
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2020-01-01"})},
            states=[{"events": [], "coverage": {"kind": "custom-script"}}],  # no passcode
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        with self.assertRaises(ErrataSelectionError) as ctx:
            build_lflist(fmt, repo)
        self.assertIn("no historical_passcode", str(ctx.exception))


class ExplicitIncludeCoverageKindsTest(V2ConsumerTestBase):
    """Objective 2: an explicit include pins the BASELINE state, and the
    five coverage kinds are five different answers - not one silent
    "no override"."""

    def _include_fixture(self, coverage):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={"include": ["erratum-v2-beta"]},
        )
        # Undated event: permanently ambiguous, baseline always plausible, so
        # the include is a legitimate adjudication and the coverage kind is
        # the only variable under test.
        self.add_erratum_v2(
            events={"e1": v2_event()},
            states=([{"events": [], "coverage": coverage}] if coverage is not None else None),
        )
        repo = self._repo()
        return repo, self._fmt(repo)

    def test_include_baseline_reuse_upstream_substitutes(self):
        repo, fmt = self._include_fixture(
            v2_coverage(kind="reuse-upstream", historical_passcode=511000201)
        )
        overrides = select_applicable_errata(fmt, repo)
        self.assertEqual(historical_identity(overrides[200].implementation), (511000201, ()))
        self.assertEqual([], self._errors(repo))

    def test_include_baseline_none_needed_keeps_modern_and_is_valid(self):
        repo, fmt = self._include_fixture(v2_coverage(kind="none-needed"))
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)
        built = build_lflist(fmt, repo)
        self.assertIn(200, built.entries)  # modern card stays legal
        self.assertEqual([], self._errors(repo))

    def test_include_baseline_known_gap_keeps_modern_and_surfaces_divergence(self):
        repo, fmt = self._include_fixture(v2_coverage(kind="known-gap"))
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)
        self.assertIn(200, build_lflist(fmt, repo).entries)
        self.assertEqual([], self._errors(repo))
        self.assertTrue(self._warnings(repo, "format.erratum-known-divergence"))

    def test_include_baseline_unresolved_fails_safe(self):
        repo, fmt = self._include_fixture(None)  # no states[] -> UNRESOLVED baseline
        with self.assertRaises(ErrataSelectionError) as ctx:
            select_applicable_errata(fmt, repo)
        self.assertIn("unresolved", str(ctx.exception))
        self.assertTrue(self._errors(repo, "format.erratum-include-unresolved-coverage"))

    def test_include_baseline_claiming_substitution_without_passcode_fails_safe(self):
        repo, fmt = self._include_fixture({"kind": "reuse-upstream"})
        with self.assertRaises(ErrataSelectionError):
            select_applicable_errata(fmt, repo)
        self.assertTrue(self._errors(repo, "format.erratum-include-unresolved-coverage"))


class AmbiguousAdjudicationDiagnosticsTest(V2ConsumerTestBase):
    """Objective 2: include/exclude diagnostics must also fire when the
    selection is AMBIGUOUS, which previously only the determinate branch
    handled."""

    def test_ambiguous_include_with_baseline_plausible_is_a_legitimate_adjudication(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={"include": ["erratum-v2-beta"]},
        )
        self.add_erratum_v2(
            events={"e1": v2_event()},  # undated -> ambiguous, baseline plausible
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000301)}],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        self.assertEqual(historical_identity(overrides[200].implementation), (511000301, ()))
        self.assertEqual([], self._errors(repo))
        # Not a contradiction, not redundant: exactly the adjudication the
        # ambiguity asks for.
        self.assertEqual([], self._warnings(repo, "format.erratum-include-contradicts-chronology"))
        self.assertEqual([], self._warnings(repo, "format.erratum-include-redundant"))

    def test_ambiguous_include_with_baseline_impossible_is_reported(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={"include": ["erratum-v2-beta"]},
        )
        # e1 confirmed NEW at the snapshot (past date) forces every candidate
        # to contain e1; e2 is undated, so the selection stays AMBIGUOUS
        # between {e1} and {e1,e2} - and baseline {} is not among them.
        self.add_erratum_v2(
            events={
                "e1": v2_event(effective={"date": "2000-01-01"}),
                "e2": v2_event(),
            },
            states=[
                {"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000302)},
                {"events": ["e1"], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000303)},
            ],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        selection = repo.errata["erratum-v2-beta"].selection_at(day("2005-04-01"))
        self.assertEqual("ambiguous", selection.chronology)
        self.assertNotIn(frozenset(), {c.events for c in selection.candidates})
        self.assertTrue(self._errors(repo, "format.erratum-include-wrong-version"))

    def test_ambiguous_exclude_with_modern_impossible_is_reported(self):
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={"exclude": ["erratum-v2-beta"]},
        )
        # e1 confirmed OLD (future date) forbids every state containing it,
        # so the terminal/modern state is impossible; e2 undated keeps the
        # selection ambiguous between {} and {e2}.
        self.add_erratum_v2(
            events={
                "e1": v2_event(effective={"date": "2020-01-01"}),
                "e2": v2_event(),
            },
            states=[
                {"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000304)},
                {"events": ["e2"], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000305)},
            ],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        selection = repo.errata["erratum-v2-beta"].selection_at(day("2005-04-01"))
        self.assertEqual("ambiguous", selection.chronology)
        self.assertFalse(selection.modern_is_possible)
        overrides = select_applicable_errata(fmt, repo)
        self.assertNotIn(200, overrides)  # exclude still wins outright
        self.assertTrue(self._warnings(repo, "format.erratum-exclude-contradicts-chronology"))


class ProductionValidatorShapeTest(V2ConsumerTestBase):
    """Objective 6: guarantees the JSON Schema states but `Repository.load()`
    never runs. It parses raw JSON directly, so each of these is a case where
    the parser's own normalisation would otherwise make malformed data
    indistinguishable from valid data."""

    def _record(self, **kw):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(**kw)
        return self._repo()

    def test_A_repeated_id_in_one_states_events_array_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event(), "e2": v2_event()},
            states=[{"events": ["e1", "e1"], "coverage": v2_coverage(kind="none-needed")}],
        )
        self.assertTrue(self._errors(repo, "erratum.state-events-duplicate"))

    def test_A_distinct_ids_are_fine(self):
        repo = self._record(
            events={"e1": v2_event(), "e2": v2_event()},
            states=[{"events": ["e1", "e2"], "coverage": v2_coverage(kind="none-needed")}],
        )
        self.assertEqual([], self._errors(repo, "erratum.state-events-duplicate"))

    def test_B_full_v2_missing_ordering_is_an_error(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        # add_erratum_v2 always writes `ordering`; drop it to model a raw
        # authored record that omitted the block entirely.
        self.add_erratum_v2(events={"e1": v2_event()})
        path = self.root / "data/errata/v2-beta.json"
        import json as _json

        doc = _json.loads(path.read_text(encoding="utf-8"))
        del doc["ordering"]
        path.write_text(_json.dumps(doc, indent=2), encoding="utf-8")
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.missing-ordering"))

    def test_B_sugar_needs_no_authored_ordering(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.write(
            "data/errata/v2-sugar.json",
            {
                "id": "erratum-v2-sugar",
                "modern_card": {"passcode": 200, "name": "Beta"},
                "classification": "functional",
                "event": {
                    "effective": {"date": "2015-01-01"},
                    "kind": "functional",
                    "summary": "x",
                    "sources": ["test-source"],
                },
                "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000900),
                "review": {"status": "reviewed"},
                "sources": ["test-source"],
            },
        )
        repo = self._repo()
        self.assertEqual([], self._errors(repo, "erratum.missing-ordering"))

    def test_C_event_missing_effective_is_an_error(self):
        repo = self._record(
            events={"e1": {"transitions": [v2_transition(kind="functional")]}},
        )
        self.assertTrue(self._errors(repo, "erratum.event-missing-effective"))

    def test_C_effective_missing_date_key_is_an_error(self):
        repo = self._record(events={"e1": v2_event(effective={})})
        self.assertTrue(self._errors(repo, "erratum.event-missing-effective"))

    def test_C_explicit_null_date_is_valid_unknown_chronology(self):
        repo = self._record(events={"e1": v2_event(effective={"date": None})})
        self.assertEqual([], self._errors(repo, "erratum.event-missing-effective"))

    def test_D_malformed_date_on_an_ordered_event_reports_and_does_not_crash(self):
        repo = self._record(
            events={
                "e1": v2_event(effective={"date": "2010-13-45"}),
                "e2": v2_event(effective={"date": "2015-01-01"}),
            },
            ordering={"chains": [["e1", "e2"]]},
        )
        # The whole validation run completes and reports, rather than dying
        # with an uncaught ValueError out of ordering_proof().
        v = Validator(repo)
        findings = v.validate()
        self.assertTrue(findings)
        codes = {f.code for f in v.errors}
        self.assertIn("erratum.ordering-uncheckable", codes)

    def test_E_known_gap_with_historical_passcode_is_rejected(self):
        repo = self._record(
            events={"e1": v2_event()},
            states=[
                {
                    "events": [],
                    "coverage": {
                        "kind": "known-gap",
                        "gap_reason": "none upstream",
                        "gap_sources": ["test-source"],
                        "historical_passcode": 511000001,
                    },
                }
            ],
        )
        self.assertTrue(self._errors(repo, "erratum.coverage-incompatible-field"))

    def test_E_none_needed_with_implementation_payload_is_rejected(self):
        repo = self._record(
            events={"e1": v2_event()},
            states=[
                {
                    "events": [],
                    "coverage": {"kind": "none-needed", "script": "dist/scripts/c1.lua"},
                }
            ],
        )
        self.assertTrue(self._errors(repo, "erratum.coverage-incompatible-field"))

    def test_E_reuse_upstream_with_gap_fields_is_rejected(self):
        repo = self._record(
            events={"e1": v2_event()},
            states=[
                {
                    "events": [],
                    "coverage": {
                        "kind": "reuse-upstream",
                        "historical_passcode": 511000002,
                        "upstream": "ProjectIgnis",
                        "gap_reason": "should not be here",
                    },
                }
            ],
        )
        self.assertTrue(self._errors(repo, "erratum.coverage-incompatible-field"))

    def test_E_wellformed_coverages_are_accepted(self):
        repo = self._record(
            events={"e1": v2_event(), "e2": v2_event()},
            states=[
                {"events": [], "coverage": v2_coverage(kind="reuse-upstream")},
                {"events": ["e1"], "coverage": v2_coverage(kind="known-gap")},
            ],
        )
        self.assertEqual([], self._errors(repo, "erratum.coverage-incompatible-field"))


class MalformedPasscodeHardeningTest(V2ConsumerTestBase):
    """One remaining hole 5f7d2da did not close: `historical_passcode=None`
    is fail-safe, but a non-integer/out-of-range PRESENT value is not.
    `ImplementationCoverage.from_raw()` keeps the field RAW, and production
    validation does `int(hist)`/`int(variant)` - previously unguarded, so
    this crashed the validator itself rather than reporting an ERROR
    finding. A non-integer passcode must be exactly as unusable as a
    missing one everywhere: validator (report, never crash), direct build
    (ErrataSelectionError, never a bare ValueError/TypeError/
    MalformedHistoricalIdentity), and v1's own `selection_at()` (falls back
    to 'gap', its existing safe behaviour for 'no usable passcode')."""

    def test_v2_non_integer_passcode_is_reported_not_crashed(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event()},
            states=[
                {
                    "events": [],
                    "coverage": {
                        "kind": "reuse-upstream",
                        "historical_passcode": "not-a-passcode",
                        "upstream": "ProjectIgnis",
                    },
                }
            ],
        )
        repo = self._repo()
        findings = Validator(repo).validate()
        self.assertTrue(findings)  # completes; does not raise
        self.assertTrue(self._errors(repo, "erratum.malformed-passcode"))

    def test_v2_non_integer_variant_is_reported_not_crashed(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event()},
            states=[
                {
                    "events": [],
                    "coverage": {
                        "kind": "reuse-upstream",
                        "historical_passcode": 511000900,
                        "historical_variant_passcodes": ["also-not-a-passcode"],
                        "upstream": "ProjectIgnis",
                    },
                }
            ],
        )
        repo = self._repo()
        Validator(repo).validate()
        self.assertTrue(self._errors(repo, "erratum.malformed-passcode"))

    def test_v2_out_of_range_passcode_is_reported_not_crashed(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event()},
            states=[
                {
                    "events": [],
                    "coverage": {"kind": "reuse-upstream", "historical_passcode": -5, "upstream": "ProjectIgnis"},
                }
            ],
        )
        repo = self._repo()
        Validator(repo).validate()
        self.assertTrue(self._errors(repo, "erratum.malformed-passcode"))

    def test_v2_direct_build_never_leaks_a_bare_value_or_type_error(self):
        """No validator run first - the exact regression objective 1 fixed
        for a missing passcode must also hold for a malformed one."""
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2020-01-01"})},  # OLD at snapshot
            states=[
                {
                    "events": [],
                    "coverage": {
                        "kind": "reuse-upstream",
                        "historical_passcode": "not-a-passcode",
                        "upstream": "ProjectIgnis",
                    },
                }
            ],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        with self.assertRaises(ErrataSelectionError):
            build_lflist(fmt, repo)

    def test_v2_usable_v2_rejects_non_integer_passcode(self):
        from retroformats.lflist import _usable_v2
        from retroformats.model import ImplementationCoverage

        broken = ImplementationCoverage(kind=Coverage.CUSTOM_SCRIPT, historical_passcode="nope")
        self.assertIsNone(_usable_v2(broken))

    def test_v1_non_integer_passcode_falls_back_to_gap_not_a_crash(self):
        """v1's `selection_at()` already treats a missing passcode as
        'gap' - a non-integer one gets the identical, already-safe
        fallback, never an uncaught int() failure three layers downstream
        in historical_identity()."""
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum(
            id="erratum-alpha",
            modern={"passcode": 200, "name": "Beta"},
            changes=[change(date="2020-01-01")],  # OLD (not yet occurred) at snapshot: baseline in force
            impl={"strategy": "reuse-upstream", "historical_passcode": "not-a-passcode", "status": "complete"},
        )
        repo = self._repo()
        record = repo.errata["erratum-alpha"]
        snapshot = _dt.date.fromisoformat(self._fmt(repo).snapshot)
        selection = record.selection_at(snapshot)
        self.assertEqual("gap", selection.state)

    def test_v1_non_integer_passcode_is_a_validator_error_not_a_crash(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum(
            id="erratum-alpha",
            modern={"passcode": 200, "name": "Beta"},
            impl={"strategy": "reuse-upstream", "historical_passcode": "not-a-passcode", "status": "complete"},
        )
        repo = self._repo()
        Validator(repo).validate()
        self.assertTrue(self._errors(repo, "erratum.malformed-passcode"))
