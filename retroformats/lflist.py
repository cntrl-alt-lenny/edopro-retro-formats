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
    Coverage,
    Erratum,
    ErratumV2,
    Format,
    ImplementationCoverage,
    Pool,
    ReferenceIdentity,
    SelectionError,
    _is_valid_passcode,
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
    the erratum record plus WHATEVER carries its historical identity for the
    version its chronology (or an explicit include) selected — a v1
    `implementation` dict, a v2 `ImplementationCoverage`, or a v2
    `ReferenceIdentity` (an exact reference-provenance claim, orthogonal to
    Coverage — representation-gaps.md). Deliberately a three-way union, not
    a shared shape: converting a `ReferenceIdentity` into a fake `Coverage`
    (or v2 coverage into a fake v1 dict) just to avoid touching downstream
    code would hide exactly the distinctions this project's frozen
    v1/v2/Coverage boundaries exist to keep visible. Use
    `historical_identity()` to extract passcode/variants from any of the
    three — the ONLY place that needs to know all three shapes exist; the
    whitelist builder itself stays exactly as simple as before."""

    erratum: Erratum | ErratumV2
    implementation: dict | ImplementationCoverage | ReferenceIdentity


class MalformedHistoricalIdentity(ValueError):
    """A coverage/implementation claims a concrete historical substitution
    but carries no usable passcode. Raised rather than allowed to become
    `int(None)`: a build that reached here would otherwise die with an
    opaque TypeError deep inside whitelist emission."""


def historical_identity(
    override: dict | ImplementationCoverage | ReferenceIdentity,
) -> tuple[int, tuple[int, ...]]:
    """(historical_passcode, historical_variant_passcodes) from any of the
    THREE representations — the one place a v1 dict, a v2
    `ImplementationCoverage`, and a v2 `ReferenceIdentity` are all read
    through a common lens, and only for this one concrete fact, never for
    anything about WHICH state/version/reference was selected.

    Never called on a coverage/identity that has not already passed
    `_usable_v2()`/`_usable()`/the reference-identity fail-safe checks; the
    explicit raise here is a backstop so a future caller that forgets fails
    loudly and locally instead of producing `int(None)` - or, since a
    backstop must not itself be the hole it guards against, silently
    coercing a schema-invalid value (`int("123")`, `int(True)`) into one
    that looks valid. Uses the same strict `_is_valid_passcode()` authority
    every other caller does; never `int(...)`."""
    if isinstance(override, ImplementationCoverage):
        passcode = override.historical_passcode
        variants = override.historical_variant_passcodes
        where = f"coverage kind {override.kind.value}"
    elif isinstance(override, ReferenceIdentity):
        passcode = override.historical_passcode
        variants = override.historical_variant_passcodes
        where = f"reference identity {override.reference_id!r}"
    else:
        passcode = override.get("historical_passcode")
        variants = override.get("historical_variant_passcodes", []) or []
        where = f"implementation strategy {override.get('strategy')!r}"
    if passcode is None:
        raise MalformedHistoricalIdentity(
            f"{where} claims a historical substitution but records no historical_passcode"
        )
    if not _is_valid_passcode(passcode):
        raise MalformedHistoricalIdentity(
            f"{where}: historical_passcode {passcode!r} is not a valid passcode "
            "(schema: integer, 1..4294967295)"
        )
    for variant in variants:
        if not _is_valid_passcode(variant):
            raise MalformedHistoricalIdentity(
                f"{where}: historical_variant_passcodes entry {variant!r} is not a valid passcode "
                "(schema: integer, 1..4294967295)"
            )
    return passcode, tuple(variants)


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


def _valid_identity(passcode: object, variants: object) -> bool:
    """The schema's `passcode` def is the sole authority (see
    `_is_valid_passcode`): every historical_passcode and every entry of
    historical_variant_passcodes must independently satisfy it. A value that
    is present but not a valid passcode (e.g. a typo'd string) is exactly as
    unusable as a missing one — never "usable but weird"."""
    return _is_valid_passcode(passcode) and all(_is_valid_passcode(v) for v in (variants or ()))


def _usable(impl: dict | None) -> dict | None:
    if (
        impl
        and impl.get("strategy") in ("reuse-upstream", "custom-script")
        and impl.get("historical_passcode")
        and _valid_identity(impl.get("historical_passcode"), impl.get("historical_variant_passcodes"))
    ):
        return impl
    return None


SUBSTITUTING_COVERAGE_KINDS = (Coverage.REUSE_UPSTREAM, Coverage.CUSTOM_SCRIPT)


def _claims_substitution(coverage: ImplementationCoverage | None) -> bool:
    """The coverage says a concrete historical card should replace the modern
    one — regardless of whether it actually carries the identity to do it."""
    return coverage is not None and coverage.kind in SUBSTITUTING_COVERAGE_KINDS


def _usable_v2(coverage: ImplementationCoverage | None) -> ImplementationCoverage | None:
    """A v2 coverage carries a concrete, executable historical substitution
    only for REUSE_UPSTREAM/CUSTOM_SCRIPT **that actually record a
    historical_passcode** — the same two kinds `historical_identity()` knows
    how to read (design doc §2 of this task). NONE_NEEDED/KNOWN_GAP/
    UNRESOLVED/MODERN are never substitutions: NONE_NEEDED means the modern
    executable already IS correct for this state; the other three mean no
    concrete swap can be made at all.

    The passcode check mirrors legacy `_usable()` deliberately: without it a
    malformed REUSE_UPSTREAM coverage passed straight through to
    `historical_identity()` and died as `int(None)` mid-build. Malformed
    coverage is reported as a build PROBLEM by the callers that can
    (`_malformed_substitution()`), not silently dropped."""
    if (
        _claims_substitution(coverage)
        and coverage.historical_passcode is not None
        and _valid_identity(coverage.historical_passcode, coverage.historical_variant_passcodes)
    ):
        return coverage
    return None


def _malformed_substitution(coverage: ImplementationCoverage | None) -> bool:
    """Claims a substitution but cannot supply one — the case the validator
    reports as data corruption and a direct build must refuse rather than
    crash on."""
    if not _claims_substitution(coverage):
        return False
    if coverage.historical_passcode is None:
        return True
    return not _valid_identity(coverage.historical_passcode, coverage.historical_variant_passcodes)


def baseline_override(erratum: Erratum | ErratumV2) -> dict | ImplementationCoverage | None:
    """The erratum's baseline historical implementation, when it is usable as
    a substitution (an upstream or custom historical passcode). v2's
    baseline is the `frozenset()` down-set — never a different state merely
    because baseline itself lacks a usable implementation (design doc §4 of
    this task): a NONE_NEEDED/KNOWN_GAP/UNRESOLVED baseline yields no
    substitution here, full stop, not a fallback to some other state."""
    if isinstance(erratum, ErratumV2):
        return _usable_v2(erratum.state_for(frozenset()).coverage)
    return _usable(erratum.implementation)


def in_reference(erratum: Erratum | ErratumV2, parity: dict) -> bool:
    """Whether a record is part of the reference implementation this format
    reproduces. Provenance decides it: upstream ships historical variants for
    cards its own list does NOT use, so "has an upstream variant" is not the
    same question as "the reference substitutes it"."""
    marker = parity.get("provenance_source")
    if not marker:
        return True
    return marker in erratum.sources


_NO_REFERENCE_ID_MATCH = object()
"""Sentinel distinguishing 'this format names no reference_id, or this
record has no matching reference_identities[] entry - fall through to the
structural walk' from 'a matching entry exists but is malformed/mismatched
- FAIL SAFE, do not fall through' (frozen precedence, task section 4).
`None` alone cannot carry this distinction, since it is also the walk's own
'nothing found' result."""


def _reference_identity_override(
    erratum: ErratumV2, parity: dict, problems: list[str]
) -> "ReferenceIdentity | None | object":
    """Step 3 of the frozen reference-parity precedence (task section 4):
    an exact, authored `reference_identities[]` entry outranks the
    structural Coverage walk for the SAME reference — it is a different,
    more specific kind of fact ("reference X uses card entry Y"), not a
    heuristic guess at one.

    Returns `_NO_REFERENCE_ID_MATCH` when the format's parity policy names
    no `reference_id`, or this record has no entry with that
    `reference_id` — the caller MUST fall through to the existing
    provenance-membership + structural-walk behaviour (step 4).

    Returns `None` when a MATCHING entry exists but is malformed (no valid
    passcode) or declares a `provenance_source` that contradicts the
    format's own — a problem is appended and the caller MUST NOT fall
    through: an exact assertion that turns out corrupt or misconfigured is
    never silently replaced by a weaker heuristic's guess.

    Returns the `ReferenceIdentity` itself when a matching, well-formed
    entry is found."""
    reference_id = parity.get("reference_id")
    if not reference_id:
        return _NO_REFERENCE_ID_MATCH
    matches = [r for r in erratum.reference_identities if r.reference_id == reference_id]
    if not matches:
        return _NO_REFERENCE_ID_MATCH
    if len(matches) > 1:
        # Two authored entries claiming the SAME reference_id is ambiguous
        # data, not a tie to break by whichever happened to be declared
        # first - declaration order is not adjudication. Fails safe exactly
        # like a matched-but-malformed single entry: a problem is appended
        # and the caller must NOT fall through to the structural walk.
        problems.append(
            f"{erratum.id}: {len(matches)} reference_identities[] entries declare the same "
            f"reference_id {reference_id!r}; declaration order is not adjudication - "
            "de-duplicate or disambiguate the authored data"
        )
        return None
    matching = matches[0]
    fault = _reference_identity_fault(matching, erratum, parity)
    if fault is not None:
        problems.append(
            f"{erratum.id}: reference_identities[] entry for reference_id {reference_id!r} {fault}"
        )
        return None
    return matching


def _reference_identity_fault(
    identity: ReferenceIdentity, erratum: ErratumV2, parity: dict
) -> str | None:
    """Why a MATCHING exact identity is not usable for a direct build, or
    None when it is genuinely well formed.

    A direct `build_lflist()` call cannot assume `validate` ran first, and
    `ReferenceIdentity.from_raw()` deliberately does not police semantics —
    it even coerces `reference_id`/`provenance_source` through `str()`, so
    a schema-invalid authored value can arrive here looking like a string.
    Every build-critical part of the identity is therefore re-checked
    against the RAW authored entry, not the coerced dataclass, so obviously
    malformed data can never be emitted. Nothing is coerced or repaired:
    the caller fails safe with `ErrataSelectionError`, never a fallback to
    the structural walk, a silent modern card, or a raw ValueError/
    TypeError from deep inside the build."""
    raw = identity.raw or {}
    for field_name in ("reference_id", "provenance_source", "upstream"):
        value = raw.get(field_name)
        if not isinstance(value, str) or not value.strip():
            return (
                f"declares {field_name}={value!r}, which is not a non-empty string; "
                "parity refuses to build from a malformed identity"
            )
    if "script" in raw:
        # script is optional (may be absent entirely) but, per schema,
        # strictly a non-empty string when authored at all - an authored
        # null or "" is malformed data, not a spelling of "absent".
        script = raw["script"]
        if script is None or not isinstance(script, str) or not script.strip():
            return (
                f"declares script={script!r}, which must be a non-empty string when "
                "present (omit the field entirely if genuinely unknown)"
            )
    variants_raw = raw.get("historical_variant_passcodes", [])
    if not isinstance(variants_raw, list):
        return (
            f"declares historical_variant_passcodes={variants_raw!r}, which is not a list; "
            "parity refuses to guess whether that means no variants or malformed authored data"
        )
    if identity.historical_passcode is None or not _valid_identity(
        identity.historical_passcode, identity.historical_variant_passcodes
    ):
        return (
            "records no usable historical_passcode; parity cannot emit a substitution it "
            "has no identity for"
        )
    if identity.historical_passcode == erratum.modern_card.passcode:
        return (
            f"declares historical_passcode {identity.historical_passcode} equal to "
            "modern_card.passcode; if the reference uses the modern card there is no "
            "substitution to make"
        )
    if identity.provenance_source not in erratum.sources:
        return (
            f"declares provenance_source {identity.provenance_source!r}, which is not in "
            "this record's own sources; the assertion cites a source the record does not carry"
        )
    expected_provenance = parity.get("provenance_source")
    if expected_provenance and identity.provenance_source != expected_provenance:
        return (
            f"declares provenance_source {identity.provenance_source!r}, but format "
            f"reference_parity declares provenance_source {expected_provenance!r} - "
            "configuration mismatch, refusing to guess which is correct"
        )
    return None


def _v2_parity_walk_override(
    erratum: ErratumV2, parity: dict | None = None, problems: list[str] | None = None
) -> ImplementationCoverage | ReferenceIdentity | None:
    """The frozen design's deterministic structural walk (§5 of the
    original design task), now preceded by the exact reference-identity
    check (task section 4's step 3) when `parity` is given: fewest
    relevant events first, ties broken by sorted event-id tuple, starting
    from baseline — the first state in that walk carrying a usable
    historical override. Purely structural (never chronology, never
    declaration order): `structural_states()` is already keyed by event-set
    and sorted (size, sorted ids), so this walk is invariant under
    `events{}`'s declaration order by construction."""
    local_problems = problems if problems is not None else []
    if parity:
        reference_override = _reference_identity_override(erratum, parity, local_problems)
        if reference_override is not _NO_REFERENCE_ID_MATCH:
            return reference_override  # a ReferenceIdentity, or None (fail-safe; problem appended)
    return _v2_structural_walk(erratum, local_problems)


def _v2_structural_walk(erratum: ErratumV2, local_problems: list[str]) -> ImplementationCoverage | None:
    """The structural half alone (step 4's second stage), with no exact-
    identity check and no membership gate - split out so
    `resolve_v2_parity()` can order the three stages itself."""
    for down_set in erratum.structural_states():
        coverage = erratum.state_for(down_set).coverage
        if _malformed_substitution(coverage):
            # Never silently walk past corrupt identity data and pick a later
            # state as if this one had said nothing.
            local_problems.append(
                f"{erratum.id}: state {sorted(down_set) or 'baseline'} declares coverage "
                f"{coverage.kind.value} but records no historical_passcode; parity cannot "
                "emit a substitution it has no identity for"
            )
            return None
        usable = _usable_v2(coverage)
        if usable is not None:
            return usable
    return None


@dataclass(frozen=True)
class ParityResolution:
    """How one record resolved against one format's `reference_parity`.

    `via` names WHICH stage of the frozen precedence decided, which the
    validator needs in order to report accurately (an exact authored
    assertion and a structural guess are different findings), and which
    keeps "outside the reference" distinguishable from "inside it, but the
    walk found nothing to substitute"."""

    override: "ImplementationCoverage | ReferenceIdentity | None"
    via: str  # reference-identity | structural-walk | outside-reference | unusable

    @property
    def outside_reference(self) -> bool:
        return self.via == "outside-reference"


def resolve_v2_parity(erratum: ErratumV2, parity: dict, problems: list[str]) -> ParityResolution:
    """Steps 3-4 of the frozen v2 reference-parity precedence, in ONE place.

    The full order is: 1 exclude, 2 include, 3 exact matching
    `reference_identities[]` entry, 4 provenance membership then structural
    parity walk, 5 chronology. Steps 1/2/5 belong to the callers; 3 and 4
    live here, because they are the pair that must not be reordered - and
    were: the builder and the validator each asked `in_reference()` FIRST
    and so never reached the exact lookup for a record the provenance gate
    rejected. An exact authored assertion ("reference X uses card entry Y")
    is a different, more specific kind of fact than a membership heuristic,
    and outranks it.

    Both the builder (`_select_v2_override`) and the validator
    (`_validate_v2_parity`) call this and nothing else, so they cannot
    drift into different precedence again.

    Note the asymmetry, which is deliberate: a matching-but-unusable
    identity FAILS SAFE (`via="unusable"`, a problem appended) and is never
    downgraded to the structural walk, whereas NO matching entry falls
    through to the old behaviour untouched."""
    identity = _reference_identity_override(erratum, parity, problems)
    if identity is not _NO_REFERENCE_ID_MATCH:
        if identity is None:
            return ParityResolution(None, "unusable")
        return ParityResolution(identity, "reference-identity")
    if not in_reference(erratum, parity):
        return ParityResolution(None, "outside-reference")
    return ParityResolution(_v2_structural_walk(erratum, problems), "structural-walk")


def parity_override(
    erratum: Erratum | ErratumV2, parity: dict | None = None, problems: list[str] | None = None
) -> dict | ImplementationCoverage | ReferenceIdentity | None:
    """The historical implementation a reference-parity format must emit.

    A reference list ships ONE historical variant per card, and reproducing it
    is the whole point of parity — so if research mapped that variant to a
    later revision than the baseline (leaving the baseline itself
    unimplemented), parity still emits the variant the reference carries.
    The validator separately reports where our chronology and the reference
    disagree, so the mapping question stays visible.

    v2 (design doc §5 of this task): this is a PARITY-ONLY policy, not
    chronology selection — an exact `reference_identities[]` entry wins
    first when `parity` names a matching `reference_id`; otherwise it walks
    `structural_states()` deterministically (never `events{}` declaration
    order, never a snapshot) and takes the first usable historical override
    it finds. `parity`/`problems` are ignored on the v1 path - v1 records
    never carry `reference_identities`.
    """
    if isinstance(erratum, ErratumV2):
        return _v2_parity_walk_override(erratum, parity, problems)
    usable = baseline_override(erratum)
    if usable is not None:
        return usable
    for change in erratum.relevant_changes():
        usable = _usable(change.get("resulting_implementation"))
        if usable is not None:
            return usable
    return None


def _executable_outcome(coverage: ImplementationCoverage) -> tuple | None:
    """A hashable summary of what a v2 coverage kind actually executes as,
    for checking whether 2+ ambiguous non-modern candidates would produce
    the SAME playable result under unresolved_policy 'historical' (design
    doc §7 of this task). None means "no concrete outcome can be
    established" (KNOWN_GAP/UNRESOLVED) and is never treated as agreeing
    with anything, including another None."""
    if _claims_substitution(coverage):
        # A substitution with no usable passcode establishes no outcome at
        # all: it must never be able to "agree" with a well-formed
        # candidate, whether the passcode is missing OR simply not a valid
        # integer passcode.
        if coverage.historical_passcode is None or not _valid_identity(
            coverage.historical_passcode, coverage.historical_variant_passcodes
        ):
            return None
        return ("substitute", coverage.historical_passcode, coverage.historical_variant_passcodes)
    if coverage.kind == Coverage.NONE_NEEDED:
        return ("modern",)
    return None


def _select_v1_override(
    erratum: Erratum,
    fmt: Format,
    snapshot: _dt.date | None,
    parity: dict | None,
    policy: str | None,
    problems: list[str],
) -> dict | None:
    """Unchanged legacy resolution — see select_applicable_errata's own
    docstring for the 5-step order this implements."""
    if erratum.id in fmt.errata_exclude:
        return None
    if erratum.id in fmt.errata_include:
        return baseline_override(erratum)
    if parity:
        if in_reference(erratum, parity):
            return parity_override(erratum)
        return None
    if snapshot is None or not erratum.relevant_changes():
        return None
    if erratum.review_status != "reviewed":
        return None
    selection = erratum.selection_at(snapshot)
    if selection.state == "historical":
        return selection.implementation
    if selection.state == "ambiguous":
        if policy == "historical":
            return baseline_override(erratum)
        if policy == "modern":
            return None  # documented conservative default; validator names each card
        problems.append(
            f"{erratum.id}: chronology ambiguous at snapshot {snapshot} "
            "(narrow the change's effective chronology, adjudicate with a "
            "documented errata_overrides include/exclude, or state an "
            "errata_overrides.unresolved_policy)"
        )
        return None
    if selection.state == "gap" and not selection.acknowledged_gap:
        problems.append(
            f"{erratum.id}: version {selection.version_index} applies at {snapshot} "
            "but has no usable implementation and the record does not acknowledge "
            "the gap (record one, document implementation.gap, or exclude)"
        )
    # An ACKNOWLEDGED gap deliberately falls through to the modern card: the
    # divergence is recorded on the record and reported, not silent.
    return None


def _select_v2_override(
    erratum: ErratumV2,
    fmt: Format,
    snapshot: _dt.date | None,
    parity: dict | None,
    policy: str | None,
    problems: list[str],
) -> ImplementationCoverage | ReferenceIdentity | None:
    """The v2 resolution, matching select_applicable_errata's 5-step order
    in SHAPE only — v2 has no numeric version, so "historical" under
    ambiguity is re-derived from event-set semantics, never a fallback to
    "the first/smallest candidate" (design doc §§4-8 of this task)."""
    if erratum.id in fmt.errata_exclude:
        return None
    if erratum.id in fmt.errata_include:
        # include pins the BASELINE semantic state (frozenset()) — never a
        # different v2 state merely because baseline lacks an override. What
        # that pin MEANS depends on the baseline's coverage kind, and the
        # five kinds are genuinely different answers, not one "no override":
        #   REUSE_UPSTREAM/CUSTOM_SCRIPT -> substitute it;
        #   NONE_NEEDED  -> keep modern; the modern executable IS the baseline
        #                   behaviour, so the pin is satisfied;
        #   KNOWN_GAP    -> keep modern, but the format is knowingly playing a
        #                   divergent card; validate.py surfaces it;
        #   UNRESOLVED   -> FAIL SAFE. An explicit include is a claim about
        #                   WHICH state applies, never permission to ignore
        #                   that we do not know how to build that state.
        baseline = erratum.state_for(frozenset()).coverage
        if _malformed_substitution(baseline):
            problems.append(
                f"{erratum.id}: explicitly included, and its baseline declares coverage "
                f"{baseline.kind.value}, but it records no historical_passcode; there is no "
                "identity to substitute"
            )
            return None
        if baseline.kind == Coverage.UNRESOLVED:
            problems.append(
                f"{erratum.id}: explicitly included, but its baseline implementation coverage "
                "is unresolved — an include says which state applies, not how to build it; "
                "record coverage (reuse-upstream/custom-script/none-needed), document a "
                "known-gap, or drop the include"
            )
            return None
        return _usable_v2(baseline)
    if parity:
        # Step 3 (exact reference_identities[] entry) then step 4
        # (provenance membership + structural walk), in that order and via
        # the one primitive the validator also uses. Asking in_reference()
        # first here is exactly the bug this replaces: it gated the exact
        # lookup behind a weaker membership heuristic.
        return resolve_v2_parity(erratum, parity, problems).override
    if snapshot is None or not erratum.has_implementation_relevant_history():
        return None
    if erratum.review_status != "reviewed":
        return None
    try:
        selection = erratum.selection_at(snapshot)
    except SelectionError as exc:
        # A genuinely contradictory record, or one whose chronology cannot be
        # parsed at all — the validator's ordering/effective invariants
        # (step 3) should have already reported the underlying CONTRADICTED
        # edge or bad date, but a direct build call must still fail safe
        # rather than crash uncaught: it cannot assume validate ran first.
        problems.append(f"{erratum.id}: {exc}")
        return None
    all_relevant_ids = frozenset(e.id for e in erratum.relevant_events())
    if selection.chronology == "determinate":
        candidate = selection.candidates[0]
        if candidate.events == all_relevant_ids:
            return None  # terminal/modern: no override
        coverage = candidate.coverage
        if _claims_substitution(coverage):
            usable = _usable_v2(coverage)
            if usable is not None:
                return usable
            problems.append(
                f"{erratum.id}: determinate historical state {sorted(candidate.events)} declares "
                f"coverage {coverage.kind.value} at {snapshot} but records no "
                "historical_passcode; there is no identity to substitute"
            )
            return None
        if coverage.kind in (Coverage.NONE_NEEDED, Coverage.KNOWN_GAP):
            # NONE_NEEDED: the modern executable already IS correct for this
            # state. KNOWN_GAP: an ACKNOWLEDGED divergence — keep modern,
            # validate.py surfaces the documented gap; never a build error.
            return None
        problems.append(
            f"{erratum.id}: determinate historical state {sorted(candidate.events)} applies "
            f"at {snapshot} but its implementation coverage is unresolved (record one, "
            "document a known-gap, or exclude)"
        )
        return None
    # ambiguous
    if policy == "modern":
        return None  # validator names each card if modern is a known-wrong fallback
    if policy == "historical":
        non_modern = [c for c in selection.candidates if c.events != all_relevant_ids]
        outcomes = [_executable_outcome(c.coverage) for c in non_modern]
        if None in outcomes or len(set(outcomes)) != 1:
            problems.append(
                f"{erratum.id}: chronology ambiguous at snapshot {snapshot} between "
                f"{[sorted(c.events) for c in selection.candidates]}, and unresolved_policy "
                "'historical' cannot resolve to one concrete executable outcome — the "
                "plausible non-modern candidates disagree, or one has no usable coverage; "
                "adjudicate this card explicitly with errata_overrides"
            )
            return None
        if outcomes[0][0] == "substitute":
            return next(c.coverage for c in non_modern if _executable_outcome(c.coverage) == outcomes[0])
        return None  # every plausible non-modern candidate agrees on NONE_NEEDED
    problems.append(
        f"{erratum.id}: chronology ambiguous at snapshot {snapshot} "
        "(narrow an event's effective chronology, adjudicate with a "
        "documented errata_overrides include/exclude, or state an "
        "errata_overrides.unresolved_policy)"
    )
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

    v1-shaped and v2-shaped records both follow this same 5-step order, but
    through entirely separate resolution functions (`_select_v1_override`/
    `_select_v2_override`) — never one shared code path, per design doc §8's
    hard legacy/v2 boundary.
    """
    selected: dict[int, SelectedOverride] = {}
    problems: list[str] = []
    snapshot = _dt.date.fromisoformat(fmt.snapshot) if fmt.snapshot else None
    parity = fmt.reference_parity
    policy = (fmt.unresolved_policy or {}).get("choice")

    for erratum in repo.errata.values():
        if isinstance(erratum, ErratumV2):
            override = _select_v2_override(erratum, fmt, snapshot, parity, policy, problems)
        else:
            override = _select_v1_override(erratum, fmt, snapshot, parity, policy, problems)
        if override is not None:
            selected[erratum.modern_card.passcode] = SelectedOverride(erratum, override)
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
            # selected historical passcode (and its artwork variants) — read
            # through historical_identity() so a v1 dict and a v2
            # ImplementationCoverage are handled by the one place that needs
            # to know both shapes exist, not by this loop.
            passcode, variants = historical_identity(override.implementation)
            emit_codes = [passcode, *variants]
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
