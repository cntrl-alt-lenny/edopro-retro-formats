"""Typed views over the canonical JSON records.

These are deliberately thin: every object keeps the raw dict it was loaded
from (`.raw`), and only the fields the toolchain actually computes with are
lifted into attributes. Semantic correctness is the validator's job, so the
constructors here fail only on structurally unusable input.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
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


PROVEN, CONTRADICTED, INCONCLUSIVE = "proven", "contradicted", "inconclusive"


def last_confirmed_old(effective: dict[str, Any]) -> _dt.date | None:
    """The latest date this event is GUARANTEED not to have happened yet, or
    None if the evidence never guarantees that (design doc §5). Exact date:
    the day before the precision-widened interval starts. Bounded: the
    attested-through date. Undated: None."""
    date = effective.get("date")
    if date:
        lo, _hi = _precision_bounds(str(date), str(effective.get("precision") or "day"))
        return lo - _dt.timedelta(days=1)
    old_through = effective.get("old_attested_through")
    return parse_date(str(old_through)) if old_through else None


def first_confirmed_new(effective: dict[str, Any]) -> _dt.date | None:
    """The earliest date this event is GUARANTEED to have already happened,
    or None if the evidence never guarantees that. Exact date: the
    precision-widened interval's end (the effective date itself, at day
    precision). Bounded: the attested-from date. Undated: None."""
    date = effective.get("date")
    if date:
        _lo, hi = _precision_bounds(str(date), str(effective.get("precision") or "day"))
        return hi
    new_from = effective.get("new_attested_from")
    return parse_date(str(new_from)) if new_from else None


def ordering_proof(before_effective: dict[str, Any], after_effective: dict[str, Any]) -> str:
    """PROVEN / CONTRADICTED / INCONCLUSIVE for the assertion `before` <
    `after`, worked out precisely (design doc §5) from the SAME chronology
    primitives `change_state_at()` uses — never a different combination of
    the evidence. Overlapping intervals alone are never CONTRADICTED, only
    INCONCLUSIVE; the two are provably mutually exclusive and dual
    (PROVEN(A<B) <=> CONTRADICTED(B<A))."""
    fcn_before = first_confirmed_new(before_effective)
    lco_after = last_confirmed_old(after_effective)
    if fcn_before is not None and lco_after is not None and fcn_before <= lco_after:
        return PROVEN
    lco_before = last_confirmed_old(before_effective)
    fcn_after = first_confirmed_new(after_effective)
    if lco_before is not None and fcn_after is not None and lco_before >= fcn_after:
        return CONTRADICTED
    return INCONCLUSIVE


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


# ---------------------------------------------------------------------------
# v2: historical-event DAG (docs/research/erratum-state-model-v2.md, frozen).
#
# Implementation step 2 of that document's revised sequence: this runtime
# path exists ALONGSIDE Erratum/ErratumSelection above, which stay exactly
# as they are. Every currently-canonical record is v1-shaped and continues
# to load and select through the legacy classes, byte for byte unchanged.
# No v1 concept (integer version_index, positional candidates) may leak into
# the types below; no v2 concept (event-set state identity) may leak into
# ErratumSelection above. See §8 of the design document for why: the two
# are semantically incompatible for the 49 structurally affected records,
# not merely differently shaped.
# ---------------------------------------------------------------------------


class SelectionError(Exception):
    """A v2 record's chronology is contradictory at a snapshot: no
    structurally reachable historical state is consistent with every
    event's independently-computed OLD/AMBIGUOUS/NEW status. This is a
    per-snapshot runtime condition, distinct from DataError (a record too
    malformed to load at all) — step 3's ordering-edge validator invariants
    are what should prevent a real record from ever reaching this state;
    until they exist, this is the defined, explicit failure behaviour
    rather than a silently invented answer."""


class Coverage(Enum):
    """The six-kind implementation-coverage sum type (design doc §4).
    MODERN is always synthesised, unconditionally, for the all-events
    (terminal) down-set alone — an author MAY still write a terminal
    `states[]` entry with kind 'modern' as redundant documentation (the
    schema permits it), but this runtime never trusts or even reads that
    entry: `_state_for()` synthesises MODERN for the terminal state
    regardless of what, if anything, is authored there. Ensuring 'modern'
    is never *wrongly* authored elsewhere is step 3's validator's job, not
    this constructor's. UNRESOLVED is never authored at all — the schema's
    `authoredCoverage` has no branch for it; it is exclusively the
    mechanical default for a reachable non-terminal down-set with no
    matching `states[]` entry. The other four (REUSE_UPSTREAM,
    CUSTOM_SCRIPT, NONE_NEEDED, KNOWN_GAP) are the ordinary authored kinds
    for any non-terminal state."""

    MODERN = "modern"
    REUSE_UPSTREAM = "reuse-upstream"
    CUSTOM_SCRIPT = "custom-script"
    NONE_NEEDED = "none-needed"
    KNOWN_GAP = "known-gap"
    UNRESOLVED = "unresolved"


# The coverage sum type's per-kind field sets, mirroring
# schemas/erratum.schema.json's `coverage*` branches EXACTLY (each of which is
# `additionalProperties: false`). Declared once here so the production
# validator - which runs on raw JSON before any schema check - enforces the
# same closed payload the schema does, instead of growing a second, drifting
# coverage model. `tests/test_erratum_schema.py` asserts this map still equals
# the schema's own branches, so the two cannot diverge unnoticed.
COVERAGE_FIELDS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    # kind: (required, allowed)
    "modern": (frozenset({"kind"}), frozenset({"kind"})),
    "reuse-upstream": (
        frozenset({"kind", "historical_passcode", "upstream"}),
        frozenset({"kind", "historical_passcode", "historical_variant_passcodes", "upstream", "script"}),
    ),
    "custom-script": (
        frozenset({"kind", "historical_passcode", "script"}),
        frozenset({"kind", "historical_passcode", "historical_variant_passcodes", "upstream", "script"}),
    ),
    "none-needed": (frozenset({"kind"}), frozenset({"kind"})),
    "known-gap": (
        frozenset({"kind", "gap_reason", "gap_sources"}),
        frozenset({"kind", "gap_reason", "gap_sources"}),
    ),
}


@dataclass(frozen=True)
class ImplementationCoverage:
    kind: Coverage
    historical_passcode: int | None = None
    historical_variant_passcodes: tuple[int, ...] = ()
    upstream: str | None = None
    script: str | None = None
    gap_reason: str | None = None
    gap_sources: tuple[str, ...] = ()

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "ImplementationCoverage":
        return cls(
            kind=Coverage(raw.get("kind")),
            historical_passcode=raw.get("historical_passcode"),
            historical_variant_passcodes=tuple(raw.get("historical_variant_passcodes", [])),
            upstream=raw.get("upstream"),
            script=raw.get("script"),
            gap_reason=raw.get("gap_reason"),
            gap_sources=tuple(raw.get("gap_sources", [])),
        )

    @classmethod
    def modern(cls) -> "ImplementationCoverage":
        return cls(kind=Coverage.MODERN)

    @classmethod
    def unresolved(cls) -> "ImplementationCoverage":
        return cls(kind=Coverage.UNRESOLVED)


@dataclass(frozen=True)
class HistoricalTransition:
    """One behavioural question an event answers. Chronology-free — an
    event's own `effective` block is the only chronology (design doc §1)."""

    kind: str
    axis: str | None
    summary: str
    historical_text: str | None
    modern_text: str | None
    sources: tuple[str, ...]
    raw: dict[str, Any]

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "HistoricalTransition":
        return cls(
            kind=str(raw.get("kind", "")),
            axis=raw.get("axis"),
            summary=str(raw.get("summary", "")),
            historical_text=raw.get("historical_text"),
            modern_text=raw.get("modern_text"),
            sources=tuple(raw.get("sources", [])),
            raw=raw,
        )

    @property
    def is_implementation_relevant(self) -> bool:
        return self.kind in IMPLEMENTATION_RELEVANT_KINDS


@dataclass(frozen=True)
class HistoricalEvent:
    """One historical-chronology node. A 2+-transition event is a sourced
    co-occurrence claim, not two events (design doc §2, §5 item 5)."""

    id: str
    effective: dict[str, Any]
    transitions: tuple[HistoricalTransition, ...]
    cooccurrence_sources: tuple[str, ...]
    raw: dict[str, Any]

    @classmethod
    def from_raw(cls, event_id: str, raw: dict[str, Any]) -> "HistoricalEvent":
        return cls(
            id=event_id,
            effective=dict(raw.get("effective") or {}),
            transitions=tuple(HistoricalTransition.from_raw(t) for t in raw.get("transitions", [])),
            cooccurrence_sources=tuple(raw.get("cooccurrence_sources", [])),
            raw=raw,
        )

    @property
    def is_implementation_relevant(self) -> bool:
        """An event creates a distinguishable HistoricalState dimension iff
        at least one of its transitions does (design doc: cosmetic/engine-
        only events never create an implementation-state bit)."""
        return any(t.is_implementation_relevant for t in self.transitions)

    def state_at(self, snapshot: _dt.date) -> str:
        """OLD/AMBIGUOUS/NEW at `snapshot`, via the same chronology rule
        v1 changes use — reused directly, unmodified, on a change-shaped
        wrapper around this event's own `effective` block."""
        return change_state_at({"effective": self.effective}, snapshot)


@dataclass(frozen=True)
class HistoricalState:
    """A candidate historical state: which relevant events have occurred.
    `events` (a frozenset of event ids) is this state's ONLY identity —
    `label` and `coverage` are descriptive, never compared. Compare states
    with `.events ==`, never `is` or whole-object `==` (design doc §9)."""

    events: frozenset[str]
    label: str
    coverage: ImplementationCoverage


@dataclass(frozen=True)
class SemanticErratumSelection:
    """The v2 selection result at one snapshot — chronology and per-
    candidate coverage as separate dimensions (design doc §9), never an
    integer version_index or positional candidates tuple."""

    chronology: str  # "determinate" | "ambiguous"
    candidates: tuple[HistoricalState, ...]
    modern_state: HistoricalState

    @property
    def is_modern(self) -> bool:
        return self.chronology == "determinate" and self.candidates[0].events == self.modern_state.events

    @property
    def modern_is_possible(self) -> bool:
        return any(c.events == self.modern_state.events for c in self.candidates)

    @property
    def has_known_gap(self) -> bool:
        return any(c.coverage.kind == Coverage.KNOWN_GAP for c in self.candidates)

    @property
    def needs_implementation_research(self) -> bool:
        return any(c.coverage.kind == Coverage.UNRESOLVED for c in self.candidates)


def _descendants_and_check_acyclic(
    all_ids: frozenset[str], pairs: list[tuple[str, str]], record_id: str, path: Path
) -> dict[str, frozenset[str]]:
    """before_id -> set of after_ids transitively reachable through `pairs`.
    Raises DataError for a dangling reference or a cycle — both structurally
    unusable input for down-set enumeration, not a step-3 semantic concern."""
    direct: dict[str, set[str]] = {node: set() for node in all_ids}
    for before, after in pairs:
        if before not in all_ids or after not in all_ids:
            raise DataError(
                path, f"{record_id}: ordering references unknown event id in ({before!r}, {after!r})"
            )
        direct[before].add(after)
    descendants: dict[str, frozenset[str]] = {}
    for node in all_ids:
        seen: set[str] = set()
        stack = list(direct[node])
        while stack:
            nxt = stack.pop()
            if nxt in seen:
                continue
            seen.add(nxt)
            stack.extend(direct[nxt])
        if node in seen:
            raise DataError(path, f"{record_id}: ordering graph contains a cycle through {node!r}")
        descendants[node] = frozenset(seen)
    return descendants


def _predecessors_among(
    ids: frozenset[str], descendants: dict[str, frozenset[str]]
) -> dict[str, frozenset[str]]:
    """For each event B in `ids`, every other event A in `ids` transitively
    ordered before it — even through an intermediate not itself in `ids`,
    e.g. `A -> some-intermediate -> B` still yields A before B. Called with
    the FULL event id set (§9 correction): cosmetic/engine-only events
    have their own predecessors too, needed for full-DAG consistency, not
    only for propagating order past them."""
    return {
        after: frozenset(before for before in ids if before != after and after in descendants.get(before, ()))
        for after in ids
    }


def _reachable_down_sets(
    ids: frozenset[str], predecessors: dict[str, frozenset[str]]
) -> tuple[frozenset[str], ...]:
    """Every down-set (order ideal) the ordering DAG can produce over
    `ids` — exhaustive, not sampled; the corpus's largest record has only
    a handful of events. Deterministically ordered by (size, sorted ids),
    never by declaration/JSON order."""
    sorted_ids = tuple(sorted(ids))
    valid: list[frozenset[str]] = []
    for size in range(len(sorted_ids) + 1):
        for combo in combinations(sorted_ids, size):
            candidate = frozenset(combo)
            if all(predecessors.get(member, frozenset()) <= candidate for member in candidate):
                valid.append(candidate)
    return tuple(sorted(valid, key=lambda s: (len(s), tuple(sorted(s)))))


def _desugar_v2_sugar(raw: dict[str, Any], path: Path) -> dict[str, Any]:
    """The flattened single-event/single-transition sugar -> the equivalent
    full `events{}`/`ordering`/`states[]` shape, so exactly one parser
    (`ErratumV2.load`) ever implements the semantics (design doc §13).

    Sugar is only for a single FUNCTIONAL or RULING transition. A
    cosmetic/engine-only event creates no implementation-state dimension, so
    its relevant-event set is empty, `{}` IS the terminal state, and the
    terminal state's coverage is unconditionally MODERN - while the sugar's
    required `coverage` is an *authored baseline* coverage, which may never
    be MODERN. Such a record is therefore schema-valid-looking but has no
    consistent runtime meaning: the authored coverage would be silently
    discarded. Rejected here rather than quietly ignored, because
    `Repository.load()` runs before any JSON Schema check."""
    event_raw = raw.get("event") or {}
    kind = event_raw.get("kind")
    if kind not in IMPLEMENTATION_RELEVANT_KINDS:
        raise DataError(
            path,
            f"{raw.get('id', '<no id>')}: flattened v2 sugar carries a {kind!r} transition, but "
            "sugar is only for a single functional/ruling transition - a cosmetic/engine-only "
            "event creates no implementation-state dimension, so there is no baseline state for "
            "its `coverage` to describe. Write it as full v2 instead: events{} with the "
            "transition, ordering {}, and no states[].",
        )
    transition_raw = {
        "kind": event_raw.get("kind"),
        "axis": event_raw.get("axis"),
        "historical_text": event_raw.get("historical_text"),
        "modern_text": event_raw.get("modern_text"),
        "summary": event_raw.get("summary"),
        "sources": event_raw.get("sources", []),
    }
    desugared = {k: v for k, v in raw.items() if k not in ("event", "coverage")}
    desugared["events"] = {
        "event": {"effective": event_raw.get("effective") or {}, "transitions": [transition_raw]}
    }
    desugared["ordering"] = {}
    coverage = raw.get("coverage")
    desugared["states"] = [{"events": [], "coverage": coverage}] if coverage is not None else []
    return desugared


@dataclass
class ErratumV2:
    """A v2-shaped erratum record: the historical-event DAG (design doc
    §2), parsed and selected entirely independently of `Erratum` above —
    never sharing a code path, never inferring order from declaration
    position. Construct via `.load()`, exactly like `Erratum`."""

    id: str
    modern_card: CardRef
    classification: str
    events: dict[str, HistoricalEvent]
    raw_chains: tuple[tuple[str, ...], ...]
    raw_edges: tuple[dict[str, Any], ...]
    authored_states: dict[frozenset[str], ImplementationCoverage]
    sources: list[str]
    path: Path
    raw: dict[str, Any]
    # Full-event-DAG down-sets (over EVERY event, relevant or not) — §9's
    # correction: a cosmetic/engine-only event still happened-or-didn't at
    # a snapshot, and its own status can force a relevant predecessor to
    # have occurred or a relevant successor not to have, even though the
    # event itself never appears in a HistoricalState's identity. Projected
    # onto relevant ids only inside selection_at(), never here.
    _full_reachable: tuple[frozenset[str], ...]
    # "sugar" | "full": which shape the AUTHOR wrote. Sugar legitimately has
    # no authored `ordering` (desugaring synthesises `{}`), while full v2
    # requires an explicit one even when empty - a distinction the desugared
    # `raw` can no longer show, so it is recorded at parse time.
    authored_shape: str = "full"

    @classmethod
    def load(cls, raw: dict[str, Any], path: Path) -> "ErratumV2":
        authored_shape = "full"
        if "event" in raw:
            authored_shape = "sugar"
            raw = _desugar_v2_sugar(raw, path)
        record_id = str(raw.get("id", ""))
        events = {
            event_id: HistoricalEvent.from_raw(event_id, event_raw)
            for event_id, event_raw in (raw.get("events") or {}).items()
        }
        ordering = raw.get("ordering") or {}
        raw_chains = tuple(tuple(chain) for chain in ordering.get("chains", []))
        raw_edges = tuple(dict(edge) for edge in ordering.get("edges", []))
        pairs: list[tuple[str, str]] = []
        for chain in raw_chains:
            pairs.extend(zip(chain, chain[1:]))
        for edge in raw_edges:
            pairs.append((str(edge.get("before")), str(edge.get("after"))))
        all_ids = frozenset(events.keys())
        descendants = _descendants_and_check_acyclic(all_ids, pairs, record_id, path)
        # Predecessors and down-sets are computed over the FULL event set,
        # not just the relevant subset — a cosmetic/engine-only event still
        # has real chronology and real ordering constraints; only its
        # PROJECTION onto relevant ids is dropped, at selection time, never
        # its participation in what "consistent" means (§9 correction).
        predecessors = _predecessors_among(all_ids, descendants)
        full_reachable = _reachable_down_sets(all_ids, predecessors)
        try:
            authored_states = {
                frozenset(entry.get("events", [])): ImplementationCoverage.from_raw(entry.get("coverage") or {})
                for entry in raw.get("states", [])
            }
        except ValueError as exc:
            raise DataError(path, f"{record_id}: bad states[] coverage: {exc}") from exc
        return cls(
            id=record_id,
            modern_card=CardRef.from_raw(raw.get("modern_card", {}), path),
            classification=str(raw.get("classification", "")),
            events=events,
            raw_chains=raw_chains,
            raw_edges=raw_edges,
            authored_states=authored_states,
            sources=list(raw.get("sources", [])),
            path=path,
            raw=raw,
            _full_reachable=full_reachable,
            authored_shape=authored_shape,
        )

    def relevant_events(self) -> tuple[HistoricalEvent, ...]:
        return tuple(
            sorted((e for e in self.events.values() if e.is_implementation_relevant), key=lambda e: e.id)
        )

    def has_implementation_relevant_history(self) -> bool:
        return bool(self.relevant_events())

    @property
    def review_status(self) -> str:
        review = self.raw.get("review") or {}
        return str(review.get("status", "imported"))

    def structural_states(self) -> tuple[frozenset[str], ...]:
        """Every relevant-event down-set the ordering DAG can structurally
        produce, independent of any snapshot's chronology — the full-DAG
        down-sets projected onto relevant ids, deduplicated and
        deterministically ordered. Used for the reference-parity walk
        (§13 step 5) and for validating `states[]` entries against real
        structural reachability, neither of which is about a snapshot."""
        all_relevant_ids = frozenset(e.id for e in self.relevant_events())
        projected = {down_set & all_relevant_ids for down_set in self._full_reachable}
        return tuple(sorted(projected, key=lambda s: (len(s), tuple(sorted(s)))))

    def state_for(self, down_set: frozenset[str]) -> HistoricalState:
        """Public entry point for `_state_for`, keyed only by the down-set —
        callers outside this class (lflist.py, validate.py) should never
        need to separately track `all_relevant_ids` themselves."""
        all_relevant_ids = frozenset(e.id for e in self.relevant_events())
        return self._state_for(down_set, all_relevant_ids)

    def _state_for(self, down_set: frozenset[str], all_relevant_ids: frozenset[str]) -> HistoricalState:
        if down_set == all_relevant_ids:
            # Never read from authored_states: the terminal state's coverage
            # is structurally, unconditionally MODERN (design doc §4) — an
            # author may document it, but it is never trusted, only checked,
            # and that check is step 3's job, not this constructor's.
            coverage = ImplementationCoverage.modern()
        else:
            coverage = self.authored_states.get(down_set) or ImplementationCoverage.unresolved()
        label = ", ".join(sorted(down_set)) if down_set else "baseline"
        return HistoricalState(events=down_set, label=label, coverage=coverage)

    def selection_at(self, snapshot: _dt.date) -> SemanticErratumSelection:
        """Every distinguishable HistoricalState consistent with `snapshot`
        (design doc §2/§9) — never a range of integer positions, never
        inferred from declaration order.

        Correction (§9): a cosmetic/engine-only event creates no state
        DIMENSION, but it still happened-or-didn't, and that fact can
        force a relevant predecessor to have occurred (a confirmed-NEW
        successor requires every predecessor, relevant or not) or block a
        relevant successor (a confirmed-OLD predecessor forbids every
        successor, relevant or not) — even though the non-relevant event
        itself never appears in any state's identity. So: (1) find every
        FULL-event down-set consistent with EVERY event's own status,
        relevant or not; (2) project each survivor onto relevant ids only;
        (3) deduplicate — a non-relevant event genuinely undetermined at
        this snapshot must not fork one real implementation state into
        several identical-looking candidates.
        """
        all_relevant_ids = frozenset(e.id for e in self.relevant_events())
        try:
            statuses = {
                event_id: event.state_at(snapshot) for event_id, event in self.events.items()
            }
        except (ValueError, TypeError) as exc:
            # Malformed chronology (an unparseable date) is a property of the
            # RECORD, surfaced here as the one typed failure every caller
            # already handles, rather than as a raw ValueError escaping from
            # date parsing into whichever consumer happened to ask. The bad
            # date itself is reported by the validator's own effective-block
            # checks; this keeps a validation run - or a direct build - from
            # dying on it.
            raise SelectionError(
                f"{self.id}: chronology cannot be evaluated at {snapshot}: {exc}"
            ) from exc
        projected: set[frozenset[str]] = set()
        for down_set in self._full_reachable:
            consistent = True
            for event_id, status in statuses.items():
                if event_id in down_set:
                    if status == OLD:
                        consistent = False
                        break
                elif status == NEW:
                    consistent = False
                    break
            if consistent:
                projected.add(down_set & all_relevant_ids)
        if not projected:
            raise SelectionError(
                f"{self.id}: no historical state at {snapshot} is consistent with its own chronology "
                "(a contradictory v2 record — step 3's validator invariants should prevent this)"
            )
        ordered = sorted(projected, key=lambda s: (len(s), tuple(sorted(s))))
        states = tuple(self._state_for(s, all_relevant_ids) for s in ordered)
        modern_state = self._state_for(all_relevant_ids, all_relevant_ids)
        chronology = "determinate" if len(states) == 1 else "ambiguous"
        return SemanticErratumSelection(chronology=chronology, candidates=states, modern_state=modern_state)


def load_erratum_record(raw: dict[str, Any], path: Path) -> "Erratum | ErratumV2":
    """Structural shape dispatch (design doc §13 step 2): a record's shape
    is a fact about which top-level keys it has, mutually exclusive by
    schema construction — never a heuristic, never inferred from content.
    `changes` -> legacy v1; `events` -> full v2; `event` -> v2 sugar
    (desugars inside `ErratumV2.load`, so there is exactly one v2 parser,
    not two). `Repository.load()` calls this directly, before any JSON
    Schema validation runs — this function cannot assume schema-clean
    input, so it enforces the mutual exclusion itself: EXACTLY one of the
    three discriminators may be present, never zero, never two or more."""
    has_changes = "changes" in raw
    has_events = "events" in raw
    has_event = "event" in raw
    discriminators = (has_changes, has_events, has_event)
    if sum(discriminators) != 1:
        present = [name for name, flag in (("changes", has_changes), ("events", has_events), ("event", has_event)) if flag]
        raise DataError(
            path,
            "erratum record must have exactly one of changes/events/event "
            f"(v1/v2-full/v2-sugar); found {present or 'none'}",
        )
    if has_changes:
        return Erratum.load(raw, path)
    return ErratumV2.load(raw, path)


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
