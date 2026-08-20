"""Fetch the raw sources the errata research pipeline normalises. Network stage.

Downloads into a local cache directory (NEVER committed; see
docs/data-sources.md rule 3), mirroring fetch_release_sources.py conventions:
polite batching, descriptive User-Agent, a fetch manifest stamping URL,
retrieval time and byte size so the normaliser can record provenance.

Yugipedia's Card Errata namespace (ns 3010) holds one structured page per
errata'd card: an {{Errata table}} per language whose loreN parameters carry
each successive card text (with <del>/<ins> diff markup) and whose capN
captions name the printing that exemplifies each version. Those captions are
the dating evidence: the introducing set's release date bounds when the new
text became available. Set dates are fetched through the same Semantic
MediaWiki properties the release importer uses (raw 1/YYYY[/M[/D]] values
preserve precision).

Stages (run in order; each is cached and resumable):

  python -m retroformats.importers.fetch_errata_sources --cache DIR --list-namespace
      -> errata/allpages.json           every Card Errata: page title

  python -m retroformats.importers.fetch_errata_sources --cache DIR \
         --pages-for-names names.json   [--refresh]
      -> errata/pages/<slug>.json       wikitext per requested card name
                                        (missing pages recorded as absent)

  python -m retroformats.importers.fetch_errata_sources --cache DIR \
         --set-dates sets.json
      -> errata/set-dates.json          release-date printouts per set title
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = (
    "edopro-retro-formats/0.1 "
    "(https://github.com/cntrl-alt-lenny/edopro-retro-formats; open-source preservation project)"
)

YUGIPEDIA_API = "https://yugipedia.com/api.php"
ERRATA_NAMESPACE = 3010
TITLE_BATCH = 50  # anonymous API limit for multi-title queries
SET_BATCH = 15  # page-disjunction ask queries get long; stay well under URL limits
DELAY_SECONDS = 1.1  # policy: at most 1 request per second

DATE_PROPERTIES = [
    "North American English release date",
    "European English release date",
    "Oceanic English release date",
    "Worldwide English release date",
    "English release date",
]


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _api(params: dict[str, str]) -> dict:
    url = f"{YUGIPEDIA_API}?{urllib.parse.urlencode(params)}"
    payload = json.loads(_get(url).decode("utf-8"))
    time.sleep(DELAY_SECONDS)
    return payload


def _manifest(cache: Path) -> dict:
    path = cache / "errata" / "fetch-manifest.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_manifest(cache: Path, manifest: dict) -> None:
    path = cache / "errata" / "fetch-manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")


def _stamp(manifest: dict, key: str, url: str, size: int) -> None:
    manifest[key] = {
        "url": url,
        "retrieved": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "bytes": size,
    }


def slug_for(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return slug or "unnamed"


def list_namespace(cache: Path) -> None:
    out = cache / "errata" / "allpages.json"
    manifest = _manifest(cache)
    titles: list[str] = []
    apcontinue: str | None = None
    while True:
        params = {
            "action": "query",
            "list": "allpages",
            "apnamespace": str(ERRATA_NAMESPACE),
            "aplimit": "500",
            "format": "json",
        }
        if apcontinue:
            params["apcontinue"] = apcontinue
        payload = _api(params)
        batch = payload.get("query", {}).get("allpages", [])
        titles.extend(p["title"] for p in batch)
        print(f"listed {len(titles)} Card Errata pages...", file=sys.stderr)
        cont = payload.get("continue", {}).get("apcontinue")
        if not cont:
            break
        apcontinue = cont
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"titles": titles}, indent=0, ensure_ascii=False), encoding="utf-8")
    _stamp(manifest, "allpages.json", f"{YUGIPEDIA_API}?action=query&list=allpages&apnamespace={ERRATA_NAMESPACE}", out.stat().st_size)
    _save_manifest(cache, manifest)
    print(f"wrote {out} ({len(titles)} titles)")


def fetch_pages(cache: Path, names: list[str], refresh: bool) -> None:
    pages_dir = cache / "errata" / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    manifest = _manifest(cache)

    wanted: dict[str, str] = {}  # page title -> card name
    for name in names:
        path = pages_dir / f"{slug_for(name)}.json"
        if path.exists() and not refresh:
            continue
        wanted[f"Card Errata:{name}"] = name

    print(f"{len(names) - len(wanted)} cached, fetching {len(wanted)}", file=sys.stderr)
    titles = sorted(wanted)
    for i in range(0, len(titles), TITLE_BATCH):
        batch = titles[i : i + TITLE_BATCH]
        payload = _api(
            {
                "action": "query",
                "prop": "revisions",
                "rvslots": "main",
                "rvprop": "content|ids|timestamp",
                "redirects": "1",
                "titles": "|".join(batch),
                "format": "json",
            }
        )
        query = payload.get("query", {})
        # map redirected/normalised titles back to what we asked for
        asked_by_result: dict[str, str] = {t: t for t in batch}
        for entry in [*query.get("normalized", []), *query.get("redirects", [])]:
            src, dst = entry.get("from"), entry.get("to")
            for asked, current in list(asked_by_result.items()):
                if current == src:
                    asked_by_result[asked] = dst
        by_result: dict[str, str] = {v: k for k, v in asked_by_result.items()}
        for page in query.get("pages", {}).values():
            title = page.get("title", "")
            asked = by_result.get(title, title)
            name = wanted.get(asked)
            if name is None:
                continue
            out = pages_dir / f"{slug_for(name)}.json"
            if "missing" in page:
                record = {"card": name, "title": asked, "missing": True}
            else:
                rev = (page.get("revisions") or [{}])[0]
                # Yugipedia's MediaWiki predates the slots API shape: content
                # arrives at rev["*"]. Accept both forms.
                wikitext = rev.get("*") or ((rev.get("slots") or {}).get("main") or {}).get("*", "")
                record = {
                    "card": name,
                    "title": title,
                    "pageid": page.get("pageid"),
                    "revid": rev.get("revid"),
                    "revision_timestamp": rev.get("timestamp"),
                    "wikitext": wikitext,
                }
            out.write_text(json.dumps(record, indent=0, ensure_ascii=False), encoding="utf-8")
            _stamp(manifest, f"pages/{out.name}", f"{YUGIPEDIA_API} query/revisions {asked}", out.stat().st_size)
        print(f"fetched {min(i + TITLE_BATCH, len(titles))}/{len(titles)}", file=sys.stderr)
    _save_manifest(cache, manifest)


def fetch_set_dates(cache: Path, set_titles: list[str], refresh: bool) -> None:
    out = cache / "errata" / "set-dates.json"
    existing: dict[str, dict] = {}
    if out.exists() and not refresh:
        existing = json.loads(out.read_text(encoding="utf-8"))
    manifest = _manifest(cache)
    todo = sorted({t for t in set_titles if t and t not in existing})
    print(f"{len(set_titles) - len(todo)} set dates cached, fetching {len(todo)}", file=sys.stderr)

    # SMW page-name conditions do not follow redirects; resolve them first.
    resolved: dict[str, str] = {}
    for i in range(0, len(todo), TITLE_BATCH):
        batch = todo[i : i + TITLE_BATCH]
        payload = _api(
            {"action": "query", "redirects": "1", "titles": "|".join(batch), "format": "json"}
        )
        for entry in payload.get("query", {}).get("redirects", []):
            resolved[entry.get("from", "")] = entry.get("to", "")

    printouts = "|".join(f"?{p}" for p in DATE_PROPERTIES)
    for i in range(0, len(todo), SET_BATCH):
        batch = [resolved.get(t, t) for t in todo[i : i + SET_BATCH]]
        condition = "[[" + "||".join(batch) + "]]"
        payload = _api(
            {
                "action": "ask",
                "format": "json",
                "api_version": "2",
                "query": f"{condition}|{printouts}|limit={len(batch)}",
            }
        )
        results = payload.get("query", {}).get("results", {}) or {}
        found = set()
        back = {resolved.get(t, t): t for t in todo[i : i + SET_BATCH]}
        for title, row in results.items():
            asked = back.get(title, title)
            found.add(asked)
            record = {
                "fulltext": row.get("fulltext"),
                "printouts": {
                    prop: [v.get("raw") for v in (row.get("printouts", {}).get(prop) or [])]
                    for prop in DATE_PROPERTIES
                },
            }
            existing[asked] = record
            existing.setdefault(title, record)
        for title in todo[i : i + SET_BATCH]:
            if title not in found:
                existing.setdefault(title, {"missing": True})
        print(f"fetched {min(i + SET_BATCH, len(todo))}/{len(todo)}", file=sys.stderr)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(existing, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    _stamp(manifest, "set-dates.json", f"{YUGIPEDIA_API}?action=ask (page-disjunction release-date queries)", out.stat().st_size)
    _save_manifest(cache, manifest)
    print(f"wrote {out} ({len(existing)} sets)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "retroformats")
    parser.add_argument("--refresh", action="store_true", help="re-download cached files")
    parser.add_argument("--list-namespace", action="store_true", help="list every Card Errata page title")
    parser.add_argument(
        "--pages-for-names",
        type=Path,
        help="JSON file: list of card names whose Card Errata pages to fetch",
    )
    parser.add_argument(
        "--set-dates",
        type=Path,
        help="JSON file: list of set page titles whose release dates to fetch",
    )
    args = parser.parse_args(argv)

    did_something = False
    if args.list_namespace:
        list_namespace(args.cache)
        did_something = True
    if args.pages_for_names:
        names = json.loads(args.pages_for_names.read_text(encoding="utf-8"))
        fetch_pages(args.cache, list(names), args.refresh)
        did_something = True
    if args.set_dates:
        titles = json.loads(args.set_dates.read_text(encoding="utf-8"))
        fetch_set_dates(args.cache, list(titles), args.refresh)
        did_something = True
    if not did_something:
        parser.error("nothing to do: pass --list-namespace, --pages-for-names, and/or --set-dates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
