"""Runtime tests for the v2 semantic model/parser/selector (implementation
step 2 of docs/research/erratum-state-model-v2.md's frozen design).

This is a NEW, separate runtime path alongside the legacy v1 Erratum/
ErratumSelection in retroformats/model.py, which stay completely unmodified
— see tests/test_repo_data.py's test_giant_rat_selection_shape for the
existing, still-passing lock on real-data legacy behaviour. Every test here
constructs a synthetic v2 fixture (no canonical record uses this shape yet)
and exercises ErratumV2.load()/.selection_at() directly, matching this
document's design precisely:
- events are the chronology nodes; declaration order in a dict is never
  read as evidence (Python dict key order is preserved but structurally
  irrelevant here — this file's "declaration-order invariance" test proves
  it, not merely asserts it);
- omitted ordering means no edge, never "chained to the previous entry";
- a candidate state's identity is its event-set, never a position, a count,
  or a whole-object comparison (HistoricalState.label/.coverage are
  descriptive only);
- coverage is looked up by event-set: the all-events state is always
  MODERN (synthesised, never authored), any other reachable-but-unauthored
  state is UNRESOLVED, and an authored states[] entry is used verbatim;
- a cosmetic/engine-only event never creates a state dimension, but still
  participates in the ordering GRAPH, so a chain through one still induces
  a real constraint between the relevant events on either side of it.
"""

from __future__ import annotations

import datetime as _dt
import unittest
from pathlib import Path

from retroformats.model import (
    Coverage,
    DataError,
    Erratum,
    ErratumV2,
    HistoricalState,
    ImplementationCoverage,
    SelectionError,
    SemanticErratumSelection,
    load_erratum_record,
)


def day(s: str) -> _dt.date:
    return _dt.date.fromisoformat(s)


def transition(kind="ruling", summary="changed", axis=None, **kw):
    t = {"kind": kind, "summary": summary, "sources": ["test-source"]}
    if axis is not None:
        t["axis"] = axis
    t.update(kw)
    return t


def event(effective=None, transitions=None, cooccurrence_sources=None, **kw):
    e = {
        "effective": effective if effective is not None else {"date": None},
        "transitions": transitions if transitions is not None else [transition()],
    }
    if cooccurrence_sources is not None:
        e["cooccurrence_sources"] = cooccurrence_sources
    e.update(kw)
    return e


def coverage(kind="reuse-upstream", **kw):
    c = {"kind": kind}
    if kind == "reuse-upstream":
        c.setdefault("historical_passcode", 511000000)
        c.setdefault("upstream", "ProjectIgnis/BabelCDB goat-entries.cdb")
    elif kind == "custom-script":
        c.setdefault("historical_passcode", 511000001)
        c.setdefault("script", "dist/scripts/c511000001.lua")
    elif kind == "known-gap":
        c.setdefault("gap_reason", "no upstream implementation exists")
        c.setdefault("gap_sources", ["test-source"])
    c.update(kw)
    return c


def erratum_v2_of(**kw) -> ErratumV2:
    raw = {
        "id": kw.pop("id", "erratum-v2-x"),
        "modern_card": kw.pop("modern_card", {"passcode": 200, "name": "Beta"}),
        "classification": kw.pop("classification", "ruling"),
        "events": kw.pop("events"),
        "sources": ["test-source"],
    }
    if "ordering" in kw:
        raw["ordering"] = kw.pop("ordering")
    if "states" in kw:
        raw["states"] = kw.pop("states")
    raw.update(kw)
    return ErratumV2.load(raw, Path("x.json"))


def event_sets(selection: SemanticErratumSelection) -> set[frozenset[str]]:
    return {c.events for c in selection.candidates}


class GiantRatV2Test(unittest.TestCase):
    """§9.A: the canonical worked example. Must NOT reproduce v1's
    numeric candidates=(0,1), and must NOT produce {verification} —
    verification is confirmed OLD at Edison, so no valid down-set may
    include it."""

    def setUp(self):
        self.erratum = erratum_v2_of(
            id="erratum-giant-rat",
            events={
                "verification": event(
                    effective={
                        "date": None,
                        "old_attested_through": "2011-02-02",
                        "new_attested_from": "2019-04-03",
                    },
                    transitions=[transition(axis="search-reveal-procedure")],
                ),
                "activation-semantics": event(
                    effective={"date": None},
                    transitions=[transition(axis="search-activation-legality")],
                ),
            },
            ordering={},
            states=[
                {"events": [], "coverage": coverage(kind="reuse-upstream")},
                {"events": ["activation-semantics"], "coverage": coverage(kind="known-gap")},
            ],
        )

    def test_edison_candidates_are_exactly_empty_and_activation_alone(self):
        selection = self.erratum.selection_at(day("2010-04-24"))
        self.assertEqual(
            event_sets(selection), {frozenset(), frozenset({"activation-semantics"})}
        )

    def test_edison_chronology_is_ambiguous(self):
        selection = self.erratum.selection_at(day("2010-04-24"))
        self.assertEqual(selection.chronology, "ambiguous")

    def test_edison_modern_is_not_possible(self):
        # verification is confirmed OLD, so the all-events (modern) state
        # can never survive at Edison -- this is a KNOWN error, not a
        # neutral ambiguity, exactly like v1's modern_is_possible contract.
        selection = self.erratum.selection_at(day("2010-04-24"))
        self.assertFalse(selection.modern_is_possible)

    def test_edison_has_known_gap(self):
        selection = self.erratum.selection_at(day("2010-04-24"))
        self.assertTrue(selection.has_known_gap)

    def test_verification_alone_never_appears_while_verification_is_confirmed_old(self):
        # Through 2011-02-02 verification is confirmed OLD (old_attested_
        # through), so {verification} alone can never be a valid candidate
        # there -- activation being permanently AMBIGUOUS never excludes it
        # on its own (AMBIGUOUS satisfies "not NEW" trivially); only
        # verification's own OLD status can exclude {verification}.
        for snapshot in (day("2000-01-01"), day("2010-04-24"), day("2011-02-02")):
            selection = self.erratum.selection_at(snapshot)
            self.assertNotIn(frozenset({"verification"}), event_sets(selection))

    def test_verification_alone_becomes_reachable_once_verification_is_no_longer_old(self):
        # Once past 2011-02-02, verification's own status is AMBIGUOUS (and
        # NEW from 2019-04-03), so {verification} alone becomes a genuinely
        # valid candidate -- activation being undated never blocks it.
        selection = self.erratum.selection_at(day("2015-01-01"))
        self.assertIn(frozenset({"verification"}), event_sets(selection))


class YZTankDragonV2Test(unittest.TestCase):
    """§9.B: two completely undated, unordered relevant events -> exactly
    the 4 combinatorial states, never v1's 3 array-prefix candidates."""

    def test_four_states_at_any_snapshot(self):
        erratum = erratum_v2_of(
            events={
                "material-rule": event(transitions=[transition(kind="ruling")]),
                "summon-rule": event(transitions=[transition(kind="functional")]),
            },
            ordering={},
        )
        for snapshot in (day("2000-01-01"), day("2010-04-24"), day("2030-01-01")):
            selection = erratum.selection_at(snapshot)
            self.assertEqual(
                event_sets(selection),
                {
                    frozenset(),
                    frozenset({"material-rule"}),
                    frozenset({"summon-rule"}),
                    frozenset({"material-rule", "summon-rule"}),
                },
            )
            self.assertEqual(selection.chronology, "ambiguous")


class DeclarationOrderInvarianceTest(unittest.TestCase):
    """§9.C: reversed events{} key order must select identically."""

    def test_reversed_key_order_gives_identical_selection(self):
        verification = event(
            effective={"date": None, "old_attested_through": "2011-02-02"},
            transitions=[transition(axis="verification")],
        )
        activation = event(effective={"date": None}, transitions=[transition(axis="activation")])
        forward = erratum_v2_of(
            id="forward", events={"verification": verification, "activation": activation}, ordering={}
        )
        reversed_ = erratum_v2_of(
            id="reversed", events={"activation": activation, "verification": verification}, ordering={}
        )
        for snapshot in (day("2005-01-01"), day("2010-04-24"), day("2020-01-01")):
            self.assertEqual(
                event_sets(forward.selection_at(snapshot)), event_sets(reversed_.selection_at(snapshot))
            )


class PartialOrderV2Test(unittest.TestCase):
    """§9.D: A < C, B unordered -> exactly the down-sets a partial order
    over {A < C, B free} produces. {C} and {B, C} must never appear."""

    def test_partial_order_down_sets(self):
        erratum = erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),
                "B": event(transitions=[transition(kind="ruling")]),
                "C": event(transitions=[transition(kind="functional")]),
            },
            ordering={"chains": [["A", "C"]]},
        )
        selection = erratum.selection_at(day("2010-04-24"))
        got = event_sets(selection)
        self.assertEqual(
            got,
            {
                frozenset(),
                frozenset({"A"}),
                frozenset({"B"}),
                frozenset({"A", "B"}),
                frozenset({"A", "C"}),
                frozenset({"A", "B", "C"}),
            },
        )
        self.assertNotIn(frozenset({"C"}), got)
        self.assertNotIn(frozenset({"B", "C"}), got)


class CooccurrenceV2Test(unittest.TestCase):
    """§9.E: one event, two relevant transitions -> ONE state dimension,
    exactly 2 down-sets, never 4 transition combinations."""

    def test_one_event_two_transitions_is_two_states_not_four(self):
        erratum = erratum_v2_of(
            events={
                "policy-revision": event(
                    effective={"date": None, "basis": "Konami policy revision, exact date unresolved"},
                    transitions=[transition(axis="axis-a"), transition(axis="axis-b")],
                    cooccurrence_sources=["src-cooccurrence"],
                )
            },
            ordering={},
        )
        selection = erratum.selection_at(day("2010-04-24"))
        self.assertEqual(event_sets(selection), {frozenset(), frozenset({"policy-revision"})})


class FullDatedChainV2Test(unittest.TestCase):
    """§9.F: before/between/after a proven-ordered chain -> a single
    determinate HistoricalState each time."""

    def setUp(self):
        self.erratum = erratum_v2_of(
            events={
                "v1": event(effective={"date": "2005-01-01"}, transitions=[transition(kind="functional")]),
                "v2": event(effective={"date": "2010-01-01"}, transitions=[transition(kind="functional")]),
            },
            ordering={"chains": [["v1", "v2"]]},
        )

    def test_before_first_event(self):
        selection = self.erratum.selection_at(day("2000-01-01"))
        self.assertEqual(selection.chronology, "determinate")
        self.assertEqual(event_sets(selection), {frozenset()})

    def test_between_events(self):
        selection = self.erratum.selection_at(day("2007-01-01"))
        self.assertEqual(selection.chronology, "determinate")
        self.assertEqual(event_sets(selection), {frozenset({"v1"})})

    def test_after_final_event(self):
        selection = self.erratum.selection_at(day("2015-01-01"))
        self.assertEqual(selection.chronology, "determinate")
        self.assertEqual(event_sets(selection), {frozenset({"v1", "v2"})})
        self.assertTrue(selection.is_modern)


class SameDateSeparateEventsV2Test(unittest.TestCase):
    """§9.G: two distinct events sharing an exact date, no edge — never a
    mixed candidate merely because they are structurally separate."""

    def test_no_mixed_candidate_around_the_shared_date(self):
        erratum = erratum_v2_of(
            events={
                "A": event(
                    effective={"date": "2015-06-01", "precision": "day"},
                    transitions=[transition(kind="functional")],
                ),
                "B": event(
                    effective={"date": "2015-06-01", "precision": "day"},
                    transitions=[transition(kind="ruling")],
                ),
            },
            ordering={},
        )
        before = erratum.selection_at(day("2015-05-31"))
        on = erratum.selection_at(day("2015-06-01"))
        self.assertEqual(event_sets(before), {frozenset()})
        self.assertEqual(event_sets(on), {frozenset({"A", "B"})})


class CoverageDefaultingV2Test(unittest.TestCase):
    """§9.H: authored states[] used verbatim; any other reachable
    non-terminal state is UNRESOLVED; the terminal state is always
    MODERN, synthesised, never read from an authored entry."""

    def test_defaulting_rules(self):
        erratum = erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),
                "B": event(transitions=[transition(kind="ruling")]),
            },
            ordering={},
            states=[{"events": ["A"], "coverage": coverage(kind="reuse-upstream")}],
        )
        selection = erratum.selection_at(day("2010-04-24"))
        by_events = {c.events: c for c in selection.candidates}
        self.assertEqual(by_events[frozenset()].coverage.kind, Coverage.UNRESOLVED)
        self.assertEqual(by_events[frozenset({"A"})].coverage.kind, Coverage.REUSE_UPSTREAM)
        self.assertEqual(by_events[frozenset({"B"})].coverage.kind, Coverage.UNRESOLVED)
        self.assertEqual(by_events[frozenset({"A", "B"})].coverage.kind, Coverage.MODERN)

    def test_terminal_state_ignores_an_authored_entry(self):
        # Even if a record's own (not-yet-validated) states[] authors a
        # non-modern entry for the all-events down-set, the terminal state
        # is still synthesised MODERN -- catching this is step 3's
        # validator's job, but step 2 must never trust it either way.
        erratum = erratum_v2_of(
            events={"A": event(transitions=[transition(kind="ruling")])},
            ordering={},
            states=[{"events": ["A"], "coverage": coverage(kind="known-gap")}],
        )
        selection = erratum.selection_at(day("2030-01-01"))
        modern_candidates = [c for c in selection.candidates if c.events == frozenset({"A"})]
        self.assertEqual(len(modern_candidates), 1)
        self.assertEqual(modern_candidates[0].coverage.kind, Coverage.MODERN)


class CosmeticEngineFilteringV2Test(unittest.TestCase):
    """§9.I: a cosmetic/engine-only event creates no state dimension; a
    mixed event (ruling + cosmetic) still creates exactly one."""

    def test_cosmetic_only_event_creates_no_dimension(self):
        erratum = erratum_v2_of(
            events={
                "cosmetic-only": event(
                    effective={"date": "2010-01-01"}, transitions=[transition(kind="cosmetic")]
                ),
                "real": event(transitions=[transition(kind="ruling")]),
            },
            ordering={},
        )
        self.assertEqual({e.id for e in erratum.relevant_events()}, {"real"})
        selection = erratum.selection_at(day("2010-04-24"))
        self.assertEqual(event_sets(selection), {frozenset(), frozenset({"real"})})

    def test_engine_only_event_creates_no_dimension(self):
        erratum = erratum_v2_of(
            events={
                "engine-only": event(
                    effective={"date": "2010-01-01"}, transitions=[transition(kind="engine")]
                ),
                "real": event(transitions=[transition(kind="functional")]),
            },
            ordering={},
        )
        self.assertEqual({e.id for e in erratum.relevant_events()}, {"real"})

    def test_mixed_ruling_and_cosmetic_event_is_one_dimension(self):
        erratum = erratum_v2_of(
            events={
                "mixed": event(
                    transitions=[transition(kind="cosmetic"), transition(kind="ruling")],
                    cooccurrence_sources=["src"],
                )
            },
            ordering={},
        )
        self.assertEqual({e.id for e in erratum.relevant_events()}, {"mixed"})
        selection = erratum.selection_at(day("2010-04-24"))
        self.assertEqual(event_sets(selection), {frozenset(), frozenset({"mixed"})})


class TransitivityThroughNonRelevantEventV2Test(unittest.TestCase):
    """§9.J, corrected: relevant A -> cosmetic-only C -> relevant B must
    still induce A-before-B structurally — but a non-relevant event's OWN
    chronology status is a real historical fact too, not merely a graph
    position. This class proves both halves: (1) the induced ORDER survives
    a non-relevant intermediate, and (2) that intermediate's own OLD/NEW
    status, not just its position, further constrains which projected
    candidates are reachable — a distinction the previous, buggy version of
    this test conflated by only checking case (1)."""

    def test_C_confirmed_old_blocks_B_even_though_A_alone_survives(self):
        # §9.C (corrected): at a snapshot where the cosmetic intermediate C
        # is confirmed OLD, {A,B} must NOT be possible -- B transitively
        # requires C, and C being OLD forbids C (and therefore B) from any
        # surviving down-set. Only {} and {A} survive.
        erratum = erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),
                "C": event(effective={"date": "2012-01-01"}, transitions=[transition(kind="cosmetic")]),
                "B": event(transitions=[transition(kind="functional")]),
            },
            ordering={"chains": [["A", "C", "B"]]},
        )
        selection = erratum.selection_at(day("2010-04-24"))  # before C's date: C is OLD
        got = event_sets(selection)
        self.assertEqual(got, {frozenset(), frozenset({"A"})})
        self.assertNotIn(frozenset({"A", "B"}), got)
        self.assertNotIn(frozenset({"B"}), got)

    def test_C_ambiguous_makes_A_B_reachable_again(self):
        # The companion case the task asked for: make C itself AMBIGUOUS
        # (undated) instead of confirmed OLD, so a full state containing C
        # (and therefore {A,B} once projected) becomes reachable again --
        # proving the earlier block was C's chronology, not the mere
        # existence of an intermediate node.
        erratum = erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),
                "C": event(transitions=[transition(kind="cosmetic")]),  # undated -> ambiguous
                "B": event(transitions=[transition(kind="functional")]),
            },
            ordering={"chains": [["A", "C", "B"]]},
        )
        selection = erratum.selection_at(day("2010-04-24"))
        got = event_sets(selection)
        self.assertEqual(got, {frozenset(), frozenset({"A"}), frozenset({"A", "B"})})
        self.assertNotIn(frozenset({"B"}), got)  # B still can never appear without A

    def test_A_non_relevant_new_successor_forces_relevant_predecessor(self):
        # §9's test A: relevant A (ambiguous) -> cosmetic C (confirmed NEW)
        # -- C having definitely happened forces A to have happened too,
        # even though C itself is never a candidate identity.
        erratum = erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),  # undated -> ambiguous
                "C": event(effective={"date": "2005-01-01"}, transitions=[transition(kind="cosmetic")]),
            },
            ordering={"chains": [["A", "C"]]},
        )
        selection = erratum.selection_at(day("2010-04-24"))  # after C's date: C is NEW
        self.assertEqual(event_sets(selection), {frozenset({"A"})})

    def test_B_non_relevant_old_predecessor_blocks_relevant_successor(self):
        # §9's test B: cosmetic C (confirmed OLD) -> relevant B (ambiguous)
        # -- C definitely NOT having happened forbids B from having
        # happened either, forcing the sole projected candidate to {}.
        erratum = erratum_v2_of(
            events={
                "C": event(effective={"date": "2020-01-01"}, transitions=[transition(kind="cosmetic")]),
                "B": event(transitions=[transition(kind="ruling")]),  # undated -> ambiguous
            },
            ordering={"chains": [["C", "B"]]},
        )
        selection = erratum.selection_at(day("2010-04-24"))  # before C's date: C is OLD
        self.assertEqual(event_sets(selection), {frozenset()})

    def test_D_two_non_relevant_intermediates_survive_ordering_and_chronology(self):
        # §9's test D: relevant A -> cosmetic C1 -> engine C2 -> relevant B.
        # Confirm BOTH halves through two layers of non-relevant events:
        # ordering projection (C1/C2 never appear in any candidate) AND
        # chronology propagation (B's reachability tracks C1/C2's own
        # status, not merely their graph position).
        erratum = erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),
                "C1": event(effective={"date": "2020-01-01"}, transitions=[transition(kind="cosmetic")]),
                "C2": event(effective={"date": "2020-06-01"}, transitions=[transition(kind="engine")]),
                "B": event(transitions=[transition(kind="functional")]),
            },
            ordering={"chains": [["A", "C1", "C2", "B"]]},
        )
        # Both C1 and C2 confirmed OLD here -> B (and even C1/C2) blocked.
        before = erratum.selection_at(day("2010-04-24"))
        got_before = event_sets(before)
        self.assertEqual(got_before, {frozenset(), frozenset({"A"})})
        self.assertNotIn(frozenset({"A", "B"}), got_before)
        # Both C1 and C2 confirmed NEW here -> B becomes reachable, and
        # neither C1 nor C2 ever appears as its own projected identity.
        after = erratum.selection_at(day("2021-01-01"))
        got_after = event_sets(after)
        self.assertEqual(got_after, {frozenset({"A"}), frozenset({"A", "B"})})
        for candidate in got_after:
            self.assertNotIn("C1", candidate)
            self.assertNotIn("C2", candidate)

    def test_E_unordered_non_relevant_events_do_not_fork_candidates(self):
        # §9's test E: an unordered, permanently-ambiguous cosmetic event
        # with no ordering relation to anything doubles the FULL down-set
        # space ({X} vs no-X for every combination) but must NOT double the
        # number of distinct PROJECTED HistoricalState identities -- dedup
        # must collapse X's own undetermined status.
        erratum = erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),  # undated -> ambiguous
                "X": event(transitions=[transition(kind="cosmetic")]),  # undated -> ambiguous, unordered
            },
            ordering={},
        )
        selection = erratum.selection_at(day("2010-04-24"))
        self.assertEqual(event_sets(selection), {frozenset(), frozenset({"A"})})


class NonRelevantEventFactsAreNotDiscardedTest(unittest.TestCase):
    """§5's adversarial principle, tested directly: "does removing an
    event from HistoricalState identity accidentally remove facts about
    whether that historical event occurred?" The answer must be no —
    proved here by holding every RELEVANT event's own chronology fixed
    and changing ONLY a cosmetic event's chronology, then showing the
    projected candidate set changes anyway, purely because of a fact
    about an event that never appears in any candidate's identity."""

    def _erratum(self, cosmetic_date: str | None) -> ErratumV2:
        return erratum_v2_of(
            events={
                "A": event(transitions=[transition(kind="ruling")]),  # undated -> ambiguous, always
                "cosmetic-gate": event(
                    effective={"date": cosmetic_date}, transitions=[transition(kind="cosmetic")]
                ),
            },
            ordering={"chains": [["A", "cosmetic-gate"]]},
        )

    def test_cosmetic_events_own_status_still_changes_the_projected_result(self):
        undetermined = self._erratum(cosmetic_date=None)  # cosmetic-gate always AMBIGUOUS
        confirmed_new = self._erratum(cosmetic_date="2005-01-01")  # NEW well before the snapshot

        snapshot = day("2010-04-24")
        undetermined_candidates = event_sets(undetermined.selection_at(snapshot))
        confirmed_candidates = event_sets(confirmed_new.selection_at(snapshot))

        # "A" alone is never provably excluded/required while cosmetic-gate
        # is merely ambiguous (both {} and {A} survive)...
        self.assertEqual(undetermined_candidates, {frozenset(), frozenset({"A"})})
        # ...but once cosmetic-gate is CONFIRMED to have happened, A (its
        # sole predecessor) is thereby forced to have happened too, even
        # though cosmetic-gate itself is never part of either candidate
        # set's identity. The fact was never in HistoricalState.events, but
        # it was never discarded either -- it still changed the answer.
        self.assertEqual(confirmed_candidates, {frozenset({"A"})})
        self.assertNotEqual(undetermined_candidates, confirmed_candidates)


class SugarFullV2EquivalenceTest(unittest.TestCase):
    """§12 adversarial checklist: the flattened sugar must desugar into
    exactly the same selection semantics as the equivalent full v2 shape,
    at every snapshot, not merely the same shape of output."""

    def test_sugar_and_full_v2_select_identically(self):
        full = erratum_v2_of(
            id="full",
            events={
                "e1": event(
                    effective={"date": "2015-06-01", "precision": "day"},
                    transitions=[transition(kind="functional", summary="x")],
                )
            },
            ordering={},
            states=[{"events": [], "coverage": coverage(kind="reuse-upstream")}],
        )
        sugar = ErratumV2.load(
            {
                "id": "sugar",
                "modern_card": {"passcode": 200, "name": "Beta"},
                "classification": "functional",
                "event": {
                    "effective": {"date": "2015-06-01", "precision": "day"},
                    "kind": "functional",
                    "summary": "x",
                    "sources": ["test-source"],
                },
                "coverage": coverage(kind="reuse-upstream"),
                "sources": ["test-source"],
            },
            Path("sugar.json"),
        )
        def shape(selection):
            # Event ids are record-local — "e1" in one record and "event"
            # in another are never meant to compare equal. What must match
            # is the STRUCTURE: is this candidate baseline ({}) or terminal
            # (non-empty), and what coverage does it carry.
            return {(bool(c.events), c.coverage.kind) for c in selection.candidates}

        for snapshot in (day("2010-01-01"), day("2015-06-01"), day("2020-01-01")):
            full_sel = full.selection_at(snapshot)
            sugar_sel = sugar.selection_at(snapshot)
            self.assertEqual(full_sel.chronology, sugar_sel.chronology)
            self.assertEqual(shape(full_sel), shape(sugar_sel))


class StateIdentityIsEventSetTest(unittest.TestCase):
    """§12 adversarial checklist: helpers must compare `.events`, never
    whole-object identity/equality — two independently-built states with
    the same event-set but different label/coverage must still compare
    as "the same state" wherever identity, not description, is what
    matters."""

    def test_is_modern_uses_event_set_not_whole_object_equality(self):
        modern_marker = HistoricalState(
            events=frozenset({"x"}), label="modern-label", coverage=ImplementationCoverage.modern()
        )
        actual_candidate = HistoricalState(
            events=frozenset({"x"}),
            label="a completely different label",
            coverage=ImplementationCoverage(kind=Coverage.UNRESOLVED),
        )
        self.assertEqual(modern_marker.events, actual_candidate.events)
        self.assertNotEqual(modern_marker, actual_candidate)  # whole-object equality differs
        selection = SemanticErratumSelection(
            chronology="determinate", candidates=(actual_candidate,), modern_state=modern_marker
        )
        self.assertTrue(selection.is_modern)
        self.assertTrue(selection.modern_is_possible)


class CandidateOrderingIsDeterministicTest(unittest.TestCase):
    """§6: candidate order is deterministic (size, then sorted ids) —
    never JSON/dict declaration order."""

    def test_candidates_ordered_by_size_then_sorted_ids(self):
        erratum = erratum_v2_of(
            events={
                "z-event": event(transitions=[transition(kind="ruling")]),
                "a-event": event(transitions=[transition(kind="ruling")]),
            },
            ordering={},
        )
        selection = erratum.selection_at(day("2010-04-24"))
        ordered = [tuple(sorted(c.events)) for c in selection.candidates]
        self.assertEqual(ordered, sorted(ordered, key=lambda t: (len(t), t)))


class MalformedV2InputTest(unittest.TestCase):
    """§7/§12: a clear, defined failure — never an invented answer — for
    structurally unusable (cyclic/dangling) or chronologically
    contradictory synthetic input. Step 3's validator invariants are what
    should keep real records from ever reaching either case."""

    def test_cyclic_ordering_raises_data_error(self):
        with self.assertRaises(DataError):
            erratum_v2_of(
                events={
                    "A": event(transitions=[transition(kind="ruling")]),
                    "B": event(transitions=[transition(kind="ruling")]),
                },
                ordering={
                    "edges": [
                        {"before": "A", "after": "B", "basis": "researcher-inference", "note": "x"},
                        {"before": "B", "after": "A", "basis": "researcher-inference", "note": "y"},
                    ]
                },
            )

    def test_dangling_ordering_reference_raises_data_error(self):
        with self.assertRaises(DataError):
            erratum_v2_of(
                events={"A": event(transitions=[transition(kind="ruling")])},
                ordering={
                    "edges": [
                        {
                            "before": "A",
                            "after": "does-not-exist",
                            "basis": "researcher-inference",
                            "note": "x",
                        }
                    ]
                },
            )

    def test_contradictory_chronology_raises_selection_error(self):
        # ordering.chains asserts A before B, but the dates say B is
        # already confirmed NEW while A (which B's declared order requires
        # to have already happened) is still confirmed OLD -- impossible
        # under the declared order. Every down-set is excluded.
        erratum = erratum_v2_of(
            events={
                "A": event(effective={"date": "2020-01-01"}, transitions=[transition(kind="functional")]),
                "B": event(effective={"date": "2010-01-01"}, transitions=[transition(kind="functional")]),
            },
            ordering={"chains": [["A", "B"]]},
        )
        with self.assertRaises(SelectionError):
            erratum.selection_at(day("2015-01-01"))


class ShapeDispatchTest(unittest.TestCase):
    """§3: structural dispatch by top-level key, mutually exclusive by
    schema construction — never a heuristic."""

    def test_changes_dispatches_to_legacy_erratum(self):
        raw = {
            "id": "erratum-v1-dispatch",
            "modern_card": {"passcode": 1, "name": "X"},
            "classification": "functional",
            "changes": [
                {
                    "kind": "functional",
                    "effective": {"date": "2020-01-01"},
                    "summary": "s",
                    "sources": ["s"],
                }
            ],
            "implementation": {"strategy": "none-needed", "status": "complete"},
            "sources": ["s"],
        }
        record = load_erratum_record(raw, Path("x.json"))
        self.assertIsInstance(record, Erratum)

    def test_events_dispatches_to_v2(self):
        raw = {
            "id": "erratum-v2-dispatch",
            "modern_card": {"passcode": 2, "name": "Y"},
            "classification": "ruling",
            "events": {"e1": event(transitions=[transition(kind="ruling")])},
            "ordering": {},
            "sources": ["s"],
        }
        record = load_erratum_record(raw, Path("x.json"))
        self.assertIsInstance(record, ErratumV2)

    def test_event_sugar_dispatches_to_v2(self):
        raw = {
            "id": "erratum-sugar-dispatch",
            "modern_card": {"passcode": 3, "name": "Z"},
            "classification": "functional",
            "event": {
                "effective": {"date": "2020-01-01"},
                "kind": "functional",
                "summary": "s",
                "sources": ["s"],
            },
            "coverage": coverage(kind="none-needed"),
            "sources": ["s"],
        }
        record = load_erratum_record(raw, Path("x.json"))
        self.assertIsInstance(record, ErratumV2)

    def _base_raw(self) -> dict:
        return {
            "id": "erratum-shape-conflict",
            "modern_card": {"passcode": 9, "name": "W"},
            "classification": "functional",
            "sources": ["s"],
        }

    def test_changes_and_events_both_present_is_rejected(self):
        raw = self._base_raw()
        raw["changes"] = [
            {"kind": "functional", "effective": {"date": "2020-01-01"}, "summary": "s", "sources": ["s"]}
        ]
        raw["implementation"] = {"strategy": "none-needed", "status": "complete"}
        raw["events"] = {"e1": event(transitions=[transition(kind="ruling")])}
        raw["ordering"] = {}
        with self.assertRaises(DataError):
            load_erratum_record(raw, Path("x.json"))

    def test_changes_and_event_both_present_is_rejected(self):
        raw = self._base_raw()
        raw["changes"] = [
            {"kind": "functional", "effective": {"date": "2020-01-01"}, "summary": "s", "sources": ["s"]}
        ]
        raw["implementation"] = {"strategy": "none-needed", "status": "complete"}
        raw["event"] = {"effective": {"date": "2020-01-01"}, "kind": "functional", "summary": "s", "sources": ["s"]}
        raw["coverage"] = coverage(kind="none-needed")
        with self.assertRaises(DataError):
            load_erratum_record(raw, Path("x.json"))

    def test_events_and_event_both_present_is_rejected(self):
        raw = self._base_raw()
        raw["events"] = {"e1": event(transitions=[transition(kind="ruling")])}
        raw["ordering"] = {}
        raw["event"] = {"effective": {"date": "2020-01-01"}, "kind": "functional", "summary": "s", "sources": ["s"]}
        raw["coverage"] = coverage(kind="none-needed")
        with self.assertRaises(DataError):
            load_erratum_record(raw, Path("x.json"))

    def test_changes_events_and_event_all_present_is_rejected(self):
        raw = self._base_raw()
        raw["changes"] = [
            {"kind": "functional", "effective": {"date": "2020-01-01"}, "summary": "s", "sources": ["s"]}
        ]
        raw["implementation"] = {"strategy": "none-needed", "status": "complete"}
        raw["events"] = {"e1": event(transitions=[transition(kind="ruling")])}
        raw["ordering"] = {}
        raw["event"] = {"effective": {"date": "2020-01-01"}, "kind": "functional", "summary": "s", "sources": ["s"]}
        raw["coverage"] = coverage(kind="none-needed")
        with self.assertRaises(DataError):
            load_erratum_record(raw, Path("x.json"))

    def test_none_of_the_three_discriminators_is_rejected(self):
        raw = self._base_raw()
        with self.assertRaises(DataError):
            load_erratum_record(raw, Path("x.json"))


if __name__ == "__main__":
    unittest.main()


class CosmeticEngineSugarRuntimeTest(unittest.TestCase):
    """The runtime half of the sugar restriction. `Repository.load()` parses
    records BEFORE any JSON Schema check runs, so the parser must refuse
    cosmetic/engine sugar itself rather than rely on the schema - and the
    full-v2 equivalent must load with no implementation dimension at all."""

    @staticmethod
    def _sugar(kind: str) -> dict:
        return {
            "id": "erratum-sugar-kind",
            "modern_card": {"passcode": 200, "name": "Beta"},
            "classification": kind,
            "event": {
                "effective": {"date": "2011-07-01"},
                "kind": kind,
                "summary": "x",
                "sources": ["s"],
            },
            "coverage": {"kind": "none-needed"},
            "sources": ["s"],
        }

    @staticmethod
    def _full(kind: str) -> dict:
        return {
            "id": "erratum-full-kind",
            "modern_card": {"passcode": 200, "name": "Beta"},
            "classification": kind,
            "events": {
                "e1": {
                    "effective": {"date": "2011-07-01"},
                    "transitions": [{"kind": kind, "summary": "x", "sources": ["s"]}],
                }
            },
            "ordering": {},
            "sources": ["s"],
        }

    def test_cosmetic_sugar_is_rejected_at_load(self):
        with self.assertRaises(DataError) as ctx:
            load_erratum_record(self._sugar("cosmetic"), Path("x.json"))
        self.assertIn("functional/ruling", str(ctx.exception))

    def test_engine_sugar_is_rejected_at_load(self):
        with self.assertRaises(DataError):
            load_erratum_record(self._sugar("engine"), Path("x.json"))

    def test_functional_sugar_still_loads(self):
        record = load_erratum_record(self._sugar("functional"), Path("x.json"))
        self.assertEqual(1, len(record.relevant_events()))

    def test_full_v2_cosmetic_has_no_implementation_dimension(self):
        record = load_erratum_record(self._full("cosmetic"), Path("x.json"))
        self.assertEqual((), record.relevant_events())
        self.assertFalse(record.has_implementation_relevant_history())
        # Exactly one structural state, and it IS the terminal one, so its
        # coverage is the synthesised MODERN - no historical state exists.
        self.assertEqual((frozenset(),), record.structural_states())
        self.assertEqual(Coverage.MODERN, record.state_for(frozenset()).coverage.kind)

    def test_full_v2_engine_has_no_implementation_dimension(self):
        record = load_erratum_record(self._full("engine"), Path("x.json"))
        self.assertEqual((), record.relevant_events())
        self.assertEqual((frozenset(),), record.structural_states())
        self.assertEqual(Coverage.MODERN, record.state_for(frozenset()).coverage.kind)
