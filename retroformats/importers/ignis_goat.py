"""Import Project Ignis's GOAT format implementation into canonical data.

Reads (local clones of):
- ProjectIgnis/LFLists      -> GOAT.lflist.conf     (the reference whitelist)
- ProjectIgnis/BabelCDB     -> goat-entries.cdb     ("(GOAT)" card versions)
                               cards-unofficial.cdb ("(Pre-Errata)" card versions)
                               cards.cdb            (modern card identities)

Writes:
- data/pools/pool-goat-2005-ignis.json    (canonical passcodes + variants)
- data/banlists/tcg/2005-04.json          (statuses derived from the whitelist counts)
- data/errata/*.json                      (one per pre-errata card, reuse-upstream)
- data/imported/ignis-goat-report.json    (import summary incl. the errata include
                                           list to mirror into format.json)

The whitelist's codes are decomposed into canonical identities:
- a code found in goat-entries.cdb or cards-unofficial.cdb is a historical
  implementation; its `alias` column is the modern card -> canonical passcode,
  plus an erratum record;
- a code aliasing another within +/-10 is an artwork variant -> recorded in
  variant_passcodes of its base;
- anything else is its own canonical card.

Run:  python -m retroformats.importers.ignis_goat \
          --lflists /path/to/ProjectIgnis-LFLists \
          --babelcdb /path/to/ProjectIgnis-BabelCDB
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from ..lflist import ARTWORK_OFFSET, parse_lflist
from ..model import STATUS_TO_COUNT
from ..repo import find_repo_root

COUNT_TO_STATUS = {v: k for k, v in STATUS_TO_COUNT.items()}

SRC_LFLISTS = "ignis-lflists"
SRC_BABELCDB = "ignis-babelcdb"


def git_head(path: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    return out.stdout.strip() if out.returncode == 0 else "unknown"


def read_cdb(path: Path) -> dict[int, dict]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT datas.id, datas.ot, datas.alias, texts.name, texts.desc "
            "FROM datas JOIN texts ON texts.id = datas.id"
        ).fetchall()
    finally:
        con.close()
    return {
        int(r[0]): {"ot": int(r[1]), "alias": int(r[2]), "name": r[3], "desc": r[4]}
        for r in rows
    }


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "unnamed"


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def run(lflists_dir: Path, babelcdb_dir: Path, root: Path) -> int:
    lflists_rev = git_head(lflists_dir)
    babelcdb_rev = git_head(babelcdb_dir)

    goat_text = (lflists_dir / "GOAT.lflist.conf").read_text(encoding="utf-8")
    parsed = parse_lflist(goat_text)
    if len(parsed) != 1:
        print(f"expected exactly one list in GOAT.lflist.conf, got {list(parsed)}", file=sys.stderr)
        return 1
    (source_list_name, counts) = next(iter(parsed.items()))

    cards_cdb = read_cdb(babelcdb_dir / "cards.cdb")
    override_cdb: dict[int, dict] = {}
    for cdb_name in ("goat-entries.cdb", "cards-unofficial.cdb"):
        for code, row in read_cdb(babelcdb_dir / cdb_name).items():
            row = dict(row, file=cdb_name)
            override_cdb.setdefault(code, row)

    problems: list[str] = []
    # canonical passcode ->
    #   {"count": int, "variants": set[int], "goat_code": int|None, "goat_variants": set[int]}
    canonical: dict[int, dict] = {}

    def claim(canon: int, count: int, source_code: int) -> dict:
        slot = canonical.setdefault(
            canon, {"count": count, "variants": set(), "goat_code": None, "goat_variants": set()}
        )
        if slot["count"] != count:
            problems.append(
                f"inconsistent counts for canonical {canon}: {slot['count']} vs {count} (via {source_code})"
            )
        return slot

    for code, count in sorted(counts.items()):
        override_row = override_cdb.get(code)
        if override_row is not None:
            canon = override_row["alias"]
            if canon == 0:
                problems.append(f"override entry {code} has no alias; cannot resolve canonical card")
                continue
            if canon not in cards_cdb:
                problems.append(f"override entry {code}: alias {canon} not in cards.cdb")
                continue
            slot = claim(canon, count, code)
            if slot["goat_code"] is None:
                slot["goat_code"] = code
            elif abs(code - slot["goat_code"]) < ARTWORK_OFFSET:
                # several artworks of the same historical implementation
                primary = min(code, slot["goat_code"])
                slot["goat_variants"].add(max(code, slot["goat_code"]))
                slot["goat_code"] = primary
            else:
                problems.append(
                    f"canonical {canon} has two unrelated override codes: {slot['goat_code']} and {code}"
                )
            continue
        row = cards_cdb.get(code)
        if row is None:
            problems.append(f"code {code} not in cards.cdb or goat-entries.cdb")
            continue
        alias = row["alias"]
        if alias and abs(code - alias) < ARTWORK_OFFSET and alias in counts:
            claim(alias, count, code)["variants"].add(code)
        else:
            claim(code, count, code)

    # A canonical card must never appear BOTH directly and via a goat override:
    # upstream omits the modern code when a pre-errata version exists.
    for canon, slot in canonical.items():
        if slot["goat_code"] is not None and canon in counts:
            problems.append(
                f"canonical {canon} is listed directly AND has goat override {slot['goat_code']}"
            )

    if problems:
        for p in problems:
            print(f"IMPORT ERROR: {p}", file=sys.stderr)
        return 1

    def modern_name(canon: int) -> str:
        return cards_cdb[canon]["name"]

    # ---- pool ----------------------------------------------------------
    pool_cards = []
    for canon in sorted(canonical):
        slot = canonical[canon]
        entry = {"passcode": canon, "name": modern_name(canon)}
        if slot["variants"]:
            entry["variant_passcodes"] = sorted(slot["variants"])
        pool_cards.append(entry)
    pool = {
        "$schema": "../../schemas/pool.schema.json",
        "id": "pool-goat-2005-ignis",
        "region": "TCG",
        "kind": "extensional",
        "cards": pool_cards,
        "completeness": "complete",
        "sources": [SRC_LFLISTS],
        "notes": (
            "Imported from Project Ignis's GOAT whitelist (community-vetted GOAT card pool, "
            f"source list name {source_list_name!r}). Includes cards the list pins at 0 copies: "
            "they were printed in period and are forbidden via the banlist. Canonical passcodes; "
            "pre-errata implementation codes live in data/errata/."
        ),
    }
    write_json(root / "data" / "pools" / "pool-goat-2005-ignis.json", pool)

    # ---- banlist -------------------------------------------------------
    entries = []
    for canon in sorted(canonical):
        count = canonical[canon]["count"]
        if count in COUNT_TO_STATUS:
            entries.append(
                {
                    "card": {"passcode": canon, "name": modern_name(canon)},
                    "status": COUNT_TO_STATUS[count],
                }
            )
    banlist = {
        "$schema": "../../../schemas/banlist.schema.json",
        "id": "tcg-2005-04",
        "region": "TCG",
        "effective_date": "2005-04-01",
        "superseded_by_date": "2005-10-01",
        "supersedes": None,
        "entries": entries,
        "completeness": "partial",
        "sources": [SRC_LFLISTS],
        "notes": (
            "Derived from Project Ignis's GOAT whitelist counts, restricted to the GOAT card "
            "pool. TODO: cross-check against the April 2005 TCG list as published (Yugipedia) "
            "and upgrade completeness; the effective/superseded dates are the community-"
            "documented April 1 / October 1 2005 TCG list boundaries and also need a primary "
            "citation."
        ),
    }
    write_json(root / "data" / "banlists" / "tcg" / "2005-04.json", banlist)

    # ---- errata --------------------------------------------------------
    used_slugs: dict[str, int] = {}
    erratum_ids = []
    for canon in sorted(canonical):
        slot = canonical[canon]
        goat_code = slot["goat_code"]
        if goat_code is None:
            continue
        goat_row = override_cdb[goat_code]
        base_slug = slugify(modern_name(canon))
        if base_slug in used_slugs:
            used_slugs[base_slug] += 1
            base_slug = f"{base_slug}-{used_slugs[base_slug]}"
        else:
            used_slugs[base_slug] = 1
        erratum_id = f"erratum-{base_slug}"
        erratum_ids.append(erratum_id)
        record = {
            "$schema": "../../schemas/erratum.schema.json",
            "id": erratum_id,
            "modern_card": {"passcode": canon, "name": modern_name(canon)},
            "classification": "functional",
            "changes": [
                {
                    "date_effective": None,
                    "historical_text": goat_row["desc"],
                    "modern_text": cards_cdb[canon]["desc"],
                    "summary": (
                        "Project Ignis ships a distinct GOAT-era implementation of this card, "
                        "establishing that its period behaviour/text differs from the modern "
                        "implementation. Texts transcribed from the cited databases."
                    ),
                    "sources": [SRC_BABELCDB],
                }
            ],
            "implementation": {
                "strategy": "reuse-upstream",
                "historical_passcode": goat_code,
                **(
                    {"historical_variant_passcodes": sorted(slot["goat_variants"])}
                    if slot["goat_variants"]
                    else {}
                ),
                "upstream": f"ProjectIgnis/BabelCDB {goat_row['file']} + ProjectIgnis/CardScripts",
                "script": f"c{goat_code}.lua",
                "status": "complete",
                "tested": False,
            },
            "sources": [SRC_BABELCDB, SRC_LFLISTS],
            "notes": (
                "Auto-imported. classification=functional mirrors upstream's decision to ship a "
                "separate implementation; the effective date of the modern text and a per-card "
                "review (functional vs ruling) are still TODO."
            ),
        }
        write_json(root / "data" / "errata" / f"{base_slug}.json", record)

    # ---- report --------------------------------------------------------
    report = {
        "importer": "retroformats.importers.ignis_goat",
        "source_revisions": {
            "ProjectIgnis/LFLists": lflists_rev,
            "ProjectIgnis/BabelCDB": babelcdb_rev,
        },
        "source_list_name": source_list_name,
        "stats": {
            "whitelist_codes": len(counts),
            "canonical_cards": len(canonical),
            "artwork_variants": sum(len(s["variants"]) for s in canonical.values()),
            "pre_errata_overrides": len(erratum_ids),
            "banlist_entries": len(entries),
        },
        "errata_include_for_format": erratum_ids,
    }
    write_json(root / "data" / "imported" / "ignis-goat-report.json", report)

    print(json.dumps(report["stats"], indent=2))
    print(f"sources: LFLists@{lflists_rev[:12]} BabelCDB@{babelcdb_rev[:12]}")
    print("Remember to mirror errata_include_for_format into formats/2005-04-goat/format.json")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lflists", required=True, type=Path)
    parser.add_argument("--babelcdb", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = args.root or find_repo_root(Path(__file__).parent)
    return run(args.lflists, args.babelcdb, root)


if __name__ == "__main__":
    sys.exit(main())
