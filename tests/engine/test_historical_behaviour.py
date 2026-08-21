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
MILLENNIUM_SHIELD = 32012841  # vanilla, ATK 0 / DEF 3000
ABARE_USHIONI = 89718302  # ignition, LOCATION_MZONE, no cost/target/condition
MALICIOUS = 9411399  # "Destiny HERO - Malicious": ignition, LOCATION_GRAVE, cost banishes itself
OOKAZI = 19523799  # Normal Spell: no target/condition/deck dependency, resolves without touching the field
VANILLA_NORMAL_SUMMON = 97017120  # "Giant Rat": Level 4 EARTH, summon doesn't itself start a chain

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
class IgnitionPriorityMatrixTest(unittest.TestCase):
    """Ignition Effect Priority (docs/research/edison-rules.md #1, corrected):
    a 2x2 behavioural matrix, independently re-derived from the pinned core
    after review flagged that the original single Mausoleum-of-the-Emperor
    test could have been validating the WRONG Edison behaviour.

    FreeChain's "case 8" (processor.cpp, the "obsolete ignition effect
    ruling" block) grants a special IMMEDIATE priority window - activate an
    Ignition Effect as Chain Link 1, before the opponent gets any response -
    gated on two independent axes that the two existing flags each couple
    together in a DIFFERENT single direction:

      gate:     "the event was EVENT_CHAIN_END, OR the turn player just
                 Normal/Special/Flip-Summoned"           (OCG_OBSOLETE_IGNITION)
             vs "any time the chain is empty in Main Phase" (TCG_FAST_EFFECT_IGNITION)
      location: LOCATION_MZONE only                        (OCG_OBSOLETE_IGNITION)
             vs unrestricted                                (TCG_FAST_EFFECT_IGNITION)

    Period rulings research (docs/research/edison-rules.md #1) concluded 2010
    TCG practice was a hybrid of these that NEITHER existing flag reproduces:
    gate = Summon success ONLY (NOT also a bare chain-end with no Summon),
    location = unrestricted. This class tests all four corners of that 2x2
    (Summon vs non-Summon chain-end x candidate in the Monster Zone vs
    elsewhere) against both existing configurations, to show precisely where
    each one matches or overreaches relative to the derived historical rule -
    scenarios A and B are exactly reproduced by MR1|TCG_FAST_EFFECT_IGNITION;
    C and D are NOT, by either configuration, and are the reason
    DUEL_TCG_FAST_EFFECT_IGNITION was NOT added to the Edison profile (see the
    dossier's Decision section) - this is an ENGINE-LEVEL KNOWN GAP, not
    something either flag combination can currently represent exactly.

    Every candidate card here is EFFECT_TYPE_IGNITION with no registered
    Cost.* callback (Abare Ushioni, Destiny HERO - Malicious's cost is a bare
    self-banish, not a SetCost callback) - a card using SetCost(Cost.PayLP)
    was tried first (Gear Golem the Moving Fortress) and never appeared as a
    case-8 candidate under ANY flag configuration, including ones that must
    logically include it; that turned out to be specific to how case 8's
    synthetic empty event interacts with a registered Cost callback, not a
    fact about the ignition-priority mechanism itself, so it was dropped as a
    test subject to avoid conflating an unrelated card-script quirk with the
    behaviour under test.

    (All scenarios must go through Debug.ReloadFieldBegin(flags, 0) - passing
    `flags` positionally with rule=0 - since ReloadFieldBegin OVERWRITES
    field::core.duel_options with its own first argument (libdebug.cpp),
    discarding whatever OCG_CreateDuel was given; `scenario()`'s docstring
    above has the full explanation.)
    """

    @staticmethod
    def _decode_idle(prompt: H.Message):
        prompt._buf.seek(0)
        prompt.u8()  # player
        lists: dict[str, list[int]] = {}
        for name, entry_size in (
            ("summonable", 10),
            ("spsummonable", 10),
            ("repositionable", 7),
            ("msetable", 10),
            ("ssetable", 10),
        ):
            count = prompt.u32()
            codes = []
            for _ in range(count):
                codes.append(prompt.u32())
                prompt._buf.read(entry_size - 4)
            lists[name] = codes
        count = prompt.u32()
        activatable = []
        for _ in range(count):
            activatable.append(prompt.u32())
            prompt.u8(); prompt.u8(); prompt.u32(); prompt.u64(); prompt.u8()
        lists["activatable"] = activatable
        return lists

    def _offered_via_priority_window(
        self, flags: int, setup: str, first_action, candidate_code: int
    ) -> bool:
        """Drive `first_action` (a callable(idle_lists) -> (action, index))
        from the very first MSG_SELECT_IDLECMD, then scan every
        MSG_SELECT_CHAIN afterwards for `candidate_code` offered to player 0 -
        i.e. specifically the IMMEDIATE case-8 priority pop-up, not merely
        "is it activatable via the normal idle-command menu" (which every
        Ignition Effect always is, unconditionally, via a completely separate
        always-on scan later in the same processor file - that is NOT what
        DUEL_OCG_OBSOLETE_IGNITION/DUEL_TCG_FAST_EFFECT_IGNITION control, and
        conflating the two was an earlier dead end in this investigation)."""
        duel = H.Duel(flags=flags, seed=7)
        duel.load_scenario(
            f"Debug.ReloadFieldBegin({flags},0)\n"
            "Debug.SetPlayerInfo(0,8000,0,0)\n"
            "Debug.SetPlayerInfo(1,8000,0,0)\n"
            + setup
            + "Debug.ReloadFieldEnd()\n"
        )
        self.addCleanup(duel.close)
        duel.start()

        def respond_idle(prompt):
            action, idx = first_action(self._decode_idle(prompt))
            return H.answer_idle(action, idx)

        duel.respond(H.MSG_SELECT_IDLECMD, respond_idle)
        duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
        duel.default_response(H.MSG_SELECT_POSITION, lambda p: H.answer_position(0x1))
        duel.default_response(H.MSG_SELECT_PLACE, H.answer_place_first_free)
        duel.run()
        for m in duel.messages:
            if m.type != H.MSG_SELECT_CHAIN:
                continue
            m._buf.seek(0)
            player = m.u8()
            m.u8(); m.u8(); m.u32(); m.u32()  # spe_count, forced, hint timings
            count = m.u32()
            codes = []
            for _ in range(count):
                codes.append(m.u32())
                m.u8(); m.u8(); m.u32()
            if player == 0 and candidate_code in codes:
                return True
        return False

    def _scenario_summon_mzone(self, flags: int) -> bool:
        # A: successful Summon (of a DIFFERENT card), candidate already on
        # the Monster Zone. Historically expected: offered.
        setup = (
            f"Debug.AddCard({ABARE_USHIONI},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({VANILLA_NORMAL_SUMMON},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
        )
        return self._offered_via_priority_window(
            flags, setup,
            lambda lists: (0, lists["summonable"].index(VANILLA_NORMAL_SUMMON)),
            ABARE_USHIONI,
        )

    def _scenario_summon_gy(self, flags: int) -> bool:
        # B: successful Summon (of a DIFFERENT card), candidate in the GY -
        # the "Destiny HERO - Malicious" case period rulings describe.
        # Historically expected: offered (does not have to be the summoned
        # monster, does not have to be on the Monster Zone).
        setup = (
            f"Debug.AddCard({MALICIOUS},0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({MALICIOUS},0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({VANILLA_NORMAL_SUMMON},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
        )
        return self._offered_via_priority_window(
            flags, setup,
            lambda lists: (0, lists["summonable"].index(VANILLA_NORMAL_SUMMON)),
            MALICIOUS,
        )

    def _scenario_chainend_mzone(self, flags: int) -> bool:
        # C: a chain resolves WITHOUT a Summon (Ookazi: no target, no
        # condition, no deck dependency, doesn't touch the field), candidate
        # on the Monster Zone. Historically expected: NOT offered - only
        # ordinary Spell Speed 2+ priority applies here, not Ignition Effect
        # Priority specifically.
        setup = (
            f"Debug.AddCard({ABARE_USHIONI},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({OOKAZI},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
        )
        return self._offered_via_priority_window(
            flags, setup,
            lambda lists: (5, lists["activatable"].index(OOKAZI)),
            ABARE_USHIONI,
        )

    def _scenario_chainend_gy(self, flags: int) -> bool:
        # D: a chain resolves WITHOUT a Summon, candidate in the GY.
        # Historically expected: NOT offered (same reasoning as C).
        setup = (
            f"Debug.AddCard({MALICIOUS},0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)\n"
            f"Debug.AddCard({MALICIOUS},0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)\n"
            f"Debug.AddCard({OOKAZI},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n"
        )
        return self._offered_via_priority_window(
            flags, setup,
            lambda lists: (5, lists["activatable"].index(OOKAZI)),
            MALICIOUS,
        )

    # -- A: Summon + Monster Zone - both configs match the derived rule -----

    def test_summon_mzone_offered_under_ocg_obsolete_ignition(self):
        self.assertTrue(self._scenario_summon_mzone(DUEL_MODE_MR1))

    def test_summon_mzone_offered_under_tcg_fast_effect_ignition(self):
        self.assertTrue(
            self._scenario_summon_mzone(DUEL_MODE_MR1 | DUEL_TCG_FAST_EFFECT_IGNITION)
        )

    # -- B: Summon + Graveyard - only TCG_FAST_EFFECT_IGNITION matches ------

    def test_summon_gy_not_offered_under_ocg_obsolete_ignition_alone(self):
        # MR1's location==LOCATION_MZONE filter wrongly excludes this,
        # relative to the derived Edison rule (Destiny HERO - Malicious from
        # the GY, right after Summoning something else, is exactly the
        # period-rulings example this scenario models).
        self.assertFalse(self._scenario_summon_gy(DUEL_MODE_MR1))

    def test_summon_gy_offered_under_tcg_fast_effect_ignition(self):
        self.assertTrue(
            self._scenario_summon_gy(DUEL_MODE_MR1 | DUEL_TCG_FAST_EFFECT_IGNITION)
        )

    # -- C, D: non-Summon chain-end - a KNOWN ENGINE GAP, not reproduced by --
    # -- either flag combination; these tests pin the CURRENT (imperfect)  --
    # -- engine behaviour so a future engine change that closes the gap is --
    # -- noticed, not silently re-broken. See docs/research/edison-rules.md #1.

    def test_chainend_mzone_is_wrongly_offered_under_ocg_obsolete_ignition(self):
        # KNOWN GAP: the derived Edison rule says this should NOT be offered
        # (no Summon happened) - plain MR1 offers it anyway, because its gate
        # is "chain-end OR Summon", not "Summon only".
        self.assertTrue(self._scenario_chainend_mzone(DUEL_MODE_MR1))

    def test_chainend_mzone_is_wrongly_offered_under_tcg_fast_effect_ignition(self):
        # KNOWN GAP: same as above - TCG_FAST_EFFECT_IGNITION's gate is "any
        # empty chain in Main Phase", which is even broader than MR1's.
        self.assertTrue(
            self._scenario_chainend_mzone(DUEL_MODE_MR1 | DUEL_TCG_FAST_EFFECT_IGNITION)
        )

    def test_chainend_gy_not_offered_under_ocg_obsolete_ignition(self):
        # Matches the derived rule here, but ONLY because MR1's
        # location==LOCATION_MZONE filter happens to also exclude it - not
        # because the gate correctly excludes non-Summon chain-ends (test
        # above proves it doesn't). Kept to document that MR1's "accidental"
        # correctness does not generalise to scenario C.
        self.assertFalse(self._scenario_chainend_gy(DUEL_MODE_MR1))

    def test_chainend_gy_is_wrongly_offered_under_tcg_fast_effect_ignition(self):
        # KNOWN GAP: the derived Edison rule says this should NOT be offered.
        # This is the scenario the original (pre-correction) version of this
        # test suite got backwards: it used Mausoleum of the Emperor (a Field
        # Zone ignition effect, i.e. this exact C/D shape) via Dark Hole (a
        # non-Summon chain-end) and asserted TCG_FAST_EFFECT_IGNITION
        # offering it was the DESIRED Edison behaviour. Per the corrected
        # research, that was demonstrating exactly the overreach this test
        # now documents as wrong, which is why DUEL_TCG_FAST_EFFECT_IGNITION
        # is NOT in the Edison profile.
        self.assertTrue(
            self._scenario_chainend_gy(DUEL_MODE_MR1 | DUEL_TCG_FAST_EFFECT_IGNITION)
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
