"""Deterministic generation of EDOPro *.lflist.conf files from canonical data.

Output format (verified against EDOPro's parser, gframe/deck_manager.cpp:35-87,
and Project Ignis's GOAT.lflist.conf; see docs/edopro-research.md):

    #[<list name>]          <- comment, conventional
    !<list name>            <- the name EDOPro shows in the banlist dropdown
    $whitelist              <- optional: cards NOT listed become illegal
    <code> <count> --<comment>

Canonical data references cards by their MODERN passcode. This module maps
canonical entries to the passcodes EDOPro must actually see:

- when a format uses a card's historical (pre-errata) implementation, the
  historical passcode replaces the modern one entirely — exactly as upstream's
  GOAT list omits the modern Chaos Emperor Dragon and whitelists 511000819;
- artwork-variant passcodes (cdb alias within +/-10 of the base code, the
  range EDOPro treats as the same functional card: gframe/data_manager.h:74-85)
  found in the card index are emitted alongside their base code, because
  whitelists only extend a base entry to variants inside that range.

Determinism: entries are grouped into fixed sections and sorted by passcode;
the header carries no timestamps; identical inputs give identical bytes.

EDOPro identifies a list by an order-independent hash of its (code, count)
pairs — the name is NOT hashed — so a generated list whose entries match an
upstream list is network-compatible with it. `lflist_hash` reimplements
gframe/deck_manager.cpp:57,80 so tests can prove such parity.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from . import GENERATOR_NAME
from .model import (
    ARTWORK_OFFSET,  # re-exported; importers historically import it from here
    STATUS_TO_COUNT,
    UNLIMITED_COUNT,
    Banlist,
    Erratum,
    Format,
    Pool,
)
from .repo import Repository

_SECTION_ORDER = ("forbidden", "limited", "semilimited", "unlimited")
_SECTION_HEADERS = {
    "forbidden": "#forbidden",
    "limited": "#limited",
    "semilimited": "#semilimited",
    "unlimited": "#unlimited (whitelist pool)",
}

HASH_SEED = 0x7DFCEE6A


def lflist_hash(entries: dict[int, int]) -> int:
    """EDOPro's banlist content hash (gframe/deck_manager.cpp:57,80).

    Assumes each (code, count) appears once, which holds for generated lists
    (the parser folds every LINE into the hash, so duplicated lines in
    hand-written files can diverge)."""
    h = HASH_SEED
    for code, count in entries.items():
        code &= 0xFFFFFFFF
        rot18 = ((code << 18) | (code >> 14)) & 0xFFFFFFFF
        rot27 = ((code << (27 + count)) | (code >> (5 - count))) & 0xFFFFFFFF
        h ^= rot18 ^ rot27
    return h & 0xFFFFFFFF


def parse_lflist(text: str) -> dict[str, dict[int, int]]:
    """Parse an lflist.conf into {list name: {code: count}} (mirrors
    gframe/deck_manager.cpp:35-87 closely enough for round-trip testing)."""
    lists: dict[str, dict[int, int]] = {}
    current: dict[int, int] | None = None
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            current = lists.setdefault(line[1:], {})
            continue
        if line.startswith("$"):
            continue
        if current is None:
            continue
        head, _, rest = line.partition(" ")
        try:
            code = int(head)
        except ValueError:
            continue
        if code == 0:
            continue
        digits = ""
        for ch in rest.lstrip():
            if ch in "-0123456789":
                digits += ch
            else:
                break
        try:
            current[code] = int(digits)
        except ValueError:
            continue
    return lists


@dataclass(frozen=True)
class SelectedOverride:
    """One card whose modern implementation must be substituted in a format:
    the erratum record plus the implementation of the version its chronology
    (or an explicit include) selected for the snapshot."""

    erratum: Erratum
    implementation: dict


class ErrataSelectionError(ValueError):
    """Raised when a format's errata applicability cannot be decided safely:
    a reviewed record's chronology is ambiguous at the snapshot, or the
    selected version has no usable implementation, and the format does not
    adjudicate it via errata_overrides. The validator reports the same
    conditions as errors; this exception keeps direct build calls fail-safe."""

    def __init__(self, fmt_id: str, problems: list[str]):
        super().__init__(
            f"{fmt_id}: errata applicability is undecidable for {len(problems)} record(s):\n  "
            + "\n  ".join(problems)
        )
        self.problems = problems


def baseline_override(erratum: Erratum) -> dict | None:
    """The erratum's baseline historical implementation, when it is usable as
    a substitution (an upstream or custom historical passcode)."""
    impl = erratum.implementation
    if impl.get("strategy") in ("reuse-upstream", "custom-script") and impl.get(
        "historical_passcode"
    ):
        return impl
    return None


def select_applicable_errata(fmt: Format, repo: Repository) -> dict[int, SelectedOverride]:
    """{modern passcode: selected override} for every historical substitution
    active in fmt, computed fail-safe from each record's chronology.

    Resolution order per record:

    1. an explicit `exclude` wins outright (the format keeps the modern card);
    2. an explicit `include` pins the BASELINE version — a per-card
       adjudication of last resort;
    3. `reference_parity`: the format is defined by reproducing an existing
       reference implementation, so every record with a baseline historical
       implementation is substituted (that is what the reference list does);
    4. otherwise the record's own chronology decides, and only for REVIEWED
       records — an imported record never applies computationally, so a
       mechanically-guessed import cannot quietly change a format;
    5. ambiguity resolves through `unresolved_policy` when the format states
       one, and is a hard error otherwise. Selection never guesses silently.
    """
    selected: dict[int, SelectedOverride] = {}
    problems: list[str] = []
    snapshot = _dt.date.fromisoformat(fmt.snapshot) if fmt.snapshot else None
    parity = fmt.reference_parity
    policy = (fmt.unresolved_policy or {}).get("choice")

    for erratum in repo.errata.values():
        if erratum.id in fmt.errata_exclude:
            continue
        if erratum.id in fmt.errata_include:
            impl = baseline_override(erratum)
            if impl is not None:
                selected[erratum.modern_card.passcode] = SelectedOverride(erratum, impl)
            continue
        if parity:
            # Reproducing the reference implementation is the format's
            # definition; disagreements with our chronology are reported by
            # the validator rather than silently changing the output.
            impl = baseline_override(erratum)
            if impl is not None:
                selected[erratum.modern_card.passcode] = SelectedOverride(erratum, impl)
            continue
        if snapshot is None or not erratum.relevant_changes():
            continue
        if erratum.review_status != "reviewed":
            continue
        selection = erratum.selection_at(snapshot)
        if selection.state == "historical":
            selected[erratum.modern_card.passcode] = SelectedOverride(
                erratum, selection.implementation
            )
        elif selection.state == "ambiguous":
            if policy == "historical":
                impl = baseline_override(erratum)
                if impl is not None:
                    selected[erratum.modern_card.passcode] = SelectedOverride(erratum, impl)
            elif policy == "modern":
                pass  # documented conservative default; validator names each card
            else:
                problems.append(
                    f"{erratum.id}: chronology ambiguous at snapshot {snapshot} "
                    "(narrow the change's effective chronology, adjudicate with a "
                    "documented errata_overrides include/exclude, or state an "
                    "errata_overrides.unresolved_policy)"
                )
        elif selection.state == "gap" and not selection.acknowledged_gap:
            problems.append(
                f"{erratum.id}: version {selection.version_index} applies at {snapshot} "
                "but has no usable implementation and the record does not acknowledge "
                "the gap (record one, document implementation.gap, or exclude)"
            )
        # An ACKNOWLEDGED gap deliberately falls through to the modern card:
        # the divergence is recorded on the record and reported, not silent.
    if problems:
        raise ErrataSelectionError(fmt.id, problems)
    return selected


def list_display_name(fmt: Format) -> str:
    """The `!name` shown in EDOPro. Prefixed so retro lists group together,
    sort chronologically, and never collide with Project Ignis's names."""
    return f"Retro {fmt.id}"


@dataclass
class BuiltList:
    text: str
    entries: dict[int, int]
    hash: int


def build_lflist(fmt: Format, repo: Repository) -> BuiltList:
    banlist = repo.banlists[fmt.banlist_id]
    pool = repo.pools[fmt.pool_id]
    if pool.cards:
        # Extensional pools always carry cards; release-cutoff pools carry
        # them once materialised from the release dataset (the validator
        # recomputes and cross-checks that projection on every run).
        return _build_whitelist(fmt, banlist, pool, repo)
    # Without a materialised pool we can still emit the historical
    # Forbidden/Limited list; the format is then only accurate for decks
    # already restricted to period cards. The header says so.
    return _build_banlist_only(fmt, banlist)


def _header(fmt: Format, mode_note: str) -> list[str]:
    name = list_display_name(fmt)
    return [
        f"#[{name}]",
        f"!{name}",
        f"# {fmt.name} ({fmt.region}), snapshot {fmt.snapshot}",
        f"# GENERATED by {GENERATOR_NAME} from formats/{fmt.id}/ -- do not edit by hand.",
        f"# {mode_note}",
    ]


def _finish(lines: list[str], sections: dict[str, list[tuple[int, int, str]]]) -> BuiltList:
    entries: dict[int, int] = {}
    for section in _SECTION_ORDER:
        rows = sections.get(section) or []
        if not rows:
            continue
        lines.append(_SECTION_HEADERS[section])
        for passcode, count, comment in sorted(rows):
            lines.append(f"{passcode} {count} --{comment}")
            entries[passcode] = count
    return BuiltList(text="\n".join(lines) + "\n", entries=entries, hash=lflist_hash(entries))


def _build_whitelist(fmt: Format, banlist: Banlist, pool: Pool, repo: Repository) -> BuiltList:
    status_by_code = {e.card.passcode: e.status for e in banlist.entries}
    overrides = select_applicable_errata(fmt, repo)

    sections: dict[str, list[tuple[int, int, str]]] = {s: [] for s in _SECTION_ORDER}
    for card in pool.cards:
        status = status_by_code.get(card.passcode, "unlimited")
        count = STATUS_TO_COUNT.get(status, UNLIMITED_COUNT)
        section = status if status in sections else "unlimited"
        override = overrides.get(card.passcode)
        if override is not None:
            # The modern implementation is period-incorrect: emit ONLY the
            # selected historical passcode (and its artwork variants).
            impl = override.implementation
            emit_codes = [
                int(impl["historical_passcode"]),
                *(int(v) for v in impl.get("historical_variant_passcodes", [])),
            ]
            label = f"{card.name} (pre-errata)"
        else:
            emit_codes = [card.passcode, *card.variants]
            label = card.name
        for code in sorted(set(emit_codes)):
            sections[section].append((code, count, label))

    lines = _header(fmt, "Whitelist: cards not listed here are not legal in this format.")
    lines.append("$whitelist")
    return _finish(lines, sections)


def _build_banlist_only(fmt: Format, banlist: Banlist) -> BuiltList:
    lines = _header(
        fmt,
        "Forbidden/Limited only: the historical card pool is NOT enforced yet "
        "(pool data pending); newer cards must be excluded manually.",
    )
    sections: dict[str, list[tuple[int, int, str]]] = {s: [] for s in _SECTION_ORDER}
    for entry in banlist.entries:
        sections[entry.status].append(
            (entry.card.passcode, STATUS_TO_COUNT[entry.status], entry.card.name)
        )
    return _finish(lines, sections)
