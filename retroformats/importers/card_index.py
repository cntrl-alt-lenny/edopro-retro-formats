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

from ..lflist import MalformedHistoricalIdentity, _usable_v2, historical_identity
from ..model import ErratumV2
from ..repo import Repository, find_repo_root
from .ignis_goat import git_head, read_cdb, write_json


def collect_referenced_passcodes(repo: Repository) -> set[int]:
    """Every canonical passcode the repository can legitimately reference —
    not merely codes GOAT/Edison currently emit. Mixed v1/v2 corpus: a v1
    `Erratum` and a v2 `ErratumV2` carry historical identity in genuinely
    different shapes (design doc §8's hard legacy/v2 boundary — no shared
    representation), so each is read through its own native API rather than
    a common dict-shaped guess."""
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
        if isinstance(erratum, ErratumV2):
            # `implementation_metadata[]` is deliberately never touched here:
            # it is workflow/research metadata orthogonal to Coverage
            # entirely (model.py's own ImplementationMetadata docstring),
            # never a card identity. Only kinds that claim an executable
            # historical substitution (REUSE_UPSTREAM/CUSTOM_SCRIPT) carry a
            # passcode at all — `_usable_v2()` is the same gate lflist.py
            # itself uses, so "referenced" here means exactly what "usable
            # substitution" means everywhere else in this codebase, not a
            # second, drifting definition. MODERN/NONE_NEEDED/KNOWN_GAP/
            # UNRESOLVED never reach `historical_identity()` at all.
            for coverage in erratum.authored_states.values():
                usable = _usable_v2(coverage)
                if usable is None:
                    continue
                try:
                    passcode, variants = historical_identity(usable)
                except MalformedHistoricalIdentity:
                    continue  # validator reports the malformed entry
                refs.add(passcode)
                refs.update(variants)
            # reference_identities[] is an exact, sourced identity claim in
            # its own right (model.py's ReferenceIdentity docstring) — not
            # gated by a Coverage kind at all, since it isn't Coverage.
            for identity in erratum.reference_identities:
                try:
                    passcode, variants = historical_identity(identity)
                except MalformedHistoricalIdentity:
                    continue  # validator reports the malformed entry
                refs.add(passcode)
                refs.update(variants)
            continue
        # Legacy v1 (unchanged): EVERY version's implementation, not just the
        # baseline — a card with multiple historical revisions carries one
        # per change, and a code the build can emit must be identifiable.
        implementations = [
            erratum.implementation,
            *(c.get("resulting_implementation") for c in erratum.changes),
        ]
        for impl in implementations:
            if not impl:
                continue
            hist = impl.get("historical_passcode")
            if hist:
                refs.add(int(hist))
            refs.update(int(v) for v in impl.get("historical_variant_passcodes", []) or [])
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
