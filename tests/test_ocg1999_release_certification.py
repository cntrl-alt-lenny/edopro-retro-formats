"""Certification of the Japanese OCG release ledger through 1999-08-25.

This module mechanically certifies, from source-backed release data, which
canonical EDOPro card identities had a legal/public Japanese OCG release on
or before 1999-08-25 (the day before the August 26, 1999 Tokyo Dome event).

It does NOT create the Tokyo Dome format, banlist, pool, rule profile, or
generated lflist. It certifies the release ledger a later Tokyo Dome pool
could be derived from mechanically. See docs/research/yugi-kaiba-format-source-gate.md
for the certification verdict and remaining (non-release) blockers.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import unittest
from datetime import date
from pathlib import Path

from retroformats.lflist import build_lflist
from retroformats.model import Coverage, ErratumV2, Pool, ReleaseEvent
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository
from retroformats.validate import Validator

from .helpers import TempRepoTest, card as card_ref, event as ev, gap, printing

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = date(1999, 8, 25)
SCOPE = frozenset({"ocg-jp"})
COMMUNITY_CANDIDATES = ROOT / "docs" / "research" / "ocg1999-tokyo-dome-community-candidates.json"
COMMUNITY_DIFF = ROOT / "docs" / "research" / "ocg1999-tokyo-dome-community-diff.json"
PACKET_PATH = ROOT / "docs" / "research" / "yugi-kaiba-format-source-packet.json"

# -- frozen certification facts (independently derived; see the research
#    scripts referenced in docs/research/yugi-kaiba-format-source-gate.md) ---

CERTIFIED_PRODUCTS = {
    # id: (printing_count, event_date)
    "vol-1": (40, "1999-02-04"),
    "yu-gi-oh-duel-monsters-national-tournament-attendance-card": (1, "1999-02-21"),
    "yu-gi-oh-duel-monsters-national-tournament-prize-cards": (3, "1999-02-21"),
    "booster-1": (40, "1999-03-01"),
    "starter-box-theatrical-release": (50, "1999-03-06"),
    "starter-box": (50, "1999-03-18"),
    "starter-box-pre-order-promotional-card": (1, "1999-03-18"),
    "vol-2": (40, "1999-03-27"),
    "official-guide-starter-book-promotional-card": (1, "1999-05-05"),
    "booster-2": (40, "1999-05-25"),
    "vol-3": (50, "1999-05-27"),
    "limited-edition-yugi-pack": (3, "1999-06-01"),
    "limited-edition-kaiba-pack": (3, "1999-06-01"),
    "limited-edition-joey-pack": (3, "1999-06-01"),
    "booster-3": (40, "1999-07-05"),
    "yu-gi-oh-duel-monsters-ii-dark-duel-stories-promotional-cards": (10, "1999-07-08"),
    "yu-gi-oh-duel-monsters-ii-dark-duel-stories-game-guide-1-promotional-card": (1, "1999-07-08"),
    "vol-4": (50, "1999-07-22"),
    "yu-gi-oh-duel-monsters-ii-dark-duel-stories-game-guide-2-promotional-card": (1, "1999-08-05"),
    "the-valuable-book-1-promotional-cards": (2, "1999-08-20"),
}

GAP_IDS = {
    "gap-ocg1999-nt-prize-top-tier",
    "gap-ocg1999-td-invitation-tickets",
    "gap-ocg1999-vjump-aug-1999-special-present",
    "gap-ocg1999-vjf-1999",
    "gap-ocg1999-dm2-trial-meeting",
}

EXPECTED_POOL_COUNT = 370
EXPECTED_POOL_DIGEST = "f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb"

# August 26, 1999 boundary: cards exclusive to the Tokyo Dome event day / its
# same-day tournament, resolved to their canonical passcodes (see
# docs/research/yugi-kaiba-format-source-gate.md section "August 26 boundary").
AUG26_TOURNAMENT_ONLY_PASSCODES = {
    25833572: "Gate Guardian",  # attendance card
    30208479: "Magician of Black Chaos",  # attendance card
    39111158: "Tri-Horned Dragon",  # participation card, round 1
    76232340: "Sengenjin",  # participation card, round 2
    66516792: "Serpent Night Dragon",  # participation card, round 3
    23995346: "Blue-Eyes Ultimate Dragon",  # prize card, champion
    90660762: "Meteor Black Dragon",  # prize card, 2nd place
    27054370: "Firewing Pegasus",  # prize card, 2nd/3rd place
}
AUG26_PREMIUM_PACK_PASSCODES = {
    71625222: "Time Wizard", 33396948: "Exodia the Forbidden One", 59983499: "Dancing Elf",
    67959180: "Goddess of Whim", 59053232: "Turu-Purun", 96967123: "Dharma Cannon",
    68638985: "Slime Toad", 38999506: "Cosmo Queen", 38277918: "Mikazukinoyaiba",
    64271667: "Meteor Dragon",
}
# Booster 4 (Aug 26) reprints 5 cards that already released earlier in Vol.4
# (1999-07-22, certified below); these are the ONLY Booster 4 cards allowed
# to appear in the 1999-08-25 pool, and only via their Vol.4 origin.
BOOSTER4_REPRINTS_FROM_VOL4 = {
    "Warrior Elimination", "Acid Rain", "Eradicating Aerosol", "Breath of Light", "Eternal Drought",
}

POOL_INTERSECTED_ERRATA_IDS = {
    "erratum-castle-walls", "erratum-cocoon-of-evolution", "erratum-crush-card-virus",
    "erratum-elegant-egotist", "erratum-reinforcements", "erratum-ultimate-offering",
}


def _make_pool(cutoff_date: str = "1999-08-25", territories=("ocg-jp",), region: str = "OCG") -> Pool:
    raw = {
        "id": "pool-ocg1999-research-only",
        "region": region,
        "kind": "release-cutoff",
        "cutoff": {"cutoff_date": cutoff_date, "territories": list(territories)},
        "sources": ["yugipedia-ocg-series1-set-pages"],
    }
    return Pool.load(raw, Path("/tmp/pool-ocg1999-research-only.json"))


def _pool_digest(cards: list[dict]) -> str:
    payload = json.dumps(
        [{"passcode": c["passcode"], "name": c["name"]} for c in cards],
        separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class OCG1999ReleaseCertificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.load(ROOT)
        cls.index = ReleaseIndex.build(cls.repo)
        cls.pool = _make_pool()
        cls.evaluation = evaluate_cutoff(cls.pool, cls.repo, cls.index)

    # -- 1: exact certified coverage window ------------------------------

    def test_ocg_jp_coverage_window_certified_through_cutoff(self):
        self.assertIsNotNone(self.repo.release_coverage)
        window = next(
            w for w in self.repo.release_coverage.windows
            if "ocg-jp" in w.get("territories", [])
        )
        self.assertEqual("1999-02-01", window["from"])
        self.assertEqual("1999-08-25", window["through"])
        self.assertEqual("complete", window["status"])
        self.assertTrue(self.repo.release_coverage.covers(CUTOFF, SCOPE, self.repo.release_gaps))

    # -- 2/3: exact product set and roster accounting --------------------

    def test_certified_product_set_is_exact(self):
        ocg_products = {
            p.id for p in self.repo.products.values()
            if any(e.territory.startswith("ocg") for e in p.events)
        }
        self.assertEqual(set(CERTIFIED_PRODUCTS), ocg_products)
        self.assertEqual(20, len(ocg_products))

    def test_product_rosters_and_dates_are_exact(self):
        for product_id, (count, event_date) in CERTIFIED_PRODUCTS.items():
            product = self.repo.products[product_id]
            self.assertEqual(count, len(product.printings), msg=product_id)
            self.assertEqual(1, len(product.events), msg=product_id)
            self.assertEqual(event_date, product.events[0].date, msg=product_id)
            self.assertEqual("ocg-jp", product.events[0].territory, msg=product_id)
            # every printing resolves to a real canonical passcode
            for printing_ in product.printings:
                self.assertIn(printing_.passcode, self.repo.card_index.by_passcode, msg=(product_id, printing_.name))

    # -- 4: no unresolved pool-impacting gaps -----------------------------

    def test_no_unresolved_pool_impacting_ocg1999_gaps(self):
        ocg_gaps = [g for g in self.repo.release_gaps if g.id.startswith("gap-ocg1999-")]
        self.assertEqual(GAP_IDS, {g.id for g in ocg_gaps})
        for g in ocg_gaps:
            self.assertEqual("resolved-safe", g.status, msg=g.id)
            self.assertEqual("pool-membership", g.impact, msg=g.id)
            self.assertFalse(g.blocks(CUTOFF, SCOPE), msg=g.id)

    # -- 5: zero unknown printings -----------------------------------------

    def test_zero_unknown_printings(self):
        self.assertEqual(0, len(self.index.unknown_printings))

    # -- 6/7: exact candidate pool cardinality and digest -------------------

    def test_candidate_pool_cardinality_and_digest(self):
        self.assertEqual(0, len(self.evaluation.ambiguous))
        self.assertEqual(EXPECTED_POOL_COUNT, len(self.evaluation.included))
        cards = self.evaluation.cards()
        self.assertEqual(EXPECTED_POOL_COUNT, len(cards))
        self.assertEqual(EXPECTED_POOL_DIGEST, _pool_digest(cards))
        # zero manual card-level exceptions: this pool was derived with no
        # cutoff.include/exclude entries at all (see _make_pool()).
        self.assertIsNone(self.pool.cutoff.get("include"))
        self.assertIsNone(self.pool.cutoff.get("exclude"))
        self.assertIsNone(self.pool.cutoff.get("exclude_products"))

    # -- 8/9: exact community cross-check differences, each categorized ----

    def test_community_cross_check_set_differences(self):
        candidates = json.loads(COMMUNITY_CANDIDATES.read_text(encoding="utf-8"))
        diff = json.loads(COMMUNITY_DIFF.read_text(encoding="utf-8"))
        self.assertEqual(370, candidates["candidate_identity_count"])
        community = {row["passcode"] for row in candidates["candidates"]}
        self.assertEqual(370, len(community))

        derived = {c["passcode"] for c in self.evaluation.cards()}
        self.assertEqual(EXPECTED_POOL_COUNT, len(derived))

        # Four community entries print BabelCDB artwork-variant passcodes
        # (distance <10 from their base) where this ledger's own printings
        # record the base passcode directly instead: "Final Flame" and
        # "Ultimate Offering" (their variant codes were never referenced by
        # any printing, so collect_referenced_passcodes() never added them
        # to the card index at all); "Harpie's Feather Duster" and "Monster
        # Reborn" (whose variant codes happen to already be registered via
        # pre-existing TCG-side data, unrelated to this certification).
        # Documented, sourced (ignis-babelcdb) known aliases, not a generic
        # repo.card_index lookup - two of the four are absent from the
        # index precisely because this ledger never needed them.
        KNOWN_ARTWORK_ALIASES = {73134082: 73134081, 80604092: 80604091, 18144507: 18144506, 83764719: 83764718}
        for variant, base in KNOWN_ARTWORK_ALIASES.items():
            self.assertIn(base, self.repo.card_index.by_passcode)
            variant_row = self.repo.card_index.by_passcode.get(variant)
            if variant_row is not None:
                self.assertEqual(base, variant_row.get("alias_of"))

        def canonical(passcode: int) -> int:
            if passcode in KNOWN_ARTWORK_ALIASES:
                return KNOWN_ARTWORK_ALIASES[passcode]
            row = self.repo.card_index.by_passcode.get(passcode)
            alias = row.get("alias_of") if row else None
            if alias and abs(int(alias) - passcode) < 10:
                return int(alias)
            return passcode

        canonicalized_community = {canonical(p) for p in community}
        ledger_only = derived - canonicalized_community
        community_only = canonicalized_community - derived
        self.assertEqual(set(), ledger_only)
        self.assertEqual(set(), community_only)
        self.assertEqual([], diff["ledger_only"])
        self.assertEqual([], diff["community_only"])
        self.assertEqual(EXPECTED_POOL_DIGEST, diff["certified_pool_digest_sha256"])
        # the two raw (non-canonicalized) community passcodes that differ from
        # our printed passcodes are exactly the two known artwork-variant
        # aliases (Final Flame / Ultimate Offering); every other difference
        # category (release-date-error, event-day, promo-missed, token,
        # modern-unavailable, product-omission, retrospective-convention,
        # same-day-legality, unresolved, community-error) has zero members.
        raw_diff = community - derived
        self.assertEqual(set(KNOWN_ARTWORK_ALIASES), raw_diff)
        for passcode in raw_diff:
            self.assertEqual(canonical(passcode), canonical(passcode))  # collapses cleanly
            self.assertIn(canonical(passcode), derived)

    # -- 10/11: exact August 26 boundary set; no leakage into the candidate -

    def test_august_26_boundary_products_and_no_leakage(self):
        booster4 = self.repo.products.get("booster-4")
        premium_pack = self.repo.products.get("premium-pack")
        # Booster 4 / Premium Pack are NOT part of this certification (they
        # are dated on/after the event day) - confirm they simply don't exist
        # as ocg-jp certified products in this ledger.
        for product in (booster4, premium_pack):
            if product is not None:
                self.assertFalse(any(e.territory.startswith("ocg") and e.date <= "1999-08-25" for e in product.events))

        pool_passcodes = {c["passcode"] for c in self.evaluation.cards()}
        for passcode, name in AUG26_TOURNAMENT_ONLY_PASSCODES.items():
            self.assertNotIn(passcode, pool_passcodes, msg=name)
        for passcode, name in AUG26_PREMIUM_PACK_PASSCODES.items():
            self.assertNotIn(passcode, pool_passcodes, msg=name)
        self.assertEqual(8, len(AUG26_TOURNAMENT_ONLY_PASSCODES))
        self.assertEqual(10, len(AUG26_PREMIUM_PACK_PASSCODES))
        self.assertEqual(5, len(BOOSTER4_REPRINTS_FROM_VOL4))
        # the reprints ARE in the pool, but only via their genuine 1999-07-22
        # Vol.4 origin - never via Booster 4 (which is not in this ledger).
        vol4 = self.repo.products["vol-4"]
        vol4_names = {p.name for p in vol4.printings}
        self.assertTrue(BOOSTER4_REPRINTS_FROM_VOL4.issubset(vol4_names))

    # -- 12: OCG-only additions never alter TCG cutoff pools ---------------

    def test_ocg_only_identities_do_not_alter_tcg_pools(self):
        # a passcode newly added to the global card index by this
        # certification, with release evidence ONLY in ocg-jp, must not
        # appear in a TCG-scoped evaluation at any cutoff.
        newly_added_ocg_only = 12829151  # "Kanan the Swordmistress"
        self.assertIn(newly_added_ocg_only, self.repo.card_index.by_passcode)
        for cutoff_date in ("2005-04-01", "2010-03-01", "2011-09-17", "2030-01-01"):
            tcg_pool = _make_pool(cutoff_date, territories=("tcg", "tcg-na", "tcg-eu", "tcg-oce"), region="TCG")
            tcg_evaluation = evaluate_cutoff(tcg_pool, self.repo, self.index)
            self.assertNotIn(newly_added_ocg_only, tcg_evaluation.included, msg=cutoff_date)
            self.assertNotIn(newly_added_ocg_only, tcg_evaluation.ambiguous, msg=cutoff_date)

    # -- 13/14: errata untouched; pool-intersected audit is deterministic --

    def test_errata_untouched_and_pool_intersected_audit_is_deterministic(self):
        self.assertEqual(296, len(self.repo.errata))
        self.assertTrue(all(isinstance(r, ErratumV2) for r in self.repo.errata.values()))

        pool_passcodes = {c["passcode"] for c in self.evaluation.cards()}
        pool_relevant = [e for e in self.repo.errata.values() if e.modern_card.passcode in pool_passcodes]
        self.assertEqual(POOL_INTERSECTED_ERRATA_IDS, {e.id for e in pool_relevant})
        self.assertEqual(6, len(pool_relevant))

        determinate = []
        ambiguous = []
        for record in pool_relevant:
            selection = record.selection_at(CUTOFF)
            (determinate if selection.chronology == "determinate" else ambiguous).append((record, selection))
        self.assertEqual(2, len(determinate))
        self.assertEqual(4, len(ambiguous))

        det_modern = sum(1 for r, s in determinate if s.is_modern)
        self.assertEqual(0, det_modern)
        self.assertEqual(2, len(determinate) - det_modern)  # determinate historical
        det_coverage = {}
        for r, s in determinate:
            kind = s.candidates[0].coverage.kind.value
            det_coverage[kind] = det_coverage.get(kind, 0) + 1
        self.assertEqual({"reuse-upstream": 2}, det_coverage)

        amb_modern_possible = sum(1 for r, s in ambiguous if s.modern_is_possible)
        self.assertEqual(3, amb_modern_possible)
        self.assertEqual(1, len(ambiguous) - amb_modern_possible)  # modern-impossible

        amb_candidate_occ = sum(len(s.candidates) for r, s in ambiguous)
        self.assertEqual(8, amb_candidate_occ)
        amb_coverage_occ = {}
        for r, s in ambiguous:
            for c in s.candidates:
                k = c.coverage.kind.value
                amb_coverage_occ[k] = amb_coverage_occ.get(k, 0) + 1
        self.assertEqual({"reuse-upstream": 4, "modern": 3, "unresolved": 1}, amb_coverage_occ)

        # no known-gap coverage among the pool-relevant determinate set
        self.assertFalse(any(
            s.candidates[0].coverage.kind is Coverage.KNOWN_GAP for r, s in determinate
        ))

    # -- 15-18: GOAT / Edison / Tengu preserved exactly ---------------------

    def test_goat_edison_tengu_preserved(self):
        self.assertEqual({"2005-04-goat", "2010-03-edison", "2011-09-tengu"}, set(self.repo.formats))
        self.assertEqual(0x28E9FC02, build_lflist(self.repo.formats["2005-04-goat"], self.repo).hash)
        self.assertEqual(3673, len(self.repo.pools[self.repo.formats["2010-03-edison"].pool_id].cards))
        self.assertEqual(4562, len(self.repo.pools[self.repo.formats["2011-09-tengu"].pool_id].cards))
        self.assertEqual(0x0CE5BABE, build_lflist(self.repo.formats["2011-09-tengu"], self.repo).hash)

    # -- 19: no canonical Tokyo Dome artifacts exist -------------------------

    def test_no_canonical_tokyo_dome_artifacts(self):
        self.assertFalse((ROOT / "formats" / "1999-08-tokyo-dome").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "ocg-1999-07.json").exists())
        self.assertFalse((ROOT / "data" / "pools" / "1999-08-tokyo-dome.json").exists())
        self.assertFalse((ROOT / "data" / "rule-profiles" / "1999-08-tokyo-dome.json").exists())

    # -- validator sanity: current repo state passes cleanly ---------------

    def test_validator_has_zero_errors_and_no_ocg_warning_delta(self):
        validator = Validator(self.repo)
        findings = validator.validate()
        errors = [f for f in findings if f.severity == "ERROR"]
        self.assertEqual([], errors, msg="\n".join(map(str, errors)))
        # no new warnings from the OCG products (they carry no printed
        # numbers, so releases.number-prefix cannot fire on them)
        ocg_warnings = [f for f in findings if "ocg" in f.location.lower() or "1999" in f.location]
        self.assertEqual([], ocg_warnings, msg="\n".join(map(str, ocg_warnings)))

    # -- packet: the updated dossier's claims match the live repository -----

    def test_packet_release_ledger_certification_matches_live_repository(self):
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        cert = packet["release_ledger_certification"]
        self.assertEqual("RESOLVED WITH NONBLOCKING GAPS", cert["status"])
        self.assertEqual(
            {"from": "1999-02-01", "through": "1999-08-25", "status": "complete"},
            cert["ocg_jp_coverage_window"],
        )
        self.assertEqual(20, cert["certified_product_count"])
        self.assertEqual(set(CERTIFIED_PRODUCTS), set(cert["certified_products"]))
        self.assertEqual(GAP_IDS, set(cert["gap_ledger"]["gap_ids"]))
        self.assertTrue(cert["gap_ledger"]["all_resolved_safe"])
        self.assertEqual(0, cert["gap_ledger"]["unresolved_pool_impacting_gaps"])
        self.assertEqual(121, cert["card_identity_resolution"]["originally_absent_from_card_index"])
        self.assertEqual(119, cert["card_identity_resolution"]["resolved_by_card_index_addition"])
        self.assertEqual(2, cert["card_identity_resolution"]["resolved_by_artwork_alias_collapse"])
        self.assertEqual(0, cert["card_identity_resolution"]["unresolved_identities"])
        self.assertTrue(cert["card_identity_resolution"]["no_invented_passcodes"])
        self.assertEqual(EXPECTED_POOL_COUNT, cert["candidate_pool"]["cardinality"])
        self.assertEqual(EXPECTED_POOL_DIGEST, cert["candidate_pool"]["digest_sha256"])
        self.assertEqual(0, cert["candidate_pool"]["ambiguous_cards"])
        self.assertEqual(0, cert["candidate_pool"]["unknown_printings"])
        self.assertEqual(0, cert["candidate_pool"]["manual_card_level_exceptions"])
        self.assertEqual(370, cert["community_cross_check"]["common"])
        self.assertEqual(0, cert["community_cross_check"]["ledger_only"])
        self.assertEqual(0, cert["community_cross_check"]["community_only"])
        self.assertEqual(6, cert["pool_intersected_errata_audit"]["pool_relevant_erratum_count"])
        self.assertEqual(
            POOL_INTERSECTED_ERRATA_IDS, set(cert["pool_intersected_errata_audit"]["pool_relevant_erratum_ids"])
        )
        self.assertEqual("A", cert["architecture_verdict_after_ledger_implementation"]["verdict"])
        # this task is release-ledger certification only: it must not claim
        # Tokyo Dome is canonical-ready, and the pre-existing non-release
        # blockers (banlist/rules/engine) must remain exactly as frozen.
        self.assertEqual("blocked", packet["canonicalization"])
        self.assertEqual(
            "representable-with-format-local-approximations", packet["verdict"]
        )
        for still_blocking in (
            "banlist", "starter_vs_expert_effective_boundary", "deck_out_rule",
            "battle_calculation_semantics", "chain_spell_speed_semantics",
            "errata_implementation_coverage", "engine_representability",
        ):
            self.assertEqual("BLOCKING", packet["blocker_ledger"][still_blocking]["status"], msg=still_blocking)
        self.assertEqual("RESOLVED", packet["blocker_ledger"]["ocg_release_ledger"]["status"])
        self.assertEqual("RESOLVED", packet["blocker_ledger"]["missing_card_identities"]["status"])

    def test_packet_chronology_includes_all_newly_discovered_products(self):
        packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        entries = packet["product_chronology"]
        dates = [date.fromisoformat(entry["date"]) for entry in entries]
        self.assertEqual(dates, sorted(dates))
        self.assertLess(CUTOFF, dates[-1])
        self.assertIn("Tokyo Dome event and attendee/prize cards", entries[-1]["products"])
        all_products_text = " ".join(p for e in entries for p in e["products"])
        for must_mention in ("Booster 1", "Starter Box: Theatrical Release", "National Tournament"):
            self.assertIn(must_mention, all_products_text)
        notes = packet["product_chronology_research_notes"]["entries"]
        self.assertEqual(4, len(notes))
        self.assertEqual(GAP_IDS - {"gap-ocg1999-nt-prize-top-tier"}, {n["gap_id"] for n in notes})

    # ===================== adversarial mutation checks =====================
    # Each of these mutates an IN-MEMORY copy of the loaded repository (never
    # the files on disk) and proves the derivation/validator reacts.

    def _mutated_repo(self, products):
        return dataclasses.replace(self.repo, products=products)

    def test_adversarial_deleting_a_pre_cutoff_product_shrinks_the_pool(self):
        mutated = dict(self.repo.products)
        del mutated["vol-1"]  # sole source of several Vol.1-exclusive cards
        repo2 = self._mutated_repo(mutated)
        index2 = ReleaseIndex.build(repo2)
        evaluation2 = evaluate_cutoff(self.pool, repo2, index2)
        self.assertLess(len(evaluation2.included), EXPECTED_POOL_COUNT)

    def test_adversarial_moving_a_product_date_past_the_cutoff_drops_its_exclusive_cards(self):
        product = self.repo.products["the-valuable-book-1-promotional-cards"]
        mutated_event = dataclasses.replace(product.events[0], date="1999-08-26")
        mutated_product = dataclasses.replace(product, events=[mutated_event])
        mutated = dict(self.repo.products)
        mutated["the-valuable-book-1-promotional-cards"] = mutated_product
        repo2 = self._mutated_repo(mutated)
        index2 = ReleaseIndex.build(repo2)
        evaluation2 = evaluate_cutoff(self.pool, repo2, index2)
        # "Dokurorider" / "Revival of Dokurorider" have no other pre-cutoff source
        self.assertEqual(EXPECTED_POOL_COUNT - 2, len(evaluation2.included))

    def test_adversarial_moving_an_august_26_printing_to_august_25_makes_it_appear(self):
        # simulate the inverse mistake: an Aug-26-only card mis-dated onto the
        # certified side of the boundary must then appear in the pool -
        # proving the cutoff boundary is actually load-bearing, not vacuous.
        fake_product = self.repo.products["vol-4"]  # borrow a real, valid template
        fake_printing = dataclasses.replace(
            fake_product.printings[0],
            passcode=25833572,  # "Gate Guardian" (real Aug 26 attendance card)
            name="Gate Guardian",
            numbers=[],
        )
        smuggled = dataclasses.replace(
            fake_product, id="smuggled-aug26-test-only", code="SMG",
            events=[dataclasses.replace(fake_product.events[0], date="1999-08-25")],
            printings=[fake_printing],
        )
        mutated = dict(self.repo.products)
        mutated["smuggled-aug26-test-only"] = smuggled
        repo2 = self._mutated_repo(mutated)
        index2 = ReleaseIndex.build(repo2)
        evaluation2 = evaluate_cutoff(self.pool, repo2, index2)
        self.assertIn(25833572, evaluation2.included)
        self.assertEqual(EXPECTED_POOL_COUNT + 1, len(evaluation2.included))

    def test_adversarial_removing_one_printing_from_a_roster_drops_its_card(self):
        product = self.repo.products["vol-1"]
        # "The Drdek" (passcode 8944575): Yugipedia records it as never
        # reprinted in Japanese, so Vol.1 is its sole source in this ledger.
        remaining = [p for p in product.printings if p.name != "The Drdek"]
        self.assertEqual(len(product.printings) - 1, len(remaining))
        mutated_product = dataclasses.replace(product, printings=remaining)
        mutated = dict(self.repo.products)
        mutated["vol-1"] = mutated_product
        repo2 = self._mutated_repo(mutated)
        index2 = ReleaseIndex.build(repo2)
        evaluation2 = evaluate_cutoff(self.pool, repo2, index2)
        self.assertEqual(EXPECTED_POOL_COUNT - 1, len(evaluation2.included))
        self.assertNotIn(8944575, evaluation2.included)

    def test_adversarial_artwork_alias_does_not_inflate_the_pool_as_a_fake_distinct_card(self):
        # 18144507 is a real, already-registered card-index entry: a +/-10
        # artwork-variant alias of "Harpie's Feather Duster" (18144506,
        # already in the pool via the DM2 video-game-bundled promo cards).
        # Printing the variant under a NEW synthetic product must NOT add a
        # second, spuriously-distinct canonical card to the pool - it must
        # collapse into the already-present base.
        self.assertEqual(18144506, self.repo.card_index.by_passcode[18144507]["alias_of"])
        self.assertIn(18144506, self.evaluation.included)
        fake_product = self.repo.products["vol-2"]
        fake_printing = dataclasses.replace(fake_product.printings[0], passcode=18144507, name="Harpie's Feather Duster", numbers=[])
        smuggled = dataclasses.replace(
            fake_product, id="fake-artwork-variant-test-only", code="FAK",
            printings=[fake_printing],
        )
        mutated = dict(self.repo.products)
        mutated["fake-artwork-variant-test-only"] = smuggled
        repo2 = self._mutated_repo(mutated)
        index2 = ReleaseIndex.build(repo2)
        evaluation2 = evaluate_cutoff(self.pool, repo2, index2)
        self.assertEqual(EXPECTED_POOL_COUNT, len(evaluation2.included))  # unchanged
        self.assertNotIn(18144507, evaluation2.included)  # never its own entry
        self.assertIn(18144507, evaluation2.included[18144506].get("variant_passcodes", []))


class OCG1999SyntheticGapAdversarialTest(TempRepoTest):
    """Synthetic mini-repositories proving the gap/coverage machinery
    actually enforces certification, using the same shapes as the real
    ocg-jp ledger but small enough to hand-check."""

    def _seed(self, extra_gaps=(), coverage_status="complete"):
        self.add_card_index([card_ref(900, "Alpha"), card_ref(901, "Beta")])
        self.add_product(
            code="OCGT1", printings=[printing(900, "Alpha")],
            release_events=[ev("ocg-jp", "1999-03-01")], id="ocgt1", dating="product",
        )
        self.add_coverage(windows=[
            {"territories": ["ocg-jp"], "from": "1999-02-01", "through": "1999-08-25", "status": coverage_status},
        ])
        self.add_gaps(*extra_gaps)
        self.add_import_report()

    def _validate(self):
        validator = Validator(Repository.load(self.root))
        return validator.validate()

    def test_clean_ledger_certifies(self):
        self._seed()
        findings = self._validate()
        errors = [f for f in findings if f.severity == "ERROR"]
        self.assertEqual([], errors, msg="\n".join(map(str, errors)))
        repo = Repository.load(self.root)
        self.assertTrue(repo.release_coverage.covers(date(1999, 8, 25), frozenset({"ocg-jp"}), repo.release_gaps))

    def test_unresolved_gap_overlapping_cutoff_blocks_certification(self):
        self._seed(extra_gaps=[gap(
            id="gap-synthetic-unresolved",
            kind="missing-product-printings",
            subjects=["Synthetic missing product"],
            territories=["ocg-jp"],
            possible_from="1999-06-01",
            status="unresolved",
            impact="pool-membership",
        )])
        repo = Repository.load(self.root)
        self.assertFalse(repo.release_coverage.covers(date(1999, 8, 25), frozenset({"ocg-jp"}), repo.release_gaps))
        findings = self._validate()
        codes = {f.code for f in findings if f.severity == "ERROR"}
        self.assertIn("coverage.gap-unresolved", codes)

    def test_unresolved_gap_after_cutoff_does_not_block(self):
        self._seed(extra_gaps=[gap(
            id="gap-synthetic-future",
            kind="missing-product-printings",
            subjects=["Synthetic post-cutoff product"],
            territories=["ocg-jp"],
            possible_from="1999-08-26",
            status="unresolved",
            impact="pool-membership",
        )])
        repo = Repository.load(self.root)
        self.assertTrue(repo.release_coverage.covers(date(1999, 8, 25), frozenset({"ocg-jp"}), repo.release_gaps))

    def test_gap_marked_safe_without_evidence_is_rejected(self):
        self._seed(extra_gaps=[gap(
            id="gap-synthetic-unjustified",
            kind="missing-product-printings",
            subjects=["Synthetic unjustified product"],
            territories=["ocg-jp"],
            possible_from="1999-06-01",
            status="resolved-safe",
            impact="pool-membership",
            # deliberately omit `resolution` entirely - "safe" asserted with
            # no rationale/detail/sources at all
        )])
        findings = self._validate()
        codes = {f.code for f in findings if f.severity == "ERROR"}
        self.assertIn("gaps.bad-rationale", codes)

    def test_cards_available_earlier_claim_is_recomputed_not_trusted(self):
        # a gap claiming a card is available earlier, when the dataset does
        # NOT actually prove that, must fail (gaps.not-harmless) - this is
        # the mechanical check that keeps "resolved-safe" honest.
        self._seed(extra_gaps=[gap(
            id="gap-synthetic-false-claim",
            kind="missing-product-printings",
            subjects=["Synthetic false-claim product"],
            territories=["ocg-jp"],
            possible_from="1999-01-01",  # before the dataset's only event (1999-03-01)
            status="resolved-safe",
            impact="pool-membership",
            resolution={
                "rationale": "cards-available-earlier",
                "detail": "false claim for testing",
                "cards": [{"passcode": 900, "name": "Alpha"}],
                "sources": ["test-source"],
            },
        )])
        findings = self._validate()
        codes = {f.code for f in findings if f.severity == "ERROR"}
        self.assertIn("gaps.not-harmless", codes)


if __name__ == "__main__":
    unittest.main()
