"""Pinned-core experiment for the early OCG Main -> Battle -> Main question.

This is deliberately a research test, not a canonical Tokyo Dome profile.
It compares the default MR1-style phase flow, the same flow with
DUEL_NO_MAIN_PHASE_2, and MR1 with DUEL_OCG_OBSOLETE_IGNITION removed.
"""

from __future__ import annotations

import unittest

from . import harness as H
from .test_historical_behaviour import (
    DUEL_ATTACK_FIRST_TURN,
    DUEL_MODE_MR1,
    DUEL_MODE_MR1_NO_IGNITION_FLAG,
    GIANT_RAT,
    SUMMONED_SKULL,
)


DUEL_NO_MAIN_PHASE_2 = 0x200000


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class TokyoDomePhaseExperimentTest(unittest.TestCase):
    """Compare legal post-battle actions, not historical phase labels."""

    def _run_phase_flow(self, flags: int, go_to_main2: bool) -> tuple[list[int], list[tuple[int, ...]], int]:
        duel = H.Duel(flags=flags, seed=7)
        duel.load_scenario(
            f"Debug.ReloadFieldBegin({flags},0)\n"
            "Debug.SetPlayerInfo(0,8000,0,0)\n"
            "Debug.SetPlayerInfo(1,8000,0,0)\n"
            f"Debug.AddCard({SUMMONED_SKULL},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({GIANT_RAT},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
            "Debug.ReloadFieldEnd()\n"
        )
        duel.start()
        idle_counts: list[tuple[int, ...]] = []

        def parse_idle(prompt: H.Message) -> tuple[int, ...]:
            prompt._buf.seek(0)
            prompt.u8()  # player
            counts = []
            for entry_size in (10, 10, 7, 10, 10):
                count = prompt.u32()
                counts.append(count)
                prompt._buf.read(count * entry_size)
            counts.append(prompt.u32())  # activatable
            result = tuple(counts)
            idle_counts.append(result)
            return result

        def initial_idle(prompt: H.Message) -> bytes:
            parse_idle(prompt)
            return H.answer_idle(6)  # enter Battle Phase

        def later_idle(prompt: H.Message) -> bytes:
            counts = parse_idle(prompt)
            if counts[0]:
                return H.answer_idle(0, 0)  # Normal Summon Giant Rat
            return H.answer_idle(7)  # End Phase

        duel.respond(H.MSG_SELECT_IDLECMD, initial_idle)
        duel.respond(H.MSG_SELECT_BATTLECMD, H.answer_battle(1, 0))  # attack
        duel.respond(
            H.MSG_SELECT_BATTLECMD,
            H.answer_battle(2 if go_to_main2 else 3),
        )
        duel.default_response(H.MSG_SELECT_IDLECMD, later_idle)
        duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
        duel.default_response(H.MSG_SELECT_POSITION, H.answer_position(H.POS_FACEUP_ATTACK))
        duel.default_response(H.MSG_SELECT_PLACE, H.answer_place_first_free)
        duel.default_response(H.MSG_SELECT_CARD, H.answer_cards(0))
        try:
            duel.run(turns=1, max_steps=180)
            phases = [message.u16() for message in duel.seen(H.MSG_NEW_PHASE)]
            summons = len(duel.seen(H.MSG_SUMMONED))
            return phases, idle_counts, summons
        finally:
            duel.close()

    def test_default_mr1_keeps_post_battle_action_window(self):
        phases, idle_counts, summons = self._run_phase_flow(
            DUEL_MODE_MR1 | DUEL_ATTACK_FIRST_TURN, True
        )
        self.assertEqual([0x0001, 0x0002, 0x0004, 0x0008, 0x0100, 0x0200], phases)
        self.assertIn((1, 0, 0, 1, 0, 0), idle_counts)
        self.assertGreaterEqual(summons, 1)

    def test_no_main_phase_2_removes_the_historical_action_window(self):
        phases, idle_counts, summons = self._run_phase_flow(
            DUEL_MODE_MR1 | DUEL_ATTACK_FIRST_TURN | DUEL_NO_MAIN_PHASE_2, False
        )
        self.assertEqual([0x0001, 0x0002, 0x0004, 0x0008, 0x0200], phases)
        self.assertEqual([], idle_counts[1:])
        self.assertEqual(0, summons)

    def test_removing_obsolete_ignition_does_not_change_phase_flow(self):
        phases, idle_counts, summons = self._run_phase_flow(
            DUEL_MODE_MR1_NO_IGNITION_FLAG | DUEL_ATTACK_FIRST_TURN, True
        )
        self.assertEqual([0x0001, 0x0002, 0x0004, 0x0008, 0x0100, 0x0200], phases)
        self.assertIn((1, 0, 0, 1, 0, 0), idle_counts)
        self.assertGreaterEqual(summons, 1)


if __name__ == "__main__":
    unittest.main()
