"""Engine-level regression tests for historical card behaviour.

Each test runs the SAME scenario against the historical implementation and
the modern one, asserting that the real ocgcore produces the era difference
the errata record claims. `implementation.tested: true` in data/errata/ is
backed by exactly these executions - a lua file existing is never enough.

Prerequisites (tests skip otherwise): RETROFORMATS_OCGCORE pointing at an
OCG API 11 core library, and the pinned BabelCDB + CardScripts checkouts
under RETROFORMATS_REPOS. On Windows run under WSL with DeltaBagooska's
libocgcore.so (the shipped ocgcore.dll is 32-bit; CPython is 64-bit).

    RETROFORMATS_OCGCORE=~/.cache/retroformats/engine/libocgcore.so \
    python3 -m unittest tests.engine.test_historical_behaviour -v
"""

from __future__ import annotations

import unittest

from . import harness as H

# Composite duel modes, computed from the pinned ocgapi_constants.h (the
# rule-profile flag lists expand to exactly these; see tests/test_repo_data).
DUEL_MODE_MR1 = 0xD0700
DUEL_MODE_GOAT = 0x7F80D072C

DARK_HOLE = 53129443
SUMMONED_SKULL = 70781052  # 2500 ATK: not searchable by Sangan
GIANT_RAT = 4335645  # 1400 ATK: searchable
SANGAN_MODERN = 26202165
SANGAN_GOAT = 504700178
SANGAN_PRE_ERRATA = 511002631
IMPERIAL_ORDER_MODERN = 61740673
IMPERIAL_ORDER_PRE = 511002996


def scenario(flags: int, setup: str, seed: int = 7) -> H.Duel:
    duel = H.Duel(flags=flags, seed=seed)
    duel.load_scenario(
        "Debug.ReloadFieldBegin(0x2000000,4)\n"  # DUEL_PSEUDO_SHUFFLE-free; flag param is for reload only
        "Debug.SetPlayerInfo(0,8000,0,0)\n"
        "Debug.SetPlayerInfo(1,8000,0,0)\n"
        + setup
        + "Debug.ReloadFieldEnd()\n"
    )
    duel.start()
    return duel


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class SanganEraBehaviourTest(unittest.TestCase):
    """The Sangan record's three eras, executed:
    GOAT (504700178): mandatory trigger, failed search proven by revealing
    the deck (Duel.GoatConfirm - the era verification procedure);
    pre-errata (511002631): no verification, no name-lock, no once-per-turn;
    modern (26202165): hard once per turn."""

    def _destroy_sangan(self, sangan_code: int, deck: list[int], copies: int = 1) -> H.Duel:
        setup = f"Debug.AddCard({DARK_HOLE},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
        for i, code in enumerate(deck):
            setup += f"Debug.AddCard({code},0,0,LOCATION_DECK,{i},POS_FACEDOWN_DEFENSE)\n"
        for seq in range(copies):
            setup += f"Debug.AddCard({sangan_code},0,0,LOCATION_MZONE,{seq},POS_FACEUP_ATTACK)\n"
        duel = scenario(DUEL_MODE_GOAT, setup)
        duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))  # activate Dark Hole
        duel.default_response(H.MSG_SELECT_PLACE, H.answer_place_first_free)
        duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
        duel.default_response(H.MSG_SELECT_CARD, H.answer_cards(0))
        duel.run()
        self.addCleanup(duel.close)
        return duel

    def test_goat_sangan_reveals_deck_when_search_finds_nothing(self):
        # Deck holds no <=1500 ATK monster. The GOAT-era mandatory trigger
        # still resolves and the whiffed search is proven by revealing the
        # deck (MSG_CONFIRM_CARDS), per 2005 TCG verification policy.
        duel = self._destroy_sangan(SANGAN_GOAT, [SUMMONED_SKULL] * 3)
        confirms = duel.seen(H.MSG_CONFIRM_CARDS)
        self.assertTrue(
            confirms, "GOAT Sangan must reveal the deck to prove the failed search"
        )

    def test_modern_sangan_does_not_reveal_on_empty_search(self):
        duel = self._destroy_sangan(SANGAN_MODERN, [SUMMONED_SKULL] * 3)
        self.assertFalse(
            duel.seen(H.MSG_CONFIRM_CARDS),
            "modern Sangan reveals nothing - the verification procedure is gone",
        )

    def _double_sangan_searches(self, sangan_code: int) -> int:
        duel = self._destroy_sangan(
            sangan_code, [GIANT_RAT, GIANT_RAT, SUMMONED_SKULL], copies=2
        )
        searches = [
            m
            for m in duel.moves()
            if m["from"]["location"] == H.LOCATION_DECK
            and m["to"]["location"] == H.LOCATION_HAND
        ]
        return len(searches)

    def test_pre_errata_sangan_has_no_once_per_turn(self):
        # Two pre-errata Sangans destroyed together: both mandatory triggers
        # resolve - two searches.
        self.assertEqual(2, self._double_sangan_searches(SANGAN_PRE_ERRATA))

    def test_modern_sangan_hard_once_per_turn(self):
        # The 2016 erratum's 'You can only use this effect of "Sangan" once
        # per turn' limits the pair to a single search.
        self.assertEqual(1, self._double_sangan_searches(SANGAN_MODERN))


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class ImperialOrderEraBehaviourTest(unittest.TestCase):
    """Pre-errata Imperial Order: maintenance is OPTIONAL ('pay 700 LP or
    destroy this card' - the owner chooses in their own Standby Phase).
    Modern: payment is mandatory whenever possible, in every Standby Phase."""

    def _standby(self, code: int) -> H.Duel:
        setup = (
            f"Debug.AddCard({code},0,0,LOCATION_SZONE,0,POS_FACEUP)\n"
            # give player 0 a draw so turn phases progress naturally
            f"Debug.AddCard({SUMMONED_SKULL},0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)\n"
        )
        duel = scenario(DUEL_MODE_GOAT, setup)
        self.addCleanup(duel.close)
        return duel

    def test_pre_errata_owner_chooses_and_may_let_it_die(self):
        duel = self._standby(IMPERIAL_ORDER_PRE)
        duel.respond(H.MSG_SELECT_YESNO, H.answer_int(0))  # decline the payment
        duel.run()
        self.assertTrue(
            duel.seen(H.MSG_SELECT_YESNO),
            "pre-errata Imperial Order must ASK its owner about the payment",
        )
        destroyed = [
            m for m in duel.moves() if m["to"]["location"] == H.LOCATION_GRAVE
        ]
        self.assertTrue(destroyed, "declining the payment destroys Imperial Order")
        self.assertFalse(duel.seen(H.MSG_PAY_LPCOST))

    def test_modern_payment_is_forced(self):
        duel = self._standby(IMPERIAL_ORDER_MODERN)
        duel.run()
        self.assertTrue(
            duel.seen(H.MSG_PAY_LPCOST),
            "modern Imperial Order takes its 700 LP without asking",
        )
        destroyed = [
            m for m in duel.moves() if m["to"]["location"] == H.LOCATION_GRAVE
        ]
        self.assertFalse(destroyed)


if __name__ == "__main__":
    unittest.main()
