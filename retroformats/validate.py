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
    COVERAGE_FIELDS,
    CHANGE_KINDS,
    CONTRADICTED,
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
    PROVEN,
    PRODUCT_KINDS,
    REGION_SCOPE_BITS,
    RESERVED_PASSCODE_RANGE,
    STATUS_TO_COUNT,
    TERRITORIES,
    Banlist,
    Coverage,
    ErratumV2,
    Format,
    Pool,
    SelectionError,
    normalise_name,
    ordering_proof,
    territory_matches_scope,
)
from .model import _precision_bounds as _model_precision_bounds
from .model import _is_valid_passcode
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
        if passcode in RESERVED_PASSCODE_RANGE:
            self.error(
                "card.reserved-passcode-collision",
                location,
                f"{context}: passcode {passcode} ({name!r}) falls inside this project's own "
                "reserved range (retroformats/model.py's RESERVED_PASSCODE_RANGE, "
                "600000000-699999999) - nothing in canonical data may use it yet; see "
                "docs/roadmap.md item 7",
            )
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
        if basis is None:
            self.error(
                "pool.missing-legality-basis",
                pool.path,
                "legality_basis is not set - a pool must declare what it CLAIMS to be "
                "(availability / historical-policy / community-retrospective), see "
                "schemas/pool.schema.json",
            )
        elif basis not in ("availability", "historical-policy", "community-retrospective"):
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
                for entry in pool.cutoff.get("region_substitutions", []):
                    if (
                        not isinstance(entry, dict)
                        or not isinstance(entry.get("from"), dict)
                        or not isinstance(entry.get("to"), dict)
                    ):
                        self.error("pool.bad-exception", pool.path, f"cutoff.region_substitutions entry {entry!r}")
                        continue
                    try:
                        from_code = int(entry["from"]["passcode"])
                        from_name = str(entry["from"]["name"])
                        to_code = int(entry["to"]["passcode"])
                        to_name = str(entry["to"]["name"])
                    except (TypeError, ValueError, KeyError):
                        self.error("pool.bad-exception", pool.path, f"cutoff.region_substitutions entry {entry!r}")
                        continue
                    self._check_card(from_code, from_name, pool.path, "cutoff.region_substitutions.from")
                    self._check_card(to_code, to_name, pool.path, "cutoff.region_substitutions.to")
                    if from_code == to_code:
                        self.error(
                            "pool.bad-exception",
                            pool.path,
                            f"cutoff.region_substitutions {to_name}: from and to are the same passcode",
                        )
                    if not entry.get("reason"):
                        self.error(
                            "pool.exception-unreasoned",
                            pool.path,
                            f"cutoff.region_substitutions {to_name}: historical exceptions must state a reason",
                        )
                    if not entry.get("sources"):
                        self.error(
                            "pool.exception-unsourced",
                            pool.path,
                            f"cutoff.region_substitutions {to_name}: historical exceptions must cite sources",
                        )
                    else:
                        self._check_sources(list(entry["sources"]), pool.path, None, "cutoff.region_substitutions")
        else:
            self.error("pool.bad-kind", pool.path, f"kind {pool.kind!r}")
        seen: set[int] = set()
        region_bit = REGION_SCOPE_BITS.get(pool.region)
        for card in pool.cards:
            if card.passcode in seen:
                self.error("pool.duplicate-card", pool.path, f"passcode {card.passcode} ({card.name}) listed twice")
            seen.add(card.passcode)
            self._check_card(card.passcode, card.name, pool.path, "pool entry")
            if region_bit is not None:
                row = self.repo.card_index.by_passcode.get(card.passcode)
                ot = row.get("ot") if row else None
                if ot is not None and not (int(ot) & region_bit):
                    self.error(
                        "pool.card-region-scope-mismatch",
                        pool.path,
                        f"{card.name}: passcode {card.passcode} (ot={ot}) is not scoped for {pool.region} - "
                        "an EDOPro official-cards room would reject it; if BabelCDB ships a differently-scoped "
                        "sibling for this printing, add a sourced cutoff.region_substitutions entry",
                    )
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
            if isinstance(erratum, ErratumV2):
                self._validate_erratum_v2(erratum)
                continue
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
            if erratum.classification == "engine" and strategy in (
                "reuse-upstream",
                "custom-script",
            ):
                # engine means "a rule profile reproduces this, not a card
                # override". Carrying a historical card implementation
                # contradicts that: the record is claiming both routes at
                # once, and computed selection will use neither.
                self.warn(
                    "erratum.engine-with-card-implementation",
                    erratum.path,
                    "classification engine says a rule profile reproduces this, but the "
                    f"record carries a {strategy} card implementation that computed "
                    "selection can never use; if the difference is only reproducible "
                    "per card (e.g. a per-effect damage-step flag no DUEL_* flag sets), "
                    "classify it ruling instead",
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

    # -- v2 (historical-event DAG) record checks --------------------------
    # docs/research/erratum-state-model-v2.md, frozen. A dedicated branch,
    # not a v1 changes[] fabrication: v2 has no changes[]/implementation at
    # all. Covers the design doc's ten §10 invariants plus the same
    # general-record checks v1 gets, adapted to events{}/transitions[].
    # Invariants 1-2 (real event ids, no ordering cycles) are already
    # enforced at ErratumV2.load() time — a malformed record never survives
    # loading, and surfaces as a load.failed finding via repo.load_errors
    # (see validate()) rather than being silently dropped.

    def _validate_erratum_v2(self, erratum: ErratumV2) -> None:
        if not _ERRATUM_ID_RE.match(erratum.id):
            self.error("erratum.bad-id", erratum.path, f"id {erratum.id!r} does not match erratum-<slug>")
        if erratum.classification not in CHANGE_KINDS:
            self.error("erratum.bad-classification", erratum.path, f"{erratum.classification!r}")
        self._check_card(
            erratum.modern_card.passcode, erratum.modern_card.name, erratum.path, "erratum modern_card"
        )
        if not erratum.events:
            self.error("erratum.no-events", erratum.path, "events{} is empty")

        dominant_kinds: list[str] = []
        for event_id, event in erratum.events.items():
            dominant_kinds.extend(self._validate_v2_event(erratum, event_id, event))

        if dominant_kinds:
            dominant = max(dominant_kinds, key=lambda k: KIND_SEVERITY[k])
            if erratum.classification in CHANGE_KINDS and erratum.classification != dominant:
                self.error(
                    "erratum.classification-mismatch",
                    erratum.path,
                    f"classification {erratum.classification!r} but the dominant transition "
                    f"kind is {dominant!r} (severity functional > ruling > engine > cosmetic)",
                )

        self._validate_v2_shape(erratum)
        self._validate_v2_ordering(erratum)
        self._validate_v2_states(erratum)
        self._validate_v2_implementation_metadata(erratum)
        self._validate_v2_reference_identities(erratum)

        review = erratum.raw.get("review") or {}
        if review and review.get("status") not in ("imported", "reviewed"):
            self.error("erratum.bad-review-status", erratum.path, f"review.status {review.get('status')!r}")
        relevant = erratum.relevant_events()
        # Ported from the v1 check of the same name (final-gate correction
        # 1): a functional text change normally requires a historical
        # implementation, so a NONE_NEEDED baseline is a data-quality smell
        # worth flagging as a documented, deliberate decision rather than
        # an oversight. `state_for(frozenset())` reads the AUTHORED
        # baseline coverage here, never the synthesised-MODERN terminal
        # branch: that branch only fires when frozenset() == all_relevant_
        # ids, i.e. zero relevant events, which `relevant` already rules
        # out - so this can never warn about a record whose baseline IS
        # the terminal/modern state.
        if (
            relevant
            and erratum.classification == "functional"
            and erratum.state_for(frozenset()).coverage.kind == Coverage.NONE_NEEDED
        ):
            self.warn(
                "erratum.functional-none-needed",
                erratum.path,
                "a functional text change normally requires a historical implementation; "
                "none-needed must be a documented, deliberate decision",
            )
        if erratum.review_status != "reviewed":
            self.warn(
                "erratum.unreviewed",
                erratum.path,
                "record is imported but not yet reviewed; classification and chronology "
                "are unverified, and formats apply it only via explicit errata_overrides",
            )
        elif relevant and not any(
            e.effective.get("date")
            or e.effective.get("old_attested_through")
            or e.effective.get("new_attested_from")
            for e in relevant
        ):
            self.warn(
                "erratum.undated",
                erratum.path,
                "reviewed, but no behavioural event carries any effective chronology; "
                "formats whose snapshot could straddle it must adjudicate explicitly",
            )
        self._check_sources(erratum.sources, erratum.path, None, "erratum")

    def _validate_v2_event(self, erratum: ErratumV2, event_id: str, event) -> list[str]:
        """One event's chronology and transitions; returns its transitions'
        kinds for the record's dominant-classification check. Invariant 10
        (co-occurrence sources) lives here: a 2+-transition event is a
        first-class co-occurrence claim needing its own evidence, never
        inferred from the individual transitions' own sources."""
        self._validate_v2_effective(erratum, event_id, event.effective)
        if len(event.transitions) >= 2:
            sources = event.cooccurrence_sources
            if not sources:
                self.error(
                    "erratum.cooccurrence-unsourced",
                    erratum.path,
                    f"events.{event_id}: {len(event.transitions)} transitions but no "
                    "cooccurrence_sources — 2+ transitions in one event is a co-occurrence "
                    "claim needing its own evidence, not merely each transition's own sources",
                )
            else:
                self._check_sources(list(sources), erratum.path, None, f"events.{event_id} cooccurrence")
        kinds: list[str] = []
        if not event.transitions:
            self.error("erratum.event-no-transitions", erratum.path, f"events.{event_id}: transitions[] is empty")
        for i, transition in enumerate(event.transitions):
            if transition.kind not in CHANGE_KINDS:
                self.error(
                    "erratum.bad-change-kind",
                    erratum.path,
                    f"events.{event_id}.transitions[{i}].kind {transition.kind!r}",
                )
            else:
                kinds.append(transition.kind)
            if not transition.sources:
                self.error(
                    "erratum.change-unsourced", erratum.path, f"events.{event_id}.transitions[{i}] cites no sources"
                )
            else:
                self._check_sources(
                    list(transition.sources), erratum.path, None, f"events.{event_id}.transitions[{i}]"
                )
        return kinds

    def _validate_v2_effective(self, erratum: ErratumV2, event_id: str, effective: dict) -> None:
        """The same effective-chronology soundness checks v1's changes[]
        get (date/precision/status/corroboration/bounds), scoped to one v2
        event's own `effective` block instead of one v1 change's."""
        date = effective.get("date")
        precision = effective.get("precision")
        status = effective.get("status")
        old_through = self._date(effective.get("old_attested_through"))
        new_from = self._date(effective.get("new_attested_from"))
        if effective.get("old_attested_through") and old_through is None:
            self.error("erratum.bad-date", erratum.path, f"events.{event_id} old_attested_through is not a date")
        if effective.get("new_attested_from") and new_from is None:
            self.error("erratum.bad-date", erratum.path, f"events.{event_id} new_attested_from is not a date")
        if precision is not None and precision not in PRECISIONS:
            self.error("erratum.bad-precision", erratum.path, f"events.{event_id} precision {precision!r}")
            precision = None
        if status is not None and status not in EFFECTIVE_STATUSES:
            self.error("erratum.bad-effective-status", erratum.path, f"events.{event_id} status {status!r}")
        corroboration = effective.get("corroboration") or []
        if status == "verified" and not corroboration:
            self.error(
                "erratum.unverified-verified",
                erratum.path,
                f"events.{event_id} claims status 'verified' but records no corroboration; "
                "cite the period/primary source (url + quoted sentence) or use 'reported'",
            )
        for item in corroboration:
            if not item.get("url") or not item.get("quote"):
                self.error(
                    "erratum.bad-corroboration",
                    erratum.path,
                    f"events.{event_id} corroboration entry needs a url and a quoted sentence",
                )
        if old_through and new_from and old_through >= new_from:
            self.error(
                "erratum.bounds-inverted",
                erratum.path,
                f"events.{event_id}: old attested through {old_through} but new attested from "
                f"{new_from}; the old attestation must precede the new one",
            )
        if date is None:
            return
        if self._date(date) is None:
            self.error("erratum.bad-date", erratum.path, f"events.{event_id} effective.date {date!r}")
            return
        try:
            lo, hi = _model_precision_bounds(str(date), str(precision or "day"))
        except ValueError:
            self.error("erratum.bad-date", erratum.path, f"events.{event_id} effective.date {date!r}")
            return
        if old_through and old_through >= hi:
            self.error(
                "erratum.bounds-contradict-date",
                erratum.path,
                f"events.{event_id}: old attested through {old_through}, but the effective "
                f"date says the new behaviour was in force by {hi}",
            )
        if new_from and new_from < lo:
            self.error(
                "erratum.bounds-contradict-date",
                erratum.path,
                f"events.{event_id}: new attested from {new_from}, before the earliest "
                f"possible effective date {lo}",
            )

    def _safe_ordering_proof(
        self, erratum: ErratumV2, before_id: str, after_id: str, before_eff: dict, after_eff: dict
    ) -> str | None:
        """`ordering_proof()` over chronology that `_validate_v2_effective`
        may already have reported as malformed. A bad date must produce a
        finding and let validation continue, never an uncaught ValueError
        out of the whole run - the record is being validated precisely
        BECAUSE it might be broken."""
        try:
            return ordering_proof(before_eff, after_eff)
        except (ValueError, TypeError) as exc:
            self.error(
                "erratum.ordering-uncheckable",
                erratum.path,
                f"ordering edge {before_id!r} -> {after_id!r} cannot be checked: one of the "
                f"events has malformed chronology ({exc})",
            )
            return None

    def _validate_v2_shape(self, erratum: ErratumV2) -> None:
        """Raw-shape guarantees the JSON Schema states but `Repository.load()`
        never runs: it parses raw JSON directly, so anything the schema alone
        enforces is unenforced in production until it is also checked here.

        Each of these is a case where the parser's own normalisation would
        otherwise make malformed data indistinguishable from valid data."""
        raw = erratum.raw
        # A. `states[].events` is a SET. frozenset() silently collapses a
        # repeated id, so ["e1","e1"] would parse as {"e1"} and validate as
        # if the author had written a different, well-formed document.
        for index, entry in enumerate(raw.get("states") or []):
            ids = entry.get("events")
            if not isinstance(ids, list):
                continue
            seen: set[str] = set()
            for event_id in ids:
                if event_id in seen:
                    self.error(
                        "erratum.state-events-duplicate",
                        erratum.path,
                        f"states[{index}].events repeats {event_id!r}; a state's events are a "
                        "SET of ids, and a repeated member is malformed rather than a second "
                        "encoding of the same set",
                    )
                seen.add(event_id)
        # A2. The same repeated-id check for implementation_metadata[].events
        # - an independent array, but its `events` field is the same kind of
        # set-shaped id list and has the same frozenset()-collapse hazard.
        for index, entry in enumerate(raw.get("implementation_metadata") or []):
            ids = entry.get("events")
            if not isinstance(ids, list):
                continue
            seen_meta: set[str] = set()
            for event_id in ids:
                if event_id in seen_meta:
                    self.error(
                        "erratum.metadata-events-duplicate",
                        erratum.path,
                        f"implementation_metadata[{index}].events repeats {event_id!r}; an "
                        "entry's events are a SET of ids, and a repeated member is malformed "
                        "rather than a second encoding of the same set",
                    )
                seen_meta.add(event_id)
        # B. Full v2 must author `ordering` explicitly, even as `{}` - saying
        # "these events have no known order" is a claim, and its absence is
        # an omission. Sugar has no authored ordering by construction.
        if erratum.authored_shape == "full" and "ordering" not in raw:
            self.error(
                "erratum.missing-ordering",
                erratum.path,
                "full v2 records must state `ordering` explicitly, even when empty ({}): "
                "an absent ordering block is an omission, not an assertion that no order "
                "is known",
            )
        # C. An event's chronology must exist as a shape. A missing
        # `effective`, or an `effective` with no `date` key at all, parses to
        # exactly the same permanently-AMBIGUOUS behaviour as an explicit
        # `"date": null` - so silence would masquerade as a researched
        # "chronology unknown" claim.
        for event_id, event_raw in (raw.get("events") or {}).items():
            if not isinstance(event_raw, dict):
                continue
            if "effective" not in event_raw:
                self.error(
                    "erratum.event-missing-effective",
                    erratum.path,
                    f"events[{event_id!r}] has no `effective` block; explicit unknown "
                    'chronology is written {"date": null}, never omitted',
                )
                continue
            effective = event_raw.get("effective")
            if not isinstance(effective, dict) or "date" not in effective:
                self.error(
                    "erratum.event-missing-effective",
                    erratum.path,
                    f"events[{event_id!r}].effective has no `date` key; explicit unknown "
                    'chronology is written {"date": null}, never omitted',
                )

    def _validate_v2_ordering(self, erratum: ErratumV2) -> None:
        """Invariants 6-7: every declared ordering constraint — chain-
        desugared pairs AND explicit edges alike, never only literal
        `ordering.edges` entries, since a chain is sugar over edges, not a
        way to bypass the same proof burden — must pass the PROVEN/
        CONTRADICTED chronology test, and anything not PROVEN must carry
        an explicit, resolvable evidentiary basis (design doc §5, §10)."""
        for chain in erratum.raw_chains:
            for before_id, after_id in zip(chain, chain[1:]):
                before_event = erratum.events.get(before_id)
                after_event = erratum.events.get(after_id)
                if before_event is None or after_event is None:
                    continue  # dangling reference already a load.failed finding
                proof = self._safe_ordering_proof(
                    erratum, before_id, after_id, before_event.effective, after_event.effective
                )
                if proof is None:
                    continue
                if proof == CONTRADICTED:
                    self.error(
                        "erratum.ordering-contradicted",
                        erratum.path,
                        f"ordering.chains edge {before_id!r} -> {after_id!r} is CONTRADICTED "
                        "by chronology under every possible date assignment",
                    )
                elif proof != PROVEN:
                    self.error(
                        "erratum.ordering-chain-not-proven",
                        erratum.path,
                        f"ordering.chains edge {before_id!r} -> {after_id!r} is not PROVEN by "
                        "chronology alone (chains sugar always requires basis 'date-proven'); "
                        "use an explicit ordering.edges entry with a justified basis instead",
                    )
        for edge in erratum.raw_edges:
            before_id, after_id, basis = edge.get("before"), edge.get("after"), edge.get("basis")
            before_event = erratum.events.get(before_id)
            after_event = erratum.events.get(after_id)
            if before_event is None or after_event is None:
                continue  # dangling reference already a load.failed finding
            proof = self._safe_ordering_proof(
                erratum, before_id, after_id, before_event.effective, after_event.effective
            )
            if proof is None:
                continue
            if proof == CONTRADICTED:
                self.error(
                    "erratum.ordering-contradicted",
                    erratum.path,
                    f"ordering.edges edge {before_id!r} -> {after_id!r} (basis {basis!r}) is "
                    "CONTRADICTED by chronology regardless of its claimed basis",
                )
                continue
            if basis == "date-proven":
                if proof != PROVEN:
                    self.error(
                        "erratum.ordering-basis-unproven",
                        erratum.path,
                        f"ordering.edges edge {before_id!r} -> {after_id!r} claims basis "
                        "'date-proven' but chronology does not prove it",
                    )
            elif basis in ("directly-sourced", "researcher-inference"):
                if not edge.get("note"):
                    self.error(
                        "erratum.ordering-edge-unjustified",
                        erratum.path,
                        f"ordering.edges edge {before_id!r} -> {after_id!r} (basis {basis!r}) "
                        "needs an explanatory note",
                    )
                sources = edge.get("sources") or []
                if basis == "directly-sourced" and not sources:
                    self.error(
                        "erratum.ordering-edge-unjustified",
                        erratum.path,
                        f"ordering.edges edge {before_id!r} -> {after_id!r}: basis "
                        "'directly-sourced' needs sources citing what states the order",
                    )
                elif sources:
                    self._check_sources(
                        list(sources), erratum.path, None, f"ordering edge {before_id}->{after_id}"
                    )
            else:
                self.error(
                    "erratum.ordering-bad-basis",
                    erratum.path,
                    f"ordering.edges edge {before_id!r} -> {after_id!r}: basis {basis!r}",
                )

    def _validate_v2_states(self, erratum: ErratumV2) -> None:
        """Invariants 3-5 (and 8, which the design document's own text
        shows is the same underlying defect as 3 — one check, not two
        noisy findings): authored `states[]` keys, read from the RAW array
        (ErratumV2.authored_states is already a dict and would have
        silently collapsed a duplicate before this ever ran) — every key
        must reference real, implementation-relevant event ids and be a
        structurally reachable down-set; no two entries may share a
        semantic (frozenset) key even if their JSON arrays differ
        textually; MODERN is legal only for the terminal (all-relevant-
        events) state, and a terminal entry, if authored at all, must say
        MODERN."""
        relevant_ids = frozenset(e.id for e in erratum.relevant_events())
        reachable = set(erratum.structural_states())
        seen_keys: set[frozenset[str]] = set()
        for i, entry in enumerate(erratum.raw.get("states") or []):
            raw_event_ids = entry.get("events") or []
            ids = frozenset(raw_event_ids)
            location = f"states[{i}]"

            unknown = [e for e in raw_event_ids if e not in erratum.events]
            if unknown:
                self.error(
                    "erratum.state-unknown-event", erratum.path, f"{location}: unknown event id(s) {unknown}"
                )
                continue
            non_relevant = [e for e in raw_event_ids if not erratum.events[e].is_implementation_relevant]
            if non_relevant:
                self.error(
                    "erratum.state-non-relevant-event",
                    erratum.path,
                    f"{location}: cosmetic/engine-only event id(s) {non_relevant} cannot "
                    "appear in an implementation-state key",
                )
                continue
            if ids in seen_keys:
                self.error(
                    "erratum.state-duplicate-key",
                    erratum.path,
                    f"{location}: semantic key {sorted(ids)} duplicates an earlier states[] "
                    "entry (array spelling differs but the event-set is the same)",
                )
            seen_keys.add(ids)
            if ids not in reachable:
                self.error(
                    "erratum.state-unreachable",
                    erratum.path,
                    f"{location}: down-set {sorted(ids)} is not structurally reachable from "
                    "the declared events{}/ordering",
                )
                continue
            coverage_raw = entry.get("coverage") or {}
            is_terminal = ids == relevant_ids
            if is_terminal and coverage_raw.get("kind") != "modern":
                self.error(
                    "erratum.terminal-not-modern",
                    erratum.path,
                    f"{location}: the all-events state must be coverage.kind 'modern' if "
                    f"authored at all; found {coverage_raw.get('kind')!r}",
                )
            elif not is_terminal and coverage_raw.get("kind") == "modern":
                self.error(
                    "erratum.non-terminal-modern",
                    erratum.path,
                    f"{location}: coverage.kind 'modern' is only valid for the all-events "
                    f"state; {sorted(ids)} is not it",
                )
            self._validate_v2_coverage(erratum, location, coverage_raw)

    def _validate_v2_implementation_metadata(self, erratum: ErratumV2) -> None:
        """`implementation_metadata[]` (representation-gaps.md, task
        section 2): deliberately INDEPENDENT of `_validate_v2_states()` -
        this checks only that an AUTHORED entry is well-formed, never that
        every state also has metadata or vice versa. A state may legitimately
        have coverage with no metadata, metadata with no (or mechanically-
        UNRESOLVED) coverage, or both; only a malformed entry is an error,
        never a cross-array absence (task section 10)."""
        reachable = set(erratum.structural_states())
        seen_keys: set[frozenset[str]] = set()
        for i, entry in enumerate(erratum.raw.get("implementation_metadata") or []):
            raw_event_ids = entry.get("events") or []
            ids = frozenset(raw_event_ids)
            location = f"implementation_metadata[{i}]"

            unknown = [e for e in raw_event_ids if e not in erratum.events]
            if unknown:
                self.error(
                    "erratum.metadata-unknown-event",
                    erratum.path,
                    f"{location}: unknown event id(s) {unknown}",
                )
                continue
            non_relevant = [e for e in raw_event_ids if not erratum.events[e].is_implementation_relevant]
            if non_relevant:
                self.error(
                    "erratum.metadata-non-relevant-event",
                    erratum.path,
                    f"{location}: cosmetic/engine-only event id(s) {non_relevant} cannot "
                    "appear in an implementation-metadata key",
                )
                continue
            if ids in seen_keys:
                self.error(
                    "erratum.metadata-duplicate-key",
                    erratum.path,
                    f"{location}: semantic key {sorted(ids)} duplicates an earlier "
                    "implementation_metadata[] entry (array spelling differs but the "
                    "event-set is the same)",
                )
            seen_keys.add(ids)
            if ids not in reachable:
                self.error(
                    "erratum.metadata-unreachable",
                    erratum.path,
                    f"{location}: down-set {sorted(ids)} is not structurally reachable from "
                    "the declared events{}/ordering",
                )
                continue
            payload_keys = set(entry) - {"events"}
            if not payload_keys:
                self.error(
                    "erratum.metadata-empty",
                    erratum.path,
                    f"{location}: no metadata fields besides `events` - this entry records "
                    "nothing",
                )
                continue
            if "status" in entry and entry.get("status") not in IMPLEMENTATION_STATUSES:
                self.error(
                    "erratum.metadata-bad-status",
                    erratum.path,
                    f"{location}: status {entry.get('status')!r}",
                )
            if "tested" in entry and not isinstance(entry.get("tested"), bool):
                self.error(
                    "erratum.metadata-bad-type",
                    erratum.path,
                    f"{location}: tested must be a boolean",
                )
            if "reason" in entry and not (isinstance(entry.get("reason"), str) and entry.get("reason")):
                self.error(
                    "erratum.metadata-bad-type",
                    erratum.path,
                    f"{location}: reason must be a non-empty string",
                )
            gap = entry.get("gap")
            if "gap" in entry:
                if not isinstance(gap, dict) or not gap:
                    self.error(
                        "erratum.metadata-bad-gap",
                        erratum.path,
                        f"{location}.gap: must be a non-empty object",
                    )
                else:
                    if "upstream_checked" in gap and not isinstance(gap.get("upstream_checked"), bool):
                        self.error(
                            "erratum.metadata-bad-type",
                            erratum.path,
                            f"{location}.gap: upstream_checked must be a boolean",
                        )
                    if "behavioural_impact" in gap and not (
                        isinstance(gap.get("behavioural_impact"), str) and gap.get("behavioural_impact")
                    ):
                        self.error(
                            "erratum.metadata-bad-type",
                            erratum.path,
                            f"{location}.gap: behavioural_impact must be a non-empty string",
                        )

    def _validate_v2_reference_identities(self, erratum: ErratumV2) -> None:
        """`reference_identities[]` (representation-gaps.md, task section
        3/6): unique `reference_id` per record; `provenance_source`
        resolves through the source registry AND appears in this record's
        own `sources`; strict passcode/variant validation (the same
        authority Coverage uses); the +/-10 artwork-variant rule; card
        alias points back to the modern card; `historical_passcode` must
        not equal `modern_card.passcode` (if the reference uses the modern
        card, no entry is necessary at all)."""
        seen_reference_ids: set[str] = set()
        for i, identity in enumerate(erratum.reference_identities):
            location = f"reference_identities[{i}]"
            # Raw primitive types FIRST. Production validation never runs the
            # JSON Schema (Repository.load parses raw JSON; the schema checker
            # lives in tests), and ReferenceIdentity.from_raw() coerces
            # reference_id/provenance_source through str() - so a
            # schema-invalid value would otherwise arrive here already looking
            # like a valid string and pass every check below it. This closes
            # that specific coercion hole rather than reimplementing the
            # schema: the semantic checks that follow are unchanged.
            raw_identity = identity.raw or {}
            for field_name, required in (
                ("reference_id", True),
                ("provenance_source", True),
                ("upstream", True),
                ("script", False),
            ):
                if field_name not in raw_identity:
                    continue  # genuinely absent: required-ness is enforced below
                # Explicit null is NOT treated as absence here (it used to
                # be skipped, the same hole `historical_variant_passcodes`
                # had): reference_id/provenance_source coerce through
                # str(None) == "None" downstream, a truthy-looking value
                # that would otherwise sail past every "missing" check as
                # if the author had genuinely named their reference "None".
                value = raw_identity[field_name]
                if not isinstance(value, str) or not value.strip():
                    self.error(
                        "erratum.reference-identity-malformed-field",
                        erratum.path,
                        f"{location}.{field_name}: expected a non-empty string, got "
                        f"{value!r} ({type(value).__name__})",
                    )
            if "historical_variant_passcodes" in raw_identity:
                variants_raw = raw_identity["historical_variant_passcodes"]
                if not isinstance(variants_raw, list):
                    self.error(
                        "erratum.reference-identity-malformed-field",
                        erratum.path,
                        f"{location}.historical_variant_passcodes: expected an array, got "
                        f"{variants_raw!r} ({type(variants_raw).__name__})",
                    )
            if not identity.reference_id:
                self.error(
                    "erratum.reference-identity-missing-id",
                    erratum.path,
                    f"{location}: reference_id is required",
                )
                continue
            if identity.reference_id in seen_reference_ids:
                self.error(
                    "erratum.reference-identity-duplicate-id",
                    erratum.path,
                    f"{location}: reference_id {identity.reference_id!r} duplicates an "
                    "earlier reference_identities[] entry",
                )
            seen_reference_ids.add(identity.reference_id)

            if not identity.provenance_source:
                self.error(
                    "erratum.reference-identity-missing-provenance",
                    erratum.path,
                    f"{location}: provenance_source is required",
                )
            else:
                if self.repo.resolve_source(identity.provenance_source, None) is None:
                    self.error(
                        "sources.unresolved",
                        erratum.path,
                        f"{location}: cites unknown source id {identity.provenance_source!r}",
                    )
                if identity.provenance_source not in erratum.sources:
                    self.error(
                        "erratum.reference-identity-provenance-not-in-sources",
                        erratum.path,
                        f"{location}: provenance_source {identity.provenance_source!r} is not "
                        "in this record's own `sources`",
                    )

            hist = identity.historical_passcode
            if hist is None:
                self.error(
                    "erratum.no-historical-passcode",
                    erratum.path,
                    f"{location}: historical_passcode is required",
                )
            else:
                hist_int = self._safe_passcode(hist, erratum, location, "historical_passcode")
                if hist_int is not None:
                    if hist_int == erratum.modern_card.passcode:
                        self.error(
                            "erratum.reference-identity-matches-modern",
                            erratum.path,
                            f"{location}: historical_passcode equals modern_card.passcode "
                            f"({hist_int}) - if the reference uses the modern card, no "
                            "reference_identities entry is necessary",
                        )
                    self._check_card_alias(hist_int, erratum, location)
                for variant in identity.historical_variant_passcodes:
                    variant_int = self._safe_passcode(
                        variant, erratum, location, "historical_variant_passcodes entry"
                    )
                    if variant_int is None or hist_int is None:
                        continue
                    if abs(variant_int - hist_int) >= 10:
                        self.error(
                            "erratum.variant-out-of-range",
                            erratum.path,
                            f"{location}: variant {variant} is not within +/-10 of {hist}",
                        )
                    self._check_card_alias(variant_int, erratum, location)

            if not identity.upstream:
                self.error(
                    "erratum.reference-identity-missing-upstream",
                    erratum.path,
                    f"{location}: upstream is required",
                )

    def _validate_v2_coverage(self, erratum: ErratumV2, location: str, coverage: dict) -> None:
        """Invariant 16 (of this task's numbering): semantic coverage
        validation the schema also constrains structurally, but the
        production validator must not assume ran — Repository.load()
        parses raw JSON directly, the schema checker lives in tests."""
        kind = coverage.get("kind")
        if kind == "unresolved":
            self.error(
                "erratum.coverage-unresolved-authored",
                erratum.path,
                f"{location}.coverage: 'unresolved' must never be authored — it is "
                "exclusively the mechanical default for an unauthored reachable state",
            )
            return
        if kind in ("reuse-upstream", "custom-script"):
            hist = coverage.get("historical_passcode")
            if hist is None:
                # Absent or explicit null: genuinely nothing recorded yet.
                # Distinct from PRESENT-but-invalid (0, a bool, a string, an
                # out-of-range value) - `not hist` would treat 0 identically
                # to missing and never reach `_safe_passcode()`'s ERROR.
                self.error(
                    "erratum.no-historical-passcode",
                    erratum.path,
                    f"{location}.coverage: strategy {kind} but no historical_passcode",
                )
            else:
                hist_int = self._safe_passcode(hist, erratum, f"{location}.coverage", "historical_passcode")
                if hist_int is not None:
                    self._check_card_alias(hist_int, erratum, f"{location}.coverage")
                for variant in coverage.get("historical_variant_passcodes", []) or []:
                    variant_int = self._safe_passcode(
                        variant, erratum, f"{location}.coverage", "historical_variant_passcodes entry"
                    )
                    if variant_int is None or hist_int is None:
                        continue
                    if abs(variant_int - hist_int) >= 10:
                        self.error(
                            "erratum.variant-out-of-range",
                            erratum.path,
                            f"{location}.coverage: variant {variant} is not within +/-10 of {hist}",
                        )
                    self._check_card_alias(variant_int, erratum, f"{location}.coverage")
            if kind == "reuse-upstream" and not coverage.get("upstream"):
                self.error(
                    "erratum.no-upstream",
                    erratum.path,
                    f"{location}.coverage: strategy reuse-upstream but no upstream recorded",
                )
            if kind == "custom-script" and not coverage.get("script"):
                self.error(
                    "erratum.no-script",
                    erratum.path,
                    f"{location}.coverage: strategy custom-script but no script recorded",
                )
        elif kind == "known-gap":
            if not coverage.get("gap_reason"):
                self.error("erratum.gap-unjustified", erratum.path, f"{location}.coverage: gap_reason is required")
            if not coverage.get("gap_sources"):
                self.error("erratum.gap-unjustified", erratum.path, f"{location}.coverage: gap_sources is required")
            else:
                self._check_sources(list(coverage["gap_sources"]), erratum.path, None, f"{location}.coverage gap")
        elif kind not in ("none-needed", "modern"):
            self.error("erratum.bad-strategy", erratum.path, f"{location}.coverage: kind {kind!r}")
        # The coverage sum type is CLOSED: each kind allows exactly the fields
        # its schema branch allows (all of which are additionalProperties:
        # false). A payload carrying another kind's fields - known-gap with a
        # historical_passcode, none-needed with a script, modern with either -
        # is materially incompatible data, not harmless extra detail, and the
        # production validator must reject it even though it never runs the
        # schema. COVERAGE_FIELDS is the single shared authority.
        fields = COVERAGE_FIELDS.get(str(kind))
        if fields is not None:
            _required, allowed = fields
            for field in sorted(set(coverage) - allowed):
                self.error(
                    "erratum.coverage-incompatible-field",
                    erratum.path,
                    f"{location}.coverage: kind {kind!r} does not allow field {field!r} "
                    "(the coverage sum type is closed per kind)",
                )

    # -- v2 format-applicability checks (invariant 9 + §§6-8 of this task) -
    # Mirror the v1 per-format loops in SHAPE (exclude/include/parity/
    # chronology), never in mechanism — v2 has no numeric version, so each
    # branch is re-derived from event-set semantics, matching exactly what
    # lflist.py's _select_v2_override actually computes (so a record that
    # validates cleanly here never surprises the builder).

    def _validate_v2_parity(self, erratum: ErratumV2, fmt: Format, snapshot: _dt.date) -> None:
        from .lflist import ReferenceIdentity, _usable_v2, resolve_v2_parity

        # Frozen precedence (task section 2, matching lflist._select_v2_override
        # exactly): exclude wins, then include, and ONLY THEN does parity
        # govern. Both are adjudications belonging to _validate_v2_applicability
        # - an explicitly included card BUILDS from baseline/chronology
        # semantics (never from parity), so it must be ANALYSED that way too,
        # not have parity diagnostics run against a resolution the builder
        # never actually uses for this card. Zero-relevant-event (parity-only)
        # records are never excluded/included by definition in the current
        # corpus, but the check is unconditional so it stays correct if that
        # ever changes.
        if erratum.id in fmt.errata_exclude:
            return  # handled by _validate_v2_applicability
        if erratum.id in fmt.errata_include:
            return  # handled by _validate_v2_applicability - include pins baseline, not parity
        all_relevant_ids = frozenset(e.id for e in erratum.relevant_events())
        # ONE shared primitive with the builder, so the two cannot disagree
        # about precedence: the exact reference_identities[] lookup happens
        # BEFORE the provenance-membership gate, and a matching-but-unusable
        # entry is reported here rather than silently downgraded to the walk.
        problems: list[str] = []
        resolution = resolve_v2_parity(erratum, fmt.reference_parity, problems)
        for problem in problems:
            self.error("erratum.reference-identity-invalid", fmt.path, problem)
        if resolution.outside_reference:
            # Outside the reference: our own research may still say a
            # historical state applies here. Parity keeps the modern card,
            # but the finding is worth surfacing as a candidate contribution
            # back to the reference.
            if erratum.has_implementation_relevant_history():
                try:
                    selection = erratum.selection_at(snapshot)
                except SelectionError:
                    # A genuinely contradictory record — _validate_v2_ordering
                    # (run once per record, unconditionally, before any format
                    # is checked) has already reported the underlying
                    # CONTRADICTED edge; this is not a second, independent
                    # defect to name, only a consequence of the first.
                    return
                # Shadow-migration gate (task section 8) found this check
                # firing on 43 records it never used to under v1: comparing
                # the candidate's EVENT-SET identity against all_relevant_ids
                # is not the same question v1 asked. v1's own selection_at()
                # deliberately reports state="modern", not "historical", for
                # a non-terminal version whose coverage strategy is
                # `none-needed` (model.py: "a documented decision that the
                # modern implementation stands in for this version") - a
                # non-terminal state can legitimately behave exactly like
                # modern, and warning about it here is a false positive, not
                # a real chronology/reference disagreement. `_usable_v2()`
                # mirrors v1's exact historical-vs-modern-vs-gap rule (only
                # REUSE_UPSTREAM/CUSTOM_SCRIPT with a usable passcode count),
                # so the two can no longer disagree about which candidates
                # this warning describes.
                if selection.chronology == "determinate" and _usable_v2(selection.candidates[0].coverage) is not None:
                    self.warn(
                        "format.parity-omits-historical",
                        fmt.path,
                        f"{erratum.modern_card.name}: this record's chronology says a "
                        f"historical state applies at {snapshot}, but the reference "
                        "implementation does not substitute this card, so parity keeps "
                        "the modern one",
                    )
            return
        override = resolution.override
        if override is None:
            return
        if erratum.review_status != "reviewed":
            return
        if not erratum.has_implementation_relevant_history():
            via = (
                "an authored reference_identities[] entry"
                if isinstance(override, ReferenceIdentity)
                else "reference parity"
            )
            self.warn(
                "format.parity-substitutes-non-behavioural",
                fmt.path,
                f"{erratum.modern_card.name}: {via} substitutes the upstream "
                f"variant, but the record finds no functional or ruling transition "
                f"({erratum.classification}) - the reference ships it for period text, "
                "not behaviour",
            )
            return
        try:
            selection = erratum.selection_at(snapshot)
        except SelectionError:
            return  # already reported by _validate_v2_ordering; see above
        if selection.chronology == "determinate" and selection.candidates[0].events == all_relevant_ids:
            self.warn(
                "format.parity-contradicts-chronology",
                fmt.path,
                f"{erratum.modern_card.name}: reference parity substitutes the upstream "
                f"variant, but this record's chronology says the modern state was already "
                f"in force at {snapshot}",
            )

    def _validate_v2_applicability(self, erratum: ErratumV2, fmt: Format, snapshot: _dt.date) -> None:
        if not erratum.has_implementation_relevant_history():
            return
        excluded = erratum.id in fmt.errata_exclude
        included = erratum.id in fmt.errata_include and not excluded
        if fmt.reference_parity and not excluded and not included:
            # Frozen precedence (task section 2): exclude and include are
            # adjudications that outrank parity, so a card carrying either
            # is analysed HERE with the same include/baseline-coverage and
            # chronology diagnostics a non-parity format gets - never with
            # parity diagnostics for a resolution the builder does not
            # actually use for this card. A card that is neither is parity's
            # to govern and to report on (_validate_v2_parity).
            return
        all_relevant_ids = frozenset(e.id for e in erratum.relevant_events())
        if erratum.review_status != "reviewed":
            if included and erratum.state_for(frozenset()).coverage.kind == Coverage.UNRESOLVED:
                self.warn(
                    "format.erratum-unimplemented",
                    fmt.path,
                    f"{erratum.modern_card.name}: included but baseline implementation "
                    "coverage is unresolved",
                )
            return
        try:
            selection = erratum.selection_at(snapshot)
        except SelectionError:
            return  # already reported by _validate_v2_ordering; see _validate_v2_parity
        if excluded:
            # An exclude always keeps modern. The question worth reporting is
            # whether the evidence says modern is WRONG here - and that is a
            # property of the candidate set, not of determinacy: an ambiguous
            # selection whose candidates all exclude the modern state is just
            # as deliberate a contradiction as a determinate historical one,
            # and used to go entirely unreported.
            if not selection.modern_is_possible:
                if selection.chronology == "determinate":
                    detail = f"chronology says a historical state applies at {snapshot}"
                else:
                    detail = (
                        f"chronology at {snapshot} is ambiguous between states "
                        f"{[sorted(c.events) for c in selection.candidates]}, none of which is "
                        "the modern state"
                    )
                self.warn(
                    "format.erratum-exclude-contradicts-chronology",
                    fmt.path,
                    f"{erratum.id}: {detail} but the format excludes it, keeping the modern "
                    "card; document the deliberate deviation in the format notes",
                )
            return
        if included:
            baseline_coverage = erratum.state_for(frozenset()).coverage
            # First: what the pin can actually deliver, independent of chronology.
            if baseline_coverage.kind == Coverage.UNRESOLVED:
                self.error(
                    "format.erratum-include-unresolved-coverage",
                    fmt.path,
                    f"{erratum.id}: explicitly included, but the baseline state's "
                    "implementation coverage is unresolved; an include asserts WHICH state "
                    "applies, never that an unknown implementation may be ignored - record "
                    "coverage, document a known-gap, or drop the include",
                )
            elif baseline_coverage.kind == Coverage.KNOWN_GAP:
                self.warn(
                    "format.erratum-known-divergence",
                    fmt.path,
                    f"{erratum.modern_card.name}: explicitly included, but the baseline state "
                    f"is not reproducible ({baseline_coverage.gap_reason}); the modern "
                    "implementation is used and the divergence is acknowledged on the record",
                )
            elif (
                baseline_coverage.kind in (Coverage.REUSE_UPSTREAM, Coverage.CUSTOM_SCRIPT)
                and baseline_coverage.historical_passcode is None
            ):
                self.error(
                    "format.erratum-include-unresolved-coverage",
                    fmt.path,
                    f"{erratum.id}: explicitly included, and its baseline declares coverage "
                    f"{baseline_coverage.kind.value}, but records no historical_passcode; "
                    "there is no identity to substitute",
                )
            # Second: whether chronology agrees baseline is the state to pin.
            baseline_plausible = any(c.events == frozenset() for c in selection.candidates)
            if selection.chronology == "determinate" and selection.candidates[0].events == all_relevant_ids:
                self.warn(
                    "format.erratum-include-contradicts-chronology",
                    fmt.path,
                    f"{erratum.id}: chronology says the modern state applies at {snapshot} "
                    "but the format pins the baseline state; document the deliberate "
                    "deviation in the format notes",
                )
            elif selection.chronology == "determinate" and selection.candidates[0].events == frozenset():
                self.warn(
                    "format.erratum-include-redundant",
                    fmt.path,
                    f"{erratum.id}: computed selection already chooses the baseline state; "
                    "the explicit include can be removed",
                )
            elif selection.chronology == "determinate":
                self.error(
                    "format.erratum-include-wrong-version",
                    fmt.path,
                    f"{erratum.id}: chronology selects state "
                    f"{sorted(selection.candidates[0].events)} at {snapshot}, but an explicit "
                    "include pins the baseline state; remove the include or fix the data",
                )
            elif not baseline_plausible:
                # Ambiguous, but baseline is not among the states the evidence
                # allows at all: the include is contradicted just as squarely
                # as in the determinate case, and this used to be silent.
                self.error(
                    "format.erratum-include-wrong-version",
                    fmt.path,
                    f"{erratum.id}: chronology at {snapshot} is ambiguous between states "
                    f"{[sorted(c.events) for c in selection.candidates]}, and the baseline "
                    "state is not among them, but an explicit include pins the baseline; "
                    "remove the include or fix the data",
                )
            # Ambiguous WITH baseline plausible: the include is exactly the
            # documented adjudication the ambiguity calls for - no finding.
            return
        if fmt.reference_parity:
            # Neither excluded nor included, under a parity format: parity
            # governs this card's selection (never unresolved_policy, which
            # the builder's parity branch never consults), and
            # _validate_v2_parity reports its own diagnostics for it.
            return
        if selection.chronology == "ambiguous":
            policy = fmt.unresolved_policy or {}
            choice = policy.get("choice")
            if choice == "modern":
                if not selection.modern_is_possible:
                    self.warn(
                        "format.erratum-modern-known-wrong",
                        fmt.path,
                        f"{erratum.modern_card.name}: chronology is ambiguous at {snapshot} "
                        f"between states {[sorted(c.events) for c in selection.candidates]}, "
                        "and the modern state is NOT among them - the unresolved_policy "
                        "fallback to modern is a known divergence, not a neutral default",
                    )
                else:
                    self.warn(
                        "format.erratum-unresolved-defaulted",
                        fmt.path,
                        f"{erratum.modern_card.name}: chronology ambiguous at {snapshot}; "
                        "resolved as 'modern' by this format's documented unresolved_policy",
                    )
            elif choice == "historical":
                self._validate_v2_historical_policy(erratum, fmt, snapshot, selection, all_relevant_ids)
            else:
                self.error(
                    "format.erratum-ambiguous",
                    fmt.path,
                    f"{erratum.id}: effective chronology is ambiguous at snapshot {snapshot} "
                    f"(events {sorted(erratum.events.keys())}); narrow the chronology, "
                    "adjudicate with a documented errata_overrides include/exclude, or state "
                    "an errata_overrides.unresolved_policy — selection will not guess",
                )
        elif selection.chronology == "determinate":
            candidate = selection.candidates[0]
            if candidate.events == all_relevant_ids:
                return  # modern, nothing to report
            coverage = candidate.coverage
            if coverage.kind == Coverage.KNOWN_GAP:
                self.warn(
                    "format.erratum-known-divergence",
                    fmt.path,
                    f"{erratum.modern_card.name}: state {sorted(candidate.events)} applies at "
                    f"{snapshot} but is not reproducible ({coverage.gap_reason}); the modern "
                    "implementation is used and the divergence is acknowledged on the record",
                )
            elif coverage.kind == Coverage.UNRESOLVED:
                self.error(
                    "format.erratum-implementation-gap",
                    fmt.path,
                    f"{erratum.id}: state {sorted(candidate.events)} applies at {snapshot} but "
                    "has no usable implementation coverage and the record does not acknowledge "
                    "the gap; record one (reuse-upstream/custom-script), document a "
                    "known-gap, or exclude with documentation",
                )

    def _validate_v2_historical_policy(
        self,
        erratum: ErratumV2,
        fmt: Format,
        snapshot: _dt.date,
        selection,
        all_relevant_ids: frozenset[str],
    ) -> None:
        """unresolved_policy 'historical' for v2 (design doc §7 of this
        task): only ever resolvable when every plausible non-modern
        candidate agrees on ONE concrete executable outcome — never "the
        smallest state," never "baseline merely because it exists," never
        candidates[0]. Reuses lflist.py's own agreement check
        (`_executable_outcome`) so a record that validates cleanly here is
        guaranteed to resolve identically at build time."""
        from .lflist import _executable_outcome

        non_modern = [c for c in selection.candidates if c.events != all_relevant_ids]
        outcomes = [_executable_outcome(c.coverage) for c in non_modern]
        if None in outcomes or len(set(outcomes)) != 1:
            self.error(
                "format.erratum-historical-policy-unresolved",
                fmt.path,
                f"{erratum.modern_card.name}: chronology ambiguous at {snapshot} between "
                f"states {[sorted(c.events) for c in selection.candidates]}, and "
                "unresolved_policy 'historical' cannot resolve to one concrete executable "
                "outcome - the plausible non-modern candidates disagree, or one has no "
                "usable coverage; adjudicate this card explicitly with errata_overrides",
            )
        else:
            self.warn(
                "format.erratum-unresolved-defaulted",
                fmt.path,
                f"{erratum.modern_card.name}: chronology ambiguous at {snapshot}; resolved "
                "as 'historical' by this format's documented unresolved_policy",
            )

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
        corroboration = effective.get("corroboration") or []
        if status == "verified" and not corroboration:
            # "verified" is earned by recorded, checkable corroboration - not
            # by a reviewer's confidence.
            self.error(
                "erratum.unverified-verified",
                erratum.path,
                f"changes[{index}] claims status 'verified' but records no corroboration; "
                "cite the period/primary source (url + quoted sentence) or use 'reported'",
            )
        for item in corroboration:
            if not item.get("url") or not item.get("quote"):
                self.error(
                    "erratum.bad-corroboration",
                    erratum.path,
                    f"changes[{index}] corroboration entry needs a url and a quoted sentence",
                )
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
        hist_missing = impl.get("historical_passcode") is None
        if strategy in ("reuse-upstream", "custom-script") and hist_missing:
            # Absent or explicit null only - a PRESENT but invalid value
            # (0, a bool, a string, an out-of-range value) is not "not
            # recorded yet", it is malformed data, and gets the ERROR below
            # via `_safe_passcode()` instead of this WARN.
            self.warn(
                "erratum.no-historical-passcode",
                erratum.path,
                f"{what}: strategy {strategy} but no historical_passcode recorded yet",
            )
        gap = impl.get("gap")
        if gap is not None:
            if strategy != "unresolved":
                self.error(
                    "erratum.gap-with-implementation",
                    erratum.path,
                    f"{what}: implementation.gap acknowledges an unreproducible version, "
                    f"but strategy is {strategy!r}; a gap belongs on strategy 'unresolved'",
                )
            if not gap.get("reason"):
                self.error("erratum.gap-unjustified", erratum.path, f"{what}: gap.reason is required")
            if not gap.get("sources"):
                self.error("erratum.gap-unjustified", erratum.path, f"{what}: gap.sources is required")
            else:
                self._check_sources(list(gap["sources"]), erratum.path, None, f"{what} gap")
        hist = impl.get("historical_passcode")
        if not hist_missing:
            hist_int = self._safe_passcode(hist, erratum, what, "historical_passcode")
            if hist_int is not None:
                self._check_card_alias(hist_int, erratum, what)
            for variant in impl.get("historical_variant_passcodes", []) or []:
                variant_int = self._safe_passcode(variant, erratum, what, "historical_variant_passcodes entry")
                if variant_int is None or hist_int is None:
                    continue
                if abs(variant_int - hist_int) >= 10:
                    self.error(
                        "erratum.variant-out-of-range",
                        erratum.path,
                        f"{what}: variant {variant} is not within +/-10 of {hist}; EDOPro "
                        "treats farther codes as separate cards, not artwork variants",
                    )
                self._check_card_alias(variant_int, erratum, what)

    def _safe_passcode(self, value: object, erratum, what: str, field: str) -> int | None:
        """Guarded against malformed passcode data (schema's `passcode` def:
        an integer in 1..4294967295, matching `_is_valid_passcode()`'s
        strict, non-coercive check) - `Repository.load()` keeps
        historical_passcode/historical_variant_passcodes RAW and runs before
        any schema check, so malformed data here must become an ERROR
        finding, never an uncaught ValueError. Deliberately does NOT
        `int(value)` first: coercing before validating would silently
        accept "123", `True`, or 1.5 - none of which are a JSON integer -
        exactly the gap a coercive check would reopen."""
        if not _is_valid_passcode(value):
            self.error(
                "erratum.malformed-passcode",
                erratum.path,
                f"{what}: {field} {value!r} is not a valid passcode (schema: integer, 1..4294967295)",
            )
            return None
        if value in RESERVED_PASSCODE_RANGE:
            self.error(
                "card.reserved-passcode-collision",
                erratum.path,
                f"{what}: {field} {value} falls inside this project's own reserved range "
                "(retroformats/model.py's RESERVED_PASSCODE_RANGE, 600000000-699999999) - "
                "nothing in canonical data may use it yet; see docs/roadmap.md item 7",
            )
            return None
        return value

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
            pool_codes = pool.passcodes() | {
                int(sub["from"]["passcode"])
                for sub in (pool.cutoff or {}).get("region_substitutions", [])
            }
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
        overrides = fmt.raw.get("errata_overrides") or {}
        for key, policy in (
            ("reference_parity", fmt.reference_parity),
            ("unresolved_policy", fmt.unresolved_policy),
        ):
            if not policy:
                continue
            if not policy.get("reason"):
                self.error("format.policy-unjustified", fmt.path, f"{key}.reason is required")
            if not policy.get("sources"):
                self.error("format.policy-unjustified", fmt.path, f"{key}.sources is required")
            else:
                self._check_sources(list(policy["sources"]), fmt.path, fmt.id, key)
        if fmt.unresolved_policy and fmt.unresolved_policy.get("choice") not in (
            "modern",
            "historical",
        ):
            self.error(
                "format.bad-unresolved-policy",
                fmt.path,
                f"unresolved_policy.choice {fmt.unresolved_policy.get('choice')!r}",
            )
        # NOTE (task section 2): a blanket "every include is redundant under
        # parity" warning used to live here. That is not generally true
        # under the frozen precedence - exclude wins, then include, and only
        # THEN does parity govern (lflist._select_v2_override,
        # resolve_v2_parity) - so an include can deliberately pin a DIFFERENT
        # state than parity would independently select for the same card
        # (see test_parity_and_include_disagree_validator_analyses_include_not_parity).
        # Proving redundancy correctly would mean comparing, per card, what
        # the include resolves to against what resolve_v2_parity() would
        # independently resolve to for that same card - a genuinely
        # per-card fact, not a per-format one - so the blanket warning was
        # removed rather than narrowed to a check this format-level loop
        # cannot make correctly.
        if snapshot and fmt.reference_parity:
            # Parity is the format's definition, but where our own research
            # disagrees with the reference the divergence must stay visible.
            for erratum in self.repo.errata.values():
                if isinstance(erratum, ErratumV2):
                    self._validate_v2_parity(erratum, fmt, snapshot)
                    continue
                if erratum.id in fmt.errata_exclude:
                    continue
                from .lflist import in_reference, parity_override

                if not in_reference(erratum, fmt.reference_parity):
                    # Outside the reference: our research may still say this
                    # card needs a historical version here. Parity keeps the
                    # modern card, but the finding is worth surfacing - it is
                    # a candidate contribution back to the reference.
                    if erratum.relevant_changes():
                        selection = erratum.selection_at(snapshot)
                        if selection.state == "historical":
                            self.warn(
                                "format.parity-omits-historical",
                                fmt.path,
                                f"{erratum.modern_card.name}: this record's chronology says "
                                f"a historical version applies at {snapshot}, but the "
                                "reference implementation does not substitute this card, "
                                "so parity keeps the modern one",
                            )
                    continue
                if parity_override(erratum) is None:
                    continue
                if erratum.review_status != "reviewed":
                    continue
                if not erratum.relevant_changes():
                    self.warn(
                        "format.parity-substitutes-non-behavioural",
                        fmt.path,
                        f"{erratum.modern_card.name}: reference parity substitutes the "
                        f"upstream variant, but the record finds no functional or ruling "
                        f"change ({erratum.classification}) - the reference ships it for "
                        "period text, not behaviour",
                    )
                    continue
                selection = erratum.selection_at(snapshot)
                if selection.state == "modern" and selection.version_index is not None:
                    self.warn(
                        "format.parity-contradicts-chronology",
                        fmt.path,
                        f"{erratum.modern_card.name}: reference parity substitutes the "
                        f"upstream variant, but this record's chronology says the modern "
                        f"card was already in force at {snapshot}",
                    )

        if snapshot:
            for erratum in self.repo.errata.values():
                if isinstance(erratum, ErratumV2):
                    self._validate_v2_applicability(erratum, fmt, snapshot)
                    continue
                if not erratum.relevant_changes():
                    continue
                if fmt.reference_parity:
                    continue  # parity governs; disagreements reported above
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
                    policy = fmt.unresolved_policy or {}
                    if policy.get("choice") in ("modern", "historical"):
                        # Explicit, sourced, and named per card: the choice is
                        # auditable rather than silent.
                        if policy["choice"] == "modern" and not selection.modern_is_possible:
                            # Sharper than an ordinary default: the evidence
                            # cannot say WHICH historical version applies, but
                            # it can say the modern card is not one of them.
                            # Falling back to modern is a known error, and is
                            # reported as such rather than as a neutral choice.
                            self.warn(
                                "format.erratum-modern-known-wrong",
                                fmt.path,
                                f"{erratum.modern_card.name}: chronology is ambiguous at "
                                f"{snapshot} between versions "
                                f"{list(selection.candidates)}, and the modern card "
                                f"(version {selection.modern_version}) is NOT among them - "
                                "the unresolved_policy fallback to modern is a known "
                                "divergence, not a neutral default",
                            )
                        else:
                            self.warn(
                                "format.erratum-unresolved-defaulted",
                                fmt.path,
                                f"{erratum.modern_card.name}: chronology ambiguous at "
                                f"{snapshot}; resolved as {policy['choice']!r} by this "
                                "format's documented unresolved_policy",
                            )
                    else:
                        self.error(
                            "format.erratum-ambiguous",
                            fmt.path,
                            f"{erratum.id}: effective chronology is ambiguous at snapshot "
                            f"{snapshot} (changes {list(selection.ambiguous_changes)}); "
                            "narrow the chronology, adjudicate with a documented "
                            "errata_overrides include/exclude, or state an "
                            "errata_overrides.unresolved_policy — selection will not guess",
                        )
                elif selection.state == "gap":
                    gap = selection.acknowledged_gap
                    if gap:
                        # A documented, examined divergence: the format keeps
                        # the modern card and the shortfall stays visible
                        # (report surfaces it) rather than blocking forever.
                        self.warn(
                            "format.erratum-known-divergence",
                            fmt.path,
                            f"{erratum.modern_card.name}: version {selection.version_index} "
                            f"applies at {snapshot} but is not reproducible "
                            f"({gap.get('reason')}); the modern implementation is used and "
                            "the divergence is acknowledged on the record",
                        )
                    else:
                        self.error(
                            "format.erratum-implementation-gap",
                            fmt.path,
                            f"{erratum.id}: version {selection.version_index} applies at "
                            f"{snapshot} but has no usable implementation and the record "
                            "does not acknowledge the gap; record an implementation "
                            "(reuse-upstream/custom-script), document implementation.gap, "
                            "or exclude with documentation",
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
