# Engine-level regression testing

`tests/engine/` runs scripted duel scenarios against the **real ocgcore** and
asserts era behaviours from the engine's own message stream. This is what
makes `implementation.tested: true` in `data/errata/` mean something: a Lua
file existing proves nothing, an executed behavioural difference does.

## What it drives

The same core and card scripts EDOPro executes:

- **Core**: the OCG API 11 library (`edo9300/ygopro-core`), loaded through
  `ctypes` from `$RETROFORMATS_OCGCORE`. CI and `scripts/engine_env.py` compile
  it from the source revision `data/sources.json` pins for `ygopro-core`. Project
  Ignis's prebuilt binaries in
  [DeltaBagooska](https://github.com/ProjectIgnis/DeltaBagooska) (`bin/`) load
  fine but are **not** used for verification: nothing ties one to a source
  revision (see "Pinned inputs").
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

**In CI**, the `engine` job in `.github/workflows/ci.yml` prepares the pinned
inputs and runs every engine test on each push and pull request. The `check` job
next to it is unchanged: it still runs the whole suite on Python 3.10 and 3.13,
where the engine tests skip, so the main suite stays standard-library-only with no
network access.

**Locally** (Linux or macOS), the same two commands CI runs:

```bash
python scripts/engine_env.py prepare --dest ~/.cache/retroformats   # network, ~1-2 min
python scripts/engine_env.py run --dest ~/.cache/retroformats --expect-at-least 40
```

`prepare` fetches and verifies the pinned inputs and compiles the core (it needs
`git`, `make` and a C++17 compiler); `run` re-verifies them offline, then runs
`tests/engine` and **fails on any skip**, failure or error, or if fewer than 40
tests execute. The layout it produces is `DEST/repos/babelcdb`,
`DEST/repos/cardscripts` and `DEST/engine/libocgcore.{so,dylib}`.

The harness itself only needs two environment variables, so a core and checkouts
obtained some other way also work, but then nothing has verified them against the
pins:

```bash
RETROFORMATS_OCGCORE=DEST/engine/libocgcore.so \
RETROFORMATS_REPOS=DEST/repos \
python3 -m unittest discover -t . -s tests/engine -v
```

Without those variables the engine tests **skip** - in `unittest discover -t . -s
tests` too, which is why the main suite stays green on a bare runner. A skip is
not a pass: plain `unittest` exits 0 with every engine test skipped, which is exactly the
state this project was in before the `engine` job. Only `engine_env.py run`
refuses it.

**Windows**: DeltaBagooska's `ocgcore.dll` is 32-bit while a stock CPython is
64-bit, so `ctypes` cannot load it, and the helper builds for Linux and macOS
only. Run the engine tests under WSL.

## Pinned inputs

Every external input the engine job uses is taken at a recorded revision and
checked, so a moved upstream cannot silently change what is tested. The
revisions are the ones `data/sources.json` already records for the project's
claims; the helper reads them from there rather than keeping its own copy.

| Input | Pinned by | Verified how |
|---|---|---|
| BabelCDB | `ignis-babelcdb` revision | fetched by full commit hash; `git rev-parse HEAD` must equal the pin and no tracked file may differ |
| CardScripts | `ignis-cardscripts` revision | same |
| ocgcore source | `ygopro-core` revision | same |
| Lua | the core's own `lua/src` submodule, at the commit the core's tree records for the pinned revision | same, fetched from the URL in the core's `.gitmodules` |
| premake5 | version `5.0.0-beta2`, the one the core's `scripts/install-premake5.sh` downloads | SHA-256 in `scripts/engine_env.py`, checked before unpacking |
| the built library | compiled from the four sources above | its SHA-256 is recorded in `manifest.json` at build time and re-checked by `run`; the manifest also records the source revisions and the compiler |

Fetching by full hash means the server either serves that commit or the fetch
fails, so a force-pushed or deleted upstream fails the job loudly instead of
testing something else. `run` repeats the checkout checks offline before every
run, so a stale or edited cache is refused, not tested.

**Why the core is built rather than downloaded.** DeltaBagooska's `bin/` commits
say "Update core" and link a core commit (for the latest `libocgcore.so`
commit when this was written, `8eba148`, that is `fd2a557`, which is not the
pinned revision). The binary itself is stripped and carries no revision string
(checked with `strings`), so nothing independent confirms what it was built
from. A binary from
there could only be pinned by its own checksum, which would pin a file, not the
claim "this is the pinned ygopro-core revision". Building from the pinned source,
with the core's own premake5 configuration, is the only route that makes that
claim true.

## How the engine differs from what EDOPro players run

Stated plainly, so a green engine job is not read as more than it is:

- **The binary is built here, not shipped by Project Ignis.** Same source
  revision, but compiled with the runner's compiler (`ubuntu-latest`'s `g++`,
  recorded in the log, not pinned) in the Release configuration of the core's
  premake5 build. It is not byte-identical to any binary players have.
- **The pin is a point in time.** EDOPro follows the core's current development
  and Project Ignis's current card scripts; the pinned revisions are the ones this
  project last recorded. Behaviour changes upstream after the pin are not seen
  until the pin is deliberately moved.
- **Only what is asserted is tested.** The harness is headless and answers
  prompts from scripted responses. There is no client layer: no deck or
  banlist enforcement, no room/duel-flag setup by the client, no networking or
  UI. Duel flags come from this project's rule profiles, not from whatever a
  given EDOPro room sets.
- **Card data is a merge of three databases** (`cards.cdb`, `goat-entries.cdb`,
  `cards-unofficial.cdb`) and scripts are resolved by the harness's own
  filename search, modelled on EDOPro's but not EDOPro's code.
- **CI covers Linux x86-64 only.** Other platforms are untested here: no
  evidence survives in this project of the pinned core being built or run on
  macOS, Windows, or any architecture other than what the `engine` job's
  runner uses.

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

### Generated historical cards

`tests/engine/test_edison_historical_scripts.py` covers the two cards this project
writes itself (`docs/errata.md`, "Generated historical cards"). The harness merges
`dist/databases/*.cdb` into its card data and searches `dist/scripts/` after the
upstream folders, as a client with `data_path`/`script_path` pointed at `dist/` would
(`RETROFORMATS_DIST` overrides the folder). Each scenario runs against the modern card
and the generated one:

| Card | Behaviour asserted | Historical (generated) | Modern |
|---|---|---|---|
| Metalzoa | revival by Monster Reborn | not a legal target | a legal target |
| Super Vehicroid - Stealth Union | equip effect | only a monster you control; unusable with none | any face-up monster, either side |

Beside each difference are control scenarios (summon procedure, equip, piercing damage,
attack-all) that must behave the same, so a script cannot pass by doing
nothing. They prove the scripts against those scenarios only: each record's
`not_reproduced` lists what is neither tested nor established.

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
