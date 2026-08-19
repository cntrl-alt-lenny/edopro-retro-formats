"""Deriving card availability from canonical release records.

The release dataset (data/releases/products/*.json) stores raw historical
facts: products, their release events per territory, and their printings.
This module derives what pools need from those facts:

    "was canonical card X legally obtainable in scope S on or before date D?"

Derivation rules (documented in docs/releases.md):

- A printing is governed by its own release events if it has any, else by its
  product's events - except in `dating: per-printing` products (serial promo
  series), where an event-less printing is deliberately undated and
  contributes nothing. Reprints therefore can never move a card's first
  availability: extra printings only ever ADD (later) events, and the
  derivation takes the earliest.
- Only events whose kind grants real availability count (retail, event,
  distribution-start - not prerelease).
- Territory scoping: an event matches a scope per
  model.territory_matches_scope (umbrella 'tcg' events satisfy any TCG
  territory and vice versa).
- Printed passcodes are canonicalised through the card index: an alias within
  the artwork window (+/-10) accrues availability to its base card and is
  remembered as a variant; anything else is its own canonical card.
- Precision and disputes widen an event's possible date range. A card is
  definitely in a cutoff pool only if some event's whole range is <= cutoff;
  if the only candidate events straddle the cutoff, the card is AMBIGUOUS and
  must be resolved by an explicit, sourced pool include/exclude - never
  silently.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from .model import (
    ARTWORK_OFFSET,
    AVAILABILITY_KINDS,
    Pool,
    Printing,
    Product,
    ReleaseEvent,
    territory_family,
    territory_matches_scope,
)
from .repo import Repository

TCG_SCOPE = frozenset({"tcg", "tcg-na", "tcg-eu", "tcg-oce"})
OCG_SCOPE = frozenset({"ocg", "ocg-jp", "ocg-kr", "ocg-asia"})


def default_scope(region: str) -> frozenset[str]:
    """The territories whose releases count for a pool of this region.

    TCG defaults to ALL TCG territories: historically a card released
    anywhere in the TCG was tournament-legal TCG-wide (Europe-only Retro Pack
    cards were legal at North American events). Pools tracking one
    territory's shelves can narrow this via cutoff.territories.
    """
    if region == "TCG":
        return TCG_SCOPE
    if region == "OCG":
        return OCG_SCOPE
    return TCG_SCOPE | OCG_SCOPE


@dataclass(frozen=True)
class EventRef:
    """One availability-granting event, traced back to where it came from."""

    product_id: str
    printed_passcode: int
    number: str | None
    event: ReleaseEvent


@dataclass
class CardAvailability:
    """Everything the release dataset knows about one canonical card."""

    passcode: int
    events: list[EventRef] = field(default_factory=list)
    printed_codes: set[int] = field(default_factory=set)
    undated_printings: list[tuple[str, int]] = field(default_factory=list)

    def variants(self) -> set[int]:
        return {c for c in self.printed_codes if c != self.passcode}


@dataclass
class ReleaseIndex:
    """Canonical-card availability derived from every product record."""

    by_canonical: dict[int, CardAvailability] = field(default_factory=dict)
    unknown_printings: list[tuple[str, int, str]] = field(default_factory=list)

    @classmethod
    def build(cls, repo: Repository) -> "ReleaseIndex":
        index = cls()
        card_index = repo.card_index
        for code in sorted(repo.products):
            product = repo.products[code]
            for printing in product.printings:
                canonical = index._canonicalise(printing.passcode, card_index)
                if canonical is None:
                    index.unknown_printings.append(
                        (product.id, printing.passcode, printing.name)
                    )
                    continue
                slot = index.by_canonical.setdefault(canonical, CardAvailability(canonical))
                slot.printed_codes.add(printing.passcode)
                events = product.events_for(printing)
                dated = False
                for event in events:
                    if event.kind not in AVAILABILITY_KINDS:
                        continue
                    dated = True
                    slot.events.append(
                        EventRef(
                            product_id=product.id,
                            printed_passcode=printing.passcode,
                            number=printing.numbers[0] if printing.numbers else None,
                            event=event,
                        )
                    )
                if not dated:
                    slot.undated_printings.append((product.id, printing.passcode))
        return index

    @staticmethod
    def _canonicalise(passcode: int, card_index) -> int | None:
        row = card_index.by_passcode.get(passcode)
        if row is None:
            return None
        alias = row.get("alias_of")
        if alias and abs(int(alias) - passcode) < ARTWORK_OFFSET:
            return int(alias)
        return passcode

    def dated_canonical_count(self) -> int:
        return sum(1 for a in self.by_canonical.values() if a.events)


@dataclass
class CutoffEvaluation:
    """The derived membership of one release-cutoff pool."""

    included: dict[int, dict] = field(default_factory=dict)  # canonical -> pool card entry
    ambiguous: dict[int, list[EventRef]] = field(default_factory=dict)
    forced_in: list[int] = field(default_factory=list)
    forced_out: list[int] = field(default_factory=list)
    scope: frozenset[str] = frozenset()

    def cards(self) -> list[dict]:
        return [self.included[code] for code in sorted(self.included)]


def evaluate_cutoff(pool: Pool, repo: Repository, index: ReleaseIndex | None = None) -> CutoffEvaluation:
    """Compute a release-cutoff pool's membership from the release dataset.

    Deterministic: same canonical data, same result. Ambiguities (events whose
    possible date range straddles the cutoff) are returned, not resolved - the
    validator turns unresolved ones into errors.
    """
    if pool.kind != "release-cutoff" or not pool.cutoff:
        raise ValueError(f"pool {pool.id} is not a release-cutoff pool")
    index = index or ReleaseIndex.build(repo)
    cutoff = _dt.date.fromisoformat(str(pool.cutoff["cutoff_date"]))
    scope = frozenset(pool.cutoff.get("territories") or default_scope(pool.region))
    excluded_products = {
        str(entry.get("product")) for entry in pool.cutoff.get("exclude_products", [])
    }

    result = CutoffEvaluation(scope=scope)
    name_of = repo.card_index.name_of

    for canonical, availability in index.by_canonical.items():
        in_scope = [
            ref for ref in availability.events
            if ref.product_id not in excluded_products
            and territory_matches_scope(ref.event.territory, scope)
        ]
        if not in_scope:
            continue
        definite = [ref for ref in in_scope if ref.event.bounds()[1] <= cutoff]
        straddling = [
            ref for ref in in_scope
            if ref.event.bounds()[0] <= cutoff < ref.event.bounds()[1]
        ]
        if definite:
            result.included[canonical] = _pool_entry(canonical, availability, definite, name_of)
        elif straddling:
            result.ambiguous[canonical] = straddling

    for entry in pool.cutoff.get("include", []):
        code = int(entry["card"]["passcode"])
        result.ambiguous.pop(code, None)
        if code not in result.included:
            pool_entry = {"passcode": code, "name": str(entry["card"]["name"])}
            availability = index.by_canonical.get(code)
            if availability:
                # variants that were themselves printed by the cutoff, under
                # the widest reading of the forced-in card's events
                definite = [
                    ref for ref in availability.events
                    if territory_matches_scope(ref.event.territory, scope)
                    and ref.event.bounds()[0] <= cutoff
                ]
                variants = _variants_of(code, definite)
                if variants:
                    pool_entry["variant_passcodes"] = sorted(variants)
            result.included[code] = pool_entry
            result.forced_in.append(code)

    for entry in pool.cutoff.get("exclude", []):
        code = int(entry["card"]["passcode"])
        if code in result.included:
            del result.included[code]
            result.forced_out.append(code)
        result.ambiguous.pop(code, None)

    return result


def _pool_entry(canonical: int, availability: CardAvailability, definite: list[EventRef], name_of) -> dict:
    entry: dict = {"passcode": canonical, "name": name_of(canonical) or ""}
    variants = _variants_of(canonical, definite)
    if variants:
        entry["variant_passcodes"] = sorted(variants)
    return entry


def _variants_of(canonical: int, definite: list[EventRef]) -> set[int]:
    """Variant passcodes among the printings that were definitely available by
    the cutoff (an artwork code first printed after the format is not emitted)."""
    return {ref.printed_passcode for ref in definite} - {canonical}


def materialize_pool(pool: Pool, repo: Repository, index: ReleaseIndex | None = None):
    """Return (new raw pool dict with cards filled in, evaluation).

    The caller decides whether to write it; the validator recomputes this on
    every run and fails on drift, so the committed cards stay a reviewable
    projection of the release facts.
    """
    evaluation = evaluate_cutoff(pool, repo, index)
    raw = dict(pool.raw)
    raw["cards"] = evaluation.cards()
    return raw, evaluation
