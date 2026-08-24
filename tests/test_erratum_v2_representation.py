"""End-to-end tests for the two representation-gap mechanisms
(docs/research/erratum-v2-representation-gaps.md, implemented by the task
that also wrote this file): `implementation_metadata[]` (workflow/research
metadata, orthogonal to Coverage) and `reference_identities[]` (exact
reference-provenance identity, orthogonal to Coverage/behavioural state).

No canonical record uses either field yet - every fixture here is
constructed fresh, exactly like tests/test_erratum_v2_consumers.py, whose
`V2ConsumerTestBase` this file reuses directly.
"""

from __future__ import annotations

import datetime as _dt
import unittest

from retroformats.lflist import (
    ReferenceIdentity,
    build_lflist,
    historical_identity,
    select_applicable_errata,
)
from retroformats.model import Coverage, ErratumV2, ImplementationCoverage
from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import card, v2_coverage, v2_event, v2_transition
from .test_erratum_v2_consumers import V2ConsumerTestBase


def day(s: str) -> _dt.date:
    return _dt.date.fromisoformat(s)


# =============================================================================
# implementation_metadata[]
# =============================================================================


class ImplementationMetadataParsingTest(V2ConsumerTestBase):
    """Parsing/runtime behaviour: baseline/resulting/terminal entries parse
    correctly, metadata never changes Coverage or selection, and absent
    metadata is fully valid (never warned about)."""

    def test_baseline_metadata_parses(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": [], "status": "complete", "tested": True}],
        )
        repo = self._repo()
        erratum = repo.errata["erratum-v2-beta"]
        metadata = erratum.metadata_for(frozenset())
        self.assertIsNotNone(metadata)
        self.assertEqual("complete", metadata.status)
        self.assertTrue(metadata.tested)

    def test_resulting_state_metadata_parses(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": ["e1"], "status": "missing", "reason": "no upstream variant"}],
        )
        repo = self._repo()
        erratum = repo.errata["erratum-v2-beta"]
        metadata = erratum.metadata_for(frozenset({"e1"}))
        self.assertIsNotNone(metadata)
        self.assertEqual("missing", metadata.status)
        self.assertEqual("no upstream variant", metadata.reason)

    def test_terminal_state_metadata_is_valid(self):
        """A record with 1 relevant event: the terminal (all-events) state
        is `{"e1"}`. Metadata there is legal and does not touch the
        synthesised MODERN coverage."""
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": ["e1"], "tested": True}],
        )
        repo = self._repo()
        erratum = repo.errata["erratum-v2-beta"]
        self.assertEqual(Coverage.MODERN, erratum.state_for(frozenset({"e1"})).coverage.kind)
        self.assertTrue(erratum.metadata_for(frozenset({"e1"})).tested)

    def test_metadata_on_mechanically_unresolved_state_does_not_change_coverage(self):
        """A state with NO states[] entry is mechanically UNRESOLVED -
        implementation_metadata[] may still describe it."""
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(), "e2": v2_event()},
            states=[],  # nothing authored: {"e1"} and {"e2"} default to UNRESOLVED
            implementation_metadata=[{"events": ["e1"], "reason": "still researching"}],
        )
        repo = self._repo()
        erratum = repo.errata["erratum-v2-beta"]
        self.assertEqual(Coverage.UNRESOLVED, erratum.state_for(frozenset({"e1"})).coverage.kind)
        self.assertEqual("still researching", erratum.metadata_for(frozenset({"e1"})).reason)

    def test_metadata_does_not_change_selection_at(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2000-01-01"})},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream")}],
        )
        repo = self._repo()
        without = repo.errata["erratum-v2-beta"].selection_at(day("2005-01-01"))

        self.setUp()
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(effective={"date": "2000-01-01"})},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream")}],
            implementation_metadata=[{"events": [], "status": "complete", "tested": True}],
        )
        repo2 = self._repo()
        withit = repo2.errata["erratum-v2-beta"].selection_at(day("2005-01-01"))

        self.assertEqual(without.chronology, withit.chronology)
        self.assertEqual([c.events for c in without.candidates], [c.events for c in withit.candidates])
        self.assertEqual([c.coverage.kind for c in without.candidates], [c.coverage.kind for c in withit.candidates])

    def test_absent_metadata_arrays_are_fully_valid_no_warning(self):
        """Task section 10: no cross-array warnings for absence."""
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event(), "e2": v2_event()},
            states=[
                {"events": [], "coverage": v2_coverage(kind="reuse-upstream")},
                {"events": ["e1"], "coverage": v2_coverage(kind="known-gap")},
            ],
        )
        repo = self._repo()
        findings = Validator(repo).validate()
        codes = {f.code for f in findings}
        self.assertFalse({c for c in codes if c.startswith("erratum.metadata-")})

    def test_a_state_may_have_metadata_with_no_states_entry_at_all(self):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(
            events={"e1": v2_event()},
            states=[],
            implementation_metadata=[{"events": [], "status": "partial"}],
        )
        repo = self._repo()
        findings = Validator(repo).validate()
        codes = {f.code for f in findings}
        self.assertFalse({c for c in codes if c.startswith("erratum.metadata-")})


class ImplementationMetadataValidationTest(V2ConsumerTestBase):
    """`_validate_v2_implementation_metadata()` - one error per malformed
    authored entry, never a cross-array warning for legitimate absence."""

    def _record(self, **kw):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        self.add_erratum_v2(**kw)
        return self._repo()

    def test_unknown_event_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": ["nope"], "status": "complete"}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-unknown-event"))

    def test_non_relevant_event_in_key_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event(transitions=[v2_transition(kind="cosmetic")])},
            implementation_metadata=[{"events": ["e1"], "status": "complete"}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-non-relevant-event"))

    def test_unreachable_key_is_an_error(self):
        repo = self._record(
            events={
                "e1": v2_event(effective={"date": None, "old_attested_through": "2011-02-02", "new_attested_from": "2019-04-03"}),
                "e2": v2_event(effective={"date": "2016-09-15"}),
            },
            ordering={"edges": [{"before": "e2", "after": "e1", "basis": "date-proven"}]},
            implementation_metadata=[{"events": ["e1"], "status": "complete"}],  # e1-before-e2 down-set unreachable
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-unreachable"))

    def test_duplicate_semantic_key_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event(), "e2": v2_event()},
            implementation_metadata=[
                {"events": ["e1", "e2"], "status": "complete"},
                {"events": ["e2", "e1"], "tested": True},  # same SET, different array spelling
            ],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-duplicate-key"))

    def test_repeated_id_inside_one_events_array_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": ["e1", "e1"], "status": "complete"}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-events-duplicate"))

    def test_empty_metadata_entry_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": []}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-empty"))

    def test_bad_status_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": [], "status": "not-a-real-status"}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-bad-status"))

    def test_bad_tested_type_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": [], "tested": "yes"}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-bad-type"))

    def test_bad_reason_type_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": [], "reason": ""}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-bad-type"))

    def test_bad_gap_upstream_checked_type_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": [], "gap": {"upstream_checked": "yes"}}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-bad-type"))

    def test_bad_gap_behavioural_impact_type_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": [], "gap": {"behavioural_impact": ""}}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-bad-type"))

    def test_empty_gap_object_is_an_error(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[{"events": [], "gap": {}}],
        )
        self.assertTrue(self._errors(repo, "erratum.metadata-bad-gap"))

    def test_well_formed_entry_is_accepted(self):
        repo = self._record(
            events={"e1": v2_event()},
            implementation_metadata=[
                {
                    "events": [],
                    "status": "complete",
                    "tested": True,
                    "reason": "documented",
                    "gap": {"upstream_checked": True, "behavioural_impact": "nothing plays differently"},
                }
            ],
        )
        codes = {f.code for f in Validator(repo).validate()}
        self.assertFalse({c for c in codes if c.startswith("erratum.metadata-")})


class SugarImplementationMetadataTest(V2ConsumerTestBase):
    """Task section 2: sugar support is required. Sugar's implicit event id
    is `"event"`, so metadata keys are `[]` (baseline) or `["event"]`
    (terminal) - subject to ordinary reachability rules."""

    def _sugar(self, **extra):
        self._standard_fixture(pool_cards=[card(200, "Beta")])
        payload = {
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
        }
        payload.update(extra)
        self.write("data/errata/v2-sugar.json", payload)
        return self._repo()

    def test_sugar_baseline_metadata_works(self):
        repo = self._sugar(implementation_metadata=[{"events": [], "status": "complete", "tested": True}])
        erratum = repo.errata["erratum-v2-sugar"]
        self.assertIsInstance(erratum, ErratumV2)
        metadata = erratum.metadata_for(frozenset())
        self.assertEqual("complete", metadata.status)
        codes = {f.code for f in Validator(repo).validate()}
        self.assertFalse({c for c in codes if c.startswith("erratum.metadata-")})

    def test_sugar_terminal_metadata_works(self):
        repo = self._sugar(implementation_metadata=[{"events": ["event"], "tested": True}])
        erratum = repo.errata["erratum-v2-sugar"]
        self.assertTrue(erratum.metadata_for(frozenset({"event"})).tested)
        codes = {f.code for f in Validator(repo).validate()}
        self.assertFalse({c for c in codes if c.startswith("erratum.metadata-")})

    def test_sugar_without_metadata_is_still_fully_valid(self):
        """The 180 sugar-eligible records must remain valid WITHOUT
        metadata too - it is optional, not required."""
        repo = self._sugar()
        codes = {f.code for f in Validator(repo).validate()}
        self.assertFalse({c for c in codes if c.startswith("erratum.metadata-")})


# =============================================================================
# reference_identities[]
# =============================================================================


class ReferenceIdentityValidationTest(V2ConsumerTestBase):
    """`_validate_v2_reference_identities()` - record-level well-formedness,
    independent of any specific format."""

    def _record(self, reference_identities, **kw):
        self._standard_fixture(pool_cards=[card(71044499, "Nobleman of Crossout")], **kw)
        self.add_erratum_v2(
            id="erratum-parity-only",
            modern={"passcode": 71044499, "name": "Nobleman of Crossout"},
            classification="cosmetic",
            events={"e1": v2_event(transitions=[v2_transition(kind="cosmetic")])},
            states=[],
            reference_identities=reference_identities,
        )
        return self._repo()

    def _ref(self, **overrides):
        base = {
            "reference_id": "project-ignis-goat",
            "provenance_source": "test-source",
            "historical_passcode": 504700116,
            "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb",
        }
        base.update(overrides)
        return base

    def test_same_provenance_source_may_appear_on_two_different_reference_ids(self):
        repo = self._record(
            [
                self._ref(reference_id="ref-a", historical_passcode=504700116),
                self._ref(reference_id="ref-b", historical_passcode=504700117),
            ]
        )
        self.assertEqual([], self._errors(repo, "erratum.reference-identity-duplicate-id"))

    def test_duplicate_reference_id_on_one_record_is_rejected(self):
        repo = self._record(
            [
                self._ref(reference_id="dup", historical_passcode=504700116),
                self._ref(reference_id="dup", historical_passcode=504700117),
            ]
        )
        self.assertTrue(self._errors(repo, "erratum.reference-identity-duplicate-id"))

    def test_unresolved_provenance_source_is_an_error(self):
        repo = self._record([self._ref(provenance_source="totally-unknown-source-id")])
        self.assertTrue(self._errors(repo, "sources.unresolved"))

    def test_provenance_source_not_on_record_is_an_error(self):
        """`erratum.sources` doesn't cite the provenance_source at all."""
        self._standard_fixture(pool_cards=[card(71044499, "Nobleman of Crossout")])
        self.add_erratum_v2(
            id="erratum-parity-only",
            modern={"passcode": 71044499, "name": "Nobleman of Crossout"},
            classification="cosmetic",
            events={"e1": v2_event(transitions=[v2_transition(kind="cosmetic")])},
            states=[],
            sources=["some-other-source"],
            reference_identities=[self._ref(provenance_source="test-source")],
        )
        repo = self._repo()
        self.assertTrue(self._errors(repo, "erratum.reference-identity-provenance-not-in-sources"))

    def test_strict_passcode_errors(self):
        repo = self._record([self._ref(historical_passcode="not-a-passcode")])
        self.assertTrue(self._errors(repo, "erratum.malformed-passcode"))

    def test_missing_passcode_is_an_error(self):
        ref = self._ref()
        del ref["historical_passcode"]
        repo = self._record([ref])
        self.assertTrue(self._errors(repo, "erratum.no-historical-passcode"))

    def test_bad_variant_is_an_error(self):
        repo = self._record(
            [self._ref(historical_variant_passcodes=["not-a-passcode"])]
        )
        self.assertTrue(self._errors(repo, "erratum.malformed-passcode"))

    def test_out_of_range_variant_is_an_error(self):
        repo = self._record(
            [self._ref(historical_passcode=504700116, historical_variant_passcodes=[504700200])]
        )
        self.assertTrue(self._errors(repo, "erratum.variant-out-of-range"))

    def test_modern_passcode_as_reference_identity_is_rejected(self):
        repo = self._record([self._ref(historical_passcode=71044499)])
        self.assertTrue(self._errors(repo, "erratum.reference-identity-matches-modern"))

    def test_missing_upstream_is_an_error(self):
        ref = self._ref()
        del ref["upstream"]
        repo = self._record([ref])
        self.assertTrue(self._errors(repo, "erratum.reference-identity-missing-upstream"))

    def test_missing_reference_id_is_an_error(self):
        ref = self._ref()
        del ref["reference_id"]
        repo = self._record([ref])
        self.assertTrue(self._errors(repo, "erratum.reference-identity-missing-id"))

    def test_well_formed_entry_is_accepted(self):
        repo = self._record([self._ref()])
        codes = {f.code for f in Validator(repo).validate()}
        self.assertFalse({c for c in codes if c.startswith("erratum.reference-identity-")})


class ReferenceIdentityParityPrecedenceTest(V2ConsumerTestBase):
    """Task section 4's frozen precedence: exclude > include > exact
    matching reference_identity > structural walk > chronology. A matching
    but malformed/mismatched identity fails safe rather than falling
    through."""

    def _fixture(self, reference_identities, parity_reference_id="project-ignis-goat", **fmt_kw):
        self._standard_fixture(
            pool_cards=[card(71044499, "Nobleman of Crossout")],
            errata_overrides={
                "reference_parity": {
                    "reason": "test",
                    "reference_id": parity_reference_id,
                    "provenance_source": "test-source",
                    "sources": ["test-source"],
                },
                "sources": ["test-source"],
            },
            **fmt_kw,
        )
        self.add_erratum_v2(
            id="erratum-parity-only",
            modern={"passcode": 71044499, "name": "Nobleman of Crossout"},
            classification="cosmetic",
            events={"e1": v2_event(transitions=[v2_transition(kind="cosmetic")])},
            states=[],
            reference_identities=reference_identities,
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        return repo, fmt

    def _ref(self, **overrides):
        base = {
            "reference_id": "project-ignis-goat",
            "provenance_source": "test-source",
            "historical_passcode": 504700116,
            "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb",
        }
        base.update(overrides)
        return base

    def test_matching_reference_id_exact_identity_wins_before_parity_walk(self):
        repo, fmt = self._fixture([self._ref(historical_passcode=504700116)])
        overrides = select_applicable_errata(fmt, repo)
        override = overrides[71044499]
        self.assertIsInstance(override.implementation, ReferenceIdentity)
        self.assertEqual((504700116, ()), historical_identity(override.implementation))

    def test_missing_matching_identity_falls_back_to_old_walk(self):
        """No reference_identities at all: falls through to the structural
        walk exactly as before this task."""
        self._standard_fixture(
            pool_cards=[card(71044499, "Nobleman of Crossout")],
            errata_overrides={
                "reference_parity": {
                    "reason": "test",
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "sources": ["test-source"],
                },
                "sources": ["test-source"],
            },
        )
        self.add_erratum_v2(
            id="erratum-v2-beta",
            modern={"passcode": 200, "name": "Beta"},
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000077)}],
        )
        self.add_pool(cards=[card(71044499, "Nobleman of Crossout"), card(200, "Beta")])
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        override = overrides[200]
        self.assertIsInstance(override.implementation, ImplementationCoverage)
        self.assertEqual((511000077, ()), historical_identity(override.implementation))

    def test_malformed_matching_identity_fails_safe(self):
        """A matching reference_id entry with no usable passcode - the
        build must refuse, never fall back to the structural walk."""
        self._standard_fixture(
            pool_cards=[card(71044499, "Nobleman of Crossout")],
            errata_overrides={
                "reference_parity": {
                    "reason": "test",
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "sources": ["test-source"],
                },
                "sources": ["test-source"],
            },
        )
        self.add_erratum_v2(
            id="erratum-parity-only",
            modern={"passcode": 71044499, "name": "Nobleman of Crossout"},
            classification="cosmetic",
            events={"e1": v2_event(transitions=[v2_transition(kind="cosmetic")])},
            states=[
                {"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=999888777)}
            ],  # a structural fallback WOULD find this if the walk ran
            reference_identities=[
                {
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb",
                    # no historical_passcode - malformed
                }
            ],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        with self.assertRaises(Exception):
            from retroformats.lflist import ErrataSelectionError

            try:
                select_applicable_errata(fmt, repo)
            except ErrataSelectionError:
                raise

    def test_reference_id_absent_from_format_preserves_old_behaviour(self):
        """A format with NO reference_id at all: identical to
        pre-this-task behaviour, the structural walk runs directly. Uses a
        record WITH a relevant event (unlike the parity-only fixtures
        elsewhere in this class) because a zero-relevant-event record's
        only state is always the synthesised-MODERN terminal one - the
        structural walk can never find anything there regardless of
        reference_id, which is exactly the representation gap this task
        closes, not what this test is checking."""
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "reference_parity": {"reason": "test", "provenance_source": "test-source", "sources": ["test-source"]},
                "sources": ["test-source"],
            },
        )
        self.add_erratum_v2(
            id="erratum-v2-beta",
            modern={"passcode": 200, "name": "Beta"},
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=504700200)}],
            reference_identities=[self._ref(historical_passcode=504700116)],  # present, but format ignores it
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        override = overrides[200]
        self.assertIsInstance(override.implementation, ImplementationCoverage)
        self.assertEqual((504700200, ()), historical_identity(override.implementation))

    def test_reference_identity_on_a_relevant_event_record_is_allowed(self):
        """Section 4: a v2 record WITH relevant behavioural events may
        also carry a reference_identity, and exact parity still wins."""
        self._standard_fixture(
            pool_cards=[card(200, "Beta")],
            errata_overrides={
                "reference_parity": {
                    "reason": "test",
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "sources": ["test-source"],
                },
                "sources": ["test-source"],
            },
        )
        self.add_erratum_v2(
            id="erratum-v2-beta",
            modern={"passcode": 200, "name": "Beta"},
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000001)}],
            reference_identities=[
                {
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "historical_passcode": 511000099,  # DIFFERENT from the coverage-walk passcode
                    "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb",
                }
            ],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        overrides = select_applicable_errata(fmt, repo)
        override = overrides[200]
        self.assertIsInstance(override.implementation, ReferenceIdentity)
        self.assertEqual((511000099, ()), historical_identity(override.implementation))

    def test_provenance_source_mismatch_is_a_configuration_error(self):
        repo, fmt = self._fixture(
            [self._ref(provenance_source="a-different-source")],
        )
        self.add_pool(cards=[card(71044499, "Nobleman of Crossout")])
        self._standard_fixture(
            pool_cards=[card(71044499, "Nobleman of Crossout")],
            errata_overrides={
                "reference_parity": {
                    "reason": "test",
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "sources": ["test-source", "a-different-source"],
                },
                "sources": ["test-source", "a-different-source"],
            },
        )
        self.add_erratum_v2(
            id="erratum-parity-only",
            modern={"passcode": 71044499, "name": "Nobleman of Crossout"},
            classification="cosmetic",
            events={"e1": v2_event(transitions=[v2_transition(kind="cosmetic")])},
            states=[],
            sources=["test-source", "a-different-source"],
            reference_identities=[self._ref(provenance_source="a-different-source")],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        snapshot = day(fmt.snapshot)
        v = Validator(repo)
        v.validate()
        codes = {f.code for f in v.errors}
        self.assertIn("erratum.reference-identity-invalid", codes)


class SelectedOverrideCarrierTest(V2ConsumerTestBase):
    """SelectedOverride/historical_identity handles ReferenceIdentity
    directly, without disguising it as Coverage or a v1 dict."""

    def test_historical_identity_reads_a_reference_identity_directly(self):
        identity = ReferenceIdentity(
            reference_id="project-ignis-goat",
            provenance_source="ignis-lflists",
            historical_passcode=504700116,
            historical_variant_passcodes=(),
            upstream="ProjectIgnis/BabelCDB goat-entries.cdb",
            script=None,
        )
        self.assertEqual((504700116, ()), historical_identity(identity))

    def test_build_lflist_emits_the_reference_identity_passcode(self):
        self._standard_fixture(
            pool_cards=[card(71044499, "Nobleman of Crossout")],
            errata_overrides={
                "reference_parity": {
                    "reason": "test",
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "sources": ["test-source"],
                },
                "sources": ["test-source"],
            },
        )
        self.add_erratum_v2(
            id="erratum-parity-only",
            modern={"passcode": 71044499, "name": "Nobleman of Crossout"},
            classification="cosmetic",
            events={"e1": v2_event(transitions=[v2_transition(kind="cosmetic")])},
            states=[],
            reference_identities=[
                {
                    "reference_id": "project-ignis-goat",
                    "provenance_source": "test-source",
                    "historical_passcode": 504700116,
                    "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb",
                }
            ],
        )
        repo = self._repo()
        fmt = self._fmt(repo)
        built = build_lflist(fmt, repo)
        self.assertIn(504700116, built.entries)
        self.assertNotIn(71044499, built.entries)


if __name__ == "__main__":
    unittest.main()
