# Engine-level regression testing

`tests/engine/` runs scripted duel scenarios against the **real ocgcore** and
asserts era behaviours from the engine's own message stream. This is what
makes `implementation.tested: true` in `data/errata/` mean something: a Lua
file existing proves nothing, an executed behavioural difference does.

## What it drives

The same core and card scripts EDOPro executes:

- **Core**: the OCG API 11 library (`edo9300/ygopro-core`), loaded through
  `ctypes` from `$RETROFORMATS_OCGCORE`. Project Ignis ships production
  builds in [DeltaBagooska](https://github.com/ProjectIgnis/DeltaBagooska)
  under `bin/` (`libocgcore.so`, `ocgcore.dll`, …).
- **Card data**: the pinned BabelCDB checkout (`cards.cdb`,
  `goat-entries.cdb`, `cards-unofficial.cdb`) under `$RETROFORMATS_REPOS`,
  merged the way a client merges them.
- **Scripts**: the pinned CardScripts checkout, resolved *by filename* across
  `official/`, `goat/`, `pre-errata/`, `unofficial/` — exactly how EDOPro
  resolves them (`docs/research/ignis-goat.md` §4), so a historical passcode
  transparently picks up its historical script.
- **Scenarios**: built with the core's own `Debug.*` API
  (`ReloadFieldBegin` / `SetPlayerInfo` / `AddCard` / `ReloadFieldEnd`) — the
  mechanism EDOPro's puzzle mode uses. Any board state is reachable without
  scripting a whole duel.

## Running it

```bash
RETROFORMATS_OCGCORE=~/.cache/retroformats/engine/libocgcore.so \
RETROFORMATS_REPOS=~/.cache/retroformats/repos \
python3 -m unittest discover -t . -s tests/engine -v
```

Without those variables the engine tests **skip** (they are part of
`unittest discover -t . -s tests` and skip there too), so the stdlib-only,
no-download contract of the main suite is preserved and CI stays green on a
bare runner.

**Windows**: DeltaBagooska's `ocgcore.dll` is 32-bit while a stock CPython is
64-bit, so `ctypes` cannot load it. Run the engine tests under WSL against
`libocgcore.so` (verified working), or build a 64-bit core.

Fetching the prerequisites:

```bash
mkdir -p ~/.cache/retroformats/engine
curl -L -o ~/.cache/retroformats/engine/libocgcore.so \
  https://raw.githubusercontent.com/ProjectIgnis/DeltaBagooska/master/bin/libocgcore.so
```

BabelCDB and CardScripts are cloned at the revisions pinned in
`data/sources.json`.

## How a scenario works

```python
duel = H.Duel(flags=DUEL_MODE_GOAT, seed=7)
duel.load_scenario("""
Debug.ReloadFieldBegin(0x2000000,4)
Debug.SetPlayerInfo(0,8000,0,0)
Debug.SetPlayerInfo(1,8000,0,0)
Debug.AddCard(504700178,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)   -- Sangan (GOAT)
Debug.ReloadFieldEnd()
""")
duel.start()
duel.respond(H.MSG_SELECT_IDLECMD, H.answer_idle(5, 0))       # ordered script
duel.default_response(H.MSG_SELECT_CHAIN, H.answer_chain_decline_unless_forced)
duel.run()
assert duel.seen(H.MSG_CONFIRM_CARDS)                          # era assertion
```

- `respond()` queues an **ordered** answer consumed only when the prompt type
  matches; `default_response()` sets a standing answer for a message type.
- Anything unscripted **fails loud** — a regression test must never guess,
  and `MSG_RETRY` (the core rejecting a malformed answer) is an error, not a
  silent retry. Running out of scripted answers simply ends the observation
  window.
- Message framing is `[u32 length][u8 type + payload]` per
  `duel::generate_buffer`; response encodings follow `playerop.cpp`. Both are
  documented per helper in `tests/engine/harness.py`.

Duel flags come from the rule profiles: `DUEL_MODE_GOAT` = `0x7F80D072C`,
`DUEL_MODE_MR1` = `0xD0700`, expanded from the pinned `ocgapi_constants.h`
(the same expansion `tests/test_repo_data.py` asserts the profiles against).

## What is asserted today

`tests/engine/test_historical_behaviour.py` covers the two eras that the
research established are *behaviourally* load-bearing, in both directions
(historical implementation vs modern implementation, same scenario):

| Behaviour | Historical | Modern |
|---|---|---|
| Failed search reveals the Deck (period verification procedure) | `MSG_CONFIRM_CARDS` emitted by Sangan (GOAT) | no reveal |
| Sangan's post-2016 hard once-per-turn | two pre-errata copies → **2** searches | modern pair → **1** search |
| Imperial Order maintenance | pre-errata asks its controller (`MSG_SELECT_YESNO`), declining destroys it | modern pays automatically (`MSG_PAY_LPCOST`), never asks |

Each asserts *gameplay*, not file existence, and each pairs the historical
implementation against the modern one so the difference — not merely the
behaviour — is what the test locks down.

## Extending it

Add a scenario per behavioural claim you want to certify, then set
`implementation.tested: true` on the erratum record it proves. Prefer
assertions on structural messages (`MSG_CONFIRM_CARDS`, `MSG_PAY_LPCOST`,
`MSG_MOVE` transitions via `duel.moves()`) over LP arithmetic: they state the
mechanism rather than a side effect.

Known gaps worth closing next: damage-step legality windows, equip survival
when the target leaves, and trigger-timing (`missing the timing`) cases —
each needs a scenario that reaches the Battle Phase, which the harness
supports (`answer_battle`) but no test exercises yet.
