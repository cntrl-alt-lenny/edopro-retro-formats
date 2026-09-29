"""Engine tests for the historical cards this project generates for BOTH the
Edison (2010-04-24) and Tengu (2011-09-17) formats (roadmap item 7, round 031):
Goddess of Whim, Strike Ninja and Green Baboon, plus one test for each of the four
cards round 035 removed (Metalzoa, Rise of the Snake Deity, Malefic Blue-Eyes White
Dragon, Soul Rope), which assert that the modern card is used and does what Konami's
period rulings say (docs/research/period-rulings-generated-scripts.md).

Each generated card's record puts the same historical state at both snapshots, so each
generated card replaces the modern one in both lists. Every difference test therefore runs
its scenario under both formats' duel options (`FORMATS`), once with the modern card (its
cards.cdb code, the script Project Ignis ships) and once with this repository's generated
card (`dist/databases/retro-formats.cdb`, `dist/scripts/c<passcode>.lua`), in the same
scenario, and asserts the difference the erratum record claims. A generated script that
behaved like the modern card would leave the two runs identical and the historical
assertion would be red.

"Control" tests exist so a script cannot pass by doing nothing: they show it
still behaves like the modern card where the period text and the modern text
agree.

Prerequisites are those of tests/engine/harness.py (skips when the engine is
absent), plus a committed dist/ (this module reads it, exactly as a client
whose data_path/script_path point at dist/ would).
"""

from __future__ import annotations

import sqlite3
import struct
import unittest
from pathlib import Path

from . import harness as H
from .test_edison_historical_scripts import (
    DUEL_MODE_EDISON,
    GIANT_RAT,
    MONSTER_REBORN,
    deck_fillers,
    standing_answers,
)
from .test_historical_behaviour import (
    DARK_HOLE,
    DUEL_ATTACK_FIRST_TURN,
    DUEL_MODE_MR1,
    scenario,
)

# Tengu's rule profile (data/rule-profiles/tcg-mr2-tengu.json) is exactly the
# compiled Master Rule 1 flag set with no 0-ATK rule; Edison's is that plus the
# 0-ATK rule (tests/test_tengu_format.py pins both flag lists).
DUEL_MODE_TENGU = DUEL_MODE_MR1
FORMATS = (("edison", DUEL_MODE_EDISON), ("tengu", DUEL_MODE_TENGU))

MSG_TOSS_COIN = 130

PALE_BEAST = 21263083  # vanilla Level 4 Beast, 1500 ATK
GIGANTES = 47606319  # 1900 ATK Rock: the monster that wins a battle against the cards above

GODDESS_MODERN = 67959180
GODDESS_HISTORICAL = 600000004

NINJA_MODERN = 41006930
NINJA_HISTORICAL = 600000005
FERAL_IMP = 41392891  # DARK

BABOON_MODERN = 46668237
BABOON_HISTORICAL = 600000006

SNAKE_MODERN = 16067089
SNAKE_RETIRED = 600000007  # removed in round 035: the modern card is used
VENNOMINON = 72677437
VENNOMINAGA = 8062132

MALEFIC_MODERN = 9433350
MALEFIC_RETIRED = 600000008  # removed in round 035
METALZOA_MODERN = 50705071
METALZOA_RETIRED = 600000001  # removed in round 035
BLUE_EYES = 89631139
SOGEN = 86318356  # Field Spell
MALEFIC_PARADOX = 8310162

ROPE_MODERN = 37383714
ROPE_RETIRED = 600000009  # removed in round 035

# -- prompt helpers -----------------------------------------------------------


def select_minimum(prompt: H.Message) -> bytes:
    """MSG_SELECT_CARD: choose the first `min` cards offered."""
    prompt._buf.seek(0)
    prompt.u8()  # player
    prompt.u8()  # cancelable
    minimum = prompt.u32()
    return H.answer_cards(*range(minimum))


def select_first_unselected(prompt: H.Message) -> bytes:
    """MSG_SELECT_UNSELECT_CARD (the modern Metalzoa-style procedure prompt):
    take the first card. Response: int32 1 then the index (playerop.cpp)."""
    return struct.pack("<ii", 1, 0)


def chain_offers(prompt: H.Message) -> tuple[int, int, list[int]]:
    """MSG_SELECT_CHAIN: (player, forced, codes offered). Layout as in
    harness.answer_chain_decline_unless_forced, then per entry: u32 code,
    u8, u8, u32."""
    prompt._buf.seek(0)
    player = prompt.u8()
    prompt.u8()  # spe_count
    forced = prompt.u8()
    prompt.u32()
    prompt.u32()  # hint timings
    codes = []
    for _ in range(prompt.u32()):
        codes.append(prompt.u32())
        prompt.u8()
        prompt.u8()
        prompt.u32()
    return player, forced, codes


class Offers:
    """Answers player 0's chain prompts by chaining `wanted` whenever it is on
    offer, and records every code player 0 was offered."""

    def __init__(self, wanted: int | None):
        self.wanted = wanted
        self.offered: list[list[int]] = []

    def __call__(self, prompt: H.Message) -> bytes:
        player, forced, codes = chain_offers(prompt)
        if player == 0:
            self.offered.append(codes)
            if self.wanted in codes:
                return H.answer_int(codes.index(self.wanted))
        return H.answer_int(0 if forced else -1)

    def was_offered(self) -> bool:
        return any(self.wanted in codes for codes in self.offered)


def run_scenario(setup: str, mode: int, *, idle, offers: Offers | None = None, battle=None, turns: int = 1):
    """One duel from `setup` with the standing answers every test here shares."""
    duel = scenario(mode, setup + deck_fillers())
    duel.default_response(H.MSG_SELECT_IDLECMD, idle)
    duel.default_response(H.MSG_SELECT_CARD, select_minimum)
    duel.default_response(H.MSG_SELECT_UNSELECT_CARD, select_first_unselected)
    duel.default_response(H.MSG_SELECT_OPTION, H.answer_int(0))
    duel.default_response(H.MSG_SELECT_EFFECTYN, H.answer_int(1))
    duel.default_response(H.MSG_SELECT_YESNO, H.answer_int(1))
    standing_answers(duel)
    if offers is not None:
        duel.default_response(H.MSG_SELECT_CHAIN, offers)
    if battle is not None:
        duel.default_response(H.MSG_SELECT_BATTLECMD, battle)
    duel.run(turns=turns)
    return duel


def chained_codes(duel: H.Duel) -> list[int]:
    codes = []
    for message in duel.seen(H.MSG_CHAINING):
        message._buf.seek(0)
        codes.append(message.u32())
    return codes


def moved(duel: H.Duel, code: int, source: int, target: int) -> int:
    """How many times `code` moved from location `source` to `target`."""
    return sum(
        1
        for m in duel.moves()
        if m["code"] == code and m["from"]["location"] == source and m["to"]["location"] == target
    )


def attack_once():
    """SELECT_BATTLECMD: attack with the first attacker offered, then end."""
    state = {"attacked": False}

    def answer(prompt):
        if not state["attacked"] and H.battle_lists(prompt)["attackable"]:
            state["attacked"] = True
            return H.answer_battle(1, 0)
        return H.answer_battle(3)

    return answer


def activate_capped(cap: int):
    """SELECT_IDLECMD: activate the first available effect until `cap`
    activations have been made, then end the turn."""
    state = {"done": 0}

    def answer(prompt):
        if state["done"] < cap and H.idle_lists(prompt)["activatable"]:
            state["done"] += 1
            return H.answer_idle(5, 0)
        return H.answer_idle(7)

    return answer


def in_both_formats(test):
    """Run `test(self, mode)` once per format under a subTest."""

    def wrapper(self):
        for name, mode in FORMATS:
            with self.subTest(format=name):
                test(self, mode)

    wrapper.__name__ = test.__name__
    wrapper.__doc__ = test.__doc__
    return wrapper


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class GoddessOfWhimSharedTest(unittest.TestCase):
    """Period text: "Toss a coin and call Heads or Tails. Call it right and this
    card's ATK will be doubled during this turn. Call it wrong and it will be
    halved during this turn." No use limit. The modern card: "Once per turn:"."""

    def _run(self, code: int, mode: int, cap: int):
        setup = (
            f"local g=Debug.AddCard({code},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            "local probe=Effect.GlobalEffect()\n"
            "probe:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)\n"
            "probe:SetCode(EVENT_PHASE+PHASE_END)\n"
            "probe:SetCountLimit(1)\n"
            'probe:SetOperation(function() Debug.Message("ATK "..g:GetAttack()) end)\n'
            "Duel.RegisterEffect(probe,0)\n"
        )
        duel = run_scenario(setup, mode, idle=activate_capped(cap))
        atk = [int(text.split()[1]) for _kind, text in duel.log if text.startswith("ATK ")]
        return duel, atk

    @in_both_formats
    def test_the_period_card_can_be_activated_again_in_the_same_turn(self, mode):
        modern, _ = self._run(GODDESS_MODERN, mode, cap=3)
        historical, _ = self._run(GODDESS_HISTORICAL, mode, cap=3)
        self.assertEqual([GODDESS_MODERN], chained_codes(modern), "the modern card is limited to once per turn")
        self.assertEqual([GODDESS_HISTORICAL] * 3, chained_codes(historical), "the period card has no limit")
        self.assertEqual(3, len(historical.seen(MSG_TOSS_COIN)), "each activation tosses a coin")

    @in_both_formats
    def test_one_activation_tosses_a_coin_and_doubles_or_halves_atk_like_the_modern_card(self, mode):
        modern, modern_atk = self._run(GODDESS_MODERN, mode, cap=1)
        historical, historical_atk = self._run(GODDESS_HISTORICAL, mode, cap=1)
        self.assertEqual(1, len(modern.seen(MSG_TOSS_COIN)))
        self.assertEqual(1, len(historical.seen(MSG_TOSS_COIN)))
        self.assertIn(historical_atk[0], (1900, 475), "950 ATK doubled or halved (rounded up)")
        self.assertEqual(modern_atk[0], historical_atk[0], "same seed, same call: same result and amount")


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class StrikeNinjaSharedTest(unittest.TestCase):
    """Period text: "... You can only use this effect once per turn." No name
    qualifier, so each copy has its own use. The modern card: "You can only use
    this effect of "Strike Ninja" once per turn"."""

    def _run(self, code: int, mode: int, copies: int):
        setup = "".join(
            f"Debug.AddCard({code},0,0,LOCATION_MZONE,{seq},POS_FACEUP_ATTACK)\n" for seq in range(copies)
        )
        setup += "".join(f"Debug.AddCard({FERAL_IMP},0,0,LOCATION_GRAVE,{seq},POS_FACEUP)\n" for seq in range(4))
        return run_scenario(setup, mode, idle=activate_capped(4))

    @in_both_formats
    def test_two_copies_can_each_use_the_effect_in_the_same_turn(self, mode):
        modern = self._run(NINJA_MODERN, mode, copies=2)
        historical = self._run(NINJA_HISTORICAL, mode, copies=2)
        self.assertEqual([NINJA_MODERN], chained_codes(modern), "one use per turn across both copies")
        self.assertEqual([NINJA_HISTORICAL] * 2, chained_codes(historical), "one use per copy")
        self.assertEqual(2, moved(historical, NINJA_HISTORICAL, H.LOCATION_MZONE, H.LOCATION_REMOVED))
        self.assertEqual(
            2,
            moved(historical, NINJA_HISTORICAL, H.LOCATION_REMOVED, H.LOCATION_MZONE),
            "both return during the End Phase",
        )
        self.assertEqual(4, moved(historical, FERAL_IMP, H.LOCATION_GRAVE, H.LOCATION_REMOVED))

    @in_both_formats
    def test_one_use_banishes_two_dark_monsters_and_the_ninja_returns_like_the_modern_card(self, mode):
        modern = self._run(NINJA_MODERN, mode, copies=1)
        historical = self._run(NINJA_HISTORICAL, mode, copies=1)

        def shape(duel, code):
            return [
                (m["code"] if m["code"] == FERAL_IMP else "ninja", m["from"]["location"], m["to"]["location"])
                for m in duel.moves()
                if m["code"] in (FERAL_IMP, code)
            ]

        self.assertEqual(shape(modern, NINJA_MODERN), shape(historical, NINJA_HISTORICAL))
        self.assertEqual(2, moved(historical, FERAL_IMP, H.LOCATION_GRAVE, H.LOCATION_REMOVED))
        self.assertEqual(1, moved(historical, NINJA_HISTORICAL, H.LOCATION_MZONE, H.LOCATION_REMOVED))
        self.assertEqual(1, moved(historical, NINJA_HISTORICAL, H.LOCATION_REMOVED, H.LOCATION_MZONE))


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class GreenBaboonSharedTest(unittest.TestCase):
    """Period text: "When a Beast-Type monster you control is destroyed and sent
    to the Graveyard, you can pay 1000 Life Points to Special Summon this card
    from your hand or the Graveyard." The modern card needs the Beast to have
    been face-up and cannot be used in the Damage Step. Konami's errata lists
    (compiled 2009-07-30, 2010-01-05, 2010-11-05) say "You cannot activate the
    effect of this card during the Damage Step", so the generated card keeps only
    the no-face-up difference (round 035; a UDE ruling says otherwise on that, its
    range in force is not shown, and it is on the owner's list)."""

    def _dark_hole(self, baboon: int, beast_position: str, beast: int, mode: int):
        setup = (
            f"Debug.AddCard({DARK_HOLE},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({baboon},0,0,LOCATION_HAND,1,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({beast},0,0,LOCATION_MZONE,0,{beast_position})\n"
        )
        offers = Offers(baboon)
        duel = scenario(mode, setup + deck_fillers())
        duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Dark Hole
        duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
        duel.default_response(H.MSG_SELECT_CARD, select_minimum)
        standing_answers(duel)
        duel.default_response(H.MSG_SELECT_CHAIN, offers)
        duel.run(turns=1)
        return duel, offers

    def _battle(self, baboon: int, mode: int):
        setup = (
            f"Debug.AddCard({baboon},0,0,LOCATION_HAND,1,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({PALE_BEAST},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({GIGANTES},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        )
        offers = Offers(baboon)
        duel = run_scenario(
            setup, mode | DUEL_ATTACK_FIRST_TURN, idle=H.answer_idle(6), offers=offers, battle=attack_once()
        )
        return duel, offers

    @in_both_formats
    def test_a_face_down_beast_destroyed_lets_the_period_card_special_summon_itself(self, mode):
        modern, modern_offers = self._dark_hole(BABOON_MODERN, "POS_FACEDOWN_DEFENSE", PALE_BEAST, mode)
        historical, offers = self._dark_hole(BABOON_HISTORICAL, "POS_FACEDOWN_DEFENSE", PALE_BEAST, mode)
        self.assertFalse(modern_offers.was_offered(), "the modern card needs a face-up Beast")
        self.assertEqual(0, moved(modern, BABOON_MODERN, H.LOCATION_HAND, H.LOCATION_MZONE))
        self.assertTrue(offers.was_offered())
        self.assertEqual(1, moved(historical, BABOON_HISTORICAL, H.LOCATION_HAND, H.LOCATION_MZONE))
        self.assertEqual(1, len(historical.seen(H.MSG_PAY_LPCOST)), "1000 Life Points are paid")

    @in_both_formats
    def test_a_beast_destroyed_by_battle_offers_neither_card_in_the_damage_step(self, mode):
        # Round 035: the round-031 script allowed the Damage Step (EFFECT_FLAG_DAMAGE_STEP); Konami's
        # errata lists and rulebook forbid it, so the period card is not offered, like the modern one.
        modern, modern_offers = self._battle(BABOON_MODERN, mode)
        historical, offers = self._battle(BABOON_HISTORICAL, mode)
        self.assertEqual(1, moved(modern, PALE_BEAST, H.LOCATION_MZONE, H.LOCATION_GRAVE))
        self.assertFalse(modern_offers.was_offered(), "the modern card is barred from the Damage Step")
        self.assertEqual(1, moved(historical, PALE_BEAST, H.LOCATION_MZONE, H.LOCATION_GRAVE))
        self.assertFalse(offers.was_offered(), "so is the period card: Konami's lists say so")
        self.assertEqual(0, moved(historical, BABOON_HISTORICAL, H.LOCATION_HAND, H.LOCATION_MZONE))

    @in_both_formats
    def test_with_two_copies_available_only_one_is_special_summoned_like_the_modern_card(self, mode):
        # Konami's lists: "you can only Special Summon 1 "Green Baboon, Defender of the Forest," even if
        # multiple copies are available in your hand/Graveyard." Both cards satisfy it in this scenario.
        for baboon in (BABOON_MODERN, BABOON_HISTORICAL):
            with self.subTest(card=baboon):
                setup = (
                    f"Debug.AddCard({DARK_HOLE},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
                    f"Debug.AddCard({baboon},0,0,LOCATION_HAND,1,POS_FACEDOWN_DEFENSE)\n"
                    f"Debug.AddCard({baboon},0,0,LOCATION_HAND,2,POS_FACEDOWN_DEFENSE)\n"
                    f"Debug.AddCard({PALE_BEAST},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
                )
                offers = Offers(baboon)
                duel = scenario(mode, setup + deck_fillers())
                duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Dark Hole
                duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
                duel.default_response(H.MSG_SELECT_CARD, select_minimum)
                standing_answers(duel)
                duel.default_response(H.MSG_SELECT_CHAIN, offers)
                duel.run(turns=1)
                self.assertTrue(offers.was_offered())
                self.assertEqual(1, moved(duel, baboon, H.LOCATION_HAND, H.LOCATION_MZONE))
                self.assertEqual(1, len(duel.seen(H.MSG_PAY_LPCOST)))

    @in_both_formats
    def test_a_face_up_beast_destroyed_by_a_card_effect_works_and_a_rock_does_not_like_the_modern_card(self, mode):
        for baboon in (BABOON_MODERN, BABOON_HISTORICAL):
            with self.subTest(card=baboon):
                duel, offers = self._dark_hole(baboon, "POS_FACEUP_ATTACK", PALE_BEAST, mode)
                self.assertTrue(offers.was_offered())
                self.assertEqual(1, moved(duel, baboon, H.LOCATION_HAND, H.LOCATION_MZONE))
                self.assertEqual(1, len(duel.seen(H.MSG_PAY_LPCOST)))
                duel, offers = self._dark_hole(baboon, "POS_FACEUP_ATTACK", GIGANTES, mode)
                self.assertFalse(offers.was_offered(), "a destroyed Rock is not a Beast")
                self.assertEqual(0, moved(duel, baboon, H.LOCATION_HAND, H.LOCATION_MZONE))


LFLIST_DIR = Path(__file__).resolve().parents[2] / "dist" / "lflists"
DIST_DIR = Path(__file__).resolve().parents[2] / "dist"


def listed_codes(format_id: str) -> set[int]:
    """The passcodes a built lflist whitelists, read from dist/ as a client would."""
    codes = set()
    for line in (LFLIST_DIR / f"{format_id}.lflist.conf").read_text(encoding="utf-8").splitlines():
        head = line.split("--", 1)[0].split()
        if len(head) == 2 and head[0].isdigit():
            codes.add(int(head[0]))
    return codes


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class RetiredCardsUseTheModernCardTest(unittest.TestCase):
    """Round 035 removed four generated cards because Konami's period rulings show the modern card
    behaves as the era card did (docs/research/period-rulings-generated-scripts.md). Each test asserts
    that the lists name the modern code and no generated code, that the generated row and script are
    gone, and that the modern card does what those rulings say. Red on the wrong behaviour: restore
    the generated code to a list, or put back the round-031 script (the scratch runs in the report)."""

    def _assert_the_modern_card_is_used(self, modern: int, retired: int, formats: tuple[str, ...]):
        for format_id in formats:
            with self.subTest(format=format_id):
                codes = listed_codes(format_id)
                self.assertIn(modern, codes, "the list names the modern card")
                self.assertNotIn(retired, codes, "and no longer the generated one")
        self.assertFalse((DIST_DIR / "scripts" / f"c{retired}.lua").exists())
        con = sqlite3.connect(f"file:{DIST_DIR / 'databases' / 'retro-formats.cdb'}?mode=ro", uri=True)
        try:
            self.assertEqual([], con.execute("SELECT id FROM datas WHERE id = ?", (retired,)).fetchall())
        finally:
            con.close()

    def _reborn_candidates(self, code: int, mode: int) -> list[int]:
        setup = (
            f"Debug.AddCard({MONSTER_REBORN},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({SOGEN},0,0,LOCATION_SZONE,5,POS_FACEUP)\n"
            f"Debug.AddCard({code},0,0,LOCATION_GRAVE,0,POS_FACEUP,true)\n"
            f"Debug.AddCard({GIANT_RAT},0,0,LOCATION_GRAVE,1,POS_FACEUP)\n"
        )
        offered: list[list[int]] = []

        def take_first(prompt):
            offered.append(H.card_candidates(prompt))
            return H.answer_cards(0)

        duel = scenario(mode, setup + deck_fillers())
        duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Monster Reborn
        duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
        duel.default_response(H.MSG_SELECT_CARD, take_first)
        standing_answers(duel)
        duel.run(turns=1)
        self.assertEqual(1, len(offered), "Monster Reborn must ask for exactly one target")
        return offered[0]

    @in_both_formats
    def test_metalzoa_is_the_modern_card_and_can_be_revived_after_a_proper_summon(self, mode):
        # Konami's rulebook: a Special Summon Monster may be Special Summoned by another card's effect
        # once it was properly Special Summoned; "can only be Special Summoned by" is not "except by".
        # Metalzoa's erratum precedes Tengu's snapshot, so only Edison's list ever carried the generated card.
        self._assert_the_modern_card_is_used(METALZOA_MODERN, METALZOA_RETIRED, ("2010-03-edison", "2011-09-tengu"))
        self.assertIn(METALZOA_MODERN, self._reborn_candidates(METALZOA_MODERN, mode))

    @in_both_formats
    def test_malefic_blue_eyes_is_the_modern_card_and_can_be_revived_after_a_proper_summon(self, mode):
        self._assert_the_modern_card_is_used(MALEFIC_MODERN, MALEFIC_RETIRED, ("2010-03-edison", "2011-09-tengu"))
        candidates = self._reborn_candidates(MALEFIC_MODERN, mode)
        self.assertIn(MALEFIC_MODERN, candidates)
        self.assertIn(GIANT_RAT, candidates)

    def _snake(self, mode: int, *, by_battle: bool):
        setup = (
            f"Debug.AddCard({SNAKE_MODERN},0,0,LOCATION_SZONE,0,POS_FACEDOWN)\n"
            f"Debug.AddCard({VENNOMINON},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({VENNOMINAGA},0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)\n"
        )
        offers = Offers(SNAKE_MODERN)
        if by_battle:
            setup += f"Debug.AddCard({GIGANTES},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            duel = run_scenario(
                setup, mode | DUEL_ATTACK_FIRST_TURN, idle=H.answer_idle(6), offers=offers, battle=attack_once()
            )
        else:
            setup += f"Debug.AddCard({DARK_HOLE},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
            duel = scenario(mode, setup + deck_fillers())
            duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Dark Hole
            duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
            duel.default_response(H.MSG_SELECT_CARD, select_minimum)
            standing_answers(duel)
            duel.default_response(H.MSG_SELECT_CHAIN, offers)
            duel.run(turns=1)
        return duel, offers

    @in_both_formats
    def test_rise_of_the_snake_deity_is_the_modern_card_which_is_not_offered_in_the_damage_step(self, mode):
        # Konami's rulebook: only Counter Traps and cards that change ATK/DEF may be activated in the
        # Damage Step, and the UDE Netrep answered for this card that it cannot be. So the period card,
        # like the modern one, cannot respond to a Vennominon destroyed in battle.
        self._assert_the_modern_card_is_used(SNAKE_MODERN, SNAKE_RETIRED, ("2010-03-edison", "2011-09-tengu"))
        duel, offers = self._snake(mode, by_battle=True)
        self.assertEqual(1, moved(duel, VENNOMINON, H.LOCATION_MZONE, H.LOCATION_GRAVE))
        self.assertFalse(offers.was_offered())
        self.assertEqual(0, moved(duel, VENNOMINAGA, H.LOCATION_DECK, H.LOCATION_MZONE))
        duel, offers = self._snake(mode, by_battle=False)
        self.assertTrue(offers.was_offered(), "destroyed by a card effect it is offered")
        self.assertEqual(1, moved(duel, VENNOMINAGA, H.LOCATION_DECK, H.LOCATION_MZONE))

    def _rope(self, mode: int, *, by_battle: bool):
        setup = (
            f"Debug.AddCard({ROPE_MODERN},0,0,LOCATION_SZONE,0,POS_FACEDOWN)\n"
            f"Debug.AddCard({PALE_BEAST},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({GIANT_RAT},0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)\n"
        )
        offers = Offers(ROPE_MODERN)
        if by_battle:
            setup += f"Debug.AddCard({GIGANTES},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            duel = run_scenario(
                setup, mode | DUEL_ATTACK_FIRST_TURN, idle=H.answer_idle(6), offers=offers, battle=attack_once()
            )
        else:
            setup += f"Debug.AddCard({DARK_HOLE},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
            duel = scenario(mode, setup + deck_fillers())
            duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Dark Hole
            duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
            duel.default_response(H.MSG_SELECT_CARD, select_minimum)
            standing_answers(duel)
            duel.default_response(H.MSG_SELECT_CHAIN, offers)
            duel.run(turns=1)
        return duel, offers

    @in_both_formats
    def test_soul_rope_is_the_modern_card_which_is_not_offered_in_the_damage_step(self, mode):
        # Same rulebook rule as Rise of the Snake Deity. The 2015 "by a card effect" difference
        # is not reproduced and is a known gap on the record.
        self._assert_the_modern_card_is_used(ROPE_MODERN, ROPE_RETIRED, ("2010-03-edison", "2011-09-tengu"))
        duel, offers = self._rope(mode, by_battle=True)
        self.assertEqual(1, moved(duel, PALE_BEAST, H.LOCATION_MZONE, H.LOCATION_GRAVE))
        self.assertFalse(offers.was_offered())
        self.assertEqual(0, moved(duel, GIANT_RAT, H.LOCATION_DECK, H.LOCATION_MZONE))
        duel, offers = self._rope(mode, by_battle=False)
        self.assertTrue(offers.was_offered(), "destroyed by a card effect it is offered")
        self.assertEqual(1, moved(duel, GIANT_RAT, H.LOCATION_DECK, H.LOCATION_MZONE))
        self.assertEqual(1, len(duel.seen(H.MSG_PAY_LPCOST)))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
