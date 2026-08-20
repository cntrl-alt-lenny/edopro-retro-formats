"""Headless ocgcore harness: run scripted duel scenarios against the real
engine and assert era behaviours from the message stream.

This drives the same core and card scripts EDOPro executes:

- the core library (OCG API 11, edo9300/ygopro-core) is loaded via ctypes
  from $RETROFORMATS_OCGCORE (e.g. libocgcore.so from
  ProjectIgnis/DeltaBagooska - the production binary EDOPro ships);
- card data comes from the pinned BabelCDB checkout (cards.cdb,
  goat-entries.cdb, cards-unofficial.cdb) under $RETROFORMATS_REPOS;
- scripts come from the pinned CardScripts checkout (official/, goat/,
  pre-errata/, unofficial/ + constant.lua/utility.lua), resolved by filename
  exactly like EDOPro resolves them (docs/research/ignis-goat.md section 4);
- scenarios are set up with the core's own Debug API (Debug.ReloadFieldBegin
  / SetPlayerInfo / AddCard / ReloadFieldEnd), the mechanism EDOPro puzzles
  use, so any board state is reachable without scripting a whole duel.

Message-buffer framing per duel::generate_buffer (duel.cpp:103): repeated
[u32 length][u8 msg_type + payload]. Response formats follow playerop.cpp
(cached copies of the exact revision live in the research cache). The driver
answers interactive messages from a scripted responder queue and FAILS LOUD
on anything unscripted - a regression test must never guess.

Windows note: DeltaBagooska ships only a 32-bit ocgcore.dll; CPython here is
64-bit, so on Windows run these tests under WSL against libocgcore.so
(verified working). Tests skip when RETROFORMATS_OCGCORE is unset.
"""

from __future__ import annotations

import ctypes
import io
import os
import sqlite3
import struct
from pathlib import Path

# -- constants (ocgapi_constants.h, pinned revision) ------------------------

LOCATION_DECK = 0x01
LOCATION_HAND = 0x02
LOCATION_MZONE = 0x04
LOCATION_SZONE = 0x08
LOCATION_GRAVE = 0x10
LOCATION_REMOVED = 0x20
LOCATION_EXTRA = 0x40

POS_FACEUP_ATTACK = 0x1
POS_FACEDOWN_ATTACK = 0x2
POS_FACEUP_DEFENSE = 0x4
POS_FACEDOWN_DEFENSE = 0x8

MSG_RETRY = 1
MSG_HINT = 2
MSG_WIN = 5
MSG_SELECT_BATTLECMD = 10
MSG_SELECT_IDLECMD = 11
MSG_SELECT_EFFECTYN = 12
MSG_SELECT_YESNO = 13
MSG_SELECT_OPTION = 14
MSG_SELECT_CARD = 15
MSG_SELECT_CHAIN = 16
MSG_SELECT_PLACE = 18
MSG_SELECT_POSITION = 19
MSG_SELECT_TRIBUTE = 20
MSG_SELECT_UNSELECT_CARD = 26
MSG_CONFIRM_DECKTOP = 30
MSG_CONFIRM_CARDS = 31
MSG_SHUFFLE_DECK = 32
MSG_SHUFFLE_HAND = 33
MSG_NEW_TURN = 40
MSG_NEW_PHASE = 41
MSG_MOVE = 50
MSG_POS_CHANGE = 53
MSG_SET = 54
MSG_SUMMONING = 60
MSG_SUMMONED = 61
MSG_SPSUMMONING = 62
MSG_SPSUMMONED = 63
MSG_FLIPSUMMONING = 64
MSG_FLIPSUMMONED = 65
MSG_CHAINING = 70
MSG_CHAINED = 71
MSG_CHAIN_SOLVING = 72
MSG_CHAIN_SOLVED = 73
MSG_CHAIN_END = 74
MSG_CARD_SELECTED = 80
MSG_RANDOM_SELECTED = 81
MSG_BECOME_TARGET = 83
MSG_DRAW = 90
MSG_DAMAGE = 91
MSG_RECOVER = 92
MSG_EQUIP = 93
MSG_LPUPDATE = 94
MSG_UNEQUIP = 95
MSG_CARD_TARGET = 96
MSG_PAY_LPCOST = 100
MSG_ATTACK = 110
MSG_BATTLE = 111
MSG_DAMAGE_STEP_START = 113
MSG_DAMAGE_STEP_END = 114

MSG_NAMES = {v: k for k, v in list(globals().items()) if k.startswith("MSG_")}

OCG_DUEL_STATUS_END = 0
OCG_DUEL_STATUS_AWAITING = 1
OCG_DUEL_STATUS_CONTINUE = 2

# -- ctypes API (ocgapi_types.h, OCG_VERSION 11.0) --------------------------


class OCG_CardData(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_uint32),
        ("alias", ctypes.c_uint32),
        ("setcodes", ctypes.POINTER(ctypes.c_uint16)),
        ("type", ctypes.c_uint32),
        ("level", ctypes.c_uint32),
        ("attribute", ctypes.c_uint32),
        ("race", ctypes.c_uint64),
        ("attack", ctypes.c_int32),
        ("defense", ctypes.c_int32),
        ("lscale", ctypes.c_uint32),
        ("rscale", ctypes.c_uint32),
        ("link_marker", ctypes.c_uint32),
    ]


class OCG_Player(ctypes.Structure):
    _fields_ = [
        ("startingLP", ctypes.c_uint32),
        ("startingDrawCount", ctypes.c_uint32),
        ("drawCountPerTurn", ctypes.c_uint32),
    ]


DataReader = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(OCG_CardData))
DataReaderDone = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(OCG_CardData))
ScriptReader = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)
LogHandler = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int)


class OCG_DuelOptions(ctypes.Structure):
    _fields_ = [
        ("seed", ctypes.c_uint64 * 4),
        ("flags", ctypes.c_uint64),
        ("team1", OCG_Player),
        ("team2", OCG_Player),
        ("cardReader", DataReader),
        ("payload1", ctypes.c_void_p),
        ("scriptReader", ScriptReader),
        ("payload2", ctypes.c_void_p),
        ("logHandler", LogHandler),
        ("payload3", ctypes.c_void_p),
        ("cardReaderDone", DataReaderDone),
        ("payload4", ctypes.c_void_p),
        ("enableUnsafeLibraries", ctypes.c_uint8),
    ]


class OCG_NewCardInfo(ctypes.Structure):
    _fields_ = [
        ("team", ctypes.c_uint8),
        ("duelist", ctypes.c_uint8),
        ("code", ctypes.c_uint32),
        ("con", ctypes.c_uint8),
        ("loc", ctypes.c_uint32),
        ("seq", ctypes.c_uint32),
        ("pos", ctypes.c_uint32),
    ]


def core_path() -> Path | None:
    value = os.environ.get("RETROFORMATS_OCGCORE")
    return Path(value) if value else None


def repos_path() -> Path:
    value = os.environ.get("RETROFORMATS_REPOS")
    if value:
        return Path(value)
    return Path.home() / ".cache" / "retroformats" / "repos"


def available() -> bool:
    path = core_path()
    return bool(
        path
        and path.exists()
        and (repos_path() / "babelcdb" / "cards.cdb").exists()
        and (repos_path() / "cardscripts" / "constant.lua").exists()
    )


class CardDatabase:
    """Card data for the reader callback, merged like a client would."""

    def __init__(self, babel: Path):
        self.rows: dict[int, tuple] = {}
        for cdb in ("cards.cdb", "goat-entries.cdb", "cards-unofficial.cdb"):
            path = babel / cdb
            if not path.exists():
                continue
            con = sqlite3.connect(path)
            for row in con.execute(
                "SELECT id, alias, setcode, type, atk, def, level, race, attribute FROM datas"
            ):
                self.rows[int(row[0])] = row
            con.close()

    def fill(self, code: int, data: OCG_CardData, setcode_buf) -> None:
        row = self.rows.get(code)
        data.code = code
        if row is None:
            return
        _, alias, setcode, type_, atk, def_, level, race, attribute = row
        data.alias = int(alias)
        # setcode packs up to 4 16-bit archetype codes into a 64-bit int.
        packed = int(setcode) & 0xFFFFFFFFFFFFFFFF
        n = 0
        while packed and n < 4:
            setcode_buf[n] = packed & 0xFFFF
            packed >>= 16
            n += 1
        setcode_buf[n] = 0
        data.setcodes = ctypes.cast(setcode_buf, ctypes.POINTER(ctypes.c_uint16))
        data.type = int(type_) & 0xFFFFFFFF
        data.attack = int(atk)
        data.defense = int(def_)
        # level packs pendulum scales in the upper bytes
        data.level = int(level) & 0xFF
        data.lscale = (int(level) >> 24) & 0xFF
        data.rscale = (int(level) >> 16) & 0xFF
        data.race = int(race) & 0xFFFFFFFFFFFFFFFF
        data.attribute = int(attribute) & 0xFFFFFFFF
        data.link_marker = 0


class Message:
    """One parsed core message: type + a cursor over its payload."""

    def __init__(self, msg_type: int, payload: bytes):
        self.type = msg_type
        self.name = MSG_NAMES.get(msg_type, f"MSG_{msg_type}")
        self.payload = payload
        self._buf = io.BytesIO(payload)

    def u8(self) -> int:
        return struct.unpack("<B", self._buf.read(1))[0]

    def u16(self) -> int:
        return struct.unpack("<H", self._buf.read(2))[0]

    def u32(self) -> int:
        return struct.unpack("<I", self._buf.read(4))[0]

    def u64(self) -> int:
        return struct.unpack("<Q", self._buf.read(8))[0]

    def loc_info(self) -> dict:
        controler, location = struct.unpack("<BB", self._buf.read(2))
        sequence, position = struct.unpack("<II", self._buf.read(8))
        return {
            "controler": controler,
            "location": location,
            "sequence": sequence,
            "position": position,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<{self.name} {self.payload[:24].hex()}>"


class ScenarioError(AssertionError):
    pass


class Duel:
    """One headless duel over a scenario script, with scripted responses."""

    def __init__(self, flags: int, seed: int = 1, lp: int = 8000):
        if not available():  # pragma: no cover
            raise RuntimeError("ocgcore harness prerequisites missing")
        self.lib = ctypes.CDLL(str(core_path()))
        self.lib.OCG_CreateDuel.restype = ctypes.c_int
        self.lib.OCG_CreateDuel.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(OCG_DuelOptions)]
        self.lib.OCG_DestroyDuel.argtypes = [ctypes.c_void_p]
        self.lib.OCG_DuelNewCard.argtypes = [ctypes.c_void_p, ctypes.POINTER(OCG_NewCardInfo)]
        self.lib.OCG_StartDuel.argtypes = [ctypes.c_void_p]
        self.lib.OCG_DuelProcess.restype = ctypes.c_int
        self.lib.OCG_DuelProcess.argtypes = [ctypes.c_void_p]
        self.lib.OCG_DuelGetMessage.restype = ctypes.POINTER(ctypes.c_uint8)
        self.lib.OCG_DuelGetMessage.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        self.lib.OCG_DuelSetResponse.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
        self.lib.OCG_LoadScript.restype = ctypes.c_int
        self.lib.OCG_LoadScript.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p]

        repos = repos_path()
        self.scripts_root = repos / "cardscripts"
        self.db = CardDatabase(repos / "babelcdb")
        self.log: list[tuple[int, str]] = []
        self.messages: list[Message] = []
        self.responders: list = []
        self.defaults: dict[int, object] = {}
        self._setcode_bufs: dict[int, object] = {}

        harness = self

        @DataReader
        def card_reader(_payload, code, data):
            buf = harness._setcode_bufs.setdefault(code, (ctypes.c_uint16 * 5)())
            harness.db.fill(code, data.contents, buf)

        @DataReaderDone
        def card_reader_done(_payload, _data):
            pass

        @ScriptReader
        def script_reader(_payload, duel, name):
            return 1 if harness._load_script_file(duel, name.decode("utf-8")) else 0

        @LogHandler
        def log_handler(_payload, string, log_type):
            harness.log.append((log_type, string.decode("utf-8", "replace")))

        # keep callback objects alive for the duel's lifetime
        self._callbacks = (card_reader, card_reader_done, script_reader, log_handler)

        options = OCG_DuelOptions()
        options.seed = (ctypes.c_uint64 * 4)(seed, seed, seed, seed)
        options.flags = flags
        options.team1 = OCG_Player(lp, 5, 1)
        options.team2 = OCG_Player(lp, 5, 1)
        options.cardReader = card_reader
        options.scriptReader = script_reader
        options.logHandler = log_handler
        options.cardReaderDone = card_reader_done
        options.enableUnsafeLibraries = 1

        self.duel = ctypes.c_void_p()
        status = self.lib.OCG_CreateDuel(ctypes.byref(self.duel), ctypes.byref(options))
        if status != 0:
            raise ScenarioError(f"OCG_CreateDuel failed: {status}")
        for base in ("constant.lua", "utility.lua"):
            if not self._load_script_file(self.duel, base):
                raise ScenarioError(f"failed to load {base}")

    def _load_script_file(self, duel, name: str) -> bool:
        base = name.rsplit("/", 1)[-1]
        for sub in ("", "official", "goat", "pre-errata", "unofficial", "pre-release"):
            path = self.scripts_root / sub / base if sub else self.scripts_root / base
            if path.exists():
                content = path.read_bytes()
                return bool(
                    self.lib.OCG_LoadScript(duel, content, len(content), base.encode())
                )
        return False

    def load_scenario(self, lua: str) -> None:
        """Run a Debug.* setup script (the puzzle mechanism)."""
        content = lua.encode("utf-8")
        if not self.lib.OCG_LoadScript(self.duel, content, len(content), b"scenario.lua"):
            raise ScenarioError(f"scenario script failed to load; log: {self.log[-5:]}")

    def start(self) -> None:
        self.lib.OCG_StartDuel(self.duel)

    def respond(self, msg_type: int, answer) -> None:
        """Queue one scripted response: `answer` is bytes, or a callable
        receiving the parsed prompt and returning bytes. Consumed in order,
        but only when the prompt's type matches the queue head - otherwise
        the default for that type (if any) answers."""
        self.responders.append((msg_type, answer))

    def default_response(self, msg_type: int, answer) -> None:
        """Standing answer for a message type (e.g. always decline to chain).
        The scripted queue takes precedence when its head matches."""
        self.defaults[msg_type] = answer

    # -- driving ---------------------------------------------------------

    def run(self, max_steps: int = 200, turns: int | None = None) -> list[Message]:
        """Process until the scripted responses are exhausted (the scenario's
        observation window), the duel ends, or max_steps passes. Responding
        wrongly raises; running out of scripted answers just stops.

        `turns` bounds the window to that many turns, which a scenario driven
        by standing defaults needs: without it, defaults keep answering the
        opponent's turns forever and the duel never settles."""
        for _ in range(max_steps):
            if turns is not None and len(self.seen(MSG_NEW_TURN)) > turns:
                return self.messages
            status = self.lib.OCG_DuelProcess(self.duel)
            batch = self._drain_messages()
            self.messages.extend(batch)
            if status == OCG_DUEL_STATUS_END:
                return self.messages
            if status == OCG_DUEL_STATUS_AWAITING:
                prompt = next(
                    (m for m in reversed(batch) if m.type in _INTERACTIVE), None
                )
                if prompt is None:
                    raise ScenarioError(
                        f"core awaits a response but no interactive message seen; "
                        f"last: {[m.name for m in batch[-5:]]}"
                    )
                if prompt.type == MSG_RETRY:
                    raise ScenarioError("core rejected a scripted response (MSG_RETRY)")
                if not self._answer(prompt):
                    return self.messages  # observation window over
        raise ScenarioError("scenario did not settle within max_steps")

    def _answer(self, prompt: Message) -> bool:
        answer = None
        if self.responders and self.responders[0][0] == prompt.type:
            answer = self.responders.pop(0)[1]
        elif prompt.type in self.defaults:
            answer = self.defaults[prompt.type]
        elif not self.responders:
            return False  # nothing scripted left and no default: stop observing
        else:
            raise ScenarioError(
                f"prompt order mismatch: expected {MSG_NAMES.get(self.responders[0][0])}, "
                f"core asked {prompt.name} ({prompt.payload.hex()})"
            )
        if callable(answer):
            answer = answer(prompt)
        self.lib.OCG_DuelSetResponse(self.duel, bytes(answer), len(answer))
        return True

    def _drain_messages(self) -> list[Message]:
        length = ctypes.c_uint32()
        buf = self.lib.OCG_DuelGetMessage(self.duel, ctypes.byref(length))
        raw = bytes(ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8 * length.value)).contents) if length.value else b""
        out: list[Message] = []
        pos = 0
        while pos + 4 <= len(raw):
            (size,) = struct.unpack_from("<I", raw, pos)
            pos += 4
            chunk = raw[pos : pos + size]
            pos += size
            if chunk:
                out.append(Message(chunk[0], chunk[1:]))
        return out

    def close(self) -> None:
        if self.duel:
            self.lib.OCG_DestroyDuel(self.duel)
            self.duel = None

    # -- assertions ------------------------------------------------------

    def seen(self, msg_type: int) -> list[Message]:
        return [m for m in self.messages if m.type == msg_type]

    def moves(self) -> list[dict]:
        out = []
        for m in self.seen(MSG_MOVE):
            m._buf.seek(0)
            code = m.u32()
            prev = m.loc_info()
            cur = m.loc_info()
            reason = m.u32()
            out.append({"code": code, "from": prev, "to": cur, "reason": reason})
        return out


_INTERACTIVE = {
    MSG_RETRY,
    MSG_SELECT_BATTLECMD,
    MSG_SELECT_IDLECMD,
    MSG_SELECT_EFFECTYN,
    MSG_SELECT_YESNO,
    MSG_SELECT_OPTION,
    MSG_SELECT_CARD,
    MSG_SELECT_CHAIN,
    MSG_SELECT_PLACE,
    MSG_SELECT_POSITION,
    MSG_SELECT_TRIBUTE,
    MSG_SELECT_UNSELECT_CARD,
}


# -- canned responses (formats per playerop.cpp, pinned revision) -----------

def answer_int(value: int) -> bytes:
    return struct.pack("<i", value)


def answer_cards(*indices: int) -> bytes:
    return struct.pack("<iI", 0, len(indices)) + b"".join(
        struct.pack("<I", i) for i in indices
    )


def answer_no_chain() -> bytes:
    return struct.pack("<i", -1)


def answer_chain_decline_unless_forced(prompt: Message) -> bytes:
    """SELECT_CHAIN: decline, except when the core marks the prompt `forced`
    (a mandatory trigger MUST go on the chain - declining is rejected with
    MSG_RETRY, playerop.cpp SelectChain). Message layout: u8 player,
    u8 spe_count, u8 forced, u32 hint_timing x2, u32 count, [entries]."""
    prompt._buf.seek(0)
    prompt.u8()  # player
    prompt.u8()  # spe_count
    forced = prompt.u8()
    return struct.pack("<i", 0 if forced else -1)


def answer_idle(action: int, index: int = 0) -> bytes:
    """SELECT_IDLECMD: t|s<<16; t: 0 summon, 1 spsummon, 2 repos, 3 mset,
    4 sset, 5 activate, 6 to battle phase, 7 to end phase."""
    return struct.pack("<i", (action & 0xFFFF) | (index << 16))


def answer_battle(action: int, index: int = 0) -> bytes:
    """SELECT_BATTLECMD: t: 0 chain, 1 attack, 2 to main2, 3 to end."""
    return struct.pack("<i", (action & 0xFFFF) | (index << 16))


def answer_position(position: int) -> bytes:
    return struct.pack("<i", position)


def answer_idle_activate_or_end(prompt: Message) -> bytes:
    """SELECT_IDLECMD: activate the first available effect, or end the turn
    when none is offered. Lets a scenario ask "do it again" without knowing
    whether the card's once-per-turn already stopped it.

    Layout (playerop.cpp SelectIdleCmd): u8 player, then five card lists
    (summonable / spsummonable / repositionable / msetable / ssetable), then
    the activatable list. Each list is a u32 count followed by fixed-size
    entries; only `repositionable` uses a u8 sequence, the others u32.
    """
    prompt._buf.seek(0)
    prompt.u8()  # player
    for entry_size in (10, 10, 7, 10, 10):  # code+con+loc+seq per list
        count = prompt.u32()
        prompt._buf.read(count * entry_size)
    activatable = prompt.u32()
    if activatable:
        return answer_idle(5, 0)
    return answer_idle(7)  # to End Phase


def answer_place_first_free(prompt: Message) -> bytes:
    """SELECT_PLACE: pick the first zone the flag bitmask allows.
    Message: u8 player, u8 count, u32 flag (bit SET = zone disabled).
    Response: u8 player, u8 location, u8 sequence."""
    prompt._buf.seek(0)
    player = prompt.u8()
    prompt.u8()  # count (1 for our scenarios)
    flag = prompt.u32()
    # player 0 mzone bits 0-6, szone bits 8-15 (client convention)
    for seq in range(5):
        if not (flag & (1 << seq)):
            return struct.pack("<BBB", player, LOCATION_MZONE, seq)
    for seq in range(5):
        if not (flag & (1 << (8 + seq))):
            return struct.pack("<BBB", player, LOCATION_SZONE, seq)
    raise ScenarioError(f"no free zone (flag {flag:#010x})")
