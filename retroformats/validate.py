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
    IMPLEMENTATION_STATUSES,
    STATUS_TO_COUNT,
    Banlist,
    Format,
    Pool,
)
from .repo import Repository

ERROR = "ERROR"
WARNING = "WARNING"

_FORMAT_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[a-z0-9-]+$")
_BANLIST_ID_RE = re.compile(r"^(tcg|ocg|ww)-[0-9]{4}-[0-9]{2}$")
_POOL_ID_RE = re.compile(r"^pool-[a-z0-9-]+$")
_PROFILE_ID_RE = re.compile(r"^rules-[a-z0-9-]+$")
_ERRATUM_ID_RE = re.compile(r"^erratum-[a-z0-9-]+$")
_FLAG_RE = re.compile(r"^DUEL_[A-Z0-9_]+$")


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
        if pool.kind == "extensional":
            if not pool.cards:
                self.error("pool.empty", pool.path, "extensional pool has no cards")
        elif pool.kind == "release-cutoff":
            if not pool.cutoff or not self._date((pool.cutoff or {}).get("cutoff_date")):
                self.error("pool.bad-cutoff", pool.path, "release-cutoff pool needs cutoff.cutoff_date")
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
            if erratum.classification not in ("functional", "cosmetic", "ruling", "engine"):
                self.error("erratum.bad-classification", erratum.path, f"{erratum.classification!r}")
            self._check_card(
                erratum.modern_card.passcode, erratum.modern_card.name, erratum.path, "erratum modern_card"
            )
            if not erratum.changes:
                self.error("erratum.no-changes", erratum.path, "changes[] is empty")
            for change in erratum.changes:
                eff = change.get("date_effective")
                if eff is not None and self._date(eff) is None:
                    self.error("erratum.bad-date", erratum.path, f"date_effective {eff!r} is not a valid date")
                if not change.get("sources"):
                    self.error("erratum.change-unsourced", erratum.path, "a change entry cites no sources")
                else:
                    self._check_sources(change["sources"], erratum.path, None, "erratum change")
            impl = erratum.implementation
            strategy = impl.get("strategy")
            if strategy not in ("none-needed", "reuse-upstream", "custom-script", "unresolved"):
                self.error("erratum.bad-strategy", erratum.path, f"implementation.strategy {strategy!r}")
            if impl.get("status") not in IMPLEMENTATION_STATUSES:
                self.error("erratum.bad-status", erratum.path, f"implementation.status {impl.get('status')!r}")
            if strategy in ("reuse-upstream", "custom-script") and not impl.get("historical_passcode"):
                self.warn(
                    "erratum.no-historical-passcode",
                    erratum.path,
                    f"strategy {strategy} but no historical_passcode recorded yet",
                )
            hist = impl.get("historical_passcode")
            if hist:
                self._check_card_alias(int(hist), erratum)
            if erratum.classification == "cosmetic" and strategy not in ("none-needed", "unresolved"):
                self.warn(
                    "erratum.cosmetic-with-override",
                    erratum.path,
                    "cosmetic errata should not need a historical implementation",
                )
            if erratum.classification in ("functional", "ruling") and not any(
                c.get("date_effective") for c in erratum.changes
            ):
                self.warn(
                    "erratum.undated",
                    erratum.path,
                    "no change has a date_effective; per-format applicability relies on "
                    "explicit errata_overrides.include until the date is researched",
                )
            self._check_sources(erratum.sources, erratum.path, None, "erratum")

    def _check_card_alias(self, historical_passcode: int, erratum) -> None:
        index = self.repo.card_index
        if not index.by_passcode:
            return
        row = index.by_passcode.get(historical_passcode)
        if row is None:
            self.warn(
                "erratum.historical-passcode-unindexed",
                erratum.path,
                f"historical passcode {historical_passcode} is not in the card index "
                "(add it via the importer so alias/name can be cross-checked)",
            )
            return
        alias = row.get("alias_of")
        if alias and int(alias) != erratum.modern_card.passcode:
            self.error(
                "erratum.alias-mismatch",
                erratum.path,
                f"historical passcode {historical_passcode} aliases {alias}, "
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

        if banlist is not None and pool is not None and pool.kind == "extensional":
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

        # errata references and applicability: a functional erratum whose modern
        # behaviour began after this snapshot means this format needs the
        # historical version. Undated errata are reported once, in _validate_errata.
        for ref in [*fmt.errata_include, *fmt.errata_exclude]:
            if ref not in self.repo.errata:
                self.error(
                    "format.unresolved-erratum",
                    fmt.path,
                    f"errata_overrides references unknown erratum id {ref!r}",
                )
        if snapshot:
            for erratum in self.repo.errata.values():
                if erratum.classification not in ("functional", "ruling"):
                    continue
                if erratum.id in fmt.errata_exclude:
                    continue
                applies = erratum.historical_behaviour_applies_on(snapshot)
                if applies is None:
                    applies = erratum.id in fmt.errata_include
                if applies and erratum.implementation.get("status") in ("missing", "stub"):
                    self.warn(
                        "format.erratum-unimplemented",
                        fmt.path,
                        f"{erratum.modern_card.name}: historical behaviour applies at {snapshot} "
                        f"but implementation status is {erratum.implementation.get('status')!r}",
                    )

    def _validate_releases(self) -> None:
        for release_file in self.repo.releases:
            raw = release_file["raw"]
            path = release_file["path"]
            seen: set[str] = set()
            for product in raw.get("products", []):
                code = product.get("code", "")
                if code in seen:
                    self.error("releases.duplicate-code", path, f"product code {code!r} listed twice")
                seen.add(code)
                if self._date(product.get("release_date")) is None:
                    self.error("releases.bad-date", path, f"{code}: release_date {product.get('release_date')!r}")
                if not product.get("sources"):
                    self.error("releases.unsourced", path, f"product {code!r} cites no sources")

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
        self._validate_releases()
        return self.findings

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == WARNING]
