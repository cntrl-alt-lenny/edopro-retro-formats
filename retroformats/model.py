"""Typed views over the canonical JSON records.

These are deliberately thin: every object keeps the raw dict it was loaded
from (`.raw`), and only the fields the toolchain actually computes with are
lifted into attributes. Semantic correctness is the validator's job, so the
constructors here fail only on structurally unusable input.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STATUS_TO_COUNT = {"forbidden": 0, "limited": 1, "semilimited": 2}
UNLIMITED_COUNT = 3

IMPLEMENTATION_STATUSES = ("missing", "stub", "partial", "complete", "verified")


class DataError(Exception):
    """A record is too malformed to load at all."""

    def __init__(self, path: Path, message: str):
        super().__init__(f"{path}: {message}")
        self.path = path
        self.message = message


def parse_date(value: str) -> _dt.date:
    return _dt.date.fromisoformat(value)


@dataclass(frozen=True)
class CardRef:
    passcode: int
    name: str

    @classmethod
    def from_raw(cls, raw: dict[str, Any], path: Path) -> "CardRef":
        try:
            return cls(passcode=int(raw["passcode"]), name=str(raw["name"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise DataError(path, f"bad card reference {raw!r}: {exc}") from exc


@dataclass
class BanlistEntry:
    card: CardRef
    status: str
    raw: dict[str, Any]

    @property
    def count(self) -> int:
        return STATUS_TO_COUNT[self.status]


@dataclass
class Banlist:
    id: str
    region: str
    effective_date: str
    entries: list[BanlistEntry]
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "Banlist":
        entries = []
        for e in raw.get("entries", []):
            entries.append(
                BanlistEntry(
                    card=CardRef.from_raw(e.get("card", {}), path),
                    status=str(e.get("status", "")),
                    raw=e,
                )
            )
        return cls(
            id=str(raw.get("id", "")),
            region=str(raw.get("region", "")),
            effective_date=str(raw.get("effective_date", "")),
            entries=entries,
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )


@dataclass(frozen=True)
class PoolCard:
    passcode: int
    name: str
    variants: tuple[int, ...] = ()

    @classmethod
    def from_raw(cls, raw: dict[str, Any], path: Path) -> "PoolCard":
        try:
            return cls(
                passcode=int(raw["passcode"]),
                name=str(raw["name"]),
                variants=tuple(int(v) for v in raw.get("variant_passcodes", [])),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DataError(path, f"bad pool card {raw!r}: {exc}") from exc


@dataclass
class Pool:
    id: str
    region: str
    kind: str  # "extensional" | "release-cutoff"
    cards: list[PoolCard]
    cutoff: dict[str, Any] | None
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "Pool":
        cards = [PoolCard.from_raw(c, path) for c in raw.get("cards", [])]
        return cls(
            id=str(raw.get("id", "")),
            region=str(raw.get("region", "")),
            kind=str(raw.get("kind", "")),
            cards=cards,
            cutoff=raw.get("cutoff"),
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )

    def passcodes(self) -> set[int]:
        return {c.passcode for c in self.cards}


@dataclass
class RuleProfile:
    id: str
    name: str
    preset: str | None
    flags: list[str]
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "RuleProfile":
        engine = raw.get("engine", {}) or {}
        return cls(
            id=str(raw.get("id", "")),
            name=str(raw.get("name", "")),
            preset=engine.get("preset"),
            flags=list(engine.get("flags", [])),
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )


@dataclass
class Erratum:
    id: str
    modern_card: CardRef
    classification: str
    changes: list[dict[str, Any]]
    implementation: dict[str, Any]
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "Erratum":
        return cls(
            id=str(raw.get("id", "")),
            modern_card=CardRef.from_raw(raw.get("modern_card", {}), path),
            classification=str(raw.get("classification", "")),
            changes=list(raw.get("changes", [])),
            implementation=dict(raw.get("implementation", {})),
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )

    def historical_behaviour_applies_on(self, snapshot: _dt.date) -> bool | None:
        """True if, at `snapshot`, the card behaved per its oldest recorded text.

        Returns None when no change carries a usable date (undecidable yet).
        Only meaningful for classifications that alter behaviour.
        """
        dates = []
        for change in self.changes:
            eff = change.get("date_effective")
            if eff:
                dates.append(parse_date(eff))
        if not dates:
            return None
        return snapshot < min(dates)


@dataclass
class Format:
    id: str
    name: str
    region: str
    start: str
    end: str | None
    snapshot: str
    previous: str | None
    next: str | None
    banlist_id: str
    pool_id: str
    rule_profile_id: str
    errata_include: list[str]
    errata_exclude: list[str]
    implementation_status: dict[str, str]
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "Format":
        period = raw.get("period", {}) or {}
        chrono = raw.get("chronology", {}) or {}
        overrides = raw.get("errata_overrides", {}) or {}
        return cls(
            id=str(raw.get("id", "")),
            name=str(raw.get("name", "")),
            region=str(raw.get("region", "")),
            start=str(period.get("start", "")),
            end=period.get("end"),
            snapshot=str(period.get("snapshot", "")),
            previous=chrono.get("previous"),
            next=chrono.get("next"),
            banlist_id=str(raw.get("banlist", "")),
            pool_id=str(raw.get("card_pool", "")),
            rule_profile_id=str(raw.get("rule_profile", "")),
            errata_include=list(overrides.get("include", [])),
            errata_exclude=list(overrides.get("exclude", [])),
            implementation_status=dict(raw.get("implementation_status", {})),
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )

    @property
    def snapshot_date(self) -> _dt.date:
        return parse_date(self.snapshot)


@dataclass
class Source:
    id: str
    kind: str
    title: str
    url: str | None
    raw: dict[str, Any]


@dataclass
class CardIndex:
    by_passcode: dict[int, dict[str, Any]] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)

    def name_of(self, passcode: int) -> str | None:
        card = self.by_passcode.get(passcode)
        return card["name"] if card else None

    def alias_of(self, passcode: int) -> int | None:
        card = self.by_passcode.get(passcode)
        if card is None:
            return None
        alias = card.get("alias_of")
        return int(alias) if alias else None
