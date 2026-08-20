"""Normalise cached errata research sources into per-card research packets.

Offline stage (network material comes from fetch_errata_sources.py; upstream
repository checkouts are pinned local clones). For every card under research
this produces a deterministic JSON packet gathering ALL the evidence a
per-card review needs, plus mechanically derived chronology candidates:

- the English text lineage from Yugipedia's Card Errata page ({{Errata
  table}} lore/caption parameters), each version's clean text and the
  printing/set that exemplifies it;
- release dates for those sets (from data/releases/ when in-window, else
  from the fetched set-dates cache), with SMW raw precision preserved;
- the historical and modern card texts from the pinned BabelCDB checkout and
  which lineage version each one matches (exact after normalisation, or the
  best fuzzy match with its ratio);
- the pinned CardScripts historical vs modern Lua scripts, their upstream
  annotation comments, and a normalised unified diff;
- mechanical chronology candidates: for the transition between the matched
  historical and modern versions, the earliest possible TCG date of each
  intermediate version's exemplifying printing (new_attested_from bounds).

The packets are evidence carriers, not decisions: classification and any
effective-date claims stronger than the mechanical bounds must come from the
per-card review, citing sources. Nothing here invents dates.

Run:  python -m retroformats.importers.errata_research \
          --cache ~/.cache/retroformats --repos ~/.cache/retroformats/repos \
          [--names research-names.json] [--out DIR]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT_MARKER = ("formats", "data")

# ---------------------------------------------------------------------------
# wikitext parsing


def split_language_sections(wikitext: str) -> dict[str, str]:
    """{'English': section text, ...}; text before any heading maps to ''."""
    sections: dict[str, str] = {}
    current = ""
    buf: list[str] = []
    for line in wikitext.splitlines():
        m = re.match(r"^==\s*([^=]+?)\s*==\s*$", line)
        if m:
            sections[current] = "\n".join(buf)
            current = m.group(1)
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf)
    return sections


def find_templates(text: str, name: str) -> list[str]:
    """Bodies of every {{name ...}} template invocation, brace-balanced."""
    out: list[str] = []
    lowered = text.casefold()
    needle = "{{" + name.casefold()
    start = 0
    while True:
        i = lowered.find(needle, start)
        if i < 0:
            return out
        depth = 0
        j = i
        while j < len(text) - 1:
            pair = text[j : j + 2]
            if pair == "{{":
                depth += 1
                j += 2
            elif pair == "}}":
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        out.append(text[i + 2 : j - 2])
        start = j


def template_params(body: str) -> dict[str, str]:
    """Split a template body into params on top-level pipes."""
    depth_brace = depth_bracket = 0
    parts: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(body):
        two = body[i : i + 2]
        if two == "{{":
            depth_brace += 1
            buf.append(two)
            i += 2
            continue
        if two == "}}" and depth_brace:
            depth_brace -= 1
            buf.append(two)
            i += 2
            continue
        if two == "[[":
            depth_bracket += 1
            buf.append(two)
            i += 2
            continue
        if two == "]]" and depth_bracket:
            depth_bracket -= 1
            buf.append(two)
            i += 2
            continue
        if body[i] == "|" and not depth_brace and not depth_bracket:
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(body[i])
        i += 1
    parts.append("".join(buf))

    params: dict[str, str] = {}
    for part in parts[1:]:  # parts[0] is the template name
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        params[key.strip()] = value.strip()
    return params


_LINK_RE = re.compile(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]")


def clean_lore(raw: str) -> str:
    """A version's plain text: strip diff markup (keeping content), links,
    quotes and layout markup; collapse whitespace."""
    text = raw
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # The <hr>/<p> blocks carry Japanese ATK/DEF footers - drop them entirely.
    text = re.sub(r"<hr[^>]*/?>.*$", "", text, flags=re.S)
    text = re.sub(r"</?(?:del|ins|b|i|u|sup|sub|span|small|nowiki)[^>]*>", "", text)
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"\{\{Ruby\|([^|}]*)\|[^}]*\}\}", r"\1", text, flags=re.I)
    text = _LINK_RE.sub(lambda m: m.group(2) if m.group(2) is not None else m.group(1), text)
    text = text.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", text).strip()


# Caption links that qualify a printing rather than naming its product.
_NON_SET_LINKS = {"1st edition", "unlimited edition", "limited edition"}

# Caption set links that are ambiguous or OCG-titled on Yugipedia; map to the
# TCG set page that actually dates the pictured printing.
SET_ALIASES = {
    "Structure Deck: Marik": "Structure Deck: Marik (TCG)",
    "Structure Deck: Onslaught of the Fire Kings": "Onslaught of the Fire Kings Structure Deck",
}


def parse_caption(raw: str) -> dict:
    """Card number and set links from a capN parameter. The last set link is
    the product the pictured printing actually came from (italicised reprint
    qualifiers follow the original set link); edition-qualifier links are not
    products."""
    links = _LINK_RE.findall(raw or "")
    number = None
    sets: list[str] = []
    for target, _display in links:
        target = target.strip()
        if not target or target.casefold() in _NON_SET_LINKS:
            continue
        if number is None and re.match(r"^[A-Z0-9]{2,6}-[A-Z]{0,3}\d{1,3}$", target):
            number = target
        elif re.match(r"^[A-Z0-9]{2,6}-\d{1,3}$", target) and number is None:
            number = target
        else:
            sets.append(SET_ALIASES.get(target, target))
    return {"number": number, "sets": sets, "dating_set": sets[-1] if sets else None}


def parse_errata_tables(wikitext: str) -> dict[str, list[dict]]:
    """{language: [version entries]} from every {{Errata table}} on a page."""
    out: dict[str, list[dict]] = {}
    for section, text in split_language_sections(wikitext).items():
        for body in find_templates(text, "Errata table"):
            params = template_params(body)
            lang = params.get("lang", "en")
            language = section or ("Japanese" if lang == "ja" else "English")
            versions: list[dict] = []
            indices = sorted(
                {int(m.group(1)) for k in params for m in [re.match(r"lore(\d+)$", k)] if m}
            )
            for i in indices:
                cap = parse_caption(params.get(f"cap{i}", ""))
                versions.append(
                    {
                        "index": i,
                        "text": clean_lore(params.get(f"lore{i}", "")),
                        "raw_lore": params.get(f"lore{i}", ""),
                        **cap,
                    }
                )
            if versions:
                out.setdefault(language, []).extend(versions)
    return out


# ---------------------------------------------------------------------------
# set dates

_RAW_DATE_RE = re.compile(r"^1/(\d{4})(?:/(\d{1,2})(?:/(\d{1,2}))?)?$")


def parse_smw_raw(raw: str) -> dict | None:
    m = _RAW_DATE_RE.match(str(raw or ""))
    if not m:
        return None
    year, month, day = m.group(1), m.group(2), m.group(3)
    if day:
        return {"date": f"{year}-{int(month):02d}-{int(day):02d}", "precision": "day"}
    if month:
        return {"date": f"{year}-{int(month):02d}-01", "precision": "month"}
    return {"date": f"{year}-01-01", "precision": "year"}


def normalise_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.casefold())


class SetDates:
    """Release dates per set title: the repository's own release dataset
    first (curated, certified), the fetched SMW cache as fallback."""

    def __init__(self, repo_root: Path, cache: Path):
        self.by_norm: dict[str, dict] = {}
        products_dir = repo_root / "data" / "releases" / "products"
        if products_dir.is_dir():
            for path in sorted(products_dir.glob("*.json")):
                product = json.loads(path.read_text(encoding="utf-8"))
                events = [
                    {
                        "territory": e.get("territory"),
                        "date": e.get("date"),
                        "precision": e.get("precision", "day"),
                        "kind": e.get("kind", "retail"),
                    }
                    for e in product.get("release_events", [])
                ]
                if events:
                    self.by_norm[normalise_name(product.get("name", ""))] = {
                        "source": "data/releases",
                        "product_id": product.get("id"),
                        "events": events,
                    }
        self.fetched: dict[str, dict] = {}
        fetched_path = cache / "errata" / "set-dates.json"
        if fetched_path.exists():
            self.fetched = json.loads(fetched_path.read_text(encoding="utf-8"))

    def lookup(self, set_title: str) -> dict | None:
        hit = self.by_norm.get(normalise_name(set_title))
        if hit:
            return hit
        raw = self.fetched.get(set_title)
        if raw and not raw.get("missing"):
            events = []
            for prop, values in (raw.get("printouts") or {}).items():
                for value in values or []:
                    parsed = parse_smw_raw(value)
                    if parsed:
                        events.append({"territory": prop, "kind": "retail", **parsed})
            if events:
                return {"source": "yugipedia-set-pages", "events": events}
        return None

    @staticmethod
    def earliest(events: list[dict]) -> dict | None:
        """The earliest event by its earliest possible real date."""
        def key(e):
            date, precision = e["date"], e.get("precision", "day")
            return date[:4] if precision == "year" else date[:7] if precision == "month" else date

        dated = [e for e in events if e.get("date")]
        if not dated:
            return None
        return min(dated, key=key)


# ---------------------------------------------------------------------------
# cdb + script evidence


def load_cdb_texts(babel: Path) -> dict[int, dict]:
    rows: dict[int, dict] = {}
    for cdb in ("cards.cdb", "goat-entries.cdb", "cards-unofficial.cdb"):
        path = babel / cdb
        if not path.exists():
            continue
        con = sqlite3.connect(path)
        for pid, ot, alias, name, desc in con.execute(
            "SELECT d.id, d.ot, d.alias, t.name, t.desc FROM datas d JOIN texts t ON d.id=t.id"
        ):
            rows[int(pid)] = {"cdb": cdb, "ot": ot, "alias": int(alias), "name": name, "desc": desc}
        con.close()
    return rows


def normalise_card_text(text: str) -> str:
    text = (text or "").replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("●", " ").replace("•", " ")
    text = re.sub(r"[.,:;–—-]", " ", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def best_match(text: str, versions: list[dict]) -> dict | None:
    if not text or not versions:
        return None
    target = normalise_card_text(text)
    best = None
    for version in versions:
        candidate = normalise_card_text(version["text"])
        if not candidate:
            continue
        if candidate == target:
            return {"index": version["index"], "ratio": 1.0, "exact": True}
        ratio = difflib.SequenceMatcher(a=target, b=candidate, autojunk=False).ratio()
        if best is None or ratio > best["ratio"]:
            best = {"index": version["index"], "ratio": round(ratio, 4), "exact": False}
    return best


def script_path_for(scripts_root: Path, passcode: int) -> tuple[str, Path] | tuple[None, None]:
    for sub in ("goat", "pre-errata", "official", "unofficial"):
        path = scripts_root / sub / f"c{passcode}.lua"
        if path.exists():
            return sub, path
    return None, None


def leading_annotations(path: Path) -> list[str]:
    notes: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            notes.append(stripped.lstrip("-").strip())
        elif stripped:
            break
    return notes[1:]  # the first comment line is the Japanese card name


def normalised_script_lines(path: Path, own_id: int, modern_id: int) -> list[str]:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = re.sub(r"--.*$", "", line).strip()
        if line:
            lines.append(line.replace(str(own_id), "SELFID").replace(str(modern_id), "MODID"))
    return lines


# ---------------------------------------------------------------------------
# packet assembly


def build_packets(
    repo_root: Path,
    cache: Path,
    repos: Path,
    names: list[str] | None,
    out_dir: Path,
) -> dict:
    babel = repos / "babelcdb"
    scripts_root = repos / "cardscripts"
    cdb = load_cdb_texts(babel)
    by_name = {}
    for pid, row in cdb.items():
        if row["cdb"] == "cards.cdb":
            by_name.setdefault(row["name"], pid)
    set_dates = SetDates(repo_root, cache)
    pages_dir = cache / "errata" / "pages"

    # corpus records + upstream implementations per modern passcode
    corpus: dict[int, dict] = {}
    for path in sorted((repo_root / "data" / "errata").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        corpus[record["modern_card"]["passcode"]] = {
            "slug": path.stem,
            "record": record,
        }
    upstream_by_modern: dict[int, list[int]] = {}
    for pid, row in cdb.items():
        if row["cdb"] in ("goat-entries.cdb", "cards-unofficial.cdb") and row["alias"]:
            upstream_by_modern.setdefault(row["alias"], []).append(pid)

    wanted_names = names or sorted(
        {info["record"]["modern_card"]["name"] for info in corpus.values()}
    )

    missing_sets: set[str] = set()
    summary = {
        "packets": 0,
        "with_errata_page": 0,
        "english_lineages": 0,
        "unmatched_historical_text": [],
        "unmatched_modern_text": [],
        "missing_set_dates": [],
    }
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in sorted(wanted_names):
        modern_code = by_name.get(name)
        if modern_code is None:
            print(f"SKIP {name}: not in cards.cdb", file=sys.stderr)
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
        packet: dict = {
            "card": {"passcode": modern_code, "name": name},
            "corpus_record": corpus.get(modern_code, {}).get("slug"),
            "modern_text": cdb[modern_code]["desc"],
        }

        # upstream historical implementations
        impls = []
        for code in sorted(upstream_by_modern.get(modern_code, [])):
            row = cdb[code]
            sub, spath = script_path_for(scripts_root, code)
            impl = {
                "passcode": code,
                "cdb": row["cdb"],
                "name": row["name"],
                "text": row["desc"],
                "script": f"{sub}/c{code}.lua" if spath else None,
                "annotations": leading_annotations(spath) if spath else [],
            }
            msub, mpath = script_path_for(scripts_root, modern_code)
            if spath and mpath:
                a = normalised_script_lines(spath, code, modern_code)
                b = normalised_script_lines(mpath, modern_code, modern_code)
                impl["script_diff"] = list(
                    difflib.unified_diff(b, a, "modern", row["name"], lineterm="", n=1)
                )
                impl["uses_goatconfirm"] = any("GoatConfirm" in ln for ln in a)
            impls.append(impl)
        packet["upstream_implementations"] = impls

        # Yugipedia errata lineage
        page_path = pages_dir / f"{slug}.json"
        if page_path.exists():
            page = json.loads(page_path.read_text(encoding="utf-8"))
            if page.get("missing"):
                packet["errata_page"] = {"missing": True}
            else:
                summary["with_errata_page"] += 1
                lineages = parse_errata_tables(page.get("wikitext", ""))
                english = lineages.get("English", [])
                if english:
                    summary["english_lineages"] += 1
                for version in english:
                    dating_set = version.get("dating_set")
                    if dating_set:
                        dates = set_dates.lookup(dating_set)
                        if dates:
                            version["set_dates"] = dates
                            earliest = SetDates.earliest(dates["events"])
                            if earliest:
                                version["earliest_tcg_date"] = earliest
                        else:
                            missing_sets.add(dating_set)
                packet["errata_page"] = {
                    "title": page.get("title"),
                    "revid": page.get("revid"),
                    "english_versions": english,
                    "other_languages": sorted(k for k in lineages if k != "English"),
                }
                for impl in impls:
                    impl["text_matches_version"] = best_match(impl["text"], english)
                packet["modern_text_matches_version"] = best_match(
                    packet["modern_text"], english
                )
                if english:
                    if any(
                        (impl.get("text_matches_version") or {}).get("ratio", 0) < 0.9
                        for impl in impls
                    ):
                        summary["unmatched_historical_text"].append(name)
                    if (packet["modern_text_matches_version"] or {}).get("ratio", 0) < 0.9:
                        summary["unmatched_modern_text"].append(name)
        else:
            packet["errata_page"] = {"not_fetched": True}

        out = out_dir / f"{slug}.json"
        out.write_text(
            json.dumps(packet, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        summary["packets"] += 1

    summary["missing_set_dates"] = sorted(missing_sets)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "retroformats")
    parser.add_argument("--repos", type=Path, default=None, help="pinned upstream checkouts (default: <cache>/repos)")
    parser.add_argument("--names", type=Path, help="JSON list of card names (default: every corpus record)")
    parser.add_argument("--out", type=Path, help="packet output dir (default: <cache>/errata/research)")
    parser.add_argument("--root", type=Path, default=None, help="repository root")
    args = parser.parse_args(argv)

    root = args.root
    if root is None:
        current = Path.cwd()
        for candidate in [current, *current.parents]:
            if all((candidate / m).is_dir() for m in REPO_ROOT_MARKER):
                root = candidate
                break
        else:
            parser.error("could not locate the repository root; pass --root")
    repos = args.repos or (args.cache / "repos")
    names = json.loads(args.names.read_text(encoding="utf-8")) if args.names else None
    out_dir = args.out or (args.cache / "errata" / "research")

    summary = build_packets(root, args.cache, repos, names, out_dir)
    print(json.dumps(summary, indent=1))
    (args.cache / "errata" / "research-summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
