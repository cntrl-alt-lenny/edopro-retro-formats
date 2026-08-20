"""Normalise cached release sources into canonical product records. Offline stage.

Reads the cache written by fetch_release_sources plus a local BabelCDB clone,
and writes:

- data/releases/products/*.json   (one file per product; importer-owned)
- data/releases/coverage.json     (the window the dataset claims to cover)
- data/imported/releases-report.json  (matching stats, discrepancies, gaps)

Source roles (see docs/data-sources.md):
- Yugipedia set pages are the DATE authority: per-territory English release
  dates (NA/EU/Oceanic/Worldwide) with precision taken from SMW's raw
  '1/YYYY[/M[/D]]' form - never from the day-padded timestamp.
- The YGOPRODeck bulk dump is the PRINTINGS authority: which cards appear in
  which product, under which numbers. Its single per-set tcg_date is region-
  inconsistent (verified: EU for some sets, NA for others), so it is only
  (a) a corroborating source when it equals a Yugipedia date exactly,
  (b) the fallback date when Yugipedia has none, and
  (c) a discrepancy-report trigger otherwise.
- BabelCDB cards.cdb is the identity authority: every printing is stored
  under its canonical EDOPro passcode (alias resolved when within the +/-10
  artwork window - matching upstream GOAT-list conventions, where far-alias
  alternate arts are their own entries). Cards that cannot be matched are
  reported, never guessed.

Determinism: the same cache + cdb revision produces byte-identical output.

Run:  python -m retroformats.importers.tcg_releases \
          --cache ~/.cache/retroformats --babelcdb /path/to/BabelCDB \
          [--through 2010-12-31]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

from ..model import ARTWORK_OFFSET, ReleaseEvent
from ..repo import find_repo_root
from .ignis_goat import git_head, read_cdb, slugify, write_json

SRC_YUGIPEDIA = "yugipedia-set-pages"
SRC_YGOPRODECK = "ygoprodeck-api"

WINDOW_START = "2002-03-01"  # the TCG began with LOB, 2002-03-08 (NA)

TERRITORY_BY_SLUG = {
    "na": "tcg-na",
    "eu": "tcg-eu",
    "oce": "tcg-oce",
    "ww": "tcg",
    "en": "tcg",
}

# Card frame/types that are not deck-legal cards and must not enter pools.
NON_PLAYABLE_TYPES = ("Token", "Skill Card")


def parse_smw_raw(raw: str) -> tuple[str, str] | None:
    """SMW date '1/YYYY[/M[/D]]' -> (ISO date padded to the 1st, precision).

    The leading '1' is SMW's calendar model (Gregorian). The timestamp SMW
    also returns silently pads to the 1st, so precision MUST come from here.
    """
    parts = raw.split("/")
    if not parts or parts[0] != "1" or len(parts) < 2:
        return None
    try:
        year = int(parts[1])
        month = int(parts[2]) if len(parts) > 2 else 1
        day = int(parts[3]) if len(parts) > 3 else 1
        date = _dt.date(year, month, day).isoformat()
    except ValueError:
        return None
    precision = "year" if len(parts) == 2 else "month" if len(parts) == 3 else "day"
    return date, precision


from ..model import normalise_name  # noqa: E402  (shared with the validator)


def product_kind(name: str, set_type: str | None) -> str:
    n = name.lower()
    t = (set_type or "").lower()
    if "shonen jump championship" in n or "prize card" in n:
        return "promo-tournament"
    if "shonen jump" in n or "subscription" in n:
        return "promo-subscription"
    if "tin" in n:
        return "tin"
    if "structure deck" in t or "structure deck" in n:
        return "structure"
    if "starter deck" in t or n.startswith("starter deck"):
        return "starter"
    if "booster" in t:
        return "booster"
    if "magazine" in t:
        return "promo-magazine"
    if "video game" in t:
        return "promo-videogame"
    if "promotional" in t or "promotional card" in n or "participation card" in n:
        return "promo-other"
    return "other"


def canonical_passcode(card: dict, cdb: dict[int, dict]) -> int | None:
    """Resolve a YGOPRODeck card record to its canonical EDOPro passcode.

    The top-level id is not always the printed passcode (Dark Magician's is
    46986420 while the canonical 46986414 sits in card_images), so every
    image id is a candidate. Returns None when nothing matches BabelCDB.
    """
    candidates = [int(card["id"])] + [
        int(img["id"]) for img in card.get("card_images", []) if "id" in img
    ]
    present = [c for c in dict.fromkeys(candidates) if c in cdb]
    if not present:
        return None
    for code in present:
        if cdb[code]["alias"] == 0:
            return code
    code = present[0]
    alias = cdb[code]["alias"]
    if alias and abs(code - alias) < ARTWORK_OFFSET:
        return alias
    return code


def load_cache(cache: Path) -> dict:
    data = {
        "cards": json.loads((cache / "ygoprodeck" / "cardinfo_full_misc.json").read_text(encoding="utf-8"))["data"],
        "sets": json.loads((cache / "ygoprodeck" / "cardsets.json").read_text(encoding="utf-8")),
        "yugipedia": {},
        "manifest": {},
    }
    manifest_path = cache / "fetch-manifest.json"
    if manifest_path.exists():
        data["manifest"] = json.loads(manifest_path.read_text(encoding="utf-8"))
    for slug in TERRITORY_BY_SLUG:
        path = cache / "yugipedia" / f"products_{slug}.json"
        if path.exists():
            data["yugipedia"][slug] = json.loads(path.read_text(encoding="utf-8"))["results"]
    return data


def merge_yugipedia(per_property: dict[str, dict]) -> dict[str, dict]:
    """{page title: {dates: {slug: (iso, precision)}, prefix, set_type}}."""
    merged: dict[str, dict] = {}
    for slug, results in per_property.items():
        for title, record in results.items():
            printouts = record.get("printouts", {})
            entry = merged.setdefault(title, {"dates": {}, "prefix": None, "set_type": None})
            for date_slug, prop in (
                ("na", "North American English release date"),
                ("eu", "European English release date"),
                ("oce", "Oceanic English release date"),
                ("ww", "Worldwide English release date"),
                ("en", "English release date"),
            ):
                for value in printouts.get(prop, []) or []:
                    parsed = parse_smw_raw(str(value.get("raw", "")))
                    if parsed and date_slug not in entry["dates"]:
                        entry["dates"][date_slug] = parsed
            for prefix in printouts.get("English set prefix", []) or []:
                entry["prefix"] = entry["prefix"] or str(prefix)
            for set_type in printouts.get("Set type", []) or []:
                value = set_type.get("fulltext") if isinstance(set_type, dict) else set_type
                entry["set_type"] = entry["set_type"] or str(value)
    return merged


def build_products(
    cache_data: dict,
    cdb: dict[int, dict],
    through: str,
    curated_names: set[str] | None = None,
) -> tuple[list[dict], dict]:
    """Pure normalisation: (product records sorted by id, report).

    curated_names: normalised names of curated product records already in the
    dataset - excluded from the yugipedia-only gap report since their rosters
    are covered."""
    curated_names = curated_names or set()
    report: dict = {
        "unmatched_cards": [],
        "name_mismatches": [],
        "date_discrepancies": [],
        "products_without_printings": [],
        "yugipedia_only_products": [],
        "curated_covered_products": [],
        "skipped_products": [],
        "non_playable_skipped": 0,
        "prefix_mismatched_printings": 0,
        "ot_conflicts": [],
    }
    yugipedia = merge_yugipedia(cache_data["yugipedia"])
    yugipedia_by_norm = {normalise_name(t): t for t in yugipedia}
    matched_titles: set[str] = set()

    def bounds(iso: str, precision: str):
        return ReleaseEvent._bounds(iso, precision)

    # -- product table -----------------------------------------------------
    products: dict[str, dict] = {}  # keyed by normalised ygoprodeck set_name
    for ygo_set in cache_data["sets"]:
        set_name = str(ygo_set["set_name"])
        norm = normalise_name(set_name)
        if norm in products:
            report["skipped_products"].append(
                {"product": set_name,
                 "reason": f"normalised name collides with {products[norm]['name']!r}"}
            )
            continue
        title = yugipedia_by_norm.get(norm)
        if title:
            matched_titles.add(title)
        wiki = yugipedia.get(title, {}) if title else {}
        dates = dict(wiki.get("dates", {}))
        ygo_date = ygo_set.get("tcg_date")

        # Sneak Peek / participation promos were handed out at events, not
        # sold at retail. Both kinds grant availability; the label is for
        # honesty and future per-kind policy.
        name_l = set_name.lower()
        event_kind = "event" if ("sneak peek" in name_l or "participation" in name_l) else "retail"

        events = []
        # Territory-specific properties are authoritative; the generic
        # "English release date" is a derived earliest-English value and is
        # used only when nothing else exists (verified: no 2002-2010 product
        # has it earlier than every territory date).
        if any(s in dates for s in ("na", "eu", "oce", "ww")):
            date_slugs = [s for s in ("na", "eu", "oce", "ww") if s in dates]
        elif "en" in dates:
            date_slugs = ["en"]
        else:
            date_slugs = []
        corroborated = False
        consistent = False
        for slug in date_slugs:
            iso, precision = dates[slug]
            sources = [SRC_YUGIPEDIA]
            if ygo_date:
                lo, hi = bounds(iso, precision)
                if precision == "day" and str(ygo_date) == iso:
                    # exact same day claim: genuine corroboration
                    sources.append(SRC_YGOPRODECK)
                    corroborated = True
                elif lo.isoformat() <= str(ygo_date) <= hi.isoformat():
                    # inside a coarse-precision window: consistent, but a
                    # padded-date match must not fabricate corroboration
                    consistent = True
            events.append(
                {
                    "territory": TERRITORY_BY_SLUG[slug],
                    "date": iso,
                    "precision": precision,
                    "status": "reported",
                    "kind": event_kind,
                    "sources": sources,
                }
            )
        if not events and ygo_date:
            events.append(
                {
                    "territory": "tcg",
                    "date": str(ygo_date),
                    "precision": "day",
                    "status": "reported",
                    "kind": event_kind,
                    "sources": [SRC_YGOPRODECK],
                }
            )
        elif events and ygo_date and not corroborated and not consistent:
            report["date_discrepancies"].append(
                {
                    "product": set_name,
                    "ygoprodeck": ygo_date,
                    "yugipedia": {s: dates[s][0] for s in dates},
                }
            )

        if not events:
            report["skipped_products"].append({"product": set_name, "reason": "no release date"})
            continue
        event_bounds = [bounds(e["date"], e["precision"]) for e in events]
        earliest = min(lo for lo, _ in event_bounds).isoformat()
        latest = max(hi for _, hi in event_bounds).isoformat()
        if earliest > through:
            continue  # after the import window; not an error
        if latest < WINDOW_START:
            report["skipped_products"].append(
                {"product": set_name, "reason": f"predates the TCG ({earliest})"}
            )
            continue

        products[norm] = {
            "id": slugify(set_name),
            "code": str(ygo_set.get("set_code") or (wiki.get("prefix") or "UNSET")),
            "name": set_name,
            "kind": product_kind(set_name, wiki.get("set_type")),
            "events": events,
            "yugipedia_page": title,
            "yugipedia_dated": bool(date_slugs),
            "printings": {},  # canonical passcode -> {name, numbers set}
        }

    # Yugipedia products with in-window dates that matched no YGOPRODeck set:
    # they get no printings and are therefore absent from the dataset - an
    # honest gap, not a silent one.
    for title, entry in yugipedia.items():
        if title in matched_titles or not entry["dates"]:
            continue
        if normalise_name(title) in curated_names:
            # Roster recovered into a curated product record. Reported under
            # its own key - and still requiring a gap-ledger record - so a
            # name-matching curated stub cannot silently erase the anomaly.
            report["curated_covered_products"].append(title)
            continue
        parsed = [bounds(iso, precision) for iso, precision in entry["dates"].values()]
        earliest = min(lo for lo, _ in parsed).isoformat()
        latest = max(hi for _, hi in parsed).isoformat()
        if earliest <= through and latest >= WINDOW_START:
            report["yugipedia_only_products"].append(title)

    # -- printings ----------------------------------------------------------
    for card in cache_data["cards"]:
        in_window_sets = [
            s for s in card.get("card_sets", []) if normalise_name(str(s["set_name"])) in products
        ]
        if not in_window_sets:
            continue
        if any(t in str(card.get("type", "")) for t in NON_PLAYABLE_TYPES):
            report["non_playable_skipped"] += 1
            continue
        canonical = canonical_passcode(card, cdb)
        if canonical is None:
            report["unmatched_cards"].append(
                {"ygoprodeck_id": card["id"], "name": card["name"],
                 "sets": sorted({str(s["set_name"]) for s in in_window_sets})}
            )
            continue
        cdb_row = cdb[canonical]
        if normalise_name(cdb_row["name"]) != normalise_name(str(card["name"])):
            report["name_mismatches"].append(
                {"passcode": canonical, "babelcdb": cdb_row["name"], "ygoprodeck": card["name"]}
            )
        if not cdb_row["ot"] & 0x2:
            report["ot_conflicts"].append(
                {"passcode": canonical, "name": cdb_row["name"], "ot": cdb_row["ot"],
                 "note": "printed in a TCG product but cards.cdb ot lacks the TCG bit"}
            )
        for ygo_set in in_window_sets:
            product = products[normalise_name(str(ygo_set["set_name"]))]
            slot = product["printings"].setdefault(
                canonical, {"name": cdb_row["name"], "numbers": set()}
            )
            slot["numbers"].add(str(ygo_set["set_code"]))

    # -- serialise ----------------------------------------------------------
    records = []
    used_ids: dict[str, str] = {}
    for norm in sorted(products, key=lambda n: products[n]["id"]):
        product = products[norm]
        if product["id"] in used_ids:
            report["skipped_products"].append(
                {"product": product["name"],
                 "reason": f"id collision with {used_ids[product['id']]!r}"}
            )
            continue
        used_ids[product["id"]] = product["name"]
        if not product["printings"]:
            report["products_without_printings"].append(product["name"])
        printings = [
            {
                "passcode": passcode,
                "name": slot["name"],
                "numbers": sorted(slot["numbers"]),
            }
            for passcode, slot in sorted(product["printings"].items())
        ]
        report["prefix_mismatched_printings"] += sum(
            1 for p in printings
            if p["numbers"] and not any(n.startswith(f"{product['code']}-") for n in p["numbers"])
        )
        sources = sorted({s for e in product["events"] for s in e["sources"]} | {SRC_YGOPRODECK})
        record = {
            "$schema": "../../../schemas/product-release.schema.json",
            "id": product["id"],
            "code": product["code"],
            "name": product["name"],
            "kind": product["kind"],
            "release_events": product["events"],
            "printings": printings,
            "sources": sources,
        }
        if product["yugipedia_dated"]:
            record["notes"] = f"Dates from Yugipedia set page {product['yugipedia_page']!r}; printings from the YGOPRODeck bulk dump."
        else:
            record["notes"] = "No usable Yugipedia date; single unspecified-territory date from the YGOPRODeck bulk dump."
        records.append(record)

    # deterministic report
    report["unmatched_cards"].sort(key=lambda r: (str(r["name"]), r["ygoprodeck_id"]))
    report["name_mismatches"].sort(key=lambda r: r["passcode"])
    report["date_discrepancies"].sort(key=lambda r: r["product"])
    report["products_without_printings"].sort()
    report["yugipedia_only_products"].sort()
    report["curated_covered_products"].sort()
    report["skipped_products"].sort(key=lambda r: r["product"])
    report["ot_conflicts"].sort(key=lambda r: r["passcode"])
    return records, report


def run(cache: Path, babelcdb: Path, root: Path, through: str) -> int:
    cache_data = load_cache(cache)
    if not cache_data["yugipedia"]:
        print("cache has no yugipedia/products_*.json; run fetch_release_sources first", file=sys.stderr)
        return 1
    cdb = read_cdb(babelcdb / "cards.cdb")

    # Curated product records (hand-recovered rosters, marked "curated": true)
    # are preserved across re-imports and take precedence over generated ones.
    products_dir = root / "data" / "releases" / "products"
    products_dir.mkdir(parents=True, exist_ok=True)
    curated_names: set[str] = set()
    curated_ids: set[str] = set()
    for path in sorted(products_dir.glob("*.json")):
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("curated"):
            curated_names.add(normalise_name(str(existing.get("name", ""))))
            curated_ids.add(str(existing.get("id", "")))

    records, report = build_products(
        cache_data, cdb, through, curated_names=curated_names
    )

    for stale in products_dir.glob("*.json"):
        existing = json.loads(stale.read_text(encoding="utf-8"))
        if not existing.get("curated"):
            stale.unlink()
    written = 0
    for record in records:
        if record["id"] in curated_ids:
            report["skipped_products"].append(
                {"product": record["name"], "reason": "a curated record with this id exists"}
            )
            continue
        write_json(products_dir / f"{record['id']}.json", record)
        written += 1
    report["generated_products_written"] = written
    report["curated_products_preserved"] = len(curated_ids)

    coverage = {
        "$schema": "../../schemas/releases-coverage.schema.json",
        "windows": [
            {
                "territories": ["tcg", "tcg-na", "tcg-eu", "tcg-oce"],
                "from": WINDOW_START,
                "through": through,
                "status": "complete",
                "note": (
                    "English-family TCG products enumerated from Yugipedia set pages "
                    "(all five English release-date properties) joined with the YGOPRODeck "
                    "bulk dump; see data/imported/releases-report.json for known gaps."
                ),
            }
        ],
        "known_gaps": [
            f"{len(report['products_without_printings'])} products have no printings "
            "(no YGOPRODeck card lists them; mostly repackagings and non-card products)",
            f"{len(report['unmatched_cards'])} in-window cards could not be matched to BabelCDB",
            f"{len(report['date_discrepancies'])} products where YGOPRODeck's date matches no "
            "Yugipedia date (recorded in the report; Yugipedia governs)",
            f"{len(report['yugipedia_only_products'])} Yugipedia-dated in-window products matched "
            "no YGOPRODeck set and are absent (no printing rosters available)",
            f"{report['prefix_mismatched_printings']} printings carry numbers from a different "
            "product's prefix (upstream set-membership quirks; validator warns per case)",
            "Renamed products (Magic Ruler / Spell Ruler) import as two products sharing dates",
        ],
        "sources": [SRC_YUGIPEDIA, SRC_YGOPRODECK],
    }
    write_json(root / "data" / "releases" / "coverage.json", coverage)

    stats = {
        "products_written": report.get("generated_products_written", len(records)),
        "curated_preserved": report.get("curated_products_preserved", 0),
        "printings": sum(len(r["printings"]) for r in records),
        "release_events": sum(len(r["release_events"]) for r in records),
        "unmatched_cards": len(report["unmatched_cards"]),
        "name_mismatches": len(report["name_mismatches"]),
        "date_discrepancies": len(report["date_discrepancies"]),
        "products_without_printings": len(report["products_without_printings"]),
        "yugipedia_only_products": len(report["yugipedia_only_products"]),
        "prefix_mismatched_printings": report["prefix_mismatched_printings"],
        "skipped_products": len(report["skipped_products"]),
        "non_playable_skipped": report["non_playable_skipped"],
        "ot_conflicts": len(report["ot_conflicts"]),
    }
    write_json(
        root / "data" / "imported" / "releases-report.json",
        {
            "importer": "retroformats.importers.tcg_releases",
            "window": {"from": WINDOW_START, "through": through},
            "source_revisions": {
                "ProjectIgnis/BabelCDB": git_head(babelcdb),
                "fetch_manifest": cache_data["manifest"],
            },
            "stats": stats,
            **report,
        },
    )
    print(json.dumps(stats, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--babelcdb", required=True, type=Path)
    parser.add_argument("--through", default="2010-12-31")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = args.root or find_repo_root(Path(__file__).parent)
    return run(args.cache.expanduser(), args.babelcdb, root, args.through)


if __name__ == "__main__":
    sys.exit(main())
