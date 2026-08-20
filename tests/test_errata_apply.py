"""Unit tests for the errata decision applier's evidence guards.

The applier is the gate between a per-card review and the canonical dataset.
Its job is to make unverifiable claims impossible to record: dates are
recomputed from the research packet, shared chronology is copied from the
sourced table, texts are copied from the packet, and implementations must
match the era they claim. These tests attack each guard.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from retroformats.importers.errata_apply import DecisionError, apply_decision

PACKET = {
    "card": {"passcode": 200, "name": "Beta"},
    "corpus_record": "beta",
    "modern_text": "Modern text of Beta.",
    "upstream_implementations": [
        {
            "passcode": 510000000,
            "cdb": "goat-entries.cdb",
            "name": "Beta (GOAT)",
            "text": "Old text of Beta.",
            "script": "goat/c510000000.lua",
            "annotations": [],
            "text_matches_version": {"index": 0, "ratio": 1.0, "exact": True},
        },
        {
            "passcode": 510000001,
            "cdb": "cards-unofficial.cdb",
            "name": "Beta (Pre-Errata)",
            "text": "Middle text of Beta.",
            "script": "pre-errata/c510000001.lua",
            "annotations": [],
            "text_matches_version": {"index": 1, "ratio": 1.0, "exact": True},
        },
    ],
    "errata_page": {
        "title": "Card Errata:Beta",
        "english_versions": [
            {
                "index": 0,
                "text": "Old text of Beta.",
                "number": "AAA-EN001",
                "dating_set": "Set Alpha",
                "earliest_tcg_date": {"date": "2002-06-26", "precision": "day"},
            },
            {
                "index": 1,
                "text": "Middle text of Beta.",
                "number": "BBB-EN002",
                "dating_set": "Set Beta",
                "earliest_tcg_date": {"date": "2008-07-08", "precision": "day"},
            },
            {
                "index": 2,
                "text": "Modern text of Beta.",
                "number": "CCC-EN003",
                "dating_set": "Set Gamma",
                "earliest_tcg_date": {"date": "2016-09-15", "precision": "day"},
            },
        ],
    },
    "modern_text_matches_version": {"index": 2, "ratio": 1.0, "exact": True},
}

CHRONOLOGIES = {
    "search-verification": {
        "old_attested_through": "2011-02-02",
        "new_attested_from": "2019-04-03",
        "status": "verified",
        "basis": "period rulings documents",
        "corroboration": [
            {
                "url": "http://web.archive.org/web/20050616025109/http://example.invalid/rulings",
                "title": "period rulings capture",
                "quote": "your opponent gets to see your Deck to verify",
                "archived": True,
            }
        ],
    },
    "unbacked-claim": {
        "old_attested_through": "2011-02-02",
        "status": "verified",
        "basis": "someone was confident",
    },
}

# The default decision records one functional change from lineage version 1
# to version 2, so its baseline implementation is the variant whose database
# text IS version 1 (510000001).
BASELINE = {
    "strategy": "reuse-upstream",
    "historical_passcode": 510000001,
    "status": "complete",
    "tested": False,
}


def decision(**kw):
    base = {
        "slug": "beta",
        "passcode": 200,
        "classification": "functional",
        "changes": [
            {
                "kind": "functional",
                "effective": {},
                "date_evidence": {"kind": "set-release", "introduces_version": 2},
                "historical_text_version": 1,
                "modern_text_version": 2,
                "summary": "The modern printing added a hard once-per-turn.",
                "sources": ["ignis-babelcdb"],
            }
        ],
        "baseline_implementation": dict(BASELINE),
        "review_notes": "",
        "flags": [],
    }
    base.update(kw)
    return base


class ApplierTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="errata-apply-test-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.errata = self.root / "errata"
        self.packets = self.root / "packets"
        self.errata.mkdir()
        self.packets.mkdir()
        (self.packets / "beta.json").write_text(json.dumps(PACKET), encoding="utf-8")

    def apply(self, dec, packet=None):
        if packet is not None:
            (self.packets / "beta.json").write_text(json.dumps(packet), encoding="utf-8")
        return apply_decision(dec, self.errata, self.packets, CHRONOLOGIES, "2026-08-20")

    # -- happy path ------------------------------------------------------

    def test_set_release_evidence_populates_the_date_from_the_packet(self):
        _, record = self.apply(decision())
        effective = record["changes"][0]["effective"]
        self.assertEqual("2016-09-15", effective["date"])
        self.assertEqual("day", effective["precision"])
        self.assertIn("CCC-EN003", effective["basis"])
        # texts are copied from the lineage, not from the decision
        self.assertEqual("Middle text of Beta.", record["changes"][0]["historical_text"])
        self.assertEqual("Modern text of Beta.", record["changes"][0]["modern_text"])
        self.assertEqual("reviewed", record["review"]["status"])

    def test_shared_chronology_bounds_come_from_the_table(self):
        dec = decision(
            classification="ruling",
            baseline_implementation={
                "strategy": "reuse-upstream",
                "historical_passcode": 510000000,
                "status": "complete",
            },
            changes=[
                {
                    "kind": "ruling",
                    "effective": {},
                    "date_evidence": {"kind": "shared-chronology", "id": "search-verification"},
                    "historical_text_version": 0,
                    "summary": "period verification procedure",
                    "sources": ["ignis-cardscripts"],
                }
            ],
        )
        _, record = self.apply(dec)
        effective = record["changes"][0]["effective"]
        self.assertEqual("2011-02-02", effective["old_attested_through"])
        self.assertEqual("2019-04-03", effective["new_attested_from"])
        self.assertEqual("verified", effective["status"])
        # the table's evidence travels with the claim, so it stays checkable
        self.assertEqual(1, len(effective["corroboration"]))
        self.assertIn("see your Deck to verify", effective["corroboration"][0]["quote"])

    def test_verified_status_without_corroboration_is_rejected(self):
        dec = decision(
            classification="ruling",
            baseline_implementation={
                "strategy": "reuse-upstream",
                "historical_passcode": 510000000,
                "status": "complete",
            },
            changes=[
                {
                    "kind": "ruling",
                    "effective": {},
                    "date_evidence": {"kind": "shared-chronology", "id": "unbacked-claim"},
                    "historical_text_version": 0,
                    "summary": "confidently asserted",
                    "sources": ["ignis-cardscripts"],
                }
            ],
        )
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("records no corroboration", str(ctx.exception))

    def test_unknown_chronology_needs_no_evidence(self):
        dec = decision(
            classification="ruling",
            baseline_implementation={
                "strategy": "reuse-upstream",
                "historical_passcode": 510000000,
                "status": "complete",
            },
            changes=[
                {
                    "kind": "ruling",
                    "effective": {},
                    "historical_text_version": 0,
                    "summary": "undated era difference",
                    "sources": ["ignis-cardscripts"],
                }
            ],
        )
        _, record = self.apply(dec)
        self.assertEqual({"date": None}, record["changes"][0]["effective"])

    # -- guards ----------------------------------------------------------

    def test_a_typed_date_that_contradicts_the_packet_is_rejected(self):
        dec = decision()
        dec["changes"][0]["effective"] = {"date": "2015-01-01"}
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("packet earliest TCG date", str(ctx.exception))

    def test_a_typed_precision_that_contradicts_the_packet_is_rejected(self):
        dec = decision()
        dec["changes"][0]["effective"] = {"precision": "month"}
        with self.assertRaises(DecisionError):
            self.apply(dec)

    def test_chronology_without_evidence_is_rejected(self):
        dec = decision()
        dec["changes"][0].pop("date_evidence")
        dec["changes"][0]["effective"] = {"date": "2016-09-15"}
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("no date_evidence", str(ctx.exception))

    def test_undefined_shared_chronology_is_rejected(self):
        dec = decision()
        dec["changes"][0]["date_evidence"] = {"kind": "shared-chronology", "id": "nope"}
        with self.assertRaises(DecisionError):
            self.apply(dec)

    def test_external_evidence_needs_url_and_quote(self):
        dec = decision()
        dec["changes"][0]["date_evidence"] = {"kind": "external", "url": "https://x.invalid"}
        dec["changes"][0]["effective"] = {"date": "2016-09-15"}
        with self.assertRaises(DecisionError):
            self.apply(dec)

    def test_archive_capture_bound_must_equal_the_capture_date(self):
        dec = decision()
        dec["changes"][0]["date_evidence"] = {
            "kind": "external",
            "url": "http://web.archive.org/web/20090220140225/http://example.invalid/",
            "quote": "the card reads ...",
        }
        dec["changes"][0]["effective"] = {"new_attested_from": "2008-01-01"}
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("not attested by any cited archive capture", str(ctx.exception))
        # the capture's own date is accepted
        dec["changes"][0]["effective"] = {"new_attested_from": "2009-02-20"}
        _, record = self.apply(dec)
        self.assertEqual("2009-02-20", record["changes"][0]["effective"]["new_attested_from"])

    def test_bounds_may_be_backed_by_the_decisions_own_citations(self):
        # A reviewer who cites two archive captures and claims exactly those
        # two dates as bounds needs no separate date_evidence block.
        dec = decision(
            classification="ruling",
            baseline_implementation={
                "strategy": "reuse-upstream",
                "historical_passcode": 510000000,
                "status": "complete",
            },
            changes=[
                {
                    "kind": "ruling",
                    "effective": {
                        "old_attested_through": "2005-06-16",
                        "new_attested_from": "2008-12-15",
                        "status": "verified",
                    },
                    "historical_text_version": 0,
                    "summary": "per-card activation condition tightened",
                    "sources": ["ignis-cardscripts"],
                }
            ],
            external_citations=[
                {
                    "url": "http://web.archive.org/web/20050616025109/http://example.invalid/a",
                    "quote": "you can activate it with none in your Deck",
                    "used_for": "old_attested_through",
                },
                {
                    "url": "http://web.archive.org/web/20081215065604/http://example.invalid/b",
                    "quote": "you cannot activate it without one",
                    "used_for": "new_attested_from",
                },
            ],
        )
        _, record = self.apply(dec)
        effective = record["changes"][0]["effective"]
        self.assertEqual("2005-06-16", effective["old_attested_through"])
        self.assertEqual("2008-12-15", effective["new_attested_from"])

    def test_a_bound_with_no_attesting_capture_is_still_rejected(self):
        dec = decision(
            classification="ruling",
            baseline_implementation={
                "strategy": "reuse-upstream",
                "historical_passcode": 510000000,
                "status": "complete",
            },
            changes=[
                {
                    "kind": "ruling",
                    "effective": {
                        "old_attested_through": "2005-06-16",
                        "new_attested_from": "2007-01-01",  # nothing attests this
                        "status": "verified",
                    },
                    "historical_text_version": 0,
                    "summary": "invented tightening",
                    "sources": ["ignis-cardscripts"],
                }
            ],
            external_citations=[
                {
                    "url": "http://web.archive.org/web/20050616025109/http://example.invalid/a",
                    "quote": "you can activate it with none in your Deck",
                    "used_for": "old_attested_through",
                }
            ],
        )
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("not each attested by a cited archive capture", str(ctx.exception))

    def test_hand_transcribed_text_is_rejected(self):
        dec = decision()
        dec["changes"][0].pop("historical_text_version")
        dec["changes"][0]["historical_text"] = "Something I typed from memory."
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("does not match any packet-carried cdb text", str(ctx.exception))

    def test_literal_text_matching_the_packet_is_accepted(self):
        dec = decision()
        dec["changes"][0].pop("historical_text_version")
        dec["changes"][0]["historical_text"] = "Old text of Beta."
        _, record = self.apply(dec)
        self.assertEqual("Old text of Beta.", record["changes"][0]["historical_text"])

    def test_reuse_upstream_passcode_must_exist_in_the_packet(self):
        dec = decision(
            baseline_implementation={
                "strategy": "reuse-upstream",
                "historical_passcode": 999999999,
                "status": "complete",
            }
        )
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("no such upstream implementation", str(ctx.exception))

    def test_upstream_variant_from_the_wrong_era_is_rejected(self):
        # The change says version 1 was in force before it, but the baseline
        # passes the variant whose database text is version 0.
        dec = decision()
        dec["baseline_implementation"]["historical_passcode"] = 510000000  # text is v0
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("different era", str(ctx.exception))

    def test_era_mismatch_can_be_acknowledged_deliberately(self):
        dec = decision(era_mismatch_ack="upstream ships one variant for both revisions")
        dec["baseline_implementation"]["historical_passcode"] = 510000000
        _, record = self.apply(dec)
        self.assertEqual(510000000, record["implementation"]["historical_passcode"])

    def test_intermediate_version_implementation_is_era_checked_too(self):
        # Two behavioural changes: baseline implements v0, the version the
        # first change creates implements v1. Swapping them must be caught.
        dec = decision(
            baseline_implementation={
                "strategy": "reuse-upstream",
                "historical_passcode": 510000001,  # text is v1, but claims v0
                "status": "complete",
            },
            changes=[
                {
                    "kind": "ruling",
                    "effective": {},
                    "historical_text_version": 0,
                    "resulting_implementation": {
                        "strategy": "reuse-upstream",
                        "historical_passcode": 510000000,
                        "status": "complete",
                    },
                    "summary": "era procedure ended",
                    "sources": ["ignis-cardscripts"],
                },
                {
                    "kind": "functional",
                    "effective": {},
                    "historical_text_version": 1,
                    "summary": "the modern erratum",
                    "sources": ["ignis-babelcdb"],
                },
            ],
        )
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("different era", str(ctx.exception))

    def test_classification_must_equal_the_dominant_change_kind(self):
        dec = decision(classification="cosmetic")
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("dominant change kind", str(ctx.exception))

    def test_resulting_implementation_only_on_behavioural_changes(self):
        dec = decision(
            classification="functional",
            changes=[
                {
                    "kind": "cosmetic",
                    "effective": {},
                    "resulting_implementation": dict(BASELINE),
                    "summary": "rewording",
                    "sources": ["yugipedia-card-errata"],
                },
                {
                    "kind": "functional",
                    "effective": {},
                    "summary": "real change",
                    "sources": ["ignis-babelcdb"],
                },
            ],
        )
        with self.assertRaises(DecisionError) as ctx:
            self.apply(dec)
        self.assertIn("only functional/ruling", str(ctx.exception))

    def test_passcode_must_match_the_packet(self):
        with self.assertRaises(DecisionError):
            self.apply(decision(passcode=999))

    def test_missing_packet_is_rejected(self):
        with self.assertRaises(DecisionError):
            self.apply(decision(slug="nonexistent"))

    def test_lineage_version_that_does_not_exist_is_rejected(self):
        dec = decision()
        dec["changes"][0]["date_evidence"] = {"kind": "set-release", "introduces_version": 9}
        with self.assertRaises(DecisionError):
            self.apply(dec)

    def test_set_release_needs_a_dated_printing(self):
        packet = json.loads(json.dumps(PACKET))
        del packet["errata_page"]["english_versions"][2]["earliest_tcg_date"]
        with self.assertRaises(DecisionError) as ctx:
            self.apply(decision(), packet=packet)
        self.assertIn("no dated set", str(ctx.exception))

    # -- determinism -----------------------------------------------------

    def test_output_is_deterministic_and_key_ordered(self):
        _, a = self.apply(decision())
        _, b = self.apply(decision())
        self.assertEqual(json.dumps(a), json.dumps(b))
        self.assertEqual(
            ["$schema", "id", "modern_card", "classification", "changes",
             "implementation", "review", "sources"],
            [k for k in a if k in {
                "$schema", "id", "modern_card", "classification", "changes",
                "implementation", "review", "sources"}],
        )


if __name__ == "__main__":
    unittest.main()
