"""Research-only gate for the proposed early OCG Tokyo Dome snapshot."""

from __future__ import annotations

import json
import hashlib
import unittest
from datetime import date
from pathlib import Path

from retroformats.model import Coverage, ErratumV2, Pool
from retroformats.lflist import build_lflist
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "research" / "yugi-kaiba-format-source-packet.json"


class YugiKaibaResearchGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        cls.repo = Repository.load(ROOT)

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
        architecture = self.packet["architecture"]
        self.assertEqual("B", architecture["verdict"])
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
        # This research gate originally recorded zero ocg-territory release events as
        # part of its "blocking" verdict. The 2026-08 release-ledger certification
        # (see test_ocg1999_release_certification.py) has since built a real, sourced
        # ocg-jp product ledger through 1999-08-25 - so this assertion now checks that
        # the ledger exists and is exactly the certified 19 products, not that it is
        # absent (19, not 20: a 2026-08 recertification pass found and deleted one
        # fabricated product - see docs/research/yugi-kaiba-format-source-gate.md
        # "2026-08 recertification"). Canonical Tokyo Dome artifacts remain absent
        # (checked below): the release-ledger blocker being resolved does not by
        # itself make the format canonical-ready (banlist/rules/engine blockers
        # remain, per blocker_ledger).
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

    def test_rules_and_restriction_research_2026_08_is_present_and_structured(self):
        # 2026-08 addendum: the multi-agent restriction-list/rules research gate.
        # This checks the new packet section exists with the required structure -
        # it does NOT re-derive the swarm's historical conclusions (those are prose
        # research findings, not repo-checkable facts), only that the packet
        # honestly records BLOCKED verdicts rather than a canonicalized answer.
        research = self.packet["tokyo_dome_rules_and_restriction_research_2026_08"]
        self.assertEqual("BLOCKED_BY_BOTH", research["architecture_verdict"])
        self.assertEqual("BLOCKED", research["restriction_list_research"]["verdict"])
        self.assertEqual("UNCHANGED: pre-event (1999-08-25), not event-day", research["format_identity"]["snapshot_verdict"])
        self.assertEqual("1999-08-25", research["format_identity"]["recommended_snapshot"])
        self.assertEqual("1999-08-tokyo-dome", research["format_identity"]["recommended_id"])

        # Errata accounting in the new section must match the same live
        # recomputation the older test_frozen_errata_are_all_v2_and_accounted_at_snapshot
        # performs independently below - both derive from repo state, not from each other.
        audit = research["errata_intersection_audit"]
        self.assertEqual(370, audit["pool_size"])
        self.assertEqual(
            "f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb",
            audit["pool_digest_sha256"],
        )
        self.assertEqual(6, audit["pool_relevant_errata_count"])
        self.assertEqual(2, audit["determinate_count"])
        self.assertEqual(4, audit["ambiguous_count"])

        # No new canonical artifact is ever claimed by this section.
        non_actions = " ".join(research["explicit_non_actions"])
        for phrase in (
            "No formats/1999-* canonical format directory was created",
            "No canonical banlist was created",
            "No canonical pool was created",
            "No canonical rule profile was created",
            "dist/ was not modified",
            "No runtime behavior was modified",
            "No schema was modified",
        ):
            self.assertIn(phrase, non_actions)

    def test_rules_research_pool_digest_matches_live_recomputation(self):
        # Recomputed directly from repo state (not read from the packet), exactly
        # like test_frozen_errata_are_all_v2_and_accounted_at_snapshot does for
        # errata - this is the anti-circularity check for the 2026-08 addendum's
        # own pool_digest_sha256 claim.
        raw_pool = {
            "id": "pool-ocg1999-research-only",
            "region": "OCG",
            "kind": "release-cutoff",
            "cutoff": {"cutoff_date": "1999-08-25", "territories": ["ocg-jp"]},
            "sources": ["yugipedia-ocg-series1-set-pages"],
        }
        pool = Pool.load(raw_pool, ROOT / "research-only-pool.json")
        index = ReleaseIndex.build(self.repo)
        evaluation = evaluate_cutoff(pool, self.repo, index)
        cards = evaluation.cards()
        digest = hashlib.sha256(
            json.dumps(
                [{"passcode": c["passcode"], "name": c["name"]} for c in cards],
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(370, len(cards))
        self.assertEqual("f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb", digest)

        research = self.packet["tokyo_dome_rules_and_restriction_research_2026_08"]
        self.assertEqual(len(cards), research["errata_intersection_audit"]["pool_size"])
        self.assertEqual(digest, research["errata_intersection_audit"]["pool_digest_sha256"])

    def test_gate_guardian_and_its_fusion_materials_are_absent_from_the_pre_event_pool(self):
        # Independent repo-state verification (not read from the packet's own
        # prose) backing the format_identity.snapshot_rationale claim that Gate
        # Guardian could not have been Fusion Summoned by anyone restricted to
        # the certified pre-event pool: neither it nor any of its three Fusion
        # Material monsters (Suijin, Kazejin, Sanga of the Thunder) are in the
        # certified 370-card 1999-08-25 pool.
        raw_pool = {
            "id": "pool-ocg1999-research-only",
            "region": "OCG",
            "kind": "release-cutoff",
            "cutoff": {"cutoff_date": "1999-08-25", "territories": ["ocg-jp"]},
            "sources": ["yugipedia-ocg-series1-set-pages"],
        }
        pool = Pool.load(raw_pool, ROOT / "research-only-pool.json")
        index = ReleaseIndex.build(self.repo)
        evaluation = evaluate_cutoff(pool, self.repo, index)
        names_in_pool = {c["name"] for c in evaluation.cards()}
        for excluded in ("Gate Guardian", "Suijin", "Kazejin", "Sanga of the Thunder"):
            self.assertNotIn(excluded, names_in_pool)

    def test_reconciliation_with_prior_gate_flags_the_first_turn_attack_conflict(self):
        # The prior hardening gate's own blocker_ledger row for "first_turn_attack"
        # says RESOLVED. This session's swarm found a genuine, unresolved
        # disagreement about that historical claim. That contradiction must stay
        # visible in the packet, not be silently smoothed over - this test only
        # checks the contradiction is recorded, it does not resolve it either way.
        self.assertEqual("RESOLVED", self.packet["blocker_ledger"]["first_turn_attack"]["status"])
        research = self.packet["tokyo_dome_rules_and_restriction_research_2026_08"]
        reconciliation = research["reconciliation_with_prior_gate"]
        topics = {item["topic"] for item in reconciliation["divergences"]}
        self.assertIn("First-turn attack legality", topics)
        first_turn = next(item for item in reconciliation["divergences"] if item["topic"] == "First-turn attack legality")
        self.assertIn("RESOLVED", first_turn["prior_gate_verdict"])
        self.assertIn("AMBIGUOUS", research["rule_chronology"]["areas"][2]["aug_25_26_1999_status"])
        self.assertEqual("First-turn attack", research["rule_chronology"]["areas"][2]["area"])

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


if __name__ == "__main__":
    unittest.main()
