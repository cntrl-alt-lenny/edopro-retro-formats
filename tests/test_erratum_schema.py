"""Schema-level tests for schemas/erratum.schema.json's v2 shapes.

These exercise the actual schema file (via tests/schema_check.py's
dependency-free JSON Schema subset checker), not a reimplementation of its
rules in Python — a typo in the schema's if/then/oneOf structure should fail
a test here. Covers the holes closed in this pass: co-occurrence needs its
own event-level evidence (invariant 10), a directly-sourced ordering edge
needs a citation (not just a note), authored coverage is a real discriminated
sum type per kind (not a shared bag of optional fields, and 'unresolved' is
never authorable), state.events/ordering.chains reject duplicate ids, and the
full v2 shape requires an (even empty) `ordering` block.
"""

from __future__ import annotations

import glob
import json
import unittest
from pathlib import Path

from .schema_check import REPO_ROOT, Registry, validate as schema_validate, validate_erratum

REGISTRY = Registry()

# The one pre-existing, unrelated data/schema mismatch in the corpus today
# (data/errata/spiritual-energy-settle-machine.json has a stray top-level
# `implementation.reason` field the schema has never allowed outside
# `implementation.gap.reason`) — confirmed pre-existing against the prior
# (v1-only) schema too, not introduced by the v2 addition. Flagged separately
# for a data fix; not this schema's job to accept it.
KNOWN_PRE_EXISTING_FAILURE = "spiritual-energy-settle-machine"


def is_valid(doc: dict) -> bool:
    return not validate_erratum(doc, REGISTRY)


# -- shared builders ---------------------------------------------------------

def giant_rat_v2() -> dict:
    """The design doc's own worked example (docs/research/erratum-state-model-v2.md
    §2): two separate, unordered events, three authored states."""
    return {
        "id": "erratum-giant-rat",
        "modern_card": {"passcode": 97017120, "name": "Giant Rat"},
        "classification": "ruling",
        "events": {
            "verification": {
                "effective": {
                    "date": None,
                    "old_attested_through": "2011-02-02",
                    "new_attested_from": "2019-04-03",
                },
                "transitions": [
                    {
                        "kind": "ruling",
                        "axis": "search-reveal-procedure",
                        "summary": "Deck-reveal-on-whiff required.",
                        "sources": ["s-verification"],
                    }
                ],
            },
            "activation-semantics": {
                "effective": {"date": None},
                "transitions": [
                    {
                        "kind": "ruling",
                        "axis": "search-activation-legality",
                        "summary": "No-valid-target activation allowance.",
                        "sources": ["s-activation"],
                    }
                ],
            },
        },
        "ordering": {},
        "states": [
            {
                "events": [],
                "coverage": {
                    "kind": "reuse-upstream",
                    "historical_passcode": 504700172,
                    "upstream": "ProjectIgnis/BabelCDB goat-entries.cdb",
                },
            },
            {
                "events": ["activation-semantics"],
                "coverage": {
                    "kind": "known-gap",
                    "gap_reason": "No upstream implementation exists for a state where only one had changed.",
                    "gap_sources": ["s-gap"],
                },
            },
            {"events": ["verification", "activation-semantics"], "coverage": {"kind": "modern"}},
        ],
        "sources": ["s-top"],
    }


def single_event_v2(**overrides) -> dict:
    """A minimal, ordinary full-v2 record: one event, one transition."""
    doc = {
        "id": "erratum-single",
        "modern_card": {"passcode": 11111111, "name": "Single"},
        "classification": "functional",
        "events": {
            "e1": {
                "effective": {"date": "2020-01-01", "precision": "day"},
                "transitions": [
                    {"kind": "functional", "summary": "A change.", "sources": ["s1"]}
                ],
            }
        },
        "ordering": {},
        "sources": ["s-top"],
    }
    doc.update(overrides)
    return doc


def two_undated_events_v2(**overrides) -> dict:
    """Two events with no chronology at all — used to build ordering-edge cases."""
    doc = {
        "id": "erratum-two-undated",
        "modern_card": {"passcode": 22222222, "name": "Two Undated"},
        "classification": "ruling",
        "events": {
            "x1": {
                "effective": {"date": None},
                "transitions": [{"kind": "ruling", "summary": "First.", "sources": ["s1"]}],
            },
            "x2": {
                "effective": {"date": None},
                "transitions": [{"kind": "ruling", "summary": "Second.", "sources": ["s2"]}],
            },
        },
        "ordering": {},
        "sources": ["s-top"],
    }
    doc.update(overrides)
    return doc


def flattened_sugar(**overrides) -> dict:
    doc = {
        "id": "erratum-flattened",
        "modern_card": {"passcode": 33333333, "name": "Flattened"},
        "classification": "functional",
        "event": {
            "effective": {"date": "2015-06-01", "precision": "day"},
            "kind": "functional",
            "summary": "A change.",
            "sources": ["s1"],
        },
        "coverage": {"kind": "reuse-upstream", "historical_passcode": 511000000, "upstream": "ProjectIgnis"},
        "sources": ["s-top"],
    }
    doc.update(overrides)
    return doc


class PositiveShapeTest(unittest.TestCase):
    """Documents this schema accepts must actually validate — every worked
    example the design doc gives, and the ordinary common cases."""

    def test_giant_rat_full_v2_shape(self):
        self.assertEqual(validate_erratum(giant_rat_v2(), REGISTRY), [])

    def test_ordinary_single_transition_event(self):
        self.assertEqual(validate_erratum(single_event_v2(), REGISTRY), [])

    def test_sourced_genuine_cooccurrence_event(self):
        doc = {
            "id": "erratum-policy-revision",
            "modern_card": {"passcode": 44444444, "name": "Policy Revision"},
            "classification": "ruling",
            "events": {
                "policy-revision": {
                    "effective": {"date": None, "basis": "Konami policy revision, exact date unresolved"},
                    "transitions": [
                        {"kind": "ruling", "axis": "axis-a", "summary": "Behaviour A.", "sources": ["s1"]},
                        {"kind": "ruling", "axis": "axis-b", "summary": "Behaviour B.", "sources": ["s2"]},
                    ],
                    "cooccurrence_sources": ["s-cooccurrence"],
                }
            },
            "ordering": {},
            "sources": ["s-top"],
        }
        self.assertEqual(validate_erratum(doc, REGISTRY), [])

    def test_date_proven_edge_via_chains(self):
        doc = {
            "id": "erratum-chained",
            "modern_card": {"passcode": 55555555, "name": "Chained"},
            "classification": "functional",
            "events": {
                "v1": {"effective": {"date": "2005-01-01"}, "transitions": [{"kind": "functional", "summary": "s", "sources": ["s"]}]},
                "v2": {"effective": {"date": "2010-01-01"}, "transitions": [{"kind": "functional", "summary": "s", "sources": ["s"]}]},
            },
            "ordering": {"chains": [["v1", "v2"]]},
            "sources": ["s-top"],
        }
        self.assertEqual(validate_erratum(doc, REGISTRY), [])

    def test_directly_sourced_edge_with_source_refs(self):
        doc = two_undated_events_v2()
        doc["ordering"] = {
            "edges": [
                {
                    "before": "x1",
                    "after": "x2",
                    "basis": "directly-sourced",
                    "note": "A period ruling document states x1 preceded x2.",
                    "sources": ["s-order"],
                }
            ]
        }
        self.assertEqual(validate_erratum(doc, REGISTRY), [])

    def test_researcher_inference_edge_needs_only_a_note(self):
        doc = two_undated_events_v2()
        doc["ordering"] = {
            "edges": [
                {
                    "before": "x1",
                    "after": "x2",
                    "basis": "researcher-inference",
                    "note": "Inferred from the functional change reading as a refinement of the ruling change.",
                }
            ]
        }
        self.assertEqual(validate_erratum(doc, REGISTRY), [])

    def test_flattened_ordinary_historical_record(self):
        self.assertEqual(validate_erratum(flattened_sugar(), REGISTRY), [])

    def test_flattened_sugar_none_needed_is_valid(self):
        doc = flattened_sugar(coverage={"kind": "none-needed"})
        self.assertEqual(validate_erratum(doc, REGISTRY), [])

    def test_custom_script_with_required_identity_is_valid(self):
        doc = giant_rat_v2()
        doc["states"][0]["coverage"] = {
            "kind": "custom-script",
            "historical_passcode": 511000001,
            "script": "dist/scripts/c511000001.lua",
        }
        self.assertEqual(validate_erratum(doc, REGISTRY), [])


class NegativeShapeTest(unittest.TestCase):
    """Documents this schema must reject — the holes this pass closed."""

    def test_two_transition_event_without_cooccurrence_sources_is_rejected(self):
        doc = {
            "id": "erratum-policy-revision-bad",
            "modern_card": {"passcode": 66666666, "name": "Bad Policy Revision"},
            "classification": "ruling",
            "events": {
                "policy-revision": {
                    "effective": {"date": None},
                    "transitions": [
                        {"kind": "ruling", "axis": "axis-a", "summary": "A", "sources": ["s1"]},
                        {"kind": "ruling", "axis": "axis-b", "summary": "B", "sources": ["s2"]},
                    ],
                    # cooccurrence_sources deliberately omitted
                }
            },
            "ordering": {},
            "sources": ["s-top"],
        }
        self.assertFalse(is_valid(doc))

    def test_single_transition_event_does_not_require_cooccurrence_sources(self):
        # The negative case's mirror: a lone transition must NOT be forced to
        # cite redundant co-occurrence evidence it has no claim to make.
        self.assertEqual(validate_erratum(single_event_v2(), REGISTRY), [])

    def test_directly_sourced_edge_without_source_refs_is_rejected(self):
        doc = two_undated_events_v2()
        doc["ordering"] = {
            "edges": [
                {"before": "x1", "after": "x2", "basis": "directly-sourced", "note": "A period document says so."}
                # sources deliberately omitted
            ]
        }
        self.assertFalse(is_valid(doc))

    def test_authored_coverage_kind_unresolved_is_rejected(self):
        doc = giant_rat_v2()
        doc["states"][1]["coverage"] = {"kind": "unresolved"}
        self.assertFalse(is_valid(doc))

    def test_reuse_upstream_missing_implementation_identity_is_rejected(self):
        doc = giant_rat_v2()
        del doc["states"][0]["coverage"]["upstream"]
        self.assertFalse(is_valid(doc))

    def test_custom_script_missing_implementation_identity_is_rejected(self):
        doc = giant_rat_v2()
        doc["states"][0]["coverage"] = {"kind": "custom-script", "historical_passcode": 511000002}
        # script deliberately omitted
        self.assertFalse(is_valid(doc))

    def test_known_gap_carrying_historical_implementation_fields_is_rejected(self):
        doc = giant_rat_v2()
        doc["states"][1]["coverage"] = {
            "kind": "known-gap",
            "gap_reason": "r",
            "gap_sources": ["s"],
            "historical_passcode": 511000003,
        }
        self.assertFalse(is_valid(doc))

    def test_duplicate_event_id_inside_state_events_is_rejected(self):
        doc = giant_rat_v2()
        doc["states"][2]["events"] = ["verification", "verification"]
        self.assertFalse(is_valid(doc))

    def test_duplicate_id_inside_one_ordering_chain_is_rejected(self):
        doc = single_event_v2()
        doc["ordering"] = {"chains": [["e1", "e1"]]}
        self.assertFalse(is_valid(doc))

    def test_flattened_sugar_with_coverage_kind_modern_is_rejected(self):
        doc = flattened_sugar(coverage={"kind": "modern"})
        self.assertFalse(is_valid(doc))

    def test_full_v2_shape_missing_ordering_entirely_is_rejected(self):
        doc = single_event_v2()
        del doc["ordering"]
        self.assertFalse(is_valid(doc))

    def test_mixed_v1_and_v2_fields_is_rejected(self):
        doc = {
            "id": "erratum-mixed",
            "modern_card": {"passcode": 77777777, "name": "Mixed"},
            "classification": "functional",
            "changes": [{"kind": "functional", "effective": {"date": "2020-01-01"}, "summary": "s", "sources": ["s"]}],
            "implementation": {"strategy": "none-needed", "status": "complete"},
            "events": {"e1": {"effective": {"date": None}, "transitions": [{"kind": "ruling", "summary": "s", "sources": ["s"]}]}},
            "ordering": {},
            "sources": ["s"],
        }
        self.assertFalse(is_valid(doc))


class CorpusRegressionTest(unittest.TestCase):
    """Every currently-migrated (v1-shaped) record must still validate — this
    pass's job was to ADD v2 alongside v1, not to change what v1 accepts."""

    def test_every_errata_record_validates_except_the_one_known_pre_existing_failure(self):
        failures = []
        for path in sorted(glob.glob(str(REPO_ROOT / "data" / "errata" / "*.json"))):
            if KNOWN_PRE_EXISTING_FAILURE in path:
                continue
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            errors = validate_erratum(doc, REGISTRY)
            if errors:
                failures.append((Path(path).name, errors[:3]))
        self.assertEqual(failures, [], f"{len(failures)} record(s) unexpectedly failed schema validation")

    def test_the_one_known_pre_existing_failure_is_still_exactly_that(self):
        # Guards against silently masking a real regression as "the known
        # one": if this ever starts passing, the mismatch was fixed elsewhere
        # and this exclusion should be removed; if a DIFFERENT error appears,
        # something about the schema or the file changed and needs a look.
        path = REPO_ROOT / "data" / "errata" / f"{KNOWN_PRE_EXISTING_FAILURE}.json"
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        errors = validate_erratum(doc, REGISTRY)
        self.assertEqual(len(errors), 1)
        self.assertIn("implementation", errors[0])
        self.assertIn("reason", errors[0])


if __name__ == "__main__":
    unittest.main()


class CosmeticEngineSugarTest(unittest.TestCase):
    """Sugar is only for a single FUNCTIONAL or RULING transition.

    A cosmetic/engine-only event creates no implementation-state dimension,
    so its relevant-event set is empty, `{}` IS the terminal state, and the
    terminal state's coverage is unconditionally 'modern' - which the sugar's
    required `authoredBaselineCoverage` rightly forbids. Permitting the shape
    made a record that is schema-valid but has no consistent runtime meaning:
    the authored coverage is silently discarded. Full v2 expresses these
    records correctly, with no authored states at all."""

    def test_cosmetic_sugar_is_rejected(self):
        doc = flattened_sugar(
            classification="cosmetic",
            event={
                "effective": {"date": "2011-07-01", "precision": "day"},
                "kind": "cosmetic",
                "summary": "PSCT rewording only.",
                "sources": ["s1"],
            },
            coverage={"kind": "none-needed"},
        )
        self.assertFalse(is_valid(doc))

    def test_engine_sugar_is_rejected(self):
        doc = flattened_sugar(
            classification="engine",
            event={
                "effective": {"date": "2008-03-01", "precision": "day"},
                "kind": "engine",
                "summary": "Rules-era difference.",
                "sources": ["s1"],
            },
            coverage={"kind": "none-needed"},
        )
        self.assertFalse(is_valid(doc))

    def test_functional_and_ruling_sugar_remain_valid(self):
        self.assertTrue(is_valid(flattened_sugar()))
        self.assertTrue(
            is_valid(
                flattened_sugar(
                    classification="ruling",
                    event={
                        "effective": {"date": None},
                        "kind": "ruling",
                        "summary": "Era procedure.",
                        "sources": ["s1"],
                    },
                )
            )
        )

    def test_equivalent_full_v2_cosmetic_record_is_valid(self):
        doc = {
            "id": "erratum-cosmetic-full",
            "modern_card": {"passcode": 33333333, "name": "Flattened"},
            "classification": "cosmetic",
            "events": {
                "psct": {
                    "effective": {"date": "2011-07-01", "precision": "day"},
                    "transitions": [
                        {"kind": "cosmetic", "summary": "PSCT rewording only.", "sources": ["s1"]}
                    ],
                }
            },
            "ordering": {},
            "sources": ["s-top"],
        }
        self.assertTrue(is_valid(doc))

    def test_equivalent_full_v2_engine_record_is_valid(self):
        doc = {
            "id": "erratum-engine-full",
            "modern_card": {"passcode": 33333333, "name": "Flattened"},
            "classification": "engine",
            "events": {
                "mr1": {
                    "effective": {"date": "2008-03-01", "precision": "day"},
                    "transitions": [
                        {"kind": "engine", "summary": "Rules-era difference.", "sources": ["s1"]}
                    ],
                }
            },
            "ordering": {},
            "sources": ["s-top"],
        }
        self.assertTrue(is_valid(doc))


class CoverageFieldMapAgreesWithSchemaTest(unittest.TestCase):
    """`retroformats.model.COVERAGE_FIELDS` is what the PRODUCTION validator
    enforces (it never runs the schema). This proves the two cannot drift:
    the map must equal the schema's own `coverage*` branches, field for
    field, so there is one coverage model rather than two."""

    def test_map_matches_schema_branches_exactly(self):
        from retroformats.model import COVERAGE_FIELDS

        schema = json.loads(
            (REPO_ROOT / "schemas" / "erratum.schema.json").read_text(encoding="utf-8")
        )
        defs = schema["$defs"]
        branches = {
            "modern": "coverageModern",
            "reuse-upstream": "coverageReuseUpstream",
            "custom-script": "coverageCustomScript",
            "none-needed": "coverageNoneNeeded",
            "known-gap": "coverageKnownGap",
        }
        self.assertEqual(set(branches), set(COVERAGE_FIELDS))
        for kind, def_name in branches.items():
            branch = defs[def_name]
            self.assertFalse(
                branch.get("additionalProperties", True),
                f"{def_name} must be a closed object for the map to be authoritative",
            )
            required, allowed = COVERAGE_FIELDS[kind]
            self.assertEqual(set(branch["required"]), set(required), f"{kind} required")
            self.assertEqual(set(branch["properties"]), set(allowed), f"{kind} allowed")


class PasscodeValiditySchemaAgreementTest(unittest.TestCase):
    """`retroformats.model._is_valid_passcode()` must classify every sample
    EXACTLY as this project's own schema checker does for the `passcode`
    $def (`type: integer, minimum: 1, maximum: 4294967295`) — never a
    re-guessed notion of "integer" (a coercive `int(value)` would silently
    accept "123", True, and 1.5, none of which this project's own
    `_matches_type(v, "integer")` treats as a JSON integer)."""

    SAMPLES = [
        1,
        4294967295,
        4294967296,
        0,
        -1,
        511000042,
        "123",
        "not-a-passcode",
        1.5,
        123.0,
        True,
        False,
        None,
        [1],
        {},
    ]

    def test_agrees_with_schema_check_for_every_sample(self):
        from retroformats.model import _is_valid_passcode

        registry = Registry()
        common = registry.docs["common.schema.json"]
        passcode_schema = common["$defs"]["passcode"]
        for value in self.SAMPLES:
            errors = schema_validate(passcode_schema, value, registry, common)
            self.assertEqual(not errors, _is_valid_passcode(value), f"value={value!r}")
