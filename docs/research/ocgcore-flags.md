> Point-in-time research note (2026-08-19), verified against the pinned revisions in data/sources.json.

# ocgcore duel-mode / rule flags — research note

Date: 2026-08-19
Sources examined:
- `/workspace/edo9300/ygopro-core` (standalone clone of edo9300/ygopro-core, HEAD = `46779fbe40e6a9bd8967f5dc6a03f4eaa6550d57`, 2026-08-19)
- Pinned EDOPro submodule commit `158aebe758be3c46249c75d602e3f16d63d2ef31` (fetched into the clone via `git fetch --depth 1 origin <sha>`; the clone is shallow and did not contain it initially)
- `/home/user/edopro` (EDOPro client, HEAD = `9d6fb3e8417c88008ba1e08b5b7f751cbdba82ac`)

Important location note (CONFIRMED): at current ocgcore master the `DUEL_*` flags are **not** in `common.h` anymore — `common.h` only contains engine-internal symbols and `#include "ocgapi_constants.h"` (common.h:33). The flags live in `/workspace/edo9300/ygopro-core/ocgapi_constants.h:378-428`. At the pinned EDOPro commit `158aebe7` they were still in `common.h` (lines 421-470 of that revision).

---

## 1. Complete DUEL_* flag list (CONFIRMED, ocgapi_constants.h:379-415; identical values at pinned commit 158aebe7 common.h:421-457)

| Flag | Hex value | Bit |
|---|---|---|
| `DUEL_TEST_MODE` | `0x01` | 0 |
| `DUEL_ATTACK_FIRST_TURN` | `0x02` | 1 |
| `DUEL_USE_TRAPS_IN_NEW_CHAIN` | `0x04` | 2 |
| `DUEL_6_STEP_BATLLE_STEP` (sic, typo in source) | `0x08` | 3 |
| `DUEL_PSEUDO_SHUFFLE` | `0x10` | 4 |
| `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE` | `0x20` | 5 |
| `DUEL_SIMPLE_AI` | `0x40` | 6 |
| `DUEL_RELAY` | `0x80` | 7 |
| `DUEL_OCG_OBSOLETE_IGNITION` | `0x100` | 8 |
| `DUEL_1ST_TURN_DRAW` | `0x200` | 9 |
| `DUEL_1_FACEUP_FIELD` | `0x400` | 10 |
| `DUEL_PZONE` | `0x800` | 11 |
| `DUEL_SEPARATE_PZONE` | `0x1000` | 12 |
| `DUEL_EMZONE` | `0x2000` | 13 |
| `DUEL_FSX_MMZONE` | `0x4000` | 14 |
| `DUEL_TRAP_MONSTERS_NOT_USE_ZONE` | `0x8000` | 15 |
| `DUEL_RETURN_TO_DECK_TRIGGERS` | `0x10000` | 16 |
| `DUEL_TRIGGER_ONLY_IN_LOCATION` | `0x20000` | 17 |
| `DUEL_SPSUMMON_ONCE_OLD_NEGATE` | `0x40000` | 18 |
| `DUEL_CANNOT_SUMMON_OATH_OLD` | `0x80000` | 19 |
| `DUEL_NO_STANDBY_PHASE` | `0x100000` | 20 |
| `DUEL_NO_MAIN_PHASE_2` | `0x200000` | 21 |
| `DUEL_3_COLUMNS_FIELD` | `0x400000` | 22 |
| `DUEL_DRAW_UNTIL_5` | `0x800000` | 23 |
| `DUEL_NO_HAND_LIMIT` | `0x1000000` | 24 |
| `DUEL_UNLIMITED_SUMMONS` | `0x2000000` | 25 |
| `DUEL_INVERTED_QUICK_PRIORITY` | `0x4000000` | 26 |
| `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET` | `0x8000000` | 27 |
| `DUEL_0_ATK_DESTROYED` | `0x10000000` | 28 |
| `DUEL_STORE_ATTACK_REPLAYS` | `0x20000000` | 29 |
| `DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP` | `0x40000000` | 30 |
| `DUEL_CAN_REPOS_IF_NON_SUMPLAYER` | `0x80000000` | 31 |
| `DUEL_TCG_SEGOC_NONPUBLIC` | `0x100000000` | 32 |
| `DUEL_TCG_SEGOC_FIRSTTRIGGER` | `0x200000000` | 33 |
| `DUEL_TCG_FAST_EFFECT_IGNITION` | `0x400000000` | 34 |
| `DUEL_EXTRA_DECK_RITUAL` | `0x800000000` | 35 |
| `DUEL_NORMAL_SUMMON_FACEUP_DEF` | `0x1000000000` | 36 |

### Composite mode defines (CONFIRMED, ocgapi_constants.h:416-428) with computed values

| Composite | Definition (verbatim member flags) | Computed hex |
|---|---|---|
| `DUEL_MODE_SPEED` | 3_COLUMNS_FIELD \| NO_MAIN_PHASE_2 \| TRAP_MONSTERS_NOT_USE_ZONE \| TRIGGER_ONLY_IN_LOCATION | `0x628000` |
| `DUEL_MODE_RUSH` | 3_COLUMNS_FIELD \| NO_MAIN_PHASE_2 \| NO_STANDBY_PHASE \| 1ST_TURN_DRAW \| INVERTED_QUICK_PRIORITY \| DRAW_UNTIL_5 \| NO_HAND_LIMIT \| UNLIMITED_SUMMONS \| TRAP_MONSTERS_NOT_USE_ZONE \| TRIGGER_ONLY_IN_LOCATION \| EXTRA_DECK_RITUAL | `0x807F28200` |
| `DUEL_MODE_MR1` | OCG_OBSOLETE_IGNITION \| 1ST_TURN_DRAW \| 1_FACEUP_FIELD \| SPSUMMON_ONCE_OLD_NEGATE \| RETURN_TO_DECK_TRIGGERS \| CANNOT_SUMMON_OATH_OLD | `0xD0700` |
| `DUEL_MODE_GOAT` | MODE_MR1 \| TCG_FAST_EFFECT_IGNITION \| USE_TRAPS_IN_NEW_CHAIN \| 6_STEP_BATLLE_STEP \| TRIGGER_WHEN_PRIVATE_KNOWLEDGE \| EQUIP_NOT_SENT_IF_MISSING_TARGET \| 0_ATK_DESTROYED \| STORE_ATTACK_REPLAYS \| SINGLE_CHAIN_IN_DAMAGE_SUBSTEP \| CAN_REPOS_IF_NON_SUMPLAYER \| TCG_SEGOC_NONPUBLIC \| TCG_SEGOC_FIRSTTRIGGER | `0x7F80D072C` |
| `DUEL_MODE_MR2` | 1ST_TURN_DRAW \| 1_FACEUP_FIELD \| SPSUMMON_ONCE_OLD_NEGATE \| RETURN_TO_DECK_TRIGGERS \| CANNOT_SUMMON_OATH_OLD | `0xD0600` |
| `DUEL_MODE_MR3` | PZONE \| SEPARATE_PZONE \| SPSUMMON_ONCE_OLD_NEGATE \| RETURN_TO_DECK_TRIGGERS \| CANNOT_SUMMON_OATH_OLD | `0xD1800` |
| `DUEL_MODE_MR4` | PZONE \| EMZONE \| SPSUMMON_ONCE_OLD_NEGATE \| RETURN_TO_DECK_TRIGGERS \| CANNOT_SUMMON_OATH_OLD | `0xD2800` |
| `DUEL_MODE_MR5` | PZONE \| EMZONE \| FSX_MMZONE \| TRAP_MONSTERS_NOT_USE_ZONE \| TRIGGER_ONLY_IN_LOCATION | `0x2E800` |

Cross-check (CONFIRMED): EDOPro's default `lastDuelParam` is `0x2E800` with comment `//#define DUEL_MODE_MR5` (`/home/user/edopro/gframe/game_config.inl:22`), matching the computed MR5 value.

The `DUEL_MODE_MR*_FORB` defines (ocgapi_constants.h:424-428) are **not duel flags** — they are `TYPE_*` bitmasks of card types banned from decks for that mode (MR1_FORB = XYZ|PENDULUM|LINK, MR2_FORB = PENDULUM|LINK, MR3_FORB = LINK, MR4/MR5_FORB = 0). They are enforced entirely client/server-side in deck checking (`/home/user/edopro/gframe/deck_manager.cpp:204-206`, sent as `HostInfo::forbiddentypes`), never passed to ocgcore.

### GOAT vs MR1 diff (CONFIRMED)

`DUEL_MODE_GOAT = DUEL_MODE_MR1 | <11 extra flags>`. GOAT **removes nothing** from MR1 (pure superset; `GOAT & ~MR1 = 0x7F800002C`). Extra flags added, with at least one engine usage site and plain-language effect each:

1. **`DUEL_TCG_FAST_EFFECT_IGNITION` (0x400000000)** — processor.cpp:797/809/826. The gate at :797 opens the "obsolete ignition" block if either this or `DUEL_OCG_OBSOLETE_IGNITION` is set, in Main Phase 1/2. With the TCG flag, the turn player's ignition effects are queued as `ignition_priority_chains` at *any* point where the chain is empty (`core.current_chain.size() == 0`, :809) and from any location (:826); with only the OCG flag, this happens only after a chain end or a successful Normal/Special/Flip Summon by the turn player (`check_events_ocg`, :800-808) and only for monsters in the Monster Zone (:826). Plainly: the turn player may activate ignition effects "with priority" before the opponent can respond — the TCG variant is broader than the OCG variant. (Historical mapping to pre-March-2011 "ignition priority" is a game-history claim — needs external sourcing.)
2. **`DUEL_USE_TRAPS_IN_NEW_CHAIN` (0x4)** — processor.cpp:3754. `get_cteffect` (field.cpp:3143-3183) identifies a Continuous Trap (`TYPE_TRAP|TYPE_CONTINUOUS`) whose activation is a bare "free chain" activation and which has separate trigger/quick effects currently usable. Without the flag, on activating such a trap the engine asks the player (prompt 94, processor.cpp:3761) whether to also use one of its effects as part of the same chain link; **with the flag (GOAT) that combined activation is disabled** — the card activation and its effects must go in separate chains.
3. **`DUEL_6_STEP_BATLLE_STEP` (0x8)** — processor.cpp:2305, 2345, 2585. With the flag, the open chain window at the start of the Damage Step (hint event 40, :2307-2315) is only opened when there is actually a trigger to resolve, and the "before damage calculation" window (hint 41, :2345-2356) is skipped when the previous sub-step already consumed the only trigger window — i.e. the Damage Step has fewer distinct timing windows (an older, 6-step damage-step structure per the flag name; exact historical step mapping needs external sources).
4. **`DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE` (0x20)** — effect.cpp:236, 256; processor.cpp:632/711/714/3714; field.cpp:3261. With the flag, `check_trigger_effect` returns TRUE unconditionally for private-knowledge cases (field.cpp:3261-3262), and effects whose handler is in the Deck or face-down Extra Deck remain activatable (effect.cpp:256-263 is skipped). Plainly: trigger effects still fire even when only their owner can know the card is where it is (in deck / face-down extra / hand), instead of being silently dropped.
5. **`DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET` (0x8000000)** — operations.cpp:1688. When an equip's target is no longer a face-up monster in the Monster Zone, the engine normally sends the equip card to the GY; with the flag, if the equip card is (still) being treated while in the Monster Zone context the equip action simply fails without sending the card to the GY.
6. **`DUEL_0_ATK_DESTROYED` (0x10000000)** — processor.cpp:2974. In an ATK-vs-ATK battle that ties, both monsters are destroyed only if ATK != 0 by default; with the flag, **two 0-ATK monsters battling each other also destroy each other**.
7. **`DUEL_STORE_ATTACK_REPLAYS` (0x20000000)** — processor.cpp:2197, 2217. With the flag, when a replay occurs (set of attackable targets changed) the engine auto-answers the "replay?" prompt with FALSE (:2197-2198) instead of asking, and at :2217 the attack declaration is *not* counted against the monster's `announce_count` unless the attack was explicitly canceled — the replay is "stored" rather than immediately re-prompted, changing whether the monster is considered to have used up its attack. (Exact rules-history intent needs external sourcing; the mechanical effect is as described.)
8. **`DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP` (0x40000000)** — processor.cpp:2315, 2356, 2387, 2597, 2639. Passed as the `single_chain` argument to `Processors::PointEvent` during damage-step sub-steps: only one chain may be built per damage-step sub-step timing window (no second chain after the first resolves).
9. **`DUEL_CAN_REPOS_IF_NON_SUMPLAYER` (0x80000000)** — card.cpp:3272 (`is_can_be_flip_summoned`), card.cpp:3773 (position change). Normally a monster summoned/set/flipped this turn cannot change position; with the flag, the restriction only applies if the summoning player still controls it — a monster whose control changed after being summoned by the opponent **can** be repositioned/flip summoned by its new controller.
10. **`DUEL_TCG_SEGOC_NONPUBLIC` (0x100000000)** — processor.cpp:731; field.cpp:3245. Governs SEGOC (Simultaneous Effects Go On Chain) treatment of non-public triggers (hand/deck/out-of-range triggers, `check_nonpublic_trigger` field.cpp:3235-3251). Without the flag (OCG behavior), non-public optional triggers are excluded from the forced SEGOC ordering and get their own later window; with the flag (TCG behavior), the separate non-public window list is cleared (processor.cpp:731-732 `core.new_ochain_h.clear()`) — non-public triggers are placed in the same SEGOC chain-building pass as public ones.
11. **`DUEL_TCG_SEGOC_FIRSTTRIGGER` (0x200000000)** — processor.cpp:646-653, 734-741, 759. When multiple simultaneous events queued triggers, the candidate list is sorted by `event_id` and truncated to only triggers from the *first* event (:647-652) — i.e. under TCG SEGOC only effects that triggered off the earliest event are put on this chain, rather than all pending triggers being mixed together.
12. Additionally, GOAT inherits **`DUEL_OCG_OBSOLETE_IGNITION`** from MR1 and combines it with `DUEL_TCG_FAST_EFFECT_IGNITION`; since the TCG variant's conditions are a superset (processor.cpp:809, 826 test `is_flag(DUEL_TCG_FAST_EFFECT_IGNITION) || <OCG condition>`), the TCG behavior dominates when both are set.

### MR1's own flags (each with usage site)

- **`DUEL_OCG_OBSOLETE_IGNITION` (0x100)** — processor.cpp:797-835. See item 1 above: turn player can activate ignition effects of Monster-Zone monsters immediately after their summon or after a chain ends, before the opponent may respond ("summon priority").
- **`DUEL_1ST_TURN_DRAW` (0x200)** — processor.cpp:3381. The turn-1 player also draws in their Draw Phase (`is_flag(DUEL_1ST_TURN_DRAW) || infos.turn_id > 1`). Without it, no draw on the game's first turn (post-2014 rule; era mapping needs external source).
- **`DUEL_1_FACEUP_FIELD` (0x400)** — processor.cpp:4162-4168, 4294-4300; operations.cpp:4914-4917. Old Field Spell behavior: only one Field Spell is active at a time — activating yours disables the opponent's face-up Field Spell (:4164-4166) and destroys it by rule when the activation resolves (:4297-4299); replacing your own is a rule *destruction* (operations.cpp:4917) rather than the modern "send to GY" (operations.cpp:4915).
- **`DUEL_SPSUMMON_ONCE_OLD_NEGATE` (0x40000)** — processor.cpp:3861-3875, 4103, 4230, 4250; operations.cpp:3126, 3247, 3378, 3459. For cards with a "only one can be Special Summoned per..." (`spsummon_code`/`GLOBALFLAG_SPSUMMON_ONCE`) restriction: the per-duel/turn counter is incremented at activation/attempt time (and tracked in `_rst` maps so it can be rolled back), i.e. **a negated Special Summon still counts** against the once-restriction under the old ruling.
- **`DUEL_RETURN_TO_DECK_TRIGGERS` (0x10000)** — operations.cpp:38-41, 60-63; effect.cpp:256. Effects of cards whose trigger location was the Deck (or face-down Extra Deck) keep their relation even when the chain is negated/disabled, and such cards' effects remain activatable from the deck — plainly, cards returned to the Deck can still resolve/trigger their effects instead of being cut off.
- **`DUEL_CANNOT_SUMMON_OATH_OLD` (0x80000)** — field.cpp:2321-2350 (`set_spsummon_counter`); processor.cpp:3855-3859; operations.cpp:2242 etc. Changes when "cannot Special Summon"-style oath counters are applied: with the flag, per-chain counters are tracked and applied at activation (with rollback tracking `_rst`), i.e. oath restrictions of the old style bind from activation rather than resolution. (Mechanically: `set_spsummon_counter(triggering_player, true, true)` is called when a chain link with a summon op-info is activated, processor.cpp:3855-3857.)

## 2. Historical-era flags vs convenience/simulator flags

**Rule-era flags** (encode a historical TCG/OCG rule difference; grouping CONFIRMED from how the MODE_* composites use them, era attribution itself is game-history and needs external sources):
- Master-Rule zone/structure: `DUEL_PZONE`, `DUEL_SEPARATE_PZONE` (MR3 pendulum zones being dedicated zones vs sharing S/T zones — field.cpp:1251-1270), `DUEL_EMZONE` (Extra Monster Zone, field.cpp:674-848, card.cpp:1302), `DUEL_FSX_MMZONE` (MR2020: Fusion/Synchro/Xyz can go to Main Monster Zones — field.cpp:848), `DUEL_TRAP_MONSTERS_NOT_USE_ZONE` (Trap Monsters no longer occupy both an S/T and a monster zone — card.cpp:3815, operations.cpp:1605-1660).
- Old-ruling behavior: `DUEL_OCG_OBSOLETE_IGNITION`, `DUEL_TCG_FAST_EFFECT_IGNITION`, `DUEL_1ST_TURN_DRAW`, `DUEL_ATTACK_FIRST_TURN` (Battle Phase allowed on turn 1 — field.cpp:3285, processor.cpp:1463), `DUEL_1_FACEUP_FIELD`, `DUEL_SPSUMMON_ONCE_OLD_NEGATE`, `DUEL_CANNOT_SUMMON_OATH_OLD`, `DUEL_RETURN_TO_DECK_TRIGGERS`, `DUEL_TRIGGER_ONLY_IN_LOCATION` (effects only trigger while the card retains its trigger relation — field.cpp:3255; used by MR5/Speed/Rush, i.e. the *modern* strictness), `DUEL_USE_TRAPS_IN_NEW_CHAIN`, `DUEL_6_STEP_BATLLE_STEP`, `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE`, `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET`, `DUEL_0_ATK_DESTROYED`, `DUEL_STORE_ATTACK_REPLAYS`, `DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP`, `DUEL_CAN_REPOS_IF_NON_SUMPLAYER`, `DUEL_TCG_SEGOC_NONPUBLIC`, `DUEL_TCG_SEGOC_FIRSTTRIGGER`, `DUEL_NORMAL_SUMMON_FACEUP_DEF` (Normal Summon in face-up Defense allowed — field.cpp:2760-2763; used by Rush Duel scripts/format, not in any MODE_ composite).
- Note `DUEL_TCG_SEGOC_NONPUBLIC` is also used by EDOPro as the marker bit for "TCG behavior" in lobby display (`/home/user/edopro/gframe/server_lobby.cpp:128`).

**Variant-format flags** (Speed/Rush Duel, not historical TCG eras): `DUEL_3_COLUMNS_FIELD` (3-wide field — field.cpp:529-633), `DUEL_NO_MAIN_PHASE_2` (processor.cpp:1864, 3529), `DUEL_NO_STANDBY_PHASE` (processor.cpp:3408), `DUEL_DRAW_UNTIL_5` (draw up to 5 — processor.cpp:3383-3385), `DUEL_NO_HAND_LIMIT` (skip end-phase discard to 6 — processor.cpp:533), `DUEL_UNLIMITED_SUMMONS` (get_summon_count_limit returns effectively infinite — field.cpp:1958-1959), `DUEL_INVERTED_QUICK_PRIORITY` (non-turn player gets fast-effect priority first — processor.cpp:493, 843), `DUEL_EXTRA_DECK_RITUAL` (Rituals live in the Extra Deck — field.cpp:1273-1275).

**Convenience/simulator flags** (no rules-history meaning):
- `DUEL_TEST_MODE` (0x01): **defined but has zero usage sites in the core at both master and the pinned commit** (verified by grep and `git grep` at 158aebe7) — a legacy no-op kept for value compatibility.
- `DUEL_PSEUDO_SHUFFLE` (0x10): deck/extra "shuffles" are skipped (order preserved) except hand shuffles — field.cpp:955; used for replay determinism (EDOPro sets it for replays, duelclient.cpp:261).
- `DUEL_SIMPLE_AI` (0x40): player 1's choices are auto-answered by trivial built-in logic — playerop.cpp:165, 188, 216, 298, 353, 404, 460, 517, 613, 876.
- `DUEL_RELAY` (0x80): relay tag-duel mode — turn/team rotation and win checking differ (processor.cpp:3336, 4383, 4693).

## 3. How flags are passed at duel creation (CONFIRMED)

- API entry: `OCG_CreateDuel(OCG_Duel*, const OCG_DuelOptions*)` — ocgapi.h:31.
- `OCG_DuelOptions.flags` is **`uint64_t`** — ocgapi_types.h:66. Stored verbatim into `field::core.duel_options` (field.cpp:68), declared `uint64_t duel_options` (field.h:327).
- `field::is_flag(uint64_t flag)` requires **all** bits: `return (core.duel_options & flag) == flag;` (field.cpp:1248-1249). So `is_flag(DUEL_MODE_GOAT)` would only be true if every GOAT bit is set; engine code always tests single flags.
- **32-bit truncation quirk (CONFIRMED):** two client-facing serializations write only the low 32 bits: `MSG_RELOAD_FIELD` (`message->write<uint32_t>(core.duel_options)`, field.cpp:79) and `OCG_DuelQueryField` (`insert_value<uint32_t>(...)`, ocgapi.cpp:255). Flags at bit >= 32 (both SEGOC flags, TCG_FAST_EFFECT_IGNITION, EXTRA_DECK_RITUAL, NORMAL_SUMMON_FACEUP_DEF) are absent from those buffers; clients must learn them out-of-band.
- Lua access: `Duel.IsDuelType(flag)` / `Duel.GetDuelType()` expose `duel_options` to card scripts (libduel.cpp:3568-3577); `Debug.ReloadFieldBegin` can overwrite `core.duel_options` and accepts an MR shorthand 1-5 that maps to `DUEL_MODE_MR#` (libdebug.cpp:171-182).
- EDOPro transport: the network `HostInfo` splits the 64-bit value into `duel_flag_high`/`duel_flag_low` (`/home/user/edopro/gframe/network.h:51,57`), recombined as `(low | high << 32)` at generic_duel.cpp:598, duelclient.cpp:723, server_lobby.cpp:115. Replays store the full `uint64_t` in new format, `uint32_t` in old yrp format (replay.cpp:228-230; replay.h:127).
- EDOPro selects GOAT mode by literally assigning `mainGame->duel_param = DUEL_MODE_GOAT` with `forbiddentypes = DUEL_MODE_MR1_FORB` (menu_handler.cpp:932-933; also deck_con.cpp:200), and detects "GOAT" for display when the whole param equals `DUEL_MODE_GOAT` (duelclient.cpp:756, game.cpp:3138, server_lobby.cpp:118). GOAT lobby matching also checks GOAT deck sizes (duelclient.cpp:808).

## 4. Pinned submodule commit vs standalone master (CONFIRMED)

- EDOPro gitlink: `160000 commit 158aebe758be3c46249c75d602e3f16d63d2ef31 ocgcore` (`git ls-tree HEAD` in /home/user/edopro). That commit is `2025-04-17 "Add duel flag DUEL_NORMAL_SUMMON_FACEUP_DEF"`.
- The standalone clone is shallow and initially lacked the commit; `git fetch --depth 1 origin 158aebe7...` succeeded, so the comparison **was** performed (the task's anticipated limitation did not materialize).
- Result: the DUEL_* flag set, values, and all DUEL_MODE_* composites are **byte-for-byte identical** between the pinned commit (common.h:421-470 at that revision) and current master (ocgapi_constants.h:379-428). The pinned commit is in fact the commit that introduced the newest flag (`DUEL_NORMAL_SUMMON_FACEUP_DEF`), so EDOPro's core is fully current w.r.t. flags. Between the two revisions the defines merely moved from `common.h` into the new split headers (`ocgapi_constants.h`).
- EDOPro's vendored header `/home/user/edopro/gframe/ocgapi_constants.h` is byte-identical to core master's (verified with `diff`); `gframe/ocgapi_types.h` differs only by two extra duel-creation error enum values on master (`OCG_DUEL_CREATION_INCOMPATIBLE_LUA_API`, `OCG_DUEL_CREATION_NULL_RNG_SEED`), with `OCG_DuelOptions` unchanged.

## 5. Historical-rules gaps (justified strictly from the flag list)

The flag list parametrizes exactly these axes: turn structure (first-turn draw/attack, standby/MP2 skips), field geometry (columns, P/EM zones, trap-monster zones), ignition-effect priority, SEGOC ordering/visibility, damage-step chain windows, attack replays, 0-ATK ties, equip/field-spell disposal, deck-return triggers, private-knowledge triggers, summon-negation/oath counter timing, repositioning after control change, summon count, hand limit, ritual location, plus simulator conveniences. **No DUEL_ flag exists for anything outside those axes.** Concretely:

- **No flag for "missing the timing" / when-vs-if trigger conventions.** Nothing in the list touches optional-trigger timing windows beyond SEGOC ordering; any historical divergence in missing-the-timing handling (if such existed — game-history claim, needs sources) cannot be toggled.
- **No flag for chain-resolution or spell-speed rules.** Spell speeds, chain legality, and priority passing (other than `DUEL_INVERTED_QUICK_PRIORITY` and the ignition flags) are hard-coded.
- **No flags for deck construction:** deck/extra/side sizes, forbidden card types, and banlists are entirely client-side (EDOPro `HostInfo` fields `forbiddentypes`, deck size ranges; `DeckManager::CheckDeckContent` deck_manager.cpp:204). The `DUEL_MODE_MR*_FORB` constants exist but are consumed only by the client. Historical format recreation must pair core flags with client-side lflists (`/workspace/projectignis/lflists`) and deck-size settings.
- **No flags for starting LP / starting hand / draw count** — these are per-player numbers in `OCG_Player` (`startingLP`, `startingDrawCount`, `drawCountPerTurn`, ocgapi_types.h:53-57), not flags; a historical format needing e.g. different LP must set those instead.
- **No flag for pre-errata card behavior.** Flags change engine procedure only; per-card historical text/rulings (e.g. GOAT-era card behavior) must come from alternate card databases/scripts (babelcdb GOAT cdbs + cardscripts), not from any DUEL_ flag.
- **No flag for match/side-deck procedure, time rules, or tiebreakers** — `best_of`/match handling is client-side (netserver.cpp:363).
- **No flag for coin/dice/RPS or first-player determination conventions** — seed and RNG are `OCG_DuelOptions.seed`; who goes first is decided by the client.
- **No flag covering historical variations in battle-position rules other than** `DUEL_CAN_REPOS_IF_NON_SUMPLAYER` and `DUEL_NORMAL_SUMMON_FACEUP_DEF`; e.g. any other historical set/position nuance (game-history claim — needs sources before asserting one exists) has no toggle.

## Assumptions / uncertain items

- Attribution of specific flags to specific real-world rule changes/dates (e.g. "ignition priority removed in TCG March 2011", "first-turn draw removed in 2014", "old field spell rules until MR3") is **NOT verified from source** — the code only encodes the mechanics, and flag names ("OBSOLETE", "OLD", "TCG_") imply but do not document eras. Needs external rulebook/format-library sourcing.
- The precise rules-history semantics of `DUEL_STORE_ATTACK_REPLAYS` (which player-facing GOAT-era replay rule it models) is inferred from mechanics only; the engine effect (auto-decline replay prompt, attack not counted toward announce_count unless canceled) is confirmed at processor.cpp:2197, 2217.
- `DUEL_6_STEP_BATLLE_STEP` ("BATLLE" typo is in the source) — confirmed mechanical effect is suppression of empty damage-step chain windows; mapping to the documented historical 6-step damage step needs external sources.
- The GOAT composite's fidelity to the actual 2005 TCG ruleset is a design decision by the ocgcore/Project Ignis maintainers, not something the code proves.
