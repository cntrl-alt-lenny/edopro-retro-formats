"""Reproducibility checks for the research-only Tengu format gate.

These tests intentionally do not create a format, banlist, pool, or rule
profile.  They prove only the researched inputs and the current architecture's
ability to evaluate a proposed snapshot in memory.
"""

from __future__ import annotations

import datetime as _dt
import json
import unittest
from dataclasses import replace
from pathlib import Path

from retroformats.lflist import select_applicable_errata
from retroformats.model import Coverage, ErratumV2, Pool
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs" / "research" / "tengu-format-source-packet.json"
COMMUNITY_DIFF = ROOT / "docs" / "research" / "tengu-format-community-diff.json"
COMMUNITY_CANDIDATES = ROOT / "docs" / "research" / "tengu-format-community-candidates.json"

DT_EXCLUDED_PRODUCTS = (
    "duel-terminal-4",
    "duel-terminal-5",
    "duel-terminal-5a",
)
SNEAK_PEEK_EXCLUDED_PRODUCTS = (
    "storm-of-ragnarok-sneak-peek-participation-card",
    "extreme-victory-sneak-peek-participation-card",
    "generation-force-sneak-peek-participation-card",
)


EXPECTED_EDISON_STYLE_FALLBACK = {
    "erratum-splendid-venus": (5645210, 511003054),
    "erratum-goyo-guardian": (7391448, 511002994),
    "erratum-sinister-serpent": (8131171, 511000818),
    "erratum-imperial-custom": (9995766, 9995776),
    "erratum-cyber-blader": (10248389, 511002991),
    "erratum-swords-of-concealing-light": (12923641, 504700018),
    "erratum-stronghold-the-moving-fortress": (13955608, 511003022),
    "erratum-summoner-of-illusions": (14644902, 504700184),
    "erratum-rescue-cat": (14878871, 511002992),
    "erratum-ultimate-tyranno": (15894048, 511003009),
    "erratum-night-assailant": (16226786, 16226796),
    "erratum-exchange-of-the-spirit": (17484499, 511000820),
    "erratum-ryko-lightsworn-hunter": (21502796, 511003007),
    "erratum-makyura-the-destructor": (21593977, 21593987),
    "erratum-cost-down": (23265313, 504700039),
    "erratum-heavy-mech-support-platform": (23265594, 511002851),
    "erratum-burning-land": (24294108, 504700043),
    "erratum-ancient-fairy-dragon": (25862681, 25862691),
    "erratum-super-rejuvenation": (27770341, 504700049),
    "erratum-nutrient-z": (29389368, 504700051),
    "erratum-dark-strike-fighter": (32646477, 511000229),
    "erratum-clear-world": (33900648, 33900658),
    "erratum-manga-ryu-ran": (38369349, 504700062),
    "erratum-dark-magician-of-chaos": (40737112, 511001039),
    "erratum-gilasaurus": (45894482, 511003006),
    "erratum-brionac-dragon-of-the-ice-barrier": (50321796, 511002993),
    "erratum-blue-eyes-toon-dragon": (53183600, 504700086),
    "erratum-mysterious-puppeteer": (54098121, 504700088),
    "erratum-destiny-hero-disk-commander": (56570271, 511003116),
    "erratum-crush-card-virus": (57728570, 511000822),
    "erratum-wulf-lightsworn-beast": (58996430, 511003020),
    "erratum-imperial-order": (61740673, 511002996),
    "erratum-senet-switch": (63394872, 63394882),
    "erratum-z-metal-tank": (64500000, 511002853),
    "erratum-big-shield-gardna": (65240384, 65240394),
    "erratum-toon-mermaid": (65458948, 504700108),
    "erratum-y-dragon-head": (65622692, 511002852),
    "erratum-armored-cybern": (67159705, 511003055),
    "erratum-spirit-ryu": (67957315, 504700185),
    "erratum-my-body-as-a-shield": (69279219, 504700189),
    "erratum-future-fusion": (77565204, 511002997),
    "erratum-darkness-approaches": (80168720, 511003028),
    "erratum-chaos-emperor-dragon-envoy-of-the-end": (82301904, 511000819),
    "erratum-ring-of-destruction": (83555666, 511000824),
    "erratum-king-tiger-wanghu": (83986578, 504700143),
    "erratum-brain-control": (87910978, 511002995),
    "erratum-red-eyes-darkness-metal-dragon": (88264978, 88264988),
    "erratum-hallowed-life-barrier": (88789641, 504700153),
    "erratum-toon-summoned-skull": (91842653, 504700160),
    "erratum-jirai-gumo": (94773007, 504700190),
    "erratum-catapult-turtle": (95727991, 511000228),
    "erratum-w-wing-catapult": (96300057, 511002901),
}


def _fresh_tengu_pool_raw(pool_id):
    raw = {
        "$schema": "../../schemas/pool.schema.json",
        "id": pool_id,
        "region": "TCG",
        "kind": "release-cutoff",
        "cutoff": {
            "cutoff_date": "2011-09-17",
            "territories": ["tcg", "tcg-na", "tcg-eu", "tcg-oce"],
            "include": [],
            "exclude": [],
            "exclude_products": [
                {
                    "product": product,
                    "reason": "Period-2011 Duel Terminal sanctioned-legality policy.",
                    "sources": ["konami-tcg-tournament-policy-v11-2011"],
                }
                for product in DT_EXCLUDED_PRODUCTS
            ] + [
                {
                    "product": product,
                    "reason": "Official 2011 product archive identifies this as an event-only Sneak Peek participation product; it is not used as retail pool authority.",
                    "sources": ["konami-2011-product-pages", "yugipedia-set-pages"],
                }
                for product in SNEAK_PEEK_EXCLUDED_PRODUCTS
            ],
        },
    }
    return raw


def _fresh_tengu_evaluation(repo):
    index = ReleaseIndex.build(repo)
    raw = _fresh_tengu_pool_raw("research-only-tengu-community-comparison")
    return evaluate_cutoff(Pool.load(raw, Path("/tmp/research-only-tengu-community-comparison.json")), repo, index)


class TenguResearchGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(ROOT)
        cls.packet = json.loads(PACKET.read_text(encoding="utf-8"))
        cls.community_candidates = json.loads(COMMUNITY_CANDIDATES.read_text(encoding="utf-8"))

    def test_canonical_tengu_artifacts_exist(self):
        self.assertTrue(any(ROOT.glob("formats/*tengu*")))
        self.assertTrue(any((ROOT / "data" / "banlists").glob("**/*2011-09*")))
        self.assertTrue(any((ROOT / "data" / "pools").glob("*tengu*")))
        self.assertTrue(any((ROOT / "data" / "rule-profiles").glob("*tengu*")))

    def test_researched_banlist_packet_is_exactly_sized_and_internally_consistent(self):
        banlist = self.packet["banlist"]
        self.assertIn("yugioh-card.com", banlist["source"])
        self.assertEqual(51, len(banlist["forbidden"]))
        self.assertEqual(65, len(banlist["limited"]))
        self.assertEqual(18, len(banlist["semi_limited"]))
        self.assertEqual(7, len(banlist["unlimited_changes"]))
        all_codes = [row["passcode"] for key in ("forbidden", "limited", "semi_limited", "unlimited_changes") for row in banlist[key]]
        self.assertEqual(len(all_codes), len(set(all_codes)))
        self.assertEqual(85602018, next(row["passcode"] for row in banlist["forbidden"] if row["name"] == "Last Will"))

    def test_all_296_errata_evaluate_at_proposed_snapshot_without_runtime_changes(self):
        self.assertEqual([], [str(e) for e in self.repo.load_errors])
        self.assertEqual(296, len(self.repo.errata))
        self.assertTrue(all(isinstance(e, ErratumV2) for e in self.repo.errata.values()))
        snapshot = _dt.date(2011, 9, 17)
        selections = {eid: e.selection_at(snapshot) for eid, e in self.repo.errata.items()}
        determinate = [s for s in selections.values() if s.chronology == "determinate"]
        ambiguous = [s for s in selections.values() if s.chronology == "ambiguous"]
        self.assertEqual(126, len(determinate))
        self.assertEqual(170, len(ambiguous))
        self.assertEqual(33, sum(s.candidates[0].coverage.kind == Coverage.MODERN for s in determinate))
        self.assertEqual(52, sum(s.candidates[0].coverage.kind == Coverage.REUSE_UPSTREAM for s in determinate))
        self.assertEqual(38, sum(s.candidates[0].coverage.kind == Coverage.KNOWN_GAP for s in determinate))
        self.assertEqual(3, sum(s.candidates[0].coverage.kind == Coverage.NONE_NEEDED for s in determinate))
        self.assertEqual(126, 33 + 52 + 38 + 3)
        self.assertEqual(161, sum(s.modern_is_possible for s in ambiguous))
        self.assertEqual(9, sum(not s.modern_is_possible for s in ambiguous))

        unresolved_records = sum(
            any(candidate.coverage.kind == Coverage.UNRESOLVED for candidate in s.candidates)
            for s in selections.values()
        )
        unresolved_occurrences = sum(
            sum(candidate.coverage.kind == Coverage.UNRESOLVED for candidate in s.candidates)
            for s in selections.values()
        )
        self.assertEqual(47, unresolved_records)
        self.assertEqual(89, unresolved_occurrences)

        fallback_format = replace(
            self.repo.formats["2010-03-edison"],
            id="research-only-tengu-fallback",
            snapshot="2011-09-17",
            reference_parity=None,
            errata_include=[],
            errata_exclude=[],
        )
        fallback = select_applicable_errata(fallback_format, self.repo)
        actual_mapping = {
            override.erratum.id: (modern_passcode, override.implementation.historical_passcode)
            for modern_passcode, override in fallback.items()
        }
        self.assertEqual(EXPECTED_EDISON_STYLE_FALLBACK, actual_mapping)
        self.assertEqual(52, len(actual_mapping))

        audit = self.packet["release_certification"]["erratum_audit_at_snapshot"]
        self.assertEqual(89, audit["unresolved_candidate_state_occurrences"])
        self.assertEqual(52, audit["historical_substitution_count"])
        self.assertEqual(
            EXPECTED_EDISON_STYLE_FALLBACK,
            {
                row["id"]: (row["modern_passcode"], row["historical_passcode"])
                for row in audit["historical_fallback_mapping"]
            },
        )

    def test_community_pool_difference_is_exact_and_canonicalizes_aliases(self):
        diff = json.loads(COMMUNITY_DIFF.read_text(encoding="utf-8"))
        source = diff["source"]
        self.assertEqual("https://tenguformat.com/wp-content/uploads/database/allCardsTengu.json", source["url"])
        self.assertEqual("f9aae30f4501b28545ff498d494b1ac87b282b4eb4f4f99873c073531ff163cc", source["sha256"])
        self.assertEqual(5035, source["records"])
        self.assertEqual(4572, source["dated_candidate_count"])
        self.assertEqual(4562, diff["certified_pool_count"])
        candidates = self.community_candidates
        for key in ("url", "retrieved", "sha256", "records", "date_field", "comparison_cutoff"):
            self.assertEqual(source[key], candidates["source"][key])
        self.assertEqual(5033, candidates["candidate_record_count"])
        self.assertEqual(4572, candidates["candidate_identity_count"])
        community_candidate = set(candidates["candidate_passcodes"])
        self.assertEqual(4572, len(community_candidate))

        evaluation = _fresh_tengu_evaluation(self.repo)
        derived_ours = set(evaluation.included)
        self.assertEqual(4562, len(derived_ours))
        self.assertEqual(0, len(evaluation.ambiguous))

        ours = {
            10000010, 37115575, 56043446, 87259077, 88071625,
        }
        community = {
            10000002, 18807109, 19230408, 35686188, 39751094, 56043447,
            64335805, 68540059, 73134082, 80604092, 81480461, 83011278,
            83764719, 84080939, 84257640,
        }
        self.assertEqual(ours, {row["passcode"] for row in diff["ours_minus_tenguformat"]})
        self.assertEqual(community, {row["passcode"] for row in diff["tenguformat_minus_ours"]})
        self.assertEqual(ours, derived_ours - community_candidate)
        self.assertEqual(community, community_candidate - derived_ours)
        canonicalized_community = (community_candidate - community) | {
            row["our_canonical_passcode"] for row in diff["tenguformat_minus_ours"]
        }
        self.assertEqual(
            {10000010, 37115575, 87259077, 88071625},
            derived_ours - canonicalized_community,
        )
        self.assertEqual(set(), canonicalized_community - derived_ours)
        self.assertEqual(
            {
                "ours_only": [10000010, 37115575, 87259077, 88071625],
                "community_only": [],
            },
            diff["canonicalized_semantic_difference"],
        )
        self.assertEqual(5, len(ours))
        self.assertEqual(15, len(community))
        self.assertTrue(all(not row["changes_toronto_legality"] for row in diff["ours_minus_tenguformat"] + diff["tenguformat_minus_ours"]))
        self.assertNotIn(33574806, derived_ours)
        self.assertNotIn(33574806, community_candidate)
        self.assertNotEqual(ours, ({33574806} | derived_ours) - community_candidate)
        self.assertNotEqual(ours, (derived_ours - {10000010}) - community_candidate)

        for row in diff["tenguformat_minus_ours"]:
            canonical = row["our_canonical_passcode"]
            self.assertIn(canonical, self.repo.card_index.by_passcode)
            self.assertEqual(row["our_canonical_name"], self.repo.card_index.name_of(canonical))
            self.assertEqual("alias-or-artwork-identity", row["classification"])
            indexed = self.repo.card_index.by_passcode.get(row["passcode"])
            if indexed is not None and indexed.get("alias_of") is not None:
                self.assertEqual(canonical, int(indexed["alias_of"]))
        for row in diff["ours_minus_tenguformat"]:
            self.assertEqual(row["name"], self.repo.card_index.name_of(row["passcode"]))
            self.assertIn(row["classification"], {"community-omission", "community-date-error", "alias-or-artwork-identity"})

        packet_cross_check = self.packet["release_certification"]["community_pool_cross_check"]
        self.assertEqual("tengu-format-community-candidates.json", packet_cross_check["fixture"])
        self.assertEqual("tengu-format-community-diff.json", packet_cross_check["difference_fixture"])
        self.assertEqual(ours, set(packet_cross_check["ours_minus_tenguformat"]))
        self.assertEqual(community, set(packet_cross_check["tenguformat_minus_ours"]))
        self.assertEqual(
            diff["canonicalized_semantic_difference"],
            packet_cross_check["canonicalized_semantic_difference"],
        )

    def test_certified_release_projection_is_fresh_not_edison_derived(self):
        self.assertIsNotNone(self.repo.release_coverage)
        self.assertTrue(
            self.repo.release_coverage.covers(
                _dt.date(2011, 9, 17),
                frozenset({"tcg", "tcg-na", "tcg-eu", "tcg-oce"}),
                self.repo.release_gaps,
            )
        )
        index = ReleaseIndex.build(self.repo)
        raw = _fresh_tengu_pool_raw("research-only-tengu-projection")
        pool = Pool.load(raw, Path("/tmp/research-only-tengu-projection.json"))
        evaluation = evaluate_cutoff(pool, self.repo, index)
        self.assertEqual(4562, len(evaluation.included))
        self.assertEqual(0, len(evaluation.ambiguous))
        self.assertEqual(0, len(index.unknown_printings))
        excluded = {entry["product"] for entry in raw["cutoff"]["exclude_products"]}
        self.assertNotIn("the-shining-darkness", excluded)
        self.assertNotIn("shonen-jump-may-2010-subscription-bonus", excluded)
        source_by_product = {entry["product"]: entry["sources"] for entry in raw["cutoff"]["exclude_products"]}
        for product in DT_EXCLUDED_PRODUCTS:
            self.assertEqual(["konami-tcg-tournament-policy-v11-2011"], source_by_product[product])
        for product in SNEAK_PEEK_EXCLUDED_PRODUCTS:
            self.assertEqual(["konami-2011-product-pages", "yugipedia-set-pages"], source_by_product[product])

        # 4593 at Tengu's own gate; +119 from the 2026-08 ocg-jp (pre-1999-08-25) release
        # ledger certification, which adds dated canonical cards no TCG pool (including
        # Tengu's) ever includes - see test_yugi_kaiba_format_gate.py and
        # test_ocg1999_release_certification.py for the ocg-jp-scoped assertions.
        self.assertEqual(4712, index.dated_canonical_count())

    def test_official_release_correction_removes_escuridao_from_snapshot(self):
        product = self.repo.products["yu-gi-oh-gx-volume-9-promotional-card"]
        event = product.events[0]
        self.assertEqual("2012-08-07", event.date)
        self.assertEqual("day", event.precision)
        self.assertIn("konami-card-database", event.sources)
        evaluation = _fresh_tengu_evaluation(self.repo)
        self.assertNotIn(33574806, evaluation.included)
        self.assertNotIn(33574806, evaluation.ambiguous)

    def test_remaining_ledger_only_release_evidence_is_pinned(self):
        expected = {
            "shonen-jump-vol-9-issue-1-promotional-card": ("2011-01-01", "month", 10000010),
            "shonen-jump-vol-9-issue-3-promotional-card": ("2011-03-01", "month", 37115575),
            "shonen-jump-december-2010-subscription-bonus": ("2010-12-01", "month", 87259077),
            "shonen-jump-may-2010-subscription-bonus": ("2010-05-01", "month", 88071625),
        }
        for product_id, (date, precision, passcode) in expected.items():
            product = self.repo.products[product_id]
            event = product.events[0]
            self.assertEqual(date, event.date)
            self.assertEqual(precision, event.precision)
            self.assertIn("konami-card-database", event.sources)
            self.assertIn(passcode, {printing.passcode for printing in product.printings})

    def test_packet_records_the_certified_projection_and_import_audit(self):
        certification = self.packet["release_certification"]
        self.assertTrue(certification["coverage_certified"])
        self.assertEqual(411, certification["ledger_products"])
        self.assertEqual(41, certification["new_product_records_added"])
        self.assertEqual("konami-tcg-tournament-policy-v11-2011", certification["candidate_pool"]["duel_terminal_exclusion_source"])
        self.assertEqual(4562, certification["candidate_pool"]["included_cards"])
        self.assertEqual(0, certification["candidate_pool"]["ambiguous_cards"])
        self.assertEqual(0, certification["candidate_pool"]["unknown_printings"])
        self.assertEqual(0, certification["import_anomalies"]["unresolved_pool_impacting_gaps"])

    def test_release_ledger_has_the_2011_products_and_import_anomalies_accounted(self):
        expected = {
            "collectible-tins-2011-wave-1", "demo-pack", "dragunity-legion-structure-deck",
            "duel-terminal-4", "duel-terminal-5", "duel-terminal-5a",
            "duelist-league-3-participation-cards", "duelist-pack-collection-tin-2011",
            "duelist-pack-crow", "duelist-pack-yusei-3", "extreme-victory",
            "extreme-victory-sneak-peek-participation-card", "generation-force",
            "generation-force-sneak-peek-participation-card", "generation-force-special-edition",
            "gold-series-4-pyramids-edition", "hidden-arsenal-4-trishula-s-triumph",
            "hidden-arsenal-special-edition", "lost-sanctuary-structure-deck",
            "shonen-jump-june-july-2011-subscription-bonus", "shonen-jump-vol-9-issue-3-promotional-card",
            "shonen-jump-vol-9-issue-4-promotional-card", "shonen-jump-vol-9-issue-6-promotional-card",
            "shonen-jump-vol-9-issue-8-promotional-card", "starter-deck-dawn-of-the-xyz",
            "storm-of-ragnarok", "storm-of-ragnarok-sneak-peek-participation-card",
            "storm-of-ragnarok-special-edition", "turbo-pack-booster-five", "turbo-pack-booster-six",
            "world-championship-2011-card-pack", "yu-gi-oh-3d-bonds-beyond-time-dvd-promotional-card",
            "yu-gi-oh-3d-bonds-beyond-time-movie-pack", "yu-gi-oh-3d-bonds-beyond-time-theater-distribution-card",
            "yu-gi-oh-5d-s-volume-1-promotional-card",
            "yu-gi-oh-5d-s-world-championship-2011-over-the-nexus-promotional-cards",
            "yu-gi-oh-championship-series-2011-prize-card", "yu-gi-oh-gx-volume-6-promotional-card",
            "yu-gi-oh-gx-volume-7-promotional-card", "yu-gi-oh-gx-volume-9-promotional-card",
            "yu-gi-oh-world-championship-qualifier-national-championships-2011-prize-cards",
        }
        self.assertEqual(41, len(expected))
        self.assertTrue(expected.issubset(self.repo.products))
        # 411 at Tengu's own gate (399 generated + 12 curated); +20 curated ocg-jp
        # (pre-1999-08-25) products from the 2026-08 release ledger certification.
        # products_written (Yugipedia+YGOPRODeck-generated TCG count) is untouched.
        self.assertEqual(430, len(self.repo.products))
        self.assertEqual(399, self.repo.import_report["stats"]["products_written"])
        self.assertEqual(31, self.repo.import_report["stats"]["curated_preserved"])
        self.assertEqual(34, self.repo.import_report["stats"]["yugipedia_only_products"])
        subjects = {s for g in self.repo.release_gaps for s in g.raw["subjects"]}
        self.assertIn("Yu-Gi-Oh! 3D Bonds Beyond Time Blu-ray promotional card", subjects)
        self.assertIn("Yu-Gi-Oh! World Championship 2011 prize cards", subjects)

    def test_proposed_flags_are_declared_research_inputs_not_hidden_runtime_changes(self):
        self.assertEqual(
            {
                "DUEL_OCG_OBSOLETE_IGNITION",
                "DUEL_1ST_TURN_DRAW",
                "DUEL_1_FACEUP_FIELD",
                "DUEL_SPSUMMON_ONCE_OLD_NEGATE",
                "DUEL_RETURN_TO_DECK_TRIGGERS",
                "DUEL_CANNOT_SUMMON_OATH_OLD",
            },
            set(self.packet["proposed_engine_flags"]),
        )


if __name__ == "__main__":
    unittest.main()
