"""Canonical regression tests for Tengu Format (2011-09-tengu).

Verifies the complete end-to-end integration:
- format definition and metadata
- snapshot and region
- banlist counts (51/65/18) and identity verification
- release-cutoff pool derivation (4,562 canonical cards)
- product exclusions and boundary edge cases
- rule-profile flags, client settings, and partial status
- errata evaluation at snapshot (52 historical substitutions, 38 divergences, 9 known-wrong fallbacks)
- exact 52 historical substitution mapping parity
- generated EDOPro lflist whitelist semantics, determinism, and pinned hash (0xBCBDBABE)
- protected baselines for GOAT and Edison
"""

from __future__ import annotations

import datetime as _dt
import json
import unittest
from pathlib import Path

from retroformats.build import build_all
from retroformats.lflist import (
    build_lflist,
    historical_identity,
    lflist_hash,
    parse_lflist,
    select_applicable_errata,
)
from retroformats.model import Coverage, ErratumV2
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository
from retroformats.validate import Validator
from tests.test_tengu_format_gate import EXPECTED_EDISON_STYLE_FALLBACK

ROOT = Path(__file__).resolve().parents[1]
# Pinned 2026-08-31: Mind Master's pool passcode moved 96782886 -> 96782896
# (region_substitutions, roadmap 1e / card-identity fix) - the only content
# change, so only the hash moved, not cardinality or any other card's status.
TENGU_HASH = 0xBCBDBABE
GOAT_HASH = 0x28E9FC02
EDISON_POOL_COUNT = 3673
TENGU_POOL_COUNT = 4562


class TenguFormatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(ROOT)
        cls.index = ReleaseIndex.build(cls.repo)
        cls.fmt = cls.repo.formats["2011-09-tengu"]

    def test_1_format_exists_and_loads(self):
        self.assertIn("2011-09-tengu", self.repo.formats)
        self.assertEqual("Tengu Format", self.fmt.name)
        self.assertEqual(["Tengu Plant", "Tengu"], self.fmt.raw["aliases"])

    def test_2_snapshot_is_exactly_2011_09_17(self):
        self.assertEqual("2011-09-17", self.fmt.snapshot)

    def test_3_region_is_tcg(self):
        self.assertEqual("TCG", self.fmt.region)

    def test_4_banlist_is_effective_2011_09_01(self):
        self.assertEqual("tcg-2011-09", self.fmt.banlist_id)
        banlist = self.repo.banlists["tcg-2011-09"]
        self.assertEqual("2011-09-01", banlist.effective_date)
        self.assertEqual("TCG", banlist.region)
        self.assertEqual("verified", banlist.raw["completeness"])

    def test_5_banlist_counts_are_exactly_51_65_18(self):
        banlist = self.repo.banlists["tcg-2011-09"]
        forbidden = [e for e in banlist.entries if e.status == "forbidden"]
        limited = [e for e in banlist.entries if e.status == "limited"]
        semilimited = [e for e in banlist.entries if e.status == "semilimited"]
        self.assertEqual(51, len(forbidden))
        self.assertEqual(65, len(limited))
        self.assertEqual(18, len(semilimited))
        self.assertEqual(134, len(banlist.entries))

        # No duplicate passcodes in banlist
        codes = [e.card.passcode for e in banlist.entries]
        self.assertEqual(len(codes), len(set(codes)))

        # Every passcode and name matches the card index
        for entry in banlist.entries:
            self.assertIn(entry.card.passcode, self.repo.card_index.by_passcode)
            self.assertEqual(
                entry.card.name,
                self.repo.card_index.name_of(entry.card.passcode),
            )

        # The seven cards moved to Unlimited must NOT appear as restricted entries
        unlimited_changes = {
            57774843: "Judgment Dragon",
            23205979: "Spirit Reaper",
            22046459: "Megamorph",
            5318639: "Mystical Space Typhoon",
            3659803: "Overload Fusion",
            85742772: "Gravity Bind",
            53567095: "Icarus Attack",
        }
        for code, name in unlimited_changes.items():
            self.assertNotIn(
                code,
                set(codes),
                f"{name} was moved to Unlimited and must not be restricted",
            )

    def test_6_pool_is_exactly_4562_cards(self):
        self.assertEqual("pool-tengu-2011", self.fmt.pool_id)
        pool = self.repo.pools["pool-tengu-2011"]
        self.assertEqual(TENGU_POOL_COUNT, len(pool.cards))
        self.assertEqual("verified", pool.raw["completeness"])
        self.assertEqual("community-retrospective", pool.raw["legality_basis"])

    def test_7_pool_has_zero_unresolved_release_ambiguities(self):
        pool = self.repo.pools["pool-tengu-2011"]
        evaluation = evaluate_cutoff(pool, self.repo, self.index)
        self.assertEqual(TENGU_POOL_COUNT, len(evaluation.included))
        self.assertEqual(0, len(evaluation.ambiguous))
        self.assertEqual(0, len(evaluation.forced_in))
        self.assertEqual(0, len(evaluation.forced_out))

    def test_8_pool_has_zero_unknown_printings(self):
        self.assertEqual(0, len(self.index.unknown_printings))

    def test_9_escuridao_is_absent(self):
        pool = self.repo.pools["pool-tengu-2011"]
        codes = pool.passcodes()
        self.assertNotIn(33574806, codes, "Elemental HERO Escuridao was released in 2012")

    def test_10_representative_genf_cards_are_present(self):
        pool = self.repo.pools["pool-tengu-2011"]
        codes = pool.passcodes()
        genf_samples = {
            10028593: "Reborn Tengu (EXVC)",
            9888196: "Orient Dragon (GENF)",
            69610924: "Number 17: Leviathan Dragon (GENF)",
            68597372: "Wind-Up Zenmaister (GENF)",
            10802915: "Tour Guide From the Underworld (EXVC)",
        }
        for code, name in genf_samples.items():
            self.assertIn(code, codes, f"{name} must be legal in Tengu format")

    def test_11_representative_early_xyz_cards_are_present(self):
        pool = self.repo.pools["pool-tengu-2011"]
        codes = pool.passcodes()
        xyz_samples = {
            84013237: "Number 39: Utopia (YS11)",
            10002346: "Gachi Gachi Gantetsu (YS11)",
            47013502: "Grenosaurus (YS11)",
            69610924: "Number 17: Leviathan Dragon (GENF)",
        }
        for code, name in xyz_samples.items():
            self.assertIn(code, codes, f"{name} must be legal in Tengu format")

    def test_12_dt_exclusives_do_not_leak_into_legality(self):
        pool = self.repo.pools["pool-tengu-2011"]
        codes = pool.passcodes()
        dt_exclusives = {
            1264319: "Gem-Knight Fusion (DT04 machine-only)",
            27004302: "Gem-Armadillo (DT04 machine-only)",
            12986807: "Laval the Greater (DT05 machine-only)",
            13220032: "Vylon Charger (DT05 machine-only)",
            27126980: "Gem-Knight Sapphire (DT05a machine-only)",
        }
        for code, name in dt_exclusives.items():
            self.assertNotIn(code, codes, f"{name} must NOT leak into Tengu legality")

    def test_13_sneak_peek_and_dt_exclusions_have_correct_provenance(self):
        pool = self.repo.pools["pool-tengu-2011"]
        cutoff = pool.cutoff
        dt_prods = {"duel-terminal-4", "duel-terminal-5", "duel-terminal-5a"}
        sp_prods = {
            "storm-of-ragnarok-sneak-peek-participation-card",
            "extreme-victory-sneak-peek-participation-card",
            "generation-force-sneak-peek-participation-card",
        }
        by_prod = {entry["product"]: entry for entry in cutoff["exclude_products"]}
        for prod in dt_prods:
            self.assertIn(prod, by_prod)
            self.assertEqual(
                ["konami-tcg-tournament-policy-v11-2011"],
                by_prod[prod]["sources"],
            )
        for prod in sp_prods:
            self.assertIn(prod, by_prod)
            self.assertEqual(
                ["konami-2011-product-pages", "yugipedia-set-pages"],
                by_prod[prod]["sources"],
            )

    def test_14_rule_profile_flags_are_exactly_approved_six(self):
        self.assertEqual("rules-tcg-mr2-tengu", self.fmt.rule_profile_id)
        rule = self.repo.rule_profiles["rules-tcg-mr2-tengu"]
        expected_flags = {
            "DUEL_OCG_OBSOLETE_IGNITION",
            "DUEL_1ST_TURN_DRAW",
            "DUEL_1_FACEUP_FIELD",
            "DUEL_SPSUMMON_ONCE_OLD_NEGATE",
            "DUEL_RETURN_TO_DECK_TRIGGERS",
            "DUEL_CANNOT_SUMMON_OATH_OLD",
        }
        self.assertEqual(expected_flags, set(rule.flags))
        self.assertEqual(6, len(rule.flags))

    def test_15_duel_0_atk_destroyed_is_absent(self):
        rule = self.repo.rule_profiles["rules-tcg-mr2-tengu"]
        self.assertNotIn("DUEL_0_ATK_DESTROYED", rule.flags)

    def test_16_duel_tcg_fast_effect_ignition_is_absent(self):
        rule = self.repo.rule_profiles["rules-tcg-mr2-tengu"]
        self.assertNotIn("DUEL_TCG_FAST_EFFECT_IGNITION", rule.flags)

    def test_17_rule_profile_status_remains_partial(self):
        self.assertEqual("partial", self.fmt.implementation_status.get("rule_profile"))

    def test_18_all_296_errata_remain_v2(self):
        self.assertEqual(296, len(self.repo.errata))
        self.assertTrue(all(isinstance(e, ErratumV2) for e in self.repo.errata.values()))

    def test_19_tengu_snapshot_erratum_audit(self):
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

    def test_20_exact_52_historical_substitutions_match_approved_mapping(self):
        overrides = select_applicable_errata(self.fmt, self.repo)
        actual_mapping = {
            override.erratum.id: (modern_passcode, override.implementation.historical_passcode)
            for modern_passcode, override in overrides.items()
        }
        self.assertEqual(EXPECTED_EDISON_STYLE_FALLBACK, actual_mapping)
        self.assertEqual(52, len(actual_mapping))

    def test_21_no_unexpected_extra_substitutions(self):
        overrides = select_applicable_errata(self.fmt, self.repo)
        self.assertEqual(set(EXPECTED_EDISON_STYLE_FALLBACK.keys()), {o.erratum.id for o in overrides.values()})

    def test_22_nine_ambiguous_modern_impossible_are_known_wrong_fallbacks(self):
        snapshot = _dt.date(2011, 9, 17)
        known_wrong = []
        for e in self.repo.errata.values():
            if not e.has_implementation_relevant_history():
                continue
            sel = e.selection_at(snapshot)
            if sel.chronology == "ambiguous" and not sel.modern_is_possible:
                known_wrong.append(e.modern_card.name)
        expected_known_wrong = {
            "Axe of Despair",
            "Paladin of White Dragon",
            "Sangan",
            "Tyrant Dragon",
            "Vampire Lord",
            "Witch of the Black Forest",
            "XY-Dragon Cannon",
            "XYZ-Dragon Cannon",
            "XZ-Tank Cannon",
        }
        self.assertEqual(expected_known_wrong, set(known_wrong))
        self.assertEqual(9, len(known_wrong))

    def test_23_ambiguous_modern_possible_records_use_documented_unresolved_policy(self):
        self.assertIsNotNone(self.fmt.unresolved_policy)
        self.assertEqual("modern", self.fmt.unresolved_policy.get("choice"))

    def test_24_determinate_known_gap_states_remain_acknowledged_divergences(self):
        snapshot = _dt.date(2011, 9, 17)
        divergences = []
        for e in self.repo.errata.values():
            if not e.has_implementation_relevant_history():
                continue
            sel = e.selection_at(snapshot)
            if sel.chronology == "determinate" and sel.candidates[0].coverage.kind == Coverage.KNOWN_GAP:
                divergences.append(e.modern_card.name)
        self.assertEqual(38, len(divergences))

    def test_25_generated_tengu_lflist_contains_every_legal_card_correctly(self):
        built = build_lflist(self.fmt, self.repo)
        self.assertIn("$whitelist", built.text)
        pool = self.repo.pools["pool-tengu-2011"]
        banlist = self.repo.banlists["tcg-2011-09"]
        status_by_code = {e.card.passcode: e.status for e in banlist.entries}
        # Mirrors lflist.py's own region_substitution_origin bridge: a
        # region-substituted pool card's status is looked up under the
        # passcode the banlist was transcribed against, not its own.
        region_substitution_origin = {
            int(sub["to"]["passcode"]): int(sub["from"]["passcode"])
            for sub in (pool.cutoff or {}).get("region_substitutions", [])
        }
        overrides = select_applicable_errata(self.fmt, self.repo)

        expected_codes: dict[int, int] = {}
        counts = {"forbidden": 0, "limited": 1, "semilimited": 2}
        for card in pool.cards:
            status = status_by_code.get(card.passcode)
            if status is None and card.passcode in region_substitution_origin:
                status = status_by_code.get(region_substitution_origin[card.passcode])
            count = counts.get(status or "", 3)
            override = overrides.get(card.passcode)
            if override is not None:
                passcode, variants = historical_identity(override.implementation)
                codes = [passcode, *variants]
            else:
                codes = [card.passcode, *card.variants]
            for code in codes:
                expected_codes[code] = count

        self.assertEqual(expected_codes, built.entries)
        self.assertEqual(4564, len(built.entries))

    def test_26_historical_identity_transfer_and_no_duplicate_playable_copies(self):
        built = build_lflist(self.fmt, self.repo)
        overrides = select_applicable_errata(self.fmt, self.repo)
        banlist = self.repo.banlists["tcg-2011-09"]
        status_by_code = {e.card.passcode: e.status for e in banlist.entries}

        for modern_code, override in overrides.items():
            hist_code, variants = historical_identity(override.implementation)
            # Modern passcode must NOT be in whitelist
            self.assertNotIn(
                modern_code,
                built.entries,
                f"Modern passcode {modern_code} must not appear when historical {hist_code} is substituted",
            )
            # Historical passcode must appear at the exact status count
            expected_count = {"forbidden": 0, "limited": 1, "semilimited": 2}.get(
                status_by_code.get(modern_code, ""), 3
            )
            self.assertEqual(
                expected_count,
                built.entries[hist_code],
                f"Historical {hist_code} must receive count {expected_count}",
            )

        # Specific restricted cards checks:
        # Chaos Emperor Dragon (82301904 -> 511000819): forbidden -> 0
        self.assertNotIn(82301904, built.entries)
        self.assertEqual(0, built.entries[511000819])

        # Brionac (50321796 -> 511002993): limited -> 1
        self.assertNotIn(50321796, built.entries)
        self.assertEqual(1, built.entries[511002993])

        # Future Fusion (77565204 -> 511002997): limited -> 1
        self.assertNotIn(77565204, built.entries)
        self.assertEqual(1, built.entries[511002997])

        # Red-Eyes Darkness Metal Dragon (88264978 -> 88264988): unlimited in pool -> 3
        self.assertNotIn(88264978, built.entries)
        self.assertEqual(3, built.entries[88264988])

    def test_27_generated_output_is_deterministic(self):
        built1 = build_lflist(self.fmt, self.repo)
        built2 = build_lflist(self.fmt, self.repo)
        self.assertEqual(built1.text, built2.text)
        self.assertEqual(built1.hash, built2.hash)

    def test_28_generated_output_hash_is_pinned(self):
        built = build_lflist(self.fmt, self.repo)
        self.assertEqual(TENGU_HASH, built.hash)
        self.assertEqual(TENGU_HASH, lflist_hash(built.entries))

    def test_29_goat_output_remains_byte_identical_and_hash_pinned(self):
        goat_fmt = self.repo.formats["2005-04-goat"]
        built_goat = build_lflist(goat_fmt, self.repo)
        self.assertEqual(GOAT_HASH, built_goat.hash)
        self.assertEqual(1700, len(self.repo.pools["pool-goat-2005-ignis"].cards))

    def test_30_edison_output_remains_byte_identical_and_pool_cardinality_pinned(self):
        # Hash pinned 2026-08-31: Mind Master's pool passcode moved
        # 96782886 -> 96782896 (region_substitutions, roadmap 1e); pool
        # cardinality is unaffected (substitution, not add/remove).
        edison_fmt = self.repo.formats["2010-03-edison"]
        built_edison = build_lflist(edison_fmt, self.repo)
        self.assertEqual(0x34088AB6, built_edison.hash)
        self.assertEqual(EDISON_POOL_COUNT, len(self.repo.pools["pool-edison-2010"].cards))


if __name__ == "__main__":
    unittest.main()
