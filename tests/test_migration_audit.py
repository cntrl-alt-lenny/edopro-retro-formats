"""The v1 -> v2 migration audit, as a test rather than a number in prose.

`docs/research/erratum-v2-migration-audit.md` reports a partition of the
296-record corpus. That partition is DERIVED by `tests/migration_audit.py`
from the current runtime, and these tests keep the derivation honest.

**Corrected pass.** The prior version of this file locked in a false
296-of-296 equivalence claim, produced by a comparator that reduced a v2
ambiguous candidate to `len(candidate.events)` and compared that INTEGER
against v1's positional candidate index - silently equating `{A}` and `{B}`
because both have size 1. `CardinalityCollapseRegressionTest` below pins the
exact shape of that bug so it cannot return unnoticed. The corrected
comparator is a genuine SET comparison of (event-identity, coverage-
signature) pairs, and it reproduces the frozen design document's own
247-safe / 49-nontrivial / 48-self-contradictory partition exactly, with
YZ-Tank Dragon as the sole record in the 49 that is not in the 48 - matching
`docs/research/erratum-state-model-v2.md` section 7 by name.
"""

from __future__ import annotations

import datetime as _dt
import itertools
import unittest
from pathlib import Path

from retroformats.model import (
    AMBIGUOUS,
    NEW,
    OLD,
    PROVEN,
    Erratum,
    ErratumV2,
    change_state_at,
    ordering_proof,
)
from retroformats.repo import Repository

from . import migration_audit as audit
from .migration_audit import (
    CAT_COSMETIC_ONLY,
    CAT_FULL_SINGLE,
    CAT_MANUAL_REVIEW,
    CAT_MULTI_ORDERED,
    CAT_PARITY_ONLY,
    CAT_RESEARCHED_NONTRIVIAL,
    CAT_SUGAR,
    MANUAL_REVIEW_IDS,
    ORDER_FULL,
    ORDER_NONE,
    ORDER_SINGLE,
    ORDER_ZERO,
    RESEARCH_ALREADY_RESEARCHED,
    RESEARCH_NEEDS_MANUAL_REVIEW,
    audit_corpus,
    candidate_v2,
    v1_claimed_states,
    v2_claimed_states,
)


class MigrationAuditPartitionTest(unittest.TestCase):
    """The derived partition the report publishes. If a canonical record
    changes shape, these numbers move and the report must be re-derived -
    which is the point of computing rather than asserting them.

    **The equivalence count is 247, not 296.** The prior pass's 296/296 was
    a comparator bug (see module docstring); this is the corrected, derived
    output, and it exactly reproduces the frozen design document's own
    figures - it was neither assumed as an input nor forced to match."""

    @classmethod
    def setUpClass(cls):
        cls.result = audit_corpus()
        cls.rows = cls.result["rows"]
        cls.summary = cls.result["summary"]
        cls.by_id = {r["id"]: r for r in cls.rows}

    def test_every_v1_record_is_covered(self):
        self.assertEqual(296, self.summary["records"])
        self.assertEqual(296, len(self.rows))

    def test_equivalence_reproduces_the_frozen_247_49_split(self):
        self.assertEqual(247, self.summary["equivalent"])
        self.assertEqual(49, self.summary["not_equivalent"])

    def test_legacy_self_contradiction_reproduces_the_frozen_48(self):
        """Design doc section 7's exact, independently-implemented test -
        not a copy of the equivalence result, a different computation that
        happens to be checked against the same frozen figure."""
        self.assertEqual(48, self.summary["legacy_self_contradictory_count"])

    def test_yz_tank_dragon_is_the_sole_49_minus_48_exception(self):
        """Design doc section 7, verbatim: 'the sole exception, at every
        snapshot, forever, is YZ-Tank Dragon' - in the 49 (not equivalent),
        never in the 48 (never self-contradictory, only ever incomplete)."""
        not_equivalent = set(self.summary["not_equivalent_ids"])
        self_contradictory = set(self.summary["legacy_self_contradictory_ids"])
        self.assertEqual({"erratum-yz-tank-dragon"}, not_equivalent - self_contradictory)
        self.assertEqual(set(), self_contradictory - not_equivalent, "48 must be a subset of 49")

    def test_named_examples_from_the_design_document_are_in_the_48(self):
        """Section 7 names these explicitly as part of the 48 (the 44 from
        the Edison audit plus Sangan, Witch of the Black Forest, Insect
        Imitation, Last Will)."""
        for rid in (
            "erratum-giant-rat",
            "erratum-sangan",
            "erratum-witch-of-the-black-forest",
            "erratum-insect-imitation",
            "erratum-last-will",
        ):
            self.assertTrue(self.by_id[rid]["legacy_self_contradictory"], rid)
            self.assertFalse(self.by_id[rid]["equivalent"], rid)

    def test_trivial_236_matches_the_frozen_taxonomy(self):
        """0-1 relevant changes: design doc's '236 trivial'."""
        trivial = [r for r in self.rows if r["relevant_event_count"] <= 1]
        self.assertEqual(236, len(trivial))

    def test_ordering_structure_reproduces_the_frozen_11_fully_ordered(self):
        """'Has a proven edge' is NOT 'fully ordered' (a 3-event partial
        order would have one but not be total) - this counts records whose
        relevant-event down-set space is a single total chain."""
        self.assertEqual(11, self.summary["ordering_structure"].get(ORDER_FULL, 0))
        fully_ordered = sorted(r["id"] for r in self.rows if r["ordering_structure"] == ORDER_FULL)
        self.assertEqual(
            [
                "erratum-blackwing-sirocco-the-dawn",
                "erratum-blue-eyes-toon-dragon",
                "erratum-blue-eyes-ultimate-dragon",
                "erratum-dark-necrofear",
                "erratum-necrovalley",
                "erratum-night-assailant",
                "erratum-rescue-cat",
                "erratum-soul-rope",
                "erratum-swords-of-concealing-light",
                "erratum-toon-mermaid",
                "erratum-toon-summoned-skull",
            ],
            fully_ordered,
        )
        for rid in fully_ordered:
            self.assertTrue(self.by_id[rid]["equivalent"], rid)

    def test_ordering_structure_never_conflates_any_edge_with_fully_ordered(self):
        """Every non-trivial (2+ relevant event) record that is NOT fully
        ordered has EITHER zero proven edges among its relevant events, OR a
        genuine partial order - the audit reports which, rather than
        assuming 'has an edge' implies a total one."""
        for r in self.rows:
            if r["relevant_event_count"] < 2:
                continue
            self.assertIn(r["ordering_structure"], (ORDER_FULL, ORDER_NONE, "partial-order"), r["id"])
            if r["ordering_structure"] == ORDER_FULL:
                self.assertEqual(r["relevant_event_count"] + 1, r["structural_state_count"], r["id"])
            elif r["ordering_structure"] == ORDER_NONE:
                self.assertEqual(2 ** r["relevant_event_count"], r["structural_state_count"], r["id"])

    def test_partition_counts(self):
        """The 49 not-equivalent records are NOT uniformly manual-review:
        only the 2 the design document names by name are. The other 47
        already have a documented (if not further-subdivided) research
        classification."""
        self.assertEqual(
            {
                CAT_SUGAR: 180,
                CAT_FULL_SINGLE: 35,
                CAT_MULTI_ORDERED: 11,
                CAT_RESEARCHED_NONTRIVIAL: 47,
                CAT_MANUAL_REVIEW: 2,
                CAT_PARITY_ONLY: 11,
                CAT_COSMETIC_ONLY: 10,
            },
            self.summary["categories"],
        )
        self.assertEqual(296, sum(self.summary["categories"].values()))

    def test_current_migration_readiness_accounting(self):
        """Equivalence (247) is necessary, not sufficient: 236 of them have
        no known chronology/shape obstacle once the 11 parity-only records
        are set aside - but that is NOT a data-preservation or
        migration-safety certification (v1 metadata with no v2
        destination affects them too), and the bookkeeping must say so
        explicitly rather than reporting '247 safe to migrate' or '236
        immediately migratable'."""
        self.assertEqual(247, self.summary["semantic_equivalent"])
        self.assertEqual(236, self.summary["chronology_shape_ready"])
        self.assertEqual(236, len(self.summary["chronology_shape_ready_ids"]))
        self.assertEqual(11, self.summary["parity_only_blocked"])
        self.assertEqual(236 + 11, self.summary["semantic_equivalent"])
        self.assertEqual(49, self.summary["nontrivial_migration_scope"])
        self.assertEqual(47, self.summary["nontrivial_already_researched"])
        self.assertEqual(2, self.summary["nontrivial_needs_manual_review"])
        self.assertEqual(
            ["erratum-insect-imitation", "erratum-last-will"],
            self.summary["nontrivial_needs_manual_review_ids"],
        )
        self.assertEqual(47 + 2, self.summary["nontrivial_migration_scope"])

    def test_representation_implemented_but_not_migrated(self):
        """Both representation gaps now have a v2 destination
        (implementation_metadata[]/reference_identities[]) and this
        audit's own candidate construction verifies every record's v1
        metadata/identity round-trips into them - but `chronology_shape_
        ready=236` must still never be read as 'migrated': no
        data/errata/*.json record has actually changed."""
        self.assertEqual("representation-implemented-not-migrated", self.summary["data_preservation_status"])
        self.assertEqual(0, self.summary["parity_only_unrepresented_count"])
        self.assertEqual(0, self.summary["metadata_unrepresented_count"])
        self.assertEqual([], self.summary["metadata_not_preserved_ids"])
        self.assertEqual([], self.summary["reference_identity_not_preserved_ids"])
        self.assertEqual([], self.summary["data_not_preserved_ids"])
        detail = self.summary["data_preservation_status_detail"]
        self.assertIn("No data/errata/*.json record has been migrated", detail)
        self.assertNotIn("immediately_migratable", self.summary)

    def test_all_247_equivalent_records_pass_full_representation_preservation(self):
        """The task's own required check: every one of the 247
        semantically-equivalent records' candidate v2 preserves everything
        `_data_preserved()` checks (transitions, coverage, metadata,
        reference identity)."""
        for row in self.rows:
            if row["equivalent"]:
                self.assertTrue(row["data_preserved"], row["id"])
                self.assertTrue(row["coverage_preserved"], row["id"])
                self.assertTrue(row["metadata_preserved"], row["id"])
                self.assertTrue(row["reference_identity_preserved"], row["id"])

    def test_manual_review_ids_match_the_design_document(self):
        self.assertEqual({"erratum-insect-imitation", "erratum-last-will"}, MANUAL_REVIEW_IDS)
        for rid in MANUAL_REVIEW_IDS:
            self.assertEqual(CAT_MANUAL_REVIEW, self.by_id[rid]["category"])
            self.assertEqual(RESEARCH_NEEDS_MANUAL_REVIEW, self.by_id[rid]["research_status"])
        for row in self.rows:
            if row["category"] == CAT_RESEARCHED_NONTRIVIAL:
                self.assertNotIn(row["id"], MANUAL_REVIEW_IDS)
                self.assertEqual(RESEARCH_ALREADY_RESEARCHED, row["research_status"])

    def test_sugar_eligibility_requires_one_event_in_total(self):
        """Under full-event semantics every change is an event, including
        cosmetic/engine ones - so a record with one RELEVANT change but a
        cosmetic change beside it has two events and cannot use single-event
        sugar. This is why sugar-eligibility is 180, not the 236 records
        that merely have <=1 relevant change."""
        self.assertEqual(180, self.summary["sugar_eligible_count"])
        for row in self.rows:
            if row["sugar_eligible"]:
                self.assertEqual(1, row["event_count"], row["id"])
                self.assertEqual(1, row["relevant_event_count"], row["id"])
                self.assertEqual(ORDER_SINGLE, row["ordering_structure"], row["id"])

    def test_parity_only_records_are_named_exactly(self):
        ids = sorted(r["id"] for r in self.rows if r["category"] == CAT_PARITY_ONLY)
        self.assertEqual(
            [
                "erratum-bubble-crash",
                "erratum-chaosrider-gustaph",
                "erratum-cipher-soldier",
                "erratum-dark-jeroid",
                "erratum-injection-fairy-lily",
                "erratum-kazejin",
                "erratum-mirage-knight",
                "erratum-nobleman-of-crossout",
                "erratum-nobleman-of-extermination",
                "erratum-shinato-king-of-a-higher-plane",
                "erratum-suijin",
            ],
            ids,
        )
        for rid in ids:
            self.assertEqual(ORDER_ZERO, self.by_id[rid]["ordering_structure"], rid)

    def test_data_is_never_silently_dropped_by_construction(self):
        """historical_text/modern_text/summary/sources survive candidate
        construction for every one of the 296 records."""
        self.assertEqual([], self.summary["data_not_preserved_ids"])
        for row in self.rows:
            self.assertTrue(row["data_preserved"], row["id"])

    def test_necrovalley_is_the_safe_fully_ordered_worked_example(self):
        row = self.by_id["erratum-necrovalley"]
        self.assertTrue(row["equivalent"])
        self.assertEqual(ORDER_FULL, row["ordering_structure"])
        self.assertEqual(4, row["relevant_event_count"])
        self.assertEqual(CAT_MULTI_ORDERED, row["category"])

    def test_a_sugar_eligible_one_change_record_is_safe(self):
        row = self.by_id["erratum-a-cat-of-ill-omen"]
        self.assertTrue(row["equivalent"])
        self.assertTrue(row["sugar_eligible"])
        self.assertEqual(CAT_SUGAR, row["category"])


class GiantRatWorkedExampleTest(unittest.TestCase):
    """Section 5/11's required worked counterexample. At Edison
    (2010-04-24): v1's positional label '1' claims the FIRST relevant
    change (verification) occurred - but verification's own chronology is
    independently confirmed OLD (old_attested_through 2011-02-02) at that
    date, so v1's claim is impossible. v2's real chronology instead proves
    only the SECOND relevant change (activation, fully undated) is
    plausible. Equal cardinality (both length-1 event-sets), different
    identity - exactly the bug the corrected comparator exists to catch."""

    EDISON = _dt.date(2010, 4, 24)

    @classmethod
    def setUpClass(cls):
        repo = Repository.load(audit.REPO_ROOT)
        cls.record = repo.errata["erratum-giant-rat"]
        cls.v2 = candidate_v2(cls.record)
        cls.row = audit.compare(cls.record)

    def test_not_equivalent_and_self_contradictory(self):
        self.assertFalse(self.row["equivalent"])
        self.assertTrue(self.row["legacy_self_contradictory"])
        # Giant Rat is not one of the design document's 2 named
        # manual-review records - it already has a documented research
        # classification (the Edison-audit "bundled" taxonomy).
        self.assertEqual(CAT_RESEARCHED_NONTRIVIAL, self.row["category"])
        self.assertNotIn(self.record.id, MANUAL_REVIEW_IDS)

    def test_v1_claims_verification_v2_proves_activation(self):
        v1_states = v1_claimed_states(self.record, self.EDISON)
        v2_states = v2_claimed_states(self.v2, self.EDISON)
        self.assertNotEqual(v1_states, v2_states)
        v1_singleton = next(events for events, _ in v1_states if len(events) == 1)
        v2_singleton = next(events for events, _ in v2_states if len(events) == 1)
        self.assertEqual(1, len(v1_singleton))
        self.assertEqual(1, len(v2_singleton))
        self.assertNotEqual(v1_singleton, v2_singleton, "same cardinality, different identity")
        # v1's claimed singleton is c0 (verification, listed first); v2's
        # real singleton is c1 (activation) - verification is independently
        # confirmed OLD at Edison, so v1's claim is not just unproven, it is
        # impossible.
        self.assertEqual(frozenset({"c0"}), v1_singleton)
        self.assertEqual(frozenset({"c1"}), v2_singleton)

    def test_giant_rat_baseline_states_do_agree(self):
        """The mismatch is specific to the ambiguous singleton, not total -
        both sides agree the empty (pre-errata baseline) state is possible
        and reuse-upstream 504700172."""
        v1_states = v1_claimed_states(self.record, self.EDISON)
        v2_states = v2_claimed_states(self.v2, self.EDISON)
        baseline = (frozenset(), ("reuse-upstream", 504700172, ()))
        self.assertIn(baseline, v1_states)
        self.assertIn(baseline, v2_states)


class CardinalityCollapseRegressionTest(unittest.TestCase):
    """The exact defect this correction fixes, isolated from any real
    record: two states of equal SIZE but different IDENTITY must never
    compare equal. The prior comparator computed `len(candidate.events)`
    and compared THAT - {A} and {B} both have length 1, so it silently
    treated them as the same state."""

    def test_equal_size_different_identity_states_compare_unequal(self):
        a_state = (frozenset({"c0"}), ("reuse-upstream", 1, ()))
        b_state = (frozenset({"c1"}), ("reuse-upstream", 1, ()))
        self.assertEqual(len(a_state[0]), len(b_state[0]), "same cardinality...")
        self.assertNotEqual(a_state, b_state, "...but not the same state")
        self.assertNotEqual({a_state}, {b_state})

    def test_cardinality_alone_would_have_missed_giant_rat(self):
        """Reproduces the OLD bug's exact reduction, to prove it WOULD have
        called Giant Rat's mismatched states equal."""
        repo = Repository.load(audit.REPO_ROOT)
        record = repo.errata["erratum-giant-rat"]
        v2 = candidate_v2(record)
        edison = _dt.date(2010, 4, 24)
        v1_sizes = sorted(len(events) for events, _ in v1_claimed_states(record, edison))
        v2_sizes = sorted(len(events) for events, _ in v2_claimed_states(v2, edison))
        self.assertEqual(v1_sizes, v2_sizes, "the old bug's cardinality view saw no difference")
        v1_states = v1_claimed_states(record, edison)
        v2_states = v2_claimed_states(v2, edison)
        self.assertNotEqual(v1_states, v2_states, "the corrected identity view does")


class YZTankDragonMissingStateTest(unittest.TestCase):
    """Design doc section 7's other worked counterexample. v1's positional
    model over two relevant changes offers exactly three candidates -
    prefixes `{}`, `{first}`, `{first,second}` - and structurally cannot
    express `{second}` alone. v2's real down-set space over two genuinely
    unordered events is the full power set: all four subsets are
    structurally reachable. YZ-Tank Dragon is undated on both events, so it
    is never self-contradictory (no independent confirmation ever
    disagrees with any v1 candidate) - it is merely INCOMPLETE, a different
    defect from the 48's."""

    @classmethod
    def setUpClass(cls):
        repo = Repository.load(audit.REPO_ROOT)
        cls.record = repo.errata["erratum-yz-tank-dragon"]
        cls.relevant_indices = audit._relevant_indices(cls.record)
        cls.v2 = candidate_v2(cls.record)
        cls.row = audit.compare(cls.record)

    def test_not_equivalent_but_never_self_contradictory(self):
        self.assertFalse(self.row["equivalent"])
        self.assertFalse(self.row["legacy_self_contradictory"])

    def test_v2_structural_state_space_is_the_full_power_set(self):
        self.assertEqual(2, len(self.relevant_indices))
        self.assertEqual(4, len(self.v2.structural_states()))
        self.assertEqual(audit.ORDER_NONE, self.row["ordering_structure"])

    def test_v1_can_never_claim_the_second_event_alone(self):
        second_only = frozenset({audit._event_id(self.relevant_indices[1])})
        self.assertIn(second_only, self.v2.structural_states())
        claimable = set()
        for day in audit.boundary_dates(self.record):
            for events, _ in v1_claimed_states(self.record, day):
                claimable.add(events)
        self.assertNotIn(second_only, claimable)


class SanganAndWitchWorkedExamplesTest(unittest.TestCase):
    """Section 5's other two required worked records: both fully dated, and
    still not fully ordered (the ordering test finds no PROVEN relation
    between the ruling change and the later functional/cosmetic ones, since
    the ruling change's own attestation window - 2011-02-02..2019-04-03 -
    overlaps the other changes' exact dates in neither direction)."""

    @classmethod
    def setUpClass(cls):
        repo = Repository.load(audit.REPO_ROOT)
        cls.rows = {
            rid: audit.compare(repo.errata[rid])
            for rid in ("erratum-sangan", "erratum-witch-of-the-black-forest")
        }

    def test_neither_is_equivalent_and_both_are_self_contradictory(self):
        for row in self.rows.values():
            self.assertFalse(row["equivalent"])
            self.assertTrue(row["legacy_self_contradictory"])

    def test_dated_does_not_imply_ordered(self):
        """Both records ARE fully dated, and both still have every relevant
        subset structurally reachable (no proven order among the RELEVANT
        events) - `proven_edge_count` alone is not the right check, since a
        cosmetic sibling change can carry its own proven edge without
        constraining the relevant events at all; `ordering_structure` is."""
        for row in self.rows.values():
            self.assertEqual(audit.ORDER_NONE, row["ordering_structure"])
            self.assertEqual(2 ** row["relevant_event_count"], row["structural_state_count"])


class ParityOnlyIdentityIsUnrepresentableTest(unittest.TestCase):
    """A record with zero implementation-relevant events has exactly one
    structural state, `{}`, which IS the terminal state - so its coverage is
    unconditionally MODERN and any authored historical identity is silently
    discarded. v2 as frozen cannot carry these identities. Unaffected by the
    comparator correction (these records have no relevant events to compare)
    - re-verified here rather than assumed."""

    @staticmethod
    def _zero_relevant_v2() -> ErratumV2:
        return ErratumV2.load(
            {
                "id": "erratum-parity-only",
                "modern_card": {"passcode": 71044499, "name": "Nobleman of Crossout"},
                "classification": "cosmetic",
                "events": {
                    "psct": {
                        "effective": {"date": "2012-06-01"},
                        "transitions": [
                            {"kind": "cosmetic", "summary": "wording", "sources": ["s"]}
                        ],
                    }
                },
                "ordering": {},
                # An author TRYING to record the parity identity anyway:
                "states": [
                    {
                        "events": [],
                        "coverage": {
                            "kind": "reuse-upstream",
                            "historical_passcode": 504700116,
                            "upstream": "ProjectIgnis",
                        },
                    }
                ],
                "sources": ["s"],
            },
            Path("x.json"),
        )

    def test_authored_identity_is_discarded_because_baseline_is_terminal(self):
        from retroformats.model import Coverage

        record = self._zero_relevant_v2()
        self.assertEqual((), record.relevant_events())
        self.assertEqual((frozenset(),), record.structural_states())
        self.assertEqual(Coverage.MODERN, record.state_for(frozenset()).coverage.kind)

    def test_parity_walk_can_never_find_it(self):
        from retroformats.lflist import _v2_parity_walk_override

        self.assertIsNone(_v2_parity_walk_override(self._zero_relevant_v2()))


class AuditSensitivityTest(unittest.TestCase):
    """"49 of 296 not equivalent" is only meaningful if the comparison could
    have said otherwise for records the real migration would never produce.
    This constructs a record where FULL-event semantics genuinely differ
    from relevant-only semantics - via a researcher-INFERENCE edge, which
    `candidate_v2()` itself never emits (it only emits date-PROVEN edges) -
    and proves the comparator detects it."""

    SNAPSHOT = _dt.date(2005, 4, 1)

    def _pair(self):
        # A cosmetic event (c1) confirmed NEW, ordered AFTER an undated
        # relevant event (c0) by an INFERENCE edge (nothing about an undated
        # event is date-provable). Full-event reasoning: c1 having occurred
        # forces its predecessor c0 to have occurred too - even though c1
        # never appears in a state's identity. Event ids match what
        # candidate_v2() would assign (c{index}), so v1_claimed_states/
        # v2_claimed_states are directly comparable.
        v2 = ErratumV2.load(
            {
                "id": "erratum-synth",
                "modern_card": {"passcode": 200, "name": "Beta"},
                "classification": "functional",
                "events": {
                    "c0": {
                        "effective": {"date": None},
                        "transitions": [{"kind": "functional", "summary": "x", "sources": ["s"]}],
                    },
                    "c1": {
                        "effective": {"date": "2000-01-01"},
                        "transitions": [{"kind": "cosmetic", "summary": "y", "sources": ["s"]}],
                    },
                },
                "ordering": {
                    "edges": [
                        {
                            "before": "c0",
                            "after": "c1",
                            "basis": "researcher-inference",
                            "note": "the rewording postdates the behavioural change",
                        }
                    ]
                },
                "states": [
                    {
                        "events": [],
                        "coverage": {
                            "kind": "reuse-upstream",
                            "historical_passcode": 511000001,
                            "upstream": "ProjectIgnis",
                        },
                    }
                ],
                "review": {"status": "reviewed"},
                "sources": ["s"],
            },
            Path("x.json"),
        )
        v1 = Erratum.load(
            {
                "id": "erratum-synth",
                "modern_card": {"passcode": 200, "name": "Beta"},
                "classification": "functional",
                "changes": [
                    {"kind": "functional", "effective": {"date": None}, "summary": "x", "sources": ["s"]},
                    {"kind": "cosmetic", "effective": {"date": "2000-01-01"}, "summary": "y", "sources": ["s"]},
                ],
                "implementation": {
                    "strategy": "reuse-upstream",
                    "historical_passcode": 511000001,
                    "status": "complete",
                },
                "review": {"status": "reviewed"},
                "sources": ["s"],
            },
            Path("x.json"),
        )
        return v1, v2

    def test_nonrelevant_event_chronology_constrains_a_relevant_event(self):
        _v1, v2 = self._pair()
        selection = v2.selection_at(self.SNAPSHOT)
        # The cosmetic event is not part of any state's identity...
        self.assertEqual([["c0"]], [sorted(c.events) for c in selection.candidates])
        # ...yet it collapsed the ambiguity to a single determinate state.
        self.assertEqual("determinate", selection.chronology)

    def test_audit_comparison_detects_the_difference(self):
        v1, v2 = self._pair()
        v1_states = v1_claimed_states(v1, self.SNAPSHOT)
        v2_states = v2_claimed_states(v2, self.SNAPSHOT)
        # v1 still thinks the pre-errata baseline is a live possibility...
        self.assertIn((frozenset(), ("reuse-upstream", 511000001, ())), v1_states)
        # ...v2's full-event reasoning has already ruled it out.
        self.assertNotIn((frozenset(), ("reuse-upstream", 511000001, ())), v2_states)
        self.assertNotEqual(v1_states, v2_states)


class ProvenEdgesAddNoConstraintTest(unittest.TestCase):
    """A structural fact about `ordering_proof()`, independent of the
    comparator correction above: a date-PROVEN edge can never constrain a
    down-set beyond what the two events' own statuses already do. This is
    WHY a fully-ordered record's real chronology can never disagree with
    itself once migrated - it does NOT claim v1 and candidate-v2 always
    agree (they do not: see the 49 above), only that PROVEN edges are never
    themselves a source of surprise."""

    @staticmethod
    def _chronologies():
        out = []
        for date in ("2005-01-01", "2008-06-15", "2010-12-01"):
            out.append({"date": date})
            out.append({"date": date, "precision": "month"})
            out.append({"date": date, "precision": "year"})
        for a, b in itertools.combinations(
            ("2004-01-01", "2006-06-01", "2009-03-03", "2012-01-01"), 2
        ):
            out.append({"date": None, "old_attested_through": a, "new_attested_from": b})
        out.append({"date": None})
        return out

    @staticmethod
    def _probe_days():
        return [
            _dt.date(year, month, day)
            for year in range(2003, 2014)
            for month in (1, 3, 6, 9, 12)
            for day in (1, 15, 28)
        ]

    def test_no_proven_edge_adds_a_constraint(self):
        chronologies = self._chronologies()
        days = self._probe_days()
        proven_pairs = 0
        for before, after in itertools.permutations(chronologies, 2):
            if ordering_proof(before, after) != PROVEN:
                continue
            proven_pairs += 1
            for day in days:
                state_before = change_state_at({"effective": before}, day)
                state_after = change_state_at({"effective": after}, day)
                if state_after == NEW:
                    self.assertEqual(NEW, state_before, (before, after, day))
                if state_before == OLD:
                    self.assertEqual(OLD, state_after, (before, after, day))
        self.assertGreater(proven_pairs, 0, "the search must actually exercise proven edges")

    def test_an_inference_edge_by_contrast_can_add_one(self):
        # The dual: exactly the case AuditSensitivityTest exploits. Nothing
        # about an undated event is provable, so the constraint there comes
        # from the edge, not the dates.
        undated = {"date": None}
        dated = {"date": "2000-01-01"}
        self.assertNotEqual(PROVEN, ordering_proof(undated, dated))
        day = _dt.date(2005, 4, 1)
        self.assertEqual(AMBIGUOUS, change_state_at({"effective": undated}, day))
        self.assertEqual(NEW, change_state_at({"effective": dated}, day))


class AuditIsNotVacuousTest(unittest.TestCase):
    """Mutation tests on the audit itself, per this task's objective 11 (C,
    D): deliberately break the migration in two specific forbidden ways and
    require the corrected comparator to detect MORE non-equivalence than
    the genuine, already-present 49 - proving the detection power is real,
    not merely inherited from records that were already flagged."""

    @classmethod
    def setUpClass(cls):
        repo = Repository.load(audit.REPO_ROOT)
        cls.records = [e for e in repo.errata.values() if isinstance(e, Erratum)]
        cls.baseline_not_equivalent = audit_corpus()["summary"]["not_equivalent"]

    def test_C_ordering_copied_from_array_position_is_detected(self):
        """The shortcut this task forbids: treating `changes[]` order as an
        ordering claim."""
        real_candidate = audit.candidate_v2

        def positional(record):
            raw = dict(real_candidate(record).raw)
            ids = sorted(raw["events"])
            raw["ordering"] = {
                "edges": [
                    {
                        "before": before,
                        "after": after,
                        "basis": "researcher-inference",
                        "note": "array position (deliberately wrong)",
                    }
                    for before, after in zip(ids, ids[1:])
                ]
            }
            return ErratumV2.load(raw, Path(record.path))

        try:
            audit.candidate_v2 = positional
            detected = sum(1 for r in self.records if not audit.compare(r)["equivalent"])
        finally:
            audit.candidate_v2 = real_candidate
        self.assertGreater(
            detected,
            self.baseline_not_equivalent,
            "array-position ordering must break MORE records than the genuine 49",
        )

    def test_D_state_coverage_shifted_by_one_event_is_detected(self):
        """Objective 11's other forbidden shortcut: attributing a version's
        coverage to the wrong down-set."""
        real_candidate = audit.candidate_v2

        def shifted(record):
            v2 = real_candidate(record)
            raw = dict(v2.raw)
            states = raw.get("states") or []
            if len(states) < 2:
                return v2
            covs = [s["coverage"] for s in states]
            raw2 = dict(raw)
            raw2["states"] = [dict(s, coverage=covs[(i + 1) % len(covs)]) for i, s in enumerate(states)]
            return ErratumV2.load(raw2, Path(record.path))

        try:
            audit.candidate_v2 = shifted
            detected = sum(1 for r in self.records if not audit.compare(r)["equivalent"])
        finally:
            audit.candidate_v2 = real_candidate
        self.assertGreater(
            detected,
            self.baseline_not_equivalent,
            "shifted coverage must break MORE records than the genuine 49",
        )


class CoveragePreservationTest(unittest.TestCase):
    """Task objective 1: every coverage field with a direct v2
    representation must survive migration, not just executable identity.
    `script` is optional-but-allowed on reuse-upstream coverage (schema's
    `coverageReuseUpstream` permits it) and was previously silently
    dropped - Giant Rat's baseline implementation is the concrete
    counterexample the task names, but the fix applies to all 242
    reuse-upstream implementations in the corpus, all of which carry a
    `script` alongside `upstream`."""

    def test_giant_rat_script_survives_migration(self):
        repo = Repository.load(audit.REPO_ROOT)
        record = repo.errata["erratum-giant-rat"]
        v2 = candidate_v2(record)
        baseline = v2.authored_states[frozenset()]
        self.assertEqual("goat/c504700172.lua", baseline.script)
        self.assertTrue(audit._coverage_preserved(record, v2))
        self.assertTrue(audit._data_preserved(record, v2))

    def test_all_296_records_pass_coverage_preservation(self):
        repo = Repository.load(audit.REPO_ROOT)
        for record in repo.errata.values():
            if not isinstance(record, Erratum):
                continue
            v2 = audit.candidate_v2(record)
            self.assertTrue(audit._coverage_preserved(record, v2), record.id)

    def test_check_is_independent_of_construction_a_dropped_script_is_detected(self):
        """Mutation test: if `_coverage_from_v1()` regressed and silently
        dropped `script` again, `_coverage_preserved()` must notice - it
        does NOT trust `candidate_v2()` merely because it constructed the
        candidate itself; it re-derives the expectation from the v1 record
        independently and checks the REAL parsed coverage."""
        repo = Repository.load(audit.REPO_ROOT)
        record = repo.errata["erratum-giant-rat"]
        real_coverage_from_v1 = audit._coverage_from_v1

        def dropping_script(impl):
            coverage = real_coverage_from_v1(impl)
            if coverage is not None:
                coverage.pop("script", None)
            return coverage

        try:
            audit._coverage_from_v1 = dropping_script
            v2 = audit.candidate_v2(record)
        finally:
            audit._coverage_from_v1 = real_coverage_from_v1
        self.assertFalse(audit._coverage_preserved(record, v2))


class CoverageKindDistinctionTest(unittest.TestCase):
    """Task objective 3: reuse-upstream and custom-script at the SAME
    passcode are different migration-data claims (different provenance,
    different `COVERAGE_FIELDS` shape) and must not compare equal merely
    because both currently execute as the identical substitution; a
    known-gap must not compare equal to a DIFFERENT known-gap merely
    because both fall back to modern execution today."""

    def test_reuse_upstream_and_custom_script_have_different_signatures(self):
        self.assertNotEqual(
            audit._v1_coverage_signature({"strategy": "reuse-upstream", "historical_passcode": 1}),
            audit._v1_coverage_signature(
                {"strategy": "custom-script", "historical_passcode": 1, "script": "x.lua"}
            ),
        )

    def test_known_gap_reasons_are_not_conflated(self):
        a = audit._v1_coverage_signature({"strategy": "unresolved", "gap": {"reason": "A", "sources": ["s"]}})
        b = audit._v1_coverage_signature({"strategy": "unresolved", "gap": {"reason": "B", "sources": ["s"]}})
        bare_unresolved = audit._v1_coverage_signature({"strategy": "unresolved"})
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, bare_unresolved)
        self.assertNotEqual(b, bare_unresolved)

    def test_v2_side_agrees(self):
        from retroformats.model import Coverage, ImplementationCoverage

        ru = ImplementationCoverage(kind=Coverage.REUSE_UPSTREAM, historical_passcode=1)
        cs = ImplementationCoverage(kind=Coverage.CUSTOM_SCRIPT, historical_passcode=1)
        self.assertNotEqual(audit._v2_coverage_signature(ru), audit._v2_coverage_signature(cs))
        gap_a = ImplementationCoverage(kind=Coverage.KNOWN_GAP, gap_reason="A", gap_sources=("s",))
        gap_b = ImplementationCoverage(kind=Coverage.KNOWN_GAP, gap_reason="B", gap_sources=("s",))
        self.assertNotEqual(audit._v2_coverage_signature(gap_a), audit._v2_coverage_signature(gap_b))

    def test_mutation_swapping_coverage_kind_is_detected(self):
        """A real, currently-equivalent reuse-upstream sugar record: swap
        its candidate coverage to custom-script at the SAME passcode. The
        audit MUST now report it non-equivalent - coverage KIND is part of
        the migration-data claim, not just the final passcode."""
        repo = Repository.load(audit.REPO_ROOT)
        record = repo.errata["erratum-a-cat-of-ill-omen"]
        baseline_row = audit.compare(record)
        self.assertTrue(baseline_row["equivalent"])
        self.assertEqual("reuse-upstream", record.implementation.get("strategy"))

        real_candidate = audit.candidate_v2

        def kind_swapped(rec):
            v2 = real_candidate(rec)
            if rec.id != record.id:
                return v2
            raw = dict(v2.raw)
            states = []
            for entry in raw.get("states", []):
                entry = dict(entry)
                coverage = dict(entry["coverage"])
                if coverage.get("kind") == "reuse-upstream":
                    coverage["kind"] = "custom-script"
                    coverage.setdefault("script", "goat/mutated.lua")
                    coverage.pop("upstream", None)
                entry["coverage"] = coverage
                states.append(entry)
            raw["states"] = states
            return ErratumV2.load(raw, Path(rec.path))

        try:
            audit.candidate_v2 = kind_swapped
            mutated_row = audit.compare(record)
        finally:
            audit.candidate_v2 = real_candidate
        self.assertFalse(
            mutated_row["equivalent"],
            "swapping reuse-upstream to custom-script at the same passcode must be detected",
        )


class MetadataInventoryTest(unittest.TestCase):
    """Task objective 1's honest inventory: v1 implementation metadata with
    NO v2 coverage destination must be reported explicitly, not silently
    folded into "data_preserved=True" by omission. UNKNOWN != DISCARD.

    **Corrected TWICE now.** First pass: `record_count` actually counted
    IMPLEMENTATION-OBJECT occurrences, not records. Second pass: even after
    that fix, `resulting_implementation_occurrence_count` was still
    counting UNIQUE RECORDS with a resulting implementation (12), not
    occurrences (16 - Necrovalley alone has three) - and worse,
    `by_record[rid]["resulting"] = value` silently OVERWROTE one record's
    earlier resulting_implementation with a later one before any
    baseline-vs-resulting comparison ran, so a record whose FIRST resulting
    state diverged from baseline but whose LAST one happened to match it
    was invisible to the old divergence check. Fixed by giving every
    occurrence an exact, never-overwritten locator (`"baseline"` or
    `"resulting:<change-index>"`) and comparing ALL of a record's
    occurrences together. The fix is not cosmetic: it found a genuinely
    divergent record (`erratum-swords-of-concealing-light`) the previous,
    already-"corrected" pass missed entirely."""

    @classmethod
    def setUpClass(cls):
        repo = Repository.load(audit.REPO_ROOT)
        cls.inventory = {row["field"]: row for row in audit.metadata_inventory(repo.errata)}

    def test_occurrence_count_is_distinct_from_unique_record_count(self):
        """312 implementation-object occurrences of `status` come from
        only 296 DISTINCT records (296 baseline + 16 resulting occurrences,
        spread across only 12 distinct records) - never call 312 OR 12
        "records" where occurrences are meant."""
        status = self.inventory["status"]
        self.assertEqual(312, status["implementation_occurrence_count"])
        self.assertEqual(296, status["unique_record_count"])
        self.assertEqual(296, len(status["unique_record_ids"]))
        self.assertEqual(296, status["baseline_occurrence_count"])
        self.assertEqual(16, status["resulting_implementation_occurrence_count"])
        self.assertEqual(296, status["unique_baseline_record_count"])
        self.assertEqual(12, status["unique_resulting_record_count"])
        self.assertNotEqual(status["implementation_occurrence_count"], status["unique_record_count"])
        self.assertNotEqual(
            status["resulting_implementation_occurrence_count"], status["unique_resulting_record_count"]
        )

    def test_known_metadata_fields_are_now_represented(self):
        """**Corrected again**: these 4 fields (plus the bare `reason`) had
        no v2 destination when this test was first written. This task
        implements `implementation_metadata[]` as that destination
        (representation-gaps.md), so `metadata_inventory()` now reports
        them as REPRESENTED - `has_v2_destination: True`, `would_be_lost_
        on_migration: False` - not because the data changed, but because a
        place for it to go now exists in the schema/runtime."""
        # field: (occurrences, unique records, baseline occ, resulting occ,
        #         unique baseline records, unique resulting records)
        expected = {
            "status": (312, 296, 296, 16, 296, 12),
            "tested": (252, 240, 236, 16, 236, 12),
            "gap.upstream_checked": (56, 53, 48, 8, 48, 7),
            "gap.behavioural_impact": (56, 53, 48, 8, 48, 7),
        }
        for field, (occ, uniq, base_occ, res_occ, uniq_base, uniq_res) in expected.items():
            self.assertIn(field, self.inventory)
            row = self.inventory[field]
            self.assertEqual(occ, row["implementation_occurrence_count"], field)
            self.assertEqual(uniq, row["unique_record_count"], field)
            self.assertEqual(uniq, len(row["unique_record_ids"]), field)
            self.assertEqual(base_occ, row["baseline_occurrence_count"], field)
            self.assertEqual(res_occ, row["resulting_implementation_occurrence_count"], field)
            self.assertEqual(uniq_base, row["unique_baseline_record_count"], field)
            self.assertEqual(uniq_res, row["unique_resulting_record_count"], field)
            self.assertTrue(row["has_v2_destination"], field)
            self.assertFalse(row["would_be_lost_on_migration"], field)
            self.assertTrue(row["representative_baseline_ids"] or row["representative_resulting_ids"], field)
            self.assertTrue(row["representative_occurrences"], field)
            for occurrence in row["representative_occurrences"]:
                self.assertIn(occurrence["locator"].split(":")[0], ("baseline", "resulting"), field)

    def test_bare_reason_is_also_represented(self):
        row = self.inventory["reason"]
        self.assertTrue(row["has_v2_destination"])
        self.assertFalse(row["would_be_lost_on_migration"])

    def test_a_genuinely_unknown_future_field_would_still_be_unrepresented(self):
        """`KNOWN_METADATA_FIELDS` is exactly the frozen shape's fields,
        not "everything metadata_inventory() might ever see" - a field
        outside it must still be reported as a real gap."""
        self.assertNotIn("some-future-field", audit.KNOWN_METADATA_FIELDS)

    def test_status_is_provably_state_specific_via_a_resulting_implementation(self):
        """The task's required worked example: an erratum whose
        `resulting_implementation` carries a DIFFERENT `status` than its
        baseline `implementation` - proof that this metadata varies BY
        STATE, not just by record, so a record-level field cannot preserve
        it. 7 records now, not the previous (buggy) pass's 6."""
        status = self.inventory["status"]
        self.assertEqual(
            [
                "erratum-blue-eyes-toon-dragon",
                "erratum-insect-imitation",
                "erratum-last-will",
                "erratum-necrovalley",
                "erratum-night-assailant",
                "erratum-swords-of-concealing-light",
                "erratum-yz-tank-dragon",
            ],
            status["records_with_multiple_distinct_values"],
        )
        repo = Repository.load(audit.REPO_ROOT)
        record = repo.errata["erratum-blue-eyes-toon-dragon"]
        baseline_status = (record.implementation or {}).get("status")
        resulting_statuses = {
            c["resulting_implementation"]["status"]
            for c in record.changes
            if c.get("resulting_implementation") and "status" in c["resulting_implementation"]
        }
        self.assertNotIn(baseline_status, resulting_statuses)

    def test_the_previously_missed_record_has_a_non_final_divergent_occurrence(self):
        """`erratum-swords-of-concealing-light`: baseline is `complete`, its
        FIRST resulting_implementation is `missing`, its second and third
        are `complete` again. The old (buggy) "keep only the last
        resulting value" comparison saw complete-vs-complete and missed the
        genuine divergence at change index 0 entirely."""
        repo = Repository.load(audit.REPO_ROOT)
        record = repo.errata["erratum-swords-of-concealing-light"]
        baseline_status = (record.implementation or {}).get("status")
        resulting_statuses = [
            c["resulting_implementation"].get("status")
            for c in record.changes
            if c.get("resulting_implementation") and "status" in c["resulting_implementation"]
        ]
        self.assertEqual("complete", baseline_status)
        self.assertEqual(["missing", "complete", "complete"], resulting_statuses)
        self.assertNotEqual(baseline_status, resulting_statuses[0])
        self.assertEqual(baseline_status, resulting_statuses[-1])

    def test_tested_also_diverges_for_at_least_one_record(self):
        tested = self.inventory["tested"]
        self.assertIn("erratum-rescue-cat", tested["records_with_multiple_distinct_values"])

    def test_gap_behavioural_impact_diverges_for_two_records(self):
        row = self.inventory["gap.behavioural_impact"]
        self.assertEqual(
            ["erratum-dark-necrofear", "erratum-necrovalley"], row["records_with_multiple_distinct_values"]
        )

    def test_gap_upstream_checked_is_not_state_specific_in_current_data(self):
        """A field CAN be uniformly True everywhere (no observed
        divergence) while still being structurally state-specific
        (authored per implementation object) - the two are different
        claims, and the inventory must not overstate what the data shows."""
        row = self.inventory["gap.upstream_checked"]
        self.assertEqual([], row["records_with_multiple_distinct_values"])
        self.assertTrue(row["records_with_multiple_occurrences"])  # multiple occurrences...
        self.assertEqual({"True": 56}, row["value_distribution"])  # ...but always the same value

    def test_represented_fields_are_not_in_the_inventory(self):
        """Fields WITH a v2 destination (including the newly-fixed
        `script`/`upstream` optional pair) must not appear as losses."""
        for field in (
            "historical_passcode",
            "historical_variant_passcodes",
            "upstream",
            "script",
            "strategy",
            "gap.reason",
            "gap.sources",
        ):
            self.assertNotIn(field, self.inventory, field)


class ReferenceIdentityCandidateTest(unittest.TestCase):
    """Task section 8's REFERENCE IDENTITIES requirement: for the 11
    parity-only records, derive the matching current reference consumer
    from the repository's OWN format policy - never hard-code
    'project-ignis-goat' inside generic migration logic - and produce
    exactly one reference identity each, with the exact v1 passcode/
    variants/upstream/script."""

    PARITY_ONLY_IDS = (
        "erratum-bubble-crash",
        "erratum-chaosrider-gustaph",
        "erratum-cipher-soldier",
        "erratum-dark-jeroid",
        "erratum-injection-fairy-lily",
        "erratum-kazejin",
        "erratum-mirage-knight",
        "erratum-nobleman-of-crossout",
        "erratum-nobleman-of-extermination",
        "erratum-shinato-king-of-a-higher-plane",
        "erratum-suijin",
    )

    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(audit.REPO_ROOT)

    def test_derivation_reads_the_format_not_a_hard_coded_string(self):
        """Proof this is genuinely DERIVED: point a synthetic format's
        reference_parity at a different reference_id/provenance_source and
        confirm the derivation follows it, rather than always emitting
        'project-ignis-goat' regardless of what any format actually
        declares."""
        from retroformats.model import Format

        record = self.repo.errata["erratum-nobleman-of-crossout"]
        real = audit.derive_reference_identities(record, self.repo)
        self.assertEqual("project-ignis-goat", real[0]["reference_id"])

        fake_fmt = Format.load(
            {
                "id": "synthetic-fmt",
                "name": "Synthetic",
                "region": "TCG",
                "period": {"start": "2005-04-01", "end": None, "snapshot": "2005-04-01"},
                "banlist": "x",
                "card_pool": "x",
                "rule_profile": "x",
                "errata_policy": "computed",
                "errata_overrides": {
                    "reference_parity": {
                        "reference_id": "totally-different-id",
                        "provenance_source": "ignis-lflists",
                        "reason": "synthetic",
                        "sources": ["ignis-lflists"],
                    },
                    "sources": ["ignis-lflists"],
                },
                "sources": ["ignis-lflists"],
            },
            record.path,
        )
        fake_repo = type("FakeRepo", (), {"formats": {"synthetic-fmt": fake_fmt}})()
        derived = audit.derive_reference_identities(record, fake_repo)
        self.assertEqual(1, len(derived))
        self.assertEqual("totally-different-id", derived[0]["reference_id"])

    def test_exactly_the_11_parity_only_records_get_exactly_one_entry(self):
        for record in self.repo.errata.values():
            if not isinstance(record, audit.Erratum):
                continue
            identities = audit.derive_reference_identities(record, self.repo)
            if record.id in self.PARITY_ONLY_IDS:
                self.assertEqual(1, len(identities), record.id)
            else:
                self.assertEqual([], identities, record.id)

    def test_each_identity_round_trips_the_exact_v1_passcode_upstream_script(self):
        for record_id in self.PARITY_ONLY_IDS:
            record = self.repo.errata[record_id]
            impl = record.implementation
            identities = audit.derive_reference_identities(record, self.repo)
            entry = identities[0]
            self.assertEqual("project-ignis-goat", entry["reference_id"], record_id)
            self.assertEqual("ignis-lflists", entry["provenance_source"], record_id)
            self.assertEqual(impl["historical_passcode"], entry["historical_passcode"], record_id)
            self.assertEqual(
                list(impl.get("historical_variant_passcodes", [])),
                entry["historical_variant_passcodes"],
                record_id,
            )
            self.assertEqual(impl.get("upstream"), entry["upstream"], record_id)
            self.assertEqual(impl.get("script"), entry["script"], record_id)

    def test_candidate_v2_carries_the_identity_and_preservation_check_passes(self):
        for record_id in self.PARITY_ONLY_IDS:
            record = self.repo.errata[record_id]
            identities = audit.derive_reference_identities(record, self.repo)
            v2 = audit.candidate_v2(record, identities)
            self.assertEqual(1, len(v2.reference_identities), record_id)
            self.assertTrue(audit._reference_identity_preserved(record, v2), record_id)

    def test_without_the_derived_identity_preservation_correctly_fails(self):
        """The preservation check must have real teeth: a parity-only
        record's candidate WITHOUT any reference_identities must fail the
        check, proving it is not vacuously true for every input."""
        record = self.repo.errata["erratum-nobleman-of-crossout"]
        v2_without = audit.candidate_v2(record)  # no reference_identities passed
        self.assertFalse(audit._reference_identity_preserved(record, v2_without))

    def test_mutation_wrong_passcode_is_detected(self):
        """Independent preservation test (task section 8): mutate the
        derived identity's passcode and confirm the check notices."""
        record = self.repo.errata["erratum-nobleman-of-crossout"]
        identities = audit.derive_reference_identities(record, self.repo)
        mutated = [dict(identities[0], historical_passcode=identities[0]["historical_passcode"] + 1)]
        v2 = audit.candidate_v2(record, mutated)
        self.assertFalse(audit._reference_identity_preserved(record, v2))


class ImplementationMetadataCandidateTest(unittest.TestCase):
    """Task section 8's IMPLEMENTATION METADATA requirement: map each v1
    implementation OBJECT to the semantic state it describes (baseline ->
    `events=[]`; a relevant change's `resulting_implementation` -> the
    down-set that change CREATED, i.e. the same legacy-claimed prefix
    event-set `states[]` already uses) and independently verify no
    occurrence silently disappears."""

    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(audit.REPO_ROOT)

    def test_baseline_metadata_maps_to_the_empty_down_set(self):
        record = self.repo.errata["erratum-a-cat-of-ill-omen"]
        v2 = audit.candidate_v2(record)
        baseline = v2.implementation_metadata.get(frozenset())
        self.assertIsNotNone(baseline)
        self.assertEqual(record.implementation.get("status"), baseline.status)
        self.assertEqual(record.implementation.get("tested"), baseline.tested)

    def test_resulting_implementation_maps_to_the_state_it_created(self):
        """Blue-Eyes Toon Dragon: baseline status=complete at {}, the one
        relevant change's resulting_implementation status=missing at the
        down-set THAT CHANGE created ({c0})."""
        record = self.repo.errata["erratum-blue-eyes-toon-dragon"]
        relevant_indices = audit._relevant_indices(record)
        v2 = audit.candidate_v2(record)
        baseline = v2.implementation_metadata.get(frozenset())
        self.assertEqual("complete", baseline.status)
        created = v2.implementation_metadata.get(frozenset({audit._event_id(relevant_indices[0])}))
        self.assertIsNotNone(created)
        self.assertEqual("missing", created.status)

    def test_metadata_never_changes_coverage_or_selection(self):
        """implementation_metadata[] is orthogonal to Coverage entirely -
        adding it must not change what selection_at()/state_for() return
        for any real record."""
        for record in self.repo.errata.values():
            if not isinstance(record, audit.Erratum):
                continue
            v2 = audit.candidate_v2(record)
            if not v2.implementation_metadata:
                continue
            for day in audit.boundary_dates(record):
                with_metadata = audit.v2_claimed_states(v2, day)
                v2_no_metadata = audit.candidate_v2(record)
                v2_no_metadata.implementation_metadata.clear()
                without_metadata = audit.v2_claimed_states(v2_no_metadata, day)
                self.assertEqual(with_metadata, without_metadata, record.id)

    def test_no_implementation_occurrence_silently_disappears(self):
        """Independent preservation test (task section 8): every v1
        implementation object that carries at least one metadata field
        must have a corresponding, correctly-valued
        implementation_metadata[] entry in the candidate."""
        for record in self.repo.errata.values():
            if not isinstance(record, audit.Erratum):
                continue
            v2 = audit.candidate_v2(record)
            self.assertTrue(audit._metadata_preserved(record, v2), record.id)

    def test_mutation_dropped_status_is_detected(self):
        """Independent preservation test: monkeypatch
        `_implementation_metadata_from_v1()` to silently drop `status` and
        confirm `_metadata_preserved()` notices - it does not trust
        `candidate_v2()` merely because it built the candidate itself."""
        record = self.repo.errata["erratum-a-cat-of-ill-omen"]
        self.assertIsNotNone((record.implementation or {}).get("status"))
        real = audit._implementation_metadata_from_v1

        def dropping_status(impl):
            entry = real(impl)
            if entry is not None:
                entry.pop("status", None)
            return entry or None

        try:
            audit._implementation_metadata_from_v1 = dropping_status
            v2 = audit.candidate_v2(record)
        finally:
            audit._implementation_metadata_from_v1 = real
        self.assertFalse(audit._metadata_preserved(record, v2))


if __name__ == "__main__":
    unittest.main()
