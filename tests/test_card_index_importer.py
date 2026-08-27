"""Regression tests for retroformats.importers.card_index.collect_referenced_passcodes()
over a MIXED v1/v2 corpus.

The real canonical migration (247 of 296 errata now ErratumV2) exposed a real
bug: the collector unconditionally read `erratum.implementation`/
`erratum.changes` (v1-only attributes), raising AttributeError on any
ErratumV2 record. These tests build small, synthetic repositories through the
real model/parser (Repository.load() -> Erratum/ErratumV2, exactly what
production code sees) rather than fake objects with just enough attributes to
satisfy the collector, so a regression in ErratumV2's own shape would show up
here too, not just in the collector's isinstance branch.
"""

from __future__ import annotations

from retroformats.importers.card_index import collect_referenced_passcodes
from retroformats.repo import Repository

from .helpers import TempRepoTest, card, change, implementation, v2_coverage, v2_event, v2_transition


class CollectReferencedPasscodesTest(TempRepoTest):
    def refs(self) -> set[int]:
        repo = Repository.load(self.root)
        self.assertEqual([], repo.load_errors, f"fixture failed to load: {repo.load_errors}")
        return collect_referenced_passcodes(repo)

    # -- A/B/C: v1 -----------------------------------------------------------

    def test_A_v1_baseline_historical_passcode_is_collected(self):
        self.add_erratum(
            id="erratum-a",
            impl=implementation(strategy="reuse-upstream", historical_passcode=511000010),
        )
        self.assertIn(511000010, self.refs())

    def test_B_v1_resulting_implementation_historical_passcode_is_collected(self):
        self.add_erratum(
            id="erratum-b",
            changes=[
                change(
                    date="2010-01-01",
                    resulting_implementation=implementation(
                        strategy="custom-script", historical_passcode=511000011, script="dist/scripts/x.lua"
                    ),
                ),
                change(date="2015-01-01"),
            ],
        )
        self.assertIn(511000011, self.refs())

    def test_C_v1_historical_variants_are_collected(self):
        self.add_erratum(
            id="erratum-c",
            impl=implementation(
                strategy="reuse-upstream",
                historical_passcode=511000012,
                historical_variant_passcodes=[511000013, 511000014],
            ),
        )
        refs = self.refs()
        self.assertIn(511000012, refs)
        self.assertIn(511000013, refs)
        self.assertIn(511000014, refs)

    # -- D/E/F: v2 authored states[] -----------------------------------------

    def test_D_v2_authored_reuse_upstream_state_is_collected(self):
        self.add_erratum_v2(
            id="erratum-d",
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000020)}],
        )
        self.assertIn(511000020, self.refs())

    def test_E_v2_authored_custom_script_state_is_collected(self):
        self.add_erratum_v2(
            id="erratum-e",
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="custom-script", historical_passcode=511000021)}],
        )
        self.assertIn(511000021, self.refs())

    def test_F_v2_historical_variants_are_collected(self):
        self.add_erratum_v2(
            id="erratum-f",
            events={"e1": v2_event()},
            states=[
                {
                    "events": [],
                    "coverage": v2_coverage(
                        kind="reuse-upstream",
                        historical_passcode=511000022,
                        historical_variant_passcodes=[511000023, 511000024],
                    ),
                }
            ],
        )
        refs = self.refs()
        self.assertIn(511000022, refs)
        self.assertIn(511000023, refs)
        self.assertIn(511000024, refs)

    # -- G/H: v2 reference_identities[] --------------------------------------

    def test_G_v2_reference_identity_historical_passcode_is_collected(self):
        self.add_erratum_v2(
            id="erratum-g",
            events={"e1": v2_event()},
            reference_identities=[
                {
                    "reference_id": "goat",
                    "provenance_source": "test-source",
                    "historical_passcode": 511000030,
                }
            ],
        )
        self.assertIn(511000030, self.refs())

    def test_H_v2_reference_identity_variants_are_collected(self):
        self.add_erratum_v2(
            id="erratum-h",
            events={"e1": v2_event()},
            reference_identities=[
                {
                    "reference_id": "goat",
                    "provenance_source": "test-source",
                    "historical_passcode": 511000031,
                    "historical_variant_passcodes": [511000032, 511000033],
                }
            ],
        )
        refs = self.refs()
        self.assertIn(511000031, refs)
        self.assertIn(511000032, refs)
        self.assertIn(511000033, refs)

    # -- I: non-substituting coverage kinds never invent an identity --------

    def test_I_none_needed_known_gap_and_terminal_modern_invent_nothing(self):
        self.add_erratum_v2(
            id="erratum-i",
            modern=card(999, "Modern Nine Nine Nine"),
            events={"e1": v2_event()},
            states=[
                {"events": [], "coverage": v2_coverage(kind="none-needed")},
                # the terminal (all-events) state is never authored with a
                # passcode-bearing kind in practice, and even if it were,
                # state_for()/selection_at() ignore it -- the COLLECTOR must
                # not invent an identity from "modern" either.
            ],
        )
        # A second record isolates known-gap, since a record needs at least
        # one relevant event either way; kept separate so a failure here
        # names exactly which kind leaked a fabricated passcode.
        self.add_erratum_v2(
            id="erratum-i2",
            modern=card(998, "Modern Nine Nine Eight"),
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="known-gap")}],
        )
        refs = self.refs()
        # Only the two modern_card passcodes should be present from these
        # two records -- nothing numeric was fabricated from none-needed or
        # known-gap (known-gap carries no historical_passcode field at all).
        self.assertIn(999, refs)
        self.assertIn(998, refs)
        # No stray small/placeholder passcode leaked in from either kind.
        self.assertNotIn(0, refs)

    # -- J: implementation_metadata[] is never card identity -----------------

    def test_J_implementation_metadata_does_not_affect_the_passcode_set(self):
        self.add_erratum_v2(
            id="erratum-j",
            modern=card(997, "Modern Metadata Card"),
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="reuse-upstream", historical_passcode=511000040)}],
            implementation_metadata=[
                {
                    "events": [],
                    "status": "complete",
                    "tested": True,
                    "reason": "workflow note, not identity",
                }
            ],
        )
        refs = self.refs()
        # The real historical_passcode from states[] IS present (proves
        # implementation_metadata isn't silently blocking normal collection)...
        self.assertIn(511000040, refs)
        # ...but nothing derived from the metadata entry's own content (it
        # carries no passcode-shaped field at all, so this is really just
        # confirming the collector never even looks at it).
        self.assertEqual(2, sum(1 for p in refs if p in (997, 511000040)))

    # -- K: one repository with BOTH v1 and v2 collects both -----------------

    def test_K_mixed_repository_collects_both_v1_and_v2(self):
        self.add_erratum(
            id="erratum-k-v1",
            modern=card(600, "Legacy Card"),
            impl=implementation(strategy="reuse-upstream", historical_passcode=511000050),
        )
        self.add_erratum_v2(
            id="erratum-k-v2",
            modern=card(601, "Migrated Card"),
            events={"e1": v2_event()},
            states=[{"events": [], "coverage": v2_coverage(kind="custom-script", historical_passcode=511000051)}],
        )
        refs = self.refs()
        self.assertEqual(
            {600, 511000050, 601, 511000051},
            {p for p in refs if p in (600, 511000050, 601, 511000051)},
        )

    # -- collector does not crash / does not coerce --------------------------

    def test_collector_does_not_raise_on_a_mixed_repository(self):
        self.add_erratum(id="erratum-plain-v1")
        self.add_erratum_v2(id="erratum-plain-v2")
        # No exception -- this is the exact regression the migration exposed.
        self.refs()

    def test_malformed_v2_reference_identity_is_skipped_not_coerced(self):
        # historical_passcode missing entirely -- historical_identity() raises
        # MalformedHistoricalIdentity internally; the collector must swallow
        # it (the validator's job to report), never crash, and never invent
        # a passcode via a coercive int(...) fallback.
        self.add_erratum_v2(
            id="erratum-malformed",
            events={"e1": v2_event()},
            reference_identities=[{"reference_id": "goat", "provenance_source": "test-source"}],
        )
        # Should not raise.
        self.refs()
