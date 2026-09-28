"""Engine tests for the historical cards this project generates itself
(roadmap item 7, rounds 029/030): Metalzoa and Super Vehicroid - Stealth Union
as they were in the Edison format (2010-04-24).

Every test runs one scenario against the real ocgcore, once with the modern
card (its cards.cdb code, the script Project Ignis ships) and once with this
repository's generated historical card (a reserved 6xxxxxxxx passcode, its
`dist/databases/retro-formats.cdb` row and `dist/scripts/c<passcode>.lua`), and
asserts the era difference the erratum record claims. The pairing is what makes
each test able to fail: a generated script that behaved like the modern card
would leave the two runs identical and the historical assertion would be red.

The scenarios that are NOT era differences ("control" tests) exist so the
generated script cannot pass merely by doing nothing: its summon procedure,
equip, battle and trigger paths are exercised too, next to the modern card
where a comparison is meaningful.

Prerequisites are those of tests/engine/harness.py (skips when the engine is
absent), plus a committed dist/ (this module reads it, exactly as a client
whose data_path/script_path point at dist/ would).
"""

from __future__ import annotations

import unittest

from . import harness as H
from .test_historical_behaviour import (
    DUEL_0_ATK_DESTROYED,
    DUEL_ATTACK_FIRST_TURN,
    DUEL_MODE_MR1,
    MILLENNIUM_SHIELD,
    scenario,
)

# Edison's host settings (dist/README.md): Master Rule 1 plus the 0-ATK rule.
DUEL_MODE_EDISON = DUEL_MODE_MR1 | DUEL_0_ATK_DESTROYED

MONSTER_REBORN = 83764718
GIANT_RAT = 97017120  # 1400 ATK / 1450 DEF, trigger when destroyed by battle

METALZOA_MODERN = 50705071
METALZOA_HISTORICAL = 600000001
ZOA = 24311372
METALMORPH = 68540058

STEALTH_UNION_MODERN = 3897065
STEALTH_UNION_HISTORICAL = 600000002

# The (modern, historical) pairs, for the identity test.
HISTORICAL_PAIRS = (
    ("Metalzoa", METALZOA_MODERN, METALZOA_HISTORICAL),
    ("Super Vehicroid - Stealth Union", STEALTH_UNION_MODERN, STEALTH_UNION_HISTORICAL),
    # Round 031: the cards shared with Tengu (tests/engine/test_shared_historical_scripts.py).
    ("Goddess of Whim", 67959180, 600000004),
    ("Strike Ninja", 41006930, 600000005),
    ("Green Baboon, Defender of the Forest", 46668237, 600000006),
    ("Rise of the Snake Deity", 16067089, 600000007),
    ("Malefic Blue-Eyes White Dragon", 9433350, 600000008),
    ("Soul Rope", 37383714, 600000009),
)


def deck_fillers(count: int = 3) -> str:
    """Draw-phase fodder for both players, so the duel never decks out."""
    out = ""
    for i in range(count):
        out += f"Debug.AddCard({MILLENNIUM_SHIELD},0,0,LOCATION_DECK,{i},POS_FACEDOWN_DEFENSE)\n"
        out += f"Debug.AddCard({MILLENNIUM_SHIELD},1,1,LOCATION_DECK,{i},POS_FACEDOWN_DEFENSE)\n"
    return out


def standing_answers(duel: H.Duel) -> None:
    duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
    duel.default_response(H.MSG_SELECT_PLACE, H.answer_place_first_free)
    duel.default_response(H.MSG_SELECT_POSITION, H.answer_position(H.POS_FACEUP_ATTACK))


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class GeneratedCardIdentityTest(unittest.TestCase):
    """The row the generator wrote aliases the modern card, so in a duel the
    historical card IS its modern card for every name and code check
    (docs/research/ignis-goat.md section 6), while it stays a distinct row
    with its own script."""

    def test_generated_rows_alias_the_modern_card_in_a_duel(self):
        for name, modern, historical in HISTORICAL_PAIRS:
            with self.subTest(card=name):
                setup = (
                    f"local c=Debug.AddCard({historical},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
                    f'Debug.Message("IDENT "..c:GetCode().." "..c:GetOriginalCode().." "..tostring(c:IsCode({modern})))\n'
                    + deck_fillers()
                )
                duel = scenario(DUEL_MODE_EDISON, setup)
                self.addCleanup(duel.close)
                lines = [text for _kind, text in duel.log if text.startswith("IDENT ")]
                self.assertEqual(
                    [f"IDENT {modern} {historical} true"],
                    lines,
                    "in a duel the historical row must resolve to the modern code (alias) "
                    "while keeping its own original code",
                )


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class MetalzoaEdisonTest(unittest.TestCase):
    """Era text (AST/TFK-002): "This monster can only be Special Summoned from
    your Deck to your side of the field by offering "Zoa" equipped with
    "Metalmorph" as a Tribute." Modern text: once properly Summoned it may be
    Special Summoned again (revived) from the Graveyard."""

    def _monster_reborn_candidates(self, metalzoa: int) -> list[int]:
        # Metalzoa is placed in the Graveyard already marked as properly
        # Summoned (Debug.AddCard's `proc` argument): the modern card's best
        # case for revival, and no shortcut for the historical one, which
        # allows no Special Summon outside its own procedure at all.
        setup = (
            f"Debug.AddCard({MONSTER_REBORN},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({metalzoa},0,0,LOCATION_GRAVE,0,POS_FACEUP,true)\n"
            f"Debug.AddCard({GIANT_RAT},0,0,LOCATION_GRAVE,1,POS_FACEUP)\n" + deck_fillers()
        )
        duel = scenario(DUEL_MODE_EDISON, setup)
        self.addCleanup(duel.close)
        offered: list[list[int]] = []

        def take_first(prompt):
            offered.append(H.card_candidates(prompt))
            return H.answer_cards(0)

        duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Monster Reborn
        duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
        duel.default_response(H.MSG_SELECT_CARD, take_first)
        standing_answers(duel)
        duel.run(turns=1)
        self.assertEqual(1, len(offered), "Monster Reborn must ask for exactly one target")
        return offered[0]

    def test_modern_metalzoa_can_be_revived_by_monster_reborn(self):
        self.assertIn(METALZOA_MODERN, self._monster_reborn_candidates(METALZOA_MODERN))

    def test_historical_metalzoa_cannot_be_revived_by_monster_reborn(self):
        candidates = self._monster_reborn_candidates(METALZOA_HISTORICAL)
        self.assertNotIn(METALZOA_HISTORICAL, candidates)
        self.assertEqual(
            [GIANT_RAT], candidates, "Monster Reborn still works: only Metalzoa is excluded"
        )

    def _procedure_run(self, code: int, equip_metalmorph: bool) -> tuple[list[dict], list[int]]:
        setup = f"Debug.AddCard({ZOA},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        # Metalmorph is a Trap that equips itself when it resolves, so it is
        # activated for real rather than attached with Debug.PreEquip (a Trap
        # placed that way is destroyed by the core as soon as the duel starts).
        setup += f"Debug.AddCard({METALMORPH},0,0,LOCATION_SZONE,0,POS_FACEDOWN)\n"
        setup += f"Debug.AddCard({code},0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)\n" + deck_fillers()
        duel = scenario(DUEL_MODE_EDISON, setup)
        self.addCleanup(duel.close)
        spsummonable: list[int] = []
        seen_first = []

        def idle(prompt):
            lists = H.idle_lists(prompt)
            spsummonable.extend(code_ for code_, _seq in lists["spsummonable"])
            if not seen_first:
                seen_first.append(True)
                if equip_metalmorph:
                    return H.answer_idle(5, 0)  # activate Metalmorph on Zoa
                return H.answer_idle(7)
            if lists["spsummonable"]:
                return H.answer_idle(1, 0)
            return H.answer_idle(7)

        duel.default_response(H.MSG_SELECT_IDLECMD, idle)
        duel.default_response(H.MSG_SELECT_CARD, H.answer_cards(0))
        standing_answers(duel)
        duel.run(turns=1)
        return duel.moves(), spsummonable

    def test_historical_procedure_summons_from_deck_by_tributing_the_equipped_zoa(self):
        moves, offered = self._procedure_run(METALZOA_HISTORICAL, equip_metalmorph=True)
        self.assertIn(METALZOA_HISTORICAL, offered)
        released = [m for m in moves if m["code"] == ZOA and m["to"]["location"] == H.LOCATION_GRAVE]
        self.assertTrue(released, "Zoa must be Tributed for the procedure")
        self.assertTrue(released[-1]["reason"] & 0x80, "Zoa leaves as a Release")
        summoned = [
            m
            for m in moves
            if m["code"] == METALZOA_HISTORICAL
            and m["from"]["location"] == H.LOCATION_DECK
            and m["to"]["location"] == H.LOCATION_MZONE
        ]
        self.assertEqual(1, len(summoned), "Metalzoa must be Special Summoned from the Deck")

    def test_historical_procedure_matches_the_modern_card_summoning_from_the_deck(self):
        modern_moves, _ = self._procedure_run(METALZOA_MODERN, equip_metalmorph=True)
        hist_moves, _ = self._procedure_run(METALZOA_HISTORICAL, equip_metalmorph=True)

        def shape(moves, code):
            return [
                (
                    ZOA if m["code"] == ZOA else METALMORPH if m["code"] == METALMORPH else "metalzoa",
                    m["from"]["location"],
                    m["to"]["location"],
                )
                for m in moves
                if m["code"] in (ZOA, METALMORPH, code)
            ]

        self.assertEqual(shape(modern_moves, METALZOA_MODERN), shape(hist_moves, METALZOA_HISTORICAL))

    def test_historical_procedure_is_not_offered_without_metalmorph(self):
        _moves, offered = self._procedure_run(METALZOA_HISTORICAL, equip_metalmorph=False)
        self.assertEqual([], offered, "Zoa alone is not enough: it must be equipped with Metalmorph")

    def test_historical_metalzoa_cannot_be_normal_summoned_or_set(self):
        setup = f"Debug.AddCard({METALZOA_HISTORICAL},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
        # two Tributes are available, so only a rule against Normal Summoning
        # can stop a Level 8
        setup += f"Debug.AddCard({MILLENNIUM_SHIELD},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        setup += f"Debug.AddCard({MILLENNIUM_SHIELD},0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)\n"
        duel = scenario(DUEL_MODE_EDISON, setup + deck_fillers())
        self.addCleanup(duel.close)
        lists: list[dict] = []

        def idle(prompt):
            lists.append(H.idle_lists(prompt))
            return H.answer_idle(7)

        duel.default_response(H.MSG_SELECT_IDLECMD, idle)
        standing_answers(duel)
        duel.run(turns=1)
        self.assertTrue(lists)
        self.assertEqual([], lists[0]["summonable"])
        self.assertEqual([], lists[0]["msetable"])


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class StealthUnionEdisonTest(unittest.TestCase):
    """Era text (GLAS-EN041): "Once per turn, you can select 1 monster you
    control, except a Machine-Type monster, and equip it to this card." Modern
    text: "select 1 face-up monster on the field", so it can take an
    opponent's monster."""

    def _board(self, code: int, own_monster: bool, opponent_monsters: int, position: str = "POS_FACEUP_ATTACK") -> str:
        setup = f"Debug.AddCard({code},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        if own_monster:
            setup += f"Debug.AddCard({MILLENNIUM_SHIELD},0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)\n"
        for i in range(opponent_monsters):
            setup += f"Debug.AddCard({MILLENNIUM_SHIELD},1,1,LOCATION_MZONE,{i},{position})\n"
        return setup + deck_fillers()

    def _first_idle(self, code: int, own_monster: bool, opponent_monsters: int) -> dict:
        duel = scenario(DUEL_MODE_EDISON, self._board(code, own_monster, opponent_monsters))
        self.addCleanup(duel.close)
        lists: list[dict] = []

        def idle(prompt):
            lists.append(H.idle_lists(prompt))
            return H.answer_idle(7)

        duel.default_response(H.MSG_SELECT_IDLECMD, idle)
        standing_answers(duel)
        duel.run(turns=1)
        self.assertTrue(lists)
        return lists[0]

    def _equip_candidates(self, code: int) -> tuple[list[int], list[dict], H.Duel]:
        """Activate the equip effect with one own and one opposing non-Machine
        monster face-up; returns the target prompt's candidates, the moves and the duel."""
        duel = scenario(DUEL_MODE_EDISON, self._board(code, own_monster=True, opponent_monsters=1))
        self.addCleanup(duel.close)
        offered: list[list[int]] = []

        def take_first(prompt):
            offered.append(H.card_candidates(prompt))
            return H.answer_cards(0)

        duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))
        duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
        duel.default_response(H.MSG_SELECT_CARD, take_first)
        standing_answers(duel)
        duel.run(turns=1)
        self.assertEqual(1, len(offered), "the equip effect must ask for exactly one target")
        return offered[0], duel.moves(), duel

    def test_modern_card_can_equip_an_opponents_monster_with_no_monster_of_its_own(self):
        lists = self._first_idle(STEALTH_UNION_MODERN, own_monster=False, opponent_monsters=1)
        self.assertEqual([(STEALTH_UNION_MODERN, 0)], lists["activatable"])

    def test_historical_card_cannot_use_its_equip_effect_when_only_the_opponent_has_a_monster(self):
        lists = self._first_idle(STEALTH_UNION_HISTORICAL, own_monster=False, opponent_monsters=1)
        self.assertEqual([], lists["activatable"], "the era effect selects only a monster you control")

    def test_historical_card_uses_its_equip_effect_on_its_own_monster(self):
        lists = self._first_idle(STEALTH_UNION_HISTORICAL, own_monster=True, opponent_monsters=1)
        self.assertEqual([(STEALTH_UNION_HISTORICAL, 0)], lists["activatable"])

    def test_modern_card_offers_both_players_monsters_as_equip_targets(self):
        candidates, _moves, _duel = self._equip_candidates(STEALTH_UNION_MODERN)
        self.assertEqual(2, len(candidates), "own and opposing face-up non-Machine monsters")

    def test_historical_card_offers_only_its_own_monster_as_an_equip_target(self):
        candidates, moves, duel = self._equip_candidates(STEALTH_UNION_HISTORICAL)
        self.assertEqual(1, len(candidates))
        self.assertTrue(duel.seen(H.MSG_EQUIP), "the own monster is equipped")
        equipped = [m for m in moves if m["to"]["location"] == H.LOCATION_SZONE]
        self.assertEqual(1, len(equipped))
        self.assertEqual(0, equipped[0]["from"]["controler"], "the equipped monster is the one the player controls")

    def _attack(self, code: int, equip_first: bool, defender_position: str, opponent_monsters: int):
        duel = scenario(
            DUEL_MODE_EDISON | DUEL_ATTACK_FIRST_TURN,
            self._board(code, own_monster=equip_first, opponent_monsters=opponent_monsters, position=defender_position),
        )
        self.addCleanup(duel.close)
        if equip_first:
            duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))
        duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(6))  # to the Battle Phase
        duel.default_response(H.MSG_SELECT_BATTLECMD, H.answer_battle_attack_or_end)
        duel.default_response(H.MSG_SELECT_CARD, H.answer_cards(0))
        standing_answers(duel)
        duel.run(turns=1)
        return duel

    @staticmethod
    def _battle_damage(duel: H.Duel) -> list[tuple[int, int]]:
        out = []
        for m in duel.seen(H.MSG_DAMAGE):
            m._buf.seek(0)
            out.append((m.u8(), m.u32()))
        return out

    def test_attack_halves_original_atk_and_pierces_defense_like_the_modern_card(self):
        # 3600 halved is 1800; Millennium Shield has 3000 DEF, so use a Giant
        # Rat (1450 DEF) as the defender: piercing damage 1800 - 1450 = 350.
        results = {}
        for label, code in (("modern", STEALTH_UNION_MODERN), ("historical", STEALTH_UNION_HISTORICAL)):
            duel = scenario(
                DUEL_MODE_EDISON | DUEL_ATTACK_FIRST_TURN,
                f"Debug.AddCard({code},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
                f"Debug.AddCard({GIANT_RAT},1,1,LOCATION_MZONE,0,POS_FACEUP_DEFENSE)\n" + deck_fillers(),
            )
            self.addCleanup(duel.close)
            duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(6))
            duel.default_response(H.MSG_SELECT_BATTLECMD, H.answer_battle_attack_or_end)
            duel.default_response(H.MSG_SELECT_CARD, H.answer_cards(0))
            standing_answers(duel)
            duel.run(turns=1)
            results[label] = self._battle_damage(duel)
        self.assertEqual([(1, 350)], results["modern"])
        self.assertEqual(results["modern"], results["historical"])

    def test_equipped_by_its_effect_it_attacks_every_opposing_monster_once_like_the_modern_card(self):
        attacks = {}
        for label, code in (("modern", STEALTH_UNION_MODERN), ("historical", STEALTH_UNION_HISTORICAL)):
            duel = self._attack(code, equip_first=True, defender_position="POS_FACEUP_ATTACK", opponent_monsters=2)
            attacks[label] = len(duel.seen(H.MSG_ATTACK))
        self.assertEqual(2, attacks["modern"])
        self.assertEqual(2, attacks["historical"])

    def test_historical_card_attacks_only_once_without_an_equipped_monster(self):
        duel = self._attack(
            STEALTH_UNION_HISTORICAL, equip_first=False, defender_position="POS_FACEUP_ATTACK", opponent_monsters=2
        )
        self.assertEqual(1, len(duel.seen(H.MSG_ATTACK)))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
