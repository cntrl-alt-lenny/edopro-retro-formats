"""Rebuild data/cards/index.json from the passcodes referenced in canonical data.

The index is the validator's ground truth for passcode<->name pairs and alias
relationships. It contains ONLY cards this repository actually references
(banlists, pools incl. variants, errata modern + historical codes), looked up
in local clones of ProjectIgnis/BabelCDB (cards.cdb, goat-entries.cdb).

Run:  python -m retroformats.importers.card_index --babelcdb /path/to/BabelCDB
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..repo import Repository, find_repo_root
from .ignis_goat import git_head, read_cdb, write_json


def collect_referenced_passcodes(repo: Repository) -> set[int]:
    refs: set[int] = set()
    for banlist in repo.banlists.values():
        for entry in banlist.entries:
            refs.add(entry.card.passcode)
    for pool in repo.pools.values():
        for card in pool.cards:
            refs.add(card.passcode)
            refs.update(card.variants)
        for key in ("include", "exclude"):
            for entry in (pool.cutoff or {}).get(key, []):
                try:
                    refs.add(int(entry.get("card", {}).get("passcode")))
                except (TypeError, ValueError):
                    pass  # validator reports the malformed entry
    for erratum in repo.errata.values():
        refs.add(erratum.modern_card.passcode)
        hist = erratum.implementation.get("historical_passcode")
        if hist:
            refs.add(int(hist))
        refs.update(int(v) for v in erratum.implementation.get("historical_variant_passcodes", []))
    for product in repo.products.values():
        for printing in product.printings:
            refs.add(printing.passcode)
    return refs


def run(babelcdb_dir: Path, root: Path) -> int:
    repo = Repository.load(root)
    refs = collect_referenced_passcodes(repo)

    cards_cdb = read_cdb(babelcdb_dir / "cards.cdb")
    goat_cdb = read_cdb(babelcdb_dir / "goat-entries.cdb")
    goat_cdb.update(read_cdb(babelcdb_dir / "cards-unofficial.cdb"))

    missing: list[int] = []
    rows = []
    for code in sorted(refs):
        row = goat_cdb.get(code) or cards_cdb.get(code)
        if row is None:
            missing.append(code)
            continue
        rows.append(
            {
                "passcode": code,
                "name": row["name"],
                "alias_of": row["alias"] or None,
                "ot": row["ot"],
            }
        )

    if missing:
        for code in missing:
            print(f"INDEX ERROR: referenced passcode {code} not found in BabelCDB", file=sys.stderr)
        return 1

    index = {
        "$schema": "../../schemas/card-index.schema.json",
        "generated_by": "retroformats.importers.card_index",
        "source": {
            "repository": "https://github.com/ProjectIgnis/BabelCDB",
            "revision": git_head(babelcdb_dir),
            "files": ["cards.cdb", "goat-entries.cdb", "cards-unofficial.cdb"],
        },
        "cards": rows,
    }
    write_json(root / "data" / "cards" / "index.json", index)
    print(f"card index: {len(rows)} cards")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--babelcdb", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = args.root or find_repo_root(Path(__file__).parent)
    return run(args.babelcdb, root)


if __name__ == "__main__":
    sys.exit(main())
