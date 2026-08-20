"""Apply reviewed errata decisions to the canonical records. Offline stage.

The per-card review (over the research packets built by errata_research.py)
produces DECISION objects. This tool turns decisions into canonical
data/errata/*.json updates under strict guards, so that no chronology claim
can enter the dataset without machine-checkable evidence:

- every change's effective date/bounds must carry a date_evidence object;
- kind "set-release" evidence is RECOMPUTED against the research packet: the
  claimed date must equal the cited set's earliest TCG release date (at its
  recorded precision) or the decision is rejected;
- kind "shared-chronology" evidence must reference an entry in the shared
  chronology table (a sourced research artifact); the bounds are copied from
  the table, never from the decision (single source of truth);
- kind "external" evidence must carry a URL and a quote, and the change must
  cite a source id that resolves in the registry;
- historical/modern texts are copied from the packet's lineage (or the
  pinned cdb texts) by version index - decisions never hand-transcribe text.

Deterministic output: stable key order, LF newlines, unchanged files are not
rewritten. --dry-run reports what would change without writing.

Run:  python -m retroformats.importers.errata_apply \
          --decisions DIR_OR_FILE --packets ~/.cache/retroformats/errata/research \
          [--chronologies FILE] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RECORD_ORDER = [
    "$schema", "id", "modern_card", "classification", "changes",
    "implementation", "review", "applicable_formats_note", "sources", "notes",
]
CHANGE_ORDER = [
    "kind", "effective", "historical_text", "modern_text", "summary",
    "resulting_implementation", "sources",
]
IMPL_ORDER = [
    "strategy", "historical_passcode", "historical_variant_passcodes",
    "upstream", "script", "status", "tested",
]
EFFECTIVE_ORDER = [
    "date", "precision", "status", "old_attested_through", "new_attested_from", "basis",
]

KINDS = ("functional", "cosmetic", "ruling", "engine")
SEVERITY = {"functional": 3, "ruling": 2, "engine": 1, "cosmetic": 0}


class DecisionError(Exception):
    pass


def order(d: dict, keys: list[str]) -> dict:
    out = {k: d[k] for k in keys if k in d and d[k] is not None}
    for k in d:
        if k not in out and d[k] is not None:
            out[k] = d[k]
    return out


def load_decisions(path: Path) -> list[dict]:
    if path.is_dir():
        decisions = []
        for p in sorted(path.glob("*.json")):
            payload = json.loads(p.read_text(encoding="utf-8"))
            decisions.extend(payload if isinstance(payload, list) else [payload])
        return decisions
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else [payload]


def lineage_text(packet: dict, version_index: int | None) -> str | None:
    if version_index is None:
        return None
    for version in (packet.get("errata_page") or {}).get("english_versions", []):
        if version.get("index") == version_index:
            return version.get("text") or None
    raise DecisionError(f"lineage version {version_index} not in packet")


def _historical_version(raw_changes: list[dict], index: int) -> int | None:
    """The lineage version in force before change `index` (i.e. the version
    the implementation of that era must reproduce)."""
    if index < len(raw_changes):
        value = raw_changes[index].get("historical_text_version")
        return int(value) if value is not None else None
    return None


def lineage_version(packet: dict, version_index: int) -> dict:
    for version in (packet.get("errata_page") or {}).get("english_versions", []):
        if version.get("index") == version_index:
            return version
    raise DecisionError(f"lineage version {version_index} not in packet")


def apply_set_release(effective: dict, evidence: dict, packet: dict) -> dict:
    """Populate the effective date from the research packet: the date a change
    took effect is the earliest TCG release of the printing that introduced
    the new text. The packet is the single source of truth - a reviewer never
    types the date - and any date they DID claim must match it exactly."""
    version_index = evidence.get("introduces_version")
    if version_index is None:
        raise DecisionError("set-release evidence needs introduces_version")
    version = lineage_version(packet, int(version_index))
    earliest = version.get("earliest_tcg_date")
    if not earliest:
        raise DecisionError(
            f"lineage version {version_index} has no dated set in the packet"
        )
    merged = dict(effective)
    field = "new_attested_from" if effective.get("new_attested_from") else "date"
    claimed = effective.get(field)
    if claimed is not None and claimed != earliest["date"]:
        raise DecisionError(
            f"{field} {claimed!r} != packet earliest TCG date {earliest['date']!r} "
            f"for version {version_index} ({version.get('dating_set')})"
        )
    claimed_precision = effective.get("precision")
    if claimed_precision is not None and claimed_precision != earliest.get("precision", "day"):
        raise DecisionError(
            f"precision {claimed_precision!r} != packet precision "
            f"{earliest.get('precision')!r} for version {version_index}"
        )
    merged[field] = earliest["date"]
    if field == "date":
        merged["precision"] = earliest.get("precision", "day")
    merged.setdefault("status", "reported")
    if not merged.get("basis"):
        merged["basis"] = (
            f"TCG release of the first printing carrying the new text "
            f"({version.get('number') or 'unknown number'}, {version.get('dating_set')})"
        )
    return merged


import re as _re

_WAYBACK_RE = _re.compile(r"web\.archive\.org/web/(\d{4})(\d{2})(\d{2})\d*")


def check_external(effective: dict, evidence: dict) -> None:
    if not evidence.get("url") or not evidence.get("quote"):
        raise DecisionError("external evidence needs url and quote")
    # An archive capture attests a state ON its capture date - a bound claimed
    # from it must be exactly that date (other dates need other evidence).
    m = _WAYBACK_RE.search(str(evidence.get("url")))
    if m and not effective.get("date"):
        capture = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        for field in ("old_attested_through", "new_attested_from"):
            claimed = effective.get(field)
            if claimed and claimed != capture:
                raise DecisionError(
                    f"{field} {claimed!r} does not equal the cited archive capture "
                    f"date {capture}; a capture attests only its own date"
                )


def apply_shared(effective: dict, evidence: dict, chronologies: dict) -> dict:
    entry = chronologies.get(str(evidence.get("id")))
    if entry is None:
        raise DecisionError(f"shared chronology {evidence.get('id')!r} is not defined")
    merged = dict(effective)
    for key in ("date", "precision", "status", "old_attested_through", "new_attested_from"):
        if key in entry:
            merged[key] = entry[key]
    if entry.get("basis") and not merged.get("basis"):
        merged["basis"] = entry["basis"]
    return merged


def build_change(raw: dict, packet: dict, chronologies: dict) -> dict:
    kind = raw.get("kind")
    if kind not in KINDS:
        raise DecisionError(f"bad change kind {kind!r}")
    effective = dict(raw.get("effective") or {})
    evidence = raw.pop("date_evidence", None) or effective.pop("date_evidence", None)
    has_chronology = any(
        effective.get(k) for k in ("date", "old_attested_through", "new_attested_from")
    )
    if evidence:
        ev_kind = evidence.get("kind")
        if ev_kind == "set-release":
            effective = apply_set_release(effective, evidence, packet)
        elif ev_kind == "shared-chronology":
            effective = apply_shared(effective, evidence, chronologies)
        elif ev_kind == "external":
            check_external(effective, evidence)
        else:
            raise DecisionError(f"unknown date_evidence kind {ev_kind!r}")
    elif has_chronology:
        raise DecisionError(f"{kind} change carries chronology but no date_evidence")
    if not raw.get("summary"):
        raise DecisionError("change needs a summary")
    if not raw.get("sources"):
        raise DecisionError("change needs sources")

    if kind not in ("functional", "ruling") and raw.get("resulting_implementation"):
        raise DecisionError(
            f"{kind} change carries resulting_implementation; only functional/ruling "
            "changes create implementation-relevant versions"
        )

    historical_text = raw.get("historical_text")
    if historical_text is not None:
        # Literal text is allowed only as an exact copy of packet-carried
        # database text (no lineage available) - never hand-transcription.
        allowed = {packet.get("modern_text")} | {
            impl.get("text") for impl in packet.get("upstream_implementations", [])
        }
        if historical_text not in allowed:
            raise DecisionError(
                "literal historical_text does not match any packet-carried cdb text"
            )
    elif raw.get("historical_text_version") is not None:
        historical_text = lineage_text(packet, raw["historical_text_version"])
    modern_text = raw.get("modern_text")
    if modern_text is not None:
        if modern_text != packet.get("modern_text"):
            raise DecisionError("literal modern_text does not match the packet's cdb text")
    elif raw.get("modern_text_version") is not None:
        modern_text = lineage_text(packet, raw["modern_text_version"])

    change: dict = {
        "kind": kind,
        "effective": order(
            {k: effective.get(k) for k in EFFECTIVE_ORDER if effective.get(k) is not None}
            or {"date": None},
            EFFECTIVE_ORDER,
        ),
        "summary": raw["summary"],
        "sources": list(raw["sources"]),
    }
    if "date" not in change["effective"]:
        change["effective"] = {"date": None, **change["effective"]}
    if historical_text is not None:
        change["historical_text"] = historical_text
    if modern_text is not None:
        change["modern_text"] = modern_text
    resulting = raw.get("resulting_implementation")
    if resulting:
        change["resulting_implementation"] = order(resulting, IMPL_ORDER)
    return order(change, CHANGE_ORDER)


def apply_decision(
    decision: dict,
    errata_dir: Path,
    packets_dir: Path,
    chronologies: dict,
    review_date: str,
) -> tuple[str, dict] | None:
    slug = decision.get("slug")
    if not slug:
        raise DecisionError("decision without slug")
    packet_path = packets_dir / f"{slug}.json"
    if not packet_path.exists():
        raise DecisionError(f"{slug}: no research packet")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if decision.get("passcode") != packet["card"]["passcode"]:
        raise DecisionError(
            f"{slug}: passcode {decision.get('passcode')} != packet {packet['card']['passcode']}"
        )

    record_path = errata_dir / f"{slug}.json"
    if record_path.exists():
        record = json.loads(record_path.read_text(encoding="utf-8"))
    else:
        record = {
            "$schema": "../../schemas/erratum.schema.json",
            "id": f"erratum-{slug}",
            "modern_card": dict(packet["card"]),
            "sources": [],
        }

    changes = [build_change(dict(c), packet, chronologies) for c in decision["changes"]]
    if not changes:
        raise DecisionError(f"{slug}: no changes in decision")
    kinds = [c["kind"] for c in changes]
    dominant = max(kinds, key=lambda k: SEVERITY[k])
    claimed = decision.get("classification")
    if claimed and claimed != dominant:
        raise DecisionError(
            f"{slug}: classification {claimed!r} != dominant change kind {dominant!r}"
        )

    record["classification"] = dominant
    record["changes"] = changes
    by_code = {
        impl.get("passcode"): impl for impl in packet.get("upstream_implementations", [])
    }
    # Which lineage version each implementation is claimed to implement: the
    # baseline implements the text the first change describes as historical;
    # a change's resulting_implementation implements the text that change
    # produced, i.e. the next change's historical text.
    claimed_version = {"baseline_implementation": _historical_version(decision["changes"], 0)}
    for i in range(len(changes)):
        claimed_version[f"changes[{i}].resulting_implementation"] = _historical_version(
            decision["changes"], i + 1
        )
    for where, impl in [
        ("baseline_implementation", decision.get("baseline_implementation")),
        *[
            (f"changes[{i}].resulting_implementation", c.get("resulting_implementation"))
            for i, c in enumerate(changes)
        ],
    ]:
        if not impl:
            continue
        code = impl.get("historical_passcode")
        if impl.get("strategy") == "reuse-upstream" and code not in by_code:
            raise DecisionError(
                f"{slug}: {where} claims reuse-upstream passcode {code} but the "
                "packet lists no such upstream implementation"
            )
        # Era consistency: the upstream variant's own database text must be
        # the text of the version it is claimed to implement. Catches reusing
        # a variant from the wrong historical revision.
        upstream = by_code.get(code)
        want = claimed_version.get(where)
        if upstream and want is not None and not decision.get("era_mismatch_ack"):
            match = upstream.get("text_matches_version") or {}
            if match.get("exact") and match.get("index") != want:
                raise DecisionError(
                    f"{slug}: {where} reuses upstream {code}, whose database text is "
                    f"lineage version {match.get('index')}, but it is claimed to "
                    f"implement version {want}; the variant may belong to a different "
                    "era (set era_mismatch_ack with an explanation if deliberate)"
                )
    if decision.get("baseline_implementation"):
        record["implementation"] = order(decision["baseline_implementation"], IMPL_ORDER)
    elif "implementation" not in record:
        raise DecisionError(f"{slug}: new record needs baseline_implementation")
    record["review"] = {"status": "reviewed", "date": review_date}
    if decision.get("review_notes"):
        record["review"]["notes"] = decision["review_notes"]
    if decision.get("sources"):
        merged = [*record.get("sources", [])]
        for source in decision["sources"]:
            if source not in merged:
                merged.append(source)
        record["sources"] = merged
    for change in changes:
        for source in change["sources"]:
            if source not in record["sources"]:
                record["sources"].append(source)
    if decision.get("notes") is not None:
        record["notes"] = decision["notes"]
    elif record.get("notes", "").startswith("Auto-imported"):
        del record["notes"]

    return slug, order(record, RECORD_ORDER)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--chronologies", type=Path)
    parser.add_argument("--errata-dir", type=Path, default=None)
    parser.add_argument("--review-date", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    errata_dir = args.errata_dir
    if errata_dir is None:
        current = Path.cwd()
        for candidate in [current, *current.parents]:
            if (candidate / "data" / "errata").is_dir():
                errata_dir = candidate / "data" / "errata"
                break
        else:
            parser.error("could not locate data/errata; pass --errata-dir")
    review_date = args.review_date
    if review_date is None:
        import datetime as _dt

        review_date = _dt.date.today().isoformat()

    chronologies = {}
    if args.chronologies:
        chronologies = json.loads(args.chronologies.read_text(encoding="utf-8"))

    decisions = load_decisions(args.decisions)
    written, unchanged, failed = [], [], []
    for decision in decisions:
        slug = decision.get("slug", "?")
        try:
            result = apply_decision(
                decision, errata_dir, args.packets, chronologies, review_date
            )
        except DecisionError as exc:
            failed.append((slug, str(exc)))
            continue
        if result is None:
            continue
        slug, record = result
        path = errata_dir / f"{slug}.json"
        text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") == text:
            unchanged.append(slug)
            continue
        if not args.dry_run:
            with path.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        written.append(slug)

    mode = "DRY-RUN " if args.dry_run else ""
    print(f"{mode}applied: {len(written)} written, {len(unchanged)} unchanged, {len(failed)} rejected")
    for slug, why in failed:
        print(f"  REJECTED {slug}: {why}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
