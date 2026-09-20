#!/usr/bin/env python3
"""Generate the repository's live README progress badge endpoint document."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "progress-badge.json"
AREA_KEYS = ("banlist", "card_pool", "rule_profile", "errata")
VALID_STATUSES = {"missing", "stub", "partial", "complete", "verified"}
COUNTED_STATUSES = {"complete", "verified"}


def build_payload() -> dict[str, object]:
    formats: list[dict[str, object]] = []
    complete_or_verified = 0

    for path in sorted((ROOT / "formats").glob("*/format.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        statuses = record["implementation_status"]
        areas = {key: statuses[key] for key in AREA_KEYS}
        invalid = {
            key: value
            for key, value in {**areas, "overall": statuses["overall"]}.items()
            if value not in VALID_STATUSES
        }
        if invalid:
            raise ValueError(f"{path}: invalid implementation status: {invalid}")
        complete_or_verified += sum(value in COUNTED_STATUSES for value in areas.values())
        formats.append(
            {
                "id": record["id"],
                "name": record["name"],
                "areas": areas,
                "overall": statuses["overall"],
            }
        )

    total_areas = len(formats) * len(AREA_KEYS)
    return {
        "schemaVersion": 1,
        "label": "progress",
        "message": f"{complete_or_verified}/{total_areas} areas",
        "color": "blue",
        "cacheSeconds": 300,
        "source": "formats/*/format.json implementation_status",
        "complete_or_verified_areas": complete_or_verified,
        "total_areas": total_areas,
        "formats": formats,
    }


def rendered_payload(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="check that the endpoint document is current")
    args = parser.parse_args()

    expected = rendered_payload(build_payload())
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
        if actual != expected:
            print("progress badge is stale; run python3 scripts/generate_progress_badge.py", file=sys.stderr)
            return 1
        print(f"progress badge current: {json.loads(expected)['message']}")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}: {json.loads(expected)['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
