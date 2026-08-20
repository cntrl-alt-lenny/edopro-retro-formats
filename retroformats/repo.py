"""Loading the whole repository's canonical data into one object."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .model import (
    Banlist,
    CardIndex,
    DataError,
    Erratum,
    Format,
    Pool,
    Product,
    ReleaseCoverage,
    ReleaseGap,
    RuleProfile,
    Source,
)


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise DataError(path, f"invalid JSON: {exc}") from exc


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upwards until a directory containing formats/ and data/ is found."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "formats").is_dir() and (candidate / "data").is_dir():
            return candidate
    raise SystemExit(
        "Could not locate the repository root (a directory containing formats/ and data/)."
    )


@dataclass
class Repository:
    root: Path
    banlists: dict[str, Banlist] = field(default_factory=dict)
    pools: dict[str, Pool] = field(default_factory=dict)
    rule_profiles: dict[str, RuleProfile] = field(default_factory=dict)
    errata: dict[str, Erratum] = field(default_factory=dict)
    formats: dict[str, Format] = field(default_factory=dict)
    global_sources: dict[str, Source] = field(default_factory=dict)
    format_sources: dict[str, dict[str, Source]] = field(default_factory=dict)
    card_index: CardIndex = field(default_factory=CardIndex)
    products: dict[str, Product] = field(default_factory=dict)
    release_coverage: ReleaseCoverage | None = None
    release_gaps: list[ReleaseGap] = field(default_factory=list)
    import_report: dict[str, Any] = field(default_factory=dict)
    load_errors: list[DataError] = field(default_factory=list)

    @classmethod
    def load(cls, root: Path) -> "Repository":
        repo = cls(root=root)

        def try_load(path: Path, loader) -> None:
            try:
                loader(_read_json(path), path)
            except DataError as exc:
                repo.load_errors.append(exc)

        for path in sorted((root / "data" / "banlists").rglob("*.json")):
            try_load(path, lambda raw, p: repo._add(repo.banlists, Banlist.load(raw, p)))
        for path in sorted((root / "data" / "pools").glob("*.json")):
            try_load(path, lambda raw, p: repo._add(repo.pools, Pool.load(raw, p)))
        for path in sorted((root / "data" / "rule-profiles").glob("*.json")):
            try_load(path, lambda raw, p: repo._add(repo.rule_profiles, RuleProfile.load(raw, p)))
        for path in sorted((root / "data" / "errata").glob("*.json")):
            try_load(path, lambda raw, p: repo._add(repo.errata, Erratum.load(raw, p)))

        sources_path = root / "data" / "sources.json"
        if sources_path.exists():
            try_load(sources_path, lambda raw, p: repo._load_sources(raw, p, None))

        for format_dir in sorted((root / "formats").iterdir()):
            if not format_dir.is_dir():
                continue
            fmt_path = format_dir / "format.json"
            if fmt_path.exists():
                try_load(fmt_path, lambda raw, p: repo._add(repo.formats, Format.load(raw, p)))
            fmt_sources = format_dir / "sources.json"
            if fmt_sources.exists():
                try_load(
                    fmt_sources,
                    lambda raw, p, name=format_dir.name: repo._load_sources(raw, p, name),
                )

        index_path = root / "data" / "cards" / "index.json"
        if index_path.exists():
            try_load(index_path, repo._load_card_index)

        for path in sorted((root / "data" / "releases" / "products").glob("*.json")):
            try_load(path, lambda raw, p: repo._add(repo.products, Product.load(raw, p)))

        coverage_path = root / "data" / "releases" / "coverage.json"
        if coverage_path.exists():
            try_load(
                coverage_path,
                lambda raw, p: setattr(repo, "release_coverage", ReleaseCoverage.load(raw, p)),
            )

        gaps_path = root / "data" / "releases" / "gaps.json"
        if gaps_path.exists():
            try_load(
                gaps_path,
                lambda raw, p: repo.release_gaps.extend(
                    ReleaseGap.load(g, p) for g in raw.get("gaps", [])
                ),
            )

        # The import report is a generated artifact, but the validator uses it
        # to prove that every anomaly the importer detected is accounted for
        # in the gap ledger.
        report_path = root / "data" / "imported" / "releases-report.json"
        if report_path.exists():
            try_load(report_path, lambda raw, p: repo.import_report.update(raw))

        return repo

    def _add(self, table: dict[str, Any], record: Any) -> None:
        if record.id in table:
            self.load_errors.append(
                DataError(record.path, f"duplicate id {record.id!r} (also in {table[record.id].path})")
            )
            return
        table[record.id] = record

    def _load_sources(self, raw: dict[str, Any], path: Path, format_id: str | None) -> None:
        target = self.global_sources if format_id is None else self.format_sources.setdefault(format_id, {})
        for entry in raw.get("sources", []):
            source = Source(
                id=str(entry.get("id", "")),
                kind=str(entry.get("kind", "")),
                title=str(entry.get("title", "")),
                url=entry.get("url"),
                raw=entry,
            )
            if source.id in target:
                self.load_errors.append(DataError(path, f"duplicate source id {source.id!r}"))
                continue
            target[source.id] = source

    def _load_card_index(self, raw: dict[str, Any], path: Path) -> None:
        self.card_index.source = raw.get("source", {})
        for card in raw.get("cards", []):
            try:
                self.card_index.by_passcode[int(card["passcode"])] = card
            except (KeyError, TypeError, ValueError) as exc:
                self.load_errors.append(DataError(path, f"bad card index row {card!r}: {exc}"))

    def resolve_source(self, source_id: str, format_id: str | None = None) -> Source | None:
        if format_id is not None:
            local = self.format_sources.get(format_id, {})
            if source_id in local:
                return local[source_id]
        return self.global_sources.get(source_id)
