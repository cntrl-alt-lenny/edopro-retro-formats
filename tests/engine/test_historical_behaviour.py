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
RESCUE_CAT_MODERN = 14878871
RESCUE_CAT_PRE_ERRATA = 511002992
NIMBLE_MOMONGA = 22567609  # Level 2 Beast: legal Rescue Cat target
MAUSOLEUM_OF_THE_EMPEROR = 80921533  # Field Spell, ignition effect, LOCATION_FZONE
DARK_HOLE = 53129443
GIANT_RAT = 4335645
MILLENNIUM_SHIELD = 32012841  # vanilla, ATK 0 / DEF 3000

# Individual flags this test module checks in isolation, beyond the composite
# modes above (values from the pinned ocgapi_constants.h; docs/research/
# edison-rules.md records the source line for each).
DUEL_ATTACK_FIRST_TURN = 0x02  # not era-relevant here - only lets the puzzle attack on turn 1
DUEL_0_ATK_DESTROYED = 0x10000000
DUEL_TCG_FAST_EFFECT_IGNITION = 0x400000000


def scenario(flags: int, setup: str, seed: int = 7) -> H.Duel:
    duel = H.Duel(flags=flags, seed=seed)
    duel.load_scenario(
        # Debug.ReloadFieldBegin(flag, rule, build) OVERWRITES field::core.duel_options
        # with `flag` (libdebug.cpp ReloadFieldBegin: `pduel->game_field->core.duel_options
        # = flag`, run AFTER OCG_CreateDuel already set it from `flags` via field::field()
        # at field.cpp:68) - so `flag` here must be the SAME `flags` the scenario was built
        # with, or the intended duel-options are silently discarded and every scenario runs
        # under whatever `flag`/`rule` happened to be hardcoded instead. `rule=0` skips the
        # rule>0-implies-OR-in-a-DUEL_MODE_MR<rule> convenience the API also offers (a bare
        # 1-5 forwarded as `rule` ORs in that MR preset on top of `flag`; we pass our own
        # complete flag set instead, so no preset should be added on top).
        f"Debug.ReloadFieldBegin({flags},0)\n"
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
        duel.run(turns=1)
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
class RescueCatEraBehaviourTest(unittest.TestCase):
    """Rescue Cat's 2017 erratum (DUSA-EN072) added a hard once-per-turn.
    Edison plays the pre-errata card (511002992), which EdisonFormat.com's
    Functional Errata list independently describes as having "no 'once per
    name' restriction"."""

    def _both_cats_try(self, cat_code: int) -> int:
        setup = ""
        for i, code in enumerate([NIMBLE_MOMONGA] * 4):
            setup += f"Debug.AddCard({code},0,0,LOCATION_DECK,{i},POS_FACEDOWN_DEFENSE)\n"
        setup += f"Debug.AddCard({cat_code},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
        setup += f"Debug.AddCard({cat_code},0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)\n"
        duel = scenario(DUEL_MODE_MR1, setup)
        self.addCleanup(duel.close)
        # Keep activating for as long as the engine offers an effect - the
        # once-per-turn is what decides when it stops, not the script.
        duel.default_response(H.MSG_SELECT_IDLECMD, H.answer_idle_activate_or_end)
        duel.default_response(H.MSG_SELECT_PLACE, H.answer_place_first_free)
        duel.default_response(H.MSG_SELECT_POSITION, H.answer_position(H.POS_FACEUP_ATTACK))
        duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
        duel.default_response(H.MSG_SELECT_CARD, H.answer_cards(0, 1))
        duel.run(turns=1)
        return len(
            [
                m
                for m in duel.moves()
                if m["from"]["location"] == H.LOCATION_DECK
                and m["to"]["location"] == H.LOCATION_MZONE
            ]
        )

    def test_pre_errata_rescue_cat_has_no_once_per_turn(self):
        # Two pre-errata copies each Special Summon a pair: four monsters.
        self.assertEqual(4, self._both_cats_try(RESCUE_CAT_PRE_ERRATA))

    def test_modern_rescue_cat_is_hard_once_per_turn(self):
        self.assertEqual(2, self._both_cats_try(RESCUE_CAT_MODERN))


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
        duel.run(turns=1)
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
        duel.run(turns=1)
        self.assertTrue(
            duel.seen(H.MSG_PAY_LPCOST),
            "modern Imperial Order takes its 700 LP without asking",
        )
        destroyed = [
            m for m in duel.moves() if m["to"]["location"] == H.LOCATION_GRAVE
        ]
        self.assertFalse(destroyed)


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class IgnitionPriorityFlagTest(unittest.TestCase):
    """DUEL_TCG_FAST_EFFECT_IGNITION vs the OCG_OBSOLETE_IGNITION already in
    every MR1-based profile (docs/research/edison-rules.md #1): after a chain
    resolves (EVENT_CHAIN_END), the engine offers an automatic priority
    chain-window for ignition effects, queued from `case 8` in
    field::process(Processors::PointEvent) (processor.cpp). With ONLY
    OCG_OBSOLETE_IGNITION, the candidate scan filters to
    `phandler->current.location == LOCATION_MZONE` - a Field Spell's ignition
    effect is never offered this way. With DUEL_TCG_FAST_EFFECT_IGNITION, that
    location filter is bypassed entirely (`is_flag(...) || location==MZONE`),
    so the SAME Field Spell effect IS offered.

    Mausoleum of the Emperor (Field Spell, ignition, LOCATION_FZONE) makes
    this the cleanest observable case: activate Dark Hole (destroys a monster,
    chain resolves), then check whether the very next MSG_SELECT_CHAIN for
    the turn player lists Mausoleum's code as a candidate.

    (Both configurations must go through Debug.ReloadFieldBegin(flags, 0) -
    passing `flags` positionally with rule=0, not a hardcoded (0x2000000,4) -
    since ReloadFieldBegin OVERWRITES field::core.duel_options with its own
    first argument (libdebug.cpp), discarding whatever OCG_CreateDuel was
    given. `scenario()` above was fixed to do this; a test that bypasses it
    would silently exercise the wrong flags for BOTH configurations, which is
    exactly the failure mode that produced no observable difference in early
    manual probing of this same flag pair before the fix.)
    """

    def _mausoleum_priority_after_chain_end(self, flags: int) -> bool:
        duel = H.Duel(flags=flags, seed=7)
        duel.load_scenario(
            f"Debug.ReloadFieldBegin({flags},0)\n"
            "Debug.SetPlayerInfo(0,8000,0,0)\n"
            "Debug.SetPlayerInfo(1,8000,0,0)\n"
            f"Debug.AddCard({MAUSOLEUM_OF_THE_EMPEROR},0,0,LOCATION_FZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({SUMMONED_SKULL},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({DARK_HOLE},0,0,LOCATION_HAND,1,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({GIANT_RAT},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            "Debug.ReloadFieldEnd()\n"
        )
        self.addCleanup(duel.close)
        duel.start()
        # Two ignition-type effects are offered from hand at Main Phase 1
        # start: Mausoleum's own "activate" wrapper (index 0) and Dark Hole
        # (index 1) - Mausoleum's own activation isn't what's under test here.
        duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 1))  # activate Dark Hole
        duel.default_response(H.MSG_SELECT_PLACE, H.answer_place_first_free)
        duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
        duel.run()
        chain_end_at = next(
            i for i, m in enumerate(duel.messages) if m.type == H.MSG_CHAIN_END
        )
        for m in duel.messages[chain_end_at + 1 :]:
            if m.type != H.MSG_SELECT_CHAIN:
                continue
            m._buf.seek(0)
            player = m.u8()
            m.u8()  # spe_count
            m.u8()  # forced
            m.u32()  # hint timing 1
            m.u32()  # hint timing 2
            count = m.u32()
            codes = []
            for _ in range(count):
                codes.append(m.u32())
                m.u8()
                m.u8()
                m.u32()
            if player == 0 and MAUSOLEUM_OF_THE_EMPEROR in codes:
                return True
        return False

    def test_ocg_obsolete_ignition_alone_excludes_field_spell(self):
        # Negative control: plain MR1 (rules-tcg-goat's baseline, and the
        # Edison profile's own baseline before docs/research/edison-rules.md
        # #1 added DUEL_TCG_FAST_EFFECT_IGNITION on top of it). This must
        # FAIL to offer Mausoleum here, proving the OCG-style condition alone
        # does not grant Field/Spell-zone ignition priority - the divergence
        # the next test shows the flag actually fixes.
        self.assertFalse(
            self._mausoleum_priority_after_chain_end(DUEL_MODE_MR1),
            "plain MR1 (OCG_OBSOLETE_IGNITION only) must not offer a "
            "Field Spell's ignition effect via the priority chain window",
        )

    def test_tcg_fast_effect_ignition_offers_field_spell(self):
        self.assertTrue(
            self._mausoleum_priority_after_chain_end(
                DUEL_MODE_MR1 | DUEL_TCG_FAST_EFFECT_IGNITION
            ),
            "DUEL_TCG_FAST_EFFECT_IGNITION must offer a Field Spell's "
            "ignition effect via the priority chain window right after a "
            "chain ends - the location filter is bypassed for this flag",
        )


@unittest.skipUnless(H.available(), "ocgcore + pinned checkouts not available")
class ZeroAtkBattleFlagTest(unittest.TestCase):
    """DUEL_0_ATK_DESTROYED (docs/research/edison-rules.md #4): two monsters
    with equal ATK destroy each other in battle by default UNLESS that ATK is
    0, per processor.cpp's battle-damage-calculation tie branch
    (`if(a != 0 || is_flag(DUEL_0_ATK_DESTROYED)) { bd[0]=bd[1]=true; }`).
    Two 0-ATK monsters (Millennium Shield, vanilla) battling each other are
    therefore destroyed only with the flag set."""

    def _both_zero_atk_destroyed(self, flags: int) -> int:
        duel = H.Duel(flags=flags, seed=7)
        duel.load_scenario(
            f"Debug.ReloadFieldBegin({flags},0)\n"
            "Debug.SetPlayerInfo(0,8000,0,0)\n"
            "Debug.SetPlayerInfo(1,8000,0,0)\n"
            f"Debug.AddCard({MILLENNIUM_SHIELD},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({MILLENNIUM_SHIELD},1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            "Debug.ReloadFieldEnd()\n"
        )
        self.addCleanup(duel.close)
        duel.start()
        duel.respond(H.MSG_SELECT_IDLECMD, lambda p: H.answer_idle(6))  # to Battle Phase
        duel.default_response(H.MSG_SELECT_IDLECMD, lambda p: H.answer_idle(7))  # else: to End Phase
        duel.respond(H.MSG_SELECT_BATTLECMD, lambda p: H.answer_battle(1, 0))  # attack
        duel.default_response(H.MSG_SELECT_BATTLECMD, lambda p: H.answer_battle(3))  # else: to End
        duel.default_response(H.MSG_SELECT_CARD, H.answer_cards(0))
        duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
        duel.run(turns=1)
        destroyed = [
            m
            for m in duel.moves()
            if m["code"] == MILLENNIUM_SHIELD
            and m["from"]["location"] == H.LOCATION_MZONE
            and m["to"]["location"] == H.LOCATION_GRAVE
        ]
        return len(destroyed)

    def test_modern_default_neither_zero_atk_monster_is_destroyed(self):
        # Negative control: plain MR1 (rules-tcg-goat's baseline, and the
        # Edison profile's own baseline before docs/research/edison-rules.md
        # #6 added DUEL_0_ATK_DESTROYED on top of it). This must FAIL to
        # destroy either monster, matching the modern default and showing
        # the divergence the next test shows the flag actually fixes.
        self.assertEqual(
            0,
            self._both_zero_atk_destroyed(DUEL_MODE_MR1 | DUEL_ATTACK_FIRST_TURN),
            "without DUEL_0_ATK_DESTROYED, two 0-ATK monsters tying in "
            "battle must NOT be destroyed (modern default)",
        )

    def test_flag_destroys_both_zero_atk_monsters(self):
        self.assertEqual(
            2,
            self._both_zero_atk_destroyed(
                DUEL_MODE_MR1 | DUEL_0_ATK_DESTROYED | DUEL_ATTACK_FIRST_TURN
            ),
            "DUEL_0_ATK_DESTROYED must destroy BOTH 0-ATK monsters in a tied battle",
        )


if __name__ == "__main__":
    unittest.main()
