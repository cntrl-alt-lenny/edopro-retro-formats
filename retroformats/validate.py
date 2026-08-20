"""Semantic validation of the canonical datasets.

The JSON Schemas in schemas/ document record shapes; this module enforces the
rules that matter for correctness and that schemas cannot express: referential
integrity, chronology, pool/banlist consistency, provenance coverage, and
card-identity cross-checks against the generated card index.

Every finding carries a stable code so tests and CI can assert on them.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from pathlib import Path

from .model import (
    AVAILABILITY_KINDS,
    CHANGE_KINDS,
    EFFECTIVE_STATUSES,
    EVENT_KINDS,
    EVENT_STATUSES,
    GAP_IMPACTS,
    GAP_KINDS,
    GAP_RATIONALES,
    GAP_STATUSES,
    IMPLEMENTATION_STATUSES,
    KIND_SEVERITY,
    PRECISIONS,
    PRODUCT_KINDS,
    STATUS_TO_COUNT,
    TERRITORIES,
    Banlist,
    Format,
    Pool,
    normalise_name,
    territory_matches_scope,
)
from .model import _precision_bounds as _model_precision_bounds
from .releases import ReleaseIndex, default_scope, evaluate_cutoff
from .repo import Repository

ERROR = "ERROR"
WARNING = "WARNING"

_FORMAT_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[a-z0-9-]+$")
_BANLIST_ID_RE = re.compile(r"^(tcg|ocg|ww)-[0-9]{4}-[0-9]{2}$")
_POOL_ID_RE = re.compile(r"^pool-[a-z0-9-]+$")
_PROFILE_ID_RE = re.compile(r"^rules-[a-z0-9-]+$")
_ERRATUM_ID_RE = re.compile(r"^erratum-[a-z0-9-]+$")
_FLAG_RE = re.compile(r"^DUEL_[A-Z0-9_]+$")
_PRODUCT_CODE_RE = re.compile(r"^[A-Z0-9][A-Za-z0-9-]{1,15}$")
_PRODUCT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")
_GAP_ID_RE = re.compile(r"^gap-[a-z0-9-]+$")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity} [{self.code}] {self.location}: {self.message}"


class Validator:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.findings: list[Finding] = []

    # -- helpers ---------------------------------------------------------

    def _emit(self, severity: str, code: str, location: Path | str, message: str) -> None:
        loc = str(location)
        root = str(self.repo.root)
        if loc.startswith(root):
            loc = loc[len(root) :].lstrip("/")
        self.findings.append(Finding(severity, code, loc, message))

    def error(self, code: str, location: Path | str, message: str) -> None:
        self._emit(ERROR, code, location, message)

    def warn(self, code: str, location: Path | str, message: str) -> None:
        self._emit(WARNING, code, location, message)

    @staticmethod
    def _date(value: str | None) -> _dt.date | None:
        if not value:
            return None
        try:
            return _dt.date.fromisoformat(value)
        except ValueError:
            return None

    def _check_sources(self, refs: list[str], location: Path, format_id: str | None, what: str) -> None:
        if not refs:
            self.error("sources.missing", location, f"{what} cites no sources")
            return
        for ref in refs:
            if self.repo.resolve_source(ref, format_id) is None:
                self.error(
                    "sources.unresolved",
                    location,
                    f"{what} cites unknown source id {ref!r}",
                )

    def _check_card(self, passcode: int, name: str, location: Path, context: str) -> None:
        index = self.repo.card_index
        if not index.by_passcode:
            return  # index absent entirely; reported once in validate()
        known = index.name_of(passcode)
        if known is None:
            self.error(
                "card.unknown-passcode",
                location,
                f"{context}: passcode {passcode} ({name!r}) is not in data/cards/index.json",
            )
        elif known != name:
            self.error(
                "card.name-mismatch",
                location,
                f"{context}: passcode {passcode} is {known!r} in the card index, data says {name!r}",
            )

    # -- record checks ---------------------------------------------------

    def _validate_banlist(self, banlist: Banlist) -> None:
        if not _BANLIST_ID_RE.match(banlist.id):
            self.error("banlist.bad-id", banlist.path, f"id {banlist.id!r} does not match <region>-<yyyy>-<mm>")
        if self._date(banlist.effective_date) is None:
            self.error("banlist.bad-date", banlist.path, f"effective_date {banlist.effective_date!r} is not a valid date")
        seen: dict[int, str] = {}
        for entry in banlist.entries:
            if entry.status not in STATUS_TO_COUNT:
                self.error("banlist.bad-status", banlist.path, f"{entry.card.name}: status {entry.status!r}")
            if entry.card.passcode in seen:
                self.error(
                    "banlist.duplicate-card",
                    banlist.path,
                    f"passcode {entry.card.passcode} listed twice ({seen[entry.card.passcode]!r} / {entry.card.name!r})",
                )
            seen[entry.card.passcode] = entry.card.name
            self._check_card(entry.card.passcode, entry.card.name, banlist.path, "banlist entry")
        self._check_sources(banlist.sources, banlist.path, None, "banlist")

    def _validate_pool(self, pool: Pool) -> None:
        if not _POOL_ID_RE.match(pool.id):
            self.error("pool.bad-id", pool.path, f"id {pool.id!r} does not match pool-<slug>")
        if pool.region not in ("TCG", "OCG", "Worldwide"):
            # An unknown region would silently widen default territory scoping.
            self.error("pool.bad-region", pool.path, f"region {pool.region!r}")
        basis = pool.raw.get("legality_basis")
        if basis is not None and basis not in ("availability", "historical-policy", "community-retrospective"):
            self.error("pool.bad-legality-basis", pool.path, f"legality_basis {basis!r}")
        if pool.kind == "extensional":
            if not pool.cards:
                self.error("pool.empty", pool.path, "extensional pool has no cards")
        elif pool.kind == "release-cutoff":
            if not pool.cutoff or not self._date((pool.cutoff or {}).get("cutoff_date")):
                self.error("pool.bad-cutoff", pool.path, "release-cutoff pool needs cutoff.cutoff_date")
            else:
                for territory in pool.cutoff.get("territories", []):
                    if territory not in TERRITORIES:
                        self.error("pool.bad-territory", pool.path, f"cutoff territory {territory!r}")
                for entry in pool.cutoff.get("exclude_products", []):
                    product_id = str(entry.get("product", ""))
                    if self.repo.products and product_id not in self.repo.products:
                        self.error(
                            "pool.unresolved-product",
                            pool.path,
                            f"cutoff.exclude_products references unknown product id {product_id!r}",
                        )
                    if not entry.get("reason"):
                        self.error(
                            "pool.exception-unreasoned",
                            pool.path,
                            f"cutoff.exclude_products {product_id}: historical exceptions must state a reason",
                        )
                    if not entry.get("sources"):
                        self.error(
                            "pool.exception-unsourced",
                            pool.path,
                            f"cutoff.exclude_products {product_id}: historical exceptions must cite sources",
                        )
                    else:
                        self._check_sources(list(entry["sources"]), pool.path, None, "cutoff.exclude_products")
                for key in ("include", "exclude"):
                    for entry in pool.cutoff.get(key, []):
                        if not isinstance(entry, dict) or not isinstance(entry.get("card"), dict):
                            self.error("pool.bad-exception", pool.path, f"cutoff.{key} entry {entry!r}")
                            continue
                        card_ref = entry["card"]
                        try:
                            passcode = int(card_ref.get("passcode"))
                            name = str(card_ref.get("name"))
                        except (TypeError, ValueError):
                            self.error("pool.bad-exception", pool.path, f"cutoff.{key} entry {entry!r}")
                            continue
                        self._check_card(passcode, name, pool.path, f"cutoff.{key} entry")
                        row = self.repo.card_index.by_passcode.get(passcode)
                        alias = row.get("alias_of") if row else None
                        if alias and abs(int(alias) - passcode) < 10:
                            self.error(
                                "pool.exception-noncanonical",
                                pool.path,
                                f"cutoff.{key} {name}: passcode {passcode} is an artwork variant "
                                f"of {alias}; exceptions must reference the canonical passcode",
                            )
                        if not entry.get("reason"):
                            self.error(
                                "pool.exception-unreasoned",
                                pool.path,
                                f"cutoff.{key} {name}: historical exceptions must state a reason",
                            )
                        if not entry.get("sources"):
                            self.error(
                                "pool.exception-unsourced",
                                pool.path,
                                f"cutoff.{key} {name}: historical exceptions must cite sources",
                            )
                        else:
                            self._check_sources(list(entry["sources"]), pool.path, None, f"cutoff.{key}")
        else:
            self.error("pool.bad-kind", pool.path, f"kind {pool.kind!r}")
        seen: set[int] = set()
        for card in pool.cards:
            if card.passcode in seen:
                self.error("pool.duplicate-card", pool.path, f"passcode {card.passcode} ({card.name}) listed twice")
            seen.add(card.passcode)
            self._check_card(card.passcode, card.name, pool.path, "pool entry")
            for variant in card.variants:
                if variant in seen:
                    self.error("pool.duplicate-card", pool.path, f"variant passcode {variant} ({card.name}) listed twice")
                seen.add(variant)
                if abs(variant - card.passcode) >= 10:
                    self.error(
                        "pool.variant-out-of-range",
                        pool.path,
                        f"{card.name}: variant {variant} is not within +/-10 of {card.passcode}; "
                        "EDOPro whitelists only extend to alias codes in that range",
                    )
                index_row = self.repo.card_index.by_passcode.get(variant)
                if index_row is not None:
                    alias = index_row.get("alias_of")
                    if not alias or int(alias) != card.passcode:
                        self.error(
                            "pool.variant-alias-mismatch",
                            pool.path,
                            f"{card.name}: variant {variant} does not alias {card.passcode} in the card index",
                        )
        self._check_sources(pool.sources, pool.path, None, "pool")

    def _validate_rule_profiles(self) -> None:
        for profile in self.repo.rule_profiles.values():
            if not _PROFILE_ID_RE.match(profile.id):
                self.error("rules.bad-id", profile.path, f"id {profile.id!r} does not match rules-<slug>")
            if not profile.flags:
                self.error("rules.no-flags", profile.path, "engine.flags is empty")
            for flag in profile.flags:
                if not _FLAG_RE.match(flag):
                    self.error("rules.bad-flag", profile.path, f"flag {flag!r} does not look like a DUEL_* macro")
                if flag.startswith("DUEL_MODE_"):
                    self.error(
                        "rules.composite-flag",
                        profile.path,
                        f"{flag} is a composite mode macro; engine.flags must list individual flags "
                        "(put the macro in engine.preset instead)",
                    )
            self._check_sources(profile.sources, profile.path, None, "rule profile")

    def _validate_errata(self) -> None:
        for erratum in self.repo.errata.values():
            if not _ERRATUM_ID_RE.match(erratum.id):
                self.error("erratum.bad-id", erratum.path, f"id {erratum.id!r} does not match erratum-<slug>")
            if erratum.classification not in CHANGE_KINDS:
                self.error("erratum.bad-classification", erratum.path, f"{erratum.classification!r}")
            self._check_card(
                erratum.modern_card.passcode, erratum.modern_card.name, erratum.path, "erratum modern_card"
            )
            if not erratum.changes:
                self.error("erratum.no-changes", erratum.path, "changes[] is empty")
            max_earlier_start: _dt.date | None = None
            for i, change in enumerate(erratum.changes):
                kind = change.get("kind")
                if kind not in CHANGE_KINDS:
                    self.error("erratum.bad-change-kind", erratum.path, f"changes[{i}].kind {kind!r}")
                bounds = self._validate_effective(erratum, i, change)
                if bounds is not None:
                    earliest, latest = bounds
                    # Definite inversion only: this change certainly finished
                    # taking effect before an earlier change could have begun.
                    # Overlapping uncertainty intervals are legitimate.
                    if (
                        latest is not None
                        and max_earlier_start is not None
                        and latest < max_earlier_start
                    ):
                        self.error(
                            "erratum.changes-out-of-order",
                            erratum.path,
                            f"changes[{i}] took effect by {latest}, before an earlier change "
                            f"could have begun ({max_earlier_start}); changes[] must be "
                            "ordered oldest to newest",
                        )
                    if earliest is not None:
                        max_earlier_start = max(max_earlier_start or earliest, earliest)
                if not change.get("sources"):
                    self.error("erratum.change-unsourced", erratum.path, "a change entry cites no sources")
                else:
                    self._check_sources(change["sources"], erratum.path, None, "erratum change")
                resulting = change.get("resulting_implementation")
                if resulting is not None:
                    if i == len(erratum.changes) - 1:
                        self.error(
                            "erratum.modern-implementation-recorded",
                            erratum.path,
                            f"changes[{i}] is the final change; the version it creates is the "
                            "modern card, implemented by cards.cdb — resulting_implementation "
                            "must not be recorded for it",
                        )
                    self._validate_implementation(erratum, resulting, f"changes[{i}].resulting_implementation")
            self._validate_implementation(erratum, erratum.implementation, "implementation")
            strategy = erratum.implementation.get("strategy")

            # The record's summary classification must equal the dominant
            # change kind, so tools filtering on classification see the truth.
            kinds = [c.get("kind") for c in erratum.changes if c.get("kind") in CHANGE_KINDS]
            if kinds:
                dominant = max(kinds, key=lambda k: KIND_SEVERITY[k])
                if erratum.classification in CHANGE_KINDS and erratum.classification != dominant:
                    self.error(
                        "erratum.classification-mismatch",
                        erratum.path,
                        f"classification {erratum.classification!r} but the dominant change "
                        f"kind is {dominant!r} (severity functional > ruling > engine > cosmetic)",
                    )

            relevant = erratum.relevant_changes()
            if not relevant and strategy in ("reuse-upstream", "custom-script"):
                # Computed selection never substitutes such a record; only an
                # explicit, documented format-level include can (e.g. to stay
                # entry-for-entry identical to an upstream reference list that
                # ships a period-text variant of a behaviourally equal card).
                self.warn(
                    "erratum.no-behavioural-change-with-override",
                    erratum.path,
                    "no functional or ruling change is recorded: cosmetic and engine "
                    "differences never substitute a historical card computationally; "
                    "the recorded implementation is usable only via an explicit "
                    "errata_overrides include (document why in the format notes)",
                )
            if relevant and erratum.classification == "functional" and strategy == "none-needed":
                self.warn(
                    "erratum.functional-none-needed",
                    erratum.path,
                    "a functional text change normally requires a historical implementation; "
                    "none-needed must be a documented, deliberate decision",
                )

            review = erratum.raw.get("review") or {}
            if review and review.get("status") not in ("imported", "reviewed"):
                self.error("erratum.bad-review-status", erratum.path, f"review.status {review.get('status')!r}")
            if erratum.review_status != "reviewed":
                self.warn(
                    "erratum.unreviewed",
                    erratum.path,
                    "record is imported but not yet reviewed; classification and chronology "
                    "are unverified, and formats apply it only via explicit errata_overrides",
                )
            elif relevant and not any(
                (c.get("effective") or {}).get("date")
                or (c.get("effective") or {}).get("old_attested_through")
                or (c.get("effective") or {}).get("new_attested_from")
                for c in relevant
            ):
                self.warn(
                    "erratum.undated",
                    erratum.path,
                    "reviewed, but no behavioural change carries any effective chronology; "
                    "formats whose snapshot could straddle it must adjudicate explicitly",
                )
            self._check_sources(erratum.sources, erratum.path, None, "erratum")

    def _validate_effective(
        self, erratum, index: int, change: dict
    ) -> tuple[_dt.date | None, _dt.date | None] | None:
        """Check one change's effective chronology; returns (earliest, latest)
        possible effect date for ordering checks, or None if malformed."""
        effective = change.get("effective")
        if not isinstance(effective, dict):
            self.error(
                "erratum.no-effective",
                erratum.path,
                f"changes[{index}] has no effective chronology object",
            )
            return None
        date = effective.get("date")
        precision = effective.get("precision")
        status = effective.get("status")
        old_through = self._date(effective.get("old_attested_through"))
        new_from = self._date(effective.get("new_attested_from"))
        if effective.get("old_attested_through") and old_through is None:
            self.error("erratum.bad-date", erratum.path, f"changes[{index}] old_attested_through is not a date")
        if effective.get("new_attested_from") and new_from is None:
            self.error("erratum.bad-date", erratum.path, f"changes[{index}] new_attested_from is not a date")
        if precision is not None and precision not in PRECISIONS:
            self.error("erratum.bad-precision", erratum.path, f"changes[{index}] precision {precision!r}")
            precision = None
        if status is not None and status not in EFFECTIVE_STATUSES:
            self.error("erratum.bad-effective-status", erratum.path, f"changes[{index}] status {status!r}")
        if old_through and new_from and old_through >= new_from:
            self.error(
                "erratum.bounds-inverted",
                erratum.path,
                f"changes[{index}]: old text attested through {old_through} but new text "
                f"attested from {new_from}; the old attestation must precede the new one",
            )
        if date is None:
            if new_from or old_through:
                return (old_through, None) if new_from is None else (old_through, new_from)
            return (None, None)
        if self._date(date) is None:
            self.error("erratum.bad-date", erratum.path, f"changes[{index}] effective.date {date!r}")
            return None
        try:
            lo, hi = _model_precision_bounds(str(date), str(precision or "day"))
        except ValueError:
            self.error("erratum.bad-date", erratum.path, f"changes[{index}] effective.date {date!r}")
            return None
        if old_through and old_through >= hi:
            self.error(
                "erratum.bounds-contradict-date",
                erratum.path,
                f"changes[{index}]: old text attested through {old_through}, but the effective "
                f"date says the new text was in force by {hi}",
            )
        if new_from and new_from < lo:
            self.error(
                "erratum.bounds-contradict-date",
                erratum.path,
                f"changes[{index}]: new text attested from {new_from}, before the earliest "
                f"possible effective date {lo}",
            )
        return (lo, hi)

    def _validate_implementation(self, erratum, impl: dict, what: str) -> None:
        strategy = impl.get("strategy")
        if strategy not in ("none-needed", "reuse-upstream", "custom-script", "unresolved"):
            self.error("erratum.bad-strategy", erratum.path, f"{what}.strategy {strategy!r}")
        if impl.get("status") not in IMPLEMENTATION_STATUSES:
            self.error("erratum.bad-status", erratum.path, f"{what}.status {impl.get('status')!r}")
        if strategy in ("reuse-upstream", "custom-script") and not impl.get("historical_passcode"):
            self.warn(
                "erratum.no-historical-passcode",
                erratum.path,
                f"{what}: strategy {strategy} but no historical_passcode recorded yet",
            )
        hist = impl.get("historical_passcode")
        if hist:
            self._check_card_alias(int(hist), erratum, what)
            for variant in impl.get("historical_variant_passcodes", []) or []:
                if abs(int(variant) - int(hist)) >= 10:
                    self.error(
                        "erratum.variant-out-of-range",
                        erratum.path,
                        f"{what}: variant {variant} is not within +/-10 of {hist}; EDOPro "
                        "treats farther codes as separate cards, not artwork variants",
                    )
                self._check_card_alias(int(variant), erratum, what)

    def _check_card_alias(self, historical_passcode: int, erratum, what: str = "implementation") -> None:
        index = self.repo.card_index
        if not index.by_passcode:
            return
        row = index.by_passcode.get(historical_passcode)
        if row is None:
            self.warn(
                "erratum.historical-passcode-unindexed",
                erratum.path,
                f"{what}: historical passcode {historical_passcode} is not in the card index "
                "(add it via the importer so alias/name can be cross-checked)",
            )
            return
        alias = row.get("alias_of")
        if alias and int(alias) != erratum.modern_card.passcode:
            # Artwork variants alias the base historical code instead of the
            # modern card; those are validated against their base above.
            base = index.by_passcode.get(int(alias))
            base_alias = base.get("alias_of") if base else None
            if not (base_alias and int(base_alias) == erratum.modern_card.passcode):
                self.error(
                    "erratum.alias-mismatch",
                    erratum.path,
                    f"{what}: historical passcode {historical_passcode} aliases {alias}, "
                    f"but modern_card is {erratum.modern_card.passcode}",
                )

    def _validate_format(self, fmt: Format) -> None:
        if not _FORMAT_ID_RE.match(fmt.id):
            self.error("format.bad-id", fmt.path, f"id {fmt.id!r} does not match yyyy-mm-<slug>")
        if fmt.path.parent.name != fmt.id:
            self.error(
                "format.id-dir-mismatch",
                fmt.path,
                f"id {fmt.id!r} but directory is {fmt.path.parent.name!r}",
            )

        start = self._date(fmt.start)
        end = self._date(fmt.end) if fmt.end else None
        snapshot = self._date(fmt.snapshot)
        if start is None:
            self.error("format.bad-date", fmt.path, f"period.start {fmt.start!r}")
        if snapshot is None:
            self.error("format.bad-date", fmt.path, f"period.snapshot {fmt.snapshot!r}")
        if fmt.end is not None and end is None:
            self.error("format.bad-date", fmt.path, f"period.end {fmt.end!r}")
        if start and snapshot and snapshot < start:
            self.error("format.snapshot-before-start", fmt.path, f"snapshot {snapshot} < start {start}")
        if end and snapshot and snapshot > end:
            self.error("format.snapshot-after-end", fmt.path, f"snapshot {snapshot} > end {end}")

        # references
        banlist = self.repo.banlists.get(fmt.banlist_id)
        if banlist is None:
            self.error("format.unresolved-banlist", fmt.path, f"banlist {fmt.banlist_id!r} not found")
        pool = self.repo.pools.get(fmt.pool_id)
        if pool is None:
            self.error("format.unresolved-pool", fmt.path, f"card_pool {fmt.pool_id!r} not found")
        if fmt.rule_profile_id not in self.repo.rule_profiles:
            self.error("format.unresolved-rules", fmt.path, f"rule_profile {fmt.rule_profile_id!r} not found")

        if banlist is not None:
            if banlist.region != fmt.region and banlist.region != "Worldwide":
                self.warn(
                    "format.region-mismatch",
                    fmt.path,
                    f"format region {fmt.region} but banlist {banlist.id} is {banlist.region}",
                )
            eff = self._date(banlist.effective_date)
            if eff and snapshot and not (eff <= snapshot):
                self.error(
                    "format.banlist-not-in-force",
                    fmt.path,
                    f"banlist {banlist.id} took effect {eff}, after the snapshot date {snapshot}",
                )
            superseded = self._date(banlist.raw.get("superseded_by_date"))
            if superseded and snapshot and snapshot >= superseded:
                self.error(
                    "format.banlist-superseded",
                    fmt.path,
                    f"banlist {banlist.id} was superseded on {superseded}, on/before snapshot {snapshot}",
                )

        if banlist is not None and pool is not None and pool.cards:
            pool_codes = pool.passcodes()
            for entry in banlist.entries:
                if entry.status in ("limited", "semilimited") and entry.card.passcode not in pool_codes:
                    self.warn(
                        "format.restricted-card-outside-pool",
                        fmt.path,
                        f"{entry.card.name} is {entry.status} on {banlist.id} but absent from pool {pool.id} "
                        "(fine only if the card genuinely postdates the pool)",
                    )

        # chronology
        for label, ref in (("previous", fmt.previous), ("next", fmt.next)):
            if ref is None:
                continue
            other = self.repo.formats.get(ref)
            if other is None:
                self.warn(
                    "format.unresolved-chronology",
                    fmt.path,
                    f"chronology.{label} {ref!r} is not (yet) a format in this repository",
                )
                continue
            other_start = self._date(other.start)
            if label == "previous" and other_start and start and not (other_start < start):
                self.error(
                    "format.chronology-order",
                    fmt.path,
                    f"previous format {other.id} starts {other_start}, not before {start}",
                )
            if label == "next" and other_start and start and not (start < other_start):
                self.error(
                    "format.chronology-order",
                    fmt.path,
                    f"next format {other.id} starts {other_start}, not after {start}",
                )
            back = other.next if label == "previous" else other.previous
            if back is not None and back != fmt.id:
                self.warn(
                    "format.chronology-asymmetric",
                    fmt.path,
                    f"{other.id}.chronology does not point back at {fmt.id}",
                )

        for component, status in fmt.implementation_status.items():
            if status not in IMPLEMENTATION_STATUSES:
                self.error(
                    "format.bad-implementation-status",
                    fmt.path,
                    f"implementation_status.{component} = {status!r}",
                )

        self._check_sources(fmt.sources, fmt.path, fmt.id, "format")

        # errata references and applicability. Computed selection is fail-safe:
        # a REVIEWED record whose chronology is ambiguous at this snapshot, or
        # whose selected version lacks an implementation, is an ERROR unless
        # the format adjudicates it via errata_overrides. Imported (unreviewed)
        # records apply only via explicit include and are warned about once,
        # in _validate_errata.
        for ref in [*fmt.errata_include, *fmt.errata_exclude]:
            if ref not in self.repo.errata:
                self.error(
                    "format.unresolved-erratum",
                    fmt.path,
                    f"errata_overrides references unknown erratum id {ref!r}",
                )
        if snapshot:
            for erratum in self.repo.errata.values():
                if not erratum.relevant_changes():
                    continue
                excluded = erratum.id in fmt.errata_exclude
                included = erratum.id in fmt.errata_include and not excluded
                if erratum.review_status != "reviewed":
                    if included and erratum.implementation.get("status") in ("missing", "stub"):
                        self.warn(
                            "format.erratum-unimplemented",
                            fmt.path,
                            f"{erratum.modern_card.name}: included but implementation status "
                            f"is {erratum.implementation.get('status')!r}",
                        )
                    continue
                selection = erratum.selection_at(snapshot)
                if excluded:
                    if selection.state == "historical":
                        self.warn(
                            "format.erratum-exclude-contradicts-chronology",
                            fmt.path,
                            f"{erratum.id}: chronology says the historical version applies at "
                            f"{snapshot} but the format excludes it; document the deliberate "
                            "deviation in the format notes",
                        )
                    continue
                if included:
                    if selection.state == "modern" and selection.version_index is not None:
                        self.warn(
                            "format.erratum-include-contradicts-chronology",
                            fmt.path,
                            f"{erratum.id}: chronology says the modern card applies at "
                            f"{snapshot} but the format pins the baseline version; document "
                            "the deliberate deviation in the format notes",
                        )
                    elif selection.state == "historical" and selection.version_index == 0:
                        self.warn(
                            "format.erratum-include-redundant",
                            fmt.path,
                            f"{erratum.id}: computed selection already chooses the baseline "
                            "version; the explicit include can be removed",
                        )
                    elif selection.state == "historical":
                        self.error(
                            "format.erratum-include-wrong-version",
                            fmt.path,
                            f"{erratum.id}: chronology selects version "
                            f"{selection.version_index} at {snapshot}, but an explicit include "
                            "pins the baseline version; remove the include or fix the data",
                        )
                    continue
                if selection.state == "ambiguous":
                    self.error(
                        "format.erratum-ambiguous",
                        fmt.path,
                        f"{erratum.id}: effective chronology is ambiguous at snapshot "
                        f"{snapshot} (changes {list(selection.ambiguous_changes)}); narrow "
                        "the chronology or adjudicate with a documented "
                        "errata_overrides include/exclude — selection will not guess",
                    )
                elif selection.state == "gap":
                    self.error(
                        "format.erratum-implementation-gap",
                        fmt.path,
                        f"{erratum.id}: version {selection.version_index} applies at "
                        f"{snapshot} but has no usable implementation; record one "
                        "(reuse-upstream/custom-script) or exclude with documentation",
                    )
                elif selection.state == "historical" and selection.implementation.get(
                    "status"
                ) in ("missing", "stub"):
                    self.warn(
                        "format.erratum-unimplemented",
                        fmt.path,
                        f"{erratum.modern_card.name}: historical behaviour applies at {snapshot} "
                        f"but implementation status is {selection.implementation.get('status')!r}",
                    )

    def _validate_event(self, event, path: Path, context: str) -> None:
        if event.territory not in TERRITORIES:
            self.error("releases.bad-territory", path, f"{context}: territory {event.territory!r}")
        if event.precision not in PRECISIONS:
            self.error("releases.bad-precision", path, f"{context}: precision {event.precision!r}")
        if event.status not in EVENT_STATUSES:
            self.error("releases.bad-status", path, f"{context}: status {event.status!r}")
        if event.kind not in EVENT_KINDS:
            self.error("releases.bad-event-kind", path, f"{context}: kind {event.kind!r}")
        if self._date(event.date) is None:
            self.error("releases.bad-date", path, f"{context}: date {event.date!r}")
        if event.status == "disputed" and not event.dispute:
            self.error(
                "releases.dispute-missing",
                path,
                f"{context}: status is disputed but no dispute alternatives are recorded",
            )
        if event.dispute and event.status != "disputed":
            self.error(
                "releases.dispute-unexpected",
                path,
                f"{context}: dispute alternatives recorded but status is {event.status!r}",
            )
        for alt in event.dispute:
            if self._date(str(alt.get("date"))) is None:
                self.error("releases.bad-date", path, f"{context}: dispute date {alt.get('date')!r}")
            alt_precision = alt.get("precision")
            if alt_precision is not None and alt_precision not in PRECISIONS:
                # bounds() would otherwise silently read an unknown precision
                # as day-precise - narrowing exactly the uncertainty the
                # dispute records.
                self.error(
                    "releases.bad-precision",
                    path,
                    f"{context}: dispute precision {alt_precision!r}",
                )
            if not alt.get("sources"):
                self.error("releases.unsourced", path, f"{context}: a dispute alternative cites no sources")
            else:
                self._check_sources(list(alt["sources"]), path, None, f"{context} dispute")
        self._check_sources(event.sources, path, None, f"{context} event")

    def _validate_products(self) -> None:
        for product in self.repo.products.values():
            path = product.path
            if not _PRODUCT_ID_RE.match(product.id):
                self.error("releases.bad-id", path, f"product id {product.id!r} is not a slug")
            if not _PRODUCT_CODE_RE.match(product.code):
                self.error("releases.bad-code", path, f"product code {product.code!r}")
            if path.stem != product.id:
                self.error(
                    "releases.id-file-mismatch",
                    path,
                    f"id {product.id!r} but file is {path.name!r}",
                )
            if product.kind not in PRODUCT_KINDS:
                self.error("releases.bad-kind", path, f"kind {product.kind!r}")
            if product.dating not in ("product", "per-printing"):
                self.error("releases.bad-dating", path, f"dating {product.dating!r}")
            if product.dating == "per-printing" and product.events:
                self.error(
                    "releases.dating-conflict",
                    path,
                    "dating=per-printing products must not carry product-level release_events",
                )
            if product.dating == "product" and not product.events:
                self.warn(
                    "releases.undated-product",
                    path,
                    "product has no release events; its printings grant no availability",
                )
            for event in product.events:
                self._validate_event(event, path, f"product {product.code}")
            seen: set[int] = set()
            for printing in product.printings:
                if printing.passcode in seen:
                    self.error(
                        "releases.duplicate-printing",
                        path,
                        f"passcode {printing.passcode} ({printing.name}) printed twice in {product.code}; "
                        "merge the rows (numbers is a list)",
                    )
                seen.add(printing.passcode)
                self._check_card(printing.passcode, printing.name, path, f"printing in {product.code}")
                for number in printing.numbers:
                    if not number.startswith(f"{product.code}-"):
                        self.warn(
                            "releases.number-prefix",
                            path,
                            f"printing number {number!r} does not start with {product.code!r}-",
                        )
                for event in printing.events:
                    self._validate_event(event, path, f"printing {printing.passcode} in {product.code}")
            self._check_sources(product.sources, path, None, f"product {product.code}")

        # A canonical card that was printed but is undated everywhere can never
        # enter a pool - fine for reprints, a research gap for first prints.
        if self.repo.products:
            index = ReleaseIndex.build(self.repo)
            for canonical in sorted(index.by_canonical):
                availability = index.by_canonical[canonical]
                if not availability.events and availability.undated_printings:
                    products = ", ".join(sorted({p for p, _ in availability.undated_printings}))
                    self.warn(
                        "releases.card-undated",
                        f"data/releases/products ({products})",
                        f"passcode {canonical}: every known printing is undated; "
                        "the card cannot enter any release-cutoff pool until one is dated",
                    )

    def _validate_gaps(self) -> None:
        """The gap ledger must be structurally sound, its resolutions must be
        justified - and mechanically verified where possible - and every
        anomaly the importer detected must be accounted for. Certification
        inputs (the import report, the ledger) must themselves be present and
        current whenever anything consumes certification."""
        gaps = self.repo.release_gaps
        coverage = self.repo.release_coverage
        report = self.repo.import_report
        gaps_location = "data/releases/gaps.json"

        # -- certification consumers demand certification inputs -------------
        consumers = bool(
            coverage is not None
            and any(w.get("status") in ("complete", "verified") for w in coverage.windows)
        ) or any(
            p.kind == "release-cutoff" and p.raw.get("cards") for p in self.repo.pools.values()
        )
        if consumers and not report:
            self.error(
                "coverage.no-import-report",
                "data/imported/releases-report.json",
                "coverage claims completeness (or a materialised pool exists) but the "
                "import report is absent - anomaly accounting cannot be checked, so "
                "certification cannot be defended",
            )
        if report:
            # bind the committed report to the committed dataset so a stale or
            # hand-edited report cannot vouch for anomalies it no longer reflects
            stats = report.get("stats", {}) or {}
            generated = sum(1 for p in self.repo.products.values() if not p.raw.get("curated"))
            curated = len(self.repo.products) - generated
            if (
                stats.get("products_written") != generated
                or stats.get("curated_preserved") != curated
            ):
                self.error(
                    "coverage.report-stale",
                    "data/imported/releases-report.json",
                    f"import report stats (written={stats.get('products_written')}, "
                    f"curated={stats.get('curated_preserved')}) do not match the dataset "
                    f"(generated={generated}, curated={curated}); re-run the importer",
                )

        if not gaps and not report and coverage is None:
            return

        mechanical_ok = not self._release_data_has_errors()
        if gaps and not mechanical_ok:
            self.warn(
                "gaps.not-cross-checked",
                gaps_location,
                "resolution recomputation skipped while the release data has structural errors",
            )
        seen_ids: set[str] = set()
        availability_index: ReleaseIndex | None = None

        def canonical(passcode: int) -> int:
            row = self.repo.card_index.by_passcode.get(passcode)
            alias = row.get("alias_of") if row else None
            if alias and abs(int(alias) - passcode) < 10:
                return int(alias)
            return passcode

        def provable_by(passcode: int, day, scope: frozenset[str]):
            """The earliest date the card is PROVABLY available within `scope`
            (min over scoped availability events of each event's latest bound).
            Returns None when nothing proves availability."""
            nonlocal availability_index
            if availability_index is None:
                availability_index = ReleaseIndex.build(self.repo)
            availability = availability_index.by_canonical.get(passcode)
            if not availability:
                return None
            bounds = [
                ref.event.bounds()[1]
                for ref in availability.events
                if territory_matches_scope(ref.event.territory, scope)
            ]
            return min(bounds) if bounds else None

        for gap in gaps:
            path = gap.path
            if not _GAP_ID_RE.match(gap.id):
                self.error("gaps.bad-id", path, f"gap id {gap.id!r}")
            if gap.id in seen_ids:
                self.error("gaps.duplicate-id", path, f"gap id {gap.id!r} appears twice")
            seen_ids.add(gap.id)
            if gap.kind not in GAP_KINDS:
                self.error("gaps.bad-kind", path, f"{gap.id}: kind {gap.kind!r}")
            if gap.status not in GAP_STATUSES:
                self.error("gaps.bad-status", path, f"{gap.id}: status {gap.status!r}")
            if gap.impact not in GAP_IMPACTS:
                self.error("gaps.bad-impact", path, f"{gap.id}: impact {gap.impact!r}")
            elif gap.kind in ("missing-product-printings", "unmatched-cards", "undated-availability") and gap.impact != "pool-membership":
                self.error(
                    "gaps.bad-impact",
                    path,
                    f"{gap.id}: kind {gap.kind} is a pool-membership question by definition; "
                    "impact provenance-only would let the anomaly bypass certification unexamined",
                )
            if not gap.subjects:
                self.error("gaps.no-subjects", path, f"{gap.id}: subjects[] is empty")
            if not gap.territories:
                self.error(
                    "gaps.no-territories",
                    path,
                    f"{gap.id}: territories[] is empty (blocks() treats this as everywhere, "
                    "but the record must say where the gap applies)",
                )
            for territory in gap.territories:
                if territory not in TERRITORIES:
                    self.error("gaps.bad-territory", path, f"{gap.id}: territory {territory!r}")
            if gap.date_precision not in PRECISIONS:
                self.error("gaps.bad-precision", path, f"{gap.id}: date_precision {gap.date_precision!r}")
            if self._date(gap.possible_from) is None:
                self.error("gaps.bad-date", path, f"{gap.id}: possible_from {gap.possible_from!r}")
            self._check_sources(gap.sources, path, None, f"gap {gap.id}")

            if gap.status == "unresolved":
                if gap.resolution:
                    self.error(
                        "gaps.resolution-unexpected",
                        path,
                        f"{gap.id}: unresolved gaps must not carry a resolution",
                    )
                continue

            # resolved-*: the claim must be justified and, where possible, proven.
            resolution = gap.resolution or {}
            rationale = resolution.get("rationale")
            if rationale not in GAP_RATIONALES:
                self.error("gaps.bad-rationale", path, f"{gap.id}: resolution.rationale {rationale!r}")
                continue
            if not resolution.get("detail"):
                self.error("gaps.unjustified", path, f"{gap.id}: resolution.detail is required")
            if not resolution.get("sources"):
                self.error("gaps.unjustified", path, f"{gap.id}: resolution.sources is required")
            else:
                self._check_sources(list(resolution["sources"]), path, None, f"gap {gap.id} resolution")

            gap_start = gap.earliest_possible()
            gap_scope = frozenset(gap.territories) if gap.territories else frozenset(TERRITORIES)

            if gap.status == "resolved-imported" or rationale == "roster-imported":
                product_id = resolution.get("product")
                product = self.repo.products.get(str(product_id))
                if product is None:
                    self.error(
                        "gaps.import-missing",
                        path,
                        f"{gap.id}: resolution.product {product_id!r} is not a product in the dataset",
                    )
                elif not product.printings:
                    self.error(
                        "gaps.import-missing",
                        path,
                        f"{gap.id}: resolution.product {product_id!r} has no printings",
                    )
                else:
                    # the recovering product must BE the gap's subject, not just
                    # any product that happens to exist
                    subject_norms = {normalise_name(s) for s in gap.subjects}
                    if normalise_name(product.name) not in subject_norms:
                        self.error(
                            "gaps.import-mismatch",
                            path,
                            f"{gap.id}: resolution.product {product_id!r} ({product.name!r}) "
                            "does not match any gap subject",
                        )
                    dated = [
                        e for e in product.events
                        if e.kind in AVAILABILITY_KINDS
                        and self._date(e.date) is not None
                        and territory_matches_scope(e.territory, gap_scope)
                    ]
                    if not dated:
                        self.error(
                            "gaps.import-missing",
                            path,
                            f"{gap.id}: resolution.product {product_id!r} grants no dated "
                            "availability in the gap's territories",
                        )

            if rationale == "repackaging-only":
                rebundled = resolution.get("products") or []
                if not rebundled:
                    self.error(
                        "gaps.unjustified",
                        path,
                        f"{gap.id}: repackaging-only requires resolution.products",
                    )
                for product_id in rebundled:
                    product = self.repo.products.get(str(product_id))
                    if product is None:
                        self.error(
                            "gaps.import-missing",
                            path,
                            f"{gap.id}: repackaged product {product_id!r} is not in the dataset",
                        )
                        continue
                    if not mechanical_ok or gap_start is None:
                        continue
                    # a bundle cannot precede its contents: each rebundled
                    # product must provably be at retail by the gap's earliest
                    # possible date, in the gap's territories
                    try:
                        bounds = [
                            e.bounds()[1]
                            for e in product.events
                            if e.kind in AVAILABILITY_KINDS
                            and territory_matches_scope(e.territory, gap_scope)
                        ]
                    except ValueError:
                        bounds = []
                    earliest = min(bounds) if bounds else None
                    if earliest is None or earliest > gap_start:
                        self.error(
                            "gaps.not-harmless",
                            path,
                            f"{gap.id}: rebundled product {product_id!r} is not provably at "
                            f"retail by {gap_start} in {sorted(gap_scope)}; a bundle cannot "
                            "precede its contents, so either the gap window or the product "
                            "dates are wrong",
                        )

            if rationale == "cards-available-earlier":
                cards = resolution.get("cards") or []
                if not cards:
                    self.error(
                        "gaps.unjustified",
                        path,
                        f"{gap.id}: cards-available-earlier requires resolution.cards",
                    )
                if gap_start is None or not mechanical_ok:
                    continue  # bad-date / structural errors already reported
                for card in cards:
                    try:
                        raw_passcode = int(card.get("passcode"))
                    except (TypeError, ValueError):
                        self.error("gaps.unjustified", path, f"{gap.id}: bad card entry {card!r}")
                        continue
                    self._check_card(raw_passcode, str(card.get("name", "")), path, f"gap {gap.id} card")
                    passcode = canonical(raw_passcode)
                    try:
                        earliest = provable_by(passcode, gap_start, gap_scope)
                    except ValueError:
                        earliest = None
                    # The card must PROVABLY be available by the gap's earliest
                    # possible date IN THE GAP'S TERRITORIES - availability
                    # elsewhere cannot make a territory-scoped pool whole.
                    if earliest is None or earliest > gap_start:
                        self.error(
                            "gaps.not-harmless",
                            path,
                            f"{gap.id}: {card.get('name')} ({passcode}) is not provably available "
                            f"by {gap_start} in {sorted(gap_scope)} through the dataset; "
                            "the gap could alter a pool",
                        )

        # -- accounting: nothing the importer detected may go unrecorded -----
        if report:
            accounted: set[str] = set()
            for gap in gaps:
                accounted.update(gap.subjects)
            for key, label in (
                ("yugipedia_only_products", "product"),
                ("products_without_printings", "product"),
                ("curated_covered_products", "curated-covered product"),
            ):
                for subject in report.get(key, []):
                    if subject not in accounted:
                        self.error(
                            "gaps.unaccounted",
                            gaps_location,
                            f"import report lists {label} {subject!r} ({key}) "
                            "but no gap record accounts for it",
                        )
            for card in report.get("unmatched_cards", []):
                subject = str(card.get("name", ""))
                if subject not in accounted:
                    self.error(
                        "gaps.unaccounted",
                        gaps_location,
                        f"import report lists unmatched card {subject!r} "
                        "but no gap record accounts for it",
                    )

        # -- claims: a complete/verified window must not overlap an
        #    unresolved pool-impacting gap ---------------------------------
        if coverage is not None:
            for i, window in enumerate(coverage.windows):
                if window.get("status") not in ("complete", "verified"):
                    continue
                end = self._date(str(window.get("through")))
                if end is None:
                    continue  # coverage.bad-window already reported
                window_scope = frozenset(window.get("territories", []))
                for gap in gaps:
                    if gap.blocks(end, window_scope):
                        self.error(
                            "coverage.gap-unresolved",
                            coverage.path,
                            f"window {i} claims {window.get('status')!r} coverage through "
                            f"{window.get('through')} but gap {gap.id} "
                            f"({gap.subjects[0] if gap.subjects else gap.kind}) is unresolved "
                            "and could alter availability inside it",
                        )

    def _validate_coverage(self) -> None:
        coverage = self.repo.release_coverage
        if coverage is None:
            return
        for i, window in enumerate(coverage.windows):
            start = self._date(str(window.get("from")))
            end = self._date(str(window.get("through")))
            if start is None or end is None or start > end:
                self.error(
                    "coverage.bad-window",
                    coverage.path,
                    f"window {i}: from {window.get('from')!r} through {window.get('through')!r}",
                )
            for t in window.get("territories", []):
                if t not in TERRITORIES:
                    self.error("coverage.bad-territory", coverage.path, f"window {i}: {t!r}")
            if window.get("status") not in IMPLEMENTATION_STATUSES:
                self.error("coverage.bad-window", coverage.path, f"window {i}: status {window.get('status')!r}")
        self._check_sources(coverage.sources, coverage.path, None, "release coverage")

    def _release_data_has_errors(self) -> bool:
        """Structural errors that would make derivation crash or mislead.

        Only releases.* (malformed events feed bounds()) and load.* gate the
        materialised-pool cross-check; gap/coverage findings are judgements
        over structurally sound data and must not suppress pool checks."""
        return any(
            f.severity == ERROR and f.code.startswith(("releases.", "load."))
            for f in self.findings
        )

    def _validate_materialized_pools(self) -> None:
        """A release-cutoff pool with cards committed must be exactly what the
        release dataset derives - materialisation is a projection, not data."""
        if self._release_data_has_errors():
            # Derivation assumes structurally valid release data; evaluating
            # over broken records would crash or mislead. The structural
            # errors above already fail validation.
            self.warn(
                "pool.not-cross-checked",
                "data/pools",
                "materialised pools were not recomputed because the release "
                "dataset has structural errors (fix those first)",
            )
            return
        index = None
        for pool in self.repo.pools.values():
            if pool.kind != "release-cutoff" or not pool.raw.get("cards"):
                continue
            if not self._date((pool.cutoff or {}).get("cutoff_date")):
                continue  # pool.bad-cutoff already reported
            cutoff = _dt.date.fromisoformat(str(pool.cutoff["cutoff_date"]))
            scope = frozenset(pool.cutoff.get("territories") or default_scope(pool.region))
            coverage = self.repo.release_coverage
            if coverage is None or not coverage.covers(cutoff, scope, self.repo.release_gaps):
                self.error(
                    "pool.no-coverage",
                    pool.path,
                    f"pool is materialised but coverage of {sorted(scope)} through {cutoff} "
                    "cannot be certified (no claimed-complete window, or an unresolved "
                    "pool-impacting gap overlaps it)",
                )
            if index is None:
                index = ReleaseIndex.build(self.repo)
            try:
                evaluation = evaluate_cutoff(pool, self.repo, index)
            except (ValueError, TypeError, KeyError) as exc:
                # e.g. a malformed cutoff exception entry; the specific defect
                # is reported by _validate_pool - this keeps the contract that
                # validate() returns findings instead of raising.
                self.error(
                    "pool.evaluation-failed",
                    pool.path,
                    f"could not recompute the pool from release data: {exc}",
                )
                continue
            for code in sorted(evaluation.ambiguous):
                refs = evaluation.ambiguous[code]
                spans = "; ".join(
                    f"{r.product_id} {r.event.date} ({r.event.precision}/{r.event.status})"
                    for r in refs[:3]
                )
                self.error(
                    "pool.cutoff-ambiguous",
                    pool.path,
                    f"passcode {code}: possible release dates straddle the cutoff ({spans}); "
                    "resolve with a sourced cutoff.include/exclude entry",
                )
            committed = {c.passcode: c for c in pool.cards}
            computed = {c["passcode"]: c for c in evaluation.cards()}
            for code in sorted(computed.keys() - committed.keys())[:20]:
                self.error(
                    "pool.materialization-drift",
                    pool.path,
                    f"release data derives {code} ({computed[code]['name']}) but the committed pool lacks it; "
                    "run: python -m retroformats materialize",
                )
            for code in sorted(committed.keys() - computed.keys())[:20]:
                self.error(
                    "pool.materialization-drift",
                    pool.path,
                    f"committed pool contains {code} ({committed[code].name}) but release data does not derive it; "
                    "run: python -m retroformats materialize",
                )
            for code in sorted(committed.keys() & computed.keys()):
                have = sorted(committed[code].variants)
                want = sorted(computed[code].get("variant_passcodes", []))
                if have != want:
                    self.error(
                        "pool.materialization-drift",
                        pool.path,
                        f"passcode {code}: committed variants {have} != derived {want}; "
                        "run: python -m retroformats materialize",
                    )

    # -- entry point -----------------------------------------------------

    def validate(self) -> list[Finding]:
        for exc in self.repo.load_errors:
            self.error("load.failed", exc.path, exc.message)
        if not self.repo.card_index.by_passcode:
            self.warn(
                "card.index-missing",
                "data/cards/index.json",
                "card index absent or empty; passcode/name cross-checks skipped",
            )
        for banlist in self.repo.banlists.values():
            self._validate_banlist(banlist)
        for pool in self.repo.pools.values():
            self._validate_pool(pool)
        self._validate_rule_profiles()
        self._validate_errata()
        for fmt in self.repo.formats.values():
            self._validate_format(fmt)
        self._validate_products()
        self._validate_coverage()
        self._validate_gaps()
        self._validate_materialized_pools()
        return self.findings

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == WARNING]
