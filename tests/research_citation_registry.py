"""Research-citation registry check.

This is deliberately a test-suite check rather than a validator rule.  The
validator checks structured canonical records; this check audits prose and
research packets against the source registry without changing validator
findings or their meanings.

The ratchet is intentionally two-part:

* the committed backlog must describe exactly the currently unregistered
  citations; and
* current backlog URLs must be a subset of the immutable baseline set below.

Therefore a new unregistered citation cannot be hidden by adding it to the
backlog, while registering a source and removing its backlog entry is allowed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


RESEARCH_DIR = Path("docs/research")
BACKLOG_RELATIVE = Path("tests/fixtures/research-citation-backlog.json")
RESEARCH_SUFFIXES = {".md", ".json"}

# This is populated from the base-tree inventory for this round.  It is code,
# rather than mutable backlog metadata, so the backlog may shrink but cannot be
# expanded by editing only the backlog file.
BASELINE_UNREGISTERED_URLS: frozenset[str] = frozenset({
    "http://home.att.ne.jp/moon/puppiy/rule/E-rule/Data3.htm",
    "http://web.archive.org/web/20021017065706/http://home.att.ne.jp/moon/puppiy/rule/E-rule/Data3.htm",
    "http://web.archive.org/web/20051224104351/http://home.att.ne.jp/moon/puppiy/rule/E-rule/Data3.htm",
    "http://web.archive.org/web/20210827044513/https://www.yugioh-card-collection.com/entry/20190216/1550286000",
    "http://web.archive.org/web/20241209111117/https://ygoldschool.com/99-tokyodome-limit/",
    "http://web.archive.org/web/20241209111117im_/https://ygoldschool.com/wp-content/uploads/2021/09/tokyo-dome-ocg-rule.jpg",
    "http://web.archive.org/web/20250131180932/https://ygoldschool.com/tokyo-dome-tyuusi/",
    "https://archive.org/details/yugioh-official-guide-starter-book-may-05-1999",
    "https://auctions.yahoo.co.jp/jp/auction/b1233880768",
    "https://aucview.aucfan.com/yahoo/b1233880768/",
    "https://dejideji.com/1999year-vjamp/",
    "https://formatlibrary.com/api/banlists/september-2011?category=TCG",
    "https://formatlibrary.com/api/formats/tokyo-dome",
    "https://formatlibrary.com/api/formats/yugi-kaiba",
    "https://github.com/ProjectIgnis/DeltaBagooska",
    "https://github.com/ProjectIgnis/Puzzles",
    "https://github.com/edo9300/ygopro-core/blob/46779fbe40e6a9bd8967f5dc6a03f4eaa6550d57/ocgapi_constants.h",
    "https://github.com/you/goat-format-pack",
    "https://ja.wikipedia.org/wiki/Vジャンプ",
    "https://jp.mercari.com/item/m44588227599",
    "https://kperovic.com/metagame/yugioh4cb2.html?tabid=33&ArticleId=6095",
    "https://kperovic.com/metagame/yugioha1d5.html?tabid=33&ArticleId=6222",
    "https://ms.yugipedia.com//5/51/Master_Guide_p84.jpg",
    "https://ms.yugipedia.com/a/a1/2003_tournament_rulings.pdf",
    "https://ndlsearch.ndl.go.jp/books/R100000002-I000000087566",
    "https://ocg-card.com/latest/g2t/",
    "https://ocg-card.com/latest/ogs/",
    "https://ocg-card.com/limit/old/",
    "https://raw.githubusercontent.com/ProjectIgnis/CardScripts/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/goat/c504700147.lua",
    "https://raw.githubusercontent.com/ProjectIgnis/CardScripts/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c85602018.lua",
    "https://raw.githubusercontent.com/edo9300/ygopro-core/158aebe758be3c46249c75d602e3f16d63d2ef31/processor.cpp",
    "https://roadoftheking.com/deck-out/",
    "https://templeofra.neocities.org/yugioh-1999",
    "https://tenguformat.com/banlist/",
    "https://tenguformat.com/wp-content/uploads/database/allCardsTengu.json",
    "https://web-japan.org/kidsweb/ja/archives/cool/99-10-12/yugioh-j.html",
    "https://web.archive.org/web/20070103194937/http://www.upperdeckentertainment.com/yugioh/uk/faq_specific.htm",
    "https://web.archive.org/web/20110102003949/http://www.yugioh-card.com/en/gameplay/rulings/101109%20GoldSeries3_TF5%20Rulings%20-%20x.pdf",
    "https://web.archive.org/web/20110102004742/http://www.yugioh-card.com/en/gameplay/rulings/SOVR_sneak_ruling.pdf",
    "https://web.archive.org/web/20110102005218/http://www.yugioh-card.com/en/gameplay/rulings/RGBT%20Rules%20v1-2.pdf",
    "https://web.archive.org/web/20110102005442/http://www.yugioh-card.com/en/gameplay/rulings/ABPF_sneak_ruling.pdf",
    "https://web.archive.org/web/20110102005552/http://www.yugioh-card.com/en/gameplay/rulings/CRMS_sneak_ruling.pdf",
    "https://web.archive.org/web/20110102005855/http://www.yugioh-card.com/en/gameplay/penalty_guide/KDE_TCG_Tournament%20Policy_13Dec10.pdf",
    "https://web.archive.org/web/20110102005947/http://www.yugioh-card.com/en/gameplay/rulings/100325DPTin_%20HA_SDWS_ST09_Rules.pdf",
    "https://web.archive.org/web/20110626063446/http://www.yugioh-card.com:80/en/gameplay/rulings/EXVCRulesBook000512_1.2_x.pdf",
    "https://web.archive.org/web/20110712120241/http://www.yugioh-card.com:80/en/gameplay/rulings/DREVRulebook110517_v1.1x.pdf",
    "https://web.archive.org/web/20110725024153/http://www.yugioh-card.com:80/en/gameplay/rulings/ABPF%20Rules%20Booklet_110512_v1.1x.pdf",
    "https://web.archive.org/web/20110725024218/http://www.yugioh-card.com:80/en/gameplay/rulings/HA03RulesBook110323x.pdf",
    "https://web.archive.org/web/20110902060515/http://www.yugioh-card.com:80/en/gameplay/rulings/TSHDRulebook_100430.pdf",
    "https://web.archive.org/web/20110902060847/http://www.yugioh-card.com:80/en/gameplay/rulings/ANPR_sneak_ruling.pdf",
    "https://web.archive.org/web/20120807043904/http://www.yugioh-card.com/en/gameplay/errata/101105%20recent%20errata%20list%20-%20x.pdf",
    "https://web.archive.org/web/20120807043904/http://www.yugioh-card.com/en/gameplay/rulings_errata.html",
    "https://web.archive.org/web/20130203103237/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/YGOTournamentPolicy_v1-3_Jan2013.pdf",
    "https://web.archive.org/web/20130226131637/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/KDE_TCG_Tournament_Policy_Feb2013.pdf",
    "https://web.archive.org/web/20131215021346/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/KDE%20TCG%20Tournament%20Policy%20v1.4%202013November14.pdf",
    "https://web.archive.org/web/20180712131639/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/KDE-US_TCG_Tournament_Policy_v2018June01.pdf",
    "https://web.archive.org/web/20180712131741/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/YGO_Tournament_Policy_v_2018June01.pdf",
    "https://web.archive.org/web/20220516110625/https://www.yugioh-card-collection.com/entry/2018/03/08/013321",
    "https://www.angelfire.com/anime5/innovation/netrep.pdf",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=4885&ope=2",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=5131&ope=2&request_locale=en",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=9042&ope=2&request_locale=en",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=1102001&request_locale=ja&rp=99999&sess=1",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=111101000&request_locale=ja&rp=99999&sess=1",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=1111108007&request_locale=en",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=1121204008&request_locale=en&rp=99999",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=131302003&request_locale=ja&rp=99999&sess=1",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=3301003&request_locale=ja&rp=99999&sess=1",
    "https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=3301004&request_locale=ja&rp=99999&sess=1",
    "https://www.goatformat.com/home/ruling-notice-last-will",
    "https://www.latimes.com/archives/la-xpm-1999-sep-24-mn-13493-story.html",
    "https://www.mercari.com/jp/items/m38958545693/",
    "https://www.mercari.com/jp/items/m67527388590/",
    "https://www.pojo.com/yu-gi-oh/FeaturedWriters/Baneful/2017/6-19.shtml",
    "https://www.yugioh-card-collection.com/entry/2018/03/08/013321",
    "https://www.yugioh-card-collection.com/entry/20190216/1550286000",
    "https://www.yugioh-card.com/en/downloads/penalty_guide/YGOTCG_Policy_v_2_2.pdf",
    "https://www.yugioh-card.com/en/downloads/penalty_guide/YGOTCG_Tournament_Policy_v_2_5.pdf",
    "https://www.yugioh-card.com/en/products/past_products/exvc/",
    "https://www.yugioh-card.com/en/products/past_products/genf/",
    "https://www.yugioh-card.com/en/products/past_products/ha-se/",
    "https://www.yugioh-card.com/en/products/past_products/ha04/",
    "https://www.yugioh-card.com/en/products/past_products/starter2011/",
    "https://www.yugioh-card.com/en/products/past_products/stor/",
    "https://www.yugioh-card.com/en/products/past_products/tin-2011w1-wz/",
    "https://x.com/Vg_akira/status/1779107282443518237",
    "https://ygoceanbridge.blogspot.com/2022/07/blog-post_29.html?m=1",
    "https://ygoldschool.com/99-tokyodome-limit/",
    "https://ygoldschool.com/tokyo-dome-tyuusi/",
    "https://ygoldschool.com/wp-content/uploads/2021/09/tokyo-dome-ocg-rule.jpg",
    "https://ygoprodeck.com/article/master-rules-a-history-302488",
    "https://ygoprodeck.com/cube/view-cube/18262",
    "https://ygorganization.com/ogocg/",
    "https://yugioh-history.com/environment/fragments/forbidden-list-1999",
    "https://yugioh-history.com/environment/generation-one-20",
    "https://yugioh-history.com/environment/generation-one-4",
    "https://yugioh-starter.com/what-is-the-first-forbidden-cards/",
    "https://yugioh.fandom.com/wiki/Forum%3AInsect_Imitation",
    "https://yugioh.fandom.com/wiki/July_1999_Lists",
    "https://yugiohblog.konami.com/2011/ycs/ycs-toronto-first-timers-2/",
    "https://yugiohblog.konami.com/2012/ycs/12-08-toronto/yu-gi-oh-championship-series-toronto-faq/",
    "https://yugiohblog.konami.com/category/ycs/11-09-toronto/",
    "https://yugipedia.com",
    "https://yugipedia.com/wiki/August_1999_Lists",
    "https://yugipedia.com/wiki/August_1999_Lists?action=raw",
    "https://yugipedia.com/wiki/Damage_calculation",
    "https://yugipedia.com/wiki/Exodia_the_Forbidden_One?action=raw",
    "https://yugipedia.com/wiki/File:Master_Guide_p84.jpg",
    "https://yugipedia.com/wiki/Premium_Pack_(Japanese)?action=raw",
    "https://yugipedia.com/wiki/Yu-Gi-Oh!_Official_Card_Game",
})

URL_RE = re.compile(r"https?://[^\s<>\[\]\"']+")
WAYBACK_HOSTS = {"web.archive.org", "wayback.archive-it.org"}
INTERNAL_REPOSITORY_PREFIX = "/cntrl-alt-lenny/edopro-retro-formats"
REDIRECT_DESTINATIONS = {
    "http://www.yugioh-card.com/",
    "http://www.yugioh-card.com/en/",
}
REDIRECT_EXEMPTION_MARKER = (
    "<!-- citation-exempt: redirect-destination; "
    "observed HTTP-302 destination, not the cited FAQ source -->"
)


@dataclass(frozen=True)
class Occurrence:
    path: str
    line: int
    exemption: str | None = None


@dataclass
class Citation:
    url: str
    key: str
    occurrences: list[Occurrence] = field(default_factory=list)


def _trim_url(raw: str) -> str:
    """Remove prose/Markdown punctuation while preserving URL parentheses."""

    value = raw.rstrip(".,;:!?`")
    while value.endswith("]") and value.count("]") > value.count("["):
        value = value[:-1]
    while value.endswith(")") and value.count(")") > value.count("("):
        value = value[:-1]
    return value


def _url_keys(url: str) -> set[str]:
    """Return resource-level normalized keys for HTTP and HTTPS variants."""

    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return set()
    host = parsed.hostname.lower()
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    port = parsed.port
    netloc = host
    if port and port not in {80, 443}:
        netloc = f"{host}:{port}"
    # Fragment identifiers select a view of a page, not a different source.
    normalized = urlunsplit(("https", netloc, path, parsed.query, ""))
    keys = {normalized}
    # Treat HTTP and HTTPS as the same source resource.  The archive wrapper's
    # original scheme is transport metadata, not a separate historical source.
    return keys


REDIRECT_DESTINATION_KEYS = frozenset(
    key for destination in REDIRECT_DESTINATIONS for key in _url_keys(destination)
)


def _wayback_original(url: str) -> str | None:
    parsed = urlsplit(url)
    if parsed.hostname not in WAYBACK_HOSTS:
        return None
    match = re.match(r"^/(?:web|save)/\d{1,14}[a-z]*/(https?://.+)$", parsed.path)
    if not match:
        return None
    return match.group(1)


def _iter_urls(text: str):
    for url, _ in _iter_url_tokens(text):
        yield url


def _iter_url_tokens(text: str):
    for match in URL_RE.finditer(text):
        url = _trim_url(match.group(0))
        if url:
            marker = (
                REDIRECT_EXEMPTION_MARKER
                if re.match(r"[ \t]*" + re.escape(REDIRECT_EXEMPTION_MARKER), text[match.end():])
                else None
            )
            yield url, marker


def _source_registry(root: Path) -> tuple[set[str], dict[str, list[str]]]:
    payload = json.loads((root / "data/sources.json").read_text())
    keys: set[str] = set()
    owners: dict[str, list[str]] = defaultdict(list)
    for record in payload["sources"]:
        source_id = str(record["id"])
        # A record's canonical url is authoritative, and URLs in its textual
        # metadata are accepted because existing records explicitly use notes
        # to name original and related URLs.
        for value in record.values():
            if not isinstance(value, str):
                continue
            for url in _iter_urls(value):
                for key in _url_keys(url):
                    keys.add(key)
                    if source_id not in owners[key]:
                        owners[key].append(source_id)
                original = _wayback_original(url)
                if original:
                    for key in _url_keys(original):
                        keys.add(key)
                        if source_id not in owners[key]:
                            owners[key].append(source_id)
    return keys, owners


def _exemption(url: str, occurrence: Occurrence, marker: str | None = None) -> str | None:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host == "github.com" and parsed.path.lower().startswith(INTERNAL_REPOSITORY_PREFIX):
        return "internal repository navigation, not external source evidence"
    if "{" in url or "}" in url or "<" in url or ">" in url:
        return "URL template/example with an unresolved placeholder"
    if (
        occurrence.path == "docs/research/edison-behaviour-gaps.md"
        and marker == REDIRECT_EXEMPTION_MARKER
        and _url_keys(url).intersection(REDIRECT_DESTINATION_KEYS)
    ):
        return "observed HTTP-302 destination, not the cited FAQ source"
    return None


def scan_citations(root: Path) -> dict[str, Citation]:
    citations: dict[str, Citation] = {}
    research_root = root / RESEARCH_DIR
    for path in sorted(research_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in RESEARCH_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            for url, marker in _iter_url_tokens(line):
                keys = _url_keys(url)
                if not keys:
                    continue
                key = sorted(keys)[0]
                location = Occurrence(relative, line_number)
                occurrence = Occurrence(relative, line_number, _exemption(url, location, marker))
                citation = citations.setdefault(key, Citation(url=url, key=key))
                citation.occurrences.append(occurrence)
    return citations


def _load_backlog(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text())
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("backlog entries must be a list")
    result: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("url"), str):
            raise ValueError(f"malformed backlog entry: {entry!r}")
        url = entry["url"]
        keys = _url_keys(url)
        if len(keys) != 1:
            raise ValueError(f"backlog URL is not a single HTTP(S) URL: {url!r}")
        key = next(iter(keys))
        if key in result:
            raise ValueError(f"duplicate backlog URL after normalization: {url!r}")
        result[key] = entry
    return result


def unregistered_citations(root: Path) -> tuple[dict[str, Citation], dict[str, list[str]]]:
    citations = scan_citations(root)
    registered, owners = _source_registry(root)
    unregistered: dict[str, Citation] = {}
    for key, citation in citations.items():
        # A URL key is unregistered when at least one occurrence is not
        # exempt.  An exemption is a property of its use, not a license for
        # every occurrence of the same normalized resource.
        if any(occurrence.exemption is None for occurrence in citation.occurrences) and key not in registered:
            original = _wayback_original(citation.url)
            if original and _url_keys(original).isdisjoint(registered):
                unregistered[key] = citation
            elif not original and key not in registered:
                unregistered[key] = citation
    return unregistered, owners


def category(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    if host in WAYBACK_HOSTS:
        return "archived capture"
    if host in {
        "www.yugioh-card.com",
        "db.yugioh-card.com",
        "www.db.yugioh-card.com",
        "yugiohblog.konami.com",
        "www.konami.com",
        "web-japan.org",
        "ndlsearch.ndl.go.jp",
        "www.latimes.com",
    }:
        return "official or institutional page"
    if host in {"github.com", "raw.githubusercontent.com"}:
        return "repository/code page"
    return "community or other external page"


def check(root: Path, backlog_path: Path | None = None) -> list[str]:
    backlog_path = backlog_path or root / BACKLOG_RELATIVE
    errors: list[str] = []
    try:
        unregistered, _ = unregistered_citations(root)
        backlog = _load_backlog(backlog_path)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return [f"citation registry check could not load inputs: {exc}"]

    current = set(unregistered)
    listed = set(backlog)
    if current != listed:
        for key in sorted(current - listed):
            citation = unregistered[key]
            locations = ", ".join(
                f"{o.path}:{o.line}" for o in citation.occurrences if o.exemption is None
            )
            errors.append(f"unregistered citation not listed in backlog: {citation.url} ({locations})")
        for key in sorted(listed - current):
            errors.append(f"backlog entry is no longer an unregistered citation: {backlog[key]['url']}")
    baseline = {
        key
        for url in BASELINE_UNREGISTERED_URLS
        for key in _url_keys(url)
    }
    grown = listed - baseline
    for key in sorted(grown):
        errors.append(f"citation backlog grew beyond the base ratchet: {backlog[key]['url']}")
    new_unregistered = current - baseline
    for key in sorted(new_unregistered):
        citation = unregistered[key]
        errors.append(f"new unregistered citation is outside the base ratchet: {citation.url}")
    return errors


def report(root: Path, backlog_path: Path | None = None) -> str:
    backlog_path = backlog_path or root / BACKLOG_RELATIVE
    citations = scan_citations(root)
    unregistered, _ = unregistered_citations(root)
    exempt = [c for c in citations.values() if any(o.exemption for o in c.occurrences)]
    counts = Counter(category(c.url) for c in unregistered.values())
    lines = [
        f"research citation registry: {len(citations)} unique URL tokens; "
        f"{len(unregistered)} unregistered; {len(exempt)} explicit exemptions; "
        f"backlog={len(_load_backlog(backlog_path))}",
    ]
    for name in sorted(counts):
        lines.append(f"  {name}: {counts[name]}")
    errors = check(root, backlog_path)
    if errors:
        lines.append(f"FAIL ({len(errors)} finding(s))")
        lines.extend(f"  {error}" for error in errors)
    else:
        lines.append("OK")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--backlog", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    print(report(root, args.backlog.resolve() if args.backlog else None))
    return 0 if not check(root, args.backlog.resolve() if args.backlog else None) else 1


if __name__ == "__main__":
    sys.exit(main())
