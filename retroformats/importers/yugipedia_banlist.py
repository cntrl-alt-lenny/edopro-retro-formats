"""Import a TCG Forbidden/Limited list from a Yugipedia 'Limitation list' page.

Input: the raw JSON of a MediaWiki parse API call, fetched separately, e.g.:

    curl -o march2010.json 'https://yugipedia.com/api.php?action=parse&page=March%202010%20Lists%20(TCG)&format=json&prop=wikitext'

(The raw fetch is a cache and is NOT committed; only the distilled banlist
record is, citing the page and the Konami references it carries.)

Card names are resolved to passcodes against a local BabelCDB cards.cdb;
every unresolved or ambiguous name aborts the import — no guessing.

Run:  python -m retroformats.importers.yugipedia_banlist \
          --wikitext march2010.json --babelcdb /path/to/BabelCDB \
          --id tcg-2010-03 --sources yugipedia-march-2010 konami-limited-2010-03
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ..repo import find_repo_root
from .ignis_goat import read_cdb, write_json

_FIELD_RE = re.compile(r"^\|\s*(\w+)\s*=\s*(.*)$")


def parse_limitation_list(wikitext: str) -> dict[str, object]:
    """Extract the {{Limitation list}} template fields as {field: [names]}."""
    fields: dict[str, list[str]] = {}
    meta: dict[str, str] = {}
    current: str | None = None
    in_template = False
    for line in wikitext.splitlines():
        stripped = line.strip()
        if stripped.startswith("{{Limitation list"):
            in_template = True
            continue
        if not in_template:
            continue
        if stripped.startswith("}}"):
            break
        m = _FIELD_RE.match(stripped)
        if m:
            key, rest = m.group(1), m.group(2).strip()
            if key in ("forbidden", "limited", "semi_limited", "no_longer_on_list"):
                current = key
                fields[current] = []
                rest = ""
            else:
                current = None
                meta[key] = rest
            if not rest:
                continue
            stripped = rest
        if current is None or not stripped:
            continue
        # strip the "// prev::Status" change annotations and [[links]]
        name = stripped.split("//")[0].strip()
        name = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", name)
        if name:
            fields[current].append(name)
    return {"fields": fields, "meta": meta}


def resolve_names(names: list[str], cards_cdb: dict[int, dict]) -> tuple[dict[str, int], list[str]]:
    by_name: dict[str, list[int]] = {}
    for code, row in cards_cdb.items():
        by_name.setdefault(row["name"], []).append(code)
    resolved: dict[str, int] = {}
    problems: list[str] = []
    for name in names:
        codes = by_name.get(name)
        if not codes:
            problems.append(f"name not found in cards.cdb: {name!r}")
            continue
        # Prefer the base printing (alias == 0); artwork variants alias it.
        base = [c for c in codes if cards_cdb[c]["alias"] == 0]
        if len(base) == 1:
            resolved[name] = base[0]
        elif len(codes) == 1:
            resolved[name] = codes[0]
        else:
            problems.append(f"ambiguous name {name!r}: candidate passcodes {sorted(codes)}")
    return resolved, problems


def run(
    wikitext_path: Path,
    babelcdb_dir: Path,
    root: Path,
    banlist_id: str,
    source_ids: list[str],
    page_note: str,
) -> int:
    raw = json.loads(wikitext_path.read_text(encoding="utf-8"))
    wikitext = raw["parse"]["wikitext"]["*"]
    page_title = raw["parse"]["title"]
    parsed = parse_limitation_list(wikitext)
    fields = parsed["fields"]
    meta = parsed["meta"]

    cards_cdb = read_cdb(babelcdb_dir / "cards.cdb")

    status_map = {"forbidden": "forbidden", "limited": "limited", "semi_limited": "semilimited"}
    entries = []
    problems: list[str] = []
    for field, status in status_map.items():
        names = fields.get(field, [])
        resolved, field_problems = resolve_names(names, cards_cdb)
        problems.extend(field_problems)
        for name in names:
            if name in resolved:
                entries.append(
                    {"card": {"passcode": resolved[name], "name": name}, "status": status}
                )
    if problems:
        for p in problems:
            print(f"IMPORT ERROR: {p}", file=sys.stderr)
        return 1

    entries.sort(key=lambda e: (e["status"], e["card"]["passcode"]))

    def _date(us_date: str) -> str | None:
        m = re.match(r"(\w+) (\d+), (\d{4})", us_date or "")
        if not m:
            return None
        months = "January February March April May June July August September October November December".split()
        return f"{m.group(3)}-{months.index(m.group(1)) + 1:02d}-{int(m.group(2)):02d}"

    start = _date(meta.get("start_date", ""))
    end = _date(meta.get("end_date", ""))
    if start is None:
        print(f"IMPORT ERROR: could not parse start_date {meta.get('start_date')!r}", file=sys.stderr)
        return 1

    region_dir = banlist_id.split("-")[0]
    banlist = {
        "$schema": "../../../schemas/banlist.schema.json",
        "id": banlist_id,
        "region": "TCG" if region_dir == "tcg" else "OCG",
        "effective_date": start,
        "superseded_by_date": end and _next_day(end),
        "supersedes": None,
        "entries": entries,
        "completeness": "complete",
        "sources": source_ids,
        "notes": (
            f"Transcribed from Yugipedia page {page_title!r} ({page_note}); the page cites "
            "Konami's own list (see the source registry entries). Names resolved to passcodes "
            "against ProjectIgnis/BabelCDB cards.cdb, preferring base printings (alias=0). "
            f"Yugipedia also records: no_longer_on_list = {fields.get('no_longer_on_list', [])}."
        ),
    }
    out = root / "data" / "banlists" / region_dir / f"{banlist_id.split('-', 1)[1]}.json"
    write_json(out, banlist)
    counts = {s: sum(1 for e in entries if e["status"] == s) for s in ("forbidden", "limited", "semilimited")}
    print(f"wrote {out} ({counts})")
    return 0


def _next_day(iso: str) -> str:
    import datetime as dt

    return (dt.date.fromisoformat(iso) + dt.timedelta(days=1)).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wikitext", required=True, type=Path, help="saved MediaWiki parse JSON")
    parser.add_argument("--babelcdb", required=True, type=Path)
    parser.add_argument("--id", required=True, help="banlist id, e.g. tcg-2010-03")
    parser.add_argument("--sources", required=True, nargs="+", help="source registry ids to cite")
    parser.add_argument("--page-note", default="MediaWiki parse API")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = args.root or find_repo_root(Path(__file__).parent)
    return run(args.wikitext, args.babelcdb, root, args.id, args.sources, args.page_note)


if __name__ == "__main__":
    sys.exit(main())
