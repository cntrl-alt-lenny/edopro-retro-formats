"""Engine tests for the historical cards this project generates for BOTH the
Edison (2010-04-24) and Tengu (2011-09-17) formats (roadmap item 7): Strike Ninja and
Dice Re-Roll, plus tests for the cards that were removed or never shipped because period
rulings show the modern card behaves as the era card did: Metalzoa, Rise of the Snake Deity,
Malefic Blue-Eyes White Dragon, Soul Rope (round 035), and Goddess of Whim, Green Baboon,
Dark Master - Zorc and the five strict-nomi cards Gigantes, The Rock Spirit, Garuda the Wind
Spirit, VW-Tiger Catapult and Gladiator Beast Heraklinos (round 036). Those tests assert that
the modern card is used and does what the rulings say
(docs/research/period-rulings-generated-scripts.md).

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
GODDESS_RETIRED = 600000004  # removed in round 036: the modern card is used

NINJA_MODERN = 41006930
NINJA_HISTORICAL = 600000005
FERAL_IMP = 41392891  # DARK

BABOON_MODERN = 46668237
BABOON_RETIRED = 600000006  # removed in round 036

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

ZORC_MODERN = 97642679
ZORC_RETIRED = 600000015  # proposed in round 034, never shipped

DICE_MODERN = 83241722
DICE_HISTORICAL = 600000016
MSG_TOSS_DICE = 131

# Round 036: the Union Condition (Machina Peacekeeper, Machina Gearframe) and Chaos Neos.
MECHANICALCHASER = 7359741  # vanilla Level 4 Machine
HEAVY_MECH_SUPPORT_PLATFORM = 23265594  # a Union monster under the current rules
PEACEKEEPER_MODERN = 78349103
PEACEKEEPER_HISTORICAL = 600000018
GEARFRAME_MODERN = 42940404
GEARFRAME_HISTORICAL = 600000019
CHAOS_NEOS_MODERN = 17032740
CHAOS_NEOS_HISTORICAL = 600000020
FROG_MODERN = 12538374
FROG_HISTORICAL = 600000021

# Round 034's five strict-nomi proposals, never shipped: (name, modern card, the number round 034 proposed).
NOMI_CARDS = (
    ("Gigantes", 47606319, 600000010),
    ("The Rock Spirit", 76305638, 600000011),
    ("Garuda the Wind Spirit", 12800777, 600000012),
    ("VW-Tiger Catapult", 58859575, 600000013),
    ("Gladiator Beast Heraklinos", 27346636, 600000014),
)

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



class UnionConditionMixin:
    """Konami's Advanced Game Play FAQ and its Cyber Phoenix entry (counted under the owner's decision of
    2026-09-29), and Konami's Delta Tri ruling of 2010-04-30 (Tengu): "A monster can only be equipped with
    1 Union Monster at a time". The modern Union procedure has no such limit.

    The scenarios equip a real Union monster (Heavy Mech Support Platform, a modern-rule Union) to a
    Machine, then ask whether the card under test can be equipped to the same Machine (and the reverse).
    The unequip position is NOT tested: no ruling read covers it."""

    MODERN: int
    HISTORICAL: int

    def _idle_offers(self, code: int, mode: int, setup: str) -> tuple[H.Duel, bool, list[int]]:
        seen: list[list[int]] = []

        def idle(prompt):
            codes = [c for c, _seq in H.idle_lists(prompt)["activatable"]]
            seen.append(codes)
            return H.answer_idle(7)

        duel = run_scenario(setup, mode, idle=idle)
        return duel, any(code in codes for codes in seen), seen[0] if seen else []

    def _carrying(self, union: int) -> str:
        return (
            f"local x=Debug.AddCard({MECHANICALCHASER},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"local u=Debug.AddCard({union},0,0,LOCATION_SZONE,0,POS_FACEUP)\n"
            "Debug.PreEquip(u,x)\n"
            "aux.SetUnionState(u)\n"
        )

    @in_both_formats
    def test_a_monster_carrying_a_union_cannot_be_given_a_second_one(self, mode):
        for code in (self.MODERN, self.HISTORICAL):
            with self.subTest(card=code):
                setup = self._carrying(HEAVY_MECH_SUPPORT_PLATFORM) + (
                    f"Debug.AddCard({code},0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)\n"
                )
                duel, offered, _ = self._idle_offers(code, mode, setup)
                if code == self.MODERN:
                    self.assertTrue(offered, "the modern card can join a Union monster on the same Machine")
                else:
                    self.assertFalse(offered, "the period card cannot: a monster carries 1 Union monster at a time")

    @in_both_formats
    def test_a_union_cannot_be_given_to_a_monster_carrying_the_card(self, mode):
        for code in (self.MODERN, self.HISTORICAL):
            with self.subTest(card=code):
                setup = self._carrying(code) + (
                    f"Debug.AddCard({HEAVY_MECH_SUPPORT_PLATFORM},0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)\n"
                )
                duel, offered, _ = self._idle_offers(HEAVY_MECH_SUPPORT_PLATFORM, mode, setup)
                if code == self.MODERN:
                    self.assertTrue(offered, "under the modern card another Union monster can be equipped")
                else:
                    self.assertFalse(offered, "under the period card the monster already carries its 1 Union monster")

    @in_both_formats
    def test_a_machine_with_no_union_is_equipped_like_the_modern_card(self, mode):
        for code in (self.MODERN, self.HISTORICAL):
            with self.subTest(card=code):
                setup = (
                    f"Debug.AddCard({MECHANICALCHASER},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
                    f"Debug.AddCard({code},0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)\n"
                )
                state = {"done": False}

                def idle(prompt, code=code, state=state):
                    activatable = [c for c, _seq in H.idle_lists(prompt)["activatable"]]
                    if not state["done"] and code in activatable:
                        state["done"] = True
                        return H.answer_idle(5, activatable.index(code))
                    return H.answer_idle(7)

                duel = run_scenario(setup, mode, idle=idle)
                self.assertTrue(state["done"], "the equip effect is offered")
                self.assertEqual(1, moved(duel, code, H.LOCATION_MZONE, H.LOCATION_SZONE), "it becomes an Equip Card")
                self.assertEqual(
                    1,
                    sum(1 for m in duel.seen(H.MSG_EQUIP)),
                    "and is equipped to the Machine",
                )


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class MachinaPeacekeeperSharedTest(UnionConditionMixin, unittest.TestCase):
    MODERN = PEACEKEEPER_MODERN
    HISTORICAL = PEACEKEEPER_HISTORICAL


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class MachinaGearframeSharedTest(UnionConditionMixin, unittest.TestCase):
    MODERN = GEARFRAME_MODERN
    HISTORICAL = GEARFRAME_HISTORICAL


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class ChaosNeosSharedTest(unittest.TestCase):
    """Konami's rulebook (Versions 7.0 to 8.0): an Ignition Effect is used "just by declaring its activation
    during your Main Phase", and Main Phase 2 allows "the same" actions as Main Phase 1 (a limit on the number
    of times something can be done still applies across both). The era text has no phase for the coin effect;
    the modern text says "during your Main Phase 1". Only the phase is tested: the coin is random, and the
    contact Fusion procedure and the revival rule are the modern script's."""

    def _run(self, code: int, mode: int, *, use_in_main_phase_1: bool):
        setup = (
            f"Debug.AddCard({code},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)\n"
            f"Debug.AddCard({GIANT_RAT},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        )
        seen: list[bool] = []
        state = {"used": False}

        def idle(prompt):
            activatable = [c for c, _seq in H.idle_lists(prompt)["activatable"]]
            offered = code in activatable
            seen.append(offered)
            if len(seen) == 1:
                if use_in_main_phase_1 and offered:
                    state["used"] = True
                    return H.answer_idle(5, activatable.index(code))
                return H.answer_idle(6)  # to the Battle Phase
            return H.answer_idle(7)

        duel = run_scenario(setup, mode | DUEL_ATTACK_FIRST_TURN, idle=idle, battle=lambda prompt: H.answer_battle(2))  # 2: to Main Phase 2
        return duel, seen, state["used"]

    @in_both_formats
    def test_the_coin_effect_can_be_used_in_main_phase_2_under_the_period_card_only(self, mode):
        _, modern, _ = self._run(CHAOS_NEOS_MODERN, mode, use_in_main_phase_1=False)
        _, historical, _ = self._run(CHAOS_NEOS_HISTORICAL, mode, use_in_main_phase_1=False)
        self.assertEqual([True, False], modern[:2], "the modern card: Main Phase 1 only")
        self.assertEqual([True, True], historical[:2], "the period card: either Main Phase")

    @in_both_formats
    def test_once_used_in_main_phase_1_it_is_not_offered_again_in_main_phase_2_like_the_modern_card(self, mode):
        for code in (CHAOS_NEOS_MODERN, CHAOS_NEOS_HISTORICAL):
            with self.subTest(card=code):
                duel, seen, used = self._run(code, mode, use_in_main_phase_1=True)
                self.assertTrue(used)
                self.assertEqual(1, len(duel.seen(MSG_TOSS_COIN)), "one toss of three coins in the whole turn")
                self.assertEqual(0, moved(duel, code, H.LOCATION_MZONE, H.LOCATION_HAND), "the coin did not bounce it: the check is meaningful")
                self.assertFalse(seen[1], "the once-per-turn limit holds across both Main Phases")


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class TreebornFrogSharedTest(unittest.TestCase):
    """Card FAQ (Konami-hosted 2008-12-15, page S-T; counted under the owner's decision of 2026-09-29): "If the
    effect of "Treeborn Frog" is negated, you can activate its effect again during the same Standby Phase and
    Special Summon it." and "If you Special Summon "Treeborn Frog" during your Standby Phase, then it's sent to the
    Graveyard during that same Standby Phase (like if it's Tributed for "Enemy Controller"), you can Special Summon
    "Treeborn Frog" again that same Standby Phase." The era text has no use limit; the modern card is "Once per
    turn". Each scenario uses one standing effect of the scenario's own (a negation, or a send to the Graveyard),
    limited to one use, so a period card that could repeat has something to repeat after."""

    NEGATE_FIRST = (
        "local e=Effect.GlobalEffect()\n"
        "e:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)\n"
        "e:SetCode(EVENT_CHAINING)\n"
        "e:SetCountLimit(1)\n"
        f"e:SetCondition(function(e,tp,eg,ep,ev,re,r,rp) return re:GetHandler():IsCode({FROG_MODERN}) end)\n"
        "e:SetOperation(function(e,tp,eg,ep,ev,re,r,rp) Duel.NegateActivation(ev) end)\n"
        "Duel.RegisterEffect(e,0)\n"
    )
    SEND_FIRST_SUMMON_AWAY = (
        "local e=Effect.GlobalEffect()\n"
        "e:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)\n"
        "e:SetCode(EVENT_SPSUMMON_SUCCESS)\n"
        "e:SetCountLimit(1)\n"
        f"e:SetCondition(function(e,tp,eg,ep,ev,re,r,rp) return eg:IsExists(Card.IsCode,1,nil,{FROG_MODERN}) end)\n"
        "e:SetOperation(function(e,tp,eg,ep,ev,re,r,rp) Duel.SendtoGrave(eg,REASON_EFFECT) end)\n"
        "Duel.RegisterEffect(e,0)\n"
    )

    def _run(self, code: int, mode: int, extra: str):
        setup = f"Debug.AddCard({code},0,0,LOCATION_GRAVE,0,POS_FACEUP)\n" + extra
        offers = Offers(code)
        duel = run_scenario(setup, mode, idle=H.answer_idle(7), offers=offers, turns=1)
        return duel

    @in_both_formats
    def test_a_negated_activation_can_be_made_again_in_the_same_standby_phase(self, mode):
        modern = self._run(FROG_MODERN, mode, self.NEGATE_FIRST)
        historical = self._run(FROG_HISTORICAL, mode, self.NEGATE_FIRST)
        self.assertEqual([FROG_MODERN], chained_codes(modern), "once per turn: the negated activation used it up")
        self.assertEqual(0, moved(modern, FROG_MODERN, H.LOCATION_GRAVE, H.LOCATION_MZONE))
        self.assertEqual([FROG_HISTORICAL] * 2, chained_codes(historical), "no limit: it is activated again")
        self.assertEqual(1, moved(historical, FROG_HISTORICAL, H.LOCATION_GRAVE, H.LOCATION_MZONE))

    @in_both_formats
    def test_a_frog_sent_away_after_its_summon_can_be_summoned_again_like_the_modern_card(self, mode):
        # The FAQ's second entry. It is NOT a difference in the engine: a card that has left the field is a new
        # card as far as its "once per turn" is concerned, so the modern script also lets the Frog return. The
        # test pins that, so the difference above cannot be mistaken for this one.
        for code in (FROG_MODERN, FROG_HISTORICAL):
            with self.subTest(card=code):
                duel = self._run(code, mode, self.SEND_FIRST_SUMMON_AWAY)
                self.assertEqual([code] * 2, chained_codes(duel))
                self.assertEqual(2, moved(duel, code, H.LOCATION_GRAVE, H.LOCATION_MZONE), "summoned twice")
                self.assertEqual(1, moved(duel, code, H.LOCATION_MZONE, H.LOCATION_GRAVE), "sent away once")

    @in_both_formats
    def test_an_ordinary_standby_phase_special_summons_it_once_like_the_modern_card(self, mode):
        for code in (FROG_MODERN, FROG_HISTORICAL):
            with self.subTest(card=code):
                duel = self._run(code, mode, "")
                self.assertEqual([code], chained_codes(duel))
                self.assertEqual(1, moved(duel, code, H.LOCATION_GRAVE, H.LOCATION_MZONE))


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class DiceRerollSharedTest(unittest.TestCase):
    """Card FAQ (UDE 2005-07-01, Konami-hosted 2008-12-15; counted under the owner's decision of
    2026-09-29): "You activate "Dice Re-Roll" before you activate the effect which will let you roll a
    die. Then you can use the effect of "Dice Re-Roll" once during the turn in which you activated it."
    So each activation has its own re-roll. The modern card: "(You can only gain this effect once per
    turn.)" - one re-roll per turn however many copies are activated.

    The scenario is the one the ruling describes and no more: each copy is activated BEFORE the die roll
    it answers (two Dark Master - Zorc give two separate rolls in one turn). No copy ever re-rolls an
    already re-rolled result: no ruling read covers that (round 034's scenario did it, and was dropped)."""

    def _run(self, reroll: int, mode: int, copies: int):
        setup = "".join(
            f"Debug.AddCard({ZORC_MODERN},0,0,LOCATION_MZONE,{seq},POS_FACEUP_ATTACK,true)\n" for seq in range(copies)
        )
        setup += f"Debug.AddCard({GIANT_RAT},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        setup += "".join(f"Debug.AddCard({reroll},0,0,LOCATION_SZONE,{seq},POS_FACEDOWN)\n" for seq in range(copies))
        plan = [code for _ in range(copies) for code in (reroll, ZORC_MODERN)]
        state = {"step": 0}

        def idle(prompt):
            activatable = [code for code, _seq in H.idle_lists(prompt)["activatable"]]
            if state["step"] < len(plan) and plan[state["step"]] in activatable:
                code = plan[state["step"]]
                state["step"] += 1
                return H.answer_idle(5, activatable.index(code))
            return H.answer_idle(7)

        duel = run_scenario(setup, mode, idle=idle)
        self.assertEqual(len(plan), state["step"], "every planned activation was made")
        return duel

    @in_both_formats
    def test_a_second_activation_in_the_turn_gives_a_second_re_roll(self, mode):
        modern = self._run(DICE_MODERN, mode, copies=2)
        historical = self._run(DICE_HISTORICAL, mode, copies=2)
        self.assertEqual(
            [DICE_MODERN, ZORC_MODERN] * 2,
            [c for c in chained_codes(modern) if c in (DICE_MODERN, ZORC_MODERN)],
        )
        self.assertEqual(
            [DICE_HISTORICAL, ZORC_MODERN] * 2,
            [c for c in chained_codes(historical) if c in (DICE_HISTORICAL, ZORC_MODERN)],
        )
        self.assertEqual(3, len(modern.seen(MSG_TOSS_DICE)), "two rolls and one re-roll: the flag is per player")
        self.assertEqual(4, len(historical.seen(MSG_TOSS_DICE)), "two rolls and one re-roll for each activation")

    @in_both_formats
    def test_one_activation_gives_one_re_roll_like_the_modern_card(self, mode):
        modern = self._run(DICE_MODERN, mode, copies=1)
        historical = self._run(DICE_HISTORICAL, mode, copies=1)
        self.assertEqual(2, len(modern.seen(MSG_TOSS_DICE)), "one roll and one re-roll")
        self.assertEqual(2, len(historical.seen(MSG_TOSS_DICE)))


def dark_hole_baboon(baboon: int, beast_position: str, beast: int, mode: int, copies: int = 1):
    """Dark Hole destroys `beast` with `copies` of `baboon` in hand; returns (duel, offers)."""
    setup = f"Debug.AddCard({DARK_HOLE},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n" + "".join(
        f"Debug.AddCard({baboon},0,0,LOCATION_HAND,{1 + i},POS_FACEDOWN_DEFENSE)\n" for i in range(copies)
    )
    setup += f"Debug.AddCard({beast},0,0,LOCATION_MZONE,0,{beast_position})\n"
    offers = Offers(baboon)
    duel = scenario(mode, setup + deck_fillers())
    duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Dark Hole
    duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle(7))
    duel.default_response(H.MSG_SELECT_CARD, select_minimum)
    standing_answers(duel)
    duel.default_response(H.MSG_SELECT_CHAIN, offers)
    duel.run(turns=1)
    return duel, offers


def battle_baboon(baboon: int, mode: int):
    """A Beast of the player's is destroyed in battle with `baboon` in hand; returns (duel, offers)."""
    setup = (
        f"Debug.AddCard({baboon},0,0,LOCATION_HAND,1,POS_FACEDOWN_DEFENSE)\n"
        f"Debug.AddCard({PALE_BEAST},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        f"Debug.AddCard({GIGANTES},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
    )
    offers = Offers(baboon)
    duel = run_scenario(setup, mode | DUEL_ATTACK_FIRST_TURN, idle=H.answer_idle(6), offers=offers, battle=attack_once())
    return duel, offers


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
    """Round 035 removed four generated cards, and round 036 two more (Goddess of Whim, Green Baboon) and
    stopped three proposals (round 034's Dark Master - Zorc and its strict-nomi cards), because period
    rulings show the modern card behaves as the era card did
    (docs/research/period-rulings-generated-scripts.md). Each test asserts that the lists name the modern
    code and no generated code, that no generated row or script exists, and that the modern card does
    what those rulings say. Red on the wrong behaviour: restore the generated code to a list, or put back
    the earlier script (the scratch runs in the report)."""

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


    @in_both_formats
    def test_goddess_of_whim_is_the_modern_card_and_is_used_once_per_turn(self, mode):
        # The card FAQ (Konami-hosted 2008-12-15): "It can only be used once per turn, during your Main
        # Phase." So the era card is limited to one use a turn, like the modern one.
        self._assert_the_modern_card_is_used(GODDESS_MODERN, GODDESS_RETIRED, ("2010-03-edison", "2011-09-tengu"))
        setup = (
            f"local g=Debug.AddCard({GODDESS_MODERN},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            "local probe=Effect.GlobalEffect()\n"
            "probe:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)\n"
            "probe:SetCode(EVENT_PHASE+PHASE_END)\n"
            "probe:SetCountLimit(1)\n"
            'probe:SetOperation(function() Debug.Message("ATK "..g:GetAttack()) end)\n'
            "Duel.RegisterEffect(probe,0)\n"
        )
        duel = run_scenario(setup, mode, idle=activate_capped(3))
        self.assertEqual([GODDESS_MODERN], chained_codes(duel), "a second activation is refused")
        self.assertEqual(1, len(duel.seen(MSG_TOSS_COIN)))
        atk = [int(text.split()[1]) for _kind, text in duel.log if text.startswith("ATK ")]
        self.assertIn(atk[0], (1900, 475), "950 ATK doubled or halved (rounded up)")

    @in_both_formats
    def test_green_baboon_is_the_modern_card_and_needs_a_face_up_beast_outside_the_damage_step(self, mode):
        # The UDE Netrep (2007-09-28) and the card FAQ (Konami-hosted 2008-12-15): a Beast destroyed
        # face-down does not trigger it; Konami's errata lists (2009-07-30 onward): "You cannot activate
        # the effect of this card during the Damage Step", and only 1 copy may be Special Summoned.
        self._assert_the_modern_card_is_used(BABOON_MODERN, BABOON_RETIRED, ("2010-03-edison", "2011-09-tengu"))
        duel, offers = dark_hole_baboon(BABOON_MODERN, "POS_FACEDOWN_DEFENSE", PALE_BEAST, mode)
        self.assertFalse(offers.was_offered(), "a face-down Beast does not trigger it")
        self.assertEqual(0, moved(duel, BABOON_MODERN, H.LOCATION_HAND, H.LOCATION_MZONE))
        duel, offers = battle_baboon(BABOON_MODERN, mode)
        self.assertEqual(1, moved(duel, PALE_BEAST, H.LOCATION_MZONE, H.LOCATION_GRAVE))
        self.assertFalse(offers.was_offered(), "not in the Damage Step")
        duel, offers = dark_hole_baboon(BABOON_MODERN, "POS_FACEUP_ATTACK", PALE_BEAST, mode)
        self.assertTrue(offers.was_offered(), "a face-up Beast destroyed by a card effect triggers it")
        self.assertEqual(1, moved(duel, BABOON_MODERN, H.LOCATION_HAND, H.LOCATION_MZONE))
        self.assertEqual(1, len(duel.seen(H.MSG_PAY_LPCOST)), "1000 Life Points are paid")
        duel, offers = dark_hole_baboon(BABOON_MODERN, "POS_FACEUP_ATTACK", GIGANTES, mode)
        self.assertFalse(offers.was_offered(), "a destroyed Rock is not a Beast")
        duel, offers = dark_hole_baboon(BABOON_MODERN, "POS_FACEUP_ATTACK", PALE_BEAST, mode, copies=2)
        self.assertEqual(1, moved(duel, BABOON_MODERN, H.LOCATION_HAND, H.LOCATION_MZONE), "only one copy is summoned")

    @in_both_formats
    def test_dark_master_zorc_is_the_modern_card_and_rolls_once_per_turn(self, mode):
        # The UDE Netrep (2007-10-11): "You can only roll the 6-sided die once. Ex: If you use the effect
        # during Main Phase 1, you would not be able to use it again during Main Phase 2."
        self._assert_the_modern_card_is_used(ZORC_MODERN, ZORC_RETIRED, ("2010-03-edison", "2011-09-tengu"))
        setup = (
            f"Debug.AddCard({ZORC_MODERN},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)\n"
            f"Debug.AddCard({GIANT_RAT},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({GIANT_RAT},1,1,LOCATION_MZONE,1,POS_FACEUP_ATTACK)\n"
        )
        duel = run_scenario(setup, mode, idle=activate_capped(2))
        self.assertEqual([ZORC_MODERN], chained_codes(duel), "a second roll in the turn is refused")
        self.assertEqual(1, len(duel.seen(MSG_TOSS_DICE)))

    @in_both_formats
    def test_the_five_nomi_cards_are_the_modern_cards_and_can_be_revived_after_a_proper_summon(self, mode):
        # Konami's rulebook, strategy article and Extreme Victory ruling (the class answer of round 035):
        # a monster worded "can only be Special Summoned by" can be Special Summoned again once it was
        # properly Special Summoned. All five say "can only be", none says "except".
        for name, modern, proposed in NOMI_CARDS:
            with self.subTest(card=name):
                self._assert_the_modern_card_is_used(modern, proposed, ("2010-03-edison", "2011-09-tengu"))
                self.assertIn(modern, self._reborn_candidates(modern, mode))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
