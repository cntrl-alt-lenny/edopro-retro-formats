"""The v1 -> v2 migration audit, as a test rather than a number in prose.

`docs/research/erratum-v2-migration-audit.md` reports a partition of the
296-record corpus. That partition is DERIVED by `tests/migration_audit.py`
from the current runtime, and these tests keep the derivation honest:

- the reported counts are re-computed here, so the document cannot drift
  away from the code;
- the audit's comparison is proved SENSITIVE (it detects a real full-event
  chronology difference when one exists), so "everything is equivalent" is
  a finding rather than a blind spot;
- the structural reason the corpus comes out equivalent - a date-PROVEN
  ordering edge can never add a constraint the two events' own chronology
  does not already impose - is asserted directly.
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

from .migration_audit import (
    CAT_COSMETIC_ONLY,
    CAT_MULTI_ORDERED,
    CAT_MULTI_UNORDERED,
    CAT_PARITY_ONLY,
    CAT_SUGAR,
    audit_corpus,
    v1_outcome,
    v2_outcome,
)


class MigrationAuditPartitionTest(unittest.TestCase):
    """The derived partition the report publishes. If a canonical record
    changes shape, these numbers move and the report must be re-derived -
    which is the point of computing rather than asserting them."""

    @classmethod
    def setUpClass(cls):
        cls.result = audit_corpus()
        cls.rows = cls.result["rows"]
        cls.summary = cls.result["summary"]

    def test_every_v1_record_is_covered(self):
        self.assertEqual(296, self.summary["records"])
        self.assertEqual(296, len(self.rows))

    def test_all_records_are_mechanically_equivalent_under_full_event_semantics(self):
        """The safe count is an OUTPUT: every record's v1 selection and its
        candidate-v2 selection agree at EVERY chronology boundary."""
        self.assertEqual(0, self.summary["not_equivalent"])
        self.assertEqual(296, self.summary["equivalent"])

    def test_partition_counts(self):
        self.assertEqual(
            {
                CAT_SUGAR: 180,
                "full-v2-single-event": 35,
                CAT_MULTI_ORDERED: 17,
                CAT_MULTI_UNORDERED: 43,
                CAT_PARITY_ONLY: 11,
                CAT_COSMETIC_ONLY: 10,
            },
            self.summary["categories"],
        )
        self.assertEqual(296, sum(self.summary["categories"].values()))

    def test_sugar_eligibility_requires_one_event_in_total(self):
        """Under full-event semantics every change is an event, including
        cosmetic/engine ones - so a record with one RELEVANT change but a
        cosmetic change beside it has two events and cannot use single-event
        sugar. This is why sugar-eligibility is 180, not the 236 records that
        merely have <=1 relevant change."""
        for row in self.rows:
            if row["category"] == CAT_SUGAR:
                self.assertEqual(1, row["changes"], row["id"])
                self.assertEqual(1, row["relevant_changes"], row["id"])
        with_one_relevant = [r for r in self.rows if r["relevant_changes"] <= 1]
        self.assertEqual(236, len(with_one_relevant))

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


class ParityOnlyIdentityIsUnrepresentableTest(unittest.TestCase):
    """Objective 4's representation problem, stated as an executable fact:
    a record with zero implementation-relevant events has exactly one
    structural state, `{}`, which IS the terminal state - so its coverage is
    unconditionally MODERN and any authored historical identity is silently
    discarded. v2 as frozen cannot carry these identities."""

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
    """"All 296 equivalent" is only meaningful if the comparison could have
    said otherwise. This constructs a record where FULL-event semantics
    genuinely differ from relevant-only semantics and proves the audit's own
    comparison detects it."""

    SNAPSHOT = _dt.date(2005, 4, 1)

    def _pair(self):
        # A cosmetic event confirmed NEW, ordered AFTER an undated relevant
        # event by an INFERENCE edge (nothing about an undated event can be
        # date-proven). Full-event reasoning: the cosmetic event having
        # occurred forces its predecessor to have occurred too - even though
        # the cosmetic event never appears in a state's identity.
        v2 = ErratumV2.load(
            {
                "id": "erratum-synth",
                "modern_card": {"passcode": 200, "name": "Beta"},
                "classification": "functional",
                "events": {
                    "rel": {
                        "effective": {"date": None},
                        "transitions": [{"kind": "functional", "summary": "x", "sources": ["s"]}],
                    },
                    "cos": {
                        "effective": {"date": "2000-01-01"},
                        "transitions": [{"kind": "cosmetic", "summary": "y", "sources": ["s"]}],
                    },
                },
                "ordering": {
                    "edges": [
                        {
                            "before": "rel",
                            "after": "cos",
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
        self.assertEqual([["rel"]], [sorted(c.events) for c in selection.candidates])
        # ...yet it collapsed the ambiguity to a single determinate state.
        self.assertEqual("determinate", selection.chronology)

    def test_audit_comparison_detects_the_difference(self):
        v1, v2 = self._pair()
        self.assertEqual(("ambiguous", (0, 1)), v1_outcome(v1, self.SNAPSHOT))
        self.assertEqual(("modern",), v2_outcome(v2, self.SNAPSHOT))
        self.assertNotEqual(v1_outcome(v1, self.SNAPSHOT), v2_outcome(v2, self.SNAPSHOT))


class ProvenEdgesAddNoConstraintTest(unittest.TestCase):
    """WHY the corpus comes out equivalent, asserted rather than assumed.

    The migration only ever emits date-PROVEN ordering edges. Such an edge
    can never constrain a down-set beyond what the two events' own statuses
    already do: if `before < after` is date-proven, then `after` being NEW at
    a snapshot already implies `before` is NEW, and `before` being OLD already
    implies `after` is OLD. So full-event down-set reasoning and relevant-only
    reasoning cannot diverge for a migrated record."""

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


if __name__ == "__main__":
    unittest.main()


class AuditIsNotVacuousTest(unittest.TestCase):
    """A mutation test on the audit itself. "296 of 296 equivalent" is only
    trustworthy if the comparison would have failed on a migration that got
    it wrong - so deliberately break the migration and require detection."""

    def test_ordering_copied_from_array_position_is_detected(self):
        """The shortcut the task forbids: treating `changes[]` order as an
        ordering claim. If the audit could not see the difference, it could
        not certify that NOT doing it is safe either."""
        from pathlib import Path as _Path

        from retroformats.model import ErratumV2
        from retroformats.repo import Repository

        from . import migration_audit as audit

        repo = Repository.load(audit.REPO_ROOT)
        records = [e for e in repo.errata.values() if isinstance(e, Erratum)]
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
            return ErratumV2.load(raw, _Path(record.path))

        try:
            audit.candidate_v2 = positional
            detected = sum(1 for r in records if not audit.compare(r)["equivalent"])
        finally:
            audit.candidate_v2 = real_candidate
        self.assertGreater(
            detected, 0, "the audit must detect an ordering claim invented from array position"
        )
