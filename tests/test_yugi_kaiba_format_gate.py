"""Research-only gate for the proposed early OCG Tokyo Dome snapshot.

The packet has exactly ONE current-authoritative Tokyo Dome research
section: ``tokyo_dome_research_current``. Anything under the top-level
``superseded_findings`` key is archived/rejected history and must never be
read as current - tests in this module enforce that boundary explicitly,
not just check that prose fields exist.
"""

from __future__ import annotations

import json
import hashlib
import copy
import re
import unittest
from datetime import date
from pathlib import Path

from retroformats.model import Coverage, ErratumV2, Pool
from retroformats.lflist import build_lflist
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "research" / "yugi-kaiba-format-source-packet.json"

# Substrings that must never appear inside a DATA field (not narrative prose)
# of the current-authoritative section - these are exactly the wrong claims
# the rejected 2026-08 pass made, and their presence in a data field (as
# opposed to a "this was corrected" sentence) would mean a ghost of a
# conclusion we already know is wrong has leaked back into active use.
BANNED_AS_CURRENT_VALUE = ("probable 2000", "genuinely disputed between agents")


# Phrases from now-corrected/superseded framings that must never appear as
# ACTIVE terminology anywhere under tokyo_dome_research_current. Quoting an
# old phrase for correction purposes is fine (see EXEMPT_PATH_MARKERS below),
# asserting it as live status text is not.
LEGACY_BANNED_PHRASES = (
    "bounded-to-proven",
    "moderately, not fully, resolved",
    "moderately resolved, not fully settled",
)

# A path is exempt from the legacy-phrase ban if any segment (case-
# insensitive) matches one of these markers - these are exactly the kind of
# "explicitly archival/audit field" the task calls out (prior_claim,
# supersedes, correction-history fields).
EXEMPT_PATH_MARKERS = ("supersedes", "prior_claim", "correction", "adversarial_audit")

# Semantic (value-content) May-5-proof-contamination check: a SENTENCE is a
# violation if it mentions the exact Expert Rules date AND a proof/certainty
# word, UNLESS that SAME SENTENCE also carries a negation/hedge cue ("not",
# "NOT", "do not read ... as", etc.) - i.e. it reads as a positive assertion
# rather than a correction/rejection. This catches contamination inside
# ORDINARY PROSE VALUES, not just fields whose PATH happens to be named
# "confirmed"/"proven" - the exact blind spot that let the Tribute-Summon
# bug survive the previous pass's test_B.
#
# Checking is SENTENCE-scoped, not whole-string: a long field can
# legitimately contain several sentences, only one of which discusses the
# May-5 date, while an UNRELATED sentence elsewhere in the same field
# happens to contain the word "not" (e.g. "not an under-sourced guess").  A
# whole-string "does 'not' appear anywhere" check would let that unrelated
# "not" mask a genuinely unhedged claim in a different sentence - verified
# during this task's own adversarial self-check, where a whole-string
# version of this function failed to catch Mutation A.
#
# The exemption is intentionally NARROW: only `prior_claim` (the literal
# "here is what was wrongly claimed" quote field) is exempt. Unlike the
# legacy-phrase check (test_A), `correction` fields are NOT blanket-exempt
# here - a correction's own prose is ACTIVE, CURRENT text and must not
# itself read as an unhedged positive assertion; it needs to pass the same
# sentence-level check as any other field. `supersedes` as a whole is not a
# safe blanket marker either, since it contains both prior_claim (safe to
# exempt) and correction (must be checked normally).
MAY_5_DATE_PATTERN = re.compile(r"1999-05-05|may\s+5,?\s*1999", re.I)
PROOF_WORD_PATTERN = re.compile(r"\bproven\b|\bconfirmed\b|\bdefinitely\b", re.I)
NEGATION_TOKEN_PATTERN = re.compile(r"\bnot\b", re.I)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
MAY_5_CHECK_EXEMPT_PATH_MARKERS = ("prior_claim",)


def _is_may_5_proof_violation(path, value):
    """True if `value` positively asserts May 5 as a proven/confirmed date
    in some sentence, outside the literal prior_claim quote field."""
    path_str = "/".join(path).lower()
    if any(marker in path_str for marker in MAY_5_CHECK_EXEMPT_PATH_MARKERS):
        return False
    for sentence in SENTENCE_SPLIT_PATTERN.split(value):
        if (
            MAY_5_DATE_PATTERN.search(sentence)
            and PROOF_WORD_PATTERN.search(sentence)
            and not NEGATION_TOKEN_PATTERN.search(sentence)
        ):
            return True
    return False


def _walk_strings(value, path=()):
    """Yield (path_tuple, string_value) for every string leaf in a JSON tree."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk_strings(v, path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk_strings(v, path + (str(i),))
    elif isinstance(value, str):
        yield path, value


def _make_pool():
    raw_pool = {
        "id": "pool-ocg1999-research-only", "region": "OCG", "kind": "release-cutoff",
        "cutoff": {"cutoff_date": "1999-08-25", "territories": ["ocg-jp"]},
        "sources": ["yugipedia-ocg-series1-set-pages"],
    }
    return Pool.load(raw_pool, ROOT / "research-only-pool.json")


class YugiKaibaResearchGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        cls.repo = Repository.load(ROOT)

    # ------------------------------------------------------------------
    # Original (pre-2026-08) hardening-gate fields - unaffected by this
    # session's archival reorg, still describe current truth, re-checked.
    # ------------------------------------------------------------------

    def test_packet_is_research_only_and_rejects_requested_label(self):
        self.assertEqual("research-gate-only", self.packet["status"])
        self.assertEqual("blocked", self.packet["canonicalization"])
        self.assertEqual("rejected", self.packet["target_recommendation"]["requested_label_verdict"])
        self.assertFalse(self.packet["scope"]["canonical_format_created"])

    def test_recommendation_is_the_pre_event_ocg_japan_snapshot(self):
        target = self.packet["target_recommendation"]
        self.assertEqual("1999-08-tokyo-dome", target["id"])
        self.assertEqual("OCG", target["region"])
        self.assertEqual("1999-08-25", target["snapshot"])
        self.assertEqual("1999-08-26", target["event"]["date"])
        self.assertIsNone(target["previous"])
        self.assertEqual("OCG", self.packet["card_pool"]["format_region"])
        self.assertEqual(["ocg-jp"], self.packet["card_pool"]["territories"])

    def test_region_and_territory_use_the_shared_schema_semantics(self):
        common = json.loads((ROOT / "schemas" / "common.schema.json").read_text(encoding="utf-8"))
        fmt = json.loads((ROOT / "schemas" / "format.schema.json").read_text(encoding="utf-8"))
        pool = json.loads((ROOT / "schemas" / "pool.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "common.schema.json#/$defs/region",
            fmt["properties"]["region"]["$ref"],
        )
        self.assertIn("OCG", common["$defs"]["region"]["enum"])
        self.assertNotIn("ocg-jp", common["$defs"]["region"]["enum"])
        self.assertIn("ocg-jp", common["$defs"]["territory"]["enum"])
        self.assertEqual(
            "common.schema.json#/$defs/territory",
            pool["properties"]["cutoff"]["properties"]["territories"]["items"]["$ref"],
        )

    def test_source_references_are_unique_and_resolvable(self):
        sources = self.packet["sources"]
        ids = [source["id"] for source in sources]
        self.assertEqual(len(ids), len(set(ids)))
        known = set(ids)

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "source_ids":
                        for source_id in child:
                            self.assertIn(source_id, known)
                    elif key == "source_id":
                        self.assertIn(child, known)
                    else:
                        walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(self.packet)
        for source in sources:
            self.assertTrue(source["url"].startswith(("http://", "https://")))

    def test_product_chronology_has_event_day_after_cutoff(self):
        entries = self.packet["product_chronology"]
        dates = [date.fromisoformat(entry["date"]) for entry in entries]
        self.assertEqual(dates, sorted(dates))
        self.assertLess(date.fromisoformat("1999-08-25"), dates[-1])
        self.assertIn("Tokyo Dome event and attendee/prize cards", entries[-1]["products"])

    def test_rules_and_architecture_keep_gaps_explicit(self):
        rules = self.packet["rules"]
        topics = {fact["topic"] for fact in rules["facts"]}
        self.assertIn("deck_out", topics)
        self.assertIn("battle_damage", topics)
        self.assertIn("chain_and_spell_speed", topics)
        self.assertIn("higher-LP-wins-deck-out", rules["candidate_core_flags"]["known_gaps"])
        # Regression: the old top-level "architecture" field (bare verdict "B")
        # no longer exists - it was renamed and explicitly scoped to
        # schema/host representability only, so it can never be mistaken for
        # a competing Tokyo Dome canonicalization verdict.
        self.assertNotIn("architecture", self.packet)
        architecture = self.packet["schema_host_architecture_assessment"]
        self.assertNotEqual("B", architecture["verdict"])
        self.assertIn("schema/host", architecture["verdict"].lower())
        self.assertIn("BLOCKED_BY_BOTH", architecture["_scope"])
        self.assertFalse(architecture["schema_change_required"])
        self.assertTrue(architecture["schema_enhancement_desirable"])
        self.assertFalse(architecture["runtime_change_required"])
        self.assertTrue(architecture["format_local_approximation_required"])
        self.assertEqual([40, None], architecture["historical_unbounded_deck_limits"]["main"])
        self.assertEqual([0, None], architecture["historical_unbounded_deck_limits"]["extra"])
        self.assertEqual([10, 10], architecture["historical_unbounded_deck_limits"]["side"])
        self.assertEqual([40, 999], architecture["host_representation"]["main"])
        self.assertTrue(architecture["host_representation"]["999_is_client_ceiling_not_historical_unbounded"])
        self.assertTrue(architecture["init_lua_feasibility"]["sanctioned_hook"])
        self.assertFalse(architecture["init_lua_feasibility"]["can_exactly_intercept_deckout"])

        flags = rules["candidate_core_flags"]
        self.assertIn("DUEL_NO_HAND_LIMIT", flags["accepted_for_rule_profile_research"])
        self.assertIn("DUEL_1_FACEUP_FIELD", flags["accepted_for_rule_profile_research"])
        self.assertNotIn("DUEL_NO_MAIN_PHASE_2", flags["accepted_for_rule_profile_research"])
        self.assertIn("DUEL_NO_MAIN_PHASE_2", flags["rejected"])
        self.assertIn("DUEL_OCG_OBSOLETE_IGNITION", flags["rejected"])
        self.assertEqual("wrong", next(row["classification"] for row in rules["core_flag_audit"] if row["flag"] == "DUEL_NO_MAIN_PHASE_2"))
        self.assertEqual("phase-engine-experiment", self.packet["phase_experiment"]["source_id"])
        self.assertEqual("mechanically-closer", self.packet["phase_experiment"]["configurations"][0]["classification"])
        self.assertEqual("historically-wrong", self.packet["phase_experiment"]["configurations"][1]["classification"])

    def test_frozen_errata_are_all_v2_and_accounted_at_snapshot(self):
        errata = list(self.repo.errata.values())
        self.assertEqual(296, len(errata))
        self.assertTrue(all(isinstance(record, ErratumV2) for record in errata))

        snapshot = date(1999, 8, 25)
        determinate = []
        ambiguous = []
        for record in errata:
            selection = record.selection_at(snapshot)
            (determinate if selection.chronology == "determinate" else ambiguous).append(selection)

        audit = self.packet["errata_audit"]
        self.assertEqual(296, audit["total"])
        self.assertEqual(146, len(determinate))
        self.assertEqual(150, len(ambiguous))
        self.assertEqual(146, audit["chronology"]["determinate"])
        self.assertEqual(150, audit["chronology"]["ambiguous"])

        determinate_modern = sum(selection.is_modern for selection in determinate)
        determinate_historical = len(determinate) - determinate_modern
        self.assertEqual(21, determinate_modern)
        self.assertEqual(125, determinate_historical)
        self.assertEqual(21, audit["determinate"]["modern"])
        self.assertEqual(125, audit["determinate"]["historical"])

        determinate_coverage = {}
        for selection in determinate:
            if selection.is_modern:
                continue
            kind = selection.candidates[0].coverage.kind.value
            determinate_coverage[kind] = determinate_coverage.get(kind, 0) + 1
        self.assertEqual({"reuse-upstream": 79, "known-gap": 42, "none-needed": 4}, determinate_coverage)
        self.assertEqual(determinate_coverage, audit["determinate"]["coverage"])
        self.assertEqual(set(), set(determinate_coverage) - {"reuse-upstream", "known-gap", "none-needed"})

        self.assertEqual(104, sum(selection.modern_is_possible for selection in ambiguous))
        self.assertEqual(46, sum(not selection.modern_is_possible for selection in ambiguous))
        self.assertEqual(104, audit["ambiguous"]["modern_possible"])
        self.assertEqual(46, audit["ambiguous"]["modern_impossible"])

        coverage_occurrences = {}
        candidate_occurrences = 0
        for selection in ambiguous:
            candidate_occurrences += len(selection.candidates)
            for candidate in selection.candidates:
                kind = candidate.coverage.kind.value
                coverage_occurrences[kind] = coverage_occurrences.get(kind, 0) + 1
        self.assertEqual(302, candidate_occurrences)
        self.assertEqual(302, audit["ambiguous"]["candidate_occurrences"])
        self.assertEqual(
            {"reuse-upstream": 144, "unresolved": 47, "known-gap": 7, "modern": 104},
            coverage_occurrences,
        )
        self.assertEqual(coverage_occurrences, audit["ambiguous"]["candidate_coverage_occurrences"])

        modern_impossible_ids = sorted(
            record.id for record in errata
            if (selection := record.selection_at(snapshot)).chronology == "ambiguous"
            and not selection.modern_is_possible
        )
        unresolved_record_ids = sorted(
            record.id for record in errata
            if (selection := record.selection_at(snapshot)).chronology == "ambiguous"
            and any(candidate.coverage.kind is Coverage.UNRESOLVED for candidate in selection.candidates)
        )
        self.assertEqual(46, len(modern_impossible_ids))
        self.assertEqual(47, len(unresolved_record_ids))
        self.assertEqual(modern_impossible_ids, audit["ambiguous_modern_impossible_ids"])
        self.assertEqual(unresolved_record_ids, audit["ambiguous_unresolved_record_ids"])

        substitutions = []
        for record in errata:
            selection = record.selection_at(snapshot)
            if selection.chronology != "determinate" or selection.is_modern:
                continue
            if selection.candidates[0].coverage.kind is not Coverage.REUSE_UPSTREAM:
                continue
            substitutions.append({
                "erratum_id": record.id,
                "modern_passcode": record.modern_card.passcode,
                "selected_events": sorted(selection.candidates[0].events),
                "selected_historical_passcode": selection.candidates[0].coverage.historical_passcode,
                "coverage_kind": selection.candidates[0].coverage.kind.value,
            })
        substitutions.sort(key=lambda row: row["erratum_id"])
        digest_input = json.dumps(substitutions, separators=(",", ":"), sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(digest_input).hexdigest()
        self.assertEqual(79, len(substitutions))
        self.assertEqual(substitutions, audit["determinate_historical_substitutions"])
        self.assertEqual(digest, audit["determinate_historical_substitutions_digest"])
        self.assertEqual("b45a38f83be490899d2fd64198b70ea86170ea55f1c24ef3c50194d0546ceaa2", digest)

    def test_repository_has_the_certified_ocg_ledger_but_no_early_canonical_artifacts(self):
        # Regression 14/15: no canonical Tokyo Dome artifacts exist; existing
        # canonical formats and generated outputs remain unchanged.
        ocg_products = {
            product.id for product in self.repo.products.values()
            if any(event.territory.startswith("ocg") for event in product.events)
        }
        self.assertEqual(19, len(ocg_products))
        self.assertTrue(all(product_id in self.repo.products for product_id in ocg_products))
        self.assertEqual({"2005-04-goat", "2010-03-edison", "2011-09-tengu"}, set(self.repo.formats))
        self.assertEqual(0x28E9FC02, build_lflist(self.repo.formats["2005-04-goat"], self.repo).hash)
        self.assertEqual(3673, len(self.repo.pools[self.repo.formats["2010-03-edison"].pool_id].cards))
        self.assertEqual(4562, len(self.repo.pools[self.repo.formats["2011-09-tengu"].pool_id].cards))
        self.assertEqual(0x0CE5BABE, build_lflist(self.repo.formats["2011-09-tengu"], self.repo).hash)
        self.assertFalse((ROOT / "formats" / "1999-08-tokyo-dome").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "ocg-1999-07.json").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "1999-08-tokyo-dome.json").exists())
        self.assertFalse((ROOT / "data" / "pools" / "1999-08-tokyo-dome.json").exists())
        self.assertFalse((ROOT / "data" / "rule-profiles" / "1999-08-tokyo-dome.json").exists())
        self.assertEqual(296, len(self.repo.errata))
        self.assertTrue(all(isinstance(record, ErratumV2) for record in self.repo.errata.values()))

    def test_coverage_gate_does_not_promote_modern_fallback_to_certification(self):
        audit = self.packet["errata_audit"]
        policy = audit["modern_policy_effect"]
        self.assertTrue(policy["explicit_policy_required"])
        self.assertEqual(150, policy["ambiguous_records_left_unresolved"])
        self.assertFalse(policy["certifiable"])
        self.assertEqual(Coverage.UNRESOLVED.value, "unresolved")

    def test_blocker_ledger_is_complete_and_uses_frozen_statuses(self):
        required = {
            "format_name_date_convention", "event_card_pool_cutoff", "ocg_release_ledger",
            "missing_card_identities", "banlist", "starter_vs_expert_effective_boundary",
            "main_battle_main_behaviour", "first_turn_draw", "first_turn_attack", "hand_limit",
            "deck_size_representation", "side_fusion_deck_constraints", "deck_out_rule",
            "battle_calculation_semantics", "chain_spell_speed_semantics", "errata_chronology",
            "errata_implementation_coverage", "engine_representability", "schema_representability",
        }
        ledger = self.packet["blocker_ledger"]
        self.assertEqual(required, set(ledger))
        allowed = {"RESOLVED", "RESOLVED WITH APPROXIMATION", "UNRESOLVED", "BLOCKING", "NONBLOCKING"}
        self.assertTrue(all(entry["status"] in allowed for entry in ledger.values()))
        self.assertTrue(all(entry["reason"] for entry in ledger.values()))

    def test_top_level_banlist_field_no_longer_asserts_the_stale_working_id(self):
        # The top-level `banlist` field previously asserted working_id
        # "ocg-1999-07" as if it were current - that date is now known
        # wrong. It must point to the current-authoritative section instead
        # of asserting a specific dated/scoped identifier itself.
        banlist = self.packet["banlist"]
        self.assertNotEqual("ocg-1999-07", banlist["working_id"])
        self.assertIn("tokyo_dome_research_current", banlist["conflict"])

    def test_gate_scope_declares_no_shared_data_or_runtime_mutation(self):
        scope = self.packet["scope"]
        self.assertEqual(
            {
                "docs/research/yugi-kaiba-format-source-gate.md",
                "docs/research/yugi-kaiba-format-source-packet.json",
                "tests/test_yugi_kaiba_format_gate.py",
                "tests/engine/test_tokyo_dome_rules.py",
            },
            set(scope["files_added_by_gate"]),
        )
        self.assertFalse(scope["runtime_or_schema_changed"])
        self.assertFalse(scope["errata_changed"])
        self.assertFalse(any(path.startswith(("formats/", "data/", "schemas/", "retroformats/", "dist/")) for path in scope["files_added_by_gate"]))

    # ------------------------------------------------------------------
    # Single-authoritative-state invariant (hardening pass, this session)
    # ------------------------------------------------------------------

    def test_exactly_one_authoritative_current_tokyo_dome_research_state(self):
        # Regression 1: there is exactly one authoritative/current Tokyo
        # Dome research state, and its authority is self-describing.
        self.assertNotIn("tokyo_dome_rules_and_restriction_research_2026_08", self.packet)
        self.assertNotIn("tokyo_dome_rules_corrective_gate_2026_08", self.packet)
        self.assertIn("tokyo_dome_research_current", self.packet)
        current = self.packet["tokyo_dome_research_current"]
        self.assertEqual("current-authoritative", current["status"])

        self.assertIn("superseded_findings", self.packet)
        archive = self.packet["superseded_findings"]
        self.assertIn("rejected_2026_08_rules_and_restriction_research", archive)
        self.assertIn("_why_rejected", archive["rejected_2026_08_rules_and_restriction_research"])

    def test_superseded_claims_cannot_appear_in_active_current_fields(self):
        # Regressions 2, 12, 13: the specific wrong claims from the rejected
        # pass must not appear as asserted DATA VALUES in the current
        # section - they may appear only inside clearly-labeled
        # correction/audit-trail prose (fields whose own key names signal
        # that context), and they MUST still be present in the archive
        # (proving nothing was silently deleted, only relabeled).
        current = self.packet["tokyo_dome_research_current"]
        archive = self.packet["superseded_findings"]["rejected_2026_08_rules_and_restriction_research"]

        # The archive still honestly contains the rejected claims - nothing
        # was deleted, only relabeled as non-authoritative.
        archive_text = json.dumps(archive, ensure_ascii=False).lower()
        self.assertIn("probable 2000", archive_text)
        self.assertIn("genuinely disputed between agents", archive_text)

        # The evidence matrix's actual DATA fields (not narrative/correction
        # prose fields) must never assert the wrong values.
        matrix = {row["rule_area"]: row for row in current["evidence_matrix"]}
        self.assertNotIn("2000", matrix["starting_lp"]["starter_box_state"])
        self.assertEqual("PROVEN", matrix["first_turn_attack"]["starter_box_evidence_status"])
        self.assertNotIn("AMBIGUOUS", matrix["first_turn_attack"]["starter_box_evidence_status"])
        self.assertNotEqual("EXACT", matrix["deck_out"]["engine_representation"])

        # Narrative correction fields (supersedes.corrected_claims,
        # starter_box_baseline) are explicitly ALLOWED to quote the old wrong
        # phrase, but only paired with a correction in the same entry/field -
        # verify that pairing rather than banning the phrase outright.
        for claim in current["supersedes"]["corrected_claims"]:
            if "probable 2000" in claim["prior_claim"].lower() or "2000 lp" in claim["prior_claim"].lower():
                self.assertIn("correction", claim)
                self.assertTrue(claim["correction"])
            if "disputed between agents" in claim["prior_claim"].lower():
                self.assertIn("correction", claim)
                self.assertTrue(claim["correction"])

    # ------------------------------------------------------------------
    # Evidence matrix - three tiers, never collapsed
    # ------------------------------------------------------------------

    def test_evidence_matrix_keeps_three_tiers_separate(self):
        # Regression: three-tier structure, now with later_1999_evidence_status
        # as a real structured field (added this session).
        current = self.packet["tokyo_dome_research_current"]
        matrix = current["evidence_matrix"]
        self.assertEqual(15, len(matrix))
        required_columns = {
            "rule_area", "starter_box_state", "starter_box_evidence_status", "starter_box_source_ids",
            "later_1999_state", "later_1999_evidence_status", "later_1999_effective_bounds", "later_1999_source_ids",
            "tokyo_dome_state", "tokyo_dome_evidence_status", "tokyo_dome_source_ids",
            "engine_representation", "engine_notes", "remaining_uncertainty",
        }
        allowed_tier_status = {"PROVEN", "BOUNDED", "AMBIGUOUS", "UNKNOWN"}
        allowed_later_1999_status = allowed_tier_status | {"STRONG_SECONDARY_RECONSTRUCTION"}
        for row in matrix:
            self.assertEqual(required_columns, set(row))
            self.assertIn(row["starter_box_evidence_status"], allowed_tier_status)
            self.assertIn(row["later_1999_evidence_status"], allowed_later_1999_status)
            self.assertIn(row["tokyo_dome_evidence_status"], allowed_tier_status)

        rule_areas = {row["rule_area"] for row in matrix}
        for expected in (
            "starting_lp", "starting_hand", "first_turn_draw", "first_turn_attack", "deck_out",
            "main_battle_main_sequence", "normal_summon_set", "tribute_summon", "fusion",
            "hand_limit", "deck_size", "side_deck", "win_condition", "spell_trap_response",
            "battle_damage_procedure",
        ):
            self.assertIn(expected, rule_areas)

    def test_starting_lp_starter_box_state_is_8000(self):
        # Regression 3.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["evidence_matrix"]}
        starting_lp = matrix["starting_lp"]
        self.assertEqual("PROVEN", starting_lp["starter_box_evidence_status"])
        self.assertIn("8000", starting_lp["starter_box_state"])
        self.assertNotIn("2000", starting_lp["starter_box_state"])
        baseline = current["starter_box_baseline"]["resolved"]["starting_lp"]
        self.assertTrue(baseline.startswith("8000"))

    def test_first_turn_attack_starter_box_state_is_prohibited_and_proven(self):
        # Regression 4.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["evidence_matrix"]}
        first_turn_attack = matrix["first_turn_attack"]
        self.assertEqual("PROVEN", first_turn_attack["starter_box_evidence_status"])
        self.assertIn("cannot attack", first_turn_attack["starter_box_state"].lower())
        self.assertTrue(len(first_turn_attack["starter_box_source_ids"]) > 0)
        self.assertEqual("UNKNOWN", first_turn_attack["tokyo_dome_evidence_status"])
        self.assertNotEqual("PROVEN", first_turn_attack["tokyo_dome_evidence_status"])

    def test_deck_out_representation_is_not_exact_modern_behaviour(self):
        # Regression 5.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["evidence_matrix"]}
        deck_out = matrix["deck_out"]
        self.assertEqual("NOT_REPRESENTABLE", deck_out["engine_representation"])
        self.assertNotEqual("EXACT", deck_out["engine_representation"])
        self.assertIn("lp", deck_out["starter_box_state"].lower())
        self.assertEqual("PROVEN", deck_out["starter_box_evidence_status"])

    def test_main_battle_main_rejects_duel_no_main_phase_2(self):
        # Regression 6.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["evidence_matrix"]}
        main_phase = matrix["main_battle_main_sequence"]
        self.assertEqual("PROVEN", main_phase["starter_box_evidence_status"])
        self.assertIn("remains the main phase", main_phase["starter_box_state"].lower())
        self.assertEqual("DEFAULT_OMISSION", main_phase["engine_representation"])
        self.assertIn("DUEL_NO_MAIN_PHASE_2", main_phase["engine_notes"])
        self.assertIn("variant-format flag", main_phase["engine_notes"].lower())

    def test_starter_box_hand_limit_and_tribute_are_not_falsely_proven(self):
        # Regression 7.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["evidence_matrix"]}
        for area in ("hand_limit", "tribute_summon"):
            row = matrix[area]
            self.assertNotEqual("PROVEN", row["starter_box_evidence_status"])
            self.assertEqual("UNKNOWN", row["starter_box_evidence_status"])

    def test_may_5_expert_rules_boundary_is_not_proven(self):
        # Regression 8: exact May 5 boundary is STRONG_SECONDARY_RECONSTRUCTION,
        # not PROVEN, unless the packet contains newly obtained primary/period
        # evidence supporting PROVEN - it does not, so it must not be PROVEN.
        # Checked at both the structured status field AND the prose fields
        # (later_1999_state, later_1999_effective_bounds) that sit right next
        # to it - a status field alone doesn't stop a reader who only reads
        # the prose from meeting an unhedged "introduced ... 1999-05-05"
        # sentence, so the prose itself must not read as a hard boundary.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["evidence_matrix"]}
        for area in ("tribute_summon", "fusion", "spell_trap_response"):
            row = matrix[area]
            self.assertEqual("STRONG_SECONDARY_RECONSTRUCTION", row["later_1999_evidence_status"])
            self.assertNotEqual("PROVEN", row["later_1999_evidence_status"])
            for field in ("later_1999_state", "later_1999_effective_bounds"):
                value = row[field]
                if "1999-05-05" in value:
                    self.assertFalse(
                        _is_may_5_proof_violation(("evidence_matrix", area, field), value),
                        f"{area}.{field} reads as an unhedged May-5 boundary: {value!r}",
                    )
        self.assertIn("STRONG_SECONDARY_RECONSTRUCTION", current["change_boundary_before_tokyo_dome"]["answer"])

    def test_no_row_claims_tokyo_dome_proven_without_its_own_source(self):
        current = self.packet["tokyo_dome_research_current"]
        matrix = current["evidence_matrix"]
        for row in matrix:
            if row["tokyo_dome_evidence_status"] == "PROVEN":
                self.assertTrue(len(row["tokyo_dome_source_ids"]) > 0)
                self.assertNotEqual(set(row["tokyo_dome_source_ids"]), set(row["starter_box_source_ids"]))
        proven_at_tokyo_dome = [row["rule_area"] for row in matrix if row["tokyo_dome_evidence_status"] == "PROVEN"]
        self.assertEqual([], proven_at_tokyo_dome)

    def test_supersedes_five_specific_prior_claims(self):
        current = self.packet["tokyo_dome_research_current"]
        corrected = current["supersedes"]["corrected_claims"]
        self.assertEqual(5, len(corrected))
        joined = " ".join(c["prior_claim"] for c in corrected)
        for marker in ("first-turn attack", "Deck-out", "2000 LP", "Main Phase", "Hand size limit"):
            self.assertIn(marker, joined)

    # ------------------------------------------------------------------
    # Restriction list - research confidence vs. canonicalization readiness
    # ------------------------------------------------------------------

    def test_restriction_list_confidence_and_canonicalization_are_separate_fields(self):
        # Regression 9.
        current = self.packet["tokyo_dome_research_current"]
        restriction = current["restriction_list_current"]
        self.assertIn("research_confidence", restriction)
        self.assertIn("canonicalization_status", restriction)
        self.assertIsInstance(restriction["research_confidence"], dict)
        self.assertIsInstance(restriction["canonicalization_status"], dict)
        # These must be genuinely distinct concepts, not the same string twice.
        self.assertNotEqual(
            restriction["research_confidence"].get("confidence_level"),
            restriction["canonicalization_status"].get("status"),
        )
        self.assertEqual(3, len(restriction["content"]["cards"]))

    def test_restriction_list_canonicalization_remains_blocked(self):
        # Regression 10.
        current = self.packet["tokyo_dome_research_current"]
        restriction = current["restriction_list_current"]
        self.assertEqual("BLOCKING", restriction["canonicalization_status"]["status"])
        self.assertIn("what_would_unblock_this", restriction["canonicalization_status"])
        self.assertFalse((ROOT / "data" / "banlists" / "ocg-1999-07.json").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "1999-08-tokyo-dome.json").exists())

    def test_master_guide_p84_was_actually_inspected_not_merely_cited(self):
        current = self.packet["tokyo_dome_research_current"]
        verification = current["restriction_list_current"]["master_guide_p84_verification"]
        self.assertTrue(verification["attempted"])
        self.assertTrue(verification["actually_inspected"])
        self.assertIn("1592318", str(verification["file_provenance"]["file_size_bytes"]))
        self.assertEqual("2106x2981", verification["file_provenance"]["pixel_dimensions"])
        self.assertIn("大会限定", verification["what_is_actually_visible"])
        self.assertIn("what_this_does_not_establish", verification)
        # Personally inspecting a 2004 retrospective must not be conflated
        # with inspecting a contemporaneous 1999 primary document.
        self.assertIn("2004", verification["what_this_does_not_establish"])

    def test_yugipedia_revision_provenance_has_exact_identifiers(self):
        # Regression 11.
        current = self.packet["tokyo_dome_research_current"]
        prov = current["restriction_list_current"]["yugipedia_revision_provenance"]
        self.assertGreaterEqual(len(prov["revisions"]), 5)
        for rev in prov["revisions"]:
            self.assertIsInstance(rev["revid"], int)
            self.assertTrue(rev["timestamp"])
            self.assertTrue(rev["user"])
        revids = {rev["revid"] for rev in prov["revisions"]}
        self.assertIn(3443496, revids)  # page creation
        self.assertIn(5830434, revids)  # final move+rewrite
        self.assertEqual("July 1999 Forbidden and Limited Lists", prov["page_title_before_move"])
        self.assertEqual("August 1999 Lists", prov["page_title_after_move"])

    def test_event_disruption_terminology_is_tiered_not_overclaimed(self):
        current = self.packet["tokyo_dome_research_current"]
        ed = current["event_disruption_reassessment"]
        self.assertIn("evidence_tier", ed)
        self.assertIn("period_source_status", ed)
        self.assertIn("NO PERIOD (1999) ARTICLE", ed["period_source_status"])
        # The old overclaiming label must not appear as this field's status.
        combined = json.dumps(ed, ensure_ascii=False)
        self.assertNotIn("BOUNDED-to-PROVEN", combined)

    # ------------------------------------------------------------------
    # Architecture verdict - re-derived, blockers separated by kind
    # ------------------------------------------------------------------

    def test_architecture_verdict_separates_historical_and_engine_blockers(self):
        current = self.packet["tokyo_dome_research_current"]
        self.assertEqual("BLOCKED_BY_BOTH", current["architecture_verdict"])
        detail = current["architecture_verdict_detail"]
        self.assertIn("historical_evidence_blockers", detail)
        self.assertIn("engine_representation_blockers", detail)
        self.assertGreater(len(detail["historical_evidence_blockers"]["items"]), 0)
        self.assertGreater(len(detail["engine_representation_blockers"]["items"]), 0)
        engine_items = " ".join(detail["engine_representation_blockers"]["items"])
        self.assertIn("deck_out", engine_items)
        # Tribute Summon's engine gap must be explicitly excluded from the
        # blocker list, per the task's own reasoning about applicability.
        self.assertNotIn("tribute_summon -", engine_items)
        self.assertIn("explicitly_not_counted_as_a_blocker", detail)
        self.assertIn("tribute_summon", detail["explicitly_not_counted_as_a_blocker"])

        readiness = current["tokyo_dome_rule_profile_readiness"]
        self.assertEqual("BLOCKED_BY_HISTORICAL_EVIDENCE", readiness["verdict"])

    # ------------------------------------------------------------------
    # Release ledger - preserved and re-verified live
    # ------------------------------------------------------------------

    def test_release_ledger_reverified_live_and_unchanged(self):
        current = self.packet["tokyo_dome_research_current"]
        preserved = current["release_ledger_preserved"]["verified_this_session"]
        self.assertEqual("1999-08-25", preserved["pre_event_snapshot"])
        self.assertEqual(370, preserved["pool_size"])
        self.assertEqual(
            "f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb",
            preserved["pool_digest_sha256"],
        )
        self.assertEqual(19, preserved["products_through_cutoff"])

        pool = _make_pool()
        index = ReleaseIndex.build(self.repo)
        evaluation = evaluate_cutoff(pool, self.repo, index)
        cards = evaluation.cards()
        digest = hashlib.sha256(
            json.dumps(
                [{"passcode": c["passcode"], "name": c["name"]} for c in cards],
                separators=(",", ":"), sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(370, len(cards))
        self.assertEqual("f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb", digest)

        names_in_pool = {c["name"] for c in cards}
        for excluded in ("Gate Guardian", "Suijin", "Kazejin", "Sanga of the Thunder", "Exodia the Forbidden One"):
            self.assertNotIn(excluded, names_in_pool)

        fabricated = ROOT / "data" / "releases" / "products" / "yu-gi-oh-duel-monsters-national-tournament-prize-cards.json"
        self.assertFalse(fabricated.exists())

    def test_personally_reverified_claims_are_recorded(self):
        current = self.packet["tokyo_dome_research_current"]
        claims = current["personally_reverified_claims"]
        self.assertGreaterEqual(len(claims), 5)
        for c in claims:
            self.assertTrue(c["claim_source_id"])
            self.assertTrue(c["source_url"])
            self.assertTrue(c["exact_rule_claim"])
            self.assertTrue(c["supporting_excerpt"])
            self.assertTrue(c["what_it_establishes"])

    # ------------------------------------------------------------------
    # Final consistency-cleanup pass: recursive invariants over the whole
    # active/current subtree, not just selected fields.
    # ------------------------------------------------------------------

    def test_A_no_superseded_active_terminology_anywhere(self):
        # 6A: walk every scalar string under tokyo_dome_research_current and
        # fail on legacy active-language phrases, except inside explicitly
        # archival/audit-labeled paths (structural exclusion, not regex).
        current = self.packet["tokyo_dome_research_current"]
        violations = []
        for path, s in _walk_strings(current, ("tokyo_dome_research_current",)):
            path_str = "/".join(path).lower()
            if any(marker in path_str for marker in EXEMPT_PATH_MARKERS):
                continue
            low = s.lower()
            for phrase in LEGACY_BANNED_PHRASES:
                if phrase in low:
                    violations.append((path, phrase))
        self.assertEqual([], violations, f"legacy phrases found outside archival fields: {violations}")

        # The archive itself is explicitly permitted (even expected) to still
        # contain some of this old wording, proving nothing was silently
        # deleted, only relabeled as non-authoritative.
        archive_text = json.dumps(self.packet["superseded_findings"], ensure_ascii=False)
        # (Not asserting presence of every phrase here - the archive's own
        # content is whatever the rejected pass actually wrote; this session
        # does not edit it. The important invariant is the one above: these
        # phrases cannot leak into the ACTIVE section.)
        self.assertTrue(archive_text)

    def test_B_no_exact_may_5_claim_inside_confirmed_semantics_fields(self):
        # 6B: any field whose path means confirmed/proven/definitely-changed
        # must not encode 1999-05-05 as the exact Expert Rules effective
        # date. Checked both structurally (evidence_matrix status pairing)
        # and via a generic recursive path-name scan - not just one entry.
        current = self.packet["tokyo_dome_research_current"]

        for row in current["evidence_matrix"]:
            # Only the later_1999 tier's own status governs the later_1999
            # date claim - starter_box_evidence_status is a genuinely
            # independent sub-claim (e.g. spell_trap_response's Starter Box
            # "no chain concept" is legitimately PROVEN even though its
            # separate later-1999 cap-removal date is not) and must not be
            # asserted to correlate with it.
            if "1999-05-05" in row.get("later_1999_effective_bounds", ""):
                self.assertNotEqual("PROVEN", row["later_1999_evidence_status"])
                self.assertEqual("STRONG_SECONDARY_RECONSTRUCTION", row["later_1999_evidence_status"])

        cb = current["change_boundary_before_tokyo_dome"]
        self.assertNotIn("confirmed_changed_by_aug_26_1999", cb)
        confirmed_unchanged_text = " ".join(cb["confirmed_unchanged_by_aug_26_1999"])
        self.assertNotIn("1999-05-05", confirmed_unchanged_text)

        hyp = cb["exact_date_hypothesis_for_the_above"]
        self.assertEqual("1999-05-05", hyp["best_supported_exact_date_hypothesis"])
        self.assertEqual("STRONG_SECONDARY_RECONSTRUCTION", hyp["evidence_status"])
        self.assertNotEqual("PROVEN", hyp["evidence_status"])

        violations = []
        for path, s in _walk_strings(current, ()):
            path_str = "/".join(path).lower()
            semantically_confirmed = (
                "confirmed" in path_str or "proven" in path_str or "definitely" in path_str
            )
            if semantically_confirmed and "1999-05-05" in s:
                violations.append(path)
        self.assertEqual([], violations, f"1999-05-05 found inside a confirmed/proven-semantics field: {violations}")

    def test_B2_no_semantic_may_5_proof_contamination_in_active_prose(self):
        # 6B strengthened: the previous test only caught contamination when
        # the FIELD PATH happened to be named confirmed/proven/definitely.
        # That missed ordinary prose fields (e.g.
        # supersedes.corrected_claims[*].correction) whose VALUE positively
        # asserted "introduced by the May 5, 1999 ... revision - PROVEN for
        # the later-1999 tier" while the path itself said nothing special.
        # This recursively inspects every active scalar string's CONTENT,
        # not just its path, distinguishing a positive assertion from a
        # correction/negation via a "not"/negation-token check - not a
        # naive global ban on the words "PROVEN" and "1999-05-05" appearing
        # together (see _is_may_5_proof_violation and its docstring).
        current = self.packet["tokyo_dome_research_current"]
        violations = [
            (path, s) for path, s in _walk_strings(current, ())
            if _is_may_5_proof_violation(path, s)
        ]
        self.assertEqual(
            [], violations,
            f"active prose positively asserts May 5 as proven/confirmed: {violations}",
        )

        # Archival/audit paths remain explicitly exempt by design - prove
        # that exemption is real (not merely "no such content exists") by
        # confirming at least one archival path DOES contain the rejected
        # language, and the exemption is what keeps it out of the violation
        # list above, not mere absence.
        corrected_claims = current["supersedes"]["corrected_claims"]
        prior_claim_text = " ".join(c["prior_claim"] for c in corrected_claims)
        self.assertIn("PROVEN", prior_claim_text)

    def test_tribute_summon_corrected_claim_matches_evidence_matrix(self):
        # 6/item 5: direct, structural regression for the specific surviving
        # bug - the Tribute Summon corrected-claim entry must not say the
        # May 5 transition is PROVEN, must identify the exact date as
        # secondary/reconstructed/unproven, and must remain consistent with
        # the evidence_matrix's own tribute_summon row.
        current = self.packet["tokyo_dome_research_current"]
        corrected_claims = current["supersedes"]["corrected_claims"]
        tribute_claim = next(
            c for c in corrected_claims
            if "Tribute" in c["prior_claim"] and "Tribute/Advance Summon" in c["prior_claim"]
        )
        correction = tribute_claim["correction"]

        # Must not contain the exact bad phrase that survived the previous pass.
        self.assertNotIn(
            "PROVEN for the later-1999 tier, dated with reasonable confidence",
            correction,
        )
        # Must explicitly identify the exact date as not proven / reconstructed.
        self.assertIn("STRONG_SECONDARY_RECONSTRUCTION", correction)
        self.assertIn("not PROVEN", correction)
        self.assertFalse(_is_may_5_proof_violation(("supersedes", "corrected_claims", "4", "correction"), correction))

        # Must remain consistent with the evidence_matrix's own status for
        # this rule area - the correction is not allowed to drift from the
        # matrix it is meant to describe.
        tribute_row = next(r for r in current["evidence_matrix"] if r["rule_area"] == "tribute_summon")
        self.assertEqual("STRONG_SECONDARY_RECONSTRUCTION", tribute_row["later_1999_evidence_status"])
        self.assertEqual("UNKNOWN", tribute_row["starter_box_evidence_status"])

    def test_C_exactly_one_unqualified_architecture_verdict(self):
        # 6C: exactly one current unqualified format-level verdict,
        # BLOCKED_BY_BOTH. Any legacy "B" verdict is explicitly scoped to
        # schema/host representability, not left as a competing answer.
        self.assertNotIn("architecture", self.packet)
        self.assertEqual("BLOCKED_BY_BOTH", self.packet["tokyo_dome_research_current"]["architecture_verdict"])

        scoped = self.packet["schema_host_architecture_assessment"]
        self.assertNotEqual("B", scoped["verdict"])
        self.assertNotEqual("BLOCKED_BY_BOTH", scoped["verdict"])
        self.assertIn("schema", scoped["verdict"].lower())
        self.assertIn("BLOCKED_BY_BOTH", scoped["_scope"])
        self.assertIn("tokyo_dome_research_current.architecture_verdict", scoped["_scope"])

    def test_D_all_active_certified_product_references_are_19(self):
        # 6D: all active certified-product references resolve to 19; no
        # stale "20 products" wording survives anywhere outside the archive.
        self.assertEqual(19, self.packet["release_ledger_certification"]["certified_product_count"])
        violations = []
        for path, s in _walk_strings(self.packet, ()):
            if path and path[0] == "superseded_findings":
                continue
            low = s.lower()
            if "20 product" in low or "all 20" in low or "(20 curated" in low or "20-product" in low:
                violations.append((path, s[:200]))
        self.assertEqual([], violations, f"stale '20 products' reference(s): {violations}")

    def test_E_restriction_list_status_derives_only_from_the_two_axes(self):
        # 6E: all active restriction-list status consumers derive from
        # research_confidence + canonicalization_status; no third legacy
        # summary field exists to contradict them.
        rc = self.packet["tokyo_dome_research_current"]["restriction_list_current"]
        self.assertEqual(
            {
                "_read_me_first", "content", "research_confidence", "canonicalization_status",
                "master_guide_p84_verification", "yugipedia_revision_provenance",
            },
            set(rc.keys()),
        )
        self.assertEqual("BLOCKING", rc["canonicalization_status"]["status"])
        self.assertIn("MODERATE-TO-GOOD", rc["research_confidence"]["confidence_level"])

    def test_trap_hole_followup_is_context_not_independent_scope_proof(self):
        # The Master Guide finding must remain: header = strongest evidence
        # for tournament-limited scope; Trap Hole's later unrestriction is
        # additional chronology/context, not independent proof of scope.
        reasoning = self.packet["tokyo_dome_research_current"]["restriction_list_current"]["research_confidence"]["reasoning"]
        self.assertIn("大会限定", reasoning)  # the header text is still present and load-bearing
        self.assertIn("CHRONOLOGY/CONTEXT", reasoning)
        self.assertIn("NOT treated here as separately proving", reasoning)
        self.assertNotIn("independent data point supporting the tournament-specific reading", reasoning)
        self.assertNotIn("independent evidence favoring a one-off tournament rule", reasoning)

    def test_no_dangling_references_to_renamed_restriction_field(self):
        # The prior session's restriction_list_reassessment field was
        # renamed to restriction_list_current - no active prose may still
        # point readers at the old, now-nonexistent name.
        current = self.packet["tokyo_dome_research_current"]
        for path, s in _walk_strings(current, ()):
            self.assertNotIn("restriction_list_reassessment", s)

    # ------------------------------------------------------------------
    # 2026-08-29 primary-source resolution addendum
    # ------------------------------------------------------------------

    def _assert_primary_source_invariants(self, packet):
        current = packet["tokyo_dome_research_current"]
        resolution = current["primary_source_resolution_2026_08_29"]
        sources = {source["id"]: source for source in packet["sources"]}

        effective = resolution["expert_rules_primary_material"]["effective_date_adjudication"]
        if effective["all_three_changes_effective_on_1999_05_05"]["status"] == "PROVEN":
            source_ids = effective["all_three_changes_effective_on_1999_05_05"]["source_ids"]
            effective_sources = [sources[source_id] for source_id in source_ids if source_id in sources]
            if not any(source.get("effective_transition_primary") for source in effective_sources):
                raise AssertionError("publication/content evidence was laundered into an exact effective date")
        if resolution["tokyo_dome_event_ruleset_adjudication"]["status"] == "PROVEN":
            event_ids = resolution["tokyo_dome_event_ruleset_adjudication"]["event_specific_source_ids_inspected"]
            event_sources = [sources[source_id] for source_id in event_ids if source_id in sources]
            if not any(source.get("event_specific_primary") for source in event_sources):
                raise AssertionError("general or retrospective evidence was laundered into event adoption")

        restriction = resolution["restriction_list_scope_adjudication"]
        if restriction["required_outcome"] != "UNRESOLVED_BLOCKING":
            raise AssertionError("restriction-list content was laundered into a scope verdict")

        for row in resolution["three_column_evidence_matrix"]:
            if row["tokyo_dome"]["status"] == "PROVEN":
                event_ids = row["tokyo_dome"]["source_ids"]
                event_sources = [sources[source_id] for source_id in event_ids if source_id in sources]
                if not any(source.get("event_specific_primary") for source in event_sources):
                    raise AssertionError(f"{row['rule_area']} has no event-specific primary evidence")

    def test_actual_1999_expert_rules_scan_is_recorded_without_date_or_event_laundering(self):
        current = self.packet["tokyo_dome_research_current"]
        resolution = current["primary_source_resolution_2026_08_29"]
        material = resolution["expert_rules_primary_material"]
        document = material["document"]
        self.assertTrue(material["located"])
        self.assertEqual("1999-05-05", document["publication_date"])
        self.assertEqual([101, 102, 103, 104, 105, 107, 108, 109], document["personally_inspected_pages"])
        self.assertEqual("PROVEN", material["effective_date_adjudication"]["publication_date"]["status"])
        self.assertEqual("PROVEN", material["effective_date_adjudication"]["expert_rules_available_by_1999_05_05"]["status"])
        self.assertEqual(
            "SUPPORTED_BUT_INCOMPLETE",
            material["effective_date_adjudication"]["all_three_changes_effective_on_1999_05_05"]["status"],
        )
        self.assertFalse(resolution["tokyo_dome_event_ruleset_adjudication"]["expert_rules_directly_proven_at_event"])
        self.assertEqual("UNKNOWN", resolution["tokyo_dome_event_ruleset_adjudication"]["status"])
        self._assert_primary_source_invariants(self.packet)

    def test_three_column_matrix_uses_the_required_status_vocabulary_and_keeps_event_unknown(self):
        resolution = self.packet["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]
        allowed = {
            "PROVEN",
            "STRONG_SECONDARY_RECONSTRUCTION",
            "SUPPORTED_BUT_INCOMPLETE",
            "UNKNOWN",
            "CONTRADICTED",
            "NOT_APPLICABLE",
        }
        matrix = resolution["three_column_evidence_matrix"]
        self.assertGreaterEqual(len(matrix), 15)
        for row in matrix:
            self.assertEqual({"rule_area", "starter_box", "later_pre_tokyo_dome", "tokyo_dome"}, set(row))
            for column in ("starter_box", "later_pre_tokyo_dome", "tokyo_dome"):
                self.assertIn(row[column]["status"], allowed)
                self.assertIn("source_ids", row[column])
            if row["tokyo_dome"]["status"] == "PROVEN":
                self.fail(f"event-specific rule was promoted without an event document: {row['rule_area']}")

    def test_restriction_scope_has_exact_required_unresolved_verdict_and_separate_hypotheses(self):
        scope = self.packet["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["restriction_list_scope_adjudication"]
        self.assertEqual("UNRESOLVED_BLOCKING", scope["required_outcome"])
        self.assertEqual("UNRESOLVED_BLOCKING", scope["verdict"])
        self.assertEqual({"H1", "H2", "H3", "H4"}, {hypothesis["id"] for hypothesis in scope["hypotheses"]})
        self.assertEqual({"Raigeki", "Dark Hole", "Trap Hole"}, {card["name"] for card in scope["content"]})
        self.assertIn("contemporaneous", scope["what_would_close_it"].lower())

    def test_adversarial_source_laundering_mutations_fail(self):
        # A: a secondary May-5 claim cannot become a proven effective date.
        mutated = copy.deepcopy(self.packet)
        effective = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["expert_rules_primary_material"]["effective_date_adjudication"]
        effective["all_three_changes_effective_on_1999_05_05"]["status"] = "PROVEN"
        with self.assertRaises(AssertionError):
            self._assert_primary_source_invariants(mutated)

        # B: a general guide cannot become an event-specific proof.
        mutated = copy.deepcopy(self.packet)
        event = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["tokyo_dome_event_ruleset_adjudication"]
        event["status"] = "PROVEN"
        event["event_specific_source_ids_inspected"] = ["official-guide-starter-book-1999-scan"]
        with self.assertRaises(AssertionError):
            self._assert_primary_source_invariants(mutated)

        # C: list content cannot become proof of list scope.
        mutated = copy.deepcopy(self.packet)
        scope = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["restriction_list_scope_adjudication"]
        scope["required_outcome"] = "PROVEN_TOKYO_DOME_ONLY"
        with self.assertRaises(AssertionError):
            self._assert_primary_source_invariants(mutated)

    def test_legitimate_new_primary_source_can_be_attached_to_a_promotion(self):
        # F: the invariant is evidence-sensitive, not a permanent ban on
        # future promotion. A future researcher may promote a proposition
        # only after attaching a source explicitly marked as establishing that
        # exact proposition.
        mutated = copy.deepcopy(self.packet)
        fixture = {
            "id": "fixture-event-rulesheet",
            "label": "Future inspected Tokyo Dome rulesheet fixture",
            "kind": "contemporaneous-official-primary-scan",
            "url": "https://example.invalid/future-tokyo-dome-rulesheet",
            "event_specific_primary": True,
            "effective_transition_primary": True,
        }
        mutated["sources"].append(fixture)
        resolution = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]
        effective = resolution["expert_rules_primary_material"]["effective_date_adjudication"]["all_three_changes_effective_on_1999_05_05"]
        effective["status"] = "PROVEN"
        effective["source_ids"] = ["fixture-event-rulesheet"]
        event = resolution["tokyo_dome_event_ruleset_adjudication"]
        event["status"] = "PROVEN"
        event["event_specific_source_ids_inspected"] = ["fixture-event-rulesheet"]
        self._assert_primary_source_invariants(mutated)

    def test_resolution_preserves_approved_certification_and_non_actions(self):
        current = self.packet["tokyo_dome_research_current"]
        resolution = current["primary_source_resolution_2026_08_29"]
        self.assertEqual("BLOCKED_BY_BOTH", resolution["architecture_verdict"])
        self.assertEqual("BLOCKED_BY_BOTH", current["architecture_verdict"])
        self.assertEqual(19, current["release_ledger_preserved"]["verified_this_session"]["products_through_cutoff"])
        self.assertEqual(370, current["release_ledger_preserved"]["verified_this_session"]["pool_size"])
        self.assertEqual("f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb", current["release_ledger_preserved"]["verified_this_session"]["pool_digest_sha256"])
        self.assertTrue(any("canonical Tokyo Dome" in item for item in resolution["explicit_non_actions"]))


if __name__ == "__main__":
    unittest.main()
