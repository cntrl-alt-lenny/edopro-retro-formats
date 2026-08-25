"""Tests for the dry-run migration materializer (final pre-migration gate,
task section 7/9).

**POST-MIGRATION NOTE**: the real 247-record canonical migration has
happened (commit immediately after
1937239d9fd0ebfb47dc850f298c11c3a60679b0). `MaterializedCorpusTest` below
now reads the FROZEN PRE-MIGRATION SNAPSHOT
(`tests.pre_migration_fixture.load_pre_migration_repo()`), never the live
`Repository.load(audit.REPO_ROOT)` - that would now return the mixed 247
v2 + 49 v1 reality, on which the materializer only has 49 records left to
work with. Reading the frozen snapshot instead means this class is now a
REPRODUCIBILITY proof: it confirms the materializer, run again today
against the exact same frozen pre-migration input, still deterministically
produces the exact target set that was actually written to `data/
errata/` - not merely that it once did. `ToSugarUnitTest` is unaffected
either way: it uses synthetic fixtures, never the corpus.
"""

from __future__ import annotations

import json
import unittest

from retroformats.model import ErratumV2
from retroformats.repo import Repository

from . import migration_audit as audit
from . import migration_materializer as mm
from .pre_migration_fixture import load_pre_migration_repo


class MaterializedCorpusTest(unittest.TestCase):
    """The section 9 headline, reproduced against the FROZEN pre-migration
    snapshot: every one of the 247 semantically-equivalent records'
    materialized target passes schema, load, preservation, and production
    semantic validation - computed once per class, since a full corpus
    materialize+verify pass is expensive and every test below reads the
    SAME immutable result. This is now a reproducibility check (task
    section 7): it proves the materializer, re-run today, still produces
    exactly the migration that was actually performed."""

    @classmethod
    def setUpClass(cls):
        cls.repo = load_pre_migration_repo()
        cls.audit_result = audit.audit_corpus(cls.repo)
        cls.rows = cls.audit_result["rows"]
        cls.by_id = {r["id"]: r for r in cls.rows}
        cls.materialized = mm.materialize_corpus(cls.repo, cls.rows)
        cls.verification = mm.verify_materialized_corpus(cls.repo, cls.rows)

    def test_generated_target_counts(self):
        self.assertEqual(247, self.verification["generated_target_count"])
        self.assertEqual(180, self.verification["sugar_target_count"])
        self.assertEqual(67, self.verification["full_target_count"])
        self.assertEqual(247, len(self.materialized["targets"]))
        self.assertEqual(180, len(self.materialized["sugar_ids"]))
        self.assertEqual(67, len(self.materialized["full_ids"]))

    def test_no_failures_of_any_kind(self):
        """The task's own required result: every list empty."""
        self.assertEqual([], self.verification["schema_failures"])
        self.assertEqual([], self.verification["load_failures"])
        self.assertEqual([], self.verification["preservation_failures"])
        self.assertEqual([], self.verification["validation_errors"])

    def test_every_target_matches_the_real_on_disk_file_exactly(self):
        """The actual proof behind this class's own reproducibility claim
        (found missing by adversarial review): every one of the 247
        freshly re-materialized targets, computed here from the FROZEN
        pre-migration snapshot, must equal - both structurally (parsed
        dict equality) AND byte-for-byte (the exact JSON text) - the REAL
        `data/errata/*.json` file currently on disk. Every other check in
        this class only tests the in-memory materializer output's own
        internal self-consistency; this is the one that actually compares
        it against reality, so a future divergence between migration_
        materializer.py's logic and the 247 committed files - from either
        side changing - would be caught here, not silently missed."""
        live_repo = Repository.load(audit.REPO_ROOT)
        content_mismatches = []
        byte_mismatches = []
        for record_id, target in self.materialized["targets"].items():
            path = live_repo.errata[record_id].path
            on_disk_text = path.read_text(encoding="utf-8")
            on_disk = json.loads(on_disk_text)
            if on_disk != target:
                content_mismatches.append(record_id)
                continue
            expected_text = json.dumps(target, indent=2, ensure_ascii=False) + "\n"
            if expected_text != on_disk_text:
                byte_mismatches.append(record_id)
        self.assertEqual([], content_mismatches, "materialized content differs from the on-disk file")
        self.assertEqual([], byte_mismatches, "content matches but JSON formatting differs from the on-disk file")

    def test_excluded_ids_are_exactly_the_frozen_49(self):
        self.assertEqual(49, len(self.materialized["excluded_ids"]))
        self.assertEqual(
            sorted(r["id"] for r in self.rows if not r["equivalent"]),
            self.materialized["excluded_ids"],
        )
        self.assertEqual(
            set(self.materialized["targets"]) | set(self.materialized["excluded_ids"]),
            {r["id"] for r in self.rows},
        )
        self.assertEqual(
            set(),
            set(self.materialized["targets"]) & set(self.materialized["excluded_ids"]),
        )

    def test_full_67_breakdown_matches_the_task_accounting(self):
        """35 one-relevant-with-nonrelevant-siblings + 11 fully-ordered
        multi-relevant + 11 parity-only-identity + 10 pure cosmetic/engine
        = 67."""
        counts: dict[str, int] = {}
        for record_id in self.materialized["full_ids"]:
            category = self.by_id[record_id]["category"]
            counts[category] = counts.get(category, 0) + 1
        self.assertEqual(
            {
                audit.CAT_FULL_SINGLE: 35,
                audit.CAT_MULTI_ORDERED: 11,
                audit.CAT_PARITY_ONLY: 11,
                audit.CAT_COSMETIC_ONLY: 10,
            },
            counts,
        )
        self.assertEqual(67, sum(counts.values()))

    def test_sugar_180_are_exactly_the_sugar_eligible_category(self):
        self.assertEqual(
            sorted(r["id"] for r in self.rows if r["equivalent"] and r["category"] == audit.CAT_SUGAR),
            self.materialized["sugar_ids"],
        )

    def test_every_sugar_eligible_record_has_an_authorable_baseline(self):
        """`is_sugar_eligible()`'s third condition (an authorable baseline
        coverage, beyond the two `compare()`'s own `sugar_eligible` field
        already checks) never actually demotes any of the 180 in the
        CURRENT corpus - verified here, not assumed, exactly like this
        module's own docstring promises."""
        for record_id in self.materialized["sugar_ids"]:
            record = self.repo.errata[record_id]
            self.assertTrue(mm.is_sugar_eligible(record), record_id)
        # And the inverse: nothing outside the 180 is sugar-shaped.
        for record_id in self.materialized["full_ids"]:
            record = self.repo.errata[record_id]
            self.assertFalse(mm.is_sugar_eligible(record), record_id)

    def test_sugar_shape_has_the_flattened_keys_only(self):
        sample_id = self.materialized["sugar_ids"][0]
        target = self.materialized["targets"][sample_id]
        self.assertIn("event", target)
        self.assertIn("coverage", target)
        self.assertNotIn("events", target)
        self.assertNotIn("ordering", target)
        self.assertNotIn("states", target)
        self.assertEqual(mm.SCHEMA_PATH, target["$schema"])

    def test_full_shape_has_the_structured_keys_only(self):
        sample_id = self.materialized["full_ids"][0]
        target = self.materialized["targets"][sample_id]
        self.assertIn("events", target)
        self.assertIn("states", target)
        self.assertNotIn("event", target)
        self.assertNotIn("coverage", target)
        self.assertEqual(mm.SCHEMA_PATH, target["$schema"])

    def test_materialization_is_deterministic(self):
        """Same input, same output - required by this module's own
        docstring ('deterministic migration materializer')."""
        again = mm.materialize_corpus(self.repo, self.rows)
        self.assertEqual(self.materialized["targets"], again["targets"])

    def test_ordering_never_comes_from_v1_array_position(self):
        """Every full-shape target's ordering edges are exactly the
        date-proven ones `ordering_proof()` computes - the same set
        `candidate_v2_raw()` (reused verbatim by the materializer for the
        full shape) already produces, never re-derived from `changes[]`
        position by this module."""
        for record_id in self.materialized["full_ids"]:
            record = self.repo.errata[record_id]
            reference_identities = audit.derive_reference_identities(record, self.repo)
            expected_raw = audit.candidate_v2_raw(record, reference_identities)
            target = self.materialized["targets"][record_id]
            self.assertEqual(expected_raw.get("ordering", {}), target.get("ordering", {}), record_id)

    def test_reference_identities_only_on_the_11_parity_only_records(self):
        parity_only_ids = {
            r["id"] for r in self.rows if r["equivalent"] and r["category"] == audit.CAT_PARITY_ONLY
        }
        self.assertEqual(11, len(parity_only_ids))
        for record_id, target in self.materialized["targets"].items():
            identities = target.get("reference_identities") or []
            if record_id in parity_only_ids:
                self.assertEqual(1, len(identities), record_id)
            else:
                self.assertEqual([], identities, record_id)


class ToSugarUnitTest(unittest.TestCase):
    """`_to_sugar()` in isolation, independent of the real corpus."""

    def _full_raw(self, **overrides):
        raw = {
            "id": "erratum-synthetic",
            "modern_card": {"passcode": 200, "name": "Synthetic"},
            "classification": "ruling",
            "events": {
                "c0": {
                    "effective": {"date": "2010-01-01"},
                    "transitions": [
                        {
                            "kind": "ruling",
                            "axis": "targeting",
                            "historical_text": "old",
                            "modern_text": "new",
                            "summary": "s",
                            "sources": ["src-a"],
                        }
                    ],
                }
            },
            "ordering": {},
            "states": [{"events": [], "coverage": {"kind": "none-needed"}}],
            "implementation_metadata": [{"events": [], "status": "complete"}, {"events": ["c0"], "status": "missing"}],
            "reference_identities": [],
            "review": {"status": "reviewed"},
            "sources": ["src-a"],
        }
        raw.update(overrides)
        return raw

    def test_flattens_event_and_coverage(self):
        sugar = mm._to_sugar(self._full_raw())
        self.assertEqual("ruling", sugar["event"]["kind"])
        self.assertEqual({"date": "2010-01-01"}, sugar["event"]["effective"])
        self.assertEqual({"kind": "none-needed"}, sugar["coverage"])
        self.assertNotIn("events", sugar)
        self.assertNotIn("states", sugar)
        self.assertNotIn("ordering", sugar)

    def test_rewrites_metadata_event_ids_from_c0_to_event(self):
        sugar = mm._to_sugar(self._full_raw())
        events_seen = [tuple(e["events"]) for e in sugar["implementation_metadata"]]
        self.assertIn((), events_seen)
        self.assertIn(("event",), events_seen)
        self.assertNotIn(("c0",), events_seen)

    def test_raises_on_more_than_one_event(self):
        raw = self._full_raw()
        raw["events"]["c1"] = dict(raw["events"]["c0"])
        with self.assertRaises(ValueError):
            mm._to_sugar(raw)

    def test_raises_without_an_authored_baseline_coverage(self):
        raw = self._full_raw(states=[])
        with self.assertRaises(ValueError):
            mm._to_sugar(raw)

    def test_desugars_back_to_the_same_semantics(self):
        """Round-trip proof: the sugar this function produces, parsed
        through the real `ErratumV2.load()` (which calls
        `_desugar_v2_sugar()` internally), carries the same event/coverage
        content as the full shape it was flattened from."""
        full_raw = self._full_raw()
        sugar_raw = mm._to_sugar(dict(full_raw, id="erratum-sugar-rt"))
        from pathlib import Path

        full_v2 = ErratumV2.load(dict(full_raw, id="erratum-full-rt"), Path("full.json"))
        sugar_v2 = ErratumV2.load(sugar_raw, Path("sugar.json"))
        self.assertEqual(len(full_v2.events), len(sugar_v2.events))
        (full_event,) = full_v2.events.values()
        (sugar_event,) = sugar_v2.events.values()
        self.assertEqual(full_event.effective, sugar_event.effective)
        self.assertEqual(
            full_event.transitions[0].historical_text, sugar_event.transitions[0].historical_text
        )
        self.assertEqual(full_v2.authored_states, sugar_v2.authored_states)


if __name__ == "__main__":
    unittest.main()
