"""Fetch the raw sources the TCG release importer normalises. Network stage.

Downloads into a local cache directory (NEVER committed; see
docs/data-sources.md rule 3):

- YGOPRODeck bulk dumps (their API guide instructs consumers to download once
  and store locally):
    cardinfo.php?misc=yes   -> ygoprodeck/cardinfo_full_misc.json  (~25 MB)
    cardsets.php            -> ygoprodeck/cardsets.json
- Yugipedia product release dates via Semantic MediaWiki ask queries, one per
  English-family release-date property (their API policy names card-database
  building as an anticipated use; max 1 req/s, descriptive User-Agent):
    yugipedia/products_<property-slug>.json

Existing cache files are kept (pass --refresh to re-download). A
fetch-manifest.json records URL, retrieval time, and byte size per file so the
normaliser can stamp provenance.

Run:  python -m retroformats.importers.fetch_release_sources \
          --cache ~/.cache/retroformats [--through 2010-12-31] [--refresh]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = (
    "edopro-retro-formats/0.1 "
    "(https://github.com/cntrl-alt-lenny/edopro-retro-formats; open-source preservation project)"
)

YGOPRODECK_CARDINFO = "https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes"
YGOPRODECK_CARDSETS = "https://db.ygoprodeck.com/api/v7/cardsets.php"
YUGIPEDIA_API = "https://yugipedia.com/api.php"

# The English-family release-date properties on Yugipedia set pages. A product
# is enumerated if ANY of them falls inside the window, so Europe-only
# products (Retro Pack) and NA-only promos are all captured.
DATE_PROPERTIES = {
    "na": "North American English release date",
    "eu": "European English release date",
    "oce": "Oceanic English release date",
    "ww": "Worldwide English release date",
    "en": "English release date",
}
EXTRA_PRINTOUTS = ["English set prefix", "Set type"]

YUGIPEDIA_DELAY_SECONDS = 1.1  # policy: at most 1 request per second


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _fetch_to(path: Path, url: str, manifest: dict, refresh: bool) -> None:
    if path.exists() and not refresh:
        print(f"cached  {path.name}")
        return
    print(f"fetch   {url}")
    payload = _fetch(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    manifest[str(path.name)] = {
        "url": url,
        "retrieved": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "bytes": len(payload),
    }


def _ask_query(prop: str, window_start: str, window_end: str, offset: int) -> str:
    printouts = "|".join(f"?{p}" for p in [*DATE_PROPERTIES.values(), *EXTRA_PRINTOUTS])
    query = (
        f"[[Medium::TCG]][[Page type::Set page]]"
        f"[[{prop}::>{window_start}]][[{prop}::<{window_end}]]"
        f"|{printouts}|limit=500|offset={offset}"
    )
    return f"{YUGIPEDIA_API}?action=ask&format=json&api_version=2&query={urllib.parse.quote(query)}"


def fetch_yugipedia_products(
    cache: Path, window_start: str, window_end: str, manifest: dict, refresh: bool
) -> None:
    for slug, prop in DATE_PROPERTIES.items():
        out = cache / "yugipedia" / f"products_{slug}.json"
        if out.exists() and not refresh:
            print(f"cached  {out.name}")
            continue
        pages: dict = {}
        offset = 0
        while True:
            url = _ask_query(prop, window_start, window_end, offset)
            print(f"fetch   yugipedia ask {prop!r} offset {offset}")
            payload = json.loads(_fetch(url))
            if "error" in payload or "query" not in payload:
                # never cache an error response as an empty result set
                raise RuntimeError(f"yugipedia ask failed for {prop!r}: {payload.get('error', payload)}")
            results = payload.get("query", {}).get("results", {})
            # api_version=2 returns a dict keyed by page title
            pages.update(results)
            cont = payload.get("query-continue-offset")
            if not cont:
                break
            offset = int(cont)
            time.sleep(YUGIPEDIA_DELAY_SECONDS)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump({"property": prop, "results": pages}, fh, indent=1, ensure_ascii=False)
        manifest[out.name] = {
            "url": _ask_query(prop, window_start, window_end, 0),
            "retrieved": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "pages": len(pages),
        }
        time.sleep(YUGIPEDIA_DELAY_SECONDS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--window-start", default="2002-01-01")
    parser.add_argument(
        "--through",
        default="2010-12-31",
        help="fetch products whose release dates fall on or before this date",
    )
    parser.add_argument("--refresh", action="store_true", help="re-download cached files")
    args = parser.parse_args()

    cache: Path = args.cache.expanduser()
    manifest_path = cache / "fetch-manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # ask's date range operators exclude the endpoints we pass, so widen by a day.
    start = (_dt.date.fromisoformat(args.window_start) - _dt.timedelta(days=1)).isoformat()
    end = (_dt.date.fromisoformat(args.through) + _dt.timedelta(days=1)).isoformat()

    _fetch_to(cache / "ygoprodeck" / "cardinfo_full_misc.json", YGOPRODECK_CARDINFO, manifest, args.refresh)
    _fetch_to(cache / "ygoprodeck" / "cardsets.json", YGOPRODECK_CARDSETS, manifest, args.refresh)
    fetch_yugipedia_products(cache, start, end, manifest, args.refresh)

    with manifest_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"manifest -> {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
