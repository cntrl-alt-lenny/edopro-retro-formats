#!/usr/bin/env python3
"""Generate the README format atlas from pinned Format Library data.

The catalog is refreshed explicitly from Format Library's public API. Ordinary
generation is offline and deterministic: canonical progress comes from
formats/*/format.json, while research-only progress is curated separately.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs" / "format-library-catalog.json"
PROGRESS_PATH = ROOT / "docs" / "format-atlas-progress.json"
OUTPUT_PATH = ROOT / "docs" / "assets" / "format-atlas.svg"
SOURCE_URL = "https://formatlibrary.com/api/formats"

AREA_KEYS = ("banlist", "card_pool", "rule_profile", "errata")
AREA_LABELS = (
    ("B", "Banlist"),
    ("P", "Card pool"),
    ("R", "Rules"),
    ("E", "Card text"),
)
STATUS_COLORS = {
    "missing": "#334155",
    "stub": "#64748b",
    "research": "#a78bfa",
    "partial": "#f59e0b",
    "complete": "#38bdf8",
    "verified": "#34d399",
}
STATUS_LABELS = {
    "missing": "Not started",
    "stub": "Stub",
    "research": "Research",
    "partial": "Partial",
    "complete": "Complete",
    "verified": "Verified",
}
ERA_ORDER = ("DM", "GX", "5D's", "ZEXAL", "ARC-V", "VRAINS", "SEVENS", "GO RUSH!!")
ERA_COLUMNS = (
    ("DM",),
    ("GX", "5D's"),
    ("ZEXAL", "ARC-V"),
    ("VRAINS", "SEVENS", "GO RUSH!!"),
)
ERA_ACCENTS = {
    "DM": "#a78bfa",
    "GX": "#2dd4bf",
    "5D's": "#38bdf8",
    "ZEXAL": "#60a5fa",
    "ARC-V": "#f472b6",
    "VRAINS": "#fb923c",
    "SEVENS": "#4ade80",
    "GO RUSH!!": "#f87171",
}
ROLLING_ORDER = {"Traditional": 0, "Genesys": 1, "Advanced": 2}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def catalog_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    raw_date = item.get("date")
    if raw_date:
        return (0, raw_date, item["category"], item["name"].casefold())
    return (1, ROLLING_ORDER.get(item["name"], 99), item["name"].casefold())


def refresh_catalog() -> dict[str, Any]:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "edopro-retro-formats format-atlas generator"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw_formats = json.load(response)

    formats = []
    for item in raw_formats:
        formats.append(
            {
                "id": item["id"],
                "name": item["name"],
                "date": item.get("date") or None,
                "banlist": item.get("banlist") or None,
                "category": item["category"],
                "era": item["era"],
                "event_name": item.get("eventName") or None,
                "is_popular": bool(item.get("isPopular")),
                "is_spotlight": bool(item.get("isSpotlight")),
            }
        )
    formats.sort(key=catalog_sort_key)

    catalog = {
        "source": SOURCE_URL,
        "retrieved_at": date.today().isoformat(),
        "description": "Pinned presentation snapshot of Format Library's public format catalog. Refresh explicitly; normal atlas generation is offline.",
        "count": len(formats),
        "formats": formats,
    }
    write_json(CATALOG_PATH, catalog)
    return catalog


def normalize_name(value: str) -> str:
    value = re.sub(r"\bformat\b", "", value, flags=re.IGNORECASE)
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def canonical_progress(catalog: dict[str, Any]) -> dict[int, dict[str, Any]]:
    by_region_and_name: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in catalog["formats"]:
        key = (item["category"], normalize_name(item["name"]))
        by_region_and_name.setdefault(key, []).append(item)

    result: dict[int, dict[str, Any]] = {}
    for path in sorted((ROOT / "formats").glob("*/format.json")):
        record = read_json(path)
        names = [record["name"], *record.get("aliases", [])]
        matches: dict[int, dict[str, Any]] = {}
        for name in names:
            key = (record["region"], normalize_name(name))
            for item in by_region_and_name.get(key, []):
                matches[item["id"]] = item
        if len(matches) != 1:
            labels = ", ".join(sorted(item["name"] for item in matches.values())) or "none"
            raise ValueError(f"{record['id']} must match exactly one Format Library entry; found {labels}")

        format_library_id = next(iter(matches))
        statuses = record["implementation_status"]
        areas = {key: statuses[key] for key in AREA_KEYS}
        result[format_library_id] = {
            "kind": "canonical",
            "format_id": record["id"],
            "areas": areas,
            "overall": statuses["overall"],
        }
    return result


def combined_progress(catalog: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result = canonical_progress(catalog)
    overrides = read_json(PROGRESS_PATH)
    valid_ids = {item["id"] for item in catalog["formats"]}
    for raw_id, override in overrides["formats"].items():
        item_id = int(raw_id)
        if item_id not in valid_ids:
            raise ValueError(f"research progress references unknown Format Library id {item_id}")
        if item_id in result:
            raise ValueError(f"Format Library id {item_id} is both canonical and research-only")
        areas = override["areas"]
        if set(areas) != set(AREA_KEYS):
            raise ValueError(f"research progress for id {item_id} must define exactly {AREA_KEYS}")
        unknown = set(areas.values()) - set(STATUS_COLORS)
        if unknown:
            raise ValueError(f"research progress for id {item_id} uses unknown statuses: {sorted(unknown)}")
        result[item_id] = override
    return result


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def format_date(raw_date: str | None) -> str:
    if not raw_date:
        return "live"
    return f"{raw_date[2:4]}.{raw_date[5:7]}"


def year_span(items: list[dict[str, Any]]) -> str:
    years = [item["date"][:4] for item in items if item.get("date")]
    if not years:
        return "current"
    if years[0] == years[-1]:
        return years[0]
    return f"{years[0]}–{years[-1]}"


def text_size(name: str) -> float:
    length = len(name)
    if length >= 18:
        return 7.0
    if length >= 15:
        return 7.6
    if length >= 12:
        return 8.2
    return 8.8


def render_tile(
    item: dict[str, Any],
    progress: dict[int, dict[str, Any]],
    x: float,
    y: float,
) -> list[str]:
    state = progress.get(item["id"])
    areas = state["areas"] if state else {key: "missing" for key in AREA_KEYS}
    kind = state["kind"] if state else "planned"
    stroke = "#25334a"
    stroke_width = "0.8"
    filter_attr = ""
    if kind == "canonical":
        stroke = "#38bdf8"
        stroke_width = "1.2"
        filter_attr = ' filter="url(#soft-glow)"'
    elif kind == "research":
        stroke = "#a78bfa"
        stroke_width = "1.1"

    territory = "O" if item["category"] == "OCG" else "T"
    territory_color = "#fb7185" if territory == "O" else "#60a5fa"
    metadata = " ".join(
        [
            f'data-format-id="{item["id"]}"',
            f'data-format-name="{esc(item["name"])}"',
            f'data-category="{item["category"]}"',
            f'data-kind="{kind}"',
            *[f'data-{key.replace("_", "-")}="{areas[key]}"' for key in AREA_KEYS],
        ]
    )
    lines = [f'      <g class="format" {metadata}>']
    lines.append(
        f'        <rect x="{x:.1f}" y="{y:.1f}" width="132" height="27" rx="7" '
        f'fill="#111b2e" stroke="{stroke}" stroke-width="{stroke_width}"{filter_attr}/>'
    )
    lines.append(
        f'        <circle cx="{x + 9:.1f}" cy="{y + 10:.1f}" r="5" fill="{territory_color}" opacity="0.92"/>'
    )
    lines.append(
        f'        <text x="{x + 9:.1f}" y="{y + 12.3:.1f}" text-anchor="middle" '
        f'font-size="6.2" font-weight="800" fill="#07111f">{territory}</text>'
    )
    lines.append(
        f'        <text x="{x + 18:.1f}" y="{y + 12.8:.1f}" font-size="{text_size(item["name"]):.1f}" '
        f'font-weight="650" fill="#e5edf8">{esc(item["name"])}</text>'
    )
    lines.append(
        f'        <text x="{x + 127:.1f}" y="{y + 12.8:.1f}" text-anchor="end" '
        f'font-size="7.2" fill="#7f91aa">{format_date(item.get("date"))}</text>'
    )
    bar_x = x + 7
    for key in AREA_KEYS:
        color = STATUS_COLORS[areas[key]]
        lines.append(
            f'        <rect x="{bar_x:.1f}" y="{y + 21.5:.1f}" width="27.5" height="2.5" '
            f'rx="1.25" fill="{color}"/>'
        )
        bar_x += 30.5
    lines.append("      </g>")
    return lines


def render_svg(catalog: dict[str, Any]) -> str:
    progress = combined_progress(catalog)
    formats_by_era = {
        era: [item for item in catalog["formats"] if item["era"] == era]
        for era in ERA_ORDER
    }

    width = 1200
    top = 132.0
    column_xs = (30.0, 320.0, 610.0, 900.0)
    tile_gap_x = 8.0
    row_step = 32.0
    section_gap = 13.0
    section_header_height = 27.0
    content_bottom = top
    body: list[str] = []

    for column_x, eras in zip(column_xs, ERA_COLUMNS):
        y = top
        for era in eras:
            items = formats_by_era[era]
            accent = ERA_ACCENTS[era]
            body.append(
                f'    <g class="era" data-era="{esc(era)}">\n'
                f'      <rect x="{column_x:.1f}" y="{y:.1f}" width="272" height="21" rx="6" '
                f'fill="{accent}" opacity="0.10"/>\n'
                f'      <rect x="{column_x:.1f}" y="{y:.1f}" width="3" height="21" rx="1.5" fill="{accent}"/>\n'
                f'      <text x="{column_x + 11:.1f}" y="{y + 14.2:.1f}" font-size="10" font-weight="750" '
                f'letter-spacing="0.8" fill="{accent}">{esc(era)}</text>\n'
                f'      <text x="{column_x + 262:.1f}" y="{y + 14.2:.1f}" text-anchor="end" font-size="8" '
                f'fill="#71839d">{year_span(items)} · {len(items)}</text>\n'
                f'    </g>'
            )
            y += section_header_height
            for index, item in enumerate(items):
                tile_x = column_x + (index % 2) * (132 + tile_gap_x)
                tile_y = y + (index // 2) * row_step
                body.extend(render_tile(item, progress, tile_x, tile_y))
            rows = (len(items) + 1) // 2
            y += rows * row_step + section_gap
        content_bottom = max(content_bottom, y)

    height = int(content_bottom + 34)
    source_host = "formatlibrary.com"
    legend_x = 32
    area_legend: list[str] = []
    for short, label in AREA_LABELS:
        area_legend.append(
            f'    <rect x="{legend_x}" y="88" width="18" height="18" rx="5" fill="#17233a" stroke="#2a3a54"/>\n'
            f'    <text x="{legend_x + 9}" y="100.5" text-anchor="middle" font-size="8" font-weight="800" fill="#d9e5f5">{short}</text>\n'
            f'    <text x="{legend_x + 24}" y="100.5" font-size="9" fill="#8ea0ba">{label}</text>'
        )
        legend_x += 108

    status_x = 622
    status_legend: list[str] = []
    for status in ("missing", "stub", "research", "partial", "complete", "verified"):
        status_legend.append(
            f'    <circle cx="{status_x}" cy="97" r="4" fill="{STATUS_COLORS[status]}"/>\n'
            f'    <text x="{status_x + 9}" y="100.5" font-size="8.5" fill="#8ea0ba">{STATUS_LABELS[status]}</text>'
        )
        status_x += 91

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="atlas-title atlas-desc">
  <title id="atlas-title">Yu-Gi-Oh! historical format implementation atlas</title>
  <desc id="atlas-desc">All {catalog['count']} formats in the pinned Format Library catalog, ordered by era and date. Four coloured bars on every format show this repository's banlist, card pool, rules, and historical card text progress.</desc>
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#07101f"/>
      <stop offset="0.55" stop-color="#0b1426"/>
      <stop offset="1" stop-color="#111827"/>
    </linearGradient>
    <radialGradient id="aura-a">
      <stop offset="0" stop-color="#7c3aed" stop-opacity="0.16"/>
      <stop offset="1" stop-color="#7c3aed" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="aura-b">
      <stop offset="0" stop-color="#0284c7" stop-opacity="0.15"/>
      <stop offset="1" stop-color="#0284c7" stop-opacity="0"/>
    </radialGradient>
    <filter id="soft-glow" x="-20%" y="-50%" width="140%" height="200%">
      <feGaussianBlur stdDeviation="1.4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" rx="18" fill="url(#panel)"/>
  <ellipse cx="105" cy="20" rx="300" ry="170" fill="url(#aura-a)"/>
  <ellipse cx="1090" cy="15" rx="330" ry="180" fill="url(#aura-b)"/>
  <g font-family="Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif">
    <text x="32" y="37" font-size="18" font-weight="800" letter-spacing="2.2" fill="#f3f7fc">FORMAT ATLAS</text>
    <text x="32" y="59" font-size="10.5" fill="#91a3bd">Format Library chronology · repository implementation coverage</text>
    <rect x="1018" y="25" width="150" height="30" rx="15" fill="#101d32" stroke="#2b3d59"/>
    <text x="1093" y="44.5" text-anchor="middle" font-size="10" font-weight="700" fill="#c9d8eb">{catalog['count']} FORMATS · TCG + OCG</text>
{chr(10).join(area_legend)}
{chr(10).join(status_legend)}
    <line x1="30" y1="119" x2="1170" y2="119" stroke="#26354d"/>
{chr(10).join(body)}
    <text x="32" y="{height - 18}" font-size="8" fill="#61738e">Pinned from {source_host} · canonical colours are generated from format.json · catalog {esc(catalog['retrieved_at'])}</text>
    <text x="1168" y="{height - 18}" text-anchor="end" font-size="8" fill="#61738e">T = TCG · O = OCG · chronological within each era</text>
  </g>
</svg>
'''
    return svg


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="refresh the pinned catalog from Format Library before rendering")
    parser.add_argument("--check", action="store_true", help="fail if the checked-in SVG differs from a fresh offline render")
    args = parser.parse_args()

    if args.refresh:
        catalog = refresh_catalog()
    else:
        if not CATALOG_PATH.exists():
            parser.error(f"{CATALOG_PATH.relative_to(ROOT)} does not exist; run with --refresh")
        catalog = read_json(CATALOG_PATH)

    rendered = render_svg(catalog)
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            print(f"stale: {OUTPUT_PATH.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"ok: {OUTPUT_PATH.relative_to(ROOT)} ({catalog['count']} formats)")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"generated {OUTPUT_PATH.relative_to(ROOT)} ({catalog['count']} formats)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
