"""Generation of the custom-card database and scripts (roadmap item 7).

Canonical input, per generated card, is a `data/custom-cards/c<passcode>.json`
record plus the Lua script it names. The generator emits, and only emits:

- `dist/databases/retro-formats.cdb`: one `datas` + `texts` row per card, in the
  standard BabelCDB/ygopro layout. Each row aliases the modern card, carries
  `ot = 8` (SCOPE_ILLEGAL, so it is not legal in an official-cards room and is
  playable only through a whitelist that names it) and takes its text from the
  sourced period text on the record.
- `dist/scripts/c<passcode>.lua`: the record's script, byte for byte. EDOPro finds
  a script by that filename in any folder under a repository's `script_path`
  (docs/research/ignis-goat.md section 4), so no other layout is needed.

Identity in a duel and in deck building comes entirely from the row's `alias`
(docs/research/ignis-goat.md section 6; docs/research/edopro-lflists.md): the
card *is* its modern card for name and code checks, and copies count together
under the alias root. The historical passcode has to be listed in a whitelist
explicitly, because a whitelist follows an alias only within +/-10.

Everything here is standard library only. `sqlite3` writes the database, so the
file's bytes must not depend on the SQLite version that wrote it: the three
header fields that record it are normalised (`_normalise_sqlite_header`), and the
page layout for one fixed schema and sorted inserts is otherwise deterministic.
`tests/test_custom_cards.py` pins that by comparing bytes.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from .model import CustomCard
from .repo import Repository

CDB_NAME = "retro-formats.cdb"

# Standard BabelCDB layout (docs/research/ignis-goat.md section 2). Kept verbatim so
# a client's own loader, which upserts rows by passcode, treats these like any
# other cdb.
_DATAS_DDL = (
    'CREATE TABLE "datas" ("id" INTEGER,"ot" INTEGER,"alias" INTEGER,"setcode" INTEGER,'
    '"type" INTEGER,"atk" INTEGER,"def" INTEGER,"level" INTEGER,"race" INTEGER,'
    '"attribute" INTEGER,"category" INTEGER,PRIMARY KEY("id"))'
)
_TEXTS_DDL = (
    'CREATE TABLE "texts" ("id" INTEGER,"name" TEXT,"desc" TEXT,'
    + ",".join(f'"str{i}" TEXT' for i in range(1, 17))
    + ',PRIMARY KEY("id"))'
)


def _normalise_sqlite_header(data: bytearray) -> None:
    """Zero the header fields that record which SQLite wrote the file.

    Offset 24: file change counter; 92: version-valid-for; 96: SQLITE_VERSION_NUMBER
    (https://www.sqlite.org/fileformat.html section 1.3). The first two must
    stay equal for the counter to be trusted, so both are set to 1."""
    data[24:28] = (1).to_bytes(4, "big")
    data[92:96] = (1).to_bytes(4, "big")
    data[96:100] = (0).to_bytes(4, "big")


def cards_sorted(repo: Repository) -> list[CustomCard]:
    return [repo.custom_cards[code] for code in sorted(repo.custom_cards)]


def build_cdb_bytes(cards: list[CustomCard]) -> bytes:
    """The database file for `cards`, deterministic for equal input."""
    fd, tmp_name = tempfile.mkstemp(suffix=".cdb")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.unlink()
        con = sqlite3.connect(str(tmp), isolation_level=None)
        try:
            con.execute("PRAGMA page_size=4096")
            con.execute("PRAGMA journal_mode=DELETE")
            con.execute("BEGIN")
            con.execute(_DATAS_DDL)
            con.execute(_TEXTS_DDL)
            for card in sorted(cards, key=lambda c: c.passcode):
                cdb = card.cdb
                con.execute(
                    "INSERT INTO datas VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        card.passcode,
                        cdb["ot"],
                        card.alias,
                        cdb["setcode"],
                        cdb["type"],
                        cdb["atk"],
                        cdb["def"],
                        cdb["level"],
                        cdb["race"],
                        cdb["attribute"],
                        cdb["category"],
                    ),
                )
                con.execute(
                    "INSERT INTO texts VALUES (?,?,?" + ",?" * 16 + ")",
                    (card.passcode, card.name, card.desc, *([""] * 16)),
                )
            con.execute("COMMIT")
        finally:
            con.close()
        data = bytearray(tmp.read_bytes())
    finally:
        for leftover in (tmp, Path(str(tmp) + "-journal")):
            if leftover.exists():
                leftover.unlink()
    _normalise_sqlite_header(data)
    return bytes(data)


def read_cdb_rows(path: Path) -> dict[int, dict[str, object]]:
    """{passcode: merged datas+texts row} for reading a generated (or any)
    cdb back; used by tests and by the validator's cross-checks."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        con.row_factory = sqlite3.Row
        rows: dict[int, dict[str, object]] = {}
        for row in con.execute("SELECT * FROM datas"):
            rows[int(row["id"])] = dict(row)
        for row in con.execute("SELECT id, name, desc FROM texts"):
            rows.setdefault(int(row["id"]), {}).update(name=row["name"], desc=row["desc"])
        return rows
    finally:
        con.close()


def script_filename(card: CustomCard) -> str:
    return f"c{card.passcode}.lua"


def read_script(repo: Repository, card: CustomCard) -> bytes:
    """The canonical script text, LF-normalised (a Windows checkout with CRLF
    must still regenerate the same bytes)."""
    raw = (repo.root / card.script).read_bytes()
    return raw.replace(b"\r\n", b"\n")


def expected_outputs(repo: Repository) -> dict[str, bytes]:
    """{path relative to dist/: exact bytes} for every generated database and
    script. Empty when the repository defines no custom cards."""
    cards = cards_sorted(repo)
    if not cards:
        return {}
    out: dict[str, bytes] = {f"databases/{CDB_NAME}": build_cdb_bytes(cards)}
    for card in cards:
        out[f"scripts/{script_filename(card)}"] = read_script(repo, card)
    return out


# Files the generator does not own. Anything else in these two folders is stale
# output (a removed card, a renamed script) and is deleted, so `build --check`
# reports a missing removal as drift instead of leaving a script no record
# claims in dist/.
_KEEP = {".gitkeep"}


def build_custom_cards(repo: Repository, dist: Path) -> list[Path]:
    """Write every generated database and script under `dist`; delete stale
    generated files. Returns the paths written."""
    outputs = expected_outputs(repo)
    written: list[Path] = []
    for rel, data in sorted(outputs.items()):
        target = dist / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
        written.append(target)
    for sub in ("databases", "scripts"):
        folder = dist / sub
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.name not in _KEEP and f"{sub}/{path.name}" not in outputs:
                path.unlink()
    return written


def stale_generated_files(repo: Repository, dist: Path) -> list[str]:
    """Differences between `dist` and what the canonical data generates, as
    human-readable lines: a missing file, a stale (different) file, or an
    unexpected extra one. Empty means dist/ is exactly the generated set."""
    outputs = expected_outputs(repo)
    problems: list[str] = []
    for rel, data in sorted(outputs.items()):
        target = dist / rel
        if not target.is_file():
            problems.append(f"missing: dist/{rel}")
        elif target.read_bytes() != data:
            problems.append(f"stale: dist/{rel}")
    for sub in ("databases", "scripts"):
        folder = dist / sub
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.name not in _KEEP and f"{sub}/{path.name}" not in outputs:
                problems.append(f"unexpected: dist/{sub}/{path.name}")
    return problems
