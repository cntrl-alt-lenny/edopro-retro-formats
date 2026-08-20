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

# CARD_ARTWORK_VERSIONS_OFFSET in EDOPro's gframe/data_manager.h: a cdb alias
# within this window marks an artwork variant of the same functional card.
ARTWORK_OFFSET = 10

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


# Change kinds that require a different card implementation for the era before
# them. Cosmetic (wording-only) and engine (rule-profile) transitions never do.
IMPLEMENTATION_RELEVANT_KINDS = ("functional", "ruling")
CHANGE_KINDS = ("functional", "cosmetic", "ruling", "engine")
# Dominance order for deriving a record's summary classification.
KIND_SEVERITY = {"functional": 3, "ruling": 2, "engine": 1, "cosmetic": 0}
EFFECTIVE_STATUSES = ("verified", "reported")

OLD, NEW, AMBIGUOUS = "old", "new", "ambiguous"


def _precision_bounds(date_str: str, precision: str) -> tuple[_dt.date, _dt.date]:
    d = parse_date(date_str)
    if precision == "month":
        return _dt.date(d.year, d.month, 1), _last_day_of_month(d.year, d.month)
    if precision == "year":
        return _dt.date(d.year, 1, 1), _dt.date(d.year, 12, 31)
    return d, d


def change_state_at(change: dict[str, Any], snapshot: _dt.date) -> str:
    """Whether `snapshot` falls before (OLD), on/after (NEW), or inside the
    uncertainty interval (AMBIGUOUS) of one change's effective chronology.

    On the effective date itself the NEW behaviour applies. A month/year-
    precise date widens into an interval; bounded chronology uses the latest
    attestation of the old behaviour and the earliest of the new. Unknown
    chronology is AMBIGUOUS — never silently old or new.
    """
    effective = change.get("effective") or {}
    date = effective.get("date")
    if date:
        lo, hi = _precision_bounds(str(date), str(effective.get("precision") or "day"))
        if snapshot < lo:
            return OLD
        if snapshot >= hi:
            return NEW
        return AMBIGUOUS
    old_through = effective.get("old_attested_through")
    new_from = effective.get("new_attested_from")
    if old_through and snapshot <= parse_date(str(old_through)):
        return OLD
    if new_from and snapshot >= parse_date(str(new_from)):
        return NEW
    return AMBIGUOUS


@dataclass(frozen=True)
class ErratumSelection:
    """The implementation decision for one erratum at one snapshot date.

    state:
      "modern"     — the modern implementation is correct (or accepted:
                     the selected version's strategy is none-needed);
      "historical" — `implementation` (a dict) must substitute the modern card;
      "ambiguous"  — the snapshot falls inside an unresolved transition
                     interval; selection must not proceed without explicit,
                     documented adjudication;
      "gap"        — the chronology is determinate but the selected version
                     has no usable implementation (strategy unresolved or no
                     historical passcode).
    version_index counts implementation-relevant transitions that have
    occurred by the snapshot (0 = baseline version).
    """

    state: str
    implementation: dict[str, Any] | None = None
    version_index: int | None = None
    ambiguous_changes: tuple[int, ...] = ()
    candidates: tuple[int, ...] = ()
    modern_version: int | None = None

    @property
    def modern_is_possible(self) -> bool:
        """Whether the MODERN implementation is among the versions the
        evidence still allows. False means the chronology cannot say which
        historical version applies, but it CAN say the modern card is wrong —
        so falling back to modern is a known error, not a neutral default."""
        if self.state != "ambiguous":
            return True
        return self.modern_version in self.candidates

    @property
    def acknowledged_gap(self) -> dict[str, Any] | None:
        """For state 'gap': the record's documented acknowledgement of the
        divergence, when it carries one. None means the gap is unexamined."""
        if self.state != "gap" or not self.implementation:
            return None
        gap = self.implementation.get("gap")
        return dict(gap) if gap else None


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

    @property
    def review_status(self) -> str:
        review = self.raw.get("review") or {}
        return str(review.get("status", "imported"))

    def relevant_changes(self) -> list[dict[str, Any]]:
        """The changes that require a different card implementation for the
        era before them (functional and ruling transitions)."""
        return [c for c in self.changes if c.get("kind") in IMPLEMENTATION_RELEVANT_KINDS]

    def implementation_for_version(self, version_index: int) -> dict[str, Any] | None:
        """The implementation of version `version_index` (0 = baseline, k>0 =
        the version created by the k-th implementation-relevant change).
        Returns None for the modern version or when nothing is recorded."""
        relevant = self.relevant_changes()
        if version_index >= len(relevant):
            return None  # the modern card — implemented by cards.cdb
        if version_index == 0:
            return self.implementation
        recorded = relevant[version_index - 1].get("resulting_implementation")
        return dict(recorded) if recorded else None

    def selection_at(self, snapshot: _dt.date) -> ErratumSelection:
        """Which implementation this card needs at `snapshot`, fail-safe.

        Walks the implementation-relevant changes: the version in force is
        determined by how many transitions had taken effect by the snapshot.
        Any transition whose state at the snapshot is ambiguous makes the
        whole selection ambiguous unless the determinate transitions already
        pin the version (they cannot: states are monotone when chronology is
        consistent, so one ambiguous straddling change is always decisive).
        """
        relevant = self.relevant_changes()
        if not relevant:
            return ErratumSelection(state="modern")
        states = [change_state_at(c, snapshot) for c in relevant]
        definite_new = sum(1 for s in states if s == NEW)
        definite_old = sum(1 for s in states if s == OLD)
        k_min = definite_new
        k_max = len(relevant) - definite_old
        if k_min != k_max:
            ambiguous = tuple(i for i, s in enumerate(states) if s == AMBIGUOUS)
            return ErratumSelection(
                state="ambiguous",
                ambiguous_changes=ambiguous,
                candidates=tuple(range(k_min, k_max + 1)),
                modern_version=len(relevant),
            )
        version = k_min
        if version >= len(relevant):
            return ErratumSelection(state="modern", version_index=version)
        impl = self.implementation_for_version(version)
        if impl is None or impl.get("strategy") == "unresolved":
            return ErratumSelection(state="gap", implementation=impl, version_index=version)
        if impl.get("strategy") == "none-needed":
            # A documented decision that the modern implementation stands in
            # for this version (e.g. a ruling difference not reproduced).
            return ErratumSelection(state="modern", implementation=impl, version_index=version)
        if not impl.get("historical_passcode"):
            return ErratumSelection(state="gap", implementation=impl, version_index=version)
        return ErratumSelection(state="historical", implementation=impl, version_index=version)


TERRITORIES = ("tcg", "tcg-na", "tcg-eu", "tcg-oce", "ocg", "ocg-jp", "ocg-kr", "ocg-asia")
PRECISIONS = ("day", "month", "year")
EVENT_STATUSES = ("verified", "reported", "disputed")
EVENT_KINDS = ("retail", "event", "prerelease", "distribution-start")
# Event kinds that made a card legally obtainable (sneak-peek/prerelease
# availability is recorded but does not count toward tournament pools).
AVAILABILITY_KINDS = ("retail", "event", "distribution-start")
PRODUCT_KINDS = (
    "booster", "structure", "starter", "tin", "special", "reprint-set",
    "promo-magazine", "promo-videogame", "promo-tournament",
    "promo-subscription", "promo-other", "other",
)


def normalise_name(name: str) -> str:
    """Loose identity for product/set names across sources (case- and
    punctuation-insensitive)."""
    import re as _re

    return _re.sub(r"[^a-z0-9]+", "", name.casefold())


def territory_family(territory: str) -> str:
    return "ocg" if territory.startswith("ocg") else "tcg"


def territory_matches_scope(territory: str, scope: frozenset[str]) -> bool:
    """True when an event in `territory` counts for a pool scoped to `scope`.

    An umbrella territory ('tcg'/'ocg' - a source that did not distinguish)
    satisfies any territory of its family, and a family umbrella in the scope
    accepts any specific territory of that family.
    """
    if territory in scope:
        return True
    family = territory_family(territory)
    if territory == family:  # umbrella event: matches any scoped territory of the family
        return any(territory_family(s) == family for s in scope)
    return family in scope  # specific event: matches an umbrella scope


def _last_day_of_month(year: int, month: int) -> _dt.date:
    if month == 12:
        return _dt.date(year, 12, 31)
    return _dt.date(year, month + 1, 1) - _dt.timedelta(days=1)


@dataclass
class ReleaseEvent:
    territory: str
    date: str
    precision: str
    status: str
    kind: str
    dispute: list[dict[str, Any]]
    sources: list[str]
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "ReleaseEvent":
        try:
            return cls(
                territory=str(raw["territory"]),
                date=str(raw["date"]),
                precision=str(raw.get("precision", "day")),
                status=str(raw.get("status", "reported")),
                kind=str(raw.get("kind", "retail")),
                dispute=list(raw.get("dispute", [])),
                sources=list(raw.get("sources", [])),
                raw=raw,
            )
        except KeyError as exc:
            raise DataError(path, f"release event {raw!r} missing {exc}") from exc

    @staticmethod
    def _bounds(date_str: str, precision: str) -> tuple[_dt.date, _dt.date]:
        d = parse_date(date_str)
        if precision == "month":
            return _dt.date(d.year, d.month, 1), _last_day_of_month(d.year, d.month)
        if precision == "year":
            return _dt.date(d.year, 1, 1), _dt.date(d.year, 12, 31)
        return d, d

    def bounds(self) -> tuple[_dt.date, _dt.date]:
        """(earliest, latest) possible real date, widened by precision and by
        every recorded dispute alternative. Certainty about a cutoff exists
        only when the whole range lies on one side of it."""
        earliest, latest = self._bounds(self.date, self.precision)
        for alt in self.dispute:
            alt_date = alt.get("date")
            if not alt_date:
                continue
            lo, hi = self._bounds(str(alt_date), str(alt.get("precision", "day")))
            earliest = min(earliest, lo)
            latest = max(latest, hi)
        return earliest, latest


@dataclass
class Printing:
    passcode: int
    name: str
    numbers: list[str]
    events: list[ReleaseEvent]
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "Printing":
        try:
            return cls(
                passcode=int(raw["passcode"]),
                name=str(raw["name"]),
                numbers=[str(n) for n in raw.get("numbers", [])],
                events=[ReleaseEvent.load(e, path) for e in raw.get("release_events", [])],
                raw=raw,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DataError(path, f"bad printing {raw!r}: {exc}") from exc


@dataclass
class Product:
    id: str
    code: str
    name: str
    kind: str
    dating: str  # "product" | "per-printing"
    events: list[ReleaseEvent]
    printings: list[Printing]
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "Product":
        return cls(
            id=str(raw.get("id", "")),
            code=str(raw.get("code", "")),
            name=str(raw.get("name", "")),
            kind=str(raw.get("kind", "")),
            dating=str(raw.get("dating", "product")),
            events=[ReleaseEvent.load(e, path) for e in raw.get("release_events", [])],
            printings=[Printing.load(p, path) for p in raw.get("printings", [])],
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )

    def events_for(self, printing: Printing) -> list[ReleaseEvent]:
        """The release events governing one printing: its own if present,
        otherwise the product-level events (unless dating=per-printing, where
        an event-less printing is deliberately undated - a reprint whose
        serial-promo date is unresearched contributes no availability)."""
        if printing.events:
            return printing.events
        if self.dating == "per-printing":
            return []
        return self.events


GAP_KINDS = ("missing-product-printings", "unmatched-cards", "undated-availability", "other")
GAP_STATUSES = ("unresolved", "resolved-safe", "resolved-imported")
GAP_IMPACTS = ("pool-membership", "provenance-only")
GAP_RATIONALES = (
    "no-playable-cards",
    "cards-available-earlier",
    "repackaging-only",
    "roster-imported",
)


@dataclass
class ReleaseGap:
    id: str
    kind: str
    subjects: list[str]
    territories: list[str]
    possible_from: str
    date_precision: str
    status: str
    impact: str
    resolution: dict[str, Any] | None
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "ReleaseGap":
        return cls(
            id=str(raw.get("id", "")),
            kind=str(raw.get("kind", "")),
            subjects=[str(s) for s in raw.get("subjects", [])],
            territories=[str(t) for t in raw.get("territories", [])],
            possible_from=str(raw.get("possible_from", "")),
            date_precision=str(raw.get("date_precision", "day")),
            status=str(raw.get("status", "")),
            impact=str(raw.get("impact", "")),
            resolution=raw.get("resolution"),
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )

    def earliest_possible(self) -> _dt.date | None:
        try:
            lo, _ = ReleaseEvent._bounds(self.possible_from, self.date_precision)
        except ValueError:
            return None
        return lo

    def blocks(self, day: _dt.date, scope: frozenset[str]) -> bool:
        """True when this gap could alter card availability for a cutoff at
        `day` under territory `scope`: it is unresolved, could change pool
        membership, could have begun on or before `day`, and touches a scoped
        territory. An unparseable date blocks conservatively."""
        if self.status != "unresolved" or self.impact != "pool-membership":
            return False
        earliest = self.earliest_possible()
        if earliest is not None and earliest > day:
            return False
        if not self.territories:
            # a gap that doesn't say where it applies blocks everywhere
            # (the validator separately rejects the record)
            return True
        return any(territory_matches_scope(t, scope) for t in self.territories)


@dataclass
class ReleaseCoverage:
    windows: list[dict[str, Any]]
    known_gaps: list[str]
    sources: list[str]
    path: Path
    raw: dict[str, Any]

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "ReleaseCoverage":
        return cls(
            windows=list(raw.get("windows", [])),
            known_gaps=list(raw.get("known_gaps", [])),
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
        )

    def covers(
        self,
        day: _dt.date,
        scope: frozenset[str],
        gaps: "list[ReleaseGap] | tuple[ReleaseGap, ...]" = (),
    ) -> bool:
        """True when the dataset can DEFEND completeness for `day`/`scope`:
        some claimed-complete window contains them (umbrella territories cover
        their family) AND no unresolved pool-impacting gap could alter
        availability at or before `day` in a scoped territory. Certification
        is earned - a window's status flag alone is never sufficient."""
        for gap in gaps:
            if gap.blocks(day, scope):
                return False
        for window in self.windows:
            if window.get("status") not in ("complete", "verified"):
                continue
            try:
                start = parse_date(str(window.get("from")))
                end = parse_date(str(window.get("through")))
            except ValueError:
                continue
            if not (start <= day <= end):
                continue
            covered = set(window.get("territories", []))
            if all(
                t in covered or territory_family(t) in covered
                for t in scope
            ):
                return True
        return False


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
    reference_parity: dict[str, Any] | None
    unresolved_policy: dict[str, Any] | None
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
            reference_parity=overrides.get("reference_parity"),
            unresolved_policy=overrides.get("unresolved_policy"),
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
